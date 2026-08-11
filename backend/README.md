# LocalPay Backend

> FastAPI + PostgreSQL/PostGIS 로 구성된 LocalPay 지도 서비스 API 서버.
> Phase 10 (1차) 범위: 서버 구조 · DB 스키마 · Docker · 6개 API + 25개 Dummy 매장 seed.

## 스택

- Python 3.12
- FastAPI 0.115.x
- SQLAlchemy 2.x (async, asyncpg)
- Alembic (async env.py)
- GeoAlchemy2 + PostGIS 3.x
- Pydantic 2.x (camelCase alias — iOS Codable 호환)
- Docker / Docker Compose

## 폴더 구조

```
backend/
├── app/
│   ├── main.py             FastAPI factory (프로덕션에서 /docs 비활성)
│   ├── config.py           환경변수 (pydantic-settings)
│   ├── database.py         async 엔진 + 세션
│   ├── deps.py             SessionDep
│   ├── api/
│   │   ├── health.py       GET /health, /db-health
│   │   └── v1/
│   │       ├── router.py
│   │       └── merchants.py  가맹점 조회 API (list/detail/nearby/map)
│   ├── models/
│   │   ├── base.py
│   │   └── merchant.py     Merchant + MerchantReview + MerchantPaymentVerification
│   ├── schemas/
│   │   ├── common.py       CamelModel base
│   │   └── merchant.py     iOS Domain Model 과 호환되는 응답 스키마
│   └── seed/
│       ├── seed_data.py    안양 25개 매장 (iOS DummyMerchantSeed 포팅)
│       └── run_seed.py     python -m app.seed.run_seed
├── alembic/
│   ├── env.py              async 마이그레이션 실행기
│   └── versions/0001_initial.py   CREATE EXTENSION postgis + 3 tables + indexes
├── tests/
│   └── test_health.py
├── alembic.ini
├── Dockerfile
├── entrypoint.sh           migrate → (optional seed) → uvicorn
├── requirements.txt
├── pyproject.toml          (ruff / pytest)
└── .env.example
```

## API (v1)

| Method | Path | 설명 |
|---|---|---|
| GET | `/health` | 서비스 liveness |
| GET | `/db-health` | Postgres 왕복 + PostGIS 버전 |
| GET | `/api/v1/merchants` | 목록. Query: `category`, `payment=all\|onnuri\|localCurrency\|both`, `limit` |
| GET | `/api/v1/merchants/{id}` | 단일 매장 상세 |
| GET | `/api/v1/merchants/nearby` | 주변 검색. `lat`, `lng`, `radius(m)`. PostGIS `ST_DWithin` |
| GET | `/api/v1/merchants/map` | 지도 영역. `north/south/east/west`. `ST_Intersects` |

응답은 **iOS `Merchant` 도메인 모델과 동일한 camelCase JSON**. iOS `RemoteMerchantRepository` 가 `JSONDecoder.decode([Merchant].self, from:)` 로 바로 디코드 가능.

## 로컬 실행 (VPS 배포와 동일한 방식)

이 저장소는 회사 Mac 에서 개발만 하고 실행은 Hostinger VPS 의 `/opt/localpay` 에서 검증합니다.

VPS 절차 (deploy/README.md 상세):

```bash
cd /opt/localpay
git pull
cd deploy
cp .env.example .env       # 최초 1회. POSTGRES_PASSWORD 등 실제 값으로 수정
docker compose up -d --build
docker compose logs -f api
```

## 환경변수

`.env.example` 참조. 프로덕션에서는 다음이 필수:
- `DATABASE_URL` — asyncpg DSN
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` (compose 에서 참조)
- `ENV=production` (Swagger 비활성화)
- `SEED_ON_START=true` — Phase 10 데모용. 실 데이터 연동 후에는 `false`

## Migration

컨테이너가 시작될 때 `entrypoint.sh` 가 자동으로 `alembic upgrade head` 를 실행합니다.

수동 실행:

```bash
docker compose exec api alembic upgrade head
```

## Seed

`SEED_ON_START=true` 로 컨테이너 시작 시 자동 seed. 수동 재실행:

```bash
docker compose exec api python -m app.seed.run_seed
```

Seed 는 **truncate + re-insert** 방식이므로 사용자 생성 데이터가 들어가면 별도 로직이 필요합니다 (Phase 11+).

## 테스트

```bash
docker compose exec api pytest -q
```

## 향후 확장

- Phase 11: 공공데이터 임포터 (`worker/` 하위)
- Phase 11: Kakao Local API 좌표 보정
- Phase 12: 회원가입 / 즐겨찾기 / 후기 서버 저장
- Phase 12: 관리자 페이지, 신고/수정 요청

`../docs/API_SCHEMA.md`, `../docs/DB_SCHEMA.md` 참조.
