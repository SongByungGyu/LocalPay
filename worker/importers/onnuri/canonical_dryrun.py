"""Canonical candidate dry-run (Gate 3-B2).

두 입력 방식 모두 지원:
  1. CSV 파일 → parse → normalize → canonical (파일 있으면 사용)
  2. DB raw_onnuri_merchants → normalize → canonical (DB write 없음, 순수 read)

Gate 3-B2 는 canonical merchants 에 실제 INSERT 하지 않는다.
결과는 통계 · market aggregation 만 리포트.
"""
from __future__ import annotations

import asyncio
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from worker.importers.onnuri.canonical import (
    LOC_SOURCE_MARKET_CENTROID,
    LOC_SOURCE_MARKET_DATASET,
    CanonicalMerchantCandidate,
    to_canonical,
)
from worker.importers.onnuri.normalizer import normalize
from worker.importers.onnuri.parser import iter_records
from worker.importers.onnuri.writer import _row_hash


@dataclass
class MarketAggregate:
    market_name: str
    centroid_lat: Optional[float]
    centroid_lng: Optional[float]
    location_source: Optional[str]
    location_confidence: Optional[float]
    merchant_count: int
    supports_paper: int
    supports_digital: int
    supports_both: int
    category_counts: Dict[str, int] = field(default_factory=dict)
    sample_merchants: List[str] = field(default_factory=list)


@dataclass
class CanonicalDryRunReport:
    input_source: str        # "csv:<path>" or "db:raw_onnuri_merchants"
    snapshot_date: str
    region_filter: str

    total_input_rows: int
    normalized_ok: int
    normalized_dropped: int
    canonical_generated: int

    location_source_counts: Dict[str, int] = field(default_factory=dict)
    location_precision_counts: Dict[str, int] = field(default_factory=dict)

    category_counts: Dict[str, int] = field(default_factory=dict)

    coordinate_valid: int = 0
    coordinate_missing: int = 0

    # 시장별 집계.
    market_aggregates: List[MarketAggregate] = field(default_factory=list)

    # 정확 좌표 없이 지도 노출 불가한 매장 수.
    unmappable_to_map: int = 0

    # sample candidates (앞 10건).
    sample: List[Dict[str, Any]] = field(default_factory=list)

    def as_text(self) -> str:
        L: List[str] = []
        L.append(f"[CanonicalDryRun] input={self.input_source} snapshot={self.snapshot_date} region={self.region_filter}")
        L.append(f"  total_input_rows      = {self.total_input_rows}")
        L.append(f"  normalized_ok         = {self.normalized_ok}")
        L.append(f"  normalized_dropped    = {self.normalized_dropped}")
        L.append(f"  canonical_generated   = {self.canonical_generated}")
        L.append(f"  unmappable_to_map     = {self.unmappable_to_map}")
        L.append("")
        L.append("[Coordinate]")
        L.append(f"  valid   = {self.coordinate_valid}")
        L.append(f"  missing = {self.coordinate_missing}")
        L.append("")
        L.append("[Location source 분포]")
        for k, v in sorted(self.location_source_counts.items(), key=lambda x: -x[1]):
            L.append(f"  {k or '(none)':<25} = {v}")
        L.append("[Location precision 분포]")
        for k, v in sorted(self.location_precision_counts.items(), key=lambda x: -x[1]):
            L.append(f"  {k or '(none)':<25} = {v}")
        L.append("")
        L.append("[Category 분포]")
        for k, v in sorted(self.category_counts.items(), key=lambda x: -x[1]):
            L.append(f"  {k:<12} = {v}")
        L.append("")
        L.append("[Market Aggregation Preview]  (/api/v1/markets/map 후보)")
        L.append(f"  총 {len(self.market_aggregates)} 시장/상점가")
        for m in self.market_aggregates:
            L.append(
                f"  - {m.market_name}"
                f"  count={m.merchant_count}"
                f"  paper={m.supports_paper}  digital={m.supports_digital}  both={m.supports_both}"
                f"  ({m.centroid_lat}, {m.centroid_lng})"
                f"  src={m.location_source}  conf={m.location_confidence}"
            )
            cat_str = ", ".join(f"{c}={n}" for c, n in sorted(m.category_counts.items(), key=lambda x: -x[1])[:5])
            L.append(f"    category top5: {cat_str}")
            L.append(f"    sample: {', '.join(m.sample_merchants[:3])}")
        L.append("")
        L.append("[Canonical Sample (앞 10건)]")
        for i, s in enumerate(self.sample, 1):
            L.append(f"  {i}. id={s['id']}  name={s['name']}  cat={s['category']}  "
                     f"market={s.get('market_name') or '-'}  "
                     f"({s.get('latitude')}, {s.get('longitude')})  "
                     f"loc={s.get('location_source')}/{s.get('location_precision')}"
                     f"/{s.get('location_confidence')}")
        return "\n".join(L)


