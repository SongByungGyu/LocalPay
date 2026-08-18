"""Market Aggregate endpoints (Gate 3-C 스펙 §7, §8).

`location_precision = 'market_level'` 인 매장을 `market_name` 기준으로 집계.
지도 마커는 시장 단위, 탭 시 매장 리스트 API 로 상세 fetch.

- GET /api/v1/markets/map?north&south&east&west&category&payment
- GET /api/v1/markets/{market_id}/merchants?category&payment&q&limit&offset

marketId 는 `market:<url-safe-slug-of-name>` 형태.
"""
from __future__ import annotations

import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.orm import selectinload

from app.deps import SessionDep
from app.models.merchant import Merchant
from app.schemas.common import CamelModel
from app.schemas.merchant import MerchantOut

router = APIRouter(prefix="/markets", tags=["markets"])


VALID_CATEGORIES = {
    "restaurant", "cafe", "pharmacy", "mart", "market",
    "food", "beauty", "life", "etc",
}
VALID_PAYMENT_FILTERS = {"all", "onnuri", "localCurrency", "both"}

DEFAULT_LIMIT = 100
MAX_LIMIT = 500
MAX_BBOX_DEGREES = 6.0


# ---------- schema ----------

class MarketAggregateOut(CamelModel):
    id: str                              # e.g. "market:안양중앙시장"
    name: str
    latitude: float
    longitude: float
    merchant_count: int
    paper_count: int
    digital_count: int
    location_source: Optional[str] = None
    location_precision: str
    location_confidence: Optional[float] = None


# ---------- helpers ----------

_MARKET_ID_SAFE_RE = re.compile(r"[^\w가-힣ㄱ-ㅎㅏ-ㅣ-]")


