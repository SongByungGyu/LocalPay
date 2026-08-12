# 08. Phase 13 Gate 1 — 지도 BBOX + 서버 Search

- 보고일: 2026-08-12
- 이전 커밋: `72059d1 feat(infra): expose LocalPay API through Traefik HTTPS (Phase 12)`
- 커밋:
  - `e50b668 feat(search): add /api/v1/search + BBOX size guard on /merchants/map`
  - `a36ee76 feat(ios): load merchants by map bounding box + server search`
- 상태: **완료. Simulator + 실기기 iPhone 모두 HTTPS 로 지도 BBOX 자동 로딩 · 서버 검색 정상.**

## 한 줄 요약

지도 로딩을 `fetchAll(1000)` → `/api/v1/merchants/map?north&south&east&west` BBOX 방식으로 전환, iOS 는 400ms debounce · Task 취소 · generation counter 로 stale 응답 폐기 · 유사 BBOX 스킵을 갖춘 안전한 카메라 연동을 구현했다. 검색은 로컬 필터 → 서버 `/api/v1/search` (name/marketName/description/products + PostGIS 거리) 로 스왑했다. iOS UI/UX · Dummy · Preview · Test 는 변경하지 않았다. Gate 2 이후 (실 데이터 import) 관련 신규 테이블은 아직 만들지 않았다 (스펙 §5 준수).

## BBOX

- **Backend**: 기존 `GET /api/v1/merchants/map` 유지 + **MAX_BBOX_DEGREES = 6.0** 상한 추가 (전세계 zoom-out 방지 → 400 반환). north>south · east>west validation 유지. category/payment 필터 유지. backward compatibility 유지
- **max limit**: 1000 (기존 유지)
- **validation**: north/south/east/west 순서, bbox 면적 6°×6°, category enum, payment enum
- **category/payment**: 함께 사용 가능
- **iOS camera integration**: `MapHomeView.onMapCameraChange(frequency:.onEnd)` → `MKCoordinateRegion` → `MapBBox` → `viewModel.onCameraChanged(bbox:)`
- **debounce**: 400ms (`Task.sleep`, 스펙 §5-6 300~500ms 범위)
- **cancellation**: 이전 debounce Task `cancel()` + 진행 중 fetch Task `cancel()` + `HTTPClient` 에서 `URLError.cancelled` → `CancellationError` 로 변환 (오탐 노이즈 제거)
- **race prevention**: `generation` UInt64 카운터. 응답 도착 시 `mySeq == self.generation` 확인, 아니면 폐기. 카메라를 빠르게 여러 번 이동해도 최신 세대 응답만 반영
- **유사 BBOX 스킵**: `MapBBox.isApproximatelyEqual(to:tolerance:)` 0.0005° (~55m) 이내면 요청 자체 스킵

## Search

- **endpoint**: `GET /api/v1/search`
- **파라미터**: `q` (필수, min 1) / `lat` / `lng` / `radius` / `category` / `payment` / `limit` / `offset`
- **searchable fields**: `merchants.name`, `market_name`, `description`, `products` (JSONB text 캐스팅 부분일치)
- **location search**: `lat/lng` 함께 있으면 PostGIS `ST_DWithin` + `ST_Distance` (Geography) 로 반경 필터 · 거리 정렬 · 응답에 `distanceMeters` 채움. `radius` 미지정 시 30km 기본
- **관련도/정렬**: 위치 없으면 `lower(name) == lower(q)` 정확 매치 우선, 그 뒤 alphabetical
- **iOS integration**: `RemoteMerchantRepository.search()` → `/api/v1/search?q=&limit=100`. 기존 fetchAll → 로컬 필터 방식 폐기. Dummy 는 로컬 필터 유지 (Preview/Test)
- **pagination**: `limit` (기본 50, 최대 200), `offset` (최대 10,000)
- **한국어 카테고리 매핑**: `음식점 → restaurant`, `약국 → pharmacy` 등 (이름/설명에 걸리는 케이스 대응 별개)

## Verification

- **Simulator (iPhone 15, iOS 18, SSH 터널 없음)**:
  ```
  [RepositoryFactory] → RemoteMerchantRepository baseURL=https://localpay.bgcompanyoffice.cloud
  [HTTPClient] GET .../api/v1/merchants/map?north=…&south=…&east=…&west=…&payment=all&limit=1000
  [HTTPClient] ← HTTP 200 bytes=10623
  [HTTPClient] ✓ decoded 10 items
  [MapHomeViewModel] BBOX ok count=10
  ```
- **Physical Device (사용자 실기기, HTTPS)**:
  - 초기 안양 count=10 (fallback BBOX 영역)
  - 지도 이동에 따라 count 10 → 2 → 0 → 0 → 2 → 16 → 16 → 17 (BBOX 정확 반영)
  - `[HTTPClient] cancelled: …` 로그 확인 (race prevention 정상)
  - 검색 Tab → 정상 결과 표시
