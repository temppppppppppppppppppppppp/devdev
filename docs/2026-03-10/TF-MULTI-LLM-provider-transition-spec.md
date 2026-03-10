# TF-MULTI-LLM: 멀티 프로바이더 전환 실행 명세

> 작성: 2026-03-10
> 인코딩: UTF-8
> 목적: Claude API / OpenAI API / Vertex AI를 "도입 가능 상태"로 준비하되, 현재 운영은 Gemini 중심으로 유지
> 상태: 실행 문서화 완료
> 감리: 5-pass 재감리 완료
> 실행 판단: GO
> 실행 현황: Phase 0-4.5 완료
> 현재 중단선: non-Gemini 주권 경로 실운영 전환은 보류
> 단, "Gemini 유지", "백엔드 우선", "점진적 opt-in" 전제가 필수

---

## 1. 결론

이 문서는 이제 `바로 구현 순서를 잡을 수 있는 실행 문서`로 본다.

다만 방향은 원문보다 더 보수적으로 잡아야 한다.

1. 첫 배치는 `멀티 프로바이더 활성화`가 아니라 `멀티 프로바이더를 받아들일 추상화 껍데기`를 넣는 일이다.
2. `Director`, `Chief Writer`, `Analyst`는 첫 배치에서 계속 Gemini로 유지한다.
3. 프론트엔드와 브리지도 첫 배치에서는 건드리지 않는 쪽이 맞다.
4. 사용자가 실제로 다른 프로바이더로 갈아타지 않더라도, 이 배치는 의미가 있다.
   이유: 현재 코드의 Gemini 결합도를 낮추고, 이후 opt-in 전환 비용을 줄이기 때문이다.

---

## 2. 현재 상태 진단

### 2-A. 현재 코드 표면

| 항목 | 현재 상태 | 판정 |
|------|-----------|------|
| 기본 생성 SDK 표면 | `from google import genai`, `from google.genai import types` | 현행 사실 |
| 기본 인증 방식 | `GOOGLE_API_KEY` + `GOOGLE_API_KEY_2~9` | Gemini 중심 |
| 모델 SSOT | `config/models.yaml` 의 `agents`, `fallback_chain`, `sub_components`, `role_constants` | Gemini만 실사용 |
| 프론트 설정 UI | Gemini API Key 입력만 노출 | 멀티 프로바이더 미대응 |
| 브리지 입력 경로 | `ProcessRunner._build_env()` 가 Google 키만 subprocess env로 전달 | 멀티 프로바이더 미대응 |
| 임베딩 경로 | `VecMemory`, `SemanticPlotGuard` 모두 Gemini 임베딩 전용 | 1차 범위 밖 |

### 2-B. 감리로 확인된 핵심 사실

1. `google SDK import` 는 프로덕션 모듈 기준 `18개 파일`에 퍼져 있다.
2. direct `generate_content()` 호출은 프로덕션 모듈 기준 `21개 파일`에 퍼져 있다.
3. 따라서 `base_agent.ask()` 만 라우터로 감싸도 멀티 프로바이더 준비가 끝나지 않는다.
4. 프론트엔드와 브리지의 키/설정 흐름은 아직 `Google 전용`이다.
5. `requirements.txt`, `build/prepare_python_embed.ps1`, `geuldobi-desktop/DESKTOP-GUIDE.md` 는 아직 `google-generativeai` 라고 적고 있다.
   반면 코드 표면은 `from google import genai` 를 사용한다.
6. 즉, 구현 전 `의존성 선언과 실제 import 표면의 정합성 확인`이 먼저 필요하다.

### 2-C. 현재 문서에서 바로잡은 부분

- `SDK import 파일 17개` -> `18개` 로 보정
- `Phase 1에서 Claude/GPT 가격표까지 반영 완료` 서술 제거
- `Phase 2는 base_agent 위임만 하면 된다` 식의 과소 범위 서술 제거
- `초기 Director -> Claude 전환` 제안을 후순위 opt-in 실험으로 하향
- `프론트/브리지 변경` 을 필수 단계에서 선택 단계로 하향

---

## 3. 실행 원칙

### 3-A. 최상위 원칙

1. `Gemini-first 유지`
   첫 배치 후에도 `models.yaml` 이 전부 Gemini면 현재와 동일하게 동작해야 한다.
2. `백엔드 우선`
   처음부터 Electron 설정 UI, preload, bridge payload 를 바꾸지 않는다.
