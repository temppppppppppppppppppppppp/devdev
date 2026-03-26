# Multi-Provider Spine + Vertex Entry Compact Survey

Date: 2026-03-26
Status: final (3-pass audited, parallel survey merged and re-audited)
Type: system-track parallel survey (merged)
Canonical Path: `docs/2026-03-26/multi-provider-spine-vertex-entry-compact-survey.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-26/llm-multi-provider-context-note.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-operating-note.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-parallel-survey-master-order.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-a-survey.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-b-survey.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-c-survey.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-lane-d-survey.md`

Evidence Basis:
- `config/models.yaml`
- `modules/core/models_config.py`
- `modules/core/llm_router.py`
- `modules/core/llm_provider.py`
- `modules/core/llm_schema.py`
- `modules/core/response_schemas.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/openai_provider.py`
- `modules/domain/agents/base_agent.py`
- `modules/api/process_runner.py`
- `modules/core/metrics_collector.py`
- `tests/test_llm_router.py`

Commit State:
- Baseline Commit: `07e9aaf8`
- Baseline Dirty Summary: workspace already dirty (`config/models.yaml`, `modules/core/llm_generate.py`, `modules/core/llm_provider.py`, `modules/core/llm_router.py`, `modules/core/providers/vertex_provider.py`)
- Merge Audit Note: original lane-local outputs for A/D were missing; they were re-audited and reconstructed from live workspace evidence during merge

## 1. Findings

### 1.1 What Is Already Multi-Provider-Friendly

- `llm_router.py:10-29` already has provider registration plus `BACKEND_FAMILY_MAP`
- `llm_router.py:104-129` already routes Gemini, Vertex, Claude, and GPT families by prefix
- `config/models.yaml:1-16` already has `vertex_ai.enabled: true` with `project_id_env`, `location_env`, and `credentials_env`
- `llm_provider.py:7-28` already defines provider-neutral `LLMRequest` / `LLMResponse`, and `LLMResponse` already has `provider`, `backend`, `family` fields
- `vertex_provider.py:54-88` is already a real Vertex adapter, not a stub
- `tests/test_llm_router.py:30-41,146-203` already covers Vertex resolution and provider generate path
- `metrics_collector.py:207-240` already wants neutral metrics fields: `input_tokens`, `output_tokens`, `cached_tokens`, `thinking_tokens`

### 1.2 What Is Still Gemini-Native

- `base_agent.py:1057-1077,1340-1355,1480-1488,2145-2163` still builds `google.genai.types.GenerateContentConfig` at 4 sites
- `response_schemas.py` still authors structured output as Gemini `types.Schema`
- `base_agent.py:282-287,424-425,439-442,467-470` still normalizes usage from Gemini-shaped keys only
- `base_agent.py:1385-1393,2182-2195` still parses thinking from Gemini response structure
- `models_config.py:11-41` inline defaults are still Gemini-only
- `metrics_collector.py:72-82` pricing table is still Gemini-only

### 1.3 What Must Change for Vertex Entry Now

The old conclusion "enable Vertex first" is stale. Vertex is already enabled in `config/models.yaml`.

The smallest real Wave 1 is now:

1. `process_runner.py:780-808`
   - inject Vertex env vars for subprocess launches
   - at minimum: `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `GOOGLE_APPLICATION_CREDENTIALS`
2. `vertex_provider.py:115-136` plus sibling providers
   - populate `backend` / `family` on `LLMResponse`, not only `provider`
3. `base_agent.py` -> `metrics_collector.py`
   - propagate provider identity into metrics or runtime audit payloads so Gemini-direct vs Gemini-on-Vertex is visible

Recommended but still bounded in the same wave:

4. `metrics_collector.py:72-82`
   - make Vertex pricing explicit instead of inheriting Gemini pricing by silent normalization

### 1.4 What Should Wait for Later Providers

- provider-neutral config dict compilation instead of Gemini `GenerateContentConfig`
- schema SSOT migration from Gemini `types.Schema` to dict/json-schema-first
- Anthropic/OpenAI usage key normalization in `BaseAgent`
- provider-neutral content model
- capability negotiation layer
- full pricing matrix for all providers

## 2. Survey Topology

4 lanes were merged:

| Lane | Scope | Status |
|------|-------|--------|
| A | Identity / Config / Routing | reconstructed during merge audit |
| B | BaseAgent / Request Construction | present |
| C | Provider Adapter Boundary | present |
| D | Usage / Cost / Telemetry | reconstructed during merge audit |

## 3. What Is Already Multi-Provider-Friendly

### 3.1 Identity / Routing

- `llm_router.py:25-29` already separates backend from family
- `llm_router.py:104-114` already resolves `vertexai:` as `vertex_ai`
- `config/models.yaml:1-16` already has live Vertex provider config and it is enabled

### 3.2 Provider Boundary

- `vertex_provider.py:54-88` builds a real Vertex client with either Express API key or project/location/credentials
- `vertex_provider.py:89-136` already issues live `generate_content()` calls and returns normalized `LLMResponse`
- `anthropic_provider.py` and `openai_provider.py` already exist, so the codebase is beyond single-provider-only shape

### 3.3 Schema Bridge

- `llm_schema.py:21-96` already provides `dict <-> Gemini Schema` conversion
- `openai_provider.py:57-70` already uses the dict bridge for JSON schema output

### 3.4 Neutral Metrics Sink

- `metrics_collector.py:207-240` and `292-310` already use neutral token fields and neutral cost calculation inputs

## 4. What Is Still Gemini-Native

### 4.1 Request Compilation

Lane B is still the dominant future debt:

- `base_agent.py:1057-1077`
- `base_agent.py:1340-1355`
- `base_agent.py:1480-1488`
- `base_agent.py:2145-2163`

All 4 build Gemini-native config objects directly.

### 4.2 Usage Key Extraction

Lane D remains the dominant observability debt:

- `base_agent.py:282-287`
- `base_agent.py:424-425`
- `base_agent.py:439-442`
- `base_agent.py:467-470`

This path is still safe for Gemini and Vertex, but not for Claude/OpenAI.

### 4.3 Identity Propagation Stops Midway

- `llm_provider.py:16-28` already has `provider/backend/family`
- providers currently populate only `provider`
- metrics do not consume any of those identity fields

So the spine exists, but it is not carried far enough downstream to become operationally visible.

### 4.4 Launch Contract

- `process_runner.py:780-808` still injects only `GOOGLE_API_KEY`, `GOOGLE_API_KEY_2..9`, and `SLACK_WEBHOOK_URL`
- Vertex subprocess runs still cannot rely on the runner to inject `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, or `GOOGLE_APPLICATION_CREDENTIALS`

