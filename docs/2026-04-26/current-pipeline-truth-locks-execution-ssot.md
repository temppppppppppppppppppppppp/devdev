# Current Pipeline Truth Locks Execution SSOT

Date: 2026-04-26
Status: completed
Canonical Path: `docs/2026-04-26/current-pipeline-truth-locks-execution-ssot.md`
Temp Mirror Path: `docs/temp/current-pipeline-truth-locks-execution-ssot.md`
Commit State:
- Baseline Commit: `6f930a28b2b0b4fad00e51bc569a282c6af0b393`
- Baseline Dirty Summary: `clean`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none; live evidence rechecked before save`
Source Survey Docs: live current-pipeline parallel deep-dive synthesis plus local recheck on 2026-04-26; no separate survey doc saved
Evidence Artifacts: inline live-code evidence in this document
Side-Effect Coverage: covered

## 0. Execution Metadata Block

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: current-pipeline-truth-locks
  status: completed
  queue_role: historical_backing
  roadmap_rank: 1
  depends_on: []
  tranches:
    - id: stage4-settlement-complete-truth
      title: Lock Stage4 PASS settlement and completion truth
    - id: stage2-exhausted-arc-retry-contract
      title: Preserve Stage2 exhausted-arc retry semantics
    - id: stage4-hydration-session-freshness
      title: Scope Stage4 persisted previous_attempt hydration to fresh session truth
    - id: stage0-stage234-source-lineage-cache-gate
      title: Gate Stage2/3/4 cached material against Stage0 source lineage
    - id: stage234-artifact-proof-benchmark-truth
      title: Recompute artifact proof truth and stop false benchmark completion
    - id: direct-supervised-runner-semantic-exit-ci
      title: Make direct supervised runner shell exits and CI coverage semantic
    - id: secondary-pipeline-truth-sweep
      title: Resolve remaining P2/P3 pipeline truth gaps
  verification_commands:
    - python -m pytest tests/test_stage4_orchestrator.py tests/test_stage4_post_processor.py tests/test_stage4_interview_round.py
    - python -m pytest tests/test_stage2_orchestrator.py
    - python -m pytest tests/test_stage4_canary_tools.py tests/test_failure_analyzer.py
    - python scripts/check_utf8_hygiene.py docs/2026-04-26/current-pipeline-truth-locks-execution-ssot.md docs/temp/current-pipeline-truth-locks-execution-ssot.md
    - python scripts/ops_validator.py --strict
```

## 1. Intent

This execution SSOT controls the sequential remediation of all currently confirmed pipeline-truth findings from the 2026-04-26 deep dive.

The goal is not to add new product features. The goal is to make the existing Stage0 -> Stage2 -> Stage3 -> Stage4 pipeline harder to lie to itself about runtime truth:

- a Stage4 PASS is not authoritative until post-pass settlement is fully settled;
- Stage2 retry choices must not be silently converted to next;
- persisted retry memory must not leak across fresh sessions;
- cached arcs and downstream contexts must be tied to their source material lineage;
- artifact, proof, and benchmark records must reflect actual bytes and actual target completion;
- shell exits and CI must fail when semantic pipeline proof fails.

## 2. Baseline Facts

Live-code evidence was rechecked on commit `6f930a28b2b0b4fad00e51bc569a282c6af0b393`.

Stage4 PASS attempt and completion truth:
- `modules/core/stage4_interview_round.py:6559` records `_record_s4_attempt(... success=True, verdict=...)` while building the positive verdict payload.
- `modules/core/stage4_post_processor.py:1368` can fail `_save_pass_result_primary_db`, emit `primary_db_failed`, and return `False`.
- `modules/core/stage4_post_processor.py:1414` can fail later metadata settlement, emit `primary_persisted_meta_failed`, and return `False`.
- `modules/core/stage4_post_processor.py:1499` is the first observed `fully_settled` settlement status.
- `modules/core/stage4_orchestrator.py:1483` receives `False` from `process_pass_result` and returns `False`.
- `modules/core/stage4_orchestrator.py:2814` emits `stage4_complete` after `_run_interview_loop` returns without `should_return`.

Stage2 retry truth:
- `modules/core/stage2_orchestrator.py:767` returns a retry payload when the operator chooses retry.
- `modules/core/stage2_orchestrator.py:1676` documents that the exhausted-arc boundary only normalizes abort/skip.
- `modules/core/stage2_orchestrator.py:1693` handles skip, then line `1695` returns `action: next` for every other action, swallowing retry.

Source lineage and cached material:
- `modules/core/stage2_orchestrator.py:338` reads current `plot_roadmap`.
- `modules/core/stage2_orchestrator.py:372` loads existing refined arcs from DB anchor `arcs`.
- `modules/core/stage2_orchestrator.py:426` declares Stage2 complete by count only.
- `modules/core/stage3_orchestrator.py:1802` injects current `plot_roadmap[arc_idx]` by ordinal.
- `modules/core/stage4_context_packets.py:623` injects current `plot_roadmap[arc_idx]` by ordinal.

