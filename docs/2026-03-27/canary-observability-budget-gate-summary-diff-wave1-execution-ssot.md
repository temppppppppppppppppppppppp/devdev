Date: 2026-03-27
Status: closed (realized; closure-audited)
Document Type: system-track execution SSOT
Canonical Path: `docs/2026-03-27/canary-observability-budget-gate-summary-diff-wave1-execution-ssot.md`
Temp Mirror Path: `docs/temp/canary-observability-budget-gate-summary-diff-wave1-execution-ssot.md`
Promotion Basis:
- `docs/2026-03-27/canary-observability-optimization-prep-compact-survey-order.md`
- `docs/2026-03-27/canary-observability-optimization-prep-compact-survey.md`
Authority Note:
- This SSOT is derived from read-only code and artifact re-audit.
- It intentionally excludes shadow replay and golden contract fixture design work.

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked narrative-router/config/orientation/runtime/provider/stage surfaces, queue-state.json, logs/artifacts; untracked dated docs, anthropic_vertex provider/tests, probe script, project artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Source Survey Docs:
- `docs/2026-03-27/canary-observability-optimization-prep-compact-survey-order.md`
- `docs/2026-03-27/canary-observability-optimization-prep-compact-survey.md`
- `docs/2026-03-27/state-and-maturity-execution-roadmap.md`

Evidence Artifacts:
- `modules/api/bridge_server.py`
- `scripts/diff_canary_summaries.py`
- `modules/core/stage4_canary_tools.py`
- `modules/core/db_manager.py`
- `modules/core/pass_rate_monitor.py`
- `modules/core/failure_analyzer.py`
- `tests/test_bridge_quality_summary.py`
- `tests/test_diff_canary_summaries.py`
- `tests/test_stage4_canary_tools.py`
- `tests/test_run_stage4_canary.py`
- `tests/test_run_stage34_canary.py`
- `projects/canary_0325/logs/stage34_canary_summary.json`
- `projects/canary_0325_stage4_wave2/logs/canary_summary.json`
- `projects/canary_0325_stage4_wave2/logs/pass_rate_monitor.json`
- `projects/canary_0326_stage3_pfee/logs/stage3_canary_summary.json`

Side-Effect Coverage: covered

## 1. Intent

Realize the smallest safe canary-observability follow-up wave.

The wave goal is:
- add one operator-facing budget status summary to the existing quality dashboard
- add one read-only canary summary diff path over existing summary artifacts
- reuse the existing canary and dashboard substrate without opening a replay or fixture-design wave

This wave is intentionally bounded:
- read-model or summary-layer only
- no runtime-enforced budget blocking
- no new persistence substrate
- no replay or golden-fixture authority work

## 2. Baseline Facts

- `_build_quality_dashboard_payload()` in `modules/api/bridge_server.py` already assembles the relevant budget-adjacent payloads:
  - `cost_summary`
  - `episode_rol`
  - `gate_repair_summary`
- `build_stage3_canary_summary()`, `build_stage4_canary_summary()`, and `build_stage4_branch_inventory()` in `modules/core/stage4_canary_tools.py` already normalize the proof material the diff wave needs:
  - hard gate status
  - sink-alignment rollups
  - patch-trace rollups
  - retry-required coverage
  - proof-status rollups
- existing proof tests already cover the two main operator surfaces this wave intends to extend:
  - dashboard summary path
  - Stage3/Stage4 canary summary tooling
- the strongest authority inputs are already present in existing sinks:
  - DB `llm_calls`
  - DB `cost_log`
  - DB `stage_attempts`
  - gate-repair snapshots
  - persisted canary summary JSON
- `pass_rate_monitor.json` remains explicitly non-authoritative and must stay a companion input, not a promoted source of truth
- this item enters a non-empty queue and therefore must be governed by the aggregate roadmap before later code realization starts

## 3. Scope

Included:
- dashboard read-model work in `modules/api/bridge_server.py`
- any tiny read-only helper needed to keep `_build_quality_dashboard_payload()` at the sink-boundary level rather than inlining more logic
- one read-only canary summary comparison shell:
  - preferably a new bounded script such as `scripts/diff_canary_summaries.py`
  - optionally one small shared normalizer in `modules/core/stage4_canary_tools.py` if the script needs it
