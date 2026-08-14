"""Raw → Normalized 온누리 레코드 변환.

- 상호명/시장명/주소: whitespace + Unicode normalize, 원본 보존
- 지류/디지털 여부: 'Y'/'N'/'O'/'X'/'있음'/'없음' 등 관대하게 파싱 → bool
- 등록년도: int 로 변환 시도, 실패 시 None
- 취급품목: 콤마/슬래시/파이프 기준 split, 각 항목 trim, 최대 20개
- 안양 필터: 2025-07-31 공식 CSV 는 소재지 컬럼이 시도(예: "경기") 만 담기 때문에
  주소 기반으로는 시군구를 판별할 수 없다. 대신 소속 시장명에 "안양" 이 포함되거나
  알려진 안양 소재 시장/상점가 이름이면 anyang 으로 분류한다.
  향후 상세 주소 포함 데이터셋으로 바뀌면 주소 기반 fallback 을 우선한다.
- 카테고리: market_name/products 키워드 기반 매핑, 불확실 → etc
- 좌표: 원본에 없음 → 항상 None + geocode_status="pending"
"""
from __future__ import annotations

import re
import unicodedata
from typing import List, Optional, Tuple

from worker.importers.onnuri.anyang_markets import ANYANG_MARKET_COORDS, lookup_market
from worker.importers.onnuri.category_mapper import map_category
from worker.importers.onnuri.models import NormalizedOnnuriRecord, RawOnnuriRecord


# Y/N 파싱: 다양한 표기 대응.
_TRUE_TOKENS = {"y", "yes", "o", "true", "1", "있음", "가능", "가맹"}
_FALSE_TOKENS = {"n", "no", "x", "false", "0", "없음", "불가", "미가맹"}


def normalize(raw: RawOnnuriRecord) -> Optional[NormalizedOnnuriRecord]:
    """이름/주소 없으면 None (skip). 나머지는 관대하게 진행."""
    name_norm = _clean_ws(raw.merchant_name)
    if not name_norm:
        return None
    addr_norm = _clean_ws(raw.address)
    if not addr_norm:
        return None

    market_norm = _clean_ws(raw.market_name)
    products = _split_products(raw.products_raw)
    sido, sigungu = _split_address_head(addr_norm)
    anyang_district = _classify_anyang(sido, sigungu, addr_norm, market_name=market_norm)

    # 시장 좌표 사전 lookup (안양 sample 용). 매핑 실패 시 좌표 없음 유지.
    market_coord = lookup_market(market_norm)
    if market_coord is not None:
        lat, lng, coord_district = market_coord
        coord_valid = True
        geocode_status = "resolved_market"
        # 사전 district 값이 있으면 이걸로 정정 (더 정확).
        if not anyang_district or anyang_district == "unknown":
            anyang_district = coord_district
    else:
        lat, lng = None, None
        coord_valid = False
        geocode_status = "pending"
    # marketName 은 category 결정에서 제외 (스펙 §결정 2). affiliation 정보로만 보존.
    mapped_cat, cat_src = map_category(
        products=products,
        merchant_name=name_norm,
    )

    return NormalizedOnnuriRecord(
        merchant_name=raw.merchant_name or "",
        merchant_name_normalized=name_norm,
        market_name=raw.market_name,
        market_name_normalized=market_norm,
        address=raw.address or "",
        address_normalized=addr_norm,
        latitude=lat,
        longitude=lng,
        coordinate_valid=coord_valid,
        geocode_status=geocode_status,
        supports_paper=_parse_yn(raw.supports_paper_raw),
        supports_digital=_parse_yn(raw.supports_digital_raw),
        supports_onnuri=True,
        products=products,
        products_raw=raw.products_raw,
        mapped_category=mapped_cat,
        category_source=cat_src,
        registration_year=_parse_year(raw.registration_year_raw),
        anyang_district=anyang_district,
        sido_raw=sido,
        sigungu_raw=sigungu,
    )


def _clean_ws(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = unicodedata.normalize("NFC", value).strip()
    s = re.sub(r"\s+", " ", s)
    return s or None


def _parse_yn(raw: Optional[str]) -> bool:
    if not raw:
        return False
    v = raw.strip().lower()
    if v in _TRUE_TOKENS:
        return True
    if v in _FALSE_TOKENS:
        return False
    # 알 수 없는 표기는 False (안전 기본값). 추론 금지.
    return False


def _parse_year(raw: Optional[str]) -> Optional[int]:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 4:
        return None
    try:
        y = int(digits[:4])
    except ValueError:
        return None
    if 1900 <= y <= 2100:
        return y
    return None


def _split_products(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    parts = re.split(r"[,\|/·、]", raw)
    tokens: List[str] = []
    seen = set()
    for p in parts:
        t = _clean_ws(p)
        if not t:
            continue
        if t in seen:
            continue
        seen.add(t)
        tokens.append(t)
        if len(tokens) >= 20:
            break
    return tokens


def _split_address_head(addr: str) -> Tuple[Optional[str], Optional[str]]:
    """주소 앞부분을 공백 기준 토큰화해 시/도 · 시/군/구 후보 반환.

    예: '경기도 안양시 만안구 만안로 232' → ('경기도', '안양시')
    반환값은 '만안구/동안구' 판별에는 사용 안 함 (별도 anyang classify 에서 처리).
    """
    tokens = addr.split(" ")
    if not tokens:
        return None, None
    sido = tokens[0] if tokens else None
    sigungu = tokens[1] if len(tokens) > 1 else None
    return sido, sigungu


def _classify_anyang(
    sido: Optional[str],
    sigungu: Optional[str],
    full_addr: str,
    market_name: Optional[str] = None,
) -> Optional[str]:
    """안양시 여부와 만안구/동안구 분류.

    2025-07-31 온누리 CSV 는 주소가 시도(예: '경기') 만 담고 시군구가 없어
    주소 기반 매칭이 불가능하다. 대신 소속 시장명 기반 매칭을 우선한다.

    반환값:
        "manan" / "dongan" / "unknown" / None
        - manan/dongan: 알려진 안양 시장에 매칭 (anyang_markets.py 사전 참조)
        - unknown: 시장명에 "안양" 포함되지만 구 매핑 사전에 없음
        - None: 안양 아님
    """
    # 1) 시장명 기반 판정 (anyang_markets.py 사전, single source of truth).
    if market_name:
        mkt = market_name.strip()
        coord = ANYANG_MARKET_COORDS.get(mkt)
        if coord is not None:
            return coord[2]     # (lat, lng, district) 튜플의 district
        if "안양" in mkt:
            return "unknown"

    # 2) 주소 기반 fallback (향후 상세 주소 포함 데이터셋 대비).
    if sido and ("경기" in sido) and sigungu and "안양시" in sigungu:
        if "만안구" in full_addr:
            return "manan"
        if "동안구" in full_addr:
            return "dongan"
        return "unknown"

    return None
