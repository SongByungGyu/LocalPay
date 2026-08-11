# API_INTEGRATION — 실 데이터 · 외부 SDK 연결 가이드

> 현재 앱은 모든 데이터를 `DummyMerchantRepository` 로만 제공합니다.
> 실제 데이터 · SDK 를 붙일 때 **정확히 어떤 파일 · 어떤 함수 · 어떤 계약**을 손봐야 하는지 정리합니다.
> 코드 위치는 이 저장소 기준 상대경로입니다.

---

## 1. 온누리상품권 가맹점 공공데이터

### 1.1 데이터 원천 (사전 조사 필요)

- 소상공인시장진흥공단 온누리상품권 가맹점 조회 API
- 지자체별 지역사랑상품권 가맹점 데이터 (예: 경기지역화폐, 인천e음 등)
- 공공데이터포털 개방 API 우선 활용

> 실제 발급받는 API Key 는 **절대 코드에 삽입하지 말 것** (CLAUDE.md §2, §42).

### 1.2 연결 지점

| 대체 대상 | 신규 구현 |
|---|---|
| `LocalPay/Data/Dummy/DummyMerchantRepository.swift` | `LocalPay/Data/Repository/RemoteMerchantRepository.swift` (신규) |
| `DummyMerchantSeed.allMerchants` | 서버 페이지네이션 응답 |

### 1.3 구현 스켈레톤

```swift
// LocalPay/Data/Repository/RemoteMerchantRepository.swift
import CoreLocation
import Foundation

final class RemoteMerchantRepository: MerchantRepository {
    private let baseURL: URL
    private let session: URLSession
    private let apiKey: String   // Config 에서 주입

    init(baseURL: URL, apiKey: String, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.apiKey = apiKey
        self.session = session
    }

    func fetchAll() async throws -> [Merchant] {
        var req = URLRequest(url: baseURL.appending(path: "/merchants"))
        req.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        let (data, _) = try await session.data(for: req)
        return try JSONDecoder.local.decode([Merchant].self, from: data)
    }

    // fetch(id:), search(query:), nearby(center:radiusMeters:), filter(category:payment:) 도 동일 패턴
}
```

### 1.4 주입 지점

- `LocalPay/App/LocalPayApp.swift` 는 현재 스토어만 주입. Repository 는 각 ViewModel `init` 에서 기본값으로 `DummyMerchantRepository()` 사용
- 실제로 교체할 때는 다음 중 하나:
  1. **각 ViewModel 을 초기화하는 화면에서 명시 주입** — 예: `MapHomeView() { MapHomeViewModel(repository: RemoteMerchantRepository(...)) }`
  2. **간단한 서비스 컨테이너 도입** — `AppServices` 신설 후 Environment 로 주입

Repository protocol 자체는 안정적이라 변경 필요 없음.

### 1.5 서버 응답 스키마 (제안)

`Merchant` 모델 필드와 1:1 매핑되도록 서버 스키마를 설계하는 것이 가장 편함.

```jsonc
// GET /v1/merchants?bbox=...&payment=all&category=all
[
  {
    "id": "srv-001",
    "name": "안양중앙시장 행복정육점",
    "category": "food",                       // enum MerchantCategory
    "latitude": 37.3946,
    "longitude": 126.9235,
    "address": "경기 안양시 만안구 만안로 232 안양중앙시장 내",
    "roadAddress": "경기 안양시 만안구 만안로 232",
    "phone": "031-441-1101",
    "supportsOnnuri": true,
    "supportsLocalCurrency": true,
    "localCurrencyName": "안양사랑페이",
    "supportedPaymentTypes": ["onnuriDigital","onnuriPaper","onnuriCard","localCurrency","card"],
    "products": ["삼겹살","목살","한우 등심","선물세트"],
    "businessHours": { "summary": "매일 09:00 - 20:00", "closedNote": "둘째·넷째 일요일 휴무" },
    "rating": 4.7,
    "reviewCount": 128,
    "marketName": "안양중앙시장",
    "description": "3대째 이어온 정육점.",
    "lastVerifiedAt": "2026-08-10T00:00:00Z",
    "reviews": [ /* Review 모델과 동일 */ ],
    "recentPayments": [ /* PaymentVerification 모델과 동일 */ ]
  }
]
```

---

## 2. Kakao Local (장소정보 보완)

### 2.1 사용 시나리오

- 공공데이터에서 좌표가 없거나 부정확한 매장의 좌표 보정
- 검색어 자동완성 (매장 · 상품 이름 + 주변 랜드마크)
- 카테고리 태깅 보완

### 2.2 연결 지점

- 신규 `LocalPay/Utilities/PlaceEnricher.swift` 유틸
  - `func enrich(_ raw: Merchant) async throws -> Merchant`
- **`Merchant` 모델은 변경 없음**. 기존 필드에 값을 보충
- 호출은 `RemoteMerchantRepository` 내부에서 순차 결합 (예: paginated fetch → enrich → cache)

### 2.3 KEY 관리

