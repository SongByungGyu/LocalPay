# LocalPay iOS MVP 개발 마스터 프롬프트

> 이 문서는 `마스터프로젝트/CLAUDE.md`(거버넌스 룰)의 하위 프로젝트 컨텍스트다.
> 상위 룰(합니다체, 티켓, Surgical Changes 등)은 그대로 상속한다.
> 이 파일은 **LocalPay iOS 프로젝트 전용 개발 지침**만 담는다.

너는 시니어 iOS 개발자이자 모바일 서비스 설계자다.

지금부터 **온누리상품권 및 지역화폐 사용 가능 가맹점을 지도에서 찾을 수 있는 iOS 앱**을 개발한다.

프로젝트의 목표는 우선 실제 서버 없이 동작하는 **완성도 높은 Dummy MVP 앱**을 만드는 것이다.

UI/UX와 전체 앱 구조를 먼저 완성한 뒤, 이후 온누리상품권 공공데이터, 지역화폐 가맹점 API 및 실제 Backend를 연결할 예정이다.

---

# 1. 서비스 개요

서비스 가칭:

**LocalPay**

핵심 목적:

사용자가 현재 위치를 기준으로

* 온누리상품권 사용 가능 매장
* 지역화폐 사용 가능 매장
* 두 결제수단 모두 가능한 매장

을 지도에서 빠르게 찾을 수 있도록 한다.

단순히 가맹점 위치만 보여주는 것이 아니라,

* 음식점
* 카페
* 약국
* 시장
* 마트
* 식품
* 미용
* 생활
* 기타

등 카테고리별로 찾을 수 있어야 한다.

가맹점 상세 화면에서는

* 사용할 수 있는 상품권
* 판매 상품
* 주소
* 전화번호
* 영업정보
* 후기
* 실제 상품권 결제 성공 여부

등을 확인할 수 있도록 한다.

향후에는 마이페이지에서 온누리상품권 및 지역화폐의 잔액까지 조회할 수 있도록 확장한다.

단, **현재 MVP에서는 실제 개인 잔액 API를 사용하지 않는다.**

---

# 2. 가장 중요한 개발 원칙

이번 개발의 우선순위는 다음과 같다.

1. 실제 사용할 수 있을 정도의 UI/UX 구현
2. 지도 중심의 사용 흐름 완성
3. Dummy 데이터만으로 전체 기능 동작
4. 향후 Backend 교체가 쉬운 구조
5. 향후 Kakao Map SDK 교체가 쉬운 지도 추상화
6. 과도한 Clean Architecture 적용 금지
7. 읽기 쉽고 유지보수 가능한 코드 작성

현재 단계에서는 실제 공공 API 및 유료 API 호출을 하지 않는다.

API KEY도 코드에 직접 삽입하지 않는다.

---

# 3. 개발 환경

다음 기술을 기본으로 사용한다.

* Swift
* SwiftUI
* iOS 17+
* Swift Concurrency
* Observation 또는 ObservableObject
* NavigationStack
* MapKit
* CoreLocation

외부 라이브러리는 현재 단계에서 사용하지 않는다.

가능하면 Apple 기본 Framework만 사용한다.

---

# 4. 지도 전략

## Phase 1

현재 Dummy MVP에서는

**Apple MapKit**

을 사용한다.

이유:

* 빠른 개발
* SwiftUI Map 지원
* API Key 불필요
* Simulator 테스트 용이
* UI/UX 검증에 집중 가능

하지만 지도 구현을 MapKit에 강하게 종속시키지 않는다.

향후 실서비스에서는 국내 장소 서비스 품질 등을 고려해

**Kakao Map iOS SDK**

사용을 검토한다.

따라서 지도 관련 로직은 가능한 한 View 내부에 직접 퍼뜨리지 말고 지도 데이터와 UI 상태를 분리한다.

예:

MapView
MapViewModel
MapRegion
MapMarkerModel

정도의 구조를 유지한다.

향후 다음 형태로 확장 가능해야 한다.

MapProvider

* AppleMapProvider
* KakaoMapProvider

단, 현재 MVP에서 불필요하게 Protocol 구조를 과도하게 만드는 것은 피한다.

---

# 5. 핵심 사용자 흐름

앱 실행

↓

현재 위치 확인

↓

주변 가맹점 지도 표시

↓

결제수단 필터

↓

카테고리 필터

↓

지도 핀 선택

↓

하단 가맹점 Preview Card

↓

