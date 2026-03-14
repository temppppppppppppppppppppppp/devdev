# Execution Closure Template

Use this template when a realized execution SSOT needs a canonical closure record or closure section.

---

# <topic> Execution Closure Note

Date: YYYY-MM-DD
Status: closed | partially_realized | blocked
Canonical Execution Path: `docs/YYYY-MM-DD/<topic>-execution-ssot.md`
Temp Mirror Path: `docs/temp/<topic>-execution-ssot.md` | `none`
Canonical Roadmap Path: `docs/YYYY-MM-DD/<topic>-execution-roadmap.md` | `none`
Temp Roadmap Path: `docs/temp/execution-roadmap.md` | `none`
Verification Artifacts:
- `docs/YYYY-MM-DD/<topic>-verification.md`
- `<test output or evidence path>`

## 1. Realized Scope
- What landed.
- What was intentionally left out.

## 2. Verification Summary
- tests run:
- runtime checks:
- unverified areas:

## 3. Residual Risks
- `<risk>`
- `<risk>`

## 4. Follow-Up
- next queue item:
- next survey needed:
- owner or trigger:

## 5. Temp Cleanup
- execution SSOT mirror removed: yes | no
- roadmap mirror removed: yes | no
- queue-state refreshed or removed: yes | no

---

Before final save:
- complete the document 3-pass audit
- update the canonical execution SSOT first
- run the ops validator before deleting temp queue artifacts
