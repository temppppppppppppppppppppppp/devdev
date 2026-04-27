# Issue #59 Terminal 10 - Final Synthesis And Execution Readiness

Status: final after 3-pass adversarial audit  
Supersedes: `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-terminal-10-synthesis-readiness-memo.md`  
Scope: synthesis of T01-T09, implementation tranche proposal, and readiness gates

## Executive Synthesis

Issue #59 is ready for execution planning.

The main conclusion is stable: Stage4 proof-digest `warn`, CoVe runtime advisory, CoVe semantic fail-closed retry, Director PASS authority, and settled attempt verdict are separate contracts. The current system already preserves most of that distinction internally, but some operator, dashboard, and benchmark surfaces collapse or omit the distinctions.

The most urgent implementation direction is not "make warn disappear." It is "make warn explain itself without becoming a false completion or false failure claim."

## Confirmed Findings

1. Current Stage4 analyzer status for session `20260427_070604` is `warn`, with 15 attempts considered and 15/15 final/lifecycle completeness.
2. The current top issue is `P1 sink_coverage_gap x15`, caused by `pass_rate_monitor` absence for current Stage4 attempts.
3. #59 rationale/runtime warning fields are real:
   - `selection_reason_mismatches=4`
   - `verdict_reason_mismatches=4`
   - `runtime_advisory_mismatches=10`
   - `retry_directives_mismatches=4`
   - `rationale_metadata_missing=6`
   - `gate_repair_metadata_missing=4`
4. Some selection/verdict mismatches are probably phase drift between original Director rationale and later settled/post-fix rationale.
5. CoVe runtime exception advisory preserves Director PASS and is already logged in `episode_production`, `runtime_audit`, and UI events.
6. CoVe semantic critical fail-closed retry is separately implemented with `cove_fail_closed=True`.
7. Dashboard proof status correctly avoids canonical truth claims, but bridge compact summaries omit several #59 issue fields.
8. The current `runtime_audit_summary.json` is stage3-scoped and stale/insufficient for current Stage4 proof despite direct Stage4 analyzer evidence.
9. Benchmark scripts surface `digest=warn` and Stage4 status fragments, but do not yet preserve the #59 taxonomy or CoVe advisory/fail-closed split.
10. Regression coverage exists for core CoVe and FailureAnalyzer paths, but dashboard, benchmark, stale-summary, and Stage4 compact warn paths need tests.

## Recommended Execution Tranches

### Tranche A - Proof Digest Taxonomy And Phase Semantics

Owner surfaces:

- `modules/core/failure_analyzer.py`
- `modules/core/stage4_canary_tools.py`
- relevant Stage4 persistence call sites

Work:

- Introduce or expose warn taxonomy buckets.
- Separate original Director rationale from settled/post-fix rationale.
- Decide whether `pass_rate_monitor` is required, optional, or legacy for Stage4 current-session proof.

Acceptance:

- Stage4 current-session warn returns itemized reason counts.
- Legitimate Director-to-settled phase drift is not mislabeled as generic corruption.

### Tranche B - Operator Dashboard And Freshness

Owner surfaces:

- `modules/api/bridge_server.py`
- `tests/test_bridge_quality_summary.py`

Work:

- Add #59 issue fields to bridge compact sink summary.
- Add runtime summary freshness/staleness signal for later Stage4 DB evidence.
- Add dashboard warn snapshot tests.

Acceptance:

- Dashboard shows `proof_evidence_warning` plus #59 issue counts.
- Stage3-scoped runtime summary cannot masquerade as current Stage4 proof.

### Tranche C - CoVe Contract Hardening

Owner surfaces:

- `modules/core/stage4_outcome_runtime.py`
- `tests/test_stage4_orchestrator.py`

Work:

- Lock four CoVe cases: quick exception, LLM exception, noncritical issue, critical fail-closed retry.
- Fix unreachable assertions in the existing CoVe runtime test.

Acceptance:

- Runtime advisory never increments semantic reject/fail-closed counters.
- Semantic critical CoVe result still requests retry.

### Tranche D - Benchmark Evidence Packet

Owner surfaces:

- `scripts/archive_benchmark_record.py`
- `scripts/backfill_benchmark_native_post_run_evidence.py`
- `scripts/compare_benchmark_records.py`
- `scripts/report_benchmark_operator_lines.py`

Work:

- Extend benchmark native evidence with Stage4 diagnostic packet.
- Preserve CoVe runtime advisory count separately from semantic fail-closed retry count.
- Include proof-digest warn taxonomy counts and archive reproducibility status.

Acceptance:

- Issue #62 can compare early-April/current attempt and reject rates without mixing advisory failures into semantic rejects.
- Issue #65 reproducibility guardrails remain intact.

## Non-Goals

- Do not remove Director authority.
- Do not make Python decide narrative quality.
- Do not bulk-track large project snapshots just to make benchmarks reproducible.
- Do not force all proof-digest warns to fail the run.

## Readiness Gate

Execution is ready after this synthesis if the implementer accepts these gates:

- Use current workspace state before editing.
- Re-run a focused 3-pass audit on this synthesis before code changes.
- Add focused tests before or alongside behavior changes.
- Treat current run evidence as stopped/provisional.

## 3-Pass Save Audit

- Pass 1: T01-T09 evidence was cross-checked against source, tests, live DB/logs, docs, benchmark scripts, and GitHub Issues #62/#65.
- Pass 2: Adversarial conflicts were checked: stale runtime summary, Director-versus-settled authority, runtime advisory versus semantic fail-closed, and warn versus fail.
- Pass 3: Execution readiness was scoped to contracts/tests/operator surfaces without changing runtime or canonical narrative authority.

