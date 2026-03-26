Date: 2026-03-26
Status: final (3-pass audited, context note)
Document Type: system-track operating note
Canonical Path: `docs/2026-03-26/llm-multi-provider-context-note.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-26/model-switch-schema-contract-compatibility-survey.md`
Evidence Basis:
- `config/models.yaml`
- `modules/core/models_config.py`
- `modules/core/llm_provider.py`
- `modules/core/llm_router.py`
- `modules/core/llm_schema.py`
- `modules/core/response_schemas.py`
- `modules/core/providers/{gemini,vertex,anthropic,openai}_provider.py`
- `modules/domain/agents/base_agent.py`
- `modules/api/process_runner.py`
- `modules/core/metrics_collector.py`
- `tests/test_llm_router.py`
- Anthropic official docs for Messages API, Claude on Vertex AI, Structured Outputs, and Features Overview
- Google Cloud official docs for Google Gen AI SDK on Vertex AI
- OpenAI official model docs showing feature availability by model

Commit State:
- Baseline Commit: `d82631f3163c7ba62d48dc80ee2d707485b04373`
- Baseline Dirty Summary: `clean workspace`

## 1. Purpose
- Capture the decision context behind the question: "Can Geuldobi use Gemini, Vertex, Claude, and OpenAI elegantly at the same time?"
- Distinguish the architectural shape that stays clean from the shape that will drift into provider-specific branches.
- Record the current local constraints so a later implementation wave does not restart from vague intuition.
- Fix the current near-term target: make `OpenAI / Claude / Vertex AI / Gemini` API usage possible first.
- Keep lower-priority ideas and adjacent improvement lanes available, but out of the main execution focus.

## 2. Short Answer
Yes, a multi-provider runtime is feasible and can stay clean.

It does **not** stay clean if `vertex`, `gemini`, `claude`, and `openai` are treated as one flat peer list.

The clean shape is:
- `backend / transport` is one axis
- `model vendor / family` is a second axis
- `capability` is a third axis

In practice:
- `google_direct` and `google_vertex` are backends
- `gemini`, `claude`, `gpt` are model families
- `structured_output`, `thinking`, `prompt_cache`, `tool_use`, `long_context` are capabilities

## 2A. Current Target Scope
The current implementation target is narrow:
- make `OpenAI / Claude / Vertex AI / Gemini` API paths usable
- do this before opening a self-hosted or local-model wave

Out of current target scope:
- self-hosted local model lane
- low-priority local inference optimization
- broader model-governance expansion beyond what is required for the 4 API paths above

## 3. Why `vertex` Is Not a Peer to `claude`
`Vertex` is a serving and authentication surface, not a model family by itself.

Mixing these into one enum causes avoidable confusion:
- `gemini` can run on Google Developer API or Vertex AI
- `claude` can run on Anthropic direct API or Vertex AI
- `openai` is currently a direct API family in this workspace

If the routing key is only `"vertex"` or `"claude"`, the runtime loses the distinction between:
- who serves the request
- who owns the model semantics
- which feature set is actually available

## 4. Current Workspace State

### 4.1 Good Foundations Already Exist
- `config/models.yaml` already separates provider enablement from agent model assignment.
- `modules/core/llm_provider.py` defines provider-neutral `LLMRequest` and `LLMResponse`.
- `modules/core/llm_router.py` already routes by model naming convention.
- `modules/core/llm_schema.py` and `modules/core/response_schemas.py` already contain a partial dict-based schema bridge.

This means the codebase already has the right **outer skeleton** for a multi-provider runtime.

### 4.2 The Main Coupling Still Lives in `BaseAgent`
The practical bottleneck is `modules/domain/agents/base_agent.py`.

Current live assumptions:
- request config is built as `google.genai.types.GenerateContentConfig`
- structured output uses Gemini-style `response_mime_type="application/json"` plus `response_schema`
- thinking uses Gemini `ThinkingConfig`
- prompt caching uses Gemini cache APIs
- token usage aggregation reads Gemini-native keys such as `prompt_token_count` and `candidates_token_count`

So the router layer is provider-aware, but the dominant call path is still Gemini-native.

### 4.3 Current `vertex_ai` Means "Gemini on Vertex"
The current `VertexAIProvider` uses `google.genai.Client(vertexai=True)` and calls `models.generate_content(...)`.

That is a valid Google/Gemini-on-Vertex path.

It is **not** a generic Vertex abstraction and is **not** a Claude-on-Vertex adapter yet.

## 5. External API Context As Of 2026-03-26

