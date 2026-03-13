# [MLW-T5] Test Realism / Fake App Regression Findings

> 작성일: 2026-03-13
> 작성자: `claude-opus-4-6`
> 상태: `PASS 3 complete / confirmed`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-live-wiring-contract-detail-full-survey-audit-order.md`
> 참고: `MFS-T5-protocol-tests-regression-findings.md`

---

## 조사 범위

- `tests/` 전반의 `MagicMock`, `SimpleNamespace`, lambda, `inspect.getsource` 기반 테스트
- `Stage2Context.from_app()`, `Stage3Context.from_app()`, `Stage4Context.from_app()` 테스트 커버리지
- 기존 감리 문서 9건과의 중복 대조
- source-string assertion 계열 DI 회귀 가드

## 필수 근거

- `tests/test_stage2_context.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_context.py`
- `tests/test_resume_status.py`
- `docs/2026-03-13/MFS-T5-protocol-tests-regression-findings.md`
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`

## PASS 기록

- PASS 1: 후보 7건 식별
  - Stage2 `from_app()` 75% slot blind spot (36/48 untested)
  - Stage4 `from_app()` 48% slot blind spot (14/29 untested)
  - spec-less `MagicMock()` in context from_app tests enabling false green
  - `SimpleNamespace` fake app in control-plane tests (25 files, 246 instances)
  - source-string assertions as single-point DI guards (47 occurrences, 14 files)
  - lambda `side_effect` masking callback signature drift (25 files)
  - Stage3 spec-less MagicMock with 100% assertion (positive finding)
- PASS 2: 후보 3건 제거
  - spec-less `MagicMock` 후보는 MLW-T5-001/002의 contributing mechanism으로 병합 (독립 finding 불요)
  - lambda `side_effect` 후보는 MRF-T5-002, MCP-T2-02와 범위 중첩 + live-wiring-contract보다 일반 test hygiene 영역이므로 제거
  - Stage3 positive finding은 finding이 아니라 benchmark 참조로 전환
- PASS 3: 최종 4건 확정

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| MLW-T5-001 | P1 | confirmed | `tests/test_stage2_context.py`, `modules/core/stage2_context.py::from_app` | Stage2 `from_app()` 48슬롯 중 36개(75%)가 테스트 미검증 — spec-less `MagicMock`이 app surface drift를 은닉한다 |
| MLW-T5-002 | P1 | confirmed | `tests/test_stage4_context.py`, `modules/core/stage4_context.py::from_app` | Stage4 `from_app()` 29슬롯 중 14개(48%)가 테스트 미검증 — critical `world_state`/`fact_ledger` 포함 |
| MLW-T5-003 | P2 | confirmed | 14개 테스트 파일, 47개 `inspect.getsource` 호출 | DI-wiring source-string assertion이 단일 장벽으로 존재하며 비의미적 소스 변경에 깨진다 |
| MLW-T5-004 | P3 | confirmed | `tests/test_resume_status.py`, `tests/test_main_a_rollback.py` 등 25개 파일 | `SimpleNamespace` fake app가 246개소에서 구조 검증 없이 `SovereignApp` 표면을 대체한다 |

---

## Findings

### [MLW-T5-001] Stage2 `from_app()` 75% slot blind spot — spec-less MagicMock이 false green을 만든다

1. ID
- `MLW-T5-001`

2. Severity
- `P1`

3. 현상 요약
- `Stage2Context.from_app()`는 48개 슬롯을 `SovereignApp`에서 추출한다 (필수 5 + 확장 19 + 콜백 22 + sync 1 + logger 1).
- `tests/test_stage2_context.py`의 `from_app` 관련 테스트는 이 중 **12개만 검증**한다 (필수 5 + 콜백 6 + context_advisor 1).
- **36개 슬롯이 테스트되지 않는다.** 여기에는:
  - 확장 모듈 18개: `selected_genre`, `preset_registry`, `perf_timer`, `semantic_plot_guard`, `failure_learner`, `memory`, `stage2_optimizer`, `arc_draft_validator`, `arc_corrector`, `constraint_compiler`, `stage_rejection_history`, `pass_rate_monitor`, `quality_dashboard`, `quality_amplifier`, `agent_intelligence`, `constitutional_checker`, `self_reflector`, `adversarial_self_play`
  - 콜백 16개: `cumulative_state_cache`, `cumulative_state_cache_key`, `write_audit_summary`, `validate_arc_mapping`, `validate_arc_integrity`, `state_tracker_loaded_arcs`, `get_max_episode_from_manuscripts`, `generate_structured_arc_feedback`, `generate_reverse_feedback_stage3_to_2`, `fix_entity_registry_protagonist`, `calculate_arc_from_episode`, `build_strong_kind_feedback`, `build_minimal_arc_context`, `analyze_rejection_pattern_v60`, `get_adaptive_feedback_intensity`, `use_arc_corrector`
  - 인프라 2개: `sync_cache_key_to_app` (weakref 콜백), `session_logger`
