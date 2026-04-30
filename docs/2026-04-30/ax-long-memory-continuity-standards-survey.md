# AX Long-Memory / Continuity Standards Survey

Date: 2026-04-30
Status: revised after additional 3-round internal survey and 3-pass document audit
Issue: GitHub #145, "AX팀 제공 자료 제작 및 3pass 감리"
Branch: `codex/ax-review-packet-3pass`
Baseline Commit: `ae57b439 Refresh ops queue state`
Baseline Dirty Summary: untracked AX/prose docs and `projects/0_카나리아` generated text/check outputs exist; this survey does not modify project originals or runtime code.
Scope: local archive, current code, GitHub issues/PRs, and external public references for the question: "Is there a solved long-form writing standard for long-term memory and continuity?"

## Executive Answer

There is no single external "solved standard" that makes long-form AI writing continuity a solved problem.

There is, however, a strong de facto standard pattern across papers, open-source projects, agent-memory docs, and our own historical surveys:

1. Canon / story bible / invariant constraints as the authority layer.
2. Episode/event ledger for what happened, when, and with what consequences.
3. Evidence retrieval with source excerpts, not only summaries.
4. Rolling summaries by scene / episode / arc / volume / series.
5. Generation from hierarchical plans, not one-shot prose.
6. Continuity gates plus rerank/revise/retry loops.
7. Lineage/freshness metadata so downstream plans know which accepted manuscript they were generated from.
8. Human/editor/Director authority over narrative truth; memory/cache are helpers, not sovereign canon.
9. Benchmark windows that prove the system under long-run conditions instead of assuming memory works.

글도비 already implements much of this pattern, but should not claim the problem is "solved" until the open terminal proof and benchmark lanes are closed. The current honest statement is:

> 글도비 has a layered long-memory architecture aligned with the best external patterns, but still needs terminal 5-arc proof and cache/session-memory impact benchmarking before calling it production-trusted for long serial writing.

## What I Searched

Local archive / current workspace:

- `docs/이전/2026-02-27/long_term_memory_system_250ep_recommendation.md`
- archived commit `72633262`:
  - `docs/2026-03-26/long-run-continuity-probe-plan.md`
  - `docs/2026-03-26/arc-boundary-window-a-probe-report.md`
  - `docs/2026-03-26/lookback-boundary-window-b-probe-report.md`
- archived commit `24a66de2`:
  - `docs/2026-03-20/sparse-attention-memory-applicability-to-tf.md`
- current docs:
  - `docs/2026-04-23/stage234-session-memory-max-utilization-deep-dive-adversarial-3pass-audit.md`
  - `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/*`
  - `docs/2026-04-30/ax-bottleneck-deepdive-survey.md`
- current code anchors:
  - `modules/core/fact_ledger.py`
  - `modules/core/world_state.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/session_memory_envelope.py`
  - `modules/core/authoritative_continuity_projection.py`
  - `modules/core/final_accepted_context.py`
  - `modules/core/blueprint_lineage.py`
  - `modules/core/frontier_staleness.py`
  - `modules/core/db_manager.py`

GitHub:

- Issues: #3, #57, #58, #64, #121, #129, #130, #145.
- PRs: #52, #54, #125, #128, #135, #136, #140, #141, #144.

Additional internal survey loop on 2026-04-30:

- Round 1: current code authority/memory survey.
- Round 2: archive/temp/live-artifact continuity evidence survey.
- Round 3: GitHub/tests/proof-gap synthesis survey.
- Verification pass: direct re-check of the cited code/docs anchors before this revision.

External public references:

- Re3, EMNLP 2022: <https://aclanthology.org/2022.emnlp-main.296/>
- DOC, ACL 2023: <https://aclanthology.org/2023.acl-long.190/>
- DOC codebase / follow-up implementation: <https://github.com/yangkevin2/doc-story-generation>, <https://github.com/facebookresearch/doc-storygen-v2>
- Dramatron: <https://github.com/google-deepmind/dramatron>
- RecurrentGPT: <https://github.com/aiwaves-cn/RecurrentGPT>
- LongWriter / AgentWrite: <https://arxiv.org/abs/2408.07055>, <https://github.com/THUDM/LongWriter>
- Vertex AI context cache: <https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview>
- Vertex AI Agent Engine Memory Bank: <https://cloud.google.com/agent-builder/agent-engine/memory-bank/overview>
- LangGraph memory overview: <https://docs.langchain.com/oss/python/langgraph/memory>
- Anthropic prompt caching: <https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching>

