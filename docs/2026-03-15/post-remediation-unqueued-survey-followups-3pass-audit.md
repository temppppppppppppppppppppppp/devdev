<!-- [완료] -->
# Post-Remediation Unqueued Survey Follow-Ups 3-Pass Audit

Date: 2026-03-15
Status: final
Canonical Follow-On: `docs/2026-03-15/post-remediation-unqueued-survey-followups-execution-ssot.md`
Temp Mirror Follow-On: `docs/temp/post-remediation-unqueued-survey-followups-execution-ssot.md`
Commit State:
- Baseline Commit: `bbb00a77c7356a32fe6358642cff0d3d445b7e8e`
- Baseline Dirty Summary: `dirty: AGENTS/docs/harness/menu7 docs edits, active roadmap/temp edits, harness/test edits, deleted local transcript file, unrelated pdf/style/log artifacts, and untracked post-remediation docs plus projects/000/`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `stagewise manuscript-truth lane is closed; TF-012, TF-014, TF-015, TF-016, and TF-019 are implemented, while TF-013, TF-017, TF-018, and TF-020 are closed as bounded decision/report artifacts`
Source Evidence:
- `docs/2026-03-15/codebase-global-post-remediation-3pass-audit.md`
- `docs/2026-03-15/codebase-global-post-remediation-deep-global-survey.md`
- `docs/2026-03-15/codebase-global-post-remediation-tf-composition.md`
- `docs/2026-03-15/codebase-global-post-remediation-cross-cut-integrity-matrix.md`
- `docs/2026-03-15/codebase-global-post-remediation-uncertainty-contradiction-ledger.md`
- `docs/2026-03-15/codebase-global-post-remediation-evidence-manifest.md`
- `docs/2026-03-15/codebase-global-post-remediation-evidence.txt`
- `docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-investigation.md`
- `docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-3pass-audit.md`
- `docs/2026-03-15/stage4-cw-context-db-retrieval-reject-persistence-evidence.txt`
- `docs/2026-03-15/menu7-desired-arc-input-contract-remediation-execution-ssot.md`
- `docs/2026-03-15/runtime-operator-surface-unification-refresh-remediation-execution-ssot.md`
- `docs/2026-03-15/backend-front-control-plane-connectivity-hardening-remediation-execution-ssot.md`

## 1. Intent
- Save one integrated execution SSOT for the final 2026-03-15 action-bearing survey findings that were still outside the active temp queue.
- Keep this document explicitly narrower than "all today's docs" so evidence-only files, drafts, and already-queued items do not become duplicate queue authorities.
- Preserve menu `7` as its own dedicated queue item while absorbing the remaining residual follow-up work into one bounded lane.

## 2. Pass 1. Structure And Scope
- Document type is correct:
  - this is an execution SSOT for residual follow-up work, not a fresh survey bundle or a second roadmap
- Scope is explicit:
  - included: final action-bearing residual items `TF-012` through `TF-020`
  - excluded: already-queued items `TF-007` through `TF-011`, closed/superseded execution lanes, draft-live-run documents, and non-system notes
- Output set is coherent:
  - one canonical execution SSOT
  - one temp mirror
  - no competing per-item roadmap
- Queue semantics are clear:
  - this document is a single residual lane beneath the master post-remediation roadmap, not a replacement for it

Pass 1 judgment:
- pass

## 3. Pass 2. Evidence And Consistency
- The residual item boundary is supported by the post-remediation TF composition:
  - `TF-010` and `TF-011` already belong to dedicated operator-surface execution lanes
  - `TF-012` through `TF-020` remain as the unqueued residual action-bearing set
- The Stage 4 follow-up is both final and action-bearing:
  - `stage4-cw-context-db-retrieval-reject-persistence-investigation.md` is final
  - its conclusions are narrow enough to support one bounded runtime follow-up lane rather than a full new survey bundle
- Draft and provisional documents are correctly excluded:
  - `codebase-stagewise-live-merge-000-*` files remain `draft-live-run-pending`
  - they are useful evidence, but not authoritative enough to govern queue creation
