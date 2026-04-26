# Current Pipeline Residual Truth Locks Execution SSOT

Date: 2026-04-26
Status: closed
Canonical Path: `docs/2026-04-26/current-pipeline-residual-truth-locks-execution-ssot.md`
Temp Mirror Path: removed after closure; former path was `docs/temp/current-pipeline-residual-truth-locks-execution-ssot.md`
Commit State:
- Baseline Commit: `b816e76004d7b3a84f3ce5736702b4888f6521c4`
- Baseline Dirty Summary: clean
- Resume Commit: `45ccc7685a01aa0a37ffde380c346c5d14473730`
- Resume Drift Summary: main includes PR #36 through PR #39; this closure update only adds CI coverage and canonical queue cleanup.
Source Survey Docs:
- `docs/2026-04-26/current-pipeline-truth-locks-execution-ssot.md`
- post-merge interactive residual survey on `main` at `b816e76004d7b3a84f3ce5736702b4888f6521c4`
Evidence Artifacts:
- no separate raw evidence artifact was materialized; source paths and line anchors are embedded below
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: current-pipeline-residual-truth-locks
  status: closed
  queue_role: closed
  roadmap_rank: 1
  depends_on:
    - docs/2026-04-26/current-pipeline-truth-locks-execution-ssot.md
  tranches:
    - id: stage4-post-pass-exception-fail-closed
      title: Fail closed on Stage4 post-pass manager exceptions
    - id: stage2-lineageless-cache-fail-closed
      title: Refuse lineageless cached Stage2 arcs instead of blessing stale cache
    - id: stage4-settlement-side-effect-containment
      title: Contain post-pass side effects when primary metadata settlement fails
    - id: direct-runner-archive-exit-truth
      title: Make direct runner shell success depend on archive success when archive is enabled
    - id: benchmark-archive-reproducibility-truth
      title: Make benchmark index truth reproducible or explicitly external
    - id: legacy-cache-lineage-auditability
      title: Make legacy context-cache lineage bypasses auditable
    - id: doc-and-ci-consistency-cleanup
      title: Close stale execution status wording and add Stage4 post-pass CI coverage
  verification_commands:
    - python -m pytest tests/test_stage4_post_processor.py -q
    - python -m pytest tests/test_stage4_post_processor.py -k "meta_save_failed or settlement or collect_manager" -q
    - python -m pytest tests/test_stage2_orchestrator.py -k "bootstrap_stage2_arc_pipeline" -q
    - python -m pytest tests/test_direct_supervised_semantic_exit.py tests/test_run_stage2_direct_supervised.py tests/test_run_stage3_direct_supervised.py tests/test_run_stage4_direct_supervised.py -q
    - python -m pytest tests/test_archive_benchmark_record.py tests/test_failure_analyzer.py -q
    - python scripts/ops_validator.py --strict
