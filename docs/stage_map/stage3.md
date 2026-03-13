# Stage 3 Map

## Scope
- Define what Stage 3 is responsible for.
  - Arc를 에피소드 단위 Blueprint로 변환하고, 검증 후 저장한다.
  - 시작점은 기존 Blueprint와 기존 원고를 함께 본 `production_head + 1`이다.
  - 각 화는 `ThreePhaseBlueprintGenerator`로 생성하고, PASS 계열 결과만 `blueprints` 테이블과 txt export에 저장한다.
  - Stage 3는 `StateTracker`, `WorldState`, `FactLedger`를 lazy init하고, Blueprint에 `_stage3_meta`와 선택적 `_inventory_gaps`를 부착한다.
  - 순차 의존성을 강하게 유지한다. 현재 화가 실패하면 후속 화는 생성하지 않는다.
- Out of scope:
  - Arc 생성/수정(Stage 2 책임).
  - 최종 원고 생성(Stage 4 책임).
  - Stage 3 자체가 장기 저장소를 새로 설계하는 것. 현재 구현은 기존 DB 상태를 읽어 Blueprint 생성에 반영한다.

## Why
- 왜 Stage 3를 분리하는가? Arc 전략을 실제 화 단위 장면 구조로 바꾸는 첫 번째 단계이기 때문이다.
- 왜 기존 원고와 기존 Blueprint를 같이 보나? 이미 생산된 화와 설계된 화 사이의 간극을 줄이기 위해서다.
- 왜 ThreePhase인가? 제약 수집, 다중 후보 생성, Director 판정을 묶어 Blueprint 품질과 일관성을 동시에 관리하기 위해서다.
- 왜 실패 시 바로 멈추는가? 다음 화 Blueprint는 현재 화 Blueprint를 전제로 연속성 검증을 수행하기 때문이다.

## Entry Points
- Primary:
  - `Stage3Orchestrator.stage_3_batch_blueprinting(target_ep=None)`
- Secondary:
  - `Stage3Orchestrator._process_single_episode()`
  - `Stage3Orchestrator._generate_blueprint()`
  - `ThreePhaseBlueprintGenerator.generate()`
  - `UnifiedBlueprintValidator.validate()`
- Notes:
  - Stage 3는 `current_project.arcs`가 비어 있으면 즉시 종료한다.
  - `target_ep`를 외부에서 넘기지 않으면 사용자 입력으로 종료 화를 받는다.

## Inputs
- Required:
  - `current_project.arcs`
  - `current_project.db`
  - `agents["three_phase_bp"]`
  - `agents["director"]`
- Optional:
  - 최근 Blueprint 30개
  - 최근 원고 30개
  - `state_extractor`
  - `context_advisor`
  - `vec_memory` 또는 `memory`
  - `state_tracker`
  - `world_state`
  - `fact_ledger`
  - `sys.hud.pro_root` (`prev_hud`)
  - `adversarial_self_play`
  - `selected_genre`
  - `protagonist_config`

## Outputs
- Files:
  - `plans/blueprints/blueprint_XXXX.txt`
    - human-readable export
- DB updates:
  - `blueprints` 테이블
  - `stage_attempts` (PASS/REJECT)
  - `cost_record`
    - 현재 구현은 REJECT 이벤트 기록 위주
  - `quality_dashboard` 기록
  - `audit_event`
- In-memory state:
  - `prev_blueprints` 최근 30개
  - Arc 단위 Entity Registry 캐시
  - Blueprint별 `_stage3_meta`
  - 선택적 `_inventory_gaps`

## Dependencies
- Internal modules:
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage3_context.py`
  - `modules/domain/agents/three_phase_blueprint_generator.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/blueprint_ensemble.py`
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/models/blueprint.py`
  - `modules/core/project_manager.py`
  - `modules/core/db_manager.py`
