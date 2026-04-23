# Authority Alignment Benchmark Operating Model Hardening Execution SSOT

Date: 2026-04-23
Status: execution-ready (3-pass audited; parked future wave; upstream proof and benchmark governor lane; read-only benchmark comparator plus first watchpoint seed landed on 2026-04-23; note-backed rerun, guarded-summary staleness, explicit evidence-json companion watchpoints, benchmark companion-link sidecars, and operator-facing report/markdown/comment helpers landed later the same day)
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
- `scripts/compare_benchmark_records.py`
- `scripts/report_benchmark_operator_lines.py`
- `scripts/render_benchmark_operator_comment_md.py`
- `scripts/post_benchmark_operator_comment.py`
- `scripts/diff_canary_summaries.py`
- `scripts/regression_validation_tiers.py`
- `benchmarks/README.md`
- `benchmarks/benchmark_index.csv`
- `tests/test_archive_benchmark_record.py`
- `tests/test_compare_benchmark_records.py`
- `tests/test_report_benchmark_operator_lines.py`
- `tests/test_render_benchmark_operator_comment_md.py`
- `tests/test_post_benchmark_operator_comment.py`
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
  - a first read-only benchmark-to-benchmark comparator now exists over `benchmark_index.csv`, `manifest.json`, and `stage_metrics.csv`
  - a first comparator-backed watchpoint vocabulary now exists for coarse status, tag, proof-digest, Stage4 regression signals, note-backed rerun progression, guarded-summary staleness attention, explicit evidence-json companion summaries, and sidecar-linked companion loading
  - read-only operator-facing wrappers now exist for batch report lines, GitHub-comment-ready markdown rendering, and optional issue comment posting over the same benchmark surfaces
  - full markdown post-run merge-audit mapping is still missing
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
  - benchmark-record comparison now has a first read-only comparator seed
  - rerun proof and post-run merge audit are still document-backed
- Current watchpoint posture is partial:
  - generic regression tiers exist
  - the benchmark comparator now emits a small first watchpoint vocabulary plus note-backed rerun, stale-summary attention, explicit evidence-json companion summaries, and auto-follow for explicit companion-link sidecars
  - operator-facing wrappers now expose the same surface as one-line report payloads, issue-comment-ready markdown, and optional `gh issue comment` posting helpers without changing comparator or audit semantics
  - full rerun and markdown post-run merge-audit linkage is still not normalized into comparator outputs, and live record-level link population is still manual

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
  - benchmark-record comparator
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
   - first seed landed as `scripts/compare_benchmark_records.py`
   - current surface compares `benchmark_index.csv`, `manifest.json`, and `stage_metrics.csv` in read-only mode
   - current surface also emits a first watchpoint vocabulary for coarse status/tag shifts plus Stage4 attempt, pass-like, cost, proof-digest attention, note-backed rerun progression, guarded-summary staleness attention, explicit evidence-json companion summaries, and sidecar-linked companion loading
   - explicit companion sidecars can now be written next to archived benchmark records without mutating benchmark/index truth
   - next step is to normalize markdown post-run merge-audit mapping on top of this comparator-backed rerun/watchpoint surface
3. Rerun diff and watchpoint contract
   - extend the first watchpoint vocabulary beyond coarse comparator-backed signals, shallow rerun markers, explicit evidence-json companions, and sidecar link metadata
   - normalize markdown post-run merge audit linkage
4. Operator-facing benchmark hardening surface
   - first seed landed as `scripts/report_benchmark_operator_lines.py`
   - current surface also includes `scripts/render_benchmark_operator_comment_md.py` and `scripts/post_benchmark_operator_comment.py` so the same benchmark operator payload can be previewed, rendered as markdown, or posted to GitHub issue comments without redefining truth or gate semantics
   - default snapshot cadence is bounded and manual: refresh the operator snapshot after a landed comparator/watchpoint/helper tranche, after live benchmark companion-link population changes, or immediately before posting a new `#5` issue snapshot
   - operator order stays fixed as `report_benchmark_operator_lines.py` -> `render_benchmark_operator_comment_md.py` -> optional `post_benchmark_operator_comment.py --post`
   - explicit helper ergonomics now also include `--latest-live-pair` on the report/render/post wrappers for the common "latest two live benchmark records" snapshot path without changing default behavior
   - `post_benchmark_operator_comment.py` also now supports `--issue-5-defaults` to fill the repo-local `#5` target when omitted, while still requiring explicit `--post` before any GitHub write occurs
   - the common issue-5 snapshot preset is now `--issue-5-snapshot`: on report/render it enables the latest-live-pair path, and on post it enables both the repo-local `#5` target defaults and latest-live-pair while still keeping GitHub writes behind explicit `--post`
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
- `pytest tests/test_report_benchmark_operator_lines.py -q`
- `pytest tests/test_render_benchmark_operator_comment_md.py -q`
- `pytest tests/test_post_benchmark_operator_comment.py -q`
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
