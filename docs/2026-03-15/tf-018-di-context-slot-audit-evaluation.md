<!-- [완료] -->
# TF-018 DI Context Slot Audit Evaluation

Date: 2026-03-15
Status: final
Canonical Path: `docs/2026-03-15/tf-018-di-context-slot-audit-evaluation.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: active roadmap/temp docs, post-remediation bundle docs, runtime/operator and Stage 4 follow-up edits, projects/000 artifacts, and unrelated historical doc churn`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `TF-012 is implemented, TF-013 and TF-017 are already closed as decision docs, and this evaluation checks whether TF-018 should stay documentation-only or expand into a successor DI refactor lane`
Parent Lane: `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
TF Composition Source: `docs/2026-03-15/codebase-global-post-remediation-tf-composition.md`
Source Evidence:
- `docs/2026-03-15/codebase-global-post-remediation-deep-global-survey.md`
- `docs/2026-03-15/codebase-global-post-remediation-cross-cut-integrity-matrix.md`
- `docs/2026-03-15/codebase-global-post-remediation-evidence.txt`
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight.py`
- `main_a.py`
- `tests/test_stage2_context.py`
- `tests/test_stage4_context.py`
- `tests/test_runtime_ownership_contract.py`
- `tests/integration/test_pipeline_smoke.py`
- `tests/test_main_a_persistence_helpers.py`

## 1. Intent
- Evaluate whether `TF-018` should refactor DI context slot surfaces, especially the large `Stage2Context`, into grouped callbacks or delegated sub-objects.
- Keep the outcome bounded to one decision: retain the current flat structure with refreshed inventory authority, or spawn a successor execution SSOT for DI refactor work.
- Avoid opportunistic Stage 2/3/4 interface churn while the residual lane is still active.

## 2. Current DI Surface
- Live `__slots__` inventory is now:
  - `Stage2Context`: `52`
  - `Stage3Context`: `24`
  - `Stage4Context`: `30`
- The original post-remediation survey snapshot still records `47 / 19 / 26` for those same contexts.
- That means the March 15 survey bundle is now stale as a slot-count authority, but the drift is a documentation-snapshot gap, not by itself a runtime defect.

## 3. Evidence Review

### 3.1 Count Drift Is Real But Bounded
- Current source inspection shows:
  - `Stage2Context` now includes `context_advisor`, `adversarial_self_play`, `retry_feedback_contract`, `retry_feedback_missing_callbacks`, and `session_logger` beyond the older summary shape.
  - `Stage3Context` now includes `context_advisor`, `adversarial_self_play`, `pass_rate_monitor`, and `session_logger` beyond the older summary shape.
  - `Stage4Context` now includes `context_advisor`, `emotion_tracker`, `session_logger`, and `_stage4_context_budget_meta`, with callback-like surfaces partially moved behind property accessors.
- The live slot totals therefore need a refreshed authority source, but there is no fresh evidence that the count drift itself caused AttributeError regressions or broken stage entry wiring.

### 3.2 The Stage2 Flat Surface Is Deeply Entrenched
- A static grep across `modules/core` and `tests` found `105` direct references to the relevant `Stage2Context` callback/observer attributes such as:
  - `generate_reverse_feedback_stage3_to_2`
  - `generate_reverse_feedback_stage4_to_2`
  - `build_minimal_arc_context`
  - `build_focused_context`
  - `analyze_rejection_pattern_v60`
  - `get_adaptive_feedback_intensity`
  - `generate_arc_context_v60`
  - `sync_cache_key_to_app`
  - validation and commit callbacks
- `Stage2Orchestrator`, `stage2_preflight.py`, `stage2_finalizer.py`, and `stage2_validation_pipeline.py` all call those surfaces through direct flat `ctx.<name>` access.
- `tests/test_runtime_ownership_contract.py` also treats the current flat callback map as the live compatibility contract.

