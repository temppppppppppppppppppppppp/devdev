# MLW-T4: Protocol / Facade / Runtime Slot Bridge Findings

> 작성일: 2026-03-13
> 작성자: `Codex`
> 터미널: `T4`
> 상태: `PASS3 complete / re-audited`
> 기준 오더: `main_a-live-wiring-contract-detail-full-survey-audit-order.md`
> 실행 요약: `PASS1 후보 8건 -> PASS2 제거 3건 -> PASS3 확정 5건`

---

## 조사 범위

- `modules/protocols/app_services.py`
- `modules/core/services/audit_service.py`
- `modules/core/services/state_service.py`
- `modules/core/services/project_service.py`
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `main_a.py`
- `tests/test_protocols_services.py`
- `tests/test_audit_service.py`
- `tests/test_state_service.py`
- `tests/test_stage2_context.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_orchestrator.py`
- 중복 대조 문서:
  - `docs/2026-03-13/MFS-T5-protocol-tests-regression-findings.md`
  - `docs/2026-03-13/MPN-T5-consumer-tests-legacy-contract-findings.md`
  - `docs/2026-03-13/MRF-T1-stage2-callback-binding-findings.md`

## 실행 검증

- `pytest -q tests/test_protocols_services.py tests/test_audit_service.py tests/test_state_service.py tests/test_stage2_context.py tests/test_stage3_orchestrator.py`
  - 결과: `147 passed in 3.52s`
- `pytest -q tests/test_stage4_context.py tests/test_stage4_orchestrator.py`
  - 결과: `19 failed, 45 passed, 20 errors in 5.50s`
  - 공통 실패 원인: `modules/core/stage4_context.py:148` `AttributeError: 'Stage4Context' object has no attribute 'generate_writer_guidance_v60_8'`

---

## PASS 기록

### PASS 1 후보

- 후보 1: `Stage4Context`의 callback contract가 `__slots__` / `__init__` / `from_app()` 사이에서 갈라져 있고, 현재는 constructor 자체가 깨져 있다.
- 후보 2: `app_services.py` Protocol 계층이 runtime bridge에서 실제로 쓰이지 않는다.
- 후보 3: audit summary bridge가 Protocol, context slot, direct app call로 갈라져 tagged contract를 한 곳도 일관되게 잠그지 못한다.
- 후보 4: `safe_commit()` 반환값 의미가 Stage3과 Stage4에서 다르다.
- 후보 5: `Stage4Context.get_int_input`은 optional slot인데 consumer는 두 곳에서 required처럼 쓴다.
- 후보 6: `StateServiceProtocol` vs `StateService` 이름이 혼동을 만든다.
- 후보 7: Stage2의 `analyze_rejection_pattern_v60`가 무가드 hard-call이다.
- 후보 8: `from_app()` 자체가 테스트되지 않아 construction-time blind spot이 남아 있다.

### PASS 2 제거

- 후보 6 제거:
  - `StateServiceProtocol`은 `StateTracker` facade를, `StateService`는 helper service를 모델링한다는 점이 docstring과 `tests/test_protocols_services.py`의 non-conform test로 이미 명시돼 있다.
  - naming awkwardness만으로 live wiring defect로 확정하기는 어렵다.
- 후보 7 제거:
  - 기존 초안의 `analyze_rejection_pattern_v60` direct hard-call 주장은 stale이다.
  - 현재 `modules/core/stage2_orchestrator.py:117-136`은 `_compose_rejection_pattern_feedback()` 안에서 `callable()` guard와 diagnostic fallback을 사용한다.
- 후보 8 제거:
  - `from_app()` 테스트는 없다가 아니라 이미 존재한다.
  - `tests/test_stage2_context.py`, `tests/test_stage3_orchestrator.py`, `tests/test_stage4_context.py`에 mapping/None-path test가 있다.
  - 다만 대부분 synthetic app/MagicMock 기반이라 real `SovereignApp` contract를 잠그지 못한다는 점만 coverage gap으로 유지한다.

