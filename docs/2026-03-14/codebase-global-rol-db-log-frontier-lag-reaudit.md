# Codebase Global ROL DB Log Frontier Lag Re-Audit

Date: 2026-03-14
Status: final
Canonical Path: `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-reaudit.md`
Related Evidence Manifest: `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-reaudit-evidence-manifest.md`
Roadmap Policy: `single-ssot`
Confidence Model: `docs/implementation/integrity-confidence-scoring-contract.md`
Confidence Target: 95%
Commit State:
- Baseline Commit: `2a4d45a4896282d9cf96e67e8daff9dd0287ef4f`
- Baseline Dirty Summary: `dirty: 7 tracked, 3 untracked; hotspots: docs/implementation/*, 260314-print.txt`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Predecessor Survey Docs:
- `docs/2026-03-14/codebase-global-rol-deep-global-survey.md`
- `docs/2026-03-14/codebase-global-rol-post-closure-reaudit.md`
- `docs/2026-03-14/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md`
- `docs/2026-03-14/auto-frontier-lag-n-arc-test-harness-ssot.md`

## 1. Intent
- Re-audit the live workspace after the earlier 2026-03-14 closure and reopen only the DB/log/menu `7` tracks contradicted by fresh evidence.
- Treat `260314-print.txt` as a first-class live artifact rather than as an informal note.
- Keep this cycle documentation-only while producing execution-ready follow-on SSOTs.

## 2. Scope Lock
- included surfaces:
  - `260314-print.txt`
  - `main_a.py`
  - `modules/core/db_manager.py`
  - `modules/core/services/audit_service.py`
  - `modules/core/stage2_orchestrator.py`
  - `modules/core/stage3_orchestrator.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/pass_rate_monitor.py`
  - `projects/00_20260314/project_data.db`
  - `projects/00_20260314/logs/session_20260314_213845.log`
  - `projects/00_20260314/logs/runtime_audit_summary.json`
  - `projects/00_20260314/logs/pass_rate_monitor.json`
  - `projects/00_20260314/logs/session/decisions.jsonl`
  - `projects/00_20260314/logs/episode_production.jsonl`
  - `error.log`
- excluded surfaces:
  - implementation of the reopened fixes
  - unrelated build and archive outputs
  - historical docs not required to resolve current contradictions
- mode lock:
  - survey-only
  - no code edits
  - no DB mutation
  - no runtime replay beyond read-only analysis commands
- evidence basis:
  - `docs/2026-03-14/db-log-frontier-lag-reaudit-prompt-sites.txt`
  - `docs/2026-03-14/db-log-frontier-lag-reaudit-sink-alignment.json`
  - `docs/2026-03-14/db-log-frontier-lag-reaudit-migration-noise.txt`
  - `docs/2026-03-14/db-log-frontier-lag-reaudit-encoding-samples.txt`

## 3. Coverage Matrix
- macro views covered:
  - reopened operator contract for interactive menu `7`
  - reopened runtime proof-digest trust boundary
  - reopened DB bootstrap/audit-summary interaction
- micro views covered:
  - exact prompt call sites
  - exact attempt-key sink joins
  - exact duplicate-column timestamp clusters
  - exact encoding/decode samples
- cross-cut views covered:
  - persistence sink alignment
  - UI-event mirroring durability
  - operator-visible artifact encoding boundaries
  - predecessor-document contradiction handling
- operational views covered:
  - reopened queue justification
  - execution SSOT mapping
  - single-roadmap authority

## 4. Macro View
- The older macro topology from `docs/2026-03-14/codebase-global-rol-deep-global-survey.md` remains valid. Runtime authority is still concentrated in `main_a.py`, persistence in `DBManager`, and audit proof generation in `AuditService`.
- The closed `docs/2026-03-14/codebase-global-rol-post-closure-reaudit.md` is no longer sufficient for this bundle. Its “no fresh P1” conclusion is contradicted by current menu `7`, sink-alignment, and UI-event evidence.
- `docs/2026-03-14/residual-print-ui-log-db-full-survey-3pass-execution-ssot.md` remains directionally valid about the intended `ui.log` plus durable sink substrate, but the current session proves that `ui_events` DB mirroring is still partially failing.
- `docs/2026-03-14/auto-frontier-lag-n-arc-test-harness-ssot.md` remains valid for bounded harness semantics such as `batch_size_override`, but it does not settle the interactive operator contract for menu `7`.