- `app_mock`은 `MagicMock()` (spec 없음)이므로, `from_app()`에서 `getattr(app, "_missing_method_name", None)` 대신 `getattr(app, "_any_typo", None)` → MagicMock auto-attribute가 반환되어 `None`이 아닌 MagicMock 객체가 슬롯에 주입된다.
- 대조적으로 **Stage3**는 `test_from_app_all_slots()` (L983-1011)에서 24개 전 슬롯을 100% 검증하며 이것이 benchmark다.

4. 코드 근거
- `from_app()` 전체 매핑: `modules/core/stage2_context.py:207-259` (48 슬롯)
- 테스트 `from_app` 검증: `tests/test_stage2_context.py:54-61` (필수 5종만) + `tests/test_stage2_context.py:91-106` (콜백 6종만) + `tests/test_stage2_context.py:122-126` (context_advisor 1종)
- spec-less fixture: `tests/test_stage2_context.py:32` — `app = MagicMock()` (spec 미지정)
- Stage3 benchmark: `tests/test_stage3_orchestrator.py:983-1011` — 24개 전 슬롯 검증

5. downstream 영향 경계
- `main_a.py`에서 `_validate_arc_mapping`, `_generate_structured_arc_feedback` 등의 메서드가 rename/삭제되어도 Stage2 from_app 테스트는 초록으로 남는다
- `sync_cache_key_to_app` weakref 콜백이 잘못 구성되어도 테스트가 감지하지 못한다
- Stage2 품질/검증 모듈 18개의 실제 app 바인딩이 drift해도 테스트가 초록으로 남는다

6. 현재 테스트 근거 또는 테스트 부재
- 존재: 필수 5종 identity 검증, 콜백 6종 identity 검증, optional None 기본값 검증, `MagicMock(spec=[])` app에서 callback=None 검증
- 부재: 확장 모듈 18종 from_app 추출 검증, 콜백 16종 from_app 추출 검증, `sync_cache_key_to_app` 실행 검증, `session_logger` 추출 검증

7. 기존 문서와의 중복 여부
- `related-but-new-live-wiring-surface`
- MRF-T5-001은 retry-feedback 콜백 부분집합만 다룬다. 이번 finding은 전체 48 슬롯의 from_app 추출 커버리지를 live-wiring 관점에서 전수 측정한 것이며 MRF-T5-001보다 넓고 직접적이다.

8. 권장 후속 조치
- Stage3 `test_from_app_all_slots()` 패턴을 복제해 `test_stage2_context.py`에 `test_from_app_all_slots_comprehensive()` 추가 — 48개 전 슬롯 assertion
- `app_mock` fixture에 `spec=[]` 대신 실제 `SovereignApp` attribute 목록을 명시적으로 설정하거나, 최소한 `from_app` 테스트에서 모든 슬롯의 identity를 검증
- `sync_cache_key_to_app` weakref 콜백은 별도 focused test 추가 (weakref deref + state mutation 확인)

---

### [MLW-T5-002] Stage4 `from_app()` 48% slot blind spot — critical `world_state`/`fact_ledger` 미검증

1. ID
- `MLW-T5-002`

2. Severity
- `P1`

3. 현상 요약
- `Stage4Context.from_app()`는 29개 슬롯을 추출한다 (필수 5 + 확장 14 + conditional_modules 1 + 콜백 7 + logger 1 + budget_meta 1).
- `tests/test_stage4_context.py`의 `from_app` 관련 테스트는 이 중 **15개만 검증**한다.
- **14개 슬롯이 테스트되지 않는다:**
  - `memory`, `world_state`, `fact_ledger` — 서사 연속성의 핵심 인프라
  - `character_voice`, `perf_timer`, `foreshadow_tracker`, `failure_learner`, `diversity_engine`, `semantic_plot_guard` — 분석/추적 모듈
  - `quality_dashboard`, `pacing_analyzer`, `emotion_tracker` — 품질 모듈
  - `selected_genre` — 장르 가드 바인딩
  - `session_logger` — 세션 로깅