### PASS 3 확정

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| `MLW-T4-001` | `P1` | confirmed | `modules/core/stage4_context.py`, `main_a.py` | `Stage4Context`는 callback 2개를 `__slots__`에 선언하지 않은 채 `__init__`/`from_app()`에서 할당해, live Stage4 entry가 현재 즉시 `AttributeError`로 붕괴한다 |
| `MLW-T4-002` | `P2` | confirmed | `modules/protocols/app_services.py`, `stage2/3/4_context.py` | `app_services.py` Protocol은 production runtime bridge에서 소비되지 않아, protocol green이 live wiring 보증으로 연결되지 않는다 |
| `MLW-T4-003` | `P2` | confirmed | `app_services.py`, `main_a.py`, `stage2_orchestrator.py`, `stage3_orchestrator.py`, `stage4_orchestrator.py` | audit summary bridge는 public Protocol, private app wrapper, tagged ctx callback, direct `self.app` call로 분열돼 있다 |
| `MLW-T4-004` | `P2` | confirmed | `stage3_orchestrator.py`, `stage4_orchestrator.py` | 같은 `safe_commit()` 콜백을 Stage3은 failure gate로, Stage4는 fire-and-forget cleanup으로 해석한다 |
| `MLW-T4-005` | `P2` | confirmed | `stage4_context.py`, `stage4_orchestrator.py` | `Stage4Context`는 `get_int_input=None`을 허용하지만 `_prepare_stage4_session()`은 두 지점에서 무가드로 직접 호출한다 |

---

## Final Findings

### [MLW-T4-001] P1 - `Stage4Context` callback contract split-brain이 현재 constructor 자체를 깨뜨린다

1. ID
   - `MLW-T4-001`
2. Severity
   - `P1`
3. 현상 요약
   - `Stage4Context` docstring과 `__slots__`는 callback 7종만 가진다고 서술한다.
   - 그러나 실제 `__init__`와 `from_app()`는 `generate_writer_guidance_v60_8`, `enrich_director_result` 2개를 추가로 받아 할당한다.
   - 두 이름은 `__slots__`에 없기 때문에 `Stage4Context(...)`와 `Stage4Context.from_app(...)`가 현재 코드에서 즉시 `AttributeError`로 실패한다.
   - 이 문제는 dormant helper 여부와 무관하게, slot bridge가 이미 깨져 있다는 뜻이다.
4. 코드 근거
   - `modules/core/stage4_context.py:40-42` callback 7종 서술
   - `modules/core/stage4_context.py:70-80` `__slots__`에는 `generate_writer_guidance_v60_8`, `enrich_director_result`가 없음
   - `modules/core/stage4_context.py:109-119` `__init__`는 두 callback 파라미터를 받음
   - `modules/core/stage4_context.py:148-149` 두 callback을 실제로 할당함
   - `modules/core/stage4_context.py:195-196` `from_app()`도 `app._generate_writer_guidance_v60_8`, `app._enrich_director_result`를 포획함
   - `main_a.py:3544` Stage4 진입 시 `self._stage4_orch.ctx = Stage4Context.from_app(self)`를 직접 호출함
   - `tests/test_stage4_context.py:147-148`, `tests/test_stage4_context.py:171-183`, `tests/test_stage4_context.py:194-197`은 이 두 callback slot이 존재해야 함을 전제로 테스트를 작성함
   - 실행 검증: `pytest -q tests/test_stage4_context.py tests/test_stage4_orchestrator.py` -> `19 failed, 45 passed, 20 errors`; 공통 traceback은 `modules/core/stage4_context.py:148`
5. downstream 영향 경계
   - `main_a.py`의 Stage4 live entry
   - `Stage4Orchestrator.ctx` lazy auto-build
   - `limit_mode` session setup
   - Stage4 관련 post-processor / quality regression / repetition hook 테스트 전부
6. 현재 테스트 근거 또는 테스트 부재
   - blind spot이 아니라 현재 회귀 스위트가 이미 red다.
   - Stage4 관련 테스트가 광범위하게 실패하고 있어, 문제는 문서상 추정이 아니라 실행으로 재현된다.
7. 기존 문서와의 중복 여부
   - `none`
   - 기존 dormant-helper 문서들은 `_generate_writer_guidance_v60_8`, `_enrich_director_result`의 live consumer 부재를 다뤘지만, 이 둘이 `Stage4Context` constructor를 깨뜨린다는 slot-level failure는 닫지 않았다.
