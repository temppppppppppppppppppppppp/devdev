# S4: LLM 통합 SSOT

> 최종 갱신: 2026-03-18
> 소스: llm-integration-deepdive, llm-deepdive corrections, 6-pass verdict, model-selection-report
> 감리: 6-pass adversarial (24 real issues: 2 HIGH, 11 MEDIUM, 11 LOW, 4 FALSE deleted)

---

## 1. 개관

글도비 v2의 LLM 통합은 `BaseAgent` 추상 클래스를 기반으로 47개 에이전트가 동작한다.
주 모델은 Gemini 2.5 Pro이며, 할당량 초과 시 Gemini 2.5 Flash로 자동 폴백한다.

### 1.1 아키텍처 구조

```
에이전트 (47개)
  └─ BaseAgent.ask()
       ├─ 프롬프트 조립 (directives + task + format)
       ├─ 크기 게이트 (MAX_CONTEXT_CHARS)
       ├─ 모델 스택 구성 + 쿼터 필터
       ├─ API 호출 (LLMRouter → Provider)
       ├─ 재시도 / 폴백 / 이어쓰기
       └─ 응답 반환 (원시 텍스트)
  └─ _extract_json_robust()     ← 모든 응답의 1차 JSON 파서
  └─ _ask_with_cached_context() ← 캐시 경로
```

### 1.2 에이전트-모델 매핑

| 티어 | 모델 | 에이전트 수 | 대표 에이전트 |
|------|------|------------|-------------|
| Pro | gemini-2.5-pro | 7-8개 | chief_writer, director, analyst, continuity_inspector, four_phase_arc_generator, blueprint_ensemble, three_phase_blueprint_generator, state_locked_arc_generator |
| Flash | gemini-2.5-flash | 10+개 | manager, block_enricher, preflight_checker, state_extractor, arc_corrector, arc_critic, consensus_validator, unified_arc_validator, unified_blueprint_validator, critic, weaver, writer |

**설정 소스**: `config/models.yaml` (`agents:` 섹션)에서 에이전트별 모델 지정. `_get_agent_default_model()` 함수가 snake_case 에이전트 키로 조회.

### 1.3 프로바이더 구조

| 프로바이더 | 상태 | 경로 |
|-----------|------|------|
| Gemini (google-genai) | **프로덕션 사용 중** | `modules/core/providers/gemini_provider.py` |
| OpenAI | 코드 존재, 미검증 | `modules/core/providers/openai_provider.py` |
| Anthropic | 코드 존재, 미검증 | `modules/core/providers/anthropic_provider.py` |

**라우팅**: `llm_router.py`가 모델명 접두사로 프로바이더 결정. `claude-*` → anthropic, `gpt-*` → openai, 나머지 → gemini.

---

## 2. BaseAgent 내부

### 2.1 Core ask() 파이프라인

**위치**: `base_agent.py` L592-860

```
ask(prompt, temperature=0.5, response_schema=None, thinking_level=None)
  1. 이전 상태 초기화 (last_partial_response, usage_tracking)
  2. 프롬프트 조립: directives + task + format
  3. 크기 게이트 적용 (_apply_prompt_size_gate)
  4. API 키 순환 체크 (이전 429 발생 시)
  5. 모델 스택 구성 (_build_model_stack)
  6. 메인 루프 (MAX_CONTINUATIONS=5):
     a. API_DELAY 대기 (기본 0.1초)
     b. _generate_content() 호출
     c. 에러 시 → _handle_api_error() (네트워크/Rate Limit/쿼터 분기)
     d. 응답 추출 + 병합 + 이어쓰기 판정
  7. 비용 추적 종료
  8. DB 로깅
  9. 원시 텍스트 반환 (JSON 파싱 없음)
```

**핵심 특성**:
- `ask()`는 원시 텍스트를 반환한다. JSON 파싱은 호출자가 `_extract_json_robust()`를 직접 호출하여 수행한다 (60+ 호출부 확인).
- 연속 응답(이어쓰기) 최대 5회 + 백업 모델 1회 = **최대 6회 API 호출** (원본 보고서의 10회 주장은 오류로 교정됨).

### 2.2 모델 config & 폴백 체인

**위치**: `base_agent.py` L49-54, L930-1013

```python
DEFAULT_MODEL_FALLBACK_CHAIN = {
    "gemini-2.5-pro": "gemini-2.5-flash",
    "gemini-2.5-flash": "gemini-2.5-flash",  # 자기참조
}
```

**폴백 체인 동작**:
1. `_build_model_stack()` (L936-943)에서 model_stack 구성
2. `self.backup_model != self.primary_model` 조건으로 **자기참조 중복 제거** (L938)
3. primary가 flash이면 model_stack = `[flash]` 단일 → `max_quota_retries = 1` → 0 < 0 = False → 즉시 "all fallbacks exhausted"
4. **순환 무한루프 불가능** (6-pass 검증 완료)

**YAML 오버라이드**: `config/models.yaml`의 `fallback_chain:` 섹션이 하드코딩보다 우선.

### 2.3 API 키 회전

**위치**: `base_agent.py` L184-269

| 항목 | 값 | 소스 |
|------|-----|------|
| 키 로드 | `GOOGLE_API_KEY`, `GOOGLE_API_KEY_2`, ... (최대 10개) | 환경변수 |
| 최소 쿨다운 | 10초 (`_MIN_ROTATION_INTERVAL`) | system.yaml |
| Lock | `_rotation_lock` (RLock, 재진입 허용) | 클래스 변수 |
| 연속 회전 카운터 | `_rotation_count` | primary 성공 시 리셋 (L670-672) |

