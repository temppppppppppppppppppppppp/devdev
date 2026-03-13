# [MCP-T4] Destructive Ops / Recovery Findings

> 작성일: 2026-03-13
> 상태: `3pass executed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check`
> 기준 오더: `main_a-control-plane-detail-full-survey-audit-order.md`

---

## 조사 범위

- `main_a.py`
  - `_reset_stage_2()`
  - `_rewind_stage_2()`
  - `_rollback_episode()`
  - `_wipe_production_data()`
  - `_shutdown_app()`
- `modules/core/services/project_service.py`
- `modules/core/db_manager.py`
- `modules/core/foreshadow_tracker.py`
- destructive op 이후 invalidate/restore 되는 runtime tracker/cache 경계

## 필수 근거

- `tests/test_main_a_rollback.py`
- `tests/test_project_service.py`
- `tests/property/test_db_rollback_props.py`
- `tests/chaos/test_partial_commit.py`
- `tests/integration/test_patch_wiring.py`
- 추가 확인
  - `tests/test_resume_status.py`
  - `tests/test_safe_ops_db_consistency.py`
  - `tests/test_bridge_quality_summary.py`

## PASS 기록

- PASS 1: 완료
  - 후보 6건 수집
  - destructive op 범위, rollback invariant, shutdown non-blocking 경계, 기존 문서 중복 여부 확인
- PASS 2: 완료
  - 관련 테스트 `63 passed in 6.66s`
  - ad hoc 재현 4건으로 false-return/partial-cleanup, foreshadow wipe, shutdown abort 검증
  - 기존 문서와 겹치는 `protocol/direct-cursor` 성격 항목은 재오픈하지 않음
- PASS 3: 완료
  - PASS1 후보 6건 -> PASS2 제거 3건 -> 최종 3건

## Executive Summary

- `reset_stage_2()`, `rewind_stage_2()`, `rollback_episode()`는 실패를 반환한 뒤에도 이미 파괴적 DB 변경이 커밋될 수 있다.
- `main_a.py`의 rollback/rewind 후처리는 `foreshadow_tracker.clear() + save_to_db()`로 과거 복선까지 전부 삭제한다.
- `_shutdown_app()`은 일부 flush만 non-blocking이며, `bible`/`genre_info` 저장 실패는 DB close 이전에 종료 시퀀스를 중단시킨다.

## PASS 2 제거 항목

| 후보 | 판정 | 이유 |
|----|----|----|
| `rewind_stage_2()`의 Stage 2 selection delete가 `ep_num`에 의존 | 제거 | 현재 Stage 2 기록 경로는 `ep_num=global_arc_no`를 사용해 즉시 오작동 근거가 부족 |
| `wipe_production_data()` 전용 partial cleanup finding 분리 | 제거 | 구조는 `MCP-T4-001`과 동일하며 별도 독립 finding으로 쪼개면 중복 |
| `world_state/fact_ledger/preset restore` 테스트 공백 자체 | 제거 | coverage gap으로는 유효하지만 단독 제품 결함으로 확정할 근거는 부족 |

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| MCP-T4-001 | P1 | retained | `project_service.py` / `reset_stage_2`, `rewind_stage_2`, `rollback_episode` | 실패 반환 뒤에도 destructive DB mutation이 이미 커밋되어 app cache와 DB가 어긋날 수 있음 |
| MCP-T4-002 | P1 | retained | `main_a.py` / `_rewind_stage_2`, `_rollback_episode` | rewind/rollback 성공 후 `foreshadow_tracker` 전체 초기화로 target 이전 복선까지 소거됨 |
| MCP-T4-003 | P2 | retained | `main_a.py` / `_shutdown_app` | shutdown이 anchor save 실패를 비차단 처리하지 않아 DB close 이전에 종료 시퀀스가 중단됨 |

---

## [MCP-T4-001] P1 | destructive op가 `False`를 반환한 뒤에도 이미 일부 DB 삭제가 커밋된다

**현상 요약**

`ProjectService`의 `reset_stage_2()`, `rewind_stage_2()`, `rollback_episode()`는 마지막 성공 판정 전에 이미 `db.reset_after(...)`로 destructive delete를 커밋한다. 이후 `safe_commit()` 또는 `save_anchor("bible"/"arcs")` 단계에서 실패하면 메서드는 `False`를 반환하지만, upstream `main_a.py`는 이를 "실패했으니 runtime cache를 건드리지 말아야 하는 경로"로 해석한다. 결과적으로 DB는 일부 비워졌는데 app cache/tracker는 이전 상태를 계속 들고 있는 split-brain이 생긴다.

**코드 근거**

- `modules/core/services/project_service.py:161-168`
  - `reset_stage_2()`가 `project.db.reset_after(1)` 후에야 `_safe_commit()`로 Stage 2 metadata 삭제를 확정한다.
- `modules/core/services/project_service.py:221-225`
  - `rewind_stage_2()`가 `project.db.reset_after(target_ep)` 후 `save_anchor("arcs", updated_arcs)`를 호출한다.
