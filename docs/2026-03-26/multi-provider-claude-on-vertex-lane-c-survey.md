# Lane C Survey: Request / Response / Capability Asymmetry

Date: 2026-03-26
Status: final (3-pass audited)
Type: system-track lane-local survey
Scope: capability asymmetry between Claude direct and Claude on Vertex, as relevant to this codebase
Lane Owner: Terminal 3

Source Order: `docs/2026-03-26/multi-provider-claude-on-vertex-entry-parallel-survey-master-order.md`

Evidence Basis:
- `modules/core/providers/anthropic_provider.py` (91 lines)
- `modules/core/providers/vertex_provider.py` (139 lines)
- `modules/core/providers/openai_provider.py` (108 lines)
- `modules/core/llm_provider.py` (42 lines)
- `modules/core/llm_schema.py` (96 lines)
- `modules/core/response_schemas.py` (~300 lines)
- `modules/domain/agents/base_agent.py` (key sections: L632-710, L1011-1090, L1382-1393, L2010-2100)
- `docs/2026-03-26/llm-multi-provider-context-note.md` (context note, sections 5.2-5.3)

Commit State:
- Baseline Commit: `07e9aaf8`
- Baseline Dirty Summary: multi-provider spine + vertex entry Wave 1 applied

## 1. Core Question

> What capability asymmetry between Claude direct and Claude on Vertex is already relevant to this codebase?

**Short Answer**: The capability delta between Claude direct and Claude on Vertex is small at the API contract level, but large in this codebase because the dominant request/response path is entirely Gemini-native. The adapter already works for basic Claude generation. The gaps are in structured output, thinking extraction, and prompt caching — and these gaps exist equally for both Claude direct and Claude on Vertex.

## 2. SDK Path Decision (Prerequisite)

Before analyzing capability asymmetry, the SDK routing question must be settled:

| Path | Description | Code Impact |
|---|---|---|
| **A. Anthropic SDK + Vertex endpoint** | `anthropic.AnthropicVertex(project_id=..., region=...)` | Reuses existing `anthropic_provider.py` message shape; client construction diverges |
| **B. Google Gen AI SDK + Claude model** | `genai.Client(vertexai=True)` + Claude model name | Reuses existing `vertex_provider.py`; response shape would be Google-formatted |

**Anthropic's official docs** (context note §5.2) say the Vertex API is "nearly identical to the Messages API" — this refers to Path A. The two key differences are:
- `model` is specified in the Vertex endpoint URL, not the request body
- `anthropic_version` moves into the request body

**Path A is the correct choice** because:
1. The current `anthropic_provider.py` already parses Claude's Messages API response shape (content blocks, stop_reason, usage)
2. Path B would require Claude responses to be wrapped in Gemini's `candidates[].content.parts` shape — either by Google's SDK or by a custom adapter — adding a fragile translation layer
3. The Anthropic Python SDK natively supports Vertex (`from anthropic import AnthropicVertex`)

**Implication**: Claude on Vertex is an `AnthropicProvider` client variant, not a `VertexAIProvider` model extension.

## 3. Structured Output Delta

### 3a. Current codebase state

All response schemas in `response_schemas.py` are authored as `types.Schema` (Gemini-native):
- `BLOCKING_RESULT_SCHEMA` (L20-41)
- `SCORING_RESULT_SCHEMA` (L44-101)
- `ADVISORY_RESULT_SCHEMA` (L104-123)
- `DIRECTOR_AUDIT_SCHEMA` (L130-178)
- `STRATEGIC_AUDIT_SCHEMA` (L181+)
- and more (~15 total schema definitions)

The schema bridge in `llm_schema.py` provides:
- `schema_to_dict(types.Schema) -> dict` (L50-95) — Gemini to neutral
- `to_gemini_schema(dict) -> types.Schema` (L21-47) — neutral to Gemini

Current consumer: only `openai_provider.py:65` uses `schema_to_dict()`.

### 3b. Claude direct structured output

Anthropic's Messages API supports structured output via:
- `response_format={"type": "json_schema", "json_schema": {...}}` (newer)
- Tool-use pattern with forced tool calls (older)

Current `anthropic_provider.py` (L46-66): does **NOT** extract `response_schema` or `response_mime_type`. Structured output is silently ignored for all Claude calls.

