<!-- [참고자료] -->
# TF-BA: Base Agent 컨텍스트 캐싱 딥다이브

| Field | Value |
|-------|-------|
| Baseline | bbb00a77 |
| Date | 2026-03-15 |
| Scope | Base Agent: context caching, provider fallback, JSON extraction, cost tracking, error classification |
| Source files | base_agent.py:2141줄 |
| TF Items | 14 (CRITICAL 2 / IMPORTANT 7 / INSIGHT 5) |

---

## 1. Executive Summary

Base Agent의 `ask()` 메서드는 LLM 호출, 재시도, 폴백, 비용 추적, 컨텍스트 캐싱을 통합한 ~250줄 규모의 제어 흐름이다. 전반적으로 방어적 프로그래밍이 잘 되어 있으나, 다음 핵심 문제가 발견되었다:

1. **CRITICAL**: 로컬 TTL과 서버 TTL 간 drift로 인해 만료된 캐시 이름으로 API 호출이 발생할 수 있고, 이 경우 `_ask_with_cached_context`가 `ask()`로 재귀 폴백하면서 비용이 이중 기록된다.
2. **CRITICAL**: `_ask_with_cached_context` 경로에 MetricsCollector `start_call`/`end_call` 페어가 완전히 누락되어 전체 비용 추적에 빈 구간이 존재한다.
3. **IMPORTANT**: 폴백 config에서 `http_options` 누락, 에러 분류의 overlap, JSON 추출 fallback의 데이터 손실 등 7건의 개선 필요 사항이 존재한다.

---

## 2. Architecture / Data Flow Diagram (ASCII)

```
                              ask(prompt, temperature, ...)
                                      |
                     +----------------+----------------+
                     |                                 |
               _build_model_stack()            _reset_usage_tracking()
               (model_stack, config,           last_partial_response = ""
                metric_id via start_call)
                     |
                     v
             +===============================+
             |  MAIN LOOP (max 5 attempts)   |
             |  while attempt < 5:           |
             |    sleep(API_DELAY)           |
             |    _generate_content()        |---> GeminiProvider.generate()
             |         |                     |          |
             |    on SUCCESS:                |     LLMResponse.raw returned
             |      _accumulate_usage()      |
             |      _extract_and_merge()     |
             |         |                     |
             |    if MAX_TOKENS:             |
             |      continuation prompt      |
             |      attempt++; continue      |
             |    else:                      |
             |      break                    |
             |         |                     |
             |    on ERROR:                  |
             |      _handle_api_error()      |
             |        |                      |
             |   +----+-----+-----+         |
             |   |NET  |RATE |QUOTA|         |
             |   |retry|back |fall |         |
             |   |     |off  |back |         |
             |   +----+-----+-----+         |
             +===============================+
                     |
          +----------+----------+
          |                     |
     SUCCESS path          EXCEPTION path
          |                     |
   end_call(success=True)  _classify_error()
   _log_llm_call_to_db()  end_call(success=False)
   session_logger.log()    _attempt_backup_recovery()
   return full_response         |
                          +-----+------+
                          |            |
                     backup OK    backup FAIL
                          |            |
                     return text  return partial/error


    _ask_with_cached_context(cache_name, prompt, ...)
                     |
              cache_name empty? --YES--> ask(fallback)
                     |
                    NO
                     |
              wrap prompt
              build config with cached_content=cache_name
              _generate_content()
                     |
              +------+------+
              |             |
         SUCCESS        EXCEPTION
              |             |
         return text    log warning
                        ask(fallback)   <-- recursive fallback


    _get_or_create_context_cache(cache_type, content, ttl, project_name)
                     |
              compute content_hash (MD5)
              build cache_key
                     |
         +--- Lock: _cache_lock ---+
         |  check _context_caches  |
         |  if hit & TTL valid:    |
         |    return cached name   |
         |  if expired:            |
         |    pop(cache_key)       |
         +---------+---------------+
                   |
              content < 50K chars? --YES--> return None
                   |
              client.caches.create()  (Gemini API)
                   |
         +--- Lock: _cache_lock ---+
         |  store cache info       |
         |  evict if > MAX entries |
         +---------+---------------+
                   |
              return cache_name
```

---

## 3. TF Items

### TF-BA-01: 로컬 TTL vs 서버 TTL Drift — 만료 캐시 사용 가능 — CRITICAL

