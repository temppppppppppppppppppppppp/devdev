# Evidence Triangulation Contract

Date: 2026-03-14
Status: active
Applies To: high-rigor system-track surveys and execution-doc synthesis

## 1. Purpose
- Raise the quality bar for claims that drive execution docs or severity decisions.
- Reduce the chance that one misleading grep or stale note becomes policy.

## 2. Evidence Classes

| Class | Source Type | Example |
| --- | --- | --- |
| A | direct live-code reading | `main_a.py`, `modules/core/logger.py` |
| B | structured inventory or search evidence | AST inventory, `rg` counts, path census |
| C | operational or verification surface | tests, canary helpers, bridge contracts, runner scripts |
| D | config or contract authority | prompt YAML, IPC/API/event contracts, config files |
| E | historical or governance lineage | prior survey doc, existing execution SSOT, harness contract |

## 3. Claim Requirements
- descriptive claims may use one strong primary source
- hotspot or count claims should use class A or D plus class B
- cross-cut behavior claims should use at least two classes
- critical architecture or severity claims should use at least three classes when feasible

Recommended minimums:
- `P1` claim: A + B + one of C/D/E
- "this is the authoritative entry" claim: A + D, with C preferred if runtime helpers exist
- "this side-effect is durable or non-durable" claim: A + B, with C preferred

## 4. Contradiction Handling
If evidence classes disagree:
- record the contradiction explicitly
- do not silently choose the preferred answer
- cap confidence until the contradiction is explained or bounded

## 5. Confidence Caps
- unresolved contradiction on a critical claim caps confidence below 95
- single-sourced `P1` claim caps confidence below 90
- count claims without structured evidence should be downgraded to approximate statements