Stage4 persisted previous_attempt hydration:
- `modules/core/stage4_interview_round.py:2420` loads `get_stage_attempts_for_arc(arc_num, stages=(4,), limit=12)`.
- `modules/core/stage4_interview_round.py:2431` filters only by same episode.
- `modules/core/db_manager.py:2779` exposes `get_stage_attempts_for_arc` without a `session_id` filter.

Artifact and benchmark proof truth:
- `modules/core/artifact_logging.py:58` writes artifact snapshots under `logs/artifacts/stageN/<scope>/attempt_NN/...`; the path does not include session ID.
- `modules/core/failure_analyzer.py:2271` compares sink metadata and line `2338` checks artifact existence, but does not recompute actual file bytes against `content_hash`.
- `benchmarks/benchmark_index.csv:6` records `target_ep=18,status=completed` while notes say `after_latest_ep=17`.
- `benchmarks/.gitignore:1` ignores all benchmark archive snapshot folders except allowlisted index/README/gitignore.

Direct supervised runners and CI:
- `scripts/run_stage2_direct_supervised.py:51`, `scripts/run_stage3_direct_supervised.py:53`, and `scripts/run_stage4_direct_supervised.py:46` return shell exit code `0` after printing payloads.
- The same scripts compute semantic payload success later (`stage2` line `107`, `stage3` line `92`, `stage4` line `76`).
- `scripts/canary_semantic_exit.py:39` only fails archive proof when an archive failure is present; missing archive proof remains outside that helper's hard failure surface.

## 3. Scope

Included:
- Stage4 pass-settlement, completion, proof, and attempt-record truth.
- Stage2 exhausted-arc retry semantics.
- Stage4 previous_attempt hydration freshness.
- Stage0/BI/TR source lineage guardrails for Stage2/3/4 cached material.
- Artifact byte-hash verification and benchmark completion semantics.
- Direct supervised runner semantic exit codes and CI coverage for these locks.
- Secondary P2/P3 truth gaps only after higher-priority runtime truth locks are closed.

Excluded:
- Desktop/UI redesign.
- New narrative quality criteria.
- Any Python-only pass/reject authority over manuscript quality.
- WorkGuard or material-side production changes unless they are needed as source-lineage evidence.
- Live API or memory-bank feature expansion.

## 4. Pass 1. Inventory Summary

| Area | Severity | Runtime Meaning | First Action |
| --- | --- | --- | --- |
| Stage4 settlement and completion truth | P0/P1 | PASS attempt and `stage4_complete` can appear before fully-settled proof | implement first |
| Stage2 retry contract | P1 | operator retry choice can be swallowed into next | implement second |
| Stage4 hydration freshness | P1 | stale persisted retry memory can enter fresh runs | implement third |
| Source lineage/cache gate | P0/P1 | stale arcs can pair with new `plot_roadmap` by ordinal | implement fourth |
| Artifact/benchmark proof truth | P0/P1 | metadata may certify stale or missing artifact truth | implement fifth |
| Direct runner semantic exit/CI | P1 | shell success can hide payload failure; CI misses lock tests | implement sixth |
| Secondary truth sweep | P2/P3 | CoVe fail-closed wording, model/provider cache keys, quad cache blind spots | implement seventh |

## 5. Pass 2. Semantic Classification

Class A - authoritative truth locks:
- Stage4 settlement and completion truth.
- Artifact byte proof and benchmark target completion truth.

Class B - stale-context prevention:
- Stage4 previous_attempt hydration session freshness.
- Stage0 -> Stage2/3/4 source lineage and cache gates.

Class C - operator-control correctness:
- Stage2 retry semantics.
- Direct supervised runner semantic shell exits.
- CI coverage expansion.

Class D - parked secondary truth cleanup:
- CoVe fail-closed messaging/runtime mismatch.
- process-local context cache key dimensions.
- DB-persisted quad cache content/model freshness.

## 6. Side-Effect Map

file writes / artifacts:
- Stage4 settlement changes can affect manuscript, episode bible, settlement packet, artifact snapshots, and benchmark archive claims.
- Artifact proof work can change `logs/artifacts`, benchmark archive manifests, and proof summaries.

DB / schema / transaction boundaries:
- Stage4 pass settlement touches episode persistence, episode metadata, `stage_attempts`, UI events, and authority rows.
- Hydration freshness may require filtering `stage_attempts` by `session_id` or adding a bounded fallback contract.
- Source-lineage cache gates may require anchor metadata or lineage hashes for cached arcs.

