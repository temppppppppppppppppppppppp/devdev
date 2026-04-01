# 0_0 Stage4 Canonical Entity Postselect Remediation Execution SSOT

Date: 2026-04-01
Status: partially_realized (code landed, static validation closed; runtime partial proof captured; closure denied)
Canonical Path: `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
- Baseline Dirty Summary: `dirty: canary_0_0_stage34_arc2_ep2loop_r2 runtime logs/db/artifacts active; new bounded survey docs untracked`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `new dominant blocker isolated to Stage4 split-truth seam after advisory T1-T3 landed and Arc2 canary advanced`
Source Survey Docs:
- `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-bounded-survey.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-continuation-runtime-audit.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-bounded-survey.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-audit.md`
Evidence Artifacts:
- `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-evidence.json`
- `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-evidence.json`
- `projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/state_changes.jsonl`
- `projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/ui_events.jsonl`
- `projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/episode_production.jsonl`
- `projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0004/attempt_06/final_manuscript__B.txt`
- `projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0005/attempt_01/rejected_best__C_narrative.txt`
- `projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0005/attempt_02/rejected_best__B_narrative.txt`
Side-Effect Coverage: covered
Parent Lane: `0_0-stage2-stage3-stage4-readiness-remediation` (partial)

## 1. Intent

Realize the next bounded Stage4 fix after `Stage2/3 context normalization` and `ep2 advisory T1-T3` landed.

This wave exists because current runtime evidence shows the dominant residual blocker is now a split canonical truth seam:

- `Stage3` fact-lock institution truth can remain stale (`신성증권 박성호 PB`)
- `Stage4` can locally correct the manuscript (`대한증권 강민철`)
- `post_select_conflict` can still downgrade the round using phantom pressure/state truth that is absent from the persisted final manuscript

This is not a Stage2 hierarchy wave, not a broad Stage4 redesign, and not a resume declaration.

## 2. Baseline Facts

- `ep5 Stage4 round 1` primary reject is correct: the handed-off Stage3 blueprint still carries stale institution/person truth.
- `ep5 Stage4 round 2` locally repairs the entity truth in the manuscript, but `post_select_conflict` still downgrades the round.
- The persisted final `ep4` manuscript is clean; it does not contain the intrusion event later cited by `ep5` continuity/post-select downgrade.
- `state_changes.jsonl` still persists intrusion-style `active_pressure_vectors` sourced from `stage4_post_processor`.
- `Stage4PostPassRuntime` currently derives `active_pressure_vectors` from blueprint ending fields, not from the final accepted manuscript.
- `BlueprintConstraintCompiler._build_fact_lock_packet()` currently mixes previous-manuscript and previous-blueprint institution anchors into one packet without a canonical priority rule.

## 3. Scope

Included:
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- focused supporting tests under `tests/`
- roadmap and temp-queue refresh required to insert this lane

Excluded:
- Stage4 global resume
- fresh canary execution in this turn
- Stage4 advisory policy redesign beyond already-landed T1-T3
- broad Director or TruthGate redesign
- Stage2 schema redesign
- DB schema changes

## 4. Pass 1. Inventory Summary

- post-pass pressure-vector owner:
  - `Stage4PostProcessor._build_active_pressure_vectors()`
  - `Stage4PostPassRuntime._apply_state_text_and_pressure_vectors()`
- Stage3 fact-lock owner:
  - `BlueprintConstraintCompiler._build_fact_lock_packet()`
- downstream consumer path:
  - `Stage4ContextPackets.build_condensed_world_state_summary()`
  - `stage4_interview_round._execute_round_post_select_validation()`

Main hotspots for this wave:

1. blueprint ending-hook truth is being promoted into canonical post-pass state without final-manuscript alignment
2. previous blueprint institution anchors can compete with accepted previous-manuscript institution truth
3. Stage4 post-select continuity/history checks consume `story_context` that still includes the misaligned pressure vectors

## 5. Pass 2. Semantic Classification

- Class A. Primary realization now
  - post-pass `active_pressure_vectors` must align to final accepted manuscript truth
  - Stage3 fact-lock institution anchor building must become manuscript-first when sources conflict

- Class B. Residual but deferred inside this lane
  - broader post-select observability beyond already-landed T1-T3
  - entity/person canonicalization beyond institution-source priority

- Class C. Explicitly deferred outside this lane
  - Stage4 retry architecture redesign
  - Stage4 global resume
  - Stage2/3 broader vocabulary/contract normalization

## 6. Side-Effect Map

- file writes / artifacts:
  - future Stage4 post-pass canonical artifacts may no longer persist phantom pressure vectors
  - future Stage3 fact-lock packets may emit fewer stale institution anchors

- DB / schema / transaction boundaries:
  - no schema change
  - same state/bible sinks remain in use

- JSONL / log / audit sinks:
  - no new sink schema required
  - state log content may change because phantom pressure vectors are filtered

- console / UI / operator output:
  - indirect only; fewer downstream continuity/post-select conflicts expected

- rollback / recovery / retry:
  - post-select downgrade rate should fall if phantom pressure vectors are removed
  - Stage3 retry churn from stale institution drift should fall if fact-lock packet converges earlier

- cache / global state:
  - canonical world-state pressure vectors may differ for newly generated runs

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

This wave stays deliberately small and attacks one split-truth boundary on each side of the Stage3/4 handoff.

### Tranche 1. Post-Pass Pressure Vector Alignment

Goal:

- stop persisting blueprint-only ending-hook pressure that is not reflected in the final accepted manuscript

Realization:

- add a bounded manuscript-alignment filter in the Stage4 post-pass path
- `active_pressure_vectors` may still be built from blueprint ending fields, but only vectors corroborated by the final manuscript should survive into canonical state/bible payloads
- corroboration should be lightweight and deterministic:
  - use vector text and extracted cue terms
  - require evidence in the accepted manuscript before persisting

Why first:

- this is the shortest path to eliminate the phantom `ep4 intrusion` truth that polluted `ep5 post_select_conflict`

### Tranche 2. Fact-Lock Institution Canonical Source Priority

Goal:

- prevent stale previous-blueprint institution anchors from outranking cleaner accepted previous-manuscript truth

Realization:

- in `BlueprintConstraintCompiler._build_fact_lock_packet()`, separate institution anchors by source
- when the previous manuscript yields institution names, treat that set as canonical and do not append conflicting blueprint-only institution names into the same packet
- preserve non-institution anchors from blueprint as before

Why second:

- this narrows the Stage3 handoff drift that caused `ep5 round 1` primary reject

### Tranche 3. Focused Regression Closure

Goal:

- close the two seams with targeted tests and verification only

Realization:

- extend post-pass tests to prove phantom pressure vectors are dropped when absent from final manuscript and retained when corroborated
- extend fact-lock tests to prove manuscript-first institution priority suppresses conflicting blueprint institution anchors

## 8. Execution Tranches

1. `Tranche 1` post-pass pressure-vector alignment in `stage4_post_processor.py` / `stage4_post_pass_runtime.py`
2. `Tranche 2` fact-lock institution canonical priority in `blueprint_constraint_compiler.py`
3. `Tranche 3` focused regression tests and queue/doc refresh

## 9. Acceptance Criteria

- `active_pressure_vectors` are not persisted when their cue terms/text are absent from the final accepted manuscript
- corroborated pressure vectors still persist normally
- a stale previous-blueprint institution does not enter `fact_lock_packet` when the accepted previous manuscript already provides a different institution name
- non-institution fact-lock anchors are preserved
- no new `180+ LOC` function is introduced
- existing Stage4 advisory T1-T3 behavior remains intact
- roadmap and temp queue reflect this lane as the next active dependency for the parent lane

## 10. Verification Plan

- `pytest tests/test_stage4_post_processor.py -q`
- `pytest tests/test_stage23_stage4_readiness_wave1.py -q`
- `pytest tests/test_stage3_blueprint_state_precision_guardrail.py -q`
- `python -m py_compile modules/core/stage4_post_processor.py modules/core/stage4_post_pass_runtime.py modules/domain/agents/blueprint_constraint_compiler.py`
- `ruff check modules/core/stage4_post_processor.py modules/core/stage4_post_pass_runtime.py modules/domain/agents/blueprint_constraint_compiler.py tests/test_stage4_post_processor.py tests/test_stage23_stage4_readiness_wave1.py tests/test_stage3_blueprint_state_precision_guardrail.py`
- `python scripts/check_utf8_hygiene.py docs/2026-04-01/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md docs/temp/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md docs/2026-04-01/active-temp-execution-roadmap.md docs/temp/execution-roadmap.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- keep `Stage4 paused`
- do not run a new canary in this turn
- do not widen this into a broad Stage4 or Stage3 redesign
- do not mutate source project `0_0`
- do not change DB schema
- preserve Director final authority; this wave only narrows canonical input/state truth before the Director/post-select path consumes it

