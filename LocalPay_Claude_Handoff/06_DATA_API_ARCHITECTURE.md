# 06. 데이터 / API / 서버 아키텍처 문서

## 1. 전체 구조

```text
Android App
  │
  ├─ Kakao Map SDK  ── 지도 렌더링
  │
  └─ REST API
       │
       ▼
Backend API
  │
  ├─ Merchant Search
  ├─ Merchant Detail
  ├─ Reviews
  ├─ Favorites
  ├─ Policy
  └─ Wallet Provider (Future)
       │
       ▼
PostgreSQL + PostGIS
       ▲
       │
Data Ingestion / Normalizer
  ├─ 온누리 공공데이터
  ├─ 지역화폐 통합 가맹점 API
  └─ Kakao Local 보강
```

MVP Android는 서버 없이 `DummyMerchantRepository`로 완성할 수 있어야 한다.

---

## 2. 데이터 소스

### 2.1 온누리상품권

공식 후보:

- 소상공인시장진흥공단 `전국 온누리상품권 가맹점 현황`

활용 예상 필드:

- 가맹점명
- 시장명
- 소재지/주소
- 취급품목
- 충전식카드/지류/모바일 취급 여부 등

특징:

- 파일형 공공데이터를 Batch Import하는 방식으로 설계
- 원본 갱신 주기와 우리 sync 주기를 구분

### 2.2 지역화폐

공식 후보:

- 한국조폐공사 `통합 가맹점기본정보`

활용 예상 필드:

- 가맹점명
- 대표전화
- 주소
- 위도/경도
- 사업자 상태
- 표준산업분류코드
- 제공기관/지역 코드

### 2.3 정책 정보

- 지역사랑상품권 지자체별 판매정책정보
- 할인율/판매정책 기간/한도 등 제공 가능한 값을 서비스 모델로 정규화

### 2.4 Kakao Local

용도:

- 주소 → 좌표 보정
- 장소명 검색
- 카테고리 보강
- 전화번호/도로명주소 등 장소정보 보강

주의:

- Kakao 장소정보와 공공 가맹점 정보를 자동으로 동일 업체라고 단정하지 않는다.
- 매칭 신뢰도 score를 사용한다.

---

## 3. Merchant Domain Model

권장 Kotlin Domain:

```kotlin
data class Merchant(
    val id: String,
    val name: String,
    val category: MerchantCategory,
    val location: GeoPoint,
    val address: String,
    val roadAddress: String?,
    val phone: String?,
    val marketName: String?,
    val paymentMethods: List<PaymentMethodSupport>,
    val products: List<String>,
    val rating: Double?,
    val reviewCount: Int,
    val lastVerifiedAt: Instant?,
    val sourceUpdatedAt: Instant?,
    val businessStatus: BusinessStatus,
    val sourceSummary: List<DataSourceType>
)
```

Payment:

```kotlin
data class PaymentMethodSupport(
    val type: PaymentType,
    val status: SupportStatus,
    val currencyName: String?,
    val source: DataSourceType,
    val updatedAt: Instant?
)

enum class SupportStatus {
    SUPPORTED,
    NOT_SUPPORTED,
    UNKNOWN
}
```

---

## 4. DB Schema 제안

### merchants

- id UUID
- normalized_name
- display_name
- category
- address
- road_address
- geom geography(Point, 4326)
- phone
- market_name
- business_status
- created_at
- updated_at

Index:

- GIST(geom)
- normalized_name trigram/full-text 고려

### merchant_sources

- id
- merchant_id
- source_type
- source_record_id
- raw_name
- raw_address
- source_updated_at
- synced_at
- raw_payload_json

### merchant_payment_methods

- id
- merchant_id
- payment_type
- currency_name
- support_status
- source_type
- source_updated_at

### merchant_products

- id
- merchant_id
- product_name
- normalized_product_name
- source_type

### reviews

- id
- merchant_id
- user_id
- rating
- payment_result
- payment_type
- purchased_item
- body
- created_at

### user_verifications

- id
- merchant_id
- user_id
- payment_type
- result SUCCESS/FAILURE
- verified_at

### favorites

- user_id
- merchant_id
- created_at

### local_currency_policies

- region_code
- currency_name
- discount_rate
- purchase_limit
- valid_from
- valid_to
- source_updated_at

---

## 5. 중복 가맹점 병합 전략

공공데이터 두 종류와 Kakao 장소가 중복될 수 있다.

### 1차 후보 생성

