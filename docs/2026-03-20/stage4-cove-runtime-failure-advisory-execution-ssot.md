# Stage4 CoVe Runtime Failure Advisory Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage4-cove-runtime-failure-advisory-execution-ssot.md`
Temp Mirror Path: `removed at closure`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: fresh-run project 0_260320, docs/mmmm collector bundle, closed Stage4 observability items, ongoing dated-doc churn`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/rol-global-post-run-merge-audit.md`
- `docs/2026-03-20/rol-post-run-action-bearing-split-3pass-audit.md`
- `docs/2026-03-20/stage4-retry-pathology-observability-and-escalation-execution-ssot.md`
Evidence Artifacts:
- `projects/0_260320/print.txt`
- `projects/0_260320/logs/session/decisions.jsonl`
- `projects/0_260320/logs/session/ui_events.jsonl`
- `modules/core/stage4_orchestrator.py`
- `tests/test_stage4_orchestrator.py`
Side-Effect Coverage: covered

## 1. Intent

Stop CoVe runtime failures from overturning a Director PASS.

This item is intentionally narrow:
- keep CoVe semantic reject authority
- remove CoVe runtime-error veto authority
- preserve observability with explicit advisory logging

## 2. Baseline Facts

- `modules/core/stage4_orchestrator.py` currently fail-closes both:
  - `quick_verify(...)` runtime exceptions
  - `verify(...)` runtime exceptions
- the fail-closed path rewrites a provisional PASS into a retry lane even when the failure is infrastructural rather than semantic.
- fresh run `0_260320` showed:
  - temporary PASS
  - later CoVe runtime failure
  - downgrade back into `REJECT/retry`
- post-select continuity/history veto is separate and remains an intentional final gate.

## 3. Scope

Included:
- `modules/core/stage4_orchestrator.py`
- bounded Stage4 CoVe runtime-error handling
- focused tests for runtime-advisory vs semantic-reject split

Excluded:
- changing CoVe semantic reject behavior
- changing post-select downgrade semantics
- changing Director scoring or Stage4 repair-lane policy
- broad CoVe redesign

## 4. Realization Architecture

### Tranche 1. Runtime/semantic split
- if `quick_verify(...)` or `verify(...)` raises a runtime exception:
  - keep the current PASS candidate
  - log a CoVe runtime advisory
  - keep post-run observability
- if CoVe returns semantic regeneration demand:
  - keep the current fail-closed retry behavior

### Tranche 2. Advisory visibility
- persist a bounded runtime advisory row to Stage4 logs/audit output
- keep the signal visible for later watchlist/policy review

## 5. Policy Decision

Decision:
- `CoVe semantic conflict` may still overturn provisional PASS
- `CoVe runtime failure` must not overturn provisional PASS

Rationale:
- semantic conflict is content judgment
- runtime failure is infrastructure failure
- infrastructure failure should not outrank Director judgment

## 6. Side-Effect Map

- file writes / artifacts:
  - bounded JSONL/log additions only
- DB / schema:
  - none
- JSONL / audit sinks:
  - yes
- console / UI output:
  - yes, compact advisory line allowed
- retry semantics:
  - changed only for CoVe runtime failure

## 7. Validation Plan

Minimum:
- focused tests for:
  - `verify(...)` runtime exception no longer causes retry
  - `quick_verify(...)` runtime exception no longer causes retry
  - semantic `should_regenerate` still causes retry
- UTF-8 hygiene
- `git diff --check`

## 8. Pass/Fail Criteria

Pass:
- Director PASS survives CoVe runtime exception
- CoVe semantic reject still fails closed
- runtime advisory remains observable in logs/audit

Fail:
- runtime exception still forces retry
- semantic reject path is weakened

## 9. Queue Priority

- priority:
  - `1`
- rationale:
  - explicit user decision
  - bounded policy change with clear code surface

## 10. Confidence

- pass 1:
  - fresh-run evidence and live code align
- pass 2:
  - scope is narrow and authority split is explicit
- pass 3:
  - rollback risk bounded to CoVe runtime branch only
- estimated confidence:
  - `0.95`

## 11. Closure Note

Closed after Stage4 CoVe runtime exceptions were split from semantic CoVe reject behavior.

Implemented:
- `verify(...)` runtime exceptions now preserve Director PASS and emit a bounded runtime advisory
- `quick_verify(...)` runtime exceptions now preserve Director PASS and emit a bounded runtime advisory
- semantic `should_regenerate` still uses the existing fail-closed retry lane
- runtime advisory rows now persist as `STAGE4_COVE_RUNTIME_ADVISORY`

Verification Evidence:
- `python -m pytest tests/test_stage4_orchestrator.py -k "cove or retry_pathology or log_escalation_event" -q`
- `python -m pytest tests/test_v75b_escalation.py -q`
- `python -m pytest tests/test_stage4_interview_round.py -k "post_select_conflict_preserves_patch_seed_metadata" -q`

Residual Notes:
- this item does not weaken post-select continuity/history veto
- this item does not change semantic CoVe reject authority
