# Retry Budget Policy Outline

Date: 2026-03-17
Status: draft
Canonical Path: `docs/2026-03-17/retry-budget-policy-outline.md`
Document Type: planning note
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Scope:
- preserve brainstorming context around Stage 4 retry budget semantics
- focus on round budget, generation strategy budget, escalation budget, and retry guidance injection
- keep the note at planning level without opening an execution queue
Non-Goals:
- no code changes in this note
- no claim that the note is 3-pass finalized
- no execution SSOT, roadmap, or implementation order in this note

## 0. Live Snapshot
- current Stage 4 retry policy is not simply "too many retries" or "too few retries"
- the real issue is semantic spread: multiple retry budgets exist, but they are not named or governed as one coherent policy
- round count, repair path, strategy budget, escalation tools, and retry guidance all exist already, but they are split across several functions and timing layers
- the system is safer than a naive fixed retry loop, but the operator-visible logic is harder to read than necessary

### Current Code Touchpoints
- round orchestration and candidate generation entry:
  - `modules/core/stage4_interview_round.py` -> `run()`
  - `modules/core/stage4_interview_round.py` -> `_generate_candidates()`
- PASS_WITH_FIX bounded local repair loop:
  - `modules/core/stage4_interview_round.py` -> `_execute_pass_with_fix_loop()`
- REJECT bucket classification, ToT/MAD escalation, and next-round state assembly:
  - `modules/core/stage4_interview_round.py` -> `_handle_reject()`
- adaptive retry guidance and ultimate recommendations:
  - `modules/core/adaptive_retry.py` -> `AdaptiveRetryManager`
- strategy budget handling inside writer ensemble:
  - `modules/domain/agents/chief_writer.py` -> `_select_ensemble_strategies()` / `generate_ensemble()`

## 0A. Working Assumptions
- retry quality improves when "how many times", "how broadly", "with which strategy budget", and "with which escalation tools" are separated clearly
- current Stage 4 behavior already has enough raw mechanisms; the main gap is policy readability and policy shape
- score should not dominate routing when fix scope and reject bucket already provide stronger local signals
- heavy automation is not needed yet; first priority is naming and aligning the existing retry layers

## 1. Main Finding
- current Stage 4 retry behavior already contains at least four different budget types:
  - round budget
  - generation budget
  - escalation budget
  - guidance budget
- because these layers are not surfaced as a single policy model, the retry path feels more ad hoc than it actually is

## 2. The Four Existing Retry Budgets

### 2.1 Round Budget
- round 0 always runs a full ensemble generation
- current default shape:
  - round 0 -> full budget, three strategies
  - later rounds -> route through repair or regenerate logic
- this is the outer budget envelope

### 2.2 Generation Budget
- retry generation currently selects among:
  - inplace patch
  - patch-with-feedback
  - regenerate-with-feedback
- key inputs:
  - `fix_scope`
  - `reject_bucket`
  - fallback score thresholds
- this is the most operationally important retry budget today

### 2.3 Escalation Budget
- certain reject buckets open stronger tools:
  - `structure_error` -> ToT guidance
  - `constraint_violation` -> MAD guidance
  - `round_num >= 2` with prior attempt -> ASP correction candidate
- these tools are already acting like an escalation budget, even though the policy is not named that way

### 2.4 Guidance Budget
- retry context also thickens through prompt-side guidance:
  - Director feedback
  - retry provenance
  - adaptive retry injection prompt
- this means retry policy is not only about generation strategy count; it is also about how much repair context is injected

## 3. Current Strengths
- round 0 is simple and stable: full ensemble with predictable starting shape
- local repair paths exist before full rewrite, which avoids wasting rewrite effort on clearly local fixes
- escalation tools are bucket-aware rather than randomly applied
- tests already pin down several important semantics:
  - reduced strategy budget for `constraint_violation`
  - full strategy budget for `structure_error`
  - post-select conflict patch preference on early retry

## 4. Current Weaknesses

### 4.1 Budget Meaning Is Split Across Multiple Fields
- `fix_scope`, `reject_bucket`, `score`, and `round_num` all influence routing
- no single field explains the retry budget policy for a given attempt

