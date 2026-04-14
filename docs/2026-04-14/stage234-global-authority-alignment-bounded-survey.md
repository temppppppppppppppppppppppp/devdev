# Stage234 Global Authority Alignment Bounded Survey

Date: 2026-04-14
Status: final (3-pass audited lane-shape authority; current implementation note refreshed after current-head `Tranche D` rerun-gate audit)
Canonical Path: `docs/2026-04-14/stage234-global-authority-alignment-bounded-survey.md`
Commit State:
- Baseline Commit: `f005794b578d68bb855a960778c75ca3f77787a6`
- Baseline Dirty Summary: `clean main after Tranche C snapshot, post-C audit cleanup, and evidence-branch split`
- Resume Commit: `8a9490531f7fa2f0527cb70407cdb804d87d7ddd`
- Resume Drift Summary: `the survey body remains the lane-shape authority; current implementation has now moved from current-head Tranche A land to current-head A/B/C realization plus a recorded Tranche D rerun-gate audit, so no further pre-rerun code tranche is open inside this lane and rerun remains operator-gated`
Source Survey Docs:
- `docs/2026-04-14/stage3-fundamental-root-cause-bounded-survey.md`
- `docs/2026-04-14/0_0-stage3-state-arbiter-envelope-bounded-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-14/stage234-global-authority-alignment-tranche-b-working-tree-3pass-audit.md`
- `docs/2026-04-14/stage234-global-authority-alignment-tranche-c-working-tree-3pass-audit.md`
- `docs/2026-04-14/stage234-global-authority-alignment-tranche-d-current-head-3pass-audit.md`
Evidence Artifacts:
- `modules/domain/agents/arc_ensemble.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_postselect_runtime.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/domain/agents/chief_writer_context_packets.py`
Side-Effect Coverage: covered (Stage2 emission, Stage3 carryover arbitration, Stage4 intake authority, Stage4 post-pass owner contract, queue/controller docs)
Confidence: `96%`

Current-head implementation note:

- the body below remains the pre-`Tranche A` inventory and root-cause basis that selected this lane
- current implementation note:
  - `Tranche A/B/C` are landed on current-head `2fec364d`
  - current-head `Tranche D` rerun-gate audit is recorded in `stage234-global-authority-alignment-tranche-d-current-head-3pass-audit.md`
  - working-tree closure status is recorded in `stage234-global-authority-alignment-tranche-b-working-tree-3pass-audit.md`
  - working-tree closure status is also recorded in `stage234-global-authority-alignment-tranche-c-working-tree-3pass-audit.md`
  - no further pre-rerun code tranche is open inside this lane
  - fresh rerun remains operator-gated under `stage3-debt-remediation-bounded-survey-and-rerun-gate.md`

## 1. Intent

Identify the next bounded long-horizon fix point after `Stage3 Tranche A/B/C`.

This survey asks one question:

- if the operator wants to keep going debt-first instead of opening rerun-first proof, what is the narrowest cross-stage authority-alignment lane with the best structural ROI?

This is not:

- a `Polaris` rewrite
- a whole-pipeline vocabulary rewrite
- a broad retry-runtime refactor
- a fresh rerun authorization

## 2. Scope

Included:

- Stage2 carryover/start-state emission:
  - `modules/domain/agents/arc_ensemble.py`
  - `modules/core/stage2_finalizer.py`
- Stage3 pre-generation carryover arbitration:
  - `modules/core/episode_state_arbiter.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
- Stage4 intake and post-pass authority surfaces:
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_postselect_runtime.py`
  - `modules/core/stage4_post_pass_runtime.py`
  - `modules/domain/agents/chief_writer_context_packets.py`

Excluded:

- `Stage3RetryCoordinator` follow-up refactor
- broad Stage4 writer redesign
- prompt-style retuning
- DB schema redesign
- repo-wide rename sweep

## 3. Pass 1. Inventory Summary

### 3.1 Stage2 still emits carryover truth through more than one lane

Current Stage2 authority surfaces are split across:

1. structured arc packet fields:
   - `state_constraints.arc_start_state`
   - `state_constraints.arc_end_state`
   - `joint_docs`
2. prompt-facing carryover transport:
   - `arc_ensemble._render_carryover_authority_packet()`
3. sink/observability summary:
   - `stage2_finalizer._build_stage2_carryover_authority_summary()`
   - Stage2 `carryover_authority` observability rows

Operational consequence:

- Stage2 now preserves more carryover truth than before
- but it still does not emit one canonical cross-stage packet that later stages consume unchanged

### 3.2 Stage3 now has a real local arbiter, but it is still Stage3-local

`EpisodeStateArbiter` is real and useful:

- it resolves source precedence
- it records `dropped_conflicts`
- it surfaces `rewrite_required_reasons`

