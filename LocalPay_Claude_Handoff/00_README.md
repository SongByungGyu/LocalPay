# LocalPay Map — Claude 개발 인수인계 패키지

> 작업명(가칭): **LocalPay Map**  
> 대상: Android 우선 개발  
> 문서 기준일: 2026-08-11  
> 목적: 온누리상품권/지역화폐 사용처를 지도에서 탐색하고, 실제 사용 정보와 후기까지 확인하는 모바일 서비스의 MVP 개발

---

## 1. 이 패키지의 목적

이 폴더는 Claude Code/Claude에게 프로젝트를 넘겼을 때 별도 설명 없이도 MVP를 구현할 수 있도록 만든 인수인계 문서다.

핵심 서비스는 다음 한 문장으로 정의한다.

> **“내 주변에서 내가 가진 온누리상품권 또는 지역화폐를 어디서, 무엇을 살 때 사용할 수 있는지 가장 빠르게 알려주는 지도 앱.”**

MVP의 핵심은 **잔액 조회가 아니라 사용처 탐색 경험**이다. 개인 잔액 API는 공개 연동 가능 여부/제휴가 확정되지 않았으므로 MVP에서는 실제 잔액 조회를 구현하지 않는다.

---

## 2. Claude가 읽을 순서

1. `01_SERVICE_PLANNING.md` — 서비스 목표, 사용자, MVP 범위
2. `02_SERVICE_DEFINITION.md` — 화면/기능/사용자 플로우
3. `03_DESIGN_SYSTEM.md` — 디자인 원칙, 컬러, 컴포넌트
4. `04_UI_SPEC.md` — Android dp/sp 기준 상세 UI 규격
5. `05_REQUIREMENTS_SPEC.md` — 기능/비기능 요구사항과 우선순위
6. `06_DATA_API_ARCHITECTURE.md` — 공공데이터, 서버, DB, API 구조
7. `07_ANDROID_TECH_SPEC.md` — Android 기술스택/패키지/상태관리
8. `08_CLAUDE_MASTER_PROMPT.md` — Claude Code 실행용 메인 프롬프트
9. `09_ACCEPTANCE_CHECKLIST.md` — MVP 완료 판정 체크리스트

`prototype/index.html`은 이미 만든 HTML 더미 화면이다. 디자인의 절대 기준은 아니며 **인터랙션/정보구조 참고용**이다.

---

## 3. MVP 핵심 범위

### 반드시 구현

- 지도 중심 홈
- 현재 위치 또는 기본 위치 표시
- 온누리 / 지역화폐 / 둘 다 필터
- 음식점 / 카페 / 약국 / 마트 / 시장 / 식품 / 미용 / 생활 등 카테고리 필터
- 지도 영역 내 가맹점 핀/클러스터
- 가게명/상품명 검색
- 가맹점 미리보기 카드
- 가맹점 상세
- 결제수단/취급상품/주소/전화/최근 확인일 표시
- 자체 후기 UI와 더미 후기
- 즐겨찾기
- MY
- 잔액 영역은 **연동 준비중 또는 더미**로 표시
- 실제 API가 없어도 완성된 UX를 검증할 수 있는 Repository 기반 Dummy Data Mode

### MVP에서 제외

- 실제 결제/충전
- 실시간 온누리/지역화폐 개인 잔액 조회
- 네이버/카카오 리뷰 스크래핑
- 가맹점 정산
- 사장님 인증/관리 페이지
- 광고/결제 수익화
- 관리자 웹

---

## 4. 기술 방향 요약

- Android: Kotlin + Jetpack Compose
- Architecture: ViewModel + StateFlow + Repository
- Map: Kakao Map Android SDK 우선
- Location: Fused Location Provider
- Network: Retrofit + OkHttp + Kotlin Coroutines
- DI: Hilt
- Local cache: Room
- Image: Coil
- Backend 권장: REST API + PostgreSQL + PostGIS
- 공공데이터: 온누리 전국 가맹점 현황 + 한국조폐공사 통합 지역사랑상품권 가맹점 정보
- 장소 보강: Kakao Local REST API

---

## 5. 개발 원칙

1. UI가 데이터 공급자에 직접 의존하지 않는다.
2. `MerchantRepository`를 통해 Dummy/Remote를 교체 가능하게 한다.
3. 지도 SDK도 가능한 한 화면 로직과 분리한다.
4. API Key/Secret은 코드와 Git에 포함하지 않는다.
5. 외부 리뷰를 무단 수집하지 않는다.
6. 가맹점의 “상품권 사용 가능” 여부는 지도 사업자 데이터가 아니라 **우리 DB의 출처가 있는 데이터**로 판정한다.
7. 공공데이터는 최신성이 늦을 수 있으므로 `sourceUpdatedAt`, `lastVerifiedAt`을 사용자에게 표시 가능한 구조로 유지한다.
8. MVP에서는 가짜 데이터임을 개발 빌드에서 명확히 구분한다.

---

## 6. 참고 공식 소스

- Kakao Map / Local API: https://developers.kakao.com/docs/ko/kakaomap/common
- Kakao Local REST API: https://developers.kakao.com/docs/ko/kakaomap/rest-api
- 온누리상품권 전국 가맹점 현황: https://www.data.go.kr/data/3060079/fileData.do
- 한국조폐공사 통합 가맹점기본정보: https://www.data.go.kr/data/15119539/openapi.do
- 지역사랑상품권 지자체별 판매정책정보: https://www.data.go.kr/data/15125217/openapi.do

외부 정책/API는 개발 착수 시 다시 확인하고 변경 가능성을 전제로 구현한다.
