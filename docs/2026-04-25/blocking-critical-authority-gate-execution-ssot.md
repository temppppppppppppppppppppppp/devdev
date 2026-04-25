# Blocking Critical Authority Gate Execution SSOT

Date: 2026-04-25
Status: closed-corrected
Canonical Path: `docs/2026-04-25/blocking-critical-authority-gate-execution-ssot.md`
Temp Mirror Path: `docs/temp/blocking-critical-authority-gate-execution-ssot.md`

Commit State:

- Baseline Commit: `ccc3ac914fe32a2179b96636ea0c6d352e2e2713`
- Baseline Dirty Summary: `dirty: untracked docs/2026-04-25/codebase-parallel-maintenance-deep-dive-wave2-synthesis.md`
- Resume Commit: `ccc3ac914fe32a2179b96636ea0c6d352e2e2713`
- Resume Drift Summary: `none beyond the untracked source survey doc`

Source Survey Docs:

- `docs/2026-04-25/codebase-parallel-maintenance-deep-dive-wave2-synthesis.md`

Evidence Artifacts:

- live code inspection of `modules/validation/validation_orchestrator.py`
- live code inspection of `modules/core/stage4_interview_round.py`
- live code inspection of `modules/core/stage4_director_runtime.py`
- focused tests under `tests/chaos/` and `tests/test_stage4_interview_round.py`

Side-Effect Coverage: covered

Authority Correction:

- User correction after first implementation pass: `PASS` / `REJECT` is LLM Director authority only.
- Python may collect and surface structured CRITICAL evidence, but must not mechanically force `REJECT`.
- This document is retained as a corrected closure record so future work does not reintroduce Python hard-veto logic.

## 1. Intent

Turn CRITICAL `BlockingValidator` failures into high-salience structured evidence for LLM Director judgment.

The target invariant is narrow: if structured blocking validation says a present-time hard-block violation exists, the Director must see the evidence clearly. Python must not decide `PASS` or `REJECT` on its own. For the workspace's absolute death-state rule, deceased NPC action/dialogue evidence is surfaced as CRITICAL, while recall/mention allowances remain the validator's collection responsibility and final judgment remains with the LLM Director.

## 2. Baseline Facts

- `ValidationOrchestrator._run_blocking_validation()` stores failing `BlockingValidator` output as `_blocking_advisory`.
- `ValidationOrchestrator._apply_advisory_penalties()` currently applies a capped penalty, so a high scoring manuscript can still end as PASS.
- `ValidationOrchestrator._finalize_validation_result()` currently decides PASS / CONDITIONAL_PASS / REJECT from score thresholds.
- Stage4 pre-Director candidate validation appends blocking failures to `warnings` and `focus_points`.
- Stage4 Director gate already has a downstream override pattern for quality floor and strong advisory escalation.
- Stage3 already has a dead-NPC precheck override that converts an otherwise positive pipeline result to REJECT.

## 3. Scope

Included:

- `modules/validation/validation_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_director_runtime.py`
- focused regression tests for ValidationOrchestrator and Stage4 advisory-surface semantics

Excluded:

- reworking `BlockingValidator` detection heuristics
- changing recall/flashback allowance rules
- broad Stage4 run-result authority work
- CI workflow expansion

## 4. Pass 1. Inventory Summary

Runtime authority seams:

- ValidationOrchestrator score gate: blocking failures are advisory and capped by score penalty.
- Stage4 pre-Director validation: blocking failures are candidate warnings and should also carry structured CRITICAL markers.
- Stage4 Director review: final verdict remains LLM-owned; Python evidence should be visible, not mechanically decisive.

Existing safety anchors:

- `tests/chaos/test_dead_npc_hard_block.py` proves the validator can classify action vs recall cases.
- `tests/chaos/test_feedback_loop.py` proves blocking failures reach ValidationOrchestrator advisory and failure learner paths.
- `tests/test_stage4_interview_round.py` already covers many gate semantics and candidate validation helper surfaces.

## 5. Pass 2. Semantic Classification

Class A: Structured detector authority

- `BlockingValidator` remains the detector.
- Runtime must preserve CRITICAL blocking failures as structured evidence for Director review.

Class B: Director sovereignty boundary

- Director still evaluates quality, selection, and repair reasoning.
- Director remains the only authority for `PASS` / `REJECT`.
- Python must not hard-veto a Director verdict.

Class C: Operator visibility and persistence

- CRITICAL-looking Python findings should leave explicit `suspected_critical_blocking` / `suspected_critical_blocking_failures` evidence in runtime surfaces.
- Existing warning/focus surfaces should remain visible for operator context.

## 6. Side-Effect Map

- file writes / artifacts: no runtime artifact write path is directly changed.
- DB / schema / transaction boundaries: no schema change.
- JSONL / log / audit sinks: existing advisory and validation surfaces may record structured CRITICAL evidence.
- console / UI / operator output: Stage4 UI should expose the CRITICAL evidence as Director-facing advisory context.
- rollback / recovery / retry: no Python-driven verdict reroute.
- cache / global state: no cache contract change.
- bootstrap fallback / config-env mutation: not applicable.

## 7. Realization Architecture

