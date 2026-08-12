"""Worker CLI entry point.

사용법:
    python -m worker.cli local-currency --region anyang --limit 100 --dry-run
    python -m worker.cli local-currency --region anyang-manan --limit 200 --dry-run
    python -m worker.cli local-currency --region anyang --fixture fixture.json --dry-run

--dry-run 은 이번 Gate 의 유일한 실행 모드. Production DB 에 어떤 쓰기도 없다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from worker.core.config import load_config
from worker.importers.local_currency.client import REGION_CODES
from worker.importers.local_currency.importer import run_dry_run


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

    args = parser.parse_args(argv)

    if args.command == "local-currency":
        return _cmd_local_currency(args)

    parser.print_help()
    return 2


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
            report = run_dry_run(
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
