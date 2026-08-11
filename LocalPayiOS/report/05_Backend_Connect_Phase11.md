# 05. Backend Connect Phase 11 — iOS ↔ FastAPI 실 연결

- 보고일: 2026-08-11
- 이전 단계: Phase 10 (`e31274c feat(backend): FastAPI + PostgreSQL/PostGIS 1차 서버`)
- 상태: **회사 Mac Simulator 에서 SSH 터널 경유로 VPS 서버에 연결. Unit Test 7건 통과. UI 무변경.**

## 한 줄 요약

`DummyMerchantRepository` 를 그대로 두고 `RemoteMerchantRepository` 를 신규 구현해 iOS 앱이 `http://127.0.0.1:18080` (SSH 터널 → VPS FastAPI) 로 실제 매장 데이터를 받아옵니다. `Merchant` 도메인 모델·기존 UI/UX·`LocalPayApp` DI 는 변경하지 않았고, Preview / XCTest 에서는 Factory 가 자동으로 Dummy 로 폴백합니다.

## 신규/변경 파일

| 종류 | 파일 | 역할 |
|---|---|---|
| 신규 | `LocalPay/Data/Network/AppConfiguration.swift` | Base URL 관리 (DEBUG=`127.0.0.1:18080`, Release=placeholder) |
| 신규 | `LocalPay/Data/Network/NetworkError.swift` | `invalidURL / invalidResponse / httpStatus / decoding / transport` + 사용자 안전 문구 |
| 신규 | `LocalPay/Data/Network/JSONDecoder+LocalPay.swift` | fractional-seconds 포함/미포함 ISO-8601 Date 를 모두 처리 |
| 신규 | `LocalPay/Data/Network/HTTPClient.swift` | `URLSession` + `async/await` GET wrapper |
| 신규 | `LocalPay/Data/Repository/RemoteMerchantRepository.swift` | 4개 API 매핑. `search` 는 fetchAll + 로컬 필터 (Phase 11 서버 검색 없음) |
| 신규 | `LocalPay/Data/RepositoryFactory.swift` | Preview/Test → Dummy, 그 외 → Remote |
| 신규 | `LocalPayTests/RemoteMerchantRepositoryDecodingTests.swift` | 실 서버 응답 샘플 + fractional Date decode 검증 (7 tests) |
| 변경 | `LocalPayiOS/project.yml` | `NSAllowsLocalNetworking: true`, `LocalPayTests` target 추가 |
| 변경 | `LocalPayiOS/LocalPay/Resources/Info.plist` | `NSAllowsLocalNetworking: true` (HTTP localhost 허용) |
| 변경 | `Features/Map/MapHomeViewModel.swift` | init default 를 `RepositoryFactory.makeMerchantRepository()` 로 |
| 변경 | `Features/Search/SearchViewModel.swift` | 동일 |
| 변경 | `Features/MerchantDetail/MerchantDetailViewModel.swift` | 동일 |

**LocalPayApp.swift 는 변경하지 않았음.** 기존 `FavoritesStore` · `ReviewsStore` environment 주입 구조 그대로 유지.

## 엔드포인트 매핑

| Repository 메서드 | 서버 |
|---|---|
| `fetchAll()` | `GET /api/v1/merchants?limit=1000` |
| `fetch(id:)` | `GET /api/v1/merchants/{id}` (404 → `nil`, 그 외 → throw) |
| `search(query:)` | `fetchAll()` + `DummyMerchantRepository` 와 동일한 로컬 필터 규칙 재사용 |
| `nearby(center:, radiusMeters:)` | `GET /api/v1/merchants/nearby?lat&lng&radius&limit=500` |
| `filter(category:, payment:)` | `GET /api/v1/merchants?category&payment&limit=1000` (`all` 은 파라미터 생략) |

## Date Decoding 세부

- 서버 실 응답 예: `"2026-08-10T06:03:17.625283Z"` — microseconds(6자리) + `Z`.
- 기본 `JSONDecoder.dateDecodingStrategy = .iso8601` 은 fractional seconds 를 처리하지 못하므로 **custom strategy** 사용.
- `LocalPayDateFormatters.parse` 가 `withFractionalSeconds` → `withInternetDateTime` 순으로 시도. 두 형태 모두 지원.
- 테스트로 안전 확인:
  - `testDate_withFractionalSeconds_decodes`
  - `testDate_withoutFractionalSeconds_decodes`
  - `testDate_invalid_returnsNil`
  - `testMerchant_realServerSample_decodes` (실 서버 `m-001` 응답 축약본)
  - `testMerchantArray_withDistanceMeters_decodes` (실 서버 `/nearby` 응답 축약본)

## DI 전략 — RepositoryFactory

```swift
if isRunningInPreview || isRunningInTests { return DummyMerchantRepository() }
return RemoteMerchantRepository(baseURL: AppConfiguration.current.apiBaseURL)
```

- `XCODE_RUNNING_FOR_PREVIEWS == "1"` → SwiftUI Preview 는 Dummy
- `NSClassFromString("XCTestCase") != nil` → XCTest 는 Dummy
- 그 외 → Remote

ViewModel default parameter 만 팩토리로 교체하고 View 코드는 무변경. Preview 는 여전히 오프라인 Dummy 로 렌더링됨.

## 검증

| 항목 | 결과 |
|---|---|
| `xcodegen generate` | ✅ |
| `xcodebuild ... clean build` (iOS Simulator, Debug) | ✅ `** BUILD SUCCEEDED **` |
| `xcodebuild ... test` (iPhone 15 Simulator, iOS 18.0) | ✅ `Executed 7 tests, with 0 failures` |
| `curl /health` (SSH 터널 경유) | ✅ `{"status":"ok",...}` |
| `curl /api/v1/merchants?limit=1` | ✅ 실 응답 확인 |
| Simulator 앱 launch | ✅ crash 없이 정상 실행 |

## 남은 확인 사항 (사용자 수동)

- Simulator 에서 25개 Marker 표시 · 필터 · 상세 · 즐겨찾기 UX 시각적 검증
- 위치 권한 허용 후 `/nearby` 실 호출 흐름 (현재는 필터/전체만 호출됨)
- 네트워크 단절 시 사용자 에러 표시 문구 (`NetworkError.userMessage`) 확인

## 다음 후보

1. 지도 카메라 이동 시 `/api/v1/merchants/map` (BBOX) 호출로 마커 자동 재조회
2. 서버 Search endpoint (Phase 11+) 도입 후 `search(query:)` 를 서버 검색으로 스왑
3. 실 공공데이터 sync + Bearer 토큰 인증 (Phase 12)
4. 오프라인 fallback (`DummyMerchantRepository`) 자동 전환 정책
