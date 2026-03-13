# XC-LLM-T1: Shared Router Singleton 스레드 안전 — Findings

> 작성일: 2026-03-13
> 감사 범위: `llm_router.py`, `base_agent.py`, `stage4_interview_round.py`

---

## 실행 요약

`LLMProviderRouter`는 `_SHARED_ROUTER` 모듈-레벨 전역 변수를 통해 공유 싱글톤으로 사용된다. `get_shared_llm_router()` 함수에 Lock이 없으며, `get_provider_for_model()` 내부의 lazy provider 빌드도 동기화 없이 `self._providers` dict에 쓰기를 수행한다. Stage4 Advisory chain은 `ThreadPoolExecutor(max_workers=8)`로 8개 스레드를 동시 실행하며, 각 스레드가 `director.ask()` → `BaseAgent._generate_content()` → `self._llm_router.get_provider_for_model()` 경로를 통해 router에 접근한다.

---

## PASS 1: 후보 수집

### [XC-LLM-001] P3 | _SHARED_ROUTER 싱글톤 초기화 경합 (Lock 부재)

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-001 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `get_shared_llm_router()`가 Lock 없이 check-then-write로 싱글톤을 생성한다. |
| 코드 근거 | `modules/core/llm_router.py:131-138` |
| 영향 경계 | 전체 파이프라인 (모든 LLM 호출) |
| 테스트 근거 | `test_llm_router.py:47-48` — `test_shared_router_is_singleton()` 존재하나 단일 스레드 테스트 |
| 기존 중복 여부 | **T1-22 (P3)와 동일 — 중복 확인됨** |
| 권장 후속 조치 | `threading.Lock` 추가 (0.5h). 단, 실질 영향 미미: CPython GIL이 dict 할당을 원자적으로 보호하며, 최악의 경우 LLMProviderRouter가 2회 생성되더라도 무상태(stateless) 객체이므로 기능적 문제 없음. |

```python
# llm_router.py:131-138
_SHARED_ROUTER: LLMProviderRouter | None = None

def get_shared_llm_router(*, force_reload: bool = False) -> LLMProviderRouter:
    global _SHARED_ROUTER
    if force_reload or _SHARED_ROUTER is None:  # ← check
        _SHARED_ROUTER = LLMProviderRouter()     # ← write (Lock 없음)
    return _SHARED_ROUTER
```

**신뢰도**: HIGH (코드 사실). **영향도**: LOW (GIL + 무상태).

---

### [XC-LLM-002] P3 | get_provider_for_model() 내 _providers dict lazy write 비동기화

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-002 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `get_provider_for_model()`에서 미등록 provider를 lazy-build 후 `self._providers[name] = provider`로 저장하는데 Lock이 없다. |
| 코드 근거 | `modules/core/llm_router.py:118-122` |
| 영향 경계 | Provider 전환 시 (현재 Gemini-only 운영이므로 사실상 미도달) |
| 테스트 근거 | `test_llm_router.py` — 단일 스레드 등록 테스트만 존재 |
| 기존 중복 여부 | T1-19와 부분 관련 (T1-19는 disabled provider가 build되는 논리적 허점, 본 건은 동시성) |
| 권장 후속 조치 | Lock 추가 (0.5h). 현재 운영 환경에서 Gemini만 enabled이고, 생성자에서 이미 Gemini provider가 등록되므로 lazy-build 경로 도달 불가. |

```python
# llm_router.py:118-122
provider = self._providers.get(provider_name)
if provider is None:
    if provider_config:
        provider = _build_provider(provider_name, provider_config)
        self._providers[provider_name] = provider  # ← Lock 없는 dict write
```

**신뢰도**: HIGH (코드 사실). **영향도**: 사실상 NONE (Gemini-only 운영 시 미도달).

---

### [XC-LLM-003] P3 | Advisory chain 8스레드 동시 router 접근

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-003 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | Stage4 advisory chain이 `ThreadPoolExecutor(max_workers=8)`로 병렬 실행 시, 8개 스레드가 동일한 `_llm_router` 인스턴스의 `get_provider_for_model()`을 동시 호출한다. |
| 코드 근거 | `modules/core/stage4_interview_round.py:3807-3812` (ThreadPoolExecutor), `modules/core/stage4_interview_round.py:92-100` (`_truth_gate_llm_ask` → `director.ask()`), `modules/domain/agents/base_agent.py:334-345` (`_generate_content()` → `self._llm_router.get_provider_for_model()`) |
| 영향 경계 | Stage4 에피소드 생성 |
| 테스트 근거 | 멀티스레드 router 접근 테스트 부재 |
| 기존 중복 여부 | 신규 (T1-22는 싱글톤 초기화만 다룸, 동시 접근 자체는 미다룸) |
| 권장 후속 조치 | 현재 안전: (1) Gemini provider가 이미 `__init__`에서 등록되어 lazy-build 미발생, (2) `get_provider_for_model()`은 dict read-only 경로만 타므로 GIL 보호 하에 안전, (3) 각 스레드가 공유하는 건 router 객체 자체뿐이고, 실제 API 호출은 각자의 client/request로 수행. 형식적 Lock 추가만 권장 (0.5h). |