### 3.3 Partial Anti-Growth Patterns Already Exist
- `Stage2Context` already centralizes retry-feedback resolution through `_RETRY_FEEDBACK_CALLBACK_SPECS` plus `_build_retry_feedback_contract()`.
- That means the large retry-feedback family is already documented and tracked in one place even though the runtime surface remains flat for downstream compatibility.
- `Stage4Context` already applies the stronger grouping pattern that TF-018 might otherwise propose:
  - `8` optional modules are collapsed into `conditional_modules`
  - selected callback-like surfaces are stored behind property accessors backed by `_stage4_context_budget_meta`
- `tests/test_main_a_persistence_helpers.py` also asserts that reserved StateService facade shims do not leak into Stage 2/3/4 context slots, so slot growth is already bounded by explicit exclusion rules.

### 3.4 Refactor Risk Is Higher Than Current Benefit
- Replacing the current flat `Stage2Context` callback surface with grouped delegates would widen scope across:
  - `Stage2Context.__init__`
  - `Stage2Context.from_app()`
  - the runtime ownership contract JSON and its tests
  - Stage 2 orchestrator/preflight/finalizer/validation helpers
  - multiple smoke/e2e/integration tests that inject or assert direct callback names
- Current evidence does not show a corresponding runtime failure class that this refactor would solve right now.
- The stronger immediate defect is stale documentation authority for slot counts, not a proven need to redesign the runtime interface.

## 4. Verification
- `python -m pytest tests/test_stage2_context.py` -> targeted Stage 2 DI context contract coverage
- `python -m pytest tests/test_stage4_context.py` -> targeted Stage 4 composite/property context coverage
- `python -m pytest tests/test_runtime_ownership_contract.py` -> live context-factory and callback-surface contract coverage
- `python -m pytest tests/integration/test_pipeline_smoke.py -k "stage2_context_slot_count or stage4_context_slot_count"` -> smoke slot-count assertions
- `python -m pytest tests/test_main_a_persistence_helpers.py -k reserved_state_service_facade_shims` -> guard that reserved facade shims remain outside Stage contexts
- Static line inspection confirmed:
  - live slot totals of `52 / 24 / 30`
  - `Stage2Context` retry callback contract/ledger
  - `Stage4Context` `conditional_modules` grouping plus property-backed callback storage
  - stale survey snapshot counts in the March 15 bundle

## 5. Decision
- Retain the current flat `Stage2Context` and `Stage3Context` runtime surface for now.
- Retain the current hybrid `Stage4Context` grouping pattern without forcing the same pattern onto Stage 2 immediately.
- Treat TF-018 as complete through a bounded decision document rather than code changes.

## 6. Rationale
- The current problem is inventory drift, not a proven DI runtime defect.
- Stage 2 flat callback names are already a wide compatibility surface across runtime code and tests.
- The workspace already introduced narrower anti-growth measures where risk was higher:
  - retry callback contract metadata in Stage 2
  - grouped conditional modules and hidden callback storage in Stage 4
- Forcing a new grouping pattern now would be a broad interface migration without evidence of current user-facing or runtime benefit.

## 7. Reopen Triggers
- Reopen TF-018 only if one of the following becomes true:
  - fresh live evidence shows concrete DI context defects caused by slot-growth or callback-surface sprawl
  - the Stage 2 callback surface is first collapsed behind a narrower compatibility contract in code and tests
  - a future lane explicitly asks for a `Stage2Context v2` or staged DI refactor rather than a bounded audit
  - slot counts continue growing without corresponding ownership tests or inventory refreshes

## 8. Operating Consequence
- The residual lane stays active, but TF-018 is satisfied by this decision doc.
- Future DI audits should use live source counts (`52 / 24 / 30`) rather than the stale March 15 survey snapshot counts (`47 / 19 / 26`).
- The next residual evaluation item should proceed without assuming an imminent Stage 2 callback-grouping refactor.