**키 회전 절차**:
1. `_key_rotation_pending = True` 시 `ask()` 진입부에서 `_try_rotate_key()` 호출
2. Lock 내에서 키 인덱스 캡처 → Lock 해제 → Client 생성 (capture-then-release 패턴)
3. 실패 시 이전 키로 롤백

**[HIGH] 모든 키 소진 시**: `_rotation_count >= len(api_keys) - 1` → `return None` → 호출부에서 기존 키 유지, **WARNING 로그 없음** (L224-226). 운영자에게 키 소진 사실이 전달되지 않음.

```python
# base_agent.py L224-226
if cls._rotation_count >= len(cls._api_keys) - 1:
    cls._key_rotation_pending = False
    return None  # ← 경고 로그 없음
```

### 2.4 프롬프트 크기 게이트

**위치**: `base_agent.py` L306-326

```python
def _apply_prompt_size_gate(self, prompt: str) -> str:
    max_chars = int(self.MAX_CONTEXT_CHARS or 0)
    if len(prompt) <= max_chars:
        return prompt
    notice = "\n\n[System Note] Prompt truncated by safety gate..."
    keep = max(0, max_chars - len(notice))
    clipped = prompt[:keep] + notice
    logging.warning("[TF3-H7] Prompt length gate applied: %d -> %d chars...",
        len(prompt), len(clipped), self._agent_name)
    self.requires_human_intervention = True
    return clipped
```

**동작**:
- 문자 수 기반 절단 (토큰 수 아님)
- 앞부분 보존, 뒷부분 삭제
- `logging.warning()` 발생 + `requires_human_intervention = True` 설정
- 원본 보고서의 "무경고 절단" 주장은 **오류** — 경고 있음 (6-pass 교정)

**제한사항**: 한국어 멀티바이트 특성상 문자 수와 토큰 수 불일치. 호출자 중 `requires_human_intervention` 플래그를 검사하지 않는 경로 존재.

### 2.5 Thinking Budget 맵

**위치**: `base_agent.py` L153-156

```python
THINKING_BUDGET_MAP = {
    "minimal": 1024,
    "low": 4096,
    "medium": 8192,
    "high": 16384,
    "maximum": 24576
}
```

**동작**: `system.yaml`에서 오버라이드 가능. 문자열 레벨 → 정수 변환. 오타 레벨 (예: `"medimu"`) 시 기본값 8192로 무경고 폴백 (L984).

**적용 경로**: `ask()` L981-987, `_ask_with_cached_context()` L2015-2020 — 둘 다 `ThinkingConfig(thinking_budget=budget, include_thoughts=True)` 생성.

### 2.6 Temperature & 샘플링

**위치**: `base_agent.py` L969-974

```python
config_params = {
    "temperature": temperature,       # ask() 기본값 0.5
    "max_output_tokens": self.MAX_OUTPUT_TOKENS,  # system.yaml, 기본 8192
    "top_p": 0.95,                    # 하드코딩
    "response_mime_type": "application/json",
}
```

| 파라미터 | 값 | 설정 가능 여부 |
|---------|-----|-------------|
| temperature | 0.5 (ask 기본), 0.3 (_ask_with_cached_context 기본) | 호출 시 전달 |
| top_p | 0.95 | **하드코딩** (4곳: L972, L1181, L1342, L2006) |
| top_k | 미노출 | 설정 불가 |
| frequency_penalty | 미노출 | 설정 불가 |
| max_output_tokens | 8192 (기본) | system.yaml |

**Temperature 기본값 차이**:
- `ask()`: 0.5 (L592)
- `_ask_with_cached_context()`: 0.3 (L1967)
- 6-pass 검증 결과: **모든 호출부가 명시적 temperature를 전달**하므로 기본값 차이는 실제 발현하지 않음 → LOW

---

## 3. 응답 처리

### 3.1 5단계 JSON 추출 파이프라인

**위치**: `base_agent.py` L1670-1793

`_extract_json_robust()`는 `ask()` 반환값에 대한 **모든 응답의 유일한 JSON 파서**이다. 60+ 호출부에서 직접 호출됨. "최후수단 파서"가 아님 (1차 교정 보고서의 오류, 6-pass에서 정정).

| 단계 | 처리 | 세부 |
|------|------|------|
| 0. 크기 게이트 | 500KB 초과 시 절삭 (L1680-1682) | `_MAX_JSON_PAYLOAD` = system.yaml 설정, 기본 500,000 |
| 1. 괄호 자동 닫기 | `{` > `}` 시 `}` 추가 (L1685-1688) | 홀수 따옴표도 보정 |
| 2. 마크다운 제거 | ` ```json ``` ` 스트립 (L1695) | 정규식 치환 |
| 3. JSON 블록 추출 | `(\{.*\}\|\[.*\])` greedy 매칭 (L1696-1698) | 첫 번째 매칭만 캡처 |
| 4. 2단계 파싱 | `json.loads(strict=False)` → `ast.literal_eval` (L1701-1707) | strict=False: 제어문자 허용 |
| 5. 재귀 평탄화 | 100노드 방문 제한, 깊이 20 제한 (L1740-1790) | 순환 참조 감지 (`seen_ids`) |

**파싱 실패 폴백 순서**:
1. `_parse_and_repair_hard()` — Hard Repair
2. 정규식: `tactical_doc` 필드 추출
3. 정규식: `content` 필드 추출
4. 정규식: `scene_breakdown` 필드 추출
5. 정규식: `integrated_scenario` 필드 추출
6. 최종: `{"parsing_error": True, "content": text, "status": "RAW_TEXT_ONLY"}`

### 3.2 Hard Repair

