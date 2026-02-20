# Codex Findings Sweep100 (Manual-Only)

This file is governed by:
- `AGENTS.md` (root manual sweep guard)
- `docs/codex_sweep100_manual_plan.md`

## Execution Mode
- Mode: uninterrupted manual sweep
- Mid-run user query: prohibited unless hard blocker
- Hard blocker record must include: blocker, last completed round, resume condition

## Validation Command
```bash
python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100 --allow-empty
python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100
python scripts/validate_manual_sweep.py docs/codex_findings_sweep100_manual.md --from-round 1 --to-round 100 --max-fp-ratio 0.35 --max-fp-streak 2
```

## Round Template
```markdown
### Round N

**Read files**: `file1.py`, `file2.py`

**Manual inspection evidence**:
- `file:line` function/branch path manually verified.
- `file:line` fallback/exception path manually verified.
- caller-callee contract trace + intent check.

**Confirmed Bugs** (runtime crashes or incorrect results):
- none

**Risks** (needs design confirmation):
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- none
```

## Checkpoint Template (Every 10 Rounds)
```markdown
## Checkpoint - Manual Round XX

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | N (P0: a, P1: b, P2: c, P3: d) |
| Cumulative Risks | N |
| Cumulative False Positives Excluded | N |
| Cumulative Test Gaps | N |
| Phase False-Positive Ratio | X% |
| Consecutive Empty Rounds | N |
| Manual Evidence Compliance Rate | X% |
```

### Round 1

**Read Files**: `modules/core/stage2_orchestrator.py`, `modules/core/stage2_context.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_orchestrator.py:26` constructor keeps lazy DI handles (`_ctx`, `_validation_pipeline`, `_preflight`, `_finalizer`) and defers heavy object creation.
- `modules/core/stage2_orchestrator.py:41` lazily builds context via `Stage2Context.from_app`; caller-callee traced to `modules/core/stage2_context.py:184`.
- `modules/core/stage2_context.py:191` to `modules/core/stage2_context.py:231` uses `getattr(..., None)` for optional app capabilities, matching fail-soft DI intent instead of strict required contract.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_context.py:184` missing unit test that verifies `from_app` mapping when optional app attributes are absent but required 5 fields exist.

### Round 2

**Read Files**: `modules/core/stage2_orchestrator.py`, `modules/core/stage2_context.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_orchestrator.py:118` to `modules/core/stage2_orchestrator.py:126` explicitly guards missing bible anchor and exits early, preventing downstream null access.
- `modules/core/stage2_orchestrator.py:128` to `modules/core/stage2_orchestrator.py:131` intentionally allows empty `volumes_strategy` with default arc execution path.
- Caller-callee contract checked: `modules/core/stage2_orchestrator.py:211` uses `self.ctx.get_int_input`; optional binding source is `modules/core/stage2_context.py:220`, so runtime depends on app wiring rather than local fallback.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_orchestrator.py:129` missing regression test for empty volume strategy path (`volumes=[]`) to confirm default strategy behavior stays stable.

### Round 3

**Read Files**: `modules/core/stage2_orchestrator.py`, `modules/core/stage2_context.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_orchestrator.py:157` to `modules/core/stage2_orchestrator.py:166` rebuilds `StateTracker` when cache is absent or stale (`existing_tracker_arcs > len(all_refined_arcs)`), which is explicit reset intent.
- `modules/core/stage2_orchestrator.py:172` to `modules/core/stage2_orchestrator.py:175` loads only incremental arcs and updates `_state_tracker_loaded_arcs` through context field.
- `modules/core/stage2_orchestrator.py:178` to `modules/core/stage2_orchestrator.py:181` persists financial registry only in investment genre, matching conditional domain policy.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_orchestrator.py:161` missing boundary test where `existing_tracker_arcs` exceeds current arc count after rollback/trim.

### Round 4

**Read Files**: `modules/core/stage2_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_orchestrator.py:266` to `modules/core/stage2_orchestrator.py:280` sanitizes gather results by removing exceptions and non-dict entries before later stages.
- `modules/core/stage2_orchestrator.py:308` to `modules/core/stage2_orchestrator.py:320` reconstructs original arc order after partial recovery via `_success_indices` + `recovery_map`.
- `modules/core/stage2_orchestrator.py:325` to `modules/core/stage2_orchestrator.py:328` hard-stops when batch becomes empty, preventing silent progression with no arc data.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_orchestrator.py:311` missing deterministic test for interleaved success/failure indices to verify order restoration after recovery.

### Round 5

**Read Files**: `modules/core/stage2_orchestrator.py`, `modules/core/stage2_preflight.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_orchestrator.py:393` to `modules/core/stage2_orchestrator.py:404` caller-callee handoff into `Stage2PreflightAnalysis._preflight_state_setup` (`modules/core/stage2_preflight.py:20`) confirmed.
- `modules/core/stage2_orchestrator.py:486` to `modules/core/stage2_orchestrator.py:503` validation pipeline can force retry without mutating `refined_arc`, preserving attempt-loop contract.
- `modules/core/stage2_orchestrator.py:681`, `modules/core/stage2_orchestrator.py:712`, `modules/core/stage2_orchestrator.py:766` use blocking `input()` inside async flow and manual-failure branch.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/stage2_orchestrator.py:686` async pipeline includes blocking stdin prompt; if executed in non-interactive runner this can stall stage progression. Intent check: current implementation appears CLI-first, so classified as risk until non-interactive contract is confirmed.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_orchestrator.py:681` missing non-interactive integration test that asserts stage2 exits safely without hanging on stdin.

### Round 6

**Read Files**: `modules/core/stage2_preflight.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_preflight.py:43` to `modules/core/stage2_preflight.py:67` `_compute_arc_drive` wraps weaver failure with explicit error dict fallback.
- `modules/core/stage2_preflight.py:103` to `modules/core/stage2_preflight.py:113` threadpool parallel block applies timeout and degrades to empty defaults on failure.
- `modules/core/stage2_preflight.py:129` to `modules/core/stage2_preflight.py:167` constraint block is always regenerated and can be augmented by compiler output.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/core/stage2_preflight.py:108` broad exception around parallel preflight is intentional fail-soft policy for continuity; manual inspection shows explicit fallback assignment, not silent undefined state.

**Test Gaps**:
- `modules/core/stage2_preflight.py:106` missing timeout-path test where one future exceeds 300s and verifies fallback values are propagated.

### Round 7

**Read Files**: `modules/core/stage2_preflight.py`, `modules/core/stage2_context.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_preflight.py:146` to `modules/core/stage2_preflight.py:151` updates `ctx` cache and synchronizes both key+cache to app via `sync_cache_key_to_app(arc_count, cache=state_result)`.
- `modules/core/stage2_preflight.py:386` to `modules/core/stage2_preflight.py:391` second extraction path syncs only key (`sync_cache_key_to_app(arc_count)`), not cache payload.
- `modules/core/stage2_context.py:232` to `modules/core/stage2_context.py:234` confirms lambda writes app cache only when `cache is not None`; caller-callee contract mismatch is possible on key-only sync path.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/stage2_preflight.py:391` potential app/ctx cache divergence when sync is key-only; intent check: may be acceptable if app never reads cache directly in this branch, but that contract is not proven locally.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_preflight.py:391` missing test that validates app-level `_cumulative_state_cache` consistency after arc-analysis extraction path.

### Round 8

**Read Files**: `modules/core/stage2_preflight.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_preflight.py:236` to `modules/core/stage2_preflight.py:245` context assembly order is explicit (`quality trend` -> `constraint` -> `preflight injection`), then reused by analyst phase.
- `modules/core/stage2_preflight.py:297` to `modules/core/stage2_preflight.py:301` retry mode intentionally compresses context to minimal form plus feedback.
- `modules/core/stage2_preflight.py:303` to `modules/core/stage2_preflight.py:323` and `modules/core/stage2_preflight.py:330` to `modules/core/stage2_preflight.py:350` add reverse feedback from stage3/stage4 only when threshold/preconditions are met.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_preflight.py:311` missing test for `len(arc_stage3_failures) >= 3` threshold boundary to ensure reverse-feedback injection trigger is correct.

### Round 9

**Read Files**: `modules/core/stage2_preflight.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_preflight.py:481` to `modules/core/stage2_preflight.py:487` patch-mode entry is gated by previous score and `best_arc` presence, preventing unconditional patch path.
- `modules/core/stage2_preflight.py:533` to `modules/core/stage2_preflight.py:548` safely falls back to full generate path when patch result is absent.
- `modules/core/stage2_preflight.py:773` to `modules/core/stage2_preflight.py:785` audits patch attempt metadata, so downstream observability can distinguish patch vs normal generation.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_preflight.py:529` missing test that enforces patch-fallback branch sets telemetry (`fallback=True`) and still produces valid generate invocation.

### Round 10

**Read Files**: `modules/core/stage2_preflight.py`, `modules/core/stage2_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_preflight.py:597` to `modules/core/stage2_preflight.py:620` creates deep-copy snapshot for rollback before mutating tracker state.
- `modules/core/stage2_preflight.py:623` to `modules/core/stage2_preflight.py:637` applies multiple extraction/update operations in one pass after FourPhase PASS.
- `modules/core/stage2_preflight.py:642` to `modules/core/stage2_preflight.py:723` wraps many enrichment sub-steps in warning-only exception handlers; caller continues into orchestrator finalize path (`modules/core/stage2_orchestrator.py:513`).

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/stage2_preflight.py:677` optional-exception strategy can leave partial state-tracker updates without hard failure; intent check: continuity-oriented fail-soft is explicit, but data completeness risk remains for downstream analytics.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_preflight.py:623` missing fault-injection test that forces one extractor failure and verifies minimal invariant set for tracker consistency.

## Checkpoint - Manual Round 10

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 0 (P0: 0, P1: 0, P2: 0, P3: 0) |
| Cumulative Risks | 3 |
| Cumulative False Positives Excluded | 1 |
| Cumulative Test Gaps | 10 |
| Phase False-Positive Ratio | 25.0% |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% |

### Round 11

**Read Files**: `modules/core/stage2_validation_pipeline.py`, `modules/core/stage2_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_orchestrator.py:486` to `modules/core/stage2_orchestrator.py:503` calls validation chain and branches on returned `action`.
- `modules/core/stage2_validation_pipeline.py:23` to `modules/core/stage2_validation_pipeline.py:48` confirms `run_validation` contract is `proceed` or `retry` with updated feedback.
- `modules/core/stage2_validation_pipeline.py:169` to `modules/core/stage2_validation_pipeline.py:181` enforces refined-arc type guard and mapping validation before downstream finalizer.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_validation_pipeline.py:170` missing test for non-dict `refined_arc` return path to ensure retry feedback remains deterministic.

