Date: 2026-03-27
Status: final (3-pass audited)
Document Type: system-track defer priority freeze
Canonical Path: `docs/2026-03-27/llm-friendliness-gimmick-elegance-defer-priority-freeze.md`
Temp Mirror Path: none
Supersedes:
- chat-local defer ordering for this topic
- lane-local Opus wording when it conflicts with live-code evidence
Source Survey Docs:
- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-merge-audit.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t2-provider-router-elegance.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t3-stage4-authority-verdict.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t4-writer-context-injection.md`
- `docs/2026-03-27/opus/rol-llm-gimmick-t5-fact-authority-genre-state.md`
Evidence Basis:
- live re-audit of provider/router, writer/context, state/fact, and Stage 4 handoff surfaces
- static signature counting for the ChiefWriter request chain
- current `docs/temp/queue-state.json`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked provider/context/validator/stage4/orientation/runtime surfaces, queue-state.json, logs/artifacts; untracked dated docs, anthropic_vertex provider/tests, probe script, project artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Executive Summary

This document freezes the current `defer` ordering above the Opus lane reports.

The key correction from the deep-dive re-audit is that the old "technique/realm canonical authority" claim was directionally right but too broad. Live code already has:
- protagonist skill persistence
- a wuxia-only Stage 4 authority clause
- a wuxia protagonist technique-vs-realm blocking check

So the frozen top priority is **not** "technique/realm is broadly broken." The frozen top priority is the narrower **fact-contract correctness cluster**:
- `state_changes schema formalization`
- `realm authority / NPC technique-model gap`

Later Opus passes may add evidence, but they do **not** get to casually reorder this backlog unless they show a live-code contradiction or fresh runtime failure that invalidates this freeze.

## 2. Freeze Rule

This document is the top authority for defer ordering in the `LLM friendliness + gimmick elegance` thread until superseded by a later dated top-level doc.

Allowed reasons to reorder:
- live code contradicts a frozen claim
- a fresh runtime failure materially changes risk ranking
- a structural patch lands and removes one frozen item

Not allowed:
- lane-local wording drift
- impressionistic "this feels uglier now" arguments
- reusing the older broad T5 wording without checking current code

## 3. Frozen Priority

### Tier 1. Fact-Contract Correctness Cluster

This is the highest frozen cluster because it is the only defer area still tied to possible long-run narrative contradiction rather than mostly navigation or maintainability cost.

#### 1A. `state_changes schema formalization`

Status: `supported`

Why it stays at the top:
- `StateTracker` still builds and returns a wide raw `state_changes` dict shape without a formal typed contract in the inspected runtime surface.
- `StateTrackerNPC` still consumes `state_changes` with repeated dict access plus regex fallback patterns, which keeps producer/consumer expectations partly implicit.
- `WorldState` still applies many `state_changes` sections directly via dict keys, so schema drift can spread across multiple owners.

Live anchors:
- `modules/domain/agents/state_tracker.py:1609-1626`
- `modules/domain/agents/state_tracker_npc.py:830-849`
- `modules/domain/agents/state_tracker_npc.py:882-920`
- `modules/domain/agents/state_tracker_npc.py:971-987`
- `modules/core/world_state.py:697-726`

Frozen judgment:
- this is a real structural contract gap
- this is not solved by more comments
- this should be treated as the first executable defer when a fact-contract wave opens

#### 1B. `realm authority / NPC technique-model gap`

Status: `partially supported`

Why it stays in Tier 1, but narrowed:
- the remaining live gap is specifically `realm` authority and NPC-side technique/realm ownership
- the broader claim that technique/realm is still mostly unguarded is not true anymore

What already exists live:
- protagonist skill accumulation in `StateTracker`
- protagonist skill summary injection
- wuxia-only Stage 4 authority clause
- wuxia protagonist technique-vs-realm blocking check
- `wuxia.yaml` realm limits reused by guard/validator logic

What still does **not** have a clean owner:
- protagonist `realm` as a clearly canonical persisted owner in this inspected slice
- NPC technique mastery
- NPC realm progression

Live anchors:
- `modules/domain/agents/state_tracker.py:141-142`
- `modules/domain/agents/state_tracker.py:1394`
- `modules/core/stage4_context_builder.py:1716-1730`
- `modules/validation/blocking_validator.py:130-133`
- `modules/validation/blocking_validator_consistency_checks.py:375-429`
- `modules/core/world_state.py:764-774`

Frozen judgment:
- keep this in Tier 1 because it is still the main unresolved wuxia fact seam
- do **not** describe it as a broad technique/realm collapse
- execution scoping should stay protagonist-realm plus NPC ownership gap, not a full wuxia registry project

### Tier 2. `provider identity / usage normalization consolidation`

Status: `supported`

Why it ranks here:
- provider identity is still split across router inference, metrics inference, and generate-bridge overwrite logic
- usage normalization still lives in `BaseAgent`, while providers return mixed raw shapes
- this is a real contract-normalization problem, but it is more reasoning-drift than direct narrative contradiction

Live anchors:
- `modules/core/llm_router.py:119-134`
- `modules/core/metrics_collector.py:101-105`
- `modules/core/llm_generate.py:24-30`
- `modules/domain/agents/base_agent.py:396-400`
- `modules/core/providers/gemini_provider.py:32-41`
- `modules/core/providers/anthropic_provider.py:76-82`
- `modules/core/providers/openai_provider.py:91-98`

Frozen judgment:
- real and still deferred
- below Tier 1 because current risk is primarily silent contract drift, not the strongest correctness seam

### Tier 3. `writer/context request-shape cleanup`

Status: `partially supported`

Why it moved below provider consolidation:
- the oversized request surface is still real
- but the older "35-parameter forwarding chain" label is now too imprecise for top-level freezing
- live code already has some local bundling, so the lane is ugly but not untouched

Live correction:
- current signatures are still large, but the exact counts are `36 / 32 / 31 / 34` across the main forwarding chain, not a literal uniform 35
- `stage4_interview_round.py` now builds `_common_writer_kwargs`
- `chief_writer.py` already uses a `request_bundle` for per-candidate dispatch

Live anchors:
- `modules/domain/agents/chief_writer.py:560-607`
- `modules/domain/agents/chief_writer.py:790-818`
- `modules/domain/agents/chief_writer_context.py:114`
- `modules/domain/agents/chief_writer_prompts.py:50`
- `modules/core/stage4_interview_round.py:2053-2078`

Frozen judgment:
- still worth doing
- but no longer justified as the highest defer
- treat this as a structural cleanup wave after fact-contract and provider-normalization work

### Tier 4. ``_god1_*` replacement`

Status: `supported`

Why it stays last:
- the hidden handoff still exists
- the channel is still mutable and cross-file
- but it is narrow, documented, stable, and already carries a migration TODO

Live anchors:
- `modules/core/stage4_interview_round.py:2270-2293`
- `modules/core/stage4_director_runtime.py:102-110`
- `modules/core/stage4_director_runtime.py:167`
- `modules/core/stage4_interview_round.py:4608`

Frozen judgment:
- do not forget it
- do not let it jump ahead of larger correctness or contract-normalization items without fresh evidence

## 4. Explicit Non-Frozen Claims

The following older phrasings are **not** frozen as authoritative:

- "`technique/realm canonical authority` is the top deferred risk" in a broad sense
- "`35-parameter forwarding chain`" as an exact current-state measurement

Replacement reading:
- `technique/realm` must now be read narrowly as `realm owner + NPC technique-model gap`
- `writer/context` must now be read as `oversized request-shape chain with partial local bundling already present`

## 5. Operating Consequence

If a new defer-focused wave opens, use this order:

1. fact-contract cluster
2. provider identity / usage normalization
3. writer/context request-shape cleanup
4. `_god1_*` replacement

Within the fact-contract cluster, start with:
1. `state_changes schema formalization`
2. `realm authority / NPC technique-model gap`

If a later survey wants a different order, it must explicitly say which frozen claim failed against live code.

## 6. Side-Effect Coverage

Not applicable for runtime side effects in this turn.

This was a static documentation re-audit only. No code patch, no DB write, no execution queue mutation, and no temp execution mirror were created.

Current queue truth:
- `docs/temp/queue-state.json` remains `empty`

## 7. Confidence And Limits

Estimated confidence: `96%`

Why:
- the freeze is grounded in live code, not only in the Opus reports
- the two over-broad Opus claims were explicitly corrected before freezing
- the remaining ranking is based on current contract/correctness exposure rather than aesthetics alone

Limits:
- static re-audit only; no fresh runtime probe was run in this turn
- if a later execution wave materially changes these surfaces, this freeze must be superseded rather than silently reused

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- confirmed this is a top-level priority freeze, not a survey or execution SSOT
- made the freeze rule explicit
- separated frozen claims from non-frozen older phrasing
- PASS

### Pass 2. Evidence and Consistency
- checked the frozen order against current live code and existing merge artifacts
- corrected the over-broad `technique/realm` claim
- corrected the over-specific `35-parameter` wording
- PASS

### Pass 3. Execution and Readability
- made reorder conditions operationally explicit
- made next-wave consequence explicit
- confirmed no canonical/temp execution semantics were needed
- PASS

