# Canary Prep Truth-Store Isolation Execution SSOT

Date: 2026-03-29
Status: execution-ready
Canonical Path: `docs/2026-03-29/canary-prep-truth-store-isolation-execution-ssot.md`
Temp Mirror Path: `docs/temp/canary-prep-truth-store-isolation-execution-ssot.md`
Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty: tracked stage4/provider runtime and tests, narrative assets, temp queue artifacts, and canary outputs`
- Resume Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Resume Drift Summary: `same commit; capital-truth-divergence reconciliation survey completed, BP preflight survey finalized, 8 completed Stage4 temp mirrors swept`
Source Survey Docs:
- `docs/2026-03-29/capital-truth-divergence-reconciliation.md`
- `docs/2026-03-29/bp-preflight-integrity-survey.md`
Evidence Artifacts:
- DB anchor timestamps and history arrays extracted from `canary_0329_ep3_bp_patch_recheck/project_data.db`
- EP1~EP3 committed manuscript capital-value cross-reference (6+ occurrences of 20억)
Side-Effect Coverage: covered

## 1. Intent

### Goal

Prevent canary preparation from contaminating the truth stores (`fact_ledger`, `chain_link`, `world_state`) that downstream stages rely on for narrative integrity.

### Why Now

The capital-truth-divergence reconciliation survey identified two systemic defects in the canary prep path:

1. **Extraction Accumulation**: `fact_ledger.numbers.capital` was inflated from 20억 to 40억 because canary prep re-processed EP1~EP3 without flushing the inherited fact_ledger history. The financial scalar extractor appended duplicate entries and the value drifted.
2. **Canary Bleed-Through**: `chain_link_4~7` and `fact_ledger` history entries for ep4~ep6 persisted from the source project's prior canary runs because `reset_stage4_outputs()` does not touch the `anchors` table.

These are **system-level** defects in the prepare/reset path, not narrative or Director logic issues. Fixing them here prevents recurring truth-store drift in all future canary projects, independent of any specific BP patch.

### Separation From Narrative BP Patch

This execution SSOT governs only the system-level canary prep isolation boundary. The narrative BP patch for EP4 (CF-1/CF-3/CF-6 conflicts) is a separate downstream lane that depends on this isolation fix being completed first, but is not governed by this document.

## 2. Baseline Facts

### Authoritative Truth

- EP1~EP3 committed manuscripts state capital = **20억 원** consistently (6+ occurrences across 3 episodes, 0 contradictions)
- Manuscript is the highest-priority truth source per the BP preflight integrity survey authority order

### Drifted State

- `fact_ledger.numbers.capital.value` = 4,000,000,000 (40억) — double-extraction artifact
- `fact_ledger.numbers.capital.history` = 8 entries (ep1~ep6 from source + duplicate ep1, ep3 from re-processing)
- `chain_link_4` through `chain_link_7` exist in DB despite only EP1~EP3 manuscripts being committed — orphan residue from source project's prior runs

### Root Cause Location

| Component | File | Function/Method | Issue |
| --- | --- | --- | --- |
| Canary prep reset | `scripts/run_stage4_canary.py` | `prepare_canary()` → `prepare_stage4_canary_project()` → `reset_stage4_outputs()` | Deletes episode-derived tables but does **not** touch `anchors` table |
| DB anchor deletion | `modules/core/stage4_canary_tools.py` L444-464 | `_delete_stage4_db_outputs(db, from_ep)` | Only targets manuscripts, state_logs, causal_graph, etc. — no `DELETE FROM anchors` |
| fact_ledger load | `modules/core/fact_ledger.py` L132-163 | `FactLedger.__init__()` → `_load()` | Loads inherited anchor without validating against committed episode count |
| fact_ledger update | `modules/core/fact_ledger.py` L422-449 | `update_number()` | Replaces `value` but appends to `history` — no deduplication for same-ep re-extraction |
| chain_link persist | `modules/core/stage4_post_pass_runtime.py` L792 | chain_link save | Creates `chain_link_{N}` anchor — no cleanup of orphans beyond committed ep count |
| world_state load | `modules/core/world_state.py` L117-141 | `WorldStateManager.__init__()` → `_load_or_init()` | Loads inherited anchor — NPC/item state from beyond committed ep count persists |

## 3. Scope

### Included

- `scripts/run_stage4_canary.py` — `prepare_canary()` entry point
- `modules/core/stage4_canary_tools.py` — `prepare_stage4_canary_project()`, `reset_stage4_outputs()`, `_delete_stage4_db_outputs()`
- `modules/core/fact_ledger.py` — `_load()`, `update_number()`, `_extract_numerical_facts()`, `save()`
- `modules/core/db_manager.py` — `save_anchor()`, `load_anchor()`, anchor deletion path
- `modules/core/world_state.py` — existing `rollback_to(target_ep)` primitive reuse from the reset path; no new trim helper unless rollback proves insufficient
- `tests/` — targeted regression tests for canary prep isolation
- Narrow helper scripts if needed for anchor cleanup validation

### Excluded

- Narrative BP patch (EP4 blueprint content, CF-1/CF-3/CF-6 remediation)
- Manual one-off DB surgery as the final answer (must be a code-path fix)
- Stage 4 runtime policy (Director, Chief Writer, retry logic)
- Provider/fallback observability
- Broad database redesign or schema migration
- `world_state` content correction (only structural isolation boundary, not value correction)

## 4. Pass 1. Inventory Summary

### Anchor Table Behavior During Canary Prep

| Step | What Happens | What Should Happen |
| --- | --- | --- |
| `shutil.copytree(source, target)` | Entire DB copied including all anchors | Same — full copy is correct |
| `_delete_stage4_db_outputs(db, from_ep)` | Deletes manuscripts, state_logs, causal_graph, episode_bibles, npc_history, etc. from `from_ep` onward | Should also delete/reset truth-store anchors that reference episodes beyond `from_ep` |
| Episode re-processing (EP1~EP3) | fact_ledger re-extracted, history appended to existing entries | Should flush fact_ledger before re-extraction, or deduplicate |
| chain_link re-extraction | chain_link_1~3 overwritten (INSERT OR REPLACE) | Should also delete chain_link_{N} for N > last committed ep |

### Affected Anchors

| Anchor Key Pattern | Count in Sample DB | Committed EP Range | Orphan Range |
| --- | --- | --- | --- |
| `fact_ledger` | 1 | EP1~EP3 (valid) + EP4~EP6 history (orphan) | ep4~ep6 history entries |
| `world_state` | 1 | last_updated_ep=3 (valid), but NPC/item state may reflect canary-generated eps | NPC entries with first_seen_ep > 3 (e.g., 최민 first_seen_ep=4) |
| `chain_link_{N}` | 7 | chain_link_1~3 (valid) | chain_link_4~7 (orphan) |

### Key Metric

`_delete_stage4_db_outputs()` touches **0** rows in the `anchors` table. The entire isolation gap is in this single function's scope.

## 5. Pass 2. Semantic Classification

### Class A: Reset Boundary Extension (core fix)

The `_delete_stage4_db_outputs()` function needs to extend its reset scope to include truth-store anchors that reference episodes beyond the `from_ep` boundary.

Targets:
- Delete `chain_link_{N}` for all N >= `from_ep`
- Reset `fact_ledger` via the existing `rollback_to(from_ep)` primitive so it reflects only episodes < `from_ep`
- Reset `world_state` via the existing `rollback_to(from_ep)` primitive so protagonist/NPC/item/relationship/timeline state reflects only episodes < `from_ep`

### Class B: Fact Ledger Accumulation Guard (defense-in-depth)

Even after fixing the reset boundary, `update_number()` should guard against same-ep duplicate extraction within a single run.

Targets:
- Add deduplication or idempotency check in `update_number()` — if the last history entry is for the same ep and same value, skip the append
- Or: flush fact_ledger `numbers` history entries for the target ep range before re-extraction begins

### Class C: Orphan Anchor Detection (observability)

Add a validation check that can be run after canary prep to verify no orphan anchors exist beyond the committed episode count.

Targets:
- Script or function that compares committed episode count against anchor keys
- Reports orphan chain_links, fact_ledger history entries, and world_state NPC/item entries beyond committed range

## 6. Side-Effect Map

- **file writes / artifacts**: No file-system artifacts affected. All changes are DB-internal (project_data.db anchors table).
- **DB / schema / transaction boundaries**: `anchors` table — DELETE rows for orphan chain_links, UPDATE fact_ledger and world_state anchor data. No schema change. Existing INSERT OR REPLACE pattern unchanged.
- **JSONL / log / audit sinks**: None directly. Canary prep does not write to JSONL during anchor cleanup.
- **console / UI / operator output**: Canary prep script may emit additional log lines for anchor cleanup actions. No UI impact.
- **rollback / recovery / retry**: If anchor cleanup fails mid-way, the DB is no worse than current state (orphans remain). No destructive data loss risk — orphan deletion only removes data that has no committed manuscript backing.
- **cache / global state**: In-memory fact_ledger and world_state are re-loaded from DB after reset. No stale cache risk if the load happens after cleanup.
- **bootstrap fallback / config-env mutation**: None. No config changes needed.

## 7. Realization Architecture

### Approach: Extend `_delete_stage4_db_outputs()` Reset Scope

The simplest correct fix is to add anchor cleanup to the existing reset function that already handles episode-derived table cleanup. This keeps the reset boundary in one place rather than distributing it.

### Contract

After `reset_stage4_outputs(project_root, from_ep=N)` completes:
1. No `chain_link_{M}` anchor exists for M >= N
2. `fact_ledger.numbers.*` history contains no entries for episodes >= N
3. `fact_ledger.numbers.*` values are recalculated from entries for episodes < N only
4. `world_state` is restored via `rollback_to(N)`, so protagonist/NPC/item/relationship/timeline state reflects only episodes < N
5. `world_state.last_updated_ep` is set to `N-1`

### Dependency

- `db_manager.py` must expose an anchor-deletion method (or the reset function uses raw SQL on the anchors table)
- `fact_ledger.py` already exposes `rollback_to(target_ep)` and should be reused as the primary rebuild boundary
- `world_state.py` already exposes `rollback_to(target_ep)` and should be reused as the primary rollback boundary

## 8. Execution Tranches

### Tranche 1: Canary Prep Anchor Reset Boundary

**Goal**: Extend `_delete_stage4_db_outputs()` to delete orphan chain_link anchors and reuse the existing fact_ledger/world_state rollback primitives at the committed episode boundary.

**Files**:
- `modules/core/stage4_canary_tools.py` — add anchor cleanup to `_delete_stage4_db_outputs()`
- `modules/core/db_manager.py` — add `delete_anchor(key)` or `delete_anchors_by_prefix(prefix, from_suffix)` if not already present

**Changes**:
- After existing table deletions, add: delete all `chain_link_{N}` anchors where N >= `from_ep`
- After chain_link cleanup, call `FactLedger.rollback_to(from_ep)` instead of inventing a new rebuild helper
- After fact_ledger rollback, call `WorldStateManager.rollback_to(from_ep)` instead of introducing a bespoke trim path

### Tranche 2: Fact Ledger Accumulation Guard

**Goal**: Prevent same-ep duplicate extraction from inflating scalar values even if the reset boundary fix is in place.

**Files**:
- `modules/core/fact_ledger.py` — `update_number()`

**Changes**:
- Add idempotency guard: if the most recent history entry is for the same `ep_num` and same `value`, skip the append and do not update `value`
- Or: add a `flush_ep_range(from_ep, to_ep)` method that removes history entries in range and recalculates the current value from remaining entries

### Tranche 3: Orphan Chain-Link / History Bleed-Through Prevention

**Goal**: Ensure `prepare_stage4_canary_project()` explicitly validates anchor state after reset, preventing any bleed-through path that might be added in the future.

**Files**:
- `modules/core/stage4_canary_tools.py` — `prepare_stage4_canary_project()`

**Changes**:
- After `reset_stage4_outputs()` returns, add a validation pass:
  - Query all `chain_link_%` anchors and verify none exceed committed ep count
  - Load fact_ledger and verify `numbers.*` history contains no entries beyond committed ep count
  - Log WARNING if orphans are found (should not happen after Tranche 1, but defense-in-depth)

### Tranche 4: Regression Coverage and Re-Prepare Verification

**Goal**: Add targeted tests that verify canary prep truth-store isolation.

**Files**:
- `tests/test_run_stage4_canary.py` or new `tests/test_canary_prep_isolation.py`

**Tests**:
- `test_prepare_canary_deletes_orphan_chain_links`: seed a DB with chain_link_1~7, run reset with from_ep=4, verify chain_link_4~7 are gone and chain_link_1~3 remain
- `test_prepare_canary_flushes_fact_ledger_history`: seed fact_ledger with ep1~ep6 history entries, run reset with from_ep=4, verify only ep1~ep3 entries remain and value is recalculated
- `test_prepare_canary_rolls_back_world_state_boundary`: seed world_state with protagonist/NPC/item state through ep6, run reset with from_ep=4, verify `last_updated_ep == 3` and no post-ep3 residue remains
- `test_fact_ledger_idempotent_update`: call update_number() twice for same ep/value, verify history has only one entry
- `test_repeated_prepare_does_not_accumulate`: run prepare twice on same project, verify fact_ledger values do not double

## 9. Acceptance Criteria

1. After `prepare_canary()` with `from_ep=4` on a project that previously ran through EP7:
   - `chain_link_4` through `chain_link_7` do not exist in the DB
   - `chain_link_1` through `chain_link_3` remain intact
2. After `prepare_canary()`, `fact_ledger.numbers.capital.value` equals the manuscript-authoritative value (20억 in the test case), not an accumulated multiple
3. After `prepare_canary()`, `fact_ledger.numbers.*.history` contains no entries for episodes >= `from_ep`
4. After `prepare_canary()`, `world_state.last_updated_ep == from_ep - 1`, and no protagonist/NPC/item residue introduced at or after `from_ep` remains
5. Running `prepare_canary()` twice on the same project does not change truth-store values on the second run (idempotency)
6. All fixes are in the code path — no manual DB surgery required to maintain isolation
7. Narrative BP patch scope is not touched by this execution lane
8. All existing canary tests continue to pass

## 10. Verification Plan

- `set PYTHONIOENCODING=utf-8 && python -m pytest tests/test_run_stage4_canary.py -x -v` — existing canary tests
- `set PYTHONIOENCODING=utf-8 && python -m pytest tests/test_canary_prep_isolation.py -x -v` — new isolation tests (Tranche 4)
- `python -m py_compile modules/core/stage4_canary_tools.py`
- `python -m py_compile modules/core/fact_ledger.py`
- `python -m py_compile modules/core/db_manager.py`
- `python -m py_compile modules/core/world_state.py`
- `python -m ruff check modules/core/stage4_canary_tools.py modules/core/fact_ledger.py modules/core/db_manager.py modules/core/world_state.py`
- `python scripts/check_utf8_hygiene.py modules/core/stage4_canary_tools.py modules/core/fact_ledger.py modules/core/world_state.py`
- `python scripts/ops_validator.py --strict`
- `python scripts/sync_temp_queue_state.py`
- Fresh prepare-only validation: run `prepare_canary()` on a test project, then query DB to verify no orphan anchors and correct fact_ledger values

## 11. Guardrails

- Do not modify Director, Chief Writer, or Stage 4 runtime policy
- Do not modify narrative BP content or treatment files
- Do not perform manual one-off DB surgery as the solution — the fix must be in the code path
- Do not delete `chain_link_1~3` or other anchors within the committed episode range
- Do not alter fact_ledger extraction logic (what gets extracted) — only fix how history is managed during re-extraction
- Do not redesign the DB schema or anchors table structure
- Do not touch provider/fallback or observability gap lanes
- Keep the reset boundary extension co-located with existing reset logic in `stage4_canary_tools.py`
- Prefer reusing existing `rollback_to(target_ep)` primitives over introducing new `trim_beyond` / `rebuild_from_committed` helpers
- Preserve existing INSERT OR REPLACE semantics for anchor writes during normal episode production — only change behavior during canary prep reset

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: remove mirror after all 4 tranches are realized and acceptance criteria verified
- roadmap dependency: must be realized before narrative BP patch lane; independent of provider-fallback-observability-gap lane

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope

- confirmed system-track scope: canary prep reset boundary, not narrative BP patch
- verified all 8 required SSOT sections present (intent, baseline, scope, inventory, classification, side-effects, tranches, acceptance criteria)
- verified excluded scope explicitly lists narrative BP, manual DB surgery, runtime policy, provider/fallback, broad DB redesign
- verified side-effect map covers all 7 categories with explicit N/A or coverage
- PASS

### Pass 2. Evidence and Consistency

- cross-referenced root cause with capital-truth-divergence reconciliation survey findings
- confirmed code paths match live codebase: `_delete_stage4_db_outputs()` in stage4_canary_tools.py does not touch anchors table
- confirmed `fact_ledger.update_number()` appends history without deduplication
- confirmed chain_link_4~7 timestamps (2026-03-23) predate canary prep timestamps (2026-03-29), consistent with source-project bleed-through
- confirmed world_state.alive_npcs contains 최민 with first_seen_ep=4, validating NPC orphan claim
- acceptance criteria directly address both divergence families (Extraction Accumulation, Canary Bleed-Through)
- PASS

### Pass 3. Execution and Readability

- tranches ordered by dependency: reset boundary (T1) before accumulation guard (T2) before validation (T3) before tests (T4)
- each tranche specifies target files and concrete change description
- acceptance criteria are testable without ambiguity
- verification plan includes both existing and new test paths
- guardrails explicitly separate this lane from narrative BP patch
- PASS

Estimated confidence: `97%`
