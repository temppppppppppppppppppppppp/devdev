# Frontier Lag Clean 5-Arc Stabilization Execution SSOT

Date: 2026-04-26
Track: system
Status: implementation-in-progress (T0-T5 realized; T6 proposal store added; T7 projection and continuity canary set added; T8 strict 1-arc smoke passed; T9-A~C realized; T9-D/E/F/G/H guardrails added, including hard runtime worker kill shell; strict 5-arc pending)
Canonical Path: `docs/2026-04-26/frontier-lag-clean-5arc-stabilization-execution-ssot.md`
Temp Mirror Path: `docs/temp/frontier-lag-clean-5arc-stabilization-execution-ssot.md`
Commit State:
- Baseline Commit: `a76689ec6c7d1ff6a55686d9889be15009ebb4b7`
- Baseline Dirty Summary: dirty before this document: `M 0_temp.txt`, untracked lane/report/project artifacts
- Resume Commit: `7dc668c524501dd27db156bdf2c7342e55b791e9`
- Resume Drift Summary: #56/#59 landed and were retired from the active temp queue by PR #85; Frontier Lag is now queue rank 1/front-active. Current-state re-audit on 2026-04-27 confirmed T0-T9/T6/T7 source and targeted regression evidence still match this SSOT, with strict fresh multi-arc proof still pending.
Source Survey Docs:
- `docs/2026-04-26/frontier-lag-clean-5arc-lane-a-failure-forensics.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-lane-b-memory-cache-audit.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-lane-c-methodology-research.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-lane-d-continuity-bridge-design.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-lane-e-clean-harness-design.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-lane-f-governance-audit.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-headquarters-notes.md`
Evidence Artifacts:
- local code verification snippets from the files named in section 2
- returned subagent verification for Stage 4 retry authority surfaces
- T8 strict fresh 1-arc project: `projects/auto_t8_smoke_20260426_214331_1arc`
- T8 runtime analysis SSOT: `docs/2026-04-26/auto-frontier-lag-1arc-runtime-analysis-ssot.md`
Side-Effect Coverage: covered

## 0. Scope

This document turns the six parallel deep-dive reports into an implementation order for making Frontier Lag 5-arc runs clean, observable, and authority-aligned.

Inputs:

- `docs/2026-04-26/frontier-lag-clean-5arc-lane-a-failure-forensics.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-lane-b-memory-cache-audit.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-lane-c-methodology-research.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-lane-d-continuity-bridge-design.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-lane-e-clean-harness-design.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-lane-f-governance-audit.md`
- `docs/2026-04-26/frontier-lag-clean-5arc-headquarters-notes.md`
- Local code verification on `main` at `a76689ec6c7d1ff6a55686d9889be15009ebb4b7`
- One returned subagent verification on Stage 4 retry authority surfaces

Non-scope:

- Do not add desktop UI features in this wave.
- Do not relax Director quality gates to make the harness pass.
- Do not make Python decide narrative PASS or REJECT.
- Do not treat provider context caching as story memory.

## 1. Executive Verdict

Clean 5-arc is not yet a safe default. The blocker is not simply Producer intelligence and not simply Director quality. The failure shape is a multi-authority collapse: Director verdict, Python validator route, retry advisory payloads, structured state, repair contracts, and harness objective semantics can each behave like an authority surface without a single typed hierarchy.

The execution goal is therefore not "make the model obey harder." The goal is to collapse all downstream authority into explicit typed contracts:

- Director verdict remains immutable as a Director output.
- Python may collect, normalize, route, and block unsafe artifact adoption, but may not rewrite Director PASS or REJECT.
- Runtime route status must live beside Director verdict, not inside it.
- Advisory payloads must carry authority level before they can affect retry behavior.
- Harness process success must be separate from objective success.
- Skipped or quarantined arcs must never count as advanced arcs.
- Reusing an existing project must refuse or explicitly reset failed state before a clean-run claim.

## 2. Confirmed Findings

### P0-A: Binding trapdoor can override emergency fallback

Evidence: `modules/domain/agents/three_phase_blueprint_runtime.py:2985`.

When a best blueprint exists and Director score is high enough for emergency fallback, `prev_binding_issue_count > 0` currently sets `pipeline_result["final_verdict"] = "FAILED"` and returns no blueprint. That makes a runtime binding guard effectively rewrite the terminal outcome.

Execution requirement:

- Preserve `director_verdict` and `director_score`.
- Put runtime blocking in `runtime_route_verdict`, `runtime_route_reason`, and `objective_status`.
- If a binding issue prevents artifact adoption, mark objective blocked without pretending Python issued a Director REJECT.

### P0-B: Binding prevalidation rewrites PASS/PASS_WITH_WARNING into PASS_WITH_FIX

Evidence: `modules/domain/agents/unified_blueprint_validator.py:740`.

`_apply_binding_prevalidation_contract` merges Python binding issues into feedback/reason/scope and rewrites PASS-like Director output into `PASS_WITH_FIX`.

Execution requirement:

- Split `director_verdict` from `runtime_route_verdict`.
- Python binding prevalidation may emit `runtime_route_action = repair_required` or `regenerate_required`.
- It may not mutate `director_verdict`, `director_feedback`, or `director_fix_scope`.

### P0-C: Worker process success is conflated with objective success

Evidence: `scripts/run_auto_frontier_lag_harness.py:551`.

The worker writes `"status": "success"` when the process completes. Analysis later fails if the requested arc boundary is not reached, but the manifest still looks successful at the process layer.

Execution requirement:

- Add `process_status`, `process_success`, `objective_status`, `objective_success`, and `objective_root_cause`.
- Keep legacy `status` only as compatibility surface, not as a decision source.

### P0-D: Stage 3 skip can count as arc advancement

Evidence: `main_a.py:4184` and `main_a.py:4248`.

The skip path returns `arcs_advanced_delta = 1` with `manuscripts_delta = 0`. That lets an unproduced arc look advanced.

Execution requirement:

- Strict mode is default.
- Skip/quarantine is survey-only or explicitly requested.
- Skip increments `arcs_skipped`, not `arcs_advanced`.
- Boundary success requires produced downstream artifact progress, not skip progress.

### P0-E: Reuse-existing-project lacks a failed-state guard

Evidence: `scripts/run_auto_frontier_lag_harness.py:211`, `scripts/run_auto_frontier_lag_harness.py:527`, and `modules/core/db_manager.py:1939`.

The harness exposes `--reuse-existing-project` and asserts frontier readiness, while `reset_after()` exists in the DB manager but is not called by the inspected reuse path. This means a reused project can carry stale FAILED Stage 3/4 rows into a later "clean" attempt unless a separate manual reset occurred.

Execution requirement:

- Reuse must refuse if current frontier contains failed Stage 3/4 state.
- Explicit reset requires a separate flag and a target episode, then calls `reset_after(target_ep)` before running.
- The manifest must record `reuse_policy`, `reuse_failed_state_detected`, `reuse_reset_after_ep`, and a project epoch/hash before and after reset.

Confidence note:

- The dedicated subagent verification for this item timed out.
- Local code evidence is enough for execution planning because the harness reuse path was inspected and no reset call was found there.

### P0-F: Continuity bridge can become another advisory blob unless typed

Evidence: Lane D and Lane F convergence.

A bridge that stores "recommended fixes" inside generic advisory flags would recreate the same authority collapse. Bridge proposals must not directly patch facts or downstream state.

Execution requirement:

- Use a dedicated `continuity_bridge_proposals` table.
- Python writes proposals only.
- Director adjudicates proposals.
- `applied_status` changes only after Director approval.
- Allowed fix scopes are `candidate_only` and `escalate_to_human`.

### P1-A: Terminal Stage 3 failure lacks enough artifact evidence

Evidence: Lane A and local runtime path.

The failure identified Jan1/Jan3 conflict, but the terminal Stage 3 failure did not preserve enough selected-candidate artifact evidence for fast root-cause replay.

Execution requirement:

- Add a terminal failure diagnostic snapshot containing selected candidate key, candidate hash, raw candidate excerpt/hash, binding issues, Director verdict layer, runtime route layer, and no official artifact adoption if blocked.

### P1-B: Failure digest can mask the real root cause

Evidence: Lane A and `scripts/run_auto_frontier_lag_harness.py:928`.

`requested_arc_boundary_not_reached` is useful but too broad. It hides the actual Stage 3 cause such as `arc_timeline` mismatch.

Execution requirement:

- Add layered root causes: `objective_root_cause`, `stage_root_cause`, `semantic_root_cause`, `authority_root_cause`.
- The top-level failure digest may stay short, but must point to the detailed diagnostic snapshot.

### P1-C: Session memory and context caching are not sufficient continuity control

Evidence: Lane B.

Stage 4 session memory envelope was applied, but Stage 2/3 were effectively not protected by it. Context cache hits were provider/performance behavior, not continuity authority.

Execution requirement:

- Treat context caching as cost/latency only.
- Add an authoritative head/tail continuity projection for Stage 2 -> Stage 3 -> Stage 4.
- Add continuity canaries keyed to per-arc anchor facts.

### P1-D: Stage 4 retry authority needs explicit discriminator

Evidence: returned subagent verification.

`director_selections.advisory_warnings` is mostly historical companion data, but `stage_attempts.advisory_flags` is saved, hydrated, and consumed by retry routing through fields such as `fix_pack`, `retry_budget_axes`, `repair_contract`, and `scope_authority`. The payload mixes warnings and retry contracts without a universal `authority_level`.

Execution requirement:

- Add `authority_level = advisory | route | verdict | historical_companion` to route-sensitive payloads.
- Consumers must reject or ignore missing authority levels for route-sensitive fields.
- `stage_attempts` remains the final authority sink for retry resume; `director_selections` remains historical companion unless explicitly promoted by a typed contract.

## 3. Execution Order

### T0: Verdict and Route Authority Split

Primary files:

- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/core/stage3_orchestrator.py`
- `tests/test_unified_blueprint_validator_lane_c.py`
- `tests/test_blueprint_patch_mode.py`

Implementation:

- Introduce immutable fields: `director_verdict`, `director_score`, `director_feedback`, `director_fix_scope`.
- Introduce runtime fields: `runtime_route_verdict`, `runtime_route_action`, `runtime_route_reason`, `runtime_route_scope`, `runtime_route_authority`.
- Convert binding prevalidation from verdict rewrite to route annotation.
- Convert emergency fallback blocking from `final_verdict = FAILED` to `objective_status = blocked_by_runtime_guard` while preserving Director layer.
- Any compatibility `final_verdict` must be derived at the boundary with provenance, not used as the internal source of truth.

Acceptance:

- A PASS-like Director verdict plus binding issue keeps `director_verdict` unchanged.
- Python route can block objective success but cannot present itself as Director REJECT.
- Tests assert old mutation path is gone.

### T1: Terminal Stage 3 Diagnostic Snapshot

Primary files:

- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/db_manager.py`
- `tests/test_blueprint_patch_mode.py`
- `tests/test_stage3_orchestrator.py`

Implementation:

- Write a terminal diagnostic snapshot when Stage 3 exhausts retries or runtime route blocks adoption.
- Snapshot must include selected candidate metadata, candidate hash, binding issue categories, Director layer, runtime route layer, and artifact adoption status.
- Do not write rejected/blocking candidates as official blueprint artifacts.
- Link the snapshot path from `stage_attempts.advisory_flags` or an equivalent diagnostic field.

Acceptance:

- A terminal failure has replayable evidence.
- Failure digest points to snapshot path.
- No artifact truth confusion: diagnostic snapshot is not an accepted blueprint.

### T2: Harness Process/Object Split

Primary files:

- `scripts/run_auto_frontier_lag_harness.py`
- `tests/test_auto_frontier_lag_harness.py`

Implementation:

- Worker result writes `process_status` and `process_success`.
- Analyzer writes `objective_status`, `objective_success`, `objective_root_cause`, and `boundary_reached`.
- Legacy `status` is retained but not sufficient for success.
- Failure digest includes both process and objective layers.

Acceptance:

- Completed process with unmet arc boundary is `process_success = true` and `objective_success = false`.
- Clean-run success requires both process and objective success.

### T3: Strict Stage 3 Failure Policy

Primary files:

- `main_a.py`
- `scripts/run_auto_frontier_lag_harness.py`
- `tests/test_one_stop_frontier_lag_auto_continue.py`
- `tests/test_auto_frontier_lag_harness.py`

Implementation:

- Add `--stage3-failure-policy strict | skip | quarantine`.
- Default is `strict`.
- In automated mode, no-operator default must be stop, not skip.
- `skip` and `quarantine` require explicit survey/diagnostic intent.
- Skip/quarantine increments dedicated counters and never increments `arcs_advanced`.

Acceptance:

- Stage 3 fail with strict policy stops with explicit stop reason.
- Skip policy returns `arcs_advanced_delta = 0`, `arcs_skipped_delta = 1`.
- Objective boundary cannot be met by skipped arcs.

### T4: Reuse Existing Project Guard

Primary files:

- `scripts/run_auto_frontier_lag_harness.py`
- `modules/core/db_manager.py`
- `tests/test_auto_frontier_lag_harness.py`

Implementation:

- Before reuse, inspect Stage 3/4 failed rows at or after the current frontier boundary.
- Default behavior: refuse reuse if failed state exists.
- Optional explicit reset behavior: `--reuse-reset-after-ep N`.
- Reset behavior must call `reset_after(N)` and then re-read state.
- Manifest records failed-state count, reset target, reset result, pre/post project epoch, and DB hash if available.

Acceptance:

- Reuse with failed state refuses by default.
- Reuse with explicit reset removes failed rows at or after target episode.
- Clean-run report cannot be generated from stale failed state.

### T5: Advisory Authority Discriminator

