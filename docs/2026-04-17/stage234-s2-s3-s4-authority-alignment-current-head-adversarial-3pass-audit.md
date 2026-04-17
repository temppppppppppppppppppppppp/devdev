# Stage234 S2-S3-S4 Authority Alignment Current-Head Adversarial 3-Pass Audit

Date: 2026-04-17
Status: final (3-pass audited; bounded current-head re-audit after the post-merge proof/frontier follow-up commits landed)
Canonical Path: `docs/2026-04-17/stage234-s2-s3-s4-authority-alignment-current-head-adversarial-3pass-audit.md`
Commit State:
- Baseline Commit: `ce0f3b47b465fcd67796f75e0497a5f7c7b2424f`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-16/stage234-s2-s3-s4-authority-alignment-post-merge-current-head-adversarial-3pass-audit.md`
- `docs/2026-04-14/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
- `docs/temp/execution-roadmap.md`
- `docs/2026-04-16/stage234-global-authority-alignment-post-r12-stage4-current-session-closure-current-head-3pass-audit.md`
Evidence Artifacts:
- `modules/core/stage2_finalizer.py`
- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage3_blueprint_state_precision_guardrail.py`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_chief_writer_context.py`
- `tests/test_stage4_interview_round.py`
Side-Effect Coverage: covered (Stage2 end-state promotion into shared transport, Stage3 opening/time/fact-lock precedence, Stage4 numeric owner vs transport lineage, writer-context hard-canon ordering, Stage4 current-session raw/selection sink parity, governing-doc current-head anchor drift)
Confidence: `96%`

## 1. Intent

Re-audit one bounded question on the live current head:

- did the later `ce0f3b47` / `e0ffc8df` follow-up reopen or silently drift the `S2 -> S3 -> S4` authority-alignment lane?

This audit is intentionally narrower than a new runtime proof run.

It does not:

- authorize fresh Stage3 or Stage34 runtime
- reopen `Stage234` implementation
- replace the active roadmap or execution SSOT

## 2. Adversarial Findings

### Finding 1. The existing governing docs are stale as literal current-head anchors again

Severity: medium

The last canonical current-head authority audit is still anchored at `eb5460ac`, and the active authority execution SSOT still resumes from `eb5460ac`, while the active roadmap mirror still resumes from `6325ad42`:

- `docs/2026-04-16/stage234-s2-s3-s4-authority-alignment-post-merge-current-head-adversarial-3pass-audit.md`
- `docs/2026-04-14/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
- `docs/temp/execution-roadmap.md`

Current `HEAD` is now `ce0f3b47`, and there are real post-audit code deltas on authority-lane files:

- `modules/core/stage2_finalizer.py`
- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`

Adversarial consequence:

- the older docs remain valid provenance
- they should not be read as the only literal current-head governance anchor until a new current-head audit exists

This document is that new anchor.

### Finding 2. The live code changes tighten upstream authority semantics instead of reopening owner drift

Severity: low

The current-head deltas are bounded and authority-preserving:

- `Stage2Finalizer` now promotes the last tactical end-state into structured `arc_end_state` only when the structured fields are still placeholder/unknown, while still preserving explicit authoritative empty inventory clears such as `[]` instead of overwriting them with tactical prose
- `EpisodeStateArbiter` now treats `arc_data.state_changes.timeline` as the preferred time authority on true arc openings and emits an explicit `opening_transition_expectation` when the new opening anchor intentionally differs from the previous episode ending
- `BlueprintConstraintCompiler` now suppresses stale previous-opening fact-lock anchors when authoritative arc-opening location or timeline truth already exists upstream for that arc opening

Adversarial read:

- this is not a hidden promotion of packet transport into a new owner
- this is a bounded Stage2/Stage3 alignment follow-up that reduces stale-anchor pressure at true arc openings

### Finding 3. No downstream Stage4 owner inversion was found

Severity: none