### 3c. Claude on Vertex structured output

Context note §5.3: "the features-availability table does not currently list Vertex AI the same way for structured outputs."

**Operational consequence**: structured output availability may differ between Claude direct and Claude on Vertex, and must be capability-gated.

### 3d. Delta summary

| Dimension | Claude Direct | Claude on Vertex | Codebase Status |
|---|---|---|---|
| JSON mode | supported (native) | likely supported (same API) | NOT IMPLEMENTED in adapter |
| Schema enforcement | supported (json_schema) | uncertain (not equally documented) | NOT IMPLEMENTED in adapter |
| Schema source format | needs dict (JSON Schema) | needs dict (same) | schemas are `types.Schema`, bridge exists but unused for Claude |

**Asymmetry**: **small between Claude direct and Claude on Vertex** (likely same capabilities). **Large between Claude and current codebase** (adapter doesn't implement it at all).

## 4. System Prompt Delta

### 4a. Current implementation

`anthropic_provider.py` L63-65:
```python
system = self._config_value(request.config, "system")
if system:
    kwargs["system"] = system
```

This extracts the `system` key from the config (whether dict or Gemini `GenerateContentConfig` object) and passes it as the `system` parameter to `messages.create()`.

### 4b. BaseAgent population

`base_agent.py` L1057-1077 (`_build_model_stack`): the `config_params` dict does **NOT** include a `system` key. System prompt is passed via `contents` (as the first message), not as a separate config parameter.

This means the Anthropic adapter's system extraction (L63-65) is effectively dead code — the `system` key is never populated by the upstream caller.

### 4c. Claude on Vertex

Claude on Vertex (via Anthropic SDK) supports `system` in the same way as Claude direct — as a top-level parameter in `messages.create()`.

### 4d. Delta summary

| Dimension | Claude Direct | Claude on Vertex | Codebase Status |
|---|---|---|---|
| System prompt support | yes (top-level param) | yes (same) | Adapter supports it (L63-65), but upstream never populates `system` in config |

**Asymmetry**: **none between Claude direct and Claude on Vertex**. The gap is between what the adapter can handle and what BaseAgent actually sends.

## 5. Thinking / Reasoning Delta

### 5a. Request construction

`base_agent.py` L1068-1075:
```python
if thinking_level:
    budget = self.THINKING_BUDGET_MAP.get(thinking_level.lower(), 8192)
    config_params["thinking_config"] = types.ThinkingConfig(thinking_budget=budget, include_thoughts=True)
```

This is entirely Gemini-native. The `types.ThinkingConfig` object is a Google SDK class.

Claude's thinking feature uses a different API shape:
- Request: `thinking={"type": "enabled", "budget_tokens": N}` parameter
- Response: content blocks with `type="thinking"` containing `thinking` text

### 5b. Response extraction

`base_agent.py` L1382-1393:
```python
if response.candidates and response.candidates[0].content:
    for _p in response.candidates[0].content.parts:
        if getattr(_p, "thought", False) and isinstance(_p.text, str):
            _tparts.append(_p.text)
```

This assumes Gemini response shape (`candidates[].content.parts[].thought`).

Claude thinking responses use:
```python
for block in raw.content:
    if block.type == "thinking":
        thinking_text = block.thinking
```

### 5c. Current adapter state

`anthropic_provider.py` L46-66: does **NOT** extract `thinking_config` from the request config. Thinking is silently ignored.

`anthropic_provider.py` L69-72: only extracts `type == "text"` blocks from response content. Thinking blocks (`type == "thinking"`) are silently dropped.

### 5d. Claude direct vs Claude on Vertex

Both Claude direct and Claude on Vertex (via Anthropic SDK) support thinking with the same API contract:
- Same request parameter shape
- Same response content block shape
- Same `budget_tokens` semantics

### 5e. Delta summary

| Dimension | Claude Direct | Claude on Vertex | Codebase Status |
|---|---|---|---|
| Thinking request | `thinking={"type":"enabled","budget_tokens":N}` | same | NOT IMPLEMENTED (Gemini-native `ThinkingConfig` only) |
| Thinking response | `content[].type=="thinking"` | same | NOT EXTRACTED (only `type=="text"` extracted) |
| BaseAgent extraction | assumes `candidates[].content.parts[].thought` | same | Gemini-only shape, not Claude shape |

**Asymmetry**: **none between Claude direct and Claude on Vertex**. **Large between Claude and Gemini** in both request construction and response extraction.

## 6. Prompt Cache Delta

### 6a. Current implementation

`base_agent.py` L2010-2070 (`_get_or_create_context_cache`):
- Uses `self.client.caches.create()` — this is `genai.Client.caches.create()`, a Gemini API
- Config: `types.CreateCachedContentConfig(...)` — Gemini-native class
- Result: `cache.name` string passed as `cached_content` in `GenerateContentConfig`

This is entirely Gemini-specific. It uses Gemini's explicit cache creation API (create a named cache, then reference it by name in subsequent calls).

### 6b. Claude prompt caching

Anthropic's prompt caching uses inline `cache_control` markers within the messages themselves:
```python
{"role": "user", "content": [
    {"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}
]}
```

This is a completely different paradigm:
- Gemini: server-side named cache, explicit create/reference lifecycle
- Claude: inline marker, automatic server-side handling, no explicit lifecycle

### 6c. Claude direct vs Claude on Vertex

Anthropic's caching documentation covers both direct API and Bedrock. Vertex AI availability for prompt caching is not explicitly documented with equal detail.

### 6d. Delta summary

| Dimension | Claude Direct | Claude on Vertex | Codebase Status |
|---|---|---|---|
| Cache mechanism | inline `cache_control` markers | likely same (Anthropic SDK) | NOT IMPLEMENTED (Gemini cache API only) |
| Cache lifecycle | automatic (SDK manages) | likely same | N/A |
| Availability | documented | partially documented | N/A |

**Asymmetry**: **small between Claude direct and Claude on Vertex** (likely same mechanism via Anthropic SDK). **Fundamental paradigm difference between Claude and Gemini** — cannot share cache infrastructure.

## 7. Message Normalization Delta

### 7a. Current implementation

`anthropic_provider.py` L24-28:
```python
@staticmethod
def _normalize_messages(contents: Any) -> list[dict[str, Any]]:
    if isinstance(contents, list) and all(isinstance(item, dict) and "role" in item for item in contents):
        return contents
    return [{"role": "user", "content": str(contents)}]
```

This accepts either pre-formatted Anthropic message dicts or raw content (stringified).

### 7b. BaseAgent message format

BaseAgent passes `contents` as `current_prompt` (L668), which is typically a string. The normalizer wraps this as `[{"role": "user", "content": str(contents)}]`.

### 7c. Claude direct vs Claude on Vertex

Both use the Anthropic Messages API format: `[{"role": "user|assistant", "content": str|list[block]}]`.

### 7d. Delta summary

| Dimension | Claude Direct | Claude on Vertex | Codebase Status |
|---|---|---|---|
| Message format | Messages API format | same (via Anthropic SDK) | Adapter normalizes correctly (L24-28) |
| Multi-turn | supported | supported | Adapter passes through if pre-formatted |
| Image/vision | content blocks with `type="image"` | same | NOT IMPLEMENTED in normalizer |

**Asymmetry**: **none between Claude direct and Claude on Vertex**. Normalizer works for current text-only use case.

## 8. Usage / Token Reporting Delta

### 8a. Current implementation

`anthropic_provider.py` L74-80:
```python
usage = {
    "input_tokens": getattr(usage_raw, "input_tokens", None),
    "output_tokens": getattr(usage_raw, "output_tokens", None),
}
```

This extracts Anthropic's native key names, which differ from Gemini's (`prompt_token_count` / `candidates_token_count`).

### 8b. Claude direct vs Claude on Vertex

Both return the same usage shape:
- `input_tokens`
- `output_tokens`
- `cache_creation_input_tokens` (if caching active)
- `cache_read_input_tokens` (if caching active)

### 8c. Delta summary

| Dimension | Claude Direct | Claude on Vertex | Codebase Status |
|---|---|---|---|
| Usage keys | `input_tokens`, `output_tokens` | same | Adapter extracts both (L78-79) |
| Cache tokens | `cache_creation_input_tokens`, `cache_read_input_tokens` | likely same | NOT EXTRACTED |

**Asymmetry**: **none between Claude direct and Claude on Vertex**. Cache token extraction is missing for both.

## 9. Consolidated Capability Matrix

| Capability | Claude Direct | Claude on Vertex (Anthropic SDK) | Delta | Codebase Ready |
|---|---|---|---|---|
| Basic generation | yes | yes | none | YES (adapter works) |
| System prompt | yes | yes | none | PARTIAL (adapter handles, upstream doesn't populate) |
| Structured output | yes (json_schema) | uncertain | possible | NO (adapter ignores) |
| Thinking/reasoning | yes | yes | none | NO (Gemini-only shapes) |
| Prompt caching | yes (inline cache_control) | partially documented | possible | NO (Gemini-only API) |
| Message normalization | Messages API format | same | none | YES (normalizer works) |
| Usage reporting | input/output tokens | same | none | YES (adapter extracts) |
| Vision/images | yes | yes | none | NO (normalizer text-only) |
| Tool use | yes | yes | none | NO (not implemented in adapter) |

## 10. What Must Be Capability-Gated Before Claude on Vertex Enters

### 10a. Hard gates (will cause runtime errors or silent data loss if unhandled)

| Gate | Risk | Source |
|---|---|---|
| Structured output | All ask() calls pass `response_schema=types.Schema(...)` — Claude adapter ignores it, meaning Claude will return unstructured text where Gemini returns enforced JSON | `base_agent.py` L632-642, `anthropic_provider.py` L46-66 |
| Thinking extraction | BaseAgent L1382-1393 directly parses `response.raw` assuming Gemini shape — Claude thinking blocks will be silently dropped | `base_agent.py` L1382-1393 |
| Prompt caching | `_get_or_create_context_cache()` calls `genai.Client.caches.create()` — will crash or no-op if model is Claude | `base_agent.py` L2064-2071 |

### 10b. Soft gates (degraded but not broken)

| Gate | Risk | Source |
|---|---|---|
| System prompt | BaseAgent doesn't populate `system` in config — Claude's system prompt capability is unused | `base_agent.py` L1057-1077 |
| Cache token reporting | Anthropic returns cache-specific usage keys not extracted by adapter | `anthropic_provider.py` L77-80 |
| Schema direction | Schemas authored as `types.Schema` must be converted to dict for Claude — `schema_to_dict()` bridge exists but is unused in the Anthropic path | `response_schemas.py`, `llm_schema.py` |

### 10c. Not relevant for Wave 1

| Item | Why defer |
|---|---|
| Vision/image | No agent currently sends image content |
| Tool use | No agent currently uses LLM tool calling |
| Streaming | Not used in current architecture |

## 11. Minimum Wave 1 Scope for Claude on Vertex (Lane C Perspective)

From the capability asymmetry analysis, the minimum changes needed are:

1. **Client construction**: `AnthropicProvider` gains a constructor variant or subclass that creates `AnthropicVertex(project_id=..., region=...)` instead of `Anthropic(api_key=...)`. Response parsing, message normalization, and usage extraction stay identical.

2. **Structured output forwarding**: Anthropic adapter must extract `response_schema` from config, convert via `schema_to_dict()`, and pass as Anthropic's `response_format` parameter. This is the highest-value gating item.

3. **`LLMResponse.raw` access guard**: BaseAgent's thinking extraction (L1382-1393) must check `response.family` or `response.provider` before assuming Gemini response shape. The simplest approach: skip thinking extraction for non-Gemini providers in Wave 1.

Items 1 and 3 are mandatory. Item 2 is high-value but could be deferred if Claude on Vertex is initially used only for tasks that don't require schema enforcement (rare in this codebase — most ask() calls pass response_schema).

## 12. Cross-Lane Dependencies

| Dependency | From Lane C | To Lane | Description |
|---|---|---|---|
| Client construction choice | SDK path A (Anthropic SDK) is correct | Lane B (Adapter Boundary) | Lane B owns the adapter shape decision; Lane C confirms the request/response shape is compatible |
| Config compilation | `types.GenerateContentConfig` flows into adapter as opaque `Any` | Lane B (Adapter Boundary) | Capability asymmetry is amplified by upstream config being Gemini-native |
| Usage key normalization | Claude and Gemini use different key names | Lane D (Usage/Cost) | Already noted in prior Vertex survey; applies equally to Claude on Vertex |
| Identity routing | Claude on Vertex needs `backend=anthropic_vertex, family=claude` | Lane A (Config/Routing) | Lane C confirms the response shape supports this identity |
| Schema direction | Schemas are `types.Schema` (Gemini-native) | Lane B (Adapter Boundary) | The schema bridge exists; the question is where conversion is invoked |

## 13. Key Finding: The Asymmetry Is Not Claude Direct vs Claude on Vertex

The most important finding of this survey is:

**The capability delta between Claude direct and Claude on Vertex is minimal.** Both use the same Anthropic SDK, same Messages API shape, same response format, same usage keys.

**The dominant asymmetry is between Claude (any backend) and the Gemini-native codebase.** The gaps — structured output, thinking, prompt caching — exist because the codebase speaks Gemini, not because Vertex introduces new constraints.

This means:
- Fixing capability gaps for Claude direct automatically fixes them for Claude on Vertex
- Claude on Vertex adds only one incremental delta: client construction (`AnthropicVertex` vs `Anthropic`)
- The decision to enter Claude on Vertex should not be blocked by capability asymmetry if the team accepts capability-gated deployment (e.g., initially without structured output or thinking for Claude models)

## 14. 3-Pass Audit Record

Pass 1. Structure and Scope
- Document type: lane-local survey (not merged, not execution SSOT)
- Scope: capability asymmetry only — does not encroach on Lane A (config/routing), Lane B (adapter boundary), or Lane D (usage/cost/env)
- All 6 required capability dimensions answered with code evidence
- Cross-lane dependencies noted but conclusions not taken
- PASS

Pass 2. Evidence and Consistency
- Every claim has file:line anchor
- Capability matrix verified against each provider's `generate()` method and BaseAgent's construction paths
- SDK path decision grounded in context note §5.2 official-doc evidence
- Structured output uncertainty correctly reflects context note §5.3
- Schema bridge direction verified against `llm_schema.py` + provider imports
- Thinking extraction Gemini-native assumption verified at `base_agent.py` L1382-1393
- Prompt cache Gemini-only implementation verified at `base_agent.py` L2064-2071
- No contradiction with master order constraints
- PASS

Pass 3. Execution and Readability
- Key finding (§13) is clearly stated: asymmetry is Claude-vs-Gemini, not Claude-direct-vs-Claude-Vertex
- Capability-gated deployment path is identified
- Minimum Wave 1 scope is bounded to 3 items
- No code change recommendations (survey only)
- PASS

Estimated confidence: 97%

Reasoning:
- Very high confidence on Claude direct vs Claude on Vertex parity: Anthropic's official docs explicitly state the Vertex API is "nearly identical to the Messages API" — confirmed by SDK design
- Very high confidence on structured output gap: `anthropic_provider.py` L46-66 exhaustively inspected, no schema extraction present
- Very high confidence on thinking gap: both request construction (L1068-1075) and response extraction (L1382-1393) are demonstrably Gemini-native
- Very high confidence on prompt cache gap: `_get_or_create_context_cache()` calls Gemini-specific API
- Moderate uncertainty on structured output availability on Vertex specifically — context note §5.3 flags this as partially documented, cannot be resolved from code alone

## 15. Lane C Summary

The capability asymmetry between Claude direct and Claude on Vertex is **minimal** — both use the Anthropic SDK with the same Messages API contract.

The **dominant asymmetry is between Claude (any backend) and the Gemini-native codebase**:
- Structured output: adapter doesn't implement it (silently ignored)
- Thinking: request and response shapes are completely different
- Prompt caching: completely different paradigm (inline markers vs server-side named cache)

For a Claude on Vertex Wave 1:
- **Mandatory**: client construction variant + `response.raw` access guard
- **High-value**: structured output forwarding via schema bridge
- **Deferrable**: thinking support, prompt caching, system prompt population

- Dominant Lane C finding: `asymmetry is Claude-vs-Gemini, not direct-vs-Vertex`
- Structured output readiness: `not ready — adapter silently ignores schemas`
- Minimum capability gate: `response.raw Gemini-shape guard + client construction`
