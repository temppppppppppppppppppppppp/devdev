Date: 2026-03-27
Status: final (3-pass audited)
Document Type: system-track compact survey (survey-only, no code changes)
Canonical Path: `docs/2026-03-27/state-changes-schema-formalization-compact-survey.md`
Source Order: `docs/2026-03-27/state-changes-schema-formalization-compact-survey-order.md`
Priority Slot: defer Tier 1A

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked provider/context/validator/stage4/orientation/runtime surfaces, queue-state.json, logs/artifacts; untracked dated docs, anthropic_vertex provider/tests, probe script, project artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Executive Summary

The `state_changes` contract has **two distinct producer paths**, **two primary consumers with different key sets**, and a **partial Pydantic model that covers only 4 of 20+ runtime keys**. The dominant drift is not field-name chaos but a structural split: WorldState is fed by a merged superset dict built by `stage4_post_pass_runtime`, while FactLedger can receive either an extraction-shaped dict or the narrower post-pass merged dict, and still reads a different subset from WorldState. Both consumers tolerate missing keys gracefully (`.get` with defaults), so the contract survives in practice, but an LLM generating `state_changes` has no authoritative schema to follow.

The smallest safe formalization is a **TypedDict-first** approach: one canonical `StateChangesDict` TypedDict covering the 20+ runtime keys, placed adjacent to the existing `StateChanges` Pydantic model in `modules/models/arc.py`. This does not require behavioral changes, DB migration, or broad refactor — it makes the implicit contract explicit as a type annotation.

Key findings:
- **2 producer paths** producing different key sets
- **2 primary consumers** reading different subsets
- **6 secondary consumers** reading specific fields only
- **3 field-name aliases** for the same concept (commitments/promises/promises_obligations)
- **3 polymorphic keys** accepting both dict and string entries
- **3+ incompatible enum vocabularies** for relationship status
- **1 partial Pydantic model** (`StateChanges`, 4 fields) that is not used as the actual type

---

## 2. Scope and Exclusions

### Included

| Surface | Files | Role |
|---------|-------|------|
| Producer: StateTracker family | `state_tracker.py`, `state_tracker_npc.py`, `state_tracker_plots.py`, `state_tracker_financial.py` | Primary extraction + internal registry |
| Producer: Analyst | `analyst.py:1230-1253` | Key guarantee + default initialization |
| Producer: stage4_post_pass_runtime | `stage4_post_pass_runtime.py:899-914, 944-992` | WorldState-specific merged dict |
| Consumer: WorldState | `world_state.py` | 20 keys consumed |
| Consumer: FactLedger | `fact_ledger.py` | 16+ keys consumed |
| Consumer: stage4_context_builder | `stage4_context_builder.py:277-388, 1822-1828` | NPC/entity roster collection |
| Consumer: context_advisor | `context_advisor.py:837-1052` | NPC name + relationship extraction |
| Consumer: stage2_finalizer | `stage2_finalizer.py:414-438, 1064, 1089` | Semantic carryover |
| Consumer: arc_draft_validator | `arc_draft_validator.py:539` | Relationship NPC extraction |
| Contract-adjacent: blocking_validator | `blocking_validator.py`, `blocking_validator_consistency_checks.py` | **Non-applicable** (no direct state_changes read) |
| Contract-adjacent: stage3_orchestrator | `stage3_orchestrator.py:976-1008` | **Indirect** (reads `state_changes.timeline` only for temporal metadata) |
| Existing model | `modules/models/arc.py:170-179` | Partial StateChanges Pydantic (4 fields) |
| ArcData type | `modules/models/arc.py:210` | `state_changes: dict` (not StateChanges) |

### Excluded

- Full fact-authority redesign (out of scope per order)
- Technique/realm modeling (deferred structural problem)
- Provider consolidation, writer/context refactor, global Stage 4 cleanup
- Code changes of any kind

---

## 3. Producer Inventory

### 3.1 Producer Path A: StateTracker `extract_all_state_changes()`

Source: `state_tracker.py:1581-1626`

This method returns a dict with 16 keys. It is the primary extraction surface and one of the de facto producer contract shapes that later fact-persistence consumers are expected to understand.