3. `추상화 우선, 전환은 나중`
   먼저 provider abstraction 을 넣고, 실제 provider cutover 는 후속 opt-in 으로 분리한다.
4. `임베딩 경로 분리`
   `VecMemory`, `SemanticPlotGuard` 같은 임베딩 경로는 1차 멀티 프로바이더 범위에 넣지 않는다.
5. `Director 주권 유지`
   프로바이더를 섞더라도 품질 판정 구조는 바꾸지 않는다.

### 3-B. 첫 배치에서 하지 않을 것

- Director를 Claude로 옮기지 않는다.
- Chief Writer를 OpenAI로 옮기지 않는다.
- 프론트엔드에 Anthropic/OpenAI 키 입력 UI를 넣지 않는다.
- 브리지 `/run` payload 에 provider 필드를 강제로 넣지 않는다.
- Vertex AI 서비스 계정 흐름을 1차 범위에 넣지 않는다.
- Gemini 임베딩 경로를 손대지 않는다.

---

## 4. 목표 아키텍처

```text
config/models.yaml
        |
        v
LLMProviderRouter
        |
   +----+----+---------+
   |         |         |
Gemini   Anthropic   OpenAI
   |
Vertex AI (후순위, 선택)
```

### 4-A. 최소 인터페이스

```python
@dataclass
class LLMRequest:
    prompt: str | list[dict]
    model: str
    temperature: float = 0.7
    max_tokens: int = 8192
    response_format: str = "text"
    json_schema: dict | None = None
    thinking: bool = False
    thinking_budget: int = 0
    timeout_ms: int = 300_000
    cache_key: str | None = None


@dataclass
class LLMResponse:
    text: str
    thinking_text: str = ""
    finish_reason: str = "stop"
    usage: dict | None = None
    raw: object | None = None


class LLMProvider(Protocol):
    def generate(self, request: LLMRequest) -> LLMResponse: ...
    def supports_caching(self) -> bool: ...
    def supports_thinking(self) -> bool: ...
    def supports_json_schema(self) -> bool: ...
```

### 4-B. 중요한 해석

- `GeminiProvider` 는 첫 배치에서 기존 동작을 최대한 그대로 감싼다.
- `AnthropicProvider` 와 `OpenAIProvider` 는 처음엔 `추가만` 하고, 기본 라우팅에는 쓰지 않는다.
- `Vertex AI` 는 별도 인증/배포 부담이 크므로 마지막 단계로 미룬다.

---

## 5. 실제 실행 순서

### Phase 0. 사전 정합성 정리

목표: 런타임 표면과 의존성 선언을 맞추되, 동작은 바꾸지 않는다.

### 작업

- clean env 기준으로 `from google import genai` import smoke 확인
- `requirements.txt` 의 Google SDK 표기 정합성 확인
- `build/prepare_python_embed.ps1` 의 런타임 패키지 표기 정합성 확인
- `geuldobi-desktop/DESKTOP-GUIDE.md` 의 SDK 명칭 정합성 확인
- 테스트 기준선 기록
  - 현재 기준: `pytest --collect-only -q tests` -> `3843 collected`

### 산출물

- 의존성 선언 mismatch 해소
- 실행 환경 문서 정합화
- 런타임 동작 변화 `0`
- 실행 검증
  - `python -m pytest tests/ -q` -> `3827 passed, 16 skipped, 1 warning`

### 비고

이 단계는 작아 보여도 중요하다.
지금 상태에선 코드 표면과 빌드/문서 표면이 다르기 때문에, 멀티 프로바이더보다 먼저 잡는 게 맞다.

---

### Phase 1. GeminiProvider 추상화 껍데기 추가

목표: 실제 동작은 Gemini 그대로 두고, 호출 경로만 추상화한다.

### 작업

- `modules/core/llm_provider.py` 신규
- `modules/core/llm_router.py` 신규
- `modules/core/providers/gemini_provider.py` 신규
- `modules/domain/agents/base_agent.py`
  - `ask()` 시그니처 불변
  - 내부 Gemini 호출을 `GeminiProvider.generate()` 로 위임

### 이 단계에서 지킬 것

- `BaseAgent.ask()` 외부 계약 불변
- `GOOGLE_API_KEY` 로테이션 로직 불변
- Context Caching 은 Gemini 전용으로 유지
- `models.yaml` 이 전부 Gemini면 결과 동작 동일

