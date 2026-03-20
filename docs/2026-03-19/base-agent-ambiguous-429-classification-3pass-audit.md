# BaseAgent Ambiguous `429` Classification 3-Pass Audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/base-agent-ambiguous-429-classification-3pass-audit.md`
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
- `tests/test_base_agent.py`
- `tests/test_sweep18.py`
- `tests/test_edge_cases.py`
Scope:
- re-check live ambiguous `429` handling in `BaseAgent`
- decide whether it is a narrow runtime bugfix or a policy boundary
- patch and verify only the classification branch

---

## Pass 1. Live Issue Restatement

The live issue was real.

Before this fix:
- explicit `429 + rate/limit` went to the same-model rate-limit backoff lane
- `resource_exhausted` and explicit `quota` markers went to the quota/fallback lane
- bare `429` with no stronger marker was treated as rate-limit by default

That default was too optimistic.

For a bare `429`, the system had no reliable proof that waiting on the same model was correct.
In practice, the safer bounded behavior is:

- keep explicit rate-limit on backoff/retry
- send ambiguous bare `429` to the fallback/quota lane

---

## Pass 2. Applied Fix

The fix is narrow and local to `_handle_api_error()`.

1. explicit quota markers remain quota/fallback
- `resource_exhausted`
- `quota`

2. explicit rate-limit remains same-model backoff
- `429` plus clear rate/limit wording
- `too many requests` is also treated as explicit rate-limit wording

3. bare ambiguous `429` now prefers immediate fallback
- it no longer enters the same-model backoff loop
- it is treated as quota-like uncertainty and moves to the safer fallback lane

This does not change the higher-level `AgentErrorType` contract.
It only changes which recovery lane a bare `429` takes.

---

## Pass 3. Verification and Outcome

New regressions:
- `tests/test_base_agent.py`
  - ambiguous bare `429` uses immediate fallback
  - explicit `429 rate limit` still uses backoff/retry

Validation run:
- `python -m pytest tests/test_base_agent.py -k "ClassifyError or HandleApiError" -q` → `9 passed`
- `python -m pytest tests/test_sweep18.py -k "quota_fallback" -q` → `1 passed`
- `python -m pytest tests/test_edge_cases.py -k "quota_exceeded_handling" -q` → `1 passed`
- `python -m pytest tests/test_base_agent.py -q` → `76 passed`

Conclusion:
- ambiguous bare `429` no longer burns same-model wait cycles by default
- explicit rate-limit behavior is preserved
- this bounded high-ROI item is complete

Next bounded screening candidate:
- API-key exhaustion with weak explicit operator signal
