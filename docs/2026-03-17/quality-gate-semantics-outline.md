# Quality Gate Semantics Outline

Date: 2026-03-17
Status: draft
Canonical Path: `docs/2026-03-17/quality-gate-semantics-outline.md`
Document Type: planning note
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Scope:
- preserve brainstorming context around Stage 4 quality-gate semantics
- focus on meaning separation between verdict, score, advisory, repair scope, and retry routing
- keep the note at planning level without opening an execution queue
Non-Goals:
- no code changes in this note
- no claim that the note is 3-pass finalized
- no execution SSOT, roadmap, or implementation order in this note

## 0. Live Snapshot
- current Stage 4 logic is safer than a naive single-verdict path because it layers quality floor, post-select conflict checks, patch re-audit, and retry provenance
- the main weakness is not absence of checks but semantic overloading: one apparent `verdict` carries too many meanings at different times
- `fix_scope` currently acts as both a Director judgment artifact and a practical routing lever for inplace/patch/rewrite behavior
- advisory signals are nominally "reference only" in some places but still shape Director context and retry behavior strongly enough to matter operationally

### Current Code Touchpoints
- main verdict post-processing: `modules/core/stage4_interview_round.py` -> `_process_verdict()`
- post-select downgrade path: `modules/core/stage4_interview_round.py` -> `_run_post_select_checks()`
- PASS_WITH_FIX patch loop: `modules/core/stage4_interview_round.py` -> `_execute_pass_with_fix_loop()`
- REJECT routing and retry-state assembly: `modules/core/stage4_interview_round.py` -> `_handle_reject()`
- next-round strategy routing: `modules/core/stage4_interview_round.py` -> `_generate_candidates()`
- advisory classification and suppression: `modules/core/stage4_interview_round.py` -> `_classify_advisory_tier()` / `_suppress_conflicting_advisories()`

## 0A. Working Assumptions
- process quality improves when result, reason, routing scope, and reference warnings are separated cleanly
- the current system already has enough information; the main issue is that the information is spread across overlapping semantic roles
- a small semantic cleanup could improve operator readability, retry clarity, and later observability without immediately changing model behavior
- this topic should stay below heavy automation for now; meaning separation comes first

## 1. Main Finding
- current Stage 4 quality gating behaves more like a chain of gate transitions than a single verdict
- the code currently passes through at least these transitions:
  - Director primary verdict
  - quality-floor downgrade
  - post-select conflict downgrade
  - PASS_WITH_FIX patch loop and re-audit
  - final retry or accept path
- because these transitions reuse the same labels and overlapping fields, logs and process reasoning become harder to interpret than necessary

## 2. Current Semantic Overload

### 2.1 Verdict Overload
- one apparent `verdict` can refer to:
  - Director first judgment
  - pre-floor result
  - post-floor result
  - post-conflict result
  - post-patch result

### 2.2 Reason Overload
- explanatory material is distributed across:
  - `verdict_reason`
  - `director_feedback`
  - `open_review`
  - `rejection_reason`
- these fields do not currently map cleanly to one semantic layer each

### 2.3 Repair Overload
- `PASS_WITH_FIX` already implies some repair meaning
- `fix_scope` separately describes repair extent
- later retry generation also uses `fix_scope` plus score fallback to choose inplace/patch/rewrite behavior

### 2.4 Advisory Overload
- advisory signals are classified, merged, suppressed, and injected into Director context
- some paths explicitly describe advisory as non-decisive reference
- operationally, advisory still influences retry and selection surfaces strongly enough to blur the line between "reference" and "decision support"

### 2.5 Score Overload
- score acts both as a quality index and as a gate floor trigger
- a Director `PASS` can still become `REJECT` because score is below threshold

## 3. V1 Target Model

### 3.1 `director_verdict`
- the first Director judgment before downstream hard gates
- useful for understanding model judgment quality separately from system gating

