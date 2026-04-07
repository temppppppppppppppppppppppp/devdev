# Stage234 Handoff Harness Merge Audit

Date: 2026-04-07
Status: final
Document Type: merged survey audit
Canonical Path: `docs/2026-04-07/stage234-handoff-harness-merge-audit.md`
Temp Mirror Path: `(none - merge-only audit; no docs/temp mirror)`
Track: system
Mode: read-only merge audit; no code patching; no queue mutation
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: active temp roadmap/queue mirrors plus widespread narrative/output/docs deltas; four stage234 terminal survey docs landed under docs/2026-04-07`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-07/stage234-terminal1-stage2-producer-handoff-survey.md`
- `docs/2026-04-07/stage234-terminal2-stage3-binding-handoff-survey.md`
- `docs/2026-04-07/stage234-terminal3-stage4-consumer-handoff-survey.md`
- `docs/2026-04-07/stage234-terminal4-crosscut-authority-matrix-survey.md`
Side-Effect Coverage: inherited from the four source survey docs; this merge turn added no new live-run evidence and performed no new side-effect sweep beyond source-doc consolidation
Confidence: `96%`

## 1. Coverage

This audit merged the four bounded lane docs created by the 2026-04-07
`Stage234 Handoff Harness 4-Terminal Parallel Survey Order`.

Included:

- Stage2 producer / handoff findings
- Stage3 binding / blueprint handoff findings
- Stage4 consumer / manuscript handoff findings
- Cross-stage authority / compression / promotion findings
- Existing queue coverage checks against:
  - `docs/2026-04-01/active-temp-execution-roadmap.md`
  - `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
  - `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
  - `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
  - `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`

Excluded:

- code patching
- `docs/temp/` mutation
- queue reordering
- fresh runtime or live-run evidence
- new execution SSOT creation before merge and promotion gate review

Convergence result:

- no material contradiction was found across the four lane docs
- all four lane docs converge on `existing queue coverage`
- the cross-cut lane is stronger than the single-stage lanes for topic framing,
  but it still does not justify a new topic slug

## 2. Findings

### F-1. Numeric carryover baseline promotion remains the sharpest still-live seam (severity: high, class: cross-stage with Stage4 front ownership)

Terminal 3 and Terminal 4 agree on the same front issue:

- Stage4 persists `numeric_carryover_authority` and related owner metadata, but
  does not autonomously promote manuscript-proven numeric changes into the next
  carryover baseline.
- This creates bounded false-positive contradiction pressure at the next-episode
  boundary even when the current episode passed.

Converging source findings:

- Terminal 3 `F-2`
- Terminal 4 `F1`

Primary owner files:

- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/fact_ledger.py`

Queue mapping:

- active front of `0_0-stage4-consumer-contract-normalization-remediation`

### F-2. Constraint strength is diluted from Stage2 structured truth into Stage4 prose advisory (severity: high, class: cross-stage)

Terminal 2, Terminal 3, and Terminal 4 all point to the same authority-loss
family:

- Stage2 emits strong structured constraint truth.
- Stage3 transports it, but mostly as prompt/compiler prose.
- Stage4 consumes it as context text, not as a machine-meaningful binding
  contract.

The clearest named example is `constraint_summary`:

- Stage2 emits it as a meaningful structured field.
- Stage3 compiler preserves it only as prompt text.
- Stage4 re-renders it as short advisory context lines.

Converging source findings:

- Terminal 2 `F3`
- Terminal 3 `F-1`
- Terminal 4 `F2` and `F7`

Primary owner files:

- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/arc_ensemble.py`

Queue mapping:

- `0_0-stage234-cross-stage-contract-normalization-remediation`
- partially overlaps `0_0-stage3-contract-tightening-remediation`

### F-3. Stage4 still persists split truth without autonomous reconciliation (severity: high, class: cross-stage with Stage4 local manifestation)

The new survey stack confirms that explicit provenance is better than before,
but the runtime still carries multiple surviving truth surfaces:

- `final_state_updates`
- `actual_truth`
- `world_state` and storage overlays

The system now records these boundaries clearly, but it does not yet reconcile
them into a single autonomous carryover authority for the next boundary.

Converging source findings:

- Terminal 3 `F-2`
- Terminal 4 `F3`

Primary owner files:

- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_context_builder.py`

Queue mapping:

- `0_0-stage4-consumer-contract-normalization-remediation`
- `0_0-stage234-cross-stage-contract-normalization-remediation`

### F-4. Stage3 binding scope remains too advisory for several factual categories (severity: high, class: stage-local with downstream impact)

The narrowest new clarity from this wave is not that Stage3 lacks structure.
It is that Stage3's Python validation can detect several important issue
families without escalating them into binding repair pressure.

Examples called out by the Stage3 lane:

- `dead_npc`
- `fact_lock_location`
- `fact_lock_item`
- `stop_line_violation`

These remain advisory-only unless the Director LLM independently catches and
acts on them.

Converging source findings:

- Terminal 2 `F2`
- supported by Terminal 4 `F4`

Primary owner files:

- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage3_orchestrator.py`

Queue mapping:

- primary focus of `0_0-stage3-contract-tightening-remediation`

### F-5. Stage2 mission authority is still split between a strong structured packet and prose-dominant tactical truth (severity: medium, class: stage-local -> cross-stage)

Terminal 1 shows that Stage2 does have a real structured packet:

- `episode_details`
- `state_constraints`

But the richest mission truth still lives in `tactical_doc` prose, which
downstream stages cannot strongly traverse as machine-meaningful structure.

This is not a generic "Stage2 is weak" conclusion.
It is a more precise conclusion:

- Stage2 is `content-sufficient`
- Stage2 remains `schema-fragile`
- the strongest mission authority is still too prose-dominant

Converging source findings:

- Terminal 1 `F-1`, `F-2`, `F-3`
- Terminal 4 `F6`

Primary owner files:

- `modules/domain/agents/arc_ensemble.py`
- `modules/core/response_schemas.py`
- `modules/core/stage2_contracts.py`
- `modules/core/stage2_finalizer.py`

Queue mapping:

- `0_0-stage2-contract-normalization-remediation`

### F-6. Dead or low-signal packet fields remain at the Stage2 -> Stage3 boundary (severity: medium, class: cross-stage)

The four lane docs agree that several fields still survive persistence without
surviving meaning:

- `beat_sequence`
- `hybrid_composition`
- `semantic_carryover`
- parts of `_stage3_meta`

These fields fall into two families:

- structurally persisted but downstream-dead
- structurally persisted but advisory-only and too weak to change behavior

Converging source findings:

- Terminal 1 `F-5`
- Terminal 2 `F1`, `F5`, `F6`, `F7`
- Terminal 4 `F4`, `F5`

Primary owner files:

- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_outcome_runtime.py`

Queue mapping:

- `0_0-stage2-contract-normalization-remediation`
- `0_0-stage3-contract-tightening-remediation`
- `0_0-stage234-cross-stage-contract-normalization-remediation`

## 3. Non-Issues

- Blueprint transport itself is clean. No survey found JSON corruption or
  transport-level loss at the Stage3 -> Stage4 DB handoff.
- Stage2 is not missing narrative content at the front. The problem remains
  packaging, persistence, binding strength, and boundary semantics.
- Stage4 provenance infrastructure is a positive substrate, not a new blocker.
  `state_truth_owner_contract` and fix-pack provenance are useful landed
  surfaces, even though the promotion loop remains open.
- `Stage4 Work Identity Authority` is a positive authority packet, not a loss
  point.
- No terminal produced evidence of a brand-new bounded debt family with no
  plausible home in the current queue.

## 4. Merged Owner Verdict

The narrowest owner families remain stable after merge:

- Stage2 packet / persistence family:
  - `modules/domain/agents/arc_ensemble.py`
  - `modules/core/stage2_contracts.py`
  - `modules/core/stage2_finalizer.py`
- Stage3 compiler / binding family:
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/core/stage3_orchestrator.py`
- Stage4 consumer / post-pass family:
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_post_pass_runtime.py`
  - `modules/core/stage4_interview_round.py`
- Cross-stage persistence / baseline family:
  - `modules/core/fact_ledger.py`
  - `modules/core/db_manager.py`
  - `modules/core/project_manager.py`

This owner map matches the active queue structure rather than challenging it.

## 5. Queue Mapping

| Merged Finding Group | Existing Queue Item | Coverage Verdict |
| --- | --- | --- |
| numeric carryover baseline promotion | `0_0-stage4-consumer-contract-normalization-remediation` | active front; directly covered |
| split truth and post-pass owner boundary | `0_0-stage4-consumer-contract-normalization-remediation` + `0_0-stage234-cross-stage-contract-normalization-remediation` | covered across active + parked substrate |
| Stage3 binding scope gap | `0_0-stage3-contract-tightening-remediation` | covered; still parked |
| constraint strength inversion | `0_0-stage234-cross-stage-contract-normalization-remediation` | covered; long-term shared substrate |
| Stage2 prose-dominant mission authority | `0_0-stage2-contract-normalization-remediation` | covered; residual Stage2 lane |
| dead/low-signal field cleanup | `0_0-stage2-contract-normalization-remediation` + `0_0-stage3-contract-tightening-remediation` | covered |
| reactive repair-contract synthesis | `0_0-stage4-repair-contract-normalization-remediation` | covered as Stage4 repair grammar debt |

No merged finding group remained without an execution home.

## 6. Promotion Decision

Decision: `merge-first-no-promotion`

Rationale:

- all four terminal docs independently landed on `covered-by-existing-queue`
- the cross-cut lane explicitly recommended `merge-first-no-promotion`
- the merged result sharpened owner and queue mapping, but did not create a new
  bounded topic slug
- the strongest open seam is still the existing active `Stage4 consumer`
  numeric-baseline / owner-boundary lane, not a new independent lane
- promoting a new execution SSOT here would duplicate existing queue items and
  weaken queue discipline

Therefore:

- do not create a new execution SSOT from this merge
- keep the current roadmap ordering intact
- use this merged audit as fresh evidence when the following items are next
  re-audited:
  - `0_0-stage4-consumer-contract-normalization-remediation`
  - `0_0-stage3-contract-tightening-remediation`
  - `0_0-stage2-contract-normalization-remediation`
  - `0_0-stage234-cross-stage-contract-normalization-remediation`

## 7. 3-Pass Audit Note

Pass 1. Structure and scope

- merge-only audit scope is explicit
- no canonical/temp confusion
- no execution action is claimed beyond audit and queue mapping

Pass 2. Evidence and consistency

- all four source docs exist and were read
- no material contradiction was found across findings or promotion signals
- merged findings stayed bounded to source-doc evidence and existing queue docs

Pass 3. Execution and readability

- next operational consequence is explicit: attach this merged audit as evidence
  to existing queue items when those items are next re-audited
- overreach was trimmed: no new lane promotion, no queue mutation, no patching

Estimated Confidence: `96%`
