# 0_0-stage234-global-authority-alignment-bounded-remediation Execution SSOT

Date: 2026-04-14
Status: pending (3-pass audited through merged-main post-merge adversarial current-head re-audit; `Tranche A/B/C`, hostile-reading hardening, the final bounded residual closures, the later medium and contract-drift closures, the later Stage4 runtime-authority-drift sibling residual closure, and the later `r12` Stage4 current-session closure wave are all landed on the current workspace; no additional pre-rerun code tranche is open, the latest bounded Stage234 closure anchor now points at one Stage4 current-session proof, and broader Stage3 / backend-wide proof remains operator-gated)
Canonical Path: `docs/2026-04-14/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `f005794b578d68bb855a960778c75ca3f77787a6`
- Baseline Dirty Summary: `clean main after Tranche C snapshot, post-C audit cleanup, and evidence-branch split`
- Resume Commit: `eb5460ac9797cdb097bf5050ec902f6436f796fc` (`merged main after PR #1; tree-identical to the audited r12 closure branch head on code/content state`)
- Resume Drift Summary: `the merged current workspace still carries the full bounded Stage234 chain plus the hostile-reading hardening, final residual closures, the later medium and contract-drift closures, the later Stage4 runtime-authority-drift sibling residual closure, and the later r12 Stage4 current-session closure wave: post-merge adversarial re-audit found no S2/S3/S4 authority-alignment code reopen on merged main, the latest bounded Stage234 closure anchor still points at one canary where the final authority sink / historical companion role / current-session sink alignment / hard gates all close together, and older pre-merge current-head SHA wording below is now provenance-only rather than the literal merged-head anchor`
Source Survey Docs:
- `docs/2026-04-14/stage234-global-authority-alignment-bounded-survey.md`
- `docs/2026-04-14/stage234-global-authority-alignment-tranche-a-current-head-3pass-audit.md`
- `docs/2026-04-14/stage234-global-authority-alignment-tranche-b-working-tree-3pass-audit.md`
- `docs/2026-04-14/stage234-global-authority-alignment-tranche-c-working-tree-3pass-audit.md`
- `docs/2026-04-14/stage234-global-authority-alignment-tranche-d-current-head-3pass-audit.md`
- `docs/2026-04-15/stage234-global-authority-alignment-post-residual-current-head-3pass-audit.md`
- `docs/2026-04-15/stage234-global-authority-alignment-post-medium-current-head-3pass-audit.md`
- `docs/2026-04-15/stage234-global-authority-alignment-post-contract-drift-current-head-3pass-audit.md`
- `docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-current-head-3pass-audit.md`
- `docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-working-tree-3pass-audit.md`
- `docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-live-canary-working-tree-3pass-audit.md`
- `docs/2026-04-16/stage234-global-authority-alignment-post-r12-stage4-current-session-closure-current-head-3pass-audit.md`
- `docs/2026-04-16/stage234-s2-s3-s4-authority-alignment-post-merge-current-head-adversarial-3pass-audit.md`
- `docs/2026-04-14/stage3-fundamental-root-cause-bounded-survey.md`
- `docs/2026-04-14/0_0-stage3-state-arbiter-envelope-bounded-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
Evidence Artifacts:
- `modules/core/cross_stage_authority_packet.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_postselect_runtime.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `tests/test_stage4_cw_false_miss_remediation.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_continuity_packet.py`
- `tests/test_runtime_authority_contract.py`
Side-Effect Coverage: covered (cross-stage authority transport, Stage2/3/4 prompt and sink surfaces, chief-writer carryover-ceiling parity, Stage4 HUD snapshot/live-HUD sink alignment, Stage4 advisory/logging contract honesty, Stage4 DB final sink persistence under live canary proof, roadmap/queue controller updates)
Confidence: `97%`

2026-04-16 merged-main post-merge adversarial drift override:

- Local audit HEAD: `eb5460ac9797cdb097bf5050ec902f6436f796fc`
- authoritative audit doc:
  - `docs/2026-04-16/stage234-s2-s3-s4-authority-alignment-post-merge-current-head-adversarial-3pass-audit.md`
