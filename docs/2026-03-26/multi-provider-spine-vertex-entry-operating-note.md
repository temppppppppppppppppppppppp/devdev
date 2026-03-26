# Multi-Provider Spine + Vertex Entry Operating Note

Date: 2026-03-26
Status: final
Type: system-track operating note
Scope: today's Vertex entry and the architecture required to survive later Claude/OpenAI rollout

## 1. Why This Note Exists

The system is about to enter `Vertex AI` today.

Planned near-term expansion:

- today: `Gemini on Vertex`
- within about a week: `Claude Code` / Anthropic lane
- later: `OpenAI`

So the immediate question is not only:

- "How do we make Vertex work today?"

but also:

- "How do we avoid baking today's Vertex work into another Gemini-only architecture?"

This note fixes the answer:

- today's work may be bounded to Vertex entry
- but the architecture must already follow a multi-provider spine

## 2. Short Answer

Yes, this should be documented and treated as an architectural rule now.

The correct shape is:

- `backend`
- `family`
- `capability`

Not:

- one flat provider enum like `gemini / vertex / claude / openai`

That flat model becomes brittle immediately once:

- Gemini exists on both direct API and Vertex
- Claude exists on Anthropic direct and later Vertex
- OpenAI has model-specific feature asymmetry

## 3. The Three-Axis Spine

### 3.1 Backend

Backend answers:

- who serves the request
- which auth/transport surface is used

Current and near-term useful values:

- `google_direct`
- `google_vertex`
- `anthropic_direct`
- `anthropic_vertex`
- `openai_direct`

### 3.2 Family

Family answers:

- what model semantics we are dealing with

Current and near-term useful values:

- `gemini`
- `claude`
- `gpt`

### 3.3 Capability

Capability answers:

- what the selected model/backend pair can actually do

Minimum useful capability set:

- `structured_output`
- `thinking`
- `prompt_cache`
- `tool_use`
- `vision`
- `long_context`

This matters because support is not uniform:

- not every OpenAI model supports the same structured output
- Claude direct and Claude on Vertex are similar but not identical
- Gemini direct and Gemini on Vertex are close, but still backend-distinct

## 4. The Main Rule

`Vertex is a backend, not a model family.`

So today's entry should not create a runtime identity like:

- `provider = vertex`

It should create identities like:

- `backend=google_vertex, family=gemini`

Later:

- `backend=anthropic_direct, family=claude`
- `backend=openai_direct, family=gpt`

## 5. What Must Stay Provider-Neutral

The app layer should build one neutral request contract first.

Suggested request fields:

- `temperature`
- `top_p`
- `max_output_tokens`
- `system`
- `json_mode`
- `response_schema`
- `reasoning_hint`
- `timeout_ms`
- `cache_hint`

The app layer should not directly construct:

- Gemini-native config objects
- Anthropic-native request objects
- OpenAI-native request objects

Those should be compiled only at the provider adapter boundary.

## 6. Where Provider-Specific Differences Belong

Provider-specific differences belong in adapters.

That means:

- `BaseAgent` should not become a forest of `if gemini / if claude / if openai`
- request compilation should happen inside provider/back-end adapters
- feature fallbacks should be capability-driven, not ad hoc prompt branching

Good:

- app creates neutral request
- adapter compiles request for provider/backend
- adapter normalizes usage

Bad:

- app directly builds Gemini `ThinkingConfig`
- app assumes all providers use the same schema mechanism
- app assumes caching/thinking/JSON are universal

## 7. Usage and Cost Normalization

Usage must be normalized at the provider boundary.

Shared target shape:

- `input_tokens`
- `output_tokens`
- `cached_tokens`
- `thinking_tokens`
- `total_tokens`
- `total_cost_usd`
- `provider`
- `model`

Why this matters:

- the system already uses cost/usage telemetry operationally
- if Vertex, Claude, and OpenAI each surface usage differently, local metrics drift immediately
- this is the easiest place to create invisible billing and observability errors

## 8. What Today Should Actually Do

Today's goal is not "finish multi-provider."

Today's goal is:

- enter `Gemini on Vertex`
- do it in a way that does not block later Claude/OpenAI rollout

So today's bounded implementation should mean:

1. `google_vertex` becomes a first-class backend
2. `gemini` remains the family
3. request compilation for that path stays adapter-owned
4. usage normalization is shared
5. current runtime behavior remains stable for existing Gemini-direct lanes

## 9. What Today Should Explicitly Not Do

Do not:

- create a flat `vertex` provider abstraction that hides family semantics
- widen every prompt/runtime path for all providers at once
- design the whole system around one temporary Gemini-on-Vertex shortcut
- assume Claude/OpenAI feature parity before capability gating exists

Today's work should be a bounded step on the multi-provider spine, not a rushed all-provider rollout.

## 10. Recommended Rollout Order

Recommended order:

1. define/lock the spine:
   - backend
   - family
   - capability
2. land `Gemini on Vertex`
3. normalize usage and capability handling
4. add `Anthropic direct`
5. add `OpenAI direct`
6. only then add `Anthropic on Vertex` if still needed

Reason:

- Gemini direct and Gemini Vertex are the closest pair
- Anthropic direct is cleaner than Anthropic-on-Vertex for first adoption
- OpenAI adds another capability asymmetry axis
- Anthropic-on-Vertex is where fake abstraction is easiest if introduced too early

## 11. Operational Consequence

From this point on:

- local code changes should be reviewed against the multi-provider spine
- today's Vertex work is allowed
- but new Gemini-only hardcoding is not

In practical terms:

- bounded Vertex entry is good
- Gemini-shaped architecture drift is bad

## 12. Single Summary

Today is a `Vertex entry` day, not a `Gemini-only recommitment` day.

The correct move is:

- implement `Gemini on Vertex`
- inside a spine that already separates
  - backend
  - family
  - capability

So later Claude/OpenAI rollout is additive instead of painful.

In short:

`today's solution must already be shaped like a multi-provider system.`
