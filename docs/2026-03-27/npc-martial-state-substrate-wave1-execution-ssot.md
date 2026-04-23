# NPC Martial State Substrate Wave1 Execution SSOT

Date: 2026-03-27
Status: closed historical backing (2026-04-23 live compaction re-audit; the wave1 storage substrate is now code-visible and test-backed across schema, Stage2 preservation, Stage4 world-only bridging, WorldState replay, and rollback, so the old blocked queue item is preserved as landed history)
Canonical Path: `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`
Commit State:
- Baseline Commit: `161b71348732e06d9542daf3f54ad8a65126eada`
- Baseline Dirty Summary: `dirty: untracked docs only (npc-technique-realm-persistence-compact-survey.md, npc-technique-realm-owner-model-design-memo.md, npc-technique-realm-execution-readiness-deep-dive-audit.md)`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `reopened after authority reconciliation; same-day closure was premature because persisted runtime authority flows through Stage 4 bible_delta["state_changes"], not tracker extractors; later parked on 2026-03-28 after Director reorder because no live Stage 4 / STV seam diff remained`
Source Survey Docs:
- `docs/2026-03-27/npc-technique-realm-persistence-compact-survey.md`
- `docs/2026-03-27/npc-technique-realm-owner-model-design-memo.md`
- `docs/2026-03-27/npc-technique-realm-execution-readiness-deep-dive-audit.md`
- `docs/2026-04-19/npc-martial-state-substrate-wave1-reactivation-refresh.md`
Evidence Artifacts:
- none
Side-Effect Coverage: covered

## 1. Intent

Realize the smallest viable owner substrate for NPC martial current state.

Why now:

- the deep-dive audit concluded broad NPC martial authority work is still `no-go`
- the same audit concluded a strictly storage-only substrate wave is `conditional go`
- this document exists to realize only that bounded substrate and nothing larger

## 2. Baseline Facts

- protagonist martial authority is already settled enough
- NPC technique / realm still has no persisted owner
- a new state-change family must survive the full canonical path, not just `arc.py`
- replay-authoritative truth still comes from `episode_bibles.state_changes`
- persisted write authority in wave 1 is the Stage 4 manager-delta -> `bible_delta["state_changes"]` path
- the tightest semantic edge is the delta threshold: only explicit, high-confidence NPC martial changes should be recorded

## 3. Scope

Included:
- `modules/models/arc.py`
- `modules/core/response_schemas.py`
- `modules/domain/agents/analyst.py`
- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/world_state.py`
- bounded tests for the touched substrate

Excluded:
- `modules/core/fact_ledger.py`
- `modules/core/stage4_context_builder.py`
- `modules/validation/blocking_validator_consistency_checks.py`
- `modules/core/truth_gate.py`
- `modules/core/semantic_query_broker.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- Stage 4 canonical injection changes
- validator / truth-gate activation
- reveal ledger or chronology
- new DB tables or new top-level Bible fields

## 4. Pass 1. Inventory Summary

- producer contract surfaces: `arc.py`, `response_schemas.py`, `analyst.py`, `state_tracker.py`, `state_tracker_npc.py`
- persistence fan-out surface: `stage4_post_pass_runtime.py`
- realized current-state owner surface: `world_state.py`
- replay / rollback path: existing `episode_bibles.state_changes` replay into `WorldState`
- currently inert consumer surfaces: `truth_gate.py`, `semantic_query_broker.py`, `npc_drift_advisor.py`, `chief_writer_context_packets.py`

## 5. Pass 2. Semantic Classification

- Class A. Mandatory substrate seams
  - `StateChangesDict` contract
  - LLM-facing `state_changes` schema
  - analyst default/normalization path
  - NPC extractor path
  - Stage 4 post-pass persistence fan-out
  - `WorldState.alive_npcs[name]["martial_state"]`

- Class B. Required semantic guardrails
  - explicit realm advancement only
  - explicit learned/mastered/attained technique deltas only
  - no speculative regex-only combat-prose mining as canonical truth

- Class C. Explicitly deferred consumers
  - Stage 4 canonical prompt injection
  - validator enforcement
  - chronology / reveal / usage history
  - `FactLedger` martial modeling

## 6. Side-Effect Map