- current gate result:
  - merged `main` is tree-identical to the audited `r12` closure branch head on code/content state
  - post-merge adversarial re-audit finds no `S2 -> S3 -> S4` authority-alignment reopen on the merged head
  - the existing `r12` current-session closure remains a valid bounded Stage234 anchor on merged `main`
  - older pre-merge `current-head` SHAs in the lower override blocks remain provenance-only when their literal head wording conflicts with this merged-main block
- current practical next action:
  - keep this lane proof-pending / operator-gated for broader proof, use this merged-main adversarial re-audit as the current-head governance anchor, and do not reopen Stage234 code unless later evidence opens a new bounded sibling residual
- historical-read note:
  - every lower 2026-04-16 / 2026-04-15 / 2026-04-14 override block remains provenance only; if any lower block's former literal `current-head` wording conflicts with the merged-main block above, the merged-main block wins

2026-04-16 post-r12 Stage4 current-session closure override:

- Local audit HEAD: `810f3fef3d11f4154b284e8002d7aaa8b07f7fe6`
- authoritative audit doc:
  - `docs/2026-04-16/stage234-global-authority-alignment-post-r12-stage4-current-session-closure-current-head-3pass-audit.md`
- later closure additions beyond the 2026-04-15 live-canary / selection-companion residual follow-ups:
  - pass-rate monitor and runtime-audit summary now persist on the same bounded canary exit path
  - reject-path companion rationale and raw-surface sinks no longer overwrite the historical companion row while normalized patch-trace metadata stays attached to the authoritative attempt sink
  - structured sink patch-trace normalization now survives rewrite-shaped winning attempts when advisory `partial_fix_eval.is_patch_attempt` proves patch lineage
- current gate result:
  - the Stage4 current-session closure objective is satisfied on the current head via `projects/_canary/canary_0_0_stage4_ep2_sinkproof_r12_patchtraceclosure`
  - `final_authority_contract_summary.status = ok`, `selection_role = historical_companion`, `current_session_sink_alignment_summary.status = ok`, and `hard_gates.status = pass` now close on the same bounded canary
  - no additional pre-rerun code tranche is open inside this lane after the `r12` closure
  - this is a bounded current-session closure anchor, not a broader Stage234 lane closure or backend-wide proof claim
  - broader Stage3 / backend-wide proof remains threshold-cleared but operator-gated under `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
- current practical next action:
  - keep this lane proof-pending / operator-gated for broader proof, treat the `r12` current-session closure as the latest workspace anchor, and only reopen this lane if later evidence reopens a bounded sibling residual rather than the already closed current-session Stage4 sink-alignment target
- historical-read note:
  - every 2026-04-15 / 2026-04-14 override block below remains provenance only; if any lower block's former `current practical next action` or `latest workspace anchor` wording conflicts with the 2026-04-16 block above, the 2026-04-16 block wins

2026-04-15 post-runtime-authority-drift live-canary working-tree closure override:

- Local workspace base HEAD: `03be22fcedfc7a196b92b59854d6fc9dfa1418f3`
- authoritative audit doc:
  - `docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-live-canary-working-tree-3pass-audit.md`
- later closure additions beyond the code-only working-tree closure:
  - the first bounded Stage4-only live canary exposed one more final-sink hole: `_build_stage4_db_attempt_payload()` leaked unsupported contract keys such as `director_verdict` into `save_stage_attempt()`, so Stage4 final sink rows failed while manuscripts/state logs/director companion rows still persisted
  - the bounded follow-up patch now keeps only schema-compatible top-level DB fields and leaves richer contract projection inside `advisory_flags`
  - the fresh Stage4-only canary rerun now records one coherent final sink row together with the persisted `hud_snapshot` and `state_logs.data.actual_truth`
- current gate result:
  - no additional pre-rerun code tranche is open inside this lane after the live-canary follow-up
  - one bounded Stage4-only live proof is now recorded on `projects/_canary/canary_0_0_stage4_ep2_sinkproof_r3_runtimeauth`
  - broader rerun remains threshold-cleared but operator-gated under `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
  - current residual warning is the narrower pre-final raw/selection surface drift plus unexercised retry coverage, not a reopen of the repaired final sink
