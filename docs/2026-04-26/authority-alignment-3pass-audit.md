# Authority Alignment 3-Pass Audit

Date: 2026-04-26
Status: final
Canonical Path: `docs/2026-04-26/authority-alignment-3pass-audit.md`
Commit State:
- Baseline Commit: `e341e0a7826925391bc6572cf418d373a71ad608`
- Baseline Dirty Summary: clean
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: none
Source Inputs:
- live parallel authority-alignment survey on current `main`
- local source recheck on 2026-04-26
- prior closed execution docs:
  - `docs/2026-04-26/current-pipeline-truth-locks-execution-ssot.md`
  - `docs/2026-04-26/current-pipeline-residual-truth-locks-execution-ssot.md`
  - `docs/2026-04-26/current-pipeline-post-settlement-truth-residuals-execution-ssot.md`
Evidence Artifacts:
- no separate raw artifact materialized; inspected source/test paths are embedded below
Side-Effect Coverage: covered

## 1. Intent

Verify whether the new authority-alignment findings are real before creating an execution SSOT.

The audit is bounded to the current Stage2/Stage3/Stage4 pipeline authority surfaces:
- final settlement truth
- canonical Bible / WorldState / FactLedger mutation authority
- Director final-judgment ownership versus Python runtime routing gates
- operator and mirror surfaces that can overstate completion

## 2. Pass 1 - Structure and Scope

Result: PASS.

Scope is system-track maintenance, not narrative material production. The audit checks live code, tests, DB/write side effects, and operator-facing status surfaces. It does not authorize broad product work, desktop redesign, or new feature expansion.

Included surfaces:
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/stage3_validation_boundary.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_postselect_runtime.py`
- `modules/api/bridge_server.py`
- `main_a.py`
- `modules/core/project_manager.py`
- `tests/test_stage4_post_processor.py`

Excluded surfaces:
- material-side WorkGuard/TR/BI generation
- desktop packaging work unrelated to operator authority labels
- any change that lets Python own narrative PASS/REJECT quality

## 3. Pass 2 - Evidence and Consistency

Result: PASS.

Confirmed findings:
- P0 confirmed: `WorldState` / `FactLedger` atomic metadata save failures are treated as non-blocking and can allow `process_pass_result()` to return `True`.
  - `stage4_post_pass_runtime.py::_save_world_state_atomic()` catches metadata persistence failures and calls `_handle_atomic_metadata_failure()` without raising or returning failure.
  - `stage4_post_processor.py::process_pass_result()` only blocks on `_meta_save_failed`, then emits `fully_settled`.
  - Existing tests explicitly assert the current non-blocking behavior:
    - `test_transaction_rollback_on_failure`
    - `test_world_state_save_false_surfaces_last_save_error`
    - `test_fact_ledger_save_false_surfaces_last_save_error`
  - Verification run: `python -m pytest tests/test_stage4_post_processor.py -k "transaction_rollback_on_failure or world_state_save_false_surfaces_last_save_error or fact_ledger_save_false_surfaces_last_save_error" -q` passed with 3 tests.
- P1 confirmed: Manager-derived `new_lore.Key_NPCs` can mutate existing `master_bible.AssetLibrary.KeyNPCs` fields before canonical Bible shutdown persistence.
  - `_merge_manager_key_npcs_into_master_bible()` updates existing NPC dict fields when values differ.
  - `_build_manager_delta_collections()` calls that merge automatically.
  - `SovereignApp._persist_shutdown_project_state()` later saves `current_project.master_bible` through `save_v20_anchor("bible", ...)`.
  - Existing test `test_merge_manager_key_npcs_into_master_bible_merges_existing_and_new_entries` proves the merge path is intentional; verification run passed.
- P2 confirmed: Stage2/Stage3/Stage4 Python quality gates and post-select gates can mutate Director PASS-like verdicts to REJECT-like routing.
  - This is already partially labeled as `python_runtime_routing_gate`, but the same payload field often remains `final_verdict` or `decision`.
  - This should be normalized after the P0/P1 truth-persistence fixes, not before.
- P2/P3 confirmed: operator and mirror surfaces can overstate completion when they rely on process exit, stale README queue notes, or partial proof availability.

Rejected or downgraded findings:
- No current P0 was confirmed for CI missing core Stage4 truth shards; current workflow already includes a focused pipeline truth-lock shard from the prior wave.
- No standalone session-memory/cache-over-durable-truth P0 was confirmed during this audit.
- The Manager->Bible path is not pure Python fact rewriting because the source is an LLM Manager result; severity is P1 because it lacks a Director/fact-commit boundary for canonical Bible mutation.

## 4. Pass 3 - Execution Shape

Result: PASS.

Execution should be split into four ordered tranches:
1. Fail closed on Stage4 atomic truth-store persistence failures.
2. Add a Director/fact-commit boundary for Manager-derived canonical Bible NPC mutations.
3. Normalize verdict-layer fields so Python gates route or block automation without owning final narrative judgment.
4. Tighten operator/mirror wording so UI/ClickUp/README/dashboard surfaces cannot outrank canonical truth.

The first tranche is mandatory before any later cleanup because it controls whether `fully_settled` can be emitted with failed durable truth stores.

## 5. Side-Effect Coverage

file writes / artifacts:
- Stage4 settlement packet and human-facing export are downstream of metadata persistence.
- Canonical Bible anchor writes occur through `save_v20_anchor("bible", ...)`.

DB / schema / transaction boundaries:
- `WorldState.save()` and `FactLedger.save()` are current atomic metadata persistence sinks.
- `stage_attempts` settlement status and `fully_settled` UI events can present final truth after metadata failure.
- Touched DB diagnostic `TEXT` fields must preserve full text and avoid Python slicing.

JSONL / log / audit sinks:
- Stage4 settlement status and session logs are evidence sinks, not durable truth by themselves.
- Metadata failure must be represented as settlement-blocking, not as a soft advisory.

console / UI / operator output:
- Operator output should distinguish primary manuscript saved, metadata truth-store failed, settlement packet failed, human export failed, and fully settled.
- Console mojibake is not encoding evidence.

rollback / recovery / retry:
- Existing rollback helpers are not enough if the top-level settlement still returns success.
- Preferred fix: make atomic metadata failure return or raise a settlement-blocking signal.

cache / global state:
- Manager-derived NPC and position updates can mutate in-memory `master_bible` and `world_state._state`.
- Those mutations must not become canonical without an explicit LLM/Director-owned commit boundary.

bootstrap fallback / config-env mutation:
- Not directly applicable.

## 6. Confidence Gate

Estimated confidence: 96%.

Rationale:
- The P0 finding is backed by live source, existing tests that assert the risky behavior, and a focused pytest run.
- The P1 finding is backed by live source, canonical shutdown persistence, and an existing focused test.
- The P2/P3 findings are real but intentionally lower priority because prior waves already improved metadata wording and CI coverage.

Save decision: final audit save is allowed.
