# ROL Global Live-Run Preflight Watchlist

Date: 2026-03-20
Status: draft-live-run-pending
Canonical Path: `docs/2026-03-20/rol-global-live-run-preflight-watchlist.md`
Related Order: `docs/2026-03-20/rol-global-live-run-merge-audit-order.md`
Related Survey Backbone: `docs/2026-03-20/rol-global-integrity-survey-3pass-audit.md`
Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: 128 tracked/other, 17 untracked; hotspots: geuldobi-desktop/, modules/core/, modules/domain/agents/, docs/2026-03-20/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose

이 문서는 `desktop spike + Stage2/3/4 smoke` 실행 전에

- 무엇을 볼지
- 어떤 evidence를 남길지
- 무엇이 현재 blocking인지

를 고정하기 위한 preflight watchlist다.

이 문서는 final conclusion이 아니다.
run 완료 전까지는 draft-live-run-pending 상태를 유지한다.

## 2. Current Preflight Reality

live workspace 확인 결과:

- fixture project root exists:
  - `projects/코덱스_테스트`
- but smoke scripts의 핵심 prerequisite는 현재 비어 있다:
  - `projects/코덱스_테스트/project_data.db` → missing
  - `projects/코덱스_테스트/plans/arcs` → missing
  - `projects/코덱스_테스트/plans/blueprints` → missing
  - `projects/코덱스_테스트/plans/manuscripts` → missing
- existing operator log surface:
  - `projects/코덱스_테스트/logs/` exists
  - at least one legacy session log is present

즉:
- `R1 desktop spike`는 바로 가능
- `R2/R3/R4 smoke`는 현재 상태 그대로는 blocked 가능성이 높다

## 3. Blocking Gates

### BG-1. Stage 2/3/4 smoke fixture DB missing

Affected lanes:
- R2 `python scripts/run_stage2_smoke.py`
- R3 `python scripts/run_stage3_smoke.py`
- R4 `python scripts/run_stage4_smoke.py`

Reason:
- 세 script 모두 `projects/코덱스_테스트/project_data.db` 존재를 전제로 assert한다

Temporary bound:
- DB가 복구되거나 fixture seed가 다시 준비되기 전까지 smoke run success/failure를 시스템 의미로 읽지 않는다

Closure action:
- preferred:
  `dist/workspace-seed/projects/investment_canary_demo`를 temporary fixture clone으로
  `projects/코덱스_테스트`에 복구
- reference:
  `docs/2026-03-20/rol-live-run-fixture-target-selection-audit.md`

### BG-2. Downstream plan artifact dirs absent

Affected lanes:
- R2 arcs export
- R3 blueprint export
- R4 manuscript export

Reason:
- script가 생성하긴 하지만, 현재는 baseline artifact truth가 비어 있다

Temporary bound:
- run 후 생성 여부 자체를 evidence로 본다

## 4. Lane Watchlist

## R1. Desktop Spike

Command:
- `cd geuldobi-desktop`
- `npm run start:desktop-spike`

Watch:
- Electron app boot
- preload bridge attach
- bridge backend boot on port `8300`
- renderer quality/operator surfaces render
- office tab blank/resize regression
- prompt overlay shell state and desktop shell errors

Evidence to capture:
- desktop console output
- bridge server boot logs if visible
- operator-visible shell screenshot or observation note
- any startup error modal or blank surface note

Terminal-state markers:
- `booted-and-visible`
- `booted-with-render-degradation`
- `backend-boot-failed`
- `renderer-failed`

## R2. Stage 2 Smoke

Command:
- `python scripts/run_stage2_smoke.py`

Watch:
- fixture DB availability
- Stage2 arc generation completion
- writes to fixture DB
- exports under `plans/arcs/`
- tactical_doc / arc JSON persistence

Evidence to capture:
- full stdout/stderr
- whether `project_data.db` precondition failed
- created/updated files under `projects/코덱스_테스트/plans/arcs/`
- any new DB/log side effects

Terminal-state markers:
- `blocked-missing-db`
- `completed`
- `failed-runtime`

## R3. Stage 3 Smoke

Command:
- `python scripts/run_stage3_smoke.py`

Watch:
- blueprint path completion
- Stage3 quality signal persistence
- writes to fixture DB
- exports under `plans/blueprints/`
- PASS/PASS_WITH_WARNING surface behavior if visible

Evidence to capture:
- full stdout/stderr
- whether fixture prerequisites are missing
- created/updated files under `projects/코덱스_테스트/plans/blueprints/`
- any dashboard-related sink updates

Terminal-state markers:
- `blocked-missing-db`
- `completed`
- `failed-runtime`

## R4. Stage 4 Smoke

Command:
- `python scripts/run_stage4_smoke.py`

Watch:
- manuscript path completion
- Stage4 post-processor writes
- manuscript exports under `plans/manuscripts/`
- proof-facing companion summary behavior if any
- interview/post-processor sink integrity

Evidence to capture:
- full stdout/stderr
- whether fixture prerequisites are missing
- created/updated files under `projects/코덱스_테스트/plans/manuscripts/`
- any log/summary/proof-facing output

Terminal-state markers:
- `blocked-missing-db`
- `completed`
- `failed-runtime`

## 5. Escalation Triggers

다음 중 하나가 생기면 canary로 올린다.

- smoke blocked 이유가 단순 fixture missing이 아님
- smoke completed인데 sink/artifact truth가 어긋남
- desktop shell과 backend state가 어긋남
- Stage4 proof-facing sink가 예상과 다름

Escalation targets:
- `scripts/run_stage4_canary.py`
- `scripts/run_stage34_canary.py`
- `scripts/e2e_menu_smoke.ps1`

## 6. Evidence Capture Contract

run 전에 기록:
- current blocking state
- current fixture project existence
- current missing prerequisites

run 중 기록:
- raw terminal output
- created files and paths
- DB/log/sink observations
- operator shell observations

run 후 기록:
- lane별 terminal-state marker
- smoke vs expected side-effect diff
- escalation 여부와 이유

## 7. Immediate Next Action

다음 실제 작업 순서:

1. `BG-1` 해소 여부 판단
2. preferred path면 seeded project clone으로 `projects/코덱스_테스트` 복구
3. 가능하면 `R1 desktop spike` 먼저 수행
4. fixture DB가 준비되면 `R2 -> R3 -> R4`
5. evidence manifest 작성
6. post-run merge audit로 이동

## 8. Confidence

현재 confidence: `0.95`

근거:
- live-run harness와 current run entrypoints를 직접 재확인했다
- smoke script 3개와 desktop package script를 직접 읽었다
- fixture project actual existence/missing prerequisites를 live filesystem으로 확인했다
- 아직 run 전이므로 결과 해석 confidence는 아니라, preflight watchlist confidence만 의미한다