가맹점 상세

↓

후기 / 상품 / 결제정보 확인

↓

즐겨찾기

↓

MY에서 저장한 장소 확인

이 흐름을 우선 완성한다.

---

# 6. Tab 구조

하단 Tab Bar는 다음 4개를 사용한다.

1. 지도
2. 검색
3. 즐겨찾기
4. MY

SF Symbols를 사용한다.

예:

지도
map.fill

검색
magnifyingglass

즐겨찾기
heart.fill

MY
person.fill

---

# 7. 지도 Home 화면

앱의 가장 중요한 화면이다.

상단에 Floating Search Bar를 배치한다.

예:

"가게, 상품, 시장을 검색해보세요"

검색창 아래에는 결제수단 Filter Chip을 둔다.

* 전체
* 온누리
* 지역화폐
* 둘 다

그 아래 또는 검색창 아래 Horizontal Scroll 형태로 카테고리를 표시한다.

* 전체
* 음식점
* 카페
* 약국
* 마트
* 시장
* 식품
* 미용
* 생활

카테고리는 아이콘과 텍스트를 함께 표시한다.

---

# 8. 지도 Marker

가맹점 결제수단에 따라 Marker를 시각적으로 구분한다.

예:

온누리만 가능
→ 초록 계열

지역화폐만 가능
→ 주황 계열

둘 다 가능
→ 파랑 또는 별도의 복합 아이콘

단, 색상만으로 정보를 전달하지 않는다.

Marker 내부에 간단한 Symbol 또는 형태 차이를 둔다.

Marker 선택 시 선택상태가 명확히 보여야 한다.

---

# 9. 지도 Cluster

Dummy MVP 초기 버전에서는 복잡한 Cluster 알고리즘을 구현할 필요는 없다.

다만 향후 전국 가맹점 데이터를 표시할 것을 고려해 구조상

"현재 지도 영역 내 Merchant만 표시"

할 수 있도록 한다.

향후 Backend에서는 Bounding Box 기반 검색을 적용한다.

---

# 10. 현재 위치

CoreLocation을 사용한다.

처음 위치 권한이 없다면 설명 UI를 제공한다.

위치 권한 거절 상태에서도 앱은 사용 가능해야 한다.

기본 Dummy 지역은

**경기도 안양시**

근처 좌표를 사용한다.

현재 위치 버튼을 지도 우측 하단 Floating Button 형태로 제공한다.

---

# 11. Merchant 데이터 모델

Merchant Model에는 최소 다음 데이터가 필요하다.

id

name

category

latitude

longitude

address

roadAddress

phone

distance

supportsOnnuri

supportsLocalCurrency

localCurrencyName

supportedPaymentTypes

products

businessHours

rating

reviewCount

favorite

marketName

description

lastVerifiedAt

reviews

---

# 12. PaymentType

다음 상품권 유형을 구분할 수 있도록 한다.

예:

* 디지털 온누리
* 지류 온누리
* 카드형 온누리
* 지역화폐
* QR
* 카드

현재 Dummy Data에서는 실제 정책과 완전히 일치할 필요는 없으며

반드시 화면에

"DEMO"

또는

"예시 데이터"

임을 알 수 있게 한다.

---

# 13. Dummy Merchant

최소 20~30개 이상 생성한다.

안양을 기준으로 현실적인 이름의 가상의 매장을 구성한다.

예:

안양중앙시장 행복정육점

평촌우리약국

범계할머니손칼국수

중앙시장 청년반찬

안양착한카페

평촌생활마트

등.

모든 가맹점이 같은 형태가 되지 않도록 한다.

결제수단도 다양하게 배분한다.

예:

온누리만

지역화폐만

둘 다

---

# 14. Merchant Category

enum으로 관리한다.

예:

all

restaurant

cafe

pharmacy

mart

market

food

beauty

life

etc

각 Category에는

title

icon

을 제공한다.

---

# 15. Marker 선택

Marker를 누르면 화면 하단에서 Merchant Preview Card가 올라온다.

Card 정보:

가게명

카테고리

별점

리뷰 수

거리

온누리 가능 여부

지역화폐 가능 여부

대표 상품 2~3개

상세보기 버튼

즐겨찾기 버튼

카드를 위로 Swipe해 상세로 이동시키는 기능은 MVP에서는 필수가 아니다.

단순 Tap으로 상세 진입하면 된다.

---

# 16. Merchant 상세 화면

상세화면 상단:

