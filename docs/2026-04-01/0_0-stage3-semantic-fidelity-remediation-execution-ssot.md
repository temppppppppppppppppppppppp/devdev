# 0_0 Stage3 Semantic Fidelity Remediation Execution SSOT

Date: 2026-04-01
Status: closed (code landed, runtime-validated)
Canonical Path: `docs/2026-04-01/0_0-stage3-semantic-fidelity-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage3-semantic-fidelity-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
- Baseline Dirty Summary: `dirty: 0_0 runtime logs/db/artifacts and 0_temp scratch active; prior 2026-04-01 Stage3 canary/code/doc work already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `revalidated against fresh Stage3-only canary evidence; residual semantic-fidelity seam confirmed and bounded`
Source Survey Docs:
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-bounded-survey.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-runtime-audit.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-runtime-audit-evidence.json`
- `projects/canary_0_0_stage3_arc2_readiness_r3/logs/stage3_canary_summary.json`
- `projects/canary_0_0_stage3_arc2_semantic_r5/logs/stage3_canary_summary.json`
- `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`
- `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-evidence.json`
- `projects/canary_0_0_stage3_arc2_readiness_r3/logs/session/llm_io.jsonl`
- `projects/canary_0_0_stage3_arc2_readiness_r3/logs/session/decisions.jsonl`
- `projects/canary_0_0_stage3_arc2_readiness_r3/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`
- `projects/0_0/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
Side-Effect Coverage: covered
Supersedes / Builds On:
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` (kept as substrate lane; residual semantic blocker extracted here)

## 1. Intent

Realize the minimum validator-side fixes required to stop Stage 3 from passing semantically off-arc blueprints after a local `PASS_WITH_FIX` patch cycle.

This wave exists because the fresh `0_0` partial Stage3 canary proved:

- structural runtime now works
- Stage 3 can still end as `PASS`
- but the final artifact can retain non-authorized physical-threat/action beats that are absent from the current episode tactical authority

## 2. Baseline Facts

- `ep5` current-session Director compare returned `PASS_WITH_FIX`, not `PASS`.
- the `PASS_WITH_FIX` feedback repaired institution name and timeline drift in-place.
- the final saved blueprint still retained `취객 난입 / 멱살 / 무단침입` beats that are not present in the Stage 2 episode tactical authority.
- `fact_lock_institution` and `arc_timeline` appeared in candidate Python advisory, but the true residual blocker is the missing semantic contradiction category for off-arc physical-threat invention.
- current binding-prevalidation policy only upgrades plain `PASS`; it does not merge binding issues into feedback when Director already returned `PASS_WITH_FIX` or `PASS_WITH_WARNING`.

## 3. Scope

Included:
- `modules/domain/agents/unified_blueprint_validator.py`
- targeted Stage 3 semantic-fidelity regression tests
- execution-doc and roadmap refresh needed to queue and realize this wave

Excluded:
- Stage 2 schema redesign
- `blueprint_ensemble.py` authority wording rework beyond already-landed substrate
- Stage 3 retry architecture redesign
- Stage 4 resume
- DB schema or sink redesign

## 4. Pass 1. Inventory Summary

- validator decision owner:
  - `UnifiedBlueprintValidator._run_compare_validation()`
  - `UnifiedBlueprintValidator._apply_binding_prevalidation_contract()`
- semantic-prevalidation owner:
  - `UnifiedBlueprintValidator._python_pre_validate()`
- runtime evidence owner:
  - `three_phase_blueprint_runtime.py` PASS_WITH_FIX loop proves the leak but does not own the missing semantic category

Main hotspots for this wave:

1. binding issues are not merged into feedback once verdict is already `PASS_WITH_FIX`
2. no bounded prevalidation category currently captures unauthorized off-arc physical-threat/action invention
3. institution fact-lock remains advisory-only at the binding-category layer

## 5. Pass 2. Semantic Classification

- Class A. Primary realization now
  - merge binding-prevalidation notes into non-reject repair verdicts, not only plain `PASS`
  - add bounded tactical semantic-fidelity detection for off-arc threat/action invention
  - promote `fact_lock_institution` into the binding-prevalidation category set

- Class B. Residual inside this lane
  - threshold tuning if new tactical detector is too noisy in non-finance arcs

- Class C. Explicitly deferred outside this lane
  - general semantic world-model redesign
  - Stage 2 tactical schema normalization
  - stale `_ensemble_meta.python_warnings` refresh after patch adoption

## 6. Side-Effect Map

- file writes / artifacts:
  - future Stage 3 blueprints may shift from `PASS` to `PASS_WITH_FIX` or `REJECT` under stronger semantic checks

- DB / schema / transaction boundaries:
  - no schema change
  - `stage_attempts.verdict` distribution may change for weak blueprints

- JSONL / log / audit sinks:
  - `selection_reason`, `verdict_reason`, `fix_scope_reasoning`, and validation feedback may include new binding snippets

- console / UI / operator output:
  - Stage 3 operator logs may show the new semantic-fidelity category in feedback

- rollback / recovery / retry:
  - `PASS_WITH_FIX` loop may receive richer feedback and therefore patch different spans

- cache / global state:
  - not applicable

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

This wave stays entirely inside the validator contract.

Architecture:

1. detect semantic contradiction before Director compare result is finalized
2. treat that contradiction as binding at the validator layer
3. if Director already chose `PASS_WITH_FIX`, keep the verdict but merge binding notes into feedback and fix-scope reasoning instead of silently dropping them

Key contract decision:

- `PASS` + binding issues -> promote to `PASS_WITH_FIX`
- `PASS_WITH_FIX` / `PASS_WITH_WARNING` + binding issues -> keep verdict but append binding note and preserve repair scope
- `REJECT` remains unchanged

## 8. Execution Tranches

1. extend `_apply_binding_prevalidation_contract()` so binding notes survive pre-existing repair verdicts
2. add bounded `tactical_semantic_fidelity` prevalidation and promote `fact_lock_institution` into binding categories
3. add targeted regressions for:
   - binding-note merge on `PASS_WITH_FIX`
   - tactical off-arc intrusion detection
   - no false positive when tactical authority explicitly authorizes action/threat
4. refresh SSOT/roadmap mirrors and keep Stage 4 paused

## 9. Acceptance Criteria

- `PASS_WITH_FIX` results can no longer silently drop binding-prevalidation issues from feedback
- validator can flag an `ep5`-style off-arc intrusion/action insertion as a bounded semantic-fidelity issue
- `fact_lock_institution` is binding-prevalidation eligible
- no new `180+ LOC` function is introduced
- targeted tests prove the new behavior without reopening Stage 4

## 10. Verification Plan

- targeted pytest for the touched validator regression file(s)
- `python -m py_compile modules/domain/agents/unified_blueprint_validator.py <touched tests>`
- `ruff check modules/domain/agents/unified_blueprint_validator.py <touched tests>`
- `python scripts/check_utf8_hygiene.py` on touched code/docs
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not resume Stage 4 in this turn
- do not widen this wave into Stage 2 tactical schema redesign
- do not re-open the already landed Stage3 authority-promotion substrate
- keep the detector bounded to clearly unauthorized physical-threat/action invention; do not attempt a general semantic evaluator here

## 12. Temp Queue Notes

- temp status: `in_progress`
- cleanup condition:
  - remove mirror only after code verification and closure audit
- roadmap dependency:
  - this lane temporarily outranks the parent `0_0-stage2-stage3-stage4-readiness-remediation` lane because it is the only remaining blocker before Stage 4 can be reconsidered

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- kept the lane bounded to validator policy leak + semantic contradiction detection
- excluded Stage 4 resume and broad Stage 2 redesign

Pass 2, evidence and consistency:

- aligned the lane to fresh canary evidence showing `PASS_WITH_FIX` from Director but `PASS` final persistence after local repair
- bounded the residual blocker to unauthorized physical-threat/action insertion, not already-fixed institution/timeline repair

Pass 3, execution and readability:

- ordered the tranches so policy leak closes before detector tuning
- made queue consequence explicit: Stage 4 stays paused

Confidence: `96%`

## 15. Execution Update

Implemented:

- widened `_apply_binding_prevalidation_contract()` so binding issues are merged into feedback even when Director already returned a repair verdict
- promoted `fact_lock_institution` into the binding category set
- added bounded `tactical_semantic_fidelity` detection for unauthorized physical-threat/action invention
- added focused regressions in `tests/test_stage23_stage4_readiness_wave1.py`

Static verification closed:

- `python -m py_compile modules/domain/agents/unified_blueprint_validator.py tests/test_stage23_stage4_readiness_wave1.py`
- `pytest tests/test_stage23_stage4_readiness_wave1.py -q`
- `ruff check modules/domain/agents/unified_blueprint_validator.py tests/test_stage23_stage4_readiness_wave1.py`

Runtime closure:

- bounded `Stage3-only canary` on `0_0` Arc2 (`canary_0_0_stage3_arc2_semantic_r5`) removed the original `ep5` intrusion subplot at final artifact truth
- closure record lives in `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`
