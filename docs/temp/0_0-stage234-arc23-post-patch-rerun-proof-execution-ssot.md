# 0_0-stage234-arc23-post-patch-rerun-proof Execution SSOT

Date: 2026-04-16
Status: partially_realized (3-pass re-audited through the 2026-04-17 Stage34 demo frontier follow-up; Stage2 Arc2/3 post-patch proof remains green, the previously bounded Stage3 boundary residual is now cleared in bounded scope, and the remaining open blocker is the single-episode Stage34 demo frontier/source-contract mismatch on the current `ep7` lineage)
Canonical Path: `docs/2026-04-16/0_0-stage234-arc23-post-patch-rerun-proof-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage234-arc23-post-patch-rerun-proof-execution-ssot.md`
Commit State:
- Baseline Commit: `cf744f871d3fd0d98d51e0fda7c83de8024f143b`
- Baseline Dirty Summary: `dirty: active user/live-run drift (`0_temp.txt`, `config/style_references/investment/style_guide.json`), local Stage2 patch/test files, legacy project deletions, and untracked 2026-04-16 audit docs already present in worktree`
- Resume Commit: `6325ad427afd75c73abc37b32b29ec217ffe2f9a`
- Resume Drift Summary: `current resume head is the user-requested merged branch head; fresh proof evidence now exists under the Arc2/3 canary chain (`stage34_ep7_r1`, `stage34_ep7_r2`, `stage34_ep7_r3`, `stage3_ep7_r2`, `stage3_from_stage3r1_ep7_r1`, and `stage3_from_stage3r1_ep7_r2`), and the lane's current authoritative state is no longer the earlier Stage3 residual handoff but the narrower Stage34 single-episode demo frontier/source-contract blocker after the exact-lineage Stage3 follow-up and the partial `r3` runtime inspection landed`
Source Survey Docs:
- `docs/2026-04-16/stage234-arc23-stage2-packet-fidelity-focused-3pass-audit.md`
- `docs/2026-04-16/stage234-s2-s3-s4-global-parallel-adversarial-3pass-audit.md`
- `docs/2026-04-16/stage234-s2-s3-s4-bounded-live-merge-post-run-merge-audit.md`
- `docs/2026-04-16/stage234-arc23-postpatch-proof-session-context.md`
- `docs/2026-04-16/stage234-arc23-post-patch-rerun-proof-post-run-merge-audit.md`
- `docs/2026-04-17/stage234-arc23-stage34-single-episode-demo-frontier-context.md`
- `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
Evidence Artifacts:
- `0_temp.txt`
- `projects/00_260416/project_data.db`
- `projects/00_260416/logs/session_20260416_111959.log`
- `projects/00_260416/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- `projects/00_260416/logs/artifacts/stage2/arc_003/attempt_01/final_arc__balanced.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_r1/logs/stage3_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r1/logs/stage34_ep_demo_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/project_data.db`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/stage34_ep_demo_canary_prep.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/stage34_ep_demo_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/pass_rate_monitor.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/quality_metrics.jsonl`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/session/ui_events.jsonl`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/session_20260416_182308.log`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r3/project_data.db`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r3/logs/episode_production.jsonl`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r3/logs/pass_rate_monitor.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r3/logs/session_20260417_083723.log`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_ep7_r2/logs/stage3_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r1/logs/stage3_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r1/logs/session/ui_events.jsonl`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2/logs/stage3_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2/logs/session/ui_events.jsonl`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2/logs/session/llm_io.jsonl`
- `modules/core/stage2_finalizer.py`
- `modules/core/cross_stage_authority_packet.py`
- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_post_pass_runtime.py`
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_stage3_blueprint_state_precision_guardrail.py`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py`
- `tests/test_chief_writer_context.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_stage4_interview_round.py`
Side-Effect Coverage: covered (Stage2 finalization and packet rebuild, Stage3 carryforward consume, Stage3 prompt/fact-lock compilation, Stage4 numeric/location consume, runtime artifact generation, DB/log persistence, bounded test execution, and post-run audit closure)
Confidence: `97%`

Authoritative Override Note:

- Section `14` preserves the immediate clean `stage34_ep7_r2` post-run merge read.
- Section `15` is now the active override for the formerly open Stage3 boundary residual after the exact failed-lineage Stage3 follow-up landed and passed.

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

- temp status: partially_realized
- cleanup condition: keep the temp mirror until the single-episode Stage34 demo source-contract blocker is either resolved or explicitly demoted by a later canonical roadmap update
- roadmap dependency: bounded Arc2/3 proof lane stays active until the Stage34 demo source-contract blocker is resolved or the utility contract is revised

