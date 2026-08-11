# 05. 요구명세서 (SRS)

## 1. 범위

Android MVP의 기능/비기능 요구사항을 정의한다.

우선순위:

- **P0**: MVP 필수
- **P1**: MVP 권장
- **P2**: 이후 단계

---

## 2. 기능 요구사항

### MAP — 지도

| ID | Priority | 요구사항 | 수용 기준 |
|---|---:|---|---|
| FR-MAP-001 | P0 | 앱은 지도 홈을 기본 진입 화면으로 제공해야 한다. | 앱 실행 후 지도 화면 표시 |
| FR-MAP-002 | P0 | 위치 권한 허용 시 현재 위치를 표시해야 한다. | 사용자 위치 indicator 표시 |
| FR-MAP-003 | P0 | 위치 권한 거절 시 앱이 사용 가능해야 한다. | 기본/마지막 위치로 지도 표시 |
| FR-MAP-004 | P0 | 지도 영역 내 가맹점을 marker로 표시해야 한다. | dummy repository 기준 marker 표시 |
| FR-MAP-005 | P0 | 온누리/지역화폐/둘 다 상태를 marker에서 구분해야 한다. | 색 외 텍스트/아이콘 보조 |
| FR-MAP-006 | P0 | marker 선택 시 가맹점 미리보기 카드가 나타나야 한다. | 선택 merchant 정보 일치 |
| FR-MAP-007 | P0 | 필터 변경 시 marker가 즉시 갱신되어야 한다. | 조건 외 marker 제거 |
| FR-MAP-008 | P1 | 다수 marker는 cluster 처리해야 한다. | 지도 축소 시 cluster 표시 |
| FR-MAP-009 | P0 | 지도 이동 후 현재 영역 재검색 기능을 제공해야 한다. | 버튼 탭 후 bounds 재조회 |

### FILTER — 필터

| ID | Priority | 요구사항 |
|---|---:|---|
| FR-FLT-001 | P0 | 전체/온누리/지역화폐/둘 다 결제필터 제공 |
| FR-FLT-002 | P0 | 카테고리 필터 제공 |
| FR-FLT-003 | P0 | 결제필터와 카테고리 필터를 조합 가능 |
| FR-FLT-004 | P1 | 필터 상태는 지도→상세→뒤로가기 후 유지 |
| FR-FLT-005 | P1 | 필터 초기화 제공 |

### SEARCH — 검색

| ID | Priority | 요구사항 |
|---|---:|---|
| FR-SRH-001 | P0 | 가맹점명 검색 |
| FR-SRH-002 | P0 | 취급상품 검색 |
| FR-SRH-003 | P0 | 카테고리 검색 |
| FR-SRH-004 | P1 | 최근 검색어 저장 |
| FR-SRH-005 | P1 | 가까운 순/최근 확인 순 정렬 |
| FR-SRH-006 | P1 | 검색 결과와 결제수단 필터 조합 |

### MERCHANT — 상세

| ID | Priority | 요구사항 |
|---|---:|---|
| FR-MER-001 | P0 | 매장명/카테고리/주소 표시 |
| FR-MER-002 | P0 | 지원 결제수단 표시 |
| FR-MER-003 | P0 | 정보 없음과 불가 상태를 구분 |
| FR-MER-004 | P0 | 취급상품 표시 |
| FR-MER-005 | P0 | 데이터 갱신/최근 확인 정보 표시 |
| FR-MER-006 | P0 | 후기 미리보기 표시 |
| FR-MER-007 | P1 | 전화 CTA |
| FR-MER-008 | P1 | 길찾기 CTA |

### REVIEW — 후기

| ID | Priority | 요구사항 |
|---|---:|---|
| FR-REV-001 | P0 | 후기 목록 제공 |
| FR-REV-002 | P0 | 별점 표시 |
| FR-REV-003 | P0 | 결제 성공/실패/미사용 상태 표현 |
| FR-REV-004 | P0 | 사용 결제수단 표시 |
| FR-REV-005 | P1 | MVP 더미/로컬 후기 작성 |
| FR-REV-006 | P2 | 사진 후기 |
| FR-REV-007 | P2 | 신고/차단 |

### FAVORITE — 즐겨찾기

| ID | Priority | 요구사항 |
|---|---:|---|
| FR-FAV-001 | P0 | 가맹점 즐겨찾기 추가/삭제 |
| FR-FAV-002 | P0 | 앱 재실행 후 유지 |
| FR-FAV-003 | P0 | 즐겨찾기 목록 표시 |

### MY / WALLET

| ID | Priority | 요구사항 |
|---|---:|---|
| FR-MY-001 | P0 | MY 화면 제공 |
| FR-MY-002 | P0 | 내 상품권 영역 제공 |
| FR-MY-003 | P0 | 실제 연동 전에는 잔액 Placeholder 또는 명시적 Dummy만 표시 |
| FR-MY-004 | P1 | 기본 지역 설정 |
| FR-WAL-001 | P2 | 제휴 API 확보 후 개인 잔액 조회 Provider 연동 |
| FR-WAL-002 | P2 | 여러 지역화폐 Provider 통합 표시 |

