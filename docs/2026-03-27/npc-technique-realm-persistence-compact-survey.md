# NPC Technique-Realm Persistence Compact Survey

Date: 2026-03-27
Status: final (survey-only, no code changes)
Type: system-track compact survey + design memo
Canonical Path: `docs/2026-03-27/npc-technique-realm-persistence-compact-survey.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-defer-priority-freeze.md`
- `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md`
- `docs/2026-03-27/wuxia-technique-realm-tracking-design-memo.md`
- `docs/2026-03-27/wuxia-technique-realm-contract-alignment-wave1-execution-ssot.md`
Evidence Basis:
- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/core/world_state.py`
- `modules/core/stage4_context_builder.py`
- `modules/validation/blocking_validator.py`
- `modules/validation/blocking_validator_consistency_checks.py`
- `modules/models/arc.py`
- `config/genres/wuxia.yaml`
Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked narrative/router/provider/stage4/test/doc surfaces, logs/artifacts; untracked dated docs, provider adapters/tests, canary projects, narrative artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Side-Effect Coverage: not-applicable

## 1. Executive Summary

The next real deferred seam is no longer protagonist technique / realm authority. That slice was already narrowed and closed in the protagonist-first wave. The remaining seam is the heavier one:

- NPC technique mastery has no persistent owner
- NPC realm progression has no persistent owner
- technique reveal / usage history has no persistent owner

This is why ROI is only medium-to-low for an immediate implementation wave. The remaining work is not another prompt or validator cleanup. It is a modeling and persistence question.

Bottom line:
- importance: high for long-run wuxia continuity
- immediate ROI: medium-to-low
- execution SSOT now: **no**
- better next artifact: **design-first compact survey** defining the smallest viable owner model

## 2. Scope

Included:
- live owner surfaces for protagonist vs NPC martial facts
- current `state_changes` and `WorldState` persistence boundaries
- current Stage 4 and validator usage of technique / realm facts
- bounded design options for NPC technique / realm ownership

Excluded:
- code changes
- new execution SSOT
- registry implementation
- DB schema migration
- non-wuxia genre modeling
- fight geography or choreography persistence

## 3. Live Baseline

### 3.1 What Already Exists

Protagonist-side ownership exists today:
- `StateTracker` owns `protagonist_skills` and `skill_acquisitions`
- `StateTrackerNPC.extract_skill_acquisitions_from_arc()` only registers protagonist skills
- `WorldState._apply_actor_and_inventory_state_changes()` applies `skill_acquisitions` only to `self._state["protagonist"]["skills"]`
- `stage4_context_builder.py` injects a wuxia-only protagonist authority clause when protagonist skills are present
- `blocking_validator_consistency_checks.py` runs a wuxia technique-vs-realm check only for the protagonist, using `martial_hud.actual_truth.realm` or `context["protagonist_realm"]`
- `config/genres/wuxia.yaml` already provides `realm_hierarchy` and `realm_technique_limits`

### 3.2 What Does Not Exist

NPC-side ownership does not exist in the inspected runtime slice:
- `StateChangesDict` has no NPC technique or NPC realm fields
- `StateTracker.extract_all_state_changes()` emits no NPC martial-state payload
- `StateTrackerNPC` extracts protagonist skills, injuries, movements, relationships, and personality, but not NPC technique mastery or NPC realm progression
- `WorldState` persists NPC `known_attrs` such as injury, location, permanent injuries, knowledge tags, and secrets, but not technique mastery or realm
- `get_canonical_constraints()` and the Stage 4 canonical block do not surface NPC technique / realm as owned canonical facts
- validator logic has no NPC technique-vs-realm enforcement path

## 4. Current Contract Gap

The remaining gap is not one thing. It is three layers:

1. current-state ownership gap
- the system cannot answer "what technique set does NPC X currently canonically know?" or "what realm is NPC X canonically at?" from a persisted owner

2. event-history gap
- the system cannot answer "when was technique Y first revealed for NPC X?" or "was this move previously established?"

3. authority gap
- because there is no owner, prompt statements or validator rules would be forced to infer from manuscript text or advisory summaries

The first gap is the minimum viable target. The second and third only become tractable after the first exists.

## 5. Why Simple Fixes Have Low ROI

### Option A. Prompt-Only NPC Advisory

Shape:
- inject a new Stage 4 note telling the model to stay consistent about NPC technique / realm

Pros:
- cheap
- low blast radius

Cons:
- no actual owner to anchor the advice
- no way to distinguish established NPC fact from a one-off manuscript flourish
- easiest path to false confidence

Verdict:
- not recommended

### Option B. Validator-Only NPC Consistency

Shape:
- reject when manuscript shows an NPC using a disallowed technique or realm-inconsistent move

Pros:
- catches some obvious contradictions

Cons:
- still lacks a persisted NPC owner
- would have to infer from manuscript text, regex, or partial advisory context
- high false-positive / false-negative risk

Verdict:
- not recommended as the first move

### Option C. Full Registry / Usage Ledger

Shape:
- persist NPC technique mastery, realm progression, and reveal history as a dedicated registry

Pros:
- strongest long-run continuity model

Cons:
- highest blast radius
- effectively a new subsystem
- poor near-term ROI

Verdict:
- too heavy for the next wave

## 6. Smallest Plausible Owner Model

If this seam is ever promoted into execution, the smallest plausible model is:

### Slice 1. Current NPC martial state only

Persist only:
- current NPC realm
- current NPC known technique list or compact technique families

Do not persist yet:
- full usage chronology
- reveal ledger
- fight-scene event history

### Slice 2. Reuse existing owner channels where possible

Prefer:
- `state_changes` extension for explicit NPC martial deltas
- `WorldState` current NPC state as the realized owner surface

Avoid for the first wave:
- new DB tables
- separate registry service
- replay redesign

### Slice 3. Keep protagonist and NPC concerns separate

Do not reopen protagonist authority work already closed.

The next design should treat:
- protagonist technique / realm = settled enough
- NPC technique / realm = new owner-model problem

## 7. Recommended Design Direction

If a future execution wave is opened, the bounded design should look like this:

1. extend `StateChangesDict` with one compact NPC martial delta family
- example shape:
  - `npc_martial_state_changes`
  - entries like `{name, realm, techniques, episode, source}`

2. teach `StateTracker` / `StateTrackerNPC` to emit only explicit deltas
- no regex-only backfill as the canonical owner
- regex can remain extraction assist, but not final authority

3. teach `WorldState` to persist only current realized NPC martial facts
- current realm
- current known techniques or technique families

4. stop there for wave 1 of this problem
- no reveal chronology
- no usage ledger
- no broad registry

This is the only shape that looks plausibly worth the engineering cost.

## 8. Blast Radius If Executed

The minimum affected surfaces would likely be:
- `modules/models/arc.py`
- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/core/world_state.py`
- Stage 4 context injection that decides whether NPC martial facts become canonical prompt material
- validator logic only after a persisted owner exists
- replay / rollback paths indirectly, because `state_changes` is replayed into `WorldState`