### 3.2 `final_verdict`
- the true terminal result after all hard gates and patch re-audit
- this should be the top-level user-facing outcome

### 3.3 `gate_basis`
- short canonical reason for the terminal gate transition
- examples:
  - `director_primary_pass`
  - `quality_floor_fail`
  - `post_select_conflict`
  - `patch_reaudit_pass`
  - `patch_reaudit_fail`
  - `continuity_firewall`
  - `empty_feedback_abort`

### 3.4 `repair_scope`
- independent description of how broad the repair must be
- examples:
  - `none`
  - `inplace`
  - `partial`
  - `full`

### 3.5 `advisory_state`
- explicit status for how advisory signals are being used
- examples:
  - `reference_only`
  - `decision_support`
  - `escalated`

### 3.6 `score`
- primarily a quality index
- if a floor exists, floor failure should be modeled as a separate gate event rather than an implicit reinterpretation of score

## 4. Why This Helps
- distinguishes "Director liked it" from "system hard gate rejected it"
- separates "how broad is the fix" from "what is the result"
- keeps advisory in its own layer instead of letting it silently drift into gate semantics
- makes later dashboards and operator reviews much easier to interpret

## 5. Comparison: Current vs V1

### Current
- `verdict` mixes multiple stages of judgment
- `fix_scope` is both explanation and routing input
- `score` is both index and veto floor
- advisory is nominally reference but can behave like decision-support material
- logs preserve many details but require reconstruction to interpret process state

### V1
- `director_verdict` and `final_verdict` separate first judgment from final outcome
- `gate_basis` explains terminal transition
- `repair_scope` describes repair width only
- `advisory_state` clarifies advisory authority
- `score` remains quality index, while gate failures become explicit transition reasons

## 6. Five-Step Sequential Hardening

### Step 1. Meaning Separation
- introduce or at least conceptualize:
  - `director_verdict`
  - `final_verdict`
  - `repair_scope`
  - `gate_basis`
- this is the highest-ROI layer because it clarifies the rest of the system without changing behavior much

### Step 2. Score Role Fixing
- define score as quality index first
- model floor failure explicitly as `quality_floor_fail`
- stop letting score silently act as both narrative explanation and direct terminal veto

### Step 3. Advisory Isolation
- make advisory usage explicit:
  - reference
  - decision-support
  - escalated
- this prevents advisory from being "softly decisive" without a visible state change

### Step 4. Routing Separation
- distinguish verdict semantics from retry routing
- future routing surfaces can then operate through:
  - `repair_scope`
  - `retry_strategy`
  - `retry_budget`
- this keeps retry mechanics from overloading verdict meaning

### Step 5. Observability Alignment
- align logging and dashboards to the semantic model
- minimum useful fields:
  - `director_verdict`
  - `final_verdict`
  - `gate_basis`
  - `repair_scope`
  - `advisory_state`
  - `score`

## 7. Recommended Stop Line
- current ROI is highest at Step 1 and Step 2
- Step 3 is still reasonable soon after
- Step 4 and Step 5 should wait until the semantic split is stable enough to justify logging and routing refactors
- going further now would risk overengineering before the core language is stabilized

## 8. Why This Topic Has High ROI
- verdict semantics influence:
  - retry behavior
  - PASS_WITH_FIX interpretation
  - operator trust
  - dashboard readability
  - future policy work
- a semantic cleanup here improves both local debugging and later process-design work

## 9. Open Questions To Resume Later
- whether `PASS_WITH_FIX` should survive as a terminal user-facing verdict or become mostly an intermediate repair marker
- whether some current `open_review` content really belongs under `gate_basis` or `verdict_reason`
- how much of `advisory_state` should be explicit in saved artifacts versus only in runtime traces
- whether score-floor behavior should stay global or become bucket-specific
- how tightly this semantic model should be aligned with the separate `PASS_WITH_FIX local repair contract` note
