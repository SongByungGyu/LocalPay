"""market_name + products 문자열로부터 LocalPay MerchantCategory 매핑.

원본 온누리 데이터에는 표준산업분류코드(KSIC) 가 없어서 (지역화폐 API 와 달리)
문자열 키워드로 추정할 수밖에 없다. 확실치 않으면 반드시 `etc` 로 보내고,
category_source 를 함께 반환해 나중에 canonical merge 단계에서
낮은 confidence 매핑을 수동 검토할 수 있게 한다.

무리한 추론 금지 (스펙 §18).
"""
from __future__ import annotations

from typing import List, Optional, Tuple

DEFAULT_CATEGORY = "etc"

# 시장/상점가 이름 힌트. "시장" 이 들어가 있으면 대개 전통시장.
MARKET_KEYWORDS = ("시장", "상점가", "골목형", "재래시장")

# 상품 키워드 매핑. 순서 중요 (구체적인 것 먼저).
PRODUCT_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    # 약국.
    (("약국", "약", "의약"), "pharmacy"),
    # 카페 · 커피.
    (("카페", "커피", "coffee", "cafe", "브런치"), "cafe"),
    # 미용.
    (("미용", "헤어", "네일", "네일아트", "피부", "메이크업"), "beauty"),
    # 마트 · 편의점.
    (("마트", "슈퍼", "편의점", "농협", "하나로"), "mart"),
    # 음식점 계열 (분식/식당/한식/중식/일식/양식/치킨/피자/고기).
    (
        (
            "식당", "분식", "한식", "중식", "일식", "양식", "치킨", "피자",
            "칼국수", "국수", "냉면", "회", "설렁탕", "탕", "국밥",
            "고기", "삼겹살", "돼지", "소고기", "한우", "정육",
            "떡볶이", "김밥", "우동", "라면", "돈까스", "돈가스",
            "베이커리", "빵", "제과",
        ),
        "restaurant",
    ),
    # 식품 (마트가 아니라 특정 식품 소매점).
    (
        (
            "청과", "과일", "채소", "농산", "수산", "정육점", "반찬",
            "떡집", "떡", "김치", "젓갈", "곡물", "쌀", "잡곡",
        ),
        "food",
    ),
    # 생활 서비스 (세탁·수선 등).
    (("세탁", "수선", "사진", "인쇄", "복사", "열쇠"), "life"),
)


def map_category(
    *,
    market_name: Optional[str],
    products: List[str],
) -> Tuple[str, str]:
    """
    Returns:
        (category, source)
        - source: 'market_name' / 'product_keyword' / 'default'
    """
    # market_name 이 "시장/상점가" 이면 market 로 강하게 매핑.
    if market_name:
        low = market_name.lower()
        for kw in MARKET_KEYWORDS:
            if kw in market_name:
                return "market", "market_name"

    # products 키워드 매치.
    joined = " ".join((p or "") for p in products).lower()
    if joined:
        for keywords, cat in PRODUCT_KEYWORDS:
            for kw in keywords:
                if kw.lower() in joined:
                    return cat, "product_keyword"

    return DEFAULT_CATEGORY, "default"
