# 0_0 Stage2-Stage3 Stage4-Readiness Remediation Execution SSOT

Date: 2026-04-01
Status: partial — Stage3 closure candidate confirmed via ctxnorm_r1 canary runtime; Stage4 blocked by ep2 advisory escalation loop (separate issue, not Tranche D regression); Stage4 still paused
Canonical Path: `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
- Baseline Dirty Summary: `dirty: 0_0 live runtime logs/db/artifacts plus 0_temp scratch dirty; legacy temp queue still present; 2026-03-31 0_0 survey docs untracked`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `revalidated against live code plus 2026-04-01 context-hierarchy survey; context-normalization tranche promoted ahead of any new canary`
Source Survey Docs:
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-bounded-survey.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane1-stage2-authority-draft.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane2-stage3-transform-validator-draft.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane3-artifact-truth-vertical-slice-draft.md`
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-lane4-stage4-intake-readiness-draft.md`
- `docs/2026-04-01/0_0-stage2-stage3-context-hierarchy-bounded-survey.md`
Evidence Artifacts:
- `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-evidence.json`
- `docs/2026-04-01/0_0-stage2-stage3-context-hierarchy-bounded-evidence.json`
- `projects/0_0/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/0_0/logs/artifacts/stage3/ep_0005/attempt_06/final_blueprint__action_focused.json`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-runtime-audit.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-runtime-audit-evidence.json`
- `projects/canary_0_0_stage3_arc2_readiness_r3/logs/stage3_canary_summary.json`
Side-Effect Coverage: covered
Supersedes / Builds On:
- `docs/2026-03-25/stage3-blueprint-clarity-density-wave1-execution-ssot.md` (closed prior wave; residual gap remains in live `0_0`)

## 1. Intent

Realize the minimum upstream fixes required to make `Stage 2 -> Stage 3 -> Stage 4` structurally safer before Stage 4 is resumed for `0_0`.

This wave is not a broad Stage 2 redesign and not another Stage 4 remediation wave.

This wave exists because the fresh `0_0` survey proved:

- Stage 2 is not the primary blocker
- Stage 3 is the primary blocker
- Stage 4 is currently a fail-open consumer of contaminated Stage 3 artifacts

## 2. Baseline Facts

- `Arc 1 (ep 1-4)` is broadly Stage4-ready.
- `Arc 2 (ep 5-9)` is not Stage4-ready in current artifact truth.
- The first major break is `Stage 2 -> Stage 3` generation fidelity.
- `arc_constraint_summary` is currently rendered in the weakest authority band in `blueprint_ensemble.py`.
- existing binding prevalidation covers:
  - `scene_completeness`
  - `arc_timeline`
  - `capital_unit`
- blind or weak coverage remains for:
  - opening anchor completeness
  - mission clarity
  - timeline specificity
  - protagonist-state readiness
- `scene_specificity` and `scenario_density` checks are already landed from the prior clarity-density wave and should be treated as substrate, not reopened.

## 3. Scope

Included:

- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `config/prompts/ensemble.yaml`
- `modules/domain/agents/unified_blueprint_validator.py`
- bounded supporting test surfaces for Stage 3 authority / prevalidation behavior
- execution-doc and roadmap refresh required to queue this wave

Excluded:

- Stage 2 schema normalization beyond noting the seam
- large Stage 3 retry-architecture redesign
- Stage 3 self-audit or Director rubric redesign
- Stage 3 -> Stage 4 `must_not_erase` population wave
- Stage 4 resume or fresh live run in this turn
- DB schema changes

## 4. Pass 1. Inventory Summary

- generation-authority owner:
  - `BlueprintEnsembleGenerator._format_constraints()`
- Stage 3 validator owner:
  - `UnifiedBlueprintValidator._python_pre_validate()`
  - `UnifiedBlueprintValidator._apply_binding_prevalidation_contract()`
- supporting runtime owner:
  - `three_phase_blueprint_runtime.py` retry path remains in scope only as residual follow-up, not tranche A/B

Main hotspots for this wave:

1. `arc_constraint_summary` authority demotion
2. Stage4-readiness prevalidation blind spots
3. Stage 2 current-block DNA being flattened behind raw JSON and oversized previous-context payload
4. Stage 3 prompt hierarchy letting `arc_focus` and bulky `prev_info` compete too directly with hard constraints
5. ensuring new prevalidation categories flow through existing PASS -> PASS_WITH_FIX binding behavior

## 5. Pass 2. Semantic Classification

- Class A. Primary realization now
  - promote Stage 2 prohibition material from weak advisory treatment
  - widen Stage 3 binding prevalidation for Stage4-readiness structural fields

- Class B. Residual but deferred inside this lane
  - retry authority preservation under hard-episode churn
  - Stage 3 -> Stage 4 negative-obligation contract population

- Class C. Explicitly deferred outside this lane
  - Stage 2 schema normalization
  - large validator/Director constitutional redesign
  - Stage 4 pause/resume operational policy