- Closed or superseded lanes are correctly excluded:
  - `interactive-prompt-contract-refresh-execution-ssot.md` is closed
  - `frontierlag-nonstop-utf8-hygiene-remediation-execution-ssot.md` is closed
  - the current residual lane should not reopen either item
- Existing active queue items are correctly left outside this lane:
  - menu7
  - backend-front/control-plane
  - runtime/operator surface
  - completed persistence and encoding lanes retained in temp pending closure cleanup
- Workspace drift does not invalidate tranche order:
  - the new `projects/000` manuscript-truth report closes its own lane and reduces duplicate Stage 4 re-survey pressure
  - the integrated residual lane is now the active master-roadmap queue controller for the remaining residual work
  - `TF-012` has landed as the first direct runtime follow-up through existing DB helper and Stage 4 context surfaces
  - `TF-013` has now ended as a bounded decision doc with no successor split
  - `TF-017` has now ended as a bounded decision doc with no successor split
  - `TF-018` has now ended as a bounded decision doc with no successor split
  - `TF-020` has now ended as a bounded report artifact with no successor split

Pass 2 judgment:
- pass

## 4. Pass 3. Execution Shape
- The execution shape is actionable:
  1. `TF-012` has landed first as the only direct runtime follow-up
  2. `TF-013` has ended as a bounded decision doc that retains the current single-connection model
  3. `TF-017` has ended as a bounded decision doc that retains the split JSONL lock strategy
  4. `TF-018` has ended as a bounded decision doc that retains the current DI structure while refreshing live slot inventory authority
  5. `TF-020` has ended as a bounded coverage-mapping report with explicit blocker disclosure rather than a new implementation lane
  6. broader code-health items are now fully closed after `TF-014` runtime print hardening, `TF-015` auto-fix, `TF-016` manual entrypoint suppression, and `TF-019` guard-config validation
- The document avoids roadmap fragmentation:
  - it creates one residual lane instead of spawning many low-signal queue items from every evidence artifact
- Guardrails are explicit:
  - do not reopen menu `7`
  - do not over-diagnose the Stage 4 issue as blanket miswiring
  - do not promote draft-live-run notes to active queue authority
- Execution-start shape is still bounded:
  - tranche `1` can proceed as a helper/context follow-up without reopening DB schema, prompt surfaces, or the broad residual backlog
  - richer retrieval authority can land inside existing DB helper and Stage 4 context surfaces with targeted regression coverage only

Pass 3 judgment:
- pass

## 5. Confidence And Save Gate
- Pass 1 structure and scope: pass
- Pass 2 evidence and consistency: pass
- Pass 3 execution and readability: pass
- Estimated confidence: `97%`
- Save decision: final save allowed
- Execution-start decision: proceed allowed for `TF-012`
- Post-implementation decision: `TF-012`, `TF-014`, `TF-015`, `TF-016`, and `TF-019` accepted; `TF-013`, `TF-017`, `TF-018`, and `TF-020` accepted as bounded decision/report artifacts; close the residual lane

## 6. Audit Conclusion
- The residual 2026-03-15 action-bearing survey findings should be governed by one integrated execution SSOT, not by a new set of parallel per-item queue docs.
- Menu `7` remains a separate dedicated execution lane and is intentionally excluded from this integrated residual lane.
- The master roadmap should reference this document as the sole queue authority for the now-complete residual items `TF-012` through `TF-020` and then remove the temp mirror during closure refresh.

## 7. TF-012 Post-Implementation Confirmation
- Landed files:
  - `modules/core/db_manager.py`
  - `modules/core/stage4_context_builder.py`
  - `tests/test_db_manager.py`
  - `tests/test_stage4_context_builder.py`
- Landed behavior:
  - Stage 4 attempt retrieval now exposes richer persisted rationale/artifact lineage without a schema change
  - mandatory Stage 4 failure context now includes representative rejection and retry/advisory guidance instead of the thinner prior subset
