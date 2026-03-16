<!-- [참고자료] -->
# TF-AR: Adaptive Retry 전략 선택 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | Adaptive Retry: error classification, strategy selection, retry context management |
| Source files | adaptive_retry.py:859줄 |
| TF Items | 12 (CRITICAL 2 / IMPORTANT 5 / INSIGHT 5) |

## 1. Executive Summary

`modules/core/adaptive_retry.py`는 세 개의 독립적 재시도 메커니즘을 하나의 파일에 담고 있다:

1. **AdaptiveRetryStrategy** (L70-433): V49.4 원본. 태스크 ID 기반 `RetryContext` 관리, 에러 분류(5종), 전략 선택, 프롬프트 주입.
2. **AdaptiveRetryManager** (L473-771): V54.3 강화판. 에피소드/에이전트 단위 실패 기록, 에러 분류(8종), 필살기 권장, FailureLearner 연동.
3. **retry_with_feedback** (L793-858): V65 범용 래퍼. 에러 분류/전략 선택 없이 순수 재시도+피드백 루프.

핵심 문제는 **두 분류기(classify_error vs record_failure)의 비대칭**, **V54.3 에러 타입 3종이 전략 맵에 누락**, **싱글턴 컨텍스트 무한 축적**이다.

## 2. Architecture / Data Flow Diagram (ASCII)

```
                      +-------------------+
                      | Caller (Stage4 /  |
                      | Analyst / Stage01)|
                      +--------+----------+
                               |
              +----------------+----------------+
              |                                 |
   [Path A: AdaptiveRetryStrategy]    [Path B: AdaptiveRetryManager]
              |                                 |
              v                                 v
   classify_error(error_info)         record_failure(ep, agent, error_info)
   L114-186                           L522-575
   (5 keyword lists)                  |
              |                       +-> strategy.classify_error()  [5종]
              v                       +-> V54.3 override keywords    [3종 추가]
   should_retry(task_id, error_info)  |
   L188-212                           v
   |                            get_retry_guidance(ep, agent)   L577-650
   | ctx.attempt >= max?        get_injection_prompt(ep, agent) L683-726
   |   yes -> return False      should_trigger_ultimate(ep, agent) L652-681
   |   no  -> attempt++         |
   v                            v
   get_retry_strategy(task_id, error_type, error_info)
   L214-252
   |
   | switch(error_type):
   |   CONSTRAINT_VIOLATION -> _strategy_for_constraint_violation  L254
   |   QUALITY_ISSUE        -> _strategy_for_quality_issue         L294
   |   STRUCTURE_ERROR      -> _strategy_for_structure_error       L324
   |   TIMEOUT              -> _strategy_for_timeout               L358
   |   QUOTA_EXCEEDED       -> _strategy_for_quota_exceeded        L381
   |   ** CHARACTER_INCONSISTENCY -> FALLS THROUGH (default) **
   |   ** LOGIC_ERROR             -> FALLS THROUGH (default) **
   |   ** SCOPE_OVERFLOW          -> FALLS THROUGH (default) **
   |   ** UNKNOWN                 -> FALLS THROUGH (default) **
   |
   v
   apply_strategy(task_id, base_prompt, strategy) -> modified_prompt
   L394-426

   [Path C: retry_with_feedback]   L793-858
   +-> func(attempt, feedback)
   +-> on_success(result)?  -> return (result, N, True)
   +-> on_failure(result, attempt) -> feedback
   +-> loop until max_attempts
```

```
  Singleton Lifecycle:

  Module load
      |
      v
  _adaptive_retry_instance = None   (L436)
  _adaptive_manager_instance = None (L774)
      |
      v
  get_adaptive_retry()  -> double-checked lock -> AdaptiveRetryStrategy()
  get_adaptive_manager() -> double-checked lock -> AdaptiveRetryManager()
      |
      v
  main_a.py L2071: self.adaptive_manager = _v50["get_adaptive_manager"]()
      |
      v
  NEVER RESET — contexts dict grows for entire process lifetime
```

## 3. TF Items

### TF-AR-01: V54.3 에러 타입 3종이 get_retry_strategy에서 누락 -- CRITICAL

