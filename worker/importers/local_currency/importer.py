"""Dry-run 오케스트레이션: fetch → parse → normalize → quality report."""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from worker.importers.local_currency.client import (
    LocalCurrencyApiClient,
    REGION_CODES,
)
from worker.importers.local_currency.normalizer import normalize
from worker.importers.local_currency.parser import parse_response_items


@dataclass
class DryRunReport:
    region: str
    region_code: str
    requested: int
    fetched: int
    parsed: int
    normalized_valid: int
    normalized_dropped: int
    api_calls: int
    total_reported: Optional[int]

    coord_valid: int
    coord_missing: int
    coord_invalid: int

    name_valid: int
    name_empty: int

    address_valid: int
    address_empty: int

    phone_present: int
    phone_missing: int

    industry_mapped: int
    industry_unmapped: int

    business_status_counts: Dict[str, int]
    category_counts: Dict[str, int]

    sample_merchants: List[Dict[str, Any]]

    def as_text(self) -> str:
        lines: List[str] = []
        lines.append(f"[DryRun] region: {self.region} (code={self.region_code})")
        lines.append(
            f"  requested={self.requested}  fetched={self.fetched}  "
            f"parsed={self.parsed}  api_calls={self.api_calls}  "
            f"total_reported={self.total_reported}"
        )
        lines.append("")
        lines.append("[Coordinates]")
        lines.append(
            f"  valid={self.coord_valid}  missing={self.coord_missing}  invalid={self.coord_invalid}"
        )
        lines.append("[Merchant Name]")
        lines.append(f"  valid={self.name_valid}  empty={self.name_empty}")
        lines.append("[Address]")
        lines.append(f"  valid={self.address_valid}  empty={self.address_empty}")
        lines.append("[Phone]")
        lines.append(f"  present={self.phone_present}  missing={self.phone_missing}")
        lines.append("[Industry]")
        lines.append(f"  mapped={self.industry_mapped}  unmapped={self.industry_unmapped}")
        lines.append("[Business Status]")
        for k, v in self.business_status_counts.items():
            lines.append(f"  {k}={v}")
        lines.append("[Category]")
        for k, v in self.category_counts.items():
            lines.append(f"  {k}={v}")
        lines.append("")
        lines.append("[Sample Merchants]")
        for i, m in enumerate(self.sample_merchants, 1):
            lines.append(
                f"  {i}. {m['name']}  |  {m['address']}  |  "
                f"({m['lat']},{m['lng']})  |  cat={m['category']}  |  "
                f"status={m['business_status']}"
            )
        return "\n".join(lines)


def run_dry_run(
    *,
    service_key: str,
    region: str,
    max_records: int,
    page_size: int = 100,
    fixture_path: Optional[Path] = None,
) -> DryRunReport:
    if fixture_path:
        items, api_calls, total_reported = _load_fixture(fixture_path)
        region_code = REGION_CODES.get(region, "(fixture)")
    else:
        client = LocalCurrencyApiClient(service_key=service_key)
        result = client.fetch_region(region, max_records=max_records, page_size=page_size)
        items = result.fetched
        api_calls = result.api_calls
        total_reported = result.total_reported
        region_code = REGION_CODES[region]

    raw_records = parse_response_items(items)
    parsed_count = len(raw_records)

    normalized_valid = []
    normalized_dropped = 0
    for r in raw_records:
        n = normalize(r)
        if n is None:
            normalized_dropped += 1
        else:
            normalized_valid.append(n)

    coord_valid = sum(1 for n in normalized_valid if n.coordinate_valid)
    coord_missing = sum(1 for n in normalized_valid if n.coordinate_reason == "missing")
    coord_invalid = sum(
        1 for n in normalized_valid if not n.coordinate_valid and n.coordinate_reason != "missing"
    )

    name_valid = sum(1 for r in raw_records if r.merchant_name)
    name_empty = parsed_count - name_valid

    address_valid = sum(1 for r in raw_records if r.address)
    address_empty = parsed_count - address_valid

    phone_present = sum(1 for r in raw_records if r.phone)
    phone_missing = parsed_count - phone_present

    industry_mapped = sum(1 for n in normalized_valid if n.mapped_category != "etc")
    industry_unmapped = len(normalized_valid) - industry_mapped

    status_counts = Counter(
        (n.business_status or "unknown") for n in normalized_valid
    )
    category_counts = Counter(n.mapped_category for n in normalized_valid)

    sample = [_sample_summary(n) for n in normalized_valid[:10]]

    return DryRunReport(
        region=region,
        region_code=region_code,
        requested=max_records,
        fetched=len(items),
        parsed=parsed_count,
        normalized_valid=len(normalized_valid),
        normalized_dropped=normalized_dropped,
        api_calls=api_calls,
        total_reported=total_reported,
        coord_valid=coord_valid,
        coord_missing=coord_missing,
        coord_invalid=coord_invalid,
        name_valid=name_valid,
        name_empty=name_empty,
        address_valid=address_valid,
        address_empty=address_empty,
        phone_present=phone_present,
        phone_missing=phone_missing,
        industry_mapped=industry_mapped,
        industry_unmapped=industry_unmapped,
        business_status_counts=dict(status_counts),
        category_counts=dict(category_counts),
        sample_merchants=sample,
    )


def _sample_summary(n) -> Dict[str, Any]:
    return {
        "name": n.merchant_name_normalized,
        "address": n.address_normalized,
        "lat": n.latitude,
        "lng": n.longitude,
        "category": n.mapped_category,
        "business_status": n.business_status or "unknown",
    }


def _load_fixture(path: Path) -> tuple[list[Dict[str, Any]], int, Optional[int]]:
    """Key 없이 로컬 sample fixture 로 파이프라인만 검증할 때 사용."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data, 0, None
    if isinstance(data, dict) and "items" in data:
        return list(data["items"]), 0, data.get("totalCount")
    raise ValueError(f"unsupported fixture shape: {type(data).__name__}")
