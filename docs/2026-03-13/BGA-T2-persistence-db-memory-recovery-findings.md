# [BGA-T2] Persistence / DB / Memory / Recovery Findings

> 작성일: 2026-03-13
> 상태: `PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / artifact-proof cross-check / UTF-8 only`
> 기준 오더: `backend-global-full-survey-master-audit-order.md`
> 실행 요약: `PASS1 후보 5건 -> PASS2 제거 2건 -> PASS3 확정 3건`

---

## 조사 범위

- `main_a.py`
  - `_reset_stage_2()`
  - `_rewind_stage_2()`
  - `_rollback_episode()`
  - `_wipe_production_data()`
  - boot / shutdown의 tracker load-save 경로
- `modules/core/services/project_service.py`
- `modules/core/db_manager.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/emotion_tracker.py`
- `modules/core/state_delta_tracker.py`
- `modules/domain/agents/base_agent.py`

## 필수 근거

- 읽은 테스트:
  - `tests/test_project_service.py`
  - `tests/test_main_a_rollback.py`
  - `tests/integration/test_patch_wiring.py`
  - `tests/test_db_manager.py`
  - `tests/test_db_integrity_recovery.py`
  - `tests/test_state_service.py`
  - `tests/property/test_db_rollback_props.py`
  - `tests/property/test_rollback_props.py`
  - `tests/chaos/test_partial_commit.py`
  - `tests/chaos/test_rollback_boundary.py`
  - `tests/test_main_a_persistence_helpers.py`
- 읽은 참조 문서:
  - `docs/2026-03-13/main_a-persistence-narrative-detail-consolidated-findings.md`
  - `docs/2026-03-13/main_a-runtime-recovery-lifecycle-detail-consolidated-findings.md`
  - `docs/2026-03-13/XC-DB-consolidated-findings.md`
  - `docs/2026-03-13/XC-MEM-consolidated-findings.md`
  - `docs/2026-03-13/XC-ERR-consolidated-findings.md`
- 실행 검증:
  - `pytest -q tests/test_project_service.py tests/test_main_a_rollback.py tests/integration/test_patch_wiring.py tests/test_db_manager.py tests/test_db_integrity_recovery.py`
  - 결과: `60 passed in 3.07s`
  - `pytest -q tests/property/test_db_rollback_props.py tests/property/test_rollback_props.py tests/chaos/test_partial_commit.py tests/chaos/test_rollback_boundary.py`
  - 결과: `44 passed in 7.43s`
  - `pytest -q tests/test_state_service.py`
  - 결과: `41 passed in 1.82s`
  - `pytest -q tests/test_main_a_persistence_helpers.py`
  - 결과: `collection error - Stage4Context __slots__ conflicts with class variable`
- 정적 교차 검증:
  - `project_service.py`의 destructive op success path와 `_restore_runtime_state()` 반환 계약 비교
  - `db_manager.py::reset_after()` 삭제 범위와 anchor/tracker persistence 표면 비교
  - `main_a.py` boot / shutdown의 `emotion_history` load-save 경로와 destructive op 경로 비교
  - `base_agent.py` global context cache lifecycle와 destructive op invalidation 범위 비교

## PASS 기록

- PASS 1:
  - 후보 1: destructive op 성공 판정이 runtime restore 성공과 여전히 분리돼 있는가
  - 후보 2: `emotion_history` anchor가 rollback/reset/wipe 뒤 next-boot 오염을 다시 주입하는가
  - 후보 3: destructive op 이후 `BaseAgent._context_caches`가 살아남는가
  - 후보 4: `_safe_commit()` false 경로에서 미커밋 트랜잭션이 여전히 유령처럼 남는가
  - 후보 5: `EmotionArcTracker` / `StateDeltaTracker` 자체 rollback semantics가 target ep 이후 데이터를 남기는가
- PASS 2:
  - 후보 4 제거: 현재 `ProjectService`는 `_safe_commit()` false 경로마다 `_rollback_open_transaction(project)`를 호출한다. 구 `XC-ERR-016` 유령 트랜잭션 패턴은 이 경로 기준 재현되지 않았다.
  - 후보 5 제거: `EmotionArcTracker.rollback_to()`와 `StateDeltaTracker.rollback_to()`의 `< target_ep` semantics는 현재 코드와 property/chaos 테스트에서 잠겨 있다. 남아 있는 문제는 tracker core trim이 아니라 persistence/restore proof surface다.
