# Opus TF-5: Integration Debug Audit (TF-F)

> 감사일: 2026-02-23  
> 감사자: Codex (GPT-5)  
> 방법: 수동 라인 단위 코드 열람 (검색 결과 단독 근거 사용 금지)  
> 대상 파일:
> - `main_a.py`
> - `modules/core/services/project_service.py`
> - `config/models.yaml`
> - `config/settings/validation.yaml`
> - 호출 계약 확인: `modules/core/stage2_preflight.py`, `modules/core/vec_memory.py`

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 1 |
| LOW | 0 |

---

### [F-1] Stage2 reset가 DB 커밋 실패를 무시하고 성공 상태를 강제함 — HIGH
- **위치**: `modules/core/services/project_service.py:48`, `modules/core/services/project_service.py:49`, `modules/core/services/project_service.py:50`, `main_a.py:347`, `main_a.py:358`, `main_a.py:1977`
- **코드 인용**:
```python
# project_service.py
project.db.cursor.execute("DELETE FROM anchors WHERE key = 'arcs'")
self._safe_commit()
project.arcs = []
self._ui.log("✅ Stage 2 데이터가 삭제되었습니다...")
```
```python
# main_a.py
try:
    self.current_project.db.conn.commit()
    return True
except Exception:
    ...
    return False
```
- **현상**: `_safe_commit()`의 반환값(`False`)을 확인하지 않고 메모리 상태(`project.arcs=[]`)와 성공 로그를 강제한다.
- **재현 시나리오**: 메뉴 `88`(main_a.py:1977)로 Stage2 reset 실행 중 커밋 실패(락/디스크 오류) 발생 시, DB는 롤백됐는데 앱 메모리는 삭제 완료 상태로 진행된다.
- **영향**: 같은 세션에서 DB와 인메모리 아크 상태가 분기되어 Stage 2/3 진입 판단이 오염된다(잘못된 운영 판단/후속 파이프라인 오작동).
- **수정 제안**: `if not self._safe_commit(): return`으로 즉시 중단하고 성공 로그/메모리 갱신을 커밋 성공 후로 이동.

### [F-2] rollback_episode가 커밋 실패 후에도 파일/벡터 삭제를 계속 수행함 — HIGH
- **위치**: `modules/core/services/project_service.py:162`, `modules/core/services/project_service.py:185`, `modules/core/services/project_service.py:188`, `modules/core/services/project_service.py:198`, `main_a.py:1973`
- **코드 인용**:
```python
# project_service.py
project.db.cursor.execute(f"DELETE FROM {t} WHERE ep_num >= ?", (target_ep,))
...
self._safe_commit()

for f in project.paths.drafts.glob("*.txt"):
    ...
    f.unlink()
```
```python
memory = self._memory_fn()
if memory and hasattr(memory, "delete_episodes_from"):
    deleted = memory.delete_episodes_from(target_ep)
```
- **현상**: SQL 삭제 후 `_safe_commit()` 실패 여부를 확인하지 않고 원고 파일 삭제/벡터 메모리 삭제를 계속한다.
- **재현 시나리오**: 메뉴 `44`(main_a.py:1973) 롤백 중 커밋 실패 시 SQL은 롤백되지만 파일·벡터는 이미 삭제되어 스토어 간 상태가 찢어진다.
- **영향**: DB에는 남아있는 회차가 파일/벡터에서는 사라지는 교차 스토어 불일치가 발생한다(복구 비용 높음, 연속성/검색 경로 오작동).
- **수정 제안**: `_safe_commit()` 결과가 `False`면 즉시 `return`하고 파일/벡터 삭제 단계를 실행하지 않도록 가드.

### [F-3] 롤백 취소/실패 시에도 main이 state_tracker를 강제로 파기함 — MEDIUM
- **위치**: `modules/core/services/project_service.py:115`, `main_a.py:2781`, `main_a.py:2782`
- **코드 인용**:
```python
# project_service.py
if confirm != "y":
    self._ui.log("❌ 취소되었습니다.")
    return
```
```python
# main_a.py
def _rollback_episode(self):
    self._project_service.rollback_episode()
    self.state_tracker = None
```
- **현상**: 서비스 레이어는 취소/실패를 반환값으로 전달하지 않는데, 호출부는 결과와 무관하게 `state_tracker`를 파기한다.
- **재현 시나리오**: 롤백 메뉴 진입 후 `n`으로 취소하면 실제 롤백은 미수행이지만 즉시 `state_tracker=None` 및 캐시 무효화가 실행된다.
- **영향**: 사용자 취소만으로 런타임 상태 추적기가 불필요하게 초기화되어 다음 Stage에서 상태 재구축 오버헤드/검증 일관성 저하가 발생한다.
- **수정 제안**: `rollback_episode()`가 `bool` 성공 여부를 반환하도록 바꾸고, `True`일 때만 `state_tracker`/캐시를 무효화.

---

## 비이슈 확인 (회귀 점검)
- `config/models.yaml:3`에서 `manager: gemini-2.5-flash`가 반영되어 Tier 3 A-1 설정 회귀는 확인되지 않음.
- `main_a.py:2291`, `main_a.py:2525`, `main_a.py:3071` 경로에서 Stage 2/3/4 DI가 각각 주입되어 통합 배선 자체는 유지됨.