### Round 12

**Read Files**: `modules/core/stage2_validation_pipeline.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_validation_pipeline.py:89` to `modules/core/stage2_validation_pipeline.py:125` self-reflector branch is gated to analyst generation path and protected by exception handling.
- `modules/core/stage2_validation_pipeline.py:108` to `modules/core/stage2_validation_pipeline.py:114` list response from self-reflector is normalized to first dict candidate before replacing arc.
- `modules/core/stage2_validation_pipeline.py:130` to `modules/core/stage2_validation_pipeline.py:167` consensus REJECT path immediately returns retry with synthesized feedback; PASS path only toggles flag.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_validation_pipeline.py:109` missing regression test for self-reflector list payload (`[dict]` and `[non-dict]`) normalization.

### Round 13

**Read Files**: `modules/core/stage2_validation_pipeline.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_validation_pipeline.py:217` to `modules/core/stage2_validation_pipeline.py:223` flow guard REJECT path sets explicit retry feedback and exits early.
- `modules/core/stage2_validation_pipeline.py:604` to `modules/core/stage2_validation_pipeline.py:689` flow-structure analyzer path uses analyzer result when available, legacy fallback on import failure, and PASS fallback on runtime exception.
- `modules/core/stage2_validation_pipeline.py:691` to `modules/core/stage2_validation_pipeline.py:713` legacy guard uses Jaccard stagnation hits and deterministic reject threshold.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/stage2_validation_pipeline.py:687` runtime exception in advanced flow analyzer returns PASS (`fallback=True`), which can suppress quality rejection under analyzer failure. Intent check: fail-open appears deliberate for continuity, so this remains risk pending policy confirmation.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_validation_pipeline.py:684` missing test that forces `ImportError` and validates legacy guard takeover behavior.

### Round 14

**Read Files**: `modules/core/stage2_validation_pipeline.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_validation_pipeline.py:390` to `modules/core/stage2_validation_pipeline.py:402` continuity inspection caller-callee path verified (`continuity_inspector.inspect_arc` result drives reject/pass branch).
- `modules/core/stage2_validation_pipeline.py:403` to `modules/core/stage2_validation_pipeline.py:522` reject branch records metrics/failure memory and emits structured retry feedback.
- `modules/core/stage2_validation_pipeline.py:524` to `modules/core/stage2_validation_pipeline.py:549` pass branch applies corrected docs/constraints and stores successful examples with non-blocking metric guards.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage2_validation_pipeline.py:465` missing test for `duplicate_acquisition` violation path that verifies banned-item warning composition.

### Round 15

**Read Files**: `modules/core/stage2_finalizer.py`, `modules/core/stage2_context.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_finalizer.py:311` to `modules/core/stage2_finalizer.py:334` DB commit failure path pops appended arc and restores `StateTracker` snapshot when available.
- `modules/core/stage2_finalizer.py:466` to `modules/core/stage2_finalizer.py:531` director REJECT branch composes feedback, records reject metrics, and returns retry metadata for patch mode.
- `modules/core/stage2_finalizer.py:668` appends to `stage_rejection_history` unconditionally; related context source is optional in `modules/core/stage2_context.py:202`.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/stage2_finalizer.py:668` reject-metrics path assumes `stage_rejection_history` is a mutable list; if app wiring leaves it `None`, REJECT handling can raise and interrupt retry flow. Intent check: project may guarantee initialization, but this contract is not enforced locally.

**False Positives Excluded**:
- `modules/core/stage2_finalizer.py:131` director audit exception fallback to synthetic PASS is intentional fail-soft continuity behavior with explicit reason tagging, not a direct logic defect.

**Test Gaps**:
- `modules/core/stage2_finalizer.py:326` missing failure-injection test that verifies snapshot rollback restores all tracked fields after commit exception.

### Round 16

**Read Files**: `modules/core/stage3_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage3_orchestrator.py:69` to `modules/core/stage3_orchestrator.py:71` stage prerequisite guard blocks Stage 3 when arcs are absent.
- `modules/core/stage3_orchestrator.py:76` to `modules/core/stage3_orchestrator.py:91` lazy initialization of tracker/world/fact ledger is followed by ctx sync from app object.
- `modules/core/stage3_orchestrator.py:139` to `modules/core/stage3_orchestrator.py:145` main loop delegates each episode to `_process_single_episode` and honors returned break signal.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage3_orchestrator.py:88` missing test where one lazy-init helper fails and verifies ctx sync keeps other initialized modules intact.

### Round 17

**Read Files**: `modules/core/stage3_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage3_orchestrator.py:249` to `modules/core/stage3_orchestrator.py:256` existing blueprint path intentionally skips regeneration while updating `prev_blueprints`.
- `modules/core/stage3_orchestrator.py:259` to `modules/core/stage3_orchestrator.py:270` enforces previous-episode blueprint existence before generating next one.
- `modules/core/stage3_orchestrator.py:272` to `modules/core/stage3_orchestrator.py:281` blocks processing on missing arc context or invalid `ep_start` to prevent broken continuity input.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage3_orchestrator.py:261` missing test for continuity block branch where `working_ep-1` blueprint is missing.

### Round 18

**Read Files**: `modules/core/stage3_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage3_orchestrator.py:338` to `modules/core/stage3_orchestrator.py:367` entity registry cache invalidation is arc-index based and resets cache index on extraction failure.
- `modules/core/stage3_orchestrator.py:434` to `modules/core/stage3_orchestrator.py:450` blueprint generation call passes arc context, previous blueprint history, entity registry, and adversarial flags in one contract.
- `modules/core/stage3_orchestrator.py:485` to `modules/core/stage3_orchestrator.py:495` success path validates blueprint integrity and DB commit before counting success.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage3_orchestrator.py:365` missing test that confirms cache index resets to `-1` after entity extraction exception.

### Round 19

**Read Files**: `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage4_orchestrator.py:233` to `modules/core/stage4_orchestrator.py:272` lazy initialization of stage4 submodules (`post_processor`, `context_builder`, `interview_round`) verified with ctx-reset invalidation.
- `modules/core/stage4_orchestrator.py:278` to `modules/core/stage4_orchestrator.py:327` chain-link extractor enforces minimum manuscript size, calls director parse helpers, and returns empty dict on failure.
- `modules/core/stage4_orchestrator.py:478` to `modules/core/stage4_orchestrator.py:515` mandatory context truncation removes low-priority trailing sections before fallback hard truncation.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage4_orchestrator.py:493` missing test that validates section-drop truncation preserves high-priority leading sections under oversized mandatory context.

### Round 20

**Read Files**: `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage4_orchestrator.py:360` to `modules/core/stage4_orchestrator.py:390` main interview loop has explicit guardrails for max loops, target episode stop, and missing blueprint/arc data.
- `modules/core/stage4_orchestrator.py:587` to `modules/core/stage4_orchestrator.py:636` 5-round interview logic accepts PASS with optional CoVe post-verification and can convert CoVe failure back into retry.
- `modules/core/stage4_orchestrator.py:641` to `modules/core/stage4_orchestrator.py:660` fallback path offers manual choice between last-best manuscript and skip when all rounds fail.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/stage4_orchestrator.py:648` fallback uses interactive input (`get_int_input`) in failure branch; automated/non-interactive runtime could stall if no UI input backend is wired. Intent check: current flow appears operator-driven CLI, so kept as risk.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage4_orchestrator.py:621` missing test for CoVe `should_regenerate=True` path to ensure retry feedback correctly overrides pass candidate.

## Checkpoint - Manual Round 20

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 0 (P0: 0, P1: 0, P2: 0, P3: 0) |
| Cumulative Risks | 6 |
| Cumulative False Positives Excluded | 2 |
| Cumulative Test Gaps | 20 |
| Phase False-Positive Ratio | 25.0% |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% |

### Round 21

**Read Files**: `modules/core/stage4_context_builder.py`, `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage4_context_builder.py:27` to `modules/core/stage4_context_builder.py:62` chain-link loader validates anchor type and returns empty section on missing/invalid payload.
- `modules/core/stage4_context_builder.py:64` to `modules/core/stage4_context_builder.py:114` extended lookback digest uses bounded excerpt retrieval and global length cap.
- Caller-callee path manually traced: `modules/core/stage4_orchestrator.py:392` invokes `prepare_episode_context`, which includes chain-link/world-state fields built in `modules/core/stage4_context_builder.py:116`.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage4_context_builder.py:81` missing test for `get_recent_manuscript_excerpts` partial data where some episodes are absent/out of range.

### Round 22

**Read Files**: `modules/core/stage4_context_builder.py`

**Manual Inspection Evidence**:
- `modules/core/stage4_context_builder.py:208` to `modules/core/stage4_context_builder.py:238` returns safe empty prompt bundle when writer agent is unavailable.
- `modules/core/stage4_context_builder.py:270` to `modules/core/stage4_context_builder.py:415` mandatory context merges Arc constraints, world/fact summaries, state-tracker summaries, and volume/series summaries.
- `modules/core/stage4_context_builder.py:499` to `modules/core/stage4_context_builder.py:526` final prompt bundle includes anti-trope/justification/reflexion injections with guarded exception paths.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage4_context_builder.py:306` missing test to verify ordering invariants when both `fact_ledger` and `world_state` summaries are present.

### Round 23

**Read Files**: `modules/core/prompt_builder.py`

**Manual Inspection Evidence**:
- `modules/core/prompt_builder.py:50` to `modules/core/prompt_builder.py:117` arc-position guide maps episode ratio to structured writing instructions.
- `modules/core/prompt_builder.py:122` to `modules/core/prompt_builder.py:173` high-impact-zone guide computes front/back scene allocation from blueprint scene count.
- `modules/core/prompt_builder.py:451` to `modules/core/prompt_builder.py:489` writer guidance aggregator composes multiple pure guidance sections only when each sub-guide is available.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/prompt_builder.py:145` missing test for odd/even scene count split to verify per-scene allocation arithmetic.

