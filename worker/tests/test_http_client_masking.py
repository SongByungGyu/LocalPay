"""URL 로그 masking 이 실제 secret 를 감추는지 검증."""
from __future__ import annotations

from worker.core.http_client import _mask_url, _mask_val


def test_mask_service_key_in_url():
    u = "http://apis.data.go.kr/x?serviceKey=REALSECRETVALUE&pageNo=1"
    m = _mask_url(u)
    assert "REALSECRETVALUE" not in m
    assert "serviceKey=***" in m
    assert "pageNo=1" in m


def test_mask_multiple_keys():
    u = "http://x?ServiceKey=abc&other=1&apiKey=xyz"
    m = _mask_url(u)
    assert "abc" not in m
    assert "xyz" not in m
    assert "other=1" in m


def test_mask_val_non_secret_passthrough():
    assert _mask_val("pageNo", 3) == "3"
    assert _mask_val("serviceKey", "SECRET") == "***"
