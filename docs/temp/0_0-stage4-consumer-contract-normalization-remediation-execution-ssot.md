# 0_0 Stage4 Consumer-Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: partially_realized (aggregate Stage4 wave active; flashback, NpcDrift, fix-pack provenance, post-pass state owner-boundary, intake authority, and sink-alignment follow-up patches are now runtime-backed; 2026-04-03 fresh full run plus r2 Stage4-only sinkproof prove ep2 can PASS, the earlier metadata/sink hard-fail interpretation no longer fronts the queue, the 2026-04-06 revalidation kept the next bounded debt on numeric asset authority / carryover owner-boundary rather than replay-first residuals, and the 2026-04-07 bounded post-pass numeric carryover refresh patch landed with focused static validation while fresh canary/live proof remains explicitly deferred by operator)
Canonical Path: `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
- Baseline Dirty Summary: `dirty: active Stage4 docs/code/test deltas, prepared canary targets, temp roadmap/queue active`
- Resume Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Resume Drift Summary: `2026-04-07 bounded Stage4 consumer implementation landed in post-pass runtime: carryover refresh now accepts structured numeric truth from actual_truth plus director fallback, promotion metadata is persisted in state_truth_owner_contract, focused pytest/ruff/py_compile validation closed, and operator explicitly deferred fresh canary/live proof so the lane stays partial pending runtime measurement`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-post-select-continuity-seam-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-bounded-survey.md`
- `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-bounded-survey.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-bounded-survey.md`
- `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r4-audit.md`
- `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r5-audit.md`
- `docs/2026-04-03/0_0-stage4-ep2-continuity-handoff-context.md`
- `docs/2026-04-03/0_0-stage34-ep2-fresh-run-post-run-merge-audit.md`
- `docs/2026-04-03/0_0-stage4-ep2-sinkproof-r2-runtime-closure-audit.md`
- `docs/2026-04-03/0_0-stage4-numeric-asset-authority-carryover-bounded-survey.md`
- `docs/2026-04-06/rol-global-terminal4-stage4-pipeline-p0p1.md`
- `docs/2026-04-07/stage4-consumer-front-implementation-context.md`
- `docs/2026-04-07/stage234-handoff-harness-merge-audit.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-evidence.json`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-evidence.json`
- `docs/2026-04-02/0_0-stage4-post-select-continuity-seam-evidence.json`
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-evidence.json`
- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-evidence.json`
- `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-evidence.json`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-evidence.json`
- `docs/2026-04-03/0_0-stage34-ep2-fresh-run-post-run-merge-evidence.json`
- `docs/2026-04-03/0_0-stage4-ep2-sinkproof-r2-runtime-closure-evidence.json`
- `docs/2026-04-03/0_0-stage4-numeric-asset-authority-carryover-bounded-survey-evidence.json`
Side-Effect Coverage: covered
Parent Lane:
- `0_0-stage2-stage3-stage4-readiness-remediation`

## 1. Intent

Promote the latest Stage4 survey synthesis into one bounded execution wave that targets the remaining `consumer-side contract debt`, not another broad prompt or Stage2/3 redesign.

This execution SSOT exists because the current dominant Stage4 debt is now well-isolated:

- intake truth is hierarchy-aware but prose-flattened
- finalization loses bounded repair precision around `fix_pack` and `post_select_conflict`
- post-pass state persists three partially independent truth surfaces
- artifact drift cost now clusters around those consumer/finalization seams

This wave is not a global Stage4 redesign. It is an aggregate contract-normalization lane that sits above the already-landed narrower Stage4 substrate patches.

## 2. Baseline Facts

- `Stage4` is best described as `consumer/finalization split-truth-heavy`.
- `ep1` is consistently clean; `ep2+` is where carryover-dependent contradictions first become visible.
- The dominant runtime cost seams are:
  - `post_select_conflict + missing_fix_pack`
  - `strong_advisory_escalation_non_local_fix + missing_patch_targets`
