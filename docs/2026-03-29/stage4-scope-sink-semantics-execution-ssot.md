# Stage4 Scope Sink Semantics Execution SSOT

Date: 2026-03-29
Status: closed
Canonical Path: `docs/2026-03-29/stage4-scope-sink-semantics-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-scope-sink-semantics-execution-ssot.md`
Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty tracked drift in stage4/runtime/tests, provider/runtime code, temp queue artifacts, canary outputs, and unrelated narrative assets`
- Resume Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Resume Drift Summary: `same commit; the semantics wave landed, the follow-up scope_origin micro-fix landed, and later live evidence showed the remaining mixed verdict was an audit-reading issue rather than a reopen-worthy code defect`
Source Survey Docs:
- `docs/2026-03-29/stage4-scope-sink-semantics-full-survey-audit-order.md`
- `docs/2026-03-29/stage4-scope-sink-semantics-full-survey.md`
Evidence Artifacts:
- `projects/canary_0329_feedback_windowing_check/logs/episode_production.jsonl`
- `projects/canary_0329_retry_loop_compression_check/logs/episode_production.jsonl`
- `projects/canary_0329_retry_loop_compression_check/logs/session/decisions.jsonl`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/director_ensemble.py`
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe follow-up after retry-loop compression.

The live canary shows the behavioral loop is now much healthier.
The remaining high-ROI defect is semantic ambiguity in operator-facing sinks:

> multiple Stage 4 fields with adjacent names now describe different semantic layers, but the sinks do not explicitly label those layers, and carryover metadata is only partially persistent.

This wave is not a runtime policy redesign.
This wave is a bounded semantics-and-persistence clarification pass.

## 2. Baseline Facts

- `authoritative_fix_scope` now reaches the main JSONL sinks and correctly represents Director-origin scope
- `fix_scope` still carries multiple meanings depending on sink
- `repair_scope` is effectively the runtime lane view, but that meaning is implicit
- `reuse_contract` materially affects retry behavior but is not persisted to operator sinks
- `conflict_contract` is persisted on the pathology side, but not clearly linked on the resolved side
- high-score `post_select_conflict` rationale preservation is now working in live evidence
- some blanking paths still exist, but the remaining defect is lack of explicit elision labeling, not universal rationale loss
- DB schema rename would be too broad for the current ROI

## 3. Scope

Included:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/domain/agents/chief_writer.py`
- targeted tests:
  - `tests/test_stage4_interview_round.py`
  - one narrow sink/payload test file already covering retry-pathology or carryover payloads
- canonical execution SSOT and temp mirror maintenance

Excluded:

- DB schema migration or column rename
- lane routing changes
- `fix_scope` / `fix_pack` policy redesign
- provider/fallback work
- feedback-windowing work
- retry-loop-compression logic changes
- prompt redesign outside additive sink metadata or carryover persistence

## 4. Pass 1. Inventory Summary

- one naming overload:
  - `fix_scope`
- one implicit alias:
  - `repair_scope`
- two carryover payloads with incomplete persistence:
  - `conflict_contract`
  - `reuse_contract`
- one remaining unlabeled runtime transformation:
  - rationale elision when a path still blanks preserved rationale fields

## 5. Pass 2. Semantic Classification

- Class A: patch now
  - additive scope-origin metadata
  - `reuse_contract` persistence to at least one operator sink
  - conflict-resolution linkage on the resolved PASS side
  - rationale-elision marker where blanking still happens

- Class B: explicitly deferred
  - schema rename of `fix_scope`
  - DB migration to split semantic fields
  - retry routing or escalation changes
  - patch-lane / fix-pack redesign
  - provider observability merge

## 6. Side-Effect Map

- file writes / artifacts:
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_reject_runtime.py`
  - `modules/core/stage4_outcome_runtime.py`
  - `modules/domain/agents/chief_writer.py` only if the sink contract requires additive payload consumption or pass-through adjustment
  - targeted tests
  - canonical execution SSOT and temp mirror

- DB / schema / transaction boundaries:
  - no schema change allowed
  - additive JSON payload fields are allowed only where existing persistence paths already exist

- JSONL / log / audit sinks:
  - `decisions.jsonl`
  - `episode_production.jsonl`
  - retry pathology payloads
  - any additive metadata must preserve current fields rather than replace them

- console / UI / operator output:
  - no broad console redesign
  - additive clarity fields are allowed

- rollback / recovery / retry:
  - retry behavior must not change
  - this wave is interpretability-first

- cache / global state:
  - not applicable

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### 7.1 Scope Origin Contract

Each emitted scope-like field should explicitly disclose its layer.

Minimum contract:

- `authoritative_fix_scope_origin = "director_authoritative"`
- widened `fix_scope_origin = "runtime_widened"` or equivalent when the field is carrying runtime-resolved scope
- carried pathology scope should disclose that it comes from prior-attempt carryover
- `repair_scope_origin = "runtime_lane"`

Guardrail:

- additive only
- no field rename
- no removal of current fields

### 7.2 Carryover Persistence Contract

The operator should be able to tell:

- whether manuscript reuse was active
- what conflict payload was being resolved
- whether the resolved PASS was linked to a previous conflict

Minimum safe move:

- persist `reuse_contract` to at least one operator-facing sink
- add conflict-resolution linkage to the resolved side without changing retry behavior

Guardrail:

- no attempt to turn `reuse_contract` into routing logic
- no attempt to turn `conflict_contract` into patch-ready fix instructions

### 7.3 Rationale Elision Contract

Where runtime still intentionally blanks rationale fields, emit an additive marker such as:

- `rationale_blanked_by`
- or a semantically equivalent elision reason

Guardrail:

- do not re-open broad rationale preservation policy
- only label remaining blanking paths

### 7.4 Human-Facing Semantics Matrix

The audited survey itself is the canonical semantics matrix for this wave.
Implementation should align sink metadata with that matrix rather than invent a second competing contract.

## 8. Execution Tranches

1. Tranche 1: scope-origin labeling
   - add additive origin/layer metadata beside emitted scope fields
   - cover decisions, episode entries, and pathology entries where relevant

2. Tranche 2: carryover persistence
   - persist `reuse_contract`
   - add resolved-side linkage for `conflict_contract`
   - keep persistence additive

3. Tranche 3: rationale-elision labeling
   - label remaining runtime blanking paths
   - avoid changing preserved high-score paths that already passed live validation

4. Tranche 4: regression coverage
   - prove field meanings are separable in sinks
   - prove carryover metadata now survives into operator evidence
   - prove no routing behavior changed

## 9. Acceptance Criteria

- operators can distinguish Director-authoritative scope from runtime-widened scope from runtime lane scope without reading source code
- `reuse_contract` reaches at least one persistent operator-facing sink
- a resolved PASS can be linked back to the originating `conflict_contract` in operator evidence
- remaining rationale blanking paths carry an additive reason marker
- no schema change occurs
- no retry routing or lane semantics change occurs

## 10. Verification Plan

- targeted pytest for:
  - scope metadata emission in `tests/test_stage4_interview_round.py`
  - retry-pathology payload persistence in a narrow Stage 4 payload test
  - rationale-elision labeling in a narrow reject-path test
- `python -m py_compile` on touched code/tests
- `ruff check` on touched code/tests
- `python scripts/check_utf8_hygiene.py` on touched code/tests/docs
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

Fresh canary validation should happen after this wave lands, but it does not need the same large sample size as retry-loop compression because behavior is not supposed to change.

## 11. Guardrails

- do not rename DB columns in this wave
- do not change retry routing
- do not change `fix_scope` or `repair_scope` decision semantics
- do not reopen provider/fallback, feedback-windowing, or retry-loop-compression logic
- do not remove existing sink fields to force clarity; add explicit metadata instead
- do not introduce silent coupling between carryover persistence and routing behavior

## 12. Temp Queue Notes

- temp status: completed; mirror cleanup deferred to a dedicated closure sweep
- cleanup condition:
  - remove `docs/temp/stage4-scope-sink-semantics-execution-ssot.md` during the next dedicated closure sweep
- roadmap dependency:
  - refresh `docs/temp/execution-roadmap.md` during closure sweep so the queue reflects this item's closed status

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- queue sync command: `python scripts/sync_temp_queue_state.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule:
  - re-run this document's 3-pass audit and confirm at least `95%` confidence against the current workspace state before patching from it

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope

- bounded the wave to additive metadata and persistence only
- kept schema rename and routing changes explicitly excluded
- PASS

### Pass 2. Evidence and Consistency

- aligned the document with the newest retry-loop-compression canary
- reflected that rationale preservation is already fixed for the high-score downgraded path
- kept the remaining defect framed as semantics drift and persistence gaps
- PASS

### Pass 3. Execution and Readability

- tranches map directly to the residual high-ROI gaps
- acceptance criteria are operator-readable and behavior-preserving
- roadmap dependency is explicit
- PASS

Estimated confidence: `96%`

## 15. Closure Note

Date: 2026-03-29
Closure Status: closed

### 15.1 Realized Scope

- additive `scope_origin` metadata now reaches the main operator-facing JSONL sinks
- `reuse_contract` and resolved-side carryover metadata now persist into operator evidence
- remaining runtime rationale blanking paths now carry explicit elision labeling
- the follow-up micro-fix extended `scope_origin` into `decisions.jsonl` and preserved carried override provenance in retry pathology payloads

### 15.2 Verification Summary

- implementation verification:
  - targeted scope-sink regression shard: `9 passed`
  - broad Stage4 regression slice after landing: `227 passed` with `4` known pre-existing failures excluded from the wave
  - `python -m py_compile`, `ruff check`, UTF-8 hygiene, `sync_temp_queue_state.py`, and `ops_validator.py --strict` all passed at realization time
- follow-up micro-fix verification:
  - targeted regression shard: `3 passed`
  - `python -m py_compile`, `ruff check`, UTF-8 hygiene, `sync_temp_queue_state.py`, and `ops_validator.py --strict` all passed again
- live evidence:
  - the later `canary_0329_scope_sink_semantics_check` mixed report was re-read against raw sink rows
  - raw `decisions.jsonl` and `runtime_audit.jsonl` showed that the reported `fix_scope=director_authoritative` issue came from confusing actual scope values with `scope_origin` provenance labels
  - no additional code defect was confirmed from that canary

### 15.3 Residual Risks

- operator audits can still misread actual scope values versus `scope_origin` labels unless the reading template stays explicit
- resolved-side `conflict_resolution_linkage` is test-verified but was not re-observed in a dedicated live canary that actually resolved from a prior conflict contract
- temp mirror cleanup is still pending

### 15.4 Follow-Up

- next queue action: dedicated closure sweep for completed Stage4 execution mirrors
- low-priority follow-up only if ROI rises: improve canary audit reading rules so provenance labels are not mistaken for actual scope values

### 15.5 Temp Cleanup

- execution SSOT mirror removed: no
- roadmap mirror removed: no
- queue-state refreshed or removed: deferred to the closure sweep
