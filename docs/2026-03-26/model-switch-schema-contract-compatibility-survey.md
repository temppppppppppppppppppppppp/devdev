# Model-Switch Schema / Output-Contract Compatibility Survey

Date: 2026-03-26
Status: survey-complete
Document Type: system-track survey report
Source Order: `docs/2026-03-26/model-switch-schema-contract-compatibility-1terminal-master-order.md`
Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`
Baseline Dirty Summary: dirty — Stage 4 Wave 1/2 code and tests, observability files, dated docs, no active temp execution queue

---

## 1. Findings Summary

The codebase has a **two-layer architecture**: a model-agnostic routing/envelope layer (`LLMProvider` protocol, `LLMResponse` dataclass, `LLMProviderRouter`) and a Gemini-first implementation layer that bypasses the abstraction at 19+ callsites. The routing layer is well-designed but underutilized — most production code constructs Gemini-native `types.GenerateContentConfig` objects directly and reads Gemini-native usage metadata keys.

The dominant compatibility seam is **mixed**: token usage key normalization (provider-adapter) and direct Gemini config construction (schema/config bypass) are the two largest friction surfaces, with retry/error classification as a secondary concern.

---

## 2. Robust Contract Surfaces (Model-Agnostic)

### 2A. Provider Abstraction Layer

| Surface | File:Line | Status |
|---------|-----------|--------|
| `LLMProvider` protocol | `llm_provider.py:31-36` | ROBUST — clean Protocol with `generate()` returning `LLMResponse` |
| `LLMResponse` dataclass | `llm_provider.py:16-28` | ROBUST — `text`, `finish_reason`, `usage: dict`, `raw`, `provider` |
| `LLMProviderRouter` | `llm_router.py:60-123` | ROBUST — model prefix → provider dispatch, YAML-driven enablement |
| Provider inference | `llm_router.py:93-104` | ROBUST — covers `gemini*`, `claude*`, `gpt*/o1/o3/o4`, `vertexai:` |
| 4 provider implementations | `providers/{gemini,anthropic,openai,vertex}_provider.py` | ROBUST — each normalizes to `LLMResponse` |
| Schema conversion utilities | `llm_schema.py:21-47` (to_gemini) / `50-95` (to_dict) | ROBUST — bidirectional dict ↔ `types.Schema` |
| OpenAI config normalization | `openai_provider.py:57-70` | ROBUST — maps `response_mime_type` + `response_schema` to OpenAI `text.format` |
| Anthropic message normalization | `anthropic_provider.py:25-28, 46-88` | ROBUST — normalizes contents + extracts text blocks |

### 2B. JSON Parsing

| Surface | File:Line | Status |
|---------|-----------|--------|
| `_extract_json_robust()` | `base_agent.py:1811-1934` | ROBUST — model-agnostic: bracket repair, regex extraction, `ast.literal_eval` fallback, recursive flattening |
| `_parse_and_repair_hard()` | `base_agent.py:1936-1976` | ROBUST — last-resort JSON recovery, no provider assumptions |
| List normalization | `chief_writer.py:754-761` | ROBUST — handles `list` → `dict[0]` unwrap from any model |
| Content format normalization | `chief_writer.py:859-873` | ROBUST — string/list/dict/nested polymorphism |
| Markdown fence stripping | `chief_writer.py:1425-1426` | ROBUST — strips ` ```json ``` ` wrappers |

### 2C. Error Handling & Retry

| Surface | File:Line | Status |
|---------|-----------|--------|
| Network retry constants | `base_agent.py:278-281` | ROBUST — generic exponential backoff (10-30s, 22 retries) |
| Error string pattern matching | `base_agent.py:1210-1224` | MIXED — uses generic patterns ("429", "quota", "resource_exhausted") that work across providers, but has `is_gemini3_rate_limit: False` placeholder |
| Continuation prompt | `base_agent.py:1440-1451` | ROBUST — generic truncation recovery, no provider assumptions |

### 2D. Config Override

| Surface | File:Line | Status |
|---------|-----------|--------|
| YAML-driven model config | `models_config.py:45-63` | ROBUST — `config/models.yaml` overrides inline defaults |
| Agent model resolution | `models_config.py:66-97` | ROBUST — `load_model_contract()` with provenance tracking |
| Model fallback chain | `base_agent.py:298-300` | ROBUST — `_resolve_backup_model()` with provider-prefix support |

---

## 3. Brittle Model-Shaped Assumptions

### 3A. CRITICAL — Direct Gemini Config Construction (19 callsites, 15 files)

These callsites construct `types.GenerateContentConfig` directly, bypassing the provider abstraction. A model switch would require touching every one.

| File | Line(s) | Context |
|------|---------|---------|
| `base_agent.py` | 1077, 1355, 1488, 2163 | `_build_model_stack()`, retry config, backup config, cached context |
| `analyst.py` | 870 | Schema-enabled generation |
| `director_continuity.py` | 599 | Continuity verification |
| `manuscript_validator.py` | 612 | Validation generation |
| `state_tracker_npc.py` | 774, 2165 | NPC state extraction (2 callsites) |
| `writer.py` | 281 | Manuscript generation |
| `weaver.py` | 63 | Scene weaving |
| `narrative_structure_analyzer.py` | 148 | Structure analysis |
| `response_schemas.py` | 914 | Schema validation |
| `stage4_orchestrator.py` | 700 | Blueprint preflight |
| `stage0/reverse_expander.py` | 92 | Reverse expansion |
| `stage0/style_extractor.py` | 1176 | Style extraction |
| `stage0/story_expander.py` | 87 | Story expansion |
| `advisory_validator.py` | 149 | Advisory validation |
| `scoring_validator.py` | 271 | Score validation |

**Impact**: Every callsite passes Gemini-native `types.GenerateContentConfig` as `config=` to `_generate_content()` or `client.models.generate_content()`. Non-Gemini providers cannot accept these objects.

**Existing mitigation**: `openai_provider.py:41-72` already reads config values generically via `_config_value(config, key)`, so the OpenAI provider can accept either dict or Gemini config objects. `anthropic_provider.py:17-22` has the same pattern. However, the Gemini-specific parameters (`thinking_config`, `http_options`, `response_mime_type`) have no provider-neutral equivalents defined yet.

### 3B. CRITICAL — Token Usage Key Mismatch

The Gemini provider returns Gemini-native keys; consuming code only reads Gemini-native keys.

| Layer | Gemini Keys | Anthropic Keys | OpenAI Keys |
|-------|-------------|----------------|-------------|
| Provider output | `prompt_token_count`, `candidates_token_count`, `thoughts_token_count`, `cached_content_token_count` | `input_tokens`, `output_tokens` | `input_tokens`, `output_tokens`, `total_tokens` |
| Consumer expectation | `base_agent.py:282-287` `_USAGE_KEYS` | — | — |
| Metric payload builder | `base_agent.py:439-442` reads Gemini keys only | Falls back to token estimation | Falls back to token estimation |
| Session cost kwargs | `base_agent.py:466-470` maps Gemini → standard | Empty dict (no match) | Empty dict (no match) |

**Impact**: When using Anthropic or OpenAI providers, token counting falls through to heuristic estimation (`collector.estimate_tokens()`), session logger receives no token data, and cost calculation uses default Gemini pricing.

### 3C. HIGH — Thinking API Coupling

| Surface | File:Line | Details |
|---------|-----------|---------|
| `THINKING_BUDGET_MAP` | `base_agent.py:155-158` | Maps `minimal/low/medium/high/maximum` → integer budgets (1K-24K) |
| `types.ThinkingConfig()` | `base_agent.py:1068-1075` | Gemini 2.5+ exclusive API |
| Thinking content extraction | `base_agent.py:1382-1393, 2184-2194` | Reads `response.candidates[0].content.parts` → `getattr(_p, "thought", False)` |
| ChiefWriter thinking usage | `chief_writer.py:850, 856, 1500, 1831` | All manuscript generation uses `thinking_level="medium"` |

**Impact**: Claude's extended thinking uses a different API surface (`thinking` parameter with `type: "enabled"`). OpenAI o1/o3/o4 have "reasoning tokens" with no user-facing thinking output. The extraction logic in `base_agent.py:1382-1393` depends on Gemini's `candidates[0].content.parts` structure with `.thought` attribute.

### 3D. HIGH — Context Caching (Gemini-Only)

| Surface | File:Line | Details |
|---------|-----------|---------|
| Cache infrastructure | `base_agent.py:2005-2008` | `_context_caches`, `_cache_lock`, `_CONTEXT_CACHE_MAX`, `_MIN_CACHE_CONTENT` |
| Cache creation | `base_agent.py:2063-2071` | `self.client.caches.create()` + `types.CreateCachedContentConfig()` |
| Cache consumption | `base_agent.py:2149` | `"cached_content": cache_name` in config |
| 5 agent integrations | ChiefWriter, ArcEnsemble, BprintEnsemble, DirectorEnsemble, DirectorContinuity | `_ask_with_cached_context()` calls |

**Impact**: Gemini's cached content API has no direct equivalent in Claude or OpenAI. Claude has prompt caching (automatic, not explicit), OpenAI has no equivalent. The entire caching subsystem is Gemini-specific and would need to be either skipped or re-implemented per provider.

### 3E. MEDIUM — Response Structure Parsing

| Surface | File:Line | Assumption |
|---------|-----------|------------|
| `response.text` access | `base_agent.py:1377-1379` | Expects `.text` property; Gemini may raise `ValueError` on safety filter |
| `response.candidates[0].content.parts` | `base_agent.py:1385-1388` | Gemini-specific nested structure for thinking extraction |
| `finish_reason` values | `base_agent.py:1422-1427` | Expects `"MAX_TOKENS"`, `"LENGTH"`, `"stop"` — Anthropic uses `"end_turn"`, `"max_tokens"` |

**Mitigation**: The LLM router already normalizes `.text` and `.finish_reason` in each provider's `generate()` method. However, `base_agent.py` still accesses `response.raw` directly for thinking extraction (L1385), bypassing the normalization.

### 3F. MEDIUM — Cost Model

| Surface | File:Line | Details |
|---------|-----------|---------|
| `MODEL_COSTS` dict | `metrics_collector.py:71-82` | Only covers `gemini-2.5-flash` and `gemini-2.5-pro` |
| Default fallback | `metrics_collector.py:81` | Uses Gemini Pro pricing as default for unknown models |
| `_normalize_billable_model()` | `metrics_collector.py:85-91` | Only strips Vertex prefixes |

**Impact**: Claude and OpenAI models get charged at Gemini Pro rates. Not a functional break, but cost reporting will be inaccurate.

### 3G. MEDIUM — Hardcoded Model Defaults

| Surface | File:Line | Details |
|---------|-----------|---------|
| `DEFAULT_PRO_MODEL` | `models_config.py:11` | `"gemini-3.1-pro-preview"` |
| `DEFAULT_FLASH_MODEL` | `models_config.py:13` | `"gemini-2.5-flash"` |
| 18 agent role mappings | `models_config.py:15-36` | All point to Gemini models |
| Fallback chain | `models_config.py:38-42` | Gemini Pro → Gemini Pro fallback → Flash |

**Mitigation**: All overridable via `config/models.yaml`. A model switch only requires YAML changes, not code changes.

### 3H. LOW — Prompt Markers & Content Extraction

| Surface | File:Line | Details |
|---------|-----------|---------|
| `[원고_끝]` marker | `chief_writer.py:1753` | Korean end-of-manuscript marker, model-agnostic in principle but untested with non-Gemini models |
| `"patch_state_updates"` regex search | `chief_writer.py:1727-1750` | Searches for JSON key as literal string in response |
| Context window 400K truncation | `blueprint_ensemble.py:1181, 1209` | Assumes Gemini's 1M+ context; Claude 200K would need different limits |

---

## 4. Architecture Assessment

### 4A. What Already Works

The codebase has a **Phase 1 provider abstraction** already in place:

```
config/models.yaml → models_config.py → llm_router.py → providers/{gemini,anthropic,openai,vertex}_provider.py
                                                ↓
                                        LLMResponse (normalized)
