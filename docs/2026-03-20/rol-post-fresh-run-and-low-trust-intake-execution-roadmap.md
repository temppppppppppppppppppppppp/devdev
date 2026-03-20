# ROL Post-Fresh-Run and Low-Trust Intake Execution Roadmap

Date: 2026-03-20
Status: completed
Canonical Path: `docs/2026-03-20/rol-post-fresh-run-and-low-trust-intake-execution-roadmap.md`
Temp Mirror Path: `none (completed historical roadmap; current temp queue is empty)`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: existing project fixture churn, docs/mmmm collector docs, fresh run project 0_260320, active smoke-fixture temp mirror`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Closure Note:
- This roadmap is complete.
- The downstream execution queue that it opened was later exhausted and `docs/temp/` returned to empty-queue mode.
Controlled Bundle:
- `docs/2026-03-20/rol-global-integrity-survey-3pass-audit.md`
- `docs/2026-03-20/rol-global-integrity-evidence-manifest.md`
- `docs/2026-03-20/rol-global-live-run-merge-audit-order.md`
- `docs/2026-03-20/rol-global-live-run-preflight-watchlist.md`
- `docs/2026-03-20/rol-live-run-fixture-target-selection-audit.md`
- `docs/2026-03-20/smoke-fixture-alignment-execution-ssot.md`
- `docs/temp/smoke-fixture-alignment-execution-ssot.md`
- `docs/mmmm/20-terminal-deep-global-survey-master-order.md`
- `docs/mmmm/T01-sovereign-app-bootstrap-survey.md`
- `docs/mmmm/T02-stage2-orch-context-survey.md`
- `docs/mmmm/T03-stage2-preflight-finalizer-survey.md`
- `docs/mmmm/T04-stage3-pipeline-survey.md`
- `docs/mmmm/T05-stage4-orch-context-survey.md`
- `docs/mmmm/T06-stage4-interview-postproc-survey.md`
- `docs/mmmm/T07-director-system-survey.md`
- `docs/mmmm/T08-chief-writer-system-survey.md`
- `docs/mmmm/T09-arc-generation-validation-survey.md`
- `docs/mmmm/T10-blueprint-generation-validation-survey.md`
- `docs/mmmm/T11-agent-infra-analyst-survey.md`
- `docs/mmmm/T12-state-tracking-world-state-survey.md`
- `docs/mmmm/T13-continuity-system-survey.md`
- `docs/mmmm/T14-validation-pipeline-survey.md`
- `docs/mmmm/T15-quality-intel-advisory-survey.md`
- `docs/mmmm/T16-database-persistence-logging-survey.md`
- `docs/mmmm/T17-config-constants-prompts-schemas-survey.md`
- `docs/mmmm/T18-stage0-helpers-narrative-utils-survey.md`
- `docs/mmmm/T19-desktop-api-bridge-survey.md`
- `docs/mmmm/T20-crosscut-regression-integrity-survey.md`
- `projects/0_260320/`
- `projects/0_260320/print.txt`

## 1. Purpose
- Process the failed bounded fresh run under live-merge rules.
- Reuse existing canonical ROL survey documents as the authority backbone.
- Treat `docs/mmmm/` only as low-trust collector intake that must be re-checked against live code and fresh run evidence.
- Convert the fresh run into a bounded post-run merge audit before creating any new action-bearing execution SSOTs.
- Keep `smoke-fixture-alignment` as the only active temp execution item until new action-bearing items are proven.

## 2. Authority and Intake Rules

### 2.1 Authority order
1. completed fresh run evidence from `projects/0_260320/`
2. live workspace code
3. existing canonical 2026-03-20 ROL docs
4. `docs/mmmm/` collector surveys
5. stale survey text or memory

### 2.2 `docs/mmmm/` handling rule
- `docs/mmmm/` is not execution authority.
- It is allowed to contribute:
  - candidate watchlist items
  - code path hints
  - area grouping
  - possible regression/test anchors
- It is not allowed to contribute without re-check:
  - final severity
  - resolved/regressed claims
  - execution ordering
  - closure decisions

### 2.3 Temp queue rule
- `docs/temp/` currently contains one active execution SSOT mirror only:
  - `docs/temp/smoke-fixture-alignment-execution-ssot.md`
- No temp roadmap is created in this tranche.
- A temp roadmap is deferred unless the post-run merge produces `2+` active execution SSOTs.

## 3. Bundle Inventory

### 3.1 Canonical backbone
- `rol-global-integrity-survey-3pass-audit`
- `rol-global-integrity-evidence-manifest`
- `rol-global-live-run-merge-audit-order`
- `rol-global-live-run-preflight-watchlist`
- `rol-live-run-fixture-target-selection-audit`
- `smoke-fixture-alignment-execution-ssot`

### 3.2 Low-trust intake lanes from `docs/mmmm/`
- master order / collector routing:
  - `20-terminal-deep-global-survey-master-order.md`
- runtime and orchestration:
  - `T01`, `T02`, `T03`, `T04`, `T05`, `T06`
- director / writer / agent system:
  - `T07`, `T08`, `T11`
- arc / blueprint / continuity / validation:
  - `T09`, `T10`, `T12`, `T13`, `T14`, `T15`
- persistence / config / desktop / cross-cut:
  - `T16`, `T17`, `T18`, `T19`, `T20`

### 3.3 First re-audit priority inside `docs/mmmm/`
- first tranche:
  - `T20-crosscut-regression-integrity-survey.md`
  - `T16-database-persistence-logging-survey.md`
  - `T17-config-constants-prompts-schemas-survey.md`
  - `T19-desktop-api-bridge-survey.md`
- second tranche:
  - `T02-stage2-orch-context-survey.md`
  - `T04-stage3-pipeline-survey.md`
  - `T05-stage4-orch-context-survey.md`
  - `T14-validation-pipeline-survey.md`
- intake note:
  - these priorities come from filename/header triage only and still require live-code re-check before any merge claim

### 3.4 Fresh run evidence bundle
- run root:
  - `projects/0_260320/`
- operator transcript:
  - `projects/0_260320/print.txt`
- primary sinks:
  - `projects/0_260320/logs/session/decisions.jsonl`
  - `projects/0_260320/logs/session/ui_events.jsonl`
  - `projects/0_260320/logs/session/llm_io.jsonl`
- stage artifacts:
  - `projects/0_260320/logs/artifacts/stage3/ep_0002/...`
  - `projects/0_260320/logs/artifacts/stage4/ep_0002/...`
- live blueprint and draft surfaces:
  - `projects/0_260320/plans/blueprints/blueprint_0002.txt`
  - `projects/0_260320/drafts/ep_0001.txt`

## 4. Dependency Graph
- terminal-state freeze -> fresh-run evidence manifest refresh
- fresh-run evidence manifest refresh -> `docs/mmmm` intake triage
- `docs/mmmm` intake triage + fresh-run evidence -> canonical post-run merge audit
- canonical post-run merge audit -> action-bearing split decision
- action-bearing split decision -> update or close `smoke-fixture-alignment`

Shared substrate:
- Stage4 retry pathology
- blueprint inplace patch observability
- CoVe fail-closed behavior
- smoke fixture alignment
- live-merge watchlist discipline

## 5. Execution Order
Priority basis:
- live-run merge harness
- evidence-first merge
- single-temp-item queue preservation
- OPUS intake remains collector-only

1. Freeze the `0_260320` run into a documented terminal state.
2. Refresh or replace the fresh-run evidence manifest for `0_260320`.
3. Triage `docs/mmmm/` into low-trust intake groups and map candidates to live evidence surfaces.
4. Re-run the post-run merge audit against the fresh run and current canonical backbone.
5. Split confirmed action-bearing findings into bounded execution items or policy audits.
6. Reassess `smoke-fixture-alignment` queue status only after the merge result is stable.

## 5A. Per-Step Validity Gate
- every item in this roadmap must pass a validity gate before execution begins
- no item may start directly from the prior item's completion message alone

### 5A.1 Required checks before each item
1. re-open the governing canonical docs for the item's scope
2. confirm the live workspace paths still exist and still match the planned target
3. confirm no newer live evidence supersedes the planned inputs
4. re-check temp queue state and ensure the queue assumptions are still true
5. if the item touches code, re-run the governing doc confidence gate against current workspace state before patching

### 5A.2 Minimum validation outputs
- one short preflight note in the working log or follow-up audit
- explicit statement of:
  - target paths
  - input evidence set
  - whether the item is still valid, superseded, or blocked

### 5A.3 Abort conditions
- fresh live evidence contradicts the item plan
- canonical backbone changed in a way that invalidates the step order
- temp queue changed from single-item to multi-item and now requires a roadmap refresh
- required evidence paths are missing, overwritten, or no longer attributable

## 6. Per-Item Plan

### Item A. Terminal-State Freeze
- goal:
  - stop treating `0_260320` as an active run and convert it into bounded failed evidence
- prerequisites:
  - operator confirms the run is stopped or intentionally abandoned
- validity gate:
  - confirm the run is truly terminal and no evidence files are still actively mutating
- execution notes:
  - preserve `print.txt`
  - preserve `logs/session/*`
  - preserve `logs/artifacts/stage3/ep_0002/*`
  - preserve `logs/artifacts/stage4/ep_0002/*`
  - capture whether the live blueprint was overwritten after V75-D patch
- completion signal:
  - run state documented as `failed` or `aborted-by-operator`
  - evidence paths frozen

### Item B. Fresh-Run Evidence Refresh
- goal:
  - create a manifest specific to the `0_260320 frontier lag 1arc` failure run
- prerequisites:
  - Item A complete
- validity gate:
  - confirm Item A freeze paths and timestamps are stable
- execution notes:
  - do not overwrite prior smoke-manifest meaning without explicit distinction
  - prefer a separate evidence manifest keyed to `0_260320`
  - highlight:
    - repeated post-select continuity/history conflicts
    - contradiction firewall escalation
    - V75-D blueprint inplace patch success log
    - missing patched blueprint artifact snapshot
    - CoVe runtime failure after a temporary PASS
- completion signal:
  - evidence manifest saved
  - all key sinks and artifact paths listed

### Item C. `docs/mmmm/` Intake Triage
- goal:
  - turn the 20 collector docs into a bounded hint ledger
- prerequisites:
  - none beyond canonical backbone availability
- validity gate:
  - confirm `docs/mmmm/` bundle contents have not changed since roadmap capture
- execution notes:
  - group by lane
  - strip authority language
  - mark stale/noisy/no-trust portions
  - re-audit first in this order:
    - `T20`, `T16`, `T17`, `T19`
    - `T02`, `T04`, `T05`, `T14`
  - link only the parts that intersect the fresh run:
    - Stage4 orchestration
    - Stage4 interview/postproc
    - director system
    - chief writer
    - blueprint generation/validation
    - continuity
    - persistence/logging
    - desktop/app if spike evidence matters
- completion signal:
  - one canonical triage doc for `docs/mmmm/`
  - mapped candidate watchlist with live-code paths

### Item D. Canonical Post-Run Merge Audit Refresh
- goal:
  - merge:
    - existing canonical survey backbone
    - fresh run evidence from `0_260320`
    - low-trust collector hints from `docs/mmmm/`
- prerequisites:
  - Items B and C complete
- validity gate:
  - confirm evidence manifest and intake triage are both final enough for merge
- execution notes:
  - reuse existing watchlist but reclassify:
    - fired
    - not-fired
    - superseded
    - partial / inconclusive
  - explicitly state that the `0_260320` run is a bounded failure sample, not a broad quality verdict
- completion signal:
  - canonical post-run merge audit saved
  - confidence re-estimated

### Item E. Action-Bearing Split
- goal:
  - decide which findings become bounded execution SSOTs
- prerequisites:
  - Item D complete
- validity gate:
  - confirm the merge audit confidence and finding classes are stable enough to split
- execution notes:
  - likely candidate buckets:
    - Stage4 retry pathology / repeated post-select downgrade
    - blueprint inplace patch observability gap
    - CoVe runtime failure fail-closed path
    - smoke-fixture alignment follow-up if still open
  - policy-only items should remain audits, not execution docs
- completion signal:
  - each confirmed finding is classified as:
    - bounded execution SSOT
    - policy audit
    - watchlist only

### Item F. Queue and Closure Decision
- goal:
  - keep temp queue clean and singular
- prerequisites:
  - Item E complete
- validity gate:
  - confirm no additional action-bearing execution docs were created outside the split process
- execution notes:
  - if only `smoke-fixture-alignment` remains active, keep current temp mirror only
  - if `2+` new execution SSOTs emerge, create a canonical aggregate roadmap and then mirror it to `docs/temp/execution-roadmap.md`
  - if `smoke-fixture-alignment` is superseded or closed, use closure harness and remove only that mirror
- completion signal:
  - temp queue state matches canonical decisions
  - `ops_validator` passes

## 7. Shared Risks and Side-Effects
- active run ambiguity:
  - do not finalize merge claims until the `0_260320` run is explicitly terminal
- OPUS overclaim risk:
  - `docs/mmmm/` may contain false authority, stale counts, or noisy severity language
- artifact overwrite risk:
  - Stage4 blueprint inplace patch may overwrite a live blueprint surface without preserving a patched snapshot artifact
- terminal mojibake risk:
  - shell-rendered mojibake must not drive source edits without UTF-8 re-check
- queue collision risk:
  - `smoke-fixture-alignment` must remain the only temp mirror unless new execution items are truly confirmed

## 8. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| Item A. Terminal-State Freeze | completed | 2026-03-20 | none |
| Item B. Fresh-Run Evidence Refresh | completed | 2026-03-20 | none |
| Item C. `docs/mmmm/` Intake Triage | completed | 2026-03-20 | none |
| Item D. Canonical Post-Run Merge Audit Refresh | completed | 2026-03-20 | none |
| Item E. Action-Bearing Split | completed | 2026-03-20 | none |
| Item F. Queue and Closure Decision | completed | 2026-03-20 | none |

Allowed statuses:
- pending
- in_progress
- completed
- blocked

## 9. Queue Cleanup Rule
- do not create a temp roadmap in this tranche unless `2+` active execution SSOTs are confirmed
- keep `docs/temp/smoke-fixture-alignment-execution-ssot.md` as the only temp execution item until the merge audit proves otherwise
- if the merge audit closes `smoke-fixture-alignment`, remove only that mirror and leave `docs/temp/README.md`
- if the merge audit creates additional execution SSOTs, create one canonical roadmap only, then mirror it to `docs/temp/execution-roadmap.md`

## 10. Confidence and Save Gate
- pass 1:
  - scope, authority, and live-merge role separation checked
- pass 2:
  - path inventory, commit state, and queue status checked
- pass 3:
  - execution order, temp-queue rule, and action split logic checked
- estimated confidence:
  - `0.96`

This roadmap is actionable because it does not depend on OPUS trust. It treats `docs/mmmm/` as intake only and puts terminal-state capture plus fresh evidence merge ahead of all execution decisions.
