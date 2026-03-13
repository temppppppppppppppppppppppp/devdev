# XC-LLM Track: 3-Pass 재감사 최종본 — 오탐 제거 완료

> 작성일: 2026-03-13
> 3-Pass 재감사 완료: 오탐 제거 + 최종 severity 확정

---

## 3-Pass 재감사 요약

| 단계 | 결과 |
|------|------|
| PASS 1 (후보 수집) | 14건 수집 |
| PASS 2 (교차 검증) | 1건 중복 제거 (XC-LLM-001 = T1-22), 13건 유지 |
| PASS 3 (오탐 제거) | 1건 추가 제거 (XC-LLM-013: force_reload 호출자 0건 확인, 이론적 경로만), **최종 12건** |

---

## 오탐 제거 상세

### 제거 1: XC-LLM-001 — T1-22 완전 중복
- **PASS 1 내용**: `_SHARED_ROUTER` 싱글톤 초기화 시 Lock 부재
- **제거 사유**: 기존 T1-22 (P3)와 동일 파일, 동일 줄, 동일 현상

### 제거 2: XC-LLM-013 — force_reload 호출자 부재로 사실상 dead path
- **PASS 1 내용**: `force_reload=True` 시 기존 에이전트 인스턴스와 경합
- **제거 사유**: 전체 코드베이스에서 `force_reload=True` 호출자가 0건. 코드 경로 자체가 미도달. 향후 호출자 추가 시 재평가 필요하나, 현재 finding으로 유지할 실익 없음.

---

## 최종 확정 Findings (12건)

### P2 (2건) — 멀티 Provider 전환 시 P1 전이 가능

#### [XC-LLM-005] P2 | generate_content_via_router() raw 반환 → 호출자 Gemini 의존

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-005 |
| Severity | P2 |
| 현상 요약 | `generate_content_via_router()`가 `response.raw`를 반환. 호출자 15곳+이 `.text` 접근. Anthropic/OpenAI raw 응답에 `.text` 속성 없음. |
| 코드 근거 | `modules/core/llm_generate.py:21` — `return response.raw` |
| 영향 경계 | 호출자: adversarial_self_play, advisory_validator, chain_of_verification, cross_agent_verifier, multi_agent_deliberation, narrative_structure_analyzer, self_reflection, tree_of_thoughts, scoring_validator, main_a.py (2곳), stage0 modules (3곳), stage4_orchestrator |
| 테스트 근거 | `test_llm_router.py` — Gemini raw 보존 테스트만. 비-Gemini 호출자 호환성 미검증. |
| 기존 중복 여부 | T1-11 확장 (T1-11은 P3 하향 판정, 본 건은 호출자 전수 조사로 영향 범위 확대) |
| 권장 후속 조치 | `return response` (LLMResponse 반환)로 변경. 호출자 `response.text`는 LLMResponse.text에서 동작. 공수: 2h. |
| 3-Pass 판정 | **확정** — 의도적 기술 부채(base_agent.py 주석 확인), 현재 안전, 전환 시 필수 수정 |

#### [XC-LLM-008] P2 | BaseAgent._generate_content() raw 반환 — 12+ 에이전트 영향

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-008 |
| Severity | P2 |
| 현상 요약 | `BaseAgent._generate_content()`가 `response.raw` 반환. 모든 에이전트의 LLM 호출이 Gemini native 응답 구조에 의존. |
| 코드 근거 | `modules/domain/agents/base_agent.py:345` — `return response.raw` |
| 영향 경계 | ChiefWriter, Director, Analyst, Weaver, Writer 등 12+ 에이전트 |
| 테스트 근거 | 반환 타입 검증 테스트 부재 |
| 기존 중복 여부 | XC-LLM-005 동일 근본 원인, 다른 경로 |
| 권장 후속 조치 | `return response` + 점진 마이그레이션. `ask()` 등 고수준 메서드에서 `.text` 접근 패턴 통일. 공수: 4h. |
| 3-Pass 판정 | **확정** — 주석에 "Phase 1 provider shim" 명시, 의도적 기술 부채 |

---

