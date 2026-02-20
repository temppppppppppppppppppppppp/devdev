# Codex Manual Runtime Agent Inventory (2026-02-20)

## Purpose
- Answer the question: should we identify major agents first?
- Scope: Stage2/3/4 runtime paths, Pydantic touchpoints, Protocol/ABC status.
- Method: manual code inspection with file/line evidence.

## 1) Runtime agent registry (`self.agents`)
- Evidence: `main_a.py:1322` to `main_a.py:1381`

| key | class | evidence |
|---|---|---|
| `analyst` | `Analyst` | `main_a.py:1323` |
| `writer` | `Writer` | `main_a.py:1327` |
| `director` | `Director` | `main_a.py:1330` |
| `manager` | `Manager` | `main_a.py:1333` |
| `weaver` | `Weaver` | `main_a.py:1337` |
| `continuity_inspector` | `ContinuityInspector` | `main_a.py:1343` |
| `critic` | `Critic` | `main_a.py:1348` |
| `state_extractor` | `StateExtractor` | `main_a.py:1350` |
| `arc_ensemble` | `ArcEnsembleGenerator` | `main_a.py:1354` |
| `four_phase` | `FourPhaseArcGenerator` | `main_a.py:1358` |
| `state_locked` | `StateLockedArcGenerator` | `main_a.py:1362` |
| `preflight` | `PreflightChecker` | `main_a.py:1366` |
| `arc_critic` | `ArcCritic` | `main_a.py:1370` |
| `consensus` | `ConsensusValidator` | `main_a.py:1374` |
| `three_phase_bp` | `ThreePhaseBlueprintGenerator` | `main_a.py:1378` |

### Stage2 helper modules outside `self.agents`
- Evidence: `main_a.py:1384` to `main_a.py:1396`
- `arc_draft_validator`
- `constraint_compiler`
- `negative_injector`
- `arc_corrector`
- `stage2_optimizer`

## 2) Actual stage call chains

### Stage2 (Arc)
- Orchestrator submodules:
- `Stage2ValidationPipeline` lazy init: `modules/core/stage2_orchestrator.py:56` to `modules/core/stage2_orchestrator.py:62`
- `Stage2PreflightAnalysis` lazy init: `modules/core/stage2_orchestrator.py:65` to `modules/core/stage2_orchestrator.py:71`
- `Stage2Finalizer` lazy init: `modules/core/stage2_orchestrator.py:74` to `modules/core/stage2_orchestrator.py:80`

- Preflight calls:
- `weaver.generate_arc_drive(...)`: `modules/core/stage2_preflight.py:50`
- `preflight.analyze(...)`: `modules/core/stage2_preflight.py:83`
- `preflight.generate_analyst_injection(...)`: `modules/core/stage2_preflight.py:87`
- `state_extractor.extract_cumulative_state(...)`: `modules/core/stage2_preflight.py:146`, `modules/core/stage2_preflight.py:386`
- `four_phase.patch_arc_with_feedback(...)`: `modules/core/stage2_preflight.py:512`
- `four_phase.generate(...)`: `modules/core/stage2_preflight.py:534`

- Validation calls:
- `arc_draft_validator.validate(...)`: `modules/core/stage2_validation_pipeline.py:67`, `modules/core/stage2_validation_pipeline.py:258`
- `consensus.validate_with_consensus(...)`: `modules/core/stage2_validation_pipeline.py:134`
- `continuity_inspector.inspect_arc(...)`: `modules/core/stage2_validation_pipeline.py:397`

- Finalizer calls:
- `director.audit_strategic_plan(...)`: `modules/core/stage2_finalizer.py:133`
- Pydantic Arc validation (`ingress+egress`): `modules/core/stage2_finalizer.py:307`

### Stage3 (Blueprint)
- Entity registry extraction:
- `state_extractor.extract_cumulative_state(...)`: `modules/core/stage3_orchestrator.py:344`

- Blueprint generation:
- `three_phase_bp.generate(...)`: `modules/core/stage3_orchestrator.py:434`
- `director` passed into generator: `modules/core/stage3_orchestrator.py:440`

### Stage4 (Manuscript)
- Stage4 builds local runtime objects (not only `app.agents`):
- `ChiefWriter`: `modules/core/stage4_orchestrator.py:646`
- `ManuscriptValidator`: `modules/core/stage4_orchestrator.py:652`
- `ConsistencyValidator`: `modules/core/stage4_orchestrator.py:655`
- `BlockingValidator`: `modules/core/stage4_orchestrator.py:657`
- `ContinuityValidator`: `modules/core/stage4_orchestrator.py:658`

