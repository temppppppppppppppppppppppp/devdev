# Current Pipeline Post-Settlement Truth Residuals Execution SSOT

Date: 2026-04-26
Status: active
Canonical Path: `docs/2026-04-26/current-pipeline-post-settlement-truth-residuals-execution-ssot.md`
Temp Mirror Path: `docs/temp/current-pipeline-post-settlement-truth-residuals-execution-ssot.md`
Commit State:
- Baseline Commit: `871713eab804d6ed6f8e2fb48a9f56dedff89dd7`
- Baseline Dirty Summary: clean
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: none
Source Survey Docs:
- interactive parallel deep-dive survey on 2026-04-26 after PR #40 merge
- `docs/2026-04-26/current-pipeline-residual-truth-locks-execution-ssot.md`
Evidence Artifacts:
- no separate raw evidence artifact was materialized; source paths and anchors are embedded below
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: current-pipeline-post-settlement-truth-residuals
  github_issue: 41
  status: in_progress
  queue_role: front_active
  roadmap_rank: 1
  depends_on: []
  tranches:
    - id: stage4-post-settlement-side-effect-containment
      title: Defer or contain Stage4 side effects until fully-settled truth exists
    - id: durable-truth-report-cross-checks
      title: Cross-check benchmark and stagewise truth reports against settled DB truth
    - id: pipeline-truth-lock-ci-coverage
      title: Add missing focused CI shards for current truth locks
    - id: director-authority-normalization
      title: Normalize downstream gate wording so Python blocks routing, not final narrative judgment
  verification_commands:
    - python -m pytest tests/test_stage4_post_processor.py -q
    - python -m pytest tests/test_stage4_orchestrator.py -k "settlement or completion" -q
    - python -m pytest tests/test_archive_benchmark_record.py tests/test_failure_analyzer.py -q
    - python -m pytest tests/test_stage4_context_builder.py tests/test_stage2_stage3_episode_boundary_guardrail.py -q
    - python -m pytest tests/test_direct_supervised_semantic_exit.py tests/test_run_stage2_direct_supervised.py tests/test_run_stage3_direct_supervised.py tests/test_run_stage4_direct_supervised.py -q
    - python -m pytest tests/test_main_a_boot_binding.py -q
    - python -m pytest tests/test_stage2_finalizer.py -q
    - python -m pytest tests/test_blueprint_patch_mode.py -q
    - python -m pytest tests/test_stage4_interview_round.py -q
    - python -m pytest tests/test_stage4_cw_false_miss_remediation.py -q
    - python scripts/ops_validator.py --strict