Primary files:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/session_memory_envelope.py`
- `modules/core/db_manager.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_session_memory_envelope.py`

Implementation:

- Add `authority_level` to advisory surfaces used for retry behavior.
- Allowed levels: `advisory`, `route`, `verdict`, `historical_companion`.
- `fix_pack`, `repair_contract`, `scope_authority`, and `retry_budget_axes` must carry or inherit an explicit level.
- Retry consumers must not treat unlabeled advisory payload as authority-bearing.
- Preserve `stage_attempts` as final retry authority sink; keep `director_selections` historical unless typed promotion exists.

Acceptance:

- Missing `authority_level` on route-sensitive fields fails closed or is ignored.
- Advisory warnings alone cannot drive retry route.
- Existing Stage 4 session memory envelope remains present but typed.

### T6: Continuity Bridge Proposal Store

Primary files:

- `modules/core/db_manager.py`
- New migration/bootstrap hook if needed
- New bridge module under `modules/core/` or equivalent
- `tests/test_continuity_bridge_proposals.py`

Implementation:

- Add `continuity_bridge_proposals`.
- Minimum columns: `bridge_id`, `source_stage`, `target_stage`, `work_id`, `project_id`, `arc_num`, `ep_num`, `authority_source`, `observed_downstream_candidate`, `observed_conflict`, `proposed_bridge`, `allowed_fix_scope`, `director_verdict`, `director_reason`, `applied_status`, `applied_artifact_key`, `created_at`, `source_hashes`.
- Python detector writes `applied_status = pending_director`.
- Director changes status to approved/rejected/escalate.
- Only approved bridges can be projected into downstream prompts.
- Projection must include provenance and authority level.

Acceptance:

- Python cannot apply bridge fixes.
- Bridge proposal can prevent repeated Jan1/Jan3-style contradiction by surfacing a candidate-only correction to Director.
- DB records both the proposed bridge and Director decision.

### T7: Authoritative Continuity Projection and Canary Set

Primary files:

- Stage 2/3/4 context builders
- `modules/core/session_memory_envelope.py`
- New or existing canary/eval tests

Implementation:

- Build a small authoritative head/tail state packet per arc.
- Include current arc boundary facts, last accepted date/location/state, forbidden regressions, and unresolved bridge proposals.
- Keep archival memory separate from authority core.
- Keep context caching purely performance-oriented.
- Add continuity canaries for date drift, location drift, dead-character action, and prior-failure replay.

Acceptance:

- Stage 3 receives the authoritative arc head/tail continuity packet.
- Stage 4 receives the same continuity facts through typed session memory.
- Canary failures are objective failures, not hidden warnings.

### T8: Validation and Clean-Run Reentry

Primary files:

- Touched implementation tests
- `scripts/check_utf8_hygiene.py`
- `scripts/run_auto_frontier_lag_harness.py`

Validation sequence:

1. Run targeted tests for T0/T1.
2. Run targeted tests for T2/T3/T4.
3. Run targeted tests for T5/T6/T7.
4. Run UTF-8 hygiene checks on touched files.
5. Run ops validator if temp execution queue is active.
6. Run one fresh strict 1-arc or 2-arc smoke with a new project.
7. Only after the above passes, run strict fresh 5-arc.

Success criteria:

- No Director verdict mutation by Python.
- No advisory payload without authority level affects retry route.
- No skipped arc counts as advanced.
- No reused failed state is accepted as clean.
- Process success and objective success are both present and both true for clean-run success.
- Terminal failure, if any, has a diagnostic snapshot that explains the semantic cause.

## 4. Side-Effect Coverage

File writes:

- Diagnostic snapshots under project logs or a dedicated diagnostic path.
- Harness worker result, analysis, failure digest, and SSOT logs.
- Possible new bridge proposal artifacts only if DB export is added.

DB writes:

- `stage_attempts.advisory_flags` remains active but must become authority-typed.
- New `continuity_bridge_proposals` table is expected.
- `reset_after()` may be invoked only by explicit reuse-reset flow.

Console/UI:

- Strict mode should clearly say no-operator/default stop.
- Skip/quarantine must display that the arc was not advanced.

Rollback/recovery:

- Reuse reset requires pre/post manifest evidence.
- Reset must be explicit and target-bound.

Cache/global state:

- Context cache is not continuity authority.
- Cache metrics stay observability-only.

Config/env:

- New harness flags must default to strict/safe behavior.

## 5. Implementation Guardrails

- Do not implement T6 bridge application before T0/T5 authority split exists.
- Do not rely on regex/Python to decide narrative correctness.
- Do not delete existing user/untracked project artifacts during implementation.
- Do not run broad pytest in parallel by default.
- Do not claim clean run from reused state unless T4 passes.
- Do not declare success from `status = success` alone.

## 6. 3-Pass Adversarial Audit

### Pass 1: Evidence Completeness

Adversarial question: Did we overfit to the six reports without checking code?

Result: PASS.

Reasoning:

- P0-A and P0-B were verified directly in code.
- P0-C and P0-D were verified directly in code.
- P0-E was verified locally as a missing guard in the harness reuse path, with `reset_after()` present elsewhere.
- P1-D was refined by subagent verification: `director_selections` is historical companion, while `stage_attempts.advisory_flags` is the retry authority path.

Residual uncertainty:

- The timed-out subagent did not return P0-E verification.
- The execution doc therefore phrases P0-E as local-code-confirmed planning evidence, not as completed implementation proof.

### Pass 2: Governance and Authority

Adversarial question: Does the plan violate the workspace principle that Python collects and LLM judges?

Result: PASS.

Reasoning:

- The plan removes Python verdict mutation.
- Runtime blocking is expressed as objective/route status, not Director verdict.
- Continuity bridge proposals are pending Director adjudication by default.
- Advisory payloads need authority labels before consumers can use them.

Residual uncertainty:

- Existing compatibility fields named `final_verdict` are widespread. T0 must be careful to avoid a half-migration where old consumers still read mutated fields.

### Pass 3: Execution Safety

Adversarial question: Can this be implemented without causing a giant unstable refactor?

Result: PASS WITH SEQUENCING REQUIREMENT.

Reasoning:

- The order starts with the narrowest authority split before DB schema expansion.
- Harness process/object split and strict skip policy are bounded.
- Reuse guard uses existing `reset_after()` rather than inventing a new reset mechanism.
- Bridge DB/table work is delayed until route authority is typed.

Required sequence:

- T0 through T4 must land before any claim of clean 5-arc readiness.
- T5 must land before T6 bridge proposals can be used in retry routes.
- T8 strict fresh run is the only final clean-run proof.

Confidence: 96%.

## 7. Final Go/No-Go

Execution document status: GO.

Clean 5-arc runtime status: PARTIAL-GO for strict fresh 1-arc proof; NO-GO for strict fresh 5-arc claim until a 5-arc run passes.

Bridge/memory expansion status: T6 proposal storage, T7 typed projection, and T7 continuity canary tripwires are implemented. Operational clean-run confidence remains NO-GO until a fresh 5-arc validation pass.

Recommended next action:

Run strict fresh 5-arc only after deciding the cost/time window is acceptable; the current safety baseline now includes T7 projection and continuity canary tripwires.

## 8. Implementation Progress

Updated: 2026-04-27

Completed:

- T0 realized: Director verdict and runtime route authority are split in Stage 3 validation surfaces.
- T1 realized: terminal Stage 3 runtime blocks now write diagnostic snapshots without official artifact adoption.
- T2 realized: auto Frontier Lag harness separates process success from objective success.
- T3 realized: Stage 3 strict failure policy is default; explicit skip/quarantine increments `arcs_skipped`, not `arcs_advanced`.
- T4 realized: reuse-existing-project now refuses failed Stage 3/4 state by default and only runs `reset_after(N)` through explicit `--reuse-reset-after-ep N`.
- T5 realized: Stage 4 advisory retry surfaces now carry explicit authority inheritance labels. `stage_attempts` route payloads are labeled `route`; `director_selections` advisory payloads default to `historical_companion` unless explicitly promoted.
- T6 realized: `continuity_bridge_proposals` stores Python-collected bridge proposals as `pending_director`; Director adjudication is separate and no bridge is auto-applied.
- T7 projection path realized: `authoritative_continuity_projection` builds a typed route packet from accepted blueprint/arc state plus Director-approved or pending bridge proposals, injects it into Stage 3 semantic context and Stage 4 tier-0 mandatory context, and preserves it in the Stage 4 session memory envelope.
- T7 continuity canary set realized: deterministic tripwires now cover date drift, location drift, deceased-character active-role recurrence, and prior-failure replay. Canary findings are not Director verdicts; they require Director review and block only unattended clean-run claims through strict evidence gaps.
- T8 strict fresh 1-arc smoke passed: `projects/auto_t8_smoke_20260426_214331_1arc` reached requested arc boundary with `process_success=true`, `objective_success=true`, `arcs_advanced=1`, `arcs_skipped=0`, Stage3 `aligned`, Stage4 `aligned`, and 2 manuscripts produced.
- T8 analysis hardening realized: Stage4 `director_selections` companion rows no longer fail sink alignment merely because historical selected-candidate paths differ from final manuscript paths or omit route-only runtime advisory fields; stale `auto_frontier_lag_failure_digest.json` is removed after successful reanalysis.

Validation:

- `python -m py_compile main_a.py scripts/run_auto_frontier_lag_harness.py`
- `python -m py_compile modules/core/advisory_authority.py modules/core/session_memory_envelope.py modules/core/db_manager.py modules/core/stage4_interview_round.py`
- `python -m pytest tests/test_auto_frontier_lag_harness.py tests/test_one_stop_frontier_lag_auto_continue.py -q` -> 38 passed
- `python -m pytest tests/test_auto_frontier_lag_harness.py -q` -> 25 passed
- `python -m pytest tests/test_unified_blueprint_validator_lane_c.py tests/test_blueprint_patch_mode.py tests/test_stage3_orchestrator.py::TestProcessSingleEpisode::test_stage3_sink_payload_builders_share_packet_contract tests/test_stage3_orchestrator.py::TestStageAttemptObservability::test_handle_failure_persists_stage3_director_selection tests/test_auto_frontier_lag_harness.py tests/test_one_stop_frontier_lag_auto_continue.py -q` -> 188 passed
- `python -m pytest tests/test_advisory_authority.py tests/test_session_memory_envelope.py tests/test_db_manager.py::test_update_director_selection_rationale_merges_advisory_warnings tests/test_db_manager.py::test_get_latest_stage4_gate_repair_snapshot_surfaces_repair_contract_and_scope_authority tests/test_db_manager.py::test_get_latest_stage4_gate_repair_snapshot_backfills_nested_gate_contract_fields tests/test_db_manager.py::test_get_latest_stage4_gate_repair_snapshot_falls_back_to_root_fix_scope_column tests/test_stage4_interview_round.py::TestRecordS4Attempt::test_build_stage4_attempt_contract_packet_shares_contract_fields -q` -> 11 passed
- `python -m pytest tests/test_advisory_authority.py tests/test_session_memory_envelope.py tests/test_db_manager.py::test_update_director_selection_rationale_merges_advisory_warnings tests/test_db_manager.py::test_get_latest_stage4_gate_repair_snapshot_surfaces_repair_contract_and_scope_authority tests/test_db_manager.py::test_get_latest_stage4_gate_repair_snapshot_backfills_nested_gate_contract_fields tests/test_db_manager.py::test_get_latest_stage4_gate_repair_snapshot_falls_back_to_root_fix_scope_column tests/test_stage4_interview_round.py::TestRecordS4Attempt::test_build_stage4_attempt_contract_packet_shares_contract_fields tests/test_unified_blueprint_validator_lane_c.py tests/test_blueprint_patch_mode.py tests/test_stage3_orchestrator.py::TestProcessSingleEpisode::test_stage3_sink_payload_builders_share_packet_contract tests/test_stage3_orchestrator.py::TestStageAttemptObservability::test_handle_failure_persists_stage3_director_selection tests/test_auto_frontier_lag_harness.py tests/test_one_stop_frontier_lag_auto_continue.py -q` -> 199 passed
- `python scripts/check_utf8_hygiene.py <touched files>` -> passed
- `python scripts/ops_validator.py --strict` -> passed
- `git diff --check -- <touched files>` -> passed
- T8 attempt 1: operator invocation failed before project creation because the PowerShell `Start-Process` trigger argument contained spaces.
- T8 attempt 2: Stage0 failed because the harness default profile still pointed at stale seed file names removed by root cleanup.
- T8 seed-path fix validation: `python -m pytest tests/test_auto_frontier_lag_harness.py::test_default_profile_points_to_available_stage0_seed_files tests/test_auto_frontier_lag_harness.py::test_build_worker_command_targets_same_script_and_has_no_timeout_flag -q` -> 2 passed
- T8 smoke: `python scripts/run_auto_frontier_lag_harness.py run --arc-count 1 --target-project auto_t8_smoke_20260426_214331_1arc --trigger T8_strict_fresh_1arc_smoke_after_seed_path_fix --stage3-failure-policy strict --poll-interval-seconds 60 --operational-attempt-cap 5` -> process/objective success after reanalysis
- T8 analysis proof: `python scripts/run_auto_frontier_lag_harness.py analyze --project auto_t8_smoke_20260426_214331_1arc --arc-count 1` -> `judgment=success`, `root_cause=""`, Stage3/Stage4 sink alignment `ok`, confidence `95`, finalized `true`
- Analyzer hardening validation: `python -m pytest tests/test_failure_analyzer.py::test_failure_analyzer_build_sink_alignment_summary_payload_marks_warn_and_counts_contract_rows tests/test_failure_analyzer.py::test_failure_analyzer_stage4_companion_missing_runtime_advisory_is_not_metadata_gap tests/test_failure_analyzer.py::test_failure_analyzer_sink_alignment_summary_aligns_stage4_session_rationale_with_director_selection tests/test_failure_analyzer.py::test_failure_analyzer_sink_alignment_summary_flags_stage4_runtime_rationale_mismatch tests/test_auto_frontier_lag_harness.py::test_analyze_project_removes_stale_failure_digest_after_success tests/test_auto_frontier_lag_harness.py::test_default_profile_points_to_available_stage0_seed_files tests/test_auto_frontier_lag_harness.py::test_run_three_pass_audit_only_finalizes_success_at_95 -q` -> 7 passed
- Reanalysis hygiene validation: stale `projects/auto_t8_smoke_20260426_214331_1arc/logs/auto_frontier_lag_failure_digest.json` absent after successful analysis
- T7 projection validation: `python -m pytest tests/test_authoritative_continuity_projection.py tests/test_session_memory_envelope.py -q` -> 7 passed
- T7 Stage3/Stage4 validation: `python -m pytest tests/test_stage3_orchestrator.py -q` -> 107 passed; `python -m pytest tests/test_stage4_context_builder.py -q` -> 113 passed
- T7 canary validation: `python -m pytest tests/test_continuity_canary.py tests/test_auto_frontier_lag_harness.py::test_strict_success_gaps_include_continuity_canary_review_required tests/test_auto_frontier_lag_harness.py::test_analyze_project_fails_success_when_continuity_canary_requires_review -q` -> 5 passed
- T7 canary/harness regression: `python -m pytest tests/test_auto_frontier_lag_harness.py tests/test_one_stop_frontier_lag_auto_continue.py -q` -> 53 passed

Known residual:

- Repository-wide `git diff --check` still reports pre-existing trailing whitespace in `0_temp.txt`; touched implementation files pass scoped diff check.
- Strict fresh 1-arc proof passed; strict fresh 5-arc remains pending and should not be claimed yet.
- Jan1/Jan3-class drift is guarded by projection plus canary tripwires, but not yet proven by a fresh multi-arc run.

## 9. T9 Uninterrupted 5-Arc Operations Hardening

Updated: 2026-04-27

Source:

- Six-agent read-only deep dive requested for 5-arc uninterrupted operation.
- Local evidence already collected from `main_a.py`, `scripts/run_auto_frontier_lag_harness.py`, Stage 3 runtime, Stage 4 runtime, and prior failed 5-arc analysis.
- T9 is additive to T6/T7. It does not replace continuity bridge/projection work.

### 9.1 Reclassified Risk Register

#### Operational P0: Stage 4 LLM calls lack hard wall-clock containment

Evidence:

- `modules/domain/agents/chief_writer.py` uses threaded candidate generation and `Future.cancel()`, but a running provider SDK call is not forcibly killed.
- `modules/core/providers/openai_provider.py` and `modules/core/providers/anthropic_provider.py` do not provide an explicit per-request timeout in the inspected paths.

Risk:

- A strict 5-arc run can remain process-alive while a provider call hangs or runs far past the intended ensemble timeout.
- This is not a Director quality issue. It is an unattended operations boundary issue.

Execution requirement:

- Add provider/request timeout plumbing or a bounded process-level execution shell for ChiefWriter candidate calls.
- Stage 4 must emit structured `stage4_provider_timeout` or `stage4_budget_exhausted` telemetry instead of relying on thread cancellation.
- Add a fake provider test that sleeps past timeout and proves Stage 4 exits within the configured deadline.

#### Operational P0: No hard cost/token/runtime/disk budget for 5-arc

Evidence:

- T8 strict 1-arc smoke used `822,810` tokens, about `$2.565796`, and about 35 minutes.
- The old failed 5-arc attempt used about `2,456,297` tokens, about `$6.47955`, and about 97 minutes while advancing only 1 arc.
- The harness has poll and attempt controls, but no hard `max_cost`, `max_tokens`, `max_runtime`, or project-size cap.

Risk:

- A clean 5-arc attempt can become expensive or operationally ambiguous before it reaches semantic failure.

Execution requirement:

- Add preflight budget estimate and enforced caps.
- Persist budget fields in worker result, poll state, analysis SSOT, and failure digest.
- On cap breach, stop with objective failure and a non-ambiguous root cause.

#### P1: Watchdog can kill legitimate retry loops by matching free-text failure glyphs

Evidence:

- `scripts/run_auto_frontier_lag_harness.py` classifies tail text containing `Traceback`, crash dump markers, or `❌` as failed.
- Stage 4 normal retry/reject paths can log visible reject/failure glyphs while the process is still doing a valid retry.

Risk:

- Python watchdog can terminate a live LLM retry path, turning recoverable Director rejection into process death.

Execution requirement:

- Replace glyph/free-text fatal matching with structured fatal events.
- Recoverable Stage 3/4 reject tails must classify as `progressing` or `retrying`, not `failed`.
- Add a unit test where a Stage 4 REJECT tail containing `❌` does not terminate the worker.

#### P1: Analyzer can report success when strict DB evidence is missing or empty

Evidence:

- Empty Stage 3/4 alignment summaries can be initialized and later not fail unless a bad summary is truthy.
- Successful reanalysis removes stale failure digest.

Risk:

- A strict run could look clean when required authority evidence was never recorded.

Execution requirement:

- Strict analysis must require DB presence, non-empty Stage 3/4 summaries, expected `stage_attempts`, final-authority rows, artifact hashes, and final artifact existence.
- Successful digest cleanup is allowed only after required evidence gates pass.

#### P1: Stage 4 partial progress can be counted as arc advancement

Evidence:

- `_run_frontier_lag_stage4_sync` computes `arc_manuscripts` as any positive manuscript delta and can return `arcs_advanced_delta = 1` even if `ms_max_after < stage4_target`.

Risk:

- A partially generated arc can count as advanced in the main loop.

Execution requirement:

- In clean mode, Stage 4 arc advancement must require `ms_max_after >= stage4_target`.
- Partial progress should return `stage4_target_not_reached` or equivalent objective failure.

#### P1: MAX_TOKENS continuation is incomplete on normalized and cached provider paths

Evidence:

- `LLMResponse` carries `finish_reason`, but continuation logic checks provider-specific candidate structures.
- Cached context paths can perform direct generation and log `continuation_count = 0`.

Risk:

- Truncated JSON/manuscript output can enter retry churn or Director rejection instead of being continued or failed closed.

Execution requirement:

- Route normalized `finish_reason == MAX_TOKENS` through continuation or structured fail-closed logic.
- Add tests for normal and cached-context provider paths.

#### P1: Final authority DB writes are best-effort while callers continue

Evidence:

- `save_stage_attempt` catches failures and returns `False`.
- Stage 3/4 callers can continue without hard-failing strict authority persistence.

Risk:

- Artifact may exist while final authority evidence is missing.

Execution requirement:

- Strict mode must hard-fail missing final authority persistence or post-run validation must fail the objective.
- Add a test where forced DB write failure prevents clean objective success.

#### P1: T6/T7 continuity authority still needs fresh multi-arc proof

Evidence:

- T6 bridge proposal store and T7 shared authoritative continuity projection are implemented.
- Dedicated continuity canaries are implemented.
- Fresh multi-arc proof remains pending.
- Session memory and context caching are telemetry/performance helpers, not the authority carrier for Jan1/Jan3-class drift.

Risk:

- The same cross-arc date/location/state contradiction can reappear after many expensive retries.

Execution requirement:

- Run fresh multi-arc validation before claiming robust 5-arc operation.
- Python may propose or project typed authority packets; Director still adjudicates narrative correctness.

### 9.2 Additional P2/P3 Hardening Queue

P2 items:

- Prompt-blocked states should not wait forever in strict unattended mode. Convert unhandled prompt markers into explicit `manual_wait_blocked` after a small number of windows or fail immediately in headless mode.
- Poll history should be appended/flushed as JSONL every poll, not only after process exit.
- Reuse/reanalysis must include run-id freshness so stale worker results cannot be trusted after crash or reuse.
- Attempt cap should be derived from structured DB/session events, not only the last 20 log lines.
- `reset_after()` should delete stale Stage 3 `director_selections` companion rows as well as Stage 3/4 attempts.
- Analyzer artifact verification should include settlement packets and human-facing `drafts/ep_####.txt` files.
- Session filtering should filter by session before limiting where possible, to avoid stale-row lookback under accumulation.
- `PassRateMonitor` reconciliation should treat `PASS_WITH_FIX` consistently with live Stage 4 semantics if it is a non-terminal accepted route.
- Advisory free text must not be rendered as mandatory Director feedback unless it carries a route/verdict authority label.
- Stage 4 context trimming must preserve hard-canon/authority sections before any generic BaseAgent safety clip.