### 완료 기준

- BaseAgent 기반 에이전트 동작 불변
- 모델 SSOT 불변
- Google-only 운영 가능
- 실행 검증
  - `python -m pytest tests/test_llm_router.py tests/test_base_agent.py tests/test_agents.py tests/test_validation.py -q` -> `95 passed`
  - `python -m pytest tests/test_blueprint_preflight.py tests/test_satisfaction_framework.py -q` -> `34 passed`

---

### Phase 2. 스키마/직접 호출 경로 정리

목표: `BaseAgent 밖` 에 흩어진 Gemini 결합점을 정리한다.

### 왜 필요한가

현재 direct `generate_content()` 호출이 `21개 파일`에 있다.
즉 `base_agent.py` 만 정리해도 나머지 경로는 여전히 Gemini 직접 결합 상태다.

### 작업

- `modules/core/llm_schema.py` 신규
  - 내부 SSOT 는 `dict` 기반 JSON schema
  - Gemini/OpenAI/Anthropic 변환기는 어댑터로 분리
- `modules/core/response_schemas.py`
  - `types.Schema` 직접 정의를 내부 SSOT + 변환 호출 구조로 재편
- direct caller 정리
  - `modules/validation/advisory_validator.py`
  - `modules/validation/scoring_validator.py`
  - `modules/core/narrative_structure_analyzer.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/stage0/story_expander.py`
  - `modules/core/stage0/reverse_expander.py`
  - `modules/core/stage0/style_extractor.py`
  - `modules/domain/agents/analyst.py`
  - `modules/domain/agents/director_continuity.py`
  - `modules/domain/agents/manuscript_validator.py`
  - `modules/domain/agents/state_tracker_npc.py`
  - `modules/domain/agents/weaver.py`
  - `modules/domain/agents/writer.py`
  - 그 외 direct caller 계열

### 해석

이 단계가 실제 핵심이다.
문서상 난이도는 `response_schemas + 4 validator` 정도로 작아 보였지만, 현재 코드 기준 실제 범위는 더 넓다.

### 완료 기준

- 프로덕션 direct caller 가 provider abstraction 을 통과
- `types.Schema` 결합도가 눈에 띄게 낮아짐
- 여전히 기본 운영은 Gemini
- 실행 검증
  - direct `generate_content()` 호출면은 `BaseAgent/provider/example` 외 정리 완료
  - `python -m pytest tests/test_llm_router.py tests/test_llm_schema.py tests/test_base_agent.py tests/test_validation.py tests/test_agents.py tests/test_four_phase_arc_generator.py tests/test_nc3_checklist.py tests/test_pass_with_fix.py tests/test_blueprint_preflight.py tests/test_satisfaction_framework.py -q` -> `242 passed`
  - `python -m pytest tests/ -q` -> `3822 passed, 16 skipped, 1 warning`

---

### Phase 3. 멀티 프로바이더 등록만 추가

목표: 다른 provider 를 "쓸 수 있게만" 만들고, 기본값은 건드리지 않는다.

### 작업