8. 권장 후속 조치
   - `Stage4Context.__slots__`에 두 이름을 추가하거나, 정말 dead surface라면 `__init__`/`from_app()`에서 두 이름을 제거해야 한다.
   - 수정 후 `tests/test_stage4_context.py tests/test_stage4_orchestrator.py`를 우선 복구 게이트로 돌린다.

### [MLW-T4-002] P2 - `app_services.py` Protocol 계층이 실제 runtime bridge에서 소비되지 않는다

1. ID
   - `MLW-T4-002`
2. Severity
   - `P2`
3. 현상 요약
   - `UIServiceProtocol`, `AuditServiceProtocol`, `ProjectRepositoryProtocol`, `StateServiceProtocol`, `ConfigServiceProtocol`은 정의돼 있고 테스트도 있다.
   - 그러나 실제 Stage2/3/4 wiring은 이 Protocol을 import하거나 `isinstance()`/assert로 검증하지 않는다.
   - production bridge는 전부 `from_app()`의 attribute capture와 private wrapper binding에 의존한다.
   - 따라서 protocol test가 green이어도 실제 `main_a.py` surface와 context slot contract가 drift할 수 있다.
4. 코드 근거
   - `rg -n "modules\\.protocols\\.app_services|from modules\\.protocols\\.app_services|UIServiceProtocol|AuditServiceProtocol|ProjectRepositoryProtocol|StateServiceProtocol|ConfigServiceProtocol" modules main_a.py`
     - 결과는 사실상 `modules/protocols/app_services.py` 정의부와 service docstring 주석뿐이며, runtime bridge에서의 실제 import/검사는 확인되지 않음
   - `modules/core/stage2_context.py:309-363` `from_app()`는 `_safe_getattr()`로 app surface를 직접 포획
   - `modules/core/stage3_context.py:100-128` `from_app()`는 plain `getattr()`로 app surface를 직접 포획
   - `modules/core/stage4_context.py:158-200` `from_app()`는 `_safe_getattr()`로 app surface를 직접 포획
   - 어느 경로에도 `Protocol` conformance assertion이 없다
5. downstream 영향 경계
   - protocol 정의/테스트가 live runtime contract의 안전망이 되지 못한다
   - context slot rename, wrapper signature drift, app surface 누락이 protocol green 뒤에 남을 수 있다
   - `main_a.py -> ctx.from_app() -> consumer` 체인은 protocol layer와 별개로 움직인다
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_protocols_services.py`는 mock structural typing을 검증한다
   - `pytest -q tests/test_protocols_services.py tests/test_audit_service.py tests/test_state_service.py tests/test_stage2_context.py tests/test_stage3_orchestrator.py`는 `147 passed in 3.52s`
   - 하지만 이 green은 real `SovereignApp` fixture나 construction-time protocol check를 포함하지 않는다
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - 선택지는 둘 중 하나다
   - Protocol을 documentation-only artifact로 명시 격하한다
   - 또는 `from_app()`/integration test에서 real host fixture에 대한 contract assertion을 추가한다

### [MLW-T4-003] P2 - audit summary bridge가 Protocol, ctx slot, direct app call로 분열돼 tagged contract를 잠그지 못한다

1. ID
   - `MLW-T4-003`
2. Severity
   - `P2`
3. 현상 요약
   - `AuditServiceProtocol`은 public method 이름과 무인자 `write_audit_summary(self)`를 정의한다.
   - 실제 runtime은 `main_a.py` private wrapper (`_audit_event`, `_flush_audit_buffer`, `_write_audit_summary(tag="snapshot")`)를 쓴다.
   - Stage2/3는 `ctx.write_audit_summary("stage*_complete")`를 호출하지만, Stage4 완료 경로는 `self.app._write_audit_summary("stage4_complete")`를 직접 호출한다.
   - 즉, audit bridge는 Protocol, context slot, direct app path가 서로 다른 contract를 가리키고 있고, protocol test는 그중 어느 쪽도 정확히 모델링하지 않는다.
4. 코드 근거
   - `modules/protocols/app_services.py:46-67` `AuditServiceProtocol`
   - `modules/core/services/audit_service.py:72` 실제 구현은 `write_audit_summary(self, tag: str = "snapshot")`
   - `main_a.py:2831-2839` private wrapper `_audit_event`, `_flush_audit_buffer`, `_write_audit_summary(tag="snapshot")`
   - `modules/core/stage2_context.py:338-347` Stage2는 private wrapper를 ctx callback으로 바인딩
   - `modules/core/stage3_context.py:117-123` Stage3도 private wrapper를 ctx callback으로 바인딩
   - `modules/core/stage2_orchestrator.py:946-947` Stage2는 `self.ctx.write_audit_summary("stage2_complete")`
   - `modules/core/stage3_orchestrator.py:600-601` Stage3는 `ctx.write_audit_summary("stage3_complete")`
   - `modules/core/stage4_orchestrator.py:1601-1603` Stage4는 `self.app._write_audit_summary("stage4_complete")`를 direct call
   - `tests/test_protocols_services.py:95-102` `MockAudit.write_audit_summary()`는 무인자 mock
5. downstream 영향 경계
   - Stage2 완료 audit summary
   - Stage3 완료 audit summary
   - Stage4 완료 audit summary
   - 향후 audit facade refactor 시 stage별로 서로 다른 붕괴 양상을 만들 수 있다
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_audit_service.py`는 실제 service의 tagged summary 구현을 본다
   - `tests/test_protocols_services.py`는 무인자 mock을 conforming으로 승인한다
   - Stage2/3/4가 동일 tagged bridge를 공유하는지 보는 real host integration test는 없다
