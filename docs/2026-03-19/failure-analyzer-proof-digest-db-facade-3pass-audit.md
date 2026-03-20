# failure-analyzer-proof-digest-db-facade-3pass-audit

Date: 2026-03-19
Status: final
Confidence: `0.97`
Canonical Path: `docs/2026-03-19/failure-analyzer-proof-digest-db-facade-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `dirty: large active worktree; git status --short count = 114`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
- `docs/2026-03-18/OPUS/0_260318-project-analysis-report.md`
- `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Evidence Basis:
- `modules/core/services/audit_service.py`
- `modules/core/failure_analyzer.py`
- `modules/core/db_manager.py`
- `tests/test_audit_service.py`
- `tests/test_bridge_quality_summary.py`
Scope:
- fix the proof-digest DB wrapper mismatch between `AuditService` and `FailureAnalyzer`
- preserve read-only proof-digest behavior
- keep `DBManager` boot out of the proof-digest path
- non-goal: broader failure-analyzer redesign or project-wide log survey

---

## Pass 1. Structure and Scope

This item is intentionally narrow.

The live mismatch was:
- `AuditService._resolve_proof_digest_db()` returned a read-only wrapper with only `conn` and `db_path`
- `FailureAnalyzer.sink_alignment_summary(stage=4)` expected `get_stage4_final_authority_rows()`
- the real method existed only on `DBManager`

Operational effect:
- the proof-digest path could emit a soft failure for `sink_alignment_final_authority_contract`
- that failure could surface in runtime health and quality dashboard summaries

---

## Pass 2. Evidence and Consistency

### 1. The mismatch was real

Observed live call chain:
- `AuditService._build_proof_digest()` constructed the DB wrapper
- `FailureAnalyzer(...).sink_alignment_summary(stage=4)` called `self.db.get_stage4_final_authority_rows(...)`

The wrapper did not implement that method.
The real method lived in `DBManager`.

Conclusion:
- the project DB/log report was directionally correct on this point
- but the fix still had to be revalidated against live code before patching

### 2. The safe fix is a read-only facade, not DBManager re-entry

The chosen fix keeps proof-digest read-only and avoids `DBManager` boot:
- add a minimal `_ProofDigestDBFacade`
- expose:
  - `conn`
  - `cursor`
  - `_lock`
  - `_director_stage_predicate`
  - `get_stage4_final_authority_rows`

This preserves:
- read-only SQLite access
- `FailureAnalyzer` compatibility
- the test contract that proof-digest must not re-enter full `DBManager` initialization

Conclusion:
- this is lower-risk than broadening `FailureAnalyzer` fallback behavior

### 3. Regression now locks the real contract

Direct regression evidence:
- `tests/test_audit_service.py::test_write_summary_includes_structured_proof_digest`
  - keeps the `DBManager` constructor explosion guard
  - now also asserts the runtime audit log does not contain `sink_alignment_final_authority_contract`
- `tests/test_bridge_quality_summary.py::test_quality_dashboard_endpoint_surfaces_proof_status_and_sink_alignment`
  - now rejects that failure component in runtime health output

Conclusion:
- the fix is not just interface-shape compatible
- the soft-failure symptom is also covered

---

## Pass 3. Operational Meaning and Next Step

### Final judgment

1. This was a real, high-ROI defect.

2. It was narrow enough to fix directly without extra policy work.

3. It should be treated as an exception item pulled from the project DB/log investigation, not as a reason to restore S8 as patch authority.

### Safe operating rule from this audit

Do:
- keep proof-digest on a read-only facade path
- keep `DBManager` boot out of proof-digest summary generation
- treat runtime-health soft failures from this component as regressions

Do not:
- reintroduce a bare `SimpleNamespace(conn=..., db_path=...)` wrapper
- silently swallow this mismatch again as “expected soft failure”
- use this fix as evidence that all S8 project-specific claims are now trusted

### Audit result

- runtime code change: completed
- regression hardening: completed
- documentation conclusion: proof-digest now exposes the minimum `FailureAnalyzer` DB contract without re-entering `DBManager` boot
