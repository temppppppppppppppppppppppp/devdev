# Geuldobi V2 Post-Reentry Residual Risk 3-Pass Audit

Date: 2026-03-18
Status: final
Canonical Path: `docs/2026-03-18/geuldobi-v2-post-reentry-residual-risk-3pass-audit.md`
Commit State:
- Baseline Commit: `8eb5c955408e759c0d45585773604acf4ff2efcb`
- Baseline Dirty Summary: `dirty: 24 tracked/deleted, 1 untracked; hotspots: docs/2026-03-17 closure corrections, modules/core/{stage2_preflight,stage2_finalizer,stage4_context_builder,story_expander,stage01_helpers,constraint_db,response_schemas}.py, modules/domain/agents/{arc_draft_validator,blueprint_constraint_compiler,blueprint_ensemble,director_ensemble,three_phase_blueprint_generator,unified_blueprint_validator}.py, modules/models/blueprint.py, tests/test_legacy_reentry_reaudit.py`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Reviewed Bundle:
- `docs/2026-03-17/geuldobi-v2-stage23-semantic-transport-restoration-execution-ssot.md`
- `docs/2026-03-17/geuldobi-v2-stage0-stage2-substrate-hardening-execution-ssot.md`
- `docs/2026-03-17/geuldobi-v2-stage23-semantic-validation-hardening-execution-ssot.md`
- `docs/2026-03-17/geuldobi-v2-legacy-survey-reentry-execution-roadmap.md`
- live workspace code under `modules/core/` and `modules/domain/agents/`
Confidence After Audit: `96%`

## Purpose
- identify the bounded residual risks that still remain after the prior three-item reentry queue was re-audited and closed
- convert those residual risks into a fresh execution bundle instead of overloading the closed 2026-03-17 queue
- keep authority aligned with live code rather than stale integrated-survey text or overstated closure summaries

## Pass 1. Fact Accuracy
- residual transport risk still exists after the closed semantic-transport item:
  - `modules/core/stage2_finalizer.py` produces `constraint_summary` and bounded text `rationale_digest`, but no stable structured carryover contract exists yet
  - `modules/domain/agents/blueprint_constraint_compiler.py` still transports `constraint_summary` and `state_changes_summary`, not a structured rationale lane
  - `modules/core/stage4_context_builder.py` injects free-text `rationale_digest`, while trim protection and loss warnings still center on other sections; semantic carryover can still disappear under budget pressure without an explicit dedicated warning
- residual Stage 0 / Stage 2 substrate risk still exists after the closed substrate-hardening item:
  - `modules/core/stage0/story_expander.py` records `_completeness_warnings`, but weak Bible outputs still pass without an LLM-mediated retry or stop-save path
  - Stage 0 continuity remains prompt-only and mostly immediate-previous-block scoped
  - `modules/core/stage0/__init__.py` and `modules/core/stage01_helpers.py` still split roadmap injection/gating authority, which is a drift risk
- residual validation-hardening risk still exists after the closed Stage23 validation item:
  - typed `scene_breakdown` support now exists in schema/model/main generation paths
  - `modules/domain/agents/arc_draft_validator.py` now emits downstream advisory issues for named-anchor and action-density signals
  - `modules/domain/agents/unified_blueprint_validator.py` still compares first and prevalidates only the selected candidate, while `modules/domain/agents/director_ensemble.py` compare output lacks a structured advisory-weight channel and `modules/domain/agents/blueprint_ensemble.py` does not populate the expected `python_warnings` bridge

## Pass 2. Queue Extraction

### Item A. Structured semantic carryover
- open a new execution item to replace text-only carryover with a bounded structured transport contract from Stage 2 into Stage 4 and, where needed, Stage 3 transport
- require explicit trim-loss observability if carried semantic sections are dropped

### Item B. LLM-mediated completeness retry
- open a new execution item to turn weak Stage 0 completeness and continuity signals into bounded retry or stop-save escalation
- unify the real roadmap gate path so fresh generation and extension do not drift

### Item C. Director advisory fidelity escalation
- open a new execution item to make candidate-level advisory and fidelity signals visible to compare-mode selection and bounded retry logic
- avoid broad scoring-system redesign or heuristic sprawl

## Pass 3. ROI and Ordering
- order the queue as `A -> B -> C`
- Item A goes first because Item C should consume richer structured truth than today's free-text carryover
- Item B goes second because it hardens upstream quality floor and save gating without depending on Item C
- Item C goes last because it should consume richer truth from Item A and clearer upstream floor signals from Item B
- the prior 2026-03-17 queue remains historically closed; this follow-on bundle must use new canonical docs and new temp mirrors

## Result
- a fresh three-item residual-risk execution queue is warranted
- the governing documents for that queue should live under `docs/2026-03-18/`
- the active temp queue should contain only the new execution SSOT mirrors plus a single aggregate roadmap mirror
- before any code implementation from the new queue, each targeted canonical SSOT and the roadmap must be re-audited against the then-current workspace and reconfirmed at `>=95%` confidence
