# 0_0 Stage4 Partial-Fix Hardening Remediation Execution SSOT

Date: 2026-04-07
Status: partially_realized (2026-04-07 merge-survey promotion clarified shared schema dependency, `partial_fix_eval`, and `repair_trace` / readback work inside this lane; the first bounded Stage4 tranche has now landed by anchoring `PatchTargetRecord` normalization, persisting structured `partial_fix_eval` / `repair_trace` payloads through Stage4 patch traces and `stage_attempts`, and widening analyzer + readback surfaces while explicit verifier canary/live proof remained deferred; a later 2026-04-08 fresh `000_ㅇㅇㅇ` Stage4 `ep1` post-run merge audit then exposed PASS-side `episode_production` / session sink finalization drift, a bounded `stage4_interview_round.py` logging follow-up landed, the subsequent `canary_000_ㅇㅇㅇ_stage4_ep1_sinkproof_r1` Stage4-only rerun proved current-session Stage4 sink alignment clean, a later bounded proof-operational metadata tranche then landed across Stage4 control-plane/session scope, post-pass contract signals, and `runtime_audit_summary.json` synthesis without creating a new queue topic or making `proof_intent` mandatory, and the latest same-day bounded implementation tranche now lands companion-sink advisory sync, `PassRateMonitor` compatibility, and numeric-consistency proof surfacing while a fresh rerun remains pending)
Canonical Path: `docs/2026-04-07/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-partial-fix-hardening-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: 139 tracked, 106 untracked; hotspots: docs/, treatments/, material_ssot/, modules/, tests/`
- Resume Commit: `6dd7712ea9a58802221634081ba199bc872d2349`
- Resume Drift Summary: `the bounded Stage4 partial-fix tranche remains landed, the 2026-04-08 fresh `000_ㅇㅇㅇ` audit exposed PASS-side sink drift, the bounded `stage4_interview_round.py` logging follow-up landed, the later `canary_000_ㅇㅇㅇ_stage4_ep1_sinkproof_r1` Stage4-only rerun now proves current-session Stage4 sink alignment / authority / rationale surfaces clean, a later same-day proof-operational metadata follow-up landed across `stage4_orchestrator.py`, `stage4_post_pass_runtime.py`, and `audit_service.py` so real fresh runs now emit session-scoped Stage4 proof metadata without requiring mandatory `proof_intent`, and the newest bounded proof-channel tranche now lands `director_selections` companion advisory sync, `PassRateMonitor` compatibility with live Stage4 attempt payloads, and analyzer/canary numeric-consistency surfacing while the dedicated verifier tranche and fresh rerun remain pending inside this same lane`
Source Survey Docs:
- `docs/2026-04-07/stage4-data-shape-pwf-bounded-survey.md`
- `docs/2026-04-07/stage-parallel-container-and-pwf-master-survey.md`
- `docs/2026-04-07/partial-fix-terminal1-eval-harness-survey.md`
- `docs/2026-04-07/partial-fix-terminal2-shared-patch-address-schema-survey.md`
- `docs/2026-04-07/partial-fix-terminal3-operator-before-after-trace-survey.md`
- `docs/2026-04-07/partial-fix-hardening-parallel-merge-survey.md`
- `docs/2026-04-08/000-fresh-run-stage4-ep1-post-run-merge-audit.md`
- `docs/2026-04-08/0_0-stage4-ep1-sinkproof-r1-runtime-closure-audit.md`
- `docs/2026-04-08/stage4-proof-operational-metadata-bounded-survey.md`
- `docs/2026-04-08/stage4-ep2-interrupted-run-evidence-harvest-bounded-survey.md`
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
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/services/audit_service.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_inplace_local_ops.py`
- `modules/core/failure_analyzer.py`
- `modules/core/db_manager.py`
- `modules/api/bridge_server.py`
- `modules/core/stage4_canary_tools.py`
- bounded Stage4 local repair selection and post-patch verification surfaces
- bounded fix-pack address precision, `partial_fix_eval`, and patch-trace fidelity improvements
- bounded Stage4 proof-operational metadata and runtime-summary synthesis for later fresh-run proof reuse
- bounded current-session companion sink truth plus numeric-consistency proof surfacing for interrupted/live retry runs

Excluded:

- broad Stage4 repair-contract grammar redesign
- current front-owner Stage4 consumer or repair implementation work
- broad Stage4 owner-surface refactor
- new queue rank creation
- new DB table or column creation
- mandatory operator-supplied `proof_intent`
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

## 8B. Fresh Run Audit Update (2026-04-08)

- fresh `projects/000_ㅇㅇㅇ` evidence now proves Stage4 `ep1` persistence success:
  - `stage_attempts` final row is `PASS`
  - `drafts/ep_0001.txt` and DB `manuscripts` stay aligned
  - the final artifact path is `logs/artifacts/stage4/ep_0001/attempt_01/patched_after_fix__A_InPlace.txt`
- the same completed run still leaves `runtime_audit_summary.json` at `proof_digest.status = warn` because PASS-side sinks disagree on final patched truth:
  - `episode_production.jsonl` retained pre-fix `PASS_WITH_FIX` / `director_primary_pass_with_fix` metadata
  - `logs/session/decisions.jsonl` carried the final rationale but dropped the bounded `fix_pack`
  - `director_selections` remained the expected pre-final companion rather than the final authority row
- bounded follow-up landed in `stage4_interview_round.py`:
  - pass-side logging now merges non-empty trace fields onto the original `director_result` so partial traces cannot erase `fix_pack`
  - `episode_production` and session logging now receive explicit final `selection_reason`, `verdict_reason`, `gate_semantics`, `fix_pack`, `runtime_advisory`, and `retry_directives`
- queue consequence:
  - keep this lane `partially_realized`
  - do not claim closure until a fresh rerun re-proves the patched pass-side sink alignment

## 8C. Stage4-only Sinkproof Update (2026-04-08)

- `projects/_canary/canary_000_ㅇㅇㅇ_stage4_ep1_sinkproof_r1` now provides the bounded rerun proof requested by the fresh `000_ㅇㅇㅇ` audit:
  - `proof_scope_summary.scope_status = stage4_only`
  - `proof_scope_summary.stage4_sink_alignment_status = ok`
  - `sink_alignment_summary.status = ok`
  - `current_session_sink_alignment_summary.status = ok`
- final-authority and rationale surfaces are also clean on the rerun:
  - `final_authority_contract_summary.status = ok`
  - `rationale_contract_summary.status = ok`
  - `companion_audit_summary.status = ok`
  - `gate_repair_surface_summary.status = ok`
- the remaining warns are bounded and out of scope for the original Stage4 sink-alignment question:
  - top-level `proof_digest.status = warn` remains because Stage3 probe data is copied baseline carryover from the source project
  - `hard_gates.warnings = ["stage4_retry_contract_not_exercised"]` because `ep1` passed in round 1, so the retry path was not exercised
- queue consequence:
  - keep this lane `partially_realized`
  - treat the rerun-pending PASS-side sink-alignment blocker as runtime-closed and positive
  - leave the dedicated verifier hardening and broader local-vs-structural policy tightening for the next tranche inside this same lane

## 8D. Proof Operational Metadata Update (2026-04-08)

- operator follow-up clarified that real fresh runs should gain better proof reuse metadata, but should not require mandatory `proof_intent`
- bounded follow-up landed inside this same lane:
  - `stage4_orchestrator.py` now emits `stage4_session_scope` at Stage4 session start and tags `target_ep_reached` plus `stage4_complete` with `session_id`
  - `stage4_post_pass_runtime.py` now tags `STAGE4_POST_PASS_CONTRACT` and the mirrored `stage4_post_pass_contract_signal` with the current `session_id`
  - `audit_service.py` now extends `runtime_audit_summary.json -> proof_digest.operational_metadata` with:
    - `latest_session_id`
    - `stage3_live_session`
    - `stage4_live_session`
    - `retry_exercised`
    - `patch_exercised`
    - `post_pass_contract_signal_count`
    - `session_scope`
    - `non_exercised_reasons`
- guardrails kept:
  - no new DB schema
  - no canary harness changes
  - no mandatory `proof_intent`
  - no new queue topic
- targeted verification closed:
  - `pytest tests/test_audit_service.py -k "operational_metadata or proof_digest or committed_snapshot_only" -q`
  - `pytest tests/test_stage4_orchestrator.py -k "target_ep_reached or session_scope" -q`
  - `pytest tests/test_stage4_post_processor.py -k "post_pass_contract_signal" -q`
  - `ruff check modules/core/services/audit_service.py modules/core/stage4_orchestrator.py modules/core/stage4_post_pass_runtime.py tests/test_audit_service.py tests/test_stage4_orchestrator.py tests/test_stage4_post_processor.py`
  - `python -m py_compile modules/core/services/audit_service.py modules/core/stage4_orchestrator.py modules/core/stage4_post_pass_runtime.py`
- queue consequence:
  - keep this lane `partially_realized`
  - treat this as proof-aware observability support for later fresh-run closure reuse, not as verifier closure by itself

## 8E. Interrupted EP2 Evidence Harvest Update (2026-04-08)

- interrupted `projects/_canary/canary_000_ㅇㅇㅇ_stage4_ep2_numauth_r1` analyze is not closure proof, but it did capture new same-session Stage4 evidence:
  - `current_session_sink_alignment_summary.status = warn`
  - `scope_authority_fix_scope_mismatches = 2`
  - `scope_authority_widened_mismatches = 1`
  - `gate_repair_metadata_missing = 2`
- mismatch shape is bounded and specific:
  - `stage_attempts` plus `episode_production` agree on widened runtime scope
  - `director_selections` companion rows lag behind on widened `fix_scope` / `widened` / repair metadata
  - therefore the immediate same-lane patch target is companion sink truth, not broad Stage4 owner reassignment
- the same run also surfaced a proof-channel observability regression:
  - `pass_rate_monitor_cache_missing` is accompanied by repeated session-log failures: `PassRateMonitor.record_attempt() got an unexpected keyword argument 'fix_scope'`
  - treat this as bounded Stage4 proof-channel compatibility debt inside the same lane
- numauth evidence split is now explicit:
  - semantic ownership of `numeric asset authority / carryover owner-boundary` remains with `0_0-stage4-consumer-contract-normalization-remediation`
  - but the current proof channel still leaves repeated `numeric_carryover_authority` signals in run logs without one official analyze summary field, so surfacing that evidence belongs here as bounded proof-channel hardening
- upstream evidence was also harvested, but does not change immediate order:
  - flashback/location/inventory drift signals are strong enough to justify a later Stage2/Stage3 observability tranche
  - however that proof wave should still follow the Stage4 proof-channel fixes above, not precede them
- queue consequence:
  - keep this lane `partially_realized`
  - treat the next bounded implementation tranche as:
    - companion sink scope-authority synchronization
    - `PassRateMonitor` compatibility
    - numeric-consistency proof surfacing
  - do not reopen Stage2/Stage3 ahead of these Stage4 proof-channel fixes

## 8F. Proof-Channel Implementation Update (2026-04-08)

- the bounded proof-channel tranche identified in `8E` is now code-landed without opening a new queue topic:
  - `modules/core/db_manager.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_reject_runtime.py`
  - `modules/core/pass_rate_monitor.py`
  - `modules/core/failure_analyzer.py`
  - `modules/core/services/audit_service.py`
  - `modules/core/stage4_canary_tools.py`
- landed behavior:
  - final Stage4 rationale sync now also merges final advisory payloads into `director_selections.advisory_warnings`, so same-session companion rows can follow widened runtime `scope_authority` / repair metadata instead of freezing the initial selection-time view
  - `PassRateMonitor.record_attempt()` now accepts and persists current Stage4 gate/authority payload fields instead of dropping the row with `unexpected keyword argument 'fix_scope'`
  - analyzer / proof outputs now expose `numeric_consistency_summary` from persisted Stage4 `runtime_advisory` / `retry_directives` text, so interrupted/live numauth evidence is no longer log-only
- bounded validation landed before any fresh rerun:
  - targeted pytest shards for `db_manager`, `stage4_interview_round`, `pass_rate_monitor`, `failure_analyzer`, `audit_service`, and `stage4_canary_tools`
  - `ruff check` on touched code/tests
  - `python -m py_compile` on touched code/tests
  - `python scripts/check_utf8_hygiene.py` on touched code/tests
  - `python scripts/ops_validator.py --strict`
- existing interrupted canary re-analyze now confirms the new proof surface without opening a fresh run:
  - `projects/_canary/canary_000_ㅇㅇㅇ_stage4_ep2_numauth_r1/logs/canary_summary.json` now includes `numeric_consistency_summary.status = warn`
  - the same summary still shows the captured current-session companion drift buckets, so the lane is now implementation-landed but not closure-ready
- queue consequence:
  - keep this lane `partially_realized`
  - treat the next runtime action as a fresh rerun to validate:
    - companion sink alignment after the advisory-sync patch
    - `PassRateMonitor` cache persistence on a live retry session
    - Stage4 numeric-consistency surfacing on a fresh proof run rather than interrupted evidence only

## 9. Acceptance Criteria

- Stage4 can express one stable partial-fix address family across both local-op and structural patch flows
- `patch_targets` can be expressed as structured records while preserving current summary text
- `must_fix`, `do_not_regress`, and `success_condition` influence actual post-patch gating, not only prompt text
- exact local edits are preferred when truly local and mechanically verifiable
- structural patch remains bounded to target scenes when local edit is insufficient
- Stage4 persists bounded `partial_fix_eval` outcomes and exposes aggregate rates without inventing a new queue lane
- Stage4 exposes bounded `repair_trace[]` entries to operator readback with `target`, `old_excerpt`, `new_excerpt`, `why_changed`, and truthful `guard_result`
- `runtime_audit_summary.json` exposes latest-session proof-operational metadata for Stage4 fresh runs without requiring operator-supplied `proof_intent`
- current-session companion sinks do not drift on widened `scope_authority` / repair metadata relative to `stage_attempts` plus `episode_production`
- Stage4 proof summaries surface bounded numeric-consistency authority evidence instead of leaving it log-only
- Stage4 proof runs retain `PassRateMonitor` evidence without non-blocking argument-signature failure
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
- targeted audit/control-plane regression checks for Stage4 session scope and proof-operational metadata
- targeted regression checks for same-session companion sink scope-authority serialization and `PassRateMonitor` compatibility
- targeted analyzer/proof-summary checks for numeric-consistency evidence surfacing
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
- folded the later interrupted `ep2` evidence harvest into the same lane without reopening queue ownership or misclassifying the numeric seam as upstream-first

Pass 3, execution and readability:

- made the implementation sequence explicit: shared schema -> address -> selection -> verifier/sink -> repair trace -> aggregator
- extended the same lane with a bounded proof-operational metadata tranche instead of inventing a new queue topic
- made the post-harvest next tranche explicit: companion sink truth -> monitor compatibility -> numeric surfacing
- recorded that bounded implementation has now landed and moved the lane to fresh-rerun-pending rather than leaving the proof-channel tranche only as a survey recommendation
- kept activation order subordinate to the current proof-deferred Stage4 front queue

Confidence: `97%`
