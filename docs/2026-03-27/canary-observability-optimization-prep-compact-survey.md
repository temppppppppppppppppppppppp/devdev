Date: 2026-03-27
Status: final (3-pass audited)
Document Type: system-track compact survey
Canonical Path: `docs/2026-03-27/canary-observability-optimization-prep-compact-survey.md`
Temp Mirror Path: none
Parent Authority:
- `docs/2026-03-27/canary-observability-optimization-prep-compact-survey-order.md`
- `docs/2026-03-27/state-changes-schema-formalization-wave1-execution-ssot.md`
- `docs/2026-03-27/state-and-maturity-execution-roadmap.md`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked narrative-router/config/orientation/runtime/provider/stage surfaces, queue-state.json, logs/artifacts; untracked dated docs, anthropic_vertex provider/tests, probe script, project artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Executive Summary

Current workspace readiness is split cleanly:

- `ready now`
  - baseline canary lanes
  - cost/time/retry measurement
  - quality dashboard interpretation surfaces
  - provider boundary probe matrix for future expansion
- `short additional work`
  - budget gate
  - canary summary diff
- `design needed`
  - shadow replay
  - golden contract fixture pack

The strongest next step after wave1 closure is **two documents**, not one combined implementation wave:

1. one bounded execution SSOT for near-term canary/observability additions
   - budget gate
   - canary summary diff
   - baseline canary reuse as existing substrate, not a new build-out
2. one separate survey order for
   - shadow replay
   - golden contract fixture pack

Reason:
- near-term work can stay read-model or summary-layer bounded
- replay and golden-fixture work cross rollback, DB reset, artifact regeneration, and fixture authority boundaries

## 2. Scope And Exclusions

Inspected surfaces:
- canary execution
  - `scripts/run_stage3_canary.py`
  - `scripts/run_stage34_canary.py`
  - `scripts/run_stage4_canary.py`
  - `modules/core/stage4_canary_tools.py`
  - `scripts/regression_validation_tiers.py`
  - `scripts/probe_claude_vertex_matrix.py`
- measurement and dashboard
  - `modules/core/pass_rate_monitor.py`
  - `modules/api/bridge_server.py`
  - `modules/core/db_manager.py`
  - `modules/core/failure_analyzer.py`
  - `modules/core/quality_dashboard.py`
- fixture and replay adjacent
  - `scripts/prepare_smoke_fixture.py`
  - `scripts/smoke_fixture_contract.py`
  - `scripts/run_stage2_smoke.py`
  - `scripts/run_stage3_smoke.py`
  - `scripts/run_stage4_smoke.py`
  - `modules/core/smoke_fixture_tools.py`
- minimum proof tests
  - `tests/test_run_stage4_canary.py`
  - `tests/test_stage4_canary_tools.py`
  - `tests/test_bridge_quality_summary.py`
  - `tests/test_pass_rate_monitor_rol.py`
  - `tests/test_arc_difficulty.py`
  - `tests/test_probe_claude_vertex_matrix.py`
- directly relevant adjacent tests
  - `tests/test_run_stage3_canary.py`
  - `tests/test_run_stage34_canary.py`
  - `tests/test_smoke_fixture_contract.py`

Read-only evidence also included existing live artifacts:
- `projects/canary_0325/logs/stage34_canary_summary.json`
- `projects/canary_0325_stage4_wave2/logs/canary_summary.json`
- `projects/canary_0325_stage4_wave2/logs/pass_rate_monitor.json`
- `projects/canary_0326_stage3_pfee/logs/stage3_canary_summary.json`
- `projects/코덱스_테스트/logs/smoke_fixture_prep.json`

Exclusions:
- no production code changes
- no tests changed
- no mutation-capable canary or smoke helpers were executed in this survey
- no queue artifact changes
- no new execution SSOT or roadmap promotion

## 3. Classification Table

