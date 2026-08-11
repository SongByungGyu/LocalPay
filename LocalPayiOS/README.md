# LocalPay iOS (Dummy MVP)

> 사용자가 **가진 온누리상품권 · 지역화폐로 무엇을 어디에서 살 수 있는지** 지도에서 가장 빠르게 알려주는 iOS 앱.
> 현 단계는 실서버 없이 동작하는 완성도 높은 Dummy MVP.

## 프로젝트 소개

- 서비스명(가칭): **LocalPay**
- 목표: 온누리상품권 · 지역화폐 사용 가능 매장을 지도 · 검색 · 즐겨찾기 흐름으로 탐색
- 차별점: 단순 위치가 아니라 **"내가 가진 상품권으로 무엇을 살 수 있는가"** 를 해결. 결제 인증형 후기 + 최근 결제 확인 로그 노출
- 현재 단계: **UI/UX + 아키텍처 완성**. 실 공공데이터 / 지역화폐 API / 개인 잔액 API 미연결

## 지원 iOS

- iOS 17.0+ (SwiftUI 신 Map API 사용)
- Swift 5.10
- Xcode 16 / 17 이상 권장 (개발은 Xcode 26.4 로 확인)

## 기술 Stack

| 영역 | 사용 기술 |
|---|---|
| UI | SwiftUI, NavigationStack, `Layout` protocol (Flow chip) |
| 상태 | `@Observable` (Observation framework) |
| 비동기 | Swift Concurrency (`async`/`await`, `Task`) |
| 지도 | Apple **MapKit** — iOS 17 신 `Map(position:selection:)` + `Annotation` |
| 위치 | CoreLocation (`CLLocationManager`) |
| 저장 | UserDefaults (즐겨찾기 · 사용자 후기) |
| 외부 라이브러리 | **없음** (Apple 기본 프레임워크만 사용) |
| 프로젝트 생성 | [xcodegen](https://github.com/yonaskolb/XcodeGen) (`project.yml` → `LocalPay.xcodeproj`) |

## Project Structure

```
LocalPayiOS/
├── CLAUDE.md                        ← iOS 프로젝트 전용 마스터 프롬프트
├── project.yml                      ← xcodegen 스펙 (사실상 프로젝트 정의)
├── LocalPay.xcodeproj               ← xcodegen 재생성 산출물
├── README.md                        ← 이 파일
├── TODO.md                          ← 다음 개발 단계 정리
├── API_INTEGRATION.md               ← 실 데이터 연결 지점 안내
└── LocalPay/
    ├── App/
    │   ├── LocalPayApp.swift        ← @main + 전역 스토어 주입
    │   └── RootTabView.swift        ← 4-Tab (지도/검색/즐겨찾기/MY)
    │
    ├── Models/                      ← Merchant, PaymentType, MerchantCategory,
    │                                   Review, PaymentVerification, BusinessHours,
    │                                   MapRegion, MapMarkerModel, PaymentFilter
    ├── Data/
    │   ├── Repository/
    │   │   └── MerchantRepository.swift        ← protocol
    │   └── Dummy/
    │       ├── DummyMerchantRepository.swift   ← 인메모리 구현체
    │       └── DummyMerchantSeed.swift         ← 안양 25개 가상 매장
    │
    ├── DesignSystem/                ← AppColor / AppTypography / AppSpacing
    │
    ├── Components/                  ← 재사용 UI (Chip, Card, Badge, ...)
    │   ├── AppSearchBar / PaymentBadge / PaymentBadgeStyle
    │   ├── MerchantCard / MerchantMarker
    │   ├── CategoryChip / PaymentFilterChip / ProductChip
    │   ├── RatingView / SectionHeader / FavoriteToggleButton
    │   ├── FloatingLocationButton
    │   ├── EmptyStateView / LoadingView
    │   └── PhaseOnePlaceholder / (초기 스켈레톤용)
    │
    ├── Features/
    │   ├── Map/         MapHomeView + MapHomeViewModel + MerchantPreviewCard
    │   ├── Search/      SearchHomeView + SearchViewModel + SortOption
    │   ├── MerchantDetail/  MerchantDetailView + ViewModel
    │   ├── Favorites/   FavoritesHomeView + FavoritesStore
    │   ├── Reviews/     ReviewsStore + ReviewCard + ReviewComposerView
    │   └── MyPage/      MyPageHomeView + BalanceCard + CurrencyPolicyCard
    │
    ├── Utilities/       LocationService / GeoDistance / DateHelper / DistanceFormatter
    │
    └── Resources/
        ├── Info.plist   위치 권한 문구 포함
        └── Assets.xcassets/
            ├── AccentColor.colorset
            ├── AppIcon.appiconset
            └── Colors/  (Background / Surface / Primary / Onnuri /
                          LocalCurrency / Both / TextPrimary / TextSecondary /
                          Divider / Success / Error — Dark Mode 대응)
```

## 실행 방법

```bash
# 1) xcodegen 설치 (최초 1회)
brew install xcodegen

# 2) 프로젝트 클론 후 이 폴더로 진입
cd LocalPayiOS

# 3) 프로젝트 재생성 (project.yml / 파일 추가 · 이동 · 삭제 시마다 필요)
xcodegen generate

# 4) Xcode 로 열기
open LocalPay.xcodeproj

# CLI 빌드
xcodebuild \
  -project LocalPay.xcodeproj \
  -scheme LocalPay \
  -destination 'generic/platform=iOS Simulator' \
  -configuration Debug build
```

- Xcode 에서 스킴 = `LocalPay`, 시뮬레이터 = iPhone 15/16 계열 권장
- Bundle Identifier = `com.localpay.ios` (임시). 실기기 배포 시 팀 지정 필요
- 위치 권한 문구는 `Info.plist` 의 `NSLocationWhenInUseUsageDescription` 참고

## Dummy Data 설명

- 위치: `LocalPay/Data/Dummy/DummyMerchantSeed.swift`
- **총 25개 가상 매장**, 좌표는 안양시청 (37.3943, 126.9568) 반경 약 3 km
- 카테고리: `restaurant / cafe / pharmacy / mart / market / food / beauty / life / etc` 골고루 배분
- 결제 조합: **온누리만 / 지역화폐만 / 둘 다 / 둘 다 미지원** 케이스 모두 포함 (Marker · Badge 검증용)
- 리뷰 · 최근 결제 · 판매 상품 · 시장명 · 영업시간 등 상세 필드 포함
- 사용자가 앱 안에서 새로 작성한 리뷰는 `ReviewsStore` → `UserDefaults` 로 별도 보관 (seed 를 덮어쓰지 않음)
- 즐겨찾기는 `FavoritesStore` → `UserDefaults`
- 모든 잔액 · 지역화폐 혜택 정보는 **"DEMO" 뱃지** 로 표시. 실제 값 아님 (CLAUDE.md §12)

## 지도 구조

지도 SDK 종속을 최소화하기 위해 **다음 3 계층으로 분리**했습니다.

```
[SwiftUI View]  MapHomeView          ← MapKit 을 직접 참조
      │
      ↓ 관찰
[ViewModel]     MapHomeViewModel     ← Merchant, MapMarkerModel 만 노출 (MapKit 미참조)
      │
      ↓ 사용
[Domain]        Merchant / MapMarkerModel / MapRegion   ← MapKit 클래스 미사용, 좌표는 원시 Double
```

- 좌표는 항상 `Double(latitude, longitude)` 로 보관 → `CLLocationCoordinate2D` computed property 로 노출
- `MapMarkerModel`, `MapRegion` 은 **어떤 지도 SDK 도 몰라야 한다** 는 원칙 유지
- 실제 지도 렌더링과 카메라 제어(`MapCameraPosition`) 만 `MapHomeView` 에서 MapKit 을 사용

## 향후 Kakao Map 전환 방법

`API_INTEGRATION.md` 상세 참조. 요약:

1. `Kakao Map iOS SDK` 를 추가 (SPM 또는 xcframework)
2. `LocalPay/Features/Map/` 하위에 `KakaoMapView.swift`(UIViewRepresentable) 를 추가
3. `MapHomeView` 안에서 조건부로 `AppleMapView` / `KakaoMapView` 를 스왑
4. `MapHomeViewModel` 은 **수정 불필요** (Merchant / MapMarkerModel 만 노출)
5. `MapRegion` → Kakao SDK 좌표 변환 어댑터만 추가

**ViewModel · Repository · Merchant 모델을 손대지 않는 게 이 구조의 목적**입니다.

## 향후 Backend 연결 방법

`API_INTEGRATION.md` 상세 참조. 요약:

1. 새 파일 `LocalPay/Data/Repository/RemoteMerchantRepository.swift` 생성 → `MerchantRepository` 채택
2. `URLSession` 기반 `async` fetch 구현
3. `LocalPayApp` 또는 각 ViewModel 의 `init` 에서 주입 대상만 교체
4. 도메인 모델(`Merchant` 등) 은 그대로 사용 (Codable 채택 이미 완료)

## 실제 온누리/지역화폐 데이터 연결 위치

| 데이터 | 연결 지점 |
|---|---|
| 온누리상품권 공공데이터 | `RemoteMerchantRepository.fetchAll()` → seed 대체 |
| 지역사랑상품권 가맹점 데이터 | 위와 동일. `Merchant.supportsLocalCurrency` / `localCurrencyName` 필드 채우기 |
| Kakao Local (장소 보완) | 매장 검색 · 좌표 보정 시 별도 `PlaceEnricher` 유틸에서 호출 |
| 개인 잔액 API | `Features/MyPage/BalanceCard.swift` — 현재 DEMO 잔액. 실 연동 시 `WalletService` 신설 후 주입 |
| 최근 결제 확인 로그 | `Merchant.recentPayments` — 서비스 오픈 시 서버 이벤트 스트림으로 대체 |

## 현재 구현되지 않은 기능

- 실서버 연동 (모든 데이터는 인메모리 Dummy)
- 회원 가입 · 로그인 · 인증
- 실제 개인 상품권/지역화폐 잔액 조회
- 실제 결제 · 상품권 사용 처리
- Push 알림 · Deep Link
- 이미지 자산 (매장 대표 이미지는 카테고리 아이콘 + 결제수단 색상 그라디언트로 대체)
- Kakao Map / KakaoLocal SDK
- 앱 아이콘 이미지 (placeholder appiconset 만 존재)
- Unit / UI Test 코드

## 완료된 MVP 사용자 흐름 (Simulator 확인)

CLAUDE.md §43 기준 흐름이 전부 동작합니다.

1. 앱 실행 → 지도 홈 (안양 중심 fallback)
2. 온누리 필터 선택 → 마커 색·아이콘·개수 즉시 변경
3. 카테고리 (음식점 등) 선택 → 지도 필터링
4. 마커 탭 → 하단 Preview Card
5. "상세보기" → Merchant Detail 화면
6. 판매 상품 · 결제 가능 상품권 · 최근 결제 확인 · 후기 확인
7. 하트로 즐겨찾기 등록
8. 즐겨찾기 Tab → 목록에 반영 (앱 재실행 후에도 유지)
9. 검색 Tab → "삼겹살" · "약국" 등 검색 / 거리·평점·후기순 정렬
10. MY Tab → 프로필, DEMO 잔액, 지역화폐 혜택 카드, 스탯

## 참고 문서

- `CLAUDE.md` — 이 프로젝트 마스터 프롬프트 (요구사항 원본)
- `TODO.md` — 다음 단계 백로그
- `API_INTEGRATION.md` — 실 API 연결 매핑
- `../LocalPay_Claude_Handoff/` — (원래 Android 대상이었던) 기획 · UI · 데이터 아키텍처 참고 문서
