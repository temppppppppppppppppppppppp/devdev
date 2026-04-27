# Issue #59 Terminal 08 - Benchmark Archive Impact

Status: final after 3-pass adversarial audit  
Scope: benchmark comparisons, archive fields, and Issue #62/#65 dependency surface

## Finding Summary

Issue #59 affects benchmark work because reject/runtime comparisons need to distinguish:

- settled Stage4 reject count
- post-select conflict reject count
- CoVe semantic fail-closed retry count
- CoVe runtime advisory PASS-preserved count
- proof-digest evidence warn taxonomy
- stale/provisional runtime summary status

Current benchmark surfaces partially capture proof digest and Stage4 live-session status, but do not yet capture the #59 taxonomy or CoVe advisory split.

## Evidence

- GitHub Issue #62 asks for early-April vs current Stage4 reject and attempt-rate comparison.
- GitHub Issue #65 asks whether benchmark archives are reproducible enough when snapshots are local ignored evidence.
- `benchmarks/README.md` states snapshot folders are ignored by git by default and index rows may be `local_ignored_snapshot` or `local_only_non_reproducible`.
- `scripts/archive_benchmark_record.py` records stage metrics including `attempt_count`, `pass_like_count`, and `reject_count`.
- `scripts/compare_benchmark_records.py` loads compact runtime fields:
  - `proof_digest_status`
  - `operational_status`
  - `stage4_live_session_status`
  - `stage4_retry_exercised`
  - `stage4_patch_exercised`
  - `stage4_target_ep_reached`
  - `stage4_complete_emitted`
  - `stage4_post_pass_contract_signal_count`
- `scripts/report_benchmark_operator_lines.py` surfaces compact fragments such as `digest=warn`, `operational=...`, `live=...`, and `contracts=N`.

## Risk / Gap

Benchmark comparison can say "reject rate improved" while missing why rejects happened or whether proof warnings are stale/dashboard-only/advisory-only.

For Issue #59 specifically, missing benchmark dimensions are:

- `stage4_cove_runtime_advisory_count`
- `stage4_cove_pass_preserved_count`
- `stage4_cove_fail_closed_retry_count`
- `stage4_proof_warn_taxonomy_counts`
- `stage4_runtime_summary_freshness_for_stage4`
- `stage4_settled_vs_director_verdict_divergence_count`

Without these, Issue #62 can compare attempt counts but cannot explain whether current improvements are real bounded recovery or a different mix of advisory/staleness signals.

## Suggested Contract Or Test

Extend benchmark native post-run evidence with a compact Stage4 diagnostic packet:

- `attempt_count`, `pass_count`, `reject_count`
- `reject_by_failure_category`
- `attempts_before_pass_by_episode`
- `no_pass_after_rejects_by_episode`
- `cove_runtime_advisory_count`
- `cove_fail_closed_retry_count`
- `proof_digest_status`
- `proof_digest_issue_counts`
- `runtime_summary_scope_status`
- `archive_evidence_reproducibility_status`

Add tests that a benchmark comparison with `proof_digest_status=warn` and `cove_runtime_advisory_count>0` produces operator watchpoints without counting runtime advisory as semantic reject.

## Implementation Owner Surface

- `scripts/archive_benchmark_record.py`
- `scripts/backfill_benchmark_native_post_run_evidence.py`
- `scripts/compare_benchmark_records.py`
- `scripts/report_benchmark_operator_lines.py`
- `benchmarks/README.md`

## Open Questions

- Should future 5-arc proof runs export a small tracked evidence packet even when full DB/log snapshots remain ignored?
- Should stopped runs be benchmarked in a separate provisional lane from completed proof runs?

## 3-Pass Save Audit

- Pass 1: Local benchmark scripts and GitHub Issues #62/#65 were checked.
- Pass 2: Runtime advisory and semantic reject metrics were separated.
- Pass 3: Archive reproducibility language follows #65 guardrails and does not ask to bulk-track large snapshots.

