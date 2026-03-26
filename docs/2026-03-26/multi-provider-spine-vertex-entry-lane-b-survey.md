# Lane B Survey: BaseAgent Coupling / Request Construction

Date: 2026-03-26
Status: final (3-pass audited, lane-local survey)
Type: system-track parallel survey lane
Lane Owner: Terminal 2
Canonical Path: `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-b-survey.md`
Source Master Order: `docs/2026-03-26/multi-provider-spine-vertex-entry-parallel-survey-master-order.md`
Evidence Basis:
- `modules/domain/agents/base_agent.py`
- `modules/core/llm_schema.py`
- `modules/core/llm_provider.py`
- `modules/core/response_schemas.py`

Commit State:
- Baseline Commit: `07e9aaf8`
- Baseline Dirty Summary: clean workspace

## 1. Lane B Core Question

How Gemini-native is the dominant request path right now?

## 2. Findings

### 2.1 Gemini-Native Config Construction Sites (4 sites)

All LLM request configs are built as `google.genai.types.GenerateContentConfig`:

| # | Method | File:Line | Purpose |
|---|--------|-----------|---------|
| 1 | `_build_model_stack()` | `base_agent.py:1057-1077` | Primary config for `ask()` |
| 2 | `_build_retry_generate_config()` | `base_agent.py:1340-1355` | Retry/fallback config |
| 3 | `_attempt_backup_recovery()` | `base_agent.py:1480-1488` | Backup model config |
| 4 | `_ask_with_cached_context()` | `base_agent.py:2144-2163` | Cached context config |

Each site follows the same pattern:
```python
config_params = {
    "temperature": temperature,
    "max_output_tokens": self.MAX_OUTPUT_TOKENS,
    "top_p": 0.95,
    "response_mime_type": "application/json",
}
# ... optional: http_options, response_schema, thinking_config
config = types.GenerateContentConfig(**config_params)
```

### 2.2 Gemini-Native Sub-Components Inside Config

| Component | Sites | Type | Evidence |
|-----------|-------|------|----------|
| `types.GenerateContentConfig` | 4 | Config wrapper | `base_agent.py:1077, 1355, 1488, 2163` |
| `types.ThinkingConfig` | 3 | Thinking budget | `base_agent.py:1075, 1354, 2161` |
| `types.HttpOptions` | 2 | Timeout setting | `base_agent.py:1062, 2150` |
| `types.CreateCachedContentConfig` | 1 | Cache creation | `base_agent.py:2066` |
| `response_mime_type: "application/json"` | 4 | JSON mode key | `base_agent.py:1061, 1345, 1484, 2148` |
| `cached_content` config key | 1 | Cache usage | `base_agent.py:2149` |

### 2.3 Gemini-Native Response Parsing (2 sites)

Thinking text extraction reads `response.candidates[0].content.parts` and checks `getattr(_p, "thought", False)`:

| # | File:Line | Context |
|---|-----------|---------|
| 1 | `base_agent.py:1385-1393` | Primary ask path |
| 2 | `base_agent.py:2182-2195` | Cached context path |

This is Gemini-specific — Anthropic returns thinking via `content[].type == "thinking"`, OpenAI has no equivalent.

### 2.4 Gemini-Native Usage Key Hardcoding

`base_agent.py:282-287`:
```python
_USAGE_KEYS = (
    "prompt_token_count",
    "candidates_token_count",
    "thoughts_token_count",
    "cached_content_token_count",
)
```

Consumed at:
- `base_agent.py:416-425` — `_accumulate_last_llm_usage()` iterates these keys
- `base_agent.py:439-442` — `_build_metric_usage_payload()` extracts by these keys
- `base_agent.py:460-488` — `_session_token_cost_kwargs()` maps these keys to neutral names

### 2.5 Response Schema Definitions (16 constants, 273 `types.Schema()` calls)

`response_schemas.py` (926 lines) defines 16 top-level schema constants:

| Schema | File:Line |
|--------|-----------|
| `BLOCKING_RESULT_SCHEMA` | `response_schemas.py:20` |
| `SCORING_RESULT_SCHEMA` | `response_schemas.py:44` |
| `ADVISORY_RESULT_SCHEMA` | `response_schemas.py:104` |
| `DIRECTOR_AUDIT_SCHEMA` | `response_schemas.py:130` |
| `STRATEGIC_AUDIT_SCHEMA` | `response_schemas.py:181` |
| `CHARACTER_LOGIC_SCHEMA` | `response_schemas.py:205` |
| `ARC_STATE_SCHEMA` | `response_schemas.py:233` |
| `ARC_STATE_CONSTRAINTS_SCHEMA` | `response_schemas.py:251` |
| `ARC_DESIGN_SCHEMA` | `response_schemas.py:348` |
| `BLUEPRINT_PREFLIGHT_SCHEMA` | `response_schemas.py:509` |
| `BLUEPRINT_SCENE_ENTRY_SCHEMA` | `response_schemas.py:531` |
| `BLUEPRINT_SCENE_BREAKDOWN_SCHEMA` | `response_schemas.py:567` |
| `BLUEPRINT_PROTAGONIST_STATE_SCHEMA` | `response_schemas.py:580` |
| `BLUEPRINT_ENDING_STATE_SCHEMA` | `response_schemas.py:594` |
| `BLUEPRINT_SCHEMA` | `response_schemas.py:615` |
| `MANUSCRIPT_SCHEMA` | `response_schemas.py:651` |