- `modules/core/providers/anthropic_provider.py` 신규
- `modules/core/providers/openai_provider.py` 신규
- `config/models.yaml` 에 `providers:` 섹션 추가
- router prefix 규칙 추가
- 환경변수 이름만 정의
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`
  - Vertex AI 는 별도 프로젝트/리전/서비스계정 정의

### 이 단계에서 하지 않을 것

- Electron 설정창에 Anthropic/OpenAI 키 입력란 추가 안 함
- bridge/process_runner 에 provider-specific env 주입 추가 안 함
- 실제 agent 기본 모델 변경 안 함

### 완료 기준

- 설정만 하면 provider 인스턴스 생성 가능
- 하지만 기본 `models.yaml` 은 여전히 Gemini-only
- 실행 검증
  - `config/models.yaml` 에 `providers:` 섹션 추가 완료
  - `AnthropicProvider` / `OpenAIProvider` skeleton 추가 완료
  - shared router 경로로 `BaseAgent` / direct helper 정합화 완료
  - `python -m pytest tests/test_llm_router.py tests/test_base_agent.py tests/test_agents.py tests/test_validation.py tests/test_llm_schema.py -q` -> `103 passed`
  - `python -m pytest tests/ -q` -> `3827 passed, 16 skipped, 1 warning`

---

### Phase 4. opt-in 파일럿

목표: 실제 provider 사용은 `가벼운 비주권 경로` 에서만 시험한다.

### 권장 순서

1. `advisory_cheap` 또는 `self_critique` 같은 저위험 경로
2. 필요 시 `continuity_inspector`
3. `Director`, `Chief Writer`, `Analyst` 는 마지막

### 이유

- 지금 사용자는 당장 갈아탈 계획이 없다.
- 그러므로 1차 성공 기준은 "전환 가능 상태 확보" 이지 "즉시 타 프로바이더 운영" 이 아니다.
- 주권 에이전트를 먼저 옮기면 회귀 위험이 과하다.
- Vertex AI 자격증명이 있더라도, 현재 배치는 `provider 구현/활성화`가 아니라 `준비 상태 고정`까지만 한다.

### 완료 기준

- `models.yaml` 만 바꿔 opt-in 파일럿 가능
- 실패 시 Gemini로 즉시 롤백 가능
- 현재 상태
  - 외부 타 프로바이더 API 키 부재로 실제 opt-in 호출은 보류
  - `OpenAIProvider` config passthrough (`temperature/top_p/max_output_tokens/json schema`) 보강 완료
  - `AnthropicProvider` config passthrough (`temperature/top_p/system/max_tokens`) 보강 완료
  - `VertexAIProvider` 구현 완료, 기본값은 `disabled`
  - Vertex AI opt-in 모델은 `vertexai:gemini-2.5-pro` 같은 prefix로 Google API 경로와 공존
  - 따라서 Phase 4의 종료 조건은 `배선 준비 완료 + disabled 유지 + 문서화 완료`다

---

### Phase 4.5. Vertex AI readiness clarification

목표: `Vertex AI 계정 보유` 와 `글도비에서 Vertex AI 사용 가능` 을 명확히 구분한다.

### 현재 판정

- 사용자는 Vertex AI 자격증명을 갖고 있을 수 있다.
- 현재 코드베이스는 Google API 경로와 Vertex AI 경로를 함께 둘 수 있다.
- `modules/core/providers/vertex_provider.py` 구현, `project/location/credentials` 배선, prefix 라우팅이 완료됐다.
- 기본 설정은 여전히 `disabled` 이고, 주권 경로 기본 모델도 Gemini API 쪽에 남아 있다.
- 따라서 지금 상태의 Vertex AI 는 `실사용 준비 완료, 기본 비활성` 상태다.

### 후속 조건

1. `config/models.yaml` 에서 `providers.vertex_ai.enabled: true` 로 명시 활성화
2. 인증 입력(`VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `GOOGLE_APPLICATION_CREDENTIALS`) 실제 주입
3. opt-in 대상 모델을 `vertexai:gemini-2.5-pro` 같은 prefix 로 지정
4. Gemini-only 기준선 대비 회귀 테스트 통과 확인
5. 그 뒤에만 제한적 opt-in 파일럿 검토

### 비고

이 단계는 새로운 활성화 단계가 아니라 `오해 방지용 중간 고정선` 이다.

---

### Phase 5. 프론트엔드 / 브리지 확장 (선택)

목표: 사용자가 실제로 멀티 프로바이더를 앱에서 다뤄야 할 때만 UI 를 넓힌다.

### 현재 제약

- 설정 UI 는 `Gemini API Key` 만 노출
- `ProcessRunner._build_env()` 도 Google 키만 전달
- 따라서 지금은 멀티 프로바이더를 앱에서 조작할 수 없다

### 작업

- `geuldobi-desktop/src/index.html`
- `geuldobi-desktop/src/preload.js`
- `geuldobi-desktop/src/main.js`
- `modules/api/process_runner.py`
- 필요 시 bridge settings persistence 확장

### 비고

이 단계는 `지금 당장 필요 없음`.
backend-only 멀티 프로바이더 준비가 끝난 뒤, 실제 UI 요구가 생길 때만 한다.

---

## 6. 파일 변경 목록

### 반드시 선행

| 파일 | 작업 |
|------|------|
| `requirements.txt` | Google SDK 표기 정합성 확인 |
| `build/prepare_python_embed.ps1` | embedded Python 패키지 표기 정합성 확인 |
| `geuldobi-desktop/DESKTOP-GUIDE.md` | 개발/배포 가이드의 SDK 명칭 정합성 확인 |

### Phase 1

