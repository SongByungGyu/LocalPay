"""공공데이터포털 · 외부 HTTP API 호출용 얇은 client.

- timeout · retry · exponential backoff
- HTTP status 검증
- Response body 는 캡처하지만 secret 은 요청 URL 에서 마스킹 후 로그
- 실 서비스키 값을 stdout/stderr 에 절대 출력하지 않는다
- 실패 응답을 조용히 빈 값으로 만들지 않는다 (스펙 §6)
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


class ExternalApiError(RuntimeError):
    def __init__(self, message: str, *, status: Optional[int] = None, body_preview: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.body_preview = body_preview

    def __str__(self) -> str:  # pragma: no cover
        parts = [super().__str__()]
        if self.status is not None:
            parts.append(f"status={self.status}")
        if self.body_preview:
            parts.append(f"body={self.body_preview[:200]}")
        return " | ".join(parts)


_SECRET_QUERY_KEYS = ("serviceKey", "ServiceKey", "apikey", "apiKey", "key")


def _mask_url(url: str) -> str:
    """URL 의 serviceKey 등 민감 파라미터 값을 마스킹."""
    masked = url
    for k in _SECRET_QUERY_KEYS:
        masked = re.sub(
            rf"({k}=)[^&]*",
            rf"\1***",
            masked,
        )
    return masked


@dataclass
class HttpResponse:
    url: str          # masked
    status: int
    json_body: Any
    raw_bytes_len: int


class ExternalHttpClient:
    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.5,
    ):
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._backoff = retry_backoff_seconds

    def get_json(self, url: str, params: Dict[str, Any]) -> HttpResponse:
        """
        JSON 응답을 반환하는 GET.
        - retryable: connection error, timeout, 5xx, 특정 4xx (429)
        - non-retryable: 4xx 대부분 → 즉시 throw
        """
        masked = _mask_url(url + "?" + "&".join(f"{k}={_mask_val(k,v)}" for k, v in params.items()))
        last_error: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    resp = client.get(url, params=params)
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_error = e
                self._sleep_backoff(attempt)
                continue

            status = resp.status_code
            body_preview = resp.text[:500]

            # 재시도 대상 status.
            if status == 429 or 500 <= status < 600:
                last_error = ExternalApiError(
                    f"transient status {status}",
                    status=status,
                    body_preview=body_preview,
                )
                self._sleep_backoff(attempt)
                continue

            if 400 <= status < 500:
                raise ExternalApiError(
                    f"client error {status}",
                    status=status,
                    body_preview=body_preview,
                )
            if status < 200 or status >= 300:
                raise ExternalApiError(
                    f"unexpected status {status}",
                    status=status,
                    body_preview=body_preview,
                )

            try:
                data = resp.json()
            except Exception as e:  # noqa: BLE001
                raise ExternalApiError(
                    "response body is not valid JSON",
                    status=status,
                    body_preview=body_preview,
                ) from e

            return HttpResponse(
                url=masked,
                status=status,
                json_body=data,
                raw_bytes_len=len(resp.content),
            )

        # 모든 retry 실패.
        raise ExternalApiError(
            f"failed after {self._max_retries} attempts: {last_error}",
            status=getattr(last_error, "status", None),
            body_preview=getattr(last_error, "body_preview", None),
        )

    def _sleep_backoff(self, attempt: int) -> None:
        # exponential: 1.5^attempt
        time.sleep(self._backoff * attempt)


def _mask_val(k: str, v: Any) -> str:
    if k in _SECRET_QUERY_KEYS:
        return "***"
    return str(v)
