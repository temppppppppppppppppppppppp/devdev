# Evidence Manifest Template

Use this template when a survey or execution topic has multiple evidence artifacts that should be indexed explicitly.

---

# <topic> Evidence Manifest

Date: YYYY-MM-DD
Status: draft | active | final
Topic: `<topic>`
Related Survey Docs:
- `docs/YYYY-MM-DD/<topic>-3pass-audit.md`
Related Execution Docs:
- `docs/YYYY-MM-DD/<topic>-execution-ssot.md`

## 1. Summary
- evidence scope:
- freshness note:
- known gaps:

## 2. Artifact Index

| Artifact | Type | Acquired By | Freshness | Reuse | Notes |
| --- | --- | --- | --- | --- | --- |
| `docs/YYYY-MM-DD/<topic>-evidence.txt` | inventory | `rg` / AST / test | fresh | survey + execution | `<note>` |
| `docs/YYYY-MM-DD/<topic>-side-effects.json` | side-effect map | manual + code read | fresh | survey + closure | `<note>` |

## 3. Limitations
- `<limitation>`
- `<limitation>`

---

Before final save:
- complete the document 3-pass audit
- keep artifact paths canonical and stable
