"""Kakao geocoder 로직 유닛 테스트 (network 없음)."""
from __future__ import annotations

import pytest

from worker.importers.geocoding.kakao import (
    KakaoCandidate,
    KakaoKeywordGeocoder,
    _name_similarity,
    _normalize_name,
)


def _mk_cand(place, addr, group="", cat_name="", x=126.98, y=37.39):
    return KakaoCandidate(
        place_name=place,
        address_name=addr,
        road_address_name=addr,
        x=x, y=y,
        category_name=cat_name,
        category_group_code=group,
        phone="", place_url="",
    )


class TestNameSimilarity:
    def test_exact_match(self):
        assert _name_similarity("카페디어디디", "카페디어디디") == 1.0

    def test_substring(self):
        assert _name_similarity("카페디어디디", "카페디어디디 안양점") == 0.85
        assert _name_similarity("스타벅스 안양점", "스타벅스") == 0.85

    def test_no_overlap(self):
        s = _name_similarity("전혀다른가게", "옆집식당")
        assert 0.0 <= s <= 0.4

    def test_empty(self):
        assert _name_similarity("", "abc") == 0.0
        assert _name_similarity("abc", "") == 0.0

    def test_normalize_strips_punctuation(self):
        assert _normalize_name("살롱드니즈 범계점") == _normalize_name("살롱드니즈범계점")


class TestQueryBuilder:
    def test_three_stage_with_market(self):
        g = KakaoKeywordGeocoder(rest_api_key="dummy")
        qs = g._build_queries("카페디어디디", "안양1번가 상점가", anyang_hint=True)
        assert qs == [
            "카페디어디디 안양1번가 상점가 안양",
            "카페디어디디 안양",
            "카페디어디디",
        ]

    def test_two_stage_without_market(self):
        g = KakaoKeywordGeocoder(rest_api_key="dummy")
        qs = g._build_queries("평촌수약국", None, anyang_hint=True)
        assert qs == ["평촌수약국 안양", "평촌수약국"]

    def test_no_anyang_hint(self):
        g = KakaoKeywordGeocoder(rest_api_key="dummy")
        qs = g._build_queries("가게", "시장", anyang_hint=False)
        assert qs == ["가게"]


class TestPickAndScore:
    def _geocoder(self):
        return KakaoKeywordGeocoder(rest_api_key="dummy")

    def test_resolved_high_when_anyang_and_single_and_matching(self):
        g = self._geocoder()
        cands = [_mk_cand("평촌수약국", "경기 안양시 동안구 평촌대로 145", group="PM9")]
        r = g._pick_and_score(
            candidates=cands, merchant_name="평촌수약국", market_name=None,
            mapped_category="pharmacy", api_calls=1, query_used="평촌수약국 안양",
        )
        assert r.status == "resolved_high"
        assert r.latitude is not None and r.longitude is not None
        assert r.matched_category_group_code == "PM9"

    def test_ambiguous_when_two_similar_scores(self):
        g = self._geocoder()
        # 안양 주소 후보가 여러 개인데 모두 이름 유사도가 애매.
        cands = [
            _mk_cand("A식당", "경기 안양시 동안구 어디로 1"),
            _mk_cand("B식당", "경기 안양시 만안구 어디로 2"),
            _mk_cand("C식당", "경기 안양시 동안구 어디로 3"),
        ]
        r = g._pick_and_score(
            candidates=cands, merchant_name="이름다른식당", market_name=None,
            mapped_category=None, api_calls=1, query_used="이름다른식당 안양",
        )
        assert r.status in ("ambiguous", "resolved_medium", "failed")

    def test_failed_when_no_anyang_match(self):
        g = self._geocoder()
        # 모든 후보가 안양 주소 아님.
        cands = [
            _mk_cand("어떤가게", "서울특별시 중구 세종대로 100"),
            _mk_cand("다른가게", "부산광역시 수영구 광안해변로 10"),
        ]
        r = g._pick_and_score(
            candidates=cands, merchant_name="어떤가게", market_name=None,
            mapped_category=None, api_calls=1, query_used="어떤가게 안양",
        )
        assert r.status == "failed"
        assert r.latitude is None
        assert "no anyang" in r.reasons[-2].lower() or "no anyang" in " ".join(r.reasons).lower()

    def test_category_mismatch_lowers_score(self):
        g = self._geocoder()
        # mapped_category=pharmacy 인데 kakao 는 FD6(음식점) → 카테고리 mismatch.
        cands = [_mk_cand("이름약국", "경기 안양시 동안구 평촌대로 145", group="FD6")]
        r = g._pick_and_score(
            candidates=cands, merchant_name="이름약국", market_name=None,
            mapped_category="pharmacy", api_calls=1, query_used="이름약국",
        )
        # cat 매칭 실패 → score 감소. 단일 후보 보너스 + 이름/주소 있어 medium 가능.
        assert r.status in ("resolved_medium", "resolved_high", "ambiguous")
        assert "cat_mismatch" in " ".join(r.reasons)


def test_geocoder_rejects_empty_key():
    with pytest.raises(ValueError):
        KakaoKeywordGeocoder(rest_api_key="")