## 5. Micro View
- Menu `7` still prompts on the normal path. `main_a.py:4186-4193` asks for the initial Arc batch size, and `260314-print.txt:255-256` plus `session_20260314_213845.log:335-339` confirm that the prompt fired during the observed run.
- Menu `7` is only partially non-interactive today. `main_a.py:4295` and `main_a.py:4317` still ask skip-or-abort on Stage 3 failure or exception, while `main_a.py:4386-4388` still optionally waits for menu return.
- The saved `runtime_audit_summary.json` overstates current sink misalignment. It was written at `22:10:51`, before `pass_rate_monitor.json` reached its `22:11:26` final state, so the saved `pass_rate_monitor: 0` coverage is stale.
- Live analyzer output with `include_session_decisions=True` shows `stage3.status = ok` and narrows Stage 4 to only two `selection_reason` mismatches.
- Those two mismatches split cleanly:
  - truncation drift: `director_selections.selection_reason` is truncated to 200 chars in `modules/core/db_manager.py:2714`, while `stage_attempts` keeps 500 chars at `modules/core/db_manager.py:3190`
  - patch provenance drift: `modules/core/stage4_interview_round.py:2012-2017` prefixes `director_selections.selection_reason` with `[patch|score=...]`, while session and episode sinks keep human rationale only
- `ui_events` DB mirroring still rejects string stage labels. The session log records `save_ui_event failed (non-blocking)` for `stage0`, `stage3`, `stage4`, and `shutdown`, with counts `89`, `6`, `78`, and `10`.
- Duplicate-column migration noise repeats four times in the same session. The clusters align with project boot and `write_audit_summary(...)` calls from Stage 2, Stage 3, and Stage 4.
- Encoding evidence is boundary-localized: authoritative source text is fine, UTF-8 operator artifacts remain readable, but `error.log` is UTF-16 and embeds mojibake UI prompt lines.

## 6. Cross-Cut Integrity Matrix

| Surface | Saved or Prior Claim | Fresh Live Evidence | Integrity Judgment | Action Track |
| --- | --- | --- | --- | --- |
| Menu `7` normal path | earlier queue closure left one initial prompt intact | prompt still fires at `main_a.py:4186-4193` and in `260314-print.txt:255-256` | contradicted for current operator contract | `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md` |
| Runtime proof digest | `runtime_audit_summary.json` says Stage 3/4 final sinks are missing | live analyzer after monitor flush shows Stage 3 `ok` and Stage 4 narrowed to rationale drift | stale timing plus residual rationale drift | `docs/2026-03-14/runtime-audit-rationale-sink-alignment-remediation-execution-ssot.md` |
| Stage 4 rationale fields | saved summary reports `selection_reason_mismatches = 2` | live join confirms two real mismatches driven by truncation and patch prefix | confirmed and root-caused | `docs/2026-03-14/runtime-audit-rationale-sink-alignment-remediation-execution-ssot.md` |
| `ui_events` DB mirror | prior operator-surface work implied durable mirroring | current session still logs stage-label type failures | contradicted and reopened | `docs/2026-03-14/runtime-audit-rationale-sink-alignment-remediation-execution-ssot.md` |
| DB bootstrap compatibility logs | prior closure did not flag new queue item | `80` duplicate-column lines across four clusters | noisy but bounded; now action-bearing because repeated during audit summaries | `docs/2026-03-14/db-bootstrap-migration-noise-remediation-execution-ssot.md` |
| Encoding boundary | earlier mojibake track was treated as closed | source and UTF-8 artifacts are clean, but `error.log` remains boundary-corrupted | reopened as boundary-specific, not source-wide | `docs/2026-03-14/encoding-boundary-mojibake-refresh-remediation-execution-ssot.md` |

