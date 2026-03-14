# Execution Roadmap Template

Use this template when two or more execution SSOT mirror copies exist in `docs/temp/`.

For codebase-global deep survey bundles, this roadmap is the single SSOT roadmap for the bundle.

---

# <topic> Aggregate Execution Roadmap

Date: YYYY-MM-DD
Status: draft | active | closed
Canonical Path: `docs/YYYY-MM-DD/<topic>-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Queue Snapshot:
- `docs/temp/<item-a>-execution-ssot.md`
- `docs/temp/<item-b>-execution-ssot.md`

## 1. Purpose
- Why an aggregate roadmap is needed.
- Which execution queue items it governs.
- Why this is the only roadmap with SSOT authority for the active bundle.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `<item-a>` | `docs/YYYY-MM-DD/...` | `docs/temp/...` | pending | `<note>` |
| `<item-b>` | `docs/YYYY-MM-DD/...` | `docs/temp/...` | pending | `<note>` |

## 3. Dependency Graph
- `<item-a> -> <item-b>`
- shared substrate:
- merge opportunities:

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`

1. `<item>`
2. `<item>`
3. `<item>`

## 5. Per-Item Plan

### <item-a>
- goal:
- prerequisites:
- execution notes:
- completion signal:
- temp cleanup action:

### <item-b>
- goal:
- prerequisites:
- execution notes:
- completion signal:
- temp cleanup action:

## 6. Shared Risks and Side-Effects
- shared write paths:
- shared DB/schema touchpoints:
- shared logs/UI surfaces:
- rollback/recovery concerns:
- queue collision or ordering risks:

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `<item-a>` | pending | YYYY-MM-DD | none |
| `<item-b>` | pending | YYYY-MM-DD | none |

Allowed statuses:
- pending
- in_progress
- completed
- blocked

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- remove `docs/temp/queue-state.json` if present
- leave `docs/temp/README.md`

---

Before final save:
- run the document 3-pass audit
- save the canonical roadmap first
- then refresh `docs/temp/execution-roadmap.md`
- run the ops validator if the temp roadmap mirror was created or refreshed

Before starting implementation from this roadmap:
- re-run the document 3-pass audit against the current workspace state
- confirm the ordering, dependencies, and controlled execution SSOT set are still valid
- confirm no parallel SSOT roadmap exists for the same active bundle
- confirm estimated confidence is at least 95%