| Topic | Classification | Basis |
| --- | --- | --- |
| baseline canary | `ready now` | Stage3, Stage4, and Stage3->4 canary runners already exist, persist proof summaries, and are test-covered |
| cost/time/retry measurement | `ready now` | DB, pass-rate cache, runtime audit, and dashboard payloads already expose usable cost, duration, retry, and ROL inputs |
| quality dashboard interpretation | `ready now` | `/quality/dashboard` already returns proof, cost, patch, ROL, calibration, and retrieval views in a read-only operator surface |
| budget gate | `short additional work` | existing metrics are already present; only thresholding and presentation logic are missing |
| canary summary diff | `short additional work` | normalized canary summary JSON already exists; diffing can stay read-only |
| shadow replay | `design needed` | current tooling resets and reruns mutable project copies; no authoritative replay contract exists |
| golden contract fixture pack | `design needed` | current smoke fixture contract only guarantees shallow readiness, not frozen golden outputs or expected proof snapshots |
| provider boundary probe matrix | `ready now` | probe helper and tests already exist for future expansion, but live pass/fail remains environment-dependent |

## 4. Ready-Now Asset Ledger

| Asset | Owner Files | Entry Command Or Function | Mode | Evidence Artifact Produced | Usable Immediately After Wave1 Closure? | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| baseline canary lanes | `scripts/run_stage3_canary.py`; `scripts/run_stage34_canary.py`; `scripts/run_stage4_canary.py`; `modules/core/stage4_canary_tools.py` | `python scripts/run_stage3_canary.py ...`; `python scripts/run_stage34_canary.py ...`; `python scripts/run_stage4_canary.py ...`; `build_stage3_canary_summary()`; `build_stage4_canary_summary()`; `build_stage4_branch_inventory()` | mutation-capable runners plus read-only summary builders | `logs/stage3_canary_summary.json`; `logs/stage34_canary_summary.json`; `logs/canary_summary.json`; `logs/canary_companion_audit.json`; optional branch inventory JSON | `yes, bounded` | Strong enough for disposable-copy stabilization checks. Explicitly not a backend-wide proof net. Stage4 summary only probes Stage3 by sink alignment unless the Stage34 lane is used. |
| cost/time/retry measurement | `modules/core/pass_rate_monitor.py`; `modules/core/db_manager.py`; `modules/core/failure_analyzer.py`; `modules/core/stage4_canary_tools.py` | `PassRateMonitor.record_attempt()`; `PassRateMonitor.get_patch_effectiveness()`; `PassRateMonitor.get_episode_rol_snapshot()`; `PassRateMonitor.get_arc_cost_correlation()`; `DBManager.get_cost_summary()`; `DBManager.get_latest_stage4_gate_repair_snapshot()` | mixed: runtime writers plus read-only readers | `logs/pass_rate_monitor.json`; DB `llm_calls`; DB `cost_log`; DB `stage_attempts`; canary summary telemetry blocks | `yes, with authority caveat` | Cost and duration are already measurable. Retry metadata is split between `retry_budget_axes` and DB-only rationale fields. `pass_rate_monitor.json` is explicitly non-authoritative, but still useful as a companion cache. |
| quality dashboard interpretation surfaces | `modules/api/bridge_server.py`; `modules/core/quality_dashboard.py`; `modules/core/failure_analyzer.py`; `modules/core/db_manager.py` | `GET /quality/summary`; `GET /quality/dashboard`; `_build_quality_dashboard_payload()` | read-only endpoint over mixed authoritative and companion sinks | dashboard payload with `quality_summary`, `proof_status`, `sink_alignment_summary`, `runtime_audit_summary`, `cost_summary`, `patch_effectiveness`, `episode_rol`, `arc_cost_correlation`, `gate_repair_summary`, calibration | `yes, as operator read model` | Endpoint is already tested to avoid DB mutation. Use it as companion interpretation, not sole authority, because some sections depend on `quality_metrics.jsonl` and `pass_rate_monitor.json`. |
| provider boundary probe matrix | `scripts/probe_claude_vertex_matrix.py`; `tests/test_probe_claude_vertex_matrix.py` | `python scripts/probe_claude_vertex_matrix.py [--json] [--output <file>]` | read-mostly, network-capable, optional local file write | terminal report or optional JSON file | `yes, for expansion planning only` | Good enough to test model/region/provider reachability before adding more canary lanes. Not a stabilization proof surface by itself. |

## 5. Short-Additional Work Map

### Budget Gate

