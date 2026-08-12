# 09. Phase 13 Gate 2-A — 지역화폐 안양 Sample Dry-Run

- 보고일: 2026-08-12
- 이전 커밋: `ef57740 docs(report): Phase 13 Gate 1 완료 보고 (BBOX + Search)`
- 상태: **완료. Production DB 무변경. Service Key 대기 상태.**

## 한 줄 요약

한국조폐공사 통합 지역화폐 가맹점 API (Dataset 15119539) 를 안전하게 호출·정규화하는 워커 파이프라인 (`worker/` 신규) 을 완성하고, fixture 기반 dry-run 으로 fetch → parse → normalize → quality report 흐름을 검증했다. **운영 DB 는 어떤 쓰기도 발생하지 않았고**, 실 API 호출은 사용자 서비스 키 발급 후 VPS `.env` 에 값이 세팅되면 즉시 가능하다.

## Official API

- **Dataset**: `15119539` 한국조폐공사_통합_가맹점기본정보
- **Endpoint**: `GET http://apis.data.go.kr/B190001/localFranchisesV2/franchiseV2`
- **Auth**: query param `serviceKey` (소문자 s)
- **Pagination**: `pageNo` / `numOfRows`
- **Region filter**: 사용처지역코드 5자리 (시도 2 + 시군구 3) 또는 읍면동코드 8자리. 안양 만안구 `41171`, 동안구 `41173`
- **Rate limit**: 개발계정 10,000/일. 운영계정은 활용사례 등록 시 신청
- **Update frequency**: 공공데이터포털 상 갱신주기 미표기 (수정일: 2025-12-04 기준)
- **주요 응답 필드 (문서 기재)**: 가맹점명, 대표전화번호, 주소, 위경도, 사업자 상태, 표준산업분류코드
- 실 JSON 필드명은 완전 공개되지 않아 parser 가 관대한 alias 사용 (`frcsNm`/`frcNm`/`mrhstNm`/`가맹점명` 등). 실 응답 확인 후 축소 커밋 예정

전체 스펙 · 활용신청 절차: [`docs/PUBLIC_DATA_SETUP.md`](../../docs/PUBLIC_DATA_SETUP.md)

## Service Key

- **configured**: **NO** (VPS `/opt/localpay/deploy/.env` 에 `DATA_GO_KR_SERVICE_KEY` 미설정)
- **git exposure**: 없음. `.env` 는 gitignored, `.env.example` 에만 `CHANGE_ME` placeholder 추가
- 실 API 호출은 사용자가 활용신청 · 인증키 발급 · VPS `.env` 세팅한 뒤에만 가능

## Anyang Dry-Run (fixture 기반)

Service Key 미설정 상태라 파이프라인 검증을 위해 fixture 로 실행:

| 항목 | anyang-manan | anyang-dongan |
|---|---|---|
| requested | 100 | 100 |
| fetched (fixture) | 9 | 9 |
| parsed | 9 | 9 |
| API calls | 0 (fixture) | 0 (fixture) |

### Coordinates
- valid: **5**
- missing: 1 (좌표 필드 자체 없음)
- invalid: 2 (`zero-zero` 1건, `out-of-range` 1건)

### Merchant Name
- valid: 8
- empty: 1 (드롭됨)

### Address
- valid: 9
- empty: 0

### Phone
- present: 6
- missing: 3

### Industry
- mapped: 7
- unmapped: 1 (`etc`)

### Business Status
- 정상영업: 6
- 휴업: 1
- unknown: 1

### Category 매핑 (검증)
- food: 1 (KSIC 47211)
- pharmacy: 2 (KSIC 47811, 47812)
- cafe: 2 (KSIC 56220)
- restaurant: 1 (KSIC 56111)
- beauty: 1 (KSIC 96112)
- etc: 1 (KSIC 99999 unmapped)

## Sample Merchants (fixture, 개인정보/실키 없음)

1. 안양중앙시장 행복정육점 | 경기 안양시 만안구 만안로 232 | (37.3946, 126.9235) | food | 정상영업
2. 평촌우리약국 | 경기 안양시 동안구 평촌대로 145 | (37.3893, 126.9812) | pharmacy | 정상영업
3. 안양착한카페 | 경기 안양시 동안구 시민대로 250 | (37.3956, 126.9573) | cafe | 정상영업
4. 범계할머니칼국수 | 경기 안양시 동안구 관양로 88 | (37.3901, 126.9887) | restaurant | 정상영업
5. 지점없는집 | 경기 안양시 만안구 어딘가 | (좌표 zero-zero 거부) | cafe | 휴업
6. 좌표없는가게 | 경기 안양시 만안구 안양로 100 | (좌표 없음) | beauty | 정상영업
7. 잘못된좌표가게 | 경기 안양시 동안구 어디로 50 | (out-of-range 거부) | pharmacy | 정상영업
8. 빈이름테스트 | 경기 안양시 동안구 시민대로 10 | (37.4, 126.95) | etc | unknown

