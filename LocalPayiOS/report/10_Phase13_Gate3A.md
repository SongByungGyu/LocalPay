# 10. Phase 13 Gate 3-A — 온누리 안양 Sample Dry-Run

- 보고일: 2026-08-13
- 이전 커밋: `a1996bd fix(data): normalize URL-encoded serviceKey ...`
- 상태: **완료. Production DB 무변경. 사용자 파일 다운로드 대기.**

## 한 줄 요약

소상공인시장진흥공단 전국 온누리상품권 가맹점 현황 CSV 를 안전하게 파싱·정규화하는 워커 파이프라인 (`worker/importers/onnuri/`) 을 완성하고, fixture 로 파이프라인 · 안양 필터 · 카테고리 매핑 · 좌표 부재 통계까지 검증했다. 사용자가 실 파일을 [Dataset 3060079](https://www.data.go.kr/data/3060079/fileData.do) 에서 다운로드해서 `data/import/onnuri/` 에 배치하면 즉시 실 안양 sample dry-run 이 가능하다.

## Gate 2 (Local Currency)

- **status**: **BLOCKED**
- **reason**: KOMSCO 통합 API (Dataset 15119539) 지역 요청 필터 파라미터 미확인. 11가지 이름 시도 전부 810만 건 전국 반환. 참고문서는 코드표 xlsx 하나만 공개
- **next action**: `docs/LOCAL_CURRENCY_API_BLOCKER.md` 참조. Q&A 문의 / 표준데이터셋 15100062 / 개별 API 중 사용자 결정 대기. **개발계정으로 전국 810만 Full Fetch 금지**

## Onnuri Official Source (2026-08-13 웹 확인)

- **dataset**: `3060079` 소상공인시장진흥공단_전국 온누리상품권 가맹점 현황
- **latest snapshot**: `소상공인시장진흥공단_전국 온누리상품권 가맹점 현황_20250731`
- **기준일**: 2025-07-31 (다음 등록 예정: 2026-08-12, 오늘 자정 기준 미표기)
- **file format**: CSV (open API 는 XML/JSON)
- **source rows**: 125,589 (공식 표기)
- **encoding**: 페이지 미표기. worker parser 가 utf-8-sig → utf-8 → cp949 → euc-kr 순 자동 감지
- **column header** (7개):
  1. 가맹점명
  2. 소속 시장명(또는 상점가)
  3. 소재지
  4. 취급품목
  5. 지류형 가맹 여부
  6. 디지털형 가맹 여부
  7. 등록년도
- **좌표**: **없음** (지도 노출 위해 별도 geocoding 필요)
- 로그인 없이 다운로드 · 무료 · 이용허락 제한 없음

## 파일 확보 방식

원본 CSV 는 대용량이고 재배포 지양 원칙에 따라 git 에 커밋하지 않는다.

- 사용자 액션: [Dataset 3060079](https://www.data.go.kr/data/3060079/fileData.do) 에서 파일 다운로드
- 파일 위치: `data/import/onnuri/소상공인시장진흥공단_전국 온누리상품권 가맹점 현황_20250731.csv`
- `.gitignore` 확장: `data/import/`, `소상공인시장진흥공단_*.csv`, `onnuri_*.csv`

## Anyang (fixture 기반 검증 결과)

Service 파일 대신 `worker/tests/fixtures/onnuri_sample.csv` (13행) 로 검증:

| 항목 | 값 |
|---|---|
| source_rows | 13 |
| parsed_ok | 12 |
| invalid_rows | 1 (이름/주소 결측) |
| anyang_total | 9 |
| Manan | 4 |
| Dongan | 5 |
| unknown | 0 |

### Anyang 필드 완성도
- name_valid=9, address_valid=9, products_present=8

### Anyang Payments (동일 매장이 paper+digital 둘 다 지원 시 both 로 별도 카운트)
- paper: 6 (both 포함)
- digital: 5 (both 포함)
- both: 2
- neither: 0

### Anyang Products
- available: 8
- missing: 1 (원본 취급품목 필드 empty)

### Anyang Category
- market: 3 (시장 이름 매치 최우선)
- restaurant/pharmacy/cafe/food/beauty/life: 각 1
- etc: 0
- **source**: market_name 3건, product_keyword 6건, default 0

### Anyang Coordinates
- valid: 0
- missing: 9
- invalid: 0
- **geocode_required: 9 / 9 (100%)** — 온누리 원본은 좌표 미제공. 지도 노출 위해 Kakao Local 등 geocoding 필요 (Gate 4 이후 별도 결정)

### Quality
- invalid rows: 1
- duplicate name candidates: 0

## Dry Run

- **production DB writes**: **0**
- **production migration**: **없음** (Gate 3-A 는 스켈레톤·검증 단계, 스펙 §27)

## Tests

- **total**: 83
- **passed**: 83
- **failed**: 0
- 신규 (온누리) 34건 커버:
  - header alias 매핑 (공식 · 약식 표기)
  - encoding 자동 감지
  - iter_records 전체 yield
  - Y/N 파싱 (Y/N/O/X/있음/없음/가능/불가/가맹/미가맹/1/0/unknown)
  - year 파싱 (년/월일/범위밖)
  - products split (comma/slash/pipe, dedup)
  - anyang classify (만안/동안/unknown/None)
  - normalize edge case (이름/주소 결측 drop)
  - category mapper (시장명 · 상품 키워드)
  - dry-run report (anyang 통계 · 좌표 부재 · duplicate)

## VPS

- **source file size**: N/A (아직 VPS 업로드 X)
- **disk impact**: 0
- **memory impact**: 0
- 이번 Gate 는 로컬 개발 환경 (mac + .venv-worker) 에서만 실행. VPS 무영향
- BG Company · Traefik · Docker volume · iOS 무영향

## Git

- **commits** (예정):
  - `docs(data): document KOMSCO regional filter blocker`
  - `feat(data): add Onnuri snapshot parser and dry-run pipeline`
- **push**: 예정

## Gate 3-B Proposal (사용자 승인 필요)

1. **Alembic migration `0002_raw_and_source_tables.py`**
   - `raw_onnuri_merchants` (JSONB raw_payload)
   - `raw_local_currency_merchants` (Gate 2 재개 대비)
   - `merchant_sources` (canonical ↔ raw 매핑, `source_type`/`source_provider`/`confidence`)
   - `data_import_runs` (배치 추적)
   - `geocode_queue` (온누리 pending 좌표)
2. **`--write` 모드 CLI 추가** (기본은 여전히 `--dry-run`)
3. **안양 실 파일 raw table 저장 검증** — 만안/동안 각 수백~수천 건 예상
4. **Canonical merge 는 Gate 4 별도** (dedup + confidence 검증 후)

### 좌표 정책 결정 (Gate 3-B 이전)
- Kakao Local REST API 검토 (안양 예상 좌표 필요 수 ×1건씩) — Q/D 대응
- 대안: 안양시 도로명 주소 → 시도별 정형 좌표 데이터셋 (표준지역코드) 매핑
- 온누리 표시할지 여부: 좌표 없이는 지도 노출 불가. 리스트 뷰만 지원할지 논의

## User approval required

**YES**

## User action required

### 액션 1 — 원본 CSV 다운로드
1. [Dataset 3060079 페이지](https://www.data.go.kr/data/3060079/fileData.do) 접속
2. 페이지 하단 "파일데이터" 섹션에서 **CSV** 다운로드
3. 로컬 저장소 하위 `data/import/onnuri/` 폴더 생성 후 다운로드된 파일 이동
   ```bash
   mkdir -p data/import/onnuri
   mv ~/Downloads/소상공인시장진흥공단_전국\ 온누리상품권*.csv data/import/onnuri/
   ```
4. Claude 에게 "파일 배치 완료" 알려주기 → 실 파일로 dry-run 재실행 → 안양 실제 건수·카테고리·품목 통계 확인

### 액션 2 — Gate 2 blocker 대응 선택
`docs/LOCAL_CURRENCY_API_BLOCKER.md` 후속 옵션 중 선택 (Q&A 문의 / 표준데이터셋 15100062 / 개별 API / 지역화폐 보류).

## Remaining

1. 사용자 파일 다운로드 → 실 안양 sample dry-run
2. Gate 3-B (migration + raw insert + geocoding 정책) — 사용자 승인 후
3. Gate 4 (Dedup + Canonical Merchant)
4. Gate 2 재개 조건 확립
