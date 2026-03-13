# MDH-T1: Retry / Guidance Helper Liveness Findings

> 작성일: 2026-03-13
> 작성자: `codex-gpt-5`
> 트랙: `main_a.py` dormant helper / live consumer inventory — Terminal 1
> 상태: `PASS 3 확정 (re-audit)`
> 범위: retry / guidance helper 7종의 실제 caller, DI 바인딩, 테스트 근거 재조사

---

## 1. 요약

| # | Helper | 현재 판정 | Severity | 실제 consumer / 경로 | 비고 |
|---|--------|-----------|----------|----------------------|------|
| 1 | `_generate_writer_guidance_v60_8` | **LIVE surface (현재 binding broken)** | P0 | `Stage4Context.from_app()` → `Stage4ContextBuilder.build_mandatory_context()` | dormant 아님. `Stage4Context.__slots__` 누락으로 바인딩이 깨짐 |
| 2 | `_generate_arc_position_guide` | **DORMANT** | P3 | 확인된 production caller 없음 | 테스트 전용 pure/helper surface |
| 3 | `_simplify_prompt_for_retry` | **DORMANT** | P3 | 확인된 production caller 없음 | 테스트 전용 retry surface |
| 4 | `_build_focused_context` | **LIVE** | - | `Stage2Context.from_app()` → `Stage2ValidationPipeline` | direct wrapper가 실제 주입됨 |
| 5 | `_build_minimal_arc_context` | **LIVE** | - | `Stage2Context.from_app()` → `Stage2Preflight` | direct wrapper가 실제 주입됨 |
| 6 | `_generate_reverse_feedback_stage4_to_3` | **LIVE (conditional)** | - | `Stage4Orchestrator._build_stage4_to_3_reverse_feedback()` → blueprint patch / regenerate 경로 | repeated `LOGIC_ERROR` 이후 사용 |
| 7 | `_enrich_director_result` | **LIVE surface (현재 binding broken)** | P0 | `Stage4Context.from_app()` → `Stage4InterviewRound._maybe_enrich_director_result()` | dormant 아님. `Stage4Context.__slots__` 누락으로 바인딩이 깨짐 |

정리:

- **확정 finding 3건**
- `P0 1건`, `P3 2건`
- OPUS 초안의 dormant 판정 5건 중 **3건은 오탐**이었다.

---

## 2. 확정 Findings

### MDH-T1-01: `Stage4Context` callback slot 누락으로 T1 Stage4 live surface 2종이 현재 runtime에서 막혀 있다

- **ID**: `MDH-T1-01`
- **Severity**: `P0`
- **현상 요약**: `_generate_writer_guidance_v60_8`와 `_enrich_director_result`는 둘 다 Stage 4에서 실제 consumer를 가지는 intended live surface다. 그러나 `modules/core/stage4_context.py`는 `__init__()`과 `from_app()`에서 두 callback을 받도록 확장됐지만, `__slots__`에는 두 속성이 빠져 있다. 그 결과 `Stage4Context.from_app()` 호출 시 `AttributeError`가 발생하고, Stage 4 진입 자체가 깨진다.
- **코드 근거**:
  - `modules/core/stage4_context.py:45`의 `__slots__`에 `generate_writer_guidance_v60_8`, `enrich_director_result`가 없음
  - 같은 파일 `:115-116`, `:148-149`, `:195-196`은 두 callback을 생성자/바인딩 경로에 포함
  - `main_a.py:3544`는 Stage 4 진입 직전에 `self._stage4_orch.ctx = Stage4Context.from_app(self)`를 실행
  - `modules/core/stage4_context_builder.py:2514-2533`는 `generate_writer_guidance_v60_8`를 실제 prompt 조립 경로에서 호출
  - `modules/core/stage4_interview_round.py:839-863`, `:1902`는 `enrich_director_result`를 실제 verdict 후처리 경로에서 호출
- **downstream 영향 경계**:
  - Stage 4 context auto-build / explicit DI 주입 경로가 즉시 예외로 실패
  - writer guidance 주입과 director result enrichment는 dormant가 아니라 **binding-broken live consumer** 상태
  - T1 live/dormant inventory를 단순 grep으로 잠그면 잘못된 결론이 된다
- **현재 테스트 근거 또는 테스트 부재**:
  - `tests/test_stage4_context.py`, `tests/test_stage4_orchestrator.py`, `tests/test_stage4_interview_round.py`가 모두 같은 `AttributeError`로 연쇄 실패
  - 재조사 실행 결과:
    - `pytest -q tests/test_stage2_context.py tests/test_stage2_preflight.py tests/test_stage2_validation_pipeline.py tests/test_stage4_context.py tests/test_stage4_context_builder.py tests/test_stage4_orchestrator.py tests/test_stage4_interview_round.py`
    - 결과: `20 failed, 227 passed, 20 errors`
    - 핵심 오류: `AttributeError: 'Stage4Context' object has no attribute 'generate_writer_guidance_v60_8'`
