# Authority Alignment Benchmark Operating Model Hardening Execution SSOT

Date: 2026-04-23
Status: execution-ready (3-pass audited; parked future wave; upstream proof and benchmark governor lane)
Canonical Path: `docs/2026-04-23/authority-alignment-benchmark-operating-model-hardening-execution-ssot.md`
Temp Mirror Path: `docs/temp/authority-alignment-benchmark-operating-model-hardening-execution-ssot.md`
Commit State:
- Baseline Commit: `30b9436fc3a5c3fcc3f6397bf23bfe45d24af918`
- Baseline Dirty Summary: `dirty: prior queue and governance doc updates plus untracked docs/2026-04-23/; no unrelated project-data cleanup performed`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `2026-04-23 issue-5 formalization re-audit promoted the proof governor into its own parked execution lane ahead of #3`
Source Survey Docs:
- `docs/2026-04-23/authority-alignment-benchmark-operating-model-hardening-3pass-audit.md`
- `docs/2026-04-23/stage234-session-memory-max-utilization-deep-dive-adversarial-3pass-audit.md`
Evidence Artifacts:
- `modules/core/cross_stage_authority_packet.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_post_pass_runtime.py`
- `scripts/archive_benchmark_record.py`
- `scripts/benchmark_archive_runtime.py`
- `scripts/diff_canary_summaries.py`
- `scripts/regression_validation_tiers.py`
- `benchmarks/README.md`
- `benchmarks/benchmark_index.csv`
- `tests/test_archive_benchmark_record.py`
- `tests/test_diff_canary_summaries.py`
- `tests/test_regression_validation_tier_contract.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py`
- `tests/test_stage4_post_processor.py`
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: authority-alignment-benchmark-operating-model-hardening
  depends_on: []
  tranches:
    - id: authority-benchmark-proof-contract-freeze
      title: Authority and benchmark proof contract freeze
    - id: benchmark-record-comparison
      title: Benchmark-record comparison surface
    - id: rerun-diff-watchpoint-contract
      title: Rerun diff and watchpoint contract
    - id: operator-facing-benchmark-hardening
      title: Operator-facing benchmark hardening surface
    - id: downstream-proof-gate-alignment
      title: Downstream proof gate alignment
  github_issue: 5
```

## 1. Intent

- Convert GitHub issue `#5` into one execution-ready SSOT that governs authority alignment proof, benchmark archive comparison, rerun diff normalization, and regression watchpoint hardening.
- Make the queue reflect the real dependency graph: this lane sits upstream of `stage234-session-memory-max-utilization`.
- Keep the lane narrow and proof-first. This is not a request to reopen every historical authority document as active realization work.

## 2. Baseline Facts

- GitHub issue `#5` is open and explicitly asks for authority surface documentation, carryover hardening, benchmark archive comparison, rerun diff, and regression watchpoints.
- Current Stage2, Stage3, and Stage4 already expose real authority transport surfaces:
  - `cross_stage_authority_packet.v1`
  - `episode_state_packet`
  - `state_truth_owner_contract`
- Current benchmark substrate is also live:
  - benchmark records archive to `benchmarks/`
  - each record carries `manifest.json` and `stage_metrics.csv`
  - `benchmark_index.csv` exists as the current quick comparison surface
- The comparison layer is incomplete:
  - canary-summary diff exists
  - benchmark-to-benchmark structured comparison does not yet exist
  - explicit benchmark-hardening watchpoint normalization is still missing
- Current queue posture has now been refreshed to match that reality:
  - `authority-alignment-benchmark-operating-model-hardening` is the visible rank-1 parked proof lane
  - `stage234-session-memory-max-utilization` remains visible as the downstream rank-2 rollout lane
  - ClickUp reflection remains optional and user-triggered only

## 3. Scope

Included:

- cross-stage authority transport and owner-contract runtime surfaces
- benchmark archive scripts, archive corpus shape, and comparison-readiness surfaces
- rerun diff and regression-watchpoint normalization surfaces
- queue artifacts required to expose `#5` as a standalone execution lane

Excluded:

- direct session-memory rollout implementation from `#3`
- donor expansion realization from `#4`
- reopening the historical `00_0420` lane as a current front-active blocker
- broad architectural cleanup unrelated to proof, benchmark, or authority operating model hardening
- ClickUp reflection unless the user explicitly requests it

## 4. Pass 1. Inventory Summary

- Authority owner substrate already spans Stage2, Stage3, and Stage4.
- Benchmark archive substrate already spans scripts, archive records, and auto-archive runner wiring.
- Current comparison is split:
  - canary summary diff is code-backed
  - rerun proof and post-run merge audit are document-backed
  - benchmark-record comparison is missing
- Current watchpoint posture is partial:
  - generic regression tiers exist
  - issue-specific benchmark watchpoints do not yet

## 5. Pass 2. Semantic Classification

- Class A: authority transport and truth-owner surfaces
  - transport payload creation
  - truth packet consumption
  - post-pass owner declaration
