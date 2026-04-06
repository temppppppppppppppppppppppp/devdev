# Terminal 2 — Stage2 Pipeline P0-P1 Severity Survey

Date: 2026-04-06
Mode: read-only global severity sweep
Lane: Stage2 generation, normalization, validation, finalization
Baseline Commit: `6189dc92`

## Verdict: P1 (two live seams)

No live P0 found in this lane.
Two live P1 seams confirmed with static evidence.

---

## P1-001: `joint_docs.world_joint` silently overwritten at persistence time

### Entry → Owner → Sink → Consequence

- **Entry**: LLM generates `joint_docs.world_joint` as a required schema field (`modules/core/response_schemas.py:399-401`)
- **Owner**: `modules/core/stage2_finalizer.py:1208-1209` — `refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})`
- **Sink**: Canonical arc persisted to DB via `save_v20_anchor("arcs", all_refined_arcs)` at `stage2_finalizer.py:1464`
- **Consequence**: Stage3/4 consumers receive wrong or stale `world_joint`:
  - `modules/domain/agents/four_phase_arc_generator.py:1288-1302` — next arc's carryover_world_joint prompt
  - `modules/domain/agents/continuity_arc.py:1020` — Stage3 continuity context
  - `modules/core/prompt_builder.py:688` — prompt world-state injection
  - `modules/domain/agents/constraint_compiler.py:238` — constraint "world_state" field

### Evidence

The overwrite pattern is confirmed in three separate locations:

1. `stage2_validation_pipeline.py:919` — before ContinuityInspector (pre-Director)
2. `stage2_preflight_runtime.py:81` — in preflight runtime
3. `stage2_finalizer.py:1209` — after Director PASS (pre-persistence)

The subsequent repair steps (`_sync_stage2_end_state_inventory_contract`, `_sync_stage2_end_location_contract`) re-derive `physical_inventory` and `final_location` from `state_constraints` (LLM output). But `world_joint` has **no equivalent sync step** — it stays as whatever the enriched_block provided, which is either:

- An empty string (enriched_block has no `joint_docs`)
- A default "변화 없음" (from default injection at `stage2_finalizer.py:1277`)
- A stale block-level value (from the treatment design, not reflecting this arc's events)

The LLM's arc-specific `world_joint` (describing world-state changes produced during this arc) is silently discarded.

### Severity Justification

P1 because:

- The persisted `world_joint` is read by Stage3 consumers as authoritative world context
- The field is required in the response schema, so the LLM always generates it
- The overwrite causes a reproducible world-state truth gap at every arc persistence
- No recovery mechanism exists in the current pipeline
- Not P0 because no existing canonical artifact is destructively damaged — the loss occurs at first-write time

### Owner Files

1. `modules/core/stage2_finalizer.py` (primary — line 1209, persistence-time overwrite)
2. `modules/core/stage2_validation_pipeline.py` (secondary — line 919, pre-Director overwrite)

---

## P1-002: `status_shadow` silently overwritten at persistence time

### Entry → Owner → Sink → Consequence

- **Entry**: LLM generates `status_shadow` with `item_consumption`, `expected_injuries`, `key_stat_change` as schema fields (`modules/core/response_schemas.py:403-410`)
- **Owner**: `modules/core/stage2_finalizer.py:1210` — `refined_arc["status_shadow"] = enriched_block.get("status_shadow", {})`
- **Sink**: `_compute_inventory_carryover()` at `stage2_finalizer.py:1287-1290` uses `status_shadow.item_consumption` to determine which items to subtract from the previous arc's inventory
- **Consequence**: Inventory carryover uses wrong `item_consumption` (empty or stale), causing:
  - Items the LLM declared consumed to remain in the canonical inventory
  - `expected_injuries` and `key_stat_change` data lost for downstream context

### Evidence

The overwrite follows the same triple-location pattern as P1-001:

1. `stage2_validation_pipeline.py:920`
2. `stage2_preflight_runtime.py:82`
3. `stage2_finalizer.py:1210`

After the overwrite, `_repair_stage2_pass_arc_structure` at line 1283-1297 computes inventory carryover:

```python
curr_status = refined_arc.get("status_shadow", {}) or {}
inherited = _compute_inventory_carryover(
    prev_joint.get("physical_inventory", []),
    curr_status.get("item_consumption", []),  # ← enriched_block's version, not LLM's
    state_constraints.get("protagonist_items") or state_constraints.get("items_acquired", []),
)
```

The enriched_block's `status_shadow.item_consumption` is typically empty (it's a pre-generation block), so nothing gets subtracted from the previous inventory.

### Mitigation (partial)

`_sync_stage2_end_state_inventory_contract` at line 1301 can override the wrong carryover if `arc_end_state.equipment` (from LLM output) is non-empty:

```python
canonical_inventory = end_inventory  # ← from arc_end_state.equipment (LLM)
if not canonical_inventory and prev_arc:
    # fallback to carryover (uses wrong item_consumption)
```

When the LLM populates `arc_end_state.equipment`, the sync step recovers. When it doesn't (e.g., the LLM leaves it empty and relies on joint_docs), the wrong carryover persists.

### Severity Justification

P1 because:

- `item_consumption` data loss causes deterministic inventory truth drift
- The mitigation (`arc_end_state.equipment`) is conditional, not guaranteed
- `expected_injuries` and `key_stat_change` loss affects operator context but doesn't directly corrupt canonical artifacts
- Not P0 because the inventory sync step provides a partial recovery path

### Owner Files

