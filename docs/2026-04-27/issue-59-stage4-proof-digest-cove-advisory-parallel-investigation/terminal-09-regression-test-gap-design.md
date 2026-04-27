# Issue #59 Terminal 09 - Regression Test Gap Design

Status: final after 3-pass adversarial audit  
Scope: existing coverage, missing regression tests, and proposed test matrix

## Finding Summary

Existing tests cover many Stage4 CoVe and FailureAnalyzer behaviors, but Issue #59 still needs regression coverage across integration surfaces:

- bridge/dashboard warn payload
- audit-service Stage4 proof-digest warn compaction
- stale runtime summary versus later Stage4 DB evidence
- benchmark packet taxonomy
- CoVe runtime advisory versus semantic fail-closed counting

## Existing Coverage

Covered:

- Stage4 runtime CoVe LLM parse/runtime exception preserves final manuscript and emits advisory.
- Stage4 quick verification exception preserves PASS and emits advisory.
- CoVe semantic regeneration requests produce retry disposition with `cove_fail_closed=True`.
- FailureAnalyzer Stage4 aligned rationale can be clean.
- FailureAnalyzer Stage4 runtime/retry mismatch can produce `warn`.
- FailureAnalyzer Stage4 companion missing runtime advisory does not become a metadata gap by itself.
- Dashboard OK proof status says dashboard proof is not canonical settlement authority.

## Gaps

Important missing tests:

- Bridge compact Stage4 warn includes `runtime_advisory_mismatches`, `retry_directives_mismatches`, `selection_reason_mismatches`, `verdict_reason_mismatches`, and `rationale_metadata_missing`.
- Audit-service Stage4 compact proof digest preserves the same #59 issue fields under a Stage4 warn case. Current runtime/retry compact test evidence is stronger for Stage2 than Stage4.
- Stale `runtime_audit_summary.json` tagged `stage3_complete` is not treated as current Stage4 proof when later Stage4 attempts exist.
- Benchmark comparison does not preserve CoVe runtime advisory count separately from semantic reject/fail-closed count.
- One Stage4 orchestrator CoVe runtime test has assertions after a `return`, leaving part of the intended test path unreachable.

## Suggested Test Matrix

Add focused tests:

- `test_bridge_dashboard_stage4_warn_surfaces_rationale_runtime_counts`
- `test_audit_service_stage4_proof_digest_warn_preserves_issue59_counts`
- `test_dashboard_marks_runtime_summary_stale_for_later_stage4_attempts`
- `test_benchmark_packet_separates_cove_runtime_advisory_from_fail_closed_reject`
- `test_stage4_cove_runtime_exception_second_round_assertions_reachable`
- `test_stage4_phase_drift_classification_for_director_vs_settled_reason`

## Implementation Owner Surface

- `tests/test_bridge_quality_summary.py`
- `tests/test_audit_service.py`
- `tests/test_stage4_orchestrator.py`
- benchmark script tests
- `tests/test_failure_analyzer.py`

## Open Questions

- Should phase-drift classification be introduced before writing dashboard tests, or should tests first lock the current generic mismatch behavior?
- Should benchmark tests use synthetic archive records or a minimal fixture copied from the current project?

## 3-Pass Save Audit

- Pass 1: Existing test names and coverage themes were checked.
- Pass 2: Test gaps were limited to #59 behavior and adjacent benchmark surfaces.
- Pass 3: Proposed tests avoid broad full-suite execution or memory-heavy validation.

