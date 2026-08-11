# deploy — LocalPay Backend 배포 (Hostinger VPS 전용)

> 이 폴더는 **VPS 에서만 실행**한다. 회사 Mac 에서 docker compose up 하지 않는다.
> VPS 의 기존 **BG Company 서비스와는 완전히 격리**된 별도 스택.

## 격리 요약

| 구분 | 값 |
|---|---|
| 컨테이너 이름 | `localpay-api`, `localpay-db` |
| Docker 네트워크 | `localpay_net` (전용) |
| Docker 볼륨 | `localpay_pg_data` (전용) |
| 외부 노출 포트 | `127.0.0.1:18080` → API (localhost 만) |
| Postgres 외부 노출 | **없음** (호스트로 매핑 안 함) |

BG Company 스택의 어떤 리소스 이름도 재사용하지 않으므로 서로 영향이 없다.

## 최초 배포 (VPS)

```bash
# 1) 저장소 clone (최초 1회)
sudo mkdir -p /opt
cd /opt
git clone https://github.com/SongByungGyu/LocalPay.git localpay
cd localpay

# 2) 배포 환경변수 세팅 (최초 1회)
cd deploy
cp .env.example .env
# POSTGRES_PASSWORD 를 강한 랜덤값으로 바꾸고,
# 같은 값을 DATABASE_URL 안에도 반영한다.
vi .env

# 3) 빌드 + 기동
docker compose up -d --build

# 4) 로그 확인 (Ctrl+C 로 로그만 빠져나옴, 컨테이너는 유지)
docker compose logs -f api
```

기동 후 30초 이내에 다음이 순차 발생:
1. `localpay-db` healthy
2. `localpay-api` 시작 → `entrypoint.sh` 가 `alembic upgrade head`
3. `SEED_ON_START=true` 인 경우 `python -m app.seed.run_seed` 로 25개 매장 삽입
4. `uvicorn` 이 `0.0.0.0:8000` 리슨 → 호스트의 `127.0.0.1:18080` 에서 접근 가능

## 헬스 체크 (VPS 셸에서)

```bash
curl -sS http://127.0.0.1:18080/health
# {"status":"ok","service":"localpay-backend","version":"0.1.0"}

curl -sS http://127.0.0.1:18080/db-health
# {"status":"ok","postgres":"ok","postgis":"3.4.x"}

curl -sS "http://127.0.0.1:18080/api/v1/merchants?limit=3" | head -c 400
```

## 이후 배포 (git pull → 재빌드)

```bash
cd /opt/localpay
git status                    # 로컬 변경 없음 확인
git pull

cd deploy
docker compose up -d --build  # 이미지 재빌드 + 무중단에 가깝게 재기동
docker compose logs -f api    # 정상 기동 확인 후 Ctrl+C
```

이 과정에서 `localpay_pg_data` 볼륨은 유지되므로 DB 데이터가 보존된다.

## 상태 확인 · 로그

```bash
docker compose ps
docker compose logs -f db
docker compose logs -f api

# 컨테이너 내부 셸
docker compose exec api bash
docker compose exec db psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

## 수동 마이그레이션 / 시드

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seed.run_seed
```

## 절대 실행하지 말 것

```bash
docker compose down -v           # localpay_pg_data 삭제 → 데이터 파괴
docker volume rm localpay_pg_data
docker system prune -a --volumes
docker volume prune
```

BG Company 스택의 컨테이너/네트워크/볼륨 이름을 참조하는 어떤 조작도 하지 않는다.

## 재기동만 필요한 경우

```bash
docker compose restart api           # API 만
docker compose restart               # 전체 (DB 포함)
```

`restart` 는 볼륨과 이미지를 건드리지 않는다.

## 외부 노출 (선택)

현재 API 는 `127.0.0.1:18080` 에만 바인딩되어 외부에서 접근할 수 없다.
외부 도메인으로 노출하려면 별도의 리버스 프록시(Nginx/Traefik) 에서 `http://127.0.0.1:18080` 을 upstream 으로 두는 것을 권장한다 (BG Company Traefik 을 재구성하지 않고 별도 config 로).

Phase 10 검증 단계에서는 SSH 터널만으로 충분:

```bash
# Mac 에서
ssh -L 18080:127.0.0.1:18080 <vps-user>@<vps-host>
# 이후 Mac 브라우저에서 http://127.0.0.1:18080/health
```
