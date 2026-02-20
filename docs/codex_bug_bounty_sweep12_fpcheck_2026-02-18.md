# Codex Bug Bounty Sweep 12 + FP Recheck (No Code Changes)

- Date: 2026-02-18
- Scope: Stage2 preflight persistence, manuscript backfill sync path, narrative summary anchor save path
- Method: 3 additional static rounds + false-positive/conditional recheck
- Constraint: source code untouched (report-only)

## Round 1

### S12-R1-F1) Stage2 preflight anchor saves ignore `save_v20_anchor` bool result
- Severity: MEDIUM
- Evidence:
  - financial registry save (bool ignored): `modules/core/stage2_preflight.py:598`
  - arc summary save (bool ignored + success log): `modules/core/stage2_preflight.py:674`, `modules/core/stage2_preflight.py:675`
  - bool contract source: `modules/core/project_manager.py:176`, `modules/core/project_manager.py:253`, `modules/core/project_manager.py:258`
- Why:
  - `save_v20_anchor()` returns success/failure as bool.
  - Current code only handles exceptions. If `False` is returned, preflight can proceed as if saved (and for arc summary, emit explicit success log).

## Round 2

### S12-R2-F1) `sync_existing_manuscripts()` marks episode as synced even when vector save fails
- Severity: HIGH
- Evidence:
  - vector write returns bool: `modules/core/vec_memory.py:180`, `modules/core/vec_memory.py:193`, `modules/core/vec_memory.py:226`, `modules/core/vec_memory.py:230`
  - caller ignores bool: `modules/core/project_manager.py:855`
  - caller unconditionally sets sync status to success: `modules/core/project_manager.py:865`
- Why:
  - `memorize_v20_episode()` can return `False` for DB/embed/save failure.
  - Caller does not branch on return value and still sets `sync_status=1`, causing false-success sync metadata.

## Round 3

### S12-R3-F1) Narrative summary anchor save can fail silently but success is still logged
- Severity: MEDIUM
- Evidence:
  - save call with bool return ignored: `main_a.py:2829`
  - success log emitted: `main_a.py:2838`
  - bool contract source: `modules/core/db_manager.py:778`, `modules/core/db_manager.py:796`
- Why:
  - `save_anchor()` returns `False` on failure without raising.
  - The path proceeds to commit/log success semantics without checking return value, so persistence failure can be masked operationally.

## FP / Conditional Recheck

### C-1) `commit_full_episode_data()` bible save bool not checked
- Verdict: Conditional risk (not promoted to confirmed in this sweep)
- Evidence:
  - `modules/core/project_manager.py:540`
  - local definition found: `modules/core/project_manager.py:455`
  - no direct live callsite found by grep in runtime modules during this sweep
- Reason:
  - The pattern is risky if invoked, but current static callsite scan did not identify an active direct call path in runtime orchestrators.

## Priority Recommendation

1. P1: S12-R2-F1 (sync status corruption risk)
2. P2: S12-R1-F1 (preflight anchor false-success)
3. P2: S12-R3-F1 (narrative summary save observability mismatch)

## Notes

- No source code was modified in this sweep.
- This document is an addendum after `docs/codex_bug_bounty_sweep11_fpcheck_2026-02-18.md`.
