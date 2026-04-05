# 00_골든 Stage2 Terminal 3: Observability and Auto-Correct Owner Map

Date: 2026-04-06
Status: final
Mode: read-only bounded survey
Scope: latest Stage2 run for `00_골든`, session `20260406_013527`
Authoritative sinks:
- `projects/00_골든/logs/session/decisions.jsonl`
- `projects/00_골든/logs/session/ui_events.jsonl`
- `projects/00_골든/logs/runtime_audit.jsonl`
- `projects/00_골든/logs/quality_metrics.jsonl`

---

## Findings First

### F-1. Three sinks, no unified view

Stage 2 correction and retrieval evidence is fragmented across three JSONL sinks with no cross-reference or aggregation:

| Sink | File | Stage 2 Content |
|------|------|----------------|
| runtime_audit | `logs/runtime_audit.jsonl` | `v60_25_auto_correct` events (ArcAutoCorrector corrections), `v60_10_state_extracted` events |
| quality_metrics | `logs/quality_metrics.jsonl` | `retrieval_observation` events (provenance ledger, budget ledger, coverage warnings) |
| ui_events | `logs/session/ui_events.jsonl` | All `ui.log()` output: `[S2-OBS]`, `[End Location Sync]`, `[End Inventory Sync]`, `[Entity Canonicalization]`, `physical_inventory carryover`, Director verdicts |

An operator wanting "what corrections happened across all 5 arcs" must cross-read all three files manually. No single endpoint summarizes the full correction picture.

### F-2. Correction data split between two sinks with different truncation

The same ArcAutoCorrector event is logged twice with different data:

- **runtime_audit**: `v60_25_auto_correct` → `corrections[:5]` (up to 5 correction strings)
- **ui_events/console**: `[S2-OBS] Auto-correct arc N: ...` → `corrections[:3]` with `...` suffix

Neither sink records the **full** correction list. For arcs with 4+ corrections (arcs 1, 2, 4, 5 in this run), some corrections are invisible in both sinks.

### F-3. Finalizer sync corrections have no audit trail

Four correction families emitted by `stage2_finalizer.py` go to console/ui_events only — no `audit_event()` call:

| Correction | Finalizer Line | Console? | runtime_audit? |
|------------|---------------|----------|----------------|
| `[End Location Sync]` | L1318 | Yes | **No** |
| `[End Inventory Sync]` | L1307 | Yes | **No** |
| `[Entity Canonicalization]` | L873 | Yes | **No** |
| `physical_inventory deterministic carryover` | L1295 | Yes | **No** |

These four corrections appear every arc (Sync) or selectively (Canonicalization: arcs 4, 5 attempt 1, 5 attempt 2). They are durably logged in `ui_events.jsonl` (component=`"UI"`, visible=`true`), but the structured audit sink has no record. A downstream tool querying `runtime_audit.jsonl` for "all Stage 2 corrections" will miss them entirely.

### F-4. Retrieval budget/provenance completely hidden from operator

The `retrieval_observation` records in `quality_metrics.jsonl` contain high-signal data invisible to the operator:

| Field | Arc 1 Value | Arc 2-5 Value | Console Visible? |
|-------|-------------|---------------|-----------------|
| `effective_cap` | 0 | 50,000 | **No** |
| `protected_summary_survived` | false | false | **No** |
| `source_counts` | `{"legacy_high_res": 1}` | `{"vec_memory": 5}` | **No** |
| `provenance_ledger` | full | full | **No** |
| `budget_ledger` | full | full | **No** |
| `vector_context_chars` | 449 | 388-424 | Only via `[TF-38] 벡터 검색 완료 (N자)` — char count only |

The operator sees only `🔎 [TF-38] 벡터 검색 완료 (449자)` — a single character count. No provenance breakdown, no budget utilization, no dropped source information. The `protected_summary_survived: false` pattern (all 7 observations) is invisible.

### F-5. No cross-arc correction accumulation

There is no summary or accumulator showing correction pressure across arcs. Each arc's corrections appear independently. The operator cannot detect whether correction volume is rising, falling, or stable without manually reading the entire log.