P3 items:

- Human-facing SSOT should record the actual polling interval instead of hardcoded cadence text.
- Operator progress counters should count actual blueprint file extensions produced by the current pipeline.
- Analysis reports should surface cost, token, duration, and project-size metrics near the top.

### 9.3 T9 Execution Order

T9-A: Watchdog structured fatal-state hardening.

- Replace free-text `❌` fatal matching with structured fatal/crash evidence.
- Add recoverable reject-tail tests.

T9-B: Strict analysis evidence gates.

- Require non-empty Stage 3/4 DB evidence and final artifact/hash evidence before success.
- Protect stale failure digest cleanup behind the strict evidence gates.

T9-C: Stage 4 target-reached advancement contract.

- Require `ms_max_after >= stage4_target` for clean `arcs_advanced_delta = 1`.
- Add partial-progress tests.

T9-D: Provider timeout and budget circuit breakers.

- Add explicit per-call timeout or bounded execution shell for Stage 4 candidate generation.
- Add runtime/token/cost/project-size caps with structured stop reasons.

T9-E: MAX_TOKENS continuation and fail-closed behavior.

- Normalize continuation detection across provider wrappers and cached-context paths.
- Add synthetic finish-reason tests.

T9-F: Authority persistence hard-fail in strict mode.

- Ensure missing final authority DB rows cannot produce clean objective success.
- Add forced DB write failure tests.

