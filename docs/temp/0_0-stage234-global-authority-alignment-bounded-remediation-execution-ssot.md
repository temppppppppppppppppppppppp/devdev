# 0_0-stage234-global-authority-alignment-bounded-remediation Execution SSOT

Date: 2026-04-14
Status: active (3-pass audited through current-head `Tranche A`; working-tree `Tranche B` and `Tranche C` closure audits are now recorded; `Tranche D` is the next bounded gate)
Canonical Path: `docs/2026-04-14/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `f005794b578d68bb855a960778c75ca3f77787a6`
- Baseline Dirty Summary: `clean main after Tranche C snapshot, post-C audit cleanup, and evidence-branch split`
- Resume Commit: `8a9490531f7fa2f0527cb70407cdb804d87d7ddd` (`stage2: emit cross-stage authority packet`)
- Resume Drift Summary: `current head lands the bounded Tranche A Stage2 emission slice, the live working tree also lands bounded Tranche B Stage3 preferential consume, and the current working tree now also lands bounded Tranche C Stage4 intake/post-pass reuse: Stage4ContextBuilder reuses explicit CrossStageAuthorityPacket numeric lineage with ledger-first fallback, and Stage4PostPassRuntime carries that transport lineage into numeric carryover authority contracts while atomic overlay reuses the settled contract fields; the Tranche C closure audit is now recorded and Tranche D becomes the next gate`
Source Survey Docs:
- `docs/2026-04-14/stage234-global-authority-alignment-bounded-survey.md`
- `docs/2026-04-14/stage234-global-authority-alignment-tranche-a-current-head-3pass-audit.md`
- `docs/2026-04-14/stage234-global-authority-alignment-tranche-b-working-tree-3pass-audit.md`
- `docs/2026-04-14/stage234-global-authority-alignment-tranche-c-working-tree-3pass-audit.md`
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
- `modules/domain/agents/chief_writer_context_packets.py`
Side-Effect Coverage: covered (cross-stage authority transport, Stage2/3/4 prompt and sink surfaces, roadmap/queue controller updates)
Confidence: `96%`

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
  - `Tranche D` proof / rerun gate revisit
- current practical next action:
  - use the recorded `Tranche C` closure to decide whether rerun should reopen or remain operator-gated

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

The post-`Tranche C` branch decision is now exercised as:

- `fresh rerun`: deferred and still operator-gated
- `retry owner debt`: deferred as a lower-ROI follow-up
- `next active bounded lane`: `0_0-stage234-global-authority-alignment-bounded-remediation`

Current next action:

1. open `Tranche D` as a bounded proof / rerun gate revisit
2. re-audit the governing docs against the current head before deciding whether fresh rerun reopens
3. do not widen into broader Stage4 redesign, `ChiefWriter` plumbing, or retry-owner debt in the same wave
