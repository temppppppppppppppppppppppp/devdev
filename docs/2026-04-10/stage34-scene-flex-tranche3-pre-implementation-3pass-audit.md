# Stage34 Scene-Flex Tranche 3 Pre-Implementation 3-Pass Audit

Date: 2026-04-10
Audit Type: current-head pre-implementation re-audit
Scope: `Tranche 3. Overflow / Completeness Heuristic Normalization`
HEAD: `d76c5f56b78982d23706895190c7735b2472f9a4`
Source SSOT: `docs/2026-04-09/0_0-stage34-scene-flex-contract-normalization-remediation-execution-ssot.md`
Supporting Docs:
- `docs/2026-04-09/scene-flex-current-context-handoff.md`
- `docs/2026-04-09/stage34-scene-flex-tranche2-implementation-3pass-audit.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
Commit State:
- Baseline Commit: `d76c5f56b78982d23706895190c7735b2472f9a4`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Verdict

Current-head pre-implementation audit says `Tranche 3` is implementation-ready under the explicit operator reactivation, but the live owner map is slightly different from the earlier parked note.

Direct current-head severity read:

- `P2`: active Python reject / regenerate heuristics still penalize dense low-scene manuscripts through fixed `scene_count`-derived overflow and reflection formulas
- `P3`: active warning / advisory surfaces still echo the same rigid slot-thinking in Stage4 candidate review
- `P4`: dormant or secondary prompt / dashboard / template surfaces still carry stale `scene_coverage` or `4-6 scenes` language, but they are not the first bounded implementation target

Current recommendation:

- start with a bounded `Wave A` on the active runtime heuristics that actually influence reject / regenerate / warning flow
- treat `director_continuity` as a conditional `Wave B` inside the same tranche only if the first wave stays bounded
- keep dormant prompt / dashboard cleanup out of the first implementation pass unless new evidence proves they are live

No direct `Tranche 2` blocker remains.

## 2. Current-Head Owner Map

### A. Primary Must-Fix Surfaces

- `modules/validation/blocking_validator_scene_checks.py::_check_scope_overflow`
  - current logic still uses `scene_count * 1500` as the dominant manuscript overflow budget
  - this is a real blocking path: `modules/validation/blocking_validator.py` calls it in manuscript mode and appends failures when it returns `passed=False`
- `modules/core/cross_agent_verifier.py::_python_precheck_writer`
  - current logic still computes:
    - `reflection_rate = reflected_count / scene_count`
    - `max_expected_length = len(scene_breakdown) * 1500 * 1.5`
  - this is a real regeneration pressure path: `verify_writer_compliance()` uses the Python precheck first, and `modules/core/stage4_director_runtime.py` appends `[CrossVerify:VIOLATION]` warnings to candidate validation results when this path fires

### B. Active Adjacent Warning Surfaces

- `modules/core/pre_director_checklist.py::_check_manuscript_blueprint_alignment`
  - current logic still emits scene-alignment warnings from `overall_ratio < 0.3` and `overall_ratio < 0.5`
- `modules/core/pre_director_checklist.py::_check_manuscript_scope`
  - current logic still warns from `scene_count * 1500 * 1.4`
  - this is active in Stage4: `modules/core/stage4_director_runtime.py` appends `[PreCheck]` warnings and UI log output from `PreDirectorChecklist.check(...)`
- `modules/core/confidence_calibration.py::_score_manuscript_scene_coverage`
  - current logic still scores manuscript confidence with keyword-match ratio buckets `0 / 5 / 10 / 15`
  - this is also active in Stage4: `modules/core/stage4_director_runtime.py` appends `[Confidence:*]` warning strings from `confidence_calibrator.assess(...)`
- `modules/domain/agents/director_continuity.py::_validate_blueprint_completeness_v60`
  - current logic still fails below `65%` scene coverage and warns below `75%`
  - this is a real active surface through `DirectorContinuityValidator`; it is the strongest candidate for a bounded `Wave B` if `Wave A` lands cleanly

### C. Dormant, Secondary, or Separate-Family Surfaces

- `modules/core/quality_amplifier.py::generate_architect_constraints`
  - still says `씬 개수는 4-6개로 제한`
  - repo search found no active production call site for this architect-facing method on current HEAD
- `modules/core/writer_template.py::validate_against_template`
  - still reports `scene_coverage` from keyword-count misses
  - repo search found no active production call site outside tests on current HEAD
- `modules/core/quality_dashboard.py::predict_pass_probability`
  - still applies `씬 반영 부족 / 경계 / 우수` weights from `scene_coverage`
  - current-head repo search found no external production call site outside its own local warning helper
  - this function is already `150 LOC`, so it should not be pulled into `Wave A` casually
- `modules/domain/agents/unified_blueprint_validator.py`
  - `avg_chars_per_scene` remains a Stage3 blueprint-density heuristic
  - this is the same broad family, but it is not the same manuscript-side owner as the live Tranche 3 runtime pressure lane
- `modules/domain/agents/manuscript_validator.py::_check_scene_coverage`
  - current implementation is intentionally disabled and always returns `100`
  - it is not a blocking owner for this tranche

## 3. Runtime Consequence Split

The live runtime split on current HEAD is:

- hard / semi-hard pressure:
  - `BlockingValidator` failure
  - `CrossAgentVerifier` violation and regeneration pressure
- active warning pressure:
  - `PreDirectorChecklist`
  - `ConfidenceCalibrator`
- later-stage or secondary pressure:
  - `DirectorContinuityValidator`
  - dormant prompt / dashboard / template surfaces

This means the earlier 2026-04-09 parked note was directionally correct about the heuristic family, but not fully current about which surfaces are active enough to deserve first-wave implementation.

## 4. Recommended Tranche Boundary

### Wave A. Immediate Bounded Implementation

Keep the first implementation pass to these four files:

- `modules/validation/blocking_validator_scene_checks.py`
- `modules/core/cross_agent_verifier.py`
- `modules/core/pre_director_checklist.py`
- `modules/core/confidence_calibration.py`

Reason:

- these surfaces are active on current HEAD
- they directly drive manuscript reject / regenerate / warning pressure
- they are small enough to keep the tranche bounded

### Wave B. Conditional Same-Tranche Follow-Up

Add only if `Wave A` lands cleanly and the lane still stays bounded:

- `modules/domain/agents/director_continuity.py`

Reason:

- it is active and real
- but it is downstream enough that it can be separated if the first wave already absorbs the main pressure

### Explicitly Parked For Now

- `modules/core/quality_amplifier.py`
- `modules/core/writer_template.py`
- `modules/core/quality_dashboard.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/manuscript_validator.py`

Reason:

- these are dormant, secondary, or separate-family surfaces on current HEAD
- pulling them into the first patch risks inflating the lane from heuristic normalization into broad prompt / dashboard cleanup

## 5. Test State and Gaps

Current baseline verification executed during this audit:

- `python -m pytest tests/test_blocking_validator_submodules.py -k "scope_overflow_smoke" -q`
  - `1 passed`
- `python -m pytest tests/test_pre_director_checklist_wave3.py -q`
  - `4 passed`
- `python -m pytest tests/test_confidence_calibration_lane.py -q`
  - `5 passed`
- `python -m pytest tests/test_scene_cardinality_contract.py tests/test_unified_blueprint_validator_lane_c.py -k "two_scene" -q`
  - `2 passed`
- `python -m pytest tests/test_director_continuity_blueprint_v60.py -q`
  - `6 passed`

Current protection gaps:

- no targeted regression currently proves `_check_scope_overflow()` accepts dense `2-scene` or `3-scene` manuscripts when obligation density is sufficient
- no targeted regression currently proves `_python_precheck_writer()` avoids false `씬 반영 부족` on dense low-scene manuscripts
- no targeted regression currently proves `PreDirectorChecklist` warning thresholds stop punishing low scene count by itself
- no targeted regression currently proves `ConfidenceCalibrator` stops down-scoring manuscripts simply because fewer scenes carry more dwell time
- `DirectorContinuityValidator` has coverage tests, but not a current-head regression that explicitly protects dense `2-scene` / `3-scene` manuscripts for this lane
- the dormant prompt / dashboard / template surfaces have smoke or definition coverage, not meaningful runtime-wiring coverage

Important current-head nuance:

- `tests/test_pre_director_checklist_wave3.py` already encodes the current one-scene overflow warning behavior
- that does not block the planned Tranche 3 work by itself, because the intended contract is still compatible with rejecting or warning on truly collapsed one-scene manuscripts
- the missing tests are the dense `2-scene`, dense `3-scene`, and stable `5-scene` protections

## 6. Side-Effect Coverage

- file writes: not-applicable for the inspected heuristic functions
- DB / transaction: not-applicable
- JSONL / logs / audit sinks: not-applicable inside the inspected functions themselves
- console / UI: covered
  - `stage4_director_runtime` appends warning strings for `PreCheck`, `Confidence`, and `CrossVerify`, and emits one UI log line for `PreDirectorChecklist`
- recovery / retry: covered
  - `BlockingValidator` contributes direct failures
  - `CrossAgentVerifier` can trigger regeneration pressure through violation count
- cache / global state: partial
  - `QualityDashboard` reads in-memory history, but the inspected prediction path does not write state
- bootstrap / config-env: covered
  - `_threshold("scope.chars_per_scene", 1500)` remains a config-shaped boundary
  - stale default constraint text in `quality_amplifier` is a bootstrap-adjacent secondary surface
- external interfaces: not-applicable for the inspected Python heuristic functions in this tranche

## 7. Complexity Guardrail Notes

Current function sizes relevant to the next patch:

- `modules/validation/blocking_validator_scene_checks.py::_check_scope_overflow` = `75 LOC`
- `modules/core/cross_agent_verifier.py::_python_precheck_writer` = `62 LOC`
- `modules/core/pre_director_checklist.py::_check_manuscript_blueprint_alignment` = `116 LOC`
- `modules/core/pre_director_checklist.py::_check_manuscript_scope` = `22 LOC`
- `modules/core/confidence_calibration.py::_score_manuscript_scene_coverage` = `20 LOC`
- `modules/domain/agents/director_continuity.py::_validate_blueprint_completeness_v60` = `56 LOC`
- `modules/core/writer_template.py::validate_against_template` = `58 LOC`
- `modules/core/quality_dashboard.py::predict_pass_probability` = `150 LOC`

Implementation implication:

- do not casually widen `predict_pass_probability`; keep it parked unless the lane explicitly expands
- if `pre_director_checklist._check_manuscript_blueprint_alignment` is touched, keep the patch bounded and be ready to split helper logic if it starts drifting into the `120+ LOC` pressure band

## 8. Implementation Start Recommendation

When implementation starts from this audit, use this order:

1. normalize `BlockingValidator` overflow logic away from rigid `scene_count * fixed chars_per_scene`
2. normalize `CrossAgentVerifier` writer precheck away from naive `reflected_count / scene_count` and fixed per-scene length budgeting
3. align `PreDirectorChecklist` warning heuristics with the new obligation-first rule
4. align `ConfidenceCalibrator` manuscript scene-coverage scoring with the same rule
5. decide whether `DirectorContinuityValidator` must join the same patch or stay as a bounded follow-up

Target new regressions:

- dense `2-scene` manuscript with high obligation materialization should avoid false overflow / false missing-scene warnings
- dense `3-scene` manuscript should remain viable through the active Python precheck lane
- stable `5-scene` manuscript should continue to pass without new regressions
- one-scene collapse should still remain reject / warning territory where the existing contract requires it

## 9. 3-Pass Audit Record

Pass 1. Structure and scope:

- kept the audit bounded to the explicit `Tranche 3 pre-implementation` ask
- separated active runtime owners from dormant or separate-family surfaces
- kept roadmap / queue discussion descriptive only, without widening into implementation

Pass 2. Evidence and consistency:

- revalidated the 2026-04-09 SSOT / handoff / tranche-2 audit against the live `main` HEAD
- checked direct code paths and current production call-site visibility with repo search rather than relying only on the older parked note
- confirmed the baseline workspace is clean and the current HEAD already contains the scene-flex tranche-1/2 checkpoint

Pass 3. Execution and readability:

- converted the owner inventory into an implementation order the next patch can actually follow
- made the first-wave / second-wave boundary explicit
- attached concrete baseline test evidence and named the missing regressions required for safe implementation

Confidence: `97%`
