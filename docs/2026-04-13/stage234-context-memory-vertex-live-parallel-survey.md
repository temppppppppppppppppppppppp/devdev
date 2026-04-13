# Stage234 Context Memory / Vertex Live Parallel Survey

- Date: 2026-04-13
- Scope: current multi-provider runtime state, provider-native session memory options, Vertex Live / Sessions / Memory Bank applicability, and a practical context-memory improvement path for the Stage2/3/4 pipeline
- Mode: survey-only, parallel evidence collection across local code/state plus official provider documentation
- Baseline Commit: `2b7cb64f2d1fe2cd1152806a5cc37795609f9755`
- Baseline Dirty Summary: `dirty workspace; active hotspots: Stage3 runtime/orchestrator/validator, Stage4 retry/post-select surfaces, failure analyzer, docs/temp mirrors, provider routing`
- 3-pass audit: completed before save
- Confidence: 96%

## Scope

This survey answers four questions:

1. what our current memory/state situation actually is
2. whether we are still too stateless at the provider layer
3. whether `Vertex Live API` is a good next move for this pipeline
4. what the most practical context-memory improvement path is from here

This document does not patch code. It fixes the current architecture story and narrows the next implementation choices.

## Evidence Sources

### Local code and runtime substrate

- `config/models.yaml`
- `main_a.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/openai_provider.py`
- `modules/core/llm_router.py`
- `modules/core/context_advisor.py`
- `modules/core/vec_memory.py`
- `modules/core/session_logger.py`
- `modules/core/project_support.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/semantic_query_broker.py`
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/director_caching.py`

### Official provider docs

- OpenAI conversation state:
  - https://developers.openai.com/api/docs/guides/conversation-state
- Anthropic prompt caching:
  - https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Anthropic context windows:
  - https://platform.claude.com/docs/en/build-with-claude/context-windows
- Vertex AI Sessions:
  - https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview
- Vertex AI Context Cache:
  - https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview
- Vertex Live API session management:
  - https://cloud.google.com/vertex-ai/generative-ai/docs/live-api/start-manage-session
- Vertex Memory Bank:
  - https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/quickstart-api
- Vertex Live + MemoryCorpus:
  - https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/use-rag-in-multimodal-live

## Executive Summary

- We are not purely stateless today.
- Our current durable memory story is mostly `DB truth + anchors + VecMemory + ContextAdvisor + cross-stage packets`, not provider-native session memory.
- The provider layer is still mostly stateless:
  - Anthropic direct: no prompt caching or conversation/session state is wired
  - Vertex provider: plain `generate_content`; no Live API / Sessions / Memory Bank / Context Cache wiring
  - OpenAI provider: plain `responses.create`; no conversation-state threading is wired
- We still carry old Gemini/Vertex cached-context code paths in the agent layer, but they are now partially stale against Sonnet-direct high-intelligence routing.
- `Vertex Live API` is worth considering, but not as the primary memory fix for the Stage2/3/4 production pipeline.
- The most practical improvement path is:
  1. keep hard truth in our DB/anchor/fact-ledger layer
  2. make provider capability handling explicit
  3. add prompt/prefix caching for Sonnet lanes
  4. add a provider-neutral session-memory envelope
  5. treat Vertex Live / Memory Bank as optional sidecar memory, not SSOT

## Current State

### 1. Our pipeline is already doing nontrivial memory work outside the providers

The current stack is not memory-empty.

What we already have:

- durable stage truth in SQLite / DB surfaces
- project anchors through `VecMemory.save_v20_anchor()` / `load_v20_anchor()`
- vector-backed semantic retrieval through `VecMemory`
- stage-aware retrieval planning through `ContextAdvisor`
- structured relationship / fact reconstruction through `SemanticQueryBroker`
- retry packets and truth pins across Stage3/4
- session telemetry through `SessionLogger`

Operationally this means:

- the pipeline already has a real memory architecture
- but that architecture is mostly app-managed, not provider-managed

### 2. Provider-native state is still weak

#### Anthropic direct

`modules/core/providers/anthropic_provider.py` currently does a plain `Anthropic.messages.create(...)`.

What is missing:

- no prompt caching support
- no provider-side conversation threading
- no session/container abstraction
- no long-lived reusable prefix handling

Result:

- every Sonnet call is effectively a fresh stateless request at the provider layer

#### Vertex provider

`modules/core/providers/vertex_provider.py` currently does a plain `client.models.generate_content(...)`.

What is missing:

- no Context Cache usage
- no Agent Engine Sessions usage
- no Live API usage
- no Memory Bank usage

Result:

- current Vertex usage is also mostly stateless at the provider layer

#### OpenAI provider

`modules/core/providers/openai_provider.py` currently uses `responses.create(...)`.

What is missing:

- no `previous_response_id`
- no conversation-state threading
- no server-side conversation reuse

Result:

- OpenAI support is provider-neutral and minimal, not memory-aware

### 3. We still have legacy Vertex cached-context code in the agent layer

This is the most important local architecture nuance.

Evidence:

- `modules/domain/agents/base_agent.py` still has `_get_or_create_context_cache(...)`
- that helper uses Gemini / Vertex cached content creation through `self.client.caches.create(...)`
- `blueprint_ensemble.py`, `chief_writer.py`, `analyst.py`, and `director_caching.py` still try to create and/or consume `cached_content`

But our current high-intelligence lanes are now Sonnet direct:

- `config/models.yaml` routes `chief_writer`, `director`, `blueprint_ensemble`, `three_phase_blueprint_generator`, `four_phase_arc_generator`, and other key producers to `claude-sonnet-4-6`
- the Anthropic provider ignores `cached_content` config entirely

So the current reality is:

- the old cache path is still present
- but it is no longer a clean fit for the current Sonnet-heavy routing
- in Sonnet lanes this path likely degrades to fallback/no-op/error handling rather than true cached-context reuse

This is not catastrophic, but it is now architectural debt.

### 4. Session telemetry exists, but it is not the memory source of truth

`modules/core/session_logger.py` is valuable for observability, replay, and audit.

But it is not our durable truth or retrieval substrate.

That distinction matters:

- `SessionLogger` is good for diagnostics
- `DB + anchors + fact/state packets` are good for durable truth
- provider-native memory would be a convenience and cost/latency optimization layer, not the authority layer

## External Capability Survey

### OpenAI conversation state

Official docs show that OpenAI can preserve conversation state through response chaining such as `previous_response_id`.

This helps for:

- short-lived multi-turn continuity
- reducing the need to resend every recent message manually

But it does not replace:

- hard truth persistence
- our DB-backed fact/state authority
- long-horizon production memory planning

### Anthropic prompt caching

Anthropic officially supports prompt caching.

What it helps with:

- reusing large repeated prompt prefixes
- reducing repeated input cost and latency on stable context blocks

Why it matters to us:

- our current best-quality lanes are now Sonnet direct
- our biggest repeated inputs are exactly the sort of stable context blocks that prompt caching is designed for

This makes prompt caching the single highest-ROI provider-native memory improvement for the current stack.

### Anthropic long context

Anthropic context windows are useful working memory, not durable memory.

That means:

- longer context can reduce truncation pressure
- but it does not remove the need for truth routing, anchors, fact ledgers, or retry packets

### Vertex Sessions

Vertex Agent Engine Sessions officially preserve conversation history and context across interactions.

This is closer to real session memory than plain stateless API calls.

Useful for:

- interactive assistants
- operator-facing chat/session flows
- shorter-lived stateful agent conversations

Less obviously useful for:

- Stage2/3/4 batch production lanes where durable truth already lives in our own system

### Vertex Context Cache

Vertex Context Cache officially supports reusable large-context prefixes and has a default expiration window.

This is helpful for:

- repeated stable prefixes
- cost/latency optimization

This is not the same thing as:

- durable narrative truth
- long-horizon agent memory

### Vertex Live API

Vertex Live API supports session lifecycle management and session resume.

This is attractive when we want:

- low-latency interactive conversations
- realtime or quasi-realtime assistant sessions
- continuity inside one live operator session

But our current Stage2/3/4 pipeline is:

- batch-heavy
- multi-agent
- truth-packet-driven
- DB-authoritative

So `Vertex Live API` is interesting, but not the cleanest first fix for the pain we are feeling today.

### Vertex Memory Bank

Memory Bank is the closest official Vertex feature to persistent memory.

Useful for:

- user-scoped soft memory
- assistant-side long-term recollection
- externalized memory retrieval across sessions

But it still should not outrank:

- our DB truth
- world-state / fact-ledger authority
- stage attempt packets

### Live + MemoryCorpus / RAG

This is useful for multimodal or conversational retrieval sidecars.

It is promising for:

- operator copilots
- research assistants
- sidecar retrieval experiences

It is much less compelling as the immediate primary fix for:

- Stage3/Stage4 production retry churn
- cross-stage truth drift
- authoritative state transport

## Findings

### Finding 1. Our real problem is not zero memory; it is fragmented memory responsibility

We already have:

- hard truth memory
- semantic retrieval memory
- retry/attempt memory
- observability/session telemetry

But these layers are split across:

- DB / anchors
- VecMemory
- ContextAdvisor
- stage runtime packets
- legacy provider-specific cache helpers

This creates two costs:

- repeated context assembly cost
- blurry ownership over what should be provider memory vs app memory

### Finding 2. Sonnet direct made old Vertex context-cache residue partially stale

Before the routing shift, Gemini-style `cached_content` was a plausible optimization for high-intelligence lanes.

Now:

- Sonnet direct is the main high-intelligence engine
- the old cached-content helpers still exist
- but the active provider does not consume those config fields

So the codebase currently contains a memory optimization layer that is no longer aligned with the dominant provider path.

This is now a cleanup and capability-normalization problem.

### Finding 3. Vertex Live API is not the best first move for the main production pipeline

`Vertex Live API` solves a different problem best:

- live interactive stateful sessions
- realtime multimodal or assistant experiences

Our main pain today is:

- repeated stable prompt prefixes
- provider-layer statelessness in batch lanes
- cross-stage truth transport cost
- memory fragmentation across our own orchestration stack

The first move should therefore be:

- prompt/prefix caching for Sonnet
- provider-neutral session-memory envelope
- capability cleanup around old Vertex cache residue

not a direct migration of the core pipeline to `Vertex Live API`

### Finding 4. Provider-native memory should stay secondary to our truth system

This is the most important governance conclusion.

Hard truth should remain in:

- DB
- world state
- fact ledger
- anchors
- stage contracts

Provider-native memory should remain:

- advisory
- performance-oriented
- convenience-oriented

That keeps us aligned with the workspace governance model and protects us against provider drift.

## Recommended Architecture

### Layer A. Hard truth memory

Keep authoritative truth in our own system:

- DB stage/state rows
- fact ledgers
- world-state packets
- anchors
- truth pins
- retry contracts

This layer remains SSOT.

### Layer B. Soft retrieval memory

Keep and continue improving:

- `VecMemory`
- `ContextAdvisor`
- `SemanticQueryBroker`

This layer should answer:

- what is relevant now
- what should be re-injected
- what evidence supports this retry

### Layer C. Provider-native prefix/session helpers

Add provider-native memory only where it clearly helps:

- Anthropic prompt caching for Sonnet stable prefixes
- optional short-lived conversation threading where supported
- explicit capability flags so no provider receives unsupported cache/session config

This layer should be treated as:

- optimization
- convenience
- short-lived working memory

### Layer D. Optional interactive live-memory sidecar

If we later want a more stateful interactive assistant, use:

- Vertex Sessions / Live API / Memory Bank / MemoryCorpus

But keep it as:

- operator-side assistant substrate
- research / debugging / cockpit sidecar

not the main authority path for Stage2/3/4 production truth

## Implementation Options

### Option 1. Lowest-risk, highest-ROI

Introduce a provider capability map and cleanly separate:

- hard truth memory
- soft retrieval memory
- provider-native cache/session features

Then:

- short-circuit stale Gemini cached-context logic for non-Gemini providers
- add Anthropic prompt caching support
- expose cache hit/miss/cached-token observability

Expected value:

- immediate reduction in redundant prompt cost
- less fake/failed cache behavior in Sonnet lanes
- cleaner provider semantics

### Option 2. Medium-risk, likely worthwhile

Add a provider-neutral `session memory envelope` inside our own orchestration layer.

Contents:

- recent-turn compressed summary
- stable truth pins
- active retry directives
- last accepted verdict surface
- per-stage carryover packet

Then:

- inject provider-native conversation/session hints where supported
- keep the envelope itself in our own DB/state plane

Expected value:

- less repeated recomposition overhead
- more stable retry continuity
- no provider lock-in

### Option 3. Targeted Vertex Live sidecar

Use `Vertex Live API` only for a narrow assistant role such as:

- cockpit copilot
- operator debugging assistant
- retrieval-heavy exploratory chat

Expected value:

- better human-facing session continuity
- less stateless pain in interactive ops

Tradeoff:

- does not directly solve core Stage3/4 production memory first

### Option 4. Full provider-memory ambition

Combine:

- Sonnet prompt caching
- provider-neutral session envelope
- optional Vertex Memory Bank sidecar

This is the most capable end-state, but not the first move.

## Recommended Tranches

### Tranche 1. Capability cleanup

Goal:

- make the current stack honest about what each provider can and cannot do

Targets:

- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/openai_provider.py`
- `modules/core/llm_router.py`
- legacy cache call sites in `BaseAgent`, `ChiefWriter`, `BlueprintEnsemble`, `DirectorCachingManager`, and related helpers

