"""Local currency importer 유닛 테스트.

DB 접근 없이 parser · normalizer · category mapper · client extract logic 만 검증.
공공데이터포털 실제 응답 스키마의 관대한 필드 매핑을 확인한다.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from worker.importers.local_currency.category_mapper import (
    DEFAULT_CATEGORY,
    map_industry_to_category,
)
from worker.importers.local_currency.client import _extract_items
from worker.importers.local_currency.normalizer import normalize
from worker.importers.local_currency.parser import parse_response_items

FIXTURE = Path(__file__).parent / "fixtures" / "anyang_sample.json"


def load_items():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# ---------- category mapper ----------

@pytest.mark.parametrize(
    "code,expected",
    [
        ("47811", "pharmacy"),
        ("47812", "pharmacy"),
        ("56111", "restaurant"),
        ("56129", "restaurant"),
        ("56220", "cafe"),
        ("47211", "food"),   # KSIC 47211 계열 = 식품 소매 → food
        ("47110", "mart"),   # KSIC 4711 계열 = 종합 소매 → mart
        ("96112", "beauty"),
        ("99999", DEFAULT_CATEGORY),
        (None, DEFAULT_CATEGORY),
        ("", DEFAULT_CATEGORY),
    ],
)
def test_category_mapper(code, expected):
    assert map_industry_to_category(code) == expected


# ---------- parser ----------

def test_parser_extracts_all_records():
    items = load_items()
    parsed = parse_response_items(items)
    assert len(parsed) == len(items)
    assert parsed[0].merchant_name == "안양중앙시장 행복정육점"  # whitespace 는 parser 시점에도 trim
    assert parsed[0].latitude == pytest.approx(37.3946)
    assert parsed[0].longitude == pytest.approx(126.9235)
    assert parsed[0].industry_code == "47211"
    assert parsed[0].raw_payload["frcsNo"] == "TEST-0001"


def test_parser_returns_none_for_missing_optional_fields():
    parsed = parse_response_items([
        {"frcsNm": "이름만", "frcsAddr": "주소만"}
    ])
    r = parsed[0]
    assert r.merchant_name == "이름만"
    assert r.phone is None
    assert r.latitude is None
    assert r.industry_code is None


# ---------- normalizer ----------

def test_normalizer_drops_when_name_empty():
    parsed = parse_response_items(load_items())
    # TEST-0009 는 name="" → None 후 normalize None.
    empty_name_records = [r for r in parsed if r.source_merchant_id == "TEST-0009"]
    assert len(empty_name_records) == 1
    assert normalize(empty_name_records[0]) is None


def test_normalizer_drops_when_address_empty():
    parsed = parse_response_items([{"frcsNm": "이름만"}])
    assert normalize(parsed[0]) is None


def test_normalizer_valid_record():
    parsed = parse_response_items(load_items())
    first = normalize(parsed[0])
    assert first is not None
    assert first.merchant_name_normalized == "안양중앙시장 행복정육점"
    assert first.address_normalized.startswith("경기 안양시 만안구")
    assert first.coordinate_valid is True
    assert first.mapped_category == "food"   # fixture indutyCd=47211 (식품 소매) → food
    assert first.supports_local_currency is True
    assert first.supports_onnuri is False


def test_normalizer_phone_formatting():
    parsed = parse_response_items(load_items())
    # TEST-0002 phone "0313876789" (10 digit) → "031-387-6789"
    r = next(x for x in parsed if x.source_merchant_id == "TEST-0002")
    n = normalize(r)
    assert n is not None
    assert n.phone_normalized == "031-387-6789"


def test_normalizer_zero_zero_coordinate_invalid():
    parsed = parse_response_items(load_items())
    r = next(x for x in parsed if x.source_merchant_id == "TEST-0005")
    n = normalize(r)
    assert n is not None
    assert n.coordinate_valid is False
    assert n.coordinate_reason == "zero-zero"
    assert n.latitude is None


def test_normalizer_missing_coordinate():
    parsed = parse_response_items(load_items())
    r = next(x for x in parsed if x.source_merchant_id == "TEST-0006")
    n = normalize(r)
    assert n is not None
    assert n.coordinate_valid is False
    assert n.coordinate_reason == "missing"


def test_normalizer_out_of_range_coordinate():
    parsed = parse_response_items(load_items())
    r = next(x for x in parsed if x.source_merchant_id == "TEST-0007")
    n = normalize(r)
    assert n is not None
    assert n.coordinate_valid is False
    assert "out-of-range" in (n.coordinate_reason or "")


def test_normalizer_unmapped_industry_goes_to_etc():
    parsed = parse_response_items(load_items())
    r = next(x for x in parsed if x.source_merchant_id == "TEST-0008")
    n = normalize(r)
    assert n is not None
    assert n.mapped_category == "etc"


# ---------- client _extract_items ----------

def test_extract_items_service_error_raises():
    from worker.core.http_client import ExternalApiError
    err = {
        "OpenAPI_ServiceResponse": {
            "cmmMsgHeader": {
                "errMsg": "SERVICE_KEY_IS_NOT_REGISTERED_ERROR",
                "returnAuthMsg": "등록되지 않은 서비스키",
                "returnReasonCode": "30",
            }
        }
    }
    with pytest.raises(ExternalApiError):
        _extract_items(err)


def test_extract_items_result_code_error_raises():
    from worker.core.http_client import ExternalApiError
    err = {
        "response": {
            "header": {"resultCode": "22", "resultMsg": "SERVICE_ACCESS_DENIED_ERROR"},
            "body": {},
        }
    }
    with pytest.raises(ExternalApiError):
        _extract_items(err)


def test_extract_items_success_shape():
    body = {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "OK"},
            "body": {
                "totalCount": 3,
                "items": {
                    "item": [
                        {"frcsNm": "A"},
                        {"frcsNm": "B"},
                        {"frcsNm": "C"},
                    ]
                },
            },
        }
    }
    items, total = _extract_items(body)
    assert total == 3
    assert [i["frcsNm"] for i in items] == ["A", "B", "C"]


def test_extract_items_single_item_as_dict():
    body = {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "OK"},
            "body": {
                "totalCount": 1,
                "items": {"item": {"frcsNm": "solo"}},
            },
        }
    }
    items, total = _extract_items(body)
    assert total == 1
    assert items == [{"frcsNm": "solo"}]


def test_client_normalizes_url_encoded_service_key():
    """공공데이터포털 Encoding/Decoding 어느 걸 넣어도 canonical (decoded) 로 보관.
    이중 인코딩 방지."""
    from worker.importers.local_currency.client import LocalCurrencyApiClient
    encoded = "abcd%2Befg%3D%3D"     # 사용자가 Encoding 값을 넣은 케이스
    decoded = "abcd+efg=="            # canonical
    c1 = LocalCurrencyApiClient(service_key=encoded)
    c2 = LocalCurrencyApiClient(service_key=decoded)
    assert c1._service_key == decoded
    assert c2._service_key == decoded


def test_extract_items_items_as_list_directly():
    body = {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "OK"},
            "body": {
                "totalCount": 2,
                "items": [{"frcsNm": "x"}, {"frcsNm": "y"}],
            },
        }
    }
    items, total = _extract_items(body)
    assert total == 2
    assert len(items) == 2
