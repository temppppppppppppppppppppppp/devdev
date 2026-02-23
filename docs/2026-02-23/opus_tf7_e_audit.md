# TF-7-E 감사 보고서 — World State / Fact Ledger / State Delta

## 감사 파일 목록
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/state_delta_tracker.py`
- `modules/core/services/project_service.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/project_manager.py`
- `modules/core/db_manager.py`
- `modules/core/constraint_db.py`
- `modules/core/reference_anchor.py`
- `main_a.py`

## 발견 이슈 (총 1건)

### [TF-7-E-1] Rollback 후 WorldState/FactLedger 메모리 객체가 stale 상태로 재사용될 수 있음 (HIGH)
**증거 파일/라인**
- `modules/core/services/project_service.py:220`
- `modules/core/services/project_service.py:221`
- `main_a.py:289`
- `main_a.py:2784`
- `main_a.py:3028`
- `main_a.py:3043`
- `modules/core/stage4_context_builder.py:582`
- `modules/core/stage4_context_builder.py:614`
- `modules/core/world_state.py:433`
- `modules/core/fact_ledger.py:558`
- `modules/core/project_manager.py:902`
- `modules/core/project_manager.py:906`

**수동 근거**
- ProjectService 롤백 경로는 DB 삭제 후 `project._load_from_db()`와 invalidator만 호출한다.
- invalidator는 `state_tracker`만 `None`으로 만든다.
- 성공 후에도 `world_state`/`fact_ledger`는 명시적으로 무효화하지 않는다.
- Stage4 진입 시 `world_state`/`fact_ledger`는 `None`일 때만 lazy init된다.
- Stage4 mandatory context는 현재 메모리의 world/fact 요약을 그대로 주입한다.
- 반면 동일 코드베이스의 backtrack 경로에는 `world_state.rollback_to()`/`fact_ledger.rollback_to()` 호출이 존재한다.

**Caller-callee 계약 추적**
- Caller: `ProjectService.rollback_episode()` (`modules/core/services/project_service.py:220`)
- Callee(현재): `project._load_from_db()`, `state_tracker_invalidator` (`modules/core/services/project_service.py:220`, `modules/core/services/project_service.py:221`)
- 누락된 기대 callee: `WorldStateManager.rollback_to()`, `FactLedger.rollback_to()` (`modules/core/world_state.py:433`, `modules/core/fact_ledger.py:558`)

**Bug-vs-intent 판단**
- 월드/팩트 롤백 API 자체는 구현돼 있고(`world_state.py`, `fact_ledger.py`), 별도 backtrack 경로에서는 실제 호출한다(`project_manager.py:902`, `project_manager.py:906`).
- 따라서 ProjectService 롤백 경로의 누락은 설계 의도보다 연결 누락(배선 불일치)로 판단했다.

## Risk (추가 확인 필요)

### [TF-7-E-R1] StateDeltaTracker에 rollback/reset 계약이 없어 롤백 이후 history 정합성 위험이 남음 (MEDIUM, Risk)
**증거 파일/라인**
- `modules/core/state_delta_tracker.py:99`
- `modules/core/state_delta_tracker.py:100`
- `main_a.py:306`
- `main_a.py:2784`

**수동 근거**
- `StateDeltaTracker`는 `energy_history`/`injury_history`를 누적하지만, 파일 전역에 rollback/reset 메서드가 없다(전체 수동 열람).
- 롤백 성공 경로에서 `state_tracker`만 무효화되고 `state_delta_tracker`는 별도 초기화 경로가 확인되지 않았다.

**Risk 판단 근거**
- 즉시 크래시 경로는 확인되지 않았지만, 롤백 후 상태 추적 history 오염 가능성이 있어 Risk로 분류.

## [FP] 오탐 목록

### [FP-1] WorldState/FactLedger는 롤백 API가 없다
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/world_state.py:433` (`rollback_to`)
  - `modules/core/fact_ledger.py:558` (`rollback_to`)

### [FP-2] ReferenceAnchor는 미래 앵커를 필터링하지 않는다
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/reference_anchor.py:230`
  - `modules/core/reference_anchor.py:231`

## TF-6-A 패치 파급 확인

| 점검 항목 | 결과 | 근거 |
|---|---|---|
| Episode Bible rollback delete 경로 유지 | 확인됨 | `modules/core/services/project_service.py:181`, `modules/core/db_manager.py:962` |
| 롤백 후 DB 재로드 + tracker invalidation 수행 | 확인됨 | `modules/core/services/project_service.py:220`, `modules/core/services/project_service.py:221` |
| WorldState/FactLedger 동기 롤백까지 포함 | 미확인(누락) | `modules/core/services/project_service.py:160`~`modules/core/services/project_service.py:234` |

## 요약 테이블
| 분류 | 건수 | 항목 |
|---|---:|---|
| HIGH | 1 | `TF-7-E-1` |
| Risk | 1 | `TF-7-E-R1` |
| FP | 2 | `FP-1`, `FP-2` |

