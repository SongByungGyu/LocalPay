# LOCAL_CURRENCY_API_BLOCKER — KOMSCO 통합 API 지역 필터 미확인 이슈

> Phase 13 Gate 2 진행 중 확인된 blocker 를 기록한다.
> 이 문서 자체에 서비스 키 값은 절대 기록하지 않는다.

## 상태

**BLOCKED** — 서버측 지역 요청 필터 파라미터를 확인하지 못함.

## Dataset

- **ID**: `15119539`
- **제목**: 한국조폐공사_통합_가맹점기본정보
- 관련 페이지: [https://www.data.go.kr/data/15119539/openapi.do](https://www.data.go.kr/data/15119539/openapi.do)

## 확인된 사실

### API 접속
- **Base URL**: `http://apis.data.go.kr/B190001/localFranchisesV2`
- **Endpoint**: `GET /franchiseV2`
- **Auth**: query param `serviceKey` (Encoding/Decoding 모두 worker 가 자동 정규화)
- **Format**: `type=json` 지원 (JSON+XML)

### 응답 스키마 (실측)
```json
{
  "currentCount": 10,
  "matchCount": 8109528,
  "totalCount": 8109528,
  "page": 1,
  "perPage": 10,
  "data": [
    {
      "frcs_nm": "…",
      "frcs_addr": "…",
      "frcs_dtl_addr": "…",
      "frcs_rprs_telno": "…",
      "frcs_zip": "…",
      "lat": null,
      "lot": null,
      "bzmn_stts": "03",
      "bzmn_stts_nm": "폐업자",
      "ksic_cd": "961",
      "ksic_cd_nm": "…",
      "usage_rgn_cd": "47250",
      "emd_cd": null,
      "emd_nm": null,
      "brno": "…",
      "frcs_reg_se": "02",
      "frcs_reg_se_nm": "변경",
      "frcs_stlm_info_se": "01,02",
      "frcs_stlm_info_se_nm": "카드,모바일",
      "pvsn_inst_cd": "I0000011",
      "crtr_ymd": "20260401",
      "bk_awa_perf_hd_yn": "N",
      "onl_dlvy_ent_use_yn": "N",
      "pos_use_yn": "N",
      "ppr_frcs_aply_yn": "N",
      "te_gds_hd_yn": "N",
      "qr_reg_conm": null,
      "alt_text": "…"
    }
  ]
}
```

### Pagination (실측)
- 파라미터: `page`, `perPage`
- 공공데이터포털 표준 `pageNo`, `numOfRows` 는 무시됨
- 기본 perPage = 10

### 응답 지역 필드
- `usage_rgn_cd` (5자리, 시도 2 + 시군구 3) — 응답에는 정상 담김
- 참고문서 `(참고)사용처지역코드.xlsx` 에 코드표 존재
  - 안양시 만안구 = `41171`, 동안구 = `41173`

## 문제 — 지역 요청 필터 미확인

동일 조건에서 아래 11가지 파라미터 이름을 실 API 로 시도했으나 **모두 무시됨** (반환 결과가 `matchCount=8,109,528` 로 동일, `first.usage_rgn_cd=47250` 로 안양 필터 미적용):

| 시도 | 결과 |
|---|---|
| `usePlcRegnCd=41171` | 810만 (전국) |
| `usage_rgn_cd=41171` | 810만 |
| `usageRgnCd=41171` | 810만 |
| `usePlcRgnCd=41171` | 810만 |
| `useplcrgncd=41171` | 810만 |
| `USEPLCRGNCD=41171` | 810만 |
| `rgnCd=41171` | 810만 |
| `regnCd=41171` | 810만 |
| `signguCd=41171` | 810만 |
| `sido=41 sgg=171` | 810만 |
| `usePlcCd=41171` / `usePlcAreaCd=41171` / `useCd=41171` | 810만 |

### 참고문서 상태
공공데이터포털 페이지의 "참고문서" 섹션에는 코드 표 (xlsx) 만 있고, OpenAPI 활용가이드 · 명세서 · 요청변수 표 문서는 공개되어 있지 않음. 즉 서버 측 요청 파라미터 이름을 확인할 공식 소스가 없음.

## Full Fetch 를 하지 않는 이유

- 전체 매장 수: **8,109,528 건**
- 개발계정 traffic: **10,000 호출/일**
- 최대 perPage 가정 300 → 하루 300만건 → **최소 3일** 소요
- API 남용 리스크
- 그 사이 데이터 갱신도 발생 → 스냅샷 무결성 깨짐
- Backend/VPS 처리 리소스도 낭비

**결정**: 개발계정으로 전국 810만 건 Full Fetch 는 **금지**.

## 후속 옵션

1. **KOMSCO / 공공데이터포털 Q&A 문의**
   - 지역 요청 필터 파라미터 정확한 이름 · 사용법
   - 응답 수 ~ 수 일 예상
2. **공식 활용가이드 재확인**
   - 페이지 재조회, PDF 첨부 있을 수 있음
3. **개별 상품권 API 활용신청**
   - 15108275 지류 · 15108279 카드 · 15108285 모바일
   - 각 API 가 지역 필터 지원 가능성. 재신청 · 문서 확인 필요
4. **표준데이터셋 15100062 (전국지역화폐가맹점표준데이터)**
   - CSV 파일 형태로 제공, 지역별 분리 가능성
   - Traffic 무관
5. **운영계정 트래픽 확대 신청**
   - 활용사례 등록 필요, 승인까지 시간
6. **client-side filter (권장 X)**
   - 810만 건 전체 fetch 후 `usage_rgn_cd` 로 걸러야 하는데 개발계정으로는 3일 소요

## 진행 방침 (2026-08-13)

- Gate 2 는 **BLOCKED** 유지
- Gate 3 (온누리 파일 방식) 을 먼저 진행하여 파이프라인 · canonical merge 검증
- KOMSCO 이슈는 아래 중 하나가 해결되면 Gate 2 재개:
  - Q&A 응답 수신
  - 활용가이드 확보
  - 대안 dataset 채택 결정

## 보안 메모

- 이 문서에 서비스 키 값 (Encoding/Decoding 모두) 절대 기록 금지
- 실제 값은 VPS `/opt/localpay/deploy/.env` 의 `DATA_GO_KR_SERVICE_KEY` 에만 존재
- worker `WorkerConfig.masked_key` · `http_client._mask_url` 가 로그 masking 담당

## 관련 문서

- `docs/PUBLIC_DATA_SETUP.md` — 활용신청 절차
- `worker/importers/local_currency/` — 파이프라인 코드 (인증 · 파싱 · 정규화 완비)
- `LocalPayiOS/report/09_Phase13_Gate2A.md` — Gate 2-A 완료 보고
