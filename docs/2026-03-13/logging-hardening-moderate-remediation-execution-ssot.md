# Logging Hardening Moderate Remediation Execution SSOT

Date: 2026-03-13
Status: draft for implementation
Confidence Target: 95%
Primary References:
- `docs/2026-03-12/TF-S4-logging-reinforcement-audit.md`
- `docs/2026-03-12/TF-LOG-full-pipeline-logging-audit.md`
- `docs/2026-03-13/stage4-director-cw-log-informed-remediation-postfix-5pass-closure.md`

## 1. Intent
- Concept: not too aggressive, but slightly aggressive.
- Default bias: reinforce logging where it materially improves postmortem reconstruction, without turning the codebase into a logging-only refactor.
- This order favors Stage 4 and Director observability first, then cheap cross-stage wins.

## 2. Scope
### Included
- `modules/domain/agents/director_ensemble.py`
  - Mirror Stage 2/3/4 Director print frames into structured `logging.*` calls.
  - Preserve print output; do not remove operator-facing console frames.
- `modules/core/stage4_interview_round.py`
  - Add attempt-key-aware major logs for the Stage 4 round lifecycle.
  - Carry `attempt_key` into session decision logging where possible.
  - Strengthen `episode_production.jsonl` with easier-to-join token/cost aliases.
- `modules/core/stage4_post_processor.py`
  - Add a compact episode-end summary log with cost/token totals when a pass result is persisted.
- Focused tests for the above.

### Conditionally Included
- `modules/core/stage4_orchestrator.py`
  - Only if needed for summary-log placement or attempt context propagation.

### Excluded
- Full print eradication across all stages.
- Global log-level reclassification for all modules.
- Stage 0/2/3 full structured JSONL rollout.
- Bulk prefix injection into every existing `logging.info/warning/error` call.
- Build, UI, canary rerun, or non-logging functional refactors.

## 3. Work Packages
### LHM-1. Director Frame Mirror
- Add a shared helper in `director_ensemble.py` that emits one concise summary line and selective detail lines for:
  - stage
  - ep_num
  - verdict/decision
  - score
  - selected candidate
  - selection reason
  - verdict reason
  - fix scope
  - contradiction count
  - optional open review
  - optional thinking snippet
- Use the helper in:
  - Stage 2 arc compare frame
  - Stage 3 blueprint compare frame
  - Stage 4 manuscript director frame

### LHM-2. Stage 4 Attempt-Key Major Logs
- Add a helper in `stage4_interview_round.py` for:
  - deterministic round `attempt_key`
  - attempt-prefixed major logs
- Use it for:
  - round start
  - director review start
  - advisory chain completion
  - final verdict summary
- Pass the same `attempt_key` into `session_logger.log_decision(...)` meta.

### LHM-3. Stage 4 Token/Cost Joinability
- Add top-level aliases to `episode_production.jsonl` entries:
  - `token_cost`
  - `token_usage`
- Alias values should come from the existing round metrics delta, not a second metrics source.
- Do not break existing `round_metrics` shape.

### LHM-4. Episode-End Summary
- Add one episode-end summary line in `stage4_post_processor.py` after cost snapshot persistence.
- Minimum fields:
  - `ep_num`
  - `arc_no`
  - `title`
  - manuscript length
  - total calls
  - total tokens
  - total cost
- This is a summary log, not a new sink.

### LHM-5. Focused Regression
- Add or update tests for:
  - Director logging helper output
  - Stage 4 `episode_production` token aliases
  - Stage 4 summary logging after episode cost persistence

## 4. Acceptance Criteria
- Director Stage 2/3/4 print frames are mirrored by `logging` with no operator print removal.
- Major Stage 4 round logs expose `attempt_key`.
- `session_logger` decision rows for Stage 4 include `attempt_key` in meta.
- `episode_production.jsonl` rows expose `token_cost` and `token_usage` without breaking existing readers.
- Successful Stage 4 episode persistence emits one compact summary log line.
- Focused regressions pass.

## 5. Non-Goals and Guardrails
- Do not rewrite historical logs or backfill old projects.
- Do not convert every debug line to structured logging.
- Do not add a new database schema unless unavoidable.
- Do not widen scope into Stage 0/2/3 sink redesign in this tranche.

## 6. Verification Plan
- `python -m py_compile` on modified modules/tests
- Focused pytest set around:
  - Director logging helper
  - Stage 4 interview round logging
  - Stage 4 post processor cost/summary
- Optional narrow follow-up:
  - canary/log analysis tests if touched indirectly

## 7. Expected Outcome
- Better postmortem readability from existing sinks.
- Lower gap between console-only operator output and file-based forensic logs.
- Better Stage 4 attempt-to-cost correlation without a large logging rewrite.
