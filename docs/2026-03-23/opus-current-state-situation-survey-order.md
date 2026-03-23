Date: 2026-03-23
Status: active
Document Type: bounded survey order
Canonical Path: `docs/2026-03-23/opus-current-state-situation-survey-order.md`
Temp Mirror Path: none

## 1. Purpose
- Give Opus a bounded `current state` survey order after the long-function campaign, fresh run, post-audit closures, deep-dive reports, and the current max-retention DB logging queue item.
- Produce a clean situation-awareness report that tells Codex:
  - what is already closed and trustworthy
  - what is still active or pending
  - what is provisional or stale
  - what is the highest-ROI next action

## 2. Current Context
- High-risk long-function bands are cleared in live code.
- Fresh run already happened.
- Several execution SSOTs were realized and audited closed.
- One active pending queue item remains:
  - `docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md`
- This order is for situation awareness only.
- This order is not a realization wave.

## 3. Inputs Opus Must Read
Read these first, in this order:
1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/2026-03-23/daily-roadmap-2026-03-23.md`
4. `docs/temp/queue-state.json`
5. `docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md`
6. `docs/2026-03-23/fresh-run-3pass-audit-report.md`
7. `docs/2026-03-23/weekend-long-function-global-3pass-audit.md`
8. `docs/2026-03-23/director-pipeline-7axis-deep-dive.md`
9. `docs/2026-03-23/generation-coherence-deep-dive-report.md`
10. `docs/2026-03-23/opus-llm-friendliness-global-survey-report.md`
11. `docs/2026-03-23/llm-codebase-orientation-pack.md`

## 4. Survey Scope
Included:
- operational status across current docs and queue state
- closure status of long-function and post-audit execution work
- fresh-run conclusions and remaining follow-up debt
- provisional vs final report hygiene
- active pending queue interpretation
- highest-ROI next action recommendation

Excluded:
- code changes
- queue closure
- roadmap rewrite
- new execution SSOT creation
- refactor planning beyond a short recommendation section

## 5. Required Questions
1. What is already `completed and validated` in the current workspace?
2. What is `active pending` right now?
3. Which documents or claims are `provisional`, `stale`, or partially superseded?
4. Which unresolved items are true runtime risks versus observability or readability debt?
5. What is the single highest-ROI next action for Codex after this survey?

## 6. Required Method
### Pass 1. Document and Queue Inventory
- Reconcile the current roadmap memo, queue-state, active execution SSOT, and major audit outputs.
- Separate:
  - completed / validated
  - active pending
  - provisional
  - stale / superseded

### Pass 2. Claim Reconciliation
- Check whether the main claims across fresh run, long-function audit, deep dives, and LLM-friendliness survey agree or conflict.
- Mark each meaningful conflict as one of:
  - no conflict
  - stale wording only
  - unresolved but bounded
  - active risk

### Pass 3. Operational Recommendation Merge
- Produce a short operator-facing conclusion:
  - repo health snapshot
  - current active queue item
  - blocked vs unblocked next action
  - what Codex should do next

## 7. Mandatory Output
Write the report to:
- `docs/2026-03-23/current-state-situation-survey-report.md`

The report must contain:
1. Executive Summary
2. Current State Snapshot
3. Completed And Validated Work
4. Active Pending Work
5. Provisional / Stale / Superseded Items
6. Current Risk Register
7. Highest-ROI Next Action
8. Confidence And Limits

## 8. Acceptance Criteria
- The report explicitly identifies the single active pending queue item, if still active.
- The report clearly distinguishes `completed`, `pending`, and `provisional`.
- The report does not claim code or queue closure that did not happen.
- The report states whether the system is currently in:
  - stabilization mode
  - refactor mode
  - survey mode
  - execution mode
- The report gives one clear next action for Codex.
- Apply 3-pass document audit before final save.
- Confidence must be at least 95%, or the report remains provisional.

## 9. Operator Notes
- Treat `daily-roadmap-2026-03-23.md` as a planning memo, not as the execution authority.
- Treat `docs/temp/queue-state.json` and the active temp mirror as higher-authority queue state than stale roadmap wording.
- Live workspace state beats older survey wording.
- Do not refresh or mutate any queue artifact during this survey.

## 10. Opus Prompt
Use this prompt as-is:

```text
System-track bounded survey order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/2026-03-23/opus-current-state-situation-survey-order.md
4. docs/2026-03-23/daily-roadmap-2026-03-23.md
5. docs/temp/queue-state.json
6. docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md
7. docs/2026-03-23/fresh-run-3pass-audit-report.md
8. docs/2026-03-23/weekend-long-function-global-3pass-audit.md
9. docs/2026-03-23/director-pipeline-7axis-deep-dive.md
10. docs/2026-03-23/generation-coherence-deep-dive-report.md
11. docs/2026-03-23/opus-llm-friendliness-global-survey-report.md
12. docs/2026-03-23/llm-codebase-orientation-pack.md

Task:
Produce a bounded current-state situation survey for the live workspace.

Primary goal:
Tell Codex, with current evidence, what is completed and trustworthy, what is still active pending, what is provisional or stale, and what the next action should be.

Hard constraints:
- Survey only. No code changes.
- No queue closure.
- No roadmap rewrite.
- No new execution SSOT creation.
- Do not overrule live queue state with stale memo language.
- Do not invent completed work.
- If confidence stays below 95%, mark the report provisional.

Required method:
1. Inventory current docs and queue state.
2. Reconcile claims across fresh run, long-function audit, deep dives, and survey outputs.
3. Classify each meaningful thread as:
   - completed and validated
   - active pending
   - provisional
   - stale or superseded
   - active risk
4. Recommend exactly one highest-ROI next action for Codex.

Write the report to:
docs/2026-03-23/current-state-situation-survey-report.md

Mandatory report structure:
1. Executive Summary
2. Current State Snapshot
3. Completed And Validated Work
4. Active Pending Work
5. Provisional / Stale / Superseded Items
6. Current Risk Register
7. Highest-ROI Next Action
8. Confidence And Limits

Acceptance criteria:
- identifies the single active pending queue item if one exists
- separates completed, pending, and provisional cleanly
- states whether the repo is currently in stabilization, refactor, survey, or execution mode
- names exactly one next action for Codex
- uses 3-pass document audit before final save
- confidence >= 95%, or the report is marked provisional

After saving, run:
- python scripts/check_utf8_hygiene.py docs/2026-03-23/current-state-situation-survey-report.md docs/2026-03-23/opus-current-state-situation-survey-order.md
- python scripts/ops_validator.py

In the final response to me:
- summarize the current state first
- then the active pending item
- then the provisional/stale items
- then the single recommended next action
- then confidence
- keep it concise
```

## 11. 3-Pass Audit Record
- Pass 1: bounded the order to situation awareness only and fixed the live input set around the current queue state.
- Pass 2: separated `completed`, `active pending`, and `provisional/stale` as explicit required outputs.
- Pass 3: embedded the Opus-ready prompt and rechecked that the order does not mutate queue or execution state.

## 12. Confidence
- Confidence: 98%
- Basis:
  - single active pending queue item is explicit in live queue-state
  - the task is document-only and bounded
  - the order does not depend on unstable external data
