"""raw_onnuri_merchants → canonical merchants INSERT + merchant_sources 연결.

Idempotency (Gate 3-C 스펙 §5):
  - Canonical id 는 stable (`onnuri-a-{row_hash[:16]}`) → 재실행 시 ON CONFLICT DO NOTHING.
  - merchant_sources 는 (merchant_id, raw_id) 조합 unique → 재실행 무한 증가 없음.
  - postgres CHECK constraint 를 위반하지 않도록 location metadata 세팅.

Non-destructive:
  - Dummy 25 (source='seed-anyang-v1') 및 다른 canonical row 무변경.
  - reviews, payment_verifications 무영향.
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional

try:
    import asyncpg  # type: ignore
except ImportError:  # pragma: no cover
    asyncpg = None

from worker.importers.onnuri.canonical import CanonicalMerchantCandidate, to_canonical
from worker.importers.onnuri.models import RawOnnuriRecord
from worker.importers.onnuri.normalizer import normalize
from worker.importers.onnuri.writer import _normalize_dsn


@dataclass
class CanonicalWriteReport:
    snapshot_date: str
    raw_rows_scanned: int
    candidates_generated: int
    inserted: int
    existing_skipped: int
    invalid: int
    source_links_created: int
    error_count: int

    categories: Dict[str, int] = field(default_factory=dict)
    payment_counts: Dict[str, int] = field(default_factory=dict)   # paper/digital/both/neither
    market_counts: Dict[str, int] = field(default_factory=dict)    # market_name → count

    def as_text(self) -> str:
        L: List[str] = []
        L.append(f"[CanonicalWrite] snapshot={self.snapshot_date}")
        L.append(f"  raw_rows              = {self.raw_rows_scanned}")
        L.append(f"  candidates            = {self.candidates_generated}")
        L.append(f"  inserted              = {self.inserted}")
        L.append(f"  existing skipped      = {self.existing_skipped}")
        L.append(f"  invalid               = {self.invalid}")
        L.append(f"  source_links created  = {self.source_links_created}")
        L.append(f"  errors                = {self.error_count}")
        L.append("")
        L.append("[categories]")
        for k, v in sorted(self.categories.items(), key=lambda x: -x[1]):
            L.append(f"  {k:<12} = {v}")
        L.append("[payments]")
        for k, v in self.payment_counts.items():
            L.append(f"  {k} = {v}")
        L.append(f"[markets]  {len(self.market_counts)} 개 그룹, 상위 5")
        for k, v in sorted(self.market_counts.items(), key=lambda x: -x[1])[:5]:
            L.append(f"  {k}: {v}")
        return "\n".join(L)


# ---------- data load from DB ----------

async def _load_raw_records(conn, snapshot_date: date) -> List[tuple[uuid.UUID, str, RawOnnuriRecord]]:
    """raw_onnuri_merchants 에서 스냅샷 필터로 read."""
    rows = await conn.fetch(
        """
        SELECT id, row_hash, merchant_name, market_name, address_sido,
               products_raw, supports_paper_raw, supports_digital_raw,
               registration_year_raw, raw_payload
        FROM raw_onnuri_merchants
        WHERE source_snapshot_date = $1
        """,
        snapshot_date,
    )
    out: List[tuple[uuid.UUID, str, RawOnnuriRecord]] = []
    for row in rows:
        payload_raw = row["raw_payload"]
        if isinstance(payload_raw, str):
            try:
                payload = json.loads(payload_raw)
            except Exception:  # noqa: BLE001
                payload = {}
        else:
            payload = payload_raw or {}
        raw = RawOnnuriRecord(
            merchant_name=row["merchant_name"],
            market_name=row["market_name"],
            address=row["address_sido"],
            products_raw=row["products_raw"],
            supports_paper_raw=row["supports_paper_raw"],
            supports_digital_raw=row["supports_digital_raw"],
            registration_year_raw=row["registration_year_raw"],
            raw_payload=payload,
        )
        out.append((row["id"], row["row_hash"], raw))
    return out


# ---------- write pipeline ----------

async def _run_write_async(
    *,
    dsn: str,
    snapshot_date: date,
    dry_run: bool,
) -> CanonicalWriteReport:
    if asyncpg is None:
        raise RuntimeError("asyncpg not installed (컨테이너 안에서 실행)")
    conn = await asyncpg.connect(_normalize_dsn(dsn))
    try:
        raw_rows = await _load_raw_records(conn, snapshot_date)

        candidates: List[tuple[uuid.UUID, CanonicalMerchantCandidate]] = []
        invalid = 0
        cat_counter: Dict[str, int] = {}
        pay_counter: Dict[str, int] = {"paper": 0, "digital": 0, "both": 0, "neither": 0}
        market_counter: Dict[str, int] = {}

        for raw_id, row_hash, raw in raw_rows:
            n = normalize(raw)
            if n is None:
                invalid += 1
                continue
            c = to_canonical(n, row_hash=row_hash, snapshot_date=snapshot_date.isoformat())
            candidates.append((raw_id, c))
            cat_counter[c.category] = cat_counter.get(c.category, 0) + 1
            key = "%s_%s" % (
                "P" if "onnuriPaper" in c.supported_payment_types else "-",
                "D" if "onnuriDigital" in c.supported_payment_types else "-",
            )
            if key == "P_D":
                pay_counter["both"] += 1
                pay_counter["paper"] += 1
                pay_counter["digital"] += 1
            elif key == "P_-":
                pay_counter["paper"] += 1
            elif key == "-_D":
                pay_counter["digital"] += 1
            else:
                pay_counter["neither"] += 1
            mk = c.market_name or "(no market)"
            market_counter[mk] = market_counter.get(mk, 0) + 1

        inserted = 0
        existing_skipped = 0
        source_links = 0
        errors = 0

        if dry_run:
            # dry run: 실 INSERT 안 함, 기존 canonical merchants 중 candidate id 와 겹치는 것만 count.
            ids = [c.id for _, c in candidates]
            if ids:
                exists = await conn.fetch(
                    "SELECT id FROM merchants WHERE id = ANY($1::text[])",
                    ids,
                )
                existing_skipped = len(exists)
        else:
            first_error_reported = False
            async with conn.transaction():
                for raw_id, c in candidates:
                    try:
                        # 각 INSERT 를 savepoint 로 감싸 개별 실패 격리
                        # (postgres 는 트랜잭션 안 에러 후 후속 명령 전부 무시).
                        async with conn.transaction():
                            result = await conn.execute(
                                """
                                INSERT INTO merchants (
                                    id, name, category,
                                    latitude, longitude, geom,
                                    address, road_address, phone,
                                    supports_onnuri, supports_local_currency, local_currency_name,
                                    supported_payment_types, products, business_hours,
                                    rating, review_count,
                                    market_name, description, last_verified_at,
                                    source, source_id, is_active,
                                    created_at, updated_at,
                                    location_source, location_precision, location_confidence
                                ) VALUES (
                                    $1, $2, $3,
                                    $4, $5,
                                    CASE WHEN $4::float IS NULL OR $5::float IS NULL THEN NULL
                                         ELSE ST_SetSRID(ST_MakePoint($5::float, $4::float), 4326)
                                    END,
                                    $6, $7, $8,
                                    $9, $10, $11,
                                    $12::jsonb, $13::jsonb, $14::jsonb,
                                    $15, $16,
                                    $17, $18, $19,
                                    $20, $21, $22,
                                    now(), now(),
                                    $23, $24, $25
                                )
                                ON CONFLICT (id) DO NOTHING
                                """,
                                c.id, c.name, c.category,
                                c.latitude, c.longitude,
                                c.address, c.road_address, c.phone,
                                c.supports_onnuri, c.supports_local_currency, c.local_currency_name,
                                json.dumps(c.supported_payment_types),
                                json.dumps(c.products),
                                json.dumps(c.business_hours) if c.business_hours else None,
                                c.rating, c.review_count,
                                c.market_name, c.description, None,
                                c.source, c.source_id, c.is_active,
                                c.location_source, c.location_precision, c.location_confidence,
                            )
                            if result.endswith(" 1"):
                                inserted += 1
                            else:
                                existing_skipped += 1

                            # merchant_sources link (idempotent).
                            link_result = await conn.execute(
                                """
                                INSERT INTO merchant_sources (
                                    id, merchant_id, source_type, source_provider, raw_id,
                                    confidence, matched_by
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                                """,
                                uuid.uuid4(), c.id, "onnuri", "komsco-snapshot", raw_id,
                                "exact", "raw_hash",
                            )
                            if link_result.endswith(" 1"):
                                source_links += 1
                    except Exception as e:  # noqa: BLE001
                        errors += 1
                        if not first_error_reported:
                            import sys
                            print(f"[write error sample] id={c.id} {type(e).__name__}: {e}", file=sys.stderr)
                            first_error_reported = True

                # merchant_sources 는 unique 없음 → 재실행 중복 방지 위해 별도 정리 필요.
                # 여기서는 (merchant_id, raw_id) 중복이 있으면 최신 1개만 남기고 삭제
                # (이번 세션은 첫 INSERT 라 문제 없지만, 재실행 대비).
                await conn.execute(
                    """
                    DELETE FROM merchant_sources
                     WHERE id IN (
                        SELECT id FROM (
                          SELECT id,
                                 row_number() OVER (
                                    PARTITION BY merchant_id, raw_id
                                    ORDER BY created_at DESC
                                 ) AS rn
                            FROM merchant_sources
                           WHERE source_type = 'onnuri'
                        ) t
                        WHERE t.rn > 1
                     )
                    """
                )
    finally:
        await conn.close()

    return CanonicalWriteReport(
        snapshot_date=snapshot_date.isoformat(),
        raw_rows_scanned=len(raw_rows),
        candidates_generated=len(candidates),
        inserted=inserted,
        existing_skipped=existing_skipped,
        invalid=invalid,
        source_links_created=source_links,
        error_count=errors,
        categories=cat_counter,
        payment_counts=pay_counter,
        market_counts=market_counter,
    )


def run_write_sync(
    *,
    snapshot_date: date,
    dry_run: bool = True,
    database_url: Optional[str] = None,
) -> CanonicalWriteReport:
    dsn = database_url or os.environ.get("DATABASE_URL") or ""
    if not dsn:
        raise RuntimeError("DATABASE_URL 필요")
    return asyncio.run(_run_write_async(
        dsn=dsn, snapshot_date=snapshot_date, dry_run=dry_run,
    ))
