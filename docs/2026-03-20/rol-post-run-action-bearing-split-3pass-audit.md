# ROL Post-Run Action-Bearing Split

Date: 2026-03-20
Status: completed
Canonical Path: `docs/2026-03-20/rol-post-run-action-bearing-split-3pass-audit.md`
Related Merge Audit: `docs/2026-03-20/rol-global-post-run-merge-audit.md`
Related Roadmap: `docs/2026-03-20/rol-post-fresh-run-and-low-trust-intake-execution-roadmap.md`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: fresh-run project 0_260320, docs/mmmm collector bundle, active smoke-fixture temp mirror, ongoing dated-doc churn`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose

- Split the merged `0_260320` findings into:
  - bounded execution SSOT
  - policy audit
  - watchlist-only
- Preserve the low-trust role of `docs/mmmm/`.
- Decide whether the temp execution queue must expand beyond `smoke-fixture-alignment`.

## 2. Validity Gate

Target Paths:
- `docs/2026-03-20/rol-global-post-run-merge-audit.md`
- `docs/2026-03-20/rol-live-run-0_260320-evidence-manifest.md`
- `docs/2026-03-20/rol-low-trust-mmmm-intake-triage-3pass-audit.md`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/artifact_logging.py`

Input Evidence Set:
- bounded fresh run `projects/0_260320/`
- canonical post-run merge audit
- low-trust `docs/mmmm/` hint ledger

Checks:
- merge audit confidence remains `0.96`
- temp queue still contains only `smoke-fixture-alignment` before this split
- no newer fresh run supersedes `0_260320`

Result:
- Item E is still valid

## 3. Classification Summary

| Finding | Classification | Why |
| --- | --- | --- |
| Stage4 retry pathology around `post_select_conflict` / `continuity_firewall` | bounded execution SSOT | concrete live failure pattern with stable code paths |
| V75-D blueprint inplace patch observability gap | bounded execution SSOT | concrete logging/artifact gap with narrow implementation surface |
| CoVe fail-closed after provisional PASS | watchlist-only for now | fail-closed semantics are currently intentional; fresh run exposed one bounded runtime-failure sample, not a stable standalone defect class |
| smoke fixture alignment | existing bounded execution SSOT | already active and still open |

## 4. Live-Code Re-Check Notes

### 4.1 Stage4 retry pathology
- `modules/core/stage4_interview_round.py` downgrades provisional PASS to `REJECT` when post-select continuity/history checks fire and stores the retry lane as `reject_bucket=post_select_conflict`.
- `modules/core/stage4_interview_round.py` widens `fix_scope=inplace` to `partial` when `fix_pack` is not ready, producing the visible `Fix Pack is missing` loop seen in the fresh run.
- `projects/0_260320/logs/session/decisions.jsonl` shows repeated `director PASS -> post_select_conflict downgrade`.
- `projects/0_260320/logs/session/ui_events.jsonl` and `print.txt` show the same loop progressing into `Contradiction Firewall`.

### 4.2 Blueprint inplace patch observability gap
- `modules/core/stage4_orchestrator.py` executes V75-D blueprint inplace patch and mutates `round_ctx.blueprint` in memory.
- That V75-D path logs success and computes diff/change-ratio, but does not persist a patched blueprint artifact snapshot through `snapshot_logged_artifact(...)`.
- `projects/0_260320/logs/artifacts/stage4/ep_0002/` contains manuscript attempt artifacts only; no visible patched-blueprint snapshot exists for the successful V75-D event.

### 4.3 CoVe provisional-PASS fail-closed
- `modules/core/stage4_orchestrator.py` intentionally fail-closes both `quick_verify` and `verify` runtime errors.
- Existing tests already pin the retry-on-runtime-failure behavior.
- Current evidence is sufficient to keep this in the watchlist, but not yet sufficient to open a separate execution queue item.

## 5. Low-Trust `docs/mmmm/` Reuse

Hint-only reusable intersections:
- `T05-stage4-orch-context-survey.md`
  - retry-lane and Stage4 orchestration path hints
- `T10-blueprint-generation-validation-survey.md`
  - blueprint patch path hints
- `T14-validation-pipeline-survey.md`
  - CoVe/validation path hints
- `T16-database-persistence-logging-survey.md`
  - sink and observability path hints
- `T20-crosscut-regression-integrity-survey.md`
  - regression/test anchor hints

Not accepted:
- final severities
- closure wording
- sync/no-drift claims

## 6. Split Decision

### 6.1 Create bounded execution SSOTs now
- `docs/2026-03-20/stage4-blueprint-inplace-patch-observability-execution-ssot.md`
- `docs/2026-03-20/stage4-retry-pathology-observability-and-escalation-execution-ssot.md`

### 6.2 Do not create a standalone CoVe execution SSOT yet
- keep CoVe runtime failure after provisional PASS in the watchlist
- let Stage4 retry-pathology work collect better evidence first
- only re-open as a standalone execution item if:
  - it repeats across multiple runs, or
  - a concrete code-level runtime root cause appears

## 7. Queue Impact

- `smoke-fixture-alignment` remains active.
- two new bounded execution SSOTs are now confirmed.
- because there are now `2+` active execution SSOTs, a canonical aggregate roadmap is required.
- temp queue must expand from single-item mode to roadmap-governed mode.

## 8. Item-E Completion Decision

- roadmap item:
  - `Item E. Action-Bearing Split`
- result:
  - `completed`
- reason:
  - findings are now classed into execution / watchlist tiers with live-code backing

## 9. Confidence

- pass 1:
  - merge inputs and target paths revalidated
- pass 2:
  - live code re-checked for Stage4 retry / V75-D / CoVe semantics
- pass 3:
  - queue impact and low-trust intake separation checked
- estimated confidence:
  - `0.96`
