"""Onnuri importer 유닛 테스트 (DB 불필요)."""
from __future__ import annotations

from pathlib import Path

import pytest

from worker.importers.onnuri.category_mapper import DEFAULT_CATEGORY, map_category
from worker.importers.onnuri.importer import run_dry_run
from worker.importers.onnuri.normalizer import (
    _classify_anyang,
    _parse_yn,
    _parse_year,
    _split_products,
    normalize,
)
from worker.importers.onnuri.parser import (
    build_header_map,
    detect_encoding,
    inspect_file,
    iter_records,
)
from worker.importers.onnuri.models import RawOnnuriRecord

FIXTURE = Path(__file__).parent / "fixtures" / "onnuri_sample.csv"


# ---------- parser: header ----------

def test_header_map_official_columns():
    header = [
        "가맹점명", "소속 시장명(또는 상점가)", "소재지",
        "취급품목", "지류형 가맹 여부", "디지털형 가맹 여부", "등록년도",
    ]
    m = build_header_map(header)
    assert m["merchant_name"] == "가맹점명"
    assert m["market_name"] == "소속 시장명(또는 상점가)"
    assert m["address"] == "소재지"
    assert m["products_raw"] == "취급품목"
    assert m["supports_paper_raw"] == "지류형 가맹 여부"
    assert m["supports_digital_raw"] == "디지털형 가맹 여부"
    assert m["registration_year_raw"] == "등록년도"


def test_header_map_tolerates_whitespace_variants():
    header = ["가맹점명", "소속시장명(또는상점가)", "주소", "품목", "지류형", "디지털형", "등록연도"]
    m = build_header_map(header)
    assert m["merchant_name"] == "가맹점명"
    assert m["market_name"] == "소속시장명(또는상점가)"
    assert m["address"] == "주소"
    assert m["products_raw"] == "품목"
    assert m["supports_paper_raw"] == "지류형"
    assert m["supports_digital_raw"] == "디지털형"
    assert m["registration_year_raw"] == "등록연도"


def test_inspect_file_returns_encoding_and_header():
    info = inspect_file(FIXTURE)
    assert info.size_bytes > 0
    assert info.encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr")
    assert "가맹점명" in info.header
    assert info.header_map["merchant_name"] == "가맹점명"


def test_iter_records_yields_all_rows_including_invalid():
    records = list(iter_records(FIXTURE))
    # 원본 fixture 는 13행 (header 제외). 모두 yield (normalize 는 별도 단계).
    assert len(records) == 13


# ---------- normalizer helpers ----------

@pytest.mark.parametrize("raw,expected", [
    ("Y", True), ("N", False), ("y", True), ("n", False),
    ("O", True), ("X", False), ("있음", True), ("없음", False),
    ("가능", True), ("불가", False), ("가맹", True), ("미가맹", False),
    ("1", True), ("0", False),
    ("", False), (None, False), ("wtf", False),   # 알 수 없으면 False (안전)
])
def test_parse_yn(raw, expected):
    assert _parse_yn(raw) is expected


@pytest.mark.parametrize("raw,expected", [
    ("2020", 2020), ("2020년", 2020), ("2020.05.01", 2020),
    ("20200501", 2020), ("abc", None), (None, None), ("", None),
    ("1800", None), ("2200", None),   # 범위 밖
])
def test_parse_year(raw, expected):
    assert _parse_year(raw) == expected


def test_split_products_comma_and_slash():
    assert _split_products("돼지고기, 한우, 선물세트") == ["돼지고기", "한우", "선물세트"]
    assert _split_products("커피/브런치") == ["커피", "브런치"]
    assert _split_products("김치|나물|반찬") == ["김치", "나물", "반찬"]
    assert _split_products("떡") == ["떡"]
    assert _split_products("") == []
    assert _split_products(None) == []
    # dedup
    assert _split_products("커피, 커피, 브런치") == ["커피", "브런치"]


@pytest.mark.parametrize("sido,sigungu,full,expected", [
    ("경기도", "안양시", "경기도 안양시 만안구 만안로 232", "manan"),
    ("경기도", "안양시", "경기도 안양시 동안구 시민대로 250", "dongan"),
    ("경기도", "안양시", "경기도 안양시 안양로", "unknown"),
    ("서울특별시", "중구", "서울특별시 중구 세종대로", None),
    ("부산광역시", "수영구", "부산광역시 수영구", None),
])
def test_classify_anyang(sido, sigungu, full, expected):
    assert _classify_anyang(sido, sigungu, full) == expected


