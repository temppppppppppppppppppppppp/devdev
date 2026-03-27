# Per-Work Fact Contract Authority Compact Survey

Date: 2026-03-27
Status: final (3-pass audited)
Type: system-track compact survey (survey-only, no code changes)
Canonical Path: `docs/2026-03-27/per-work-fact-contract-authority-compact-survey.md`
Scope: per-work fact ownership, authority hierarchy, conflict resolution, and LLM injection priority across all persistence/generation layers
Excluded: model-switch concerns, UI/desktop, pricing/billing, Stage 0 handoff mechanics

Commit State:
- Baseline Commit: `eb7a41d8`
- Baseline Dirty Summary: clean workspace

Evidence Basis:
- `modules/core/fact_ledger.py` (FactLedger)
- `modules/core/world_state.py` (WorldStateManager)
- `modules/core/reference_anchor.py` (ReferenceAnchor)
- `modules/core/stage4_context_builder.py` (tier-0 injection + overlap suppression)
- `modules/core/stage4_immutable_fact_contract.py` (ImmutableFactPacket)
- `modules/core/stage4_context_packets.py` (context packets)
- `modules/domain/agents/state_tracker.py` (StateTracker + NPC/Entity Registry)
- `modules/domain/agents/state_tracker_npc.py` (NPC sub-module)
- `modules/domain/agents/state_tracker_plots.py` (Entity Name Registry)
- `modules/domain/agents/chief_writer_context.py` (prompt assembly order)
- `modules/domain/agents/blueprint_ensemble.py` (blueprint context)
- `modules/core/stage2_orchestrator.py` (Stage 2 fact flow)
- `modules/core/stage3_orchestrator.py` (Stage 3 fact flow + init)
- `modules/core/stage4_orchestrator.py` (Stage 4 fact flow)
- `modules/core/project_manager.py` (ProjectContext + master_bible)
- `config/genres/wuxia.yaml` (injury/realm constraints)
- `docs/2026-03-26/wuxia-combat-scene-readiness-compact-survey.md`
- `docs/2026-03-26/wuxia-combat-quality-probe-report.md`
- `docs/2026-03-26/lookback-boundary-window-b-probe-report.md`

## 1. Findings

### 1.1 Fact Layer Inventory

The codebase has 8 distinct fact-bearing layers. Each stores a different fact class at a different lifecycle phase.

| # | Layer | File | Fact Class | Lifecycle Phase |
|---|-------|------|-----------|-----------------|
| 1 | **BI (Master Bible)** | `project_manager.py:137` | Identity, protagonist config, asset library, world origin, genre | Static (pre-generation) |
| 2 | **TR (Treatment)** | External JSON, loaded `main_a.py:1773` | Per-episode plan: setting, NPCs, conflicts, outcomes | Planned (pre-generation) |
| 3 | **FactLedger** | `fact_ledger.py:117` | Characters, numbers, items, locations, organizations + history chains | Realized (post-Stage 4) |
| 4 | **WorldState** | `world_state.py:86` | Protagonist state, alive/dead NPCs, relationships, items, plots, timeline, laws, motivations, promises | Realized (post-Stage 4) |
| 5 | **StateTracker** | `state_tracker.py:96` | Per-episode NPC registry, injuries, weapons, items, entity names, plots, companions | Extracted (post-arc, pre-Stage 4) |
| 6 | **Entity Registry** | `state_tracker.py:135` via `state_tracker_plots.py:879` | Entity names + aliases + type (organization/location/object) | Extracted (Stage 2) |
| 7 | **Reference Anchors** | `reference_anchor.py:14` | Combat, item, relationship, location, power, revelation, injury, decision events | Realized (post-manuscript, Stage 4) |
| 8 | **ImmutableFactPacket** | `stage4_immutable_fact_contract.py:65` | Opening anchor, committed state facts, completed events, scene obligations | Derived (per-attempt, ephemeral) |

### 1.2 Authority Already Clear

These authority relationships are explicitly coded with overlap suppression and precedence notes.

