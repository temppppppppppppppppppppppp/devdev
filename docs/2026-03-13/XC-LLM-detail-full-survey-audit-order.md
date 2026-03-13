# XC-LLM Track: LLM Provider 추상화 계층 안전성 — 조사 계획

> 작성일: 2026-03-13
> 감사 대상: LLM Router / Provider / Generate 계층 전체

---

## 1. 감사 범위

| 파일 | 줄 수 (approx) | 역할 |
|------|------|------|
| `modules/core/llm_router.py` | 139 | Shared Singleton Router, Provider 해석/빌드 |
| `modules/core/llm_provider.py` | 37 | LLMProvider Protocol, LLMRequest/LLMResponse 데이터클래스 |
| `modules/core/llm_generate.py` | 22 | `generate_content_via_router()` 공용 헬퍼 |
| `modules/core/constants.py` | 905 | `AIModels` import-time YAML 캐시, `_LazyThreshold` |
| `modules/domain/agents/base_agent.py` | 1800+ | `_generate_content()` provider shim, fallback chain |
| `modules/core/providers/gemini_provider.py` | 50 | Gemini Provider 구현체 |
| `modules/core/providers/anthropic_provider.py` | 89 | Anthropic Provider 구현체 |
| `modules/core/providers/openai_provider.py` | 107 | OpenAI Provider 구현체 |
| `modules/core/providers/vertex_provider.py` | 119 | Vertex AI Provider 구현체 |

---

## 2. 타겟별 조사 초점

### XC-LLM-T1: Shared Router Singleton 스레드 안전

**조사 대상 코드**:
- `llm_router.py:131-138` — `_SHARED_ROUTER` global + `get_shared_llm_router()` (Lock 없음)
- `llm_router.py:112-125` — `get_provider_for_model()` 내 lazy `_build_provider()` + `self._providers[name] = provider`
- `base_agent.py:287` — `__init__`에서 `get_shared_llm_router()` 호출
- `stage4_interview_round.py:3807` — `ThreadPoolExecutor(max_workers=8)` advisory chain

**조사 질문**:
1. `_SHARED_ROUTER` 싱글톤 생성 시 race condition 가능한가?
2. `get_provider_for_model()` 내 `_providers` dict 동시 읽기/쓰기가 발생하는가?
3. Advisory chain 8스레드가 동시에 router를 통해 API 호출 시 문제가 있는가?
4. GIL이 실질적 보호를 제공하는가?

### XC-LLM-T2: Provider간 Response 타입 분산

**조사 대상 코드**:
- `llm_generate.py:21` — `return response.raw` (Any 타입)
- `llm_provider.py:27` — `LLMResponse.raw: Any | None`
- 각 Provider의 `generate()` → `LLMResponse` 생성 패턴
- 호출자의 `response.text` 접근 패턴

**조사 질문**:
1. `generate_content_via_router()`가 `response.raw`를 반환하는데, 호출자가 `.text` 접근 시 provider별로 안전한가?
2. Provider간 `usage` dict 키가 일관되지 않는 문제가 있는가?
3. `finish_reason` 값이 provider별로 다른데, 하류 코드가 이를 올바르게 처리하는가?

### XC-LLM-T3: 모델 설정 런타임 불변성

**조사 대상 코드**:
- `constants.py:9-24` — `_load_model_from_yaml()` import-time 호출
- `constants.py:266-298` — `AIModels` 클래스 (import-time 캐싱)
- `base_agent.py:85-96` — `_load_model_config()` 매 호출 시 파일 I/O
- `llm_router.py:31-47` — `_load_provider_configs()` 인스턴스 생성 시 파일 I/O

**조사 질문**:
1. `AIModels` 상수가 import-time에 고정되는데, YAML 파일 변경 시 반영 불가한가?
2. `base_agent.py` `_load_model_config()`은 매 에이전트 생성마다 YAML을 읽는데, 성능/일관성 문제는?
3. `_SHARED_ROUTER`의 `force_reload=True` 경로가 안전한가?

---

## 3. 3-Pass 방법론

| Pass | 목적 | 기준 |
|------|------|------|
| PASS 1 | 후보 수집 | 코드 근거 + HIGH/MED/LOW 신뢰도 |
| PASS 2 | 교차 검증 | 런타임 도달 가능성, 기존 262+ finding 중복 확인 |
| PASS 3 | 최종 확정 | 오탐 제거, P0-P3 최종 배정 |

---

## 4. 기존 finding 교차 참조 대상

| ID | 내용 | 출처 |
|----|------|------|
| T1-11 | `llm_generate.py:21` raw → 멀티 Provider 전환 시 잠재적 | OPUS-TF-T1 (P3 하향) |
| T1-18 | `llm_router.py:45-46` YAML 실패 시 silent pass | OPUS-TF-T1 (P3) |
| T1-19 | `llm_router.py:112-125` disabled provider lazy-build 허점 | OPUS-TF-T1 (P3) |
| T1-22 | `llm_router.py:134-138` 싱글톤 비원자적 | OPUS-TF-T1 (P3) |
| T1-31 | `constants.py:40-50` _LazyThreshold 멀티스레드 중복 계산 | OPUS-TF-T1 (P3) |

---

## 5. 출력 파일

1. `XC-LLM-T1-shared-router-singleton-thread-safety-findings.md`
2. `XC-LLM-T2-provider-response-type-dispersion-findings.md`
3. `XC-LLM-T3-model-config-runtime-immutability-findings.md`
4. `XC-LLM-consolidated-findings.md`
5. `XC-LLM-consolidated-findings-3pass-reaudit.md`
