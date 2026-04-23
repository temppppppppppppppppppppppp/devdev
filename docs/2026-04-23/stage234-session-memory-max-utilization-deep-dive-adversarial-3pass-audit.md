# Stage234 Session Memory Max-Utilization Deep Dive Adversarial 3-Pass Audit

Date: 2026-04-23
Status: final
Scope: GitHub issue-backed + live-code-backed deep survey of how far session memory can be utilized across Stage2, Stage3, and Stage4 on the current `main` workspace
Mode: survey-only, documentation-only; no production code mutation
Canonical Path: `docs/2026-04-23/stage234-session-memory-max-utilization-deep-dive-adversarial-3pass-audit.md`
Commit State:
- Baseline Commit: `30b9436fc3a5c3fcc3f6397bf23bfe45d24af918`
- Baseline Dirty Summary: `dirty: untracked docs/2026-04-23/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same dirty surface; codebase-centered adversarial re-audit in-place`
Queue Note:
- `docs/temp/` active execution queue exists, but this order explicitly redirected into a fresh survey/doc cycle; no queue artifact was mutated in this turn.
Confidence: `97%`

## 1. Intent

Answer one bounded system-track question:

- `GitHub issues` and the live `main` workspace taken together, what is the maximum realistic way to exploit session memory across `S2-S3-S4` without violating current SSOT governance, and what should be considered immediate, medium, and sidecar lanes?

This document does **not**:

- open a new execution SSOT
- reorder the active temp roadmap
- patch production code
- promote provider-native memory to SSOT

## 2. Executive Answer

Short answer:

1. The repo already has a large amount of memory substrate.
2. The main problem is **not memory absence** but **memory fragmentation, trim loss, resume loss, and underused provider-native cache/session capabilities**.
3. `Issue #3` is the correct front-door problem statement, but it now lands on a slightly different workspace reality than the older 2026-04-13 survey assumed:
   - on `2026-04-13`, the memory survey treated the main high-intelligence path as Sonnet-heavy
   - on current `main` (`2026-04-23`), `config/models.yaml` again routes the core Stage2/3/4 producers to `vertexai:gemini-*`
   - this makes `Vertex context cache` materially more relevant again than the earlier Sonnet-first reading implied
4. The best near-term sequence is still:
   - keep hard truth in DB / fact-ledger / world-state / anchors
   - reactivate and measure the already-present cache path for heavy stable prefixes
   - add one internal provider-neutral session-memory envelope
   - start with `Stage4`, then `Stage3`, then `Stage2`
   - keep `Vertex Sessions / Live API / Memory Bank` as bounded secondary layers unless a later proof wave justifies more

## 3. Source Set

### 3.1 GitHub issue sources

Current origin repo:

- `temppppppppppppppppppppppp/devdev`

Relevant issues inspected via `gh issue view` on `2026-04-23`:

- `#3` `Next Wave: pipeline session-memory integration experiment (S2-S4, phased)`  
  Opened `2026-04-22`, updated `2026-04-22`
- `#5` `Next Wave: authority alignment and benchmark operating model hardening`  
  Opened `2026-04-22`, updated `2026-04-22`
- `#6` `Roadmap: next wave for Stage4 stability, donor expansion, and authority hardening`  
  Opened `2026-04-22`, updated `2026-04-22`
- `#4` `Next Wave: expand donor structure with R&D success-pattern transfer`  
  Opened `2026-04-22`, updated `2026-04-22`

### 3.2 Current-code evidence

- `config/models.yaml`
- `modules/core/providers/vertex_provider.py`
- `modules/core/providers/anthropic_provider.py`
- `modules/core/providers/openai_provider.py`
- `modules/domain/agents/base_agent.py`
- `modules/core/context_advisor.py`
- `modules/core/vec_memory.py`
- `modules/core/session_logger.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_optimizer.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage3_envelope_builder.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/chief_writer.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_post_pass_runtime.py`

### 3.3 Canonical prior docs re-audited against current `main`