| Fact Domain | Authoritative Layer | Mechanism | Evidence |
|-------------|-------------------|-----------|----------|
| NPC death status | WorldState | `overlap_sources["dead_npc"] = "world_state"` | `stage4_context_builder.py:951` |
| Item ownership/status | WorldState | `overlap_sources["item_state"] = "world_state"` | `stage4_context_builder.py:952` |
| Relationship changes | WorldState | `overlap_sources["relationship_changes"] = "world_state"` | `stage4_context_builder.py:953` |
| NPC injury state | WorldState | `overlap_sources["npc_injury"] = "world_state"` | `stage4_context_builder.py:954` |
| NPC movement | WorldState | `overlap_sources["npc_movement"] = "world_state"` | `stage4_context_builder.py:955` |
| Timeline | WorldState | `overlap_sources["time_timeline"] = "world_state"` | `stage4_context_builder.py:956` |
| Financial/numeric state | FactLedger | `overlap_sources["financial_state"] = "fact_ledger"` | `stage4_context_builder.py:960` |
| Protagonist identity/config | BI (Master Bible) | Injected as immutable world origin; never overridden | `chief_writer_context.py:233-237` |
| Dead NPC action ban | StateTracker NPC Registry | `"절대 살아있는 것처럼 등장시키지 말 것"` — CRITICAL severity | `state_tracker_npc.py:1619` |
| Opening anchor / scene 1 | ImmutableFactPacket | Derived from blueprint + prev manuscript; HARD violation if drifted | `stage4_immutable_fact_contract.py:31-36` |

**Authority precedence note** (explicit in code at `stage4_context_builder.py:991`):
> "persisted canonical 레이어가 같은 영역의 arc-derived state_tracker 요약보다 우선한다."

This means: **WorldState/FactLedger > StateTracker** when both cover the same domain.

### 1.3 Authority Conflicted or Ambiguous

These domains lack explicit authority mapping in the overlap suppression system.

| Fact Domain | Competing Layers | Current Behavior | Risk |
|-------------|-----------------|-----------------|------|
| **NPC personality traits** | StateTracker (`npc_registry.personality_traits`) vs WorldState (`alive_npcs.personality`) vs BI (initial characterization) | No overlap suppression entry. Both injected independently. | Personality drift if StateTracker and WorldState diverge over long runs. Low severity — personality is soft, not hard fact. |
| **Technique/skill inventory** | StateTracker (`protagonist_skills`) vs WorldState (`protagonist.skills`, max 50) vs BI (MartialHUD) | WorldState caps at 50 (LRU). StateTracker has no cap. BI defines baseline. No explicit authority mapping. | WorldState may silently prune skills that StateTracker still references. Low risk — cap is generous. |
| **Active plots** | WorldState (`active_plots`, max 100) vs StateTracker (`active_plots`) | Both track independently. No suppression entry. WorldState keeps last 100. | Stale plots may persist differently in each layer. Low practical risk — 100 is generous. |
| **Entity names/aliases** | Entity Registry (LRU 500) vs WorldState (`alive_npcs` names) vs FactLedger (`characters` names) | Entity Registry is in-memory only (not DB-persisted). WorldState and FactLedger use DB. | Entity Registry can lose old entries via LRU while WorldState/FactLedger retain them. Name consistency warnings only — no REJECT. |
| **Fight geography** | Not tracked by any layer | Combat survey confirmed: spatial progression not persisted | Cross-episode fight location can drift undetected. Already flagged in `wuxia-combat-scene-readiness-compact-survey.md`. |
| **Technique progression** | Not tracked by any layer | Combat survey confirmed: no per-fight technique history | Repetitive choreography possible. Already flagged in combat survey. |

### 1.4 Injection Priority — Current State

The Stage 4 tier-0 context builder (`stage4_context_builder.py:1621-1706`) uses `insert(0, ...)` which means **later inserts appear first**. Reading the code sequentially, the final prompt ordering (top = first seen by LLM) is:

| Priority | Layer | Budget | Method | Evidence |
|----------|-------|--------|--------|----------|
| **L0** (highest) | NPC Boundary Block | unbounded | `_build_npc_boundary_block()` | `stage4_context_builder.py:1700-1702` |
| **L1** | Continuity Packet | unbounded | `build_continuity_packet()` | `stage4_context_builder.py:1683-1685` |
| **L2** | Canonical Block (NPC constraints 62% + Numeric constraints 38%) | 13,000 chars | `get_canonical_constraints()` + `get_canonical_summary()` | `stage4_context_builder.py:1667-1676` |
| **L3** | FactLedger Summary | 25,000 chars | `to_summary()` or `build_condensed_fact_ledger_summary()` | `stage4_context_builder.py:1649-1661` |
| **L4** | Timeline Summary | 3,000 chars | `get_timeline_summary()` | `stage4_context_builder.py:1638-1644` |
| **L5** | WorldState Summary | 50,000 chars | `get_summary()` or `build_condensed_world_state_summary()` | `stage4_context_builder.py:1621-1633` |

