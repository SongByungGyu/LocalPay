# worker

LocalPay 실 데이터 수집·정규화·병합 파이썬 워커.

## 구조 (Phase 13 Gate 2-A 기준)

```
worker/
├── core/
│   ├── config.py          Env 로드. Service Key masking
│   └── http_client.py     Timeout/retry/backoff + secret URL masking
├── importers/
│   └── local_currency/
│       ├── client.py            KOMSCO 통합 API (Dataset 15119539) 호출
│       ├── parser.py            응답 → RawLocalCurrencyRecord (관대한 field alias)
│       ├── normalizer.py        Raw → Normalized (name/phone/addr/coord)
│       ├── category_mapper.py   KSIC → LocalPay MerchantCategory
│       ├── models.py            RawRecord / NormalizedRecord 데이터 클래스
│       └── importer.py          Dry-run 오케스트레이션 · Quality Report
├── cli.py                 python -m worker.cli ... entry point
└── tests/                 pytest (DB 불필요)
```

## 원칙

- **Service Key 는 오직 `.env` 환경변수** (`DATA_GO_KR_SERVICE_KEY`). 코드·git·로그·__repr__ 어디에도 원본 노출 금지 (`WorkerConfig.masked_key`, `http_client._mask_url` 사용).
- **좌표를 임의 생성하지 않는다.** 대한민국 대략 범위 (33~39 lat, 124~132 lng) 밖은 invalid, `(0,0)` 도 invalid.
- **불확실한 산업분류는 `etc`.** 추정 금지 (스펙 §14).
- **원본 payload 는 항상 보존** (`raw_payload` JSONB, DB 도입 시).

## 사용법 (Dry-Run only, Gate 2-A)

로컬 개발 (Key 없이 로직만 검증):

```bash
python3 -m venv .venv-worker
./.venv-worker/bin/pip install httpx==0.28.1 pytest==8.3.4

# 파이프라인 검증 (fixture)
./.venv-worker/bin/python -m worker.cli local-currency \
  --region anyang \
  --fixture worker/tests/fixtures/anyang_sample.json \
  --dry-run

# 유닛 테스트
./.venv-worker/bin/python -m pytest worker/tests -q
```

실 API 호출 (Service Key 발급 후 VPS):

```bash
# VPS 에서 (SSH_KEY 발급 · /opt/localpay/deploy/.env 에 DATA_GO_KR_SERVICE_KEY 세팅 완료 상태)
cd /opt/localpay
python3 -m worker.cli local-currency \
  --region anyang \
  --limit 100 \
  --dry-run
```

지원 region alias:
- `anyang` — 만안구 + 동안구 합쳐 각각 fetch
- `anyang-manan` — 41171
- `anyang-dongan` — 41173

`--dry-run` 은 **필수 옵션**. 이번 Gate 는 어떤 DB write 도 하지 않는다.

## Gate 2-B 이후 확장 계획 (사용자 승인 후)

- Alembic migration: `raw_local_currency_merchants`, `merchant_sources`, `data_import_runs`
- Importer 에 `--write` 모드 추가 (dry-run 반대)
- Canonical merchant 병합 (Gate 4 dedup)
- 전국 pagination (Gate 5 dry-run + Gate 6 실 실행)
- 온누리 snapshot importer (Gate 3)
- Kakao Local 좌표 보정 (`geocode_queue`)

## 참고

- `docs/PUBLIC_DATA_SETUP.md` — 공공데이터포털 활용신청 절차 · Service Key 관리
- `docs/DATA_PIPELINE.md` (Gate 4 이후 작성 예정) — Raw → Canonical 전체 파이프라인
- `LocalPayiOS/report/09_Phase13_Gate2A.md` — 이번 Gate 실행 결과
