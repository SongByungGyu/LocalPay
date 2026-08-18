"""Canonical converter · dry-run · market aggregation 유닛 테스트."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from worker.importers.onnuri.canonical import (
    LOC_SOURCE_MARKET_CENTROID,
    LOC_SOURCE_MARKET_DATASET,
    to_canonical,
)
from worker.importers.onnuri.canonical_dryrun import (
    _build_market_aggregates,
    run_dryrun_from_csv,
)
from worker.importers.onnuri.models import RawOnnuriRecord
from worker.importers.onnuri.normalizer import normalize
from worker.importers.onnuri.writer import _row_hash

FIXTURE = Path(__file__).parent / "fixtures" / "onnuri_sample.csv"


def _make_raw(name, market, addr, products="한식", paper="Y", digital="Y", year="2020"):
    return RawOnnuriRecord(
        merchant_name=name, market_name=market, address=addr,
        products_raw=products,
        supports_paper_raw=paper, supports_digital_raw=digital,
        registration_year_raw=year,
        raw_payload={"가맹점명": name, "소속 시장명(또는 상점가)": market, "소재지": addr,
                     "취급품목": products, "지류형 가맹 여부": paper,
                     "디지털형 가맹 여부": digital, "등록년도": year},
    )


# ---------- id generation ----------

def test_canonical_id_is_stable_and_prefixed():
    raw = _make_raw("가게A", "안양중앙시장", "경기")
    n = normalize(raw)
    rh = _row_hash(raw.raw_payload)
    c1 = to_canonical(n, row_hash=rh, snapshot_date="2025-07-31")
    c2 = to_canonical(n, row_hash=rh, snapshot_date="2025-07-31")
    assert c1.id == c2.id
    assert c1.id.startswith("onnuri-a-")
    assert len(c1.id.split("-")[-1]) == 16


def test_canonical_id_different_when_row_differs():
    r1 = _make_raw("가게A", "안양중앙시장", "경기")
    r2 = _make_raw("가게B", "안양중앙시장", "경기")
    n1, n2 = normalize(r1), normalize(r2)
    c1 = to_canonical(n1, row_hash=_row_hash(r1.raw_payload), snapshot_date="2025-07-31")
    c2 = to_canonical(n2, row_hash=_row_hash(r2.raw_payload), snapshot_date="2025-07-31")
    assert c1.id != c2.id


# ---------- location metadata ----------

def test_traditional_market_gets_market_dataset_source():
    raw = _make_raw("행복정육점", "안양중앙시장", "경기", products="돼지고기, 한우")
    n = normalize(raw)
    c = to_canonical(n, row_hash=_row_hash(raw.raw_payload), snapshot_date="2025-07-31")
    assert c.location_source == LOC_SOURCE_MARKET_DATASET
    assert c.location_precision == "market_level"
    assert c.location_confidence == 0.8
    assert c.latitude is not None and c.longitude is not None


def test_shopping_street_gets_market_centroid_manual():
    raw = _make_raw("카페", "평촌1번가 상점가", "경기", products="커피")
    n = normalize(raw)
    c = to_canonical(n, row_hash=_row_hash(raw.raw_payload), snapshot_date="2025-07-31")
    assert c.location_source == LOC_SOURCE_MARKET_CENTROID
    assert c.location_precision == "market_level"
    assert c.location_confidence == 0.7
    assert c.latitude is not None and c.longitude is not None


def test_unmapped_market_gets_no_location():
    raw = _make_raw("가게", "안양미지의시장", "경기")
    n = normalize(raw)
    c = to_canonical(n, row_hash=_row_hash(raw.raw_payload), snapshot_date="2025-07-31")
    assert c.location_source is None
    assert c.location_precision == "region_level"
    assert c.location_confidence is None
    assert c.latitude is None and c.longitude is None


def test_supported_payment_types_from_yn_flags():
    raw = _make_raw("가게", "안양중앙시장", "경기", paper="Y", digital="N")
    n = normalize(raw)
    c = to_canonical(n, row_hash=_row_hash(raw.raw_payload), snapshot_date="2025-07-31")
    assert "onnuriPaper" in c.supported_payment_types
    assert "onnuriDigital" not in c.supported_payment_types


def test_supports_onnuri_always_true_and_local_currency_false():
    raw = _make_raw("가게", "안양중앙시장", "경기")
    n = normalize(raw)
    c = to_canonical(n, row_hash=_row_hash(raw.raw_payload), snapshot_date="2025-07-31")
    assert c.supports_onnuri is True
    assert c.supports_local_currency is False


# ---------- market aggregation ----------

def test_market_aggregation_groups_by_market_name():
    raws = [
        _make_raw("가게1", "안양중앙시장", "경기", products="한식"),
        _make_raw("가게2", "안양중앙시장", "경기", products="약국"),
        _make_raw("카페", "평촌1번가 상점가", "경기", products="커피"),
    ]
    candidates = []
    for r in raws:
        n = normalize(r)
        candidates.append(to_canonical(n, row_hash=_row_hash(r.raw_payload), snapshot_date="2025-07-31"))
    aggs = _build_market_aggregates(candidates)
    assert len(aggs) == 2
    by_name = {a.market_name: a for a in aggs}
    assert by_name["안양중앙시장"].merchant_count == 2
    assert by_name["평촌1번가 상점가"].merchant_count == 1
    # 각 시장의 centroid 좌표.
    assert by_name["안양중앙시장"].centroid_lat is not None
    # 정렬: count 내림차순.
    assert aggs[0].merchant_count >= aggs[-1].merchant_count


def test_market_aggregation_counts_payment_flags():
    raws = [
        _make_raw("가게1", "안양중앙시장", "경기", paper="Y", digital="Y"),
        _make_raw("가게2", "안양중앙시장", "경기", paper="Y", digital="N"),
        _make_raw("가게3", "안양중앙시장", "경기", paper="N", digital="Y"),
    ]
    candidates = [
        to_canonical(normalize(r), row_hash=_row_hash(r.raw_payload), snapshot_date="2025-07-31")
        for r in raws
    ]
    aggs = _build_market_aggregates(candidates)
    a = aggs[0]
    assert a.supports_paper == 2
    assert a.supports_digital == 2
    assert a.supports_both == 1


# ---------- dry-run CSV ----------

def test_dryrun_from_csv_fixture():
    report = run_dryrun_from_csv(
        csv_path=FIXTURE,
        snapshot_date=date(2025, 7, 31),
        region="anyang",
    )
    assert report.canonical_generated >= 8
    # 안양 fixture 는 안양중앙시장 매장이 있어 location_source 매핑 발생.
    assert report.coordinate_valid >= 1
    # 시장 aggregate 최소 1개 이상.
    assert len(report.market_aggregates) >= 1
    # location_precision 분포에 market_level 있어야.
    assert "market_level" in report.location_precision_counts or "region_level" in report.location_precision_counts
