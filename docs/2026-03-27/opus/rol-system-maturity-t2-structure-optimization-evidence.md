Date: 2026-03-27
Type: T2 lane evidence manifest
Parent Report: `docs/2026-03-27/opus/rol-system-maturity-t2-structure-optimization.md`

## Live AST Recount Summary

- Scan date: 2026-03-27
- Scope: `main_a.py` + `modules/core/` + `modules/domain/` + `modules/api/` + `modules/validation/`
- Total files: 252
- Total LOC: 169,087
- Total functions/methods: 4,892
- Total classes: 432
- Parse errors: 0

## Band Distribution

| Band | Count | % |
|------|-------|---|
| 180+ | 3 | 0.06% |
| 150-179 | 21 | 0.43% |
| 120-149 | 74 | 1.51% |
| 100-119 | 91 | 1.86% |
| 80-99 | 182 | 3.72% |
| 60-79 | 301 | 6.15% |
| 40-59 | 592 | 12.10% |
| 20-39 | 1,200 | 24.53% |
| 1-19 | 2,428 | 49.63% |

## 180+ Functions (Complete List)

| LOC | File:Line | Function |
|-----|-----------|----------|
| 205 | `modules/domain/agents/blueprint_ensemble.py:846` | `BlueprintEnsembleGenerator._format_constraints` |
| 184 | `modules/core/stage3_orchestrator.py:2586` | `Stage3Orchestrator._record_stage3_failure_attempt` |
| 184 | `modules/domain/agents/director_ensemble.py:1224` | `DirectorEnsembleSelector._build_ensemble_decision_payload` |

## 150-179 Functions (Top 10)

| LOC | File:Line | Function |
|-----|-----------|----------|
| 174 | `modules/core/stage4_interview_round.py:3635` | `Stage4InterviewRound._run_post_select_checks` |
| 170 | `modules/core/stage4_interview_round.py:5401` | `Stage4InterviewRound._append_episode_log` |
| 166 | `modules/domain/agents/three_phase_blueprint_runtime.py:998` | `ThreePhaseBlueprintRuntime._run_pass_with_fix_iteration` |
| 163 | `modules/core/stage4_reject_runtime.py:422` | `Stage4RejectRuntime._build_reject_guidance_payload` |
| 161 | `modules/validation/blocking_validator_scene_checks.py:258` | `BlockingValidatorSceneChecks._check_cliffhanger_ending` |
| 160 | `main_a.py:3175` | `SovereignApp._build_genre_selection_catalog` |
| 159 | `modules/domain/agents/base_agent.py:2122` | `BaseAgent._ask_with_cached_context` |
| 159 | `modules/domain/agents/chief_writer_context.py:114` | `ChiefWriterContextBuilder.build_common_context` |
| 158 | `modules/core/genre_guards/sports_guard.py:15` | `SportsGuard.__init__` |
| 156 | `modules/domain/agents/analyst.py:664` | `Analyst._prepare_single_arc_plan_context` |

## Owner Pressure — 50+ Direct Methods (Complete List)

| Class | Methods | LOC | File |
|-------|---------|-----|------|
| SovereignApp | 175 | 4,455 | `main_a.py` |
| DBManager | 133 | 3,396 | `modules/core/db_manager.py` |
| StateTracker | 109 | 1,543 | `modules/domain/agents/state_tracker.py` |
| ChiefWriter | 78 | 2,228 | `modules/domain/agents/chief_writer.py` |
| Stage4ContextBuilder | 61 | 2,616 | `modules/core/stage4_context_builder.py` |
| FailureAnalyzer | 60 | 2,360 | `modules/core/failure_analyzer.py` |
| Stage2PreflightAnalysis | 53 | 1,761 | `modules/core/stage2_preflight.py` |
| BaseAgent | 52 | 2,187 | `modules/domain/agents/base_agent.py` |
| Stage2Orchestrator | 51 | 1,654 | `modules/core/stage2_orchestrator.py` |

## Owner Pressure — 30-49 Direct Methods (Top 10)

| Class | Methods | LOC | File |
|-------|---------|-----|------|
| ContinuityInspector | 48 | 1,267 | `modules/domain/agents/continuity_inspector.py` |
| StateTrackerNPC | 48 | 766 | `modules/domain/agents/state_tracker_npc.py` |
| Stage01Helpers | 45 | 992 | `modules/core/stage01_helpers.py` |
| VecMemory | 44 | 1,191 | `modules/core/vec_memory.py` |
| ValidationOrchestrator | 43 | 1,082 | `modules/validation/validation_orchestrator.py` |
| Stage4InterviewRound | 42 | 5,573 | `modules/core/stage4_interview_round.py` |
| Stage3Orchestrator | 41 | 2,815 | `modules/core/stage3_orchestrator.py` |
| Stage4Orchestrator | 39 | 2,376 | `modules/core/stage4_orchestrator.py` |
| BridgeServer | 38 | 2,334 | `modules/api/bridge_server.py` |
| DirectorEnsembleSelector | 37 | 2,014 | `modules/domain/agents/director_ensemble.py` |

## V2 Audit Baseline vs Live Delta

| Metric | V2 Audit (2026-03-22) | Live (2026-03-27) | Delta |
|--------|----------------------|-------------------|-------|
| Files | 267 | 252 | -15 |
| LOC | 166,410 | 169,087 | +2,677 |
| Functions | 4,697 | 4,892 | +195 |
| Classes | 474 | 432 | -42 |
| 180+ | 0 | 3 | +3 |
| 100+ | 171 | 189 | +18 |
| 50+ method classes | 12 | 9 | -3 |

## Dirty Workspace Structural Impact

| File | Net Lines | Structural Risk |
|------|-----------|-----------------|
| `modules/core/stage3_orchestrator.py` | +83 | No new 180+; new function `_apply_stage3_dead_npc_precheck` at 66 LOC |
| `modules/core/stage4_context_builder.py` | +53 | `_build_tier0_mandatory_sections` grew 101→134 (crossed 120 threshold) |
| `modules/validation/blocking_validator_consistency_checks.py` | +59 | New function `_check_wuxia_technique_realm_consistency` at 58 LOC |
| `modules/core/providers/anthropic_vertex_provider.py` (new) | 67 | Clean thin subclass, 4 small methods |

## Module Split Verification

All 11 extracted runtime modules confirmed present in live workspace:

| Module | Present |
|--------|---------|
| `stage4_retry_runtime.py` | Yes |
| `stage4_reject_runtime.py` | Yes |
| `stage4_director_runtime.py` | Yes |
| `stage4_context_packets.py` | Yes |
| `stage4_outcome_runtime.py` | Yes |
| `stage4_post_pass_runtime.py` | Yes |
| `stage4_episode_logging.py` | Yes |
| `stage2_preflight_runtime.py` | Yes |
| `db_bootstrap_runtime.py` | Yes |
| `three_phase_blueprint_runtime.py` | Yes |
| `four_phase_arc_runtime.py` | Yes |