## 5. Required Investigation Answers

### Q1. Dominant architecture risk if Vertex is added quickly today?

Not "Vertex itself breaks." The real risk is that Vertex now works just well enough to hide the remaining Gemini-shaped debt before Claude/OpenAI arrive.

### Q2. Main bottleneck?

For today's Vertex entry:

- `process_runner` env contract
- provider identity propagation into observability

For next week's Claude/OpenAI survivability:

- BaseAgent Gemini-native request construction
- Gemini-only usage-key extraction

### Q3. Smallest bounded Wave 1 that admits Gemini on Vertex without poisoning future work?

**Wave 1: Vertex Runtime Entry + Identity/Observability Wiring**

Essential:

1. subprocess Vertex env injection
2. `LLMResponse.backend/family` population
3. provider/backend/family propagation into metrics or runtime audit

Recommended:

4. explicit Vertex pricing normalization

### Q4. What must explicitly stay out of Wave 1?

- config builder abstraction rewrite
- schema migration rewrite
- Anthropic/OpenAI usage dispatch rewrite
- capability negotiation
- full launch contract widening for every future provider

### Q5. Should the next step be no action, one execution SSOT, or one narrower follow-up survey?

**One execution SSOT.**

The remaining Wave 1 is small, bounded, and current-code-grounded.

## 6. Cross-Lane Dependencies

| From | To | Dependency |
|------|----|------------|
| A | D | router/model normalization affects billing identity and pricing lookup |
| B | C | BaseAgent still compiles Gemini-native config that adapters consume |
| B | D | BaseAgent still controls usage-field mapping before metrics |
| C | D | providers emit heterogeneous usage shapes and incomplete identity fields |

## 7. Risk Summary

| Risk | Severity | Vertex Impact | Claude/OpenAI Impact |
|------|----------|---------------|----------------------|
| BaseAgent config compilation is Gemini-native | high | none now | blocks clean entry |
| Usage extraction is Gemini-only | high | low | high |
| Provider identity not propagated into metrics | medium | medium | high |
| ProcessRunner env contract is Google-API-key-only | high | high | medium |
| Pricing table is Gemini-only | medium | medium | high |

## 8. Mandatory Final Lines

- Dominant multi-provider seam: `vertex-runtime-env-plus-identity-propagation`
- Best next single move: `execution-ssot-for-vertex-runtime-entry-and-observability`
- Should Codex open an execution SSOT now: `yes`

## 9. 3-Pass Audit Record

Pass 1. Structure and Scope
- merged survey type is correct
- lane ownership and missing-lane reconstruction are explicit
- findings are bounded to provider/backend/runtime coupling
- PASS

Pass 2. Evidence and Consistency
- stale claim "`vertex_ai.enabled: false`" removed after live recheck of `config/models.yaml`
- stale recommendation "add backend/family fields to LLMResponse" corrected because fields already exist in `llm_provider.py`
- remaining identity gap re-scoped to propagation, not field creation
- env-contract claim rechecked against `process_runner.py:780-808`
- PASS

Pass 3. Execution and Readability
- wave boundary is clear and small
- immediate Vertex needs are separated from later Claude/OpenAI debt
- next operational consequence is explicit
- PASS

Estimated confidence: 97%