**위치**: `base_agent.py` L1795-1837

```python
def _parse_and_repair_hard(self, json_str) -> dict:
    # 괄호 보정
    processed = re.sub(r":\s*null\b", ": None", json_str)
    processed = re.sub(r":\s*true\b", ": True", processed)
    processed = re.sub(r":\s*false\b", ": False", processed)
    return ast.literal_eval(processed)
```

**치환 규칙**: `null` → `None`, `true` → `True`, `false` → `False`

**실패 시**: 2-pass 정규식으로 키-값 쌍 추출
- Pass 1: 문자열 값 (`"key": "value"`)
- Pass 2: 숫자, 불리언, null

**최종 실패**: `{"content": json_str, "status": "REPAIRED_RAW"}` — 타입이 변경됨 (예상 구조와 다른 dict)

### 3.3 ast.literal_eval (안전)

**위치**: `base_agent.py` L1706, L1807

- `ast.literal_eval`은 리터럴만 평가 — `eval()`/`exec()`이 아니므로 **코드 실행 위험 없음** (6-pass 보안 전수 조사 확인)
- Hard Repair에서 JSON → Python 리터럴 변환 후 사용

### 3.4 response_schema 강제 (Gemini JSON 모드)

**위치**: `base_agent.py` L972-978

```python
config_params["response_mime_type"] = "application/json"
if response_schema:
    config_params["response_schema"] = response_schema
```

**동작**: Gemini API가 `response_schema`에 맞는 JSON만 생성하도록 강제. 이 API 수준 타입 강제가 `json.loads(strict=False)`의 NaN/Infinity 허용 리스크를 실질적으로 차단함.

**스키마 정의**: `modules/core/response_schemas.py`에서 `google.genai.types.Schema` 객체로 정의. `get_schema_for_task()` 함수로 작업 유형별 스키마 조회.

---

## 4. 토큰 추적 → S7 참조

토큰 카운팅과 비용 추적은 `MetricsCollector` (싱글턴, `modules/core/metrics_collector.py`)가 담당한다. S7 (메트릭/관측성 SSOT)에서 상세 기술.

**BaseAgent와의 접점**:

| 접점 | 위치 | 설명 |
|------|------|------|
| `_build_metric_usage_payload()` | L417-448 | usage dict → 메트릭 페이로드 변환 |
| `_accumulate_last_llm_usage()` | L406-415 | 연속 호출 시 usage 누적 |
| `_coerce_usage_int()` | L394-400 | 안전한 정수 변환 |
| 추정 폴백 | L434-436 | API 실측값 없을 때 → `estimate_tokens()` 사용 |

**usage 키 이름**: Gemini 기준 (`prompt_token_count`, `candidates_token_count`, `cached_content_token_count`, `thoughts_token_count`). OpenAI 프로바이더 사용 시 키 불일치로 토큰 카운트 0 → 추정 폴백 (MEDIUM 이슈).

**추정 함수** (`metrics_collector.py` L274-290):
```python
korean_chars = sum(1 for c in text if "가" <= c <= "힣")
other_chars = len(text) - korean_chars
return int(korean_chars / 1.5 + other_chars / 4)
```
- 자모(`ㄱ-ㅎ`, `ㅏ-ㅣ`) 미포함
- 실제 Gemini 토크나이저와 ±30% 오차
- **실패 호출에서만 사용** — 성공 시 API 실측값 우선 (L434-436 조건)
- 6-pass 교정: 원본 HIGH → **LOW** (실패 한정 폴백이므로)

---

## 5. 컨텍스트 캐시

### 5.1 Config

**위치**: `base_agent.py` L1864-1867

| 설정 | 값 | 소스 |
|------|-----|------|
| 최소 캐시 크기 | 50,000자 (`_MIN_CACHE_CONTENT`) | system.yaml `cache.min_content_chars` |
| 최대 엔트리 | 50 (`_CONTEXT_CACHE_MAX`) | system.yaml `cache.context_max_entries` |
| TTL | 30분 (1800초, 기본값) | `_get_or_create_context_cache()` 파라미터 |
| 해시 알고리즘 | MD5, truncated 16자 | L1894 |
| Lock | `_cache_lock` (threading.Lock) | L1865 |
| 제거 정책 | 생성 시각 기준 FIFO (접근 시각 아님) | L1943 |

### 5.2 Cache Key 구성

**위치**: `base_agent.py` L1894-1895

```python
content_hash = hashlib.md5(content.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]
cache_key = f"{cache_type}_{project_name}_{content_hash}"
```

**격리 메커니즘**: `cache_key`에 `content_hash`가 포함 → 동일 네임스페이스라도 **다른 콘텐츠면 다른 키** → 실질적 프로젝트 간 캐시 오염 불가.

50 엔트리에서 MD5 16자(64비트) 충돌 확률: ~3.4e-17 (실질 무의미).

### 5.3 Namespace 폴백 체인

**위치**: `base_agent.py` L1848-1862

```python
project_token = (
    _sanitize(work_id)           # 1순위: work_id
    or _sanitize(name)           # 2순위: name
    or _sanitize(project_name)   # 3순위: project_name
    or _sanitize(genre)          # 4순위: genre
    or "default"                 # 5순위: 리터럴 "default"
)
```

**`_sanitize_context_cache_token(None)` 동작**:
```python
@staticmethod
def _sanitize_context_cache_token(value: object) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", str(value or "")).strip("_.")
```
- `value=None` → `value or ""` → `""` → regex → `""` → strip → `""` (빈 문자열)
- 빈 문자열은 falsy → `or` 체인에서 다음 후보로 이동
- 원본 보고서의 `None→"none"` 주장은 **FALSE** (6-pass 확정 삭제)

