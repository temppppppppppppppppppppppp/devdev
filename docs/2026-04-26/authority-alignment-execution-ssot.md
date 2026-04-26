# Authority Alignment Execution SSOT

Date: 2026-04-26
Status: closed
Canonical Path: `docs/2026-04-26/authority-alignment-execution-ssot.md`
Temp Mirror Path: `docs/temp/authority-alignment-execution-ssot.md`
Commit State:
- Baseline Commit: `e341e0a7826925391bc6572cf418d373a71ad608`
- Baseline Dirty Summary: clean
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: none
Source Survey Docs:
- `docs/2026-04-26/authority-alignment-3pass-audit.md`
Evidence Artifacts:
- no separate raw evidence artifact materialized; live source/test evidence is embedded in the audit and below
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: authority-alignment
  status: completed
  queue_role: front_active
  roadmap_rank: 1
  depends_on: []
  tranches:
    - id: stage4-atomic-truth-store-fail-closed
      title: Block fully_settled when WorldState or FactLedger persistence fails
    - id: manager-bible-fact-commit-boundary
      title: Gate Manager-derived Bible NPC mutations behind explicit fact-commit authority
    - id: verdict-layer-contract-normalization
      title: Separate Director final judgment from Python runtime routing gates
    - id: operator-mirror-authority-labels
      title: Prevent operator and mirror surfaces from overstating canonical truth
  verification_commands:
    - python -m pytest tests/test_stage4_post_processor.py -q
    - python -m pytest tests/test_stage2_finalizer.py -q
    - python -m pytest tests/test_blueprint_patch_mode.py -q
    - python -m pytest tests/test_stage4_interview_round.py -q
    - python scripts/ops_validator.py --strict
