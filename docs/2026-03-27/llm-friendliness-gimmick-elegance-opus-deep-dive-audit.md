Date: 2026-03-27
Status: final (3-pass audited)
Document Type: system-track Opus deep-dive audit
Canonical Path: `docs/2026-03-27/llm-friendliness-gimmick-elegance-opus-deep-dive-audit.md`
Temp Mirror Path: none
Audit Target:
- `docs/2026-03-27/rol-llm-friendliness-gimmick-elegance-6terminal-merge-audit.md`
- Opus lane reports T2, T3, T4, T5
Related Freeze:
- `docs/2026-03-27/llm-friendliness-gimmick-elegance-defer-priority-freeze.md`

Commit State:
- Baseline Commit: `eb7a41d86a52b075861bcbd59a402622ab08d6cc`
- Baseline Dirty Summary: `dirty: tracked provider/context/validator/stage4/orientation/runtime surfaces, queue-state.json, logs/artifacts; untracked dated docs, anthropic_vertex provider/tests, probe script, project artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Executive Summary

The Opus survey bundle is still **directionally valid**. The merge-level conclusions remain usable:
- `cheap-fix-first`
- `no merged P0`
- `mixed but tractable`

But the deep-dive re-audit found two places where Opus wording was stronger than current live code supports:

1. `technique/realm canonical authority` was too broad
2. `35-parameter forwarding chain` was too exact

So the correct summary is:
- `provider identity / usage normalization`: supported
- `state_changes schema formalization`: supported
- `writer/context request-shape cleanup`: partially supported
- `technique/realm canonical authority`: partially supported and must be narrowed
- ``_god1_*` replacement`: supported

Bottom line:
- the Opus bundle is usable as a survey bundle
- it is **not** safe to reuse verbatim as the top defer authority
- the new freeze doc should be treated as the top-level correction layer

## 2. Scope And Method

This was a static live-code re-audit.

Included:
- provider/router/generate/usage surfaces
- ChiefWriter request-shape chain
- StateTracker / StateTrackerNPC / WorldState / BlockingValidator / WuxiaGuard fact surfaces
- Stage 4 `_god1_*` handoff surfaces
- current queue truth from `docs/temp/queue-state.json`

Excluded:
- fresh runtime execution
- new tests
- code modification

Method:
- re-read the merge audit and the four relevant Opus lane reports
- re-check the live code anchors they rely on
- measure current ChiefWriter signature sizes directly
- classify each defer claim as `supported`, `partially supported`, or `not supported`

## 3. Audit Matrix

| Claim | Opus Direction | Live Verdict | Audit Correction |
| --- | --- | --- | --- |
| `state_changes schema formalization` is a real deferred structural gap | T5 / merge audit | `supported` | keep as a top defer item |
| `technique/realm canonical authority` is the top deferred risk | T5 / chat summary | `partially supported` | narrow to `realm owner + NPC technique-model gap`; do not describe as broadly unguarded |
| `provider identity / usage normalization consolidation` is a real deferred consolidation seam | T2 / merge audit | `supported` | keep below fact-contract cluster |
| `writer/context request-shape cleanup` remains a major structural inelegance | T4 / merge audit | `partially supported` | still true in shape, but some local bundling already exists and the old parameter count label is stale |
| ``_god1_*` replacement` remains a real deferred cleanup | T3 / merge audit | `supported` | keep deferred and low in the stack |

## 4. Detailed Findings

### 4.1 `state_changes schema formalization`

Verdict: `supported`

Why:
- `StateTracker` still emits a wide ad hoc `state_changes` dict with many optional keys.
- `StateTrackerNPC` still reads that dict field-by-field and falls back to regex extraction when fields are missing.
- `WorldState` still consumes `state_changes` via repeated `.get()` access across multiple update sections.
- no `TypedDict` or equivalent typed schema for `state_changes` was found in the inspected runtime files.

Live anchors:
- `modules/domain/agents/state_tracker.py:1609-1626`
- `modules/domain/agents/state_tracker_npc.py:830-849`
- `modules/domain/agents/state_tracker_npc.py:882-920`
- `modules/domain/agents/state_tracker_npc.py:940-989`
- `modules/core/world_state.py:697-726`

Audit judgment:
- Opus was right to keep this deferred
- this is a real producer/consumer contract problem
- this deserves promotion above more aesthetic cleanup work

### 4.2 `technique/realm canonical authority`

Verdict: `partially supported`

What Opus got right:
- there is still no clean canonical persisted owner for protagonist `realm` in the inspected slice
- NPC technique/realm ownership is still missing
- the remaining gap is still the main wuxia-specific fact seam

What Opus overstated:
- the live system is not broadly unguarded anymore
- protagonist-side technique handling already exists in multiple places

Live evidence that narrows the claim:
- protagonist skill accumulation exists in `StateTracker`
- protagonist skill summaries are still emitted as an advisory domain
- Stage 4 injects a wuxia-only technique/realm authority clause
- `BlockingValidator` always runs a protagonist technique-vs-realm consistency check
- `WuxiaGuard` still enforces `realm_technique_limits`

Live anchors:
- `modules/domain/agents/state_tracker.py:141-142`
- `modules/domain/agents/state_tracker.py:1394`
- `modules/core/stage4_context_builder.py:1716-1730`
- `modules/validation/blocking_validator.py:130-133`
- `modules/validation/blocking_validator_consistency_checks.py:375-429`
- `modules/core/genre_guards/wuxia_guard.py:181-182`
- `modules/core/genre_guards/wuxia_guard.py:303-308`
- `modules/core/world_state.py:764-774`
- `modules/core/world_state.py:849-860`

Audit judgment:
- keep the item
- rename it in top-level planning as `realm authority / NPC technique-model gap`
- do not carry forward the older broad wording unchanged

### 4.3 `provider identity / usage normalization consolidation`

Verdict: `supported`

Why:
- provider identity still exists in three places:
  - router inference
  - metrics inference
  - generate-bridge overwrite
- usage normalization still happens in `BaseAgent`, while providers return mixed raw usage shapes
- no single shared identity-and-usage utility exists in the inspected surfaces

Live anchors:
- `modules/core/llm_router.py:119-134`
- `modules/core/metrics_collector.py:101-105`
- `modules/core/llm_generate.py:24-30`
- `modules/domain/agents/base_agent.py:396-414`
- `modules/core/providers/gemini_provider.py:32-41`
- `modules/core/providers/anthropic_provider.py:76-82`
- `modules/core/providers/openai_provider.py:91-98`

Audit judgment:
- Opus was correct
- this remains a real deferred consolidation seam
- the lane is still mostly contract drift, not the strongest correctness seam

### 4.4 `writer/context request-shape cleanup`

Verdict: `partially supported`

What Opus got right:
- the request surface is still oversized
- the forwarding chain is still a real structural inelegance

What Opus overstated:
- the old `35-parameter` label no longer describes live code precisely
- some local bundling has already happened, so the lane is not as untouched as the older wording implies

Current measured signature sizes:
- `ChiefWriter.generate_ensemble`: `36` params excluding `self`
- `ChiefWriter._prepare_generate_ensemble_context`: `32`
- `ChiefWriterContextBuilder.build_common_context`: `31`
- `build_chief_writer_main_prompt`: `34`

Existing partial cleanup:
- `stage4_interview_round.py` assembles `_common_writer_kwargs` once
- `chief_writer.py` builds a per-candidate `request_bundle`

Live anchors:
- `modules/domain/agents/chief_writer.py:560-607`
- `modules/domain/agents/chief_writer.py:790-820`
- `modules/domain/agents/chief_writer_context.py:114`
- `modules/domain/agents/chief_writer_prompts.py:50`
- `modules/core/stage4_interview_round.py:2053-2078`

Audit judgment:
- keep the defer item
- downgrade the exact old wording
- rank it below fact-contract and provider-normalization work

### 4.5 ``_god1_*` replacement`

Verdict: `supported`

Why:
- the hidden owner-to-runtime handoff is still live
- the consumer still uses `getattr(owner, "_god1_*", None)`
- the producer still sets 7 `_god1_*` fields
- one `_god1_*` value is written back and later re-read

Live anchors:
- `modules/core/stage4_interview_round.py:2270-2293`
- `modules/core/stage4_director_runtime.py:102-110`
- `modules/core/stage4_director_runtime.py:167`
- `modules/core/stage4_interview_round.py:4608`

Measured field inventory:
- `_god1_arc_data`
- `_god1_arc_pos`
- `_god1_director_memory_context`
- `_god1_prev_manuscript`
- `_god1_round_num`
- `_god1_stage4_spinner`
- `_god1_total_ep_in_arc`

Audit judgment:
- Opus was correct
- keep this deferred
- its narrow scope and existing comments still make it lower priority than the broader contract items

## 5. Overall Verdict On The Opus Bundle

Overall verdict: `usable but needs correction at the top layer`

What remains valid:
- no merged P0
- cheap-fix-first framing
- the provider lane is a real deferred contract-normalization seam
- `_god1_*` is still a real long-term cleanup

What needed correction:
- the fact lane was too broad in how it described `technique/realm`
- the writer lane was too literal in how it described the forwarding count

Operational consequence:
- keep using the Opus docs as source surveys
- use the new top-level freeze doc, not the raw Opus phrasing, for defer ordering

## 6. Side-Effect Coverage

Not applicable for runtime side effects in this turn.

This audit was static only:
- no code patch
- no DB write
- no execution queue change
- no temp execution mirror

Current queue truth:
- `docs/temp/queue-state.json` reports `queue_mode: empty`

## 7. Confidence And Limits

Estimated confidence: `96%`

Why:
- all audited claims were checked against live code, not only survey prose
- two claims were materially corrected rather than rubber-stamped
- cross-checks included independent signature counting and handoff field inventory

Limits:
- static-only audit; no fresh runtime run was performed
- this audit only re-scoped the defer claims, not the already closed Wave 1 implementation results

## 3-Pass Audit Record

### Pass 1. Structure and Scope
- kept the document focused on validating Opus claims against live code
- separated scope, matrix, and detailed findings
- PASS

### Pass 2. Evidence and Consistency
- verified each deferred claim against current source files
- corrected over-broad or stale wording where needed
- confirmed queue truth independently
- PASS

### Pass 3. Execution and Readability
- made the operating consequence explicit
- tied the audit to the new top-level freeze doc
- trimmed any move toward execution planning
- PASS