### Round 24

**Read Files**: `modules/core/prompt_builder.py`

**Manual Inspection Evidence**:
- `modules/core/prompt_builder.py:514` to `modules/core/prompt_builder.py:560` app-aware arc-context builder uses cache keying and falls back to Python-derived context on extractor failure.
- `modules/core/prompt_builder.py:562` to `modules/core/prompt_builder.py:690` fallback context computes continuity locks from prior arcs, inventory, grants, and energy/injury/location summaries.
- `modules/core/prompt_builder.py:858` to `modules/core/prompt_builder.py:919` validation-context builder composes lore/HUD/history/NPC profiles with guarded POV extraction.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/prompt_builder.py:530` missing cache-behavior test that verifies `_cumulative_state_cache_key` hit/miss transitions across arc-count changes.

### Round 25

**Read Files**: `modules/core/stage4_post_processor.py`, `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage4_post_processor.py:38` to `modules/core/stage4_post_processor.py:55` DB-first commit and rollback policy is explicit before HUD update, preventing HUD/DB divergence on commit failure.
- `modules/core/stage4_post_processor.py:208` to `modules/core/stage4_post_processor.py:451` Episode Bible + world/fact ledger updates are chained with bounded fail-soft handling per subsystem.
- Caller-callee traced: stage4 loop hands PASS payload to post-processor in `modules/core/stage4_orchestrator.py:550`; session wrap-up path executes `run_post_episode_tasks` via `modules/core/stage4_orchestrator.py:568`.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/stage4_post_processor.py:614` session wrap-up waits on `input()`; in unattended execution environments this can block completion. Intent check: current flow is interactive CLI-oriented, so classified as risk.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/stage4_post_processor.py:49` missing integration test that simulates DB save exception and asserts rollback + `False` return propagation to stage4 loop.

### Round 26

**Read Files**: `modules/domain/agents/chief_writer.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/chief_writer.py:186` builds shared prompt context through `ChiefWriterContextBuilder` before candidate fan-out.
- `modules/domain/agents/chief_writer.py:252` to `modules/domain/agents/chief_writer.py:325` runs 3-strategy candidate generation in `ThreadPoolExecutor` and collects results via `as_completed`.
- `modules/domain/agents/chief_writer.py:341` to `modules/domain/agents/chief_writer.py:383` applies fallback generation and final candidate schema validation.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/chief_writer.py:279` `as_completed(timeout=...)` timeout does not hard-cancel running worker calls; long-running LLM calls can still delay executor shutdown. Intent check: code comments acknowledge this, but operational latency risk remains.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/chief_writer.py:314` missing timeout simulation test that verifies partial candidate collection behavior when only 일부 futures complete.

### Round 27

**Read Files**: `modules/domain/agents/chief_writer.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/chief_writer.py:416` to `modules/domain/agents/chief_writer.py:437` switches between cached-context ask and full-prompt fallback path.
- `modules/domain/agents/chief_writer.py:460` to `modules/domain/agents/chief_writer.py:473` normalizes non-string manuscript payloads (`list`/`dict`/other) before downstream critique.
- `modules/domain/agents/chief_writer.py:482` to `modules/domain/agents/chief_writer.py:505` self-critique parse is guarded and reverts to original candidate fields on parse failure.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/chief_writer.py:490` missing test for critique output where `content` is dict/list to verify normalization + title/state fallback.

### Round 28

**Read Files**: `modules/domain/agents/chief_writer.py`, `modules/core/prompt_loader.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/chief_writer.py:686` to `modules/domain/agents/chief_writer.py:733` patch mode loads `PATCH_MODE_PROMPT` and degrades to local fallback template on loader failure.
- `modules/domain/agents/chief_writer.py:735` to `modules/domain/agents/chief_writer.py:743` escapes braces in feedback/manuscript before template formatting to avoid placeholder collisions.
- Caller-callee contract traced: `patch_with_feedback` re-enters `generate_ensemble` at `modules/domain/agents/chief_writer.py:774` with narrowed single-strategy retry.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/chief_writer.py:745` missing test that forces prompt-loader failure and verifies patch fallback prompt still preserves core feedback fields.

### Round 29

**Read Files**: `modules/domain/agents/director.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/director.py:53` to `modules/domain/agents/director.py:64` director delegates major responsibilities to specialized subcomponents (caching, grading, continuity, auditor, ensemble).
- `modules/domain/agents/director.py:124` to `modules/domain/agents/director.py:176` manuscript/strategic audit methods are thin pass-through wrappers with full parameter forwarding.
- `modules/domain/agents/director.py:244` to `modules/domain/agents/director.py:257` ensemble selection wrapper passes mandatory context/history/story context into selector without local mutation.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/director.py:36` default assignment for `self.use_v0128` appears merged into comment region in this source view; if true at runtime, any early access before `set_v0128_enabled` could raise attribute errors. Intent check: may be display/encoding artifact, so treated as risk pending runtime-path confirmation.

**False Positives Excluded**:
- `modules/domain/agents/director.py:124` wrapper-heavy structure itself is intentional decomposition (not dead logic), so thin methods are not classified as defects.

**Test Gaps**:
- `modules/domain/agents/director.py:33` missing constructor test that asserts all expected runtime flags are initialized before first audit call.

### Round 30

**Read Files**: `modules/domain/agents/manager.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/manager.py:129` to `modules/domain/agents/manager.py:136` state/lore/seeds/history inputs are normalized before prompt assembly.
- `modules/domain/agents/manager.py:139` to `modules/domain/agents/manager.py:146` prompt template uses sequential `.replace()` expansion for placeholders.
- `modules/domain/agents/manager.py:149` to `modules/domain/agents/manager.py:158` model response is parsed via robust JSON extractor and returns parsing-error envelope on failure.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/manager.py:140` chained global `.replace()` can also replace placeholder-like tokens that appear inside already-inserted manuscript text, potentially mutating user content in prompt body. Intent check: current approach aims for simplicity after brace-escape removal, so treated as risk until input-domain constraints are explicit.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/manager.py:140` missing regression test where manuscript contains `{current_state_json}` literal to verify prompt substitution isolation.

## Checkpoint - Manual Round 30

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 0 (P0: 0, P1: 0, P2: 0, P3: 0) |
| Cumulative Risks | 10 |
| Cumulative False Positives Excluded | 3 |
| Cumulative Test Gaps | 30 |
| Phase False-Positive Ratio | 23.1% |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% |

### Round 31

**Read Files**: `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker.py:118` to `modules/domain/agents/state_tracker.py:183` constructor initializes core registries and composes NPC/financial/plots submodules as facade backends.
- `modules/domain/agents/state_tracker.py:184` to `modules/domain/agents/state_tracker.py:250` `full_extract_from_arcs` runs multi-extractor pipeline with per-step fail-soft `try/except` handling.
- `modules/domain/agents/state_tracker.py:247` to `modules/domain/agents/state_tracker.py:249` financial extraction is explicitly gated by `genre == "investment"`.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker.py:194` broad fail-soft blocks in initialization extraction can hide persistent parser regressions and continue with partial state; intent is resilience, so this is classified as operational risk, not immediate defect.

**False Positives Excluded**:
- `modules/domain/agents/state_tracker.py:248` investment-only financial extraction is intentional genre scoping, not missing coverage for non-investment arcs.

**Test Gaps**:
- `modules/domain/agents/state_tracker.py:194` missing test that injects extractor exceptions and asserts warning + continuation semantics with explicit degraded-state visibility.

### Round 32

**Read Files**: `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker.py:251` to `modules/domain/agents/state_tracker.py:285` tracking field defaults diverge by `PresetRegistry` availability and preserve backward-compatible baseline keys.
- `modules/domain/agents/state_tracker.py:317` to `modules/domain/agents/state_tracker.py:345` refresh path adds only missing fields and deep-copies defaults into both global field maps and existing NPC entries.
- `modules/domain/agents/state_tracker.py:352` to `modules/domain/agents/state_tracker.py:404` dynamic episode/NPC factory methods correctly route known attributes vs `extra_fields`.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/domain/agents/state_tracker.py:334` deep-copy usage for preset defaults is deliberate defensive handling for mutable defaults, not unnecessary duplication.

**Test Gaps**:
- `modules/domain/agents/state_tracker.py:341` missing regression test that proves newly activated NPC preset fields are backfilled into pre-existing `npc_registry` entries.

### Round 33

**Read Files**: `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker.py:405` to `modules/domain/agents/state_tracker.py:433` internal-energy parser normalizes int/float/percent-string and clamps to `0..100`.
- `modules/domain/agents/state_tracker.py:434` to `modules/domain/agents/state_tracker.py:460` non-numeric text fallback maps heuristic phrases to coarse bands before defaulting.
- `modules/domain/agents/state_tracker.py:462` to `modules/domain/agents/state_tracker.py:463` parser returns midpoint fallback (`50`) when no signal is found.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker.py:434` heuristic phrase mapping for narrative text can misclassify ambiguous descriptions (for example, mixed high/low cues in one sentence), which may propagate noisy energy continuity checks.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker.py:430` missing mixed-input tests for strings containing both numbers and descriptive qualifiers to verify deterministic precedence.

### Round 34

