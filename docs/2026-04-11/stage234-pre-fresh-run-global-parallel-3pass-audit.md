# Stage234 Pre-Fresh-Run Global Parallel 3-Pass Audit

Date: 2026-04-11
Status: final
Canonical Path: `docs/2026-04-11/stage234-pre-fresh-run-global-parallel-3pass-audit.md`
Doc Type: global system-track audit
Scope: current live workspace across Stage2-Stage4 after the latest pre-fresh-run bounded patches and before the next expensive fresh run
Baseline Commit: `2b7cb64f`
Baseline Dirty Summary: `dirty live workspace; Stage2/Stage3 code+tests, roadmap/SSOT docs, and unrelated material-side files remain modified in-worktree, so this audit treats the live workspace rather than clean HEAD as authority`
Resume Commit: `2b7cb64f`
Resume Drift Summary: `the earlier Stage2 P2 tranche is now extended with tactical start-state finance sync plus Stage4 aligned episode_production green-path coverage, Stage3 truth-first/opening/advisory slices remain landed and green, and the next intended operator action is still one fresh run rather than more broad static patching`
Source Survey Docs:
- `docs/2026-04-11/stage23-live-workspace-static-parallel-survey.md`
- `docs/2026-04-11/stage34-live-workspace-static-parallel-roadmap-validity-survey.md`
- `docs/2026-04-11/stage2-stage4-p2-tranche-3pass-audit.md`
- `docs/2026-04-11/stage234-live-run-pending-static-parallel-global-survey.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md`
Evidence Artifacts:
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/failure_analyzer.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/director_continuity.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- directly relevant Stage2/Stage3/FailureAnalyzer tests
Side-Effect Coverage: covered for static code, sink, roadmap, and execution-doc surfaces only; no fresh runtime proof is claimed here

## 1. Question

Before the next expensive fresh run, what static S2-S4 risks still remain on the current live workspace, which earlier residuals are now actually closed, and what smarter/elegant improvement directions are worth tracking behind proof?

## 2. Scope

Included:

- current live Stage2 / Stage3 / Stage4 code surfaces touched by the latest bounded patches
- current execution roadmap and governing S2-S4 execution SSOT docs
- targeted low-memory validation for touched S2-S4 tests
- touched-area complexity recount for major S2-S4 owners

Excluded:

- fresh runtime truth, DB truth, or post-run merge conclusions
- queue mutation, temp-mirror mutation, or ClickUp mutation
- unrelated Stage0 / material-side work
- broad refactors beyond static audit and bounded pre-run fixes

## 3. Verification Basis

Commands run during this audit:

- `python -m py_compile modules/core/stage2_finalizer.py modules/core/stage2_orchestrator.py modules/core/failure_analyzer.py modules/core/stage3_orchestrator.py modules/domain/agents/blueprint_constraint_compiler.py modules/domain/agents/unified_blueprint_validator.py modules/domain/agents/three_phase_blueprint_runtime.py modules/domain/agents/director_continuity.py tests/test_stage2_finalizer.py tests/test_failure_analyzer.py tests/test_stage3_orchestrator.py tests/test_stage3_orchestrator_handle_success_lane_c.py tests/test_stage3_blueprint_state_precision_guardrail.py tests/test_stage3_clarity_density_wave1.py tests/test_unified_blueprint_validator_lane_c.py tests/test_blueprint_patch_mode.py tests/test_director_auditor_pre_llm_lane.py tests/test_stage2_stage3_episode_boundary_guardrail.py`
- `python -m ruff check ...same file set...`
- `python scripts/check_utf8_hygiene.py ...same file set...`
- `pytest tests/test_stage2_finalizer.py tests/test_failure_analyzer.py -q`
- `pytest tests/test_stage2_orchestrator_lane_f.py -q`
- `pytest tests/test_stage3_orchestrator.py tests/test_stage3_orchestrator_handle_success_lane_c.py -q`
- `pytest tests/test_stage3_blueprint_state_precision_guardrail.py tests/test_stage3_clarity_density_wave1.py tests/test_unified_blueprint_validator_lane_c.py tests/test_blueprint_patch_mode.py tests/test_director_auditor_pre_llm_lane.py tests/test_stage2_stage3_episode_boundary_guardrail.py -q`

Observed results:

- static checks: pass
- targeted pytest shards: `359 passed`
- latest bounded pre-run closures are backed by current green shards rather than stale verbal memory only

This is an audit-only doc. No `docs/temp/` mirror was created.

## 4. Answer First

- static `P0`: none
- static `P1`: none newly reopened across Stage2-Stage4
- code-side `P2`: the previously open Stage2 residual trio is now statically closed on the live workspace
- remaining `P2`: mostly document/controller drift, not newly reopened code defects
- remaining `P3`: still significant structural pressure across Stage2, Stage3, Stage4, and `FailureAnalyzer`
- next action before proof does **not** need another broad patch wave
- the right sequence is:
  - freeze this pre-run state
  - execute the fresh run
  - then do one merged S2-S4 post-run 3-pass audit

## 5. Pass 1 Audit

### Structure and scope

