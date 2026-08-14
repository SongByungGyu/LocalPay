"""merchants: add location_source / precision / confidence + backfill dummy seed

Phase 13 Gate 3-B2.

이 migration 은 non-destructive:
  - ADD COLUMN (nullable) → 기존 데이터 손실 없음
  - CHECK constraint 는 NULL 허용 → 기존 25건은 NULL 로 남았다가 backfill 로 채움
  - Dummy 25 (source='seed-anyang-v1') 에 한해 dummy_seed/exact/1.0 backfill
  - 다른 매장 데이터·리뷰·결제 무영향
  - downgrade 는 완전 대칭 (DROP COLUMN CASCADE 없이 CHECK → COLUMN 순)

Revision ID: 0003_add_location_metadata
Revises: 0002_raw_and_source_tables
Create Date: 2026-08-14 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_location_metadata"
down_revision: Union[str, None] = "0002_raw_and_source_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("merchants", sa.Column("location_source", sa.String(length=32), nullable=True))
    op.add_column("merchants", sa.Column("location_precision", sa.String(length=16), nullable=True))
    op.add_column("merchants", sa.Column("location_confidence", sa.Float(), nullable=True))

    # CHECK constraint 는 NULL 은 통과 (SQL 표준). 지정된 enum 값만 허용.
    op.create_check_constraint(
        "ck_merchants_location_source",
        "merchants",
        (
            "location_source IS NULL OR location_source IN ("
            "'source_exact','market_dataset','market_centroid_manual',"
            "'kakao_place','manual','dummy_seed')"
        ),
    )
    op.create_check_constraint(
        "ck_merchants_location_precision",
        "merchants",
        (
            "location_precision IS NULL OR location_precision IN ("
            "'exact','approximate','market_level','region_level')"
        ),
    )
    op.create_check_constraint(
        "ck_merchants_location_confidence",
        "merchants",
        "location_confidence IS NULL OR (location_confidence >= 0.0 AND location_confidence <= 1.0)",
    )

    # Dummy seed 25건 backfill. 다른 source 는 영향 X.
    op.execute(
        """
        UPDATE merchants
           SET location_source = 'dummy_seed',
               location_precision = 'exact',
               location_confidence = 1.0
         WHERE source = 'seed-anyang-v1'
           AND location_source IS NULL
        """
    )


def downgrade() -> None:
    op.drop_constraint("ck_merchants_location_confidence", "merchants", type_="check")
    op.drop_constraint("ck_merchants_location_precision", "merchants", type_="check")
    op.drop_constraint("ck_merchants_location_source", "merchants", type_="check")
    op.drop_column("merchants", "location_confidence")
    op.drop_column("merchants", "location_precision")
    op.drop_column("merchants", "location_source")
