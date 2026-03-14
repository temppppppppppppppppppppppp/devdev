# Stage 4 Canary Archive Locator Note

Created: 2026-03-13
Updated: 2026-03-14
Status: `runtime-refreshed-live-and-branch-inventoried`

## Summary

Historical Stage 4 canary artifacts still live under `projects/기록용/*`.
Current-workspace proof artifacts now include four distinct tiers:

- `projects/00_test_07_runtime_proof_refresh_20260314`
  - equivalent analyze refresh over preserved canary data
  - useful for stale/provenance re-audit
  - not a fresh live rerun
- `projects/00_test_09_full_live_runtime_proof_refresh_20260314`
  - fresh full live Stage 4 rerun on current code
  - accepted current closure basis
- `projects/00_test_10_retry_live_runtime_proof_refresh_20260314`
  - fresh current live retry-branch proof
  - branch-only proof for `retry_required_row_count > 0`
- `projects/00_test_12_stage34_live_runtime_proof_refresh_20260314`
  - fresh current live Stage 3 -> 4 frontier proof
  - post-closure multi-stage extension over the Stage 4 closure family

Historical archive evidence and current proof evidence are not the same proof tier.

## Historical Archive Inventory

| class | workspace path | proof file | note |
| --- | --- | --- | --- |
| historical | `projects/기록용/00_test_05` | `logs/canary_summary.json` | archived summary only |
| historical | `projects/기록용/00_test_06` | `logs/canary_summary.json` | archived failed / proof-gap example |
| historical | `projects/기록용/00_test_07` | `logs/canary_summary.json` | archived pass-era canary before current companion audit |

## Current Proof Inventory

### A. Equivalent Analyze Refresh

- `project_locator`: `projects/00_test_07_runtime_proof_refresh_20260314`
- summary: `projects/00_test_07_runtime_proof_refresh_20260314/logs/canary_summary.json`
- companion audit: `projects/00_test_07_runtime_proof_refresh_20260314/logs/canary_companion_audit.json`
- source archive copied from: `projects/기록용/00_test_07`
- classification: `current`
- proof origin: `current_workspace_refresh`
- judgment:
  - equivalent refresh over preserved artifacts
  - useful for current-contract re-audit
  - not accepted as current closure basis

### B. Fresh Full Live Rerun

- `project_locator`: `projects/00_test_09_full_live_runtime_proof_refresh_20260314`
- summary: `projects/00_test_09_full_live_runtime_proof_refresh_20260314/logs/canary_summary.json`
- companion audit: `projects/00_test_09_full_live_runtime_proof_refresh_20260314/logs/canary_companion_audit.json`
- source archive copied from: `projects/기록용/00_test_02`
- latest session: `20260314_112302`
- classification: `current`
- proof origin: `current_workspace_refresh`
- judgment:
  - `sink_alignment_summary.status = ok`
  - `rationale_contract_summary.status = ok`
  - `companion_audit_summary.status = ok`
  - accepted current closure basis

### C. Fresh Retry-Branch Live Proof

- `project_locator`: `projects/00_test_10_retry_live_runtime_proof_refresh_20260314`
- summary: `projects/00_test_10_retry_live_runtime_proof_refresh_20260314/logs/canary_summary.json`
- companion audit: `projects/00_test_10_retry_live_runtime_proof_refresh_20260314/logs/canary_companion_audit.json`
- source archive copied from: `projects/기록용/00_test_02`
- latest session: `20260314_123030`
- classification: `current`
- proof origin: `current_workspace_refresh`
- judgment:
  - `rationale_contract_summary.retry_required_row_count = 1`
  - `rows_missing_retry_context = []`
  - same run exercised `Round 1 REJECT -> Round 2 PASS`
  - `current_session_sink_alignment_summary.status = ok`
  - whole-run sink alignment remains `warn` only because older-session rows remain in the copied project

### D. Fresh Stage 3 -> 4 Live Proof Extension

- `project_locator`: `projects/00_test_12_stage34_live_runtime_proof_refresh_20260314`
- summary: `projects/00_test_12_stage34_live_runtime_proof_refresh_20260314/logs/stage34_canary_summary.json`
- source archive copied from: `projects/기록용/00_test_02`
- latest session: `20260314_150959`
- classification: `current`
- proof origin: `current_workspace_refresh`
- judgment:
  - same-session `shared_session_id` present
  - `stage3_current_session_sink_alignment_summary.status = ok`
  - nested `stage4_canary_summary.current_session_sink_alignment_summary.status = ok`
  - nested `rationale_contract_summary.status = ok`
  - nested `companion_audit_summary.status = ok`
  - `multi_stage_proof_scope_summary.status = pass`
  - post-closure proof extension; not used as the Stage 4 closure basis

## Interpretation Rules

- `historical`
  - archived proof under `projects/기록용/*`
  - useful for provenance and comparison
  - never sufficient as current closure by itself
- `current`
  - refreshed proof artifact under active `projects/*`
  - Stage 4 proof artifacts carry `project_locator`, `logs/canary_summary.json`, and `logs/canary_companion_audit.json`
  - Stage 3 -> 4 frontier proof artifacts carry `project_locator` and `logs/stage34_canary_summary.json`
  - may be analyze-only refresh, full live rerun, branch-only live proof, or post-closure multi-stage proof extension
- `closure basis`
  - must be a current fresh live rerun
  - must show same-session sink alignment / rationale contract / companion audit on current code
- `branch-only proof`
  - may prove a specific runtime branch on current code
  - does not replace the closure basis when whole-run sink alignment remains `warn`

## Canonical Locator Rule

- Use `canary_summary.json.project_locator` as the canonical locator.
- When discussing archived proof, preserve both:
  - actual workspace path
  - proof class = `historical`
- When discussing current proof, preserve all three:
  - `project_locator`
  - `logs/canary_summary.json`
  - `logs/canary_companion_audit.json`

## Decision For This Turn

- accepted closure basis remains `00_test_09_full_live_runtime_proof_refresh_20260314`
- retry branch proof is now present as `00_test_10_retry_live_runtime_proof_refresh_20260314`
- Stage 3 -> 4 live proof extension is now present as `00_test_12_stage34_live_runtime_proof_refresh_20260314`
- same-session branch sink completeness is now explicit for both patch-path and retry-path proof
- remaining open implementation defect from the old retry residual:
  - none
