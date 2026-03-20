# Long-Function Decomposition Live Re-Audit (3Pass)

Date: 2026-03-20
Status: final
Canonical Path: `docs/2026-03-20/long-function-decomposition-live-reaudit-3pass-audit.md`
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: pre-existing stage4/smoke/doc changes, project artifact churn, docs/mmmm intake; no active temp execution queue at start`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/TF-static-complexity-audit.md`
Evidence Artifacts:
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage2_preflight.py`
- `modules/core/failure_analyzer.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/domain/agents/four_phase_arc_generator.py`
- `modules/domain/agents/director_ensemble.py`
Side-Effect Coverage: covered

## 1. Intent
- Re-audit `TF-static-complexity-audit.md` from live code instead of treating it as self-proving authority.
- Establish which long-function hotspots are real, which are first-tranche execution candidates, and which should remain deferred despite size.

## 2. Scope
Included:
- Production Python runtime surfaces only.
- Long-function size, execution-friendliness, nearby regression coverage, and policy-risk screening.

Excluded:
- `tests/`, `docs/`, `projects/`, embedded vendor libraries, and direct realization work.
- Full cyclomatic re-measurement beyond what is needed to validate execution-candidate ranking.

## 3. Pass 1. Live Size Recheck
- The TF document was not an OPUS collector artifact and already contained substantial live truth.
- A direct AST recheck against production files confirmed the main hotspot set.
- One audit caveat surfaced: several core files are saved as `utf-8-sig`, so naive `utf-8` parsers can silently miss them. This is an analysis boundary issue, not a refactor finding.

Validated live hotspot lengths:

| Surface | Live LOC |
| --- | ---: |
| `Stage4InterviewRound.run` | 1,149 |
| `Stage2Finalizer.run_finalize` | 1,134 |
| `Stage2Orchestrator.stage_2_arcs_async_logic` | 788 |
| `ThreePhaseBlueprintGenerator.generate` | 739 |
| `DirectorEnsemble.select_and_judge_ensemble` | 660 |
| `Stage2Preflight._preflight_enrichment` | 656 |
| `FailureAnalyzer.sink_alignment_summary` | 628 |
| `FourPhaseArcGenerator.generate` | 620 |
| `Stage4ContextBuilder.build_mandatory_context` | 611 |
| `Stage4Orchestrator._handle_round_outcome` | 490 |

## 4. Pass 2. Execution-Friendliness Classification
Execution-friendliness was judged on four axes:
- clear internal phase boundaries already visible in the code
- existing regression surface close to the function
- limited policy-sovereignty entanglement
- reasonable chance to extract orchestration helpers without changing runtime meaning

### 4.1 First-Tranche Friendly
- `Stage2Finalizer.run_finalize`
  - Large, but already surrounded by many local helpers and dense Stage 2 regression coverage.
  - Strong candidate for orchestration-wrapper extraction.
- `Stage2Orchestrator.stage_2_arcs_async_logic`
  - Very long and phase-structured: bootstrap, batch enrichment, per-arc processing, finalize/recovery.
  - Best realized after `Stage2Finalizer`, not before.
- `Stage4ContextBuilder.build_mandatory_context`
  - High branch density, but unusually rich unit-test surface.
  - Good candidate for tier-assembly and retrieval-section extraction.

### 4.2 Reserve / Later Candidates
- `Stage4Orchestrator._handle_round_outcome`
  - Strong execution candidate in isolation, but smaller and recently modified.
  - Better kept as reserve until the first decomposition queue stabilizes.
- `Stage2Preflight._preflight_enrichment`
  - Long and action-bearing, but partially overlaps Stage 2 orchestration contracts.
  - Better handled after `stage_2_arcs_async_logic`.
- `FailureAnalyzer.sink_alignment_summary`
  - Long and test-backed, but less urgent than Stage 2 and Stage 4 production orchestration surfaces.

### 4.3 Explicitly Deferred Despite Size
- `Stage4InterviewRound.run`
  - Longest surface, but tightly coupled to Stage 4 governance, retry policy, and director sovereignty semantics.
  - Poor first-tranche ROI despite size.
- `DirectorEnsemble.select_and_judge_ensemble`
  - Semantically central and policy-heavy; the blast radius is larger than the raw LOC implies.
- `ThreePhaseBlueprintGenerator.generate`
  - Long, but currently intertwined with prompt/selection semantics and recent Stage 3 ownership work.
- `FourPhaseArcGenerator.generate`
  - Long and important, but Stage 2 pacing ownership changed recently, making it a worse first decomposition target right now.

## 5. Pass 3. Re-Audit Outcome
The TF static audit remains usable as a low-noise starting point, but it is not the execution queue by itself.

Canonical shortlist for immediate decomposition planning:
1. `Stage2Finalizer.run_finalize`
2. `Stage2Orchestrator.stage_2_arcs_async_logic`
3. `Stage4ContextBuilder.build_mandatory_context`

Reserve shortlist:
1. `Stage4Orchestrator._handle_round_outcome`
2. `Stage2Preflight._preflight_enrichment`
3. `FailureAnalyzer.sink_alignment_summary`

## 6. Operating Consequence
- Proceed to a dedicated hotspot survey using the validated shortlist above.
- Promote only the action-bearing shortlist into execution SSOTs.
- Because more than one execution item is expected, an aggregate roadmap should be created in the same turn as the SSOTs.

## 7. Confidence
- Estimated confidence after 3-pass re-audit: `0.96`
- Rationale:
  - live LOCs were directly rechecked
  - nearby regression files were verified to exist
  - first-tranche selection is bounded by current policy-risk, not only by raw size
