# HTTPS_DEPLOYMENT — LocalPay API 운영 배포 (Phase 12)

> 목표: SSH 터널 없이 실기기·시뮬레이터·모든 네트워크에서 접근 가능한 HTTPS 엔드포인트로 LocalPay Backend 를 공개한다.
> 원칙: 동일 VPS 의 **기존 BG Company · Hermes 서비스는 어떤 것도 건드리지 않는다.**

---

## 아키텍처

```
iPhone (Wi-Fi/LTE) ─┐
Simulator ──────────┤
Web (사내 검증)     │
                    ↓ HTTPS 443
        https://localpay.bgcompanyoffice.cloud
                    ↓
        Traefik v3 (host mode, Docker provider,
                    Let's Encrypt HTTP-01 resolver)
                    │
                    ↓ container IP :8000
              localpay-api (FastAPI)
                    │
                    ↓ localpay_net 내부
              localpay-db (PostgreSQL 16 + PostGIS 3.4)
```

- 외부 서비스 진입점은 **Traefik 443 하나뿐**
- FastAPI 8000 · PostgreSQL 5432 은 외부에 직접 노출되지 않음
- Traefik 자체 설정 파일은 **수정하지 않음** — LocalPay compose 의 라벨만으로 라우팅

## 도메인

| 항목 | 값 |
|---|---|
| 서비스 URL | `https://localpay.bgcompanyoffice.cloud` |
| DNS Type / Name / Value | `A` / `localpay` / `72.60.108.42` (Hostinger hPanel) |
| 인증서 | Let's Encrypt (issuer `YR1`), 90일, 자동 갱신 |
| 저장소 | Docker volume `traefik_traefik-letsencrypt` |

## Traefik 재사용 방식 (기존 인프라 무변경)

VPS Traefik 이 이미 다음 조건이라 새 파일 추가 없이 라벨만으로 라우팅 가능하다.

- `network_mode: host` — 호스트 80/443 직접 사용
- `--providers.docker=true --providers.docker.exposedbydefault=false` — 라벨 기반 자동 등록
- `--certificatesresolvers.letsencrypt.acme.httpchallenge=true` — LocalPay 신규 도메인도 같은 resolver 로 자동 발급
- `--entrypoints.web.http.redirections.entrypoint.to=websecure` — HTTP→HTTPS 전역 redirect (LocalPay 도 자동 적용)

**LocalPay compose 서비스 `api` 에 붙는 라벨:**

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.localpay-api.entrypoints=websecure"
  - "traefik.http.routers.localpay-api.rule=Host(`localpay.bgcompanyoffice.cloud`)"
  - "traefik.http.routers.localpay-api.tls=true"
  - "traefik.http.routers.localpay-api.tls.certresolver=letsencrypt"
  - "traefik.http.services.localpay-api.loadbalancer.server.port=8000"
```

라우터 이름 `localpay-api` 는 기존 라우터와 겹치지 않는다.

## 최초 발급 절차 (요약)

1. Hostinger hPanel → `bgcompanyoffice.cloud` → DNS Zone → A 레코드 추가 (`localpay` → `72.60.108.42`, TTL 14400)
2. `dig +short localpay.bgcompanyoffice.cloud` 로 반영 확인 (수분 이내)
3. `deploy/docker-compose.yml` 에 위 라벨 6줄 추가
4. VPS: `cd /opt/localpay/deploy && cp docker-compose.yml docker-compose.yml.bak.pre-traefik.$(date -u +%Y%m%d-%H%M%S)`
5. 로컬에서 수정한 파일 VPS 로 복사 (`scp` 또는 `git pull`)
6. `docker compose up -d api` (db 는 재기동 안 됨, 볼륨 무손실)
7. Traefik 이 라벨 감지 → Let's Encrypt HTTP-01 challenge → 인증서 발급 (~10-30초)
8. `curl -sS https://localpay.bgcompanyoffice.cloud/health` 로 200 확인

## 검증 명령

```bash
# HTTPS 200
curl -sS https://localpay.bgcompanyoffice.cloud/health

# Merchant 25개
curl -sS "https://localpay.bgcompanyoffice.cloud/api/v1/merchants?limit=100" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"

# 인증서 issuer / 유효 기간
echo | openssl s_client -connect localpay.bgcompanyoffice.cloud:443 \
  -servername localpay.bgcompanyoffice.cloud 2>/dev/null \
  | openssl x509 -noout -issuer -subject -dates

# HTTP → HTTPS 자동 redirect (Traefik 전역 정책)
curl -sI http://localpay.bgcompanyoffice.cloud/health   # HTTP/1.1 308

# 회귀 (기존 서비스)
curl -sI https://bgcompanyoffice.cloud/            # HTTP/2 307
curl -sI https://www.bgcompanyoffice.cloud/         # HTTP/2 307
```

