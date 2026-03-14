# Execution SSOT Template

Use this template for canonical execution SSOT documents saved to `docs/YYYY-MM-DD/`.

---

# <topic> Execution SSOT

Date: YYYY-MM-DD
Status: draft | active | execution-ready | closed
Canonical Path: `docs/YYYY-MM-DD/<topic>-execution-ssot.md`
Temp Mirror Path: `docs/temp/<topic>-execution-ssot.md`
Source Survey Docs:
- `docs/YYYY-MM-DD/<topic>-full-survey-audit-order.md`
- `docs/YYYY-MM-DD/<topic>-3pass-audit.md`
Evidence Artifacts:
- `docs/YYYY-MM-DD/<topic>-evidence.txt`
- `docs/YYYY-MM-DD/<topic>-side-effects.txt`
Side-Effect Coverage: covered | partial | not-applicable

## 1. Intent
- What this execution document is trying to realize.
- Why this is being executed now.

## 2. Baseline Facts
- Stable facts derived from the survey.
- Counts, hotspots, and key constraints.

## 3. Scope
Included:
- `<path or surface>`

Excluded:
- `<path or surface>`

## 4. Pass 1. Inventory Summary
- Key inventory totals
- Main hotspots
- Runtime vs script/test separation if relevant

## 5. Pass 2. Semantic Classification
- Class A:
- Class B:
- Class C:

## 6. Side-Effect Map
- file writes / artifacts:
- DB / schema / transaction boundaries:
- JSONL / log / audit sinks:
- console / UI / operator output:
- rollback / recovery / retry:
- cache / global state:
- bootstrap fallback / config-env mutation:

If a category is not applicable, say so explicitly.

## 7. Realization Architecture
- substrate requirements
- contracts or interfaces
- queue or dependency constraints

## 8. Execution Tranches
1. `<tranche>`
2. `<tranche>`
3. `<tranche>`

## 9. Acceptance Criteria
- `<criterion>`
- `<criterion>`

## 10. Verification Plan
- `<test or validation>`
- `<test or validation>`

## 11. Guardrails
- `<guardrail>`
- `<guardrail>`

## 12. Temp Queue Notes
- temp status: pending | in_progress | completed
- cleanup condition:
- roadmap dependency:

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

---

Before final save:
- run the document 3-pass audit
- save the canonical file first
- then refresh the temp mirror copy
- run the ops validator if a temp mirror was created or refreshed

Before starting implementation from this document:
- re-run the document 3-pass audit against the current workspace state
- confirm the document still reflects live code and dependencies
- confirm estimated confidence is at least 95%
