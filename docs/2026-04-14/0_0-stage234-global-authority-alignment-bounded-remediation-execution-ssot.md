# 0_0-stage234-global-authority-alignment-bounded-remediation Execution SSOT

Date: 2026-04-14
Status: active (3-pass audited; next bounded long-horizon follow-up after Stage3 Tranche C)
Canonical Path: `docs/2026-04-14/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `f005794b578d68bb855a960778c75ca3f77787a6`
- Baseline Dirty Summary: `clean main after Tranche C snapshot, post-C audit cleanup, and evidence-branch split`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-14/stage234-global-authority-alignment-bounded-survey.md`
- `docs/2026-04-14/stage3-fundamental-root-cause-bounded-survey.md`
- `docs/2026-04-14/0_0-stage3-state-arbiter-envelope-bounded-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
Evidence Artifacts:
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

1. realize `Tranche A`
2. snapshot and validate
3. then decide whether `Tranche B` opens immediately or after another bounded audit
