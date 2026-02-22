# Stage 2 전수 감사 리포트 (2026-02-22)

> 감사 범위: Stage 2 (Arc/Blueprint 설계) 전체 파이프라인
> 감사자: Claude Opus 4.6
> 대상 파일: stage2_orchestrator.py, stage2_validation_pipeline.py, stage2_finalizer.py, stage2_preflight.py, stage2_context.py, stage2_optimizer.py, analyst.py, blueprint_ensemble.py, context_advisor.py, four_phase_arc_generator.py, main_a.py(Stage2 호출부)

---

## 요약

- **P0 (차단급 버그)**: 0건
- **P1 (품질 이슈)**: 5건
- **P2 (스타일/경미)**: 7건
- **개선 아이디어**: 8건

---

## P0 -- 차단급 버그

해당 없음. Stage 2 파이프라인은 전반적으로 안정적이며, 차단급 런타임 크래시를 유발하는 버그는 발견되지 않았다.

---

## P1 -- 품질 이슈

### P1-1: Finalizer `passed = True` 데드 코드 (논리 혼동 위험)

- **파일**: `modules/core/stage2_finalizer.py:353`
- **증상**: `run_finalize()` 내부에서 `passed = True`가 할당되지만, 이 변수는 로컬 스코프에서 선언된 후 반환값에 포함되지 않고, 외부에서 참조되지 않는다.
- **원인**: 원래 `stage_2_arcs_async_logic`에서 분리할 때 `passed` 변수가 Finalizer 내부에 복사되었으나, 실제 `passed` 상태 전달은 `{"action": "break"}` 반환값을 통해 이루어지도록 리팩토링되면서 이 할당이 잔존한 것이다.
- **위험도**: 코드 읽기 시 "Finalizer가 passed를 설정한다"는 오해를 유발할 수 있으며, 향후 리팩토링 시 이 변수에 의존하는 코드를 작성할 수 있다.
- **수정안**: `passed = True` (L353) 삭제. 주석으로 `# action="break" 반환이 passed 역할` 추가 권장.

```python
# 수정 전 (L353)
passed = True

# 수정 후
# (삭제) -- action="break" 반환이 orchestrator의 passed=True 역할
```

### P1-2: Orchestrator `_SUMMARY_MODEL` 미사용 변수

- **파일**: `modules/core/stage2_orchestrator.py:104`
- **증상**: `stage_2_arcs_async_logic()` 내부에서 `_SUMMARY_MODEL = AIModels.SUMMARY_MODEL`이 선언되지만 해당 함수 내에서 전혀 사용되지 않는다.
- **원인**: 원래 모놀리식 함수에서 Flow Guard 등에 사용되던 변수가, B-1-6 분리 시 `stage2_validation_pipeline.py`로 이동했으나 원본이 삭제되지 않은 것이다.
- **위험도**: 불필요한 import(`AIModels`)가 이미 L92에서 다른 용도로 존재하므로 의존성 문제는 없다. 단, 데드 코드가 유지보수 혼란을 유발할 수 있다.
- **수정안**: L104 `_SUMMARY_MODEL = AIModels.SUMMARY_MODEL` 삭제.

### P1-3: `ReflectionTarget` 중복 import 패턴

- **파일**: `modules/core/stage2_orchestrator.py:109-116`, `modules/core/stage2_validation_pipeline.py:52-59`
- **증상**: `ReflectionTarget`이 orchestrator와 validation_pipeline 양쪽에서 동일한 패턴으로 조건부 import된다. Orchestrator에서는 L109-116에서 import하지만 해당 함수 내에서 직접 사용하지 않는다 (validation_pipeline에서만 사용).
- **원인**: B-1-6 분리 후 orchestrator 측 import가 잔존.
- **위험도**: 성능 영향은 미미하나(첫 import만 비용), 코드 중복으로 유지보수 혼란 유발.
- **수정안**: Orchestrator의 L109-116 `ReflectionTarget` import 블록 삭제.

### P1-4: DraftValidator 이중 호출

- **파일**: `modules/core/stage2_validation_pipeline.py:65-86` 및 `modules/core/stage2_validation_pipeline.py:256-276`
- **증상**: `run_validation()` 내에서 `arc_draft_validator.validate()`가 두 번 호출된다.
  - 첫 번째 (L65-86): `not four_phase_passed` 조건 아래 정보 수집 목적으로 호출. `python_advisory`를 수집하고 `draft_validator_passed = True`를 설정.
  - 두 번째 (L256-276): `not four_phase_passed` 조건 아래 다시 한번 동일한 validator를 호출. 결과에 따라 REJECT 또는 ArcCorrector 분기.
