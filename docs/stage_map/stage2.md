# Stage 2 Map

## Scope
- Arc 설계 파이프라인을 실행한다: Preflight 상태준비 → FourPhase 생성/보강 → Pre-Director 검증 체인 → Director 전략 심사.
- PASS된 Arc를 저장하고(anchors + txt export), Stage3/Stage4가 사용할 연속성 상태(StateTracker/ConstraintDB/요약 anchor)를 갱신한다.
- Out of scope: Blueprint 생성(Stage3), 원고 집필(Stage4), Bible/Volume 생성(Stage0/1).

## Why
- 왜 FourPhase인가? 초안-자기검증-패치 분기를 한 파이프라인으로 묶어 Stage2 초기 통과율을 높이기 위해서다.
- 왜 앙상블/다중 검증인가? 단일 생성기 편향을 줄이고 DraftValidator·Consensus·ContinuityInspector로 실패 유형을 분해하기 위해서다.
- 왜 Director audit을 분리했나? Python 사전검증은 빠른 필터 역할만 하고, 최종 전략/서사 판정은 Director가 맡는 주권주의를 지키기 위해서다.
- 왜 PASS_WITH_FIX가 있나? (TF-27~34) Director가 "거의 합격이나 소수 수정 필요"를 표현할 수 있도록. fix_scope 기반 3-tier 라우팅(inplace/partial/full)으로 수정 전략을 분기한다.
- 왜 constraint_block을 매 시도마다 초기화하나? (TF-47) retry loop 내에서 advisory 텍스트가 `+=`로 누적되면 3회 시도 시 3배 중복이 되기 때문이다.

## Entry Points
- Primary: `Stage2Orchestrator.stage_2_arcs_async_logic()` (`modules/core/stage2_orchestrator.py`)
- Secondary:
  - `Stage2PreflightAnalysis._preflight_state_setup() / _preflight_arc_analysis() / _preflight_enrichment()`
  - `Stage2ValidationPipeline.run_validation()`
  - `Stage2Finalizer.run_finalize()`
  - Director 심사 진입: `DirectorQualityAuditor.audit_strategic_plan()`

## Inputs
- Required:
  - `current_project.master_bible` (없으면 `load_anchor("bible")`로 복원)
  - `bible_root.plot_roadmap` (Arc source block)
  - 기존 Arc 누적본 `load_anchor("arcs")` (없으면 빈 리스트)
  - 현재 프로젝트/장르 컨텍스트(`selected_genre`, `volumes_strategy`)
- Optional:
  - 사용자 입력 target arc limit (`get_int_input`)
  - StateTracker/ConstraintCompiler/ContextAdvisor/VecMemory/Optimizer/QualityDashboard
  - `previous_attempt`(REJECT 후 패치 모드 판단용)

## Outputs
- Files:
  - Arc 실패 시 `logs/arc_{arc_no}_failure_report.txt` 생성
  - Arc 저장 시 `projects/{project}/plans/arcs/arc_XXX.txt` human-readable export
- DB updates:
  - 최종 Arc 집합: `save_v20_anchor("arcs", all_refined_arcs)` → DB `anchors` 키 `arcs`
  - Stage2 메트릭: `cost_log` (PASS/REJECT), `pass_rate_monitor`, `quality_dashboard` 기록 경유
  - 부가 anchor: `arc_summary_{n}`, `volume_summary_{n}`, `series_summary`, `financial_registry` 등
- In-memory state:
  - `all_refined_arcs`, `current_ep_start`, `current_feedback`, `director_feedback_for_fourphase`
  - `StateTracker` 레지스트리(npc/item/plot/time/skill/financial 등) 증분 갱신
  - `ConstraintDB.arc_states`, `cumulative_state_cache`

## Dependencies
- Internal modules:
  - `Stage2PreflightAnalysis`, `Stage2ValidationPipeline`, `Stage2Finalizer`
  - `FourPhaseArcGenerator`, `ArcEnsembleGenerator`, `UnifiedArcValidator`
  - `DirectorQualityAuditor.audit_strategic_plan()`
  - `ConstraintDB`, `StateTracker`, `ConstraintCompiler`, `SemanticPlotGuard`
  - `NarrativeContextFormatter` (LM-G): 동기/약속/Arc스케일을 `enhanced_context`에 prepend (순수 Python, LLM/DB 없음)
  - `CentralSchemaBuilder` (TF-45): 장르별 프롬프트 스키마 생성 (비무협 장르 오염 방지)
- External services/models:
  - Analyst/Weaver/FourPhase/Director LLM 호출 경로
  - VecMemory 검색 경로(`retrieve_high_res_context` 또는 advisor plan 기반 multi-query)
  - Smart Context Retrieval (SC-0~6): `ContextAdvisor`가 RetrievalPlan 기반 multi-query 실행

