Date: 2026-03-23
Document Type: Q5 evidence manifest (raw anchors and source inventory)
Terminal: T5

---

## Source File Inventory

| File | LOC | Read Coverage |
|------|-----|---------------|
| `modules/core/world_state.py` | ~1,312 | Full |
| `modules/core/fact_ledger.py` | ~859 | Full |
| `modules/domain/agents/state_tracker.py` | ~1,669 | Full |
| `modules/domain/agents/state_tracker_npc.py` | ~2,205 | Full |
| `modules/validation/continuity_validator.py` | ~1,265 | Full |
| `modules/domain/agents/continuity_arc.py` | ~1,096 | Full |
| `modules/core/stage4_post_pass_runtime.py` | Partial (L712-1117) | Post-pass update flow |
| `modules/core/stage4_post_processor.py` | Partial (L756-799, L879-968, L1030-1068) | Post-pass pipeline + rollback |
| `modules/core/stage4_interview_round.py` | Partial (L3349-3390, L4485-4700) | Continuity + advisory chains |
| `modules/core/stage4_director_runtime.py` | Partial (L93-229) | Pre-validation flow |
| `modules/core/stage4_context_builder.py` | Partial (L1353-1375, L1641-1657) | Chain link + fact ledger injection |
| `modules/core/stage2_orchestrator.py` | Partial (L281-361) | StateTracker init + context |
| `modules/core/stage3_orchestrator.py` | Partial (L572-587, L724-759) | Lazy init + binding |
| `modules/core/db_manager.py` | Partial (L993-1026) | Anchor system |

---

## P0 Finding Anchors

### P0-1: Cross-System Atomicity Gap

```
stage4_post_pass_runtime.py:1070  _save_world_state_atomic()
stage4_post_pass_runtime.py:1081  snapshot pre-save state
stage4_post_pass_runtime.py:1091  sequential OR transaction mode
stage4_post_pass_runtime.py:939   world_state.update_from_state_changes()
stage4_post_pass_runtime.py:982   fact_ledger.update_from_state_changes()
stage4_post_pass_runtime.py:1030  _handle_atomic_metadata_rollback() — only covers world_state+fact_ledger, not state_tracker
```

### P0-2: Entity Exact String Match

```
fact_ledger.py:504   _upsert_character() — chars[name] direct key
fact_ledger.py:536   _upsert_item() — items[name] direct key
fact_ledger.py:565   _upsert_location() — locations[name] direct key
fact_ledger.py:584   _upsert_organization() — orgs[name] direct key
fact_ledger.py:420   update_number() — numbers[key] direct key
state_tracker_npc.py:384  create_npc_entry() — npc_registry[name] direct key
```

### P0-3: ContinuityValidator No WorldState/FactLedger

```
stage4_interview_round.py:3349  _run_director_continuity_and_state_tracker_advisories()
stage4_interview_round.py:3363  continuity_validator.validate(next_ep, manuscript, cv_context)
continuity_validator.py:129     validate() — no world_state param
continuity_validator.py:147     _get_prev_hud() — reads from context only
continuity_validator.py:288     fallback returns None on failure
```

### P0-4: LLM Verification Fallback

```
state_tracker_npc.py:751  _verify_npc_names_llm() entry
state_tracker_npc.py:752  if self.tracker._llm_client is None: return candidates (unfiltered)
state_tracker_npc.py:76-140   _NPC_DEATH_EXCLUDE_WORDS (exists but not used in fallback)
```

---

## P1 Finding Anchors

### P1-1: WorldState Silent FIFO

```
world_state.py:215   protagonist.skills[:50]
world_state.py:423   timeline[-20:]
world_state.py:432   cumulative_elapsed.history[-20:]
world_state.py:477   motivations — max 20
world_state.py:510   promises — max 30
world_state.py:724   destroyed[-100:]
world_state.py:725   active_pressure_vectors[-5:]
world_state.py:727   world_notes[-10:]
```

### P1-2: FactLedger Silent FIFO

```
fact_ledger.py:433   numbers history[-100:]
fact_ledger.py:528   characters history[-100:]
fact_ledger.py:560   items history[-100:]
fact_ledger.py:580   locations history[-100:]
fact_ledger.py:595   organizations history[-100:]
```

### P1-3: Partial Section Update

```
world_state.py:690   update_from_state_changes() entry
world_state.py:198   §1-4a exception catch (actor/inventory)
world_state.py:218   §5-8 exception catch (entity/companion)
world_state.py:239   §12-14 exception catch (timeline/goal)
world_state.py:260   §15-17 exception catch (physical/known)
world_state.py:711   last_updated_ep = ep_num (ALWAYS set)
```

### P1-4: NPC-NPC LRU 50

```
state_tracker_npc.py:1688  npc_npc_relationships dict
state_tracker_npc.py:1698  if len > 50: pop oldest
state_tracker_npc.py:1700  no logging
```

