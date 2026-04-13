# 0_0 Stage234 Cross-Stage Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: partially_realized (promoted from parked on 2026-04-07 roadmap reorder; a first bounded activation tranche landed around shared alias survival for `constraint_summary` plus mission packets, and the 2026-04-12 compact follow-ups are now also partially landed on the live workspace: Stage4 now understands a backward-compatible `strategy_feedback_map`, the bounded `style_guide anchor fallback reuse` slice is also landed, the later `post-select truth-pin / retry-lane hardening` slice is now also landed, and the same feedback-routing contract still remains pending for Stage3 and then Stage2)
Canonical Path: `docs/2026-04-02/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `c5c5180bd3493bced341e21f29abb754a163de56`
- Baseline Dirty Summary: `dirty: config/models.yaml, active/temp roadmap mirrors, queue-state, canary fixpack runtime artifacts, and 2026-04-02 survey bundles/lane drafts present in workspace`
- Resume Commit: `2b7cb64f2d1fe2cd1152806a5cc37795609f9755`
- Resume Drift Summary: `2026-04-07 bounded first activation tranche remains landed, and the 2026-04-12 compact follow-ups now split into three landed Stage4-first slices under this same lane: `feedback routing` still follows an ensemble-first, bespoke-later pattern across Stage2/3/4, but Stage4 now owns the first backward-compatible per-strategy retry feedback map while the same pattern still remains to be extended to Stage3 and Stage2, the bounded `style_guide anchor fallback reuse` seam is also landed so persisted project-local style truth can suppress repeated `카카오 / 네이버` prompting, and the later Stage4 `post-select truth-pin / retry-lane hardening` slice is now also landed so semantic-hard post-select conflict families reroute away from bounded local patch retries`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-bounded-survey.md`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage3-static-global-bounded-survey.md`
- `docs/2026-04-02/0_0-stage2-production-consumption-global-bounded-survey.md`
- `docs/2026-04-12/stage234-feedback-routing-compact-survey.md`
- `docs/2026-04-12/stage4-style-guide-anchor-fallback-compact-survey.md`
- `docs/2026-04-12/stage4-ep2-post-select-conflict-loop-compact-survey.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage234-cross-stage-vocabulary-source-of-truth-matrix-evidence.json`
- `docs/2026-04-02/0_0-stage4-consumer-finalization-global-evidence.json`
- `docs/2026-04-02/0_0-stage3-static-global-evidence.json`
- `docs/2026-04-02/0_0-stage2-production-consumption-global-evidence.json`
Side-Effect Coverage: covered

## 1. Intent

Preserve a bounded pending lane for `Stage2/3/4 cross-stage contract normalization` without promoting it ahead of the current active Stage4 consumer/finalization lanes.

This execution SSOT exists because the matrix survey proved:

- the dominant remaining debt is not missing concepts but cross-stage rename, strength inversion, owner collision, and prose flattening
- the costliest seam is `Stage3 -> Stage4`
- `Stage4` split truth (`final_state_updates`, `actual_truth`, `world_state`) is a substrate problem, not a one-off bug
- long-term simplification work now needs a real shared vocabulary and source-of-truth contract

## 2. Baseline Facts

- `Stage2` is `content-sufficient but schema-fragile`.
- `Stage3` is `compiler-like but enforcement-lossy`.
- `Stage4` is `consumer/finalization split-truth-heavy`.
- The current system is `cross-stage-vocabulary-drift heavy`.
- The highest-cost drift types are:
  - rename without mapping
  - strength inversion
  - structure-to-prose flattening
  - multi-owner truth concepts
- The most expensive boundary is `Stage3 -> Stage4`.

## 3. Scope

Included:

- shared cross-stage vocabulary definition for repeated concepts
- explicit owner and strength matrix for major Stage2/3/4 truth concepts
- contract normalization for:
  - authority strength
  - episode mission
  - repair/finalization terms
  - post-finalization truth surfaces
- bounded alias normalization where concept drift is already proven
- bounded owner-consolidation substrate work where one concept currently has multiple owners

Excluded:

- broad architecture rewrite
- immediate Stage-count reduction
- fresh canary in this lane
- active Stage4 seam patches already covered by existing Stage4 execution SSOTs
- repo-wide string rename sweep in one turn
- DB schema redesign
- narrative artifact rewrites in `projects/`

## 4. Pass 1. Inventory Summary

Primary inventory totals and findings from the matrix survey:

- 33 major concepts traced across Stage2/3/4
- only a small stable subset remain true equivalents across boundaries
- several Stage2 fields are effectively dead or low-signal by the next boundary
- Stage4 introduces additional local vocabulary for upstream truths

Highest-cost mismatch families:

1. `constraint_summary -> arc_constraint_summary -> Stage4 hard prohibition prose`
2. `tactical_doc -> arc_focus -> arc_tactical`
3. `state_changes -> state_changes_summary -> final_state_updates / actual_truth / world_state`

## 5. Pass 2. Semantic Classification

### Class A. Primary realization when this lane is reactivated

- shared authority-strength vocabulary
- shared episode-mission vocabulary
- shared repair/finalization vocabulary
- shared feedback-routing vocabulary
- explicit owner matrix for post-finalization truth surfaces

### Class B. Residual but related

- Stage3 compiler/substep compression
- Stage2 keep-or-drop field cleanup
- Stage4 consumer-side prompt/prose de-flattening

### Class C. Explicitly deferred outside this lane

- active Stage4 canary/closure work
- Stage4 global resume decision
- full Stage3 compression
- large architecture reduction from `2/3/4` to `2/4`

## 6. Side-Effect Map

- file writes / artifacts:
  - contract docs and code-facing field family normalization may change serialized repair/state payloads

- DB / schema / transaction boundaries:
  - no schema redesign in this lane
  - existing payload field families may be normalized or receive compatibility metadata

- JSONL / log / audit sinks:
  - operator-visible field names may become more explicit and more uniform

- console / UI / operator output:
  - owner and repair-scope lineage may become clearer

- rollback / recovery / retry:
  - repair-routing and post-select behavior may change once shared repair vocabulary is normalized

- cache / global state:
  - context-builder and cross-stage packet caches may need bounded key alignment

- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

This pending lane sits above the current Stage4 seam docs. It should reuse, not replace, the evidence and substrate already produced by:

- `0_0-stage4-consumer-contract-normalization-remediation`
- `0_0-stage4-post-select-continuity-contract-normalization-remediation`
- `0_0-stage4-fixpack-finalization-remediation`
- `0_0-stage4-canonical-entity-postselect-remediation`
- pending Stage3 and Stage2 normalization docs

The architectural rule for this lane:

- define the canonical cross-stage concept family first
- define owner and strength next
- only then normalize the code surface that transports or consumes the concept

## 8. Execution Tranches

### Tranche 1. Shared Vocabulary Contract

Goal:

- formalize shared concept families across Stage2/3/4

Targets:

- authority strength family
- episode mission family
- repair/finalization family
- post-finalization truth family

Outputs:

- one canonical matrix or contract doc
- one code-facing vocabulary mapping for repeated fields and aliases

### Tranche 2. Owner and Strength Normalization

Goal:

- remove or explicitly govern owner collisions and strength inversion

Targets:

- `fix_scope / authoritative_fix_scope / repair_scope`
- `final_state_updates / actual_truth / world_state`
- `constraint_summary` family strength normalization
- `shared feedback -> strategy feedback -> selected-attempt feedback` routing boundaries

Outputs:

- explicit owner-precedence contract
- explicit strength-by-stage contract

### Tranche 3. Boundary Transport Tightening

Goal:

- preserve machine-readable authority where it is currently flattened or renamed away

Targets:

- `Stage2 -> Stage3` mission and state packet aliases
- `Stage3 -> Stage4` machine-readable constraint survival
- bounded Stage4 intake/post-pass term normalization

Outputs:

- narrowed boundary normalization patches
- compatibility metadata where immediate deletion is too risky

### Tranche 4. Feedback Routing Tightening

Goal:

- keep shared Director guidance as the common hard-constraint layer while making retry feedback more candidate-aware and strategy-aware across Stage2/3/4

Targets:

- `Stage4` first: `strategy_specific_feedback` string -> bounded `strategy_feedback_map`
- `Stage3` next: reuse `candidate_advisories` plus retry state for the same map shape
- `Stage2` last: reuse Arc quality/advisory flags for a lighter per-strategy feedback map

Outputs:

- one backward-compatible feedback-routing contract
- bounded retry-routing patches starting with Stage4
- targeted tests that lock shared-feedback vs strategy-feedback separation

### Tranche 5. Style-Guide Anchor Fallback Tightening

Goal:

- stop `Stage4` from needlessly re-prompting `카카오 / 네이버` when project-local style-guide truth already exists

Targets:

- decouple persisted `style_guide` reuse from global `stage0_available`
- preserve the existing owner model where `Stage0` remains the producer of style truth and `Stage4` acts only as the consumer
- allow a project-local fallback path that prefers:
  - persisted anchor truth first
  - `stage0_output/style_guide.json` second
  - operator prompt only when no richer project-local style truth exists

Outputs:

- one bounded Stage0 -> Stage4 style-hydration contract
- no unnecessary repeated platform-style prompt on projects that already have persisted style truth
- targeted tests that lock `anchor/file truth beats operator fallback`

## 8A. Implementation Update (2026-04-07)

Landed bounded tranche:

- `modules/core/stage_cross_stage_contract.py` now provides a shared alias helper for the highest-cost vocabulary family in this lane: `constraint_summary` vs `arc_constraint_summary`, plus bounded extraction of current-episode mission lines from canonical `episode_details`.
- `modules/core/stage4_context_builder.py` now consumes that helper in `work_focus`, work-identity slot summaries, and tier0 mandatory sections, so Stage4 no longer depends only on `constraint_summary` and now exposes a machine-readable current-episode mission packet instead of flattening that handoff into prose-only tactical context.
- `tests/test_stage4_context_builder.py` now locks the new alias survival contract in place, including `arc_constraint_summary` fallback and current-episode mission packet promotion into Stage4 mandatory context.

Residual deferred inside this lane:

- broader owner-precedence normalization for `fix_scope / authoritative_fix_scope / repair_scope`
- broader split-truth owner normalization for `final_state_updates / actual_truth / world_state`
- Stage2 -> Stage3 transport tightening beyond the bounded Stage4 consumer intake slice
- cross-stage feedback-routing tightening beyond the first bounded Stage4 tranche
- fresh canary/live proof

Complexity recount:

- `_compose_work_focus_text(...)` is now `52 LOC`
- `_build_work_identity_slot_summary(...)` is now `88 LOC`
- `_build_tier0_mandatory_sections(...)` is now `160 LOC` and remains a bounded shell, not a new semantic-core hotspot
- no new `180+ LOC` function was introduced in this tranche

## 9. Acceptance Criteria

- the highest-cost shared concept families have a canonical vocabulary
- each major concept has an explicit authoritative owner
- each major concept has an explicit strength classification by stage
- known split-truth concepts no longer rely on implicit owner inference
- retry feedback can distinguish `shared feedback`, `strategy-specific feedback`, and `selected-attempt-only feedback` without collapsing them into one opaque string
- Stage4 does not re-prompt `카카오 / 네이버` when the current project already has valid `style_guide` truth in an anchor or `stage0_output/style_guide.json`
- future Stage-count simplification can cite this matrix instead of intuition
- no new `180+ LOC` function is introduced in the first activation tranche

## 10. Verification Plan

- re-run 3-pass audit against the live workspace before any code patching from this document
- `python -m py_compile modules/core/stage_cross_stage_contract.py modules/core/stage4_context_builder.py tests/test_stage4_context_builder.py`
- `pytest tests/test_stage4_context_builder.py -q`
- `ruff check modules/core/stage_cross_stage_contract.py modules/core/stage4_context_builder.py tests/test_stage4_context_builder.py`
- `python -m py_compile modules/core/stage4_orchestrator.py modules/core/project_support.py tests/test_stage4_orchestrator.py`
- `pytest tests/test_stage4_orchestrator.py -k "style_guide" -q`
- `ruff check modules/core/stage4_orchestrator.py modules/core/project_support.py tests/test_stage4_orchestrator.py`
- `pytest tests/test_stage3_orchestrator.py tests/test_stage4_interview_round.py tests/test_failure_analyzer.py -q`
- validate UTF-8 hygiene on the SSOT and mirror
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`
- keep runtime proof bounded and deferred until explicit reactivation

