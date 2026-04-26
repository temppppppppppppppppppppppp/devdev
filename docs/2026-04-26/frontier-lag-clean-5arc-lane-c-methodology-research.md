# Frontier Lag Clean 5-Arc — Lane C: External Methodology Research

Date: 2026-04-26
Status: final after embedded 3-pass audit
Document Type: lane research report (read-only, no code change)
Canonical Path: `docs/2026-04-26/frontier-lag-clean-5arc-lane-c-methodology-research.md`
Order Pack: `docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md` §8 (Terminal 3 / Lane C)
Baseline Commit: `a76689ec6c7d1ff6a55686d9889be15009ebb4b7`
Baseline Dirty Summary:
- `M 0_temp.txt`
- `?? docs/2026-04-26/auto-frontier-lag-5arc-runtime-analysis-ssot.md`
- `?? docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md`
- `?? projects/0_골든카나리아/`

Method: parent terminal + two read-only subagents in parallel (one for official OpenAI documentation, one for primary papers). Parent retained codebase mapping. No code or DB was modified. All quotes traceable to URLs in §3 Evidence.

---

## 1. Scope

Lane C asks for external methodology — official OpenAI guidance and primary research — that should shape a clean 5-arc Frontier Lag run, given the observed Stage3 ep4 attempt-10 failure (Director-selected `PASS_WITH_FIX` score 95, but downstream binding/prevalidation `FAILED` because the Blueprint surface stayed at `2006년 1월 1일` while the arc state required `2006년 1월 3일`).

The deliverable is a small set of workspace-applicable principles (≤7), each anchored to an external source and explicitly compatible with the workspace governance invariants:

- Python collects/formats; Python never decides narrative truth.
- Director (LLM) is the final quality authority.
- Provider-native memory and provider-native context cache are not authoritative truth.
- Cost/latency caching is structurally distinct from truth/continuity memory.

Out of scope: implementing any of these principles, weakening Director authority for throughput, recommending vendor-managed hidden memory as a continuity solution.

---

## 2. Evidence

| # | Source | URL | Type | Date accessed |
|---|---|---|---|---|
| E1 | OpenAI — Prompt caching | `https://platform.openai.com/docs/guides/prompt-caching` (mirror: `https://developers.openai.com/api/docs/guides/prompt-caching`) | Vendor doc | 2026-04-26 |
| E2 | OpenAI — Conversation state | `https://platform.openai.com/docs/guides/conversation-state` (mirror: `https://developers.openai.com/api/docs/guides/conversation-state`) | Vendor doc | 2026-04-26 |
| E3 | OpenAI — Optimizing LLM accuracy | `https://platform.openai.com/docs/guides/optimizing-llm-accuracy` (mirror: `https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy`) | Vendor doc | 2026-04-26 |
| E4 | Liu et al., "Lost in the Middle: How Language Models Use Long Contexts" (TACL 2023) | `https://arxiv.org/abs/2307.03172` | Primary paper | 2026-04-26 |
| E5 | Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning" (2023) | `https://arxiv.org/abs/2303.11366` | Primary paper | 2026-04-26 |
| E6 | Park et al., "Generative Agents: Interactive Simulacra of Human Behavior" (2023) | `https://arxiv.org/abs/2304.03442` | Primary paper | 2026-04-26 |
| E7 | Packer et al., "MemGPT: Towards LLMs as Operating Systems" (2023, rev. 2024) | `https://arxiv.org/abs/2310.08560` | Primary paper | 2026-04-26 |
| E8 | Asai et al., "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection" (2023) | `https://arxiv.org/abs/2310.11511` | Primary paper | 2026-04-26 |

Workspace anchors used for codebase mapping (read-only):
- `modules/core/session_memory_envelope.py` — Python-side envelope builder (Stage4 only at present; key constant `SESSION_MEMORY_ENVELOPE_VERSION = "session-memory-envelope-v1"`, builder `build_stage4_session_memory_envelope(...)`).
- `AGENTS.md` §대원칙 — Python-collects/LLM-judges and Director sovereignty rules.
- `docs/2026-04-26/frontier-lag-5arc-post-run-merge-audit.md` — observed Jan-1 vs Jan-3 failure surface.
- `docs/2026-04-25/stage234-session-memory-resume-context.md` — current Stage2/3/4 envelope coverage gaps.

