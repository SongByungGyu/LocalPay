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


@pytest.mark.parametrize("sido,sigungu,full,market,expected", [
    # 주소 기반 (fallback) — 시군구 상세 있을 때
    ("경기도", "안양시", "경기도 안양시 만안구 만안로 232", None, "manan"),
    ("경기도", "안양시", "경기도 안양시 동안구 시민대로 250", None, "dongan"),
    ("경기도", "안양시", "경기도 안양시 안양로", None, "unknown"),
    ("서울특별시", "중구", "서울특별시 중구 세종대로", None, None),
    ("부산광역시", "수영구", "부산광역시 수영구", None, None),
    # 시장명 기반 (2025-07-31 CSV 스펙에서 주소가 시도만 있는 경우)
    ("경기", None, "경기", "안양중앙시장", "manan"),
    ("경기", None, "경기", "안양남부시장", "manan"),
    ("경기", None, "경기", "안양관양시장", "dongan"),
    ("경기", None, "경기", "평촌1번가 상점가", "dongan"),
    ("경기", None, "경기", "안양미지의시장", "unknown"),   # "안양" 포함이지만 매핑 미상
    ("서울", None, "서울", "명동상점가", None),
])
def test_classify_anyang(sido, sigungu, full, market, expected):
    assert _classify_anyang(sido, sigungu, full, market_name=market) == expected


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
    assert n.market_name_normalized == "안양중앙시장"      # 시장명은 affiliation 정보로 보존
    assert n.supports_paper is True
    assert n.supports_digital is True
    assert n.supports_onnuri is True
    assert n.products == ["돼지고기", "한우", "선물세트"]
    # 스펙 §결정 2 — market_name 이 category 를 덮지 않음.
    # 정육점 은 products=[돼지고기, 한우] → food.
    assert n.mapped_category == "food"
    assert n.category_source == "product_keyword"
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

def test_category_mapper_market_name_ignored():
    """스펙 §결정 2: marketName 은 category 결정에서 제외."""
    # 시장에 속했더라도 products 로 판단.
    cat, src = map_category(
        market_name="안양중앙시장", products=["돼지고기", "한우"], merchant_name="행복정육점"
    )
    assert cat == "food"
    assert src == "product_keyword"
    # products 도 없으면 name 으로.
    cat, src = map_category(
        market_name="안양중앙시장", products=[], merchant_name="평촌수약국"
    )
    assert cat == "pharmacy"
    assert src == "name_keyword"
    # products/name 다 매칭 없으면 etc — 시장명 있어도 market 로 분류되지 않음.
    cat, src = map_category(market_name="안양중앙시장", products=[], merchant_name="이름없음가게")
    assert cat == DEFAULT_CATEGORY
    assert src == "default"


@pytest.mark.parametrize("products,expected", [
    (["의약품"], "pharmacy"),
    (["커피", "브런치"], "cafe"),
    (["헤어", "네일"], "beauty"),
    (["쌀", "채소"], "food"),
    (["세탁"], "life"),
    (["칼국수"], "restaurant"),
    (["짬뽕"], "restaurant"),
    (["미용"], "beauty"),
    (["케이크", "음료"], "cafe"),           # 케이크 → cafe (베이커리 계열)
    (["약품"], "pharmacy"),
    (["잡화"], DEFAULT_CATEGORY),
    ([], DEFAULT_CATEGORY),
])
def test_category_mapper_products(products, expected):
    cat, _src = map_category(products=products)
    assert cat == expected


@pytest.mark.parametrize("name,expected", [
    ("평촌수약국", "pharmacy"),
    ("스타벅스", DEFAULT_CATEGORY),           # 카페 키워드 없음. products 없으면 default.
    ("카페디어디디", "cafe"),
    ("살롱드니즈", "beauty"),
    ("이름없음", DEFAULT_CATEGORY),
])
def test_category_mapper_name_fallback(name, expected):
    cat, _src = map_category(products=[], merchant_name=name)
    assert cat == expected


# ---------- importer dry-run ----------

def test_dry_run_produces_anyang_stats_only():
    report = run_dry_run(file_path=FIXTURE, region="anyang")
    # source 13 rows.
    assert report.source_rows == 13
    # 안양 지역만 anyang_total 로 카운트. 서울/부산은 제외.
    assert report.anyang_total >= 8
    # 새 로직: 시장명 기반 매칭 우선.
    #   fixture 상 "안양중앙시장" 매핑 = manan, 나머지 미지의 시장은 unknown.
    #   주소 기반 fallback 은 상세 시군구 있는 경우만.
    assert report.anyang_manan + report.anyang_dongan + report.anyang_unknown >= 8
    assert report.anyang_dongan >= 3    # 동안구 상세 주소 기반 fallback
    # 좌표는 온누리 원본에 없음 → 모두 geocode 필요.
    assert report.coord_valid == 0
    assert report.geocode_required == report.anyang_total
    # 스펙 §결정 2 — marketName 은 category 결정 제외.
    # 시장 소속이라도 products 로 판단하므로 market 카테고리 자체가 등장하지 않을 수 있음.
    # 대신 product_keyword 로 매핑된 항목이 존재해야 함.
    assert report.category_source_counts.get("product_keyword", 0) >= 1
