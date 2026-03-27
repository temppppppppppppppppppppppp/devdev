# NPC Technique-Realm Owner-Model Design Memo

Date: 2026-03-27
Status: final
Type: system-track design memo (design-only, no code changes)
Canonical Path: `docs/2026-03-27/npc-technique-realm-owner-model-design-memo.md`
Temp Mirror Path: none
Inputs:
- `docs/2026-03-27/npc-technique-realm-persistence-compact-survey.md`
- `docs/2026-03-27/wuxia-technique-realm-tracking-design-memo.md`
- `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md`
Evidence Basis:
- `modules/models/arc.py`
- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/core/world_state.py`
- `modules/core/stage4_context_builder.py`
- `modules/validation/blocking_validator_consistency_checks.py`
- `config/genres/wuxia.yaml`
Commit State:
- Baseline Commit: `161b71348732e06d9542daf3f54ad8a65126eada`
- Baseline Dirty Summary: `dirty: 1 untracked doc; hotspot: docs/2026-03-27/npc-technique-realm-persistence-compact-survey.md`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Side-Effect Coverage: not-applicable

## 1. Executive Summary

The open wuxia seam is no longer broad technique/realm authority. It is narrower:

- protagonist martial authority is good enough for bounded contract work
- NPC martial authority still has no persistent owner

This memo exists to answer one question only:

What is the smallest viable owner model for NPC technique / realm facts if this seam is ever promoted out of defer?

Answer:
- one shared delta payload for NPC martial changes
- one persistent owner surface in `WorldState`
- no reveal ledger
- no chronology registry
- no execution SSOT yet

On the NPC modeling question, this memo is the narrower authority over the older broad `wuxia-technique-realm-tracking-design-memo.md`.

## 2. Problem Statement

Today the system can persist:
- protagonist learned techniques
- protagonist-facing realm guard usage
- NPC injuries, location, relation, personality, and other known attributes

Today the system cannot persist:
- NPC current canonical realm
- NPC current canonical technique set
- NPC technique reveal history

That means Stage 4 or validators would have to infer NPC martial facts from manuscript text or advisory summaries. That is the wrong owner model.

## 3. Design Goal

If this seam is promoted later, the first wave should solve only this:

- "What NPC martial facts are currently canonical now?"

It should not try to solve:

- "When exactly was every NPC technique first revealed?"
- "How many times was each move used?"
- "What is the full martial chronology across episodes?"

Those are event-history problems, not minimum owner problems.

## 4. Live Baseline

### 4.1 Settled Enough

- `StateTracker` and `StateTrackerNPC.extract_skill_acquisitions_from_arc()` already persist protagonist technique acquisition through `skill_acquisitions`
- `WorldState._apply_actor_and_inventory_state_changes()` already realizes protagonist skills into `self._state["protagonist"]["skills"]`
- `stage4_context_builder.py` already injects a wuxia-only protagonist technique/realm authority clause
- `blocking_validator_consistency_checks.py` already runs a protagonist-only technique-vs-realm check using `wuxia.yaml`

### 4.2 Missing Owner

- `StateChangesDict` has no NPC martial payload family
- `StateTracker.extract_all_state_changes()` emits no NPC martial state
- `WorldState` persists NPC `known_attrs`, but no canonical martial slot
- validator logic has no NPC martial owner to read from

This is why the remaining problem is modeling, not prompt wording.

## 5. Recommended Minimal Owner Model

### 5.1 One Shared Delta Payload

Do not split realm and technique into separate top-level payload families in the first wave.

Recommended family:
- `npc_martial_state_changes`

Recommended entry shape:

```python
{
    "name": "NPC name",
    "episode": 12,
    "source": "state_changes" | "tracker_extract",
    "realm": "peak_realm",
    "techniques_learned": ["technique_a", "movement_b"],
}
```

Rules:
- `name` is required
- `episode` is required for replay clarity
- `realm` is optional
- `techniques_learned` is optional and additive-only
- missing fields mean "no change", not "clear existing state"

Why one shared family:
- realm and technique are read together in wuxia logic
- the same extraction pass would usually emit both
- replay semantics are simpler with one ordered payload family
- it avoids a false contract split where realm and techniques can silently drift apart

### 5.2 One Persistent Owner Surface

Do not hide this inside generic `known_attrs` as the canonical owner.

Recommended `WorldState` target:

```python
alive_npcs[name]["martial_state"] = {
    "realm": "peak_realm",
    "realm_changed_ep": 12,
    "techniques": ["technique_a", "movement_b"],
    "last_martial_ep": 12,
}
```

Why:
- `known_attrs` is useful for human-readable snapshots, but it is too generic for later validator or Stage 4 contract use
- a dedicated `martial_state` slot keeps future ownership explicit
- current-state ownership becomes queryable without building a new registry

### 5.3 Keep Technique History Out

Do not add:
- `technique_usage_history`
- `reveal_ledger`
- `first_seen_ep_per_technique`

in the first owner-model wave.

Reason:
- those are chronology artifacts
- they inflate replay and validation cost immediately
- they are not required to answer the minimum continuity question

## 6. Replay / Rollback Implications

The design only works if replay stays cheap and deterministic.

Required semantics:
- `npc_martial_state_changes` entries replay in arc order
- `realm` is last-write-wins
- `techniques_learned` is additive union
- absence of a field means no-op
- rollback/rebuild must be possible from existing arc/state-change replay, without a new side registry

This is the main reason to prefer:
- explicit deltas in `StateChangesDict`
- realized owner in `WorldState`

and to avoid:
- manuscript regex as canonical source
- separate DB tables in the first wave

## 7. Extraction Boundary

If this is executed later, extraction should stay bounded.

Good first-wave extraction candidates:
- explicit `state_changes` martial entries already emitted by upstream stages
- narrow tracker extraction when the arc clearly states an NPC realm advancement
- narrow tracker extraction when the arc clearly states an NPC learned or revealed technique

Bad first-wave extraction candidates:
- speculative regex mining of combat prose
- backfilling full NPC martial state from historical manuscript text
- inferring a complete technique set from one move mention

The payload should only capture high-confidence explicit deltas.

## 8. Stage 4 / Validator Consequence

Do not start here.

Only after the owner exists should later waves consider:
- Stage 4 canonical injection of NPC martial facts
- validator-level NPC technique-vs-realm checks

Without a persisted owner, both would be overconfident heuristics.

## 9. Why This Still Is Not Execution-Ready

Even with the minimum owner model clarified, there is still open design work:

- exact extraction threshold for "NPC learned technique" versus "NPC merely used a move once"
- whether `techniques` should store exact names only or allow compact family buckets
- whether `martial_state` should mirror into prompt-facing canonical summaries immediately or one wave later

So the next artifact, if any, should still be a bounded execution SSOT only after those three edges are resolved.

## 10. Recommended Next Step

Do not open implementation immediately.

If this seam is promoted later, open one bounded execution SSOT only for:
- `StateChangesDict` extension with `npc_martial_state_changes`
- bounded `StateTracker` / `StateTrackerNPC` emission
- bounded `WorldState` persistence into `alive_npcs[name]["martial_state"]`

Explicitly exclude:
- chronology ledger
- reveal history
- Stage 4 injection changes
- validator changes
- new DB tables

## 11. 3-Pass Audit Record

Pass 1. Structure and Scope
- kept the memo on minimum owner-model only
- separated owner-model from later prompt/validator work
- avoided inflating into execution SSOT
- PASS

Pass 2. Evidence and Consistency
- rechecked that protagonist martial ownership already exists in `StateTracker`, `WorldState`, Stage 4, and validator surfaces
- rechecked that NPC martial ownership is absent from `StateChangesDict`, `StateTracker`, and `WorldState`
- kept all design claims bounded to replayable current-state ownership
- PASS

Pass 3. Execution and Readability
- made the recommended payload and owner slot concrete
- made replay semantics explicit
- kept chronology and registry work clearly out of scope
- PASS

Estimated confidence: 96%

---

- Minimum owner-model recommendation: `one npc_martial_state_changes payload + one WorldState martial_state owner`
- Immediate ROI: `still medium-to-low`
- Should Codex open an execution SSOT now: `not yet`