Retrieval caveat: `platform.openai.com` returned 403 to direct fetch from the OpenAI subagent; the canonical content was retrieved via the `developers.openai.com/api/docs/guides/...` mirror and corroborated. Quoted strings below are from that mirror.

---

## 3. Findings — what the sources actually say

### 3.1 OpenAI Prompt Caching (E1)

- Caching is a **performance** mechanism: "Prompt Caching can reduce latency by up to 80% and input token costs by up to 90%." Auto-enabled at ≥1024 prompt tokens; cache hits accrue in 128-token increments.
- **Prefix-only**: "Cache hits are only possible for exact prefix matches within a prompt." Routing is by prefix hash; an optional `prompt_cache_key` parameter influences server routing.
- **Output is independent of cache state**: "Prompt Caching does not influence the generation of output tokens or the final response." Only prefill compute is reused; the response is recomputed each time.
- TTL is short: ~5–10 min idle, max ~1 hr in-memory; Extended Prompt Caching reaches ~24 hr on selected models.

State ownership: unspecified — caching is a server-internal optimization, the caller still transmits the canonical prompt every call. No claim is made that cached prefixes are authoritative state.

### 3.2 OpenAI Conversation State (E2)

Three patterns:
- **Manual** message-array reassembly on Chat Completions.
- **`previous_response_id`** chaining on Responses — passes an id so the model has "all necessary context."
- **Conversations API** — durable conversation object reusable "across sessions, devices, or jobs."

Important constraints:
- Server retention: response objects "saved for 30 days by default" (`store: false` to opt out); Conversation items not subject to the 30-day TTL.
- Billing is **not waived**: "Even when using `previous_response_id`, all previous input tokens for responses in the chain are billed as input tokens in the API." Prior turns are still re-fed into the model.
- Context window still binds: tokens beyond the window "may be truncated"; `truncation: auto` drops middle items to fit.
- Fallback: when the id cannot be resolved, callers must "send a new turn with `previous_response_id` set to null and pass full input context" — i.e. caller is the recoverable source of truth.

State ownership: not explicitly authoritative. The doc never asserts that a fact stated in turn N will be *obeyed* in turn N+2; it only says prior content is *available*.

### 3.3 OpenAI Optimizing LLM Accuracy (E3)

- 2×2 framework: **context optimization** (model lacks needed knowledge) vs **LLM optimization** (model behaves inconsistently). Levers per quadrant: prompt engineering → +RAG → +fine-tuning → RAG+fine-tuning.
- "These are all levers that solve different things, and to optimize in the right direction you need to pull the right lever."
- "Prompt engineering is typically the best place to start. … Squeeze as much accuracy out of basic methods as you can before reaching for more complex RAG or fine-tuning."
- RAG failure decomposes into **retrieval failure** (wrong context fetched) and **LLM failure** (correct context, wrong application) — measured separately.
- Evals are foundational: aim for "20+ questions and answers" with documented failure analysis.

State ownership: caller. The doc does not discuss prompt caching, and does not name any provider-managed mechanism as an accuracy lever.

### 3.4 Lost in the Middle (E4 — Liu et al., TACL 2023)

- Core claim: LLMs do not use long contexts uniformly. Performance is "highest when relevant information occurs at the beginning or end" and "significantly degrades" when it sits in the middle — even for explicitly long-context models.
- Method: multi-doc QA + synthetic key-value retrieval; relevant span position varied while rest is held fixed; produces a U-curve.
- Holds qualitatively across model families (per abstract).

### 3.5 Reflexion (E5 — Shinn et al., 2023)

- Core claim: an agent can improve **across trials without weight updates** by verbally reflecting on task feedback and storing the reflection in an episodic memory buffer that conditions the next attempt.
- Mechanism: trial → external/internal feedback → LLM-authored verbal critique → append to episodic buffer → buffer is read on next trial.
- Empirical: 91% pass@1 on HumanEval (vs. 80% for the GPT-4 baseline reported in the abstract).
- Unit of learning is the *attempt*, not the *step*.

