# Max-Retention / Max-Display / Pre-Rerun Aggregate Execution Roadmap

Date: 2026-03-23
Status: active
Canonical Path: `docs/2026-03-23/max-retention-observability-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `a3b9a286`
- Baseline Dirty Summary: `dirty: active 2026-03-23 docs, runtime/db edits, two active Q8 items, and one closed Q3/Q4/Q6 item`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Queue Snapshot:
- `docs/temp/db-logging-integrity-post-audit-execution-ssot.md`
- `docs/temp/console-log-max-display-post-audit-execution-ssot.md`

## 1. Purpose
- Provide the single active SSOT roadmap for the current pre-rerun bundle.
- Govern execution order between:
  - the DB max-retention item
  - the console max-display parity item
  - the already-realized Q3/Q4/Q6 pre-rerun correctness item
- Keep shared Stage 2/3/4 operator, verdict, and persistence work from colliding in temp queue handling.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `db-logging-integrity-post-audit-execution-ssot` | `docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md` | `docs/temp/db-logging-integrity-post-audit-execution-ssot.md` | in_progress | max-retention DB wave partly realized; raw advisory payload + contract alignment landed, live closure still pending |
| `console-log-max-display-post-audit-execution-ssot` | `docs/2026-03-23/console-log-max-display-post-audit-execution-ssot.md` | `docs/temp/console-log-max-display-post-audit-execution-ssot.md` | pending | max-display / no-truncation operator surface wave derived from console audit |
| `q3-q4-q6-pre-rerun-fixes-execution-ssot` | `docs/2026-03-23/q3-q4-q6-pre-rerun-fixes-execution-ssot.md` | removed after closure | completed | realized by Opus, audited by Codex, and closed; one `ep_type` forwarding drift corrected during audit |

## 3. Dependency Graph
- active dependency: `db-logging-integrity-post-audit-execution-ssot -> console-log-max-display-post-audit-execution-ssot`
- completed ahead-of-queue:
  - `q3-q4-q6-pre-rerun-fixes-execution-ssot`
- shared substrate:
  - `modules/core/stage4_interview_round.py`
  - `modules/domain/agents/director_ensemble.py`
  - `modules/core/stage2_finalizer.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_reject_runtime.py`
  - `modules/core/vec_memory.py`
  - `modules/core/stage4_context_builder.py`
- merge opportunities:
  - one shared Stage 3/4 fresh live lane after all three items land
  - one shared operator-transcript vs DB-parity audit before final closure

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`

1. `db-logging-integrity-post-audit-execution-ssot`
2. `console-log-max-display-post-audit-execution-ssot`
3. closed: `q3-q4-q6-pre-rerun-fixes-execution-ssot`

## 5. Per-Item Plan

### db-logging-integrity-post-audit-execution-ssot
- goal:
  - finish the max-retention DB wave and verify that raw adjunct rows and expanded Stage 4 detail fields populate in live execution
- prerequisites:
  - current code changes remain green
  - fresh Stage 3/4 lane available for validation
- execution notes:
  - do not reopen cleanup or pruning
  - focus on closure evidence for `director_thinking`, `advisory_warnings_raw`, and Stage 4 detail columns
- completion signal:
  - fresh live lane shows raw rows and detail columns populated as designed
  - Codex closes the execution SSOT
- temp cleanup action:
  - remove `docs/temp/db-logging-integrity-post-audit-execution-ssot.md` immediately after closure

### console-log-max-display-post-audit-execution-ssot
- goal:
  - eliminate operator-visible truncation and detail omission on decision-bearing Stage 2/3/4 surfaces
- prerequisites:
  - DB retention item is either closed or stable enough that console-vs-DB parity targets are known
- execution notes:
  - preserve verdict logic and score math
  - surface provenance, detail, and full rationale rather than changing policy
  - treat already-landed `director_ensemble.py` Stage 4 max-display / provenance lines from the closed Q3/Q4/Q6 item as baseline, not remaining scope
- completion signal:
  - one Stage 3 lane and one Stage 4 lane show full operator-visible rationale/advisory/provenance without silent truncation
  - Codex closes the execution SSOT
- temp cleanup action:
  - remove `docs/temp/console-log-max-display-post-audit-execution-ssot.md` immediately after closure

### q3-q4-q6-pre-rerun-fixes-execution-ssot
- goal:
  - realize the bounded pre-rerun fixes for verdict correctness, feedback fidelity, and retrieval silent degradation
- prerequisites:
  - completed
- execution notes:
  - realized by Opus and audited by Codex
  - `ep_type` forwarding drift was corrected during closure audit
  - a small subset of `director_ensemble.py` console max-display work landed here and is now treated as baseline by the console item
- completion signal:
  - achieved
- temp cleanup action:
  - completed

## 6. Shared Risks and Side-Effects
- shared write paths:
  - Stage 4 interview round persistence and operator surfacing
  - director ensemble operator output
  - Stage 2 finalizer rationale output
  - Stage 3 operator output and parity checks
- shared DB/schema touchpoints:
  - `stage_attempts`
  - `director_selections`
  - `attempt_raw_rationale`
- shared logs/UI surfaces:
  - Rich operator console
  - standard logging sinks
- shared verdict/control surfaces:
  - adaptive decision path
  - Stage 4 reject/retry feedback path
  - retrieval fallback observability path
- rollback/recovery concerns:
  - avoid any verdict/routing/retry behavior drift while expanding evidence and display
- queue collision or ordering risks:
  - all three items touch the same Stage 2/3/4 families
  - keep them serialized under this roadmap rather than parallelized

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `db-logging-integrity-post-audit-execution-ssot` | in_progress | 2026-03-23 | fresh Stage 3/4 live closure evidence not yet captured |
| `console-log-max-display-post-audit-execution-ssot` | pending | 2026-03-23 | waits on stable DB-retention parity baseline |
| `q3-q4-q6-pre-rerun-fixes-execution-ssot` | completed | 2026-03-23 | none |

Allowed statuses:
- pending
- in_progress
- completed
- blocked

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when the two remaining active items are completed, remove `docs/temp/execution-roadmap.md`
- refresh `docs/temp/queue-state.json` through `python scripts/sync_temp_queue_state.py`
- leave `docs/temp/README.md`

## 9. 3-Pass Audit Record
- Pass 1: confirmed the queue originally contained three pre-rerun execution items
- Pass 2: updated the roadmap after early realization of the Q3/Q4/Q6 item
- Pass 3: rechecked active queue count, closed-item lineage, and residual overlap notes for the console item

## 10. Confidence
- Estimated confidence: 97%
- Residual uncertainty:
  - the DB item may close quickly if live Stage 3/4 evidence is collected immediately
  - the console item may still adjust formatting choices during implementation Pass 1
  - the two remaining active items still need fresh live closure evidence
