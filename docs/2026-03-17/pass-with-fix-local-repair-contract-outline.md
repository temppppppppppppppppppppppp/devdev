# PASS_WITH_FIX Local Repair Contract Outline

Date: 2026-03-17
Status: draft
Canonical Path: `docs/2026-03-17/pass-with-fix-local-repair-contract-outline.md`
Document Type: planning note
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Scope:
- refine `PASS_WITH_FIX` into a narrow local-repair contract for Stage 4
- improve process clarity before any code change or execution queue work
- focus on verdict semantics, fix-pack structure, local-repair eligibility, and bounded rollout
Non-Goals:
- no code changes in this note
- no final execution SSOT or roadmap in this note
- no claim that the outline is 3-pass finalized yet

## 0. Live Snapshot
- current `PASS_WITH_FIX` loop is already safer than a naive patch loop: it is bounded, keeps patch provenance, and re-audits through Director
- current weakness is not raw safety but semantic width: the verdict still covers more than a strict local-repair contract
- current repair payload is actionable but still text-heavy; a smaller structured `Fix Pack` would likely reduce ambiguity
- score fallback still appears in local-repair routing and should eventually be secondary to issue-family and repairability judgment

### Current Code Touchpoints
- verdict processing: `modules/core/stage4_interview_round.py` -> `_process_verdict()`
- patch loop: `modules/core/stage4_interview_round.py` -> `_execute_pass_with_fix_loop()`
- reject/retry routing after failed repair: `modules/core/stage4_interview_round.py` -> `_handle_reject()` and `_generate_candidates()`
- current repair-text extraction: `modules/core/stage4_interview_round.py` -> `_extract_fix_feedback()`

## 0A. Working Assumptions
- the main value of `PASS_WITH_FIX` is fast local salvage, not broad rewrite avoidance at any cost
- a verdict that is semantically blurry makes patching noisier even if the loop itself is technically safe
- any repair lane that cannot name target scope, protected scope, and success condition should probably be `REJECT`
- improving `PASS_WITH_FIX` should start with semantics and payload shape before adding heavier policy or automation

## 1. Problem Framing
- `PASS_WITH_FIX` currently works as a safe patch loop, but its meaning is still broader than a true local-repair contract.
- some cases that should go directly to `REJECT` can still drift into patch semantics before being pushed back out.
- the process is safer than before, but the meaning of the verdict and the shape of the repair payload can still be made clearer.

## 2. Target State
- `PASS_WITH_FIX` means only: local, bounded, inplace-repairable issue
- `REJECT` means: anything that needs partial/full rewrite, structural repair, or broad continuity recovery
- the patch loop receives a structured `Fix Pack`, not a loose text bundle

### Why This Matters
- avoids wasting local patch attempts on problems that actually need rewrite
- makes Director re-audit easier because repair intent is explicit
- makes logs and later analysis more meaningful because `PASS_WITH_FIX` becomes a cleaner class of event

## 3. Verdict Semantics
- `PASS`: accepted without repair
- `PASS_WITH_FIX`: repairable by local inplace patch only
- `REJECT`: rewrite or broader repair required

## 4. Local-Repair Eligibility Rule
- patch target can be named precisely
- protected areas can be named precisely
- success condition can be written in one short sentence
- repair does not require blueprint/frontier redesign
- repair does not require broad truth/continuity restoration

### Director Check Questions
- can I point to the exact segment or beat to repair
- can I state what must not change during repair
- can I describe success without re-evaluating the whole manuscript architecture
- if this repair succeeds, would I still need a broader rewrite

## 5. Cases That Likely Fit PASS_WITH_FIX
- ending tension is weak but the scene structure is otherwise sound
- local transition or connective tissue is weak
- wording/rhythm/delivery needs line-level repair
- payoff beat exists but needs sharper local emphasis
- a small continuity stitch is missing inside an otherwise correct scene structure

## 6. Cases That Should Go Straight To REJECT
- blueprint function is missing
- active threat carry-over is broadly missing
- relationship carry-over is broadly missing
- truth or continuity conflict is the core issue
- scene order or narrative structure needs redesign
- multiple issue families break at once

## 7. Fix Pack Draft Shape
- `fix_scope`
- `must_fix`
- `do_not_regress`
- `patch_targets`
- `success_condition`
- `evidence_summary`

### Fix Pack Intent
- `must_fix` is the smallest set of changes that justifies a local repair attempt
- `do_not_regress` protects already-correct continuity, threat, relationship, or emotional beats
- `patch_targets` keeps the patch lane surgical rather than manuscript-wide
- `success_condition` prevents Director re-audit from drifting into vague "better or not" judgment

## 8. Fix Pack Principles
- keep `must_fix` to the smallest actionable set
- keep `do_not_regress` explicit so patch scope stays narrow
- require `patch_targets` to point to scene/segment scope, not vague whole-manuscript advice
- translate evidence into repairable guidance rather than dumping validator internals

## 9. Patch Loop Improvement Themes
- narrow the verdict before patch begins
- separate patch lane from rewrite lane more cleanly
- run a light quick-check before Director re-audit
- preserve patch provenance so the same weak local fix is not repeated blindly

### Minimal v1 Direction
- keep the existing bounded patch loop
- clarify when that loop should be entered
- replace loose repair text with a smaller `Fix Pack`
- keep broader policy learning and automation out until the new semantics are stable

## 10. Minimal Rollout Order
- clarify verdict semantics first
- introduce `Fix Pack` second
- consider light patch-lane separation third
- postpone deeper automation or policy learning until the semantics are stable

### Stop Line
- if the semantics alone materially reduce noisy patch attempts, stop there before building more
- if `Fix Pack` alone makes repair clearer, stop there before adding new lanes or extra automation
- treat observability-heavy or policy-heavy follow-ons as optional later work, not baseline v1 work

## 11. Overengineering Boundary
- semantics clarification is not overengineering
- `Fix Pack` structure is not overengineering
- deeper scoring policy, adaptive routing, or separate automation agents likely are overengineering for now

## 12. Brainstorming Questions
- which current `PASS_WITH_FIX` buckets are truly local-repairable?
- what is the smallest useful `Fix Pack` that improves clarity without bloating prompts?
- how should Director decide local-repair eligibility without relying on score too heavily?
- where should the boundary sit between patchable continuity stitch and rewrite-required continuity failure?

## 13. Open Questions To Resume Later
- whether local-repair eligibility should be keyed mainly by issue family, target scope clarity, or both
- whether the first quick-check should be continuity-first, style-first, or bucket-specific
- how much patch provenance should be shown to Director on re-audit before it becomes noise
- whether `PASS_WITH_FIX` should remain a visible verdict label or be renamed internally while keeping external semantics stable
