# 03. 디자인 문서 / Design System

## 1. 디자인 방향

### 키워드

- 생활밀착
- 신뢰
- 빠른 탐색
- 친근함
- 과도한 금융앱 느낌 지양
- 지도 위 정보 가독성 최우선

### 제품 인상

“상품권 앱”보다 **“동네 지도/생활 앱”**처럼 보여야 한다.

사용자가 앱을 켠 순간 가장 먼저 봐야 하는 것은 잔액이 아니라 **주변 사용처**다.

---

## 2. 화면 구조 원칙

1. 지도 면적을 크게 유지한다.
2. 필터는 한 손으로 즉시 변경할 수 있어야 한다.
3. 결제수단은 텍스트만이 아니라 Badge/Icon을 함께 사용한다.
4. 상세 정보는 한 화면에 모두 펼치지 않고 섹션으로 나눈다.
5. “지원 안 함”과 “정보 없음”을 시각적으로 구분한다.
6. 사용자 리뷰보다 “실제 결제 확인” 정보를 우선 노출할 수 있다.
7. 접근성: 컬러만으로 상태를 구분하지 않는다.

---

## 3. Color Token 제안

> 실제 브랜드 확정 전 임시 토큰. Compose Theme로 정의한다.

| Token | Value | 용도 |
|---|---|---|
| Primary | #1F8A5B | 브랜드/핵심 CTA |
| PrimaryContainer | #DDF4E8 | 선택 Chip/강조 배경 |
| OnPrimary | #FFFFFF | Primary 위 텍스트 |
| Onnuri | #16A34A | 온누리 배지/핀 |
| LocalCurrency | #F59E0B | 지역화폐 배지/핀 |
| Both | #2563EB | 둘 다 지원 |
| Error | #D92D20 | 오류/최근 실패 경고 |
| Warning | #B54708 | 주의/오래된 정보 |
| TextPrimary | #1C1C1E | 기본 텍스트 |
| TextSecondary | #6B7280 | 보조 텍스트 |
| Border | #E5E7EB | 구분선 |
| Surface | #FFFFFF | 카드/시트 |
| SurfaceSubtle | #F7F8FA | 배경 |
| MapOverlay | #FFFFFF | 지도 Floating UI |

### 컬러 규칙

- 온누리/지역화폐 컬러는 “결제수단 구분” 용도.
- 접근성을 위해 배지에는 반드시 텍스트/아이콘을 포함.
- 선택/비선택 상태의 명암 대비 확보.

---

## 4. Typography

MVP는 Android System Font를 기본으로 사용한다.

| Style | sp | Weight | 용도 |
|---|---:|---|---|
| DisplaySmall | 28 | Bold | MY 잔액/큰 수치 |
| TitleLarge | 22 | Bold | 상세 매장명 |
| TitleMedium | 18 | SemiBold | 섹션 제목 |
| BodyLarge | 16 | Regular | 주요 본문 |
| BodyMedium | 14 | Regular | 리스트/설명 |
| LabelLarge | 14 | SemiBold | 버튼/Chip |
| LabelMedium | 12 | Medium | 배지/보조정보 |
| Caption | 11 | Regular | 출처/갱신시점 |

- 사용자 폰트 배율을 존중한다.
- 주요 버튼 텍스트는 최소 14sp.
- 텍스트 잘림보다 2줄 허용을 우선한다.

---

## 5. Spacing Grid

4dp 기반.

- 4: Icon/text 미세 간격
- 8: 내부 소간격
- 12: Chip/리스트 요소
- 16: 기본 화면 padding
- 20: 카드 내부 큰 간격
- 24: 섹션 간격
- 32: 큰 구간 분리

---

## 6. Radius / Elevation

| Component | Radius |
|---|---:|
| Search Bar | 16dp |
| Filter Chip | 18dp 또는 pill |
| Card | 16dp |
| Bottom Sheet | Top 24dp |
| Badge | 8dp |
| Floating Button | 16dp / circle |

Elevation은 과도하게 사용하지 않는다.

- Search/Floating UI: 2~4dp
- Selected Card: 4~6dp
- 일반 Card: 0~1dp + Border

---

## 7. 핵심 컴포넌트

### 7.1 SearchBar

- 높이 52dp
- 좌우 16dp
- 검색 아이콘 20~24dp
- Placeholder: `가게, 상품, 시장을 검색해보세요`
- 우측 Clear 아이콘

### 7.2 PaymentFilterChip

상태:

- Default
- Selected
- Disabled

라벨:

- 전체
- 온누리
- 지역화폐
- 둘 다

최소 터치 영역 48dp를 확보한다.

### 7.3 CategoryChip

아이콘 + 텍스트.

예:

- 음식
- 카페
- 약국
- 마트
- 시장
- 생활

### 7.4 MerchantMarker

정보 우선순위:

1. 결제수단 타입
2. 선택 상태
3. 클러스터 여부

Marker에 너무 많은 텍스트를 넣지 않는다.

### 7.5 MerchantPeekCard

- 매장명
- 카테고리 · 거리
- 결제수단 Badge
- 대표상품 1~2개
- 즐겨찾기
- 상세로 진입할 시각적 affordance

### 7.6 PaymentBadge

예:

- `온누리`
- `지역화폐`
- `둘 다`
- `정보 확인 필요`

### 7.7 FreshnessBadge

예:

- `최근 결제 확인 · 2일 전`
- `공공데이터 · 2026.08 갱신`
- `정보가 오래됐어요`

---

## 8. 지도 화면 레이아웃 원칙

### Top Stack

```text
16dp
[ Search Bar                 ]
8dp
[전체] [온누리] [지역화폐] [둘 다]
8dp
[전체][음식][카페][약국][마트] →
```

Top UI는 지도 위 floating surface.

### Center/Bottom

- 오른쪽 하단: 현재위치 Floating Button
- 지도 이동 후: 상단/중앙 `이 지역에서 다시 검색`
- Marker 탭 후: Bottom Peek Card
- Bottom Nav가 card와 겹치지 않음

---

## 9. 상세 화면 디자인

### 섹션 순서

1. 매장 헤더
2. 결제 가능 수단
3. 최근 결제 확인
4. 대표 상품/취급 품목
5. 위치/전화/영업정보
6. 후기
7. 데이터 출처/최신성
8. 하단 CTA

### Fixed Bottom Action

- 전화
- 길찾기
- 후기

필요 시 3개 equal width.

---

## 10. Empty / Error 디자인

### Empty

- 아이콘
- 한 줄 제목
- 1~2줄 설명
- 필터 초기화 버튼

### Error

- 기술 오류코드 노출 금지
- 재시도 CTA
- 개발 빌드만 debug detail 표시 가능

---

## 11. Dark Mode

MVP 필수는 아니지만 Theme token은 Light/Dark 확장 가능하게 정의한다.

지도 SDK의 스타일 지원 여부에 따라 별도 검토한다.

---

## 12. 접근성

- 터치 target 최소 48dp
- 중요한 상태는 색 + 텍스트 + 아이콘
- contentDescription 제공
- Map Marker 선택 시 접근 가능한 리스트 대안 제공 고려
- Dynamic Font 대응
- Contrast 기준 충족
