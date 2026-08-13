"""Raw → Normalized 온누리 레코드 변환.

- 상호명/시장명/주소: whitespace + Unicode normalize, 원본 보존
- 지류/디지털 여부: 'Y'/'N'/'O'/'X'/'있음'/'없음' 등 관대하게 파싱 → bool
- 등록년도: int 로 변환 시도, 실패 시 None
- 취급품목: 콤마/슬래시/파이프 기준 split, 각 항목 trim, 최대 20개
- 안양 필터: 주소 앞부분에 "안양시" 포함 + 만안/동안 분류
- 카테고리: market_name/products 키워드 기반 매핑, 불확실 → etc
- 좌표: 원본에 없음 → 항상 None + geocode_status="pending"
"""
from __future__ import annotations

import re
import unicodedata
from typing import List, Optional, Tuple

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
    anyang_district = _classify_anyang(sido, sigungu, addr_norm)
    mapped_cat, cat_src = map_category(
        market_name=market_norm,
        products=products,
    )

    return NormalizedOnnuriRecord(
        merchant_name=raw.merchant_name or "",
        merchant_name_normalized=name_norm,
        market_name=raw.market_name,
        market_name_normalized=market_norm,
        address=raw.address or "",
        address_normalized=addr_norm,
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
    sido: Optional[str], sigungu: Optional[str], full_addr: str
) -> Optional[str]:
    """안양시 여부와 만안구/동안구 분류."""
    if not (sido and ("경기" in sido)):
        # 경기도 아닌데 '안양시' 문자열 우연히 있어도 우리 안양 필터 대상 X.
        return None
    if not sigungu or "안양시" not in sigungu:
        return None
    # 만안구/동안구는 주소 전체 문자열에서 탐색 (sigungu 는 '안양시' 만일 수 있음).
    if "만안구" in full_addr:
        return "manan"
    if "동안구" in full_addr:
        return "dongan"
    # 안양시는 맞지만 구 미명시 → 만안 기본값 대신 unknown (안전).
    return "unknown"
