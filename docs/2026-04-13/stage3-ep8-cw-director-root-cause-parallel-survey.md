# Stage3 EP8 CW vs Director Root-Cause Parallel Survey

- Date: 2026-04-13
- Scope: live `0_temp.txt` rerun capture plus current `main@32d6f0c8` static re-audit of Stage3 ownership for the `ep8` reject loop
- Mode: survey-only, parallel, live-evidence merge; no code changes in this turn
- Canonical Path: `docs/2026-04-13/stage3-ep8-cw-director-root-cause-parallel-survey.md`
- Baseline Commit: `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `dirty: live 000_260412_a run artifacts, 0_temp capture, local Vertex provider/model edits, and targeted router/base-agent test expectation edits already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none during this survey`
- Side-Effect Coverage: live console capture, project DB/artifacts, validator/runtime/generator code, and targeted tests inspected; no queue membership or runtime artifacts were mutated in this survey step
- Confidence: `97%`

## Purpose

This survey answers one bounded question:

- is the current `ep8` Stage3 failure family primarily a `CW/generator` problem or a `Director/validator` problem, and what should the formal next action be

This document is survey-only.

This document does not open a new queue lane.

This document does not claim closure of the broader Stage3 lane.

## Evidence Anchors

Live runtime anchors:

- `0_temp.txt`
- `projects/000_260412_a/project_data.db`
- `projects/000_260412_a/logs/pass_rate_monitor.json`
- `projects/000_260412_a/logs/session/ui_events.jsonl`
- `projects/000_260412_a/logs/artifacts/stage3/ep_0007/attempt_10/final_blueprint__action_focused.json`
- `projects/000_260412_a/plans/arcs/arc_002.txt`

Current code owners:

- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/response_schemas.py`
- `modules/core/stage_cross_stage_contract.py`
- `modules/core/stage3_orchestrator.py`

Targeted validation shards:

- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_unified_blueprint_validator_lane_c.py`
- `tests/test_blueprint_patch_mode.py`
- `tests/test_stage23_stage4_readiness_wave1.py`

Queue / execution anchors:

- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`

## Executive Summary

- The current `ep8` blocker is not best explained as a `Director` false reject. The heavier fault is that Stage3 producer-side candidate generation still lets structurally weak or authority-drifting blueprints survive long enough to hit validator churn.
- `0_temp.txt` shows four visible `ep8` failures plus a fifth attempt starting, and the outer retry ceiling remains `10` on this Stage3 path.
- The validator is not totally blameless: `opening_transition` normalization is strict, `tactical_semantic_fidelity` uses broad heuristics, and the fixed `after 3 patch attempts` terminal message is misleading for regenerate-before-patch routes.
- The next formal action should therefore not be another paid rerun first. The next cheap tranche is one bounded producer-side contract-alignment and failure-surface-honesty slice, then a bounded `ep7/ep8` rerun.

## Findings

### 1. The live `ep8` loop is real and already expensive

`0_temp.txt` shows four clear `ep8` reject cycles followed by a fifth generation start:

- `fix_scope: full` with `opening_transition` mismatch
- `fix_scope: full` with `tactical_semantic_fidelity`, `opening_transition`, and `scenario_density`
- `fix_scope: full` with `scene_breakdown` missing, `scene_count = 0`, and `protagonist_state` empty
- `fix_scope: full` with `opening_transition` plus `scenario_density`

The Stage3 outer retry ceiling remains `10` because `stage3_orchestrator.py` still calls the runtime with `max_retries=9` while operator output says `최대 10회 시도`.

Conclusion:

- this is a live reject loop, not a log-only illusion
- the current captured run is already in paid failure territory before `ep8` closure

### 2. Director is not the primary owner of the reject family

The code path still runs Python-side prevalidation before the Director compare call:

- `_python_pre_validate(...)` happens first in `unified_blueprint_validator.py:1034`
- the Director call follows in `unified_blueprint_validator.py:1076`

The specific `0_temp.txt` issue families are real prevalidation outputs:

- required field / missing `scene_breakdown`: `unified_blueprint_validator.py:1144`
- low scene count: `unified_blueprint_validator.py:1168`
- `opening_transition` mismatch: `unified_blueprint_validator.py:2020`
- empty `protagonist_state`: `unified_blueprint_validator.py:2089`
- unauthorized tactical event marker: `unified_blueprint_validator.py:2379`
- low scenario density: `unified_blueprint_validator.py:2458`

Conclusion:

- the Director is not inventing these categories after the fact
- the more accurate picture is `Director picks the best available candidate, then validator/runtime overlays a binding/full-regenerate decision on top`

### 3. Producer-side contract alignment is weaker than the validator contract it feeds

Current Stage3 prompt guidance is stronger than the actual machine gate:

- prompt examples ask for `scene_breakdown 2~5`, `integrated_scenario 1000+`, and explicit state payloads
- the schema only requires `episode_number`, `scene_breakdown`, and `integrated_scenario` in `response_schemas.py:705`
- `opening_transition` and `protagonist_state` are present but not required in `response_schemas.py:685` and `response_schemas.py:702`
- `_request_blueprint_generation(...)` in `blueprint_ensemble.py:767` only blocks when the required pair is missing
- qualification still accepts candidates using a lighter `scene_gate + integrated_len >= 500` surface in `blueprint_ensemble.py:482` and `blueprint_ensemble.py:493`

Conclusion:

- the Stage3 producer path is still looser than the validator contract that later treats `opening_transition`, `protagonist_state`, and dense local structure as meaningful
- that mismatch is the clearest cheap upstream fix