JSONL / log / audit sinks:
- `stage4_pass_settlement_status`, `stage4_complete`, stage attempts, pass-rate monitor, session decisions, episode production JSONL, and benchmark index are in scope.

console / UI / operator output:
- Failed settlement must be visibly non-complete.
- Stage2 retry must tell the operator that retry is actually happening.
- Direct runners must keep JSON payload output but return semantic shell failure on semantic failure.

rollback / recovery / retry:
- Stage4 settlement failure must not be represented as a complete run.
- Stage2 retry must preserve retry loop state and not advance arc progress.
- Hydration changes must not erase same-session retry memory.

cache / global state:
- StateTracker-loaded arcs, DB anchor caches, context cache keys, and previous_attempt hydration are in scope.

bootstrap fallback / config-env mutation:
- Not directly applicable except CI workflow updates in the runner semantic-exit tranche.

## 7. Realization Architecture

Use a strict sequence. Do not jump to a later, easier item if an earlier item still controls downstream truth.

1. Lock Stage4 settlement and completion truth.
2. Lock Stage2 retry semantics.
3. Scope Stage4 persisted hydration to fresh-session truth.
4. Add source-lineage/cache gates before Stage2/3/4 reuse.
5. Recompute artifact proof truth and fix benchmark completion semantics.
6. Convert direct supervised runner exits and CI coverage to semantic truth.
7. Sweep remaining P2/P3 truth mismatches.

Design constraints:
- Python collectors may gather facts, compare bytes, and format proof payloads.
- Python must not decide narrative pass/reject quality.
- Director/LLM remains the only authority for manuscript quality decisions.
- `fully_settled` is the only authoritative Stage4 PASS settlement state.
- A shell success code is allowed only when the payload's already-authored semantic proof is successful.

## 8. Execution Tranches

1. `stage4-settlement-complete-truth`
   - Move or defer PASS-success attempt recording so it cannot become authoritative before settlement.
   - Ensure settlement failure cannot emit `stage4_complete`.
   - Add regression tests for failed primary DB and failed metadata settlement.

2. `stage2-exhausted-arc-retry-contract`
   - Preserve `action: retry` from `_handle_stage2_arc_failure`.
   - Ensure the calling loop retries the same arc instead of advancing.
   - Add focused Stage2 retry regression coverage.

3. `stage4-hydration-session-freshness`
   - Add session-aware filtering to persisted previous_attempt hydration.
   - Keep explicit in-memory previous_attempt as higher authority than DB hydration.
   - Add regression tests for same-episode stale cross-session rows.

4. `stage0-stage234-source-lineage-cache-gate`
   - Define source lineage fingerprint for `plot_roadmap` and cached arcs.
   - Refuse or invalidate stale cached arcs when lineage changes.
   - Ensure Stage3 and Stage4 ordinal context injection cannot silently pair stale arcs with new treatment blocks.

5. `stage234-artifact-proof-benchmark-truth`
   - Recompute artifact bytes and compare with recorded `content_hash`.
   - Treat missing byte proof or mismatched bytes as non-authoritative proof.
   - Prevent benchmark `completed` when `after_latest_ep < target_ep`.

6. `direct-supervised-runner-semantic-exit-ci`
   - Make Stage2/3/4 direct supervised scripts return non-zero on payload `success: false`.
   - Add tests or script-level proof for semantic exit codes.
   - Expand CI workflow to cover run-control and pipeline truth locks that are currently local-only.

7. `secondary-pipeline-truth-sweep`
   - Reconcile Stage4 CoVe fail-closed wording with actual behavior.
   - Add model/provider dimensions to context cache keys where needed.
   - Add content/model freshness checks for DB-persisted quad caches where runtime use proves risk.

## 9. Acceptance Criteria

- Stage4 settlement failure does not leave an authoritative PASS attempt, `stage4_complete`, or benchmark-completed proof behind.
- A Stage4 PASS attempt becomes authoritative only after `fully_settled` settlement.
- Stage2 exhausted-arc retry actually retries the same arc.
- Stage4 persisted previous_attempt hydration cannot import a failed attempt from another session unless an explicit, audited fallback says so.
- Stage2/3/4 cached material reuse is blocked or invalidated when source lineage changes.
- Artifact proof recomputes actual file bytes before accepting recorded content hashes.
- Benchmark status cannot be `completed` when target progress was not reached.
- Direct supervised scripts return non-zero when payload semantic success is false.
- CI covers the tests needed to prevent recurrence of the implemented locks.

## 10. Verification Plan

Run verification in small, memory-conservative shards:

1. Stage4 settlement shard:
   - `python -m pytest tests/test_stage4_orchestrator.py tests/test_stage4_post_processor.py tests/test_stage4_interview_round.py`

2. Stage2 retry shard:
   - `python -m pytest tests/test_stage2_orchestrator.py`

