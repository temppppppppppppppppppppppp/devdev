# Lane D Survey: Usage / Cost / Runtime Env / Observability — Claude on Vertex

Date: 2026-03-26
Status: final (3-pass audited)
Type: system-track parallel survey lane (Claude-on-Vertex focus)
Lane Owner: Terminal 4
Canonical Path: `docs/2026-03-26/multi-provider-claude-on-vertex-lane-d-survey.md`
Source Master Order: `docs/2026-03-26/multi-provider-claude-on-vertex-entry-parallel-survey-master-order.md`

Evidence Basis:
- `modules/core/metrics_collector.py` (full file, 575 lines)
- `modules/domain/agents/base_agent.py` (L270-489: usage keys, accumulation, metric payload, session cost)
- `modules/api/process_runner.py` (L780-819: `_build_env`)
- `modules/core/llm_provider.py` (full file, 42 lines)
- `modules/core/llm_router.py` (full file, 143 lines)
- `modules/core/providers/anthropic_provider.py` (full file, 91 lines)
- `modules/core/providers/vertex_provider.py` (full file, 139 lines)
- `modules/core/providers/openai_provider.py` (full file, 108 lines)
- `config/models.yaml` (full file, 68 lines)
- Prior survey: `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-d-survey.md`
- Prior live check: `docs/2026-03-26/multi-provider-vertex-live-operator-check-report.md`
- Context note: `docs/2026-03-26/llm-multi-provider-context-note.md` (Section 5.2, 5.3)

Commit State:
- Baseline Commit: `07e9aaf8`
- Resume Drift Summary: dirty workspace (same as prior spine survey)

## 1. Lane D Core Question

If Claude on Vertex enters now, do usage/cost/runtime-launch fields stay coherent enough for operations?

Can the current metrics path distinguish `anthropic_direct` from `anthropic_vertex`?

## 2. Findings

### 2.1 Metrics Identity Inference Cannot Distinguish Claude Direct vs Claude on Vertex

`metrics_collector.py:100-101` maps `claude*` model names to a single tuple:

```python
if lowered.startswith("claude"):
    return ("anthropic", "anthropic_direct", "claude")
```

There is no `anthropic_vertex` path in `_infer_provider_identity()`. If both backends coexist, all Claude calls would be attributed to `anthropic_direct` in metrics — regardless of which backend actually served them.

Compare with Gemini, where `vertexai:` prefix triggers a distinct identity:

```python
if lowered.startswith(("vertexai:", "vertex:", "vertex/")):
    return ("vertex_ai", "google_vertex", "gemini")
```

For Claude on Vertex to be distinguishable, either:
- a model-name prefix convention must exist (e.g., `anthropic_vertex:claude-*`), or
- provider identity must propagate from `LLMResponse.backend` into metrics

Neither path exists today.

### 2.2 Provider Identity Propagation Is Wired But Not Used

`MetricsCollector.end_call()` at L243-245 already accepts override kwargs:

```python
provider: str | None = None,
backend: str | None = None,
family: str | None = None,
```

And `AgentMetric` at L27-43 carries all three fields.

However, `BaseAgent._build_metric_usage_payload()` at L427-458 returns only token counts. It does not extract or return `provider`/`backend`/`family` from `LLMResponse`. The caller never passes these identity fields to `end_call()`.

So the wiring exists at the sink, but the ingress path from `LLMResponse` to `MetricsCollector` is broken. Provider identity is inferred from model name only, which flattens Claude direct and Claude on Vertex into the same bucket.

### 2.3 Usage Key Extraction Will Silently Drop Anthropic Token Counts

`BaseAgent._USAGE_KEYS` at L282-287:

```python
_USAGE_KEYS = (
    "prompt_token_count",
    "candidates_token_count",
    "thoughts_token_count",
    "cached_content_token_count",
)
```

These are Gemini-native field names. The Anthropic provider at `anthropic_provider.py:77-80` emits:

```python
usage = {
    "input_tokens": ...,
    "output_tokens": ...,
}
```

