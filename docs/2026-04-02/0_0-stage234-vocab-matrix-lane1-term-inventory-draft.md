# 0_0 Stage234 Vocab Matrix Lane 1: Cross-Stage Term Inventory

- Date: 2026-04-02
- Status: draft-bounded-partial-evidence
- Role: Opus Terminal 1 — cross-stage term inventory lane
- Mode: survey only, read-only only
- Source Surfaces:
  - `modules/domain/agents/arc_ensemble.py`
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/core/stage4_context_builder.py`
  - `config/prompts/ensemble.yaml`
- Related Surveys:
  - `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
  - `docs/2026-04-02/0_0-stage3-static-global-bounded-survey.md`
  - `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
- Master Order: `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-parallel-master-order.md`

---

## 1. Coverage

### Surfaces Read

| Surface | Lines Read | Key Vocabulary Extracted |
|---|---|---|
| `arc_ensemble.py` | L1-500 | state_constraints, joint_docs, status_shadow, tactical_doc, state_changes, constraint_block, beat_sequence, hybrid_composition, pacing_decision, episode_details, energy_system_block |
| `blueprint_ensemble.py` | L1-500 | scene_breakdown, integrated_scenario, constraint_block (dict), arc_focus, prev_info, hud_context, core_tension, ending_hook, ending_state, protagonist_state, start_location/end_location, time_flow |
| `stage4_context_builder.py` | L1-500, grep | mandatory_context, retrieval_plan, canonical_constraints, world_state_summary, fact_ledger_summary, chain_link_section, cumulative_bible, arc_constraint_summary, coverage_warnings, tier0/tier1/tier2_parts |
| `ensemble.yaml` | L1-450 | ENSEMBLE_ARC_PROMPT fields, BLUEPRINT_GENERATION_PROMPT fields, state_changes sub-fields (20+ categories), investment_calc, episode_details |

### Supplemental Grep Coverage

| Term Family | Files Found |
|---|---|
| `fix_pack / post_select_conflict / actual_truth / final_state_updates / active_pressure_vectors` | 30 files across modules/ |
| `constraint_summary` | 8 files (arc_ensemble, blueprint_constraint_compiler, stage3_orch, stage4_context_builder, stage2_finalizer, models/arc, stage2_preflight, manuscript_truth_report) |
| `semantic_carryover / beat_sequence / hybrid_composition / prohibition_summary / entity_registry` | 20 files |
| `pacing_signal / pacing_decision / pacing_analyzer / pacing_notes` | 14 files |

---

## 2. Findings

### 2A. Cross-Stage Term Inventory Table

The table below catalogs the major repeated concepts across Stage2/3/4. Each row identifies:
- The canonical concept
- The term(s) used at each stage
- Whether the terms are true equivalents, partial overlaps, or independent concepts

| # | Concept Family | Stage2 Term(s) | Stage3 Term(s) | Stage4 Term(s) | Equivalence Class |
|---|---|---|---|---|---|
| 1 | **Episode Mission** | `tactical_doc` (prose, primary authority) | `arc_focus` (re-derived from tactical_doc via extraction) | `arc_tactical` (re-serialized, passed to CW) | **Partial overlap** — same content origin, different packaging at each stage |
| 2 | **State Constraints** | `state_constraints` (structured JSON: arc_start_state, arc_end_state, items_acquired, items_consumed, investment_calc) | consumed via `constraint_block` dict → `BlueprintConstraintCompiler._format_constraints()` | consumed indirectly through blueprint prose; not passed as structured JSON to CW | **True equivalent at S2/S3 boundary, lossy at S3/S4 boundary** |
| 3 | **Joint Documents** | `joint_docs` (final_location, physical_inventory, world_joint) | not consumed by name; subsumed into `prev_info` | not consumed by name; subsumed into carryover context | **Partial overlap** — identity lost after Stage2 |
| 4 | **State Changes** | `state_changes` (20+ sub-fields: npc_deaths, skill_acquisitions, relationship_changes, timeline, resolved_plots, npc_injuries, npc_movements, entity_destructions, npc_personality_changes, npc_npc_relationships, npc_introductions, numerical_facts, time_markers, permanent_injuries, companion_changes, commitments, protagonist_emotion, npc_dialogue_profiles, financial_events, episode_details) | consumed for NPC roster discovery and constraint enforcement; compressed | consumed for entity discovery, NPC roster, state tracker updates; demotion to advisory | **True equivalent at S2 origin, progressively demoted downstream** |
| 5 | **Status Shadow** | `status_shadow` (genre-specific expected state snapshot) | not directly consumed by name | not directly consumed by name | **Stage2-local term** — does not survive boundary |
| 6 | **Constraint Summary** | `constraint_summary` (Stage2 → downstream prohibition) | `arc_constraint_summary` in BlueprintConstraintCompiler; advisory strength | `arc_constraint_summary` in Stage4ContextBuilder; Tier-0 hard prohibition strength | **Same term, strength inversion** — advisory in S3, hard in S4 |
| 7 | **Beat Sequence** | `beat_sequence` (per-episode narrative beat list) | dropped at S2→S3 boundary | not consumed | **Dead field at boundary** |
| 8 | **Hybrid Composition** | `hybrid_composition` (primary/secondary/mixing_logic) | dropped at S2→S3 boundary | not consumed | **Dead field at boundary** |
| 9 | **Pacing Decision** | `pacing_decision` (pace_mode, ep_count_reasoning, density_focus) | `pacing_notes` in blueprint; `pacing_signals` as input | `pacing_analyzer` module in Stage4Context | **Partial overlap** — concept survives but term and structure change at each stage |
| 10 | **Scene Breakdown** | (not produced) | `scene_breakdown` (dict of scenes with type, title, location, characters, summary, tension_level, key_events) | consumed as blueprint dict; `scene_breakdown` or `scenes` keys extracted | **Stage3-origin term, consumed as-is in S4** |
| 11 | **Integrated Scenario** | (not produced) | `integrated_scenario` (1000+ char prose) | consumed as blueprint prose; `integrated_scenario` key extracted | **Stage3-origin term, consumed as-is in S4** |
| 12 | **Ending Hook / Ending State** | (not produced) | `ending_hook`, `ending_state` (location, timeline, protagonist_status) | consumed as carryover reference | **Stage3-origin term** |
| 13 | **Protagonist Config** | protagonist_name, protagonist_config (from bible) | protagonist_name, protagonist_instructions | protagonist_name via `_resolve_protagonist_name()` (bible/world_state/callback) | **True equivalent** — stable across all stages |
| 14 | **Constraint Block** | `constraint_block` (string, pre-formatted prohibition/constraint text) | `constraint_block` (dict, compiled by BlueprintConstraintCompiler with must_focus, stop_line, arc_constraint_summary, immutable_fact_carryover) | (not consumed by this name; subsumed into mandatory_context) | **Same name, different type** — string in S2, dict in S3 |
| 15 | **Prohibition Summary** | `prohibition_summary` (formatted forbidden items/actions) | consumed as part of constraint_block | consumed indirectly via mandatory_context Tier-0 | **Partial overlap** — name stable S2→S3, identity lost in S4 |
| 16 | **Entity Registry** | `entity_registry` (NPC/entity dict passed to arc prompt) | (not consumed by name; NPC data flows through state_tracker) | NPC roster via `_collect_npc_roster()`, `_collect_arc_state_entities()` | **Partial overlap** — same data, different access patterns per stage |
| 17 | **HUD / State Display** | (not produced) | `hud_context` via `_build_hud_context()` | `hud_report` in Stage4EpisodeStatePayload | **Partial overlap** — same concept, different names |
| 18 | **World State** | (not produced; world state is upstream persistent) | (not consumed directly) | `world_state_summary` via WorldStateManager, Tier-0 injection | **Stage4-dominant term** |
| 19 | **Fact Ledger** | (not produced; fact ledger is upstream persistent) | (not consumed directly) | `fact_ledger_summary` via FactLedger, Tier-0 injection | **Stage4-dominant term** |
| 20 | **Chain Link** | (not produced) | (not consumed) | `chain_link_section` via DB anchor `chain_link_{ep}` | **Stage4-only term** |
| 21 | **Cumulative Bible** | (not produced; bible is upstream persistent) | (not consumed directly) | `cumulative_bible` via DBManager, dead_npcs extraction | **Stage4-dominant term** |
| 22 | **Fix Pack** | (not produced) | (not produced) | `fix_pack` (Director-authored or runtime-backfilled: patch_targets, must_fix, do_not_regress, success_condition, target_kind) | **Stage4-only term** |
| 23 | **Post-Select Conflict** | (not produced) | (not produced) | `post_select_conflict` (contract for post-selection contradiction handling, fix_scope routing) | **Stage4-only term** |
| 24 | **Actual Truth** | (not produced) | (not produced) | `actual_truth` (Manager-authored episode state: martial_arts, active_pressure_vectors, etc.) | **Stage4-only term** |
| 25 | **Final State Updates** | (not produced) | (not produced) | `final_state_updates` (Director-authored episode state update dict) | **Stage4-only term** |
| 26 | **Active Pressure Vectors** | (not produced) | (not produced; derived from blueprint) | `active_pressure_vectors` (blueprint-derived, manuscript-filtered, injected into actual_truth and world_state) | **Stage4-only term, blueprint-sourced** |
| 27 | **Mandatory Context** | (not produced) | (not produced) | `mandatory_context` (assembled Tier-0/1/2 context for CW/Director) | **Stage4-only term** |
| 28 | **Retrieval Plan** | (not produced) | (not produced) | `retrieval_plan` via ContextAdvisor (RetrievalSources, coverage) | **Stage4-only term** |
| 29 | **Semantic Carryover** | `semantic_carryover` (structured carryover from prior arc) | not consumed by name | not consumed; dead/low-signal field | **Dead field** |
| 30 | **Episode Details** | `episode_details` (per-episode key scenes list) | consumed via `_resolve_blueprint_arc_focus()` for per-episode extraction | consumed indirectly via arc_data | **Partial overlap** — thin/weak field |
| 31 | **Immutable Fact Carryover** | (not produced by name) | `immutable_fact_carryover` in BlueprintConstraintCompiler | (not consumed by name in S4) | **Stage3-local term** |
| 32 | **Must Focus / Stop Line** | (not produced by name) | `must_focus`, `stop_line` in constraint_block dict | (not consumed by name; subsumed) | **Stage3-local terms** |
| 33 | **Volume Strategy** | `vol_strategy` (string) | (consumed as pass-through in arc_focus context) | (not consumed by name) | **Stage2-origin, boundary-lossy** |

### 2B. Concept Family Classification

Based on the inventory, concepts cluster into five families:

#### Family A: Cross-Stage Hard Truth (stable identity, Stage2-origin)
- `state_constraints`, `protagonist_name/config`, `arc_no/ep_start/ep_end/ep_count`
- These survive all boundaries with largely stable identity.

#### Family B: Cross-Stage Mission (content survives, packaging changes)
- `tactical_doc` → `arc_focus` → `arc_tactical`
- `constraint_summary` → `arc_constraint_summary` (strength inversion)
- `prohibition_summary` → constraint prose
- Content is the same; name, strength, and structure change at each boundary.

#### Family C: Stage-Boundary Dead/Demoted Fields
- `beat_sequence`, `hybrid_composition`, `semantic_carryover`, `status_shadow`, `vol_strategy`
- Produced at Stage2, dropped or ignored at the S2→S3 boundary.

#### Family D: Stage3-Origin Terms (consumed in S4)
- `scene_breakdown`, `integrated_scenario`, `ending_hook`, `ending_state`, `must_focus`, `stop_line`, `immutable_fact_carryover`
- Born in Stage3, consumed as blueprint dict in Stage4.

#### Family E: Stage4-Only Terms (consumer/finalization vocabulary)
- `fix_pack`, `post_select_conflict`, `actual_truth`, `final_state_updates`, `active_pressure_vectors`, `mandatory_context`, `retrieval_plan`, `world_state_summary`, `fact_ledger_summary`, `chain_link_section`, `cumulative_bible`
- Born and consumed entirely within Stage4.

### 2C. Which Terms Are True Equivalents vs Partial Overlaps

**True equivalents (same concept, same meaning, stable across stages):**
- `protagonist_name` / `protagonist_config`
- `arc_no`, `ep_start`, `ep_end`, `ep_count`
- `scene_breakdown`, `integrated_scenario` (S3→S4 passthrough)
- `state_constraints` (S2→S3 structured pass)

**Partial overlaps (same concept, different name/strength/structure):**
- `tactical_doc` / `arc_focus` / `arc_tactical` — same content, different packaging
- `constraint_summary` / `arc_constraint_summary` — same content, **strength inversion** (advisory S3 vs hard S4)
- `constraint_block` — string in S2, dict in S3, absorbed in S4
- `entity_registry` / NPC roster / `_collect_npc_roster()` — same data, different access
- `hud_context` / `hud_report` — same concept, different names
- `pacing_decision` / `pacing_signals` / `pacing_analyzer` / `pacing_notes` — concept survives, structure changes
- `state_changes` — produced in S2, consumed in S3 (compressed), consumed in S4 (entity discovery + advisory demotion)

**Not equivalents despite similar names:**
- `constraint_block` string (S2) vs `constraint_block` dict (S3) — same name, fundamentally different type and role
- `fix_pack` (Director-authored) vs `fix_pack` (runtime-backfilled) — same name, different provenance within S4
- `final_state_updates` (Director) vs `actual_truth` (Manager) — both describe post-episode state but from different owners

### 2D. Concept Families Needing Shared Canonical Vocabulary First

**Priority 1 — Episode Truth Post-Finalization:**
- `final_state_updates`, `actual_truth`, `world_state` are three names for overlapping slices of the same episode reality
- These need a single canonical vocabulary before any simplification work
- This is the triple-split problem identified in the Stage4 consumer survey

**Priority 2 — Authority Strength Vocabulary:**
- `hard truth`, `mission truth`, `carryover truth`, `advisory` are used in surveys but do not exist as formal contract terms in code
- `constraint_summary` exhibits strength inversion because there is no shared vocabulary for authority strength
- `IMMUTABLE > HARD CONSTRAINT > EXPECTED CONTINUITY > ADVISORY` exists in Stage3 BlueprintConstraintCompiler but is not cross-stage

**Priority 3 — Episode Mission Authority:**
- `tactical_doc` → `arc_focus` → `arc_tactical` name drift obscures that these are the same content
- A canonical name for "the narrative mission for this episode" would reduce translation pressure

**Priority 4 — Repair/Finalization Contract:**
- `fix_pack`, `post_select_conflict`, `authoritative_fix_scope`, `fix_scope` are Stage4-local terms that describe repair routing
- These should enter the cross-stage matrix as shared vocabulary if contract normalization proceeds

### 2E. Stage4 Consumer-Seam Vocabulary Integration

The following Stage4-only terms must be included in the cross-stage matrix rather than treated as local glossary, because they describe truths that originate upstream:

| Stage4 Term | Upstream Origin | Why Cross-Stage |
|---|---|---|
| `fix_pack` | Director decision based on S2/S3 constraint violations | Repair targets reference S2/S3 constraint vocabulary |
| `post_select_conflict` | Contradiction between S3 blueprint and S4 manuscript | Conflict taxonomy depends on S2/S3 contract definitions |
| `actual_truth` | Manager-assembled from S2 state_changes + S4 runtime | Reconciliation depends on shared vocabulary with S2 state_constraints |
| `final_state_updates` | Director-observed from S4 generation | Overlaps S2 state_constraints and S4 actual_truth; needs shared field family |
| `active_pressure_vectors` | S3 blueprint-derived, S4 manuscript-filtered | Blueprint origin makes this cross-stage |

---

## 3. Non-Issues

1. **Protagonist identity** — `protagonist_name` and `protagonist_config` are stable across all three stages. No drift detected.
2. **Scene breakdown / integrated_scenario** — These Stage3-origin terms pass cleanly into Stage4 as blueprint dict keys. No name collision or strength inversion.
3. **Stage numbering and episode numbering** — `arc_no`, `ep_start`, `ep_end`, `ep_count` are stable hard truth with no term drift.
4. **Genre typing** — `GenreTypes` enum (WUXIA, HUNTER, INVESTMENT, FANTASY) is stable across stages. No term conflict.
5. **DB persistence boundary** — The Stage3→Stage4 handoff via DB-serialized blueprint dict is architecturally clean. The issue is semantic contract, not transport.

---

## 4. Verdict

**high-term-drift**

Justification:
- 33 major concepts were inventoried across Stage2/3/4
- Of these, only 4 are true equivalents with stable identity across all stages
- 10+ concepts exhibit partial overlap with name, strength, or structure changes
- 5 concepts are dead/demoted at the first boundary (S2→S3)
- The most damaging drift is not naming noise but **strength inversion** (`constraint_summary` advisory in S3 vs hard in S4) and **triple split** (`final_state_updates` / `actual_truth` / `world_state`)
- Stage4-only finalization vocabulary (5 terms) describes truths that originate upstream but has no shared cross-stage vocabulary

The evidence strongly supports:
1. **Contract normalization** as the highest-priority next step
2. **A shared authority-strength vocabulary** (hard/mission/carryover/advisory) that is enforced in code, not just surveys
3. **Owner consolidation** for the triple state-truth split

---

## 5. Stop

read-only lane complete; no files mutated

---

## 3-Pass Audit Record

Pass 1 (structure and scope):
- Stayed within term inventory lane scope
- Did not encroach on owner-strength matrix (Lane 2), transport drift (Lane 3), or vertical slices (Lane 4)
- Included Stage4 consumer-seam vocabulary as required by master order

Pass 2 (evidence and consistency):
- All terms traced to specific code surfaces and grep evidence
- Used existing stage survey findings as baseline rather than re-proving
- Equivalence classifications cross-checked against code type signatures (string vs dict for constraint_block)

Pass 3 (execution and readability):
- Inventory table has 33 entries with clear equivalence classification
- Five concept families identified with clear ordering
- Verdict with justification connects directly to inventory evidence

Confidence: 94%
(2% deducted: did not exhaustively read all 30 files found by grep for fix_pack family; relied on representative samples and existing Stage4 survey. 4% reserved: some partial-overlap classifications could shift to dead-field or true-equivalent with deeper vertical slice evidence from Lane 4.)
