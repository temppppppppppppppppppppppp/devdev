# Issue #59 Terminal 07 - Live Run Current Session Status

Status: final after 3-pass adversarial audit  
Scope: current live run status, stopped/provisional handling, and stale summary risk

## Finding Summary

The current Stage4 evidence must be treated as stopped/provisional, not completed proof.

Current direct evidence:

- project: `projects/01_골든카나리아`
- latest Stage4 session: `20260427_070604`
- direct Stage4 analyzer status: `warn`
- current-session attempts considered: 15
- current-session final/lifecycle completeness: 15/15 and 15/15
- latest Stage4 stopped point: `ep9` has two `REJECT` rows and no persisted PASS in the sampled current rows

Important stale-surface finding:

- `projects/01_골든카나리아/logs/runtime_audit_summary.json` is tagged `stage3_complete` at `2026-04-27 08:37:01`.
- That summary reports `proof_digest.status=ok` and has no compact Stage4 stage entry.
- Direct current-session analyzer evidence after Stage4 activity reports `warn`.

So the runtime summary should not be used alone as current Stage4 proof.

## Evidence

- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md` records current Stage4 status after stop: `ep9` had two `POST_SELECT_CONFLICT` rejects and no PASS persisted.
- Same handoff records the improvement pattern: Stage4 conflicts are being caught and recovering in 2 to 4 attempts so far.
- Same handoff records CoVe LLM runtime failures after some PASSes, with Stage4 preserving Director PASS.
- `docs/2026-04-27/auto-frontier-lag-5arc-runtime-analysis-ssot.md` records both `stage3_current_session_status: warn` and `stage4_current_session_status: warn`.
- Direct analyzer current-session Stage4 summary reports top issue `P1 sink_coverage_gap x15`.

## Risk / Gap

If a consumer reads only `runtime_audit_summary.json`, it may conclude proof digest is OK because the latest written summary is stage3-scoped. That conflicts with later Stage4 DB/log evidence.

This is a freshness and scope problem, not necessarily a Stage4 quality failure.

## Suggested Contract Or Test

Add a current-session proof freshness rule:

- If latest DB Stage4 attempt timestamp/session is later than `runtime_audit_summary.timestamp`, dashboard and benchmark readers must mark runtime summary as `stale_for_stage4`.
- If `runtime_audit_summary.tag` is not Stage4-related and direct Stage4 attempts exist after that summary, display `runtime_summary_scope=pre_stage4_or_partial`.
- Current-session analyzer evidence should win over stale compact summary for diagnostic status.

Test expectation: a stage3-scoped runtime summary plus later Stage4 attempts produces dashboard/benchmark warning `runtime_summary_stale_for_stage4`.

## Implementation Owner Surface

- `modules/api/bridge_server.py`
- `scripts/compare_benchmark_records.py`
- `scripts/backfill_benchmark_native_post_run_evidence.py`
- `scripts/run_auto_frontier_lag_harness.py`

## Open Questions

- Should Stage4 stop/handoff write a final compact runtime summary even when the run is interrupted?
- Should `runtime_audit_summary` include last DB attempt timestamp per stage?

## 3-Pass Save Audit

- Pass 1: Current DB/analyzer evidence was checked against runtime summary and handoff docs.
- Pass 2: Staleness was separated from proof failure.
- Pass 3: Stopped/provisional status was preserved in the language.

