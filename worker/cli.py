"""Worker CLI entry point.

사용법:
    # 지역화폐 (Gate 2-A, BLOCKED — docs/LOCAL_CURRENCY_API_BLOCKER.md 참조)
    python -m worker.cli local-currency --region anyang --limit 100 --dry-run
    python -m worker.cli local-currency --region anyang --fixture fixture.json --dry-run

    # 온누리 (Gate 3-A)
    python -m worker.cli onnuri --file /path/to/온누리_20250731.csv --region anyang --dry-run
    python -m worker.cli onnuri --file /path/to/file.csv --region anyang --limit 500 --dry-run

--dry-run 은 이번 Gate 의 유일한 실행 모드. Production DB 에 어떤 쓰기도 없다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from worker.core.config import load_config
from worker.importers.geocoding.poc import format_report as format_poc_report
from worker.importers.geocoding.poc import run_poc as run_kakao_poc
from worker.importers.local_currency.client import REGION_CODES
from worker.importers.local_currency.importer import run_dry_run as run_local_currency_dry_run
from worker.importers.onnuri.importer import run_dry_run as run_onnuri_dry_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="worker", description="LocalPay data importers")
    sub = parser.add_subparsers(dest="command", required=True)

    p_local = sub.add_parser(
        "local-currency",
        help="한국조폐공사 통합 지역화폐 가맹점 (Dataset 15119539)",
    )
    p_local.add_argument(
        "--region",
        required=True,
        help=(
            "지역 alias. 안양은 두 개 구가 있어 세 종류 지원:\n"
            "  anyang → 만안구+동안구 각각 fetch 후 합계\n"
            "  anyang-manan / anyang-dongan → 개별"
        ),
    )
    p_local.add_argument("--limit", type=int, default=100, help="최대 fetch 건수 (dry-run 상한)")
    p_local.add_argument("--page-size", type=int, default=100, help="API pageSize (기본 100)")
    p_local.add_argument("--fixture", type=Path, default=None, help="로컬 JSON fixture 경로 (Key 없을 때 파이프라인 검증용)")
    p_local.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="필수. Gate 2-A 는 dry-run 만 허용. DB 에 어떤 쓰기도 발생하지 않는다.",
    )

    p_onnuri = sub.add_parser(
        "onnuri",
        help="소상공인시장진흥공단 전국 온누리상품권 가맹점 (Dataset 3060079)",
    )
    p_onnuri.add_argument("--file", required=False, type=Path, default=None, help="공식 CSV 파일 경로 (--from-db 시 생략 가능)")
    p_onnuri.add_argument(
        "--region",
        default="anyang",
        choices=["anyang"],
        help="Gate 3-A 는 안양만 지원 (스펙 §14)",
    )
    p_onnuri.add_argument("--limit", type=int, default=None, help="안양 record 상한 (개발/디버깅용)")
    p_onnuri.add_argument("--encoding", default=None, help="CSV encoding 강제 (미지정 시 자동)")
    p_mode = p_onnuri.add_mutually_exclusive_group(required=True)
    p_mode.add_argument(
        "--dry-run",
        action="store_true",
        help="DB 무변경. 통계 · sample 만 출력",
    )
    p_mode.add_argument(
        "--write",
        action="store_true",
        help="Gate 3-B1 이상 — raw_onnuri_merchants 에 실제 저장 (idempotent).",
    )
    p_mode.add_argument(
        "--canonical-dryrun",
        action="store_true",
        help=(
            "Gate 3-B2 — raw → CanonicalMerchantCandidate 변환 dry-run. "
            "canonical merchants 에 INSERT 하지 않고 통계·market aggregation만 출력. "
            "입력은 --file (CSV) 또는 --from-db (raw_onnuri_merchants) 중 선택."
        ),
    )
    p_mode.add_argument(
        "--canonical-write-dryrun",
        action="store_true",
        help="Gate 3-C 사전 검증 — 실제 INSERT 는 하지 않고 기존 canonical 과 충돌만 확인",
    )
    p_mode.add_argument(
        "--canonical-write",
        action="store_true",
        help=(
            "Gate 3-C — raw_onnuri_merchants → canonical merchants INSERT + "
            "merchant_sources 연결. ON CONFLICT DO NOTHING 로 idempotent."
        ),
    )
    p_onnuri.add_argument(
        "--from-db",
        action="store_true",
        help="canonical-dryrun 시 CSV 대신 raw_onnuri_merchants 에서 로드",
    )
    p_onnuri.add_argument(
        "--snapshot-date",
        default="2025-07-31",
        help="스냅샷 기준일 (ISO 8601 YYYY-MM-DD). raw_onnuri_merchants.source_snapshot_date 에 저장",
    )
    p_onnuri.add_argument(
        "--official-metadata-rows",
        type=int,
        default=None,
        help="공식 metadata 상 row count (row_count_discrepancy 판단용, 예: 125589)",
    )

    p_kakao = sub.add_parser(
        "kakao-poc",
        help="Kakao Local Keyword Search PoC — 안양 온누리 sample geocoding (100건 기본)",
    )
    p_kakao.add_argument("--file", required=True, type=Path, help="온누리 CSV 경로")
    p_kakao.add_argument("--sample-size", type=int, default=100)
    p_kakao.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="필수. Kakao 실 API 는 호출되지만 DB 에 쓰지 않고 리포트만 출력",
    )

    args = parser.parse_args(argv)

    if args.command == "local-currency":
        return _cmd_local_currency(args)
    if args.command == "onnuri":
        return _cmd_onnuri(args)
    if args.command == "kakao-poc":
        return _cmd_kakao_poc(args)

    parser.print_help()
    return 2


def _cmd_kakao_poc(args: argparse.Namespace) -> int:
    if not args.dry_run:
        print("ERROR: --dry-run 필수", file=sys.stderr)
        return 2
    if not args.file.is_file():
        print(f"ERROR: file not found: {args.file}", file=sys.stderr)
        return 2

    import os
    key = os.environ.get("KAKAO_REST_API_KEY")
    if not key:
        print(
            "ERROR: KAKAO_REST_API_KEY 가 세팅되어 있지 않다.\n"
            "  - https://developers.kakao.com 에서 앱 만들고 REST API 키 발급 후\n"
            "  - VPS /opt/localpay/deploy/.env 에 KAKAO_REST_API_KEY=<값> 추가",
            file=sys.stderr,
        )
        return 3

    print(f"[cfg] kakao-poc: file={args.file} sample={args.sample_size}")
    try:
        report = run_kakao_poc(
            csv_path=args.file, kakao_key=key, sample_size=args.sample_size
        )
    except Exception as e:  # noqa: BLE001
        print(f"[error] kakao-poc failed: {e}", file=sys.stderr)
        return 1

    print()
    print(format_poc_report(report))
    print()
    print("[gate] Kakao PoC 완료. 1,255건 실행은 사용자 승인 대기.")
    return 0


def _cmd_onnuri(args: argparse.Namespace) -> int:
    # 아래 모드는 raw_onnuri_merchants DB read 로 실행 → --file 불필요.
    from_db_only = (
        (getattr(args, "canonical_dryrun", False) and getattr(args, "from_db", False))
        or getattr(args, "canonical_write", False)
        or getattr(args, "canonical_write_dryrun", False)
    )
    needs_file = not from_db_only
    if needs_file:
        if args.file is None:
            print("ERROR: --file 필수 (또는 --canonical-dryrun --from-db)", file=sys.stderr)
            return 2
        if not args.file.is_file():
            print(f"ERROR: file not found: {args.file}", file=sys.stderr)
            return 2

    if getattr(args, "canonical_dryrun", False):
        return _cmd_onnuri_canonical_dryrun(args)

    if getattr(args, "canonical_write_dryrun", False) or getattr(args, "canonical_write", False):
        return _cmd_onnuri_canonical_write(args)

    if args.dry_run:
        print(f"[cfg] onnuri dry-run: file={args.file} region={args.region} limit={args.limit}")
        try:
            report = run_onnuri_dry_run(
                file_path=args.file,
                region=args.region,
                limit=args.limit,
            )
        except Exception as e:  # noqa: BLE001
            print(f"[error] onnuri dry-run failed: {e}", file=sys.stderr)
            return 1
        print()
        print(report.as_text())
        print()
        print("[gate] Gate 3-A dry-run 완료. Production DB 에는 어떤 쓰기도 발생하지 않았다.")
        return 0

    # --- --write 모드 (Gate 3-B1) ---
    from datetime import date
    from worker.importers.onnuri.writer import run_write_sync

    snapshot = date.fromisoformat(args.snapshot_date)
    print(
        f"[cfg] onnuri --write: file={args.file} snapshot={snapshot} "
        f"region={args.region} official_meta_rows={args.official_metadata_rows}"
    )
    print("  ⚠ raw_onnuri_merchants 에 실제 저장. canonical merchants 및 iOS 는 변경 없음.")
    try:
        report = run_write_sync(
            csv_path=args.file,
            snapshot_date=snapshot,
            region_filter=args.region,
            official_metadata_rows=args.official_metadata_rows,
        )
    except Exception as e:  # noqa: BLE001
        print(f"[error] onnuri write failed: {e}", file=sys.stderr)
        return 1
    print()
    print(report.as_text())
    print()
    print("[gate] Gate 3-B1 write 완료. canonical merchants 는 아직 생성되지 않는다.")
    return 0


def _cmd_onnuri_canonical_dryrun(args: argparse.Namespace) -> int:
    from datetime import date
    from worker.importers.onnuri.canonical_dryrun import (
        run_dryrun_from_csv, run_dryrun_from_db,
    )

    snapshot = date.fromisoformat(args.snapshot_date)
    print(f"[cfg] onnuri --canonical-dryrun: snapshot={snapshot} region={args.region} from_db={args.from_db}")
    print("  ⚠ canonical merchants 에 INSERT 하지 않는다. dry-run 만.")
    try:
        if args.from_db:
            report = run_dryrun_from_db(snapshot_date=snapshot, region=args.region)
        else:
            report = run_dryrun_from_csv(
                csv_path=args.file, snapshot_date=snapshot, region=args.region,
            )
    except Exception as e:  # noqa: BLE001
        print(f"[error] canonical-dryrun failed: {e}", file=sys.stderr)
        return 1
    print()
    print(report.as_text())
    print()
    print("[gate] Gate 3-B2 canonical-dryrun 완료. Production canonical merchants 무변경.")
    return 0


def _cmd_onnuri_canonical_write(args: argparse.Namespace) -> int:
    from datetime import date
    from worker.importers.onnuri.canonical_writer import run_write_sync as run_canonical_write

    snapshot = date.fromisoformat(args.snapshot_date)
    dry_run = getattr(args, "canonical_write_dryrun", False)
    label = "canonical-write-dryrun" if dry_run else "canonical-write"
    print(f"[cfg] onnuri --{label}: snapshot={snapshot} region={args.region}")
    if dry_run:
        print("  ⚠ 사전 검증 (INSERT 없음). 기존 canonical 과의 id 충돌만 확인.")
    else:
        print("  ⚠ 실제 canonical INSERT + merchant_sources 연결 (idempotent).")
    try:
        report = run_canonical_write(snapshot_date=snapshot, dry_run=dry_run)
    except Exception as e:  # noqa: BLE001
        print(f"[error] {label} failed: {e}", file=sys.stderr)
        return 1
    print()
    print(report.as_text())
    print()
    if dry_run:
        print("[gate] Gate 3-C canonical-write-dryrun 완료. Production 무변경.")
    else:
        print("[gate] Gate 3-C canonical-write 완료.")
    return 0


def _cmd_local_currency(args: argparse.Namespace) -> int:
    if not args.dry_run:  # argparse 에서 required=True 지만 안전 이중.
        print("ERROR: --dry-run 필수. Gate 2-A 는 실제 write 를 하지 않는다.", file=sys.stderr)
        return 2

    cfg = load_config()
    print(f"[cfg] {cfg!r}")

    # region alias.
    if args.region == "anyang":
        regions = ["anyang-manan", "anyang-dongan"]
    elif args.region in REGION_CODES:
        regions = [args.region]
    else:
        print(f"ERROR: unknown region: {args.region}. supported: {sorted(list(REGION_CODES)+['anyang'])}", file=sys.stderr)
        return 2

    if not cfg.has_service_key and args.fixture is None:
        print(
            "ERROR: DATA_GO_KR_SERVICE_KEY 가 설정되어 있지 않고 --fixture 도 없다.\n"
            "  - 공공데이터포털에서 Dataset 15119539 활용신청 후 발급된 서비스키를 얻어 VPS `/opt/localpay/deploy/.env` 의\n"
            "    DATA_GO_KR_SERVICE_KEY 에 넣거나\n"
            "  - `--fixture <path.json>` 으로 로컬 sample 응답을 넘겨 파이프라인만 검증할 수 있다.",
            file=sys.stderr,
        )
        return 3

    exit_code = 0
    for r in regions:
        try:
            report = run_local_currency_dry_run(
                service_key=cfg.data_go_kr_service_key or "",
                region=r,
                max_records=args.limit,
                page_size=args.page_size,
                fixture_path=args.fixture,
            )
        except Exception as e:  # noqa: BLE001
            print(f"[error] region={r}: {e}", file=sys.stderr)
            exit_code = 1
            continue

        print()
        print(report.as_text())

    print()
    print("[gate] Gate 2-A dry-run 완료. Production DB 에는 어떤 쓰기도 발생하지 않았다.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