## 11. Guardrails

- do not activate this wave ahead of current Stage4 active seams without explicit reprioritization
- do not turn this into a repo-wide blind rename wave
- do not delete Stage3 as part of this lane
- do not introduce DB schema migration in the first activation tranche
- keep compatibility/alias bridges explicit while old and new terms coexist
- keep `director_feedback` as the shared hard-constraint layer; do not replace it with per-candidate prompts
- keep `strategy_specific_feedback` backward-compatible until all consuming stages safely understand the map form

## 12. Temp Queue Notes

- temp status: `in_progress`
- cleanup condition:
  - remove the mirror only on explicit closure, replacement, or strategic cancellation
- roadmap dependency:
  - remains below the current active Stage4 consumer/finalization lane
  - remains above or alongside longer-term Stage3/Stage2 simplification discussion as the contract substrate

## 12A. 2026-04-12 Compact Re-Audit

3-pass result:

- Pass 1: scope still fits this lane because the problem is not a new seam family but a cross-stage routing contract between shared feedback, strategy feedback, and selected-attempt remediation.
- Pass 2: live code evidence shows all three stages still use an `ensemble-first, bespoke-later` pattern, with Stage4 retaining the highest first-patch ROI.
- Pass 3: the bounded realization path is clear and does not require a new queue topic; a Stage4-first tranche can land under this existing execution SSOT.

