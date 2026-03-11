# Runbook

Purpose:
- Define the current operational semantics for destructive safe-op menu actions.

Desktop UI:
- Safe Ops now surfaces a read-only preview before execution.
- The preview distinguishes `deleted` vs `preserved` scope.
- The confirm modal reflects Stage 2 vs Stage 4 `director_selections` split.

## Scope and Entry Points
- Menu `44` -> `main_a.py:_rollback_episode()` -> `ProjectService.rollback_episode()`
- Menu `77` -> `main_a.py:_wipe_production_data()` -> `ProjectService.wipe_production_data()`
- Menu `88` -> `main_a.py:_reset_stage_2()` -> `ProjectService.reset_stage_2()`
- Menu `99` -> `main_a.py:_rewind_stage_2()` -> `ProjectService.rewind_stage_2()`

## Menu 44: Stage 4 Episode Rollback
Operator inputs:
1. Select `target_ep` in `1..latest_ep`.
2. Confirm destructive rollback for every artifact `ep >= target_ep`.

Data operations:
1. If possible, restore HUD protagonist `actual_truth` from `state_logs[target_ep - 1]`.
2. Call `db.reset_after(target_ep)`:
- `blueprints`
- `state_logs`
- `causal_graph`
- `manuscripts`
- `martial_tracker`
- `episode_bibles`
- `sync_status`
- `karma_status`
- `npc_history`
- `episode_sentence_hashes`
- `episode_satisfaction_tags`
- `director_selections` for Stage 4 / legacy episode selections only
- `episode_pacing`
- `episode_quality_labels`
- `episode_quality_signals`
- `episode_quality_observations`
- `episode_meta`
- `episode_fts`
- `vec_episodes`
- `foreshadow`
- `npc_relationship_edges`
- `npc_relationship_history`
- `stage_attempts` for stages `3` and `4`
3. Restore seeds recovered after `target_ep`:
- `UPDATE seeds SET status='active', recovered_ep=NULL WHERE recovered_ep >= target_ep`
4. Save restored bible anchor if HUD rollback data was found.

Non-DB operations:
1. Delete draft files `ep >= target_ep`.
2. Delete vector memory via `memory.delete_episodes_from(target_ep)` if available.
3. Reload project from DB.
4. Roll runtime state back to `target_ep`:
- `world_state.rollback_to(target_ep)` if available
- `fact_ledger.rollback_to(target_ep)` if available
- `emotion_tracker.rollback_to(target_ep)` if available
- `state_delta_tracker.rollback_to(target_ep)` if available
5. Restore preset registry if configured.

Post-success cache invalidation in `main_a.py`:
- `state_tracker = None`
- prompt timeline cache invalidate
- cumulative state cache clear
- narrative summaries cache clear
- writer manuscript cache invalidate
- director cache invalidate
- foreshadow tracker clear + DB sync

Notes:
- `encyclopedia` is no longer force-wiped during episode rollback.
- Stage 2 `director_selections` are preserved during episode rollback because the table now carries a `stage` split.

## Menu 77: Wipe Production Data
Operator action:
1. Confirm wipe prompt.

Intent:
- Keep setup/design assets.
- Remove episode-derived production artifacts so generation can restart cleanly.

Data operations:
1. Call `db.reset_after(1)` to clear all episode-derived tables listed in Menu `44`.
2. Restore all recovered seeds:
- `UPDATE seeds SET status='active', recovered_ep=NULL`

Non-DB operations:
1. Delete all draft txt files.
2. Delete all vector memory via `memory.delete_all_episodes()` if available.
3. Reload project from DB and roll runtime state back to the initial state.

Post-success cache invalidation in `main_a.py`:
- `state_tracker = None`
- prompt timeline cache invalidate
- cumulative state cache clear
- narrative summaries cache clear
- writer manuscript cache invalidate
- director cache invalidate
- `state_extractor` cache invalidate
- foreshadow tracker clear + DB sync

Notes:
- This action now clears `npc_history`, quality tables, pacing tables, relationship history, Stage 3/4 `stage_attempts`, and Stage 4 `director_selections`.
- Stage 2 arc design and Stage 2 selection history are preserved.

## Menu 88: Stage 2 Reset (Full Arc Reset)
Operator action:
1. Confirm reset prompt.