def _canonical_to_sample_dict(c: CanonicalMerchantCandidate) -> Dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "category": c.category,
        "market_name": c.market_name,
        "latitude": c.latitude,
        "longitude": c.longitude,
        "location_source": c.location_source,
        "location_precision": c.location_precision,
        "location_confidence": c.location_confidence,
        "supports_onnuri": c.supports_onnuri,
        "supported_payment_types": c.supported_payment_types,
        "products": c.products[:5],
        "anyang_district": c.anyang_district,
    }


def _build_market_aggregates(candidates: List[CanonicalMerchantCandidate]) -> List[MarketAggregate]:
    """시장별 집계 (docs/MAP_UX_TODO.md - /api/v1/markets/map 후보)."""
    by_market: Dict[str, List[CanonicalMerchantCandidate]] = defaultdict(list)
    for c in candidates:
        key = c.market_name or "(no market)"
        by_market[key].append(c)

    out: List[MarketAggregate] = []
    for name, ms in by_market.items():
        # centroid: 시장별 매장이 모두 동일 좌표 (사전 매핑) 이므로 첫 매장 좌표 사용.
        centroid_lat = ms[0].latitude
        centroid_lng = ms[0].longitude
        loc_src = ms[0].location_source
        loc_conf = ms[0].location_confidence

        cnt_paper = sum(1 for c in ms if "onnuriPaper" in c.supported_payment_types)
        cnt_digital = sum(1 for c in ms if "onnuriDigital" in c.supported_payment_types)
        cnt_both = sum(
            1 for c in ms
            if "onnuriPaper" in c.supported_payment_types
            and "onnuriDigital" in c.supported_payment_types
        )

        cat_counts = Counter(c.category for c in ms)
        sample_names = [c.name for c in ms[:5]]

        out.append(MarketAggregate(
            market_name=name,
            centroid_lat=centroid_lat,
            centroid_lng=centroid_lng,
            location_source=loc_src,
            location_confidence=loc_conf,
            merchant_count=len(ms),
            supports_paper=cnt_paper,
            supports_digital=cnt_digital,
            supports_both=cnt_both,
            category_counts=dict(cat_counts),
            sample_merchants=sample_names,
        ))
    out.sort(key=lambda m: -m.merchant_count)
    return out


# ---------- Input: CSV ----------

def run_dryrun_from_csv(
    *,
    csv_path: Path,
    snapshot_date: date,
    region: str = "anyang",
) -> CanonicalDryRunReport:
    total = 0
    normalized_ok = 0
    normalized_dropped = 0
    candidates: List[CanonicalMerchantCandidate] = []

    for raw in iter_records(csv_path):
        total += 1
        n = normalize(raw)
        if n is None:
            normalized_dropped += 1
            continue
        normalized_ok += 1
        if region == "anyang" and n.anyang_district is None:
            continue
        rh = _row_hash(raw.raw_payload)
        candidates.append(
            to_canonical(n, row_hash=rh, snapshot_date=snapshot_date.isoformat())
        )

    return _build_report(
        input_source=f"csv:{csv_path.name}",
        snapshot_date=snapshot_date.isoformat(),
        region=region,
        total_input_rows=total,
        normalized_ok=normalized_ok,
        normalized_dropped=normalized_dropped,
        candidates=candidates,
    )


