# 11. Phase 13 Gate 3-B1 — Onnuri 안양 Raw 저장 완료

- 보고일: 2026-08-14
- 이전 커밋: `bad14f9 feat(onnuri): market-level coord mapping`
- 상태: **완료. Raw 1,251건 저장. Idempotent 검증. canonical/dummy/iOS/Kakao 무변경.**

## 한 줄 요약

Alembic 0002 migration 을 VPS production DB 에 적용해 raw/source/import/geocode 5개 테이블 생성 후, 온누리 안양 매장 1,255건을 `raw_onnuri_merchants` 에 저장했다. `row_hash + UNIQUE(source_snapshot_date, row_hash)` 로 idempotent 보장 (같은 CSV 재실행 → inserted=0). `data_import_runs.run_metadata` 에 SHA-256·discrepancy 등 원본 무결성 메타 전부 기록. **canonical `merchants` 무변경 (25건 그대로) · iOS 무변경 · Kakao 호출 0**.

## Migration
- **before revision**: `0001_initial`
- **after revision**: `0002_raw_and_source_tables (head)`
- **created tables**: `data_import_runs`, `raw_onnuri_merchants`, `raw_local_currency_merchants`, `merchant_sources`, `geocode_queue`
- **created indexes**: 10 (GIST 없음 — 시장 좌표는 canonical 미반영, geocode_queue 는 status/source_raw)
- **downgrade verified**: 각 테이블 `def downgrade()` 대칭 drop, `merchants/reviews/payment_verifications` 무영향
- **destructive**: 없음 (기존 테이블 무변경, ALTER 없음)

## Import
- **source file**: `소상공인시장진흥공단_전국 온누리상품권 가맹점 현황_20250731.csv` (컨테이너에 `/tmp/onnuri.csv` 로 복사)
- **source hash (SHA-256)**: `8f97cf9cc7bb744b9b06637ac271cd8435b41cd1917defd05103ebd01a728692`
- **source rows**: 150,541
- **Anyang raw inserted (1차)**: **1,251**
- **skipped (1차)**: 4 (안양 매장 안 exact 중복 4건)
- **invalid (parse skip)**: 41 (이름/주소 결측)
- **duplicate prevented (2차 재실행)**: 1,255 (row_hash + UNIQUE 로 완전 skip, DB row count 그대로 1,251 유지)

## Import Run
- **run 1**: status=`succeeded`, fetched=150,541, parsed=150,500, inserted=1,251, skipped=4, error=0
- **run 2** (idempotent 검증): status=`succeeded`, inserted=0, skipped=1,255, error=0
- 두 run 모두 `run_metadata.row_count_discrepancy = true` 기록

`data_import_runs.run_metadata` 저장된 필드 (스펙 §1 준수):
- `source_dataset_id` = "3060079"
- `source_filename` = "onnuri.csv"
- `source_snapshot_date` = "2025-07-31"
- `source_file_size` = 10,510,225
- `source_file_sha256` = 위 hash
- `parsed_row_count` = 150,541
- `invalid_row_count` = 41
- `exact_duplicate_groups` = 456
- `exact_duplicate_extra_rows` = 794
- `official_metadata_row_count` = 125,589
- `row_count_discrepancy` = true
- `region_filter` = "anyang"
- `imported_at` (테이블 column `started_at/finished_at`)

## Production
- **canonical merchants changed**: **NO** (여전히 25건, Dummy 유지)
- **Dummy 25 changed**: **NO**
- **merchant_reviews changed**: NO (21건)
- **merchant_payment_verifications changed**: NO (32건)
- **iOS changed**: **NO** (Gate 1 상태 그대로, HTTPS 도메인 · 지도 · 검색 · 즐겨찾기)
- **Kakao API 호출**: **0** (시장 사전으로 대체됨)
- **BG Company · Traefik · Hermes**: 무변경

## Location
- **exact merchant coordinates**: **0** (canonical merchants 에 신규 raw 좌표 반영 안 함)
- **market-level coordinate candidates**: **1,255** (raw_onnuri_merchants 안, 시장 사전으로 매핑 가능한 규모)
- **location precision policy documented**: **YES** (`docs/LOCATION_PRECISION.md`)
- **map UX policy documented**: **YES** (`docs/MAP_UX_TODO.md`)

