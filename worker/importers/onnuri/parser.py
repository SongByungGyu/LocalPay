"""온누리 공식 CSV → RawOnnuriRecord 스트리밍 파서.

- Encoding 자동 감지 (utf-8-sig / utf-8 / cp949 / euc-kr 순 시도).
  공공데이터포털 CSV 는 대개 CP949 / EUC-KR.
- 전체 파일을 메모리에 올리지 않는다. `csv.DictReader` 를 iterator 로 사용.
- Header 이름은 관대한 alias 로 매핑 (스냅샷마다 미세 변화 대응).
- 잘못된 행 하나 때문에 전체 실패하지 않는다: yield 실패 시 skip 카운트만 증가.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

from worker.importers.onnuri.models import RawOnnuriRecord

# 각 논리 필드별로 허용하는 CSV header 이름 후보 (whitespace 무시, 대소문자 무시).
HEADER_ALIASES: Dict[str, Tuple[str, ...]] = {
    "merchant_name": ("가맹점명", "상호명", "업소명"),
    "market_name": (
        "소속 시장명(또는 상점가)",
        "소속시장명(또는상점가)",
        "소속 시장명",
        "시장명",
        "상점가",
    ),
    "address": ("소재지", "주소", "가맹점 주소"),
    "products_raw": ("취급품목", "취급 품목", "품목"),
    "supports_paper_raw": (
        "지류형 가맹 여부",
        "지류형가맹여부",
        "지류 가맹 여부",
        "지류형",
    ),
    "supports_digital_raw": (
        "디지털형 가맹 여부",
        "디지털형가맹여부",
        "디지털 가맹 여부",
        "디지털형",
    ),
    "registration_year_raw": ("등록년도", "등록연도", "등록 년도"),
}


class OnnuriParseError(RuntimeError):
    pass


@dataclass
class FileInfo:
    path: Path
    size_bytes: int
    encoding: str
    header: List[str]
    header_map: Dict[str, Optional[str]]   # 논리 필드 → 실제 header 이름 (없으면 None)


def detect_encoding(path: Path) -> str:
    """BOM 우선 검사 후 여러 encoding 으로 sample decode 시도.

    주의: sample decode 로만 판단하면 UTF-8 파일의 4KB 경계에서 multi-byte
    문자가 잘려 UnicodeDecodeError 가 나고 cp949 로 잘못 fallback 될 수 있다.
    → BOM (`EF BB BF`) 이 있으면 무조건 utf-8-sig 확정.
    """
    with path.open("rb") as f:
        head4 = f.read(4)
    if head4[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"
    if head4[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return "utf-16"

    # BOM 없으면 sample 로 시도. 잘림 방지 위해 sample 을 크게.
    with path.open("rb") as f:
        sample = f.read(65536)
    # UTF-8 시도 시 partial multi-byte 잘림을 관용적으로 판정.
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            sample.decode(enc)
            return enc
        except UnicodeDecodeError as e:
            # UTF-8 후보인데 sample 마지막 몇 바이트에서만 잘렸다면 UTF-8 확정.
            if enc == "utf-8" and e.end >= len(sample) - 4:
                return "utf-8"
            continue
    return "cp949"


def _norm_header(name: str) -> str:
    return name.replace(" ", "").replace("\t", "").strip().lower()


def build_header_map(header: List[str]) -> Dict[str, Optional[str]]:
    """CSV 실 header 이름을 논리 필드에 매핑."""
    normalized_to_actual: Dict[str, str] = {}
    for h in header:
        normalized_to_actual[_norm_header(h)] = h

    mapping: Dict[str, Optional[str]] = {}
    for logical, aliases in HEADER_ALIASES.items():
        found = None
        for alias in aliases:
            key = _norm_header(alias)
            if key in normalized_to_actual:
                found = normalized_to_actual[key]
                break
        mapping[logical] = found
    return mapping


def inspect_file(path: Path) -> FileInfo:
    """파일을 읽지 않고 첫 header 만 확인한다 (dry-run 진입 전 진단용)."""
    enc = detect_encoding(path)
    with path.open("r", encoding=enc, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
    return FileInfo(
        path=path,
        size_bytes=path.stat().st_size,
        encoding=enc,
        header=header,
        header_map=build_header_map(header),
    )


def iter_records(
    path: Path,
    *,
    encoding: Optional[str] = None,
    row_filter: Optional[Callable[[Dict[str, Any]], bool]] = None,
    on_error: Optional[Callable[[int, Exception, Dict[str, Any]], None]] = None,
) -> Iterator[RawOnnuriRecord]:
    """
    CSV 를 streaming 으로 읽어 RawOnnuriRecord 를 yield 한다.
    - encoding=None 이면 자동 감지.
    - row_filter(row_dict) → False 이면 skip (예: 안양만 남기기).
    - 한 행 파싱 실패 시 on_error 콜백 호출 후 skip (전체 실패 없음).
    """
    enc = encoding or detect_encoding(path)
    with path.open("r", encoding=enc, newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        header_map = build_header_map(header)
        if not header_map.get("merchant_name") or not header_map.get("address"):
            raise OnnuriParseError(
                f"required columns (가맹점명/소재지) not found. header={header}"
            )

        for line_no, row in enumerate(reader, start=2):
            try:
                if row_filter is not None and not row_filter(row):
                    continue
                yield _row_to_raw(row, header_map)
            except Exception as e:  # noqa: BLE001
                if on_error is not None:
                    on_error(line_no, e, dict(row))
                continue


def _row_to_raw(row: Dict[str, Any], header_map: Dict[str, Optional[str]]) -> RawOnnuriRecord:
    def _get(logical: str) -> Optional[str]:
        actual = header_map.get(logical)
        if not actual:
            return None
        v = row.get(actual)
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    return RawOnnuriRecord(
        merchant_name=_get("merchant_name"),
        market_name=_get("market_name"),
        address=_get("address"),
        products_raw=_get("products_raw"),
        supports_paper_raw=_get("supports_paper_raw"),
        supports_digital_raw=_get("supports_digital_raw"),
        registration_year_raw=_get("registration_year_raw"),
        raw_payload=dict(row),
    )
