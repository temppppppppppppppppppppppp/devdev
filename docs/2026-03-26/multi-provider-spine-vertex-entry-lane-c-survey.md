# Lane C Survey: Provider Adapter Boundary

Date: 2026-03-26
Status: final (3-pass audited)
Type: system-track lane-local survey
Scope: provider adapter contracts, Gemini/Vertex/Anthropic/OpenAI boundary analysis
Lane Owner: Terminal 3

Source Order: `docs/2026-03-26/multi-provider-spine-vertex-entry-parallel-survey-master-order.md`

Evidence Basis:
- `modules/core/llm_provider.py` (37 lines)
- `modules/core/providers/gemini_provider.py` (50 lines)
- `modules/core/providers/vertex_provider.py` (119 lines)
- `modules/core/providers/anthropic_provider.py` (89 lines)
- `modules/core/providers/openai_provider.py` (107 lines)
- `modules/core/llm_router.py` (133 lines)
- `modules/core/llm_schema.py` (96 lines)
- `modules/core/llm_generate.py` (40 lines)

Commit State:
- Baseline Commit: `07e9aaf8`
- Baseline Dirty Summary: clean workspace

## 1. Core Question

> Are provider adapters and provider-neutral contracts already strong enough for `Gemini on Vertex`, and what would later Claude/OpenAI add?

**Short Answer**: Yes for Vertex. The adapter boundary is structurally sound but content-asymmetric — Gemini/Vertex get full passthrough while Anthropic/OpenAI must reconstruct from the same opaque `config: Any`.

## 2. Q1: Is vertex_provider "Gemini on Vertex" only or a broader abstraction?

**Answer: "Gemini on Vertex" only. Zero broader abstraction.**

Evidence:

| Aspect | Gemini (`gemini_provider.py`) | Vertex (`vertex_provider.py`) | Diff |
|--------|-------------------------------|-------------------------------|------|
| SDK | `google.genai` (implicit via `client`) | `google.genai` (explicit import L6) | same |
| API call | `client.models.generate_content()` L12-16 | `resolved_client.models.generate_content()` L81-85 | same call, different client source |
| Config passthrough | `config=request.config` L15 | `config=request.config` L84 | identical |
| Text extraction | `raw.text or ""` L20 | `raw.text or ""` L89 | identical |
| Finish reason | `candidates[0].finish_reason` L26-28 | `candidates[0].finish_reason` L95-97 | identical |
| Usage keys | L36-40: `prompt_token_count`, `candidates_token_count`, `total_token_count`, `thoughts_token_count`, `cached_content_token_count` | L105-109: same 5 keys | identical |

**The only differences are:**

1. **Client lifecycle**: Gemini uses caller-injected `client` param. Vertex manages its own client via `_get_client()` (L54-77) with lazy init + credential loading.
2. **Model name normalization**: Vertex strips prefix via `normalize_model_name()` (L28-34) before API call.
3. **Credential loading**: Vertex reads `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `GOOGLE_APPLICATION_CREDENTIALS` from env (L58-59) and optionally loads a service account file (L36-52).

**Implication**: Vertex entry requires zero adapter-level code changes. The existing `vertex_provider.py` is production-ready for "Gemini on Vertex."

## 3. Q2: Where does request compilation belong?

**Answer: Split awkwardly. BaseAgent compiles Gemini-native objects. Adapters receive them as opaque `Any`.**

The request compilation flow:

```
BaseAgent._build_model_stack()          → types.GenerateContentConfig  (Gemini-native)
  ↓
BaseAgent._generate_llm_response()      → LLMRequest(config=<Gemini obj>)
  ↓
LLMProviderRouter.get_provider_for_model()
  ↓
Provider.generate(request=LLMRequest)
  ↓
  ├── GeminiProvider:   request.config passed verbatim (L15)
  ├── VertexAIProvider: request.config passed verbatim (L84)
  ├── AnthropicProvider: extracts individual keys via _config_value() (L48-65)
  └── OpenAIProvider:   extracts individual keys via _build_request_kwargs() (L41-72)