시장 centroid 좌표는 Gate 4 canonical merge 이전 `location_source=market_dataset`(전통시장 5개) 또는 `market_centroid_manual`(상점가 7개), `location_precision=market_level`, `location_confidence=0.7–0.8` 로 저장할 예정. **개별 매장 마커로 사용 금지.**

## Row discrepancy
- **official metadata**: 125,589
- **actual parsed**: 150,541
- **exact duplicate adjusted**: 149,747 (=150,541 − 794 extra)
- **status**: **UNRESOLVED**. Raw 는 원본 보존 목적으로 저장하되, canonical import 시 이 discrepancy 규명이 신뢰성 검증 항목으로 유지 (스펙 §1).

## Tests
- **total**: 111
- **passed**: 111
- **failed**: 0
- writer.py 자체 (asyncpg 필요) 통합 검증은 컨테이너 안에서 실 실행으로 대체됨. 두 번 실행하여 idempotent 검증까지 통과.

## 신규 파일
| 종류 | 파일 |
|---|---|
| 신규 | `worker/importers/onnuri/writer.py` — asyncpg 트랜잭션 · row_hash idempotent |
| 신규 | `docs/LOCATION_PRECISION.md` — location_source/precision/confidence 메타 설계 |
| 신규 | `docs/MAP_UX_TODO.md` — 시장 대표 마커 UX 원칙, 개별 마커 금지 |
| 신규 | `LocalPayiOS/report/11_Phase13_Gate3B1.md` (본 문서) |
| 수정 | `worker/cli.py` — `--dry-run` / `--write` mutually exclusive, `--snapshot-date`, `--official-metadata-rows` |

## Git
- **commits** (2026-08-14):
  - `17efb08 feat(onnuri): --write mode + idempotent raw insert + import_runs metadata (Gate 3-B1)`
  - (이번 문서 커밋 예정)
- **push**: `bad14f9..17efb08 main -> main` 완료, 문서 커밋 후 별도 push

## Gate 3-B2 recommendation

**Gate 3-B2 (canonical merge)** 로 넘어가기 전 아래 3가지 선결 필요:

1. **Row count discrepancy 규명** (150,541 vs 125,589) — 공공데이터포털 Q&A 문의 또는 재다운로드 비교. 규명 없이 canonical import 는 신뢰성 검증 실패
2. **Migration `0003_add_location_metadata.py`** 초안 — merchants 테이블에 `location_source`, `location_precision`, `location_confidence` 3필드 추가 (nullable, 기존 25건은 dummy_seed/exact/1.0 backfill)
3. **Canonical merge 정책 확정**:
   - Onnuri raw 1,251건 → canonical merchants 어떻게 병합? (id 규칙 · dedup 우선순위 · location_source 설정)
   - Dummy 25 유지 vs 데이터 소스 표시 (`data_source=dummy` 필터)
   - Gate 4 dedup (name/address/phone/coord) 는 Onnuri 만으로는 address 가 시도만 있어 dedup 신뢰도 낮음 → Gate 2 (지역화폐) 이후 통합 dedup 이 자연스러움

## Rollback (필요 시)
```bash
# 1. raw 데이터만 삭제 (컨테이너 안, PostgreSQL)
docker exec localpay-db psql -U localpay -d localpay -c "
  DELETE FROM raw_onnuri_merchants;
  DELETE FROM data_import_runs WHERE source='onnuri';
"

# 2. 또는 migration downgrade (5개 테이블 전체 drop)
docker exec localpay-api alembic downgrade 0001_initial
# → merchants/reviews/payment_verifications 및 Dummy 25 무영향
```

## Remaining
1. Row count discrepancy 대응 결정
2. Gate 3-B2 진행 여부 (canonical merge + location metadata migration)
3. Gate 2 (지역화폐) blocker 해결 방향 결정
4. Gate 4 (통합 dedup) 는 Gate 2/3 raw 다 확보 후