가게 대표 Placeholder 이미지

가게명

카테고리

별점

리뷰 수

거리

즐겨찾기

그 아래:

## 사용 가능한 결제

예:

디지털 온누리 가능

지류 온누리 가능

안양사랑페이 가능

등.

그 아래:

## 판매 상품

Chip 형태로 표시한다.

예:

삼겹살

목살

한우

선물세트

그 아래:

## 가게 정보

주소

전화

영업시간

시장명

최근 정보 확인일

등.

그 아래:

## 최근 결제 확인

사용자 결제 인증 Dummy Data를 보여준다.

예:

오늘 디지털 온누리 결제 성공

3일 전 안양사랑페이 결제 성공

7일 전 지류 온누리 결제 성공

그 아래:

## 후기

후기 목록을 표시한다.

---

# 17. 후기 구조

단순 리뷰 앱과 차별화하기 위해

"상품권 결제 인증 후기"

를 핵심으로 한다.

Review Model 예:

id

userName

rating

content

createdAt

paymentType

paymentVerified

purchasedProduct

후기 UI 예:

★★★★★

"삼겹살 구매했는데 온누리 결제 잘 됩니다."

✅ 디지털 온누리 결제 확인

구매상품: 삼겹살

3일 전

현재 MVP에서는 작성기능도 Dummy로 구현 가능하다.

작성한 리뷰는 앱 실행 중 Local State 또는 UserDefaults/SwiftData 등에 저장해도 된다.

---

# 18. 검색 화면

검색 대상:

가게 이름

상품

시장

카테고리

예:

"삼겹살"

검색 시

삼겹살을 판매하는 Dummy Merchant만 보여준다.

예:

"약국"

검색 시

약국 Category의 Merchant를 보여준다.

검색 결과 상단에는 Filter를 제공한다.

* 거리순
* 평점순
* 후기순

현재 Dummy MVP에서는 실제 거리 계산 또는 Dummy 값을 사용해도 된다.

---

# 19. 검색 결과 View

List 또는 Card UI로 표현한다.

각 Merchant Card에는:

가게명

카테고리

거리

결제 가능 상품권

대표상품

평점

후기수

즐겨찾기

를 표시한다.

Card를 누르면 상세화면으로 이동한다.

---

# 20. 즐겨찾기

사용자가 Merchant를 즐겨찾기에 등록할 수 있도록 한다.

즐겨찾기는 앱 종료 후에도 유지되도록 구현한다.

MVP에서는

UserDefaults

또는

SwiftData

를 사용할 수 있다.

과도한 DB 구현은 하지 않는다.

즐겨찾기 화면에서는 등록된 Merchant를 Card 목록으로 표시한다.

---

# 21. MY 화면

MY 화면은 다음 구조로 한다.

상단:

프로필 Placeholder

닉네임

기본 지역

예:

병규님

안양시

그 아래:

## 내 상품권

디지털 온누리

잔액 연동 준비중

[공식 앱에서 확인]

안양사랑페이

잔액 연동 준비중

[공식 앱에서 확인]

개발 Preview Mode에서는 다음과 같은 Dummy 잔액을 표시할 수 있다.

디지털 온누리
128,500원

안양사랑페이
43,200원

단 반드시

DEMO

표시를 해야 한다.

---

# 22. MY 추가 항목

다음 정보를 표시한다.

즐겨찾기 매장 수

작성한 후기 수

결제 인증 수

기본 지역

알림 설정

앱 정보

---

# 23. 지역화폐 정책 카드

MY 또는 지도 상단에서 지역별 혜택 정보를 보여줄 수 있도록 Card를 만든다.

Dummy 예:

안양사랑페이

이번 달 충전 혜택
7%

월 구매한도
30만원

정보 기준일
2026.08

모두 Dummy임을 명확히 표시한다.

---

# 24. Empty / Loading / Error UI

다음 상태도 구현한다.

검색 결과 없음

즐겨찾기 없음

주변 가맹점 없음

위치 권한 없음

데이터 Loading

Network Error Placeholder

실제 Network 연결 전에도 View State 구조를 만든다.

예:

idle

loading

loaded

empty

error

---

# 25. Architecture

과도하게 복잡하지 않은 MVVM 구조를 사용한다.

예:

App
│
├── Models
│
├── Data
│   ├── Repository
│   └── Dummy
│
├── Features
│   ├── Map
│   ├── Search
│   ├── MerchantDetail
│   ├── Favorites
│   └── MyPage
│
├── Components
│
├── DesignSystem
│
└── Utilities

