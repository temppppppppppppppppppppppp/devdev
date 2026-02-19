# Codex Bug Bounty Sweep 5 + False-Positive Triage (No Code Changes)

- Date: 2026-02-18
- Scope: `main_a.py`, `modules/core/**`, `modules/domain/agents/**`, `modules/core/services/**`
- Method: static deep read + cross-module contract trace + prior finding re-validation

## Summary

- Revalidated items: 15
- `Confirmed`: 11
- `Conditional / Design-risk`: 3
- `Likely False Positive`: 1

## Sweep 1~2 Revalidation (FP Check)

| ID | Prior Finding | Recheck Verdict | Evidence |
|---|---|---|---|
| BB-01 | StateTracker validation effectively disabled | Confirmed | `modules/domain/agents/analyst.py:927`, `modules/domain/agents/analyst.py:928`, `modules/domain/agents/analyst.py:1446`, `modules/domain/agents/analyst.py:1451` |
| BB-02 | `joint_docs` contract mismatch (nested vs top-level) | Confirmed | `modules/domain/agents/analyst.py:413`, `modules/domain/agents/analyst.py:416`, `modules/core/stage2_finalizer.py:174`, `modules/core/stage2_finalizer.py:188` |
| BB-03 | ArcCorrector change-ratio guard bypass when output grows | Confirmed | `modules/domain/agents/arc_corrector.py:505`, `modules/domain/agents/arc_corrector.py:506` |
| BB-04 | `physical_inventory` fallback type mismatch (string vs array) | Confirmed | `modules/core/stage2_finalizer.py:193`, `modules/core/response_schemas.py:284` |
| BB-05 | Reset path ignores commit result but reports success | Confirmed | `modules/core/services/project_service.py:49`, `modules/core/services/project_service.py:50`, `modules/core/services/project_service.py:51` |
| BB-06 | Rollback/Wipe cross-store non-atomic ordering | Conditional / Design-risk | `modules/core/services/project_service.py:185`, `modules/core/services/project_service.py:188`, `modules/core/services/project_service.py:258`, `modules/core/services/project_service.py:260`, `modules/core/services/project_service.py:273` |
| BB-07 | Backup response validator key-field bias | Conditional / Path-dependent | `modules/domain/agents/base_agent.py:797`, `modules/domain/agents/base_agent.py:800`, `modules/domain/agents/arc_critic.py:317` |
| BB-08 | Project picker crash if `projects/` missing | Likely False Positive | `main_a.py:2654` vs bootstrap creation at `modules/core/config_manager.py:21`, `modules/core/config_manager.py:22` and system init `modules/core/system.py:18` |
| BB-09 | HUD anomaly checker masks internal errors as no-anomaly | Confirmed | `modules/domain/agents/chief_writer_context.py:781`, `modules/domain/agents/chief_writer_context.py:782`, `modules/domain/agents/chief_writer_context.py:925` |

## Sweep 3~5 New / Strengthened Findings

### BB-10) Stage2 commit bool contract is ignored (False-success risk)
- Severity: CRITICAL
- Evidence:
  - `main_a.py:303` (`_safe_commit_async()` returns `bool`)
  - `modules/core/stage2_finalizer.py:282` save called
  - `modules/core/stage2_finalizer.py:283` await commit called
  - `modules/core/stage2_finalizer.py:303` success path proceeds without bool check
- Why:
  - Only exceptions are handled; `False` return path is silently treated as success.

### BB-11) Stage3 blueprint commit result ignored
- Severity: HIGH
- Evidence:
  - `modules/core/stage3_orchestrator.py:478`
  - `modules/core/stage3_orchestrator.py:479`
  - `modules/core/stage3_orchestrator.py:482`
- Why:
  - Failed commit can still increment success flow and history state.

### BB-12) Rewind/Rollback persistence results ignored
- Severity: HIGH
- Evidence:
  - `modules/core/services/project_service.py:79`
  - `modules/core/services/project_service.py:185`
- Why:
  - Save/commit bool contracts are not consumed, enabling false-success operator feedback.

### BB-13) `joint_docs/status_shadow` overwrite pattern can discard generated data
- Severity: HIGH (Conditional)
- Evidence:
  - `modules/core/stage2_preflight.py:538`, `modules/core/stage2_preflight.py:539`
  - `modules/core/stage2_validation_pipeline.py:386`, `modules/core/stage2_validation_pipeline.py:387`
  - `modules/core/stage2_finalizer.py:174`, `modules/core/stage2_finalizer.py:175`
- Why:
  - Blind overwrite from `enriched_block` may regress data from other generators/correctors depending on runtime path.

### BB-14) Type-unsafe `.get()` on potentially non-dict LLM fields
- Severity: HIGH
- Evidence:
  - `modules/core/stage2_finalizer.py:199`, `modules/core/stage2_finalizer.py:200`
  - `modules/core/stage2_finalizer.py:206`, `modules/core/stage2_finalizer.py:207`
- Why:
  - Truthy non-dict payload in `joint_docs`/`status_shadow` can hard-crash (`AttributeError`).

### BB-15) Analyst fallback path still has `arcs` shape drift
- Severity: MEDIUM
- Evidence:
  - Dict-style access: `modules/domain/agents/analyst.py:951`, `modules/domain/agents/analyst.py:952`
  - List-style access: `modules/domain/agents/analyst.py:1471`, `modules/domain/agents/analyst.py:1472`
  - Stage2 save uses list: `modules/core/stage2_finalizer.py:282`
- Why:
  - Fallback continuity lookup can be skipped silently due shape mismatch.

### BB-16) Additional low-priority bool-ignore call sites
- Severity: LOW
- Evidence:
  - `main_a.py:1096`, `main_a.py:1097`
  - `modules/core/stage4_orchestrator.py:811`, `modules/core/stage4_orchestrator.py:818`
- Why:
  - Commit/save bool results are discarded; mostly impacts operability/error transparency.

## Recommended Fix Order

1. P0 durability truthfulness: BB-10, BB-11, BB-12.
2. P1 contract/data correctness: BB-02, BB-04, BB-14, BB-15.
3. P1 continuity quality protection: BB-01, BB-09, BB-13.
4. P2 fallback resilience/ops: BB-07, BB-16 class issues.

## Notes

- No source code was modified in this sweep.
- This document supersedes the status of findings in:
  - `docs/codex_bug_bounty_sweep_2026-02-18.md`
  - `docs/codex_bug_bounty_sweep2_2026-02-18.md`