**Read Files**: `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker.py:465` to `modules/domain/agents/state_tracker.py:533` arc tactical doc loader seeds base episode state, parses per-episode data, tracks acquired/consumed items, then builds transitions.
- `modules/domain/agents/state_tracker.py:539` to `modules/domain/agents/state_tracker.py:577` per-episode parse starts from previous state snapshot and applies local updates plus checkpoint deltas.
- `modules/domain/agents/state_tracker.py:624` to `modules/domain/agents/state_tracker.py:641` acquisition/consumption episode inference falls back to arc start/end when explicit episode token is absent.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker.py:497` missing test that passes non-list `equipment` payload and asserts graceful empty-list normalization without contaminating weapon/item continuity.

### Round 35

**Read Files**: `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker.py:579` to `modules/domain/agents/state_tracker.py:613` text extractor updates injuries/items/weapons/location from regex pattern banks.
- `modules/domain/agents/state_tracker.py:615` to `modules/domain/agents/state_tracker.py:623` checkpoint application extracts explicit change blocks when tagged, otherwise parses full checkpoint text.
- `modules/domain/agents/state_tracker.py:570` to `modules/domain/agents/state_tracker.py:575` checkpoint matching is done via string-pattern containment over rendered episode marker tokens.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker.py:570` checkpoint token matching relies on rigid textual marker forms, so minor formatting drift in planner outputs may silently skip intended state applications.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker.py:570` missing parametrized tests for checkpoint marker variants (spacing, bracket style, localized token variants).

### Round 36

**Read Files**: `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker.py:643` to `modules/domain/agents/state_tracker.py:661` transition builder clears and reconstructs DAG edges by sorted episode numbers.
- `modules/domain/agents/state_tracker.py:662` to `modules/domain/agents/state_tracker.py:681` change computation covers location, weapon/item set changes, injuries, and internal energy deltas.
- `modules/domain/agents/state_tracker.py:669` to `modules/domain/agents/state_tracker.py:673` item/weapon comparisons are set-based to ignore list ordering noise.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/domain/agents/state_tracker.py:669` order-insensitive comparison is intentional continuity behavior; list reordering alone is not a defect.

**Test Gaps**:
- `modules/domain/agents/state_tracker.py:669` missing regression test that verifies pure reorder of weapons/items does not emit false transition change records.

### Round 37

**Read Files**: `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker.py:683` to `modules/domain/agents/state_tracker.py:710` timeline validation aggregates six rule families into issue list.
- `modules/domain/agents/state_tracker.py:712` to `modules/domain/agents/state_tracker.py:759` duplicate-acquisition and rapid-recovery checks use transition diffs + severity mapping.
- `modules/domain/agents/state_tracker.py:829` to `modules/domain/agents/state_tracker.py:849` weapon continuity flags all disappearing weapons as major issues.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker.py:839` unconditional major severity for every weapon disappearance can over-report when legitimate transfer/loss is implied elsewhere but not explicitly extracted.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker.py:839` missing precision test set that distinguishes explained weapon transfer vs unexplained disappearance severity.

### Round 38

**Read Files**: `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker.py:944` to `modules/domain/agents/state_tracker.py:1023` facade delegates NPC extraction/validation APIs to `StateTrackerNPC` backend without local mutation.
- `modules/domain/agents/state_tracker.py:1028` to `modules/domain/agents/state_tracker.py:1042` DB binding/history lookup APIs fail closed to empty structures when DB manager is absent.
- `modules/domain/agents/state_tracker.py:1048` to `modules/domain/agents/state_tracker.py:1210` financial/plots/time/commitment/emotion APIs are thin delegation surfaces preserving single-source submodule logic.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/domain/agents/state_tracker.py:972` wrapper-style method bodies are intentional facade seams and should not be flagged as dead or redundant code.

**Test Gaps**:
- `modules/domain/agents/state_tracker.py:1034` missing test for no-DB mode ensuring callers handle empty history/latest-field results consistently.

### Round 39

**Read Files**: `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker.py:1230` to `modules/domain/agents/state_tracker.py:1317` arc summary builder prioritizes NPCs referenced in `state_changes` before fallback to recent registry actors.
- `modules/domain/agents/state_tracker.py:1294` to `modules/domain/agents/state_tracker.py:1309` resolved/destroyed/active plots are filtered per arc and status.
- `modules/domain/agents/state_tracker.py:1319` to `modules/domain/agents/state_tracker.py:1355` prompt formatter limits output to recent 3 arcs and hard-truncates to 3000 chars.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker.py:1353` char-count truncation can clip structured context mid-section, reducing downstream prompt coherence under dense summaries.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker.py:1324` missing test that validates section ordering and truncation stability when each arc summary is near token budget.

### Round 40

**Read Files**: `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker.py:1361` to `modules/domain/agents/state_tracker.py:1406` unified state extraction composes 16 state-change buckets across NPC/plots/financial/time/commitment facets.
- `modules/domain/agents/state_tracker.py:1434` to `modules/domain/agents/state_tracker.py:1453` multi-arc builder merges per-arc states and transition lists without rebuilding cross-arc edges.
- `modules/domain/agents/state_tracker.py:643` to `modules/domain/agents/state_tracker.py:661` only `_build_transitions()` computes adjacency from sorted episodes, but this function is not called in `create_tracker_from_arcs`.

**Confirmed Bugs**:
- [P1-Continuity] `modules/domain/agents/state_tracker.py:1449` multi-arc aggregation omits boundary transition edges (for example, EP5->EP6), causing continuity validators to skip cross-arc diffs. Manual repro: two 5-episode arcs produce 10 states but only 8 transitions and no `5->6` edge. Intent check: the design intent is arc-spanning continuity validation, so boundary omission is a real defect, not a policy choice.

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker.py:1434` missing integration test that asserts `create_tracker_from_arcs` rebuilds complete `N-1` transitions across merged episode ranges.

## Checkpoint - Manual Round 40

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 1 (P0: 0, P1: 1, P2: 0, P3: 0) |
| Cumulative Risks | 15 |
| Cumulative False Positives Excluded | 7 |
| Cumulative Test Gaps | 40 |
| Phase False-Positive Ratio | 30.4% |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% |

### Round 41

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:20` to `modules/domain/agents/state_tracker_npc.py:67` module-level compiled regex banks are predeclared for relationship/injury/movement/companion/permanent-injury extraction.
- `modules/domain/agents/state_tracker_npc.py:70` to `modules/domain/agents/state_tracker_npc.py:87` submodule is a pure facade backend using `self.tracker` shared state.
- `modules/domain/agents/state_tracker_npc.py:73` to `modules/domain/agents/state_tracker_npc.py:83` genre-specific skill log labels normalize logging semantics across presets.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:21` missing performance-regression test proving module-level compiled patterns prevent per-arc recompilation overhead.

### Round 42

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:92` to `modules/domain/agents/state_tracker_npc.py:117` `_record_change` performs DB write-through with fail-soft warning fallback.
- `modules/domain/agents/state_tracker_npc.py:122` to `modules/domain/agents/state_tracker_npc.py:143` `register_npc_death` updates registry state and records status transition history.
- `modules/domain/agents/state_tracker_npc.py:145` to `modules/domain/agents/state_tracker_npc.py:197` `register_npc_info` writes field-level deltas only when value actually changed.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:173` missing test that verifies no duplicate DB history row is emitted when incoming NPC field value is unchanged.

### Round 43

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:199` to `modules/domain/agents/state_tracker_npc.py:275` NPC weapon/level drift checker emits WARNING-level change envelopes using regex matches against new arc content.
- `modules/domain/agents/state_tracker_npc.py:213` to `modules/domain/agents/state_tracker_npc.py:216` weapon extraction uses narrow suffix-based pattern assumptions.
- `modules/domain/agents/state_tracker_npc.py:249` to `modules/domain/agents/state_tracker_npc.py:257` level parsing compensates for swapped regex group ordering.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_npc.py:213` static weapon/level pattern bank is genre-biased and may produce noisy warnings when tactical text style diverges from assumed noun endings.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:231` missing test where regex captures a known NPC nickname to validate false-warning suppression against canonical name mapping.

### Round 44

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:277` to `modules/domain/agents/state_tracker_npc.py:336` `extract_npc_info_from_arc` loads tactical text and extracts weapon/level fields into registry.
- `modules/domain/agents/state_tracker_npc.py:291` to `modules/domain/agents/state_tracker_npc.py:292` non-`wuxia` genre short-circuits extraction by design.
- `modules/domain/agents/state_tracker_npc.py:313` to `modules/domain/agents/state_tracker_npc.py:315` exclusion list removes generic nouns before registration.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/domain/agents/state_tracker_npc.py:291` genre gate that returns empty for non-`wuxia` is intentional anti-noise policy, not a missing implementation bug.

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:291` missing policy test that ensures non-`wuxia` flows keep extracting other state domains while skipping only weapon/level regex.

### Round 45

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:342` to `modules/domain/agents/state_tracker_npc.py:365` standalone-name validator checks both left/right Hangul boundaries with particle allowlist.
- `modules/domain/agents/state_tracker_npc.py:367` to `modules/domain/agents/state_tracker_npc.py:428` dead-NPC appearance detector blocks post-death action usage while allowing flashback/remembrance contexts.
- `modules/domain/agents/state_tracker_npc.py:388` to `modules/domain/agents/state_tracker_npc.py:417` enforcement requires both standalone-name hit and action-token confirmation.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_npc.py:407` action-pattern containment is lexical and may still over-trigger for quoted planning/meta text that is not actual in-scene reappearance.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:403` missing negative test set for memorial-dialogue variants to verify flashback exemption precision.

### Round 46

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:434` to `modules/domain/agents/state_tracker_npc.py:447` protagonist-skill registration is idempotent and genre-tagged in logs.
- `modules/domain/agents/state_tracker_npc.py:449` to `modules/domain/agents/state_tracker_npc.py:484` unlearned-skill checker intentionally emits INFO-level suspicious records instead of hard reject.
- `modules/domain/agents/state_tracker_npc.py:486` to `modules/domain/agents/state_tracker_npc.py:526` entity registry export consolidates dead NPCs, NPC snapshots, known skills, and latest protagonist inventory.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:515` missing test ensuring `protagonist_items` export handles duplicate overlap between `items` and `weapons` deterministically.

### Round 47

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:528` to `modules/domain/agents/state_tracker_npc.py:559` registry merge preserves dead-state dominance and applies filtered updates for empty/zero/False values.
- `modules/domain/agents/state_tracker_npc.py:536` to `modules/domain/agents/state_tracker_npc.py:541` existing dead NPC cannot be overwritten by non-dead incoming snapshot.
- `modules/domain/agents/state_tracker_npc.py:545` to `modules/domain/agents/state_tracker_npc.py:552` filtered merge skips destructive empty-value overwrites.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_npc.py:550` conditional skip for integer `0` updates can also suppress legitimate zero-valued resets in future numeric fields if schema expands.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:545` missing merge-matrix test across `(existing value, incoming value)` combinations including `0`, `False`, empty string, and `None`.