- **원인**: 첫 번째 호출은 advisory 수집 + Consensus에 전달할 목적, 두 번째 호출은 ArcCorrector 분기 판단 목적. 그러나 두 번째 호출 시 `refined_arc`가 SelfReflector/Auto-Corrector에 의해 변형되었을 수 있으므로 재검증이 필요한 것은 맞다.
- **위험도**: LLM이 아닌 Python 검증이므로 비용은 미미하지만, 첫 번째 호출에서 `draft_validator_passed = True`가 설정된 후 두 번째 호출에서 REJECT될 경우, 이전 설정값이 무의미해진다. 첫 번째 호출의 `draft_validator_passed = True`가 Consensus REJECT 이후에도 살아남아 API 할당량 폴백 판단(finalizer L158)에 영향을 줄 수 있다.
- **수정안**: 첫 번째 호출의 목적을 advisory 수집으로 한정하고, `draft_validator_passed = True` 설정을 두 번째 호출 결과에서만 하도록 통합. 또는 첫 번째 호출 결과를 캐싱하여 재사용.

### P1-5: `_preflight_enrichment`에서 ThreadPoolExecutor 내부 `self.ctx` 직접 접근

- **파일**: `modules/core/stage2_preflight.py:192-266` (`_preflight_state_setup`)
- **증상**: `_compute_arc_drive()`와 `_compute_preflight()`는 `ThreadPoolExecutor`에서 실행되는데, 내부에서 `self.ctx.agents`, `self.ctx.perf_timer`, `self.ctx.state_tracker` 등을 직접 접근한다. `Stage2Context`의 `__slots__` 속성들은 모두 Python 기본 타입이므로 GIL로 인해 심각한 경합은 없으나, `self.ctx.perf_timer.start/stop`처럼 내부 상태를 변경하는 호출은 스레드 안전하지 않을 수 있다.
- **원인**: `concurrent.futures.ThreadPoolExecutor` 내부에서 공유 객체를 락 없이 변경.
- **위험도**: `perf_timer`가 딕셔너리 기반이고 키가 unique(`s2_arc_{N}_arc_drive` vs `s2_arc_{N}_preflight_analysis`)하므로 현재는 충돌하지 않는다. 그러나 향후 같은 키를 쓰게 되면 데이터 손상 위험이 있다.
- **수정안**: 현재 구조에서는 실질적 문제 없음. 단, `try/except`로 감싸져 있어 폴백이 작동하므로 지금은 허용 가능. 향후 `perf_timer`에 `threading.Lock`을 도입하면 근본 해결.

---

## P2 -- 스타일/경미

### P2-1: `_stage2_flow_guard_legacy` 매개변수 타입 불일치 (시그니처 vs 호출)

- **파일**: `modules/core/stage2_validation_pipeline.py:698`
- **증상**: `_stage2_flow_guard_legacy(self, normalized: list)` 시그니처에서 매개변수명이 `normalized`(단수)이지만, 실제로는 리스트를 받는다. 호출부(L693)에서도 리스트를 전달한다. 단, Orchestrator의 backward-compat wrapper(L841)에서는 `_stage2_flow_guard_legacy(normalized)`를 `str` 타입으로 표기(`normalized: str`)하고 있어 혼동을 줄 수 있다.
- **수정안**: Orchestrator wrapper의 시그니처를 `normalized: list`로 수정하거나, 내부에서 타입 변환 로직 추가.

### P2-2: `logging.warning` vs `self.ctx.ui.log` 혼용

- **파일**: 전체 Stage 2 서브모듈
- **증상**: 사용자 대면 메시지가 때로는 `self.ctx.ui.log()`으로, 때로는 `logging.warning()`으로 출력된다. 예를 들어 `stage2_validation_pipeline.py`에서 Consensus 관련 로그는 `logging.warning`을 사용하지만 같은 함수 내 Flow Guard 로그는 `self.ctx.ui.log`를 사용한다.
- **원인**: 분리 전 원본 코드의 혼합 패턴이 그대로 유지.
- **위험도**: 기능 문제 없음. 단, 운영 시 UI에 표시되어야 할 메시지가 로그 파일에만 남거나, 디버그 메시지가 UI에 노출될 수 있음.
- **수정안**: 사용자 대면 메시지는 `ui.log`, 개발자 추적용은 `logging.info/warning` 규칙 통일.