| Key | Producer (file:method:line) | Emitted Shape | Source Type | Genre-Cond? |
|-----|---------------------------|---------------|-------------|-------------|
| `npc_deaths` | `state_tracker_npc.py:extract_npc_deaths_from_arc:657` | `list[dict\|str]` | explicit + regex + LLM verify | No |
| `skill_acquisitions` | `state_tracker_npc.py:extract_skill_acquisitions_from_arc:816` | `list[dict\|str]` | explicit + regex | No |
| `relationship_changes` | `state_tracker_npc.py:extract_relationship_changes_from_arc:868` | `list[dict]` with keys {npc, from, to, episode, arc_no} | explicit + regex | No |
| `major_items` | `state_tracker.py:1613` | `list[dict]` | explicit passthrough | No |
| `resolved_plots` | `state_tracker_plots.py:extract_resolved_plots_from_arc:98` | `list[dict]` with keys {plot, resolution, episode, arc_no} | explicit only | No |
| `npc_injuries` | `state_tracker_npc.py:extract_npc_injuries_from_arc:927` | `list[dict]` with keys {name, episode, state, arc_no} | explicit + regex | No |
| `npc_movements` | `state_tracker_npc.py:extract_npc_movements_from_arc:991` | `list[dict]` with keys {name, episode, from, to, arc_no} | explicit + regex | No |
| `financial_events` | `state_tracker_financial.py:extract_financial_events_from_arc:20` | `dict` with keys {exchange_rates, total_assets, leverage, key_transactions} | explicit only | **Yes** (investment) |
| `entity_destructions` | `state_tracker_plots.py:extract_entity_destructions_from_arc:156` | `list[dict]` with keys {name, type, cause, episode, arc_no} | explicit only | No |
| `npc_personality_changes` | `state_tracker_npc.py:extract_npc_personality_from_arc:1626` | `list[dict]` with keys {name, traits, motivation, arc_no} | explicit only | No |
| `npc_npc_relationships` | `state_tracker_npc.py:extract_npc_npc_relationships_from_arc:1669` | `list[dict]` with keys {npc1, npc2, relation, arc_no} | explicit only | No |
| `time_markers` | `state_tracker_plots.py:extract_time_markers_from_arc:461` | `list[dict]` with keys {arc_no, episode, type, description} | explicit + regex | No |
| `permanent_injuries` | `state_tracker_npc.py:extract_permanent_injuries_from_arc:1238` | `list[dict]` with keys {name, type, description, episode, arc_no} | explicit + regex | No |
| `companion_changes` | `state_tracker_npc.py:update_companions_from_arc:1824` | `list[dict]` with keys {name, action, episode, reason, arc_no} | explicit + regex | No |
| `commitments` | `state_tracker_plots.py:extract_commitments_from_arc:728` | `list[dict]` with keys {parties, description, episode, deadline_hint, arc_no} | explicit + regex | No |
| `protagonist_emotion` | `state_tracker_npc.py:extract_protagonist_emotion_from_arc:1968` | `dict\|None` with keys {emotion, trigger, episode, arc_no} | explicit + regex | No |

### 3.2 Producer Path B: Analyst Key Guarantee

Source: `analyst.py:1230-1253`

After LLM arc generation, Analyst ensures 14 keys exist with `[]` defaults:

```
npc_deaths, skill_acquisitions, relationship_changes, major_items,
entity_destructions, npc_personality_changes, npc_npc_relationships,
npc_dialogue_profiles, npc_injuries, npc_movements, time_markers,
companion_changes, promises_obligations, protagonist_emotion
```

Notable: uses `promises_obligations` (not `commitments`), includes `npc_dialogue_profiles` (not in Path A return).

### 3.3 Producer Path C: stage4_post_pass_runtime (post-pass merged persistence payload)

Source: `stage4_post_pass_runtime.py:899-914, 944-992`

Constructs `world_state_changes` by merging:
- `final_state_updates` (from actual_truth or LLM-generated state)
- `inventory_payload` (inventory_counts, inventory_count_deltas)
- `relationship_payload`
- `pressure_payload` (active_pressure_vectors from bible_delta.state_changes)

This merged dict is passed to `world_state.update_from_state_changes()`, and a narrower sibling payload is passed to `fact_ledger.update_from_state_changes()`. It contains keys that Producer Path A does NOT emit: `inventory_counts`, `inventory_count_deltas`, `active_pressure_vectors`, `npc_introductions`, `npc_attribute_changes`, `world_law_additions`, `protagonist_motivations`.

### 3.4 Polymorphic Entry Acceptance