- **Location**: `adaptive_retry.py:L241-L252` (`get_retry_strategy`)
- **Description**: `ErrorType` enum에는 8종+UNKNOWN=9개 값이 정의되어 있으나(L42-54), `get_retry_strategy`의 if-elif 체인은 5종(CONSTRAINT_VIOLATION, QUALITY_ISSUE, STRUCTURE_ERROR, TIMEOUT, QUOTA_EXCEEDED)만 처리한다. V54.3에서 추가된 CHARACTER_INCONSISTENCY, LOGIC_ERROR, SCOPE_OVERFLOW와 UNKNOWN은 모두 fall-through하여 L233-238의 기본 전략(빈 prompt_injection, temperature_delta=0.0)을 반환한다.
- **Evidence**:
  ```python
  # L241-252
  if error_type == ErrorType.CONSTRAINT_VIOLATION:
      strategy = self._strategy_for_constraint_violation(ctx, error_info)
  elif error_type == ErrorType.QUALITY_ISSUE:
      strategy = self._strategy_for_quality_issue(ctx, error_info)
  elif error_type == ErrorType.STRUCTURE_ERROR:
      strategy = self._strategy_for_structure_error(ctx, error_info)
  elif error_type == ErrorType.TIMEOUT:
      strategy = self._strategy_for_timeout(ctx, error_info)
  elif error_type == ErrorType.QUOTA_EXCEEDED:
      strategy = self._strategy_for_quota_exceeded(ctx, error_info)
  # CHARACTER_INCONSISTENCY / LOGIC_ERROR / SCOPE_OVERFLOW -> no handler
  return strategy
  ```
- **Impact**: V54.3 에러 타입으로 분류된 에러는 전략이 없어서 빈 프롬프트 주입+온도 무변경으로 재시도된다. 이는 동일한 실수를 반복하게 만들어 재시도 예산을 낭비한다.
- **Caveat**: 실제 호출 경로 분석 결과, `AdaptiveRetryStrategy.get_retry_strategy`는 테스트 외에 직접 호출 코드가 확인되지 않았다. 실전에서는 `AdaptiveRetryManager.get_injection_prompt` (L683)가 주로 사용되며, 이 경로에서는 `get_retry_guidance` (L577)가 V54.3 타입별 지침을 정상 생성한다. 따라서 실전 영향은 **AdaptiveRetryStrategy를 단독으로 사용하는 경우에만 발생**한다.
- **Suggested fix direction**: `get_retry_strategy`에 CHARACTER_INCONSISTENCY, LOGIC_ERROR, SCOPE_OVERFLOW 분기 추가. 또는 `get_retry_guidance`에서 이미 처리하므로 docstring에 "V54.3 타입은 AdaptiveRetryManager 경로에서만 지원" 명시.

---

### TF-AR-02: MAX_RETRIES_BY_TYPE에 V54.3 에러 타입 3종 누락 -- CRITICAL

- **Location**: `adaptive_retry.py:L79-L86` (`MAX_RETRIES_BY_TYPE`), `adaptive_retry.py:L88-L96` (`WAIT_TIME_BY_TYPE`)
- **Description**: `MAX_RETRIES_BY_TYPE`와 `WAIT_TIME_BY_TYPE` 딕셔너리에 CHARACTER_INCONSISTENCY, LOGIC_ERROR, SCOPE_OVERFLOW 키가 없다. `should_retry` (L205)에서 `self.MAX_RETRIES_BY_TYPE.get(error_type, 2)`로 기본값 2를 사용하고, `get_retry_strategy` (L234)에서 `self.WAIT_TIME_BY_TYPE.get(error_type, 1)`로 기본값 1초를 사용한다.
- **Evidence**:
  ```python
  # L79-86
  MAX_RETRIES_BY_TYPE = {
      ErrorType.CONSTRAINT_VIOLATION: 3,
      ErrorType.QUALITY_ISSUE: 2,
      ErrorType.STRUCTURE_ERROR: 2,
      ErrorType.TIMEOUT: 1,
      ErrorType.QUOTA_EXCEEDED: 3,
      ErrorType.UNKNOWN: 2,
  }
  # CHARACTER_INCONSISTENCY, LOGIC_ERROR, SCOPE_OVERFLOW -> 없음 -> default 2
  ```
