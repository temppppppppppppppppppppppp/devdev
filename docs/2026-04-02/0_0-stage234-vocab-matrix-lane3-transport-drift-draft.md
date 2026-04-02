# 0_0 Stage234 Vocab Matrix Lane 3: Transport and Boundary Drift Draft

- date: 2026-04-02
- status: draft-bounded-partial-evidence
- lane: 3 (transport and boundary drift)
- role: Opus Terminal 3
- parent order: `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-parallel-master-order.md`
- guardrails: survey only, read-only, no code edits, no DB writes, no docs/temp mutation, static analysis only

## Coverage

Inspected surfaces:

- `modules/domain/agents/blueprint_constraint_compiler.py` — Stage2→Stage3 constraint compilation boundary
- `modules/core/stage4_context_builder.py` — Stage4 Tier 0 truth intake and prompt assembly
- `modules/domain/agents/chief_writer_context.py` — CW context consumption surface
- `modules/core/stage4_post_pass_runtime.py` — Stage4 post-pass state truth persistence

Cross-referenced survey baselines:

- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md` (Stage4 consumer survey, already proven)
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md` (Stage2 survey)
- `docs/2026-04-02/0_0-stage3-static-global-bounded-survey.md` (Stage3 survey)

## Findings

### Finding 1: Stage2→Stage3 boundary is structure-to-prose with alias renames

`BlueprintConstraintCompiler.compile()` is the formal Stage2→Stage3 boundary gate. It reads `arc_data` (the Stage2 output) and produces a `constraint_block` dict. The transport behavior is:

| Stage2 field | Transport | Stage3 field name | Structure preserved? |
|---|---|---|---|
| `tactical_doc` | regex extraction via `extract_episode_tactical()` | `must_focus.content` | Partial — episode-scoped text only |
| `constraint_summary` | pass-through string | `arc_constraint_summary` | Yes — but renamed |
| `state_changes` | `_summarize_state_changes()` | `state_changes_summary` | No — dict→prose |
| `episode_details` | used for title/focus priority | `must_focus.arc_title` | Partial |
| `beat_sequence` | fallback only, type-unstable (dict|str) | `must_focus.content` (fallback) | No |
| `semantic_carryover` | `_normalize_semantic_carryover()` | `semantic_carryover` | Shape preserved but often empty/low-signal |

New artifacts synthesized at this boundary (not passed through from Stage2):

- `fact_lock_packet` — synthesized from `prev_blueprint` + `prev_manuscript_ending` + `arc_data`
- `capital_continuity_packet` — investment-genre only, synthesized from prior state
- `immutable_fact_carryover` — prior-arc recovery obligations

Evidence lines:
- `blueprint_constraint_compiler.py` L44-136: `compile()` shows the full field mapping
- `blueprint_constraint_compiler.py` L97: `_summarize_state_changes()` compresses dict→prose
- `blueprint_constraint_compiler.py` L98: `_normalize_semantic_carryover()` — normalizes but often receives empty input
- `blueprint_constraint_compiler.py` L92-94: `constraint_summary` field is renamed to `arc_constraint_summary` without explicit mapping declaration

### Finding 2: Stage3→Stage4 handoff destroys the constraint hierarchy

Stage3's internal constraint hierarchy (`IMMUTABLE > HARD CONSTRAINT > EXPECTED CONTINUITY > ADVISORY`) does NOT survive into Stage4. The Stage3→Stage4 handoff is a single blueprint dict stored in DB.

Stage4 receives:
- blueprint dict (scene_breakdown, integrated_scenario, ending_hook, etc.)
- arc_data (direct Stage2 pass-through)

Stage4 does NOT receive:
- Stage3's constraint priority banding metadata
- Stage3's prevalidation results or binding verdicts
- Stage3's fact_lock, capital_continuity, or immutable_fact structure as tagged authority blocks

Instead, Stage4 independently rebuilds its own Tier 0 authority stack:

```
canonical constraints (world_state NPC L0 + fact_ledger numeric L0)
  > continuity packet (blueprint-entity intersection with world_state)
  > fact ledger summary (25K prose)
  > timeline summary
  > world state summary (50K prose)
  > mandatory_context (arc constraints, etc.)
  > arc_constraint_summary (Stage2 pass-through)
```

Evidence lines:
- `stage4_context_builder.py` L1626-1748: `_build_tier0_mandatory_sections()` shows full rebuild from ctx sources
- `stage4_context_builder.py` L1646-1648: `arc_constraint_summary` read directly from `arc_data`, not from Stage3 output
- `stage4_context_builder.py` L1650-1665: `world_state_summary` built from Python `world_state` object
- `stage4_context_builder.py` L1678-1693: `fact_ledger_summary` built from Python `fact_ledger` object
- `stage4_context_builder.py` L1695-1712: `canonical_constraints` built from persisted authority stores

Implication: Stage3's constraint compilation work is partially redundant because Stage4 cannot see it and rebuilds from upstream sources. The `compile_to_prompt()` output in `blueprint_constraint_compiler.py` is consumed only by Stage3's internal LLM generation, not by Stage4.

### Finding 3: Stage4 Tier 0 truth intake flattens all authority to prose

All Stage4 Tier 0 sections enter the CW prompt as prose blocks, regardless of their upstream structure:

| Truth source | Upstream structure | Stage4 intake form | CW prompt form |
|---|---|---|---|
| `world_state` | Python dict (`_state`) | `get_summary(50K)` → prose | prose block |
| `fact_ledger` | Python dict (`_ledger`) | `to_summary(25K)` → prose | prose block |
| `canonical_constraints` | structured NPC + numeric entries | `get_canonical_constraints()` → prose | prose block |
| `continuity_packet` | entity list intersection | `build_continuity_packet()` → prose | prose block |
| `arc_constraint_summary` | Stage2 string | pass-through | `[Arc 제약 - MUST NOT DO]` block |
| `chain_link_section` | DB anchor JSON | `load_chain_link_section()` → prose | prose block |

The chief_writer_context.py L114-282 `build_common_context()` signature shows that ALL authority enters as string parameters, with `self.host._escape_braces()` applied universally. There is no machine-readable authority tagging once content enters the CW prompt.

Evidence lines:
- `chief_writer_context.py` L206-210: `_build_immutable_fact_section()` renders to prose
- `chief_writer_context.py` L215-224: `_build_writer_core_sections()` splits into hard_canon (prose) and soft_guidance (prose)
- `chief_writer_context.py` L233-282: `build_chief_writer_main_prompt()` call — all arguments are strings
- `stage4_context_builder.py` L2186-2191: `world_state_summary` is prose (50K chars)

### Finding 4: Stage4 post-pass state truth splits into three unreconciled surfaces

After PASS, Stage4 persists truth through three separate owners:

| Truth surface | Owner | Persistence path | Content |
|---|---|---|---|
| `final_state_updates` | Director (LLM) | interview round judgment | episode resolution as Director sees it |
| `actual_truth` | Manager (LLM) | `state_updates_from_audit.actual_truth` | episode state as Manager reads manuscript |
| `world_state` | Python | `world_state.update_from_state_changes()` + `.save()` | cumulative world state dict |

Additional:
- `active_pressure_vectors` are injected INTO `actual_truth` dict at L467, making Manager truth the carrier for blueprint-derived pressure data that Manager did not author
- `bible_delta` is assembled from mixed sources (actual_truth, final_state_updates, arc_data) at L746-765
- `fact_ledger` is updated from both `world_state_changes` and `bible_delta` separately at L1097-1103

The merge at `_merge_storage_only_state_change_families()` (L70-88) uses `actual_truth` as base and `final_state_updates` as fallback — but only for `npc_martial_state_changes`, a single storage-only family. The broader reconciliation between Director truth, Manager truth, and Python truth does not happen.

