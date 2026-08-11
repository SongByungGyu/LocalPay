# 06. Backend Connect — 시뮬레이터 0건 이슈 진단·복구

- 보고일: 2026-08-11
- 이전 단계: Phase 11 (`da45029 feat(ios): iOS ↔ FastAPI backend 실 연결`)
- 마감 커밋: `68b81d6 fix(ios): backend 연결 진단·복구 (localhost URL + DEBUG 로그 + 서명 허용)`
- 상태: **iOS 18 Simulator 에서 서버 25개 마커 정상 표시. 원인 특정 완료. 후속 옵션 문서화.**

## 한 줄 요약

Phase 11 코드 자체는 이상 없었고, **Xcode 26 / iOS 26.4 Simulator 가 host Mac 의 loopback (`lo0`) 접근을 sandbox 로 차단** 하는 신규 이슈가 원인이었다. iOS 18 Simulator 로 device 를 바꾸면 즉시 25개 마커가 뜬다. 재발 방지·후속 진단을 위해 baseURL 을 `localhost` (Happy Eyeballs 로 IPv4/IPv6 자동 폴백) 로 바꾸고, HTTPClient · Factory · ViewModel 에 `#if DEBUG` 콘솔 로그를 추가했다.

## 증상

- Simulator 실행 시 지도에 마커 0개
- "현재 필터에 맞는 가맹점이 없어요" chip 만 표시
- host Mac 에서 `curl http://127.0.0.1:18080/api/v1/merchants?limit=100` 은 25건 정상 반환
- SSH 터널 (`ssh -N -L 18080:127.0.0.1:18080 localpay-vps`) 은 살아있음

## 진단 과정

### 1) DEBUG 로그 3곳 심기

MapHomeViewModel 의 catch 는 원래 조용히 `visibleMerchants = []` 하고 사용자 문구만 세팅해서 원인이 안 보였다. `#if DEBUG` 로 다음을 추가.

- `RepositoryFactory` — 어떤 Repository 가 주입되었고 baseURL 이 무엇인지
- `HTTPClient` — 실제 GET URL, HTTP status, 응답 bytes, decoded item count, 실패 시 원인 (transport · decoding)
- `MapHomeViewModel.reload` — 성공 시 count / filter 값, 실패 시 underlying error

### 2) 회사 Mac (iOS 18 Simulator) 재검증

로그가 명확했다.
```
[RepositoryFactory] → RemoteMerchantRepository baseURL=http://127.0.0.1:18080
[HTTPClient] GET http://127.0.0.1:18080/api/v1/merchants?payment=all&limit=1000
[HTTPClient] ← HTTP 200 bytes=28825
[HTTPClient] ✓ decoded 25 items
[MapHomeViewModel] reload ok count=25 category=all payment=all
```
→ **코드는 정상**. 원인은 사용자 환경.

### 3) 사용자 Mac (iOS 26 Simulator) 로그
```
[HTTPClient] GET http://127.0.0.1:18080/api/v1/merchants?payment=all&limit=1000
Socket SO_ERROR [61: Connection refused]
[C1.1.1 ::1.18080 ... interface: lo0] failing
[C1.1.2 127.0.0.1:18080 ... interface: lo0] failing
[HTTPClient] ✗ transport error: Code=-1004 "서버에 연결할 수 없습니다."
```
`errno 61 = ECONNREFUSED`. 하지만 사용자 Mac 의 `lsof -iTCP:18080 -sTCP:LISTEN`:
```
ssh 50179 byunggyusong  IPv6 ... TCP [::1]:18080     (LISTEN)
ssh 50179 byunggyusong  IPv4 ... TCP 127.0.0.1:18080 (LISTEN)
```
- SSH 터널이 **IPv4 · IPv6 둘 다** listen 중
- `curl -4`, `curl -6` 둘 다 200 성공
- 그럼에도 시뮬레이터에서만 refused

### 4) `localhost` 로 변경 후에도 실패

시뮬레이터 로그가 IPv6 → IPv4 를 **둘 다 시도하고 둘 다 refused**. Happy Eyeballs 는 정상 작동 중. 즉 IPv4/IPv6 문제가 아님.

### 5) 원인 특정

→ **Xcode 26 iOS 26.4 Simulator 는 host Mac 의 loopback 접근을 sandbox 로 차단**. iOS 18 시뮬레이터는 host `lo0` 을 그대로 공유하지만 iOS 26 시뮬레이터에서는 해당 경로가 격리되어 있음. curl (host 프로세스) 은 성공하지만 시뮬레이터 프로세스는 실패하는 이유.

## 즉시 해결책

**iOS 18 Simulator 로 device 변경 → ⌘R** → 마커 25개 정상 표시.

Xcode 상단 device picker 에서 iOS 뒤 숫자가 `18.x` 인 device (예: `iPhone 15 (18.0)`) 선택.

## 반영된 방어 코드 (커밋 `68b81d6`)