# ---------- normalizer.normalize ----------

def test_normalize_drops_when_name_or_address_empty():
    r = RawOnnuriRecord(
        merchant_name=None, market_name=None, address="경기도 안양시 만안구",
        products_raw=None, supports_paper_raw=None, supports_digital_raw=None,
        registration_year_raw=None,
    )
    assert normalize(r) is None
    r2 = RawOnnuriRecord(
        merchant_name="이름있음", market_name=None, address=None,
        products_raw=None, supports_paper_raw=None, supports_digital_raw=None,
        registration_year_raw=None,
    )
    assert normalize(r2) is None


def test_normalize_valid_anyang_manan():
    r = RawOnnuriRecord(
        merchant_name="  안양중앙시장 행복정육점 ",
        market_name="안양중앙시장",
        address="경기도 안양시 만안구 만안로 232",
        products_raw="돼지고기, 한우, 선물세트",
        supports_paper_raw="Y",
        supports_digital_raw="Y",
        registration_year_raw="2019",
    )
    n = normalize(r)
    assert n is not None
    assert n.merchant_name_normalized == "안양중앙시장 행복정육점"
    assert n.market_name_normalized == "안양중앙시장"
    assert n.supports_paper is True
    assert n.supports_digital is True
    assert n.supports_onnuri is True
    assert n.products == ["돼지고기", "한우", "선물세트"]
    assert n.mapped_category == "market"     # 시장명 힌트 최우선
    assert n.category_source == "market_name"
    assert n.registration_year == 2019
    assert n.anyang_district == "manan"
    assert n.coordinate_valid is False       # 온누리 원본은 좌표 없음
    assert n.geocode_status == "pending"


def test_normalize_pharmacy_by_product_keyword():
    r = RawOnnuriRecord(
        merchant_name="평촌우리약국", market_name=None,
        address="경기도 안양시 동안구 평촌대로 145",
        products_raw="의약품",
        supports_paper_raw="Y", supports_digital_raw="N",
        registration_year_raw="2018",
    )
    n = normalize(r)
    assert n.mapped_category == "pharmacy"
    assert n.category_source == "product_keyword"
    assert n.supports_paper is True
    assert n.supports_digital is False


def test_normalize_non_anyang_is_none_district():
    r = RawOnnuriRecord(
        merchant_name="서울가게", market_name=None,
        address="서울특별시 중구 세종대로 110",
        products_raw="커피", supports_paper_raw="N", supports_digital_raw="Y",
        registration_year_raw="2021",
    )
    n = normalize(r)
    assert n is not None
    assert n.anyang_district is None
    assert n.mapped_category == "cafe"


# ---------- category mapper ----------

def test_category_mapper_market_name_priority():
    assert map_category(market_name="안양중앙시장", products=[])[0] == "market"


@pytest.mark.parametrize("products,expected", [
    (["의약품"], "pharmacy"),
    (["커피", "브런치"], "cafe"),
    (["헤어", "네일"], "beauty"),
    (["쌀", "채소"], "food"),
    (["세탁"], "life"),
    (["칼국수"], "restaurant"),
    (["잡화"], DEFAULT_CATEGORY),
    ([], DEFAULT_CATEGORY),
])
def test_category_mapper_products(products, expected):
    cat, _src = map_category(market_name=None, products=products)
    assert cat == expected


# ---------- importer dry-run ----------

def test_dry_run_produces_anyang_stats_only():
    report = run_dry_run(file_path=FIXTURE, region="anyang")
    # source 13 rows.
    assert report.source_rows == 13
    # 안양 지역만 anyang_total 로 카운트. 서울/부산은 제외.
    assert report.anyang_total >= 8
    # 최소한 만안 3+, 동안 3+, unknown 0+ (fixture 상)
    assert report.anyang_manan >= 3
    assert report.anyang_dongan >= 3
    # 좌표는 온누리 원본에 없음 → 모두 geocode 필요.
    assert report.coord_valid == 0
    assert report.geocode_required == report.anyang_total
    # 카테고리 매핑 최소 1개 이상 market 로 분류 (안양중앙시장).
    assert report.category_counts.get("market", 0) >= 1
