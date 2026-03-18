# Geuldobi V2 Stage0 Stage2 Substrate Hardening Execution SSOT

Date: 2026-03-17
Status: closed
Canonical Path: `docs/2026-03-17/geuldobi-v2-stage0-stage2-substrate-hardening-execution-ssot.md`
Temp Mirror Path: `removed 2026-03-18`
Commit State:
- Baseline Commit: `8eb5c955408e759c0d45585773604acf4ff2efcb`
- Baseline Dirty Summary: `dirty (item 1 realization + item 1 closure docs)`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `item 1 code landed in stage2_preflight, stage2_finalizer, stage4_context_builder, blueprint_constraint_compiler`
Realization Summary:
- Slice A: `story_expander.py:254` — Bible bounded completeness warning gate (5 fact checks, operator warning, `_completeness_warnings`, top-level protagonist persona/background awareness)
- Slice A: `story_expander.py:478` — Treatment details cross-batch continuity (prev block id/title/reward)
- Slice B: `stage01_helpers.py:686` — plot_roadmap handoff contract validation for both injected and preexisting roadmap paths
- Slice C: `stage2_finalizer.py:847` — PASS_WITH_FIX quality floor 적용 (PASS-only → PASS+PASS_WITH_FIX)
- Slice C: `constraint_db.py:541` — snapshot()/restore() expanded to cover semantic item registry state as well as `arc_states`
- Slice C: `stage2_finalizer.py:400+` — CDB snapshot + retry-path rollback restore sites keep ConstraintDB and StateTracker aligned
Source Survey Docs:
- `docs/2026-03-17/별도 조사2/ssot_stage0-stage2-architecture-survey.md`
- `docs/2026-03-17/geuldobi-v2-legacy-survey-validity-roi-audit.md`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `96%`

## 1. Intent
- raise the upstream quality floor before Stage 3 and Stage 4 ever see weak or ambiguous substrate
- harden the Stage 0 -> Stage 2 contract where the live code still depends on loose or accidental guarantees
- close a small set of correctness gaps rather than expanding low-ROI telemetry or tuning work

## 2. Baseline Facts
- Stage 0 Bible generation still validates mostly structural success, not semantic completeness
  - `modules/core/stage0/story_expander.py:198`
- Stage 0 initial Treatment generation still lacks strong batch-to-batch continuity context
  - `modules/core/stage0/story_expander.py:305`
  - `modules/core/stage0/story_expander.py:441`
  - `modules/core/stage0/story_expander.py:478`
- `plot_roadmap` fallback exists now, but the handoff contract remains implicit
  - `modules/core/stage01_helpers.py:669`
  - `modules/core/stage01_helpers.py:680`
  - `modules/core/stage01_helpers.py:682`
- Stage 2 finalizer still applies the quality floor only to `PASS`, not `PASS_WITH_FIX`
  - `modules/core/stage2_finalizer.py:847`
- ConstraintDB still lacks snapshot / rollback symmetry with StateTracker
  - `modules/core/constraint_db.py`
  - `modules/core/stage2_finalizer.py:863`
- POV policy normalization now exists, so the old survey's `S0-5` is not a top-priority execution target
  - `modules/core/project_support.py:41`

## 3. Scope
Included:
- `modules/core/stage0/story_expander.py`
- `modules/core/stage01_helpers.py`
- `modules/core/project_support.py` only where needed for contract clarity
- `modules/core/stage2_finalizer.py`
- `modules/core/constraint_db.py`
- any local contract or model file needed to make the `plot_roadmap` handoff explicit
- directly affected tests

Excluded:
- low-priority style-cache invalidation work
- already-partial POV policy normalization work
- broad Stage 0 UX changes
- Stage 2 retrieval-budget tuning already partly covered by landed provenance/budget work

## 4. Realization Slices

### Slice A. Stage 0 minimum quality gates
- add bounded completeness validation for generated Bible
- add bounded continuity validation or retry signal for initial Treatment batches
- keep LLM as judge for semantic retry decisions; Python only collects threshold facts and routes

### Slice B. Explicit `plot_roadmap` handoff contract
- define the Stage 0 -> Stage 2 contract for `plot_roadmap` / raw block shape explicitly
- make fallback semantics readable and testable

