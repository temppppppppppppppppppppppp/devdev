## QualityDashboard Persistence Operator Signal 3-Pass Audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/quality-dashboard-persistence-operator-signal-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `same working session; dirty tree already in progress`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `bounded follow-up within same remediation stream`
Source Governing Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/opus-remaining-high-roi-screening-3pass-audit.md`
Live Code Basis:
- `modules/core/quality_dashboard.py`
- `modules/api/bridge_server.py`
- `tests/test_quality_regression.py`
- `tests/test_bridge_quality_summary.py`
Scope:
- bounded operator-signal follow-up for quality metric persistence failure
- non-goal: redesign quality metric storage

---

## Pass 1. Question

When `QualityDashboard` fails to append `quality_metrics.jsonl`, is that failure operator-visible enough?

Before this patch, the answer was no.

---

## Pass 2. Live Finding

`QualityDashboard._save_record()` only emitted a warning log on file-write failure.

That meant:

- quality metrics could fail to persist
- the failure might never surface into the existing runtime-health path
- dashboard operators could miss the storage problem unless they were watching raw logs

This is a bounded operator-signal gap, not a storage-architecture rewrite.

---

## Pass 3. Resolution

Resolution applied:

- `modules/core/quality_dashboard.py`
  - persistence failure now records an in-memory `persistence_health` summary
  - best-effort soft-failure event is appended to `logs/soft_failures.jsonl`
  - component/operation used:
    - `quality_dashboard`
    - `save_record`
- `tests/test_quality_regression.py`
  - added direct regression for save failure -> `persistence_health` + `soft_failures.jsonl`
- `tests/test_bridge_quality_summary.py`
  - added endpoint regression proving `runtime_health` surfaces `quality_dashboard.save_record`

Validation run:

- `python -m pytest tests/test_quality_regression.py -k "PersistenceHealth or RetrievalObservationSummary" -q`
- `python -m pytest tests/test_bridge_quality_summary.py -k "quality_dashboard_persistence_failure or quality_signal_snapshot" -q`

Result:

- bounded operator-signal gap: fixed
- no storage policy change
- existing runtime-health channel now sees this failure class