- `fix_pack` truth is not single-origin: Director-authored and runtime-backfilled contracts coexist.
- `final_state_updates`, `actual_truth`, and `world_state` are persisted without a fully normalized owner boundary.
- Existing Stage4 lanes already landed useful substrate:
- `ep2 advisory escalation` improved Flashback FP and operator visibility
- `canonical entity postselect` improved post-pass pressure/state truth alignment
- `fixpack finalization` improved backfill/preservation
- `post-select continuity contract` improved contradiction subtype persistence
- the contaminated Stage4-only ep2 canary isolated a real `NpcDrift relation-tag` seam, and the later `r2` Stage4-only sinkproof run now provides positive runtime proof that this seam is no longer the immediate live blocker
- the fresh full run remains the higher-authority source for the original opening/replay warnings, but the later merged re-audit shows those warnings no longer front the queue
- the latest runtime picture is now split: `r5` is newest but API-limited, while `r4` remains the richest correction-path snapshot
- current Stage4 opening-authority surfaces are internally inconsistent: the global contract allows explicit transitions, but some writer-facing opening-anchor surfaces still read like unconditional same-location/time hard locks
- the correct fail-close rule is `undeclared replay/jump = reject`, not `location/time change itself = reject`
- the fresh full run in `projects/00_20260403` proves `ep2` can reach `PASS` through a bounded `PASS_WITH_FIX -> inplace patch -> PASS` path
- the `r2` Stage4-only sinkproof run proves Stage4 final authority now lands in `stage_attempts`, and current-session sink alignment no longer hard-fails
- the fresh full run and the `r2` Stage4-only sinkproof run both finish with clean final PASS rows, while the failed `r2` round-1 pathology is typed as `contradiction_type = 수치`
- archived and current artifact truth now show a split numeric ladder: arc-level `20억` band, blueprint/manuscript `200억`, and resumed ep1 FactLedger `1천만원`
- The remaining issue is no longer “Stage4 cannot pass or persist final authority.” It is “finish bounded numeric asset authority / carryover owner-boundary follow-up without prematurely reopening upstream hierarchy work.”
- 2026-04-06 Opus revalidation confirmed the remaining live P1 is a `baseline promotion gap`, not a false PASS or final-sink failure: legitimately changed numeric truth can still be re-flagged at the next-episode boundary when carryover baseline ownership is not explicitly promoted.

## 3. Scope

Included:

- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_immutable_fact_contract.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/domain/agents/chief_writer_context.py`
- focused Stage4 contract regressions, immutable-fact/opening-authority alignment, and queue/doc refresh

Excluded:

- Stage2 contract normalization
- Stage3 contract tightening
- broad Director prompt redesign
- global Stage4 resume declaration
- fresh canary in this document
- DB schema redesign
- artifact rewrites in `projects/`

## 4. Pass 1. Inventory Summary

Primary owner surfaces:

- intake authority / prose flattening:
  - `stage4_context_builder.py`
  - `chief_writer_context.py`
- fix-pack and verdict reclassification:
  - `stage4_interview_round.py`
  - `stage4_retry_runtime.py`
  - `stage4_reject_runtime.py`
- post-pass state persistence:
  - `stage4_post_processor.py`
  - `stage4_post_pass_runtime.py`

Primary debt inventory for this wave:

1. intake canonical truth arrives as prose rather than preserved machine-readable authority
2. bounded repair vs full rewrite is still too easy to flatten at finalization
3. fix-pack provenance and routing semantics are not normalized enough
4. `final_state_updates` / `actual_truth` / `world_state` owner boundary is underspecified
5. operator-visible truth, retry truth, and persisted truth can diverge by design without an explicit contract map
6. opening-authority wording across Stage4 intake surfaces is inconsistent about whether declared transitions are allowed

## 5. Pass 2. Semantic Classification

### Class A. Primary realization now

- numeric asset authority / carryover owner-boundary investigation
- post-select bounded-repair contract normalization
- fix-pack provenance and routing normalization
- post-pass state-truth owner boundary normalization

### Class B. Residual but related

- flashback continuity local-fix normalization
- NpcDrift relation-tag semantic/local-fix normalization
- operator-facing provenance exposure for synthesized vs authoritative repair contracts

### Class C. Explicitly deferred outside this lane

- Stage2/3 vocabulary normalization as a whole
- broad Stage4 prompt retuning
- canary closure itself
- architecture compression

## 6. Side-Effect Map

- file writes / artifacts:
  - future Stage4 retry/finalization artifacts may retain clearer subtype/fix-pack/state provenance

- DB / schema / transaction boundaries:
  - no schema changes in this lane
  - state log payload content may shift if owner boundaries are normalized

- JSONL / log / audit sinks:
  - `ui_events.jsonl`, `episode_production.jsonl`, and retry lineage may gain clearer provenance/contract fields or clearer reuse of existing ones

- console / UI / operator output:
  - operator-visible explanation of why a PASS became REJECT may become clearer
  - state-source ambiguity may become more explicit

- rollback / recovery / retry:
  - bounded local repair should trigger more reliably before rewrite-class collapse
  - retry churn should fall if fix-pack/state truth contracts stop flattening

- cache / global state:
  - post-pass state surfaces may become less contradictory, affecting later context assembly

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

This wave is an aggregate normalization layer that consumes existing Stage4 substrate work rather than replacing it.

Substrate already landed:

- `0_0-stage4-ep2-advisory-escalation-loop-remediation`
- `0_0-stage4-canonical-entity-postselect-remediation`
- `0_0-stage4-fixpack-finalization-remediation`
- `0_0-stage4-post-select-continuity-contract-normalization-remediation`
- `0_0-stage4-flashback-continuity-localfix-remediation`

This new execution SSOT should be read as:

- the umbrella contract-normalization wave that decides what remains to be tightened across those substrate lanes
- the direct prerequisite for moving the parent readiness lane beyond `blocked`

## 8. Execution Tranches

### Tranche 1. Post-Select Repair Contract Normalization

Goal:

- preserve bounded contradiction subtype and bounded repairability through the full `post_select_conflict -> reject guidance -> retry snapshot` path

Primary targets:

- `stage4_interview_round.py`
- `stage4_reject_runtime.py`
- `stage4_retry_runtime.py`

Acceptance shape:

- bounded `proper_noun / timeline / entity_ref / local_phrase` conflicts do not collapse into rewrite-only handling without carrying subtype/fixability context
- `authoritative_fix_scope` and derived runtime scope no longer feel like unrelated truths

### Tranche 2. Fix-Pack Provenance and Routing Normalization

Goal:

- clarify and normalize the distinction between Director-authored and runtime-synthesized fix-pack truth

Primary targets:

- `stage4_interview_round.py`
- `stage4_retry_runtime.py`
- focused operator-visible sinks

Acceptance shape:

- strong-advisory backfill remains bounded
- runtime-synthesized repair obligations are clearly distinguishable from Director-authored ones
- local-fixable advisories do not fail closed merely because provenance or patch-target packaging is coarse

Realization update (2026-04-02):

- `stage4_interview_round.py` now stamps `fix_pack.provenance` as one of `director_authored`, `runtime_backfilled`, or `runtime_synthesized`
- provenance survives `fix_pack` normalization, payload export, and operator-visible fix feedback text
- `stage4_retry_runtime.py` now treats bounded `runtime_backfilled` / `runtime_synthesized` local fix-packs as `patch_revision` candidates instead of silently treating them like Director-authored inplace orders
- `stage4_reject_runtime.py` now persists `fix_pack_origin` so retry evidence can distinguish `runtime_generated_prefers_patch` from `director_authored_allows_inplace`
- focused static validation is closed; runtime proof remains deferred
- touched hotspot note: `_normalize_director_gate_semantics` remains a pre-existing `220 LOC` legacy hotspot, but this tranche did not introduce a new `180+ LOC` function

### Tranche 3. Post-Pass State Owner Boundary Normalization

Goal:

- reduce split-truth across `final_state_updates`, `actual_truth`, and `world_state`

Primary targets:

- `stage4_post_processor.py`
- `stage4_post_pass_runtime.py`

Acceptance shape:

- owner boundaries are explicit by field family
- fallback from Manager truth to Director truth is visible rather than silent
- blueprint-derived overlays like `active_pressure_vectors` do not masquerade as Manager-owned truth without provenance

Realization update (2026-04-02):

- `stage4_post_pass_runtime.py` now builds and persists `state_truth_owner_contract` alongside `episode_bible.state_changes` and `state_log`
- the contract explicitly marks:
  - `actual_truth_surface` as `manager_actual_truth` or `director_state_updates_fallback`
  - `final_state_updates` as Director-owned
  - `inventory_counts` / `relationship_changes` as runtime storage overlays
  - `npc_martial_state_changes` as arc-state world-only storage
  - `active_pressure_vectors` as `runtime_blueprint_overlay` with `blueprint_filtered_by_manuscript` provenance
- focused static validation is closed; runtime proof remains deferred

### Tranche 4. Intake Authority Protection

Goal:

- preserve Stage2/3 work-identity authority as a tier-0 Stage4 intake packet instead of letting it collapse into budget-sensitive prose

Primary targets:

- `stage4_context_builder.py`
- `stage4_immutable_fact_contract.py`
- `chief_writer_context.py`

Acceptance shape:

- Stage4 work identity (`tracking_slots`, `mandatory_scene_engines`, registry cues, linked authority entities, active constraint spine) survives as an explicit tier-0 authority packet
- Chief Writer hard canon sees that packet before softer reference/context sections
- the authority packet remains bounded and does not expand Stage4 into a second Stage2/3 prose layer

Realization update (2026-04-02):

- `stage4_context_builder.py` now injects `[Stage4 Work Identity Authority]` into the tier-0 mandatory stack before the softer work-slot summary layer
- the packet carries bounded work-focus fields (`tracking_slots`, `mandatory_scene_engines`, `registry_profiles`) plus linked authority entities and active constraint spine
- `chief_writer_context.py` now re-surfaces that packet at the head of `writer_hard_canon_section` instead of leaving it buried inside generic `mandatory_context`
- focused static validation is closed; runtime proof remains deferred

Revalidation update (2026-04-03):

- the later merged runtime re-audit shows the opening-authority seam is no longer the front blocker for `ep2`
- the next bounded realization target under this intake-authority tranche is numeric carryover authority alignment across `stage4_context_builder.py`, `chief_writer_context_packets.py`, and the contradiction-firewall readback surfaces
- the implementation guardrail remains `declared transition contract`, not `same-location hard lock`; valid explicit transitions and POV-policy-compatible alternate openings remain allowed

Runtime closure update (2026-04-03, `r2` sinkproof canary):

- `canary_0_0_stage4_ep2_sinkproof_r2` reached `ep2` Stage4 `PASS` in round 2 with authoritative `stage_attempts` rows present for both reject/pass attempts
- `proof_scope_summary.scope_status = stage4_only` and `stage3_probe_origin = baseline_copy`, so this result is no longer blurred by Stage3 regeneration questions
- `hard_gates.status` is now `pass`; current-session sink alignment clears `final_sink_missing`, `lifecycle_sink_missing`, `final_score_mismatches`, and `artifact_metadata_missing`
- the later analyzer/readback backfill clears `gate_repair_metadata_missing`, and patch-trace non-exercise no longer counts as a closure-blocking hard-gate warning
- this demotes both the flashback and NpcDrift child seams from immediate live blockers to residual/substrate lanes under the aggregate consumer wave

Realization update (2026-04-05):

- `director_ensemble.py` now promotes `numeric_carryover_authority` firewall hits into a structured Stage4 contract instead of leaving them as typed contradiction text only
- the Director return payload now synthesizes `fix_pack`, `repair_contract`, and `scope_authority` with `target_kind=local_sentence`, `authoritative_fix_scope=partial`, and `provenance=runtime_synthesized` when carryover-baseline/current-asset authority splits are detected
- this keeps the active numeric owner-boundary seam in the existing Stage4 consumer lane while also feeding the already-landed reject/retry/session sink wiring with a richer contract shape
- targeted verification: `pytest tests/test_a4_failure_pattern.py -q`, `pytest tests/test_v75c_contradiction_firewall.py -q`, `pytest tests/test_stage4_interview_round.py -k "authoritative_fix_scope_metadata or numeric_carryover_operator_notes or stage4_db_attempt_payload" -q`, `ruff check`, `python -m py_compile`

Realization update (2026-04-07):

- `stage4_post_pass_runtime.py` now computes a bounded numeric carryover refresh plan that accepts asset-family structured numeric truth from `actual_truth` first and `final_state_updates` fallback, then reuses that plan for FactLedger carryover overlay plus `state_truth_owner_contract` promotion metadata
- `state_truth_owner_contract.numeric_carryover_authority` now records `promotion_rule`, `promoted_fields`, and `promotion_sources` when a carryover baseline refresh is emitted from structured post-pass truth
- focused verification closed: `pytest tests/test_stage4_post_processor.py::TestStateTruthOwnerContract::test_marks_promoted_numeric_carryover_refresh_sources tests/test_stage4_post_processor.py::TestAtomicMetadataSave::test_build_atomic_state_payloads_promotes_actual_truth_numeric_carryover_into_fact_ledger tests/test_stage4_post_processor.py::TestAtomicMetadataSave::test_build_atomic_state_payloads_promotes_string_and_director_fallback_numeric_carryover -q`, `pytest tests/test_stage4_post_processor.py -k "numeric_carryover_authority or carryover" -q`, `pytest tests/test_stage4_context_builder.py -k "numeric_carryover_authority or carryover" -q`, `pytest tests/test_a4_failure_pattern.py -q`, `pytest tests/test_v75c_contradiction_firewall.py -q`, `ruff check modules/core/stage4_post_pass_runtime.py tests/test_stage4_post_processor.py`, `python -m py_compile modules/core/stage4_post_pass_runtime.py tests/test_stage4_post_processor.py`
- operator explicitly deferred fresh canary/live proof, so this lane remains `partial`; treat the code landing as implementation progress, not runtime closure

## 9. Acceptance Criteria

- Stage4 bounded contradiction types preserve enough subtype detail to support local repair where appropriate
- fix-pack provenance is explicit enough that runtime-synthesized contracts are not indistinguishable from Director-authored contracts
- `final_state_updates`, `actual_truth`, and `world_state` have a clearer owner/provenance boundary for high-risk field families
- Stage4 opening-authority surfaces reject undeclared replay/jumps without treating declared transitions or POV-policy-compatible alternate openings as automatic drift
- new Stage4 behavior stays bounded and does not reopen Stage2/3 hierarchy work
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted Stage4 interview/finalization regressions
- targeted post-pass/state provenance regressions
- `pytest tests/test_stage4_context_builder.py -k "opening" -q`
- `pytest tests/test_chief_writer_context.py -k "opening" -q`
- `pytest tests/test_stage4_immutable_fact_contract.py -k "opening or carryover" -q`
- `python -m py_compile` on touched production modules
- `ruff check` on touched files
- targeted pytest shards only
- `python scripts/check_utf8_hygiene.py docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md docs/2026-04-01/active-temp-execution-roadmap.md docs/temp/execution-roadmap.md docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-parallel-master-order.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- keep `Stage4` paused
- do not widen this wave into broad Stage4 redesign
- do not reopen Stage2 or Stage3 implementation from this document
- do not run a canary from this document
- preserve Director final authority
- treat existing narrower Stage4 lanes as substrate, not as contradictory authorities
- do not encode the ep2 carryover local-fix into a global same-location or same-time hard lock