- targeted regression coverage in:
  - `tests/test_bridge_quality_summary.py`
  - `tests/test_stage4_canary_tools.py`
  - one new diff-specific test file if needed
- queue-governance refresh for:
  - `docs/2026-03-27/state-and-maturity-execution-roadmap.md`
  - `docs/temp/execution-roadmap.md`
  - `docs/temp/queue-state.json`

Excluded:
- shadow replay
- golden contract fixture pack
- runtime-enforced budget blocking
- new canary lanes or new canary target mutation logic
- provider matrix expansion
- smoke fixture redesign
- new DB tables, schema changes, or new JSONL/audit sinks
- broad observability UI redesign outside the current dashboard payload
- the broader `system-maturity-next-band-wave1` uplift wave itself

## 4. Pass 1. Inventory Summary

- relevant dashboard sink-boundary functions already exist in `modules/api/bridge_server.py`:
  - `_build_cost_summary_payload()`
  - `_build_episode_rol_payload()`
  - `_build_gate_repair_summary()`
  - `_build_quality_dashboard_payload()`
- relevant canary summary builders already exist in `modules/core/stage4_canary_tools.py`:
  - `build_stage3_canary_summary()`
  - `build_stage4_canary_summary()`
  - `build_stage4_branch_inventory()`
- live proof artifact families already exist:
  - Stage3 summary JSON
  - Stage4 summary JSON
  - Stage3->4 summary JSON
  - pass-rate companion JSON
- current test substrate already covers the main touched surfaces:
  - dashboard read-only summary behavior
  - Stage4 canary summary generation
  - Stage3 and Stage3->4 canary script behavior

Operational implication:
- this wave does not need a new data source
- it only needs one bounded aggregation helper on the dashboard side and one bounded comparison shell on the canary-summary side

## 5. Pass 2. Semantic Classification

- Class A. Budget Status Read Model
  - derive a compact status block from already-available cost, retry, and repair metrics
  - keep the result explanatory and operator-facing
  - keep authoritative versus companion inputs explicit
- Class B. Canary Summary Diff
  - compare two existing canary summary payloads or files
  - report operator-facing deltas without re-running a canary
  - stay read-only against existing summary JSON
- Class C. Explicitly Deferred Design Work
  - replay, golden fixture authority, or runtime gate enforcement do not belong in this wave
  - if implementation pressure crosses those boundaries, stop and reopen scope

## 6. Side-Effect Map

- file writes / artifacts:
  - source updates in the bounded dashboard and canary-summary surfaces
  - targeted test updates
  - canonical and temp execution-doc refreshes
  - the diff path should default to stdout or returned data, not a new durable artifact sink
- DB / schema / transaction boundaries:
  - none
  - dashboard work must remain read-only against existing DB query helpers
- JSONL / log / audit sinks:
  - none required for this wave
  - existing canary summary JSON remains the consumed proof substrate
- console / UI / operator output:
  - dashboard payload gains one bounded summary section
  - diff shell may emit a bounded console or JSON comparison result
- rollback / recovery / retry:
  - no new retry path is introduced
  - the budget status interprets existing retry and repair metadata only
- cache / global state:
  - `pass_rate_monitor.json` may be consumed as a companion cache
  - this wave must not silently elevate it to authoritative truth
- bootstrap fallback / config-env mutation:
  - none expected

## 7. Realization Architecture

### Budget Status Path

- treat `_build_quality_dashboard_payload()` as the sink boundary
- add one small helper such as `_build_budget_status_payload()` adjacent to the current payload builders
- feed that helper from already-available inputs:
  - `cost_summary`
  - `episode_rol`
  - `gate_repair_summary.retry_budget_axes`
  - retrieval budget data only if it is already present in the existing dashboard assembly path
- keep thresholds local and explicit in wave1
- present the result as operator guidance, not as an execution gate

### Canary Summary Diff Path

