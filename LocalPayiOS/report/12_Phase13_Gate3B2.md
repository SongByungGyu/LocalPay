# 12. Phase 13 Gate 3-B2 — Location Metadata Migration + Canonical Dry-Run

- 보고일: 2026-08-18
- 이전 커밋: `20095fe docs(report): Phase 13 Gate 3-B1 완료 보고`
- 상태: **완료. Migration 0003 apply · Dummy 25 backfill · Onnuri canonical 1,251 dry-run 성공. canonical merchants INSERT 0.**

## 한 줄 요약

Migration 0003 로 `merchants` 에 3개 location metadata 필드 (source/precision/confidence) 를 non-destructively 추가하고 Dummy 25건을 `dummy_seed/exact/1.0` 로 backfill 했다. `CanonicalMerchantCandidate` 변환기와 dry-run 파이프라인을 신설해 안양 raw 1,251건 전체를 canonical 후보로 변환하며, 12개 시장 aggregation (`/api/v1/markets/map` 후보) 을 완비했다. **canonical merchants 는 여전히 25건 · iOS · Kakao · Traefik · BG Company 무변경.**

## Migration 0003

**before revision**: `0002_raw_and_source_tables`  
**after revision**: `0003_add_location_metadata (head)`  

### 변경 내용 (Non-destructive)
- ADD COLUMN `merchants.location_source` VARCHAR(32) NULL
- ADD COLUMN `merchants.location_precision` VARCHAR(16) NULL
- ADD COLUMN `merchants.location_confidence` FLOAT NULL
- CHECK constraints (NULL 통과, 지정 enum 만):
  - `location_source ∈ {source_exact, market_dataset, market_centroid_manual, kakao_place, manual, dummy_seed}`
  - `location_precision ∈ {exact, approximate, market_level, region_level}`
  - `location_confidence ∈ [0.0, 1.0]`

### Downgrade 대칭
```
drop_constraint (3개) → drop_column (3개)
```

### Dummy 25 Backfill
Migration upgrade() 내 UPDATE 문 실행 안 됨 (원인: `alembic upgrade` 시 UPDATE 가 auto-commit 되지 않은 것으로 추정. 후속 조사 필요). **수동 UPDATE 로 backfill 완료**:
```
merchants WHERE source='seed-anyang-v1' → dummy_seed/exact/1.0  (25건)
```

## Backend Model / Schema
- `app/models/merchant.py`: 3필드 추가 (Mapped[Optional[...]], nullable=True)
- `app/schemas/merchant.py::MerchantOut`: `locationSource / locationPrecision / locationConfidence` optional camelCase alias
- 컨테이너 rebuild 완료. HTTPS 200 정상. iOS Merchant 도메인 무변경 (Gate 3-B2 는 backend 확장까지만)

## Canonical Candidate 변환기

`worker/importers/onnuri/canonical.py`:
- `CanonicalMerchantCandidate` — Backend MerchantOut · iOS Merchant 호환 dataclass
- `to_canonical()` — Raw + Normalized → Canonical
- **id 규칙**: `onnuri-a-{row_hash[:16]}` (idempotent · scoped · traceable)
- **Location metadata 자동 결정** (docs/LOCATION_PRECISION.md 준수):
  - 전통시장 5개 (안양중앙시장·중앙인정·남부·육동·관양) → `market_dataset / market_level / 0.8`
  - 상점가 7개 (안양1번가·일번가·중앙지하도·가구·농수산물·아크로·평촌1번가) → `market_centroid_manual / market_level / 0.7`
  - 매핑 없음 → `None / region_level / None` (지도 미노출)
- Payment YN → `["onnuriPaper", "onnuriDigital"]` list

## Canonical Dry-Run (DB raw 1,251 → candidate)

`worker/importers/onnuri/canonical_dryrun.py` + CLI `--canonical-dryrun --from-db` 로 실행:

| 항목 | 값 |
|---|---|
| input | `db:raw_onnuri_merchants` (snapshot 2025-07-31) |
| total_input_rows | 1,251 |
| normalized_ok | 1,251 |
| normalized_dropped | 0 |
| **canonical_generated** | **1,251** |
| coordinate_valid | 1,251 |
| coordinate_missing | 0 |
| unmappable_to_map | 0 |

### Location source 분포
- `market_dataset`: 564
- `market_centroid_manual`: 687

### Location precision 분포
- `market_level`: 1,251 (모두)

### Category 분포
- restaurant 338 · food 187 · beauty 55 · cafe 37 · pharmacy 32 · life 17 · mart 17 · etc 568

### 로컬 CSV vs DB raw 차이
- 로컬 CSV: 1,255 canonical (안양 매장)
- DB raw: 1,251 canonical (안양 매장 중 exact duplicate 4건 dedup 후 저장된 상태)
- 차이 4건 = writer 저장 시 UNIQUE(source_snapshot_date, row_hash) 로 걸러진 것 → 정합

## Market Aggregation Preview (/api/v1/markets/map 후보)

12개 시장/상점가 완전 aggregation:

| 시장/상점가 | count | paper | digital | both | (centroid) | source/conf |
|---|---:|---:|---:|---:|---|---|
| 안양중앙인정시장 | 269 | 269 | 239 | 239 | (37.39648, 126.91957) | market_dataset / 0.8 |
| 평촌1번가 상점가 | 218 | 218 | 218 | 218 | (37.39072, 126.98432) | market_centroid_manual / 0.7 |
| 안양1번가 상점가 | 143 | 143 | 143 | 143 | (37.40340, 126.92264) | market_centroid_manual / 0.7 |
| 안양일번가 지하쇼핑몰 | 137 | 137 | 136 | 136 | (37.40340, 126.92264) | market_centroid_manual / 0.7 |
| 안양남부시장 | 114 | 114 | 106 | 106 | (37.39593, 126.92496) | market_dataset / 0.8 |
| 안양관양시장 | 108 | 108 | 95 | 95 | (37.40522, 126.95931) | market_dataset / 0.8 |
| 안양중앙시장 | 72 | 72 | 58 | 58 | (37.39757, 126.91967) | market_dataset / 0.8 |
| 안양가구상점가 | 58 | 58 | 58 | 58 | (37.39620, 126.91850) | market_centroid_manual / 0.7 |
| 안양농수산물 골목형상점가 | 53 | 53 | 53 | 53 | (37.39525, 126.92466) | market_centroid_manual / 0.7 |
| 안양아크로상가골목형상점가 | 52 | 52 | 52 | 52 | (37.39485, 126.97673) | market_centroid_manual / 0.7 |
| 안양중앙지하도상가 | 26 | 26 | 25 | 25 | (37.39820, 126.92100) | market_centroid_manual / 0.7 |
| 안양육동시장 | 1 | 1 | 1 | 1 | (37.39059, 126.93022) | market_dataset / 0.8 |

## Production 무변경 확인
- **canonical merchants**: 25건 (Dummy) 그대로 · location metadata=`dummy_seed/exact/1.0` backfill
- **merchant_reviews**: 21건 무변경
- **merchant_payment_verifications**: 32건 무변경
- **raw_onnuri_merchants**: 1,251건 (Gate 3-B1 저장 그대로)
- **data_import_runs**: 2건 (Gate 3-B1 저장 그대로, 추가 배치 없음)
- **iOS**: 무변경
- **Kakao API 호출**: 0
- **Traefik · BG Company · Hermes**: 무변경 · 무재기동 (api 컨테이너만 rebuild)

## Tests
- **total**: 121
- **passed**: 121
- **failed**: 0
- 신규 (canonical) 10건: id stability · scope · location metadata enum · payment YN · market aggregation grouping · category count

## 문서
| 종류 | 파일 |
|---|---|
| 신규 | `docs/CANONICAL_CANDIDATE.md` — Candidate 설계 · id 규칙 · location metadata 결정 · Gate 4 이전 확정 필요 사항 |
| 신규 | `worker/importers/onnuri/canonical.py` |
| 신규 | `worker/importers/onnuri/canonical_dryrun.py` |
| 신규 | `worker/tests/test_canonical.py` (10건) |
| 신규 | `backend/alembic/versions/0003_add_location_metadata.py` |
| 수정 | `backend/app/models/merchant.py` (3필드) |
| 수정 | `backend/app/schemas/merchant.py::MerchantOut` (3필드) |
| 수정 | `worker/cli.py` (`--canonical-dryrun`, `--from-db`) |

## Git
- commits (2026-08-14 ~ 18):
  - `5870bb8 feat(db): migration 0003 add location metadata + Dummy 25 backfill`
  - `9d2a879 feat(canonical): CanonicalMerchantCandidate + dry-run + market aggregation`
  - (이번 문서 커밋 예정)
- push: `20095fe..9d2a879 main -> main` 완료, 문서 별도 push

## Gate 4 recommendation

Gate 4 (Dedup + Canonical Merchant INSERT) 진입 전 3가지 확정 필요:

1. **Dedup 정책**: name normalize + address (온누리는 시도만 있어 신뢰도 낮음) + phone (온누리 원본 없음) + coord (시장 centroid 는 정확도 낮음) → 실질적으로 온누리만 있으면 dedup 신뢰도 매우 낮음. **Gate 2 (지역화폐) 확보 후 통합 dedup 이 자연스러움**
2. **Traditional market vs 상점가 dict 분리**: 현재 `anyang_markets.py` 는 두 카테고리를 dict 로만 구분. canonical.py 상단의 `TRADITIONAL_MARKET_NAMES` 상수도 하드코딩 → 사전을 두 카테고리로 분리해 자동화
3. **Row count discrepancy 규명**: 여전히 미해결 (150,541 vs 125,589). canonical INSERT 이전 정합성 확인 항목

## Rollback (필요 시)
```bash
# 1. Migration 0003 downgrade (3필드 · CHECK 삭제, 데이터 무손실)
docker exec localpay-api alembic downgrade 0002_raw_and_source_tables
# → merchants 25건 유지, source/precision/confidence 컬럼만 사라짐

# 2. Backend model/schema 롤백 시 컨테이너 rebuild
```

## Remaining
1. Gate 4 (Dedup + Canonical INSERT) 진행 여부 결정 — Gate 2 확보 우선 여부
2. Row count discrepancy 규명 (Q&A · 재다운로드 비교)
3. Migration UPDATE 실행 안 된 원인 조사 (alembic transactional DDL 이슈)
