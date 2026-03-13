# Stage 2 Map

## Scope
- Define what Stage 2 is responsible for.
  - `MasterBible.plot_roadmap`를 Arc 단위로 읽어 배치별 농축, 인과율 용접, Arc 설계, Director 심사까지 수행한다.
  - PASS한 Arc만 `arcs` 앵커와 txt export에 저장하고, StateTracker/ConstraintDB/요약 앵커를 갱신한다.
  - Stage 2는 권 전략(`volumes`)을 참조하지만, 비어 있어도 기본 `strategy_doc=""`로 계속 진행한다.
  - Python 검증기들은 대부분 advisory를 조립해 Director에게 넘기고, 최종 PASS/REJECT는 Director와 QualityGate가 확정한다.
- Out of scope:
  - Bible/Treatment/권 전략 생성(Stage 0/1 책임).
  - Blueprint 생성(Stage 3 책임).
  - 원고 생성(Stage 4 책임).
  - Arc 실패 후 자동 완전 복구. 현재 구현은 재시도와 수동 개입 분기까지가 한계다.

## Why
- 왜 Stage 2를 별도 파이프라인으로 두는가? Arc는 장기 연재에서 가장 많은 인과/연속성 결정을 담는 중간 산출물이기 때문이다.
- 왜 배치 농축과 순차 설계를 같이 쓰는가? 전처리는 병렬로 처리하되, 실제 Arc 설계는 이전 Arc 상태를 물고 가야 하기 때문이다.
- 왜 검증을 advisory 중심으로 돌리는가? Python이 결함 신호를 빨리 모으되, 최종 서사 판정은 Director가 하도록 주권을 남겨두기 위해서다.
- 왜 PASS_WITH_FIX가 있는가? 거의 통과 가능한 Arc를 전면 재생성 대신 국소 수정으로 살리기 위해서다.

## Entry Points
- Primary:
  - `Stage2Orchestrator.stage_2_arcs_async_logic(target_arc_count=None)`
- Secondary:
  - `Stage2PreflightAnalysis._preflight_state_setup()`
  - `Stage2PreflightAnalysis._preflight_arc_analysis()`
  - `Stage2PreflightAnalysis._preflight_enrichment()`
  - `Stage2ValidationPipeline.run_validation()`
  - `Stage2Finalizer.run_finalize()`
- Notes:
  - Stage 2는 배치 크기 5, 농축 병렬도 5(`asyncio.Semaphore(5)`)를 사용한다.
  - 프로그래밍 호출 시 `target_arc_count`로 상한을 줄일 수 있고, 대화형 실행은 기본 5개 Arc 범위로 안내된다.

## Inputs
- Required:
  - `current_project.master_bible`
    - 없으면 `load_anchor("bible")`로 복원 시도
  - `MasterBible.plot_roadmap`
  - `current_project.db.load_anchor("arcs")`
  - `agents["analyst"]`
  - `agents["director"]`
- Optional:
  - `current_project.volumes`
    - 없으면 `load_anchor("volumes")`, 그래도 없으면 권 전략 없이 진행
  - `selected_genre`
  - `StateTracker`
  - `ConstraintCompiler`
  - `ConstraintDB`
  - `VecMemory` / `ContextAdvisor`
  - `quality_dashboard`
  - `pass_rate_monitor`
  - `stage2_optimizer`
  - `previous_attempt`
    - 이전 REJECT Arc를 패치/재생성 라우팅할 때 사용
  - 기존 원고 수
    - `get_max_episode_from_manuscripts()`가 있으면 smart skip 경고에 사용

## Outputs
- Files:
  - `plans/arcs/arc_XXX.txt`
    - `save_v20_anchor("arcs", ...)` 경유 human-readable export
  - `logs/arc_{arc_no}_failure_report.txt`
    - 최종 실패 시 생성
- DB updates:
  - `save_v20_anchor("arcs", all_refined_arcs)`
  - 선택적 `financial_registry`
  - 선택적 `volume_summary_{n}`
  - 선택적 `series_summary`
  - `stage_attempts`
  - `director_selections`
  - `cost_record`
  - Arc dependency graph (`upsert_arc_dependency`)
