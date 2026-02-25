# Runbook

Purpose:
- Define operational procedures for rollback/reset/rewind actions used by the main menu.

## Scope and Entry Points
- Menu `44` -> `main_a.py:_rollback_episode()` -> `ProjectService.rollback_episode()`
- Menu `77` -> `main_a.py:_wipe_production_data()` -> `ProjectService.wipe_production_data()`
- Menu `88` -> `main_a.py:_reset_stage_2()` -> `ProjectService.reset_stage_2()`
- Menu `99` -> `main_a.py:_rewind_stage_2()` -> `ProjectService.rewind_stage_2()`

## Menu 44: Stage 4 Episode Rollback
Operator inputs:
1. Confirm target episode `target_ep` in range `1..latest_ep`.
2. Confirm destructive rollback for all records `ep >= target_ep`.

Data operations:
1. Optional HUD rollback in `anchors[key='bible']` using `state_logs[target_ep-1]` snapshot.
2. Delete `ep_num >= target_ep` from:
- `manuscripts`
- `blueprints`
- `state_logs`
- `martial_tracker`
- `sync_status`
- `causal_graph`
3. Additional cleanup:
- `DELETE FROM encyclopedia` (full wipe)
- `DELETE FROM karma_status WHERE last_updated_ep >= target_ep`
- `DELETE FROM npc_history WHERE episode_no >= target_ep`
- `UPDATE seeds SET status='active', recovered_ep=NULL WHERE recovered_ep >= target_ep`
- `DELETE FROM director_selections WHERE ep_num >= target_ep`
- `delete_episode_bibles_after(target_ep - 1)` (removes episode bibles for rolled-back range)
4. Reset selected SQLite sequences for episode tables.
5. Commit DB transaction via safe commit.

Non-DB operations:
1. Delete draft files matching episode number `>= target_ep` in `projects/{name}/drafts/*.txt`.
2. Vector memory cleanup via `memory.delete_episodes_from(target_ep)`.
3. Reload project from DB (`project._load_from_db()`).
4. Runtime tracker rollback:
- `world_state.rollback_to(target_ep)` if available.
- `fact_ledger.rollback_to(target_ep)` if available.
- `emotion_tracker.rollback_to(target_ep)` if available.
- `state_delta_tracker.rollback_to(target_ep)` if available.
5. Restore preset registry callback if configured.

Post-success cache invalidation in `main_a.py` wrapper:
- `state_tracker = None`
- prompt timeline cache invalidate
- cumulative state cache clear
- narrative summaries cache clear
- writer manuscript cache invalidate (if supported)
- director cache invalidate (if supported)
- foreshadow tracker clear + DB sync (if supported)

## Menu 77: Wipe Production Data (Stage 4 Reset)
Operator action:
1. Confirm wipe prompt.

Data operations:
1. Full table delete (all rows):
- `manuscripts`
- `blueprints`
- `state_logs`
- `martial_tracker`
- `causal_graph`
- `sync_status`
- `karma_status`
2. `UPDATE seeds SET status='active', recovered_ep=NULL`
3. Commit DB transaction.

Non-DB operations:
1. Delete all draft txt files in `projects/{name}/drafts/`.
2. Vector memory full cleanup via `memory.delete_all_episodes()` if available.

Notes:
- This action does not delete `npc_history` in `ProjectService.wipe_production_data()`.

## Menu 88: Stage 2 Reset (Arcs Full Clear)
Operator action:
1. Confirm reset prompt.

Data operations:
1. `DELETE FROM anchors WHERE key='arcs'`
2. Safe commit.
3. In-memory `project.arcs = []`

Result:
- Stage 2 is treated as not completed; arc design must be regenerated.

## Menu 99: Stage 2 Selective Rewind
Operator inputs:
1. Enter `target_no` in `1..len(project.arcs)`.
2. Confirm delete from `target_no` to last arc.

Data operations:
1. Build `updated_arcs = [arc for arc in arcs if arc.arc_no < target_no]`.
2. Persist with `save_v20_anchor('arcs', updated_arcs)`.
3. Replace in-memory `project.arcs = updated_arcs`.

Post-wrapper cache handling:
- Clear cumulative state cache and key.
- Invalidate timeline cache.
- Clear narrative summaries cache.
- Invalidate `state_extractor` cache if supported.

## NPC History Rollback Policy
- `npc_history` behaves as append-only during forward generation.
- Rollback path (menu `44`) explicitly deletes `npc_history` records with `episode_no >= target_ep`.
- Wipe path (menu `77`) does not touch `npc_history`.
- Stage 2 reset/rewind (menu `88`/`99`) does not touch `npc_history`.

## Legacy/Support Path (ProjectContext)
- `ProjectContext.reset_project(target_ep)` calls `db.reset_after(target_ep)` and removes draft files `ep_*.txt >= target_ep`.
- `ProjectContext.auto_backtrack_v35(...)` can call `reset_project`, vector memory rewind, and optional `world_state/fact_ledger` rollback.
- `db.reset_after(target_ep)` includes broader cleanup (for example `npc_history`, `episode_sentence_hashes`, `episode_satisfaction_tags`, `director_selections`, `episode_pacing`, `episode_meta`).

## Incident Template
- Timestamp:
- Menu action (`44`/`77`/`88`/`99`):
- Target episode/arc:
- Trigger:
- Impact:
- Immediate mitigation:
- Root cause:
- Preventive action:

## Last Verified
- Date: 2026-02-25
- Commit: `f99119d`
- Code Sync (Yes/No): Yes
- Verified By: Codex

