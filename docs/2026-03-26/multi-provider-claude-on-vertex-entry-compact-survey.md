# Multi-Provider Claude on Vertex Entry Compact Survey

Date: 2026-03-26
Status: final (3-pass audited, parallel survey merged)
Type: system-track parallel survey (merged)
Canonical Path: `docs/2026-03-26/multi-provider-claude-on-vertex-entry-compact-survey.md`
Temp Mirror Path: none
Source Survey Docs:
- `docs/2026-03-26/multi-provider-claude-on-vertex-entry-parallel-survey-master-order.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-a-survey.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-b-survey.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-c-survey.md`
- `docs/2026-03-26/multi-provider-claude-on-vertex-lane-d-survey.md`
- `docs/2026-03-26/llm-multi-provider-context-note.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-operating-note.md`
- `docs/2026-03-26/multi-provider-spine-vertex-entry-compact-survey.md`
- `docs/2026-03-26/multi-provider-vertex-live-operator-check-report.md`

Evidence Basis:
- `config/models.yaml`
- `modules/core/models_config.py`
- `modules/core/llm_router.py`
- `modules/core/llm_provider.py`
- `modules/core/llm_schema.py`
- `modules/core/response_schemas.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/gemini_provider.py`
- `modules/core/providers/openai_provider.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/metrics_collector.py`
- `modules/api/process_runner.py`
- `tests/test_llm_router.py`

Commit State:
- Baseline Commit: `07e9aaf8`
- Baseline Dirty Summary: dirty workspace (`config/models.yaml`, `modules/core/llm_provider.py`, `modules/core/llm_router.py`, provider files, multi-provider docs)

## 1. Findings

### 1.1 What Is Already Claude-on-Vertex-Friendly

- `LLMResponse` already has `provider`, `backend`, and `family` fields in `modules/core/llm_provider.py`
- router/provider registration shape is already extensible in `modules/core/llm_router.py`
- `AnthropicProvider` already has the right message request/response shape for Claude family work
- Vertex-side GCP env passthrough already exists in `modules/api/process_runner.py`
- metrics sink already has neutral token fields and already stores provider/backend/family on `AgentMetric`
- the codebase already proved `Gemini direct` vs `Gemini on Vertex` dual-backend observability, so the spine pattern itself is validated

### 1.2 What Is Still Anthropic-Direct-Only

- `modules/core/llm_router.py` has no `anthropic_vertex` registration, map entry, or routing prefix
- `config/models.yaml` has no `anthropic_vertex` provider section
- `modules/core/providers/anthropic_provider.py` only builds `Anthropic(api_key=...)`, not `AnthropicVertex(project_id=..., region=...)`
- `modules/core/providers/anthropic_provider.py` hardcodes `backend="anthropic_direct"`
- `modules/api/process_runner.py` does not inject `ANTHROPIC_API_KEY`

### 1.3 What Is Still Gemini-Native and Will Hurt Claude Either Way

- `modules/domain/agents/base_agent.py` still compiles Gemini-native `GenerateContentConfig`
- `modules/domain/agents/base_agent.py` still extracts usage from Gemini keys only
- `modules/domain/agents/base_agent.py` still parses thinking from Gemini response shape only
- `modules/core/response_schemas.py` still authors schemas as Gemini `types.Schema`
- `modules/core/providers/anthropic_provider.py` currently ignores `response_schema` / `response_mime_type`
- `modules/core/metrics_collector.py` has no Claude pricing entries

The important merged conclusion from Lane C is:

`the dominant asymmetry is Claude-vs-Gemini code assumptions, not Claude-direct-vs-Claude-on-Vertex`

So Claude on Vertex adds only a small backend/client delta on top of the broader Claude-family readiness gaps.

## 2. What Must Change for Claude on Vertex Now

The smallest realistic Wave 1 is not "full Claude support." It is:

1. Identity / routing admission
   - add `anthropic_vertex` provider identity
   - add one explicit routing prefix convention
   - add provider config section in `config/models.yaml`

2. Adapter boundary
   - add a dedicated `AnthropicVertexProvider` path
   - do not try to force Claude through `VertexAIProvider`
   - do not collapse direct and vertex auth into one dirty conditional unless necessary