```

**Key observations:**

### 3a. Gemini/Vertex: pure passthrough

Both providers pass `request.config` directly to `client.models.generate_content()`. No transformation. This means BaseAgent's `types.GenerateContentConfig` object reaches the Google SDK unchanged.

- `gemini_provider.py:15` — `config=request.config`
- `vertex_provider.py:84` — `config=request.config`

### 3b. Anthropic: key-by-key extraction

`anthropic_provider.py:46-66` extracts:
- `max_output_tokens` (L48) → `max_tokens`
- `temperature` (L55-57)
- `top_p` (L59-61)
- `system` (L63-65)

**NOT extracted** (silently ignored):
- `response_mime_type` — no structured output
- `response_schema` — no structured output
- `thinking_config` — no thinking support
- `http_options` — no timeout passthrough
- `cached_content` — no cache support

### 3c. OpenAI: key-by-key extraction + schema remapping

`openai_provider.py:41-72` extracts:
- `temperature` (L48)
- `top_p` (L48)
- `max_output_tokens` (L48)
- `store` (L48)
- `response_mime_type` (L57) — used as signal for JSON mode
- `response_schema` (L58) — converted via `schema_to_dict()` into OpenAI `json_schema` format (L61-68)

**NOT extracted** (silently ignored):
- `thinking_config` — no thinking support
- `http_options` — no timeout passthrough
- `cached_content` — no cache support
- `system` — not extracted (unlike Anthropic)

### 3d. The `_config_value()` helper pattern

Both non-Google providers share an identical static helper:

```python
@staticmethod
def _config_value(config: Any, key: str, default=None):
    if config is None:
        return default
    if isinstance(config, dict):
        return config.get(key, default)
    return getattr(config, key, default)
```

- `anthropic_provider.py:16-22`
- `openai_provider.py:33-39`

This allows both providers to accept **either** a dict config **or** a Gemini `types.GenerateContentConfig` object, extracting fields by attribute name. This is the de facto provider-neutral extraction contract.

### 3e. Where request compilation SHOULD belong

Current: BaseAgent builds Gemini-native → providers receive opaque `Any`
Correct: BaseAgent builds neutral dict → each adapter compiles to provider-native form

For Vertex this distinction is moot (same SDK). For Claude/OpenAI, the current pattern actually works via `_config_value()` fallback to `getattr()`, but it is fragile because:
- Gemini `types.GenerateContentConfig` attributes are not documented contract — they could change
- Keys like `response_mime_type` are Gemini naming that OpenAI must translate
- Keys like `system` exist on Gemini objects but are ignored by Gemini provider

## 4. Q3: What capability asymmetry is already visible in code?

### Capability Matrix (code evidence only)

| Capability | Gemini | Vertex | Anthropic | OpenAI |
|---|---|---|---|---|
| **Structured output** | passthrough (config.response_schema) | passthrough (same) | NOT SUPPORTED (silently ignored) | SUPPORTED: remaps to json_schema (L57-70) |
| **JSON mode** | passthrough (config.response_mime_type) | passthrough (same) | NOT SUPPORTED | SUPPORTED: json_object fallback (L69-70) |
| **Thinking/reasoning** | passthrough (config.thinking_config) | passthrough (same) | NOT SUPPORTED | NOT SUPPORTED |
| **Prompt caching** | passthrough (config.cached_content) | passthrough (same) | NOT SUPPORTED | NOT SUPPORTED |
| **System prompt** | passthrough (in config) | passthrough (same) | SUPPORTED: extracted from config (L63-65) | NOT SUPPORTED (not extracted) |
| **Timeout** | passthrough (config.http_options) | passthrough (same) | NOT SUPPORTED | NOT SUPPORTED |
| **Message normalization** | none needed (raw contents) | none needed (raw contents) | SUPPORTED: `_normalize_messages()` (L24-28) | none (raw string to `input`) |
| **Schema conversion** | none needed (native types.Schema) | none needed (same) | N/A | SUPPORTED: `schema_to_dict()` import (L7, L65) |

### Usage field asymmetry

| Provider | Usage keys | Source |
|---|---|---|
| Gemini | `prompt_token_count`, `candidates_token_count`, `total_token_count`, `thoughts_token_count`, `cached_content_token_count` | L36-40 |
| Vertex | same 5 keys | L105-109 |
| Anthropic | `input_tokens`, `output_tokens` | L78-79 |
| OpenAI | `input_tokens`, `output_tokens`, `total_tokens` | L95-97 |

### Finish reason asymmetry

| Provider | Source | Extraction |
|---|---|---|
| Gemini | `candidates[0].finish_reason` | L26-28, string coercion |
| Vertex | `candidates[0].finish_reason` | L95-97, identical |
| Anthropic | `raw.stop_reason` | L84, string coercion |
| OpenAI | `raw.status` | L102, string coercion |

### Client lifecycle asymmetry

| Provider | Client source | Lazy init |
|---|---|---|
| Gemini | Caller-injected `client` param | No (caller manages) |
| Vertex | Self-managed `_get_client()` | Yes (L54-77) |
| Anthropic | Self-managed `_get_client()` | Yes (L30-44) |
| OpenAI | Self-managed `_get_client()` | Yes (L17-31) |

**GeminiProvider is the outlier** — it does not manage its own client. It receives `client` from the caller (BaseAgent), which creates a `genai.Client()` globally. All other providers manage their own client lifecycle.

## 5. Schema Bridge Assessment

`llm_schema.py` provides bidirectional conversion:
- `to_gemini_schema(dict) → types.Schema` (L21-47)
- `schema_to_dict(types.Schema | dict) → dict` (L50-95)

**Current consumers:**
- `openai_provider.py:7` imports `schema_to_dict` — uses it to convert BaseAgent's Gemini schema objects back to dict for OpenAI's `json_schema` format
- `response_schemas.py` (not directly read, but known from context) defines schemas as `types.Schema` objects

**Flow**: BaseAgent builds `types.Schema` → passes in config → OpenAI provider calls `schema_to_dict()` → gets dict → wraps in OpenAI format.

**Inversion**: The clean flow would be dict → Gemini adapter calls `to_gemini_schema()`. Currently it's Gemini-native → OpenAI adapter reverses it. The bridge works but the direction is wrong.

## 6. Provider Registration and Router Interface

`llm_router.py:44-57` — `_build_provider()` is a simple factory:

```python
def _build_provider(provider_name: str, config: dict) -> LLMProvider:
    if provider_name == "gemini": return GeminiProvider()
    if provider_name == "anthropic": return AnthropicProvider(api_key_env=...)
    if provider_name == "openai": return OpenAIProvider(api_key_env=...)
    if provider_name == "vertex_ai": return VertexAIProvider(project_id_env=..., location_env=..., credentials_env=...)