```

This layer is clean and correctly designed. The OpenAI provider already normalizes `response_mime_type` and `response_schema` via `schema_to_dict()`. The Anthropic provider normalizes messages and text extraction. All four providers return `LLMResponse`.

### 4B. What Breaks

The **gap** is between the provider abstraction and the consuming code:

1. **Config construction**: 19 callsites create `types.GenerateContentConfig` directly instead of using a provider-neutral config envelope
2. **Usage key reading**: `base_agent.py` reads Gemini-native keys (`prompt_token_count`, `candidates_token_count`) instead of standard keys
3. **Thinking API**: config construction + response parsing are both Gemini-specific
4. **Context caching**: entire subsystem is Gemini-exclusive
5. **Raw response access**: thinking extraction bypasses `LLMResponse.text` and reads `response.raw.candidates[0].content.parts`

### 4C. Bypass Topology

```
                    LLMRouter (ROBUST)
                         │
                    LLMResponse.text (ROBUST)
                         │
          ┌──────────────┼──────────────┐
          │              │              │
    ask() main path   thinking     caching
    (MIXED)           extraction    subsystem
          │           (BRITTLE)    (BRITTLE)
          │              │              │
    _build_model_stack   reads         reads
    types.GenerateContent  .raw.candidates  client.caches.create
    Config (BRITTLE)    [0].content    (BRITTLE)
          │              .parts
          │              │
    _build_metric_usage   _USAGE_KEYS
    _payload (BRITTLE)    Gemini-only
                          (BRITTLE)