3. Minimal runtime safety
   - guard Gemini-specific `response.raw` thinking extraction for non-Gemini families
   - otherwise Claude responses risk being parsed through the wrong raw shape assumptions

4. Minimal observability correctness
   - distinguish `anthropic_direct` vs `anthropic_vertex`
   - add Claude pricing entries
   - stop silently dropping Anthropic usage into heuristic estimation if Wave 1 is expected to be operationally trustworthy

## 3. Recommended Wave Shape

Recommended bounded Wave 1:

- routing/config identity for `anthropic_vertex`
- `AnthropicVertexProvider` introduction
- `AnthropicProvider` small refactor so backend identity is not hardcoded
- non-Gemini raw-response access guard in `BaseAgent`
- minimal Anthropic usage/pricing/metrics identity correction

What should explicitly stay out:

- full provider-neutral request config rewrite
- full schema SSOT migration away from Gemini `types.Schema`
- prompt caching redesign
- full Claude thinking support
- broad OpenAI or future-provider abstraction work

## 4. Dominant Risk

The dominant risk is **not** that Claude on Vertex has a wildly different API.

The dominant risk is that the codebase may admit Claude on Vertex at the routing layer, but still behave like a Gemini-first runtime in:

- schema handling
- usage accounting
- raw response interpretation

That would create a fake success where calls route but operational correctness and structured-output safety are weak.

## 5. Required Investigation Answers

### Q1. Dominant architecture risk if Claude on Vertex is added next?

`routing succeeds, but runtime still assumes Gemini`

### Q2. Main bottleneck?

Tie between:

- missing `anthropic_vertex` identity/adapter path
- Gemini-native runtime assumptions in `BaseAgent` and metrics

### Q3. Smallest bounded Wave 1 that makes Claude on Vertex real without poisoning future work?

`anthropic_vertex routing + AnthropicVertexProvider + minimal non-Gemini runtime/metrics guardrails`

### Q4. What must explicitly stay out of that Wave 1?

- provider-neutral config rewrite
- schema migration rewrite
- prompt cache redesign
- full Claude thinking feature support
- broad all-provider cleanup

### Q5. Next step?

`one execution SSOT`

## 6. Strongest Merge Conclusions By Lane

### Lane A

- `anthropic_vertex` cannot be expressed today
- recommended prefix direction: `anthropic-vertex:claude-*`

### Lane B

- best adapter shape is a separate `AnthropicVertexProvider`, likely via subclass/reuse of current Anthropic logic

### Lane C

- capability gap is mostly Claude-vs-Gemini assumptions, not direct-vs-Vertex differences
- minimum runtime guard: do not let non-Gemini providers hit Gemini raw-shape thinking parsing

### Lane D

- current usage/pricing/metrics path is not trustworthy for Claude
- if Wave 1 is meant to be operational, observability fixes cannot be skipped completely

## 7. Recommendation

Open one bounded execution SSOT now.

That SSOT should be narrower than "Claude support" and broader than "just router registration."

Target it at:

- `anthropic_vertex` identity admission
- `AnthropicVertexProvider`
- minimal non-Gemini runtime guard
- minimal Claude observability correctness

## 8. Mandatory Final Lines

- Dominant Claude-on-Vertex seam: `anthropic_vertex-entry-blocked-by-missing-identity-adapter-and-gemini-native-runtime-assumptions`
- Best next single move: `open-bounded-claude-on-vertex-execution-ssot`
- Should Codex open an execution SSOT now: `yes`

## 9. 3-Pass Audit Record

Pass 1. Structure and Scope
- merged survey type is correct
- lane boundaries remain visible
- recommendation stays bounded to Claude-on-Vertex entry, not broad provider redesign
- PASS

Pass 2. Evidence and Consistency
- lane-local claims were checked against live code for:
  - missing `anthropic_vertex`
  - Gemini-only usage extraction
  - lack of Anthropic env injection
  - absence of Claude pricing entries
- no contradiction found between lane conclusions
- PASS

Pass 3. Execution and Readability
- findings-first structure preserved
- "already friendly / still direct-only / still Gemini-native" separation is explicit
- next move is singular and operationally actionable
- PASS

Estimated confidence: 97%
