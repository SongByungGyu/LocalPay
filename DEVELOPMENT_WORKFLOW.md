# Development Workflow

LocalPay 저장소를 여러 기기(회사 · 집 · VPS)에서 안전하게 이어서 개발하기 위한 규칙.

**GitHub `main` 이 항상 Source of Truth** 입니다.

---

## 역할 분리

```
┌──────────────────┐          ┌──────────────────┐
│   회사 (사무실)   │          │       집        │
│  Claude Code     │          │      Codex       │
│      + Xcode     │          │                  │
│   iOS 개발       │          │  Backend 개발    │
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         └─────────┐    push    ┌──────┘
                   ▼            ▼
             ┌──────────────────────┐
             │   GitHub `main`      │
             │  (Source of Truth)   │
             └──────────┬───────────┘
                        │  pull
                        ▼
                 ┌──────────────┐
                 │     VPS      │
                 │  배포 전용    │
                 │ (개발 금지)   │
                 └──────────────┘
```

---

## 회사에서 작업 시작

```bash
# 1) 어제/집에서 push된 변경사항 가져오기
git status                # 로컬 미커밋 확인
git pull --rebase         # 원격 최신 반영

# 2) iOS 작업 (Xcode / Claude Code)
#    파일 추가·이동·삭제한 경우:
cd LocalPayiOS && xcodegen generate

# 3) 빌드 검증
xcodebuild -project LocalPayiOS/LocalPay.xcodeproj -scheme LocalPay \
  -destination 'generic/platform=iOS Simulator' -configuration Debug build

# 4) 커밋 & push
git status
git add <구체적 파일들>          # git add . 는 되도록 지양
git commit -m "ios: <변경 요약>"
git push
```

## 회사에서 작업 종료 전 체크리스트

- [ ] `git status` 가 clean 인가 (미커밋 파일 없음)
- [ ] `.env` / API Key / private key 를 실수로 추가하지 않았는가
- [ ] `git log origin/main..HEAD` 이 비어있는가 (푸시 누락 없음)

---

## 집에서 작업 시작

```bash
# 1) 회사에서 push된 iOS 변경사항 가져오기
git status
git pull --rebase

# 2) Backend 작업 (Codex)
cd backend
# 예: docker compose up -d
#     pnpm install / uv sync

# 3) 커밋 & push
git status
git add <구체적 파일들>
git commit -m "backend: <변경 요약>"
git push
```

---

## VPS 배포

```bash
ssh <VPS>
cd /opt/localpay
git status                    # clean 확인
git pull                      # main 최신 반영

# Backend 재기동
docker compose up -d --build

# NEVER:
#   docker compose down -v   # PostgreSQL 볼륨 파괴됨
#   git reset --hard         # 배포 이력 손실
```

---

## 커밋 메시지 규칙

`<scope>: <변경 요약>` 형태 권장.

| Scope | 예시 |
|---|---|
| `ios` | `ios: 지도 마커 선택 시 하단 프리뷰 추가` |
| `ios(detail)` | `ios(detail): 후기 작성 시트 도입` |
| `backend` | `backend: 가맹점 검색 API 초안` |
| `worker` | `worker: 공공데이터 CSV 임포터 추가` |
| `deploy` | `deploy: docker-compose PostGIS 확장` |
| `docs` | `docs: DEVELOPMENT_WORKFLOW 갱신` |
| `chore` | `chore: .gitignore 에 xcuserdata 추가` |

## 절대 금지 명령 (Git 히스토리 파괴)

```bash
git reset --hard <원격보다 앞선 커밋>    # 상대 작업 소실 위험
git clean -fdx                          # 미추적 파일 전부 삭제
git push --force                        # 원격 히스토리 덮어씀 (main 절대 금지)
git push --force-with-lease             # 위와 동일. 협업 브랜치 금지
```

정말 필요할 때는 새 브랜치를 파고, 원격에는 push 하지 않는다.

---

## 충돌(Conflict) 대응

- 두 기기에서 서로 다른 파일을 건드렸다면 → `git pull --rebase` 만으로 자연스럽게 해결
- **동일 파일 충돌 시 반드시 수동 병합**. 어느 한쪽을 자동으로 버리지 않는다.
- 특히 다음 파일은 자동 해결 금지 (기기별 로컬 상태가 섞일 수 있음):
  - `LocalPayiOS/project.yml` → 병합 후 `xcodegen generate` 재실행
  - `LocalPayiOS/LocalPay.xcodeproj/project.pbxproj` → **되도록 xcodegen 이 재생성**. 수동 편집 지양
  - `README.md`, `.gitignore`, 향후 `backend/compose.yaml`
- 병합 직후:
  ```bash
  git status                   # 충돌 마커 남았는지 확인
  git add <resolved-file>
  git rebase --continue        # 또는 git commit
  ```

---

## Secret 관리

- API Key · DB Password · Token 등은 **절대 커밋 금지**
- 필요하면 `.env` (gitignored) 로 로컬에 두고 `.env.example` 만 커밋
- iOS 에서 키가 필요할 경우: `Secrets.xcconfig` (gitignored) + 참조 pattern

로컬에서 실수로 커밋한 경우:

```bash
# 방금 커밋 (아직 push 전) 되돌리기
git reset --soft HEAD~1
# 파일에서 secret 제거 후 재커밋
```

이미 push 된 경우 → **즉시 해당 키를 회전(rotate) 시키고** history rewrite 여부 별도 판단.

---

## Xcode 프로젝트 파일 규칙

- `LocalPay.xcodeproj` 는 xcodegen 이 재생성
- 파일 추가·이동·삭제 시 **반드시** `xcodegen generate` 실행 후 커밋
- `xcuserdata/`, `*.xcuserstate` 는 gitignore 로 제외됨 (사용자별 UI 상태)
- 병합 충돌이 잦다면 `project.yml` 만 편집하고 `.xcodeproj` 는 재생성

---

## 확인 명령 모음

```bash
# 지금 어디 있는지
git status
git log --oneline --graph --decorate --all -10

# 원격 정보
git remote -v
git branch -vv

# 아직 push 안 된 커밋
git log origin/main..HEAD

# 원격에는 있는데 로컬에 없는 커밋
git log HEAD..origin/main
```
