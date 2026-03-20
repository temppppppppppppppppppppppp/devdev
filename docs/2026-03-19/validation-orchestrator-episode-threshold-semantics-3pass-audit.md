# validation-orchestrator-episode-threshold-semantics-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.95`
Canonical Path: `docs/2026-03-19/validation-orchestrator-episode-threshold-semantics-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 112`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Evidence Basis:
- `modules/validation/validation_orchestrator.py`
- `tests/test_validation_orchestrator.py`
Scope:
- audit whether episode-type adaptive-threshold adjustments are accidental magic numbers or intentional policy semantics
- clarify how overlapping episode types combine
- add direct regression coverage for the current combination rule
- non-goal: retune validation thresholds or rewrite adaptive-threshold policy

---

## Pass 1. Structure and Scope

This audit is limited to episode-type threshold adjustment in `ValidationOrchestrator`.

Covered behavior:
- `opening`
- `climax`
- `transition`
- `arc_finale`
- `volume_finale`

Key operator question:
- are these values just stale constants that should be freely edited, or are they active validation policy boundaries?

This audit does not cover:
- genre base thresholds
- streak adjustments
- pattern-based adjustments
- manual threshold override behavior

---

## Pass 2. Evidence and Consistency

### 1. Live code clearly models episode type as policy

`modules/validation/validation_orchestrator.py` defines `EPISODE_TYPE_ADJUSTMENTS` as a named policy table.

Observed live configuration:
- `opening`: `+5` on episodes `1, 2, 3`
- `climax`: `+3`
- `transition`: `-3`
- `arc_finale`: `+5`
- `volume_finale`: `+7`

Why this matters:
- these are not inline ad-hoc numbers inside scoring code
- they are a top-level policy map
- comments explicitly describe narrative role, such as `opening: higher bar`

Conclusion:
- these values are policy semantics, not generic low-risk tuning scraps

### 2. Overlap behavior is intentional and non-additive on the positive side

The combination rule is important.

`_get_episode_type_adjustment_v59()` does not sum all matching deltas.
Instead it does:
- keep the strongest matching positive delta
- keep the strongest matching negative delta
- return `positive_adj + negative_adj`

Operational meaning:
- overlapping positive episode types do not stack indefinitely
- but a positive and a negative can offset each other

Concrete live examples:
- episode `1` gets `opening +5`
- episode `5` matches `transition -3` and `arc_finale +5`, producing `+2`
- episode `50` matches `climax +3`, `arc_finale +5`, and `volume_finale +7`, but returns only `+7`

Conclusion:
- current behavior is not accidental addition logic
- it is a bounded policy rule that prevents runaway positive stacking

### 3. Direct regression coverage added in this audit

Before this audit, tests only covered:
- profile loading
- clamping
- general validation paths

They did not directly fix:
- opening episodes having a higher bar
- overlap using strongest positive plus strongest negative
- volume finale preferring `+7` rather than additive stacking

New regression coverage now fixes these semantics into contract:
- `ep=1 -> +5`
- `ep=5 -> +2`
- `ep=50 -> +7`

Rerun evidence:
- `python -m pytest tests/test_validation_orchestrator.py -k "episode_type_adjustment or adaptive_threshold_is_clamped" -q`
- `python -m pytest tests/test_validation_orchestrator.py -q`

Conclusion:
- there is now direct regression coverage for this episode-threshold policy boundary

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. The episode-type threshold table should be treated as active validation policy.

2. The current overlap rule should also be treated as intentional policy:
- strongest positive only
- strongest negative only
- additive only across sign boundary

3. This is not a low-risk cleanup target.
Changing it would alter pass/fail pressure across opening, transition, and finale episodes.

### Safe operating rule from this audit

Do:
- keep the current episode-type adjustment table
- keep the current overlap rule unless policy owners explicitly want different stacking
- preserve the new direct regression tests

Do not:
- casually sum all positive adjustments
- flatten opening/finale bias into a single generic threshold
- treat this area as mere magic-number cleanup

### Recommended next actions

1. Keep this item in the `policy boundary` bucket.
2. If retuning is ever needed, decide separately:
   - opening pressure
   - transition relaxation
   - arc finale pressure
   - volume finale pressure
   - overlap stacking policy
3. Any retune should update tests first or in the same patch.

### Audit result

- runtime code change: not needed
- regression hardening: completed
- documentation conclusion: episode-type adaptive-threshold behavior is intentional policy semantics
