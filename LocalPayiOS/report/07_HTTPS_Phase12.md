# 07. HTTPS Phase 12 — 실기기·시뮬레이터 SSH 터널 없이 접속

- 보고일: 2026-08-12
- 이전 커밋: `1d62179 docs(report): Phase 11 backend 연결 진단·복구 보고`
- 상태: **완료. iPhone 실기기 · Simulator 모두 SSH 터널 없이 HTTPS 로 25개 마커 로딩 확인.**

## 한 줄 요약

VPS 의 기존 Traefik (host mode + Docker provider + Let's Encrypt HTTP-01) 을 그대로 재사용해 **`deploy/docker-compose.yml` 의 라벨 6줄 추가만으로** LocalPay Backend 를 `https://localpay.bgcompanyoffice.cloud` 에 공개했다. Traefik 자체 파일 · BG Company / Hermes 스택은 **하나도 건드리지 않았다.**

## Traefik

- 기존 구성: v3.7.5, `network_mode: host`, Docker provider, `letsencrypt` resolver (HTTP-01), 전역 HTTP→HTTPS 308 redirect, 파일 `/docker/traefik/docker-compose.yml`
- LocalPay Router: `localpay-api` (`websecure` entrypoint, `tls.certresolver=letsencrypt`, `loadbalancer.server.port=8000`)
- 라우터 이름 · 도메인 · 인증서 모두 기존과 겹치지 않음

## DNS

- Domain: `localpay.bgcompanyoffice.cloud`
- Record: `A localpay 72.60.108.42` (Hostinger hPanel, TTL 14400)
- Resolution: 4개 resolver (local / 8.8.8.8 / 1.1.1.1 / VPS) 모두 `72.60.108.42` 확인. 반영 시간 수분

## Backend

- `/health` → `HTTP/2 200`, `{"status":"ok","service":"localpay-backend","version":"0.1.0"}`
- `/db-health` → 정상 (PostgreSQL/PostGIS ok)
- `/api/v1/merchants?limit=100` → 25건 정상 응답, decode 성공
- HTTP → HTTPS: `308 Permanent Redirect` (Traefik 전역 정책)

## TLS

- Issuer: `C=US, O=Let's Encrypt, CN=YR1`
- Subject CN: `localpay.bgcompanyoffice.cloud`
- Valid: `2026-08-12 03:56:10 UTC ~ 2026-11-10 03:56:09 UTC` (90일)
- 저장소: Docker volume `traefik_traefik-letsencrypt` (BG Company 인증서와 같은 볼륨, 서로 독립 항목)
- 자동 갱신 (Traefik 기본 정책)

## 보안 검증

| 항목 | 결과 |
|---|---|
| localpay-db 5432 외부 노출 | ❌ (컨테이너 네트워크 내부만) |
| bg-company-postgres 5432 외부 노출 | 127.0.0.1 만 (변경 없음) |
| FastAPI 8000 직접 외부 노출 | ❌ |
| 127.0.0.1:18080 → 8000 매핑 | 유지 (로컬 curl · 필요 시 SSH 터널용) |
| 외부 진입점 | Traefik 443 only |
| `.env` · secret · private key git 유출 | 없음 |

## 회귀 검증 (기존 서비스 무영향)

| 항목 | 결과 |
|---|---|
| `bg-company-web` | Up (healthy), 무재기동 |
| `bg-company-hermes-bridge` | Up (healthy) |
| `hermes-agent-8hkq-hermes-agent-1` | Up |
| `bg-company-postgres` | Up (healthy) |
| `traefik-traefik-1` | Up 6 weeks (무재기동) |
| `https://bgcompanyoffice.cloud/` | HTTP/2 307 정상 (변경 없음) |
| `https://www.bgcompanyoffice.cloud/` | HTTP/2 307 정상 |
| 발급된 다른 인증서 | 무변경 |

## iOS

- Base URL: `https://localpay.bgcompanyoffice.cloud` (DEBUG · Release 통합)
- `Info.plist` NSAllowsLocalNetworking 제거 (HTTP loopback 불필요)
- 127.0.0.1 / localhost 잔재 없음 (실 코드 · 주석 다 정리)
- **Simulator (iOS 18)**: SSH 터널 종료 상태에서 25개 정상 로딩
  ```
  [RepositoryFactory] → RemoteMerchantRepository baseURL=https://localpay.bgcompanyoffice.cloud
  [HTTPClient] GET https://localpay.bgcompanyoffice.cloud/api/v1/merchants?payment=all&limit=1000
  [HTTPClient] ← HTTP 200 bytes=28825
  [HTTPClient] ✓ decoded 25 items
  [MapHomeViewModel] reload ok count=25 category=all payment=all
  ```
- **실기기 iPhone**: 사용자 육안 검증, 마커 표시 정상. Wi-Fi 검증 완료
- SSH Tunnel required: **아니오** (Phase 12 목표 달성)

## 신규/변경 파일

| 종류 | 파일 |
|---|---|
| 신규 | `docs/HTTPS_DEPLOYMENT.md` — 아키텍처 · 최초 발급 · 검증 · 트러블슈팅 · 롤백 · TODO |
| 신규 | `LocalPayiOS/report/07_HTTPS_Phase12.md` (본 문서) |
| 변경 | `deploy/docker-compose.yml` — Traefik 라벨 6줄 + 주석 추가 |
| 변경 | `deploy/README.md` — 외부 노출 섹션을 Phase 12 HTTPS 구조로 갱신 |
| 변경 | `LocalPayiOS/LocalPay/Data/Network/AppConfiguration.swift` — HTTPS 도메인으로 통합 |
| 변경 | `LocalPayiOS/LocalPay/Resources/Info.plist` — NSAllowsLocalNetworking 제거 |
| 변경 | `LocalPayiOS/project.yml` — NSAllowsLocalNetworking 제거 |
| 변경 | `LocalPayiOS/report/REPORT.md` — 07 항목 링크 추가 |

## Rollback

`docs/HTTPS_DEPLOYMENT.md` § "롤백" 참조. 요약:
1. `git revert` 로 라벨 커밋 취소
2. `docker compose up -d api` — Traefik 이 즉시 라우터 제거
3. 필요 시 Hostinger 에서 DNS A 레코드 삭제
4. 기존 BG Company 라우팅 · 인증서에는 아무 영향 없음

## 남은 이슈 / TODO

1. **`/db-health` 노출 정책** — 외부에서 인증 없이 접근 가능. 정보 노출은 최소지만 Phase 13+ 에서 관리 전용으로 제한 후보
2. **인증서 만료 알림 채널** — 자동 갱신되지만 실패 시 Slack/이메일 통지 도입 후보
3. **레이트리미팅 · WAF** — Phase 13+ 실 공공데이터 도입 시 Traefik middleware 검토
4. **LTE/5G 검증** — 이번엔 Wi-Fi 만 확인. 실서비스 이전 셀룰러에서도 확인 필요
5. **Bearer 인증** — Phase 12+ (`docs/API_SCHEMA.md`) 후속

## 다음 마일스톤 (변경 없음)

Phase 11 후속 항목 그대로:
1. `/api/v1/merchants/map` (BBOX) 카메라 이동 시 자동 재조회
2. 서버 Search endpoint → `search(query:)` 스왑
3. 실 공공데이터 sync + Bearer 인증
