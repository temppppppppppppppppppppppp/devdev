Date: 2026-03-23
Status: provisional (3-pass audited, below confidence gate)
Document Type: Q5 long-term consistency bounded deep-dive survey report
Canonical Path: `docs/2026-03-23/opus/q5-long-term-consistency-deep-dive.md`
Terminal: T5
Axis: Q5 "잘 기억하냐" — long-run consistency, WorldState/FactLedger/StateTracker alignment

---

## 1. Executive Summary

Q5 consistency infrastructure is **architecturally sound** with 4 independent persistence systems (WorldState, FactLedger, StateTracker, ChainLinks) and 2 continuity validators. All are DB-backed via the anchor system, with atomic rollback support in Stage 4 post-pass.

**Critical finding**: The 4 systems operate as **parallel silos** — no cross-system consistency enforcement exists. WorldState and FactLedger receive the same `state_changes` dict but maintain independent ledgers. If one save succeeds and the other fails, no mechanism detects or corrects the divergence.

**Top 3 structural risks for long-running series (100+ episodes)**:
1. **Entity resolution by exact string match** — FactLedger and StateTracker both use dict key lookup with no alias resolution. Name variants across 100+ episodes silently create duplicate entity records.
2. **Silent FIFO truncation** — WorldState caps lists at 20-100 entries, FactLedger caps history at 100 per entity. Oldest data silently discarded without logging.
3. **ContinuityValidator blind to world state** — validates only episode-local HUD snapshots, cannot see cross-arc WorldState or FactLedger. Long-term fact contradictions pass undetected.

P0: 4 | P1: 8 | P2: 6 | Total findings: 18

---

## 2. Current Ownership / Flow Map

### 2.1 Module Ownership

| Module | Owner | Role | LOC |
|--------|-------|------|-----|
| `modules/core/world_state.py` | WorldStateManager | 9-field world snapshot (protagonist, NPCs, items, timeline, plots, laws) | ~1,312 |
| `modules/core/fact_ledger.py` | FactLedger | 5-category entity ledger (characters, items, locations, organizations, numbers) | ~859 |
| `modules/domain/agents/state_tracker.py` | StateTracker (facade) | DAG timeline + NPC/Financial/Plots submodule orchestration | ~1,669 |
| `modules/domain/agents/state_tracker_npc.py` | StateTrackerNPC | NPC registry, death/injury/movement/relationship tracking | ~2,205 |
| `modules/validation/continuity_validator.py` | ContinuityValidator | Episode-level Python-only state contradiction detection | ~1,265 |
| `modules/domain/agents/continuity_arc.py` | ContinuityArcValidator | Arc-level cross-arc consistency (Python precheck + LLM phase) | ~1,096 |

### 2.2 Data Flow Map

```
Stage 2 (Arc Design):
  StateTracker.full_extract_from_arcs()  → reads from passed arcs
  FactLedger context                     → injected into prompts
  WorldState context                     → [MISSING — GAP-A1]

Stage 3 (Blueprint):
  Lazy init: WorldState, FactLedger      → from DB anchors
  StateTracker.bind_world_state()        → one-way reference binding
  NPC/Timeline summaries                 → injected into prompts

Stage 4 Pre-Validation:
  ContinuityValidator                    → reads prev_hud only [GAP-A3]
  TruthGate advisory                     → reads WorldState + FactLedger
  NpcDrift advisory                      → reads WorldState NPC snapshots

Stage 4 Post-Pass:
  Chain link extraction + save           → DB anchor per episode
  WorldState atomic update               → state_changes → save()
  FactLedger atomic update               → state_changes + bible_delta → save()
  State log                              → DB state_logs table
```

### 2.3 Persistence Anchors

| Anchor Key | System | Write | Read |
|------------|--------|-------|------|
| `world_state` | WorldStateManager | Stage 4 post-pass | Stage 3 lazy init, Stage 4 advisories |
| `fact_ledger` | FactLedger | Stage 4 post-pass | Stage 2 preflight, Stage 3 lazy init |
| `chain_link_{ep}` | ChainLink | Stage 4 post-pass | Stage 4 context builder |
| `financial_registry` | StateTrackerFinancial | Stage 2 finalizer | Stage 2 orchestrator |

---

## 3. Top Hotspots

### P0 (Critical) — 4 findings