Evidence lines:
- `stage4_post_pass_runtime.py` L70-88: merge function only handles one family
- `stage4_post_pass_runtime.py` L281-414: `_collect_manager_and_build_delta()` shows actual_truth coming from Manager LLM
- `stage4_post_pass_runtime.py` L416-473: `_apply_state_text_and_pressure_vectors()` mutates actual_truth with pressure vectors
- `stage4_post_pass_runtime.py` L555-566: `_prepare_manager_delta_context()` shows actual_truth extraction from Manager audit
- `stage4_post_pass_runtime.py` L1050-1091: `_persist_atomic_world_state()` updates Python WorldState independently

### Finding 5: Alias renames without explicit canonical mapping

Cross-stage field renames observed with no mapping declaration:

| Concept | Stage2 name | Stage3 name | Stage4 intake name | Post-pass name |
|---|---|---|---|---|
| Episode mission | `tactical_doc` | `arc_focus` (LLM prose) | `arc_tactical` | (not persisted as such) |
| Arc constraint | `constraint_summary` | `arc_constraint_summary` | `[Arc 제약 - MUST NOT DO]` | (consumed, not persisted) |
| State mutations | `state_changes` (dict) | `state_changes_summary` (prose) | via `_collect_arc_state_entities()` | `persisted_state_changes` / `bible_delta.state_changes` |
| NPC roster | `state_changes.npc_*` fields | blueprint `npcs` lists | `_collect_npc_roster()` → `cp_entities.npcs` | `bible_delta.new_npcs` / `world_state.alive_npcs` |
| Carryover facts | `constraint_summary` | `fact_lock_packet.anchors` | `canonical_constraints` / `continuity_packet` | `world_state` + `fact_ledger` |
| World truth | (not in Stage2) | (not in Stage3) | `world_state_summary` (50K prose) | `world_state._state` (dict) |
| Fact truth | (not in Stage2) | (not in Stage3) | `fact_ledger_summary` (25K prose) | `fact_ledger._ledger` (dict) |
| Pressure vectors | (not in Stage2) | (not in Stage3) | (not in intake) | `actual_truth.active_pressure_vectors` |

The `missing_semantic_carryover` coverage warning at L840-843 in `stage4_context_builder.py` explicitly acknowledges that semantic_carryover planned at Stage2 does not survive into Stage4.

### Finding 6: The most redundant translation pressure is at the Stage3→Stage4 boundary

Stage4 independently re-derives the truth that Stage3 already compiled:

1. Stage3's `BlueprintConstraintCompiler` reads `arc_data.constraint_summary` and compiles it into `constraint_block.arc_constraint_summary`
2. Stage4's `_build_tier0_mandatory_sections()` reads the same `arc_data.constraint_summary` directly and injects it as Tier 0
3. Stage3's `fact_lock_packet` is compiled from prev_blueprint + manuscript truth
4. Stage4's canonical_constraints block is independently built from `world_state.get_canonical_constraints()` + `fact_ledger.get_canonical_summary()`

This means the Stage3→Stage4 boundary carries **blueprint-shaped output** but Stage4 does not trust that output for authority — it re-fetches authority from persistent stores. The translation pressure is therefore in two places:

- Stage3 LLM translating constraints INTO blueprint prose (which Stage4 then treats as advisory)
- Stage4 rebuilding authority independently (which duplicates constraint compilation effort)

## Non-Issues

1. **Stage3→Stage4 handoff architecture is clean.** The DB-serialized blueprint dict is a well-defined boundary. The issue is not transport corruption but semantic authority loss.

2. **Stage4 Tier 0 injection ordering is deliberate.** The `insert(0, ...)` pattern creates a stable priority stack. The code comment at L1635-1642 explicitly documents the intended ordering.

3. **Genre-specific transport packets are bounded.** The `capital_continuity_packet` (investment) and wuxia technique/realm clause are genre-conditional and do not create cross-genre alias confusion.

4. **`_fit_context_text()` truncation is budgeted.** The truncation at each boundary is explicit and logged. This is design-time budget management, not accidental loss.

## Boundary Drift Ledger

### Ledger A: Structure-to-Prose Boundaries

