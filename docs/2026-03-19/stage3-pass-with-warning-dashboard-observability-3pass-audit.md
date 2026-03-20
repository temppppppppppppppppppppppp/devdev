## Stage3 PASS_WITH_WARNING Dashboard Observability 3-Pass Audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/stage3-pass-with-warning-dashboard-observability-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `same working session; dirty tree already in progress`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `bounded follow-up within same remediation stream`
Source Governing Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/opus-remaining-high-roi-screening-3pass-audit.md`
Source OPUS Survey Doc:
- `docs/2026-03-18/OPUS/geuldobi-stage23-deepdive-hidden-areas-survey.md`
Live Code Basis:
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/quality_dashboard.py`
- `tests/chaos/test_stage3_metrics.py`
Scope:
- bounded follow-up on Stage 3 degraded-success observability
- non-goal: rewrite Stage 3 fallback semantics

---

## Pass 1. Question

The live Stage 3 fallback policy still allows a previous best Blueprint to return `PASS_WITH_WARNING`.

That semantic choice remains a policy boundary.

The bounded question here is narrower:

- when Stage 3 returns `PASS_WITH_WARNING` with `quality_gate_failed` or `quality_risk`, does the quality dashboard keep that degraded-success signal, or flatten it into a plain `PASS`?

---

## Pass 2. Live Finding

Before this patch:

- `Stage3Orchestrator._handle_success()` recorded Stage 3 success into the quality dashboard as plain `PASS`
- warning fields were emitted as an empty list even when `quality_gate_failed` and `quality_risk` were present
- `QualityDashboard` pass aggregation did not count `PASS_WITH_WARNING` as pass

This meant:

- Stage 3 degraded success was still operationally visible in runtime payloads
- but dashboard-oriented validation history lost the distinction between clean success and warning success

That is an observability defect, not a semantic fallback defect.

---

## Pass 3. Resolution

Resolution applied:

- `modules/core/stage3_orchestrator.py`
  - dashboard record now preserves `decision="PASS_WITH_WARNING"` when that is the final verdict
  - dashboard warning list now carries `quality_gate_failed` and `quality_risk`
  - dashboard payload now includes `quality_signals`
- `modules/core/quality_dashboard.py`
  - pass-rate aggregation now counts `PASS_WITH_WARNING` as pass
- `tests/chaos/test_stage3_metrics.py`
  - added direct regression for degraded-success dashboard recording

Validation run:

- `python -m pytest tests/chaos/test_stage3_metrics.py -q`
- `python -m pytest tests/test_stage3_orchestrator.py -k "quality_risk or stage3_success_logs_episode_summary" -q`
- `python -m pytest tests/test_bridge_quality_summary.py -k "quality_dashboard or proof_status_and_sink_alignment" -q`
- `python -m pytest tests/integration/test_patch_wiring.py -k "handle_success or handle_failure" -q`
- `python scripts/check_utf8_hygiene.py modules/core/stage3_orchestrator.py modules/core/quality_dashboard.py tests/chaos/test_stage3_metrics.py`
- `git diff --check -- modules/core/stage3_orchestrator.py modules/core/quality_dashboard.py tests/chaos/test_stage3_metrics.py`

Result:

- bounded observability issue: fixed
- Stage 3 emergency fallback semantics: unchanged
- future policy question, if reopened later:
  - should Stage 3 emergency fallback still be allowed to return `PASS_WITH_WARNING` at all?
