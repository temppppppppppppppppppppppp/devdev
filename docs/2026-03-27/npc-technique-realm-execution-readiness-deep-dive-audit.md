# NPC Technique-Realm Execution Readiness Deep-Dive Audit

Date: 2026-03-27
Status: final (survey-only, no code changes)
Type: system-track deep-dive readiness audit
Canonical Path: `docs/2026-03-27/npc-technique-realm-execution-readiness-deep-dive-audit.md`
Temp Mirror Path: none
Inputs:
- `docs/2026-03-27/npc-technique-realm-persistence-compact-survey.md`
- `docs/2026-03-27/npc-technique-realm-owner-model-design-memo.md`
Evidence Basis:
- `modules/models/arc.py`
- `modules/core/response_schemas.py`
- `modules/domain/agents/analyst.py`
- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/stage4_context_builder.py`
- `modules/validation/blocking_validator_consistency_checks.py`
- `modules/core/truth_gate.py`
- `modules/core/semantic_query_broker.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/core/npc_drift_advisor.py`
- `modules/core/project_manager.py`
- `modules/core/services/project_service.py`
- `config/genres/wuxia.yaml`
Commit State:
- Baseline Commit: `161b71348732e06d9542daf3f54ad8a65126eada`
- Baseline Dirty Summary: `untracked survey/design docs only: npc-technique-realm-persistence-compact-survey.md, npc-technique-realm-owner-model-design-memo.md`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none observed during audit`
Side-Effect Coverage:
- file write: included
- replay / rollback: included
- Stage 4 prompt injection: included
- validator / truth surfaces: included
- DB / ledger persistence: included
- live runtime execution: not run in this audit

## 1. Executive Judgment

Bottom line:

- broad execution wave now: **no-go**
- narrowly bounded substrate-only wave: **conditional go**
- recommended next move if promoted: `one small execution SSOT`, but only after three gates are written explicitly into scope

The main reason is simple. This seam is no longer blocked by "unknown unknowns." It is blocked by a small number of very specific contract decisions:

1. who canonically emits NPC martial deltas
2. what counts as a high-confidence NPC martial delta
3. whether the first wave is storage-only or also activates Stage 4 / validator consumers
4. whether the payload survives the Stage 4 post-pass fan-out into replay-authoritative `episode_bibles.state_changes`

Live code inspection says the right first wave is still narrow:

- extend `StateChangesDict`
- extend upstream `state_changes` schema/defaulting surfaces
- emit high-confidence NPC martial deltas
- preserve the payload through Stage 4 post-pass into `bible_delta["state_changes"]`
- persist them into `WorldState.alive_npcs[name]["martial_state"]`
- stop there

If the wave widens past that into chronology, reveal ledger, Stage 4 injection, or validator enforcement, readiness drops back to **no-go**.

## 2. What Is Already Settled

The protagonist slice is no longer the blocker.

Live evidence shows:

- `StateTracker.extract_all_state_changes()` already owns protagonist-oriented `skill_acquisitions`
- `StateTrackerNPC.extract_skill_acquisitions_from_arc()` still only feeds protagonist skill acquisition
- `WorldState._apply_actor_and_inventory_state_changes()` applies `skill_acquisitions` only to `self._state["protagonist"]["skills"]`
- `stage4_context_builder.py` already injects a wuxia-only protagonist technique / realm authority clause
- `blocking_validator_consistency_checks.py` already runs a protagonist-only technique-vs-realm check using `martial_hud.actual_truth.realm` or `context["protagonist_realm"]`

Conclusion:

- protagonist martial authority is settled enough for this decision
- the remaining seam is specifically `NPC technique / realm current-state ownership`

## 3. What Is Missing Today

Live evidence shows there is still no persistent owner for NPC martial state.

Current absence:

- `StateChangesDict` has no `npc_martial_state_changes`
- `response_schemas.py` does not expose such a family in the LLM-facing `state_changes` schema
- `analyst.py` does not guarantee or normalize such a family in post-processing defaults
- `StateTracker.extract_all_state_changes()` does not emit any NPC martial payload
- `StateTrackerNPC` has no extractor for NPC realm advancement or NPC technique mastery persistence
- `WorldState` has no dedicated `alive_npcs[name]["martial_state"]` owner slot
- `get_known_skills()` remains protagonist-only
- `get_npc_role_snapshot()` surfaces `role_at_intro`, `first_seen_ep`, and `known_attrs`, but no martial owner

Conclusion:

- prompt text and validator rules cannot be made authoritative yet
- the missing problem is not "better advice"
- the missing problem is "no persisted owner exists"

## 4. The Real Blast Radius

The initial design memo was directionally correct, but this audit narrows the real write set more precisely.

Any first real wave would minimally touch:

- `modules/models/arc.py`
- `modules/core/response_schemas.py`
- `modules/domain/agents/analyst.py`
- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/world_state.py`
- bounded tests around those surfaces

Why this matters:

- adding a new `state_changes` family is not only a `TypedDict` change
- upstream LLM schema and analyst defaulting are part of the canonical producer contract
- raw `arc["state_changes"]` alone is not enough, because `StateTracker.extract_all_state_changes()` reconstructs the canonical state-change payload
- even that is not enough by itself, because Stage 4 post-pass is the real persistence fan-out into `episode_bibles.state_changes`

This is the most important readiness fact in the whole audit.

## 5. Replay And Rollback Are Not The Primary Blocker

Replay looks tractable if the design stays narrow.

Live evidence:

- `stage4_post_pass_runtime.py` rewrites arc outputs into `bible_delta["state_changes"]`, `state_logs`, `world_state_changes`, and `fact_ledger_changes`
- `WorldState.rollback_to()` resets to init state and replays `episode_bibles[*].state_changes`
- `FactLedger.rollback_to()` also rebuilds by replaying `state_changes`
- `project_manager.py` and `project_service.py` already route rollback through these replay paths

Implication:

- if `npc_martial_state_changes` never survives the Stage 4 post-pass fan-out, replay will never see it
- a storage-only `npc_martial_state_changes` family replayed into `WorldState` is conceptually compatible with the current replay model
- replay becomes expensive only if the wave also introduces chronology, reveal ledger, or a separate registry

Conclusion:

- replay is not the main blocker
- the real blocker is the end-to-end canonical path: producer boundary plus Stage 4 persistence fan-out plus activation scope

## 6. Consumer Surfaces Are Safer Than They Look

The good news is that many current consumer surfaces are `known_attrs`-centric, not martial-state-centric.

Live evidence:

- `truth_gate.py` uses `get_known_skills()` and `get_npc_role_snapshot()`
- `semantic_query_broker.py` reads `alive_npcs` mainly for `relation`, `role`, and `known_attrs`
- `chief_writer_context_packets.py` merges NPC snapshot data from `known_attrs`
- `npc_drift_advisor.py` also keys off `known_attrs`

Implication:

- adding `alive_npcs[name]["martial_state"]` can be largely inert-by-default
- that lowers regression risk for a first storage wave

But the same evidence also means:

- a storage-only wave will not immediately improve Stage 4 prompt truth or validator power
- those consumer gains would need a later activation wave

Conclusion:

- inert storage-first is feasible
- storage-first plus immediate consumer activation is not yet justified

## 7. Last Narrow Issues That Still Need Explicit Decisions

This seam is no longer "investigate more until clarity appears." The remaining issues are explicit design gates.

### Gate 1. Canonical Producer Authority

Question:

- what is the canonical producer for `npc_martial_state_changes`?

Required answer:

- LLM-facing `state_changes` schema may expose the family
- analyst defaults may preserve the family
- but canonical authority still has to flow through `StateTracker.extract_all_state_changes()`

Why it matters:

- if this is not explicit, the new family will look present upstream but disappear in the canonical producer path

Judgment:

- this gate is understood
- it does not block execution if the SSOT states it explicitly

### Gate 2. High-Confidence Delta Threshold

Question:

- when does the system record an NPC martial delta?

Required answer:

- explicit realm advancement: yes
- explicit "learned/mastered/attained" technique delta: yes
- one-off move mention or combat flavor: no
- speculative regex backfill from prose: no

Why it matters:

- this is the difference between a stable current-state owner and a noisy pseudo-registry

Judgment:

- this is the tightest unresolved semantic edge
- it is still manageable if the first wave uses only high-confidence explicit deltas

### Gate 3. Storage-Only Versus Activated Consumers

Question:

- does wave 1 only persist NPC martial state, or also inject it into Stage 4 and validators?

Required answer:

- wave 1 should be storage-only
- no Stage 4 canonical injection
- no validator enforcement
- no reveal ledger
- no chronology

Why it matters:

- widening past storage-only multiplies semantic and regression risk immediately

Judgment:

- this gate is fully decided by the audit
- execution is only viable if the SSOT enforces storage-only scope

### Gate 4. Replay-Authoritative Persistence Path

Question:

- does the new payload remain nested under canonical `state_changes` all the way through Stage 4 post-pass and episode-bible persistence?

Required answer:

- yes
- the first wave must keep the payload inside `state_changes`
- it must survive `stage4_post_pass_runtime.py` into `bible_delta["state_changes"]`
- it must not rely on a new top-level Bible field or separate table

Why it matters:

- `episode_bibles.state_changes` is what rollback replays
- new top-level or side-table modeling would immediately expand into DB serialization, cleanup tooling, and reset lists

Judgment:

- this gate is now explicit
- execution is only viable if the first wave stays nested and replay-authoritative

## 8. Go / No-Go Matrix

### Case A. Broad NPC Martial Authority Wave

Includes any of:

- Stage 4 canonical injection
- validator enforcement
- chronology / reveal ledger
- usage history
- registry or new DB tables

Verdict:

- **no-go**

Reason:

- blast radius becomes too wide relative to current certainty
- current consumer surfaces are not prepared for authoritative activation

### Case B. Storage-Only Substrate Wave

Includes only:

- new `npc_martial_state_changes` family
- upstream schema/default support
- bounded tracker emission
- Stage 4 post-pass pass-through into canonical `bible_delta["state_changes"]`
- bounded `WorldState.alive_npcs[name]["martial_state"]` persistence
- replay-safe tests

Verdict:

- **conditional go**

Conditions:

- producer authority written explicitly
- high-confidence extraction threshold written explicitly
- storage-only scope written explicitly
- payload remains nested under canonical `state_changes`

### Case C. Prompt-Only Or Validator-Only Shortcut

Verdict:

- **no-go**

Reason:

- creates overconfident enforcement without a persisted owner

## 9. Recommended Execution Shape If Promoted

If this seam is promoted, the first execution SSOT should be no bigger than this:

1. add `npc_martial_state_changes` to `StateChangesDict`
2. expose it in `response_schemas.py`
3. preserve/default it in `analyst.py`
4. emit only explicit high-confidence deltas from `StateTracker` / `StateTrackerNPC`
5. preserve the payload through `stage4_post_pass_runtime.py` into `bible_delta["state_changes"]`
6. persist only current NPC martial state into `WorldState.alive_npcs[name]["martial_state"]`
7. verify replay / rollback safety with bounded tests

Explicit exclusions:

- `FactLedger` martial fact modeling
- `get_npc_role_snapshot()` expansion
- Stage 4 canonical injection
- truth gate / validator activation
- technique chronology
- reveal ledger
- usage counters
- new DB tables

Notes:

- if a future design tries to add a new top-level Bible field or dedicated table, it is no longer this wave
- that wider shape would also pull in `db_manager.py`, cleanup tooling, and broader reset paths

## 10. Practical Risk If We Wait

The cost of waiting is real but bounded.

If deferred longer:

- long-run wuxia continuity can still drift on NPC martial facts
- the system can still miss contradictions like sudden realm jumps or unearned technique knowledge

But if executed too broadly now:

- the project risks building a fake canonical layer
- or accidentally opening a registry-scale subsystem

This is why the right answer is not "never do it."
It is:

- do it only as a narrow substrate wave

## 11. Final Decision

Decision:

- execution now, broad form: **no**
- execution now, bounded substrate form: **yes, but only conditionally**

Operationally, that means:

- it is now reasonable to open a bounded execution SSOT
- but only if the SSOT is explicitly framed as `NPC martial current-state substrate only`
- if the requested scope includes Stage 4 consumer activation, validators, reveal chronology, ledger behavior, or new DB/table modeling, the answer flips back to **not yet**

Estimated confidence: 97%

## 12. 3-Pass Audit Record

Pass 1. Surface Inventory
- re-checked producer, schema, `WorldState`, replay, Stage 4, validator, and consumer surfaces
- confirmed the missing owner is real and localized
- PASS

Pass 2. Contract Narrowing
- separated broad authority fantasies from the actually viable storage substrate
- identified the three remaining explicit gates
- PASS

Pass 3. Readiness Judgment
- converted the findings into a real go / no-go matrix
- made the decision executable for a future bounded SSOT
- PASS

---

- Broad wave readiness: `no-go`
- Storage-only substrate wave readiness: `conditional go`
- Tightest remaining edges: `high-confidence NPC martial delta threshold`, `Stage 4 post-pass persistence fan-out`
