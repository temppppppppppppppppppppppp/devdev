# Per-Work Registry Need Compact Survey

Date: 2026-03-27
Status: final
Type: system-track compact survey (survey-only, no code changes)
Scope: whether a per-work registry layer is needed, what it would own, how it differs from existing systems
Excluded: wuxia-only design bias, narrative pipeline execution, runtime optimization

Evidence Basis:
- `modules/core/fact_ledger.py`
- `modules/core/world_state.py`
- `modules/core/reference_anchor.py`
- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/validation/continuity_validator.py`
- `modules/validation/blocking_validator.py`
- `modules/validation/blocking_validator_entity_checks.py`
- `modules/domain/agents/state_extractor.py` (EntityRegistry)
- `modules/core/genre_guards/work_guard.py`
- `modules/core/db_manager.py` (episode_bibles, cumulative_bible, encyclopedia)
- `docs/2026-03-26/wuxia-combat-scene-readiness-compact-survey.md`
- `docs/2026-03-26/wuxia-combat-quality-probe-report.md`
- `docs/2026-03-26/lookback-boundary-window-b-probe-report.md`

Commit State:
- Baseline Commit: `07e9aaf8`

## 1. Findings

### 1.1 Current Entity-Tracking Systems Inventory

The codebase already operates **7 distinct per-work entity-tracking systems**. All are per-work scoped via separate `ProjectContext` / `project_data.db` instances.

| System | Storage | Update Trigger | Scope |
|--------|---------|----------------|-------|
| **FactLedger** | SQLite anchor `fact_ledger` | Stage 4 post-pass | 5 categories: characters, numbers, items, locations, organizations |
| **WorldStateManager** | SQLite anchor `world_state` | Stage 4 post-pass | 13+ categories: protagonist, alive/dead NPCs, relationships, items, plots, timeline, promises, motivations, pressure vectors, world laws, elapsed time |
| **StateTracker** | In-memory + DB anchors | Arc extraction (Stage 2) | 20+ registries: NPC registry, skills, items, companions, emotions, dialogue profiles, NPC-NPC relationships, genre-specific registries |
| **EntityRegistry** (StateExtractor) | Ephemeral (LLM cache) | Arc extraction (LLM) | 5 categories: characters, organizations, locations, objects, concepts |
| **Reference Anchors** | SQLite anchor `reference_anchors` | Stage 4 post-generation | 8 event types: combat, item, relationship, location, power, revelation, injury, decision |
| **Episode Bible** | SQLite table `episode_bibles` | Post-manuscript | Per-episode delta: new/lost items, new NPCs, deaths, relationship changes, state changes, time, reveals |
| **WorkGuard** | YAML file `work_guard.yaml` | Manual (design-time) | Character constraints, role fit, tracking slots, mandatory scene engines |

### 1.2 Coverage Matrix — Investigation Question 1

| Fact Category | Already Covered By | Coverage Level |
|---------------|-------------------|----------------|
| **Static identity** (name, role, status) | WorldState `alive_npcs` (role, relation, personality, location, first_seen_ep, role_at_intro, known_attrs), FactLedger `characters` (status, role, relationship), EntityRegistry `characters` (name, role, context), Master Bible BI `KeyNPCs` | **Full** — 4 systems track this |
| **Ownership** (item possession) | WorldState `active_items` (ep_acquired, status, quantity), FactLedger `items` (owner, status, quantity), StateTracker `global_items` / `acquired_items` / `consumed_items` / `item_state_registry`, Episode Bible `new_items` / `lost_items` | **Full** — 4 systems track this |
| **Injuries** | StateTracker `injuries` (정상/경상/중상/위독), StateTrackerNPC `extract_npc_injuries` + `extract_permanent_injuries` (amputation/blindness/scars), WorldState `protagonist.injuries` + NPC `known_attrs.injury` + `known_attrs.permanent_injuries`, Reference Anchors `injury` type (critical, preserved indefinitely), ContinuityValidator injury-action consistency, Wuxia Guard `injury_action_limits` | **Full** — 6 systems participate |
| **Relationships** | WorldState `relationships` (protagonist↔NPC) + NPC `known_attrs`, StateTracker `npc_npc_relationships` (NPC↔NPC network), FactLedger `characters.relationship` | **Full** — 3 systems with two-axis coverage (protag↔NPC and NPC↔NPC) |
| **Event history** | WorldState `timeline` + `cumulative_elapsed` + `active_plots` + `resolved_plots`, FactLedger per-entity `history[]` (max 100 per entity), Reference Anchors 8 event types with ep-linked summaries (max 1000), Episode Bible `key_events` + `reveals` + `causal_links` | **Full** — 4 systems, different granularity |
| **Skill/technique use history** | StateTracker `protagonist_skills` + `skill_acquisitions` (skill→arc mapping), WorldState `protagonist.skills` (max 50), Wuxia Guard `realm_technique_limits` (realm gates technique access) | **Partial** — which techniques are *learned* is tracked; which techniques were *used in a specific fight* is not |
| **Organization/sect membership** | FactLedger `organizations` (name, status, leader), EntityRegistry `organizations` (name, type, context), WorldState NPC `role_at_intro` (may include faction implicitly) | **Partial** — organizations exist as entities, but no explicit "character X belongs to organization Y" membership edge |

### 1.3 What a Per-Work Registry Would Add

A hypothetical per-work registry would need to add value **beyond** what 7 existing systems already provide. The only candidate gaps are:

#### Gap 1: Cross-Episode Fight Geography (from wuxia combat survey)
- **What's missing**: No structured field persists spatial progression within a sustained fight (e.g., "pushed from hall to courtyard to cliff edge")
- **Current state**: Spatial keywords exist in `ActionSceneEvaluator` (advisory), geography exists in narrative text (not structured)
- **Combat probe result**: Geography was adequate for closed-space combat (tent). Open-field multi-episode battles remain untested.
- **Could be solved by**: Adding an optional `fight_geography` field to WorldState or blueprint contract — **no new system needed**

#### Gap 2: Technique Usage History Within a Fight
- **What's missing**: No tracking of which specific techniques have been used/revealed during a multi-episode fight
- **Current state**: `protagonist_skills` tracks what's learned. `realm_technique_limits` gates access. But no "technique X was already shown in EP5 scene 3" record.
- **Combat probe result**: Not a problem in the probed window (protagonist was awakening — limited repertoire). Persists as risk for established fighters.
- **Could be solved by**: Extending StateTracker with a `technique_usage_log` per arc — **no new system needed**

#### Gap 3: Explicit Organization Membership Edges
- **What's missing**: No structured "character X is a member of sect Y with rank Z" mapping
- **Current state**: FactLedger tracks organizations as entities. NPC `role_at_intro` or `known_attrs` may carry faction implicitly. But no queryable membership graph.
- **Could be solved by**: Adding a `memberships` field to WorldState NPC entries — **no new system needed**

#### Gap 4: Cross-Episode Tactical Escalation Validation
- **What's missing**: ActionSceneEvaluator checks within-manuscript escalation but not whether EP6's fight escalates beyond EP5's climax
- **Current state**: Tension levels are tracked per blueprint scene but not persisted for cross-episode comparison
- **Could be solved by**: Extending Reference Anchors or ActionSceneEvaluator to carry forward previous escalation state — **no new system needed**

### 1.4 Already Covered — No Gap

| Often-Assumed Gap | Actually Covered By |
|-------------------|---------------------|
| "NPC state is scattered" | WorldState `alive_npcs` has 8+ fields per NPC including `known_attrs` dict with structured change tracking |
| "Item state is scattered" | WorldState `active_items` + FactLedger `items` + StateTracker `item_state_registry` — triple-covered |
| "Death tracking is fragile" | StateTracker + WorldState + FactLedger all independently track NPC death with arc/episode/cause |
| "No cumulative state" | Episode Bible `get_cumulative_bible(up_to_ep)` provides incremental accumulation with LRU cache |
| "No cross-episode anchors" | Reference Anchors preserve 1000 events with critical types (injury, item, power) kept indefinitely |
| "Lookback window loses facts" | Lookback probe report confirms: FactLedger + WorldState persist facts regardless of validator window. EP1 facts survived at EP12 with 0 contradictions. |
| "BI/TR entities are not ingested" | Master Bible → AssetLibrary → Encyclopedia pipeline. StateExtractor extracts entity registry from each arc. |

### 1.5 Overlap Problem — Existing Redundancy

The current architecture has the **opposite** of a missing-registry problem. Entity identity is tracked in **too many places simultaneously**:

| Entity Aspect | Systems Tracking It | Redundancy |
|---------------|---------------------|------------|
| NPC name/status | WorldState, FactLedger, StateTracker, EntityRegistry | 4x |
| NPC death | WorldState, FactLedger, StateTracker | 3x |
| Item ownership | WorldState, FactLedger, StateTracker, Episode Bible | 4x |
| Relationships | WorldState, StateTracker, FactLedger | 3x |
| Protagonist skills | WorldState, StateTracker | 2x |

This redundancy is intentional (defense-in-depth for continuity) but means adding an 8th system would increase coordination cost without solving a novel problem.

## 2. Investigation Question Answers

### Q1. What facts are already covered?

- Static identity: **Full** (4 systems)
- Ownership: **Full** (4 systems)
- Injuries: **Full** (6 systems participate)
- Relationships: **Full** (3 systems, two-axis)
- Event history: **Full** (4 systems, different granularity)
- Skill/technique use history: **Partial** (learned = tracked, used-in-fight = not)
- Organization/sect membership: **Partial** (orgs exist as entities, membership edges implicit)

### Q2. What gaps remain that a per-work registry would uniquely solve?

**None that require a new system.** The 4 identified gaps (fight geography, technique usage, org membership, cross-episode escalation) are field-level extensions to existing systems. They do not require a new architectural layer.

### Q3. Is a per-work registry materially different from a character sheet?

**No.** The current distributed system already serves as a multi-layered character sheet:
- WorldState `alive_npcs` = dynamic character sheet (role, personality, injuries, location, relationships)
- FactLedger `characters` = event-sourced character history
- StateTracker `npc_registry` = arc-scoped extraction cache
- WorkGuard `character_constraints` = design-time behavioral constraints
- Master Bible BI `KeyNPCs` = initial character specification

A per-work registry that consolidates these would be a read-only aggregation facade, not a new data source. The write authority already exists in WorldState (for dynamic state) and FactLedger (for event history).

### Q4. Should the registry be seeded from BI, updated from TR, and verified from manuscript?

This pattern **already operates**:
- Seeded from BI: Master Bible → AssetLibrary → Encyclopedia → Validation Context
- Updated from generation: Arc → StateExtractor → EntityRegistry + state_changes → WorldState/FactLedger
- Verified from manuscript: ContinuityValidator, BlockingValidator, Director contradiction checks

Adding a per-work registry into this flow would add a 3rd persistence path for the same data (alongside WorldState and FactLedger), increasing write-back complexity without new coverage.

### Q5. Which parts should remain in existing systems vs move to registry?

**All parts should remain in existing systems.** No transfer is justified because:
- WorldState is the authoritative NPC/item/plot state (updated per episode, DB-persisted)
- FactLedger is the authoritative event-sourced history (max 100 per entity, DB-persisted)
- StateTracker is the authoritative arc-extraction cache (volatile, regenerated from arcs)
- Reference Anchors are the authoritative cross-episode event markers (DB-persisted, critical types preserved indefinitely)

Moving any of these to a per-work registry would break the current update/query contracts without adding coverage.

### Q6. Is the right next move no action, design memo, or execution SSOT?

**No action** on a per-work registry.

If the 4 field-level gaps are deemed important enough to address (they are not blocking production today):
- Fight geography → design memo scoped to WorldState or blueprint contract extension
- Technique usage → design memo scoped to StateTracker extension
- Org membership → design memo scoped to WorldState NPC field extension
- Cross-episode escalation → design memo scoped to ActionSceneEvaluator or Reference Anchors

Each of these is a **small, bounded field addition** to an existing system, not a new architectural layer.

## 3. Classification

### Already Covered by Existing Systems

1. NPC static identity (name, role, status, first appearance) — WorldState, FactLedger, EntityRegistry, BI
2. NPC dynamic state (injuries, personality, location, relationships) — WorldState known_attrs, StateTracker
3. NPC death tracking and enforcement — StateTracker + WorldState + FactLedger + BlockingValidator
4. Item ownership, acquisition, consumption, destruction — WorldState + FactLedger + StateTracker + Episode Bible
5. Protagonist skill acquisition history — StateTracker + WorldState
6. Relationship network (protagonist↔NPC and NPC↔NPC) — WorldState + StateTracker + FactLedger
7. Event timeline and causality — WorldState timeline + FactLedger history + Reference Anchors + Episode Bible
8. Cross-episode fact survival — FactLedger + WorldState persist beyond validator lookback window (confirmed by EP12 probe)
9. Organization entity tracking — FactLedger organizations + EntityRegistry
10. Cumulative state assembly — Episode Bible `get_cumulative_bible()` with LRU cache

### Partially Covered

1. **Skill/technique usage tracking** — which techniques are *learned* is tracked; which were *used in a specific fight scene* is not
2. **Organization membership edges** — organizations exist as entities; "character X belongs to org Y" is implicit in NPC role, not a queryable edge
3. **Fight geography persistence** — spatial terms exist in narrative text and ActionSceneEvaluator keywords; not persisted as structured state

### Clearly Missing

1. **Per-fight technique usage log** — no system records "technique X was used in EP5 scene 3, technique Y in EP6 scene 1" for repetition detection
2. **Cross-episode tactical escalation state** — ActionSceneEvaluator scores within-manuscript only; no carry-forward of previous episode's peak escalation
3. **Structured fight geography field** — no persistent "current fight location" that validators can check across episodes

## 4. Risk Assessment

| Proposed Action | Risk | Justification |
|----------------|------|---------------|
| Add per-work registry (new system) | **High** — adds 8th entity-tracking system, increases write-back coordination, breaks no gap that existing systems can't address | Not justified |
| Extend existing systems (field additions) | **Low** — bounded changes to WorldState, StateTracker, or Reference Anchors | Justified if gaps manifest as production failures |
| No action | **Acceptable** — combat probe passed; lookback probe passed; gaps are in untested multi-episode open-field battle scenarios | Current recommendation |

## 5. Recommendation

**No action.**

The per-work registry need is low. The codebase already has 7 per-work entity-tracking systems with substantial overlap. The 3 clearly missing capabilities (technique usage log, cross-episode escalation, fight geography) are small field-level extensions to existing systems, not an architectural gap requiring a new layer.

The wuxia combat probe (EP1-EP3 closed-space combat) passed cleanly. The lookback probe (EP1 facts at EP12) passed with 0 contradictions. The identified gaps have not manifested as production failures.

If a future probe (multi-episode open-field battle) reveals actual drift from these gaps, the correct response is a targeted design memo for the specific extension (fight geography field in WorldState, or technique usage in StateTracker), not a new per-work registry system.

---

## 3-Pass Audit Record

Pass 1. Structure and Scope
- Survey type correct (compact survey, no code changes)
- Scope explicit: per-work registry need assessment against 7 existing systems
- All 6 investigation questions answered
- All required evidence surfaces inspected via 3 parallel exploration agents
- Classification into already-covered / partially-covered / clearly-missing is explicit
- PASS

Pass 2. Evidence and Consistency
- FactLedger schema verified: 5 entity categories, DB anchor `fact_ledger`, Stage 4 update trigger
- WorldState schema verified: 13+ categories, `_INIT_STATE` with 9 initial fields, DB anchor `world_state`
- StateTracker verified: 20+ registries, `EpisodeState` dataclass, `full_extract_from_arcs()` with 17 extraction methods
- EntityRegistry verified: ephemeral LLM cache, 5 categories, `extract_cumulative_state()` accumulation
- Reference Anchors verified: 8 types, max 1000, critical types preserved indefinitely
- Episode Bible verified: `episode_bibles` table, `get_cumulative_bible()` with LRU cache
- WorkGuard verified: `work_guard.yaml`, `character_constraints`, `role_fit_constraints`
- Combat probe findings correctly cited: PASS at EP1-EP3, geography adequate for closed-space
- Lookback probe findings correctly cited: PASS at EP12, 0 contradictions, EP1 facts survived
- Overlap counts verified against agent exploration results
- No overclaim: gaps are stated as "not tested in production" rather than "confirmed failures"
- PASS

Pass 3. Execution and Readability
- Single recommendation: no action
- Clear separation of covered / partially covered / missing
- No scope creep into execution SSOT or code changes
- Escalation path explicit: if future probe reveals drift → targeted design memo, not new system
- PASS

Estimated confidence: 97%

---

- Per-work registry need: **low**
- Dominant uncovered seam: **per-fight-technique-usage-and-geography-not-persisted**
- Should Codex open an execution SSOT now: **no**
