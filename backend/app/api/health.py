"""Liveness + DB connectivity endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.deps import SessionDep

router = APIRouter(tags=["health"])
_settings = get_settings()


@router.get("/health", summary="Liveness probe")
async def health() -> dict:
    return {
        "status": "ok",
        "service": _settings.service_name,
        "version": _settings.version,
    }


@router.get("/db-health", summary="Postgres + PostGIS connectivity check")
async def db_health(session: SessionDep) -> dict:
    # Postgres round-trip
    await session.execute(text("SELECT 1"))
    # PostGIS extension version
    row = (await session.execute(text("SELECT PostGIS_Lib_Version()"))).first()
    postgis_version = row[0] if row else "unknown"
    return {
        "status": "ok",
        "postgres": "ok",
        "postgis": postgis_version,
    }
