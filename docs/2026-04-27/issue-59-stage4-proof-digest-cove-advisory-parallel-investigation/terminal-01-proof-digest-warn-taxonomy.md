# Issue #59 Terminal 01 - Proof Digest Warn Taxonomy

Status: final after 3-pass adversarial audit  
Scope: Stage4 proof-digest `warn` taxonomy, source/runtime evidence, and contract split

## Finding Summary

Stage4 proof digest `warn` is currently an evidence-alignment status, not a canonical narrative quality verdict.

For project `projects/01_골든카나리아`, the direct current-session analyzer result for Stage4 session `20260427_070604` is:

- `status`: `warn`
- `attempts_considered`: 15
- `complete_final_attempts`: 15
- `complete_lifecycle_attempts`: 15
- `coverage_gap_count`: 15
- `structured_issue_count`: 52
- `raw_issue_count`: 0
- top headline: `P1 sink_coverage_gap x15`

The warning decomposes into five main buckets:

- `pass_rate_monitor` final-sink coverage gap for all 15 current-session Stage4 attempts.
- Selection/verdict reason drift between original Director selection rows and later post-fix/finalized sinks.
- Runtime advisory and retry directive drift between structured sinks.
- Missing retry-directive metadata in `stage_attempts` for attempts where companion sinks carry a retry context.
- Gate/repair metadata missing in `session_decisions` for selected fix-pack fields.

## Evidence

- `modules/core/failure_analyzer.py` builds Stage4 sink alignment from `stage_attempts`, `director_selections`, `episode_production`, `session_decisions`, `attempt_raw_rationale`, and `pass_rate_monitor`.
- `modules/core/failure_analyzer.py` emits `warn` when sink coverage, mismatch, raw rationale, or metadata issues remain.
- Current direct analyzer evidence for `20260427_070604`:
  - coverage: `stage_attempts=15`, `director_selections=15`, `episode_production=15`, `session_decisions=15`, `attempt_raw_rationale=15`, `pass_rate_monitor=0`
  - mismatch counts: `selection_reason_mismatches=4`, `verdict_reason_mismatches=4`, `runtime_advisory_mismatches=10`, `retry_directives_mismatches=4`
  - metadata counts: `rationale_metadata_missing=6`, `gate_repair_metadata_missing=4`
- Existing tests already prove the analyzer can:
  - treat aligned Stage4 rationale as clean
  - avoid treating a missing Stage4 companion runtime advisory as a metadata gap
  - flag Stage4 runtime/retry rationale mismatch as `warn`

## Risk / Gap

The taxonomy is present in `FailureAnalyzer`, but operator-facing summaries can collapse it into a single `warn`. Without a durable taxonomy surface, later benchmark or dashboard work may treat all `warn` cases as equivalent.

## Suggested Contract Or Test

Add a Stage4 proof-digest taxonomy contract:

- `coverage_warn`: sink row is missing, but other final/lifecycle sinks are complete.
- `rationale_drift_warn`: same attempt key carries different reason text across stage/final/post-fix sinks.
- `runtime_advisory_warn`: runtime advisory or retry directive differs across sinks.
- `metadata_gap_warn`: a sink is missing a required companion metadata field.
- `raw_contract_warn`: raw rationale projection disagrees with structured sinks.

Test expectation: a current-session Stage4 summary with `pass_rate_monitor=0` and otherwise complete final/lifecycle evidence remains `warn`, not `fail`, and returns itemized issue counts.

## Implementation Owner Surface

- `modules/core/failure_analyzer.py`
- `modules/core/stage4_canary_tools.py`
- `modules/core/services/audit_service.py`
- `modules/api/bridge_server.py`

## Open Questions

- Should `pass_rate_monitor` be required for Stage4 current-session proof, or demoted to a legacy/optional sink for Stage4?
- Should Director-selection rationale and settled/post-fix rationale be treated as separate phases instead of mismatches?

## 3-Pass Save Audit

- Pass 1: Evidence scope checked against source, tests, live DB summary, and runtime logs.
- Pass 2: Adversarial split checked: no Python judgment is treated as Director judgment.
- Pass 3: Save readiness checked: findings are diagnostic and do not prescribe code mutation.