- **Location**: `base_agent.py:L1893-L1905` (로컬 TTL 체크) + `L1919-L1926` (서버 TTL 설정)
- **Description**: `_get_or_create_context_cache`는 로컬 `_context_caches` 딕셔너리에 `created_at` 타임스탬프를 저장하고, 이를 `ttl_seconds`와 비교하여 캐시 유효성을 판단한다. 동시에 Gemini API에는 `ttl=f"{ttl_seconds}s"`를 전달한다. 그러나 두 타이머가 동기화되지 않는다:
  - 로컬 `created_at`은 API 호출 **전**(`L1893`)에 캡처된다
  - 서버 TTL은 API가 캐시를 **생성한 시점**부터 시작한다
  - API 호출 지연(수 초 가능)만큼 로컬 TTL이 서버보다 빨리 만료된다고 볼 수 있으나, 실제 문제는 **반대 방향**이다
  - 서버의 TTL은 정확히 `ttl_seconds`초 후 만료되지만, 로컬 체크는 `current_time - created_at < ttl_seconds`이므로 **거의 동시에 만료**된다
  - 진짜 문제: 경계 타이밍에서 로컬은 아직 유효하다고 판단하여 `cache_name`을 반환하지만, 서버에서는 이미 만료되어 `_ask_with_cached_context`가 404/NOT_FOUND 에러를 받을 수 있다
- **Evidence**:
  ```python
  # L1893: current_time 캡처 (API 호출 전)
  current_time = time.time()
  # L1900: 로컬 TTL 체크
  if current_time - cached_info["created_at"] < ttl_seconds:
      return {"cache_name": cached_info.get("name"), "cached": True, ...}
  # L1933: created_at에 API 호출 전 시간 저장
  self._context_caches[cache_key] = {
      "name": cache.name,
      "created_at": current_time,  # API 호출 전 시간!
  }
  ```
- **Impact**: TTL 경계(599~601초 구간)에서 로컬은 유효라고 판단하여 캐시 이름을 반환하지만 서버에서는 만료된 상태. `_ask_with_cached_context`에서 에러 발생 → `ask()`로 폴백되면서 최소 수 초 지연 + 비용 이중 발생. 야간 무인 운영에서 10분 TTL(600s) 캐시가 경계에 도달할 확률이 높다.
- **Suggested fix direction**: 로컬 TTL 체크에 safety margin 적용 (예: `ttl_seconds - 30`으로 30초 일찍 만료 처리). 또는 `created_at`을 API 응답 이후에 설정.

---

### TF-BA-02: `_ask_with_cached_context` 경로 MetricsCollector 완전 누락 — CRITICAL

- **Location**: `base_agent.py:L1959-L2081`
- **Description**: `_ask_with_cached_context`는 `_generate_content`를 직접 호출하지만, `MetricsCollector.start_call()`/`end_call()` 페어가 전혀 없다. `ask()` 메서드는 `_build_model_stack()` 내에서 `start_call()`을 수행하고(L998-L1005), 성공/실패 시 `end_call()`을 호출하지만(L773-L784, L853-L870), `_ask_with_cached_context`는 이 경로를 완전히 우회한다.
- **Evidence**:
  ```python
  # L1959-L2081: _ask_with_cached_context 전체 메서드
  # "metric_id", "start_call", "end_call" 문자열이 단 한 번도 등장하지 않음
  # DB 로깅은 L2051-L2061에서 수행하지만 MetricsCollector는 누락
  ```
- **Impact**: 컨텍스트 캐시 기반 호출(ChiefWriter, ArcEnsemble, BlueprintEnsemble, DirectorEnsemble, DirectorContinuity 등 5개 에이전트)의 토큰/비용이 MetricsCollector 집계에서 빠진다. 세션 리포트의 비용 합계가 실제보다 상당히 낮게 집계된다. `_log_llm_call_to_db`는 호출되므로 DB에는 기록되지만, MetricsCollector의 인메모리 집계(`_scope_cost`, `_scope_tokens`, `_model_tokens`)와 불일치한다.
- **Suggested fix direction**: `_ask_with_cached_context` 시작부에 `start_call()` 추가, 성공/실패 분기 각각에 `end_call()` 추가. `_build_metric_usage_payload` 재사용.

---

### TF-BA-03: 폴백/백업 config에서 `http_options` 누락 — IMPORTANT

- **Location**: `base_agent.py:L1177-L1193` (쿼터 폴백 config) + `L1338-L1346` (백업 모델 config)
- **Description**: 메인 `ask()` 경로의 config는 `http_options`로 타임아웃을 설정한다(L973). 그러나 쿼터 폴백(`_handle_api_error`, L1177-L1193)과 백업 모델(`_attempt_backup_recovery`, L1338-L1346)의 config 재생성 시 `http_options`가 누락된다.
- **Evidence**:
  ```python
  # L973 (메인 config) — http_options 포함
  config_params = {
      ...
      "http_options": types.HttpOptions(timeout=max(10_000, int(self.API_TIMEOUT) * 1000)),
  }

  # L1177 (폴백 config) — http_options 누락!
  fallback_config_params = {
      "temperature": temperature,
      "max_output_tokens": self.MAX_OUTPUT_TOKENS,
      "top_p": 0.95,
      "response_mime_type": "application/json",
  }

  # L1338 (백업 config) — http_options 누락!
  backup_config_params = {
      "temperature": temperature,
      "max_output_tokens": self.MAX_OUTPUT_TOKENS,
      "top_p": 0.95,
      "response_mime_type": "application/json",
  }
  ```