### 5.1 Google
Google's official Gen AI SDK documentation says the SDK provides a unified interface for Gemini Developer API and Gemini on Vertex AI, and that code often ports between them with only a few exceptions.

Operational consequence:
- treating `google_direct` and `google_vertex` as the same adapter family is reasonable
- a backend switch inside the Gemini family is relatively cheap

### 5.2 Anthropic
Anthropic's official "Claude on Vertex AI" docs say the Vertex API is nearly identical to the Messages API, with two key differences:
- `model` is specified in the Vertex endpoint URL rather than the body
- `anthropic_version` moves into the request body and must use the Vertex-specific value

Operational consequence:
- `claude_direct` and `claude_vertex` can share most message-shape logic
- they still should not be collapsed into one undifferentiated provider ID

### 5.3 Anthropic Structured Output Availability
Anthropic's structured output and features-overview docs are asymmetric:
- Structured outputs are clearly documented for Claude API and Bedrock
- the features-availability table does not currently list Vertex AI the same way for structured outputs

Operational consequence:
- do not assume "Claude direct structured output" and "Claude on Vertex structured output" are interchangeable without model-by-model validation
- capability gating is required

### 5.4 OpenAI
OpenAI feature support is model-specific, not vendor-wide.

Examples from current official model docs:
- `gpt-4o-mini` supports structured outputs
- `o4-mini-deep-research` does not

Operational consequence:
- OpenAI must be routed by `capability + model`, not just `"openai"`

## 6. Recommended Internal Contract
The clean target is a three-layer contract.

### 6.1 Model Identity
Use an internal identity that separates backend and model family.

Suggested shape:

```text
backend: google_direct | google_vertex | anthropic_direct | anthropic_vertex | openai_direct
family: gemini | claude | gpt
model: concrete snapshot or alias
```

Example:
- `backend=google_vertex, family=gemini, model=gemini-2.5-pro`
- `backend=anthropic_vertex, family=claude, model=claude-opus-4-6`

### 6.2 Capability Set
Resolve a capability object before request dispatch.

Suggested minimum fields:
- `structured_output`
- `strict_tool_use`
- `reasoning_config`
- `explicit_prompt_cache`
- `long_context`
- `vision_input`

This prevents brittle assumptions such as:
- all OpenAI models support structured output
- all Claude-on-Vertex models match Claude direct behavior
- all Vertex paths support the same cache or schema features

### 6.3 Provider-Neutral Request Config
The app should build a neutral config dict first, then let each adapter compile it.

Suggested fields:
- `temperature`
- `top_p`
- `max_output_tokens`
- `system`
- `json_mode`
- `response_schema`
- `reasoning_hint`
- `timeout_ms`
- `cache_hint`

The app layer should stop constructing Gemini-native config objects directly.

### 6.4 Usage Normalization
Normalize usage at the provider boundary into one shared shape:
- `input_tokens`
- `output_tokens`
- `cached_tokens`
- `reasoning_tokens`
- `total_tokens`

This is the smallest high-value hardening step because it removes silent billing and telemetry drift first.

## 7. Recommended Implementation Order
If realization starts later, the order should stay bounded.

1. Normalize usage keys in all providers.
2. Move config construction out of `BaseAgent` into adapter-owned compilation.
3. Add capability detection and capability-aware fallback.
4. Treat caching as per-provider optional behavior, not universal contract.
5. Add new backends in this order:
   - Gemini direct / Gemini Vertex family normalization
   - Anthropic direct
   - OpenAI direct
   - Anthropic on Vertex

Reason:
- Google direct and Google Vertex are the closest pair
- Anthropic direct is simpler than Anthropic on Vertex in the current codebase
- Anthropic on Vertex is the easiest place to create a false abstraction if introduced too early

## 8. Mainline Supporting Lanes
These are still relevant to the 4-API target and stay in the main body because they directly affect rollout viability.

### 8.1 Credential and Launch Contract
`ProcessRunner` currently injects Google API keys and Slack webhook values, but not equivalent Anthropic/OpenAI/Vertex credentials.