- External services/models:
  - Director
    - `compare_and_select_blueprint()`
    - `audit_manuscript()`
  - ThreePhase ensemble/validator LLM 호출
  - optional VecMemory / ContextAdvisor / Slack notifier

## State and Cache
- Persistent state:
  - Stage 3 SSOT는 `blueprints` 테이블이다.
  - `plans/blueprints/*.txt`는 export 전용이다.
- Runtime cache:
  - `prev_blueprints[-30:]`
  - `_entity_cache_arc_idx`
  - `_cached_entity_registry`
  - `ThreePhaseBlueprintGenerator`의 `cached_constraint_block`
- Invalidation rules:
  - Arc 인덱스가 바뀌면 Entity Registry 캐시를 다시 만든다.
  - `prev_blueprints`는 30개를 넘기면 앞부분을 버린다.
  - ThreePhase retry는 `_initial_feedback` 기준으로 재조립하며, 피드백을 무한 누적하지 않는다.

## Failure and Recovery
- Common failure patterns:
  - `current_project.arcs` 부재
  - 직전 화 Blueprint 부재
  - 현재 화 Arc 컨텍스트 미검출
  - `ep_start` 누락
  - Ensemble 후보 전부 실패
  - Director REJECT / QualityGate 미달
  - Blueprint 무결성 실패
  - DB 커밋 실패
- Recovery flow:
  - Stage 3는 시작 전에 `StateTracker`, `WorldState`, `FactLedger`를 lazy init한다.
    - 초기화 실패는 비차단이다.
  - 각 화는 `three_phase_bp.generate(..., max_retries=9)`로 생성한다.
    - 총 10회 시도
  - ThreePhase 내부에서 constraint block은 첫 시도 후 캐시 재사용한다.
  - retry마다 이전 REJECT 피드백, 점수, fix_scope, 전략 정보를 다시 주입한다.
  - 성공 후 저장 또는 실패 후 중단만 있으며, 실패 화를 건너뛰고 다음 화로 넘어가지 않는다.
- ThreePhase generation behavior:
  - 기본 경로는 Ensemble 3후보 생성이다.
  - 후보 최소 기준은 `scene_count >= 4`와 `integrated_scenario >= 500자`다.
  - 이후 `UnifiedBlueprintValidator`는 필수 필드, `integrated_scenario >= 800자`, 씬 수 3개 이상 등을 advisory로 검사한다.
  - 후보가 여러 개면 Director가 `compare_and_select_blueprint()`로 비교 선택한다.
  - 후보가 1개면 Director `audit_manuscript()` 경로로 최종 판정한다.
  - Director가 없으면 `REJECT`다. PASS 폴백이 아니다.
- Patch mode behavior:
  - `score >= patch_mode.inplace_below(60)` 또는 `fix_scope=="inplace"`면 in-place patch를 시도한다.
  - `fix_scope=="partial"`이면 거절된 전략 1개만 재생성한다.
  - `score < patch_mode.rewrite_below(50)`이면 `_previous_best`를 버리고 전면 재생성한다.
- QualityGate behavior:
  - `verdict == PASS`인데 `score < scoring.quality_gate_score(90)`면 REJECT로 전환한다.
  - `PASS_WITH_FIX`는 최초 진입 시 QualityGate를 바로 적용하지 않는다.
  - patch 재심사에서 `PASS`가 나와도 다시 90점 미만이면 종료한다.
- PASS_WITH_FIX / PASS_WITH_WARNING:
  - `PASS_WITH_FIX`는 최대 3회 in-place patch + 재심사를 수행한다.
  - 소진 후 마지막 판정이 `PASS_WITH_FIX` 또는 `PASS_WITH_WARNING`이면 패치본을 채택할 수 있다.
  - 모든 재시도 실패 후에도 마지막 점수가 `rewrite_below(50)` 이상이면 긴급 폴백 `PASS_WITH_WARNING`을 허용한다.
  - 이 경우 `quality_gate_failed=True`, `quality_risk=True`가 붙는다.

