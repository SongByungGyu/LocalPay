"""Application settings sourced from environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+asyncpg://localpay:localpay@db:5432/localpay",
        description="Async SQLAlchemy DSN (asyncpg driver required).",
    )

    env: str = Field(default="production")
    log_level: str = Field(default="info")

    # Comma-separated list of allowed CORS origins. Empty = no cross-origin.
    cors_origins: str = Field(default="")

    service_name: str = "localpay-backend"
    version: str = "0.1.0"

    @property
    def cors_origin_list(self) -> List[str]:
        raw = (self.cors_origins or "").strip()
        if not raw:
            return []
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
