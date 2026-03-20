# BaseAgent Key Exhaustion Operator Signal 3-Pass Audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/base-agent-key-exhaustion-operator-signal-3pass-audit.md`
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
Scope:
- confirm whether key-rotation exhaustion still lacks explicit operator signal
- apply the narrowest runtime-visible fix
- verify no fallback regression

---

## Pass 1. Live Issue Restatement

The live issue was real.

`BaseAgent.ask()` checked `_key_rotation_pending` and called `_try_rotate_key()`.
If rotation could not continue, `_try_rotate_key()` returned `None` and `ask()` simply continued.

That hid three different operator-relevant states:
- only one key configured
- all configured keys already exhausted
- rotation temporarily blocked by cooldown

The most important missing signal was:
- all keys already exhausted, but the system kept proceeding without a direct operator-facing warning

---

## Pass 2. Applied Fix

The fix stayed narrow.

1. `_try_rotate_key()` now returns `(new_client, reason)`
- success: `(client, None)`
- failure: `(None, reason)`

2. `ask()` now surfaces rotation-unavailable reasons
- `single_key_only`
- `all_keys_exhausted`
- `rotation_cooldown`
- `client_create_failed`

3. operator-visible signaling was added
- warning for real exhaustion/failure states
- informational signal for cooldown

This does not change model fallback policy.
It only makes key-rotation failure states explicit to operators.

---

## Pass 3. Verification and Outcome

New regressions:
- `tests/test_base_agent.py`
  - `_try_rotate_key()` reports `all_keys_exhausted`
  - `ask()` surfaces the exhaustion reason through operator logging

Validation run:
- `python -m pytest tests/test_base_agent.py -k "HandleApiError or KeyRotationSignal" -q` → `4 passed`
- `python -m pytest tests/test_sweep18.py -k "quota_fallback" -q` → `1 passed`
- `python -m pytest tests/test_base_agent.py -q` → `78 passed`

Conclusion:
- key-rotation exhaustion is no longer silent at the operator layer
- the bounded fallback behavior remains intact
- this bounded high-ROI item is complete

Remaining bounded candidates after this are weaker than the items already completed.
