# [MRL-T2] Cache / Anchor / History Lifecycle Findings

> 작성일: 2026-03-13
> 상태: `3pass executed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-runtime-recovery-lifecycle-detail-full-survey-audit-order.md`

---

## 조사 범위

- `main_a.py`
  - `_ignite_quad_cache_system()`
  - `_is_cache_alive()`
  - `_load_v50_history()`
  - boot 이후 cache/history restore 관련 inline restore, destructive-op wrapper
- 직접 downstream
  - `modules/core/services/project_service.py`
  - `modules/core/db_manager.py`
  - `modules/core/emotion_tracker.py`
  - `modules/core/stage4_post_processor.py`
- 기존 문서
  - `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`
  - `docs/2026-03-13/MPN-T1-commit-preset-recovery-findings.md`
  - `docs/2026-03-13/MDH-T4-bootstrap-history-cache-helper-liveness-findings.md`

## 필수 근거

- `tests/test_stage_transition.py`
- `tests/test_project_service.py`
- `modules/core/services/project_service.py`
- `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`

## 추가 검증 근거

- `tests/property/test_db_rollback_props.py`
- `tests/chaos/test_partial_commit.py`
- `tests/integration/test_patch_wiring.py`
- `modules/core/db_manager.py`
- `modules/core/emotion_tracker.py`
- `modules/core/stage4_post_processor.py`

## PASS 기록

- PASS 1: 완료
  - 후보 4건 수집
  - `sys_caches` live recovery 연결 여부, `_load_v50_history()`의 실질적 지위, destructive-op 이후 next-boot drift 여부, history restore authority 분산 여부를 분리했다.
- PASS 2: 완료
  - 코드 근거, 테스트 근거, 기존 문서 중복 여부를 교차 검증했다.
  - 실행 검증:
    - `pytest tests/test_stage_transition.py tests/test_project_service.py tests/property/test_db_rollback_props.py tests/chaos/test_partial_commit.py tests/integration/test_patch_wiring.py -q`
    - 결과: `52 passed in 4.46s`
  - ad hoc verification 1건 수행:
    - `EmotionArcTracker.save_to_db()` 후 `rollback_to()`만 호출하면 live tracker는 잘리지만, 새 tracker가 `load_from_db()`를 하면 rollback 이전 미래 에피소드가 다시 로드되는 것을 재현했다.
- PASS 3: 완료
  - PASS1 후보 4건 -> PASS2 제거 2건 -> 최종 2건

## Executive Summary

- `emotion_history`는 destructive recovery에서 메모리상으로만 잘리고 DB anchor에는 남기 때문에, rollback/reset/wipe 직후의 runtime state와 다음 부팅 후 runtime state가 서로 달라진다.
- cache/history restore는 단일 authority가 없다. `sys_caches`는 dead helper에 묶여 있고, `_load_v50_history()`는 stub이며, 실제 live restore는 boot inline load와 destructive-op wrapper의 ad hoc sync로 분산돼 있다.

## PASS 2 제거 항목

| 후보 | 판정 | 이유 |
|----|----|----|
| `_ignite_quad_cache_system()` dead code 자체 | 제거 | `docs/2026-03-13/MDH-T4-bootstrap-history-cache-helper-liveness-findings.md`에서 dead 확정이 이미 닫혀 있다. 이번 문서에서는 dead 여부가 아니라 runtime lifecycle graph 연결성만 남긴다. |
| `_load_v50_history()` no-op stub 자체 | 제거 | `docs/2026-03-13/MDH-T4-bootstrap-history-cache-helper-liveness-findings.md`, `docs/2026-03-13/MCP-T2-agent-bootstrap-di-findings.md`에서 이미 관측됐다. 이번 문서에서는 stub 자체 재오픈이 아니라 live restore authority 붕괴만 유지한다. |

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| `MRL-T2-001` | `P1` | retained | `modules/core/services/project_service.py`, `modules/core/emotion_tracker.py`, `main_a.py` | destructive recovery가 `emotion_history`를 메모리에서만 자르고 DB에는 남겨서 다음 boot에서 rollback 이전 감정 이력이 재오염된다 |
| `MRL-T2-002` | `P2` | retained | `main_a.py`, `modules/core/services/project_service.py` | cache/history restore의 nominal helper가 live recovery authority가 아니어서 boot, destructive-op, next-boot가 서로 다른 복구 경로를 가진다 |