- Verification:
  - `python -m py_compile modules/core/db_manager.py modules/core/stage4_context_builder.py tests/test_db_manager.py tests/test_stage4_context_builder.py`
  - `python -m pytest tests/test_db_manager.py -k "stage_attempts_for_arc or save_stage_attempt_persists_rationale_fields"` -> `2 passed, 28 deselected`
  - `python -m pytest tests/test_stage4_context_builder.py -k "stage2_failure_context"` -> `1 passed, 48 deselected`
- Queue decision:
  - accept `TF-012` as complete inside the integrated lane
  - keep the residual lane open for the remaining TF items

## 8. TF-013 Decision Confirmation
- Landed files:
  - `docs/2026-03-15/tf-013-db-connection-pooling-evaluation.md`
  - `docs/2026-03-15/tf-013-db-connection-pooling-evaluation-3pass-audit.md`
- Landed decision:
  - retain the current single shared SQLite connection model
  - do not create a successor execution SSOT for general-purpose pooling
- Evidence basis:
  - current DB model remains `RLock + WAL + nested transaction checks + 30s timeout`
  - `AuditService` already has a dedicated read-only `mode=ro` connection seam for proof/audit reads
  - Stage 4 DB advisory reads are assembled serially outside the 8-way advisory executor
  - direct `.conn.*` bypasses still exist across `8` non-DBManager files, so pooling would widen scope into abstraction refactoring
- Verification:
  - `python -m pytest tests/test_integrity.py -k concurrent_episode_number_generation` -> `1 passed, 21 deselected`
  - `rg -n "database is locked" projects/00_260315/logs docs/2026-03-15 -g "*.log" -g "*.txt" -g "*.md"` -> `0 matches`
- Queue decision:
  - accept `TF-013` as complete inside the integrated lane
  - continue with the remaining evaluation items, then the later hardening tranche

## 9. TF-017 Decision Confirmation
- Landed files:
  - `docs/2026-03-15/tf-017-jsonl-sink-consolidation-evaluation.md`
  - `docs/2026-03-15/tf-017-jsonl-sink-consolidation-evaluation-3pass-audit.md`
- Landed decision:
  - retain the current split JSONL sink lock strategy
  - do not create a successor execution SSOT for global lock unification
- Evidence basis:
  - completed-slice JSONL/DB sink alignment remained intact after the earlier persistence lane
  - `SessionLogger`, `AuditService`, `SoftFailure`, `QualityDashboard`, and Stage 4 append helpers still have materially different writer lifecycle semantics
  - current code-visible writer ownership is not normalized enough for safe lock unification yet
- Verification:
  - `python -m pytest tests/test_session_logger.py -k "ui_event_creates_ui_events_jsonl"` -> `1 passed, 20 deselected`
  - `python -m pytest tests/test_audit_service.py -k "runtime_audit"` -> `1 passed, 11 deselected`
  - `python -m pytest tests/test_validation_orchestrator_soft_failure.py` -> `4 passed`
  - `python -m pytest tests/test_failure_analyzer.py -k "sink_alignment_uses_selection_candidate_key_from_episode_production_when_available or failure_analyzer_summary_reports_soft_failures"` -> `2 passed, 11 deselected`
  - `python -m pytest tests/test_stage4_orchestrator.py -k "runtime_audit_summary"` -> `5 passed, 51 deselected`
- Queue decision:
  - accept `TF-017` as complete inside the integrated lane
  - continue with `TF-020`, then the later hardening tranche

## 10. TF-018 Decision Confirmation
- Landed files:
  - `docs/2026-03-15/tf-018-di-context-slot-audit-evaluation.md`
  - `docs/2026-03-15/tf-018-di-context-slot-audit-evaluation-3pass-audit.md`
- Landed decision:
  - retain the current flat `Stage2Context` and `Stage3Context` runtime surface
  - retain the current hybrid `Stage4Context` grouping pattern
  - do not create a successor execution SSOT for DI callback grouping or Stage 2 sub-object delegation
