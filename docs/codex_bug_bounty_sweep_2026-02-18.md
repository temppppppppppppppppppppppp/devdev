# Codex Bug Bounty Sweep Report (No Code Changes)

- Date: 2026-02-18
- Scope: `main_a.py`, `modules/core/**`, `modules/domain/agents/**`, `modules/core/services/**`
- Method: static sweep + manual line validation (no source edits, no runtime patching)

## Findings (Ordered by Severity)

### 1) State consistency check is effectively disabled
- Severity: CRITICAL
- Evidence:
  - `modules/domain/agents/analyst.py:927` calls state tracker validation
  - `modules/domain/agents/analyst.py:1451` immediately returns `[]`
- Why this is a bug:
  - The pipeline appears to enforce state continuity, but the core checker is hard-disabled.
  - Contradictions can pass silently because `if state_issues:` branch at `modules/domain/agents/analyst.py:929` never fires.
- Impact:
  - High risk of cross-arc inconsistency in production output.

### 2) `joint_docs` schema path is inconsistent (nested vs top-level)
- Severity: CRITICAL
- Evidence:
  - Analyst writes/reads nested path:
    - `modules/domain/agents/analyst.py:191`
    - `modules/domain/agents/analyst.py:413`
    - `modules/domain/agents/analyst.py:416`
  - Stage2/final validators expect top-level path:
    - `modules/core/stage2_finalizer.py:174`
    - `modules/core/stage2_finalizer.py:188`
- Why this is a bug:
  - Two incompatible contracts exist for the same field.
  - Auto-corrections in Analyst can be invisible to downstream modules that read top-level `joint_docs`.
- Impact:
  - Continuity correction appears to run but can be dropped in later stages.

### 3) ArcCorrector change guard can be bypassed by expansion
- Severity: HIGH
- Evidence:
  - `modules/domain/agents/arc_corrector.py:505` returns `True` when corrected text is longer.
- Why this is a bug:
  - Change-ratio safeguard only constrains shrink/delete cases.
  - A very large additive rewrite can pass guard even when semantically unsafe.
- Impact:
  - Over-correction risk and hidden narrative drift.

### 4) Stage2 fallback injects wrong type for `physical_inventory`
- Severity: HIGH
- Evidence:
  - `modules/core/stage2_finalizer.py:193` sets `"physical_inventory": "물품 미정"` (string)
  - Schema expects array:
    - `modules/core/response_schemas.py:284`
- Why this is a bug:
  - Contract violation at fallback path.
  - Subsequent logic may branch incorrectly or skip inheritance due non-list truthy string.
- Impact:
  - Data quality degradation and inconsistent downstream behavior.

### 5) Reset path can report success even when DB commit failed
- Severity: HIGH
- Evidence:
  - `modules/core/services/project_service.py:49` calls `_safe_commit()` without checking result
  - `modules/core/services/project_service.py:50` mutates in-memory state and
  - `modules/core/services/project_service.py:51` logs success unconditionally
- Why this is a bug:
  - DB failure can still produce success UX and mutated runtime state.
- Impact:
  - Operator misled; DB/runtime divergence.

### 6) Wipe/rollback ordering allows partial irreversible state
- Severity: HIGH
- Evidence:
  - `modules/core/services/project_service.py:185` commit in rollback flow, then file/vector cleanup later
  - `modules/core/services/project_service.py:258` commit in wipe flow
  - `modules/core/services/project_service.py:260` file deletion after commit
  - `modules/core/services/project_service.py:273` errors are only logged
- Why this is a bug:
  - Cross-store operations (DB, files, vector store) are not atomic.
  - Failures after commit cause partial state with no compensating rollback.
- Impact:
  - Recovery complexity and integrity incidents after interrupted maintenance operations.

### 7) Backup-response validator is over-specialized to a subset of agent outputs
- Severity: MEDIUM
- Evidence:
  - Generic backup gate:
    - `modules/domain/agents/base_agent.py:649`
    - `modules/domain/agents/base_agent.py:797`
  - Requires one of `content/tactical_doc/integrated_scenario/title/state_updates`.
  - Counterexample output shape exists (critic-style):
    - `modules/domain/agents/arc_critic.py:318`
    - `modules/domain/agents/arc_critic.py:320`
- Why this is a bug:
  - Valid JSON outputs from some agents can be rejected during fallback path.
- Impact:
  - Reduced resilience exactly when fallback is needed.

### 8) Project picker can crash on fresh environment
- Severity: MEDIUM
- Evidence:
  - `main_a.py:2654` uses `root.iterdir()` without existence guard on `projects/`.
- Why this is a bug:
  - First-run or moved workspace can raise `FileNotFoundError` before user-facing handling.
- Impact:
  - Boot-time crash in uninitialized environments.

### 9) HUD anomaly checker masks internal failures as “no anomaly”
- Severity: MEDIUM
- Evidence:
  - `modules/domain/agents/chief_writer_context.py:793`
  - `modules/domain/agents/chief_writer_context.py:794`
- Why this is a bug:
  - Exception path returns `has_anomalies: False`, which suppresses warnings in callers.
- Impact:
  - Hidden continuity/hud-quality issues during episode generation.

## Triage Order (Recommended)
1. Fix contract breakages first: Findings #1, #2, #4.
2. Fix integrity/recovery next: Findings #3, #5, #6.
3. Then resilience/operability: Findings #7, #8, #9.

## Notes
- No code changes were made in this sweep.
- This report is intended for handoff to Opus for implementation planning.