- `docs/2026-04-13/stage234-context-memory-vertex-live-parallel-survey.md`
- `docs/2026-04-13/stage234-context-memory-vertex-live-3pass-audit.md`
- `docs/2026-04-13/t3-producer-context-packet-audit.md`
- `docs/2026-04-13/t9-stage2-to-stage3-handoff-quality-audit.md`
- `docs/2026-04-07/stage4-consumer-front-implementation-context.md`
- `docs/2026-04-16/stage234-global-authority-alignment-post-r12-stage4-current-session-closure-current-head-3pass-audit.md`

### 3.4 Official provider docs checked on 2026-04-23

- Vertex AI Context Cache overview: <https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview>
- Vertex AI Context Cache usage: <https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-use>
- Vertex AI Live session management: <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api/start-manage-session>
- Vertex AI Agent Engine Sessions overview: <https://docs.cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview>
- Vertex AI Memory Bank overview: <https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/overview>
- Vertex Live + MemoryCorpus / RAG memory context: <https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/use-rag-in-multimodal-live>
- Anthropic prompt caching: <https://platform.claude.com/docs/en/docs/build-with-claude/prompt-caching>
- Vertex AI Claude prompt caching: <https://cloud.google.com/vertex-ai/generative-ai/docs/partner-models/claude/prompt-caching>

## 4. GitHub-Issue Reading

### 4.1 `#3` is the direct parent problem statement

`#3` correctly frames the main lane:

- scope is explicitly `S2-S4`
- rollout order is explicitly `S4 -> S3 -> S2`
- current pain is described as provider-side statelessness plus retry/rewrite/resume continuity weakness
- hard truth must remain in `DB / carryover packet / fact ledger`
- target gains are carryover-loss reduction, chronology/continuity improvement, and retry-cost reduction

This issue is operationally consistent with the live codebase.

### 4.2 `#5` is the guardrail issue, not a side topic

`#5` is necessary because session-memory work is easy to overclaim.

Its role:

- benchmark archive expansion
- rerun diff / regression watchpoints
- authority-alignment framing
- proof standard for whether memory experiments actually helped

Without `#5`, memory work risks becoming anecdotal.

### 4.3 `#6` is the umbrella that keeps memory from becoming a silo

`#6` groups memory with donor, benchmark, and ensemble work.

This matters because the live workspace shows all four surfaces are coupled:

- memory quality affects retry convergence
- donor structure affects how much prior pattern knowledge must be re-injected
- benchmark visibility decides whether improvements are real
- ensemble depth and retry routing decide how often the same context is resent

### 4.4 `#4` is not “session memory”, but it is reusable structured memory

`#4` proposes reusable donor slots and donor injection paths into `Stage2/3/4`.

That makes it a complementary lane:

- not session memory in the provider sense
- but a durable reusable memory surface in the orchestration sense

It should be treated as a memory-adjacent structured prior, not ignored.

## 5. Pass 1. Full Inventory

### 5.1 Current memory surfaces that already exist

The current workspace already has five meaningful memory families:

1. Hard-truth memory
   - DB rows
   - anchors
   - world state
   - fact ledger
   - stage contracts
2. Retrieval memory
   - `VecMemory`
   - `ContextAdvisor`
   - semantic query / relation slices
3. Session-local retry memory
   - Stage2 optimizer failure memory
   - Stage3 retry directives / runtime advisory
   - Stage4 retry advisory digest / retry directives / retry budget axes
4. Prompt-prefix cache substrate
   - `BaseAgent._get_or_create_context_cache(...)`
   - `BaseAgent._ask_with_cached_context(...)`
   - `BlueprintEnsemble` / `ChiefWriter` cache call sites
5. Observability memory
   - `SessionLogger`
   - `quality_metrics.jsonl`
   - `runtime_audit_summary.json`
   - bridge/dashboard summaries

### 5.2 Cross-stage provider reality on current `main`

Current `config/models.yaml` routes the core Stage2/3/4 producers to `vertexai:gemini-*`, not to Sonnet.

That means:

- `VertexAIProvider` is now the main provider path for these stages
- `VertexAIProvider.generate()` is still a plain `models.generate_content(...)` call
- no session handle, no live-session lifecycle, and no memory-bank surface is wired in the provider
- but the live code still exposes `cached_content_token_count` in the provider usage payload
- the currently routed core models (`gemini-3.1-pro-preview`, `gemini-2.5-flash`) sit on the Gemini/Vertex family that current Google docs list as context-cache-capable

