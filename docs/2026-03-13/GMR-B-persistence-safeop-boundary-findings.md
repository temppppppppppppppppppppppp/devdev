# GMR-B Persistence, SSOT & Safe-Op Boundary Findings

> Date: 2026-03-13
> Commit: `d9825a69`
> Workspace State: dirty

## PASS 1 관찰

- `docs/stage_map/interfaces.md`는 DB를 durable handoff surface로 정의한다.
- `modules/core/db_manager.py:2283-2346`의 `reset_after()`가 episode-derived data 삭제의 중심이다.
- `modules/core/services/project_service.py`가 reset/rewind/rollback/wipe에서 앵커 삭제, vector 삭제, runtime restore를 결합한다.

## PASS 2 교차 검증

- `db_manager.py`는 `anchors`, `blueprints`, `state_logs`, `episode_bibles`, `director_selections`, `stage_attempts` 삭제를 중심으로 safe-op를 수행한다.
- `ProjectService._restore_runtime_state()`는 `world_state`, `fact_ledger`, `emotion_tracker`, `state_delta_tracker`, `preset_registry` 복원을 각각 별도 처리한다.
- `main_a.py:3228-3348`는 safe-op 후 일부 app cache와 agent cache를 수동 무효화한다.

## PASS 3 최종 findings

### [GMR-B-001] safe-op의 durable delete는 DB 중심이지만 runtime restore는 best-effort fail-open이다

- Severity: `P1`
- Evidence:
  - `modules/core/services/project_service.py:63-98`
  - `modules/core/services/project_service.py:177-214`
  - `modules/core/services/project_service.py:286-433`
- Why macro risk:
  - DB rollback/wipe/reset가 성공해도 `world_state.rollback_to()`, `fact_ledger.rollback_to()` 실패는 UI 로그만 남기고 계속 진행한다.
  - 결과적으로 “DB truth는 과거 시점, runtime state는 부분 복원”인 비대칭 상태가 허용된다.
- Recommended next order:
  - safe-op 결과를 `DB restored / runtime restored / tracker restored`로 분리 기록하는 후속 오더 필요.

### [GMR-B-002] DBManager는 local cursor 전환 정책과 legacy shared cursor 사용이 공존한다

- Severity: `P1`
- Evidence:
  - `modules/core/db_manager.py:46-55`
  - `modules/core/db_manager.py:1564-1575`
  - `modules/core/db_manager.py:1843-1850`
- Why macro risk:
  - 클래스 주석은 `self.cursor`를 backward compatibility용 legacy surface로 규정하지만, live anchor/blueprint 경로 일부는 여전히 `self.cursor`를 사용한다.
  - WAL + `check_same_thread=False` 환경에서 이 혼합은 조사 난이도와 concurrency risk를 동시에 올린다.
- Recommended next order:
  - live writer/reader 경로의 cursor 사용 패턴을 별도 inventory로 분리 문서화.

## Closed assumptions

- “txt export가 handoff truth다” 가설은 기각한다.
- 현재 실운영 truth는 DB 중심이라고 보는 것이 맞다.

## Last Verified
- Date: 2026-03-13
- Commit: `d9825a69`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