- **Impact**: 폴백/백업 모델 호출 시 SDK 기본 타임아웃이 적용된다. `self.API_TIMEOUT`은 기본 300초(5분)이며, SDK 기본값이 이보다 짧으면 야간 무인 운영 시 불필요한 타임아웃 발생 가능. SDK 기본값이 더 길면 비용 폭증 방지 실패.
- **Suggested fix direction**: config 생성을 `_build_config()` 헬퍼로 통합하여 일관성 보장.

---

### TF-BA-04: `_classify_error`와 `_is_network_error` 분류 중복/충돌 — IMPORTANT

- **Location**: `base_agent.py:L1498-L1511` (`_classify_error`) + `L1543-L1560` (`_is_network_error`)
- **Description**: 두 메서드가 에러를 독립적으로 분류하지만 기준이 충돌한다:
  - `_classify_error`: "timeout" → `TIMEOUT`, "connection"/"network"/"ssl" → `NETWORK_ERROR`
  - `_is_network_error`: "timeout", "connection", "network", "ssl" 모두 네트워크 에러로 분류
  - 따라서 타임아웃 에러는 `_classify_error`에서는 `TIMEOUT`이지만 `_is_network_error`에서는 `True`
  - `_handle_api_error`(L1053)에서 `_is_network_error`가 먼저 체크되므로, **타임아웃 에러도 네트워크 재시도 경로로 진입**한다
- **Evidence**:
  ```python
  # L1053: _is_network_error가 먼저 체크됨
  if self._is_network_error(api_error) and network_retry_count < self.MAX_NETWORK_RETRIES:
      # 이 분기에 타임아웃도 진입 (최대 22회 재시도)

  # L1498-L1503: _classify_error에서는 timeout을 별도로 분류
  if "timeout" in error_str or "timed out" in error_str or "deadline" in error_str:
      return AgentErrorType.TIMEOUT
  ```
- **Impact**: 순수 API 타임아웃(서버 과부하 등)도 네트워크 재시도 경로(최대 22회, 10~30초 백오프)로 진입한다. 최악의 경우 22 * 30 = 660초(11분) 동안 재시도가 반복될 수 있다. 타임아웃의 원인이 프롬프트 크기라면 재시도가 무의미하다.
- **Suggested fix direction**: `_is_network_error`에서 "timeout"을 제외하거나, `_handle_api_error`에서 타임아웃 전용 분기를 네트워크 분기 전에 추가. 타임아웃 시 프롬프트 크기 기반 판단 로직 추가 검토.

---

### TF-BA-05: `_extract_json_robust` 평탄화 엔진의 데이터 구조 변환 — IMPORTANT

- **Location**: `base_agent.py:L1742-L1786`
- **Description**: `process_node()` 재귀 함수가 JSON 응답을 평탄화할 때, 원본 데이터 구조가 **비가역적으로 변환**된다:
  1. 중첩 dict의 모든 키-값이 최상위 `final_dict`에 병합된다 (L1776-L1778)
  2. 동일 키가 여러 깊이에 존재하면 나중 방문이 이전 값을 덮어쓴다 (`if clean_k not in final_dict or val is not None`)
  3. 리스트 내 dict들의 키가 모두 최상위로 올라와 구조 정보가 소실된다
  4. `_RECURSE_KEYS` (`actual_truth`, `ProjectData`, `MasterBible`)에 해당하는 키의 값은 재귀 처리 후 **자체도 final_dict에 추가**됨 (L1770-L1778의 for 루프가 모든 키를 순회)
- **Evidence**:
  ```python
  # L1770-L1778: 모든 키를 순회하면서 RECURSE_KEYS도 최상위에 추가
  for k, val in node.items():
      if k in _RECURSE_KEYS and isinstance(val, dict | list):
          process_node(val, depth + 1)  # 자식을 평탄화
      else:
          clean_k = str(k).strip("'\" ")
          if clean_k not in final_dict or val is not None:
              final_dict[clean_k] = val  # 모든 키가 최상위로
  ```
  주목: `_RECURSE_KEYS`에 해당하는 키는 `if k in _RECURSE_KEYS` 분기로 진입하여 `else` 블록을 실행하지 **않으므로**, 해당 키 자체(`actual_truth` 등)는 final_dict에 추가되지 않는다. 이것은 의도적 설계일 수 있으나, 해당 키의 값(원본 dict/list)에 접근할 방법이 사라진다.