- PASS 3:
  - 확정 3건만 `BGA-T2-*`로 채택

## Finding Ledger

| ID | Severity | 상태 | 파일/함수 | 요약 |
|----|----------|------|-----------|------|
| `BGA-T2-001` | `P1` | confirmed | `modules/core/services/project_service.py::_restore_runtime_state()`, destructive op 4종 | destructive op이 DB/파일 삭제 후 runtime restore soft-failure를 성공처럼 통과시킨다 |
| `BGA-T2-002` | `P2` | confirmed | `project_service.py`, `db_manager.py::reset_after()`, `emotion_tracker.py`, `main_a.py` boot/shutdown | `emotion_history` anchor가 destructive op 직후 즉시 정리되지 않아 next-boot 오염 창이 남는다 |
| `BGA-T2-003` | `P2` | confirmed | `main_a.py` destructive op wrappers, `modules/domain/agents/base_agent.py` | destructive op cache invalidation이 `BaseAgent._context_caches`를 비우지 않아 global Gemini context cache가 남는다 |

## Final Findings

### [BGA-T2-001] P1 - destructive op이 runtime restore soft-failure를 성공처럼 닫는다

1. ID
   - `BGA-T2-001`
2. Severity
   - `P1`
3. 현상 요약
   - `reset_stage_2()`, `rewind_stage_2()`, `rollback_episode()`, `wipe_production_data()`는 DB reset과 draft/vector 삭제를 끝낸 뒤 `_restore_runtime_state()`를 호출하고 즉시 성공 로그와 `True`를 반환한다.
   - 그런데 `_restore_runtime_state()`는 `world_state.rollback_to()`, `fact_ledger.rollback_to()`, `preset_registry` restore 실패를 모두 UI log만 남기고 무시한다.
   - 반대로 `_assert_rollback_invariants()`는 `EmotionArcTracker`와 `StateDeltaTracker`만 경고 대상으로 본다. `world_state`, `fact_ledger`, preset restore 실패는 success verdict를 뒤집지 못한다.
   - 결과적으로 destructive op은 이미 DB/파일/vector 상태를 지운 뒤, runtime restore가 부분 실패해도 operator에게 성공처럼 닫힐 수 있다.
4. 코드 근거
   - `modules/core/services/project_service.py:70-98`에서 `world_state`, `fact_ledger`, `preset_registry` restore 실패는 예외를 삼키고 로그만 남긴다.
   - 같은 함수의 `modules/core/services/project_service.py:84-92`는 tracker rollback은 예외 보호 없이 그대로 호출한다. restore 계층 내부에서도 failure semantics가 일관되지 않다.
   - `modules/core/services/project_service.py:208-211`, `modules/core/services/project_service.py:277-280`, `modules/core/services/project_service.py:367-371`은 `_restore_runtime_state()` 직후 성공 메시지와 `True`를 반환한다.
   - `modules/core/services/project_service.py:377-397`의 invariant check는 emotion/state_delta만 검사하고 `world_state` / `fact_ledger` / preset restore는 보지 않는다.