Additionally, **outside tier-0**, the Chief Writer prompt assembly (`chief_writer_context.py:229-272`) injects:

| Position | Layer | Evidence |
|----------|-------|----------|
| Early (line 233) | BI: World Origin Constraint | `chief_writer_context.py:233-237` |
| Mid (line 244) | TR: Scene Breakdown (blueprint-derived) | `chief_writer_context.py:244` |
| Mid (line 247-249) | StateTracker: HUD + High-Density HUD + Trends | `chief_writer_context.py:247-249` |
| Mid (line 252) | TR: Arc Doc (treatment block) | `chief_writer_context.py:252` |
| Mid (line 253) | BI: Core Identity Desire | `chief_writer_context.py:253` |
| Late (line 258) | Prev Manuscripts (immutable truth) | `chief_writer_context.py:258` |
| Late (line 265) | ImmutableFactPacket Section | `chief_writer_context.py:265` |

### 1.5 Injection Priority — What's Unclear

| Gap | Description | Impact |
|-----|-------------|--------|
| **BI vs FactLedger number conflict** | BI defines initial numeric facts (e.g., starting assets). FactLedger tracks runtime numeric evolution. If BI and FactLedger disagree (e.g., BI says "원금 10억" but FactLedger says "원금 20억" after in-story update), no explicit rule decides which the LLM should trust. | Low — FactLedger is append-only and tracks `established_ep`, so the runtime value should always be more current. But no prompt-level statement tells the LLM "FactLedger numbers supersede BI numbers." |
| **Reference Anchors vs WorldState item state** | Reference Anchors claim `"특히 아이템(무기), 위치, 인간관계, 부상 상태는 최신 앵커를 따르십시오"` (`reference_anchor.py:318`). WorldState also claims authority over items, injuries, relationships, movement. | Low in practice because anchors are extracted from the same manuscripts that update WorldState. But if anchor extraction lag differs from WorldState update lag, the two could temporarily disagree. No explicit reconciliation. |
| **Stage 3 advisory vs Stage 4 canonical** | Stage 3 gets FactLedger/WorldState as advisory only (`stage3_orchestrator.py:204-235`). Blueprint generation sees state but cannot guarantee the blueprint won't plan something that contradicts current canonical state. | Medium — blueprints are plans, not commitments. But if a blueprint plans an NPC action that WorldState says is impossible (e.g., dead NPC), the conflict surfaces only at Stage 4 validation, not at blueprint time. |

### 1.6 Static vs Planned vs Realized Classification

| Phase | Layers | Mutability | Who Can Change |
|-------|--------|------------|----------------|
| **Static** (never changes during run) | BI (Master Bible), Genre Guard YAML | Immutable after Stage 0 | Only user (manual edit) |
| **Planned** (intent, not yet happened) | TR (Treatment), Blueprint | Read-only input during generation | User (TR); Stage 3 pipeline (Blueprint) |
| **Realized** (confirmed by manuscript) | FactLedger, WorldState, Reference Anchors | Append-only after Stage 4 | LLM via Director-approved manuscripts |
| **Extracted** (derived from realized) | StateTracker, Entity Registry, ImmutableFactPacket | Re-derived each cycle | Python extraction from arcs/manuscripts |

### 1.7 Registry-Worthy Gaps

| Gap | Severity | Registry-Worthy? | Rationale |
|-----|----------|-------------------|-----------|
| Fight geography not persisted | Medium | No — addressed by combat survey | Already flagged; contract extension wave scoped |
| Technique progression not tracked | Low | No — addressed by combat survey | Low practical impact in probed windows |
| Entity Registry in-memory only (no DB) | Low | No | LRU 500 is generous; validation-only use |
| NPC personality authority ambiguous | Low | No | Personality is soft fact; drift is acceptable |
| BI→FactLedger numeric handoff has no explicit LLM-facing rule | Medium | **Yes** | The LLM has no prompt-level statement resolving "BI says X, FactLedger says Y." Currently works because FactLedger tracks `established_ep` and the LLM infers recency, but this is implicit, not contractual. |
| Stage 3 sees canonical state as advisory only | Medium | **Yes** | Blueprints can plan actions contradicting current WorldState/FactLedger. Contradiction surfaces only at Stage 4 validation, costing a full rejected cycle. |

## 2. Core Question Answers

### Q1. Which layer owns which fact type?

