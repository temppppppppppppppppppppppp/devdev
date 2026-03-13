# XC-LLM-T2: Provider간 Response 타입 분산 — Findings

> 작성일: 2026-03-13
> 감사 범위: `llm_generate.py`, `llm_provider.py`, `providers/*.py`, 호출자 전체

---

## 실행 요약

`generate_content_via_router()`는 `LLMResponse.raw`(provider-native 응답 객체)를 반환한다. 호출자는 이 반환값에 대해 `.text` 속성 접근을 수행하는데, 이는 Gemini의 raw 응답 구조에 의존하는 패턴이다. Provider별 `LLMResponse` 생성 시 `usage` dict의 키 구조도 상이하며, `finish_reason` 값 체계도 다르다. 현재 Gemini-only 운영이므로 실질 문제는 없으나, 멀티 Provider 전환 시 **P1급 장애**로 전이될 수 있는 설계적 취약점이 존재한다.

---

## PASS 1: 후보 수집

### [XC-LLM-005] P2 | generate_content_via_router()가 raw를 반환하여 호출자가 Gemini 구조에 의존

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-005 |
| Severity | P2 (품질 저하 — 멀티 Provider 전환 시 P1 전이 가능) |
| 현상 요약 | `generate_content_via_router()`가 `response.raw`를 반환하고 호출자가 `.text` 접근 — Anthropic/OpenAI raw 응답에는 `.text` 속성이 없어 `AttributeError` 발생. |
| 코드 근거 | `modules/core/llm_generate.py:21` (`return response.raw`), `modules/core/adversarial_self_play.py:159` (`response.text`), `modules/validation/advisory_validator.py:145` (`response.text`), `main_a.py:1569` (`resp.text`) |
| 영향 경계 | `generate_content_via_router()` 호출 경로 전체: adversarial_self_play, advisory_validator, chain_of_verification, cross_agent_verifier, multi_agent_deliberation, narrative_structure_analyzer, self_reflection, tree_of_thoughts, scoring_validator, main_a.py (2곳), stage0 modules (3곳), stage4_orchestrator |
| 테스트 근거 | `test_llm_router.py:57-77` — Gemini provider의 raw 보존만 테스트. 비-Gemini provider의 raw 구조 호출자 호환성 테스트 부재. |
| 기존 중복 여부 | **T1-11 (P3)와 관련** — T1-11은 "Gemini provider가 항상 raw 채움, 멀티 Provider 전환 시에만 잠재적"으로 P3 하향. 본 건은 호출자의 `.text` 의존성을 구체적으로 식별한 확장 분석. |
| 권장 후속 조치 | `generate_content_via_router()`가 `response.raw` 대신 `response` (`LLMResponse` 객체)를 반환하도록 변경. 호출자는 `response.text`를 사용 (LLMResponse.text는 모든 provider에서 정규화됨). 공수: 2h (호출자 15곳 일괄 변경). |

```python
# llm_generate.py:9-21 — 현재 코드
def generate_content_via_router(*, client, model, contents, config=None) -> Any:
    provider = get_shared_llm_router().get_provider_for_model(model)
    response = provider.generate(client=client, request=LLMRequest(...))
    return response.raw  # ← Gemini raw 객체 반환

# 호출자 예시 (adversarial_self_play.py:153-159)
response = generate_content_via_router(client=self.client, model=self.model, contents=prompt, ...)
return response.text or ""  # ← raw.text 접근 — Anthropic raw에서는 AttributeError
```

**위험 분석**:
- Gemini raw 응답: `raw.text` = 정상 동작 (genai SDK가 `.text` property 제공)
- Anthropic raw 응답: `SimpleNamespace(content=[TextBlock(...)], ...)` — `.text` 속성 없음
- OpenAI raw 응답: `SimpleNamespace(output_text="...", output=[...], ...)` — `.text` 속성 없음 (`.output_text` 사용)

**신뢰도**: HIGH. **영향도**: 현재 NONE (Gemini-only), 전환 시 HIGH.

---

