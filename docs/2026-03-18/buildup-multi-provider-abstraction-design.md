# 멀티프로바이더 추상화 레이어 설계문서

**문서 유형**: 빌드업 (코드 변경 전 설계 확정)
**대상**: S4-EX-MP1 (LLM Integration Execution)
**작성일**: 2026-03-18
**상태**: DESIGN — 코드 미착수
**감리**: 3회 전면 재조사 + 적대적 3-pass 완료 (6 TF 병렬 투입)
**교정 이력**: 초판 3파일 → 2차 18파일 → **3차 25+파일** (Stage 0 우회 5개, 인프라 2개 추가, response_schemas dict layer 기발견)

---

## 1. 현행 Gemini SDK 결합도 전수 조사

### 1.1 핵심 호출 체인
```
BaseAgent.ask(prompt)
  → _build_model_stack()         # types.GenerateContentConfig 생성 (Gemini 전용)
    → _generate_content()        # _generate_llm_response().raw 반환
      → _generate_llm_response() # LLMProviderRouter → Provider.generate()
        → GeminiProvider.generate(client, request)
          → client.models.generate_content(model, contents, config)
```

### 1.2 Gemini SDK 의존 파일 전수 목록

**3회 전면 재조사 반영: 총 25+개 파일 (초판 3 → 2차 18 → 3차 25+)**

#### A. 인프라 계층 (5파일)
| 파일 | Gemini 전용 사용 | 영향도 |
|------|-----------------|--------|
| `base_agent.py` | `types.GenerateContentConfig`(L989,1194,1347,2022), `types.ThinkingConfig`(L987), `types.HttpOptions`(L974), `client.caches.create()`(L1923) | CRITICAL |
| `response_schemas.py` | `types.Schema` 282건, `types.Type` 274건, `client.models.generate_content`(L899) | CRITICAL — **완화: `_TASK_SCHEMA_SPECS` dict 레지스트리(L662)와 `get_schema_spec_for_task()`(L685)가 이미 프로바이더 중립 dict 반환. `get_schema_for_task()`(L682)만 Gemini 전용 — 이 함수에 프로바이더 분기 추가하면 해결** |
| `llm_schema.py` | `to_gemini_schema()`, `schema_to_dict()`, `_TYPE_NAME_TO_GEMINI` 매핑 | CRITICAL — **양방향 변환 이미 구현** |
| `narrative_structure_analyzer.py` | `types.GenerateContentConfig`(L148), `response_mime_type`(L151) | MEDIUM **(3차 발견)** |
| `tree_of_thoughts.py` | `response_mime_type`(L657) dict config | LOW **(3차 발견)** |

#### B. 에이전트 계층 (10파일)
| 파일 | Gemini 전용 사용 |
|------|-----------------|
| `analyst.py` | `types.GenerateContentConfig`, `cached_content` |
| `director_caching.py` | `from google.genai import types` |
| `director_continuity.py` | `types.GenerateContentConfig` |
| `manuscript_validator.py` | `_types.GenerateContentConfig` |
| `state_tracker_npc.py` | `types.GenerateContentConfig` (2개 메서드) |
| `weaver.py` | `types.GenerateContentConfig`, `cached_content` |
| `writer.py` | `types.GenerateContentConfig` |
| `blueprint_ensemble.py` | `response_schema` (Gemini `types.Schema` 객체) |
| `three_phase_blueprint_generator.py` | `response_schema` (Gemini `types.Schema` 객체) |
| `stage4_orchestrator.py` | `types.GenerateContentConfig` |

#### C. 검증 계층 (2파일)
| 파일 | Gemini 전용 사용 |
|------|-----------------|
| `advisory_validator.py` | `types.GenerateContentConfig` |
| `scoring_validator.py` | `types.GenerateContentConfig` |

#### D. Stage 0 / 유틸리티 계층 (5파일 — 3차 전면 재조사에서 발견, BaseAgent 경로 우회)
| 파일 | Gemini 전용 사용 |
|------|-----------------|
| `stage0/story_expander.py` | **자체 `genai.Client()` 생성**(L57), `types.GenerateContentConfig`(L82) |
| `stage0/reverse_expander.py` | **자체 `genai.Client()` 생성**(L67), `types.GenerateContentConfig`(L92) |
| `stage0/style_extractor.py` | **자체 `genai.Client()` 생성**(L1150), `types.GenerateContentConfig`(L1176) |
| `vec_memory.py` | **자체 `genai.Client()` 생성**(L139) |
| `semantic_plot_guard.py` | **자체 `genai.Client()` 생성**(L79) |

