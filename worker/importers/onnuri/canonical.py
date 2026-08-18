"""Onnuri raw → CanonicalMerchantCandidate 변환.

Gate 3-B2 는 이 변환을 **메모리에서 dry-run 만** 수행한다. canonical `merchants`
테이블에 실제 INSERT 는 하지 않는다 (Gate 4 이후).

## Canonical id 규칙

`onnuri-a-{row_hash[:16]}`
  - `onnuri` = 소스 종류
  - `a` = 지역 (anyang). 향후 전국 확장 시 sido 코드 사용
  - `row_hash[:16]` = SHA1(공식 7 field tab-join) 앞 16자.
    → 동일 소스 동일 스냅샷의 동일 매장은 항상 같은 id 를 얻음 (idempotent).
    → snapshot 이 바뀌어도 (파일 갱신) 매장 데이터가 동일하면 같은 id 유지.

## Location metadata

시장 매핑 여부에 따라 (docs/LOCATION_PRECISION.md):
  - 전통시장 5개 (dataset 매칭) → source=market_dataset, precision=market_level, confidence=0.8
  - 상점가 7개 (하드코딩) → source=market_centroid_manual, precision=market_level, confidence=0.7
  - 매칭 없음 → 좌표 없음, source=None, precision=region_level (지도 미노출)

anyang_markets.py 사전이 두 카테고리를 구분하지 않으니 이번 Gate 는 모두
market_centroid_manual/0.7 로 통일 (안전한 기본값). Gate 4 이전 사전을 두 카테고리로
분리하여 정확한 confidence 배정 예정.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from worker.importers.onnuri.anyang_markets import lookup_market
from worker.importers.onnuri.models import NormalizedOnnuriRecord


# location_source 후보
LOC_SOURCE_MARKET_DATASET = "market_dataset"        # 전통시장 dataset 매칭
LOC_SOURCE_MARKET_CENTROID = "market_centroid_manual"  # 상점가 하드코딩
LOC_SOURCE_KAKAO = "kakao_place"
LOC_SOURCE_MANUAL = "manual"
LOC_SOURCE_DUMMY = "dummy_seed"
LOC_SOURCE_SOURCE_EXACT = "source_exact"

# 전통시장 dataset 매칭된 시장 (Gate 3-B2 시점 사전 상수. 향후 데이터화 예정).
TRADITIONAL_MARKET_NAMES: set[str] = {
    "안양중앙시장",
    "안양중앙인정시장",
    "안양남부시장",
    "안양육동시장",
    "안양관양시장",
}


@dataclass
class CanonicalMerchantCandidate:
    """Backend `MerchantOut` 과 호환되는 canonical merchant 후보.

    Dry-run 결과이므로 아직 DB 에 저장되지 않는다.
    필드 이름은 iOS `Merchant` 도메인과 1:1 호환 (docs/API_SCHEMA.md).
    """

    id: str
    name: str
    category: str

    latitude: Optional[float]
    longitude: Optional[float]

    address: str
    road_address: Optional[str]
    phone: Optional[str]

    supports_onnuri: bool
    supports_local_currency: bool
    local_currency_name: Optional[str]
    supported_payment_types: List[str]

    products: List[str]
    business_hours: Optional[Dict[str, str]]
    rating: float
    review_count: int

    market_name: Optional[str]
    description: Optional[str]

    source: str            # 예: "onnuri-snapshot-20250731"
    source_id: Optional[str]

    is_active: bool

    location_source: Optional[str]
    location_precision: Optional[str]
    location_confidence: Optional[float]

    # dry-run 만 유지되는 참고 정보 (실 DB 저장 시 제외).
    raw_row_hash: str = ""
    anyang_district: Optional[str] = None
    reasons: List[str] = field(default_factory=list)


def to_canonical(
    normalized: NormalizedOnnuriRecord,
    *,
    row_hash: str,
    snapshot_date: str,
    region_alias: str = "a",   # 'a' = anyang
) -> CanonicalMerchantCandidate:
    """NormalizedOnnuriRecord → CanonicalMerchantCandidate.

    row_hash 는 raw 저장 시 계산한 것 (writer._row_hash) 을 재사용해 id 안정성 유지.
    """
    canonical_id = f"onnuri-{region_alias}-{row_hash[:16]}"

    # 지원 결제수단 (온누리 계열).
    supported_types: List[str] = []
    if normalized.supports_paper:
        supported_types.append("onnuriPaper")
    if normalized.supports_digital:
        supported_types.append("onnuriDigital")

    # Location metadata 결정.
    market_norm = normalized.market_name_normalized
    coord = lookup_market(market_norm) if market_norm else None
    if coord is not None:
        lat, lng, _district = coord
        if market_norm in TRADITIONAL_MARKET_NAMES:
            loc_source = LOC_SOURCE_MARKET_DATASET
            loc_confidence = 0.8
        else:
            loc_source = LOC_SOURCE_MARKET_CENTROID
            loc_confidence = 0.7
        loc_precision = "market_level"
    else:
        lat, lng = None, None
        loc_source = None
        loc_precision = "region_level"
        loc_confidence = None

    return CanonicalMerchantCandidate(
        id=canonical_id,
        name=normalized.merchant_name_normalized,
        category=normalized.mapped_category,
        latitude=lat,
        longitude=lng,
        address=normalized.address_normalized,
        road_address=normalized.road_address if hasattr(normalized, "road_address") else None,
        phone=None,   # 온누리 원본은 전화번호 미제공 (스펙 3060079)
        supports_onnuri=True,
        supports_local_currency=False,   # 온누리 데이터셋만으로는 판정 불가
        local_currency_name=None,
        supported_payment_types=supported_types,
        products=list(normalized.products),
        business_hours=None,             # 온누리 원본은 영업시간 미제공
        rating=0.0,
        review_count=0,
        market_name=normalized.market_name,
        description=None,
        source=f"onnuri-snapshot-{snapshot_date}",
        source_id=row_hash,
        is_active=True,
        location_source=loc_source,
        location_precision=loc_precision,
        location_confidence=loc_confidence,
        raw_row_hash=row_hash,
        anyang_district=normalized.anyang_district,
        reasons=[
            f"category_source={normalized.category_source}",
            f"market={market_norm or '-'}",
            f"district={normalized.anyang_district or '-'}",
        ],
    )