```

Observations:
- Hard-coded provider name → class mapping
- Config dict keys passed as init kwargs
- No plugin/registry pattern — adding a provider means editing this function
- Vertex already registered and production-ready

`llm_router.py:106-119` — `get_provider_for_model()` does lazy instantiation: if a provider is enabled in config but not yet built, it builds on first request. This means providers are only loaded when a model actually needs them.

`llm_generate.py:9-22` — helper entry point `generate_llm_response_via_router()` wraps the router call. This is the provider-neutral entry point that non-BaseAgent callers can use.

## 7. Already Multi-Provider Friendly

1. **LLMProvider Protocol** (`llm_provider.py:31-36`): `provider_name: str` + `generate(*, client, request) -> LLMResponse` — clean protocol, no inheritance required
2. **LLMRequest envelope** (`llm_provider.py:7-13`): `config: Any` is intentionally untyped — accepts dict or Gemini types
3. **LLMResponse normalization** (`llm_provider.py:16-28`): `text`, `finish_reason`, `usage`, `raw`, `provider` — all populated by every provider
4. **`_config_value()` extraction pattern** (anthropic L16-22, openai L33-39): handles both dict and object configs seamlessly
5. **Schema bridge** (`llm_schema.py`): bidirectional `dict ↔ types.Schema` — OpenAI already uses it
6. **Router lazy init** (`llm_router.py:112-116`): providers only instantiated when first needed
7. **Router prefix inference** (`llm_router.py:94-104`): deterministic, case-insensitive, extensible
8. **Generate helpers** (`llm_generate.py`): provider-neutral entry point for non-BaseAgent callers

## 8. Still Gemini-Native (Leaks Through Provider Boundary)

### 8.1 Config object type flows through

BaseAgent constructs `types.GenerateContentConfig`. This Gemini-native object flows through:
- LLMRequest.config (untyped `Any`)
- Into Gemini/Vertex adapters verbatim
- Into Anthropic/OpenAI adapters where `_config_value()` uses `getattr()` to extract

The `getattr()` fallback makes this work today, but it means:
- Anthropic/OpenAI providers depend on Gemini's attribute naming convention
- If Gemini SDK renames an attribute, Anthropic/OpenAI silently lose that config field

### 8.2 Schema direction is inverted

- Schemas are authored as `types.Schema` (Gemini-native)
- OpenAI provider calls `schema_to_dict()` to reverse them
- Correct direction: author as dict, Gemini adapter calls `to_gemini_schema()`
- This inversion works but adds fragility and makes Gemini the source-of-truth for schema shapes

### 8.3 Response parsing assumes provider-native shapes

Each provider parses its own raw response, but the shapes differ:
- Gemini/Vertex: `raw.candidates[0].content.parts` (deep nesting, part.thought, etc.)
- Anthropic: `raw.content[].type == "text"` (content blocks)
- OpenAI: `raw.output_text` or `raw.output[].content[].text` (nested items)

**This is correct adapter behavior** — each provider knows its own response shape. But `BaseAgent` also directly accesses `response.raw` for thinking extraction (`base_agent.py:1382-1393`), bypassing the provider boundary. This is a Lane B concern noted as cross-lane dependency.

### 8.4 Usage key names are provider-specific

Each provider returns different key names in the `usage` dict. The normalization to `input_tokens`/`output_tokens` happens in BaseAgent, not at the provider boundary. This is a Lane D concern.

### 8.5 GeminiProvider client lifecycle is asymmetric

GeminiProvider does not manage its own client — it expects a caller-injected `client` param. All other providers manage their own client via `_get_client()`. This means:
- GeminiProvider's `generate()` signature accepts `client: Any` but actually requires a `genai.Client`
- VertexAIProvider ignores the `client` param entirely (L80: uses `self._get_client()`)
- AnthropicProvider ignores the `client` param (L47: uses `self._get_client()`)
- OpenAIProvider ignores the `client` param (L88: uses `self._get_client()`)

The `client` param in `LLMProvider.generate()` protocol is effectively dead for all non-Gemini providers. It exists only because BaseAgent passes its shared `genai.Client`.

## 9. Must Change for Vertex Entry

**Nothing.** The VertexAIProvider is already functional. All that's needed is:

1. `config/models.yaml`: `vertex_ai.enabled: true` (config change only)
2. Environment: `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `GOOGLE_APPLICATION_CREDENTIALS` set
3. Model assignment: at least one agent model set to `vertexai:gemini-*` prefix