1. `modules/core/stage2_finalizer.py` (primary — lines 1210, 1287-1290)

---

## Watchlist Only

### W-001: Carryover authority packet text parsing fragility

- `modules/domain/agents/arc_ensemble.py:52-77` — `_extract_carryover_authority_packet` parses prev-arc context text for numeric carryover values
- Fragile text parsing could cause wrong capital/portfolio numbers in the next arc's generation prompt
- Bounded by Director validation — the Director can catch arithmetic inconsistencies via `NumericConsistencyChecker` and `_check_cross_arc_asset_continuity`
- Not P1 because it's a generation-time input issue, not a persistence-time truth corruption

### W-002: Entity alias map coverage gaps

- `modules/core/stage2_entity_contract.py` — alias map covers specific patterns (locations, financial objects) but not all entity variations
- Non-canonical entity names can persist if the alias map doesn't cover them
- Bounded — doesn't cause false PASS, and the normalization is best-effort by design
- Not P1 because it's an incompleteness issue, not a wrong-canonicalization path

### W-003: Legacy persistence path

- `modules/core/stage2_finalizer.py:1730` — `_legacy_stage2_pass_persistence_and_tail_body` exists as a defined method
- Only called from tests (`tests/test_stage2_finalizer_lane_d.py:282`), not from production code
- Skips the commit step (`_persist_stage2_pass_arc_commit`) compared to the active path
- Not a live risk because it's not on the production code path

---

## Required Questions

### 1. Stage2에서 false PASS, wrong canonicalization, entity/numeric drift persistence가 P0-P1로 열려 있나

- **false PASS**: no live P0-P1. Director sovereignty is intact — all pre-Director checks (DraftValidator, Consensus, SelfReflector) feed advisories to the Director, not bypass it. PASS_WITH_FIX handling and QualityGate score check are both live and functioning.
- **wrong canonicalization**: **P1 confirmed**. Two persistence-time overwrite seams silently replace LLM-generated `joint_docs.world_joint` and `status_shadow` with enriched_block values.
- **entity/numeric drift persistence**: watchlist only. Entity alias coverage gaps and carryover text parsing fragility exist but are bounded by Director validation and downstream sync steps.

### 2. Stage2 validation과 finalizer 사이에 authoritative truth가 바뀌거나 빠지는 seam이 있나

**Yes** — two confirmed seams:

- The validation pipeline (`stage2_validation_pipeline.py:919-920`) overwrites `joint_docs` and `status_shadow` BEFORE the Director sees the arc. The Director audits the arc with stale block-level `world_joint` and empty `status_shadow`.
- The finalizer (`stage2_finalizer.py:1209-1210`) overwrites them AGAIN after Director PASS, before persistence. Even if the Director somehow referenced the LLM's original values, they're discarded at this point.
- The repair steps between validation and persistence recover `final_location` and `physical_inventory` via `state_constraints`, but do NOT recover `world_joint`, `item_consumption`, `expected_injuries`, or `key_stat_change`.

### 3. 이 lane에서 지금 가장 위험한 owner file 1~3개는 무엇인가

1. **`modules/core/stage2_finalizer.py`** — primary owner of both P1 seams (lines 1208-1210, 1287-1290) and the canonical persistence sink
2. **`modules/core/stage2_validation_pipeline.py`** — secondary owner of the pre-Director overwrite (lines 919-920) that causes the Director to audit with wrong `world_joint`/`status_shadow`

### 4. 지금 보이는 위험이 front blocker인가, 아니면 fresh run 전 watchlist인가

**Fresh run 전 bounded fix를 진지하게 검토해야 하는 P1 수준.**

- The `world_joint` loss is deterministic and reproducible on every arc persistence
- The `item_consumption` loss affects inventory truth on every carryover computation where `arc_end_state.equipment` is empty
- However, the system has been operating with this pattern (the overwrite pattern exists in three locations, suggesting it was intentional or at least long-standing)
- Runtime evidence from existing fresh runs (e.g., `__000403`) shows arcs passing through the pipeline, which means the downstream impact may be tolerable in practice even if technically incorrect
- Recommended approach: bounded fix before fresh run to preserve `world_joint` through the overwrite, or at minimum add a `world_joint` re-sync step parallel to the existing `final_location` and `physical_inventory` sync steps

**Static evidence is sufficient** to confirm both P1 seams. The overwrite code paths are clear and unconditional. Fresh run would confirm the runtime impact magnitude but is not required to establish the seams exist.

---

## 3-Pass Audit Record

### Pass 1. Structure and Scope

- Document type: terminal survey output for read-only P0-P1 sweep
- Scope: Stage2 generation, normalization, validation, finalization pipeline
- Focus files: all six assigned files inspected
- Findings-first structure with P0/P1 verdict in first section

### Pass 2. Evidence and Consistency

- All file paths verified against live codebase
- Line numbers cross-checked against current code
- The triple-location overwrite pattern (`finalizer:1209-1210`, `validation_pipeline:919-920`, `preflight_runtime:81-82`) confirmed via grep
- Response schema confirmation (`response_schemas.py:399-410`) that both fields are LLM-generated
- Downstream consumer list verified via grep for `world_joint` across modules

### Pass 3. Execution and Readability

- Two P1 findings with clear entry→owner→sink→consequence chains
- Watchlist items separated from live P1 findings
- Required questions answered with specific evidence references
- No queue changes proposed, no code patches applied
- Owner file set is narrow: 2 files for 2 P1 seams

Confidence: 96%

---

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
