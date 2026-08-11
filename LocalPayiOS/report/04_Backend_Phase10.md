# 04. Backend Phase 10 — FastAPI + PostGIS 1차 서버

- 보고일: 2026-08-11
- 커밋: `e31274c feat(backend): FastAPI + PostgreSQL/PostGIS 1차 서버 (Phase 10)`
- 상태: **회사 Mac 에서 소스 작성 · GitHub push 완료.** VPS 실행 검증은 다음 단계에서 수행

## 한 줄 요약

iOS Dummy MVP 와 완전히 호환되는 스키마의 FastAPI + PostgreSQL/PostGIS 서버를 monorepo `backend/` 로 추가하고, 기존 VPS BG Company 스택과 완전히 격리된 Docker Compose 배포 셋을 `deploy/` 로 만들었습니다. 25개 안양 매장은 iOS `DummyMerchantSeed.swift` 를 1:1 포팅하여 서버 seed 로 사용합니다.

## Phase 10 지표

| 항목 | 값 |
|---|---|
| 신규 파일 | 39 (backend 26 + deploy 3 + docs 2 + worker 1 + models/schemas/api 등 재분류) |
| Python 파일 문법 검증 | `python3 -m py_compile` 전부 통과 |
| Shell 검증 | `sh -n backend/entrypoint.sh` 통과 |
| YAML 검증 | `yaml.safe_load(deploy/docker-compose.yml)` 통과 |
| GitHub Push | ✅ `c0ec5df..e31274c main -> main` |
| Docker 로컬 실행 | ⛔ 회사 Mac 미검증 (VPS 에서 검증 예정) |

## 완성된 것

### 1. Backend 서버 (`backend/`)

FastAPI 앱, 6개 엔드포인트, iOS Domain 과 호환되는 camelCase 응답:

| Endpoint | 설명 |
|---|---|
| `GET /health` | liveness |
| `GET /db-health` | Postgres 왕복 + `PostGIS_Lib_Version()` |
| `GET /api/v1/merchants` | 목록 (`category`, `payment`, `limit` 필터) |
| `GET /api/v1/merchants/{id}` | 상세 (404 처리) |
| `GET /api/v1/merchants/nearby` | `ST_DWithin(geography)` — 정확한 미터 + `distanceMeters` 응답 필드 |
| `GET /api/v1/merchants/map` | `ST_Intersects` + `ST_MakeEnvelope` (BBOX) |

- 응답은 **iOS `Merchant`** 구조와 동일한 camelCase → 향후 `RemoteMerchantRepository` 에서 `JSONDecoder.decode([Merchant].self, from:)` 로 직행 가능
- 프로덕션(`ENV=production`)에서는 `/docs`, `/redoc`, `/openapi.json` 자동 비활성
- CORS 는 `CORS_ORIGINS` env 로 명시적 허용만 가능

### 2. DB Schema (Alembic 초기 마이그레이션)

- `CREATE EXTENSION IF NOT EXISTS postgis`
- `merchants` — GIST index on `geom(Point,4326)` + category / payment_flags / active_category indexes
- `merchant_reviews` (FK, CASCADE, CHECK rating 1~5)
- `merchant_payment_verifications` (FK, CASCADE)
- 모든 스키마 변경은 새 리비전으로 관리한다는 원칙을 `docs/DB_SCHEMA.md` 에 명시

### 3. Seed 데이터 (`backend/app/seed/`)

- `seed_data.py` — iOS `DummyMerchantSeed.swift` 를 그대로 포팅. 매장 ID 도 동일 (`m-001` ~ `m-025`)
- `run_seed.py` — truncate 후 재삽입. `python -m app.seed.run_seed` 로 CLI 실행
- 25개 매장 · 결제 조합 (온누리만/지역화폐만/둘 다/둘 다 미지원) · 카테고리 골고루 · 리뷰 + 최근 결제 인증 로그 포함
- 컨테이너 시작 시 `SEED_ON_START=true` 면 자동 실행

### 4. Docker (`deploy/`)

**격리 원칙 (BG Company 절대 침범 금지):**

| 구분 | 값 | 이유 |
|---|---|---|
| 컨테이너 | `localpay-api`, `localpay-db` | 이름 충돌 X |
| 네트워크 | `localpay_net` | 전용 |
| 볼륨 | `localpay_pg_data` | 전용 |
| API 포트 | `127.0.0.1:18080` → 8000 | 외부 접근 불가, localhost만 |
| Postgres 포트 | **호스트 미매핑** | 컨테이너 네트워크 내부만 |

- `deploy/README.md` 에 `docker compose down -v`, `docker system prune`, `docker volume prune` **금지** 명시
- `entrypoint.sh` 가 `alembic upgrade head → (seed) → uvicorn` 순으로 안전 부팅

