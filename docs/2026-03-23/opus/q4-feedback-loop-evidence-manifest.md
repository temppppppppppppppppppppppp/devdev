Date: 2026-03-23
Document Type: Q4 evidence manifest
Terminal: T4
Canonical Path: `docs/2026-03-23/opus/q4-feedback-loop-evidence-manifest.md`

---

## Source File Inventory

| File | Lines | Relevance |
|------|-------|-----------|
| `modules/core/stage4_reject_runtime.py` | 819 | Primary — reject guidance, retry snapshot, reject-side logging |
| `modules/core/stage4_interview_round.py` | ~4600 | Primary — feedback provenance, attempt history, reject bucket |
| `modules/core/stage2_finalizer.py` | 3234 | Primary — Stage 2 reject path, director audit handoff |
| `modules/domain/agents/director_auditor.py` | 1488 | Primary — audit_strategic_plan, V0128 validation |
| `modules/core/stage3_orchestrator.py` | 2674 | Primary — Stage 3 reject reason, rejection history |
| `modules/domain/agents/chief_writer.py` | ~2100 | Secondary — feedback consumption in regeneration |
| `modules/domain/agents/director_ensemble.py` | ~2400 | Reference — verdict/feedback production |
| `modules/core/stage4_director_runtime.py` | ~800 | Reference — director review orchestration |
| `modules/core/stage4_retry_runtime.py` | ~620 | Reference — retry iteration control |

---

## Key Method Trace (Stage 4 Feedback Path)

### 1. Feedback Provenance Assembly
- `Stage4InterviewRound._build_retry_feedback_provenance()` — L556-658
  - Splits director_feedback into system_lines / general_lines
  - Collects evidence from selected_validation (truth_gate_warnings, structured_violations, quality_signal_warnings)
  - Builds runtime_advisory digest from `_last_advisory_details`
  - Produces `merged_feedback` string + 6-field provenance dict

### 2. Reject Guidance Assembly
- `Stage4RejectRuntime._build_reject_guidance_payload()` — L390-502
  - Calls `_build_retry_feedback_provenance()`
  - Classifies reject_bucket (constraint_violation / structure_error / quality_issue)
  - Checks continuity_replay → escalates fix_scope
  - Checks fix_pack contract → may widen to partial
  - Conditionally invokes ToT (structure_error) or MAD (constraint_violation)

### 3. Retry Snapshot Assembly
- `Stage4RejectRuntime._build_reject_retry_snapshot()` — L309-388
  - **L342**: `"rejection_reason": director_feedback` — FIELD LOSS (merged string replaces structured reason)
  - **L365**: `"contradiction_details": list(...)[:3]` — REDUCTION (5→3)
  - Includes: score_breakdown, gate_basis, validation_warnings[:20], fix_scope/pack, error_category
  - Inherits prior_attempts via `_inherit_attempt_history()` (max 3 deduped)
  - Computes retry_budget_axes

### 4. Attempt Snapshot Compaction
- `Stage4InterviewRound._compact_attempt_snapshot()` — L1130-1154
  - `fix_scope_reasoning[:200]`, `open_review[:200]`, `rejection_reason[:240]`
  - `action_items[:3]`, `contradiction_types[:5]`
  - `contradiction_details` compact to 2 items, 120 chars each

### 5. ChiefWriter Consumption
- `ChiefWriter._build_regeneration_feedback()` — L1069-1102
  - Injects `director_feedback` as-is
  - Reads `previous_attempt["rejection_reason"]` (gets merged string, not original)
  - Reads `score_breakdown`, `validation_warnings[:10]`, `fix_scope_reasoning`, `open_review`
- `ChiefWriter._build_regeneration_strategy_hints()` — L1104-1116
  - Reads `action_items`, `selected_strategy_key`, `selection_reason`

---

## Key Method Trace (Stage 2 Feedback Path)

### 1. Director Audit
- `DirectorQualityAuditor.audit_strategic_plan()` — L970-1125
  - Entity consistency check → immediate REJECT if mismatches
  - Protagonist name hard guard → immediate REJECT if missing
  - LLM strategic audit prompt (STRATEGIC_AUDIT_PROMPT_V30)
  - Self-consistency voting (3 votes)
  - Contradiction firewall (CRITICAL≥1 or MAJOR≥2 → REJECT)