- **Existing UI regression**: 필터 · 상세 · 즐겨찾기 · MY · 리뷰 작성 무변경. 기존 화면 그대로

## Server-side 실 API 검증 (HTTPS)

```
/api/v1/merchants/map (안양 BBOX)           → count=17
/api/v1/merchants/map (전세계 zoom-out)     → 400 bbox too large
/api/v1/merchants/map (north<south)         → 400 north must be greater than south
/api/v1/merchants/map (east<west)           → 400 east must be greater than west
/api/v1/search?q=삼겹살                     → 1건 (m-001 안양중앙시장 행복정육점)
/api/v1/search?q=약국                       → 1건 (m-004 평촌우리약국)
/api/v1/search?q=삼겹살&lat=&lng=&radius=   → distanceMeters=2878.6m
/api/v1/search (q 누락)                     → 422
/api/v1/search?q=x&lat only                 → 400 lat and lng must be provided together
/api/v1/search?q=x&radius (lat 없이)        → 400 radius requires lat/lng
/api/v1/search?q=x&payment=wat              → 400 invalid payment
/api/v1/search?q=x&category=not-a-cat       → 400 invalid category
```

## Tests

- **Backend**: `test_health.py` 1건 + `test_route_registration.py` 신규 8건 (bbox 순서 · bbox 면적 상한 · search 파라미터 필수 · lat/lng 짝 · radius 짝 · payment/category 검증). 컨테이너 내 `pytest tests/` 통과
- **iOS**: 기존 `RemoteMerchantRepositoryDecodingTests` 7건 유지 · 통과. BBOX 응답도 기존 `Merchant` 스키마 그대로라 별도 decode 테스트 불필요. Simulator 실행 검증 통과

## 변경 파일

| 종류 | 파일 |
|---|---|
| 신규 | `backend/app/api/v1/search.py` |
| 신규 | `backend/tests/test_route_registration.py` |
| 수정 | `backend/app/api/v1/merchants.py` (BBOX 면적 상한) |
| 수정 | `backend/app/api/v1/router.py` (search 라우터 마운트) |
| 신규 | `LocalPay/Models/MapRegion.swift` — `MapBBox` struct + extension |
| 수정 | `LocalPay/Data/Repository/MerchantRepository.swift` (`mapMerchants` 추가) |
| 수정 | `LocalPay/Data/Repository/RemoteMerchantRepository.swift` (BBOX + 서버 search) |
| 수정 | `LocalPay/Data/Dummy/DummyMerchantRepository.swift` (BBOX 로컬 필터) |
| 수정 | `LocalPay/Data/Network/HTTPClient.swift` (URLError.cancelled → CancellationError) |
| 수정 | `LocalPay/Features/Map/MapHomeViewModel.swift` (debounce + cancel + generation + BBOX) |
| 수정 | `LocalPay/Features/Map/MapHomeView.swift` (`onMapCameraChange`) |

## 스펙 §5 준수 확인 — Gate 1 에서 하지 않은 것

- ❌ `raw_local_currency_merchants`, `raw_onnuri_merchants`, `merchant_sources`, `merchant_payment_methods`, `data_import_runs`, `geocode_queue` 미생성
- ❌ 전국 데이터 Import 미실행
- ❌ 공공데이터 API · Kakao Local 미호출
- ❌ Dummy 25개 유지 · 삭제 안 함
- ❌ 운영 DB destructive migration 없음
- ❌ BG Company · Traefik · Docker volume 무변경

## Git

- **commits**:
  - `e50b668 feat(search): add /api/v1/search + BBOX size guard on /merchants/map`
  - `a36ee76 feat(ios): load merchants by map bounding box + server search`
- **push**: `72059d1..a36ee76 main -> main` 완료

## Remaining

### Gate 2 준비 사항 (다음 세션)
1. `data.go.kr` KOMSCO 지역화폐 통합가맹점 API 활용신청 상태 확인
2. 최신 공식 API 명세 (Parameter/Response/Rate limit) 웹으로 재확인
3. `raw_local_currency_merchants` + `merchant_sources` + `data_import_runs` migration 설계
4. `worker/importers/local_currency/` 구조 (parser/importer/README)
5. 안양 지역 코드 확인 후 sample import (100~500건)
6. Dry-run + 검증 후 사용자 승인 → Gate 3 (온누리) 로

### 사용자에게 필요한 작업
1. **공공데이터포털에서 API 활용신청** — `한국조폐공사_통합_가맹점기본정보` (Dataset 15119539). Key 발급되면 VPS `/opt/localpay/deploy/.env` 에 `DATA_GO_KR_SERVICE_KEY=…` 추가 (Git 절대 금지)
2. Gate 3 에서 온누리 CSV snapshot 다운로드 필요 (`소상공인시장진흥공단_전국 온누리상품권 가맹점 현황` Dataset 3060079). 최신본 확인 후 사용자가 로컬에 저장 · VPS 로 전송
