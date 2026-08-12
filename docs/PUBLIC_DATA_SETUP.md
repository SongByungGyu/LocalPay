# PUBLIC_DATA_SETUP — 공공데이터포털 활용신청 & Service Key 관리

> 이번 Phase 13 부터 LocalPay 는 공공데이터포털의 실 API 를 호출합니다.
> Service Key 는 절대 git 에 커밋하지 않으며, 오직 VPS `.env` 에서만 사용합니다.

## 필요한 활용신청 목록

| Gate | Dataset | 제공기관 | 용도 | 환경변수 |
|---|---|---|---|---|
| **2** (지역화폐) | `15119539` — 한국조폐공사_통합_가맹점기본정보 | 한국조폐공사 (KOMSCO) | 지역사랑상품권 통합 가맹점 fetch | `DATA_GO_KR_SERVICE_KEY` |
| 3 (온누리) | `3060079` — 소상공인시장진흥공단_전국 온누리상품권 가맹점 현황 | 소상공인시장진흥공단 | 온누리 CSV/XLSX snapshot 다운로드 | (파일 다운로드, key 미사용) |
| 추후 | Kakao Local REST | Kakao | 주소→좌표 보정 (필요 시) | `KAKAO_REST_API_KEY` |

## Gate 2 — 지역화폐 활용신청 절차

### 1) 공공데이터포털 로그인
[https://www.data.go.kr](https://www.data.go.kr) 로그인 (회원가입 필요).

### 2) Dataset 페이지 이동
[한국조폐공사_통합_가맹점기본정보 (15119539)](https://www.data.go.kr/data/15119539/openapi.do)

### 3) 활용신청 클릭
- 유형: **개발계정**
- 사용 목적: "지역화폐 사용처를 지도에서 안내하는 iOS 앱 개발"
- 상세 기능: "지역별 가맹점 목록 조회, 지도 표시"
- 트래픽: 기본 10,000 / 일

**대개 즉시 승인** (수 초 ~ 수 분). 승인되면 마이페이지 → 오픈API → 인증키 관리에서 **일반 인증키 (Decoding)** 값을 복사.

### 4) VPS `.env` 에 저장

```bash
ssh localpay-vps
cd /opt/localpay/deploy
sudo nano .env
```

다음 줄을 추가/수정:

```
DATA_GO_KR_SERVICE_KEY=<복사한 인증키 값 그대로>
```

`.env` 는 **절대 git 에 커밋되지 않도록** `.gitignore` 관리 중 (실제 확인: `git status` 에서 `.env` 표시 안 됨).

### 5) 정상 세팅 확인 (값 노출 없이)

```bash
ssh localpay-vps '
cd /opt/localpay/deploy
if grep -q "^DATA_GO_KR_SERVICE_KEY=..*" .env; then
  LEN=$(grep "^DATA_GO_KR_SERVICE_KEY=" .env | awk -F= "{print length(\$2)}")
  echo "CONFIGURED (len=$LEN)"
else
  echo "MISSING"
fi
'
```

### 6) 실 API 호출 테스트 (VPS 에서, worker 모듈)

```bash
# VPS 에서
cd /opt/localpay
python3 -m worker.cli local-currency \
  --region anyang \
  --limit 10 \
  --dry-run
```

정상이면 `[DryRun] region: anyang-manan (code=41171) requested=10 fetched=X …` 형태로 출력.
API 응답 스키마가 처음 확인되므로, parser 의 field alias 를 실제 응답 이름에 맞춰 축소 커밋한다.

## API 스펙 (2026-08 확인 기준)

| 항목 | 값 |
|---|---|
| Base URL | `http://apis.data.go.kr/B190001/localFranchisesV2` |
| Endpoint | `GET /franchiseV2` |
| Auth | query param `serviceKey` (소문자 s) |
| 응답 포맷 | JSON+XML, 우리는 `type=json` 사용 |
| Pagination | `pageNo`, `numOfRows` |
| 지역 필터 | 사용처지역코드 5자리 (시도 2 + 시군구 3), 또는 읍면동코드 8자리 |
| 개발계정 traffic | 10,000 / 일 |
| 운영계정 | 활용사례 등록 시 신청 → 트래픽 증량 가능 |
| 갱신 주기 | 공공데이터포털 표기 없음 (수정일 기준 참고) |

**주요 필드 (문서 기재)**: 가맹점명, 대표전화번호, 주소, 위경도, 사업자 상태, 표준산업분류코드.
정확한 JSON 필드명은 공식 문서에 완전 공개되지 않아 worker parser 가 관대한 alias 로 매핑한다 (`frcsNm`/`frcNm`/`mrhstNm`/`가맹점명` 등). 실 응답 확인 후 alias 를 축소한다.

## 안양 지역 코드

행정표준 시군구 코드 (5자리, 시도 2 + 시군구 3):

| 지역 | 코드 |
|---|---|
| 경기 안양시 만안구 | `41171` |
| 경기 안양시 동안구 | `41173` |

## Rate limit / Traffic 보호

- 개발계정 10,000/일 → 안양 sample 100건은 페이지 1~2회로 충분
- Worker `--limit` 옵션 필수 사용
- Rate limit 초과 시 KOMSCO API 는 다음날 00시(KST)에 리셋
- Dry-run 결과에 `api_calls=` 를 출력해 소비량 확인

## Secret 유출 방지 원칙

- Source code 에 절대 하드코딩 금지
- `git status` / `git diff` / `git log -p` 어디에도 실 key 노출 금지
- 로그·에러 메시지에도 마스킹 (worker 는 `WorkerConfig.masked_key`, `http_client._mask_url` 이 자동 처리)
- 사용자와 Claude 사이 채팅에서도 key 값 절대 공유 금지 (필요하면 사용자 본인이 VPS `.env` 에 직접 입력)

## 다음 gate 준비

- **Gate 3 온누리 CSV**: `3060079` 데이터셋에서 최신 CSV/XLSX snapshot 다운로드 (Key 불필요). VPS `/opt/localpay/data/onnuri/` 에 업로드해두면 worker 가 stream 파싱
- **Kakao Local (선택)**: 좌표 없는 온누리 데이터가 얼마나 되는지 Gate 3 결과 확인 후 필요성 판단