This is why the next step should still be design-first, not execution-first.

## 9. Operating Consequence

Current recommendation:
- keep this as deferred
- do not open an execution SSOT yet
- if you want to push this forward, open one more bounded **owner-model design memo** for:
  - NPC martial delta shape
  - current-state persistence target
  - replay / rollback implications
  - whether realm and technique should share one payload or two

If a fresh runtime failure starts showing repeated NPC martial contradictions in actual wuxia output, then the priority can be raised.

## 10. Queue Truth

- active temp execution SSOT mirrors: `0`
- `docs/temp/queue-state.json`: absent
- this survey does not open a queue item

## 11. 3-Pass Audit Record

Pass 1. Structure and Scope
- kept the document survey-only
- separated current owner facts from future design direction
- avoided inflating into an execution SSOT
- PASS

Pass 2. Evidence and Consistency
- verified protagonist-only martial ownership in `StateTracker`, `WorldState`, Stage 4, and validator surfaces
- verified absence of NPC martial persistence in `StateChangesDict`, `StateTracker`, and `WorldState`
- bounded all design claims to currently inspected owner surfaces
- PASS

Pass 3. Execution and Readability
- made the immediate consequence explicit: design-first, not execution-first
- made the smallest plausible owner model concrete enough for a later follow-up
- kept heavy registry ideas clearly out of the recommended next step
- PASS

Estimated confidence: 96%

---

- ROI judgment: `medium-to-low`
- Dominant unresolved seam: `NPC technique / realm has no persisted owner`
- Should Codex open an execution SSOT now: `no`
