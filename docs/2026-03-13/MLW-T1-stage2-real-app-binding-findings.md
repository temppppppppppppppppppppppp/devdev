# [MLW-T1] Stage2 Real-App Binding Findings

> 작성일: 2026-03-13
> 작성자: `Codex`
> 상태: `PASS3 re-audited`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-live-wiring-contract-detail-full-survey-audit-order.md`
> 실행 요약: `PASS1 후보 8건 -> PASS2 제거 4건 (기존 문서 중복 1 + 오판 2 + coverage gap 1) -> 최종 4건`
> 메모: `기존 OPUS 초안을 전량 재검증했으며, 잘못된 항목 2건(session_logger dead slot, MagicMock auto-attribute 가정)을 폐기했다.`

---

## 조사 범위

- `main_a.py`
  - Stage2 진입점 3곳
    - `_stage_2_arcs()`
    - One-stop frontier lag 내부 Stage2 진입
    - One-stop frontier lag auto-continue 내부 Stage2 진입
- 직접 downstream
  - `modules/core/stage2_context.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage2_preflight.py`
  - `modules/core/stage2_validation_pipeline.py`
  - `modules/core/stage2_finalizer.py`

## 필수 근거

- 읽은 테스트
  - `tests/test_stage2_context.py`
  - `tests/test_stage2_validation_pipeline.py`
  - `tests/test_stage2_finalizer.py`
  - `tests/test_main_a_stage_entry_contracts.py`
  - `tests/test_one_stop_frontier_lag_auto_continue.py`
  - `tests/e2e/test_l3_stage2_realproject.py`
  - `tests/test_sweep3.py`
- 읽은 참조 문서
  - `docs/2026-03-13/MRF-T1-stage2-callback-binding-findings.md`
  - `docs/2026-03-13/MFS-T2-state-service-validation-findings.md`
  - `docs/2026-03-13/MLW-T5-test-realism-regression-findings.md`
- 실행 검증
  - `pytest -q tests/test_stage2_context.py tests/test_stage2_validation_pipeline.py tests/test_stage2_finalizer.py tests/test_main_a_stage_entry_contracts.py::test_stage2_wrapper_calls_resume_status_and_syncs_ctx_state tests/test_one_stop_frontier_lag_auto_continue.py tests/e2e/test_l3_stage2_realproject.py`
  - 결과: `67 passed, 5 skipped`
  - lightweight real-app 확인:
    - `SovereignApp.__new__(SovereignApp)`에 최소 필수 속성만 주입한 뒤 `Stage2Context.from_app()` 호출
    - 현재 코드 기준 핵심 callback 19종 + `sync_cache_key_to_app`가 모두 callable
    - `retry_feedback_missing_callbacks["required"] == []`

---

## PASS 기록

### PASS 1 - 표면 수집 (후보 8건)

| # | 확신도 | 현상 | 비고 |
|---|--------|------|------|
| 1 | HIGH | Stage2 real-app chain을 끝까지 태우는 회귀 테스트 부재 | P1 candidate |
| 2 | HIGH | `validate_arc_data_fields` repair hook가 real-app Stage2 graph에 미바인딩 | duplicate candidate (`MFS-T2-001`) |
| 3 | MED | `cumulative_state_cache` populate/clear live wiring 비대칭 | P3 candidate |
| 4 | MED | `state_tracker` / `_state_tracker_loaded_arcs` write-back 계약이 3개 진입점에 수동 복제 | P3 candidate |
| 5 | LOW | `session_logger` Stage2 dead slot | candidate |
| 6 | MED | `calculate_arc_from_episode` 무가드 호출 | coverage-gap candidate |
| 7 | MED | spec-less `MagicMock` auto-attribute가 missing callback을 truthy로 숨김 | candidate |
| 8 | LOW | `Stage2Context` 문서/테스트 메타데이터가 실제 슬롯 표면과 불일치 | P3 candidate |

### PASS 2 - 교차 검증

- 후보 2 제거: `already-covered-do-not-reopen`.
  - `docs/2026-03-13/MFS-T2-state-service-validation-findings.md`의 `[MFS-T2-001]`이 동일 표면을 이미 P1으로 닫고 있다.
- 후보 5 제거: `not-a-finding`.
  - `session_logger`는 `modules/core/stage2_orchestrator.py:690-699`와 `modules/core/stage2_finalizer.py:643-650`에서 실제 사용된다.
- 후보 6 축소: `coverage gap / open question`.
  - `modules/core/stage2_orchestrator.py:274-279`의 무가드 호출 자체는 남아 있지만, lightweight real-app 확인에서는 `_get_max_episode_from_manuscripts`와 `_calculate_arc_from_episode`가 모두 현재 `SovereignApp` 표면에 존재하고 callable이었다.
  - 즉시 real-app wiring mismatch가 아니라 manual ctx injection / partial host path의 방어 공백에 가깝다.
- 후보 7 제거: `incorrect-premise`.
  - `modules/core/stage2_context.py:61-71`의 `_safe_getattr()`는 `inspect.getattr_static()`로 missing attribute를 먼저 걸러낸다.
  - bare `MagicMock()`에 대해 직접 확인한 결과, 지정하지 않은 Stage2 slot은 truthy `MagicMock`이 아니라 `None`으로 들어간다.
  - 문제의 핵심은 auto-attribute 은닉이 아니라, **real `SovereignApp` bound method 체인을 실행하는 테스트가 없다는 점**이다.

### PASS 3 - 최종 확정 (4건)

- `MLW-T1-001` ~ `MLW-T1-004` 채택

---

## 현재 양성 확인

아래는 이번 재조사에서 명시적으로 확인한 `현재는 맞는 것`들이다.

- `Stage2Context.from_app()`와 `main_a.py`의 현재 Stage2 bound method 이름은 지금 시점 코드 기준으로는 어긋나지 않았다.
- lightweight real-app 확인에서 핵심 callback 19종 + `sync_cache_key_to_app`는 모두 callable이었다.
- `retry_feedback_missing_callbacks["required"] == []`였고, `optional_with_fallback`도 빈 리스트였다.
- 따라서 이번 문서의 핵심은 “현재 즉시 실패하는 name mismatch”가 아니라, **실제 Stage2 live wiring 계약이 테스트와 문서에서 어떻게 덜 잠겨 있는가**다.

---

## Finding Ledger

| ID | Severity | 상태 | 파일/함수 | 요약 |
|----|----------|------|-----------|------|
| MLW-T1-001 | P1 | confirmed | `main_a.py`, `tests/test_stage2_context.py`, `tests/test_main_a_stage_entry_contracts.py`, `tests/test_one_stop_frontier_lag_auto_continue.py`, `tests/e2e/test_l3_stage2_realproject.py` | 현재 테스트군은 `SovereignApp -> Stage2Context.from_app() -> Stage2 consumer` 실경로를 한 번도 끝까지 실행하지 않는다 |
| MLW-T1-002 | P3 | confirmed | `stage2_context.py`, `stage2_preflight.py`, `stage2_finalizer.py`, `main_a.py` | `cumulative_state_cache`는 populate 시 ctx->app으로 동기화되지만 clear 시에는 ctx만 지워져 live wiring이 비대칭이다 |
| MLW-T1-003 | P3 | confirmed | `main_a.py`, `stage2_orchestrator.py`, 관련 wrapper tests | `state_tracker` / `_state_tracker_loaded_arcs` write-back 계약이 Stage2 진입점 3곳에 수동 복제되어 있고 alternate path는 real context로 잠기지 않았다 |
| MLW-T1-004 | P3 | confirmed | `stage2_context.py`, `tests/integration/test_pipeline_smoke.py`, `tests/test_stage2_context.py` | `Stage2Context` 문서와 테스트 메타가 실제 50-slot 표면과 optionality를 따라가지 못해 audit confidence를 과장한다 |

---

## Final Findings

### [MLW-T1-001] P1 - Stage2 real-app binding chain을 실제로 태우는 회귀 테스트가 없다

1. ID
   - `MLW-T1-001`
2. Severity
   - `P1`
3. 현상 요약
   - `main_a.py`의 실제 production 경로는 `Stage2Context.from_app(self)`로 ctx를 만들고, 그 ctx가 `Stage2Orchestrator/Preflight/Validation/Finalizer`로 흘러간다.
   - 그런데 현재 테스트는 이 경로를 끝까지 잠그지 않는다.
   - `tests/test_stage2_context.py`는 `from_app()`를 `MagicMock()` 또는 ad-hoc object에 대해서만 검증한다.
   - `tests/test_main_a_stage_entry_contracts.py::test_stage2_wrapper_calls_resume_status_and_syncs_ctx_state`는 핵심 wrapper test인데, 정작 `Stage2Context.from_app`를 sentinel ctx로 monkeypatch해 실제 binding을 우회한다.
   - `tests/test_one_stop_frontier_lag_auto_continue.py`는 아예 `modules.core.stage2_context` 모듈을 fake module로 갈아끼우고 `from_app()`가 `SimpleNamespace(app=app)`만 반환하게 만든다.
   - `tests/e2e/test_l3_stage2_realproject.py`도 real DB smoke이지만 `Stage2Context(...)`를 수동 구성해 `Stage2Orchestrator`에 직접 주입한다.
   - 즉, Stage2 관련 테스트가 많아도 `SovereignApp bound method -> from_app -> live consumer` 체인은 비어 있다.
4. 코드 근거
   - `main_a.py:2685`, `main_a.py:3722`, `main_a.py:3965` — 세 Stage2 진입점 모두 `Stage2Context.from_app(self)` 사용
   - `tests/test_stage2_context.py:54-161` — `from_app()` 테스트 대상이 `MagicMock` 또는 synthetic app
   - `tests/test_main_a_stage_entry_contracts.py:93-115` — `Stage2Context.from_app` monkeypatch 후 sentinel ctx 주입
   - `tests/test_one_stop_frontier_lag_auto_continue.py:8-15` — fake `Stage2Context.from_app()`
   - `tests/test_one_stop_frontier_lag_auto_continue.py:103-106`, `191-194`, `237-240` — `patch.dict(sys.modules, {"modules.core.stage2_context": fake_stage2, ...})`
   - `tests/e2e/test_l3_stage2_realproject.py:205-225` — `Stage2Context(...)` 수동 조립
5. downstream 영향 경계
   - `_validate_arc_mapping`, `_validate_arc_integrity`, `_safe_commit_async`, `_get_max_episode_from_manuscripts`, `_calculate_arc_from_episode`, retry-feedback helper, cache sync callback 같은 **real `SovereignApp` bound method 표면**이 drift해도 현재 테스트망이 놓칠 수 있다.
   - 특히 `main_a.py`의 private export rename/삭제, `Stage2Context.from_app()` slot 추가/삭제, wrapper boilerplate drift가 production path에서만 드러날 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - 실행한 Stage2 범위 테스트는 `67 passed, 5 skipped`였다.
   - 하지만 이 녹색은 Stage2 business logic과 일부 wrapper 동작을 확인할 뿐, `real app -> from_app -> consumer` 결합 자체를 잠그지 않는다.
   - 이번 조사 중 직접 수행한 lightweight real-app 확인에서는 현재 코드가 맞았지만, 그 검사는 테스트 suite의 일부가 아니다.
7. 기존 문서와의 중복 여부
   - `related-but-narrower-live-wiring-surface`
   - `MFS-T2-002`와 `MLW-T5-001`이 넓은 테스트 realism / shim drift를 다뤘다.
   - 이번 항목은 그중에서도 **Stage2의 3개 실진입점이 모두 real `from_app()` 경로로 검증되지 않는다는 점**을 별도로 잠근다.
8. 권장 후속 조치
   - `SovereignApp.__new__(SovereignApp)` 기반 lightweight real-app fixture를 만들고, `Stage2Context.from_app(real_app_fixture)`로 핵심 slot identity를 고정한다.
   - `_stage_2_arcs()` wrapper test는 `from_app()` monkeypatch를 제거한 별도 케이스를 추가한다.
   - one-stop Stage2 진입 tests도 fake module 치환 대신 real `Stage2Context.from_app()` 경로를 최소 1회는 태워야 한다.

---

### [MLW-T1-002] P3 - `cumulative_state_cache` live wiring은 populate만 동기화하고 clear는 ctx에만 반영한다

1. ID
   - `MLW-T1-002`
2. Severity
   - `P3`
3. 현상 요약
   - `Stage2Context.from_app()`는 `_cumulative_state_cache`, `_cumulative_state_cache_key`를 app에서 읽고, 동시에 `sync_cache_key_to_app` weakref callback을 만든다.
   - `Stage2Preflight`는 cache populate 시 `ctx`뿐 아니라 app에도 `sync_cache_key_to_app(arc_count, cache=state_result)`로 즉시 동기화한다.
   - 그러나 `Stage2Finalizer.run_finalize()`는 성공 후 `self.ctx.cumulative_state_cache = None`, `self.ctx.cumulative_state_cache_key = None`만 수행하고 app 쪽 clear는 호출하지 않는다.
   - `main_a.py` wrapper 3곳도 종료 시 `state_tracker` 계열만 sync하고 `_cumulative_state_cache*`는 손대지 않는다.
   - 결과적으로 populate는 `ctx -> app`으로 흐르지만 clear는 `ctx`에서만 끝나는 비대칭 live wiring이다.
4. 코드 근거
   - `modules/core/stage2_context.py:339-360` — app cache 읽기 + `sync_cache_key_to_app=_make_sync_callback(...)`
   - `modules/core/stage2_preflight.py:712-716` — state extractor cache populate 후 app sync
   - `modules/core/stage2_preflight.py:1053-1057` — constraint compiler path에서도 동일 sync
   - `modules/core/stage2_finalizer.py:1125-1126` — ctx cache only clear
   - `main_a.py:2703-2706`, `main_a.py:3741-3744`, `main_a.py:3985-3988` — wrapper 종료 시 state tracker만 write-back
   - `modules/core/stage2_orchestrator.py:318-319` — 다음 run 시작 시 ctx cache reset
5. downstream 영향 경계
   - correctness는 현재 `stage_2_arcs_async_logic()` 시작부 reset이 보호한다.
   - 다만 성공 직후 app 객체에는 stale `_cumulative_state_cache` / `_cumulative_state_cache_key`가 남을 수 있다.
   - 영향은 주로 메모리 잔류, 관측성 혼선, future refactor 시 cache ownership 오해에 가깝다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_sweep3.py:262-279`는 `sync_cache_key_to_app` 콜백 직접 호출만 본다.
   - `tests/test_stage2_finalizer.py:35-36`는 ctx cache 필드를 세팅하지만 finalize 후 app 쪽 cache 정리 여부는 보지 않는다.
   - real app fixture에서 `populate -> finalize -> app cache cleared` round-trip을 검증하는 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - `Stage2Finalizer` 성공 경로에서 `sync_cache_key_to_app(None)` 또는 동등한 clear sync를 호출해 방향을 맞춘다.
   - 또는 app cache를 wrapper 종료 시 명시적으로 지우고, real-app round-trip regression test를 추가한다.