- prefer a new read-only bounded shell under `scripts/` rather than expanding `modules/core/stage4_canary_tools.py` into another large owner surface
- if a shared normalizer is unavoidable, keep it small and adjacent to `build_stage4_branch_inventory()`
- compare the first diff version on exactly these domains:
  - `hard_gates.status`
  - hard-gate `errors` and `warnings`
  - sink-alignment issue counts
  - patch-trace exercised/count and strategy counts
  - retry-required coverage
  - proof-status rollup
- diff logic must never call the mutation-capable canary prep or run flows

### Queue and Complexity Rule

- this execution doc becomes a queued item and must be realized under the aggregate roadmap
- relative to `system-maturity-next-band-wave1`, this wave should run first unless the roadmap is explicitly refreshed again
- reason:
  - smaller blast radius
  - stronger immediate verification path
  - shared leverage for later canary-discipline and exercised-path work
- if implementation starts to bloat `_build_quality_dashboard_payload()` or any existing 120+ LOC helper, treat the dashboard helper as a `sink boundary` and split logic instead of growing the hot function

## 8. Execution Tranches

1. Dashboard Budget Status
   - add the bounded helper and payload field
   - define wave1 threshold semantics and status labels
   - keep the wording explicit about authoritative versus companion inputs

2. Read-Only Canary Summary Diff
   - add the comparison shell and any tiny shared normalizer it needs
   - support comparison of existing persisted summary payloads without rerun
   - keep output stable enough for operator use and regression testing

3. Regression Coverage and Queue Proof
   - extend read-only dashboard tests for the new payload field
   - add diff-focused tests over representative summary fixtures or inline payloads
   - refresh roadmap and queue-state artifacts so the queue remains authoritative after promotion

## 9. Acceptance Criteria

- `/quality/dashboard` exposes one new budget-status section built only from pre-existing metrics or summary inputs
- the dashboard path remains read-only:
  - no new DB writes
  - no new schema changes
  - no new JSONL or audit sinks
- the budget-status output explicitly distinguishes authoritative inputs from companion inputs when both are present
- one read-only diff path can compare two existing canary summary payloads or files and report bounded deltas for:
  - hard-gate status
  - sink alignment
  - patch trace
  - retry-required coverage
  - proof-status rollup
- the diff path does not invoke project copy, reset, rerun, or live app boot
- targeted tests cover both the dashboard payload extension and the diff behavior
- queue artifacts are synchronized after the execution doc enters `docs/temp/`

## 10. Verification Plan

