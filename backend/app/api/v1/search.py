"""Merchant search endpoint.

MVP 는 PostgreSQL + PostGIS 만으로 이름 · 시장명 · 취급품목 · 카테고리를 검색한다.
Elasticsearch 등 별도 검색 인프라는 도입하지 않는다 (Phase 13 스펙 §10).

- `q` 는 대소문자 무시 부분일치.
- 매장 name/marketName/description 에 매치하면 관련도가 높다고 본다.
- products (JSONB text 배열) 에 매치되어도 결과에 포함된다.
- category 는 raw enum 값 (예: `restaurant`) 또는 한국어 표시명 (예: `음식점`) 둘 다 허용한다.
- lat/lng 가 함께 주어지면 PostGIS 로 거리를 계산해 응답의 `distanceMeters` 에 채우고,
  radius 가 있으면 필터링, 없으면 거리순 정렬만 한다.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from geoalchemy2.types import Geography
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import selectinload

from app.deps import SessionDep
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantOut

router = APIRouter(prefix="/search", tags=["search"])

DEFAULT_LIMIT = 50
MAX_LIMIT = 200
DEFAULT_RADIUS_M = 5000
MAX_RADIUS_M = 30_000

VALID_CATEGORIES = {
    "restaurant", "cafe", "pharmacy", "mart", "market",
    "food", "beauty", "life", "etc",
}
VALID_PAYMENT_FILTERS = {"all", "onnuri", "localCurrency", "both"}

# 한국어 카테고리 표시명 → raw enum. 사용자가 "약국" 이라고 검색해도 pharmacy 로 매핑.
CATEGORY_KO_TO_RAW = {
    "전체": None,
    "음식점": "restaurant",
    "카페": "cafe",
    "약국": "pharmacy",
    "마트": "mart",
    "시장": "market",
    "식품": "food",
    "미용": "beauty",
    "생활": "life",
    "기타": "etc",
}


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


def _load_options():
    return (
        selectinload(Merchant.reviews),
        selectinload(Merchant.recent_payments),
    )


def _to_out(merchant: Merchant, distance_meters: Optional[float] = None) -> MerchantOut:
    dumped = MerchantOut.model_validate(merchant)
    if distance_meters is not None:
        dumped = dumped.model_copy(update={"distance_meters": float(distance_meters)})
    return dumped


@router.get(
    "",
    response_model=List[MerchantOut],
    response_model_by_alias=True,
    summary="가맹점 검색 (이름·시장·상품·카테고리)",
)
async def search_merchants(
    session: SessionDep,
    q: str = Query(..., min_length=1, max_length=100, description="검색어"),
    lat: Optional[float] = Query(default=None, ge=-90, le=90),
    lng: Optional[float] = Query(default=None, ge=-180, le=180),
    radius: Optional[int] = Query(
        default=None,
        ge=1,
        le=MAX_RADIUS_M,
        description="meters. lat/lng 와 함께 주면 반경 필터, 없으면 거리순 정렬만.",
    ),
    category: Optional[str] = Query(default=None),
    payment: str = Query(default="all"),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0, le=10_000),
) -> List[MerchantOut]:
    # lat/lng 는 함께 주거나 함께 생략해야 한다 (둘 중 하나만 오면 오해 방지 차원에서 400).
    if (lat is None) != (lng is None):
        raise HTTPException(status_code=400, detail="lat and lng must be provided together")
    if radius is not None and lat is None:
        raise HTTPException(status_code=400, detail="radius requires lat/lng")

    if payment not in VALID_PAYMENT_FILTERS:
        raise HTTPException(status_code=400, detail=f"invalid payment: {payment}")

    resolved_category: Optional[str] = None
    if category:
        # 한국어 표기 → raw enum. 매칭 실패해도 raw enum 그 자체이면 허용.
        mapped = CATEGORY_KO_TO_RAW.get(category, category)
        if mapped is not None and mapped not in VALID_CATEGORIES:
            raise HTTPException(status_code=400, detail=f"invalid category: {category}")
        resolved_category = mapped

    q_norm = q.strip()
    if not q_norm:
        raise HTTPException(status_code=400, detail="q must not be empty")
    like_pattern = f"%{q_norm}%"

    # products 는 JSONB 이라 SQL 상에서는 텍스트로 캐스팅해 부분일치 검색한다.
    # 대규모 데이터에서는 별도 tsvector · pg_trgm 인덱스 도입이 필요하지만
    # MVP 는 정확성 우선. Phase 13 스펙 §10.
    products_as_text = cast(Merchant.products, String)

    text_match = or_(
        func.lower(Merchant.name).contains(func.lower(q_norm)),
        func.coalesce(func.lower(Merchant.market_name), "").contains(func.lower(q_norm)),
        func.coalesce(func.lower(Merchant.description), "").contains(func.lower(q_norm)),
        func.lower(products_as_text).contains(func.lower(q_norm)),
    )

    stmt = (
        select(Merchant)
        .options(*_load_options())
        .where(Merchant.is_active.is_(True))
        .where(text_match)
    )
    if resolved_category:
        stmt = stmt.where(Merchant.category == resolved_category)
    stmt = _apply_payment_filter(stmt, payment)

    distance_expr = None
    if lat is not None and lng is not None:
        point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
        geom_geog = cast(Merchant.geom, Geography)
        point_geog = cast(point, Geography)
        distance_expr = func.ST_Distance(geom_geog, point_geog).label("distance_meters")

        effective_radius = radius if radius is not None else MAX_RADIUS_M
        stmt = stmt.where(func.ST_DWithin(geom_geog, point_geog, effective_radius))

        stmt = select(Merchant, distance_expr).options(*_load_options()).where(
            Merchant.is_active.is_(True),
            text_match,
            func.ST_DWithin(geom_geog, point_geog, effective_radius),
        )
        if resolved_category:
            stmt = stmt.where(Merchant.category == resolved_category)
        stmt = _apply_payment_filter(stmt, payment)
        # 위치가 있으면 거리순.
        stmt = stmt.order_by("distance_meters")
    else:
        # 위치 없으면 이름 정확 매치 우선, 그 다음 이름 alphabetical.
        stmt = stmt.order_by(
            (func.lower(Merchant.name) == func.lower(q_norm)).desc(),
            Merchant.name,
        )

    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)

    if distance_expr is not None:
        rows = result.all()
        return [_to_out(row[0], distance_meters=row[1]) for row in rows]

    merchants = result.scalars().all()
    return [_to_out(m) for m in merchants]
