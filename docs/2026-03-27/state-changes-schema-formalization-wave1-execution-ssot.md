Date: 2026-03-27
Status: closed (realized; closure-audited)
Document Type: system-track execution SSOT
Canonical Path: `docs/2026-03-27/state-changes-schema-formalization-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/state-changes-schema-formalization-wave1-execution-ssot.md`
Promotion Basis:
- `docs/2026-03-27/state-changes-schema-formalization-compact-survey.md`
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-defer-priority-freeze.md`
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-opus-deep-dive-audit.md`
Authority Note:
- This SSOT is derived from live-code re-audit.
- Opus lane wording is background only and is not treated as direct authority for this wave.

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked provider/context/validator/stage4/orientation/runtime surfaces, queue-state.json, logs/artifacts; untracked dated docs, anthropic_vertex provider/tests, probe script, project artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Source Survey Docs:
- `docs/2026-03-27/state-changes-schema-formalization-compact-survey-order.md`
- `docs/2026-03-27/state-changes-schema-formalization-compact-survey.md`
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-defer-priority-freeze.md`
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-opus-deep-dive-audit.md`

Evidence Artifacts:
- `modules/models/arc.py`
- `modules/protocols/app_services.py`
- `modules/protocols/agents.py`
- `modules/domain/agents/state_tracker.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `tests/test_pydantic_models.py`
- `tests/test_tf10_episode_details.py`

Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe `state_changes` formalization wave.

The goal is:
- make the top-level `state_changes` contract explicit
- make that contract visible in the model and highest-value type surfaces
- avoid behavioral change
- avoid schema redesign, enum normalization, or producer-path consolidation

This wave is intentionally type-first and contract-first.

## 2. Adversarial 3-Pass Re-Audit

### Pass 1. Authority / Scope Audit

Live-code findings:
- `ArcData.state_changes` is still annotated as plain `dict` in `modules/models/arc.py:210`
- the existing `StateChanges` Pydantic model covers only 4 fields in `modules/models/arc.py:170-179`
- runtime imports of `StateChanges` were not found outside tests
- direct `state_changes: dict` or equivalent return annotations appear in 17 locations across 7 runtime/protocol files

Implication:
- adding a canonical `TypedDict` is execution-worthy
- removing or renaming the existing `StateChanges` Pydantic class is unnecessary and riskier than this wave needs

### Pass 2. Blast-Radius Audit

Live-code findings:
- primary direct consumers are still `WorldState` and `FactLedger`
- secondary typed touchpoints are `StateTracker.extract_all_state_changes()`, two protocols, and two helper consumers
- no import-cycle evidence was found that would block importing a type from `modules.models.arc` into these files

Implication:
- bounded annotation adoption is safe
- the natural wave boundary is:
  - model anchor
  - producer/protocol signatures
  - primary consumer signatures
  - two secondary helper signatures

What this pass rejects:
- nested entry TypedDict explosion
- enum module introduction
- changing `stage4_post_pass_runtime` payload composition
- changing Analyst key-guarantee behavior

### Pass 3. Execution Shape Audit

Result:
- `TypedDict-first` remains the right execution shape
- the wave should update the top-level contract and selected annotations only
- runtime logic, key meaning, alias behavior, and fallback behavior must remain unchanged

## 3. Scope

Included:
- `modules/models/arc.py`
- `modules/protocols/app_services.py`
- `modules/protocols/agents.py`
- `modules/domain/agents/state_tracker.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `tests/test_pydantic_models.py`
- `tests/test_tf10_episode_details.py`

Excluded:
- `modules/domain/agents/analyst.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage3_orchestrator.py`
- enum normalization
- field alias cleanup
- producer-path merge/consolidation
- nested per-entry TypedDict decomposition beyond what is minimally necessary
- any behavioral change in `WorldState`, `FactLedger`, or `StateTracker`

## 4. Live Baseline Summary

Current live state:
- `StateChanges` Pydantic exists but is a minimal compat model, not the true runtime contract
- `ArcData.state_changes` is still plain `dict`
- runtime producer/consumer code already tolerates missing keys with `.get()` defaults
- current correctness risk is contract opacity, not a crashing schema mismatch

This means the right move is:
- formalize the top-level key contract
- propagate that contract to high-value signatures
- keep all runtime semantics unchanged

## 5. Realization Architecture

### Tranche A. Canonical Type Anchor

Add one canonical `StateChangesDict` TypedDict in `modules/models/arc.py`.

Rules:
- top-level contract only
- broad, compatibility-friendly shapes
- no attempt to encode every nested entry as a strict model in this wave

Expected shape style:
- `total=False`
- broad value types such as:
  - `list[dict[str, Any] | str]`
  - `list[dict[str, Any]]`
  - `dict[str, Any]`
  - `dict[str, int]`
  - scalar numeric fields where already consumed directly

Also:
- update `ArcData.state_changes` from `dict` to `StateChangesDict`
- keep existing `StateChanges` Pydantic class import-compatible
- change its docstring/comment to mark it as a limited legacy compat shell rather than canonical SSOT

### Tranche B. High-Value Annotation Adoption

Adopt `StateChangesDict` in the bounded runtime/protocol ring:
- `modules/protocols/app_services.py`
- `modules/protocols/agents.py`
- `modules/domain/agents/state_tracker.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`

This tranche is type-only:
- function signatures
- helper signatures
- return types
- no logic rewrites

### Tranche C. Regression Coverage

Adjust or extend tests only where needed to preserve confidence in:
- `ArcData.model_validate()` compatibility
- `StateChanges` compat shell continued availability
- no regression in Pydantic acceptance of existing `state_changes` payloads

## 6. Acceptance Criteria