### Round 48

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:564` to `modules/domain/agents/state_tracker_npc.py:634` death extraction prioritizes `state_changes.npc_deaths` then falls back to regex + optional LLM verification.
- `modules/domain/agents/state_tracker_npc.py:636` to `modules/domain/agents/state_tracker_npc.py:684` LLM verifier constrains output to candidate intersection and falls back to raw candidates on failure.
- `modules/domain/agents/state_tracker_npc.py:625` to `modules/domain/agents/state_tracker_npc.py:633` verified candidates are registered with arc-context death metadata.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_npc.py:672` on empty/invalid LLM response, verifier returns unfiltered regex candidates (fail-open), which can reintroduce generic-noun false positives.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:672` missing test that simulates malformed LLM JSON and validates downstream guardrails against bulk false death registration.

### Round 49

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:686` to `modules/domain/agents/state_tracker_npc.py:737` skill-acquisition extraction follows state-changes-first then regex fallback.
- `modules/domain/agents/state_tracker_npc.py:738` to `modules/domain/agents/state_tracker_npc.py:788` relationship changes are reflected both in result payload and NPC registry relation fields.
- `modules/domain/agents/state_tracker_npc.py:749` to `modules/domain/agents/state_tracker_npc.py:780` regex fallback is only entered when no structured relationship changes were extracted.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:772` missing mixed-source test where state_changes has partial relationship entries and regex fallback should decide whether to supplement or stay exclusive.

### Round 50

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:790` to `modules/domain/agents/state_tracker_npc.py:836` NPC injury extraction updates registry from structured data, else regex fallback.
- `modules/domain/agents/state_tracker_npc.py:838` to `modules/domain/agents/state_tracker_npc.py:884` movement extraction mirrors same precedence contract (state_changes first, regex only if empty).
- `modules/domain/agents/state_tracker_npc.py:820` to `modules/domain/agents/state_tracker_npc.py:883` regex fallback results also mutate tracker registry (`injury`/`location`).

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_npc.py:821` precedence policy is all-or-nothing; when structured list is partially populated, regex supplementation is skipped and incremental signals can be dropped.

**False Positives Excluded**:
- `modules/domain/agents/state_tracker_npc.py:820` fallback deferral when structured state exists is intentional trust-priority toward planner JSON, not a parsing omission by itself.

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:821` missing hybrid-input test proving expected behavior when one NPC injury is present in state_changes and another appears only in tactical prose.

## Checkpoint - Manual Round 50

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 1 (P0: 0, P1: 1, P2: 0, P3: 0) |
| Cumulative Risks | 20 |
| Cumulative False Positives Excluded | 9 |
| Cumulative Test Gaps | 50 |
| Phase False-Positive Ratio | 30.0% |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% |

### Round 51

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:890` to `modules/domain/agents/state_tracker_npc.py:929` relationship-regex extractor applies three pattern families and deduplicates per NPC.
- `modules/domain/agents/state_tracker_npc.py:904` to `modules/domain/agents/state_tracker_npc.py:913` arrow-style relation transitions carry both `from` and `to` states.
- `modules/domain/agents/state_tracker_npc.py:916` to `modules/domain/agents/state_tracker_npc.py:927` reconcile/betray patterns produce canonical relation shifts for simplified signals.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:901` missing test ensuring dedupe keying by NPC does not erase legitimately distinct multi-step relation transitions inside one arc.

### Round 52

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:931` to `modules/domain/agents/state_tracker_npc.py:980` injury-regex extractor normalizes forward/reverse forms and maps generic injury token to light injury.
- `modules/domain/agents/state_tracker_npc.py:945` to `modules/domain/agents/state_tracker_npc.py:950` extraction iterates compiled pattern tuples with optional default state injection.
- `modules/domain/agents/state_tracker_npc.py:974` to `modules/domain/agents/state_tracker_npc.py:978` output dedupes by NPC name via `seen` set.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_npc.py:974` per-NPC dedupe can collapse multiple injury-state changes in the same arc into one record, reducing temporal fidelity.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:974` missing test with one NPC receiving sequential injury escalations to verify whether only final or all states should persist.

### Round 53

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:982` to `modules/domain/agents/state_tracker_npc.py:1024` movement-regex extractor handles from-to, to-only, and leave-only movement phrase families.
- `modules/domain/agents/state_tracker_npc.py:996` to `modules/domain/agents/state_tracker_npc.py:1023` each pattern writes a normalized `{name, from, to}` payload with dedupe.
- `modules/domain/agents/state_tracker_npc.py:989` to `modules/domain/agents/state_tracker_npc.py:990` empty tactical input is explicitly short-circuited.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:1006` missing test that checks precedence when both from-to and to-only patterns match the same sentence for one NPC.

### Round 54

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:1030` to `modules/domain/agents/state_tracker_npc.py:1065` permanent-injury register validates injury type, deduplicates `(description, arc_no)`, and persists per NPC.
- `modules/domain/agents/state_tracker_npc.py:1067` to `modules/domain/agents/state_tracker_npc.py:1104` extraction prefers structured `state_changes.permanent_injuries` and early-returns once populated.
- `modules/domain/agents/state_tracker_npc.py:1117` to `modules/domain/agents/state_tracker_npc.py:1153` regex fallback classifies amputation/blindness/scar with normalized descriptions.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:1053` missing duplicate-guard test covering same description across different arcs to confirm intended per-arc retention behavior.

### Round 55

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:1156` to `modules/domain/agents/state_tracker_npc.py:1177` permanent-injury summary emits prompt-ready lines and returns empty string when none exist.
- `modules/domain/agents/state_tracker_npc.py:1183` to `modules/domain/agents/state_tracker_npc.py:1224` `revive_npc` requires explicit call, restores alive status, and stores recovery audit history.
- `modules/domain/agents/state_tracker_npc.py:1195` to `modules/domain/agents/state_tracker_npc.py:1202` revival is rejected for unknown/already-alive NPCs.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_npc.py:1183` revival accepts any free-form reason string and has no policy hook, so accidental operator misuse can silently undo critical death constraints.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:1215` missing audit test that ensures each revival append keeps prior history immutable and ordered.

### Round 56

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:1230` to `modules/domain/agents/state_tracker_npc.py:1327` blueprint dead-NPC guard merges integrated scenario + scene breakdown text then applies boundary/flashback/action checks.
- `modules/domain/agents/state_tracker_npc.py:1329` to `modules/domain/agents/state_tracker_npc.py:1411` manuscript dead-NPC guard mirrors blueprint flow with broader flashback/action token bank.
- `modules/domain/agents/state_tracker_npc.py:1245` to `modules/domain/agents/state_tracker_npc.py:1249` arc number is inferred from input when not explicitly supplied.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_npc.py:1384` manuscript action-pattern list is broad substring matching and may still produce context-ambiguous CRITICAL flags in quoted narration/planning prose.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:1258` missing test for mixed `scene_breakdown` container types (list+dict-style content variants) to ensure deterministic content merge coverage.

### Round 57

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:1436` to `modules/domain/agents/state_tracker_npc.py:1455` personality-change extractor maps `state_changes` entries into registry via `register_npc_info`.
- `modules/domain/agents/state_tracker_npc.py:1479` to `modules/domain/agents/state_tracker_npc.py:1495` NPC-NPC relationship extraction normalizes dict payloads then routes through relationship registry update.
- `modules/domain/agents/state_tracker_npc.py:1497` to `modules/domain/agents/state_tracker_npc.py:1510` relationship register stores sorted-pair key and keeps limited history metadata (`prev_relation`, `prev_arc`).

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/domain/agents/state_tracker_npc.py:1508` 50-entry cap in NPC-NPC relationship cache is intentional bounded-memory policy, not unintended data loss bug.

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:1508` missing boundary test asserting deterministic eviction order when relationship map exceeds cap.

### Round 58

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:1527` to `modules/domain/agents/state_tracker_npc.py:1541` dialogue-style registration merges incoming fields with existing profile to avoid blank overwrite.
- `modules/domain/agents/state_tracker_npc.py:1542` to `modules/domain/agents/state_tracker_npc.py:1601` dialogue-style extraction prioritizes explicit `npc_dialogue_profiles` and backfills from personality traits only when explicit profile is absent.
- `modules/domain/agents/state_tracker_npc.py:1603` to `modules/domain/agents/state_tracker_npc.py:1620` summary builder emits only profiles with at least one concrete style attribute.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/domain/agents/state_tracker_npc.py:1566` trait-to-dialogue heuristic mapping is an intentional fallback inference path, not a deterministic characterization bug.

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:1572` missing precedence test confirming explicit `npc_dialogue_profiles` always override personality-derived style inference.

### Round 59

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:1626` to `modules/domain/agents/state_tracker_npc.py:1673` companion update flow applies state_changes-first policy and regex fallback.
- `modules/domain/agents/state_tracker_npc.py:1675` to `modules/domain/agents/state_tracker_npc.py:1684` companion state mutation is action-based (`join` append, `leave` filter-out).
- `modules/domain/agents/state_tracker_npc.py:1686` to `modules/domain/agents/state_tracker_npc.py:1719` regex extraction dedupes names across join/leave pattern families.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_npc.py:1698` shared dedupe set across join and leave patterns can suppress second event when same NPC is both joined and left in one tactical block.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:1701` missing scenario test for same-arc join+leave mentions to verify expected final companion state.