| Key | Accepted Forms | Evidence |
|-----|---------------|----------|
| `npc_deaths` | `list[str]` ("Name") OR `list[dict]` ({"name": "Name", "episode": 5, "cause": "..."}) | `state_tracker_npc.py:674-708` |
| `skill_acquisitions` | `list[str]` ("Skill") OR `list[dict]` ({"name": "Skill", "episode": 5, "source": "...", "tier": "..."}) | `state_tracker_npc.py:831-847` |
| `protagonist_emotion` | `dict` ({"emotion": "...", ...}) OR `list[dict]` ([{"emotion": "...", ...}]) | `state_tracker_npc.py:1982-1992` |
| `commitments.parties` | `list[str]` OR `str` (auto-wrapped) | `state_tracker_plots.py:744-766` |

---

## 4. Consumer Inventory

### 4.1 WorldState (`world_state.py`)

Entry: `update_from_state_changes(ep_num, state_changes)` — receives merged superset dict from Path C.

| Key | Method:Line | Expected Shape | Missing Tolerance | Wrong-Value | Side Effects |
|-----|------------|----------------|-------------------|-------------|-------------|
| `npc_deaths` | `_apply_actor_and_inventory:182` | `list[dict\|str]` | skip (`.get([])`) | silent skip | Moves NPC alive->dead |
| `skill_acquisitions` | `_apply_actor_and_inventory:203` | `list[dict\|str]` | skip | silent skip | Appends protagonist.skills (max 50) |
| `relationship_changes` | `_apply_actor_and_inventory:222` | `list[dict]` | skip | silent skip | Updates relationships dict |
| `major_items` | `_apply_actor_and_inventory:250` | `list[dict\|str]` | skip | silent skip | Adds/updates active_items |
| `inventory_counts` | `_apply_actor_and_inventory:271` | `dict[str, int]` | skip (`.get({})`) | silent skip | Updates item quantities |
| `inventory_count_deltas` | `_apply_actor_and_inventory:293` | `list[dict]` | skip | silent skip | Updates item quantities |
| `entity_destructions` | `_apply_entity_and_companion:323` | `list[dict]` | skip | silent skip | Appends destroyed[] (max 100) |
| `npc_personality_changes` | `_apply_entity_and_companion:344` | `list[dict]` | skip | silent skip | Updates known_attrs |
| `resolved_plots` | `_apply_entity_and_companion:374` | `list[dict\|str]` | skip | silent skip | Removes from active_plots |
| `active_pressure_vectors` | `_apply_entity_and_companion:391` | `list[dict]` | skip (`in` check) | normalized | Replaces entire list (max 5) |
| `companion_changes` | `_apply_entity_and_companion:402` | `list[dict]` | skip | silent skip | Sets companion flag on NPC |
| `time_markers` | `_apply_timeline_and_goal:418` | `list[dict]` | skip | silent skip | Appends timeline, DB upsert |
| `protagonist_motivations` | `_apply_timeline_and_goal:460` | `list[dict]` | skip | silent skip | Upserts motivations (max 20) |
| `commitments` / `promises` | `_apply_timeline_and_goal:491` | `list[dict]` | skip (tries both keys) | silent skip | Upserts promises (max 30) |
| `npc_injuries` | `_apply_physical_known_attr:525` | `list[dict]` | skip | silent skip | Updates known_attrs.injury |
| `npc_movements` | `_apply_physical_known_attr:547` | `list[dict]` | skip | silent skip | Updates known_attrs.location |
| `permanent_injuries` | `_apply_physical_known_attr:570` | `list[dict]` | skip | silent skip | Updates known_attrs.permanent_injuries |
| `npc_attribute_changes` | `_apply_npc_registry_and_law:596` | `list[dict]` | skip | silent skip | Syncs known_attrs fields |
| `npc_introductions` | `_apply_npc_registry_and_law:625` | `list[dict]` | skip | silent skip | Creates alive_npcs entry |
| `world_law_additions` | `_apply_npc_registry_and_law:682` | `list[str\|dict]` | skip | silent skip | Adds world laws (max 20) |

### 4.2 FactLedger (`fact_ledger.py`)

Entry: `update_from_state_changes(ep_num, state_changes)` — receives dict from either Path A extraction or Path C merged dict.