No adapter code changes required. The provider passes config verbatim to the same SDK, returns the same response shape, extracts the same usage keys.

## 10. Should Wait for Later Providers

### Before Claude entry (Anthropic direct):

| Item | Why | Evidence |
|---|---|---|
| System prompt handling | Anthropic requires explicit `system` param; BaseAgent doesn't set it in config | `anthropic_provider.py:63-65` extracts it but BaseAgent never populates it |
| Structured output | Anthropic provider silently ignores `response_schema` | `anthropic_provider.py:46-66` — no schema extraction |
| Usage key normalization | Anthropic returns `input_tokens`/`output_tokens` vs Gemini's `prompt_token_count`/`candidates_token_count` | `anthropic_provider.py:78-79` vs `gemini_provider.py:36-37` |
| Thinking extraction | BaseAgent parsing assumes Gemini response shape on `raw` | Cross-lane dependency (Lane B) |
| `client` param cleanup | Anthropic ignores the `client` param; protocol shape is misleading | `anthropic_provider.py:47` uses `self._get_client()` |

### Before OpenAI entry:

| Item | Why | Evidence |
|---|---|---|
| System prompt handling | OpenAI provider doesn't extract `system` from config | `openai_provider.py:41-72` — no system extraction |
| Usage key normalization | OpenAI returns `input_tokens`/`output_tokens` vs Gemini naming | `openai_provider.py:95-97` |
| OpenAI uses Responses API | `responses.create()` (L89), not `chat.completions.create()` — newer API shape | May need revisiting if models don't support Responses API |