## 6. Side-Effect Map

- file writes / artifacts:
  - Stage 3 candidate generation prompt authority changes may alter future blueprint artifacts
  - no direct artifact rewrites this turn

- DB / schema / transaction boundaries:
  - not applicable

- JSONL / log / audit sinks:
  - no new sink schema planned
  - future validation_result issue categories may include new structural categories

- console / UI / operator output:
  - prevalidation warnings and PASS_WITH_FIX feedback may surface new categories

- rollback / recovery / retry:
- existing retry loop remains intact
- stricter binding issues may increase PASS_WITH_FIX incidence on weak blueprints
- Stage 2/3 prompt order changes may alter future arc/blueprint artifact structure without changing DB schema

- cache / global state:
  - no new global state

- bootstrap fallback / config-env mutation:
  - none planned

## 7. Realization Architecture

This wave is intentionally split into a small bounded substrate and a residual follow-up path.

### Tranche A. Authority Promotion

Goal:

- stop treating Stage 2 prohibition material as soft reference-only text

Realization:

- in `blueprint_ensemble.py`, move `arc_constraint_summary` out of the `ADVISORY` band
- place it in `HARD CONSTRAINT` with wording that makes contradiction disallowed, not merely discouraged

Why first:

- this is the highest-leverage generation-side fix
- it directly targets the survey-proven authority demotion seam

### Tranche B. Stage4-Readiness Binding Prevalidation

Goal:

- make structurally weak blueprints surface as binding PASS_WITH_FIX instead of slipping through as clean PASS

Realization:

- widen `_BINDING_PREVALIDATION_CATEGORIES`
- add one bounded collector for Stage4-readiness contract issues:
  - `opening_anchor`
  - `mission_clarity`
  - `timeline_specificity`
  - `protagonist_state`
- wire this collector into `_python_pre_validate()`

Why second:

- existing binding escalation already exists
- new categories can ride the existing PASS -> PASS_WITH_FIX contract without redesigning Director ownership

### Tranche C. Residual Follow-Up, Not In This Turn

- retry authority preservation
- Stage 3 -> Stage 4 negative-obligation contract (`must_not_erase`)
- Stage 2 schema normalization
- fact-lock / timeline contradiction escalation beyond advisory-only pass behavior

### Tranche D. Stage2/3 Context Normalization

Goal:

- make Stage 2 and Stage 3 prompt bundles behave more like explicit authority stacks and less like mixed payload dumps

Realization:

- Stage 2:
  - replace raw `curr_block` JSON prompt injection with a structured current-block authority packet
  - move current-block DNA ahead of large previous-arc context in the prompt order
- Stage 3:
  - move hard constraints ahead of arc-mission prose in the prompt order
  - mark `prev_info` as tiered continuity/archive material instead of an undifferentiated blob
  - align cached shared-context ordering to the same hierarchy

Why now:

- the fresh context-hierarchy survey showed the next primary blocker is upstream flattening, not missing runtime evidence
- another canary before normalization would mostly reconfirm known semantic drift rather than buy new signal

## 8. Execution Tranches

1. `Tranche A` authority promotion in `blueprint_ensemble.py`
2. `Tranche B` Stage4-readiness binding prevalidation in `unified_blueprint_validator.py`
3. `Tranche D` Stage2/3 context normalization in `arc_ensemble.py`, `blueprint_ensemble.py`, `ensemble.yaml`
4. targeted regression and doc/queue sync
5. residual canary decision after bounded verification

## 9. Acceptance Criteria

- `arc_constraint_summary` no longer renders in the weakest advisory band
- targeted tests prove the new authority placement
- Stage 3 Python prevalidation can now emit:
  - `opening_anchor`
  - `mission_clarity`
  - `timeline_specificity`
  - `protagonist_state`
- those new categories trigger the existing binding PASS -> PASS_WITH_FIX contract
- Stage 2 prompt bundle renders a structured current-block authority packet instead of raw JSON dump
- Stage 2 prompt order presents current-block DNA ahead of previous-arc context
- Stage 3 prompt order presents constraints ahead of arc-focus prose
- Stage 3 previous-info bundle exposes explicit tiering between direct truth and archive appendix
- no new `180+ LOC` function is introduced by the touched change set
- queue mirror and roadmap are refreshed coherently

## 10. Verification Plan

- `pytest tests/test_stage3_clarity_density_wave1.py -q`
- targeted arc-ensemble prompt packet regression
- targeted blueprint-ensemble hierarchy regression
- targeted validator regression file for new Stage4-readiness categories
- `python -m py_compile` on touched production modules
- `python scripts/check_utf8_hygiene.py` on touched code/docs
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- do not reopen Stage 4 in this turn
- do not redesign Stage 2 schema in this turn
- do not widen this wave into Stage 3 retry-architecture overhaul
- do not run a new canary in this turn
- preserve Director final authority; Python prevalidation remains pre-Director and binding only in the existing PASS -> PASS_WITH_FIX seam
- if new category noise becomes excessive, reduce thresholding rather than bypass binding semantics wholesale

