# Stage 1 Map

## Scope
- Define what Stage 1 is responsible for.
  - `MasterBible.plot_roadmap`를 읽어 `VolumeSettings.ARCS_PER_VOLUME` 단위로 아크를 묶고, 권별 `strategy_doc`를 순차 생성한다.
  - 각 권 결과를 `strategy_doc >= 2000자`와 미래 권 누수 검증으로 판정한다.
  - 모든 권이 통과했을 때만 DB `volumes` 앵커와 `current_project.volumes`를 갱신한다.
  - 직전 권 요약을 `context_accumulator`로 다음 권 프롬프트에 전달해 연속성을 유지한다.
- Out of scope:
  - 개별 Arc 전술 설계(Stage 2 책임).
  - Blueprint 생성(Stage 3 책임).
  - 원고 생성(Stage 4 책임).
  - 실패 권의 부분 저장 또는 수동 병합.
  - Stage 1 자체가 품질 게이트의 최종 권위가 되는 것. 현재 구현은 보조 검증 + 재시도 수준이다.

## Why
- 왜 권 단위 설계를 두는가? Stage 2가 개별 Arc를 설계할 때 상위 전략 문맥이 필요하기 때문이다.
- 왜 순차 설계인가? 앞선 권의 요약을 다음 권에 전달해야 중반 이후 권 전략의 일관성이 유지되기 때문이다.
- 왜 Stage 1이 선택 사항인가? Stage 2는 `volumes`가 비어 있어도 빈 `strategy_doc` 기본값으로 계속 진행하도록 설계돼 있기 때문이다.
- 왜 미래 권 누수를 막는가? 현재 권 전략이 후속 권 내용을 과도하게 확정하면 Stage 2 이후의 자유도가 급격히 줄어들기 때문이다.

## Entry Points
- Primary:
  - `main_a.py` 메인 메뉴 `choice == "1"` → `SovereignApp._stage_1_volumes()` → `Stage01Helpers.stage_1_volumes()`
- Secondary:
  - `Analyst.plan_single_volume_v20()`
  - `SovereignApp._validate_volume_boundaries()`
  - `UIService.show_volume_table()` (`_show_volume_table()` 경유)

## Inputs
- Required:
  - `current_project.master_bible`
  - `master_bible["MasterBible"]["plot_roadmap"]`
  - `app.agents["analyst"]`
- Optional:
  - `ProjectData.MetaInfo` (`meta_info` JSON 문자열로 전달)
  - `AssetLibrary`
  - `protagonist_config`
  - `app._get_protagonist_name()`가 추출한 주인공 이름
  - 기존 `current_project.volumes`
    - Stage 1 자체는 이를 입력으로 읽지 않으며, Stage 2가 비어 있는 경우 기본 전략으로 폴백한다.

## Outputs
- Files:
  - 전용 파일 출력 없음. Stage 1은 DB 앵커 + UI 로그 중심이다.
- DB updates:
  - `save_v20_anchor("volumes", final_volumes)`
  - `audit_event`
    - `analyst_error`
    - `volume_boundary_violation`
    - `recovery_failed`
- In-memory state:
  - `current_project.volumes = final_volumes`

## Dependencies
- Internal modules:
  - `modules/core/stage01_helpers.py`
  - `modules/domain/agents/analyst.py`
  - `modules/domain/agents/analyst_prompt_api.py`
  - `modules/core/adaptive_retry.py`
  - `modules/core/constants.py`
    - `VolumeSettings.ARCS_PER_VOLUME`
    - `RetryLimits.DIRECTOR_MAX_ATTEMPTS`
  - `modules/core/spinners.py` (`StageSpinner`)
  - `modules/core/services/ui_service.py`
  - `main_a.py`
    - `_validate_volume_boundaries`
    - `_get_protagonist_name`
    - `_safe_commit`
    - `_show_volume_table`
    - `_audit_event`
- External services/models:
  - `Analyst.ask()` 기반 Gemini 계열 호출
  - 현재 권 설계 프롬프트는 `temperature=0.7`, `thinking_level="low"`로 호출된다.

## State and Cache
- Persistent state:
  - `anchors["volumes"]`
  - Stage 2는 `current_project.volumes`가 비어 있으면 DB `volumes` 앵커를 로드하고, 그래도 없으면 빈 전략으로 진행한다.
- Runtime cache:
  - `context_accumulator`
    - 이전 권 `strategy_doc` 앞 500자를 누적한다.
    - 최근 3권만 전문을 유지하고, 더 오래된 권은 `"(요약 생략)"` 표시로 압축한다.
  - `meta_info`
    - `ProjectData.MetaInfo`를 JSON 문자열로 직렬화한 프롬프트 보조 컨텍스트다.
- Invalidation rules:
  - Stage 1이 완주하면 `save_v20_anchor("volumes", ...)`로 기존 권 전략을 전량 교체한다.
  - 중간 권에서 실패하면 이번 실행에서 통과한 앞선 권도 저장하지 않는다.
  - Stage 0 Bible이 바뀌어도 Stage 1 결과는 자동 무효화되지 않는다. 운영자가 재실행해야 한다.