## External Finding

### 1. Long-form story papers converge on hierarchy plus revision

Re3 frames long stories as a planning and revision problem: plan first, repeatedly inject plan and current story state, rerank continuations, then edit for factual consistency. DOC goes further: it moves more creative burden into a detailed hierarchical outline and then controls drafting against outline details.

Implication for 글도비:

- Stage3 blueprint / Stage4 draft split is directionally correct.
- The "memory" problem is not only recall. It is also plan obedience, accepted-state freshness, and revision authority.
- Stage4 prose polishing cannot fix a stale or contradictory Stage3 plan.

### 2. Co-writing systems do not remove the human/editor authority layer

Dramatron uses hierarchical story generation for coherent scripts, but its own documentation treats it as a co-writing and exploration tool, not autonomous final-play generation. Its value is structure and ideation, followed by human compilation, editing, and rewriting.

Implication for 글도비:

- Director sovereignty is not a quirky local rule; it matches the practical external pattern.
- Python gates should route evidence and block obvious contradictions, but not become the story judge.

### 3. "Memory systems" split into semantic, episodic, and procedural layers

LangGraph and related agent-memory docs distinguish short-term thread state from long-term cross-session memory, and split long-term memory into semantic facts, episodic experiences, and procedural behavior. RecurrentGPT similarly separates short-term state from long-term summaries and retrieves prior paragraph summaries.

Implication for 글도비:

- A single memory table or vector store is not enough.
- FactLedger / WorldState / episode events / retry pathology / WorkGuard-style procedural rules should remain separate layers with explicit read priority.

### 4. Provider memory/cache features are helper infrastructure, not canon

Vertex context cache and Anthropic prompt caching are cost/latency tools for repeated context. Vertex Memory Bank can generate and retrieve persistent memories, but Google explicitly frames memory poisoning and prompt injection as risks.

Implication for 글도비:

- AX should help us measure and optimize cache/session use, not replace the DB/fact-ledger/story-bible authority model.
- Provider-native memory can become a sidecar retrieval layer only if every retrieved memory has freshness, scope, and authority labeling.

### 5. Long output length is not the same as long continuity

LongWriter / AgentWrite is important because it shows decomposition can push 10,000+ word generation. But output length alone does not prove 250-episode continuity. It is relevant as evidence for decomposition, not as a solved serial-fiction memory standard.

## Internal Archive Finding

### 1. The 250EP recommendation already named the right architecture

`docs/이전/2026-02-27/long_term_memory_system_250ep_recommendation.md` proposed a Hybrid Memory Stack:

- L0 Canonical Constraints
- L1 Episodic Event Log
- L2 Evidence Retrieval with source excerpts
- L3 Rolling Narrative Summaries
- L4 Continuity Gate with `CRITICAL / MAJOR / MINOR`

It also warned that the weak point was not the search engine, but the memory model: what to structure, persist, inject, and validate.

Current judgment:

- This doc is still conceptually correct.
- The needed update is not to invent a new standard, but to align the current implementation and AX packet around this layered standard.

### 2. The March 26 long-run probes found continuity stronger than expected, but not fully proven

Archived commit `72633262` contains the sparse probe plan and Window A/B reports.

Key results:

- Window A, arc boundary EP5: persistence layers held, but hook reconciliation cost rose to 4 attempts.
- Window B, EP8-EP12 lookback boundary: EP1 facts survived at EP12; zero target contradictions; no retry amplification.
- The 10-episode retrospective-validator lookback was not the binding limit because generation context still received durable FactLedger/WorldState/cumulative-bible data.

Current judgment:

- Long-run continuity was not obviously broken at EP12.
- The remaining risk moved from "does memory exist?" to "does the right authority surface win when layers disagree?"

### 3. The April 23 session-memory survey already made the correct distinction

`docs/2026-04-23/stage234-session-memory-max-utilization-deep-dive-adversarial-3pass-audit.md` concluded:

- The main issue was not absence of memory.
- The issue was fragmentation, trim loss, resume loss, underused cache/session capability, and weak measurement.
- Hard truth should remain in DB / FactLedger / WorldState / anchors.
- Vertex context cache is an immediate measurable front door; Vertex Sessions / Live API / Memory Bank are secondary unless proven.