Repository 구조:

MerchantRepository

DummyMerchantRepository

향후:

RemoteMerchantRepository

로 교체 가능하게 한다.

---

# 26. MerchantRepository

최소 다음 기능이 필요하다.

fetchMerchants()

searchMerchants(query:)

fetchMerchant(id:)

fetchNearbyMerchants(...)

filterByCategory(...)

filterByPayment(...)

현재 구현체는 DummyMerchantRepository를 사용한다.

---

# 27. 향후 Backend 고려

향후 서버는 다음 데이터를 관리한다.

Merchant

Product

Review

User

Favorite

PaymentVerification

CurrencyPolicy

WalletConnection

추천 Backend DB:

PostgreSQL + PostGIS

하지만 현재 iOS 프로젝트에서는 Backend를 구현하지 않는다.

---

# 28. 실제 데이터 연결 계획

향후 실제 서비스 단계에서는 다음 데이터를 사용할 예정이다.

온누리상품권 가맹점 공공데이터

지역사랑상품권 가맹점 데이터

Kakao Local API를 통한 장소정보 보완

우리 Backend

하지만 현재 개발에서는 이 API를 직접 호출하지 않는다.

Mock / Dummy Repository만 사용한다.

---

# 29. 향후 지도 전환

MapKit으로 MVP를 완성한 후

Kakao Map iOS SDK

적용 가능성을 고려한다.

Kakao Map 사용 시 SwiftUI에서 UIKit 기반 SDK를 감싸야 한다면

UIViewRepresentable

또는 적절한 Wrapper 계층을 구성한다.

중요:

Merchant / Search / Filter / ViewModel이 MapKit 클래스에 직접 의존하지 않도록 한다.

---

# 30. 디자인 방향

전체적인 디자인은

카카오맵

네이버지도

토스

당근

같은 한국 모바일 서비스의 간결한 UX를 참고한다.

단 특정 서비스 UI를 그대로 복사하지 않는다.

디자인 키워드:

깔끔함

친근함

지도 중심

높은 가독성

큰 터치 영역

정보 과밀 방지

Bottom Sheet 활용

Rounded Card

---

# 31. 기본 UI 규격

기본 화면 Horizontal Padding:

16pt

Card Corner Radius:

16~20pt

Button 높이:

48~52pt

Chip 높이:

36~40pt

최소 Touch Target:

44pt

Navigation Title:

20~24pt 수준

본문:

15~17pt

보조텍스트:

13~14pt

시스템 Dynamic Type을 최대한 지원한다.

---

# 32. 색상

Asset Catalog 또는 Design Token 형태로 관리한다.

예:

Background

Surface

Primary

Onnuri

LocalCurrency

Both

TextPrimary

TextSecondary

Divider

Success

Error

단 Color를 View마다 하드코딩하지 않는다.

Dark Mode도 깨지지 않게 구성한다.

---

# 33. 재사용 Components

다음 UI는 Component화한다.

SearchBar

CategoryChip

PaymentFilterChip

MerchantMarker

MerchantCard

MerchantPreviewCard

PaymentBadge

ProductChip

RatingView

EmptyStateView

SectionHeader

BalanceCard

ReviewCard

FloatingLocationButton

---

# 34. Navigation

NavigationStack 기반으로 한다.

예:

RootTabView

MapHomeView
→ MerchantDetailView

SearchView
→ SearchResultView
→ MerchantDetailView

FavoriteView
→ MerchantDetailView

MyPageView

---

# 35. 접근성

다음 기본 접근성을 적용한다.

VoiceOver Label

Dynamic Type

44pt 이상 Touch Area

색상 외 정보 전달

텍스트 Contrast 확보

---

# 36. 개인정보/보안

현재 MVP에서

회원가입

실제 결제정보

실제 상품권 잔액

주민번호

금융정보

등은 저장하지 않는다.

Dummy 데이터만 사용한다.

---

# 37. 테스트

최소 다음 항목을 확인한다.

앱 실행 성공

Tab 이동

지도 표시

Dummy Marker 표시

카테고리 필터

상품권 필터

검색

Merchant 선택

상세 진입

즐겨찾기 추가/삭제

MY 화면

위치 권한 거절 상태

Empty State

---

# 38. Preview

SwiftUI Preview를 적극 활용한다.

주요 화면은 Preview가 동작하도록 한다.

