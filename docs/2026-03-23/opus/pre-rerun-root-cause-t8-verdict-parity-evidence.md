Date: 2026-03-23
Document Type: evidence manifest
Terminal: T8
Parent Report: `docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity.md`

---

# T8 Evidence Manifest: Director and Post-Select DB/Console Parity

## 1. Console Evidence

| Line Range | Content | Used For |
|------------|---------|----------|
| 537-548 | Ep1 Director PASS score=98, gate=director_primary_pass | Parity baseline (PASS path) |
| 629-638 | Ep2 Director PASS score=98, gate=director_primary_pass | Parity baseline (PASS path) |
| 727-746 | Ep3 Round 1 Director REJECT score=80, gate=director_primary_reject | REJECT path parity |
| 752 | Ep3 Round 2 all candidates failed | Empty candidate path |
| 810-831 | Ep3 Round 3 Director REJECT score=76, gate=director_primary_reject | REJECT path parity |
| 893-912 | Ep3 Round 4 Director PASS score=98 → post-select 2 conflicts → REJECT | **Split-brain case** |
| 902-908 | Post-select continuity conflict details (timeline 1/18 vs 1/17) | Post-select evidence |
| 909 | "2 post-select conflicts detected -> downgrade to REJECT" | Gate downgrade confirmation |
| 910 | "[Lane3 Gate] REJECT retry widened to partial: Fix Pack is missing" | Gate feedback path |
| 961-971 | Ep3 Round 5 Director PASS score=98, no post-select conflict | Final PASS path |
| 351-384 | Director Thinking full text (Ep1) | Thinking preservation check |
| 392 | mojibake encoding artifact | False lead (terminal, not DB) |

## 2. DB Evidence: stage_attempts

| id | stage | ep | att | verdict | score | initial_verdict | key reasoning fields | finding |
|----|-------|-----|-----|---------|-------|-----------------|---------------------|---------|
| 1 | 2 | 1 | 1 | PASS | 100 | NULL | all empty | F-2 |
| 2-5 | 3 | 1-4 | var | PASS | 92-98 | NULL | all empty | F-2 |
| 6 | 4 | 1 | 1 | PASS | 98 | PASS | all populated | baseline |
| 7 | 4 | 2 | 1 | PASS | 98 | PASS | all populated | baseline |
| 8 | 4 | 3 | 1 | REJECT | 80 | NULL | populated | F-1 (REJECT path, no initial_verdict) |
| 9 | 4 | 3 | 2 | EMPTY | 0 | NULL | all empty | empty candidate path |
| 10 | 4 | 3 | 3 | REJECT | 76 | NULL | populated | F-1 (REJECT path) |
| 11 | 4 | 3 | 4 | REJECT | 98 | NULL | populated | **F-1 split-brain** |
| 12 | 4 | 3 | 5 | PASS | 98 | PASS | populated | baseline |

### id=11 split-brain detail
- `verdict = REJECT` (final)
- `score = 98` (Director's score, not overridden)
- `initial_verdict = NULL` (should be "PASS")
- `advisory_flags.gate_semantics.director_verdict = "PASS"`
- `advisory_flags.gate_semantics.final_verdict = "REJECT"`
- `advisory_flags.gate_semantics.gate_basis = "post_select_conflict"`
- `reject_reason` contains "[Lane3 Gate] REJECT..." and "[Continuity Conflict]..." text

## 3. DB Evidence: director_selections

| id | stage | ep | round | verdict | score | director_thinking | selection_reason | finding |
|----|-------|-----|-------|---------|-------|-------------------|-----------------|---------|
| 1 | 2 | 1 | 1 | PASS | 100 | 4,116+ chars | populated | F-2 cross-check |
| 2 | 3 | 1 | 2 | PASS | 92 | "" (empty) | "score strong" | F-4 |
| 3-5 | 3 | 2-4 | 1 | PASS | 95-98 | "" (empty) | populated | F-4 |
| 6-7 | 4 | 1-2 | 0 | PASS | 98 | populated | populated | baseline |
| 8 | 4 | 3 | 0 | REJECT | 80 | populated | populated | baseline |
| 9 | 4 | 3 | 2 | REJECT | 76 | populated | populated | baseline |
| 10 | 4 | 3 | 3 | **PASS** | 98 | populated | populated | **F-1 cross-check: Director DID say PASS** |
| 11 | 4 | 3 | 4 | PASS | 98 | populated | populated | baseline |

## 4. DB Evidence: attempt_raw_rationale

| id | attempt_key | stage | ep | payload_kind | payload_len |
|----|------------|-------|-----|-------------|-------------|
| 1-2 | s4:ep1:arc1:a1 | 4 | 1 | director_thinking / advisory_warnings_raw | 4116 / 1964 |
| 3-4 | s4:ep2:arc1:a1 | 4 | 2 | director_thinking / advisory_warnings_raw | 3261 / 2651 |
| 5-12 | s4:ep3:arc1:a1-a5 | 4 | 3 | director_thinking / advisory_warnings_raw | 2602-4333 / 2012-3704 |

**Finding F-5**: No Stage 2 or Stage 3 entries exist.

## 5. runtime_audit.jsonl Evidence

| timestamp | type | ep | round | gate_basis | score | relevant to |
|-----------|------|-----|-------|------------|-------|-------------|
| 14:25:37 | stage4_retry_pathology_signal | 3 | 1 | director_primary_reject | 80 | F-1 baseline |
| 14:31:35 | stage4_retry_pathology_signal | 3 | 2 | (empty) | 0 | empty candidate |
| 14:36:47 | stage4_retry_pathology_signal | 3 | 3 | director_primary_reject | 76 | F-1 baseline |
| 14:36:47 | stage4_retry_pathology_repeat | 3 | 3 | director_primary_reject | 76 | repeat detection |
| 14:44:37 | stage4_retry_pathology_signal | 3 | 4 | **post_select_conflict** | 98 | **F-1 split-brain** |

## 6. Source Code Anchors

| Finding | File | Line | Evidence |
|---------|------|------|----------|
| F-1 | `modules/core/stage4_interview_round.py` | L5643 | `initial_verdict or None` — empty string becomes NULL |
| F-2 | `modules/core/stage2_finalizer.py` | L2691-2706 | save_stage_attempt call without reasoning fields |
| F-2 | `modules/core/stage3_orchestrator.py` | L1858-1874 | save_stage_attempt call without reasoning fields |
| F-3 | `modules/core/stage2_finalizer.py` | L2837 | `reject_reason=str(audit.get("reason", ""))[:500]` |
| F-4 | `modules/core/stage3_orchestrator.py` | L1875-1879 | save_director_selection call (director_thinking populated by caller or not) |

## 7. DB Schema Reference

### stage_attempts (32 columns)
Key reasoning columns: `reject_reason`, `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives`, `initial_verdict`, `score_breakdown`, `advisory_flags`

### director_selections (22 columns)
Key columns: `verdict`, `score`, `selection_reason`, `verdict_reason`, `pre_firewall_score`, `firewall_triggered`, `firewall_reason`, `director_thinking`, `advisory_warnings`

### attempt_raw_rationale (7 columns)
Key columns: `attempt_key`, `stage`, `ep_num`, `payload_kind`, `payload`
