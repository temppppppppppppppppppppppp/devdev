# Geuldobi V2 Stage23 Semantic Transport Restoration Execution SSOT

Date: 2026-03-17
Status: execution-ready
Canonical Path: `docs/2026-03-17/geuldobi-v2-stage23-semantic-transport-restoration-execution-ssot.md`
Temp Mirror Path: `docs/temp/geuldobi-v2-stage23-semantic-transport-restoration-execution-ssot.md`
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: prior lane1~3 and follow-on item edits, runtime log, authority-hygiene changes, survey bundles, and local drafts; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same commit; no active temp queue before opening this item`
Source Survey Docs:
- `docs/2026-03-17/별도 조사2/ssot_stage23-improvement-survey.md`
- `docs/2026-03-17/별도 조사/ssot_integrated-survey.md`
- `docs/2026-03-17/geuldobi-v2-legacy-survey-validity-roi-audit.md`
Side-Effect Coverage: covered
Confidence After 3-Pass Audit: `96%`

## 1. Intent
- restore Stage 2 and Stage 3 semantic payloads that currently collapse into thin operational summaries before Stage 4
- preserve rationale, trigger, justification, and bounded semantic carry-over without violating the Python-collects / LLM-judges invariant
- reuse the already-landed provenance and budget substrate instead of inventing a parallel logging lane

## 2. Baseline Facts
- Arc schemas already carry richer semantic fields than the final Stage 4 context receives
  - `modules/core/response_schemas.py:296`
  - `modules/models/arc.py:98`
- Stage 2 preflight still maps relationship deltas without trigger or justification
  - `modules/core/stage2_preflight.py:1418`
- Stage 2 finalizer still compresses rich state constraints into a short `constraint_summary`
  - `modules/core/stage2_finalizer.py:1039`
- Stage 4 still injects `constraint_summary` as the main hard carry-over path
  - `modules/core/stage4_context_builder.py:2374`
- stop-line extraction and formatting remain tightly truncated
  - `modules/domain/agents/blueprint_constraint_compiler.py:230`
  - `modules/domain/agents/blueprint_constraint_compiler.py:131`
- provenance and budget ledgers already exist and should be extended, not replaced
  - `modules/core/context_advisor.py:197`
  - `modules/core/stage2_preflight.py:1217`
  - `modules/core/stage3_orchestrator.py:1254`
  - `modules/core/stage4_context_builder.py:2795`

## 3. Scope
Included:
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/context_advisor.py`
- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- directly affected tests and operator-visible provenance sinks

Excluded:
- lane2 semantic split already landed
- lane3 `PASS_WITH_FIX` contract already landed
- broad new benchmark or human-feedback systems
- full Stage 0 redesign

## 4. Realization Slices

### Slice A. Relationship rationale survival
- preserve `trigger` / `justification` when Stage 2 maps enriched-block relationship deltas into arc state
- make Stage 4 relationship query / carry-over aware of bounded rationale fields instead of only target + delta

### Slice B. Richer state-constraint carry-over
- preserve selected `state_constraints` / `state_changes` semantic fields beyond short `constraint_summary`
- minimum target set:
  - relationship trigger / justification
  - power-change growth justification
  - foreshadow summary
  - continuity rationale where present

### Slice C. Stop-line truncation normalization
- remove the current double-tight truncation shape as the default path
- make truncation explicit in provenance / overflow metadata when it still occurs

## 5. Acceptance Criteria
- Stage 4 mandatory context can carry more than `constraint_summary` alone for the targeted semantic fields
- relationship changes survive with at least one rationale field (`trigger` or `justification`) when upstream data has it
- stop-line transport no longer silently collapses via the current tight extraction/format pair
- provenance / budget sinks record semantic carry-over or truncation using the already-landed ledger path
- no Python-side final quality authority is added

## 6. Primary Risks
- over-widening Stage 4 payloads into noisy debug blobs
- duplicating semantic payload in multiple incompatible fields
- exposing raw upstream payloads without bounded prioritization

## 7. Execution Notes
- prefer a compact `semantic_carryover` / `rationale_digest` style contract over raw structure dumping
- keep Stage 4 ordering aligned with the landed Tier 0 / 1 / 2 structure
- if a field cannot survive fully, surface that loss via provenance rather than inventing synthetic judgment

## 8. Verification Plan
- targeted Stage 2 preflight tests for relationship rationale survival
- targeted Stage 4 context-builder tests for semantic carry-over presence and truncation accounting
- targeted constraint-compiler tests for stop-line transport limits
- `python scripts/check_utf8_hygiene.py ...`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 9. 3-Pass Audit Notes

### Pass 1. Validity
- the legacy survey diagnosis still matches live code for semantic-loss paths

### Pass 2. Accuracy
- updated to account for already-landed provenance and budget infrastructure

### Pass 3. ROI
- narrowed the item to transport restoration only
- left broader semantic validation and Stage 0 substrate work to separate items
