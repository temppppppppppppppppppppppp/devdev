# [MLW-T1] Stage2 Real-App Binding Findings

> 작성일: 2026-03-13
> 작성자: `Claude Opus`
> 상태: `PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-live-wiring-contract-detail-full-survey-audit-order.md`
> 실행 요약: `PASS1 후보 9건 -> PASS2 제거 3건 (기존 문서 중복 2건 + 비해당 1건) -> 최종 6건`

---

## 조사 범위

- `main_a.py`
  - Stage2에 export하는 bound method 전반
  - Stage2 진입점 3곳: `_stage_2_arcs()` L2633, OneStop Stage2 L3672, OneStop Stage2 L3918
- 직접 downstream
  - `modules/core/stage2_context.py` (48 __slots__)
  - `modules/core/stage2_orchestrator.py` (907줄)
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_finalizer.py`
  - `modules/core/stage2_preflight.py`

## 필수 근거

- 읽은 테스트:
  - `tests/test_stage2_context.py`
  - `tests/test_stage2_validation_pipeline.py`
- 읽은 참조 문서:
  - `docs/2026-03-13/MRF-T1-stage2-callback-binding-findings.md`

---

## PASS 기록

### PASS 1 - 표면 수집 (후보 9건)

| # | 확신도 | 현상 | 비고 |
|---|--------|------|------|
| 1 | HIGH | `cumulative_state_cache` finalizer→app sync gap | P3 candidate |
| 2 | MED | `calculate_arc_from_episode` 무가드 호출 | P2 candidate |
| 3 | MED | `session_logger` Stage2 consumer 미사용 dead slot | P3 candidate |
| 4 | LOW | docstring 슬롯 카운트 drift (21종→23, 18종→20) | P3 candidate |
| 5 | MED | spec-less MagicMock이 app surface drift 은폐 | P2 candidate |
| 6 | LOW | `state_tracker_loaded_arcs` 양방향 데이터 채널 패턴 | P3 candidate |
| 7 | LOW | 3개 Stage2 진입점이 write-back 패턴을 각각 복제 | P3 candidate |
| 8 | HIGH | `analyze_rejection_pattern_v60` 무가드 호출 | duplicate candidate (MRF-T1-001) |
| 9 | MED | callback bundle fallback 규약 불일치 | duplicate candidate (MRF-T1-002) |

### PASS 2 - 교차 검증

- 후보 8 제거: `already-covered-do-not-reopen`. MRF-T1-001이 동일 surface를 P1으로 확정 완료.
- 후보 9 제거: `already-covered-do-not-reopen`. MRF-T1-002가 동일 surface를 P2로 확정 완료.
- 후보 7 병합: 3개 진입점 모두 동일 write-back 패턴을 정확히 복제하고 있어 현재 drift 없음. Finding 6과 병합하여 P3으로 통합.

### PASS 3 - 최종 확정 (6건)

- MLW-T1-001 ~ MLW-T1-006 채택.

---

## Finding Ledger

| ID | Severity | 상태 | 파일/함수 | 요약 |
|----|----------|------|-----------|------|
| MLW-T1-001 | P2 | confirmed | `stage2_orchestrator.py:224` | `calculate_arc_from_episode` 무가드 호출 — `get_max_episode_from_manuscripts` callable 여부에 간접 의존하지만 명시적 guard 부재 |
| MLW-T1-002 | P2 | confirmed | `tests/test_stage2_context.py`, `tests/test_stage2_validation_pipeline.py` | spec-less `MagicMock`이 real-app surface drift를 은폐 — SovereignApp rename/삭제를 감지 불가 |
| MLW-T1-003 | P3 | confirmed | `stage2_finalizer.py:1125-1126`, `stage2_context.py:257` | `cumulative_state_cache` finalizer reset이 ctx만 초기화하고 app에 sync하지 않음 (정합성 영향 없음 — orchestrator top-of-run reset이 보호) |
| MLW-T1-004 | P3 | confirmed | `stage2_context.py:81,97`, `stage2_orchestrator.py:201`, `main_a.py:2661` | `state_tracker_loaded_arcs`와 `cumulative_state_cache`/`key`가 callback이 아닌 양방향 mutable data 채널로 사용됨 |
| MLW-T1-005 | P3 | confirmed | `stage2_context.py:99` | `session_logger` 슬롯이 Stage2 consumer 어디에서도 읽히지 않는 dead slot |
| MLW-T1-006 | P3 | confirmed | `stage2_context.py:22-44` | docstring 슬롯 카운트 drift — "확장 18종" 실제 20 (context_advisor, adversarial_self_play 누락), "콜백 21종" 실제 23 (sync_cache_key_to_app, session_logger 누락) |

---

## Final Findings

### [MLW-T1-001] P2 — `calculate_arc_from_episode` 무가드 호출

1. ID
   - `MLW-T1-001`
2. Severity
   - `P2`
3. 현상 요약
   - `Stage2Orchestrator.stage_2_arcs_async_logic()` L224에서 `self.ctx.calculate_arc_from_episode(existing_ms_max_ep)`를 `callable()` guard 없이 직접 호출한다.
   - 이 호출은 `existing_ms_max_ep > 0` 조건 안에 있으며, 이 조건은 `get_max_episode_from_manuscripts()`가 callable이어야 참이 된다.
   - 두 callback은 동일 `from_app()` 호출에서 같은 app 객체로부터 추출되므로, 한쪽이 있으면 다른 쪽도 있을 가능성이 높다.
   - 그러나 `Stage2Context`는 두 callback 모두 optional (`None` 기본값)이므로, manual injection 시 한쪽만 설정하면 crash 가능.
4. 코드 근거
   - `modules/core/stage2_orchestrator.py:218-224` — `get_max_episode_from_manuscripts`는 L220에서 `callable(getattr(...))` guard, `calculate_arc_from_episode`는 L224에서 무가드
   - `modules/core/stage2_context.py:144,148` — 둘 다 `=None` 기본값
   - `modules/core/stage2_context.py:244,250` — 둘 다 `getattr(app, "_...", None)`
5. downstream 영향 경계
   - `calculate_arc_from_episode`가 None이면 `TypeError: 'NoneType' is not callable` → smart skip 로직에서 crash
   - 이 crash는 Stage2 전체를 중단시킨다 (Arc 설계 루프 진입 전 crash)
   - 실제 운영에서는 `from_app()`이 항상 real app에서 추출하므로 발생 확률은 매우 낮다
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage2_context.py:128-139`는 callback 없는 app에서 `from_app()` 동작만 확인
   - `calculate_arc_from_episode` 부재 + `get_max_episode_from_manuscripts` 존재 조합은 테스트 없음