The current pre-run tranche is coherent and bounded:

1. Stage2 tactical `[시작 상태]` sync now carries the same finance truth that the structured `arc_start_state` already carries.
   - `modules/core/stage2_finalizer.py:203`
   - `modules/core/stage2_finalizer.py:221`
2. Stage2 runtime-advisory fallback and UI `ep_num` normalization remain landed and green.
   - `modules/core/stage2_finalizer.py:1120`
   - `modules/core/stage2_orchestrator.py:1206`
   - `modules/core/stage2_orchestrator.py:1249`
3. Stage4 aligned green-path parity now explicitly includes `episode_production`.
   - `tests/test_failure_analyzer.py:2530`
4. Stage3 truth-first / opening-authority / advisory-directive normalization still sits on green regression coverage.
   - `modules/core/stage3_orchestrator.py:2033`
   - `modules/domain/agents/blueprint_constraint_compiler.py:716`
   - `modules/domain/agents/unified_blueprint_validator.py:320`
   - `modules/domain/agents/three_phase_blueprint_runtime.py:1389`

No scope-creep or policy violations were found in this tranche.

## 6. Pass 2 Audit

### 6.1 No new static `P0/P1` reopened

The earlier Stage2 `runtime_advisory` / `ep_num` / carryover-truth trio is no longer a live code-side `P2` on this workspace:

- Stage2 tactical finance sync is now present in code and guarded by tests.
  - `modules/core/stage2_finalizer.py:203`
  - `modules/core/stage2_finalizer.py:221`
  - `tests/test_stage2_finalizer.py:1657`
- Stage4 aligned parity now covers `episode_production` on the green path.
  - `tests/test_failure_analyzer.py:2530`
- Stage3 truth-first and advisory hardening continue to validate cleanly.
  - `modules/core/stage3_orchestrator.py:2033`
  - `modules/core/stage3_orchestrator.py:2949`
  - `modules/domain/agents/unified_blueprint_validator.py:2110`
  - `modules/domain/agents/three_phase_blueprint_runtime.py:1389`

Static conclusion: current live workspace does not justify a new code-first `P1` before proof.

### 6.2 Remaining `P2` is now mostly roadmap / SSOT drift

The biggest residual mismatch is no longer production code. It is that several governing docs still describe already-landed Stage2 residuals as open.

1. The active roadmap still says Stage2 `runtime_advisory`, `ep_num`, and carryover-authority truth are open.
   - `docs/2026-04-01/active-temp-execution-roadmap.md:61`
   - `docs/2026-04-01/active-temp-execution-roadmap.md:110`
   - `docs/2026-04-01/active-temp-execution-roadmap.md:193`
2. The Stage2 parent execution SSOT still says the same trio is live residue.
   - `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md:4`
   - `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md:11`
   - `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md:1157`
3. Live code now contradicts that older wording.
   - `modules/core/stage2_finalizer.py:203`
   - `modules/core/stage2_finalizer.py:221`
   - `modules/core/stage2_finalizer.py:1120`
   - `modules/core/stage2_orchestrator.py:1206`
   - `modules/core/stage2_orchestrator.py:1249`

Severity: `P2 doc/controller drift`, not `P2 runtime blocker`.

### 6.3 Minor `P2` doc drift also exists on Stage4 owner-surface recount

The Stage4 owner-surface SSOT is still materially valid, but one complexity recount number is now stale against the current live file.

- execution SSOT still records `159 direct methods / 2 180+ / 5 120+`
  - `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md:145`
  - `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-remediation-execution-ssot.md:196`
- current AST recount is `159 direct methods / 2 180+ / 6 120+`
  - `modules/core/stage4_interview_round.py:2266`
  - `modules/core/stage4_interview_round.py:2509`
  - `modules/core/stage4_interview_round.py:6600`

Severity: low `P2` documentation drift only.

### 6.4 `P3` structural pressure remains the real static debt

Current live recount:

- `Stage2Finalizer`: `51` direct methods / `7` `120+` / `1` `180+`
  - top hotspot: `_record_s2_pass_metrics`
  - `modules/core/stage2_finalizer.py:3463`
- `Stage2Orchestrator`: `51` direct methods / `3` `120+`
  - top hotspots: `_bootstrap_stage2_arc_pipeline`, `_run_stage2_single_arc_attempt`, `_run_stage2_batch_enrichment`
  - `modules/core/stage2_orchestrator.py:1182`
- `FailureAnalyzer`: `75` direct methods / `3` `120+`
  - top hotspots: `_collect_sink_alignment_gate_repair_results`, `_build_sink_alignment_summary_payload`, `patch_trace_summary`
  - `modules/core/failure_analyzer.py:1309`
  - `modules/core/failure_analyzer.py:1785`
  - `modules/core/failure_analyzer.py:2235`
- `Stage3Orchestrator`: `46` direct methods / `4` `120+` / `1` `180+`
  - top hotspot: `_record_stage3_failure_attempt`
  - `modules/core/stage3_orchestrator.py:2949`
- `UnifiedBlueprintValidator`: `46` direct methods / `4` `120+`
  - `modules/domain/agents/unified_blueprint_validator.py:2110`