- `StateChangesDict` exists in `modules/models/arc.py`
- `ArcData.state_changes` is annotated to `StateChangesDict`
- the existing `StateChanges` Pydantic class remains import-compatible and explicitly marked as a limited compat shell
- bounded annotation adoption lands in the included runtime/protocol files
- no producer/consumer logic changes
- no key rename, alias removal, enum normalization, or payload consolidation lands in this wave
- existing runtime behavior remains dict-compatible

## 7. Side-Effect Map

- file writes:
  - model/type annotations
  - type imports
  - targeted tests
- DB/schema:
  - none
- JSONL/log/audit sinks:
  - none
- console/operator output:
  - none
- rollback/recovery/retry:
  - none
- cache/global state:
  - none
- import graph risk:
  - `modules.models.arc` becomes the canonical export location for `StateChangesDict`
  - included files may import that type

## 8. Verification Plan

- `python -m py_compile modules/models/arc.py modules/protocols/app_services.py modules/protocols/agents.py modules/domain/agents/state_tracker.py modules/core/world_state.py modules/core/fact_ledger.py modules/core/stage2_finalizer.py modules/domain/agents/blueprint_constraint_compiler.py`
- `pytest tests/test_pydantic_models.py -q`
- `pytest tests/test_tf10_episode_details.py -q`
- `python scripts/check_utf8_hygiene.py modules/models/arc.py modules/protocols/app_services.py modules/protocols/agents.py modules/domain/agents/state_tracker.py modules/core/world_state.py modules/core/fact_ledger.py modules/core/stage2_finalizer.py modules/domain/agents/blueprint_constraint_compiler.py tests/test_pydantic_models.py tests/test_tf10_episode_details.py docs/2026-03-27/state-changes-schema-formalization-wave1-execution-ssot.md docs/temp/state-changes-schema-formalization-wave1-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 9. Guardrails

- Do not remove `StateChanges` Pydantic in this wave
- Do not introduce strict nested entry models unless a touched file truly requires one
- Do not normalize enums in this wave
- Do not rename `commitments/promises/promises_obligations` in this wave
- Do not touch `stage4_post_pass_runtime` payload assembly in this wave
- Do not touch Analyst key-guarantee logic in this wave
- If implementation starts needing runtime logic changes, stop and reopen scope

## 10. Deferred Items

Remain deferred after this wave:
- enum/value normalization
- alias cleanup
- `financial_events` shape reconciliation
- `timeline` contract cleanup
- `promises_obligations` cleanup
- broader `state_changes` producer-path consolidation
- realm/NPC technique modeling

## 11. Temp Queue Notes

- temp status: closed
- cleanup condition: completed after closure audit confirmed canonical/roadmap/code coherence
- roadmap dependency: `docs/2026-03-27/state-and-maturity-execution-roadmap.md`

## 12. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- queue sync command: `python scripts/sync_temp_queue_state.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: before patching, re-run the 3-pass audit against the live workspace and confirm this SSOT still holds at >=95% confidence

## 13. 3-Pass Audit Record

### Pass 1. Structure and Scope
- confirmed that the survey supports a bounded execution wave
- rejected broad refactor expansion up front
- locked the wave to type-first formalization
- PASS

### Pass 2. Evidence and Consistency
- confirmed live `ArcData.state_changes` remains plain `dict`
- confirmed `StateChanges` is minimal and non-canonical
- confirmed 17 direct annotation sites exist in the bounded ring
- confirmed runtime imports of `StateChanges` are test-only
- PASS

### Pass 3. Execution Readiness
- selected a bounded touched-file set
- selected verification that matches the no-behavior-change scope
- kept deferred items out of scope
- PASS

Estimated confidence: `96%`

## 14. Promotion Judgment

Promotion result: `promoted`

Reason:
- the compact survey is strong enough
- the hostile re-audit did not find a scope-breaking contradiction
- the best next step is now implementation, not another broad survey

## 15. Closure Note

Closure date: `2026-03-27`
Closure result: `closed`

Realized scope:
- added canonical `StateChangesDict` top-level TypedDict in `modules/models/arc.py`
- updated `ArcData.state_changes` to `StateChangesDict`
- preserved `StateChanges` Pydantic as a limited legacy compat shell
- propagated `StateChangesDict` through the bounded producer/protocol/consumer/helper ring:
  - `modules/protocols/app_services.py`
  - `modules/protocols/agents.py`
  - `modules/domain/agents/state_tracker.py`
  - `modules/core/world_state.py`
  - `modules/core/fact_ledger.py`
  - `modules/core/stage2_finalizer.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
- added regression coverage for TypedDict importability and `ArcData` compatibility in `tests/test_pydantic_models.py`

Verification evidence:
- `python -m py_compile modules/models/arc.py modules/protocols/app_services.py modules/protocols/agents.py modules/domain/agents/state_tracker.py modules/core/world_state.py modules/core/fact_ledger.py modules/core/stage2_finalizer.py modules/domain/agents/blueprint_constraint_compiler.py` -> PASS
- `python -m pytest tests/test_pydantic_models.py -q` -> `61 passed`
- `python -m pytest tests/test_tf10_episode_details.py -q` -> `19 passed`
- `python scripts/ops_validator.py` -> PASS

Residual caveats:
- `python -m ruff check` on the touched file set still reports two pre-existing local unused-import findings in `modules/core/stage2_finalizer.py` (`RecoveryLimits`, `_threshold`); this wave did not widen them
- the exact SSOT UTF-8 hygiene command still hits inherited `state_tracker.py` suspicious-token lines (`612-615`); no new wave-local UTF-8 regression was identified during diff review

Behavior judgment:
- diff inspection plus compile/test results support `no behavior change`
- this wave is treated as closed because the bounded contract formalization landed and the remaining lint/hygiene issues are inherited residuals, not correctness regressions opened by this wave
