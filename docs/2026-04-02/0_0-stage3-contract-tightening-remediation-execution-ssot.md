# 0_0 Stage3 Contract Tightening Remediation Execution SSOT

Date: 2026-04-02
Status: parked (survey-backed future wave; narrowed to binding and semantic-handoff enforcement only; explicit tier-2.5 canary proof pending, no execution yet)
Canonical Path: `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
- Baseline Dirty Summary: `dirty: canary_0_0_stage34_arc2_fixpack_r1 runtime logs/db/artifacts modified; 2026-04-02 Stage2/Stage3 survey docs and lane drafts untracked`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage3-static-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage3-static-global-evidence.json`
- `projects/0_0/logs/artifacts/stage3/ep_0005/attempt_06/final_blueprint__action_focused.json`
- `projects/0_0/logs/artifacts/stage3/ep_0006/attempt_09/final_blueprint__dialogue_focused.json`
- `projects/canary_0_0_stage3_arc2_semantic_r5/logs/artifacts/stage3/ep_0005/attempt_02/final_blueprint__dialogue_focused.json`
Side-Effect Coverage: covered

## 1. Intent

Preserve a bounded future wave for `Stage3 contract tightening` without promoting it ahead of active `Stage4` remediation seams.

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
  - not applicable for this bounded future wave

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
- do not let this parked wave outrank current active Stage4 seams without deliberate reprioritization
- do not widen this lane into broad Stage3 prompt retuning
- do not widen this lane into Stage2 redesign or Stage4 redesign
- do not run a canary from this lane until explicit operator approval

## 12. Temp Queue Notes

- temp status: `parked`
- cleanup condition:
  - keep the temp mirror as a future-wave queue item until explicit closure or replacement
- roadmap dependency:
  - this item stays below active Stage4 lanes and above the more distant Stage2 normalization future wave

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a future bounded execution SSOT, not an active lane
- narrowed this wave to validator/binding enforcement plus semantic handoff preservation
- excluded broad Stage3 prompt retuning, Stage2 normalization, and active Stage4 remediation from scope

Pass 2, evidence and consistency:

- aligned the document with the Stage3 static global survey verdict
- bounded claims to surveyed static evidence and prior artifact truth only

Pass 3, execution and readability:

- made the parking status explicit
- kept tranches validator/compiler-owned and implementable
- tied future activation to an explicit canary-proof gate rather than implicit urgency

Confidence: `96%`
