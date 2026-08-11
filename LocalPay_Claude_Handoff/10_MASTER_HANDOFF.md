# LocalPay Map — 통합 인수인계 요약

이 문서는 빠르게 한 파일만 전달해야 할 때 사용하는 요약본이다. 상세 요구사항은 같은 폴더의 개별 문서를 우선한다.

## 제품

온누리상품권/지역화폐 사용 가능한 가맹점을 지도에서 보여주고, 사용 가능한 결제수단, 카테고리, 취급상품, 후기, 최근 결제 확인을 한 번에 제공한다.

## Android

- Kotlin
- Jetpack Compose
- Material 3
- ViewModel + StateFlow
- Repository
- Hilt
- Retrofit/OkHttp
- Room
- Coil
- Fused Location
- Kakao Map Android SDK

## Backend Future

- REST API
- PostgreSQL + PostGIS
- Public-data ingestion
- Kakao Local enrichment

## MVP 핵심

1. 지도 홈
2. 결제필터: 전체/온누리/지역화폐/둘 다
3. 카테고리
4. 가게/상품 검색
5. 매장 상세
6. 상품정보
7. 자체 후기/결제인증
8. 즐겨찾기
9. MY
10. 잔액은 Placeholder

## 중요 제한

- 잔액 공개/제휴 API 확보 전 실잔액 연동 금지
- 외부 리뷰 크롤링 금지
- Kakao는 지도/장소 보강이며 상품권 지원 여부의 단독 source가 아님
- secrets Git 커밋 금지

## 데이터

- 온누리 전국 가맹점 공공데이터
- 한국조폐공사 통합 지역사랑상품권 가맹점 API
- 지역상품권 정책정보
- Kakao Local

## Domain Key

- Merchant
- PaymentMethodSupport
- SupportStatus: SUPPORTED / NOT_SUPPORTED / UNKNOWN
- Review
- UserVerification
- Favorite
- LocalCurrencyPolicy

## 개발 순서

1. Compose Scaffold
2. Theme/Navigation
3. Domain/Repository
4. 20+ Dummy merchants
5. Map/Home
6. Search
7. Detail
8. Favorite Room
9. Review local
10. MY
11. Kakao Map SDK
12. Tests
13. Remote repository skeleton

## 완료 기준

더미 데이터만으로도 앱 실행부터 지도→필터→매장→상세→후기→즐겨찾기→MY까지 전 사용자 플로우가 작동해야 한다.