- 정규화 주소 동일
- 정규화 이름 유사
- 좌표 거리 50m 이내

### Score 예시

- 도로명주소 동일: +60
- 상호명 exact: +30
- 상호명 유사도 높음: +20
- 좌표 20m 이내: +20
- 전화번호 동일: +40

Threshold 이상일 때 자동 병합.

애매한 경우 source를 분리 보관하고 관리자 검토 대상으로 남긴다.

---

## 6. 좌표 처리

온누리 데이터에 좌표가 없거나 불완전할 수 있으므로:

```text
원본 주소
  ↓
주소 정규화
  ↓
기존 좌표 확인
  ↓ 없으면
Kakao Local 주소 검색
  ↓
좌표 저장 + geocode source 기록
```

API 호출 비용/쿼터를 고려해 동일 주소 재호출을 방지한다.

---

## 7. 지도 Query API

### GET /v1/merchants

Parameters:

```text
swLat
swLng
neLat
neLng
zoom
payment
category
query
sort
limit
cursor
```

예시 Response:

```json
{
  "items": [
    {
      "id": "m_001",
      "name": "중앙시장 우리정육",
      "category": "GROCERY",
      "lat": 37.0,
      "lng": 127.0,
      "distanceMeters": 420,
      "payments": ["ONNURI", "LOCAL_CURRENCY"],
      "paymentLabel": "둘 다",
      "products": ["한우", "삼겹살"],
      "lastVerifiedAt": "2026-08-09T10:00:00+09:00"
    }
  ],
  "nextCursor": null
}
```

지도용 response는 상세 전체 payload보다 가볍게 유지한다.

---

## 8. 상세 API

### GET /v1/merchants/{merchantId}

- 기본 정보
- 상세 결제수단
- 상품
- 정책/지역화폐 이름
- 최신성
- 후기 요약
- source summary

---

## 9. 검색 API

### GET /v1/search

Parameters:

- q
- lat/lng optional
- payment
- category
- sort

검색 우선순위 예:

1. 매장명 exact/prefix
2. 상품 exact/prefix
3. 카테고리
4. 시장명
5. 주소

---

## 10. Review API — Phase 2

- `GET /v1/merchants/{id}/reviews`
- `POST /v1/merchants/{id}/reviews`
- `DELETE /v1/reviews/{id}`

MVP는 repository interface만 만들고 Local 구현 가능.

---

## 11. Favorite API — Phase 2

MVP는 Room 사용.

Server 연동 후:

- `GET /v1/me/favorites`
- `PUT /v1/me/favorites/{merchantId}`
- `DELETE /v1/me/favorites/{merchantId}`

---

## 12. Wallet API — Future

이 영역은 Provider Adapter 구조만 정의한다.

```text
WalletRepository
  ├─ OnnuriWalletProvider
  ├─ LocalCurrencyProviderA
  └─ LocalCurrencyProviderB
```

제휴/공식 사용자 인증이 가능한 Provider만 붙인다.

예상 Domain:

```kotlin
data class WalletBalance(
    val provider: WalletProvider,
    val currencyName: String,
    val balance: Long,
    val updatedAt: Instant
)
```

MVP에는 `RemoteWalletProvider`를 구현하지 않는다.

---

## 13. Android Dummy Dataset

최소 15~30개 가맹점을 넣는다.

분포:

- 결제 타입: 온누리만 / 지역화폐만 / 둘 다
- 카테고리: 음식/카페/약국/마트/시장/식품/미용/생활
- 후기 있음/없음
- 최근 확인 있음/없음
- 정보 오래됨 사례

테스트가 가능하도록 데이터 다양성을 의도적으로 만든다.

---

## 14. 데이터 수집 배치 — 서버 도입 시

```text
01 Fetch
02 Validate
03 Normalize
04 Geocode missing coordinates
05 Deduplicate / Match
06 Upsert Merchant
07 Update Source Records
08 Build Search Index
09 Emit Metrics
```

실패 row는 버리지 않고 quarantine/error table에 저장한다.

---

## 15. 공식 참고 URL

- Kakao Map: https://developers.kakao.com/docs/ko/kakaomap/common
- Kakao Local REST: https://developers.kakao.com/docs/ko/kakaomap/rest-api
- 온누리 전국 가맹점: https://www.data.go.kr/data/3060079/fileData.do
- 지역화폐 통합 가맹점: https://www.data.go.kr/data/15119539/openapi.do
- 지역화폐 정책: https://www.data.go.kr/data/15125217/openapi.do
