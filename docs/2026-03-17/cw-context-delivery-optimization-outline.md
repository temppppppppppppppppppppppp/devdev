# CW Context Delivery Optimization Outline

Date: 2026-03-17
Status: draft
Canonical Path: `docs/2026-03-17/cw-context-delivery-optimization-outline.md`
Document Type: planning note
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Scope:
- optimize how context is delivered to Chief Writer so the pipeline produces better manuscripts through a better process
- focus on structure, timing, packaging, and authority of context handoff
- do not assume any one model is the subject; treat context delivery design as the main variable
Non-Goals:
- no code changes in this note
- no final execution queue in this note
- no claim that the outline is 3-pass finalized yet

## 0. Live Snapshot
- current live path already does a decent job on retry-time context, especially through `previous_attempt`, retry provenance, and Director-mediated feedback
- current live path is weaker on first-write guidance: CW sees large mandatory context and truth material, but not yet a concise `Pre-Write Pack`
- continuity carry-over is materially better than before because `relationship_changes` and `active_pressure_vectors` now persist and re-enter Stage 4
- style signals like `ai_slop`, `ced_score`, and `dialogue_ratio` are currently more useful after failure than before first draft

### Current Code Touchpoints
- pre-write context assembly: `modules/core/stage4_context_builder.py` -> `build_mandatory_context()`
- CW input handoff: `modules/core/stage4_interview_round.py` -> `_build_common_writer_kwargs()` and Stage 4 run path
- retry-time evidence handoff: `modules/core/stage4_interview_round.py` -> `_build_retry_feedback_provenance()`
- carry-over persistence source: `modules/core/stage4_post_processor.py`

## 0A. Working Assumptions
- better manuscripts should come from better context architecture, not just stronger retry pressure
- CW should see sparse, usable guidance before writing and more explicit evidence after failure
- Python may extract candidate facts and low-level seeds, but final meaning and priority stay with LLM/Director
- the first useful improvement is likely a concise `Pre-Write Pack`, not a larger mandatory context blob

## 0B. Current-State Mapping
- estimated `Pre-Write Pack` readiness: partial only; truth base and carry-over exist, but `soft style guidance`, `forbidden regression`, `character intent`, and `freedom zone` are weak or absent
- estimated `Repair Pack` readiness: stronger; reject bucket, evidence summary, action items, fix scope, and retry provenance already survive reasonably well
- immediate design implication: improve first-write briefing before adding more retry complexity

## 1. Problem Framing
- What kinds of context help CW write better before failure?
- What kinds of context help CW revise better after REJECT?
- Which context forms improve quality without flattening prose or over-constraining generation?

## 2. Survey Boundary
- Stage 4 CW prompt inputs
- Director-mediated retry feedback
- validator/advisory evidence that survives into `previous_attempt`
- continuity and world-state carry-over that affects writing quality
- context budget, section ordering, and truncation behavior

## 3. Context Taxonomy
- truth and continuity context
- style and anti-slop context
- retrieval and coverage context
- rewrite directives and reject rationale
- process memory from previous attempts

## 4. Timing Windows
- pre-generation guidance
- same-round candidate selection and rejection
- post-REJECT retry context
- repeated-failure escalation context
- post-episode persistence and next-episode re-entry

## 5. Delivery Forms
- raw metric exposure
- natural-language digest
- structured evidence block
- ranked evidence shortlist
- hybrid delivery: soft pre-guidance + strong retry evidence

## 6. Authority Design
- what CW should see directly
- what should stay Director-mediated
- what should remain validator-only evidence
- where Python may measure but must not decide

### Authority Boundary Agreed In Brainstorm
- Python may produce bounded seed candidates only
- a bounded curator layer is acceptable only as a `skill`, not as a new free-judgment agent
- Director remains the final editor/approver of any CW-facing pack
- CW should consume only the approved pack, never raw seeds or raw validator output

## 7. Quality Tradeoffs To Measure
- pass/reject improvement
- manuscript quality improvement
- prose flattening risk
- over-guidance and template drift
- token and context budget cost

## 8. Investigation Method
- inventory current producer -> handoff -> consumer path
- classify contexts by timing, authority, and format
- compare current path against desired writing outcomes
- identify dead, weak, overloaded, or badly-timed context surfaces

### Suggested Initial Survey Pass
- trace current `mandatory_context` ordering and section density
- identify which currently injected sections are `must preserve`, `nice to know`, or likely noise
- map which retry-only signals could be translated into lighter pre-write guidance without leaking raw metrics
- identify which context items are deterministic enough for Python seed extraction and which require Director judgment

## 9. Candidate Structural Improvement Themes
- give weaker natural-language style guidance earlier
- reserve stronger evidence for Director-mediated retry
- rank context by actionability rather than by source only
- separate "must preserve truth" from "should improve style"
- tune context intensity across repeated retries instead of one fixed payload

### Candidate Pre-Write Pack Fields
- `Episode Objective`
- `Character Intent`
- `Carry-Over Focus`
- `Forbidden Regression`
- `Soft Style Guidance`
- `Reference Anchor`
- `Freedom Zone`

### Safe Automation Boundary
- automate first: `Carry-Over Focus`, `Forbidden Regression`, `Reference Anchor`, and a weak `Soft Style Skeleton`
- keep Director-owned: `Episode Objective`, `Character Intent`, and `Freedom Zone`
- prefer `seed candidates -> curator skill -> Director approval -> CW` over direct Python-to-CW handoff

## 10. Desired Outputs From The Full Survey
- context delivery inventory
- failure pattern taxonomy
- recommended handoff architecture
- staged rollout plan for safe experimentation
- acceptance criteria for "better process, better manuscript"

### Rollout Shape Agreed So Far
- `v1`: Python seed extraction in shadow mode only
- `v1.5`: Director shadow approval on curator output
- `v2`: limited CW injection of `carry_over_focus` and `forbidden_regression`
- postpone broader style automation or full pack rollout until low-noise behavior is proven

### Overengineering Boundary
- full automation of interpretation is out of scope for now
- adding more retry-time complexity before fixing first-write guidance is likely the wrong order
- large new agent stacks are less desirable than one bounded `PreWrite Pack Curator` skill

## 11. Brainstorming Questions
- What should CW know before writing versus only after failing?
- Which context categories deserve hard persistence versus ephemeral advisory?
- How much style guidance is useful before it starts poisoning voice?
- Should retry context escalate by round count, reject bucket, or issue family?

## 12. Open Questions To Resume Later
- where exactly should the `Pre-Write Pack` sit inside `mandatory_context` ordering
- how much of `Stage 2 failure context` should remain visible on first write rather than retry only
- whether `soft style guidance` should stay purely Director-authored in v1
- what log or shadow evidence is minimally sufficient to judge noise before CW-facing rollout