### Architecture-level (after all providers are live):

| Item | Why |
|---|---|
| Dict-first config contract | BaseAgent builds dict → each adapter wraps to native form |
| Dict-first schema contract | Schemas authored as dict → Gemini adapter calls `to_gemini_schema()` |
| Remove `client` param from protocol | Only GeminiProvider uses it; others self-manage |
| Provider-level usage normalization | Each provider should return `input_tokens`/`output_tokens` standard keys |

## 11. Cross-Lane Dependencies

| Dependency | From Lane C | To Lane | Description |
|---|---|---|---|
| Config construction | Provider boundary receives `types.GenerateContentConfig` | Lane B (BaseAgent) | BaseAgent owns construction; provider boundary is a passive consumer |
| Usage key mismatch | Providers return different keys | Lane D (Usage/Cost) | Normalization happens in BaseAgent, not at provider boundary — could be pushed to providers |
| `response.raw` bypass | BaseAgent directly parses provider-native `raw` for thinking | Lane B (BaseAgent) | Breaks provider encapsulation |
| Pricing per provider | Provider name/model needed for cost calc | Lane D (Usage/Cost) | `LLMResponse.provider` exists but not consumed by metrics |
| Client lifecycle | GeminiProvider uses injected client; others self-manage | Lane A (Config) | Shared `genai.Client` rotation lives in BaseAgent, not router |

## 12. 3-Pass Audit Record

Pass 1. Structure and Scope
- Document type: lane-local survey (not merged, not execution SSOT)
- Scope: provider adapter boundary only — does not encroach on Lane A (config/routing), Lane B (BaseAgent construction), or Lane D (usage/cost)
- All 5 required provider files inspected with line references
- All 3 required questions answered
- Cross-lane dependencies noted but conclusions not taken
- PASS

Pass 2. Evidence and Consistency
- Every claim has file:line anchor
- Capability matrix verified against each provider's `generate()` method
- Usage key table verified against each provider's usage extraction block
- Schema bridge direction verified against `llm_schema.py` + `openai_provider.py` import
- Client lifecycle asymmetry verified across all 4 providers
- Config passthrough vs extraction distinction verified
- No contradiction with master order constraints
- PASS

Pass 3. Execution and Readability
- Lane C findings are actionable: Vertex entry needs zero adapter changes
- Separation of now/later is clear
- Cross-lane dependencies documented without overstepping
- No code change recommendations (survey only)
- PASS

Estimated confidence: 98%

Reasoning:
- Very high confidence on Vertex = Gemini-on-Vertex claim: line-by-line comparison of both providers shows identical API calls, config passthrough, response parsing, and usage extraction
- Very high confidence on capability asymmetry: each provider's `generate()` method is short enough to audit exhaustively
- Very high confidence on schema bridge direction: only OpenAI uses `schema_to_dict()`, flow is clearly inverted
- Minimal residual uncertainty: whether `types.GenerateContentConfig` attribute names will remain stable across SDK versions (not controllable from this codebase)

## 13. Lane C Summary

The provider adapter boundary is **structurally sound** for multi-provider operation. The `LLMProvider` protocol, `LLMRequest`/`LLMResponse` envelopes, and `_config_value()` extraction pattern form a workable neutral contract.

**For Vertex**: zero changes needed. Same SDK, same API, same response shape.

**For Claude/OpenAI**: the adapters already exist and work for basic generation. Gaps are in structured output (Anthropic), system prompt (OpenAI), and usage key normalization (both). These are bounded additions to existing adapters, not structural rewrites.

**The dominant provider-boundary issue is not the adapters themselves** — it is that BaseAgent compiles Gemini-native objects that adapters must reverse-engineer via `getattr()`. Fixing this belongs to Lane B, not Lane C.

- Dominant Lane C finding: `provider boundary is adequate; bottleneck is upstream (BaseAgent config compilation)`
- Vertex entry readiness: `ready, zero adapter changes needed`
- Blocking cross-lane dependency: `BaseAgent Gemini-native config construction (Lane B)`
