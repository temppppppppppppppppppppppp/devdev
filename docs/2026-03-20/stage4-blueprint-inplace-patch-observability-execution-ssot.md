# Stage4 Blueprint Inplace Patch Observability Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage4-blueprint-inplace-patch-observability-execution-ssot.md`
Temp Mirror Path: `removed at closure`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: fresh-run project 0_260320, docs/mmmm collector bundle, active smoke-fixture temp mirror, ongoing dated-doc churn`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/rol-global-post-run-merge-audit.md`
- `docs/2026-03-20/rol-live-run-0_260320-evidence-manifest.md`
- `docs/2026-03-20/rol-low-trust-mmmm-intake-triage-3pass-audit.md`
- `docs/2026-03-20/rol-post-run-action-bearing-split-3pass-audit.md`
Evidence Artifacts:
- `projects/0_260320/logs/session/ui_events.jsonl`
- `projects/0_260320/logs/session/decisions.jsonl`
- `projects/0_260320/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__dialogue_focused.json`
- `projects/0_260320/logs/artifacts/stage4/ep_0002/`
- `projects/0_260320/plans/blueprints/blueprint_0002.txt`
- `modules/core/stage4_orchestrator.py`
- `modules/core/artifact_logging.py`
- `tests/test_v75d_graduated_escalation.py`
Side-Effect Coverage: covered

## 1. Intent

Persist a durable proof trail when Stage4 V75-D blueprint inplace patch succeeds.

The fresh run proved that V75-D can succeed in memory but still leave no visible patched-blueprint artifact. This execution item exists to make that patch auditable after the fact.

## 2. Baseline Facts

- `projects/0_260320/logs/session/ui_events.jsonl` logs V75-D blueprint inplace patch success.
- `modules/core/stage4_orchestrator.py` mutates `round_ctx.blueprint` when V75-D succeeds.
- the same V75-D branch computes diff/change-ratio diagnostics but does not snapshot the patched blueprint through `snapshot_logged_artifact(...)`.
- `projects/0_260320/logs/artifacts/stage4/ep_0002/` contains manuscript attempt artifacts only; no dedicated patched-blueprint artifact is visible.
- Stage4 already persists manuscript-side artifacts such as `selected_before_fix`, `rejected_best`, and `patched_after_fix`.

## 3. Scope

Included:
- `modules/core/stage4_orchestrator.py`
- `modules/core/artifact_logging.py`
- bounded Stage4 audit/logging linkage for V75-D blueprint patch success
- focused regression tests for V75-D artifact persistence

Excluded:
- redesign of V75-D escalation semantics
- Stage3 blueprint generation redesign
- broader proof-digest/report pipeline redesign
- manuscript-side artifact naming changes unrelated to blueprint patch visibility

## 4. Realization Architecture

### Tranche 1. Patched blueprint snapshot
- on successful V75-D patch, persist a stable UTF-8 artifact snapshot under the Stage4 attempt artifact tree
- artifact should be clearly distinguishable from Stage3 blueprint final artifacts
- the snapshot should reflect the actual patched blueprint bytes that the next retry round uses

Recommended shape:
- artifact kind: `patched_blueprint_after_fix`
- stable linkage metadata:
  - candidate/attempt key
  - content hash
  - artifact path

### Tranche 2. Audit/log linkage
- persist one bounded runtime breadcrumb so later merge audits can join:
  - ep / round
  - V75-D success
  - patched blueprint artifact path
  - optional change-ratio / diff summary
- preferred surfaces:
  - `audit_event(...)`
  - or a bounded Stage4 control-row/log event

### Tranche 3. Regression lock
- add focused regression that proves:
  - V75-D success now yields a persisted patched-blueprint artifact
  - the linkage path is visible to later audit/report consumers

## 5. Side-Effect Map

- file writes / artifacts:
  - new Stage4 artifact snapshot under `logs/artifacts/stage4/...`
- DB / schema / transaction boundaries:
  - none required if bounded to artifact + audit/log linkage
- JSONL / log / audit sinks:
  - one additional audit/log event on V75-D success is acceptable
- console / UI / operator output:
  - optional short path hint; not required
- rollback / recovery / retry:
  - must not change retry semantics, only observability
- cache / global state:
  - none beyond existing `round_ctx.blueprint` mutation

## 6. Validation Plan

Minimum:
- focused regression for V75-D snapshot persistence
- targeted Stage4 artifact-path assertion
- UTF-8 hygiene on touched docs/code
- `git diff --check`

Preferred:
- re-run the bounded `0_260320`-style failure path or a synthetic V75-D success test fixture
- confirm later audit surfaces can see the artifact path

## 7. Pass/Fail Criteria

Pass:
- successful V75-D patch leaves a durable patched-blueprint artifact
- later audits can identify that artifact without relying on UI text alone

Fail:
- success is still visible only in UI/console logs
- the patched blueprint remains untraceable as a file-level artifact

## 8. Queue Priority

- priority:
  - `2`
- rationale:
  - narrower and higher-confidence than the broader Stage4 retry-pathology item
  - improves future diagnosis before deeper Stage4 behavior changes

## 9. Confidence

- pass 1:
  - fresh-run evidence and code path aligned
- pass 2:
  - scope bounded to observability, not semantics
- pass 3:
  - queue role and validation plan checked
- estimated confidence:
  - `0.97`

## 10. Closure Note

Status:
- `closed`

Realization Summary:
- `modules/core/stage4_orchestrator.py` now persists a stable `patched_blueprint_after_fix` artifact when V75-D blueprint inplace patch succeeds
- the same V75-D success branch now emits bounded linkage metadata:
  - `candidate_key`
  - `content_hash`
  - `artifact_path`
- linkage is persisted in both:
  - `audit_event("stage4_v75d_blueprint_patch_snapshot", ...)`
  - `episode_production.jsonl` via `_log_escalation_event(...)`

Verification Evidence:
- `python -m pytest tests/test_v75b_escalation.py -q`
- `python -m pytest tests/test_stage4_orchestrator.py -k "log_escalation_event" -q`
- `python -m pytest tests/test_artifact_logging.py -q`

Residual Risk:
- this item fixes proof-trace visibility only
- broader retry grouping / escalation policy remains active under:
  - `docs/2026-03-20/stage4-retry-pathology-observability-and-escalation-execution-ssot.md`

Queue Action:
- temp mirror removed at closure
- aggregate roadmap retired because the queue returned to single-item mode
