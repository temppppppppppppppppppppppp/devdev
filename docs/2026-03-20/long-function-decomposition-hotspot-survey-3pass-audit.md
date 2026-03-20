# Long-Function Decomposition Hotspot Survey (3Pass)

Date: 2026-03-20
Status: final
Canonical Path: `docs/2026-03-20/long-function-decomposition-hotspot-survey-3pass-audit.md`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: pre-existing stage4/smoke/doc changes, project artifact churn, docs/mmmm intake; no active temp execution queue at start`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/TF-static-complexity-audit.md`
- `docs/2026-03-20/long-function-decomposition-live-reaudit-3pass-audit.md`
Evidence Artifacts:
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_pass_with_fix.py`
- `tests/test_stage2_pipeline.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_continuity_packet.py`
Side-Effect Coverage: covered

## 1. Intent
- Turn the live re-audit into an execution-ready hotspot survey.
- Select the smallest high-ROI bundle that is still meaningful enough to warrant a queue and roadmap.

## 2. Selection Rule
Hotspots were ranked using:
- decomposition leverage
- nearby regression readiness
- policy/governance blast radius
- expected helper-extraction clarity

## 3. Hotspot Matrix

| Candidate | Live LOC | Test Surface | First-Tranche Verdict | Reason |
| --- | ---: | --- | --- | --- |
| `Stage2Finalizer.run_finalize` | 1,134 | strong | promote | largest Stage 2 orchestration knot with strong direct tests |
| `Stage2Orchestrator.stage_2_arcs_async_logic` | 788 | medium-strong | promote | clear phase boundaries, but depends on Stage 2 substrate clarity |
| `Stage4ContextBuilder.build_mandatory_context` | 611 | very strong | promote | branch-heavy but unusually well-tested |
| `Stage4Orchestrator._handle_round_outcome` | 490 | strong | reserve | good later item, but smaller and recently touched |
| `Stage2Preflight._preflight_enrichment` | 656 | medium | reserve | overlaps Stage 2 orchestrator sequencing |
| `FailureAnalyzer.sink_alignment_summary` | 628 | strong | reserve | valuable but lower leverage than the first three |
| `Stage4InterviewRound.run` | 1,149 | medium | defer | too policy-heavy for tranche 1 |
| `DirectorEnsemble.select_and_judge_ensemble` | 660 | strong | defer | sovereignty and grading semantics dominate raw size |
| `ThreePhaseBlueprintGenerator.generate` | 739 | medium | defer | recent Stage 3 semantics still settling |
| `FourPhaseArcGenerator.generate` | 620 | medium | defer | Stage 2 pacing ownership recently changed |

## 4. Action-Bearing Split

### 4.1 Promote Now
1. `Stage2Finalizer.run_finalize`
2. `Stage2Orchestrator.stage_2_arcs_async_logic`
3. `Stage4ContextBuilder.build_mandatory_context`

### 4.2 Keep as Reserve
1. `Stage4Orchestrator._handle_round_outcome`
2. `Stage2Preflight._preflight_enrichment`
3. `FailureAnalyzer.sink_alignment_summary`

### 4.3 Explicit Deferrals
- `Stage4InterviewRound.run`
- `DirectorEnsemble.select_and_judge_ensemble`
- `ThreePhaseBlueprintGenerator.generate`
- `FourPhaseArcGenerator.generate`

## 5. Why This Bundle Has the Best ROI
- It creates a real queue of three substantial items without immediately entering Stage 4 sovereignty refactors.
- Two items sit in Stage 2, allowing shared realization thinking instead of one-off cleanup.
- The Stage 4 item is branch-heavy but protected by the strongest direct test surface in the bundle.
- All three are orchestration/builder surfaces where helper extraction can lower review cost before any semantic rewrite.

## 6. Required Queue Shape
- Create one canonical execution SSOT per promoted hotspot.
- Create a single aggregate roadmap because the queue size is `3`.
- Start with the Stage 2 substrate item before the broader Stage 2 orchestrator item.

Recommended order:
1. `stage2-finalizer-run-finalize-decomposition`
2. `stage2-orchestrator-stage-2-arcs-async-logic-decomposition`
3. `stage4-context-builder-build-mandatory-context-decomposition`

## 7. Confidence
- Estimated confidence after 3-pass hotspot survey: `0.96`
- Enough to open an execution-doc queue, but not to start patching without revalidation at execution start.
