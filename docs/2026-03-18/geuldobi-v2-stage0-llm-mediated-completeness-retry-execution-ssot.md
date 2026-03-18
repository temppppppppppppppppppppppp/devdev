# Geuldobi V2 Stage0 LLM-Mediated Completeness Retry Execution SSOT

Date: 2026-03-18
Status: closed
Canonical Path: `docs/2026-03-18/geuldobi-v2-stage0-llm-mediated-completeness-retry-execution-ssot.md`
Temp Mirror Path: `removed 2026-03-18`
Commit State:
- Baseline Commit: `8eb5c955408e759c0d45585773604acf4ff2efcb`
- Baseline Dirty Summary: `dirty: 24 tracked/deleted, 1 untracked; hotspots: docs/2026-03-17 closure corrections, modules/core/{stage2_preflight,stage2_finalizer,stage4_context_builder,story_expander,stage01_helpers,constraint_db,response_schemas}.py, modules/domain/agents/{arc_draft_validator,blueprint_constraint_compiler,blueprint_ensemble,director_ensemble,three_phase_blueprint_generator,unified_blueprint_validator}.py, modules/models/blueprint.py, tests/test_legacy_reentry_reaudit.py`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-18/geuldobi-v2-post-reentry-residual-risk-3pass-audit.md`
- `docs/2026-03-17/geuldobi-v2-stage0-stage2-substrate-hardening-execution-ssot.md`
Evidence Artifacts:
- `live workspace evidence only; no separate txt/json artifact saved for queue-open`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `96%`
Realization Summary:
- `modules/core/stage0/story_expander.py`: added deterministic Stage 0 review facts, bounded `PASS/RETRY/REJECT` review path, and widened detail-generation continuity carry-over from one block to a bounded multi-block window
- `modules/core/stage0_handoff.py`: centralized `plot_roadmap` normalization and Stage 2 consumer-backed readiness validation so `title/summary` alone no longer masquerade as handoff readiness
- `modules/core/stage0/__init__.py`: fresh concept generation now loops through the bounded Stage 0 review gate before any `stage0_output` save occurs
- `modules/core/stage01_helpers.py`: block extension now reuses the same Stage 0 review gate and a shared persistence helper, preserving `treatment_extended.json` while blocking non-ready handoff saves
- `modules/core/stage2_orchestrator.py` and `main_a.py`: Stage 2/frontier entrypoints now reject invalid or summary-only `plot_roadmap` payloads instead of checking only for non-empty lists
- `tests/test_stage0_fixes.py` and `tests/test_stage01_helpers.py`: added regressions for bounded stop-save, stronger roadmap validation, and extension persistence routing

## 1. Intent
- convert weak Stage 0 completeness warnings into a bounded LLM-mediated retry or stop-save path
- harden continuity handoff without giving Python creative authority over whether a Bible or Treatment is "good"
- collapse duplicated roadmap gate authority so fresh generation and extension follow the same readiness rule

## 2. Baseline Facts
- `modules/core/stage0/story_expander.py` records `_completeness_warnings`, but warning-only flow allows weak Bible outputs to proceed
- Stage 0 detail generation currently injects only immediate previous-block continuity context during `_generate_details()`
- `modules/core/stage0/story_expander.py` can still merge extension batches into `self.treatment` without an automatic continuity reject path
- `modules/core/stage0/__init__.py` and `modules/core/stage01_helpers.py` both own pieces of roadmap injection/gating, which is a drift risk
- `modules/core/stage01_helpers.py` currently treats `title` or `summary` as sufficient roadmap content even though downstream consumers rely on a richer structure
- current Stage 2 entrypoints still mainly gate on non-empty `plot_roadmap`

## 3. Scope
Included:
- `modules/core/stage0/story_expander.py`
- `modules/core/stage01_helpers.py`
- `modules/core/stage0/__init__.py`
- `main_a.py` readiness touchpoints if required
- targeted tests for Stage 0 retry, save gating, and continuity handoff

Excluded:
- broad Stage 0 UX redesign
- hard-fail Python quality scoring
- unrelated style-cache or POV-policy work
- downstream Stage 3 Director selection logic

## 4. Pass 1. Inventory Summary
- completeness evidence hotspot: `story_expander.py`
- handoff/save hotspot: `stage01_helpers.py`
- duplicated gate authority hotspot: `stage0/__init__.py`
- downstream readiness hotspot: `main_a.py` and related readiness consumers

## 5. Pass 2. Semantic Classification
- Class A: deterministic completeness and continuity evidence aggregation in Python
- Class B: LLM-mediated retry or stop-save escalation path
- Class C: shared roadmap gate authority and save-time enforcement

## 6. Side-Effect Map
- file writes / artifacts: `treatment_generated.json`, `treatment_extended.json`, `stage0_output/treatment.json`, and `anchors[bible].plot_roadmap`
- DB / schema / transaction boundaries: not applicable
- JSONL / log / audit sinks: Stage 0 warning/retry logs may gain bounded escalation markers
- console / UI / operator output: operator-visible warning, retry, or stop-save messages are expected
- rollback / recovery / retry: bounded retry loop or escalation path is in scope
- cache / global state: existing Stage 0 manager state only; no new long-lived cache
- bootstrap fallback / config-env mutation: not applicable

## 7. Realization Architecture
- Python should continue to gather deterministic evidence only:
  - missing required fields
  - count mismatches
  - previous accepted batch snapshot
  - candidate batch snapshot
  - save/handoff target state
- those facts should feed a bounded LLM judge path that can return `PASS`, `RETRY`, or `REJECT`
- auto-retry must be bounded and should stop save/handoff after max attempts rather than persisting warning-only artifacts
- roadmap readiness should match real downstream use, not just `title` or `summary`
- fresh generation and extension should share one gate path before mutating `self.treatment` or saving files

## 8. Execution Tranches
1. formalize bounded retry/escalation triggers from existing warning facts and continuity evidence
2. add an LLM-mediated retry or stop-save review path that consumes those facts
3. unify roadmap gate authority for fresh generation and extension, then cover the new flow with targeted tests

## 9. Acceptance Criteria
- weak completeness states can trigger a bounded retry or stop-save path
- Python still collects evidence only and does not perform final creative acceptance
- continuity handoff is stronger than immediate-previous-block only
- fresh generation and extension use the same gate path before save/handoff
- roadmap readiness reflects real downstream consumer needs rather than a loose `title`/`summary` proxy alone

## 10. Verification Plan
- targeted tests for completeness warning aggregation and retry trigger conditions
- targeted tests for Stage 0 continuity carryover and extension gating
- targeted tests for Stage 01 roadmap readiness enforcement
- targeted tests for Stage 2 readiness surfaces affected by the stronger gate
- `python scripts/check_utf8_hygiene.py ...`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails
- do not introduce Python hard-reject creative scoring
- do not expand Stage 0 into a broad product redesign
- keep retry counts bounded
- keep continuity carryover compact and prompt-safe
- do not let file-presence alone masquerade as readiness after this gate is introduced

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition: remove temp mirror immediately after this item is realized, closed, and reflected in the governing roadmap
- roadmap dependency: item 2 of `docs/2026-03-18/geuldobi-v2-post-reentry-residual-risk-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Realization Evidence
- tests: `pytest tests/test_stage0_fixes.py -q` -> `16 passed`
- tests: `pytest tests/test_stage01_helpers.py -q` -> `46 passed`
- tests: `pytest tests/test_stage01_fixes.py -q` -> `19 passed`
- tests: `pytest tests/test_stage2_orchestrator.py -q` -> `2 passed`
- tests: `pytest tests/test_run_stage34_canary.py -q` -> `4 passed`
- tests: `pytest tests/test_auto_frontier_lag_harness.py -q` -> `10 passed`
- aggregate targeted regression shard: `97 passed`
- `python -m py_compile` on touched code/tests: pass
- `ruff check` on touched code/tests: pass
- `ruff format --check` on touched code/tests: pass
- `python scripts/check_utf8_hygiene.py ...`: pass
- `python scripts/sync_temp_queue_state.py`: queue refreshed after mirror removal
- `python scripts/ops_validator.py --strict`: pass

## 15. Closure Note
Date: 2026-03-18
Status: closed

### Outcome
- weak Stage 0 completeness states can now trigger bounded retry or stop-save instead of falling straight through to save/handoff
- fresh generation and block extension now share the same Stage 0 review and persistence authority instead of drifting across separate save paths
- `plot_roadmap` readiness now tracks fields Stage 2 can actually consume, so `title/summary`-only placeholders are blocked before Stage 2 entry

### Residual Risks
- the preferred path remains LLM-mediated; when the judge is unavailable the fallback is intentionally deterministic and conservative rather than creative
- manual Bible-only import remains saveable without treatment because that path is not automatically treated as Stage 2-ready handoff
- the continuity carry-over is bounded to a small recent window by design; it reduces blind seams but does not attempt a full long-range continuity judge

### Temp Cleanup
- execution SSOT mirror removed: yes (`docs/temp/geuldobi-v2-stage0-llm-mediated-completeness-retry-execution-ssot.md`)
- roadmap mirror retained: yes (`docs/temp/execution-roadmap.md`) because item 3 remains active
- queue-state refreshed: yes (`docs/temp/queue-state.json`)