- Evidence basis:
  - live source inspection now shows slot counts of `Stage2=52`, `Stage3=24`, and `Stage4=30`, while the older March 15 survey bundle still records `47 / 19 / 26`
  - Stage 2 callback/observer names remain a broad downstream compatibility surface across runtime code and tests
  - Stage 2 already centralizes retry callback resolution through `_RETRY_FEEDBACK_CALLBACK_SPECS` and the retry contract/missing-callback ledger
  - Stage 4 already groups optional modules into `conditional_modules` and stores selected callback-like surfaces behind property accessors backed by `_stage4_context_budget_meta`
- Verification:
  - `python -m pytest tests/test_stage2_context.py` -> `20 passed`
  - `python -m pytest tests/test_stage4_context.py` -> `34 passed`
  - `python -m pytest tests/test_runtime_ownership_contract.py` -> `6 passed`
  - `python -m pytest tests/integration/test_pipeline_smoke.py -k "stage2_context_slot_count or stage4_context_slot_count"` -> `2 passed, 32 deselected`
  - `python -m pytest tests/test_main_a_persistence_helpers.py -k reserved_state_service_facade_shims` -> `1 passed, 9 deselected`
- Queue decision:
  - accept `TF-018` as complete inside the integrated lane
  - continue with `TF-020`, then the later hardening tranche

## 11. TF-020 Report Confirmation
- Landed files:
  - `docs/2026-03-15/tf-020-test-coverage-mapping-report.md`
  - `docs/2026-03-15/tf-020-test-coverage-mapping-report-3pass-audit.md`
  - `docs/2026-03-15/tf-020-test-coverage-report.txt`
  - `docs/2026-03-15/tf-020-test-coverage-report.json`
- Landed decision:
  - save the current module-level coverage baseline as a report artifact
  - do not create a successor execution SSOT for TF-020 itself
- Evidence basis:
  - current workspace counts are `245` module files and `309` test files, replacing the stale survey snapshot `244 / 315`
  - Coverage.py captured `60.63%` total coverage across `60,763` executable statements
  - `16` executable modules are currently at `0%` coverage and `32` are below `25%`
  - the low-memory full-suite run recorded `26` shards total with `14` passed and `12` failed
- Verification:
  - `python scripts/run_pytest_lowmem.py tests --chunk-size 12 --keep-going --log-dir logs/pytest_lowmem/tf020_20260315_235935 --pytest-arg=--cov=modules --pytest-arg=--cov-append --pytest-arg=--cov-report=term-missing:skip-covered` -> `26 shards / 14 passed / 12 failed`
  - `python -m coverage json --data-file logs/coverage/tf020_20260315_235935/.coverage -o logs/coverage/tf020_20260315_235935/coverage.json` -> `saved`
  - `python -m coverage report --data-file logs/coverage/tf020_20260315_235935/.coverage` -> `60.63%`
- Queue decision:
  - accept `TF-020` as complete inside the integrated lane
  - continue only with the later hardening tranche

## 12. TF-014 Implementation Confirmation
- Landed files:
  - `main_a.py`
  - `modules/core/stage2_finalizer.py`
  - `modules/core/vec_memory.py`
  - `tests/test_runtime_print_allowlist.py`
  - `docs/2026-03-16/tf-014-console-print-audit.md`
  - `docs/2026-03-16/tf-014-console-print-audit-3pass-audit.md`
- Landed decision:
  - remove the `5` remaining runtime diagnostic builtin prints
  - keep only the `2` bootstrap prints in `main_a.py` plus the `8` operator-facing blank-line spinner prints in `modules/core/stage0/spinner.py`
- Evidence basis:
  - AST recount is the authoritative builtin-print measure, not regex alone
  - `main_a.py` lazy-import warnings, `stage2_finalizer.py` Director status prints, and `vec_memory.py` fallback logging all already had safer non-builtin output paths available
