# Geuldobi V2 Stage23 Semantic Validation Hardening Execution SSOT

Date: 2026-03-17
Status: execution-ready
Canonical Path: `docs/2026-03-17/geuldobi-v2-stage23-semantic-validation-hardening-execution-ssot.md`
Temp Mirror Path: `docs/temp/geuldobi-v2-stage23-semantic-validation-hardening-execution-ssot.md`
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: prior lane1~3 and follow-on item edits, runtime log, authority-hygiene changes, survey bundles, and local drafts; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same commit; no active temp queue before opening this item`
Source Survey Docs:
- `docs/2026-03-17/별도 조사2/ssot_stage23-improvement-survey.md`
- `docs/2026-03-17/별도 조사/ssot_integrated-survey.md`
- `docs/2026-03-17/geuldobi-v2-legacy-survey-validity-roi-audit.md`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `95%`

## 1. Intent
- reduce the current form-only validation bias in Stage 2 and Stage 3
- make structural validators meaning-aware where the cost/benefit is strongest
- keep this item focused on bounded validation hardening, not a full scoring-system redesign

## 2. Baseline Facts
- Blueprint schema still leaves `scene_breakdown` as a bare object
  - `modules/core/response_schemas.py:516`
- Blueprint model still accepts an untyped dict for `scene_breakdown`
  - `modules/models/blueprint.py:39`
- unified blueprint validation still focuses on required fields, length, scene count, stop-line, and continuity
  - `modules/domain/agents/unified_blueprint_validator.py:331`
- arc tactical validation still emphasizes length, episode coverage, and markers
  - `modules/domain/agents/arc_ensemble.py:962`
  - `modules/domain/agents/arc_draft_validator.py:382`
- integrated survey ideas like broad human-calibration loops remain out of scope for this item

## 3. Scope
Included:
- `modules/core/response_schemas.py`
- `modules/models/blueprint.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/arc_draft_validator.py`
- directly affected tests

Excluded:
- new external feedback systems
- full Director scoring redesign
- broad benchmark corpus or Positive Reference DB work
- transport restoration handled in a separate item

## 4. Realization Slices

### Slice A. Typed `scene_breakdown` contract
- move `scene_breakdown` from bare object acceptance toward a bounded typed contract
- require enough structure that downstream checks can inspect more than count alone

### Slice B. Tactical specificity proxies
- add low-cost semantic proxies for `tactical_doc`
- examples:
  - scene-goal density
  - concrete action or consequence markers
  - named anchor spread

### Slice C. Blueprint / Arc intent fidelity
- add a bounded fidelity check between upstream intent and Blueprint / Arc realization
- target the highest-value gap first rather than building a universal semantic judge

## 5. Acceptance Criteria
- `scene_breakdown` is no longer just a bare object in the primary schema path
- tactical validation can fail or warn on generic-but-long text, not just on short text
- Blueprint / Arc validation includes at least one meaning-aware fidelity check beyond raw structure
- the new checks remain bounded and testable without giving Python final creative judgment authority

## 6. Primary Risks
- attempting full semantic judgment in Python
- over-constraining Blueprint output schemas too early
- false negatives from naive keyword-only specificity checks

## 7. Execution Notes
- this lane should follow or pair with semantic transport restoration so it validates richer truth, not lossy leftovers
- prefer narrow high-signal proxies over wide heuristic sprawl
- keep ending-hook or scene-budget extras in backlog unless they fall out naturally from the main slices

## 8. Verification Plan
- targeted schema / model tests for `scene_breakdown`
- targeted Stage 2 validator tests for specificity proxies
- targeted Blueprint validator tests for bounded fidelity checks
- `python scripts/check_utf8_hygiene.py ...`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 9. 3-Pass Audit Notes

### Pass 1. Validity
- the form-bias diagnosis still matches the live validation stack

### Pass 2. Accuracy
- removed already-landed provenance work from this lane

### Pass 3. ROI
- narrowed to three bounded validation slices only
