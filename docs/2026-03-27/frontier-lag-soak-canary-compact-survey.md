# Frontier Lag Soak Canary Compact Survey

- date: 2026-03-27
- status: final
- track: system
- mode: survey-only
- confidence: 95
- scope: runner/control seam, lightweight config seam, observability seam
- question: can the workspace support a low-cost frontier-lag soak canary for continuity and state persistence before a broader implementation wave

## Executive Verdict

Yes, with bounded ROI.

The workspace already has enough runner and analysis surface to avoid a net-new harness. The best base is `scripts/run_auto_frontier_lag_harness.py`, with `scripts/run_stage34_canary.py` as the smaller proof seam for Stage 3 -> 4 frontier closure.

The reuse value is real, but the current harnesses do not yet expose the three controls that the proposed special canary needs:

1. harness-level all-flash model override
2. harness-level 1000-char manuscript policy override
3. harness-level disable list for heavier Stage 4 paths

That means the idea is viable, but should be framed as a bounded harness extension, not a zero-work toggle.

## Evidence Sources

- `scripts/run_stage34_canary.py:95`
  `run_canary()` boots live app surfaces and drives `_one_stop_pipeline_frontier_lag()`.
- `scripts/run_stage34_canary.py:247`
  `_clamp_frontier_lag_to_target_ep()` already provides a bounded frontier close seam.
- `main_a.py:4243`
  `_run_frontier_lag_arc_step()` is the per-arc frontier step.
- `main_a.py:4277`
  `_prepare_frontier_lag_batch_request()` already shapes arc-count and batch-size limits.
- `main_a.py:4389`
  `_one_stop_pipeline_frontier_lag()` is the real repeat loop.
- `main_a.py:4437`
  requested arc limit already has an explicit stop reason.
- `scripts/run_auto_frontier_lag_harness.py:320`
  `run_worker()` already owns N-arc frontier execution.
- `scripts/run_auto_frontier_lag_harness.py:483`
  `capture_poll_snapshot()` already collects live progress signals.
- `scripts/run_auto_frontier_lag_harness.py:532`
  `classify_poll_transition()` already defines watchdog stop logic.
- `scripts/run_auto_frontier_lag_harness.py:564`
  `analyze_project()` already merges runtime evidence and sink-alignment analysis.
- `scripts/run_auto_frontier_lag_harness.py:777`
  `write_execution_ssot()` already emits a dated runtime-analysis doc.
- `config/models.yaml:38`
  `manager` is already on `gemini-2.5-flash`.
- `config/models.yaml:39`
  `chief_writer` is still on `gemini-3.1-pro-preview`.
- `config/models.yaml:56`
  `writer` is on `gemini-2.5-flash`.
- `config/settings/validation.yaml:13`
  manuscript minimum is still `4000`.
- `config/settings/validation.yaml:15`
  manuscript target is still `5000`.
- `modules/core/constants.py:284`
  Stage 4 writer model is resolved from `agents.chief_writer`.
- `modules/core/constants.py:285`
  Stage 2 main model is resolved from `agents.four_phase_arc_generator`.
- `modules/core/stage4_orchestrator.py:2335`
  Stage 4 session bootstrap uses `STAGE4_FIXED_WRITER_MODEL`.
- `modules/core/sovereign_bootstrap_runtime.py:95`
  Stage 2 main agents use `AIModels.STAGE2_MAIN_MODEL`.
- `modules/core/pass_rate_monitor.py:16`
  `pass_rate_monitor.json` is explicitly non-authoritative.
- `modules/api/control_plane_contract.py:52`
  `episode_production.jsonl` is a declared control-plane evidence surface.
- `modules/api/control_plane_contract.py:60`
  `runtime_audit_summary` is a point-in-time snapshot, not durable authority.
- `modules/core/failure_analyzer.py:1260`
  `sink_alignment_summary()` already knows how to compare Stage 3/4 sinks.
- `modules/core/db_manager.py:601`
  `episode_bibles` save path exists and is queryable.
- `modules/core/db_manager.py:1319`
  `state_logs` save path exists and is queryable.
- `modules/core/world_state.py:768`
  `world_state` update path exists and can be replayed from episode bibles.
- `tests/test_auto_frontier_lag_harness.py:208`
  the current auto harness worker path is already regression-covered.
- `tests/test_run_stage34_canary.py:46`
  the Stage 3 -> 4 clamp behavior is already regression-covered.