Execution consequence:

1. treat the backward-compatible `Stage4 strategy_feedback_map` tranche as landed
2. extend the same routing contract to `Stage3`
3. extend a lighter version to `Stage2`

## 12B. 2026-04-12 Live Workspace Update

Landed bounded follow-up:

- `chief_writer.py` now understands a backward-compatible `strategy_feedback_map` and prefers per-strategy retry guidance from that map when present.
- `stage4_reject_runtime.py` now persists the selected-strategy retry-focus bundle into reject snapshot state so the Stage4 tranche has real runtime inputs instead of staying doc-only.

## 12C. 2026-04-12 Stage4 Style-Guide Fallback Re-Audit

3-pass result:

- Pass 1: the repeated `카카오 / 네이버` prompt is not a manuscript-persistence problem; it is a bounded `Stage0 style truth -> Stage4 session style hydration` seam.
- Pass 2: live project evidence proves persisted `style_guide` truth already exists in both anchor storage and `stage0_output/style_guide.json`, so the prompt is unnecessary fallback behavior when it still appears.
- Pass 3: ownership fits this lane because the seam is a cross-stage producer/consumer contract issue, not a new standalone Stage4 family.

Execution consequence:

1. keep the Stage4 feedback-routing tranche as landed
2. promote `style_guide anchor fallback reuse` as the next bounded Stage4-first slice inside this same lane
3. keep Stage3 and then Stage2 feedback-routing extension behind that bounded operator-facing fix

