# C4 Quality Risk Discriminability Reclassification (3-Pass Audit)

Date: 2026-03-20
Mode: system-track live reclassification
Confidence: 0.97

Superseded by:

- `docs/2026-03-20/c4-quality-risk-semantic-split-3pass-audit.md`

## Scope

- Source screening note:
  - `docs/2026-03-20/opus-be-p0-p3-remaining-screening-3pass-audit.md`
- Live re-check targets:
  - `modules/domain/agents/director_ensemble.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/domain/agents/three_phase_blueprint_generator.py`
  - `tests/test_director_modules.py`
  - `tests/test_blueprint_patch_mode.py`

## Original Claim

OPUS marked `quality_risk` as a bounded backend bug because verdict-driven folding made the signal nearly flat.

## Live Re-check

The verdict-folding is not isolated to one Stage 3 adapter layer.

It currently exists in all three places:

- `director_ensemble.compare_and_select_blueprint()`
  - `quality_risk = ... or decision in ("PASS_WITH_FIX", "PASS_WITH_WARNING")`
- `unified_blueprint_validator.validate()`
  - compare flow folds verdict into `quality_risk`
- `three_phase_blueprint_generator.generate()`
  - pipeline meta folds verdict into `_validation_quality_risk`

There is also explicit test coverage for the current semantics:

- `tests/test_director_modules.py`
  - `PASS_WITH_WARNING` is expected to set `quality_risk=True` even when candidate advisory risk is false
- `tests/test_blueprint_patch_mode.py`
  - Stage 3 pipeline is expected to persist `quality_risk`

## Judgment

`C4` is still live as a semantic concern, but it is no longer a good bounded patch candidate.

Why:

- the behavior is cross-layer, not local
- downstream Stage 4 uses Stage 3 `quality_risk` for advisory and early-trigger logic
- current tests encode the present meaning as intentional behavior

So the problem is not "missing patch" anymore.
It is a policy question:

- should `quality_risk` mean only evidence-backed structural risk
- or should it continue to include verdict-level repair pressure

## Decision

Reclassify `C4` from bounded backend patch to policy-shaped item.

No code change is made in this turn.

## Outcome

Within the remaining OPUS BE P0-P3 screening set, there are no clearly bounded backend patch candidates left after `C1`, `C8`, and `C10`.
