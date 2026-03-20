# C8 Stage3 Intermediate Reject Observability (3-Pass Audit)

Date: 2026-03-20
Mode: system-track bounded backend patch
Confidence: 0.96

## Scope

- Source screening note:
  - `docs/2026-03-20/opus-be-p0-p3-remaining-screening-3pass-audit.md`
- Touched live files:
  - `modules/domain/agents/three_phase_blueprint_generator.py`
  - `tests/test_blueprint_patch_mode.py`

## Problem

Stage 3 final PASS / final REJECT was already persisted by `Stage3Orchestrator`, but retry-loop rejects inside `ThreePhaseBlueprintGenerator.generate()` could disappear when a later retry recovered to PASS.

The missing observability paths were the retry-loop `continue` branches:

- phase-2 generate failure
- continuity reject before validator compare
- validation reject before the next retry
- PASS_WITH_FIX patch retry exhaustion falling back into the next generate retry

This made Stage 3 retry history flatter than the live control flow.

## Decision

Add an observability-only intermediate reject sink inside `ThreePhaseBlueprintGenerator`.

Rules:

- record only when another retry still exists
- do not duplicate the terminal failure row
- keep final Stage3 orchestrator persistence unchanged
- use a distinct attempt-key suffix so intermediate rows do not collide with final rows

## Patch

`ThreePhaseBlueprintGenerator` now has `_record_intermediate_reject(...)`.

It writes `pass_rate_monitor.record_attempt(...)` with:

- `stage=3`
- `success=False`
- `final_verdict="REJECT"`
- `generation_method="blueprint_intermediate"`
- `attempt_key=<stage3-attempt-key>:intermediate:<event_tag>`
- `error_category=<event_tag>`

Current event tags:

- `generate_failed`
- `continuity_reject`
- `patch_retry_reject`
- `validation_reject`

The helper exits early when the current retry is already the terminal retry, so the last failed attempt remains owned by the existing final Stage3 failure sink.

## Regression Coverage

Added in `tests/test_blueprint_patch_mode.py`:

- `generate_failed` on retry 0 followed by recovery PASS
- `continuity_reject` on retry 0 followed by recovery PASS
- `validation_reject` on retry 0 followed by recovery PASS
- terminal retry reject does not emit an intermediate row

## Validation

- `python -m pytest tests/test_blueprint_patch_mode.py -q`
- `python -m pytest tests/test_stage3_orchestrator.py -k "stage3_success_records_pass_rate_monitor or stage3_failure_records_pass_rate_monitor or stage3_attempt_key_uses_metrics_session_id_when_available" -q`

Result:

- `21 passed`
- `3 passed, 70 deselected`

## Outcome

`C8` is now closed as a bounded backend observability patch.

Stage 3 retry-loop rejects no longer vanish when a later retry succeeds, and terminal failure ownership remains with `Stage3Orchestrator`.
