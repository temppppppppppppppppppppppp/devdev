# TF Logging / Failure Learning / Silent Failure Plan

작성일: 2026-03-10  
인코딩: UTF-8  
상태: P1 구현 완료  
판정: PASS  
확신도: 97%

## 0-A. 실행 결과 (2026-03-10)

이번 배치에서 실제 반영된 범위는 아래 5건이다.

1. `modules/core/soft_failure.py`
공통 `soft_failure` 구조 이벤트/JSONL 적재/감사 relay/throttle 추가

2. `modules/core/session_logger.py`
세션 로거 자체 실패를 `debug-only`에서 `soft_failure + health snapshot`으로 승격

3. `modules/core/failure_analyzer.py`
summary 하위 진단 실패를 개별 soft failure로 기록하고 전체 요약은 계속 반환

4. `modules/validation/validation_orchestrator.py`, `modules/core/stage4_post_processor.py`
FailureLearner 기록 실패, Stage 4 sidecar/state/meta 저장 실패를 구조화 기록

5. `modules/api/process_runner.py`, `modules/api/bridge_server.py`, `geuldobi-desktop/src/index.html`
`run_failed`를 `returncode-only`에서 `failure_phase / last_prompt_step / stdout_tail / stderr_tail / duration` 포함 진단 이벤트로 확장

검증 결과:

- `ruff check` 타깃 파일 통과
- 타깃 회귀 `92 passed`
- API/bridge 추가 회귀 `110 passed`
- 전체 `pytest tests/ -q` -> `3848 passed, 16 skipped, 1 warning`
- `pytest --collect-only -q tests` -> `3864 collected`
- `npm run start:spike` -> PASS

## 0. 결론

무작정 `전역 전수 조사`부터 때리는 것은 비효율적이다.  
현재 글도비는 이미 아래 관측 경로를 갖고 있다.

- `modules/domain/agents/base_agent.py` -> `llm_calls`
- `modules/core/stage2_finalizer.py`, `modules/core/stage3_orchestrator.py`, `modules/core/stage4_interview_round.py` -> `stage_attempts`
- `modules/core/session_logger.py` -> `llm_io.jsonl`, `decisions.jsonl`, `state_changes.jsonl`
- `modules/core/services/audit_service.py` -> `runtime_audit.jsonl`, `runtime_audit_summary.json`
- `modules/core/quality_dashboard.py` -> `quality_metrics.jsonl`
- `modules/core/stage4_orchestrator.py`, `modules/core/stage4_interview_round.py` -> `episode_production.jsonl`

즉 문제는 `로깅 부재`가 아니라 아래 2가지다.

1. 실패가 기록되더라도 `학습 가능한 형태`로 연결되지 않는 곳이 있다.
2. 실패가 `비차단`이라는 이유로 너무 조용하게 지나가 운영자와 대시보드가 놓치는 곳이 있다.

따라서 이번 배치는 `전역 전수 조사`가 아니라 `집중 관측 보강`이 먼저다.

## 1. 현재 상태 요약

### 이미 있는 것

- LLM 호출 성공/실패는 `llm_calls`와 `SessionLogger.log_llm_call()`로 남는다.
- Stage 2/3/4 합격/실패는 `stage_attempts`와 `SessionLogger.log_decision()`로 남는다.
- Stage 4 품질/회귀/운영 지표는 `quality_metrics.jsonl`, `episode_production.jsonl`, `runtime_audit.jsonl`에 분산 저장된다.
- 브리지는 `/status`, `/events`, `/quality/summary`, `/quality/dashboard`까지 갖고 있다.

### 실제 남은 갭

#### LOG-P1-1. `SessionLogger` 자체 실패가 너무 조용하다

`modules/core/session_logger.py`

- `_write()` 실패 -> `logging.debug`만 남김
- `_maybe_rotate()` 실패 -> `logging.debug`만 남김

영향:
- `llm_io.jsonl`, `decisions.jsonl`, `state_changes.jsonl`가 안 써져도 운영자는 모를 수 있다.
- 실패 학습의 원천 로그가 비어도 후속 분석은 원인을 모른다.

#### LOG-P1-2. `FailureAnalyzer` 진단 실패가 너무 조용하다

`modules/core/failure_analyzer.py`

- `summary()`
- `top_success_patterns()`
- `quality_distribution()`
- `stage_pass_rates()`
- `failure_prompt_patterns()` 등 다수

대부분 예외를 `logging.debug`로만 흡수한다.

영향:
- 실패 분석기가 망가져도 운영자는 "실패 패턴이 없는 것"처럼 오해할 수 있다.
- `실패에서 배우기` 루프가 끊겨도 가시성이 약하다.

#### LOG-P1-3. `ValidationOrchestrator`의 학습 기록 실패가 너무 조용하다

`modules/validation/validation_orchestrator.py`

- `FailureLearner.record_failure()` 실패 시 `logging.debug(... 무시)` 처리

영향:
- `BLOCKING`/`CONTINUITY` 실패가 Director advisory로는 가더라도, 실패 학습 데이터 축적은 비어 있을 수 있다.

