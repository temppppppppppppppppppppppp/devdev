# [BGA-T3] Facade / Helper / DI / Live Consumer Findings

> 작성일: 2026-03-13
> 상태: `PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / artifact-proof cross-check / UTF-8 only`
> 기준 오더: `backend-global-full-survey-master-audit-order.md`
> 실행 요약: `PASS1 후보 5건 -> PASS2 제거 2건 -> PASS3 확정 3건`

---

## 조사 범위

- `main_a.py`
  - `_validate_arc_data_fields()`
  - `_generate_writer_guidance_v60_8()`
  - `_generate_arc_context_v60()`
  - Stage 4 entry의 `Stage4Context.from_app()` 경로
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/protocols/app_services.py`

## 필수 근거

- 읽은 테스트:
  - `tests/test_stage2_context.py`
  - `tests/test_stage3_orchestrator.py`
  - `tests/test_protocols_services.py`
  - `tests/test_stage4_context.py`
  - `tests/test_stage4_orchestrator.py`
  - `tests/test_stage4_context_builder.py`
  - `tests/test_main_a_retry_feedback.py`
  - `tests/integration/test_patch_wiring.py`
- 읽은 참조 문서:
  - `docs/2026-03-13/main_a-facade-shim-detail-consolidated-findings.md`
  - `docs/2026-03-13/main_a-retry-feedback-detail-consolidated-findings.md`
  - `docs/2026-03-13/main_a-dormant-helper-live-consumer-detail-consolidated-findings.md`
  - `docs/2026-03-13/XC-DI-consolidated-findings.md`
- 실행 검증:
  - `pytest -q tests/test_stage2_context.py tests/test_stage3_orchestrator.py tests/test_protocols_services.py`
  - 결과: `103 passed in 2.76s`
  - `pytest -q tests/test_stage4_context.py tests/test_stage4_orchestrator.py tests/test_stage4_context_builder.py tests/test_main_a_retry_feedback.py`
  - 결과: `collection error - Stage4Context __slots__ conflicts with class variable`
  - `pytest -q tests/test_stage4_orchestrator.py tests/test_stage4_context_builder.py tests/test_main_a_retry_feedback.py`
  - 결과: `3 failed, 97 passed, 8 errors in 3.44s`
  - `pytest -q tests/test_stage4_context_builder.py`
  - 결과: `49 passed in 1.71s`
  - `pytest -q tests/test_stage4_orchestrator.py -k "stage4_complete or early_return or failed_exhaustion"`
  - 결과: `2 passed, 54 deselected in 1.50s`
- 정적 교차 검증:
  - `Stage4Context`의 `__slots__`와 property 이름 충돌 여부 확인
  - `Stage4Orchestrator.ctx` auto-build와 `main_a.py` Stage 4 entry import 경로 비교
  - `Stage3Orchestrator`의 lazy init / ctx sync가 injected context를 덮어쓰는지 확인
  - `Stage2Context.from_app()` retry-feedback callback binding과 current tests 비교

## PASS 기록

- PASS 1:
  - 후보 1: `Stage4Context`가 현재 코드에서 import 가능한 live DI surface인가
  - 후보 2: Stage4 regression net이 실제 `from_app()` / `orch.ctx` auto-build 경로를 잠그는가
  - 후보 3: Stage3 injected context가 실제 runtime에서 source of truth로 존중되는가
  - 후보 4: Stage2 retry-feedback callback binding drift가 여전히 live path에서 깨져 있는가
  - 후보 5: Stage3 completion summary가 실패 path도 success처럼 덮는가
- PASS 2:
  - 후보 4 제거: `Stage2Context.from_app()`는 callback tier/fallback contract를 현재 코드에서 구성하고, `tests/test_stage2_context.py`가 real bound method와 fallback 경로를 직접 잠근다.
  - 후보 5 제거: `Stage3Orchestrator._handle_failure()`는 현재 항상 `break=True`를 반환하며, `tests/test_stage3_orchestrator.py`도 break path에서 `stage3_complete` summary가 쓰이지 않음을 잠근다.
- PASS 3:
  - 확정 3건만 `BGA-T3-*`로 채택

## Finding Ledger

| ID | Severity | 상태 | 파일/함수 | 요약 |
|----|----------|------|-----------|------|
| `BGA-T3-001` | `P0` | confirmed | `modules/core/stage4_context.py`, `modules/core/stage4_orchestrator.py`, `main_a.py` | `Stage4Context`가 `__slots__`와 property 충돌로 import 단계에서 즉시 죽는다 |
| `BGA-T3-002` | `P2` | confirmed | `modules/core/stage3_orchestrator.py` | Stage3 lazy init이 injected context를 source of truth로 보지 않고 `self.app` state로 덮어쓴다 |
| `BGA-T3-003` | `P2` | confirmed | `tests/test_stage4_orchestrator.py`, `tests/test_stage4_context_builder.py`, `Stage4Orchestrator.ctx` | stage4 회귀망 대부분이 injected mock context로 green이고 실제 auto-build/live DI path는 비어 있다 |

## Final Findings

### [BGA-T3-001] P0 - `Stage4Context`가 `__slots__` / property 이름 충돌로 import 단계에서 즉시 죽는다

1. ID
   - `BGA-T3-001`
2. Severity
   - `P0`
3. 현상 요약
   - `Stage4Context`는 `generate_writer_guidance_v60_8`, `enrich_director_result`를 `__slots__`에 선언하면서 같은 이름의 property도 다시 정의한다.
   - Python class creation 시 이 조합은 `ValueError: 'generate_writer_guidance_v60_8' in __slots__ conflicts with class variable`를 발생시킨다.
   - Stage 4 live path는 `main_a.py`와 `Stage4Orchestrator.ctx` 둘 다 `Stage4Context.from_app()`를 import해서 쓰므로, 실제 Stage 4 진입 자체가 import 단계에서 죽을 수 있다.
4. 코드 근거
   - `modules/core/stage4_context.py:47-80`은 `generate_writer_guidance_v60_8`, `enrich_director_result`를 `__slots__`에 포함한다.
   - `modules/core/stage4_context.py:159-160`은 초기화 중 같은 이름의 attribute에 값을 넣는다.
   - `modules/core/stage4_context.py:171-191`은 동일 이름의 property / setter를 다시 선언한다.
   - `modules/core/stage4_orchestrator.py:201-204`는 auto-build 시 `from modules.core.stage4_context import Stage4Context` 후 `Stage4Context.from_app(self.app)`를 호출한다.
   - `main_a.py:3625-3628`도 Stage 4 entry에서 같은 import / `from_app()` 경로를 사용한다.
5. downstream 영향 경계
   - Stage 4 chief writer live entry
   - Stage 4 orchestrator auto-build DI path
   - `generate_writer_guidance_v60_8`, `enrich_director_result` callback live consumer 전체
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage4_context.py:7` 자체가 `Stage4Context` import를 시도한다.
   - `pytest -q tests/test_stage4_context.py tests/test_stage4_orchestrator.py tests/test_stage4_context_builder.py tests/test_main_a_retry_feedback.py`는 현재 `Stage4Context __slots__ conflicts with class variable`로 collection 단계에서 멈춘다.
   - `pytest -q tests/test_stage4_orchestrator.py tests/test_stage4_context_builder.py tests/test_main_a_retry_feedback.py`도 `3 failed, 97 passed, 8 errors`를 내며, error 대부분이 `orch.ctx` 또는 `Stage4Context.from_app()` 접근 시점에 집중된다.
