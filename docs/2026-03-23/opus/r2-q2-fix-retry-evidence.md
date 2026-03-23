Date: 2026-03-23
Document Type: R2 evidence manifest
Axis: Q2 -- fix/retry quality
Terminal: T2

## Source Anchors

### Code-Fix Verification (Commit 79f570f2)

| Fix | File | Line(s) | Before | After | Evidence Type |
|-----|------|---------|--------|-------|---------------|
| rejection_reason field | `stage4_reject_runtime.py` | 342-343 | `director_feedback` | `director_result.get("verdict_reason") or director_feedback` + `merged_director_feedback` | commit diff + live source |
| contradiction_details | `stage4_reject_runtime.py` | 366-368 | `[:3]` | `[:5]` (commit), full list (dirty) | commit diff + dirty diff + live source |
| re-audit warnings | `stage4_retry_runtime.py` | 600 | `current_feedback[:500]` | `current_feedback[:2000]` | commit diff + live source |
| re-audit focus_points | `stage4_retry_runtime.py` | 602 | `current_feedback[:300]` | `current_feedback[:1000]` | commit diff + live source |
| retry_directives | `stage4_interview_round.py` | 649-650 | `" / ".join()[:500]` | `"\n".join()` (dirty) | commit diff + dirty diff + live source |
| _compact_text signature | `stage4_interview_round.py` | 458-461 | `limit: int = 500` | `limit: int or None = 500` | commit diff |
| _join_unique_lines default | `stage4_interview_round.py` | 468 | `limit: int = 500` | `limit: int or None = None` | commit diff |
| advisory digest max_items | `stage4_interview_round.py` | 195-198 | `max_items=5`, `text[:240]` | `max_items=None`, no truncation | commit diff |
| validation evidence limit_per_key | `stage4_interview_round.py` | 492 | `3` | `None` | commit diff |
| contradiction detail max_items | `stage4_interview_round.py` | 618 | `3` | `None` | commit diff |
| truth_gate/violations/quality warnings | `stage4_interview_round.py` | 629-643 | `[:3]` per type | full | commit diff |
| fix_pack fields | `stage4_interview_round.py` | 5113-5145 | `[:6]`, `[:5]`, `[:220]` | full | commit diff |
| DB attempt payload | `stage4_interview_round.py` | 5606+ | 6 fields | +6 new fields (failure_category, initial_verdict, score_breakdown, is_patch, is_patch_fallback, patch_strategy) | commit diff |

### Dirty State Verification

| Fix | File | Committed State | Dirty State | Evidence Type |
|-----|------|----------------|-------------|---------------|
| contradiction_details | `stage4_reject_runtime.py` | `[:5]` | full list, `[pre-rerun]` comment | dirty diff |
| validation_warnings | `stage4_reject_runtime.py` | `limit=20` | `limit=50`, `[pre-rerun]` comment | dirty diff |
| retry_directives join | `stage4_interview_round.py` | `" / ".join()` | `"\n".join()`, `[pre-rerun] 구조 보존` comment | dirty diff |

### Persisting Issues

| Finding | File | Line(s) | Evidence Type |
|---------|------|---------|---------------|
| V60.97 swap mechanism | `director_ensemble.py` | 907-913 | live source |
| Pass rate counter: phase3_pass | `three_phase_blueprint_runtime.py` | 1111 | live source |
| Pass rate counter: phase3_reject (fix failure) | `three_phase_blueprint_runtime.py` | 981 | live source |
| Pass rate counter: phase3_reject (continuity) | `three_phase_blueprint_runtime.py` | 531 | live source |
| Pass rate counter: phase3_reject (validation) | `three_phase_blueprint_runtime.py` | 1157 | live source |
| Quality gate threshold 90 | `three_phase_blueprint_runtime.py` | 682 | live source |
| DB verdict_reason 500 truncation | `stage4_interview_round.py` | 399-401 | live source |
| DB feedback_provenance 500 truncation | `stage4_interview_round.py` | 5461-5463 | live source |
| Stage 3 retry feedback [:1200] | `three_phase_blueprint_runtime.py` | 186-187 | live source |
| Terminal failure feedback [:200] | `three_phase_blueprint_runtime.py` | 1082 | live source |

### Fresh Run Evidence (0_0323)

| Finding | Source | Evidence Type |
|---------|--------|---------------|
| Ep3 5-round fix/retry cycle | `projects/0_0323/logs/pass_rate_monitor.json` | artifact |
| Ep3 R2 patch failure (empty_candidates) | `projects/0_0323/logs/pass_rate_monitor.json` attempt_num=2 | artifact |
| Ep3 R4 A-3 downgrade (post_select_conflict) | `projects/0_0323/logs/pass_rate_monitor.json` attempt_num=4 | artifact |
| Ep3 R5 patch mode success | `projects/0_0323/logs/pass_rate_monitor.json` attempt_num=5 | artifact |
| rejection_reason field carries verdict_reason | `projects/0_0323/logs/pass_rate_monitor.json` R1 entry | artifact |
| V60.97 non-trigger across all Stage 4 episodes | `projects/0_0323/logs/pass_rate_monitor.json` all S4 entries | artifact |
| Stage 3 no PASS_WITH_FIX->failure path | `projects/0_0323/logs/pass_rate_monitor.json` all S3 entries | artifact |

### Cross-Reference Reports

| Report | Key Finding Absorbed |
|--------|---------------------|
| T5 `pre-rerun-root-cause-t5-stage4-write-fix.md` | F-1 (patch failure), F-2 (feedback non-convergence), F-3 (DB truncation), F-5 (retry_directives), F-6 (empty snapshot), F-7 (contradiction) |
| T7 `pre-rerun-root-cause-t7-verdict-chain.md` | F-1 (post-select correct), F-6 (V60.97 safeguards) |
| 7-axis `director-pipeline-7axis-deep-dive.md` | H-1 through H-7 (feedback flow hotspots) |
| Merge audit `q1-q8-current-state-merge-audit.md` | Q2 "1 stale" re-evaluated as "persists (P2)" |

## Inventory Notes

- Total primary scope files read: 3 (stage4_retry_runtime.py, stage4_reject_runtime.py, director_ensemble.py)
- Total supporting files read: 2 (stage4_interview_round.py, three_phase_blueprint_runtime.py)
- Commit diffs verified: 3 files in 79f570f2
- Dirty state diffs verified: 2 files
- Context docs read: 11 (per R2 survey order Section 11)
- Fresh run artifacts inspected: pass_rate_monitor.json, decisions.jsonl, runtime_audit.jsonl
- All line numbers verified against live workspace at dirty state (post-79f570f2 + uncommitted)