### 5.4 Gemini Context Caching API 연동

**위치**: `base_agent.py` L1922-1930

```python
cache = self.client.caches.create(
    model=self.primary_model,
    config=types.CreateCachedContentConfig(
        contents=[{"role": "user", "parts": [{"text": content}]}],
        ttl=f"{ttl_seconds}s",
        display_name=f"{cache_type}_cache_{project_name}",
    ),
)
```

- 캐싱 실패 시 에러를 잡아 캐시 없이 진행 (L1951-1961)
- 429/quota 에러 시 `_key_rotation_pending = True` 예약 (L1957-1958)
- 응답 캐싱(동일 프롬프트 재호출 시)은 미구현 — 매번 새로 생성

---

## 6. 응답 스키마 (response_schemas.py)

**위치**: `modules/core/response_schemas.py` (912행)

### 6.1 anyOf 패턴 — 5곳 (HIGH)

| # | 위치 | 필드 | anyOf 타입 |
|---|------|------|-----------|
| 1 | L518-546 | `BLUEPRINT_SCENE_ENTRY_SCHEMA` | OBJECT \| STRING |
| 2 | L528-532 | `characters` 필드 | STRING \| ARRAY |
| 3 | L534-538 | `key_events` 필드 | STRING \| ARRAY |
| 4 | L572-576 | `equipment` 필드 | STRING \| ARRAY |
| 5 | L585-596 | `timeline` 필드 | STRING \| OBJECT |

**영향**: Gemini가 비결정적으로 string 또는 object/array를 반환. 하류 소비자가 타입을 가정하면 런타임 오류.

**현재 방어 현황** (6-pass 전수 조사):
- **isinstance 가드 있음 — 13곳**: `blueprint_ensemble.py` L246/L866/L1094, `director_continuity.py` L288, `stage4_interview_round.py` L646/L726, `stage3_orchestrator.py` L1932, `stage4_context_builder.py` L199, `chief_writer_context.py` L367, `stage0_handoff.py` L121, `confidence_calibration.py` L251, `state_service.py` L363, `three_phase_blueprint_generator.py` L334
- **약한 가드 — 1곳**: `confidence_calibration.py` L256 — `or []` 패턴으로 string 시 글자 단위 순회 가능

**심각도**: **HIGH** — 현재 방어는 양호하나, 신규 소비자 추가 시 isinstance 가드 누락 리스크 지속. 유지보수 부담.

### 6.2 스키마 라운드트립 손실

- `schema_to_dict()` (`llm_schema.py`): Gemini `types.Schema` → dict 변환
- `to_gemini_schema()` (`llm_schema.py`): dict → Gemini `types.Schema` 역변환
- **라운드트립 시 손실 가능 항목**: enum 순서, description, 정수 min/max 제약
- `_TASK_SCHEMA_SPECS` (L662): 시작 시 dict 캐시 생성 (`schema_to_dict()` 1회 호출)

### 6.3 프로바이더 제한사항

| 프로바이더 | 구조화 출력 | 비고 |
|-----------|-----------|------|
| Gemini | `response_mime_type` + `response_schema` | **현행 사용** |
| OpenAI | Structured Outputs / JSON Mode | 코드 존재, 스키마 전달 시 `minimum`/`maximum` 제약 누락 |
| Anthropic | Tool use 강제 패턴 | `response_schema` 파라미터 없음 |

---

## 7. 동시성

### 7.1 Lock 순서 및 역할

| Lock | 타입 | 보호 대상 | 위치 |
|------|------|-----------|------|
| `_rotation_lock` | RLock (재진입) | API 키 회전 상태, _key_rotation_pending, _rotation_count | L191 |
| `_quota_lock` | Lock | _quota_exhausted_models | L172 |
| `_cache_lock` | Lock | _context_caches | L1865 |

**Lock 순서**: rotation → quota → cache (교착 없음, 6-pass 검증)

**capture-then-release 패턴**: `_rotation_lock` 내에서 키 인덱스를 캡처하고 Lock 해제 후 Client 생성. 원본 보고서의 "TOCTOU" 주장은 **FALSE** — 코드에 명시적 주석 존재 (L249-250), `_key_rotation_pending` 단발 플래그로 동시 진입 차단.

### 7.2 ThreadPoolExecutor (앙상블)

**위치**: `blueprint_ensemble.py` L300-370

- 3개 스레드가 동시에 전략별 Blueprint 생성
- `hud_context`는 Python 문자열 (immutable) → 스레드 간 변경 불가
- 원본 보고서의 "방어적 복사 필요" 주장은 **FALSE** (6-pass 확정 삭제)

### 7.3 MetricsCollector 스레드 안전성

- `threading.Lock()` 보호 확인
- `_agent_durations` 500개 상한, `_context_caches` 50개 상한
- 무한 메모리 증가: **안전** (6-pass 보안 전수 조사)

---

## 8. 모델 선정 보고서 핵심

**소스**: `geuldobi-v2-llm-model-selection-report.md` (5Pass 보강판, 확신도 86%)

### 8.1 시스템 요구사항 (MUST)

| 요구사항 | 현행값 | 근거 |
|----------|--------|------|
| 컨텍스트 윈도우 | 1,000,000자 (≈500K-700K 토큰) | `validation.yaml` L75 |
| 최대 출력 토큰 | 65,536 토큰 | `system.yaml` L18 |
| 구조화 출력 (JSON) | 필수 — `response_mime_type: application/json` | `base_agent.py` L972 |
| 컨텍스트 캐싱 | 50,000자 이상 시 활성, 5개 에이전트 적용 | `system.yaml` L36-40 |
| 동시 요청 | 8-9개 병렬 (Advisory Chain) | `stage4_interview_round.py` L2330 |
| API 타임아웃 | 300초 (5분) | `system.yaml` L17 |
| 확장 추론 (Thinking) | 1,024~24,576 토큰 예산 | `system.yaml` L7-12 |
| 폴백 체인 | pro → flash 자동 전환 | `models.yaml` L47-49 |