## 12. Temp Queue Notes

- temp status: `in_progress`
- cleanup condition:
  - remove temp mirror only after code lands, focused validation passes, and a later closure audit completes
- roadmap dependency:
  - this lane becomes the direct prerequisite for advancing `0_0-stage2-stage3-stage4-readiness-remediation` beyond `partial`

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope

- kept the lane bounded to two concrete truth-alignment seams
- excluded canary execution, Stage4 resume, and broad redesign
- canonical/temp paths and queue implications are explicit

### Pass 2. Evidence and Consistency

- all baseline claims tie back to the bounded survey and canary artifacts
- the split-truth explanation is triangulated across final manuscript artifact, state log payload, and code anchors
- parent-lane dependency is consistent with the current roadmap state

### Pass 3. Execution and Readability

- tranches are ordered by direct runtime leverage
- acceptance criteria and verification are executable
- non-goals and guardrails keep this from inflating into another broad Stage4 wave

Confidence: `96%`

## 15. Static Validation Update

Realization completed in this turn:

- `stage4_post_processor.py`
  - added manuscript-alignment filtering for post-pass `active_pressure_vectors`
- `stage4_post_pass_runtime.py`
  - routed post-pass vectors through the new manuscript-alignment filter before persistence
- `blueprint_constraint_compiler.py`
  - made institution anchors manuscript-first when previous manuscript truth conflicts with stale blueprint institution hints