## 12. Temp Queue Notes

- temp status: `partial`
- cleanup condition:
  - keep the temp mirror as the new aggregate Stage4 contract-normalization lane until explicit realization or replacement
- roadmap dependency:
  - this lane becomes the new highest-level Stage4 contract wave
  - the immediate bounded follow-up is now `numeric asset authority / carryover owner-boundary` investigation inside the existing Stage4 consumer family
  - the flashback lane now sits below that as a completed runtime-positive substrate lane rather than the next front seam
  - the NpcDrift lane now sits below that as a runtime-positive substrate lane rather than an immediate live blocker
  - existing Stage4 partial lanes remain below it as substrate

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- promoted the new Stage4 survey into one bounded aggregate execution SSOT
- kept the scope on consumer/finalization contracts only

Pass 2, evidence and consistency:

- used the new Stage4 consumer-finalization survey as primary authority
- preserved lineage to the existing narrower Stage4 surveys and partial execution lanes
- did not overclaim runtime closure
- 2026-04-03 revalidation added the latest `r5` runtime audit and confirmed the active owner is still Stage4, not the parked Stage3 opening-transition lane
- 2026-04-03 closure update added the `r2` Stage4-only sinkproof audit, and the later analyzer/readback backfill plus hard-gate policy trim cleared the old metadata/sink seam; the subsequent numeric authority re-audit moved the next bounded seam to asset carryover/authority mismatch rather than replay/repetition, patch-trace non-exercise, or NPC false reject

