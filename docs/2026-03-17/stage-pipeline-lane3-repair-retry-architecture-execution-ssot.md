# Stage Pipeline Lane 3 PASS_WITH_FIX and Retry Architecture Execution SSOT

Date: 2026-03-17
Status: execution-ready
Canonical Path: `docs/2026-03-17/stage-pipeline-lane3-repair-retry-architecture-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage-pipeline-lane3-repair-retry-architecture-execution-ssot.md`
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-17/stage-pipeline-process-integrity-global-survey.md`
- `docs/2026-03-17/pass-with-fix-local-repair-contract-outline.md`
- `docs/2026-03-17/retry-budget-policy-outline.md`
Evidence Artifacts:
- `docs/2026-03-17/stage-pipeline-process-integrity-evidence-manifest.md`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `96%`

## 1. Intent
- realize the bounded survey finding that Stage 4 repair and retry machinery is functionally rich but semantically fragmented
- narrow `PASS_WITH_FIX` into a true local-repair contract before further policy automation
- make retry budget behavior easier to reason about across rounds, repair width, strategy count, escalation tools, and guidance thickness

## 2. Baseline Facts
- current Stage 4 already has:
  - bounded PASS_WITH_FIX patch loop
  - patch/regenerate/rewrite routing
  - reduced/full strategy budgets
  - ToT, MAD, ASP, and adaptive guidance overlays
- main weakness is not lack of mechanisms but split policy meaning
- `PASS_WITH_FIX` remains broader than a pure local-repair contract
- retry budget meaning is currently distributed across `round_num`, `fix_scope`, `reject_bucket`, score fallback, and side-channel guidance

## 3. Scope
Included:
- `modules/core/stage4_interview_round.py`
- `modules/core/adaptive_retry.py`
- `modules/domain/agents/chief_writer.py`
- local repair eligibility, fix-pack structure, round schedule, and retry budget semantics
- targeted tests for PASS_WITH_FIX, strategy budgets, reject routing, and escalation overlays

Excluded:
- upstream CW context ranking except where retry prompt thickness later depends on it
- Director semantic split except where verdict meaning must align
- persistence or bridge/dashboard expansion unless later observability alignment is explicitly needed

## 4. Pass 1. Inventory Summary
- existing budget layers:
  - round budget
  - generation and repair budget
  - escalation budget
  - guidance budget
- existing safety strengths:
  - bounded local patch loop
  - Director re-audit after patch
  - targeted bucket-specific escalation tools
- current ambiguity:
  - which cases should truly enter local repair versus go straight to rewrite or reject

## 5. Pass 2. Semantic Classification
- Class A: local repair contract
  - truly bounded inplace repair with clear targets and explicit non-regression boundaries
- Class B: targeted rewrite and regenerate paths
  - broader repair that still preserves prior attempt learning
- Class C: escalation overlays
  - ToT, MAD, ASP, adaptive retry guidance, and later-round evidence thickening

## 6. Side-Effect Map
- file writes / artifacts:
  - retry history, patch provenance, attempt summaries, and any saved repair metadata
- DB / schema / transaction boundaries:
  - not-applicable for primary lane intent; no schema change target
- JSONL / log / audit sinks:
  - retry classification, strategy selection, patch outcomes, and round-level telemetry
- console / UI / operator output:
  - operator summaries and potential dashboard lane metrics may later consume clearer retry semantics
- rollback / recovery / retry:
  - this lane directly governs retry routing, escalation, and local repair semantics
- cache / global state:
  - prior-attempt state, recent strategy budget memory, adaptive retry state
- bootstrap fallback / config-env mutation:
  - none expected

## 7. Realization Architecture
- narrow `PASS_WITH_FIX` so it means only local, bounded, inplace-repairable issues
- introduce a compact structured `Fix Pack` with:
  - `fix_scope`
  - `must_fix`
  - `do_not_regress`
  - `patch_targets`
  - `success_condition`
  - `evidence_summary`
- separate retry policy into explicit budget axes:
  - round
  - repair
  - strategy
  - escalation
  - guidance
- demote score fallback behind clearer structural signals such as `reject_bucket` and repair feasibility

## 8. Execution Tranches
1. PASS_WITH_FIX semantics narrowing
   - define local-repair eligibility and push broad cases directly to REJECT or rewrite lanes
2. Fix Pack execution contract
   - replace loose repair text with a smaller structured repair payload
3. retry budget alignment
   - make round schedule and budget axes explicit
   - reduce score dominance and normalize escalation ladders

## 9. Acceptance Criteria
- `PASS_WITH_FIX` is reserved for genuinely local, inplace-repairable cases
- broader repair cases route directly to REJECT or rewrite-oriented handling
- a structured `Fix Pack` exists between Director judgment, patch logic, and re-audit
- retry behavior can be explained through named budget axes rather than only implicit branch logic
- round policy reads coherently as a schedule rather than a scattered collection of fallbacks

## 10. Verification Plan
- `python -m pytest tests/test_stage4_interview_round.py -k "pass_with_fix or reduced_strategy_budget or full_strategy_budget or post_select_conflict"`
- `python -m pytest tests/test_stage4_interview_round.py -k "adaptive or retry"`
- `python -m pytest tests/test_stage2_preflight.py -k "stage3_reverse_feedback"`
- `python -m pytest tests/test_stage3_orchestrator.py -k "rejection_history"`
- `python scripts/ops_validator.py`
- bounded review of patch provenance and retry traces to confirm route meaning matches new lane contracts

## 11. Guardrails
- do not widen PASS_WITH_FIX while attempting to improve retry success rate
- avoid introducing heavy automation or scoring policy before semantics stabilize
- keep adaptive retry as a bounded guidance participant unless a later re-audit justifies stronger authority
- keep lane 3 dependent on lane 2 semantics where verdict and repair fields overlap

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition:
  - remove `docs/temp/stage-pipeline-lane3-repair-retry-architecture-execution-ssot.md` only after implementation closes and the roadmap marks this item completed
- roadmap dependency:
  - `docs/2026-03-17/stage-pipeline-process-integrity-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document
