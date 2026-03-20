# Blueprint Ensemble `last_error_type` Race 3-Pass Audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/blueprint-ensemble-last-error-type-race-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `same working session; bounded remediation under dirty tree`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `same working session; no governing-doc reset`
Source Governing Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/opus-remaining-high-roi-screening-3pass-audit.md`
Evidence Basis:
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `tests/test_tier4_ensemble_caching.py`
- `tests/test_blueprint_patch_mode.py`
Scope:
- confirm whether OPUS-derived `last_error_type` race is still live
- apply the narrowest safe fix
- verify caller fast-fail semantics after the fix

---

## Pass 1. Live Issue Restatement

The live problem was real.

- `BlueprintEnsembleGenerator.generate_ensemble()` fanned out worker threads through one shared ensemble/base-agent instance.
- worker failures wrote only one shared `self.last_error_type`
- `ThreePhaseBlueprintGenerator.generate()` later read only that single field for `schema_incompatible` fast-fail

That meant the final classification was vulnerable to last-writer-wins behavior.

There was also a second loss path:

- `_generate_single()` returned plain `None` for non-dict or missing-field failures
- those failures could collapse to `unknown` even when they were effectively schema incompatibility

---

## Pass 2. Applied Fix

The fix stayed narrow and did not change Stage 3 routing policy.

1. `BlueprintEnsembleGenerator`
- added `last_error_types`
- worker failures now surface local error types instead of relying on a shared mutable slot
- `generate_ensemble()` aggregates all worker error types after fan-out completes
- `last_error_type` is now derived once from the aggregated bundle, with `schema_incompatible` taking priority
- non-dict / missing required field failures are now classified as `schema_incompatible`

2. `ThreePhaseBlueprintGenerator`
- no-Blueprint failure handling now prefers `last_error_types`
- if any worker reported `schema_incompatible`, the caller fast-fails on that reason even if the stale single-field value differs

This is a bounded correctness fix, not a policy rewrite.

---

## Pass 3. Verification and Outcome

Targeted regressions added:
- `tests/test_tier4_ensemble_caching.py`
  - worker error bundle aggregation
  - `schema_incompatible` priority over other worker failures
- `tests/test_blueprint_patch_mode.py`
  - caller prefers aggregated worker bundle over stale single `last_error_type`

Validation run:
- `python -m pytest tests/test_tier4_ensemble_caching.py -k "blueprint_ensemble" -q` → `8 passed`
- `python -m pytest tests/test_blueprint_patch_mode.py -k "schema_incompatible" -q` → `3 passed`
- `python -m pytest tests/test_agent_perf_timer.py -k "BlueprintEnsemble" -q` → `1 passed`
- `python -m pytest tests/test_blueprint_patch_mode.py -q` → `17 passed`

Conclusion:
- the race is closed for the bounded Stage 3 caller contract
- `schema_incompatible` fast-fail is now based on aggregated worker evidence
- this screening item is complete

Next high-ROI candidate:
- ambiguous `429` classification in `BaseAgent`