5. downstream 영향 경계
   - rollback / rewind / wipe / reset 전체 destructive op surface
   - 다음 Stage 2/3/4 재생산 시 읽히는 runtime memory view
   - operator가 신뢰하는 success/failure 로그 의미
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_project_service.py:71-87`, `tests/test_project_service.py:127-146`, `tests/test_project_service.py:192-229`, `tests/test_project_service.py:263-278`은 DB reset, anchor 삭제, memory delete 호출과 success surface만 잠근다.
   - `tests/property/test_db_rollback_props.py:1-12`, `tests/property/test_db_rollback_props.py:150-194`, `tests/chaos/test_partial_commit.py:1-32`는 `_assert_rollback_invariants()`가 emotion/state_delta warning을 내는지만 본다.
   - 현재 회귀망에는 `world_state.rollback_to()` 실패, `fact_ledger.rollback_to()` 실패, `preset_registry` restore 실패가 return value나 success log를 바꾸는지 검증하는 테스트가 없다.
7. 기존 문서와의 중복 여부
   - `cross-track-confirmed`
   - `MRL-T4-002`, `XC-MEM-T3-001`, `XC-MEM-T3-002`, `XC-ERR-017~020`과 관련되지만, 이번 finding은 이를 destructive op success contract 관점에서 한 항목으로 재구성한 전역 T2 SSOT다.
8. 권장 후속 조치
   - `_restore_runtime_state()`가 structured result를 반환하게 하고, destructive op은 최소한 `hard failure`, `soft failure`, `success`를 구분해 닫아야 한다.
   - `world_state`, `fact_ledger`, preset restore 상태를 invariant 검증에 포함해야 한다.
   - failure-path 회귀 테스트를 추가해야 한다: `rollback_to raise -> success 금지 or degraded-success 명시`.

### [BGA-T2-002] P2 - `emotion_history` anchor가 destructive op 직후 즉시 정리되지 않아 next-boot 오염 창이 남는다

1. ID
   - `BGA-T2-002`
2. Severity
   - `P2`
3. 현상 요약
   - destructive op 경로는 현재 프로세스 메모리의 `EmotionArcTracker`만 `rollback_to(target_ep)`로 잘라낸다.
   - 하지만 DB 쪽 `emotion_history` anchor는 `reset_after()` 대상이 아니고, destructive op 직후에도 다시 저장되지 않는다.
   - boot에서는 `emotion_history`를 DB anchor에서 재로드하고, save는 정상 종료 시점에만 일어난다.
   - 따라서 destructive op 직후 비정상 종료, 재시작 전 crash, save-before-exit 우회가 발생하면 stale future emotion history가 다음 boot에 다시 주입될 수 있다.
4. 코드 근거
   - `modules/core/services/project_service.py:84-87`은 destructive op restore에서 emotion tracker를 in-memory rollback만 한다.
   - `modules/core/db_manager.py:2289-2329`의 `reset_after()` 삭제 목록에는 `anchors WHERE key = 'emotion_history'` 또는 동등한 정리 경로가 없다.
   - `modules/core/emotion_tracker.py:382`는 emotion history를 `save_anchor("emotion_history", ...)`로 저장하고, `modules/core/emotion_tracker.py:391`은 같은 anchor를 로드한다.
   - `main_a.py:1828-1833`은 boot 시 `self.emotion_tracker.load_from_db(self.current_project.db)`를 호출하고, `main_a.py:2554-2558`은 종료 시점에만 `save_to_db()`를 호출한다.
5. downstream 영향 경계
   - destructive recovery 이후 next-boot state reconstruction
   - Stage 4 continuity / advisory가 참조하는 emotion timeline
   - operator가 기대하는 "rollback 후 같은 프로젝트 재부팅" 의미
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_project_service.py:71-87`, `tests/test_project_service.py:192-229`, `tests/test_project_service.py:263-278`은 destructive op 이후 `emotion_history` anchor contents를 확인하지 않는다.
   - `tests/test_main_a_rollback.py:51-108`, `tests/test_main_a_rollback.py:111-150`은 local cache reset과 foreshadow sync만 확인하고 emotion tracker persistence는 다루지 않는다.
   - 현재 회귀망에는 `rollback/reset/wipe -> restart -> emotion_history 재로드` 시나리오를 잠그는 테스트가 없다.
7. 기존 문서와의 중복 여부
   - `cross-track-confirmed`
   - `MRL-T2-001`의 next-boot contamination 우려를 현재 코드 기준 anchor-level evidence로 재확인했다.
8. 권장 후속 조치
   - destructive op 성공 직후 `emotion_history` anchor를 즉시 저장하거나 삭제해야 한다.
   - `next boot after rollback/reset/wipe` 회귀 테스트를 추가해야 한다.
   - shutdown save에만 의존하는 tracker persistence는 recovery contract와 분리해서 검토해야 한다.

### [BGA-T2-003] P2 - destructive op cache invalidation이 `BaseAgent._context_caches`를 비우지 않는다

1. ID
   - `BGA-T2-003`
2. Severity
   - `P2`