From this run's evidence:
- Arc 1: 4 corrections (location sync, 2x internal_energy, items_consumed abstract)
- Arc 2: 4 corrections (PATCH-B unknown item, location sync, 2x internal_energy)
- Arc 3: 3 corrections (location sync, 2x internal_energy)
- Arc 4: 5 corrections (C-1 meta term, location sync, 2x internal_energy, items_consumed abstract)
- Arc 5 attempt 1: 5 corrections (C-1 meta term, location sync, 2x internal_energy, items_consumed abstract)
- Arc 5 attempt 2: 4 corrections (C-1 meta term, 2x internal_energy, items_consumed abstract)

Total: 25 auto-corrections across 6 attempts, plus 5 End Location Sync, 4 physical_inventory carryover, 3 Entity Canonicalization, 1 End Inventory Sync. Grand total: ~38 corrections. None of this is aggregated anywhere.

---

## Q1: Which correction families are only visible in runtime_audit versus visible in UI/console?

### Console-visible AND runtime_audit

| Family | Console Tag | Audit Type | Owner |
|--------|------------|------------|-------|
| ArcAutoCorrector corrections | `[S2-OBS] Auto-correct arc N:` | `v60_25_auto_correct` | `stage2_validation_pipeline.py:491` + `stage2_validation_pipeline.py:470` |

### Console-visible but NOT in runtime_audit

| Family | Console Tag | Owner File | Owner Line |
|--------|------------|------------|-----------|
| End Location Sync | `🔧 [End Location Sync]` | `stage2_finalizer.py` | L1318 |
| End Inventory Sync | `🔧 [End Inventory Sync]` | `stage2_finalizer.py` | L1307 |
| Entity Canonicalization | `🔧 [Entity Canonicalization]` | `stage2_finalizer.py` | L873 |
| Physical inventory carryover | `🔄 [V49.6] physical_inventory deterministic carryover` | `stage2_finalizer.py` | L1295 |
| StateExtractor readiness | `[S2-OBS] StateExtractor context ready` | `prompt_builder.py` | L593 |
| Director verdicts | `🎬 [Director] PASS/REJECT (score=N)` | stage2 main loop | via `ui.log()` |

### runtime_audit only (NOT console-visible in detail)

| Family | Audit Type | Owner File | Owner Line |
|--------|-----------|------------|-----------|
| Draft validation reject | `draft_validation_reject` | `stage2_validation_pipeline.py` | L726 |
| Continuity inspector reject | `continuity_inspector_reject` | `stage2_validation_pipeline.py` | L1004 |
| Arc corrector success/fail | `arc_corrector_success` / `arc_corrector_fail` | `stage2_validation_pipeline.py` | L831 / L810 |
| Flow guard | `flow_guard` | `stage2_validation_pipeline.py` | L546 |
| Duplicate guard | `duplicate_guard` | `stage2_validation_pipeline.py` | L617 |
| Constraint suspected | `constraint_suspected` | `stage2_validation_pipeline.py` | L516 |
| Patch mode entry | `stage2_patch_mode` | `stage2_preflight.py` | L1646 |
| Four-phase verdict failure | `four_phase_final_verdict_failure` | `stage2_preflight.py` | L1747 |
| Vector search failure | `s2_vector_search_failed` | `stage2_preflight.py` | L344, L1302 |

### quality_metrics only (NOT in console or runtime_audit)

| Family | Metric Type | Owner File | Owner Line |
|--------|-----------|------------|-----------|
| Retrieval observation | `retrieval_observation` | `quality_dashboard.py` | L270 |

(Called from `stage2_preflight.py:1353`)

---

## Q2: Which repeated corrections are harmless residue versus real front blockers?

### Harmless residue (expected, recurring, no functional impact)

**1. `internal_energy` field removal** — every arc, start_state + end_state (10 removals across 6 attempts)
- Owner: `stage2_optimizer.py` `ArcAutoCorrector._normalize_internal_energy()` L564
- Root cause: LLM prompt template emits wuxia-default `internal_energy` field for non-wuxia (investment) genre
- Impact: None — consistently cleaned before Director review
- Verdict: **harmless residue**, but noisy — could be prevented by genre-filtered prompt template