### Round 60

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:1750` to `modules/domain/agents/state_tracker_npc.py:1843` protagonist-emotion extraction/normalization updates tracker state via structured payload or regex fallback.
- `modules/domain/agents/state_tracker_npc.py:1873` to `modules/domain/agents/state_tracker_npc.py:1922` relationship/injury/movement/protagonist-skill summaries are formatted for mandatory context injection with bounded slices.
- `modules/domain/agents/state_tracker_npc.py:1928` to `modules/domain/agents/state_tracker_npc.py:2006` periodic LLM cleanup removes candidate generic nouns from alive NPC registry with fail-soft exception handling.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_npc.py:1989` single-pass LLM cleanup can delete valid alive NPCs if model returns false positives, with no confidence threshold or human confirmation gate.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:1989` missing safety test that enforces allowlist/protected-name behavior during LLM-driven cleanup.

## Checkpoint - Manual Round 60

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 1 (P0: 0, P1: 1, P2: 0, P3: 0) |
| Cumulative Risks | 25 |
| Cumulative False Positives Excluded | 11 |
| Cumulative Test Gaps | 60 |
| Phase False-Positive Ratio | 29.7% |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% |

### Round 61

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:14` to `modules/domain/agents/state_tracker_plots.py:52` module-level compiled regex constants define shared extraction patterns for destroyed entities, time checks, item events, and commitments.
- `modules/domain/agents/state_tracker_plots.py:55` to `modules/domain/agents/state_tracker_plots.py:85` submodule is state facade around `self.tracker` with explicit time-pattern banks.
- `modules/domain/agents/state_tracker_plots.py:58` to `modules/domain/agents/state_tracker_plots.py:82` time marker families are partitioned by elapsed/season/day/date signal classes.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:58` missing test that validates each time-pattern family triggers only its intended marker type without cross-class leakage.

### Round 62

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:91` to `modules/domain/agents/state_tracker_plots.py:118` resolved-plot extractor upserts by `(plot, arc_no)` dedupe key.
- `modules/domain/agents/state_tracker_plots.py:120` to `modules/domain/agents/state_tracker_plots.py:131` resolved-plot summary renders prompt-friendly chronology.
- `modules/domain/agents/state_tracker_plots.py:137` to `modules/domain/agents/state_tracker_plots.py:162` entity-destruction extraction writes normalized records and dedupes by `(name, arc_no)`.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_plots.py:113` dedupe on plot+arc can mask distinct resolution details for repeated same-arc updates if downstream wants revision history fidelity.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:113` missing test for duplicate plot key with differing resolution payload in same arc.

### Round 63

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:164` to `modules/domain/agents/state_tracker_plots.py:169` manual entity-destruction register uses name-based dedupe guard.
- `modules/domain/agents/state_tracker_plots.py:170` to `modules/domain/agents/state_tracker_plots.py:199` destroyed-entity manuscript guard checks activity/revival patterns per destroyed entity name.
- `modules/domain/agents/state_tracker_plots.py:201` to `modules/domain/agents/state_tracker_plots.py:210` destruction summary enforces reactivation prohibition context in prompt text.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/domain/agents/state_tracker_plots.py:183` regex warning on destroyed-entity activity is intentional conservative guardrail and should not be auto-classified as deterministic defect.

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:184` missing tests for quoted historical references to destroyed entities to separate narration from active-world actions.

### Round 64

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:216` to `modules/domain/agents/state_tracker_plots.py:236` item-state register preserves previous condition transitions for change traceability.
- `modules/domain/agents/state_tracker_plots.py:237` to `modules/domain/agents/state_tracker_plots.py:281` item-state extraction follows state_changes-first then regex fallback.
- `modules/domain/agents/state_tracker_plots.py:265` to `modules/domain/agents/state_tracker_plots.py:279` fallback only activates when no structured `major_items` extraction result exists.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_plots.py:266` all-or-nothing fallback means partially populated structured item lists suppress regex supplementation and may miss additional item transitions.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:266` missing hybrid-source test for partial `major_items` plus additional prose-only item events.

### Round 65

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:283` to `modules/domain/agents/state_tracker_plots.py:295` item summary renders condition-centric active-state guidance.
- `modules/domain/agents/state_tracker_plots.py:301` to `modules/domain/agents/state_tracker_plots.py:315` active plot register tracks first mention, latest mention, and status transitions.
- `modules/domain/agents/state_tracker_plots.py:316` to `modules/domain/agents/state_tracker_plots.py:350` arc update path marks resolved plots and revives suspended plots when re-mentioned.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:345` missing test that suspended plot status flips back to `active` only when canonical plot name match occurs.

### Round 66

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:352` to `modules/domain/agents/state_tracker_plots.py:371` suspended-plot detector marks stale unresolved plots by arc-gap threshold.
- `modules/domain/agents/state_tracker_plots.py:373` to `modules/domain/agents/state_tracker_plots.py:401` suspension summary partitions suspended vs active plot lists.
- `modules/domain/agents/state_tracker_plots.py:359` to `modules/domain/agents/state_tracker_plots.py:361` status mutation to `suspended` occurs in-place during warning generation.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_plots.py:361` warning-generation side effect mutates canonical status, so repeated check calls can alter state without explicit workflow commit step.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:352` missing idempotency test for repeated suspension checks on unchanged arc number.

### Round 67

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:407` to `modules/domain/agents/state_tracker_plots.py:441` time-marker register enforces marker-type whitelist, dedupe, and 100-entry retention cap.
- `modules/domain/agents/state_tracker_plots.py:442` to `modules/domain/agents/state_tracker_plots.py:470` structured time-marker extraction writes canonical arc/episode/type/description records.
- `modules/domain/agents/state_tracker_plots.py:472` to `modules/domain/agents/state_tracker_plots.py:508` regex time extraction fills elapsed/season/day/date classes from tactical prose.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:439` missing cap-behavior test that verifies oldest timeline markers are evicted in FIFO order after 100 entries.

### Round 68

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:481` to `modules/domain/agents/state_tracker_plots.py:506` regex fallback stores inferred time markers with `episode=arc_no`.
- `modules/domain/agents/state_tracker_plots.py:510` to `modules/domain/agents/state_tracker_plots.py:536` timeline summary emits last 20 markers with type labels.
- `modules/domain/agents/state_tracker_plots.py:538` to `modules/domain/agents/state_tracker_plots.py:620` time-consistency checker raises rapid-recovery, season contradiction, and impossible-travel warnings.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_plots.py:484` regex-derived markers stamping `episode=arc_no` can blur episode granularity and degrade chronology precision in long arcs.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:484` missing regression test that verifies downstream consumers tolerate arc-level placeholder episodes from prose-only extraction.

### Round 69

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:626` to `modules/domain/agents/state_tracker_plots.py:665` major-item regex extractor separates acquire/loss dedupe sets to allow dual-state capture.
- `modules/domain/agents/state_tracker_plots.py:649` to `modules/domain/agents/state_tracker_plots.py:663` exclusion set filters generic words before materializing item events.
- `modules/domain/agents/state_tracker_plots.py:640` to `modules/domain/agents/state_tracker_plots.py:643` independent seen sets preserve both acquisition and loss events for same item name.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/domain/agents/state_tracker_plots.py:642` separate `seen_acquire`/`seen_lose` is intentional dual-event modeling, not duplicate-event bug.

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:651` missing test where one item is acquired then lost in same arc to confirm both events remain serialized.

### Round 70

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:671` to `modules/domain/agents/state_tracker_plots.py:708` commitment register dedupes by `(description, arc_no)` and trims registry when oversized.
- `modules/domain/agents/state_tracker_plots.py:709` to `modules/domain/agents/state_tracker_plots.py:765` commitment extraction supports both `commitments` and `promises_obligations`.
- `modules/domain/agents/state_tracker_plots.py:767` to `modules/domain/agents/state_tracker_plots.py:811` regex fallback commitment extractor applies bounded description length and inferred participant list.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:727` missing compatibility test ensuring both legacy and new analyst schema fields merge without duplicate commitment rows.

## Checkpoint - Manual Round 70

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 1 (P0: 0, P1: 1, P2: 0, P3: 0) |
| Cumulative Risks | 29 |
| Cumulative False Positives Excluded | 13 |
| Cumulative Test Gaps | 70 |
| Phase False-Positive Ratio | 30.2% |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% |

### Round 71

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:813` to `modules/domain/agents/state_tracker_plots.py:830` commitment resolver uses bidirectional substring matching for fulfillment.
- `modules/domain/agents/state_tracker_plots.py:832` to `modules/domain/agents/state_tracker_plots.py:854` commitment summary reports pending obligations with optional deadline hints.
- `modules/domain/agents/state_tracker_plots.py:823` to `modules/domain/agents/state_tracker_plots.py:827` first matching pending commitment is fulfilled and returns early.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_plots.py:826` bidirectional substring resolve logic can fulfill unintended similarly-worded commitments when descriptions overlap.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:826` missing ambiguity test where two pending commitments share long common prefixes.

### Round 72

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:860` to `modules/domain/agents/state_tracker_plots.py:876` entity-name registry tracks type/first/last arc with LRU eviction.
- `modules/domain/agents/state_tracker_plots.py:877` to `modules/domain/agents/state_tracker_plots.py:900` loader imports external entity registry categories into canonical name registry.
- `modules/domain/agents/state_tracker_plots.py:867` to `modules/domain/agents/state_tracker_plots.py:872` registry schema uses list-based aliases for JSON-safe serialization.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:874` missing eviction-order test for boundary crossing at `_entity_registry_max_size`.

### Round 73

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:901` to `modules/domain/agents/state_tracker_plots.py:944` entity-name consistency checker uses prefix-derived variant detection with dedupe controls.
- `modules/domain/agents/state_tracker_plots.py:918` to `modules/domain/agents/state_tracker_plots.py:923` variant detection composes regex from canonical prefix + short Hangul suffix.
- `modules/domain/agents/state_tracker_plots.py:925` to `modules/domain/agents/state_tracker_plots.py:935` warning dedupe keys include canonical/variant pair and global seen match set.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/domain/agents/state_tracker_plots.py:930` small-length-difference rule is a heuristic consistency warning policy, not deterministic naming bug.

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:922` missing test corpus for short-name entities to verify false-warning rate under prefix similarity.

### Round 74

**Read Files**: `modules/core/world_state.py`

**Manual Inspection Evidence**:
- `modules/core/world_state.py:20` to `modules/core/world_state.py:38` world-state init schema defines protagonist/NPC/item/plot/destroyed structures.
- `modules/core/world_state.py:52` to `modules/core/world_state.py:63` loader restores `world_state` anchor or falls back to deep-copied init schema.
- `modules/core/world_state.py:64` to `modules/core/world_state.py:70` save path persists anchor with error logging on failure.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/world_state.py:56` missing migration test for partially-populated legacy anchor payloads without required keys.

### Round 75

**Read Files**: `modules/core/world_state.py`

**Manual Inspection Evidence**:
- `modules/core/world_state.py:75` to `modules/core/world_state.py:124` state-change updater processes deaths, skills, and relationship deltas with per-entry normalization.
- `modules/core/world_state.py:139` to `modules/core/world_state.py:155` major-item updates map acquire/lost/consumed actions into active-item status transitions.
- `modules/core/world_state.py:156` to `modules/core/world_state.py:177` destroyed entities are appended with duplicate-name guard and capped list retention.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/world_state.py:166` destroyed-entity dedupe by name only can suppress distinct repeated-destruction events across episodes when same entity is rebuilt then destroyed again.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/world_state.py:166` missing lifecycle test for rebuild-and-redestroy scenarios on identical entity names.

