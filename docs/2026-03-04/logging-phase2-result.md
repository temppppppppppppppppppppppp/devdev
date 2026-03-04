# 로깅 Phase 2 결과

> 구현일: 2026-03-04

## 추가 내역

| Phase | 대상 | 내용 | 완료 |
|-------|------|------|------|
| A-1 | `modules/core/db_manager.py` | `llm_calls`에 `prompt_snippet`, `response_snippet` 컬럼 추가 + 기존 DB 마이그레이션 + 실패 시 스니펫 저장 규칙 반영 | ✅ |
| A-2 | `modules/domain/agents/base_agent.py` | 실패 로깅 경로에서 `prompt_snippet`/`response_snippet` 전달 연결 | ✅ |
| A-3 | `modules/core/failure_analyzer.py` | `failed_call_snippets()`, `failure_prompt_patterns()` 추가 + `summary()` 확장 | ✅ |
| C-1 | `modules/core/stage2_finalizer.py`, `modules/core/stage2_validation_pipeline.py` | Stage2 verdict 기록 주체 확인(ValidationPipeline은 직접 verdict 미확정) + Finalizer 기록 payload(`duration_ms`, `failure_category`, `advisory_flags`) 보강 | ✅ |
| C-2 | `modules/core/stage3_orchestrator.py` | Stage3 `attempt_num` 동적화(retries 기반), REJECT 경로 `arc_num` 복원, `reject_reason` 상세화 | ✅ |
| Test | `tests/test_logging_phase2.py` | Phase2 전용 테스트 9건 추가 | ✅ |

## Stage 2/3 경로 조사 결과

- `stage2_validation_pipeline.py`
  - `run_validation()`은 `action=proceed/retry` 중심으로 동작하며, 최종 verdict 확정/저장(`save_stage_attempt`) 경로를 직접 가지지 않음.
  - 따라서 Stage2 attempt 로깅은 기존 설계대로 `stage2_finalizer.py`에서 단일 기록하는 것이 맞으며, ValidationPipeline에는 중복 기록을 추가하지 않음.

- `stage2_finalizer.py`
  - PASS/REJECT 모두 `save_stage_attempt()` 호출 시 `duration_ms` 전달.
  - `audit` 데이터에서 추출 가능한 범위 내 `failure_category`, `advisory_flags`를 보강 전달(없으면 NULL 유지).

- `stage3_orchestrator.py`
  - 기존 하드코딩 `attempt_num=1`을 `pipeline_result["retries"] + 1` 기반으로 변경.
  - REJECT 경로 `arc_num`은 함수 인자 `arc_no` 우선, 없으면 `pipeline_result["arc_no"]` fallback으로 복원.
  - REJECT 사유는 `error`, score, 검증 노트/모순 등 가용 필드를 조합해 최대 500자 저장.

## 검증 결과

- `python -m py_compile modules/core/db_manager.py modules/domain/agents/base_agent.py modules/core/failure_analyzer.py modules/core/stage2_finalizer.py modules/core/stage3_orchestrator.py tests/test_logging_phase2.py`
  - 결과: 통과

- `python -m ruff check modules/core/db_manager.py modules/domain/agents/base_agent.py modules/core/failure_analyzer.py modules/core/stage2_finalizer.py modules/core/stage2_validation_pipeline.py modules/core/stage3_orchestrator.py tests/test_logging_phase2.py`
  - 결과: `All checks passed!`

- `pytest tests/test_logging_phase2.py -v`
  - 결과: `9 passed, 0 failed`

- Stage3 회귀 검증:
  - `pytest tests/test_stage3_orchestrator.py tests/chaos/test_stage3_metrics.py tests/integration/test_patch_wiring.py -q`
  - 결과: `59 passed, 0 failed`

- 전체 테스트:
  - `pytest tests/ -q`
  - 결과: `3245 passed, 16 skipped, 1 warning, 0 failed`

- 런타임 검증:
  - 임시 DB에서 실패 스니펫 저장/조회 + `FailureAnalyzer.summary()` 확장 키 포함 확인
  - 결과: `[OK] failure snippet persistence + analyzer query works`

## 합격 기준 체크

- `llm_calls` 테이블에 `prompt_snippet`, `response_snippet` 컬럼 존재: ✅
- `save_llm_call(success=False, prompt_snippet=..., response_snippet=...)` 저장 동작: ✅
- `save_llm_call(success=True, prompt_snippet=...)` 시 snippet NULL 저장: ✅
- `prompt_snippet` 3000자 상한 적용: ✅
- `FailureAnalyzer.failed_call_snippets()`/`failure_prompt_patterns()` 정상 반환: ✅
- Stage2/Stage3 로깅 경로 조사 결과 명시: ✅
- 신규 테스트 전량 PASS: ✅
- 전체 테스트 0 failed: ✅
- ruff 위반 0건: ✅
- 로깅 경로 비차단(try/except) 유지: ✅
