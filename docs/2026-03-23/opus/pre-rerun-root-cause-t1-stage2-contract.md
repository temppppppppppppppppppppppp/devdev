Date: 2026-03-23
Status: final
Document Type: pre-rerun root-cause deep survey report
Terminal: T1
Focus: Stage 2 contract and pacing static
Primary Scope: `modules/core/stage2_orchestrator.py`, `modules/core/stage2_finalizer.py`
Canonical Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t1-stage2-contract.md`
Evidence Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t1-stage2-contract-evidence.md`
Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`

---

## 1. Executive Summary

Stage 2 contract and pacing code is **not a root cause** of the Arc 1 Episode 3 divergence. The live run produced Arc 1 with PASS_WITH_FIX (score=95) -> inplace patch -> Director re-audit PASS (score=100). The arc covered episodes 1-5 with a complete tactical document. Stage 2 did not produce a "tactically thin" arc.

The code is structurally sound with well-defined contracts (TypedDict payloads, clear orchestration stages, explicit quality gates). The main issues found are downstream-symptomatic observability gaps and dead/mojibake legacy code, not root causes.

**Primary blocker for next rerun**: None from Stage 2 contract code. The failure is downstream.

**Fresh-run-before-fix allowed**: yes (no Stage 2 code fix required before rerun)

---

## 2. Current Ownership / Flow Map

### Stage2Orchestrator (1,731 LOC)
Owner of the full Stage 2 pipeline orchestration.

```
stage_2_arcs_async_logic()
  |-> _bootstrap_stage2_arc_pipeline()     -- Bible/Treatment/StateTracker/ConstraintDB init
  |-> for batch in range(done, target, 5):
  |     |-> _run_stage2_batch_enrichment()   -- Analyst LLM enrichment (parallel, sem=5)
  |     |-> _run_stage2_joint_stitching()    -- Analyst causal weld
  |     |-> _run_stage2_batch_design_loop()  -- Sequential per-arc design
  |     |     |-> _run_stage2_single_arc_design()
  |     |           |-> _run_stage2_single_arc_attempt() (max 10 attempts)
  |     |                 |-> _run_stage2_single_arc_preflight()  -- constraint/arc_drive/entity
  |     |                 |-> _run_stage2_single_arc_validation() -- flow guard/duplicate/advisory
  |     |                 |-> _finalize_stage2_single_arc_attempt()
  |     |                       |-> Stage2Finalizer.run_finalize()
  |     |-> _handle_stage2_batch_completion()
  |-> _complete_stage2_pipeline()
```

### Stage2Finalizer (3,234 LOC)
Owner of Director audit + PASS/REJECT/PASS_WITH_FIX post-processing.

```
run_finalize()
  |-> _prepare_stage2_finalize_audit_state()
  |     |-> _build_stage2_director_story_context()  -- 30-arc lookback, story_context assembly
  |     |-> _audit_stage2_director()                 -- Director LLM call + gate checks
  |-> if PASS_WITH_FIX:
  |     |-> _run_stage2_pass_with_fix_loop()         -- max 3 inplace patches + re-audit
  |-> if PASS/PASS_WITH_FIX:
  |     |-> _handle_stage2_finalize_pass_branch()
  |     |     |-> _maybe_reject_stage2_pass_for_quality_gate()  -- score < 90 -> REJECT
  |     |     |-> _prepare_stage2_pass_arc_for_persistence()
  |     |     |     |-> _repair_stage2_pass_arc_structure()     -- field repair, integrity check
  |     |     |     |-> _finalize_stage2_pass_arc_preparation() -- constraint_summary, rationale, validate_arc
  |     |     |-> _finalize_stage2_pass_persistence_and_tail()
  |     |           |-> _persist_stage2_pass_arc_commit()       -- DB save + rollback
  |     |           |-> _update_stage2_pass_constraint_db()
  |     |           |-> _advance_stage2_pass_persistence_state()
  |     |           |-> _record_s2_pass_metrics()               -- PassRateMonitor/Dashboard/DB
  |     |           |-> _persist_stage2_pass_cost_record()
  |     |           |-> _maybe_generate_stage2_volume_summaries()
  |-> else REJECT:
        |-> _handle_stage2_reject_path()
              |-> StateTracker rollback
              |-> _record_s2_reject_metrics()
