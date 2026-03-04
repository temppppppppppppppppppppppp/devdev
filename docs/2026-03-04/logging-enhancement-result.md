# 로깅 강화 결과

> 구현일: 2026-03-04

## 추가 내역

| Phase | 대상 | 내용 | 완료 |
|-------|------|------|------|
| 1 | `modules/core/db_manager.py`, `modules/domain/agents/base_agent.py` | `llm_calls` 테이블/인덱스 추가, `save_llm_call()` 추가, BaseAgent LLM 호출 성공/실패 DB 계측 추가 | ✅ |
| 2 | `modules/core/db_manager.py`, `modules/core/stage2_finalizer.py`, `modules/core/stage3_orchestrator.py`, `modules/core/stage4_interview_round.py` | `stage_attempts` 테이블/인덱스 추가, Stage 2/3/4 verdict 확정 경로에서 `save_stage_attempt()` 호출 추가 | ✅ |
| 3 | `modules/core/db_manager.py`, `modules/core/stage4_interview_round.py` | `director_selections.advisory_warnings` 마이그레이션 추가, Stage4에서 advisory summary 전달 연결 | ✅ |
| 4 | `modules/core/failure_analyzer.py` | `FailureAnalyzer` 신규 추가 (summary 포함 다중 조회 메서드) | ✅ |
| 5 | `modules/core/stage4_interview_round.py` | `episode_production.jsonl`에 `model`, `duration_ms`, `ep_attempt_total` 추가 | ✅ |
| 6 | `tests/test_logging_enhancement.py` | 로깅 강화 테스트 9건 추가 | ✅ |

## 수동 확인 결과 (오더 0/1)

- `modules/core/db_manager.py`
- `initialize_db()` 존재 확인 (`_boot_db()` idempotent entrypoint)
- `cost_log` DDL 존재 확인
- `director_selections`에 `advisory_warnings` 마이그레이션 추가 확인
- `modules/domain/agents/base_agent.py`
- `ask()`의 성공 return 직전/실패 except 경로에서 LLM DB 계측 확인
- `_ask_with_cached_context()` 및 `_attempt_backup_recovery()` 계측 확인
- `modules/core/session_logger.py`
- LLM 기록 메서드는 `log_llm_call()` 시그니처로 존재
- 결정 기록 메서드 `log_decision()` 시그니처 확인

## 검증 결과

- `python -m py_compile modules/core/db_manager.py modules/domain/agents/base_agent.py modules/core/failure_analyzer.py modules/core/stage4_interview_round.py modules/core/stage2_finalizer.py modules/core/stage3_orchestrator.py tests/test_logging_enhancement.py`
- 결과: 통과

- `ruff check modules/ tests/`
- 결과: `All checks passed!`

- `pytest tests/test_logging_enhancement.py -v`
- 결과: `9 passed, 0 failed`

- `pytest tests/ -q`
- 결과: `3236 passed, 16 skipped, 1 warning, 0 failed`

- 런타임 스모크:
  - `FailureAnalyzer(db).summary()` dict 반환 확인
  - `[OK] FailureAnalyzer 정상 동작` 출력 확인

## 합격 기준 체크

- `llm_calls` 테이블 존재: ✅
- `stage_attempts` 테이블 존재: ✅
- `director_selections.advisory_warnings` 컬럼 존재(마이그레이션): ✅
- `FailureAnalyzer` import 가능: ✅
- `FailureAnalyzer(db).summary()` dict 반환: ✅
- 신규 테스트 PASS: ✅
- 전체 테스트 0 failed: ✅
- ruff 위반 0건: ✅
- 로깅 코드 비치명(try/except Exception 보호): ✅