## Manual Intervention Points
- User prompts:
  - `몇 화까지 설계도를 생성하시겠습니까?`
- Approvals:
  - 별도 승인 UI는 없고 Director 판정이 자동 게이트다.
- Operator checks:
  - 시작 전 `Blueprint n화 / 원고 n화까지 발견` 로그
  - 실패 시 `blueprint_fail`, `continuity_block`, `db_commit_error` 이벤트
  - 저장 후 `blueprint_XXXX.txt` export

## Context Build
- Stage 3는 Blueprint 생성 전에 아래 컨텍스트를 합성한다.
  - Smart Context Retrieval
    - `smart_retrieval.stage3_enabled`
    - Stage 3 전용 `vector_max_results` 키는 없고 `context.vector_max_results_s4`를 공유한다.
  - 원본 Treatment Block 직접 주입
  - `world_state.get_summary()` 기반 advisory 블록 (available할 때만)
  - Arc 시간 마커/타임라인 경고
  - 장기 미회수 복선 advisory (`DB-4`)
  - 최근 원고 30화 전문
  - 직전 HUD (`prev_hud`)
- prev manuscript 총량은 `ContextLimits.MAX_CONTEXT_CHARS` 상한으로 절삭한다.

## Metrics
- Throughput:
  - `success_count` / `fail_count`
  - `ThreePhaseBlueprintGenerator.get_stats().pass_rate`
- Error rate:
  - `stage_attempts`
  - `audit_event`
  - `quality_dashboard.record_validation(stage=3, ...)`
- Latency:
  - Blueprint ensemble timeout
    - 전체 `300s`
    - 후보별 `240s`
  - StageSpinner 로그

## Tests
- Unit:
  - `tests/test_stage3_orchestrator.py`
  - `tests/test_blueprint_patch_mode.py`
  - `tests/chaos/test_stage3_metrics.py`
  - `tests/chaos/test_blueprint_none.py`
- Integration:
  - `tests/e2e/test_l3_stage3_smoke.py`
  - `tests/stage3_isolated_test/test_stage3_arc3.py`
  - `tests/stage3_isolated_test/test_stage3_arc3_v2.py`
  - `tests/stage3_isolated_test/test_stage3_production.py`
- Regression:
  - `tests/test_pass_with_fix.py`
  - `tests/test_pydantic_models.py`

## Downstream Contract
- 저장된 Blueprint에는 `_stage3_meta`가 들어갈 수 있다.
  - `final_verdict`
  - `quality_gate_failed`
  - `quality_risk`
  - `last_score`
- Stage 4는 이 메타를 advisory와 조기 escalation 신호로 사용할 수 있다.

## Open Risks
- Risk 1:
  - Stage 3는 `current_project.arcs`를 자동 복원하지 않는다. Arc가 메모리에 없으면 그냥 종료한다.
- Risk 2:
  - Stage 3 전용 retrieval result 수 키가 없어 `context.vector_max_results_s4`와 결합돼 있다.
- Risk 3:
  - `PASS_WITH_WARNING`은 품질 리스크를 남긴 채 저장될 수 있다. 운영자 해석과 후속 Stage 4 대응이 중요하다.
- Risk 4:
  - 실패 시 현재 화에서 즉시 중단하므로, 한 화의 문제로 긴 생성 배치 전체가 막힐 수 있다.
- Risk 5:
  - lazy init 실패는 비차단이라 `StateTracker`/`WorldState`/`FactLedger` 없이도 진행될 수 있다. 이 경우 연속성 감시 밀도가 떨어진다.
- Risk 6:
  - Treatment Block 직접 주입 경로는 live semantics에 중요하지만, 전용 regression이 얕아 prompt-level drift를 놓칠 수 있다.
- Risk 7:
  - `generate()` 예외 / `gen_err` 안전망 경로는 존재하지만 dedicated regression coverage가 충분히 두껍지 않다.

## Last Verified
- Date: 2026-03-13
- Commit: `e18f9910`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
