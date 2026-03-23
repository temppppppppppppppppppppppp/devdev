Date: 2026-03-23
Status: final
Document Type: T2 lane evidence manifest
Lane: T2 — Verdict / Persistence / Operator
Parent Report: `docs/2026-03-23/opus/rol-live-merge-t2-verdict-persistence-operator.md`

---

## Source File Anchors

### Verdict Chain

| File | Lines | Surface |
|---|---|---|
| `modules/core/stage4_director_runtime.py` | L631-703 | Decision payload wrapping, provisional tag, console log |
| `modules/domain/agents/director_ensemble.py` | L939-952 | CONDITIONAL_PASS generation (V60.97 swap) |
| `modules/domain/agents/director_ensemble.py` | L1187-1204 | CONDITIONAL_PASS resolution to PASS/REJECT |
| `modules/core/stage4_interview_round.py` | L2306-2327 | `save_director_selection()` — DB write BEFORE post-select |
| `modules/core/stage4_interview_round.py` | L3575-3743 | `_run_post_select_checks()` — parallel continuity+history |
| `modules/core/stage4_interview_round.py` | L3685 | `verdict = "REJECT"` downgrade |
| `modules/core/stage4_interview_round.py` | L3692-3703 | `error_category` assignment (POST_SELECT_*) |
| `modules/core/stage4_interview_round.py` | L3714-3741 | `previous_attempt` dict construction (missing `fix_pack`) |
| `modules/core/stage4_interview_round.py` | L3772-3831 | `_process_verdict()` — PASS/PASS_WITH_FIX check at L3808 |
| `modules/core/stage4_interview_round.py` | L3794-3797 | Quality gate downgrade PASS→REJECT + QUALITY_FLOOR_FAIL |

### Reject / Retry

| File | Lines | Surface |
|---|---|---|
| `modules/core/stage4_reject_runtime.py` | L119-127 | Fallback error_category derivation from reject_bucket |
| `modules/core/stage4_reject_runtime.py` | L457-464 | Lane3 Gate widening to partial |
| `modules/core/stage4_reject_runtime.py` | L485,499 | ToT/MAD output truncation `[:1000]` |
| `modules/core/stage4_reject_runtime.py` | L600,602 | Reaudit feedback truncation `[:2000]`, `[:1000]` |
| `modules/core/stage4_retry_runtime.py` | L840-842 | `_evaluate_fix_pack_contract(None)` → missing_patch_targets |
| `modules/core/stage4_retry_runtime.py` | L852-858 | Consecutive empty patch detection |

### Persistence

| File | Lines | Surface |
|---|---|---|
| `modules/core/stage4_interview_round.py` | L5608-5670 | `_build_stage4_db_attempt_payload()` — failure_category mapping |
| `modules/core/stage4_interview_round.py` | L5647 | `failure_category: failure_category or None` |
| `modules/core/stage4_interview_round.py` | L5806 | `_save_stage4_db_attempt()` call |
| `modules/core/stage4_interview_round.py` | L5748 | `pass_rate_monitor.record_attempt()` — Stage 4 only |
| `modules/core/db_manager.py` | L2878-2910 | `save_stage_attempt()` signature |
| `modules/core/db_bootstrap_runtime.py` | L472-500 | `stage_attempts` table schema |
| `modules/core/pass_rate_monitor.py` | L33-65 | `AttemptRecord` dataclass fields |
| `modules/core/services/audit_service.py` | L33-39 | Authoritative sinks list (includes ghost `session_decisions`) |

### Stage 2/3 Parity

