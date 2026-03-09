# Stage 1 Map

## Scope
- Define what Stage 1 is responsible for.
  - Bible의 `plot_roadmap` (Arc 블록 목록)을 5개씩 묶어 권(Volume) 단위 고해상도 전략 문서를 순차 생성.
  - 각 권의 `strategy_doc`을 Analyst LLM이 생성하고, 분량 검증(2,000자 이상) + 미래 권 정보 누수 차단 검증을 통과해야 합격.
  - 합격된 권 전략을 DB `volumes` 앵커에 저장하고 `current_project.volumes`에 동기화.
- Out of scope:
  - Arc 전술 설계(Stage 2 책임).
  - 에피소드 Blueprint 생성(Stage 3 책임).
  - 원고 생성(Stage 4 책임).
  - Stage 1은 **선택 사항**이며, 스킵해도 Stage 2 진행이 가능하다.

## Why
- 왜 권(Volume) 단위인가? Arc 5개를 하나의 권으로 묶어 장기 연재의 거시 서사 방향을 LLM이 파악하게 하기 위해서다. 개별 Arc 설계(Stage 2) 전에 큰 그림을 잡는 단계.
- 왜 순차 생성인가? 이전 권 요약(`context_accumulator`)을 다음 권 설계에 주입하여 권 간 서사 연속성을 유지하기 위해서다.
- 왜 선택 사항인가? Volume 전략 없이도 Stage 2가 `plot_roadmap`에서 직접 Arc를 설계할 수 있으므로, 빠른 프로토타이핑 시 스킵 가능하다.
- 왜 미래 권 누수를 차단하는가? 순차 설계 원칙상 N권 설계 시점에 N+1권 이후 내용을 언급하면 서사 자유도가 훼손되기 때문이다.

## Entry Points
- Primary:
  - `SovereignApp._stage_1_volumes()` (`main_a.py` L2486) -- thin delegate
    - `Stage01Helpers.stage_1_volumes()` (`modules/core/stage01_helpers.py` L499-691)
- Secondary:
  - `Analyst.plan_single_volume_v20()` (`modules/domain/agents/analyst.py` L124-222) -- 단일 권 LLM 호출
  - `SovereignApp._validate_volume_boundaries()` (`main_a.py` L2606-2637) -- 미래 권 누수 검증
  - 메인 메뉴 choice `"1"` (`main_a.py` L2148-2149) 또는 One-Stop 파이프라인에서는 Stage 1을 호출하지 않음(Stage 2부터 시작).

## Inputs
- Required:
  - `current_project.master_bible` -- Bible 데이터. 없으면 즉시 종료.
  - `master_bible["MasterBible"]["plot_roadmap"]` -- Arc 블록 리스트. 없으면 DB 재로드 시도 후에도 없으면 종료.
- Optional:
  - `master_bible["MasterBible"]["ProjectData"]["MetaInfo"]` -- 프로젝트 메타 정보 (JSON 직렬화 후 LLM에 전달).
  - `master_bible["MasterBible"]["AssetLibrary"]` -- 자산 라이브러리 (LLM 프롬프트에 주입).
  - `master_bible["MasterBible"]["protagonist_config"]` -- 주인공 설정 (`world_origin`, `incarnation_type`).
  - `app.agents["analyst"]` -- Analyst 에이전트 (LLM 호출 주체).
  - `app.selected_genre` -- 현재 장르 (장르별 Guard 프롬프트 + role_title 결정에 사용).

## Outputs
- Files:
  - 없음. Stage 1은 파일 출력 없이 DB에만 저장한다.
- DB updates:
  - `anchors` 테이블: `save_v20_anchor("volumes", final_volumes)` -- 전체 권 전략 리스트 저장.
  - `audit_event`: `analyst_error`(유효하지 않은 결과), `volume_boundary_violation`(미래 권 누수), `recovery_failed`(DB 재로드 실패) 이벤트 기록.
- In-memory state:
  - `current_project.volumes` -- 생성된 권 전략 리스트로 동기화.

## Dependencies
- Internal modules:
  - `modules/core/stage01_helpers.py` -- Stage01Helpers 클래스 (로직 캡슐화)
  - `modules/domain/agents/analyst.py` -- `Analyst.plan_single_volume_v20()` (LLM 호출)
  - `modules/domain/agents/analyst_prompt_api.py` -- `get_plan_volume_prompt_v25()` (프롬프트 로더)
  - `modules/core/constants.py` -- `VolumeSettings.ARCS_PER_VOLUME=5`, `RetryLimits.DIRECTOR_MAX_ATTEMPTS=10`
  - `modules/core/adaptive_retry.py` -- `retry_with_feedback()` (재시도 래퍼)
  - `modules/core/spinners.py` -- `StageSpinner(1, ...)` (UI 스피너)
  - `modules/core/project_manager.py` -- `save_v20_anchor()`, `_load_from_db()` (DB 저장/복구)
  - `modules/core/genre_schema_builder.py` -- `get_genre_role_title()` (장르별 역할 칭호)
  - `main_a.py` -- `_validate_volume_boundaries()`, `_get_protagonist_name()`, `_safe_commit()`, `_show_volume_table()`, `_audit_event()`
- External services/models:
  - BaseAgent `ask()` 기반 Gemini 호출 (Analyst, `temperature=0.7`, `thinking_level="low"`).

## State and Cache
- Persistent state:
  - `anchors` 테이블의 `"volumes"` 키 -- 완성된 권 전략 JSON 리스트.
  - `StudioSystem.check_v20_readiness()` -- `db.load_anchor("volumes")` truthy 여부로 Stage 1 완료 상태 판정.