def market_name_to_id(name: str) -> str:
    """공백을 - 로 · 안전한 슬러그로. 매장명은 한글 그대로."""
    slug = _MARKET_ID_SAFE_RE.sub("-", (name or "").strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return f"market:{slug}"


def market_id_to_name_pattern(market_id: str) -> str:
    """id → 원래 시장명 후보. slug 는 공백을 - 로 바꿨으므로 역변환."""
    if not market_id.startswith("market:"):
        raise HTTPException(status_code=400, detail="invalid market id")
    slug = market_id[len("market:"):]
    # slug 안의 `-` 를 정확히 원문 공백/`-` 로 되돌릴 수 없음 → 두 후보 다 시도.
    # 안전을 위해 LIKE 검색 (한글은 그대로 유지되고 공백 자리에 `-` 나 ` ` 매칭).
    return slug.replace("-", "_")   # SQL LIKE 의 _ 는 임의 1문자


def _apply_payment_filter_merchant(stmt, payment: str):
    if payment == "onnuri":
        return stmt.where(Merchant.supports_onnuri.is_(True))
    if payment == "localCurrency":
        return stmt.where(Merchant.supports_local_currency.is_(True))
    if payment == "both":
        return stmt.where(
            and_(Merchant.supports_onnuri.is_(True), Merchant.supports_local_currency.is_(True))
        )
    return stmt


# ---------- endpoints ----------

@router.get(
    "/map",
    response_model=List[MarketAggregateOut],
    response_model_by_alias=True,
    summary="Market Aggregate BBOX (시장 대표 마커)",
)
async def markets_map(
    session: SessionDep,
    north: float = Query(..., ge=-90, le=90),
    south: float = Query(..., ge=-90, le=90),
    east: float = Query(..., ge=-180, le=180),
    west: float = Query(..., ge=-180, le=180),
    category: Optional[str] = Query(default=None),
    payment: str = Query(default="all"),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> List[MarketAggregateOut]:
    if north <= south:
        raise HTTPException(status_code=400, detail="north must be greater than south")
    if east <= west:
        raise HTTPException(status_code=400, detail="east must be greater than west")
    if (north - south) > MAX_BBOX_DEGREES or (east - west) > MAX_BBOX_DEGREES:
        raise HTTPException(status_code=400, detail=f"bbox too large (max {MAX_BBOX_DEGREES}°)")
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"invalid category: {category}")
    if payment not in VALID_PAYMENT_FILTERS:
        raise HTTPException(status_code=400, detail=f"invalid payment: {payment}")

    envelope = func.ST_MakeEnvelope(west, south, east, north, 4326)

    # market_level 매장만 대상. market_name IS NOT NULL. group by market_name.
    # 시장 이름별로 centroid 좌표 (모두 동일하므로 MIN 로 대표), count,
    # onnuriPaper/onnuriDigital 지원 매장 수, location metadata 집계.
    supported_types_text = cast(Merchant.supported_payment_types, String)

    stmt = (
        select(
            Merchant.market_name.label("market_name"),
            func.min(Merchant.latitude).label("lat"),
            func.min(Merchant.longitude).label("lng"),
            func.min(Merchant.location_source).label("location_source"),
            func.min(Merchant.location_precision).label("location_precision"),
            func.min(Merchant.location_confidence).label("location_confidence"),
            func.count().label("merchant_count"),
            func.sum(
                func.cast(
                    func.lower(supported_types_text).contains("onnuripaper"),
                    __import__("sqlalchemy").Integer,
                )
            ).label("paper_count"),
            func.sum(
                func.cast(
                    func.lower(supported_types_text).contains("onnuridigital"),
                    __import__("sqlalchemy").Integer,
                )
            ).label("digital_count"),
        )
        .where(Merchant.is_active.is_(True))
        .where(Merchant.location_precision == "market_level")
        .where(Merchant.market_name.isnot(None))
        .where(func.ST_Intersects(Merchant.geom, envelope))
        .group_by(Merchant.market_name)
    )

    if category:
        stmt = stmt.where(Merchant.category == category)
    stmt = _apply_payment_filter_merchant(stmt, payment)
    stmt = stmt.order_by(func.count().desc()).limit(limit)

    result = await session.execute(stmt)
    rows = result.all()

    out: List[MarketAggregateOut] = []
    for r in rows:
        out.append(MarketAggregateOut(
            id=market_name_to_id(r.market_name),
            name=r.market_name,
            latitude=float(r.lat),
            longitude=float(r.lng),
            merchant_count=int(r.merchant_count),
            paper_count=int(r.paper_count or 0),
            digital_count=int(r.digital_count or 0),
            location_source=r.location_source,
            location_precision=r.location_precision or "market_level",
            location_confidence=r.location_confidence,
        ))
    return out


@router.get(
    "/{market_id}/merchants",
    response_model=List[MerchantOut],
    response_model_by_alias=True,
    summary="Market 안 매장 리스트 (paginated)",
)
async def merchants_in_market(
    session: SessionDep,
    market_id: str,
    q: Optional[str] = Query(default=None, min_length=1, max_length=100),
    category: Optional[str] = Query(default=None),
    payment: str = Query(default="all"),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0, le=10_000),
) -> List[MerchantOut]:
    if not market_id.startswith("market:"):
        raise HTTPException(status_code=400, detail="invalid market id")
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"invalid category: {category}")
    if payment not in VALID_PAYMENT_FILTERS:
        raise HTTPException(status_code=400, detail=f"invalid payment: {payment}")

    slug = market_id[len("market:"):]
    # slug 안 `-` 는 SQL LIKE 의 `_` 로 (한 문자 매칭). 한글은 그대로.
    like_pattern = slug.replace("-", "_")

    stmt = (
        select(Merchant)
        .options(selectinload(Merchant.reviews), selectinload(Merchant.recent_payments))
        .where(Merchant.is_active.is_(True))
        .where(Merchant.location_precision == "market_level")
        .where(Merchant.market_name.op("LIKE")(like_pattern))
    )
    if category:
        stmt = stmt.where(Merchant.category == category)
    stmt = _apply_payment_filter_merchant(stmt, payment)

    if q:
        q_norm = q.strip()
        products_as_text = cast(Merchant.products, String)
        stmt = stmt.where(
            or_(
                func.lower(Merchant.name).contains(func.lower(q_norm)),
                func.lower(products_as_text).contains(func.lower(q_norm)),
            )
        )

    stmt = stmt.order_by(Merchant.name).offset(offset).limit(limit)
    result = await session.execute(stmt)
    merchants = result.scalars().all()
    return [MerchantOut.model_validate(m) for m in merchants]