### Round 76

**Read Files**: `modules/core/world_state.py`

**Manual Inspection Evidence**:
- `modules/core/world_state.py:178` to `modules/core/world_state.py:194` personality updates support both new and legacy field names (`traits/motivation` and compatibility aliases).
- `modules/core/world_state.py:195` to `modules/core/world_state.py:207` resolved plots remove matching active-plot entries.
- `modules/core/world_state.py:209` to `modules/core/world_state.py:230` companion updates and list caps are applied at end of unified update path.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/world_state.py:195` resolved-plot handling only subtracts from `active_plots` and does not add newly activated plots from state changes, creating potential stale under-reporting unless external calls add them.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/world_state.py:205` missing end-to-end test that validates `active_plots` lifecycle when only state_changes input is provided.

### Round 77

**Read Files**: `modules/core/world_state.py`

**Manual Inspection Evidence**:
- `modules/core/world_state.py:239` to `modules/core/world_state.py:255` protagonist-state updater mutates only supplied fields and stamps episode.
- `modules/core/world_state.py:260` to `modules/core/world_state.py:289` summary builder emits protagonist section with bounded skill list.
- `modules/core/world_state.py:290` to `modules/core/world_state.py:335` alive/dead NPC and item sections are rendered with section-level caps.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/world_state.py:282` missing test for injury summary suppression when protagonist injury state returns to normal.

### Round 78

**Read Files**: `modules/core/world_state.py`

**Manual Inspection Evidence**:
- `modules/core/world_state.py:337` to `modules/core/world_state.py:350` destroyed locations/orgs and active plot summary sections are appended in deterministic order.
- `modules/core/world_state.py:354` to `modules/core/world_state.py:357` long summaries are truncated with explicit omission marker.
- `modules/core/world_state.py:408` to `modules/core/world_state.py:426` rollback resets state and replays episode-bible `state_changes` up to target episode.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/world_state.py:421` rollback replays only `state_changes` and may miss any world-state updates applied through direct helper APIs outside episode_bible content.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/world_state.py:417` missing replay parity test comparing pre-rollback and post-replay states for mixed update paths.

### Round 79

**Read Files**: `modules/core/world_state.py`

**Manual Inspection Evidence**:
- `modules/core/world_state.py:368` to `modules/core/world_state.py:406` utility accessors expose last-updated ep, alive NPC registration, active-plot insertion, and defensive deep-copy state export.
- `modules/core/world_state.py:386` to `modules/core/world_state.py:403` active-plot helper dedupes by plot name and caps list size to 30.
- `modules/core/world_state.py:405` to `modules/core/world_state.py:406` `get_state_dict` guarantees copy semantics through JSON round-trip.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/core/world_state.py:355` summary truncation behavior is intentional prompt-budget control, not accidental data corruption.

**Test Gaps**:
- `modules/core/world_state.py:392` missing test that validates active-plot dedupe and cap logic under repeated identical insert attempts.

### Round 80

**Read Files**: `modules/core/world_state.py`, `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- Caller-callee contract manually checked: time/plot/item data produced by `modules/domain/agents/state_tracker_plots.py:442`, `modules/domain/agents/state_tracker_plots.py:709`, `modules/domain/agents/state_tracker_plots.py:237` can be consumed by world-state updater categories in `modules/core/world_state.py:75`.
- `modules/core/world_state.py:226` to `modules/core/world_state.py:230` world-state global caps align with bounded-memory intent used across plot/NPC trackers.
- `modules/core/world_state.py:364` to `modules/core/world_state.py:426` summary and rollback utility paths provide operational recovery hooks independent from extraction modules.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/world_state.py:75` missing integration test wiring real `state_tracker_plots` output payloads into `update_from_state_changes`.

## Checkpoint - Manual Round 80

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 1 (P0: 0, P1: 1, P2: 0, P3: 0) |
| Cumulative Risks | 33 |
| Cumulative False Positives Excluded | 15 |
| Cumulative Test Gaps | 80 |
| Phase False-Positive Ratio | 30.6% |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% |

### Round 81

**Read Files**: `modules/core/fact_ledger.py`

**Manual Inspection Evidence**:
- `modules/core/fact_ledger.py:20` to `modules/core/fact_ledger.py:22` fact-ledger limits define per-entity history cap and summary size cap.
- `modules/core/fact_ledger.py:35` to `modules/core/fact_ledger.py:49` loader performs schema backfill for missing keys and falls back safely on DB errors.
- `modules/core/fact_ledger.py:50` to `modules/core/fact_ledger.py:67` empty schema and save path are centralized for persistence consistency.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/fact_ledger.py:47` DB load failures silently reinitialize to empty ledger, which can mask storage outages and appear as narrative memory loss unless monitored.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/fact_ledger.py:40` missing migration test that verifies backfill correctness when one or more top-level buckets are absent in persisted anchor.

### Round 82

**Read Files**: `modules/core/fact_ledger.py`

**Manual Inspection Evidence**:
- `modules/core/fact_ledger.py:77` to `modules/core/fact_ledger.py:143` update flow ingests NPC deaths, relationships, skills, and major item transitions from `state_changes`.
- `modules/core/fact_ledger.py:91` to `modules/core/fact_ledger.py:103` death records accept both dict and string forms and append causal notes.
- `modules/core/fact_ledger.py:118` to `modules/core/fact_ledger.py:129` skill acquisitions are normalized as protagonist-owned item-like entries.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/fact_ledger.py:102` missing test that distinguishes dict-supplied death causes from string-only fallback path.

### Round 83

**Read Files**: `modules/core/fact_ledger.py`

**Manual Inspection Evidence**:
- `modules/core/fact_ledger.py:144` to `modules/core/fact_ledger.py:157` entity destructions branch by type into organization/location upsert paths.
- `modules/core/fact_ledger.py:158` to `modules/core/fact_ledger.py:203` injuries, movements, personality, and npc-npc relations are recorded as character history notes.
- `modules/core/fact_ledger.py:205` sets `last_updated_ep` after full update sweep.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/fact_ledger.py:176` movement updates are stored as free-form history note only and do not update a canonical location field, reducing structured queryability.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/fact_ledger.py:202` missing test for bidirectional NPC-NPC relation note symmetry and duplication bounds.

### Round 84

**Read Files**: `modules/core/fact_ledger.py`

**Manual Inspection Evidence**:
- `modules/core/fact_ledger.py:207` to `modules/core/fact_ledger.py:242` bible-delta updater ingests new/lost entities with typed fallback handling.
- `modules/core/fact_ledger.py:247` to `modules/core/fact_ledger.py:262` numeric ledger updater stores value/unit transitions with bounded history.
- `modules/core/fact_ledger.py:259` to `modules/core/fact_ledger.py:261` number history retains only recent entries under configured cap.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/core/fact_ledger.py:129` modeling skill acquisitions through item bucket is intentional unified ledger abstraction, not category mix-up defect.

**Test Gaps**:
- `modules/core/fact_ledger.py:257` missing test for number updates that repeat same value with and without explicit note.

### Round 85

**Read Files**: `modules/core/fact_ledger.py`

**Manual Inspection Evidence**:
- `modules/core/fact_ledger.py:267` to `modules/core/fact_ledger.py:292` character upsert initializes schema once and appends bounded note history.
- `modules/core/fact_ledger.py:293` to `modules/core/fact_ledger.py:313` item upsert tracks owner/status evolution with established and last episode markers.
- `modules/core/fact_ledger.py:282` to `modules/core/fact_ledger.py:291` optional status/role/relationship mutations preserve partial-update semantics.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/fact_ledger.py:282` missing test that confirms omitted optional fields do not erase previously stored values on upsert.

### Round 86

**Read Files**: `modules/core/fact_ledger.py`

**Manual Inspection Evidence**:
- `modules/core/fact_ledger.py:314` to `modules/core/fact_ledger.py:333` location upsert updates status/current owner with bounded history.
- `modules/core/fact_ledger.py:334` to `modules/core/fact_ledger.py:347` organization upsert mirrors location path for status/leader.
- `modules/core/fact_ledger.py:325` to `modules/core/fact_ledger.py:343` mutations are guarded by truthy checks before field overwrite.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/fact_ledger.py:327` truthy-only update guards prevent explicit clearing of owner/leader fields (empty-string reset cannot be persisted).

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/fact_ledger.py:327` missing test for explicit field-clear operations (non-empty to empty transition) on location/org ownership metadata.

### Round 87

**Read Files**: `modules/core/fact_ledger.py`

**Manual Inspection Evidence**:
- `modules/core/fact_ledger.py:353` to `modules/core/fact_ledger.py:398` summary builder emits alive/dead character sections with relationship and death-cause hints.
- `modules/core/fact_ledger.py:399` to `modules/core/fact_ledger.py:424` item section splits active vs lost/destroyed items.
- `modules/core/fact_ledger.py:480` to `modules/core/fact_ledger.py:483` summary truncation enforces maximum character budget.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/fact_ledger.py:392` missing test verifying death-cause extraction from history when multiple death-related notes exist.

### Round 88

**Read Files**: `modules/core/fact_ledger.py`