- **Impact**: 호출자가 원본 구조(예: `{"state_updates": {"characters": [...], "world": {...}}}`)를 기대하는데 평탄화되어 `characters`와 `world`가 최상위 키로 올라오면, 호출자의 `.get("state_updates")` 호출이 `None`을 반환하거나 예기치 않은 값을 반환할 수 있다. 다만 현재 코드에서 `state_updates`는 `_RECURSE_KEYS`에 포함되지 않으므로 직접적 피해는 제한적.
- **Suggested fix direction**: `_RECURSE_KEYS` 목록 검토. 평탄화 로직이 필요한 호출자와 원본 구조가 필요한 호출자를 분리하는 옵션 추가 검토. 현재 코드는 호출자 대부분이 `result.get("content")`, `result.get("tactical_doc")` 등 특정 키만 사용하므로 실제 피해가 제한적이지만, 향후 구조화된 응답 스키마 사용 확대 시 문제가 될 수 있다.

---

### TF-BA-06: `_extract_json_robust` regex 폴백의 greedy 매칭 위험 — IMPORTANT

- **Location**: `base_agent.py:L1709-L1731`
- **Description**: JSON 파싱이 완전히 실패할 때 정규식으로 특정 필드를 강제 추출한다. `"content"` 필드 추출 시 `re.search(r'"content"\s*:\s*"(.*?)"', text, re.DOTALL)` 패턴을 사용한다. `.*?`는 non-greedy이지만 `re.DOTALL`과 결합하면 첫 번째 `"`까지만 매칭하므로, 값에 이스케이프된 따옴표(`\"`)가 포함되면 잘못된 위치에서 매칭이 끝난다.
- **Evidence**:
  ```python
  # L1714-L1716: content 필드 강제 추출
  content_match = re.search(r'"content"\s*:\s*"(.*?)"', text, re.DOTALL)
  if content_match:
      return {"content": content_match.group(1), "repaired": True}
  ```
  만약 원본이 `"content": "대화: \"안녕하세요\" 라고 말했다"` 라면, 매칭은 `대화: \`에서 끝난다.
- **Impact**: 원고 텍스트에 대화문이 포함되면(한국어 소설에서 매우 빈번) content가 잘리거나 왜곡된다. 다만 이 경로는 `json.loads` + `ast.literal_eval` + `_parse_and_repair_hard` 모두 실패한 최후의 폴백이므로 발생 빈도는 낮다.
- **Suggested fix direction**: 이스케이프된 따옴표를 허용하는 패턴으로 변경: `r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"'`

---

### TF-BA-07: `_ask_with_cached_context` 폴백 시 이중 비용 발생 — IMPORTANT

- **Location**: `base_agent.py:L2064-L2081`
- **Description**: `_ask_with_cached_context`에서 캐시 경로 실패 시 `self.ask()`로 폴백한다. 이 때:
  1. 캐시 경로에서 이미 `_generate_content`가 호출되어 API 비용이 발생할 수 있다 (에러 전에 일부 응답이 전송되었을 수 있음)
  2. `ask()`가 다시 전체 프롬프트로 호출되면서 새 API 비용이 발생한다
  3. DB 로깅은 캐시 경로 실패(L2065-L2076)와 `ask()` 성공 모두 기록되므로 이중 기록된다
  4. TF-BA-02에서 지적한 대로 MetricsCollector에는 캐시 경로 비용이 기록되지 않아 불일치가 심화된다
- **Evidence**:
  ```python
  # L2064-L2081: 캐시 실패 → ask() 재귀
  except Exception as e:
      try:
          self._log_llm_call_to_db(  # DB에 실패 기록 (비용은 이미 발생)
              model=self.primary_model, ...
              success=False, error=e,
          )
      except Exception:
          pass
      # ask()가 다시 전체 흐름을 실행 — 비용 이중 발생
      return self.ask(fallback_prompt, ...)
  ```
- **Impact**: 캐시 만료 시(TF-BA-01과 연관) 비용이 1.x~2배로 증가. 특히 `full_prompt_fallback`이 비어있으면 짧은 `prompt`만으로 `ask()`가 호출되어 결과 품질도 저하될 수 있다.
- **Suggested fix direction**: 실패 시 서버측 캐시 유효성을 먼저 확인하거나, 로컬 캐시를 무효화한 후 `_get_or_create_context_cache`를 다시 호출하여 새 캐시를 만드는 경로 추가.

---

### TF-BA-08: 에러 분류에서 "429" 키워드가 QUOTA_EXCEEDED와 TIMEOUT 사이에서 오분류 가능 — IMPORTANT