#### P0-1. No Cross-System Atomicity Between WorldState and FactLedger
- **File**: `modules/core/stage4_post_pass_runtime.py:1070-1117`
- **Issue**: WorldState and FactLedger saved sequentially with independent snapshots. No XA transaction. If FactLedger save fails after WorldState succeeds, systems diverge permanently.
- **Impact**: Silent state divergence. WorldState says NPC alive, FactLedger says NPC dead (or vice versa). No detection mechanism exists.
- **Fix type**: `boundary-refactor`

#### P0-2. Entity Resolution by Exact String Match (FactLedger)
- **File**: `modules/core/fact_ledger.py:504-596` (upsert methods)
- **Issue**: All entity lookups use exact dict key match. "흑풍" vs "흑풍 (대검사)" creates 2 separate records. No alias resolution, no fuzzy matching, no deduplication.
- **Impact**: Long-running series accumulates split entity records. FactLedger summary becomes polluted with duplicates. LLM receives inconsistent entity history.
- **Fix type**: `boundary-refactor`

#### P0-3. ContinuityValidator Has No Access to WorldState/FactLedger
- **File**: `modules/core/stage4_interview_round.py:3349-3390`
- **Issue**: ContinuityValidator initialized with `context` param only. No `world_state` or `fact_ledger` injected. Validation only checks episode-local HUD snapshots.
- **Impact**: Long-term fact contradictions (e.g., "NPC died in Arc 1 but reappears in Arc 5") pass undetected by the continuity gate. Only TruthGate advisory catches these, but it's non-blocking.
- **Fix type**: `boundary-refactor`

#### P0-4. LLM Verification Fallback in NPC Death Detection
- **File**: `modules/domain/agents/state_tracker_npc.py:751-752`
- **Issue**: `_verify_npc_names_llm()` returns all regex candidates unfiltered if `self.tracker._llm_client is None`. No fallback to exclude_words filtering.
- **Impact**: General nouns ("데이터", "시장", "후원자") marked as dead NPCs. StateTracker NPC registry polluted with false deaths.
- **Fix type**: `contract-cleanup`

### P1 (Important) — 8 findings

#### P1-1. Silent FIFO Truncation Without Logging (WorldState)
- **File**: `modules/core/world_state.py:215,423,432,477,510,724-728`
- **Issue**: List fields capped (timeline: 20, destroyed: 100, promises: 30, pressure_vectors: 5). Oldest entries silently dropped. No warning logged.
- **Impact**: 200+ episode series loses historical events. LLM-facing prompts lack critical context about early-series events.
- **Fix type**: `observability-only`

#### P1-2. Silent FIFO Truncation Without Logging (FactLedger)
- **File**: `modules/core/fact_ledger.py:433,528,560,580,595`
- **Issue**: Per-entity history capped at 100 entries via `entry["history"] = entry["history"][-100:]`. No warning logged.
- **Impact**: Entity with 150+ updates loses oldest 50 events permanently. No indication to operator.
- **Fix type**: `observability-only`

#### P1-3. Partial Section Update Marks Episode as Processed (WorldState)
- **File**: `modules/core/world_state.py:690-731`
- **Issue**: 5 section try/except blocks. If one section fails (e.g., NPC deaths), the episode is still marked as `last_updated_ep = ep_num` at line 711. Partial state accepted as complete.
- **Impact**: Some categories of state changes silently lost while episode marked as fully processed.
- **Fix type**: `observability-only`

#### P1-4. NPC-NPC Relationship LRU Eviction at 50 Pairs
- **File**: `modules/domain/agents/state_tracker_npc.py:1698-1700`
- **Issue**: `npc_npc_relationships` dict has hard LRU cap at 50 pairs. No logging of evictions.
- **Impact**: High-NPC stories (50+ relationship pairs) lose old relationships silently. LLM context loses historical relationship dynamics.
- **Fix type**: `observability-only`

#### P1-5. Stage 2 Missing WorldState Context in Arc Planning
- **File**: `modules/core/stage2_orchestrator.py:281-361`
- **Issue**: FactLedger context is injected into Stage 2 prompts, but WorldState is not. Arc planning doesn't see NPC positions, world conditions, or timeline state.
- **Impact**: Arcs may be designed with incorrect assumptions about current world state.
- **Fix type**: `boundary-refactor`

#### P1-6. Chain Link Not Used in Stage 2 Planning
- **File**: `modules/core/stage2_orchestrator.py` (absent)
- **Issue**: `chain_link_{prev_ep}` data (cliffhanger, pending_actions, emotional_state) from previous arc's last episode is not loaded into Stage 2 context.
- **Impact**: New arcs don't see the cliffhanger or pending actions from the previous arc's conclusion.
- **Fix type**: `boundary-refactor`

