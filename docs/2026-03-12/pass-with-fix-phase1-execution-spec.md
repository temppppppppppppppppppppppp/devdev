# PASS_WITH_FIX Phase 1 실행 스펙

작성일: 2026-03-12  
상위 문서: `docs/2026-03-12/pass-with-fix-master-roadmap.md`  
문서 역할: `Phase 1. 계약 고정`을 구현자가 바로 착수할 수 있는 수준으로 구체화한 실행 스펙

## 0. 상태

이 문서는 코드 수정 문서가 아니라 `Phase 1 구현 전 decision-complete 실행 스펙`이다.

이번 Phase 1의 직접 목적은 아래 4개다.

1. `PASS_WITH_FIX` 계약을 하나로 고정
2. Stage 3 external contract를 고정
3. Stage 4 final score/label semantics를 고정
4. logging sink 역할을 고정

이번 Phase 1의 직접 비대상은 아래와 같다.

- `CW 일반 글쓰기 생성 구조` 변경
- structural inplace 구현
- full logging overhaul
- analytics/DB 집계 로직 실제 개편
- live rerun

## 1. 3-Pass 재감리 결과

### Pass 1. 문서 계약 재확인

확인된 사실:

- `docs/2026-03-01/verdict-logic-spec.md`는 `PASS_WITH_FIX`를 과도 상태로 규정한다.
- `docs/stage_map/interfaces.md`, `docs/stage_map/gotchas.md`, `docs/stage_map/stage2.md`, `docs/stage_map/stage3.md`, `docs/stage_map/stage4.md`는 `PASS_WITH_FIX`를 Director verdict 3종과 bypass 흐름으로 설명한다.
- 문서 SSOT가 갈라져 있으므로 Phase 1에서 먼저 계약 문구를 잠그지 않으면 구현이 흔들린다.

Phase 1 문서 판단:

- `PASS_WITH_FIX`는 기본적으로 `transient/internal verdict`로 고정한다.
- 다만 `PASS_WITH_WARNING`은 별도 degraded-success verdict로 남아 있으므로, `PASS_WITH_FIX 정리`와 혼합하지 않는다.

### Pass 2. 코드 계약 재확인

확인된 사실:

- Stage 3는 `modules/domain/agents/three_phase_blueprint_generator.py`에서 `pipeline_result["final_verdict"] = verdict`로 `PASS_WITH_FIX`를 보존할 수 있다.
- Stage 3 orchestrator는 `modules/core/stage3_orchestrator.py`에서 `PASS`, `PASS_WITH_FIX`, `PASS_WITH_WARNING`을 success 경로로 처리한다.
- Stage 4는 `modules/core/stage4_interview_round.py`에서 `save_director_selection()`과 `_append_episode_log()`를 `_process_verdict()`보다 먼저 호출한다.
- Stage 4는 `_execute_pass_with_fix_loop()` 이후에도 `_process_verdict()`에서 최초 `score` 변수를 `director_score`, `_director_quality_labels`, `_record_s4_attempt()`에 사용한다.
- FailureAnalyzer와 DB query는 `PASS_WITH_FIX`를 pass-like verdict로 집계한다.

Phase 1 문서 판단:

- Phase 1은 Stage 3 external success set과 Stage 4 final score semantics를 우선 잠가야 한다.
- analytics 집계는 Phase 1에서 구현하지 않더라도, Phase 1 문서상 기본 계약은 명시해야 한다.

### Pass 3. 테스트/운영 산출물 재확인

확인된 사실:

- `tests/test_pass_with_fix.py`는 Stage 3의 `final_verdict=PASS_WITH_FIX`를 success로 처리하는 현재 의미를 고정하고 있다.
- `tests/test_stage4_interview_round.py`는 Stage 4 metadata 저장과 round log 저장을 검증하지만, `PASS_WITH_FIX -> PASS` 후 final score가 재심사 score로 갱신되는지 확인하는 테스트는 없다.
- `projects/00_test_03` 기준으로 `episode_production.jsonl`/`director_selections`와 `stage_attempts`/`pass_rate_monitor`가 서로 다른 의미를 사용한다.