3. Hydration/source-lineage/artifact shard:
   - `python -m pytest tests/test_stage4_interview_round.py tests/test_stage4_canary_tools.py tests/test_failure_analyzer.py`

4. Direct runner/CI shard:
   - targeted script tests discovered during implementation.

5. Hygiene and ops:
   - `python scripts/check_utf8_hygiene.py <touched files>`
   - `python scripts/ops_validator.py --strict`
   - `git diff --check`

## 11. Guardrails

- Do not let regex or Python heuristics decide narrative PASS/REJECT.
- Do not weaken Director sovereignty.
- Do not reclassify a partial Stage4 settlement as complete for operator convenience.
- Do not make stale cross-session memory the default.
- Do not trust benchmark index rows without target-progress proof.
- Do not patch from stale survey text if live code contradicts it.
- Do not run full pytest in one memory-heavy batch unless the smaller shards have already passed and memory pressure is acceptable.

## 12. Temp Queue Notes

- temp status: in_progress
- cleanup condition: remove `docs/temp/current-pipeline-truth-locks-execution-ssot.md` only after all seven tranches are implemented, verified, closure-audited, and the canonical doc is marked closed.
- roadmap dependency: none; this is a single active execution SSOT with an internal tranche order, so no aggregate roadmap is required.

## 13. Document 3-Pass Audit

Pass 1 - structure and scope:
- Attack: a single SSOT for many findings could become vague and non-actionable.
- Result: the document has a fixed tranche order, per-tranche scope, acceptance criteria, side-effect map, and verification plan.

Pass 2 - evidence and consistency:
- Attack: the document could over-trust prior parallel-agent findings.
- Result: all core claims were rechecked against live code on `6f930a28`; line evidence is included inline and bounded to inspected paths.

Pass 3 - execution and readability:
- Attack: the document could accidentally authorize Python to judge manuscript quality.
- Result: guardrails explicitly separate Python fact collection from LLM/Director pass-reject authority.

Confidence Gate:
- Estimated confidence: 96%.
- Remaining uncertainty: exact implementation shape for Stage4 PASS attempt deferral may require one additional local code read before patching.
- Save decision: final canonical save and temp mirror are allowed.

## 14. Pre-Implementation Re-Audit

Current-state re-audit completed before code modification:

- Structure: still an execution SSOT, not a survey-only note.
- Evidence: the P0/P1 live-code surfaces listed above are still present on the baseline commit.
- Queue: `docs/temp` has no other active execution SSOT mirrors, so this single active mirror can govern execution without an aggregate roadmap.
- Execution readiness: begin with tranche 1 only; do not patch later tranches until tranche 1 is verified or explicitly paused.
- Confidence: 96%.

## 15. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: not required for a single active execution mirror
- execution-start rule: satisfied for tranche 1 by section 14 current-state re-audit

## 16. Tranche 1 Implementation Note

Status: partially realized; tranche 1 core lock implemented and locally verified.

Implemented changes:
- `modules/core/stage4_orchestrator.py` now blocks `stage4_complete` and audit-summary emission after a pass-settlement failure path marks completion blocked.
- `modules/core/stage4_interview_round.py` carries the pre-settlement Stage4 attempt key through internal state-update metadata for settlement auditing.
- `modules/core/stage4_post_processor.py` strips that internal metadata before normal state persistence, emits settlement status with the attempt key, and demotes failed pre-settlement PASS attempts through DB telemetry.
- `modules/core/db_manager.py` adds `mark_stage4_attempt_settlement_failed`, which changes a pre-settlement `PASS` or `PASS_WITH_FIX` Stage4 attempt to `SETTLEMENT_FAILED`.

Verification completed:
- `python -m pytest tests/test_stage4_orchestrator.py::TestStage4AuditSummary`: 11 passed.
- `python -m pytest tests/test_stage4_post_processor.py -k "returns_true_on_success or returns_false_on_db_failure or settlement_failure_demotes or returns_false_and_logs_when_meta_save_fails or returns_false_when_settlement_packet_save_fails"`: 5 passed.
- `python -m pytest tests/test_stage4_interview_round.py -k "record_s4_attempt or build_positive_verdict_payload"`: 8 passed.
- `python -m pytest tests/test_db_manager.py -k "stage_attempt or settlement"`: 8 passed.
- `python -m ruff check modules/core/stage4_orchestrator.py modules/core/stage4_interview_round.py modules/core/stage4_post_processor.py modules/core/db_manager.py tests/test_stage4_orchestrator.py tests/test_stage4_post_processor.py tests/test_stage4_interview_round.py tests/test_db_manager.py`: passed.
- `python -m py_compile modules/core/stage4_orchestrator.py modules/core/stage4_interview_round.py modules/core/stage4_post_processor.py modules/core/db_manager.py`: passed.

