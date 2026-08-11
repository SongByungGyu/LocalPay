"""Pytest fixtures.

Note: These tests exercise the FastAPI app in-process and DO NOT touch the
database. Tests that require the DB should skip when DATABASE_URL is unset.
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