#### LOG-P1-4. Stage 4 post-pass 저장 실패가 운영 집계로 안 올라간다

`modules/core/stage4_post_processor.py`

다음이 warning/UI log 수준에서 끝난다.

- `save_episode_quality_label()` 실패
- `save_episode_quality_signal()` 실패
- `save_state_log_with_summary()` 실패
- `Episode Bible` 저장 실패
- `WorldState/FactLedger` 메타 저장 실패

영향:
- 에피소드 생성은 끝났지만 후행 데이터가 일부 빠진 상태가 `운영 요약`에는 잘 안 보일 수 있다.
- 조용한 실패의 대표 표면이다.

#### LOG-P1-5. 브리지 `run_failed` 이벤트가 너무 얕다

`modules/api/bridge_server.py`, `modules/api/process_runner.py`, `geuldobi-desktop/src/index.html`

현재 `run_failed`는 사실상 `returncode`만 전달한다.

영향:
- UI는 "프로세스 종료 코드 X" 정도만 보여준다.
- 어떤 key/sub_key였는지, 마지막 prompt 단계가 무엇이었는지, stderr tail이 무엇인지, non-blocking 실패가 누적되었는지 바로 알기 어렵다.

## 2. 전역 전수 조사 필요 여부

### 결론

지금 당장은 `아니오`.

### 이유

전역 전수 조사부터 가면 아래가 섞여 버린다.

- 진짜 조용한 실패
- 의도된 graceful fallback
- 기존 print/logging 위생 부채
- 이미 해결된 관측 경로

이 상태에서 전역 조사로 시작하면 `오탐`이 많아지고, 실제 ROI 높은 표면이 묻힌다.

### 권장 순서

1. 이번 문서의 `P1 집중 보강` 수행
2. 그 뒤에도 운영자가 원인 파악을 못 하면
3. 그때 `repo-wide logging hygiene sweep`으로 확대

즉 `지금은 좁고 깊게`, 나중에 `넓고 얕게`가 맞다.

## 3. 실행 계획

### P1-A. `soft_failure` 공통 이벤트 스키마 도입

대상:

- `modules/core/session_logger.py`
- `modules/core/failure_analyzer.py`
- `modules/validation/validation_orchestrator.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/services/audit_service.py`

목표:
- 비차단 실패를 단순 `warning/debug`로 끝내지 않고, 공통 구조로 남긴다.

최소 필드:

- `component`
- `operation`
- `severity`
- `stage`
- `ep_num`
- `run_id`
- `exception_type`
- `message`
- `degraded`
- `user_visible`
- `learnable`

권장 원칙:
- 예외를 hard fail로 바꾸지 않는다.
- 대신 `runtime_audit.jsonl`과 메모리 버퍼에 남긴다.
- 동일 실패는 회차/런 단위 dedupe 또는 rate limit을 둔다.

### P1-B. `SessionLogger` / `FailureAnalyzer` 헬스 신호 추가

대상:

- `modules/core/session_logger.py`
- `modules/core/failure_analyzer.py`

목표:
- 로그 작성기나 분석기가 죽어도 조용히 끝나지 않게 한다.

권장 구현:

- `SessionLogger`에 최근 실패 카운터와 마지막 실패 시각 보관
- `FailureAnalyzer` summary 실패 시 `runtime_audit` 또는 최소 `warning` 승격
- 반복 실패 시 throttled warning 1회 + soft_failure event

비목표:
- 모든 debug를 warning으로 승격하지 않는다.

### P1-C. Stage 4 post-pass 비차단 실패를 운영 집계에 올리기

대상:

- `modules/core/stage4_post_processor.py`
- `modules/core/quality_dashboard.py`
- `modules/api/bridge_server.py`

목표:
- "원고는 저장됐지만 부가 메타가 일부 빠짐"을 사람이 바로 볼 수 있게 한다.

권장 구현:

- quality label/signal/state log/bible/world state meta 저장 실패를 `soft_failure`로 적재
- 최근 1화 기준 non-blocking failure count를 `/quality/dashboard` 또는 별도 `/runtime/health`에 노출
- UI는 작은 경고 배지나 `Last Run Warnings` 영역으로만 표시

주의:
- Director 주권/합격 판정은 건드리지 않는다.

### P1-D. 브리지 `run_failed` 진단 payload 보강

대상:

- `modules/api/process_runner.py`
- `modules/api/bridge_server.py`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/index.html`

목표:
- `run_failed`가 "returncode만 있는 이벤트"에서 벗어나게 한다.

권장 payload:

- `returncode`
- `key`
- `sub_key`
- `last_stdout_tail`
- `stderr_tail`
- `last_prompt_step`
- `failure_phase_guess`
- `soft_failure_count`
- `started_at`
- `duration_ms`

UI 노출:
- 상세 패널 또는 Run Result Summary 하단 보조 영역
- 기본은 접힘, 필요 시 펼침

### P1-E. 실패 학습 경로 보강

대상:

- `modules/validation/validation_orchestrator.py`
- `modules/core/failure_learning.py`
- `modules/core/failure_analyzer.py`

목표:
- 실패 학습 기록 자체의 실패를 다시 학습 불능 상태로 방치하지 않는다.

권장 구현:

- `FailureLearner.record_failure()` 실패 시 `soft_failure` 적재
- stage / failure_type / source validator / sample description만이라도 남김
- `FailureAnalyzer`가 이 누락률을 summary에 포함할 수 있게 준비

## 4. 후순위

### P2. 운영 로그 위생 정리

- `logging.warning`의 INFO 남용 축소
- Stage 4 주변 `print()` 제거 또는 logging 전환
- `run_failed`와 `NETWORK_ERROR` 종료 artifact 분리

이건 필요하지만, `실패에서 배우기`와 `조용한 실패 방지`보다 우선순위가 낮다.

### P3. 전역 repo-wide logging sweep

조건:

- P1 적용 후에도 원인 추적이 어렵다
- soft_failure가 너무 많아 분류 체계가 필요하다
- 운영자가 warning flood 때문에 중요한 경고를 못 본다

그때 가서 아래를 친다.

- `print()`
- `logging.warning` INFO 남용
- `except Exception: pass`
- `debug-only` fallback 과다

## 5. 금지 사항

- 실패 학습을 명분으로 LLM 호출을 추가하지 않는다.
- 비차단 실패를 대량 hard fail로 승격하지 않는다.
- Director score schema나 주권 구조를 건드리지 않는다.
- 기존 `llm_calls`, `stage_attempts`, `episode_quality_labels`, `episode_quality_signals`를 깨지 않는다.

## 6. 테스트 계획

### 타깃 테스트

- `tests/test_session_logger.py` 또는 신규 soft_failure 테스트
- `tests/test_bridge_quality_summary.py`
- `tests/test_process_runner.py`
- `tests/test_risk_approval.py`
- `tests/test_validation_orchestrator.py`
- `tests/test_stage4_post_processor.py`

### 검증 포인트

- `SessionLogger` write/rotate 실패가 조용히 사라지지 않고 구조화 이벤트로 남는지
- `FailureAnalyzer.summary()` 실패 시 운영 집계가 남는지
- `ValidationOrchestrator` FailureLearner 실패가 `debug-only`에서 벗어났는지
- `run_failed` payload가 `returncode` 외 진단 정보를 담는지
- UI가 경고를 보여도 레이아웃이 깨지지 않는지

### 기준선

- `python -m pytest --collect-only -q tests` -> `3864 collected`
- 전체 `python -m pytest tests/ -q` -> `3848 passed, 16 skipped, 1 warning`
- 기존 1 warning 허용 (`PytestCollectionWarning`)

## 7. 3-Pass 감리 메모

### Pass 1. 정합성

수정한 오탐:

- `로깅 체계가 약하다`를 `로깅 체계가 없다`로 쓰지 않음
- `run_failed 미존재`가 아니라 `run_failed payload 얕음`으로 교정
- `실패 학습 경로 부재`가 아니라 `실패 학습 실패가 너무 조용함`으로 교정

### Pass 2. 안전성

안전 원칙:

- 새 LLM 호출 없음
- Director 주권 불변
- hard gate 추가 없음
- 먼저 `관측`과 `운영 가시성`만 강화

### Pass 3. 완전성

이번 문서는 아래 3축을 모두 포함한다.

1. 원천 로그 작성기 건강성
2. 실패 학습 경로의 누락 감지
3. 운영자/UI가 보는 failure summary 표면

따라서 `실패에서 배우기`와 `조용한 실패 방지`라는 요청 범위에 맞다.

### 구현 후 감리 결과

판정: `PASS`

- `SessionLogger` write/rotate 실패 -> `soft_failure + health snapshot` 확인
- `FailureAnalyzer.summary()` 부분 실패 -> 전체 summary 비전파 + `soft_failures.jsonl` 기록 확인
- `ValidationOrchestrator` FailureLearner 기록 실패 -> `audit_event` relay + file persist 경로 확인
- `Stage4PostProcessor` sidecar/state/meta 저장 실패 -> 비차단 유지 + 구조화 기록 확인
- `bridge run_failed` -> `returncode / failure_phase / last_prompt_step / stdout_tail / stderr_tail / duration_ms` 포함 확인
- `/quality/dashboard` -> `runtime_health` read-only 집계 확인

비차단 잔여:

- `runtime_health`는 현재 `soft_failures.jsonl` 전체를 읽어 최근 창을 만들므로, 파일이 매우 커지면 P2 최적화 여지가 있다.
- `npm run start:spike` auto-close 직전 `/quality/dashboard` fetch 실패 로그 1회는 종료 artifact로 남는다.

## 8. 최종 판정

이 작업은 `필요했고`, 현재 `P1 집중 보강`은 구현/검증까지 완료됐다.  
전역 전수 조사부터 시작하지 않고, `학습 연결 + 조용한 실패 표면화`에 집중한 접근이 맞았다.

한 줄 요약:

`지금 글도비의 로깅 문제는 “없음”이 아니라 “학습 연결과 운영 가시성의 마지막 20%가 약함”이었고, 이번 배치가 그 핵심 구간을 닫았다.`