- Runtime cache:
  - `context_accumulator` -- 이전 권 요약 누적 문자열 (함수 로컬 변수, 권 순회 중에만 유지).
  - 최근 3권(`MAX_CONTEXT_VOLUMES=3`) 요약만 전문 유지, 이전 권은 `"(요약 생략)"` 으로 압축.
- Invalidation rules:
  - Stage 1을 다시 실행하면 `save_v20_anchor("volumes", ...)` 호출로 기존 데이터를 전량 덮어쓴다.
  - Stage 0 Bible 변경 시 Stage 1 재실행이 필요하나, 자동 무효화 메커니즘은 없다.

## Failure and Recovery
- Common failure patterns:
  - `plot_roadmap` 비어 있음 -- 메모리/DB 모두 없을 때 즉시 종료. "Phase 0을 다시 실행하세요" 안내.
  - Analyst LLM 응답이 `dict`가 아니거나 `None` -- `_vol_on_success`에서 `False` 반환, 재시도.
  - `strategy_doc` 분량 부족 (2,000자 미만) -- `_vol_on_success`에서 `False` 반환, 재시도.
  - 미래 권 정보 누수 (`_validate_volume_boundaries` REJECT) -- `_vol_on_success`에서 `False` 반환, 재시도.
  - JSON 파싱 실패 -- `_extract_json_robust()` 내부 폴백 처리.
- Recovery flow:
  - `retry_with_feedback()` 래퍼가 최대 `DIRECTOR_MAX_ATTEMPTS=10`회 재시도.
  - 실패 시 `_vol_on_failure`가 빈 문자열 피드백 반환 (현재 피드백 미활용).
  - `plot_roadmap` 메모리 부재 시 `current_project._load_from_db()` 1회 DB 재로드 시도.
- Fallback behavior:
  - 10회 시도 후에도 특정 권이 합격하지 못하면 `"품질 미달로 공정 중단"` 로그 후 함수 종료 (`return`). 이미 합격한 권들도 DB에 저장되지 않는다 (전량 실패 처리).
  - LLM 응답에 `tactical_doc` 키가 있고 `strategy_doc`이 없으면 자동 키 변환 (`Analyst.plan_single_volume_v20` L208).
  - `cider_score`, `vol_no` 누락 시 기본값 자동 보정 (L213-219).

## Manual Intervention Points
- User prompts:
  - Stage 1 진입 시 `[1] 진행 / [2] 스킵` 선택 (`stage01_helpers.py` L508). 기본값 `"1"` (진행).
  - Stage 2 진입 시 Stage 1 미완료면 `"Stage 1을 건너뛰고 진행하시겠습니까? (y/N)"` 확인 (`main_a.py` L2154).
- Approvals:
  - 코드상 별도 승인 단계 없음. 분량/경계 검증이 자동 게이트 역할.
- Operator checks:
  - 메인 메뉴에서 `Stage 1: Volume Strategy` 옆 상태 표시 (`⏭️ 스킵가능` / 완료 시 표시).
  - 완료 후 `_show_volume_table(final_volumes)` 호출로 권별 요약 테이블 콘솔 출력 (메서드 존재 시).

## Metrics
- Throughput:
  - 완료 시 `"{len(final_volumes)}권 대서사시 로드맵이 DB에 최종 안착"` 로그 출력.
  - 각 권 합격 시 `"제 N권 검수 완료 (분량: N자)"` 로그 출력.
- Error rate:
  - `retry_with_feedback()` 내부에서 시도 횟수 추적. 개별 로그로만 확인 가능, DB 집계 메트릭 없음.
  - `audit_event` 기록: `analyst_error`, `volume_boundary_violation`, `recovery_failed`.
- Latency:
  - `StageSpinner(1, f"제{vol_idx}권 설계")` UI 스피너로 진행 표시.
  - 권당 LLM 1회 호출 (`ask()` 타임아웃은 BaseAgent 기본값 적용).

## Tests
- Unit:
  - `tests/test_stage01_helpers.py` -- Stage01Helpers 생성자 및 phase_0 관련 테스트.
  - `tests/test_stage01_fixes.py` -- Analyst `_SafeDict`, `_extract_content_parts` 존재 검증.
- Integration:
  - 없음. Stage 1 전용 E2E/통합 테스트는 존재하지 않는다.
- Regression:
  - `tests/test_sweep23.py`, `tests/test_stage2_pipeline.py` -- Stage 1 관련 간접 참조만 포함.

## Open Risks
- Risk 1:
  - `_vol_on_failure`가 빈 문자열만 반환하므로 재시도 시 LLM에 실패 원인 피드백이 전달되지 않는다. `retry_with_feedback`의 피드백 메커니즘이 사실상 비활성 상태.
- Risk 2:
  - 특정 권 실패 시 `return`으로 함수가 즉시 종료되며, 이미 합격한 이전 권들도 `save_v20_anchor`에 도달하지 못해 DB에 저장되지 않는다. 부분 저장(partial save) 메커니즘이 없다.
- Risk 3:
  - Stage 1 전용 E2E/통합 테스트가 없어 `stage_1_volumes()` 전체 흐름의 회귀 검증이 불가하다.
- Risk 4:
  - `_validate_volume_boundaries`가 `main_a.py`(SovereignApp)에 위치하여 Stage01Helpers에서 `app._validate_volume_boundaries()` 호출로 접근한다. Stage01Helpers 단독 테스트 시 이 검증을 mock해야 하는 결합도가 존재한다.

## Last Verified
- Date: 2026-03-10
- Commit: `3a00c12`
- Code Sync (Yes/No): Yes
- Verified By: Codex