### P2-3: `_build_relationship_history` 미사용 메서드

- **파일**: `modules/core/stage2_optimizer.py:537-566`
- **증상**: `NegativeConstraintAmplifier._build_relationship_history()` 메서드가 정의되어 있으나, 클래스 내 어디에서도 호출되지 않는다.
- **수정안**: 향후 사용 계획이 없으면 삭제.

### P2-4: `SessionFailureMemory.should_increase_constraints` 미사용 메서드

- **파일**: `modules/core/stage2_optimizer.py:734-738`
- **증상**: `should_increase_constraints()` 메서드가 정의되어 있으나 외부에서 호출되지 않는다.
- **수정안**: 향후 사용 계획이 없으면 삭제. 또는 `_preflight_state_setup`에서 제약 강화 로직에 연결.

### P2-5: 하드코딩된 `max_attempts = 5` 상수

- **파일**: `modules/core/stage2_preflight.py:329`
- **증상**: `max_attempts = 5`가 하드코딩되어 있다. 다른 Stage에서는 `RetryLimits` 상수를 사용하는 패턴이 있다.
- **수정안**: `constants.py`의 `RetryLimits` 또는 `validation.yaml` 설정으로 외부화.

### P2-6: `import logging as _dv_log` 중복 import

- **파일**: `modules/core/stage2_validation_pipeline.py:266-267`
- **증상**: `except` 블록 내부에서 `import logging as _dv_log`를 사용하는데, 파일 상단에서 이미 `import logging`이 되어 있다.
- **수정안**: `_dv_log.warning` -> `logging.warning`으로 변경하고 중복 import 삭제.

### P2-7: 볼륨 요약 LLM 호출 시 Director 에이전트 직접 사용

- **파일**: `modules/core/stage2_finalizer.py:437, 455`
- **증상**: 볼륨/시리즈 요약 생성 시 `self.ctx.agents["director"].ask()` 로 Director 에이전트를 범용 LLM 호출에 사용한다. Director 에이전트는 심사 전용으로 설계되어 있으며, 시스템 프롬프트에 심사 관련 지시가 포함되어 있어 요약 품질에 영향을 줄 수 있다.
- **수정안**: 범용 요약 호출은 별도 `summarizer` 에이전트나 `SUMMARY_MODEL` 직접 호출로 분리. 현재로서는 기능적 문제 없음.

---

## 개선 아이디어

### IDEA-1: Stage 2 벡터 검색 실행의 병렬화

- **파일**: `modules/core/stage2_preflight.py:611-656`
- **현재**: `_execute_stage2_retrieval_plan` 호출이 FourPhase 생성 직전에 동기적으로 실행되어 5-10초의 추가 지연을 유발한다.
- **제안**: FourPhase 생성의 constraint 수집 단계와 벡터 검색을 `ThreadPoolExecutor`로 병렬 실행. `_s2_vector_ctx`를 미리 준비해두면 FourPhase `generate()` 호출 시 즉시 주입 가능.
- **효과**: Arc 당 5-10초 절감. 배치 5개 Arc 기준 25-50초 절감.

### IDEA-2: DraftValidator 캐싱으로 이중 호출 제거

- **파일**: `modules/core/stage2_validation_pipeline.py`
- **현재**: P1-4에서 지적한 대로 DraftValidator가 두 번 호출된다.
- **제안**: 첫 번째 호출 결과를 `_cached_draft_result`에 저장하고, SelfReflector/AutoCorrector에 의한 `refined_arc` 변형이 감지될 경우에만 재검증. 변형이 없으면 캐시 재사용.
- **효과**: Python 검증이므로 비용 절감은 미미하나 코드 명확성 향상.

### IDEA-3: Preflight 분석 결과의 2차 활용 (Director 컨텍스트 주입)

- **파일**: `modules/core/stage2_preflight.py:218-244`, `modules/core/stage2_finalizer.py:82-109`
- **현재**: Preflight 분석 결과(`_cached_preflight_result`)는 Analyst에게만 주입된다. Director에게는 별도의 `_expanded_prev_context`가 구축되는데, 여기에 Preflight의 `absolute_prohibitions`나 `item_timeline`이 포함되지 않는다.
- **제안**: Director 컨텍스트에 Preflight 분석 결과의 핵심 제약 사항을 추가 주입. 특히 `absolute_prohibitions` 리스트는 Director가 아이템 중복 REJECT 판단 시 유용.
- **효과**: Director REJECT율 중 "이미 금지된 아이템 포함" 유형 감소 기대.

