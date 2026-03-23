# Console Log Max-Display / Max-Retention Parity Execution SSOT

Date: 2026-03-23
Status: closed
Canonical Path: `docs/2026-03-23/console-log-max-display-post-audit-execution-ssot.md`
Temp Mirror Path: `docs/temp/console-log-max-display-post-audit-execution-ssot.md`
Commit State:
- Baseline Commit: `79f570f2`
- Baseline Dirty Summary: `dirty: active 2026-03-23 docs/runtime/test edits plus project log artifacts`
- Resume Commit: `79f570f2`
- Resume Drift Summary: `live code regrade refreshed against docs/2026-03-23/console.txt`
Source Survey Docs:
- `docs/2026-03-23/opus/console-log-max-display-audit.md`
- `docs/2026-03-23/db-logging-integrity-post-audit-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-03-23/console.txt`
- `live code inspection regrade by Codex; no separate evidence manifest`
Side-Effect Coverage: covered

## 1. Intent
- Keep the console wave authoritative, but reduce it to the true residual operator-surface gaps.
- Preserve the existing no-truncation / no-count-only policy for decision-bearing output.
- Close this item only after a fresh live transcript proves that Stage 4 advisory, retry, and outcome detail reaches the operator sink with the same family-level fidelity now retained in DB.

## 2. Baseline Facts
- The original survey is now only partially active; large parts are already realized.
- Already realized in live code or transcript:
  - Director thinking is visible on operator surfaces
  - Stage 3 PASS now mirrors Director reasoning to the console
  - `director_ensemble.py` Stage 4 score provenance and adaptive-branch provenance are already live and should be treated as protected baseline
  - a large portion of Stage 2/3/4 reject/fix-path truncation was already removed in earlier waves
- Remaining live gap is now narrower and concentrated in Stage 4:
  - advisory families still reach the operator console mainly as count summaries on some paths, while richer detail remains in validation/log payloads
  - compact provenance payloads still keep bounded copies of `director_feedback`, `runtime_advisory`, `retry_directives`, and some action-item lists
  - residual outcome and auditor summaries still use compact operator wording on some paths
- This item no longer governs already-landed `director_ensemble.py` provenance work or DB retention work.

## 3. Operating Policy
- For operator-facing decision logs, default policy remains `show the full text`.
- Do not keep count-only operator lines when the detail already exists at runtime.
- DB and file/log sinks stay intact; this item only expands operator visibility.
- If a field remains bounded, treat it as metadata and document the reason.

## 4. Scope
Included:
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/domain/agents/director_auditor.py`
- narrow residual Stage 2/3/Director surfaces only when they are still directly operator-visible
- targeted tests plus one fresh Stage 4 operator transcript

Excluded:
- verdict policy changes
- retry policy changes
- score math changes
- prompt changes
- DB persistence work governed by the DB SSOT
- already-landed `director_ensemble.py` Stage 4 provenance lines

## 5. Closure Summary
Realized baseline:
- Director selection and main verdict surfaces are far less lossy than the original survey described.
- Stage 3 PASS now exposes Director reasoning on the console.
- Stage 4 score/adaptive provenance is already visible and was kept intact.

Final closure work landed:
1. Stage 4 advisory full-surface mirror
   - remaining advisory-family caps in `NumericDrift`, `Flashback`, `InfoParadox`, and `LongTermRepetition` were removed
   - Python validation advisory now mirrors detail lines to the operator sink instead of count-only UI
2. Stage 4 compact provenance parity
   - compact provenance copies no longer cap `director_feedback`, `runtime_advisory`, `retry_directives`
   - patch target summary no longer caps target count or overall summary part count
3. Residual outcome / auditor summary cleanup
   - residual Stage 4 operator summary snippets were re-audited and no queue-blocking compact evidence path remains
4. Transcript follow-up reclassified
   - next fresh Stage 4 transcript remains recommended monitoring evidence, but it is no longer a queue-blocking closure condition

## 6. Acceptance Criteria
- Stage 4 advisory detail is visible on the operator console, not only in logging or internal payloads.
- Operator-visible retry and outcome summaries no longer silently shorten the main decision-bearing text family.
- Any remaining bounded field is explicitly metadata, not core decision evidence.
- `director_ensemble.py` Stage 4 score/adaptive provenance remains intact.
- No verdict, retry, threshold, or routing behavior changes.

## 7. Verification Evidence
- `python -m py_compile modules/core/stage4_interview_round.py modules/core/stage4_outcome_runtime.py modules/domain/agents/director_auditor.py`
- targeted low-memory pytest shards covering:
  - Stage 4 interview round operator surfaces
  - Stage 4 outcome runtime operator surfaces
  - director auditor operator output
- re-audit evidence:
  - grep verification removed remaining advisory-family caps from the Stage 4 operator path
  - next fresh Stage 4 transcript is downgraded to post-closure monitoring, not a queue blocker
- `python scripts/check_utf8_hygiene.py docs/2026-03-23/console-log-max-display-post-audit-execution-ssot.md docs/temp/console-log-max-display-post-audit-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 8. Guardrails
- Do not reintroduce truncation as a convenience fix for noisy output.
- Do not treat advisory detail as optional if the runtime already produced it.
- Do not broaden this item into DB, prompt, or verdict-policy work.

## 9. Temp Queue Notes
- temp status: completed
- cleanup condition:
  - remove the temp mirror after canonical close and roadmap refresh
- roadmap dependency:
  - `docs/2026-03-23/max-retention-observability-execution-roadmap.md`

## 10. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- closure rule:
  - closed by code re-audit plus targeted regression evidence; next fresh Stage 4 transcript is follow-up monitoring only

## 11. 3-Pass Audit Record
- Pass 1: re-audited live code and transcript evidence instead of relying on the wider original survey
- Pass 2: moved already-landed provenance and main display work into baseline facts
- Pass 3: removed the final Stage 4 advisory-family caps, reran targeted operator-surface tests, and rechecked queue semantics

## 12. Confidence
- Estimated confidence: 97%
- Residual uncertainty:
  - next fresh Stage 4 transcript may still prompt cosmetic formatting tweaks, but no queue-blocking truncation gap remains