T9-G: Operator evidence durability.

- Flush poll history incrementally.
- Add run-id freshness to worker results and analysis.

T9-H: Post-run artifact completeness.

- Verify settlement packets and human-facing draft files in strict analysis.
- Include cost/duration/token metrics in the analysis SSOT summary.

### 9.4 T9 3-Pass Adversarial Audit

Pass 1: Evidence completeness.

Result: PASS.

Reasoning:

- Each P0/P1 item has either direct local-code evidence or convergent multi-agent evidence.
- No item depends on console mojibake or preview text.
- T9 is intentionally scoped as operations hardening, not as proof that 5-arc is already safe.

Residual risk:

- Some exact implementation file locations may shift during coding, especially provider timeout plumbing and Stage 4 budget enforcement.

Pass 2: Governance and authority.

Result: PASS.

Reasoning:

- T9 does not ask Python to decide narrative PASS/REJECT.
- Watchdog, budget, timeout, DB evidence, and artifact evidence are process/objective gates.
- Continuity bridge/projection remains under T6/T7 and must preserve Director adjudication.

Residual risk:

- The terms `objective_success` and `runtime_route` must remain clearly distinct from Director verdicts in UI and SSOT output.

Pass 3: Execution safety.

Result: PASS WITH ORDERING REQUIREMENT.

