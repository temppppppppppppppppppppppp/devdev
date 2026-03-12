# TF Safe-Ops DB Consistency 3-Pass Audit

Date: 2026-03-11
Status: PASS
Confidence: 97%
Scope:
- `rollback_episode`
- `wipe_production_data`
- `reset_stage_2`
- `rewind_stage_2`
- DB cleanup coverage
- runtime cache invalidation
- regression / runbook sync

## Summary

이번 배치는 기존 safe-op 기능을 현재 DB 체제에 맞게 재정렬한 작업이다.

핵심 정합성은 다음과 같이 확인됐다.

- 공통 정리 기준은 [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)에 모였다.
- 각 메뉴 동작은 [project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py)에서 `db.reset_after()`를 중심으로 동작하게 정리됐다.
- 메뉴 성공 후 런타임 캐시/트래커 무효화는 [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)에서 성공 시에만 실행되게 맞춰졌다.
- 운영 의미와 실제 삭제 범위는 [runbook.md](C:/Users/User/Desktop/글도비/docs/stage_map/runbook.md)에 최신 기준으로 동기화됐다.

## Pass 1: Correctness

확인 결과, 기존의 오래된 수동 삭제 루프 대신 공통 cleanup 경로를 타도록 정리됐다.

- [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py#L2190)
  - `reset_after(target_ep)`가 다음 테이블을 함께 정리한다.
  - `episode_quality_labels`
  - `episode_quality_signals`
  - `episode_quality_observations`
  - `episode_pacing`
  - `foreshadow`
  - `npc_relationship_edges`
  - `npc_relationship_history`
  - `stage_attempts(stage 3/4)`
- [project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py#L143)
  - `reset_stage_2()`는 Stage 2 메타데이터, 요약 anchor, downstream episode 산출물을 함께 정리한다.
- [project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py#L180)
  - `rewind_stage_2()`는 제거되는 arc의 `ep_start`를 우선 사용해 `target_ep`를 추론하고, 이후 downstream episode 산출물을 정리한다.
- [project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py#L242)
  - `rollback_episode()`는 HUD `actual_truth` 복원, seed 복구, vector cleanup, runtime rollback까지 연결된다.
- [project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py#L350)
  - `wipe_production_data()`는 setup 자산은 유지하고 episode-derived 산출물만 정리한다.

판정:
- P0/P1 정합성 이슈 없음

## Pass 2: Safety

성공 시에만 캐시/트래커가 무효화되는지, 회귀가 깨지지 않는지를 확인했다.

- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py#L3030)
  - `reset_stage_2()` 성공 시에만 state/prompt/director/writer/foreshadow cache를 정리한다.
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py#L3060)
  - `rewind_stage_2()`도 성공 시에만 같은 계열 invalidation을 수행한다.
- [main_a.py](C:/Users/User/Desktop/글도비/main_a.py#L3130)
  - `wipe_production_data()`도 성공 시에만 invalidation을 수행한다.

Regression:
- `python -m pytest tests/ -q`
  - `3877 passed, 16 skipped, 1 warning`
- `python -m pytest --collect-only -q tests`
  - `3893 collected`

관련 회귀 파일:
- [test_safe_ops_db_consistency.py](C:/Users/User/Desktop/글도비/tests/test_safe_ops_db_consistency.py)
- [test_project_service.py](C:/Users/User/Desktop/글도비/tests/test_project_service.py)
- [test_main_a_rollback.py](C:/Users/User/Desktop/글도비/tests/test_main_a_rollback.py)

판정:
- 안전성 PASS

## Pass 3: Completeness

코드, 테스트, 운영 문서가 함께 업데이트됐는지 확인했다.

- 코드
  - [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py)
  - [project_service.py](C:/Users/User/Desktop/글도비/modules/core/services/project_service.py)
  - [main_a.py](C:/Users/User/Desktop/글도비/main_a.py)
- 테스트
  - [test_safe_ops_db_consistency.py](C:/Users/User/Desktop/글도비/tests/test_safe_ops_db_consistency.py)
  - [test_project_service.py](C:/Users/User/Desktop/글도비/tests/test_project_service.py)
  - [test_main_a_rollback.py](C:/Users/User/Desktop/글도비/tests/test_main_a_rollback.py)
- 운영 문서
  - [runbook.md](C:/Users/User/Desktop/글도비/docs/stage_map/runbook.md)

판정:
- 구현, 회귀, 운영 문서가 같이 닫혔다.

## Residual Limits

초기 감리 시점에는 `director_selections` Stage 2 / Stage 4 혼재가 비차단 잔여로 남아 있었다.

이 항목은 2026-03-11 후속 패치에서 해소됐다.

- 해결 문서: [TF-director-selections-stage-split-resolution.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/TF-director-selections-stage-split-resolution.md)

## Final Verdict

현재 safe-op 경로는 현 DB 체제와 정합하다.

- `rollback`
- `wipe`
- `reset`
- `rewind`

모두 현재 품질 테이블, 관계 테이블, pacing, foreshadow, stage attempts 구조를 따라간다.

후속 패치까지 포함하면 `director_selections` Stage split 문제도 해결된 상태다.
