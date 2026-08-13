"""raw_onnuri + raw_local_currency + merchant_sources + data_import_runs + geocode_queue

Phase 13 Gate 3-B0 draft.

⚠️ 이 migration 은 아직 production 에 적용하지 않는다 (스펙 §결정 4).
사용자 승인 후 `docker exec localpay-api alembic upgrade head` 로 적용한다.

Rollback:
- alembic downgrade -1 (아래 downgrade() 는 순서 반대로 완전 drop)
- 각 raw 테이블은 canonical `merchants` 를 참조하지 않도록 설계 (역참조는 merchant_sources 에서만)
- Downgrade 시 raw 데이터 손실. 필요하면 pg_dump 로 백업 후 downgrade.

원본 CSV/API 응답은 raw_payload JSONB 로 보존하므로 Normalize 로직 변경 시 재처리 가능.

Revision ID: 0002_raw_and_source_tables
Revises: 0001_initial
Create Date: 2026-08-13 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0002_raw_and_source_tables"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- 1) data_import_runs — 배치 실행 추적 ----------
    op.create_table(
        "data_import_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(length=64), nullable=False),     # 'onnuri' / 'local_currency' / ...
        sa.Column("status", sa.String(length=32), nullable=False),     # pending/running/succeeded/partial/failed
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("parsed_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("inserted_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("run_metadata", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint(
            "status IN ('pending','running','succeeded','partial','failed')",
            name="ck_import_runs_status",
        ),
    )
    op.create_index("ix_import_runs_source_started", "data_import_runs", ["source", "started_at"])

    # ---------- 2) raw_onnuri_merchants — 온누리 CSV 원본 ----------
    op.create_table(
        "raw_onnuri_merchants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("import_batch_id", UUID(as_uuid=True), sa.ForeignKey("data_import_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_snapshot_date", sa.Date(), nullable=False),  # 예: 2025-07-31
        sa.Column("row_hash", sa.String(length=64), nullable=False),   # dedup 판별용 (7 field sha1)
        sa.Column("merchant_name", sa.String(length=200), nullable=True),
        sa.Column("market_name", sa.String(length=200), nullable=True),
        sa.Column("address_sido", sa.String(length=32), nullable=True),  # 현재 CSV 는 시도만
        sa.Column("products_raw", sa.Text(), nullable=True),
        sa.Column("supports_paper_raw", sa.String(length=16), nullable=True),
        sa.Column("supports_digital_raw", sa.String(length=16), nullable=True),
        sa.Column("registration_year_raw", sa.String(length=16), nullable=True),
        sa.Column("raw_payload", JSONB(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_raw_onnuri_snapshot", "raw_onnuri_merchants", ["source_snapshot_date"])
    op.create_index("ix_raw_onnuri_market", "raw_onnuri_merchants", ["market_name"])
    op.create_index("ix_raw_onnuri_hash", "raw_onnuri_merchants", ["row_hash"])
    # 같은 snapshot 안에서 동일 row (7 field 동일) 재삽입 방지.
    op.create_unique_constraint(
        "uq_raw_onnuri_snapshot_hash",
        "raw_onnuri_merchants",
        ["source_snapshot_date", "row_hash"],
    )

    # ---------- 3) raw_local_currency_merchants — KOMSCO API 원본 (Gate 2 재개 대비) ----------
    op.create_table(
        "raw_local_currency_merchants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("import_batch_id", UUID(as_uuid=True), sa.ForeignKey("data_import_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_provider", sa.String(length=64), nullable=False),  # 'komsco-integrated' 등
        sa.Column("source_merchant_id", sa.String(length=200), nullable=True),  # 예: brno
        sa.Column("merchant_name", sa.String(length=200), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("road_address", sa.String(length=500), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("business_status", sa.String(length=64), nullable=True),
        sa.Column("industry_code", sa.String(length=32), nullable=True),
        sa.Column("region_code", sa.String(length=32), nullable=True),
        sa.Column("raw_payload", JSONB(), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_raw_lc_region", "raw_local_currency_merchants", ["region_code"])
    op.create_index("ix_raw_lc_provider_srcid", "raw_local_currency_merchants", ["source_provider", "source_merchant_id"])
    op.create_unique_constraint(
        "uq_raw_lc_provider_srcid",
        "raw_local_currency_merchants",
        ["source_provider", "source_merchant_id"],
    )

    # ---------- 4) merchant_sources — canonical ↔ raw 매핑 ----------
    # canonical merchants.id 는 Gate 4 이후에 생성. 지금은 nullable 로 두고 raw 만 pointer 로 둔다.
    op.create_table(
        "merchant_sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", sa.String(length=64), sa.ForeignKey("merchants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),      # 'onnuri' / 'local_currency' / 'dummy'
        sa.Column("source_provider", sa.String(length=64), nullable=True),
        sa.Column("raw_id", UUID(as_uuid=True), nullable=True),              # raw_*_merchants.id 참조 (soft)
        sa.Column("confidence", sa.String(length=16), nullable=False),       # exact/high/medium/low
        sa.Column("matched_by", sa.String(length=200), nullable=True),       # e.g. "name+address+phone"
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "confidence IN ('exact','high','medium','low')",
            name="ck_merchant_sources_confidence",
        ),
    )
    op.create_index("ix_merchant_sources_merchant", "merchant_sources", ["merchant_id"])
    op.create_index("ix_merchant_sources_type_raw", "merchant_sources", ["source_type", "raw_id"])

    # ---------- 5) geocode_queue — 좌표 없는 raw 매장 처리 대기 ----------
    op.create_table(
        "geocode_queue",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),      # 'onnuri' / 'local_currency'
        sa.Column("raw_id", UUID(as_uuid=True), nullable=False),
        sa.Column("query_hint", sa.Text(), nullable=True),                   # merchantName + marketName + '안양' 등
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'pending'")),
        # pending → resolved_high / resolved_medium / ambiguous / failed
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("resolved_lat", sa.Float(), nullable=True),
        sa.Column("resolved_lng", sa.Float(), nullable=True),
        sa.Column("resolved_provider", sa.String(length=64), nullable=True),  # 'kakao-keyword' 등
        sa.Column("resolved_confidence_score", sa.Float(), nullable=True),   # 0.0 ~ 1.0
        sa.Column("resolved_payload", JSONB(), nullable=True),                # Kakao 응답 원본
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), onupdate=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('pending','resolved_high','resolved_medium','ambiguous','failed')",
            name="ck_geocode_status",
        ),
    )
    op.create_index("ix_geocode_queue_status", "geocode_queue", ["status"])
    op.create_index("ix_geocode_queue_source_raw", "geocode_queue", ["source_type", "raw_id"])
    op.create_unique_constraint(
        "uq_geocode_queue_source_raw",
        "geocode_queue",
        ["source_type", "raw_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_geocode_queue_source_raw", "geocode_queue", type_="unique")
    op.drop_index("ix_geocode_queue_source_raw", table_name="geocode_queue")
    op.drop_index("ix_geocode_queue_status", table_name="geocode_queue")
    op.drop_table("geocode_queue")

    op.drop_index("ix_merchant_sources_type_raw", table_name="merchant_sources")
    op.drop_index("ix_merchant_sources_merchant", table_name="merchant_sources")
    op.drop_table("merchant_sources")

    op.drop_constraint("uq_raw_lc_provider_srcid", "raw_local_currency_merchants", type_="unique")
    op.drop_index("ix_raw_lc_provider_srcid", table_name="raw_local_currency_merchants")
    op.drop_index("ix_raw_lc_region", table_name="raw_local_currency_merchants")
    op.drop_table("raw_local_currency_merchants")

    op.drop_constraint("uq_raw_onnuri_snapshot_hash", "raw_onnuri_merchants", type_="unique")
    op.drop_index("ix_raw_onnuri_hash", table_name="raw_onnuri_merchants")
    op.drop_index("ix_raw_onnuri_market", table_name="raw_onnuri_merchants")
    op.drop_index("ix_raw_onnuri_snapshot", table_name="raw_onnuri_merchants")
    op.drop_table("raw_onnuri_merchants")

    op.drop_index("ix_import_runs_source_started", table_name="data_import_runs")
    op.drop_table("data_import_runs")