Intent:
- Drop every Stage 2 arc artifact and every downstream episode artifact.

Data operations:
1. Call `db.reset_after(1)` to clear downstream episode-derived tables.
2. Delete Stage 2-specific metadata:
- `DELETE FROM arc_dependencies`
- `DELETE FROM stage_attempts WHERE stage = 2`
- `DELETE FROM director_selections WHERE stage = 2` (+ legacy Stage 2 rows with empty `selected_label`)
3. Delete Stage 2 anchors:
- `DELETE FROM anchors WHERE key = 'arcs'`
- `DELETE FROM anchors WHERE key = 'volumes'`
- `DELETE FROM anchors WHERE key = 'series_summary'`
- `DELETE FROM anchors WHERE key LIKE 'arc_summary_%'`
- `DELETE FROM anchors WHERE key LIKE 'volume_summary_%'`
4. Commit anchor / Stage 2 metadata cleanup.
5. Set in-memory `project.arcs = []`.

Non-DB operations:
1. Delete all draft txt files.
2. Delete all vector memory via `memory.delete_all_episodes()` if available.
3. Reload project from DB and roll runtime state back to the initial state.

Post-success cache invalidation in `main_a.py`:
- `state_tracker = None`
- prompt timeline cache invalidate
- cumulative state cache clear
- narrative summaries cache clear
- writer manuscript cache invalidate
- director cache invalidate
- `state_extractor` cache invalidate
- foreshadow tracker clear + DB sync

## Menu 99: Stage 2 Selective Rewind
Operator inputs:
1. Enter `target_no` in `1..len(project.arcs)`.
2. Confirm destructive rewind.

Intent:
- Keep earlier arcs.
- Delete later arcs and every downstream episode artifact generated from the removed arc range.

Data operations:
1. Build `updated_arcs = [arc for arc in arcs if arc.arc_no < target_no]`.
2. Infer `target_ep` from the removed arcs' `ep_start` if available; otherwise fall back to `target_no`.
3. Call `db.reset_after(target_ep)` to clear downstream episode-derived tables.
4. Delete Stage 2-specific metadata for removed arcs:
- `DELETE FROM arc_dependencies WHERE from_arc_no >= target_no OR to_arc_no >= target_no`
- `DELETE FROM stage_attempts WHERE stage = 2 AND arc_num >= target_no`
- `DELETE FROM director_selections WHERE stage = 2 AND ep_num >= target_no` (+ legacy Stage 2 rows with empty `selected_label`)
5. Delete stale Stage 2 summary anchors:
- `DELETE FROM anchors WHERE key = 'volumes'`
- `DELETE FROM anchors WHERE key = 'series_summary'`
- `DELETE FROM anchors WHERE key LIKE 'volume_summary_%'`
- `DELETE FROM anchors WHERE key GLOB 'arc_summary_[0-9]*' AND CAST(SUBSTR(key, 13) AS INTEGER) >= target_no`
6. Save the reduced `arcs` anchor.
7. Replace in-memory `project.arcs = updated_arcs`.

Non-DB operations:
1. Delete draft txt files `ep >= target_ep`.
2. Delete vector memory via `memory.delete_episodes_from(target_ep)` if available.
3. Reload project from DB and roll runtime state back to `target_ep`.

Post-success cache invalidation in `main_a.py`:
- `state_tracker = None`
- prompt timeline cache invalidate
- cumulative state cache clear
- narrative summaries cache clear
- writer manuscript cache invalidate
- director cache invalidate
- `state_extractor` cache invalidate
- foreshadow tracker clear + DB sync

## Legacy / Support Path
- `ProjectContext.reset_project(target_ep)` still delegates to `db.reset_after(target_ep)` and draft cleanup.
- `db.get_rollback_impact(target_ep)` now includes quality tables, pacing, foreshadow, relationship edges, and Stage 3/4 `stage_attempts`.

## Incident Template
- Timestamp:
- Menu action (`44` / `77` / `88` / `99`):
- Target episode / arc:
- Trigger:
- Impact:
- Immediate mitigation:
- Root cause:
- Preventive action:

## Last Verified
- Date: 2026-03-11
- Code Sync: Yes
- Verified By: Codex