| Fact Type | Owner | Runner-Up |
|-----------|-------|-----------|
| Protagonist identity/config | BI | — |
| Genre rules, injury limits, realm hierarchy | Genre Guard YAML (via BI genre) | — |
| Episode plan/intent | TR (Treatment) | Blueprint |
| NPC alive/dead, items, relationships, injuries, movement, timeline | WorldState | StateTracker (derived) |
| Numeric facts (financial, quantities, dates) | FactLedger | WorldState (non-numeric) |
| Combat/item/relationship/power events | Reference Anchors | WorldState (state, not events) |
| Per-episode extracted NPC state | StateTracker | WorldState (canonical version) |
| Entity names and aliases | Entity Registry (in-memory) | WorldState `alive_npcs` keys |
| Opening anchor + committed state | ImmutableFactPacket (ephemeral) | WorldState + FactLedger (sources) |

### Q2. Which layer is authoritative on conflict?

Explicit overlap suppression at `stage4_context_builder.py:947-971`:

```
WorldState > StateTracker   for: dead_npc, item_state, relationship_changes,
                                  npc_injury, npc_movement, time_timeline
FactLedger > StateTracker   for: financial_state
BI > everything             for: protagonist identity, world origin, genre
Director > all              for: final quality verdict (AGENTS.md 대원칙 3)
```

**Not explicitly resolved:**
- BI vs FactLedger on numeric facts → FactLedger wins by recency (implicit)
- Reference Anchors vs WorldState on overlapping domains → both injected, no reconciliation
- Stage 3 advisory vs Stage 4 canonical → Stage 4 is authoritative; Stage 3 is guidance

### Q3. Which facts are static vs planned vs realized?

See §1.6 above. Key insight: the codebase correctly separates static (BI/Guard), planned (TR/Blueprint), realized (FactLedger/WorldState/Anchors), and extracted (StateTracker/Entity). The ImmutableFactPacket is a derived ephemeral that compiles from realized layers per attempt.

### Q4. What should be injected first to the LLM?

Current injection order (§1.4) places:
1. NPC boundary block (highest)
2. Continuity packet
3. Canonical constraints (NPC + numeric)
4. FactLedger summary
5. Timeline
6. WorldState summary

This is **correct in spirit** — hard constraints (NPC alive/dead, numeric limits) come before soft context (full state summary, timeline). The BI world origin is injected early in the Chief Writer prompt separately.

**One ordering concern**: The FactLedger canonical numeric summary (`L2`, 38% of 13K chars) is buried below the NPC boundary block and continuity packet. For investment/financial genres where numeric constraints are the dominant hard fact, this may be too low. But the current budget split (62% NPC / 38% numeric) is reasonable for the dominant wuxia genre.

### Q5. Is a per-work registry needed, or is stricter contract alignment enough?

**Stricter contract alignment is enough.** The two registry-worthy gaps (§1.7) are:

1. **BI→FactLedger numeric handoff**: Solvable with one prompt-level authority statement ("FactLedger 수치가 BI 초기값보다 우선") injected alongside the canonical block. No new registry needed.

2. **Stage 3 advisory→Stage 4 canonical divergence**: Solvable by adding a lightweight WorldState constraint check in blueprint validation (Stage 3). No per-work registry needed — the existing overlap suppression pattern at Stage 4 already handles the authority chain.

A per-work registry would be over-engineering for the current gap size. The existing 8-layer system covers the fact space. The gaps are in **authority declaration clarity** (what the LLM is told about precedence), not in **fact storage** (what data exists where).

## 3. Injection Priority Diagram

```
LLM Context Window (top = first tokens seen by model)
=======================================================

[TIER 0 — Hard Constraints]
  L0: NPC Boundary Block         ← alive/dead roster
  L1: Continuity Packet          ← blueprint-derived NPC/plot/item focus
  L2: Canonical Block            ← NPC constraints (62%) + numeric constraints (38%)
  L3: FactLedger Summary         ← full numeric/item/character history
  L4: Timeline Summary           ← last 20 timeline entries
  L5: WorldState Summary         ← full protagonist/NPC/relationship/plot state

[CHIEF WRITER PROMPT — Structural Context]
  BI: World Origin Constraint    ← protagonist_config, incarnation_type
  TR: Scene Breakdown            ← blueprint-derived scene plan
  StateTracker: HUD + Trends     ← per-episode extracted state
  TR: Arc Doc                    ← treatment block for this episode
  BI: Core Identity Desire       ← protagonist desire/goal

[CHIEF WRITER PROMPT — Evidence & Anchors]
  Prev Manuscripts               ← immutable text (last N episodes)
  ImmutableFactPacket            ← opening anchor + committed state + scene obligations
  Reference Anchors              ← last 30ep events + critical types (all history)

[CHIEF WRITER PROMPT — Guidance]
  Style Guide, Common Rules, Writing Guidelines, Satisfaction Guide
```

