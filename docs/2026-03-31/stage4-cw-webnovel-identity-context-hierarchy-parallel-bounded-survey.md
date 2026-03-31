# Stage4 CW Webnovel Identity / Context Hierarchy Parallel Bounded Survey

Date: 2026-03-31
Status: draft-live-run-pending
Confidence: 93% (final save blocked until the active `0_2` frontier run reaches terminal state)
Document Type: bounded synthesis survey
Canonical Path: `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-parallel-bounded-survey.md`
Temp Mirror Path: `(none - live-run pending; docs/temp forbidden)`
Baseline Commit: `170963d34d30d3076a57926c5d1ed250f13ec421`
Baseline Dirty Summary: `active 0_2 frontier-run logs/db/ui mutation in progress; 0_temp console scratch dirty`
Track: system
Mode: live-merge synthesis (`static lane survey + active frontier run + deferred post-run final audit`)
Run State: `in_progress`
Source Harnesses:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/live-run-merge-survey-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
Source Lane Drafts:
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane1-prompt-topology-draft.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane2-context-delta-draft.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane3-stage2-stage3-upstream-draft.md`
- `docs/2026-03-31/stage4-cw-webnovel-identity-context-hierarchy-lane4-runtime-symptom-taxonomy-draft.md`

## 1. Answer-First

### Hard conclusions

1. Current `CW first-pass miss` is primarily a `prompt/context hierarchy failure` plus `Stage 3 contamination`, not a clean "model is bad at webnovel writing" diagnosis.
2. The first-pass prompt is structurally `an analyst workflow with a writer label`:
   - explicit writer identity is thin
   - detailed writing rules are late
   - analytical/HUD/advisory/report blocks dominate the middle of the prompt
   - the largest prior-manuscript truth block is injected last
   Evidence: `modules/domain/agents/chief_writer_prompts.py:50-205`, `modules/domain/agents/chief_writer_context_packets.py:173-205`.
3. Retry performs better not because retry has a cleaner prompt, but because retry adds explicit conflict framing, reuse constraints, and narrower task shape on top of the same base prompt.
   Evidence: `modules/domain/agents/chief_writer.py:627-714`, `modules/domain/agents/chief_writer.py:1016-1052`, `modules/core/stage4_interview_round.py:2488-2494`.
4. Stage 3 is currently leaking meta/system/genre contamination into Stage 4 for `0_2` EP2:
   - `integrated_scenario` contains HUD/status-window language and recap-style prose
   - `scene_breakdown.key_events` repeats the same contamination in structured contract form
   Evidence: `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json:59`, `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json:95-101`.
5. The current `EP2` bad sentence is mixed, but the primary defect is still `hard truth conflict`:
   - fabricated hologram/status-window entity
   - wrong asset breakdown
   - briefing/recap register is secondary
   Evidence: `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_02/selected_before_fix__A.txt:19-25`, `projects/0_2/drafts/ep_0001.txt:91-97`, `modules/core/flashback_verifier.py:21-29`.

### Medium-confidence conclusions

1. Stage 2 is not the main source of the current briefing-style contamination, but Stage 2 fact under-specification can still widen numeric drift in downstream blueprint/manuscript generation.
2. The system has no strong detector for `briefing prose`, `recap register`, or `webnovel voice collapse` when those defects do not also create a hard truth conflict.
3. The current prompt already says "writer," but it does not strongly say "you are not an analyst/summarizer/briefing engine," so register drift is easy.

### Not supported by current evidence

1. `CW does not know it is writing a webnovel` is too strong.
   - role and writing-rule blocks do exist.
2. `model tier is the primary problem` is not supported by the current four-lane evidence.
3. `Stage 2 is the primary culprit` is not supported.
   - Stage 3 and Stage 4 consumption are more implicated.

## 2. Required Questions

### Q1. Is CW explicitly conditioned as a serialized webnovel writer, not an analyst/summarizer?

Partially, but too weakly.

- Writer identity exists in `chief_writer_prompts.py`, but it is only a thin role/task shell near the top: `modules/domain/agents/chief_writer_prompts.py:50-62`.
- Detailed writing rules exist, but appear near the end: `modules/domain/agents/chief_writer_prompts.py:203-205`.
- There is no equally explicit negative contract such as:
  - not a summarizer
  - not a briefing engine
  - not a report writer

Answer: `yes, but weak and positionally overwhelmed`.

### Q2. Which blocks behave like bad few-shot contamination?

Highest-risk contamination blocks:

| Block | Why It Contaminates |
| --- | --- |
| `prev_digest` | recap/report register |
| `hud_report`, `high_density_hud_section`, `hud_trend_section` | dashboard/system register |
| `hud_anomaly_section` | diagnostic alert register |
| `npc_frequency_section` | statistics/report register |
| `integrated_scenario_advisory_section` | long-form planning/advisory prose |
| `opening_anchor_section` | contract-style wording rather than scene model |
| `constraint_section`, `future_guard_section`, `past_guard_section` | QA/guard/inventory framing |
| `prev_manuscripts_section` with "truth source" header | prior prose is framed as evidence to verify, not craft to emulate |

Primary anchors:
- `modules/domain/agents/chief_writer_prompts.py:106-205`
- `modules/domain/agents/chief_writer_context_packets.py:173-205`

### Q3. Are the layers separated or mixed?

They are mixed.

| Layer | Current State | Gap |
| --- | --- | --- |
| `Writer Identity Layer` | present but thin | not dominant enough |
| `Hard Canon Layer` | present but scattered across the prompt | not physically consolidated |
| `Episode Mission Layer` | present | mixed with soft guidance and reporting blocks |
| `Carryover Layer` | present | partly mixed with analytical reporting |
| `Soft Guidance Layer` | present | not clearly isolated as soft |
| `Anti-Pattern Layer` | present but narrow | bans system words more than briefing register |

Critical mixed block:
- `writer_core_section` concatenates `world_state_section`, `mandatory_context`, `anti_trope_prompt`, `justification_prompt`, `reflexion_prompt` into one undifferentiated blob.
- Anchor: `modules/domain/agents/chief_writer_context.py:494-518`.

### Q4. What are the concrete differences between first-pass and retry prompt/context shape?

Retry reuses the same base prompt and adds narrow, actionable framing.

| Dimension | First-Pass | Retry |
| --- | --- | --- |
| Base prompt template | same | same |
| Base context volume | large | same large base plus more |
| Director feedback | empty or light | explicit and accumulated |
| Failure constraints | absent | explicit |
| Conflict contract | absent | explicit |
| Reuse contract | absent | explicit |
| Task shape | "write EP2" | "write EP2 without these exact failures" |

Primary anchors:
- `modules/domain/agents/chief_writer.py:627-714`
- `modules/domain/agents/chief_writer.py:1016-1052`
- `modules/domain/agents/chief_writer.py:1970-2026`
- `modules/core/stage4_interview_round.py:2488-2494`

Answer: `retry is not cleaner; retry is more directed`.

### Q5. Is Stage 2 or Stage 3 already generating under-specified or briefing-shaped scene authority before CW starts?

Mostly Stage 3.

- Current Stage 3 blueprint for EP2 injects:
  - HUD/status-window framing
  - recap/meta-style episode carryover language
  - structured key-event contamination
- Evidence:
  - `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json:59`
  - `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json:95-101`
- Stage 3 prompt does not strongly forbid briefing prose or genre contamination in `integrated_scenario`:
  - `config/prompts/ensemble.yaml:340-397`
- Stage 3 also re-injects prior blueprint scenario prose:
  - `modules/domain/agents/blueprint_ensemble.py:1124-1136`

Stage 2 is secondary:
- it can leave quantitative details under-specified, which makes numeric drift easier later
- but the current meta/system contamination is more strongly Stage 3-shaped than Stage 2-shaped

### Q6. In current `0_2` EP2, is the bad sentence primarily truth conflict, meta prose, both, or misclassification?

`both`, but `truth conflict` is primary.

Problem sentence cluster:
- `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_02/selected_before_fix__A.txt:19-25`

Why primary family is hard truth conflict:
- hologram/status window is fabricated
- "직전 화에서 확인했던 자신의 상태창" is false recall
- numeric decomposition conflicts with EP1 baseline

Why meta/briefing prose is still relevant:
- the wording reads like recap/confirmation prose rather than lived scene prose
- this is a real stylistic defect, but it is not the main reason this candidate should fail

Downstream detector verdict:
- `FlashbackVerifier` found a real issue through an imprecise path
- post-select continuity/history checks classified it more correctly
- anchors:
  - `modules/core/flashback_verifier.py:21-29`
  - `modules/core/stage4_interview_round.py:3994-4178`

### Q7. What bounded remediation seams have the highest ROI?

Provisional ranking:

1. `CW writer identity / anti-briefing hardening`
   - strong "you are a serialized webnovel writer" contract
   - strong "you are not a summarizer/analyst/briefing engine" negative contract
2. `Context hierarchy separation`
   - consolidate hard canon early
   - isolate soft guidance/advisory later
   - stop mixing hard canon and craft guidance in `writer_core_section`
3. `Stage 3 blueprint anti-briefing hardening`
   - forbid HUD/meta/system/genre contamination in `integrated_scenario`
   - tighten `scene_breakdown.key_events`
4. `Anti-meta / recap-register detector`
   - new detector or bounded pattern layer for briefing prose that survives truth checks
5. `Stage 2 fact anchoring where later numeric continuity depends on it`

## 3. Root Cause Stack

### RC-1. Writer identity exists, but is not the authority surface

The prompt says "Chief Writer," but the actual cognitive load is dominated by:
- digests
- HUDs
- advisories
- constraints
- guard lists
- statistics

The model is therefore nudged into `analysis/synthesis` register before it reaches the strongest craft rules.

Anchors:
- `modules/domain/agents/chief_writer_prompts.py:106-205`
- `modules/domain/agents/chief_writer_context_packets.py:173-205`

### RC-2. Hard canon is present but physically scattered

The problem is not absence of canon.

The problem is:
- canon is distributed across many blocks
- `prev_manuscripts_section` comes last
- `writer_core_section` mixes hard canon and soft instruction in one block

Anchors:
- `modules/domain/agents/chief_writer_context.py:177-267`
- `modules/domain/agents/chief_writer_context.py:494-518`
- `modules/domain/agents/chief_writer_context_packets.py:173-205`

### RC-3. Stage 3 is feeding CW contaminated authority

The current EP2 blueprint contains:
- status-window/HUD language
- recap/meta carryover phrasing
- wrong numeric decomposition

This is upstream contamination before CW writes prose.

Anchors:
- `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json:59`
- `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_01/patched_blueprint_after_fix__V75-D_blueprint_inplace.json:95-101`
- `modules/domain/agents/blueprint_ensemble.py:1124-1136`
- `config/prompts/ensemble.yaml:354`

### RC-4. Retry helps because it sharpens task shape

EP2 runtime evidence:

| Round | Score | Result | Why |
| --- | --- | --- | --- |
| R0 | 95 | REJECT | opening-anchor / hard-canon miss |
| R1 | 95 | REJECT | same plus flashback/history advisory |
| R2 | 94 | PASS | explicit conflict feedback narrowed the task |

Anchor:
- `projects/0_2/logs/session/decisions.jsonl:8-10`

This supports:
- not "CW is fundamentally incapable"
- but "CW first-pass is under-specified and over-contaminated"

### RC-5. The current runtime symptom is mixed, but the blocking defect is still truth

Bad sentence cluster:
- `projects/0_2/logs/artifacts/stage4/ep_0002/attempt_02/selected_before_fix__A.txt:19-25`

Canonical EP1 truth:
- `projects/0_2/drafts/ep_0001.txt:91-97`

Meaning:
- if the sentence had perfect webnovel prose but kept the fake status window and wrong numbers, it would still deserve rejection
- if the sentence had briefing-style prose but no hard truth conflict, the current system might miss it

## 4. Detector Gap Inventory

### Existing detectors that are working

1. `post-select continuity/history checks`
   - strong and correctly blocking for the current EP2 symptom
2. `FlashbackVerifier`
   - not perfectly labeled here, but it did surface a real problem

### Missing or weak detectors

| Gap | Why It Matters |
| --- | --- |
| Anti-meta / briefing prose | current pipeline can miss briefing prose if no truth conflict accompanies it |
| Recap-register detector | "직전 화에서 확인했던..." type prose can slip unless another truth conflict exposes it |
| Fabricated-entity pre-gate | status-window-style fabrication is often caught only post-select |

## 5. Execution Readiness

Static evidence is already strong enough to justify a future execution wave, but not a final SSOT close.

What is justified after the frontier run finishes:

1. `CW writer-identity / anti-briefing prompt hardening`
2. `Context hierarchy separation`
3. `Stage 3 integrated_scenario / scene_breakdown anti-contamination hardening`
4. `Anti-meta / recap-register detector seam`

What is not yet justified as a primary wave:

1. model-tier replacement
2. "CW is broken" diagnosis
3. Stage 2-first remediation

## 6. Post-Run Merge Audit Watchlist

Because the frontier run is still active, the following must be re-checked after terminal state:

1. Does briefing/recap prose recur even when no hard truth conflict exists?
2. Does Stage 3 continue to emit HUD/system/genre contamination for later episodes?
3. Does retry continue to rescue first-pass misses by explicit conflict narrowing rather than baseline quality?
4. Do any later episodes show pure webnovel-voice collapse without continuity/history conflict?

## 7. Save Gate

This document is intentionally not final.

Reason:
- `projects/0_2` frontier run is still mutating authoritative runtime sinks
- live-merge governance forbids freezing canonical final conclusions before terminal run state

Upgrade rule:
- after run terminal state, perform post-run merge audit
- rerun 3-pass audit
- require confidence `>= 95%`
- then upgrade this topic into final canonical survey conclusions
