# Stage 2 Director 점수와 Thinking 출력 불일치 조사

작성일: 2026-03-13
대상 실행: `projects/00_test`, Arc 1 생성 세션

## 질문

실행 로그에 `**Decision: PASS. Score: 10`처럼 보이는 문구가 찍혔는데, 왜 Stage 2가 승인되었는가?

## 결론

`10점인데 승인`이 아니라, 실제 승인 점수는 `100점`이다.

- 승인 로직이 사용한 공식 판정값은 Director JSON 응답의 `score=100`.
- 화면에서 문제로 보인 `Score: 10`은 Director의 `thinking` 텍스트 말미가 잘린 비공식 디버그 문자열이다.
- 즉, 승인 로직과 `thinking` 출력이 서로 다른 소스를 사용한다.

## 핵심 증거

### 1. 같은 시각의 Director 감사 호출에서 공식 응답은 `PASS / 100`

`projects/00_test/logs/session/llm_io.jsonl`의 `2026-03-13T19:56:42` Director 레코드:

- `response.decision = "PASS"`
- `response.score = 100`
- `score_breakdown = 40 + 20 + 20 + 10 + 10 = 100`

즉, Director 감사의 공식 JSON 응답은 `PASS(100)`이다.

### 2. 같은 레코드의 `thinking`은 `Score: 10`에서 끊겨 있음

동일 레코드의 `thinking` tail:

```text
**Final Verdict:** ...
**Decision: PASS. Score: 10
```

이 문자열은 화면에서 잘린 것이 아니라, 세션 로그에 저장된 원문 자체가 여기서 끝난다.

### 3. Stage 2 승인 경로는 `thinking`이 아니라 `audit["score"]`를 사용

`modules/core/stage2_finalizer.py`에서:

- `585`~`591`: 사용자에게 공식 판정 `PASS (score=100)` 출력
- `633`~`637`: `audit.get("score", 0)`를 정수로 파싱
- `849`~`858`: 승인/게이트 판정에 `_score` 사용

즉, Stage 2 승인 여부는 `thinking` 문구가 아니라 Director JSON 응답 점수로 결정된다.

### 4. `thinking`은 별도 사이드채널로 수집된다

`modules/domain/agents/base_agent.py`에서:

- `1148`~`1156`: `response.candidates[0].content.parts` 중 `thought=True` 파트를 모아 `_thinking_text` 구성
- `755`: `_last_thinking`에 저장

즉, `thinking`은 모델의 사고 텍스트를 따로 모은 값이고, JSON 본문과는 별개다.

### 5. 세션 로거 절삭이 원인은 아님

`modules/core/session_logger.py`에서:

- `47`: `max_prompt_chars=200000`
- `169`~`176`: 이 길이를 넘을 때만 절삭

문제 레코드의 `thinking_len`은 `4675`자이므로, 세션 로거가 `Score: 100`을 `10`으로 자른 것이 아니다.

## 런타임 흐름 정리

### A. Arc 후보 비교 선택

`2026-03-13T19:56:01`

- `projects/00_test/logs/session/llm_io.jsonl`
- 공식 응답: `PASS_WITH_FIX`, `score=95`
- 사유: 자금 계산 불일치 수정 필요

이는 "후보 선택 + 수정 필요" 단계다.

### B. 전략적 무결성 감사

`2026-03-13T19:56:42`

- `projects/00_test/logs/session/llm_io.jsonl`
- 공식 응답: `PASS`, `score=100`
- `projects/00_test/logs/session/decisions.jsonl`
  - `stage=stage2`
  - `decision_type=arc`
  - `result=PASS`
  - `score=100`

즉, 최종 승인에 사용된 값은 `100`이다.

## 왜 사람 눈에는 `10점 승인`처럼 보였는가

원인은 두 겹이다.

### 1. `thinking` 자체가 불완전하다

같은 세션의 다른 Director `thinking`들도 문장 중간에서 끝난다.

- `2026-03-13T20:00:07` thinking tail: 후보 비교 설명 중간에서 종료
- `2026-03-13T20:01:44` thinking tail: 문장 중간에서 종료

즉, 현재 `thinking`은 "완결된 설명문"이라고 신뢰할 수 없다. 이번 건만 특이한 것이 아니라 세션 전반에서 끝맺음이 잘린 흔적이 있다.

### 2. 공식 판정 다음에 `thinking`을 그대로 출력한다

`modules/core/stage2_finalizer.py`:

- `590`~`591`: 공식 `PASS (score=100)` 출력
- `604`~`608`: `_director_thinking`을 그대로 UI에 출력

그래서 사용자는 이미 확정된 `PASS(100)` 뒤에 붙는 불완전한 `thinking` 꼬리를 연속된 판정 메시지처럼 읽게 된다.

### 3. 바로 다음 성공 경로에서 StateExtractor 로그가 이어져 혼선이 커진다

`modules/core/stage2_finalizer.py`:

- `1155`~`1157`: 성공 직후 `generate_arc_context_v60(...)` 호출

`modules/core/prompt_builder.py`:

- `566`~`576`: 내부에서 `state_extractor.extract_cumulative_state(...)` 호출 가능

세션 로그에서도 `Score: 10` 직후 곧바로 `ConstraintDB 업데이트`, `StateExtractor` 호출 로그가 이어진다. 시각적으로는 `thinking`이 판정 본문처럼 보이기 쉽다.

## 부가 발견사항

질문의 직접 원인은 아니지만, 같은 구간에 로그 정합성 이슈가 하나 더 있다.

`projects/00_test/logs/session/decisions.jsonl`에는 다음 두 레코드가 같이 존재한다.

- `2026-03-13T19:56:42`, `decision_type=arc`, `score=100`
- `2026-03-13T19:57:11`, `decision_type=arc_design`, `score=0`

원인:

- `modules/core/stage2_finalizer.py`의 성공 반환(`1286`~`1293`)에는 `score`가 없다.
- `modules/core/stage2_orchestrator.py` `741`~`748`은 `_fin.get("score", 0)`로 세션 결정을 기록한다.

즉, 성공 경로의 최종 `arc_design` 결정 로그는 현재 `0점`으로 저장될 수 있다. 이는 승인 로직 문제는 아니지만, 관측성 관점에서는 별도 수정 후보다.

## 판단

이번 실행은 `10점 승인`이 아니다.

- 실제 승인 점수: `100`
- 문제 문구의 정체: 잘린 `thinking` 텍스트
- 승인 로직 사용값: Director JSON 응답

## 권고

이번 조사에서는 코드 수정은 하지 않았다. 후속 수정 우선순위는 아래가 적절하다.

1. `thinking`을 판정 근거처럼 보이지 않게 "partial/debug only"로 명시
2. Stage 2 성공 반환값에 `score`를 포함시켜 `arc_design` 세션 로그 `0점` 문제 제거
3. 필요하면 `thinking` tail가 문장 중간에서 끝나는 현상을 별도 API/SDK 관측 이슈로 분리 조사

## 관련 파일

- `projects/00_test/logs/session/llm_io.jsonl`
- `projects/00_test/logs/session/decisions.jsonl`
- `projects/00_test/logs/session_20260313_195031.log`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/prompt_builder.py`
- `modules/core/session_logger.py`
- `modules/domain/agents/base_agent.py`