Pass 3, execution and readability:

- made substrate relationships explicit
- separated bounded tranches by consumer contract family
- kept canary and resume actions out of scope
- clarified that the current bounded intake-authority subtask has moved from opening hard-lock debates to numeric carryover authority alignment without reopening the same-location lock question

Confidence: `96%`

## 15. 2026-04-06 Opus P0-P1 Revalidation: Numeric Carryover Promotion Gap

The 2026-04-06 global P0-P1 Opus survey did not change Stage4 queue order, but it did sharpen the active consumer-side seam into one bounded execution statement.

Queue semantics remain unchanged:

- status stays `partial`
- roadmap priority stays unchanged
- this remains the front Stage4 consumer lane above the repair-contract substrate lane

Confirmed live P1:

- `Stage4ContextBuilder` injects carryover baseline numeric authority into the writer prompt
- `stage4_post_pass_runtime` persists `state_truth_owner_contract` with `fact_ledger_carryover_baseline` ownership
- but the post-pass path still does not autonomously promote manuscript-proven numeric change into the next carryover baseline owner boundary
- the next episode therefore depends on contradiction-firewall / numeric-consistency readback to detect the split, which can create bounded false-positive retry pressure on a manuscript that actually changed the number on-page for valid plot reasons

Execution consequence:

