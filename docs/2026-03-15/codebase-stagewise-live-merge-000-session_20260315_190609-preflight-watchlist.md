<!-- [참고자료] -->
# Codebase Stagewise Live-Merge Preflight Watchlist

Date: 2026-03-15
Status: draft-live-run-pending
Project: `projects/000`
Structured Session Id: `20260315_190609`
Observed Plain Log Token: `20260315_190600`
Process State:
- `python main_a.py`
- PID `6012`
- process still alive; no full application terminal state yet
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: AGENTS/docs/harness/menu7 docs edits, harness/test edits, deleted local transcript file, unrelated pdf/style/log artifacts, and untracked projects/000/`

## 1. Scope
- per-stage deep survey across Stage `0~4`
- shared substrate:
  - runtime orchestration
  - persistence and logging
  - context carryover
  - artifact truth
- excluded for this draft:
  - desktop live runtime
  - code patching
  - final execution SSOT promotion

## 2. Pre-Run / Mid-Run Watch Items
- Stage 0:
  - style guide and bible/treatment outputs saved cleanly
  - prompt/input replay drift around Stage 0 option paths
- Stage 1:
  - thin surface concentrated in `stage01_helpers.py`
  - no fresh runtime evidence yet in current run
- Stage 2:
  - arc output truth vs constraint carryover
  - `constraint_summary` omission warning in live log
- Stage 3:
  - blueprint frontier backlog behavior
  - Stage 3 metadata handoff to Stage 4
- Stage 4:
  - CW historical carryover quality
  - Director critique surface vs final manuscript carryover
  - retry / patch / rationale lineage
- Cross-cut:
  - summary/pass-rate freshness while app is still running
  - visible mojibake in session sinks
  - stage attempt / director selection / artifact alignment

## 3. Draft Save Rule
- this watchlist is provisional because the app process is still alive
- no closure or resolved/regressed claim is authorized yet
