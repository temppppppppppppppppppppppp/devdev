# 0_0 Stage4 Partial-Fix Hardening Remediation Execution SSOT

Date: 2026-04-07
Status: partially_realized (2026-04-07 merge-survey promotion clarified shared schema dependency, `partial_fix_eval`, and `repair_trace` / readback work inside this lane; the first bounded Stage4 tranche has now landed by anchoring `PatchTargetRecord` normalization, persisting structured `partial_fix_eval` / `repair_trace` payloads through Stage4 patch traces and `stage_attempts`, and widening analyzer + readback surfaces while explicit verifier canary/live proof remains deferred)
Canonical Path: `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 139 tracked, 106 untracked; hotspots: docs/, treatments/, material_ssot/, modules/, tests/`
- Resume Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
- Resume Drift Summary: `2026-04-07 bounded Stage4 partial-fix tranche landed across `partial_fix_contract.py`, `chief_writer.py`, `chief_writer_inplace_local_ops.py`, `stage4_retry_runtime.py`, `stage4_interview_round.py`, `stage4_reject_runtime.py`, `failure_analyzer.py`, `db_manager.py`, and `bridge_server.py`: Stage4 now normalizes structured `PatchTargetRecord` payloads while preserving summary-compatible `patch_targets`, local/structural patch traces keep bounded `repair_trace` evidence, `partial_fix_eval` is persisted into patch traces and `stage_attempts`, and DB/dashboard/canary readback now exposes the new sink shape with focused regression/static validation closed`
Source Survey Docs:
- `docs/2026-04-07/stage4-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage-parallel-container-and-pwf-master-survey.md`
- `docs/2026-04-07/partial-fix-terminal1-eval-harness-survey.md`
- `docs/2026-04-07/partial-fix-terminal2-shared-patch-address-schema-survey.md`
- `docs/2026-04-07/partial-fix-terminal3-operator-before-after-trace-survey.md`
- `docs/2026-04-07/partial-fix-hardening-parallel-merge-survey.md`
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-04-07/stage-parallel-data-shape-pwf-evidence.json`
Side-Effect Coverage: covered
Parent Lane:
- `0_0-stage4-repair-contract-normalization-remediation`

## 1. Intent

Create a bounded pending-lane execution SSOT for improving Stage4 partial-fix precision without reopening broad Stage4 redesign or fix-pack grammar redesign.

This promotion incorporates the 2026-04-07 merge-survey verdict: no new queue rank is needed, but this lane must explicitly own the Stage4 anchor work for:

- the shared `PatchTargetRecord` dependency consumed later by Stage3 and Stage2
- the Stage4-side `partial_fix_eval` sink and aggregator extension
- the Stage4-local operator `repair_trace[]` contract plus bridge/readback widening

This lane exists because Stage4 already has the repo's best partial-fix substrate:

- `fix_scope=inplace` gate discipline
- structured `fix_pack`
- scene-targeted structural patch
- exact local replace ops with anchors

But the current substrate is still uneven:

- `do_not_regress` and `success_condition` are carried as contract text but not treated as first-class post-patch gates
- local-edit, structural-patch, and broader-rewrite selection remain split across multiple heuristics
- stable patch addressing is stronger than Stage2/3 but still not normalized into one reusable repair contract family

## 2. Baseline Facts

- Stage4 `PASS_WITH_FIX` already enforces `fix_scope=inplace` plus a ready `fix_pack` before local repair is allowed.
- `fix_pack` currently requires:
  - `patch_targets`
  - `must_fix`
  - `do_not_regress`
  - `success_condition`
  - `target_kind`
- Structural patch mode edits only selected scene blocks and expects `patched_blocks` keyed by `scene_id`.
- Local-edit mode already supports exact replace operations with:
  - `old_text`
  - `new_text`
  - `anchor_before`
  - `anchor_after`
- Current live code normalizes and displays `do_not_regress` and `success_condition`, but does not independently verify them as a dedicated post-patch gate.
- `stage_attempts` already persists `is_patch`, `is_patch_fallback`, `patch_strategy`, `fix_scope`, and `advisory_flags.fix_pack` for Stage4 attempts.
- `failure_analyzer.patch_trace_summary` already aggregates Stage4 patch-trace evidence and already feeds `stage4_canary_tools`.
- bridge/db readback already exposes `fix_pack` and repair-contract metadata, but does not expose before/after excerpts or per-target `guard_result`.

## 3. Scope

Included:

- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_inplace_local_ops.py`
- `modules/core/failure_analyzer.py`
- `modules/core/db_manager.py`
- `modules/api/bridge_server.py`
- `modules/core/stage4_canary_tools.py`
- bounded Stage4 local repair selection and post-patch verification surfaces
- bounded fix-pack address precision, `partial_fix_eval`, and patch-trace fidelity improvements