- **Impact**: 기본값 2로 fallback하므로 즉시 크래시는 발생하지 않는다. 그러나 CHARACTER_INCONSISTENCY 같은 에러는 단순 재시도보다 캐릭터 프로필 재주입이 필요한데, 맹목적 2회 재시도는 의미 없는 API 호출 낭비가 된다. TF-AR-01과 결합하면 빈 전략+기본 횟수로 "아무것도 안 하면서 2번 반복"하는 상황이 된다.
- **Suggested fix direction**: 3종에 대한 명시적 max_retries/wait_time 값 추가. 예: `CHARACTER_INCONSISTENCY: 2, LOGIC_ERROR: 2, SCOPE_OVERFLOW: 2`.

---

### TF-AR-03: classify_error와 record_failure의 이중 분류 비대칭 -- IMPORTANT

- **Location**: `adaptive_retry.py:L114-L186` (`classify_error`), `adaptive_retry.py:L536-L548` (`record_failure` 내부)
- **Description**: 두 분류 경로가 존재한다:
  - **Path A** (classify_error L114): message+reason+violations를 결합한 combined_text에서 5개 키워드 리스트를 순서대로 매칭. violations 포함.
  - **Path B** (record_failure L536-548): classify_error를 먼저 호출한 뒤, message+reason만으로(violations 미포함) V54.3 키워드를 체크하여 결과를 덮어씀.

  문제점:
  1. classify_error가 먼저 "score"(품질 키워드)로 QUALITY_ISSUE를 반환해도, "캐릭터" 키워드가 있으면 record_failure가 CHARACTER_INCONSISTENCY로 덮어쓴다. 우선순위가 명확하지 않다.
  2. record_failure의 V54.3 override는 violations를 검사하지 않으므로, violations에만 "캐릭터" 키워드가 있는 경우 감지 불가.
  3. "초과" 키워드가 quota_keywords("할당량 초과"에 해당)와 SCOPE_OVERFLOW 키워드("범위", "초과") 양쪽에 해당할 수 있다. classify_error에서 QUOTA_EXCEEDED로 분류된 뒤 record_failure에서 "초과" 매칭으로 SCOPE_OVERFLOW로 덮어쓰기 가능.

- **Evidence**:
  ```python
  # L170 - quota_keywords
  quota_keywords = ["quota", "rate limit", "429", "too many", "할당량", "제한"]

  # L547 - SCOPE_OVERFLOW override
  elif any(k in combined for k in ["범위", "초과", "scope", "overflow"]):
      error_type = ErrorType.SCOPE_OVERFLOW
  ```
  "할당량 초과" 메시지 → classify_error가 `QUOTA_EXCEEDED` 반환 (L183: "할당량" 매칭) → record_failure가 "초과" 매칭으로 `SCOPE_OVERFLOW`로 덮어쓰기.
- **Impact**: API 할당량 초과 에러가 SCOPE_OVERFLOW로 오분류되면 30초 대기 대신 즉시 재시도하게 되어 rate limit을 더 악화시킬 수 있다.
- **Suggested fix direction**: (1) "초과" 단독 키워드를 SCOPE_OVERFLOW에서 제거하고 "범위 초과" 복합 키워드만 사용. (2) 또는 classify_error를 V54.3 타입까지 확장하여 단일 분류기로 통합.

---

### TF-AR-04: 싱글턴 컨텍스트 dict 무한 축적 (AdaptiveRetryStrategy) -- IMPORTANT

- **Location**: `adaptive_retry.py:L99` (`self.contexts`), `adaptive_retry.py:L436-L447` (싱글턴)
- **Description**: `AdaptiveRetryStrategy`는 싱글턴(L440-447)으로, `self.contexts: dict[str, RetryContext]`에 태스크 ID별 컨텍스트를 저장한다. `reset_context` (L109-112) 메서드가 존재하지만, **코드베이스 전체에서 한 번도 호출되지 않는다** (grep 결과 확인). 따라서 프로세스 수명 동안 모든 태스크의 RetryContext가 영구 보존된다.
- **Evidence**: `reset_context` 호출처 grep 결과: 0건 (정의만 존재).
  ```python
  # L109-112
  def reset_context(self, task_id: str):
      """컨텍스트 초기화"""
      with self._lock:
          self.contexts.pop(task_id, None)
  ```
  호출처 없음.
