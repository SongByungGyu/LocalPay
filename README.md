# LocalPay

> 온누리상품권 · 지역화폐 사용 가능 가맹점을 지도에서 탐색하는 모바일 서비스.
> 사용자가 **"내가 가진 상품권으로 무엇을 어디에서 살 수 있는가"** 를 가장 빠르게 확인할 수 있도록 만드는 것이 목표.

## 저장소 구성 (Monorepo)

```
LocalPay/                        ← 이 저장소 루트
├── LocalPayiOS/                 ← ⭐ iOS 앱 (SwiftUI, iOS 17+)
│   ├── LocalPay.xcodeproj       ← xcodegen 생성
│   ├── LocalPay/                ← Swift 소스
│   ├── project.yml              ← xcodegen 스펙
│   ├── README.md
│   ├── TODO.md
│   ├── API_INTEGRATION.md
│   ├── CLAUDE.md                ← iOS 개발 프롬프트 / 규약
│   └── report/                  ← 완료 보고 문서
│
├── LocalPay_Claude_Handoff/     ← 기획 · 디자인 · 데이터 아키텍처 참고 문서
│   ├── 01_SERVICE_PLANNING.md
│   ├── 02_SERVICE_DEFINITION.md
│   ├── 03_DESIGN_SYSTEM.md
│   ├── 04_UI_SPEC.md
│   ├── 05_REQUIREMENTS_SPEC.md
│   ├── 06_DATA_API_ARCHITECTURE.md
│   ├── 09_ACCEPTANCE_CHECKLIST.md
│   └── prototype/index.html     ← HTML 프로토타입
│
├── backend/                     ← (예정) FastAPI/NestJS 기반 API 서버
├── worker/                      ← (예정) 공공데이터 수집기
├── deploy/                      ← (예정) Docker / VPS 배포
│
├── DEVELOPMENT_WORKFLOW.md      ← 회사·집·VPS 공동 작업 규칙
├── .gitignore
└── README.md                    ← 이 파일
```

- 현재는 **iOS 앱만 구현**되어 있음. 서버·워커는 앞으로 `backend/`, `worker/` 아래에 추가 예정
- 저장소를 monorepo 로 운영하는 이유: iOS/Backend/데이터 스키마의 계약이 한 저장소에서 관리되어야 클라이언트-서버 동기가 안정적

## 현재 iOS 앱 상태

- **Dummy MVP 완료**: 지도 · 검색 · 즐겨찾기 · 상세 · MY · 후기 · DEMO 잔액까지 시뮬레이터에서 종단 흐름 동작
- **외부 라이브러리 없음** (Apple 프레임워크만)
- **50 Swift 파일 · 3,715 라인 · 안양 25개 Dummy 매장**
- 자세한 내용은 [`LocalPayiOS/README.md`](LocalPayiOS/README.md) 와 [`LocalPayiOS/report/REPORT.md`](LocalPayiOS/report/REPORT.md)

## 개발 워크플로

- 회사(사무실): Claude Code + Xcode 로 **iOS** 개발
- 집: Codex 로 **Backend** 개발
- VPS: 개발 X, GitHub main 기준으로만 **배포**
- Source of Truth: **GitHub `main` 브랜치**

자세한 pull → 작업 → push 규칙은 [`DEVELOPMENT_WORKFLOW.md`](DEVELOPMENT_WORKFLOW.md) 참조.

## 기술 스택 (계획)

| 영역 | 스택 |
|---|---|
| iOS | Swift 5.10, SwiftUI, MapKit, CoreLocation, `@Observable` |
| Backend | (예정) FastAPI 또는 NestJS + PostgreSQL(+PostGIS) |
| 데이터 수집 | (예정) 공공데이터포털 · 지자체 API · Kakao Local 보완 |
| 배포 | (예정) Docker Compose + VPS |

## 라이선스

미정.
