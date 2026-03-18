# Geuldobi V2 Stage24 Structured Semantic Carryover Execution SSOT

Date: 2026-03-18
Status: closed
Canonical Path: `docs/2026-03-18/geuldobi-v2-stage24-structured-semantic-carryover-execution-ssot.md`
Temp Mirror Path: `removed 2026-03-18`
Commit State:
- Baseline Commit: `8eb5c955408e759c0d45585773604acf4ff2efcb`
- Baseline Dirty Summary: `dirty: 24 tracked/deleted, 1 untracked; hotspots: docs/2026-03-17 closure corrections, modules/core/{stage2_preflight,stage2_finalizer,stage4_context_builder,story_expander,stage01_helpers,constraint_db,response_schemas}.py, modules/domain/agents/{arc_draft_validator,blueprint_constraint_compiler,blueprint_ensemble,director_ensemble,three_phase_blueprint_generator,unified_blueprint_validator}.py, modules/models/blueprint.py, tests/test_legacy_reentry_reaudit.py`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-18/geuldobi-v2-post-reentry-residual-risk-3pass-audit.md`
- `docs/2026-03-17/geuldobi-v2-stage23-semantic-transport-restoration-execution-ssot.md`
Evidence Artifacts:
- `live workspace evidence only; no separate txt/json artifact saved for queue-open`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `96%`
Realization Summary:
- `modules/core/stage2_finalizer.py`: added bounded `semantic_carryover` production and derived `rationale_digest` from that structure
- `modules/domain/agents/blueprint_constraint_compiler.py`: transported normalized `semantic_carryover` through `constraint_block` and prompt serialization
- `modules/domain/agents/blueprint_ensemble.py`: formatted `semantic_carryover` into the live Stage 3 blueprint constraint prompt path
- `modules/core/context_advisor.py`: added a dedicated Stage 4 `arc_semantic_carryover` retrieval slot
- `modules/core/stage4_context_builder.py`: protected the semantic carryover section from early trimming and surfaced `missing_semantic_carryover` when planned carryover did not survive

## 1. Intent
- realize a bounded structured semantic-carryover contract that survives Stage 2 summarization and becomes directly consumable in Stage 4 and related Stage 3 transport
- remove the current over-reliance on free-text `rationale_digest` without dumping raw upstream payloads into prompts

## 2. Baseline Facts
- `modules/core/stage2_finalizer.py` currently emits `constraint_summary` plus text-only `rationale_digest`
- `modules/domain/agents/blueprint_constraint_compiler.py` transports `constraint_summary` and `state_changes_summary`, but not structured rationale/fidelity payload
- `modules/core/stage3_orchestrator.py` and `modules/core/context_advisor.py` do not currently expose a structured semantic-carryover lane into Stage 4 planning
- `modules/core/stage4_context_builder.py` injects `rationale_digest` into Tier 1 text, but trim protection and loss warnings do not treat it as a protected semantic section
- `modules/core/context_advisor.py` already contains budget/provenance ledger substrate that should be reused instead of duplicated

## 3. Scope
Included:
- `modules/core/stage2_finalizer.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/context_advisor.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- targeted tests that cover carryover transport, trim behavior, and Stage 4 consumption

Excluded:
- broad Stage 4 prompt redesign
- raw full-payload dumps into Stage 4
- new benchmark or external feedback systems
- unrelated Stage 0 or Director-scoring work

## 4. Pass 1. Inventory Summary
- main producer hotspot: Stage 2 finalizer
- main transport hotspots: blueprint constraint compiler and Stage 3 orchestrator
- main consumer hotspot: Stage 4 context builder and planner-facing advisor input
- main survivability hotspot: Stage 4 trim protection and loss observability

## 5. Pass 2. Semantic Classification
- Class A: structured semantic carryover producer contract
- Class B: Stage 3 / Stage 4 consumer alignment and bounded retrieval visibility
- Class C: trim-loss observability and regression-proof tests

## 6. Side-Effect Map
- file writes / artifacts: arc artifact shape may gain a bounded new field; reload compatibility matters
- DB / schema / transaction boundaries: not applicable
- JSONL / log / audit sinks: may add bounded operator-visible transport/provenance notes only
- console / UI / operator output: may expose structured-carryover presence or trim-loss warnings
- rollback / recovery / retry: not applicable
- cache / global state: reuse existing context budget/provenance ledgers only; do not add a parallel global sink
- bootstrap fallback / config-env mutation: not applicable

