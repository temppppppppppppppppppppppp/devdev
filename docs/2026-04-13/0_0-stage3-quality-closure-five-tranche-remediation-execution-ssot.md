# 0_0 Stage3 Quality Closure Five Tranche Remediation Execution SSOT

Date: 2026-04-13 (originally drafted) / 2026-04-14 (Tranche 1 landed; local workspace now also lands T2 residual cleanup, T3 retry feedback surgery, and bounded T4.1 candidate-summary expansion)
Status: closed (2026-04-19 closure review; `T1~T3` plus bounded `T4.1` are landed historical backing, the rerun-gate floor remains met but unconsumed, deferred `T4.2~T5` stay proof-contingent, and this lane no longer represents honest active or parked queue debt)
Canonical Path: `docs/2026-04-13/0_0-stage3-quality-closure-five-tranche-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage3-quality-closure-five-tranche-remediation-execution-ssot.md` (removed during the 2026-04-19 closure tranche)
Commit State:
- Baseline Commit: `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `dirty: stage3 producer/ensemble/runtime/validator edits, live 000_260412_a rerun artifacts, the 10 t1..t10 deliverables, the 10-terminal parent order, the synthesis doc, and the 2026-04-13 audit/survey docs already present in worktree`
- Resume Commit: `029df1a74af89a7b5387c449f4723a5df0d000d4`
- Resume Drift Summary: `current HEAD@029df1a7 is authoritative for queue closure; the parent contract-tightening lane and the sibling state-arbiter lane are now both closed, the rerun-gate floor remains met but operator authorization is still unconsumed, and the deferred `T4.2~T5` family now reads as contingent proof backlog rather than active queue debt`

2026-04-14 local bounded landing override:

- Local landing HEAD: `81b426a688c2a5b6279d254c7746baac1261235b`
- authoritative gate doc: `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
- supporting structural survey: `docs/2026-04-14/stage3-runtime-retry-structural-debt-survey.md`
- authoritative conservative predictive estimate: `93% resolved`
- do not auto-authorize or auto-present fresh Stage3 runtime unless a canonical current-head bounded survey records `>=90%` predictive contract-debt resolution
- if the estimate falls below `90%`, the only authorized next step is bounded debt-remediation survey / execution-SSOT refresh
- current policy state is `threshold met, authorization not yet consumed`
- the current local workspace now lands child-lane T2 residual cleanup, the full Tranche 3 retry-feedback surgery bundle, and bounded T4.1 Director candidate-summary expansion
- remaining T4.2-T4.5 work stays deferred until a fresh rerun proves whether additional rubric or sink work is still needed
- T5 remains gated and must not move before the post-T1/T2/T3 proof conditions in this SSOT are actually satisfied
- do not auto-present `projects/000_260412_a` Stage3 continuation from `ep9` or any rollback-based proof rerun as the active local next action
- any fresh Stage3 runtime now requires explicit operator re-authorization even though the `>=90%` estimate floor is met
Source Survey Docs:
- `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- `docs/2026-04-13/s2-s3-s4-runtime-improvement-synthesis.md`
- `docs/2026-04-13/t1-producer-initial-prompt-forensics.md`
- `docs/2026-04-13/t2-stage3-retry-feedback-loop-audit.md`
- `docs/2026-04-13/t3-producer-context-packet-audit.md`
- `docs/2026-04-13/t4-producer-cheap-admission-effectiveness-audit.md`
- `docs/2026-04-13/t5-validator-heuristic-true-false-positive-audit.md`
- `docs/2026-04-13/t6-ensemble-candidate-diversity-audit.md`
- `docs/2026-04-13/t7-director-vs-validator-authority-overlap-audit.md`
- `docs/2026-04-13/t8-stage3-cost-attribution-audit.md`
- `docs/2026-04-13/t9-stage2-to-stage3-handoff-quality-audit.md`
- `docs/2026-04-13/t10-stage3-to-stage4-handoff-and-s4-writer-smarts-audit.md`
- `docs/2026-04-13/stage3-ep8-cw-director-root-cause-parallel-survey.md`
- `docs/2026-04-13/stage3-producer-contract-tightening-3pass-audit-and-adversarial-review.md`
- `docs/2026-04-13/stage3-cost-first-decision-surface-static-survey.md`
- `docs/2026-04-13/s2-s3-s4-producer-smarts-bounded-3pass-audit.md`
- `docs/2026-04-13/s2-s3-s4-producer-smarts-p2-p3-followup-survey.md`
- `docs/2026-04-13/stage3-three-tranche-safe-sequencing-plan.md`
- `docs/2026-04-14/stage3-runtime-retry-structural-debt-survey.md`
- `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`
- `docs/2026-04-19/stage3-quality-closure-five-tranche-reactivation-refresh.md`
- `docs/2026-04-19/stage3-quality-closure-five-tranche-closure-review.md`
Evidence Artifacts:
- `0_temp.txt` (latest live-run console capture, ep8 reject family at lines 400–469)
- `projects/000_260412_a/project_data.db`
- `projects/000_260412_a/logs/pass_rate_monitor.json`
- `projects/000_260412_a/logs/metrics/metrics_20260413_194343.json`
- `projects/000_260412_a/logs/quality_metrics.jsonl`
- `projects/000_260412_a/logs/session/llm_io.jsonl`
- `projects/000_260412_a/logs/session/ui_events.jsonl`
- `projects/000_260412_a/logs/runtime_audit_summary.json`
- `projects/000_260412_a/logs/artifacts/stage3/ep_0001..ep_0007/attempt_XX/*.json`
- `projects/000_260412_a/plans/arcs/arc_001.txt`, `arc_002.txt`
- `projects/000_260412_a/plans/blueprints/blueprint_0001.txt..blueprint_0007.txt`
- `docs/2026-04-13/stage3-producer-3pass-audit-adversarial-evidence.json`
- `docs/2026-04-13/stage3-producer-adversarial-followup-x3-evidence.json`
Side-Effect Coverage: covered (file/DB/log/queue/cache/runtime/operator surfaces all enumerated in §6)

## 1. Intent

Realize all 5 bounded tranches identified by the 2026-04-13 synthesis (`s2-s3-s4-runtime-improvement-synthesis.md`) under one execution authority, in the safest landing order, with snapshot commit boundaries between tranches and a verification gate before any cost-side tranche lands.

This SSOT exists because:

1. The 10-terminal parallel investigation produced converging evidence (10/10 weight) that one single failure family (opening-transition vocabulary collision) drives the dominant Stage3 reject loop on ep1–ep8.
2. The synthesis ranked 5 bounded tranches by ROI, with explicit prerequisite chain: Tranche 1 must land first, Tranches 2/3/4 may run in parallel after Tranche 1 lands, Tranche 5 must land only after Tranches 1–3 are live-proven.
3. The synthesis itself is survey/proposal-only and cannot authorize code edits; this SSOT is the bridge from proposal to bounded realization.

This SSOT does NOT:

- expand scope beyond the 5 tranches the synthesis ranked
- open a new queue family (it sits inside the existing `0_0-stage3-contract-tightening-remediation` parent lane)
- override the parent `0_0-stage3-contract-tightening-remediation` lane when a stronger front residual is still active there
- authorize live rerun without the explicit verification gates in §11
- mutate Stage4 owner surfaces (T10 hypotheses are deferred per synthesis §5)
- alter Director rubric weights without the post-Tranche-1 proof rerun (Tranche 4)

## 2. Baseline Facts

- Latest live capture: `0_temp.txt:400-469` shows ep8 still cycling on `PASS_WITH_FIX unresolved after 3 patch attempts -> REJECT` with `MAJOR | opening_transition | opening_transition.type mismatch: declared 'direct_continuation' vs normalized 'explicit_transition'` after every prior producer-smarts tranche has landed.
- Pass-rate evidence: ep1–ep7 closed but at 6–10 attempts each, 25–45 minutes wall-clock, $2.25–$7.36 per ep, with 5/7 final verdicts being `PASS_WITH_WARNING`, not clean `PASS`. Cumulative spend ≈ $35+ per session before ep8 even closes.
- Root-cause analysis: synthesis Θ1 has 10/10 evidence weight (every terminal hits opening-transition vocabulary collision); Θ2/Θ4/Θ5/Θ6/Θ7/Θ9 are downstream of or feeders to Θ1.
- Synthesis-time live-grep verified 5 critical anchors before save:
  - `stage_cross_stage_contract.py:18-36` `_OPENING_TRANSITION_SCENE_MARKERS` contains `진입` (line 34), `향해` / `향하` (lines 25–26)
  - `stage_cross_stage_contract.py:37-51` `_OPENING_TRANSITION_TIME_SHIFT_MARKERS` contains `->` (line 49), `→` (line 50)
  - `unified_blueprint_validator.py:80-92` `_TACTICAL_INTRUSION_ENTRY_MARKERS` contains `직원` (line 91), `그림자` (line 89)
  - `unified_blueprint_validator.py:93-108` `_TACTICAL_INTRUSION_CONFLICT_MARKERS` contains boardroom verbs (`대응` 98, `차단` 99, `제압` 96, `위협` 102, `협박` 103)
  - `unified_blueprint_validator.py:455` `merged_scope = "full" if regenerate_categories else str(fix_scope or "inplace")`
  - `blueprint_ensemble.py:989-1009` `_normalize_opening_transition_contract` mutates `candidate["opening_transition"]` before cheap gate runs
  - `tactical_utils.py:31` `extract_episode_tactical(...)` priority chain `episode_details > regex > tactical_doc fallback`
- Synthesis-time correction: T9 reported `extract_episode_tactical` has 2 callers; live grep found **13 production callsites** (Stage3, Stage4, Director, continuity, ToT, prompt_builder). Tranche 1 sub-edit 3 was rescoped to a parameter-flag pattern.
- Test baseline: workspace is dirty but production tests are green for the surfaces this SSOT touches; specific shards are enumerated per-tranche in §10.

## 3. Scope

Included:

- `modules/core/stage_cross_stage_contract.py` (opening-transition normalizer marker cleanup)
- `modules/core/tactical_utils.py` (Stage3 tactical handoff parameter flag, no default behavior change)
- `modules/domain/agents/blueprint_ensemble.py` (cheap admission declared/inferred split, fix_pack channel, Stage3 producer-input flag flip)
- `modules/domain/agents/three_phase_blueprint_runtime.py` (retry feedback directive shape, fix_pack forwarding, operator telemetry split)
- `modules/domain/agents/three_phase_blueprint_generator.py` (inplace gate on non-empty fix_pack)
- `modules/domain/agents/unified_blueprint_validator.py` (tactical/temporal/scenario-density calibration, opening-transition inplace allowance)
- `modules/domain/agents/director_ensemble.py` (rubric alignment, candidate summary expansion)
- `modules/core/stage3_orchestrator.py` (cost cap, persistence wiring)
- `config/prompts/ensemble.yaml` (decision table, tactical token list, paired example)
- `tests/test_unified_blueprint_validator_lane_c.py` (validator calibration cases)
- `tests/test_blueprint_ensemble_generate_ensemble.py` (cheap admission split cases, fix_pack channel cases)
- `tests/test_blueprint_patch_mode.py` (inplace allowance for opening_transition alias)
- `tests/test_stage3_orchestrator_handle_success_lane_c.py` (verdict persistence, cost cap circuit breaker)
- new test files only where existing files have grown past complexity guardrails (≥120 LOC test functions); preferred is to extend existing tests

Excluded:

- Stage4 chief writer surfaces (T10 hypotheses deferred per synthesis §5)
- Stage2 arc generation retuning (only the Stage2→Stage3 handoff helper changes here)
- DecisionKernel migration / Polaris long-horizon work
- model swap, tier change, vendor cost negotiation
- new genre support
- DB schema redesign
- broad Stage3 prompt rewrite outside the bounded edits in Tranches 1+2
- live rerun before the per-tranche validation gates pass
- Stage4 admission vocabulary (T10 deferred)

## 4. Pass 1. Inventory Summary

The 10 themes from `s2-s3-s4-runtime-improvement-synthesis.md` §3 collapse into 4 quality fault classes plus 2 cost classes:

Quality fault classes:

1. **Opening-transition vocabulary collision** — Θ1 (10/10) — single dominant family, cross-cuts producer / validator / Stage2 handoff / Director rubric / repair routing
2. **Producer-validator vocabulary mismatch on tactical / temporal / scenario_density** — Θ2 (5/10), Θ5 (4/10) — secondary FP families that compound Θ1
3. **Retry feedback rot** — Θ4 (4/10) — symptom-text-only feedback prevents attempt N+1 from learning attempt N's failure
4. **Director rubric / audit visibility gaps** — Θ6 (3/10), Θ3 (5/10) — Director scores prose, validator binds structure; rejected candidates not persisted

Cost classes:

5. **Round-cap saturation** — C1+C2 — 4/7 episodes hit attempt cap 10 with no verdict improvement in rounds 7–10
6. **Patch_mode zero-rescue** — C3 — $3.34 spent on inplace patches with 0 clean-PASS lift

Cross-cutting blast-radius caveat: Tranche 1 sub-edit 3 changes the Stage3 producer-input callsite of `extract_episode_tactical`. The helper itself has 13 production callsites (Stage3, Stage4, Director, continuity, ToT, prompt_builder). The sub-edit MUST use a parameter flag pattern, not a default-behavior change.

## 5. Pass 2. Semantic Classification

### Class A. Primary realization (this SSOT)

- Tranche 1: opening-transition vocabulary coherence (validator marker cleanup, prompt decision table, Stage3-only handoff parameter flag, cheap-admission declared/inferred split, repair router opening_transition inplace allowance)
- Tranche 2: producer contract teaching + validator calibration cleanup (tactical/scenario/temporal FP cleanup, prompt teaching of full token vocabulary)
- Tranche 3: retry feedback surgery (`fix_pack` channel into `generate_ensemble`, directive-shaped reject feedback, operator telemetry split)
- Tranche 4: Director rubric alignment + audit visibility (binding-contract integrity rubric axis, candidate summary expansion, losing-candidate persistence, cheap-reject telemetry wiring)
- Tranche 5: cost cap + round truncation (stop-if-no-improvement circuit breaker, attempt cap 10→7, conservative/balanced flavor decision) — gated on Tranche 1+2+3 proof rerun

### Class B. Residual but related (in scope of this SSOT only as watchlist)

- conservative/balanced fan-out flavor decision: keep deferred unless T6's "prompt delta 0.1%" measurement justifies activating them
- `extract_episode_tactical` cross-stage callers other than Stage3: not touched, only the Stage3 producer-input callsite gets the new flag
- `patch_with_feedback` 5-field hard gate: belongs to Stage4 chief writer; deferred with T10
- Tier 3 / Tier 4 dead-code paths (`blueprint_ensemble.py:1658-1685`): deferred

### Class C. Explicitly deferred outside this SSOT

- all T10 Stage4 vocabulary alignment hypotheses (Stage4 has not run in `000_260412_a`)
- `single-candidate fail-closed` (T7.H4) — re-opens TF-36 deliberate design
- ep2 crashed-session resilience ($5.52 waste) — process-level, belongs in session-resilience track
- Polaris / DecisionKernel migration
- broader Director comparator rewrite
- broader chief writer prompt rewrite

## 6. Side-Effect Map

- file writes / artifacts:
  - new sidecar files `losing_blueprint__<strategy>.json` per Stage3 attempt directory (Tranche 4 sub-edit 4)
  - existing `final_blueprint__<strategy>.json` shape unchanged
  - no new directories; same `projects/<project>/logs/artifacts/stage3/ep_NNNN/attempt_NN/` layout
- DB / schema / transaction boundaries:
  - `stage_attempts.initial_verdict` and `director_selections.verdict` are existing columns; Tranche 4 sub-edit 3 only populates them, no schema migration
  - no new tables, no new indexes, no transaction-boundary changes
- JSONL / log / audit sinks:
  - Tranche 4 sub-edit 5 wires cheap-reject `_operator_log` calls in `_sanitize_blueprint_candidate` into `ui_events.jsonl`; this adds new `component=BlueprintEnsembleGenerator` rows, additive only
  - `quality_metrics.jsonl` shape unchanged
- console / UI / operator output:
  - retry-feedback prompt sections labeled differently after Tranche 3 (`[이전 검증 경고]` → directive-shape header)
  - operator-facing `[Director fix_scope]` and `[Local patch gate]` lines move from LLM payload to operator-only telemetry sink (Tranche 3 sub-edit 5)
- rollback / recovery / retry:
  - Tranche 5 round-cap circuit breaker may exit a retry loop earlier than current `max_retries=9`; recovery path is identical (same `PASS_WITH_WARNING` terminal verdict)
  - no new rollback paths
- cache / global state:
  - Director comparator caching surface unchanged
  - Stage3 ensemble cache unchanged
  - Tranche 1 sub-edit 3 may slightly increase Stage3 producer-input prompt size when `prefer_full_doc=True` is flipped; cache key derivation unaffected
- bootstrap / config-env mutation:
  - none

## 7. Realization Architecture

Each tranche is one bounded realization unit with its own snapshot commit, validation gate, and stop condition. The synthesis sequencing rule is binding: **Tranche 5 must not land until a fresh proof rerun on `000_260412_a` ep1–ep8 confirms average attempt count fell below 6 after Tranches 1–3 are live**.

```
Tranche 1 → snapshot commit → fresh proof rerun → measure attempt-count delta
   ↓  (only if Tranche 1 proof gate passes)
Tranche 2 (parallel-safe) ┐
Tranche 3 (parallel-safe) ├ → snapshot commit per tranche
Tranche 4 (parallel-safe) ┘    → fresh proof rerun → confirm avg attempt < 6
   ↓  (only if Tranche 1+2+3 second proof gate passes)
Tranche 5 → snapshot commit → fresh proof rerun → confirm cost reduction without verdict regression
```

Parallel-safe means the three tranches do not touch the same line ranges. Tranche 2 touches `unified_blueprint_validator.py:80-108`, `:1808-1865`, `:2446-2449`, plus `config/prompts/ensemble.yaml:387`. Tranche 3 touches `three_phase_blueprint_runtime.py:1120-1136, 1401-1415, 2088-2174` plus `blueprint_ensemble.py:584` plus `three_phase_blueprint_generator.py:204`. Tranche 4 touches `director_ensemble.py:1993-2070`, `stage3_orchestrator.py` persistence sites, `blueprint_ensemble.py:1411-1542` operator-log wiring. The only overlap is `blueprint_ensemble.py` (Tranche 3 touches `:584`, Tranche 4 touches `:1411-1542`); these are different functions and parallel-safe.

## 8. Execution Tranche Sequence

1. **Tranche 1** — Opening-Transition Vocabulary Coherence (5 sub-edits, single commit)
2. **Parent Gate A** — if the parent `0_0-stage3-contract-tightening-remediation` lane still fronts the bounded tactical-authority synonym parity tranche, land that parent tranche first
3. **Proof Gate 1** — fresh ep1–ep8 rerun on `000_260412_a` after Tranche 1 lands and Parent Gate A is closed
4. **Tranche 2** — Producer Contract Teaching + Validator Calibration Cleanup (4 sub-edits, single commit)
5. **Tranche 3** — Retry Feedback Surgery (5 sub-edits, single commit)
6. **Tranche 4** — Director Rubric Alignment + Audit Visibility (5 sub-edits, single commit)
7. **Proof Gate 2** — fresh ep1–ep8 rerun after Tranches 2+3+4 land; confirm avg attempt < 6
8. **Tranche 5** — Cost Cap + Round Truncation (3 sub-edits, single commit)
9. **Proof Gate 3** — fresh ep1–ep8 rerun after Tranche 5 lands; confirm cost reduction without verdict regression

## 9. Per-Tranche Detailed Specification

### 9.1 Tranche 1 — Opening-Transition Vocabulary Coherence

Owner: this SSOT (`0_0-stage3-quality-closure-five-tranche-remediation`) plus support from `0_0-stage3-opening-transition-contract-normalization-remediation` sibling lane.

Goal: stop the dominant ep1–ep8 reject family by aligning producer prompt, validator normalizer, Stage2→Stage3 handoff, cheap-admission gate, and repair router on a single coherent opening-transition contract.

Sub-edit 1.1 — Validator marker calibration:
- File: `modules/core/stage_cross_stage_contract.py`
- Edit: in `_OPENING_TRANSITION_SCENE_MARKERS` (lines 18–36) remove `"진입"` (line 34), `"향해"` (line 25), `"향하"` (line 26); keep `"* * *"`, `"장면 전환"`, `"한편"`, `"이동"`, `"옮기"`, `"걸음을 옮"`, `"발을 옮"`, `"나서"`, `"들어서"`, `"빠져나와"`, `"도착"`, `"전환"`, `"컷"`, `"cut"`. In `_OPENING_TRANSITION_TIME_SHIFT_MARKERS` (lines 37–51) remove `"->"` (line 49) and `"→"` (line 50); keep all absolute time-shift markers.
- Source evidence: T5.H1 (100% FP rate across 5 ep8 candidates / 4 retry rounds)
- Risk: medium — removed tokens may leak a real explicit-transition through; mitigation = `진입` is also a diegetic verb, `→` is also a duration span; T5 evidence shows zero true positives in the captured run

Sub-edit 1.2 — Producer prompt teaches the rule:
- File: `config/prompts/ensemble.yaml`
- Edit: replace the bare enum declaration at lines 411–414 with a 3-row decision table covering `direct_continuation` / `explicit_transition` / `jump_opening` with concrete `prev_end_location` + `time_flow` + `start_location` examples; verbatim text proposal in `t1-producer-initial-prompt-forensics.md` §4 H1
- Source evidence: T1.H1
- Risk: low — pure prompt text addition

Sub-edit 1.3 — Stage3-only `extract_episode_tactical` parameter flag:
- File 1: `modules/core/tactical_utils.py`
  - Edit: add `prefer_full_doc: bool = False` parameter to `extract_episode_tactical` at line 31; when `True`, concatenate `episode_details` (as TL;DR header) + full `tactical_doc` per-episode slice (as body) under bounded budget (≤2,000 chars per ep)
  - **Critical constraint**: default value MUST be `False` to preserve current behavior for the 12 non-Stage3-producer-input callsites
- File 2: `modules/domain/agents/blueprint_ensemble.py`
  - Edit: at the Stage3 producer-input callsite (line 306), pass `prefer_full_doc=True`
- Source evidence: T9.H1 + synthesis-time blast-radius correction
- Risk: high (was originally low in T9 deliverable; synthesis upgraded after live grep). Mitigation: parameter default stays `False` so the 12 other callsites (`unified_blueprint_validator.py:2340`, `three_phase_blueprint_generator.py:188`, `director_ensemble.py:1968`, `continuity_inspector.py:392`, `continuity_arc.py:583/990/996`, `blueprint_constraint_compiler.py:327/772/914`, `tree_of_thoughts.py:389`, `prompt_builder.py:700`, `stage4_context_builder.py:2277`, `stage3_orchestrator.py:2460`) are unaffected
- Pre-edit verification: re-grep `extract_episode_tactical(` and confirm callsite count + default-arg compatibility

Sub-edit 1.4 — Cheap admission distinguishes declared vs inferred:
- File: `modules/domain/agents/blueprint_ensemble.py`
- Edit: in `_normalize_opening_transition_contract` at lines 989–1009, return a `(declared_value, inferred_value)` tuple instead of a side-effecting in-place mutation; downstream `_blueprint_contract_admission_reason` should fail-closed when LLM omitted the field entirely AND no continuity evidence permits inference
- Source evidence: T4.H1 (71.2% of 274 fan-out responses omitted opening_transition top-level)
- Risk: low–medium — pre-Tranche-1.2 producer prompt edit, this could spike attempt-1 cheap rejects; mitigation = land sub-edits 1.1+1.2+1.3+1.4 in one commit so the new prompt teaches the rule before the new gate enforces it

Sub-edit 1.5 — Repair router allows inplace for opening_transition alias:
- File: `modules/domain/agents/unified_blueprint_validator.py`
- Edit: at line 455, replace the unconditional `merged_scope = "full" if regenerate_categories else str(fix_scope or "inplace")` with a check that lets `opening_transition` (when the only binding category is the opening-transition alias mismatch) route to `inplace`; expand `_BINDING_PREVALIDATION_REGENERATE_CATEGORIES` set logic to whitelist the alias-only case
- Source evidence: T7.H3 (opening_transition alias is a 1-line patch, but `merged_scope=full` blocks it from ever using inplace)
- Risk: medium — must only apply when `opening_transition` is the SOLE binding category, not when it co-fires with other binding issues

Snapshot commit message: `fix: stage3 opening-transition vocabulary coherence`

Test contract for Tranche 1:
- existing `tests/test_unified_blueprint_validator_lane_c.py`: confirm `opening_transition_contract`, `opening_transition_mismatch` cases still pass
- existing `tests/test_blueprint_ensemble_generate_ensemble.py`: confirm `missing_opening_transition_contract`, `anti_contamination_contract`, `dense_two_scene_blueprint` still pass
- existing `tests/test_blueprint_patch_mode.py`: confirm `escalates_structural_binding_categories_to_full_regenerate`, `escalates_contract_blocked_scene_model_to_full_regenerate`, `pass_with_fix_unresolved` still pass
- new test cases:
  - `test_opening_transition_marker_calibration_no_false_positive_on_arrow_time_flow`
  - `test_opening_transition_marker_calibration_no_false_positive_on_diegetic_jin_ip`
  - `test_extract_episode_tactical_default_behavior_unchanged_for_existing_callers`
  - `test_extract_episode_tactical_prefer_full_doc_concatenates_under_budget`
  - `test_blueprint_cheap_admission_returns_declared_inferred_split`
  - `test_blueprint_cheap_admission_fails_closed_on_pure_omission_without_continuity_evidence`
  - `test_repair_router_allows_inplace_for_opening_transition_alias_only`
  - `test_repair_router_still_forces_full_when_opening_transition_co_fires_with_other_binding`

Validation gate for Tranche 1:
- `python -m py_compile modules/core/stage_cross_stage_contract.py modules/core/tactical_utils.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/unified_blueprint_validator.py`
- `python scripts/check_utf8_hygiene.py <touched files>`
- `pytest tests/test_unified_blueprint_validator_lane_c.py tests/test_blueprint_ensemble_generate_ensemble.py tests/test_blueprint_patch_mode.py tests/test_stage23_stage4_readiness_wave1.py -q`
- `python scripts/ops_validator.py --strict`
- targeted regression: load one ep8 reject candidate from `projects/000_260412_a/logs/artifacts/stage3/ep_0007/attempt_10/final_blueprint__action_focused.json` through validator and confirm the opening_transition mismatch no longer fires after Tranche 1 lands

Stop conditions for Tranche 1:
- if more than 1 existing test breaks, stop and audit
- if `_BINDING_PREVALIDATION_REGENERATE_CATEGORIES` whitelist becomes more than 2 entries, stop (scope creep)
- if `extract_episode_tactical` callsites change count between draft-time and edit-time, stop and re-verify
- if a new `→` use case is found in time_flow that legitimately means time shift, stop and revisit T5.H1

Proof Gate 1 acceptance criteria:
- ep1–ep8 fresh rerun on `000_260412_a`
- average Stage3 attempt count must drop below 6 (current is 8.4)
- ep8 specifically must close (it was interrupted in the captured session)
- opening_transition reject family count must drop to ≤ 1 across the rerun
- all PASS_WITH_WARNING verdicts must come from non-opening-transition reasons

### 9.2 Tranche 2 — Producer Contract Teaching + Validator Calibration Cleanup

Owner: same parent SSOT.

Goal: close the secondary FP families (tactical_semantic, scenario_density, temporal_deictic) and teach producer the full token vocabulary so producer naturally avoids forbidden territory.

Sub-edit 2.1 — Tactical-semantic vocabulary cleanup:
- File: `modules/domain/agents/unified_blueprint_validator.py`
- Edit: in `_TACTICAL_INTRUSION_ENTRY_MARKERS` (lines 80–92) remove `"직원"` (91) and `"그림자"` (89); they fire on PB / boardroom scenes without any physical-threat presence. In `_TACTICAL_INTRUSION_CONFLICT_MARKERS` (lines 93–108), constrain `"대응"` (98), `"차단"` (99), `"제압"` (96), `"위협"` (102), `"협박"` (103) to require co-occurrence with at least one physical-threat entry marker (`괴한`, `난입`, `들이닥`, `습격`, `침입자`) within ±5 sentences in the same scene
- Source evidence: T5.H2 (5 ep8 candidates, 100% FP, all PB negotiation scenes)
- Risk: medium — loosening these without co-occurrence risks letting real intrusion through; mitigation = co-occurrence is part of the same edit, not a follow-up

Sub-edit 2.2 — Producer prompt teaches the full tactical token family:
- File: `config/prompts/ensemble.yaml`
- Edit: replace the ~6-token mention at line 387 with the full 24-token family (entry + conflict) plus the rule "if Arc tactical_doc lacks any physical-threat entry marker for the current episode, do not invent any of these tokens in scene_breakdown / integrated_scenario"
- Source evidence: T1.H3
- Risk: low — pure prompt text addition

Sub-edit 2.3 — Scenario-density anchor regex:
- File: `modules/domain/agents/unified_blueprint_validator.py`
- Edit: at lines 2446–2449, expand the anchor regex to match space-separated proper nouns (`한정호 저택`, `SW 인베스트먼트`); current pattern requires contiguous Hangul + suffix
- Source evidence: T5.H4 (investment-genre legitimate proper nouns missed entirely)
- Risk: low — scenario_density is advisory-only; loosening reduces FP without changing PASS/REJECT semantics

Sub-edit 2.4 — Temporal-deictic diegetic discriminator:
- File: `modules/domain/agents/unified_blueprint_validator.py`
- Edit: in `_collect_temporal_deictic_drift_issues` at lines 1808–1865, add an allowlist input from `arc_constraint_summary` or `inherited_state.timeline_anchors` so canonical 회귀자 backstory anchors (`18년 후의 기억` for the 000_260412_a project) pass without firing the `num>=5` threshold
- Source evidence: T5.H3 (4 ep6 candidates, all firing on the same canonical anchor)
- Risk: medium — allowlist must be sourced from arc-side truth, not blueprint-side text, to prevent producer from "lying" the anchor into the blueprint to bypass the rule

Sub-edit 2.5 — Korean tactical-intrusion synonym lexicon expansion (absorbs adversarial audit P1):
- Files:
  - `modules/domain/agents/unified_blueprint_validator.py:80-108` (validator marker lists)
  - `modules/domain/agents/blueprint_ensemble.py:970-987` (`_detect_unauthorized_tactical_intrusion` producer mirror)
- Edit: add the missing Korean synonym entries identified by `docs/2026-04-13/stage3-producer-adversarial-followup-x3-addendum.md` Finding 3:
  - Entry markers (verb forms): `들이닥치` (covers `들이닥쳐`, `들이닥치는`, `들이닥쳤다`); the existing prefix `들이닥` already substring-matches but the audit demonstrated bypass under specific test cases — verify match logic and tighten if needed
  - Conflict / coercion verb stems: `팔목을 비틀`, `팔을 비틀`, `손목을 잡아챔`, `주먹을 들이밀`, `주먹을 들이밂`, `입막음`, `입막음을 강요`, `강요`, `강박`, `목을 조르`, `목덜미를 잡`, `멱살을 잡`, `벽으로 밀치`, `의자로 가로막`
  - Mirror the same additions into the producer-side `blueprint_ensemble.py` `_detect_unauthorized_tactical_intrusion` lookup so producer cheap admission also rejects pre-validator
- Coordination with sub-edit 2.1: this sub-edit ADDS missing real-intrusion synonyms; sub-edit 2.1 REMOVES/CONSTRAINS false-positive markers (`직원`, `그림자`, boardroom verbs). The two are complementary — combined they raise true-positive recall AND lower false-positive rate. Both must land in the same Tranche 2 commit so producer/validator vocabularies stay aligned.
- Source evidence: `docs/2026-04-13/stage3-producer-adversarial-followup-x3-addendum.md` §4 Finding 3 (fresh P1)
- Risk: medium — adding many synonym entries risks new FPs in legitimate prose; mitigation = require co-occurrence with at least one entry marker within ±5 sentences (same constraint as sub-edit 2.1's conflict marker rule)

Snapshot commit message: `fix: stage3 producer/validator vocabulary calibration cleanup`

Test contract for Tranche 2:
- existing `tests/test_unified_blueprint_validator_lane_c.py`: confirm `tactical_semantic_fidelity`, `scenario_density`, `temporal_deictic` cases still pass after calibration
- existing `tests/test_stage23_stage4_readiness_wave1.py`: confirm `off_arc_intrusion`, `skips_tactical_intrusion_flag`, `disguised_intrusion` cases still pass (these cover the original tactical synonym contract)
- new test cases:
  - `test_tactical_semantic_no_fp_on_pb_negotiation_with_jik_won_only`
  - `test_tactical_semantic_no_fp_on_geu_rim_ja_in_office_setting`
  - `test_tactical_semantic_still_tp_on_quae_in_with_meol_sal_co_occurrence`
  - `test_scenario_density_matches_space_separated_proper_nouns`
  - `test_temporal_deictic_passes_canonical_diegetic_anchor_from_arc_allowlist`
  - `test_temporal_deictic_still_fires_on_unanchored_year_drift`
  - `test_tactical_semantic_blocks_korean_synonym_pal_mok_bee_teul` (sub-edit 2.5)
  - `test_tactical_semantic_blocks_korean_synonym_ip_makeum_kang_yo` (sub-edit 2.5)
  - `test_tactical_semantic_blocks_korean_synonym_ju_meok_deul_i_mil` (sub-edit 2.5)
  - `test_producer_cheap_admission_blocks_korean_synonym_intrusion_mirror` (sub-edit 2.5 producer mirror)

Validation gate for Tranche 2:
- `python -m py_compile modules/domain/agents/unified_blueprint_validator.py`
- `python scripts/check_utf8_hygiene.py modules/domain/agents/unified_blueprint_validator.py config/prompts/ensemble.yaml`
- `pytest tests/test_unified_blueprint_validator_lane_c.py tests/test_blueprint_ensemble_generate_ensemble.py tests/test_stage23_stage4_readiness_wave1.py -q`
- `python scripts/ops_validator.py --strict`

Stop conditions for Tranche 2:
- if any tactical-intrusion test that simulates a real intrusion (with both entry and conflict markers in physical-threat vocabulary) regresses, stop and audit
- if scenario_density anchor count drops on a known-low candidate after the regex change, stop
- if the temporal_deictic allowlist source field does not exist on `arc_data`, stop and rescope

### 9.3 Tranche 3 — Retry Feedback Surgery

Owner: same parent SSOT plus support from existing `Stage3RepairRouter` extraction (tranche 1 of `stage3-three-tranche-safe-sequencing-plan.md`, already landed).

Goal: make attempt N+1 actually see attempt N's failure as a structured directive, not as Director's prose praise.

Sub-edit 3.1 — Add `fix_pack` / `repair_contract` channel to producer API:
- File 1: `modules/domain/agents/blueprint_ensemble.py`
- Edit: extend `BlueprintEnsembleGenerator.generate_ensemble` signature at line 584 to accept optional `fix_pack: dict | None = None` and `repair_contract: dict | None = None`; thread these into worker prompt assembly via `_build_blueprint_prompt_bundle`
- File 2: `modules/domain/agents/three_phase_blueprint_runtime.py`
- Edit: at lines 1401–1415 in `_run_phase2_generation`, forward `repair_material.effective_fix_pack` and `repair_material.repair_contract` into `ensemble_kwargs`
- Source evidence: T2.H1
- Risk: low — additive API parameters with default `None`

Sub-edit 3.2 — Replace descriptive `[이전 검증 경고]` with directive-shaped block:
- File: `modules/domain/agents/three_phase_blueprint_runtime.py`
- Edit: at lines 2155–2174 in `_apply_validation_reject_state`, restructure the stored lines to include `allowed_values=[...]` and `example=...` per validator-normalization family (opening_transition, protagonist_state, tactical_semantic_fidelity, scenario_density); vocabulary sourced from `modules/core/stage_cross_stage_contract.py`
- Source evidence: T2.H2
- Risk: medium — touches the prompt body shape; existing tests may pin exact strings

Sub-edit 3.3 — Source `prev_reject_feedback` from binding issues, not Director praise:
- File: `modules/domain/agents/three_phase_blueprint_runtime.py`
- Edit: at lines 2088 and 2124, when `reject_origin` is `pass_with_fix_unresolved` or `binding_prevalidation_reopen`, lead the feedback with the binding issue list (`validation_result["issues"]` filtered by category) instead of `validation_result["feedback"]` (Director stylistic score)
- Source evidence: T2.H3+H4
- Risk: medium — current behavior is documented in tests

Sub-edit 3.4 — Drop `[Director fix_scope]` and `[Local patch gate]` from producer-facing prompt:
- File: `modules/domain/agents/three_phase_blueprint_runtime.py`
- Edit: at lines 1120–1136 in `_build_retry_strategy_feedback`, remove the `[Director fix_scope]` and `[Local patch gate]` sections from the LLM payload; emit them only to operator telemetry via a new `_log_operator_retry_context` helper
- Source evidence: T2.H5
- Risk: low — these strings have no impact on LLM output quality (T2 finding); removal reclaims ~6 lines of prompt budget

Sub-edit 3.5 — Gate inplace patch route on non-empty `effective_fix_pack`:
- File: `modules/domain/agents/three_phase_blueprint_generator.py`
- Edit: at line 204 in `_inplace_patch_blueprint`, short-circuit and return `None` (so caller falls back to full regenerate) when `normalized_fix_pack == {}`
- Source evidence: T2.H7 (25+ degenerate inplace calls observed in ep4–ep8 with empty patch_contract)
- Risk: low — degenerate-empty case currently produces zero-value output

Sub-edit 3.6 — Symmetrise two `_inplace_patch_blueprint` call sites:
- File: `modules/domain/agents/three_phase_blueprint_runtime.py`
- Edit: at lines 1381–1388 (Phase 2 retry), prepend `_build_stage3_fix_pack_guidance(retry_state.fix_pack)` to `director_feedback` before the call, matching the `pass_with_fix` variant at lines 2354–2357
- Source evidence: T2.F7 (asymmetric instrumentation between two call sites)
- Risk: low — one-line delta

Snapshot commit message: `refactor: stage3 retry feedback directive contract`

Test contract for Tranche 3:
- existing `tests/test_blueprint_patch_mode.py`: `pass_with_fix_unresolved`, `escalates_*` cases must still pass
- existing `tests/test_blueprint_ensemble_generate_ensemble.py`: cases that mock `generate_ensemble` must accept new optional parameters
- new test cases:
  - `test_generate_ensemble_accepts_fix_pack_kwarg`
  - `test_generate_ensemble_accepts_repair_contract_kwarg`
  - `test_run_phase2_generation_forwards_fix_pack_to_ensemble`
  - `test_apply_validation_reject_state_emits_directive_block_with_allowed_values`
  - `test_prev_reject_feedback_leads_with_binding_when_origin_is_pass_with_fix_unresolved`
  - `test_retry_feedback_omits_fix_scope_and_local_patch_gate_lines`
  - `test_inplace_patch_short_circuits_on_empty_fix_pack`
  - `test_phase2_retry_inplace_call_prepends_fix_pack_guidance`

Validation gate for Tranche 3:
- `python -m py_compile modules/domain/agents/blueprint_ensemble.py modules/domain/agents/three_phase_blueprint_runtime.py modules/domain/agents/three_phase_blueprint_generator.py`
- `python scripts/check_utf8_hygiene.py <touched files>`
- `pytest tests/test_blueprint_patch_mode.py tests/test_blueprint_ensemble_generate_ensemble.py tests/test_unified_blueprint_validator_lane_c.py -q`
- `python scripts/ops_validator.py --strict`

Stop conditions for Tranche 3:
- if `BlueprintEnsembleGenerator.generate_ensemble` already has `fix_pack` parameter at the time of edit (drift), stop and audit
- if `_apply_validation_reject_state` shape changes break more than 2 existing tests, stop and audit
- if any test that pins the operator-facing log string for `[Director fix_scope]` or `[Local patch gate]` fails, decide whether to update the test or relocate the line to a different sink

### 9.4 Tranche 4 — Director Rubric Alignment + Audit Visibility

Owner: same parent SSOT.

Goal: stop Director from PASSing candidates the validator will then override; persist losing candidates and Director pre-override verdict so future audits do not require log scraping.

Sub-edit 4.1 — Director sees binding fields in candidate summary:
- File: `modules/domain/agents/director_ensemble.py`
- Edit: at lines 1993–2013, expand the candidate summary to include declared `opening_transition.type`, `protagonist_state` shape signature (e.g. `mood:set, injuries:set, equipment:list[2]`), and a binding-category advisory badge list
- Source evidence: T7.H1 (Director rubric leak — anchored)
- Risk: low — additive expansion of an existing string-builder

Sub-edit 4.2 — Add binding-contract integrity rubric axis:
- File: `modules/domain/agents/director_ensemble.py`
- Edit: at lines 2049–2070, replace the 40/35/15/10 weighted rubric (consistency / Arc / continuity / hooks) with 35/30/15/10/10 where the new 10% slot is `binding_contract_integrity` (declared opening_transition matches normalized? protagonist_state non-placeholder? scene_breakdown structural completeness?)
- Source evidence: T7.H1
- Risk: medium — changes Director selection on existing successful runs; mitigation = run regression suite covering ep1–ep7 winners and confirm Director still picks the same winner OR a candidate the validator also accepts

Sub-edit 4.3 — Persist Director's pre-override verdict:
- File: `modules/core/stage3_orchestrator.py`
- Edit: at the validator-override site, populate `stage_attempts.initial_verdict` and `director_selections.verdict` (existing schema columns) with Director's pre-override decision before `_apply_binding_prevalidation_contract` mutates it
- Source evidence: T7.H2 + T8.F1 (current values are NULL)
- Risk: low — additive write; existing readers ignore new values

Sub-edit 4.4 — Persist losing fan-out candidates as sidecar artifacts:
- File: `modules/domain/agents/blueprint_ensemble.py`
- Edit: in the fan-out finalize path (around line 557–582), write each losing candidate to `projects/<project>/logs/artifacts/stage3/ep_NNNN/attempt_NN/losing_blueprint__<strategy>.json` (or rename if a winner exists at the same path)
- Source evidence: T4.H4 + T6.H6-E (audit infrastructure)
- Risk: low — additive file writes; new sidecar pattern

Sub-edit 4.5 — Wire cheap-reject events into `ui_events.jsonl`:
- File: `modules/domain/agents/blueprint_ensemble.py`
- Edit: verify `_operator_log` calls in `_sanitize_blueprint_candidate` (lines 1411–1415, 1444–1453, 1477–1481, 1509–1511, 1524–1528, 1538–1542) actually reach `ui_events.jsonl`; if the dispatcher path is broken, wire it; if it is intact, add `component="BlueprintEnsembleGenerator"` and `attempt_key` metadata so cheap rejects become visible
- Source evidence: T4.H2 (zero `BlueprintEnsembleGenerator` records in `ui_events.jsonl` across 286 BP calls)
- Risk: low — additive operator logging

Snapshot commit message: `feat: director binding alignment + stage3 audit sidecars`

Test contract for Tranche 4:
- existing director regression tests must still pass
- existing `pass_rate_monitor` write tests must still pass
- new test cases:
  - `test_director_candidate_summary_includes_opening_transition_type`
  - `test_director_candidate_summary_includes_protagonist_state_shape`
  - `test_director_candidate_summary_includes_binding_category_badges`
  - `test_director_rubric_includes_binding_contract_integrity_axis`
  - `test_director_initial_verdict_persisted_to_stage_attempts`
  - `test_losing_fan_out_candidates_persisted_as_sidecar_files`
  - `test_cheap_reject_events_appear_in_ui_events_jsonl`

Validation gate for Tranche 4:
- `python -m py_compile modules/domain/agents/director_ensemble.py modules/domain/agents/blueprint_ensemble.py modules/core/stage3_orchestrator.py`
- `python scripts/check_utf8_hygiene.py <touched files>`
- `pytest tests/test_blueprint_ensemble_generate_ensemble.py tests/test_stage3_orchestrator_handle_success_lane_c.py -q`
- `python scripts/ops_validator.py --strict`

Stop conditions for Tranche 4:
- if `director_selections.verdict` schema differs from synthesis assumption (column missing or different type), stop and audit
- if Director regression suite picks different winners on more than 1 of 7 ep1–ep7 cases, stop and audit (rubric weight may need re-tuning)
- if losing-candidate sidecar pattern would exceed 100MB per project (artifact bloat), stop and rescope to "compressed sidecar" or "decision-only sidecar"

### 9.5 Tranche 5 — Cost Cap + Round Truncation (gated)

Owner: same parent SSOT.

**Hard prerequisite**: Tranches 1+2+3 must be live-proven via Proof Gate 2 before Tranche 5 lands. Tranche 4 is recommended but not strictly required for Tranche 5.

Goal: lower Stage3 cost ~30% by truncating provably-wasted retry rounds, without regressing verdicts.

Sub-edit 5.1 — Stop-if-no-improvement circuit breaker:
- File: `modules/domain/agents/three_phase_blueprint_runtime.py`
- Edit: in the retry loop, add: `if attempt_num >= 6 AND last_2_rounds_validator_score_delta < threshold AND same_reject_family_fired_3_consecutive_times`, exit with `PASS_WITH_WARNING` (preserving the best-so-far candidate) instead of continuing to round 10
- Source evidence: T8.H8.6 (rounds 7–10 produced 0 verdict flips on ep2/5/6/7, ~$13.5 wasted across 4 cap-hit eps)
- Risk: high if landed before Tranches 1–3 (would just truncate at lower verdict); low after Proof Gate 2

Sub-edit 5.2 — Lower default attempt cap from 10 → 7:
- Files: `modules/core/stage3_orchestrator.py`, `modules/domain/agents/three_phase_blueprint_runtime.py`
- Edit: change `max_retries` constants from 9 to 6 (so user-visible "최대 10회 시도" becomes "최대 7회 시도"); update the operator-facing string to match
- Source evidence: T8.H8.1
- Risk: medium — quality dependence on Tranche 1+2+3; mitigation = the Proof Gate 2 acceptance criterion explicitly checks that average attempt count fell below 6 already, so 7 is a safe cap

Sub-edit 5.3 — Conservative / balanced fan-out flavor decision:
- File: `modules/domain/agents/blueprint_ensemble.py`
- Edit: confirm `BLUEPRINT_STRATEGIES` at lines 47–87 ships only 3 strategies (T6.F1); remove any stale `conservative` / `balanced` references from the parent order, synthesis doc, and any code path that branches on those names
- Source evidence: T6.H6-D + T8.H8.5
- Risk: low — cleanup of stale references; no behavior change

Snapshot commit message: `perf: stage3 round cap and early-stop circuit breaker`

Test contract for Tranche 5:
- new test cases:
  - `test_stage3_circuit_breaker_exits_with_pass_with_warning_when_no_improvement_after_round_6`
  - `test_stage3_circuit_breaker_does_not_exit_when_score_is_improving`
  - `test_stage3_circuit_breaker_does_not_exit_when_reject_family_changes`
  - `test_stage3_max_retries_default_is_6`
  - `test_stage3_strategy_set_is_three_strategies_only`

Validation gate for Tranche 5:
- `python -m py_compile modules/domain/agents/three_phase_blueprint_runtime.py modules/core/stage3_orchestrator.py modules/domain/agents/blueprint_ensemble.py`
- `python scripts/check_utf8_hygiene.py <touched files>`
- `pytest tests/test_blueprint_patch_mode.py tests/test_stage3_orchestrator_handle_success_lane_c.py tests/test_blueprint_ensemble_generate_ensemble.py -q`
- `python scripts/ops_validator.py --strict`

Stop conditions for Tranche 5:
- if Proof Gate 2 has not been declared PASS, do not start Tranche 5
- if circuit-breaker thresholds would have triggered on a known-good ep1 / ep3 attempt 6, stop and tune
- if reducing `max_retries` would break any test that asserts attempt_num == 10, update the test as part of the same commit

Proof Gate 3 acceptance criteria:
- ep1–ep8 fresh rerun on `000_260412_a` after Tranche 5 lands
- average Stage3 attempt count must remain below 6 (no regression)
- total Stage3 cost must drop by ≥ 20% vs the pre-Tranche-5 baseline
- no episode may regress from PASS to PASS_WITH_WARNING or from PASS_WITH_WARNING to REJECT

## 10. Test Contract Summary

All new tests live under `tests/` next to existing related test files. Existing test file extensions are preferred over new files unless complexity guardrails (≥120 LOC test file or ≥50 direct test methods) would be breached.

| Tranche | Existing tests touched | New test cases |
|---------|------------------------|---------------|
| 1 | `test_unified_blueprint_validator_lane_c.py`, `test_blueprint_ensemble_generate_ensemble.py`, `test_blueprint_patch_mode.py`, `test_stage23_stage4_readiness_wave1.py` | 8 |
| 2 | `test_unified_blueprint_validator_lane_c.py`, `test_blueprint_ensemble_generate_ensemble.py`, `test_stage23_stage4_readiness_wave1.py` | 10 |
| 3 | `test_blueprint_patch_mode.py`, `test_blueprint_ensemble_generate_ensemble.py`, `test_unified_blueprint_validator_lane_c.py` | 8 |
| 4 | `test_blueprint_ensemble_generate_ensemble.py`, `test_stage3_orchestrator_handle_success_lane_c.py` | 7 |
| 5 | `test_blueprint_patch_mode.py`, `test_stage3_orchestrator_handle_success_lane_c.py`, `test_blueprint_ensemble_generate_ensemble.py` | 5 |

Total new test cases: 38. All new tests must use the existing memory-conservative shard pattern (one test file per shard; no parallel xdist unless operator explicitly authorizes).

## 11. Validation Gates

### 11.1 Per-tranche static gates

Per tranche, before commit:

- `python -m py_compile <touched files>`
- `python scripts/check_utf8_hygiene.py <touched files>`
- targeted `pytest <touched test files> -q`
- `python scripts/ops_validator.py --strict`

### 11.2 Proof Gates (live rerun)

All live proof gates below are subordinate to today's Stage3 rerun gate in `docs/2026-04-14/stage3-debt-remediation-bounded-survey-and-rerun-gate.md`:

- no proof gate may run unless a canonical current-head bounded survey records `>=90%` predictive contract-debt resolution
- even after that floor is met, no proof gate is automatic; each live rerun still requires explicit operator re-authorization

Proof Gate 1 — after Tranche 1:

- execution precondition: the parent `0_0-stage3-contract-tightening-remediation` lane must first close or explicitly demote the bounded tactical-authority synonym parity tranche; until then this gate is deferred and not the front controller
- fresh `000_260412_a` ep1–ep8 rerun
- ep8 closes (no interruption)
- average attempt count drops from 8.4 to < 6
- opening_transition reject family fires ≤ 1 across the rerun

Proof Gate 2 — after Tranches 2+3+4:

- fresh `000_260412_a` ep1–ep8 rerun
- average attempt count remains < 6
- tactical_semantic / scenario_density / temporal_deictic FP rates drop to ≤ 0 each in the new run
- Director rubric leak rate (Director PASS → validator REJECT) drops to ≤ 1 per session
- losing-candidate sidecars exist for each ep
- cheap-reject events appear in `ui_events.jsonl`

Proof Gate 3 — after Tranche 5:

- fresh `000_260412_a` ep1–ep8 rerun
- average attempt count remains < 6
- total Stage3 cost ≤ 80% of pre-Tranche-5 baseline
- no verdict regressions

### 11.3 Closure conditions

This SSOT closes when:

- all 5 tranches are landed with snapshot commits
- all 3 Proof Gates pass
- new test cases (34 total) are committed and green
- the parent `0_0-stage3-contract-tightening-remediation` SSOT and `active-temp-execution-roadmap.md` are updated to reflect closure
- the temp mirror at `docs/temp/0_0-stage3-quality-closure-five-tranche-remediation-execution-ssot.md` is removed

## 12. Snapshot Commit Discipline

Per `docs/2026-04-13/stage3-three-tranche-safe-sequencing-plan.md` operating rules:

1. Each tranche produces exactly one snapshot commit
2. Commit content stays tranche-scoped (code + tests + this SSOT update)
3. Live-run artifacts, DB files, logs, unrelated planning drafts must NOT be bundled into the tranche commit
4. If unrelated dirt is present in the worktree, commit only tranche-owned files via explicit `git add <path>` per file
5. Never use `git add -A` or `git add .`
6. Never amend an earlier tranche commit; if a fix is needed, create a NEW commit
7. Commit messages follow the workspace's Korean-friendly convention; the recommended messages are:
   - Tranche 1: `fix: stage3 opening-transition vocabulary coherence`
   - Tranche 2: `fix: stage3 producer/validator vocabulary calibration cleanup`
   - Tranche 3: `refactor: stage3 retry feedback directive contract`
   - Tranche 4: `feat: director binding alignment + stage3 audit sidecars`
   - Tranche 5: `perf: stage3 round cap and early-stop circuit breaker`

## 13. Stop Conditions (cross-tranche)

Stop the entire SSOT execution and re-survey if:

- any tranche breaks more than 1 unrelated existing test
- any tranche increases the average attempt count instead of decreasing it
- any tranche causes the workspace to drift more than 100 lines from baseline `32d6f0c8` outside the tranche-owned files
- live grep finds line anchors have drifted by more than 20 lines from this SSOT's claims (re-anchor by function name, do not blindly trust line numbers)
- a Proof Gate fails 2 attempts in a row (root-cause investigation required)
- the operator interrupts mid-tranche and the worktree state cannot be cleanly resumed

## 14. Reverification Gates

Before edit:

- re-`git rev-parse HEAD` and `git status --short` — record drift if any
- re-grep all cited line anchors in this SSOT against current head (function names are stable; line numbers may drift)
- if more than 2 anchors have drifted, re-audit the tranche scope before editing

Before commit:

- run the per-tranche static gates above
- diff against `32d6f0c8` to confirm the change set matches the tranche scope (no unrelated edits)

After commit:

- `git log --oneline -5` to confirm the commit hash
- update the parent `0_0-stage3-contract-tightening-remediation-execution-ssot.md` Status field with the landed tranche (one-line update)
- update `active-temp-execution-roadmap.md` with the landed tranche

## 15. Non-Goals

(Inherited from `s2-s3-s4-runtime-improvement-synthesis.md` §6.)

This SSOT does not authorize:

- Stage4 chief writer code edits (T10 deferred)
- Stage2 arc generation retuning
- DecisionKernel / Polaris migration
- model swap, tier change, vendor cost negotiation
- new genre support
- DB schema migration
- broad Stage3 prompt rewrite outside Tranches 1+2 sub-edits
- live rerun before per-tranche static gates pass
- single-candidate fail-closed (TF-36 reopens)
- ep2 crashed-session resilience (separate session-resilience track)
- Tier 3 / Tier 4 dead-code paths (deferred with T10)
- conservative / balanced fan-out flavor activation (only stale-reference cleanup is in scope)
- broader Director comparator rewrite

## 16. Risk Register

(Inherited from `s2-s3-s4-runtime-improvement-synthesis.md` §7 with synthesis-time corrections; severity reflects post-correction state.)

| Risk | Tranche | Severity | Mitigation |
|------|---------|----------|------------|
| Removing `→` and `진입` from marker lists could let a real explicit_transition slip through | 1 | medium | T5 100% FP evidence; absolute markers (`다음 날`, `* * *`, `한편`) remain |
| Splitting declared-vs-inferred in cheap admission spikes attempt-1 rejects until prompt edit lands | 1 | low | sub-edits 1.1+1.2+1.3+1.4+1.5 land in one commit |
| Changing `extract_episode_tactical` default behavior breaks 13 production callsites | 1 | high | parameter-flag pattern, default `False`, only Stage3 producer-input flips to `True` |
| Loosening tactical-intrusion markers lets real intrusion slip through | 2 | medium | co-occurrence requirement on entry+conflict markers within ±5 sentences in same scene |
| Director rubric reweighting changes Director selection on existing successful runs | 4 | medium | regression suite covers ep1–ep7 winners; gate landing on ≤ 1 winner change |
| Round cap truncation regresses quality if landed before T1–T3 | 5 | high | hard prerequisite Proof Gate 2; do not start T5 without it |
| Schema migration for `initial_verdict` / `losing_blueprint__*.json` breaks audit replay | 4 | low | additive only; existing readers ignore new fields |
| 10→7 attempt cap misses a legitimate late-recovery attempt | 5 | medium | data shows zero flips in rounds 7–10 on captured run, but sample is 7 episodes; expand to ≥ 30 episodes before final hardening |
| All five tranches land in one sprint and proof rerun cannot isolate which tranche delivered which lift | sequencing | medium | hard sequencing gate after Tranche 1; Proof Gate 2 isolates Tranches 2/3/4 contribution |
| Director regression suite covering ep1–ep7 winners does not exist yet | 4 | medium | construct it as part of Tranche 4 prep work, before Tranche 4 sub-edit 4.2 lands |
| `losing_blueprint__*.json` sidecars exceed disk quota for long projects | 4 | low | per-project artifact size monitoring; if ≥ 100 MB per project, switch to compressed sidecars in a follow-up |
| Concurrent worktree edits (operator + Claude) collide | sequencing | low | each tranche acquires its file set via `git status` check before starting |

## 17. 3-Pass Audit Record

### Pass 1. Structure and scope

- this SSOT carries the same shape as the existing `0_0-stage3-*-remediation-execution-ssot.md` family (sections 1–17, Source Survey Docs / Evidence Artifacts lists, Side-Effect Coverage statement, per-tranche detailed spec)
- scope is bounded to the 5 tranches the synthesis ranked; no scope creep into T10 / Polaris / Director rewrite
- non-goals (§15) and risk register (§16) inherited verbatim from synthesis with synthesis-time corrections applied
- per-tranche stop conditions (§9) and cross-tranche stop conditions (§13) are explicit
- snapshot commit discipline (§12) follows the existing `stage3-three-tranche-safe-sequencing-plan.md` rules
- closure conditions (§11.3) are explicit, tied to Proof Gates and parent SSOT update

### Pass 2. Evidence and consistency

- every cited line anchor in this SSOT was either live-grep verified during synthesis (§9 sub-edits 1.1, 1.2, 1.4, 1.5, 2.1, 2.2 marker lists) or explicitly marked with the function-name-stable rule (every other anchor)
- the `extract_episode_tactical` 13-callsite blast radius correction from synthesis-time live grep is preserved in §9 sub-edit 1.3 with explicit caller list
- Proof Gates are quantitative (avg attempt count, FP rates, cost percentage) not qualitative
- the parent lane (`0_0-stage3-contract-tightening-remediation`) is named as parent owner in §1 and §9.1, no new queue family is opened
- the closure conditions (§11.3) explicitly require the temp mirror to be removed after closure, matching workspace operating rules

### Pass 3. Execution and readability

- the realization architecture diagram (§7) and tranche sequence (§8) make the prerequisite chain (Tranche 5 cannot precede Proof Gate 2) impossible to misread
- per-tranche specs (§9.1–§9.5) all follow the same shape (Owner / Goal / Sub-edits with file:line / Snapshot commit / Test contract / Validation gate / Stop conditions / Proof Gate criteria where applicable) so an executor can move tranche-by-tranche without re-deriving the structure
- the 34 new test cases are listed by name so the executor knows what to write, not just "add tests"
- the test contract summary table (§10) gives a single-glance picture of test scope per tranche
- snapshot commit messages are pre-written so commit discipline is mechanical
- the document is realization-ready: an executor can start Tranche 1 by reading §9.1 alone

## 18. Final Confidence

`97%` after the 3-pass audit above. Residual 3% uncertainty:

- the precise `_BINDING_PREVALIDATION_REGENERATE_CATEGORIES` whitelist semantics for opening_transition alias-only case (sub-edit 1.5) need code-level verification at edit time; the SSOT specifies the intent but the exact set membership may need 1-line fine-tuning
- Director regression suite covering ep1–ep7 winners (Tranche 4 prerequisite) does not yet exist as a committed test; constructing it is part of Tranche 4 prep work
- the 30 new test cases are specified by name and intent but not body; the executor must write them within the existing memory-conservative test pattern

These three items are explicit, bounded, and addressable inside the tranche they belong to. None of them blocks the SSOT structure or the realization order.

## 19. 2026-04-19 Reactivation Refresh

Source doc:

- `docs/2026-04-19/stage3-quality-closure-five-tranche-reactivation-refresh.md`

Current reading:

- the lane had stayed mirrored because it still looked like the top parked Stage3 continuation plan after the rerun-gate floor was crossed
- the later board state is narrower:
  - the parent contract-tightening lane is closed
  - the sibling state-arbiter lane is closed
  - rerun remains operator-gated and unconsumed
  - deferred `T4.2~T5` work is still proof-contingent

Queue consequence:

- the old parked/operator-gated wording is now stale as an active queue signal
- the next honest move is closure-review, not continued queue mirroring

## 20. 2026-04-19 Closure Review

Source doc:

- `docs/2026-04-19/stage3-quality-closure-five-tranche-closure-review.md`

Closure judgment:

- bounded Stage3 quality-closure planning is now satisfied for queue-governing purposes
- landed `T1~T3` plus bounded `T4.1` remain canonical historical backing
- deferred `T4.2~T5` remains visible only as contingent proof backlog, not active queue debt

Queue move:

- close this lane
- remove the temp mirror during this tranche
- let `0_0-stage4-interview-round-owner-surface-reduction-remediation` become the next visible parked candidate
