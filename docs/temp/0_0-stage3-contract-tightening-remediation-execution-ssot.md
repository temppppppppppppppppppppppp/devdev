# 0_0 Stage3 Contract Tightening Remediation Execution SSOT

Date: 2026-04-02
Status: partially_realized (promoted from parked on 2026-04-07 roadmap reorder; re-audited again against the current workspace before implementation start; the first bounded tranche then landed by widening binding enforcement for `dead_npc`, stop-line/`arc_compliance`, and `fact_lock_*` seams, persisting binding metadata through Stage3 success handoff, and teaching Stage4 to consume that metadata as real Director/retry pressure; explicit tier-2.5 canary proof still remains required before closure)
Canonical Path: `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
- Baseline Dirty Summary: `dirty: canary_0_0_stage34_arc2_fixpack_r1 runtime logs/db/artifacts modified; 2026-04-02 Stage2/Stage3 survey docs and lane drafts untracked`
- Resume Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Resume Drift Summary: `the queue was later re-ranked to make this the next unopened implementation lane, the 2026-04-07 Stage234 terminal survey confirmed the still-live Stage3 seams as binding-scope gaps plus advisory-only `_stage3_meta` handoff, the originally listed static survey and runtime closure audit now live under archived `docs/이전/` paths, the previously referenced Stage3 artifact JSON paths are no longer present in the active workspace so this SSOT now relies on the archived survey/evidence set plus the 2026-04-07 handoff survey rather than stale artifact-local pointers, and the current workspace has now landed a bounded first tranche across `unified_blueprint_validator.py`, `three_phase_blueprint_runtime.py`, `stage3_orchestrator.py`, `stage4_director_runtime.py`, and `stage4_outcome_runtime.py` with focused regression/static validation while fresh tier-2.5 canary proof stays deferred`
Source Survey Docs:
- `docs/이전/2026-04-02/0_0-stage3-static-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- `docs/이전/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`
- `docs/2026-04-07/stage234-terminal2-stage3-binding-handoff-survey.md`
Evidence Artifacts:
- `docs/이전/2026-04-02/0_0-stage3-static-global-evidence.json`
- `docs/이전/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-evidence.json`
Side-Effect Coverage: covered

## 1. Intent

Preserve a bounded queued lane for `Stage3 contract tightening` without promoting it ahead of active `Stage4` remediation seams.

This execution SSOT exists because the latest static survey proved:

- Stage3 is not hierarchy-free chaos
- Stage3 still remains the first material drift point in artifact truth
- the core problem is `weak enforcement + semantically lossy handoff`, not missing prompt structure alone

## 2. Baseline Facts

- Stage3 generation hierarchy is explicit and reasonably well-structured.
- Stage3 validator/binding is advisory-heavy and cannot independently hard-block the most dangerous seams.
- Stage3 -> Stage4 handoff is transport-clean but semantic-lossy.
- Off-arc invention improved under prior semantic-fidelity work, but timeline/institution drift remains.
- The most important residual debt is not Stage2 content starvation but Stage3 contract enforcement weakness.

## 3. Scope

Included:

- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- bounded Stage3 binding-scope and escalation hardening surfaces
- bounded Stage3 -> Stage4 semantic handoff preservation where Stage3 owns the machine-readable contract
- targeted Stage3-owned contract metadata emission required to preserve downstream subtype fidelity

Excluded:

- broad Stage3 prompt or generation retuning
- active Stage4 fix-pack/finalization work
- Stage2 contract normalization
- fresh canary execution in this lane
- DB schema redesign
- broad architecture compression in the same turn

## 4. Pass 1. Inventory Summary

Primary debt inventory for this wave:

1. binding scope gap
2. advisory-only enforcement after Python prevalidation
3. structured constraint truth surviving only as prose blueprint semantics at handoff
4. timeline and institution fidelity categories lacking strong Stage3-owned contract coverage

## 5. Pass 2. Semantic Classification

### Class A. Primary realization when this lane is reactivated

- binding scope tightening
- Stage3 -> Stage4 semantic contract preservation
- targeted timeline/entity/institution contract tightening only where validator/compiler owns the contract

### Class B. Residual but related

- broad Stage3 prompt retuning
- further reduction of off-arc invention pressure in cold-start episodes
- context caching hierarchy degradation risk

### Class C. Explicitly deferred outside this lane

- current active Stage4 remediation lanes
- Stage2 contract normalization
- fresh canary execution in this turn
- Stage3 external-stage compression itself

## 6. Side-Effect Map