- **Location**: `base_agent.py:L1498-L1511` (`_classify_error`) + `L1091-L1099` (`_handle_api_error` 내부 분류)
- **Description**: `_classify_error`와 `_handle_api_error`가 서로 다른 분류 체계를 사용한다:
  - `_classify_error`(L1504): "429" → `QUOTA_EXCEEDED` (rate와 quota 구분 없음)
  - `_handle_api_error`(L1091-L1099): "429" + "rate"/"limit" → rate limit, "resource_exhausted" → quota, 나머지 429 → ambiguous (rate limit으로 간주)
  - 두 분류의 불일치: `_classify_error`는 모든 429를 QUOTA_EXCEEDED로, `_handle_api_error`는 세분화하여 다른 재시도 전략을 적용
- **Evidence**:
  ```python
  # L1504: _classify_error — 모든 429를 QUOTA로 분류
  elif "quota" in error_str or "rate" in error_str or "429" in error_str:
      return AgentErrorType.QUOTA_EXCEEDED

  # L1095-L1099: _handle_api_error — 세분화
  is_rate_limit = "429" in error_str and ("rate" in error_str or "limit" in error_str)
  is_quota_exhausted = "resource_exhausted" in error_str or ("quota" in error_str and "429" not in error_str)
  is_ambiguous_429 = "429" in error_str and not is_rate_limit and not is_quota_exhausted
  ```
- **Impact**: `_classify_error`는 외부 except 핸들러(L837)에서 호출되어 로깅과 `_attempt_backup_recovery`의 `error_type` 파라미터에만 사용된다. 실제 재시도 전략에는 `_handle_api_error`의 분류가 사용되므로 **기능적 영향은 낮다**. 단, 로그/DB 기록의 `error_type`이 실제 재시도 전략과 불일치하여 디버깅을 어렵게 할 수 있다.
- **Suggested fix direction**: `_classify_error`를 `_handle_api_error`와 동일한 세분화 로직으로 통합하거나, `_handle_api_error`의 분류 결과를 반환 dict에 포함하여 외부 핸들러가 재사용.

---

### TF-BA-09: `_get_or_create_context_cache` 의 TOCTOU 잔여 위험 — IMPORTANT

- **Location**: `base_agent.py:L1896-L1906` (read-check) + `L1907-L1957` (create) + `L1929-L1941` (write)
- **Description**: 캐시 유효성 확인(Lock 내)과 새 캐시 생성(Lock 외, Gemini API 호출)과 캐시 저장(Lock 내) 사이에 gap이 존재한다. 두 스레드가 동시에 동일 `cache_key`에 대해:
  1. 스레드 A: Lock 잡고 확인 → 캐시 없음 → Lock 해제
  2. 스레드 B: Lock 잡고 확인 → 캐시 없음 → Lock 해제
  3. 스레드 A: API 호출 → 캐시 생성 → Lock 잡고 저장
  4. 스레드 B: API 호출 → 캐시 생성 → Lock 잡고 덮어쓰기
  결과: 동일 콘텐츠에 대해 Gemini API에 캐시가 2개 생성된다.
- **Evidence**:
  ```python
  # L1896-L1905: Lock 내에서 확인
  with self._cache_lock:
      cached_info = self._context_caches.get(cache_key)
      if cached_info:
          if current_time - cached_info["created_at"] < ttl_seconds:
              return {...}
          else:
              self._context_caches.pop(cache_key, None)
  # Lock 해제 — 여기서 다른 스레드가 동일 작업 수행 가능

  # L1919-L1926: Lock 없이 API 호출
  cache = self.client.caches.create(...)

  # L1929-L1941: Lock 잡고 저장
  with self._cache_lock:
      self._context_caches[cache_key] = {...}
  ```
- **Impact**: Gemini Context Caching API 비용이 2배 발생. 다만 현재 코드베이스에서 동일 에이전트의 동일 캐시 키에 대한 동시 호출은 드문 패턴(에피소드 처리가 순차적)이므로 실제 발생 빈도는 낮다.
- **Suggested fix direction**: Lock 범위를 확장하여 API 호출까지 포함하거나(단, API 호출 시간 동안 다른 캐시 접근이 블록됨), "생성 중" sentinel 값을 사용하여 중복 생성 방지.

---

### TF-BA-10: 비용 추적에서 폴백 모델 전환 시 `metric_id` 모델 불일치 — IMPORTANT