Complexity recount:
- `modules/core/stage4_orchestrator.py`: max function 96 LOC; touched functions `__init__` 13 LOC, `_consume_episode_round_outcome` 29 LOC, `stage_4_v2_chief_writer` 56 LOC; 120+ functions 0, 180+ functions 0.
- `modules/core/stage4_interview_round.py`: touched `_build_positive_verdict_payload` 132 LOC; classified as bounded semantic assembly for Stage4 Director PASS payload and not newly entering 180+; file has pre-existing 120+/180+ unrelated hotspots.
- `modules/core/stage4_post_processor.py`: touched `process_pass_result` reduced to 176 LOC after helper extraction; 180+ functions 0; remaining 120+ function is a bounded sink-boundary orchestration shell.
- `modules/core/db_manager.py`: touched `mark_stage4_attempt_settlement_failed` 56 LOC; file has no 180+ functions.

Residual tranche 1 risk:
- Pass-rate monitor JSONL may still contain the pre-settlement positive attempt row until the later artifact/proof tranche recomputes sink truth across all proof surfaces. DB final-authority telemetry is now demoted on settlement failure.

## 17. Tranche 2 Implementation Note

Status: realized and locally verified.

Implemented changes:
- `modules/core/stage2_orchestrator.py` now preserves an exhausted-arc `retry` choice instead of falling through to `next`.
- The exhausted retry path resets the same Arc attempt counter to `0`, carries operator retry feedback into both feedback channels, refreshes the constraint block when provided, and clears stale previous-attempt carryover before retrying the same Arc.
- `tests/test_stage2_orchestrator_lane_b.py` adds a regression proving that a retry after max-attempt exhaustion re-enters the same Arc instead of advancing.

Verification completed:
- `python -m pytest tests/test_stage2_orchestrator_lane_b.py -k "threads_attempt_state or preserves_exhausted_retry_choice"`: 2 passed.
- `python -m pytest tests/test_stage2_orchestrator_lane_b.py tests/test_stage2_orchestrator_lane_f.py`: 12 passed.
- `python -m ruff check modules/core/stage2_orchestrator.py tests/test_stage2_orchestrator_lane_b.py tests/test_stage2_orchestrator_lane_f.py`: passed.
- `python -m py_compile modules/core/stage2_orchestrator.py`: passed.

Complexity recount:
- `modules/core/stage2_orchestrator.py`: max function 156 LOC pre-existing; touched `_run_stage2_single_arc_design` 103 LOC and `_handle_stage2_single_arc_failure` 33 LOC; 180+ functions 0.

Document re-audit:
- Pass 1 structure: tranche 2 note is scoped to Stage2 retry semantics only.
- Pass 2 evidence: verification commands match the tests actually run.
- Pass 3 execution: next tranche remains Stage4 hydration session freshness.
- Estimated confidence: 96%.

## 18. Tranche 3 Implementation Note

Status: realized and locally verified.

Implemented changes:
- `modules/core/db_manager.py` extends `get_stage_attempts_for_arc` with optional `session_id` filtering and returns `session_id` in result rows.
- `modules/core/stage4_interview_round.py` resolves the current logging session and passes it into persisted previous-attempt hydration when available.
- Hydration also applies a runtime same-session filter after DB read-back, so stale rows returned by broad mocks or old surfaces are still rejected.
- `tests/test_stage4_interview_round.py` adds a regression proving stale same-episode rows from another session are not hydrated.
- `tests/test_db_manager.py` adds DB coverage for session-scoped stage-attempt lookup.

Verification completed:
- `python -m pytest tests/test_stage4_interview_round.py -k "hydrate_persisted_stage4_previous_attempt"`: 3 passed.
- `python -m pytest tests/test_db_manager.py -k "get_stage_attempts_for_arc"`: 2 passed.
- `python -m ruff check modules/core/stage4_interview_round.py modules/core/db_manager.py tests/test_stage4_interview_round.py tests/test_db_manager.py`: passed.
- `python -m py_compile modules/core/stage4_interview_round.py modules/core/db_manager.py`: passed.

Complexity recount:
- `modules/core/stage4_interview_round.py`: touched `hydrate_persisted_stage4_previous_attempt` 70 LOC; file retains pre-existing unrelated 120+/180+ hotspots.
- `modules/core/db_manager.py`: touched `get_stage_attempts_for_arc` 44 LOC and `mark_stage4_attempt_settlement_failed` 56 LOC; 180+ functions 0.

Document re-audit:
- Pass 1 structure: tranche 3 note is scoped to session freshness only.
- Pass 2 evidence: DB and runtime filters are both represented in tests.
- Pass 3 execution: next tranche remains Stage0 -> Stage2/3/4 source-lineage cache gating.
- Estimated confidence: 96%.

## 19. Tranche 4 Implementation Note

Status: realized and locally verified.

