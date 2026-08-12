"""Raw · Normalized 데이터 모델.

DB 테이블과 이름/타입을 정렬하되, 이번 Gate 2-A 는 DB 미생성 (스펙 §12).
Dry Run 통계·리포트에만 사용한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class RawLocalCurrencyRecord:
    """공공데이터포털 응답 한 건을 원본에 가깝게 담아 둔다.

    운영 DB `raw_local_currency_merchants` 후보 스키마와 필드 이름을 맞춰 둔다.
    실제 API 응답 필드명은 성공 응답이 오기 전까지 완전 확정 불가하므로,
    parser 가 여러 가능한 필드명 (예: `frcNm`, `frcsNm`, `가맹점명`) 을 관대하게 매핑한다.
    원본 payload 는 raw_payload 로 100% 보존한다.
    """

    source_provider: str
    source_merchant_id: Optional[str]

    merchant_name: Optional[str]
    phone: Optional[str]

    address: Optional[str]
    road_address: Optional[str]

    latitude: Optional[float]
    longitude: Optional[float]

    business_status: Optional[str]
    industry_code: Optional[str]

    region_code: Optional[str]

    raw_payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedLocalCurrencyRecord:
    """Normalize 후 canonical merchant 후보로 넘길 수 있는 형태."""

    source_provider: str
    source_merchant_id: Optional[str]

    merchant_name: str
    merchant_name_normalized: str

    phone: Optional[str]
    phone_normalized: Optional[str]

    address: str
    address_normalized: str
    road_address: Optional[str]

    latitude: Optional[float]
    longitude: Optional[float]
    coordinate_valid: bool
    coordinate_reason: Optional[str]

    business_status: Optional[str]
    industry_code: Optional[str]
    mapped_category: str

    region_code: Optional[str]

    supports_local_currency: bool = True
    supports_onnuri: bool = False
    local_currency_name: Optional[str] = None
