# 08. Claude Code용 마스터 개발 프롬프트

아래 내용을 Claude Code에 그대로 전달한다.

---

## START PROMPT

너는 이 프로젝트의 **Senior Android Engineer + Product Engineer**다.

현재 디렉터리에 있는 LocalPay Map 기획 문서를 먼저 전부 읽어라.

읽을 순서:

1. `00_README.md`
2. `01_SERVICE_PLANNING.md`
3. `02_SERVICE_DEFINITION.md`
4. `03_DESIGN_SYSTEM.md`
5. `04_UI_SPEC.md`
6. `05_REQUIREMENTS_SPEC.md`
7. `06_DATA_API_ARCHITECTURE.md`
8. `07_ANDROID_TECH_SPEC.md`
9. `09_ACCEPTANCE_CHECKLIST.md`

`prototype/index.html`이 있다면 화면 구조/인터랙션 참고용으로 확인하되, HTML 디자인을 그대로 기계적으로 복제하지 말고 디자인/UI 규격서를 우선한다.

### 프로젝트 목표

온누리상품권/지역화폐 사용 가능 매장을 지도에서 검색하는 Android MVP를 만든다.

핵심 흐름:

```text
앱 실행
→ 지도
→ 결제수단/카테고리 필터
→ 핀 선택
→ 가맹점 미리보기
→ 상세
→ 상품/결제수단/후기 확인
→ 즐겨찾기
```

### 반드시 지킬 것

- Kotlin + Jetpack Compose로 구현한다.
- ViewModel + StateFlow + Repository 구조를 사용한다.
- 최초 단계에서는 `DummyMerchantRepository`를 사용해 서버 없이 전체 UX가 동작해야 한다.
- UI에서 repository 구현체를 직접 참조하지 않는다.
- 온누리/지역화폐 지원 상태는 `SUPPORTED / NOT_SUPPORTED / UNKNOWN`을 구분한다.
- 실제 잔액 API가 없으므로 release 성격 화면에서 실제 잔액처럼 보이는 값을 만들지 않는다.
- 개발용 더미 잔액을 쓸 경우 화면에 `DEMO` 또는 `더미` 표시를 한다.
- 네이버/카카오 리뷰를 크롤링하거나 우회 API로 가져오지 않는다.
- 비공개 API, 사용자 계정 자동 로그인, HTML 파싱 방식으로 상품권 잔액을 수집하지 않는다.
- API Key/Secret을 Git에 넣지 않는다.
- paid API 호출이나 실제 외부 서비스 비용 발생 작업을 임의로 하지 않는다.
- 외부 SDK/API 버전은 현재 공식 문서를 확인한 뒤 안정 버전을 선택하고 Version Catalog로 관리한다.
- 기존 repository가 있다면 구조를 먼저 분석하고 불필요하게 초기화/삭제하지 않는다.

### 지도

지도 Provider는 Kakao Map Android SDK를 우선한다.

단, 다음을 분리한다.

- Domain `GeoPoint`, `GeoBounds`
- Map UI Adapter
- MerchantRepository

Business 로직/ViewModel이 Kakao SDK 타입에 직접 의존하지 않도록 한다.

Kakao key가 아직 없거나 SDK 연결을 바로 할 수 없는 경우:

1. 앱 구조/화면/더미 데이터부터 구현한다.
2. `MapContent`를 추상화한다.
3. SDK 연결 지점을 TODO와 명확한 setup 문서로 남긴다.
4. 단순 회색 박스로 끝내지 말고 가맹점 리스트/선택 UX는 검증할 수 있게 만든다.

### Dummy Dataset

최소 20개의 가맹점을 만든다.

반드시 포함:

- 온누리만 5개 이상
- 지역화폐만 5개 이상
- 둘 다 5개 이상
- 정보 UNKNOWN 사례
- 음식점/카페/약국/마트/시장/식품/미용/생활
- 상품명 검색이 가능한 데이터
- 후기 있음/없음
- 최근 결제 확인 있음/없음

### 화면

P0 화면을 모두 구현한다.

- 지도 홈
- 검색
- 가맹점 상세
- 후기 목록/작성 더미
- 즐겨찾기
- MY
- 설정/데이터 출처 최소 화면

### 지도 홈 UI

- 상단 Search Bar
- 온누리/지역화폐 Filter Chips
- Category Chips
- Map
- Current Location
- Search This Area
- Marker/Cluster
- Merchant Peek Card
- Bottom Navigation

### 디자인

`03_DESIGN_SYSTEM.md`, `04_UI_SPEC.md`의 token/spacing/size를 따른다.

Compose Theme에 색/typography/shape를 token화한다.

### 검색

가맹점명 + 상품명 + 카테고리 검색을 지원한다.

예:

`삼겹살` 검색 → products에 삼겹살이 있는 매장 검색.

### 즐겨찾기

Room으로 저장해 앱 재실행 후 유지되게 한다.

### 후기

MVP에서 local repository로 작성/목록 동작이 가능하면 좋다.

리뷰 필드:

- rating
- paymentResult
- paymentType
- purchasedItem
- body
- createdAt

### MY

Development build에서만 샘플 잔액을 표시할 수 있다.

Release/MVP에서는:

- `잔액 연동 준비중`
- 연결 가능한 공식 앱/서비스 링크를 나중에 붙일 수 있는 구조

으로 만든다.

### 에러/상태

모든 주요 화면에:

- Loading
- Content
- Empty
- Error

를 구현한다.

위치 권한 거절 상태도 정상 UX로 처리한다.

### 테스트

최소:

- filter logic unit test
- dummy repository test
- map/search ViewModel state test
- favorite repository test

가능하면 Compose UI smoke test도 추가한다.

### 작업 방식

1. 먼저 repository/현재 디렉터리를 분석한다.
2. 문서 요구사항을 요약한 뒤 구현 단계별 TODO를 만든다.
3. 프로젝트가 없으면 새 Android Compose 프로젝트를 생성한다.
4. Domain/Repository/Theme/Navigation부터 만든다.
5. Dummy MVP를 완성한다.
6. 빌드/테스트를 실행한다.
7. 빌드 오류가 있으면 수정한다.
8. 마지막에 변경 파일 목록과 실행 방법, 남은 TODO를 보고한다.

### 완료 보고 형식

```text
1. 구현 완료 기능
2. 변경/생성 파일
3. 테스트/빌드 결과
4. Kakao Map Key 설정 방법
5. 아직 Dummy인 데이터
6. 실제 API 연결 시 교체할 Repository
7. Phase 2 TODO
```

질문이 없어도 문서를 기준으로 합리적인 기본값을 선택해서 진행한다. 기능 범위를 임의로 크게 늘리지 않는다.

## END PROMPT