Implemented changes:
- `modules/core/stage0_handoff.py` defines `stage2_arcs_source_lineage` as the plot-roadmap source-lineage anchor and provides shared helpers for building, loading, and comparing `plot_roadmap` fingerprints.
- `modules/core/stage2_orchestrator.py` persists lineage on first Stage2 bootstrap and refuses cached `arcs` reuse when the saved lineage differs from the current `MasterBible.plot_roadmap`.
- `modules/core/stage3_orchestrator.py` skips Treatment Block context injection when cached Stage2 arcs no longer match the current plot-roadmap lineage.
- `modules/core/stage4_context_packets.py` skips Treatment `genre_ext` injection when cached Stage2 arcs no longer match the current plot-roadmap lineage.
- `tests/test_bi_tr_canonical_contract.py`, `tests/test_stage2_orchestrator.py`, `tests/test_stage2_stage3_episode_boundary_guardrail.py`, and `tests/test_stage4_context_builder.py` add lineage regression coverage for same-source matching, stale Stage2 cache refusal, and stale Stage3/Stage4 injection suppression.

Verification completed:
- `python -m pytest tests/test_bi_tr_canonical_contract.py -k plot_roadmap_lineage`: 1 passed.
- `python -m pytest tests/test_stage2_orchestrator.py -k bootstrap_stage2_arc_pipeline`: 3 passed.
- `python -m pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -k stale_cached_arc_lineage`: 1 passed.
- `python -m pytest tests/test_stage4_context_builder.py -k stale`: 1 passed.
- `python -m pytest tests/test_stage2_stage3_episode_boundary_guardrail.py`: 30 passed.
- `python -m pytest tests/test_stage3_orchestrator.py -k treatment_block_is_injected_into_semantic_context`: 1 passed.
- `python -m pytest tests/test_stage4_context_builder.py -k "stale or tier12 or mandatory_context"`: 30 passed.
- `python -m ruff check modules/core/stage0_handoff.py modules/core/stage2_orchestrator.py modules/core/stage3_orchestrator.py modules/core/stage4_context_packets.py tests/test_bi_tr_canonical_contract.py tests/test_stage2_orchestrator.py tests/test_stage2_stage3_episode_boundary_guardrail.py tests/test_stage4_context_builder.py`: passed.
- `python -m py_compile modules/core/stage0_handoff.py modules/core/stage2_orchestrator.py modules/core/stage3_orchestrator.py modules/core/stage4_context_packets.py`: passed.

Complexity recount:
- `modules/core/stage0_handoff.py`: max function 68 LOC; touched lineage helpers are below 30 LOC; 120+ functions 0, 180+ functions 0.
- `modules/core/stage2_orchestrator.py`: max function 158 LOC; touched `_stage2_cached_arcs_lineage_ready` remains a small runtime gate; 180+ functions 0.
- `modules/core/stage3_orchestrator.py`: touched `_inject_stage3_treatment_block_context` remains below 120 LOC; file retains pre-existing unrelated 120+ hotspots, 180+ functions 0.
- `modules/core/stage4_context_packets.py`: touched `build_tier12_auxiliary_sections` remains 158 LOC and is a bounded sink-boundary assembly shell; 180+ functions 0.

Document re-audit:
- Pass 1 structure: tranche 4 note covers Stage2 cache reuse plus Stage3/Stage4 ordinal Treatment-context injection.
- Pass 2 evidence: lineage fingerprint tests and Stage2/3/4 stale-cache regressions match the implemented runtime gates.
- Pass 3 execution: next tranche remains artifact/proof/benchmark truth; no Director or LLM pass-reject authority was moved into Python.
- Estimated confidence: 96%.

## 20. Tranche 5 Implementation Note

Status: realized and locally verified.

Implemented changes:
- `modules/core/failure_analyzer.py` now resolves artifact paths and recomputes on-disk sha256 bytes for recorded artifact proofs.
- Artifact byte mismatches are reported as `artifact_content_hash_mismatches`; placeholder non-sha256 test strings are ignored so only real sha256 proof claims are byte-checked.
- `scripts/archive_benchmark_record.py` demotes requested `completed` benchmark status to `operational_failure` when `target_ep` exists but the lane's latest proven episode is missing or below target.
- `benchmarks/benchmark_index.csv` reclassifies the two historical target-ep18 rows whose notes prove `after_latest_ep=17` from `completed` to `operational_failure`.
- `tests/test_failure_analyzer.py` adds artifact byte-hash recomputation coverage.
- `tests/test_archive_benchmark_record.py` adds target-progress status demotion coverage.