```

## 1. Intent

This document governs the next maintenance wave after the residual truth-lock queue was closed.

The previous wave made `fully_settled` the Stage4 completion authority and closed the active temp queue. A fresh parallel deep-dive found no P0, but it did find P1/P2 residuals where side effects, helper reports, or CI coverage can still make the current pipeline look safer or more complete than the settled authority proves. The goal is not new feature work. The goal is to keep the existing Stage2/3/4 pipeline from reintroducing stale truth, pre-settlement memory, or Python-owned final judgment.

## 2. Baseline Facts

- Local `main` matches `origin/main` at `871713eab804d6ed6f8e2fb48a9f56dedff89dd7`.
- `docs/temp/` has no active `*-execution-ssot.md` mirror before this document.
- `modules/core/stage4_post_processor.py` saves the primary manuscript DB row before local and post-pass side effects.
- `_run_pass_result_local_side_effects()` can update HUD state, reconcile capital, generate narrative summaries, and save tracker-derived DB sidecars before metadata, settlement packet, and human export are all settled.
- `_run_pass_result_post_pass_pipeline()` calls `_memorize_and_validate()` before `_collect_manager_and_build_delta()`.
- `modules/core/stage4_post_pass_runtime.py::_memorize_and_validate()` calls `ctx.memory.memorize_v20_episode(...)`.
- `modules/core/vec_memory.py::memorize_v20_episode()` commits vector memory and `episode_meta` rows immediately; rollback support exists through `delete_episodes_from()`, but the Stage4 pass-settlement path does not use it on later settlement failure.
- `.github/workflows/test.yml` includes `tests/test_stage4_post_processor.py`, but currently omits several focused tests that prove adjacent truth locks remain wired.

## 3. Scope

Included:
- Stage4 pass-result side-effect ordering after primary DB save and before `fully_settled`.
- Vector/session memory writes triggered by Stage4 post-pass runtime.
- Benchmark and stagewise truth/report consumers that can read stale JSONL, pass-rate, or artifact sinks without settled DB cross-checks.
- Focused CI coverage for existing truth-lock tests that are not yet part of the PR gate.
- Authority wording and routing where Python helpers mutate or appear to own final PASS/REJECT after Director review.

Excluded:
- New product features.
- Desktop UX, packaging, or app shell work.
- Narrative material-side WorkGuard/TR/BI generation.
- Broad refactors unrelated to truth settlement, side-effect containment, or CI gate coverage.
- Any change that lets Python decide narrative quality PASS/REJECT without Director/LLM authority.

## 4. Pass 1. Inventory Summary

Open severity inventory:
- P1: Stage4 can persist vector memory after primary manuscript save but before manager metadata, settlement packet, and human export are fully settled.
- P1: CI does not gate several already-existing truth-lock tests, including Stage4 completion truth, stale source-lineage suppression, direct runner archive wiring, and legacy quad cache keep-dead behavior.
- P1/P2: Benchmark archive and stagewise truth reports can infer completion from stale or non-authoritative sinks unless they cross-check settled DB truth.
- P1/P2: Stage4 CoVe/strong-advisory and Stage2/3 threshold helpers can mutate Director PASS-like outcomes, creating split authority wording even when their safety intent is valid.
- P2/P3: Some diagnostic fields still use Python truncation in status-adjacent paths; touched DB diagnostic fields must not truncate `TEXT` evidence.

Main code surfaces:
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/vec_memory.py`
- `scripts/archive_benchmark_record.py`
- `modules/core/stagewise_manuscript_truth_report.py`
- `.github/workflows/test.yml`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/stage3_validation_boundary.py`

Main test surfaces:
- `tests/test_stage4_post_processor.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_archive_benchmark_record.py`
- `tests/test_failure_analyzer.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage2_stage3_episode_boundary_guardrail.py`
- `tests/test_direct_supervised_semantic_exit.py`
- `tests/test_run_stage2_direct_supervised.py`
- `tests/test_run_stage3_direct_supervised.py`
- `tests/test_run_stage4_direct_supervised.py`
- `tests/test_main_a_boot_binding.py`

## 5. Pass 2. Semantic Classification

Class A - settlement authority:
- `fully_settled` remains the only authoritative Stage4 completed PASS settlement state.
- Primary manuscript persistence alone is not enough to publish memory, operator summaries, benchmark completion, or final report truth as completed.

Class B - side-effect containment:
- Side effects that can influence future generation or operator belief must either wait until `fully_settled` or be explicitly rollbackable/demoted when later settlement fails.
- Vector memory is high-risk because it is retrieved by later context builders and Director memory context.

Class C - evidence consumers:
- Report/archive scripts may collect and format evidence, but they must not overstate completion from stale JSONL, pass-rate, or artifact-only evidence when settled DB truth is absent or contradicted.

Class D - authority normalization:
- Python may collect hard invariant evidence and may block automatic routing until Director/LLM review.
- Python must not be framed as the final narrative PASS/REJECT judge.
- The deceased-character invariant remains absolute: acting/speaking by `deceased=True` or dead-status characters must be rejected, but the final quality authority should remain Director/LLM-owned rather than regex-owned.

## 6. Side-Effect Map

file writes / artifacts:
- Stage4 settlement packet and human-facing manuscript export are part of `fully_settled`.
- Benchmark archive outputs and stagewise truth reports must identify stale, rolled-back, or non-settled sources instead of presenting them as durable completion.

DB / schema / transaction boundaries:
- Stage4 primary manuscript DB save currently precedes local side effects and memory writes.
- Vector memory writes commit independently through `vec_memory.py`.
- Touched DB diagnostic `TEXT` fields must preserve full diagnostic text and avoid Python slicing.
- Existing DB transaction ownership must not be weakened.

JSONL / log / audit sinks:
- `episode_production.jsonl`, pass-rate files, benchmark archive records, and stagewise truth reports are evidence sinks, not final settlement authority.
- If these sinks are used, they must be cross-checked against settled DB truth or labeled advisory/stale.

console / UI / operator output:
- Operator-facing status should distinguish primary DB saved, metadata failed, packet failed, export failed, and fully settled.
- Console rendering is not encoding evidence; byte-level UTF-8 readback remains authoritative for encoding claims.

rollback / recovery / retry:
- If vector memory remains pre-settlement, later failure must remove or demote the episode memory for that `ep_num`.
- Prefer deferring future-influencing side effects until after `fully_settled` over adding complex rollback.

cache / global state:
- HUD, narrative summaries, character voice, foreshadow, emotion trackers, and vector memory can influence later runtime behavior or operator interpretation.
- Legacy cache helpers should remain dead, deleted, or CI-guarded with explicit lineage semantics.

bootstrap fallback / config-env mutation:
- Not directly applicable for Stage4 settlement ordering.
- Direct supervised runners remain in scope only for CI/archive semantic-exit coverage.

## 7. Realization Architecture

Use small sequential tranches.

1. Stage4 side-effect containment first, because it affects future context and memory truth.
2. Durable truth report cross-checks second, because they should consume the corrected settlement semantics.
3. CI coverage third, so the current truth locks stay wired in GitHub Actions.
4. Director authority normalization fourth, because it is semantically important but wider and should not block the concrete settlement containment fix.

Implementation constraints:
- Do not create a new runtime truth authority beside `fully_settled`.
- Do not turn Python regex or numeric thresholds into final narrative judgment.
- If a Python guard detects a hard invariant breach, route it as settlement-blocking evidence requiring Director/LLM-owned rejection or correction, not as autonomous quality judgment.
- Keep pytest shards focused and sequential.

## 8. Execution Tranches

1. `stage4-post-settlement-side-effect-containment`
   - Add a regression proving `ctx.memory.memorize_v20_episode()` is not called when later metadata/settlement failure prevents `fully_settled`.
   - Delay or rollback vector memory writes until after settlement packet and human export succeed.
   - Audit `_run_pass_result_local_side_effects()` and defer future-influencing side effects that should not run before `fully_settled`.
   - Preserve primary DB failure emergency dump behavior.

2. `durable-truth-report-cross-checks`
   - Make benchmark archive completion status and stagewise truth reports cross-check settled DB truth or emit explicit stale/advisory status.
   - Add tests where stale JSONL/pass-rate/artifact evidence exists after rollback or reset and must not become completed truth.
   - Ensure touched diagnostic DB fields do not slice `TEXT` evidence.

3. `pipeline-truth-lock-ci-coverage`
   - Add missing focused truth-lock tests to `.github/workflows/test.yml` without exploding CI scope.
   - At minimum cover Stage4 settlement completion, stale source-lineage suppression, direct runner archive wiring, and legacy quad cache keep-dead behavior.
   - Keep CI additions in focused shards to respect memory constraints.

4. `director-authority-normalization`
   - Inventory downstream helpers that mutate PASS/PASS_WITH_FIX/REJECT after Director review.
   - Separate absolute invariant blocking from Python-owned final judgment wording.
   - Add focused tests that prove Python warnings/gates are surfaced as runtime routing gates with Director/LLM final judgment authority instead of silently owning narrative PASS/REJECT.

## 9. Acceptance Criteria

- Stage4 vector memory is not persisted for an episode unless the pass result reaches `fully_settled`, or it is reliably removed/demoted before returning failure.
- Stage4 future-influencing side effects are explicitly classified as pre-settlement-safe, post-settlement-only, or rollbackable.
- Benchmark and stagewise truth reports cannot mark stale/rolled-back/non-settled evidence as completed truth without a settled DB cross-check.
- CI gates the focused regression tests for the current pipeline truth locks.
- Authority wording and behavior preserve Director/LLM final judgment while still enforcing absolute hard invariants.
- `python scripts/ops_validator.py --strict` passes with this temp mirror active.

## 10. Verification Plan

- `python -m pytest tests/test_stage4_post_processor.py -q`
- `python -m pytest tests/test_stage4_orchestrator.py -k "settlement or completion" -q`
- `python -m pytest tests/test_archive_benchmark_record.py tests/test_failure_analyzer.py -q`
- `python -m pytest tests/test_stage4_context_builder.py tests/test_stage2_stage3_episode_boundary_guardrail.py -q`
- `python -m pytest tests/test_direct_supervised_semantic_exit.py tests/test_run_stage2_direct_supervised.py tests/test_run_stage3_direct_supervised.py tests/test_run_stage4_direct_supervised.py -q`
- `python -m pytest tests/test_main_a_boot_binding.py -q`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Python collects, formats, blocks unsafe routing, and records evidence; Python does not own final narrative quality judgment.
- Director remains the final quality decision authority.
- `deceased=True` or dead-status characters acting/speaking remains an absolute reject condition, but the enforcement path should not be framed as regex-owned quality judgment.
- Touched diagnostic DB `TEXT` paths must not use Python truncation.
- Do not patch based on console mojibake; use byte-level UTF-8 readback for encoding claims.
- Do not start code modification from this document after drift unless the document is re-audited to at least 95% confidence.

## 12. Temp Queue Notes

- temp status: active-local-implementation-complete
- cleanup condition: remove `docs/temp/current-pipeline-post-settlement-truth-residuals-execution-ssot.md` after all tranches are implemented, verified, merged, and canonical status is updated to `closed`
- roadmap dependency: none; this is the only active execution SSOT at creation time

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: not required for a single active execution SSOT
- execution-start rule: re-run this document through the 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. Execution Progress

Completed in current realization pass:
- `stage4-post-settlement-side-effect-containment`: implemented. Stage4 local side effects and vector memory now run only after `fully_settled` status is emitted.
- `durable-truth-report-cross-checks`: implemented for benchmark archive status and stagewise manuscript truth reporting. Both now cross-check Stage4 completed claims against settled `project_data.db` manuscript truth when DB evidence is available or required.
- `pipeline-truth-lock-ci-coverage`: implemented. GitHub Actions now includes a separate pipeline truth-lock regression shard.
- `director-authority-normalization`: implemented as metadata/observability normalization without behavior-flipping. Stage2 and Stage3 quality gates now stamp Director/LLM final-judgment authority plus Python runtime routing-gate authority. Stage4 downstream override gate semantics, verdict layers, DB selection payloads, and episode JSONL logs now carry the same authority split. Operator-facing `force/downgrade/forced REJECT` wording in touched Stage2/3/4 quality-gate surfaces was normalized to runtime REJECT-route wording.

Pending:
- No remaining implementation tranche in this execution SSOT. The temp mirror remains active until the local patch is committed, pushed, reviewed, merged, and the closure harness removes the temp copy.

Validation completed:
- `python -m pytest tests/test_stage4_post_processor.py -q`: passed, 108 tests.
- `python -m pytest tests/test_stage4_orchestrator.py -k "settlement or completion" -q`: passed, 2 tests.
- `python -m pytest tests/test_archive_benchmark_record.py tests/test_stagewise_manuscript_truth_report.py -q`: passed, 10 tests.
- `python -m pytest -q tests/test_stage4_context_builder.py tests/test_stage2_stage3_episode_boundary_guardrail.py tests/test_run_stage2_direct_supervised.py tests/test_run_stage3_direct_supervised.py tests/test_run_stage4_direct_supervised.py tests/test_main_a_boot_binding.py tests/test_stagewise_manuscript_truth_report.py`: passed, 162 tests.
- `python -m pytest tests/test_stage4_interview_round.py -q`: passed, 322 tests.
- `python -m pytest tests/test_stage4_cw_false_miss_remediation.py -q`: passed, 7 tests.
- `python -m pytest tests/test_stage2_finalizer.py -q`: passed, 77 tests.
- `python -m pytest tests/test_blueprint_patch_mode.py -q`: passed, 93 tests.
- `python -m pytest tests/test_db_manager.py -k "gate_semantics or advisory" -q`: passed, 1 test.
- `python -m py_compile modules/core/stage2_finalizer.py modules/domain/agents/stage3_validation_boundary.py modules/core/stage4_interview_round.py modules/core/stage4_post_processor.py modules/core/stagewise_manuscript_truth_report.py scripts/archive_benchmark_record.py`: passed.
- `git diff --check`: passed.
- `python scripts/ops_validator.py --strict`: passed.

## 15. Document 3-Pass Audit

Pass 1 - structure and scope:
- PASS. The document is an execution SSOT, uses dated canonical and temp mirror paths, includes intent, scope, side-effect map, tranches, acceptance criteria, verification, guardrails, and cleanup notes.

Pass 2 - evidence and consistency:
- PASS. Claims are bounded to inspected source paths and the post-PR #40 baseline commit. No separate raw artifact is claimed. The document does not claim a P0 and does not overstate static survey findings as live-run proof.

Pass 3 - execution and readability:
- PASS. The execution order is sequential and starts with the smallest high-impact containment tranche. Broader authority normalization is intentionally last to avoid blocking concrete settlement fixes.

Confidence gate:
- Estimated confidence: 96%.
- Rationale: the strongest original claim, Stage4 memory before full settlement, is directly supported by local code inspection and regression coverage across `stage4_post_processor.py`, `stage4_post_pass_runtime.py`, and `vec_memory.py`. The authority-normalization tranche is deliberately metadata/observability-only, with behavior-flipping refactors avoided to preserve existing repair-loop contracts.