- `world_state`와 `fact_ledger`는 Chief Writer가 서사 모순 검사에 사용하는 핵심 모듈이다. 이 슬롯이 None으로 주입되면 TruthGate/NpcDrift/NumericDrift advisory가 무력화된다.

4. 코드 근거
- `from_app()` 전체 매핑: `modules/core/stage4_context.py:139-179` (29 슬롯)
- 테스트 검증: `tests/test_stage4_context.py:55-62` (필수 5), `tests/test_stage4_context.py:85-89` (context_advisor), `tests/test_stage4_context.py:114-122` (conditional_modules 2종), `tests/test_stage4_context.py:134-138` (pass_rate_monitor), `tests/test_stage4_context.py:162-179` (콜백 7종)
- 미검증 슬롯: `world_state` (L158), `fact_ledger` (L159), `character_voice` (L160), `perf_timer` (L161), `foreshadow_tracker` (L162), `failure_learner` (L163), `diversity_engine` (L164), `semantic_plot_guard` (L165), `selected_genre` (L166), `quality_dashboard` (L167), `pacing_analyzer` (L168), `emotion_tracker` (L169), `memory` (L155), `session_logger` (L178)

5. downstream 영향 경계
- Stage4 advisory chain 8개 (TruthGate, NpcDrift, NumericDrift, Flashback, InfoParadox, RelDrift, LongTermRep, NumericConsistency)가 `world_state`/`fact_ledger` 의존
- Chief Writer context builder가 `foreshadow_tracker`, `character_voice` 의존
- Director quality audit가 `quality_dashboard`, `pacing_analyzer` 의존
- 이 슬롯들이 `main_a.py`에서 rename/삭제되어도 테스트는 초록으로 남는다

6. 현재 테스트 근거 또는 테스트 부재
- 존재: 필수 5종, context_advisor, pass_rate_monitor, conditional_modules (부분), 콜백 7종 전량
- 부재: 확장 모듈 12종 from_app 추출, session_logger 추출

7. 기존 문서와의 중복 여부
- `related-but-new-live-wiring-surface`
- MPN-T5-003/004는 persistence helper와 Stage3 DI 관점. Stage4의 from_app 슬롯 커버리지를 전수 측정한 finding은 본건이 최초다.

8. 권장 후속 조치
- Stage3 `test_from_app_all_slots()` 패턴을 복제해 `test_stage4_context.py`에 29개 전 슬롯 assertion 추가
- conditional_modules 8종 source key 전량 검증 추가 (현재 2종만 테스트)
- `world_state`, `fact_ledger` 추출을 별도 focused test로 강화 (None 주입 시 advisory chain 무력화 경로 확인)

---

### [MLW-T5-003] DI-wiring source-string assertion이 단일 장벽으로 존재하며 비의미적 소스 변경에 깨진다

1. ID
- `MLW-T5-003`

2. Severity
- `P2`

3. 현상 요약
- 14개 테스트 파일에서 47개의 `inspect.getsource()` 호출이 DI 리팩토링 회귀 가드로 사용된다.
- 대표 예시:
  - `test_stage4_context_builder.py:614-616`: `assert "self.app" not in source` / `assert "self.ctx.semantic_plot_guard" in source`
  - `test_stage4_interview_round.py:2388-2389`: `assert "self.app" not in source`
  - `test_sweep23.py:15-16`: `assert re.search(r"protagonist_name\s*=\s*None\s*\n\s*genre\s*=\s*\"\"\s*\n\s*try:", src)`
- 이 assertions는 Phase 4C DI 전환의 유일한 회귀 가드인 경우가 많다. 별도의 behavioral test가 같은 계약을 잠그지 않는다.
- 문제: 소스 포맷 변경 (줄바꿈, 주석 추가, 메서드 인라인/추출, black/ruff 포맷팅), 또는 메서드가 부모 클래스로 이동하면 assertion이 깨지거나 (false negative) 의미 없이 통과한다 (false positive).
- source-string assertion은 wiring contract가 아니라 코드 모양을 잠그므로, real app path에서의 DI 동작을 보장하지 못한다.

