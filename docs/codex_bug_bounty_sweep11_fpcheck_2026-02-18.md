# Codex Bug Bounty Sweep 11 + FP Recheck (No Code Changes)

- Date: 2026-02-18
- Scope: persistence contracts around `save_anchor` / `save_v20_anchor`, Stage4 quality hook re-triage
- Method: 3 additional static rounds + false-positive revalidation
- Constraint: source code untouched (report-only)

## Round 1: `save_anchor` Bool Contract Audit

### R1-F1) `PatternTracker.save_to_db()` can return success on failed DB save
- Severity: HIGH
- Evidence:
  - `modules/core/pattern_tracker.py:461`
  - `modules/core/pattern_tracker.py:462`
  - `modules/core/db_manager.py:778`
  - `modules/core/db_manager.py:796`
  - downstream return passthrough: `modules/core/narrative_diversity.py:525`
- Why:
  - `save_anchor()` returns `False` on failure (without raising), but `save_to_db()` ignores that return and always returns `True` unless an exception is thrown.
  - Callers relying on boolean success get false-positive durability signals.

## Round 2: `save_v20_anchor` Callsite Truthfulness

### R2-F1) Stage0/1 helper prints DB-save success without checking `save_v20_anchor` result
- Severity: MEDIUM
- Evidence:
  - save call + success message pairs:
    - `modules/core/stage01_helpers.py:396` + `modules/core/stage01_helpers.py:399`
    - `modules/core/stage01_helpers.py:416` + `modules/core/stage01_helpers.py:417`
    - `modules/core/stage01_helpers.py:430` + `modules/core/stage01_helpers.py:431`
  - bool contract source:
    - `modules/core/project_manager.py:176`
    - `modules/core/project_manager.py:253`
    - `modules/core/project_manager.py:258`
- Why:
  - `save_v20_anchor()` returns bool success/failure.
  - These paths proceed to explicit success logs without validating return value, allowing operator-facing false-success output.

## Round 3: HUD Update Persistence Contract

### R3-F1) HUD update functions report applied changes even if persistence fails
- Severity: MEDIUM
- Evidence:
  - `modules/core/genre_hud_manager.py:97`
  - `modules/core/genre_hud_manager.py:98`
  - `modules/core/genre_hud_manager.py:100`
  - `modules/core/martial_manager.py:408`
  - `modules/core/martial_manager.py:409`
  - `modules/core/martial_manager.py:411`
  - bool contract source:
    - `modules/core/project_manager.py:176`
    - `modules/core/project_manager.py:253`
- Why:
  - Both functions update in-memory structures, call `save_v20_anchor()`, ignore bool, then return change logs.
  - On persistence failure, caller still receives “changes applied” semantics.

## False-Positive Recheck

### FP-A) Stage4 using `detect_score_regression(stage=2)`
- Verdict: Likely intentional (not a bug)
- Evidence:
  - Runtime call: `modules/core/stage4_post_processor.py:420`
  - Test expectation: `tests/test_stage4_orchestrator.py:498`
  - Design note: `docs/phase3_quality_feature_design.md:180`
- Reason:
  - Tests and design artifacts explicitly pin this hook to `stage=2` advisory behavior.

### FP-B) Existing `_safe_commit` bool-ignore candidates in this area
- Verdict: already-known class, no new unique defect extracted this round
- Reason:
  - Current round focused on uncovering new non-duplicated callsite defects; previously documented `_safe_commit` ignore issues remain valid but unchanged.

## Priority Recommendation

1. P1: R1-F1 (`pattern_tracker` false success)
2. P2: R2-F1 (Stage0/1 operator-facing success truthfulness)
3. P2: R3-F1 (HUD update persistence truthfulness)

## Notes

- No source code was modified in this sweep.
- This document is an addendum after `docs/codex_bug_bounty_sweep10_fpcheck_2026-02-18.md`.