| Field | Finding |
| --- | --- |
| smallest plausible insertion point | `modules/api/bridge_server.py` next to `_build_cost_summary_payload()`, `_build_episode_rol_payload()`, and `_build_gate_repair_summary()` inside `_build_quality_dashboard_payload()` |
| existing metrics already sufficient? | `yes` |
| new script/helper needed? | `small helper only`; no schema or new sink required |
| bounded blast radius | dashboard read-model only if implemented there first |
| why short additional work | cost, duration, retry, and repair metadata already exist in `cost_summary`, `episode_rol`, `gate_repair_summary.retry_budget_axes`, and retrieval budget ledgers. The missing piece is threshold semantics plus one compact summary payload. |

Recommendation:
- treat the first version as a **dashboard or canary-summary budget status**, not runtime enforcement
- do not turn this into a run-blocking gate until upstream ownership and threshold authority are defined

### Canary Summary Diff

| Field | Finding |
| --- | --- |
| smallest plausible insertion point | `modules/core/stage4_canary_tools.py` near `build_stage4_branch_inventory()` or a new read-only sibling script that compares existing summary JSON files |
| existing metrics already sufficient? | `yes` |
| new script/helper needed? | `yes, but read-only` |
| bounded blast radius | summary comparison only; no app/runtime path changes |
| why short additional work | canary summaries are already normalized around hard gates, sink alignment, rationale, companion audit, patch trace, and proof scope. A diff only needs to compare two summary payloads and render operator-facing deltas. |

Suggested first diff scope:
- `hard_gates.status`, `errors`, `warnings`
- sink-alignment issue counts
- patch-trace counts and strategy counts
- retry-required coverage
- proof-status rollup

## 6. Design-Needed Concept Ledger

### Shadow Replay

| Field | Finding |
| --- | --- |
| why current assets are insufficient | current canary helpers are rerun-based, not replay-based. They copy a project, delete Stage3/4 outputs, boot the live app, and regenerate artifacts. The smoke lane is also mutation-capable rather than replay-capable: Stage2 has only a partial reset helper, Stage3 has no replay reset, Stage4 only clears manuscripts, and smoke readiness ignores Stage2/3/4 telemetry dirtiness. Safe-ops surfaces only preview rollback impact; they do not provide a replay contract or a replayer. |
| authoritative inputs needed | immutable source snapshot or copy contract; session-scoped attempt ledger; artifact hash and path truth; DB table restore map; selection/final-authority linkage; replay target selector |
| mutation/risk boundary | high. Replay would touch rollback/reset semantics, DB rebuild or table rewrites, artifact regeneration, and possibly safe-ops boundaries across Stage2/3/4 data |
| separate survey before implementation? | `yes` |

Interpretation:
- `get_rollback_impact()` is useful evidence for blast radius
- it is not enough to justify replay implementation
- replay needs its own authority contract before code work

### Golden Contract Fixture Pack

| Field | Finding |
| --- | --- |
| why current assets are insufficient | current fixture preparation only guarantees a shallow readiness contract: arc count, latest blueprint number, and zero baseline manuscripts. That readiness check does not validate Stage2/3/4 attempt history, director selections, or artifact dirtiness. Smoke runners then mutate the bounded target DB and artifacts. Desktop packaging copies the canonical smoke source as a disposable seed, but there is still no immutable golden output pack, expected hashes, expected summary snapshots, or pass/fail baselines. |
| authoritative inputs needed | canonical source fixture set; frozen expected canary summaries; expected dashboard payload slices; artifact/hash expectations; refresh policy; owner for provider-specific variants |
| mutation/risk boundary | medium-high. Turning live smoke/canary assets into golden fixtures changes authority over test assets, refresh cadence, and what counts as regression truth |
| separate survey before implementation? | `yes` |

Interpretation:
- `scripts/prepare_smoke_fixture.py` and `modules/core/smoke_fixture_tools.py` are a strong substrate
- they are not yet a golden contract pack
- the missing piece is frozen expectation authority, not just more copies of fixture projects

## 7. Side-Effect Coverage

### Current Canary Helpers Mutate Project State

