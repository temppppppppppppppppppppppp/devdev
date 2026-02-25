# Agent Graph

Purpose:
- Stage 2/3/4에서 어떤 모듈/에이전트가 어떤 모듈/에이전트를 호출하는지 텍스트 트리로 정리한다.
- 버그 위치 역추적 시 출발점으로 사용한다.

## Stage 2 호출 트리
```text
stage2_orchestrator.stage_2_arcs_async_logic()
  ├─ preflight._preflight_state_setup()
  │   ├─ agents["weaver"].generate_arc_drive()
  │   ├─ agents["preflight"].analyze() -> generate_analyst_injection()
  │   └─ constraint_db.generate_constraint_block()
  ├─ preflight._preflight_arc_analysis()
  │   └─ agents["state_extractor"].extract_cumulative_state()
  ├─ preflight._preflight_enrichment()
  │   └─ agents["four_phase"].patch_arc_with_feedback() or generate(max_internal_retries=4)
  ├─ validation_pipeline.run_validation()
  │   ├─ arc_draft_validator.validate()
  │   ├─ agents["consensus"].validate_with_consensus()
  │   ├─ _stage2_flow_guard()
  │   └─ agents["continuity_inspector"].inspect_arc()
  └─ finalizer.run_finalize()
      └─ agents["director"].audit_strategic_plan()
          └─ DirectorQualityAuditor.audit_strategic_plan()
```

## Stage 3 호출 트리
```text
stage3_orchestrator.stage_3_batch_blueprinting()
  └─ _generate_blueprint()
      └─ agents["three_phase_bp"].generate()
          ├─ BlueprintConstraintCompiler.compile()
          ├─ BlueprintEnsembleGenerator.generate_ensemble()
          │   └─ ThreadPoolExecutor(max_workers=3) -> _generate_single() x N
          ├─ UnifiedBlueprintValidator.validate()
          │   └─ director.compare_and_select_blueprint()
          │       └─ DirectorEnsembleSelector.compare_and_select_blueprint()
          ├─ QualityGate (blueprint_quality_gate_score=80)
          └─ (REJECT 시) _inplace_patch_blueprint()  # 단일 LLM 수정
```

## Stage 4 호출 트리
```text
stage4_orchestrator.stage_4_v2_chief_writer()
  ├─ _prepare_stage4_session()
  │   ├─ ChiefWriter()
  │   ├─ ManuscriptValidator()
  │   ├─ ConsistencyValidator()
  │   ├─ BlockingValidator()
  │   └─ ContinuityValidator()
  └─ _run_interview_loop()
      ├─ current_project.get_blueprint(next_ep)  # DB blueprints
      ├─ context_builder.prepare_episode_context()
      ├─ _handle_round_outcome()
      │   └─ stage4_interview_round.run()  # 최대 5 라운드
      │       ├─ chief_writer.generate_ensemble() / regenerate_with_feedback() / patch_with_feedback()
      │       ├─ manuscript_validator.validate_all_candidates()
      │       ├─ consistency_validator.validate()
      │       ├─ blocking_validator.validate()
      │       ├─ continuity_validator.validate()
      │       └─ agents["director"].select_and_judge_ensemble()
      │           └─ DirectorEnsembleSelector.select_and_judge_ensemble()
      ├─ post-select checks
      │   ├─ agents["director"].check_manuscript_continuity_with_cache()
      │   └─ agents["director"].check_manuscript_history_conflicts()
      └─ post_processor.process_pass_result()
```

## 확인 메모
- Stage 3 병렬 생성은 실제 `ThreadPoolExecutor(max_workers=3)`로 구현되어 있다.
- `UnifiedBlueprintValidator`의 다후보 경로는 `director.compare_and_select_blueprint()` 호출이 핵심이며, 별도 다른 에이전트 fan-out은 없다.
- Stage 4의 Director는 `main_a.py`에서 등록되는 `agents["director"] = Director(...)`이다.
- 즉 Stage 4는 `director_continuity.py` 단독 에이전트를 직접 쓰는 구조가 아니라, `Director` 파사드 내부 위임(`DirectorEnsembleSelector`, `DirectorContinuityValidator`, `DirectorQualityAuditor`) 구조다.

## 확인 위치
- `modules/core/stage2_orchestrator.py:430`
- `modules/core/stage2_preflight.py:658`
- `modules/core/stage2_validation_pipeline.py:472`
- `modules/core/stage2_finalizer.py:133`
- `modules/core/stage3_orchestrator.py:591`
- `modules/domain/agents/blueprint_ensemble.py:17`
- `modules/domain/agents/blueprint_ensemble.py:210`
- `modules/domain/agents/unified_blueprint_validator.py:102`
- `modules/core/stage4_orchestrator.py:335`
- `modules/core/stage4_interview_round.py:811`
- `main_a.py:1462`
- `modules/domain/agents/director.py:5`