- **Impact**: 각 RetryContext는 error_history(list[dict]), injected_constraints(list[str]), prompt_modifications(list[str])를 포함한다. 장기 실행 세션에서 수백 개 태스크가 축적되면 메모리 부담이 증가한다. 다만 AdaptiveRetryManager의 `_failures`는 L557-558에서 max_history, L561-564에서 에피소드 키 50개 제한이 있으므로 Manager 쪽은 관리됨.
- **Suggested fix direction**: `apply_strategy` 또는 `should_retry`의 max_retries 도달 시 자동으로 `reset_context` 호출. 또는 contexts에 LRU/TTL 정책 적용.

---

### TF-AR-05: 동일 전략 재적용 방지 부재 -- IMPORTANT

- **Location**: `adaptive_retry.py:L188-L252` (should_retry + get_retry_strategy)
- **Description**: `should_retry`는 `ctx.attempt` 카운터만 증가시키고, `get_retry_strategy`는 에러 타입만으로 전략을 선택한다. **이전에 어떤 전략을 시도했는지 기록하지 않으므로**, 같은 에러 타입이 반복되면 동일한 전략이 동일하게 적용된다.

  예: CONSTRAINT_VIOLATION이 3회 연속 발생하면:
  - 1회차: `_strategy_for_constraint_violation` → 금지 목록 주입
  - 2회차: 동일 전략 → 금지 목록이 `ctx.injected_constraints`에 **중복 추가** (L284)
  - 3회차: 동일 전략 → 금지 목록 3중 중복

- **Evidence**:
  ```python
  # L284 - 매번 extend, 중복 체크 없음
  ctx.injected_constraints.extend(forbidden_items)
  ```
- **Impact**: 프롬프트에 중복 경고가 누적되어 토큰 낭비 발생. 다만 실제로는 다른 금지 항목이 추출되기도 하므로 "동일" 전략이라도 내용이 다를 수 있다. 진짜 문제는 전략 **에스컬레이션**이 없다는 것 -- 같은 에러가 반복되면 더 강한 전략(예: 필살기)으로 전환해야 하는데 AdaptiveRetryStrategy 단독 경로에서는 이 로직이 없다.
- **Suggested fix direction**: (1) `injected_constraints`에 set 기반 중복 제거 추가. (2) attempt 횟수에 따른 전략 에스컬레이션 로직 추가 (AdaptiveRetryManager의 ESCALATION_THRESHOLDS 패턴 참조).

---

### TF-AR-06: keyword "score"/"점수"의 과도한 매칭 범위 -- IMPORTANT

- **Location**: `adaptive_retry.py:L150-L161` (quality_keywords)
- **Description**: `quality_keywords`에 "score"와 "점수"가 포함되어 있다. 에러 메시지에 "score"가 등장하는 것은 매우 흔하며(JSON 응답에 점수 필드 포함 등), 의도하지 않은 QUALITY_ISSUE 오분류가 발생할 수 있다.
- **Evidence**:
  ```python
  # L150-161
  quality_keywords = [
      "밀도 부족", "density", "개연성", "plausibility",
      "품질", "quality", "미달", "insufficient",
      "score", "점수",  # <-- 너무 넓은 매칭
  ]
  ```
  예: `{"message": "missing required key: score"}` → "score" 매칭 → QUALITY_ISSUE로 분류. 실제로는 STRUCTURE_ERROR이어야 한다.

  그러나 순서 우선 매칭이므로 "missing"이 structure_keywords(L164)에 있어서 L179에서 먼저 STRUCTURE_ERROR로 분류된다. 문제는 "missing"이 없고 "score"만 있는 메시지에서 발생.
- **Impact**: 오분류 시 온도를 +0.1 올리는 전략이 적용되어 더 불안정한 출력이 발생할 수 있다.
- **Suggested fix direction**: "score" 단독 대신 "low score", "score 미달", "score insufficient" 등 복합 키워드 사용.

---

### TF-AR-07: keyword "제한"의 QUOTA_EXCEEDED 오매칭 -- IMPORTANT