## 7. Operational and Regression View
- The reopened queue is intentionally narrow. It is evidence-heavy, but it does not reclassify the entire repo as unstable.
- The future implementation surface is concentrated in:
  - `main_a.py`
  - `modules/core/services/audit_service.py`
  - `modules/core/db_manager.py`
  - `modules/core/stage4_interview_round.py`
  - Stage 2/3/4 orchestrator call sites
- Existing tests that should absorb the future remediation include:
  - `tests/test_one_stop_frontier_lag_auto_continue.py`
  - `tests/test_auto_frontier_lag_harness.py`
  - `tests/test_failure_analyzer.py`
  - `tests/test_audit_service.py`
  - `tests/test_safe_ops_db_consistency.py`
  - `tests/test_encoding_boundary_contract.py`
- The reopened queue will be governed only by `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-execution-roadmap.md`.

## 8. Contradiction and Uncertainty Ledger
- Contradiction 1:
  - prior authority: `docs/2026-03-14/codebase-global-rol-post-closure-reaudit.md` reported no fresh `P1`
  - fresh evidence: menu `7`, proof-digest timing, rationale drift, and `ui_events` DB failures justify a new queue
- Contradiction 2:
  - prior authority: `docs/2026-03-14/auto-frontier-lag-n-arc-test-harness-ssot.md` documented harness seams, not interactive menu policy
  - fresh evidence: the user-facing menu `7` contract now requires normal-path non-stop behavior
- Contradiction 3:
  - saved artifact: `runtime_audit_summary.json` reports `final_sink_missing`
  - live evidence: post-flush sink alignment removes those Stage 3 and final-sink Stage 4 misses
- Residual uncertainty:
  - the exact terminal-host mechanism that corrupts stderr-rendered prompts beyond the confirmed PowerShell UTF-16 wrapper is not fully isolated
  - that uncertainty is bounded and does not affect the source-vs-boundary judgment

## 9. Severity and Action Map

### P0
- none found

### P1
- menu `7` interactive normal path still stops for initial Arc-count input
- `runtime_audit_summary.json` is stale enough to misreport Stage 3/4 final-sink coverage
- Stage 4 `selection_reason` contract still diverges across sinks because of truncation and patch prefixing
- `ui_events` DB mirroring still rejects string stage labels and silently drops durable rows

### P2
- duplicate-column compatibility logging is repeated and operator-visible during the same session
- `error.log` remains a boundary-corrupted artifact and should not be treated as authoritative operator truth

## 10. Execution SSOT Mapping
- `docs/2026-03-14/frontier-lag-nonstop-contract-remediation-execution-ssot.md`
  - remove the initial normal-path Arc-count prompt while preserving bounded harness overrides and failure-path safety prompts
- `docs/2026-03-14/runtime-audit-rationale-sink-alignment-remediation-execution-ssot.md`
  - fix summary-write timing, rationale normalization, and `ui_events` stage-label persistence
- `docs/2026-03-14/db-bootstrap-migration-noise-remediation-execution-ssot.md`
  - stop audit-summary re-entry from re-running noisy compatibility migration loops
- `docs/2026-03-14/encoding-boundary-mojibake-refresh-remediation-execution-ssot.md`
  - re-establish authoritative UTF-8 operator artifact rules and quarantine boundary-only stderr capture

## 11. Single SSOT Roadmap Lineage
- The predecessor codebase-global system survey roadmap remains historically closed and is not reopened by this bundle.
- The reopened queue is governed only by `docs/2026-03-14/codebase-global-rol-db-log-frontier-lag-execution-roadmap.md`.
- No second roadmap is justified for this bundle because all current action items fit under one evidence-triangulated queue.

## 12. Confidence Summary
- Re-audit confidence: `96%`
- Why the 95% gate is met:
  - all action-bearing claims are tied to exact code or artifact locations
  - predecessor contradictions are explicit rather than implied
  - the reopened queue is narrow and decision-complete enough for implementation handoff
- Remaining uncertainty is disclosed and bounded instead of hidden, so no corrective rewrite should be required before execution planning.
