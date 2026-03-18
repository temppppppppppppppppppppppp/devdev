# Stage 3 Blueprint Schema Compatibility Execution SSOT

Date: 2026-03-18
Status: active
Canonical Path: `docs/2026-03-18/stage3-blueprint-schema-compatibility-execution-ssot.md`
Temp Mirror Path: `removed 2026-03-18 after closure`
Commit State:
- Baseline Commit: `d4e96804898491ae67085a327bf35b080ced4364`
- Baseline Dirty Summary: `dirty: 3 deleted, 4 untracked; hotspots: docs/2026-03-11 PDFs, docs/2026-03-18/stage3-blueprint* docs, projects/0_260318`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-18/stage3-blueprint-failure-deepdive-investigation.md`
- `docs/2026-03-18/geuldobi-v2-stage23-director-advisory-fidelity-escalation-execution-ssot.md`
- `docs/2026-03-18/geuldobi-v2-post-reentry-residual-risk-3pass-audit.md`
- `docs/2026-03-18/geuldobi-v2-post-reentry-residual-risk-execution-roadmap.md`
- `docs/2026-03-18/geuldobi-v2-post-reentry-residual-risk-execution-closure.md`
Evidence Artifacts:
- `projects/0_260318/logs/session/llm_io.jsonl` (`BlueprintEnsembleGenerator` failure 30건, 모두 `gemini-2.5-pro`, error=`additionalProperties is not supported in the Gemini API.`)
- `projects/0_260318/logs/session/ui_events.jsonl:255-275`
- `projects/0_260318/logs/session/ui_events.jsonl` session `20260318_114610`: Stage 2 PASS -> Stage 3 `FAILED (score=0)` at `2026-03-18 12:02:19`
- `projects/0_260318/logs/session/llm_io.jsonl` session `20260318_114610`: 30 BlueprintEnsembleGenerator attempts after the schema hotfix, 29 successful JSON responses + 1 disconnect, but successful responses all carried `scene_breakdown={}` and omitted broader Blueprint fields
- live code in `modules/core/response_schemas.py`, `modules/domain/agents/blueprint_ensemble.py`, `modules/domain/agents/three_phase_blueprint_generator.py`, `modules/core/stage3_orchestrator.py`, `modules/models/blueprint.py`
- local package state: `google-genai 1.57.0`, `google-generativeai 0.8.6`, `requirements.txt` expects `google-genai>=1.60.0`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `96%`

## 1. Intent
- unblock Stage 3 Blueprint generation without breaking the live `scene_breakdown` dict contract
- correct the current execution authority so code changes are governed by live code and live logs, not the earlier ARRAY-migration hypothesis
- stop schema-incompatible retry burn so identical API rejections do not consume the full Stage 3 retry budget

## 2. Baseline Facts
- direct failure surface is `modules/core/response_schemas.py:554-557`, where `BLUEPRINT_SCHEMA.scene_breakdown` uses `additionalProperties=BLUEPRINT_SCENE_ENTRY_SCHEMA`
- live call site is `modules/domain/agents/blueprint_ensemble.py:583-590`, which passes `response_schema=BLUEPRINT_SCHEMA` into Gemini on every ensemble candidate
- `projects/0_260318/logs/session/llm_io.jsonl` contains 30 BlueprintEnsembleGenerator failures with the same error string; the checked evidence file does not show a successful backup-model attempt for this incident
- `projects/0_260318/logs/session/ui_events.jsonl:266-268` plus `modules/core/stage3_orchestrator.py:1344-1347` explain the operator-visible `FAILED (score=0)` result: Stage 3 falls back to score `0` when Phase 2 never produces a selected score
- live runtime contract still expects `scene_breakdown` as a dict map:
  - `modules/models/blueprint.py`
  - `modules/validation/blocking_validator_scene_checks.py`
  - `modules/core/prompt_builder.py`
  - `modules/core/writer_template.py`
  - `modules/core/stage4_context_builder.py`
- `docs/2026-03-18/geuldobi-v2-stage23-director-advisory-fidelity-escalation-execution-ssot.md` overlaps the same Stage 3 surface, but its closure note omits `response_schemas.py`, `blueprint_ensemble.py`, and `blueprint.py`; treat that closed doc as insufficient authority for schema compatibility

## 3. Scope
Included:
- `modules/core/response_schemas.py`
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- targeted tests covering schema compatibility and retry containment

Excluded:
- `scene_breakdown` dict-to-array contract migration
- broad Stage 3 prompt redesign
- Stage 0 / Stage 2 substrate changes
- Director compare scoring redesign
- provider package upgrade as the sole remediation path

## 4. Pass 1. Inventory Summary
- root-cause hotspot: `modules/core/response_schemas.py`
- API submission hotspot: `modules/domain/agents/blueprint_ensemble.py`
- retry-burn hotspot: `modules/domain/agents/three_phase_blueprint_generator.py`
- operator symptom hotspot: `modules/core/stage3_orchestrator.py`
- contract-preservation hotspots: `modules/models/blueprint.py` and dict-oriented downstream consumers

## 5. Pass 2. Semantic Classification
- Class A, P0: remove the schema feature that current live Gemini path rejects while keeping Stage 3 output shape stable
- Class B, P1: classify schema-incompatible failures explicitly and stop wasting full retry budgets on deterministic API rejection
- Class C, P1: repair document authority drift so later operators do not reuse the earlier ARRAY-migration plan as if it were implementation-safe

## 6. Side-Effect Map
- file writes / artifacts: no persisted blueprint artifact shape change is allowed; saved `scene_breakdown` remains dict-shaped
- DB / schema / transaction boundaries: not applicable
- JSONL / log / audit sinks: failure classification may become more specific via `schema_incompatible`
- console / UI / operator output: Stage 3 may fail fast on schema-incompatible errors instead of logging repeated generic generation failures
- rollback / recovery / retry: deterministic schema incompatibility should short-circuit the retry loop; normal creative-quality retries remain intact
- cache / global state: `BLUEPRINT_SCHEMA` is a module-level contract used by every Stage 3 blueprint call
- bootstrap fallback / config-env mutation: not applicable

## 7. Pass 3. Realization Architecture
- keep `scene_breakdown` as a dict map in runtime contracts and downstream consumers
- remove live Gemini dependence on `additionalProperties` for the Blueprint response schema instead of forcing an array migration through the codebase
- keep typed scene expectations in Python-side model validation and downstream processing rather than in the current API schema field that is failing
- extend BaseAgent error classification with a dedicated `schema_incompatible` branch for `"not supported"` schema errors
- when Phase 2 fails with `schema_incompatible`, stop the Stage 3 retry loop immediately and mark the failure cause in pipeline metadata

## 8. Execution Tranches
1. patch the governing execution doc and mirror it into `docs/temp/`
2. make `BLUEPRINT_SCHEMA.scene_breakdown` Gemini-compatible without changing the dict runtime contract
3. classify schema-incompatible errors and fast-fail deterministic Phase 2 schema rejection
4. verify with targeted tests plus UTF-8 and ops validation

## 9. Acceptance Criteria
- `BLUEPRINT_SCHEMA.scene_breakdown` no longer uses `additionalProperties`
- live Stage 3 blueprint runtime contract remains dict-based
- BaseAgent can classify `"additionalProperties is not supported"` as `schema_incompatible`
- Stage 3 no longer burns all retries when the failure cause is deterministic schema incompatibility
- the governing execution doc reflects actual evidence counts, current temp state, and current workspace authority

## 10. Verification Plan
- `pytest tests/test_legacy_reentry_reaudit.py -q`
- `pytest tests/test_base_agent.py -q -k "schema_incompatible"`
- `pytest tests/test_blueprint_patch_mode.py -q -k "schema_incompatible"`
- `python scripts/check_utf8_hygiene.py docs/2026-03-18/stage3-blueprint-failure-deepdive-investigation.md docs/2026-03-18/stage3-blueprint-schema-compatibility-execution-ssot.md modules/core/response_schemas.py modules/domain/agents/base_agent.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/three_phase_blueprint_generator.py tests/test_legacy_reentry_reaudit.py tests/test_base_agent.py tests/test_blueprint_patch_mode.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails
- do not convert `scene_breakdown` to an array in this fix tranche
- do not rely on a provider package upgrade alone as proof of remediation
- do not broaden the patch into a general Stage 3 prompt refactor
- do not let Python take final creative judgment authority
- do not claim backup-model evidence that is not present in the checked log artifact

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition: remove the temp mirror after realization is closed and validator state is clean
- roadmap dependency: none; this is a focused single-item execution doc

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: this document is the re-audited authority for the focused patch below

