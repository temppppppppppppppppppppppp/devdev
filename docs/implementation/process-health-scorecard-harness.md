# Process Health Scorecard Harness

Date: 2026-03-14
Status: active
Applies To: periodic process checks, pre-realization readiness, and closure confidence reporting
Template: `docs/implementation/process-health-scorecard-template.md`
Automation:
- `python scripts/populate_process_health_scorecard.py`

## 1. Purpose
- Provide a compact operator-readable summary of process health.
- Make governance quality visible beyond individual docs.

## 2. When To Use
Use this harness when:
- the temp queue has active items
- the user asks for a higher-rigor operating picture
- a large realization pass is about to begin
- a closure decision needs broader confidence context

## 3. Suggested Dimensions
- governance alignment
- queue integrity
- canonical/mirror sync
- evidence freshness
- side-effect coverage
- exception debt
- validator status
- closure readiness

## 4. Output Rule
- scorecards are canonical docs in `docs/YYYY-MM-DD/`
- they may be referenced from execution docs and closure notes
- they are not temp mirrors

## 5. Guardrails
- Do not fake precision; `amber` is better than a dishonest `green`.
- Do not use the scorecard to hide concrete findings that belong in execution docs.
