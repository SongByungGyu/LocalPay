# API_SCHEMA — LocalPay Backend v1

> Phase 10 기준. iOS `Merchant` 도메인 모델과 1:1 호환되는 camelCase JSON 응답.
> Base URL (개발): `http://127.0.0.1:18080`

## 공통

- 인증: 없음 (Phase 10). Phase 12 에서 Bearer 토큰 도입 예정.
- 응답 인코딩: `application/json; charset=utf-8`
- 날짜: ISO-8601 (`2026-08-11T04:30:00+00:00`)
- 오류: FastAPI 기본 `{ "detail": "…" }` + 표준 HTTP status
- 목록 응답은 **envelope 없이 raw 배열** 반환 → `JSONDecoder.decode([Merchant].self, …)` 직행

## Endpoints

### GET `/health`

```json
{
  "status": "ok",
  "service": "localpay-backend",
  "version": "0.1.0"
}
```

### GET `/db-health`

```json
{
  "status": "ok",
  "postgres": "ok",
  "postgis": "3.4.2"
}
```

### GET `/api/v1/merchants`

Query:
- `category` (optional) — `restaurant|cafe|pharmacy|mart|market|food|beauty|life|etc`
- `payment` — `all` (기본) | `onnuri` | `localCurrency` | `both`
- `limit` — 기본 500, 최대 1000

Response: `[Merchant, ...]`

### GET `/api/v1/merchants/{id}`

- 404 if not found or `is_active=false`
- Response: 단일 `Merchant`

### GET `/api/v1/merchants/nearby`

Query:
- `lat`, `lng` — 필수 (WGS84)
- `radius` — 미터. 기본 3000, 최대 30000
- `limit`, `category`, `payment` — 위와 동일

응답의 각 `Merchant` 에 `distanceMeters` 가 채워진다 (PostGIS `ST_Distance(geography)` = 정확한 미터).

정렬: 거리 오름차순.

### GET `/api/v1/merchants/map`

지도 화면 이동 시 사용할 bounding box 조회.

Query (모두 필수):
- `north`, `south`, `east`, `west`
- `north > south`, `east > west` 강제
- `limit`, `category`, `payment` — 동일

PostGIS `ST_Intersects(geom, ST_MakeEnvelope(west, south, east, north, 4326))` 사용. `geom` 에 GIST 인덱스가 걸려 있어 대량 데이터에서도 빠름.

## Merchant JSON 스키마

```jsonc
{
  "id": "m-001",
  "name": "안양중앙시장 행복정육점",
  "category": "food",                        // MerchantCategory raw
  "latitude": 37.3946,
  "longitude": 126.9235,
  "address": "경기 안양시 만안구 만안로 232 안양중앙시장 내",
  "roadAddress": "경기 안양시 만안구 만안로 232",
  "phone": "031-441-1101",
  "distanceMeters": 145.6,                   // /nearby 에서만 값이 채워짐
  "supportsOnnuri": true,
  "supportsLocalCurrency": true,
  "localCurrencyName": "안양사랑페이",
  "supportedPaymentTypes": ["onnuriDigital","onnuriPaper","onnuriCard","localCurrency","card"],
  "products": ["삼겹살","목살","한우 등심","선물세트","양념갈비"],
  "businessHours": {
    "summary": "매일 09:00 - 20:00",
    "closedNote": "둘째·넷째 일요일 휴무"
  },
  "rating": 4.7,
  "reviewCount": 128,
  "marketName": "안양중앙시장",
  "description": "3대째 이어온 정육점. 온누리·안양사랑페이 모두 사용 가능합니다.",
  "lastVerifiedAt": "2026-08-10T04:30:00+00:00",
  "reviews": [
    {
      "id": "8b5f8c1e-...",
      "userName": "안양민준",
      "rating": 5,
      "content": "삼겹살 구매했는데 디지털 온누리 결제 잘 됩니다. 고기 신선해요.",
      "createdAt": "2026-08-08T04:30:00+00:00",
      "paymentType": "onnuriDigital",
      "paymentVerified": true,
      "purchasedProduct": "삼겹살"
    }
  ],
  "recentPayments": [
    {
      "id": "0f2f0c...",
      "paymentType": "onnuriDigital",
      "succeededAt": "2026-08-11T04:30:00+00:00",
      "note": "삼겹살 500g"
    }
  ]
}
```

## iOS 연동 스니펫

`API_INTEGRATION.md` §1.3 참조. 요약:

```swift
let decoder = JSONDecoder()
decoder.dateDecodingStrategy = .iso8601
let merchants = try decoder.decode([Merchant].self, from: data)
```

- 서버는 항상 camelCase → 별도 `keyDecodingStrategy` 불필요
- `distanceMeters` 는 옵셔널 필드이므로 `/nearby` 이외에서는 nil 로 남는다

## Error 예

| Status | Body | 원인 |
|---|---|---|
| 400 | `{"detail":"invalid payment: xxx"}` | 잘못된 쿼리 파라미터 |
| 404 | `{"detail":"merchant not found"}` | 존재하지 않는 `id` |
| 422 | FastAPI Validation error 배열 | 필수 파라미터 누락 · 타입 불일치 |
| 500 | `{"detail":"Internal Server Error"}` | 서버 예외. 상세는 로그 확인 |
