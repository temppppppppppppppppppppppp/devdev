# Stage Pipeline Lane 1 CW Context Architecture Execution SSOT

Date: 2026-03-17
Status: closed
Canonical Path: `docs/2026-03-17/stage-pipeline-lane1-cw-context-architecture-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage-pipeline-lane1-cw-context-architecture-execution-ssot.md`
Commit State:
- Baseline Commit: `100ecd03557e1b8c7a3544b5285fc80e7105050c`
- Baseline Dirty Summary: `dirty: 2 tracked docs, 1 tracked runtime log; hotspots: docs/2026-03-16/post-remediation-later-hardening-autopilot-prompt*.md, projects/test_project/logs/episode_production.jsonl`
- Resume Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Resume Drift Summary: `1 commit since baseline; worktree clean; lane-1 findings revalidated on live stage4_context_builder.py and context_advisor.py`
Source Survey Docs:
- `docs/2026-03-17/stage-pipeline-process-integrity-global-survey.md`
- `docs/2026-03-17/cw-context-delivery-optimization-outline.md`
- `docs/2026-03-17/stage4-context-composition-ranking-outline.md`
Evidence Artifacts:
- `docs/2026-03-17/stage-pipeline-process-integrity-evidence-manifest.md`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `96%`

## 1. Intent
- realize the highest-ROI upstream context architecture fixes for Chief Writer before deeper Director or retry-policy changes
- convert the bounded global survey finding `P1-A` into an execution-ready lane
- protect first-draft quality by fixing context ranking, work-focus input symmetry, and CW-facing tier order before adding more retry complexity

## 2. Baseline Facts
- live code already has strong truth and carry-over producers, but final CW `mandatory_context` remains accumulation-heavy
- writer-side retrieval computes `_work_focus` but does not yet pass it into `plan_stage4_retrieval()`
- Director-side retrieval already uses `work_focus`, so current asymmetry is writer-specific
- current problem is mainly context composition ranking, not raw retrieval absence
- bounded survey classified this lane as a shared substrate for all later process-integrity work

## 3. Scope
Included:
- `modules/core/stage4_context_builder.py`
- `modules/core/context_advisor.py`
- CW-facing context assembly order, tiering, and trim policy
- targeted tests for Stage 4 context planning and mandatory-context composition

Excluded:
- Director prompt austerity and gate-semantics cleanup
- PASS_WITH_FIX or retry-policy execution
- persistence substrate changes already closed in earlier remediation work
- desktop/UI shell review

## 4. Pass 1. Inventory Summary
- main producer surfaces:
  - truth and continuity base
  - work-slot summary
  - SC retrieval results
  - state-tracker and lookback bulk
  - future-arc and advisory sections
- main hotspot:
  - `build_mandatory_context()` in `stage4_context_builder.py`
- key asymmetry:
  - writer planner omits `work_focus` while Director planner consumes it
- main risk:
  - Tier 1 retrieval value is buried by Tier 2 bulk during composition or trim

## 5. Pass 2. Semantic Classification
- Class A: must-hold truth and carry-over
  - persisted world-state, fact-ledger continuity, relationship and threat carry-over, must-not-do constraints
- Class B: episode-direct retrieval
  - work tracking slots, scene context, relationship history, unresolved plot, bounded excerpts
- Class C: reference and advisory bulk
  - Stage 2 failure context, lookback, future-arc, pacing, foreshadow, narrative summaries, coverage-warning note

## 6. Side-Effect Map
- file writes / artifacts:
  - Stage 4 prompt text shape and any derived logs that capture CW mandatory context
- DB / schema / transaction boundaries:
  - not-applicable for primary execution scope; no schema intent
- JSONL / log / audit sinks:
  - retrieval observations and runtime prompt/debug traces may reflect new section order
- console / UI / operator output:
  - any operator-facing summaries that surface context composition or coverage warnings
- rollback / recovery / retry:
  - retry behavior should remain functionally unchanged in this lane; only pre-write context ordering changes
- cache / global state:
  - `mandatory_context` assembly and any in-memory retrieval planning caches
- bootstrap fallback / config-env mutation:
  - none expected

## 7. Realization Architecture
- establish a three-tier model:
  - Tier 0: truth and carry-over
  - Tier 1: episode-direct retrieval
  - Tier 2: advisory and bulk reference
- align writer retrieval planning with Director retrieval planning on `work_focus`
- restructure final composition as `Tier 0 -> Tier 1 -> Tier 2`
- keep `Pre-Write Pack` design as a downstream optional refinement; do not block tier cleanup on that larger design

## 8. Execution Tranches
1. input-contract alignment
   - pass writer `work_focus` into retrieval planning
   - keep behavior bounded and regression-friendly
2. tier separation and composition order
   - classify producers into Tier 0/1/2
   - reorder mandatory-context composition without changing persistence semantics
3. conditional bulk gating and tier-aware trim
   - move large advisory or history blocks behind conditional gates
   - trim Tier 2 before Tier 1 and protect Tier 0

## 9. Acceptance Criteria
- writer retrieval planner consumes `work_focus` as a first-class planning input
- Stage 4 context producers are explicitly tiered into Tier 0, Tier 1, and Tier 2
- composed CW context presents Tier 0 before Tier 1 and Tier 1 before Tier 2
- Tier 2 bulk no longer outranks or buries episode-direct retrieval by default
- coverage warnings remain observable without leading the default CW prompt

## 10. Verification Plan
- `python -m pytest tests/test_stage4_context_builder.py -k "plan_stage4_retrieval or work_slot_summary or mandatory_context or coverage_warning"`
- `python -m pytest tests/test_stage4_cv_context.py -q`
- `python -m pytest tests/test_stage4_interview_round.py -k "mandatory_context or retrieval"`
- `python scripts/ops_validator.py`
- bounded read review of `mandatory_context` ordering on representative fixtures before closure

## 11. Guardrails
- do not expand context architecture changes into Director prompt austerity inside this lane
- do not introduce new Python judgment authority; ranking and packaging only
- keep persistence surfaces and continuity sinks untouched unless a new live contradiction is discovered
- keep temp mirror synchronized only after canonical doc updates and fresh 3-pass re-audit

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition:
  - remove `docs/temp/stage-pipeline-lane1-cw-context-architecture-execution-ssot.md` only after implementation closes and the roadmap marks this item completed
- roadmap dependency:
  - `docs/2026-03-17/stage-pipeline-process-integrity-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Note
- realization outcome:
  - `modules/core/context_advisor.py` now accepts writer `work_focus` in `plan_stage4_retrieval()` and Stage 4 work-focus slots use the writer lane contract instead of the Director label
  - `modules/core/stage4_context_builder.py` now composes CW context as Tier 0 truth/carry-over -> Tier 1 work-focus and retrieval -> Tier 2 advisory bulk
  - retrieval coverage warnings remain visible but are placed in Tier 2 instead of leading the default CW prompt
- verification evidence:
  - `python -m pytest tests/test_context_advisor.py -q`
  - `python -m pytest tests/test_stage4_context_builder.py -k "plan_stage4_retrieval or work_slot_summary or mandatory_context or coverage_warning"`
  - `python -m pytest tests/test_stage4_cv_context.py -q`
  - `python -m pytest tests/test_stage4_interview_round.py -k "mandatory_context or retrieval"`
  - representative fixture review covered Tier 0/1/2 ordering via the new `mandatory_context` order assertions
- residual risk:
  - lane 2 Director semantic split remains pending and may still refine downstream prompt/telemetry semantics, but lane 1 scope is closed and independently validated