### P1-5: Stage 2 Missing WorldState

```
stage2_orchestrator.py:281-361   _run_production_cycle() — no world_state injection
stage2_preflight_runtime.py:1143  _build_fact_ledger_context() — FactLedger only
```

### P1-6: Chain Link Not in Stage 2

```
stage4_context_builder.py:1353  load_chain_link_section() — Stage 4 only
stage2_orchestrator.py — no chain_link_{ep} loading anywhere
```

### P1-7: Growth Keywords Hardcoded

```
continuity_validator.py:1009-1018  growth_keywords tuple (8 static entries)
continuity_validator.py:1090       has_growth = any(keyword in nearby_text ...)
continuity_validator.py:1091       severity = "MINOR" if has_growth else "MAJOR"
```

### P1-8: Revive NPC Non-Atomic

```
state_tracker_npc.py:1396   revive_npc() entry
state_tracker_npc.py:1402   _world_state sync attempt
state_tracker_npc.py:1406   non-blocking on exception
```

---

## Cross-Cutting Integration Gaps

| Gap ID | Source | Target | Missing Link |
|--------|--------|--------|-------------|
| GAP-A1 | Stage 2 arc planning | WorldState | No world_state summary in Stage 2 prompts |
| GAP-A3 | ContinuityValidator | WorldState/FactLedger | No reference injection |
| GAP-A5 | Stage 3 lazy init | StateTracker | Not re-bound after lazy init |
| GAP-A6 | Stage 2 planning | ChainLinks | chain_link_{prev_ep} not loaded |
| GAP-A8 | Rollback coordination | StateTracker | Not included in atomic rollback |
| GAP-A9 | Stage transitions | All systems | No cross-system consistency audit |

---

## WorldState Schema Summary (_INIT_STATE)

```
version: int (=1)
last_updated_ep: int
last_updated_source: str
protagonist: {name, location, assets, injuries, skills[max 50]}
alive_npcs: {name → {role, relation, personality, location, first_seen_ep, role_at_intro, known_attrs, companion, dual_identity}}
dead_npcs: {name → {ep, cause}}
relationships: {npc_name → relation_str}
active_items: {name → {ep_acquired, status, quantity, last_count_ep}}
destroyed: [{name, type, ep, cause}] max 100
active_plots: [{plot, status, since_ep}] max 100
active_pressure_vectors: [{text, source, cue_terms[], since_ep}] max 5
world_notes: [] max 10
world_laws: [{law, established_ep, priority}] max 50 (CRITICAL pinned)
timeline: [{ep, type, description}] max 20
motivations: [{text, status, since_ep, resolved_ep}] max 20
promises: [{text, promiser, promisee, since_ep, status}] max 30
cumulative_elapsed: {total_days, history[max 20]}
```

---

## FactLedger Schema Summary

```
characters: {name → {status, role, relationship, established_ep, last_ep, history[max 100]}}
items: {name → {owner, status, established_ep, last_ep, history[max 100], quantity}}
locations: {name → {status, current_owner, last_ep, history[max 100]}}
organizations: {name → {status, leader, last_ep, history[max 100]}}
numbers: {key → {value, unit, established_ep, established_value, last_ep, history[max 100]}}
```

---

## StateTracker Registry Fields (Per NPC)

```
Core: status, weapon, level, death_arc, death_context, last_arc
V66: personality_traits, primary_motivation, position, injury, location, relation_to_protag, job
V66.1: permanent_injuries[], revive_history[]
Dynamic: preset_registry fields (genre-specific)
Auxiliary registries:
  - entity_name_registry (OrderedDict, LRU 500)
  - npc_npc_relationships (dict, LRU 50)
  - current_companions (list)
  - pending_commitments (list)
  - protagonist_emotion (dict, no history)
  - in_world_timeline (list)
```

---

## ContinuityValidator Check Coverage

| Check Family | Lines | Severity Range | Coverage |
|-------------|-------|----------------|----------|
| Item continuity | 467-511 | CRITICAL/BLOCKING | Prev-ep only |
| Inventory count | 540-568 | WARNING | Prev-ep only |
| Weapon continuity | 570-634 | CRITICAL | Prev-ep only |
| Active pressure | 435-465 | WARNING | Prev-ep only |
| Injury continuity | 636-775 | BLOCKING/WARNING | Prev-ep only |
| Location continuity | 798-916 | BLOCKING/WARNING | Prev-ep only |
| Personality continuity | 1001-1158 | MAJOR/MINOR | Prev-ep + NPC history |
| Time consistency | 1161-1219 | BLOCKING/WARNING | External time_warnings |
| Frustration streak | 1223-1264 | WARNING | Multi-ep advisory |

**NOT covered**: Cross-arc fact contradictions, multi-episode journey validation, skill regression, relationship momentum loss, prophecy fulfillment tracking, dialogue consistency with prior arcs.