```

## 1. Intent

This document governs the next maintenance wave after PR #35 was merged into `main`.

The previous truth-lock wave closed many current pipeline issues, but the post-merge residual survey found that a few runtime paths can still make the system overstate truth. The goal is not new features. The goal is to make Stage2/3/4 runtime evidence fail closed when proof is missing, stale, or partially persisted.

## 2. Baseline Facts

- Local `main` matched `origin/main` at `b816e76004d7b3a84f3ce5736702b4888f6521c4`.
- `git status -sb` was clean before this execution SSOT was prepared.
- `docs/temp/` had no active `*-execution-ssot.md` mirror before this document.
- `python scripts/ops_validator.py --strict` passed during the residual survey before this document.
- Prior closed SSOT claimed Stage4 settlement, source-lineage gates, artifact truth, direct runner semantic exits, and context-cache lineage cleanup were realized.
- Residual survey found that those locks are partially realized but not complete across all current-pipeline paths.

## 3. Scope

Included:
- Stage4 pass settlement and post-pass manager exception handling.
- Stage2 cached arcs source-lineage handling.
- Stage3 and Stage4 downstream behavior when Stage2 arcs have missing or stale source lineage.
- Direct supervised Stage2/3/4 shell exit semantics around benchmark archive failure.
- Benchmark archive/index reproducibility.
- Context-cache lineage auditability where legacy cache names bypass the newer `BaseAgent` lineage model.
- Focused tests and CI coverage for the above.

Excluded:
- New product features.
- Desktop UX or packaging work.
- Narrative material-side WorkGuard/TR/BI generation.
- Broad complexity refactors unless they are needed to land the truth locks safely.
- External advisory implementation.

## 4. Pass 1. Inventory Summary

Runtime truth candidates:
- Stage4 post-pass exception path: `modules/core/stage4_post_pass_runtime.py`.
- Stage4 settlement status path: `modules/core/stage4_post_processor.py`.
- Stage2 source-lineage gate: `modules/core/stage0_handoff.py`, `modules/core/stage2_orchestrator.py`.
- Stage3/4 downstream source-lineage consumers: `modules/core/stage3_orchestrator.py`, `modules/core/stage4_context_packets.py`, `modules/core/stage4_orchestrator.py`.
- Direct runners: `scripts/run_stage2_direct_supervised.py`, `scripts/run_stage3_direct_supervised.py`, `scripts/run_stage4_direct_supervised.py`, `scripts/direct_supervised_semantic_exit.py`.
- Benchmark archive/index: `scripts/archive_benchmark_record.py`, `benchmarks/benchmark_index.csv`, `benchmarks/.gitignore`, `benchmarks/README.md`.
- Context-cache lineage: `modules/domain/agents/base_agent.py`, `main_a.py`, legacy agent cache-name paths.

Open severity inventory:
- P0: Stage4 post-pass manager exceptions can be swallowed while `meta_save_failed` remains false.
- P0/P1: Cached Stage2 arcs with no saved source-lineage can be accepted and then stamped with the current plot-roadmap lineage.
- P1: Benchmark index rows are not reproducible from repo state because archived record roots and DB snapshots are ignored and absent locally.
- P1/P2: Artifact proof remains partial for archive-durable evidence; full artifacts are not copied by default.
- P2: Normal direct supervised runners can return shell success even when benchmark archiving reports error.
- P2: Legacy context caches and bypasses are not fully DB-auditable with provider/auth/content lineage.
- P2/P3: Prior SSOT closure text still contains stale temp-mirror/internal status wording.

## 5. Pass 2. Semantic Classification

Class A - fail-closed truth locks:
- Stage4 must not emit `fully_settled` when primary post-pass manager work throws before durable metadata proof is complete.
- Stage2 must not treat lineageless cached arcs as fresh proof when cached arcs exist.

Class B - evidence durability and observability:
- Direct supervised shell success must reflect archive failure when archive is part of the run contract.
- Benchmark index rows must either point to available durable evidence or state that their backing artifacts are external/non-reproducible.
- Context-cache bypasses must be observable enough to explain stale-lineage fallback behavior.

Class C - cleanup and consistency:
- Prior SSOT closure/status wording should be corrected after active implementation is complete.
- PASS_WITH_FIX analytics and strong-advisory authority wording need bounded follow-up, but they should not block the two P0 fixes unless implementation proves they are coupled.

## 6. Side-Effect Map

file writes / artifacts:
- Stage4 settlement packet and human-facing manuscript export must remain authoritative only after post-pass primary metadata succeeds.
- Artifact snapshot paths may need session or run identifiers in a later tranche if overwrite risk is addressed.
- Benchmark archives may need either a reproducible small evidence bundle or explicit external evidence status.

DB / schema / transaction boundaries:
- `stage_attempts` demotion is currently best-effort. If touched, it must preserve full reason text and must not use Python truncation.
- `stage2_arcs_source_lineage` persistence must be checked when it controls cache reuse.
- Existing transaction guardrails in `DBManager` must not be weakened.

JSONL / log / audit sinks:
- `episode_production.jsonl` and `pass_rate_monitor.json` can currently contain pre-settlement PASS-like records before settlement failure demotion.
- Settlement failure should emit a clear audit/UI status and not leave downstream consumers guessing from mixed sinks.

console / UI / operator output:
- Operator-facing messages should distinguish blocked settlement from soft sidecar failures.
- Console output must not be used as encoding evidence; byte-level UTF-8 readback remains authoritative.

rollback / recovery / retry:
- Stage4 post-pass failure should return false and mark settlement failure before completion.
- Stage2 lineageless cached arcs should produce a clear refusal or explicit rebuild path instead of silently continuing.

cache / global state:
- Missing source lineage is not proof of freshness.
- Legacy cache names must not bypass model/provider/content lineage without auditable fallback.

bootstrap fallback / config-env mutation:
- Direct supervised scripts can keep their current env behavior, but archive failure should affect exit semantics when archive is enabled.

## 7. Realization Architecture

Use a strict, small-tranche order:

1. Fix Stage4 post-pass exception fail-closed behavior before touching downstream cleanup.
2. Fix Stage2 lineageless cached arcs fail-closed behavior before Stage3/4 lineage follow-up.
3. Add containment for primary metadata failure side effects only after the basic Stage4 fail-closed regression is green.
4. Align direct runner archive exit semantics.
5. Decide benchmark archive reproducibility policy.
6. Improve context-cache bypass auditability.

Implementation constraints:
- Python may collect, compare, and route already-authored evidence.
- Python must not decide narrative PASS/REJECT quality.
- Director remains final quality authority.
- `fully_settled` remains the only authoritative Stage4 completed PASS settlement.
- Do not truncate DB diagnostic reason fields in touched code.
- Prefer focused tests and sequential pytest shards.

## 8. Execution Tranches

1. `stage4-post-pass-exception-fail-closed`
   - Make broad exceptions in `_collect_manager_and_build_delta()` return `meta_save_failed=True` or a stronger settlement-blocking flag.
   - Add a regression where manager delta collection raises and `process_pass_result()` returns false instead of `fully_settled`.
   - Ensure settlement status marks the attempt as failed when an attempt key is available.

2. `stage2-lineageless-cache-fail-closed`
   - Change cached arcs plus missing source-lineage from "ready" to "not ready" unless a deliberate migration/backfill command is used.
   - Check the boolean result of lineage persistence when it is allowed.
   - Add regression coverage for cached arcs with missing lineage.

3. `stage4-settlement-side-effect-containment`
   - Stop or isolate post-pass side effects after primary `save_episode_bible` failure.
   - Ensure WorldState/FactLedger/state logs do not become authoritative for a non-settled PASS.
   - Preserve clear soft-failure behavior for non-primary sidecars.

4. `direct-runner-archive-exit-truth`
   - Update normal direct supervised semantic exit so archive `status: error` returns non-zero when archive is enabled.
   - Keep `--skip-benchmark-archive` semantics explicit for Stage4.
   - Add tests covering success plus archive error.

5. `benchmark-archive-reproducibility-truth`
   - Decide whether benchmark records are repo-local evidence or external/local-only evidence.
   - If repo-local, persist minimal reproducible archive artifacts or compact manifests.
   - If external/local-only, make `benchmark_index.csv` expose non-reproducible status instead of implying local proof.

6. `legacy-cache-lineage-auditability`
   - Add DB/cache-attempt observability for stale or missing cache lineage bypasses.
   - Avoid making old cache names authoritative without provider/model/content proof.

7. `doc-and-ci-consistency-cleanup`
   - Correct stale status wording in the prior SSOT after implementation.
   - Add or adjust CI shards for the newly locked regressions.

## 9. Acceptance Criteria

- Stage4 post-pass manager exception cannot produce a `fully_settled` status.
- Stage4 failed primary metadata settlement does not leave authoritative completion proof.
- Stage2 cached arcs with missing source lineage do not silently pass as fresh.
- Direct supervised exit code is non-zero when archive-enabled success payload contains archive `status: error`.
- Benchmark archive/index status is honest about whether backing bytes are present in repo.
- New or touched DB diagnostic fields preserve full text, without Python truncation.
- Focused tests pass sequentially.
- `python scripts/ops_validator.py --strict` passes after temp mirror creation and after implementation closure.

## 10. Verification Plan

Minimum focused shards:
- `python -m pytest tests/test_stage4_post_processor.py -k "meta_save_failed or settlement or collect_manager" -q`
- `python -m pytest tests/test_stage2_orchestrator.py -k "bootstrap_stage2_arc_pipeline" -q`
- `python -m pytest tests/test_direct_supervised_semantic_exit.py tests/test_run_stage2_direct_supervised.py tests/test_run_stage3_direct_supervised.py tests/test_run_stage4_direct_supervised.py -q`
- `python -m pytest tests/test_archive_benchmark_record.py tests/test_failure_analyzer.py -q`

Static and operational checks:
- `python -m ruff check <touched files>`
- `python -m py_compile <touched python files>`
- `python scripts/check_utf8_hygiene.py <touched text files>`
- `git diff --check`
- `python scripts/ops_validator.py --strict`

## 11. Guardrails

- Do not let a convenience sink outrank `stage_attempts` plus settlement proof.
- Do not let missing lineage mean fresh lineage.
- Do not introduce Python-based narrative quality judgment.
- Do not truncate DB diagnostic text in touched code.
- Do not patch based on PowerShell mojibake-looking output without UTF-8 byte readback.
- Do not start broad refactors while P0 fail-closed paths are still open.

## 12. Temp Queue Notes

- temp status: closed; execution mirror removed after this canonical closure update.
- cleanup condition: satisfied after all accepted tranches were implemented, verified, committed or explicitly parked, and closure notes were added to this canonical SSOT.
- roadmap dependency: no separate aggregate roadmap is required while this is the only active execution SSOT in `docs/temp/`.

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document.

## 14. Document 3-Pass Audit

Pass 1 - structure and scope:
- Document type is an execution SSOT, not a survey.
- Canonical and temp paths follow workspace rules.
- Scope is bounded to current pipeline truth locks and excludes desktop/material-side work.
- Side-effect categories are explicitly covered.

Pass 2 - evidence and consistency:
- Baseline commit and clean state are recorded.
- Findings are bounded to inspected source paths and prior SSOT claims.
- P0 items are prioritized ahead of archive/cache cleanup.
- No claim depends on console text rendering as encoding evidence.

Pass 3 - execution and readability:
- Tranches are ordered so fail-closed runtime truth comes before cleanup.
- Acceptance criteria are testable.
- Verification plan is sequential and memory-conservative.
- Temp cleanup and execution-start re-audit rules are explicit.

Estimated confidence: 96%.

## 15. Implementation Progress

Status: closed.

Completed tranches:
- `stage4-post-pass-exception-fail-closed`: `_collect_manager_and_build_delta()` now fails closed with `meta_save_failed=True` when the manager/post-pass delta path raises, and touched operator output no longer truncates the exception text.
- `stage2-lineageless-cache-fail-closed`: cached Stage2 arcs with missing source-lineage are refused instead of being stamped with the current plot-roadmap lineage; initial lineage persistence is now checked.
- `direct-runner-archive-exit-truth`: direct supervised semantic exit now returns non-zero when archive-enabled payloads contain `benchmark_archive.status` other than `ok`.
- `stage4-settlement-side-effect-containment`: `_persist_manager_delta_outputs()` now stops before WorldState, causal-link, state-log, karma, summary, numeric-authority, and contract-signal side effects when the primary `save_episode_bible` write fails; the audit payload preserves the full exception text.
- `benchmark-archive-reproducibility-truth`: benchmark manifests and index rows now mark archive backing evidence as `local_ignored_snapshot` / `local_only_non_reproducible`, with README guidance that ignored snapshot directories are local-only unless separately exported or tracked.
- `legacy-cache-lineage-auditability`: cached-context missing/stale lineage bypasses now write `context_cache_attempts` rows with `cache_outcome=bypassed` and a specific lineage reason instead of only emitting a warning before direct fallback.
- `doc-and-ci-consistency-cleanup`: CI focused PR gate now includes the full Stage4 post-processor regression file, and this canonical SSOT no longer leaves an active temp queue behind.

Focused verification completed so far:
- `python -m pytest tests/test_stage4_post_processor.py -q`: 107 passed.
- `python -m pytest tests/test_stage4_post_processor.py -k "collect_manager_and_build_delta_fails_closed_on_manager_exception or returns_false_and_logs_when_meta_save_fails or returns_true_on_success or settlement_failure_demotes" -q`: 4 passed.
- `python -m pytest tests/test_stage4_post_processor.py -k "persist_manager_delta_outputs_stops_side_effects_when_bible_save_fails or persist_manager_delta_outputs_saves_bible_and_delegates_side_effect_sinks or returns_false_and_logs_when_meta_save_fails or collect_manager_and_build_delta_fails_closed_on_manager_exception" -q`: 4 passed.
- `python -m pytest tests/test_stage2_orchestrator.py -k "bootstrap_stage2_arc_pipeline" -q`: 5 passed.
- `python -m pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -k "stale_cached_arc_lineage" -q`: 1 passed.
- `python -m pytest tests/test_stage4_context_builder.py -k "stale" -q`: 1 passed.
- `python -m pytest tests/test_direct_supervised_semantic_exit.py tests/test_run_stage2_direct_supervised.py tests/test_run_stage3_direct_supervised.py tests/test_run_stage4_direct_supervised.py -q`: 8 passed.
- `python -m pytest tests/test_archive_benchmark_record.py tests/test_failure_analyzer.py -q`: 55 passed.
- `python -m pytest tests/test_base_agent.py -k "cached_context_missing_lineage_bypasses_cache or cached_context_stale_model_lineage_bypasses_cache or cached_context_success_logs_cache_lineage or cached_context_failure_evicts_cache_by_name_and_logs_lineage or context_cache_hit_logs_direct_attempt" -q`: 5 passed.

Static and hygiene verification completed:
- `python scripts/check_utf8_hygiene.py .github/workflows/test.yml docs/2026-04-26/current-pipeline-residual-truth-locks-execution-ssot.md`: passed.
- `python -m ruff check modules/core/stage4_post_pass_runtime.py modules/core/stage0_handoff.py modules/core/stage2_orchestrator.py scripts/direct_supervised_semantic_exit.py tests/test_stage4_post_processor.py tests/test_stage2_orchestrator.py tests/test_direct_supervised_semantic_exit.py`: passed.
- `python -m ruff check modules/core/stage4_post_pass_runtime.py tests/test_stage4_post_processor.py`: passed.
- `python -m ruff check scripts/archive_benchmark_record.py tests/test_archive_benchmark_record.py`: passed.
- `python -m ruff check modules/domain/agents/base_agent.py tests/test_base_agent.py`: passed.
- `python -m py_compile modules/core/stage4_post_pass_runtime.py modules/core/stage0_handoff.py modules/core/stage2_orchestrator.py scripts/direct_supervised_semantic_exit.py tests/test_stage4_post_processor.py tests/test_stage2_orchestrator.py tests/test_direct_supervised_semantic_exit.py`: passed.
- `python -m py_compile modules/core/stage4_post_pass_runtime.py tests/test_stage4_post_processor.py`: passed.
- `python -m py_compile scripts/archive_benchmark_record.py tests/test_archive_benchmark_record.py`: passed.
- `python -m py_compile modules/domain/agents/base_agent.py tests/test_base_agent.py`: passed.
- `python scripts/check_utf8_hygiene.py <touched files>`: passed.

Complexity recount:
- `modules/core/stage4_post_pass_runtime.py`: touched `_collect_manager_and_build_delta` is 138 LOC, classified as bounded post-pass orchestration shell; file 180+ function count remains 0.
- `modules/core/stage0_handoff.py`: touched `cached_arcs_source_lineage_matches` is 13 LOC; 120+ and 180+ function counts remain 0.
- `modules/core/stage2_orchestrator.py`: touched `_save_stage2_arcs_source_lineage` is 10 LOC and `_stage2_cached_arcs_lineage_ready` is 19 LOC; file 180+ function count remains 0.
- `scripts/direct_supervised_semantic_exit.py`: touched functions are 5 LOC each; 120+ and 180+ function counts remain 0.
- `modules/domain/agents/base_agent.py`: touched `_context_cache_lineage_bypass_reason` is 13 LOC, `_log_context_cache_lineage_bypass` is 34 LOC, `_fallback_after_context_cache_lineage_bypass` is 28 LOC, and `_ask_with_cached_context` is 177 LOC; file 180+ function count remains at the pre-change count of 1.

Remaining queue:
- none.

Closure update 3-pass audit:
- Pass 1 - structure/scope: update remains inside the canonical execution SSOT, marks the execution state closed, and records the temp-mirror cleanup policy.
- Pass 2 - evidence/consistency: all accepted runtime tranches are backed by focused pytest, static, hygiene, and queue-validation evidence; the final CI cleanup is backed by the full local Stage4 post-processor shard and the workflow diff.
- Pass 3 - execution/readability: the active queue is empty, residual scope is explicit, and the temp mirror is no longer presented as an active execution artifact.

Estimated confidence after closure update: 97%.

## 16. Closure Summary

Closure state:
- closed after realizing the accepted residual truth-lock tranches and adding CI coverage for the Stage4 post-pass regression surface.
- temp execution mirror removed in the same closure change; no aggregate roadmap was required because this was the only active execution SSOT.

Residual risk:
- no remaining active item is governed by this SSOT.
- future broad surveys may still find separate pipeline hardening candidates, but they should start from a new execution doc rather than reopening this queue.