Excluded:

- broad Stage4 repair-contract grammar redesign
- current front-owner Stage4 consumer or repair implementation work
- broad Stage4 owner-surface refactor
- new queue rank creation
- new DB table or column creation
- Stage2 or Stage3 redesign inside this lane
- fresh canary execution in this documentation turn

## 4. Pass 1. Inventory Summary

Primary Stage4 partial-fix surfaces:

1. `stage4_interview_round.py`
   - fix-pack normalization
   - PASS_WITH_FIX eligibility
   - repair contract payload export
2. `chief_writer.py`
   - structural patch planning
   - target-scene patch merge
3. `chief_writer_inplace_local_ops.py`
   - exact local replace operations with text anchors

Primary debt inventory for this wave:

1. fix-pack success and regression guards are mostly textual, not executable
2. local-edit vs structural-patch routing is capable but not unified into one explicit decision model
3. stable address precision exists at the local-op layer but not as one normalized Stage4-wide patch-address contract
4. post-patch acceptance is still too dependent on full re-audit rather than a small targeted verifier layer
5. operator-facing before/after evidence is dropped before persistence and readback
6. patch telemetry exists, but `partial_fix_eval` still lacks one explicit sink shape and one explicit aggregator extension

## 5. Pass 2. Semantic Classification

### Class A. Primary realization when this lane is activated

- shared `PatchTargetRecord` dependency plus Stage4-side schema authority
- executable post-patch guard for `must_fix` / `do_not_regress` / `success_condition`
- normalized patch-address contract across local-edit and structural patch modes
- bounded `repair_trace[]` persistence/readback contract
- bounded `partial_fix_eval` sink and aggregator extension
- explicit selection policy:
  - exact local edit first
  - scene-targeted structural patch second
  - non-local rewrite or reject last

### Class B. Residual but related

- richer patch telemetry for operator comparison
- better stale target detection when scene/block anchors drift
- stronger patch exhaustion heuristics for repeated non-improving attempts

### Class C. Explicitly deferred outside this lane

- broad fix-pack redesign
- Stage4 repair grammar rename sweep
- Stage4 global retry architecture rewrite
- Stage4 owner-surface/module split

## 6. Side-Effect Map

- file writes / artifacts:
  - future Stage4 retry traces and attempt artifacts may carry richer patch-target, `repair_trace`, and post-check metadata

- DB / schema / transaction boundaries:
  - existing `stage_attempts.advisory_flags` JSON may gain bounded `partial_fix_eval` and `repair_trace` sub-objects; no new table/column is allowed in this lane

- JSONL / log / audit sinks:
  - `episode_production.patch_trace`, fix-pack summaries, and post-check results may become richer and more target-specific

- console / UI / operator output:
  - bridge `gate_repair_summary` and canary summaries may expose before/after trace plus `partial_fix_eval` rates

- rollback / recovery / retry:
  - patch retries should become shorter and more selective when local checks fail early and same-target failure is explicit