> **위험**: 이 5개 모듈은 BaseAgent.ask()를 사용하지 않고 Gemini API를 직접 호출. 멀티프로바이더 전환 시 별도 추상화 필요.

#### E. 진입점 (1파일)
| 파일 | Gemini 전용 사용 |
|------|-----------------|
| `main_a.py` | `genai.Client()`(L355,1184), `types.GenerateContentConfig`(L3961), `client.caches.create()`(L1420,1445,1469) — **캐싱 3곳** |

#### F. 프로바이더 (1파일)
| 파일 | 변경 필요 |
|------|----------|
| `anthropic_provider.py` | 메시지 변환 강화, timeout/usage 매핑 |

#### G. 설정 (1파일)
| 파일 | 변경 필요 |
|------|----------|
| `config/models.yaml` | 프로바이더 활성화, 에이전트-모델 매핑 |

**합계: `from google.genai import types` 포함 파일 25개**

> **주의**: 이 중 `tools2/` 및 `tools/` 디렉토리의 독립 스크립트 7개 (bible_builder, genre_library_builder, story_expander, treatment_builder, treatment_extractor, expand_ep15, style_transfer)는 프로덕션 파이프라인 외부. 멀티프로바이더 전환의 **필수 변경 대상은 프로덕션 18개 파일**이며, tools/ 7개는 선택적 후속 작업.

> **긍정적 발견**: `response_schemas.py`에 `_TASK_SCHEMA_SPECS` dict 레지스트리(L662)와 `get_schema_spec_for_task()` 함수(L685)가 이미 존재. 스키마 중립화 작업의 ~50%가 완료된 상태. `to_gemini_schema()`/`schema_to_dict()` 양방향 변환도 `llm_schema.py`에 구현됨.

### 1.3 응답 객체 호환성

`_generate_content()` → `_generate_llm_response().raw` 반환

| 접근 패턴 | 위치 | 안전성 |
|-----------|------|--------|
| `response.text` | `_extract_and_merge_response()` 내부 | try/except 보호 |
| `response.candidates[0].content.parts` | thinking 추출 | try/except 보호 |
| `response.candidates` (falsy 체크) | 이어쓰기 판정 | **미보호 — AttributeError 위험** |
| `response.candidates[0].finish_reason` | 위 가드 뒤 | 조건부 안전 |
| `res.text` (백업) | `_attempt_backup_recovery()` | try/except 보호 |

### 1.4 response_schemas.py 현황 (초판 완전 누락 → 3차 재조사에서 긍정/부정 양면 확인)

**기존 프로바이더 중립 인프라 (이미 존재)**:
```python
# L662: dict 레지스트리 (프로바이더 중립)
_TASK_SCHEMA_SPECS = {name: schema_to_dict(schema) for name, schema in _TASK_SCHEMA_CONSTANTS.items()}

# L685: dict 반환 함수 (프로바이더 중립)
def get_schema_spec_for_task(task_type: str) -> dict | None:
    return deepcopy(_TASK_SCHEMA_SPECS.get(task_type))
```

**Gemini 전용 진입점 (변경 필요)**:
```python
# L682: Gemini types.Schema 반환 — 이 함수에만 프로바이더 분기 추가
def get_schema_for_task(task_type: str) -> types.Schema:
    spec = get_schema_spec_for_task(task_type)
    return to_gemini_schema(spec) if spec else None  # 항상 Gemini!
```

**영향**: 에이전트가 `response_schema=get_schema_for_task("BLUEPRINT")` 형태로 호출.
Claude 전환 시 `get_schema_for_task()` → `get_schema_for_model(task, model)` 교체 필요.
**단, dict→Gemini 양방향 변환이 `llm_schema.py`에 이미 구현**되어 있으므로 작업량은 예상보다 적음.

---

## 2. 목표 아키텍처 (멀티프로바이더)

### 2.1 설계 원칙

1. **YAML 드리븐**: `models.yaml`의 에이전트-모델 매핑으로 프로바이더 자동 전환
2. **점진 전환**: Gemini 전용 기능(컨텍스트 캐싱, Thinking, Schema)은 Gemini에서만 활성
3. **폴백 크로스오버**: `claude-opus-4-6` → `claude-sonnet-4-6` → `gemini-2.5-pro` → `gemini-2.5-flash`
4. **스키마 중립화**: `response_schemas.py` → dict 기반 스키마로 전환, 프로바이더별 변환

### 2.2 핵심 변경 — 5개 계층

#### 계층 1: 스키마 중립화 (response_schemas.py + llm_schema.py)