- In-memory state:
  - `all_refined_arcs`
  - `current_ep_start`
  - `last_refined_context`
  - `current_feedback`
  - `director_feedback_for_fourphase`
  - `StateTracker`
  - `ConstraintDB.arc_states`
  - `cumulative_state_cache`

## Dependencies
- Internal modules:
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_finalizer.py`
  - `modules/core/stage2_context.py`
  - `modules/core/constraint_db.py`
  - `modules/domain/agents/state_tracker.py`
  - `modules/domain/agents/four_phase_arc_generator.py`
  - `modules/core/context_advisor.py`
  - `modules/core/project_manager.py`
- External services/models:
  - Analyst
    - block 농축
    - lack report
    - joint stitch
  - Weaver
    - `generate_arc_drive()`
  - Preflight agent
    - 누적 Arc 분석
  - FourPhase
    - `generate()`
    - `_inplace_patch_arc()`
    - `patch_arc_with_feedback()`
  - Director
    - `audit_strategic_plan()`
    - 요약 생성용 `ask()`
  - optional Consensus / SelfReflector / ContinuityInspector / VecMemory

## State and Cache
- Persistent state:
  - Arc SSOT는 `anchors["arcs"]`다.
  - `plans/arcs/*.txt`는 export 전용이다.
- Runtime cache:
  - `cumulative_state_cache`
  - `cumulative_state_cache_key`
  - `_cached_preflight_result`
  - `_cached_preflight_injection`
  - `_previous_attempt`
  - `last_refined_context`
- Invalidation rules:
  - Arc PASS 후 `cumulative_state_cache`와 key를 비운다.
  - 동일 Arc 재시도/다음 시도 시 `state_extractor.invalidate_cache(global_arc_no)`를 호출한다.
  - DB 커밋 실패나 Director REJECT 시 `st_snapshot`으로 StateTracker를 롤백한다.
  - retry 루프에서는 `_base_constraint_block`을 저장해 매 시도마다 constraint/advisory 누적을 막는다.

## Failure and Recovery
- Common failure patterns:
  - 농축 결과 예외 또는 타입 오류
  - FourPhase 생성 실패
  - malformed `refined_arc` / `enriched_block`
  - Director REJECT
  - PASS이지만 `quality_gate_score` 미달
  - DB 커밋 실패
- Recovery flow:
  - 배치 농축은 `asyncio.gather()` 후 실패 항목만 순차 재시도한다.
  - Arc 시도 횟수는 `retry.analyst_max_attempts`를 따른다.
    - 현재 `validation.yaml` 기준 `10`
  - FourPhase 전면 생성은 `max_internal_retries=9`로 호출된다.
  - retry 시 `Focus Mode`가 활성화되어 컨텍스트를 축소하되 `constraint_block`과 preflight injection은 보존한다.
  - Flow Guard / Duplicate Guard / Consensus / DraftValidator / ContinuityInspector의 의미적 실패는 주로 Python advisory로 변환되어 Director에 전달된다.
  - malformed 데이터나 필수 구조 붕괴는 Director 전 `retry`로 되돌린다.
  - final commit 직전에는 `ctx.validate_arc_data_fields()` repair hook가 있으면 Arc 구조를 한 번 더 복구 시도한다.
  - Director PASS 후 저장 실패 시 DB rollback + `all_refined_arcs.pop()` + StateTracker 롤백을 수행한다.
- PASS_WITH_FIX behavior:
  - Director가 `PASS_WITH_FIX`를 반환하면 최대 3회까지 in-place patch + 재심사를 수행한다.
  - `fix_scope`가 `partial`/`full`이면 inplace를 포기하고 retry 경로로 위임한다.
  - `PASS_WITH_FIX`는 Director 주권 존중을 위해 최초 진입 시 QualityGate를 바로 적용하지 않는다.
- QualityGate behavior:
  - `PASS`이고 `tactical_doc >= 1500자`인데 `score < scoring.quality_gate_score`면 REJECT로 전환한다.
  - 현재 `validation.yaml` 기준 `quality_gate_score = 90`
- Fallback behavior:
  - Stage 1 스킵 시 `default_vol_strategy = {"vol_no": vol_no, "strategy_doc": ""}`
  - Smart retrieval advisor 실패 시 legacy vector retrieval로 폴백
  - Patch 실패 시 full rewrite로 폴백

## Manual Intervention Points
- User prompts:
  - 시작 시 target arc limit 입력
  - 최종 실패 시
    - `1`: 건너뛰고 계속
    - `2`: 중단
    - `3`: 다시 하기
    - `4`: 수동 개입
  - 수동 개입 후
    - `[Enter]`: 재시도
    - `skip`: 건너뛰기
    - `quit`: 중단
- Approvals:
  - 최종 PASS는 Director 심사와 후행 QualityGate를 통과해야 확정된다.
- Operator checks:
  - `logs/arc_{n}_failure_report.txt`
  - 배치별 농축/용접/설계 로그
  - `plans/arcs/arc_XXX.txt` export

## Metrics
- Throughput:
  - `pass_rate_monitor.record_attempt(stage=2, ...)`
  - 배치별 완료 Arc 수
- Error rate:
  - `quality_dashboard.record_validation(stage=2, ...)`
  - `stage_rejection_history`
  - `stage_attempts`
- Latency / cost:
  - `perf_timer`
  - `save_cost_record(scope_type="arc")`
  - Director/Preflight/Generation 구간 타이머

## Tests
- Unit:
  - `tests/test_stage2_preflight.py`
  - `tests/test_stage2_preflight_helpers.py`
  - `tests/test_stage2_validation_pipeline.py`
  - `tests/test_stage2_finalizer.py`
  - `tests/test_stage2_context.py`
  - `tests/test_four_phase_arc_generator.py`
  - `tests/test_arc_patch_mode.py`
  - `tests/test_arc_draft_validator.py`
- Integration:
  - `tests/test_stage2_pipeline.py`
  - `tests/test_stage2_patch_integration.py`
  - `tests/test_director_continuity_sc5.py`
  - `tests/test_sc6_observability.py`
- Regression:
  - `tests/test_stage2_optimizer.py`
  - `tests/test_stage234_fixes.py`
  - `tests/e2e/test_l3_stage2_realproject.py`

## Open Risks
- Risk 1:
  - `Stage2Context`에는 dedicated `world_state` slot이 없는데, 오케스트레이터는 `getattr(ctx, "world_state", None)`로 bind를 시도한다. 현재는 조용히 `None`으로 흐르지만 DI truth는 완전히 잠기지 않았다.
- Risk 2:
  - 최종 실패 후 `input()` 기반 수동 분기가 있어 비대화형 실행이나 자동 운영에서 중단 지점이 된다.
- Risk 3:
  - ArcAutoCorrector, equipment / inventory 동기화 같은 Python 구조 정규화는 여전히 Director 주권 경계선에 있다. 범위가 커지면 principle drift로 다시 번질 수 있다.
- Risk 4:
  - `npc_deaths`, `skill_acquisitions`, `timeline` 계열 response schema 불일치가 남아 있어 structured extraction 대신 fallback / advisory noise가 발생할 수 있다.
- Risk 5:
  - `validate_arc_data_fields` repair hook는 live seam이지만, mock-heavy context tests만으로는 real bound-method drift를 놓칠 수 있다.
- Risk 6:
  - `volume_summary_{n}` / `series_summary`는 `arc_summary_{i}` 앵커와 Director 요약 호출에 의존한다. 요약 앵커가 비어 있으면 계층 요약이 약해진다.
- Risk 7:
  - `PASS_WITH_FIX` 소진 후에도 마지막 상태가 `PASS_WITH_FIX`이면 patched arc를 채택하는 경로가 있다. Director 주권 보존 의도는 명확하지만 운영 해석이 까다롭다.

## Last Verified
- Date: 2026-03-13
- Commit: `e18f9910`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