```

## 1. Intent

Realize the confirmed authority-alignment fixes from the 2026-04-26 3-pass audit.

The goal is maintenance, not feature expansion:
- `fully_settled` must not survive failed durable truth-store persistence.
- Canonical Bible facts must not be silently mutated by post-pass helper output without an explicit LLM/Director-owned fact-commit boundary.
- Python may collect evidence and block unsafe automation, but it must not be framed as the final narrative PASS/REJECT authority.
- Human-facing mirrors must stay below canonical runtime truth.

## 2. Baseline Facts

- Local `main` matches `origin/main` at `e341e0a7826925391bc6572cf418d373a71ad608`.
- `docs/temp/queue-state.json` was empty before this execution SSOT.
- Prior current-pipeline truth docs are closed and removed from the active temp queue.
- P0 confirmed by source and tests: `WorldState` / `FactLedger` save failures can still allow `process_pass_result()` to return `True`.
- P1 confirmed by source and tests: Manager-derived `new_lore.Key_NPCs` can mutate existing `master_bible.AssetLibrary.KeyNPCs` and later be persisted as canonical Bible.
- P2 confirmed: quality gates and post-select checks can still write REJECT-like outcomes into final verdict fields, even when metadata says Python is only a runtime routing gate.

## 3. Scope

Included:
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/project_manager.py`
- `main_a.py`
- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/stage3_validation_boundary.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_postselect_runtime.py`
- `modules/api/bridge_server.py`
- focused tests for the touched surfaces

Excluded:
- new narrative quality criteria
- desktop redesign or packaging
- material-side WorkGuard/TR/BI production
- broad refactors outside authority, persistence, or operator-truth seams
- any Python-only narrative quality PASS/REJECT decision

## 4. Pass 1. Inventory Summary

Confirmed severity inventory:
- P0: Stage4 atomic metadata persistence failure is currently non-blocking for top-level PASS settlement.
- P1: Manager-derived NPC facts can update canonical Bible state without an explicit fact-commit boundary.
- P2: Python quality/runtime gates blur final judgment semantics by mutating final verdict fields.
- P2/P3: operator/mirror surfaces can overstate success from process exit or partial proof.

Main runtime paths:
- `_save_world_state_atomic()`
- `_handle_atomic_metadata_failure()`
- `_run_pass_result_post_pass_pipeline()`
- `process_pass_result()`
- `_merge_manager_key_npcs_into_master_bible()`
- `_persist_shutdown_project_state()`
- Stage2/Stage3/Stage4 quality-gate verdict normalization helpers
- bridge `/run` completion broadcast and dashboard proof summary builders

Main test paths:
- `tests/test_stage4_post_processor.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_blueprint_patch_mode.py`
- `tests/test_stage4_interview_round.py`

## 5. Pass 2. Semantic Classification

Class A - settlement authority:
- `fully_settled` remains the only authoritative Stage4 completed PASS settlement.
- Durable truth-store persistence failure must block or demote settlement completion.

Class B - fact mutation authority:
- Manager can propose facts, but canonical Bible mutation needs an explicit commit boundary.
- Existing Bible facts should not be overwritten by helper output without conflict classification and LLM/Director ownership.

Class C - runtime routing gates:
- Python may route, block automation, and collect hard-invariant evidence.
- Python should not overwrite Director-owned final judgment fields in a way that makes Python appear to own narrative PASS/REJECT quality.

Class D - operator mirrors:
- Desktop/bridge/ClickUp/README/dashboard surfaces are companion views.
- They must not promote partial evidence or subprocess exit success above canonical pipeline truth.

## 6. Side-Effect Map

file writes / artifacts:
- Stage4 settlement packet and human manuscript export remain part of final settlement.
- Canonical Bible anchor writes happen through `save_v20_anchor("bible", ...)`.

DB / schema / transaction boundaries:
- `WorldState.save()` and `FactLedger.save()` are durable truth-store boundaries.
- `stage_attempts` and UI event rows can shape downstream repair/operator truth.
- If touched, DB diagnostic `TEXT` fields must preserve full reasons.

JSONL / log / audit sinks:
- stage attempts, UI events, JSONL logs, and dashboard summaries must remain evidence sinks.
- Metadata persistence failure should emit settlement-blocking evidence, not only warnings.

console / UI / operator output:
- Output must distinguish runtime exit, primary DB saved, metadata failed, packet failed, export failed, and fully settled.

rollback / recovery / retry:
- Existing WorldState/FactLedger rollback helps but is insufficient if top-level settlement still returns success.
- Prefer fail-closed propagation over soft warning-only recovery.

cache / global state:
- `master_bible`, `world_state._state`, and Manager-derived payloads are high-risk authority surfaces.
- Mutations must be contained until the correct commit boundary is satisfied.

bootstrap fallback / config-env mutation:
- Not directly applicable.

## 7. Realization Architecture

Use small sequential tranches. Do not start with broad normalization while P0 truth-store failure remains open.

1. Make `_save_world_state_atomic()` return or raise a settlement-blocking result.
2. Thread the result through `_run_pass_result_post_pass_pipeline()` and `process_pass_result()`.
3. Update tests that currently assert non-blocking metadata failure.
4. Replace direct Manager->Bible mutation with a proposed-delta or conflict-classified commit boundary.
5. Normalize verdict-layer contracts after the persistence and fact-commit boundaries are safe.
6. Reword operator/mirror surfaces so completion claims stay below canonical truth.

## 8. Execution Tranches

1. `stage4-atomic-truth-store-fail-closed`
   - Change atomic WorldState/FactLedger persistence failure from warning-only to settlement-blocking.
   - Ensure `process_pass_result()` returns `False` and does not emit `fully_settled` when either durable truth store fails.
   - Add or update regressions for WorldState save false, FactLedger save false, and exception paths.
   - Preserve rollback behavior where available.

2. `manager-bible-fact-commit-boundary`
   - Stop blind updates to existing `master_bible.AssetLibrary.KeyNPCs` fields from Manager `new_lore`.
   - Store Manager NPC changes as proposed deltas or only append truly new NPCs when no conflict exists.
   - Add a conflict path for existing NPC fields that differ.
   - Require explicit LLM/Director/fact-commit authority before overwriting existing canonical fields.

3. `verdict-layer-contract-normalization`
   - Inventory Stage2/3/4 paths that mutate `decision`, `verdict`, or `final_verdict` after Director review.
   - Separate fields such as `director_verdict`, `runtime_route_verdict`, `settlement_status`, and `final_judgment_authority`.
   - Keep hard invariant enforcement, especially deceased-character rejection, but frame it as routing/blocking evidence for Director-owned final judgment.

4. `operator-mirror-authority-labels`
   - Make bridge run completion and dashboard proof labels reflect semantic/canonical truth, not only process exit or partial proof availability.
   - Refresh stale human-facing queue wording if touched.
   - Keep ClickUp/GitHub sync below canonical queue-state and ops validation.

## 9. Acceptance Criteria

- `WorldState.save()` failure cannot lead to `fully_settled`.
- `FactLedger.save()` failure cannot lead to `fully_settled`.
- Stage4 settlement emits a clear non-settled status when atomic truth-store persistence fails.
- Existing rollback attempts still happen when available.
- Existing canonical `KeyNPCs` fields are not overwritten by Manager `new_lore` without explicit commit authority.
- Python quality/runtime gates are represented as runtime routing, not final narrative quality ownership.
- Operator-facing completion surfaces do not claim canonical success from subprocess exit alone.
- `python scripts/ops_validator.py --strict` passes with the temp mirror active.

## 10. Verification Plan

Minimum focused shards:
- `python -m pytest tests/test_stage4_post_processor.py -q`
- `python -m pytest tests/test_stage4_post_processor.py -k "atomic or WorldState or FactLedger or meta_save_failed or fully_settled" -q`
- `python -m pytest tests/test_stage2_finalizer.py -q`
- `python -m pytest tests/test_blueprint_patch_mode.py -q`
- `python -m pytest tests/test_stage4_interview_round.py -q`

Static and operational checks:
- `python -m ruff check <touched python files>`
- `python -m py_compile <touched python files>`
- `python scripts/check_utf8_hygiene.py <touched text/code/config/doc files>`
- `git diff --check`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Python collects, formats, compares, routes, and blocks unsafe automation; Python does not own final narrative quality judgment.
- Director/LLM remains final judgment authority.
- Deceased-character acting/speaking remains an absolute rejection invariant, but enforcement wording must not turn regex into final quality authority.
- Do not truncate touched DB diagnostic `TEXT` fields.
- Do not patch Korean/CJK text based on terminal rendering; byte-level UTF-8 readback wins.
- Do not broaden into desktop redesign, material-side pipeline, or Live API feature work.
- Do not leave temp mirror active after realization closure.

## 12. Temp Queue Notes

- temp status: in_progress
- cleanup condition: remove `docs/temp/authority-alignment-execution-ssot.md` only after all accepted tranches are implemented, verified, closure-audited, and the canonical doc is marked closed or completed.
- roadmap dependency: none; this is the only active system execution SSOT mirror at creation time.

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run this document through the 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document.

## 14. Document 3-Pass Audit

Pass 1 - structure and scope:
- PASS. This is an execution SSOT with explicit scope, tranches, side-effect coverage, acceptance criteria, verification, and temp queue notes.

Pass 2 - evidence and consistency:
- PASS. The P0 and P1 claims are backed by live source, existing tests, and focused pytest verification recorded in `docs/2026-04-26/authority-alignment-3pass-audit.md`.
- Prior closed execution docs are treated as lineage, not active queue authority.
- No claim relies on console encoding output.

Pass 3 - execution and readability:
- PASS. Execution starts with the P0 fail-closed tranche, then fact-commit boundary, then wider contract/operator normalization.
- The document does not authorize Python-owned narrative PASS/REJECT judgment.

Confidence Gate:
- Estimated confidence: 96%.
- Save decision: final canonical save and temp mirror are allowed.

## 15. Tranche 1 Implementation Note

Status: realized and locally verified.

Implemented changes:
- `modules/core/stage4_post_pass_runtime.py::_save_world_state_atomic()` now returns an explicit atomic metadata persistence status payload.
- WorldState or FactLedger persistence failure now returns `atomic_metadata_saved: false` with full failure detail instead of warning-only success.
- `modules/core/stage4_post_processor.py::_run_pass_result_post_pass_pipeline()` now converts atomic truth-store failure into `meta_save_failed=True`.
- `process_pass_result()` now routes that failure through `primary_persisted_meta_failed` and returns `False`, so `fully_settled` is not emitted.
- Settlement status `detail` no longer slices diagnostic text in Python.
- `tests/test_stage4_post_processor.py` now asserts that FactLedger exception, WorldState `save() -> False`, and FactLedger `save() -> False` all block PASS settlement.

Validation completed:
- `python -m pytest tests/test_stage4_post_processor.py -q`: passed, 108 tests.
- `python -m ruff check modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py tests/test_stage4_post_processor.py`: passed.
- `python -m py_compile modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py tests/test_stage4_post_processor.py`: passed.
- `python scripts/check_utf8_hygiene.py modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py tests/test_stage4_post_processor.py`: passed.

Complexity recount:
- `modules/core/stage4_post_pass_runtime.py`: max function 139 LOC, 180+ function count 0. Touched `_handle_atomic_metadata_failure` is 58 LOC and `_save_world_state_atomic` is 56 LOC.
- `modules/core/stage4_post_processor.py`: max function 171 LOC, 180+ function count 0. Touched `_run_pass_result_post_pass_pipeline` is 108 LOC, `_handle_post_pass_meta_failure` is 25 LOC, and `process_pass_result` is 171 LOC after helper extraction.

Document update 3-pass audit:
- Pass 1 - structure and scope: update is limited to tranche 1 and does not mark the whole SSOT closed.
- Pass 2 - evidence and consistency: validation evidence matches the touched files and tests; generated test log artifacts were removed from the worktree.
- Pass 3 - execution and readability: next tranche remains `manager-bible-fact-commit-boundary`; no Python-owned narrative PASS/REJECT authority was introduced.

Estimated confidence after tranche 1: 96%.

## 16. Tranche 2 Implementation Note

Status: realized and locally verified.

Implemented changes:
- `modules/core/stage4_post_pass_runtime.py::_merge_manager_key_npcs_into_master_bible()` no longer overwrites fields on existing `master_bible.AssetLibrary.KeyNPCs` entries.
- Manager-derived changes for existing NPCs are now stored under `MasterBible.FactCommitProposals.ManagerKeyNPCDeltas` with `authority_status: proposed_only_requires_director_fact_commit`.
- Truly new NPC entries are still appended to `AssetLibrary.KeyNPCs`.
- The function now returns a small summary payload with `appended_count`, `proposed_delta_count`, and the fact-commit authority note.
- Exception logging in the touched merge path now preserves the full exception string instead of slicing it.
- `tests/test_stage4_post_processor.py` now proves existing NPC updates become proposed deltas while new NPCs are appended.

Validation completed:
- `python -m pytest tests/test_stage4_post_processor.py -k "merge_manager_key_npcs_into_master_bible" -q`: passed, 1 test.
- `python -m pytest tests/test_stage4_post_processor.py -q`: passed, 108 tests.
- `python -m ruff check modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py tests/test_stage4_post_processor.py`: passed.
- `python -m py_compile modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py tests/test_stage4_post_processor.py`: passed.
- `python scripts/check_utf8_hygiene.py modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py tests/test_stage4_post_processor.py`: passed.

Complexity recount:
- `modules/core/stage4_post_pass_runtime.py`: max function 139 LOC, 180+ function count 0. Touched `_merge_manager_key_npcs_into_master_bible` is 85 LOC.
- `modules/core/stage4_post_processor.py`: max function 171 LOC, 180+ function count 0. No new 120+ or 180+ function was introduced.

Document update 3-pass audit:
- Pass 1 - structure and scope: update is limited to tranche 2 and does not close remaining authority-normalization work.
- Pass 2 - evidence and consistency: tests prove no direct overwrite of existing canonical NPC fields; new NPC append behavior remains.
- Pass 3 - execution and readability: next tranche remains `verdict-layer-contract-normalization`.

Estimated confidence after tranche 2: 96%.

## 17. Tranche 3 Implementation Note

Status: realized and locally verified.

Implemented changes:
- Stage2 quality-gate routing now records `director_verdict`, `runtime_route_verdict`, and `verdict_contract_version` next to the existing authority fields.
- Stage3 validation-boundary quality-gate routing now records the same verdict-layer contract fields in both the validation result and `pipeline_result["phases"]["validate"]`.
- Stage4 gate semantics now exposes `runtime_route_verdict` and `verdict_contract_version` in `gate_semantics` and `gate_semantics["verdict_layers"]`.
- Stage4 behavior was not changed: Director verdict and runtime route still produce the same PASS/REJECT outcomes as before; only the authority contract evidence was made explicit.
- The implementation deliberately kept the new Stage4 fields in small payload-builder/update functions instead of expanding the existing 180+ LOC normalization function.

Validation completed:
- `python -m pytest tests/test_stage2_finalizer.py::test_stage2_quality_gate_reject_records_runtime_gate_authority -q`: passed, 1 test.
- `python -m pytest tests/test_blueprint_patch_mode.py::TestBlueprintPatchIntegration::test_run_phase3_validation_logs_quality_gate_reason -q`: passed, 1 test.
- `python -m pytest tests/test_stage4_interview_round.py::TestLane2DirectorSemantics::test_save_director_selection_persists_gate_semantics_payload -q`: passed, 1 test.
- `python -m pytest tests/test_stage4_post_processor.py -q`: passed, 108 tests.
- `python -m ruff check modules/core/stage2_finalizer.py modules/domain/agents/stage3_validation_boundary.py modules/core/stage4_interview_round.py modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py tests/test_stage2_finalizer.py tests/test_blueprint_patch_mode.py tests/test_stage4_interview_round.py tests/test_stage4_post_processor.py`: passed.
- `python -m py_compile modules/core/stage2_finalizer.py modules/domain/agents/stage3_validation_boundary.py modules/core/stage4_interview_round.py modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py tests/test_stage2_finalizer.py tests/test_blueprint_patch_mode.py tests/test_stage4_interview_round.py tests/test_stage4_post_processor.py`: passed.
- `python scripts/check_utf8_hygiene.py modules/core/stage2_finalizer.py modules/domain/agents/stage3_validation_boundary.py modules/core/stage4_interview_round.py modules/core/stage4_post_pass_runtime.py modules/core/stage4_post_processor.py tests/test_stage2_finalizer.py tests/test_blueprint_patch_mode.py tests/test_stage4_interview_round.py tests/test_stage4_post_processor.py`: passed.

Complexity recount:
- `modules/core/stage2_finalizer.py`: touched `_maybe_reject_stage2_pass_for_quality_gate` is 79 LOC.
- `modules/domain/agents/stage3_validation_boundary.py`: touched `annotate_or_accept_terminal_quality_gate_result` is 96 LOC.
- `modules/core/stage4_interview_round.py`: touched `_apply_director_gate_update` is 22 LOC, `_build_gate_semantics_payload` is 54 LOC, and `_build_verdict_layers_payload` is 23 LOC.
- `modules/core/stage4_post_pass_runtime.py`: max function remains 139 LOC and 180+ count remains 0.
- `modules/core/stage4_post_processor.py`: max function remains 171 LOC and 180+ count remains 0.
- Pre-existing 180+ functions remain in unrelated parts of `stage2_finalizer.py` and `stage4_interview_round.py`; tranche 3 did not add or expand a 180+ function.

Document update 3-pass audit:
- Pass 1 - structure and scope: update is limited to tranche 3 and does not close the remaining operator/mirror authority-label work.
- Pass 2 - evidence and consistency: validation proves Stage2, Stage3, and Stage4 now expose separate Director and runtime route fields without changing gate behavior.
- Pass 3 - execution and readability: next tranche remains `operator-mirror-authority-labels`.

Estimated confidence after tranche 3: 96%.

## 18. Tranche 4 Implementation Note

Status: realized and locally verified.

Implemented changes:
- WebSocket `run_completed` / `run_failed` payloads now state that the event is a subprocess lifecycle signal only.
- `_build_run_exit_payload()` now includes `process_exit_status`, `completion_claim_scope`, `semantic_completion_status`, `canonical_truth_status`, and an operator-facing `authority_note`.
- Dashboard `proof_status` now labels itself as `proof_artifact_alignment_only`, with `canonical_truth_status: not_asserted_by_dashboard`.
- Dashboard proof summaries now avoid implying canonical completion; they describe proof evidence alignment only.
- `docs/implementation/event-schema-v1.json` documents the new run-exit authority fields.

Validation completed:
- `python -m pytest tests/test_process_runner.py::TestBridgeServerWiring::test_build_run_exit_payload_includes_runtime_diagnostics -q`: passed, 1 test.
- `python -m pytest tests/test_desktop_transport_contract.py::test_runtime_websocket_payload_contract_matches_renderer_and_backend_usage -q`: passed, 1 test.
- `python -m pytest tests/test_bridge_quality_summary.py::test_quality_dashboard_endpoint_surfaces_proof_status_and_sink_alignment -q`: passed, 1 test.
- `python -m pytest tests/test_api_contract.py -q`: passed, 63 tests.
- `python -m ruff check modules/api/bridge_server.py tests/test_process_runner.py tests/test_desktop_transport_contract.py tests/test_bridge_quality_summary.py`: passed.
- `python -m py_compile modules/api/bridge_server.py tests/test_process_runner.py tests/test_desktop_transport_contract.py tests/test_bridge_quality_summary.py`: passed.
- `python scripts/check_utf8_hygiene.py modules/api/bridge_server.py docs/implementation/event-schema-v1.json tests/test_process_runner.py tests/test_desktop_transport_contract.py tests/test_bridge_quality_summary.py`: passed.

Complexity recount:
- `modules/api/bridge_server.py::_build_run_exit_payload` is 20 LOC.
- `modules/api/bridge_server.py::_quality_dashboard_runtime_defaults` is 55 LOC.
- `modules/api/bridge_server.py::_build_dashboard_proof_status` is 49 LOC.
- No touched production function entered the 120+ or 180+ bands.

Document update 3-pass audit:
- Pass 1 - structure and scope: update is limited to operator/mirror authority labels.
- Pass 2 - evidence and consistency: bridge exit and dashboard proof surfaces now explicitly disclaim canonical semantic completion authority.
- Pass 3 - execution and readability: all four execution tranches are now realized.

Estimated confidence after tranche 4: 96%.

## 19. Closure Note

Closure status: closed.

Acceptance criteria review:
- PASS. `WorldState.save()` and `FactLedger.save()` failure paths now block `fully_settled`.
- PASS. Existing canonical Bible NPC fields are no longer overwritten by Manager `new_lore`; differing values become fact-commit proposals.
- PASS. Stage2, Stage3, and Stage4 verdict payloads now separate Director verdict from Python runtime route.
- PASS. Bridge and dashboard operator surfaces now avoid promoting process/proof evidence to canonical semantic completion.
- PASS. `python scripts/ops_validator.py --strict` passed while the temp mirror was active before cleanup.

Residual risk:
- No active residual implementation work remains in this execution SSOT.
- Pre-existing long functions remain in unrelated regions of `stage2_finalizer.py` and `stage4_interview_round.py`; this closure does not claim a complexity cleanup of those legacy hotspots.

Closure 3-pass audit:
- Pass 1 - realization state: all four planned tranches have landed and were locally verified with focused shards.
- Pass 2 - queue integrity: canonical and temp mirror matched before closure cleanup.
- Pass 3 - cleanup readiness: temp mirror may be removed and `docs/temp/queue-state.json` refreshed to empty.

Estimated closure confidence: 96%.