- `python -m py_compile modules/api/bridge_server.py modules/core/stage4_canary_tools.py scripts/diff_canary_summaries.py`
- `python -m pytest tests/test_bridge_quality_summary.py -q`
- `python -m pytest tests/test_stage4_canary_tools.py -q`
- `python -m pytest tests/test_run_stage4_canary.py -q`
- `python -m pytest tests/test_run_stage34_canary.py -q`
- if a new diff-only test file is added, run it as a separate sequential shard
- `python scripts/check_utf8_hygiene.py modules/api/bridge_server.py modules/core/stage4_canary_tools.py scripts/diff_canary_summaries.py tests/test_bridge_quality_summary.py tests/test_stage4_canary_tools.py docs/2026-03-27/canary-observability-budget-gate-summary-diff-wave1-execution-ssot.md docs/temp/canary-observability-budget-gate-summary-diff-wave1-execution-ssot.md docs/2026-03-27/state-and-maturity-execution-roadmap.md docs/temp/execution-roadmap.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

Pytest execution rule:
- keep the shards sequential and low-memory
- record the exact shard order in the implementation-close note

## 11. Guardrails

- Do not turn wave1 budget status into a runtime-enforced gate.
- Do not introduce new persistence sinks just to support budget status or diff output.
- Do not let the diff path call mutation-capable canary prep or run logic.
- Do not widen this wave into shadow replay, golden fixture authority, or provider-matrix design work.
- Do not silently upgrade `pass_rate_monitor.json` from companion evidence to authority.
- If the diff implementation requires broad changes inside `build_stage4_canary_summary()` or creates long-function pressure in `modules/api/bridge_server.py`, stop and restructure around a smaller helper or separate bounded shell.

## 12. Temp Queue Notes

- temp status: pending
- cleanup condition: remove the temp mirror only after closure audit confirms code, tests, canonical doc, roadmap, and queue-state coherence
- roadmap dependency: `docs/2026-03-27/state-and-maturity-execution-roadmap.md`

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py`
- queue sync command: `python scripts/sync_temp_queue_state.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: before patching code from this document, re-run the document 3-pass audit against the current workspace state and confirm this SSOT still holds at `>=95%` confidence

## 14. 3-Pass Audit Record

### Pass 1. Structure and Scope
- kept the wave to budget status and read-only summary diff only
- excluded replay, fixture authority, and runtime gate enforcement explicitly
- preserved canonical/temp queue policy
- PASS

### Pass 2. Evidence and Consistency
- execution shape is grounded in the compact survey and live owner files
- dashboard and canary diff insertion points match the currently inspected code
- queue promotion is aligned with the active roadmap model
- PASS

### Pass 3. Execution Readiness
- tranches are bounded and verification-ready
- operator authority wording is explicit
- roadmap-first queue handling is clear
- PASS

## 15. Confidence

Estimated confidence: `97%`

Basis:
- required owner files and tests were inspected directly
- the execution shape stays inside existing read-model and summary substrates
- the strongest risks are deferred explicitly rather than hidden inside this wave

## 16. Promotion Judgment

Promotion result: `promoted`

Reason:
- the compact survey already resolved the main classification question
- this wave has a clear bounded implementation path
- the next useful action is implementation from an execution doc, not another survey on the same narrow scope

## 17. Closure Note

Closure date: `2026-03-27`
Closure result: `closed`

Realized scope:
- added `budget_status` to `/quality/dashboard` as a read-only operator-guidance payload in `modules/api/bridge_server.py`
- kept the dashboard change at the sink-boundary level by adding `_build_budget_status_payload()` rather than inflating `_build_quality_dashboard_payload()` further
- explicitly separated authoritative inputs from companion inputs in the budget payload:
  - authoritative: `cost_summary`, `gate_repair_summary`
  - companion: `episode_rol`, `retrieval_summary`
- added a read-only summary diff shell in `scripts/diff_canary_summaries.py`
- supported three persisted summary shapes without rerun:
  - Stage3 summary
  - Stage4 summary
  - Stage3->4 frontier summary
- kept the diff shell file-read only and outside mutation-capable canary prep/run paths
- added regression coverage for both the dashboard guidance payload and the diff shell

Verification evidence:
- `python -m py_compile modules/api/bridge_server.py` -> PASS
- `python -m pytest tests/test_bridge_quality_summary.py -q` -> `18 passed`
- `python scripts/check_utf8_hygiene.py modules/api/bridge_server.py tests/test_bridge_quality_summary.py` -> PASS
- `python -m py_compile scripts/diff_canary_summaries.py` -> PASS
- `python -m pytest tests/test_diff_canary_summaries.py -q` -> `2 passed`
- `python -m pytest tests/test_stage4_canary_tools.py -q` -> `10 passed`
- `python scripts/check_utf8_hygiene.py scripts/diff_canary_summaries.py tests/test_diff_canary_summaries.py` -> PASS
- `python scripts/diff_canary_summaries.py projects/canary_0326_stage3_pfee/logs/stage3_canary_summary.json projects/canary_0325_stage4_wave2/logs/canary_summary.json` -> sane operator diff output observed

Residual risks and deferred scope:
- wave1 budget thresholds remain local operator guidance, not a runtime authority contract
- summary diff issue counts are comparative rollups, not a semantic severity model
- no replay, golden fixture, provider-matrix expansion, or runtime-enforced gate work landed in this wave
- no orientation-pack refresh is required from this wave because route topology, authority owners, and sink topology were not changed

Behavior judgment:
- dashboard change remains read-only
- diff shell remains file-read only
- no new DB writes, schema changes, JSONL sinks, or canary mutation paths were introduced by this wave
