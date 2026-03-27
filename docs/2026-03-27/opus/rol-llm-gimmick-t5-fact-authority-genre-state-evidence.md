Date: 2026-03-27
Document Type: evidence manifest (T5 lane)
Lane: Fact Authority / Genre Gimmick / Contract State
Parent Report: `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state.md`

## 1. Path Inventory

### Primary Scope Files

| File | Lines | Role |
|------|-------|------|
| `modules/core/stage3_orchestrator.py` | ~2600 | Stage 3 orchestration, lazy init, dead-NPC pre-check, semantic context assembly |
| `modules/core/world_state.py` | 1319 | WorldStateManager: canonical NPC state, summaries, rollback |
| `modules/core/fact_ledger.py` | 862 | FactLedger: numeric SSOT, character/item/location/org tracking |
| `modules/domain/agents/state_tracker.py` | 1668 | Main facade: episode state DAG, genre registries, extraction orchestrator |
| `modules/domain/agents/state_tracker_npc.py` | 2204 | NPC registry, death tracking, skill acquisition, relationships, permanent injuries |
| `modules/domain/agents/state_tracker_plots.py` | 963 | Resolved plots, entity destructions, item state, timeline, commitments |
| `modules/domain/agents/state_tracker_financial.py` | 124 | Investment-only financial number registry |
| `modules/validation/blocking_validator.py` | 216 | Validator facade: aggregation of 14 checks |
| `modules/validation/blocking_validator_entity_checks.py` | 491 | Entity checks: dead NPC, unowned item, damaged item, destroyed location |
| `modules/validation/blocking_validator_scene_checks.py` | 492 | Scene checks: length, scope, completeness, cliffhanger |
| `modules/validation/blocking_validator_consistency_checks.py` | 444 | Consistency checks: physical, authority, relationship, information, wuxia realm |
| `modules/core/genre_guards/__init__.py` | 86 | Guard factory: composition chain |
| `modules/core/genre_guards/base_guard.py` | 861 | Abstract base: consistency validation framework |
| `modules/core/genre_guards/wuxia_guard.py` | 662 | Wuxia: realm hierarchy, technique limits, purism |
| `modules/core/genre_guards/work_guard.py` | 964 | Work-level override wrapper |
| `modules/core/genre_guards/style_guard.py` | 173 | Style-level wrapper |
| `modules/core/genre_guards/hunter_guard.py` | 867 | Hunter-specific rules |
| `modules/core/genre_guards/fantasy_guard.py` | 362 | Fantasy-specific rules |
| `modules/core/genre_guards/investment_guard.py` | 717 | Investment-specific rules |
| `config/genres/wuxia.yaml` | 238 | Wuxia config: forbidden terms, realm hierarchy, technique limits |

### Source Survey Documents

| Document | Role |
|----------|------|
| `docs/2026-03-27/per-work-fact-system-synthesis-memo.md` | Fact system synthesis: contract-only recommended direction |
| `docs/2026-03-27/per-work-fact-contract-alignment-residual-survey.md` | Post-Wave 1 residual analysis: 10 fact families, 4-tier classification |

## 2. Key Anchor List

### Wave 1 Contract Alignment Anchors

| Anchor | File:Line | Description |
|--------|-----------|-------------|
| Authority statement injection | `stage4_context_builder.py:996-1008` | `_build_persisted_authority_statement()` — WorldState/FactLedger precedence |
| Advisory suppression | `stage4_context_builder.py:939-971` | `_filter_state_tracker_summaries_for_authority()` — 7 domain suppression |
| Canonical block position | `stage4_context_builder.py:1681-1700` | Position 0 in tier0_parts |
| Dead-NPC pre-check | `stage3_orchestrator.py:1552-1602` | `_apply_stage3_dead_npc_precheck()` |
| Dead-NPC blueprint scan | `state_tracker_npc.py:1420-1517` | `check_dead_npc_in_blueprint()` |

### Fact Authority API Anchors

| Anchor | File:Line | Description |
|--------|-----------|-------------|
| WorldState canonical constraints | `world_state.py:764-806` | `get_canonical_constraints()` — NPC intro roles + known_attrs, 8000 char cap |
| WorldState full summary | `world_state.py:1056-1082` | `get_summary()` — 50K char cap |
| WorldState long-term anchor | `world_state.py:1201-1241` | `get_long_term_anchor()` — 60+ ep immutable facts |
| WorldState TruthGate accessors | `world_state.py:1138-1153` | `get_deceased_npcs()`, `get_owned_items()`, `get_destroyed_locations()`, `get_known_skills()` |
| FactLedger canonical summary | `fact_ledger.py:767-781` | `get_canonical_summary()` — top 30 numeric facts, 5000 char cap |
| FactLedger full summary | `fact_ledger.py:605-753` | `to_summary()` — 50K char cap |

### Genre Gimmick Anchors