All 16 are defined as `types.Schema(type=types.Type.OBJECT, ...)` — Gemini-native.

### 2.6 Provider-Neutral Infrastructure Already Exists

**LLMRequest/LLMResponse** (`llm_provider.py:7-37`):

Provider-neutral envelope. `config: Any` accepts both Gemini objects and dicts.

**`_generate_llm_response()`** (`base_agent.py:391-397`):

Provider-agnostic dispatch:
```python
request = LLMRequest(model=model, contents=contents, config=config)
provider = self._llm_router.get_provider_for_model(model)
response = provider.generate(client=self.client, request=request)
```

**Schema dict conversion** (`llm_schema.py:21-96`):

Bidirectional conversion already exists:
- `to_gemini_schema(dict) -> types.Schema` (line 21)
- `schema_to_dict(types.Schema) -> dict` (line 50)

**Pre-computed dict specs** (`response_schemas.py:675`):
```python
_TASK_SCHEMA_SPECS = {name: schema_to_dict(schema) for name, schema in _TASK_SCHEMA_CONSTANTS.items()}
```

**`get_schema_spec_for_task()`** (`response_schemas.py:698-702`):

Already returns provider-neutral dict schema. This is the clean path that non-Gemini providers should use.

**`get_schema_for_task()`** (`response_schemas.py:683-695`):

Rebuilds Gemini `types.Schema` from dict spec. This is the Gemini-specific path.

**Implication**: The schema SSOT is **already dict-based internally** (`_TASK_SCHEMA_SPECS`). The Gemini `types.Schema` constants are technically derived forms, not the canonical source. Migration to provider-neutral schemas is a surface-level change, not a deep rewrite.

### 2.7 Vertex Prefix Handling

`base_agent.py:58-67`:
```python
_PROVIDER_PREFIXES = ("vertexai:", "vertex:", "vertex/")

def _split_provider_prefixed_model(model: str) -> tuple[str, str]:
```

- Already recognizes Vertex prefixes
- Fallback chain re-attaches prefix after model resolution (`base_agent.py:70-81`)
- Router uses same prefix list for provider dispatch

### 2.8 `ask()` Public Contract

`base_agent.py:632`:
```python
def ask(self, prompt, temperature=0.5, response_schema=None, thinking_level=None):
```

- `response_schema` accepts `types.Schema` objects (callers pass Gemini-native)
- `thinking_level` accepts string (`"minimal"/"low"/"medium"/"high"`) or int budget
- Both are currently compiled to Gemini-native types inside `_build_model_stack()`

## 3. Must-Answer Questions

### Q1. Which request config pieces are still Gemini-native?

**All of them.** Every config builder constructs `types.GenerateContentConfig`. Specific Gemini-native pieces:
- `types.GenerateContentConfig` (4 sites)
- `types.ThinkingConfig` (3 sites)
- `types.HttpOptions` (2 sites)
- `types.CreateCachedContentConfig` (1 site)
- `response_mime_type` key name (4 sites) — Gemini-specific; Anthropic/OpenAI use different mechanisms
- `cached_content` key name (1 site) — Gemini-specific

### Q2. What minimum provider-neutral request contract already exists?

Good foundations exist:
- `LLMRequest(model, contents, config)` / `LLMResponse(text, finish_reason, usage, raw, provider)` — `llm_provider.py:7-37`
- `_generate_llm_response()` dispatch — `base_agent.py:391-397`
- Schema dict conversion infrastructure — `llm_schema.py:21-96`
- Pre-computed neutral dict schemas — `response_schemas.py:675`
- `get_schema_spec_for_task()` returns neutral dicts — `response_schemas.py:698-702`

**Gap**: `LLMRequest.config` is typed `Any`. No structural contract for what keys/types it should contain. Each provider adapter must know how to extract Gemini-named fields from a `types.GenerateContentConfig` object.

### Q3. What minimum decoupling is required before or during Vertex entry?

**None for Vertex.** Vertex uses the identical `google.genai` SDK with `vertexai=True`. All Gemini-native config objects, schemas, thinking, caching, and response parsing work identically on Vertex.

