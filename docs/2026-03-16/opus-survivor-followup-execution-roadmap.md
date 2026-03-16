<!-- [완료] -->
<\!-- [완료] -->
# opus-survivor-followup Aggregate Execution Roadmap

Date: 2026-03-16
Status: closed
Canonical Path: `docs/2026-03-16/opus-survivor-followup-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
- Baseline Dirty Summary: `dirty: wide workspace code/docs changes already present; OPUS memo re-audit and survivor queue promotion in progress`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `all three survivor lanes are completed; the temp queue is exhausted after lane 3 closure`
Queue Snapshot:
- none; queue exhausted after final survivor closure

## 1. Purpose
- Govern the new survivor-only execution queue derived from the OPUS memo bundle.
- Keep one live roadmap with SSOT authority for the promoted survivor lanes after the older post-remediation roadmap closed.
- Ensure excluded or contradicted OPUS items do not re-enter the queue through memo drift.

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| persistence-context authority hardening | `docs/2026-03-16/persistence-context-authority-hardening-execution-ssot.md` | removed after closure | completed | survivor lane for `S0-1`, `X-2`, `TF-BA-02`, `TF-S4CB-02` closed with targeted regression coverage |
| director-feedback decision integrity hardening | `docs/2026-03-16/director-feedback-decision-integrity-hardening-execution-ssot.md` | removed after closure | completed | survivor lane for `TF-FB-01/02`, `TF-DG-01/02` closed with targeted feedback/director regression coverage |
| continuity-history and escalation guardrails | `docs/2026-03-16/continuity-history-and-escalation-guardrails-execution-ssot.md` | removed after closure | completed | survivor lane for `TF-CM-03`, `S3-1/2`, `S4-4/5`, `TF-E3` closed with bounded continuity/history/escalation regression coverage |

## 3. Dependency Graph
- `persistence-context authority hardening -> continuity-history and escalation guardrails`
- shared substrate:
  - persistence and Stage 4 authority seams should be stabilized before broader continuity follow-up
- merge opportunities:
  - none; the three survivor lanes remain intentionally separated by risk surface

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`

1. persistence-context authority hardening
2. director-feedback decision integrity hardening
3. ~~continuity-history and escalation guardrails~~ **COMPLETE** (`TF-CM-03`, `S3-1`, `S3-2`, `S4-4`, `S4-5`, `TF-E3`)

## 5. Per-Item Plan

### persistence-context authority hardening
- goal:
  - close low-level init/save/DB/metrics authority gaps without reopening the older closed persistence lane
- prerequisites:
  - use `docs/2026-03-16/opus-survivor-intake-authority-reclassification.md` as the promotion boundary
- execution notes:
  - keep scope bounded to `S0-1`, `X-2`, `TF-BA-02`, `TF-S4CB-02`
- completion signal:
  - init failure, save failure, DBManager access, and cached metrics coverage are contract-explicit and regression-tested
- temp cleanup action:
  - remove the mirror after closure
- status update:
  - completed on 2026-03-16
  - mirror removed after closure

### director-feedback decision integrity hardening
- goal:
  - stop fabricated retry quantification and partial-reject approval masking
- prerequisites:
  - no dependency on the continuity lane
- execution notes:
  - keep scope bounded to `TF-FB-01/02`, `TF-DG-01/02`
- completion signal:
  - decision and quantification contracts are explicit and regression-tested
- temp cleanup action:
  - remove the mirror after closure
- status update:
  - completed on 2026-03-16
  - mirror removed after closure

### continuity-history and escalation guardrails
- goal:
  - close the continuity/state-order, history-window, patch-loop, and escalation-log survivor gaps
- prerequisites:
  - consume the stabilized persistence/context authority from lane 1
- execution notes:
  - keep scope bounded to `TF-CM-03`, `S3-1/2`, `S4-4/5`, `TF-E3`
- completion signal:
  - continuity state-order, Stage 3 history carryover, Stage 4 retry guardrails, and escalation telemetry are regression-tested
- temp cleanup action:
  - remove the mirror after closure
- status update:
  - completed on 2026-03-16
  - mirror removed after closure

## 6. Shared Risks and Side-Effects
- shared write paths:
  - runtime Python modules, tests, and structured Stage 4 logs
- shared DB/schema touchpoints:
  - no schema expansion is planned; DB access contract changes are limited
- shared logs/UI surfaces:
  - Stage 0 UI messaging, Stage 4 escalation logs, feedback wording, approval behavior
- rollback/recovery concerns:
  - init failure handling, save failure signaling, retry-loop behavior, continuity transition semantics
- queue collision or ordering risks:
  - the survivor queue must not silently re-import excluded OPUS memo items

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| persistence-context authority hardening | completed | 2026-03-16 | none |
| director-feedback decision integrity hardening | completed | 2026-03-16 | none |
| continuity-history and escalation guardrails | completed | 2026-03-16 | none |

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- remove `docs/temp/queue-state.json` if present
- leave `docs/temp/README.md`
- cleanup status:
  - complete; only `docs/temp/README.md` remains

## 9. Next Active Item
- none; queue exhausted
- future work rule:
  - start from a new request or a newly revalidated intake, not from the closed survivor queue