### Slice C. Stage 2 substrate correctness
- apply the quality-floor story consistently when `PASS_WITH_FIX` is later promoted
- remove accidental dependency on ConstraintDB having no rollback path by making the contract explicit or symmetric

## 5. Acceptance Criteria
- weak Bible outputs surface a bounded completeness warning gate instead of silently passing without operator signal
- initial Treatment generation has at least one explicit continuity safeguard beyond title carry-over only
- `plot_roadmap` handoff expectations are testable on both injected and preexisting roadmap paths
- `PASS_WITH_FIX` cannot bypass the Stage 2 quality floor through promotion ambiguity
- ConstraintDB / StateTracker lifecycle is explicit enough that retry-path safety is no longer accidental, including semantic item registry state

## 6. Primary Risks
- over-automating Stage 0 semantic rejection in Python
- adding a brittle schema that blocks existing valid roadmap shapes
- introducing rollback code in ConstraintDB without clear transaction boundaries

## 7. Execution Notes
- treat `S0-3` as a contract-hardening task, not as a treatment-only outage bug
- keep `S0-5` out of the first tranche unless concrete contradictory live cases surface
- prefer bounded gates and explicit contracts over broad redesign

## 8. Verification Plan
- targeted Stage 0 tests for Bible completeness and Treatment continuity safeguards
- targeted Stage 0/1 helper tests for `plot_roadmap` fallback and contract shape
- targeted Stage 2 finalizer / retry-path tests for quality-floor and state-sync behavior
- `python scripts/check_utf8_hygiene.py ...`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 9. 3-Pass Audit Notes

### Pass 1. Validity
- the substrate-quality and contract issues remain live in current code after current-head revalidation

### Pass 2. Accuracy
- corrected the old survey's treatment-only reading of `plot_roadmap` fallback
- downgraded POV-policy concerns because normalization already exists
- confirmed later context-surface drift did not close the Stage 0 / Stage 2 substrate gaps tracked here

### Pass 3. ROI
- kept only the items that change upstream quality or correctness materially

## 10. Realization Evidence
- tests: 221 passed across 6 shards (finalizer 24, stage01_helpers 62, stage0 16, constraints+arc 30, protocol+sweep 33, preflight 72)
- 1 pre-existing failure: `test_stage0_pov.py::TestPOVSelection::test_pov_first_person_selected` (StageZeroManager.ui missing — unrelated to this realization)
- ruff: 0 violations
- ruff format: clean after auto-format
- UTF-8 hygiene: flagged lines are pre-existing Korean regex patterns (constraint_db L214-227, stage2_finalizer L118-175)
- ops_validator --strict: PASS (errors=0, warnings=0)
- queue-state.json: synced during the active queue and later removed after bundle closure

## 11. Closure Note
Date: 2026-03-18
Status: closed

### Verification Summary
- re-audit corrected the earlier overclaim of a hard-fail completeness gate; live code is warning-oriented by design
- re-audit also corrected existing-`plot_roadmap` validation coverage and ConstraintDB snapshot scope
- acceptance criteria were re-checked against the live code for warning-oriented completeness signaling, Treatment continuity, handoff contract clarity, PASS_WITH_FIX quality floor, and ConstraintDB / StateTracker symmetry
- targeted Stage 0, Stage 0/1 helper, Stage 2 finalizer, constraint, protocol, and preflight shards were reported as passing
- one pre-existing unrelated POV test failure remains outside this item

### Residual Risks
- Bible completeness remains warning-oriented, so very weak Bible output can still pass
- Treatment continuity only carries the immediately previous detailed block, not long-range continuity
- ConstraintDB snapshot / restore is now explicit, but current live retry paths still mostly benefit future code motion rather than frequent present-day rollbacks

### Follow-Up
- active execution queue exhausted; no next queue item remains in this bundle
- further Stage 0 / Stage 2 substrate expansion requires a fresh queue item or survey, not reuse of this closed lane

### Temp Cleanup
- execution SSOT mirror removed: yes (`docs/temp/geuldobi-v2-stage0-stage2-substrate-hardening-execution-ssot.md`)
- roadmap mirror removed: yes (`docs/temp/execution-roadmap.md`)
- queue-state refreshed or removed: yes (`docs/temp/queue-state.json` removed after queue exhaustion)
