"""Merchant read endpoints.

Response contract mirrors the iOS `Merchant` domain model. All list endpoints
return raw JSON arrays (no envelope) so `JSONDecoder.decode([Merchant].self, …)`
works directly.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from geoalchemy2.types import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.orm import selectinload

from app.deps import SessionDep
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantOut

router = APIRouter(prefix="/merchants", tags=["merchants"])

VALID_CATEGORIES = {
    "restaurant", "cafe", "pharmacy", "mart", "market",
    "food", "beauty", "life", "etc",
}
VALID_PAYMENT_FILTERS = {"all", "onnuri", "localCurrency", "both"}

DEFAULT_LIMIT = 500
MAX_LIMIT = 1000
DEFAULT_NEARBY_RADIUS_M = 3000
MAX_NEARBY_RADIUS_M = 30_000

# 지도 BBOX 상한 (도 단위, WGS84).
# 대략 남한 전체가 위도 ~4°, 경도 ~5° 안에 들어간다. 사용자가 전세계 zoom-out 상태로
# 요청해 수십만 건을 한꺼번에 반환하는 상황을 방지한다. 초과 시 400.
MAX_BBOX_DEGREES = 6.0


def _load_options():
    """Ensure related rows are batch-loaded, not lazy per row."""
    return (
        selectinload(Merchant.reviews),
        selectinload(Merchant.recent_payments),
    )


def _apply_payment_filter(stmt, payment: str):
    if payment == "onnuri":
        return stmt.where(Merchant.supports_onnuri.is_(True))
    if payment == "localCurrency":
        return stmt.where(Merchant.supports_local_currency.is_(True))
    if payment == "both":
        return stmt.where(
            Merchant.supports_onnuri.is_(True),
            Merchant.supports_local_currency.is_(True),
        )
    return stmt  # "all"


def _to_out(merchant: Merchant, distance_meters: Optional[float] = None) -> MerchantOut:
    dumped = MerchantOut.model_validate(merchant)
    if distance_meters is not None:
        dumped = dumped.model_copy(update={"distance_meters": float(distance_meters)})
    return dumped


@router.get(
    "",
    response_model=List[MerchantOut],
    response_model_by_alias=True,
    summary="가맹점 목록",
)
async def list_merchants(
    session: SessionDep,
    category: Optional[str] = Query(default=None, description="MerchantCategory raw"),
    payment: str = Query(default="all", description="all|onnuri|localCurrency|both"),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> List[MerchantOut]:
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"invalid category: {category}")
    if payment not in VALID_PAYMENT_FILTERS:
        raise HTTPException(status_code=400, detail=f"invalid payment: {payment}")

    stmt = (
        select(Merchant)
        .options(*_load_options())
        .where(Merchant.is_active.is_(True))
    )
    if category:
        stmt = stmt.where(Merchant.category == category)
    stmt = _apply_payment_filter(stmt, payment)
    stmt = stmt.order_by(Merchant.name).limit(limit)

    result = await session.execute(stmt)
    merchants = result.scalars().all()
    return [_to_out(m) for m in merchants]


@router.get(
    "/nearby",
    response_model=List[MerchantOut],
    response_model_by_alias=True,
    summary="주변 가맹점 (PostGIS ST_DWithin)",
)
async def nearby_merchants(
    session: SessionDep,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: int = Query(
        default=DEFAULT_NEARBY_RADIUS_M,
        ge=1,
        le=MAX_NEARBY_RADIUS_M,
        description="meters",
    ),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    category: Optional[str] = Query(default=None),
    payment: str = Query(default="all"),
) -> List[MerchantOut]:
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"invalid category: {category}")
    if payment not in VALID_PAYMENT_FILTERS:
        raise HTTPException(status_code=400, detail=f"invalid payment: {payment}")

    point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
    geom_geog = cast(Merchant.geom, Geography)
    point_geog = cast(point, Geography)

    distance_expr = func.ST_Distance(geom_geog, point_geog).label("distance_meters")

    stmt = (
        select(Merchant, distance_expr)
        .options(*_load_options())
        .where(Merchant.is_active.is_(True))
        .where(func.ST_DWithin(geom_geog, point_geog, radius))
    )
    if category:
        stmt = stmt.where(Merchant.category == category)
    stmt = _apply_payment_filter(stmt, payment)
    stmt = stmt.order_by("distance_meters").limit(limit)

    result = await session.execute(stmt)
    rows = result.all()
    return [_to_out(row[0], distance_meters=row[1]) for row in rows]


@router.get(
    "/map",
    response_model=List[MerchantOut],
    response_model_by_alias=True,
    summary="지도 영역(BBOX) 검색 (PostGIS ST_Intersects)",
)
async def map_merchants(
    session: SessionDep,
    north: float = Query(..., ge=-90, le=90),
    south: float = Query(..., ge=-90, le=90),
    east: float = Query(..., ge=-180, le=180),
    west: float = Query(..., ge=-180, le=180),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    category: Optional[str] = Query(default=None),
    payment: str = Query(default="all"),
) -> List[MerchantOut]:
    if north <= south:
        raise HTTPException(status_code=400, detail="north must be greater than south")
    if east <= west:
        raise HTTPException(status_code=400, detail="east must be greater than west")
    # 지구 전체나 대륙 단위 zoom-out 요청 방지. 남한 전체보다 큰 BBOX 는 거부.
    if (north - south) > MAX_BBOX_DEGREES or (east - west) > MAX_BBOX_DEGREES:
        raise HTTPException(
            status_code=400,
            detail=f"bbox too large (max {MAX_BBOX_DEGREES}°)",
        )
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"invalid category: {category}")
    if payment not in VALID_PAYMENT_FILTERS:
        raise HTTPException(status_code=400, detail=f"invalid payment: {payment}")

    envelope = func.ST_MakeEnvelope(west, south, east, north, 4326)

    stmt = (
        select(Merchant)
        .options(*_load_options())
        .where(Merchant.is_active.is_(True))
        .where(func.ST_Intersects(Merchant.geom, envelope))
    )
    if category:
        stmt = stmt.where(Merchant.category == category)
    stmt = _apply_payment_filter(stmt, payment)
    stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    merchants = result.scalars().all()
    return [_to_out(m) for m in merchants]


@router.get(
    "/{merchant_id}",
    response_model=MerchantOut,
    response_model_by_alias=True,
    summary="가맹점 상세",
)
async def merchant_detail(session: SessionDep, merchant_id: str) -> MerchantOut:
    stmt = (
        select(Merchant)
        .options(*_load_options())
        .where(Merchant.id == merchant_id)
        .where(Merchant.is_active.is_(True))
    )
    result = await session.execute(stmt)
    merchant = result.scalar_one_or_none()
    if merchant is None:
        raise HTTPException(status_code=404, detail="merchant not found")
    return _to_out(merchant)