---

## [MRL-T2-001] P1 | destructive recovery 후 `emotion_history`가 다음 boot에서 되살아난다

1. ID
   - `MRL-T2-001`
2. Severity
   - `P1`
3. 현상 요약
   - Stage 4 PASS 경로는 `emotion_history`를 DB anchor에 저장한다.
   - 그러나 rollback/reset/wipe/rewind는 `ProjectService._restore_runtime_state()`에서 `emotion_tracker.rollback_to(target_ep)`만 호출하고, 잘린 결과를 DB에 다시 저장하거나 anchor를 삭제하지 않는다.
   - 그 결과 destructive recovery 직후 현재 세션의 `emotion_tracker.history`는 맞게 보일 수 있지만, 다음 boot에서 `EmotionArcTracker.load_from_db()`가 rollback 이전 미래 에피소드 감정 이력을 다시 불러온다.
4. 코드 근거
   - Stage 4 PASS가 감정 이력을 추가하고 DB에 저장한다.
     - `modules/core/stage4_post_processor.py:484-489`
   - `EmotionArcTracker.save_to_db()` / `load_from_db()`는 `emotion_history` anchor를 직접 사용한다.
     - `modules/core/emotion_tracker.py:370-391`
   - boot path는 새 tracker를 만든 뒤 DB anchor에서 곧바로 감정 이력을 복원한다.
     - `main_a.py:1811-1816`
   - destructive recovery는 `reset_after()` 뒤 `_restore_runtime_state()`를 호출하고, 여기서 `emotion_tracker.rollback_to(target_ep)`만 수행한다.
     - `modules/core/services/project_service.py:63-96`
     - `modules/core/services/project_service.py:163-197`
     - `modules/core/services/project_service.py:201-264`
     - `modules/core/services/project_service.py:268-353`
     - `modules/core/services/project_service.py:381-409`
   - `DBManager.reset_after()`는 episode tables와 stage artifacts는 지우지만 `anchors` 테이블의 `emotion_history`는 건드리지 않는다.
     - `modules/core/db_manager.py:2283-2333`
   - anchor SSOT 주석은 허용 키를 `bible`, `arcs`, `genre_info`, `sys_caches`로만 적고 있는데, 실제 감정 이력은 별도 등록 없이 `emotion_history`에 저장된다.
     - `modules/core/db_manager.py:188-192`
     - `modules/core/emotion_tracker.py:382`
5. downstream 영향 경계
   - destructive recovery 직후 same-session에서는 `emotion_tracker.history`가 타깃 이전으로 잘린 것처럼 보여도, 앱 재시작 후에는 미래 감정 이력이 다시 로드된다.
   - `EmotionArcTracker.check_monotony()`, `get_recommended_emotion_for_next()`, `get_emotion_report()`는 모두 `history`를 직접 소비한다.
     - `modules/core/emotion_tracker.py:154`
     - `modules/core/emotion_tracker.py:291`
     - `modules/core/emotion_tracker.py:343`
   - 즉 rollback/reset/wipe 이후 다음 회차 생성에서 감정선 advisory가 이미 삭제된 화의 이력을 포함할 수 있다.
   - 동일한 destructive op라도 "재시작 없이 계속 진행"과 "재시작 후 진행"의 runtime state가 달라지는 next-boot drift다.
6. 현재 테스트 근거 또는 테스트 부재
   - 실행 검증: `pytest ...` 총 `52 passed`.
   - `tests/test_project_service.py`는 `reset_after()` 호출과 `_load_from_db()` 호출만 확인하고, `emotion_history` anchor 정리나 next-boot reload는 다루지 않는다.
   - `tests/property/test_db_rollback_props.py`, `tests/chaos/test_partial_commit.py`는 `_assert_rollback_invariants()`의 warning 조건만 검증한다. DB에 남은 감정 이력이 다음 boot에서 재주입되는지는 테스트하지 않는다.
   - `tests/integration/test_patch_wiring.py`는 Stage 4 PASS에서 `emotion_tracker.save_to_db()`가 호출되는 점과 rollback 시 `rollback_to(target_ep)`가 호출되는 점은 검증하지만, 두 경로를 연결한 "save -> rollback -> restart -> reload" 체인은 없다.
   - ad hoc verification:
     - 저장된 감정 이력 `[(1, neutral), (5, triumph)]` 상태에서 live tracker에 `rollback_to(3)`를 적용하면 메모리는 `[(1, neutral)]`로 줄었다.
     - 같은 저장소로 새 tracker를 만들어 `load_from_db()`를 수행하면 `(5, triumph)`가 다시 로드됐다.