7. 기존 문서와의 중복 여부
   - `related-but-new-live-wiring-surface`
   - `MFS-T5-001`은 tagged summary facade blind spot을 다뤘다
   - 이번 finding은 그보다 넓게 `Protocol -> ctx slot -> direct app call` 분열 자체를 live wiring 관점에서 확정한다
8. 권장 후속 조치
   - `AuditServiceProtocol` target을 명확히 하나로 정한다
   - service public API를 모델링할지, app facade private wrapper까지 포함할지 선택해야 한다
   - Stage4 completion도 `ctx` 경유로 통일하거나, 반대로 Stage2/3도 direct app facade로 통일해 bridge를 하나로 잠근다

### [MLW-T4-004] P2 - `safe_commit()` 반환값 의미가 Stage3과 Stage4에서 다르다

1. ID
   - `MLW-T4-004`
2. Severity
   - `P2`
3. 현상 요약
   - Stage3은 `safe_commit()`을 fail-gate로 다룬다.
   - Stage4는 interrupt/exception cleanup에서 `safe_commit()`을 호출만 하고 `False` 반환을 해석하지 않는다.
   - 같은 callback이 stage마다 다른 contract를 갖는 셈이어서 persistence helper 의미가 bridge 레벨에서 일관되지 않다.
4. 코드 근거
   - `modules/core/stage3_orchestrator.py:1505-1511` `if callable(ctx.safe_commit) and not ctx.safe_commit(): ... db_commit_error`
   - `modules/core/stage4_orchestrator.py:1607-1619` cleanup path에서 `self.ctx.safe_commit()` 결과를 무시
   - `tests/test_stage4_orchestrator.py:207-218`, `tests/test_stage4_orchestrator.py:294-305`는 Stage4에서 `safe_commit.assert_called_once()`만 검증
5. downstream 영향 경계
   - Stage3 blueprint persistence failure는 가시적으로 드러남
   - Stage4 cleanup persistence failure는 조용히 삼켜질 수 있음
   - shared commit helper 리팩터링 시 stage별 의미가 더 벌어질 수 있음
6. 현재 테스트 근거 또는 테스트 부재
   - Stage3 쪽은 실패 게이트 코드가 존재한다
   - Stage4 쪽은 `safe_commit=MagicMock(return_value=False)` negative test가 없다
   - 현재 Stage4 스위트는 더 앞단의 `Stage4Context` slot crash 때문에 cleanup semantic 자체를 충분히 분리 검증하지 못한다