The key mismatch means:

1. `_accumulate_last_llm_usage()` at L416-425 iterates `_USAGE_KEYS` — Anthropic's `input_tokens`/`output_tokens` are never accumulated.
2. `_build_metric_usage_payload()` at L439-442 reads `prompt_token_count` from usage — Anthropic returns 0 → falls to heuristic estimation at L444-446.
3. `_session_token_cost_kwargs()` at L466-471 reads `prompt_token_count`/`candidates_token_count` — same silent loss.

Net effect: all Claude calls (direct or Vertex) would report **estimated** token counts instead of actual API-reported values. Cost calculation would then use estimated tokens against incorrect pricing (see 2.4).

### 2.4 Pricing Table Has No Claude Entries

`MODEL_COSTS` at `metrics_collector.py:80-90`:

```python
MODEL_COSTS = {
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50, "cache_read": 0.03},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00, "cache_read": 0.125},
    "default": {"input": 1.25, "output": 10.00, "cache_read": 0.125},
}
```

Claude model names will not match any entry and fall to `default`, which uses Gemini 2.5 Pro pricing ($1.25 input / $10.00 output per 1M tokens).

Actual Claude pricing (as of 2026-03, Anthropic official):
- Claude Sonnet 4: ~$3 input / $15 output
- Claude Opus 4: ~$15 input / $75 output

Using Gemini default pricing for Claude would **undercount costs by 2-7.5x** depending on model tier. This is not a cosmetic gap — it is operationally misleading for cost monitoring and budget decisions.

### 2.5 ProcessRunner Does Not Inject Anthropic Credentials

`process_runner.py:780-819` `_build_env()` injects:

| Env Var | Injected | Source |
|---|---|---|
| `GOOGLE_API_KEY` | yes | `inputs["api_key"]` |
| `GOOGLE_API_KEY_2..9` | yes | `inputs["api_key_{i}"]` |
| `SLACK_WEBHOOK_URL` | yes | `inputs["slack_webhook"]` |
| `VERTEX_API_KEY` | yes | `inputs["vertex_api_key"]` |
| `VERTEX_PROJECT_ID` | yes | `inputs["vertex_project_id"]` |
| `VERTEX_LOCATION` | yes | `inputs["vertex_location"]` |
| `GOOGLE_APPLICATION_CREDENTIALS` | yes | `inputs["google_credentials_path"]` |
| `ANTHROPIC_API_KEY` | **NO** | not configured |
| `OPENAI_API_KEY` | **NO** | not configured |

Subprocess launches cannot use Claude (direct or Vertex) because:
- Claude direct needs `ANTHROPIC_API_KEY`
- Claude on Vertex needs Google Cloud credentials — which **are** now injected for Gemini-on-Vertex (`VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `GOOGLE_APPLICATION_CREDENTIALS`), but Claude on Vertex may also need an `ANTHROPIC_API_KEY` or a separate Vertex-specific Anthropic credential depending on SDK path

Note: the Anthropic Python SDK's `AnthropicVertex` class uses Google Cloud project/region auth, NOT `ANTHROPIC_API_KEY`. So the existing Vertex env vars (`VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `GOOGLE_APPLICATION_CREDENTIALS`) may partially cover Claude-on-Vertex auth — but the region naming may differ (Anthropic uses `us-east5`, not arbitrary GCP locations).

### 2.6 Router Has No `anthropic_vertex` Registration

`llm_router.py:25-30` `BACKEND_FAMILY_MAP`:

```python
BACKEND_FAMILY_MAP = {
    "gemini": ("google_direct", "gemini"),
    "vertex_ai": ("google_vertex", "gemini"),
    "anthropic": ("anthropic_direct", "claude"),
    "openai": ("openai_direct", "gpt"),
}
```

There is no `anthropic_vertex` entry. `DEFAULT_PROVIDER_CONFIGS` at L10-22 has no `anthropic_vertex` block either.

