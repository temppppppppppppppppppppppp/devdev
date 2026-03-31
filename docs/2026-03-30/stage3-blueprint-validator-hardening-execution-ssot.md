# Stage 3 Blueprint Validator Hardening - Execution SSOT

Date: 2026-03-30
Status: closed
Canonical Path: `docs/2026-03-30/stage3-blueprint-validator-hardening-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage3-blueprint-validator-hardening-execution-ssot.md`
Baseline Commit: `9ad4efcc`
Baseline Dirty Summary:
- `projects/0_1/project_data.db` modified
- `projects/0_1/plans/blueprints/blueprint_0008.txt` modified
- `projects/0_1/plans/blueprints/blueprint_0015.txt` modified
- `projects/0_1/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json` modified
- `projects/0_1/logs/artifacts/stage3/ep_0015/attempt_01/final_blueprint__action_focused.json` modified
- `projects/0_1/logs/session/decisions.jsonl` modified
- `projects/0_1/logs/session/ui_events.jsonl` modified
- `projects/0_1/logs/session/llm_io.jsonl` modified
- `projects/0_1/logs/quality_metrics.jsonl` modified
- `projects/0_1/plans/blueprints/blueprint_0016.txt` untracked
- `projects/0_1/logs/artifacts/stage3/ep_0016/` untracked
Source Survey Docs:
- `docs/2026-03-30/stage3-blueprint-p1-root-cause-bounded-survey.md`
- `docs/2026-03-30/0_1-stage3-blueprint-integrity-bounded-survey.md`
Evidence Artifacts:
- `projects/0_1/plans/blueprints/blueprint_0008.txt`
- `projects/0_1/plans/blueprints/blueprint_0015.txt`
- `projects/0_1/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json`
- `projects/0_1/logs/artifacts/stage3/ep_0015/attempt_01/final_blueprint__action_focused.json`
- `projects/0_1/logs/session/decisions.jsonl`
- `modules/domain/agents/unified_blueprint_validator.py`
Supplemental Checks Added During Execution Rewrite:
- verified that Python findings become compact warnings plus `quality_risk`, not binding verdict gates
- verified that Director receives those warnings via `focus_header`
- verified that `final_verdict` still mirrors Director output in the single-candidate path
- verified that compare mode also preserves Python findings as metadata only
- verified that `PASS_WITH_FIX` already routes into an existing repair loop in Stage 3 runtime

## 1. Bug Statement

Stage 3 allowed structurally incomplete blueprints to pass because two layers were simultaneously weak:

1. Missing Python invariants:
   - EP8 had empty `scene_breakdown.scene_N.characters` arrays.
   - EP15 had timeline drift between blueprint state and arc timeline.
2. Advisory-only contract:
   - Python prevalidation findings were surfaced to Director, but they did not block a plain `PASS`.

This SSOT replaces the prior "validator-only hardening" plan with a narrower and more correct plan:

- Tranche 1A: add explicit invariants for `scene.characters` and arc timeline alignment.
- Tranche 1B: make those specific invariants binding so a plain `PASS` cannot survive them unchanged.

The local EP8/EP15 artifact repairs already landed in `0_1`. This SSOT is for future Stage 3 runs.

## 2. Authoritative Validation Contract

Current Stage 3 contract in `unified_blueprint_validator.py`:

1. `_python_pre_validate()` collects issues.
2. `_build_python_warning_entries()` converts those issues into compact warnings and a boolean `quality_risk`.
3. Director receives those warnings through a `focus_header`.
4. Final verdict remains Director-owned unless Director itself chooses `PASS_WITH_FIX` or `REJECT`.

Observed code facts:

- Python findings become warnings plus metadata:
  - `python_warnings` and `quality_risk` are attached at lines 248-264.
  - `_build_python_warning_entries()` returns `entries, bool(entries)` at lines 119-151.
- Critical findings are still deferred to Director:
  - lines 401-402 log that critical Python findings are deferred.
- Director does see bounded structured warnings:
  - `focus_header` is built at lines 470-476.
- Single-candidate final verdict is still Director-owned:
  - `final_verdict = director_verdict` at line 522.
- Compare mode behaves the same way:
  - `quality_risk` is assembled from candidate advisories at lines 328-330.
  - result verdict is still the compare decision at lines 338-361.

Operational conclusion:

- The survey root cause was directionally correct.
- The prior execution SSOT was incomplete because it assumed "new invariants" alone would close the hole.
- Actual closure requires both issue generation and a binding verdict contract for selected categories.

## 3. Why The Previous Execution Shape Was Insufficient

The previous execution draft overestimated what validator-only changes could achieve.

Why it was insufficient:

1. Adding `_collect_*_issues()` alone only creates more warnings.
2. Those warnings already reach Director, so the problem is not total Director blindness.
3. If Director still returns `PASS`, the current pipeline keeps that `PASS`.
4. Therefore V-1 and V-2 can recur even after invariant collectors are added.

Correction:

- The right seam is not "validator-only."
- The right seam is "validator hardening plus binding escalation for selected invariant families."

## 4. Tranche Structure

### Tranche 1A - Add missing invariants

Scope:
- V-1: `scene_breakdown.scene_N.characters` completeness
- V-2: blueprint `ending_state.timeline` vs arc `state_changes.timeline`

### Tranche 1B - Bind selected invariants to verdict handling

Scope:
- Prevent plain `PASS` when Tranche 1A issues are present in the selected blueprint.
- Use existing `PASS_WITH_FIX` repair flow rather than immediate hard `REJECT`.

### Tranche 2 - Deferred cross-field consistency

Scope:
- V-3: `integrated_scenario` vs `scene.content` cross-field drift

Reason for deferral:
- Higher false-positive risk
- Requires semantic matching across fields rather than simple structured completeness checks
- Better treated as advisory/minor in a later wave

## 5. Recommended Repair Contract

### 5.1 V-1 scene characters completeness

New collector:
- `_collect_scene_characters_issues()`

Behavior:
- Inspect each scene's `characters`.
- Treat empty list or blank string as missing.
- Escalate to `MAJOR` when the defect is systemic.

Recommended threshold:
- `MAJOR` if 2 or more scenes are empty
- optional `MINOR` if exactly 1 scene is empty and scene content still implies active participants

Reasoning:
- EP8 was 4/4 empty.
- A single intentionally sparse side-glimpse should not auto-fail the episode.

Suggested category:
- `scene_completeness`

### 5.2 V-2 arc timeline alignment

New collector:
- `_collect_arc_timeline_alignment_issues()`

Behavior:
- Read arc timeline from `arc_data.state_changes.timeline`.
- Read blueprint ending timeline from `blueprint.ending_state.timeline`.
- Parse best-effort year/month markers from the blueprint expression.
- Flag `MAJOR` drift when the blueprint is materially out of arc range.

Recommended threshold:
- `MAJOR` when drift is 2 or more months against arc intent
- otherwise skip or stay advisory if parsing confidence is weak

Suggested category:
- `arc_timeline`

### 5.3 Binding contract for Tranche 1

New same-file helper:
- `_apply_binding_prevalidation_contract()` or equivalent

Binding set for Tranche 1:
- `scene_completeness`
- `arc_timeline`

Required behavior:

1. Single-candidate path:
   - if Director returns `PASS` and selected prevalidation contains a Tranche 1 binding issue, coerce final verdict to `PASS_WITH_FIX`
   - preserve Director score
   - append Python finding summary into feedback and verdict reason

2. Compare path:
   - inspect `selected_pre_result`
   - if compare result returns `PASS` and selected prevalidation contains a Tranche 1 binding issue, coerce result verdict to `PASS_WITH_FIX`
   - preserve candidate selection and score

3. Preserve stronger existing outcomes:
   - if Director already returns `PASS_WITH_FIX`, keep it
   - if Director returns `REJECT`, keep it

4. Do not globally turn `quality_risk` into a hard gate:
   - bind only explicit categories in the Tranche 1 set
   - avoid broad false-positive regressions

Why `PASS_WITH_FIX` is the right target:

- `three_phase_blueprint_runtime.py` already has a repair loop for `PASS_WITH_FIX` at lines 1341-1360.
- This keeps the change bounded to Stage 3 validator semantics.
- It avoids a wider policy change such as making all Python warnings reject-worthy.

## 6. Lowest-Risk Touched Surface

Production file:
- `modules/domain/agents/unified_blueprint_validator.py`

Test file:
- `tests/test_unified_blueprint_validator_lane_c.py`

Why this remains lowest risk:

- Both invariant creation and binding escalation can be implemented inside the same validator owner.
- No DB schema changes.
- No generator prompt changes.
- No runtime orchestration rewrite.
- No Stage 4 changes.