## Failure and Recovery
- Common failure patterns:
  - 프로젝트 미로드 또는 `master_bible` 부재.
  - `plot_roadmap` 부재.
  - Analyst 응답이 `dict`가 아니거나 `strategy_doc`가 지나치게 짧음.
  - `_validate_volume_boundaries()`가 `REJECT`.
  - 특정 권이 최대 재시도 안에 통과하지 못함.
- Recovery flow:
  - `plot_roadmap`가 메모리에 없으면 `current_project._load_from_db()`를 1회 시도한다.
  - 각 권 설계는 `retry_with_feedback()`로 감싼다.
  - 최대 시도 횟수는 `RetryLimits.DIRECTOR_MAX_ATTEMPTS = 10`이다.
  - `_vol_on_failure()`는 현재 빈 문자열을 반환하므로, 재시도는 구조적으로 존재하지만 실제 피드백 주입은 비활성에 가깝다.
  - `Analyst.plan_single_volume_v20()`는 일부 필드를 자동 보정한다.
    - `tactical_doc`만 있으면 `strategy_doc`로 승격
    - `cider_score` 누락 시 `0`
    - `vol_no` 누락 시 호출 인자 값 사용
- Boundary gate behavior:
  - 미래 권 번호 직접 언급(`제 N권`, `N > 현재 권`)은 `REJECT`.
  - 미래 지향 표현(`이후`, `다음 권`, `훗날`, `나중에`, `앞으로`)이 4회 이상이면 `WARNING`.
  - Stage 1 성공 판정은 `status == "REJECT"`만 차단하므로 `WARNING`은 통과한다.
- Fallback behavior:
  - Stage 1을 스킵하면 Stage 2는 `default_vol_strategy = {"vol_no": vol_no, "strategy_doc": ""}`로 진행한다.
  - 특정 권이 끝내 통과하지 못하면 즉시 종료하고 부분 저장 없이 반환한다.

## Manual Intervention Points
- User prompts:
  - 시작 시 `"[1] 진행  [2] 스킵"` 선택.
  - 스킵 후 또는 종료 후 `[Enter]` 입력.
- Approvals:
  - 별도 승인 UI는 없다.
  - 분량 게이트와 권 경계 검증이 자동 판정 역할을 한다.
- Operator checks:
  - `총 N개 아크 → M권` 로그 확인.
  - 권별 `검수 완료 (분량: X자)` 로그 확인.
  - 완료 후 `_show_volume_table(final_volumes)` 출력 확인.

## Metrics
- Throughput:
  - 총 아크 수 대비 생성 권 수.
  - 권별 통과 로그.
  - 최종 저장 권 수.
- Error rate:
  - 전용 대시보드는 없다.
  - `retry_with_feedback()` 로그와 `audit_event`로 확인한다.
- Latency:
  - 권마다 `StageSpinner(1, f"제{vol_idx}권 설계")`가 돈다.
  - 권별 LLM 호출은 최소 1회이며, 실패 시 최대 10회까지 반복될 수 있다.

## Tests
- Unit:
  - `tests/test_stage01_helpers.py`
    - 스킵
    - 프로젝트 미로드
    - `plot_roadmap` 부재
    - 권 설계 성공 저장
    - 품질 미달 중단
  - `tests/test_stage2_pipeline.py`
    - `Analyst.plan_single_volume_v20()` 시그니처
    - 필수 키 반환
    - `tactical_doc` → `strategy_doc`
    - `cider_score` 자동 보정
  - `tests/test_stage01_fixes.py`
    - Stage01Helpers 입력 가드
    - `input()` EOF 처리
    - Stage 0/1 helper 구조 회귀
- Integration:
  - 전용 Stage 1 E2E 테스트는 없다.
  - Stage 2는 `volumes` 부재 시 빈 전략으로 진행하는 경로를 코드에서 보유한다.
- Regression:
  - `tests/test_stage01_helpers.py`
  - `tests/test_stage2_pipeline.py`
  - `tests/test_stage01_fixes.py`

## Open Risks
- Risk 1:
  - `_vol_on_failure()`가 빈 문자열만 반환하므로 `retry_with_feedback()`의 재시도 품질 개선 효과가 매우 약하다.
- Risk 2:
  - 특정 권 실패 시 전체 실행이 즉시 종료되고 부분 저장이 없다.
- Risk 3:
  - Stage 1은 Analyst 작업인데 `RetryLimits.DIRECTOR_MAX_ATTEMPTS`에 결합돼 있어 정책 분리도가 낮다.
- Risk 4:
  - `_validate_volume_boundaries()`가 `main_a.py`에 남아 있어 Stage01Helpers 단독 재사용성과 테스트 분리가 약하다.
- Risk 5:
  - 전용 Stage 1 E2E가 없어 실제 장편 입력에서 권 경계 검증과 연속성 누적이 어떻게 작동하는지 자동으로 보장하지 못한다.

## Last Verified
- Date: 2026-03-10
- Commit: `d2d935b`
- Code Sync (Yes/No): Yes
- Verified By: Codex