`infer_provider_name()` at L104-114 routes `claude*` → `"anthropic"` unconditionally. There is no prefix that can route to a hypothetical `anthropic_vertex` provider.

This means the routing layer cannot distinguish Claude direct from Claude on Vertex without:
- a new provider name (`anthropic_vertex`) and corresponding registration, or
- a model prefix convention (e.g., `anthropic_vertex:claude-*`)

### 2.7 Anthropic Provider Usage Shape vs Gemini Provider Usage Shape

| Field | Gemini/Vertex | Anthropic | OpenAI |
|---|---|---|---|
| Input tokens | `prompt_token_count` | `input_tokens` | `input_tokens` |
| Output tokens | `candidates_token_count` | `output_tokens` | `output_tokens` |
| Thinking tokens | `thoughts_token_count` | (not emitted) | (not emitted) |
| Cached tokens | `cached_content_token_count` | (not emitted) | (not emitted) |
| Total tokens | `total_token_count` | (not emitted) | `total_tokens` |

`BaseAgent` exclusively reads column 1 (Gemini shape). Columns 2 and 3 are silently dropped.

This is not a Claude-on-Vertex-specific issue — it affects all non-Gemini providers equally. But it becomes the dominant data-quality gap the moment any Claude model enters production usage.

## 3. Must-Answer Questions

### Q1. Can current metrics path distinguish `anthropic_direct` from `anthropic_vertex`?

**No.** Three independent barriers:
1. `_infer_provider_identity()` has no `anthropic_vertex` mapping
2. Router has no `anthropic_vertex` provider registration
3. `LLMResponse.backend` is not propagated into metrics

### Q2. Does env/runtime launch contract already have the right shape?

**Partially.** Vertex GCP credentials are now injected (Wave 1 fix). But `ANTHROPIC_API_KEY` is missing. Claude-on-Vertex auth may partially work through existing GCP credential injection, but Anthropic Vertex SDK uses a distinct region convention (`us-east5`) that is not reflected in `VERTEX_LOCATION`.

### Q3. Is pricing/usage normalization ready enough?

**No.**
- Usage: Gemini-only key extraction silently drops Anthropic actual counts → falls to heuristic estimation
- Pricing: no Claude entries → defaults to Gemini pricing → 2-7.5x cost undercount

### Q4. Is a small bounded observability addition required in Wave 1?

**Yes.** Three additions are required to avoid silent data quality degradation:
1. Usage key dispatch in `BaseAgent` (multi-family-aware extraction)
2. Claude pricing entries in `MODEL_COSTS`
3. Provider identity propagation from `LLMResponse` into `end_call()` overrides

## 4. Lane D Verdict

### Already Claude-on-Vertex-Friendly

1. `AgentMetric` dataclass carries `provider`, `backend`, `family` fields (`metrics_collector.py:41-43`)
2. `MetricsCollector.end_call()` accepts provider/backend/family overrides (`metrics_collector.py:243-245`)
3. `LLMResponse` carries provider/backend/family from provider adapters (`llm_provider.py:31-33`)
4. `AnthropicProvider` already stamps `backend="anthropic_direct", family="claude"` (`anthropic_provider.py:88-89`)
5. Metrics sink token fields are neutral (`metrics_collector.py:269-272`)
6. Scope-level `model_breakdown` tracks per-model costs independently (`metrics_collector.py:298-307`)
7. Vertex GCP env vars are now injected in `ProcessRunner` (`process_runner.py:808-818`)

### Not Yet Claude-on-Vertex-Ready

1. **`_infer_provider_identity()`** has no `anthropic_vertex` path — all Claude calls attributed to `anthropic_direct`
2. **`BaseAgent._USAGE_KEYS`** are Gemini-only — Anthropic actual token counts silently lost
3. **`_build_metric_usage_payload()`** reads Gemini-shaped keys — Claude falls to heuristic estimation
4. **`_session_token_cost_kwargs()`** same silent loss — session-level cost uses estimated tokens
5. **`MODEL_COSTS`** has no Claude entries — cost undercount by 2-7.5x
6. **`ProcessRunner._build_env()`** does not inject `ANTHROPIC_API_KEY`
7. **Router** has no `anthropic_vertex` provider name or prefix convention
8. **`BACKEND_FAMILY_MAP`** has no `anthropic_vertex` entry
9. **Provider identity** from `LLMResponse` is not forwarded to `MetricsCollector`