#### P1-7. Growth Keywords Hardcoded — Personality Contradiction Misclassification
- **File**: `modules/validation/continuity_validator.py:1009-1018,1090-1091`
- **Issue**: `growth_keywords` tuple hardcoded (8 keywords only). No YAML config, no `_threshold()` parameterization. Personality contradiction severity (MAJOR vs MINOR) depends on exact keyword match.
- **Impact**: Personality growth expressed with synonyms ("발전", "진화") misclassified as MAJOR. Long-running series accumulates false MAJOR personality contradiction warnings.
- **Fix type**: `contract-cleanup`

#### P1-8. WorldState Revive NPC — Non-Atomic Cross-System Sync
- **File**: `modules/domain/agents/state_tracker_npc.py:1402-1406`
- **Issue**: `revive_npc()` updates StateTracker NPC registry but WorldState `dead_npcs` sync is non-blocking. If sync fails, NPC alive in StateTracker but dead in WorldState.
- **Impact**: Downstream systems receive contradictory death status for the same NPC.
- **Fix type**: `contract-cleanup`

### P2 (Advisory) — 6 findings

#### P2-1. Dead NPC Updates Silently Dropped (FactLedger)
- **File**: `modules/core/fact_ledger.py:329,340,351,370`
- **Issue**: Updates for dead characters silently `continue`'d. No warning to Director that data was suppressed.
- **Fix type**: `observability-only`

#### P2-2. Entity Name Registry LRU 500 Cap (StateTracker)
- **File**: `modules/domain/agents/state_tracker.py:135-136`
- **Issue**: 500-entry LRU. No eviction logging. Long works with >500 entities lose oldest name mappings.
- **Fix type**: `observability-only`

#### P2-3. NPC-NPC Relationships No Regex Fallback
- **File**: `modules/domain/agents/state_tracker_npc.py:1677-1685`
- **Issue**: Extraction only from state_changes. If Analyst fails to populate this field, relationship changes are silently lost.
- **Fix type**: `contract-cleanup`

#### P2-4. `_is_same_item()` Substring False Positives
- **File**: `modules/validation/continuity_validator.py:929-930`
- **Issue**: "검" matches "검은 검", "검투", "검객". Wuxia stories with many "검"-containing items trigger false BLOCKING violations.
- **Fix type**: `contract-cleanup`

#### P2-5. prev_hud Missing → Degraded Fail-Open
- **File**: `modules/validation/continuity_validator.py:152-174`
- **Issue**: If prev_hud injection fails, entire continuity validation becomes advisory-only with BLOCKING severity logged but execution continues.
- **Fix type**: `observability-only`

#### P2-6. Protagonist Emotion No History (StateTracker)
- **File**: `modules/domain/agents/state_tracker_npc.py:1960-1965`
- **Issue**: Emotion update overwrites previous state. No history list. No rollback or audit trail.
- **Fix type**: `contract-cleanup`

---

## 4. Quick Wins

| # | Finding | File:Line | Fix Type | Effort | ROI |
|---|---------|-----------|----------|--------|-----|
| QW-1 | Add WARNING log when FIFO truncation fires (WorldState) | `world_state.py:724-728` | `observability-only` | 1h | HIGH — visibility into data loss |
| QW-2 | Add WARNING log when FIFO truncation fires (FactLedger) | `fact_ledger.py:433,528,560,580,595` | `observability-only` | 1h | HIGH — same |
| QW-3 | Apply exclude_words fallback when LLM client is None (NPC death) | `state_tracker_npc.py:751-752` | `contract-cleanup` | 30m | HIGH — prevents NPC registry pollution |
| QW-4 | Log when dead NPC update is suppressed (FactLedger) | `fact_ledger.py:329,340,351,370` | `observability-only` | 30m | MEDIUM — Director audit trail |
| QW-5 | Log NPC-NPC relationship LRU evictions | `state_tracker_npc.py:1698-1700` | `observability-only` | 15m | MEDIUM — visibility |
| QW-6 | Parameterize growth_keywords via YAML config | `continuity_validator.py:1009-1018` | `contract-cleanup` | 1h | MEDIUM — reduces false MAJOR |

---

## 5. Boundary Refactor Candidates

### BR-1. Cross-System Atomic Save (WorldState + FactLedger)
- **Scope**: `stage4_post_pass_runtime.py:1070-1117`
- **Current**: Sequential save with independent snapshots
- **Target**: Wrap both saves in DB transaction or implement detect-and-reconcile layer
- **Risk**: Medium — requires DB manager transaction support extension
- **ROI**: HIGH for series >50 episodes where divergence probability increases