## 14. Realization Summary
- `modules/core/response_schemas.py`: removed `additionalProperties` from the live Blueprint response schema while preserving `scene_breakdown` as an object map
- `modules/domain/agents/base_agent.py`: added `schema_incompatible` classification and recovery hint
- `modules/domain/agents/blueprint_ensemble.py`: resets `last_error_type` per ensemble attempt so deterministic failure metadata does not leak across runs
- `modules/domain/agents/three_phase_blueprint_generator.py`: records Phase 2 `error_type` and fast-fails deterministic schema incompatibility instead of consuming the full retry budget
- `tests/test_legacy_reentry_reaudit.py`: updated schema expectation to the compatibility-preserving object contract
- `tests/test_base_agent.py`: added schema incompatibility classification coverage
- `tests/test_blueprint_patch_mode.py`: added retry-loop fast-fail coverage

## 15. Realization Evidence
- `pytest tests/test_legacy_reentry_reaudit.py -q` -> `8 passed`
- `pytest tests/test_base_agent.py -q -k schema_incompatible_error` -> `1 passed, 73 deselected`
- `pytest tests/test_blueprint_patch_mode.py -q -k schema_incompatible_failure_breaks_retry_loop` -> `1 passed, 10 deselected`
- `python -m py_compile modules/core/response_schemas.py modules/domain/agents/base_agent.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/three_phase_blueprint_generator.py` -> pass
- `python scripts/check_utf8_hygiene.py ...` on touched docs/code/tests -> pass
- `python scripts/ops_validator.py --strict` -> pass