**2. `physical_inventory` deterministic carryover** — arcs 2-5 (4 occurrences)
- Owner: `stage2_finalizer.py` L1287-1297
- Root cause: LLM does not re-emit the full physical inventory each arc; system deterministically carries it forward
- Impact: None — intentional design behavior
- Verdict: **harmless residue**, expected system behavior

**3. `End Location Sync`** — every arc (5 occurrences)
- Owner: `stage2_finalizer.py` L1313-1319
- Root cause: `state_constraints` end location and `joint_docs` location diverge after ArcAutoCorrector runs
- Impact: Low — the sync resolves the divergence, but the operator cannot tell whether the "corrected" canonical location is itself correct
- Verdict: **harmless residue with monitoring caveat** — the sync is mechanical, but if the canonical source (state_constraints) is wrong, the sync silently propagates the error

### Low-severity signal (operator should see but not blocking)

**4. `[C-1]` tactical_doc meta term 'Arc' cleanup** — arcs 4, 5 attempt 1, 5 attempt 2 (3 occurrences)
- Owner: `stage2_optimizer.py` `ArcAutoCorrector._sanitize_tactical_meta_terms()` L712
- Root cause: LLM uses system meta-term "Arc" in narrative prose
- Impact: Cosmetic — term substitution only, no content drift
- Verdict: **low-severity signal**, indicates LLM prompt could be tightened

**5. `items_consumed` abstract concept removal** — arcs 1, 4, 5 attempt 1, 5 attempt 2 (4 occurrences)
- Owner: `stage2_optimizer.py` `ArcAutoCorrector._filter_abstract_items_consumed()` L593
- Removed items: `'법인 설립 비용 약 3,200만원'`, `'WTI 6월물 매수 포지션 계약 확인서'`, `'금(XAU/USD) 선물 매수 계약서'`
- Impact: Mild risk — if a legitimate consumed physical item is wrongly classified as "abstract", state tracking breaks. In this run all removed items were correctly abstract (financial concepts, not physical objects).
- Verdict: **low-severity signal**, classification logic appears correct for this run

### Material signal (operator should investigate)

**6. `[PATCH-B]` source-unknown possession** — arc 2 only (1 occurrence)
- Owner: `stage2_optimizer.py` `ArcAutoCorrector.auto_correct()` L240
- Item: `'트레이딩용 노트북'` — flagged as present in possession but never in `items_acquired`
- Impact: The item persists in the arc. If downstream stages reference it, the provenance chain is broken.
- Verdict: **material signal** — generation coherence failure, the auto-corrector flags but does not remove

**7. Arc 3/4 location truth divergence** — cross-arc pattern (Terminal 1 owns details)
- The `[End Location Sync]` corrections show the system repeatedly correcting location across arcs 1-5, with the canonical location shifting between 여의도 and 강남. The Director (Arc 3) explicitly noted this divergence in PASS_WITH_FIX.
- Verdict: **material signal** — not a Terminal 3 primary finding, but the observability evidence confirms the divergence is visible only in scattered sync logs, not in any aggregated view

---

## Q3: Each correction family's owner file

### ArcAutoCorrector family (pre-Director validation phase)

| Sub-correction | Owner File | Function | Line |
|---------------|------------|----------|------|
| Location sync (`arc_end_state` ↔ `state_constraints`) | `modules/core/stage2_optimizer.py` | `ArcAutoCorrector._fix_joint_docs()` | L461 |
| `internal_energy` removal | `modules/core/stage2_optimizer.py` | `ArcAutoCorrector._normalize_internal_energy()` | L564 |
| Meta term `[C-1]` cleanup | `modules/core/stage2_optimizer.py` | `ArcAutoCorrector._sanitize_tactical_meta_terms()` | L712 |
| `items_consumed` abstract removal | `modules/core/stage2_optimizer.py` | `ArcAutoCorrector._filter_abstract_items_consumed()` | L593 |
| Duplicate item removal | `modules/core/stage2_optimizer.py` | `ArcAutoCorrector._remove_duplicate_items()` | L294 |
| `[PATCH-B]` unknown item flag | `modules/core/stage2_optimizer.py` | `ArcAutoCorrector.auto_correct()` | L240 |

Emission path: `stage2_optimizer.py` returns corrections → `stage2_validation_pipeline.py:461` calls `post_process_arc()` → emits to `audit_event("v60_25_auto_correct")` at L470 and `ui.log("[S2-OBS]")` at L491.

