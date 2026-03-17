# Geuldobi V2 Legacy Survey Validity ROI Audit

Date: 2026-03-17
Status: final
Canonical Path: `docs/2026-03-17/geuldobi-v2-legacy-survey-validity-roi-audit.md`
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: prior lane1~3 and follow-on item edits, runtime log, authority-hygiene changes, survey bundles, and local drafts; preserve as-is`
Source Survey Docs:
- `docs/2026-03-17/별도 조사2/ssot_stage23-improvement-survey.md`
- `docs/2026-03-17/별도 조사/ssot_integrated-survey.md`
- `docs/2026-03-17/별도 조사2/ssot_stage0-stage2-architecture-survey.md`
Confidence After 3-Pass Audit: `96%`

## 1. Intent
- re-audit three legacy survey drafts against the live codebase
- decide whether each draft is still valid, still accurate, and still worth execution effort
- extract only the still-actionable, high-ROI material into fresh execution SSOT docs

## 2. Executive Decision
- `ssot_stage23-improvement-survey.md`
  - verdict: `partially usable and execution-worthy after pruning`
  - reason:
    - the core semantic-loss and form-bias diagnosis is still mostly live
    - several line references are stale
    - the document predates the landed provenance/budget substrate and must not be treated as a standalone controller
- `ssot_integrated-survey.md`
  - verdict: `strategic reference only`
  - reason:
    - it is directionally useful as an umbrella map
    - it mixes already-landed work, broad hypotheses, live-run-dependent ideas, and low-ROI expansions
    - it is not precise enough to govern direct code changes without a fresh pruning layer
- `ssot_stage0-stage2-architecture-survey.md`
  - verdict: `mostly usable and execution-worthy after correction`
  - reason:
    - the high-ROI substrate findings are still live
    - several low-priority or fallback-related claims need correction against current code

## 3. Findings

### F1. `ssot_stage23-improvement-survey.md` is stale if read as a standalone controller
Severity: medium

The survey does not reflect the landed Stage 2/3/4 provenance and budget substrate:
- `modules/core/context_advisor.py:197`
- `modules/core/stage2_preflight.py:1217`
- `modules/core/stage3_orchestrator.py:1254`
- `modules/core/stage4_context_builder.py:2795`
- `modules/core/quality_dashboard.py:202`

This does not invalidate the semantic-loss diagnosis, but it does make the survey incomplete as a direct execution source.

### F2. `ssot_integrated-survey.md` overstates some missing observability gaps
Severity: medium

Its `G10-1` / Direction 4 framing says context consumption measurement is missing. That was true before the follow-on provenance/budget work, but the live code now has:
- `ContextBudgetTracker` and provenance ledgers in `modules/core/context_advisor.py:197`
- Stage 2 capture in `modules/core/stage2_preflight.py:1217`
- Stage 3 capture in `modules/core/stage3_orchestrator.py:1254`
- Stage 4 capture in `modules/core/stage4_context_builder.py:1671` and `modules/core/stage4_context_builder.py:2795`

So the document remains strategically useful, but direct execution based on its current wording would duplicate already-landed work.

### F3. `ssot_stage0-stage2-architecture-survey.md` is partly outdated on `S0-3`
Severity: medium

The survey says concept-path `plot_roadmap` depends on Treatment and can become empty with no fallback. The live code now has a saved-arcs fallback:
- `modules/core/stage01_helpers.py:669`
- `modules/core/stage01_helpers.py:680`
- `modules/core/stage01_helpers.py:682`

So `S0-3` is still real as a contract-quality issue, but not as a treatment-only hard block.

### F4. `ssot_stage0-stage2-architecture-survey.md` is partly outdated on `S0-5`
Severity: low

The survey treats POV x external policy combinations as ungoverned. The live code now normalizes the policy by POV and genre:
- `modules/core/project_support.py:41`
- `modules/core/project_support.py:56`
- `modules/core/project_support.py:192`

This is not a full semantic validator, but the problem is no longer an unbounded 12-combination free-for-all.

### F5. The highest-ROI unresolved issues are still live
Severity: high

The following claims remain materially true in the live code:

- Stage 2 -> 4 semantic carry-over is still heavily reduced to `constraint_summary`
  - `modules/core/stage2_finalizer.py:1039`
  - `modules/core/stage4_context_builder.py:2374`

- relationship trigger / justification is still dropped in the Stage 2 preflight mapping path
  - `modules/core/stage2_preflight.py:1418`
  - `modules/core/context_advisor.py:999`

- stop-line content still suffers tight extraction / formatting truncation
  - `modules/domain/agents/blueprint_constraint_compiler.py:230`
  - `modules/domain/agents/blueprint_constraint_compiler.py:131`

- Blueprint schema still leaves `scene_breakdown` as a bare object and the model still accepts an untyped dict
  - `modules/core/response_schemas.py:516`
  - `modules/models/blueprint.py:29`

- blueprint validation is still mostly structural and does not do beat-level fidelity checking
  - `modules/domain/agents/unified_blueprint_validator.py:331`

- tactical validation is still dominated by length and episode-marker checks, with no robust specificity proxy
  - `modules/domain/agents/arc_ensemble.py:962`
  - `modules/domain/agents/arc_draft_validator.py:382`

- Stage 0 Bible and Treatment generation still lack strong completeness / continuity gates
  - `modules/core/stage0/story_expander.py:198`
  - `modules/core/stage0/story_expander.py:305`
  - `modules/core/stage0/story_expander.py:441`
  - `modules/core/stage0/story_expander.py:478`

- Stage 2 still keeps the `PASS_WITH_FIX` quality-floor asymmetry in finalizer logic
  - `modules/core/stage2_finalizer.py:847`

- ConstraintDB still has no snapshot / rollback counterpart to the StateTracker story
  - `modules/core/constraint_db.py`
  - `modules/core/stage2_finalizer.py:863`

## 4. ROI Classification

### High ROI
- Stage 2/3 semantic transport restoration
  - why:
    - directly affects current Stage 4 output quality
    - reuses the landed provenance/budget substrate instead of replacing it
- Stage 0 / Stage 2 substrate hardening
  - why:
    - fixes upstream quality ceiling and handoff fragility
    - contains several real correctness gaps, not just telemetry wants
- Stage 2/3 semantic validation hardening
  - why:
    - converts still-formal validators into meaning-aware guards
    - should follow or pair with semantic transport work, not precede it blindly

### Medium ROI
- advisory weighting and retrieval-budget tuning from the Stage 0/2 survey
  - reason:
    - partly landed already
    - useful, but not first-order quality blockers

### Low ROI or Not Ready
- large integrated-survey themes that depend on fresh human feedback, benchmark corpus, or live-run calibration
  - examples:
    - external feedback loop closure
    - human/system calibration loop
    - Positive Reference DB expansion
    - Director SPOF redesign as a broad architecture project

## 5. Recommended Extraction
- create one execution SSOT for Stage 2/3 semantic transport restoration
- create one execution SSOT for Stage 0 / Stage 2 substrate hardening
- create one execution SSOT for Stage 2/3 semantic validation hardening
- keep `ssot_integrated-survey.md` as reference-only strategy input, not as a direct execution controller

## 6. 3-Pass Audit Notes

### Pass 1. Validity
- checked each survey against live code rather than trusting dated line references
- separated concept validity from stale implementation detail

### Pass 2. Accuracy
- corrected specifically stale claims around:
  - landed provenance/budget observability
  - `plot_roadmap` fallback
  - POV policy normalization

### Pass 3. ROI
- removed already-landed or live-run-dependent items from direct execution extraction
- kept only execution-worthy substrate and semantic-fidelity work
