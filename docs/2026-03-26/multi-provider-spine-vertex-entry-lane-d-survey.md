# Lane D Survey: Usage / Cost / Telemetry Normalization

Date: 2026-03-26
Status: final (3-pass audited, lane-local survey reconstructed during merge audit)
Type: system-track parallel survey lane
Lane Owner: Terminal 4
Canonical Path: `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-d-survey.md`
Source Master Order: `docs/2026-03-26/multi-provider-spine-vertex-entry-parallel-survey-master-order.md`

Evidence Basis:
- `modules/domain/agents/base_agent.py`
- `modules/core/metrics_collector.py`
- `modules/api/process_runner.py`
- `modules/core/llm_provider.py`

Commit State:
- Baseline Commit: `07e9aaf8`
- Resume Drift Summary: dirty workspace (`config/models.yaml`, `modules/core/llm_provider.py`, `modules/core/llm_router.py`, `modules/core/providers/vertex_provider.py`, survey docs)

## 1. Lane D Core Question

If Vertex enters now, do usage/cost fields stay coherent enough for later multi-provider operation?

## 2. Findings

### 2.1 Metrics Sink Already Wants Neutral Token Fields

- `metrics_collector.py:207-240` accepts `input_tokens`, `output_tokens`, `cached_tokens`, `thinking_tokens`
- `metrics_collector.py:292-310` calculates cost from those neutralized fields

This is good. The sink is not inherently Gemini-only.

### 2.2 BaseAgent Still Normalizes From Gemini Keys Only

- `base_agent.py:282-287` defines `_USAGE_KEYS` as:
  - `prompt_token_count`
  - `candidates_token_count`
  - `thoughts_token_count`
  - `cached_content_token_count`
- `base_agent.py:424-425` accumulates only those keys
- `base_agent.py:439-442` maps only those keys into neutral metrics payload
- `base_agent.py:467-470` also maps only those same Gemini-shaped fields for session token/cost reporting

This means:

- Gemini and Vertex work because they share the same usage shape
- Anthropic/OpenAI usage would not survive this path cleanly without fallback estimation or silent loss

### 2.3 Vertex Pricing Is Still Treated as Gemini Pricing

- `metrics_collector.py:72-82` contains Gemini-only pricing entries
- `metrics_collector.py:85-90` strips Vertex prefixes and bills the bare model name
- `metrics_collector.py:306` falls back to `MODEL_COSTS["default"]` when a model is unknown

Operationally:

- Vertex calls will be billed as Gemini by normalized model name
- That may be acceptable if intentionally equivalent
- but it is still observability debt unless explicitly confirmed

### 2.4 Provider Identity Does Not Reach Metrics

- `llm_provider.py:16-28` already has `provider`, `backend`, `family` on `LLMResponse`
- providers currently set only `provider=...`
- `base_agent.py` metric payload only carries token counts, not provider/backend/family
- `metrics_collector.end_call()` has no provider/backend/family arguments

So even though identity fields exist at the envelope layer, observability still cannot distinguish:

- Gemini direct vs Gemini on Vertex
- Claude vs GPT in downstream metrics summaries

### 2.5 ProcessRunner Environment Injection Is Still Google API Key Only

- `process_runner.py:780-808` builds subprocess env
- it injects:
  - `GEULDOBI_RUN_ID`
  - `GOOGLE_API_KEY`
  - `GOOGLE_API_KEY_2..9`
  - `SLACK_WEBHOOK_URL`
- it does **not** inject:
  - `VERTEX_PROJECT_ID`
  - `VERTEX_LOCATION`
  - `GOOGLE_APPLICATION_CREDENTIALS`
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`

This is the main Vertex-specific operational gap in the current workspace.

## 3. Must-Answer Questions

### Q1. How is usage currently normalized?

The final sink is provider-neutral, but the normalization bridge in `BaseAgent` is still Gemini-shaped.

### Q2. Are token/cost fields provider-neutral enough today?

Only for Gemini and Vertex. Not yet for Claude/OpenAI.

### Q3. Does today's Vertex entry risk hidden observability drift?

Yes, in three places:

1. Vertex cost is billed via Gemini pricing assumptions
2. provider/backend/family identity is not carried into metrics
3. subprocess launches cannot receive Vertex credential env vars through `ProcessRunner`

## 4. Lane D Verdict

### Already Multi-Provider-Friendly

1. Metrics sink fields are neutral
2. Cost calculation accepts neutral token counts
3. `LLMResponse` already has provider/backend/family slots

### Still Gemini-Native or Under-Normalized

1. Usage extraction in `BaseAgent`
2. Pricing table contents
3. Metrics attribution shape
4. `ProcessRunner` env contract

### What Must Change for Vertex Wave 1

1. Inject Vertex env vars in `ProcessRunner._build_env`
2. Decide and encode Vertex pricing path explicitly
3. Carry provider/backend/family into metrics or runtime audit payloads

### What Should Wait for Later Providers

1. Anthropic/OpenAI usage key dispatch
2. Full pricing matrix
3. Unified provider-wide observability schema expansion

## 5. 3-Pass Audit Record

Pass 1. Structure and Scope
- Lane-local survey only
- Bounded to usage/cost/telemetry normalization
- PASS

Pass 2. Evidence and Consistency
- `base_agent.py`, `metrics_collector.py`, `process_runner.py`, `llm_provider.py` rechecked against live workspace
- Verified that sink is neutral but ingress normalization is Gemini-shaped
- PASS

Pass 3. Execution and Readability
- Vertex-specific operational gap and later-provider debt clearly separated
- Merge consequence is actionable
- PASS

Estimated confidence: 97%
