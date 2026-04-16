# Stage234 S2-S3-S4 Authority Alignment Post-Merge Current-Head Adversarial 3-Pass Audit

Date: 2026-04-16
Status: final (3-pass audited; adversarial current-head re-audit after PR #1 merge on `main`)
Canonical Path: `docs/2026-04-16/stage234-s2-s3-s4-authority-alignment-post-merge-current-head-adversarial-3pass-audit.md`
Commit State:
- Baseline Commit: `eb5460ac9797cdb097bf5050ec902f6436f796fc`
- Baseline Dirty Summary: `clean main after PR #1 merge; no local tracked/untracked drift`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-14/stage234-global-authority-alignment-bounded-survey.md`
- `docs/2026-04-14/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
- `docs/2026-04-16/stage234-global-authority-alignment-post-r12-stage4-current-session-closure-current-head-3pass-audit.md`
- `docs/2026-04-16/stage3-state-arbiter-envelope-post-r12-stage234-no-reopen-current-head-3pass-audit.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
Evidence Artifacts:
- `modules/core/cross_stage_authority_packet.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage3_blueprint_state_precision_guardrail.py`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_failure_analyzer.py`
Side-Effect Coverage: covered (Stage2 packet emission and observability, Stage3 arbitration precedence, Stage4 intake ceiling authority, Stage4 post-pass owner contract persistence, Stage4 current-session reject/logging parity, roadmap/governing-doc authority)
Confidence: `97%`

## 1. Intent

Re-audit the merged `main` head after PR #1 and answer one adversarial question:

- did the `S2 -> S3 -> S4` authority-alignment lane reopen, drift, or silently downgrade when the bounded `r12` closure bundle moved from branch head to merged `main`?

This audit is intentionally narrower than a new runtime proof run.

It does not:

- authorize Stage3 runtime by itself
- reopen `Stage234` realization
- claim a fresh backend-wide proof net

## 2. Adversarial Findings

### Finding 1. Governing-doc current-head anchors are now provenance, not literal current HEAD

Severity: medium

The merged workspace head is now `eb5460ac`, but the latest governing authority docs still name pre-merge branch SHAs as their local current-head anchors:

- `0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot` resumes from `810f3fef`
- the latest Stage3 no-reopen audit is anchored at `cb11e198`

This is not a code regression, but it is real governance drift if those older SHAs are read literally as "current HEAD" on merged `main`.

Adversarial consequence:

- those docs remain valid as provenance for code/content state
- they should not be treated as the only literal current-head anchor for post-merge implementation without this re-audit or a later doc refresh

### Finding 2. No live code-level S2-S3-S4 authority-alignment reopen was found on merged `main`

Severity: none

The merged head did not introduce a hidden post-closure code delta.

Adversarial evidence:

- `git rev-list --parents -n 1 HEAD` shows `eb5460ac` is a merge commit of `44e59158` and `e59a75cd`
- `git diff --name-only e59a75cdbe32eb808cc5105ee98f0335d4c928b5..HEAD` is empty

Operational consequence:

- the merged tree is content-identical to the audited PR head
- the existing `r12` Stage4 current-session closure evidence remains portable to merged `main`

## 3. Pass 1. Governing-Doc Audit

The pre-merge authority stack already said three things:

1. `Stage234` no longer has an open pre-rerun code tranche
2. the `Stage3 state-arbiter-envelope` lane is `proof-pending / operator-gated`
3. if runtime is later authorized, prefer bounded `ep9` continuation rather than reopening hidden `Tranche E`

Adversarial check:

- does PR merge invalidate that stack?

Answer:

- no on code/content
- yes on literal head-pointer freshness

Why:

1. the merge commit changes git history identity
2. the merge commit does not change the audited closure tree
3. therefore the lane judgment survives, but the old "current-head" labels become provenance-only anchors

## 4. Pass 2. Current-Workspace Authority Audit

### 4.1 Stage2 emission remains explicit and bounded

Current `main` still emits the shared packet inside `Stage2Finalizer`:

- `modules/core/stage2_finalizer.py`
  - `build_cross_stage_authority_packet()` is called before pass-arc return
  - the resolved packet is also mirrored into advisory/observability flags when present

Adversarial read:

- Stage2 did not lose the explicit transport packet during merge
- legacy summary surfaces still coexist, but the packet remains present and versioned rather than silently implied

### 4.2 Stage3 still consumes packet truth preferentially instead of rebuilding from scratch

Current `main` still consumes the packet in two bounded places:

- `modules/core/episode_state_arbiter.py`
  - opening/protagonist/numeric truth prioritizes packet lineage when available
- `modules/domain/agents/blueprint_constraint_compiler.py`
  - Stage3 inherited-state and numeric-family extraction reuses the explicit packet contract

Adversarial read:

- Stage3 is still packet-aware on merged `main`
- no merge-side regression reintroduced a pure scattered-source rebuild

### 4.3 Stage4 still treats packet transport as lineage, not as a hidden competing owner

Current `main` still preserves the intended downstream split:

- `modules/domain/agents/chief_writer_context_packets.py`
  - FactLedger carryover baseline remains stronger when available
  - packet rows supplement or bootstrap only when the stronger persisted authority is absent
- `modules/core/stage4_post_pass_runtime.py`
  - downstream owner contract remains `fact_ledger_carryover_baseline`
  - packet-only ownership is explicitly labeled `cross_stage_authority_packet_bootstrap`
  - transport lineage is preserved under `numeric_carryover_authority`

Adversarial read:

- packet transport is not silently promoted into a competing hidden owner when FactLedger exists
- bootstrap fallback remains explicit and inspectable, not covert

### 4.4 Stage4 current-session closure parity still holds on merged `main`

The branch-to-main merge did not alter the `r12` closure tree:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`

Adversarial read:

- historical companion preservation and patch-trace parity remain on the merged head because the merge added no content delta beyond the audited branch head

Residual caution:

- this audit did not consume a brand-new post-merge canary run
- instead it verified tree identity against the already audited `e59a75cd` closure head
- that is sufficient for merged-head no-reopen judgment, but not a substitute for a future fresh runtime proof if the operator explicitly requests one

## 5. Pass 3. Verification Audit

Commands run on current merged `HEAD`:

- `git status --short --branch`
- `git rev-parse HEAD`
- `git rev-list --parents -n 1 HEAD`
- `git diff --name-only cb11e19843c464d844845394ba13910d074194ae..HEAD`
- `git diff --name-only 810f3fef3d11f4154b284e8002d7aaa8b07f7fe6..HEAD`
- `git diff --name-only e59a75cdbe32eb808cc5105ee98f0335d4c928b5..HEAD`
- `python -m py_compile modules/core/cross_stage_authority_packet.py modules/core/stage2_finalizer.py modules/core/episode_state_arbiter.py modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/chief_writer_context_packets.py modules/core/stage4_post_pass_runtime.py modules/core/stage4_interview_round.py modules/core/stage4_reject_runtime.py`
- `pytest tests/test_stage2_finalizer.py -q`
- `pytest tests/test_stage3_blueprint_state_precision_guardrail.py::TestCapitalContinuityPacket tests/test_stage3_npc_capital_carryforward_guardrail.py::TestEpisodeStatePacket -q`
- `pytest tests/test_stage4_context_builder.py::TestBuildMandatoryContext::test_build_mandatory_context_promotes_numeric_carryover_authority_packet tests/test_stage4_context_builder.py::TestBuildMandatoryContext::test_build_mandatory_context_surfaces_cross_stage_numeric_transport_lineage tests/test_stage4_context_builder.py::TestBuildMandatoryContext::test_build_mandatory_context_falls_back_to_cross_stage_numeric_packet_when_fact_ledger_missing -q`
- `pytest tests/test_stage4_post_processor.py::TestProcessPassResult::test_persist_manager_delta_outputs_surfaces_cross_stage_numeric_transport_metadata tests/test_stage4_post_processor.py::TestAtomicMetadataSave::test_build_atomic_state_payloads_promotes_actual_truth_numeric_carryover_into_fact_ledger tests/test_stage4_post_processor.py::TestAtomicMetadataSave::test_build_atomic_state_payloads_reuses_state_truth_owner_contract_numeric_fields -q`
- `pytest tests/test_stage4_interview_round.py -k "record_s4_attempt_defaults_patch_strategy_for_advisory_patch_lineage or record_s4_attempt_defaults_patch_strategy_for_direct_patch or record_s4_attempt_defaults_patch_strategy_for_patch_fallback or append_episode_log_persists_patch_trace_raw_record or append_episode_log_does_not_project_patch_trace_from_fix_pack_when_not_patch or pass_with_fix_episode_log_uses_final_attempt_meta_and_preserves_selection_meta or build_pass_result_logging_payload_preserves_nested_repair_contract_subtype or sync_reject_result_selection_rationale_skips_when_preserving_historical_companion or build_stage4_patch_advisory_payload_replaces_placeholder_patch_targets_with_trace_targets" -q`
- `pytest tests/test_failure_analyzer.py -k "tracks_stage4_feedback_provenance_mismatch or ignores_prefinal_companion_contract_and_feedback_drift or tracks_stage4_patch_trace_mismatch or ignores_pre_final_director_companion_mismatch" -q`

Results:

- worktree: clean on `main...origin/main`
- merged `HEAD`: `eb5460ac9797cdb097bf5050ec902f6436f796fc`
- merge parents: `44e59158` + `e59a75cd`
- `e59a75cd..HEAD` diff: empty
- compile: pass
- `tests/test_stage2_finalizer.py`: `68 passed`
- Stage3 packet/arbitration shard: `17 passed`
- focused Stage4 intake shard: `3 passed`
- focused Stage4 post-pass shard: `3 passed`
- focused Stage4 current-session parity shard: `9 passed`
- focused FailureAnalyzer parity shard: `4 passed`

## 6. Judgment

This adversarial 3-pass audit lands with the following bounded verdict:

1. merged `main` does not reopen the `S2-S3-S4 authority-alignment` lane at code level
2. the current tree preserves the bounded Stage234 closure state already audited on branch head
3. no hidden `Tranche E`, no forced Stage234 reopen, and no automatic Stage3 runtime authorization were discovered
4. the only material adversarial hit is document-anchor drift: older "current-head" SHA labels are now provenance-only after merge

## 7. Next Step

After this audit:

1. treat `Stage234` as still `proof-pending / operator-gated`, not reopened
2. treat bounded `ep9` continuation as the preferred future runtime path only if runtime is explicitly re-authorized
3. do not reopen Stage234 code or introduce a hidden post-closure tranche from this audit
4. before any new governing-doc-driven implementation, refresh the relevant Stage234 / Stage3 execution SSOT or roadmap anchors so they point at merged-head authority rather than pre-merge branch SHAs

## 8. 3-Pass Notes

Pass 1:

- challenged whether PR merge itself invalidated the earlier lane judgment

Pass 2:

- challenged each boundary for hidden owner drift, especially packet-bootstrap and FactLedger overlap semantics

Pass 3:

- revalidated the merged head with targeted compile/tests and tree-identity checks against the audited branch closure head
