# 07. Android 기술 설계서

## 1. Target

- Language: Kotlin
- UI: Jetpack Compose
- Design: Material 3 기반 custom theme
- Min SDK: 프로젝트 착수 시 최신 앱 전략에 맞춰 결정하되, MVP 제안 `minSdk 26+`
- Compile/Target SDK: 개발 시점 최신 안정 버전 사용

SDK 숫자는 문서에 하드코딩하지 말고 실제 프로젝트 생성 시 설치된 안정 버전을 확인한다.

---

## 2. Dependencies

권장:

- AndroidX Core
- Jetpack Compose
- Material 3
- Navigation Compose
- Lifecycle ViewModel Compose
- Kotlin Coroutines
- StateFlow
- Hilt
- Retrofit
- OkHttp
- Kotlin serialization 또는 Moshi 중 하나
- Room
- Coil
- Google Play Services Location
- Kakao Map Android SDK

버전은 Version Catalog(`libs.versions.toml`)로 관리한다.

---

## 3. Architecture

과한 멀티모듈은 MVP에서 피한다.

권장 단일 app 모듈 패키지:

```text
com.example.localpay
  ├─ app
  ├─ core
  │   ├─ ui
  │   ├─ model
  │   └─ util
  ├─ data
  │   ├─ local
  │   ├─ remote
  │   ├─ dummy
  │   └─ repository
  ├─ domain
  │   ├─ model
  │   └─ repository
  └─ feature
      ├─ map
      ├─ search
      ├─ merchantdetail
      ├─ review
      ├─ favorite
      └─ my
```

---

## 4. State Management

각 Feature:

```text
Screen
  ↓ event
ViewModel
  ↓
Repository
  ↓
Data Source
```

UI State:

```kotlin
sealed interface MapUiState {
    data object Loading : MapUiState
    data class Content(
        val merchants: List<MerchantUiModel>,
        val filters: MapFilterState,
        val selectedMerchantId: String?
    ) : MapUiState
    data class Error(val message: String) : MapUiState
}
```

가능하면 event/state를 명시적으로 관리한다.

---

## 5. Repository

```kotlin
interface MerchantRepository {
    fun observeMerchants(query: MerchantQuery): Flow<List<Merchant>>
    suspend fun getMerchant(id: String): Merchant
    suspend fun search(query: SearchQuery): List<Merchant>
}
```

구현:

```text
DummyMerchantRepository       // MVP first
RemoteMerchantRepository      // later
```

`BuildConfig` 또는 DI binding으로 모드를 전환한다.

---

## 6. Map Abstraction

카카오맵을 우선 사용하지만 Business/UI state는 SDK 객체를 직접 보관하지 않는다.

Domain:

```kotlin
data class GeoBounds(...)
data class GeoPoint(...)
data class MapCameraState(...)
```

지도 Composable 내부 adapter에서 Kakao SDK 타입으로 변환한다.

목적:

- 테스트 가능
- Kakao SDK 변경 영향 최소화
- 향후 Naver Map 전환 가능성 보존

---

## 7. Kakao Map 사용 원칙

- Native App Key는 `local.properties`/Gradle secret 처리
- repository에 key 커밋 금지
- 지도 초기화 실패 UI 준비
- marker bitmap/resource는 앱 theme와 일치
- 화면 이동 연속 callback에서 API 재조회 남발 금지

`Search This Area` UX를 사용해 사용자의 명시적 액션으로 서버 조회를 줄일 수 있다.

---

## 8. 위치 권한

권한:

- Fine location 필요 시 요청
- Coarse fallback 고려

UX:

1. 기능 설명
2. 시스템 권한 요청
3. 거절 → 기본 지역 사용
4. 설정 이동 CTA는 영구 거절 상태에만 표시

위치 권한이 없다는 이유로 앱을 막지 않는다.

---

## 9. Navigation

Top-level:

```text
MapRoute
SearchRoute
FavoriteRoute
MyRoute
```

Detail:

```text
MerchantDetail/{merchantId}
ReviewList/{merchantId}
ReviewWrite/{merchantId}
Settings
```

Merchant 객체 전체를 navigation argument로 넘기지 말고 ID를 넘긴다.

---

## 10. Room

MVP 용도:

- favorites
- recent_search
- local_reviews(optional)
- last_map_location(optional)

Remote merchant 전체 캐시는 서버 단계에서 추가.

---

## 11. Testing

### Unit

- Filter predicate
- Category mapping
- MerchantRepository dummy
- ViewModel state transition
- SupportStatus UNKNOWN 처리

### UI

최소 smoke:

- Map screen renders
- Filter chip selection
- Merchant peek card
- Detail navigation
- Favorite toggle

지도 SDK 자체는 instrumentation에서 과도하게 테스트하지 않는다.

---

## 12. Build Config

예:

```text
BuildType: debug / release
DataMode: dummy / remote
```

Debug:

- Dummy wallet 가능
- debug badge 표시

Release MVP:

- Dummy wallet 금지
- remote가 준비되지 않았다면 `연동 준비중` 표시

---

## 13. Logging

개인 위치/민감정보를 평문 로그로 남기지 않는다.

Debug log 예:

- map bounds query
- repository result count
- filter state

Release에서는 최소화.

---

## 14. 에러 모델

```kotlin
sealed class AppError {
    data object Network : AppError()
    data object LocationPermissionDenied : AppError()
    data object DataUnavailable : AppError()
    data class Unknown(val cause: Throwable) : AppError()
}
```

사용자 문구와 기술 error를 분리한다.

---

## 15. 개발 순서

### Step A — Scaffold

- Compose project
- Theme
- Navigation
- Domain models
- Repository interfaces

### Step B — Dummy MVP

- Dummy merchants
- 지도 홈
- 필터
- 상세
- 검색
- 즐겨찾기
- MY
- 후기

### Step C — Kakao Map

- SDK 연결
- marker
- camera/bounds
- location
- cluster

### Step D — Remote-ready

- Retrofit DTO/API interfaces
- Remote repository skeleton
- error/empty/loading

### Step E — Public Data Backend

Android MVP 완료 후 별도 서버 프로젝트로 진행 권장.