---

### [MLW-T1-003] P3 - `state_tracker` / `_state_tracker_loaded_arcs` write-back 계약이 3개 Stage2 진입점에 수동 복제돼 있다

1. ID
   - `MLW-T1-003`
2. Severity
   - `P3`
3. 현상 요약
   - `Stage2Orchestrator`는 `ctx.state_tracker_loaded_arcs`를 읽어 증분 StateTracker 재사용 여부를 판단한다.
   - `main_a.py`는 Stage2 종료 후 `ctx.state_tracker`와 `ctx.state_tracker_loaded_arcs`를 app에 다시 써 주는 boilerplate를 3개 진입점에 각각 직접 복제했다.
   - 현재 세 경로의 구현은 일치한다.
   - 문제는 이 계약이 공유 helper가 아니라 복제 코드로 존재하고, 테스트도 primary wrapper 1곳만 직접 본다는 점이다.
   - one-stop 계열 tests는 fake `Stage2Context` module을 써서 alternate entrypoint가 real ctx field 이름을 계속 지키는지 보지 않는다.
4. 코드 근거
   - `main_a.py:2685-2706` — primary Stage2 wrapper
   - `main_a.py:3722-3744` — one-stop frontier lag 내부 Stage2 진입
   - `main_a.py:3965-3988` — one-stop auto-continue 내부 Stage2 진입
   - `modules/core/stage2_orchestrator.py:236-247` — `existing_tracker_arcs == 0` 또는 mismatch 시 tracker reset
   - `tests/test_main_a_stage_entry_contracts.py:93-115` — primary wrapper에서만 sentinel ctx write-back 검증
   - `tests/test_one_stop_frontier_lag_auto_continue.py:8-15`, `103-106`, `191-194`, `237-240` — alternate path는 fake context module 사용
