"""WorkerConfig 가 실제 secret 값을 __repr__ 이나 log 에 노출하지 않는지 검증."""
from __future__ import annotations

from worker.core.config import WorkerConfig


def test_repr_masks_key():
    cfg = WorkerConfig(data_go_kr_service_key="abcdefghij0123456789ZZZZZZZZ")
    s = repr(cfg)
    assert "abcdefghij" not in s
    assert "ZZZZZZ" not in s
    assert "has_service_key=True" in s
    assert "masked_key=" in s


def test_masked_key_short():
    cfg = WorkerConfig(data_go_kr_service_key="short")
    assert cfg.masked_key == "***"


def test_masked_key_none():
    cfg = WorkerConfig(data_go_kr_service_key=None)
    assert cfg.masked_key == "(NOT SET)"
    assert cfg.has_service_key is False