## 7. Realization Architecture
- Stage 2 should produce a bounded structured field such as `semantic_carryover` or an equivalent explicit contract
- the structured field should carry only high-signal slices such as:
  - relationship rationale anchors
  - growth/change justification
  - foreshadow anchors
  - continuity checkpoints
- Stage 3 and Stage 4 should consume that structure directly where transport, work-focus shaping, or retrieval planning need it
- `rationale_digest` may remain as a human-readable compact summary, but it should no longer be the sole semantic bridge
- if any carried semantic section is dropped by Stage 4 trimming, the loss must be explicitly observable

## 8. Execution Tranches
1. define the bounded producer contract in Stage 2 and persist it compatibly
2. thread the contract through Stage 3 transport without duplicating incompatible fields
3. make Stage 4 consume the structure directly and cover trim-loss observability with targeted tests

## 9. Acceptance Criteria
- a bounded structured semantic-carryover contract exists in live code
- Stage 4 consumes that structure directly for at least one semantic path beyond text-only Tier 1 carryover
- Stage 3 transport no longer reduces all richer rationale into summary text alone
- any trim/drop of carried semantic sections becomes operator-visible
- provenance/budget substrate is reused rather than forked
- Python remains collector/formatter only

## 10. Verification Plan
- targeted tests for Stage 2 carryover production and persistence
- targeted tests for Stage 3 transport serialization
- targeted tests for Stage 4 direct structured-carryover consumption
- targeted tests for trim-loss warnings or observability
- `python scripts/check_utf8_hygiene.py ...`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails
- do not introduce a raw semantic blob dump
- do not create a second provenance or budget ledger stack
- do not move final semantic judgment into Python
- keep every structured field bounded and prompt-safe
- do not claim end-to-end structured carryover unless Stage 3 wiring is actually landed

## 12. Temp Queue Notes
- temp status: completed
- cleanup condition: remove temp mirror immediately after this item is realized, closed, and reflected in the governing roadmap
- roadmap dependency: item 1 of `docs/2026-03-18/geuldobi-v2-post-reentry-residual-risk-execution-roadmap.md`

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Realization Evidence
- tests: `pytest tests/test_stage2_finalizer.py -q` -> `25 passed`
- tests: `pytest tests/test_context_advisor.py -q` -> `24 passed`
- tests: `pytest tests/test_stage4_context_builder.py -q` -> `57 passed`
- tests: `pytest tests/test_legacy_reentry_reaudit.py -q` -> `8 passed`
- tests: `pytest tests/test_blueprint_patch_mode.py -q` -> `9 passed`
- tests: `pytest tests/test_tf10_episode_details.py -q` -> `16 passed`
- `ruff check` on touched code/tests: pass
- `ruff format` on touched code/tests: clean after format
- `python scripts/check_utf8_hygiene.py ...`: pass
- `python scripts/sync_temp_queue_state.py`: re-synced after temp mirror removal
- `python scripts/ops_validator.py --strict`: pass

## 15. Closure Note
Date: 2026-03-18
Status: closed

### Outcome
- Stage 2 now persists a bounded `semantic_carryover` contract instead of relying on text-only carryover alone
- Stage 3 transport carries that structure through `constraint_block` and live blueprint prompt formatting
- Stage 4 now consumes the structure directly through a dedicated retrieval slot and emits `missing_semantic_carryover` if planned carryover disappears before final mandatory context

### Residual Risks
- the structured lane is bounded and compact by design; it does not attempt a universal semantic dump
- Stage 3 work-focus shaping in `stage3_orchestrator.py` still remains summary-first; this item closed the direct blueprint transport path rather than every possible semantic entrypoint

### Temp Cleanup
- execution SSOT mirror removed: yes (`docs/temp/geuldobi-v2-stage24-structured-semantic-carryover-execution-ssot.md`)
- roadmap mirror retained: yes (`docs/temp/execution-roadmap.md`) because the bundle still has active items
- queue-state refreshed: yes (`docs/temp/queue-state.json`)