7. 기존 문서와의 중복 여부
   - `duplicate status`: `related-but-new-runtime-lifecycle-surface`
   - `MCP-T2`는 `_load_v50_history()` no-op을 coverage gap으로 남겼고, `MDH-T4`는 `_load_v50_history()` dormant / `_ignite_quad_cache_system()` dead를 분류했다.
   - 이번 finding은 helper 상태 분류가 아니라, destructive recovery 이후 next boot에서 감정 이력이 재오염되는 확정 lifecycle drift다.
8. 권장 후속 조치
   - destructive op 성공 후 `emotion_tracker.history`를 DB에 재저장하거나 `emotion_history` anchor를 타깃 기준으로 삭제/재작성한다.
   - `DBManager.reset_after()`가 관리해야 할 history anchors를 명시적으로 포함시키거나, `emotion_history`를 anchors 정책에 등록된 별도 persistence surface로 승격한다.
   - 회귀 테스트를 추가한다.
     - `save_to_db -> rollback_episode/reset_stage_2/wipe_production_data -> restart(load_from_db)` 후 미래 감정 이력이 재등장하지 않아야 한다.

---

## [MRL-T2-002] P2 | cache/history restore의 live authority가 분산돼 lifecycle graph가 하나로 잠기지 않는다

1. ID
   - `MRL-T2-002`
2. Severity
   - `P2`
3. 현상 요약
   - 코드상 nominal helper는 `_ignite_quad_cache_system()`과 `_load_v50_history()`지만, 실제 live recovery는 이 helper들이 담당하지 않는다.
   - `sys_caches`는 dead helper 안에만 있고, `_load_v50_history()`는 no-op stub이며, 실제 boot restore는 `_init_v50_modules()` 내부 inline DB load로 수행된다.
   - destructive-op 이후에도 `ProjectService._restore_runtime_state()`는 emotion/state_delta/preset만 만지고, `main_a.py` thin wrapper는 다시 foreshadow와 agent manuscript caches를 ad hoc으로 맞춘다.
   - 결과적으로 boot, destructive-op, next-boot가 같은 cache/history restore entrypoint를 공유하지 않는다.
4. 코드 근거
   - `sys_caches` read/write와 cache injection은 `_ignite_quad_cache_system()` 안에만 있고, repo 전역 caller가 없다.
     - `main_a.py:1193-1335`
     - `main_a.py:1040-1160` boot path에는 `_ignite_quad_cache_system()` 호출이 없다.
     - 기존 dead 판정: `docs/2026-03-13/MDH-T4-bootstrap-history-cache-helper-liveness-findings.md`
   - `_init_v50_modules()`는 failure learner, character voice, foreshadow, emotion tracker를 직접 DB/JSON에서 복원한다.
     - `main_a.py:1637-1828`
   - 그 직후 호출되는 `_load_v50_history()`는 deleted V50 modules에 대한 no-op stub이다.
     - `main_a.py:1956`
     - `main_a.py:2128-2140`
   - destructive-op 공통 restore helper는 world_state, fact_ledger, emotion_tracker, state_delta_tracker, preset registry만 다룬다.
     - `modules/core/services/project_service.py:63-96`
   - destructive-op thin wrapper는 다시 writer/director cache invalidation과 foreshadow reload/save를 별도 수행한다.
     - `main_a.py:3155-3285`
   - 즉 cache/history restore authority가 `_ignite_quad_cache_system()` / `_load_v50_history()` / `_init_v50_modules()` / destructive-op wrapper로 쪼개져 있다.