Current judgment:

- This remains aligned with the external evidence.
- AX help should be requested around cache/session benchmark design and telemetry, not as a request for a magical memory subsystem.

## GitHub Finding

### Closed / recently completed lanes

- #3 / PR #52 / PR #54: session-memory transport, context-cache telemetry, and GCP/Vertex route are implemented. This proves transport and observability, not long-run quality benefit.
- #121 / PR #125 / PR #128: fixed the immediate frontier staleness route where Stage3 blueprints could remain stale after accepted Stage4 manuscript truth changed, then narrowed false-positive stale blocking when regenerated Stage3 lineage matches the accepted prior manuscript.
- #129 / PR #135 / PR #140: centralized final-accepted context authority so provisional/lifecycle rows do not outrank fully settled Stage4 truth.
- #130 / PR #136 / PR #141: persisted Stage3 blueprint lineage metadata and made DB `blueprint_lineage` the first-class authority over JSON `_stage3_meta`.
- #144: refreshed ops queue state and reopened #57 as the active full auto-frontier / strict 5-arc proof tracker.
- #58: post-select carryover drift lane closed as an execution lane, but not as clean-run proof. Its evidence remains important for the broader memory/authority story.

### Still open / not proven

- #57: terminal GCP/Vertex strict 5-arc proof remains open. This is the big honesty gate. We must not claim "solved" while this is open.
- #64: context-cache/session-memory impact benchmark remains open. We can see cache/session surfaces, but we have not yet measured enough comparable windows to claim causal quality/cost benefit.
- #145: AX packet work is open and should carry this survey into system/data-flow/model/cost docs.
- Several late PRs rely on strong local validation while GitHub Actions did not always execute normally for infrastructure/account reasons. AX-facing claims should say local validation passed, not that CI independently proved everything.

## Current Code Finding

### Existing layers already match the de facto standard

| Standard Layer | Current 글도비 surface | Evidence |
| --- | --- | --- |
| Canon / invariant facts | `canonical_facts`, FactLedger numeric facts, WorkGuard/material SSOT | `modules/core/db_bootstrap_runtime.py`, `modules/core/fact_ledger.py`, `modules/core/stage4_context_builder.py` |
| Episodic event / accepted truth | final accepted context helper, manuscripts, stage attempts, settlement packet | `modules/core/final_accepted_context.py`, `modules/core/db_manager.py` |
| World/timeline state | WorldState timeline and relationship/state surfaces | `modules/core/world_state.py` |
| Evidence retrieval | VecMemory, reference anchors, context advisor, final accepted manuscript excerpts | `modules/core/stage4_context_builder.py`, `modules/core/vec_memory.py` |
| Rolling summaries | cumulative bible / summaries / episode meta | DB + context-builder surfaces |
| Hierarchical planning | Stage2/Stage3 blueprint before Stage4 prose | `modules/core/stage3_orchestrator.py`, `modules/core/stage4_orchestrator.py` |
| Continuity gate | Director continuity, post-select conflict, truth pins, retry hydration | `modules/domain/agents/director_continuity.py`, `modules/core/stage4_postselect_runtime.py`, `modules/core/stage4_interview_round.py` |
| Lineage / freshness | DB `blueprint_lineage`, frontier staleness preflight | `modules/core/blueprint_lineage.py`, `modules/core/frontier_staleness.py` |
| Cache/session sidecar | context cache attempts, session memory envelope | `modules/core/session_memory_envelope.py`, `modules/core/db_manager.py` |

### Current weak points are proof and integration, not missing primitives

The major remaining gaps are:

1. No terminal clean 5-arc proof yet (#57).
2. No benchmark-grade causal read on cache/session-memory benefit yet (#64).
3. Several continuity carriers exist, so authority order must stay centralized and observable.
4. Provider memory/cache can reduce cost and lost-context symptoms, but can also preserve stale or poisoned memory if promoted beyond sidecar.
5. Anti-AI-slop/prose polish is downstream. It is real, but it is not the root long-memory standard.

### Additional live-code risks from the second internal survey

The current implementation is much stronger than the old "we need memory" framing, but the additional code survey found five concrete places where the memory standard is not yet airtight:

1. Final-accepted fallback can still fail open on accessor exceptions.
   - `modules/core/final_accepted_context.py` catches a generic exception from `get_final_accepted_episode_context()` and then falls back to raw `get_manuscript()`.
   - This keeps legacy compatibility, but it means an authority-accessor failure can re-promote a raw manuscript row.
   - Needed follow-up: if the final-accepted accessor exists and errors, fail closed unless an explicit legacy mode is selected.

2. Final-accepted context does not currently compare manuscript-table content to the latest Stage4 attempt `content_hash` / `artifact_path`.
   - `modules/core/db_manager.py` computes a hash of the manuscript content and labels the row accepted when the latest Stage4 attempt verdict is final.
   - It does not prove that the manuscript row is the same artifact referenced by the final attempt.
   - Needed follow-up: link final Stage4 authority to manuscript content hash or artifact path before prior-context promotion.

3. Rollback/reset does not clear every authority sidecar.
   - `DBManager.reset_after()` clears blueprints, manuscripts, stage attempts, director selections, episode meta, vectors, foreshadow rows, and relationship state.
   - It does not currently clear or invalidate `blueprint_lineage`, `canonical_facts`, or `continuity_bridge_proposals`.
   - Needed follow-up: rollback should either delete or mark sidecar authority rows at/after target episode as stale.

4. Frontier hard-stale semantic detection is still narrow.
   - `modules/core/frontier_staleness.py` handles prior-manuscript hash mismatch, WTI month replay, investment-order replay, and provisional approval residue.
   - This is correct for the current canary failure family, but it is not yet a general completed-event replay detector.
   - Needed follow-up: generalize to typed completed-event, location, relationship, asset, institution, and open/closed action contracts.

5. Stage4 authority ordering is enforced by prompt insertion order and prose, not by one typed precedence manifest.
   - `stage4_context_builder` has a tier-0 ordering comment, but later authority projection and genre contract inserts mean the comment can drift.
   - Needed follow-up: add a rendered-context precedence test or typed manifest so new authority blocks cannot silently reorder the memory stack.

These are not reasons to discard the architecture. They are the strongest current candidates for turning the architecture from "mostly correct" into a production-trusted long-writing standard.

## Additional Internal Survey Synthesis

### Round 1 - Current Code

Implemented evidence is strong:

- persistent canon exists through FactLedger, WorldState, `canonical_facts`, and final-accepted manuscript accessors.
- Stage3-to-Stage4 lineage is no longer a JSON-only convention; DB `blueprint_lineage` exists and Stage4 can prefer it.
- Stage4 post-select continuity is fail-closed: provisional PASS can be downgraded when post-select truth conflicts appear.
- session memory envelope and authoritative continuity projection exist as structured sidecars.

But this round also produced the five live-code risks above. The important interpretation is: the system has the right layers, but some boundary failures can still promote stale or raw truth if a sidecar, rollback, or accessor path misbehaves.

### Round 2 - Archive / Temp / Live Artifact Evidence

Archive evidence supports the same story:

- The February 27 Hybrid Memory Stack remains the cleanest internal standard.
- March 26 Window A/B probes prove limited continuity survival, not production trust:
  - Window A: persistence held at an arc boundary, but hook/entity reconciliation cost increased.
  - Window B: EP1 facts survived to EP12, but it was a bounded Stage3-focused probe.
- April 23/26/27 docs repeatedly say session memory and context cache are helper telemetry, not continuity authority.
- `docs/temp/frontier-lag-clean-5arc-stabilization-execution-ssot.md` says strict 5-arc proof is still pending and context cache is not continuity authority.
- The supervised `0_카나리아` EP15 closure is useful evidence that the system can produce a 15-episode draft chain, but the local review report still finds P0/P1 accounting, product, institution, and event-continuity issues. That strengthens "usable but not solved."

Stale archive warning:

- Older "250ep feasible / no structural defect" style docs are too optimistic after the frontier-lag, lineage, and post-select conflict evidence.
- `docs/temp/` mirrors are queue surfaces, not final authority; dated canonical docs plus live code/evidence win.

### Round 3 - Tests / GitHub / Benchmark Proof

Current unit and integration-test coverage is broad around contracts:

- final accepted authority
- DB blueprint lineage sidecar
- frontier staleness checks
- session memory envelope
- context cache attempt telemetry
- post-select conflict downgrade and truth-pin preservation
- strict frontier proof harness gaps and continuity canary review flags

The missing proof is not "there are no tests." The missing proof is system-level:

- cache/session tests prove usage and metadata, not causal improvement.
- cache proof verifies cached-token/gate accounting, not stale-source suppression.
- benchmark snapshots are useful but not fully reproducible if full artifact trees/manuscripts are excluded.
- #57 and #64 must be treated as the production-trust pair: terminal long-run proof plus cache/session causal benchmark.

## AX Ask

Ask AX for help with the following, in this order:

1. Review the layered memory architecture, not just the model prompt.
   - Does the layer split match best practice for long-running LLM systems?
   - Are DB/FactLedger/WorldState/lineage the right authority carriers?

2. Design cache/session-memory telemetry.
   - cache creation attempts
   - cache hit/miss and cached token share
   - session-memory envelope presence
   - retries before PASS
   - continuity failure category before/after cache/session activation
   - stale-source suppression proof, not only cached-token proof

3. Optimize repeated static context cost.
   - WorkGuard / style guide / stable BI / recent accepted context are the most likely cache candidates.
   - Verify provider constraints for Gemini/Vertex explicit cache and whether our local thresholds are too conservative.
   - Review whether cache lineage should include run id, accepted manuscript hash, DB `blueprint_lineage`, artifact revision, upstream state hash, provider, and model.

4. Evaluate provider-native Memory Bank only as a sidecar.
   - It may help cross-session recall.
   - It must not outrank DB/fact-ledger/final-accepted manuscript truth.
   - It needs memory-poisoning and freshness controls.

5. Help define a long-run benchmark packet.
   - #57 terminal proof plus #64 cache/session benchmark should be treated as the production-trust gate.
   - The packet should distinguish supervised EP15 conditional pass from strict full auto-frontier 5-arc proof.
   - It should include final-accepted authority status, blueprint lineage hash/source, frontier staleness status, cache outcome counts, cached token share, session envelope presence, retries before PASS, post-select conflict subfamily, continuity canary status, and redacted artifact-truth references.

6. Review the five internal authority-boundary follow-ups.
   - fail-closed final-accepted accessor behavior
   - final manuscript content-hash linkage
   - rollback clearing/invalidation for authority sidecars
   - typed frontier stale contracts beyond WTI/investment cases
   - rendered Stage4 authority precedence test or typed manifest

## Recommended Operating Position

Do not tell AX:

- "We need long-term memory."
- "Can Memory Bank solve continuity?"
- "The prose feels AI-ish, so please optimize the model."

Tell AX:

- "We already have a layered memory architecture. The risk is authority ordering, stale lineage, context/cache measurement, and long-run proof."
- "Please help validate cost/latency/token optimization without turning provider memory into canon."
- "Please help us instrument whether cache/session-memory actually reduces retries and continuity failure families."

## Bottom Line

The best next AX packet should frame 글도비 as:

> A multi-stage long-form writing system with a mostly correct layered memory design, currently bottlenecked by proof, observability, cache/session benchmarking, and a small set of authority-boundary hardening tasks.

That is much more accurate than "we lack memory" or "we need anti-slop polishing."

## 3-Pass Document Audit

### Pass 1 - Structure / Scope

- Document type matches user request: survey-only, no code changes.
- Scope includes local archive, current code, GitHub issues/PRs, and external references.
- Additional internal survey loop is represented as three explicit rounds.
- It distinguishes standards/patterns from solved production proof.
- It does not touch original `projects/0_카나리아` artifacts.

### Pass 2 - Evidence / Consistency

- Internal archive claims are anchored to current files or archived commits identified by hash.
- GitHub claims are anchored to inspected issues/PRs.
- External claims are bounded to public paper/project/provider docs.
- New live-code risk claims were rechecked against current files before revision.
- Claims avoid over-promoting provider cache or Memory Bank to narrative authority.
- Main conclusion is consistent with `docs/2026-04-30/ax-bottleneck-deepdive-survey.md`.

### Pass 3 - Actionability / Readability

- The AX ask is concrete: architecture review, telemetry, cache/session optimization, Memory Bank sidecar evaluation, benchmark packet, and five internal authority-boundary follow-ups.
- Open proof gaps remain explicit (#57, #64).
- The recommendation is operational, not merely descriptive.

Estimated Confidence: 95%