Verification completed:
- `python -m pytest tests/test_failure_analyzer.py -k "artifact_results"`: 3 passed.
- `python -m pytest tests/test_failure_analyzer.py -k sink_alignment`: 33 passed.
- `python -m pytest tests/test_failure_analyzer.py -k "artifact_results or sink_alignment_summary_detects_missing_and_mismatch"`: 4 passed.
- `python -m pytest tests/test_archive_benchmark_record.py`: 4 passed.
- `python -m ruff check modules/core/failure_analyzer.py scripts/archive_benchmark_record.py tests/test_failure_analyzer.py tests/test_archive_benchmark_record.py`: passed.
- `python -m py_compile modules/core/failure_analyzer.py scripts/archive_benchmark_record.py`: passed.

Complexity recount:
- `modules/core/failure_analyzer.py`: touched `_collect_sink_alignment_artifact_results` is 108 LOC; touched `_build_sink_alignment_summary_payload` remains a pre-existing 299 LOC sink-boundary aggregation function; 180+ functions remain pre-existing and did not increase in count.
- `scripts/archive_benchmark_record.py`: max function 111 LOC; new benchmark status helpers are 20 LOC or less; 120+ functions 0, 180+ functions 0.

Document re-audit:
- Pass 1 structure: tranche 5 note covers both artifact proof bytes and benchmark completion semantics.
- Pass 2 evidence: verification includes direct artifact helper tests, broader sink-alignment shard, and benchmark archive status tests.
- Pass 3 execution: next tranche remains direct supervised runner semantic exits and CI coverage.
- Estimated confidence: 96%.

## 21. Tranche 6 Implementation Note

Status: realized and locally verified.

Implemented changes:
- `scripts/direct_supervised_semantic_exit.py` defines the shared semantic exit helper: shell exit 0 is allowed only when the payload has `success is True`.
- `scripts/run_stage2_direct_supervised.py`, `scripts/run_stage3_direct_supervised.py`, and `scripts/run_stage4_direct_supervised.py` now return semantic exit codes from `main()` after printing their JSON payloads.
- `.github/workflows/test.yml` adds `tests/test_direct_supervised_semantic_exit.py` and `tests/test_failure_analyzer.py` to the focused PR gate so semantic runner exits and artifact-proof truth locks are covered in CI.
- `tests/test_direct_supervised_semantic_exit.py` verifies the shared helper and source-level wiring for all three direct supervised scripts.

Verification completed:
- `python -m pytest tests/test_direct_supervised_semantic_exit.py`: 2 passed.
- `python -m pytest tests/test_failure_analyzer.py -q`: 51 passed.
- `python -m ruff check scripts/direct_supervised_semantic_exit.py scripts/run_stage2_direct_supervised.py scripts/run_stage3_direct_supervised.py scripts/run_stage4_direct_supervised.py tests/test_direct_supervised_semantic_exit.py`: passed.
- `python -m py_compile scripts/direct_supervised_semantic_exit.py scripts/run_stage2_direct_supervised.py scripts/run_stage3_direct_supervised.py scripts/run_stage4_direct_supervised.py`: passed.
- `.github/workflows/test.yml` parsed successfully with PyYAML.

Complexity recount:
- `scripts/direct_supervised_semantic_exit.py`: `semantic_exit_code` is 5 LOC.
- `scripts/run_stage2_direct_supervised.py`: max function 72 LOC; 120+ functions 0, 180+ functions 0.
- `scripts/run_stage3_direct_supervised.py`: max function 55 LOC; 120+ functions 0, 180+ functions 0.
- `scripts/run_stage4_direct_supervised.py`: max function 56 LOC; 120+ functions 0, 180+ functions 0.

Document re-audit:
- Pass 1 structure: tranche 6 note covers semantic shell exits plus CI gate coverage.
- Pass 2 evidence: tests prove helper semantics and script wiring without booting live app surfaces.
- Pass 3 execution: next tranche remains secondary P2/P3 truth sweep.
- Estimated confidence: 96%.

## 22. Tranche 7 Implementation Note

Status: realized and locally verified.

Implemented changes:
- `modules/core/stage4_outcome_runtime.py` now names CoVe runtime exceptions as `[Advisory:CoVeRuntime:*]` instead of fail-closed warnings when the Director PASS path is preserved.
- The true CoVe LLM contradiction path still uses `cove_fail_closed` and still downgrades provisional PASS to retry; Python did not gain narrative PASS/REJECT authority.
- `modules/domain/agents/base_agent.py` adds module-level context-cache key helpers that include provider/auth mode, model, project/cache type, and content hash in the process-local cache key.
- Process-local context-cache lineage now stores model and provider tokens beside the content hash.
- `_ask_with_cached_context` now bypasses cached-content use when the cache name has no fresh process-local lineage or its content/model/provider lineage does not match the current agent.
- `tests/test_base_agent.py` covers provider/model key separation plus missing/stale cached-context lineage fallback.
- `tests/test_stage4_orchestrator.py` covers the advisory CoVe runtime wording while preserving the existing Director PASS UI message.

