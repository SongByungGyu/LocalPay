"""Dry-run 오케스트레이션: file → parse → normalize → anyang filter → quality report."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from worker.importers.onnuri.models import NormalizedOnnuriRecord
from worker.importers.onnuri.normalizer import normalize
from worker.importers.onnuri.parser import inspect_file, iter_records


@dataclass
class DryRunReport:
    snapshot_file: str
    snapshot_size_bytes: int
    encoding: str
    header: List[str]

    source_rows: int
    parsed_ok: int
    invalid_rows: int
    parse_errors: int

    # 전국 (참고용).
    total_by_sido: Dict[str, int] = field(default_factory=dict)

    # 안양 전용 통계 (스펙 §15 · §20).
    anyang_total: int = 0
    anyang_manan: int = 0
    anyang_dongan: int = 0
    anyang_unknown: int = 0

    name_valid: int = 0
    name_empty: int = 0
    address_valid: int = 0
    address_empty: int = 0
    products_present: int = 0
    products_missing: int = 0

    paper_count: int = 0
    digital_count: int = 0
    both_count: int = 0
    neither_count: int = 0

    category_counts: Dict[str, int] = field(default_factory=dict)
    category_source_counts: Dict[str, int] = field(default_factory=dict)

    coord_valid: int = 0
    coord_missing: int = 0
    geocode_required: int = 0

    duplicate_name_candidates: int = 0

    sample_merchants: List[Dict[str, Any]] = field(default_factory=list)

    def as_text(self) -> str:
        L: List[str] = []
        L.append("[Snapshot]")
        L.append(f"  file={self.snapshot_file}")
        L.append(f"  size_bytes={self.snapshot_size_bytes}")
        L.append(f"  encoding={self.encoding}")
        L.append(f"  header_cols={len(self.header)}")
        L.append("")
        L.append("[Source]")
        L.append(f"  source_rows={self.source_rows}")
        L.append(f"  parsed_ok={self.parsed_ok}")
        L.append(f"  invalid_rows={self.invalid_rows}")
        L.append(f"  parse_errors={self.parse_errors}")
        L.append("")
        L.append("[전국 시도 상위]")
        for sido, n in sorted(self.total_by_sido.items(), key=lambda x: -x[1])[:8]:
            L.append(f"  {sido}={n}")
        L.append("")
        L.append("[Anyang]")
        L.append(f"  total={self.anyang_total}")
        L.append(f"  Manan={self.anyang_manan}")
        L.append(f"  Dongan={self.anyang_dongan}")
        L.append(f"  unknown={self.anyang_unknown}")
        L.append("")
        L.append("[Anyang 필드 완성도]")
        L.append(f"  name_valid={self.name_valid}  empty={self.name_empty}")
        L.append(f"  address_valid={self.address_valid}  empty={self.address_empty}")
        L.append(f"  products_present={self.products_present}  missing={self.products_missing}")
        L.append("")
        L.append("[Anyang Payments]")
        L.append(f"  paper={self.paper_count}")
        L.append(f"  digital={self.digital_count}")
        L.append(f"  both(paper+digital)={self.both_count}")
        L.append(f"  neither={self.neither_count}")
        L.append("")
        L.append("[Anyang Category]")
        for k, v in sorted(self.category_counts.items(), key=lambda x: -x[1]):
            L.append(f"  {k}={v}")
        L.append("[Category source]")
        for k, v in self.category_source_counts.items():
            L.append(f"  {k}={v}")
        L.append("")
        L.append("[Anyang Coordinates]")
        L.append(f"  valid={self.coord_valid}  missing={self.coord_missing}")
        L.append(f"  geocode_required={self.geocode_required}")
        L.append("")
        L.append(f"[Potential duplicate names]={self.duplicate_name_candidates}")
        L.append("")
        L.append("[Sample Anyang Merchants]")
        for i, m in enumerate(self.sample_merchants, 1):
            L.append(
                f"  {i}. {m['name']}  |  시장={m['market'] or '-'}  |  {m['address']}"
            )
            L.append(
                f"     products={m['products']}  |  paper={m['paper']}  digital={m['digital']}  |  cat={m['category']}(src={m['category_source']})  |  district={m['district']}"
            )
        return "\n".join(L)


def run_dry_run(
    *,
    file_path: Path,
    region: str = "anyang",
    limit: Optional[int] = None,
) -> DryRunReport:
    if region != "anyang":
        raise ValueError(f"only region=anyang is supported in Gate 3-A, got {region}")

    info = inspect_file(file_path)

    source_rows = 0
    invalid_rows = 0
    parse_errors = 0
    total_by_sido: Counter = Counter()

    anyang_records: List[NormalizedOnnuriRecord] = []

    def _on_err(line_no, exc, row):
        nonlocal parse_errors
        parse_errors += 1

    for raw in iter_records(file_path, encoding=info.encoding, on_error=_on_err):
        source_rows += 1
        # 전국 시도 카운트 (raw address 앞 토큰) — 참고용.
        addr = (raw.address or "").strip()
        first_tok = addr.split(" ", 1)[0] if addr else ""
        if first_tok:
            total_by_sido[first_tok] += 1

        n = normalize(raw)
        if n is None:
            invalid_rows += 1
            continue
        if n.anyang_district is not None:
            anyang_records.append(n)
            if limit is not None and len(anyang_records) >= limit:
                break

    report = DryRunReport(
        snapshot_file=str(file_path.name),
        snapshot_size_bytes=info.size_bytes,
        encoding=info.encoding,
        header=list(info.header),
        source_rows=source_rows,
        parsed_ok=source_rows - invalid_rows,
        invalid_rows=invalid_rows,
        parse_errors=parse_errors,
        total_by_sido=dict(total_by_sido),
    )

    # Anyang 통계 채우기.
    report.anyang_total = len(anyang_records)
    for n in anyang_records:
        if n.anyang_district == "manan":
            report.anyang_manan += 1
        elif n.anyang_district == "dongan":
            report.anyang_dongan += 1
        else:
            report.anyang_unknown += 1

    for n in anyang_records:
        if n.merchant_name_normalized:
            report.name_valid += 1
        else:
            report.name_empty += 1
        if n.address_normalized:
            report.address_valid += 1
        else:
            report.address_empty += 1
        if n.products:
            report.products_present += 1
        else:
            report.products_missing += 1

    for n in anyang_records:
        if n.supports_paper and n.supports_digital:
            report.both_count += 1
        elif n.supports_paper:
            report.paper_count += 1
        elif n.supports_digital:
            report.digital_count += 1
        else:
            report.neither_count += 1
    # paper/digital 배타 표시가 아니라 "각각 총 지원 건수" 도 이해 편의를 위해 별도 저장.
    report.paper_count += report.both_count
    report.digital_count += report.both_count

    cat_counts: Counter = Counter()
    cat_src_counts: Counter = Counter()
    for n in anyang_records:
        cat_counts[n.mapped_category] += 1
        cat_src_counts[n.category_source] += 1
    report.category_counts = dict(cat_counts)
    report.category_source_counts = dict(cat_src_counts)

    for n in anyang_records:
        if n.coordinate_valid:
            report.coord_valid += 1
        else:
            report.coord_missing += 1
            report.geocode_required += 1

    # potential duplicate: normalized_name 이 같은 항목이 2건 이상.
    name_buckets: Dict[str, int] = defaultdict(int)
    for n in anyang_records:
        name_buckets[n.merchant_name_normalized] += 1
    report.duplicate_name_candidates = sum(1 for c in name_buckets.values() if c >= 2)

    # 최대 20건 sample.
    for n in anyang_records[:20]:
        report.sample_merchants.append({
            "name": n.merchant_name_normalized,
            "market": n.market_name_normalized,
            "address": n.address_normalized,
            "products": ", ".join(n.products) if n.products else "-",
            "paper": n.supports_paper,
            "digital": n.supports_digital,
            "category": n.mapped_category,
            "category_source": n.category_source,
            "district": n.anyang_district,
        })
    return report