# ---------- Input: DB raw_onnuri_merchants ----------

async def _run_dryrun_from_db_async(
    *,
    dsn: str,
    snapshot_date: date,
    region: str = "anyang",
) -> CanonicalDryRunReport:
    try:
        import asyncpg  # type: ignore
    except ImportError:  # pragma: no cover
        raise RuntimeError("asyncpg not installed (컨테이너 안에서 실행)")

    from worker.importers.onnuri.models import RawOnnuriRecord
    from worker.importers.onnuri.writer import _normalize_dsn

    conn = await asyncpg.connect(_normalize_dsn(dsn))
    try:
        rows = await conn.fetch(
            """
            SELECT row_hash, merchant_name, market_name, address_sido,
                   products_raw, supports_paper_raw, supports_digital_raw,
                   registration_year_raw, raw_payload
            FROM raw_onnuri_merchants
            WHERE source_snapshot_date = $1
            """,
            snapshot_date,
        )
    finally:
        await conn.close()

    total = len(rows)
    normalized_ok = 0
    normalized_dropped = 0
    candidates: List[CanonicalMerchantCandidate] = []

    for row in rows:
        raw = RawOnnuriRecord(
            merchant_name=row["merchant_name"],
            market_name=row["market_name"],
            address=row["address_sido"],
            products_raw=row["products_raw"],
            supports_paper_raw=row["supports_paper_raw"],
            supports_digital_raw=row["supports_digital_raw"],
            registration_year_raw=row["registration_year_raw"],
            raw_payload=row["raw_payload"] if isinstance(row["raw_payload"], dict) else {},
        )
        n = normalize(raw)
        if n is None:
            normalized_dropped += 1
            continue
        normalized_ok += 1
        # DB 에는 이미 region 필터 통과한 raw 만 저장됨 (writer.py) → 별도 필터 불필요
        candidates.append(
            to_canonical(n, row_hash=row["row_hash"], snapshot_date=snapshot_date.isoformat())
        )

    return _build_report(
        input_source="db:raw_onnuri_merchants",
        snapshot_date=snapshot_date.isoformat(),
        region=region,
        total_input_rows=total,
        normalized_ok=normalized_ok,
        normalized_dropped=normalized_dropped,
        candidates=candidates,
    )


def run_dryrun_from_db(
    *,
    snapshot_date: date,
    region: str = "anyang",
    database_url: Optional[str] = None,
) -> CanonicalDryRunReport:
    dsn = database_url or os.environ.get("DATABASE_URL") or ""
    if not dsn:
        raise RuntimeError("DATABASE_URL 필요")
    return asyncio.run(_run_dryrun_from_db_async(
        dsn=dsn, snapshot_date=snapshot_date, region=region,
    ))


# ---------- shared report builder ----------

def _build_report(
    *, input_source, snapshot_date, region,
    total_input_rows, normalized_ok, normalized_dropped,
    candidates: List[CanonicalMerchantCandidate],
) -> CanonicalDryRunReport:
    loc_src_counts = Counter(c.location_source for c in candidates)
    loc_prec_counts = Counter(c.location_precision for c in candidates)
    cat_counts = Counter(c.category for c in candidates)

    coord_valid = sum(1 for c in candidates if c.latitude is not None and c.longitude is not None)
    coord_missing = len(candidates) - coord_valid
    unmappable = sum(1 for c in candidates if c.location_precision == "region_level")

    market_aggs = _build_market_aggregates(candidates)

    return CanonicalDryRunReport(
        input_source=input_source,
        snapshot_date=snapshot_date,
        region_filter=region,
        total_input_rows=total_input_rows,
        normalized_ok=normalized_ok,
        normalized_dropped=normalized_dropped,
        canonical_generated=len(candidates),
        location_source_counts=dict(loc_src_counts),
        location_precision_counts=dict(loc_prec_counts),
        category_counts=dict(cat_counts),
        coordinate_valid=coord_valid,
        coordinate_missing=coord_missing,
        unmappable_to_map=unmappable,
        market_aggregates=market_aggs,
        sample=[_canonical_to_sample_dict(c) for c in candidates[:10]],
    )