- **Location**: `base_agent.py:L998-L1005` (start_call) + `L773-L784` (end_call)
- **Description**: `start_call`(L1002)은 초기 `current_model`로 호출되지만, 내부 폴백(`_handle_api_error`의 `fallback_response` 경로)으로 모델이 변경된 후에도 같은 `metric_id`로 `end_call`이 호출된다. `end_call`은 원래 모델의 `AgentMetric`에 새 모델의 토큰/비용을 기록한다.
- **Evidence**:
  ```python
  # L1002: 초기 모델로 start_call
  metric_id = collector.start_call(self.agent_name, current_model)  # e.g., "gemini-2.5-pro"

  # ... _handle_api_error에서 current_model이 "gemini-2.5-flash"로 변경 ...

  # L782: 변경된 모델의 응답이지만 원래 metric_id로 end_call
  collector.end_call(metric_id, success=True, **metric_usage)
  ```
  `MetricsCollector.end_call` (L253-L254):
  ```python
  model = metric.model  # 원래 start_call 시 등록된 모델
  self._model_tokens[model]["input"] += input_tokens  # 잘못된 모델에 집계
  ```
- **Impact**: `_model_tokens` 집계에서 pro 모델에 flash 모델의 토큰이 기록되어 모델별 비용 리포트가 부정확해진다. 세션 전체 합계에는 영향 없으나 모델별 분석이 왜곡된다.
- **Suggested fix direction**: 폴백 시 원래 `metric_id`를 `end_call(success=False)`로 닫고, 새 모델로 `start_call`/`end_call` 페어를 생성.

---

### TF-BA-11: `_ask_with_cached_context`의 `_generate_content` 반환값이 `.raw` — INSIGHT

- **Location**: `base_agent.py:L2021-L2025` + `L388-L391`
- **Description**: `_generate_content`는 `_generate_llm_response().raw`를 반환한다(L391). 이것은 Gemini SDK의 네이티브 응답 객체이다. `_ask_with_cached_context`는 이 raw 객체에서 `.text`, `.candidates`, `.candidates[0].content.parts` 등에 직접 접근한다. 현재는 컨텍스트 캐싱이 Gemini 전용이므로 문제없지만, 다른 프로바이더(Anthropic, OpenAI)가 캐싱을 지원하게 되면 이 코드가 깨진다.
- **Evidence**:
  ```python
  # L2021-2025: raw Gemini 객체에 직접 접근
  response = self._generate_content(model=..., contents=..., config=config)
  # response는 Gemini raw 객체
  # L2031: response.candidates 접근 (Gemini 전용)
  if response.candidates and response.candidates[0].content:
  ```
- **Impact**: 현재 영향 없음. 향후 멀티프로바이더 캐싱 확장 시 리팩터링 필요.
- **Suggested fix direction**: `_generate_llm_response`를 사용하여 `LLMResponse` 객체를 받고, thinking 추출도 provider-neutral하게 변경.

---

### TF-BA-12: `_extract_json_robust`의 self-healing 괄호 닫기가 JSON 구조를 왜곡 가능 — INSIGHT

- **Location**: `base_agent.py:L1680-L1687`
- **Description**: 파싱 전에 열린 중괄호와 닫힌 중괄호의 수를 세어 부족한 만큼 `}`를 추가한다. 그러나 이 카운트는 문자열 값 내부의 중괄호도 포함한다. 예: `{"content": "함수 f(x) = {x+1}"}` → 열림 3, 닫힘 2로 계산 → `}`가 1개 추가되어 `{"content": "함수 f(x) = {x+1}"}}`가 된다.
- **Evidence**:
  ```python
  # L1681-1684
  open_braces = text.count("{")
  close_braces = text.count("}")
  if open_braces > close_braces:
      text += "}" * (open_braces - close_braces)
  ```
- **Impact**: 문자열 값에 중괄호가 포함된 경우(수학 표현, 코드 블록 등) 잘못된 수의 닫는 괄호가 추가되어 JSON 파싱이 실패하거나 왜곡된 결과가 나올 수 있다. 무협 소설 도메인에서는 드물지만, 투자 장르(재무 데이터)에서 발생 가능.
- **Suggested fix direction**: 문자열 리터럴 내부를 제외한 구조적 중괄호만 카운트하는 로직으로 개선. 또는 이 pre-processing을 제거하고 파싱 실패 시에만 repair를 시도.

---

### TF-BA-13: `director_continuity.py`의 캐시 재사용 경로에서 `cache_name` 누락 — INSIGHT

- **Location**: `director_continuity.py:L682-L685`
- **Description**: Blueprint 캐시 재사용 경로에서 `cache_result = {"cached": True}`를 하드코딩한다. 이 dict에는 `cache_name` 키가 없다. 이후 `cache_result.get("cache_name")`을 호출하면 `None`이 반환된다. 다만 이 특정 메서드(`check_blueprint_continuity_with_cache`)는 실제로 `cache_result.get("cache_name")`을 호출하지 않고 `cache_result.get("cached", False)`만 사용하므로 현재는 무해하다.
- **Evidence**:
  ```python
  # director_continuity.py L684
  cache_result = {"cached": True}  # cache_name 키 없음
  # L738: 사용처
  "cache_used": cache_result.get("cached", False),  # 이것만 사용 → 무해
  ```
  그러나 유사한 패턴이 manuscript 경로(L799-L800)에는 `cache_name`이 포함되어 있어 불일치:
  ```python
  # L799-L800
  cache_result = {"cached": True, "cache_name": getattr(self, "_manuscript_cache_name", None)}
  ```
