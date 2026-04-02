# 0_0 Stage234 Vocab Matrix Lane 4: Vertical Slice Draft

Date: 2026-04-02
Status: draft-bounded-partial-evidence
Document Type: survey lane draft
Lane: 4 — representative vertical slices
Terminal: Opus Terminal 4
Master Order: `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-parallel-master-order.md`
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`

## Coverage

### Inspected Slices

| Slice | Project | Episodes | Evidence Source |
|---|---|---|---|
| A | 0_0 main | ep2 | `project_data.db` anchors, blueprints, director_selections, state_logs, episode_production.jsonl |
| B | 0_0 main | ep5, ep6 | `project_data.db` director_selections, blueprints |
| C | canary_0_0_stage34_arc2_fixpack_r1 | ep2, ep3 | `project_data.db` director_selections, episode_production.jsonl (25 entries) |
| D | canary_0_1_stage34_ep14_cw_hierarchy | ep9, ep13 | `project_data.db` blueprints, director_selections, state_logs |

### Inspected Code Surfaces

- `modules/core/stage4_post_pass_runtime.py`: `world_state` persistence, `active_pressure_vectors` transport
- `modules/core/stage4_post_processor.py`: `final_state_updates` consumption (30+ references)
- `modules/core/stage4_context_builder.py`: `constraint_summary` Tier-0 promotion
- `modules/domain/agents/blueprint_constraint_compiler.py`: `constraint_summary` → `arc_constraint_summary` rename
- `modules/validation/continuity_validator.py`: `actual_truth` consumption (30+ references)

### Not Inspected

- 0_1 ep15 (0_1 main project DB empty, canary only goes to ep14)
- 0_0 ep3, ep4 in deep artifact detail (covered by Stage4 consumer survey already)
- Runtime prompt payloads (not stored in DB in full)

## Findings

### Finding 1: Cross-Stage Term Inventory From Real Artifacts

Tracing real artifact fields across Stage2 arc_payload, Stage3 blueprint, and Stage4 director_selection/state_logs reveals a consistent pattern of rename, drop, and strength inversion.

| Stage2 Field | Stage3 Equivalent | Stage4 Equivalent | Drift Type |
|---|---|---|---|
| `tactical_doc` (str 4312ch) | `integrated_scenario` (str 1614ch) | consumed as prose via context_builder | **prose compression + rename** (63% reduction) |
| `constraint_summary` (str 599ch) | `arc_constraint_summary` (renamed in compiler) | Tier-0 `[Arc 제약 - MUST NOT DO]` hard prohibition | **strength inversion**: advisory in Stage3 → hard in Stage4 |
| `beat_sequence` (list 5 items) | DROPPED | N/A | **field death** at Stage2→3 boundary |
| `hybrid_composition` (dict 3 keys) | DROPPED | N/A | **field death** at Stage2→3 boundary |
| `state_constraints` (dict 4 keys) | embedded in scene prose | N/A | **prose flattening** |
| `state_changes` (dict 8 keys) | compressed/demoted | → `actual_truth` (state_logs) + `world_state` (anchor) | **owner split + rename** |
| `joint_docs` (dict 3 keys) | not carried | consumed as context prose | **prose flattening** |
| `episode_details` (list 5 items) | not carried | N/A | **low-signal / demotion** |
| `semantic_carryover` (dict 0 keys) | N/A | N/A | **dead field** (empty in all inspected slices) |
| N/A | `scene_breakdown` (dict 4-5 scenes) | consumed as blueprint dict | Stage3-originated |
| N/A | `_inventory_gaps` (list 3-7 items) | consumed in Stage4 interview | Stage3-originated |
| N/A | `_stage3_meta` (dict 5 keys) | not consumed | Stage3-local metadata |
| N/A | N/A | `fix_pack` (dict 6 keys) | Stage4-originated |
| N/A | N/A | `gate_semantics` (dict 7 keys) | Stage4-originated |
| N/A | N/A | `authoritative_fix_scope` | Stage4-originated |
| N/A | N/A | `post_select_conflict` | Stage4-originated |
| N/A | N/A | `final_state_updates` | Director-originated |
| N/A | N/A | `actual_truth` | Manager-originated |

Evidence: `projects/0_0/project_data.db` anchors `arc_payload_0002` vs blueprints ep2-6 vs director_selections ep2.

### Finding 2: EP2 Proves The Fix-Scope Split-Truth Pattern

0_0 main ep2 `STAGE4_RETRY_PATHOLOGY` entry in `episode_production.jsonl`:

```
pathology_fingerprint: post_select_conflict|fix_pack:missing_fix_pack
reject_bucket: post_select_conflict
gate_basis: post_select_conflict
fix_scope: full
authoritative_fix_scope: inplace
repair_scope: full
scope_origin: {fix_scope: runtime_widened, authoritative_fix_scope: director_authoritative, repair_scope: runtime_lane}
```

This is not naming noise. The same concept (`어디를 어떻게 고칠지`) has three simultaneous names with different owners:
- `fix_scope`: runtime-widened to `full`
- `authoritative_fix_scope`: Director says `inplace`
- `repair_scope`: runtime lane says `full`

The `scope_origin` field explicitly tracks that the vocabulary split happened: `fix_scope: runtime_widened` vs `authoritative_fix_scope: director_authoritative`.

### Finding 3: EP5/EP6 Show Contract Degradation Under Retry Pressure

0_0 main ep5 (round 6, score 91) and ep6 (round 9, score 90) director_selections have:
- `gate_semantics`: **empty** (all keys `None`)
- `fix_pack`: **empty** (all fields empty/0)
- `authoritative_fix_scope`: **absent**

Compare to ep2 (round 0, score 96):
- Full `gate_semantics` with all 7 keys populated
- Full `fix_pack` with `patch_targets`, `must_fix`, `do_not_regress`, `success_condition`

This means the structured repair contract degrades exactly when it is most needed (high-retry episodes). The vocabulary itself becomes absent rather than merely renamed.

Evidence: `projects/0_0/project_data.db` director_selections ep2 vs ep5 vs ep6.

### Finding 4: Canary Fixpack EP2-EP3 Show The Richest Cross-Stage Vocabulary

The canary fixpack_r1 production log (25 entries) shows the most complete cross-stage vocabulary in operation:

**New terms visible only in canary pathology logs:**
- `conflict_contract`: `{contract_type: post_select_conflict, mode: rewrite_with_best_manuscript_reuse, conflicts: [...]}`
- `reuse_contract`: `{mode: best_manuscript_baseline, baseline_field: best_manuscript, conflict_field: conflict_contract}`
- `cove_fail_closed`: boolean
- `cove_runtime_failure`: boolean
- `rationale_blanked_by`: `runtime_post_select_conflict_elision`
- `plateau_detected`: boolean

**Canary ep3 shows vocabulary compound encoding in pathology:**
```
pathology_fingerprint: post_select_conflict|contradiction:고유명사|continuity_firewall|fix_pack:missing_fix_pack
```

This fingerprint string is the system's own encoding of the cross-stage vocabulary gap — it concatenates concepts from different stages and different owners into one diagnostic string.

**Key behavioral evidence from canary ep2:**
- `conflict_contract.contract_type: post_select_conflict` (Stage4 runtime term)
- `conflict_contract.conflicts[].conflict_type: continuity` (generic term)
- `reuse_contract.baseline_field: best_manuscript` (Stage4 internal term)
- `scope_origin.fix_scope: runtime_widened` (runtime-originated label)
- `scope_origin.authoritative_fix_scope: director_authoritative` (Director-originated label)

Evidence: `projects/canary_0_0_stage34_arc2_fixpack_r1/logs/episode_production.jsonl`.

### Finding 5: State Truth Triple Split Confirmed Across Both Projects

**0_0 state truth paths:**
- `state_logs.data.actual_truth`: Manager-authored HUD state (capital, total_assets, stocks, reputation, connections, market_insight, status)
- `anchors.world_state`: Python WorldStateManager state (protagonist, alive_npcs, last_updated_ep)
- `stage4_post_processor → final_state_updates`: Director-authored state deltas (30+ code references)

**0_1 state truth paths (identical structure):**
- `state_logs.data.actual_truth`: same HUD schema (capital, total_assets, stocks...)
- `anchors.world_state`: same WorldState schema

The three surfaces describe the same episode reality but persist through different code paths:
- `final_state_updates` → `stage4_post_processor.py` line 591+ → `db.update_martial_tracker()` + `_reconcile_capital()`
- `actual_truth` → `state_logs` table via Manager
- `world_state` → `stage4_post_pass_runtime.py` line 1012+ → `_persist_atomic_world_state()` → anchor

The reconciliation happens in `stage4_post_pass_runtime.py` line 1012:
```python
world_state_changes = dict(final_state_updates or {})
world_state_changes.update(inventory_payload)
world_state_changes.update(relationship_payload)
world_state_changes.update(martial_payload)
world_state_changes.update(pressure_payload)
```

This merge is where Director truth, Manager truth, and Python-extracted truth get combined — but the consumer (next episode's Stage4) sees only the merged `world_state`, not the provenance.

### Finding 6: Inventory Gap Accumulation Across Episodes

Blueprint `_inventory_gaps` grows monotonically:
- ep2: 3 items (이면지, 휴대전화, 잔고 증명서)
- ep3: 5 items (+임대차계약서, 법인 설립 접수증)
- ep4: 7 items (+보안카드, 4대 모니터 데스크톱)
- ep5: 6 items (slightly reduced)
- ep6: 5 items

This is a cross-stage signal: Stage3 produces the inventory gap list, Stage4 should resolve it, but the gap persists across episodes. The vocabulary for this gap exists only in Stage3's `_inventory_gaps` field — Stage4 has no structured counter-field to report resolution.

### Finding 7: 0_1 EP9 Shows Vocabulary Consistency But Retry Pathology

0_1 canary ep9 has 10 director_selections (6 REJECTs) despite high scores (85-98).

Blueprint structure is identical to 0_0 (same keys, no Stage2 fields carried through). The same vocabulary patterns hold:
- `fix_scope: inplace` throughout (no scope widening here, unlike 0_0)
- `gate_semantics` and `fix_pack` populated for all entries
- `actual_truth` in state_logs uses identical schema

The 0_1 ep9 retry pattern differs from 0_0 ep5/ep6: high scores get rejected repeatedly. This suggests the vocabulary gap is not about missing terms but about **strength calibration** — the same term (`REJECT`) gets applied to score-98 manuscripts.

## Non-Issues

1. **Blueprint key ordering**: Stage3 blueprint top-level key set is stable across ep2-6 and across 0_0/0_1 (same 20 keys). No structural drift within Stage3.

2. **Stage2 arc payload structure**: All inspected arc payloads (arc1, arc2 in 0_0; arc1+ in 0_1 canary) share identical field families. No structural drift within Stage2.

3. **Director selection schema**: The `director_selections` table schema is consistent across main and canary projects. When populated, `gate_semantics` and `fix_pack` have stable key sets.

4. **State_logs format**: `actual_truth` top-level key is consistent across all inspected projects and episodes.

## Verdict

`slice-proves-drift`

Justification:

The vertical slices prove three categories of cross-stage vocabulary divergence that change behavior, not just naming:

1. **Rename with strength inversion** (`constraint_summary` → advisory in Stage3, hard prohibition in Stage4): changes what gets blocked.

2. **Owner split with no reconciliation provenance** (`state_changes` → `actual_truth` + `world_state` + `final_state_updates`): obscures truth provenance for next-episode consumers.

3. **Contract degradation under pressure** (ep5/ep6 empty `gate_semantics` and `fix_pack`): removes structured repair guidance exactly when retry cost is highest.

The most compelling single piece of evidence is the canary fixpack_r1 ep2 `scope_origin` field:
```json
{
  "fix_scope": "runtime_widened",
  "authoritative_fix_scope": "director_authoritative",
  "repair_scope": "runtime_lane"
}
```

The system itself is already tracking the vocabulary split. A cross-stage source-of-truth matrix would formalize what `scope_origin` is already encoding ad hoc.

### Slice Ranking For Matrix Justification

1. **Best proof**: canary fixpack_r1 ep2-3 (richest vocabulary, explicit scope_origin tracking, compound pathology fingerprints)
2. **Second proof**: 0_0 main ep2 vs ep5/ep6 (contract degradation under retry pressure)
3. **Supporting proof**: 0_1 canary ep9 (cross-project vocabulary consistency confirmation, strength calibration gap)

## Cross-Stage Vertical Slice Tables

### Table 1: Term-by-Stage Trace for 0_0 EP2

| Concept | Stage2 (arc_payload) | Stage3 (blueprint) | Stage4 (director_selection) | Post-Pass (state_logs + anchors) |
|---|---|---|---|---|
| Mission | `tactical_doc` (4312ch) | `integrated_scenario` (1614ch) | consumed as prose context | N/A |
| Constraints | `constraint_summary` (599ch) | `arc_constraint_summary` (renamed) | Tier-0 hard prohibition | N/A |
| Beat plan | `beat_sequence` (5 items) | DROPPED | N/A | N/A |
| Composition | `hybrid_composition` (3 keys) | DROPPED | N/A | N/A |
| State | `state_changes` (8 keys) | compressed | `final_state_updates` (Director) | `actual_truth` (Manager) + `world_state` (Python) |
| Carryover | `semantic_carryover` (empty) | N/A | N/A | N/A |
| Items | `state_constraints.items_acquired` | `_inventory_gaps` (3 items) | N/A | N/A |
| Scene design | N/A | `scene_breakdown` (5 scenes) | consumed as blueprint | N/A |
| Repair contract | N/A | N/A | `fix_pack` (6 keys) + `gate_semantics` (7 keys) | N/A |
| Scope truth | N/A | N/A | `fix_scope` vs `authoritative_fix_scope` vs `repair_scope` | N/A |
| Episode truth | `episode_details` (list 5) | N/A | N/A | `episode_bibles.state_changes` |

### Table 2: Vocabulary Presence/Absence Across 0_0 Main Episodes

| Field | ep2 | ep3 | ep4 | ep5 | ep6 |
|---|---|---|---|---|---|
| Blueprint scenes | 5 | 5 | 5 | 5 | 5 |
| integrated_scenario | 1614ch | 1652ch | 1107ch | 1362ch | 1446ch |
| _inventory_gaps | 3 items | 5 items | 7 items | 6 items | 5 items |
| gate_semantics (populated) | YES | N/A (Stage3 only) | N/A | **EMPTY** | **EMPTY** |
| fix_pack (populated) | YES | N/A | N/A | **EMPTY** | **EMPTY** |
| authoritative_fix_scope | inplace | N/A | N/A | **absent** | **absent** |
| Director score | 96 | 95 | 93 | 91 | 90 |
| Retry rounds | 0 | 4 | 1 | 6 | 9 |

### Table 3: Cross-Project Term Consistency (0_0 vs 0_1)

| Term | 0_0 main | 0_0 canary fixpack | 0_1 canary |
|---|---|---|---|
| Blueprint key set | 20 keys | (same) | 20 keys (identical) |
| `integrated_scenario` | 1100-1650ch | (same) | 1437-1472ch |
| `actual_truth` in state_logs | present | present | present |
| `gate_semantics` schema | 7 keys | 7 keys | 7 keys |
| `fix_pack` schema | 6 keys | 6 keys | 6 keys |
| `scope_origin` | present in pathology | present in pathology | (not in inspected entries) |
| `_inventory_gaps` | present | present | present (ep9), absent (ep13) |

## Stop

read-only lane complete; no files mutated