### P3 (10건) — 코드 스멜 / 형식적 개선

#### [XC-LLM-002] P3 | get_provider_for_model() _providers dict lazy write 비동기화

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-002 |
| Severity | P3 |
| 현상 요약 | `get_provider_for_model()`에서 미등록 provider lazy-build 시 `_providers` dict에 Lock 없이 write. |
| 코드 근거 | `modules/core/llm_router.py:118-122` |
| 영향 경계 | 멀티 Provider 전환 시에만 유효 (현재 Gemini provider 사전 등록) |
| 테스트 근거 | 멀티스레드 등록 테스트 부재 |
| 기존 중복 여부 | T1-19 부분 관련 (관점 차이: T1-19=논리적 허점, 본 건=동시성) |
| 권장 후속 조치 | Lock 추가. 공수: 0.5h. |
| 3-Pass 판정 | **확정** |

#### [XC-LLM-003] P3 | Advisory chain 8스레드 동시 router 접근

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-003 |
| Severity | P3 |
| 현상 요약 | Stage4 advisory chain의 `ThreadPoolExecutor(max_workers=8)`에서 8스레드가 동일 router 인스턴스에 동시 접근. 현재 Gemini provider 사전 등록으로 read-only 경로만 사용되어 안전. |
| 코드 근거 | `modules/core/stage4_interview_round.py:3807-3812`, `modules/domain/agents/base_agent.py:287,342` |
| 영향 경계 | Stage4 에피소드 생성 |
| 테스트 근거 | 멀티스레드 router 접근 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 형식적 Lock 추가. 공수: 0.5h. |
| 3-Pass 판정 | **확정** |

#### [XC-LLM-004] P3 | Anthropic/OpenAI Provider _client lazy init 비동기화

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-004 |
| Severity | P3 |
| 현상 요약 | Anthropic/OpenAI provider의 `_get_client()`가 Lock 없이 `self._client` lazy init. |
| 코드 근거 | `modules/core/providers/anthropic_provider.py:30-44`, `modules/core/providers/openai_provider.py:17-30` |
| 영향 경계 | 해당 provider 활성화 시 (현재 disabled) |
| 테스트 근거 | 단일 스레드 테스트만 존재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 활성화 시 Lock 추가. 공수: 0.5h. |
| 3-Pass 판정 | **확정** |

#### [XC-LLM-006] P3 | Provider간 usage dict 키 불일치

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-006 |
| Severity | P3 |
| 현상 요약 | Gemini: `prompt_token_count/candidates_token_count`, Anthropic/OpenAI: `input_tokens/output_tokens`. BaseAgent의 `_build_metric_usage_payload()`가 Gemini 키만 탐색. |
| 코드 근거 | `modules/domain/agents/base_agent.py:382-386` |
| 영향 경계 | 비용 추적 (멀티 Provider 전환 시 토큰 수 0으로 기록) |
| 테스트 근거 | 교차 provider usage 소비 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | usage 키 정규화. 공수: 1h. |
| 3-Pass 판정 | **확정** |

#### [XC-LLM-007] P3 | Provider간 finish_reason 값 체계 불일치

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-007 |
| Severity | P3 |
| 현상 요약 | Gemini: `"STOP"` (대문자), Anthropic: `"end_turn"`, OpenAI: `"completed"`. |
| 코드 근거 | 각 provider의 `generate()` 메서드 |
| 영향 경계 | finish_reason 분기 로직 (제한적) |
| 테스트 근거 | 정규화 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | LLMResponse 생성 시 정규화. 공수: 1h. |
| 3-Pass 판정 | **확정** |

#### [XC-LLM-009] P3 | Gemini/Vertex Provider 응답 파싱 코드 중복

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-009 |
| Severity | P3 |
| 현상 요약 | GeminiProvider와 VertexAIProvider의 generate() 내 응답 파싱 코드 ~30줄 동일. |
| 코드 근거 | `modules/core/providers/gemini_provider.py:11-49` vs `modules/core/providers/vertex_provider.py:79-118` |
| 영향 경계 | 유지보수 |
| 테스트 근거 | 각 provider 독립 테스트 존재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 공통 헬퍼 추출. 공수: 1h. |
| 3-Pass 판정 | **확정** |