### 4.2 Score Fallback Is Too Central
- routing still falls back to score thresholds when fix scope is absent
- this makes retry strategy feel partially score-driven even when better structural signals exist

### 4.3 Escalation Triggers Are Heterogeneous
- ToT and MAD are bucket-driven
- ASP is round-driven
- adaptive guidance is failure-record driven
- these triggers are not yet presented as one coherent escalation ladder

### 4.4 Prompt Thickness Is Not Co-Governed With Retry Budget
- later retries usually become context-heavier, but this is not controlled by an explicit round policy
- retry budget therefore remains only partially visible at the prompt-design layer

## 5. Practical Reading Of Current Policy
- round 0 = wide search
- early retry = local repair first when plausible
- regenerate narrows strategy budget only for certain bucket families
- escalation tools appear as issue-specific overlays rather than one explicit budget ladder
- repeated failure can therefore feel uneven even when it is technically following code

## 6. V1 Target Model

### 6.1 `round_budget`
- explicit outer retry stage
- examples:
  - `r0_explore`
  - `r1_repair_first`
  - `r2_targeted_regenerate`
  - `r3_escalated_last_try`

### 6.2 `repair_budget`
- how broad the text intervention may be
- examples:
  - `none`
  - `inplace`
  - `patch`
  - `rewrite`

### 6.3 `strategy_budget`
- how many writer strategies are active
- examples:
  - `full`
  - `reduced`
  - `single`

### 6.4 `escalation_budget`
- which advanced tools are permitted this round
- examples:
  - `none`
  - `tot`
  - `mad`
  - `asp`
  - `stacked`

### 6.5 `guidance_budget`
- how thick the repair context is allowed to become
- examples:
  - `slim`
  - `repair_pack`
  - `escalated_evidence`

## 7. Five-Step Sequential Hardening

### Step 1. Name The Budget Axes
- make the existing retry layers conceptually explicit:
  - round
  - repair
  - strategy
  - escalation
  - guidance
- this is the highest-ROI clarification because it improves reasoning without forcing code redesign

### Step 2. Define A Round Schedule
- give each retry round a default posture
- candidate example:
  - `R0`: full ensemble exploration
  - `R1`: local repair first
  - `R2`: targeted regenerate or escalated repair
  - `R3+`: last escalation or stop
- this makes retry policy easier to interpret than today's mostly implicit branch web

### Step 3. Reduce Score Dominance
- route primarily from:
  - `fix_scope`
  - `reject_bucket`
  - repair feasibility
- keep score as secondary support instead of dominant fallback
- this makes retry behavior feel more structurally justified

### Step 4. Normalize Escalation Rules
- align ToT, MAD, ASP, and adaptive guidance under a common escalation ladder
- examples:
  - repeated `quality_issue` -> stronger repair evidence or ASP
  - repeated `post_select_conflict` -> rewrite bias instead of repeated local patching
  - repeated `constraint_violation` -> MAD sooner rather than later

### Step 5. Co-Govern Prompt Thickness
- tie retry budget to prompt thickness explicitly
- candidate shape:
  - `R0` -> slim context
  - `R1` -> repair pack
  - `R2` -> escalated evidence
- this connects retry policy to the separate prompt-austerity and pre-write context notes

## 8. Recommended Stop Line
- immediate ROI is highest at Step 1 through Step 3
- Step 4 is useful after retry categories are made more explicit
- Step 5 should wait until prompt-composition policy is stable enough to absorb it
- anything beyond this today would likely become overengineering

## 9. Why This Topic Has High ROI
- retry policy touches:
  - token cost
  - latency
  - PASS_WITH_FIX interpretation
  - escalation tooling
  - operator trust in round behavior
- small policy cleanup here would improve both local debugging and broader process architecture work

## 10. Open Questions To Resume Later
- whether `AdaptiveRetryManager` should become a stronger first-class retry-budget participant or remain a guidance-only side layer
- whether `post_select_conflict` should stay patch-first after the first retry or switch to rewrite bias earlier
- whether score fallback should be demoted globally or only for selected reject buckets
- whether round count and escalation count should remain coupled or be tracked separately
- how tightly this policy should align with the separate `PASS_WITH_FIX local repair contract` note
