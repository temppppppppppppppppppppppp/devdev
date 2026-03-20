# Stage4 Reverse-Feedback DI Alignment Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage4-reverse-feedback-di-alignment-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-reverse-feedback-di-alignment-execution-ssot.md`
Source Survey Docs:
- `docs/2026-03-20/rol-low-trust-mmmm-second-tranche-reaudit-3pass-audit.md`
- `docs/2026-03-20/rol-low-trust-mmmm-intake-triage-3pass-audit.md`
Evidence Artifacts:
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_context.py`
- `modules/core/feedback_system.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_orchestrator.py`
Side-Effect Coverage:
- Stage4→3 reverse feedback callback resolution
- Stage4 context DI surface
- blueprint regenerate/inplace patch feedback injection
Commit State:
- Baseline Commit: `9a4f46a8f8193c42e236cf181e0151b26a3167b4`
- Baseline Dirty Summary: `dirty: ongoing dated-doc churn, recent validation/scoring alignment closure, project/log artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Intent
- Remove the direct `self.app._generate_reverse_feedback_stage4_to_3` reach from `Stage4Orchestrator`.
- Keep Stage4 reverse-feedback generation inside the Stage4 DI/context surface.
- Preserve current behavior, including optional fallback to `FeedbackSystem`.

## 2. Baseline Facts
- `modules/core/stage4_orchestrator.py` currently resolves Stage4→3 reverse feedback by inspecting `self.app` directly.
- `modules/core/feedback_system.py` already exposes `generate_reverse_feedback_stage4_to_3(...)`.
- `modules/core/stage4_context.py` currently carries many callbacks, but not the Stage4→3 reverse-feedback callback.
- `modules/core/stage2_context.py` already uses a direct-or-fallback callback resolution pattern for retry feedback helpers.

## 3. Problem Statement
- Current Stage4 reverse-feedback generation bypasses the Stage4 DI boundary.
- That makes the orchestrator depend on hidden `SovereignApp` internals instead of the explicit Stage4 context contract.
- The issue is real but bounded: low blast radius, no policy rewrite, small write surface.

## 4. Scope

Included:
- `modules/core/stage4_context.py`
- `modules/core/stage4_orchestrator.py`
- targeted Stage4 tests

Excluded:
- Stage4 semantic retry policy
- feedback content redesign
- broad Stage4 context refactor
- Stage2/Stage3 retry callback cleanup

## 5. Execution Shape

### Tranche 1. Context Callback Surface
- add `generate_reverse_feedback_stage4_to_3` to `Stage4Context`
- make `Stage4Context.from_app(...)` resolve:
  - direct app callback first
  - `_feedback_system.generate_reverse_feedback_stage4_to_3` as fallback

### Tranche 2. Orchestrator Resolution
- switch `Stage4Orchestrator._build_stage4_to_3_reverse_feedback(...)` to use `self.ctx`
- stop direct `self.app` inspection in that helper

### Tranche 3. Regression Lock
- pin direct callback path
- pin `_feedback_system` fallback path
- pin Stage4 reverse-feedback injection still reaches blueprint patch path

## 6. Acceptance Criteria
- `Stage4Orchestrator` no longer directly reaches `self.app._generate_reverse_feedback_stage4_to_3`
- reverse-feedback callback remains optional and fail-soft
- fallback to `_feedback_system.generate_reverse_feedback_stage4_to_3` works
- targeted Stage4 tests pass
- no change to feedback text semantics

## 7. Verification Plan
- `python -m pytest tests/test_stage4_context.py -q`
- `python -m pytest tests/test_stage4_orchestrator.py -k "reverse_feedback or inplace_patch" -q`
- `python -m py_compile modules/core/stage4_context.py modules/core/stage4_orchestrator.py`
- `python scripts/check_utf8_hygiene.py ...`
- `git diff --check -- ...`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 8. Guardrails
- do not widen this into a full Stage4 DI campaign
- do not change reverse-feedback content wording
- do not change Stage4 retry stop conditions
- keep fallback optional; missing callback must still degrade to empty feedback

## 9. Completion Signal
- canonical doc updated to `closed`
- temp mirror removed
- queue-state synced back to empty mode

## 10. Closure Note
- `Stage4Context` now carries `generate_reverse_feedback_stage4_to_3` as a callback property.
- `Stage4Context.from_app(...)` resolves the callback from direct app binding first, then `_feedback_system.generate_reverse_feedback_stage4_to_3` as fallback.
- `Stage4Orchestrator._build_stage4_to_3_reverse_feedback(...)` now reads through `self.ctx` instead of directly inspecting `self.app`.
- targeted verification passed:
  - `python -m pytest tests/test_stage4_context.py -q`
  - `python -m pytest tests/test_stage4_orchestrator.py -k "reverse_feedback or inplace_patch" -q`
  - `python -m pytest tests/e2e/test_smoke_pipeline.py -k "Stage4ContextCreation" -q`
  - `python -m pytest tests/integration/test_pipeline_smoke.py -k "stage4_context_slot_count" -q`
  - `python -m pytest tests/test_main_a_persistence_helpers.py -k "reserved_state_service_facade_shims" -q`
