# TF Director Selections Stage Split Resolution

Date: 2026-03-11
Status: PASS
Confidence: 97%
Scope:
- `director_selections` Stage 2 / Stage 4 split
- safe-op cleanup precision
- legacy row compatibility

## Problem

기존 `director_selections`에는 `stage` 컬럼이 없었다.

그 결과:

- Stage 2 arc selection 이력과 Stage 4 episode selection 이력이 같은 테이블에 섞였다.
- `rollback_episode()` / `wipe_production_data()` / `reset_after()`는 `ep_num` 기준으로만 정리할 수 있었다.
- 따라서 원칙적으로는 보존되어야 할 Stage 2 selection 이력이 episode rollback/wipe에 같이 지워질 수 있었다.

## Resolution

### Schema

[db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py#L436)

- `director_selections.stage INTEGER` 추가
- 기존 DB 호환용 `ALTER TABLE` 마이그레이션 추가
- `idx_director_selections_stage_ep` 인덱스 추가

### Write Paths

[stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py#L1397)
- Stage 2 PASS/REJECT 저장 시 `stage=2`

[stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L1492)
- Stage 4 Director selection 저장 시 `stage=4`

[db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py#L2539)
- `save_director_selection(..., stage: int | None = None)`로 확장
- 기존 positional 호출 호환성 유지

### Safe-Ops Cleanup Split

[db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py#L2190)
- `reset_after(target_ep)`는 이제 Stage 4 / legacy Stage 4 selection만 삭제
- Stage 2 selection 이력은 episode rollback / wipe에서 보존

[project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py#L116)
- `reset_stage_2()`는 Stage 2 metadata 정리 시 Stage 2 selection 이력도 함께 삭제

[project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py#L116)
- `rewind_stage_2()`는 제거되는 arc range에 해당하는 Stage 2 selection 이력만 삭제

### Legacy Compatibility

legacy row는 `stage IS NULL`일 수 있다.

현재 호환 규칙:

- `selected_label == ''` 이면 legacy Stage 2로 간주
- `selected_label != ''` 이면 legacy Stage 4로 간주

즉 신규 데이터는 `stage`로 직접 분기하고, 과거 데이터는 `selected_label` 휴리스틱으로 안전하게 따라간다.

## 3-Pass Audit

### Pass 1: Correctness

확인 결과, split 방향은 코드에 일관되게 반영됐다.

- 저장 경로
  - Stage 2 -> `stage=2`
  - Stage 4 -> `stage=4`
- 삭제 경로
  - episode rollback / wipe -> Stage 4만 삭제
  - Stage 2 reset / rewind -> Stage 2만 삭제

판정:
- 정합성 PASS

### Pass 2: Safety

legacy 데이터에 대한 휴리스틱이 있기 때문에 기존 DB도 바로 깨지지 않는다.

- legacy Stage 2: `selected_label=''`
- legacy Stage 4: `selected_label!=''`

또 `save_director_selection()`는 `stage`를 끝단 keyword로 추가해서 기존 positional 테스트/호출과 충돌하지 않는다.

판정:
- 안전성 PASS

### Pass 3: Completeness

관련 코드/테스트/운영 문서가 같이 닫혔다.

- 코드
  - [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
  - [project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py)
  - [stage2_finalizer.py](C:/Users/User/Desktop/글도비/modules/core/stage2_finalizer.py)
  - [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- 테스트
  - [test_safe_ops_db_consistency.py](C:/Users/User/Desktop/글도비/tests/test_safe_ops_db_consistency.py)
  - [test_project_service.py](C:/Users/User/Desktop/글도비/tests/test_project_service.py)
  - [test_selection_tracker.py](C:/Users/User/Desktop/글도비/tests/test_selection_tracker.py)
  - [test_db_manager.py](C:/Users/User/Desktop/글도비/tests/test_db_manager.py)
- 운영 문서
  - [runbook.md](C:/Users/User/Desktop/글도비/docs/stage_map/runbook.md)

판정:
- 완전성 PASS

## Verification

- `python -m py_compile modules/core/db_manager.py modules/core/services/project_service.py modules/core/stage2_finalizer.py modules/core/stage4_interview_round.py`
- `python -m pytest tests/test_safe_ops_db_consistency.py tests/test_project_service.py tests/test_selection_tracker.py tests/test_db_manager.py -q`
  - `43 passed`
- `python -m ruff check ...`
  - PASS

## Final Verdict

기존 잔여 제한사항은 해소됐다.

`director_selections`는 이제:

- Stage 2 / Stage 4를 구분해 저장하고
- safe-op에서도 의도한 stage만 정리할 수 있다.

잔여 리스크는 `legacy null-stage row`에 대한 휴리스틱 정도이며, 현재 운영 범위에서는 비차단이다.