- file writes / artifacts:
  - future Stage3 blueprint artifact shape and metadata may change

- DB / schema / transaction boundaries:
  - not applicable for this bounded pending lane

- JSONL / log / audit sinks:
  - Stage3 prevalidation and verdict metadata may become richer or more binding

- console / UI / operator output:
  - advisory / binding categories and severity visibility may change

- rollback / recovery / retry:
  - stronger Stage3 binding can increase early-stage rejection or PASS_WITH_FIX frequency

- cache / global state:
  - cached shared context or model packet ordering could be impacted by contract strengthening

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### Tranche 1. Binding Scope Tightening

Goal:

- stop leaving high-severity seams outside effective binding behavior

Realization direction:

- review category membership and escalation semantics for high-severity Stage3 seams
- tighten which issues remain advisory-only

### Tranche 2. Timeline / Institution Fidelity Tightening

Goal:

- close timeline / institution seams only where Stage3 validator or compiler owns the contract

Realization direction:

- tighten high-severity category coverage for timeline / institution seams
- avoid broad generation retuning in the same lane

### Tranche 3. Semantic Handoff Preservation

Goal:

- make Stage4 receive stronger machine-meaningful Stage3 contract hints

Realization direction:

- preserve more Stage3 semantic subtype information at the handoff boundary
- reduce reliance on prose-only fidelity survival
- emit only the minimum Stage3-owned metadata needed for downstream bounded repair or verification

## 8. Execution Tranches

1. binding scope and escalation tightening
2. Stage3 -> Stage4 semantic contract preservation
3. targeted timeline/entity/institution contract tightening
4. bounded regression coverage
5. later runtime proof only after explicit reactivation

## 8A. Implementation Update (2026-04-07)

- Tranche 1 landed in bounded form:
  - `dead_npc`, `arc_compliance`, `fact_lock_location`, `fact_lock_item`, and `fact_lock_provenance` now participate in Stage3 binding escalation when severity is `MAJOR/CRITICAL`
- Tranche 2 landed in bounded handoff form:
  - Stage3 validation/runtime now preserves `binding_prevalidation_issue_count` plus category metadata through `pipeline_result["phases"]["validate"]` and persisted `_stage3_meta`
  - Stage4 Director and retry escalation now consume those Stage3-owned binding signals as structured caution/escalation input instead of treating them as dead handoff fields
- fresh runtime proof remains deferred:
  - focused pytest, `py_compile`, and `ruff` closed
  - explicit tier-2.5 canary proof is still required before closure

## 9. Acceptance Criteria

- highest-risk Stage3 seams no longer remain purely advisory by default
- Stage3 -> Stage4 handoff preserves more than prose-only semantics for key contract fields
- timeline and institution drift have stronger structured enforcement paths where Stage3 validator/compiler owns the contract
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted Stage3 validator regressions
- targeted Stage3 handoff contract regressions
- `python -m py_compile` on touched production modules
- `ruff check` on touched files
- targeted pytest shards only
- `python scripts/check_utf8_hygiene.py` on touched docs/code
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not activate this lane before explicit operator decision
- do not let this partial lane outrank current active Stage4 seams without deliberate reprioritization
- do not widen this lane into broad Stage3 prompt retuning
- do not widen this lane into Stage2 redesign or Stage4 redesign
- do not run a canary from this lane until explicit operator approval

## 12. Temp Queue Notes

- temp status: `in_progress`
- cleanup condition:
  - keep the temp mirror as an active verification-pending queue item until explicit closure or replacement
- roadmap dependency:
  - this item stays below active Stage4 lanes and the narrower pending Stage4/Stage2 child slices

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a bounded execution SSOT tied to the live queue rather than widening it into a broad Stage3 rewrite
- narrowed this wave to validator/binding enforcement plus semantic handoff preservation
- excluded broad Stage3 prompt retuning, Stage2 normalization, and active Stage4 remediation from scope

Pass 2, evidence and consistency:

- aligned the document with the archived Stage3 static global survey verdict and the archived runtime closure audit
- refreshed the source/evidence paths so they match the current workspace layout
- removed stale Stage3 artifact-local pointers that no longer exist in the active workspace
- incorporated the 2026-04-07 Stage234 terminal survey as the latest narrow handoff/binding confirmation

Pass 3, execution and readability:

- made the pending promotion explicit
- kept tranches validator/compiler-owned and implementable
- tied future activation to an explicit canary-proof gate rather than implicit urgency

Confidence: `98%`