```

---

## 5. Bounded Future Hardening Candidates

### Candidate A: Usage Key Normalization (Best ROI)

**Scope**: Normalize token usage keys at the provider boundary so consuming code never sees provider-specific keys.

**What changes**:
- Each provider's `generate()` returns usage dict with standard keys: `input_tokens`, `output_tokens`, `cached_tokens`, `thinking_tokens`
- `base_agent.py:_USAGE_KEYS` updated to standard keys
- `base_agent.py:_build_metric_usage_payload()` and `_session_token_cost_kwargs()` read standard keys
- `metrics_collector.py:MODEL_COSTS` extended with Claude/OpenAI pricing

**Why best ROI**:
- Touches ~3 files (providers + base_agent + metrics_collector)
- Fixes silent data loss (token counts, cost reporting)
- No prompt/schema/retry changes needed
- No risk to Gemini production path

### Candidate B: Config Envelope Normalization

**Scope**: Replace direct `types.GenerateContentConfig` construction with a provider-neutral config dict that each provider's `generate()` interprets.

**What changes**:
- Define a standard config dict shape: `{temperature, max_output_tokens, top_p, response_mime_type, response_schema, thinking_level, timeout}`
- Each provider maps this to its native config
- Remove `from google.genai import types` from 15+ files

**Why deferred**:
- Touches 19 callsites across 15 files
- Requires careful testing of each agent's generation path
- Anthropic/OpenAI providers already handle dict configs via `_config_value()`
- Higher blast radius, better as a second wave

### Candidate C: Thinking API Abstraction

**Scope**: Abstract thinking budget config + thinking content extraction per provider.

**Why deferred**:
- Only matters if target model supports thinking (Claude extended thinking, OpenAI reasoning)
- Current production uses Gemini thinking; no immediate switch planned
- Can be done as part of Candidate B

### Candidate D: Context Caching Abstraction

**Scope**: Per-provider caching strategy (explicit for Gemini, automatic for Claude, skip for OpenAI).

**Why deferred**:
- Gemini caching is a cost optimization, not a functional requirement
- Can gracefully degrade (skip caching for non-Gemini) without breaking functionality
- Lower priority than token counting and config normalization

---

## 6. Surfaces That Should Stay Untouched

1. **`_extract_json_robust()`** — already model-agnostic, heavily battle-tested, no changes needed
2. **`LLMProvider` protocol + `LLMResponse` dataclass** — clean design, no changes needed
3. **`LLMProviderRouter`** — correct routing logic, only needs extension for new model prefixes
4. **Provider `generate()` implementations** — each already normalizes to `LLMResponse`; changes should be additive (extend usage dict keys), not restructuring
5. **`config/models.yaml` override mechanism** — already supports model switching via config
6. **Prompt templates** — JSON format instructions are model-agnostic in principle; model-specific tuning is a quality concern, not a contract concern

---

## 7. Mandatory Final Lines

- Dominant compatibility seam: **mixed** (provider-adapter token keys + schema/config bypass)
- Best bounded compatibility candidate: **Usage key normalization at provider boundary** (Candidate A)
- Should Codex open an execution SSOT now: **no** (survey confidence is 96%, but no active model switch is planned — backlog this as a bounded future wave)

---

## 8. 3-Pass Audit Notes

- Pass 1 (Structure/Scope): document type is survey report, scope matches master order, included/excluded surfaces are coherent, save path is correct
- Pass 2 (Evidence/Consistency): all file:line anchors verified against live code reads, provider file contents confirmed, callsite counts cross-checked with grep results (19 `GenerateContentConfig`, 17 `response_mime_type` in production), usage key mismatch confirmed via direct provider source review
- Pass 3 (Execution/Readability): findings-first structure, one recommendation only, no overreach into provider benchmarking or migration policy, actionable candidate ranking, surfaces-to-leave-alone explicitly listed
- Confidence: 96%
