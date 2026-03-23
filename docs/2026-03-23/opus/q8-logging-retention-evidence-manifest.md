Date: 2026-03-23
Document Type: Q8 evidence manifest (raw/near-raw)
Canonical Path: `docs/2026-03-23/opus/q8-logging-retention-evidence-manifest.md`
Axis: Q8 — logging/retention observability
Terminal: T8

---

## Evidence Sources

### Primary Scope Files Read
1. `modules/domain/agents/director_ensemble.py` — Director LLM parse, score, select, firewall
2. `modules/core/stage4_interview_round.py` — Stage 4 round execution, advisory chain, settlement
3. `modules/core/stage4_director_runtime.py` — Director quality gates, operator display, verdict provenance
4. `modules/core/stage2_finalizer.py` — Stage 2 pass/reject finalization, DB/metric persistence
5. `modules/core/stage3_orchestrator.py` — Stage 3 pass/reject, selection_kwargs builder
6. `modules/core/db_manager.py` — DB save functions (save_stage_attempt, save_director_selection, save_llm_call, save_attempt_raw_rationale)
7. `modules/core/logger.py` — StudioLogger (file-only, no console handler; Rich UI handles console)
8. `modules/core/pass_rate_monitor.py` — AttemptRecord dataclass (62 fields), record_attempt sink
9. `modules/core/metrics_collector.py` — MetricsCollector (numeric aggregation, no text truncation)

### Secondary Scope Files Read
10. `modules/domain/agents/base_agent.py` — L556 thinking_snippet[:5000], L583 error_msg[:80]
11. `modules/core/db_bootstrap_runtime.py` — schema definitions (not detailed in report)
12. `modules/protocols/db_repository.py` — protocol definitions (not detailed in report)

### Context Documents Read
1. `AGENTS.md` — max-retention policy, max-display policy, encoding guardrails
2. `docs/2026-03-23/daily-roadmap-2026-03-23.md` — Q8 axis definition
3. `docs/2026-03-23/current-state-situation-survey-report.md` — risk register item #5 (DB truncation)
4. `docs/2026-03-23/fresh-run-3pass-audit-report.md` — P3-4 CostDB session cost, P3-5 Stage 3 score_breakdown
5. `docs/2026-03-23/llm-codebase-orientation-pack.md` — observability map, 4-layer sink model
6. `docs/2026-03-23/console-log-max-display-post-audit-execution-ssot.md` — Class A/B/C/D operator gap taxonomy
7. `docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md` — Class A/B DB loss taxonomy, 6 execution tranches
8. `docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md` — survey order (this investigation)

---

## Search Inventory

### Grep: `[:N]` truncation across all `modules/**/*.py`
- Total matches: 196KB output (full output persisted)
- Scope-filtered inventory: 81 unique truncation sites across 9 scope files
- Classified: 29 contract-cleanup, 22 ignore (reasonable cap / bounded metadata / error summary / prompt budget)

### Grep: `ui.log` across scope files
- `director_ensemble.py`: 0 direct ui.log calls (uses _operator_log via stage4_director_runtime)
- `stage4_interview_round.py`: 26 ui.log calls
- `stage4_director_runtime.py`: 30 ui.log calls
- `stage2_finalizer.py`: 38 ui.log calls
- `stage3_orchestrator.py`: 44 ui.log calls

### Grep: `save_stage_attempt` / `save_director_selection` call sites
- `stage4_interview_round.py`: 1 save_stage_attempt (via _save_stage4_db_attempt), 1 save_director_selection
- `stage2_finalizer.py`: 2 save_stage_attempt (PASS + REJECT), 2 save_director_selection
- `stage3_orchestrator.py`: 2 save_stage_attempt (PASS + REJECT), 2 save_director_selection

### Grep: firewall / adaptive / score_rewrite patterns
- `director_ensemble.py`: 32 firewall-related lines, _operator_log for all score rewrites
- `stage4_director_runtime.py`: 0 direct firewall mentions (delegated to director_ensemble)

---

## Key Code Anchors

### DB Layer — No Truncation (Design Intent)
- `db_manager.py:2828-2876` — `save_llm_call()`: no Python slicing in INSERT
- `db_manager.py:2878-2981` — `save_stage_attempt()`: no Python slicing in INSERT
- `db_manager.py:2152-2214` — `save_director_selection()`: no Python slicing in INSERT
- `db_manager.py:2836-2837` — `[TF-58] thinking: max-retention, no truncation` comment

### Caller Truncation Points (Policy Violations)
- `base_agent.py:556` — `thinking_snippet = str(thinking_text)[:5000]`
- `base_agent.py:583` — `error_msg=(str(error)[:80] if error else None)`
- `stage4_interview_round.py:5348` — `_selection_reason = (director_result.get("selection_reason") or "")[:500]`
- `stage4_interview_round.py:5349` — `_verdict_reason = (director_result.get("verdict_reason") or _selection_reason)[:500]`
- `stage4_director_runtime.py:685` — `decision.reason[:80]`
- `stage2_finalizer.py:2837` — `reject_reason=str(audit.get("reason", ""))[:500]`

### Stage 2/3 Missing DB Fields
- `stage3_orchestrator.py:1844-1860` — PASS save_stage_attempt: no selection_reason, verdict_reason, open_review, fix_scope_reasoning, runtime_advisory, retry_directives
- `stage3_orchestrator.py:2540-2558` — REJECT save_stage_attempt: same omissions
- `stage2_finalizer.py:2691-2710` — PASS save_stage_attempt: same omissions
- `stage2_finalizer.py:2829-2848` — REJECT save_stage_attempt: same omissions

### Logger Architecture
- `logger.py:76-84` — "글도비" logger: file handler only, no console handler
- `logger.py:92-106` — root logger: StreamHandler removed, FileHandler added
- Implication: `logging.info(...)` → file only, NOT operator visible. `ctx.ui.log(...)` → operator visible via Rich UI

### Advisory Chain Console Output
- `stage4_interview_round.py:4558-4579` — Full advisory lines displayed via ui.log
- `stage4_interview_round.py:4568-4579` — Per-type breakdown with full line content

---

## Cross-Reference with Existing SSOTs

### `console-log-max-display-post-audit-execution-ssot.md` alignment
- Class A (truncation): Confirmed — P1-2, P1-3, P1-4 in this report
- Class B (count-only): Partially confirmed — advisory is now console-visible (per-type lines) but DB-side remains summary
- Class C (provenance): Confirmed — score-mutation provenance on console via _operator_log, but not in DB
- Class D (parity drift): Confirmed — full parity matrix in Appendix B

### `db-logging-integrity-post-audit-execution-ssot.md` alignment
- Class A (Python truncation): Confirmed — P1-1, P1-2, P1-4, plus Stage 2/3 nuances
- Class B (data never reaches DB): Confirmed — P1-5, P1-6, P2-1, P2-3, P2-4
- Tranche 1 (policy flip): Directly maps to P1-1, P1-2, P1-4
- Tranche 2 (existing-contract enrichment): Directly maps to P1-5, P1-6
- Tranche 4 (raw rationale retention): Directly maps to BR-2

### `fresh-run-3pass-audit-report.md` alignment
- P3-4 (CostDB $0.50 vs $6.93): Confirmed design intent — scope-level snapshot_and_reset
- P3-5 (Stage 3 score_breakdown): Confirmed fixed — `record_attempt` now passes `score_breakdown` at L1834/L2530