## 보안 체크리스트

| 항목 | 상태 |
|---|---|
| PostgreSQL 5432 외부 노출 | ❌ (localpay-db 는 컨테이너 네트워크 내부, bg-company-postgres 는 127.0.0.1 만) |
| FastAPI 8000 직접 외부 노출 | ❌ (컨테이너 내부만, 호스트 미노출) |
| 127.0.0.1:18080 → 8000 매핑 | 유지 (개발/로컬 curl 용, 외부 접근 불가) |
| 외부 진입점 | Traefik 443 뿐 |
| `.env` git ignored | ✅ (`deploy/.env` 는 `.gitignore` 관리) |
| DB 비밀번호 · API secret git | ✅ 미포함 |
| 인증서 private key | ✅ Traefik volume 에만, git 미포함 |

## 트러블슈팅

### 1) `curl https://...` 가 timeout / SSL 에러
- DNS 반영 확인: `dig +short localpay.bgcompanyoffice.cloud` → `72.60.108.42` 여야 함
- Traefik 로그 확인: `docker logs --tail 100 traefik-traefik-1 | grep -iE 'localpay|acme|error'`
- 만약 acme rate limit 걸린 경우: 1주일 대기 또는 도메인/서브도메인 변경. 방지 위해 DNS 반영 확인 전엔 발급 시도 금지

### 2) HTTPS 는 200 인데 body 가 이상함
- localpay-api 컨테이너 로그: `docker logs --tail 100 localpay-api`
- DB 연결 확인: `curl https://localpay.bgcompanyoffice.cloud/db-health`

### 3) 기존 BG Company 라우팅이 이상함
- **즉시 롤백**: 아래 롤백 절차 실행
- 원인 분석 (Traefik 로그): `docker logs --tail 200 traefik-traefik-1 | grep -iE 'error|conflict'`

### 4) 인증서 자동 갱신 실패
- Traefik 은 만료 30일 전부터 자동 갱신 시도
- 실패 로그: `docker logs traefik-traefik-1 | grep -iE 'acme|renew'`
- 수동 갱신은 acme.json 을 삭제 후 재시작 (매우 신중히, 다른 인증서까지 재발급됨)

## 롤백 (LocalPay 만 원상복구, BG Company 무영향)

```bash
# 1) VPS 에서 compose 라벨 제거
cd /opt/localpay
git log --oneline deploy/docker-compose.yml    # Traefik 라벨 커밋 확인
git revert <hash>                              # 또는 백업 파일로 복원
cd deploy && docker compose up -d api

# 2) Traefik 이 즉시 localpay-api 라우터 삭제 → https://localpay.bgcompanyoffice.cloud 는 404

# 3) DNS 도 원하면 삭제 (Hostinger hPanel 에서 localpay A 레코드 삭제)

# 4) 검증: 기존 서비스 정상
curl -sI https://bgcompanyoffice.cloud/    # 여전히 307
docker ps                                   # 모든 컨테이너 healthy
```

## iOS AppConfiguration

Phase 12 부터 DEBUG · Release 모두 `https://localpay.bgcompanyoffice.cloud` 사용.
`Info.plist` 의 `NSAllowsLocalNetworking` 은 제거 (HTTP loopback 불필요).

별도 개발 백엔드가 필요해지면 `AppConfiguration.swift` 에 `#if DEBUG` 분기 재도입.

## TODO / 향후

- **`/db-health` 노출 범위**: 현재 인증 없이 외부 접근 가능. 정보 노출은 minimal (`{"status":"ok","postgres":"ok","postgis":"3.4.x"}`) 이지만 Phase 12+ 에서 내부/관리용으로 제한할지 검토.
- **인증서 만료 알림**: Let's Encrypt 자동 갱신되지만, 실패 시 통지 채널 (Slack/이메일) 도입 후보.
- **레이트 리미팅 · WAF**: Phase 13+ 실 공공데이터 도입 시 Traefik middleware (`ratelimit`, IP allowlist 등) 검토.
- **Bearer 토큰 인증**: `docs/API_SCHEMA.md` 에 언급된 Phase 12+ 항목. HTTPS 완료 후 다음 단계로 진행.
- **모니터링**: Traefik metrics + Prometheus/Grafana 파이프라인. 지금은 `docker logs` 수동 확인.

## 관련 문서

- `deploy/README.md` — 배포 · 재기동 · 절대 금지 명령
- `docs/API_SCHEMA.md` — API 스키마
- `LocalPayiOS/API_INTEGRATION.md` — iOS 연동 정보
- `LocalPayiOS/report/07_HTTPS_Phase12.md` — Phase 12 실행 보고