Required order:

- Do T9-A, T9-B, and T9-C before another expensive 5-arc run.
- Do T9-D and T9-E before treating 5-arc as unattended.
- Do T9-F through T9-H before making a durable clean-run claim.
- Do T6/T7 before claiming the Jan1/Jan3-class continuity problem is structurally solved.

Confidence: 96%.

### 9.5 Updated Go/No-Go

Strict fresh 1-arc: GO, already proven.

Strict fresh 5-arc as diagnostic run: CONDITIONAL GO only if cost/time risk is accepted and the result is not treated as a durable clean-run proof.

Strict fresh 5-arc as unattended clean-run claim: NO-GO until at least T9-A through T9-F and T6/T7 are implemented and validated.

Recommended next implementation step:

- Start with T9-A through T9-C because they are the smallest changes that prevent false process death, false evidence success, and false arc advancement.

### 9.6 T9 Implementation Progress

Updated: 2026-04-26

Completed:

- T9-A realized: watchdog no longer treats a free-text `❌` glyph as a fatal marker. Structured fatal markers remain `Traceback`, `crash_dump.log`, and explicit `AUTO_FRONTIER_LAG_FATAL`.
- T9-B realized: strict successful analysis now requires project DB presence, non-empty Stage 3/4 attempt evidence, and non-empty Stage 3/4 sink alignment summaries before removing a failure digest.
- T9-C realized: Stage 4 clean arc advancement now requires the manuscript frontier to reach `stage4_target`; partial progress returns `stage4_target_not_reached` and does not increment `arcs_advanced`.
- T9-D guardrail added: OpenAI/Anthropic direct providers now receive request timeout from `http_options.timeout`, and harness `run`/`plan` now supports runtime/token/cost/project-size budget caps.
- T9-D hard runtime shell added: the parent watchdog now enforces `max_runtime_seconds` independently from the long poll cadence. If an SDK call hangs inside the worker, the watchdog records `budget_runtime_seconds_exceeded` and terminates the worker process via the existing CTRL_BREAK / terminate / kill path.
- T9-E realized for normalized and cached-context paths: provider-neutral `LLMResponse.finish_reason` now triggers continuation on `MAX_TOKENS`/`LENGTH`/equivalent reasons; cached-context truncation fails closed and falls back to direct `ask()`.
- T9-E overlap repair added: continuation merge no longer treats tiny one-character overlaps as safe duplicate spans, preventing `hello` -> `helo` style corruption.
- T9-F post-run gate added: stale worker results with mismatched `run_id` now fail analysis instead of being trusted.
- T9-F exact authority persistence hard-fail added: accepted Stage 3/4 authority attempts now stop instead of continuing when `stage_attempts` cannot persist the final accepted decision. This remains a process/evidence gate only; Python still does not judge narrative PASS/REJECT.
- T9-G realized: poll history is flushed during execution, not only after worker exit.
- T9-H guardrail added: strict successful analysis now requires human-facing draft txt files and structured settlement packets for produced manuscript episodes.
- T6 proposal store added: `continuity_bridge_proposals` table plus Director-pending proposal save/query/adjudication APIs. Python writes proposals as `pending_director`; Director adjudication is a separate API and no bridge is auto-applied.
- T7 projection path added: `modules/core/authoritative_continuity_projection.py` builds the typed projection; Stage3 receives it through semantic context, Stage4 receives it as a protected tier-0 context section, and Stage4 session memory preserves the packet for retry surfaces. Pending bridge proposals are surfaced only as pending Director review; only approved bridges are rendered as Director-approved bridge material.
- T7 continuity canary set added: `modules/core/continuity_canary.py` evaluates date drift, location drift, deceased-character active-role recurrence, and prior-failure replay as objective tripwires requiring Director review. Harness analysis reads `logs/continuity_canary_report.json`; `review_required`/`failed` canary status becomes a strict evidence gap and prevents a clean objective claim.

