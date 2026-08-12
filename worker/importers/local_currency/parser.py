"""외부 API 응답 (dict) → RawLocalCurrencyRecord 변환.

공식 필드 이름 후보를 관대하게 매핑한다. KOMSCO 계열 다른 API 에서 관측된
표기 (`frcNm`, `frcsNm`, `가맹점명`, `mrhstNm` 등) 및 표준 지역화폐 데이터
필드를 모두 시도해 첫 non-empty 값을 사용한다.
공식 성공 응답을 확인한 뒤에는 이 mapping table 을 정확한 이름으로 축소한다.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from worker.importers.local_currency.models import RawLocalCurrencyRecord

# 필드별 후보명 (KOMSCO 계열 · 표준 데이터셋 관측 값 합집합).
FIELD_ALIASES: Dict[str, tuple[str, ...]] = {
    "source_merchant_id": ("frcsNo", "frcNo", "mrhstNo", "가맹점번호", "id"),
    "merchant_name": ("frcsNm", "frcNm", "mrhstNm", "brmnNm", "가맹점명", "brandNm"),
    "phone": ("frcsTelNo", "frcTelNo", "mrhstTelNo", "telNo", "대표전화번호", "phoneNumber"),
    "address": ("frcsAddr", "frcAddr", "mrhstAddr", "addr", "주소", "lnmAddr"),
    "road_address": ("frcsRoadNmAddr", "roadAddr", "roadNmAddr", "도로명주소"),
    "latitude": ("frcsLa", "frcLa", "la", "lat", "latitude", "위도"),
    "longitude": ("frcsLo", "frcLo", "lo", "lng", "longitude", "경도"),
    "business_status": ("bzsttNm", "bzsttCd", "사업자상태", "businessStatus"),
    "industry_code": ("indutyCd", "ksicCd", "표준산업분류코드", "industryCode", "bzMnBzMnCd"),
    "region_code": ("usePlcRegnCd", "sidoSggCd", "hdongCd", "brNo"),
}


def parse_response_items(
    items: Iterable[Dict[str, Any]],
    *,
    source_provider: str = "komsco-integrated",
) -> List[RawLocalCurrencyRecord]:
    return [_parse_one(item, source_provider=source_provider) for item in items]


def _parse_one(item: Dict[str, Any], *, source_provider: str) -> RawLocalCurrencyRecord:
    return RawLocalCurrencyRecord(
        source_provider=source_provider,
        source_merchant_id=_get_str(item, FIELD_ALIASES["source_merchant_id"]),
        merchant_name=_get_str(item, FIELD_ALIASES["merchant_name"]),
        phone=_get_str(item, FIELD_ALIASES["phone"]),
        address=_get_str(item, FIELD_ALIASES["address"]),
        road_address=_get_str(item, FIELD_ALIASES["road_address"]),
        latitude=_get_float(item, FIELD_ALIASES["latitude"]),
        longitude=_get_float(item, FIELD_ALIASES["longitude"]),
        business_status=_get_str(item, FIELD_ALIASES["business_status"]),
        industry_code=_get_str(item, FIELD_ALIASES["industry_code"]),
        region_code=_get_str(item, FIELD_ALIASES["region_code"]),
        raw_payload=dict(item),
    )


def _get_str(item: Dict[str, Any], keys: tuple[str, ...]) -> Optional[str]:
    for k in keys:
        if k in item and item[k] is not None and str(item[k]).strip() != "":
            return str(item[k]).strip()
    return None


def _get_float(item: Dict[str, Any], keys: tuple[str, ...]) -> Optional[float]:
    for k in keys:
        if k in item and item[k] is not None and str(item[k]).strip() != "":
            try:
                return float(item[k])
            except (TypeError, ValueError):
                continue
    return None
