# Geuldobi V2 Stage23 Director Advisory Fidelity Escalation Execution SSOT

Date: 2026-03-18
Status: closed
Canonical Path: `docs/2026-03-18/geuldobi-v2-stage23-director-advisory-fidelity-escalation-execution-ssot.md`
Temp Mirror Path: `removed 2026-03-18 after closure`
Commit State:
- Baseline Commit: `8eb5c955408e759c0d45585773604acf4ff2efcb`
- Baseline Dirty Summary: `dirty: 24 tracked/deleted, 1 untracked; hotspots: docs/2026-03-17 closure corrections, modules/core/{stage2_preflight,stage2_finalizer,stage4_context_builder,story_expander,stage01_helpers,constraint_db,response_schemas}.py, modules/domain/agents/{arc_draft_validator,blueprint_constraint_compiler,blueprint_ensemble,director_ensemble,three_phase_blueprint_generator,unified_blueprint_validator}.py, modules/models/blueprint.py, tests/test_legacy_reentry_reaudit.py`
- Resume Commit: `d4e96804898491ae67085a327bf35b080ced4364`
- Resume Drift Summary: `1 commit since baseline; schema compatibility drift touched response_schemas.py, blueprint_ensemble.py, blueprint.py, three_phase_blueprint_generator.py, stage3_orchestrator.py`
Source Survey Docs:
- `docs/2026-03-18/geuldobi-v2-post-reentry-residual-risk-3pass-audit.md`
- `docs/2026-03-17/geuldobi-v2-stage23-semantic-validation-hardening-execution-ssot.md`
Evidence Artifacts:
- `live workspace evidence only; no separate txt/json artifact saved for queue-open`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `96%`

## 1. Intent
- make candidate-level advisory and fidelity signals materially visible to compare-mode selection and bounded retry decisions
- preserve Director sovereignty by keeping Python in a bounded evidence-collection role

## 2. Baseline Facts
- `modules/core/response_schemas.py`, `modules/models/blueprint.py`, and `modules/domain/agents/blueprint_ensemble.py` now support typed `scene_breakdown` in the main generation path
- `modules/domain/agents/arc_draft_validator.py` now converts targeted warnings and suggestions into downstream `advisory_issues`
- `modules/core/stage2_validation_pipeline.py` forwards those advisory issues to later LLM-facing stages
- `modules/domain/agents/unified_blueprint_validator.py` still compares first and prevalidates only the selected candidate afterward
- `modules/domain/agents/director_ensemble.py` compare output does not yet expose a structured advisory-weight/severity channel
- `modules/domain/agents/blueprint_ensemble.py` does not currently populate the `python_warnings` bridge that compare-time consumers already know how to read
- `modules/domain/agents/three_phase_blueprint_generator.py` reduces validation output to a thin compare summary and does not preserve enough fidelity/advisory structure for stronger runtime escalation