4. 코드 근거
- DI 전환 가드: `tests/test_stage4_context_builder.py:614-616`
- DI 전환 가드: `tests/test_stage4_interview_round.py:2388-2389`
- 초기화 순서 가드: `tests/test_sweep23.py:15-16`
- 체크포인트 로직 가드: `tests/test_pipeline_audit_00.py:163, 216, 231, 244`
- 장르 가드: `tests/test_stage01_fixes.py:73, 82, 118, 128, 149, 157, 168, 179, 190`
- Stage0 가드: `tests/test_stage0_fixes.py:26, 34, 40, 46, 52, 76, 82, 89, 102, 162`
- 추가 10건: `test_npc_info_chain.py`, `test_single_candidate_monopoly.py`, `test_semantic_plot_guard.py`, `test_satisfaction_step3_tagging.py`, `test_satisfaction_step4_frustration.py`, `test_stage234_fixes.py`, `test_validator_bypass_chain.py`

5. downstream 영향 경계
- Phase 4C DI 전환 회귀 보호 (Stage4 context builder, interview round)
- Stage0/1/2 초기화 순서 보호
- 검증 파이프라인 체크포인트 보호
- 이 가드들이 false positive/negative로 전환되면 DI regression이 감지되지 않는다

6. 현재 테스트 근거 또는 테스트 부재
- 존재: 14개 파일, 47개 `inspect.getsource` 호출이 코드 모양을 잠근다
- 부재: 같은 DI 계약을 behavioral test (actual method call + assertion)로 잠그는 테스트가 대부분 없다. source-string이 유일한 가드인 경우가 다수.

7. 기존 문서와의 중복 여부
- `related-but-new-live-wiring-surface`
- MCP-T5-004는 control-plane 회귀망의 source-string 과의존을 일반 관점에서 다룬다. 이번 finding은 DI-wiring 전환 가드에 한정해 47개 호출의 구체적 범위와 단일 장벽 위험을 측정한 것이며 MCP-T5-004보다 좁고 직접적이다.

8. 권장 후속 조치
- 각 source-string assertion에 대응하는 behavioral test를 추가 (예: `Stage4ContextBuilder.build_mandatory_context(ctx)` 호출 후 `ctx.semantic_plot_guard` 경유 확인)
- source-string assertion 자체는 보조 가드로 유지 가능하나, 단일 장벽이 되지 않도록 behavioral 보완 필요
- 우선순위: `test_stage4_context_builder.py`, `test_stage4_interview_round.py`의 DI 전환 가드부터 보완

---

### [MLW-T5-004] `SimpleNamespace` fake app가 구조 검증 없이 `SovereignApp` 표면을 대체한다

1. ID
- `MLW-T5-004`

2. Severity
- `P3`

3. 현상 요약
- 25개 테스트 파일에서 246개소의 `SimpleNamespace`가 `SovereignApp` 또는 그 하위 객체 (db, project, ui) 역할을 대체한다.
- 대표 예시:
  - `test_resume_status.py:8-14`: `app = SimpleNamespace(current_project=project, ui=ui)` → `SovereignApp._show_resume_status(app)` 호출
  - `test_resume_status.py:55-64`: `app = SimpleNamespace(_PROJECTS_DIR=..., pass_rate_monitor=..., ...)` → `SovereignApp._shutdown_app(app)` 호출
  - `test_main_a_rollback.py:31-40`: 깊은 중첩 `SimpleNamespace` 구성
- `SimpleNamespace`는 어떤 속성이든 오류 없이 설정/읽기가 가능하므로, `SovereignApp`에서 속성명이 변경되거나 구조가 바뀌어도 테스트는 초록으로 남는다.
- 다만, 이 패턴은 unbound method 테스트에서 의도적으로 사용되며 (Python의 `SovereignApp.method(fake_self)` 패턴), DI context `from_app` 테스트와는 다른 목적을 가진다.

4. 코드 근거
- `test_resume_status.py:8-14, 26-30, 44-64, 73-103, 112-134, 143-165` (6개 테스트 함수)
- `test_main_a_rollback.py` (15 MagicMock + 20 SimpleNamespace)
- `test_main_a_stage_entry_contracts.py` (14 SimpleNamespace)
- `test_main_a_boot_binding.py` (6 SimpleNamespace)
- 기타 21개 파일 (protocols, sweep, e2e 등)

