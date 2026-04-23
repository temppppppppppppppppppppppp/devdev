# Frontier Lag Soak Canary Wave1 Execution SSOT

Date: 2026-03-27
Status: closed historical backing (2026-04-23 user-directed deactivation; the remaining durability-surface audit block is low ROI for the current board, so this lane is removed from the visible queue and preserved canonically only)
Canonical Path: `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md`
Temp Mirror Path: `retired on 2026-04-23 (former path: docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md)`
Commit State:
- Baseline Commit: `155906f3adb1c2f4a3810ce359f6b59124d8556a`
- Baseline Dirty Summary: `dirty: tracked npc-martial docs/code/tests, docs/temp/queue-state.json, canary DB artifact; untracked soak survey/benchmark docs, temp npc mirror, canary directories`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `2026-04-23 live compaction plus operator-directed deactivation retires this lane from the visible queue; soak-profile overrides and heavy-path controls are landed and test-backed, while the remaining post-run durability-surface audit block is preserved as historical backing only`
Source Survey Docs:
- `docs/2026-03-27/frontier-lag-soak-canary-compact-survey.md`
- `docs/2026-04-19/frontier-lag-soak-canary-wave1-reactivation-refresh.md`
Evidence Artifacts:
- none
Side-Effect Coverage: covered

## 1. Intent

Open one bounded execution SSOT for a low-cost frontier-lag soak canary harness extension.

Why now:

- the compact survey is final and 3-pass audited
- runner/control, lightweight config, and observability seams were independently corroborated
- soak-profile override work has already landed
- the remaining honest next step is the bounded post-run durability-surface audit block

## 2. Baseline Facts

- `scripts/run_auto_frontier_lag_harness.py` is the correct base harness
- `scripts/run_stage34_canary.py` remains the smaller reference seam for bounded Stage 3 -> 4 frontier closure
- the real repeat engine already exists in `main_a.py` through `_one_stop_pipeline_frontier_lag()`
- soak-profile controls now exist in the harness:
  - named soak-profile selection
  - Stage2 / Stage4 all-flash model overrides
  - manuscript min/target length overrides
  - heavy-path toggle controls
- current auto-harness observability proves liveness and sink alignment, but not long-memory state continuity, because it does not yet audit:
  - `episode_bibles`
  - `state_logs`
  - `world_state`
- the current compacted queue retires this lane from the visible board and preserves it canonically as historical backing only

## 3. Scope

Included:
- `scripts/run_auto_frontier_lag_harness.py`
- `scripts/run_stage34_canary.py`
- targeted helper seams needed to support bounded soak profile selection
- read-only post-run audit of:
  - `episode_bibles`
  - `state_logs`
  - `world_state`
- bounded tests for the harness extension
- execution-roadmap and temp-queue synchronization artifacts required by queue governance

Excluded:
- broad `main_a.py` frontier-lag refactor
- new orchestration engine
- `gold manuscript benchmark` lane
- unrelated canary/dashboard/budget-gate work
- broad global model-default changes in `config/models.yaml`
- new DB tables or schema changes
- benchmark or corpus ingestion tooling
- any mutation on non-disposable project targets

## 4. Pass 1. Inventory Summary

- reusable runner/control substrate already exists:
  - `scripts/run_auto_frontier_lag_harness.py`
  - `scripts/run_stage34_canary.py`
  - `_one_stop_pipeline_frontier_lag()` in `main_a.py`
- reusable observability substrate already exists:
  - `PassRateMonitor`
  - `FailureAnalyzer.sink_alignment_summary()`
  - `episode_production.jsonl`
  - `stage_attempts`
  - `director_selections`
- durable state surfaces needed for the soak extension already exist:
  - `episode_bibles`
  - `state_logs`
  - `world_state`
- current gap inventory:
  - soak-profile override contract is landed
  - heavy-path toggle support is landed
  - bounded tests for the override layer are landed
  - no post-run state audit block yet exists for the three durability surfaces

## 5. Pass 2. Semantic Classification

- Class A: existing reusable substrate
  - frontier-lag loop in `main_a.py`
  - `run_auto_frontier_lag_harness.py` worker/watchdog/analyze path
  - `run_stage34_canary.py` clamp/reference seam
  - `FailureAnalyzer` sink-alignment path
- Class B: bounded extension seams
  - special soak profile or override contract
  - temporary runtime model/length/toggle injection
  - post-run state audit summary
  - bounded tests for the extension
- Class C: out-of-scope fresh design
  - new orchestration engine
  - benchmark lane implementation
  - broad runtime or global-config redesign

## 6. Side-Effect Map

- file writes / artifacts:
  - canonical and temp execution docs
  - future harness outputs on disposable target projects:
    - manifest
    - poll history
    - analysis JSON
    - runtime-analysis SSOT
- DB / schema / transaction boundaries:
  - no schema changes are in scope
  - future soak pilot may read `episode_bibles`, `state_logs`, and `world_state`
  - disposable target projects only for any mutation-capable run
- JSONL / log / audit sinks:
  - `episode_production.jsonl`
  - `pass_rate_monitor.json`
  - `runtime_audit_summary.json`
  - auto-frontier-lag analysis artifacts