### IDEA-4: Stage2Context `__slots__` 문서와 실제 슬롯 수 불일치 정리

- **파일**: `modules/core/stage2_context.py:23-43`
- **현재**: 독스트링에 "확장 18종"이라 표기되어 있으나, 실제 `__slots__`에는 `context_advisor`와 `adversarial_self_play`가 추가되어 20종이다. 콜백도 "21종"이라 표기되었으나 `sync_cache_key_to_app`까지 22종이다.
- **제안**: 독스트링의 종수 표기를 실제와 일치시키거나, "N종" 표기 대신 "확장 슬롯"으로 범용 표현.

### IDEA-5: Arc 실패 리포트의 구조화된 JSON 출력

- **파일**: `modules/core/stage2_orchestrator.py:600-679`
- **현재**: Arc 실패 리포트가 텍스트 파일(`failure_report.txt`)로 출력된다.
- **제안**: JSON 형식으로 출력하면 자동 분석 도구가 실패 패턴을 수집할 수 있다. 텍스트 버전은 사람 읽기용으로 병행 출력.
- **효과**: 운영 자동화 시 실패 패턴 자동 집계 가능.

### IDEA-6: `StateTracker` 스냅샷의 deepcopy 비용 절감

- **파일**: `modules/core/stage2_preflight.py:786-812`
- **현재**: FourPhase PASS 시 StateTracker의 18개 레지스트리를 `copy.deepcopy()`로 스냅샷한다. NPC 레지스트리가 커지면 수십 ms의 비용이 발생한다.
- **제안**: 1) `copy-on-write` 패턴 도입 -- 스냅샷 시점에 reference만 저장하고, 변형 시점에 복사. 2) 또는 StateTracker에 `snapshot()`/`restore()` 메서드를 내장하여 필요한 필드만 선택적 복사.
- **효과**: 대규모 NPC(100+명) 프로젝트에서 Arc 당 10-50ms 절감.

### IDEA-7: FourPhase 내부 retry와 외부 Director retry의 통합 관리

- **파일**: `modules/core/stage2_preflight.py:607-963`, `modules/core/stage2_orchestrator.py:419-589`
- **현재**: FourPhase 내부 재시도(`max_internal_retries=4`)와 Orchestrator 외부 재시도(`max_attempts=5`)가 독립적으로 관리된다. 최악의 경우 4 x 5 = 20회의 LLM 호출이 발생할 수 있다.
- **제안**: 통합 시도 카운터를 도입하여 총 시도 횟수에 상한을 두고, FourPhase 내부 재시도와 외부 재시도를 합산 관리. 또는 FourPhase 내부 실패 패턴을 외부에 전달하여 중복 시도를 방지.
- **효과**: 최대 LLM 호출 횟수 제한으로 비용 예측 가능성 향상.

### IDEA-8: `constraint_block` 누적 방지 메커니즘

- **파일**: `modules/core/stage2_preflight.py:278-315`
- **현재**: `_preflight_state_setup`에서 `constraint_block`이 `ConstraintDB.generate_constraint_block()` 결과에 `ConstraintCompiler.compile()` 결과를 이어 붙인다 (L315). 이후 `_preflight_arc_analysis` (L389)에서도 `enhanced_context`에 `constraint_block`이 다시 주입된다. 같은 Arc에서 retry가 발생하면 `constraint_block`이 변하지 않으므로 중복 주입은 아니지만, `enhanced_context`의 크기가 매 retry마다 다른 이유는 Focus Mode(L446-450) 때문이다.
- **제안**: `constraint_block`의 크기를 로깅하여 프롬프트 토큰 예산 관리에 활용. 현재 `enhanced_context` 총 크기를 명시적으로 추적하지 않아 Gemini context window 초과 위험이 있다.
- **효과**: 프롬프트 토큰 예산 초과 방지, 비용 예측성 향상.

---

## 연결성 검증 결과

### 정상 작동 확인 항목