### 8.2 비용 비교 (토크나이저 보정 포함)

| 모델 | Input $/MTok | Output $/MTok | 캐시 읽기 | 배치 할인 |
|------|-------------|--------------|-----------|-----------|
| Claude Opus 4.6 | $5.00 | $25.00 | $0.50 (0.1x) | 50% |
| Claude Sonnet 4.6 | $3.00 | $15.00 | $0.30 (0.1x) | 50% |
| GPT-5.4 | $2.50 | $15.00 | $0.25 (0.1x) | 50% |
| Gemini 2.5 Pro | $1.25 | $10.00 | $0.125 (0.1x) | 50% |
| Gemini 2.5 Flash | $0.30 | $2.50 | $0.03 (0.1x) | 50% |

**한국어 토크나이저 효율** (비용에 직결):

| 모델 계열 | chars/token | 5,000자 → 토큰 수 |
|-----------|------------|-------------------|
| DeepSeek | ~2.02 | ~2,475 |
| Qwen | ~1.5-1.8 | ~2,800-3,300 |
| Claude | ~1.25 | ~4,000 |
| GPT | ~1.0-1.2 | ~4,200-5,000 |
| Gemini | ~0.82 | ~6,100 |

> Gemini는 동일 5,000자 한국어에 ~6,100 토큰을 소비 (Claude 대비 ~1.53x). 표면 단가만으로 비교 불가.

### 8.3 품질 벤치마크

**Mazur Writing Benchmark V4** (영어 단편, 10개 필수 요소 + 18개 루브릭):

| 순위 | 모델 | 점수 |
|------|------|------|
| 1 | Claude Opus 4.6 Thinking | 8.56 |
| 2 | **Claude Opus 4.6** | **8.53** |
| 3 | GPT-5.2 | 8.51 |
| 9 | **Gemini 2.5 Pro** | **8.22** |
| 21 | DeepSeek V3.2 | 7.60 |
| 30 | Llama 4 Maverick | 5.78 |

**EQ-Bench Creative Writing v3** (Elo 기반):

| 모델 | Elo |
|------|-----|
| Claude Sonnet 4.6 | 1936 |
| Claude Opus 4.6 | 1932 |

**LM Arena Overall Text** (2026-03-05):

| 순위 | 모델 | Elo |
|------|------|-----|
| 1 | Claude Opus 4.6 | 1504 |
| 2 | Gemini 3.1 Pro Preview | 1500 |
| 3 | Claude Opus 4.6 Thinking | 1500 |

**한국어 창작 벤치마크**: **부재**. KMMLU, KoBEST, CLIcK, HAE-RAE, KoBALT, LogicKor 전수 조사 결과 모두 NLU/교육 평가이며 문학적 창작 품질은 미측정.

**커뮤니티 합의** (DC Inside AI소설 마이너갤러리):
- 물량/비용 기준: Gemini 1위 ("한국어 감성을 잘 살림", "번역체 제일 적음")
- 윤문/품질 기준: Claude 만장일치 1위 ("윤문 능력 최강")

### 8.4 한국어 특수 요구사항

- **경어/반말 체계**: 존댓말/반말/해요체/하십시오체 — 캐릭터 관계에 따른 일관성 필수
- **의성어/의태어**: 한국어 서사에 필수적 (단일 코퍼스에서 의성어 82개, 의태어 164개)
- **번역체 (translationese)**: Gemini가 가장 적고, Claude/GPT는 프롬프팅으로 완화 가능

### 8.5 Rate Limits

| 프로바이더 | TPM | 비고 |
|-----------|-----|------|
| Gemini | **4M TPM** | 티어 없음, 유료 즉시 |
| OpenAI | 800K TPM | 티어별 차등 |
| **Claude** | **80K TPM** (기본) → 400K (Tier 4, $400+) | **가장 제한적** |

**글도비 영향**: 8-9개 병렬 Advisory Chain에서 Claude 80K TPM 기본 한도가 병목 가능. Enterprise 티어 또는 AWS Bedrock 경유 필요.

### 8.6 250화 비용 추정

| 시나리오 | 직접 비용 (배치) | 숨겨진 비용 | 합계 |
|---------|----------------|-----------|------|
| **A: Opus + Flash** | $133-310 | +$70-77 | **$203-387** |
| **B: 현행 + ChiefWriter만 Opus** | $90-120 | +$40-45 | **$130-165** |
| **C: 현행 유지 (Gemini Pro + Flash)** | $39-101 | +$29-32 | **$68-133** |

**숨겨진 비용 항목**: Thinking 토큰 (출력 단가 과금), JSON 스키마 오버헤드 (23회/에피 x 600토큰), 리트라이 비용.

