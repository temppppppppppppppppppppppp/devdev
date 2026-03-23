Date: 2026-03-23
Document Type: R2 Q8 evidence manifest
Canonical Path: `docs/2026-03-23/opus/r2-q8-logging-retention-evidence.md`
Axis: Q8 — logging/retention R2 delta survey
Terminal: T8

---

## Evidence Sources

### Primary Scope Files Read
1. `modules/core/db_manager.py` — DB save functions, schema, truncation patterns
2. `modules/core/stage4_interview_round.py` — Stage 4 settlement, advisory chain, JSONL, DB attempt save
3. `modules/domain/agents/director_ensemble.py` — Director operator display, score provenance, _log_director_frame
4. `modules/core/stage3_orchestrator.py` — Stage 3 save_stage_attempt, save_director_selection, session_logger
5. `modules/core/stage4_reject_runtime.py` — Stage 4 reject console display
6. `modules/domain/agents/base_agent.py` — _log_llm_call_to_db, thinking_snippet, error_msg

### Secondary Scope Files Read
7. `modules/core/stage2_finalizer.py` — Stage 2 save_stage_attempt, reject_reason truncation, console display

### Context Documents Read
1. `AGENTS.md` — max-retention, max-display policy
2. `docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md` — R2 survey order
3. `docs/2026-03-23/opus/q8-logging-retention-deep-dive.md` — R1 report
4. `docs/2026-03-23/opus/q8-logging-retention-evidence-manifest.md` — R1 evidence
5. `docs/2026-03-23/q1-q8-current-state-merge-audit.md` — merge audit
6. `docs/2026-03-23/fresh-run-3pass-audit-report.md` — fresh run report
7. `docs/2026-03-23/opus/pre-rerun-root-cause-t8-verdict-parity.md` — T8 parity report
8. `docs/2026-03-23/opus/console-log-max-display-audit.md` — console audit
9. `docs/2026-03-23/opus/db-logging-integrity-audit.md` — DB audit

---

## Git Evidence

### Commit 79f570f2 Diff Coverage
- `db_manager.py`: 139 insertions, verified line-by-line. 18 truncation removals + 5 new columns + 2 new methods.
- `director_ensemble.py`: 171 insertions. Operator truncation removal (15+ sites), _operator_log additions (6 sites), _director_thinking wiring (3 stages).
- `stage4_interview_round.py`: 326 insertions. `_compact_text()` limit=None, `_join_unique_lines()` limit=None, `_normalize_fix_pack()` limits=None, advisory per-type display, `_build_raw_advisory_payload()`, adjunct save, initial_verdict wiring.
- `stage3_orchestrator.py`: 61 insertions. Console error truncation removal (6 sites), log file truncation removal, director_thinking in selection_kwargs, score_breakdown in pass_rate_monitor.
- `stage4_reject_runtime.py`: 5 lines. Minor (rejection_reason truncation in reject path — still has `[:100]` at L548).

### Dirty Workspace Delta
- `stage3_orchestrator.py`: `_build_stage3_success_operator_lines()` added — Stage 3 PASS Director reasoning on console.
- `director_ensemble.py`: `_apply_ensemble_gates()` 4-method split — structural refactor only.
- `stage4_interview_round.py`: retry_directives format change — " / " → "\n".

---

## Live Source Grep Results

### db_manager.py residual truncation
```
L980:   traceback.format_exc()[:300]  — internal debug, NOT DB save
L1750:  traceback.format_exc()[:300]  — internal debug, NOT DB save
L2076:  str(e)[:80]                   — internal error log, NOT DB save
L3087:  str(message or "")[:4000]     — ui_events.message, reasonable cap
L3002:  str(prompt_id or "")[:200]    — bounded identifier
L3003:  str(artifact_path or "")[:1000] — bounded path
```

### director_ensemble.py residual truncation
```
L1552:  str(blueprint.get("ending_hook") or "?")[:100]  — Director prompt text, NOT operator display
L1936:  str(exc)[:80]                                    — error logging, reasonable
```

### stage4_interview_round.py residual truncation
```
L5368:  selection_reason[:500]     — JSONL settlement (DB path clean)
L5369:  verdict_reason[:500]       — JSONL settlement (DB path clean)
L5434:  action_items[:5]           — JSONL settlement (DB path clean)
L5436:  open_review[:300]          — JSONL settlement (DB path clean)
L5002:  _w.get('text', '')[:120]   — NumericConsistency advisory line
L4649+: str(_err)[:80] (×9)        — Advisory chain error logging, reasonable
```

### stage2_finalizer.py residual truncation (caller-side DB violation)
```
L2837:  reject_reason[:500]        — save_stage_attempt caller-side truncation (POLICY VIOLATION)
L1878:  reason[:500]               — session_logger, NOT DB
L3006:  reject_reason[:100]        — pass_rate_monitor, NOT DB
```

### stage3_orchestrator.py residual truncation
```
L2260:  reject_reason[:500]        — session_logger, NOT DB
L2261:  reason[:500]               — session_logger, NOT DB
L2262:  selection_reason[:500]     — session_logger, NOT DB
L2263:  verdict_reason[:500]       — session_logger, NOT DB
```

---

## Fresh-Run DB Evidence (projects/0_0323/project_data.db)

### stage_attempts Field Population

| id | stage | verdict | score | sr_len | vr_len | or_len | fsr_len | ra_len | initial_verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2 | PASS | 100 | 0 | 0 | 0 | 0 | 0 | NULL |
| 2 | 3 | PASS | 92 | 0 | 0 | 0 | 0 | 0 | NULL |
| 3 | 3 | PASS | 95 | 0 | 0 | 0 | 0 | 0 | NULL |
| 4 | 3 | PASS | 95 | 0 | 0 | 0 | 0 | 0 | NULL |
| 5 | 3 | PASS | 98 | 0 | 0 | 0 | 0 | 0 | NULL |
| 6 | 4 | PASS | 98 | 219 | 219 | 80 | 21 | 377 | PASS |
| 7 | 4 | PASS | 98 | 183 | 183 | 141 | 34 | 637 | PASS |
| 8 | 4 | REJECT | 80 | 147 | 76 | 237 | 186 | 878 | NULL |
| 9 | 4 | EMPTY | 0 | 0 | 0 | 0 | 0 | 0 | NULL |
| 10 | 4 | REJECT | 76 | 192 | 123 | 228 | 121 | 680 | NULL |
| 11 | 4 | REJECT | 98 | 239 | 239 | 89 | 114 | 770 | NULL |
| 12 | 4 | PASS | 98 | 202 | 202 | 144 | 18 | 528 | PASS |

Stage 2/3 vs Stage 4 reasoning field population gap confirmed.

### director_selections Director Thinking

| id | stage | director_thinking_len |
|---|---|---|
| 1 | 2 | 4767 |
| 2-5 | 3 | 0 |
| 6-11 | 4 | 2602-4333 |

Stage 3 director_thinking = 0 confirmed in PRE-fix data. Post-fix wiring exists but unverified by fresh run.

### attempt_raw_rationale Distribution

| stage | payload_kind | count | avg_payload_len |
|---|---|---|---|
| 4 | advisory_warnings_raw | 6 | 2805 |
| 4 | director_thinking | 6 | 3300 |

Stage 4 only. Stage 2/3 = 0 rows.