- current practical next action:
  - historical only at that time: keep this lane operator-gated for broader rerun, treat the live-canary proof as the latest workspace anchor, and only reopen code here if the narrower raw pre-final drift later earns its own sibling residual doc

2026-04-15 post-runtime-authority-drift working-tree closure override:

- Local workspace base HEAD: `03be22fcedfc7a196b92b59854d6fc9dfa1418f3`
- authoritative audit doc:
  - `docs/2026-04-15/stage234-global-authority-alignment-post-runtime-authority-drift-working-tree-3pass-audit.md`
- later closure additions beyond the `post-contract-drift` and reopen audits:
  - Stage4 persisted `hud_snapshot` now projects the same approved HUD truth that the live HUD applies after DB save
  - Stage4 DB-attempt advisory normalization now preserves nested gate `scope_authority` over stale root scope
  - PASS_WITH_FIX logging/persistence now preserves `fix_pack.target_kind`, and the focused stale expectations are aligned to the current contract
- current gate result:
  - the earlier `03be22fc` Stage4 sibling reopen is closed on the current workspace
  - no additional pre-rerun code tranche is open inside this lane after the runtime-authority-drift closure
  - the Stage4 prompt-facing numeric authority `limit=3` remains a non-blocking watch item rather than a reopen trigger
  - fresh rerun remains threshold-cleared but operator-gated under `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
- current practical next action:
  - keep this lane proof-pending until explicit operator re-authorization consumes runtime proof or a later closure/demotion audit supersedes it

2026-04-15 post-contract-drift current-head closure override:

- Local audit HEAD: `5757a23a16289605da26d39ad6d06c84c7e5d3e6`
- authoritative audit doc:
  - `docs/2026-04-15/stage234-global-authority-alignment-post-contract-drift-current-head-3pass-audit.md`
- later closure additions beyond the `post-medium` audit:
  - the live Stage4 writer path now safely forwards `arc_data` into `ChiefWriter.generate_ensemble()`
  - shared packet build now preserves zero-valued numeric carryover and fails closed on nullish inventory sentinels
  - Stage3 packet precedence/provenance and Stage4 packet-bootstrap owner/provenance now report truthful contract lineage
- current gate result:
  - no additional pre-rerun code tranche is open inside this lane after the contract-drift closure
  - the Stage4 prompt-facing numeric authority `limit=3` remains a non-blocking watch item rather than a reopen trigger
  - fresh rerun remains threshold-cleared but operator-gated under `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
- current practical next action:
  - keep this lane proof-pending until explicit operator re-authorization consumes runtime proof or a later closure/demotion audit supersedes it

2026-04-15 post-medium current-head closure override:

- Local audit HEAD: `d2f500228ef67bb2f6fd23bbb0e257ba881a358e`
- authoritative audit doc:
  - `docs/2026-04-15/stage234-global-authority-alignment-post-medium-current-head-3pass-audit.md`
- later closure additions beyond the `post-residual` audit:
  - Stage4 chief-writer carryover ceiling and handoff digest now reuse the same packet-aware numeric authority truth as the mandatory Stage4 authority block
  - queue/controller docs now record both Stage234 and Stage3 envelope lanes as pending proof-gated lanes rather than active unopened code fronts
- current gate result:
  - no additional pre-rerun code tranche is open inside this lane after the medium closure
  - the Stage4 prompt-facing numeric authority `limit=3` remains a non-blocking watch item rather than a reopen trigger
  - fresh rerun remains threshold-cleared but operator-gated under `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
- current practical next action:
  - keep this lane proof-pending until explicit operator re-authorization consumes runtime proof or a later closure/demotion audit supersedes it

2026-04-15 post-residual current-head closure override:

- Local audit HEAD: `f93808ff25ffb1fde64534b2e50ac25a0dba59b3`
- authoritative audit doc:
  - `docs/2026-04-15/stage234-global-authority-alignment-post-residual-current-head-3pass-audit.md`
- landed closure additions beyond the original `Tranche D` audit:
  - Stage2 explicit empty inventory clear now survives carryover summary and end-state sync fallback
  - Stage3 institution fact-lock anchor truncation now preserves manuscript-authoritative institution names under the bounded anchor cap
- current gate result:
  - no additional pre-rerun code tranche is open inside this lane after the hostile-reading hardening and final residual closures
  - the Stage4 prompt-facing numeric authority `limit=3` remains a non-blocking watch item rather than a reopen trigger
  - fresh rerun remains threshold-cleared but operator-gated under `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