## 12D. 2026-04-12 Stage4 Style-Guide Fallback Live Workspace Update

Landed bounded follow-up:

- `project_support.py` now provides `load_style_guide_file(...)` so Stage4 can read project-local `stage0_output/style_guide.json` without reopening the Stage0 family.
- `stage4_orchestrator.py` now prefers persisted `style_guide` truth from anchor first, then project-local file truth, and only falls back to the operator prompt when neither source exists.
- the same Stage4 fallback path now persists the one-time `카카오 / 네이버` choice back into the `style_guide` anchor so the operator is not asked again on the next session when no richer project-local style truth exists yet.
- `tests/test_stage4_orchestrator.py` now locks the new contract: saved anchor beats prompt even when the old `stage0_available` flag is false, `style_guide.json` beats prompt, and the prompt fallback persists a reusable anchor payload.

Current next action inside this lane:

1. keep the Stage4 feedback-routing tranche and the Stage4 style-guide fallback tranche as landed
2. extend the same routing contract to `Stage3`
3. extend a lighter version to `Stage2`
4. let fresh proof happen before any broader shared-vocabulary or owner-strength reopening

## 12E. 2026-04-12 Stage4 EP2 Post-Select Conflict Loop Re-Audit

3-pass result:

- Pass 1: the live `ep2` failure does not justify a new queue owner; it is a bounded Stage4 retry-lane and truth-routing seam that still fits this cross-stage contract lane.
- Pass 2: the operator log shows repeated `PASS_WITH_FIX -> post-select conflict -> REJECT` churn with the same shared truth drift (`대한그룹 -> 유성그룹`, protagonist personal-asset-state drift) across multiple candidates, so the first-priority failure is not one bad candidate but weak authoritative truth transport plus an over-permissive bounded retry gate.
- Pass 3: the safest next slice is a fail-only Stage4 tranche that adds typed truth pins, denies bounded local retry for semantic-hard post-select conflict families, and surfaces the same must-preserve truth to Chief Writer retry prompts.

