# Stage4 Proof-Digest CoVe Advisory Execution SSOT

Date: 2026-04-27
Track: system
Status: completed (PR #83 merged; GitHub #59 closed)
Canonical Path: `docs/2026-04-27/stage4-proof-digest-cove-advisory-execution-ssot.md`
Temp Mirror Path: removed from active queue on 2026-04-27 after closure
Commit State:
- Baseline Commit: `26b05fcd34c0d841a140613ed414bac840c9a596`
- Baseline Dirty Summary: only documentation intake work was untracked while synthesizing #59; no tracked source edits were made for this document.
- Resume Commit: `4a14b4f1f49813101520f7640aec84f7ca253198`
- Resume Drift Summary: all ten #59 terminal reports are present under `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-parallel-investigation/`; the earlier T10 readiness memo is superseded by `terminal-10-final-synthesis-readiness.md`; #58 has been retired from the active temp queue, so #59 is now roadmap rank 1/front-active.
GitHub Issue:
- #59 `[Stage4] Close proof-digest warn residues and CoVe advisory review`
Source Survey Docs:
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-10terminal-order.md`
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-terminal-returns-intake.md`
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-parallel-investigation/terminal-01-proof-digest-warn-taxonomy.md`
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-parallel-investigation/terminal-02-settled-db-final-authority.md`
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-parallel-investigation/terminal-03-rationale-metadata-sink-alignment.md`
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-parallel-investigation/terminal-04-cove-runtime-advisory-pass-preserved.md`
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-parallel-investigation/terminal-05-cove-fail-closed-retry-policy.md`
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-parallel-investigation/terminal-06-operator-display-dashboard-semantics.md`
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-parallel-investigation/terminal-07-live-run-current-session-status.md`
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-parallel-investigation/terminal-08-benchmark-archive-impact.md`
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-parallel-investigation/terminal-09-regression-test-gap-design.md`
- `docs/2026-04-27/issue-59-stage4-proof-digest-cove-advisory-parallel-investigation/terminal-10-final-synthesis-readiness.md`
Evidence Artifacts:
- Current Stage4 session evidence from T01/T02/T03/T07: session `20260427_070604`, proof digest `warn`, 15 attempts considered, final/lifecycle completeness 15/15.
- CoVe runtime advisory evidence from T02/T04/T05: 5 PASS-preserved runtime advisory events in runtime/episode audit surfaces.
- Dashboard, benchmark, and regression gap evidence from T06/T08/T09.
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: stage4-proof-digest-cove-advisory
  github_issue: 59
  status: completed
  queue_role: historical_backing
  roadmap_rank: 1
  depends_on: []
  tranches:
    - id: bridge-dashboard-warn-field-parity
      title: Bridge/dashboard warn field parity and freshness labels
    - id: cove-contract-test-hardening
      title: CoVe advisory versus semantic fail-closed regression hardening
    - id: proof-digest-taxonomy-phase-semantics
      title: Proof-digest taxonomy and phase-aware rationale semantics
    - id: benchmark-stage4-diagnostic-packet
      title: Stage4 benchmark diagnostic packet
  verification_commands:
    - python -m pytest tests/test_bridge_quality_summary.py -k "stage4 or proof or dashboard or warn" -q
    - python -m pytest tests/test_stage4_orchestrator.py -k "cove or CoVe" -q
    - python -m pytest tests/test_archive_benchmark_record.py tests/test_compare_benchmark_records.py tests/test_backfill_benchmark_native_post_run_evidence.py -q
    - python -m py_compile modules/api/bridge_server.py modules/core/services/audit_service.py modules/core/failure_analyzer.py modules/core/stage4_outcome_runtime.py
    - python scripts/check_utf8_hygiene.py <touched docs/code/tests>
    - git diff --check
    - python scripts/ops_validator.py --strict
```

## 1. Intent

Close the Issue #59 ambiguity where Stage4 proof-digest `warn`, CoVe runtime advisory, CoVe semantic fail-closed retry, Director PASS authority, and settled attempt verdict can be read as one undifferentiated failure signal.

The intended outcome is not to suppress warning evidence. The intended outcome is to make every warning explain its authority role: proof evidence, runtime advisory, semantic retry, stale summary, benchmark diagnostic, or settled attempt verdict.

## Closure Note - 2026-04-27

- PR #83 merged to `main` as `dd00a4847483eb37d9029b70e08d0c04e42db88d`.
- GitHub issue #59 is closed as completed.
- GitHub CI passed: `desktop-contract`, `lint`, `syntax-check`, and `test (3.12)`.
- The realized proof-status rendering and warning taxonomy work is now historical backing for future Frontier Lag and benchmark proof interpretation.
- This SSOT is retained as canonical historical backing; the temp mirror is removed from the active queue.

## 2. Baseline Facts

- T01/T10 confirm the latest inspected Stage4 session `20260427_070604` reports proof digest `warn`, 15 attempts considered, and 15/15 final/lifecycle completeness.
- The top current warning headline is `P1 sink_coverage_gap x15`, driven by `pass_rate_monitor` coverage gaps.
- T03 reports the current #59 warning counts: `selection_reason_mismatches=4`, `verdict_reason_mismatches=4`, `runtime_advisory_mismatches=10`, `retry_directives_mismatches=4`, `rationale_metadata_missing=6`, and `gate_repair_metadata_missing=4`.
- T02 confirms Director rows can remain `PASS_WITH_FIX` while matching `stage_attempts` rows settle as `REJECT` after post-select conflict. That is settled runtime authority, not a CoVe runtime failure.
- T04/T05 confirm CoVe runtime exceptions are advisory-only and preserve Director PASS, while semantic CoVe critical fail-closed remains the legitimate retry/downgrade path.
- T07 confirms current Stage4 evidence is stopped/provisional, not completed proof. It also flags `projects/01_골든카나리아/logs/runtime_audit_summary.json` as stale or stage3-scoped for Stage4 proof claims.
- T06 confirms the dashboard proof status contract is directionally correct, but `modules/api/bridge_server.py` omits several #59 compact issue fields that `modules/core/services/audit_service.py` already preserves.
- T08 confirms benchmark and archive scripts surface compact proof digest fragments, but they do not yet preserve CoVe runtime advisory count, semantic fail-closed count, proof-warn taxonomy, runtime-summary freshness, or settled-versus-Director divergence as separate comparison dimensions.
- T09 confirms existing tests cover many core Stage4 CoVe and FailureAnalyzer paths, but dashboard, benchmark, stale-summary, and Stage4 compact-warn paths are undercovered. One Stage4 orchestrator CoVe runtime test also contains unreachable assertions after a `return`.

## 3. Scope

Included:
- Stage4 proof-digest warning taxonomy and phase-aware rationale semantics.
- Director verdict, settled attempt verdict, CoVe runtime advisory, and CoVe semantic fail-closed role separation.
- Bridge/dashboard compact warning fields and stale runtime-summary labels.
- Benchmark evidence fields required to compare early-April or earlier records against current runs without mixing advisory residue into reject-rate movement.
- Regression tests for the operator-facing and benchmark-facing contracts.

Excluded:
- Suppressing proof-digest `warn` without explaining the source.
- Weakening Director authority or post-select fail-closed rules.
- Treating Python diagnostics as final narrative judgment.
- Claiming clean terminal 5-arc proof readiness from this work alone.
- Bulk tracking large local benchmark snapshots or project artifacts for reproducibility.

## 4. Pass 1. Inventory Summary

| Surface | Evidence | Execution Risk |
| --- | --- | --- |
| Proof digest producer | T01/T03/T10 | Generic `warn` can hide whether the issue is coverage, phase drift, advisory residue, metadata absence, or raw-contract failure. |
| DB authority rows | T02/T07 | Director PASS/PASS_WITH_FIX, settled `stage_attempts`, and runtime advisory rows can be misread if displayed without role labels. |
| CoVe runtime advisory | T04/T05 | PASS-preserved runtime exceptions must stay visible but must not be counted as semantic rejects. |
| CoVe semantic fail-closed | T05/T09 | Critical semantic CoVe results must still retry/fail closed and remain separate from runtime advisory. |
| Bridge/dashboard | T06/T09 | Compact bridge summaries omit #59 issue fields and can under-explain `proof_evidence_warning`. |
| Runtime summary freshness | T07/T09 | A stale `stage3_complete` summary can masquerade as current Stage4 proof if freshness is not explicit. |
| Benchmark/archive | T08/T09 | Early-April versus current comparisons can mix reject-rate movement with advisory/stale-summary noise. |

## 5. Pass 2. Semantic Classification

Class A - proof-evidence warning taxonomy:
- `coverage_warn`: pass-rate-monitor and sink coverage gaps.
- `rationale_drift_warn`: original Director rationale versus later settled/post-fix rationale drift.
- `runtime_advisory_warn`: PASS-preserved runtime advisory rows.
- `metadata_gap_warn`: missing retry directive, gate repair, or rationale metadata.
- `raw_contract_warn`: malformed or missing raw evidence contract data.

Class B - authority role separation:
- `director_verdict`: Director narrative authority at selection/verdict time.
- `settled_attempt_verdict`: runtime-settled attempt outcome after post-select, retry, or finalization logic.
- `cove_runtime_advisory`: observability/advisory evidence that preserves Director PASS.
- `cove_fail_closed`: semantic CoVe critical path that can trigger retry/downgrade.
- `proof_digest_status`: evidence-alignment status, not narrative verdict.

Class C - display and freshness:
- Dashboard status should continue to avoid canonical truth claims, but compact fields must include #59 counts.
- Runtime summary must carry a Stage4 freshness/scope status when later Stage4 attempts exist after a summary tagged `stage3_complete`.

Class D - benchmark interpretation:
- Benchmark packets need fields that preserve reject count, post-select conflict count, CoVe runtime advisory count, CoVe semantic fail-closed count, proof-warn taxonomy, and archive reproducibility separately.

## 6. Side-Effect Map

- file writes / artifacts: benchmark snapshots, runtime summary JSON, Stage4 proof digest reports, dashboard snapshots, docs, and regression fixtures.
- DB / schema / transaction boundaries: `stage_attempts`, `director_selections`, session decision metadata, and any analyzer read queries. No schema migration is authorized by this SSOT unless a later tranche proves it is required.
- JSONL / log / audit sinks: `episode_production.jsonl`, `runtime_audit.jsonl`, `runtime_audit_summary.json`, CoVe advisory audit events, pass-rate-monitor sink coverage, and compact proof digest payloads.
- console / UI / operator output: bridge API quality summary, dashboard proof status, benchmark operator lines, and CoVe advisory messages must distinguish authority roles.
- rollback / recovery / retry: CoVe runtime advisory must not become retry authority; semantic fail-closed retry remains fail-closed.
- cache / global state: not a primary #59 target; only inspect if stale summaries or benchmark backfills cache compact proof evidence.
- bootstrap fallback / config-env mutation: not applicable.

## 7. Realization Architecture

Use small, proof-preserving tranches:

1. First make the operator surface honest: bridge/dashboard compact payloads should carry the same #59 warning counts already present in the audit-service compact proof digest, plus an explicit freshness/scope label when runtime summaries are stale for Stage4.
2. Lock CoVe advisory versus semantic fail-closed with tests before changing any producer semantics.
3. Normalize proof-digest taxonomy and phase semantics only after dashboard and CoVe contracts make the visible behavior safe to compare.
4. Extend benchmark evidence packets last, once the field names and meaning are stable.

Synthesis decision:
- The smallest safe first implementation is `bridge-dashboard-warn-field-parity` plus the unreachable CoVe test cleanup from `cove-contract-test-hardening`.
- `proof-digest-taxonomy-phase-semantics` is broader and should not be first unless current code inspection proves it is already mostly a field-forwarding change.

## 8. Execution Tranches

1. Bridge/dashboard warn field parity and freshness labels
   - Add #59 issue fields to bridge compact sink/proof summaries where audit-service already preserves them.
   - Add or expose runtime-summary freshness/scope labels so a stale `stage3_complete` summary cannot be read as current Stage4 proof.
   - Add dashboard/bridge tests for `proof_evidence_warning` plus #59 issue counts.
2. CoVe contract test hardening
   - Fix unreachable assertions in the existing Stage4 CoVe runtime test.
   - Lock the four-way split: quick exception, LLM exception/parse failure, noncritical advisory issue, and critical semantic fail-closed retry.
   - Assert runtime advisory never increments semantic reject/fail-closed counters.
3. Proof-digest taxonomy and phase semantics
   - Expose typed warn taxonomy buckets.
   - Separate original Director-selection rationale from settled/post-fix rationale instead of treating expected phase drift as generic corruption.
   - Decide and document whether `pass_rate_monitor` is required for current-session Stage4 proof or is optional/legacy evidence.
4. Benchmark Stage4 diagnostic packet
   - Add compact fields for CoVe runtime advisory count, PASS-preserved count, CoVe semantic fail-closed count, proof-warn taxonomy counts, runtime-summary freshness, and settled-versus-Director divergence count.
   - Update archive, backfill, compare, and operator-line scripts so Issue #62 can compare early-April/current runtime or reject rates without mixing advisory failures into semantic rejects.

## 9. Acceptance Criteria

- Bridge/dashboard summaries show `proof_evidence_warning` with #59 rationale/runtime counts instead of a bare ambiguous `warn`.
- Runtime summaries carry enough freshness/scope metadata that stage3-scoped summaries cannot satisfy current Stage4 proof claims.
- CoVe runtime exceptions preserve Director PASS and remain advisory-only across logs, audit rows, UI, and tests.
- CoVe semantic critical results remain fail-closed retry evidence and are counted separately from runtime advisory.
- Proof-digest warnings are itemized by taxonomy and phase role.
- Benchmark comparison can distinguish reject count, post-select conflict count, CoVe runtime advisory count, CoVe semantic fail-closed count, proof-warn taxonomy, and stale/provisional run status.
- No code path introduced by this work lets Python diagnostics silently override Director narrative authority.

## 10. Verification Plan

- `python -m pytest tests/test_bridge_quality_summary.py -k "stage4 or proof or dashboard or warn" -q`
- `python -m pytest tests/test_stage4_orchestrator.py -k "cove or CoVe" -q`
- `python -m pytest tests/test_archive_benchmark_record.py tests/test_compare_benchmark_records.py tests/test_backfill_benchmark_native_post_run_evidence.py -q`
- Targeted tests to add or confirm:
  - `test_bridge_dashboard_stage4_warn_surfaces_rationale_runtime_counts`
  - `test_audit_service_stage4_proof_digest_warn_preserves_issue59_counts`
  - `test_dashboard_marks_runtime_summary_stale_for_later_stage4_attempts`
  - `test_benchmark_packet_separates_cove_runtime_advisory_from_fail_closed_reject`
  - `test_stage4_cove_runtime_exception_second_round_assertions_reachable`
  - `test_stage4_phase_drift_classification_for_director_vs_settled_reason`
- `python -m py_compile modules/api/bridge_server.py modules/core/services/audit_service.py modules/core/failure_analyzer.py modules/core/stage4_outcome_runtime.py`
- `python scripts/check_utf8_hygiene.py <touched docs/code/tests>`
- `git diff --check`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not make `warn` disappear by dropping evidence.
- Do not collapse Director verdict, settled attempt verdict, runtime advisory, and semantic retry into one status field.
- Do not mark a stopped/provisional Stage4 session as clean terminal proof.
- Do not treat stale `runtime_audit_summary.json` as current Stage4 proof when later Stage4 attempts exist.
- Do not count CoVe runtime advisory as semantic reject/fail-closed in benchmarks.
- Do not bulk-track ignored benchmark snapshots or project artifacts just to improve reproducibility.

## 12. Temp Queue Notes

- temp status: in_progress
- queue role: front active
- cleanup condition: remove `docs/temp/stage4-proof-digest-cove-advisory-execution-ssot.md` after all #59 tranches are realized, verified, canonical closure is recorded, and any GitHub issue update is made.
- roadmap dependency: no formal dependency edge is declared. Operationally, #59 should be considered before any fresh clean terminal 5-arc proof claim or Issue #62 benchmark comparison claim.

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- queue state: `python scripts/sync_temp_queue_state.py`
- execution-start rule: re-run this document's 3-pass audit and confirm at least 95% confidence against live workspace before code edits.

## 14. 3-Pass Document Audit

Pass 1 - structure and scope:
- PASS. This is an execution SSOT for #59 only.
- PASS. It includes intent, baseline facts, inventory, semantic classification, side effects, tranches, acceptance criteria, verification, guardrails, temp queue notes, and closure hooks.

Pass 2 - evidence and consistency:
- PASS. All ten #59 terminal reports exist and are represented.
- PASS. The older T10 readiness memo is treated as superseded by `terminal-10-final-synthesis-readiness.md`.
- PASS. The synthesis preserves the key adversarial separations: Director versus settled authority, CoVe runtime advisory versus semantic fail-closed, proof-digest warn versus narrative verdict, and stale summary versus current Stage4 proof.

Pass 3 - execution readiness:
- PASS. First implementation is intentionally scoped to bridge/dashboard field parity and CoVe test hardening before producer taxonomy or benchmark changes.
- PASS. Verification commands and cleanup rules are explicit.

Estimated operational confidence: 96%.

## 15. Realization Ledger - 2026-04-27 Bridge Warn Counts And CoVe Test Hardening

Scope realized:
- Tranche: `bridge-dashboard-warn-field-parity`, partially.
- Tranche: `cove-contract-test-hardening`, partially.
- Branch: `codex/issue59-proof-cove-dashboard`.

Code changes:
- `modules/api/bridge_server.py` now forwards the #59 warning count fields already preserved by audit-service compaction: `selection_reason_mismatches`, `verdict_reason_mismatches`, `runtime_advisory_mismatches`, `retry_directives_mismatches`, `rationale_metadata_missing`, and `gate_repair_metadata_missing`.
- `modules/api/bridge_server.py` now exposes `proof_status.warning_issue_counts` split by `sink_alignment` and `runtime_summary` so `proof_evidence_warning` carries rationale/runtime counts instead of a bare `warn`.
- `tests/test_bridge_quality_summary.py` adds regressions for bridge compact parity and dashboard runtime-summary `proof_evidence_warning` count forwarding.
- `tests/test_stage4_orchestrator.py` removes unreachable assertions after a `return` in the CoVe runtime failure test.
- `tests/test_stage4_orchestrator.py` strengthens CoVe runtime advisory assertions so PASS is preserved, only one round runs, advisory payload is written, and `STAGE4_RETRY_PATHOLOGY` is not emitted.
- `tests/test_stage4_orchestrator.py` strengthens semantic CoVe fail-closed assertions so retry guidance carries `cove_fail_closed=True` and `cove_runtime_failure=False`, while no runtime advisory row is emitted.

Validation completed:
- `python -m pytest tests/test_bridge_quality_summary.py -q` -> 21 passed.
- `python -m pytest tests/test_bridge_quality_summary.py -k "stage4 or proof or dashboard or warn" -q` -> 15 passed, 6 deselected.
- `python -m pytest tests/test_stage4_orchestrator.py -k "cove and not NpcOverexposureHook" -q` -> 31 passed, 134 deselected.
- `python -m py_compile modules/api/bridge_server.py tests/test_bridge_quality_summary.py tests/test_stage4_orchestrator.py` -> PASS.

Validation caveat:
- `python -m pytest tests/test_stage4_orchestrator.py -k "cove or CoVe" -q` is not a reliable #59 selector because pytest substring matching also selects `TestNpcOverexposureHook`. In the current workspace that selector reports two unrelated overexposure-hook failures caused by the manuscript length floor. The clean CoVe selector above passes.

Residual open work:
- This does not close #59.
- Runtime-summary Stage4 staleness detection is addressed by Section 16; producer taxonomy is addressed by Section 17; benchmark packet work is addressed by Section 18.
- Deeper phase-aware rationale semantics remain open.
- Desktop/frontend rendering of `proof_status.warning_issue_counts` remains open if a separate UI surface needs it.

Explorer follow-up notes:
- Benchmark packet should be a compact `stage4_diagnostic_packet`, not generic stage metrics. It should count CoVe runtime advisory rows, PASS-preserved advisory rows, semantic CoVe fail-closed retry rows, proof-warn taxonomy counts, runtime summary freshness, and settled-versus-Director divergence separately.
- Proof taxonomy can start as additive derived counts, but phase-aware rationale drift should eventually be producer-owned in `FailureAnalyzer` before being forwarded by audit-service and bridge.

3-pass realization audit:
- Pass 1 - scope: PASS. The patch is limited to bridge/dashboard field forwarding and CoVe regression hardening.
- Pass 2 - evidence: PASS. The patch directly implements the T06/T09 first-tranche gap and preserves T04/T05 CoVe role separation.
- Pass 3 - readiness: PASS for a partial #59 PR. Residual stale-summary, taxonomy, benchmark, and frontend-display work remains explicit.

Estimated operational confidence for this partial realization: 96%.

## 16. Realization Ledger - 2026-04-27 Runtime Summary Stage4 Freshness Guard

Scope realized:
- Tranche: `bridge-dashboard-warn-field-parity`, freshness-label residual.
- Branch: `codex/issue59-runtime-summary-freshness`.
- Implemented the T07/T09 stale-summary guard after #58 queue retirement promoted #59 to the front-active item.

Code changes:
- `modules/api/bridge_server.py` now inspects the latest DB-backed Stage4 attempt context while building the quality dashboard payload.
- Runtime audit summaries with tag/run-scope `stage3_complete`, or with a summary timestamp older than the latest Stage4 attempt timestamp, are marked `freshness.status="stale_for_stage4"` and `freshness.scope_status="pre_stage4_or_partial"`.
- The freshness payload keeps operator-facing basis fields, stale reasons, latest Stage4 attempt timestamp, session-id presence, attempt key, verdict, and Stage4 attempt count.
- `proof_status.runtime_summary_freshness_status` now forwards the freshness status. A stale-for-Stage4 summary escalates companion `proof_status.status` to `warn` while preserving the original `runtime_summary_status`.
- `tests/test_bridge_quality_summary.py` adds a regression for a `stage3_complete` runtime summary followed by a later Stage4 attempt row.

Validation completed:
- `python -m py_compile modules/api/bridge_server.py` -> PASS.
- `python -m py_compile modules/api/bridge_server.py tests/test_bridge_quality_summary.py` -> PASS.
- `python -m pytest tests/test_bridge_quality_summary.py -k "stale_for_later_stage4_attempts or stage4_warn_issue59_counts or proof_status" -q` -> 3 passed, 19 deselected.
- `python -m pytest tests/test_bridge_quality_summary.py -q` -> 22 passed.

Complexity note:
- `_build_quality_dashboard_payload` is a bounded dashboard aggregation shell and was already a long orchestrating function; this patch adds one narrow freshness-classification call without moving authority or persistence ownership.
- New helper functions are local to the bridge/dashboard companion surface and do not write DB, logs, or artifacts.

Residual open work:
- This does not close #59.
- Producer-owned typed warning taxonomy counts are addressed by Section 17; deeper phase-aware rationale semantics remain open.
- Benchmark `stage4_diagnostic_packet` remains open.
- Desktop/frontend rendering of `proof_status`, `warning_issue_counts`, and freshness fields remains open if a separate visible UI panel is required.

3-pass realization audit:
- Pass 1 - scope: PASS. The patch is limited to dashboard/runtime-summary freshness labeling and does not modify runtime settlement or Director authority.
- Pass 2 - evidence: PASS. The regression proves a stale `stage3_complete` summary can no longer masquerade as current Stage4 proof when a later Stage4 attempt exists.
- Pass 3 - readiness: PASS for a partial #59 PR. Residual taxonomy, benchmark, and optional frontend rendering remain explicit.

Estimated operational confidence for this partial realization: 96%.

## 17. Realization Ledger - 2026-04-27 Producer-Owned Proof Warning Taxonomy Counts

Scope realized:
- Tranche: `proof-digest-taxonomy-phase-semantics`, additive taxonomy-count slice.
- Branch: local continuation after PR #80 merge.
- Implemented the smallest safe producer-owned split so bridge/dashboard and benchmark follow-ups can consume typed warn buckets without inventing taxonomy at the display layer.

Code changes:
- `modules/core/failure_analyzer.py` now emits `warning_taxonomy_counts` from the sink-alignment producer:
  - `coverage_warn`
  - `rationale_drift_warn`
  - `runtime_advisory_warn`
  - `metadata_gap_warn`
  - `raw_contract_warn`
- `modules/core/services/audit_service.py` preserves producer-owned `warning_taxonomy_counts` in compact proof digest stage summaries.
- `modules/api/bridge_server.py` forwards `warning_taxonomy_counts` into `proof_status.warning_taxonomy_counts`, split by `sink_alignment` and `runtime_summary`.
- Tests cover producer emission, audit compact preservation, bridge compact preservation, and dashboard runtime-summary forwarding.

Validation completed:
- `python -m py_compile modules/core/failure_analyzer.py modules/core/services/audit_service.py modules/api/bridge_server.py` -> PASS.
- `python -m pytest tests/test_failure_analyzer.py -k "runtime_rationale_mismatch" -q` -> 2 passed, 50 deselected.
- `python -m pytest tests/test_audit_service.py -k "rationale_mismatch_issue_counts or compact_sink_alignment_summary_counts_gate_repair_contract_issues" -q` -> 2 passed, 21 deselected.
- `python -m pytest tests/test_bridge_quality_summary.py -k "stage4_warn_issue59_counts or compact_sink_alignment_summary_preserves_issue59_warn_counts" -q` -> 2 passed, 20 deselected.
- `python -m pytest tests/test_bridge_quality_summary.py -q` -> 22 passed.
- `python -m pytest tests/test_audit_service.py -q` -> 23 passed.
- `python -m pytest tests/test_failure_analyzer.py -q` -> 52 passed.

Complexity note:
- The patch adds bounded taxonomy helper logic and does not move final authority, settlement, DB schema, or runtime retry behavior.
- `_build_sink_alignment_summary_payload` remains the producer aggregation shell; this patch adds one derived count payload beside existing `coverage_gap_count`, `structured_issue_count`, and `raw_issue_count`.

Residual open work:
- This does not close #59.
- Deeper phase-aware rationale semantics remain open, especially distinguishing expected Director-selection versus settled/post-fix rationale drift from actual corruption.
- Benchmark `stage4_diagnostic_packet` remains open.
- Desktop/frontend rendering of proof/freshness/taxonomy fields remains open if a separate visible UI panel is required.

3-pass realization audit:
- Pass 1 - scope: PASS. The patch adds taxonomy counts only; it does not suppress warn evidence or alter verdict authority.
- Pass 2 - evidence: PASS. Producer, audit compact, and bridge/dashboard tests prove counts originate from `FailureAnalyzer` and are forwarded without display-layer reclassification.
- Pass 3 - readiness: PASS for a partial #59 PR. Benchmark packet is addressed by Section 18; optional frontend rendering remains explicit.

Estimated operational confidence for this partial realization: 96%.

## 18. Realization Ledger - 2026-04-27 Benchmark Stage4 Diagnostic Packet

Scope realized:
- Tranche: `benchmark-stage4-diagnostic-packet`.
- Branch: `codex/issue59-stage4-benchmark-diagnostic-packet`.
- Implemented the compact benchmark packet requested by T08/T10 so April-baseline versus current runs can compare Stage4 runtime advisory, semantic retry, proof taxonomy, stale-summary, post-select, and settled-versus-Director divergence signals without collapsing them into a generic reject rate.

Code changes:
- `scripts/archive_benchmark_record.py` now writes `manifest.stage4_diagnostic_packet` with Stage4 attempt/pass/reject counts, runtime-summary freshness, proof digest status, Stage4 proof issue/taxonomy counts, CoVe runtime advisory counts, PASS-preserved CoVe advisory counts, semantic CoVe fail-closed retry counts, post-select conflict counts, and settled-versus-Director divergence counts.
- `scripts/compare_benchmark_records.py` now loads the packet from manifest, runtime summary, or linked native post-run evidence and emits dedicated watchpoints for packet status, stale runtime summaries, and nonzero diagnostic counts.
- `scripts/backfill_benchmark_native_post_run_evidence.py` now preserves the packet as top-level native post-run evidence.
- `scripts/report_benchmark_operator_lines.py` now includes compact operator fragments such as `diag=warn`, `stale_summary`, `cove_advisory=N`, `semantic_retry=N`, and `proof_warn=N`.
- Tests cover archive creation, compare watchpoints, native evidence fallback, backfill preservation, and operator-line rendering.

Validation completed:
- `python -m py_compile scripts/archive_benchmark_record.py scripts/compare_benchmark_records.py scripts/backfill_benchmark_native_post_run_evidence.py scripts/report_benchmark_operator_lines.py` -> PASS.
- `python -m pytest tests/test_archive_benchmark_record.py -q` -> 6 passed.
- `python -m pytest tests/test_compare_benchmark_records.py -k "stage4_runtime_watchpoints or companion_post_run_evidence_watchpoints" -q` -> 2 passed, 14 deselected.
- `python -m pytest tests/test_backfill_benchmark_native_post_run_evidence.py -q` -> 2 passed.
- `python -m pytest tests/test_report_benchmark_operator_lines.py -k "native_proof_signals or proof_signal_summary" -q` -> 2 passed, 8 deselected.
- `python -m pytest tests/test_compare_benchmark_records.py -q` -> 16 passed.
- `python -m pytest tests/test_report_benchmark_operator_lines.py -q` -> 10 passed.
- `python -m pytest tests/test_backfill_benchmark_native_post_run_evidence.py tests/test_archive_benchmark_record.py tests/test_compare_benchmark_records.py tests/test_report_benchmark_operator_lines.py -q` -> 34 passed.

Complexity note:
- The archive helper is a bounded benchmark aggregation shell: it reads existing JSON/JSONL proof surfaces and writes a companion snapshot only.
- The compare/report helpers add additive read-only watchpoints and do not change benchmark verdict ranking, runtime settlement, retry behavior, DB schema, or Director authority.

Residual open work:
- This does not close #59 by itself.
- Desktop/frontend rendering of proof/freshness/taxonomy/diagnostic fields remains open if a separate visible UI panel is required.

3-pass realization audit:
- Pass 1 - scope: PASS. The packet is additive benchmark metadata and does not reinterpret runtime verdicts.
- Pass 2 - evidence: PASS. The packet keeps CoVe runtime advisory, PASS-preserved advisory, semantic fail-closed retry, proof taxonomy, post-select conflict, and settled-versus-Director divergence as separate fields.
- Pass 3 - readiness: PASS for a partial #59 PR. Targeted benchmark/archive/compare/operator tests passed, and #59 residual work remains explicit.

Estimated operational confidence for this partial realization: 96%.

## 19. Realization Ledger - 2026-04-27 Phase-Aware Stage4 Rationale Drift Classification

Scope realized:
- Tranche: `proof-digest-taxonomy-phase-semantics`, phase-aware rationale semantics slice.
- Branch: local continuation after Sections 16-18.
- Implemented the remaining core #59 distinction between expected Director-selection companion drift and real cross-sink rationale corruption.

Code changes:
- `modules/core/failure_analyzer.py` now emits `phase_drift_rationale_warnings` when Stage4 `director_selections` is explicitly marked `selection_companion_status: pre_final_candidate` and the final sinks agree on the settled selection/verdict rationale.
- Generic `selection_reason_mismatches` and `verdict_reason_mismatches` remain for true contradictions where final sinks disagree or the Director row is not a pre-final companion.
- `warning_taxonomy_counts.rationale_drift_warn` includes `phase_drift_rationale_warnings`, so proof warnings remain visible instead of disappearing.
- `modules/core/services/audit_service.py` preserves `phase_drift_rationale_warnings` in compact sink-alignment `issue_counts`.
- Tests cover the pre-final Director companion classification, the existing runtime mismatch guard, full failure analyzer coverage, and audit-service compact forwarding.

Validation completed:
- `python -m pytest tests/test_failure_analyzer.py -k "prefinal_director_rationale_drift or runtime_rationale_mismatch" -q` -> PASS, 3 tests.
- `python -m pytest tests/test_failure_analyzer.py -q` -> PASS, 53 tests.
- `python -m pytest tests/test_audit_service.py -q` -> PASS, 24 tests.
- `python -m pytest tests/test_bridge_quality_summary.py -k "compact_sink_alignment_summary_preserves_issue59_warn_counts or stage4_warn_issue59_counts or stale_for_later_stage4_attempts" -q` -> PASS, 3 tests.
- `python -m pytest tests/test_stage4_orchestrator.py -k "cove and not NpcOverexposureHook" -q` -> PASS, 31 tests.
- `python -m pytest tests/test_archive_benchmark_record.py tests/test_compare_benchmark_records.py tests/test_backfill_benchmark_native_post_run_evidence.py tests/test_report_benchmark_operator_lines.py -q` -> PASS, 34 tests.
- `python -m py_compile modules/core/failure_analyzer.py modules/core/services/audit_service.py` -> PASS.
- `python scripts/check_utf8_hygiene.py modules/core/failure_analyzer.py modules/core/services/audit_service.py tests/test_failure_analyzer.py tests/test_audit_service.py` -> PASS.
- `git diff --check -- modules/core/failure_analyzer.py modules/core/services/audit_service.py tests/test_failure_analyzer.py tests/test_audit_service.py` -> PASS.
- `python scripts/ops_validator.py --strict` -> PASS after canonical/temp mirror sync and queue-state regeneration.

Complexity note:
- `_collect_sink_alignment_rationale_results`: 159 LOC. Classification: bounded sink-comparison aggregation shell; this patch classifies one Stage4 authority-role exception and does not change DB writes, runtime settlement, retry behavior, or Director authority.
- `_is_stage4_prefinal_rationale_phase_drift` is a small predicate helper.
- `_build_sink_alignment_summary_payload`: 308 LOC pre-existing bounded proof-summary aggregation shell; this patch only forwards the new issue family through existing counters.
- `_compact_sink_alignment_summary`: 67 LOC.

Residual open work:
- This does not close #59 by itself.
- Canonical closure and GitHub #59 status/closure handling remain pending.

3-pass realization audit:
- Pass 1 - scope: PASS. The patch is limited to producer/audit classification of Stage4 rationale drift.
- Pass 2 - evidence: PASS. Expected pre-final Director companion rationale drift is itemized separately, while real mismatch guards still pass.
- Pass 3 - readiness: PASS for a partial #59 continuation. Core backend #59 semantics are now covered; optional desktop visibility and closure handling remain explicit.

Estimated operational confidence for this partial realization: 96%.

## 20. Realization Ledger - 2026-04-27 Desktop Quality Proof Rendering

Scope realized:
- Tranche: `desktop-proof-status-visible-surface`.
- Branch: local continuation after Sections 16-19.
- Implemented the remaining operator-facing desktop visibility slice so the dashboard does not rely on bridge/API payload inspection alone.

Code changes:
- `geuldobi-desktop/src/index.html` now seeds the dashboard fallback with top-level `proof_status` fields including status, freshness, semantic completion, canonical truth posture, warning issue counts, warning taxonomy counts, authority note, and summary.
- `geuldobi-desktop/src/quality_page_bootstrap.js` now nested-merges `proof_status` in `mergeDashboardData`, preventing partial payloads from dropping fallback proof fields.
- `renderResultSummarySection` now prepends proof-status alert chips to the existing recent-result signal-alert row: proof status, freshness, semantic completion, truth posture, issue total, and taxonomy total.
- `renderFailureWatchSection` now prepends compact proof diagnostic pattern rows that preserve producer-owned issue/taxonomy count labels instead of reducing proof warnings to a bare `warn`.
- `geuldobi-desktop/src/quality_react_helpers.js` preserves optional pattern `meta` text so proof count labels render in React islands and fallback DOM paths.
- `tests/test_desktop_direct_surface_contract.py` adds static contract checks for proof-status bootstrap helpers, fallback data, result-summary wiring, Failure Watch wiring, and warning count fields.

Validation completed:
- `node --check geuldobi-desktop/src/quality_page_bootstrap.js; node --check geuldobi-desktop/src/quality_react_helpers.js` -> PASS.
- `python -m pytest -q tests/test_desktop_direct_surface_contract.py tests/test_frontend_frontier_lag_wiring.py tests/test_ui_renderer_sanitization.py` -> PASS, 13 tests.
- `node tests/test_desktop_preload_bridge_behavior.js; node tests/test_desktop_material_offline_behavior.js; node tests/test_splash_runtime_behavior.js` -> PASS.
- `python -m pytest -q tests/test_bridge_quality_summary.py -k "stage4_warn_issue59_counts or stale_for_later_stage4_attempts or proof_status"` -> PASS, 3 tests, 19 deselected.
- `python -m pytest -q tests/test_failure_analyzer.py tests/test_audit_service.py` -> PASS, 77 tests.
- `python scripts/check_utf8_hygiene.py geuldobi-desktop/src/quality_page_bootstrap.js geuldobi-desktop/src/quality_react_helpers.js geuldobi-desktop/src/index.html tests/test_desktop_direct_surface_contract.py` -> PASS.
- `git diff --check -- geuldobi-desktop/src/quality_page_bootstrap.js geuldobi-desktop/src/quality_react_helpers.js geuldobi-desktop/src/index.html tests/test_desktop_direct_surface_contract.py` -> PASS.

Complexity note:
- The touched JavaScript helpers are bounded display-formatting helpers and do not change runtime settlement, DB writes, bridge authority, retry policy, or Director authority.
- The new proof chips consume producer/bridge-owned fields only; the desktop layer does not invent new warning taxonomy.

Residual open work:
- This does not close #59 by itself.
- Canonical closure and GitHub #59 status/closure handling remain pending.

3-pass realization audit:
- Pass 1 - scope: PASS. The patch is limited to desktop/dashboard visibility for existing proof-status companion fields.
- Pass 2 - evidence: PASS. Static desktop contracts, Node syntax checks, bridge proof-status tests, and backend producer/audit regressions all pass.
- Pass 3 - readiness: PASS for a #59 desktop rendering continuation. The previously open desktop/frontend visibility residual is addressed; closure handling remains explicit.

Estimated operational confidence for this partial realization: 96%.