- current practical next action:
  - keep this lane proof-pending until explicit operator re-authorization consumes runtime proof or a later closure/demotion audit supersedes it

2026-04-14 current-head Tranche D rerun-gate override:

- Local audit HEAD: `2fec364d6652ccbda68757cbc1c71a626eee5b41`
- authoritative audit doc:
  - `docs/2026-04-14/stage234-global-authority-alignment-tranche-d-current-head-3pass-audit.md`
- landed tranches:
  - `Tranche A`
  - `Tranche B`
  - `Tranche C`
- current gate result:
  - no additional pre-rerun code tranche is open inside this lane
  - the cross-stage packet path is realized end-to-end from `Stage2 emit -> Stage3 prefer -> Stage4 intake/post-pass reuse`
  - fresh rerun remains threshold-cleared but operator-gated under `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
- current practical next action:
  - keep this lane proof-pending until explicit operator re-authorization consumes runtime proof or a later closure/demotion audit supersedes it

2026-04-14 current-head Tranche A re-audit override:

- Local audit HEAD: `8a9490531f7fa2f0527cb70407cdb804d87d7ddd`
- authoritative audit doc:
  - `docs/2026-04-14/stage234-global-authority-alignment-tranche-a-current-head-3pass-audit.md`
- landed tranche:
  - `Tranche A` only
- landed effects:
  - shared `CrossStageAuthorityPacket` contract now exists under `modules/core/`
  - `Stage2Finalizer` emits the packet after Stage2 normalization into the finalized saved arc payload
  - Stage2 advisory sinks mirror the packet while preserving the legacy `carryover_authority` summary
  - carryover UI observability now exposes packet presence/version metadata only; the human-facing message shape stays unchanged
  - legacy `[Carryover Authority Packet]` text compatibility remains green on current-head tests
- remaining deferred work:
  - current-head `Tranche D` proof / rerun gate revisit is now recorded separately
- current practical next action:
  - historical only; superseded by the current-head `Tranche D` override above

## 1. Intent

Open the next bounded long-horizon lane after `Stage3 Tranche C`:

- do not widen back into rerun-first
- do not widen into `Polaris`
- do not reopen a broad vocabulary rewrite

This lane exists because:

- Stage3 local authority fragmentation has been materially reduced
- the next higher-ROI debt is now cross-stage transport fragmentation

## 2. Baseline Facts

1. Stage2 now emits stronger carryover/start-state truth, but still through multiple surfaces.
2. Stage3 now owns a real `EpisodeStatePacket`, but that packet is still Stage3-local.
3. Stage4 already owns explicit authority precedence, numeric carryover authority, and post-select truth-pin contracts.
4. The remaining gap is not missing concepts. It is the lack of one bounded shared authority transport contract across the stage boundary.

## 3. Scope

Included:

- shared cross-stage authority packet contract
- Stage2 emission of that packet
- Stage3 preferential consume of that packet
- Stage4 intake and post-pass reuse of that packet
- targeted observability and queue/doc updates required to keep the packet visible

Excluded:

- rerun execution in this document
- `Polaris` / `DecisionKernel`
- broad retry-runtime refactor
- repo-wide vocabulary sweep
- DB schema redesign
- artifact rewrites in `projects/*`

## 4. Execution Tranches

### Tranche A. CrossStageAuthorityPacket Contract + Stage2 Emission

Goal:

- create one bounded transport contract for carryover/start-state authority

Primary targets:

- new packet contract module under `modules/core/`
- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/arc_ensemble.py`

Required packet families:

- `opening_carryover`
- `protagonist_carryover`
- `numeric_carryover`
- `source_precedence`
- `provenance`

Guardrails:

- do not remove legacy Stage2 surfaces yet
- emit the new packet alongside existing fields first
- keep compatibility with current sinks and prompts

Current status:

- landed on current `main` at `8a949053`
- realized surfaces:
  - `modules/core/cross_stage_authority_packet.py`
  - `modules/core/stage2_finalizer.py`
  - `tests/test_stage2_finalizer.py`
- verified effects:
  - finalized Stage2 arcs now persist `cross_stage_authority_packet`
  - Stage2 advisory sinks now mirror `cross_stage_authority_packet`
  - legacy Stage2 carryover text packet path is preserved and still green

### Tranche B. Stage3 Preferential Consume

Goal:

- make Stage3 consume the shared packet first when present

Primary targets:

- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- bounded Stage3 observability only if required

Guardrails:

- keep `EpisodeStatePacket` as the Stage3-local working surface
- do not reopen whole-envelope work or retry-runtime work in the same tranche
- preserve compatibility fallback to current scattered inputs while migration is incomplete

### Tranche C. Stage4 Intake + Post-Pass Reuse

Goal:

- make Stage4 intake and post-pass authority surfaces reuse the same transport lineage

Primary targets:

- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_postselect_runtime.py`
- `modules/domain/agents/chief_writer_context_packets.py`

Guardrails:

- keep current numeric carryover authority logic intact unless the new packet supplies the same or stronger provenance
- do not widen into a full Stage4 writer-context redesign

### Tranche D. Proof / Rerun Gate Revisit

Goal:

- after A/B/C land, re-audit the governing docs and decide whether rerun should reopen

Current status:

- recorded on current `main` at `2fec364d`
- authoritative audit:
  - `docs/2026-04-14/stage234-global-authority-alignment-tranche-d-current-head-3pass-audit.md`
- verified result:
  - rerun remains operator-gated under the canonical Stage3 gate
  - no hidden `Tranche E` is opened by this lane alone

## 5. Acceptance Criteria

- a bounded shared `CrossStageAuthorityPacket` exists
- Stage2 emits it without deleting current compatible surfaces
- Stage3 can consume it as the preferred upstream authority transport
- Stage4 intake and post-pass can reuse its lineage rather than rebuilding the same carryover story independently
- no touched production function enters a new `180+ LOC` band
- targeted tests and ops/doc validation pass

## 6. Verification Plan

- targeted compile on new/touched modules
- targeted pytest for:
  - Stage2 carryover authority
  - Stage3 packet consume path
  - Stage4 numeric carryover authority and post-pass owner contract
- UTF-8 hygiene:
  - `python scripts/check_utf8_hygiene.py ...`
- queue/doc validation:
  - `python scripts/ops_validator.py --strict`

## 7. Non-Goals

- do not convert this into the older broad Stage234 vocabulary lane
- do not reopen `retry owner debt` inside this execution wave
- do not consume the rerun authorization with this document alone

## 8. Current Decision

The post-`Tranche D` gate decision, after the hostile-reading / medium / contract / runtime follow-ups and the later `r12` Stage4 current-session closure, is now exercised as:

- `fresh rerun`: threshold-cleared but still operator-gated
- `retry owner debt`: deferred as a lower-ROI follow-up
- `this lane`: proof-pending with no additional pre-rerun code tranche currently open after the hostile-reading hardening, later 2026-04-15 closure chain, and the bounded `r12` Stage4 current-session closure anchor

Current next action:

1. keep this lane proof-pending until explicit operator re-authorization consumes runtime proof or a later closure/demotion audit supersedes it
2. do not widen into broader Stage4 redesign, `ChiefWriter` plumbing, `Stage4PostselectRuntime`, or retry-owner debt as a hidden `Tranche E`
3. treat the next local code-first owner outside this lane as `0_0-stage3-state-arbiter-envelope-bounded-remediation` unless runtime is explicitly re-authorized first
