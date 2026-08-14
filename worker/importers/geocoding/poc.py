"""Kakao geocoding PoC (100건 sample) 오케스트레이션.

- 안양 온누리 매장 1,255건에서 category 분포 반영 stratified sample 100건 선택.
- 각 매장에 대해 KakaoKeywordGeocoder.geocode 호출.
- 4단계 confidence 통계 · category consistency · 안양외 오매칭 · 성공/실패 대표 20건 리포트.
- 1,255건 자동 실행 금지 (사용자 승인 대기, 스펙 §Gate 조건).
"""
from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from worker.importers.geocoding.kakao import GeocodeResult, KakaoKeywordGeocoder
from worker.importers.onnuri.importer import DryRunReport as OnnuriReport
from worker.importers.onnuri.models import NormalizedOnnuriRecord
from worker.importers.onnuri.normalizer import normalize
from worker.importers.onnuri.parser import iter_records

SAMPLE_SIZE_DEFAULT = 100


@dataclass
class KakaoPocReport:
    requested: int
    total_api_calls: int
    resolved_high: int = 0
    resolved_medium: int = 0
    ambiguous: int = 0
    failed: int = 0

    avg_api_calls_per_merchant: float = 0.0

    # 카테고리 정합성: (mapped_category, kakao_group) 조합별 카운트.
    category_consistency: Dict[str, int] = field(default_factory=dict)

    # 안양 밖으로 오매칭된 케이스 수 (address 에 "안양" 없음).
    false_match_outside_anyang: int = 0

    top_success: List[dict] = field(default_factory=list)
    top_failed_or_ambiguous: List[dict] = field(default_factory=list)


def _load_anyang_records(csv_path: Path) -> List[NormalizedOnnuriRecord]:
    """1,255 안양 매장을 정규화된 형태로 로드."""
    records: List[NormalizedOnnuriRecord] = []
    for raw in iter_records(csv_path):
        n = normalize(raw)
        if n and n.anyang_district is not None:
            records.append(n)
    return records


def stratified_sample(
    records: List[NormalizedOnnuriRecord],
    *,
    size: int = SAMPLE_SIZE_DEFAULT,
    seed: int = 20260814,
) -> List[NormalizedOnnuriRecord]:
    """category 분포를 반영해 sample. 각 카테고리에서 비례 추출."""
    by_cat: Dict[str, List[NormalizedOnnuriRecord]] = defaultdict(list)
    for r in records:
        by_cat[r.mapped_category].append(r)

    rng = random.Random(seed)
    total = len(records)
    quota = {cat: max(1, round(len(rs) * size / total)) for cat, rs in by_cat.items()}
    # 반올림 보정: 합이 size 와 일치하도록.
    diff = size - sum(quota.values())
    if diff != 0:
        # 가장 큰 category 에서 조정.
        biggest = max(quota, key=lambda k: quota[k])
        quota[biggest] += diff

    picked: List[NormalizedOnnuriRecord] = []
    for cat, rs in by_cat.items():
        k = min(quota.get(cat, 0), len(rs))
        picked.extend(rng.sample(rs, k))
    rng.shuffle(picked)
    return picked[:size]


def run_poc(
    *,
    csv_path: Path,
    kakao_key: str,
    sample_size: int = SAMPLE_SIZE_DEFAULT,
) -> KakaoPocReport:
    records = _load_anyang_records(csv_path)
    if not records:
        raise RuntimeError("no anyang records — check CSV / classify logic")

    sample = stratified_sample(records, size=sample_size)
    geocoder = KakaoKeywordGeocoder(rest_api_key=kakao_key)

    report = KakaoPocReport(requested=len(sample), total_api_calls=0)
    consistency: Counter = Counter()
    successes: List[GeocodeResult] = []
    failures: List[GeocodeResult] = []

    for i, rec in enumerate(sample, 1):
        res = geocoder.geocode(
            merchant_name=rec.merchant_name_normalized,
            market_name=rec.market_name_normalized,
            mapped_category=rec.mapped_category,
        )
        report.total_api_calls += res.api_calls

        if res.status == "resolved_high":
            report.resolved_high += 1
            successes.append(res)
        elif res.status == "resolved_medium":
            report.resolved_medium += 1
            successes.append(res)
        elif res.status == "ambiguous":
            report.ambiguous += 1
            failures.append(res)
        else:
            report.failed += 1
            failures.append(res)

        # category consistency.
        pair = f"{rec.mapped_category}→{res.matched_category_group_code or '-'}"
        consistency[pair] += 1

        # 안양외 오매칭 감지 (resolved 인데 매칭 주소에 "안양" 없음).
        if res.status.startswith("resolved"):
            if res.matched_address_name and "안양" not in res.matched_address_name:
                report.false_match_outside_anyang += 1

    report.avg_api_calls_per_merchant = (
        report.total_api_calls / max(1, report.requested)
    )
    report.category_consistency = dict(consistency)
    report.top_success = [_to_dict(g) for g in successes[:20]]
    report.top_failed_or_ambiguous = [_to_dict(g) for g in failures[:20]]

    return report


def _to_dict(res: GeocodeResult) -> dict:
    return {
        "merchant_name": res.merchant_name,
        "market_name": res.market_name,
        "status": res.status,
        "matched_place_name": res.matched_place_name,
        "matched_address_name": res.matched_address_name,
        "kakao_group": res.matched_category_group_code,
        "confidence_score": round(res.confidence_score, 2),
        "query_used": res.query_used,
        "api_calls": res.api_calls,
        "candidates": res.candidates_count,
        "reasons": ", ".join(res.reasons),
    }


def format_report(report: KakaoPocReport, sample_records: Optional[List[NormalizedOnnuriRecord]] = None) -> str:
    L: List[str] = []
    L.append("[Kakao PoC — 안양 온누리 100건]")
    L.append(f"  requested             = {report.requested}")
    L.append(f"  resolved_high         = {report.resolved_high}")
    L.append(f"  resolved_medium       = {report.resolved_medium}")
    L.append(f"  ambiguous             = {report.ambiguous}")
    L.append(f"  failed                = {report.failed}")
    L.append(f"  total_api_calls       = {report.total_api_calls}")
    L.append(f"  avg calls / merchant  = {report.avg_api_calls_per_merchant:.2f}")
    L.append(f"  false_match_outside_anyang = {report.false_match_outside_anyang}")
    L.append("")
    L.append("[category consistency — top 15]")
    for pair, c in sorted(report.category_consistency.items(), key=lambda x: -x[1])[:15]:
        L.append(f"  {c:>4}  {pair}")
    L.append("")
    L.append("[성공 대표 20건]")
    for i, s in enumerate(report.top_success, 1):
        L.append(
            f"  {i:>2}. {s['merchant_name']}  [{s['status']}, score={s['confidence_score']}]"
        )
        L.append(
            f"      → {s['matched_place_name']!r} @ {s['matched_address_name']!r}  group={s['kakao_group']}"
        )
    L.append("")
    L.append("[실패/애매 대표 20건]")
    for i, f_ in enumerate(report.top_failed_or_ambiguous, 1):
        L.append(
            f"  {i:>2}. {f_['merchant_name']}  [{f_['status']}]  query={f_['query_used']!r}  candidates={f_['candidates']}"
        )
        if f_["matched_place_name"]:
            L.append(
                f"      → {f_['matched_place_name']!r} @ {f_['matched_address_name']!r}"
            )
        L.append(f"      reasons: {f_['reasons']}")
    return "\n".join(L)
