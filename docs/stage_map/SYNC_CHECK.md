# stage_map 동기화 체크

> 사용법: `docs/stage_map/SYNC_CHECK.md 읽고 동기화 체크 실행해줘.`

## 먼저 읽을 것
1. `docs/stage_map/README.md`
2. `docs/stage_map/UPDATE_ORDER.md`
3. `docs/stage_map/doc_status.md`

## 체크 원칙
- 현재 기준 truth는 `current workspace code`다.
- 비교 우선순위는 `code > 2026-03-13 consolidated audits > existing stage_map docs`다.
- HEAD commit만 보지 말고 현재 dirty workspace 변경도 같이 본다.

## Step 1. 기준점 파악
- `doc_status.md`에서 active 문서 목록과 마지막 verified metadata를 확인한다.
- 각 active 문서 footer의 `Commit` / `Workspace State` / `Code Sync`가 `doc_status.md`와 일치하는지 먼저 본다.

## Step 2. 변경 파일 수집
- `git status --short`
- `git diff --name-only HEAD`
- 필요하면 `git log --oneline -20`

해석 규칙:
- `git diff --name-only HEAD`는 현재 dirty workspace 기준 변경 surface다.
- last verified commit 이후의 clean delta만이 아니라, 현재 미커밋 변경도 최신화 대상이다.

## Step 3. 변경 파일 -> stage_map 문서 매핑

| 변경된 코드 경로 | 확인할 stage_map 파일 |
|---|---|
| `modules/core/stage0/*`, `modules/core/stage01_helpers.py` | `stage0.md`, `stage1.md` |
| `modules/core/stage2_*.py`, `modules/core/stage2_context.py` | `stage2.md`, `interfaces.md`, `agent_graph.md`, `gotchas.md` |
| `modules/core/stage3_*.py`, `modules/domain/agents/three_phase_blueprint_generator.py` | `stage3.md`, `interfaces.md`, `agent_graph.md`, `gotchas.md` |
| `modules/core/stage4_*.py`, `modules/domain/agents/chief_writer*.py`, `modules/validation/consistency_validator.py` | `stage4.md`, `interfaces.md`, `agent_graph.md`, `gotchas.md` |
| `modules/core/db_manager.py`, `modules/core/project_manager.py` | `interfaces.md`, `runbook.md` |
| `modules/core/services/project_service.py` | `runbook.md` |
| `modules/core/services/ui_service.py` | `stage1.md`, `gotchas.md` |
| `config/settings/validation.yaml`, `modules/core/constants.py` | `metrics_baseline.md`, `stage2.md`, `stage3.md`, `stage4.md`, `gotchas.md` |
| `main_a.py` | `stage0.md`, `stage1.md`, `stage2.md`, `stage3.md`, `stage4.md`, `runbook.md` |

## Step 4. 문서 대조
판단 기준:
- 임계값 / 예산 / 라운드 수 변경 -> `metrics_baseline.md`, 해당 stage 문서
- 함수명 / 진입점 / callback surface 변경 -> 해당 stage 문서와 `agent_graph.md`
- 흐름 / 분기 / verdict semantics 변경 -> 해당 stage 문서, `interfaces.md`, `gotchas.md`
- DB 테이블 / handoff / anchor 의미 변경 -> `interfaces.md`
- rollback / wipe / rewind 의미 변경 -> `runbook.md`
- active footer / 원장 불일치 -> `doc_status.md`, 해당 문서 footer

## Step 5. 보고 형식

```markdown
## stage_map 동기화 체크 결과 (YYYY-MM-DD)

### ✅ 동기화됨
- [파일명]: 현재 workspace code와 문서가 일치함

### ⚠️ 업데이트 필요
- [stage_map 파일]: [불일치 내용]
  - 코드: [실제 값/동작]
  - 문서: [현재 기재된 값/동작]
  - 수정 제안: [한 줄]

### 📝 판단 불가
- [항목]: [이유]
```

## Step 6. 후속 처리
- 사용자가 `고쳐`라고 하면 해당 stage_map 파일을 수정한다.
- 사용자가 보류를 선택하면 `doc_status.md`의 note에 known drift를 남긴다.

## Last Verified
- Date: 2026-03-13
- Commit: `e18f9910`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