- `ThreePhaseBlueprintRuntime`: `31` direct methods / `3` `120+` / `1` `180+`
  - top hotspot: `_run_pass_with_fix_iteration`
  - `modules/domain/agents/three_phase_blueprint_runtime.py:1389`
- `BlueprintConstraintCompiler`: `17` direct methods / `3` `120+`
  - top hotspot: `_build_capital_continuity_packet`
  - `modules/domain/agents/blueprint_constraint_compiler.py:716`
- `DirectorContinuityValidator`: `16` direct methods / `1` `120+`
  - `modules/domain/agents/director_continuity.py:209`
- `Stage4InterviewRound`: `159` direct methods / `6` `120+` / `2` `180+`
  - top hotspot: `_append_episode_log`
  - `modules/core/stage4_interview_round.py:6600`

Severity: `P3 structure-first debt`, still correctly behind proof.

## 7. Pass 3 Audit

### Execution and readability

The current queue direction remains sound:

- Stage3 and Stage4 front lanes are still proof-pending, not newly reopened code-blocking `P1`s.
- Stage2 should no longer be described as carrying the older advisory / `ep_num` / carryover-truth code residue.
- The most efficient next action is still one expensive fresh run, not another same-day static patch wave.

Recommended order from here:

1. run the fresh S2-S4 proof wave
2. perform one merged post-run 3-pass audit
3. only then refresh roadmap / SSOT wording and queue bookkeeping
4. keep `P3` owner-surface refactors behind proof unless runtime reopens a functional issue

## 8. Smarter / Elegant Improvement Options

These are not pre-run blockers. They are the highest-value design upgrades after proof.

1. Unify `fix_pack`, `advisory_fix_pack`, `repair_contract`, `scope_authority`, and `partial_fix_eval` into one typed `repair_contract` envelope.
   - `modules/domain/agents/unified_blueprint_validator.py:320`
   - `modules/domain/agents/three_phase_blueprint_runtime.py:1185`
   - `modules/core/stage4_reject_runtime.py:89`
   - `modules/core/db_manager.py:2961`
   - Benefit: less merge/backfill glue, cleaner Stage3/Stage4 retry logic, cheaper sink parity.

2. Move Stage3 to explicit `verdict_layers` instead of letting Python-derived layers silently overwrite Director semantics.
   - `modules/domain/agents/unified_blueprint_validator.py:445`
   - `modules/core/stage4_interview_round.py:2427`
   - `modules/core/stage4_interview_round.py:2509`
   - Benefit: better director-first authority, clearer audit trails between `director_verdict`, `final_verdict`, and gate-driven escalation.

3. Introduce a shared `AttemptEvidencePacket` builder for Stage3/Stage4 sink writes.
   - `modules/core/stage3_orchestrator.py:2033`
   - `modules/core/stage3_orchestrator.py:2186`
   - `modules/core/stage3_orchestrator.py:2949`
   - `modules/core/stage4_interview_round.py:6600`
   - Benefit: reduce duplicated sink assembly and fixture drift.

4. Replace stage-specific sink branching in `FailureAnalyzer` with a declarative stage sink contract descriptor.
   - `modules/core/failure_analyzer.py:1133`
   - `modules/core/failure_analyzer.py:1596`
   - `modules/core/failure_analyzer.py:1898`
   - Benefit: parity widening becomes data-driven instead of requiring multi-site edits.

5. Promote a single `OpeningStatePacket` from Stage2 into Stage3 authority surfaces.
   - `modules/domain/agents/blueprint_constraint_compiler.py:445`
   - `modules/domain/agents/blueprint_constraint_compiler.py:508`
   - `modules/domain/agents/blueprint_constraint_compiler.py:716`
   - Benefit: one precedence path for location, equipment, injuries, and finance continuity instead of several loosely coordinated ones.

6. Replace Stage4->Stage3 free-text retry signal inference with typed `concern_codes` / `patch_objectives`.
   - `modules/core/stage4_orchestrator.py:734`
   - `modules/core/stage4_orchestrator.py:763`
   - `modules/domain/agents/three_phase_blueprint_runtime.py:1430`
   - Benefit: less string-heuristic drift, better retry locality, cleaner tests.

7. Keep advisory packets structured all the way into Director compare instead of flattening them back to summary text too early.
   - `modules/domain/agents/unified_blueprint_validator.py:543`
   - `modules/domain/agents/unified_blueprint_validator.py:1154`
   - `modules/domain/agents/unified_blueprint_validator.py:2186`
   - `modules/domain/agents/director_ensemble.py:138`
   - Benefit: better candidate selection based on patchability, evidence, and target specificity rather than prose smoothness alone.

## 9. Final Judgement

Pre-fresh-run static state is good enough to stop patching and move to proof.

The important nuance is:

- code-side `P2` debt is now materially smaller than the docs still claim
- remaining serious debt is mostly `P3` structure, not a fresh blocking bug
- the next expensive action should be the fresh run, followed by one merged audit, not more same-day static churn

Confidence: `97%`
