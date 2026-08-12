"""Raw record → Normalized record.

스펙 §13 준수:
- 상호명: 앞뒤 공백 제거, 연속 공백 통합, unicode NFC. 원본 보존.
- 전화: 숫자만 추출 후 형식 정리. 원본 보존.
- 주소: 공백 정리. 원본 보존.
- 좌표: 대한민국 대략 범위 (33~39, 124~132) 밖은 invalid. 0,0 거부.
좌표 생성 금지.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional, Tuple

from worker.importers.local_currency.category_mapper import map_industry_to_category
from worker.importers.local_currency.models import (
    NormalizedLocalCurrencyRecord,
    RawLocalCurrencyRecord,
)

# 대한민국 육상 대략 범위. 이 밖은 KOMSCO 데이터에서 오는 유효 좌표가 아님.
KR_LAT_MIN, KR_LAT_MAX = 33.0, 39.0
KR_LNG_MIN, KR_LNG_MAX = 124.0, 132.0


class NormalizationError(ValueError):
    pass


def normalize(raw: RawLocalCurrencyRecord) -> Optional[NormalizedLocalCurrencyRecord]:
    """
    normalize 실패 (예: 상호명 없음, 주소 없음) 시 None 반환.
    좌표 invalid 는 record 자체는 유지하되 coordinate_valid=False.
    호출부는 None 을 skip 한다.
    """
    name = _normalize_name(raw.merchant_name)
    if not name:
        return None
    address = _normalize_address(raw.address)
    if not address:
        return None

    lat_lng, coord_reason = _validate_coordinate(raw.latitude, raw.longitude)
    lat, lng = lat_lng if lat_lng else (None, None)

    return NormalizedLocalCurrencyRecord(
        source_provider=raw.source_provider,
        source_merchant_id=raw.source_merchant_id,
        merchant_name=raw.merchant_name or "",
        merchant_name_normalized=name,
        phone=raw.phone,
        phone_normalized=_normalize_phone(raw.phone),
        address=raw.address or "",
        address_normalized=address,
        road_address=_clean_str(raw.road_address),
        latitude=lat,
        longitude=lng,
        coordinate_valid=lat is not None,
        coordinate_reason=coord_reason,
        business_status=_clean_str(raw.business_status),
        industry_code=_clean_str(raw.industry_code),
        mapped_category=map_industry_to_category(raw.industry_code),
        region_code=_clean_str(raw.region_code),
    )


def _normalize_name(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = unicodedata.normalize("NFC", value).strip()
    v = re.sub(r"\s+", " ", v)
    return v or None


def _normalize_address(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = unicodedata.normalize("NFC", value).strip()
    v = re.sub(r"\s+", " ", v)
    return v or None


def _normalize_phone(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if not digits:
        return None
    # 국내 유선/휴대: 02, 010 등 첫 자리 별 분리.
    # 정형 안 되면 원본 digits 만 반환.
    if digits.startswith("02") and len(digits) in (9, 10):
        head, mid, tail = digits[:2], digits[2:-4], digits[-4:]
        return f"{head}-{mid}-{tail}"
    if len(digits) in (10, 11):
        head, mid, tail = digits[:3], digits[3:-4], digits[-4:]
        return f"{head}-{mid}-{tail}"
    return digits


def _clean_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = str(value).strip()
    return v or None


def _validate_coordinate(
    lat: Optional[float], lng: Optional[float]
) -> Tuple[Optional[Tuple[float, float]], Optional[str]]:
    if lat is None or lng is None:
        return None, "missing"
    if lat == 0.0 and lng == 0.0:
        return None, "zero-zero"
    if not (KR_LAT_MIN <= lat <= KR_LAT_MAX and KR_LNG_MIN <= lng <= KR_LNG_MAX):
        return None, f"out-of-range({lat},{lng})"
    return (lat, lng), None
