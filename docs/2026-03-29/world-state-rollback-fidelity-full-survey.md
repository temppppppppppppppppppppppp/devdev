# World-State Rollback Fidelity Full Survey

Date: 2026-03-29
Status: draft-for-audit
Canonical Path: `docs/2026-03-29/world-state-rollback-fidelity-full-survey.md`
Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
Baseline Dirty Summary: `dirty workspace with active stage4/provider/runtime edits, narrative assets, temp queue artifacts, and canary outputs`
Source Docs:
- `docs/2026-03-29/canary-prep-truth-store-isolation-execution-ssot.md`
- `docs/2026-03-29/bp-preflight-integrity-survey.md`
- `docs/2026-03-29/capital-truth-divergence-reconciliation.md`
Evidence Scope:
- `modules/core/world_state.py`
- `modules/core/stage4_canary_tools.py`
- `modules/core/db_manager.py`
- source project `projects/canary_0329_ep3_bp_patch_recheck`
- prepared target `projects/canary_0329_truth_store_isolation_prepare_check`

## 1. WorldState Rollback Reconstruction Contract

### Observed Contract

`WorldStateManager.rollback_to(target_ep)` at [world_state.py](C:/Users/User/Desktop/글도비/modules/core/world_state.py#L1324) does exactly this:

1. Reinitialize `world_state` to `_INIT_STATE`
2. Load all `episode_bibles`
3. Replay only `episode_bibles.state_changes` for episodes `< target_ep`
4. Save the rebuilt anchor

### What It Does Not Read

The rollback path does **not** consume:

- top-level `episode_bibles.new_npcs`
- top-level `episode_bibles.new_items`
- top-level `episode_bibles.lost_items`
- top-level `episode_bibles.relationship_changes`
- top-level `episode_bibles.time_passed`
- top-level `episode_bibles.reveals`
- committed manuscript body text
- `chain_link_{ep}` anchors

### Effective Reconstruction Surface

The rebuilt `world_state` therefore depends only on whatever is serialized inside `state_changes` and recognized by `update_from_state_changes()` at [world_state.py](C:/Users/User/Desktop/글도비/modules/core/world_state.py#L768).

That function can rebuild:

- `active_pressure_vectors`
- `inventory_counts` / `inventory_count_deltas`
- `major_items` if present inside `state_changes`
- `relationship_changes` if present inside `state_changes`
- `npc_introductions` if present inside `state_changes`
- timeline markers, motivations, promises, world laws, some NPC-known-attr fields

It cannot rebuild facts that exist only in:

- top-level bible delta fields
- manuscript prose
- chain_link continuity anchors

### Immediate Implication

`rollback_to()` is not a general "restore committed pre-EP truth" routine.
It is a narrower "replay structured `state_changes` only" routine.

That is sufficient for contamination cleanup.
It is not sufficient for high-fidelity reconstruction of all preflight-relevant world truth.

## 2. Before/After Fidelity Table

Comparison basis:

- `Authority`: EP1~EP3 committed manuscript + EP1~EP3 episode_bibles + `chain_link_3`
- `Source world_state`: `canary_0329_ep3_bp_patch_recheck`
- `Prepared target`: `canary_0329_truth_store_isolation_prepare_check`

| Field | Authority Expectation | Source world_state | Prepared target | Fidelity Verdict |
| --- | --- | --- | --- | --- |
| `protagonist.location` | EP3 committed truth + `chain_link_3` say protagonist is in the SW인베스트먼트 / 여의도 오피스텔 사무실 at the cliffhanger | empty string | empty string | under-restored, but this gap already exists before rollback; current structured stores never held it |
| `alive_npcs` | At minimum EP1~EP3 introduced cast should survive: 박성호, 한정호, 한태준, 한태민, 비서실장, 집사, 미상 발신자 family | 17 entries, but includes obvious EP4~EP6 bleed-through such as `최민`, `박성호 PB`, `한미증권 VIP 센터장` | 0 entries | blocking under-restoration |
| `relationships` | EP1~EP3 top-level `relationship_changes` record multiple active relations (`목격자`, `오해 대상`) | 17 entries, again contaminated by post-EP3 residue | 0 entries | blocking under-restoration |
| `active_items` | EP1~EP3 truth supports at least `OTP 카드`; top-level bible delta also carries legal/financial setup items. EP3 manuscript further implies office computer / monitors are in use | 10 items, but includes likely overgrown later-state residue and stale loss statuses | `OTP 카드` only | partial restoration only; nontrivial setup truth lost |
| `active_pressure_vectors` | EP3 `state_changes.active_pressure_vectors` should survive | 2 | 2 | restored correctly |
| `active_plots` | no authoritative committed active plot rows visible in sampled EP1~EP3 structured data | 0 | 0 | no issue found |
| `timeline` | `chain_link_3` carries time/location continuity, but `state_changes.time_markers` is absent | 0 | 0 | structurally sparse; not evidence of rollback regression alone |
| `cumulative_elapsed` | no structured elapsed markers in sampled EP1~EP3 `state_changes` | `{total_days: 0}` | `{total_days: 0}` | no issue found |

### Raw Before/After Snapshot

- source `world_state`
  - `last_updated_ep = 3`
  - `alive_npcs = 17`
  - `relationships = 17`
  - `active_items = 10`
  - `active_pressure_vectors = 2`
- prepared target `world_state`
  - `last_updated_ep = 3`
  - `alive_npcs = 0`
  - `relationships = 0`
  - `active_items = 1` (`OTP 카드`)
  - `active_pressure_vectors = 2`

### Key Contrast

The prepared target preserves only the fields that were actually encoded inside replayable `state_changes`:

- `inventory_counts` -> `OTP 카드`
- `active_pressure_vectors` -> retained

It drops fields that were present only in top-level bible delta:

- `new_npcs`
- `relationship_changes`
- most setup items

## 3. Under-Restoration Findings

### UF-1. Replay Ignores Top-Level Bible Delta

The most important loss is not manuscript-only nuance.
It is the loss of truth that already exists in structured episode_bible fields but sits **outside** `state_changes`.

Examples from EP1~EP3 episode_bibles:

- `new_npcs`
- `relationship_changes`
- `new_items`

These are sufficient to preserve a minimal cast/inventory/relationship world snapshot.
`rollback_to()` currently ignores them, so reconstructible truth is discarded.

### UF-2. Source WorldState Is Not a Gold Baseline

The source project `world_state` is visibly contaminated:

- `최민` with `first_seen_ep = 4`
- `박성호 (한미증권 PB)` with `first_seen_ep = 5`
- `한미증권 VIP 센터장` with `first_seen_ep = 6`

So the source anchor cannot be used as "correct pre-EP4 world state".
The prepared target is right to remove those.

### UF-3. Some Preflight-Relevant Truth Never Entered Replayable Structured Stores

Even if rollback consumed top-level bible delta, some facts still would not come back:

- protagonist exact location at EP3 ending
- `chain_link_3` pending actions
- explicit opening/ending continuity bridge
- some manuscript-established office usage context

Those currently live in:

- committed manuscript prose
- `chain_link_3`

not in replayable `world_state` inputs.

### UF-4. Current Validation Is Too Weak for Fidelity

The prepare-only validation in [stage4_canary_tools.py](C:/Users/User/Desktop/글도비/modules/core/stage4_canary_tools.py#L990) only proves:

- no orphan `chain_link_*`
- no post-boundary fact history
- no post-boundary `alive_npcs`
- no post-boundary `active_items`
- `last_updated_ep` boundary

It does **not** prove:

- pre-boundary cast is preserved
- pre-boundary relationships are preserved
- pre-boundary operator-useful world truth remains available

So `anchor_validation = ok` currently means contamination cleanup passed, not fidelity passed.

## 4. Root Cause Assessment

## Verdict

`MIXED: rollback contract + sparse source data`

### Root Cause A. Bug In Rollback Reconstruction Contract

This is a real contract bug.

Reason:

- EP1~EP3 episode_bibles already contain structured cast/inventory/relationship data outside `state_changes`
- `WorldStateManager.rollback_to()` chooses not to read that data
- therefore reconstructible truth is dropped during rollback

This is not merely an authority-order issue.
The rollback routine claims to restore prior state, but currently restores only the `state_changes` subset.

### Root Cause B. Episode-Bible / Store Sparsity

This is also real.

Some truths needed by preflight are not serialized into replayable structured stores at all:

- ending location
- time marker continuity
- pending actions / cliffhanger carryover
- certain office-usage / setup truths

Those survive in `chain_link_*` and manuscript text, not in `world_state` reconstruction inputs.

### What This Is Not

- not a failure of the `fact_ledger` fix
- not evidence that canary-prep truth-store isolation should be reverted
- not evidence that source `world_state` should be treated as the authority baseline

The isolation wave did the right thing by removing EP4+ residue.
The remaining problem is that the rollback contract restores too little clean truth after cleanup.

## 5. Recommendation

### Primary Recommendation

Open a bounded follow-up lane:

`world-state-rollback-fidelity`

Target:

1. Extend rollback reconstruction to consume top-level episode_bible delta that already exists:
   - `new_npcs`
   - `relationship_changes`
   - `new_items` / `lost_items`
2. Re-validate prepare-only on the same polluted source
3. Confirm that pre-EP4 minimal cast / relationship / item truth survives cleanup

### Secondary Recommendation

Do **not** use `world_state` alone as preflight authority after cleanup.
Until fidelity is improved, keep the current authority preference operationally interpreted as:

- manuscript
- chain_link
- fact_ledger
- world_state

for ending-state continuity fields such as:

- location
- pending action
- opening/ending bridge

### Canary / Preflight Gating

Do not run the EP4 preflight again yet.

Next order should be:

1. fix or tighten `world_state` rollback fidelity
2. rerun prepare-only validation
3. rerun EP4 preflight on the cleaned + fidelity-preserving project

### Operator Reading Rule

For the current prepared target:

- `fact_ledger` and `chain_link` are now trustworthy after cleanup
- `world_state` is trustworthy only as a contamination-free **minimum** state, not as a high-fidelity episode-carryover snapshot

## 6. Confidence

Estimated confidence: 0.96

Reason:

- direct code evidence from `rollback_to()` and `update_from_state_changes()`
- direct before/after DB anchor comparison on source vs prepared target
- direct EP1~EP3 episode_bible inspection showing top-level delta fields that rollback currently ignores

## 7. Raw Anchors

- code:
  - [world_state.py](C:/Users/User/Desktop/글도비/modules/core/world_state.py#L768)
  - [world_state.py](C:/Users/User/Desktop/글도비/modules/core/world_state.py#L1324)
  - [stage4_canary_tools.py](C:/Users/User/Desktop/글도비/modules/core/stage4_canary_tools.py#L990)
- source DB:
  - [project_data.db](C:/Users/User/Desktop/글도비/projects/canary_0329_ep3_bp_patch_recheck/project_data.db)
- prepared target DB:
  - [project_data.db](C:/Users/User/Desktop/글도비/projects/canary_0329_truth_store_isolation_prepare_check/project_data.db)
