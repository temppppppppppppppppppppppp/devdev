# Geuldobi V2 Stage23 Semantic Transport Restoration Execution SSOT

Date: 2026-03-17
Status: closed
Canonical Path: `docs/2026-03-17/geuldobi-v2-stage23-semantic-transport-restoration-execution-ssot.md`
Temp Mirror Path: `removed 2026-03-18`
Commit State:
- Baseline Commit: `8eb5c955408e759c0d45585773604acf4ff2efcb`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Realization Summary:
- Slice A: `stage2_preflight.py:1418` — trigger/justification 매핑 추가
- Slice B: `stage2_finalizer.py:1043` — rationale_digest 생성 (관계/성장/복선/연속성)
- Slice B: `stage4_context_builder.py:2377` — rationale_digest tier1 주입
- Slice C: `blueprint_constraint_compiler.py:131,238,247` — 이중 절삭 완화 (300→800 추출, 200→500 포맷) + truncation provenance
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
- Stage 4 now has tiered mandatory-context packing and budget/provenance ledgers, but still injects `constraint_summary` as the main hard carry-over path
  - `modules/core/stage4_context_builder.py:1560`
  - `modules/core/stage4_context_builder.py:2374`
- stop-line extraction and formatting remain tightly truncated
  - `modules/domain/agents/blueprint_constraint_compiler.py:230`
  - `modules/domain/agents/blueprint_constraint_compiler.py:131`
- provenance and budget ledgers already exist and were reused as substrate; this item does not add a dedicated semantic sink
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
- directly affected tests and operator-visible stop-line output

Excluded:
- lane2 semantic split already landed
- lane3 `PASS_WITH_FIX` contract already landed
- broad new benchmark or human-feedback systems
- full Stage 0 redesign

## 4. Realization Slices

### Slice A. Relationship rationale survival
- preserve `trigger` / `justification` when Stage 2 maps enriched-block relationship deltas into arc state
- make Stage 4 carry-over aware of bounded rationale fields via `rationale_digest` without widening the raw relationship query path

### Slice B. Richer state-constraint carry-over
- preserve selected `state_constraints` / `state_changes` semantic fields beyond short `constraint_summary`
- minimum target set:
  - relationship trigger / justification
  - power-change growth justification
  - foreshadow summary
  - continuity rationale where present

### Slice C. Stop-line truncation normalization
- remove the current double-tight truncation shape as the default path
- make truncation explicit in operator-visible transported output when it still occurs

## 5. Acceptance Criteria
- Stage 4 mandatory context can carry more than `constraint_summary` alone for the targeted semantic fields
- relationship delta backfill preserves or merges at least one rationale field (`trigger` or `justification`) when upstream data has it
- stop-line transport no longer silently collapses via the current tight extraction/format pair
- existing provenance / budget substrate is reused without adding a parallel sink, and truncation remains operator-visible in transported output
- no Python-side final quality authority is added

## 6. Primary Risks
- over-widening Stage 4 payloads into noisy debug blobs
- duplicating semantic payload in multiple incompatible fields
- exposing raw upstream payloads without bounded prioritization

## 7. Execution Notes
- prefer a compact `semantic_carryover` / `rationale_digest` style contract over raw structure dumping
- keep Stage 4 ordering aligned with the landed Tier 0 / 1 / 2 structure
- if a field cannot survive fully, surface that loss in transported output rather than inventing synthetic judgment

## 8. Verification Plan
- targeted Stage 2 preflight tests for relationship rationale survival
- targeted Stage 4 context-builder tests for semantic carry-over presence and truncation accounting
- targeted constraint-compiler tests for stop-line transport limits
- `python scripts/check_utf8_hygiene.py ...`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py --strict`

## 9. 3-Pass Audit Notes

### Pass 1. Validity
- the legacy survey diagnosis still matches live code for semantic-loss paths after current-head revalidation

### Pass 2. Accuracy
- updated to account for already-landed provenance / budget infrastructure and later Stage 4 tiered packing changes

### Pass 3. ROI
- narrowed the item to transport restoration only
- left broader semantic validation and Stage 0 substrate work to separate items

## 10. Realization Evidence
- tests: 231 passed (5 shards: preflight 27, finalizer 24, context_builder 56, constraint/stopline 44, related 80)
- ruff: 0 violations
- ruff format: clean after auto-format
- UTF-8 hygiene: flagged lines are pre-existing (L118-175, L1651, L423), none from this realization
- ops_validator --strict: PASS (errors=0, warnings=0)
- queue-state.json: synced during the active queue and later removed after bundle closure

## 11. Closure Note
Date: 2026-03-18
Status: closed

### Verification Summary
- re-audit corrected the earlier overclaim of a dedicated semantic carry-over sink; live code reuses existing substrate and surfaces truncation in transported stop-line text only
- relationship delta backfill now merges missing `trigger` / `justification` into pre-existing `relationship_changes` entries instead of only filling empty lists
- targeted tests, ruff, UTF-8 hygiene, queue sync, and ops validator were recorded as passing
- queue closure cleanup was completed after canonical roadmap / SSOT status updates

### Residual Risks
- `rationale_digest` is now visible to Stage 4, but actual LLM uptake can still vary
- extremely long stop-line payloads may still truncate, though truncation is now explicit
- Stage 4 relationship query extraction is still name-first; rationale arrives through tiered carry-over, not a dedicated query channel
- pre-existing UTF-8 hygiene warnings outside this slice remain out of scope

### Follow-Up
- active execution queue exhausted; no next queue item remains in this bundle
- further semantic transport expansion requires a fresh queue item or survey, not reuse of this closed lane

### Temp Cleanup
- execution SSOT mirror removed: yes (`docs/temp/geuldobi-v2-stage23-semantic-transport-restoration-execution-ssot.md`)
- roadmap mirror removed: yes (`docs/temp/execution-roadmap.md`)
- queue-state refreshed or removed: yes (`docs/temp/queue-state.json` removed after queue exhaustion)
