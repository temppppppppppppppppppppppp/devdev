# 정확한 비용 추적 구현 명세

> 2026-03-12 작성. 현재 비용 기록의 정확도 검증 + 실제 토큰 기반 비용 추적 전환 가능성 분석.

---

## 1. 현재 상태: 비용이 정확하지 않다

### 1-1. 토큰 수 — 추정치(estimate), 실측값 아님

**`base_agent.py:604-606`**:
```python
input_tokens = collector.estimate_tokens(base_prompt, is_input=True)
output_tokens = collector.estimate_tokens(full_response, is_input=False)
```

**`metrics_collector.py:270-273`** (추정 알고리즘):
```python
korean_chars = sum(1 for c in text if "가" <= c <= "힣")
other_chars = len(text) - korean_chars
return int(korean_chars / 1.5 + other_chars / 4)
```

**오차 원인**:
| 원인 | 방향 | 추정 오차폭 |
|------|------|-------------|
| 한글 토크나이저 차이 (실제 ≈ 1.2~2.0자/토큰, 고정 1.5) | ±방향 | ±15~20% |
| 특수토큰/JSON 구분자/시스템 프롬프트 미계상 | 과소 | -5~10% |
| **Thinking 토큰 완전 누락** | **과소** | **-50~500%** |
| Context Cache 할인 미반영 | 과대 | +최대 90% |

### 1-2. 가격표 — 2개 모델 모두 오류

**`metrics_collector.py:69-73` (현재)**:
```python
MODEL_COSTS = {
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},   # ← 오류
    "gemini-2.5-pro":   {"input": 1.25, "output": 5.00},   # ← output 오류
    "default":          {"input": 0.50, "output": 2.00},
}
```

**Google 공식 가격 (2026-03, ≤200K context)**:

| 모델 | Input/1M | Output/1M (thinking 포함) | Cache Read/1M | Cache Storage |
|------|----------|---------------------------|---------------|---------------|
| gemini-2.5-pro | **$1.25** ✅ | **$10.00** ❌(현재 $5.00) | **$0.3125** (25%↓) | $4.50/1M/hr |
| gemini-2.5-flash | **$0.30** ❌(현재 $0.15) | **$2.50** ❌(현재 $0.60) | $0.03 (90%↓) | $1.00/1M/hr |

> **⚠️ Pro cache read 주의**: 공식 문서 기준 $0.31/1M (≈$0.3125). Flash는 input의 10%($0.03)이나, Pro는 input의 25%($0.3125). "일률 90% 할인" 가정은 부정확.

> **200K 초과 시 할증**: pro input $2.50, output $15.00 / flash input $0.60, output $5.00

### 1-3. 종합 오차 추정

| 요인 | 현재 DB 기록 | 실제 | 비율 |
|------|-------------|------|------|
| pro output 단가 | $5.00/M | $10.00/M | **2배 과소** |
| flash input 단가 | $0.15/M | $0.30/M | **2배 과소** |
| flash output 단가 | $0.60/M | $2.50/M | **4배 과소** |
| thinking 토큰 | 0 (미계상) | output 요금으로 과금 | **누락** |
| cache read 할인 | 미반영 | 90% 할인 | 과대 계상 |

**결론**: 현재 DB 기록 비용은 실제의 **1/2 ~ 1/5** 수준으로 과소 계상되고 있을 가능성 높음.

---

## 2. 실제 토큰 추적이 가능한가?

### 가능하다. 인프라는 이미 90% 구축되어 있다.

#### 2-1. Gemini SDK `usage_metadata` — 5개 필드 제공

```python
response.usage_metadata:
    prompt_token_count          # 입력 토큰 (정확)
    candidates_token_count      # 출력 토큰 (Developer API: thinking 포함)
    total_token_count           # 합계
    thoughts_token_count        # thinking 토큰 (별도 카운터)
    cached_content_token_count  # 캐시 히트 토큰
```

#### 2-2. 현재 코드베이스 — 추출은 하지만 버린다