## 4. Authority Suppression Map

```
When WorldState present:
  arc-derived dead_npc            → SUPPRESSED (world_state canonical)
  arc-derived item_state          → SUPPRESSED (world_state canonical)
  arc-derived relationship_changes → SUPPRESSED (world_state canonical)
  arc-derived npc_injury          → SUPPRESSED (world_state canonical)
  arc-derived npc_movement        → SUPPRESSED (world_state canonical)
  arc-derived time_timeline       → SUPPRESSED (world_state canonical)

When FactLedger present:
  arc-derived financial_state     → SUPPRESSED (fact_ledger canonical)

Not suppressed (both injected):
  npc_personality                 → StateTracker + WorldState both present
  protagonist_skills              → StateTracker + WorldState both present
  active_plots                    → StateTracker + WorldState both present
  entity_names                    → Entity Registry (in-memory) + WorldState
  reference_anchors               → Independent (event log, not state)
```

## 5. Recommendation

**One design memo**, scoped to:

1. **Add one prompt-level authority statement** to the canonical block injection (`stage4_context_builder.py:1674-1676`): "FactLedger 수치 > BI 초기값. WorldState NPC 상태 > 아크 추출 요약. 충돌 시 더 최근 에피소드의 persisted layer를 따르라." (~3 lines of prompt text)

2. **Add lightweight WorldState dead-NPC pre-check in Stage 3 blueprint validation**: Before blueprint finalization, verify that no dead NPC is assigned an active role in the blueprint. Currently this is caught only at Stage 4, wasting a full generation cycle. (~20 lines of code)

Neither change requires a new registry, new DB schema, or new persistence layer. Both are bounded contract-alignment clarifications within the existing 8-layer architecture.

Do not open an execution SSOT yet — the memo should be reviewed first, and the prompt-level authority statement wording needs human approval before injection.

## 6. 3-Pass Audit Record

Pass 1. Structure and Scope
- Document type is compact survey, not execution SSOT
- Scope bounded to fact contract authority across 8 layers per order
- All 5 core questions addressed with file:line evidence
- Classification into clear/conflicted/unclear/registry-worthy is explicit
- Cross-references to combat survey and lookback probe are bounded (evidence, not conclusion takeover)
- PASS

Pass 2. Evidence and Consistency
- Overlap suppression at `stage4_context_builder.py:947-971` verified by direct read
- FactLedger schema at `fact_ledger.py:164-173` verified
- WorldState schema at `world_state.py:90-113` verified
- Tier-0 injection ordering at `stage4_context_builder.py:1621-1706` verified (insert(0,...) reversal confirmed)
- ImmutableFactPacket at `stage4_immutable_fact_contract.py:65-102` verified as derived-only
- Reference Anchor authority claim at `reference_anchor.py:302-318` verified
- StateTracker NPC authority claim at `state_tracker_npc.py:1619` verified
- Chief Writer prompt assembly at `chief_writer_context.py:229-272` verified
- Entity Registry LRU at `state_tracker_plots.py:879-894` verified
- No claims beyond inspected code
- PASS

Pass 3. Execution and Readability
- Findings-first structure
- File:line anchors for every claim
- Clear separation of: authority clear / authority conflicted / injection priority unclear / registry-worthy gaps
- Single recommendation (one design memo, not execution SSOT)
- Injection priority diagram and authority suppression map are actionable reference
- No scope creep into execution planning
- PASS

Estimated confidence: 96%

Reasoning:
- High confidence on authority mapping because the overlap suppression system at `stage4_context_builder.py:947-971` is explicit and grep-verified
- High confidence on injection ordering because the `insert(0, ...)` reversal pattern was verified by direct code read
- High confidence on gap assessment because both combat survey and lookback probe provide converging evidence
- Moderate residual uncertainty on whether any agent subclass bypasses the tier-0 injection path (checked: `chief_writer_context.py` and `blueprint_ensemble.py` follow the standard path)

---

- Contract-alignment need: **low**
- Dominant authority seam: **BI-to-FactLedger numeric handoff lacks LLM-facing precedence rule**
- Should Codex open an execution SSOT now: **no**
