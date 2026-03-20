# ROL Live-Run 0_260320 Evidence Manifest

Date: 2026-03-20
Status: active
Canonical Path: `docs/2026-03-20/rol-live-run-0_260320-evidence-manifest.md`
Related Freeze Audit: `docs/2026-03-20/rol-live-run-0_260320-terminal-state-freeze-audit.md`
Related Roadmap: `docs/2026-03-20/rol-post-fresh-run-and-low-trust-intake-execution-roadmap.md`
Scope: bounded fresh live run under `projects/0_260320`
Role: evidence inventory only
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: existing project fixture churn, docs/mmmm collector docs, fresh run project 0_260320, active smoke-fixture temp mirror`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Purpose
- Materialize the fresh-run evidence bundle for `0_260320` as a standalone manifest.
- Support the later post-run merge audit without overloading the repo-wide manifest.
- Record fired evidence themes without freezing final severity or final remediation decisions.

## 2. Run Identity
- project root:
  - `projects/0_260320/`
- session id:
  - `20260320_102544`
- run mode:
  - frontier-lag bounded run (`1 arc`)
- terminal classification:
  - bounded failure sample with orderly shutdown

## 3. Evidence Index

### 3.1 Operator transcript
- `projects/0_260320/print.txt`

### 3.2 Session sinks
- `projects/0_260320/logs/session/decisions.jsonl`
- `projects/0_260320/logs/session/ui_events.jsonl`
- `projects/0_260320/logs/session/llm_io.jsonl`

### 3.3 Stage artifacts
- Stage 3 origin:
  - `projects/0_260320/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__dialogue_focused.json`
- Stage 4 retries:
  - `projects/0_260320/logs/artifacts/stage4/ep_0002/attempt_01/`
  - `projects/0_260320/logs/artifacts/stage4/ep_0002/attempt_02/`
  - `projects/0_260320/logs/artifacts/stage4/ep_0002/attempt_03/`
  - `projects/0_260320/logs/artifacts/stage4/ep_0002/attempt_04/`
  - `projects/0_260320/logs/artifacts/stage4/ep_0002/attempt_05/`

### 3.4 Live plan surfaces
- `projects/0_260320/plans/blueprints/blueprint_0002.txt`
- `projects/0_260320/drafts/`

### 3.5 Run summary outputs
- `projects/0_260320/logs/metrics/metrics_20260320_102544.json`

## 4. Run Outcome Snapshot
- Stage 2 / Stage 3:
  - enough to continue the bounded run
- Stage 4 ep1:
  - clean `PASS`
- Stage 4 ep2:
  - repeated retry pathology
  - temporary `PASS` at later round
  - then `CoVe` runtime failure turned the path back into `REJECT`
  - run shut down before producing a clean resolved success sample for ep2

## 5. Fired Evidence Themes

### 5.1 Repeated post-select continuity/history conflict
- source:
  - `decisions.jsonl`
  - Stage 4 ep2 retry artifacts
- note:
  - multiple retries were not driven by raw generation failure, but by post-select continuity/history conflict handling

### 5.2 Contradiction Firewall escalation
- source:
  - `decisions.jsonl` Stage 4 ep2 later retry
- note:
  - the retry path escalated from conflict cleanup into a firewall-class rejection

### 5.3 V75-D blueprint inplace patch success without snapshot
- source:
  - `ui_events.jsonl`
  - stage artifact directory scan
  - `blueprint_0002.txt` timestamp check
- note:
  - success is logged
  - but a dedicated patched-blueprint snapshot was not found

### 5.4 Temporary PASS followed by CoVe runtime failure
- source:
  - `ui_events.jsonl`
  - `decisions.jsonl`
- note:
  - this is a key merge-audit signal because the run can appear to recover and then still fail closed

### 5.5 Final frontier-lag shutdown with Stage 4 backlog note
- source:
  - `print.txt`
  - `ui_events.jsonl`
- note:
  - the run exited in an orderly way, but not with a clean Stage 4 closure for ep2

## 6. Preliminary Watchlist Mapping
- likely fired:
  - Stage 4 retry pathology
  - blueprint inplace patch observability gap
  - CoVe fail-closed after provisional PASS
- likely not the primary issue:
  - simple Chief Writer generation outage
  - hard process crash
- still pending later merge classification:
  - whether the root cause is upstream Stage 3 blueprint drift, Stage 4 repair-lane insufficiency, or both

## 7. Notable File Facts
- `print.txt` final write:
  - `2026-03-20 11:45:54`
- `ui_events.jsonl` final write:
  - `2026-03-20 11:45:43`
- `llm_io.jsonl` final write:
  - `2026-03-20 11:43:33`
- `decisions.jsonl` final write:
  - `2026-03-20 11:37:48`
- Stage 4 ep2 attempt directories present:
  - `attempt_01` through `attempt_05`
- no `attempt_06` artifact directory observed

## 8. Current Use Rule
- this manifest is evidence inventory only
- it may support:
  - `docs/mmmm` intake triage
  - canonical post-run merge audit
  - action-bearing split
- it may not directly support:
  - final severity
  - resolved/regressed claims
  - execution ordering without merge audit

## 9. Item-B Completion Decision
- roadmap item:
  - `Item B. Fresh-Run Evidence Refresh`
- result:
  - `completed`
- reason:
  - the `0_260320` run now has a dedicated evidence manifest
  - key sinks, artifacts, and failure themes are enumerated

## 10. Confidence
- pass 1:
  - scope and run identity checked
- pass 2:
  - evidence paths and terminal timestamps checked
- pass 3:
  - fired-theme mapping checked against session sinks and artifact inventory
- estimated confidence:
  - `0.96`