Focused validation completed:

- `python -m py_compile modules/core/stage4_post_processor.py modules/core/stage4_post_pass_runtime.py modules/domain/agents/blueprint_constraint_compiler.py tests/test_stage4_post_processor.py tests/test_stage3_npc_capital_carryforward_guardrail.py`
- `ruff check modules/core/stage4_post_processor.py modules/core/stage4_post_pass_runtime.py modules/domain/agents/blueprint_constraint_compiler.py tests/test_stage4_post_processor.py tests/test_stage3_npc_capital_carryforward_guardrail.py`
- `pytest tests/test_stage4_post_processor.py -q`
- `pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q`
- `pytest tests/test_stage23_stage4_readiness_wave1.py -q`

Operational conclusion:

- keep `Stage4 paused`
- runtime closure proof no longer deferred; partial proof captured and closure denied
- next follow-up for this lane is a narrower Stage4 finalization seam (`fix_pack target generation + post_select proper-noun/timeline continuity`), not more broad patching

## 16. Runtime Closure Update (2026-04-02)

Canary used:

- `projects/canary_0_0_stage34_arc2_entitypost_r1`

Runtime audit:

- `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-audit.md`
- `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-evidence.json`

Post-run merge result:

- this lane produced **partial positive runtime signal**
- `Stage3 ep5-9` all passed in the canary
- `Stage4 ep2` now reaches `PASS` and the old Flashback false-positive loop does not reappear
- the run advanced beyond the prior `ep2` blocker into `ep3` and `ep4`

But closure is denied because:

- `stage34_canary_summary.json` ends with `multi_stage_proof_scope_summary.status = fail`
- `stage4 current_session_sink_alignment_summary.status = warn`
- `stage4 final_authority_contract.status = missing`
- the dominant residual blockers moved to:
  - `ep3 strong_advisory_escalation_non_local_fix` with empty `patch_targets`
  - `ep4 post_select_conflict` around proper nouns and timeline continuity

Operational consequence:

- keep this lane at `partially_realized`
- keep `Stage4 paused`
- do not advance the parent readiness lane beyond `partial`
- next bounded follow-up should target `Stage4` finalization/fix-pack and final-round continuity, not reopen Stage2/3 hierarchy work