5. downstream 영향 경계
- `_show_resume_status`, `_shutdown_app` 등 control-plane 메서드의 regression 보호
- `SovereignApp` 속성명 rename 시 해당 테스트가 감지하지 못함
- 다만 이 메서드들은 DI context가 아닌 직접 app 표면을 사용하므로 영향 범위가 control-plane에 한정

6. 현재 테스트 근거 또는 테스트 부재
- 존재: 개별 메서드의 happy/error path가 SimpleNamespace fixture로 검증됨
- 부재: `SovereignApp`의 실제 속성 목록과 SimpleNamespace fixture 사이의 drift 검증이 없음

7. 기존 문서와의 중복 여부
- `related-but-new-live-wiring-surface`
- 기존 문서에서 SimpleNamespace fake app 패턴 자체를 독립 finding으로 다룬 문서는 없다. MPN-T5-004는 MagicMock auto-attribute을, MFS-T2-002는 facade bound-method drift를 다루며 SimpleNamespace와는 다른 메커니즘이다.

8. 권장 후속 조치
- 긴급도 낮음. SimpleNamespace는 unbound method 테스트에서 유효한 패턴이며, 해당 테스트들의 목적은 method 내부 로직 검증이다.
- 중장기: 핵심 control-plane 테스트 (`_shutdown_app`, `_show_resume_status`)에 `SovereignApp` 최소 필수 속성 목록을 fixture-level에서 검증하는 guard 추가 고려
- `SovereignApp`의 public/private attribute 목록을 SSOT로 관리하고 fixture에서 참조하는 방식 검토

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| Stage2 `from_app()` 전 슬롯 검증 | **75% 미검증** | Stage3 benchmark 복제 → 48개 전 슬롯 assertion test |
| Stage4 `from_app()` 전 슬롯 검증 | **48% 미검증** | Stage3 benchmark 복제 → 29개 전 슬롯 assertion test |
| `sync_cache_key_to_app` weakref 콜백 | **미검증** | weakref deref + state mutation focused test |
| DI source-string assertion behavioral 보완 | **47개 단일 장벽** | behavioral test 추가로 이중 가드 구성 |
| SimpleNamespace fixture drift 검증 | **미검증** | SovereignApp 속성 목록 SSOT fixture |
| Stage3 `from_app()` 전 슬롯 검증 | **100% (benchmark)** | 유지 — 변경 불요 |

## Benchmark 참조

Stage3의 `test_from_app_all_slots()` (`tests/test_stage3_orchestrator.py:983-1011`)가 from_app 테스트의 표준이다:
- 24개 전 슬롯을 `is` identity로 검증
- app_mock은 spec-less MagicMock이지만 **모든 슬롯을 assertion으로 pin**하므로 drift가 감지된다
- Stage2/4에 이 패턴을 복제하면 MLW-T5-001/002가 해소된다

## 정량 요약

| 항목 | 수치 |
|------|------|
| spec-less `MagicMock()` (tests 전체) | ~1,594개소 / 40개 파일 |
| spec 있는 `MagicMock(spec=...)` | 19개소 / 9개 파일 |
| `SimpleNamespace` fake app | 246개소 / 25개 파일 |
| `inspect.getsource` assertions | 47개소 / 14개 파일 |
| Stage2 `from_app` 슬롯 커버리지 | 12/48 (25%) |
| Stage3 `from_app` 슬롯 커버리지 | 24/24 (100%) — benchmark |
| Stage4 `from_app` 슬롯 커버리지 | 15/29 (52%) |

## PASS 요약

- PASS1 후보 7건 → PASS2 제거 3건 → PASS3 확정 4건
- 핵심 위험: Stage2/4의 `from_app()` 슬롯 커버리지가 25%/52%로, spec-less MagicMock과 결합해 app surface drift를 은닉한다. Stage3가 100% benchmark로 존재하므로 복제 가능하다.
- 이미 닫힌 일반 mock-realism finding (MFS-T5-001/002, MPN-T5-003/004, MCP-T5-003/004, MRF-T5-001/002)은 재오픈하지 않았다.
- 신규 4건은 모두 `related-but-new-live-wiring-surface`로 기존 문서와 책임 경계가 분리된다.

## 마감 체크

- [x] 코드 근거 포함
- [x] downstream 영향 경계 포함
- [x] 현재 테스트 근거 또는 테스트 부재 포함
- [x] 기존 문서와의 중복 여부 포함
- [x] PASS1 → PASS2 → PASS3 요약 포함
- [x] 8필드 형식 준수
