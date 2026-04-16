# 0_0-stage234-arc23-post-patch-rerun-proof Execution SSOT

Date: 2026-04-16
Status: active (3-pass audited; operator explicitly authorized the formal Arc2/3 post-patch rerun/replay proof lane on the current workspace)
Canonical Path: `docs/2026-04-16/0_0-stage234-arc23-post-patch-rerun-proof-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage234-arc23-post-patch-rerun-proof-execution-ssot.md`
Commit State:
- Baseline Commit: `cf744f871d3fd0d98d51e0fda7c83de8024f143b`
- Baseline Dirty Summary: `dirty: active user/live-run drift (`0_temp.txt`, `config/style_references/investment/style_guide.json`), local Stage2 patch/test files, legacy project deletions, and untracked 2026-04-16 audit docs already present in worktree`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none; this execution SSOT is opened against the same audited workspace state`
Source Survey Docs:
- `docs/2026-04-16/stage234-arc23-stage2-packet-fidelity-focused-3pass-audit.md`
- `docs/2026-04-16/stage234-s2-s3-s4-global-parallel-adversarial-3pass-audit.md`
- `docs/2026-04-16/stage234-s2-s3-s4-bounded-live-merge-post-run-merge-audit.md`
Evidence Artifacts:
- `0_temp.txt`
- `projects/00_260416/project_data.db`
- `projects/00_260416/logs/session_20260416_111959.log`
- `projects/00_260416/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/00_260416/logs/artifacts/stage2/arc_003/attempt_01/final_arc__balanced.json`
- `modules/core/stage2_finalizer.py`
- `modules/core/cross_stage_authority_packet.py`
- `modules/core/episode_state_arbiter.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_post_pass_runtime.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage3_blueprint_state_precision_guardrail.py`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py`
- `tests/test_chief_writer_context.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_stage4_interview_round.py`
Side-Effect Coverage: covered (Stage2 finalization and packet rebuild, Stage3 carryforward consume, Stage4 numeric/location consume, runtime artifact generation, DB/log persistence, post-run audit closure)
Confidence: `96%`

## 1. Intent

Realize the next formal proof lane after the global parallel adversarial audit:

- bounded `Arc2/3` post-patch rerun/replay proof

This lane exists because:

- the current global audit does not justify `P1` or a broad `Stage234` reopen
- the strongest unresolved risk is still persisted `Arc2/3` Stage2 packet fidelity loss
- the latest Stage2 patch materially improves forward repair, but has not yet been proven against a post-patch Arc2/3 proof lane

This lane is not:

- a hidden `Stage234` reopen
- a broad new code tranche
- a substitute for the already-closed realized Arc1 live lane

## 2. Baseline Facts

1. The current global `S2 -> S3 -> S4` read is `P2 watch`, not `P1`.
2. The realized fresh-run lane (`Stage2 -> Stage3 ep1~ep5 -> Stage4 ep1~ep2`) closed as a bounded success.
3. Arc2/3 selected PASS Stage2 artifacts still persist stale structured closure surfaces:
   - location surfaces remain `알 수 없음`
   - `numeric_carryover` remains empty
4. The latest Stage2 patch now promotes bounded tactical `[종료 상태]` truth into structured end-state surfaces when those surfaces are still blank or placeholder-like.
5. Broad downstream numeric-consumer guardrails are green, but no post-patch Arc2/3 realized proof exists yet.
6. The operator has now explicitly authorized the formal proof route for this bounded lane.

## 3. Scope

Included:

- bounded Stage2 Arc2/3 rerun or replay proof against the patched finalizer path
- structured closure truth verification for location, equipment, and numeric carryover
- bounded Stage3/S4 downstream consume spot-checks against the repaired packet surfaces
- post-run merge audit and queue-state closure for this lane

Excluded:

- broad `Stage234` architecture reopening
- `ep9` continuation or wider Stage3 rollback proof
- retroactive in-place rewriting of old saved artifacts without a new proof run
- unrelated Stage4 redesign or non-Arc2/3 runtime work

## 4. Pass 1. Inventory Summary

### Runtime proof surfaces

- Stage2 selected artifacts for `Arc2` and `Arc3`
- packet build and finalization path in `stage2_finalizer.py`
- downstream packet consumers in `EpisodeStateArbiter`, Stage3 prompt/context builders, and Stage4 context/post-pass handlers

### Owner-pressure summary

- highest-risk owner lane: Stage2 structured end-state promotion before packet build
- supporting downstream verification lane: Stage3/Stage4 consume parity

### Live-vs-static split

- static evidence already confirms the historical loss and the bounded patch shape
- this execution lane exists to add realized post-patch proof, not to reopen the survey question from zero

## 5. Pass 2. Semantic Classification

### Class A. Upstream proof

Goal:

- show that patched Stage2 now lifts tactical end-state truth into structured packet surfaces for Arc2/3

Primary surfaces:

- `modules/core/stage2_finalizer.py`
- Arc2/3 rerun or replay artifacts

### Class B. Downstream consume proof

Goal:

- verify that repaired packet truth actually reaches Stage3/Stage4 consumers without new regressions

Primary surfaces:

- `modules/core/episode_state_arbiter.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_post_pass_runtime.py`

### Class C. Closure proof

Goal:

- merge runtime evidence back into one bounded post-run audit and decide whether Arc2/3 risk is closed, reduced, or still open fail-only

Primary surfaces:

- bounded post-run merge audit doc
- active roadmap / temp queue state

## 6. Side-Effect Map

- file writes / artifacts:
  - expected new Stage2/Stage3/Stage4 proof artifacts only if the runtime lane is executed
- DB / schema / transaction boundaries:
  - project DB writes are expected during proof execution; no schema change is part of this lane
- JSONL / log / audit sinks:
  - runtime/session/metrics/pass-rate artifacts may update during proof execution
- console / UI / operator output:
  - runtime progress, verdicts, and post-run summaries are expected
- rollback / recovery / retry:
  - bounded runtime retries are allowed inside the proof lane; broad reopen is not
- cache / global state:
  - only normal runtime state for the selected proof project; no new global cache contract work
- bootstrap fallback / config-env mutation:
  - not applicable

## 7. Realization Architecture

This lane should stay runtime-first and bounded.

Preferred sequence:

1. preserve the current evidence baseline and choose the smallest replay/rerun mode that still exercises the patched finalizer on Arc2/3
2. verify Stage2 packet surfaces directly on the newly produced artifacts
3. spot-check Stage3/S4 consumer surfaces only as far as needed to prove repaired carryforward transport
4. close the lane with one merged post-run audit instead of reopening broad survey work

The lane is successful even if it ends in a fail-only closure, as long as the fail point is bounded and owner-specific.

## 8. Execution Tranches

1. `Preflight and evidence freeze`
   - preserve current audit anchors
   - choose bounded Arc2/3 replay or rerun mode
   - confirm target project/runtime entrypoint
2. `Arc2/3 Stage2 proof`
   - run patched Arc2/3 materialization
   - inspect structured location/equipment/numeric packet surfaces
3. `Downstream consume spot-check`
   - verify Stage3/Stage4 packet intake from the new outputs
   - rerun narrow regression tests if needed
4. `Closure`
   - write the bounded post-run merge audit
   - refresh roadmap and temp queue state

## 9. Acceptance Criteria

- Arc2/3 post-patch artifacts no longer leave concrete tactical closing location trapped behind `알 수 없음` when the closure text is parseable
- Arc2/3 post-patch packet surfaces no longer leave numeric carryover empty when structured totals are recoverable from the bounded tactical end-state promotion path
- no regression appears in authoritative empty inventory clear handling
- downstream Stage3/S4 consume paths accept the repaired packet surfaces without introducing a new broad failure mode
- closure clearly records one of:
  - `risk reduced / closed in bounded scope`
  - `owner remains Stage2 with a narrower fail-only residual`

## 10. Verification Plan

- `python scripts/check_utf8_hygiene.py docs/2026-04-16/0_0-stage234-arc23-post-patch-rerun-proof-execution-ssot.md docs/temp/0_0-stage234-arc23-post-patch-rerun-proof-execution-ssot.md`
- `python scripts/ops_validator.py --strict`
- `python -m pytest tests/test_stage2_finalizer.py -q`
- `python -m pytest tests/test_stage3_blueprint_state_precision_guardrail.py -k prefers_cross_stage_numeric_carryover -q`
- `python -m pytest tests/test_stage3_npc_capital_carryforward_guardrail.py -q`
- `python -m pytest tests/test_stage4_context_builder.py -k "numeric_carryover_authority_packet or cross_stage_authority_packet" -q`
- bounded Arc2/3 runtime proof plus artifact diff review
- final bounded post-run merge audit

## 11. Guardrails

- do not widen this lane into a broad `Stage234` reopen
- do not claim full closure until new Arc2/3 proof artifacts exist
- do not overwrite unrelated user/live-run drift
- do not treat historical Arc1 success as substitute evidence for Arc2/3 repair
- if replay mode is sufficient to exercise the patched finalizer faithfully, prefer it over a wider fresh run

## 12. Temp Queue Notes

- temp status: in_progress
- cleanup condition: remove the temp mirror only after Arc2/3 proof closes and the roadmap is refreshed
- roadmap dependency: top bounded follow-up lane after the 2026-04-16 global parallel adversarial audit

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run this document's 3-pass audit against the live workspace state and refresh resume metadata before starting runtime from it
