# 04. UI 규격서 — Android / Jetpack Compose

> 단위: dp, 텍스트: sp

## 1. 공통 Layout

### Screen

- Width: device width
- Top safe area: system bars 고려
- Bottom safe area: gesture/navigation bar 고려
- 기본 horizontal padding: 16dp
- 기본 section gap: 24dp

### Bottom Navigation

- 높이: NavigationBar 기본 Material 3 규격 사용
- Item 4개: 지도 / 검색 / 즐겨찾기 / MY
- Icon: 24dp
- Label: 12sp

---

# 2. MAP-01 지도 홈 상세 규격

## 2.1 Search Bar

- 위치: Top 12~16dp
- 좌우 margin: 16dp
- height: 52dp
- radius: 16dp
- background: Surface
- elevation: 3dp
- leading icon: 22dp
- horizontal content padding: 14dp

텍스트:

- placeholder 14~16sp
- single line

## 2.2 Payment Filter Row

- Search Bar 아래 8dp
- horizontal scroll 허용
- 좌우 content padding 16dp
- chip height: 36dp visual / 48dp touch
- chip gap: 8dp

## 2.3 Category Row

- Payment Filter 아래 4~8dp
- horizontal scroll
- icon 16~18dp
- chip gap 8dp

## 2.4 Map

- Top UI 뒤 전체 available area
- Bottom Navigation까지 full bleed
- 지도 content padding을 사용해 로고/컨트롤/peek card가 겹치지 않게 한다.

## 2.5 Current Location FAB

- 48 x 48dp
- right: 16dp
- bottom: PeekCard 미노출 24dp + BottomNav 높이 고려
- PeekCard 노출 시 카드 상단으로 이동

## 2.6 Search This Area Button

- height: 40dp
- pill radius
- horizontal padding: 16dp
- 지도 카메라가 기존 조회 bounds에서 일정 이상 이동했을 때 표시

## 2.7 Marker

개별 marker 권장 visual size:

- normal: 36~40dp
- selected: 44~48dp
- cluster: 44~56dp

Marker에 `온`, `지` 같은 한 글자만 사용하지 말고 아이콘/형태로 구분한다.

## 2.8 Merchant Peek Card

- width: screen - 32dp
- min height: 132dp
- bottom: BottomNav + 12dp
- radius: 18dp
- inner padding: 16dp

구성:

```text
[가게명                       ♡]
[카테고리 · 350m]
[온누리] [안양사랑페이]
[삼겹살] [목살]
최근 결제 확인 3일 전
```

매장명 17~18sp SemiBold.

---

# 3. SRH-01 검색 화면

## Search Input

- top fixed
- height 52dp
- Back icon 24dp
- Clear icon 20dp

## Recent Search

- section title 18sp
- 최근 검색어 chip/list
- 전체 삭제 action 13~14sp

## Result Row

- min height: 108dp
- horizontal padding 16dp
- vertical padding 14dp
- thumbnail은 MVP에서는 생략 가능
- Divider 또는 Card 중 하나만 선택해 일관성 유지

Row:

```text
매장명                       350m
카테고리
[온누리] [지역화폐]
대표상품1 · 대표상품2
최근 확인 3일 전
```

---

# 4. DET-01 상세 화면

## App Bar

- TopAppBar 56dp
- Back / Favorite

## Header

- padding 20dp
- 매장명 22sp Bold
- 카테고리/거리 14sp

## Payment Section

- Card 또는 SurfaceSubtle 배경
- padding 16dp
- title 18sp SemiBold
- Badge wrap layout

## Freshness Card

- margin top 12dp
- 최근 사용자 결제 확인을 한 줄 우선 노출

## Product Section

- Chip wrap
- chip height 32~36dp
- 최대 6개 노출 후 `더보기`

## Info Row

각 row:

- min height 48dp
- icon 20dp
- label/content 14~16sp

## Review Card

- avatar 32dp optional
- rating
- payment verification tag
- body max 3 lines preview

## Bottom CTA

- container min height 72dp + safe area
- 3 actions
- 각 button 최소 48dp height

---

# 5. REV-02 후기 작성

- 전체 화면 또는 ModalBottomSheet
- 별점 target 40dp 이상
- 결제 경험 segmented control/chips
- 결제수단 multi-select
- 구매상품 TextField
- 후기 TextField min 120dp
- Submit button 52dp

Validation:

- 별점 미입력 → submit disabled 또는 inline message
- 후기 10자 미만 정책은 MVP에서 강제하지 않아도 됨

---

# 6. FAV-01 즐겨찾기

## List Row

- min 96dp
- 매장명
- 거리
- 결제수단
- 대표품목
- bookmark/favorite action

Swipe delete는 필수가 아니다.

---

# 7. MY-01

## Profile

- padding 20dp
- avatar optional 44dp
- 로그인 전/후 상태 분리 가능

## Wallet Summary

Card:

- radius 20dp
- padding 20dp
- title: `내 상품권`
- 각 상품권 row 56~64dp

Development Dummy:

```text
디지털 온누리        128,500원
안양사랑페이           43,200원
```

반드시 `DEMO` 또는 `더미` 표시.

Production MVP:

```text
디지털 온누리        잔액 연동 준비중
안양사랑페이          잔액 연동 준비중
```

## Menu Row

- min height 56dp
- icon 22dp
- label 15~16sp
- trailing chevron

---

# 8. Component State 규격

## Chip

- Default
- Selected
- Pressed
- Disabled

## Button

- Enabled
- Pressed
- Loading
- Disabled

## Merchant Data State

- Fresh: 최근 사용자 확인 또는 최신 소스
- Normal
- Stale: 업데이트 오래됨
- Unknown

---

# 9. Animation

MVP 최소 애니메이션:

- Filter selection: 150~200ms
- Peek card 등장: slide/fade 200~250ms
- Favorite: scale 100~150ms
- Cluster zoom: 지도 SDK 기본 animation

과도한 animation 금지.

---

# 10. Responsive

기준 개발 폭:

- Compact phone: 360dp+
- Typical phone: 390~430dp

Tablet은 MVP 최적화 제외. 깨지지 않게 adaptive layout만 유지.
