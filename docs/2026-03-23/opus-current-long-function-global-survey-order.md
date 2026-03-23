Date: 2026-03-23
Status: active
Document Type: system-track survey order
Canonical Path: `docs/2026-03-23/opus-current-long-function-global-survey-order.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-20/TF-static-complexity-audit-v2.md`
- `docs/2026-03-23/weekend-long-function-global-3pass-audit-order.md`
- `docs/2026-03-23/weekend-long-function-global-3pass-audit.md`
- `docs/2026-03-23/fresh-run-3pass-audit-report.md`
- `docs/2026-03-23/q1-q8-current-state-merge-audit.md`
- `docs/2026-03-23/daily-roadmap-2026-03-23.md`

Commit State:
- Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`
- Baseline Dirty Summary: `dirty workspace allowed; touched surfaces include modules/core/stage3_orchestrator.py, tests/test_stage3_orchestrator.py, docs/temp/queue-state.json, projects/0_0323/`
- Resume Commit: `same-as-baseline unless Opus starts from a newer local state`
- Resume Drift Summary: `must be refreshed at survey start before any final resolved/regressed claim`

## 1. Purpose
- Define the current Opus order for a fresh long-function global re-survey while the active fresh run remains untouched.
- Re-check the current repo-wide long-function landscape after:
  - the original long-function campaign
  - the weekend 3-pass integrity audit
  - post-audit bugfixes
  - console / DB observability expansion
- Separate:
  - truly regrown or still-risky long functions
  - acceptable bounded shells / semantic cores
  - owner-pressure surfaces that should move to refactor review later
  - stale findings that no longer match live code

This is survey-only. It is not a new realization wave.

## 2. Active Runtime Constraint
- An active fresh run is already in progress or intentionally being preserved.
- This survey must not interrupt, reset, or compete with that run.
- Do not launch another fresh run.
- Do not close queue items.
- Do not mutate active runtime evidence or logs.
- Use live workspace source plus already-saved reports as evidence.

## 3. Primary Questions
1. What is the current live long-function band state across production code?
2. Which remaining `100+` functions are acceptable bounded shells or semantic cores, and which are still real readability / maintenance risks?
3. Did recent observability / logging / retention work re-inflate any previously normalized family?
4. Which owner surfaces still carry unhealthy method pressure even if long-function bands are mostly cleared?
5. Which older long-function findings are now stale and should stop influencing execution planning?

## 4. Scope
Included production surfaces:
- `main_a.py`
- `modules/core/**/*.py`
- `modules/domain/agents/**/*.py`
- `modules/validation/**/*.py`
- `modules/api/**/*.py`

Included analysis dimensions:
- current long-function bands
- top remaining `100+` surfaces
- owner direct-method pressure
- same-file shell/core/sink boundary quality
- logging/observability changes that may have regrown functions
- stale-vs-live mismatch against prior long-function survey docs

Excluded:
- tests as scoring targets
- docs-only hotspot scoring
- new implementation
- new module split proposals beyond bounded recommendations
- interrupting or rerunning the active fresh run

## 5. Evidence Priority
Use this evidence order when claims conflict:
1. live workspace source
2. recent merge-audit / fresh-run reports
3. `docs/2026-03-20/TF-static-complexity-audit-v2.md`
4. older survey wording

Do not let older `T###` tracker wording outrank live source.

## 6. Required Method

### Pass 1. Live Static Recount
- Recount current production long-function bands from live source.
- Minimum bands:
  - `100+`
  - `150+`
  - `180+`
  - `200+`
  - `300+`
  - `500+`
- Rebuild the current top hotspot table from source, not from stale text.

### Pass 2. Structural Classification
- For each meaningful remaining hotspot, classify exactly one:
  - `bounded shell`
  - `bounded semantic core`
  - `owner-pressure risk`
  - `observability regrowth`
  - `regression suspicion`
  - `stale prior finding`
- For each hotspot, answer:
  1. current owner
  2. why the function is still large
  3. whether the size is justified
  4. whether it blocks the next fresh-run stabilization

### Pass 3. Planning Consequence
- Produce a short action table with exactly these buckets:
  - `fix before next fresh run`
  - `safe to defer until next-week refactor`
  - `no action / acceptable as-is`
- Do not produce a new execution SSOT unless the user explicitly asks after reading the report.

## 7. Mandatory Checks
- Re-score `TF-static-complexity-audit-v2.md` trustworthiness against live code.
- Check whether any recent console / DB logging work regrew previously settled functions.
- Check whether `Stage 3`, `Stage 4`, `BaseAgent`, `DBManager`, `SovereignApp`, `DirectorEnsemble`, `Stage4InterviewRound`, `Stage3Orchestrator`, and `Stage2Finalizer` changed rank materially.
- Check whether any prior P0/P1 long-function claim is now stale.

## 8. Required Deliverables
Save these outputs:
1. final report
   - `docs/2026-03-23/opus/current-long-function-global-survey-report.md`
2. optional evidence manifest, only if needed
   - `docs/2026-03-23/opus/current-long-function-global-evidence-manifest.md`

Do not create temp execution mirrors.
Do not create or refresh a queue roadmap from this survey alone.

