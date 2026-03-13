# S2D-T5: Dead Code & Test Coverage Findings

> Track: S2D-T5 | Auditor: Claude Opus 4.6 | Date: 2026-03-13
> Protocol: 3-pass (full sweep -> verify -> finalize)

---

## Summary Table

| ID | 제목 | Severity | 판정 | 위치 |
|----|------|----------|------|------|
| S2D-T5-001 | state_locked_arc_generator.py 전용 테스트 파일 부재 | P2 | 확정 | `modules/domain/agents/state_locked_arc_generator.py` |
| S2D-T5-002 | Stage2Optimizer 5개 서브클래스 중 4개 테스트 미커버 | P2 | 확정 | `modules/core/stage2_optimizer.py` |
| S2D-T5-003 | MagicMock() spec 미지정 161건 (Stage2 테스트 전체) | P2 | 확정 | `tests/test_stage2_*.py` 7개 파일 |
| S2D-T5-004 | stage2_contracts.py 단위 테스트 부재 | P3 | 확정 | `modules/core/stage2_contracts.py` |
| S2D-T5-005 | e2e 테스트가 LLM 에이전트 전량 mock - real wiring 검증 불가 | P3 | 확정 | `tests/e2e/test_l3_stage2_realproject.py` |
| S2D-T5-006 | state_locked_arc_generator.py / continuity_arc.py / continuity_inspector.py LIVE 확인 - dead code 아님 | INFO | 오탐방지 | 3개 파일 전부 |
| S2D-T5-007 | Stage2Orchestrator backward-compat wrapper 12개 - 외부 호출자 존재 | P3 | 확정 | `modules/core/stage2_orchestrator.py:1006-1057` |

---

## Findings

### [S2D-T5-001] state_locked_arc_generator.py 전용 테스트 파일 부재
- **Severity**: P2
- **위치**: `modules/domain/agents/state_locked_arc_generator.py` (583줄)
- **근거**:
  - `grep -r "state_locked_arc_generator\|StateLockedArcGenerator" tests/` 결과: 0건
  - 583줄 규모의 에이전트(163줄 class, generate() 등 핵심 메서드 포함)에 대한 단위 테스트가 전무
  - `main_a.py:131`에서 import, `main_a.py:1611`에서 인스턴스화 — live code path
  - `config/models.yaml:31`에 모델 설정 존재
- **판정**: 확정
- **권장 조치**: `tests/test_state_locked_arc_generator.py` 신규 작성. 최소 generate() 정상 경로, 파싱 실패 폴백, _lock_start_state() None 핸들링 테스트 필요.

---

### [S2D-T5-002] Stage2Optimizer 5개 서브클래스 중 4개 테스트 미커버
- **Severity**: P2
- **위치**: `modules/core/stage2_optimizer.py`
- **근거**:
  - 6개 클래스 존재:
    1. `StateSnapshotInjector` (L95) — extract_snapshot(), generate_injection_prompt() — **테스트 0건**
    2. `ArcAutoCorrector` (L227) — auto_correct() 및 하위 메서드 — `test_stage2_optimizer.py`에 3건만 (private 메서드 직접 테스트)
    3. `NegativeConstraintAmplifier` (L736) — amplify_constraints() — `test_sweep18.py`에 1건만
    4. `FocusedFeedbackGenerator` (L854) — generate_feedback() — **테스트 0건**
    5. `SessionFailureMemory` (L942) — record_failure(), get_top_failure_patterns(), generate_warning_prompt(), clear() — **테스트 0건**
    6. `FewShotExampleManager` (L1031) — add_successful_arc(), generate_example_prompt(), get_average_tactical_length() — **테스트 0건**
    7. `Stage2Optimizer` (L1099, 통합 facade) — generate_optimized_prompt(), post_process_arc(), record_result(), get_stats(), print_stats() — **테스트 0건**
  - 미테스트 public 메서드 총 15개
- **판정**: 확정
- **권장 조치**: `StateSnapshotInjector`, `FocusedFeedbackGenerator`, `SessionFailureMemory`, `FewShotExampleManager` 단위 테스트 추가. 특히 `SessionFailureMemory.record_failure()` + `generate_warning_prompt()` 조합은 Stage 2 retry 루프 품질에 직결.

---