### BR-2. Entity Alias Resolution Layer
- **Scope**: `fact_ledger.py:504-596`, `state_tracker_npc.py:384-409`
- **Current**: Exact string key lookup
- **Target**: Canonical entity registry with alias mapping (e.g., StateTracker's `entity_name_registry` extended to FactLedger)
- **Risk**: Medium — requires entity normalization pipeline
- **ROI**: HIGH for series >30 episodes where name drift is inevitable

### BR-3. ContinuityValidator WorldState/FactLedger Integration
- **Scope**: `stage4_interview_round.py:3349-3390`, `continuity_validator.py`
- **Current**: Validates only episode-local HUD snapshots
- **Target**: Inject WorldState/FactLedger references for cross-episode fact checking
- **Risk**: Low-Medium — constructor signature change + new validation methods
- **ROI**: HIGH — closes the largest coverage gap in Q5

### BR-4. Stage 2 WorldState + Chain Link Context Injection
- **Scope**: `stage2_orchestrator.py:281-361`, `stage2_preflight_runtime.py`
- **Current**: Only FactLedger summary injected
- **Target**: Add WorldState summary + chain_link_{prev_ep} to Stage 2 arc planning prompts
- **Risk**: Low — additive change, no behavioral modification
- **ROI**: MEDIUM — prevents arc designs based on stale assumptions

---

## 6. Fresh-Run Relevance

**Fresh-run-before-fix allowed: no**

The 4-episode test project fresh run (ep1-4) is **too short** to exercise Q5 structural risks:
- Entity name drift requires 30+ episodes to manifest
- FIFO truncation triggers at 20-100 entries (requires many arc completions)
- Cross-system divergence requires a save failure, not testable in happy-path runs
- ContinuityValidator gap requires multi-arc contradictions to surface

**Top 3 highest-ROI code fixes before next fresh run**:

1. **QW-3: LLM client None fallback for NPC death detection** (`state_tracker_npc.py:751-752`)
   - Category: `consistency drift`
   - Rationale: Prevents NPC registry pollution that cascades into all downstream consistency checks. Immediate, low-risk fix.

2. **QW-1 + QW-2: FIFO truncation logging** (`world_state.py:724-728`, `fact_ledger.py:433,528,560,580,595`)
   - Category: `관측성 부족`
   - Rationale: Without logging, the next fresh run will silently truncate data in longer test runs. Must have observability before we can diagnose Q5 failures.

3. **P1-7: Growth keywords parameterization** (`continuity_validator.py:1009-1018`)
   - Category: `LLM-Director 정합성 불일치`
   - Rationale: Current hardcoded keywords cause false MAJOR personality contradictions. Director receives noisy advisories that could mask real issues.

---

## 7. Confidence And Limits

**Estimated confidence: 94%**

Basis:
- All 6 primary scope files read in full with line-level analysis
- Cross-cutting data flow traced through 7 additional integration files (orchestrators, post-pass runtime, context builders)
- Findings triangulated between live code and fresh-run report observations
- Advisory chain integration verified via stage4_interview_round.py parallel executor

The 6% gap is from:
- `state_tracker_plots.py` and `state_tracker_financial.py` submodules not fully analyzed (delegated tracking) — 3%
- `director_continuity.py` integration with ContinuityArcValidator not traced end-to-end — 2%
- Live runtime behavior under save-failure conditions not verified (structural analysis only) — 1%

**Provisional items (below 95% confidence)**:
- P0-1 cross-system atomicity: Confirmed at code level, but actual divergence probability depends on DB reliability (observed 0 failures in fresh run)
- P0-2 entity resolution: Confirmed structurally, but impact depends on LLM name consistency across episodes (not measurable without longer run)

---

## 3-Pass Audit Record

### Pass 1. Evidence Collection
- Read all 6 primary scope files in full via parallel agents
- Traced cross-cutting data flow through stage orchestrators, post-pass runtime, context builders
- Confirmed fresh-run report findings against live code
- PASS

### Pass 2. Finding Classification
- Classified 18 findings into P0 (4), P1 (8), P2 (6) with file:line anchors
- Verified all P0/P1 findings have fix type assignments
- Cross-referenced with current-state situation report risk register
- PASS

### Pass 3. Report Completeness
- All 7 mandatory sections present
- All P0/P1 findings have file:line anchors
- All recommendations have fix type from allowed set
- Fresh-run-before-fix determination made with rationale
- Top 3 highest-ROI fixes identified with categories
- PASS
