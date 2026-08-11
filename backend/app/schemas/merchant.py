"""Response schemas mirroring the iOS Merchant domain model.

Field names use snake_case internally; camelCase JSON aliases are emitted so the
iOS `Codable` layer decodes without any custom `CodingKeys`.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from app.schemas.common import CamelModel


class BusinessHoursOut(CamelModel):
    summary: str
    closed_note: Optional[str] = None


class ReviewOut(CamelModel):
    id: uuid.UUID
    user_name: str
    rating: int
    content: str
    created_at: datetime
    payment_type: str
    payment_verified: bool
    purchased_product: Optional[str] = None


class PaymentVerificationOut(CamelModel):
    id: uuid.UUID
    payment_type: str
    succeeded_at: datetime
    note: Optional[str] = None


class MerchantOut(CamelModel):
    id: str
    name: str
    category: str

    latitude: float
    longitude: float

    address: str
    road_address: Optional[str] = None
    phone: Optional[str] = None

    # Populated by /nearby endpoint; otherwise omitted from JSON via exclusion.
    distance_meters: Optional[float] = None

    supports_onnuri: bool
    supports_local_currency: bool
    local_currency_name: Optional[str] = None
    supported_payment_types: List[str]

    products: List[str]
    business_hours: Optional[BusinessHoursOut] = None
    rating: float
    review_count: int

    market_name: Optional[str] = None
    description: Optional[str] = None
    last_verified_at: Optional[datetime] = None

    reviews: List[ReviewOut] = []
    recent_payments: List[PaymentVerificationOut] = []
