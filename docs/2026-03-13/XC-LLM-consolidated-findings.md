# XC-LLM Track: 통합 Findings

> 작성일: 2026-03-13
> 감사 범위: LLM Provider 추상화 계층 전체

---

## 통계 요약

| 등급 | 건수 | 비고 |
|------|------|------|
| P0 | 0 | - |
| P1 | 0 | - |
| P2 | 2 | response.raw 반환 패턴 (멀티 Provider 전환 시 P1 전이) |
| P3 | 11 | 형식적 동기화, 코드 중복, 설정 캐싱 등 |
| 제거 | 1 | T1-22 중복 |
| **합계** | **13** (유효 12) | |

---

## P2 Findings (2건)

### [XC-LLM-005] P2 | generate_content_via_router()가 raw를 반환하여 호출자가 Gemini 구조에 의존

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-005 |
| Severity | P2 (멀티 Provider 전환 시 P1 전이) |
| 현상 요약 | `generate_content_via_router()`가 `response.raw`를 반환, 호출자 15곳+이 `.text` 접근. Anthropic/OpenAI raw에서 AttributeError. |
| 코드 근거 | `modules/core/llm_generate.py:21`, `modules/core/adversarial_self_play.py:159`, `modules/validation/advisory_validator.py:145`, `main_a.py:1569,2598` |
| 영향 경계 | `generate_content_via_router()` 호출 경로 전체 (~15곳) |
| 테스트 근거 | 비-Gemini provider의 raw 호출자 호환성 테스트 부재 |
| 기존 중복 여부 | T1-11 확장 |
| 권장 후속 조치 | `LLMResponse` 반환으로 변경. 공수: 2h. |

### [XC-LLM-008] P2 | BaseAgent._generate_content()도 response.raw 반환 — 동일 패턴

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-008 |
| Severity | P2 (멀티 Provider 전환 시 P1 전이) |
| 현상 요약 | `BaseAgent._generate_content()`가 `response.raw` 반환. 12+ 에이전트 전체가 Gemini raw 응답 구조에 의존. 주석에 의도적 기술 부채 명시. |
| 코드 근거 | `modules/domain/agents/base_agent.py:334-345` |
| 영향 경계 | BaseAgent 하위 클래스 전체 (ChiefWriter, Director, Analyst 등) |
| 테스트 근거 | 반환 타입 테스트 부재 |
| 기존 중복 여부 | XC-LLM-005 동일 패턴 |
| 권장 후속 조치 | `LLMResponse` 반환 + 점진 마이그레이션. 공수: 4h. |

---

## P3 Findings (11건)

### T1: 스레드 안전 (3건)

| ID | 제목 | 코드 근거 |
|----|------|----------|
| XC-LLM-002 | get_provider_for_model() 내 _providers dict lazy write 비동기화 | `llm_router.py:118-122` |
| XC-LLM-003 | Advisory chain 8스레드 동시 router 접근 | `stage4_interview_round.py:3807`, `base_agent.py:287,342` |
| XC-LLM-004 | Anthropic/OpenAI Provider _client lazy init 비동기화 | `anthropic_provider.py:30-44`, `openai_provider.py:17-30` |

### T2: Response 타입 분산 (3건)

| ID | 제목 | 코드 근거 |
|----|------|----------|
| XC-LLM-006 | Provider간 usage dict 키 불일치 | `gemini_provider.py:35-41` vs `anthropic_provider.py:77-80` vs `openai_provider.py:94-98` |
| XC-LLM-007 | Provider간 finish_reason 값 체계 불일치 | 각 provider의 `generate()` 메서드 |
| XC-LLM-009 | Gemini/Vertex Provider 응답 파싱 코드 중복 | `gemini_provider.py:11-49` vs `vertex_provider.py:79-118` |

### T3: 모델 설정 (5건)

| ID | 제목 | 코드 근거 |
|----|------|----------|
| XC-LLM-010 | AIModels import-time 캐싱으로 YAML 변경 미반영 | `constants.py:266-298` |
| XC-LLM-011 | base_agent.py _load_model_config() 매 호출 YAML I/O | `base_agent.py:85-96` |
| XC-LLM-012 | AIModels(import-time)와 _load_model_config()(런타임) 간 잠재적 불일치 | `constants.py:295` vs `base_agent.py:290-292` |
| XC-LLM-013 | force_reload 사용 시 기존 에이전트와의 경합 | `llm_router.py:134-138`, `base_agent.py:287` |
| XC-LLM-014 | _load_model_from_yaml 실패 시 silent fallback | `constants.py:22-23` |

---

## 제거 (1건)

| ID | 제목 | 사유 |
|----|------|------|
| XC-LLM-001 | _SHARED_ROUTER 싱글톤 초기화 경합 | T1-22 (P3) 완전 중복 |

---

## 기존 finding 교차 참조

| 본 Track finding | 기존 finding | 관계 |
|-----------------|-------------|------|
| XC-LLM-001 (제거) | T1-22 | 완전 중복 |
| XC-LLM-005 | T1-11 | 확장 (호출자 의존성 전수 조사) |
| XC-LLM-014 | T1-18 | 동일 패턴 (다른 파일) |
| XC-LLM-002 | T1-19 | 부분 관련 (동시성 관점 추가) |

---

## 권장 수정 우선순위

| 우선순위 | 작업 | 대상 Finding | 공수 |
|---------|------|------------|------|
| 1 | `generate_content_via_router()` → LLMResponse 반환 | XC-LLM-005 | 2h |
| 2 | `BaseAgent._generate_content()` → LLMResponse 반환 + 점진 마이그레이션 | XC-LLM-008 | 4h |
| 3 | usage dict 키 정규화 | XC-LLM-006 | 1h |
| 4 | _load_model_config() 모듈-레벨 캐시 | XC-LLM-011 | 0.5h |
| 5 | Router/Provider Lock 추가 | XC-LLM-002,003,004 | 1.5h |
| 6 | Gemini/Vertex 응답 파싱 중복 제거 | XC-LLM-009 | 1h |
| 7 | finish_reason 정규화 | XC-LLM-007 | 1h |
| 8 | silent fallback 로깅 | XC-LLM-014 | 0.25h |
| - | 나머지 (010, 012, 013) | 의도된 설계, 수정 불필요 | 0h |

**총 공수**: ~11.25h (멀티 Provider 전환 준비)