- **Impact**: 현재 무해. Blueprint 경로가 manuscript 경로와 동일한 패턴으로 `cache_name`을 사용하도록 확장되면 버그 발생.
- **Suggested fix direction**: Blueprint 재사용 경로에도 `cache_name` 포함: `cache_result = {"cached": True, "cache_name": getattr(self, "_cached_blueprint_cache_name", None)}`.

---

### TF-BA-14: `_parse_and_repair_hard`의 regex 2-pass 패턴이 중첩 객체를 무시 — INSIGHT

- **Location**: `base_agent.py:L1809-L1828`
- **Description**: `_parse_and_repair_hard`의 regex fallback은 `"(\w+)"\s*:\s*"(.*?)"` 패턴으로 문자열 값을, `"(\w+)"\s*:\s*([-+]?\d+...)`로 숫자/불리언 값을 추출한다. 배열 값(`[...]`)과 중첩 객체(`{...}`) 값은 모두 무시된다.
- **Evidence**:
  ```python
  # L1809-L1811: 문자열 값만 추출
  kv_pattern = r'"(\w+)"\s*:\s*"(.*?)"(?="|\s*\}|\s*,)'
  # 배열/객체 값 패턴 없음
  ```
- **Impact**: `beat_sequence`, `state_updates` 등 배열/객체 타입 필드가 완전히 소실된다. 이 경로 자체가 최후의 폴백이므로 빈도는 매우 낮으나, 발생 시 핵심 데이터가 누락된다.
- **Suggested fix direction**: 배열/객체 값을 위한 3번째 pass 추가. 또는 이 단계에서는 raw text를 반환하고 호출자가 처리하도록 위임.

---

### TF-BA-15: ask() 메인 루프에서 `attempt`가 증가하지 않는 에러 경로 — INSIGHT

- **Location**: `base_agent.py:L651-L758`
- **Description**: 메인 while 루프에서 `attempt`는 MAX_TOKENS 이어쓰기 경로에서만 증가한다(L755). 에러 → `continue` 경로(네트워크 재시도, rate limit 재시도)에서는 `attempt`가 증가하지 않는다. 따라서 네트워크 재시도 22회 + rate limit 재시도 3회가 모두 `attempt = 0`인 상태에서 반복된다.
- **Evidence**:
  ```python
  # L651-L653: 메인 루프
  attempt = 0
  while attempt < MAX_CONTINUATIONS:  # MAX_CONTINUATIONS = 5
      try:
          ...
      except Exception as api_error:
          _err = self._handle_api_error(...)
          if _err["action"] == "continue":
              continue  # attempt 증가 없이 루프 재시작
          ...
      # 성공 시 이어쓰기 판정
      if _resp["action"] == "continue":
          attempt += 1  # 이어쓰기만 attempt 증가
          continue
  ```
- **Impact**: 이것은 **의도된 설계**이다 — `attempt`는 "이어쓰기(continuation) 횟수"를 의미하며, API 재시도 횟수가 아니다. 네트워크/rate limit 재시도는 자체 카운터(`network_retry_count`, `rate_limit_retry_count`)로 제한된다. 그러나 이로 인해 이론적으로 총 API 호출 횟수가 `5(이어쓰기) + 22(네트워크) + 3(rate limit) + N(폴백)` = 30+회까지 가능하여 비용이 누적될 수 있다.
- **Suggested fix direction**: 전체 API 호출 횟수에 대한 글로벌 상한(예: 50회)을 추가하여 비용 폭증 방지. 현재 로직이 의도적이므로 severity는 INSIGHT로 분류.

---

## 4. Summary Matrix

