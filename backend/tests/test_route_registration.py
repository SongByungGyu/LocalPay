"""Route registration smoke tests.

conftest.py 의 client fixture 는 DB 를 붙이지 않아 실제 DB 를 치는 endpoint
전체를 실행하지는 못하지만, 라우터가 정상 마운트되었는지·validation 이
DB 접근 전에 400 을 반환하는지는 확인할 수 있다.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_map_endpoint_registered_and_validates_bbox_order(client: AsyncClient) -> None:
    # north <= south → DB 접근 전 400
    r = await client.get(
        "/api/v1/merchants/map",
        params={"north": 37.0, "south": 37.5, "east": 127.5, "west": 127.0},
    )
    assert r.status_code == 400
    assert "north" in r.json()["detail"]


@pytest.mark.asyncio
async def test_map_endpoint_rejects_too_large_bbox(client: AsyncClient) -> None:
    # 전세계 zoom-out 방어 (MAX_BBOX_DEGREES = 6.0)
    r = await client.get(
        "/api/v1/merchants/map",
        params={"north": 60.0, "south": 0.0, "east": 130.0, "west": 120.0},
    )
    assert r.status_code == 400
    assert "bbox too large" in r.json()["detail"]


@pytest.mark.asyncio
async def test_search_endpoint_registered_and_requires_q(client: AsyncClient) -> None:
    # q 는 필수 (min_length=1). 누락 시 FastAPI 가 422 반환.
    r = await client.get("/api/v1/search")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_search_rejects_lat_without_lng(client: AsyncClient) -> None:
    r = await client.get("/api/v1/search", params={"q": "삼겹살", "lat": 37.39})
    assert r.status_code == 400
    assert "lat and lng" in r.json()["detail"]


@pytest.mark.asyncio
async def test_search_rejects_radius_without_location(client: AsyncClient) -> None:
    r = await client.get("/api/v1/search", params={"q": "삼겹살", "radius": 3000})
    assert r.status_code == 400
    assert "radius requires lat/lng" in r.json()["detail"]


@pytest.mark.asyncio
async def test_search_rejects_invalid_payment(client: AsyncClient) -> None:
    r = await client.get("/api/v1/search", params={"q": "삼겹살", "payment": "wat"})
    assert r.status_code == 400
    assert "invalid payment" in r.json()["detail"]


@pytest.mark.asyncio
async def test_search_rejects_invalid_category(client: AsyncClient) -> None:
    r = await client.get("/api/v1/search", params={"q": "삼겹살", "category": "not-a-category"})
    assert r.status_code == 400
    assert "invalid category" in r.json()["detail"]


@pytest.mark.asyncio
async def test_openapi_lists_new_endpoint(client: AsyncClient) -> None:
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/api/v1/search" in paths
    assert "/api/v1/merchants/map" in paths