**분석 상세**:

advisory chain 스레드의 호출 경로를 추적하면:

```
_advisory_truth_gate()
  → self._truth_gate_llm_ask(prompt)
    → director.ask(prompt)     # BaseAgent.ask()
      → self._generate_content(model=..., contents=..., config=...)
        → self._llm_router.get_provider_for_model(model)  # ← 여기서 router 접근
        → provider.generate(client=self.client, request=...)
```

`_llm_router`는 `BaseAgent.__init__`에서 `get_shared_llm_router()`로 획득한 동일 인스턴스다. 8개 advisory 스레드가 동시에 `get_provider_for_model("gemini-2.5-pro")`를 호출하지만, Gemini provider는 이미 등록되어 있으므로 L118 `self._providers.get(provider_name)`에서 바로 반환된다. dict의 `get()` 연산은 CPython GIL 하에서 원자적이다.

**위험 시나리오 (현재 미도달)**:
- 멀티 Provider 전환 후, 처음으로 비-Gemini 모델을 advisory chain에서 동시 요청할 경우 L121 `_build_provider()`가 N번 중복 실행될 수 있음. Provider가 무상태이므로 기능적 문제는 없으나 불필요한 객체 생성 발생.

**신뢰도**: HIGH. **영향도**: 현재 NONE, 멀티 Provider 전환 시 LOW.

---

### [XC-LLM-004] P3 | AnthropicProvider/OpenAIProvider _client lazy init 비동기화

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-004 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `AnthropicProvider._get_client()`와 `OpenAIProvider._get_client()`가 Lock 없이 `self._client`를 lazy init한다. 멀티스레드에서 동시 호출 시 client가 중복 생성될 수 있다. |
| 코드 근거 | `modules/core/providers/anthropic_provider.py:30-44`, `modules/core/providers/openai_provider.py:17-30` |
| 영향 경계 | Anthropic/OpenAI provider 사용 시 (현재 disabled) |
| 테스트 근거 | 각 provider별 단일 스레드 테스트만 존재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | Lock 추가 (0.5h). 현재 disabled이므로 미도달. 향후 활성화 시 수정 필요. |

```python
# anthropic_provider.py:30-44
def _get_client(self):
    if self._client is not None:  # ← check
        return self._client
    # ... API key 확인 + SDK import ...
    self._client = Anthropic(api_key=api_key)  # ← write (Lock 없음)
    return self._client
```

**신뢰도**: HIGH. **영향도**: 현재 NONE (disabled).

---

## PASS 2: 교차 검증

| ID | PASS 1 판정 | 런타임 도달? | 기존 중복? | PASS 2 판정 |
|----|-------------|------------|----------|------------|
| XC-LLM-001 | P3 | 예 (모든 LLM 호출) | **T1-22 중복** | 제거 (중복) |
| XC-LLM-002 | P3 | 아니오 (Gemini-only) | T1-19 부분 관련 | P3 유지 |
| XC-LLM-003 | P3 | 예 (Stage4 advisory) | 신규 | P3 유지 |
| XC-LLM-004 | P3 | 아니오 (disabled) | 신규 | P3 유지 |

---

## PASS 3: 최종 확정

### 제거: XC-LLM-001
- **사유**: T1-22와 완전 중복.

### 확정: XC-LLM-002 (P3)
- T1-19는 "disabled provider가 build되는 논리적 허점"이고, 본 건은 "동시 build 시 동기화 부재". 관점이 다르므로 유지.
- 현재 Gemini-only 운영 시 미도달이므로 P3 유지.

### 확정: XC-LLM-003 (P3)
- Advisory chain 8스레드 동시 접근은 신규 관점.
- 현재 안전 (Gemini provider 사전 등록 + dict get 원자성).
- 형식적 개선만 필요하므로 P3 유지.

### 확정: XC-LLM-004 (P3)
- disabled provider의 lazy client init. 향후 활성화 시에만 유효.
- P3 유지.

---

## T1 최종 결론

| 등급 | 건수 | 비고 |
|------|------|------|
| P0 | 0 | - |
| P1 | 0 | - |
| P2 | 0 | - |
| P3 | 3 | XC-LLM-002, 003, 004 (모두 형식적 동기화 부재, 현재 무해) |
| 제거 | 1 | XC-LLM-001 (T1-22 중복) |

**핵심 판단**: 현재 Gemini-only 운영 환경에서 LLM Router의 스레드 안전성은 **사실상 보장**된다. CPython GIL이 dict 연산을 보호하고, Gemini provider는 `__init__`에서 사전 등록되어 lazy-build 경로를 타지 않는다. 멀티 Provider 전환 시에만 Lock 추가가 의미를 가진다.