7. 기존 문서와의 중복 여부
   - `cross-track-confirmed`
   - `MDH-T1-01`이 지적한 Stage4 callback live bug를 현재 workspace 코드와 pytest failure로 재확인했다. 이번 finding은 live DI import crash로 승격해 기록한다.
8. 권장 후속 조치
   - `Stage4Context`에서 slot/property 이름 충돌을 제거해야 한다.
   - 최소 회귀 테스트를 추가해야 한다: `import Stage4Context`, `Stage4Context.from_app(app)`, `main_a` Stage 4 entry smoke.
   - Stage4 live callback slot은 property-backed meta dict 또는 plain slot 중 한 가지 방식으로만 유지해야 한다.

### [BGA-T3-002] P2 - Stage3 lazy init이 injected context를 source of truth로 보지 않고 `self.app` state로 덮어쓴다

1. ID
   - `BGA-T3-002`
2. Severity
   - `P2`
3. 현상 요약
   - `Stage3Orchestrator`는 `context=`로 주입된 `ctx`를 받을 수 있지만, 실제 실행 시 `state_tracker`, `world_state`, `fact_ledger` 초기화와 authoritative source는 `ctx`가 아니라 `self.app`다.
   - stage entry는 `_init_state_tracker_if_needed()`, `_init_world_state_if_needed()`, `_init_fact_ledger_if_needed()`를 모두 `self.app`에 대해 수행하고, 직후 `ctx.state_tracker/world_state/fact_ledger = getattr(self.app, ...)`로 덮어쓴다.
   - 그 결과 injected context에 사전 주입된 tracker/state service는 live path에서 유지된다는 보장이 없고, app와 ctx가 다른 객체를 들고 있으면 `ctx` 쪽 DI가 조용히 무효화된다.
