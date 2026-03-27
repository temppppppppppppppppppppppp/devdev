# Per-Work Fact Contract Alignment — Post-Wave 1 Residual Survey

Date: 2026-03-27
Status: final
Type: system-track compact survey (survey-only, no code changes)
Scope: residual fact-authority seams after Wave 1 closure, across 10 fact families
Excluded: code changes, execution SSOT, Wave 1 reopening, registry-by-default assumptions

Evidence Basis:
- `modules/core/stage4_context_builder.py` (lines 939-1008, 1681-1700)
- `modules/core/stage4_context_packets.py` (lines 715-784)
- `modules/core/stage3_orchestrator.py` (lines 1552-1602)
- `modules/core/world_state.py` (lines 764-806)
- `modules/core/fact_ledger.py` (lines 767-781)
- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_npc.py`
- `modules/validation/blocking_validator.py`
- `modules/validation/blocking_validator_entity_checks.py`
- `modules/validation/blocking_validator_consistency_checks.py`
- `docs/2026-03-27/per-work-fact-contract-alignment-wave1-execution-ssot.md`
- `docs/2026-03-27/per-work-fact-contract-alignment-design-memo.md`
- `docs/2026-03-27/per-work-fact-system-synthesis-memo.md`

Commit State:
- Baseline Commit: `07e9aaf8` (Wave 1 closed at `eb7a41d8`)

## 1. Wave 1 Baseline — What Was Landed

Verified in live code:

### 1.1 Prompt-Facing Authority Statement

`stage4_context_builder.py:996-1008` — `_build_persisted_authority_statement()`:
- "WorldState current-state facts override extracted or advisory summaries on conflict."
- "FactLedger numeric facts override BI seed numbers and arc-derived summaries on conflict."
- Injected at position 0 in tier0_parts (highest priority).

### 1.2 Advisory Suppression

`stage4_context_builder.py:939-971` — `_filter_state_tracker_summaries_for_authority()`:
7 domains suppressed from StateTracker tier-2 when canonical layers exist:

| Suppressed Domain | Canonical Source |
|-------------------|-----------------|
| dead_npc | world_state |
| item_state | world_state |
| relationship_changes | world_state |
| npc_injury | world_state |
| npc_movement | world_state |
| time_timeline | world_state |
| financial_state | fact_ledger |

Non-suppressed domains pass through to tier-2: entity_destruction, resolved_plots, npc_personality, npc_npc_relationship, permanent_injury, companion, commitment, protagonist_emotion, plot_suspension, npc_dialogue_style, protagonist_skills, genre-specific registries.

### 1.3 Stage 3 Dead-NPC Pre-Check

`stage3_orchestrator.py:1552-1602` — `_apply_stage3_dead_npc_precheck()`:
- Calls `state_tracker.check_dead_npc_in_blueprint()`
- Injects `dead_npc_precheck` contradiction reason if dead NPC assigned active present-time role
- Non-blocking on error (graceful degradation)

### 1.4 Injection Architecture After Wave 1

The LLM sees fact data through three tiers:

| Tier | Content | Authority |
|------|---------|-----------|
| Tier-0 (highest) | Canonical block: authority statement + WorldState `get_canonical_constraints()` (NPC fixed attrs + NPC relationship edges) + FactLedger `get_canonical_summary()` (numeric facts) | Explicit precedence declared |
| Tier-0 (body) | WorldState `get_summary()` (50K chars: all alive/dead NPCs, items, plots, timeline, relationships, promises, motivations, world laws) + FactLedger `to_summary()` (25K chars: characters, numbers, items, locations, organizations) | Canonical by source, no explicit precedence statement |
| Tier-2 | StateTracker non-suppressed summaries + authority note listing what was suppressed | Advisory / derived |

Key insight: the 7 suppressed domains are NOT lost — their canonical equivalents are present in the Tier-0 body (WorldState full summary, FactLedger full summary). The suppression prevents duplication at Tier-2, not information loss.

## 2. Residual Analysis by Fact Family

### 2.1 NPC Life / Death / Current Presence

| Layer | Coverage |
|-------|----------|
| Canonical tier-0 block | WorldState `get_canonical_constraints()` — NPC fixed attrs (role_at_intro, known_attrs) |
| Canonical tier-0 body | WorldState `get_summary()` — alive_npcs, dead_npcs with cause and ep |
| Stage 3 enforcement | dead-NPC pre-check ✅ |
| Stage 4 enforcement | BlockingValidator `_check_dead_npc_resurrection()` CRITICAL ✅ |
| Advisory | dead_npc suppressed (redundant with canonical) |

**Verdict: COVERED WELL ENOUGH.** Triple authority: canonical injection, Stage 3 pre-check, Stage 4 hard-block. No residual gap.

### 2.2 Relationships

| Layer | Coverage |
|-------|----------|
| Canonical tier-0 block | WorldState `get_canonical_constraints()` — NPC relationship edges (L0-Graph) |
| Canonical tier-0 body | WorldState `get_summary()` — protagonist-NPC relationships |
| Stage 4 enforcement | BlockingValidator `_check_relationship_consistency()` via RelationshipTracker (HIGH severity, degraded mode) ✅ |
| Advisory | relationship_changes suppressed; npc_npc_relationship passes through |

**Verdict: COVERED WELL ENOUGH.** Canonical injection + Stage 4 enforcement. NPC-NPC relationships pass through as advisory supplement.

### 2.3 Injuries / Healing / Recovery

| Layer | Coverage |
|-------|----------|
| Canonical tier-0 block | NOT explicitly included — `get_canonical_constraints()` covers NPC fixed attrs, not injury status |
| Canonical tier-0 body | WorldState `get_summary()` — protagonist `injuries` field; NPC `known_attrs` may contain injury if populated |
| Stage 4 enforcement | BlockingValidator `_check_physical_capability()` — weak body performing strong actions (MEDIUM severity) ✅ |
| Advisory | npc_injury suppressed; **permanent_injury passes through unsuppressed** ✅ |

**Verdict: PARTIALLY ALIGNED.** Protagonist injury is in canonical body. NPC injury depends on WorldState `known_attrs` population via `_apply_physical_known_attr_state_changes()`. Permanent injuries (the higher-risk category — amputations, blindness) pass through unsuppressed. The residual risk is NPC current injury status being implicitly canonical rather than explicitly declared.

### 2.4 Item Ownership / Item State

| Layer | Coverage |
|-------|----------|
| Canonical tier-0 block | FactLedger `get_canonical_summary()` — numbers only (NOT items) |
| Canonical tier-0 body | WorldState `get_summary()` — active_items; FactLedger `to_summary()` — items with owner, status |
| Stage 4 enforcement | BlockingValidator `_check_unowned_item_usage()` CRITICAL + `_check_damaged_item_usage()` CRITICAL ✅ |
| Advisory | item_state suppressed (redundant with canonical body) |

**Verdict: COVERED WELL ENOUGH.** Items are in canonical body (WorldState + FactLedger full summaries). Stage 4 enforcement is strong (two CRITICAL checks). Items are not in the tier-0 canonical block but this is appropriate — items are dynamic state, not fixed constraints.

### 2.5 Location / Movement / Geography

| Layer | Coverage |
|-------|----------|
| Canonical tier-0 block | NPC `known_attrs` may include location |
| Canonical tier-0 body | WorldState `get_summary()` — protagonist location, NPC locations |
| Stage 4 enforcement | BlockingValidator `_check_destroyed_location_visit()` CRITICAL ✅ |
| Advisory | npc_movement suppressed (redundant) |
| **Missing** | No fight geography persistence; no impossible-distance check; no location lock enforcement |

**Verdict: PARTIALLY ALIGNED.** Destroyed-location enforcement is strong. General location state is in canonical body. Fight-specific geography and spatial logic remain unmodeled — a deferred structural problem, not a Wave 1 residual.

### 2.6 Time / Chronology

| Layer | Coverage |
|-------|----------|
| Canonical tier-0 body | WorldState `get_summary()` — timeline entries, cumulative_elapsed |
| Stage 4 enforcement | ContinuityValidator (TIER 0.5) — episode-to-episode state comparison |
| Advisory | time_timeline suppressed (redundant with canonical body) |
| **Missing** | No blocking enforcement for impossible time jumps or causality violations |

**Verdict: PARTIALLY ALIGNED.** Time data is in canonical body. ContinuityValidator provides soft enforcement. No hard-block on temporal impossibilities, but these are rare and the LLM generally handles temporal sequence well.

### 2.7 Numeric Business / Resource State

| Layer | Coverage |
|-------|----------|
| Canonical tier-0 block | FactLedger `get_canonical_summary()` — "[수치 제약 (L0)]" with up to 30 numeric facts ✅ |
| Authority statement | "FactLedger numeric facts override BI seed numbers" ✅ |
| Stage 4 enforcement | NumericConsistencyChecker (advisory, Python collection + LLM judgment) |
| Advisory | financial_state suppressed (redundant) ✅ |

**Verdict: COVERED WELL ENOUGH.** Strongest canonical coverage of any fact family. Explicit authority statement + canonical injection + advisory suppression. The only weakness is that NumericConsistencyChecker is advisory, not blocking — but numeric errors are caught by Director quality judgment.

### 2.8 Wuxia Technique Use History / Realm Progression

| Layer | Coverage |
|-------|----------|
| Canonical tier-0 block | NOT included |
| Canonical tier-0 body | WorldState `get_summary()` — protagonist.skills list (max 50); NOT in FactLedger |
| Stage 3 enforcement | NONE |
| Stage 4 enforcement | NONE — no blocking check for technique/realm violations |
| Advisory | protagonist_skills passes through unsuppressed ✅; genre-specific registries (skill_cooldown, spell_repertoire) pass through ✅ |
| Persistence | StateTracker: protagonist_skills + skill_acquisitions (skill→arc). Genre-specific: skill_cooldown (hunter), spell_repertoire (fantasy). **No NPC technique tracking in any system.** |

**Verdict: CLEARLY RESIDUAL RISK.**
- Protagonist technique history exists in persistence and advisory but has no canonical authority declaration and no enforcement.
- NPC technique mastery is tracked by NO system — a character could display abilities inconsistently across arcs.
- Realm progression (wuxia 9-tier hierarchy) is gated at prompt-injection level via `wuxia.yaml realm_technique_limits` but not validated against accumulated state.
- This is the most likely fact family to produce real narrative contradictions in long-running wuxia series.

### 2.9 Organization / Sect / Company Membership

| Layer | Coverage |
|-------|----------|
| Canonical tier-0 body | FactLedger `to_summary()` — organizations (status, leader) |
| Stage 4 enforcement | RelationshipTracker factions_module handles some faction transitions |
| Advisory | entity_destruction + npc_npc_relationship pass through |
| **Missing** | No explicit "NPC X is member of Org Y with rank Z" mapping in any persistence layer |

**Verdict: PARTIALLY ALIGNED.** Organizations exist as entities with status/leader. But membership edges (which characters belong to which organizations) are not modeled. In practice, this is embedded in NPC role descriptions and relationship context. For wuxia sects with complex hierarchies, this could create silent drift.

### 2.10 Planned-vs-Realized Event Outcomes

| Layer | Coverage |
|-------|----------|
| Canonical tier-0 body | WorldState `get_summary()` — active_plots, destroyed entities |
| Advisory | resolved_plots + plot_suspension + entity_destruction all pass through unsuppressed ✅ |
| Stage 4 enforcement | ContinuityValidator compares prev_hud vs current state |
| Persistence | StateTracker: resolved_plots (max 500), entity_destructions, active_plots |

**Verdict: PARTIALLY ALIGNED.** Data exists in both persistence and advisory channels. The gap is that there is no canonical authority declaration or enforcement specifically for plan-vs-outcome reconciliation. In practice, this works because the LLM sees both planned (blueprint) and realized (manuscript) data. The risk of silent contradiction is low.

## 3. Classification

### Covered Well Enough Now

1. **NPC life/death/current presence** — canonical + pre-check + hard-block. Triple coverage.
2. **Numeric business/resource state** — canonical block + explicit authority statement + advisory suppression. Strongest coverage.
3. **Relationships** — canonical block (L0-Graph) + Stage 4 enforcement. Solid.
4. **Item ownership/state** — canonical body + two CRITICAL Stage 4 checks. Strong enforcement.

### Partially Aligned

5. **Injuries/healing/recovery** — canonical body carries protagonist; NPC injury depends on `known_attrs` population; permanent_injury unsuppressed. Residual risk is LOW because the high-stakes category (permanent injuries) passes through.
6. **Location/movement/geography** — canonical body + destroyed-location enforcement. General geography and fight geography are unmodeled but are structural problems, not contract alignment issues.
7. **Time/chronology** — canonical body + ContinuityValidator. No blocking enforcement for temporal impossibilities, but rare in practice.
8. **Organization/sect membership** — organizations tracked as entities; membership edges absent. Embedded in role descriptions. Risk is MEDIUM for complex hierarchies.
9. **Planned-vs-realized event outcomes** — data in persistence + advisory channels. No explicit authority. Risk is LOW because LLM sees both plan and outcome.

### Clearly Residual Risk

10. **Wuxia technique use history / realm progression** — no canonical authority, no enforcement, no NPC tracking. Protagonist tracking exists in advisory only. This is the one fact family where Wave 1 contract alignment did not reach and where production contradictions are plausible.

### Deferred Structural Problems

These are not contract-alignment residuals — they are modeling gaps that predate Wave 1 and cannot be solved by authority statements or suppression:

| Problem | Nature |
|---------|--------|
| NPC technique/mastery tracking | No persistence layer tracks NPC skills |
| Organization membership edges | No NPC-to-org mapping |
| Fight-specific geography | No structured spatial field |
| Cross-episode tactical escalation | ActionSceneEvaluator is intra-manuscript only |
| Event causality chains | No system tracks "Event A caused Event B" |

## 4. Investigation Question Answers

### Q1. Which fact families are now clearly covered after Wave 1?

NPC life/death, numeric/business state, relationships, item ownership. These 4 families have canonical injection, explicit authority precedence, and Stage 4 enforcement.

### Q2. Which fact families still have ambiguous ownership?

**Technique/realm**: StateTracker is the only owner but has no canonical authority declaration and no enforcement. The LLM sees skills as advisory, not as constraint.

**Organization membership**: FactLedger owns org entities but no system owns membership edges.

**Injuries**: WorldState and StateTracker both track injuries but canonical tier-0 block does not explicitly include injury status. The data is present in canonical body but without an explicit authority claim.

### Q3. Which seams are most likely to create real narrative contradictions?

1. **Technique/realm (HIGH)** — In a long wuxia series, protagonist could display techniques inconsistently or use abilities beyond their established realm. No enforcement catches this.
2. **Organization membership (MEDIUM)** — NPC could switch sect allegiance without proper narrative justification. Embedded in role descriptions but not structurally enforced.
3. **Injuries (LOW)** — NPC injury state could be inconsistent if WorldState `known_attrs` is sparse. Mitigated by permanent_injury passing through unsuppressed.

### Q4. Which residual seams are prompt-only / pre-check candidate / validator candidate / deferred?

| Seam | Classification | Rationale |
|------|---------------|-----------|
| Technique/realm authority precedence | **Prompt-only** | StateTracker advisory passes through but lacks authority declaration |
| Destroyed item as available (Stage 3) | **Pre-check candidate** | Same pattern as dead-NPC pre-check; already has Stage 4 enforcement |
| NPC technique consistency | **Validator candidate** | Could check "NPC used technique X but X was never established" |
| NPC realm-vs-technique gate | **Validator candidate** | Could check "NPC performed realm-8 technique but was established at realm-3" |
| Organization membership edges | **Deferred modeling** | Requires new persistence field, not just contract alignment |
| Fight geography | **Deferred modeling** | Requires new persistence field |
| Cross-episode escalation | **Deferred modeling** | Requires new ActionSceneEvaluator cross-episode state |
| Event causality chains | **Deferred modeling** | Requires new persistence design |

### Q5. Is a Wave 2 justified now, or should the system stop here?

**Not yet.** The dominant residual (technique/realm) is a **structural modeling problem**, not a contract-alignment problem. Wave 1 was scoped to contract alignment (authority statements + suppression + one pre-check). A Wave 2 in the same frame (contract alignment) would have diminishing returns.

The right next step, if any, is a **design memo** analyzing whether technique/realm tracking warrants a field extension to StateTracker and whether a Stage 3 destroyed-item pre-check is worth the bounded cost. This is design work, not contract alignment.

## 5. Recommendation

**One design memo**, scoped to:
1. Feasibility of extending StateTracker with per-NPC technique tracking (similar to existing `protagonist_skills` but for NPCs, with arc-level granularity)
2. Feasibility of adding a Stage 3 destroyed-item pre-check (following the dead-NPC pre-check pattern)
3. Whether technique/realm deserves a canonical authority declaration in the tier-0 prompt

Not included in that memo:
- Organization membership edges (lower risk, needs broader modeling design)
- Fight geography (structural problem, needs its own design pass)
- Causality chains (lowest priority, structural problem)
- Any registry, persistence redesign, or DB schema change

---

## 3-Pass Audit Record

Pass 1. Structure and Scope
- Survey type correct (post-wave residual, no code changes)
- 10 fact families analyzed individually with per-layer coverage
- Wave 1 treated as closed baseline — no reopening
- Registry-by-default assumptions explicitly not reopened
- Four-way distinction maintained (prompt / pre-check / validator / deferred)
- PASS

Pass 2. Evidence and Consistency
- Authority statement verified at stage4_context_builder.py:996-1008
- Suppression logic verified at stage4_context_builder.py:939-971 — confirms layer-existence check, not content check
- Stage 3 pre-check verified at stage3_orchestrator.py:1552-1602
- Canonical injection verified at stage4_context_builder.py:1681-1700 — confirmed position 0 in tier0_parts
- Advisory injection and suppression verified at stage4_context_packets.py:715-784
- WorldState `get_canonical_constraints()` verified at world_state.py:764-806 — confirmed NPC fixed attrs + relationship edges only
- FactLedger `get_canonical_summary()` verified at fact_ledger.py:767-781 — confirmed numbers only
- Suppression does NOT cause information loss — confirmed that WorldState `get_summary()` (50K) and FactLedger `to_summary()` (25K) are injected at tier-0 body alongside canonical block
- PASS

Pass 3. Execution and Readability
- Findings-first structure
- Clear 4-tier classification (covered / partially aligned / clearly residual / deferred)
- Single recommendation: one design memo
- No scope creep into execution SSOT or code changes
- PASS

Estimated confidence: 97%

---

- Residual contract-alignment need: **low**
- Dominant remaining seam: **technique-realm-tracking-has-no-canonical-authority-or-enforcement**
- Should Codex open a new execution SSOT now: **no**