### 2. Reject Path
- `Stage2Finalizer._handle_stage2_reject_path()` — L1538-1632
  - `base_feedback = audit["re_slice_instruction"]` or "밀도 보강 필요"
  - `reject_reason = audit["reason"]` or "사유 미상"
  - Adaptive intensity guide injection
  - `director_feedback_for_fourphase` = f-string (reason + feedback + intensity)
  - StateTracker rollback on four_phase generation method
  - Returns retry dict with `current_feedback`, `director_feedback_for_fourphase`

### Gap: No structured contradiction/score_breakdown/fix_scope in Stage 2 feedback

---

## Key Method Trace (Stage 3 Feedback Path)

### 1. Reject Reason Assembly
- `Stage3Orchestrator._build_stage3_reject_reason()` — L2089-2135
  - Compact string: error[:240] + score + strategy + validate_verdict + issues + contradictions[:2]
  - Overall: `[:500]`

### 2. Rejection History
- `Stage3Orchestrator._append_stage3_rejection_history()` — L2586-2618
  - Appends to `app.stage_rejection_history` (app-level list)
  - `reason[:200]`, `specific_issue[:200]`, `failure_category`, `fix_scope[:40]`
  - `score_breakdown` (5 keys max)

### Gap: No explicit contract for how rejection_history reaches next blueprint generation attempt

---

## Truncation Inventory

| Location | Field | Limit | Severity |
|----------|-------|-------|----------|
| `stage4_reject_runtime.py:545` | `director_feedback` (console) | `[:100]` | HIGH — operator surface |
| `stage4_reject_runtime.py:565` | `director_feedback` (failure_learner) | `[:150]` | MEDIUM — learning system |
| `stage4_reject_runtime.py:577` | `director_feedback` (adaptive_manager) | `[:200]` | MEDIUM — adaptation system |
| `stage4_reject_runtime.py:601` | `director_feedback` (quality_dashboard) | `[:200]` | MEDIUM — dashboard |
| `stage4_reject_runtime.py:365` | `contradiction_details` | `[:3]` | HIGH — feedback accuracy |
| `stage4_interview_round.py:1139` | `fix_scope_reasoning` (snapshot) | `[:200]` | MEDIUM — retry context |
| `stage4_interview_round.py:1140` | `open_review` (snapshot) | `[:200]` | MEDIUM — retry context |
| `stage4_interview_round.py:1143` | `rejection_reason` (snapshot) | `[:240]` | HIGH — retry context |
| `stage4_interview_round.py:1144` | `action_items` (snapshot) | `[:3]` | MEDIUM — retry context |
| `stage4_interview_round.py:637` | `retry_directives` | `[:500]` | LOW — prior round |
| `stage3_orchestrator.py:2372` | `_reject_reason` (console) | `[:140]` | MEDIUM — operator surface |
| `stage3_orchestrator.py:2577` | `_reject_reason` (log) | `[:160]` | LOW — structured log |
| `stage3_orchestrator.py:2609` | `reason` (history) | `[:200]` | MEDIUM — retry context |
| `stage2_finalizer.py:2837` | `reject_reason` (DB) | `[:500]` | MEDIUM — DB persistence |
| `stage2_finalizer.py:3006` | `reject_reason` (metrics) | `[:100]` | LOW — metrics |

---

## Cross-Reference with Existing Reports

| Source | Finding ID | Status in Live Code |
|--------|-----------|---------------------|
| `director-pipeline-7axis-deep-dive.md` §4.1 | P1-HOT: rejection_reason field loss | **confirmed live** at L342 |
| `director-pipeline-7axis-deep-dive.md` §4.1 | P1-HOT: verdict_reason 500-char truncation | **confirmed live** (via _compact_text) |
| `director-pipeline-7axis-deep-dive.md` §4.1 | P1-HOT: contradiction_details 5→3 | **confirmed live** at L365 |
| `console-log-max-display-post-audit-execution-ssot.md` Tranche 1 | operator truncation removal | **pending** — SSOT written, not realized |
| `db-logging-integrity-post-audit-execution-ssot.md` Class A | Python truncation against TEXT | **pending** — SSOT written, not realized |
| `fresh-run-3pass-audit-report.md` P1-1 | ep5 V60.97 swap → REJECT cascade | **confirmed** — feedback insufficiency may contribute |