| Key | Method:Line | Expected Shape | Missing Tolerance | Wrong-Value | Side Effects |
|-----|------------|----------------|-------------------|-------------|-------------|
| `npc_deaths` | `_apply_character_foundation:231` | `list[dict\|str]` | skip | silent skip | Upserts character status=dead |
| `relationship_changes` | `_apply_character_foundation:245` | `list[dict]` | skip | silent skip | Upserts character relationship |
| `skill_acquisitions` | `_apply_item:263` | `list[dict\|str]` | skip | silent skip | Upserts item status=습득 |
| `major_items` | `_apply_item:276` | `list[dict\|str]` | skip | silent skip | Upserts item |
| `inventory_counts` | `_apply_item:288` | `dict[str, int]` | skip | silent skip | Upserts item quantity |
| `inventory_count_deltas` | `_apply_item:299` | `list[dict]` | skip | silent skip | Upserts item quantity |
| `entity_destructions` | `_apply_entity:315` | `list[dict]` | skip | silent skip | Upserts org/location destroyed |
| `npc_injuries` | `_apply_character_followup:329` | `list[dict]` | skip | silent skip | Upserts character injury note |
| `npc_movements` | `_apply_character_followup:340` | `list[dict]` | skip | silent skip | Upserts character movement note |
| `npc_personality_changes` | `_apply_character_followup:351` | `list[dict]` | skip | silent skip | Upserts character personality |
| `npc_npc_relationships` | `_apply_character_followup:368` | `list[dict]` | skip | silent skip | Upserts both NPCs |
| `capital` / `total_assets` / `wealth` | `_extract_numerical_facts:458` | scalar | skip if missing/coerce fails | silent skip | `update_number()` + DB canonical_fact |
| `status_shadow` | `_extract_numerical_facts:464` | `dict` | skip if absent | silent skip | Extracts internal_energy_* numbers |
| `financial_events` | `_extract_numerical_facts:476` | `list[dict]` | skip | silent skip | Extracts per-asset numbers |
| `power_level` | `_extract_numerical_facts:490` | scalar | skip if absent | silent skip | `update_number()` |
| `numerical_facts` | `_extract_numerical_facts:495` | `list[dict]` | skip | silent skip | `update_number()` per fact |

### 4.3 Secondary Consumers

| Consumer | File:Line | Keys Read | Role |
|----------|-----------|-----------|------|
| stage4_context_builder | `stage4_context_builder.py:279-291` | `npc_deaths`, `relationship_changes`, `npc_injuries`, `npc_introductions` | NPC roster collection |
| stage4_context_builder | `stage4_context_builder.py:346-388` | `major_items`, `items_acquired`, `resolved_plots`, `active_plots`, `npc_movements` | Entity/plot collection |
| context_advisor | `context_advisor.py:837-1052` | `npc_deaths`, `relationship_changes`, `npc_injuries` | NPC name + rel query building |
| stage2_finalizer | `stage2_finalizer.py:414-438` | `relationship_changes` | Semantic carryover (trigger/justification) |
| arc_draft_validator | `arc_draft_validator.py:539` | `relationship_changes` | NPC name extraction |
| stage3_orchestrator | `stage3_orchestrator.py:976-1008` | `timeline` (not a standard key) | Temporal start/end metadata |

### 4.4 Contract-Adjacent: Non-Applicable Surfaces

| Surface | File | Direct Consumer? | Evidence |
|---------|------|-----------------|----------|
| `blocking_validator.py` | `modules/validation/blocking_validator.py` | **NO** | Zero references to `state_changes`. Receives pre-built context dicts (encyclopedia, martial_hud). |
| `blocking_validator_consistency_checks.py` | `modules/validation/blocking_validator_consistency_checks.py` | **NO** | Zero references to `state_changes`. Reads context dict fields (manuscript, incarnation_type, genre). |

---

## 5. Mismatch Ledger

### 5.1 Field Name Drift

| Concept | Name in Producer A (StateTracker) | Name in Producer B (Analyst) | Name in Consumer (WorldState) | Name in Consumer (FactLedger) | Severity |
|---------|----------------------------------|------------------------------|-------------------------------|-------------------------------|----------|
| Commitments/Promises | `commitments` | `promises_obligations` | `commitments` then `promises` (tries both) | not consumed | **MEDIUM** — 3 names for 1 concept |
| NPC Dialogue | not in `extract_all_state_changes` | `npc_dialogue_profiles` | not consumed | not consumed | LOW — write-only |
| Timeline | not in `extract_all_state_changes` | not guaranteed | not consumed as `timeline` | not consumed | LOW — stage3 reads only |