So the provider is:

- still largely stateless for generation
- but already capable of reporting cache token reuse if the cache path is genuinely exercised

### 5.3 Cache substrate exists but is underexercised or unproven

The code already contains a substantial Gemini/Vertex cache path:

- `BaseAgent._get_or_create_context_cache(...)`
- `BaseAgent._ask_with_cached_context(...)`
- `BlueprintEnsemble` creates a `blueprint_ensemble` cache from shared context
- `ChiefWriter` creates a `manuscript` cache from common context

Additional code-vs-provider nuance:

- current Google docs set the explicit-cache minimum at `2,048` tokens, but local code still gates cache creation behind `cache.min_content_chars = 50000`
- this means a meaningful share of cache underuse can be self-imposed by local thresholding, not just by provider limitations
- Google docs also warn that cached-content requests should not re-specify `system_instructions`, `tool_config`, or `tools`
- the current `BaseAgent._ask_with_cached_context(...)` path appears aligned on that narrow axis because it sends `cached_content` plus generation config, not tool/system fields

However, the 2026-04-13 producer audit found zero rendered `[context cached: refer to cached_content]` stubs in the observed Stage3 producer prompts.

Interpretation:

- the cache substrate exists
- the main question is no longer "should we design one from scratch?"
- it is "why is the existing cache path not showing up as a live reuse win in the observed production lane, and how do we make it measurable on current main?"

### 5.4 Session telemetry is not replay authority

`SessionLogger` clearly marks its JSONL logs as:

- optional
- best-effort
- non-authoritative
- off by default

This aligns with current governance and must stay true.

The important consequence is:

- `logs/session/*.jsonl` can support replay tooling and diagnostics
- but they must not become hidden narrative truth or hidden retry truth

### 5.5 Stage-specific memory inventory

#### Stage2

Main memory surfaces:

- retrieval plan from `ContextAdvisor`
- `VecMemory` / hybrid / dense / sparse retrieval
- work-slot summary
- fact-ledger context
- optional relation slice
- optimizer `SessionFailureMemory`
- carryover packet and carryover authority logging

Main loss points:

- retrieval clipped twice
- retry context reduced to compact feedback + preserved constraints + minimal previous state
- failure memory is deliberately lossy
- large prior context is still truncated with a head-biased `smart_truncate(...)` policy rather than a fully recency-ranked allocator

#### Stage3

Main memory surfaces:

- blueprint/manuscript history window (`24 recent + 6 anchor`, `36` cache limit)
- retrieval plan and semantic context
- treatment-block direction
- timeline advisory
- world-state / style-guide / fact-ledger / stale-seed / work-focus advisories
- previous blueprint carryover
- ending excerpt / archive appendix
- cache-capable `shared_context`

Main loss points:

- smart retrieval only sees the last `5` items from `focus_window`
- budget accounting exists but the stage still lacks one true cross-lane budget arbiter
- context compression happens locally in multiple places instead of one ranked allocator
- cache path presence is not yet being proven as a real steady-state win

#### Stage4

Main memory surfaces:

- previous manuscript / previous ending / chain-link anchor
- HUD + cumulative bible + FactLedger + WorldState + canonical summaries
- numeric carryover authority block
- retrieval plan + coverage warnings
- retry advisory digest
- retry directives
- retry budget axes
- persisted attempt/readback/patch lineage
- post-pass persistence into `episode_bible`, `state_log`, WorldState, FactLedger, VecMemory

Main loss points:

- `mandatory_context` trimming can still drop important surfaces
- current-episode retry memory is still partly loop-local even though `previous_attempt` / `feedback_provenance` reuse is strong inside the live reject loop
- durable attempt truth exists, and there is an operator-facing DB snapshot surface, but no general runtime resume hydrator wiring from persisted Stage4 snapshots back into interview-loop startup was found
- numeric truth promotion into the next carryover baseline is still under-specified

## 6. Pass 2. Semantic Classification

