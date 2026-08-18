# 13. Phase 13 Gate 3-C — 안양 온누리 실 데이터 Pilot

- 보고일: 2026-08-18
- 이전 커밋: `9aa985c docs(report): Phase 13 Gate 3-B2 완료 보고`
- 상태: **완료. 안양 canonical 1,251 저장 · Market Marker UX · Dummy 제외 · iOS Simulator 정상.**

## 한 줄 요약

Migration 재현성 fix (seed 에 location metadata 세팅), 온누리 canonical 1,251 건을 idempotent 하게 저장 (`merchants.source='onnuri-snapshot-2025-07-31'`, `location_precision='market_level'`), `merchant_sources` 로 raw ↔ canonical trace 유지. Backend 는 기본으로 Dummy 25 를 사용자 API 에서 제외하고 `market_level` 매장을 `/api/v1/merchants/map` 에서 제외 → 새 `/api/v1/markets/map` · `/api/v1/markets/{id}/merchants` 로 시장 대표 마커 + 매장 리스트 UX 제공. iOS 는 지도에 개별 매장 마커와 시장 대표 마커를 병렬 렌더링하고 시장 마커 탭 시 하단 sheet 로 매장 리스트 표시.

## Migration Reproducibility
- **issue**: Migration 0003 `upgrade()` 안의 `UPDATE merchants SET location_source='dummy_seed' WHERE source='seed-anyang-v1'` 이 apply 시점에 결과 0 rows 로 남았음 (원인 미확정 — alembic transactional 특성 또는 seed 순서 이슈)
- **fix**: `backend/app/seed/run_seed.py` 가 각 매장 생성 시 `location_source='dummy_seed', location_precision='exact', location_confidence=1.0` 을 명시적으로 설정. Migration UPDATE 는 안전장치로 유지
- **fresh DB migration**: `localpay_test` DB 로 격리 실험 → 0001 → 0002 → 0003 + seed = **25 rows with (dummy_seed / exact / 1.0)** 완전 재현

## Canonical
- **Onnuri inserted**: **1,251**
- **skipped**: 0 (첫 실행), 1,251 (재실행 idempotent 검증)
- **source links**: **1,251** (canonical merchant ↔ raw_onnuri_merchants 1:1)
- **Dummy**: **25** (그대로 유지, `dummy_seed` 표시)
- **duplicates (id)**: **0**
- 총 canonical: **1,276** (1,251 onnuri + 25 dummy)

## Market Groups
- **count**: **12** 시장/상점가
- **merchant total**: 1,251
- **largest groups**: 안양중앙인정시장 269 · 평촌1번가 상점가 218 · 안양1번가 상점가 143 · 안양일번가 지하쇼핑몰 137 · 안양남부시장 114 · 안양관양시장 108

## API
- **market map** (`/api/v1/markets/map`): 12 시장, BBOX + category + payment 필터, `merchantCount / paperCount / digitalCount` 필드
- **market list** (`/api/v1/markets/{id}/merchants`): paginated, q/category/payment 필터
- **search**: 실 데이터 검색 확인 — "약국" → 수약국·대명약국·대웅약국·독일약국·라라약국, "짬뽕" → 짬뽕타임·무비짜장짬뽕·미림양꼬치짬뽕
- **detail**: `/api/v1/merchants/{id}` 에 `locationSource / locationPrecision / locationConfidence` 필드 반환
- **dummy exclusion**: `/api/v1/merchants*`, `/api/v1/search` 기본 제외, `?include_dummy=true` 로 명시 시 포함
- **BBOX (`/api/v1/merchants/map`)**: `market_level` 매장 기본 제외 → 시장 마커로 이관, `?include_market_level=true` 로 fallback

## iOS
- **Market marker**: `MarketMarker.swift` (상점 아이콘 + count 라벨)
- **Market list**: `MarketDetailSheet.swift` sheet + `MarketMerchantsViewModel` → `/markets/{id}/merchants` fetch. medium/large presentation
- **Search**: 기존 `/api/v1/search` 는 자동으로 실 데이터 검색 (backend 가 dummy 제외 처리)
- **Detail**: 기존 `MerchantDetailView` 사용. locationPrecision 필드는 model 에 있음 (UI 표시는 sheet 상단 안내 문구로 대체: "이 위치는 …시장 대표 좌표 기준입니다")
- **Physical Device**: 사용자 검증 필요 (아래 §실기기 안내)
- **Dummy visible**: **아니오** — backend 가 API 에서 자동 제외

## Location
- **exact**: 25 (Dummy seed)
- **market_level**: 1,251 (Onnuri canonical, 12개 시장에 분포)
- **UI disclosure**: `MarketDetailSheet` 상단에 안내 문구
  > "이 위치는 {시장명} 대표 좌표 기준입니다. 개별 매장의 정확한 위치와 다를 수 있습니다."

## Snapshot
- **source**: 소상공인시장진흥공단_전국 온누리상품권 가맹점 현황 (Dataset 3060079)
- **date**: 2025-07-31
- **discrepancy status**: **OPEN** (150,541 vs 125,589, docs/LOCAL_CURRENCY_API_BLOCKER 아니라 raw 저장 metadata 에 유지). 전국 canonical import 이전 규명 필수

## Tests
- **backend**: 기존 통과 (신규 canonical writer 로직은 실 실행으로 검증 — idempotent 재실행 완전 성공)
- **iOS**: 기존 통과 + `MarketAggregate` Codable + 지도 병렬 fetch 정상 로그 (`markets=1 merchants=0`)

## Git
- **commits** (2026-08-18):
  - `e5f2a6d fix(seed): set location_source/precision/confidence on Dummy 25 (재현성 fix)`
  - `dfc5daa feat(gate3c): canonical writer + markets API + dummy exclusion`
  - `706a131 fix(worker): canonical-write* modes do not require --file`
  - `0acaa7a fix(canonical_writer): savepoint per-record + diagnostic + cast NULL floats`
  - `8b6d6a9 feat(ios): market marker + bottom sheet + Merchant location metadata (Gate 3-C)`
  - `<HEAD> docs(report): Phase 13 Gate 3-C 완료 보고`
- **push**: `9aa985c..0acaa7a` 완료, iOS · docs 커밋은 이번 push 로 반영

## Production 무변경 확인 (금지 사항)
- ❌ 전국 Onnuri canonical import — 안양만
- ❌ 지역화폐 full fetch
- ❌ Kakao Local 호출 (0)
- ❌ Gate 4 cross-source dedup
- ❌ Dummy hard delete — 25 유지, source='seed-anyang-v1' 필터로 제외
- ❌ BG Company 변경 — 무재기동

## Rollback (필요 시)
```bash
# 1. Onnuri canonical 만 삭제 (Dummy 25 무영향)
docker exec localpay-db psql -U localpay -d localpay -c "
  DELETE FROM merchant_sources WHERE source_type='onnuri';
  DELETE FROM merchants WHERE source LIKE 'onnuri-snapshot-%';
"
# 2. 필요 시 raw_onnuri_merchants 도 삭제 (canonical writer 재실행으로 복원 가능)
```

## Next
1. **Row count discrepancy 규명** (150,541 vs 125,589) — 전국 canonical import 이전 필수
2. **실기기 검증** — 사용자 iPhone 에서 안양 지도 진입 → 시장 마커 12개 → 탭 → 매장 리스트 확인
3. **Gate 4 (cross-source dedup)** — 지역화폐 Gate 2 재개 후 통합 dedup 자연스러움