Verification completed:
- `python -m pytest tests/test_base_agent.py -k "context_cache or cached_context"`: 12 passed.
- `python -m pytest tests/test_stage4_orchestrator.py -k "cove_runtime_failure or cove_fail_closed or cove_regeneration"`: 4 passed.
- `python -m ruff check modules/core/stage4_outcome_runtime.py modules/domain/agents/base_agent.py tests/test_stage4_orchestrator.py tests/test_base_agent.py`: passed.
- `python -m py_compile modules/core/stage4_outcome_runtime.py modules/domain/agents/base_agent.py`: passed.

Complexity recount:
- `modules/core/stage4_outcome_runtime.py`: max function 98 LOC; touched `_emit_cove_runtime_failure_logs` and `_build_cove_runtime_failure_messages` remain below 120 LOC; 120+ functions 0, 180+ functions 0.
- `modules/domain/agents/base_agent.py`: cache-key helper logic is module-level to avoid adding BaseAgent direct-method pressure; BaseAgent remains 62 direct methods, a pre-existing high-pressure owner.
- `modules/domain/agents/base_agent.py`: touched `_ask_with_cached_context` is 171 LOC and `_get_or_create_context_cache` is 166 LOC; both are bounded context-cache runtime shells under the 180 LOC hard band.
- `modules/domain/agents/base_agent.py`: one pre-existing unrelated 180+ function remains (`_attempt_backup_recovery` 203 LOC); this tranche did not increase the 180+ count.

Document re-audit:
- Pass 1 structure: tranche 7 note covers only secondary P2/P3 truth cleanup and does not reopen completed P0/P1 locks.
- Pass 2 evidence: tests prove CoVe runtime advisory wording, cache key separation, and stale-lineage fallback.
- Pass 3 execution: all seven tranches are now realized; next step is final closure validation and temp queue cleanup.
- Estimated confidence: 96%.

## 23. Final Validation and Closure

Status: completed; temp execution mirror removed after realization.

Sequential verification completed:
- `python -m pytest tests/test_base_agent.py -q`: 98 passed.
- `python -m pytest tests/test_stage4_orchestrator.py -q`: 165 passed.
- `python -m pytest tests/test_stage4_post_processor.py -k "returns_true_on_success or returns_false_on_db_failure or settlement_failure_demotes or returns_false_and_logs_when_meta_save_fails or returns_false_when_settlement_packet_save_fails" -q`: 5 passed.
- `python -m pytest tests/test_stage4_interview_round.py -k "record_s4_attempt or build_positive_verdict_payload or hydrate_persisted_stage4_previous_attempt" -q`: 11 passed.
- `python -m pytest tests/test_db_manager.py -k "stage_attempt or settlement or get_stage_attempts_for_arc or context_cache" -q`: 12 passed.
- `python -m pytest tests/test_bi_tr_canonical_contract.py -k plot_roadmap_lineage -q`: 1 passed.
- `python -m pytest tests/test_stage2_orchestrator.py -k bootstrap_stage2_arc_pipeline -q`: 3 passed.
- `python -m pytest tests/test_stage2_orchestrator_lane_b.py tests/test_stage2_orchestrator_lane_f.py -q`: 12 passed.
- `python -m pytest tests/test_stage2_stage3_episode_boundary_guardrail.py -q`: 30 passed.
- `python -m pytest tests/test_stage3_orchestrator.py -k treatment_block_is_injected_into_semantic_context -q`: 1 passed.
- `python -m pytest tests/test_stage4_context_builder.py -k "stale or tier12 or mandatory_context" -q`: 30 passed.
- `python -m pytest tests/test_failure_analyzer.py -q`: 51 passed.
- `python -m pytest tests/test_archive_benchmark_record.py -q`: 4 passed.
- `python -m pytest tests/test_direct_supervised_semantic_exit.py -q`: 2 passed.

Static and operational validation completed:
- `.github/workflows/test.yml` parsed successfully with PyYAML.
- `python -m ruff check <all touched python files>`: passed.
- `python -m py_compile <all touched production python files>`: passed.
- `python scripts/check_utf8_hygiene.py <all touched text/code/config/doc files>`: passed.
- `git diff --check`: passed.
- `python scripts/ops_validator.py --strict`: passed; `docs/temp` has no active execution SSOT mirrors.

Closure re-audit:
- Pass 1 structure: the execution SSOT now records all seven tranches and a final validation block.
- Pass 2 evidence: local focused regression coverage spans the touched Stage2, Stage3, Stage4, DB, cache, artifact, benchmark, direct-runner, and CI surfaces.
- Pass 3 execution: `docs/temp/current-pipeline-truth-locks-execution-ssot.md` is no longer an active execution queue item after closure.
- Estimated confidence: 96%.