- **기존 문서와의 중복 여부**: `related-but-new-live-consumer-surface`
- **권장 후속 조치**:
  - `Stage4Context.__slots__`에 두 callback 슬롯을 추가
  - Stage 4 관련 실패 테스트를 먼저 복구
  - 복구 후 T1 liveness inventory를 다시 PASS 3로 고정

### MDH-T1-02: `_generate_arc_position_guide`는 현재 production caller가 없는 test-only helper wrapper다

- **ID**: `MDH-T1-02`
- **Severity**: `P3`
- **현상 요약**: `main_a.py`의 `_generate_arc_position_guide()` wrapper와 `PromptBuilder.generate_arc_position_guide()` pure helper는 repo 전역에서 unit test 외 production caller가 확인되지 않았다. `generate_writer_guidance_v60_8()`도 이 helper를 호출하지 않는다.
- **코드 근거**:
  - `main_a.py:685-687` wrapper 정의
  - `modules/core/prompt_builder.py:86-144` pure helper 정의
  - repo 전역 검색 기준 production caller 부재
  - `modules/core/prompt_builder.py:487-525`의 `generate_writer_guidance_v60_8()`는 `generate_high_impact_zone_guide`, `generate_npc_relationship_justification`, `generate_item_acquisition_timeline`, `generate_temporal_spatial_guide`, `generate_cliche_avoidance_guide`만 사용
- **downstream 영향 경계**: 현재 runtime 영향 없음. 제거해도 production 동작면 영향은 낮다.
- **현재 테스트 근거 또는 테스트 부재**:
  - `tests/test_prompt_builder.py:76-114`만 존재
  - wrapper 직접 테스트는 없음
- **기존 문서와의 중복 여부**: `related-but-new-live-consumer-surface`
- **권장 후속 조치**:
  - 실제 production 계획이 없다면 wrapper/helper 삭제 후보로 분리
  - 유지할 경우 live caller를 명시적으로 추가하거나 문서에 test-only surface로 잠글 것

### MDH-T1-03: `_simplify_prompt_for_retry`는 현재 production caller가 없는 test-only retry surface다

- **ID**: `MDH-T1-03`
- **Severity**: `P3`
- **현상 요약**: `main_a.py`의 `_simplify_prompt_for_retry()` wrapper와 `FeedbackSystem.simplify_prompt_for_retry()`는 unit test 외 production caller가 확인되지 않았다.
- **코드 근거**:
  - `main_a.py:669-671` wrapper 정의
  - `modules/core/feedback_system.py:846-879` pure helper 정의
  - repo 전역 검색 기준 production caller 부재
- **downstream 영향 경계**: runtime 영향 없음. retry pipeline이 이 helper에 의존하지 않는다.
- **현재 테스트 근거 또는 테스트 부재**:
  - `tests/test_feedback_system.py:605-626`만 존재
  - wrapper 직접 테스트 및 production integration test 없음
- **기존 문서와의 중복 여부**: `related-but-new-live-consumer-surface`
- **권장 후속 조치**:
  - 삭제 후보로 분리하거나
  - 실제 retry flow에 쓸 계획이면 Stage2/Stage4 caller를 명시적으로 연결하고 integration test를 추가할 것

---

## 3. LIVE 확인 항목

### `_build_focused_context` — LIVE

- `Stage2Context.from_app()`는 app에 `_build_focused_context`가 있으면 fallback보다 **direct wrapper를 우선 바인딩**한다 (`modules/core/stage2_context.py:64-75`, `:309-360`).
- 바인딩된 callback은 `modules/core/stage2_validation_pipeline.py:897-902`에서 실제 retry prompt context 생성에 사용된다.
- 테스트 근거:
  - `tests/test_stage2_context.py:91-106`
  - `tests/test_stage2_validation_pipeline.py:25-33`

### `_build_minimal_arc_context` — LIVE

- 실제 app에서는 direct wrapper `_build_minimal_arc_context`가 존재하므로 `Stage2Context.from_app()`가 wrapper를 우선 사용한다.
- runtime consumer는 `modules/core/stage2_preflight.py:928-937`.
- 테스트 근거:
  - direct/fallback binding 확인: `tests/test_stage2_context.py:149-167`
  - runtime 사용 확인: `tests/test_stage2_preflight.py:262-268`

### `_generate_reverse_feedback_stage4_to_3` — LIVE (conditional)

- `modules/core/stage4_orchestrator.py:267-307`가 app의 `_generate_reverse_feedback_stage4_to_3`를 직접 조회한다.
- 이 결과는 `:1166-1176`, `:1225-1233`에서 blueprint inplace patch / regenerate feedback에 합쳐진다.
- 테스트 근거:
  - `tests/test_stage4_orchestrator.py:642-682`
