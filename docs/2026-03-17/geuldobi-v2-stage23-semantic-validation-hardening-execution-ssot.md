# Geuldobi V2 Stage23 Semantic Validation Hardening Execution SSOT

Date: 2026-03-17
Status: closed
Canonical Path: `docs/2026-03-17/geuldobi-v2-stage23-semantic-validation-hardening-execution-ssot.md`
Temp Mirror Path: `removed 2026-03-18`
Commit State:
- Baseline Commit: `8eb5c955408e759c0d45585773604acf4ff2efcb`
- Baseline Dirty Summary: `dirty (items 1+2 realization + closure docs)`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `items 1+2 code landed; items 1+2 temp mirrors removed`
Realization Summary:
- Slice A: `response_schemas.py:518` — `scene_breakdown` now uses typed scene-entry schema via `additionalProperties`
- Slice A: `modules/models/blueprint.py` — bounded `BlueprintScene` model added to the primary model path
- Slice A: `modules/domain/agents/blueprint_ensemble.py` — main ensemble generation path now uses `BLUEPRINT_SCHEMA`
- Slice A/C: `modules/domain/agents/unified_blueprint_validator.py` — scene structure / Arc NPC fidelity checks retained even in Director compare mode
- Slice B: `modules/domain/agents/arc_draft_validator.py` — named-anchor and action-density signals now propagate as downstream advisory issues
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
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
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
- `scene_breakdown` is no longer just a bare object in the primary schema/model path, and the main ensemble generation path now uses that schema
- tactical validation can warn on generic-but-long text, not just on short text, and those proxies propagate downstream as advisory issues
- Blueprint / Arc validation includes at least one meaning-aware fidelity check beyond raw structure, including the Director compare path
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
- the form-bias diagnosis still matches the live validation stack after current-head revalidation

### Pass 2. Accuracy
- removed already-landed provenance work from this lane
- confirmed later context-budget/provenance refactors did not change the schema / validator facts tracked here

### Pass 3. ROI
- narrowed to three bounded validation slices only

## 10. Realization Evidence
- tests: 195 passed across 5 shards (blueprint+protocol 28, arc 21, sweep+constraints 39, stage2 51, stage4 56)
- ruff: 0 violations
- ruff format: clean after auto-format
- UTF-8 hygiene: flagged lines are pre-existing Korean regex patterns (arc_draft_validator L45-59, L649, L704, L776, L804)
- ops_validator --strict: PASS (errors=0, warnings=0)
- queue-state.json: synced during the active queue and later removed after queue exhaustion

## 11. Closure Note
Date: 2026-03-18
Status: closed

### Verification Summary
- re-audit corrected the earlier overclaim that compare-mode and main ensemble generation were fully covered; live code now enforces schema on ensemble generation and retains python prevalidation issues after Director compare
- tactical specificity proxies now propagate as downstream advisory issues rather than remaining local-only suggestions
- acceptance criteria were re-checked against the live code for typed scene entries, tactical specificity advisories, and Arc-to-Blueprint fidelity checks
- targeted blueprint, arc, sweep/constraint, stage2, and stage4 shards were reported as passing
- temp queue cleanup was completed after canonical roadmap / SSOT status updates

### Residual Risks
- scene structure checks remain bounded and mostly advisory; string fallback is still allowed for compatibility
- action-density proxy is language-pattern-based and may miss some genre-specific concrete writing
- NPC fidelity checks only activate when relationship NPC data is present upstream

### Follow-Up
- active execution queue exhausted; no next queue item remains in this bundle
- further validation expansion requires a fresh survey or queue item, not extension of this closed lane

### Temp Cleanup
- execution SSOT mirror removed: yes (`docs/temp/geuldobi-v2-stage23-semantic-validation-hardening-execution-ssot.md`)
- roadmap mirror removed: yes (`docs/temp/execution-roadmap.md`)
- queue-state refreshed or removed: yes (`docs/temp/queue-state.json` removed after queue exhaustion)