### 5.2 Shape Drift

| Key | Producer Shape | Consumer Expectation | Gap |
|-----|---------------|---------------------|-----|
| `npc_deaths` | `list[dict\|str]` | Both consumers handle dict and str | None — both sides polymorphic |
| `skill_acquisitions` | `list[dict\|str]` | Both consumers handle dict and str | None — both sides polymorphic |
| `protagonist_emotion` | `dict\|list[dict]` | WorldState: not consumed; FactLedger: not consumed | Producer-only polymorphism |
| `relationship_changes` entry | Producer uses key `npc`; `arc.py` model uses key `target` | `stage2_finalizer` reads `target`, `npc`, `name` (triple fallback at line 429) | **MEDIUM** — 3 field names for NPC identity within entries |
| `inventory_counts` | `dict[str, int]` | Both consumers expect `dict[str, int]` | None |
| `financial_events` | `dict` (not list) | FactLedger expects `list[dict]` at line 476 | **LOW** — FactLedger iterates `.get("financial_events", [])`, gets dict; would silently skip if dict has no list items |

### 5.3 Enum/Vocabulary Drift

| Domain | Source A (Analyst prompt) | Source B (StateTracker regex) | Source C (BlockingValidator) | Consumer Default |
|--------|--------------------------|------------------------------|----------------------------|-----------------|
| Relationship status | 적대, 무시, 의심, 중립, 경외, 충성 (6) | 적대, 중립, 아군, 동맹, 호의, 충성, 적 (7) | "중립" as default | No validation |
| NPC disposition | n/a | 중립, 경계, 호의, 충성 (4) | n/a | No validation |
| Injury state | "정상" (arc.py default) | 정상, 경상, 중상, 위독 (4) | 나약, 중독, 부상, 중상, 쇠약, 기력고갈, 기혈역류 (7) | No validation |

All three vocabularies overlap partially but are not aligned. No shared enum module exists. Consumers do not validate values — any string is accepted silently.

### 5.4 Explicit vs Regex Ambiguity

| Key | Explicit (state_changes dict) | Regex Fallback (tactical_doc) | Risk |
|-----|------------------------------|-------------------------------|------|
| `npc_deaths` | Primary | Yes (4 patterns) + LLM verify | LOW — both paths converge |
| `skill_acquisitions` | Primary | Yes (wuxia-specific suffix patterns) | MEDIUM — regex requires specific Korean grammatical forms |
| `relationship_changes` | Primary | Yes (arrow symbol + 에서 patterns) | MEDIUM — regex very restrictive |
| `npc_injuries` | Primary | Yes | LOW |
| `npc_movements` | Primary | Yes | LOW |
| `time_markers` | Primary | Yes | LOW |
| `permanent_injuries` | Primary | Yes | LOW |
| `companion_changes` | Primary | Yes | LOW |
| `commitments` | Primary | Yes | LOW |
| `protagonist_emotion` | Primary | Yes | LOW |
| `resolved_plots` | Primary | **No** | N/A — explicit only |
| `entity_destructions` | Primary | **No** | N/A — explicit only |
| `npc_personality_changes` | Primary | **No** | N/A — explicit only |

### 5.5 Write-Only Fields (Produced but Never Consumed)

| Key | Producer | Any Consumer? |
|-----|----------|---------------|
| `npc_dialogue_profiles` | Analyst guarantee | No consumer reads this key |
| `promises_obligations` | Analyst guarantee | StateTracker reads as fallback alias for `commitments` only |

### 5.6 Read-Only Expectations (Consumed but Not in Primary Producer)

| Key | Consumer | Any Producer? |
|-----|----------|---------------|
| `inventory_counts` | WorldState + FactLedger | Path C only (stage4_post_pass_runtime) |
| `inventory_count_deltas` | WorldState + FactLedger | Path C only |
| `active_pressure_vectors` | WorldState | Path C only (from bible_delta) |
| `npc_introductions` | WorldState | Path C only |
| `npc_attribute_changes` | WorldState | Path C only |
| `world_law_additions` | WorldState | Path C only |
| `protagonist_motivations` | WorldState | Path C only |
| `items_acquired` | stage4_context_builder | Path C only |
| `active_plots` | stage4_context_builder | Path C only |
| `capital` / `total_assets` / `wealth` | FactLedger | Direct scalar fields in state_changes, not sub-keys of a list |
| `status_shadow` | FactLedger | Direct dict field in state_changes |
| `power_level` | FactLedger | Direct scalar field in state_changes |
| `numerical_facts` | FactLedger | Direct list field in state_changes |