```
Gemini SDK response
  ↓ usage_metadata 있음 ✅
GeminiProvider.generate()
  ↓ LLMResponse.usage에 3개 필드 추출 ✅
  ↓ LLMResponse.raw에 원본 보존 ✅
base_agent._generate_content()
  ↓ return response.raw  ← ❌ LLMResponse 버림, raw만 반환
base_agent.ask()
  ↓ collector.estimate_tokens()  ← ❌ 추정치 사용
```

**핵심 갭**: `base_agent.py:336`에서 `response.raw`만 반환하므로 `LLMResponse.usage`가 소실됨.

#### 2-3. 변경 필요 범위

| 단계 | 파일 | 변경량 | 효과 |
|------|------|--------|------|
| **S1**: `_generate_content()` 반환값 변경 | `base_agent.py` | ~5줄 | LLMResponse 보존 |
| **S2**: `ask()` 실측 토큰 사용 | `base_agent.py` | ~15줄 | 추정→실측 전환 |
| **S3**: thinking/cache 필드 추출 | `gemini_provider.py` | ~3줄 | 누락 필드 보강 |
| **S4**: 가격표 교정 + cache-aware 비용 계산 | `metrics_collector.py` | ~20줄 | 정확한 비용 |
| **S5**: `llm_generate.py` direct caller 경로 | `llm_generate.py` 외 | P2 후순위 | BaseAgent 밖 호출 커버 (~5% 비중) |

**S1~S4 총 변경량**: ~45줄, 4파일. 기존 동작 불변(fallback으로 estimate 유지). S5는 P2 후순위.

---

## 3. 구현 상세

### S1: LLMResponse 보존 (`base_agent.py:326-336`)

```python
# AS-IS
def _generate_content(self, *, model, contents, config):
    request = LLMRequest(model=model, contents=contents, config=config)
    provider = self._llm_router.get_provider_for_model(model)
    response = provider.generate(client=self.client, request=request)
    return response.raw  # ← usage 소실

# TO-BE
def _generate_content(self, *, model, contents, config):
    request = LLMRequest(model=model, contents=contents, config=config)
    provider = self._llm_router.get_provider_for_model(model)
    response = provider.generate(client=self.client, request=request)
    self._last_llm_response = response  # usage 보존
    return response.raw  # 하위호환 유지
```

**위험도**: 매우 낮음. `response.raw` 반환은 동일, side-channel로 usage만 보존.

### S2: 실측 토큰 사용 (`base_agent.py:600-606`)

```python
# AS-IS
input_tokens = collector.estimate_tokens(base_prompt, is_input=True)
output_tokens = collector.estimate_tokens(full_response, is_input=False)

# TO-BE
_usage = getattr(self, "_last_llm_response", None)
_usage = getattr(_usage, "usage", None) or {}
input_tokens = _usage.get("prompt_token_count") or collector.estimate_tokens(base_prompt, is_input=True)
output_tokens = _usage.get("candidates_token_count") or collector.estimate_tokens(full_response, is_input=False)
_thinking_tokens = _usage.get("thoughts_token_count", 0) or 0
_cached_tokens = _usage.get("cached_content_token_count", 0) or 0
```

**Fallback 보장**: usage가 None이면 기존 추정치로 자동 폴백. 기존 동작 100% 호환.

**⚠️ Thinking 토큰 중복 계산 방지**: Developer API에서 `candidates_token_count`는 thinking 토큰을 **이미 포함**. `thoughts_token_count`는 관측/로깅 전용으로 별도 추출하되, **비용 계산에는 `candidates_token_count`만 사용**해야 중복 과금 없음. Vertex AI 전환 시에만 `output = candidates + thoughts` 조정 필요.

### S3: thinking/cache 필드 추출 (`gemini_provider.py:35-39`)

