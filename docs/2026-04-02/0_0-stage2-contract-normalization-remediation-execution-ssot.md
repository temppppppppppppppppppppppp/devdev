# 0_0 Stage2 Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: parked (survey-backed future wave; narrowed to Stage2-owned packet extraction and keep-drop normalization; not active while active Stage4 finalization seams remain higher priority)
Canonical Path: `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
- Baseline Dirty Summary: `dirty: canary_0_0_stage34_arc2_fixpack_r1 runtime logs/db/artifacts modified; 2026-04-02 Stage2 survey docs and lane drafts untracked`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- `docs/2026-04-01/0_0-stage2-stage3-context-hierarchy-bounded-survey.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-bounded-survey.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage2-production-consumption-global-evidence.json`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-evidence.json`
Side-Effect Coverage: covered

## 1. Intent

Preserve a bounded, implementable future wave for `Stage2 contract normalization` without promoting it into the active queue ahead of current `Stage3 static survey` and unresolved `Stage4` finalization seams.

This execution SSOT exists because the latest survey already proved:

- `Stage2` has a real problem
- but that problem is primarily `authority packaging / contract drift`, not missing narrative content
- the first material drift still appears at `Stage3`
- therefore `Stage2` should be queued as a future upstream normalization wave, not treated as the immediate blocker

## 2. Baseline Facts

- `Stage2` is `content-sufficient but schema-fragile`.
- The strongest mission truth lives in `tactical_doc` prose rather than a strong structured packet.
- `constraint_summary` undergoes strength inversion downstream.
- `beat_sequence` and `hybrid_composition` are effectively dropped at the `Stage2 -> Stage3` boundary.
- `semantic_carryover` behaves like a dead or low-signal field in current practice.
- The first clearly visible narrative drift still appears in `Stage3`, not inside Stage2 artifacts themselves.

## 3. Scope

Included:

- `modules/domain/agents/arc_ensemble.py`
- `config/prompts/ensemble.yaml`
- bounded Stage2 mission-authority packet extraction and emission surfaces
- bounded Stage2-owned alias/export normalization at the Stage2 emission boundary
- bounded keep-or-drop normalization for Stage2-owned low-signal fields
- regression coverage for Stage2 packet meaning and field survival

Excluded:

- downstream consumer-side rename sweep across `Stage3` / `Stage4`
- `Stage3` contract tightening
- `Stage4` remediation work
- fresh canary or runtime closure proof in this lane
- DB schema redesign
- artifact rewrites in `projects/`
- large terminology rename sweep across the whole repo in one turn

## 4. Pass 1. Inventory Summary

Primary Stage2 authority owners:

- `ArcEnsembleGenerator` and related Stage2 prompt/packet builders
- Stage2 artifact emission under `projects/*/plans/` and Stage2 log artifacts

Primary debt inventory for this wave:

1. mission truth trapped in `tactical_doc` prose
2. weak or thin structured bridge fields
3. Stage2-owned fields without explicit keep-or-drop policy
4. Stage2 emission aliases that blur the real canonical packet owner

## 5. Pass 2. Semantic Classification

### Class A. Primary realization when this lane is reactivated

- structured mission authority extraction from `tactical_doc`
- Stage2-owned packet alias normalization at emission time
- keep-or-drop decisions for dead or low-signal Stage2 fields

### Class B. Residual but related

- downstream consumer-side vocabulary alignment
- `constraint_summary` strength normalization across stages
- Stage3 compiler/substep reduction

### Class C. Explicitly deferred outside this lane

- active `Stage4` finalization seams
- current `Stage3` contract tightening future wave
- fresh canary/runtime proof
- broad architecture compression beyond this bounded packet/contract wave

## 6. Side-Effect Map

- file writes / artifacts:
  - future Stage2 prompt packet and emitted authority structure may change
  - future Stage2 artifact shape may shift where structured packet fields are strengthened

- DB / schema / transaction boundaries:
  - not applicable for this bounded future wave

- JSONL / log / audit sinks:
  - packet field names and summary rendering may change in future surveys and audits

- console / UI / operator output:
  - Stage2 authority packet logging may become more explicit

- rollback / recovery / retry:
  - not primary in this lane

- cache / global state:
  - possible packet cache key or shared-context shape impact if field names are normalized

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### Tranche 1. Mission Authority Extraction

Goal:

- stop relying on prose `tactical_doc` as the only real mission owner

Realization direction:

- derive a stronger structured mission packet from `tactical_doc`
- strengthen `episode_details` or replace its weak role with a more explicit canonical packet

### Tranche 2. Contract Vocabulary Normalization

Goal:

- make the Stage2 emission owner explicit without widening into downstream rename cleanup

Realization direction:

- normalize Stage2-owned packet aliases at the emission boundary
- reduce ambiguity between `tactical_doc`, `episode_details`, and the canonical mission packet

### Tranche 3. Dead-Field Keep-or-Drop Cleanup

Goal:

- stop carrying fields that are present but non-authoritative

Realization direction:

- explicit keep-or-drop decisions for:
  - `beat_sequence`
  - `hybrid_composition`
  - `semantic_carryover`

## 8. Execution Tranches

1. Stage2 mission packet normalization
2. Stage2-owned packet alias normalization
3. dead-field keep-or-drop cleanup
4. bounded regression coverage
5. later runtime proof only after explicit reactivation

## 9. Acceptance Criteria

- Stage2 no longer relies on prose `tactical_doc` alone for mission authority
- Stage2 exports a stronger canonical mission packet or equivalent structured authority owner
- Stage2-owned field aliases no longer obscure which packet is canonical at emission time
- `beat_sequence`, `hybrid_composition`, and `semantic_carryover` each have an explicit keep-or-drop policy
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted Stage2 packet rendering regressions
- targeted Stage2 packet alias and field-survival regressions
- `python -m py_compile` on touched production modules
- `ruff check` on touched files
- targeted pytest shards only
- `python scripts/check_utf8_hygiene.py` on touched docs/code
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not let this parked wave outrank active `Stage4` finalization seams without explicit reprioritization
- do not widen this lane into downstream consumer rename cleanup in the same turn
- do not widen this lane into `Stage3` contract tightening in the same turn
- do not run a canary from this lane until explicit reactivation
- do not rewrite artifact history in `projects/`

## 12. Temp Queue Notes

- temp status: `parked`
- cleanup condition:
  - keep the temp mirror as a future-wave queue item until explicit closure or formal deactivation
- roadmap dependency:
  - this item stays below active `Stage4` lanes and below the nearer `Stage3` contract-tightening future wave

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a future bounded execution SSOT, not an active lane
- narrowed the lane to Stage2-owned packet extraction, alias normalization, and keep-or-drop policy only
- excluded downstream consumer rename cleanup, Stage3 tightening, and Stage4 remediation from scope

Pass 2, evidence and consistency:

- aligned the document with the global Stage2 production-consumption survey verdict
- kept claims bounded to known survey evidence and did not overclaim runtime impact

Pass 3, execution and readability:

- made the parking status explicit
- made the reactivation condition explicit
- kept tranches upstream-only and implementable rather than architectural-only

Confidence: `96%`
