# [MLW-T5] Test Realism / Fake App Regression Findings

> 작성일: 2026-03-13
> 작성자: `codex-terminal-5`
> 상태: `PASS 3 re-audited / supersedes prior OPUS draft`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-live-wiring-contract-detail-full-survey-audit-order.md`
> 참고 문서:
> - `docs/2026-03-13/MFS-T5-protocol-tests-regression-findings.md`
> - `docs/2026-03-13/MRF-T5-consumer-tests-regression-findings.md`
> - `docs/2026-03-13/MPN-T5-consumer-tests-legacy-contract-findings.md`

---

## 조사 범위

- `tests/test_stage2_context.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_resume_status.py`
- `tests/test_main_a_rollback.py`
- `tests/test_main_a_stage_entry_contracts.py`
- `tests/test_main_a_boot_binding.py`
- `tests/test_run_stage4_canary.py`
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- `main_a.py`

## 추가 검증 실행

- `pytest -q tests/test_stage2_context.py` -> `19 passed in 1.38s`
- `pytest -q tests/test_stage3_orchestrator.py::TestStage3ContextDI` -> `10 passed in 1.18s`
- `pytest -q tests/test_stage4_context.py` -> `16 failed, 3 passed, 12 errors in 2.77s`
- `pytest -q tests/test_main_a_stage_entry_contracts.py` -> `1 failed, 3 passed in 1.89s`
- `python -` minimal `Stage4Context.from_app(app)` smoke -> `AttributeError: 'Stage4Context' object has no attribute 'generate_writer_guidance_v60_8'`

---

## PASS 기록

- PASS 1: 후보 7건 식별
  - Stage4Context green baseline 붕괴
  - Stage2 `from_app()` positive pin coverage 과소
  - Stage4 `from_app()` residual blind spot
  - Stage3 benchmark 유효성 재검증 필요
  - source-string assertion 과의존
  - `SimpleNamespace` fake app 확산
  - lambda / inline stub 과다 사용
- PASS 2: 후보 3건 제거
  - Stage4 residual blind spot은 `MLW-T5-001`의 후속 coverage gap으로 흡수
  - Stage3 benchmark 후보는 `MPN-T5-004`와 실질 중복이라 재오픈하지 않음
  - lambda 후보는 범위가 너무 넓고 `MRF-*`, `MCP-*` 문서가 이미 더 직접적인 경계를 고정하고 있어 제거
- PASS 3: 최종 4건 확정

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| MLW-T5-001 | P0 | confirmed | `modules/core/stage4_context.py`, `tests/test_stage4_context.py`, `tests/test_main_a_stage_entry_contracts.py` | Stage4Context는 테스트 blind spot이 아니라 현재 live `from_app()` 생성 자체가 깨져 있다 |
| MLW-T5-002 | P1 | confirmed | `modules/core/stage2_context.py::from_app`, `tests/test_stage2_context.py` | Stage2 `from_app()` 50슬롯 중 positive pinning은 15개뿐이며, spec-less `MagicMock`이 나머지 35개 drift를 숨긴다 |
| MLW-T5-003 | P2 | confirmed | 14개 테스트 파일, 47개 `inspect.getsource` | live wiring 회귀 가드가 여전히 코드 모양 고정에 과의존한다 |
| MLW-T5-004 | P3 | confirmed | 34개 테스트 파일, 158개 `SimpleNamespace(` | `SimpleNamespace` surrogate가 control-plane / wrapper surface에서 실제 `SovereignApp` 구조 검증을 대체한다 |

---

## Findings

### [MLW-T5-001] Stage4Context는 blind spot 이전에 현재 live `from_app()` 생성부터 깨져 있다

1. ID
- `MLW-T5-001`

2. Severity
- `P0`

3. 현상 요약
- 기존 초안은 Stage4를 "green test 뒤에 숨은 blind spot"으로 분류했지만, PASS 2 실행 검증 결과 이 전제가 틀렸다.
- `Stage4Context.__slots__`에는 `generate_writer_guidance_v60_8`, `enrich_director_result`가 선언돼 있지 않다.
- 그런데 `__init__()`는 두 속성에 값을 대입하고, `from_app()`도 두 콜백을 바인딩한다.
- 그 결과 `Stage4Context(...)` 직접 생성, `Stage4Context.from_app(app)`, `main_a.SovereignApp._stage_4_v2_chief_writer()` wrapper 경로가 모두 즉시 `AttributeError`로 깨진다.
- 즉 이 표면은 "테스트가 초록인데 놓치는 위험"이 아니라, 현재 test/runtime 양쪽에서 이미 붉은 상태다.

4. 코드 근거
- `modules/core/stage4_context.py:45-80` — `__slots__` 선언에 두 이름이 없다
- `modules/core/stage4_context.py:115-116` — `generate_writer_guidance_v60_8`, `enrich_director_result` init 파라미터 선언
- `modules/core/stage4_context.py:148-149` — undeclared slot에 직접 대입
- `modules/core/stage4_context.py:195-196` — `from_app()`도 두 콜백을 바인딩
- `tests/test_stage4_context.py:147-148` — 두 속성이 존재한다고 전제
- `tests/test_stage4_context.py:171-183` — `from_app()`가 두 콜백을 추출한다고 전제
- `main_a.py:3544` — Stage4 wrapper가 `Stage4Context.from_app(self)`를 직접 호출
- `tests/test_main_a_stage_entry_contracts.py:22-69` — wrapper contract test가 동일 `AttributeError`로 실패

5. downstream 영향 경계
- `Stage4Context.from_app(app)` 직접 호출 경로
- `Stage4Orchestrator.ctx` auto-build 경로
- `main_a.SovereignApp._stage_4_v2_chief_writer()` Stage4 wrapper 진입
- `tests/test_stage4_context.py` 전체 기반 회귀망

6. 현재 테스트 근거 또는 테스트 부재
- 테스트 부재가 아니라 테스트 실패다.
- `pytest -q tests/test_stage4_context.py` 결과: `16 failed, 3 passed, 12 errors`
- `pytest -q tests/test_main_a_stage_entry_contracts.py` 결과: `test_stage4_wrapper_builds_context_from_app_and_preserves_session_logger` 포함 `1 failed, 3 passed`
- minimal smoke에서도 `Stage4Context.from_app(app)`가 즉시 `AttributeError`를 낸다.

7. 기존 문서와의 중복 여부
- `none`
- `MLW-T3`, 기존 OPUS 초안, prior MLW-T5 초안 모두 Stage4Context를 blind spot으로 기술했지만, 현재의 직접 생성 실패는 고정하지 못했다.

8. 권장 후속 조치
- `Stage4Context.__slots__`에 `generate_writer_guidance_v60_8`, `enrich_director_result`를 추가하거나, 반대로 `__init__`/`from_app()`에서 해당 대입 자체를 제거해 계약을 일치시킨다.
- 그 후 `tests/test_stage4_context.py`와 `tests/test_main_a_stage_entry_contracts.py`를 다시 실행해 green baseline을 복구해야 한다.
- baseline이 복구된 뒤에야 Stage4 blind spot(아래 Coverage Gap)을 다시 논할 수 있다.

---

### [MLW-T5-002] Stage2 `from_app()`는 50슬롯 중 15개만 positive pinning되고, 나머지 35개는 drift에 열린 상태다

1. ID
- `MLW-T5-002`

2. Severity
- `P1`

3. 현상 요약
- `Stage2Context.__slots__` 실제 개수는 50개다.
- 그러나 `tests/test_stage2_context.py`가 `from_app()` 경로에서 positive assertion으로 pinning하는 unique slot은 15개뿐이다.
- pinning된 15개는 필수 5종, 직접 지정한 callback 6종, `context_advisor`, fallback callback 3종이다.
- 나머지 35개 슬롯은 rename/삭제/미배선이 일어나도 현재 회귀망이 positive assertion으로 잡아 주지 못한다.
- fixture는 `app = MagicMock()` (spec 없음)이므로, 미설정 속성은 auto-created mock으로 채워져 drift를 더 쉽게 숨긴다.

4. 코드 근거
- `modules/core/stage2_context.py:134-190` — `Stage2Context.__slots__`
- `python -c ... len(Stage2Context.__slots__)` 확인 결과 `50`
- `tests/test_stage2_context.py:33` — `app = MagicMock()` spec 없음
- `tests/test_stage2_context.py:54-61` — 필수 5종만 pinning
- `tests/test_stage2_context.py:91-106` — callback 6종 pinning
- `tests/test_stage2_context.py:127-130` — `context_advisor` pinning
- `tests/test_stage2_context.py:148-167` — fallback callback 4종 중 3종만 신규 pinning (`generate_arc_context_v60`는 중복)

5. downstream 영향 경계
- `selected_genre`, `preset_registry`, `perf_timer`, `failure_learner`, `memory`, `stage2_optimizer`
- `arc_draft_validator`, `arc_corrector`, `constraint_compiler`, `pass_rate_monitor`, `quality_dashboard`
- `write_audit_summary`, `validate_arc_mapping`, `validate_arc_integrity`, `state_tracker_loaded_arcs`
- `calculate_arc_from_episode`, `generate_structured_arc_feedback`, `fix_entity_registry_protagonist`
- `sync_cache_key_to_app`, `retry_feedback_contract`, `retry_feedback_missing_callbacks`, `session_logger`

6. 현재 테스트 근거 또는 테스트 부재
- `pytest -q tests/test_stage2_context.py`는 `19 passed in 1.38s`로 green이다.
- 그러나 green 이유는 "전 슬롯 계약이 잠겼기 때문"이 아니라, positive pinning 범위가 좁고 fixture가 spec-less mock이기 때문이다.
- 특히 unpinned slot은 `from_app(real_app)`나 attribute whitelist fixture와 대조되지 않는다.

7. 기존 문서와의 중복 여부
- `related-but-new-live-wiring-surface`
- `MLW-T1-002`가 Stage2 general mock-realism 문제를 지적했다면, 본 finding은 그중에서도 `from_app()` regression net이 실제로 15/50만 고정한다는 정량 경계를 별도로 고정한다.

8. 권장 후속 조치
- `tests/test_stage2_context.py`에 Stage3형 `test_from_app_all_slots()`를 추가해 50슬롯 전량을 identity 기준으로 고정한다.
- `app_mock`는 `MagicMock(spec=[...])` 또는 명시적 fake app 클래스로 교체한다.
- 최소한 `write_audit_summary`, `validate_arc_mapping`, `calculate_arc_from_episode`, `sync_cache_key_to_app`, `session_logger`는 우선 pinning 대상이다.

---

### [MLW-T5-003] live wiring 회귀 가드가 여전히 `inspect.getsource` 47회에 과의존한다

1. ID
- `MLW-T5-003`

2. Severity
- `P2`

3. 현상 요약
- `tests/` 전체에서 `inspect.getsource(...)` 호출은 47개, 관련 파일은 14개다.
- 이 중 live wiring 관점에서 가장 중요한 가드는 여전히 Stage4 DI 계열이다.
- 예를 들어 `tests/test_stage4_context_builder.py`는 `self.app` 문자열이 없어야 하고 `self.ctx.semantic_plot_guard` 문자열이 있어야 한다는 식으로 회귀를 잠근다.
- `tests/test_stage4_interview_round.py`도 `Stage4InterviewRound` 소스에 `self.app` 문자열이 없어야 한다는 형태로 확인한다.
- 이런 가드는 코드 모양은 잠그지만, 실제 `from_app()` 생성 성공 여부나 callback wiring semantics는 보장하지 않는다.

4. 코드 근거
- 저장소 전수 계수: `inspect.getsource` `47`회 / `14`개 파일
- `tests/test_stage4_context_builder.py:644-646`
- `tests/test_stage4_interview_round.py:2412-2413`
- 추가 사용처 예시:
  - `tests/test_stage234_fixes.py:19,27,43,64,72,86`
  - `tests/test_pipeline_audit_00.py:18,163,216,231,244`
  - `tests/test_stage01_fixes.py:73,82,118,128,149,157,168,179,190`
  - `tests/test_stage0_fixes.py:26,34,40,46,52,76,82,89,102,162`

5. downstream 영향 경계
- Stage4 DI 전환 regression guard
- Stage0/1/2 helper extraction guard
- validation / audit callback refactor
- 리팩터링 저항 증가 + 의미적 drift 미검출

6. 현재 테스트 근거 또는 테스트 부재
- 현재 테스트는 존재한다. 문제는 테스트 종류다.
- `inspect.getsource` 기반 가드는 리팩터링에 매우 민감하지만, `MLW-T5-001`처럼 실제 객체 생성이 깨진 상태는 별도로 막아 주지 못했다.
- behavioral seam을 타는 contract test가 부족하다.

7. 기존 문서와의 중복 여부
- `related-but-new-live-wiring-surface`
- `MCP-T5-004`가 control-plane 일반론을 다뤘다면, 본 finding은 live wiring / DI 전환 guard에 직접 걸린 47회 사용량과 핵심 파일을 다시 고정한다.

8. 권장 후속 조치
- `inspect.getsource` 가드는 보조 가드로만 남기고, 동일 계약을 실제 객체 생성/메서드 호출 기반 test로 이중화한다.
- 우선순위는 `tests/test_stage4_context_builder.py`, `tests/test_stage4_interview_round.py`, `tests/test_stage234_fixes.py`다.

---

### [MLW-T5-004] `SimpleNamespace` surrogate가 wrapper/control-plane 표면에서 실제 `SovereignApp` 구조 검증을 대체한다

1. ID
- `MLW-T5-004`

2. Severity
- `P3`

3. 현상 요약
- `tests/` 전체에서 `SimpleNamespace(` 사용은 158회, 관련 파일은 34개다.
- 이 중 `app = SimpleNamespace(...)` 형태의 direct app surrogate만 잡아도 21회, 7개 파일이다.
- 대표적으로 `tests/test_resume_status.py`, `tests/test_main_a_rollback.py`, `tests/test_main_a_stage_entry_contracts.py`, `tests/test_main_a_boot_binding.py`, `tests/test_run_stage4_canary.py`가 여기에 해당한다.
- 이 패턴은 unbound method를 빠르게 검증하는 데는 유용하지만, `SovereignApp` 속성명/구조가 바뀌어도 fixture가 즉시 깨지지 않는다는 점에서 regression realism이 낮다.

4. 코드 근거
- 저장소 전수 계수: `SimpleNamespace(` `158`회 / `34`개 파일
- direct app surrogate: `app = SimpleNamespace(...)` `21`회 / `7`개 파일
- 예시:
  - `tests/test_resume_status.py:14,33,55,92,125,156`
  - `tests/test_main_a_rollback.py:12,56,86,116,138`
  - `tests/test_main_a_stage_entry_contracts.py:11,24,79,103`
  - `tests/test_run_stage4_canary.py:8,35`

5. downstream 영향 경계
- `_show_resume_status`, `_shutdown_app`, rollback/reset 계열 unbound method 테스트
- Stage entry wrapper contract 테스트
- canary / one-stop wrapper 테스트

6. 현재 테스트 근거 또는 테스트 부재
- 관련 테스트 다수는 green이다.
- 다만 이 green은 method body 동작을 빠르게 검증한다는 의미이지, `SovereignApp` 실제 public/private surface와 parity가 잠겼다는 뜻은 아니다.
- 특히 Stage4 wrapper 실패 사례에서도 surrogate app가 충분히 production-like였기 때문에 code bug는 드러났지만, 더 미세한 attribute drift는 여전히 놓칠 수 있다.

7. 기존 문서와의 중복 여부
- `related-but-new-live-wiring-surface`
- `MCP-T5`, `MPN-T5`가 일부 개별 사례를 다뤘다면, 본 finding은 T5 범위에서 direct surrogate 사용량을 다시 계수해 wrapper/control-plane risk로 묶는다.

8. 권장 후속 조치
- control-plane 핵심 테스트는 `SimpleNamespace`를 전부 없애라는 뜻이 아니다.
- 대신 Stage entry / shutdown / rollback처럼 live wiring 계약을 확인해야 하는 테스트에는 최소 속성 whitelist 검증 또는 명시적 fake `SovereignApp` fixture를 추가한다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| Stage4 actual slot coverage after blocker fix | open | `memory`, `world_state`, `fact_ledger`, `character_voice`, `perf_timer`, `foreshadow_tracker`, `failure_learner`, `diversity_engine`, `semantic_plot_guard`, `selected_genre`, `quality_dashboard`, `pacing_analyzer`, `emotion_tracker`, `session_logger` 14개 actual slot에 대한 positive pinning 추가 |
| Stage3 `test_from_app_all_slots()` benchmark validity | partial / already-covered | 현재 24슬롯 전량 assertion은 있으나 `adversarial_self_play` auto-attribute caveat는 `MPN-T5-004`가 이미 고정 |
| live wrapper test parity with real `SovereignApp` | partial | `SimpleNamespace` surrogate 대신 최소 fake app 클래스로 Stage2/3/4 wrapper parity 검증 필요 |
| source-string guard replacement priority | open | `test_stage4_context_builder.py`, `test_stage4_interview_round.py`에 behavior-first regression 추가 |

## 정량 요약

| 항목 | 수치 |
|------|------|
| `tests/**/*.py` 스캔 파일 수 | 286 |
| `MagicMock(` 호출 | 2,233 |
| same-line `MagicMock(...spec...)` | 20 |
| `inspect.getsource(` | 47 / 14개 파일 |
| `SimpleNamespace(` | 158 / 34개 파일 |
| `app = SimpleNamespace(...)` | 21 / 7개 파일 |
| `Stage2Context.__slots__` | 50 |
| Stage2 `from_app()` positive pinning | 15 / 50 |
| `Stage3Context.__slots__` | 24 |
| `Stage4Context.__slots__` | 30 |
| `tests/test_stage4_context.py` | 16 failed, 3 passed, 12 errors |

## PASS 요약

- PASS1 후보 7건 -> PASS2 제거 3건 -> PASS3 확정 4건
- prior OPUS 초안의 핵심 오류는 `Stage4Context`를 green blind spot으로 본 점이다. 재검증 결과 Stage4는 blind spot 이전에 baseline 자체가 적색이다.
- retained 최고 위험도는 `MLW-T5-001(P0)`이며, 이는 test realism 문제가 아니라 Stage4 live wiring 생성 실패다.
- 그 외 T5 본류 위험은 여전히 `spec-less mock`, `source-string guard`, `SimpleNamespace surrogate` 조합이 live wiring drift를 충분히 pinning하지 못한다는 점이다.

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- PASS1 -> PASS2 -> PASS3 요약 포함