## Track 1: Runner And Control Seam

Current reusable pieces are stronger than expected. The important new finding is that the core repeat engine already exists in `main_a.py`; a new orchestration engine is not the right direction.

- `scripts/run_stage34_canary.py` already proves a bounded Stage 3 -> 4 frontier run, with a target-episode clamp and a post-run analyzer.
- `scripts/run_auto_frontier_lag_harness.py` already owns:
  - plan generation
  - worker subprocess boot
  - watchdog polling
  - stall/failure classification
  - sink-alignment analysis
  - dated SSOT emission
- `main_a.py` already owns the repeat loop and stop logic:
  - per-arc step at `main_a.py:4243`
  - batch and arc-limit shaping at `main_a.py:4277`
  - loop body at `main_a.py:4389`
  - explicit `requested_arc_limit_reached` stop at `main_a.py:4437`
- The watchdog contract is explicit:
  - default review cadence is `30 * 60` seconds at `scripts/run_auto_frontier_lag_harness.py:36`
  - prompt-blocked detection is built from `PROMPT_WAIT_MARKERS` at `scripts/run_auto_frontier_lag_harness.py:40`
  - two idle windows escalate to `stalled` at `scripts/run_auto_frontier_lag_harness.py:532`

Conclusion for control seam:

- `run_auto_frontier_lag_harness.py` is the correct base for a soak canary.
- `run_stage34_canary.py` is still useful as the smaller proof seam and regression harness.
- the correct implementation style is `frontier-lag existing seam rewrap`, not `new engine`

## Track 2: Lightweight Config Seam

This is the main missing piece.

What already exists:

- Several analysis-side roles already default to flash:
  - `manager` at `config/models.yaml:38`
  - `writer` at `config/models.yaml:56`
  - `FLASH_ANALYSIS_MODEL` at `modules/core/constants.py:260`
- The harness already applies a semantic Stage 0 profile:
  - existing BI/TR replay at `scripts/run_auto_frontier_lag_harness.py:404`
  - style replay at `scripts/run_auto_frontier_lag_harness.py:433`

What is still fixed too high or too heavy for the proposed canary:

- `chief_writer` is still pro by default at `config/models.yaml:39`
- Stage 4 binds to that value through `STAGE4_FIXED_WRITER_MODEL` at `modules/core/constants.py:284` and `modules/core/stage4_orchestrator.py:2335`
- Stage 2 main agents bind to `STAGE2_MAIN_MODEL` at `modules/core/constants.py:285` and `modules/core/sovereign_bootstrap_runtime.py:95`
- Manuscript policy is still global runtime policy:
  - minimum `4000` at `config/settings/validation.yaml:13`
  - target `5000` at `config/settings/validation.yaml:15`

Important negative finding:

- `scripts/run_auto_frontier_lag_harness.py` has no harness argument for model override.
- It also has no harness argument for manuscript-length override.
- It also has no harness argument for disabling heavier Stage 4 branches.
- Its current `default_profile()` is investment-specific, not generic or wuxia-ready, at `scripts/run_auto_frontier_lag_harness.py:62`.

Conclusion for config seam:

- A special soak canary is feasible only if it adds a bounded override seam.
- The cleanest candidates are:
  - temporary config overlay for models and validation length
  - or harness-local monkeypatch/override injection before boot
- Without that, "all flash + 1000 chars" is not currently a real operating mode.

## Track 3: Observability Seam

Observability is good for liveness and Stage 3/4 sink proof, but incomplete for long-memory/state-soak claims.

What the current harness already measures:

- session log path, tail, and growth at `scripts/run_auto_frontier_lag_harness.py:483`
- blueprint and draft counts at `scripts/run_auto_frontier_lag_harness.py:483`
- Stage 3 and Stage 4 attempt counts at `scripts/run_auto_frontier_lag_harness.py:483`
- director row counts at `scripts/run_auto_frontier_lag_harness.py:483`
- runtime audit event count at `scripts/run_auto_frontier_lag_harness.py:483`
- prompt-blocked state at `scripts/run_auto_frontier_lag_harness.py:529`
- sink-alignment summaries through `FailureAnalyzer.sink_alignment_summary()` at `scripts/run_auto_frontier_lag_harness.py:564`

Authority model is also reasonably clear:

- `pass_rate_monitor.json` is non-authoritative at `modules/core/pass_rate_monitor.py:16`
- `runtime_audit_summary` is not durable authority at `modules/api/control_plane_contract.py:60`
- durable proof surfaces include `stage_attempts`, `director_selections`, and `episode_production.jsonl` through `FailureAnalyzer` and the control-plane contract

What is missing for a true continuity/state soak:

- `run_auto_frontier_lag_harness.py` does not currently read or score:
  - `episode_bibles`
  - `state_logs`
  - `world_state`
- Those surfaces do exist and are already persisted:
  - `save_episode_bible()` at `modules/core/db_manager.py:601`
  - `save_state_log_with_summary()` at `modules/core/db_manager.py:1319`
  - `world_state.update_from_state_changes()` at `modules/core/world_state.py:768`
- `world_state` can also replay from `episode_bibles`, which is useful for rollback/continuity soak checks, at `modules/core/world_state.py:1324`

Conclusion for observability seam:

- The current harness can prove liveness, boundary reach, and Stage 3/4 sink alignment.
- It cannot yet prove long-memory consistency without a new post-run state audit block.

## Minimal Realization Path

The lowest-risk implementation path is:

1. Fork or extend `scripts/run_auto_frontier_lag_harness.py` instead of starting from scratch.
2. Keep `main_a.py` frontier logic as-is and wrap it more lightly instead of moving logic out of the app.
3. Add a named special profile for the soak lane instead of overloading the current investment default profile.
4. Add bounded override inputs for:
   - Stage 2 / Stage 4 model tier
   - manuscript min/target length
   - optional heavy-path disable list
5. Add a post-run state audit that queries:
   - `episode_bibles`
   - `state_logs`
   - `world_state`
6. Start with a 3-arc pilot, then move to 20 arcs only if the pilot is stable.

## ROI Assessment

ROI is real if the goal is narrow.

- Good fit:
  - frontier lag stability
  - retry and stall detection
  - state drift detection
  - continuity drift across multiple arcs
  - rollback/replay sanity
- Weak fit:
  - manuscript quality judgment
  - full production-grade prose quality
  - heavy-direction Stage 4 behavior under normal cost settings

Practical verdict:

- as a low-cost continuity/state soak rig: yes
- as a replacement for production-quality validation: no

## Recommendation

Do not implement the special soak canary in the middle of the current live canary.

Wait for the current wuxia canary thread to finish, then open one compact execution SSOT for a bounded harness extension with this exact scope:

- base: `scripts/run_auto_frontier_lag_harness.py`
- overrides: model tier, manuscript length, heavy-path toggle set
- evidence sinks: add `episode_bibles`, `state_logs`, `world_state`
- rollout: 3-arc pilot first, 20-arc soak only after the pilot passes

## 3-Pass Audit

### Pass 1: Fact Extraction

- runner/control evidence was verified directly from `run_stage34_canary.py` and `run_auto_frontier_lag_harness.py`
- config evidence was verified directly from `config/models.yaml`, `config/settings/validation.yaml`, `modules/core/constants.py`, and runtime bootstrap files
- observability evidence was verified directly from `pass_rate_monitor.py`, `control_plane_contract.py`, `failure_analyzer.py`, `db_manager.py`, and `world_state.py`

Result: pass

### Pass 2: Contradiction Check

- no contradiction found between the runner scripts and the current config contracts
- no evidence found that a harness-level all-flash or 1000-char override already exists
- no evidence found that current auto harness analysis already audits `episode_bibles`, `state_logs`, or `world_state`

Result: pass

### Pass 3: Decision Audit

- the recommendation stays within survey-only scope
- the recommendation does not assume broad refactor or active code changes
- the proposed next step is bounded and uses an existing harness as the base

Result: pass

Final decision: save approved

## Merge Audit 2026-03-27

Three external lane rechecks were merged against this survey after the initial save.

- Track 1 runner/control seam recheck: corroborated
- Track 2 lightweight config seam recheck: corroborated
- Track 3 observability seam recheck: corroborated

Merge-audit result:

- no contradiction was found against the current survey conclusions
- one minor stale reference was corrected:
  - `modules/core/world_state.py:1325` -> `modules/core/world_state.py:1324`
- the governing recommendation remains unchanged:
  - finish the current wuxia canary first
  - then open one bounded compact execution SSOT for the soak-canary harness extension
