# DB Logging Integrity Max-Retention Execution SSOT

Date: 2026-03-23
Status: closed
Canonical Path: `docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md`
Temp Mirror Path: removed after closure
Commit State:
- Baseline Commit: `79f570f2`
- Baseline Dirty Summary: `dirty: active 2026-03-23 docs/runtime/test edits plus project log artifacts`
- Resume Commit: `79f570f2`
- Resume Drift Summary: `live DB sample plus Stage 4 persistence regression re-audit on 2026-03-23`
Source Survey Docs:
- `docs/2026-03-23/opus/db-logging-integrity-audit.md`
Evidence Artifacts:
- `projects/0_0323/project_data.db`
- `live sqlite sample on 2026-03-23; no separate evidence manifest`
Side-Effect Coverage: covered

## 1. Intent
- Keep the DB logging wave authoritative, but reduce it to the real residual work left in live code.
- Preserve the existing max-retention direction.
- Close this item after current live evidence and current write-path regression evidence jointly prove that Stage 4 failure classification and raw/detail linkage survive the active code path.

## 2. Baseline Facts
- The original survey is now mostly implemented in live code.
- Already realized in live code and DB:
  - `llm_calls.error_msg` and `llm_calls.thinking_snippet` are no longer truncated before `save_llm_call()`
  - `stage_attempts` accepts and stores `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives`, `initial_verdict`, `score_breakdown`, patch flags, and `patch_strategy`
  - `director_selections.director_thinking` exists and is populated on recent Stage 4 rows
  - `attempt_raw_rationale` exists and is populated with `director_thinking` and `advisory_warnings_raw`
- Live DB sampling from `projects/0_0323/project_data.db` confirms:
  - recent `director_selections` rows contain non-empty `director_thinking`
  - recent `attempt_raw_rationale` rows contain non-empty raw payloads linked by `attempt_key`
  - recent `stage_attempts` rows contain non-empty `score_breakdown`
- Current regression evidence confirms:
  - `Stage4InterviewRound._save_stage4_db_attempt()` forwards `error_category -> failure_category`
  - `Stage4RejectRuntime._record_reject_attempt_artifact()` forwards reject-path `error_category` into the Stage 4 attempt recorder
  - `DBManager.save_stage_attempt()` persists non-null `failure_category` and rich rationale/detail fields without truncation
- Interpreted closure fact:
  - sampled project DB `REJECT` rows with `failure_category = NULL` are treated as pre-closure baseline evidence, while the current write path is now re-proven by targeted Stage 4 and DB persistence tests

## 3. Operating Policy
- During the current transition phase, default policy remains `store as much as practical`.
- Do not reintroduce Python truncation for DB-backed evidence fields.
- Keep summary rows and raw adjunct rows linked by stable keys.
- Treat cleanup, pruning, archival, or backfill as separate work.

## 4. Scope
Included:
- `modules/domain/agents/base_agent.py`
- `modules/core/db_manager.py`
- `modules/core/db_bootstrap_runtime.py`
- `modules/protocols/db_repository.py`
- `modules/core/stage4_interview_round.py`
- targeted tests and live DB inspection for Stage 4 retention surfaces

Excluded:
- verdict policy changes
- retry policy changes
- prompt changes
- archival, pruning, compression, or backfill
- console/operator-display work governed by the console SSOT

## 5. Residual Inventory
Realized baseline:
- Stage 4 detail columns and raw adjunct retention are live.
- Raw `director_thinking` and raw advisory bundles are durably written.
- Expanded rationale text is durably written on current write paths.

Closure evidence:
1. Stage 4 reject-classification write path
   - current Stage 4 reject/runtime tests prove `error_category -> failure_category` survives the active save seam
2. Read-path linkage
   - sampled live DB rows can be reconstructed across:
     - `stage_attempts`
     - `director_selections`
     - `attempt_raw_rationale`

## 6. Acceptance Criteria
- The current Stage 4 `REJECT` write path stores non-null `failure_category` when runtime `error_category` exists.
- `stage_attempts`, `director_selections`, and `attempt_raw_rationale` can be joined by stable attempt linkage for the same Stage 4 attempt.
- `director_thinking` and raw advisory payloads remain durably recoverable from DB.
- `score_breakdown`, patch/detail fields, and rich rationale fields remain queryable on recent rows.
- No verdict or retry semantics change.

## 7. Verification Plan
- `python -m py_compile modules/domain/agents/base_agent.py modules/core/db_manager.py modules/core/db_bootstrap_runtime.py modules/protocols/db_repository.py modules/core/stage4_interview_round.py`
- targeted low-memory pytest shards covering:
  - DB logging persistence
  - Stage 4 attempt persistence
  - bootstrap schema and migration coverage
  - raw rationale linkage and retrieval
- closure evidence used:
  - sampled live DB inspection on `projects/0_0323/project_data.db`
  - `tests/test_stage4_interview_round.py`
  - `tests/test_db_manager.py`
- `python scripts/check_utf8_hygiene.py docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 8. Guardrails
- Do not reopen this item unless new live evidence shows reject-path classification drift.
- Do not broaden this item into cleanup or historical migration work.
- Treat the next real Stage 4 `REJECT` sample as monitoring evidence, not as a closure blocker.

## 9. Temp Queue Notes
- temp status: removed after closure
- cleanup condition:
  - satisfied
- roadmap dependency:
  - `docs/2026-03-23/max-retention-observability-execution-roadmap.md`

## 10. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- closure evidence used:
  - live DB linkage inspection
  - targeted Stage 4 reject-path regression tests

## 11. Closure Note
- Closure decision: `closed`
- Why now:
  - max-retention schema and write seams are landed
  - live DB inspection proves `director_thinking`, raw advisory payloads, and `attempt_key` linkage on recent Stage 4 rows
  - targeted Stage 4 and DB persistence tests now prove the active reject path forwards and stores `failure_category`
- Verification summary:
  - `python -m py_compile modules/domain/agents/base_agent.py modules/core/db_manager.py modules/core/db_bootstrap_runtime.py modules/protocols/db_repository.py modules/core/stage4_interview_round.py tests/test_stage4_interview_round.py`
  - `python -m pytest tests/test_stage4_interview_round.py -q`
  - `python -m pytest tests/test_db_manager.py -q`
  - sampled `projects/0_0323/project_data.db` inspection for `stage_attempts`, `director_selections`, `attempt_raw_rationale`
- Residual risk:
  - the next real Stage 4 `REJECT` row should still be spot-checked during normal monitoring, but no active remediation queue remains for this wave

## 12. 3-Pass Audit Record
- Pass 1: re-audited live project DB rows and current Stage 4 reject/save seams instead of relying on stale queue wording
- Pass 2: confirmed reject-path classification persistence with targeted Stage 4 and DB tests and merged that evidence with live linkage evidence
- Pass 3: rechecked canonical closure state, roadmap exhaustion, temp cleanup, and queue semantics against the current workspace state

## 13. Confidence
- Estimated confidence: 96%
- Residual uncertainty:
  - sampled project DB `REJECT` rows still reflect older `NULL failure_category` baseline state rather than a post-closure rerun sample
