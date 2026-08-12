"""Worker configuration (환경변수 로드).

- 실 Service Key 는 오직 환경변수에서만 읽는다. 코드/log/repr 에 절대 출력하지 않는다.
- .env 파일이 있으면 우선 로드 (python-dotenv 없이 직접 파싱).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _load_dotenv_if_exists() -> None:
    """가장 가까운 .env (repo root 또는 deploy/) 를 최소한으로 파싱해 os.environ 에 주입."""
    candidates = [
        Path.cwd() / ".env",
        Path.cwd() / "deploy" / ".env",
        Path(__file__).resolve().parents[2] / "deploy" / ".env",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
        except OSError:
            continue


_load_dotenv_if_exists()


@dataclass(frozen=True)
class WorkerConfig:
    """실행 시 Config snapshot. 개별 필드는 절대 원본 secret 을 직접 노출하지 않는다."""

    data_go_kr_service_key: Optional[str]
    request_timeout_seconds: float = 15.0
    max_retries: int = 3
    retry_backoff_seconds: float = 1.5

    @property
    def has_service_key(self) -> bool:
        return bool(self.data_go_kr_service_key)

    @property
    def masked_key(self) -> str:
        """로그·리포트에 사용할 masked 표현."""
        key = self.data_go_kr_service_key
        if not key:
            return "(NOT SET)"
        if len(key) <= 8:
            return "***"
        return f"{key[:4]}…{key[-4:]} (len={len(key)})"

    def __repr__(self) -> str:  # 실수로도 원본 key 가 log 에 안 나오게.
        return (
            f"WorkerConfig(has_service_key={self.has_service_key}, "
            f"masked_key={self.masked_key})"
        )


def load_config() -> WorkerConfig:
    return WorkerConfig(
        data_go_kr_service_key=os.environ.get("DATA_GO_KR_SERVICE_KEY") or None,
        request_timeout_seconds=float(os.environ.get("WORKER_HTTP_TIMEOUT", "15")),
        max_retries=int(os.environ.get("WORKER_HTTP_RETRIES", "3")),
        retry_backoff_seconds=float(os.environ.get("WORKER_HTTP_BACKOFF", "1.5")),
    )
