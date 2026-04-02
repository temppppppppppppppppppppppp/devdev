# 0_0 Stage4 Consumer-Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: partially_realized (aggregate Stage4 wave active; child NpcDrift relation-tag lane code-landed, runtime proof pending)
Canonical Path: `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
- Baseline Dirty Summary: `dirty: active Stage4 docs/code/test deltas, prepared canary targets, temp roadmap/queue active`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `NpcDrift relation-tag child lane code-landed; aggregate Stage4 consumer-contract runtime proof still pending`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-post-select-continuity-seam-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-bounded-survey.md`
- `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-bounded-survey.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-bounded-survey.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-evidence.json`
- `docs/2026-04-02/0_0-stage4-post-select-continuity-seam-evidence.json`
- `docs/2026-04-02/0_0-stage4-fixpack-finalization-evidence.json`
- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-local-fix-evidence.json`
- `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-evidence.json`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-evidence.json`
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
- `NpcDrift relation-tag` survey isolated the next live ep2 blocker but is not yet realized
- The remaining issue is no longer “add one more local fix.” It is “normalize how Stage4 consumes, reclassifies, and persists truth.”

## 3. Scope

Included:

- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/domain/agents/chief_writer_context.py`
- focused Stage4 contract regressions and queue/doc refresh

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

## 5. Pass 2. Semantic Classification

### Class A. Primary realization now

- NpcDrift relation-tag semantic/local-fix normalization
- post-select bounded-repair contract normalization
- fix-pack provenance and routing normalization
- post-pass state-truth owner boundary normalization

### Class B. Residual but related

- intake tier0 protection against prose-budget flattening
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

### Tranche 4. Focused Regression Closure

Goal:

- add only the regressions needed to lock the contracts above

## 9. Acceptance Criteria

- Stage4 bounded contradiction types preserve enough subtype detail to support local repair where appropriate
- fix-pack provenance is explicit enough that runtime-synthesized contracts are not indistinguishable from Director-authored contracts
- `final_state_updates`, `actual_truth`, and `world_state` have a clearer owner/provenance boundary for high-risk field families
- new Stage4 behavior stays bounded and does not reopen Stage2/3 hierarchy work
- no new `180+ LOC` function is introduced

## 10. Verification Plan

- targeted Stage4 interview/finalization regressions
- targeted post-pass/state provenance regressions
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

## 12. Temp Queue Notes

- temp status: `partial`
- cleanup condition:
  - keep the temp mirror as the new aggregate Stage4 contract-normalization lane until explicit realization or replacement
- roadmap dependency:
  - this lane becomes the new highest-level Stage4 contract wave
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

Pass 3, execution and readability:

- made substrate relationships explicit
- separated bounded tranches by consumer contract family
- kept canary and resume actions out of scope

Confidence: `96%`
