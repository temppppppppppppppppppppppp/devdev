# Exception Registry Harness

Date: 2026-03-14
Status: active
Applies To: explicit operational exceptions, allowlists, bootstrap-only fallbacks, and deferred violations
Template: `docs/implementation/execution-exception-template.md`

## 1. Purpose
- Make exceptions explicit, time-bounded, and reviewable.
- Prevent "just this once" process drift from becoming permanent policy.

## 2. When To Use
Use this harness when:
- a raw `print`, fallback path, or bypass is temporarily allowed
- a queue rule is intentionally deferred
- a validator warning is accepted for a bounded reason
- a bootstrap or recovery exception must remain during migration

## 3. Required Fields
- exception id
- topic
- rationale
- owner
- introduced date
- review trigger or expiration
- removal condition

## 4. Path Rule
- exception entries should be saved canonically in `docs/YYYY-MM-DD/`
- exceptions are not temp queue artifacts

## 5. Guardrails
- Do not allow silent exceptions.
- Do not create open-ended exceptions without a review trigger.
- Do not treat an exception record as a substitute for fixing the issue.
