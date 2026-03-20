## Preflight Hollow Previous-Arcs Input Gap 3-Pass Audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/preflight-hollow-prev-arcs-input-gap-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `same working session; dirty tree already in progress`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `bounded follow-up within same remediation stream`
Source Governing Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Live Code Basis:
- `modules/core/stage2_preflight.py`
- `modules/domain/agents/preflight_checker.py`
- `tests/test_stage2_preflight.py`
Scope:
- bounded input hygiene gap before `PreflightChecker.analyze()`
- non-goal: redesign Stage 2 retry policy

---

## Pass 1. Question

Should Stage 2 preflight treat previous Arcs with blank or missing `tactical_doc` as valid preflight evidence?

Answer: no.

Those inputs are too hollow to serve as real preflight context.

---

## Pass 2. Live Finding

Before this patch:

- `Stage2Preflight` passed `all_refined_arcs` directly into `PreflightChecker.analyze()`
- blank or missing `tactical_doc` values were not filtered first
- `PreflightChecker` would then build context from structurally present but semantically hollow Arcs

That could make preflight constraints look healthier than the actual evidence warranted.

---

## Pass 3. Resolution

Resolution applied:

- `modules/core/stage2_preflight.py`
  - skip hollow previous Arcs before calling `PreflightChecker.analyze()`
  - define hollow as:
    - non-dict arc payload
    - blank/missing `tactical_doc`
  - emit audit/log signal when skips occur
  - attach `_input_hygiene` metadata to cached preflight result
  - use last usable Arc, not last raw Arc, for injury carry-over correction
- `tests/test_stage2_preflight.py`
  - added regression for hollow previous-arc skipping and audit emission

Validation run:

- `python -m pytest tests/test_stage2_preflight.py -k "hollow_previous_arcs_are_skipped_before_preflight_analysis or recent_patterns_collected or stage3_reverse_feedback_injected_after_three_stage3_failures" -q`
- `python -m pytest tests/test_pass_with_fix.py -k "pwf_s2_patch_history_injected_to_story_context or finalizer_pass_with_fix_bypasses_quality_gate" -q`

Result:

- hollow preflight input gap: fixed
- behavior remains fail-soft
- skip facts are now observable through log and audit metadata