Validation:

- `python -m py_compile main_a.py scripts/run_auto_frontier_lag_harness.py`
- `python -m py_compile modules/core/providers/openai_provider.py modules/core/providers/anthropic_provider.py modules/domain/agents/base_agent.py`
- `python -m py_compile modules/core/db_bootstrap_runtime.py modules/core/db_manager.py`
- `python -m pytest tests/test_auto_frontier_lag_harness.py::test_classify_poll_transition_allows_recoverable_reject_glyph_tail tests/test_auto_frontier_lag_harness.py::test_analyze_project_removes_stale_failure_digest_after_success tests/test_auto_frontier_lag_harness.py::test_analyze_project_keeps_failure_digest_when_strict_success_evidence_missing -q` -> 3 passed
- `python -m pytest tests/test_one_stop_frontier_lag_auto_continue.py::test_run_frontier_lag_stage4_sync_blocks_when_backlog_has_no_progress tests/test_one_stop_frontier_lag_auto_continue.py::test_run_frontier_lag_stage4_sync_blocks_when_partial_progress_misses_target -q` -> 2 passed
- `python -m pytest tests/test_auto_frontier_lag_harness.py tests/test_one_stop_frontier_lag_auto_continue.py -q` -> 45 passed
- `python -m pytest tests/test_base_agent.py::TestNormalizedProviderHelpers::test_ask_continues_normalized_max_tokens_response tests/test_base_agent.py::TestNormalizedProviderHelpers::test_cached_context_max_tokens_falls_back_to_direct_ask tests/test_llm_router.py::test_openai_provider_applies_http_options_timeout_to_client tests/test_llm_router.py::test_anthropic_provider_applies_http_options_timeout_to_client -q` -> 4 passed
- `python -m pytest tests/test_auto_frontier_lag_harness.py::test_build_execution_plan_records_budget_caps tests/test_auto_frontier_lag_harness.py::test_detect_budget_breach_reports_first_exceeded_cap tests/test_auto_frontier_lag_harness.py::test_capture_poll_snapshot_surfaces_metrics_and_project_bytes tests/test_auto_frontier_lag_harness.py::test_derive_root_cause_prefers_budget_termination_reason -q` -> 4 passed
- `python -m pytest tests/test_auto_frontier_lag_harness.py::test_analyze_project_fails_stale_worker_result_run_id_mismatch tests/test_auto_frontier_lag_harness.py::test_strict_success_artifact_gaps_require_drafts_and_settlement_packets tests/test_auto_frontier_lag_harness.py::test_run_harness_does_not_wait_full_poll_window_after_quick_worker_exit -q` -> included in latest targeted pass
- `python -m pytest tests/test_auto_frontier_lag_harness.py tests/test_one_stop_frontier_lag_auto_continue.py -q` -> 49 passed
- `python -m pytest tests/test_auto_frontier_lag_harness.py tests/test_one_stop_frontier_lag_auto_continue.py -q` -> 51 passed after T9-F/G/H guardrails
- `python -m pytest tests/test_base_agent.py tests/test_llm_router.py -q` -> 150 passed
- `python -m pytest tests/test_db_manager.py::test_continuity_bridge_proposal_store_is_director_pending_by_default tests/test_db_manager.py::test_continuity_bridge_adjudication_records_director_decision_without_auto_apply -q` -> 2 passed
- `python -m pytest tests/test_db_manager.py -q` -> 61 passed
- `python -m pytest tests/test_authoritative_continuity_projection.py tests/test_session_memory_envelope.py -q` -> 7 passed
- `python -m pytest tests/test_stage3_orchestrator.py -q` -> 107 passed
- `python -m pytest tests/test_stage4_context_builder.py -q` -> 113 passed
- `python -m pytest tests/test_authoritative_continuity_projection.py tests/test_session_memory_envelope.py tests/test_stage4_context_builder.py::TestAuthoritativeContinuityProjection -q` -> 8 passed
- `python -m pytest tests/test_continuity_canary.py tests/test_auto_frontier_lag_harness.py::test_strict_success_gaps_include_continuity_canary_review_required tests/test_auto_frontier_lag_harness.py::test_analyze_project_fails_success_when_continuity_canary_requires_review -q` -> 5 passed
- `python -m pytest tests/test_auto_frontier_lag_harness.py tests/test_one_stop_frontier_lag_auto_continue.py -q` -> 53 passed
- `python -m pytest tests/test_stage3_orchestrator_handle_success_lane_c.py -q` -> 4 passed
- `python -m pytest tests/test_stage4_interview_round.py::TestRecordS4Attempt::test_save_stage4_db_attempt_uses_prelude_payload tests/test_stage4_interview_round.py::TestRecordS4Attempt::test_save_stage4_db_attempt_hard_fails_when_success_authority_write_returns_false tests/test_stage4_interview_round.py::TestRecordS4Attempt::test_attempt_key_uses_metrics_session_id_when_available -q` -> 3 passed
- `python -m pytest tests/test_stage4_interview_round.py::TestRecordS4Attempt -q` -> 135 passed
- `python -m pytest tests/test_stage3_orchestrator.py -k "attempt_key or observability or save_stage_attempt or authority or artifact_linkage" -q` -> 20 passed, 87 deselected
- `python -m pytest tests/test_auto_frontier_lag_harness.py -q` -> 38 passed
- `python scripts/check_utf8_hygiene.py modules/core/stage3_orchestrator.py modules/core/stage4_interview_round.py tests/test_stage3_orchestrator_handle_success_lane_c.py tests/test_stage4_interview_round.py` -> passed
- `python scripts/check_utf8_hygiene.py <T9 touched files and SSOT docs>` -> passed
- `git diff --check -- <T9 touched files and SSOT docs>` -> passed

Known residual:

- Fresh multi-arc proof remains pending for T7 projection/canary behavior.
- Strict fresh 5-arc unattended clean-run claim remains NO-GO.
- Per-call SDK child-process isolation is not implemented; the current hard boundary is the parent-owned worker process runtime cap.

T9-F implementation micro-audit:

- Pass 1 evidence completeness: PASS. The runtime hole was confirmed at the exact Stage 3/4 `save_stage_attempt` callsites, and forced write-failure tests now cover both accepted-authority paths.
- Pass 2 authority/governance: PASS. The new guard blocks missing persistence evidence; it does not convert Python into a narrative judge and does not mutate Director verdict text.
- Pass 3 side-effect risk: PASS. Reject/best-effort observability paths remain non-blocking; only accepted Stage 3/4 authority attempts become hard-fail when final authority persistence is unavailable or explicitly returns `False`.

