# 0_0 Stage234 Cross-Stage Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: parked (survey-backed future wave; shared vocabulary and source-of-truth normalization substrate; not active while Stage4 consumer/finalization seams remain higher priority)
Canonical Path: `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
- Baseline Dirty Summary: `dirty: config/models.yaml, active/temp roadmap mirrors, queue-state, canary fixpack runtime artifacts, and 2026-04-02 survey bundles/lane drafts present in workspace`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage3-static-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-evidence.json`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-evidence.json`
- `docs/2026-04-02/0_0-stage3-static-global-evidence.json`
- `docs/2026-04-02/0_0-stage2-production-consumption-global-evidence.json`
Side-Effect Coverage: covered

## 1. Intent

Preserve a bounded future wave for `Stage2/3/4 cross-stage contract normalization` without promoting it ahead of the current active Stage4 consumer/finalization lanes.

This execution SSOT exists because the matrix survey proved:

- the dominant remaining debt is not missing concepts but cross-stage rename, strength inversion, owner collision, and prose flattening
- the costliest seam is `Stage3 -> Stage4`
- `Stage4` split truth (`final_state_updates`, `actual_truth`, `world_state`) is a substrate problem, not a one-off bug
- long-term simplification work now needs a real shared vocabulary and source-of-truth contract

## 2. Baseline Facts

- `Stage2` is `content-sufficient but schema-fragile`.
- `Stage3` is `compiler-like but enforcement-lossy`.
- `Stage4` is `consumer/finalization split-truth-heavy`.
- The current system is `cross-stage-vocabulary-drift heavy`.
- The highest-cost drift types are:
  - rename without mapping
  - strength inversion
  - structure-to-prose flattening
  - multi-owner truth concepts
- The most expensive boundary is `Stage3 -> Stage4`.

## 3. Scope

Included:

- shared cross-stage vocabulary definition for repeated concepts
- explicit owner and strength matrix for major Stage2/3/4 truth concepts
- contract normalization for:
  - authority strength
  - episode mission
  - repair/finalization terms
  - post-finalization truth surfaces
- bounded alias normalization where concept drift is already proven
- bounded owner-consolidation substrate work where one concept currently has multiple owners

Excluded:

- broad architecture rewrite
- immediate Stage-count reduction
- fresh canary in this lane
- active Stage4 seam patches already covered by existing Stage4 execution SSOTs
- repo-wide string rename sweep in one turn
- DB schema redesign
- narrative artifact rewrites in `projects/`

## 4. Pass 1. Inventory Summary

Primary inventory totals and findings from the matrix survey:

- 33 major concepts traced across Stage2/3/4
- only a small stable subset remain true equivalents across boundaries
- several Stage2 fields are effectively dead or low-signal by the next boundary
- Stage4 introduces additional local vocabulary for upstream truths

Highest-cost mismatch families:

1. `constraint_summary -> arc_constraint_summary -> Stage4 hard prohibition prose`
2. `tactical_doc -> arc_focus -> arc_tactical`
3. `state_changes -> state_changes_summary -> final_state_updates / actual_truth / world_state`

## 5. Pass 2. Semantic Classification

### Class A. Primary realization when this lane is reactivated

- shared authority-strength vocabulary
- shared episode-mission vocabulary
- shared repair/finalization vocabulary
- explicit owner matrix for post-finalization truth surfaces

### Class B. Residual but related

- Stage3 compiler/substep compression
- Stage2 keep-or-drop field cleanup
- Stage4 consumer-side prompt/prose de-flattening

### Class C. Explicitly deferred outside this lane

- active Stage4 canary/closure work
- Stage4 global resume decision
- full Stage3 compression
- large architecture reduction from `2/3/4` to `2/4`

## 6. Side-Effect Map

- file writes / artifacts:
  - contract docs and code-facing field family normalization may change serialized repair/state payloads

- DB / schema / transaction boundaries:
  - no schema redesign in this lane
  - existing payload field families may be normalized or receive compatibility metadata

- JSONL / log / audit sinks:
  - operator-visible field names may become more explicit and more uniform

- console / UI / operator output:
  - owner and repair-scope lineage may become clearer

- rollback / recovery / retry:
  - repair-routing and post-select behavior may change once shared repair vocabulary is normalized

- cache / global state:
  - context-builder and cross-stage packet caches may need bounded key alignment

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

This future wave sits above the current Stage4 seam docs. It should reuse, not replace, the evidence and substrate already produced by:

- `0_0-stage4-consumer-contract-normalization-remediation`
- `0_0-stage4-post-select-continuity-contract-normalization-remediation`
- `0_0-stage4-fixpack-finalization-remediation`
- `0_0-stage4-canonical-entity-postselect-remediation`
- parked Stage3 and Stage2 normalization docs

The architectural rule for this lane:

- define the canonical cross-stage concept family first
- define owner and strength next
- only then normalize the code surface that transports or consumes the concept

## 8. Execution Tranches

### Tranche 1. Shared Vocabulary Contract

Goal:

- formalize shared concept families across Stage2/3/4

Targets:

- authority strength family
- episode mission family
- repair/finalization family
- post-finalization truth family

Outputs:

- one canonical matrix or contract doc
- one code-facing vocabulary mapping for repeated fields and aliases

### Tranche 2. Owner and Strength Normalization

Goal:

- remove or explicitly govern owner collisions and strength inversion

Targets:

- `fix_scope / authoritative_fix_scope / repair_scope`
- `final_state_updates / actual_truth / world_state`
- `constraint_summary` family strength normalization

Outputs:

- explicit owner-precedence contract
- explicit strength-by-stage contract

### Tranche 3. Boundary Transport Tightening

Goal:

- preserve machine-readable authority where it is currently flattened or renamed away

Targets:

- `Stage2 -> Stage3` mission and state packet aliases
- `Stage3 -> Stage4` machine-readable constraint survival
- bounded Stage4 intake/post-pass term normalization

Outputs:

- narrowed boundary normalization patches
- compatibility metadata where immediate deletion is too risky

## 9. Acceptance Criteria

- the highest-cost shared concept families have a canonical vocabulary
- each major concept has an explicit authoritative owner
- each major concept has an explicit strength classification by stage
- known split-truth concepts no longer rely on implicit owner inference
- future Stage-count simplification can cite this matrix instead of intuition

## 10. Verification Plan

- re-run 3-pass audit against the live workspace before any code patching from this document
- validate canonical/temp mirror integrity with `python scripts/ops_validator.py --strict`
- validate UTF-8 hygiene on the SSOT and mirror
- when reactivated later, use bounded static audit first and runtime proof only after patch landing

## 11. Guardrails

- do not activate this wave ahead of current Stage4 active seams without explicit reprioritization
- do not turn this into a repo-wide blind rename wave
- do not delete Stage3 as part of this lane
- do not introduce DB schema migration in the first activation tranche
- keep compatibility/alias bridges explicit while old and new terms coexist

## 12. Temp Queue Notes

- temp status: parked
- cleanup condition:
  - remove the mirror only on explicit closure, replacement, or strategic cancellation
- roadmap dependency:
  - remains below the current active Stage4 consumer/finalization lane
  - remains above or alongside longer-term Stage3/Stage2 simplification discussion as the contract substrate

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

---

## 3-Pass Audit Record

Pass 1. Structure and scope
- document type matches a parked execution SSOT
- scope is bounded to cross-stage contract normalization, not a broad rewrite
- active Stage4 seams remain out of scope and higher priority

Pass 2. Evidence and consistency
- claims are bounded to the new matrix survey and prior Stage2/Stage3/Stage4 surveys
- source docs and evidence artifacts are coherent
- queue semantics align with existing parked Stage2/Stage3 future waves

Pass 3. Execution and readability
- tranches are ordered from contract definition to boundary normalization
- operating consequence and guardrails are explicit
- overreach trimmed: no immediate architecture compression or stage deletion

Confidence: 96%