5. downstream 영향 경계
   - 어느 한 진입점이라도 `_state_tracker_loaded_arcs` write-back을 빼먹으면 다음 Stage2 run에서 `existing_tracker_arcs == 0`으로 판정되어 StateTracker가 불필요하게 재초기화될 수 있다.
   - 즉시 기능 붕괴보다는 성능/연속성/캐시 효율 저하 위험이다.
6. 현재 테스트 근거 또는 테스트 부재
   - primary wrapper는 최소 write-back을 본다.
   - alternate Stage2 entrypoint 2곳은 real `Stage2Context` field contract를 직접 잠그는 테스트가 없다.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - wrapper 종료 공통부를 `_sync_stage2_ctx_back_to_app(ctx)` 같은 helper로 추출해 drift 표면을 1곳으로 줄인다.
   - 최소한 세 Stage2 entrypoint 각각에 대해 real ctx field names를 쓰는 regression test를 추가한다.

---

### [MLW-T1-004] P3 - `Stage2Context` 문서와 테스트 메타가 실제 50-slot live surface를 따라가지 못한다

1. ID
   - `MLW-T1-004`
2. Severity
   - `P3`
3. 현상 요약
   - `Stage2Context` 클래스 docstring은 여전히 `필수 5종 / 확장 18종 / 콜백 21종` 구조를 기술한다.
   - 실제 `__slots__`는 총 `50`개이고, 확장 슬롯도 이미 `20`개다.
   - docstring은 `context_advisor`, `adversarial_self_play`를 확장 목록에서 누락했고, `sync_cache_key_to_app`, `retry_feedback_contract`, `retry_feedback_missing_callbacks`, `session_logger` 같은 post-callback live slot도 설명하지 않는다.
   - 또한 docstring은 `state_tracker`를 “필수 5종”에 넣지만, `from_app()`는 `state_tracker=_safe_getattr(app, "state_tracker", None)`로 optional 처리한다.
   - `tests/integration/test_pipeline_smoke.py`의 Stage2 slot count 주석도 아직 `필수 5 + 확장 19 + 콜백 22 = 46종`으로 남아 있다.