## 16. Closure Note
- closed on `2026-03-18`
- result: Stage 3 no longer depends on the rejected `additionalProperties` keyword, and deterministic schema incompatibility now fails fast with explicit metadata instead of draining the full retry loop
- residual risk: the runtime still relies on the local `google-genai 1.57.0` path; if future schema features reintroduce provider drift, they should be gated by focused compatibility tests before reuse in Stage 3
- temp cleanup: remove `docs/temp/stage3-blueprint-schema-compatibility-execution-ssot.md` after this canonical closure is saved and validator state remains clean

## 17. Reopen Delta (2026-03-18)
- live rerun for project `0_260318` showed that the first compatibility patch solved the API rejection but introduced a second-order contract loss: Gemini treated `scene_breakdown` like an empty structured object and emitted `scene_breakdown={}` across successful responses
- the visible symptom stayed the same (`FAILED (score=0)`), but the failure phase changed:
  - before hotfix: Phase 2 died at API submission with `additionalProperties is not supported`
  - after hotfix v1: Phase 2 returned JSON, yet Python pre-validation rejected every candidate for `scene_count < 3`, so Stage 3 still exhausted retries and ended `final_verdict=FAILED`
- amended remediation:
  - replace the empty-object `scene_breakdown` schema with explicit `scene_1..scene_5` properties
  - widen the scene entry schema to include live prompt fields such as `type`, `title`, `description`, and `tension_level`
  - widen the top-level Blueprint schema to include `title`, `start_location`, `end_location`, `ending_hook`, `protagonist_state`, and `ending_state` so structured output does not silently trim them
- keep this SSOT active until a fresh Stage 3 rerun confirms that structured responses now carry non-empty scene slots and clear Python validation
