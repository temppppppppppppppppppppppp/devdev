<!-- [참고자료] -->
# codebase-global-cleanroom-source-only Aggregate Execution Roadmap

Date: 2026-03-15
Status: superseded-by-post-remediation
Successor: `docs/2026-03-15/codebase-global-post-remediation-execution-roadmap.md`
Canonical Path: `docs/2026-03-15/codebase-global-cleanroom-source-only-execution-roadmap.md`
Temp Mirror Path: `none`
Commit State:
- Baseline Commit: `d2982aa2790f5ab81529f1e8d87cf6f6006f13c9`
- Baseline Dirty Summary: `dirty: unrelated investment/style/docs/log artifacts already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Queue Snapshot: `historical cleanroom snapshot only; the temp queue is no longer populated by these items`

## Historical Supersession Notice

- This roadmap is retained as a historical cleanroom queue snapshot only.
- Live queue authority moved first to `docs/2026-03-15/codebase-global-log-evidence-merged-execution-roadmap.md` and then to `docs/2026-03-15/codebase-global-post-remediation-execution-roadmap.md`, which is now closed.
- The pending inventory below is preserved as historical evidence and must not be read as current queue state.

## 1. Purpose
- Govern the action-bearing execution queue created by the clean-room deep global survey.
- Keep one roadmap with SSOT authority for all active execution mirrors.
- Order the bundle so source-text safety lands before desktop/control-plane connectivity hardening, and connectivity hardening lands before prompt unification and persistence boundary hardening.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| source-text hygiene | `docs/2026-03-15/source-text-utf8-hygiene-remediation-execution-ssot.md` | `docs/temp/source-text-utf8-hygiene-remediation-execution-ssot.md` | pending | establishes trustworthy text and lint substrate |
| backend-front/control-plane connectivity | `docs/2026-03-15/backend-front-control-plane-connectivity-remediation-execution-ssot.md` | `docs/temp/backend-front-control-plane-connectivity-remediation-execution-ssot.md` | pending | aligns renderer, preload, Electron main, and bridge semantics for fresh runs |
| runtime/operator surface | `docs/2026-03-15/runtime-operator-surface-unification-remediation-execution-ssot.md` | `docs/temp/runtime-operator-surface-unification-remediation-execution-ssot.md` | pending | centralizes prompt authority across console and wrapper surfaces |
| persistence/observability boundary | `docs/2026-03-15/persistence-observability-boundary-remediation-execution-ssot.md` | `docs/temp/persistence-observability-boundary-remediation-execution-ssot.md` | pending | tightens write ownership and sink boundaries |

## 3. Dependency Graph
- `source-text hygiene -> backend-front/control-plane connectivity -> runtime/operator surface -> persistence/observability boundary`
- shared substrate:
  - touched-file UTF-8 hygiene
  - desktop bridge and prompt contracts
  - sink metadata and regression expectations
- merge opportunities:
  - connectivity and prompt-surface changes can bundle detector-safe text repairs where the same files are touched

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`

1. source-text hygiene
2. backend-front/control-plane connectivity
3. runtime/operator surface
4. persistence/observability boundary

## 5. Per-Item Plan

### source-text hygiene
- goal: remove real corruption from active source and restore detector credibility
- prerequisites: none beyond current survey bundle
- execution notes: keep scope tight to active runtime/control-plane files and the checker
- completion signal: checker catches true corruption without blocking ordinary Korean prompts
- temp cleanup action: remove its temp mirror after closure

### backend-front/control-plane connectivity
- goal: align renderer, preload, Electron main, bridge server, and prompt broker so fresh runs are not gated or desynchronized by transport drift
- prerequisites: source-text lane should land first to avoid re-editing corrupted desktop/control-plane strings
- execution notes: decouple command readiness from websocket state, define reconnect behavior, and make prompt concurrency explicit instead of silently dropping events
- completion signal: run commands do not depend on websocket-open state by construction, reconnect semantics are explicit, and desktop control-plane regression tests cover the newly closed gaps
- temp cleanup action: remove its temp mirror after closure

### runtime/operator surface
- goal: centralize prompt authority across console and wrapper surfaces after transport semantics are stable
- prerequisites: source-text lane and backend-front connectivity lane should land first to avoid re-editing prompt strings and bridge semantics twice
- execution notes: protect non-interactive harnesses while reducing raw prompt duplication
- completion signal: prompt contract is unified and regression tests cover console plus wrapper telemetry without re-opening bridge-state drift
- temp cleanup action: remove its temp mirror after closure

### persistence/observability boundary
- goal: reduce write-authority spread and clarify sink ownership
- prerequisites: prompt/telemetry semantics should already be stabilized
- execution notes: keep schema churn bounded; prefer ownership cleanup and regression tightening
- completion signal: write ownership is more explicit and sink-alignment tests remain green
- temp cleanup action: remove its temp mirror after closure

## 6. Shared Risks and Side-Effects
- shared write paths:
  - source files, tests, and docs across runtime and bridge surfaces
- shared DB/schema touchpoints:
  - primarily the fourth lane; other lanes should avoid opportunistic schema edits
- shared logs/UI surfaces:
  - prompt strings, UI event metadata, bridge error messages, desktop startup warnings
- rollback/recovery concerns:
  - prompt timeout, websocket reconnect, and subprocess control must stay stable while desktop transport is hardened
- queue collision or ordering risks:
  - doing prompt unification before text hygiene and transport hardening would multiply rework
  - persistence refactors before prompt semantics settle could churn UI-event and audit contracts twice

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| source-text hygiene | pending | 2026-03-15 | none |
| backend-front/control-plane connectivity | pending | 2026-03-15 | waits on text hygiene substrate |
| runtime/operator surface | pending | 2026-03-15 | waits on text hygiene and transport stabilization |
| persistence/observability boundary | pending | 2026-03-15 | waits on prompt contract stabilization |

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- remove `docs/temp/queue-state.json` if present
- leave `docs/temp/README.md`
