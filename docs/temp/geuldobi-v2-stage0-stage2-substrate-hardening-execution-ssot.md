# Geuldobi V2 Stage0 Stage2 Substrate Hardening Execution SSOT

Date: 2026-03-17
Status: execution-ready
Canonical Path: `docs/2026-03-17/geuldobi-v2-stage0-stage2-substrate-hardening-execution-ssot.md`
Temp Mirror Path: `docs/temp/geuldobi-v2-stage0-stage2-substrate-hardening-execution-ssot.md`
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: prior lane1~3 and follow-on item edits, runtime log, authority-hygiene changes, survey bundles, and local drafts; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same commit; no active temp queue before opening this item`
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
- weak Bible outputs fail a bounded completeness gate instead of silently passing
- initial Treatment generation has at least one explicit continuity safeguard beyond title carry-over only
- `plot_roadmap` handoff expectations are testable and no longer implicit
- `PASS_WITH_FIX` cannot bypass the Stage 2 quality floor through promotion ambiguity
- ConstraintDB / StateTracker lifecycle is explicit enough that retry-path safety is no longer accidental

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
- the substrate-quality and contract issues remain live in current code

### Pass 2. Accuracy
- corrected the old survey's treatment-only reading of `plot_roadmap` fallback
- downgraded POV-policy concerns because normalization already exists

### Pass 3. ROI
- kept only the items that change upstream quality or correctness materially