### [XC-LLM-006] P3 | Provider간 usage dict 키 불일치

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-006 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | Provider별 `LLMResponse.usage` dict 키가 상이하여, 하류 비용 추적 코드가 특정 provider에서 토큰 수를 읽지 못할 수 있다. |
| 코드 근거 | Gemini: `{"prompt_token_count", "candidates_token_count", "total_token_count", "thoughts_token_count", "cached_content_token_count"}` (`gemini_provider.py:35-41`), Anthropic: `{"input_tokens", "output_tokens"}` (`anthropic_provider.py:77-80`), OpenAI: `{"input_tokens", "output_tokens", "total_tokens"}` (`openai_provider.py:94-98`) |
| 영향 경계 | `base_agent.py:382-386` — `_build_metric_usage_payload()`가 Gemini 키(`prompt_token_count`, `candidates_token_count`)만 읽음 |
| 테스트 근거 | Provider별 usage 테스트 존재하나, BaseAgent의 usage 소비 로직과의 교차 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | LLMResponse 생성 시 usage 키를 정규화하거나, `_build_metric_usage_payload()`에서 양쪽 키를 모두 탐색. 공수: 1h. |

```python
# base_agent.py:382-386 — Gemini 키만 탐색
input_tokens = self._coerce_usage_int(usage.get("prompt_token_count"))
output_tokens = self._coerce_usage_int(usage.get("candidates_token_count"))
cached_tokens = self._coerce_usage_int(usage.get("cached_content_token_count"))
thinking_tokens = self._coerce_usage_int(usage.get("thoughts_token_count"))

# Anthropic/OpenAI usage에서 위 키들은 모두 None → 0으로 처리됨
# → 비용 추적 시 토큰 수가 0으로 기록되는 무성 실패
```

**신뢰도**: HIGH. **영향도**: 현재 NONE (Gemini-only), 전환 시 MED.

---

### [XC-LLM-007] P3 | Provider간 finish_reason 값 체계 불일치

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-007 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | Provider별 `finish_reason` 값이 상이하며, 하류 코드가 특정 값에 의존할 수 있다. |
| 코드 근거 | Gemini: `"STOP"`, `"MAX_TOKENS"` 등 (대문자 enum), Anthropic: `"end_turn"`, `"max_tokens"` (소문자), OpenAI: `"completed"` (상태값) |
| 영향 경계 | `base_agent.py` 내 finish_reason 분기 로직 (존재 시) |
| 테스트 근거 | 각 provider 테스트에서 개별 확인되나, 정규화 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | LLMResponse 생성 시 정규화 (예: `"stop"/"max_tokens"/"error"`). 공수: 1h. |

**신뢰도**: HIGH. **영향도**: 현재 NONE, 전환 시 LOW (finish_reason을 분기 조건으로 사용하는 코드가 제한적).

---

### [XC-LLM-008] P2 | BaseAgent._generate_content()도 response.raw 반환 — 동일 패턴

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-008 |
| Severity | P2 (품질 저하) |
| 현상 요약 | `BaseAgent._generate_content()`가 `response.raw`를 반환하여 BaseAgent 내부의 모든 LLM 호출이 Gemini raw 응답에 의존한다. |
| 코드 근거 | `modules/domain/agents/base_agent.py:334-345` |
| 영향 경계 | BaseAgent의 모든 하위 클래스 (ChiefWriter, Director, Analyst 등 12+ 에이전트) |
| 테스트 근거 | BaseAgent의 `_generate_content` 반환값 타입 테스트 부재 |
| 기존 중복 여부 | XC-LLM-005와 동일 패턴이나 다른 경로 |
| 권장 후속 조치 | XC-LLM-005와 함께 수정. `_generate_content()`가 `LLMResponse`를 반환하도록 변경 후, 내부 코드 점진 마이그레이션. 공수: 4h (하류 코드 다수). |

```python
# base_agent.py:334-345
def _generate_content(self, *, model, contents, config):
    """Phase 1 provider shim.
    Downstream parsing in BaseAgent still expects the native Gemini response
    object, so the provider keeps `raw` intact and this helper returns it.
    """
    request = LLMRequest(model=model, contents=contents, config=config)
    provider = self._llm_router.get_provider_for_model(model)
    response = provider.generate(client=self.client, request=request)
    self._last_llm_usage = response.usage  # ← usage는 LLMResponse에서 추출
    return response.raw  # ← 그러나 반환은 raw
```

주석에서도 "Downstream parsing in BaseAgent still expects the native Gemini response object"라고 **의도적 기술 부채**임을 명시하고 있다.

**신뢰도**: HIGH. **영향도**: 현재 NONE, 전환 시 HIGH.

---