## State and Cache
- Persistent state:
  - Arc SSOT: `anchors["arcs"]` (list of Arc dict)
  - Arc txt는 export 전용(참조용), 복구 기준은 DB anchor
- Runtime cache:
  - `self.ctx.cumulative_state_cache` / `cumulative_state_cache_key`
  - Preflight 병렬 계산 캐시(`cached_preflight_result`, `cached_preflight_injection`)
  - Patch 모드 입력 캐시(`_previous_attempt`)
  - FourPhase 내부 캐시/patch fallback state (`pipeline_result`, spare candidates)
- Invalidation rules:
  - Arc PASS 후 `cumulative_state_cache`/key 초기화
  - `state_extractor.invalidate_cache(global_arc_no)`로 동일 Arc 재생성 시 스탈 캐시 제거
  - Arc DB 저장 실패/Director REJECT 시 `st_snapshot` 기반 StateTracker 롤백

## Failure and Recovery
- Common failure patterns:
  - enrich 병렬 실패/데이터 타입 오류/농축 결과 공백
  - FourPhase 생성 실패 또는 Pre-Director 검증(Flow Guard, Duplicate Guard, Draft/Consensus, continuity) REJECT
  - Director REJECT 또는 PASS 후 QualityGate 미달(`score < 90`)
  - Arc 저장 커밋 실패(`safe_commit_async` False/예외)
- Recovery flow:
  - 외부 재시도 루프: `retry.analyst_max_attempts` (기본 5)
  - FourPhase 내부 재시도: `generate(..., max_internal_retries=4)`
  - REJECT 점수 `>= PatchModeThresholds.REWRITE(50)`이면 다음 시도에서 패치 모드 후보 활성화
  - 커밋 실패 시 DB rollback + `all_refined_arcs.pop()` + StateTracker 롤백 후 retry
  - **PASS_WITH_FIX** (TF-27~34): Director가 fix_scope 지정 → inplace면 LLM 1회 국소 수정 + 재심사(최대 3회), partial/full이면 REJECT → retry 경로 위임
- Fallback behavior:
  - 패치 실패 시 전면 재생성 폴백
  - 배치 Arc 최종 실패 시 사용자 선택(건너뛰기/중단/자동 재시도/수동 개입) 지원
  - API quota 패턴 감지 시(Draft+Consensus PASS) Director REJECT를 PASS override
- **constraint_block 초기화** (TF-47): while loop 진입 전 `_base_constraint_block` 저장, 매 시도마다 원본으로 초기화하여 advisory 누적 방지

## Manual Intervention Points
- User prompts:
  - 시작 시 target arc limit 입력
  - Arc 최종 실패 시 `1=skip, 2=stop, 3=retry, 4=manual`
  - 세션 종료 시 Enter 입력
- Approvals:
  - Director `audit_strategic_plan` PASS가 최종 승인(단, QualityGate/저장 실패 시 재시도)
- Operator checks:
  - 실패 리포트 파일(`arc_{n}_failure_report.txt`) 기반 수동 수정 후 재시도 가능

## Metrics
- Throughput:
  - Arc 단위 PASS/REJECT 기록 (`pass_rate_monitor.record_attempt(stage=2, arc=...)`)
- Error rate:
  - `quality_dashboard.record_validation(stage=2)` + `stage_rejection_history`
- Latency:
  - `perf_timer`(preflight/generate/director), Arc 단위 `cost_log` 스냅샷

## Tests
- Unit:
  - `tests/test_stage2_validation_pipeline.py`
  - `tests/test_stage2_preflight.py`
  - `tests/test_stage2_preflight_helpers.py`
  - `tests/test_stage2_finalizer.py`
  - `tests/test_four_phase_arc_generator.py`
  - `tests/test_arc_draft_validator.py`
  - `tests/test_arc_patch_mode.py`
- Integration:
  - `tests/test_stage2_pipeline.py`
  - `tests/test_stage2_context.py`
  - `tests/test_stage2_patch_integration.py`
  - `tests/e2e/test_l3_stage2_realproject.py`
- Regression:
  - `tests/test_stage2_optimizer.py`
  - `tests/test_arc_difficulty.py`
  - `tests/test_stage234_fixes.py`

## Open Risks
- Risk 1: Stage2 패치 진입 조건이 `PatchModeThresholds.REWRITE`(50) 기준으로 연결되어 `patch_below`(80) 설정 의미와 괴리가 있다.
- Risk 2: 실패 처리 구간의 `input()` 기반 분기(수동 선택)는 비대화형/자동화 실행에서 운영 중단 지점이 될 수 있다.

## Last Verified
- Date: 2026-03-02
- Commit: `8476bc2`
- Code Sync (Yes/No): Yes
- Verified By: Opus