The downstream split remains intact on the current head:

- Stage4 still treats cross-stage packet rows as transport/bootstrap lineage
- FactLedger carryover baseline remains the stronger owner when available
- current-session sink parity for historical companion and patch-trace/raw evidence remains green on the focused shard

Adversarial consequence:

- no hidden `Tranche E`
- no Stage4-side reopen
- no evidence that the current Stage2/Stage3 follow-up promoted packet transport into a competing Stage4 owner

## 3. Pass 1. Current-Head Delta Inventory

Current workspace anchor:

- `HEAD`: `ce0f3b47b465fcd67796f75e0497a5f7c7b2424f`
- worktree: `clean`

Post-`eb5460ac` code deltas inside the authority lane:

- `modules/core/stage2_finalizer.py`
- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`

Post-`eb5460ac` commit history on those files:

- `e0ffc8df record arc23 post-patch proof progress`
- `ce0f3b47 Document Arc2/3 proof state and guard Stage34 demo frontier`

Scope split:

- in scope:
  - Stage2 emission and structured end-state promotion
  - Stage3 opening/protagonist/time precedence
  - Stage3 fact-lock suppression on true arc openings
  - Stage4 owner/transport semantics and current-session sink parity
  - governing-doc literal current-head freshness
- out of scope:
  - fresh runtime proof
  - Stage34 replay
  - queue reordering
  - implementation beyond this audit record

## 4. Pass 2. Live Authority Audit

### 4.1 Stage2 still emits bounded shared transport and now backfills structured end-state only under placeholder conditions

Evidence:

- `modules/core/stage2_finalizer.py:397` defines `_promote_last_tactical_end_state_to_structured_state()`
- `modules/core/stage2_finalizer.py:419`
- `modules/core/stage2_finalizer.py:427`
- `modules/core/stage2_finalizer.py:434`
- `modules/core/stage2_finalizer.py:1867`

What changed:

- last tactical end-state location/equipment/total-assets can now promote into `state_constraints.arc_end_state`
- promotion is blocked when equipment is an explicit authoritative empty clear
- numeric promotion also backfills `investment_calc.final_total_assets` only when that slot is still empty

Why this is alignment-preserving:

- the promotion only fills placeholder/unknown shells
- it does not override explicit authoritative empty inventory
- it improves the quality of the same Stage2 transport contract instead of widening owner scope

Focused evidence:

- `tests/test_stage2_finalizer.py:200`
- `tests/test_stage2_finalizer.py:1357`
- `tests/test_stage2_finalizer.py:1778`

### 4.2 Stage3 now treats true arc-opening time/location truth as authoritative and stops carrying stale previous-opening anchors into that opening

Evidence:

- `modules/core/episode_state_arbiter.py:132`
- `modules/core/episode_state_arbiter.py:313`
- `modules/core/episode_state_arbiter.py:334`
- `modules/core/episode_state_arbiter.py:438`
- `modules/core/episode_state_arbiter.py:455`
- `modules/domain/agents/blueprint_constraint_compiler.py:46`
- `modules/domain/agents/blueprint_constraint_compiler.py:56`
- `modules/domain/agents/blueprint_constraint_compiler.py:70`

What changed:

- arc-opening `time_truth` precedence now elevates `arc_data.state_changes.timeline`
- opening packets now surface an explicit `opening_transition_expectation` when the new opening location intentionally shifts
- fact-lock construction suppresses previous ending location/time/hook anchors when the opening episode already has authoritative upstream opening location or timeline truth

Why this is alignment-preserving:

- the owner is still upstream Stage2 arc truth, not a new Stage3-local invention
- the compiler is now less likely to pin the next blueprint to stale previous-episode opening anchors when the arc intentionally resets the opening
- this narrows contradiction between Stage2 intent and Stage3 consume behavior

Focused evidence:

- `tests/test_stage3_npc_capital_carryforward_guardrail.py:858`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py:907`