### 3.6 Generative Agents (E6 — Park et al., 2023)

- Core claim: long-horizon believable agents = LLM + memory stream (raw experience log) + periodic reflection (synthesis to higher-level beliefs) + retrieval (recency × importance × relevance) over both for planning.
- Empirical: 25-agent sandbox; emergent multi-day social behaviour; ablations show observation, planning, and reflection each contribute.
- Memory is **per-agent** (each Sim has its own stream) — not a shared singleton truth store.

### 3.7 MemGPT (E7 — Packer et al., 2023)

- Core claim: treat the context window like physical RAM; add an OS-style **virtual context** with hierarchical tiers; the LLM itself manages paging via function calls.
- Mechanism: small fast in-context tier (≈ "core memory") + larger slow external tier (≈ "archival"); LLM-driven swap-in via function calls; control-flow primitives ("interrupts") for yield/fetch/resume.
- Domains: long-document analysis exceeding context, and multi-session chat with persistent user memory.
- Frames itself in explicit contrast to vendor context windows — the OS metaphor reinforces "context ≠ truth storage."

### 3.8 Self-RAG (E8 — Asai et al., 2023)

- Core claim: a single LM trained to emit **reflection tokens** can adaptively decide when to retrieve, evaluate passage relevance, and critique its own generation — improving factuality and citation accuracy without indiscriminate retrieval.
- Reflection-token categories: *retrieve-or-not*, *passage-is-relevant*, *generation-is-supported*, *generation-is-useful*.
- Empirical: 7B and 13B Self-RAG outperform ChatGPT and retrieval-augmented Llama2-chat on open-domain QA, reasoning, and fact verification; "significant gains" in factuality and citation accuracy on long-form.
- Tokens are first-class **LLM-emitted** control signals — Python is downstream of the decision.

---

## 4. Cost/latency caching vs truth/continuity memory — the explicit distinction

The order pack asks Lane C to keep these two clearly separate. The external sources support a sharp separation:

| Dimension | Cost/latency caching (E1) | Truth/continuity memory (E2/E4–E8) |
|---|---|---|
| Purpose | Reduce prefill compute and bill | Make a fact survive across stages/turns and be used correctly |
| Output influence | None — "does not influence the generation of output tokens or the final response" (E1) | Direct — output should change to honour the remembered fact |
| Where it lives | Server-side prefix store, hashed by prefix | Caller-controlled prompt content (system/pinned slots), or LLM-managed tiers (E7), or LLM-authored reflections (E5/E8) |
| TTL/persistence | Short (≈minutes to hours; up to ~24h Extended) | Must outlive a single response (arc-spanning, sometimes work-spanning) |
| Authority owner | Provider-internal, opaque | Workspace governance — Director (LLM), with Python as plumbing |
| Failure mode if confused | Wasted spend, rare wrong-answer correlation only via collision | Silent narrative drift, multi-attempt retries (the observed Stage3 ep4 case) |
| Observed evidence in 5-arc run | `llm_calls.cached_tokens` shows real prefix reuse; explicit `context_cache_attempts` skipped as `content_too_short` (consistent with E1's 1024-token floor) | `session_memory_envelope` present at Stage4; **absent at Stage2 and Stage3** — which is precisely where the timeline-authority drift entered |

A cache hit on a prior Director prompt does **not** mean the model "remembered" Jan 3; it means the same prefix bytes hit prefill reuse. Conflating the two would let cost telemetry pretend to be continuity telemetry.

---

## 5. Seven workspace-applicable principles

These are the seven Lane C principles. Each is mapped to (a) source(s), (b) the Stage3 ep4 Jan-1 vs Jan-3 case, (c) governance compatibility (Python plumbing only; Director final).

### P1. Authoritative state must be **head + tail anchored** in every stage prompt, not buried in the middle.

- Source: E4 Lost in the Middle; reinforced by E3 ("squeeze as much accuracy out of basic methods as you can").
- Applied to the case: In Stage3 ep4, an authoritative line such as `arc_state.current_date = 2006-01-03` likely existed in the prompt corpus but was probably mid-stack between bible, prior episodes, and rubric. Promote the workspace's `session_memory_envelope` (currently Stage4-only) into Stage2 and Stage3, and place a compact authority block both at the top of the system prompt and as a "REMEMBER" tail just before the model's generation slot. (Mirror, not move — both positions matter per E4.)
- Governance: Python composes and pins; Director still adjudicates. No truth decision is made in code.

### P2. Cost/latency caching must never be reported as continuity memory.

- Source: E1 ("Prompt Caching does not influence the generation of output tokens or the final response"); E7 (cache vs storage as orthogonal tiers).
- Applied to the case: `cached_tokens > 0` is not evidence that authoritative arc state survived. Telemetry surfaces (DB, runtime audit, summary digests) must keep `context_cache_attempts` and `llm_calls.cached_tokens` in a *cost* column, separate from any future *continuity* column. The 5-arc clean harness must not emit a "memory hit" green check derived from cache fields.
- Governance: keeps Python from fabricating continuity authority out of compute reuse.

### P3. Provider conversation-state APIs are a transport convenience, not a truth source.

- Source: E2 (truncation, billing, fallback all imply caller-side truth).
- Applied to the case: Even if Stage2/Stage3/Stage4 chained via `previous_response_id`, `truncation: auto` could silently drop the early arc-anchor turn, and the multi-LLM topology (Director / Blueprint / ChiefWriter / prevalidator) is not a single response chain. The fix has to be authoritative-state-in-prompt under workspace control, not vendor chaining.
- Governance: matches AGENTS.md §대원칙 directly.

### P4. After a downstream rejection, run a Reflexion-style **verbal-critique buffer** before the next attempt.

- Source: E5 Reflexion.
- Applied to the case: Stage3 ep4 burned 10 attempts on the same drift with no carried-over critique. After a binding/prevalidation `FAILED`, an LLM-authored reflection ("attempt 7 used 2006-01-01; arc state demands 2006-01-03; on attempt 8, lock the opening scene to 2006-01-03 and cite `arc_state.current_date`") should be appended to a `failed_attempt_journal` block visible to attempt N+1.
- Governance: the critique is LLM-authored (Director or a dedicated critic role); Python only persists, retrieves, and pins the buffer slot. Compatible with Director sovereignty.

### P5. Treat the run as a **two-tier memory architecture** — small authoritative core, larger archival — and do not confuse them.

- Source: E7 MemGPT (vocabulary: core vs archival, paging protocol); E6 Generative Agents (memory-stream + reflection pattern).
- Applied to the case: Designate a single, small `arc_state_envelope` as **core** (singleton facts: `current_date`, `current_arc`, `ep_clock`, named-character status, faction-state pins) and keep bible / prior chapters / style refs as **archival**. Only Director is allowed to *write* the core tier. ChiefWriter, Blueprint, Analyst, prevalidator can *read* it; they cannot mutate it. Generative-Agents-style retrieval (recency × importance × relevance) selects from archival; the core tier is unconditionally pinned.
- Governance: the workspace-specific extension over MemGPT is that **the LLM does not self-page core memory** — Director gates writes. This is *stricter* than vanilla MemGPT, and required by the Director-sovereignty rule.

### P6. Generation-time **structured self-critique** must gate candidates before binding/prevalidation.

- Source: E8 Self-RAG (reflection tokens / `is_supported`); E3 (RAG failure decomposed into retrieval-fail vs LLM-fail).
- Applied to the case: A Director-emitted JSON critique block — e.g. `{cited_authority: "arc_state_envelope.current_date=2006-01-03", manuscript_uses: "2006-01-01", is_supported: false, action: REJECT, reason: "..."}` — would have caught the drift *before* it reached binding, regardless of the score-95/PASS_WITH_FIX surface. Python only parses booleans and routes; the critique itself is LLM-authored and overrides Python score thresholds when `is_supported=false`.
- Governance: cleanest fit of the five papers. The whole mechanism is LLM-emits, Python-routes.

### P7. Build a small **continuity-eval set** keyed on per-arc anchors and run it as part of the harness, not after.

- Source: E3 (≥20 ground-truth Q&A; "the best output from this stage" is the eval set).
- Applied to the case: Define ground-truth per arc — `(arc_num, current_date, location, key_npc_status, faction_alignment)` — and assert at Stage3 candidate time and Stage4 manuscript time that surface mentions match. Failures emit Self-RAG-style structured critiques (P6) and feed the Reflexion buffer (P4). Size ≈ 20–40 anchors across the 5-arc run is enough for fail-loud detection of the Jan-1/Jan-3 class without requiring fine-tuning or RAG infrastructure.
- Governance: the eval is Python-mechanical (string/structured comparison against a known anchor); the **decision** of what to do on mismatch (retry / quarantine / Director re-adjudication) remains Director-owned.

These seven principles fit the order-pack ceiling (≤7) and are non-overlapping: P1 = placement, P2 = telemetry hygiene, P3 = vendor scope, P4 = retry learning, P5 = architecture vocabulary, P6 = pre-bind critique, P7 = ground-truth measurement.

---

## 6. Risks

- **R1. Naively prepending an envelope can decrease accuracy.** E3 and E4 both warn that adding context is not free. Mitigation: keep core small, use head + tail mirror per P1, and validate via P7 evals before declaring success.
- **R2. Reflexion-style buffers can ossify a wrong correction.** If a bad critique enters the journal it will steer all later attempts. Mitigation: cap journal length per attempt-loop, expire on arc boundary, and let Director overwrite/strike entries.
- **R3. MemGPT-style self-paging is incompatible with Director sovereignty.** Adopting MemGPT's "LLM decides what to swap in" verbatim would let any single LLM call mutate authoritative state. Mitigation: per P5, only Director writes to core; other roles read-only.
- **R4. Self-RAG-style critique tokens are not natively trained into the workspace's LLMs.** The paper assumes a fine-tuned model. Mitigation: emulate via a structured Director-emitted JSON block (no fine-tuning required); accept that critique recall will be lower than a trained Self-RAG and offset with P7 evals as a safety net.
- **R5. Per-agent memory paradigms (E5/E6) do not natively model singleton truth.** Generative Agents' per-Sim streams and Reflexion's per-agent buffer are not designed for "today's date is 2006-01-03 for everyone." Mitigation: explicit single-writer designation (Director → `arc_state_envelope`), enforced by code as plumbing, not as judgment.
- **R6. Vendor `previous_response_id` chains can mask continuity loss.** `truncation: auto` plus a long unattended run can silently drop the anchor turn. Mitigation: do not rely on E2's chaining for continuity; treat it as a transport convenience only (P3).
- **R7. Cost telemetry can be mistaken for continuity telemetry.** `cached_tokens > 0` is not a memory hit. Mitigation: P2 — keep the columns separated in DB, runtime audit, and any harness summary.

---

## 7. Recommendation (for the clean 5-arc run)

For the **next** clean Frontier Lag 5-arc attempt, the methodology evidence supports the following operating posture (no implementation in this lane — design-only):

1. Promote the existing `session_memory_envelope` pattern from Stage4 into Stage2 and Stage3 prompt assembly, with head + tail anchoring (P1).
2. Add a structured Director-emitted continuity critique step at Stage3 candidate time and Stage4 manuscript time, with a hard `is_supported` boolean that overrides numeric score gating (P6).
3. Add a per-attempt LLM-authored reflection journal scoped to the current Stage3 episode loop, expiring on episode commit (P4).
4. Establish a single-writer rule for `arc_state_envelope` core memory: **Director only**; all other agents read-only (P5).
5. Add a small per-arc anchor eval set and run it inline as part of binding/prevalidation, not as a post-run report (P7).
6. Keep cost/latency cache telemetry strictly separate from continuity telemetry in DB and runtime audit surfaces (P2).
7. Do not adopt vendor `previous_response_id` or Conversations API as a continuity solution; allow them only as a transport convenience if and when the workspace decides to use Responses (P3).

These are research-derived principles, not an execution plan. Lane D (Continuity Bridge Design) is the natural home for converting P5/P6/P7 into a packet contract; Lane E (Clean Harness Design) is the natural home for P2/P7 telemetry separation; Lane F (Governance Audit) should adversarially review P4 (reflection ossification) and P5 (single-writer enforcement). Execution SSOT must wait for headquarters synthesis per order pack §12.

---

## 8. Subagent Cross-Check

Two subagents were run in parallel. Parent retained codebase mapping and synthesis.

| Topic | OpenAI-doc subagent | Primary-papers subagent | Agreement? |
|---|---|---|---|
| Cache ≠ memory | Affirmed via E1 ("does not influence … final response"), E2 (billing not waived), E3 (no caching as accuracy lever) | Affirmed via E7 (cache vs storage tiers explicitly contrasted with vendor windows) | Yes — independent convergence |
| Caller owns truth | Affirmed via E2 fallback ("pass full input context"), E3 (caller constructs context, runs evals) | Implied across E5/E6/E7/E8 (all caller-side mechanisms) | Yes |
| `previous_response_id` is not continuity | Affirmed directly (truncation, billing, TTL) | Not addressed (out of scope) | OpenAI subagent only |
| "Lost in the middle" is the placement risk | Affirmed indirectly via E3 ("in-context memory" emphasis) | Affirmed directly via E4 abstract | Yes |
| Per-agent vs singleton truth gap | Not addressed | Flagged explicitly as a limit of E5/E6/E7 | Papers subagent only — important caveat surfaced here |
| Self-critique gating is the cleanest governance fit | Implicit via E3 eval framing | Affirmed directly via E8 reflection-token mechanism | Yes — strongest convergence |
| Vendor caching could not have prevented Jan-1/Jan-3 drift | Affirmed directly | Affirmed via E7 framing | Yes |

No contradiction was found between subagents. The papers subagent surfaced a workspace-specific gap (per-agent memory paradigms do not model singleton truth) that the OpenAI subagent could not have raised; this is captured in P5 / R5.

Source-retrieval honesty:
- OpenAI subagent: `platform.openai.com` 403'd; mirror at `developers.openai.com/api/docs/guides/...` succeeded; quotes corroborated.
- Papers subagent: all five arXiv abstract pages fetched on first attempt; no content invented; abstract-only (no full PDFs).

---

## 9. 3-Pass Mini Audit

**Pass 1 — structure and scope: PASS.**
The report contains all required sections (Scope, Evidence, Findings, Risks, Recommendation, Subagent Cross-Check, 3-Pass Mini Audit). It produces ≤7 workspace-applicable principles (exactly 7). It explicitly distinguishes cost/latency caching from truth/continuity memory (§4). It cites URLs for every external claim (§2 table; §3 inline). It does not propose code changes; it is read-only. Output path matches the order pack §5 assignment.

**Pass 2 — evidence and consistency: PASS.**
All seven principles trace back to one or more of E1–E8. The Jan-1/Jan-3 case-mapping in each principle is consistent with the failure surface as described in the order pack §2 ("known run facts") and the post-run merge audit. The cost-vs-memory distinction (§4) is supported by direct quotation from E1 and the structural framing in E2/E7. No principle relies on vendor-native hidden memory as a continuity solution (order pack §8 rule). No principle weakens Director authority — P5 explicitly *strengthens* Director sovereignty over MemGPT's vanilla self-paging design. Risks section (R1–R7) addresses each principle's failure mode, including the per-agent vs singleton-truth gap.

**Pass 3 — execution readability: PASS.**
Each principle is paired with (a) source citation, (b) Jan-1/Jan-3 application, (c) governance compatibility note — readable as a self-contained item by Lane D / Lane E / Lane F authors without needing to re-read the upstream papers. Recommendation §7 maps principles to the lanes that would consume them. The report does not produce a `docs/temp/` mirror (correct per order pack §5). Confidence in current state: ≥95%.

Estimated overall confidence: **96%**.