- Verification:
  - `python -m py_compile main_a.py modules/core/stage2_finalizer.py modules/core/vec_memory.py tests/test_runtime_print_allowlist.py` -> `passed`
  - `python -m pytest tests/test_runtime_print_allowlist.py` -> `1 passed`
  - `python -m pytest tests/test_stage2_finalizer.py -k "director_pass_returns_break or director_reject_returns_retry"` -> `2 passed, 22 deselected`
  - `python -m pytest tests/test_vec_memory.py -k "test_in_memory_operational or test_status_fields or test_no_sqlite_vec_graceful"` -> `3 passed, 64 deselected`
- Queue decision:
  - accept `TF-014` as complete inside the integrated lane
  - continue with `TF-015`, `TF-016`, and `TF-019`

## 13. TF-015 Implementation Confirmation
- Landed files:
  - `docs/2026-03-16/tf-015-ruff-auto-fix.md`
  - `docs/2026-03-16/tf-015-ruff-auto-fix-3pass-audit.md`
  - auto-fixed runtime and ops-support files under `modules/`, `scripts/`, and `main_a.py`
  - `modules/api/__init__.py`
  - `modules/api/run_validator.py`
- Landed decision:
  - resolve every auto-fixable Ruff finding
  - stop when the remaining lint set becomes manual-only `E402`
- Evidence basis:
  - `ruff check --fix` reduced the live lint backlog to only `9` `E402` script-entrypoint violations
  - one validation-caught regression (`RISK_KEYS` export) was corrected immediately and kept out of the residual manual lane
- Verification:
  - `python -m py_compile main_a.py modules/api/__init__.py modules/api/bridge_server.py modules/api/prompt_broker.py modules/api/prompt_classifier.py modules/api/risk_approval.py modules/api/run_validator.py modules/core/arc_state_utils.py modules/core/db_manager.py modules/core/investment_arithmetic_checker.py modules/core/investment_math_verifier.py modules/core/services/project_service.py modules/core/services/ui_service.py modules/core/stage2_finalizer.py modules/core/stage3_orchestrator.py modules/core/stage4_context_builder.py modules/core/stage4_interview_round.py modules/core/vec_memory.py modules/domain/agents/blueprint_ensemble.py modules/domain/agents/chief_writer_context.py modules/validation/validation_orchestrator.py scripts/audit_bi_5pass.py scripts/build_execution_roadmap.py scripts/build_investment_epub_corpus.py scripts/check_utf8_hygiene.py scripts/ops_support.py scripts/ops_validator.py scripts/process_and_audit_tr_bi_loop.py scripts/repair_tr_korean_utf8.py scripts/run_auto_frontier_lag_harness.py scripts/run_pytest_lowmem.py scripts/run_stale_reference_sweep.py scripts/sync_temp_queue_state.py scripts/tr_batch_harness.py scripts/validate_deep_global_survey_bundle.py` -> `passed`
  - `python -m pytest tests/test_run_validator.py tests/test_risk_approval.py tests/test_bridge_server_http_contract.py tests/test_bridge_server_desktop_risk_gate.py tests/test_control_plane_approval_provenance_ssot.py` -> `88 passed`
  - `python -m pytest tests/test_desktop_transport_contract.py tests/test_desktop_shadow_hygiene.py tests/test_main_a_boot_binding.py tests/test_project_service.py tests/test_ui_service.py` -> `54 passed`
  - `python -m pytest tests/test_stage2_finalizer.py tests/test_stage4_context_builder.py tests/test_validation_orchestrator_soft_failure.py tests/test_vec_memory.py -k "not slow"` -> `144 passed`
  - `ruff check modules scripts main_a.py --statistics` -> `9 E402 remaining`
- Queue decision:
  - accept `TF-015` as complete inside the residual lane
  - continue with `TF-016` and `TF-019`