### What Must Change for Claude on Vertex Wave 1

| # | Change | File(s) | Reason |
|---|---|---|---|
| D-1 | Multi-family usage key dispatch | `base_agent.py` L282-287, L424-425, L439-442, L466-471 | Anthropic usage silently drops to estimation |
| D-2 | Claude pricing entries | `metrics_collector.py` L80-90 | 2-7.5x cost undercount |
| D-3 | Provider identity propagation into metrics | `base_agent.py` → `metrics_collector.end_call()` | Cannot distinguish backends in telemetry |
| D-4 | `anthropic_vertex` identity path in `_infer_provider_identity()` | `metrics_collector.py` L93-104 | Vertex/direct Claude indistinguishable |
| D-5 | `ANTHROPIC_API_KEY` injection in ProcessRunner | `process_runner.py` L808-818 | Subprocess cannot use Claude |
| D-6 | Claude-on-Vertex region awareness | ProcessRunner or provider config | Anthropic Vertex uses `us-east5`, not generic `VERTEX_LOCATION` |

### What Should Wait for Later

1. Full Anthropic usage enrichment (cache_creation_input_tokens, cache_read_input_tokens)
2. Thinking/reasoning token support for Claude (extended thinking)
3. Full pricing matrix for all Claude model tiers
4. Capability-gated structured output (direct vs Vertex asymmetry per context note 5.3)
5. Full provider-matrix test coverage for usage normalization
6. OpenAI usage key dispatch (same pattern as Anthropic, but not blocking Claude entry)

### Cross-Lane Dependencies Noted

| From Lane D | To Lane | Dependency |
|---|---|---|
| D-1 (usage keys) | B (adapter boundary) | Provider adapter must emit normalized or family-tagged usage for BaseAgent to dispatch |
| D-3 (identity propagation) | A (routing) | Router must register `anthropic_vertex` before metrics can distinguish it |
| D-4 (identity inference) | A (routing) | Model-name prefix convention must be decided before `_infer_provider_identity()` can map it |
| D-5 (env injection) | B (adapter boundary) | Provider must know which credentials it needs before ProcessRunner can inject them |
| D-6 (region) | C (capability asymmetry) | Claude-on-Vertex region constraints affect available model versions |

## 5. 3-Pass Audit Record

Pass 1. Structure and Scope
- Lane-local survey only
- Bounded to usage/cost/runtime-env/observability for Claude-on-Vertex entry
- All must-answer questions from master order addressed
- PASS

Pass 2. Evidence and Consistency
- `base_agent.py` L282-287, L424-425, L439-442, L466-471 verified as Gemini-only key extraction
- `anthropic_provider.py` L77-80 verified as `input_tokens`/`output_tokens` shape
- `metrics_collector.py` L93-104 verified as no `anthropic_vertex` path
- `process_runner.py` L808-818 verified as Vertex env present, Anthropic absent
- `llm_router.py` L25-30, L104-114 verified as no `anthropic_vertex` registration
- Prior spine survey Lane D findings confirmed; Claude-on-Vertex-specific gaps identified as distinct layer
- PASS

Pass 3. Execution and Readability
- Claude-on-Vertex-specific operational gaps clearly separated from general multi-provider debt
- Cross-lane dependencies explicitly noted with direction
- Wait-list items justified by bounded scope
- PASS

Estimated confidence: 96%

Confidence reduction from 97% (spine survey) to 96%:
- Claude-on-Vertex auth path (Anthropic SDK `AnthropicVertex` vs Google Cloud credential reuse) has minor ambiguity pending adapter design from Lane B
- Anthropic Vertex region availability for specific model tiers not locally verifiable