## 13. Validation and Closure Hooks

- validator command: `python scripts/ops_validator.py --strict`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run this document's 3-pass audit against the live workspace state and refresh resume metadata before starting runtime from it

## 14. 2026-04-16 Post-Run Merge Closure Note (Historical)

Runtime result captured:

- the fresh `r2` replay reached a terminal state
- Stage3 `ep7` ended `FAILED` on attempt `10`
- the bounded failure family was `arc_timeline` plus `opening_transition`
- no new Stage4 `ep7` row, draft, or manuscript was persisted

What this changes:

- the lane is no longer intent-only; it now has a bounded post-run merge audit and fresh runtime evidence
- the earlier Arc2/3 Stage2 proof remains authoritative and does not reopen
- the active residual is reassigned to the Stage3 Arc2-opening boundary lane plus the single-episode Stage34 demo source-contract blocker (`frozen_authority_draft_missing:ep6`)

Current operating consequence:

1. do not reopen Stage2 packet work from this result alone
2. do not treat the Stage34 single-episode demo utility as closure-grade for `ep7` on the current source lineage
3. route the next bounded action to the existing Stage3 opening-transition / boundary-contract lane before deciding whether another downstream Arc2/3 replay is still warranted

## 15. 2026-04-16 Exact Failed-Lineage Stage3 Follow-up Override

Runtime/code result captured:

- the first packet-side follow-up was necessary but not sufficient: `stage3_from_stage3r1_ep7_r1` still ended `FAILED` even though `episode_state_packet_summary.time_source` had already switched to `arc_data.state_changes.timeline`
- prompt evidence on that failed lineage showed the previous blueprint's opening-specific location/time/ending-hook anchors still being emitted as immutable `[FACT-LOCK]` truth
- the bounded compiler follow-up now suppresses those previous-opening immutable anchors when authoritative arc-opening location/timeline truth already exists and surfaces `opening.transition_expectation` into the prompt packet render path
- the fresh exact-lineage rerun `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2` now records `ep7` as `PASS` with score `95`, attempt `2`, `prevalidation = 0`, `binding = 0`, and `sink_alignment_summary.status = ok`

What this changes:

- the earlier Stage3 `arc_timeline` / `opening_transition` residual is no longer the active blocker for this lane
- Stage2 proof remains green and is now joined by exact-lineage Stage3 positive proof
- the remaining blocker for closure-grade downstream replay is the Stage34 single-episode demo utility's source-contract requirement (`frozen_authority_draft_missing:ep6`)

Current operating consequence:

1. do not reopen Stage3 opening-transition work from the historical clean `stage34_ep7_r2` failure alone
2. keep this Arc2/3 proof lane bounded and `partially_realized` until the Stage34 demo source-contract blocker is resolved or the utility contract is explicitly revised
3. if another downstream replay is attempted, do it only after frozen-authority `ep6` availability or an explicit utility-contract change

## 16. 2026-04-17 Stage34 Single-Episode Demo Frontier Mismatch Override

Runtime/code result captured:

- the Stage34 demo utility follow-up now supports sparse-target Stage4 analysis and can downgrade exact frozen-authority absence to warning when earlier authority history exists
- the fresh canary `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r3` was prepared from `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2` and launched with `target_ep = 7`
- that source lineage still had `blueprints 1..7` but only `manuscripts 1..2`, so the effective Stage4 start frontier remained `ep3`
- the live run therefore entered sequential Stage4 catch-up through lower episodes instead of an `ep7`-only proof surface; the user aborted the long run and the still-live `python` process had to be stopped explicitly afterward
- partial `r3` evidence now records manuscripts through `ep3`, Stage4 attempts through `ep4`, and no final `stage34_ep_demo_canary_summary.json`
- `scripts/run_stage34_ep_demo_canary.py` now fails fast before the live run if the resolved Stage4 `start_ep` does not equal the requested `target_ep`

What this changes:

- the active downstream blocker is no longer well-described as only `frozen_authority_draft_missing:ep6`
- the stronger and current authoritative reading is a broader Stage34 single-episode demo frontier/source-contract mismatch on this `ep7` lineage
- `stage34_ep7_r3` is a partial evidence canary that proves the contract mismatch; it is not a clean closure-grade proof target

Current operating consequence:

1. do not reuse `stage34_ep7_r3` as the next clean replay target
2. do not queue another downstream replay from the same non-aligned source lineage without either frontier-aligned source preparation or a deeper sparse-Stage4 runner revision
3. keep this Arc2/3 proof lane bounded and `partially_realized` while the next action chooses between source realignment and deeper runner-contract revision
