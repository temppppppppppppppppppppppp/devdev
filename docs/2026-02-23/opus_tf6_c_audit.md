# TF-6-C: 트랜잭션 안전성 (Transaction Safety)

## 감사 범위
- 파일: `modules/core/db_manager.py`, `modules/core/vec_memory.py`, `modules/core/services/project_service.py`, `modules/core/stage4_post_processor.py`
- 코드 줄 수: 약 500줄 수동 확인

## 발견 사항

### [TF-C-1] `commit_episode_factory()`의 중첩 트랜잭션 상태를 진입 시점 1회만 샘플링 (MEDIUM)
- **파일**: `modules/core/db_manager.py:1300`, `modules/core/db_manager.py:1376`, `modules/core/db_manager.py:1385`
- **현재 코드**:
```python
nested_transaction = self.conn.in_transaction
...
if not nested_transaction:
    self.commit()
...
if not nested_transaction:
    self.rollback()
```
- **문제**: 함수 중간에 하위 경로가 트랜잭션 상태를 바꿔도(예: 내부 rollback) 최종 분기는 초기 스냅샷만 본다.
- **영향**: 실패 경로에서 의도와 실제 트랜잭션 상태가 어긋나면 commit/rollback 호출 의미가 불명확해진다.
- **수정안**: 종료 시점 분기 전에 `self.conn.in_transaction`을 재평가하거나, 함수 전체를 단일 `transaction()` 컨텍스트로 감싼 뒤 savepoint 정책 일원화.
- **테스트**: 내부 하위 호출에서 강제 rollback 발생시키고 상위 경로가 추가 commit/rollback 없이 일관 종료되는지 검증.

### [TF-C-2] `transaction()` 컨텍스트는 `_lock` 보호 없이 직접 `BEGIN/COMMIT/ROLLBACK` 수행 (MEDIUM)
- **파일**: `modules/core/db_manager.py:1440`, `modules/core/db_manager.py:1447`, `modules/core/db_manager.py:1450`
- **현재 코드**:
```python
@contextmanager
def transaction(self):
    nested = self.conn.in_transaction
    if not nested:
        self.cursor.execute("BEGIN TRANSACTION")
    ...
    if not nested:
        self.conn.commit()
```
- **문제**: 같은 클래스의 `begin()/commit()/rollback()`은 `_lock`을 사용하지만, `transaction()`은 락 없이 직접 커넥션을 제어한다.
- **영향**: 멀티스레드 경합 시 트랜잭션 경계 race 가능성 증가.
- **수정안**: `transaction()` 내부도 `_lock` 스코프 안에서 경계 제어 수행.
- **테스트**: 다중 스레드에서 `with db.transaction()` 경쟁 쓰기 시 lock/rollback 일관성 검증.

## 요약
| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
