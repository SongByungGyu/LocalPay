"""Raw · Normalized · Filtered 온누리 데이터 모델.

Gate 3-A 는 DB 미생성 (스펙 §27). Dry-run 통계·리포트에만 사용.
운영 반영은 Gate 3-B 이후 사용자 승인 후.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RawOnnuriRecord:
    """CSV 한 행을 원문에 가까운 형태로 담는다.

    공식 컬럼 (2025-07-31 snapshot):
      가맹점명, 소속 시장명(또는 상점가), 소재지, 취급품목,
      지류형 가맹 여부, 디지털형 가맹 여부, 등록년도

    Header 가 미래 스냅샷에서 바뀔 수 있으므로 parser 가 관대한 alias 로 매핑한다.
    raw_payload 는 dict(row) 원본 그대로 보존한다.
    """

    merchant_name: Optional[str]
    market_name: Optional[str]
    address: Optional[str]
    products_raw: Optional[str]
    supports_paper_raw: Optional[str]     # "Y"/"N"/"O"/"X" 등 원문 그대로
    supports_digital_raw: Optional[str]
    registration_year_raw: Optional[str]

    raw_payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedOnnuriRecord:
    """Normalize + payment/product/category/anyang filter 통과한 후 canonical 후보."""

    merchant_name: str
    merchant_name_normalized: str

    market_name: Optional[str]
    market_name_normalized: Optional[str]

    address: str
    address_normalized: str

    # 온누리 공식 데이터는 위경도 미제공 → 항상 None + geocode_status="pending"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coordinate_valid: bool = False
    geocode_status: str = "pending"        # pending | resolved | failed | ambiguous

    supports_paper: bool = False
    supports_digital: bool = False
    supports_onnuri: bool = True            # 온누리 데이터셋이므로 항상 True

    # 취급품목을 token 화한 배열 (원본은 raw 에 보존).
    products: List[str] = field(default_factory=list)
    products_raw: Optional[str] = None

    # 카테고리 매핑 결과 + 사유. 확실치 않으면 etc.
    mapped_category: str = "etc"
    category_source: str = "default"        # "market_name" / "product_keyword" / "default"

    registration_year: Optional[int] = None

    # 안양 필터에서 분류. "manan" / "dongan" / None
    anyang_district: Optional[str] = None

    # 시·도, 시·군·구 원문 (주소 앞 두 토큰). 실패 시 None.
    sido_raw: Optional[str] = None
    sigungu_raw: Optional[str] = None
