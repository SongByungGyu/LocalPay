"""Kakao Local Keyword Place Search 기반 geocoder.

스펙 §결정 5 준수:
- /v2/local/search/keyword.json 사용 (address search 아님)
- 3단계 fallback query: (name+market+"안양") → (name+"안양") → (name)
- 결과 첫 항목 auto-adopt 금지
- Confidence 4단계: resolved_high / resolved_medium / ambiguous / failed
- LOW confidence 자동 확정 금지

Confidence 판정 후보:
- normalized name similarity (place_name vs merchant_name)
- address_name 에 "안양" 포함 여부
- category 충돌 여부 (온누리 mapped_category vs Kakao category_group_code)
- 결과 후보 수 (1건 vs 다수)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from worker.core.http_client import ExternalApiError, ExternalHttpClient

KAKAO_KEYWORD_ENDPOINT = "https://dapi.kakao.com/v2/local/search/keyword.json"

# 온누리 mapped_category → Kakao category_group_code 정합성 매핑.
# 정확히 일치하는 케이스만. 불확실 페어는 등록하지 않는다.
LOCALPAY_TO_KAKAO_GROUP = {
    "restaurant": {"FD6"},
    "cafe": {"CE7"},
    "pharmacy": {"HP8", "PM9"},   # HP8=병원, PM9=약국. 우리 pharmacy 는 PM9 매칭 시 확정.
    "mart": {"MT1", "CS2"},
    "food": set(),                 # 식품 소매 는 카카오 group 매핑 애매.
    "beauty": set(),
    "life": set(),
    "market": set(),               # (내부 카테고리에는 없음)
    "etc": set(),
}


# ---------- Data classes ----------

@dataclass
class KakaoCandidate:
    """Kakao 응답 documents[i] 를 가볍게 감쌈."""
    place_name: str
    address_name: str
    road_address_name: str
    x: float
    y: float
    category_name: str
    category_group_code: str
    phone: str
    place_url: str


@dataclass
class GeocodeResult:
    """한 온누리 매장 geocode 결과."""
    merchant_name: str
    market_name: Optional[str]

    status: str                  # resolved_high / resolved_medium / ambiguous / failed
    query_used: Optional[str] = None
    api_calls: int = 0

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    matched_place_name: Optional[str] = None
    matched_address_name: Optional[str] = None
    matched_category_group_code: Optional[str] = None
    confidence_score: float = 0.0

    reasons: List[str] = field(default_factory=list)
    candidates_count: int = 0


# ---------- Public API ----------

class KakaoKeywordGeocoder:
    """Kakao Local Keyword Search 기반 geocoder.

    파라미터:
        rest_api_key: Kakao REST API 키 (VPS .env 에서 로드)
        http: 재사용 가능한 http client (retry/backoff 포함)
    """

    def __init__(self, rest_api_key: str, http: Optional[ExternalHttpClient] = None):
        if not rest_api_key:
            raise ValueError("rest_api_key must not be empty")
        self._key = rest_api_key
        self._http = http or ExternalHttpClient()

    def geocode(
        self,
        *,
        merchant_name: str,
        market_name: Optional[str] = None,
        mapped_category: Optional[str] = None,
        anyang_hint: bool = True,
        max_candidates: int = 5,
    ) -> GeocodeResult:
        """3단계 fallback 으로 검색해 confidence 판정."""
        api_calls = 0
        candidates_history: List[tuple[str, List[KakaoCandidate]]] = []

        queries = self._build_queries(merchant_name, market_name, anyang_hint)
        best_matches: List[KakaoCandidate] = []
        used_query: Optional[str] = None

        for q in queries:
            try:
                docs = self._search(q, size=max_candidates)
            except ExternalApiError:
                docs = []
            api_calls += 1
            candidates_history.append((q, docs))
            if docs:
                best_matches = docs
                used_query = q
                break

        if not best_matches:
            return GeocodeResult(
                merchant_name=merchant_name,
                market_name=market_name,
                status="failed",
                query_used=used_query,
                api_calls=api_calls,
                candidates_count=0,
                reasons=["all queries returned 0 results"],
            )

        return self._pick_and_score(
            candidates=best_matches,
            merchant_name=merchant_name,
            market_name=market_name,
            mapped_category=mapped_category,
            api_calls=api_calls,
            query_used=used_query or "",
        )

    # ---------- internals ----------

    def _build_queries(
        self, merchant_name: str, market_name: Optional[str], anyang_hint: bool
    ) -> List[str]:
        # 스펙 §결정 5 - 3단계.
        queries: List[str] = []
        if market_name and anyang_hint:
            queries.append(f"{merchant_name} {market_name} 안양")
        if anyang_hint:
            queries.append(f"{merchant_name} 안양")
        queries.append(merchant_name)
        # 중복 제거 (순서 보존).
        seen = set()
        out = []
        for q in queries:
            q = q.strip()
            if q and q not in seen:
                seen.add(q)
                out.append(q)
        return out

    def _search(self, query: str, *, size: int) -> List[KakaoCandidate]:
        # Kakao REST API 인증 헤더. httpx 로 직접 헤더 전달.
        # ExternalHttpClient 는 headers 미지원 → 별도 httpx 호출.
        import httpx
        resp = httpx.get(
            KAKAO_KEYWORD_ENDPOINT,
            params={"query": query, "size": size},
            headers={"Authorization": f"KakaoAK {self._key}"},
            timeout=10,
        )
        if resp.status_code == 401:
            raise ExternalApiError(
                "unauthorized (401) — KAKAO_REST_API_KEY 확인 필요",
                status=401,
                body_preview=resp.text[:200],
            )
        if resp.status_code == 429:
            raise ExternalApiError(
                "rate limited (429)", status=429, body_preview=resp.text[:200]
            )
        if 400 <= resp.status_code < 500:
            raise ExternalApiError(
                f"client error {resp.status_code}",
                status=resp.status_code,
                body_preview=resp.text[:200],
            )
        if resp.status_code >= 500:
            raise ExternalApiError(
                f"server error {resp.status_code}",
                status=resp.status_code,
                body_preview=resp.text[:200],
            )
        data = resp.json()
        docs = data.get("documents") or []
        return [
            KakaoCandidate(
                place_name=d.get("place_name") or "",
                address_name=d.get("address_name") or "",
                road_address_name=d.get("road_address_name") or "",
                x=float(d["x"]) if d.get("x") else 0.0,
                y=float(d["y"]) if d.get("y") else 0.0,
                category_name=d.get("category_name") or "",
                category_group_code=d.get("category_group_code") or "",
                phone=d.get("phone") or "",
                place_url=d.get("place_url") or "",
            )
            for d in docs
        ]

    def _pick_and_score(
        self,
        *,
        candidates: List[KakaoCandidate],
        merchant_name: str,
        market_name: Optional[str],
        mapped_category: Optional[str],
        api_calls: int,
        query_used: str,
    ) -> GeocodeResult:
        anyang_candidates = [
            c for c in candidates if "안양" in (c.address_name + c.road_address_name)
        ]

        scored: List[tuple[KakaoCandidate, float, List[str]]] = []
        for cand in candidates:
            score = 0.0
            reasons: List[str] = []

            # 1) 상호명 유사도 (max 0.5).
            sim = _name_similarity(merchant_name, cand.place_name)
            score += 0.5 * sim
            reasons.append(f"name_sim={sim:.2f}")

            # 2) 주소 안양 검증 (0.25).
            in_anyang = "안양" in (cand.address_name + cand.road_address_name)
            if in_anyang:
                score += 0.25
                reasons.append("anyang_addr")
            else:
                reasons.append("!anyang_addr")

            # 3) 카테고리 정합성 (0.15).
            if mapped_category and cand.category_group_code:
                ok_set = LOCALPAY_TO_KAKAO_GROUP.get(mapped_category, set())
                if ok_set and cand.category_group_code in ok_set:
                    score += 0.15
                    reasons.append(f"cat_match({cand.category_group_code})")
                elif ok_set:
                    reasons.append(f"cat_mismatch({cand.category_group_code}!∈{sorted(ok_set)})")
                else:
                    reasons.append(f"cat_unknown_mapping({mapped_category})")

            # 4) 단일 후보 보너스 (0.10).
            if len(candidates) == 1:
                score += 0.10
                reasons.append("only_candidate")

            scored.append((cand, min(score, 1.0), reasons))

        # 안양 주소가 있는 후보를 우선. 없으면 전체 정렬.
        pool = anyang_candidates if anyang_candidates else candidates
        pool_scored = [t for t in scored if t[0] in pool]
        pool_scored.sort(key=lambda t: t[1], reverse=True)
        top, top_score, top_reasons = pool_scored[0]

        # 4단계 confidence 판정 (스펙 §결정 5).
        # - resolved_high:   top_score >= 0.75  AND 안양 주소 AND (단일 후보 or 확실히 top)
        # - resolved_medium: top_score >= 0.55  AND 안양 주소
        # - ambiguous:       상위 2개 점수차가 작거나 top_score < 0.55 이지만 안양 후보 존재
        # - failed:          안양 후보 0 or 이름 유사도 매우 낮음
        second_score = pool_scored[1][1] if len(pool_scored) >= 2 else 0.0
        margin = top_score - second_score
        in_anyang = "안양" in (top.address_name + top.road_address_name)

        if not in_anyang:
            status = "failed"
            top_reasons.append("no anyang match in any candidate")
        elif top_score >= 0.75 and margin >= 0.15:
            status = "resolved_high"
        elif top_score >= 0.55 and margin >= 0.05:
            status = "resolved_medium"
        else:
            status = "ambiguous"

        return GeocodeResult(
            merchant_name=merchant_name,
            market_name=market_name,
            status=status,
            query_used=query_used,
            api_calls=api_calls,
            latitude=top.y if status.startswith("resolved") else None,
            longitude=top.x if status.startswith("resolved") else None,
            matched_place_name=top.place_name,
            matched_address_name=top.address_name or top.road_address_name,
            matched_category_group_code=top.category_group_code or None,
            confidence_score=top_score,
            reasons=top_reasons + [f"margin={margin:.2f}"],
            candidates_count=len(candidates),
        )


# ---------- Helpers ----------

_NON_WORD_RE = re.compile(r"[\s\W_]+", re.UNICODE)


def _normalize_name(s: str) -> str:
    return _NON_WORD_RE.sub("", s or "").lower()


def _name_similarity(a: str, b: str) -> float:
    """0.0 ~ 1.0 상호명 유사도.
    - substring 완전 포함이면 강한 매치.
    - 그 외는 문자 집합 Jaccard.
    """
    a_norm = _normalize_name(a)
    b_norm = _normalize_name(b)
    if not a_norm or not b_norm:
        return 0.0
    if a_norm == b_norm:
        return 1.0
    if a_norm in b_norm or b_norm in a_norm:
        return 0.85
    set_a = set(a_norm)
    set_b = set(b_norm)
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0