### [S2D-T5-003] MagicMock() spec 미지정 161건 (Stage2 테스트 전체)
- **Severity**: P2
- **위치**: `tests/test_stage2_*.py` 7개 파일
- **근거**:
  - `MagicMock()` (spec 없음): **161건** (7개 파일)
  - `MagicMock(spec=...)`: **1건** (`test_stage2_context.py:138` — `spec=[]`)
  - 파일별 분포:
    | 파일 | MagicMock() 건수 |
    |------|-----------------|
    | test_stage2_preflight_helpers.py | 42 |
    | test_stage2_preflight.py | 37 |
    | test_stage2_context.py | 28 |
    | test_stage2_finalizer.py | 27 |
    | test_stage2_pipeline.py | 14 |
    | test_stage2_validation_pipeline.py | 9 |
    | test_stage2_orchestrator.py | 4 |
  - spec 미지정 시 존재하지 않는 속성 접근이 조용히 성공하여 실제 인터페이스 변경을 감지하지 못함
  - 예: `ctx = MagicMock()` 후 `ctx.nonexistent_attr` 접근 시 오류 없이 새 MagicMock 반환
  - 대표 사례 (`test_stage2_validation_pipeline.py:17-23`):
    ```python
    app = MagicMock()           # SovereignApp spec 없음
    ctx = MagicMock()           # Stage2Context spec 없음
    ctx.ui = MagicMock()        # UIService spec 없음
    ctx.ui.log = MagicMock()
    ctx.audit_event = MagicMock()
    ```
    Stage2Context는 `__slots__` 기반이므로 `spec=Stage2Context`를 사용하면 잘못된 속성 접근을 즉시 감지 가능.
- **판정**: 확정
- **권장 조치**: 점진적으로 `MagicMock(spec=Stage2Context)`, `MagicMock(spec=Stage2Orchestrator)` 등 spec 추가. 특히 `ctx` mock은 `__slots__`가 정의된 `Stage2Context`를 spec으로 사용하면 효과적.

---

### [S2D-T5-004] stage2_contracts.py 단위 테스트 부재
- **Severity**: P3
- **위치**: `modules/core/stage2_contracts.py` (3줄)
- **근거**:
  - 파일 내용: `TACTICAL_DOC_DUPLICATE_THRESHOLD = 0.92` 상수 1개만 정의
  - 3개 파일에서 import하여 사용 중 (`test_main_a_stage_entry_contracts.py`, `test_stage2_pipeline.py`, `test_stage2_validation_pipeline.py`)
  - 상수 파일이므로 단독 테스트 필요성은 낮음
- **판정**: 확정 (P3 — low priority)
- **권장 조치**: 상수 범위 검증 (0 < threshold <= 1.0) assertion 정도면 충분. 현재는 import 시점 테스트로 간접 커버.

---

### [S2D-T5-005] e2e 테스트가 LLM 에이전트 전량 mock - real wiring 검증 불가
- **Severity**: P3
- **위치**: `tests/e2e/test_l3_stage2_realproject.py`
- **근거**:
  - `_run_stage2_three_blocks()` (L108-246)에서 analyst, weaver, four_phase, director 전부 `MagicMock()`
  - 실제 DB(`project_data.db`)를 복사하여 사용하는 반면, 모든 에이전트는 mock → DI wiring 정합성만 검증, LLM 통합은 미검증
  - Stage2Context는 수동 생성 (L206-231) — `from_app()` 경로 미검증
  - 이는 의도적 설계 (LLM 비용/속도 문제)이지만, `from_app()` 경유 wiring 테스트는 없음
- **판정**: 확정 (P3 — 의도적 한계이나 문서화 필요)
- **권장 조치**: `from_app()` 팩토리 메서드를 통한 Stage2Context 생성 경로를 별도 테스트로 검증. LLM mock은 유지하되 DI 조립은 실제 경로 사용 권장.

---

### [S2D-T5-006] 3개 에이전트 파일 LIVE 확인 — dead code 아님
- **Severity**: INFO
- **위치**: 3개 파일
- **근거**:

  **1) `modules/domain/agents/state_locked_arc_generator.py`** — LIVE
  - `main_a.py:131`: `from modules.domain.agents.state_locked_arc_generator import StateLockedArcGenerator`
  - `main_a.py:1611`: `"state_locked": StateLockedArcGenerator(...)` — Stage 2 agents dict에 등록
  - `config/models.yaml:31`: 모델 설정 존재
  - `modules/core/constants.py:297`: `STAGE2_EXTRACTION_MODEL` 참조

  **2) `modules/domain/agents/continuity_arc.py`** — LIVE
  - `modules/domain/agents/continuity_inspector.py:34`: `from .continuity_arc import ContinuityArcValidator`
  - `continuity_inspector.py:140`: `self._arc = ContinuityArcValidator(self)`
  - `tests/test_continuity_modules.py:19`: 테스트에서 직접 import
  - `tests/test_submodule_pattern.py:52`: 서브모듈 패턴 검증

  **3) `modules/domain/agents/continuity_inspector.py`** — LIVE
  - `main_a.py:124`: `from modules.domain.agents.continuity_inspector import ContinuityInspector`
  - `main_a.py:1589`: `"continuity_inspector": ContinuityInspector(...)` — agents dict 등록
  - `modules/core/stage2_validation_pipeline.py:749`: Stage 2 검증 체인에서 직접 호출
  - God Object 분해 후 4개 서브모듈(arc/blueprint/manuscript/tracker) 위임 구조