- Interview round core calls:
- `chief_writer.generate_ensemble(...)`: `modules/core/stage4_interview_round.py:124`
- `chief_writer.patch_with_feedback(...)`: `modules/core/stage4_interview_round.py:137`
- `chief_writer.regenerate_with_feedback(...)`: `modules/core/stage4_interview_round.py:149`, `modules/core/stage4_interview_round.py:156`
- `manuscript_validator.validate_all_candidates(...)`: `modules/core/stage4_interview_round.py:236`
- `director.select_and_judge_ensemble(...)`: `modules/core/stage4_interview_round.py:568`

## 3) Stage4 conditional modules (context-driven)
- Key list is defined in `modules/core/stage4_context.py:4` to `modules/core/stage4_context.py:13`
- Accessor is `get_module(...)` in `modules/core/stage4_context.py:123`

Actual usage:
- `prompt_weighter`: `modules/core/stage4_interview_round.py:112`
- `adversarial_self_play`: `modules/core/stage4_interview_round.py:164`
- `pre_director_checklist`: `modules/core/stage4_interview_round.py:476`
- `confidence_calibrator`: `modules/core/stage4_interview_round.py:497`
- `cross_verifier`: `modules/core/stage4_interview_round.py:514`
- `tree_of_thoughts`: `modules/core/stage4_interview_round.py:690`
- `multi_agent_deliberation`: `modules/core/stage4_interview_round.py:704`
- `chain_of_verification`: `modules/core/stage4_orchestrator.py:547`

## 4) Pydantic integration status
- Model definitions:
- Arc model: `modules/models/arc.py:163` (`ArcData`), `modules/models/arc.py:206` (`validate_arc`)
- Blueprint model: `modules/models/blueprint.py:29` (`Blueprint`), `modules/models/blueprint.py:65` (`validate_blueprint`)
- Manuscript candidate model: `modules/models/manuscript.py:18` (`ManuscriptCandidate`), `modules/models/manuscript.py:43` (`validate_manuscript_candidate`)

- Runtime integration points:
- Stage2 finalizer uses `validate_arc(...)`: `modules/core/stage2_finalizer.py:307`
- Stage3 generator uses `validate_blueprint(...)`: `modules/domain/agents/three_phase_blueprint_generator.py:376`
- ChiefWriter uses `validate_manuscript_candidate(...)`: `modules/domain/agents/chief_writer.py:382`

## 5) Protocol and ABC status

### Protocol
- Protocol definitions: `modules/protocols/agents.py:57` to `modules/protocols/agents.py:159`
- `ManuscriptValidator` protocol-alias bridge exists:
- `validate = validate_candidate`: `modules/domain/agents/manuscript_validator.py:194`

- Repository-wide import check:
- `modules.protocols` imports appear in `modules/protocols/__init__.py:12` to `modules/protocols/__init__.py:30` and test files.
- No direct production-stage runtime binding call to protocols was confirmed in Stage2/3/4 execution paths.

### ABC
- Active ABC hotspots:
- `BaseGuard(ABC)`: `modules/core/genre_guards/base_guard.py:16`
- `GenreHUDManager(ABC)`: `modules/core/genre_hud_manager.py:10`
- `BaseStrategy(ABC)`: `modules/domain/strategies/base_strategy.py:4`

## 6) Decision
- Yes, major-agent mapping should be done first.
- Recommended order:
1. Freeze runtime baseline: `self.agents` + Stage2 helper modules.
2. Freeze execution baseline: actual calls in Stage2/3/4.
3. Then expand Pydantic/Protocol/ABC rollouts.

Reason:
- Registered components and actually-called components are not identical.
- Stage4 especially uses additional local validators and context-driven modules.
- This split must be explicit to avoid false positives and bad refactor order.

## Appendix: `modules/domain/agents` inventory summary
- Manual class scan completed for `modules/domain/agents/*.py`.
- Core production classes include:
- `Analyst`, `Director`, `Writer`, `Weaver`, `Manager`
- `FourPhaseArcGenerator`, `ThreePhaseBlueprintGenerator`, `ArcEnsembleGenerator`
- `ConsensusValidator`, `ContinuityInspector`, `ArcCritic`
- `StateExtractor`, `StateTracker`, `ArcDraftValidator`, `ConstraintCompiler`, `ArcCorrector`
- `ChiefWriter`, `ManuscriptValidator`
