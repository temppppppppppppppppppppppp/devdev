# Stage Pipeline Process Integrity Aggregate Execution Roadmap

Date: 2026-03-17
Status: active
Canonical Path: `docs/2026-03-17/stage-pipeline-process-integrity-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Queue Snapshot:
- `docs/temp/stage-pipeline-lane1-cw-context-architecture-execution-ssot.md`
- `docs/temp/stage-pipeline-lane2-director-gate-semantics-execution-ssot.md`
- `docs/temp/stage-pipeline-lane3-repair-retry-architecture-execution-ssot.md`
Confidence After 3-Pass Audit: `96%`

## 1. Purpose
- open one bounded execution queue from the 2026-03-17 Stage pipeline process-integrity survey
- govern exactly three execution-ready lanes:
  - CW context architecture
  - Director gate semantics and prompt austerity
  - PASS_WITH_FIX and retry architecture
- serve as the only roadmap with SSOT authority for this active bundle

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `lane-1-cw-context-architecture` | `docs/2026-03-17/stage-pipeline-lane1-cw-context-architecture-execution-ssot.md` | `docs/temp/stage-pipeline-lane1-cw-context-architecture-execution-ssot.md` | pending | upstream context substrate for all later lanes |
| `lane-2-director-gate-semantics` | `docs/2026-03-17/stage-pipeline-lane2-director-gate-semantics-execution-ssot.md` | `docs/temp/stage-pipeline-lane2-director-gate-semantics-execution-ssot.md` | pending | depends on cleaner context ranking and feeds lane 3 semantics |
| `lane-3-repair-retry-architecture` | `docs/2026-03-17/stage-pipeline-lane3-repair-retry-architecture-execution-ssot.md` | `docs/temp/stage-pipeline-lane3-repair-retry-architecture-execution-ssot.md` | pending | retry and PASS_WITH_FIX lane; best started after lane 2 semantics stabilize |

## 3. Dependency Graph
- `lane-1-cw-context-architecture -> lane-2-director-gate-semantics`
- `lane-2-director-gate-semantics -> lane-3-repair-retry-architecture`
- shared substrate:
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_interview_round.py`
  - Stage 4 prompt composition and authority boundaries
- merge opportunities:
  - lane 2 and lane 3 can share later telemetry work, but they should not be merged before semantic boundaries settle

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`

1. `lane-1-cw-context-architecture`
2. `lane-2-director-gate-semantics`
3. `lane-3-repair-retry-architecture`

## 5. Per-Item Plan

### lane-1-cw-context-architecture
- goal:
  - protect CW first-draft quality by ranking truth and retrieval above bulky advisory material
- prerequisites:
  - revalidate current `stage4_context_builder.py` and `context_advisor.py` behavior before patching
- execution notes:
  - start with writer `work_focus` planner input symmetry and tier separation
  - do not mix Director prompt austerity work into this item
- completion signal:
  - Tier 0/1/2 composition is live and writer retrieval planning accepts `work_focus`
- temp cleanup action:
  - remove the lane 1 temp mirror after closure and mark status completed

### lane-2-director-gate-semantics
- goal:
  - separate Director decision core from reference appendix and clean up verdict semantics
- prerequisites:
  - lane 1 closure or a fresh revalidation confirming lane 1 changes are unnecessary blockers
- execution notes:
  - prioritize semantic split and prompt de-duplication before broader logging or dashboard work
- completion signal:
  - Director primary judgment, final outcome, gate basis, and advisory role are meaningfully separated
- temp cleanup action:
  - remove the lane 2 temp mirror after closure and mark status completed

### lane-3-repair-retry-architecture
- goal:
  - narrow PASS_WITH_FIX and make retry budget behavior legible
- prerequisites:
  - lane 2 semantic split should be stable enough to avoid reworking repair contracts twice
- execution notes:
  - start with local-repair eligibility and Fix Pack shape before deeper policy automation
- completion signal:
  - PASS_WITH_FIX is a strict local-repair contract and retry budgets are represented coherently
- temp cleanup action:
  - remove the lane 3 temp mirror after closure and mark status completed

## 6. Shared Risks and Side-Effects
- shared write paths:
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/domain/agents/director_ensemble.py`
  - `modules/domain/agents/chief_writer.py`
- shared DB/schema touchpoints:
  - no schema work is planned, but runtime summaries and saved traces may change shape
- shared logs/UI surfaces:
  - operator-facing prompt summaries, verdict traces, retry traces, bridge quality payloads
- rollback/recovery concerns:
  - each lane can perturb Stage 4 judgment behavior; strict per-lane validation is required before advancing the queue
- queue collision or ordering risks:
  - lane 3 started too early could cement retry semantics that lane 2 later redefines

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `lane-1-cw-context-architecture` | pending | 2026-03-17 | none |
| `lane-2-director-gate-semantics` | pending | 2026-03-17 | waits on lane 1 substrate or a fresh non-blocking validity gate |
| `lane-3-repair-retry-architecture` | pending | 2026-03-17 | waits on lane 2 semantics |

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- remove `docs/temp/queue-state.json` if present
- leave `docs/temp/README.md`
