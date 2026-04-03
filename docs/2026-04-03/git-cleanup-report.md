# Git 레포지토리 정리 보고서

**일자**: 2026-04-03  
**대상**: `macximin/devdev` (글도비)  
**작업자**: wjjo + Claude

---

## 배경

레포 전체 약 9.5GB, `.git`만 2.3GB로 GitHub 권장 한도를 초과.  
과거 커밋에 대용량 바이너리(zip, pptx, csv, mp4 등)가 포함되어 있었고, 더 이상 추적할 필요 없는 실험/임시 파일이 다수 존재.

---

## 작업 내역

### 1단계: 추적 해제 및 정리

| 항목 | 내용 |
|------|------|
| `.gitignore` 보강 | `docs/이전/`, `*.csv`, `projects/canary_*/`, `projects/스트레스*/`, `tmp_*.db` 추가 |
| 아카이브 이동 | 04-03 이전 날짜 폴더 + `00_ppt/` + `mmmm/` → `docs/이전/` |
| 추적 해제 | `git rm --cached`로 대용량/실험 파일 **3,010개** 제거 |
| 브랜치 머지 | `ops/process-standardization` → `main` 머지 완료 |

### 2단계: 히스토리 재작성

| 항목 | 내용 |
|------|------|
| 도구 | `git filter-repo` |
| 대상 | docs 하위 대용량 바이너리 (zip, pptx, csv, mp4 등) |
| 결과 | 과거 커밋에서 해당 파일 참조 완전 제거 |

### 3단계: 압축 및 배포

| 항목 | Before | After |
|------|--------|-------|
| `.git` 크기 | 2.1GB | **429MB** |
| repack | - | `git repack -a -d -f && git prune` |
| force push | - | `git push --force --set-upstream origin main` 성공 |
| zip 삭제 | `geuldobi-desktop.zip` 1.5GB | 삭제 완료 |

---

## 최종 상태

| 항목 | 값 |
|------|-----|
| 전체 레포 크기 | **8.7GB** (워킹 디렉토리 ~8.3GB + .git 429MB) |
| `.git` 크기 | **429MB** (기존 대비 **-80%**) |
| 브랜치 | `main` — origin과 동기화 완료 |
| 최신 커밋 | `0481b62e` |
| 데이터 손실 | 없음 |

---

## 정리 가능 브랜치 (선택)

| 브랜치 | 상태 |
|--------|------|
| `devdev` | main에 전부 머지됨 → 삭제 가능 |
| `ops/stage0-bi-tr` | cherry-pick으로 main에 반영됨 → 삭제 가능 |
| `ops/process-standardization` | main에 머지 완료 → 삭제 가능 |
