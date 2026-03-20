# Stage4 Context Builder build_mandatory_context Decomposition Execution SSOT

Date: 2026-03-20
Status: closed
Canonical Path: `docs/2026-03-20/stage4-context-builder-build-mandatory-context-decomposition-execution-ssot.md`
Temp Mirror Path: removed after closure
Commit State:
- Baseline Commit: `7686b6c0d9795593c58e958ce068369e168d6f3f`
- Baseline Dirty Summary: `dirty: pre-existing stage4/smoke/doc changes, project artifact churn, docs/mmmm intake; no active temp execution queue at start`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-20/long-function-decomposition-live-reaudit-3pass-audit.md`
- `docs/2026-03-20/long-function-decomposition-hotspot-survey-3pass-audit.md`
Evidence Artifacts:
- `modules/core/stage4_context_builder.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_continuity_packet.py`
- `tests/test_chief_writer_context.py`
Side-Effect Coverage: covered

## 1. Intent
- Decompose `build_mandatory_context` into stable section-assembly helpers while preserving the current Stage 4 context payload contract.
- Reduce branch density without opening Stage 4 governance or retry-policy changes.

## 2. Baseline Facts
- This surface is smaller than the biggest long functions, but it carries the highest branch density among top hotspots.
- It is also one of the best-protected hotspots by direct unit tests.
- The file already contains many nearby helper methods, which makes same-file extraction realistic.

## 3. Scope
Included:
- `modules/core/stage4_context_builder.py`
- same-file helper extraction and section assembly cleanup
- regression alignment for existing context-builder tests

Excluded:
- Stage 4 retry policy changes
- writer prompt contract redesign
- retrieval algorithm rewrites
- director grading semantics

## 4. Pass 1. Inventory Summary
- mandatory baseline context
- work-focus and slot summary path
- stage2 failure context and ambient hints
- world state / timeline / fact ledger / canonical constraints layering
- retrieval observation and coverage-warning assembly

## 5. Pass 2. Semantic Classification
- Class A: tier-0 canonical/world/fact section builders
- Class B: work-focus / retrieval / authority-note section builders
- Class C: final dict assembly and warning bookkeeping

## 6. Side-Effect Map
- file writes / artifacts: none
- DB / schema / transaction boundaries: read-only retrievals and project DB reads
- JSONL / log / audit sinks: retrieval observations and HUD anomaly observations
- console / UI / operator output: non-fatal warning logs
- rollback / recovery / retry: not applicable
- cache / global state: ctx reads, planner/retrieval side observations
- bootstrap fallback / config-env mutation: not applicable

## 7. Realization Architecture
- keep `build_mandatory_context` as the public coordinator
- extract section-group helpers, not a new context subsystem
- preserve returned dict keys and existing bounded warning behavior

## 8. Execution Tranches
1. Extract tiered section-group builders around canonical/world/fact inputs.
2. Extract work-focus, retrieval, and coverage-warning assemblers.
3. Reduce final method to orchestration and returned-payload assembly.

## 9. Acceptance Criteria
- return payload shape remains unchanged
- existing Stage 4 context-builder tests continue to pass
- retrieval observation / HUD anomaly side-effects remain intact

## 10. Verification Plan
- `python -m pytest tests/test_stage4_context_builder.py -q`
- `python -m pytest tests/test_continuity_packet.py -q`
- `python -m pytest tests/test_chief_writer_context.py -q`

## 11. Guardrails
- do not merge this item with Stage 4 sovereignty or retry-policy work
- do not change retrieval budgets or warning thresholds here
- do not split into new cross-file abstractions in tranche 1

## 12. Temp Queue Notes
- temp status: closed
- cleanup condition: completed; temp mirror removed after realization and closure
- roadmap dependency: third item; independent enough to run after the Stage 2 tranche pair

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Progress Note
- 2026-03-20 realization tranche 1 completed:
  - extracted tier-0 canonical/world/fact section assembly into `_build_tier0_mandatory_sections`
  - moved mandatory baseline, arc constraint summary, world-state summary, timeline, fact-ledger summary, canonical block, continuity packet, and NPC boundary assembly out of `build_mandatory_context`
- 2026-03-20 realization tranche 2 completed:
  - extracted SC retrieval collection into `_collect_stage4_retrieval_context`
  - extracted coverage-warning recomposition and retrieval observation bookkeeping into `_compose_context_with_retrieval_coverage`
  - reduced `build_mandatory_context` to helper dispatch for work-focus, retrieval, and coverage assembly
- 2026-03-20 realization tranche 3 completed:
  - extracted tier-1/tier-2 auxiliary assembly into `_build_tier12_auxiliary_sections`
  - moved stage2 failure context, ambient hints, series/volume summaries, genre_ext, state-tracker summaries, lookback, foreshadow, semantic plot guard, pacing, narrative summaries, and future-arc context out of `build_mandatory_context`
- Closure note:
  - `build_mandatory_context` now acts as a public coordinator over tier-0, auxiliary tier-1/tier-2, retrieval, and coverage helpers
  - return payload shape and Stage 4 context side-effects were preserved under direct regression coverage