3. 현상 요약
   - `BaseAgent`는 프로젝트명과 `content_hash` 기반으로 Gemini context cache를 전역 dict `_context_caches`에 유지한다.
   - project environment를 다시 로드할 때는 이 global cache를 명시적으로 비운다.
   - 그런데 rollback/reset/rewind/wipe 성공 후 wrapper는 writer/director/state extractor cache와 foreshadow만 정리하고, `BaseAgent._context_caches`는 건드리지 않는다.
   - content hash가 자연 방어막 역할을 하긴 하지만, destructive op 직후 유사 컨텍스트 재생성이나 TTL window에서는 stale remote cache 재사용 가능성이 남는다.
4. 코드 근거
   - `modules/domain/agents/base_agent.py:1765-1807`은 cache key가 `cache_type + project_name + content_hash`이고 TTL 내 HIT를 허용함을 보여 준다.
   - `main_a.py:1044-1048`은 project env reload 시 `BaseAgent._context_caches.clear()`를 명시적으로 호출한다.
   - 반면 destructive op wrapper인 `main_a.py:3229-3254`, `main_a.py:3260-3286`, `main_a.py:3291-3326`, `main_a.py:3331-3355`는 local cache invalidation과 foreshadow sync만 수행하고 `BaseAgent` global cache는 비우지 않는다.
5. downstream 영향 경계
   - writer/director 계열 Gemini cached context 재사용 경로
   - destructive op 이후 같은 프로젝트에서 곧바로 이어지는 재생산 흐름
   - operator가 기대하는 "wipe/reset 후 fresh context" 의미
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_main_a_boot_binding.py:63-87`은 project environment reload 시 `BaseAgent._context_caches == {}`를 검증한다.
   - `tests/test_main_a_rollback.py:51-108`은 destructive op 후 `_prompt_builder`, writer, director, state_extractor, foreshadow만 검증한다.
   - destructive op 후 `BaseAgent._context_caches`가 cleared 되는지 검증하는 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `related-but-promoted`
   - `XC-MEM-T2-001`이 cache invalidation 누락을 지적했지만, 이번 finding은 이를 backend-wide destructive lifecycle contract로 승격해 기록한다.
8. 권장 후속 조치
   - destructive op 성공 후 `BaseAgent._context_caches.clear()` 또는 동등한 invalidate API를 호출해야 한다.
   - `rollback/reset/wipe -> BaseAgent cache cleared` 회귀 테스트를 추가해야 한다.
   - cache invalidation 정책을 project switch와 destructive recovery에서 동일 SSOT로 잠가야 한다.

## Rejected Candidates

| 후보 | PASS2 판정 | 근거 |
|------|------------|------|
| `_safe_commit()` false 경로가 아직 미커밋 트랜잭션을 남긴다 | removed | `modules/core/services/project_service.py:190-193`, `modules/core/services/project_service.py:254-257`, `modules/core/services/project_service.py:346-349`, `modules/core/services/project_service.py:412-414`에서 `_rollback_open_transaction(project)`가 명시적으로 호출된다. `tests/test_project_service.py:89-100`, `tests/test_project_service.py:148-165`, `tests/test_project_service.py:231-250`, `tests/test_project_service.py:280-295`도 이 경로를 잠근다. |
| tracker core rollback semantics 자체가 future episode를 남긴다 | removed | `modules/core/emotion_tracker.py`와 `modules/core/state_delta_tracker.py`의 `rollback_to()`는 `< target_ep` semantics를 사용한다. `tests/property/test_rollback_props.py`와 `tests/chaos/test_rollback_boundary.py`가 strict boundary를 green으로 고정한다. 문제는 core trim이 아니라 destructive op 후 persistence/proof lifecycle이다. |

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `world_state` / `fact_ledger` / preset restore failure-path | 테스트 공백 | `rollback_to()` 또는 preset restore 예외 주입 후 success verdict와 log semantics를 확인하는 테스트 |
| destructive op 후 next boot emotion history | 테스트 공백 | `rollback/reset/wipe -> process restart -> emotion_history reload` 회귀 테스트 |
| destructive op 후 `BaseAgent._context_caches` | 테스트 공백 | destructive op wrapper가 global cache를 비우는지 직접 검증하는 테스트 |
| `tests/test_main_a_persistence_helpers.py` | collection blocker | 현재 workspace에서 `Stage4Context __slots__ conflicts with class variable`로 수집이 막힌다. 코드 수정 금지 조건 때문에 이번 조사에서는 blocker로만 기록한다. |

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- `PASS1 -> PASS2 -> PASS3` 요약 포함