- **Location**: `adaptive_retry.py:L170` (quota_keywords)
- **Description**: `quota_keywords`에 "제한"이 포함되어 있다. 한국어 에러 메시지에서 "제한"은 "범위 제한", "길이 제한", "문자 수 제한" 등 다양한 맥락에서 사용된다.
- **Evidence**:
  ```python
  # L170
  quota_keywords = ["quota", "rate limit", "429", "too many", "할당량", "제한"]
  ```
  예: `{"message": "출력 길이 제한 초과"}` → "제한" 매칭 → QUOTA_EXCEEDED. 실제로는 TIMEOUT이어야 한다.

  다만 timeout_keywords에 "절단"은 있지만 "길이 제한"은 없다. "length"가 timeout_keywords에 있지만 한국어 메시지에서는 매칭 안 됨.
- **Impact**: QUOTA_EXCEEDED로 분류되면 30초 대기가 발생하여 불필요한 지연이 생긴다.
- **Suggested fix direction**: "제한" 단독 대신 "할당량 제한", "rate 제한" 등 복합 키워드 사용.

---

### TF-AR-08: retry_with_feedback의 on_failure 예외 무시 -- INSIGHT

- **Location**: `adaptive_retry.py:L851-L854`
- **Description**: `on_failure` 콜백에서 예외 발생 시 bare except로 잡고 feedback을 빈 문자열로 설정한다. 예외 메시지가 로깅되지 않는다.
- **Evidence**:
  ```python
  # L851-854
  if on_failure:
      try:
          feedback = on_failure(result, attempt)
      except Exception:
          feedback = ""
  ```
- **Impact**: on_failure 콜백의 버그가 완전히 묻힌다. 피드백 없이 재시도하므로 재시도 품질이 저하되지만 크래시는 방지된다.
- **Suggested fix direction**: `except Exception as e:` + `logging.warning` 추가. 기존 프로젝트 정책(V64.P4 OPTIONAL)에 부합.

---

### TF-AR-09: should_trigger_ultimate의 type_counts 빈 체크 데드코드 -- INSIGHT

- **Location**: `adaptive_retry.py:L666-L671`
- **Description**: `should_trigger_ultimate`에서 `type_counts`가 빈 dict인지 체크(L670)하지만, 바로 위에서 `if len(failures) < 2: return False, ""` (L662)로 이미 필터했으므로 failures가 2건 이상이면 type_counts는 반드시 비어 있지 않다.
- **Evidence**:
  ```python
  # L666-671
  type_counts = defaultdict(int)
  for f in failures:
      type_counts[f.error_type] += 1

  if not type_counts:  # <-- 데드코드: failures가 2건 이상이면 도달 불가
      return False, "adversarial_self_play"
  ```
- **Impact**: 기능상 무해. 방어적 코딩이지만 사실상 도달 불가 경로.
- **Suggested fix direction**: 제거하거나 주석으로 방어적 가드임을 명시.

---

### TF-AR-10: get_retry_guidance의 type_counts 빈 체크 동일 패턴 -- INSIGHT

- **Location**: `adaptive_retry.py:L601-L613`
- **Description**: `get_retry_guidance`에서도 동일한 패턴. `failures`가 빈 리스트면 L593-599에서 이미 반환하므로, L606의 `if not type_counts:` 체크는 도달 불가.
- **Evidence**:
  ```python
  # L593-599
  if not failures:
      return { ... }

  # L601-606
  type_counts = defaultdict(int)
  for f in failures:
      type_counts[f.error_type] += 1

  if not type_counts:  # <-- 데드코드
      return { ... }
  ```
- **Impact**: 동일하게 무해. 데드코드.
- **Suggested fix direction**: TF-AR-09와 동일.

---

### TF-AR-11: Mutable Default Argument 점검 결과 -- INSIGHT

- **Location**: 전체 파일
- **Description**: Python의 대표적 함정인 mutable default argument (`def func(x=[])`) 패턴은 이 파일에서 **발견되지 않았다**. `RetryContext`(L58-67)는 `field(default_factory=list)`를 사용하여 올바르게 처리하고 있다. `FailureRecord`(L457-470)도 mutable default가 없다.
- **Evidence**:
  ```python
  # L63-67 - 올바른 패턴
  error_history: list[dict] = field(default_factory=list)
  injected_constraints: list[str] = field(default_factory=list)
  prompt_modifications: list[str] = field(default_factory=list)
  ```