| File | Lines | Surface |
|---|---|---|
| `modules/core/stage3_orchestrator.py` | L1854-1883 | Stage 3 PASS `save_stage_attempt()` — missing fields |
| `modules/core/stage3_orchestrator.py` | L2628-2635 | Stage 3 REJECT `save_stage_attempt()` — missing fields |
| `modules/core/stage2_finalizer.py` | L2691 | Stage 2 PASS `save_stage_attempt()` — missing `initial_verdict` |
| `modules/core/stage2_finalizer.py` | L2829 | Stage 2 REJECT `save_stage_attempt()` |
| `modules/core/stage2_finalizer.py` | L2837 | `reject_reason[:500]` truncation — policy violation |

### Feedback Accumulation

| File | Lines | Surface |
|---|---|---|
| `modules/core/stage4_interview_round.py` | L572-671 | `_build_retry_feedback_provenance()` |
| `modules/core/stage4_interview_round.py` | L590-601 | `prev_general_lines` extraction |
| `modules/core/stage4_interview_round.py` | L648-650 | `retry_directives` concatenation — no cap |
| `modules/core/stage4_interview_round.py` | L420 | `_compact_text(..., limit=None)` — explicitly uncapped |

## Live Evidence Anchors

### Console

| Line | Signal |
|---|---|
| `console.txt:526` | Ep1 R1 Director PASS score=96 |
| `console.txt:606` | Ep2 R1 Director PASS score=95 |
| `console.txt:690` | Ep3 R1 Director REJECT score=44 (continuity_firewall) |
| `console.txt:753-772` | Ep3 R2 Director PASS_WITH_FIX score=90 → post-select REJECT |
| `console.txt:888-901` | Ep3 R3 Director PASS score=95 → post-select REJECT |
| `console.txt:1025-1038` | Ep3 R4 Director PASS score=95 → post-select REJECT |
| `console.txt:1061` | `Fix Pack patch_targets is empty` — Lane3 Gate widening |
| `console.txt:1135` | `[QR-7] 점수 plateau` — score stuck at 95 |
| `console.txt:1144` | User abort during R5 |

### DB (projects/0_0323)

| Table | Rows | Key Observation |
|---|---|---|
| `stage_attempts` | 12 | Stage 2: 1, Stage 3: 4, Stage 4: 7. All `failure_category = NULL`. |
| `director_selections` | 11 | 6 unique Stage 4 attempt_keys. 1 orphan `stage_attempts` row without match. |
| `attempt_raw_rationale` | present | `director_thinking` 2.9K→4.2K chars, `advisory_warnings_raw` 1.3K→2.1K chars. |

### JSONL / Metrics

| File | Records | Key Observation |
|---|---|---|
| `pass_rate_monitor.json` | 11 | Stage 4 only. `fix_pack_ready=False`, `fix_pack_reason=missing_patch_targets` on R3-R4. |
| `episode_production.jsonl` | present | Stage 4 escalation events only. |
| `runtime_audit.jsonl` | present | Auto-correct, db_commit, state_extracted events. No per-attempt verdict records. |

## Finding-to-Evidence Cross-Reference

| Finding | Static Anchor | Live Anchor | Triangulated? |
|---|---|---|---|
| F-1 Post-select DB gap | interview_round.py:2306→3685 | DB shows PASS where runtime used REJECT | yes |
| F-2 Missing fix_pack | interview_round.py:3714 | console.txt:1061 empty patch_targets | yes |
| F-3 failure_category NULL | interview_round.py:3697,5647 | All 7 S4 rows NULL in DB | yes |
| F-4 Stage 2/3 parity | stage3_orchestrator.py:1860 | All S2/S3 rows thin in DB | yes |
| F-5 retry_directives growth | interview_round.py:420,648 | pass_rate_monitor R3-R4 growing | yes |
| F-6 Quality gate error_category | interview_round.py:3794-3797 | not triggered in run | static-only |
| F-7 session_decisions ghost | audit_service.py:37 | no JSONL file exists | static-only |
| F-8 Pass rate S2/S3 gap | only S4 calls record_attempt | 0 S2/S3 records in monitor | yes |
| F-9 Truncation caps | reject_runtime.py:485,499 | — | static-only |
