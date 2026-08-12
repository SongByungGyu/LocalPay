"""표준산업분류(KSIC) → LocalPay MerchantCategory 매핑.

원본 industry_code 는 항상 유지한다 (RawLocalCurrencyRecord.industry_code).
불확실한 코드는 `etc` 로 보내고, 임의 추정하지 않는다 (스펙 §14).

KSIC 대분류 코드 접두 (5자리 코드의 앞 자리 기준):
  47 = 소매업 (마트/편의점/식품 등)
  56 = 음식점 및 주점업
  47811 = 약국 (약사면허 관련)
  87 = 사회복지 서비스업
등.

이번 Gate 는 안양 sample 100건 규모 검증이라 완전 커버리지가 목적이 아니고,
mapping 이 통계적으로 유의미하게 동작하는지 확인이 목적. 실 전국 데이터로
확장할 때 매핑 테이블도 함께 확장한다.
"""
from __future__ import annotations

from typing import Optional

DEFAULT_CATEGORY = "etc"

# 접두어(길이 순 내림차순으로 정렬해 가장 구체적인 것부터 매칭).
KSIC_PREFIX_TO_CATEGORY: tuple[tuple[str, str], ...] = (
    # 약국 (KSIC 47811 · 47812 계열).
    ("47811", "pharmacy"),
    ("47812", "pharmacy"),
    # 카페·비알콜 음료점.
    ("56220", "cafe"),
    ("5622", "cafe"),
    # 음식점 (한식 · 중식 · 양식 · 일식 등 전반).
    ("561", "restaurant"),
    # 이·미용업.
    ("9611", "beauty"),
    ("9612", "beauty"),
    # 종합 소매업 · 슈퍼마켓 · 편의점 계열 → mart.
    ("4711", "mart"),
    ("4712", "mart"),
    # 시장/재래시장 관련 소매.
    ("4719", "market"),
    # 식료품 소매업 → food.
    ("472", "food"),
    # 개인 서비스업 (세탁·수선 등) → life.
    ("9601", "life"),
    ("952", "life"),
)


def map_industry_to_category(industry_code: Optional[str]) -> str:
    if not industry_code:
        return DEFAULT_CATEGORY
    code = str(industry_code).strip()
    if not code:
        return DEFAULT_CATEGORY
    for prefix, cat in KSIC_PREFIX_TO_CATEGORY:
        if code.startswith(prefix):
            return cat
    return DEFAULT_CATEGORY