- console / UI / operator output:
  - existing watchdog cadence and prompt-blocked visibility remain active
- rollback / recovery / retry:
  - watchdog termination path remains existing harness behavior
  - no new rollback substrate is planned beyond read-only post-run state audit
- cache / global state:
  - any override implementation must remain harness-local and restore state after the run
- bootstrap fallback / config-env mutation:
  - avoid persistent config mutation
  - prefer bounded runtime injection or temporary overlay

If a category is not applicable, say so explicitly:
- schema mutation: not applicable
- new durable authority sink: not applicable

## 7. Realization Architecture

- substrate requirement:
  - keep `main_a.py` as the repeat engine
  - extend `scripts/run_auto_frontier_lag_harness.py` rather than inventing a new controller
- contract requirement:
  - one explicit soak profile or equivalent bounded override contract
  - explicit override inputs for:
    - Stage 2 / Stage 4 model tier
    - manuscript min/target length
    - heavy-path toggle set
- audit requirement:
  - post-run state audit must query and summarize:
    - `episode_bibles`
    - `state_logs`
    - `world_state`
- queue constraint:
  - the 2026-04-23 compacted roadmap retires this item from the visible queue as low-ROI residue
  - this lane should not be treated as active realization unless a fresh bounded reactivation decision is made

## 8. Execution Tranches

1. Tranche 1: bounded soak profile and override contract
2. Tranche 2: post-run state audit for `episode_bibles` / `state_logs` / `world_state`
3. Tranche 3: disposable 3-arc pilot canary and dated evidence note

## 9. Acceptance Criteria

- no new orchestration engine is introduced
- `run_auto_frontier_lag_harness.py` remains the governing base
- no broad `main_a.py` refactor is required
- override contract exists for:
  - model tier
  - manuscript length
  - heavy-path toggle set
- post-run analysis includes state continuity surfaces beyond sink alignment
- a 3-arc disposable pilot can be executed or yields a bounded blocker with raw evidence

## 10. Verification Plan

- `python -m py_compile` on touched harness/tests
- targeted pytest shards for:
  - `tests/test_auto_frontier_lag_harness.py`
  - any new soak-harness test file if introduced
- `python scripts/check_utf8_hygiene.py` on touched docs/scripts/tests
- disposable pilot commands after tranche 1 and tranche 2 land:
  - harness plan
  - harness run
  - harness analysis
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not overlap this item with a new wuxia canary or a resumed npc-martial hotfix lane
- do not mutate non-disposable project targets
- do not broaden the item into benchmark implementation
- do not change global production model defaults as a shortcut for harness-local override behavior
- do not recreate a temp mirror or reopen this lane without a fresh bounded queue decision
- keep authority distinctions explicit:
  - `pass_rate_monitor.json` is companion cache only
  - `runtime_audit_summary` is snapshot only
  - durable truth remains in DB and `episode_production.jsonl`

## 12. Temp Queue Notes

- temp status: retired historical backing
- cleanup condition:
  - keep no temp mirror while this lane remains historical only
  - recreate a temp mirror only after an explicit bounded reactivation decision
- roadmap dependency:
  - governed historically by `docs/2026-04-23/active-temp-execution-roadmap.md`

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run this document's 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

### Pass 1. Fact Extraction

- based on the final compact survey and the corroborated 3-lane merge audit
- queue blocker state was rechecked against the live `docs/temp/queue-state.json`
- PASS

### Pass 2. Contradiction Check

- no contradiction found between survey conclusions and the bounded soak scope
- later queue-roadmap refreshes were left free to reorder the item when blocker reality changed
- PASS

### Pass 3. Decision Audit

- opening the SSOT now is useful because the design is stable
- the document remained ready for later promotion without requiring a rewrite
- PASS

Estimated confidence: `96%`

## 15. Director Promotion 2026-03-28

Promotion Verdict: `historical promotion note`

Why promoted now:

- queue authority refresh at that historical point established the soak lane as the next candidate after the older npc-martial queue posture changed
- live process inspection showed no active wuxia canary `python` process in the workspace at decision time
- this soak item remains the highest-ROI bounded next step on already-corroborated survey evidence

Promotion 3-pass:

- Pass 1. Structure and Scope
  - promotion is bounded to queue authority only; no code realization starts in this turn
  - PASS
- Pass 2. Evidence Consistency
  - aligned the SSOT with the reordered roadmap and current live workspace evidence
  - no active npc-martial seam diff or active wuxia canary thread remains to justify holding this item back
  - PASS
- Pass 3. Execution Readability
  - promotion remained bounded to queue authority only
  - PASS

## 16. 2026-04-19 Reactivation Refresh

Source doc:

- `docs/2026-04-19/frontier-lag-soak-canary-wave1-reactivation-refresh.md`

Current reading:

- the bounded soak-harness and post-run state-audit work is still real
- the lane is not stale, but it is also not active progress anymore

Queue consequence at the time:

- keep this lane visible
- keep the temp mirror
- treat it as parked low-priority reference-validation debt rather than active implementation progress

2026-04-23 superseding note:

- the later compaction wave retired this lane from the visible queue
- the temp mirror was removed
- the canonical SSOT remains only as historical backing

Promotion confidence: `97%`