T9-D implementation micro-audit:

- Pass 1 evidence completeness: PASS. The remaining gap was not provider `http_options` injection, but the parent watchdog waiting for the long poll cadence before checking runtime caps.
- Pass 2 operational safety: PASS. The change preserves the existing worker process model and does not introduce unpicklable per-call child execution. It only shortens the watchdog sleep to the runtime deadline and terminates the worker when the cap is exceeded.
- Pass 3 false-success risk: PASS. Runtime-cap termination produces `termination_reason = budget_runtime_seconds_exceeded`, which `derive_root_cause` already treats as a failed objective root cause.

## 9.7 Current-State Re-Audit After #56/#59 Closure

Date: 2026-04-27
Baseline: `7dc668c524501dd27db156bdf2c7342e55b791e9`
Queue state: Frontier Lag is rank 1/front-active after #56 and #59 landed, passed CI, were closed, and were removed from active temp queue by PR #85.

### Pass 1 - Structure and Scope

Result: PASS.

- This SSOT remains the governing execution artifact for Frontier Lag clean 5-arc stabilization.
- The active queue and roadmap now point to this item first; the three security SSOTs remain parked behind it.
- This re-audit does not authorize a strict fresh 5-arc clean-run claim. It only clears the document/current-state gate needed before the next bounded diagnostic step.

### Pass 2 - Evidence and Consistency

Result: PASS.

Current source still supports the major implementation claims recorded above:

- T0/T1 authority split and diagnostic evidence are present in `modules/domain/agents/unified_blueprint_validator.py`, `modules/domain/agents/three_phase_blueprint_runtime.py`, and Stage3 terminal failure diagnostic paths.
- T2/T3/T4/T9 harness claims are present in `scripts/run_auto_frontier_lag_harness.py` and `main_a.py`: process/objective split, strict Stage3 skip behavior, Stage4 target-reached advancement, runtime budget caps, poll history flushing, run-id freshness, strict evidence gaps, and artifact completeness gates.
- T6/T7 claims are present in `modules/core/db_bootstrap_runtime.py`, `modules/core/db_manager.py`, `modules/core/authoritative_continuity_projection.py`, `modules/core/continuity_canary.py`, `modules/core/stage3_orchestrator.py`, `modules/core/stage4_context_builder.py`, and `modules/core/session_memory_envelope.py`.
- #56/#59 are now historical backing, not active blockers; their fixes reduce genre-strategy drift and proof/advisory ambiguity before Frontier Lag reentry.

Residual watch item:

- `final_verdict` remains a compatibility/objective field and is still consumed across Stage3 surfaces. Targeted authority-regression tests passed in this re-audit, so this is not a pre-proof blocker, but any future refactor must keep `director_verdict` and runtime route fields distinct.

### Pass 3 - Execution Readiness

Result: PASS WITH BOUNDED RUN REQUIREMENT.

Recommended next proof step:

- Run a fresh strict 2-arc diagnostic, not a 5-arc clean-run claim.
- Use a new target project, no reuse, `--stage3-failure-policy strict`, and explicit runtime/token/cost/project-size caps.
- Treat the result as a diagnostic/proof packet for multi-arc continuity projection and canary behavior.

Recommended command shape:

```powershell
python scripts/run_auto_frontier_lag_harness.py run --arc-count 2 --target-project auto_frontier_reaudit_probe_20260427_2arc --trigger frontier_reaudit_probe_after_56_59 --stage3-failure-policy strict --poll-interval-seconds 60 --operational-attempt-cap 5 --max-runtime-seconds 10800 --max-total-tokens 2500000 --max-total-cost-usd 8 --max-project-bytes 800000000
```

Rejected next step:

- Do not start with a strict fresh 5-arc unattended clean-run claim. Fresh multi-arc proof is still pending, and per-call SDK child-process isolation is still not implemented; the hard runtime boundary remains the parent-owned worker process cap.

### Validation Run During Re-Audit

- `python -m py_compile scripts/run_auto_frontier_lag_harness.py modules/core/db_manager.py modules/core/db_bootstrap_runtime.py modules/core/authoritative_continuity_projection.py modules/core/continuity_canary.py modules/core/stage3_orchestrator.py modules/core/stage4_context_builder.py modules/core/stage4_interview_round.py modules/core/stage4_retry_runtime.py modules/core/session_memory_envelope.py` -> passed
- `python -m pytest -q tests/test_auto_frontier_lag_harness.py tests/test_one_stop_frontier_lag_auto_continue.py` -> 57 passed
- `python -m pytest -q tests/test_authoritative_continuity_projection.py tests/test_continuity_canary.py tests/test_session_memory_envelope.py tests/test_stage4_context_builder.py::TestAuthoritativeContinuityProjection` -> 11 passed
- `python -m pytest -q tests/test_db_manager.py::test_continuity_bridge_proposal_store_is_director_pending_by_default tests/test_db_manager.py::test_continuity_bridge_adjudication_records_director_decision_without_auto_apply` -> 2 passed
- `python -m pytest -q tests/test_stage4_interview_round.py::TestRecordS4Attempt::test_save_stage4_db_attempt_hard_fails_when_success_authority_write_returns_false` -> 1 passed
- `python -m pytest -q tests/test_session_memory_envelope.py` -> 5 passed
- `python -m pytest -q tests/test_blueprint_patch_mode.py::TestBlueprintPatchIntegration::test_finalize_terminal_failure_blocks_emergency_fallback_with_binding_issue tests/test_unified_blueprint_validator_lane_c.py::test_lane_c_build_director_validation_result_escalates_binding_issue_to_pass_with_fix tests/test_stage3_orchestrator_handle_success_lane_c.py tests/test_db_manager.py::test_continuity_bridge_proposal_store_is_director_pending_by_default tests/test_authoritative_continuity_projection.py tests/test_session_memory_envelope.py::test_build_stage4_session_memory_envelope_preserves_authoritative_continuity_projection tests/test_auto_frontier_lag_harness.py::test_analyze_project_fails_success_when_continuity_canary_requires_review` -> 11 passed
- `python scripts/run_auto_frontier_lag_harness.py plan --arc-count 2 --target-project auto_frontier_reaudit_probe_2arc --batch-size 1 --operational-attempt-cap 24 --max-runtime-seconds 5400 --max-total-tokens 1800000 --max-total-cost-usd 6 --max-project-bytes 500000000 --stage3-failure-policy strict` -> plan rendered
- `python scripts/run_auto_frontier_lag_harness.py plan --arc-count 5 --target-project auto_frontier_reaudit_probe_5arc --batch-size 1 --operational-attempt-cap 72 --max-runtime-seconds 14400 --max-total-tokens 5000000 --max-total-cost-usd 15 --max-project-bytes 1000000000 --stage3-failure-policy strict` -> plan rendered
- `python scripts/ops_validator.py --strict` -> passed

Estimated operational confidence: 96%.