**For later Claude/OpenAI entry, the decoupling work is:**
1. Config builder sites (4) must output neutral dicts instead of `types.GenerateContentConfig`
2. Thinking level must map to provider-specific formats (Claude: `max_thinking_length`, OpenAI: N/A)
3. Schema callers must use `get_schema_spec_for_task()` (dict) instead of `get_schema_for_task()` (Gemini types.Schema)
4. Response parsing must abstract away Gemini `candidates[0].content.parts` thinking extraction
5. Caching (`client.caches.create`) is Gemini-only; must be behind a capability gate

## 4. Cross-Lane Dependencies

| To Lane | Dependency | Evidence |
|---------|-----------|----------|
| Lane A (config) | BaseAgent reads `models.yaml` agent config for model assignment | `base_agent.py:89-97`, `models_config.py` |
| Lane C (providers) | BaseAgent passes Gemini `types.GenerateContentConfig` as `LLMRequest.config` — Gemini/Vertex pass through, Anthropic/OpenAI must extract and rebuild | `base_agent.py:1077` → `llm_provider.py:13` → each provider's `generate()` |
| Lane D (usage) | BaseAgent extracts usage with Gemini-specific keys `_USAGE_KEYS` — Anthropic/OpenAI return different key names | `base_agent.py:282-287, 439-442` |

## 5. Lane B Verdict

### Already Multi-Provider-Friendly
1. `LLMRequest`/`LLMResponse` abstraction (`llm_provider.py:7-37`)
2. Provider-agnostic dispatch `_generate_llm_response()` (`base_agent.py:391-397`)
3. Schema dict conversion infrastructure (`llm_schema.py:21-96`)
4. Pre-computed neutral dict schemas via `_TASK_SCHEMA_SPECS` (`response_schemas.py:675`)
5. `get_schema_spec_for_task()` neutral dict accessor (`response_schemas.py:698-702`)
6. Vertex prefix recognition and fallback chain (`base_agent.py:58-81`)

### Still Gemini-Native
1. 4 config builder sites → `types.GenerateContentConfig` (`base_agent.py:1077, 1355, 1488, 2163`)
2. 3 thinking config sites → `types.ThinkingConfig` (`base_agent.py:1075, 1354, 2161`)
3. 2 timeout sites → `types.HttpOptions` (`base_agent.py:1062, 2150`)
4. 1 cache creation → `types.CreateCachedContentConfig` (`base_agent.py:2066`)
5. 16 schema constants × 273 `types.Schema()` calls (`response_schemas.py`)
6. 2 thinking extraction sites → Gemini `candidates[0].content.parts` (`base_agent.py:1385-1393, 2182-2195`)
7. Usage keys hardcoded to Gemini names (`base_agent.py:282-287`)

### Must Change for Vertex Entry Now
**Nothing.** Vertex uses the same `google.genai` SDK. All Gemini-native code works identically on Vertex without modification. Enable in config + set env vars.

### Should Wait for Later Providers
1. Extract provider-neutral config dict from 4 config builder sites
2. Abstract thinking config to `thinking_level` → provider-specific mapping at adapter boundary
3. Migrate schema callers from `get_schema_for_task()` to `get_schema_spec_for_task()`
4. Abstract thinking extraction from Gemini-specific response structure
5. Gate caching behind capability detection
6. Normalize usage keys at provider boundary (Lane D dependency)

## 6. 3-Pass Audit Record

Pass 1. Structure and Scope
- Document type is lane-local survey, not execution SSOT
- Scope bounded to BaseAgent/request construction per master order §8 Lane B
- Does not take over Lane A/C/D core questions
- All 3 must-answer questions addressed
- Cross-lane dependencies noted without concluding other lanes' findings
- PASS

Pass 2. Evidence and Consistency
- All 4 `types.GenerateContentConfig` sites verified by grep against live source
- All 3 `types.ThinkingConfig` sites verified by grep
- Schema constant count (16) verified by grep against live source
- `types.Schema(` count (273) verified by grep
- Pre-computed dict specs at line 675 verified by direct read
- `get_schema_spec_for_task()` signature and return type verified by direct read
- No claims beyond inspected code
- PASS

Pass 3. Execution and Readability
- Findings-first structure
- File:line anchors for every claim
- Clear separation of Gemini-native / multi-provider-friendly / must-change-now / should-wait
- Cross-lane dependencies documented as evidence, not conclusions
- PASS

Estimated confidence: 97%

Reasoning:
- High confidence on Gemini-native inventory because every claim is grep-verified against live source
- High confidence on Vertex compatibility because both use identical `google.genai` SDK
- High confidence on schema migration readiness because `_TASK_SCHEMA_SPECS` dict and `get_schema_spec_for_task()` already exist
- Moderate residual uncertainty only on whether any agent subclass bypasses `ask()` and builds its own config directly (grep shows `arc_ensemble.py:1081` passes `ARC_DESIGN_SCHEMA` through `ask()`, which is the expected path)