- `modules/core/services/project_service.py:304-312`
  - `rollback_episode()`가 `project.db.reset_after(target_ep)`와 `project.db.commit()` 이후에 `save_anchor("bible", pending_bible)`를 호출한다.
- `modules/core/db_manager.py:2283-2333`
  - `reset_after()` 내부가 자체 `commit()`을 수행해 downstream 실패와 분리된 커밋 경계를 만든다.
- `main_a.py:3045-3071`
- `main_a.py:3075-3102`
- `main_a.py:3106-3141`
  - `success`가 `True`일 때만 cache/tracker invalidation을 수행한다.

**downstream 영향 경계**

- operator는 "실패"를 보지만 `manuscripts`, `blueprints`, `state_logs`, `episode_bibles`, `foreshadow` 등은 이미 일부 삭제될 수 있다.
- app-level cache invalidation이 스킵되어 `state_tracker`, prompt timeline cache, writer/director cache가 stale 상태로 남는다.
- 이후 재시도 시 DB 실상과 runtime 상태가 달라져 destructive op preview 및 실제 동작 판단이 더 어려워진다.

**현재 테스트 근거 또는 테스트 부재**

- `tests/test_project_service.py:88-101`
  - `reset_stage_2()` commit failure는 `False`와 log만 검증하고, DB가 보존되는지는 검증하지 않는다.
- `tests/test_project_service.py:124-135`
  - `rewind_stage_2()`는 success path만 검증한다.
- `tests/test_project_service.py:159-190`
  - `rollback_episode()`는 success path와 HUD restore만 검증한다.
- `tests/test_main_a_rollback.py:23-48`
  - `False` 반환 시 cache 유지, `True` 반환 시 cache invalidation만 검증한다.
- 추가 재현:
  - `reset_stage_2()` + `safe_commit=False` -> `{'result': False, 'manuscripts': 0}`
  - `rewind_stage_2()` + `save_anchor("arcs")` 실패 -> `{'result': False, 'manuscripts': 0}`
  - `rollback_episode()` + `save_anchor("bible")` 실패 -> `{'result': False, 'manuscripts': 1}`

**기존 문서와의 중복 여부**

- `duplicate status`: `related-but-new-control-plane-surface`
- 관련 문서:
  - `OPUS-TF-T1-infrastructure-findings.md`의 direct cursor / commit contract 지적은 존재
  - 그러나 `False` 반환과 app-level cache invalidation 스킵이 결합된 control-plane partial-cleanup surface는 이번 문서가 신규다

**권장 후속 조치**

- `DBManager.reset_after(..., commit=False)` 같은 경계로 바꾸고 service 단에서 단일 트랜잭션으로 확정한다.
- 최소한 이미 destructive mutation이 커밋된 뒤 실패한 경우에는 `False` 대신 `partial_failure_committed` 같은 구조화 결과를 반환해 app cache invalidation을 강제한다.
- `reset_stage_2`, `rewind_stage_2`, `rollback_episode` 각각에 대해 "failure after reset_after" 회귀 테스트를 추가한다.

---

## [MCP-T4-002] P1 | rewind/rollback 후처리가 target 이전 복선까지 전부 지운다

**현상 요약**

`ProjectService`는 `db.reset_after(target_ep)`로 `foreshadow.planted_ep >= target_ep`만 지워 이전 복선은 보존하려고 한다. 그런데 `main_a.py`의 `_rewind_stage_2()`와 `_rollback_episode()`는 service 성공 직후 `foreshadow_tracker.clear()` 후 `save_to_db()`를 호출한다. `ForeshadowTracker.save_to_db()`는 항상 `DELETE FROM foreshadow`를 먼저 실행하므로, 결과적으로 target 이전 복선까지 모두 날아간다.

**코드 근거**

- `main_a.py:3096-3100`
  - `_rewind_stage_2()` 성공 후 `_ft.clear(); _ft.save_to_db(...)`
- `main_a.py:3134-3138`
  - `_rollback_episode()` 성공 후 `_ft.clear(); _ft.save_to_db(...)`
- `modules/core/foreshadow_tracker.py:431-461`
  - `save_to_db()`가 `DELETE FROM foreshadow` 후 전체 재삽입
- `modules/core/foreshadow_tracker.py:682-686`
  - `clear()`는 모든 hook/plant/payoff 메모리를 비운다
- `modules/core/db_manager.py:2325`
  - service 레벨 DB rollback은 원래 `planted_ep >= target_ep`만 삭제한다

**downstream 영향 경계**

- rewind/rollback 이후에도 살아 있어야 할 초반 복선이 통째로 사라진다.
- 이후 Stage 4 run이 복선 상태를 재사용할 때 seed/payoff continuity가 무너진다.
- service-level rollback invariant와 app-level cleanup invariant가 서로 다른 의미를 보게 된다.

**현재 테스트 근거 또는 테스트 부재**

- `tests/test_main_a_rollback.py:23-48`
  - rollback success/cancel 시 cache만 확인하고 foreshadow preservation은 보지 않는다.
- `tests/test_main_a_rollback.py:51-108`
  - reset/wipe의 `foreshadow_tracker.clear()`만 검증하고 rewind/rollback은 커버하지 않는다.