## Tests

- **total**: 32
- **passed**: 32
- **failed**: 0
- 커버:
  - `category_mapper` (KSIC 접두 매칭 · unmapped → etc)
  - `parser` (관대한 field alias · missing 필드)
  - `normalizer` (name/address 빈 값 drop · phone 형식 · 좌표 zero-zero · 좌표 missing · 좌표 out-of-range · unmapped industry)
  - `client._extract_items` (SERVICE_KEY_IS_NOT_REGISTERED_ERROR · resultCode!=00 · items list/dict/single-dict)
  - `WorkerConfig.__repr__` masking (실키 노출 방지)
  - `http_client._mask_url` (`serviceKey`/`ServiceKey`/`apiKey` 마스킹)

## VPS

- **disk**: 96 GB (32% 사용, 이전과 동일. worker fixture 만 로컬 실행이라 VPS 무영향)
- **memory**: 7.8 GB (변화 없음)
- **impact to BG Company**: **0**. 이번 Gate 는 VPS 컨테이너 재기동 · Docker 조작 · Traefik 수정 없음

## DB

- **production migration**: **없음** (스펙 §12 준수, Gate 2-B 승인 대기)
- **production writes**: **없음** (dry-run 만)
- **dummy status**: 25개 그대로 유지, `data_source` 컬럼 미도입

## Git

- **commits** (예정):
  - `feat(data): add local currency raw importer skeleton (Gate 2-A)`
- **push**: 예정. secret scan 통과 후

## Gate 2-B Proposed Changes (사용자 승인 필요)

Gate 2-B 는 실 API 응답을 실제 DB 에 반영하기 시작하는 단계.

- **migration**: `0002_raw_sources_import_runs.py`
  - `raw_local_currency_merchants` (JSONB raw_payload 포함)
  - `merchant_sources` (canonical ↔ raw 매핑, `source_type` / `source_provider` / `confidence`)
  - `data_import_runs` (배치 추적, status enum)
- **raw table**: 위 migration
- **import run**: `--write` 모드 CLI (기본은 여전히 `--dry-run`)
- **canonical merge**: Gate 4 이후 별도 진행 (Gate 2-B 는 raw 저장까지만)

### 사용자 승인 원칙
- 안양 실 API 100~500건 dry-run 재검증 (parser alias 축소)
- Migration 적용 (alembic upgrade head)
- Raw table 저장까지만 수행. **canonical merchants 는 아직 안 만짐**
- iOS 는 여전히 Dummy 25개만 표시

## User approval required

**YES**

다음 작업 중 하나라도 진행하려면 사용자 명시 승인 필요:
1. VPS `/opt/localpay/deploy/.env` 에 `DATA_GO_KR_SERVICE_KEY` 세팅 (사용자 본인이 활용신청 · 발급 · 입력)
2. Alembic migration `0002` 작성 · 적용
3. `--write` 모드 CLI 추가
4. Raw table 최초 저장

**정지 지점**: 스펙 §31 대로 Gate 2-A 는 여기서 종료. Gate 2-B 로 넘어가지 않음. Gate 3 온누리도 시작하지 않음.

## User action required

### 사용자 액션 1 — 공공데이터포털 활용신청

1. [공공데이터포털 로그인](https://www.data.go.kr)
2. [Dataset 15119539 페이지](https://www.data.go.kr/data/15119539/openapi.do) → **활용신청** → 개발계정
3. 승인 후 마이페이지 → 오픈API → 인증키 관리에서 **일반 인증키 (Decoding)** 복사
4. VPS 에 값 입력:
   ```bash
   ssh localpay-vps
   sudo nano /opt/localpay/deploy/.env
   # 마지막 줄 DATA_GO_KR_SERVICE_KEY=... 에 방금 복사한 값 붙여넣기
   ```
5. 값 노출 없이 세팅 확인:
   ```bash
   ssh localpay-vps '
   grep -q "^DATA_GO_KR_SERVICE_KEY=..*" /opt/localpay/deploy/.env \
     && echo CONFIGURED || echo MISSING'
   ```
6. Claude 에게 "Service Key 설정 완료" 알려주기 → Gate 2-B 진입 승인 여부 결정

### 사용자 액션 2 — Gate 2-B 진행 여부 결정

승인하시면:
- Gate 2-B: migration + raw table + 실 API 100건 저장 + parser alias 축소 커밋
- 그 후 별도 세션에서 Gate 3 (온누리), Gate 4 (dedup), Gate 5-6 (전국) 순차 진행

승인 안 하시면 여기서 완전 정지.

## Remaining

1. Service Key 발급 후 실 API 응답 스키마 확인 → parser alias 축소
2. Gate 2-B (migration + raw insert) — 사용자 승인 후
3. Gate 3 (온누리 CSV) — Service Key 무관, 파일 다운로드 필요