But it still builds the packet from translated Stage2 artifacts rather than from one shared pipeline-level authority packet.

Operational consequence:

- Stage3 local duplication is reduced
- cross-stage transport duplication is not

### 3.3 Stage4 intake and post-pass each have authority logic, but not the same transport

Stage4 intake already has explicit authority guidance:

- numeric carryover authority block in `stage4_context_builder.py`
- authority precedence statements that demote advisory summaries under canonical layers

Stage4 post-pass also has explicit authority contracts:

- `state_truth_owner_contract`
- `numeric_carryover_authority`
- post-select `truth_pins`

Operational consequence:

- Stage4 is not missing authority vocabulary
- it still reconstructs authority from multiple upstream surfaces instead of consuming the same packet that Stage3 used

### 3.4 The real cross-stage gap is transport and lineage, not missing concepts

The system already knows how to express:

- carryover authority
- source precedence
- rewrite-required reasons
- truth pins
- state-truth owner contracts

What it still lacks is one bounded transport contract across `Stage2 -> Stage3 -> Stage4`.

Operational consequence:

- the same truth family can survive each local stage
- but still drift at the stage boundary because each stage rebuilds it from a different mix of sources

## 4. Pass 2. Adversarial Hypothesis Audit

### Hypothesis A. `Stage3 A/B/C already solved the meaningful authority problem`

Verdict: rejected.

Reason:

- Stage3-local fragmentation dropped
- cross-stage transport fragmentation remains

### Hypothesis B. `Stage2 carryover authority is already the canonical upstream owner, so no new lane is needed`

Verdict: rejected.

Reason:

- Stage2 has stronger authority summaries now
- but they still coexist with text packet emission plus separate structured state fields
- later stages do not consume one shared Stage2-owned packet

### Hypothesis C. `Stage4 numeric carryover authority is the real next owner, so the fix should stay Stage4-local`

Verdict: partially accepted, then narrowed.

Reason:

- Stage4 still owns the final downstream closure for numeric carryover truth
- but a pure Stage4-local patch would again leave upstream transport semantics duplicated
- the higher-ROI move is to normalize the shared transport before another Stage4-only tightening slice

### Hypothesis D. `The right answer is to reopen the older Stage234 cross-stage vocabulary lane`

Verdict: rejected as the direct controller.

Reason:

- that older lane is broader and more vocabulary-heavy
- the current-head need is narrower:
  - cross-stage carryover/start-state transport
  - source-precedence lineage
  - Stage4 intake/post-pass reuse of the same bounded authority packet

## 5. Pass 3. Root-Cause Judgment

The next durable problem is:

`cross-stage authority transport fragmentation`

More explicit form:

`Stage2, Stage3, and Stage4 each express the same carryover/start-state authority family, but the pipeline still lacks one bounded canonical transport packet with stable provenance and precedence semantics across those boundaries.`

This is not the same as the earlier Stage3-only root cause.

Current stack after `Tranche C`:

1. `Stage3 local authority-lane fragmentation`:
   - materially reduced
2. `cross-stage authority transport fragmentation`:
   - still live
3. `retry owner debt`:
   - still real, but now lower ROI than the transport gap above

## 6. Recommended Bounded Execution Shape

### Tranche A. CrossStageAuthorityPacket contract + Stage2 emission

Goal:

- define one bounded shared packet for carryover/start-state authority

Contents:

- `opening/start-state`
- `protagonist carryover`
- `numeric carryover`
- `source_precedence`
- `provenance`

### Tranche B. Stage3 preferential consume

Goal:

- make `EpisodeStateArbiter` and compiler paths prefer the shared packet over scattered Stage2 fields when present

### Tranche C. Stage4 intake + post-pass reuse

Goal:

- make Stage4 intake authority blocks and post-pass owner contracts read the same packet lineage instead of reconstructing it separately

### Tranche D. Proof / rerun decision

Goal:

- decide whether the global authority-alignment lane is enough to justify rerun reopening, or whether more bounded runtime work is still required

## 7. Improvement Expectation

Expected high-confidence gains:

- less Stage2/3/4 carryover/start-state reinterpretation drift
- clearer provenance for numeric carryover and opening truth
- lower chance that Stage4 re-derives a different authority story than Stage3 used

Expected medium-confidence gains:

- less downstream prompt-envelope noise
- easier proof/rerun attribution because authority lineage is clearer end-to-end

Not promised by this lane alone:

- instant pass-rate jump
- elimination of all retry-runtime debt
- full cross-stage vocabulary unification

## 8. Final Judgment

The right next long-horizon bounded lane is not `retry owner debt`.

It is:

`0_0-stage234-global-authority-alignment-bounded-remediation`

with the first implementation slice focused on a shared `CrossStageAuthorityPacket`.
