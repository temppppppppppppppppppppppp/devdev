# Issue #59 Terminal 06 - Operator Display And Dashboard Semantics

Status: final after 3-pass adversarial audit  
Scope: dashboard proof status, compact sink summaries, and operator-facing semantics

## Finding Summary

The dashboard has the right high-level semantic split, but the live compact sink summary omits several issue fields that are central to Issue #59.

Good existing semantics:

- `completion_claim_scope`: `proof_artifact_alignment_only`
- `semantic_completion_status`: `proof_evidence_aligned`, `proof_evidence_warning`, or `unavailable`
- `canonical_truth_status`: `not_asserted_by_dashboard`
- authority note: dashboard proof status is a companion summary, not canonical PASS settlement authority

Gap:

- `modules/api/bridge_server.py` compact sink issue fields do not include `selection_reason_mismatches`, `verdict_reason_mismatches`, `runtime_advisory_mismatches`, `retry_directives_mismatches`, or `rationale_metadata_missing`.
- `modules/core/services/audit_service.py` compact proof digest does include these fields.

## Evidence

- `bridge_server._build_dashboard_proof_status` maps warn to `proof_evidence_warning` and explicitly avoids canonical truth claims.
- `bridge_server._compact_sink_alignment_summary` counts structural/final/candidate/artifact/gate fields, but omits the #59 rationale/runtime fields.
- `audit_service._compact_sink_alignment_summary` includes the #59 fields in compact proof digest summaries.
- Existing dashboard tests assert the OK proof-status semantics, but no warn snapshot currently proves #59 fields survive the bridge compact path.

## Risk / Gap

An operator can see `warn` while the dashboard hides why. For Issue #59, the hidden details are the actual point:

- runtime advisory mismatch
- retry directive mismatch
- selection/verdict rationale drift
- rationale metadata gaps

This creates a "warn without diagnosis" surface.

## Suggested Contract Or Test

Update bridge compact issue fields to include the same #59 rationale/runtime fields used by `audit_service`.

Add a dashboard warn fixture where Stage4 has:

- `runtime_advisory_mismatches=1`
- `retry_directives_mismatches=1`
- `rationale_metadata_missing=1`

Expected dashboard payload:

- `proof_status.status == "warn"`
- `proof_status.semantic_completion_status == "proof_evidence_warning"`
- `proof_status.canonical_truth_status == "not_asserted_by_dashboard"`
- compact Stage4 issue counts include all three #59 issue fields

## Implementation Owner Surface

- `modules/api/bridge_server.py`
- `tests/test_bridge_quality_summary.py`
- `modules/core/services/audit_service.py`

## Open Questions

- Should bridge compact simply reuse the audit-service compact helper to prevent field drift?
- Should proof status show `freshness.status` when runtime summary is scoped but not up to the latest Stage4 events?

## 3-Pass Save Audit

- Pass 1: Bridge and audit-service compaction paths were compared.
- Pass 2: Dashboard authority language was checked for canonical-truth leakage.
- Pass 3: Proposed test is display-only and does not mutate runtime behavior.