- file writes / artifacts:
  - canonical docs under `docs/2026-03-27/`
  - temp mirror under `docs/temp/`
  - no new non-doc artifact planned at SSOT-open stage

- DB / schema / transaction boundaries:
  - no new DB tables
  - no top-level Bible schema expansion
  - payload must stay nested under canonical `state_changes`

- JSONL / log / audit sinks:
  - no special new sink in wave scope
  - touched runtime may log through existing Stage 4 / world-state paths only

- console / UI / operator output:
  - no intended operator-facing behavior change

- rollback / recovery / retry:
  - payload must remain replay-authoritative through `episode_bibles.state_changes`
  - rollback correctness is part of acceptance

- cache / global state:
  - `WorldState` current-state mutation only
  - no new global registry

- bootstrap fallback / config-env mutation:
  - not-applicable

## 7. Realization Architecture

Canonical path for the new family must be:

1. upstream schema can represent `npc_martial_state_changes`
2. analyst preserves/defaults the family without dropping it
3. manager-delta `actual_truth` / `final_state_updates` remains the persisted source payload under canonical `state_changes`
4. `stage4_post_pass_runtime.py` preserves that payload inside `bible_delta["state_changes"]`
5. `StateTrackerNPC` and `StateTracker.extract_all_state_changes()` may normalize explicit-only NPC martial deltas for tracker-side consumers, but are not the replay-authoritative writer in wave 1
6. `WorldState.update_from_state_changes()` realizes current NPC martial state into `alive_npcs[name]["martial_state"]`
7. rollback replay reconstructs the same current-state result

Target shape:

- new family: `npc_martial_state_changes`
- per-entry scope:
  - `name`
  - `episode`
  - optional `realm`
  - optional `techniques_learned`

Replay semantics:

- `realm`: last-write-wins
- `techniques_learned`: additive union
- absent field: no-op

## 8. Execution Tranches

1. Contract substrate
   - extend `StateChangesDict`
   - expose the family in `response_schemas.py`
   - preserve/default the family in `analyst.py`

2. Tracker helper + persistence
   - add bounded NPC explicit-only normalization support in `state_tracker_npc.py`
   - expose the helper through `state_tracker.py`
   - preserve payload in `stage4_post_pass_runtime.py`
   - realize owner state in `world_state.py`

3. Verification
   - replay / rollback-safe tests
   - no activation of Stage 4 consumers or validators
   - bounded wuxia smoke/probe only if needed after unit-level verification

## 9. Acceptance Criteria

- `npc_martial_state_changes` exists as a canonical `StateChangesDict` family
- the family is representable by upstream response schema and is not dropped by analyst normalization
- runtime persisted authority remains nested under canonical `episode_bibles.state_changes`
- only explicit high-confidence NPC realm / technique deltas are emitted
- payload survives into canonical `episode_bibles.state_changes`
- `WorldState` persists `alive_npcs[name]["martial_state"]`
- rollback / replay reconstructs the same NPC martial current state
- no new DB tables or top-level Bible fields are introduced
- `FactLedger`, Stage 4 injection, validator, and chronology behavior remain untouched

## 10. Verification Plan

- `python -m py_compile modules/models/arc.py modules/core/response_schemas.py modules/domain/agents/analyst.py modules/domain/agents/state_tracker.py modules/domain/agents/state_tracker_npc.py modules/core/stage4_post_pass_runtime.py modules/core/world_state.py`
- `pytest tests/test_state_tracker.py -q`
- `pytest tests/test_state_tracker_npc_sweep20.py -q`
- `pytest tests/test_world_state_manager.py -q`
- `pytest tests/test_truth_gate.py -q`
- add or update bounded tests for:
  - `npc_martial_state_changes` canonical emission
  - Stage 4 post-pass pass-through into `bible_delta["state_changes"]`
  - `WorldState` replay / rollback reconstruction
- optional bounded wuxia smoke/probe only after unit-level verification is clean
- `python scripts/check_utf8_hygiene.py <touched files>`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- storage-only wave only
- no Stage 4 canonical injection
- no validator / truth-gate activation
- no `FactLedger` martial modeling
- no reveal ledger, usage history, or chronology
- no new DB tables
- no top-level Bible siblings; keep payload under canonical `state_changes`
- delta threshold must remain strict: explicit advancement / explicit learned-mastered only
- if implementation pressure expands into consumer activation or DB redesign, stop and re-scope instead of widening silently

