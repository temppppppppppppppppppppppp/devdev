# Stage2 / Stage3 Proof-Wave Opus Survey Orders for `000_260408_B`

Date: 2026-04-08
Status: active helper (post-fresh-run evidence harvest)
Target Project: `projects/000_260408_B/`
Target Session ID: `20260408_161433`
Purpose: parallel evidence harvest after the Stage2 proof-sink repair tranche, with special focus on what is now fixed, what still explains `proof_digest.status = "warn"`, and whether Stage3 absence is runtime truth or operator-choice truth.

## Shared Rules

- evidence harvest only
- do not patch code
- do not rerun the pipeline
- do not mutate DB contents
- use the fresh run under `projects/000_260408_B/` only
- do not reuse `projects/000_260408/` as truth for this wave
- if console text and persisted sinks disagree, persisted sinks win

Shared anchors to inspect first:

- `projects/000_260408_B/project_data.db`
- `projects/000_260408_B/logs/runtime_audit_summary.json`
- `projects/000_260408_B/logs/runtime_audit.jsonl`
- `projects/000_260408_B/logs/pass_rate_monitor.json`
- `projects/000_260408_B/logs/session/decisions.jsonl`
- `projects/000_260408_B/logs/session/ui_events.jsonl`
- `projects/000_260408_B/logs/artifacts/stage2/`
- `projects/000_260408_B/logs/artifacts/stage3/`
- `0_temp.txt` only as operator-intent context, not as authoritative sink truth

Known orientation hints to verify, not to trust blindly:

- this run returned to the main menu after Stage2 and the operator selected `5. Exit`
- `proof_digest.available = true`
- `proof_digest.status = "warn"`
- `proof_digest.stages` currently includes `stage2`
- `operational_metadata.stage2_live_session.status = "ok"`
- `operational_metadata.stage3_live_session.status = "absent"`
- `stage_attempts(stage=2) = 3`
- `director_selections(stage=2) = 3`
- DB `ui_events(event_kind='carryover_authority') = 3`
- `pass_rate_monitor.total_records = 3`
- `logs/session/decisions.jsonl` contains `9` rows, including `3 x arc_final`

Report format for every terminal:

1. what was checked
2. concrete evidence
3. mismatches or blanks
4. gap classification:
   - no gap
   - logging gap
   - sink drift
   - upstream semantic/runtime issue
   - operator-choice / not exercised
5. concise verdict

Every terminal must save exactly one markdown report at its assigned path below.

Canonical merge target after all 5 return:

- `docs/2026-04-08/stage23-proof-wave-000_260408_B-parallel-merge-audit.md`

## Terminal 1. Stage2 Carryover Authority Parity

Save report to:

- `docs/2026-04-08/stage23-proof-wave-000_260408_B-terminal1-stage2-carryover-authority-report.md`

Question:

- does Stage2 carryover authority now survive cleanly across DB `stage_attempts`, DB `ui_events`, session `ui_events.jsonl`, and Stage2 artifacts?

Check:

- `stage_attempts.advisory_flags.carryover_authority`
- `director_selections.advisory_warnings.carryover_authority`
- DB `ui_events` rows where `event_kind='carryover_authority'`
- `logs/session/ui_events.jsonl` rows where `event_kind='carryover_authority'`
- Stage2 artifact payloads for arc start/end state

Deliverable:

- latest carryover authority snapshot for arc 3
- per-arc parity table for start/end location, inventory counts, capital, total assets, portfolio position
- exact remaining drift, if any, including preview truncation or numeric contradictions

## Terminal 2. Stage2 Session Decision Coverage

Save report to:

- `docs/2026-04-08/stage23-proof-wave-000_260408_B-terminal2-stage2-session-decision-coverage-report.md`

Question:

- does Stage2 final decision evidence now survive into `decisions.jsonl` with enough metadata to reconstruct proof without DB-only spelunking?

Check:

- all Stage2 rows in `logs/session/decisions.jsonl`
- especially `decision_type='arc_final'`
- coverage for:
  - `session_id`
  - `attempt_key`
  - `candidate_key`
  - `artifact_path`
  - `selection_reason`
  - `verdict_reason`
  - `fix_scope`
  - `fix_scope_reasoning`
  - `carryover_authority`
- compare against latest `stage_attempts` and `director_selections`

Deliverable:

- row-kind inventory: `arc`, `arc_final`, `arc_design`
- coverage table by field
- exact remaining blanks and whether they are sink drift or genuine upstream blanks
- explain whether `proof_digest.status = "warn"` is partly driven by rationale metadata still missing

## Terminal 3. Stage2 Pass-Rate Durability

Save report to:

- `docs/2026-04-08/stage23-proof-wave-000_260408_B-terminal3-stage2-pass-rate-durability-report.md`

Question:

- is Stage2 attempt parity now durable across DB `stage_attempts`, `director_selections`, `pass_rate_monitor.json`, and artifact disk truth?

Check:

- `stage_attempts`
- `director_selections`
- `logs/pass_rate_monitor.json`
- Stage2 artifact files under `logs/artifacts/stage2/`

Deliverable:

- count parity table
- attempt-key parity table
- candidate/artifact linkage parity table
- confirm whether the old `DB 3 vs pass_rate 0` gap is now closed

## Terminal 4. Proof Digest / Runtime Summary Readiness

Save report to:

- `docs/2026-04-08/stage23-proof-wave-000_260408_B-terminal4-proof-digest-runtime-summary-report.md`

Question:

- is `runtime_audit_summary.json` now sufficient for Stage2 summary-only triage, and what exact issue still keeps `proof_digest.status = "warn"`?

Check:

- `proof_digest.available`
- `proof_digest.status`
- `proof_digest.stages.stage2`
- `proof_digest.operational_metadata.stage2_live_session`
- `proof_digest.operational_metadata.stage3_live_session`
- `session_lineage`
- `artifacts.pass_rate_monitor_exists`
- `ui_event_coverage_status`

Deliverable:

- compact summary of what is now fixed versus `projects/000_260408`
- exact root cause of current `warn`
- whether Stage2 summary-only triage is now usable for operators

## Terminal 5. Stage3 Absence Classification and Stage2-to-Stage3 Readiness

Save report to:

- `docs/2026-04-08/stage23-proof-wave-000_260408_B-terminal5-stage3-absence-and-handoff-readiness-report.md`

Question:

- why is Stage3 absent in this run, and does the latest Stage2 terminal state look coherent enough to hand off into Stage3 when the next run actually enters it?

Check:

- `0_temp.txt` near the end of the run for operator-intent context
- `runtime_audit_summary.json`
- `runtime_audit.jsonl`
- `stage_attempts(stage=3)`
- `director_selections(stage=3)`
- `blueprints`
- `llm_calls` by stage if helpful
- latest Stage2 artifact end-state plus carryover packet

Deliverable:

- classify Stage3 absence as:
  - operator exit after Stage2
  - runtime failure before Stage3
  - logging-only ambiguity
- if Stage3 was not exercised, state that clearly
- give an evidence-based read on whether latest Stage2 end-state appears semantically coherent enough for Stage3 handoff
- do not recommend code changes; this is evidence-only

## Pasteable One-Liner

Use this with the doc above:

`Target project is projects/000_260408_B from the fresh run that ended on session 20260408_161433. Do evidence harvest only. No code edits, no rerun, and save your report to the exact path assigned in docs/2026-04-08/stage23-proof-wave-000_260408_B-opus-survey-orders.md.`