- **Impact**: 없음. 양호.
- **Suggested fix direction**: 해당 없음.

---

### TF-AR-12: base_agent._classify_error와의 이중 분류 체계 -- INSIGHT

- **Location**: `adaptive_retry.py:L114-L186`, `base_agent.py:L1498-L1511`
- **Description**: `base_agent.py`에는 별도의 `_classify_error(self, error: Exception) -> str` 메서드가 있어서 Exception 객체를 분류한다. 이 분류기는 `AgentErrorType` 문자열 상수를 반환하며, `adaptive_retry.py`의 `ErrorType` enum과는 완전히 별개의 타입 체계이다.

  base_agent 분류: TIMEOUT, QUOTA_EXCEEDED, NETWORK_ERROR, MALFORMED_RESPONSE, UNKNOWN
  adaptive_retry 분류: CONSTRAINT_VIOLATION, QUALITY_ISSUE, STRUCTURE_ERROR, TIMEOUT, QUOTA_EXCEEDED, CHARACTER_INCONSISTENCY, LOGIC_ERROR, SCOPE_OVERFLOW, UNKNOWN

  두 체계는 연동되지 않으며, base_agent의 분류 결과가 adaptive_retry에 전달되지 않는다.
- **Impact**: 아키텍처 관점에서의 관찰. 현재는 각각 독립적으로 동작하므로 충돌은 없으나, base_agent의 NETWORK_ERROR가 adaptive_retry에서 감지되지 않아 네트워크 에러에 대한 적응형 재시도 전략이 없다.
- **Suggested fix direction**: 장기적으로 분류 체계 통합 고려. 단기적으로는 현행 유지 (별도 레이어이므로).

---

## 4. Summary Matrix

| ID | Title | Severity | Category | Impact |
|----|-------|----------|----------|--------|
| TF-AR-01 | V54.3 에러 타입 3종 get_retry_strategy 누락 | CRITICAL | Strategy Gap | 빈 전략으로 재시도, API 호출 낭비 |
| TF-AR-02 | V54.3 에러 타입 3종 MAX_RETRIES/WAIT_TIME 누락 | CRITICAL | Config Gap | 기본값 fallback으로 의미 없는 재시도 |
| TF-AR-03 | classify_error / record_failure 이중 분류 비대칭 | IMPORTANT | Classification | "초과" 키워드로 QUOTA→SCOPE 오분류 가능 |
| TF-AR-04 | 싱글턴 컨텍스트 dict 무한 축적 | IMPORTANT | Memory | 장기 세션에서 메모리 누적 |
| TF-AR-05 | 동일 전략 재적용 방지 부재 | IMPORTANT | Strategy | 중복 제약 누적, 에스컬레이션 없음 |
| TF-AR-06 | "score"/"점수" 과도한 매칭 | IMPORTANT | Classification | QUALITY_ISSUE 오분류 가능 |
| TF-AR-07 | "제한" 키워드 QUOTA 오매칭 | IMPORTANT | Classification | 불필요한 30초 대기 |
| TF-AR-08 | on_failure 예외 무시 | INSIGHT | Error Handling | 콜백 버그 무시 |
| TF-AR-09 | should_trigger_ultimate 데드코드 | INSIGHT | Code Hygiene | 도달 불가 분기 |
| TF-AR-10 | get_retry_guidance 데드코드 | INSIGHT | Code Hygiene | 도달 불가 분기 |
| TF-AR-11 | Mutable Default Argument 양호 | INSIGHT | Code Hygiene | 문제 없음 (확인 결과) |
| TF-AR-12 | base_agent 이중 분류 체계 | INSIGHT | Architecture | 독립 레이어, 현재 무해 |

## 5. 핵심 코드 참조 (Appendix)

### A. ErrorType enum 전체 정의 (L42-54)