### 5. 문서

- `backend/README.md` — 스택, 폴더, API, 실행 방법
- `deploy/README.md` — VPS 배포 절차 (git pull → up -d --build), 헬스체크, 위험 명령 금지 목록, SSH 터널 노출법
- `docs/API_SCHEMA.md` — v1 API 계약, `Merchant` JSON 예제, iOS 연동 스니펫, Error 표
- `docs/DB_SCHEMA.md` — 테이블/인덱스/spatial 규칙/마이그레이션 정책
- `worker/README.md` — Phase 11 계획 stub

### 6. 테스트

- `tests/test_health.py` — DB 무관 스모크 테스트
- Phase 11 에서 `/api/v1/merchants*` 통합 테스트 추가 예정 (테스트용 DB 컨테이너 필요)

## iOS 와의 호환성

- **JSON 필드명**: Pydantic `alias_generator=to_camel` + `populate_by_name=True` → 모두 camelCase. Swift `JSONDecoder` 기본 설정으로 디코드 가능
- **날짜**: ISO-8601. iOS 측에서 `dateDecodingStrategy = .iso8601` 필요 (API_INTEGRATION.md 에 이미 반영 필요 — 다음 iOS 세션에서 추가)
- **UUID**: Review/PaymentVerification 은 UUID string. Swift `UUID` 로 바로 디코드
- **매장 ID**: iOS Dummy 와 동일 (`m-001` ~ `m-025`) → iOS 즐겨찾기 · 리뷰가 서버 매장을 참조해도 매칭됨

## VPS 실행 · 검증 절차 (다음 단계)

```bash
# VPS
cd /opt/localpay
git status                  # clean 확인
git pull                    # e31274c 반영

cd deploy
cp .env.example .env        # 최초 1회
# POSTGRES_PASSWORD 를 강한 랜덤값으로 교체
# DATABASE_URL 안의 비밀번호도 동일하게 교체
vi .env

docker compose up -d --build
docker compose logs -f api  # migration + seed + uvicorn 정상 확인
```

검증 명령:

```bash
curl -sS http://127.0.0.1:18080/health
curl -sS http://127.0.0.1:18080/db-health
curl -sS "http://127.0.0.1:18080/api/v1/merchants?limit=3" | head -c 500
curl -sS "http://127.0.0.1:18080/api/v1/merchants/m-001"
curl -sS "http://127.0.0.1:18080/api/v1/merchants/nearby?lat=37.3946&lng=126.9235&radius=1500&limit=5"
curl -sS "http://127.0.0.1:18080/api/v1/merchants/map?north=37.40&south=37.38&east=126.98&west=126.92&limit=100"
```

Mac 에서 접근하려면 SSH 터널:

```bash
ssh -L 18080:127.0.0.1:18080 <vps-user>@<vps-host>
# 이후 Mac 브라우저에서 http://127.0.0.1:18080/health
```

## 알려진 한계 / TODO

- **로컬(회사 Mac) Docker 검증 없음** — Docker Desktop 미설치. VPS 에서 최초 검증
- **DB 통합 테스트 미작성** — 헬스 스모크만. Phase 11 에서 test DB 컨테이너로 확장
- **인증 없음** — 공개 read-only API. Phase 12 에서 Bearer 토큰 도입
- **CORS 기본값 비어있음** — 브라우저 접근 필요 시 `CORS_ORIGINS` 명시적 설정
- **캐시 없음** — 나중에 Redis 또는 URLCache 레벨에서 도입 검토
- **매장 대표 이미지 URL 필드 없음** — iOS 도 카테고리 아이콘 그라디언트로 대체 중. 이미지 파이프라인은 향후

## 다음 마일스톤

| Phase | 목표 |
|---|---|
| 11 | 공공데이터 임포터 (`worker/importers/onnuri`), Kakao Local 좌표 보정, `/search` 엔드포인트 |
| 12 | 회원가입/로그인, 즐겨찾기·후기 서버 저장, iOS `RemoteMerchantRepository` 도입 |
| 13 | 관리자 페이지, 신고/수정 요청, 데이터 정기 갱신 배치 |

## 산출물 위치

| 산출물 | 경로 |
|---|---|
| FastAPI 앱 | `backend/app/` |
| Alembic | `backend/alembic/` |
| Seed 데이터 (25개) | `backend/app/seed/seed_data.py` |
| Docker Compose | `deploy/docker-compose.yml` |
| VPS 배포 절차 | `deploy/README.md` |
| API 계약 | `docs/API_SCHEMA.md` |
| DB 스키마 | `docs/DB_SCHEMA.md` |
| 본 리포트 | `LocalPayiOS/report/04_Backend_Phase10.md` |
| GitHub | https://github.com/SongByungGyu/LocalPay/commit/e31274c |