Phase 1 문서 판단:

- Phase 1 구현은 반드시 테스트 수정/추가를 동반해야 한다.
- sink 역할은 운영 문서에서 먼저 잠가야 한다.

## 2. Phase 1에서 잠글 결정

Phase 1은 아래 결정을 확정한다.

### 2.1 PASS_WITH_FIX 계약

- 기본 계약: `PASS_WITH_FIX = transient/internal verdict`
- 의미: `수정 가능성이 높으므로 patch/retry 루프로 보낸다`
- 외부 최종 verdict 기본안: `PASS` 또는 `REJECT`

### 2.2 PASS_WITH_WARNING 처리

이번 initiative의 기본 범위에서 `PASS_WITH_WARNING`은 별도 degraded-success verdict로 유지한다.

이 결정이 필요한 이유:

- 현재 Stage 3 fallback 경로에 이미 존재한다.
- `PASS_WITH_FIX`와 `PASS_WITH_WARNING`을 한 Phase에서 동시에 정리하면 scope가 불필요하게 커진다.

즉, 이번 Phase 1의 규칙은 아래처럼 잠근다.

- `PASS_WITH_FIX`는 외부 최종 success set에서 제거
- `PASS_WITH_WARNING`은 현행 별도 degraded-success 예외로 유지

### 2.3 Stage 3 external success set

Phase 1 기본안:

- success path 허용: `PASS`, `PASS_WITH_WARNING`
- success path 제외: `PASS_WITH_FIX`

따라서 Stage 3는 아래 원칙으로 정리한다.

- 내부 patch loop 중에는 `PASS_WITH_FIX` 사용 가능
- stage boundary를 넘길 때는 `PASS` 또는 `REJECT`로 닫는 것을 기본으로 한다
- 불가피한 fallback degraded-success는 `PASS_WITH_WARNING`만 유지한다

### 2.4 Stage 4 final score semantics

Phase 1 기본안:

- `PASS_WITH_FIX -> patch -> PASS`가 성립하면 최종 score는 `재심사 score`
- 최종 label도 `재심사 verdict + 재심사 score` 기준

최소 동기화 대상:

- `director_score`
- `_director_quality_labels.score`
- `_director_quality_labels.verdict`
- `stage_attempts.score`
- `stage_attempts.verdict`

### 2.5 sink 역할

Phase 1 기본안:

- `director_selections`: 초기 Director 선택/판정
- `episode_production.jsonl`: round trace
- `stage_attempts`: 최종 stage attempt 결과
- `pass_rate_monitor.json`: 운영 최종 집계

Phase 1에서 요구하는 것은 `sink 역할 고정`이지, 즉시 full schema 재설계가 아니다.

## 3. 구현 작업 패키지

### WP-1. Stage 3 external contract 정리

목표:

- Stage 3가 `PASS_WITH_FIX`를 외부 success verdict로 내보내지 않게 정리

대상 코드:

- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage3_orchestrator.py`
- `tests/test_pass_with_fix.py`
- Stage 3 관련 문서

구현 요구:

- `PASS_WITH_FIX`는 stage boundary 직전 `PASS` 또는 `REJECT`로 닫히도록 정리
- `PASS_WITH_WARNING`은 Phase 1 범위에서 유지
- success set 변경에 맞춰 테스트 기대값 수정

acceptance:

- Stage 3 success path에 `PASS_WITH_FIX`가 직접 들어가지 않는다
- 기존 `PASS_WITH_WARNING` fallback은 깨지지 않는다
- 관련 문서가 새 계약과 같은 의미를 쓴다

### WP-2. Stage 4 final score/label semantics 정리

목표:

- `PASS_WITH_FIX -> patch -> PASS` 후 final score가 stale하지 않도록 정리

대상 코드:

- `modules/core/stage4_interview_round.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_pass_with_fix.py`

구현 요구:

- patch loop가 최종 verdict뿐 아니라 최종 score/최종 audit payload를 상위로 전달하는 경로를 명시
- `_process_verdict()`는 최종 결과 기록 시 최초 score가 아니라 최종 score를 사용

acceptance:

- `director_score == re-audit score`
- `_director_quality_labels.score == re-audit score`
- `stage_attempts.score == re-audit score`
- `stage_attempts.verdict == final verdict`

### WP-3. sink 계약 문서화

목표:

- 운영자가 초기판정/최종결과를 혼동하지 않도록 문서 계약을 고정

대상 문서:

- `docs/2026-03-12/pass-with-fix-master-roadmap.md`
- `docs/2026-03-12/pass-with-fix-improvement-execution-plan.md`
- `docs/2026-03-12/stage4-live-rerun-checklist.md`

구현 요구:

- sink 의미를 한 문구로 통일
- rerun 체크리스트가 그 의미를 따르도록 보장

acceptance:

- 세 문서가 동일한 sink 역할 정의를 사용
- `episode_production`은 round trace, `stage_attempts`는 final outcome이라는 점이 명확하다

### WP-4. analytics 정합성 TODO 고정

목표:

- analytics/DB 집계 개편은 Phase 2 이후로 미루되, Phase 1 문서에서 TODO를 확정

대상 코드/문서:

- `modules/core/failure_analyzer.py`
- `modules/core/db_manager.py`
- 관련 테스트
- 실행 메모 문서

구현 요구:

- Phase 1에서 즉시 집계 로직을 바꾸지 않더라도, 어떤 쿼리/집계가 `PASS_WITH_FIX`를 pass-like로 보고 있는지 명시
- Phase 2 이후 수정 대상 목록을 고정

acceptance:

- analytics 미정 상태가 문서상 숨겨지지 않는다
- 후속 Phase에서 손댈 코드 목록이 명시된다

## 4. 테스트 패키지

Phase 1 구현 시 필수 테스트는 아래와 같다.

### Stage 3

- `PASS_WITH_FIX`가 success path로 직접 들어가지 않는지
- `PASS_WITH_WARNING`은 기존 degraded-success 경로를 유지하는지

### Stage 4

- `PASS_WITH_FIX -> patch -> PASS` 후 final score가 재심사 score인지
- `PASS_WITH_FIX -> patch -> PASS` 후 `_director_quality_labels`가 재심사 기준인지
- `PASS_WITH_FIX -> patch -> PASS` 후 `stage_attempts`가 final semantics를 반영하는지

### 문서/운영 계약

- sink 역할 정의가 master/execution/rerun 문서에서 일치하는지

## 5. Phase 1 완료 기준

아래가 모두 충족되면 Phase 1 완료로 본다.

1. `PASS_WITH_FIX`의 external contract가 문서와 코드에서 일치
2. Stage 3 success set에서 `PASS_WITH_FIX` 제거
3. Stage 4 final score/label/attempt semantics 정합화
4. sink 역할이 문서에 고정
5. analytics 집계 개편 대상이 TODO로 명시
6. 관련 테스트가 새 계약을 고정

## 6. 롤백 기준

아래 중 하나가 발생하면 Phase 1은 merge 대상에서 제외한다.

- Stage 3 fallback semantics가 `PASS_WITH_WARNING`까지 함께 깨짐
- Stage 4 final score 정합화가 sink 계약과 충돌
- 새 계약을 반영한 테스트가 기존 운영 의미와 해석 불가능한 수준으로 어긋남

## 7. Phase 1 이후 바로 이어질 다음 단계

Phase 1 종료 후 다음 단계는 아래로 고정한다.

1. 실제 `PASS_WITH_FIX` 사례 재분류
2. `local/global` taxonomy 고정
3. structural inplace 설계
4. 최소 계측
5. 오프라인 회귀/골든 검증

즉, Phase 1 다음은 곧바로 rerun이 아니라 `Phase 2 추가 컨텍스트 수집`이다.
