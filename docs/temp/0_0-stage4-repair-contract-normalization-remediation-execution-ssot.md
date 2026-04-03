# 0_0 Stage4 Repair-Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: parked (survey-backed promotion complete; sink-wiring and naming-normalization tranche not yet realized)
Canonical Path: `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `aaf495d65c95c9ffe7ea99277f315a69609252db`
- Baseline Dirty Summary: `dirty: Stage4 contract docs/code/test deltas active; roadmap/temp queue already dirty; current ep2 canary work in progress`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `promoted directly from bounded survey while active ep2 runtime verification remains in flight; no realization work started from this SSOT`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage4-repair-contract-grammar-global-bounded-survey.md`
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
- shared payload builders used by summaries and operator sinks

Acceptance shape:

- scope widening is visible rather than silent
- Director-authored and runtime-synthesized contracts remain distinguishable end-to-end

## 9. Acceptance Criteria

- one canonical repair-contract grammar exists for the minimum field set
- subtype naming fragmentation is reduced to one explicit bridge or one canonical field name
- at least `subtype`, `fix_scope`, and `provenance` reach operator-visible Stage4 JSON outputs
- `authoritative_fix_scope` versus runtime-derived scope is no longer hidden in operator-facing evidence
- realization stays bounded and does not expand into broad Stage4 redesign

## 10. Verification Plan

- focused unit/regression tests for Stage4 payload builders and sink serialization
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

- temp status: parked
- cleanup condition:
  - remove the temp mirror only after bounded realization closes or the lane is superseded by a broader Stage4 contract wave
- roadmap dependency:
  - subordinate to `0_0-stage4-consumer-contract-normalization-remediation`
  - below active `ep2` runtime verification work

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

---

3-pass audit status:

- Pass 1. Structure and Scope: execution SSOT type, bounded Stage4 grammar scope, and excluded surfaces confirmed
- Pass 2. Evidence and Consistency: survey/evidence lineage, field-set summary, and operator-sink conclusions aligned
- Pass 3. Execution and Readability: tranches, acceptance criteria, and guardrails are actionable and bounded
- Confidence: 0.96