## 12. Temp Queue Notes

- temp status: blocked
- cleanup condition: remove temp mirror after implementation, closure audit, queue-state refresh, and validator clean pass
- roadmap dependency:
  - governed by `docs/2026-03-27/npc-martial-and-soak-canary-execution-roadmap.md`

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run this document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1. Scope Discipline
- kept the wave on substrate only
- re-confirmed excluded consumers and DB expansion paths
- PASS

Pass 2. Contract Completeness
- included the real canonical path, including `response_schemas.py`, `analyst.py`, and `stage4_post_pass_runtime.py`
- ensured replay-authoritative `state_changes` persistence is explicit
- PASS

Pass 3. Execution Readiness
- translated deep-dive findings into bounded tranches, acceptance, and guardrails
- confidence remains above threshold if scope stays storage-only
- PASS

Estimated confidence: 96%

---

- Readiness verdict: `execution-ready only for storage substrate scope`
- Scope-expansion verdict: `stop and re-scope`

## 15. Reopen Note

Reopen Status: `partially_realized`
Reopen Date: 2026-03-27

Why reopened:

- same-day closure was premature
- runtime authority reconciliation showed the replay-authoritative write path is `stage4_post_pass_runtime.py -> bible_delta["state_changes"]`, not `StateTracker.extract_all_state_changes()`
- unrelated tracker regex fallback edits that were introduced during UTF-8 hygiene cleanup were reverted as scope leak

Current realization state:

- contract substrate landed in `arc.py`, `response_schemas.py`, and `analyst.py`
- runtime storage path landed in `stage4_post_pass_runtime.py` and `world_state.py`
- tracker-side normalization helper landed in `state_tracker.py` and `state_tracker_npc.py`, but it is not the persisted writer in wave 1

Remaining follow-up before closure:

- keep the queue open until the reopened SSOT, temp mirror, and queue-state reflect the corrected authority model
- defer Stage 4 injection, validator activation, `FactLedger` martial modeling, chronology/reveal ledger, and any DB expansion to later waves

## 16. Re-Audit 2026-03-27

Pass 1. Structure and Scope

- canonical doc, temp mirror, and queue-state are back in sync for an active single-item queue
- scope remains storage-only and still excludes Stage 4 injection, validator, `FactLedger`, chronology/reveal ledger, and DB expansion
- PASS

Pass 2. Evidence and Consistency

- persisted replay authority is now explicitly aligned with live code: `stage4_post_pass_runtime.py -> bible_delta["state_changes"] -> episode_bibles.state_changes`
- tracker extractor additions are now documented as bounded normalization helpers, not the replay-authoritative writer
- unrelated tracker regex fallback edits introduced during hygiene cleanup were removed; the remaining code diff is back inside martial-wave scope
- targeted verification passed:
  - `python -m py_compile modules/models/arc.py modules/domain/agents/state_tracker.py modules/domain/agents/state_tracker_npc.py modules/core/stage4_post_pass_runtime.py modules/core/world_state.py`
  - `pytest tests/test_llm_schema.py -q`
  - `pytest tests/test_pydantic_models.py -q`
  - `pytest tests/test_stage2_pipeline.py -q`
  - `pytest tests/test_state_tracker.py -q`
  - `pytest tests/test_state_tracker_npc_sweep20.py -q`
  - `pytest tests/test_stage4_post_processor.py -q`
  - `pytest tests/test_world_state_manager.py -q`
  - `pytest tests/test_rollback_npc.py -q`
  - `python scripts/sync_temp_queue_state.py`
  - `python scripts/ops_validator.py --strict`
- PASS

Pass 3. Closure Readiness

- clean closure without exception is still not allowed in this turn
- full touched-file `python scripts/check_utf8_hygiene.py ...` still fails on pre-existing legacy regex/question-token patterns in `state_tracker.py` and `state_tracker_npc.py`
- bounded exception `EXC-20260327-npc-martial-wave1-utf8-hygiene` now governs this inherited false-positive surface
- PASS for closure with explicit exception governance

Re-Audit Confidence: 95%

Current operating verdict:

- realization state: `closed`
- closure state: `eligible via bounded exception`

## 17. Closure Note

