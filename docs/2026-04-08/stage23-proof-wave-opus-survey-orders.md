# Stage2 / Stage3 Proof-Wave Opus Survey Orders

Date: 2026-04-08
Status: active helper
Purpose: post-fresh-run parallel survey orders for the newly hardened Stage2 / Stage3 proof surfaces

## Shared Scope

- target project: the fresh-run project under review
- do not patch code
- do not rerun the pipeline
- treat this as evidence harvest only
- distinguish actual runtime gaps from missing-log gaps

Shared anchors to inspect first:

- `project_data.db`
- `logs/runtime_audit_summary.json`
- `logs/runtime_audit.jsonl`
- `logs/pass_rate_monitor.json`
- `logs/session/decisions.jsonl`
- `logs/session/ui_events.jsonl`
- `logs/artifacts/stage2/`
- `logs/artifacts/stage3/`

Report format for every terminal:

1. what was checked
2. concrete evidence found
3. missing or mismatched surfaces
4. whether the gap is:
   - logging gap
   - sink drift
   - actual upstream semantic/runtime issue

## Terminal 1. Stage2 Carryover Authority

Question:

- does Stage2 now expose authoritative carryover location / inventory / finance truth clearly enough for proof use?

Check:

- `stage_attempts.advisory_flags.carryover_authority`
- `director_selections.advisory_warnings.carryover_authority`
- `ui_events` / `ui_events.jsonl` with `event_kind=carryover_authority`
- Stage2 artifact payload start/end state

Deliverable:

- latest Stage2 carryover authority snapshot
- whether start/end location and inventory counts align across DB, UI event, and artifact

## Terminal 2. Stage2 Session Decision Coverage

Question:

- does Stage2 final decision evidence now survive into session sinks with enough metadata to reconstruct proof without DB-only spelunking?

Check:

- `logs/session/decisions.jsonl` Stage2 rows
- `attempt_key`, `candidate_key`, `artifact_path`
- `selection_reason`, `verdict_reason`, `fix_scope`, `fix_scope_reasoning`
- compare with `stage_attempts` latest Stage2 rows

Deliverable:

- coverage table for Stage2 decision metadata
- exact fields still blank, if any

## Terminal 3. Stage3 Source Anchor Coverage

Question:

- does Stage3 now expose actual source-anchor basis for flashback / opening / inherited inventory investigation?

Check:

- `stage_attempts.advisory_flags.source_anchor_summary`
- Stage3 `ui_events` / `ui_events.jsonl` summary lines
- Stage3 latest `selection_reason` / `verdict_reason`
- Stage3 blueprint artifact anchor surfaces

Deliverable:

- latest `source_anchor_summary`
- whether previous-blueprint end state and current Stage2 start state are both visible

## Terminal 4. Stage2 / Stage3 PassRate Durability

Question:

- do Stage2 and Stage3 attempt records now reliably reach `pass_rate_monitor.json` during the fresh run?

Check:

- `logs/pass_rate_monitor.json`
- Stage2 attempt count vs pass-rate Stage2 records
- Stage3 attempt count vs pass-rate Stage3 records
- latest `attempt_key` / `artifact_path` parity

Deliverable:

- count parity verdict for Stage2
- count parity verdict for Stage3
- any stage where record flush still appears lossy

## Terminal 5. Proof Digest / Runtime Summary Readiness

Question:

- does `runtime_audit_summary.json` now summarize Stage2 / Stage3 latest-session proof surfaces well enough for fast operator triage?

Check:

- `proof_digest.operational_metadata.stage2_live_session`
- `proof_digest.operational_metadata.stage3_live_session`
- coverage fields
- latest anchor snapshots
- `status` and any residual gaps

Deliverable:

- whether summary-only triage is now possible for Stage2
- whether summary-only triage is now possible for Stage3
- what still requires raw DB / JSONL join

## Merge Rule

- if two terminals disagree, prefer:
  - artifact / DB readback
  - then session sink rows
  - then runtime summary
  - then console transcript
- do not escalate a semantic/runtime owner change unless the evidence survives this order:
  - artifact truth
  - DB truth
  - session sink truth
  - summary truth