- **판정**: 오탐방지 (3개 파일 모두 live production path)

---

### [S2D-T5-007] Stage2Orchestrator backward-compat wrapper 12개
- **Severity**: P3
- **위치**: `modules/core/stage2_orchestrator.py:1006-1057`
- **근거**:
  - 12개 thin wrapper 메서드가 `[B-1-6]`, `[B-1-7]`, `[B-1-8]` 태그로 존재:
    ```
    _preflight_state_setup()     -> self.preflight._preflight_state_setup()
    _preflight_arc_analysis()    -> self.preflight._preflight_arc_analysis()
    _preflight_enrichment()      -> self.preflight._preflight_enrichment()
    _preflight_finalize()        -> self.finalizer.run_finalize()
    _preflight_validation()      -> self.validation_pipeline.run_validation()
    _record_s2_pass_metrics()    -> self.finalizer._record_s2_pass_metrics()
    _record_s2_reject_metrics()  -> self.finalizer._record_s2_reject_metrics()
    _normalize_tactical_text()   -> self.validation_pipeline._normalize_tactical_text()
    _is_tactical_doc_duplicate() -> self.validation_pipeline._is_tactical_doc_duplicate()
    _normalize_flow_text()       -> self.validation_pipeline._normalize_flow_text()
    _stage2_flow_guard()         -> self.validation_pipeline._stage2_flow_guard()
    _stage2_flow_guard_legacy()  -> self.validation_pipeline._stage2_flow_guard_legacy()
    ```
  - 외부 호출자:
    - `main_a.py:2788-2809`: 5개 wrapper 사용 (`_normalize_tactical_text`, `_is_tactical_doc_duplicate`, `_normalize_flow_text`, `_stage2_flow_guard`, `_stage2_flow_guard_legacy`)
    - `tests/test_stage2_preflight_helpers.py`: 나머지 7개 wrapper 사용
    - `tests/test_sc6_observability.py:174`: `_preflight_enrichment` 사용
  - dead code가 아님. `main_a.py`가 직접 참조하므로 제거 불가 (main_a.py facade 리팩터링 전까지)
  - 테스트 파일에서의 wrapper 사용은 서브모듈 직접 호출로 전환 가능
- **판정**: 확정 (P3 — 기능적 문제 없음, 코드 정리 대상)
- **권장 조치**: `main_a.py` facade 메서드가 서브모듈을 직접 호출하도록 변경 후 wrapper 제거. 테스트는 즉시 서브모듈 직접 호출로 전환 가능.

---

## Appendix: Stage 2 모듈별 테스트 커버리지 매트릭스

| 모듈 | 줄 수 | 테스트 파일 | 커버 수준 |
|------|-------|------------|----------|
| `stage2_orchestrator.py` | 907 | `test_stage2_orchestrator.py` (42줄, 2건), `test_stage2_preflight_helpers.py` (1166줄, 40+건) | 중 |
| `stage2_validation_pipeline.py` | ~1200 | `test_stage2_validation_pipeline.py`, `test_stage2_pipeline.py` | 중 |
| `stage2_preflight.py` | ~1200 | `test_stage2_preflight.py` | 중 |
| `stage2_finalizer.py` | ~1400 | `test_stage2_finalizer.py` | 중 |
| `stage2_context.py` | 368 | `test_stage2_context.py` | 상 |
| `stage2_optimizer.py` | 1211 | `test_stage2_optimizer.py` (60줄, 3건) | **하** |
| `stage2_contracts.py` | 3 | 없음 (간접 import만) | 하 |
| `state_locked_arc_generator.py` | 583 | **없음** | **미커버** |
| `continuity_arc.py` | 1012 | `test_continuity_modules.py` | 상 |
| `continuity_inspector.py` | ~420 | `test_continuity_modules.py`, `test_submodule_pattern.py` | 상 |
