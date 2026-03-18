# Geuldobi V2 Post-Reentry Residual Risk Aggregate Execution Roadmap

Date: 2026-03-18
Status: completed
Canonical Path: `docs/2026-03-18/geuldobi-v2-post-reentry-residual-risk-execution-roadmap.md`
Temp Mirror Path: `removed 2026-03-18 after queue exhaustion`
Commit State:
- Baseline Commit: `8eb5c955408e759c0d45585773604acf4ff2efcb`
- Baseline Dirty Summary: `dirty: 24 tracked/deleted, 1 untracked; hotspots: docs/2026-03-17 closure corrections, modules/core/{stage2_preflight,stage2_finalizer,stage4_context_builder,story_expander,stage01_helpers,constraint_db,response_schemas}.py, modules/domain/agents/{arc_draft_validator,blueprint_constraint_compiler,blueprint_ensemble,director_ensemble,three_phase_blueprint_generator,unified_blueprint_validator}.py, modules/models/blueprint.py, tests/test_legacy_reentry_reaudit.py`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Queue Snapshot:
- none; residual-risk queue exhausted on `2026-03-18`
Confidence After 3-Pass Audit: `96%`

## 1. Purpose
- govern the fresh residual-risk bundle extracted after the closed 2026-03-17 reentry queue
- keep this as the only SSOT roadmap for the newly opened active temp queue
- prevent follow-on implementation from reusing the already-closed historical roadmap

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `stage24-structured-semantic-carryover` | `docs/2026-03-18/geuldobi-v2-stage24-structured-semantic-carryover-execution-ssot.md` | `removed 2026-03-18` | completed | realized: bounded `semantic_carryover` producer + Stage 3 transport + Stage 4 retrieval slot + loss warning |
| `stage0-llm-mediated-completeness-retry` | `docs/2026-03-18/geuldobi-v2-stage0-llm-mediated-completeness-retry-execution-ssot.md` | `removed 2026-03-18` | completed | realized: bounded Stage 0 review facts + shared fresh/extension gate + Stage 2 consumer-backed roadmap readiness |
| `stage23-director-advisory-fidelity-escalation` | `docs/2026-03-18/geuldobi-v2-stage23-director-advisory-fidelity-escalation-execution-ssot.md` | `removed 2026-03-18` | completed | realized: compare-mode candidate prevalidation bridge + Director `PASS_WITH_FIX` support + Stage 3 quality-risk persistence |

## 3. Dependency Graph
- `stage24-structured-semantic-carryover -> stage23-director-advisory-fidelity-escalation`
- `stage0-llm-mediated-completeness-retry -> stage23-director-advisory-fidelity-escalation`
- shared substrate:
  - existing provenance/budget ledgers
  - existing typed `scene_breakdown` schema/model path
  - current Stage 0 completeness warning facts
- merge opportunities:
  - none for implementation; keep realization sequential and queue-controlled

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`

1. `stage24-structured-semantic-carryover`
2. `stage0-llm-mediated-completeness-retry`
3. `stage23-director-advisory-fidelity-escalation`

## 5. Per-Item Plan

### stage24-structured-semantic-carryover
- goal: make richer rationale/fidelity structure available beyond text-only `rationale_digest`
- prerequisites: none beyond current closed reentry fixes
- execution notes: completed on 2026-03-18; reused existing provenance/budget substrate, wired a real Stage 4 consumer path, and added loss observability
- completion signal: satisfied
- temp cleanup action: completed; temp mirror removed and queue refreshed

### stage0-llm-mediated-completeness-retry
- goal: turn warning-only completeness states into bounded LLM-mediated retry or stop-save escalation
- prerequisites: none
- execution notes: completed on 2026-03-18; added deterministic review facts, bounded Stage 0 retry/stop-save gate, a shared extension/save path, and consumer-backed roadmap readiness checks at Stage 2 entry
- completion signal: satisfied
- temp cleanup action: completed; temp mirror removed and queue refreshed

### stage23-director-advisory-fidelity-escalation
- goal: make candidate-level advisory/fidelity evidence visible to compare-mode selection and bounded escalation
- prerequisites: prefer completion of items 1 and 2 first
- execution notes: completed on 2026-03-18; added pre-compare candidate prevalidation, compact compare advisory visibility, compare-mode `PASS_WITH_FIX` support, and Stage 3 runtime persistence for `quality_risk` / selected-candidate advisory context
- completion signal: satisfied
- temp cleanup action: completed; item temp mirror removed and aggregate roadmap retired

## 6. Shared Risks and Side-Effects
- shared write paths: `modules/core/` and `modules/domain/agents/` prompt/control surfaces
- shared DB/schema touchpoints: none expected; work should remain in runtime contracts and prompt assembly
- shared logs/UI surfaces: validator, Stage 0 operator warnings, compare-mode summaries
- rollback/recovery concerns: keep retry counts bounded and avoid parallel state ledgers
- queue collision or ordering risks: Item 3 should not be realized before Item 1 and Item 2 are revalidated and, preferably, completed

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `stage24-structured-semantic-carryover` | completed | 2026-03-18 | none |
| `stage0-llm-mediated-completeness-retry` | completed | 2026-03-18 | none |
| `stage23-director-advisory-fidelity-escalation` | completed | 2026-03-18 | none |

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- remove `docs/temp/queue-state.json` if present
- leave `docs/temp/README.md`