```python
# AS-IS (3개 필드)
usage = {
    "prompt_token_count": getattr(usage_meta, "prompt_token_count", None),
    "candidates_token_count": getattr(usage_meta, "candidates_token_count", None),
    "total_token_count": getattr(usage_meta, "total_token_count", None),
}

# TO-BE (5개 필드)
usage = {
    "prompt_token_count": getattr(usage_meta, "prompt_token_count", None),
    "candidates_token_count": getattr(usage_meta, "candidates_token_count", None),
    "total_token_count": getattr(usage_meta, "total_token_count", None),
    "thoughts_token_count": getattr(usage_meta, "thoughts_token_count", None),
    "cached_content_token_count": getattr(usage_meta, "cached_content_token_count", None),
}
```

### S4: 가격표 교정 + cache-aware 비용 (`metrics_collector.py`)

#### S4-a: 가격표 교정만 (P0, 3줄 변경)

기존 `calculate_cost(model, input_tokens, output_tokens)` 시그니처 **불변**. 호출부 변경 0줄.

```python
# AS-IS (metrics_collector.py:69-73)
MODEL_COSTS = {
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gemini-2.5-pro":   {"input": 1.25, "output": 5.00},
    "default":          {"input": 0.50, "output": 2.00},
}

# TO-BE (Google 공식 2026-03 기준, ≤200K context)
MODEL_COSTS = {
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    "gemini-2.5-pro":   {"input": 1.25, "output": 10.00},
    "default":          {"input": 1.25, "output": 10.00},
}
```

**기존 호출부** (2곳, 변경 불필요):
- `metrics_collector.py:242` — `end_call()` 내부: `cost = self.calculate_cost(model, input_tokens, output_tokens)`
- `metrics_collector.py:345` — `get_session_stats()` 내부: `cost = self.calculate_cost(model, input_t, output_t)`

두 곳 모두 `(model, input_tokens, output_tokens)` 3인자 호출 → 시그니처 불변이므로 **영향 없음**.

#### S4-b: cache-aware 비용 계산 확장 (P2, ~15줄 변경)

`cached_tokens` 파라미터 추가. **default=0이므로 기존 호출부 하위호환**.

```python
MODEL_COSTS = {
    "gemini-2.5-flash": {
        "input": 0.30, "output": 2.50,
        "cache_read": 0.03, "cache_storage_per_hour": 1.00,
    },
    "gemini-2.5-pro": {
        "input": 1.25, "output": 10.00,
        "cache_read": 0.3125, "cache_storage_per_hour": 4.50,  # 공식: $0.31/1M
    },
    "default": {"input": 1.25, "output": 10.00, "cache_read": 0.3125},
}

def calculate_cost(self, model, input_tokens, output_tokens,
                   cached_tokens=0) -> float:
    costs = MODEL_COSTS.get(_normalize_billable_model(model), MODEL_COSTS["default"])
    # Developer API: candidates_token_count에 thinking 이미 포함 → 별도 가산 없음
    non_cached_input = max(0, input_tokens - cached_tokens)
    input_cost = (non_cached_input / 1_000_000) * costs["input"]
    cache_cost = (cached_tokens / 1_000_000) * costs.get("cache_read", costs["input"] * 0.1)
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + cache_cost + output_cost
```

**하위호환 보장**: `cached_tokens=0` default → 기존 2곳 호출부(`L242`, `L345`)는 수정 없이 동작. S2에서 `_cached_tokens`를 넘기는 새 호출만 cache-aware.

### S5: Direct Caller 경로 (`llm_generate.py`) — ⚠️ 별도 처리 필요

**현황**: `generate_content_via_router()`도 `response.raw`만 반환 (`llm_generate.py:21`). BaseAgent 경로와 동일하게 `LLMResponse.usage`가 소실됨.

**Direct caller 수**: 약 40+곳 (11개 파일)에서 `generate_content_via_router()` 호출.

**처리 방안**:
- **옵션 A (권장)**: `llm_generate.py` 반환값을 `LLMResponse`로 변경. 호출측에서 `response.text` 대신 `response.raw.text`로 접근 필요 → 40+곳 수정 필요 (대규모).
- **옵션 B (현실적)**: `llm_generate.py`에도 side-channel 패턴 적용. 모듈 레벨 `_last_usage` dict 보존 → `MetricsCollector`가 scope 종료 시 읽기. 호출측 변경 0줄.
- **옵션 C (최소)**: Direct caller 비용은 BaseAgent `ask()` 내부에서 호출되므로 이미 BaseAgent 스코프 집계에 포함됨 — **별도 처리 불필요**. 단, BaseAgent 밖에서 직접 호출하는 경우(advisory 등)는 미계상 감수.