Closure Status: `closed`
Closure Date: 2026-03-27

Realized scope:

- contract substrate landed in `arc.py`, `response_schemas.py`, and `analyst.py`
- runtime storage path landed in `stage4_post_pass_runtime.py` and `world_state.py`
- tracker-side explicit-only normalization helper landed in `state_tracker.py` and `state_tracker_npc.py`
- storage-only scope held; Stage 4 injection, validator activation, `FactLedger`, chronology/reveal ledger, and DB expansion were not included

Verification summary:

- targeted compile/test validation passed for schema, analyst, tracker helper, Stage 4 pass-through, world-state owner persistence, and rollback replay
- `python scripts/ops_validator.py --strict` passed with the mirror present before cleanup
- inherited tracker regex false positives on `check_utf8_hygiene.py` are explicitly governed by `docs/2026-03-27/npc-martial-state-substrate-wave1-utf8-hygiene-exception.md`

Residual risks:

- active bounded exception remains for tracker regex `suspicious_question_token` false positives
- deferred later-wave scope remains unchanged: Stage 4 injection, validator activation, `FactLedger`, chronology/reveal ledger, DB/table expansion

Temp cleanup:

- execution SSOT mirror removed: yes
- queue-state refreshed to empty: yes

## 18. Hotfix Reopen 2026-03-27

Reopen Status: `active`
Reopen Reason: `bounded martial_arts shape-normalization hotfix required before additional wuxia canaries`

Why reopened again:

- a fresh wuxia canary no longer crashes with `TypeError: unhashable type: 'dict'`
- the same canary plus targeted runtime-shape tracing found a new bounded defect: `manager.update_state_and_lore_v20` returns `actual_truth.martial_arts` as `list[dict]` while the intended contract remains string-list oriented
- current Stage 4 normalization only protects diff computation and does not normalize the persisted `actual_truth` payload before `StateTextVerifier`, `episode_bibles`, or `state_logs`
- BI/TR contamination was ruled out by read-only scans of `bible/09_bi_wuxia_heavenly_physician.json` and `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json`

Out of scope remains unchanged:

- no Stage 4 injection activation
- no validator activation
- no `FactLedger` martial modeling
- no chronology / reveal ledger
- no DB/table expansion
- no broad wuxia schema redesign

## 19. Hotfix Micro-Survey 2026-03-27

Evidence summary:

- producer drift:
  - `modules/domain/agents/manager.py` still prompts `actual_truth.martial_arts` as `[]`
  - fresh wuxia canary evidence showed raw manager output carrying `list[dict]` entries such as `{name, origin, block_acquired, evolution}`
- current normalization boundary:
  - `modules/core/stage4_post_pass_runtime.py` normalizes `martial_arts` through `_normalize_martial_arts_snapshot()`
  - that helper is currently used only inside `_collect_manager_and_build_delta()` diff computation
- persistence gap:
  - `_prepare_manager_delta_context()` normalizes `inventory_counts` but leaves `actual_truth["martial_arts"]` untouched
  - `_persist_manager_delta_outputs()` writes `actual_truth` into `bible_delta["state_changes"]`
  - `_persist_manager_state_log()` writes the same raw `actual_truth` into `state_logs`
  - `DBManager.save_state_log_with_summary()` serializes the payload without shape correction
- STV gap:
  - `StateTextVerifier.verify()` and `apply_corrections()` receive the raw `actual_truth` shape and do not normalize `martial_arts`

Operating conclusion:

- culprit family: `manager raw martial_arts producer drift + missing pre-persistence normalization boundary`
- required boundary: normalize `actual_truth["martial_arts"]` once, before STV and before any persistence sink reuses the payload

## 20. Hotfix Tranche

Bounded write scope:

- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/state_text_verifier.py` only if needed for shape-stable tests or defensive handling
- bounded tests covering Stage 4 persistence and STV-adjacent shape stability

Hotfix requirements:

1. normalize raw `actual_truth["martial_arts"]` immediately after manager output is accepted into the Stage 4 post-pass runtime
2. ensure the normalized value is the same value consumed by:
   - `StateTextVerifier`
   - `episode_bibles.state_changes`
   - `state_logs.data.actual_truth`
3. keep normalization narrow:
   - string entries stay as-is after trim / de-duplication
   - dict entries collapse to a stable technique label via existing bounded key priority (`name`, `technique`, `main_technique`, `title`)
   - unknown dicts become no-op, not persisted junk
4. do not widen into NPC martial consumer activation or broader manager schema redesign in this wave

Acceptance for the hotfix tranche:

- producer drift no longer causes mixed persistence shapes for `actual_truth.martial_arts`
- `state_logs` and `episode_bibles.state_changes` persist the normalized `list[str]` shape
- STV sees the normalized `list[str]` shape
- existing wuxia canary no longer shows `TypeError: unhashable type: 'dict'`
- after the hotfix lands, rerun the same wuxia canary once before attempting a second NPC-martial canary

## 21. Hotfix 3-Pass Addendum Audit

Pass 1. Scope Discipline

- bounded the reopen to pre-persistence `martial_arts` normalization only
- kept the wave inside the already-touched Stage 4 / STV seam
- PASS

Pass 2. Evidence Consistency

- aligned fresh canary evidence, runtime-shape tracing, and code inspection
- ruled out BI/TR contamination as the active cause
- PASS

Pass 3. Execution Readiness

- hotfix boundary is concrete and testable
- queue should be reopened as a single active execution item before patching
- PASS

Hotfix addendum confidence: 96%

## 22. Queue Reconciliation 2026-03-28

Reconciliation Verdict: `blocked`

Why blocked now:

- the declared hotfix seam remains the bounded Stage 4 / STV pre-persistence normalization path
- live `git status --short` does not touch that seam
- current dirty work is instead in provider, benchmark, TR-harness, config, and governance lanes
- leaving this item marked `active` would overstate live execution reality

Authority consequences:

- this item remains in the queue but is no longer treated as an actively advancing implementation lane
- do not treat unrelated dirty files as progress on this SSOT
- do not promote the next queue item by implication; use an explicit refreshed roadmap decision

Resume conditions:

- a fresh bounded diff appears on the declared Stage 4 / STV seam, or
- the item is formally closed or reordered by queue authority

Queue reconciliation 3-pass:

- Pass 1. Scope Discipline
  - kept the reconciliation bounded to queue authority and live-seam status only
  - PASS
- Pass 2. Evidence Consistency
  - confirmed the live dirty tree does not overlap the declared hotfix write scope
  - confirmed queue-state drift had overstated progress
  - PASS
- Pass 3. Execution Readability
  - active vs blocked state is now explicit for operators
  - the next decision boundary is clear: resume on seam or close/reorder
  - PASS

Queue reconciliation confidence: `97%`

## 23. Director Reorder 2026-03-28

Reorder Verdict: `blocked off active lane`

Why no longer the active blocker:

- live `git status --short` still shows no bounded diff on the declared Stage 4 / STV hotfix seam
- live process inspection showed no active wuxia canary `python` process whose continuity required holding the queue here
- keeping this item as a parked blocked follow-up preserves the hotfix context without forcing the active soak lane to stall

Authority consequences:

- `frontier-lag-soak-canary-wave1` is promoted ahead of this item in the aggregate roadmap
- do not treat unrelated provider, benchmark, TR-harness, governance, or future canary chatter as progress on this SSOT
- any future return to this item requires a fresh bounded diff on the declared seam or fresh survey evidence justifying reopen

Director reorder 3-pass:

- Pass 1. Structure and Scope
  - bounded this refresh to queue position and blocker truth only
  - PASS
- Pass 2. Evidence Consistency
  - confirmed the declared hotfix seam is still absent from the live dirty tree
  - confirmed no active wuxia canary process remains in the workspace at decision time
  - PASS
- Pass 3. Execution Readability
  - the item stays preserved as context, but no longer pretends to own the active lane
  - future resumption conditions are explicit for the next operator
  - PASS

Director reorder confidence: `97%`

## 24. 2026-04-19 Reactivation Refresh

Source doc:

- `docs/2026-04-19/npc-martial-state-substrate-wave1-reactivation-refresh.md`

Current reading:

- the partially landed storage substrate is still real
- the remaining Stage 4 / STV seam follow-up is still real in principle
- but there is still no fresh bounded seam diff or fresh survey evidence to justify reopen

Queue consequence:

- keep this lane visible
- keep the temp mirror
- preserve it as blocked holding rather than promoting or closing it