```python
# 목표: dict 기반 스키마 정의 → 프로바이더별 변환
def get_schema_spec_for_task(task_type: str) -> dict:
    """프로바이더 중립 dict 스키마 반환 (현행 유지)"""
    ...

def get_schema_for_model(task_type: str, model: str):
    """모델에 따라 적절한 스키마 형식 반환"""
    spec = get_schema_spec_for_task(task_type)
    if not spec:
        return None
    if is_gemini_model(model):
        return to_gemini_schema(spec)  # types.Schema
    # Claude/OpenAI: dict 그대로 반환 (또는 None — 프롬프트로 JSON 강제)
    return spec  # 또는 None
```

**영향**: `blueprint_ensemble.py`, `three_phase_blueprint_generator.py` 등에서 `get_schema_for_model(task, self.primary_model)` 호출로 교체.

#### 계층 2: Config 빌드 중앙화 (base_agent.py)

```python
@staticmethod
def _is_gemini_model(model: str) -> bool:
    normalized = (model or "").strip().lower()
    return normalized.startswith(("gemini", "vertexai:", "vertex:", "vertex/"))

def _build_llm_config(self, *, model, temperature, thinking_level=None,
                       response_schema=None, cached_content=None):
    """프로바이더별 적절한 config 반환"""
    # Gemini → types.GenerateContentConfig
    # 비-Gemini → dict
```

**영향**: `_build_model_stack()`, `_handle_api_error()`, `_attempt_backup_recovery()`, `_ask_with_cached_context()` — 4곳 교체.

**추가 필요**: 10개 에이전트 파일에서 직접 생성하는 `types.GenerateContentConfig`도 이 헬퍼로 교체하거나, `ask()` 경로로 우회.

#### 계층 3: 응답 래퍼 (base_agent.py)

```python
class _FinishCandidate:
    __slots__ = ("finish_reason", "content")
    def __init__(self, finish_reason):
        self.finish_reason = finish_reason
        self.content = None

class _UnifiedRawResponse:
    __slots__ = ("text", "candidates")
    _FINISH_MAP = {
        "end_turn": "STOP", "stop": "STOP", "completed": "STOP",
        "max_tokens": "MAX_TOKENS", "length": "MAX_TOKENS",
    }
    def __init__(self, text, finish_reason="stop"):
        self.text = text
        mapped = self._FINISH_MAP.get((finish_reason or "stop").lower(), "STOP")
        self.candidates = [_FinishCandidate(mapped)]
```

#### 계층 4: 에이전트 Gemini 직접 의존 제거 (10+ 파일)

| 패턴 | 현행 | 목표 |
|------|------|------|
| `types.GenerateContentConfig(...)` 직접 생성 | 10개 에이전트 | `self._build_llm_config()` 또는 `self.ask()` 경로 사용 |
| `config_params["cached_content"] = ...` | 5개 에이전트 | Gemini 전용 가드 또는 `_ask_with_cached_context()` 위임 |
| `from google.genai import types` | 10개 에이전트 | 제거 (base_agent 헬퍼로 대체) |

#### 계층 5: 진입점 (main_a.py)

```python
# 현행: genai.Client() 하드코딩
self.sys = StudioSystem(api_client=genai.Client(api_key=...))

# 목표: Gemini client는 유지 (Flash 에이전트용), Claude는 프로바이더가 자체 관리
# genai.Client()는 Gemini 에이전트 전용으로 유지 — AnthropicProvider는 자체 _get_client() 사용
```

**main_a.py는 최소 변경**: `genai.Client()`는 Gemini 에이전트용으로 유지. Claude 에이전트는 `AnthropicProvider._get_client()`가 독립 관리.

### 2.3 컨텍스트 캐싱 전략

| 프로바이더 | 캐싱 방식 | 글도비 대응 |
|-----------|----------|-----------|
| Gemini | `client.caches.create()` → `cached_content` 파라미터 | 현행 유지 |
| Claude | 자동 prompt caching (API 요청 시 자동 적용) | 캐싱 코드 스킵, `ask()` 폴백 |

**5개 캐싱 에이전트** (ChiefWriter, ArcEnsemble, BprintEnsemble, DirectorEnsemble, DirectorContinuity):
- `_get_or_create_context_cache()`: 비-Gemini면 `cache_name=None` 반환
- `_ask_with_cached_context()`: `cache_name=None` 시 `ask()` 폴백 (현행 로직)

---

## 3. 영향 범위 매트릭스 (교정판)