### 4. `opening_transition` mismatch is a real contract seam, not a clean false reject

The validator now compares the declared transition type with a normalized cross-stage contract:

- declared + normalized opening data is prepared around `unified_blueprint_validator.py:1361` and `unified_blueprint_validator.py:1455`
- mismatch promotion happens in `unified_blueprint_validator.py:2009`
- normalization rules in `stage_cross_stage_contract.py:205`, `stage_cross_stage_contract.py:267`, and `stage_cross_stage_contract.py:296` are intentionally sensitive to time shift, scene cues, and start-location drift

This means:

- `direct_continuation -> explicit_transition` is currently an intended strictness seam
- the cheaper next move is not to relax the validator first
- the cheaper next move is to make the producer path emit and qualify opening-transition intent more honestly

### 5. `tactical_semantic_fidelity` stays a watch item, not the first fix target

The heuristic family is admittedly broad:

- intrusion markers include wide tokens such as staff / shadow / response-style wording
- the scan still has skip logic when the tactical excerpt already contains the same event family

Current evidence does not show the offending generated blueprint text itself for `ep8`, so this category is not yet strong enough to demote from `binding watch` to `confirmed false positive`.

Conclusion:

- keep it as a secondary validator watch item
- do not let it outrank the clearer producer-side contract mismatch

### 6. The fixed `after 3 patch attempts` line is misleading on the current route

`three_phase_blueprint_runtime.py` still uses `max_fix = 3` as a loop constant around `2209`, but binding/full-regenerate routes can break back to generation before the local patch call around `2339`.

The terminal failure message still prints:

- `PASS_WITH_FIX unresolved after 3 patch attempts -> REJECT`

from `three_phase_blueprint_runtime.py:2606`

Conclusion:

- the operator-facing line overstates what actually happened on regenerate-before-patch routes
- this is a real honesty / observability bug even if it is not the primary quality blocker

### 7. Earlier `ep7` evidence also leans toward producer drift rather than pure validator overreach

The saved `ep7` final blueprint already carries:

- `opening_transition.type = explicit_transition`
- `end_location = 한미증권 청담동 지점 15층 VIP룸 입구`
- a next-morning style `time_flow`

But the arc plan for `ep8` still describes the start from the taxi and the later VIP-room confrontation as the current-episode beat.

Conclusion:

- at least part of the semantic over-consumption likely existed in generated/saved Stage3 output before the current `ep8` validator churn
- this further weakens a `Director-primary` reading

## Ownership Verdict

- `CW / generator / ensemble`: primary owner of the current `ep8` blocker family
- `Director`: secondary only; selects among imperfect candidates but is not the main source of the failure categories
- `validator`: secondary mixed owner; contract strictness is mostly legitimate, but some heuristics and route-surface messaging remain rough
- `runtime logging`: definite owner of the misleading `after 3 patch attempts` wording

## Execution Consequence

Keep the active queue shape.

Do not open a new queue lane.

Keep ownership here:

- parent owner: `0_0-stage3-contract-tightening-remediation`
- sibling support: `0_0-stage3-opening-transition-contract-normalization-remediation`
- child non-owner except route honesty / locality debt: `0_0-stage3-partial-fix-hardening-remediation`

Change the immediate-next action from `proof rerun first` to one bounded static tranche:

1. align producer-side Stage3 prompt/schema/qualify expectations with the validator contract
2. make `opening_transition` and non-empty opening-state structure producer-visible and qualify-visible without widening into broad prompt retuning
3. tighten cheap candidate admission for obviously weak structural payloads before they become expensive validator churn
4. replace the misleading fixed `after 3 patch attempts` wording with route-honest failure language
5. only then take the bounded `ep7/ep8` rerun

Explicit non-goals for that tranche:

- no broad Director retuning
- no broad tactical-semantic heuristic rewrite yet
- no new queue family
- no broad DecisionKernel migration

## Verification

Targeted current-workspace shards re-ran clean:

- `pytest tests/test_blueprint_ensemble_generate_ensemble.py -k "missing_required_fields or anti_contamination_contract or dense_two_scene_blueprint" -q`
  - `3 passed`
- `pytest tests/test_unified_blueprint_validator_lane_c.py -k "opening_transition_contract or opening_transition_mismatch or empty_key_events_as_major_scene_completeness or stage4_readiness_contract_gaps" -q`
  - `3 passed`
- `pytest tests/test_blueprint_patch_mode.py -k "escalates_structural_binding_categories_to_full_regenerate or escalates_contract_blocked_scene_model_to_full_regenerate or pass_with_fix_unresolved" -q`
  - `3 passed`
- `pytest tests/test_stage23_stage4_readiness_wave1.py -k "stage4_readiness_contract_gaps or off_arc_intrusion or skips_tactical_intrusion_flag or disguised_intrusion" -q`
  - `4 passed`

## 3-Pass Audit

Pass 1. Structure and scope:

- kept this document survey-only rather than silently widening into a new execution SSOT
- made the ownership question explicit
- kept queue consequences bounded to existing Stage3 lanes

Pass 2. Evidence and consistency:

- checked `0_temp.txt` against current validator/runtime/generator code
- checked current queue docs so the recommendation stays lane-consistent
- checked live project artifacts and DB state so the verdict is not based on console text alone

Pass 3. Execution and readability:

- converted the ownership verdict into one bounded next action
- kept broad retuning and broader refactors explicitly deferred
- separated primary blocker, secondary watch item, and operator-surface honesty debt

Confidence after 3-pass re-audit: `97%`