| Boundary | Input structure | Output form | Reversibility |
|---|---|---|---|
| `state_changes` → `state_changes_summary` | dict with typed lists | prose string | Irreversible |
| `world_state._state` → `world_state_summary` | nested dict | 50K prose | Irreversible |
| `fact_ledger._ledger` → `fact_ledger_summary` | nested dict | 25K prose | Irreversible |
| `canonical_constraints` → prompt block | structured entries | prose authority block | Irreversible |
| `continuity_packet` → prompt block | entity intersection list | prose NPC/entity summary | Irreversible |
| Blueprint constraint hierarchy → blueprint dict | banded priority metadata | flat JSON dict | Irreversible |

### Ledger B: Alias Renames Without Canonical Mapping

| Rename | From | To | Mapping declared? |
|---|---|---|---|
| `constraint_summary` → `arc_constraint_summary` | Stage2 arc field | Stage3 constraint_block field | No |
| `tactical_doc` → `arc_tactical` | Stage2 arc field | Stage4 context builder local | No |
| `state_changes` → `state_changes_summary` | Stage2 dict | Stage3 compiled prose | No |
| `actual_truth` → `latest_state.actual_truth` | Manager audit output | Persisted state | No (implicit nesting) |
| `active_pressure_vectors` → inside `actual_truth` | Blueprint-derived | Injected into Manager truth | No |

### Ledger C: Owner Drift at Boundaries

| Concept | Stage2 owner | Stage3 owner | Stage4 intake owner | Post-pass owner |
|---|---|---|---|---|
| Episode mission | Arc LLM | BlueprintEnsemble LLM | (not re-owned) | (consumed) |
| Constraint authority | Arc LLM | BlueprintConstraintCompiler (Python) | Stage4ContextBuilder (Python) | (consumed) |
| NPC state | `state_changes` (Arc LLM) | blueprint `npcs` (LLM reinterpretation) | `world_state` + `continuity_packet` (Python) | `world_state` (Python) + `actual_truth` (Manager LLM) |
| World truth | (not produced) | (not produced) | `WorldStateManager` (Python) | `WorldStateManager` (Python) |
| Fact truth | (not produced) | (not produced) | `FactLedger` (Python) | `FactLedger` (Python) |
| Pressure vectors | (not produced) | (not produced) | (not in intake) | Manager `actual_truth` dict (injected by Python) |

### Ledger D: Dead or Low-Signal Transport Channels

| Channel | Status | Evidence |
|---|---|---|
| `semantic_carryover` | Low-signal / often empty | `stage4_context_builder.py` L840-843 explicit warning for missing survival |
| `beat_sequence` | Fallback only, type-unstable | `blueprint_constraint_compiler.py` L287-296 dict/str ambiguity |
| `episode_details` | Thin or absent in practice | `blueprint_constraint_compiler.py` L327-335 multi-key probe suggests unreliable content |
| Stage3 constraint priority metadata | Completely lost at handoff | Stage4 rebuilds from persistent stores |

## Verdict

`transport-lossy`

More precisely:

- **Stage2→Stage3 boundary**: `mixed` — some pass-through, some compression, one alias rename, some new synthesis
- **Stage3→Stage4 boundary**: `lossy` — constraint hierarchy completely lost, Stage4 independently rebuilds authority
- **Stage4 intake→CW prompt**: `prose-flattened` — all structured truth becomes prose at prompt assembly
- **Stage4 post-pass state split**: `unreconciled` — three truth owners persist independently without reconciliation

The most costly boundary is **Stage3→Stage4**: Stage3's constraint compilation work is partially wasted because Stage4 cannot see it and re-derives authority from persistent stores. This is the boundary that adds the most redundant translation pressure.

The second most costly boundary is **Stage4 intake→CW prompt**: all Tier 0 authority (canonical constraints, continuity packet, world state, fact ledger, chain link) is rendered to prose. The LLM has no machine-readable way to distinguish Tier 0 from advisory content once it enters the prompt.

## Stop

read-only lane complete; no files mutated