### 6.1 What is already strong enough to exploit immediately

These do **not** need a greenfield design:

1. Hard-truth SSOT surfaces
   - DB / fact-ledger / world-state / anchors already exist and should remain the base
2. Retrieval substrate
   - `VecMemory` already supports dense, multi-query, hybrid, NPC-specific retrieval, and keyword fallback
3. Coverage observability
   - Stage2/3/4 already compute `coverage_warnings`, `source_counts`, and budget ledgers
4. Cache-capable prompt construction
   - Stage3 and Stage4 producer paths already know how to prepare reusable shared context blocks
5. Stage4 persisted retry evidence
   - attempt truth, patch lineage, and post-pass owner/provenance are already much cleaner than earlier lanes

### 6.2 What is underused but immediately actionable

These are the highest-ROI surfaces because the substrate already exists:

1. Vertex context cache usage on the current Gemini-heavy routing
2. `cached_content_token_count` observability plus explicit cache hit/miss proof as a first-class benchmark field
3. benchmarking or lowering the local `cache.min_content_chars = 50000` gate instead of treating it as a provider law
4. Stage4 resume hydration from persisted attempts
5. Trim-resistant pinning of critical memory sections
6. Promotion of repeated Stage2/3 coverage warnings from telemetry into control behavior

### 6.3 What needs real new design work

These are not present in finished form yet:

1. one provider-neutral internal session-memory envelope
2. one cross-lane budget arbiter for Stage3
3. one richer Stage2 retry-memory contract
4. one explicit numeric carryover baseline-promotion rule
5. one bounded sidecar plan for Vertex Sessions / Live API / Memory Bank, if later justified

### 6.4 What should *not* be treated as the first move

These are tempting but wrong as the front step:

1. making provider-native session state authoritative
2. pivoting the main production pipeline to `Vertex Live API` first
3. reopening old Stage4 sinkproof work as if current-session sink alignment were still the main blocker
4. treating session logs as authoritative replay truth
5. inflating this survey into a new queue wave before a benchmark/proof contract exists

## 7. Pass 3. Maximum-Utilization Plan

### 7.1 Front-order recommendation

The maximum realistic path is:

1. `Measurement first`
   - use `#5` as the proof contract owner
2. `Exploit what already exists`
   - prove and reactivate current cache/token reuse on the Gemini/Vertex lane
3. `Normalize cross-stage session memory inside our own system`
   - one provider-neutral envelope
4. `Roll out by stage`
   - `Stage4 -> Stage3 -> Stage2`
5. `Add provider-native live/session sidecars only where the gain is specific and bounded`

### 7.2 Tranche A — Benchmark and authority gate

Owner concept:

- `#5` benchmark / authority hardening

Required before broad rollout:

- compare stateless baseline vs memory-enhanced lane
- measure retry count, pass persistence, continuity contradictions, and token/cost
- record cache hits / cached tokens / session-envelope usage explicitly
- preserve authority distinction between provider memory and SSOT truth

Why first:

- memory gains are easy to imagine and hard to prove

### 7.3 Tranche B — Immediate provider-native exploitation on current main

Because current routing is back on `vertexai:gemini-*`, the fastest provider-side win is:

- fix or verify the existing `cached_content` path
- make cache hit/miss and cached-token read/write visible
- benchmark the local `50000`-char cache gate against the provider's lower explicit-cache floor instead of assuming the current gate is optimal
- target heavy stable prefixes first:
  - Stage3 `shared_context`
  - Stage4 manuscript/common context
  - large static doctrine / style / guard / archive bodies
- keep cached-call sites inside the documented request restrictions for cached-content reuse (`system_instructions`, `tool_config`, `tools`)

Why this outranks Live API first:

- the code path already exists
- official Vertex docs still support context cache with long TTL control
- provider change is minimal compared with session-lifecycle redesign

### 7.4 Tranche C — Provider-neutral session-memory envelope

This should become the main new substrate.

Recommended contents:

- recent-turn compressed summary
- truth pins
- last accepted verdict surface
- retry directives
- retry budget axes
- per-stage carryover packet
- coverage-warning history
- optional cache/prefix lineage metadata