### Finalizer sync family (post-Director finalization phase)

| Sub-correction | Owner File | Function | Line |
|---------------|------------|----------|------|
| End Location Sync | `modules/core/stage2_finalizer.py` | (arc finalization loop) | L1313-1319 |
| End Inventory Sync | `modules/core/stage2_finalizer.py` | (arc finalization loop) | L1301-1309 |
| Entity Canonicalization | `modules/core/stage2_finalizer.py` | (pre-Director entity normalization) | L873 |
| Physical inventory carryover | `modules/core/stage2_finalizer.py` | (arc finalization loop) | L1287-1297 |

Emission path: `stage2_finalizer.py` → `self.ctx.ui.log()` only → captured in console + `ui_events.jsonl`. **No** `audit_event()` call for any of these four.

### Retrieval observation family (pre-generation context phase)

| Data | Owner File | Function | Line |
|------|------------|----------|------|
| `retrieval_observation` | `modules/core/quality_dashboard.py` | `record_retrieval_observation()` | L270 |

Called from: `modules/core/stage2_preflight.py:1353`

Emission path: `stage2_preflight.py` calls `quality_dashboard.record_retrieval_observation()` → written to `quality_metrics.jsonl`. **Not** in console or runtime_audit.

### Validation gate family (pre-Director validation)

| Sub-event | Owner File | Function | Audit Type | Console? |
|-----------|------------|----------|-----------|----------|
| Draft validation reject | `stage2_validation_pipeline.py` | `run_validation()` B3 | `draft_validation_reject` | Partial (advisory list) |
| Continuity inspector reject | `stage2_validation_pipeline.py` | `run_validation()` B4 | `continuity_inspector_reject` | Partial (advisory list) |
| Flow guard | `stage2_validation_pipeline.py` | `run_validation()` B2 | `flow_guard` | Yes (rejection reason) |
| Duplicate guard | `stage2_validation_pipeline.py` | `run_validation()` B2 | `duplicate_guard` | Yes (detection notice) |

---

## Q4: Is current Stage 2 operator observability sufficient?

### What IS visible to the operator

1. **Console/ui_events**: All correction summaries via `[S2-OBS]`, all sync operations, Director verdicts with scores, Entity Canonicalization, physical_inventory carryover, preflight status, StateExtractor readiness
2. **decisions.jsonl**: Director verdict + score + reason for every arc attempt (authoritative)
3. **Retrieval char count**: `[TF-38] 벡터 검색 완료 (N자)` — single number

### Material visibility gaps

**Gap 1: No correction aggregation** (severity: MEDIUM)
- 38 corrections across 6 attempts with no summary. Operator cannot detect correction pressure trend.
- Recommended surface: end-of-batch summary line, e.g., `[S2-OBS] Batch 1-5 auto-correction summary: 25 ArcAutoCorrector + 5 Location Sync + 4 Inventory Carryover + 3 Canonicalization = 37 total`

**Gap 2: Retrieval provenance hidden** (severity: MEDIUM)
- 7 retrieval observations with full budget/provenance data visible only in `quality_metrics.jsonl`. Operator sees only character count.
- Key hidden fact: `protected_summary_survived: false` on all 7 observations. `effective_cap: 0` on Arc 1 observation.
- Recommended surface: `[S2-OBS] Retrieval: N sources, M chars, cap N% used, summary_survived=bool`

**Gap 3: Finalizer sync not in structured audit** (severity: LOW-MEDIUM)
- 4 correction families (`End Location Sync`, `End Inventory Sync`, `Entity Canonicalization`, `physical_inventory carryover`) logged in `ui_events.jsonl` but not in `runtime_audit.jsonl`.
- A tool querying `runtime_audit.jsonl` for "all Stage 2 corrections" will miss these entirely.
- Recommended surface: `audit_event("finalizer_sync", ...)` for each sync operation

**Gap 4: Auto-correct truncation** (severity: LOW)
- Console shows ≤3 corrections with `...`; runtime_audit shows ≤5. Neither records the full list for arcs with 4+ corrections.
- Recommended surface: lift runtime_audit truncation to full list (corrections are short strings, not large payloads)