4. 코드 근거
   - `modules/core/stage3_orchestrator.py:498-513`은 Stage 3 시작 시 lazy init을 수행한 뒤 `ctx.state_tracker`, `ctx.world_state`, `ctx.fact_ledger`를 `self.app`에서 다시 복사한다.
   - `modules/core/stage3_orchestrator.py:630-690`의 `_init_state_tracker_if_needed()`, `_init_world_state_if_needed()`, `_init_fact_ledger_if_needed()`는 모두 `app.*`에 직접 할당한다.
   - `modules/core/stage3_orchestrator.py:430-434`는 ctx auto-build조차 `Stage3Context.from_app(self.app)` 기반이라 app-authoritative 구조가 기본값이다.
5. downstream 영향 경계
   - Stage3 injected context consumer
   - lazy init 이후 tracker/state service identity를 기대하는 helper / facade
   - alt consumer, test harness, future service extraction 시 DI semantic contract
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage3_orchestrator.py:667-674`은 `context_advisor`와 `memory`를 ctx에 주입하는 happy path를 본다.
   - `tests/test_stage3_orchestrator.py:1029-1054`는 injected context 저장과 `get_protagonist_name` callback만 확인한다.
   - `tests/test_stage3_orchestrator.py:1084-1108`은 `from_app()` binding을 확인하지만, injected ctx의 `state_tracker/world_state/fact_ledger`가 app divergence 상황에서도 유지되는지 검증하는 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `related-but-promoted`
   - `XC-DI-005`의 `self.app` 직접 접근 문제를 Stage3 live consumer / injected context semantics 관점에서 승격해 기록한다.
8. 권장 후속 조치
   - Stage3 runtime에서 `ctx`와 `app` 중 어느 쪽이 authoritative source인지 단일 SSOT로 고정해야 한다.
   - injected context를 허용할 것이면 lazy init 결과를 ctx 기준으로 쓰거나, app sync가 일어날 때 이를 명시적으로 검증해야 한다.
   - 회귀 테스트를 추가해야 한다: `custom ctx trackers != app trackers`일 때 어떤 쪽이 유지되는지 명시 검증.

### [BGA-T3-003] P2 - stage4 회귀망 대부분이 injected mock context로 green이고 실제 auto-build/live DI path는 비어 있다

1. ID
   - `BGA-T3-003`
2. Severity
   - `P2`
3. 현상 요약
   - Stage4 관련 테스트의 상당수는 `Stage4Orchestrator(mock_app, context=ctx)`로 custom context를 직접 주입해 green을 만든다.
   - 이 경로는 broken `Stage4Context.from_app()` / `orch.ctx` auto-build import path를 우회한다.
   - 반대로 실제 auto-build를 건드리는 테스트와 fixture는 같은 `Stage4Context` import 충돌에 걸려 실패하거나 error로 무너진다.
   - 결과적으로 regression net은 live path와 동일한 surface를 잠그지 못하고, injected-context micro-test가 Stage4 DI 건강도를 과대표현한다.
4. 코드 근거
   - `modules/core/stage4_orchestrator.py:201-204`에서 live auto-build는 `Stage4Context.from_app(self.app)`를 사용한다.
   - `tests/test_stage4_orchestrator.py:141-148`, `tests/test_stage4_orchestrator.py:165-171`, `tests/test_stage4_context_builder.py:74-87`은 custom `ctx` 주입 경로를 사용한다.
   - `tests/test_stage4_orchestrator.py:271-310`, `tests/test_stage4_orchestrator.py:816-823`, `tests/test_stage4_orchestrator.py:1049-1050`, `tests/test_stage4_orchestrator.py:1120-1123`은 `Stage4Context.from_app()` 또는 `orch.ctx` auto-build에 닿는 순간 실패 surface가 된다.
5. downstream 영향 경계
   - Stage4 orchestrator regression net
   - Stage4 context builder / chief writer entry smoke coverage
   - facade/DI 변경 후 live consumer 회귀 감지 능력
6. 현재 테스트 근거 또는 테스트 부재
   - `pytest -q tests/test_stage4_context_builder.py`는 `49 passed in 1.71s`로 green이다.
   - `pytest -q tests/test_stage4_orchestrator.py -k "stage4_complete or early_return or failed_exhaustion"`도 injected context 경로만 골라 `2 passed, 54 deselected`를 기록한다.
   - 하지만 broader stage4 suite는 `pytest -q tests/test_stage4_orchestrator.py tests/test_stage4_context_builder.py tests/test_main_a_retry_feedback.py`에서 `3 failed, 97 passed, 8 errors`를 내며, live auto-build path가 분리된 채 무너진다.
7. 기존 문서와의 중복 여부
   - `cross-track-confirmed`
   - `MFS-T5-001`, `MDH-T5-003`의 proof-gap 테마와 연결되지만, 이번 finding은 Stage4 DI live path가 injected-context tests에 의해 구체적으로 가려지는 현재형 회귀망 문제를 독립적으로 잠근다.
8. 권장 후속 조치
   - Stage4 suite에 `context 미주입 -> orch.ctx auto-build -> stage4 run smoke` 경로를 최소 1개 이상 필수 고정해야 한다.
   - injected-context unit test와 live from_app path test를 별도 레이어로 나눠 보고해야 한다.
   - `Stage4Context` import smoke가 깨지면 stage4 관련 suite를 fail-fast로 닫도록 test topology를 정리해야 한다.

## Rejected Candidates

| 후보 | PASS2 판정 | 근거 |
|------|------------|------|
| Stage2 retry-feedback callback binding이 현재도 live path에서 죽어 있다 | removed | `modules/core/stage2_context.py:315-370`은 callback tier/fallback contract를 구성한다. `tests/test_stage2_context.py:94-110`, `tests/test_stage2_context.py:168-179`, `tests/test_stage2_context.py:198-219`도 real bound method / fallback 경로를 green으로 잠근다. |
| Stage3 completion summary가 failure path도 success처럼 덮는다 | removed | `modules/core/stage3_orchestrator.py:1808-1809`, `modules/core/stage3_orchestrator.py:1995-2001`에서 failure는 항상 `break=True`로 종료한다. `tests/test_stage3_orchestrator.py:982-991`도 break path에서 `_write_audit_summary("stage3_complete")`가 호출되지 않음을 검증한다. |

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| Stage4 live `from_app()` smoke | 현재 실패 surface | `Stage4Context` import / `from_app()` / `main_a` Stage 4 entry smoke를 단일 fail-fast suite로 고정 |
| Stage3 injected ctx vs app authority | 테스트 공백 | injected ctx의 tracker/world_state/fact_ledger가 app divergence 상황에서 유지되는지 검증 |
| Stage4 injected-context tests와 live path 분리 보고 | proof gap | injected-unit layer와 auto-build integration layer를 분리한 회귀 리포트 |

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- `PASS1 -> PASS2 -> PASS3` 요약 포함