7. 기존 문서와의 중복 여부
   - `related-but-new-live-wiring-surface`
   - MRF-T1-001은 `analyze_rejection_pattern_v60` 무가드를 다뤘다. 이 항목은 같은 패턴의 다른 callback에 대한 finding.
8. 권장 후속 조치
   - L224에 `callable(getattr(self.ctx, "calculate_arc_from_episode", None))` guard 추가 또는 `calculate_arc_from_episode`가 None이면 skip 처리

---

### [MLW-T1-002] P2 — spec-less MagicMock이 real-app surface drift를 은폐

1. ID
   - `MLW-T1-002`
2. Severity
   - `P2`
3. 현상 요약
   - Stage2 관련 테스트 전반에서 `MagicMock()` (spec 미지정)을 사용해 app 및 ctx를 생성한다.
   - spec 없는 MagicMock은 존재하지 않는 attribute에 접근해도 자동으로 새 MagicMock을 반환한다.
   - 따라서 `SovereignApp`에서 callback 이름이 변경/삭제되어도 테스트는 계속 초록이다.
   - `from_app()` 자체가 `getattr(app, "_xxx", None)` 패턴이라 MagicMock에서는 항상 auto-created MagicMock(truthy)을 반환하여, 실제 app에서 None이 될 slot도 테스트에서는 truthy로 동작한다.
4. 코드 근거
   - `tests/test_stage2_context.py:32-33` — `app = MagicMock()` spec 없음
   - `tests/test_stage2_context.py:91-106` — 6개 callback만 수동 설정, 나머지 17개는 MagicMock auto-attribute
   - `tests/test_stage2_context.py:128-139` — `MagicMock(spec=[])` 사용이 유일하지만 callback 부재만 확인
   - `tests/test_stage2_validation_pipeline.py:13-16` — `app = MagicMock()`, `ctx = MagicMock()` 둘 다 spec 없음
5. downstream 영향 경계
   - `SovereignApp`에서 `_generate_structured_arc_feedback` → `_generate_arc_feedback`으로 rename하면, `from_app()`은 `getattr(app, "_generate_structured_arc_feedback", None)` → None을 반환하지만, 테스트에서는 MagicMock auto-attribute가 truthy MagicMock을 반환하여 테스트 초록 유지
   - 실제 파이프라인에서는 해당 callback이 None이 되어 silent degradation 또는 crash 발생
6. 현재 테스트 근거 또는 테스트 부재
   - `from_app()` + real SovereignApp surface를 비교하는 contract regression test 없음
   - `spec=SovereignApp` 또는 attribute 화이트리스트 기반 fixture 없음