- `tests/test_safe_ops_db_consistency.py:50-61`
  - `DBManager.reset_after()`가 Stage 2/4 selection 보존 규칙을 지키는지만 본다. app-level foreshadow cleanup은 검증하지 않는다.
- 추가 재현:
  - rollback path에 `planted_ep=1` 복선 1건만 둔 상태에서 `_rollback_episode()` 실행 -> `{'before': 1, 'after': 0}`
  - 동일 조건에서 `_rewind_stage_2()` 실행 -> `{'before': 1, 'after': 0}`

**기존 문서와의 중복 여부**

- `duplicate status`: `related-but-new-control-plane-surface`
- 관련 문서:
  - `OPUS-TF-T5-domain-auxiliary-findings.md`의 `foreshadow_tracker.save_to_db()` 트랜잭션 경고는 tracker 내부 구현 이슈다
  - 이번 finding은 `main_a.py` rollback orchestration이 tracker를 잘못 사용하는 control-plane 이슈다

**권장 후속 조치**

- `ForeshadowTracker.rollback_to(target_ep)`를 추가해 target 이후만 제거한다.
- 또는 service 완료 후 tracker를 `load_from_db()`로 다시 로드해 DB 기준 상태를 복원한다.
- `reset/wipe(target=1)`에서만 `clear()`를 허용하고, rewind/rollback은 partial restore 경로를 사용한다.

---

## [MCP-T4-003] P2 | shutdown은 일부만 non-blocking이며, anchor save 실패가 DB close를 건너뛴다

**현상 요약**

`_shutdown_app()`은 metrics, session cost, pass rate, failure learner, character voice, foreshadow, emotion tracker 저장은 각각 `try/except`로 감싼다. 하지만 그 다음의 `save_v20_anchor("bible", ...)`와 `db.save_anchor("genre_info", ...)`는 예외 보호가 없다. 이 둘 중 하나가 실패하면 메모리 close, 최종 DB commit, DB close가 실행되기 전에 shutdown이 중단된다.

**코드 근거**

- `main_a.py:2415-2421`
  - `save_v20_anchor("bible", ...)`, `db.save_anchor("genre_info", ...)`가 비보호 호출
- `main_a.py:2459-2484`
  - 메모리 close, DB commit, DB close는 그 이후 단계라 앞선 예외가 나면 도달하지 못한다
- `main_a.py:2172-2189`
  - 정상 종료 선택(메뉴 5)과 `KeyboardInterrupt` 모두 `_shutdown_app()`을 직접 호출한다

**downstream 영향 경계**

- clean exit가 critical error path로 바뀔 수 있다.
- `memory.close()`, DB close, 마지막 flush가 스킵될 수 있다.
- process runner / desktop bridge 기준으로는 정상 종료와 실패 종료가 뒤섞일 위험이 있다.

**현재 테스트 근거 또는 테스트 부재**

- `tests/test_resume_status.py:51-77`
  - `pass_rate_monitor.save()` 실패만 non-blocking인지 본다.
- `tests/test_resume_status.py:80-116`
  - session cost save만 본다.
- 위 테스트들은 `save_v20_anchor()` 또는 `save_anchor("genre_info")` 실패를 전혀 다루지 않는다.
- 추가 재현:
  - `save_v20_anchor`를 `RuntimeError("anchor fail")`로 만들고 `_shutdown_app()` 호출 -> `{'raised': 'RuntimeError', 'message': 'anchor fail', 'db_close_called': False}`

**기존 문서와의 중복 여부**

- `duplicate status`: `none`

**권장 후속 조치**

- `save_v20_anchor("bible")`와 `save_anchor("genre_info")`도 각각 non-blocking 보호 구간으로 감싼다.
- 종료 함수는 "best effort flush -> unconditional memory/db close" 순서로 재구성한다.
- shutdown anchor failure regression test를 추가한다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `world_state` / `fact_ledger` / `preset_registry` restore 경로 | direct ProjectService 테스트 부재 | destructive op 후 callback failure와 partial restore를 보는 unit test |
| rewind/rollback의 foreshadow 보존 | 테스트 부재 | target 이전 복선이 유지되는지 검증하는 regression test |
| destructive op false-return partial mutation | 테스트 부재 | `reset_after()` 이후 실패를 주입해 DB/cache split-brain 여부를 보는 test |
| shutdown anchor failure | 테스트 부재 | `save_v20_anchor` / `save_anchor("genre_info")` 예외 시 DB close 보장 test |

## 마감 체크

- confirm/cancel gating 검증: 완료
- DB/file/vector memory/state restore invariant 검증: 부분 실패 2건 확정
- safe commit failure path 검증: 실패 후 partial cleanup 1건으로 확정
- shutdown non-blocking failure path 검증: 실패 후 close skip 1건으로 확정

## 최종 판정

- 최종 retained finding: `3건`
  - `P1`: 2건
  - `P2`: 1건
  - `P3`: 0건
- 현재 문서는 `template / not executed`가 아니라 `executed T4 finding set`이다.
