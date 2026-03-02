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
      │       ├─ [Advisory 체인] _director_mc_parts 수집 (LM-A~F)
      │       │   ├─ TruthGate.validate()           # LM-A: 7개 팩트 검사
      │       │   ├─ NpcDriftAdvisor.check()         # LM-B: NPC 속성 표류
      │       │   ├─ NumericDriftAdvisor.check()      # LM-C: 수치 누적 표류
      │       │   ├─ FlashbackVerifier.verify()       # LM-E: 회상 오염 감지
      │       │   ├─ InfoParadoxChecker.check()       # LM-F: 1인칭 정보 역설
      │       │   └─ RelationshipDriftAdvisor.check() # LM-D: 관계도 표류
      │       └─ agents["director"].select_and_judge_ensemble()
      │           └─ DirectorEnsembleSelector.select_and_judge_ensemble()
      ├─ [PASS_WITH_FIX 경로] (TF-27~34)
      │   ├─ fix_scope="inplace" → chief_writer.inplace_patch()
      │   │   └─ patch_state_updates JSON 추출 (TF-47: rfind+json.loads)
      │   │   └─ state_updates merge: {**final, **patch}
      │   │   └─ Director audit_manuscript() 재심사 (최대 3회)
      │   ├─ fix_scope="partial" → single_strategy 1후보 재생성
      │   └─ fix_scope="full" → Ensemble 3후보 전면 재생성
      ├─ post-select checks
      │   ├─ agents["director"].check_manuscript_continuity_with_cache()
      │   └─ agents["director"].check_manuscript_history_conflicts()
      └─ post_processor.process_pass_result()
```

## Stage 2 Advisory (LM-G)
```text
stage2_preflight._preflight_arc_analysis()
  └─ NarrativeContextFormatter.format()  # LM-G: 동기/약속/Arc스케일 enrichment
      → enhanced_context에 prepend (순수 Python, LLM/DB 없음)
```

## 확인 메모
- Stage 3 병렬 생성은 실제 `ThreadPoolExecutor(max_workers=3)`로 구현되어 있다.
- `UnifiedBlueprintValidator`의 다후보 경로는 `director.compare_and_select_blueprint()` 호출이 핵심이며, 별도 다른 에이전트 fan-out은 없다.
- Stage 4의 Director는 `main_a.py`에서 등록되는 `agents["director"] = Director(...)`이다.
- 즉 Stage 4는 `director_continuity.py` 단독 에이전트를 직접 쓰는 구조가 아니라, `Director` 파사드 내부 위임(`DirectorEnsembleSelector`, `DirectorContinuityValidator`, `DirectorQualityAuditor`) 구조다.
- Stage 4 Advisory 체인(LM-A~F)은 `_director_mc_parts`에 주입되어 Director 최종 판정의 근거 자료로 사용된다. 모두 비차단(실패 시 빈 결과).
- Context Caching: 6개 사이트 캐싱 적용 완료 — ChiefWriter/ArcEnsemble/BlueprintEnsemble fan-out, DirectorEnsemble stable/variable, DirectorContinuity Blueprint/Manuscript.
- Smart Context Retrieval (SC-0~6): `ContextAdvisor`가 RetrievalPlan 기반 multi-query 실행. Stage 2/3/4 공통.

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