5. downstream 영향 경계
   - lifecycle graph 관점에서 "어떤 cache/history surface가 boot에서 복원되고, rollback/wipe 후 어떻게 정리되며, next boot에서 무엇이 다시 살아나는지"를 한 함수/테스트 집합으로 설명할 수 없다.
   - partial remediation이 한 경로만 고치고 다른 경로를 남길 가능성이 높다. 실제로 foreshadow는 rollback 후 DB reload가 있는데, emotion history는 next-boot sync가 없고, `sys_caches`는 아예 recovery graph 바깥에 있다.
   - `sys_caches` anchor가 남아 있어도 boot/recovery가 이를 authoritative state로 취급하지 않으므로, cache anchor는 lifecycle graph 안에서 실질적 계약이 없다.
6. 현재 테스트 근거 또는 테스트 부재
   - 실행 검증: `pytest ...` 총 `52 passed`.
   - `tests/test_stage_transition.py`는 Stage2→app `state_tracker` 동기화만 재현한다. cache/history restore는 범위 밖이다.
   - `tests/test_project_service.py`는 destructive-op의 SQL/파일/vector 경계만 확인하고, `sys_caches`, `_load_v50_history()`, boot inline history restore authority는 검증하지 않는다.
   - `tests/property/test_db_rollback_props.py`와 `tests/chaos/test_partial_commit.py`는 emotion/state_delta warning invariant만 본다.
   - `tests/integration/test_patch_wiring.py`는 `emotion_tracker.save_to_db()`, `emotion_tracker.rollback_to()`, `state_delta_tracker.rollback_to()` wiring은 보지만, unified cache/history restore entrypoint는 전혀 검증하지 않는다.
7. 기존 문서와의 중복 여부
   - `duplicate status`: `related-but-new-runtime-lifecycle-surface`
   - `MCP-T2`는 `_ignite_quad_cache_system()` dead와 `_load_v50_history()` no-op을 control-plane coverage gap으로 남겼다.
   - `MDH-T4`는 helper liveness를 dead/dormant로 분류했다.
   - 이번 finding은 그 둘을 재오픈하는 것이 아니라, live recovery authority가 helper 밖으로 분산되어 runtime lifecycle graph 자체가 하나의 SSOT로 잠기지 않는다는 점을 확정한다.
8. 권장 후속 조치
   - cache/history restore의 단일 authority를 정한다.
     - `sys_caches`가 레거시면 삭제하고 lifecycle claim에서 제거
     - live surface라면 boot/destructive-op/next-boot가 같은 helper를 호출하도록 수렴
   - `_load_v50_history()`를 실제 restore coordinator로 되살리거나, 반대로 inline restore를 정식 SSOT로 승격하고 stub helper를 제거한다.
   - 회귀 테스트를 추가한다.
     - `rollback/reset/wipe -> restart` 후 emotion/foreshadow/cache surface가 같은 정책으로 복원되는지
     - `boot`와 destructive-op path가 같은 restore helper contract를 공유하는지

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `sys_caches` 실제 운영 필요성 | 불명 | 현재 제품 경로에서 quad-cache가 정말 필요한지, 아니면 완전 레거시인지 결정 |
| `_load_v50_history()` 존치 목적 | 불명 | V65 삭제 모듈 재연결 계획이 있는지, 없으면 stub 제거 가능 여부 |
| next-boot rollback regression | 테스트 부재 | `save -> destructive op -> restart -> reload` 형태의 end-to-end test |
| anchor policy vs `emotion_history` | 정책 drift | anchors SSOT에 `emotion_history`를 등록할지, 별도 테이블/별도 helper로 이동할지 결정 |

## 마감 체크

- cache anchor 저장 실패 / restore no-op / next-boot drift 경계: yes
- 코드 근거 / 테스트 근거 / 중복 여부 / 후속 조치: yes
- PASS1 후보 -> PASS2 제거 -> PASS3 확정 요약: yes

## 최종 판정

- 최종 retained finding: `2건`
  - `P0`: 0건
  - `P1`: 1건
  - `P2`: 1건
  - `P3`: 0건
- PASS1 후보 -> PASS2 제거 -> PASS3 확정
  - `PASS1 4 -> PASS2 remove 2 -> FINAL 2`
