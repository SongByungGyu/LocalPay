"""v1 API router aggregator."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.merchants import router as merchants_router
from app.api.v1.search import router as search_router

router = APIRouter(prefix="/api/v1")
router.include_router(merchants_router)
router.include_router(search_router)