- Kakao REST API Key
- 저장: `Configuration` 별 `xcconfig` 또는 CI 환경변수
- 노출 방지: `.xcconfig` 는 git ignore, CI 에서 주입

---

## 3. Kakao Map iOS SDK 전환

### 3.1 목표

Apple MapKit MVP 완료 후, 국내 장소 표현 품질을 고려해 Kakao Map 으로 지도 렌더링만 스왑.

### 3.2 원칙

- **`MapHomeViewModel` / `Merchant` / `MapMarkerModel` / `MapRegion` 은 변경 없음.**
- SwiftUI ↔ UIKit SDK 는 `UIViewRepresentable` 로 감쌈.
- 카메라 상태(`MapCameraPosition`) 는 SDK 별로 다르므로, 도메인 중립 `MapRegion` ↔ SDK 좌표 어댑터를 별도 파일로 둔다.

### 3.3 신규/변경 파일

| 신규 | `LocalPay/Features/Map/KakaoMapView.swift` — `UIViewRepresentable` 로 Kakao SDK 감쌈 |
| 신규 | `LocalPay/Features/Map/MapProviderAdapters.swift` — `MapRegion` ↔ Kakao/Apple 좌표 변환 |
| 변경 | `LocalPay/Features/Map/MapHomeView.swift` — Apple `Map` 을 조건부로 `KakaoMapView` 로 스왑 (환경 플래그) |
| 무변경 | `MapHomeViewModel.swift`, 모든 `Models/*`, 모든 `Data/*` |

### 3.4 SDK 도입

- SPM (Kakao 지원 여부 확인 후) 또는 xcframework 수동 통합
- **API Key 는 `.xcconfig` + Info.plist 조합 또는 런타임 secure storage** — 커밋 금지

---

## 4. 개인 상품권 · 지역화폐 잔액 API

### 4.1 현재 상태

- **연결하지 않음.** CLAUDE.md §2, §12, §21 원칙.
- 화면에는 항상 **"DEMO"** 뱃지가 노출됨 (`Features/MyPage/BalanceCard.swift`).
- 개발 편의 스위치 (MY 상단 Toggle) 로 예시 금액 표시 On/Off.

### 4.2 실 연동 시 파일

| 신규 | `LocalPay/Data/Wallet/WalletService.swift` (protocol) |
| 신규 | `LocalPay/Data/Wallet/OnnuriWalletService.swift`, `LocalCurrencyWalletService.swift` |
| 변경 | `LocalPay/Features/MyPage/BalanceCard.swift` — hardcoded `demoBalance` 대신 서비스 결과 사용 |
| 변경 | `LocalPay/Features/MyPage/MyPageHomeView.swift` — 서비스 주입 |

### 4.3 유의

- 실 개인 금융정보 · 잔액은 로컬 저장 금지 (CLAUDE.md §36, §42).
- Keychain 또는 서버 세션 기반으로만 접근.

---

## 5. Backend (자체 서버)

### 5.1 최종 목표 아키텍처 (CLAUDE.md §27, §45)

```
iOS App (SwiftUI)
    │
    ↓ HTTPS + async/await
Our Backend API
    │
    ↓
PostgreSQL + PostGIS
    │
    ├─ 온누리 데이터 (공공데이터 스냅샷 · 정기 sync)
    ├─ 지역화폐 데이터 (지자체 API · 정기 sync)
    └─ 사용자 데이터 (Merchant metadata / Review / Favorite / PaymentVerification)
```

### 5.2 iOS 관점 준비

- `Merchant` 모델은 서버 응답 스키마와 1:1 매핑 가능하게 설계됨 (Codable 채택 완료)
- `Review`, `PaymentVerification`, `BusinessHours` 도 Codable
- 서버 검색 · 필터는 `MerchantRepository` protocol 시그니처를 그대로 사용

---

## 6. Wallet Connection · OAuth (원거리 로드맵)

- Apple Sign-in / Kakao Sign-in 도입 시 `AuthenticationServices` 또는 Kakao SDK 사용
- 사용자 계정 발급 후에 즐겨찾기 · 후기 서버 동기화

---

## 7. 요약: "어디를 손대야 실 데이터에 붙는가"

| 붙이려는 데이터 | 만들거나 바꿔야 할 파일 |
|---|---|
| 온누리·지역화폐 매장 목록 | (신규) `Data/Repository/RemoteMerchantRepository.swift` |
| 상세/검색/근처 | 위 클래스에서 다른 메서드도 구현 |
| Kakao Local 보정 | (신규) `Utilities/PlaceEnricher.swift` + Repository 내 호출 |
| Kakao Map 지도 | (신규) `Features/Map/KakaoMapView.swift` + `MapHomeView` 스왑 로직 |
| 개인 잔액 | (신규) `Data/Wallet/WalletService.swift` + `BalanceCard` 바인딩 변경 |
| 사용자 인증 | (신규) `Features/Auth/…` + Repository 계약 확장 |

**공통적으로, 도메인 모델(`Models/*`) 과 ViewModel 대부분은 변경할 필요가 없어야 합니다.** 그게 지금 이 구조를 만든 이유입니다.