## 3. Scope
Included:
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/domain/agents/arc_draft_validator.py`
- `modules/core/stage2_validation_pipeline.py`
- related compare-mode, advisory-flow, and persistence tests

Excluded:
- full Director scoring redesign
- benchmark corpus or positive-reference DB systems
- unrelated Stage 0 substrate changes
- raw semantic-judge heuristics in Python

## 4. Pass 1. Inventory Summary
- candidate-generation hotspot: `blueprint_ensemble.py`
- compare/selection hotspots: `unified_blueprint_validator.py` and `director_ensemble.py`
- advisory production hotspot: `arc_draft_validator.py`
- downstream propagation hotspot: `stage2_validation_pipeline.py`
- persistence/retry hotspot: `three_phase_blueprint_generator.py`

## 5. Pass 2. Semantic Classification
- Class A: candidate-level advisory/fidelity evidence collection
- Class B: Director compare-mode visibility and bounded weighting
- Class C: persistence of repair scope, quality risk, and bounded escalation

## 6. Side-Effect Map
- file writes / artifacts: no new persistent artifact class; existing blueprint/arc outputs remain authoritative, but `_stage3_meta` and saved selection metadata may gain fields
- DB / schema / transaction boundaries: not applicable
- JSONL / log / audit sinks: compare-mode, selection, and advisory logs may gain structured notes
- console / UI / operator output: operator-facing advisory summaries may become clearer
- rollback / recovery / retry: bounded retry or escalation path may be added
- cache / global state: candidate metadata only; no new durable cache
- bootstrap fallback / config-env mutation: not applicable

## 7. Realization Architecture
- gather candidate-specific advisory and fidelity signals before compare-mode selection where possible
- surface those signals to the Director compare path in a compact structured form with fields such as `source`, `severity`, `category`, `message`, and `candidate_count`
- preserve `fix_scope`, `fix_scope_reasoning`, `selection_reason`, and verdict/fidelity rationale end-to-end so Stage 3 patch loops can act on them
- unresolved fidelity should not leave Stage 3 as an unmarked plain `PASS`; acceptable bounded outcomes are:
  - `PASS_WITH_FIX`
  - `REJECT`
  - `PASS` with explicit `quality_risk=True` and persisted fidelity advisory
- if advisory density is high, route the next action through a bounded LLM retry/escalation path rather than a Python hard reject

## 8. Execution Tranches
1. preserve candidate-level advisory/fidelity metadata before compare-mode selection
2. inject that metadata into Director compare visibility and returned payloads in a compact form
3. persist repair/fidelity signals through Stage 3 runtime metadata and bounded retry behavior

## 9. Acceptance Criteria
- compare-mode selection can see candidate-level advisory/fidelity evidence in a structured bounded form
- advisory flow influences the LLM decision path without replacing Director sovereignty
- unresolved fidelity cannot leave Stage 3 as an unmarked plain `PASS`
- repair instructions survive into the Stage 3 patch loop when compare returns `PASS_WITH_FIX`
- Python remains evidence collector, not final semantic judge

## 10. Verification Plan
- targeted compare-mode tests for candidate-level advisory preservation
- targeted tests for compare result payload fields and fix-scope persistence
- targeted advisory-flow tests through Stage 2 validation pipeline and Stage 3 runtime metadata
- targeted tests for `quality_risk` / `PASS_WITH_FIX` escalation behavior
- `python scripts/check_utf8_hygiene.py ...`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails
- do not build a broad scoring-system replacement
- do not add heuristic sprawl
- do not let Python hard-reject on subjective creative grounds
- keep advisory/fidelity payloads compact and explainable
- do not discard compare feedback on non-`REJECT` outcomes

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition: satisfied on 2026-03-18; temp mirror removed after canonical closure and roadmap refresh
- roadmap dependency: item 3 of `docs/2026-03-18/geuldobi-v2-post-reentry-residual-risk-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Closure Note
- closed on `2026-03-18`
- realized files:
  - `modules/domain/agents/unified_blueprint_validator.py`
  - `modules/domain/agents/director_ensemble.py`
  - `modules/domain/agents/three_phase_blueprint_generator.py`
  - `modules/core/stage3_orchestrator.py`
- realized behavior:
  - compare-mode now prevalidates every candidate before Director selection and exposes compact `python_warnings` / `quality_risk` evidence to the compare prompt
  - Director compare now supports bounded `PASS_WITH_FIX` output and preserves advisory/fix-scope metadata in the returned payload
  - Stage 3 validation metadata now persists `selection_reason`, `verdict_reason`, `quality_risk`, and compact selected-candidate advisory context
- verification:
  - `pytest tests/test_legacy_reentry_reaudit.py -q`
  - `pytest tests/test_director_modules.py -q -k "compare_and_select_"`
  - `pytest tests/test_blueprint_patch_mode.py -q`
  - `pytest tests/test_stage3_orchestrator.py -q -k "director_selection or keeps_500_char_rationale or quality_risk_advisory"`
  - `pytest tests/test_pass_with_fix.py -q -k "compare_path_propagates_fix_scope or compare_and_select_propagates_fix_scope_reasoning or validator_audit_propagates_re_slice_instruction"`
  - `ruff check ...`
  - `ruff format --check ...`
  - `python scripts/check_utf8_hygiene.py ...`
  - `python scripts/ops_validator.py --strict`

## 15. Post-Closure Delta Re-Audit
- re-audited on `2026-03-18` against workspace `d4e96804898491ae67085a327bf35b080ced4364`
- this item still governs compare-mode advisory persistence, but it is not sufficient authority for Blueprint schema compatibility
- schema failure overlap existed in the same Stage 3 surface (`response_schemas.py`, `blueprint_ensemble.py`, `blueprint.py`), and that compatibility remediation is now governed by `docs/2026-03-18/stage3-blueprint-schema-compatibility-execution-ssot.md`
- closure note omission remains documented here rather than rewritten into a false expanded realization claim
