# TODO — LocalPay iOS 다음 단계

> Dummy MVP 완료 후의 백로그. 우선순위 순.
> 세부 계약은 `API_INTEGRATION.md`, 요구사항 원본은 `CLAUDE.md`.

## Priority 1 — 실 데이터 연결 준비

- [ ] `RemoteMerchantRepository` 구현
  - `URLSession` + `async/await`
  - `Merchant` Codable 매핑 (이미 채택 완료 — 필드 이름만 맞추면 됨)
  - 서버 응답 스키마 확정 (`docs/contracts/merchant.schema.json` 생성)
- [ ] 환경별 base URL / API Key 관리
  - `Config.swift` + `Configuration` 별 Info.plist
  - **API Key 는 코드에 직접 삽입 금지** (CLAUDE.md §2)
- [ ] Bounding Box 기반 검색
  - `MerchantRepository.nearby(bbox:)` 확장
  - 서버는 PostGIS `ST_Intersects` 등 사용 예정
- [ ] 오프라인/네트워크 실패 대응 캐시 (URLCache 또는 간단한 in-memory TTL)

## Priority 2 — 지도 SDK 전환 검토

- [ ] Kakao Map iOS SDK PoC
  - `KakaoMapView: UIViewRepresentable` 신설
  - 카메라 · Annotation 이벤트 브릿지
  - Merchant / MapMarkerModel 은 그대로 사용
- [ ] `MapProvider` enum 추가 후 런타임/빌드 플래그로 스왑
- [ ] Cluster (뷰포트 내 200개+ 시 대응)

## Priority 3 — 개인 지갑 / 결제 인증

- [ ] `WalletService` 프로토콜 정의 (실 API 확정 후)
- [ ] `BalanceCard` 실 잔액 바인딩 (DEMO 스위치 유지, 명시적 fallback)
- [ ] 결제 성공 이벤트 수집 → `Merchant.recentPayments` 실시간 반영
- [ ] 후기 작성 시 결제 인증 실측 검증

## Priority 4 — 회원 · 사용자 데이터

- [ ] 회원가입/로그인 (Apple / Kakao 소셜 로그인)
- [ ] 서버 즐겨찾기 동기화 (현재는 UserDefaults)
- [ ] 사용자 리뷰 서버 저장
- [ ] 신고 · 차단 · 리뷰 검수

## Priority 5 — UI/UX 폴리시

- [ ] 지도 Bottom Sheet (드래그 · 확장 · 축소)
- [ ] 마커 클러스터링 애니메이션
- [ ] Skeleton Loading
- [ ] 앱 아이콘 · 스플래시 화면
- [ ] 매장 대표 이미지 자산 파이프라인
- [ ] 다크모드 스크린샷 QA
- [ ] Dynamic Type XXL 대응 QA
- [ ] Haptic feedback (마커 선택, 즐겨찾기 토글)

## Priority 6 — 접근성 / 국제화

- [ ] VoiceOver 시나리오 전수 검증
- [ ] Localizable.strings 분리 (현재 하드코딩된 한국어)
- [ ] 색약 대응 검증 (온누리·지역화폐·둘 다 색 구분)

## Priority 7 — 품질 · 인프라

- [ ] Unit Test — Repository, ViewModel, Utility (특히 GeoDistance / DateHelper / SortOption)
- [ ] UI Test — 앱 실행 → 지도 → Marker → 상세 흐름
- [ ] Snapshot Test — 주요 View
- [ ] CI (GitHub Actions) — xcodebuild test
- [ ] Crash reporting (Firebase Crashlytics 또는 Sentry)
- [ ] Analytics (privacy-first: 자체 서버 또는 익명 이벤트)

## 알려진 한계 / 정리 항목

- **위치 권한 거부 상태**: 안양 fallback 좌표로만 동작. 도시별 fallback 필요
- **거리 계산**: `MapRegion.anyangDefault.center` 기준 → 실제 지도 카메라 중심 반영으로 개선 필요
- **`extension String: @retroactive Identifiable`** in `MapHomeView.swift`: `navigationDestination(item:)` 편의용. 파일 스코프에 두었으나, 프로젝트 전역에 영향. 향후 `IdentifiableString` wrapper 로 대체 검토
- **`recentPayments` seed**: 실 서비스에서는 결제 이벤트 스트림으로 대체 예정