Residual caution:

- arc-opening time authority now depends more directly on `state_changes.timeline` quality
- if Stage2 timeline truth is sparse or sloppy, Stage3 will now trust that upstream truth more aggressively
- this is a quality watch item, not an owner-drift reopen

### 4.3 Stage4 still keeps FactLedger as owner and packet rows as transport/bootstrap only

Evidence:

- `tests/test_stage4_post_processor.py:1092`
- `tests/test_stage4_post_processor.py:1194`
- `tests/test_stage4_post_processor.py:2476`
- `tests/test_stage4_post_processor.py:2517`
- `tests/test_stage4_post_processor.py:2552`
- `tests/test_chief_writer_context.py:227`
- `tests/test_chief_writer_context.py:938`
- `tests/test_chief_writer_context.py:961`

Adversarial read:

- Stage4 still records `fact_ledger_carryover_baseline` as the owner when FactLedger rows exist
- packet-only fallback is explicitly labeled bootstrap rather than silently promoted into the owner slot
- writer hard-canon and carryover ceiling sections still surface the packet as upstream transport lineage, not as a hidden stronger owner

### 4.4 Current-session sink parity remains intact on the live head

Focused evidence:

- `tests/test_stage4_interview_round.py` focused shard on:
  - `sync_pass_result_selection_rationale_skips_when_preserving_historical_companion`
  - `sync_reject_result_selection_rationale_skips_when_preserving_historical_companion`
  - `build_pass_result_logging_payload_preserves_nested_repair_contract_subtype`
  - `append_episode_log_persists_patch_trace_raw_record`
  - `append_episode_log_persists_feedback_provenance_raw_record`

Adversarial read:

- historical companion preservation still wins when it should
- nested repair-contract subtype and raw patch-trace / feedback-provenance sinks still survive the current-head state
- the newer Stage2/Stage3 alignment changes did not destabilize current-session Stage4 sink honesty

## 5. Pass 3. Verification Audit

Commands run on current `HEAD`:

- `git rev-parse HEAD`
- `git status --short`
- `git diff --name-only eb5460ac9797cdb097bf5050ec902f6436f796fc..HEAD -- modules/core/cross_stage_authority_packet.py modules/core/stage2_finalizer.py modules/core/episode_state_arbiter.py modules/domain/agents/blueprint_constraint_compiler.py modules/core/stage4_context_builder.py modules/core/stage4_postselect_runtime.py modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py modules/core/stage4_interview_round.py modules/domain/agents/chief_writer_context.py modules/domain/agents/chief_writer_context_packets.py tests/test_continuity_packet.py tests/test_runtime_authority_contract.py tests/test_stage4_post_processor.py tests/test_stage4_interview_round.py tests/test_stage4_cw_false_miss_remediation.py`
- `git log --oneline eb5460ac9797cdb097bf5050ec902f6436f796fc..HEAD -- modules/core/stage2_finalizer.py modules/core/episode_state_arbiter.py modules/domain/agents/blueprint_constraint_compiler.py`
- `python -m py_compile modules/core/cross_stage_authority_packet.py modules/core/stage2_finalizer.py modules/core/episode_state_arbiter.py modules/domain/agents/blueprint_constraint_compiler.py modules/core/stage4_context_builder.py modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py modules/core/stage4_interview_round.py modules/domain/agents/chief_writer_context.py modules/domain/agents/chief_writer_context_packets.py`
- `pytest tests/test_stage2_finalizer.py -q`
- `pytest tests/test_stage3_blueprint_state_precision_guardrail.py -q`
- `pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q`
- `pytest tests/test_stage4_context_builder.py::TestBuildMandatoryContext::test_build_mandatory_context_promotes_numeric_carryover_authority_packet tests/test_stage4_context_builder.py::TestBuildMandatoryContext::test_build_mandatory_context_surfaces_cross_stage_numeric_transport_lineage tests/test_stage4_context_builder.py::TestBuildMandatoryContext::test_build_mandatory_context_falls_back_to_cross_stage_numeric_packet_when_fact_ledger_missing -q`
- `pytest tests/test_stage4_post_processor.py::TestProcessPassResult::test_persist_manager_delta_outputs_surfaces_cross_stage_numeric_transport_metadata tests/test_stage4_post_processor.py::TestAtomicMetadataSave::test_build_atomic_state_payloads_promotes_actual_truth_numeric_carryover_into_fact_ledger tests/test_stage4_post_processor.py::TestAtomicMetadataSave::test_build_atomic_state_payloads_bootstraps_packet_only_numeric_carryover_fields tests/test_stage4_post_processor.py::TestAtomicMetadataSave::test_build_atomic_state_payloads_reuses_state_truth_owner_contract_numeric_fields -q`
- `pytest tests/test_chief_writer_context.py::TestBuildCommonContext::test_build_common_context_promotes_stage4_numeric_carryover_authority_into_hard_canon tests/test_chief_writer_context.py::TestIFCPacketInputWiring::test_stage4_carryover_ceiling_falls_back_to_cross_stage_packet_when_fact_ledger_missing tests/test_chief_writer_context.py::TestIFCPacketInputWiring::test_stage4_carryover_ceiling_supplements_fact_ledger_with_packet_only_numeric_fields -q`
- `pytest tests/test_stage4_interview_round.py -k "sync_reject_result_selection_rationale_skips_when_preserving_historical_companion or sync_pass_result_selection_rationale_skips_when_preserving_historical_companion or build_pass_result_logging_payload_preserves_nested_repair_contract_subtype or append_episode_log_persists_patch_trace_raw_record or append_episode_log_persists_feedback_provenance_raw_record" -q`

