"""raw_onnuri_merchants 및 data_import_runs 에 안전하게 raw 저장.

Idempotency:
  - `row_hash` = SHA1(7 필드 tab-join). 동일 (source_snapshot_date, row_hash) 재삽입은
    UNIQUE 제약으로 자동 skip. 같은 CSV 재실행해도 duplicate 무한 증가 없음.

Transactional:
  - 하나의 트랜잭션 안에서: import_run insert → 각 record upsert → import_run update.
  - 실패 시 자동 rollback.

Metadata:
  - data_import_runs.run_metadata JSONB 에 source dataset id · filename · SHA-256 ·
    파일 크기 · row count · discrepancy 정보 기록.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import asyncpg  # type: ignore
except ImportError:  # pragma: no cover
    asyncpg = None  # writer 는 컨테이너 안에서만 실행

from worker.importers.onnuri.parser import iter_records


@dataclass
class WriteReport:
    run_id: str
    fetched_count: int
    parsed_count: int
    inserted_count: int
    skipped_count: int   # UNIQUE conflict (duplicate) 로 스킵된 수
    invalid_count: int   # parser skip (이름/주소 결측 등)
    error_count: int
    status: str          # succeeded / partial / failed
    metadata: Dict[str, Any]

    def as_text(self) -> str:
        L = []
        L.append(f"[WriteReport] run_id={self.run_id}")
        L.append(f"  status         = {self.status}")
        L.append(f"  fetched        = {self.fetched_count}")
        L.append(f"  parsed         = {self.parsed_count}")
        L.append(f"  inserted       = {self.inserted_count}")
        L.append(f"  duplicate skip = {self.skipped_count}")
        L.append(f"  invalid        = {self.invalid_count}")
        L.append(f"  errors         = {self.error_count}")
        L.append("  metadata:")
        for k, v in self.metadata.items():
            if isinstance(v, dict):
                L.append(f"    {k}:")
                for kk, vv in v.items():
                    L.append(f"      {kk} = {vv}")
            else:
                L.append(f"    {k} = {v}")
        return "\n".join(L)


def _row_hash(row: Dict[str, Any]) -> str:
    """공식 7개 field 를 정렬된 순서로 join → SHA1. Snapshot 내 중복 판별용."""
    keys = [
        "가맹점명", "소속 시장명(또는 상점가)", "소재지",
        "취급품목", "지류형 가맹 여부", "디지털형 가맹 여부", "등록년도",
    ]
    parts = [str(row.get(k, "")).strip() for k in keys]
    joined = "\t".join(parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()


def _compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_dsn(url: str) -> str:
    """DATABASE_URL 이 SQLAlchemy 형식(postgresql+asyncpg://...) 이면 asyncpg 형식으로."""
    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url[len("postgresql+asyncpg://"):]
    return url


async def _run_write(
    *,
    dsn: str,
    csv_path: Path,
    snapshot_date: date,
    region_filter: Optional[str],
    official_metadata_rows: Optional[int] = None,
) -> WriteReport:
    if asyncpg is None:
        raise RuntimeError("asyncpg not installed (worker must run in api container)")

    file_size = csv_path.stat().st_size
    file_sha = _compute_file_sha256(csv_path)

    # 1) 전체 CSV 를 한 번 훑어 통계 · 필터 결과 수집.
    total_parsed = 0
    total_invalid = 0
    exact_dup_hashes: Dict[str, int] = {}
    to_insert: List[Dict[str, Any]] = []   # (region 필터 통과한) raw 매장만

    from worker.importers.onnuri.normalizer import normalize

    def _on_err(_line_no, _exc, _row):
        nonlocal total_invalid
        total_invalid += 1

    for raw in iter_records(csv_path, on_error=_on_err):
        total_parsed += 1
        n = normalize(raw)
        if n is None:
            total_invalid += 1
            continue
        rh = _row_hash(raw.raw_payload)
        exact_dup_hashes[rh] = exact_dup_hashes.get(rh, 0) + 1

        if region_filter == "anyang" and n.anyang_district is None:
            continue
        # region 필터 통과 시 raw insert 대상.
        to_insert.append({
            "row_hash": rh,
            "merchant_name": raw.merchant_name,
            "market_name": raw.market_name,
            "address_sido": raw.address,
            "products_raw": raw.products_raw,
            "supports_paper_raw": raw.supports_paper_raw,
            "supports_digital_raw": raw.supports_digital_raw,
            "registration_year_raw": raw.registration_year_raw,
            "raw_payload": raw.raw_payload,
        })

    exact_dup_groups = sum(1 for c in exact_dup_hashes.values() if c >= 2)
    exact_dup_extras = sum((c - 1) for c in exact_dup_hashes.values() if c >= 2)

    metadata = {
        "source_dataset_id": "3060079",
        "source_filename": csv_path.name,
        "source_snapshot_date": snapshot_date.isoformat(),
        "source_file_size": file_size,
        "source_file_sha256": file_sha,
        "region_filter": region_filter or "none",
        "parsed_row_count": total_parsed,
        "invalid_row_count": total_invalid,
        "exact_duplicate_groups": exact_dup_groups,
        "exact_duplicate_extra_rows": exact_dup_extras,
        "official_metadata_row_count": official_metadata_rows,
        "row_count_discrepancy": (
            official_metadata_rows is not None
            and total_parsed != official_metadata_rows
        ),
    }

    conn = await asyncpg.connect(_normalize_dsn(dsn))
    inserted = 0
    skipped = 0
    errors = 0
    run_id = uuid.uuid4()

    try:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO data_import_runs (
                    id, source, status, fetched_count, parsed_count,
                    inserted_count, updated_count, skipped_count, error_count,
                    run_metadata
                ) VALUES ($1, 'onnuri', 'running', $2, $3, 0, 0, 0, 0, $4::jsonb)
                """,
                run_id, total_parsed, total_parsed - total_invalid,
                json.dumps(metadata, ensure_ascii=False),
            )

            for rec in to_insert:
                try:
                    row_id = uuid.uuid4()
                    result = await conn.execute(
                        """
                        INSERT INTO raw_onnuri_merchants (
                            id, import_batch_id, source_snapshot_date, row_hash,
                            merchant_name, market_name, address_sido, products_raw,
                            supports_paper_raw, supports_digital_raw,
                            registration_year_raw, raw_payload
                        ) VALUES (
                            $1, $2, $3, $4,
                            $5, $6, $7, $8,
                            $9, $10,
                            $11, $12::jsonb
                        )
                        ON CONFLICT (source_snapshot_date, row_hash) DO NOTHING
                        """,
                        row_id, run_id, snapshot_date, rec["row_hash"],
                        rec["merchant_name"], rec["market_name"], rec["address_sido"],
                        rec["products_raw"],
                        rec["supports_paper_raw"], rec["supports_digital_raw"],
                        rec["registration_year_raw"],
                        json.dumps(rec["raw_payload"], ensure_ascii=False),
                    )
                    # asyncpg 는 result 문자열이 "INSERT 0 1" (성공) 또는 "INSERT 0 0" (skip).
                    if result.endswith(" 1"):
                        inserted += 1
                    else:
                        skipped += 1
                except Exception:  # noqa: BLE001
                    errors += 1

            final_status = "succeeded" if errors == 0 else "partial"
            await conn.execute(
                """
                UPDATE data_import_runs
                SET status=$2, finished_at=now(),
                    inserted_count=$3, skipped_count=$4, error_count=$5
                WHERE id=$1
                """,
                run_id, final_status, inserted, skipped, errors,
            )
    finally:
        await conn.close()

    return WriteReport(
        run_id=str(run_id),
        fetched_count=total_parsed,
        parsed_count=total_parsed - total_invalid,
        inserted_count=inserted,
        skipped_count=skipped,
        invalid_count=total_invalid,
        error_count=errors,
        status=final_status,
        metadata=metadata,
    )


def run_write_sync(
    *,
    csv_path: Path,
    snapshot_date: date,
    region_filter: Optional[str] = "anyang",
    official_metadata_rows: Optional[int] = None,
    database_url: Optional[str] = None,
) -> WriteReport:
    """CLI 에서 호출하는 sync wrapper. DATABASE_URL 은 env 또는 인자."""
    dsn = database_url or os.environ.get("DATABASE_URL") or ""
    if not dsn:
        raise RuntimeError("DATABASE_URL 이 세팅되어 있지 않다 (컨테이너 env 확인)")
    return asyncio.run(
        _run_write(
            dsn=dsn,
            csv_path=csv_path,
            snapshot_date=snapshot_date,
            region_filter=region_filter,
            official_metadata_rows=official_metadata_rows,
        )
    )
