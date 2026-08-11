"""initial schema: postgis + merchants + reviews + payment verifications

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-11 00:00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure PostGIS is available. Using postgis/postgis image already exposes it,
    # but this is idempotent and makes the migration self-contained.
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "merchants",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "geom",
            sa.dialects.postgresql.ARRAY(sa.Float).with_variant(
                # placeholder swapped below via raw SQL
                sa.String(),
                "postgresql",
            ),
            nullable=True,
        ),  # replaced below
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("road_address", sa.String(length=500), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("supports_onnuri", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("supports_local_currency", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("local_currency_name", sa.String(length=100), nullable=True),
        sa.Column("supported_payment_types", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("products", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("business_hours", JSONB(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("market_name", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False, server_default=sa.text("'seed-anyang-v1'")),
        sa.Column("source_id", sa.String(length=200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Replace placeholder geom column with a proper PostGIS Point(4326).
    op.execute("ALTER TABLE merchants DROP COLUMN IF EXISTS geom")
    op.execute("ALTER TABLE merchants ADD COLUMN geom geometry(Point, 4326) NOT NULL DEFAULT ST_SetSRID(ST_MakePoint(0, 0), 4326)")
    op.execute("ALTER TABLE merchants ALTER COLUMN geom DROP DEFAULT")

    op.create_index("ix_merchants_geom", "merchants", ["geom"], postgresql_using="gist")
    op.create_index("ix_merchants_category", "merchants", ["category"])
    op.create_index(
        "ix_merchants_payment_flags",
        "merchants",
        ["supports_onnuri", "supports_local_currency"],
    )
    op.create_index("ix_merchants_active_category", "merchants", ["is_active", "category"])

    op.create_table(
        "merchant_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", sa.String(length=64), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_name", sa.String(length=64), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payment_type", sa.String(length=32), nullable=False),
        sa.Column("payment_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("purchased_product", sa.String(length=200), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default=sa.text("'seed'")),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
    )
    op.create_index("ix_merchant_reviews_merchant_id", "merchant_reviews", ["merchant_id"])

    op.create_table(
        "merchant_payment_verifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", sa.String(length=64), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payment_type", sa.String(length=32), nullable=False),
        sa.Column("succeeded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(length=200), nullable=True),
    )
    op.create_index(
        "ix_payment_verifications_merchant_time",
        "merchant_payment_verifications",
        ["merchant_id", "succeeded_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_payment_verifications_merchant_time", table_name="merchant_payment_verifications")
    op.drop_table("merchant_payment_verifications")

    op.drop_index("ix_merchant_reviews_merchant_id", table_name="merchant_reviews")
    op.drop_table("merchant_reviews")

    op.drop_index("ix_merchants_active_category", table_name="merchants")
    op.drop_index("ix_merchants_payment_flags", table_name="merchants")
    op.drop_index("ix_merchants_category", table_name="merchants")
    op.drop_index("ix_merchants_geom", table_name="merchants")
    op.drop_table("merchants")

    # Extension left in place; other apps on the same DB may need it. On this
    # dedicated LocalPay DB it is safe to drop, but we opt to keep it.