- Class B: benchmark archive and record surfaces
  - archive writer
  - archive wrapper
  - runner auto-archive paths
  - benchmark corpus and index
- Class C: comparison and watchpoint surfaces
  - canary diff
  - rerun proof linkage
  - regression-tier metadata
- Class D: downstream dependency governance
  - `#3` memory rollout needs proof-grade measurement from this lane
  - `#4` and `#7` can also benefit from the same benchmark/watchpoint substrate

## 6. Side-Effect Map

- file writes / artifacts:
  - this document wave writes canonical and temp execution docs plus roadmap refreshes
  - later realization tranches will likely add comparison outputs, watchpoint ledgers, or normalized benchmark summaries
- DB / schema / transaction boundaries:
  - no schema change is authorized in the initial proof and comparison tranches
  - benchmark records currently snapshot the DB rather than mutate schema
- JSONL / log / audit sinks:
  - benchmark archives already copy runtime logs and metrics
  - rerun proof linkage may touch audit summaries or benchmark metadata in later tranches
- console / UI / operator output:
  - comparison or watchpoint summaries may later expand canary or runner output
  - initial lane formalization does not require UI mutation
- rollback / recovery / retry:
  - watchpoints must not become hidden runtime blockers in the initial tranches
  - rerun comparison should remain proof-facing, not authority-overriding
- cache / global state:
  - benchmark index and archive roots are the main persistent sidecar surfaces here
  - no provider or runtime cache mutation is authorized in this execution packet
- bootstrap fallback / config-env mutation:
  - `benchmark_archive_runtime.py` already behaves as a soft-fail wrapper
  - no environment mutation is authorized in the initial lane

## 7. Realization Architecture

- Keep the lane proof-first and narrow:
  - authority surface inventory and owner readout normalization
  - benchmark-record comparison
  - rerun diff and watchpoint normalization
- Treat authority surfaces as explicit, inspectable contracts:
  - `cross_stage_authority_packet`
  - `episode_state_packet`
  - `state_truth_owner_contract`
- Compare benchmark records directly, not only canary summary JSONs.
- Normalize rerun and post-run merge audit outputs back into benchmark records or an equivalent comparison surface.
- Expose this lane as an upstream dependency for `#3` without promoting it to front-active implementation authority by default.

## 8. Execution Tranches

1. Authority and benchmark proof contract freeze
   - document current owner surfaces and benchmark archive shape under one narrow lane
2. Benchmark-record comparison surface
   - add or normalize comparator support over `benchmark_index.csv`, `manifest.json`, and `stage_metrics.csv`
3. Rerun diff and watchpoint contract
   - define explicit watchpoint vocabulary and normalize rerun/post-run merge audit linkage
4. Operator-facing benchmark hardening surface
   - make first-owner and regression readouts easier to inspect without elevating telemetry to truth
5. Downstream proof gate alignment
   - wire the lane so `#3`, `#4`, and `#7` can reference the same benchmark and authority proof standard

## 9. Acceptance Criteria

- Benchmark records become structurally comparable beyond canary-summary-only diff.
- Rerun and post-run merge audit outcomes map back into an explicit benchmark-comparison surface.
- Authority owner surfaces are documented and grouped as one operating model rather than scattered historical fragments.
- The active roadmap and queue expose this lane ahead of `stage234-session-memory-max-utilization`.
- No provider-native hidden state or telemetry surface is promoted above explicit truth-owner contracts.

## 10. Verification Plan

- `pytest tests/test_archive_benchmark_record.py -q`
- `pytest tests/test_diff_canary_summaries.py -q`
- `pytest tests/test_regression_validation_tier_contract.py -q`
- `pytest tests/test_stage2_finalizer.py -k "cross_stage_authority_packet" -q`
- `pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -k "cross_stage_authority_packet or capital_truth" -q`
- `pytest tests/test_stage4_post_processor.py -k "state_truth_owner_contract or numeric_carryover" -q`
- sequential low-memory shards only; no `xdist` or parallel pytest
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not treat the historical `00_0420` lane as if it were the current active proof lane.
- Do not confuse benchmark hardening with wholesale architecture cleanup.
- Do not use canary-summary diff alone as the benchmark comparator endpoint.
- Do not mutate DB truth-owner semantics in the initial proof tranches.
- Do not sync ClickUp unless the user explicitly requests it.
- Do not start code realization from this SSOT without a fresh 3-pass re-audit against the live workspace state.

## 12. Temp Queue Notes

- temp status: `parked future wave`
- cleanup condition:
  - keep the mirror while this lane remains the visible upstream proof governor for `#3`
  - remove or replace it only after closure or superseding narrower tranche SSOTs
- roadmap dependency:
  - ranked first because it is an honest proof and dependency blocker for the current `#3` lane
  - `stage234-session-memory-max-utilization` now depends on this lane explicitly

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the 3-pass audit on the source survey and this SSOT
  - confirm at least 95% confidence against current `main`
  - then refresh `Resume Commit` and `Resume Drift Summary` before patching code from this document