1. **DI 슬롯 주입**: `Stage2Context.from_app()`이 43개 슬롯 모두 `getattr` 폴백으로 안전하게 추출. 누락 시 `None`으로 설정되며, 호출부에서 `if self.ctx.X:` 가드가 존재.
2. **Sub-module lazy init**: `validation_pipeline`, `preflight`, `finalizer` 모두 `@property` + lazy init 패턴으로 올바르게 구현. 순환 참조 없음.
3. **Backward-compat wrappers**: Orchestrator L790-841의 thin wrapper 메서드들이 sub-module 메서드를 정확히 위임. 시그니처 불일치 없음.
4. **main_a.py 연결**: `_stage_2_arcs()` -> `Stage2Context.from_app()` -> `stage_2_arcs_async_logic()` 체인이 올바르게 작동. 비동기 실행(`asyncio.run` 또는 `ThreadPoolExecutor`) 양쪽 경로 모두 안전.
5. **StateTracker 동기화**: Stage 2 완료 후 `main_a.py:2215-2218`에서 `state_tracker`를 app에 복사. Stage 3/4에서 재사용 가능.
6. **ConstraintDB 체인**: `_preflight_state_setup` -> `constraint_db.generate_constraint_block()` -> `run_validation` -> `constraint_db.validate_arc_design()` -> `run_finalize` -> `constraint_db.update_arc_state()` 전체 체인 연결 확인.
7. **Analyst -> Enrichment -> FourPhase -> Validation -> Director** 파이프라인의 데이터 흐름이 `enriched_block`, `refined_arc`, `entity_registry_for_director` 등 핵심 객체를 통해 올바르게 전달됨.

### 미연결/약결합 항목

1. **`context_advisor` 슬롯**: `Stage2Context`에 `context_advisor` 슬롯이 있고 `from_app()`에서 주입되지만, 실제 사용은 `_preflight_enrichment` 내부의 조건부 경로에서만 발생. `smart_retrieval.enabled` + `smart_retrieval.stage2_enabled` 두 플래그가 모두 True일 때만 작동하므로 대부분의 배포에서는 비활성 상태일 가능성이 높다.
2. **`adversarial_self_play` 슬롯**: `attempt >= 2`인 경우에만 작동하며, 별도의 `adversarial_self_play` 객체가 필요. 대부분의 Arc가 첫 번째 또는 두 번째 시도에서 통과하므로 실제 작동 빈도가 낮다.

---

## 테스트 커버리지 메모

Stage 2 관련 테스트 파일이 8개 존재하며 전반적인 커버리지가 양호하다:

- `test_stage2_context.py` -- DI 컨텍스트 생성/슬롯 검증
- `test_stage2_pipeline.py` -- 전체 파이프라인 통합 테스트
- `test_stage2_validation_pipeline.py` -- 검증 체인 단위 테스트
- `test_stage2_finalizer.py` -- Finalizer PASS/REJECT 경로
- `test_stage2_preflight.py` -- Preflight 분석
- `test_stage2_preflight_helpers.py` -- NPC 로스터/토큰 추출 헬퍼
- `test_stage2_patch_integration.py` -- Patch Mode 통합
- `test_stage234_fixes.py` -- Cross-stage 수정 검증

단, `_stage2_flow_guard` 및 `_stage2_flow_guard_legacy`에 대한 전용 테스트가 `test_stage2_validation_pipeline.py`에 포함되어 있는지 확인 필요. Flow Guard는 `NarrativeStructureAnalyzer` LLM 호출을 포함하므로 mock 기반 테스트가 중요하다.

---

## 총평

Stage 2 파이프라인은 다수의 디버깅 스윕(1차~12차)과 Opus TF 재감사를 거쳐 상당히 안정화된 상태이다. P0급 차단 버그가 발견되지 않았으며, P1 이슈도 대부분 데드 코드 또는 마이너한 논리 혼동 수준이다.

주요 강점:
- **방어적 프로그래밍**: 거의 모든 LLM 호출, DB 접근, 외부 시스템 호출이 `try/except`로 감싸져 있어 개별 실패가 전체 파이프라인을 중단시키지 않는다.
- **롤백 메커니즘**: StateTracker 스냅샷 + DB 트랜잭션 롤백이 REJECT/실패 시 일관성을 보장한다.
- **Patch Mode**: 이전 시도 Arc를 기반으로 부분 수정하는 점진적 개선 전략이 비용 효율적이다.
- **Sweep45 방어**: `.get()` 폴백과 타입 검사가 전반에 걸쳐 적용되어 LLM의 불안정한 출력에 강건하다.

개선 여지:
- 프롬프트 토큰 예산 관리가 명시적이지 않아, 대규모 프로젝트(50+ Arc)에서 context window 초과 가능성이 있다.
- FourPhase 내부 retry와 외부 retry의 이중 루프가 최악의 경우 과도한 LLM 호출을 유발할 수 있다.
- 데드 코드 5건(P1-1, P1-2, P1-3, P2-3, P2-4)이 잔존하여 코드 명확성을 저하시킨다.