- 결론:
  - 항상 호출되지는 않지만 repeated `LOGIC_ERROR` 이후의 Stage 4→3 feedback chain에 연결된 **live conditional surface**다.
  - dormant로 분류하면 오탐다.

### `_generate_writer_guidance_v60_8` — LIVE surface (현재 binding broken)

- intended consumer:
  - `Stage4Context.from_app()`가 callback을 app에서 추출 (`modules/core/stage4_context.py:195`)
  - `Stage4ContextBuilder.build_mandatory_context()`가 실제 prompt 조립 시 호출 (`modules/core/stage4_context_builder.py:2514-2533`)
- 테스트 근거:
  - DI 추출: `tests/test_stage4_context.py:165-183`
  - prompt 삽입: `tests/test_stage4_context_builder.py:566-590`
- 결론:
  - dormant가 아니라 **live prompt hook**
  - 현재는 MDH-T1-01의 slot bug 때문에 binding이 깨져 있다

### `_enrich_director_result` — LIVE surface (현재 binding broken)

- intended consumer:
  - `Stage4Context.from_app()`가 callback을 app에서 추출 (`modules/core/stage4_context.py:196`)
  - `Stage4InterviewRound._maybe_enrich_director_result()`가 director verdict 후처리에서 호출 (`modules/core/stage4_interview_round.py:839-863`, `:1902`)
- 테스트 근거:
  - DI 추출: `tests/test_stage4_context.py:165-183`
  - runtime caller 코드는 존재하지만, callback invocation/merge semantics를 직접 고정한 전용 테스트는 현재 확인되지 않음
- 결론:
  - dormant가 아니라 **live verdict enrichment hook**
  - 현재는 MDH-T1-01의 slot bug 때문에 binding이 깨져 있다

---

## 4. PASS 추적 요약

| Helper | PASS 1 후보 | PASS 2 교차검증 | PASS 3 최종 |
|--------|------------|----------------|------------|
| `_generate_writer_guidance_v60_8` | DORMANT 후보 | Stage4Context + Stage4ContextBuilder live path 확인, slot bug 확인 | **LIVE surface / P0 shared finding에 편입** |
| `_generate_arc_position_guide` | DORMANT 후보 | production caller 부재 재확인 | **DORMANT 확정** |
| `_simplify_prompt_for_retry` | DORMANT 후보 | production caller 부재 재확인 | **DORMANT 확정** |
| `_build_focused_context` | LIVE 후보 | Stage2Context direct binding + validation consumer 확인 | **LIVE 확정** |
| `_build_minimal_arc_context` | LIVE 후보 | Stage2Context direct binding + preflight consumer 확인 | **LIVE 확정** |
| `_generate_reverse_feedback_stage4_to_3` | DORMANT 후보 | Stage4Orchestrator reverse feedback path 확인 | **LIVE 확정** |
| `_enrich_director_result` | DORMANT 후보 | Stage4Context + Stage4InterviewRound live path 확인, slot bug 확인 | **LIVE surface / P0 shared finding에 편입** |

- PASS 1 후보 7건
- PASS 2 제거 4건
  - dormant 오탐 제거 3건: `_generate_writer_guidance_v60_8`, `_generate_reverse_feedback_stage4_to_3`, `_enrich_director_result`
  - direct wrapper live 근거 보강 1건: `_build_minimal_arc_context`
- PASS 3 확정 3건

---

## 5. Open Questions / Coverage Gap

1. `Stage4Context` slot bug를 고친 뒤에도 `_enrich_director_result`의 callback invocation 및 merge semantics를 직접 고정하는 테스트가 아직 약하다.
2. `_generate_arc_position_guide`와 `_simplify_prompt_for_retry`는 현재 test-only surface로 보이지만, 외부 operator/manual path가 있는지는 정적 조사만으로는 100% 폐쇄되지 않는다.

---

## 6. 조사 근거 목록

- `main_a.py:432-756`, `main_a.py:3544`
- `modules/core/stage2_context.py`
- `modules/core/stage2_validation_pipeline.py:897-902`
- `modules/core/stage2_preflight.py:928-937`
- `modules/core/stage4_context.py`
- `modules/core/stage4_context_builder.py:2514-2533`
- `modules/core/stage4_interview_round.py:839-863`, `:1902`
- `modules/core/stage4_orchestrator.py:267-313`, `:1166-1176`, `:1225-1233`
- `modules/core/prompt_builder.py:86-144`, `:487-525`
- `modules/core/feedback_system.py:554-592`, `:846-879`
- `tests/test_stage2_context.py`
- `tests/test_stage2_preflight.py`
- `tests/test_stage2_validation_pipeline.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_stage4_interview_round.py`