## 12. Temp Queue Notes

- temp status: `in_progress (structural/runtime groundwork landed; context-normalization tranche active; canary deferred by user)`
- cleanup condition:
  - remove temp mirror only after implementation + verification + closure audit
- roadmap dependency:
  - explicit user redirect makes this lane priority 1 ahead of older parked/blocked legacy items

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Record

Pass 1, structure and scope:

- kept the lane bounded to Stage 3 authority + validator hardening
- did not inflate this into Stage 2 redesign or Stage 4 resume

Pass 2, evidence and consistency:

- aligned the execution shape to the `0_0` survey verdict that Stage 3 is the primary blocker
- treated prior `clarity-density wave1` as substrate, not as enough closure for the current problem

## 15. Runtime Validation Update

Current runtime evidence comes from:

- `projects/canary_0_0_stage3_arc2_readiness_r3/logs/stage3_canary_summary.json`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-runtime-audit.md`

What runtime proved:

- partial `Stage3-only canary` now works for `from_ep=5`
- `ep5~9` current-session Stage 3 sink alignment is `ok`
- `ep5~9` current-session final verdicts are all `PASS`

What runtime did not close:

- fresh `ep5` still invents off-arc physical intrusion / action interruption beats
- `fact_lock_institution` and `arc_timeline` survive as non-binding PASS noise

Operational conclusion:

- keep `Stage4` paused
- do not close this lane yet
- Stage 3 semantic fidelity child wave has now closed
- current bounded wave should target Stage2/3 context normalization before any further canary

## 16. Static Validation Update

Current turn realization:

- `Stage2` prompt now renders a structured current-block authority packet instead of raw JSON dump
- `Stage2` prompt order now presents `Current Block DNA` and `Current Block Event Guard` ahead of previous-arc carryover
- `Stage3` cached shared-context order now follows `constraints -> arc_focus -> prev_info -> hud`
- `Stage3` prompt order now presents `Constraint Stack` ahead of `Arc Mission`
- `Stage3` previous-info bundle now exposes explicit truth/archive tiers

Static validation completed:

- `python -m py_compile modules/domain/agents/arc_ensemble.py modules/domain/agents/blueprint_ensemble.py tests/test_arc_ensemble_lane_a.py tests/test_blueprint_ensemble_generate_ensemble.py`
- `ruff check modules/domain/agents/arc_ensemble.py modules/domain/agents/blueprint_ensemble.py tests/test_arc_ensemble_lane_a.py tests/test_blueprint_ensemble_generate_ensemble.py`
- `pytest tests/test_arc_ensemble_lane_a.py tests/test_blueprint_ensemble_generate_ensemble.py -q`
- `pytest tests/test_stage3_clarity_density_wave1.py tests/test_stage23_stage4_readiness_wave1.py -q`
- `pytest tests/test_tier4_ensemble_caching.py -k "arc_ensemble or blueprint_ensemble_prev_info or constraint_summary or single_format_constraints_definition" -q`

Post-validation operating decision:

- do not run canary in this turn
- keep parent lane active
- hand off runtime proof / canary decision to the later Opus-assisted step

Pass 3, execution and readability:

- tranches are ordered by ROI and dependency
- residual seams are explicitly deferred rather than hidden
- context-normalization work is intentionally bounded to prompt/handoff structure, not schema redesign

Confidence: `96%`

## 17. Context Normalization Runtime Validation Update (ctxnorm_r1 canary)

Canary: `canary_0_0_stage34_arc2_ctxnorm_r1`
Session (Stage3): `20260401_103911`
Audit doc: `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-context-normalization-runtime-closure-audit.md`
Evidence: `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-context-normalization-runtime-closure-evidence.json`

What ctxnorm_r1 proved:

- Stage3 ep5-9: all 5 PASS, current-session sink alignment `ok`
- ep5 narrative content clean (no off-arc intrusion in integrated_scenario/scenes)
- ep7 Director rejected off-arc 괴한 난입 candidate (semantic fidelity filter at Director level working)
- ep8 binding prevalidation caught 기관명 오류 and corrected inplace
- Tranche D Stage3 runtime verified

What ctxnorm_r1 did not close:

- Stage4 ep2 exhausted 10 rounds without finalization
- Root cause: `strong_advisory_escalation_non_local_fix` cycling loop — separate issue, not Tranche D regression
- Stage4 advisory escalation loop for ep2 needs separate investigation before Stage4 resume

Operational conclusion:

- Stage3 sub-verdict: `closure_candidate`
- Stage4 sub-verdict: `blocked_upstream_advisory_escalation_loop`
- Parent lane verdict: `partial`
- keep Stage4 paused
- open items: ep2 advisory loop investigation, ep5 tactical_semantic_fidelity CRITICAL confirmation, ep8 attempt-loop cost profiling