Confirmed:
- Stage3/Stage4/Stage34 canary prep copies source projects and deletes Stage3/4 DB rows, logs, memory, drafts, and artifacts on the target copy
- Stage4 and Stage34 canary runs boot live app surfaces, patch `input`, save pass-rate monitor snapshots, flush audit buffers, and persist summary JSON
- smoke runners mutate the bounded smoke target project DB and artifact directories by design
- smoke readiness today is shallow: it does not reject accumulated Stage2/3/4 telemetry or artifact-history dirtiness beyond the baseline manuscript count

Implication:
- current canary and smoke lanes are safe only when aimed at disposable targets
- they are not read-only observability tools
- the current smoke lane is not a shadow-replay lane; the closer replay substrate is the canary copy-and-reset helper family

### Current Summaries Already Persist Proof Artifacts

Confirmed artifact classes:
- canary summaries
- companion audit summaries
- runtime audit summaries
- pass-rate monitor JSON
- quality metrics JSONL
- DB `stage_attempts`, `director_selections`, `llm_calls`, and `cost_log`

Implication:
- the workspace already has enough persisted proof material to support a summary diff or dashboard budget status without adding a new persistence substrate

### Dashboard Payloads Depend On Mixed Authority Levels

Confirmed:
- DB-backed sections such as `quality_summary`, `cost_summary`, and gate-repair snapshots are stronger authority
- `pass_rate_monitor.json` is explicitly documented as non-authoritative
- `quality_metrics.jsonl` is a companion sidecar used for dashboard trend views
- `FailureAnalyzer` intentionally cross-checks these mixed sinks and reports mismatch counts

Implication:
- dashboard interpretation is ready now
- but operator wording for new budget/proof features should stay explicit about companion vs authoritative truth

### Replay-Oriented Ideas Would Cross Rollback And Regeneration Boundaries

Confirmed:
- `DBManager.get_rollback_impact()` only previews deletion counts
- safe-ops preview surfaces rollback/wipe/reset/rewind impact, but does not execute a replay contract
- canary prep helpers already show how much DB/file cleanup is involved before rerun

Implication:
- shadow replay is not a bounded extension of the current canary helpers
- it needs separate authority and side-effect design work first

## 8. Next-Doc Recommendation

Recommended split after wave1 closure:

### Document A

Type:
- bounded execution SSOT

Scope:
- near-term canary/observability work only
- budget gate
- canary summary diff
- operator-facing reuse of the existing baseline canary substrate

Why:
- all required evidence already exists
- implementation can stay read-only or summary-layer bounded
- verification can use existing canary summary JSON and dashboard tests

### Document B

Type:
- separate survey order

Scope:
- shadow replay
- golden contract fixture pack

Why:
- both items need fresh authority decisions
- both items cross replay/reset/fixture-governance boundaries
- combining them with the near-term wave would blur a small implementation lane into a new design wave

Decision:
- choose the **two-document path**
- do **not** promote replay or golden-fixture work into the same execution SSOT as budget gate and canary summary diff

## 9. Confidence And Limits

Estimated confidence: `97%`

Reasons confidence is high:
- required surfaces were inspected directly
- existing live canary artifact files were inspected directly
- required proof tests were inspected directly
- no classification depends on unverified runtime mutation during this survey

Limits:
- mutation-capable canary and smoke helpers were not executed because this order forbids it
- provider probe live success remains environment-dependent; only code path and test coverage were inspected
- some localized strings render inconsistently in shell output, so this survey relied on structural fields, function behavior, JSON keys, and tests rather than shell-rendered localized prose
- one wording drift remains in observability semantics: `pass_rate_monitor` is documented as non-authoritative while some runtime summary wording still lists it inside the broader attempt-sink set

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- document type matches a survey-only compact readiness classification
- required section order is present
- implementation authority is not assumed
- PASS

### Pass 2. Evidence and Consistency
- required surfaces and minimum proof tests were inspected
- ready-now, short-additional, and design-needed claims are bounded to live code, tests, and existing artifact files
- queue artifacts were not changed
- PASS

### Pass 3. Execution and Readability
- document answers all five success questions from the order
- near-term vs design-needed split is actionable
- side-effect boundaries are explicit enough for later promotion
- PASS