1. Add small CRITICAL evidence collectors at the Python validation boundary.
2. In `ValidationOrchestrator`, keep advisory payloads and add `suspected_critical_blocking=True` / `suspected_critical_failures`, but do not override `final_decision`.
3. In Stage4 prevalidation, annotate validation results with structured `suspected_critical_blocking_failures`.
4. In Stage4 Director runtime, preserve LLM verdict ownership; do not force `final_verdict`.
5. Keep the change small; do not add broad helper families to already-large owner classes unless required.

## 8. Execution Tranches

1. `validation-orchestrator-critical-evidence`
2. `stage4-selected-candidate-critical-evidence`
3. `focused-regression-validation`

## 9. Acceptance Criteria

- A CRITICAL blocking failure is surfaced in `_blocking_advisory` as structured evidence without Python hard-vetoing `final_decision`.
- Stage4 selected candidate validation carries `suspected_critical_blocking_failures` for Director review without Python forcing `REJECT`.
- Non-critical blocking warnings remain advisory.
- Recall/mention allowances remain covered by existing `BlockingValidator` tests.
- Operator-facing surfaces include enough reason text to understand the CRITICAL evidence.

## 10. Verification Plan

- `python -m pytest tests/chaos/test_feedback_loop.py tests/chaos/test_dead_npc_hard_block.py -q`
- `python -m pytest tests/test_stage4_interview_round.py -q -k "suspected_critical or python_validation_advisory"`
- `python scripts/check_utf8_hygiene.py modules/validation/validation_orchestrator.py modules/core/stage4_interview_round.py modules/core/stage4_director_runtime.py tests/chaos/test_feedback_loop.py tests/test_stage4_interview_round.py docs/2026-04-25/blocking-critical-authority-gate-execution-ssot.md`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not make Python rewrite factsheets or narrative facts.
- Do not broaden this into Stage4 run-result authority.
- Do not let Python mechanically decide `PASS` or `REJECT`.
- Do not make every blocking warning a hard reject.
- Do not silently drop existing warning/focus outputs.
- Do not add more than minimal methods to `Stage4InterviewRound`; direct-method pressure is already high.

## 12. Temp Queue Notes

- temp status: completed
- cleanup condition: `docs/temp/blocking-critical-authority-gate-execution-ssot.md` removed after realization and validation completed
- roadmap dependency: none; temp execution queue had no active execution SSOT mirrors before this item

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: this document was re-audited against the current workspace before code patching

## 14. Document 3-Pass Audit

Pass 1 - Structure and scope:

- Document type is execution SSOT.
- Canonical and temp mirror paths are explicit.
- Scope is intentionally narrow and excludes broader Stage4 run-result work.
- Acceptance criteria and verification plan are present.

Pass 2 - Evidence and consistency:

- Findings are traced to live code surfaces inspected after the survey.
- Baseline and resume commit fields are present.
- Dirty state is bounded to the untracked survey source document.
- The corrected design preserves the LLM Director as the only `PASS` / `REJECT` authority while surfacing structured CRITICAL evidence.

Pass 3 - Execution and readability:

- Execution tranches are small and sequenced.
- Side effects are explicit.
- Temp queue cleanup condition is explicit.
- Next reader can implement without re-surveying the whole codebase.

Estimated confidence:

- Execution SSOT confidence: `95%`

## 15. Closure Note

Closure status: `closed`

Realized changes:

- `ValidationOrchestrator` now marks suspected CRITICAL blocking evidence in `_blocking_advisory` without forcing final decision to `REJECT`.
- Stage4 pre-Director validation now tags suspected CRITICAL blocking evidence as `suspected_critical_blocking_failures` on the candidate validation result.
- Stage4 Director runtime remains LLM-verdict-owned; Python hard-veto code from the first pass was removed.
- Regression coverage was corrected to assert CRITICAL evidence surfacing rather than Python `REJECT` authority.

Verification evidence:

- `python -m py_compile modules/validation/validation_orchestrator.py modules/core/stage4_interview_round.py modules/core/stage4_director_runtime.py tests/chaos/test_feedback_loop.py tests/test_stage4_interview_round.py` passed.
- `python -m pytest tests/chaos/test_feedback_loop.py tests/chaos/test_dead_npc_hard_block.py -q` passed: `11 passed`.
- `python -m pytest tests/test_stage4_interview_round.py -q -k "suspected_critical or python_validation_advisory"` passed after authority correction: `2 passed, 318 deselected`.
- `python scripts/check_utf8_hygiene.py ...` passed for touched code, tests, and execution SSOT docs.
- `git diff --check` reported no whitespace errors; it only warned that `tests/chaos/test_feedback_loop.py` line endings will normalize from CRLF to LF when Git touches it.
- `python scripts/ops_validator.py --strict` passed before temp cleanup with one active mirror matching canonical.

Complexity evidence:

- `ValidationOrchestrator` direct method count: `45`
- `ValidationOrchestrator._finalize_validation_result`: `46 LOC`
- `ValidationOrchestrator._build_blocking_advisory`: `23 LOC`
- `Stage4InterviewRound` direct method count: `181`
- `Stage4InterviewRound._apply_blocking_validator_failures`: `48 LOC`
- `Stage4DirectorRuntime` direct method count: `26`
- No Stage4 Director hard-veto helper remains.

Residual risks:

- No fresh live Stage4 run was executed in this closure.
- Broader Stage4 run-result authority, CI tier expansion, and stale direct-supervised runtime audit handling remain separate follow-up items from the source survey.