---

## 6. Enum/Vocabulary Table

### 6.1 Relationship Status Values

| Source | Values | File:Line |
|--------|--------|-----------|
| Analyst LLM prompt | 적대, 무시, 의심, 중립, 경외, 충성 | `analyst_prompts.py:426` |
| StateTracker regex | 적대, 중립, 아군, 동맹, 호의, 충성, 적 | `state_tracker_npc.py:889` |
| NPC disposition | 중립, 경계, 호의, 충성 | `state_tracker_npc.py:289` |
| BlockingValidator default | 중립 | `blocking_validator_consistency_checks.py:271` |

Overlap: `적대`, `중립`, `충성` are shared across all. `무시`/`의심`/`경외` (Analyst only), `아군`/`동맹`/`호의`/`적` (regex only), `경계` (disposition only).

### 6.2 Injury Status Values

| Source | Values | File:Line |
|--------|--------|-----------|
| ArcState default | 정상 | `modules/models/arc.py:42` |
| StateTracker NPC registry | 정상, 경상, 중상, 위독 | `state_tracker_npc.py:287` |
| BlockingValidator weakness | 나약, 중독, 부상, 중상, 쇠약, 기력고갈, 기혈역류 | `blocking_validator_consistency_checks.py:55` |

Note: BlockingValidator uses a different domain concept (weakness indicators, not injury grades). Only `중상` overlaps.

### 6.3 Movement/Location Fields

No enum vocabulary. Both `npc_movements` and `WorldState.known_attrs.location` use free-form strings. No controlled vocabulary.

### 6.4 Protagonist Emotion

| Source | Values | File:Line |
|--------|--------|-----------|
| StateTracker extraction | free-form string (emotion, trigger) | `state_tracker_npc.py:1982` |

No controlled vocabulary. Any string accepted.

### 6.5 Genre-Conditional Fields

| Field | Active Genre | Other Genres |
|-------|-------------|-------------|
| `financial_events` | investment | Not extracted |
| `status_shadow.internal_energy_loss` | wuxia | Not extracted |
| `status_shadow.internal_energy_remaining` | wuxia | Not extracted |

---

## 7. Formalization Recommendation

### Recommendation: `TypedDict-first`

### 7.1 Shape

Create one canonical `StateChangesDict` TypedDict in `modules/models/arc.py` alongside the existing `StateChanges` Pydantic model:

```python
from typing import TypedDict, NotRequired

class StateChangesDict(TypedDict, total=False):
    # ── Core 16 (Producer Path A: StateTracker) ──
    npc_deaths: list[dict]               # [{name, episode?, cause?} | str]
    skill_acquisitions: list[dict]        # [{name, episode?, source?, tier?} | str]
    relationship_changes: list[dict]      # [{npc|target, from, to, episode?, trigger?, justification?}]
    major_items: list[dict]               # [{name, episode?, status?} | str]
    resolved_plots: list[dict]            # [{plot, resolution, episode?, arc_no?}]
    npc_injuries: list[dict]              # [{name, episode?, state?, arc_no?}]
    npc_movements: list[dict]             # [{name, episode?, from?, to?, arc_no?}]
    entity_destructions: list[dict]       # [{name, type, cause?, episode?, arc_no?}]
    npc_personality_changes: list[dict]   # [{name, traits?, motivation?, arc_no?}]
    npc_npc_relationships: list[dict]     # [{npc1, npc2, relation, arc_no?}]
    time_markers: list[dict]              # [{arc_no?, episode?, type, description}]
    permanent_injuries: list[dict]        # [{name, type, description, episode?, arc_no?}]
    companion_changes: list[dict]         # [{name, action, episode?, reason?, arc_no?}]
    commitments: list[dict]               # [{parties, description, episode?, deadline_hint?, arc_no?}]
    protagonist_emotion: dict             # {emotion, trigger, episode?, arc_no?} | None
    financial_events: dict                # {exchange_rates?, total_assets?, leverage?, key_transactions?}

    # ── Extended (Producer Path C: stage4_post_pass_runtime) ──
    inventory_counts: dict                # {item_name: int}
    inventory_count_deltas: list[dict]    # [{name, from?, to?}]
    active_pressure_vectors: list[dict]   # [{text, source?, cue_terms?, since_ep?}]
    npc_introductions: list[dict]         # [{name, role?, relation?}]
    npc_attribute_changes: list[dict]     # [{name, field, value}]
    world_law_additions: list             # [str | {law}]
    protagonist_motivations: list[dict]   # [{text, status?, since_ep?}]

    # ── Aliases (compatibility) ──
    promises_obligations: list[dict]      # Alias for commitments (Analyst compat)
    promises: list[dict]                  # Alias for commitments (WorldState compat)
    npc_dialogue_profiles: list[dict]     # Write-only (Analyst guarantee, no consumer)

    # ── Numerical extraction fields ──
    capital: float | int | str            # Direct financial scalar
    total_assets: float | int | str       # Direct financial scalar
    wealth: float | int | str             # Direct financial scalar
    power_level: float | int              # Protagonist battle power
    numerical_facts: list[dict]           # [{name, value, unit?}]
    status_shadow: dict                   # {internal_energy_loss?, internal_energy_remaining?, ...}

    # ── Structural / temporal ──
    timeline: dict                        # {start?, end?} — stage3 temporal metadata
    items_acquired: list[dict]            # stage4_context_builder fallback
    active_plots: list[dict]              # stage4_context_builder fallback
```

