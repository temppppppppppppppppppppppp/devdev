# ROL Global Live-Run Evidence Manifest

Date: 2026-03-20
Status: final
Canonical Path: `docs/2026-03-20/rol-global-live-run-evidence-manifest.md`
Related Order: `docs/2026-03-20/rol-global-live-run-merge-audit-order.md`
Related Watchlist: `docs/2026-03-20/rol-global-live-run-preflight-watchlist.md`
Related Fixture Audit: `docs/2026-03-20/rol-live-run-fixture-target-selection-audit.md`

## 1. Purpose

이 문서는 bounded live-merge run에서 실제로 실행한 command, 사용한 disposable fixture, terminal state, 생성 artifact를 사실 위주로 기록한다.

## 2. Fixture Lineage

### 2.1 Original path before restore

- original target:
  `projects/코덱스_테스트`
- preserved backup:
  `projects/코덱스_테스트__pre_live_merge_backup_20260320_092815`

### 2.2 Seed-based disposable fixture

- source:
  `dist/workspace-seed/projects/investment_canary_demo`
- restored target:
  `projects/코덱스_테스트`
- captured after R1/R2/R4:
  `projects/코덱스_테스트__seed_live_run_capture_20260320_092956`

### 2.3 Richer disposable fixture for R3

- source:
  `projects/0_260318`
- replacement target:
  `projects/코덱스_테스트`
- purpose:
  unblock `run_stage3_smoke.py` which requires `arcs >= 3`

## 3. Executed Commands

### R1. Desktop Spike

Command:
- `cd geuldobi-desktop`
- `npm run start:desktop-spike`

Terminal state:
- `booted-and-visible`

Observed facts:
- Electron app booted
- backend server started on `127.0.0.1:8300`
- main window switched to `backend-idle`
- auto-close after 5000ms executed

### R2. Stage 2 Smoke

Command:
- `python scripts/run_stage2_smoke.py`

Disposable fixture:
- seed-based clone (`investment_canary_demo` derived)

Terminal state:
- `completed-with-degraded-output`

Observed facts:
- Bible loaded
- script reported `plot_roadmap 60 blocks`
- script completed and exported:
  - `plans/arcs/arc_1.json`
  - `plans/arcs/arc_2.json`
- log side effect observed:
  - `logs/arc_3_failure_report.txt`
- warning stream included repeated:
  - `perf_timer start failed`
  - `PF-1 previous_attempt.fix_scope missing`
  - `TF-25-08 Flow Guard REJECT`

### R3. Stage 3 Smoke — first attempt

Command:
- `python scripts/run_stage3_smoke.py`

Disposable fixture:
- seed-based clone (`investment_canary_demo` derived)

Terminal state:
- `failed-precondition`

Observed facts:
- failure:
  `AssertionError: arcs must be >= 3, got 2`

### R3b. Stage 3 Smoke — rerun

Command:
- `python scripts/run_stage3_smoke.py`

Disposable fixture:
- richer clone from `projects/0_260318`

Terminal state:
- `completed`

Observed facts:
- script loaded `arcs=3`
- script completed and exported:
  - `plans/blueprints/bp_ep_1.json`
  - `plans/blueprints/bp_ep_2.json`
  - `plans/blueprints/bp_ep_3.json`

### R4. Stage 4 Smoke

Command:
- `python scripts/run_stage4_smoke.py`

Disposable fixture:
- seed-based clone (`investment_canary_demo` derived)

Terminal state:
- `completed`

Observed facts:
- script precheck passed with `arcs=2`, `blueprints=7`
- existing manuscripts were cleared from DB
- script wrote:
  - `plans/manuscripts/ep_0001.txt`
  - `plans/manuscripts/ep_0002.txt`
  - `plans/manuscripts/ep_0003.txt`
  - `plans/manuscripts/manuscript_ep1.json`
  - `plans/manuscripts/manuscript_ep2.json`
  - `plans/manuscripts/manuscript_ep3.json`
- terminal summary:
  - `manuscripts saved=3`
  - `next_ep=4`

## 4. Produced Evidence Surfaces

### Seed run capture

From `projects/코덱스_테스트__seed_live_run_capture_20260320_092956`:

- `plans/arcs/arc_1.json`
- `plans/arcs/arc_2.json`
- `plans/manuscripts/ep_0001.txt`
- `plans/manuscripts/ep_0002.txt`
- `plans/manuscripts/ep_0003.txt`
- `plans/manuscripts/manuscript_ep1.json`
- `plans/manuscripts/manuscript_ep2.json`
- `plans/manuscripts/manuscript_ep3.json`
- `logs/arc_3_failure_report.txt`

### R3 richer fixture result

From current `projects/코덱스_테스트`:

- `plans/blueprints/bp_ep_1.json`
- `plans/blueprints/bp_ep_2.json`
- `plans/blueprints/bp_ep_3.json`

## 5. Live Checks Used

- seed-based fixture pre-run:
  - `bible=True`
  - `arcs_list=2`
  - `latest_blueprint_number=7`
  - `next_episode_number=7`
- richer fixture pre-run:
  - `bible=True`
  - `arcs_list=3`
  - `latest_blueprint_number=11`
  - `next_episode_number=3`

## 6. Immediate Evidence-Only Conclusions

- desktop spike succeeded
- Stage 2 smoke did not fully satisfy a 3-block expectation on the seed-based fixture
- Stage 3 smoke is not compatible with the seed-based fixture as-is because `arcs=2`
- Stage 4 smoke is compatible with the seed-based fixture
- a richer disposable fixture can unblock Stage 3 smoke without mutating the original historical project directly

## 7. Guardrail

이 manifest는 evidence inventory다.
정책 판단이나 final severity는 `post-run merge audit`에서만 수행한다.