7. 기존 문서와의 중복 여부
   - `related-but-new-live-wiring-surface`
   - MRF-T1-002가 callback fallback 불일치를 다뤘으나, spec-less MagicMock이 surface drift를 은폐한다는 테스트 realism 자체는 다루지 않았다
   - MPN-T5, MFS-T5 문서들이 유사 주제를 다룰 수 있으나 T5 전담이므로 본 T1에서는 Stage2 한정으로 기록
8. 권장 후속 조치
   - `app_mock` fixture에 `spec=SovereignApp` 또는 명시적 attribute 화이트리스트를 적용
   - `from_app()` contract test: `from_app(real_app)` 결과에서 모든 callback 슬롯이 callable인지 확인하는 regression 추가
   - 최소한 `test_from_app_missing_callbacks_none`을 확장하여 23개 콜백 전량 확인

---

### [MLW-T1-003] P3 — `cumulative_state_cache` finalizer→app sync gap

1. ID
   - `MLW-T1-003`
2. Severity
   - `P3`
3. 현상 요약
   - `Stage2Finalizer.run_finalize()`는 Arc PASS 후 `self.ctx.cumulative_state_cache = None`, `self.ctx.cumulative_state_cache_key = None` (L1125-1126)으로 ctx를 리셋한다.
   - `Stage2Preflight`는 캐시 설정 시 `sync_cache_key_to_app` 콜백을 호출하여 app에도 동기화한다 (L669-670).
   - 그러나 finalizer는 reset 시 `sync_cache_key_to_app`을 호출하지 않는다. 따라서 app 측 캐시는 stale 상태로 남는다.
   - 정합성 영향 없음: `Stage2Orchestrator.stage_2_arcs_async_logic()` L263-264에서 매 실행 시작 시 ctx 캐시를 명시적으로 None으로 리셋하므로, `from_app()`이 stale 데이터를 주입해도 즉시 덮어쓴다.
4. 코드 근거
   - `modules/core/stage2_finalizer.py:1125-1126` — ctx reset only
   - `modules/core/stage2_preflight.py:669-670` — sync_cache_key_to_app 호출
   - `modules/core/stage2_orchestrator.py:263-264` — top-of-run reset (보호)
   - `modules/core/stage2_context.py:257` — `_make_sync_callback(weakref.ref(app))`
5. downstream 영향 경계
   - app 객체에 stale 캐시 데이터가 잔류하여 GC 대상에서 제외됨 (미미한 메모리 낭비)
   - 정합성 문제 없음 (orchestrator top-of-run reset이 보호)
6. 현재 테스트 근거 또는 테스트 부재
   - finalizer reset 후 app 측 캐시 상태를 검증하는 테스트 없음
7. 기존 문서와의 중복 여부
   - `none` — 신규 live wiring surface
8. 권장 후속 조치
   - finalizer L1125-1126 직후에 `sync_cache_key_to_app(None)` 호출 추가 (선택사항, 정합성 영향 없음)

---

### [MLW-T1-004] P3 — `state_tracker_loaded_arcs` 양방향 mutable data 채널

1. ID
   - `MLW-T1-004`
2. Severity
   - `P3`
3. 현상 요약
   - `Stage2Context`의 `state_tracker_loaded_arcs`, `cumulative_state_cache`, `cumulative_state_cache_key` 3개 슬롯은 callback(함수)이 아니라 **mutable data**로 사용된다.
   - Orchestrator가 이들을 ctx에 쓰고 (L201, L263-264), main_a.py가 Stage2 완료 후 ctx에서 읽어 app에 write-back한다 (L2661).
   - 이 패턴은 "callback slot" 이름 아래에 양방향 데이터 채널이 숨어 있는 설계로, 슬롯의 의미 경계가 흐려진다.
   - 3개 Stage2 진입점 (L2633, L3672, L3918) 모두 동일 write-back 패턴을 정확히 복제하고 있어 현재 drift 없음.
4. 코드 근거
   - `modules/core/stage2_orchestrator.py:201` — `self.ctx.state_tracker_loaded_arcs = len(all_refined_arcs)`
   - `main_a.py:2661,3699,3943` — `self._state_tracker_loaded_arcs = getattr(_s2_ctx, "state_tracker_loaded_arcs", 0)`
   - `modules/core/stage2_context.py:81` — slot 선언 (callback 섹션에 위치)
5. downstream 영향 경계
   - write-back 누락 시 `_state_tracker_loaded_arcs`가 동기화되지 않아 다음 Stage2 호출에서 StateTracker가 불필요하게 전체 리셋됨 (성능 영향)
   - 현재 모든 진입점이 write-back을 수행하므로 실제 영향 없음