#### [XC-LLM-010] P3 | AIModels import-time 캐싱으로 YAML 변경 미반영

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-010 |
| Severity | P3 |
| 현상 요약 | AIModels 15개 상수가 import-time 고정. 런타임 YAML 변경 미반영. |
| 코드 근거 | `modules/core/constants.py:266-298` |
| 영향 경계 | 이론적 (운영 중 YAML 변경 시나리오 없음) |
| 테스트 근거 | import-time 동작 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 의도된 설계. 수정 불필요. |
| 3-Pass 판정 | **확정** (의도적 설계로 인정) |

#### [XC-LLM-011] P3 | _load_model_config() 매 호출 YAML I/O (캐싱 없음)

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-011 |
| Severity | P3 |
| 현상 요약 | `base_agent.py` `_load_model_config()`이 에이전트 생성마다 `models.yaml` 읽기. |
| 코드 근거 | `modules/domain/agents/base_agent.py:85-96` |
| 영향 경계 | 성능 (미미: 65줄 YAML, OS 파일 캐시 적중) |
| 테스트 근거 | 캐싱 동작 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 모듈-레벨 캐시 추가. 공수: 0.5h. |
| 3-Pass 판정 | **확정** |

#### [XC-LLM-012] P3 | AIModels(import-time)와 _load_model_config()(런타임) 간 불일치 가능

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-012 |
| Severity | P3 |
| 현상 요약 | 두 경로가 다른 시점에 YAML을 읽어 모델명 불일치 가능. |
| 코드 근거 | `modules/core/constants.py:295` vs `modules/domain/agents/base_agent.py:290-292` |
| 영향 경계 | 이론적 (운영 중 YAML 변경 시) |
| 테스트 근거 | 일관성 검증 테스트 부재 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 두 경로 통일 (장기). 공수: 2h. |
| 3-Pass 판정 | **확정** |

#### [XC-LLM-014] P3 | _load_model_from_yaml 실패 시 silent fallback

| 필드 | 내용 |
|------|------|
| ID | XC-LLM-014 |
| Severity | P3 |
| 현상 요약 | `except Exception: pass` — 모든 예외를 무시하고 fallback 반환. 로깅 없음. |
| 코드 근거 | `modules/core/constants.py:22-23` |
| 영향 경계 | 디버깅 편의 |
| 테스트 근거 | YAML 로드 실패 테스트 부재 |
| 기존 중복 여부 | T1-18 동일 패턴 (다른 파일) |
| 권장 후속 조치 | `logging.debug()` 추가. 공수: 0.25h. |
| 3-Pass 판정 | **확정** |

---

## 최종 통계

| 등급 | 건수 | Finding ID |
|------|------|-----------|
| P0 | 0 | - |
| P1 | 0 | - |
| P2 | 2 | XC-LLM-005, XC-LLM-008 |
| P3 | 10 | XC-LLM-002, 003, 004, 006, 007, 009, 010, 011, 012, 014 |
| 제거 | 2 | XC-LLM-001 (T1-22 중복), XC-LLM-013 (dead path) |

---

## 핵심 결론

1. **P0/P1 이슈 없음**: 현재 Gemini-only 운영 환경에서 LLM Provider 추상화 계층은 안전하게 동작한다.

2. **멀티 Provider 전환 시 필수 수정 2건**: XC-LLM-005, XC-LLM-008의 `response.raw` 반환 패턴이 **유일한 blocking issue**. 수정 공수 ~6h. 이 두 건은 코드 주석에서도 "Phase 1 provider shim"으로 의도적 기술 부채임을 인정하고 있다.

3. **스레드 안전성**: CPython GIL + Gemini provider 사전 등록으로 현재 안전. Lock 추가는 형식적 개선.

4. **모델 설정**: import-time 캐싱은 의도적 설계. CLI 기반 1회 실행 패턴에 적합.

5. **총 수정 공수**: 전체 12건 수정 시 ~11.25h. 우선순위 1-2번 (P2 2건)만 수정하면 ~6h.