> **참고**: Direct caller 대부분은 advisory 에이전트(LM-B~F, P1-5 등)로, 비용 비중이 낮음 (전체의 ~5% 미만). P2 이하 우선순위.

---

## 4. Gemini Developer API vs Vertex AI 차이점

| 항목 | Developer API (현재 사용) | Vertex AI |
|------|---------------------------|-----------|
| `candidates_token_count` | thinking 토큰 **포함** | thinking 토큰 **미포함** |
| 순수 출력 토큰 | `candidates - thoughts` | `candidates` |
| 과금 기준 출력 | `candidates_token_count` 그대로 | `candidates + thoughts` |

**현재 코드베이스는 Developer API 사용** → `candidates_token_count`를 output으로 쓰면 thinking 포함 비용이 자동 반영됨.

Vertex AI 전환 시에는 `output_tokens = candidates + thoughts`로 조정 필요.

---

## 5. 00_test_02 비용 재추정

DB 기록 기준 (추정 토큰):
- 총 880,936 토큰, DB 기록 비용 **$1.64**

가격표 교정만 적용 시 (output $5→$10, flash $0.15→$0.30/$0.60→$2.50):
- pro 비중 99% 기준, output 단가 2배 → 대략 **$2.5~3.0** 예상

Thinking 토큰 포함 시 (thinking이 output의 2~5배 가능):
- 실제 비용 **$5~10** 범위 가능

**Google 대시보드 $9.4와 근접할 수 있음** → 가격표 오류 + thinking 미계상이 주요 원인.

---

## 6. 리스크 평가

| 항목 | 리스크 | 이유 |
|------|--------|------|
| S1 (side-channel 보존) | **매우 낮음** | `response.raw` 반환 불변, 속성 하나 추가 |
| S2 (실측 토큰 사용) | **낮음** | fallback으로 estimate 유지, None-safe |
| S3 (필드 추가) | **매우 낮음** | getattr default=None, 기존 3필드 불변 |
| S4 (가격표 교정) | **낮음** | 표시용 비용만 변경, 파이프라인 동작 무관 |
| S5 (direct caller) | **낮음~중간** | `llm_generate.py`도 `response.raw`만 반환 — 옵션 C(미계상 감수) 권장, 비중 ~5% |

**파이프라인 동작에 영향 없음** — 비용 추적은 관측(observability) 전용이므로 모든 변경이 side-effect free.

---

## 7. 구현 우선순위

| 우선순위 | 작업 | 변경량 | 호출부 영향 | 효과 |
|----------|------|--------|-------------|------|
| **P0** | S4-a: 가격표 교정만 | 3줄 (`MODEL_COSTS` 값만) | 0줄 | 즉시 2배 정확도 |
| **P1** | S1+S2+S3: 실측 토큰 전환 | ~25줄 (base_agent+gemini_provider) | 0줄 | 추정→실측, thinking 포함 |
| **P2** | S4-b: cache-aware 비용 계산 | ~15줄 (metrics_collector) | 0줄 (default=0) | 캐시 할인 반영 |
| **P3** | S5+Vertex AI 분기 | 향후 | 미정 | 멀티프로바이더+direct caller |

---

## 8. 결론

| 질문 | 답 |
|------|-----|
| 정확한 비용 추적이 가능한가? | **YES** — Gemini SDK가 5개 토큰 필드 제공, 인프라 90% 구축됨 |
| 현재 비용이 정확한가? | **NO** — 토큰 추정 오차 + 가격표 오류 + thinking 누락 → 실제의 1/2~1/5 |
| 변경 범위는? | S1~S4: ~45줄, 4파일, 파이프라인 동작 무영향 (S5는 P2 후순위) |
| 가장 빠른 개선은? | 가격표 3줄 교정만으로 즉시 2배 정확도 |
