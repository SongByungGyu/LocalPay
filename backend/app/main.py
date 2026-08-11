"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    # Swagger disabled in production per Phase 10 spec.
    docs_url = "/docs" if not settings.is_production else None
    redoc_url = "/redoc" if not settings.is_production else None
    openapi_url = "/openapi.json" if not settings.is_production else None

    app = FastAPI(
        title="LocalPay Backend",
        description="온누리상품권 · 지역화폐 사용처 지도 서비스 백엔드 API",
        version=settings.version,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    origins = settings.cors_origin_list
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=False,
            allow_methods=["GET"],
            allow_headers=["*"],
        )

    app.include_router(health_router)
    app.include_router(v1_router)

    return app


app = create_app()
