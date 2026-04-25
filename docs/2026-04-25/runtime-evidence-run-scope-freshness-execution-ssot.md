# Runtime Evidence Run-Scope Freshness Execution SSOT

Date: 2026-04-25
Status: closed
Canonical Path: `docs/2026-04-25/runtime-evidence-run-scope-freshness-execution-ssot.md`
Temp Mirror Path: `docs/temp/runtime-evidence-run-scope-freshness-execution-ssot.md`

Commit State:

- Baseline Commit: `ee978c7639e15e6f3c5dde22d82947cb7a718820`
- Baseline Dirty Summary: `clean`
- Resume Commit: `ee978c7639e15e6f3c5dde22d82947cb7a718820`
- Resume Drift Summary: `implementation changes in runtime summary, dashboard projection, benchmark archive, and focused tests`

Source Survey Docs:

- `docs/2026-04-25/codebase-parallel-memory-persistence-telemetry-deep-dive-wave3-synthesis.md`

Evidence Artifacts:

- live source inspection of `modules/core/services/audit_service.py`
- live source inspection of `modules/api/bridge_server.py`
- live source inspection of `scripts/archive_benchmark_record.py`
- live source inspection of `modules/core/stage4_canary_tools.py`
- live test inspection of `tests/test_audit_service.py`, `tests/test_archive_benchmark_record.py`, `tests/test_bridge_quality_summary.py`

Side-Effect Coverage: covered

## 1. Intent

Add bounded run/session freshness metadata to runtime evidence surfaces so operators can tell when a companion snapshot belongs to the current run/session versus an older project-level artifact.

This is maintenance hardening, not a new feature. Runtime audit summaries, dashboard payloads, benchmark archives, and canary proof surfaces remain companion evidence. They must not outrank DB attempt truth, JSONL/artifact truth, or Director authority.

## 2. Baseline Facts

- `AuditService.write_audit_summary()` writes `logs/runtime_audit_summary.json` with tag, timestamp, compact counts, summary window, and proof digest.
- `ProcessRunner` already passes `GEULDOBI_RUN_ID` to the engine process.
- `AuditService` does not currently expose `GEULDOBI_RUN_ID` in `runtime_audit_summary.json`.
- `bridge_server._load_runtime_audit_summary()` reports summary presence but does not classify freshness or expose top-level session/run lineage.
- `archive_benchmark_record()` stores only `runtime_audit_tag`, `latest_session_id`, and `summary_window` from the runtime summary.
- `stage4_canary_tools` reads the summary as a companion input and should receive the same lineage metadata without making it authoritative.

## 3. Scope

Included:

- `modules/core/services/audit_service.py`
- `modules/api/bridge_server.py`
- `scripts/archive_benchmark_record.py`
- focused regression tests for audit summary, dashboard projection, and benchmark archive manifest/index behavior

Excluded:

- no DB schema migration
- no canary gate hardening beyond receiving richer companion summary fields
- no live canary run
- no change to Director PASS/REJECT authority
- no change to benchmark record directory naming

## 4. Pass 1. Inventory Summary

Runtime summary producer:

- `AuditService.write_audit_summary()` is the single writer for `runtime_audit_summary.json`.
- `AuditService._build_proof_digest()` already computes `proof_digest.operational_metadata.latest_session_id`.

Consumers:

- `bridge_server._load_runtime_audit_summary()` loads the summary for quality dashboard payloads.
- `archive_benchmark_record()` copies the summary into benchmark records.
- `stage4_canary_tools` consumes the copied summary as a companion proof input.

Existing tests:

- `tests/test_audit_service.py` covers structured proof digest output.
- `tests/test_archive_benchmark_record.py` covers runtime summary fields in benchmark manifests and CSV index rows.
- `tests/test_bridge_quality_summary.py` covers dashboard payload semantics.

## 5. Pass 2. Semantic Classification

Class A: summary producer lineage

- Add explicit `run_scope` metadata to `runtime_audit_summary.json`.
- Use `GEULDOBI_RUN_ID` when present.
- Mirror latest structured session id from the proof digest after proof construction.

Class B: dashboard companion freshness

- Project `run_scope` and a small `freshness` block from summary to dashboard payload.
- Mark missing summary as `unavailable`.
- Mark summary with neither run id nor latest session id as `unknown`.
- Mark summary with either run id or latest session id as `scoped`.

Class C: benchmark archive carry-forward

- Preserve `run_scope` and `freshness` in `manifest["runtime_summary"]`.
- Add `runtime_freshness_status` to index rows for operator comparison.

## 6. Side-Effect Map

- file writes / artifacts: `logs/runtime_audit_summary.json`, benchmark `manifest.json`, benchmark index CSV.
- DB / schema / transaction boundaries: no schema change; audit summary remains committed-snapshot companion evidence.
- JSONL / log / audit sinks: no new JSONL sink; runtime summary JSON gains metadata fields.
- console / UI / operator output: quality dashboard payload gains freshness fields.
- rollback / recovery / retry: no retry behavior change; stale summary is disclosed, not deleted.
- cache / global state: no cache/global mutation; reads `GEULDOBI_RUN_ID` from environment.
- bootstrap fallback / config-env mutation: no mutation; absent env yields empty run id and `unknown` freshness.

## 7. Realization Architecture

1. Add a small helper in `AuditService` to build `run_scope` from env run id, timestamp, tag, and proof digest session lineage.
2. Add a small helper in `bridge_server` to classify runtime summary freshness and expose it with the loaded summary.
3. Extend `archive_benchmark_record()` manifest and CSV index with freshness metadata.
4. Add targeted tests without introducing broad live-run requirements.