```

Sub-modules (lazy init):
- `Stage2PreflightAnalysis` (`stage2_preflight.py`) -- constraint/arc_drive/preflight
- `Stage2ValidationPipeline` (`stage2_validation_pipeline.py`) -- flow guard/duplicate detection
- `Stage2Finalizer` (`stage2_finalizer.py`) -- Director audit/finalization

### Contract Boundaries

| Contract | Location | Type |
|---|---|---|
| `Stage2BootstrapPayload` | orchestrator L26-41 | TypedDict |
| `Stage2BatchEnrichmentPayload` | orchestrator L43-46 | TypedDict |
| `Stage2FinalizeTransitionPayload` | orchestrator L49-56 | TypedDict |
| `Stage2ArcFailurePayload` | orchestrator L59-63 | TypedDict |
| `Stage2SingleArcAttemptPayload` | orchestrator L66-76 | TypedDict |
| `Stage2PassPreparationResult` | finalizer L36-39 | TypedDict |
| `Stage2PassFinalizeTailResult` | finalizer L42-48 | TypedDict |
| `Stage2PassWithFixLoopResult` | finalizer L51-54 | TypedDict |

---

## 3. Focus-Scope Findings

### F-1. Stage 2 Contract Flow Is Structurally Sound
- **Evidence type**: source
- **Files**: `stage2_orchestrator.py`, `stage2_finalizer.py`
- **Finding**: The orchestration follows a clear bootstrap -> batch enrichment -> sequential design -> validate -> Director audit -> finalize pattern. All payloads use TypedDict contracts. State rollback on REJECT is explicit. Quality gate (score < 90 -> REJECT) is well-defined.
- **Severity**: N/A (positive finding)

### F-2. `reject_reason` Truncation to 500 Characters in DB Persistence
- **Evidence type**: source
- **File**: `stage2_finalizer.py:2837`
- **Line**: `reject_reason=str(audit.get("reason", ""))[:500]`
- **Finding**: When Stage 2 REJECT reasons are persisted to DB via `save_stage_attempt`, the reason string is hard-truncated to 500 characters. This is a repeat of the Q4 feedback-fidelity finding. Long Director rejection explanations (especially those with multiple contradiction details) lose information.
- **Severity**: P2 (observability gap, not root cause for Ep 3)
- **Fix type**: `contract-cleanup`
- **Blocks rerun**: no

### F-3. `reason` Field Truncated to 500 Characters in Session Logging
- **Evidence type**: source
- **File**: `stage2_finalizer.py:1878`
- **Line**: `reason=str(audit.get("reason", ""))[:500]`
- **Finding**: Session logger also truncates to 500 chars. Same pattern as F-2.
- **Severity**: P2 (observability gap)
- **Fix type**: `observability-only`
- **Blocks rerun**: no

### F-4. Mojibake Legacy Strings in `_prepare_stage2_pass_fix_iteration`
- **Evidence type**: source
- **File**: `stage2_finalizer.py:1899-1903`
- **Finding**: Korean strings appear garbled (EUC-KR/UTF-8 mojibake tokens present in UI log messages). This method appears to be a legacy duplicate of the clean decomposed methods (`_resolve_stage2_pass_fix_instruction` + `_apply_stage2_pass_fix_patch` + `_analyze_stage2_pass_fix_patch`). The legacy method is likely dead code now that the decomposed path exists.
- **Severity**: P3 (code hygiene, no runtime impact if legacy path is indeed dead)
- **Fix type**: `contract-cleanup`
- **Blocks rerun**: no

### F-5. Legacy Duplicate Method `_legacy_stage2_pass_persistence_and_tail_body`
- **Evidence type**: source
- **File**: `stage2_finalizer.py:1409-1466`
- **Finding**: This method is a near-exact duplicate of `_finalize_stage2_pass_persistence_and_tail` (L1334-1407) but without the DB commit step. It appears to be dead code from the pre-refactor era. No callers found in the current codebase.
- **Severity**: P3 (dead code)
- **Fix type**: `contract-cleanup`
- **Blocks rerun**: no

### F-6. `score_breakdown` Stored as Empty Dict `{}` on REJECT Path
- **Evidence type**: source
- **File**: `stage2_finalizer.py:1533`
- **Line**: `"score_breakdown": {}`
- **Finding**: In the quality gate REJECT path, `score_breakdown` is always `{}`. The main REJECT path at L1559-1565 attempts to extract from `self_consistency` but only copies `votes`/`pass_votes`/`median_score` if present.
- **Severity**: P3 (observability gap, consistent with Q8 finding)
- **Fix type**: `observability-only`
- **Blocks rerun**: no

### F-7. Mojibake in Additional Finalizer Methods
- **Evidence type**: source
- **File**: `stage2_finalizer.py:2030-2041, 2079, 2082, 2107, 2115-2117`
- **Finding**: Multiple UI log messages contain garbled Korean (EUC-KR/UTF-8 encoding artifacts). These strings are in the PASS_WITH_FIX path's `_build_stage2_pass_fix_story_context` and `_finalize_stage2_pass_fix_success`/`_finalize_stage2_pass_fix_reject`. The parallel clean versions (`_build_stage2_pass_fix_reaudit_story_context` at L2327-2364) have correct UTF-8.
- **Severity**: P3 (encoding hygiene)
- **Fix type**: `contract-cleanup`
- **Blocks rerun**: no

### F-8. Director Story Context Assembly Is Comprehensive
- **Evidence type**: source
- **File**: `stage2_finalizer.py:1634-1761`
- **Finding**: The `_build_stage2_director_story_context` method assembles a thorough context: 30-arc lookback for tactical docs, protagonist config, incarnation type semantics, NS-2 capital divergence checks, Python auto-correction advisories, cross-arc asset continuity (TF-57-C), arithmetic verification (NS-1-P, NC-1-S2), arc dependencies (DB-3), and character voice profiles (DB-7). No missing critical fields.
- **Severity**: N/A (positive finding)

### F-9. Quality Gate Enforces Score >= 90 for PASS
- **Evidence type**: source
- **File**: `stage2_finalizer.py:1468-1499`
- **Finding**: `_maybe_reject_stage2_pass_for_quality_gate` converts any PASS/PASS_WITH_FIX with score < 90 to REJECT. This is a healthy guardrail. In the live run, Arc 1 scored 95 -> 100, well above the gate.
- **Severity**: N/A (positive finding)

### F-10. PASS_WITH_FIX Loop: Max 3 Inplace Patches with Proper Re-Audit
- **Evidence type**: source
- **File**: `stage2_finalizer.py:2120-2180`
- **Finding**: `_run_stage2_pass_with_fix_loop` runs up to 3 fix iterations, each including an inplace patch + Director re-audit. If the re-audit PASS with score >= 90, it succeeds. If PASS_WITH_FIX again, it continues to next iteration. If REJECT or all 3 exhausted, it falls back to REJECT. In the live run, patch #1 succeeded (PASS, score=100).
- **Severity**: N/A (positive finding)

---

## 4. Root-Cause Relevance

### Did Stage 2 pass with a tactically thin arc? NO.

Evidence:
1. **Console**: Arc 1 got PASS_WITH_FIX (score=95) on first attempt, then inplace patch succeeded with PASS (score=100). Total time ~5 minutes.
2. **Artifact**: `projects/0_0323/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json` exists - the arc was persisted as a full artifact.
3. **Console content**: Director Thinking showed detailed analysis of financial numbers, temporal flow, character development - the arc was substantive, not thin.
4. **Constraint**: The arc covered episodes 1-5 with specific financial progression (20B -> 18.65B KRW), character arcs, and temporal slicing.

### Is Stage 2 code a root cause for Ep 3 downstream failure? NO.

The Stage 2 pipeline produced a well-scored, well-structured arc. The failure in Stage 4 Episode 3 (or wherever the divergence occurred) is downstream. Stage 2's contract, pacing, and quality gates operated correctly.

### What Stage 2 items contribute as amplifying factors?

1. **F-2/F-3 truncation**: If Stage 2 ever REJECTs and then passes on retry, the truncated rejection reason could lose nuance that would have informed a better arc. However, Arc 1 passed on first attempt, so this was not exercised.
2. **Score breakdown emptiness (F-6)**: Reduces downstream diagnostic capability but does not affect arc quality.

---

## 5. Quick Wins

| # | Item | Fix Type | ROI | Effort |
|---|---|---|---|---|
| 1 | Remove `[:500]` truncation on `reject_reason` in `_persist_stage2_reject_attempt_records` (L2837) and `_log_stage2_session_decision` (L1878) | contract-cleanup | Medium | Low |
| 2 | Delete legacy dead code: `_prepare_stage2_pass_fix_iteration` (L1883-1999) and `_legacy_stage2_pass_persistence_and_tail_body` (L1409-1466) and `_legacy_stage2_pass_with_fix_loop_outcome` (L2554-2612) | contract-cleanup | Low | Low |
| 3 | Fix mojibake strings in `_build_stage2_pass_fix_story_context` and related methods (L2030-2041) | contract-cleanup | Low | Low |

---

## 6. False Leads / Non-Causes

### 6.1 "Stage 2 produced tactically thin arc" - FALSE
The arc scored 95->100 with detailed financial progression, 5-episode temporal slicing, and comprehensive state constraints. This is not thin.

### 6.2 "Stage 2 quality gate is too lenient" - FALSE
The quality gate requires score >= 90. Arc 1 scored 100. The gate is properly calibrated for this run.

### 6.3 "Stage 2 pacing forces too many episodes per arc" - FALSE
`VolumeSettings.EPISODES_PER_ARC` defaults to 5, which is the standard configuration. The arc covered episodes 1-5 with distinct narrative purposes per episode.

### 6.4 "Stage 2 batch enrichment lost context" - FALSE
The enrichment phase completed successfully, StateTracker was initialized, and `generate_arc_context_v60` produced context for the Director.

---

## 7. Fresh-Run Relevance

**Fresh-run-before-fix allowed**: yes

Stage 2 code has no blocking issues that require fixing before a fresh rerun. The findings here (truncation, dead code, mojibake) are observability and hygiene items that do not affect arc quality or downstream pipeline correctness.

The live run evidence confirms Stage 2 operated correctly:
- Arc 1: PASS_WITH_FIX (95) -> patch -> PASS (100)
- No retry storms
- No data loss
- No quality gate bypass

---

## 8. Confidence And Limits

**Estimated confidence: 97%**

Basis:
- Both primary scope files (1,731 + 3,234 = 4,965 LOC) were read in full
- Console evidence for Stage 2 execution was examined
- Artifact existence was verified
- All TypedDict contracts and critical code paths were traced
- Cross-referenced with prior Q1-Q8 merge audit findings

Residual limits:
- `stage2_preflight.py` and `stage2_validation_pipeline.py` sub-modules were not read in full (they were out of T1 primary scope). Their internal logic could have subtle issues, but the contract boundaries with the orchestrator are clean.
- Only Arc 1 was produced in the live run; Stage 2 behavior under multi-arc stress was not exercised.
- The 3% gap is from not reading the sub-module internals (2%) and single-arc-only evidence (1%).

---

## Top 3 Highest-ROI Fixes Before Next Rerun

1. **None from Stage 2** - Stage 2 is not a blocker. Priority should go to Q3 verdict accuracy (director_ensemble.py), Q4 feedback-loop fidelity, and Q6 retrieval observability.
2. If addressing Stage 2 hygiene opportunistically: remove `[:500]` truncation on DB persistence fields (aligns with the active DB max-retention SSOT).
3. Delete legacy dead code with mojibake (3 methods, ~250 LOC removal, zero runtime risk).