## 14. TF-016 Implementation Confirmation
- Landed files:
  - `docs/2026-03-16/tf-016-ruff-manual-fix.md`
  - `docs/2026-03-16/tf-016-ruff-manual-fix-3pass-audit.md`
  - `scripts/audit_bi_5pass.py`
  - `scripts/backfill_quality_sidecars.py`
  - `scripts/build_bi_from_phase0_and_tr.py`
  - `scripts/build_chaebol_allowance_zero_assets.py`
  - `scripts/build_fallen_prince_buys_joseon_assets.py`
  - `scripts/build_investment_epub_corpus.py`
  - `scripts/process_and_audit_tr_bi_loop.py`
- Landed decision:
  - suppress the intentional entrypoint `E402` import-order cases in place with rationale
  - do not rewrite script bootstrap ordering
- Evidence basis:
  - the remaining lint set after `TF-015` was only `9` `E402` findings
  - every hit sat directly behind a required `sys.path.insert(...)` bootstrap
- Verification:
  - `python -m py_compile scripts/audit_bi_5pass.py scripts/backfill_quality_sidecars.py scripts/build_bi_from_phase0_and_tr.py scripts/build_chaebol_allowance_zero_assets.py scripts/build_fallen_prince_buys_joseon_assets.py scripts/build_investment_epub_corpus.py scripts/process_and_audit_tr_bi_loop.py` -> `passed`
  - `ruff check modules scripts main_a.py` -> `All checks passed!`
- Queue decision:
  - accept `TF-016` as complete inside the residual lane
  - continue only with `TF-019`

## 15. TF-019 Implementation Confirmation
- Landed files:
  - `docs/2026-03-16/tf-019-guard-chain-config-validation.md`
  - `docs/2026-03-16/tf-019-guard-chain-config-validation-3pass-audit.md`
  - `modules/core/genre_guards/work_guard.py`
  - `modules/core/project_support.py`
  - `main_a.py`
  - `tests/test_work_guard.py`
  - `tests/test_project_support.py`
  - `tests/test_main_a_boot_binding.py`
- Landed decision:
  - fail fast when a present `work_guard.yaml` is malformed or structurally invalid
  - keep missing and zero-byte guard files non-fatal
  - mark invalid present guard files as not ready in support-summary surfaces
- Evidence basis:
  - pre-patch `WorkGuard` downgraded malformed YAML and wrong root/container shapes to `{}` and could silently continue with the base guard
  - `main_a.py` now logs `invalid work_guard.yaml` before re-raising the config error
  - `project_support` now distinguishes `work_guard_exists` from `work_guard_valid`
- Verification:
  - `python -m py_compile modules/core/genre_guards/work_guard.py modules/core/project_support.py main_a.py tests/test_work_guard.py tests/test_project_support.py tests/test_main_a_boot_binding.py` -> `passed`
  - `ruff check modules/core/genre_guards/work_guard.py modules/core/project_support.py main_a.py tests/test_work_guard.py tests/test_project_support.py tests/test_main_a_boot_binding.py` -> `All checks passed!`
  - `python -m pytest tests/test_work_guard.py -k "invalid_yaml or invalid_work_identity_shape"` -> `2 passed, 31 deselected`
  - `python -m pytest tests/test_project_support.py -k "invalid_yaml or invalid_work_guard_not_ready or handles_missing_file"` -> `3 passed, 6 deselected`
  - `python -m pytest tests/test_main_a_boot_binding.py -k "invalid_work_guard or has_no_bare_input_calls or routes_prompt_helpers"` -> `3 passed, 8 deselected`
  - `python -m pytest tests/test_quality_sidecar_bootstrap.py -k "bootstrap_quality_sidecars_backfills_legacy_stage4_rows or quality_dashboard_endpoint_is_read_only_for_legacy_quality_sidecars"` -> `2 passed`
  - `python -m pytest tests/test_bridge_quality_summary.py -k "quality_dashboard_endpoint_combines_result_and_patterns"` -> `1 passed, 7 deselected`
- Queue decision:
  - accept `TF-019` as complete inside the residual lane
  - close the residual lane and remove its temp mirror during queue refresh