### POLICY

| ID | Priority | 요구사항 |
|---|---:|---|
| FR-POL-001 | P1 | 지역별 상품권 할인/구매한도 표시 구조 제공 |
| FR-POL-002 | P1 | 정책 시작/종료일 표시 가능 |

---

## 3. 데이터 요구사항

| ID | 요구사항 |
|---|---|
| DR-001 | Merchant는 위도/경도를 가져야 한다. |
| DR-002 | Merchant의 결제수단은 source와 updatedAt을 함께 가진다. |
| DR-003 | `UNKNOWN`과 `NOT_SUPPORTED`를 구분한다. |
| DR-004 | 공공데이터 원본 식별자를 가능한 한 유지한다. |
| DR-005 | 중복 가맹점 병합 시 원본 source records를 보존한다. |
| DR-006 | 사용자 후기와 공식/공공 데이터를 별도 필드로 관리한다. |
| DR-007 | 가맹점의 상품/품목은 검색 가능한 text/token 구조로 관리한다. |

---

## 4. 비기능 요구사항

### Performance

| ID | Priority | 요구사항 |
|---|---:|---|
| NFR-PERF-001 | P0 | 필터는 로컬 더미 기준 200ms 내 반응 체감 |
| NFR-PERF-002 | P0 | 지도는 전국 전체 가맹점을 한 번에 로딩하지 않음 |
| NFR-PERF-003 | P0 | bounds/zoom 기반 조회 구조 사용 |
| NFR-PERF-004 | P1 | 지도 이동 연속 이벤트는 debounce/throttle 적용 |
| NFR-PERF-005 | P1 | API 응답 캐시/Room 캐시 고려 |

### Security

| ID | Priority | 요구사항 |
|---|---:|---|
| NFR-SEC-001 | P0 | API Key를 Git에 커밋하지 않음 |
| NFR-SEC-002 | P0 | 개인 잔액 비공개 API 우회 사용 금지 |
| NFR-SEC-003 | P0 | 민감정보 불필요 수집 금지 |
| NFR-SEC-004 | P1 | 서버 API HTTPS만 사용 |

### Privacy

| ID | Priority | 요구사항 |
|---|---:|---|
| NFR-PRI-001 | P0 | 위치 권한은 기능 설명 후 요청 |
| NFR-PRI-002 | P0 | 위치 거절 시 핵심 기능 사용 가능 |
| NFR-PRI-003 | P1 | 정확한 위치를 서버에 영구 저장하지 않는 것을 기본 정책으로 함 |

### Reliability

| ID | Priority | 요구사항 |
|---|---:|---|
| NFR-REL-001 | P0 | API 실패 시 Crash 금지 |
| NFR-REL-002 | P0 | Empty/Error/Offline state 제공 |
| NFR-REL-003 | P1 | 오래된 캐시라도 출처/갱신일과 함께 fallback 가능 |

### Accessibility

| ID | Priority | 요구사항 |
|---|---:|---|
| NFR-ACC-001 | P0 | 최소 터치 영역 48dp |
| NFR-ACC-002 | P0 | 컬러만으로 결제 타입 구분 금지 |
| NFR-ACC-003 | P1 | TalkBack contentDescription 제공 |
| NFR-ACC-004 | P1 | 시스템 폰트 배율 대응 |

---

## 5. 외부 데이터/API 요구사항

### 온누리

- 전국 온누리상품권 가맹점 현황을 데이터 소스 후보로 사용한다.
- 가맹점명, 시장명, 주소, 취급품목, 상품권 형태 취급 여부 등을 정규화한다.
- 파일 갱신 주기를 전제로 Batch Import 구조를 갖는다.

### 지역화폐

- 한국조폐공사 통합 가맹점기본정보 API를 데이터 소스 후보로 사용한다.
- 가맹점명, 전화, 주소, 위경도, 상태, 산업분류 등을 정규화한다.

### Kakao

- Kakao Map Android SDK: 지도 렌더링
- Kakao Local REST API: 장소 검색/좌표/카테고리 보강
- Kakao 데이터는 가맹점의 상품권 지원 여부를 결정하는 최종 source로 사용하지 않는다.

---

## 6. 완료 정의 (Definition of Done)

P0 요구사항이 모두 충족되고 다음이 성공해야 한다.

- Debug build 성공
- 핵심 ViewModel unit test 또는 repository test 존재
- 위치 권한 허용/거절 양쪽 확인
- Empty/Error UI 확인
- 더미 데이터로 전체 사용자 흐름 동작
- Secret/Key가 repository에 없음
- README에 실행 방법 존재
