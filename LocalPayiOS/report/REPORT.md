# LocalPay iOS Dummy MVP — 완료 보고

- 보고일: 2026-08-11
- 프로젝트 경로: `LocalPayiOS/`
- 상태: **Phase 1 → 9 전체 완료. Simulator 빌드 성공, 경고 0건.**

## 한 줄 요약

**"내가 가진 온누리상품권 · 지역화폐로 무엇을 어디에서 살 수 있는가"** 를 지도 · 검색 · 즐겨찾기 · MY 흐름으로 해결하는 iOS 앱의 UI/UX + 아키텍처를 실서버 없이 완성했습니다. 향후 Kakao Map · 실 Backend · 개인 잔액 API 교체가 도메인 모델 변경 없이 가능하도록 구조를 잡았습니다.

## 완성 지표

| 항목 | 값 |
|---|---|
| 빌드 결과 | `xcodebuild ... clean build` → **BUILD SUCCEEDED** |
| Swift 경고 | 0 건 (AppIntents 메타데이터 관련 시스템 노트 1건 제외) |
| Swift 파일 수 | 50 |
| Swift 총 라인 수 | 3,715 |
| Dummy 매장 seed | 25 (안양시청 반경 3km, 카테고리·결제조합 골고루) |
| 지원 iOS | 17.0+ |
| 외부 라이브러리 | 없음 (Apple 프레임워크만) |
| 문서 | `README.md`, `TODO.md`, `API_INTEGRATION.md`, `CLAUDE.md` + 본 리포트 4종 |

## 검증된 사용자 흐름 (CLAUDE.md §43 준수)

1. 앱 실행 → 지도 홈 (안양 fallback 좌표)
2. 온누리 필터 → 마커 색·개수 즉시 변경
3. "음식점" 카테고리 → 지도 필터링
4. 마커 탭 → 하단 Preview Card 등장
5. "상세보기" → Merchant Detail
6. 판매 상품 · 사용 가능 결제 · 최근 결제 확인 · 후기 확인
7. 하트로 즐겨찾기 등록
8. 즐겨찾기 Tab → 목록 반영 (앱 재실행 후에도 유지)
9. 검색 Tab → "삼겹살"/"약국" 등, 거리·평점·후기순 정렬
10. MY Tab → 프로필, DEMO 잔액, 안양사랑페이 혜택 카드

## 하위 문서

| 문서 | 내용 |
|---|---|
| [01_구현_현황.md](01_구현_현황.md) | Phase 1~9 각 단계 완성 내용과 화면별 기능 |
| [02_아키텍처_및_교체지점.md](02_아키텍처_및_교체지점.md) | 계층 구조, Kakao Map · Backend · Wallet 교체 지점 |
| [03_실행_및_다음단계.md](03_실행_및_다음단계.md) | 빌드/실행 방법 + 우선순위별 다음 개발 항목 |
| [04_Backend_Phase10.md](04_Backend_Phase10.md) | FastAPI + PostGIS 1차 서버 구축 |
| [05_Backend_Connect_Phase11.md](05_Backend_Connect_Phase11.md) | iOS ↔ VPS Backend 실 연결 (RemoteMerchantRepository, Date fractional decode) |
| [06_Backend_Connect_Diagnostic.md](06_Backend_Connect_Diagnostic.md) | 시뮬레이터 0건 이슈 진단·복구 (iOS 26 Simulator loopback sandbox, localhost URL, DEBUG 로그) |

## 주요 결정 사항 (요약)

- **지도 SDK 종속 최소화**: 좌표는 원시 `Double`로 보관, `MapKit` 은 `MapHomeView` 안에만 존재. 향후 Kakao Map 전환 시 ViewModel · Repository · Models **변경 없음**.
- **Repository 추상화**: `MerchantRepository` protocol 만 인터페이스로 노출. 실 서버 연결은 `RemoteMerchantRepository` 만 신규 작성 → 스왑.
- **DEMO 상시 노출**: 잔액 · 지역화폐 혜택 · 최근 결제 등 임의 데이터가 실제로 오인되지 않도록 "DEMO" 뱃지를 화면 곳곳에 배치 (CLAUDE.md §12, §42 준수).
- **개인 금융/실제 결제 정보 미저장**: 회원가입/실 잔액/실 결제 없음. UserDefaults 는 즐겨찾기 · 사용자 리뷰만.
- **접근성**: 색상 외에도 SF Symbol 형태 차이로 결제수단 구분 (색약 대응), VoiceOver Label, 44pt 이상 Touch Target.

## 리스크 · 한계

- **실 데이터 미연결**: 이번 단계에서는 의도된 범위 밖. `API_INTEGRATION.md` 에 정확한 연결 지점 명시.
- **위치 권한 거부 시 안양 fallback 만 사용**: 도시별 fallback 은 향후 서버 지역 목록 연동 시 개선.
- **매장 대표 이미지 자산 없음**: 카테고리 아이콘 + 결제색 그라디언트로 대체. 실 이미지 파이프라인은 서버 도입 시 준비.
- **Unit/UI Test 미작성**: `Utilities/*` · `SortOption` · `DummyMerchantRepository` 부터 우선 도입 예정.

## 다음 마일스톤 후보

1. `RemoteMerchantRepository` 구현 및 공공데이터 스냅샷 서버 연동
2. Kakao Map SDK PoC (`KakaoMapView`)
3. 개인 잔액 API 확정 시 `WalletService` 도입
4. Unit Test + CI 파이프라인
