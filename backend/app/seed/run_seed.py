"""Reset & seed the merchants tables from the ported iOS Dummy data.

Usage (inside the container):
    python -m app.seed.run_seed

Behaviour:
    - Deletes every row in merchants, merchant_reviews, merchant_payment_verifications
      (reviews / payments are removed automatically via ON DELETE CASCADE).
    - Re-inserts all 25 seed merchants with fresh timestamps.
    - Sets the PostGIS point via ST_SetSRID(ST_MakePoint(lng, lat), 4326).
"""
from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import delete, func, select

from app.database import AsyncSessionLocal
from app.models.merchant import (
    Merchant,
    MerchantPaymentVerification,
    MerchantReview,
)
from app.seed.seed_data import build_seed_merchants


async def reset_and_seed() -> tuple[int, int, int]:
    seed_rows = build_seed_merchants()

    async with AsyncSessionLocal() as session:
        # Wipe existing seed. CASCADE will clean children.
        await session.execute(delete(Merchant))
        await session.flush()

        for row in seed_rows:
            m = Merchant(
                id=row["id"],
                name=row["name"],
                category=row["category"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                geom=func.ST_SetSRID(
                    func.ST_MakePoint(row["longitude"], row["latitude"]),
                    4326,
                ),
                address=row["address"],
                road_address=row.get("road_address"),
                phone=row.get("phone"),
                supports_onnuri=row["supports_onnuri"],
                supports_local_currency=row["supports_local_currency"],
                local_currency_name=row.get("local_currency_name"),
                supported_payment_types=row["supported_payment_types"],
                products=row["products"],
                business_hours=row.get("business_hours"),
                rating=row["rating"],
                review_count=row["review_count"],
                market_name=row.get("market_name"),
                description=row.get("description"),
                last_verified_at=row.get("last_verified_at"),
                source="seed-anyang-v1",
                is_active=True,
                # Phase 13 Gate 3-B2 — Dummy seed 는 exact 좌표로 취급 (수동 확인된 값).
                # docs/LOCATION_PRECISION.md 소스별 기본값 매핑.
                location_source="dummy_seed",
                location_precision="exact",
                location_confidence=1.0,
            )
            session.add(m)

            for r in row.get("reviews", []):
                session.add(
                    MerchantReview(
                        id=uuid.uuid4(),
                        merchant_id=row["id"],
                        user_name=r["user_name"],
                        rating=r["rating"],
                        content=r["content"],
                        created_at=r["created_at"],
                        payment_type=r["payment_type"],
                        payment_verified=r["payment_verified"],
                        purchased_product=r.get("purchased_product"),
                        source="seed",
                    )
                )

            for p in row.get("recent_payments", []):
                session.add(
                    MerchantPaymentVerification(
                        id=uuid.uuid4(),
                        merchant_id=row["id"],
                        payment_type=p["payment_type"],
                        succeeded_at=p["succeeded_at"],
                        note=p.get("note"),
                    )
                )

        await session.commit()

        # Return counts for logging.
        merchants = (await session.execute(select(func.count(Merchant.id)))).scalar_one()
        reviews = (await session.execute(select(func.count(MerchantReview.id)))).scalar_one()
        payments = (
            await session.execute(select(func.count(MerchantPaymentVerification.id)))
        ).scalar_one()
        return int(merchants), int(reviews), int(payments)


async def main() -> None:
    merchants, reviews, payments = await reset_and_seed()
    print(
        f"[seed] done: merchants={merchants} reviews={reviews} recent_payments={payments}"
    )


if __name__ == "__main__":
    asyncio.run(main())
