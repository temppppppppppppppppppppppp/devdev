# TF-6-A: 롤백 원자성 (Rollback Atomicity)

## 감사 범위
- 파일: `modules/core/services/project_service.py`, `modules/core/vec_memory.py`, `main_a.py`, `modules/core/db_manager.py`
- 코드 줄 수: 약 400줄 수동 확인

## 발견 사항

### [TF-A-1] 커밋 실패 시 HUD 인메모리 상태가 선반영됨 (HIGH)
- **파일**: `modules/core/services/project_service.py:147`, `modules/core/services/project_service.py:152`, `modules/core/services/project_service.py:188`
- **현재 코드**:
```python
project.db.cursor.execute("UPDATE anchors SET data = ? WHERE key = 'bible'", (...,))
project.master_bible = bible_data
...
if not self._safe_commit():
    return False
```
- **문제**: DB 커밋 성공 전에 `project.master_bible`이 갱신되어, 커밋 실패 시 DB와 인메모리 HUD가 불일치 상태로 남는다.
- **영향**: 롤백 실패 직후 같은 프로세스에서 후속 Stage를 실행하면 HUD 기준 판단이 오염될 수 있다.
- **수정안**:
```python
new_bible_data = bible_data
...
if not self._safe_commit():
    return False
project.master_bible = new_bible_data
```
또는 실패 시 이전 `project.master_bible` 스냅샷 복원.
- **테스트**: `_safe_commit()`을 `False`로 목킹하고 `rollback_episode()` 호출 후, `project.master_bible`이 호출 전 값과 동일한지 검증.

### [TF-A-2] VecMemory 삭제 예외 경로에서 명시적 rollback 누락 (MEDIUM)
- **파일**: `modules/core/vec_memory.py:894`, `modules/core/vec_memory.py:896`
- **현재 코드**:
```python
self._conn.commit()
...
except Exception as e:
    self._ui_log(...)
    return 0
```
- **문제**: 예외 시 `self._conn.rollback()`이 없어 트랜잭션 종료 의도가 코드에 명시되지 않는다.
- **영향**: 커넥션 재사용/락 경합 상황에서 상태 해석이 불명확해지고 장애 분석이 어려워진다.
- **수정안**:
```python
except Exception as e:
    try:
        self._conn.rollback()
    except Exception:
        pass
    self._ui_log(...)
    return 0
```
- **테스트**: DELETE 중간 예외를 강제로 발생시켜 `in_transaction == False`와 데이터 원복 여부를 확인.

### [TF-A-3] StateTracker 초기화가 UI 래퍼(`main_a`)에만 의존 (MEDIUM)
- **파일**: `modules/core/services/project_service.py:214`, `main_a.py:2781`, `main_a.py:2783`
- **현재 코드**:
```python
# project_service.py
project._load_from_db()

# main_a.py
success = self._project_service.rollback_episode()
if success:
    self.state_tracker = None
```
- **문제**: 서비스 레이어는 state tracker 무효화를 직접 보장하지 않고, 특정 호출자(`main_a`) 구현에 의존한다.
- **영향**: 다른 호출 경로가 생기면 롤백 후 stale `npc_registry`가 남을 수 있다.
- **수정안**: `ProjectService.rollback_episode()`에 tracker invalidation 콜백 주입 또는 서비스 반환 객체에 `invalidate_state_tracker=True` 포함.
- **테스트**: `ProjectService`를 직접 호출하는 테스트 더블에서 rollback 성공 후 tracker 무효화가 강제되는지 확인.

## 요약
| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 2 |
