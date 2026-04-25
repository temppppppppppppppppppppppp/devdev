# Stage4 Pass Settlement Authority Recheck Execution SSOT

Date: 2026-04-25
Status: execution-ready
Canonical Path: `docs/2026-04-25/stage4-pass-settlement-authority-recheck-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-pass-settlement-authority-recheck-execution-ssot.md`
Commit State:
- Baseline Commit: `2bcb2db2c4364400628cb55890609aee1f0a9db3`
- Baseline Dirty Summary: `dirty: 1 untracked; docs/2026-04-25/codebase-parallel-deep-survey-wave1-synthesis.md`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same commit; dirty docs-only queue setup: codebase-parallel-deep-survey-wave1-synthesis.md plus canonical/temp execution SSOT`
Source Survey Docs:
- `docs/2026-04-25/codebase-parallel-deep-survey-wave1-synthesis.md`
Evidence Artifacts:
- inline live-code evidence from `modules/core/stage4_post_processor.py`, `modules/core/stage4_post_pass_runtime.py`, `modules/core/stage4_orchestrator.py`, `tests/test_stage4_post_processor.py`, and `tests/test_stage4_pass_artifact_contract.py`
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: stage4-pass-settlement-authority-recheck
  status: pending
  queue_role: front_active
  roadmap_rank: 1
  depends_on: []
  tranches:
    - id: settlement-state-model
      title: Define persisted versus fully settled PASS authority
    - id: partial-settlement-observability
      title: Surface partial settlement explicitly across DB, logs, audit, and UI-facing callbacks
    - id: regression-shards
      title: Verify Stage4 post-processor and orchestrator settlement regressions
  verification_commands:
    - python -m pytest tests/test_stage4_post_processor.py -q
    - python -m pytest tests/test_stage4_pass_artifact_contract.py -q
    - python -m pytest tests/test_stage4_orchestrator.py -q
    - python scripts/ops_validator.py --strict
```

## 1. Intent

This execution item hardens Stage4 PASS settlement semantics without adding a new feature.

The current code already distinguishes several failure states by returning `False`, but the important maintenance question is sharper:

- When is a manuscript only persisted?
- When is post-pass metadata settled?
- When is an episode fully authoritative as a PASS?
- How should resume/operator surfaces avoid treating partial persistence as full success?

The goal is to make those boundaries explicit, testable, and observable.

## 2. Baseline Facts

Live-code facts:

- `Stage4PostProcessor._save_pass_result_primary_db()` saves the manuscript and HUD snapshot inside a DB transaction, then commits before downstream post-pass settlement begins.
- `Stage4PostProcessor.process_pass_result()` returns `False` when primary DB save fails.
- After primary DB save succeeds, `process_pass_result()` runs quality sidecars, local side effects, and the post-pass pipeline.
- If `post_pass_payload["meta_save_failed"]` is true, `process_pass_result()` returns `False` before settlement packet export, human-facing txt export, and final session update.
- If settlement packet save fails, `process_pass_result()` returns `False` after manuscript and metadata work may already have succeeded.
- If human-facing txt export fails, `process_pass_result()` returns `False` after structured settlement packet save.
- `Stage4Orchestrator._consume_episode_round_outcome()` breaks the episode loop when `_process_episode_pass()` returns false.

Key evidence:

- `modules/core/stage4_post_processor.py:890`
- `modules/core/stage4_post_processor.py:1213`
- `modules/core/stage4_post_processor.py:1287`
- `modules/core/stage4_post_processor.py:1303`
- `modules/core/stage4_post_processor.py:1336`
- `modules/core/stage4_post_processor.py:1363`
- `modules/core/stage4_orchestrator.py:1524`

Existing tests already cover:

- DB save failure writes emergency dump and returns false.
- metadata save failure returns false and skips settlement packet, text export, and finalization.
- settlement packet failure returns false and skips text export/finalization.
- human-facing text export failure returns false.
- pass artifact contract requires manuscript save, episode bible save, settlement packet, and relevant hard-incomplete behavior.

Key test evidence:

- `tests/test_stage4_post_processor.py:157`
- `tests/test_stage4_post_processor.py:188`
- `tests/test_stage4_post_processor.py:221`
- `tests/test_stage4_pass_artifact_contract.py:148`
- `tests/test_stage4_pass_artifact_contract.py:161`

## 3. Scope

Included:

- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_episode_logging.py`, if the final status surface needs a shared payload helper
- `modules/core/services/audit_service.py`, if audit summary status needs to distinguish partial settlement
- `modules/api/control_plane_contract.py` and bridge/UI surfaces only if the status contract already exposes misleading PASS completion
- `tests/test_stage4_post_processor.py`
- `tests/test_stage4_pass_artifact_contract.py`
- focused `tests/test_stage4_orchestrator.py` coverage only when orchestrator behavior changes

Excluded:

- Provider-native sidecars such as Live API, Memory Bank, or model-specific sessions.
- Broad Stage4 retry redesign.
- Broad UI redesign.
- DB schema migration unless live-code evidence proves no existing status channel can represent partial settlement safely.
- Full repository test suite in one pass.
- Narrative pipeline behavior outside Stage4 runtime settlement.

## 4. Pass 1. Inventory Summary

Current settlement path:

1. Normalize final manuscript.
2. Resolve approved HUD updates.
3. Save primary DB manuscript/HUD snapshot transaction.
4. Save quality sidecars.
5. Run local side effects.
6. Run post-pass pipeline:
   - Manager/audit delta.
   - episode bible and metadata persistence.
   - WorldState/FactLedger updates.
   - post-pass advisories and contract signal.
7. Abort on `meta_save_failed`.
8. Persist structured settlement packet.
9. Abort on packet save failure.
10. Write human-facing txt export.
11. Abort on txt export failure.
12. Finalize pass result session.
13. Return true.

Primary risk:

- Steps 3 through 11 create multiple partial-success states, all currently represented to the orchestrator as `False`.
- Returning `False` is safe for loop continuation, but insufficient as an authority model if downstream resume/operator code only checks whether a manuscript row or artifact exists.

## 5. Pass 2. Semantic Classification

Class A - Hard failure before durable episode content:

- Primary DB manuscript save fails.
- Expected state: no authoritative manuscript row; emergency dump may exist.
- Current behavior: returns false and attempts emergency dump.

Class B - Partial persisted episode, not fully settled:

- Primary manuscript save succeeds, but episode bible/metadata settlement fails.
- Expected state: manuscript exists, but episode must not be counted as fully PASS-settled.
- Current behavior: returns false, logs operator error, skips packet/export/finalization.

Class C - Structured settlement exists, human-facing export failed:

- Primary manuscript, metadata, and settlement packet may exist; txt export fails.
- Expected state: structured authority may be enough for machine resume, but human-facing output is incomplete.
- Current behavior: returns false and does not finalize session.

Class D - Fully settled PASS:

- Primary DB, metadata, settlement packet, human-facing export, and finalization all succeeded.
- Expected state: safe to treat episode as fully PASS-settled.
- Current behavior: returns true.

## 6. Side-Effect Map

File writes / artifacts:

- emergency manuscript dump on primary DB save failure
- structured settlement packet under Stage4 export path
- human-facing txt manuscript export
- possible logged artifacts from Stage4 retry/outcome paths

DB / schema / transaction boundaries:

- primary manuscript save and HUD snapshot are transaction-protected
- episode bible, state logs, WorldState, FactLedger, quality tables, and telemetry are separate downstream persistence surfaces
- this execution should avoid schema migration unless existing sinks cannot express the settlement state

JSONL / log / audit sinks:

- `episode_production.jsonl`
- `runtime_audit.jsonl`
- `runtime_audit_summary.json`
- session decisions/UI events
- Stage4 post-pass contract signal

Console / UI / operator output:

- `ctx.ui.log()` currently reports partial failures using error-level structured metadata.
- API/UI may still infer too much from companion status or stdout if no durable settlement state is exposed.

Rollback / recovery / retry:

- Orchestrator breaks the episode loop on false from `_process_episode_pass()`.
- Resume logic must not treat a partially persisted manuscript as a fully settled PASS unless settlement markers are complete.

Cache / global state:

- WorldState and FactLedger updates may have already occurred before later export failure states.
- Any implementation must avoid double-applying state updates on resume.

Bootstrap fallback / config-env mutation:

- Not directly applicable.

## 7. Realization Architecture

Preferred approach:

1. Introduce an internal settlement-state model before changing behavior.
2. Keep `process_pass_result()` boolean compatibility unless a narrow typed return can be contained without broad churn.
3. Make each partial state observable through an existing durable or structured sink.
4. Ensure resume/operator code can distinguish:
   - `primary_db_failed`
   - `primary_persisted_meta_failed`
   - `settlement_packet_failed`
   - `human_export_failed`
   - `fully_settled`
5. Avoid treating human-facing txt failure as identical to episode bible/metadata failure unless that is an explicit product decision.

Implementation shape to evaluate during execution:

- Option A: internal helper returns a structured settlement status while `process_pass_result()` continues returning bool.
- Option B: add durable settlement status to existing episode/attempt telemetry without schema migration.
- Option C: if no existing durable surface is sufficient, propose a small schema addition in a separate doc before implementation.

Default bias:

- Try Option A plus existing structured logs/tests first.
- Escalate to schema only if necessary.

## 8. Execution Tranches

1. Settlement status trace

- Trace all code paths from primary manuscript save through finalization.
- Identify which surfaces currently prove fully settled PASS.
- Identify whether any resume/status path treats manuscript existence as full success.
- Update this execution doc's `Resume Commit` and `Resume Drift Summary` before patching.

2. Minimal state model patch

- Add a bounded internal status helper or payload.
- Preserve existing public boolean behavior unless a caller contract update is explicitly justified.
- Ensure each partial failure path emits a consistent machine-readable status.

3. Resume/operator guard patch

- If evidence shows resume/operator status over-trusts manuscript existence, add the smallest guard needed.
- Keep companion telemetry clearly subordinate to DB/stage settlement truth.

4. Regression tests

- Add or update tests for each settlement state.
- Include one negative assertion that partial persistence is not considered fully settled.
- Keep tests focused and sequential.

5. Validation and closure

- Run targeted Stage4 shards.
- Run UTF-8 hygiene for touched text/code/docs.
- Run `ops_validator --strict`.
- Close the temp mirror only after implementation is complete and closure harness criteria are met.

## 9. Acceptance Criteria

- Every known Stage4 post-pass partial-success state has a named status.
- A fully settled PASS is distinguishable from a persisted manuscript row.
- Existing hard-incomplete behavior for metadata failure remains intact or is replaced by a stricter equivalent.
- Settlement packet and human-facing export failures remain observable.
- Resume/operator-facing surfaces do not silently promote partial settlement to full PASS.
- No broad feature work or provider-native sidecar work is introduced.
- No new production function enters `180+ LOC`.
- Any touched production function at `120+ LOC` is reviewed for bounded-shell versus extraction needs.

## 10. Verification Plan

Minimum targeted validation after implementation:

```powershell
python -m pytest tests/test_stage4_post_processor.py -q
python -m pytest tests/test_stage4_pass_artifact_contract.py -q
python -m pytest tests/test_stage4_orchestrator.py -q
python scripts/check_utf8_hygiene.py <touched files>
python scripts/ops_validator.py --strict
```

Optional follow-up validation if operator/API status surfaces are touched:

```powershell
python -m pytest tests/test_bridge_quality_summary.py tests/test_api_contract.py -q
python -m pytest tests/test_process_runner.py -q
```

Full-suite validation is not required by default and should not be run as one giant pass.

## 11. Guardrails

- Do not change Stage4 generation, retry strategy, or model/provider routing.
- Do not add Live API, Memory Bank, or other provider-native memory sidecars in this wave.
- Do not convert companion telemetry into durable authority.
- Do not rely on stdout/renderer status as proof of PASS settlement.
- Do not add schema migration unless a focused trace proves existing sinks are insufficient.
- Do not remove existing emergency manuscript dump behavior.
- Do not weaken metadata failure hard-incomplete behavior.
- Do not patch Korean/CJK text based on console rendering; use UTF-8 byte-level reads if encoding questions appear.

## 12. Temp Queue Notes

- temp status: completed
- temp mirror: `docs/temp/stage4-pass-settlement-authority-recheck-execution-ssot.md` removed after closure
- roadmap dependency: no roadmap required while this is the only active execution SSOT mirror
- cleanup condition: satisfied after implementation, validation, and this closure record

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue-state entry: not required for a single-item temp queue
- execution-start rule: re-run this document's 3-pass audit and confirm at least 95% confidence against current workspace state before patching code from this document

## 14. Document 3-Pass Audit

Pass 1 - Structure and scope:

- This is an execution SSOT, not a survey-only note.
- Canonical and temp mirror paths are explicit.
- Included/excluded surfaces are bounded.
- The work is maintenance/hardening, not a new feature.

Pass 2 - Evidence and consistency:

- Claims are tied to live-code line evidence and existing tests.
- The source survey is listed.
- Baseline dirty state acknowledges the untracked wave1 survey document.
- Resume drift is docs-only queue setup on the same commit; no production code drift before implementation.
- No live-run result is claimed.
- No schema change is pre-authorized.

Pass 3 - Execution and readability:

- Tranches are ordered from trace to minimal patch to verification.
- Acceptance criteria distinguish partial persistence from full PASS settlement.
- Side effects and rollback/resume risks are explicit.
- Temp queue behavior is explicit.

Estimated confidence:

- Execution-doc readiness confidence: `95%`

Reasons confidence is not higher:

- no fresh live Stage4 replay was performed
- no actual project DB artifact body was audited
- operator/API status surfaces were not expanded in this wave

## 15. Current Recommendation

Proceed with this item before opening lower-priority maintenance waves.

This is the best next maintenance target because it protects Stage4's core authority model: a future operator or resume path must never confuse "the manuscript row exists" with "the episode is fully settled and authoritative."

## 16. Realization Closure

Closure date: `2026-04-25`

Implemented scope:

- Added explicit Stage4 PASS settlement status payloads for `primary_db_failed`, `primary_persisted_meta_failed`, `settlement_packet_failed`, `human_export_failed`, and `fully_settled`.
- Persisted settlement status through `audit_event` and, when available, a non-visible `ui_events` structured status row.
- Kept `process_pass_result()` boolean compatibility while making partial settlement states inspectable.
- Restored `docs/2026-03-13/stage4-pass-artifact-contract.json` as the active v2 contract expected by the Stage4 artifact contract shard.

Complexity guardrail:

- `Stage4PostProcessor.process_pass_result()` remains a bounded shell around persistence and post-pass settlement.
- Post-change function length is `177` LOC by AST span, below the `180+` high-risk band.

Validation evidence:

- `python -m pytest tests/test_stage4_post_processor.py -q` -> `104 passed`
- `python -m pytest tests/test_stage4_pass_artifact_contract.py -q` -> `5 passed`
- `python -m pytest tests/test_stage4_orchestrator.py -q` -> `164 passed`
- `python scripts/check_utf8_hygiene.py modules/core/stage4_post_processor.py tests/test_stage4_post_processor.py tests/test_stage4_pass_artifact_contract.py docs/2026-03-13/stage4-pass-artifact-contract.json docs/2026-04-25/codebase-parallel-deep-survey-wave1-synthesis.md docs/2026-04-25/stage4-pass-settlement-authority-recheck-execution-ssot.md docs/temp/stage4-pass-settlement-authority-recheck-execution-ssot.md` -> pass
- `python scripts/ops_validator.py --strict` -> pass before temp mirror removal

Residual risks:

- No fresh live Stage4 replay was performed.
- Bridge/operator surfaces can now consume the new structured status, but this wave did not add new API display logic.

Closure result:

- Execution SSOT realized.
- Temp execution mirror may be removed.
