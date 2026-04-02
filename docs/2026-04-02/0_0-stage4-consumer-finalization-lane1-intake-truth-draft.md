# 0_0 Stage4 Consumer-Finalization Lane 1 — Intake Truth Ownership Draft

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Document Type: bounded lane survey draft
Lane: Terminal 1 — Stage4 intake / context truth ownership
Master Order: `docs/2026-04-02/0_0-stage4-consumer-finalization-global-parallel-master-order.md`
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
Mode: read-only static survey

## 1. Coverage

### Files Inspected

| File | Lines | Purpose |
|---|---|---|
| `modules/core/stage4_context_builder.py` | 2801 | Context assembly + retrieval + mandatory_context tiering |
| `modules/domain/agents/chief_writer_context.py` | 616 | CW prompt assembly (`build_common_context`) |
| `modules/core/stage4_interview_round.py` | 6820 | Round execution, `_build_common_writer_kwargs`, `_prepare_round_execution` |
| `modules/core/stage4_types.py` | 92 | `_RoundContext` (31-field slots dataclass) |
| `modules/core/stage4_orchestrator.py` | partial | `_prepare_episode_round`, `_build_episode_round_context` |

### Delegation Chain Traced

```
Stage4Orchestrator._prepare_episode_round()
  → Stage4ContextBuilder.prepare_episode_context()
      → _build_episode_base_payload()    [arc_pos, tactical, prev_text, lookback tiers, digest]
      → _build_episode_state_payload()   [HUD, inventory, dead_npcs, chain_link, world_state_summary]
  → Stage4ContextBuilder.build_mandatory_context()
      → _build_mandatory_context_seed()  [cp_entities, work_focus, tier0 assembly]
      → _build_mandatory_context_retrieval_coverage()  [tier1/tier2 + SC retrieval]
      → _build_mandatory_prompt_injections()  [anti-trope, justification, reflexion]
  → Stage4ContextBuilder.build_round_context()
      → _RoundContext(31 fields)
  → Stage4InterviewRound.run()
      → _prepare_round_execution()
          → _build_common_writer_kwargs()  [31 kwargs for CW]
```

## 2. Findings

### F-1. Tier 0 Authority Stack Is Well-Defined in Code But Rendered to Prose

Stage4 context builder assembles Tier 0 in `_build_tier0_mandatory_sections()` (L1626-1759) with explicit insertion ordering:

1. **Canonical constraints** (L1696-1714): `WorldState.get_canonical_constraints()` + `FactLedger.get_canonical_summary()` + authority statement
2. **Continuity Packet** (L1734-1747): NPC/item/plot entities cross-referenced against world_state
3. **Fact Ledger summary** (L1678-1693): `FactLedger.to_summary(max_chars=25000)`
4. **Timeline** (L1667-1676): `WorldState.get_timeline_summary()`
5. **World State summary** (L1650-1665): `WorldState.get_summary(max_chars=50000)`
6. **mandatory_context base** (L1644): from `_build_writer_mandatory_context(db, bible, ep)`
7. **Arc constraint summary** (L1646-1648)

**All of these arrive at CW/Director as prose text blocks inside `mandatory_context` string.** The LLM sees authority precedence only via text declarations like `"WorldState current-state facts override extracted or advisory summaries on conflict."` (L1008).

This is not a bug — it is a deliberate design choice with a known consequence: the LLM must interpret authority from text, not from structured constraints.

### F-2. Authority Contract Is Explicit and Code-Enforced

Two complementary mechanisms enforce canonical authority:

1. **Code-side** (`_filter_state_tracker_summaries_for_authority`, L939-971): Suppresses 7 StateTracker domains (`dead_npc`, `item_state`, `relationship_changes`, `npc_injury`, `npc_movement`, `time_timeline`, `financial_state`) when canonical layers (WorldState/FactLedger) are present. Suppressed domains are replaced by a note referencing the canonical source.

2. **Prompt-side** (`_build_persisted_authority_statement`, L1001-1013): Injects explicit text declaring `"WorldState current-state facts override extracted or advisory summaries on conflict"` and `"FactLedger numeric facts override BI seed numbers and arc-derived summaries on conflict"`.

Together these form the **Wave 1 authority contract** (documented in code comments at L995-999).

### F-3. Structural Upstream Truths Flattened to Prose at Intake Boundary

| Upstream Source | Intake Format | Structural Loss |
|---|---|---|
| `arc_data.tactical_doc` | String (`arc_tactical`) | dict→string cast (L2125-2127) |
| `WorldState` canonical layer | Prose `world_state_summary` (50K chars) | Structured dict → prose rendering |
| `FactLedger` | Prose `fact_ledger_summary` (25K chars) | Structured entity facts → prose |
| `chain_link_{ep}` DB anchor | Prose `chain_link_section` | Structured dict → prose section (L1389-1424) |
| `cumulative_bible` | Only `dead_npcs` extracted (L2175-2178) | Full bible → single field |
| `state_changes` (arc) | Entity extraction only, not forwarded structurally | Arc state semantics lost |

The flattening is intentional (prose is what LLMs consume) but means that **all upstream structural queryability is lost at the intake boundary**. If the LLM misinterprets a text-based authority declaration, there is no structured contract to enforce it.

### F-4. Integrated Scenario Advisory Is Explicitly Demoted

In `chief_writer_context.py` L296-301, the `integrated_scenario_advisory` is wrapped with:

```
"이 블록은 흐름 참고용이다. Opening Anchor / Immutable Facts / writer hard canon / prev digest /
structured scene contract와 충돌하면 아래 prose는 버려라."
```

This is correct — it prevents Stage 2's scenario prose from overriding Stage 4's contractual truth layers. However, the demotion is only stated in text; there is no code-level enforcement that prevents CW from following the advisory over hard canon if the LLM fails to parse the precedence.