## 9. Required Report Structure
The report must contain:
1. Executive Summary
2. Current Long-Function Band Snapshot
3. Current Top Hotspots
4. Owner-Pressure Snapshot
5. Stale-vs-Live Corrections
6. Observability Regrowth Check
7. Pre-Fresh-Run Must-Fix Items
8. Safe Deferrals
9. No-Action / Acceptable Bounded Cores
10. Confidence And Limits

For every P0 or P1 item include:
- file path
- line anchor
- current LOC
- classification
- why it matters now
- whether it blocks the next fresh run

## 10. Hard Constraints
- Survey-only. No code patches.
- Do not rerun fresh run.
- Do not close active execution SSOTs.
- Do not mutate `docs/temp/queue-state.json`.
- Do not invent new completed work.
- Do not overclaim from prior surveys when live source disagrees.
- Do not treat every `100+` function as a bug; bounded shells and bounded semantic cores are allowed.

## 11. Acceptance Criteria
- live recount is rebuilt from source
- top hotspot table is current
- stale prior findings are explicitly separated
- pre-fresh-run blockers are clearly separated from next-week refactor candidates
- confidence is at least 95%, or the report remains provisional

## 12. Suggested Read Order For Opus
1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. `docs/implementation/system-full-survey-execution-harness.md`
4. `docs/implementation/document-3pass-audit-harness.md`
5. `docs/2026-03-23/opus-current-long-function-global-survey-order.md`
6. `docs/2026-03-20/TF-static-complexity-audit-v2.md`
7. `docs/2026-03-23/weekend-long-function-global-3pass-audit.md`
8. `docs/2026-03-23/fresh-run-3pass-audit-report.md`
9. `docs/2026-03-23/q1-q8-current-state-merge-audit.md`
10. `docs/2026-03-23/daily-roadmap-2026-03-23.md`

## 13. Opus Launch Prompt
```text
System-track survey-only order.

Read these files first, in this exact order:
1. AGENTS.md
2. docs/implementation/system-order-init-harness.md
3. docs/implementation/system-full-survey-execution-harness.md
4. docs/implementation/document-3pass-audit-harness.md
5. docs/2026-03-23/opus-current-long-function-global-survey-order.md
6. docs/2026-03-20/TF-static-complexity-audit-v2.md
7. docs/2026-03-23/weekend-long-function-global-3pass-audit.md
8. docs/2026-03-23/fresh-run-3pass-audit-report.md
9. docs/2026-03-23/q1-q8-current-state-merge-audit.md
10. docs/2026-03-23/daily-roadmap-2026-03-23.md

Task:
Run a current-state global long-function survey over the live production codebase while leaving the active fresh run untouched.

Primary goal:
Rebuild the current long-function and owner-pressure picture from live source, then separate true remaining risks from stale survey residue.

Hard constraints:
- Survey-only. Do not patch code.
- Do not launch or interrupt any fresh run.
- Do not close execution SSOTs or modify queue-state.
- Do not treat stale survey wording as authoritative if live source disagrees.
- Do not reopen a refactor wave inside the report.

Required method:
1. Recount live long-function bands from production source.
2. Rank current top remaining hotspots.
3. Classify each hotspot as bounded shell / bounded semantic core / owner-pressure risk / observability regrowth / regression suspicion / stale prior finding.
4. Separate:
   - fix before next fresh run
   - safe to defer until next-week refactor
   - no action

Output:
Write the final report to:
docs/2026-03-23/opus/current-long-function-global-survey-report.md

Optional evidence manifest only if needed:
docs/2026-03-23/opus/current-long-function-global-evidence-manifest.md

The report must include:
1. Executive Summary
2. Current Long-Function Band Snapshot
3. Current Top Hotspots
4. Owner-Pressure Snapshot
5. Stale-vs-Live Corrections
6. Observability Regrowth Check
7. Pre-Fresh-Run Must-Fix Items
8. Safe Deferrals
9. No-Action / Acceptable Bounded Cores
10. Confidence And Limits

Acceptance criteria:
- live recount from source
- current top hotspot table
- stale prior findings explicitly separated
- pre-fresh-run blockers clearly separated from next-week refactor candidates
- confidence >= 95%, or provisional status if not achieved

After saving, run:
- python scripts/check_utf8_hygiene.py docs/2026-03-23/opus-current-long-function-global-survey-order.md docs/2026-03-23/opus/current-long-function-global-survey-report.md
- python scripts/ops_validator.py

In your final response to me:
- summarize the current live long-function bands first
- then summarize true pre-fresh-run blockers
- then list stale prior findings
- then give confidence
- keep it concise
```

## 14. 3-Pass Audit Record
- Pass 1
  - confirmed this is a survey order, not an execution SSOT
  - confirmed active fresh-run non-interference is explicit
- Pass 2
  - confirmed live-source-first evidence precedence and deliverable paths are coherent
  - confirmed no temp mirror / queue mutation is requested
- Pass 3
  - confirmed the prompt, report structure, and acceptance criteria are actionable for Opus

## 15. Confidence
- Confidence: 97%
- Basis:
  - grounded in the live campaign SSOT plus newer merge/fresh-run docs
  - bounded to survey-only and current-state recount
  - explicitly avoids interfering with the active fresh run