- cache / global state:
  - not primary in this lane

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

### Tranche 0. Shared PatchTargetRecord Dependency

Goal:

- pin one shared target-record contract that Stage4 anchors first and Stage3/2 consume later without creating a new queue rank

Realization direction:

- treat each `patch_targets` entry as a bounded record, not only `list[str]`
- pin shared meanings for:
  - `stage`
  - `container_kind`
  - `container_id`
  - `target_kind`
  - `scene_id`
  - `field_path`
  - `text_anchor`
  - `summary`
- keep Stage4 as the schema authority anchor while forbidding Stage4-local text-anchor rules from becoming fake Stage2/3 obligations

### Tranche 1. Patch-Address Normalization

Goal:

- unify Stage4 partial-fix targets into a stable contract that can drive both local-op and structural patch modes

Realization direction:

- define a bounded address family for:
  - `scene_id`
  - `target_kind`
  - optional local anchors
- migrate `patch_targets` toward structured target records while preserving `summary` compatibility with current human-readable strings
- keep local-op `old_text` / `anchor_before` / `anchor_after` compatible as the Stage4 `text_anchor` form

### Tranche 2. Tiered Repair Selection

Goal:

- stop choosing between local edit and structural patch through fragmented heuristics only

Realization direction:

- prefer exact local edit when `target_kind` is truly local and anchors are reliable
- prefer scene-targeted structural patch when locality is block-level rather than substring-level
- fail upward to broader rewrite or reject only when bounded local contracts are not credible

### Tranche 3. Post-Patch Targeted Verifier and Eval Sink

Goal:

- make `must_fix`, `do_not_regress`, and `success_condition` executable rather than display-only and persist their outcomes in one bounded sink

Realization direction:

- run a bounded post-patch verifier before full re-audit
- verify:
  - targeted issue disappearance
  - explicit no-regression guard preservation
  - minimum patch realism / locality conditions
- write one bounded `advisory_flags.partial_fix_eval` object containing:
  - `patch_round`
  - `is_patch_attempt`
  - `patch_target_id`
  - `target_kind`
  - `must_fix_resolved`
  - `do_not_regress_held`
  - `success_condition_met`
  - `fallback_reason`
- keep Python on fact collection only; the verifier booleans come from the LLM-side verifier, then persistence stores them

### Tranche 4. Repair Trace and Readback Hardening

Goal:

- preserve operator-facing before/after evidence without inventing a new Stage4 lane

Realization direction:

- extend patch traces with bounded `repair_trace[]` entries carrying:
  - `target`
  - `target_kind`
  - `old_excerpt`
  - `new_excerpt`
  - `why_changed`
  - `guard_result`
- capture local-edit operations instead of dropping them after application
- capture structural pre/post block excerpts before merge assignment
- surface `repair_trace` through DB snapshot/readback and bridge `gate_repair_summary`

### Tranche 5. Partial-Fix Eval Aggregator and Exhaustion Hardening

Goal:

- reduce futile PWF loops and make Stage4 patch quality measurable

Realization direction:

- extend `failure_analyzer.patch_trace_summary` with a bounded `partial_fix_eval` block carrying:
  - `local_hit_rate`
  - `fallback_to_partial_or_full`
  - `same_target_retry_avg`
  - `same_target_retry_p95`
  - `do_not_regress_violation_rate`
  - `verifier_coverage`
- harden repeated-attempt escalation based on structured `patch_target_id`
- preserve target-level outcome summaries in patch traces and canary/readback surfaces

## 8. Execution Tranches

1. shared `PatchTargetRecord` dependency anchored in Stage4
2. Stage4 patch-address normalization
3. Stage4 local-edit vs structural-patch tiering
4. Stage4 targeted post-patch verifier plus `partial_fix_eval` sink
5. Stage4 `repair_trace[]` persistence/readback widening
6. Stage4 `partial_fix_eval` aggregator and exhaustion hardening
7. bounded regression coverage
8. later canary/live proof only after explicit reactivation

