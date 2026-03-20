# C4 Quality Risk Semantic Split (3-Pass Audit)

Date: 2026-03-20
Mode: system-track bounded backend semantics patch
Confidence: 0.98

## Scope

- Source screening note:
  - `docs/2026-03-20/opus-be-p0-p3-remaining-screening-3pass-audit.md`
- Prior policy reclassification note:
  - `docs/2026-03-20/c4-quality-risk-policy-reclassification-3pass-audit.md`
- Live patch targets:
  - `modules/domain/agents/director_ensemble.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/domain/agents/three_phase_blueprint_generator.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_interview_round.py`

## Problem

`quality_risk` had been overloaded.

The same flag meant both:

- evidence-backed structural or continuity risk
- verdict-level "still needs revision" pressure from `PASS_WITH_FIX` / `PASS_WITH_WARNING`

That made the signal too flat and pushed advisory-grade repair pressure into Stage 4's stronger `quality_risk` lane.

## Live Change

The signal is now split into two tracks.

- `quality_risk`
  - real risk only
  - still includes Python/prevalidation-derived or validator/director-derived substantive risk
- `revision_required`
  - editorial or repair pressure
  - set when the result is effectively "acceptable, but still needs follow-up work"

Implemented changes:

- `director_ensemble.compare_and_select_blueprint()`
  - no longer folds `PASS_WITH_FIX` / `PASS_WITH_WARNING` directly into `quality_risk`
  - now returns `revision_required`
- `unified_blueprint_validator.validate()`
  - compare flow and single-candidate flow now emit `revision_required`
  - single-candidate `PASS_WITH_FIX` no longer forces `quality_risk=True`
- `three_phase_blueprint_generator.generate()`
  - validation phase and top-level pipeline result now persist `revision_required`
  - verdict-driven folding into pipeline `quality_risk` is removed
  - emergency `PASS_WITH_WARNING` fallback still marks both `quality_risk` and `revision_required`
- `stage3_orchestrator._handle_success()`
  - Stage 3 meta now stores both `quality_risk` and `revision_required`
  - QualityDashboard warnings/quality_signals now carry `revision_required`
  - director selection advisory payload now carries `revision_required`
- `stage4_interview_round`
  - `quality_risk` remains the high-severity Stage 4 advisory
  - `revision_required` now injects a softer Stage 3 carry-over note
  - V75-D early trigger still keys only off `quality_risk`

## Intentional Non-Change

This patch does **not** redefine every downstream policy.

Kept as-is:

- Stage 4 V75-D early trigger threshold logic
- Stage 3 quality gate semantics
- repair loop routing and Director sovereignty

The split is bounded to signal meaning, not repair-lane governance.

## Validation

Sequential shard validation:

- `python -m pytest tests/test_director_modules.py -q`
- `python -m pytest tests/test_legacy_reentry_reaudit.py -q`
- `python -m pytest tests/test_blueprint_patch_mode.py -q`
- `python -m pytest tests/test_stage3_orchestrator.py -q`
- `python -m pytest tests/chaos/test_stage3_metrics.py -q`
- `python -m pytest tests/test_pass_with_fix.py -q`

All passed in the live workspace during this patch.

## Outcome

`C4` is no longer just a policy-shaped concern.

The bounded semantic split is now implemented:

- `quality_risk` = true risk
- `revision_required` = repair/advisory pressure

This closes the OPUS-derived backend ambiguity without changing Director ownership or high-risk Stage 4 authority rules.