7. 기존 문서와의 중복 여부
   - `related-but-new-live-wiring-surface`
   - `MPN-T5-002`가 동일 현상을 shared-helper 관점에서 retained 했다
   - 이번 finding은 `protocol / facade / runtime slot bridge` 책임 경계에서 재기술한다
8. 권장 후속 조치
   - Stage4 cleanup도 `False` 반환을 log/audit event로 승격한다
   - 또는 Stage4 cleanup helper를 bool-return contract가 아닌 fire-and-forget contract로 분리한다

### [MLW-T4-005] P2 - `Stage4Context.get_int_input`은 optional slot인데 `_prepare_stage4_session()`은 두 번 무가드 호출한다

1. ID
   - `MLW-T4-005`
2. Severity
   - `P2`
3. 현상 요약
   - `Stage4Context`는 `get_int_input=None`을 허용하고, `tests/test_stage4_context.py`도 callback 미구현 app에서 `None`을 기대한다.
   - 그런데 `_prepare_stage4_session()`은 `limit_mode` target prompt와 style selection에서 `self.ctx.get_int_input(...)`를 직접 호출한다.
   - 같은 함수 안의 다른 위치(`stage4_orchestrator.py:1273-1276`)는 `callable()` guard를 사용하므로 contract가 파일 내부에서도 일관되지 않다.
4. 코드 근거
   - `modules/core/stage4_context.py:109-119` `get_int_input=None` 허용
   - `tests/test_stage4_context.py:187-199` callback 없는 app에서도 `ctx.get_int_input is None` 기대
   - `modules/core/stage4_orchestrator.py:1480-1485` target episode prompt direct call
   - `modules/core/stage4_orchestrator.py:1536-1538` style choice direct call
   - `modules/core/stage4_orchestrator.py:1273-1276` 같은 파일의 guarded call
   - `tests/test_stage4_orchestrator.py:231-251`, `tests/test_stage4_orchestrator.py:262-263`은 callback이 있는 happy path만 본다
5. downstream 영향 경계
   - `limit_mode=True` Stage4 session setup
   - style guide 미존재 시 interactive style selection
   - manual context injection / partial host / future refactor에서 immediate `TypeError` 가능성
6. 현재 테스트 근거 또는 테스트 부재
   - None-path negative test가 없다
   - 현재는 더 앞의 `Stage4Context` constructor crash가 먼저 터져 이 latent mismatch가 가려져 있다
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - `get_int_input`을 truly required callback으로 승격하거나
   - 두 call site에 `callable(getattr(self.ctx, "get_int_input", None))` guard와 fallback 정책을 넣어 contract를 통일한다

---

## Rejected Candidates

| 후보 | PASS2 판정 | 근거 |
|------|------------|------|
| `StateServiceProtocol` vs `StateService` naming confusion | removed | docstring과 `tests/test_protocols_services.py` non-conform test가 이미 의도적 분리를 명시한다. live wiring defect로 확정하기엔 약함 |
| Stage2 `analyze_rejection_pattern_v60` direct hard-call | removed | 현재 `modules/core/stage2_orchestrator.py:117-136`은 callable guard + diagnostic fallback을 사용한다. 기존 초안 stale |
| `from_app()` 테스트 부재 | removed | Stage2/3/4에 mapping test가 이미 존재한다. 다만 real host fixture 부재만 coverage gap으로 유지 |

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| real `SovereignApp` 기반 `from_app()` 검증 | 미검증 | spec 없는 `MagicMock` 대신 lightweight real host fixture로 `Stage2/3/4Context.from_app()`를 직접 검증 |
| Stage4 negative contract (`safe_commit=False`, `get_int_input=None`) | 미검증 | slot crash 수정 후 dedicated negative tests 필요 |
| `ProjectRepositoryProtocol` setter / property semantics | 부분 미검증 | `runtime_checkable` structural check가 setter 유무를 실질적으로 보장하는지 separate host-level assertion 필요 |
| Stage3 `from_app()`의 plain `getattr` auto-attr hazard | 기결 | `MPN-T5-004`가 이미 retained. T4에서는 재오픈하지 않음 |

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- `PASS1 -> PASS2 -> PASS3` 요약 포함