**Manual Inspection Evidence**:
- `modules/core/fact_ledger.py:425` to `modules/core/fact_ledger.py:468` summary prints location/org sections with destroyed vs active partitioning.
- `modules/core/fact_ledger.py:469` to `modules/core/fact_ledger.py:479` numeric facts are summarized with unit and last update episode.
- `modules/core/fact_ledger.py:481` to `modules/core/fact_ledger.py:482` overflow summaries are trimmed with explicit truncation suffix.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/core/fact_ledger.py:481` summary truncation is intentional prompt-size governance, not loss-of-source-truth since canonical ledger remains intact.

**Test Gaps**:
- `modules/core/fact_ledger.py:472` missing ordering test for numeric summary output under high-entity counts to ensure deterministic rendering.

### Round 89

**Read Files**: `modules/core/fact_ledger.py`

**Manual Inspection Evidence**:
- `modules/core/fact_ledger.py:489` to `modules/core/fact_ledger.py:519` query utilities provide character/item lookups plus aggregate stats.
- `modules/core/fact_ledger.py:521` to `modules/core/fact_ledger.py:540` rollback resets ledger and replays episode bible `state_changes` + `bible_delta`.
- `modules/core/fact_ledger.py:530` to `modules/core/fact_ledger.py:537` replay pipeline processes both state-change and delta inputs per episode.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/fact_ledger.py:537` replaying both sources may duplicate semantically identical notes when one event exists in both payloads, increasing history noise over long runs.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/fact_ledger.py:537` missing rollback replay test that asserts dedupe expectations for duplicated event sources.

### Round 90

**Read Files**: `modules/domain/agents/state_tracker_plots.py`, `modules/core/world_state.py`, `modules/core/fact_ledger.py`

**Manual Inspection Evidence**:
- Cross-module flow manually traced: state-change extractors in `modules/domain/agents/state_tracker_plots.py:237`, `modules/domain/agents/state_tracker_plots.py:709` feed world/fact update paths in `modules/core/world_state.py:75` and `modules/core/fact_ledger.py:77`.
- Bounded-memory intent consistency checked: `modules/domain/agents/state_tracker_plots.py:438`, `modules/core/world_state.py:227`, `modules/core/fact_ledger.py:20`.
- Syntax/runtime viability sanity checked via compilation of all three modules after manual read.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/world_state.py:75` missing integration test suite validating end-to-end coherence between plot extraction outputs and both world/fact ledger projections.

## Checkpoint - Manual Round 90

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 1 (P0: 0, P1: 1, P2: 0, P3: 0) |
| Cumulative Risks | 37 |
| Cumulative False Positives Excluded | 17 |
| Cumulative Test Gaps | 90 |
| Phase False-Positive Ratio | 30.9% |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% |

### Round 91

**Read Files**: `scripts/validate_manual_sweep.py`

**Manual Inspection Evidence**:
- `scripts/validate_manual_sweep.py:19` to `scripts/validate_manual_sweep.py:63` round splitter indexes markdown by `### Round N` headings and preserves per-round blocks.
- `scripts/validate_manual_sweep.py:66` to `scripts/validate_manual_sweep.py:88` section/bullet extractor is heading-driven and stops on next section boundary.
- `scripts/validate_manual_sweep.py:99` to `scripts/validate_manual_sweep.py:138` round validator enforces mandatory sections, evidence count, file:line references, and tool-output-only evidence rejection.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `scripts/validate_manual_sweep.py:71` missing parser test for markdown variants with extra blank lines or mixed heading capitalization.

### Round 92

**Read Files**: `scripts/validate_manual_sweep.py`

**Manual Inspection Evidence**:
- `scripts/validate_manual_sweep.py:141` to `scripts/validate_manual_sweep.py:157` metrics counter treats confirmed bugs as severity-tagged entries and counts other sections by non-`none` bullets.
- `scripts/validate_manual_sweep.py:160` to `scripts/validate_manual_sweep.py:206` FP checkpoint reporter computes cumulative ratios and streak progression per interval.
- `scripts/validate_manual_sweep.py:208` to `scripts/validate_manual_sweep.py:215` threshold-violation generation is explicit for both ratio and streak caps.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `scripts/validate_manual_sweep.py:193` fp-only streak increment logic is an intentional policy metric (tracking review behavior), not a miscount bug.

**Test Gaps**:
- `scripts/validate_manual_sweep.py:201` missing regression test for non-default checkpoint interval behavior (for example, interval 5 or 20).

### Round 93

**Read Files**: `scripts/validate_manual_sweep.py`

**Manual Inspection Evidence**:
- `scripts/validate_manual_sweep.py:222` to `scripts/validate_manual_sweep.py:255` CLI options expose round range, empty allowance, checkpoint interval, and FP guard thresholds.
- `scripts/validate_manual_sweep.py:264` to `scripts/validate_manual_sweep.py:265` validator reads markdown as UTF-8 with `errors="replace"` before split/parse.
- `scripts/validate_manual_sweep.py:296` to `scripts/validate_manual_sweep.py:311` exit path separates format-invalid, FP-threshold-violated, and success outcomes.

**Confirmed Bugs**:
- none

**Risks**:
- `scripts/validate_manual_sweep.py:264` using `errors="replace"` can mask underlying encoding corruption by silently substituting characters, reducing strict encoding-failure visibility.

**False Positives Excluded**:
- none

**Test Gaps**:
- `scripts/validate_manual_sweep.py:264` missing test that feeds invalid UTF-8 bytes and asserts expected failure/warning semantics.

### Round 94

**Read Files**: `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker.py:643` to `modules/domain/agents/state_tracker.py:661` `_build_transitions` is the sole adjacency builder from sorted episode keys.
- `modules/domain/agents/state_tracker.py:1434` to `modules/domain/agents/state_tracker.py:1453` multi-arc tracker creation merges per-arc states/transitions without calling `_build_transitions` on merged state.
- `modules/domain/agents/state_tracker.py:1449` merged transition list therefore remains per-arc-local and depends on source trackers' precomputed edges only.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker.py:1434` missing regression test that asserts cross-arc boundary edge creation after multi-arc merge.

### Round 95

**Read Files**: `modules/core/world_state.py`

**Manual Inspection Evidence**:
- `modules/core/world_state.py:408` to `modules/core/world_state.py:416` rollback resets in-memory state to init schema before replay.
- `modules/core/world_state.py:417` to `modules/core/world_state.py:425` replay loop iterates episode bibles up to target and reapplies `state_changes`.
- `modules/core/world_state.py:426` persisted save is executed after replay completes.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/world_state.py:419` replay quality depends on full episode-bible availability; missing/intermittent DB records lead to silently partial restoration despite successful rollback completion.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/world_state.py:417` missing fault-injection test for sparse/missing episode bible rows during rollback replay.

### Round 96

**Read Files**: `modules/core/fact_ledger.py`

**Manual Inspection Evidence**:
- `modules/core/fact_ledger.py:521` to `modules/core/fact_ledger.py:529` rollback resets ledger then replays prior episode data.
- `modules/core/fact_ledger.py:530` to `modules/core/fact_ledger.py:537` each replay iteration applies both `state_changes` and `update_from_bible_delta`.
- `modules/core/fact_ledger.py:540` rollback concludes with persistence save.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/core/fact_ledger.py:537` missing replay consistency test comparing pre-rollback snapshot vs post-rollback replay for identical target episode.

### Round 97

**Read Files**: `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_npc.py:1183` to `modules/domain/agents/state_tracker_npc.py:1224` manual NPC revival flow requires explicit invocation and writes revival audit entries.
- `modules/domain/agents/state_tracker_npc.py:1928` to `modules/domain/agents/state_tracker_npc.py:1949` LLM cleanup is guarded by minimum alive-name count and client availability checks.
- `modules/domain/agents/state_tracker_npc.py:1987` to `modules/domain/agents/state_tracker_npc.py:1994` cleanup applies destructive registry deletes on model-provided remove list for alive NPCs.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_npc.py:1989` destructive cleanup delete path lacks protected-name/confirmation guard, so model misclassification can erase valid alive NPC records.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_npc.py:1990` missing safety test with protected canonical NPC names under adversarial cleanup response payload.

### Round 98

**Read Files**: `modules/domain/agents/state_tracker_plots.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/state_tracker_plots.py:813` to `modules/domain/agents/state_tracker_plots.py:830` commitment resolver uses fuzzy substring matching and first-hit fulfillment.
- `modules/domain/agents/state_tracker_plots.py:767` to `modules/domain/agents/state_tracker_plots.py:811` regex commitment extractor truncates descriptions and infers parties heuristically.
- `modules/domain/agents/state_tracker_plots.py:832` to `modules/domain/agents/state_tracker_plots.py:854` summary renders pending commitments for mandatory context enforcement.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/agents/state_tracker_plots.py:826` fuzzy resolve rule can match unintended pending commitments with overlapping phrasing, causing premature fulfillment state changes.

**False Positives Excluded**:
- none

**Test Gaps**:
- `modules/domain/agents/state_tracker_plots.py:823` missing disambiguation tests for multiple commitments sharing partial lexical overlap.

### Round 99

**Read Files**: `scripts/validate_manual_sweep.py`, `modules/domain/agents/state_tracker_npc.py`

**Manual Inspection Evidence**:
- `scripts/validate_manual_sweep.py:264` validator performs explicit UTF-8 read path, which aligns with document encoding policy checks.
- `modules/domain/agents/state_tracker_npc.py:630` verified via UTF-8 strict read that source line retains intact Korean token (`LLM검증`) despite terminal mojibake display under non-UTF8 code page.
- `scripts/validate_manual_sweep.py:257` to `scripts/validate_manual_sweep.py:262` argument validation already fails fast for missing file/invalid interval, supporting strict run hygiene.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/domain/agents/state_tracker_npc.py:630` garbled Korean text seen in PowerShell output is a console code-page artifact, not source-file encoding corruption.

**Test Gaps**:
- `scripts/validate_manual_sweep.py:264` missing explicit encoding smoke test that asserts U+FFFD count remains zero for target sweep documents.

### Round 100

**Read Files**: `docs/codex_findings_sweep100_manual.md`, `scripts/validate_manual_sweep.py`

**Manual Inspection Evidence**:
- `docs/codex_findings_sweep100_manual.md:1` to final section manually revalidated for round structure continuity and required section presence through Round 100.
- `scripts/validate_manual_sweep.py:99` to `scripts/validate_manual_sweep.py:138` round-level contract checks match documented manual-only sweep policy.
- `scripts/validate_manual_sweep.py:160` to `scripts/validate_manual_sweep.py:219` interim FP settlement logic is aligned with 10-round checkpoint reporting cadence used in this document.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- none

**Test Gaps**:
- `scripts/validate_manual_sweep.py:222` missing CI-level guard that auto-runs 1~100 validation on each document update commit.

## Checkpoint - Manual Round 100

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 1 (P0: 0, P1: 1, P2: 0, P3: 0) |
| Cumulative Risks | 41 |
| Cumulative False Positives Excluded | 19 |
| Cumulative Test Gaps | 100 |
| Phase False-Positive Ratio | 31.1% |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% |
