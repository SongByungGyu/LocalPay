"""KOMSCO 통합 지역화폐 가맹점 API client.

- Dataset: 15119539 (한국조폐공사_통합_가맹점기본정보)
- Base URL: `http://apis.data.go.kr/B190001/localFranchisesV2`
- Endpoint: `/franchiseV2`
- Auth: `serviceKey` (query, 소문자 s)
- Format: `type=json`
- Pagination: `pageNo`, `numOfRows`
- 지역 필터 후보:
  - 사용처지역코드 (5자리, 시도 2 + 시군구 3). 안양시 만안구=`41171`, 동안구=`41173`
  - 읍면동코드 (8자리)
- 개발계정 traffic: 10,000/일

응답 field 명은 공식 문서에 완전 공개되지 않아 실제 성공 응답으로 확정한다.
parser 가 여러 후보명 (`frcNm`, `frcsNm`, `가맹점명`) 을 관대하게 매핑한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional
from urllib.parse import unquote

from worker.core.http_client import ExternalApiError, ExternalHttpClient

BASE_URL = "http://apis.data.go.kr/B190001/localFranchisesV2/franchiseV2"

# 지역별 사용처지역코드. 필요 시 확장.
# 참고: 행정표준 시군구 코드 5자리 (시도 2 + 시군구 3).
REGION_CODES = {
    "anyang-manan": "41171",   # 경기 안양 만안구
    "anyang-dongan": "41173",  # 경기 안양 동안구
}


@dataclass
class FetchResult:
    fetched: List[Dict[str, Any]]
    api_calls: int
    total_reported: Optional[int]  # API 가 header 에 totalCount 를 준다면 사용


class LocalCurrencyApiClient:
    def __init__(self, service_key: str, http: Optional[ExternalHttpClient] = None):
        if not service_key:
            raise ValueError("service_key must not be empty")
        # 공공데이터포털은 인증키를 두 가지로 제공한다:
        #   - Encoding: URL 인코딩 (예: `abc%2B==` 처럼 %2B, %3D 등 포함)
        #   - Decoding: 원본 (예: `abc+==`)
        # httpx 는 params 를 자동으로 URL 인코딩하므로, 사용자가 Encoding 값을 넣으면
        # 이중 인코딩되어 SERVICE_KEY_IS_NOT_REGISTERED_ERROR 를 유발한다.
        # 어느 쪽이든 넣어도 동작하도록 여기서 한 번 decode 해 canonical (raw) 형태로 정규화.
        # 이미 decoded 상태라면 unquote 는 no-op.
        self._service_key = unquote(service_key)
        self._http = http or ExternalHttpClient()

    def fetch_region(
        self,
        region: str,
        *,
        max_records: int = 100,
        page_size: int = 100,
    ) -> FetchResult:
        """지역 alias (예: `anyang-manan`) 로 페이지네이션 fetch."""
        if region not in REGION_CODES:
            raise ValueError(f"unknown region alias: {region}. use one of {list(REGION_CODES)}")
        return self.fetch_by_region_code(
            REGION_CODES[region],
            max_records=max_records,
            page_size=page_size,
        )

    def fetch_by_region_code(
        self,
        region_code: str,
        *,
        max_records: int = 100,
        page_size: int = 100,
    ) -> FetchResult:
        collected: List[Dict[str, Any]] = []
        api_calls = 0
        total_reported: Optional[int] = None

        for page_no in self._page_generator():
            remaining = max_records - len(collected)
            if remaining <= 0:
                break
            batch_size = min(page_size, remaining)

            params = {
                "serviceKey": self._service_key,
                "type": "json",
                "pageNo": page_no,
                "numOfRows": batch_size,
                # 실제 파라미터 이름은 공식 명세에 완전 공개되지 않아 두 후보를 모두 전달.
                # 성공 응답 확인 후 하나로 축소한다.
                "usePlcRegnCd": region_code,
                "sidoSggCd": region_code,
            }

            resp = self._http.get_json(BASE_URL, params=params)
            api_calls += 1

            items, page_total = _extract_items(resp.json_body)
            if page_total is not None:
                total_reported = page_total

            if not items:
                break
            collected.extend(items)
            if len(items) < batch_size:
                break  # 마지막 페이지.

        return FetchResult(
            fetched=collected[:max_records],
            api_calls=api_calls,
            total_reported=total_reported,
        )

    def _page_generator(self) -> Iterator[int]:
        # 무한 페이지 방지: 최대 20 페이지 (개발계정 traffic 보호).
        for i in range(1, 21):
            yield i


def _extract_items(body: Any) -> tuple[List[Dict[str, Any]], Optional[int]]:
    """
    공공데이터포털 표준 응답 skeleton 추출.
    성공 시:
        response.header.resultCode == "00"
        response.body.items 안에 리스트
        response.body.totalCount
    실패 시:
        OpenAPI_ServiceResponse.cmmMsgHeader.errMsg
    다양한 KOMSCO 계열 API 의 실제 형태가 조금씩 다르므로 관대하게 파싱한다.
    """
    if not isinstance(body, dict):
        raise ExternalApiError(f"unexpected response type: {type(body).__name__}", body_preview=str(body)[:200])

    # 인증/시스템 에러 형태.
    if "OpenAPI_ServiceResponse" in body:
        header = body["OpenAPI_ServiceResponse"].get("cmmMsgHeader") or {}
        raise ExternalApiError(
            f"api service error: {header.get('errMsg')} ({header.get('returnAuthMsg')})",
            body_preview=str(body)[:500],
        )

    resp = body.get("response") or body.get("Response")
    if not isinstance(resp, dict):
        # 이미 리스트 형태로 오는 케이스도 방어.
        if isinstance(body, list):
            return body, None
        raise ExternalApiError("response envelope not found", body_preview=str(body)[:500])

    header = resp.get("header") or {}
    result_code = str(header.get("resultCode") or "").strip()
    if result_code and result_code not in ("00", "0"):
        raise ExternalApiError(
            f"api result error: {result_code} {header.get('resultMsg')}",
            body_preview=str(body)[:500],
        )

    body_section = resp.get("body") or {}
    items_section = body_section.get("items") or {}
    total_count_raw = body_section.get("totalCount")
    total_count: Optional[int] = None
    try:
        if total_count_raw is not None:
            total_count = int(total_count_raw)
    except (TypeError, ValueError):
        total_count = None

    # items 가 dict 안의 item 리스트인 경우 / 바로 리스트인 경우 둘 다.
    if isinstance(items_section, dict):
        raw_items = items_section.get("item") or []
    elif isinstance(items_section, list):
        raw_items = items_section
    else:
        raw_items = []

    if isinstance(raw_items, dict):
        raw_items = [raw_items]  # 1건일 때 dict 로 오는 경우.

    return list(raw_items), total_count
