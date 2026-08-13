"""LocalPay MerchantCategory 매핑.

우선순위 (스펙 §"결정 2" 준수):
  1. 취급품목 (products) 에 명확한 카테고리 키워드
  2. 가맹점명 (merchant_name) 에 명확한 카테고리 키워드
  3. (향후) Kakao Local category_group_code — geocoding 결과 도입 후
  4. 판단 불가 시 etc

**marketName 은 category 결정에서 제외**한다.
'안양중앙시장' 소속 정육점 은 category=food + marketName="안양중앙시장" 으로 별개 표현.
시장/상점가 소속 여부는 Merchant.market_name 필드로 이미 보존되며 category 가 아니다.

무리한 추론 금지 — 확실치 않으면 반드시 etc.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

DEFAULT_CATEGORY = "etc"

# 각 category 를 확정할 수 있는 키워드. 구체적/명확한 것 우선.
# 순서 중요: 위에서 아래로 검사, 첫 매치 채택.
CATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # 약국 — 매우 구체적.
    ("pharmacy", ("약국", "약품", "의약", "약사")),
    # 카페 · 커피 · 디저트 (배타 우선. restaurant 보다 먼저 검사).
    ("cafe", (
        "카페", "커피", "coffee", "cafe", "라떼", "브런치",
        "에스프레소", "cappuccino", "디저트",
        "케이크", "타르트", "마카롱", "쿠키", "와플", "빙수",
    )),
    # 미용 — 명확한 개인 서비스.
    ("beauty", ("미용", "헤어", "네일", "네일아트", "피부", "메이크업", "살롱", "왁싱", "속눈썹")),
    # 마트 · 편의점 — 종합 소매 규모.
    ("mart", ("마트", "슈퍼", "편의점", "하나로", "이마트", "홈플러스", "롯데마트")),
    # 음식점 (식당/한식/중식/일식/양식/치킨/피자/분식/고기).
    (
        "restaurant",
        (
            "식당", "한식", "중식", "일식", "양식", "분식",
            "치킨", "피자", "파스타", "스테이크", "돈까스", "돈가스",
            "칼국수", "국수", "냉면", "설렁탕", "국밥", "탕",
            "짜장면", "짬뽕", "탕수육",
            "삼겹살", "닭갈비", "갈비", "구이", "고기집", "고깃집",
            "떡볶이", "김밥", "우동", "라면",
            "회", "횟집", "초밥", "스시",
            "베이커리", "빵집", "제과점",
        ),
    ),
    # 식품 소매 (특정 식품점, 마트 아닌 것). 판매하는 상품이 곧 식품 재료·가공품.
    (
        "food",
        (
            "청과", "과일", "채소", "농산", "수산", "정육", "정육점",
            "반찬", "김치", "젓갈", "곡물", "쌀", "잡곡",
            "떡집", "떡", "방앗간", "젓", "건어물",
            "돼지고기", "한우", "소고기", "닭고기",
        ),
    ),
    # 생활 서비스 (세탁·수선·인쇄·사진 등).
    ("life", ("세탁", "수선", "사진", "인쇄", "복사", "열쇠", "수리", "표구")),
)


def map_category(
    *,
    market_name: Optional[str] = None,  # 남겨두되 사용하지 않음 (BC).
    products: List[str],
    merchant_name: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Returns:
        (category, source)
        - source: 'product_keyword' | 'name_keyword' | 'default'
    marketName 은 category 결정에서 제외한다 (스펙 §결정 2).
    """
    # 1) 취급품목 매칭 (최우선).
    if products:
        joined = " ".join(products)
        for cat, keywords in CATEGORY_KEYWORDS:
            for kw in keywords:
                if kw in joined:
                    return cat, "product_keyword"

    # 2) 가맹점명 키워드 매칭.
    if merchant_name:
        for cat, keywords in CATEGORY_KEYWORDS:
            for kw in keywords:
                if kw in merchant_name:
                    return cat, "name_keyword"

    # 3) Kakao Local category_group_code 는 geocoding 도입 후 여기 삽입 예정.

    # 4) 판단 불가.
    return DEFAULT_CATEGORY, "default"