예:

MapHomeView

MerchantCard

MerchantDetailView

SearchView

FavoriteView

MyPageView

ReviewCard

---

# 39. 개발 단계

반드시 다음 순서대로 진행한다.

## Phase 1

프로젝트 기본 구조 생성

Models

Dummy Data

DesignSystem

Root Tab

## Phase 2

지도 Home

현재 위치

Marker

결제수단 Filter

Category Filter

## Phase 3

Merchant Preview

Merchant Detail

상품정보

Payment Badge

## Phase 4

검색

검색 결과

정렬

## Phase 5

즐겨찾기

Local Persistence

## Phase 6

후기 UI

Dummy 결제 인증

## Phase 7

MY

Dummy Wallet

지역화폐 혜택

## Phase 8

Empty / Error / Loading State

UI polish

Animation

Accessibility

## Phase 9

전체 Build

Warning 제거

Runtime Error 확인

README 작성

---

# 40. 작업 진행 방식

중요하다.

기존 프로젝트가 있다면 먼저 전체 구조를 분석한다.

기존 코드를 무조건 삭제하거나 덮어쓰지 않는다.

작업 시작 전:

현재 프로젝트 구조

발견된 기존 코드

수정할 파일

새로 생성할 파일

개발 순서

를 간단히 정리한다.

그 다음 실제 구현을 진행한다.

각 Phase 완료 후:

구현한 내용

생성/수정 파일

남은 작업

잠재적인 문제

를 짧게 보고한다.

---

# 41. 빌드 기준

가능하면 각 주요 Phase 종료 후

xcodebuild

또는 사용 가능한 Xcode Build 환경으로 컴파일을 확인한다.

빌드 오류가 있다면 다음 단계로 넘어가기 전에 해결한다.

Warning도 가능한 범위에서 정리한다.

---

# 42. 하지 말아야 할 것

임의로 실제 금융 API 사용 금지

공공 API Key 임의 생성 금지

실제 결제 기능 구현 금지

Web Scraping 금지

네이버/카카오 리뷰 Scraping 금지

가짜 API 응답을 실제 데이터처럼 표시 금지

Dummy 잔액을 실제 잔액처럼 표시 금지

과도한 Architecture 구축 금지

필요 없는 외부 Library 추가 금지

---

# 43. MVP 완료 기준

다음 사용자 흐름이 전부 실제로 작동해야 한다.

사용자가 앱 실행

→ 지도 확인

→ 온누리 필터 선택

→ 음식점 선택

→ 주변 Marker 변경

→ Marker 선택

→ 가게 Preview 확인

→ 상세페이지 이동

→ 판매상품 확인

→ 상품권 결제 가능 여부 확인

→ 후기 확인

→ 즐겨찾기 등록

→ 즐겨찾기 Tab 확인

→ MY 이동

→ 상품권 영역 확인

이 흐름이 Simulator에서 끊김 없이 작동하면 1차 MVP 완료로 판단한다.

---

# 44. 최종 산출물

개발이 완료되면 다음을 제공한다.

1. 정상 Build 가능한 Xcode Project

2. README.md

README에는 다음 내용을 작성한다.

* 프로젝트 소개
* 지원 iOS
* 기술 Stack
* Project Structure
* 실행 방법
* Dummy Data 설명
* 지도 구조
* 향후 Kakao Map 전환 방법
* 향후 Backend 연결 방법
* 실제 온누리/지역화폐 데이터 연결 위치
* 현재 구현되지 않은 기능

3. TODO.md

다음 개발 단계 정리

4. API_INTEGRATION.md

향후

공공데이터

Kakao Local

Backend

Wallet API

를 어느 Repository에 연결할지 설명한다.

---

# 45. 향후 최종 서비스 구조

최종적으로 아래 구조를 목표로 한다.

iOS App
SwiftUI
│
├── Map
├── Search
├── Merchant Detail
├── Review
├── Favorites
└── My
│
↓
Repository
│
↓
Backend API
│
↓
PostgreSQL + PostGIS
│
┌────┼────────────┐
│    │            │
온누리 지역화폐   장소정보
데이터 가맹점API  Kakao Local

---

# 46. 서비스에서 가장 중요한 차별점

이 앱은 단순히

"상품권 가맹점 위치를 보여주는 앱"

으로 만들면 안 된다.

궁극적으로 사용자가

"내가 가진 상품권으로 무엇을 어디에서 살 수 있는가?"