Expected production change shape:
- add 2 new collectors
- add 1 binding helper
- wire collectors into `_python_pre_validate()`
- wire binding helper into:
  - `_run_compare_validation()`
  - `_build_director_validation_result()`

## 7. Validation Matrix

### Unit and focused regression

1. V-1 positive case:
   - replay EP8-style scene payload with 4 empty `characters`
   - expect `scene_completeness` issue

2. V-1 negative case:
   - replay a known clean blueprint such as EP2 or EP9
   - expect no `scene_completeness` issue

3. V-2 positive case:
   - replay EP15-style blueprint ending timeline against Arc 4 timeline
   - expect `arc_timeline` issue

4. V-2 negative case:
   - replay a known clean timeline-aligned blueprint
   - expect no `arc_timeline` issue

5. Binding positive case, single-candidate:
   - Director mock returns `PASS`
   - prevalidation includes `scene_completeness` or `arc_timeline`
   - expect final verdict `PASS_WITH_FIX`

6. Binding positive case, compare path:
   - compare result returns `PASS`
   - selected candidate has binding issue
   - expect returned verdict `PASS_WITH_FIX`

7. Binding preservation:
   - Director `REJECT` stays `REJECT`
   - Director `PASS_WITH_FIX` stays `PASS_WITH_FIX`

8. Non-binding preservation:
   - V-3 or generic advisory does not force `PASS_WITH_FIX` in Tranche 1

### Tooling validation

- targeted `pytest` for `tests/test_unified_blueprint_validator_lane_c.py`
- `ruff check` on touched files
- `python -m py_compile` on touched production file
- `python scripts/check_utf8_hygiene.py` on canonical and temp execution docs plus touched code/tests

## 8. Closure Criteria

This execution lane is closed only when all of the following are true:

1. V-1 collector exists and is exercised by tests.
2. V-2 collector exists and is exercised by tests.
3. Plain `PASS` is no longer allowed when selected prevalidation contains Tranche 1 binding issues.
4. Compare path and single-candidate path both honor that contract.
5. Known clean fixtures do not regress into false positives for Tranche 1.
6. Existing `PASS_WITH_FIX` repair flow still works without runtime contract breakage.

## 9. Non-Goals

- No generator prompt rewrite in this tranche
- No Director prompt rewrite in this tranche
- No conversion of all `quality_risk` findings into rejection-worthy blockers
- No Tranche 2 V-3 binding in this tranche
- No blueprint regeneration lane as part of this fix
- No Stage 4 changes

## 10. Implementation Order

1. Add V-1 collector
2. Add V-2 collector
3. Wire both into `_python_pre_validate()`
4. Add binding helper for Tranche 1 categories
5. Apply binding helper in compare path
6. Apply binding helper in single-candidate final verdict path
7. Add focused tests
8. Run targeted validation

## 11. 3-Pass Audit Record

Pass 1 - structure and scope
- corrected the doc type from "validator-only hardening" to "validator plus binding contract"
- kept scope bounded to Stage 3 validator behavior
- kept canonical/temp policy explicit

Pass 2 - evidence and consistency
- re-checked the live code path in `unified_blueprint_validator.py`
- verified that Director focus header exists
- verified that verdict ownership still remains with Director in both main paths
- confirmed that `PASS_WITH_FIX` already has a runtime repair lane

Pass 3 - execution and readability
- split Tranche 1A invariant creation from Tranche 1B verdict binding
- downgraded V-3 to deferred Tranche 2
- removed the overclaim that Director sees nothing

Additional audit
- confirmed the execution seam still fits a single production owner file plus one targeted test file
- confirmed the closure criteria now depend on both warning creation and PASS blocking

Estimated confidence: 97%

## 12. Closure Update

Date: 2026-03-31
Closure Audit: `docs/2026-03-31/stage3-blueprint-validator-hardening-closure-audit.md`
Closure Evidence: `docs/2026-03-31/stage3-blueprint-validator-hardening-closure-evidence.json`
Status Rationale:
- the validator owner already contains the `scene_completeness` and `arc_timeline` collectors required by Tranche 1A
- the same owner already contains the binding prevalidation contract required by Tranche 1B
- targeted validation passed cleanly (`py_compile`, `ruff`, `pytest`, UTF-8 hygiene)
- no new code patch was required in this closure turn because the implementation was already present in the workspace