Execution consequence:

1. keep the earlier Stage4-first `strategy_feedback_map` and `style_guide anchor fallback reuse` slices as landed
2. promote a new bounded Stage4 follow-up inside this same lane: `post-select truth-pin / retry-lane hardening`
3. keep Stage3 and Stage2 feedback-routing extension behind that Stage4 fail-only follow-up

## 12F. 2026-04-12 Stage4 EP2 Post-Select Conflict Loop Live Workspace Update

Landed bounded follow-up:

- `stage4_postselect_runtime.py` now enriches post-select conflict contracts with typed truth pins, a stable conflict fingerprint, and explicit rewrite-required reasons instead of treating fix-pack readiness alone as bounded-local-fix authority.
- the same post-select downgrade path now carries those truth pins and rewrite-required reasons into `previous_attempt`, including a stronger `fix_scope_reasoning` surface for downstream retry consumers and audits.
- `stage4_retry_runtime.py` now denies `TF-F2` bounded post-select patch retries when the prior attempt is already plateau-marked, when a `qr7_contract` already exists, when continuity and history collide together, or when the conflict contract carries semantic-hard truth pins such as family-group-name drift or protagonist asset-state drift.
- `chief_writer.py` now surfaces the same typed truth pins as a must-preserve retry block so the rewrite prompt says exactly which canonical facts must not drift again.
- focused regression coverage now locks the new contract in `tests/test_stage4_interview_round.py` and `tests/test_chief_writer_candidate_lane_f.py`.

Current next action inside this lane:

1. keep the Stage4 feedback-routing tranche, the Stage4 style-guide fallback tranche, and the Stage4 post-select truth-pin / retry-lane hardening tranche as landed
2. verify the new bounded post-select deny path on the next rerun before reopening broader cross-stage owner-strength work
3. extend the same feedback-routing substrate to `Stage3` and then `Stage2`

## 12G. 2026-04-12 EP3 Live-Run Follow-up Re-Audit

Source docs:

- `docs/2026-04-12/stage234-ep3-continuity-replay-season-truth-live-run-followup-parallel-survey.md`
- `docs/2026-04-12/stage234-ep3-continuity-replay-season-truth-live-run-followup-3pass-audit.md`

3-pass result:

- Pass 1: the new live blocker no longer looks like the old Stage4 ep2 truth-pin family; the rerun shows that tranche behaving as intended.
- Pass 2: the current failure family is upstream: `blueprint_0002` already over-consumes ep3 beats, `blueprint_0003` repeats those beat families and also drifts on canonical institution truth (`대한그룹` -> `한강그룹`).
- Pass 3: the correct next owner is Stage3 parent plus Stage3 opening sibling, while Stage4 stays the downstream consumer/verifier that caught the replay and season-truth conflicts.

Execution consequence:

1. keep the Stage4-first `strategy_feedback_map`, `style_guide anchor fallback reuse`, and `post-select truth-pin / retry-lane hardening` slices as landed
2. do not reopen a new Stage4-first retry lane from this evidence
3. promote the new live blocker into `0_0-stage3-contract-tightening-remediation`
4. keep `0_0-stage3-opening-transition-contract-normalization-remediation` as the bounded sibling owner for immediate-next-day / season-truth handoff hardening
5. treat the later Stage3 fail-only / support slices as now landed inside their Stage3 owner lanes, not as a new cross-stage owner change
6. keep any later shared truth-pin/routing extension inside this cross-stage lane only after the next proof wave confirms whether further shared vocabulary work is still needed

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule:
  - re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

---

## 3-Pass Audit Record

Pass 1. Structure and scope
- document type matches a promoted pending execution SSOT
- scope is bounded to cross-stage contract normalization, not a broad rewrite
- active Stage4 seams remain out of scope and higher priority

Pass 2. Evidence and consistency
- claims are bounded to the new matrix survey and prior Stage2/Stage3/Stage4 surveys
- source docs and evidence artifacts are coherent
- queue semantics align with the promoted pending Stage2/Stage3 lanes

Pass 3. Execution and readability
- tranches are ordered from contract definition to boundary normalization
- operating consequence and guardrails are explicit
- overreach trimmed: no immediate architecture compression or stage deletion

Confidence: 96%