Local evidence:
- `modules/api/process_runner.py` writes `GOOGLE_API_KEY` and `GOOGLE_API_KEY_{i}` only
- there is no parallel input-to-env contract for `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, or `GOOGLE_APPLICATION_CREDENTIALS`

Operational consequence:
- even if provider adapters exist, the desktop/control-plane path will remain Gemini-biased until the runtime launch contract is widened

### 8.2 Model Metadata SSOT
`models.yaml` and `models_config.py` currently work mainly as role-to-model string maps plus fallback chain.

Local evidence:
- `modules/core/models_config.py` defines inline defaults as concrete Gemini aliases
- the loaded contract shape exposes source provenance, but not capability metadata

Recommended expansion:
- `backend`
- `family`
- `capabilities`
- `context_window`
- `pricing_tier`
- `region_scope`
- `supports_structured_output`
- `supports_reasoning`

Operational consequence:
- without metadata SSOT, routing logic will leak back into code branches and model-name parsing

### 8.3 `BaseAgent` Responsibility Pressure
`BaseAgent` currently combines too many policy surfaces:
- request compilation
- retry and fallback
- key rotation
- prompt caching
- usage normalization
- metrics handoff
- JSON repair

Operational consequence:
- each added provider increases the change surface of one owner file instead of staying isolated in adapters

Preferred direction:
- split along `request compile / execute / normalize / usage tracking / cache policy`

### 8.4 Schema SSOT Neutralization
The schema bridge exists, but the runtime still speaks Gemini-first in too many places.

Recommended direction:
- provider-neutral dict schema becomes the only authoritative schema form
- Gemini/OpenAI/Claude adapters compile from that dict

Operational consequence:
- this reduces repeat schema rewrites and stops provider-specific structured-output assumptions from spreading across agents

### 8.5 Observability and Cost Attribution
Cost and usage reporting are still mostly Gemini-oriented.

Local evidence:
- `modules/core/metrics_collector.py` only defines Gemini prices plus a default fallback
- Vertex billable normalization only strips Vertex prefixes; it does not add provider-aware billing semantics

Recommended additions:
- provider/backend labels in logs
- model snapshot or alias recorded at call time
- request IDs where the SDK exposes them
- region and cache-hit state where available

Operational consequence:
- without this, a multi-provider runtime may "work" while silently degrading operator trust in token and cost reports

### 8.6 Provider-Matrix Tests
Current router/provider tests are a good start, but they validate adapters mostly in isolation.

Local evidence:
- `tests/test_llm_router.py` checks enable/disable behavior and per-provider fake-SDK normalization
- it does not yet assert one shared neutral contract across providers for the same request class

Recommended matrix surfaces:
- structured JSON output contract
- finish-reason normalization
- usage normalization
- unsupported-capability rejection
- fallback preservation of schema intent

### 8.7 Task-Lane Model Selection
Current model assignment is mostly role-based:
- `director -> model`
- `writer -> model`
- `analyst -> model`

That is usable, but it is not the cleanest long-term abstraction once providers diversify.

Recommended direction:
- add task-lane selection alongside or above role defaults
- examples: `longform_generation`, `structured_audit`, `cheap_validation`, `continuity_check`, `tool_use`, `high_reasoning`

Operational consequence:
- model choice becomes capability-driven instead of role-string-driven
- provider mixing stays explicit and easier to override

## 9. Appendix Policy
The following belong in appendices unless the target scope changes:
- self-hosted local model lane
- low-priority model-cost optimization beyond the 4 API paths
- future task-lane expansion that is not required for initial API enablement

## 10. Decision Guardrails
- Do not model the world as `gemini | vertex | claude | openai`.
- Do not let `BaseAgent` own provider-native config classes long-term.
- Do not make structured output a vendor-level assumption.
- Do not let token accounting depend on Gemini-only field names.
- Do not force prompt caching into the shared contract as mandatory behavior.

## 11. Operating Consequence
The correct architectural answer is:

`multi-provider yes`

`flat single-axis provider enum no`

For Geuldobi specifically, the clean path is:
- keep the existing router skeleton
- split backend from family
- normalize capabilities and usage
- remove Gemini-native config construction from the app layer

Until that happens, adding all providers "works", but it will not be elegant.

The adjacent operating answer is:
- widen launch-time credential contracts
- promote model metadata to SSOT
- reduce `BaseAgent` policy pressure
- strengthen provider-matrix testing before broad rollout
- leave self-hosted low-priority lanes in appendix status until the 4 hosted API paths are stable

## Appendix A. Self-Hosted Low-Priority Lane
Adding a self-hosted model tier is a realistic option and fits the architecture better than adding yet another top-level hosted vendor branch.

The clean framing is:
- not "China provider"
- but `self_hosted_openai_compat` or `self_hosted_local` as a backend class

Why this framing is better:
- the operational difference is primarily hosting, privacy boundary, latency, and cost profile
- many practical self-hosted stacks expose OpenAI-compatible APIs
- the application can often reuse the same request contract while capability-gating unsupported features

### Appendix A.1 Where It Fits Best
Recommended use:
- low-importance classification
- keyword extraction
- retrieval query rewrite
- draft summarization
- typo or anomaly candidate generation
- low-cost first-pass filtering before escalation to stronger hosted models

Not recommended as final authority for:
- Director final judgment
- world/fact updates
- final PASS/REJECT decisions
- high-stakes continuity adjudication
- schema-critical structured outputs with low tolerance for drift

### Appendix A.2 Current Local Fit
The current easiest insertion path is through the OpenAI-shaped adapter family.

Local evidence:
- `modules/core/providers/openai_provider.py` already uses the OpenAI SDK and normalizes OpenAI-style responses
- however, the provider currently constructs `OpenAI(api_key=...)` only and does not yet expose `base_url` as runtime configuration

Operational consequence:
- a local or cluster model served behind an OpenAI-compatible endpoint is close to the current abstraction
- but one small adapter/config wave is still needed before Geuldobi can point the OpenAI-shaped path at `localhost` or a private inference host

### Appendix A.3 Practical Self-Hosted Shape
The most practical self-hosted path is:
- serve an open-weight model behind an OpenAI-compatible endpoint
- route only low-priority or low-risk tasks there
- escalate to hosted stronger models on failure, low confidence, or unsupported capability

Concrete examples from current official docs:
- vLLM exposes an OpenAI-compatible server
- Ollama exposes OpenAI compatibility
- Qwen3 official materials explicitly document deployment through SGLang, vLLM, and Ollama, and show OpenAI-compatible endpoints

This makes Qwen-family local serving a pragmatic reference path for Geuldobi.

### Appendix A.4 Candidate Guidance
Bounded recommendation:
- for realistic local/edge or modest GPU use, Qwen-family instruct models are the most practical reference
- for bigger self-hosted stacks, larger Qwen variants remain more realistic than treating frontier-scale hosted models as if they were cheap local utilities

Adjacent note:
- a hosted third-party API that is OpenAI-compatible, such as DeepSeek's API, is useful as an interoperability reference
- but it should not be conflated with self-hosted operation because the data-governance and dependency boundary are different

### Appendix A.5 Guardrails For This Lane
- keep this lane capability-gated
- prefer it for prefilter, triage, summarize, and candidate generation
- never silently promote it into final authority work
- preserve a clean fallback or escalation path to stronger hosted models
- treat "OpenAI-compatible" as interface compatibility, not feature parity

## 12. 3-Pass Audit Record
Pass 1. Structure and Scope
- document type is an operating note, not an execution SSOT
- scope now prioritizes the 4 hosted API paths and demotes self-hosted topics into appendix status
- PASS

Pass 2. Evidence and Consistency
- local claims checked against `models.yaml`, `models_config.py`, router/provider files, schema helpers, `BaseAgent`, `process_runner.py`, `metrics_collector.py`, and `tests/test_llm_router.py`
- external claims checked against current official vendor docs
- PASS

Pass 3. Execution and Readability
- compressed to decision-useful context
- migration order, adjacent operating lanes, and guardrails are explicit
- low-priority self-hosted material moved out of the main execution path
- no unsupported implementation promises included
- PASS

## 13. Confidence
Estimated confidence: `97%`

Reasoning:
- high confidence on current workspace coupling because the live code paths were inspected directly
- high confidence on Google and Anthropic backend differences because the official docs are explicit
- high confidence on the adjacent local operating constraints because the affected files were inspected directly
- high confidence on the self-hosted OpenAI-compatible direction because official serving docs explicitly document that interoperability path
- moderate residual uncertainty only on per-model feature parity drift over time, especially structured outputs on third-party surfaces

## 14. External References
- Anthropic Messages API: `https://platform.claude.com/docs/en/build-with-claude/working-with-messages`
- Anthropic Claude on Vertex AI: `https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai`
- Anthropic Structured Outputs: `https://platform.claude.com/docs/en/build-with-claude/structured-outputs`
- Anthropic Features Overview: `https://platform.claude.com/docs/en/build-with-claude/overview`
- Google Gen AI SDK on Vertex AI: `https://docs.cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview`
- OpenAI GPT-4o mini model page: `https://developers.openai.com/api/docs/models/gpt-4o-mini`
- OpenAI o4-mini-deep-research model page: `https://developers.openai.com/api/docs/models/o4-mini-deep-research`
- vLLM OpenAI-Compatible Server: `https://docs.vllm.ai/en/stable/serving/openai_compatible_server/`
- Ollama OpenAI compatibility: `https://docs.ollama.com/api/openai-compatibility`
- Qwen3 official repository: `https://github.com/QwenLM/Qwen3`
- DeepSeek API docs: `https://api-docs.deepseek.com/`