| Anchor | File:Line | Description |
|--------|-----------|-------------|
| Guard factory | `genre_guards/__init__.py:22-69` | `create_genre_guard()` — composition chain |
| Wuxia realm hierarchy | `wuxia.yaml:156-166` | 10-tier realm progression |
| Wuxia realm-technique limits | `wuxia.yaml:169-177` | Per-realm forbidden techniques |
| Wuxia injury-action limits | `wuxia.yaml:180-200` | Per-injury forbidden actions |
| Wuxia justification patterns | `wuxia_guard.py:314-347` | 8 bypass patterns (code-hardcoded) |
| Wuxia purism prompt | `wuxia_guard.py:222-253` | `get_v20_purism_prompt()` |
| BV wuxia realm-technique check | `blocking_validator_consistency_checks.py:374-431` | Genre-gated MEDIUM severity |
| Incarnation type mitigation | `blocking_validator_consistency_checks.py:45, 114-116, 223-226, 282-284` | Cosmetic suffix |

### StateTracker Extraction Anchors

| Anchor | File:Line | Description |
|--------|-----------|-------------|
| Full extraction orchestrator | `state_tracker.py:187-252` | `full_extract_from_arcs()` — 17+ extract methods |
| NPC death extraction | `state_tracker_npc.py:672-742` | Dual-source: state_changes + regex |
| Skill acquisition extraction | `state_tracker_npc.py:816-856` | Dual-source with wuxia regex patterns |
| Genre registries init | `state_tracker.py:142-152` | hunter/fantasy/actor registries (mostly dormant) |
| Financial extraction | `state_tracker_financial.py:20-65` | Investment-only, isolated |

### BlockingValidator Check Anchors

| Check | File:Line | Severity | Genre-Gated |
|-------|-----------|----------|-------------|
| dead_npc_resurrection | `blocking_validator_entity_checks.py:88` | CRITICAL | No |
| unowned_item_usage | `blocking_validator_entity_checks.py:283` | CRITICAL | No |
| damaged_item_usage | `blocking_validator_entity_checks.py:321` | CRITICAL | No |
| destroyed_location_visit | `blocking_validator_entity_checks.py:466` | CRITICAL | No |
| minimum_length | `blocking_validator_scene_checks.py:21` | CRITICAL | No |
| required_scenes | `blocking_validator_scene_checks.py:44` | N/A (disabled) | No |
| scope_overflow | `blocking_validator_scene_checks.py:53` | HIGH | No |
| scene_completeness | `blocking_validator_scene_checks.py:135` | HIGH | No |
| cliffhanger_ending | `blocking_validator_scene_checks.py:258` | MEDIUM | No |
| physical_capability | `blocking_validator_consistency_checks.py:30` | MEDIUM | Partial (incarnation) |
| authority_exercise | `blocking_validator_consistency_checks.py:137` | MEDIUM | Partial (incarnation) |
| relationship_consistency | `blocking_validator_consistency_checks.py:247` | HIGH (degradable) | Partial (incarnation) |
| information_consistency | `blocking_validator_consistency_checks.py:303` | MEDIUM (degradable) | No |
| wuxia_technique_realm | `blocking_validator_consistency_checks.py:374` | MEDIUM | YES (wuxia only) |

## 3. Size/Limit Constants

| Constant | Value | File:Line |
|----------|-------|-----------|
| WorldState `get_summary()` max | 50,000 chars | `world_state.py:1075-1076` |
| WorldState `get_canonical_constraints()` max | 8,000 chars | `world_state.py:801-802` |
| WorldState skills max | 50 | `world_state.py:212-215` |
| WorldState destroyed max | 100 | `world_state.py:730-731` |
| WorldState motivations max | 20 | `world_state.py:483-484` |
| WorldState promises max | 30 | `world_state.py:513-517` |
| FactLedger `to_summary()` max | 50,000 chars | `fact_ledger.py:751-752` |
| FactLedger `get_canonical_summary()` max | 5,000 chars | `fact_ledger.py:781` |
| FactLedger history per entity | 100 | `fact_ledger.py:123` |
| FactLedger alive chars display cap | 30 | `fact_ledger.py:633` |
| FactLedger numbers display cap | 15 | `fact_ledger.py:740` |
| StateTracker resolved_plots max | 500 (LRU) | `state_tracker_plots.py` |
| StateTracker entity_name_registry max | 500 (LRU) | `state_tracker_plots.py:136` |

## 4. Genre Registry Maturity Matrix

| Genre | Registry | Extraction | Validation | Enforcement | Overall |
|-------|----------|------------|------------|-------------|---------|
| Wuxia protagonist_skills | Exists | state_changes + regex | None | None | B+ |
| Wuxia NPC level | Exists (in npc_registry) | Regex only | None | None | C+ |
| Hunter skill_cooldown | Exists | state_changes | None | None | C |
| Hunter dungeon_clear | Exists | Substring match | None | None | C |
| Fantasy spell_repertoire | Exists | state_changes (partial) | None | None | C |
| Fantasy blessing_curse | Initialized | NONE | None | None | F |
| Investment financial | Exists | state_changes | FactLedger numeric | None | A |
| Actor filmography | Initialized | NONE | None | None | F |