| 파일 | 작업 |
|------|------|
| `modules/core/llm_provider.py` | 신규 |
| `modules/core/llm_router.py` | 신규 |
| `modules/core/providers/gemini_provider.py` | 신규 |
| `modules/domain/agents/base_agent.py` | GeminiProvider 위임 |

### Phase 2

| 파일 | 작업 |
|------|------|
| `modules/core/llm_schema.py` | 신규 |
| `modules/core/response_schemas.py` | `types.Schema` 직접 결합 완화 |
| `modules/validation/*.py` | schema/provider 추상화 수용 |
| `modules/core/stage0/*.py` | direct caller 정리 |
| `modules/core/*validator*.py`, `modules/core/*analyzer*.py` | direct caller 정리 |
| `modules/domain/agents/*.py` 일부 | BaseAgent 밖 direct caller 정리 |

### Phase 3

| 파일 | 작업 |
|------|------|
| `modules/core/providers/anthropic_provider.py` | 신규 |
| `modules/core/providers/openai_provider.py` | 신규 |
| `config/models.yaml` | `providers:` 섹션 추가 |

### Phase 4.5

| 파일 | 작업 |
|------|------|
| `modules/core/providers/vertex_provider.py` | 신규 |
| `modules/core/llm_router.py` | `vertexai:` prefix 라우팅 및 provider 등록 |
| `modules/domain/agents/base_agent.py` | Vertex prefix 보존 fallback |
| `modules/core/metrics_collector.py` | Vertex prefix 비용 정규화 |
| `config/models.yaml` | `vertex_ai` 설정 블록 및 prefix 예시 추가 |

### Phase 5

| 파일 | 작업 |
|------|------|
| `geuldobi-desktop/src/index.html` | provider UI 확장 시에만 |
| `geuldobi-desktop/src/preload.js` | provider 설정 bridge 추가 시에만 |
| `geuldobi-desktop/src/main.js` | settings persistence 확장 시에만 |
| `modules/api/process_runner.py` | provider env 주입 시에만 |

---

## 7. 검증 게이트

### 최소 검증

- `pytest tests/test_base_agent.py -q`
- `pytest tests/test_config_manager.py -q`
- `pytest tests/test_validation.py -q`
- `pytest tests/test_process_runner.py tests/test_run_validator.py tests/test_risk_approval.py -q`
- `pytest --collect-only -q tests`

### 권장 검증

- direct caller 를 건드린 단계에서는 해당 모듈 타깃 테스트 추가
- provider activation 전에는 `frontend-backend-connection-check.md` 의 1차 기준선 유지
- provider activation 후에는 같은 문서로 2차 회귀 체크

### 현재 기준선

- `pytest --collect-only -q tests` -> `3847 collected`
- `pytest tests/ -q` -> `3831 passed, 16 skipped, 1 warning`
- 프론트엔드-백엔드 1차 연결 체크 -> `PASS`

---

## 8. 절대 하지 말 것

- `BaseAgent.ask()` 시그니처를 바꾸지 말 것
- 첫 배치에서 `Director`, `Chief Writer`, `Analyst` 기본 모델을 바꾸지 말 것
- 첫 배치에서 프론트엔드 provider UI 를 추가하지 말 것
- 첫 배치에서 임베딩/VecMemory 경로까지 함께 옮기지 말 것
- 외부 provider 비용표를 코드 상수로 먼저 박아 넣지 말 것
  - 비용은 실행 시점 공식 가격으로 별도 검증 후 반영
- `models.yaml` 의 기존 `agents.*` 키를 바꾸지 말 것

---

## 9. 최종 판정

이 명세는 현재 기준으로 `실행 문서 적합` 판정이다.

다만 실행 해석은 반드시 아래처럼 가져가야 한다.

1. `Gemini 유지` 가 기본값
2. `추상화` 가 1차 목표
3. `타 프로바이더 활성화` 는 후속 opt-in
4. `프론트엔드 변경` 은 더 뒤
5. `Vertex AI 보유` 와 `Vertex AI 기본 활성화` 는 같은 뜻이 아니다. 현재 배치는 실사용 준비까지만 끝냈다.

즉, 이 문서의 성공 정의는
`바로 Claude/OpenAI로 갈아타는 것`이 아니라
`갈아탈 준비를 끝내고도 지금은 Gemini로 안전하게 운영 가능한 상태`를 만드는 것이다.