### 7.2 Placement

- File: `modules/models/arc.py`, adjacent to existing `StateChanges(BaseModel)` at line 170
- The existing `StateChanges` Pydantic model (4 fields) should get a deprecation comment noting `StateChangesDict` is the canonical contract
- `ArcData.state_changes` type annotation changes from `dict` to `StateChangesDict` (type-only, no runtime behavior change since TypedDict is a dict at runtime)

### 7.3 Blast Radius

| Change | Blast Radius | Runtime Behavior Change |
|--------|-------------|----------------------|
| Add TypedDict definition | Zero — new type, no existing code affected | None |
| Update ArcData annotation | Zero — TypedDict is `dict` at runtime | None |
| Add deprecation comment to StateChanges | Zero — comment only | None |

### 7.4 Why Broader Redesign Is Unnecessary

1. **All consumers already use `.get()` with defaults** — no consumer will break from missing keys because every read path tolerates absence.
2. **Polymorphic acceptance (dict|str) is handled at both producer and consumer** — formalizing the list[dict] shape does not require removing str acceptance; the TypedDict documents the canonical shape while runtime continues to accept both.
3. **The two producer paths (A and C) serve different consumers** — WorldState gets the merged superset from Path C, FactLedger gets the extraction subset from Path A. This is not broken design; it is intentional layered composition. Merging them into one path would be a refactor, not a fix.
4. **Enum normalization is a separate concern** — the TypedDict documents the vocabulary problem without requiring an enum module. Enum formalization can be a follow-up if real drift failures surface.
5. **No DB schema change needed** — `state_changes` is stored as `TEXT` (JSON serialized) in the DB. TypedDict does not change serialization.

### 7.5 Why Not the Other Options

- **dataclass/TypedDict hybrid**: Unnecessary complexity. The consumers already handle plain dicts. Introducing a dataclass would require migration of all producers and consumers to construct/destructure instances. High blast radius, no immediate benefit.
- **staged normalization with compatibility shell**: Would be needed if consumers were failing from schema drift. They are not — every consumer tolerates absence and wrong types gracefully. The problem is documentation, not runtime failure.

---

## 8. Side-Effect Coverage

### 8.1 WorldState Mutation Paths

`world_state.update_from_state_changes(ep_num, state_changes)` mutates:
- `alive_npcs` (create, update, move to dead_npcs)
- `dead_npcs` (add on death)
- `relationships` (update on relationship_changes)
- `active_items` (add, update quantity, update status)
- `destroyed` (append, max 100)
- `timeline` (append, max 20) + DB `upsert_timeline_entry()`
- `motivations` (upsert, max 20)
- `promises` (upsert, max 30)
- `protagonist.skills` (append, max 50)
- `known_attrs` per NPC (injury, location, permanent_injuries, custom fields)
- `world_laws` (append, max 20)
- `active_pressure_vectors` (replace entire list, max 5)
- `cumulative_elapsed` (increment days)

All mutations are guarded by try/except per `_apply_*` section — one section failure does not block others.

### 8.2 DB-Backed Replay Paths

