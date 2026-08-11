# DB_SCHEMA — LocalPay Backend

> PostgreSQL 16 + PostGIS 3.4
> DB 접근은 컨테이너 네트워크 내부에서만 (호스트 포트 미노출).
> 확장/변경은 반드시 새 Alembic 마이그레이션으로 관리.

## Tables

### merchants

| Column | Type | Nullable | Note |
|---|---|---|---|
| id | VARCHAR(64) | PK | iOS `Merchant.id` (예: `m-001`) |
| name | VARCHAR(200) | NOT NULL | 매장명 |
| category | VARCHAR(32) | NOT NULL | `MerchantCategory.rawValue` |
| latitude | DOUBLE PRECISION | NOT NULL | WGS84 |
| longitude | DOUBLE PRECISION | NOT NULL | WGS84 |
| geom | GEOMETRY(Point, 4326) | NOT NULL | GIST index |
| address | VARCHAR(500) | NOT NULL | |
| road_address | VARCHAR(500) | NULL | |
| phone | VARCHAR(64) | NULL | |
| supports_onnuri | BOOLEAN | NOT NULL | 기본 false |
| supports_local_currency | BOOLEAN | NOT NULL | 기본 false |
| local_currency_name | VARCHAR(100) | NULL | 예: "안양사랑페이" |
| supported_payment_types | JSONB | NOT NULL | `["onnuriDigital", ...]` |
| products | JSONB | NOT NULL | `["삼겹살", ...]` |
| business_hours | JSONB | NULL | `{"summary","closedNote"}` |
| rating | DOUBLE PRECISION | NOT NULL | 0.0 ~ 5.0 |
| review_count | INTEGER | NOT NULL | 시드 매장에 정착된 후기 수 (사용자 후기는 별도) |
| market_name | VARCHAR(200) | NULL | 시장명 |
| description | TEXT | NULL | |
| last_verified_at | TIMESTAMPTZ | NULL | |
| source | VARCHAR(64) | NOT NULL | 데이터 출처 태그 (`seed-anyang-v1` 등) |
| source_id | VARCHAR(200) | NULL | 외부 데이터의 원본 ID |
| is_active | BOOLEAN | NOT NULL | 기본 TRUE |
| created_at | TIMESTAMPTZ | NOT NULL | server default now() |
| updated_at | TIMESTAMPTZ | NOT NULL | server default now(), on update now() |

Indexes:
- `ix_merchants_geom` — GIST (`geom`)
- `ix_merchants_category` — btree (`category`)
- `ix_merchants_payment_flags` — btree (`supports_onnuri`, `supports_local_currency`)
- `ix_merchants_active_category` — btree (`is_active`, `category`)

### merchant_reviews (FK → merchants.id, ON DELETE CASCADE)

| Column | Type | Nullable | Note |
|---|---|---|---|
| id | UUID | PK | |
| merchant_id | VARCHAR(64) | NOT NULL | FK |
| user_name | VARCHAR(64) | NOT NULL | 시드는 실명 X, "안양민준" 등 |
| rating | INTEGER | NOT NULL | CHECK 1~5 |
| content | TEXT | NOT NULL | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| payment_type | VARCHAR(32) | NOT NULL | `PaymentType.rawValue` |
| payment_verified | BOOLEAN | NOT NULL | 결제 인증 여부 |
| purchased_product | VARCHAR(200) | NULL | |
| source | VARCHAR(32) | NOT NULL | `'seed'` \| 향후 `'user'` |

Index: `(merchant_id)`.

### merchant_payment_verifications (FK → merchants.id, ON DELETE CASCADE)

| Column | Type | Nullable | Note |
|---|---|---|---|
| id | UUID | PK | |
| merchant_id | VARCHAR(64) | NOT NULL | FK |
| payment_type | VARCHAR(32) | NOT NULL | |
| succeeded_at | TIMESTAMPTZ | NOT NULL | |
| note | VARCHAR(200) | NULL | |

Index: `(merchant_id, succeeded_at)`.

## Extensions

- **postgis** — `CREATE EXTENSION IF NOT EXISTS postgis` (마이그레이션 0001에서 수행). `postgis/postgis:16-3.4` 이미지에는 이미 라이브러리가 있어 create 만 하면 됨.

## Spatial 규칙

- SRID: **4326** (WGS84 위경도)
- 거리 계산: `ST_Distance(cast(geom AS geography), cast(point AS geography))` — 정확한 미터
- 근접 조회: `ST_DWithin(geog, geog, radius_m)` (인덱스 사용됨)
- 지도 영역: `ST_Intersects(geom, ST_MakeEnvelope(w,s,e,n,4326))` (GIST 사용됨)
- `geom` 은 seed / API 코드에서 항상 `ST_SetSRID(ST_MakePoint(lng, lat), 4326)` 로 채운다 (Point 순서: lng, lat).

## Migration 정책

- 스키마 변경은 반드시 **새 리비전 파일** 로. 기존 파일 편집 금지.
- 브랜치별 리비전 충돌은 `alembic merge` 로 해결.
- 프로덕션 DB 볼륨(`localpay_pg_data`)은 백업 없이 삭제 금지 (`down -v` 절대 금지).