Why this is the real center:

- it survives provider swaps
- it preserves SSOT governance
- it can hydrate retries, resumes, and cross-stage handoffs
- it reduces repeated recomposition without surrendering truth ownership

### 7.5 Tranche D — Stage4 first

Highest-value Stage4 targets:

1. resume hydration for interview/retry loop state
   - rebuild current retry context from persisted attempts before the next round starts
2. trim-resistant pinning
   - protect `chain_link`, work-slot summary, relation slice, numeric carryover authority, and active retry directives from budget trimming
3. numeric baseline-promotion closure
   - complete the autonomous carryover-baseline promotion rule in post-pass / fact-ledger coordination
4. observability join cleanup
   - make raw-rationale / patch-trace persistence visible in proof summaries

Why Stage4 first:

- issue `#3` already calls it out
- the live workspace already holds the richest retry memory but still loses it most easily on restart / trimming

### 7.6 Tranche E — Stage3 next

Highest-value Stage3 targets:

1. one real budget arbiter before generation
   - semantic context, blueprint window, ending excerpt, and archive appendix should compete under one hard cap
2. stop discarding anchor work before retrieval
   - retrieval should not be limited to `focus_window[-5:]` when the stage already tracks a much larger anchor window
3. separate Stage3 retrieval-result policy from Stage4 defaults
   - stop sharing `context.vector_max_results_s4`
4. promote repeated coverage warnings into behavior
   - rerun, widen fallback, or explicitly downgrade confidence instead of only logging warnings
5. make cache utility measurable on producer calls

### 7.7 Tranche F — Stage2 last, but still important

Highest-value Stage2 targets:

1. richer retry-memory preservation
   - go beyond “top 3 violations / 200 chars”
2. recency-aware history truncation
   - replace head-only cuts with smarter retention
3. escalate repeated retrieval-emptiness / relation-loss signals
   - warnings should eventually affect control flow, not only telemetry
4. optionally persist or envelope-wrap `SessionFailureMemory`
   - today it is useful, but too local and too lossy

### 7.8 Tranche G — Optional sidecars

Treat these as bounded secondary lanes:

- Vertex Sessions
- Vertex Live API
- Vertex Memory Bank
- Vertex Live + MemoryCorpus

Best fit:

- operator copilot
- debugging assistant
- research-side session continuity
- bounded human-facing interactive tools

Not first-fit for:

- main S2/S3/S4 production truth path

## 8. Adversarial Read

### 8.1 Claim challenged: “The system is stateless.”

Rejected.

Live code shows the workspace already has:

- DB truth
- anchors
- `VecMemory`
- `ContextAdvisor`
- retry packets
- carryover packets
- post-pass owner contracts

The correct statement is:

- provider calls are still mostly stateless
- orchestration memory is already significant

### 8.2 Claim challenged: “Session logs are enough to become replay authority.”

Rejected.

`SessionLogger` explicitly disclaims authority, and the current design remains correct on this point.

The right move is:

- use logs as replay aids and diagnostics
- keep truth in DB / fact-ledger / world-state / anchors

### 8.3 Claim challenged: “Vertex Live should be the first move.”

Rejected for current `main`.

Because current main is Gemini/Vertex-heavy again, the first provider-side memory win is context cache activation and measurement, not a full live-session migration.

### 8.4 Claim challenged: “The existing cache path is blocked mainly by provider limits.”

Partially rejected.

Official Google docs say explicit context caching is supported on the Gemini family currently routed by this workspace, and live code still has a working cache substrate.

The larger local blockers are:

- a conservative local creation gate (`cache.min_content_chars = 50000`)
- weak steady-state cache-hit proof surfaces
- lack of benchmark-first instrumentation around cache reuse

Provider limitations still matter for `Sessions / Live API / Memory Bank`, but they do not fully explain current cache underuse.

### 8.5 Claim challenged: “Stage4 sinkproof is still the main blocker.”

Rejected.

The current-head Stage4 closure docs already say current-session sink alignment is clean. The honest next blocker is memory architecture quality:

- resume hydration
- trim resistance
- envelope normalization
- numeric carryover promotion