를 해결하는 서비스가 되어야 한다.

따라서 다음 정보의 중요도가 높다.

사용 가능 상품권

실제 최근 결제 성공 여부

판매 상품

사용자 후기

현재 위치에서 거리

카테고리

지역화폐 혜택

향후 검색은

"가게"

뿐만 아니라

"상품"

중심 검색으로 발전시킨다.

예:

삼겹살

타이레놀

과일

반찬

꽃

신발

등.

---

# 47. 지금 바로 시작할 작업

우선 현재 Repository의 파일을 확인한다.

프로젝트가 없다면 새로운 SwiftUI iOS 프로젝트 구조를 생성한다.

그 다음 아래 순서로 진행한다.

1. App 구조
2. Models
3. DummyMerchantRepository
4. DesignSystem
5. RootTabView
6. MapHomeView
7. Marker / Filter
8. Merchant Preview
9. Merchant Detail
10. Search
11. Favorites
12. Reviews
13. MyPage
14. Persistence
15. Empty/Error State
16. 전체 Build 검증
17. README 작성

먼저 프로젝트 구조를 분석하고 구현 계획을 간단히 출력한 뒤 바로 개발을 시작하라.

단순 예제 코드를 제시하는 것으로 끝내지 말고 **실제 프로젝트 파일을 생성/수정하면서 실행 가능한 iOS Dummy MVP를 완성하는 것을 목표로 한다.**

---

## 부록 A — 프로젝트 물리 구조 (이 저장소 기준)

```
온누리:지역화폐사용처/
├── LocalPay_Claude_Handoff/    ← 기획/디자인 참고 문서 (원래 Android 대상이었으나 UI/데이터 스펙은 재사용 가능)
│   ├── 01_SERVICE_PLANNING.md
│   ├── 02_SERVICE_DEFINITION.md
│   ├── 03_DESIGN_SYSTEM.md
│   ├── 04_UI_SPEC.md
│   ├── 05_REQUIREMENTS_SPEC.md
│   ├── 06_DATA_API_ARCHITECTURE.md
│   ├── 09_ACCEPTANCE_CHECKLIST.md
│   └── prototype/index.html
│
└── LocalPayiOS/                ← ⭐ 이 iOS 프로젝트 루트
    ├── CLAUDE.md               ← 이 파일
    ├── project.yml             ← xcodegen 스펙
    ├── LocalPay.xcodeproj      ← xcodegen 생성 (커밋 대상)
    ├── LocalPay/
    │   ├── App/                LocalPayApp.swift, RootTabView.swift
    │   ├── Models/             Merchant, PaymentType, MerchantCategory, Review, ...
    │   ├── Data/
    │   │   ├── Repository/     MerchantRepository (protocol)
    │   │   └── Dummy/          DummyMerchantRepository + seed data
    │   ├── DesignSystem/       Colors, Typography, Spacing
    │   ├── Features/
    │   │   ├── Map/
    │   │   ├── Search/
    │   │   ├── MerchantDetail/
    │   │   ├── Favorites/
    │   │   └── MyPage/
    │   ├── Components/         재사용 UI (Chip, Card, Badge, ...)
    │   ├── Utilities/
    │   └── Resources/          Assets.xcassets, Info.plist
    ├── README.md               (Phase 9에서 작성)
    ├── TODO.md                 (Phase 9에서 작성)
    └── API_INTEGRATION.md      (Phase 9에서 작성)
```

## 부록 B — 프로젝트 생성/재생성

```bash
cd LocalPayiOS
xcodegen generate                # project.yml 변경 시 재실행
open LocalPay.xcodeproj

# CLI 빌드
xcodebuild -project LocalPay.xcodeproj -scheme LocalPay \
  -destination 'generic/platform=iOS Simulator' \
  -configuration Debug build
```

- **파일을 추가/이동/삭제한 뒤에는 반드시 `xcodegen generate`를 다시 실행한다.**
- `project.yml`의 `sources` 규칙(`LocalPay/`)이 폴더 하위 `.swift` 파일을 자동으로 포함한다.
- `.xcodeproj`는 xcodegen이 재생성하므로, 그 안을 직접 편집하지 않는다.

## 부록 C — 팀 · Bundle ID

- Bundle Identifier: `com.localpay.ios` (임시 — 사용자가 실제 팀 발급 후 교체)
- Development Team: 미지정 (Xcode에서 수동 지정 가능)
- Deployment Target: iOS 17.0
