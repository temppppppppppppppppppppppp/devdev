# Codex Bug Bounty Sweep 2 (No Code Changes)

- Date: 2026-02-18
- Scope: Stage2/3 orchestration, project ops services, analyst fallback paths
- Method: static deep read + cross-module contract tracing (no source edits)

## Findings (New in Sweep 2)

### 1) Stage2 can treat failed DB commit as success
- Severity: CRITICAL
- Evidence:
  - `main_a.py:303` defines `_safe_commit_async()` and returns `bool` (`False` on failure).
  - `modules/core/stage2_finalizer.py:283` awaits `safe_commit_async()` but never checks return value.
  - Success flow continues immediately after at `modules/core/stage2_finalizer.py:303`.
- Why this is a bug:
  - Commit failure that returns `False` is not handled (only exceptions are handled).
  - Arc/state may be treated as persisted when DB commit actually failed.
- Impact:
  - False PASS, runtime/DB divergence, recovery confusion.

### 2) Stage3 blueprint success path ignores commit result
- Severity: HIGH
- Evidence:
  - `modules/core/stage3_orchestrator.py:478` saves blueprint.
  - `modules/core/stage3_orchestrator.py:479` calls `ctx.safe_commit()` and ignores return.
  - Flow still increments success and updates history at `modules/core/stage3_orchestrator.py:482`.
- Why this is a bug:
  - Same bool-return contract issue as Stage2.
  - Failed commit can still be counted/logged as a successful episode blueprint.
- Impact:
  - Hidden data loss and incorrect operational metrics.

### 3) Project ops paths can report success after failed persistence
- Severity: HIGH
- Evidence:
  - `modules/core/services/project_service.py:49` commit result ignored in `reset_stage_2`.
  - `modules/core/services/project_service.py:50` mutates in-memory `project.arcs` anyway.
  - `modules/core/services/project_service.py:51` logs success unconditionally.
  - `modules/core/services/project_service.py:79` `save_v20_anchor("arcs", ...)` return value ignored in rewind flow.
  - `modules/core/services/project_service.py:185` rollback flow commit result ignored.
- Why this is a bug:
  - Persistence contracts (`bool` success/failure) are not respected.
  - Operator can receive success messages when state is not actually durable.
- Impact:
  - Misleading maintenance outcomes and inconsistent project state.

### 4) `joint_docs/status_shadow` are overwritten across stages (possible data loss)
- Severity: HIGH
- Evidence:
  - `modules/core/stage2_preflight.py:538`
  - `modules/core/stage2_preflight.py:539`
  - `modules/core/stage2_finalizer.py:174`
  - `modules/core/stage2_finalizer.py:175`
  - `modules/core/stage2_validation_pipeline.py:387` (non-four-phase path)
- Why this is a bug:
  - Downstream blindly overwrites these fields from `enriched_block`.
  - Can discard or regress values produced/corrected by other components (e.g., FourPhase/continuity flows).
- Impact:
  - Silent continuity degradation and harder root-cause analysis.

### 5) Type-unsafe dict access in Stage2 finalizer can hard-crash
- Severity: HIGH
- Evidence:
  - `modules/core/stage2_finalizer.py:199` then `modules/core/stage2_finalizer.py:200`
  - `modules/core/stage2_finalizer.py:206` then `modules/core/stage2_finalizer.py:207`
- Why this is a bug:
  - `.get()` is called assuming `joint_docs`/`status_shadow` are dicts.
  - These fields are injected from external model output (`enriched_block`) without strict type guard at this point.
- Impact:
  - `AttributeError` risk and stage interruption on malformed but truthy payloads.

### 6) Analyst fallback continuity loader uses wrong `arcs` anchor shape
- Severity: MEDIUM
- Evidence:
  - `modules/domain/agents/analyst.py:950` loads `arcs` anchor.
  - `modules/domain/agents/analyst.py:951` assumes dict.
  - `modules/domain/agents/analyst.py:952` expects key like `arc_{n}`.
  - Elsewhere same module treats `arcs` as list: `modules/domain/agents/analyst.py:1472`.
  - Stage2 save path stores list: `modules/core/stage2_finalizer.py:282`.
- Why this is a bug:
  - Contract mismatch makes `prev_arc_data` unresolved in this fallback logic.
  - Continuity validation block is effectively bypassed on that path.
- Impact:
  - Fallback generation quality checks silently weakened.

## Recommended Triage
1. Fix commit-result handling first: Findings #1, #2, #3.
2. Fix continuity contract handling next: Findings #4, #5.
3. Normalize fallback anchor contract: Finding #6.

## Notes
- No code changes were made.
- This file is intended as addendum to `docs/codex_bug_bounty_sweep_2026-02-18.md`.