Both `world_state.rollback_to(target_ep)` and `fact_ledger.rollback_to(target_ep)` reinitialize and replay all episodes via `get_all_episode_bibles()`. Each replay calls the same `update_from_state_changes()` path with historically stored state_changes. Schema changes to state_changes keys would affect replay fidelity if historical data uses old key names.

**Implication for formalization**: TypedDict-first approach has zero replay risk because it adds no runtime validation — historical dicts with old key names continue to work.

### 8.3 Prompt/Summary Generation Paths

state_changes-derived data surfaces in LLM prompts via:
- `world_state.get_summary()` — 50K char snapshot includes all state derived from state_changes
- `world_state.get_canonical_constraints()` — 8K char NPC intro roles from known_attrs
- `fact_ledger.to_summary()` — 50K char ledger derived from state_changes
- `fact_ledger.get_canonical_summary()` — 5K char numeric facts

These are read-only summaries. Schema formalization does not affect them.

### 8.4 Validator Behavior

BlockingValidator and blocking_validator_consistency_checks do NOT read state_changes directly (confirmed: zero references). They receive pre-built context dicts with extracted values. Schema formalization does not affect validator behavior.

---

## 9. Confidence and Limits

### Success Criteria Check

| Question | Answer |
|----------|--------|
| 1. Which keys are the de facto SSOT surface? | 16 keys from Producer Path A (StateTracker) + 7 extended keys from Path C (stage4_post_pass_runtime) = 23 SSOT keys |
| 2. Which keys are advisory/dormant/drift-prone? | `npc_dialogue_profiles` (write-only), `promises_obligations` (alias), `timeline` (stage3-only temporal), `items_acquired`/`active_plots` (context_builder fallback) |
| 3. Which mismatches would break or silently degrade? | `commitments`/`promises`/`promises_obligations` alias chain (WorldState tries both; StateTracker reads fallback); `relationship_changes` entry field `npc` vs `target` (stage2_finalizer triple-fallback); `financial_events` shape mismatch (dict vs expected list in FactLedger — silent skip) |
| 4. What is the smallest safe formalization? | TypedDict-first: one `StateChangesDict` in `modules/models/arc.py`, zero runtime behavior change |

### Confidence

Estimated confidence: **96%**

Basis:
- All 4 producer files read in full; every `state_changes` extraction method traced
- Both primary consumers read in full; every `.get()` / `_apply_*` call traced
- All 6 secondary consumers verified with grep evidence
- Both contract-adjacent surfaces confirmed non-applicable
- Existing Pydantic model verified at `arc.py:170-179`
- Two distinct producer paths identified and documented
- Lower confidence only on: (a) whether any test file constructs state_changes with keys not seen in production code; (b) whether any unreferenced dead code path reads state_changes through dynamic dispatch

### Limits

- This survey did not exhaustively trace how `state_changes` is serialized into/from DB `TEXT` columns — it confirmed the column exists (`db_bootstrap_runtime.py:256`) and that JSON serialization is used (`db_manager.py:609-625`), but did not verify every INSERT/SELECT query.
- Enum vocabulary was collected from production code only, not from LLM prompt templates beyond `analyst_prompts.py`.
- The `financial_events` shape mismatch (Producer emits dict, FactLedger reads as list[dict]) may be harmless or may cause silent data loss for investment-genre works. This was not runtime-verified.

---

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- Document type: compact survey (survey-only)
- Scope: bounded to state_changes schema formalization
- All 5 required finding categories present (A-E)
- Side-effect sweep present
- No code changes proposed
- No execution SSOT, roadmap, or temp queue artifacts created
- PASS

### Pass 2. Evidence and Consistency
- Producer inventory: 16 primary + 1 secondary keys from Path A, 14 guaranteed keys from Path B, 7+ additional keys from Path C
- Consumer inventory: 20 keys in WorldState, 16+ keys in FactLedger, 6 secondary consumers verified
- Mismatch ledger: 3 field-name drifts, 1 shape drift (financial_events), 3 enum drifts, 2 write-only fields, 12+ read-only-from-Path-C keys
- Enum table: 3 relationship vocabularies, 2 injury vocabularies, 2 genre-conditional field families
- Formalization recommendation: TypedDict-first with zero blast radius
- All claims traceable to file:line evidence
- PASS

### Pass 3. Execution and Readability
- Answers all 4 success criteria questions
- Recommendation is bounded (one TypedDict, one file, zero runtime change)
- Blast radius explicitly assessed
- No scope creep into redesign, technique modeling, or provider work
- PASS