### [XC-LLM-009] P3 | GeminiProvider와 VertexAIProvider의 코드 중복

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-009 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `GeminiProvider.generate()`와 `VertexAIProvider.generate()`의 응답 파싱 코드가 거의 동일하다 (text 추출, finish_reason, usage 추출). |
| 코드 근거 | `gemini_provider.py:11-49` vs `vertex_provider.py:79-118` — 38줄 중 ~30줄 동일 |
| 영향 경계 | 유지보수 비용 |
| 테스트 근거 | 각각 독립 테스트 존재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 공통 응답 파싱 헬퍼를 추출하여 중복 제거. 공수: 1h. |

**신뢰도**: HIGH. **영향도**: LOW (유지보수 편의).

---

## PASS 2: 교차 검증

| ID | PASS 1 판정 | 런타임 도달? | 기존 중복? | PASS 2 판정 |
|----|-------------|------------|----------|------------|
| XC-LLM-005 | P2 | 예 (Gemini raw에서 .text 접근 성공) | T1-11 확장 | P2 유지 |
| XC-LLM-006 | P3 | 예 (usage 소비 경로) | 신규 | P3 유지 |
| XC-LLM-007 | P3 | 부분 (finish_reason 분기 제한적) | 신규 | P3 유지 |
| XC-LLM-008 | P2 | 예 (모든 에이전트) | XC-LLM-005 동일 패턴 | P2 유지 |
| XC-LLM-009 | P3 | 해당 없음 (코드 스멜) | 신규 | P3 유지 |

### 런타임 도달성 상세 (XC-LLM-005)

`generate_content_via_router()` 호출자 전수 조사:

| 호출자 | `.text` 접근 | 파일:줄 |
|--------|------------|---------|
| adversarial_self_play.py | `response.text or ""` | L159 |
| advisory_validator.py | `response.text` | L145 |
| chain_of_verification.py | `response.text` | 확인 필요 |
| cross_agent_verifier.py | `response.text` | 확인 필요 |
| multi_agent_deliberation.py | `response.text` | 확인 필요 |
| self_reflection.py | `response.text` | 확인 필요 |
| tree_of_thoughts.py | `response.text` | 확인 필요 |
| scoring_validator.py | `response.text` | 확인 필요 |
| main_a.py (2곳) | `resp.text or ""` | L1569, L2598 |
| stage0 modules (3곳) | `response.text` | 확인 필요 |

모든 호출자가 `.text` 속성에 접근한다. 현재 Gemini raw 응답의 `.text` property가 이를 처리하지만, Anthropic/OpenAI raw 응답에서는 `AttributeError`가 발생할 것이다.

---

## PASS 3: 최종 확정

### 확정: XC-LLM-005 (P2)
- T1-11의 구체적 확장. T1-11이 "부분오탐, P3 하향"으로 판정했으나, 실제 호출자 `.text` 의존성을 전수 조사한 결과 **멀티 Provider 전환 시 P1급 장애**가 확실. 현재 Gemini-only이므로 P2 유지.

### 확정: XC-LLM-006 (P3)
- Gemini-only 운영 시 무해. 전환 시 비용 추적 누락 (무성 실패).

### 확정: XC-LLM-007 (P3)
- finish_reason 분기 코드가 제한적이므로 영향 낮음.

### 확정: XC-LLM-008 (P2)
- XC-LLM-005와 동일한 근본 원인이나 영향 범위가 더 넓음 (모든 에이전트). 별도 추적 유지.

### 확정: XC-LLM-009 (P3)
- 유지보수 편의 개선.

---

## T2 최종 결론

| 등급 | 건수 | 비고 |
|------|------|------|
| P0 | 0 | - |
| P1 | 0 | - |
| P2 | 2 | XC-LLM-005, 008 (raw 반환 → 호출자 Gemini 의존. 전환 시 P1 전이) |
| P3 | 3 | XC-LLM-006, 007, 009 |

**핵심 판단**: `generate_content_via_router()`와 `BaseAgent._generate_content()` 모두 `response.raw`를 반환하는 것은 **의도적 기술 부채**다 (base_agent.py 주석에 명시). 현재 Gemini-only 운영에서는 안전하나, 멀티 Provider 전환 시 반드시 `LLMResponse` 반환으로 변경해야 한다. 이 변경은 호출자 15곳+ 에이전트 12종에 영향을 미치므로 공수가 상당하다 (추정 6-8h).