Results:

- `HEAD`: `ce0f3b47b465fcd67796f75e0497a5f7c7b2424f`
- worktree: `clean`
- live post-`eb5460ac` authority-lane code diffs exist only in:
  - `modules/core/stage2_finalizer.py`
  - `modules/core/episode_state_arbiter.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
- compile: pass
- `tests/test_stage2_finalizer.py`: `71 passed`
- `tests/test_stage3_blueprint_state_precision_guardrail.py`: `49 passed`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py`: `36 passed`
- focused Stage4 context shard: `3 passed`
- focused Stage4 post-pass shard: `4 passed`
- focused chief-writer-context shard: `3 passed`
- focused Stage4 current-session parity shard: `5 passed, 308 deselected`

## 6. Judgment

This adversarial 3-pass audit lands with the following bounded verdict:

1. the current head does not reopen the `S2 -> S3 -> S4 authority-alignment` lane
2. the current-head deltas are real, but they tighten upstream authority semantics rather than creating a new owner split
3. the only material adversarial hit is governance drift: older execution/governing docs are no longer literal current-head anchors
4. downstream Stage4 owner vs transport semantics remain intact, and current-session sink parity remains green on focused verification

## 7. Next Step

After this audit:

1. treat this document as the current-head authority-alignment anchor until the next code drift
2. if any existing Stage234 execution SSOT or roadmap is later used to govern implementation, refresh its head-pointer metadata against this audit first
3. do not reopen Stage234 code or invent a hidden post-closure tranche from this audit alone
4. if runtime is later explicitly re-authorized, consume it as a separate proof action rather than treating this audit as runtime proof

## 8. 3-Pass Notes

Pass 1:

- challenged whether the later post-merge commits changed live authority-lane code at all

Pass 2:

- challenged whether the new Stage2/Stage3 deltas promoted a hidden new owner or only tightened upstream precedence

Pass 3:

- revalidated the current head with targeted compile/tests across Stage2, Stage3, Stage4 context, Stage4 post-pass, chief-writer context, and current-session parity surfaces
