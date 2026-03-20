## PASS_WITH_WARNING Verdict Enum Drift 3-Pass Audit

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/pass-with-warning-verdict-enum-drift-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `same working session; dirty tree already in progress`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `bounded follow-up within same remediation stream`
Source Governing Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
- `docs/2026-03-19/opus-remaining-high-roi-screening-3pass-audit.md`
Live Code Basis:
- `modules/core/response_schemas.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/db_manager.py`
- `tests/test_llm_schema.py`
Scope:
- narrow schema/runtime contract drift around `PASS_WITH_WARNING`
- non-goal: change Stage 3 fallback semantics

---

## Pass 1. Question

Is `PASS_WITH_WARNING` a real live verdict, or merely an internal marker?

If it is live, the response schemas should admit it.

---

## Pass 2. Live Finding

Live runtime already treats `PASS_WITH_WARNING` as a real verdict:

- `three_phase_blueprint_generator.py` can emit it as final Stage 3 result
- `db_manager.py` already includes it in success-side verdict handling

But `response_schemas.py` still constrained Director/Strategic decision enums to:

- `PASS`
- `PASS_WITH_FIX`
- `REJECT`

That is a real schema drift.

---

## Pass 3. Resolution

Resolution applied:

- `modules/core/response_schemas.py`
  - added `PASS_WITH_WARNING` to `DIRECTOR_AUDIT_SCHEMA`
  - added `PASS_WITH_WARNING` to `STRATEGIC_AUDIT_SCHEMA`
- `tests/test_llm_schema.py`
  - added schema-spec regression tests for both enums

Validation run:

- `python -m pytest tests/test_llm_schema.py -q`
- `python -m pytest tests/test_pass_with_fix.py -k "schema_contracts_live or Stage2PassWithFix" -q`
- `python -m pytest tests/test_director_modules.py -k "PASS_WITH_WARNING" -q`
- `python scripts/check_utf8_hygiene.py modules/core/response_schemas.py tests/test_llm_schema.py`
- `git diff --check -- modules/core/response_schemas.py tests/test_llm_schema.py`

Result:

- verdict enum drift: fixed
- Stage 3/DB/schema contract is now aligned on `PASS_WITH_WARNING`
