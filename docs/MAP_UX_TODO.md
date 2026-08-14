# MAP_UX_TODO — 시장 단위 좌표 상황에서의 지도 UX (Phase 13 Gate 3-B1)

> Gate 3-B1 이후 iOS 지도가 온누리 실 데이터를 표시할 때의 UX 규칙.
> **핵심 원칙: 시장 centroid 좌표를 개별 매장 마커로 절대 사용하지 않는다.**

## 배경

- 온누리 공식 CSV (Dataset 3060079, 2025-07-31) 는 `소재지` 컬럼이 **시도만** 담고 있어 매장별 정확한 좌표가 없다
- Kakao Local 유료 등록·매장별 geocoding 은 유보 상태
- 대신 소속 시장/상점가 좌표 (`worker/importers/onnuri/anyang_markets.py`) 로 각 매장을 그룹핑

**같은 좌표를 여러 매장이 공유하면 지도상 한 지점에 마커 1,255개가 겹치는 안티패턴** 이 발생한다. 이 문서는 그걸 방지하는 UX 규칙을 정의한다.

## 금지 사항 (스펙 §6)

❌ **1,255개 개별 매장에 시장 centroid 좌표를 각각 부여해 지도에 표시**  
   → 같은 픽셀에 마커 수백 개 겹침, 사용자 혼란, 앱 성능 저하

❌ **`location_precision = market_level` 매장을 개별 마커로 렌더링**

❌ **시장 centroid 좌표를 canonical `merchants.latitude / longitude` 필드에 exact 로 넣기** (Gate 3-B1 에서 하지 않음 · Gate 4 이후 `location_precision` 메타데이터와 함께 저장)

## 권장 UX (Gate 4 이후 구현)

### 지도 표시 계층 (Zoom level 별)

**Zoom high (전국~광역시)**
- 광역시·시군구 단위 클러스터 마커 (매장 수 표시)
- 예: "안양시 · 온누리 1,255곳"

**Zoom mid (시군구)**
- **시장/상점가 대표 마커** (`location_precision = market_level` 매장을 시장별로 집계)
- 마커 라벨: "안양중앙시장 · 온누리 72곳"
- 정확 좌표 매장 (`location_precision = exact/approximate`) 은 이 zoom 부터 별도 개별 마커로 표시

**Zoom low (지도 상세, 매장 이름 보임 수준)**
- 시장 대표 마커는 유지 (또는 살짝 흐리게)
- 정확 좌표 매장은 개별 마커로 명확히 표시

### 시장 마커 UI

- 마커 아이콘: 결제수단 색상 (온누리=초록) + 시장 표시 (건물/상점가 SF Symbol)
- 마커 라벨: "시장 이름 · 매장 N곳"
- 탭 시 하단 sheet 로 매장 리스트 (스크롤)
- 리스트 항목: 매장명 · 취급품목 · 지류/디지털 지원 뱃지 · 즐겨찾기 하트

### 매장 상세 진입
- 리스트 항목 탭 → 매장 상세 페이지 (기존 UI 재사용)
- 상세 페이지 상단에 "이 매장은 정확한 위치가 확인되지 않아 소속 시장 위치로 표시됩니다" 안내 (선택)

## Backend BBOX API 대응

### 현재 (Gate 1)
- `/api/v1/merchants/map?north&south&east&west` — 개별 매장 반환
- Gate 4 canonical 반영 후에도 이 endpoint 는 유지 (정확 좌표 매장은 개별로 반환)

### Gate 4 이후 추가 검토
- **신규 `/api/v1/markets/map`** — `location_precision = market_level` 매장을 시장별로 집계한 응답
  - `{ marketName, centroidLat, centroidLng, merchantCount, sampleMerchants[3], supportsPaper, supportsDigital, ... }`
  - iOS 는 이 endpoint 로 시장 마커를 그리고, 필요 시 개별 매장 endpoint 로 fetch

### Endpoint 분리 이유
- 지도 zoom 별로 다른 API 를 호출해 응답 크기 · 렌더링 부담 분산
- market-level 매장 (~55%) 을 개별 매장 API 에 섞어 반환하면 클라이언트가 필터링 부담

## 정확 좌표로 승격되는 경로

한 매장이 처음에 `market_level` 로 등장했다가 나중에 개별 좌표를 확보하면 자연스럽게 개별 마커로 전환된다:

```
Onnuri raw insert (Gate 3-B1)
     ↓  Gate 4 canonical merge
merchants.location_precision = market_level
     ↓  (미래) Kakao / KOMSCO / manual 로 정확 좌표 확보
merchants.location_precision = exact
     ↓
iOS 지도에서 개별 마커로 표시 (시장 마커의 count 에서는 빠짐)
```

## 데이터 신뢰도 관련 문구 (스펙 §12 DEMO 정책 연장)

- 지도 상단·상세 페이지에 "DEMO" 뱃지는 실 공공데이터 도입 후 조정 검토
- 시장 centroid 표시 매장은 "위치 근사" 뱃지 또는 시각적 구분 필요 (Gate 4 UI 작업)

## 완료 체크리스트 (Gate 4)

- [ ] Migration `0003_add_location_metadata.py` — merchants 에 `location_source / precision / confidence` 3필드 추가
- [ ] Onnuri canonical merge 시 시장 매핑 → `market_level` 로 저장
- [ ] Backend `/api/v1/markets/map` 신규 endpoint
- [ ] Backend `MerchantOut` schema 에 3필드 추가
- [ ] iOS `Merchant` model 에 3필드 추가
- [ ] iOS 지도 렌더링 분기 (`market_level` 매장 → 시장 마커에 흡수)
- [ ] iOS 매장 상세에 "위치 근사" 안내
- [ ] DEMO 정책 재검토

## 관련 문서

- `docs/LOCATION_PRECISION.md` — 데이터 모델 상세
- `docs/DATA_PIPELINE.md` (Gate 4 이후 예정) — 전체 파이프라인
- `LocalPayiOS/CLAUDE.md` — iOS 도메인 모델 규칙