- this lane remains the correct front owner for `numeric asset authority / carryover owner-boundary`
- the narrowest owner set stays:
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_post_pass_runtime.py`
  - writer/readback surfaces already cited under the intake-authority tranche
- the earlier metadata/readback hard-fail interpretation does not front the queue anymore; that concern now belongs below this lane

2026-04-06 bounded realization note:

- the recent `chief_writer_context_packets.py` carryover packet tightening improved writer-facing visibility by surfacing FactLedger baseline numeric authority even when previous manuscript/digest text is thin
- that patch narrows prompt ambiguity, but it does not by itself close the baseline-promotion seam described here

Revalidation note:

- static evidence is sufficient to keep this as a live P1 execution target
- fresh run is still useful for runtime impact measurement, but not required to prove the seam exists

## 16. 2026-04-09 Static Validity Recheck: Stale-Likely P1 Note

A current-HEAD static recheck against the landed code and focused tests no longer reproduces section 15 exactly as written.

Recheck anchors:

- `modules/core/stage4_context_builder.py` still injects the carryover baseline numeric authority packet into the writer prompt.
- `modules/core/stage4_post_pass_runtime.py` now builds `numeric_carryover_refresh_plan`, records promotion metadata in `state_truth_owner_contract`, and applies the numeric overlay into `fact_ledger_changes`.
- focused validation passed on current HEAD:
  - `pytest tests/test_stage4_post_processor.py::TestStateTruthOwnerContract::test_marks_promoted_numeric_carryover_refresh_sources tests/test_stage4_post_processor.py::TestAtomicMetadataSave::test_build_atomic_state_payloads_promotes_actual_truth_numeric_carryover_into_fact_ledger tests/test_stage4_post_processor.py::TestAtomicMetadataSave::test_build_atomic_state_payloads_promotes_string_and_director_fallback_numeric_carryover -q`
  - `pytest tests/test_stage4_context_builder.py -k "numeric_carryover_authority_packet" -q`

Current reading:

- the older statement that the post-pass path "still does not autonomously promote manuscript-proven numeric change into the next carryover baseline owner boundary" is now stale-likely under static review
- static review alone still cannot prove full demotion, because the operator-deferred fresh canary/live proof has not yet re-measured the next-episode boundary on current HEAD
- queue order therefore remains unchanged for now; treat this as `stale-likely / runtime-demotion-pending`, not as a fresh broad implementation reopen
- confidence after the 2026-04-06 re-audit remains `97%`

2026-04-07 implementation delta:

- the previous zero-promotion path is no longer the current code state for structured asset-family fields: post-pass now refreshes carryover baseline candidates from `actual_truth` first and `final_state_updates` fallback, and records promotion metadata in the owner contract
- operator explicitly deferred fresh canary/live proof, so this lane remains open for runtime measurement rather than broad new implementation inside the same topic
- if runtime proof continues to stay deferred, keep queue order unchanged and use fresh proof to decide whether `0_0-stage4-repair-contract-normalization-remediation` is still a true next code lane or whether the older consumer P1 framing should be demoted; do not reinterpret this as Stage4 consumer closure