4. 코드 근거
   - `modules/core/stage2_context.py:111-131` — 구 docstring 분류
   - `modules/core/stage2_context.py:141-190` — 실제 `__slots__` 50개
   - `modules/core/stage2_context.py:317` — `state_tracker` optional fetch
   - `tests/test_stage2_context.py:133-145` — `state_tracker is None` 경로를 허용
   - `tests/integration/test_pipeline_smoke.py:485` — stale slot-count 주석
5. downstream 영향 경계
   - runtime failure는 아니다.
   - 다만 audit 문서, test coverage 판단, slot count smoke comment가 실제 표면을 과소계상해 “충분히 잠겼다”는 잘못된 확신을 만들 수 있다.
   - 이번처럼 문서 기반 audit 초안이 쉽게 과장될 수 있는 원인이 된다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage2_context.py`는 일부 slot 동작만 검증한다.
   - authoritative schema source로 쓸 수 있는 “현재 slot manifest” 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - `Stage2Context` docstring과 smoke comment를 실제 50-slot surface에 맞춰 정리한다.
   - slot count만 보는 느슨한 테스트 대신, authoritative slot manifest를 고정하는 focused regression test를 추가한다.

---

## Rejected Candidates

| 후보 | PASS2 판정 | 근거 |
|------|------------|------|
| `validate_arc_data_fields` repair hook 미바인딩 | `already-covered-do-not-reopen` | `docs/2026-03-13/MFS-T2-state-service-validation-findings.md`의 `[MFS-T2-001]`이 동일 real-app surface를 이미 P1으로 확정했다 |
| `session_logger` Stage2 dead slot | `removed` | `modules/core/stage2_orchestrator.py:690-699`, `modules/core/stage2_finalizer.py:643-650`에서 실제 사용된다 |
| spec-less `MagicMock` auto-attribute가 missing callback을 truthy로 숨김 | `removed` | `_safe_getattr()`가 `inspect.getattr_static()`로 missing attr를 먼저 거른다. bare `MagicMock` 확인에서도 지정하지 않은 slot은 `None`이었다 |
| `calculate_arc_from_episode` 무가드 호출 | `coverage-gap-only` | 현재 real `SovereignApp` surface에는 `_get_max_episode_from_manuscripts`와 `_calculate_arc_from_episode`가 둘 다 존재하고 callable이었다. 문제는 future/partial-host 방어 공백이지, 현재 real-app mismatch는 아니다 |

---

## Coverage Gaps / Open Questions

1. `Stage2Context.from_app(real_app)` signature parity
   - 이번 조사에서 현재 callability는 직접 확인했지만, 이 검사가 test suite에 자동화돼 있지 않다.
   - callback별 `inspect.signature()` parity regression이 있으면 future drift를 더 빨리 잡을 수 있다.
2. `validate_arc_data_fields` repair hook
   - 이번 T1 문서에서는 중복으로 닫지 않았지만, Stage2 real-app binding에서 가장 강한 미바인딩 이슈는 여전히 `MFS-T2-001`이다.
3. manual ctx injection path
   - `calculate_arc_from_episode` 같은 slot은 real app에서는 현재 안전하지만, partial ctx/manual host 조립 경로가 얼마나 허용되어야 하는지는 문서로 잠겨 있지 않다.

---

## PASS1 -> PASS2 -> PASS3 요약

- PASS1: 후보 `8`건 수집
- PASS2:
  - 기존 문서 중복 제거 `1`건 (`MFS-T2-001`)
  - 오판 제거 `2`건 (`session_logger dead slot`, `MagicMock auto-attribute`)
  - coverage gap으로 축소 `1`건 (`calculate_arc_from_episode`)
- PASS3: 확정 `4`건
  - `P1 1건`
  - `P3 3건`
  - `P0 0건`
  - `P2 0건`

## 마감 체크

- 코드 근거 포함: `Yes`
- downstream 영향 경계 포함: `Yes`
- 현재 테스트 근거 또는 테스트 부재 포함: `Yes`
- 기존 문서와의 중복 여부 포함: `Yes`
- `PASS1 -> PASS2 -> PASS3` 요약 포함: `Yes`