| ID | Title | Severity | Location | 현재 영향 | 발생 확률 |
|---------|-------------------------------------|----------|-------------------|------------|-----------|
| TF-BA-01 | 로컬/서버 TTL drift → 만료 캐시 사용 | CRITICAL | L1893-L1933 | API 에러 + 이중 비용 | 중 (TTL 경계) |
| TF-BA-02 | cached path MetricsCollector 누락 | CRITICAL | L1959-L2081 | 비용 집계 불완전 | 확정 (구조적) |
| TF-BA-03 | 폴백/백업 config http_options 누락 | IMPORTANT | L1177, L1338 | 타임아웃 불일치 | 중 |
| TF-BA-04 | _classify_error/_is_network_error 충돌 | IMPORTANT | L1498, L1543 | 타임아웃→22회 네트워크 재시도 | 중 |
| TF-BA-05 | JSON 평탄화 데이터 구조 변환 | IMPORTANT | L1742-L1786 | 중첩 구조 소실 | 낮 (현재 도메인) |
| TF-BA-06 | regex 폴백 greedy 매칭 | IMPORTANT | L1709-L1731 | content 잘림 | 낮 (최후 폴백) |
| TF-BA-07 | 캐시 폴백 시 이중 비용 | IMPORTANT | L2064-L2081 | 비용 + DB 이중 기록 | 중 (TF-BA-01 연관) |
| TF-BA-08 | _classify_error 429 분류 불일치 | IMPORTANT | L1498, L1091 | 로그 불일치 | 낮 (기능 무영향) |
| TF-BA-09 | 캐시 생성 TOCTOU | IMPORTANT | L1896-L1941 | API 비용 2배 | 낮 (순차 처리) |
| TF-BA-10 | 폴백 시 metric 모델 불일치 | IMPORTANT | L998, L773 | 모델별 집계 왜곡 | 중 |
| TF-BA-11 | cached path의 raw 객체 직접 접근 | INSIGHT | L2021-L2025 | 없음 (Gemini 전용) | 없음 |
| TF-BA-12 | self-healing 괄호 닫기 왜곡 | INSIGHT | L1680-L1687 | 문자열 내 중괄호 | 낮 |
| TF-BA-13 | director_continuity 캐시 재사용 cache_name 누락 | INSIGHT | DC:L684 | 없음 (미사용) | 없음 |
| TF-BA-14 | repair regex 중첩 객체 무시 | INSIGHT | L1809-L1828 | 핵심 데이터 누락 | 매우 낮 |
| TF-BA-15 | ask() attempt 카운터 의미 | INSIGHT | L651-L758 | 의도적 설계 | N/A |

---

## 5. 핵심 코드 참조 (Appendix)

### A. 캐시 TTL 체크 (TF-BA-01 관련)
```python
# base_agent.py L1893-L1905
current_time = time.time()  # API 호출 전에 캡처

with self._cache_lock:
    cached_info = self._context_caches.get(cache_key)
    if cached_info:
        if current_time - cached_info["created_at"] < ttl_seconds:
            # 로컬 기준 유효 — 서버에서는 이미 만료됐을 수 있음
            return {"cache_name": cached_info.get("name"), "cached": True, ...}
        else:
            self._context_caches.pop(cache_key, None)
```

### B. MetricsCollector 누락 경로 (TF-BA-02 관련)
```python
# base_agent.py L1959-L2081 (_ask_with_cached_context)
# 메서드 전체에서 start_call/end_call 호출 없음
# 반면 ask() 메서드:
#   L1002: metric_id = collector.start_call(self.agent_name, current_model)
#   L782:  collector.end_call(metric_id, success=True, **metric_usage)
#   L862:  collector.end_call(metric_id, success=False, ...)
```

### C. http_options 불일치 (TF-BA-03 관련)
```python
# 메인 config (L973) — 포함
"http_options": types.HttpOptions(timeout=max(10_000, int(self.API_TIMEOUT) * 1000))
# 캐시 config (L2004) — 포함
"http_options": types.HttpOptions(timeout=max(10_000, int(self.API_TIMEOUT) * 1000))
# 폴백 config (L1177-L1182) — 누락!
# 백업 config (L1338-L1342) — 누락!
```

### D. 에러 분류 충돌 (TF-BA-04 관련)
```python
# _classify_error (L1502-L1503): timeout → TIMEOUT
if "timeout" in error_str or "timed out" in error_str or "deadline" in error_str:
    return AgentErrorType.TIMEOUT

# _is_network_error (L1546-L1560): timeout → True (네트워크 에러)
network_keywords = ["timeout", "deadline", "connection", ...]

# _handle_api_error (L1053): _is_network_error 먼저 체크
if self._is_network_error(api_error) and network_retry_count < self.MAX_NETWORK_RETRIES:
    # 타임아웃도 여기 진입 → 최대 22회 재시도
```

### E. TTL 사용 현황 (실측)
| 호출자 | cache_type | ttl_seconds |
|--------|-----------|------------|
| ArcEnsemble | blueprint | 600 |
| BlueprintEnsemble | blueprint | 600 |
| ChiefWriter | manuscript | 600 |
| DirectorEnsemble | blueprint | 600 |
| DirectorContinuity (blueprint) | blueprint | 1800 |
| DirectorContinuity (manuscript) | manuscript | 1800 |
| DirectorCaching | manuscript | 3600 |
| Analyst | varies | 600 |
| 기본값 (base_agent) | any | 1800 |