### F-5. Blueprint UI Contamination Sanitization

`_sanitize_writer_blueprint_payload()` (L111-124) strips lines containing UI contamination markers (`상태창`, `시스템 메시지`, `홀로그램`, etc.) from blueprint text before CW sees it. This is a **code-enforced** truth gate — contaminated blueprint prose is removed, not just demoted.

### F-6. Context Budget Can Drop Truth Sections

The tiered budget system (`_compose_tiered_mandatory_context_with_headroom`, L1266-1383) can trim or drop sections when the total exceeds `context.mandatory_context_max` (default 400K chars). Trim order:

1. Regular tier2 sections first (ratio=0.7)
2. Protected sections (work slot summary, arc_semantic_carryover) trimmed gently (ratio=0.88)
3. Emergency trim if still over budget (regular=0.5, protected=0.68)

**Risk**: Tier 0 canonical sections are not explicitly protected from the final hard trim at L1366-1372 (`compressor._smart_trim(mandatory_context, limit)`). If tier0 content alone exceeds the budget, canonical truth can be truncated.

### F-7. Prev Manuscripts Text Uses 3-Tier Lookback

`_build_prev_manuscripts_text()` (L1983-2096) constructs a tiered lookback:

- **Tier 1**: Full text of last 30 episodes (L1987-2011)
- **Tier 2**: Summaries for episodes 31-60 back (L2013-2039)
- **Tier 3**: Arc summaries for older episodes (L2041-2095)

This is a well-structured degradation. The lookback is **machine-readable at load time** (DB queries), but arrives at the LLM as concatenated prose.

### F-8. Immutable Fact Contract (IFC) Assembles Across Multiple Sources

`_build_immutable_fact_section()` in `chief_writer_context.py` (L538-574) imports `build_packet()` from `stage4_immutable_fact_contract.py` and combines:
- Blueprint facts
- Previous manuscript ending (last 2500 chars)
- World state summary
- Fact ledger summary
- Chain link section
- Previous digest

This creates a separate **hard canon** section injected into the CW prompt via `build_chief_writer_main_prompt()`. The IFC is the closest thing to a structured truth contract at the CW prompt level.

### F-9. Post-Select Conflict Contract Structure

`_build_post_select_conflict_contract()` (L127-187 in interview_round) constructs a structured dict contract with typed `conflict_type` (`continuity` | `history` | `check_error`) when conflicts are detected post-selection. This is machine-readable and carries `bounded_local_fix_hint` and `target_kind` signals.

This is a **post-intake** truth structure, but it's worth noting that it is one of the few places where Stage4 maintains structural truth rather than prose.

## 3. Non-Issues

### NI-1. Protagonist Name Resolution
Triple fallback (ctx callback → world_state → bible) at L197-225 is well-ordered with non-blocking error handling.

### NI-2. NPC Roster Collection
`_collect_npc_roster()` (L276-341) extracts from 8 state_change fields + 3 blueprint sections. Thorough and deduped.

### NI-3. NPC Boundary Block
`_build_npc_boundary_block()` (L560-654) merges alive/dead NPC info from world_state, key NPC data from bible, and known_attrs. Advisory-only (explicitly marked as reference).

### NI-4. Retrieval Plan Execution
Multi-source routing (VEC_MEMORY, DB_NPC_HISTORY, DB_NPC_RELATIONSHIP, STATIC, manuscript_db) with per-slot budget at L1015-1117. Budget tracking and compression are well-instrumented.

### NI-5. Writing Directive Injection
`WritingDirective` dataclass (stage4_types.py L77-91) is passed intact from Stage4 setup to CW. Not flattened until prompt rendering in `_build_writing_directive_section()`.

### NI-6. Blueprint Entity Cross-Reference
`_extract_blueprint_entities()` (L475-558) intersects blueprint text mentions with world_state alive/dead NPCs, active items, and active plots. This preserves structural linkage at the entity extraction step.

### NI-7. StateTracker Authority Suppression
`_filter_state_tracker_summaries_for_authority()` (L939-971) correctly suppresses 7 overlapping domains when canonical layers are present, preventing truth-split between arc-derived summaries and persisted canonical layers.

## 4. Verdict

**intake-mixed**

**Justification:**

Stage4 intake has a **well-defined authority hierarchy** (canonical > advisory > retrieval) that is both code-enforced (StateTracker domain suppression, UI contamination stripping) and prompt-declared (authority precedence statements, integrated_scenario demotion).

However, the intake is **mixed** rather than **intake-clean** because:

1. **Structural flattening**: All canonical upstream truth (WorldState, FactLedger, chain_link, arc_data) is rendered to prose strings before reaching the LLM. The authority contract relies on the LLM correctly interpreting text-based precedence declarations.

2. **Budget trim risk on Tier 0**: The final hard trim (`_smart_trim(mandatory_context, limit)`) does not explicitly protect Tier 0 canonical sections. If canonical content exceeds the budget, truth can be truncated.

3. **Integrated scenario demotion is text-only**: The Stage 2 integrated scenario advisory is marked as low-priority in text, but there is no code-level enforcement preventing the LLM from following it over hard canon.

These are design trade-offs, not bugs. The intake architecture is sound for an LLM-based pipeline, but the authority contract between upstream structural truth and downstream prose consumption is soft rather than hard.

**Single highest-impact normalization candidate (from intake perspective):**

Protecting Tier 0 canonical sections from the final hard trim step. Currently, the `_smart_trim()` at L1366-1372 treats the entire `mandatory_context` string as uniform text. Adding a protected prefix or section marker for Tier 0 content would prevent canonical truth truncation under budget pressure.

## 5. Stop

read-only lane complete; no files mutated