## 8A. Implementation Update (2026-04-07)

- Tranche 0 and Tranche 1 landed in bounded Stage4-anchor form:
  - new `modules/core/partial_fix_contract.py` owns shared `PatchTargetRecord` normalization for Stage4 and preserves summary-compatible `patch_targets`
  - `stage4_interview_round.py` and `chief_writer.py` now carry structured target records without breaking the current string contract surfaces
- Tranche 4 landed in bounded persistence/readback form:
  - local-op and structural patch paths now retain bounded `repair_trace[]` entries with target identity plus before/after excerpts
  - `stage_attempts` gate snapshots, bridge `gate_repair_summary`, and Stage4 canary summaries now expose `repair_trace` and `partial_fix_eval`
- Tranche 5 landed in bounded aggregation form:
  - `failure_analyzer.patch_trace_summary()` now emits a `partial_fix_eval` aggregate block keyed off the persisted Stage4 patch-trace sink
- explicit Tranche 3 verifier work remains deferred:
  - the new sink shape is live, but `must_fix_resolved` / `do_not_regress_held` / `success_condition_met` still wait on a later dedicated verifier tranche rather than a broad prompt redesign in this turn

## 9. Acceptance Criteria

- Stage4 can express one stable partial-fix address family across both local-op and structural patch flows
- `patch_targets` can be expressed as structured records while preserving current summary text
- `must_fix`, `do_not_regress`, and `success_condition` influence actual post-patch gating, not only prompt text
- exact local edits are preferred when truly local and mechanically verifiable
- structural patch remains bounded to target scenes when local edit is insufficient
- Stage4 persists bounded `partial_fix_eval` outcomes and exposes aggregate rates without inventing a new queue lane
- Stage4 exposes bounded `repair_trace[]` entries to operator readback with `target`, `old_excerpt`, `new_excerpt`, `why_changed`, and truthful `guard_result`
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted Stage4 interview-round regressions
- targeted chief-writer local-op regressions
- targeted structural patch regressions
- targeted `failure_analyzer.patch_trace_summary` regression checks
- targeted DB snapshot / bridge readback regressions for `repair_trace` and `partial_fix_eval`
- `python -m py_compile` on touched production modules
- `ruff check` on touched files
- targeted pytest shards only
- `python scripts/check_utf8_hygiene.py` on touched docs/code
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not activate this lane ahead of the current Stage4 consumer/repair front without explicit reprioritization
- do not widen this lane into broad fix-pack redesign
- do not widen this lane into owner-surface refactor
- do not widen this lane into Stage2/3 redesign from inside Stage4
- do not fabricate a fake cross-stage before/after trace requirement for Stage2/3 from inside this lane
- do not run canary/live proof from this lane until explicit operator approval

## 12. Temp Queue Notes

- temp status: `in_progress`
- cleanup condition:
  - keep the temp mirror as a promoted pending queue item until explicit closure, replacement, or merge into a later active Stage4 wave
- roadmap dependency:
  - this item stays below the current Stage4 consumer/repair front and below the non-wuxia Stage4 tranche, but above soak-only references

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this as a bounded pending execution SSOT rather than a front-active Stage4 lane
- limited scope to partial-fix hardening, not broad Stage4 redesign
- absorbed the merge-survey result by expanding this lane rather than inventing a new queue rank

Pass 2, evidence and consistency:

- anchored claims to live Stage4 fix-pack, structural patch, and local-op code paths
- kept the document separate from existing repair-contract grammar work
- aligned the execution scope with the 2026-04-07 eval-harness, shared-schema, and operator-trace survey conclusions

Pass 3, execution and readability:

- made the implementation sequence explicit: shared schema -> address -> selection -> verifier/sink -> repair trace -> aggregator
- kept activation order subordinate to the current proof-deferred Stage4 front queue

Confidence: `97%`
