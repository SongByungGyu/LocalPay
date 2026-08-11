"""Merchant / Review / PaymentVerification ORM models.

Field names match the iOS Merchant domain model as closely as possible so that
future `RemoteMerchantRepository` can decode responses without custom keys.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    # PostGIS point (WGS84). Populated at insert/update time from lat/lng.
    geom = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=False,
    )

    address: Mapped[str] = mapped_column(String(500), nullable=False)
    road_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    supports_onnuri: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    supports_local_currency: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    local_currency_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Array of PaymentType.rawValue strings (e.g. ["onnuriDigital","localCurrency"])
    supported_payment_types: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )
    # Array of product name strings.
    products: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # {"summary": "...", "closedNote": "..."} or None
    business_hours: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    market_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    source: Mapped[str] = mapped_column(String(64), nullable=False, default="seed-anyang-v1")
    source_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    reviews: Mapped[List["MerchantReview"]] = relationship(
        back_populates="merchant",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    recent_payments: Mapped[List["MerchantPaymentVerification"]] = relationship(
        back_populates="merchant",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(MerchantPaymentVerification.succeeded_at)",
    )

    __table_args__ = (
        Index("ix_merchants_geom", "geom", postgresql_using="gist"),
        Index("ix_merchants_payment_flags", "supports_onnuri", "supports_local_currency"),
        Index("ix_merchants_active_category", "is_active", "category"),
    )


class MerchantReview(Base):
    __tablename__ = "merchant_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_name: Mapped[str] = mapped_column(String(64), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    payment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    purchased_product: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="seed")

    merchant: Mapped[Merchant] = relationship(back_populates="reviews")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
    )


class MerchantPaymentVerification(Base):
    __tablename__ = "merchant_payment_verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    succeeded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    note: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    merchant: Mapped[Merchant] = relationship(back_populates="recent_payments")

    __table_args__ = (
        Index(
            "ix_payment_verifications_merchant_time",
            "merchant_id",
            "succeeded_at",
        ),
    )
