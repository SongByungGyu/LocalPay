# 09. MVP 검수 체크리스트

## A. 앱 실행

- [ ] Debug build 성공
- [ ] Crash 없이 앱 시작
- [ ] 지도 탭이 기본 화면
- [ ] Bottom Navigation 4개 동작

## B. 위치

- [ ] 최초 위치 권한 UX 존재
- [ ] 허용 시 현재 위치 이동
- [ ] 거절 시 앱 사용 가능
- [ ] 영구 거절 시 설정 이동 안내 가능

## C. 지도

- [ ] 가맹점 marker 표시
- [ ] 온누리/지역화폐/둘 다 구분
- [ ] marker 선택 가능
- [ ] 선택 매장 peek card 표시
- [ ] 지도 이동 후 재검색 UX
- [ ] 많은 marker cluster 또는 대체 처리

## D. 필터

- [ ] 전체
- [ ] 온누리
- [ ] 지역화폐
- [ ] 둘 다
- [ ] 카테고리 선택
- [ ] 결제수단+카테고리 조합
- [ ] 필터 후 marker/list 결과 일치

## E. 검색

- [ ] 가게명 검색
- [ ] 상품명 검색
- [ ] 카테고리 검색
- [ ] 검색 결과 상세 이동
- [ ] 검색 Empty UI

## F. 상세

- [ ] 이름
- [ ] 카테고리
- [ ] 주소
- [ ] 거리
- [ ] 결제수단
- [ ] UNKNOWN 상태 표현
- [ ] 상품/품목
- [ ] 최근 확인
- [ ] 후기 preview
- [ ] 즐겨찾기
- [ ] 전화/길찾기 UI

## G. 후기

- [ ] 목록
- [ ] 별점
- [ ] 결제 성공/실패
- [ ] 결제수단
- [ ] 작성 UI
- [ ] 더미/로컬 저장 동작

## H. 즐겨찾기

- [ ] 추가
- [ ] 삭제
- [ ] 목록 반영
- [ ] 앱 재실행 후 유지

## I. MY

- [ ] 내 상품권 영역
- [ ] 개발 더미라면 DEMO 표시
- [ ] production-like mode에서 잔액 연동 준비중 표시
- [ ] 기본 지역 영역
- [ ] 후기/결제인증 메뉴
- [ ] 설정/출처

## J. 상태/품질

- [ ] Loading
- [ ] Empty
- [ ] Error
- [ ] Offline fallback 고려
- [ ] 48dp touch target
- [ ] 색상만으로 상태 구분하지 않음
- [ ] API key Git 미포함
- [ ] 외부 리뷰 크롤링 없음
- [ ] 실제 잔액 우회 조회 없음

## K. 코드 품질

- [ ] Repository interface 분리
- [ ] Dummy repository 교체 가능
- [ ] ViewModel이 SDK 객체에 직접 결합되지 않음
- [ ] Theme token 존재
- [ ] Version Catalog 사용
- [ ] 핵심 unit test 통과

---

# 최종 MVP 승인 조건

A~J의 P0 성격 항목이 완료되고, `./gradlew assembleDebug` 및 프로젝트 테스트가 성공하면 1차 Android Dummy MVP 완료로 판단한다.