| 파일 | 변경 |
|---|---|
| `LocalPay/Data/Network/AppConfiguration.swift` | DEBUG baseURL `http://127.0.0.1:18080` → `http://localhost:18080`. IPv4-only bind 나 IPv6-only bind 인 환경에서도 Happy Eyeballs 로 성공한 쪽을 자동 선택 |
| `LocalPay/Data/RepositoryFactory.swift` | XCTest 판단을 `NSClassFromString("XCTestCase")` → `ProcessInfo.environment["XCTestConfigurationFilePath"]`. Xcode 15+ 시뮬레이터의 XCTest auto-inject 오판단 예방. DEBUG 로그 추가 |
| `LocalPay/Data/Network/HTTPClient.swift` | GET URL, HTTP status, response bytes, decode 결과/실패 원인을 `#if DEBUG print` |
| `LocalPay/Features/Map/MapHomeViewModel.swift` | `reload()` 성공/실패 지점에 `#if DEBUG print`. 조용한 실패 방지 |
| `LocalPayiOS/project.yml` | `CODE_SIGNING_ALLOWED: NO` 제거. 실기기 빌드 가능하도록 |

Release build 에는 로그 미포함 (`#if DEBUG` 로 스코프).

## 검증

| 항목 | 결과 |
|---|---|
| iOS 18 Simulator, DEBUG build, SSH 터널 활성 | 마커 25개 표시 (스크린샷 확인) |
| Xcode Console 로그 | `[HTTPClient] ← HTTP 200 bytes=28825` / `reload ok count=25` |
| Payment badge 색상 (온누리·지역화폐·둘다) | 정상 |
| DEMO 배지 오버레이 | 정상 |

## 후속 옵션 (해야 할 때 참조)

### A) iOS 26 Simulator 를 계속 쓰고 싶은 경우

Simulator 가 host loopback 을 못 붙으므로 **host Mac 의 en0 IP 사용** 필요:
1. SSH 터널을 wildcard bind 로 재실행
   ```bash
   pkill -f "ssh -N -L 18080"
   ssh -N -L 0.0.0.0:18080:127.0.0.1:18080 localpay-vps
   ```
2. `AppConfiguration` 의 DEBUG baseURL 을 `http://<Mac IP>:18080` (예: `http://192.168.0.42:18080`) 으로 변경
3. `Info.plist` 에 해당 IP 에 대한 ATS 예외 도메인 추가 (HTTP)
4. macOS 방화벽에서 SSH 프로세스 incoming 허용 (또는 방화벽 off)

### B) 실기기 iPhone 으로 개발

동일하게 host Mac 의 en0 IP 사용 + 같은 Wi-Fi 필요. 세팅 절차는 위 A) 와 동일.

### C) 코드 로 자동 감지 (도입 X, 참고용)

`#if targetEnvironment(simulator)` 로 시뮬레이터 · 실기기 분기하여 baseURL 을 다르게 세팅하는 방법도 있으나, 현재 Phase 는 개발 편의 목적이라 도입하지 않음. 실서비스 URL 이 확정되면 Release 조건으로 충분.

## 트러블슈팅 인덱스 (신규)

프로젝트에 아직 `docs/troubleshooting/` 인덱스가 없다. 이번 이슈는 대표적인 재발 가능성 있는 케이스라 향후 인덱스 도입 시 아래 항목으로 박제 후보.

- **증상**: iOS Simulator 에서 서버 데이터 0건
- **원인 후보**:
  1. SSH 터널 죽음 → `curl http://127.0.0.1:18080/health` 로 확인
  2. IPv6-only bind → `lsof -iTCP:18080 -sTCP:LISTEN` 확인, `localhost` URL 로 회피
  3. iOS 26+ Simulator loopback sandbox → iOS 18 Simulator 로 변경 또는 host IP 우회
  4. 실기기 vs Simulator 혼동 → 실기기는 host IP 필요
- **확인 로그**: `[HTTPClient] ✗ transport error: Code=-1004` + `Socket SO_ERROR [61: Connection refused]`
- **해결 파일**: `AppConfiguration.swift`, `HTTPClient.swift`, `RepositoryFactory.swift`

## 남은 이슈

- iOS 26 Simulator 에서 개발하려면 후속 옵션 A) 를 코드/설정으로 반영해야 함. **현재 Phase 에서는 iOS 18 Simulator 사용을 전제**.
- 향후 실서비스 URL 이 확정되면 Release baseURL 을 실제 도메인으로 교체 (`AppConfiguration.swift`).

## 다음 마일스톤 (변경 없음)

Phase 11 REPORT 에 정리된 다음 후보 그대로:
1. `/api/v1/merchants/map` (BBOX) 카메라 이동 시 자동 재조회
2. 서버 Search endpoint 도입 시 `search(query:)` 스왑
3. 실 공공데이터 sync + Bearer 인증 (Phase 12)