```python
class ErrorType(Enum):
    CONSTRAINT_VIOLATION = "constraint_violation"
    QUALITY_ISSUE = "quality_issue"
    STRUCTURE_ERROR = "structure_error"
    TIMEOUT = "timeout"
    QUOTA_EXCEEDED = "quota_exceeded"
    CHARACTER_INCONSISTENCY = "character_inconsistency"  # V54.3
    LOGIC_ERROR = "logic_error"                          # V54.3
    SCOPE_OVERFLOW = "scope_overflow"                     # V54.3
    UNKNOWN = "unknown"
```

### B. classify_error 키워드 순서 (L134-184)

| 순서 | 타입 | 키워드 (Korean) | 키워드 (English) |
|------|------|----------------|-----------------|
| 1 | CONSTRAINT_VIOLATION | 중복 획득, 이미 보유, 연속성, 상태 불연속, 획득 금지, 재획득 | duplicate, already, continuity, state mismatch, forbidden |
| 2 | QUALITY_ISSUE | 밀도 부족, 개연성, 품질, 미달, **점수** | density, plausibility, quality, insufficient, **score** |
| 3 | STRUCTURE_ERROR | 파싱, 누락 | json, parsing, key, missing, required, schema, format |
| 4 | TIMEOUT | 절단, 시간 초과 | timeout, max_tokens, length, truncate |
| 5 | QUOTA_EXCEEDED | 할당량, **제한** | quota, rate limit, 429, too many |

### C. record_failure V54.3 override 키워드 (L543-548)

| 우선순위 | 타입 | 키워드 |
|----------|------|--------|
| 1 | CHARACTER_INCONSISTENCY | 캐릭터, 말투, 성격, character |
| 2 | LOGIC_ERROR | 논리, 모순, 인과, logic |
| 3 | SCOPE_OVERFLOW | 범위, **초과**, scope, overflow |

### D. 필살기 매핑 (L485-492)

| 에러 타입 | 권장 필살기 | 설명 |
|-----------|------------|------|
| QUALITY_ISSUE | adversarial_self_play (ASP) | 품질 향상용 자기 대결 |
| CHARACTER_INCONSISTENCY | adversarial_self_play (ASP) | 캐릭터 일관성 검증 |
| STRUCTURE_ERROR | tree_of_thoughts (ToT) | 구조적 탐색 |
| SCOPE_OVERFLOW | tree_of_thoughts (ToT) | 범위 제어 |
| CONSTRAINT_VIOLATION | multi_agent_deliberation (MAD) | 제약 조건 심의 |
| LOGIC_ERROR | multi_agent_deliberation (MAD) | 논리적 모순 심의 |
| TIMEOUT / QUOTA_EXCEEDED / UNKNOWN | adversarial_self_play (기본값) | 매핑 없을 때 기본 |

### E. RetryContext 필드 (L58-67)

```python
@dataclass
class RetryContext:
    attempt: int = 0
    max_attempts: int = 3
    error_history: list[dict] = field(default_factory=list)     # 무한 성장 가능
    injected_constraints: list[str] = field(default_factory=list) # 중복 누적 (TF-AR-05)
    temperature_delta: float = 0.0
    should_use_schema: bool = True
    prompt_modifications: list[str] = field(default_factory=list) # 무한 성장 가능
```

### F. 실전 호출 경로 (stage4_interview_round.py L3622-3636)

```python
# Stage4에서 REJECT 시 AdaptiveRetryManager 호출
_adaptive_mgr = getattr(self.ctx, "adaptive_manager", None)
if _adaptive_mgr is not None and hasattr(_adaptive_mgr, "record_failure"):
    _adaptive_mgr.record_failure(
        ep_num=next_ep,
        agent="director",
        error_info={"reason": director_feedback[:200], "bucket": _reject_bucket},
        attempt=round_num + 1,
    )
    if hasattr(_adaptive_mgr, "get_injection_prompt"):
        _injection = _adaptive_mgr.get_injection_prompt(
            ep_num=next_ep, agent="director", current_attempt=round_num + 1
        )
```

Note: 이 경로에서는 `AdaptiveRetryManager.record_failure` → `get_injection_prompt` 순서로 호출되며, `AdaptiveRetryStrategy.get_retry_strategy`는 호출되지 않는다. 따라서 TF-AR-01/02의 CRITICAL 항목은 이 경로에서는 영향이 없고, `AdaptiveRetryStrategy`를 직접 사용하는 경로에서만 영향이 있다.