| 계층 | 파일 수 | 예상 변경량 | 위험도 |
|------|--------|-----------|--------|
| 스키마 중립화 | 2 (response_schemas, llm_schema) | ~30줄 | **MEDIUM** — dict layer 이미 존재, 프로바이더 분기만 추가 |
| Config 중앙화 | 1 (base_agent) | ~100줄 | **MEDIUM** — 핵심 경로 |
| 응답 래퍼 | 1 (base_agent) | ~30줄 | LOW |
| 에이전트 의존 제거 | 10 (agent files) | ~10줄/파일 | **MEDIUM** — 반복 작업 |
| 검증 의존 제거 | 2 (validators) | ~10줄/파일 | LOW |
| Stage 0 / 유틸리티 추상화 | 5 (story_expander 등) | ~20줄/파일 | **HIGH** — 자체 genai.Client 우회 |
| 인프라 (narrative_analyzer 등) | 2 | ~10줄/파일 | LOW |
| 프로바이더 강화 | 1 (anthropic_provider) | ~40줄 | LOW |
| 진입점 캐싱 | 1 (main_a) | ~20줄 | MEDIUM — 캐싱 3곳 |
| 설정 | 1 (models.yaml) | ~65줄 | LOW |
| **합계** | **~25파일** | **~500줄** | |

---

## 4. 실행 순서 (코드 착수 시)

```
Phase 1: 스키마 중립화 (가장 위험, 선행 필수)
  1. response_schemas.py: get_schema_for_model() 추가
  2. llm_schema.py: 프로바이더 분기 추가
  3. 스키마 사용 에이전트 4개 교체

Phase 2: base_agent.py 핵심 변경
  4. _is_gemini_model() + _build_llm_config() 추가
  5. _UnifiedRawResponse 클래스 추가
  6. _generate_content() 수정
  7. _build_model_stack() / _handle_api_error() / _attempt_backup_recovery() 교체
  8. _get_or_create_context_cache() 프로바이더 가드
  9. DEFAULT_MODEL_FALLBACK_CHAIN 업데이트

Phase 3: 에이전트 Gemini 의존 제거
  10. 10개 에이전트: types.GenerateContentConfig → _build_llm_config() 또는 ask()
  11. 2개 검증기: 동일 패턴

Phase 4: 프로바이더 + 설정
  12. anthropic_provider.py 강화
  13. models.yaml Option A 적용

Phase 5: 테스트
  14. 단위 테스트 + 통합 테스트 + 1에피소드 파일럿
```

**예상 소요: 16-24시간** (초판 4-6시간, 2차 12-16시간 주장 재교정 — Stage 0 우회 경로 5개 추가)

> **완화 요인**: response_schemas dict layer 이미 존재 → 스키마 작업 예상보다 경량 (-3시간).
> **악화 요인**: Stage 0 모듈 5개가 BaseAgent 우회 → 별도 추상화 계층 필요 (+5시간).

---

## 5. 리스크 레지스터

| 리스크 | 영향 | 완화 |
|--------|------|------|
| Claude가 JSON 프롬프트만으로 스키마 준수 실패 | 파싱 에러 급증 | `_extract_json_robust()` 이미 강건, 모니터링 추가 |
| 에이전트별 GenerateContentConfig 제거 시 회귀 | 해당 에이전트 기능 저하 | 에이전트별 개별 테스트 필수 |
| main_a.py genai.Client가 Claude 에이전트에 전달 | 무해 (AnthropicProvider._get_client()가 자체 클라이언트 사용, L46-47 확인) | 검증 완료 |
| 크로스 프로바이더 폴백 시 스키마 불일치 | 폴백 실패 | 폴백 config에서 스키마 제거 또는 변환 |
| Verdict enum이 프로바이더별 스키마와 불일치 | 비-Gemini에서 PASS_WITH_FIX 등 미인식 | 프롬프트 기반 JSON 지시로 우회 (스키마 없이도 동작) |

---

## 6. 잔여 이슈 (최종 적대적 감리 지적, 미해결)

| 이슈 | 심각도 | 상태 |
|------|--------|------|
| tools/ 7개 독립 스크립트의 전환 시점 미정의 | LOW | 프로덕션 18파일 완료 후 후속 |
| `_is_gemini_model()` None 입력 처리 문서화 필요 | LOW | 코드 착수 시 docstring 추가 |
| 한국어 토크나이저 효율 비율 — 외부 자료, 미검증 | MEDIUM | 실측 비교 테스트 필요 (비용 테이블 문서 참조) |
| 소요 시간 추정 (16-24시간) 정확도 불확실 | MEDIUM | response_schemas 완화(-3h) vs Stage0 악화(+5h) 상쇄, 실제는 경험적 |