## 8. Execution Tranches

1. Producer metadata: write `run_scope` and freshness hints into runtime audit summary.
2. Consumer projection: expose dashboard summary freshness.
3. Benchmark archival: carry freshness into manifest/index.
4. Verification and cleanup: run targeted tests, UTF-8 hygiene, diff check, ops validator, then close temp mirror.

## 9. Acceptance Criteria

- Runtime audit summary includes `run_scope.engine_run_id` when `GEULDOBI_RUN_ID` is present.
- Runtime audit summary includes `run_scope.latest_session_id` when proof digest has operational metadata.
- Dashboard runtime audit summary payload includes `freshness.status`.
- Benchmark manifest includes runtime summary freshness and run scope metadata.
- Benchmark index CSV includes a stable freshness status column.
- All additions remain advisory/companion only.

## 10. Verification Plan

- `python -m pytest tests/test_audit_service.py -q -k "summary"`
- `python -m pytest tests/test_archive_benchmark_record.py tests/test_bridge_quality_summary.py -q`
- `python -m ruff check modules/core/services/audit_service.py modules/api/bridge_server.py scripts/archive_benchmark_record.py tests/test_audit_service.py tests/test_archive_benchmark_record.py tests/test_bridge_quality_summary.py`
- `python scripts/check_utf8_hygiene.py modules/core/services/audit_service.py modules/api/bridge_server.py scripts/archive_benchmark_record.py tests/test_audit_service.py tests/test_archive_benchmark_record.py tests/test_bridge_quality_summary.py docs/2026-04-25/runtime-evidence-run-scope-freshness-execution-ssot.md`
- `git diff --check`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not make freshness metadata an authority gate.
- Do not delete stale summaries automatically.
- Do not use Python to judge narrative pass/reject quality.
- Do not change benchmark run id naming in this patch.
- Do not truncate DB `TEXT` evidence.

## 12. Temp Queue Notes

- temp status: completed
- cleanup condition: remove `docs/temp/runtime-evidence-run-scope-freshness-execution-ssot.md` after implementation, validation, and canonical closure update
- roadmap dependency: none; single queue item

## 13. Document 3-Pass Audit

Pass 1 - Structure and scope:

- Document type is execution SSOT.
- Canonical and temp paths are explicit.
- Included and excluded surfaces are bounded.
- Acceptance criteria and verification plan are present.

Pass 2 - Evidence and consistency:

- Claims are derived from live inspection on `ee978c7639e15e6f3c5dde22d82947cb7a718820`.
- The document does not claim live-run proof.
- The design preserves companion-evidence semantics and Director authority.
- Side-effect categories are covered or explicitly marked unchanged.

Pass 3 - Execution and readability:

- Execution tranches are small and ordered.
- The patch target is narrow enough for focused validation.
- Temp cleanup condition is explicit.
- Estimated confidence for implementation start: `95%`.

## 14. Closure Record

Implemented changes:

- `AuditService.write_audit_summary()` now writes `run_scope` and `freshness` companion metadata into `runtime_audit_summary.json`.
- `bridge_server._load_runtime_audit_summary()` now exposes runtime summary `run_scope` and `freshness` to the quality dashboard payload.
- `archive_benchmark_record()` now preserves runtime summary `run_scope` and `freshness` in benchmark manifests.
- `benchmark_index.csv` rows now include `runtime_freshness_status`.
- Regression tests cover audit summary producer metadata, dashboard projection, and archive/index carry-forward.

Validation:

- `python -m pytest tests/test_audit_service.py -q -k "summary"` -> `17 passed, 6 deselected`
- `python -m pytest tests/test_archive_benchmark_record.py tests/test_bridge_quality_summary.py -q` -> `21 passed`
- `python -m ruff check modules/core/services/audit_service.py modules/api/bridge_server.py scripts/archive_benchmark_record.py tests/test_audit_service.py tests/test_archive_benchmark_record.py tests/test_bridge_quality_summary.py` -> passed
- `python scripts/check_utf8_hygiene.py modules/core/services/audit_service.py modules/api/bridge_server.py scripts/archive_benchmark_record.py tests/test_audit_service.py tests/test_archive_benchmark_record.py tests/test_bridge_quality_summary.py docs/2026-04-25/runtime-evidence-run-scope-freshness-execution-ssot.md docs/temp/runtime-evidence-run-scope-freshness-execution-ssot.md` -> passed
- `git diff --check` -> passed
- `python scripts/ops_validator.py --strict` -> passed before temp closure

Complexity check:

- `AuditService.write_audit_summary`: `56 LOC`
- `bridge_server._load_runtime_audit_summary`: `45 LOC`
- `bridge_server._classify_runtime_summary_freshness`: `32 LOC`
- `archive_benchmark_record.archive_benchmark_record`: `95 LOC`
- no touched production function entered the `120+ LOC` or `180+ LOC` guard bands.

Code 3-pass audit:

- Pass 1 authority/sink audit: runtime summary, dashboard, and benchmark archive remain companion evidence; no Director or DB attempt truth authority changed.
- Pass 2 diff audit: no sink was removed; existing summary fields remain present; new fields are additive and operator-guidance-only.
- Pass 3 verification audit: targeted pytest, ruff, UTF-8 hygiene, diff check, ops validator, and complexity recount passed.

Final confidence: `96%`.