**Gemini implicit caching 주의**: 보고서 원본의 "90% CONFIRMED"는 할인율이며 적중률이 아님. 실제 적중률 40-60% 불안정 (GitHub googleapis/python-genai#1880).

---

## 9. 수치 요약표

### 9.1 BaseAgent 핵심 상수

| 상수 | 값 | 소스 | 위치 |
|------|-----|------|------|
| `MAX_OUTPUT_TOKENS` | 8192 | system.yaml `api.max_output_tokens` | L176 |
| `MAX_CONTEXT_CHARS` | ContextLimits.MAX_CONTEXT_CHARS | validation.yaml | L182 |
| `API_DELAY` | 0.1초 | system.yaml `api.delay` | L179 |
| `MAX_CONTINUATIONS` | 5 | 하드코딩 | L640 |
| `MAX_RATE_LIMIT_RETRIES` | 3 | 하드코딩 | L647 |
| `MAX_NETWORK_RETRIES` | 22 | system.yaml | 클래스 변수 |
| `NETWORK_RETRY_DELAY_BASE` | 10초 | system.yaml | 클래스 변수 |
| `NETWORK_RETRY_DELAY_MAX` | 30초 | system.yaml | 클래스 변수 |
| `_QUOTA_CACHE_DURATION` | 3600초 | system.yaml `api.quota_cache_duration` | L173 |
| `_MIN_ROTATION_INTERVAL` | 10초 | system.yaml `key_rotation.min_interval` | L190 |
| `_CONTEXT_CACHE_MAX` | 50 | system.yaml `cache.context_max_entries` | L1866 |
| `_MIN_CACHE_CONTENT` | 50,000자 | system.yaml `cache.min_content_chars` | L1867 |
| `_MAX_JSON_PAYLOAD` | 500,000자 | system.yaml `retry.max_json_payload` | L1666-1668 |

### 9.2 에러 분류 체계

| 에러 유형 | 상수 | 감지 방법 |
|-----------|------|-----------|
| timeout | `AgentErrorType.TIMEOUT` | "timeout", "timed out", "deadline" in error_str |
| quota_exceeded | `AgentErrorType.QUOTA_EXCEEDED` | "resource_exhausted" 또는 "quota" (429 미포함) |
| network_error | `AgentErrorType.NETWORK_ERROR` | "connection", "ssl", "socket" 등 |
| schema_incompatible | `AgentErrorType.SCHEMA_INCOMPATIBLE` | 스키마 불일치 전용 |
| malformed_response | `AgentErrorType.MALFORMED_RESPONSE` | 응답 파싱 실패 |
| unknown | `AgentErrorType.UNKNOWN` | 위 모두 아닐 때 |

### 9.3 재시도 전략

| 에러 유형 | 최대 재시도 | 백오프 | 모델 전환 |
|-----------|------------|--------|-----------|
| Network | 22회 | 10s + 5s*n, cap 30s | 없음 |
| Rate Limit (429+rate/limit) | 3회/모델 | 30s, 60s, 90s | 소진 시 fallback |
| Ambiguous 429 | Rate Limit으로 처리 | 동일 | 동일 |
| Quota (resource_exhausted) | 즉시 전환 | 없음 | 다음 모델 |
| Timeout | retry 내 처리 | 동일 | 없음 |

### 9.4 Thinking Budget 맵

| 레벨 | 토큰 예산 |
|------|----------|
| minimal | 1,024 |
| low | 4,096 |
| medium | 8,192 |
| high | 16,384 |
| maximum | 24,576 |

### 9.5 스키마 타입 인벤토리

| 스키마 | 용도 | required 필드 |
|--------|------|-------------|
| BLOCKING_RESULT_SCHEMA | 차단 검증 | tier, passed, failures, message |
| SCORING_RESULT_SCHEMA | 채점 검증 | tier, passed, total_score, breakdown |
| ADVISORY_RESULT_SCHEMA | 자문 검증 | tier, passed, suggestions |
| DIRECTOR_AUDIT_SCHEMA | 원고 감사 | decision, score, reason, fix_scope |
| STRATEGIC_AUDIT_SCHEMA | 전략 감사 | decision, score, loop_detected, reason, fix_scope |
| CHARACTER_LOGIC_SCHEMA | 캐릭터 논리 | decision, score, violations, severity |
| BLUEPRINT_SCHEMA | 설계도 | episode_number, scene_breakdown, integrated_scenario |
| MANUSCRIPT_SCHEMA | 원고 | content |
| ARC_DESIGN_SCHEMA | Arc 설계 | arc_no, ep_count, ep_start, ep_end, title, beat_sequence, tactical_doc |
| BLUEPRINT_PREFLIGHT_SCHEMA | 설계도 사전검증 | passed, issues, summary |

---

## 10. 발견 사항

### 10.1 HIGH (2건)

| ID | 이슈 | 파일 | 라인 | 코드 근거 | 6-Pass |
|----|------|------|------|-----------|--------|
| **H1** | anyOf 스키마 설계 (5곳) — 모든 소비자에 isinstance 방어 부담 전가. 13곳 가드 있으나 신규 소비자 누락 리스크 지속 | response_schemas.py | L518, L528, L534, L572, L585 | `anyOf=[OBJECT, STRING]` 5곳 | 6/6 |
| **H2** | API 키 전체 소진 시 무경고 — `return None` 후 기존 키 유지, 로그·경고 없음 | base_agent.py | L224-226 | `return None` — WARNING 로그 없음 | 5/6 |

### 10.2 MEDIUM (11건)

| ID | 이슈 | 파일 | 라인 | 요약 |
|----|------|------|------|------|
| **M1** | 캐시 키 장르 폴백 — content_hash가 2차 격리 제공하여 실질 오염 불가 | base_agent.py | L1848-1862, L1895 | 설계 개선 권고 (work_id 필수화) |
| **M2** | protagonist_name 포맷팅 불일치 — writer.py에서 `_escape_braces()` 미적용 (다른 에이전트는 적용) | writer.py | L166 | 보안 취약점이 아닌 데이터 무결성 리스크 |
| **M3** | 프롬프트 절단 — 경고 있으나 로그 수준. 문자 기반 절단(토큰 아님) | base_agent.py | L306-326 | `logging.warning()` + `requires_human_intervention=True` |
| **M4** | 연속 호출 최대 6회 비용 — MAX_CONTINUATIONS=5 + backup 1회 | base_agent.py | L640, L1317 | 원본 10회 주장은 오류 |
| **M5** | PASS_WITH_FIX 실패 → REJECT+부분채택 — `verdict="REJECT"` 설정 후 외부 루프 계속 | three_phase*.py | L625-645 | L631에서 부분 수정본이 best_blueprint에 채택 |
| **M6** | finish_reason 과도한 except — `except Exception: finish_reason="stop"` | gemini_provider.py | L24-30 | SAFETY/RECITATION → "stop"으로 위장 |
| **M7** | Safety 필터 → 빈 응답 — 빈 정상 응답과 구분 불가 | gemini_provider.py | L18-22 | `except (AttributeError, ValueError): text=""` |
| **M8** | OpenAI usage 키 불일치 — Gemini 키 기준 코드이므로 OpenAI 시 추정 폴백 | base_agent.py | L276-281 | `prompt_token_count` ≠ `prompt_tokens` |
| **M9** | 비용 예산 한도 미집행 — 비용 계산만, max budget 비교 없음 | metrics_collector.py | L256-269 | 예산 초과 미감지 |
| **M10** | 시스템 설정 런타임 불변 — 모듈 임포트 시 1회 로드, 런타임 변경 반영 안 됨 | base_agent.py | L149 | `_SYSTEM_CFG = _load_system_config()` |
| **M11** | 실패 시 전체 응답 DB 기록 — 성공: 미기록, 실패: 응답 전문 (길이 제한 없음) | base_agent.py | L537-538 | 민감한 소설 내용 포함 가능 |

### 10.3 LOW (11건)

| ID | 이슈 | 파일 | 라인 | 요약 |
|----|------|------|------|------|
| **L1** | `_last_thinking` 미리셋 (로그용) — ask() 진입 시 리셋 없으나 진단/로깅 전용 | base_agent.py | L302, L832 | 생성 로직 미사용. 성공 시 정상 덮어쓰기 |
| **L2** | `json.loads(strict=False)` — 제어문자 허용이 주효과. Gemini JSON 모드가 NaN 방지 | base_agent.py | L1703 | 모든 응답의 1차 파서 |
| **L3** | 폴백 체인 자기참조 (flash→flash) — `_build_model_stack()` 중복제거로 무한루프 방지 | base_agent.py | L51-54, L938 | `backup_model != primary_model` 조건 |
| **L4** | 제약 캐시 재사용 (입력 불변) — 재시도 루프 내 입력 불변이므로 stale 미발생 | three_phase*.py | L196-212 | `arc_data`/`prev_blueprint` 불변 |
| **L5** | Temperature 기본값 차이 (0.5 vs 0.3) — 모든 호출부가 명시적 전달, 미발현 | base_agent.py | L592, L1967 | 기본값 차이 실 경로 없음 |
| **L6** | 토큰 추정 ±30% (실패 한정 폴백) — 성공 시 API 실측값 사용 | metrics_collector.py | L274-290 | 비용 보고 정확도에만 영향 |
| **L7** | 배치 검증 부분 실패 — `asyncio.gather(return_exceptions=True)`, 읽기전용 | batch_validator.py | L80-94 | 하위 orchestrator 의존 |
| **L8** | top_p 0.95 하드코딩 — 4곳 반복, 설정 불가 | base_agent.py | L972, L1181, L1342, L2006 | 외부 설정 미노출 |
| **L9** | 캐시 MD5 16자 — 50 엔트리에서 충돌 확률 ~3.4e-17 | base_agent.py | L1894 | 실질 무의미 |
| **L10** | 오버랩 100자 cap — 연속 응답 앵커 매칭. 100자 이상 오버랩은 극히 드뭄 | base_agent.py | L1255-1265 | 합리적 상한 |
| **L11** | 앙상블 첫 후보 대표 반환 — 전체 후보 목록도 함께 반환, Director가 최종 선택 | blueprint_ensemble.py | L398-450 | 의도적 설계 |

### 10.4 FALSE (삭제 확정, 4건)

| ID | 원본 주장 | FALSE 근거 | 6-Pass |
|----|----------|-----------|--------|
| **F1** | f-string 이중 해제 (§10.2) | Python f-string은 변수 치환값 내 `{{`를 해제하지 않음 | 4/6 |
| **F2** | `_sanitize(None)→"none"` (§7.2) | `None or ""` → `""` (빈 문자열). `"none"` 아님 | 6/6 |
| **F3** | `_rotation_lock` TOCTOU (§16.1) | capture-then-release 패턴 + `_key_rotation_pending` 단발 플래그 | 5/6 |
| **F4** | `hud_context` 방어적 복사 필요 (§16.2) | `hud_context`는 Python 문자열 (immutable). 스레드 간 변경 불가 | 6/6 |

---

## [부록 A] 6-Pass 감리 이력

### 감리 단계 진행 경과

| 단계 | 문서 | 에이전트 | tool uses | 역할 |
|------|------|---------|-----------|------|
| 1 | llm-integration-deepdive-3pass-audit | 3회 독립 조사 | 109+ | 발견 (28건) |
| 2 | llm-deepdive-adversarial-3pass-correction | 3회 적대적 감리 | 78+ | 1차 교정 (CRITICAL 5→0, FALSE 4건) |
| 3 | devils-advocate-pass3-audit | 상세 근거 | — | Devil's Advocate |
| 4-6 | llm-deepdive-final-6pass-verdict | 3회 2차 적대적 검증 | 200+ | 최종 판정 (HIGH 4→2, 추가 교정 2건) |

### 심각도 변천사

| 심각도 | 원본 (1단계) | 1차 교정 (2단계) | **최종 (4단계)** |
|--------|-------------|-----------------|-----------------|
| CRITICAL | 5 | 0 | **0** |
| HIGH | 9 | 4 | **2** |
| MEDIUM | 10 | 12 | **11** |
| LOW | 4 | 10 | **11** |
| FALSE | 0 | 2+2 | **4** |
| **실질 합계** | 28 | 26 | **24** |

### 교정 핵심 사례

**CRITICAL → LOW (5건 전부 하향)**:
1. 캐시 키 장르 폴백 → MEDIUM: content_hash가 2차 격리 제공
2. anyOf 스키마 → HIGH: isinstance 가드 13곳 존재하나 유지보수 부담
3. protagonist_name 인젝션 → MEDIUM: 자가 호스팅 + JSON 강제 + 포맷팅 불일치 수준
4. `_last_thinking` 미리셋 → LOW: 진단 로그 전용
5. `json.loads(strict=False)` → LOW: Gemini JSON 모드가 NaN 방지

**1차 교정 오류 (6-pass에서 재교정)**:
1. `_extract_json_robust()`를 "최후수단 파서"로 기술 → 실제: **모든 응답의 유일한 JSON 파서** (60+ 호출부)
2. 토큰 추정 HIGH → LOW: 실패 호출 한정 폴백
3. 429 모호 분류 HIGH → MEDIUM: 실제 Gemini 429에 거의 항상 키워드 포함

### 확신도

**6-pass 최종 확신도: 93%**

잔여 불확실성 (7%):
1. anyOf 스키마: 미래 신규 소비자가 isinstance 가드 없이 추가될 경우
2. orchestrator 부작용: `batch_validator.py` → `orchestrator.validate()` 부작용 미완전 추적
3. 429 분류: Gemini API 에러 형식 변경 시 모호 케이스 발현 가능

---

## [부록 B] 근거 파일

### 코드 파일

| 파일 | 경로 | 역할 |
|------|------|------|
| base_agent.py | `modules/domain/agents/base_agent.py` | LLM 통합 핵심 — ask(), 폴백, 캐싱, 키 회전 |
| response_schemas.py | `modules/core/response_schemas.py` | Gemini JSON 스키마 정의 (10개 타입) |
| gemini_provider.py | `modules/core/providers/gemini_provider.py` | Gemini API 래퍼 |
| openai_provider.py | `modules/core/providers/openai_provider.py` | OpenAI API 래퍼 (미검증) |
| anthropic_provider.py | `modules/core/providers/anthropic_provider.py` | Anthropic API 래퍼 (미검증) |
| llm_router.py | `modules/core/llm_router.py` | 모델→프로바이더 라우팅 |
| llm_schema.py | `modules/core/llm_schema.py` | 스키마 변환 (Gemini types ↔ dict) |
| metrics_collector.py | `modules/core/metrics_collector.py` | 토큰/비용 추적 싱글턴 |
| blueprint_ensemble.py | `modules/domain/agents/blueprint_ensemble.py` | 앙상블 투표 + ThreadPoolExecutor |
| three_phase_blueprint_generator.py | `modules/domain/agents/three_phase_blueprint_generator.py` | 3-Phase Blueprint 생성 |
| writer.py | `modules/domain/agents/writer.py` | 원고 생성 (protagonist_name 미이스케이핑) |

### 설정 파일

| 파일 | 경로 | 역할 |
|------|------|------|
| system.yaml | `config/system.yaml` | API 설정, 캐시 설정, thinking budget |
| models.yaml | `config/models.yaml` | 에이전트별 모델, 폴백 체인 |
| validation.yaml | `config/validation.yaml` | 검증 임계값, MAX_CONTEXT_CHARS |

### 감리 문서

| 문서 | 경로 |
|------|------|
| 원본 조사 (3-pass) | `docs/2026-03-18/OPUS/geuldobi-v2-llm-integration-deepdive-3pass-audit.md` |
| 1차 교정 (적대적 3-pass) | `docs/2026-03-18/OPUS/geuldobi-v2-llm-deepdive-adversarial-3pass-correction.md` |
| 최종 판정 (6-pass) | `docs/2026-03-18/OPUS/geuldobi-v2-llm-deepdive-final-6pass-verdict.md` |
| 모델 선정 보고서 (5-pass) | `docs/2026-03-18/OPUS/geuldobi-v2-llm-model-selection-report.md` |

### 보안 전수 조사 결과 (6-pass)

| 검사 항목 | 결과 | 근거 |
|-----------|------|------|
| `eval()`/`exec()` on LLM output | **안전** | `ast.literal_eval()` 사용 — 리터럴만 평가 |
| SQL injection via LLM output | **안전** | f-string SQL은 하드코딩 스키마명 사용, LLM 출력 미삽입 |
| 파일 시스템 조작 via LLM output | **안전** | LLM 출력을 경로로 사용하는 코드 없음 |
| 하드코딩 시크릿 | **안전** | 모든 API 키 `os.getenv()` 로드 |
| 무한 메모리 증가 | **안전** | `_agent_durations` 500 상한, `_context_caches` 50 상한 |
| MetricsCollector 스레드 안전성 | **안전** | `threading.Lock()` 보호 |

---

*6-pass adversarial 감리 완료. 24 실질 이슈: 2 HIGH, 11 MEDIUM, 11 LOW, 4 FALSE 삭제.*
*확신도 93%. 문서 생성: 2026-03-18.*