**Gap 5: Validation gate details advisory-only** (severity: LOW)
- DraftValidator and ContinuityInspector findings go to Director as in-memory advisories. If Director PASS overrides advisory warnings, the operator sees only the Director's final score. The underlying validation concerns have no console surface — only `runtime_audit` has the `draft_validation_reject` / `continuity_inspector_reject` events.
- In this run, no DraftValidator or ContinuityInspector rejections fired, so this gap is latent but confirmed by code inspection.

### Overall assessment

Current Stage 2 observability is **functional but fragmented**. The operator can see the critical facts (Director verdicts, correction summaries, sync operations) during the run. However:

1. The three-sink fragmentation means post-run analysis requires manual cross-referencing.
2. The highest-signal hidden data is retrieval provenance — an operator cannot tell why retrieval returned only 388-449 chars against a 50,000-char budget.
3. Correction accumulation is absent — an operator cannot quickly gauge whether the auto-corrector is working harder or easier as arcs progress.
4. The finalizer sync audit gap is architecturally inconsistent: ArcAutoCorrector corrections get `audit_event()` calls, but finalizer corrections (which happen later in the same pipeline) do not.

These gaps are consistent with the existing parked execution SSOT's Tranche 4 ("bounded observability surfacing") and are not new discoveries, but this survey provides the concrete sink map, owner map, and per-correction evidence that Tranche 4 would need to implement.

---

## Sink Architecture Diagram

```
                Stage 2 Pipeline
                      │
    ┌─────────────────┼──────────────────┐
    │                 │                  │
    ▼                 ▼                  ▼
ArcAutoCorrector  Finalizer Sync    Retrieval Context
(stage2_optimizer)  (stage2_finalizer)  (stage2_preflight)
    │                 │                  │
    ├─→ audit_event() ├─→ ui.log()      ├─→ quality_dashboard
    │   "v60_25..."   │   ONLY           │   .record_retrieval_obs()
    │                 │                  │
    ├─→ ui.log()      │                  │
    │   "[S2-OBS]"    │                  │
    │                 │                  │
    ▼                 ▼                  ▼
runtime_audit.jsonl  ui_events.jsonl   quality_metrics.jsonl
(corrections[:5])    (all ui.log)      (retrieval provenance)
                     (corrections[:3])
```

No unified query endpoint spans all three sinks.

---

## Evidence Cross-Reference

| Evidence Source | File | Lines/Records Used |
|----------------|------|--------------------|
| Auto-correct audit events | `logs/runtime_audit.jsonl` | L1, L4, L7, L10, L13, L14 (6 `v60_25_auto_correct` records) |
| StateExtractor events | `logs/runtime_audit.jsonl` | L3, L6, L9, L12, L16 (5 `v60_10_state_extracted` records) |
| Retrieval observations | `logs/quality_metrics.jsonl` | All 7 `retrieval_observation` records |
| Director decisions | `logs/session/decisions.jsonl` | All 12 records (5 arc + 5 arc_design + 2 retry) |
| UI correction events | `logs/session/ui_events.jsonl` | seq 250, 255-256, 276, 281-282, 303, 318-319, 340, 342, 353-354, 375, 377, 394, 396, 404-405, 407 |
| Console output | `tttt.txt` | L341, L372-374, L404-405, L453-454, L501-503, L531-532 |
| ArcAutoCorrector code | `modules/core/stage2_optimizer.py` | L240, L294, L461, L564, L593, L712 |
| Validation pipeline code | `modules/core/stage2_validation_pipeline.py` | L461-496 (auto-correct emission), L470 (audit), L491 ([S2-OBS]) |
| Finalizer sync code | `modules/core/stage2_finalizer.py` | L873, L1295, L1307, L1318 |
| Preflight retrieval code | `modules/core/stage2_preflight.py` | L1353, L1378 |
| Quality dashboard code | `modules/core/quality_dashboard.py` | L270 (record_retrieval_observation) |
| Audit service code | `modules/core/services/audit_service.py` | L61 (audit_event), L74 (flush to JSONL) |
| Session logger code | `modules/core/session_logger.py` | L208-264 (log_ui_event → ui_events.jsonl) |

---

Confidence: 0.96

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
