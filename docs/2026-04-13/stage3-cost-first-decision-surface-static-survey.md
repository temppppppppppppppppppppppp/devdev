# Stage3 Cost-First Decision Surface Static Survey

- Date: 2026-04-13
- Scope: current `main@347acac3` static re-audit of Stage3 decision authority, fallback policy, local-patch eligibility, and projection semantics after the same-day binding-family static-kill tranche
- Mode: survey-only, static, cost-first; no fresh live rerun in this turn
- Canonical Path: `docs/2026-04-13/stage3-cost-first-decision-surface-static-survey.md`
- Baseline Commit: `347acac374f7246cca433d4be9c7466e802c9883`
- Baseline Dirty Summary: `dirty: active Stage3 docs/code/tests plus frozen live-run artifacts under 0_temp.txt and projects/000_260412_a`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none during this static survey`
- Side-Effect Coverage: code-path only; validator/runtime/orchestrator/generator decision and sink surfaces inspected, no new live-run evidence generated
- Confidence: `96%`

## Purpose

This survey answers one bounded question:

- after the landed binding-family static kill, what is the next highest-ROI static Stage3 improvement if the operator priority is `돈 적게 쓰기 + 코드 품질 높이기`

This document is survey-only.

This document does not open a new queue lane.

This document does not claim fresh runtime proof.

## Evidence Anchors

Frozen runtime anchors:

- `0_temp.txt`
- `projects/000_260412_a/logs/session_20260413_140153.log`

Current code owners:

- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage3_orchestrator.py`

Relevant current tests:

- `tests/test_unified_blueprint_validator_lane_c.py`
- `tests/test_blueprint_patch_mode.py`
- `tests/test_stage3_orchestrator_handle_success_lane_c.py`

Polaris / long-horizon anchor:

- `docs/2026-04-13/stage3-decision-kernel-queue-semantics-operating-note.md`

## Executive Summary

- The newly landed binding-family static-kill tranche is the correct first move for a cost-first strategy. It closes the concrete `ep7/ep8` churn family without paying for another rerun first.
- The next highest-ROI static improvement is not another broad survey and not a fresh live proof wave.
- The next high-ROI target is `repair eligibility authority`:
  - Stage3 still decides local patch eligibility mainly from `prev_fix_scope`, score, and retry heuristics
  - it does not yet drive that choice from the authoritative `repair_contract` / `scope_authority` contract it already preserves
- A second static target is `projection semantics`:
  - orchestrator still compresses some success states for dashboard output
  - this makes policy and observability less crisp than the runtime decision now deserves

## Findings

### 1. The binding-family static kill is now the correct cheap first barrier

Current code now does the right thing for the concrete expensive family that the frozen rerun surfaced:

- validator treats all MAJOR/CRITICAL binding-prevalidation categories as regenerate-only: `modules/domain/agents/unified_blueprint_validator.py:79`
- validator still emits structured binding metadata instead of burying the issue in prose only:
  - `binding_prevalidation_issue_count`: `modules/domain/agents/unified_blueprint_validator.py:724`
  - `binding_regenerate_only_categories`: `modules/domain/agents/unified_blueprint_validator.py:728`
  - `repair_scope` / `authoritative_fix_scope` / `scope_authority`: `modules/domain/agents/unified_blueprint_validator.py:734`, `modules/domain/agents/unified_blueprint_validator.py:742`, `modules/domain/agents/unified_blueprint_validator.py:752`
- runtime blocks inplace reopen when a prior reject still carries binding issues:
  - `modules/domain/agents/three_phase_blueprint_runtime.py:197`
  - `modules/domain/agents/three_phase_blueprint_runtime.py:920`
- runtime also blocks terminal warning fallback when unresolved binding issues survive to the end:
  - `modules/domain/agents/three_phase_blueprint_runtime.py:2255`
  - `modules/domain/agents/three_phase_blueprint_runtime.py:2275`

Conclusion:

- this tranche correctly kills the currently proven expensive family before another paid run
- this should remain the template for future cost-first Stage3 work: `static kill first, proof later`

### 2. Phase2 local-patch eligibility is still heuristic-first, not contract-first

The next avoidable cost surface is still open.

Runtime Phase2 decides whether to attempt local patch mainly from:

- `prev_fix_scope`: `modules/domain/agents/three_phase_blueprint_runtime.py:913`
- score threshold: `modules/domain/agents/three_phase_blueprint_runtime.py:920`
- retry plateau heuristics: `modules/domain/agents/three_phase_blueprint_runtime.py:926`

This is better than before, but it still means the routing decision is driven by:

- `fix_scope`
- retry streaks
- score

rather than by the richer authoritative contract that Stage3 already has:

- normalized `repair_contract`: `modules/domain/agents/three_phase_blueprint_runtime.py:319`
- normalized `scope_authority`: `modules/domain/agents/three_phase_blueprint_runtime.py:369`
- persisted validation payload fields: `modules/domain/agents/three_phase_blueprint_runtime.py:1462`, `modules/domain/agents/three_phase_blueprint_runtime.py:1468`

Conclusion:

- cost is still at risk whenever a future family is not explicitly covered by a hard blocker
- the next cheap static improvement is to make local-patch eligibility depend on authoritative repair contract fields, not only `fix_scope` plus retry heuristics

### 3. The path called `inplace` is still whole-blueprint regeneration

This remains the biggest structural cost truth in Stage3.

The current path:

- serializes the whole original blueprint JSON: `modules/domain/agents/three_phase_blueprint_generator.py:173`
- sends the full blueprint plus feedback back to the model: `modules/domain/agents/three_phase_blueprint_generator.py:197`, `modules/domain/agents/three_phase_blueprint_generator.py:209`
- asks the model not to redesign, but still via whole-output regeneration: `modules/domain/agents/three_phase_blueprint_generator.py:216`
- then preserves missing fields with a shallow merge: `modules/domain/agents/three_phase_blueprint_generator.py:231`

Conclusion:

- any family that leaks into this lane still spends near-regeneration cost
- therefore the cheapest quality strategy is not “make inplace smarter” first
- the cheapest strategy is “make fewer families eligible for inplace at all”

### 4. Projection semantics are still compressed downstream

Stage3 runtime and validator now carry more nuanced semantics than some downstream projections expose.

In orchestrator success handling:

- `quality_gate_failed`, `quality_risk`, and `revision_required` are preserved: `modules/core/stage3_orchestrator.py:2036`
- but the QualityDashboard projection still compresses the decision:
  - `modules/core/stage3_orchestrator.py:2587`
  - `modules/core/stage3_orchestrator.py:2590`

Current behavior:

- `PASS` stays `PASS`
- `PASS_WITH_WARNING` stays `PASS_WITH_WARNING`
- other success states are projected as `PASS`

This is not accidental drift. It is locked by current regression coverage:

- `tests/test_stage3_orchestrator_handle_success_lane_c.py:70`
- `tests/test_stage3_orchestrator_handle_success_lane_c.py:98`

Conclusion:

- this projection is workable, but it weakens the “one authoritative decision surface” goal
- for a cost-first operator, this matters because it makes proof bookkeeping and future policy tuning less precise than they could be

### 5. The next cheap tranche is narrower than Polaris, but aligned with it

The long-horizon Polaris target still points toward:

- `Stage3DecisionKernel`
- `Stage3DecisionReport`
- structured patch IR

Reference:

- `docs/2026-04-13/stage3-decision-kernel-queue-semantics-operating-note.md`

But the highest-ROI next step is still much smaller than that:

1. normalize local-patch eligibility around authoritative repair contract fields
2. normalize projection semantics so success states do not silently compress in one sink but not another

Conclusion:

- do not jump to full DecisionKernel refactor yet
- land the cheaper pre-kernel tranche first

## Recommended Next Tranche

Owner:

- keep ownership in the existing Stage3 parent lane
  - `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`

Do not open a new queue lane.

### Tranche A. Contract-driven repair eligibility

Goal:

- make Stage3 local patch eligibility deterministic and cheap

Bounded implementation direction:

- derive local patch eligibility from:
  - `repair_scope`
  - `authoritative_fix_scope`
  - `scope_authority`
  - a strict allowlist of truly local issue families
- stop treating raw `fix_scope="inplace"` as sufficient by itself
- preserve current hard binding blockers, but move future eligibility toward contract-first routing

Desired effect:

- fewer whole-blueprint pseudo-patches
- fewer paid retries on families that are not truly local

### Tranche B. Success-state projection normalization

Goal:

- make downstream observability reflect the runtime decision surface more faithfully

Bounded implementation direction:

- centralize success-state projection for:
  - persistence payload
  - quality dashboard
  - operator summary
- stop ad hoc compression of `PASS_WITH_FIX` / `PASS_WITH_WARNING` semantics in one sink only

Desired effect:

- cheaper reasoning about proofs
- cleaner future policy changes
- less need for repeated reruns just to understand what the system thinks happened

## Explicitly Not Recommended Next

- broad fresh live rerun before the next static tranche
- full `DecisionKernel` migration in the very next step
- true patch IR buildout before repair eligibility is normalized
- another broad Stage3 prompt rewrite wave

## Final Judgment

`추가 survey` is justified, and the result is clear:

- the next best move is not more rerun
- the next best move is not another broad survey
- the next best move is one bounded static tranche:
  - `contract-driven repair eligibility`
  - plus `success-state projection normalization`

That is the highest-ROI path if the operator priority is:

- spend less
- raise code quality
- rerun only after the next static quality gate is tighter

## 3-Pass Audit Record

### Pass 1. Structure / Scope

- kept the document survey-only
- bounded the scope to decision authority, fallback policy, repair eligibility, and projection semantics
- did not inflate this into a new queue lane or live-merge survey

### Pass 2. Evidence / Consistency

- tied every key claim to current code anchors or frozen same-day runtime evidence
- separated already-landed binding-family static kill from still-open cost surfaces
- kept Polaris as target-state support only, not as a claim that the current runtime is already kernelized

### Pass 3. Execution / Readability

- named one concrete next tranche instead of a vague “more refactor”
- kept the recommendation inside the existing Stage3 parent lane
- kept live rerun explicitly deferred until after the next static tranche