### 8.6 Claim challenged: “Stage2 and Stage3 need greenfield memory systems.”

Rejected.

They already have substantial memory input.

The deeper issue is:

- over-compression
- late budgeting
- telemetry-only warnings
- failure to reuse broader retained context effectively

## 9. Final Judgment

The highest-confidence reading of current `main` is:

1. `#3` is the right next-wave memory issue.
2. `#5` is the mandatory proof/benchmark governor for it.
3. The workspace already has enough memory substrate that the next big gain comes from **normalization and exploitation**, not from inventing an entirely new memory stack.
4. Because routing is currently back on `vertexai:gemini-*`, `Vertex context cache` is once again an immediate practical front-door, while `Vertex Live / Sessions / Memory Bank` remain secondary.
5. Current cache underuse is at least partly local: the workspace imposes a much higher cache-creation gate than the provider minimum and still lacks benchmark-grade cache-hit proof surfaces.
6. The central missing abstraction is still one internal provider-neutral session-memory envelope that can bridge retries, resumes, and cross-stage handoff while keeping DB/fact-ledger/world-state authoritative.

## 10. Recommended Next Step

If this survey is turned into implementation work later, the honest first execution packet should be:

1. prove current cache usage and cached-token visibility on `Stage4 -> Stage3` producer lanes
2. benchmark the local `cache.min_content_chars = 50000` gate against provider behavior and adjust only with measurement
3. define the internal session-memory envelope contract
4. implement Stage4 resume hydration + trim-resistant pinning
5. only then widen into Stage3 and Stage2

## 11. 3-Pass Audit Record

### Pass 1. Structure and scope

- Reframed the user request into one canonical survey rather than an execution SSOT because no code realization was requested.
- Included GitHub issue evidence, current live-code evidence, prior canonical doc drift checks, and current provider-doc checks.
- Explicitly excluded queue mutation, code patching, and provider-memory SSOT promotion.

### Pass 2. Evidence and consistency

- Rechecked `config/models.yaml` and corrected the stale 2026-04-13 Sonnet-heavy assumption.
- Revalidated that `vertex_provider.py` still performs plain `generate_content(...)`.
- Revalidated that `base_agent.py` still contains a live Gemini/Vertex cache substrate.
- Revalidated that the current cache substrate is routed through cache-capable Gemini families on current `main`.
- Added current official Google cache constraints that materially affect our code path: explicit-cache floor and cached-request field restrictions.
- Revalidated the Stage3 history-window claim against `_select_stage3_anchor_recent_window(...)` and the `24 / 6 / 36` live constants instead of leaving it as a narrative summary.
- Revalidated that Stage4 does have persisted repair snapshot surfaces for operator summaries, but those snapshot readers are not wired back into runtime loop hydration on current `main`.
- Cross-checked issue `#3` against current Stage2/3/4 code and found the issue’s rollout order consistent with the live architecture.
- Reconfirmed from closure docs that Stage4 current-session sink alignment is no longer the front blocker.

### Pass 3. Hostile execution/readability review

- Trimmed overreach that would have implied logs can become authority.
- Trimmed overreach that would have implied Vertex Live must be first.
- Converted “memory missing” language into the more accurate “memory fragmented / underexploited / trim-lost / resume-lost” framing.
- Kept recommendations tranche-shaped so the next operator can act without re-surveying the entire topic.

### Targeted re-audit for confidence >= 95%

- Rechecked official Vertex docs for current-session, context-cache, and memory-bank capability existence on `2026-04-23`.
- Rechecked official Anthropic and Vertex Claude prompt-caching docs to keep the non-Gemini sidecar lane current.
- Rechecked GitHub issues `#3/#4/#5/#6` by direct `gh issue view` CLI output instead of relying on list summaries.
- Rechecked that current workspace remained at the same `HEAD` but was not clean; the active dirty surface is the untracked `docs/2026-04-23/` directory containing this survey family.
- Re-ran a codebase-centered hostile pass on Stage2 truncation, Stage3 history-window selection, and Stage4 retry/resume surfaces to make sure the prose was not stronger than the code.

Final confidence remains `97%`.
