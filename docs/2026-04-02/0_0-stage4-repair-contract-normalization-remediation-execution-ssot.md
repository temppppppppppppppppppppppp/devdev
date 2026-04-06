# 0_0 Stage4 Repair-Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: partially_realized (survey-backed promotion complete; bounded sink/readback fixes have landed, but shared grammar and first-class repair metadata normalization remain open)
Canonical Path: `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `aaf495d65c95c9ffe7ea99277f315a69609252db`
- Baseline Dirty Summary: `dirty: Stage4 contract docs/code/test deltas active; roadmap/temp queue already dirty; current ep2 canary work in progress`
- Resume Commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`
- Resume Drift Summary: `the lane no longer sits at pure survey status: bounded `stage4_interview_round.py` and `db_manager.py` fixes tightened fix-scope/readback behavior, and the 2026-04-06 global P0-P1 survey confirmed the remaining live repair-contract seam is phantom mismatch inflation across repair_scope/gate_basis/readback surfaces rather than a broad Stage4 sink failure`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage4-repair-contract-grammar-global-bounded-survey.md`
- `docs/2026-04-06/rol-global-terminal4-stage4-pipeline-p0p1.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage4-repair-contract-grammar-global-evidence.json`
Side-Effect Coverage: covered
Parent Lane:
- `0_0-stage4-consumer-contract-normalization-remediation`

## 1. Intent

Promote the Stage4 repair-contract grammar survey into one bounded execution SSOT that targets shared contract debt across detector emission, retry/reject routing, post-pass finalization, and operator-visible sinks.

This lane is not a fresh bugfix wave for one episode. It exists to normalize the common grammar that Stage4 already uses inconsistently:

- subtype naming
- local-fix contract field names
- provenance visibility
- fix-scope ownership visibility
- operator sink propagation

This lane is intentionally below the active `ep2` runtime verification stack. It is a parked contract-normalization wave, not the immediate runtime blocker.

## 2. Baseline Facts

- Stage4 does not currently have one canonical repair-contract grammar.
- Current behavior is family-specific and ad hoc across:
  - `flashback`
  - `npc_drift`
  - `post_select_conflict`
  - reject snapshotting
  - retry routing
- The largest verified contract drifts are:
  - subtype naming fragmentation
  - operator sink blackout for structured repair fields
  - invisible widening from `authoritative_fix_scope` to runtime-derived scope
- 2026-04-06 revalidation narrows the still-live P1 to a specific readback class:
  - `repair_scope`, `gate_basis`, `repair_contract` grammar, and scope-authority metadata can still surface as phantom sink mismatches because first-class persistence and readback normalization are incomplete
- The survey identified a minimum common field set of 12 fields:
  - `check`
  - `severity`
  - `text`
  - `target_kind`
  - `subtype`
  - `expected_truth`
  - `local_fix_hint`
  - `local_fixable`
  - `patch_targets`
  - `must_fix`
  - `fix_scope`
  - `provenance`
- The survey conclusion was explicit: execution SSOT promotion is warranted, but the first realization tranche should be sink visibility and naming normalization, not broad redesign.

## 3. Scope

Included:

- `modules/core/flashback_verifier.py`
- `modules/core/npc_drift_advisor.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_immutable_fact_contract.py`
- `modules/core/db_manager.py`
- `modules/core/failure_analyzer.py`
- operator-visible Stage4 sink surfaces:
  - runtime evidence json
  - summary payloads
  - session decision / ui event payloads where applicable

Excluded:

- Stage2 contract normalization
- Stage3 contract tightening
- canary integrity redesign
- broad Director prompt redesign
- DB schema redesign
- fresh canary execution in this document
- global Stage4 closure declaration

## 4. Pass 1. Inventory Summary

Primary grammar surfaces:

- emission:
  - `flashback_verifier.py`
  - `npc_drift_advisor.py`
- routing:
  - `stage4_interview_round.py`
  - `stage4_retry_runtime.py`
  - `stage4_reject_runtime.py`
- finalization:
  - `stage4_post_pass_runtime.py`
  - `stage4_post_processor.py`
- sink:
  - audit/evidence/session output surfaces already used by Stage4 runtime reporting

Primary debt inventory:

1. the same semantic concept appears under multiple field names
2. structured repair fields are created and consumed internally but do not reach operator-visible outputs
3. Director-authored versus runtime-synthesized repair authority is not visible enough
4. fix-scope widening can occur without preserving the original authoritative scope in operator-facing summaries
5. post-pass truth surfaces and repair-contract truth are still too disconnected
6. metadata-absence artifacts can still inflate sink-alignment mismatch reports at readback time

## 5. Pass 2. Semantic Classification

### Class A. Primary realization now

- unify subtype naming into one canonical field family
- wire `provenance`, `fix_scope`, and `subtype` into operator-visible sinks
- preserve `authoritative_fix_scope` versus runtime-derived scope in operator evidence

### Class B. Secondary realization

- normalize `expected_truth` / `local_fix_hint` / `local_fixable` across family emitters
- normalize sink payload names so runtime evidence and summaries do not drift

### Class C. Explicitly deferred outside this lane

- broad Stage4 architectural split
- Stage2/3 upstream schema work
- Director micro-fix experiments
- canary redesign / hash-pin integrity work

## 6. Side-Effect Map

- file writes / artifacts:
  - Stage4 runtime evidence and summary artifacts may gain new structured repair fields

- DB / schema / transaction boundaries:
  - no schema change intended
  - payload content may become richer where repair-contract metadata is already persisted

- JSONL / log / audit sinks:
  - expected primary impact area
  - operator-visible structured fields should become available without changing decision ownership

- console / UI / operator output:
  - operator should be able to see at least `subtype`, `fix_scope`, and `provenance`
  - authoritative versus runtime-widened scope should no longer be silently hidden

- rollback / recovery / retry:
  - retry routing behavior should remain stable; this lane is primarily visibility and naming normalization

- cache / global state:
  - not a primary target

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

This lane sits under the aggregate Stage4 consumer-contract wave and above individual family seams.

Read it as:

- a shared grammar-and-sink substrate
- not a replacement for `flashback`, `npcdrift`, or `post_select` child lanes
- a contract normalization lane that should reduce future family-specific drift

Dependency posture:

- active `ep2` runtime verification outranks this lane
- this lane should not be used to justify broad Stage4 redesign
- realization should stay bounded to grammar normalization and sink exposure first

## 8. Execution Tranches

### Tranche 1. Minimum Grammar Canonicalization

Goal:

- normalize the minimum 12-field repair-contract set into one canonical naming contract

Primary targets:

- `stage4_interview_round.py`
- `flashback_verifier.py`
- `npc_drift_advisor.py`

Acceptance shape:

- subtype naming no longer fragments across `contradiction_subtype`, `drift_subtype`, inferred `subtype`, and `contradiction_types` without a canonical bridge

### Tranche 2. Operator-Visible Sink Wiring

Goal:

- make at least `subtype`, `fix_scope`, and `provenance` operator-visible in bounded Stage4 sinks

Primary targets:

- Stage4 runtime evidence / summary builders
- session decision / audit sink payload assembly

Acceptance shape:

- operator-visible JSON no longer drops all structured repair metadata
- the first promoted sink fields are visible without requiring log-text inference

### Tranche 3. Scope and Provenance Boundary Exposure

Goal:

- expose `authoritative_fix_scope` versus runtime-widened scope and normalize provenance wording

Primary targets:

- `stage4_reject_runtime.py`
- `stage4_post_pass_runtime.py`
- `stage4_interview_round.py`
- `db_manager.py`
- `failure_analyzer.py`
- shared payload builders used by summaries and operator sinks

Acceptance shape:

- scope widening is visible rather than silent
- Director-authored and runtime-synthesized contracts remain distinguishable end-to-end
- readback summaries no longer overcount mismatches merely because first-class repair metadata is missing or inconsistently surfaced

## 9. Acceptance Criteria

- one canonical repair-contract grammar exists for the minimum field set
- subtype naming fragmentation is reduced to one explicit bridge or one canonical field name
- at least `subtype`, `fix_scope`, and `provenance` reach operator-visible Stage4 JSON outputs
- `authoritative_fix_scope` versus runtime-derived scope is no longer hidden in operator-facing evidence
- readback and sink-alignment summaries no longer report phantom repair mismatches caused only by metadata-absence artifacts
- realization stays bounded and does not expand into broad Stage4 redesign

## 10. Verification Plan

- focused unit/regression tests for Stage4 payload builders and sink serialization
- focused regressions for:
  - `tests/test_stage4_interview_round.py -k "build_stage4_db_attempt_payload or stage4_db_attempt_payload" -q`
  - `tests/test_db_manager.py -k "latest_stage4_gate_repair_snapshot" -q`
  - `tests/test_failure_analyzer.py -k "nested_gate_semantics or gate_repair_contract_fields or scope_authority" -q`
  - `tests/test_stage4_canary_tools.py -k "build_stage4_canary_summary" -q`
- `python -m py_compile` on touched files
- `ruff check` on touched files
- UTF-8 hygiene on touched docs/code
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not let this lane outrank active `ep2` runtime blocker verification
- do not use this lane to justify broad refactor or schema redesign
- do not collapse Director authority into runtime sink convenience
- do not add new repair-contract aliases unless they are part of an explicit canonicalization bridge

## 12. Temp Queue Notes

- temp status: partial
- cleanup condition:
  - remove the temp mirror only after bounded realization closes or the lane is superseded by a broader Stage4 contract wave
- roadmap dependency:
  - subordinate to `0_0-stage4-consumer-contract-normalization-remediation`
  - below active `ep2` runtime verification work
  - remains the next open Stage4 substrate because numeric carryover work still depends on shared repair/readback grammar staying truthful

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

---

3-pass audit status:

- Pass 1. Structure and Scope: execution SSOT type, bounded Stage4 grammar scope, and excluded surfaces confirmed
- Pass 2. Evidence and Consistency: survey/evidence lineage, field-set summary, operator-sink conclusions, and the 2026-04-06 readback phantom-mismatch revalidation are aligned
- Pass 3. Execution and Readability: tranches, acceptance criteria, guardrails, and repair/readback owner files are actionable and bounded
- Confidence: 0.97

## 14. 2026-04-06 Opus P0-P1 Revalidation: Repair Readback Phantom Mismatch

The 2026-04-06 global P0-P1 Opus survey converted the remaining Stage4 repair-contract debt into a narrower execution statement than the original survey-backed promotion.

Queue semantics remain unchanged:

- this lane stays below the aggregate Stage4 consumer lane
- this lane stays above parked future-wave Stage2/3 work
- queue order does not change

Confirmed live P1:

- `stage4_interview_round.py` can correctly derive `repair_scope`, `gate_basis`, `scope_authority`, and `authoritative_fix_scope`
- but those fields are not yet normalized as first-class readback truth across all persistence/sink surfaces
- `FailureAnalyzer` and related summary/readback surfaces can therefore count `repair_scope`, `gate_basis`, `repair_contract_subtype`, or scope-authority fields as mismatches when the underlying issue is metadata absence or inconsistent sink exposure rather than verdict disagreement

2026-04-06 bounded realization note:

- the recent bounded fixes in `stage4_interview_round.py` and `db_manager.py` improved:
  - root `fix_scope` alignment with resolved `scope_authority`
  - latest gate-repair snapshot fallback/readback for root and nested scope metadata
- those fixes reduce the seam, but they do not fully close the broader repair-contract grammar/readback normalization lane

Execution consequence:

- the narrowest active owner set for this residual P1 is:
  - `modules/core/stage4_interview_round.py`
  - `modules/core/db_manager.py`
  - `modules/core/failure_analyzer.py`
- this remains the correct Stage4 substrate lane for sink-visibility, scope/provenance boundary, and phantom-mismatch normalization

Revalidation note:

- static evidence is sufficient to keep this as a live execution SSOT
- fresh run is helpful for measuring mismatch volume, but not required to prove the readback seam exists