6. 현재 테스트 근거 또는 테스트 부재
   - write-back 패턴을 검증하는 테스트 없음
7. 기존 문서와의 중복 여부
   - `none` — 신규 live wiring surface
8. 권장 후속 조치
   - 향후 신규 Stage2 진입점 추가 시 write-back 누락 주의 (관측성 목적 P3)

---

### [MLW-T1-005] P3 — `session_logger` Stage2 consumer 미사용 dead slot

1. ID
   - `MLW-T1-005`
2. Severity
   - `P3`
3. 현상 요약
   - `Stage2Context.__slots__`에 `session_logger` (L99)가 선언되어 있고, `from_app()`이 `getattr(app, "_session_logger", None)`으로 주입한다.
   - 그러나 `modules/core/stage2_orchestrator.py`, `stage2_validation_pipeline.py`, `stage2_finalizer.py`, `stage2_preflight.py` 어디에서도 `ctx.session_logger`를 읽지 않는다.
   - Stage4 consumer에서만 `ctx.session_logger`를 사용한다 (`stage4_interview_round.py`, `stage4_post_processor.py`).
4. 코드 근거
   - `modules/core/stage2_context.py:99` — slot 선언
   - `modules/core/stage2_context.py:258` — `from_app()` 주입
   - `grep ctx.session_logger modules/core/stage2_*.py` → 0 matches
5. downstream 영향 경계
   - 없음. dead slot이므로 동작에 영향 없음.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage2_context.py`에서 `session_logger` 검증 없음
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - Stage2에서 session logging이 필요하면 consumer 코드 추가, 불필요하면 slot 제거 (선택사항)

---

### [MLW-T1-006] P3 — Stage2Context docstring 슬롯 카운트 drift

1. ID
   - `MLW-T1-006`
2. Severity
   - `P3`
3. 현상 요약
   - Stage2Context 클래스 docstring (L22-44)에 기술된 슬롯 카운트가 실제 `__slots__`와 맞지 않는다.
   - docstring "확장 18종": 실제 20종 — `context_advisor` (L60)와 `adversarial_self_play` (L73)가 docstring에서 누락
   - docstring "콜백 21종": 실제 23종 — `sync_cache_key_to_app` (L97)와 `session_logger` (L99)가 docstring에서 누락
4. 코드 근거
   - `modules/core/stage2_context.py:22-44` — docstring
   - `modules/core/stage2_context.py:46-100` — `__slots__` 실제 선언
5. downstream 영향 경계
   - 없음. 문서 drift만.
6. 현재 테스트 근거 또는 테스트 부재
   - 해당 없음
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - docstring 카운트를 "확장 20종", "콜백 23종"으로 갱신하고 누락 항목을 리스트에 추가

---

## Rejected Candidates

| 후보 | PASS2 판정 | 근거 |
|------|------------|------|
| `analyze_rejection_pattern_v60` 무가드 호출 | `already-covered-do-not-reopen` | MRF-T1-001이 동일 surface를 P1으로 확정 완료 |
| callback bundle fallback 규약 불일치 | `already-covered-do-not-reopen` | MRF-T1-002가 동일 surface를 P2로 확정 완료 |
| 3개 Stage2 진입점 write-back 패턴 복제 | MLW-T1-004에 병합 | 현재 모든 진입점이 동일 패턴을 정확히 복제하고 있어 독립 finding 불필요 |

---

## Coverage Gaps / Open Questions

1. `Stage2Context.from_app()`이 **필수 5종** (`ui`, `current_project`, `agents`, `sys`)을 `getattr` 없이 직접 접근한다. 이는 app에 해당 속성이 없으면 `AttributeError`로 fail-fast하는 설계로, 의도된 contract이다. 단, `state_tracker`만 `getattr(app, "state_tracker", None)`으로 optional 처리되어 있어 "필수 5종"이라는 분류와 미세하게 어긋난다.
2. `Stage2Orchestrator.__init__`이 `self.app = app`을 유지하지만, 모든 consumer 코드(`stage2_validation_pipeline.py`, `stage2_finalizer.py`, `stage2_preflight.py`)는 `self.app`을 단 한 번도 참조하지 않는다. `self.app`은 오직 `ctx` property lazy build에서만 사용된다.

---

## PASS1 → PASS2 → PASS3 요약

- PASS1: 후보 9건 (HIGH 2, MED 4, LOW 3)
- PASS2: 기존 문서 중복 제거 2건 (MRF-T1-001/002), 병합 1건 → 잔여 6건
- PASS3: 확정 6건 (P2 2건, P3 4건, P0 0건, P1 0건)
- Severity 합계: **P0: 0, P1: 0, P2: 2, P3: 4**