Deliverables:

- provider capability map
- explicit no-op / bypass on unsupported cached-context paths
- observability on provider-native cache/session use

### Tranche 2. Sonnet prompt caching

Goal:

- reduce repeated stable-prefix cost in the currently dominant high-intelligence path

Targets:

- stable prompt-prefix builders for Stage3/Stage4
- Anthropic provider support for prompt caching
- cached-token observability

Deliverables:

- Sonnet prompt caching on bounded stable context blocks
- cache hit/miss logging

### Tranche 3. Provider-neutral session memory envelope

Goal:

- reduce stateless pain without surrendering authority to the provider

Targets:

- stage-local recent summary packet
- retry memory packet
- truth pin carryover packet
- optional provider-specific session threading adapter

Deliverables:

- one internal session-memory contract
- one adapter layer per provider family

### Tranche 4. Optional Vertex Live sidecar

Goal:

- add a stateful interactive assistant layer without rewriting the production pipeline around it

Targets:

- cockpit/debug assistant
- retrieval-heavy operator flows
- optional Memory Bank / MemoryCorpus exploration

Deliverables:

- bounded proof harness
- explicit sidecar scope

## Recommendation

The current recommendation is:

1. do not pivot the main Stage2/3/4 production pipeline to `Vertex Live API` first
2. first clean the memory architecture we already own
3. add Sonnet prompt caching next
4. add a provider-neutral session-memory envelope after that
5. explore `Vertex Live API` only as a bounded operator-side sidecar unless later proof says otherwise

This path gives us the best mix of:

- memory improvement
- low provider lock-in
- preserved SSOT authority
- lower rollout risk

## Final Judgment

Our current state is:

- not memory-empty
- not provider-memory-strong
- somewhat fragmented
- still improvable without major platform migration

`Vertex Live API` is a real option, but it is not the best first answer to the pain we are feeling today.

The smartest next move is:

- normalize provider capability handling
- stop pretending stale Gemini cache paths help Sonnet lanes
- add Sonnet prompt caching
- add one internal session-memory envelope

That is the most practical context-memory improvement path for this workspace right now.
