# Stage234 Arc2/3 Post-Patch Rerun Proof Post-Run Merge Audit

Date: 2026-04-16
Status: final (3-pass re-audited after the clean `r2` Stage34 downstream consume replay and the exact failed-lineage Stage3 follow-up)
Canonical Path: `docs/2026-04-16/stage234-arc23-post-patch-rerun-proof-post-run-merge-audit.md`
Commit State:
- Baseline Commit: `6325ad427afd75c73abc37b32b29ec217ffe2f9a`
- Baseline Dirty Summary: `clean tracked worktree on branch codex/post-merge-authority-drift-refresh before fresh runtime proof`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `fresh runtime and bounded follow-up evidence now exists under the Arc2/3 canary chain (`stage34_ep7_r1`, `stage34_ep7_r2`, `stage3_ep7_r2`, `stage3_from_stage3r1_ep7_r1`, and `stage3_from_stage3r1_ep7_r2`); the historical clean Stage34 replay failure is preserved, while the current authoritative read now also includes the bounded Stage3 packet/prompt follow-up that cleared the earlier exact-lineage boundary residual without resolving the single-episode demo source-contract blocker`
Source Survey Docs:
- `docs/2026-04-16/0_0-stage234-arc23-post-patch-rerun-proof-execution-ssot.md`
- `docs/2026-04-16/stage234-arc23-postpatch-proof-session-context.md`
- `docs/2026-04-16/stage234-arc23-stage2-packet-fidelity-focused-3pass-audit.md`
- `docs/2026-04-16/stage234-s2-s3-s4-global-parallel-adversarial-3pass-audit.md`
- `docs/implementation/live-run-merge-survey-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
Evidence Artifacts:
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_r1/project_data.db`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_r1/logs/stage3_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r1/logs/stage34_ep_demo_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/project_data.db`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/stage34_ep_demo_canary_prep.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/stage34_ep_demo_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/pass_rate_monitor.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/quality_metrics.jsonl`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/session/ui_events.jsonl`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2/logs/session_20260416_182308.log`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_ep7_r2/logs/stage3_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r1/logs/stage3_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r1/logs/session/ui_events.jsonl`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2/logs/stage3_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2/logs/session/ui_events.jsonl`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2/logs/session/llm_io.jsonl`
- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_stage3_blueprint_state_precision_guardrail.py`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py`
Side-Effect Coverage: covered for fresh canary project copies, Stage3 packet assembly, Stage3 prompt/fact-lock compilation, Stage3 runtime retries, Stage4 initialization/context loading, DB/log/metrics persistence, bounded test execution, and downstream proof summarization; no schema change occurred in this lane
Confidence: `97%`

Authoritative Override Note:

- Sections `2-7` preserve the immediate clean `stage34_ep7_r2` post-run merge read.
- Section `8` is now the authoritative update for the previously open Stage3 boundary residual after the exact failed-lineage Stage3 follow-up landed and passed.

## 1. Intent

This audit merges the already-recorded Arc2/3 post-patch proof anchors with the fresh downstream consume replay attempted on `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2`.

It answers four bounded questions:

1. does the earlier Arc2/3 Stage2 post-patch proof remain intact on the current head?
2. does a clean downstream consume rerun for `ep7` reach a new Stage3 or Stage4 success state?
3. if the downstream consume rerun fails, which owner lane does the failure belong to?
4. does the result justify reopening Stage2 packet work or a broader Stage234 runtime lane?

This audit does not claim:

- full Stage234 closure
- a broad Stage4 reopen
- a new Stage2 code tranche

## 2. Final Verdict

### Finding 1. The Arc2/3 Stage2 post-patch proof remains green in bounded scope

Severity: none

The earlier formal proof anchors still hold:

- the `r1` Arc2/3 Stage2 rerun completed successfully
- Arc2 carryover surfaces now populate concrete tactical/location/numeric truth instead of leaving the historical blank packet state
- Arc3 carryover surfaces likewise populate the repaired numeric/location lineage

The fresh downstream follow-up did not produce any evidence that reopens the Stage2 finalizer patch itself.

Operational meaning:

- the current failure is not a Stage2 packet-regression reopen
- the Stage2 patch stays realized and bounded-green on the current head

### Finding 2. The clean `r2` downstream consume replay fails in Stage3 before any new Stage4 `ep7` artifact is persisted

Severity: medium

The fresh `r2` replay reached a terminal state, but not a success state.

Authoritative terminal anchors:

- `pass_rate_monitor.json` records one new Stage3 row for `ep7` with `attempt_key = s3:ep7:arc2:a10:20260416_182309`
- that row ends `success = false` / `final_verdict = FAILED`
- the same row records `attempt_num = 10`, `duration_ms = 3490712`, and `token_cost = 3.01549`
- `stage34_ep_demo_canary_summary.json` upgrades the run into a final summary and records `ep7_final_verdict: FAILED`

The runtime failure family is bounded and explicit:

- `arc_timeline`
- `opening_transition`
- time-background contradiction (`January` wording against Arc2's `February` frame)
- `opening_transition.type` contradiction (`direct_continuation` vs `explicit_transition`)

No new Stage4 `ep7` success evidence was written:

- the summary still reports `stage4_latest_session_id = 20260416_112003`
- `draft_count` remains `2`
- Stage4 rows remain the historical `ep1~ep2` set rather than a fresh `ep7` proof

Operational meaning:

- the downstream consume proof did not close
- the fresh failure belongs to the Stage3 boundary/transition lane, not to a new Stage4 sink regression

### Finding 3. The single-episode Stage34 demo utility remains structurally partial for this Arc2/3 lane

Severity: medium

The clean `r2` replay also confirms a utility-contract blocker that already existed in the aborted `r1` target:

- `stage34_ep_demo_canary_summary.json` reports `demo_boundary_status: fail`
- the concrete boundary error is `frozen_authority_draft_missing:ep6`
- no project in the current Arc2/3 proof lineage carries a frozen `ep6` draft authority surface

This means the utility can still generate bounded evidence, but it cannot currently satisfy its own clean single-episode boundary contract for `ep7`.

Operational meaning:

- a fresh target is cleaner than the aborted one, but it does not remove this source-lineage blocker
- repeated Stage34 single-episode reruns on the same source shape should not be treated as closure-quality evidence until the frozen-authority contract is resolved or intentionally revised

## 3. Pass 1. Prior Proof Anchor Recheck

The post-run merge audit did not start from zero.

Existing bounded anchors already established:

- `r1` Stage2 Arc2/3 post-patch rerun success
- Arc2 structured totals populated at `23억원`
- Arc3 structured totals populated at `30억원`
- Stage3-only consume spot-check success recorded once in `stage3_r1`, including one earlier `ep7` PASS

Those facts remain authoritative because the current workspace head is unchanged code-wise from the branch the user asked to resume (`6325ad42`) and the fresh `r2` follow-up produced no code diff.

Pass 1 conclusion:

- the fresh consume failure is a new bounded downstream result layered on top of an already-green Stage2 proof anchor
- the correct question is therefore owner reassignment, not "did Stage2 ever repair anything?"

## 4. Pass 2. Fresh `r2` Runtime Evidence Merge

The clean replay sequence was:

1. prepare fresh target `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage34_ep7_r2`
2. run one bounded `ep7` Stage3 -> Stage4 single-episode demo
3. analyze the completed target

What the run actually did:

- Stage3 spent ten attempts on `ep7`
- UI/session evidence records a terminal `FAILED (attempt=10, score=85)` result
- the reject family stayed bounded to timeline/opening-transition contradiction and regenerate-only repair demand
- after the Stage3 failure, the runtime entered Stage4 initialization/context loading, but no new Stage4 `ep7` row or draft was persisted

Important merge fact:

- the fresh replay does not contradict the earlier Stage2 proof
- it does contradict the hope that a clean downstream replay would simply inherit the earlier one-off Stage3 success

So the post-run merge conclusion is not "everything stayed green" and not "the whole lane collapsed."

It is:

- Stage2 proof remains green
- Stage3 reproducibility at the Arc2 opening seam remains unstable
- Stage4 was never given a fresh successful `ep7` blueprint/draft pair to close on

## 5. Pass 3. Owner and Scope Decision

The bounded owner read after merge is:

### 5.1 Not a Stage2 reopen

Why not:

- no new Arc2/3 packet fidelity regression surfaced
- the fresh failure reason is temporal/transition contradiction, not missing numeric/location packet truth
- the run never produced a new contradiction showing Stage2 numeric/location carryover was blank again

### 5.2 Not a Stage4 sink reopen

Why not:

- no new Stage4 `ep7` final row exists
- the last Stage4 authority/sink evidence remains the historical `ep1~ep2` session already audited elsewhere
- this replay never reached a new Stage4 proof state worth reclassifying as a sink regression

### 5.3 A bounded Stage3 opening-transition / arc-timeline residual plus a demo-source contract blocker

Why this owner assignment fits:

- the fresh terminal reject names `arc_timeline` and `opening_transition`
- the contradiction text explicitly compares previous-blueprint continuity to Arc2 opening truth
- the utility summary independently reports the missing frozen-authority draft surface for `ep6`

That makes the clean bounded residual:

- Stage3 Arc2-opening boundary instability
- plus the single-episode Stage34 demo source-contract mismatch for this `ep7` use case

## 6. Scope Decision

This lane should now be read as:

- `partially realized`
- `Stage2 proof closed in bounded scope`
- `downstream consume proof not closed`

It should not be read as:

- `Stage2 reopened`
- `Stage4 reopened`
- `broad Stage234 rerun now required`

## 7. Recommended Next Step

The immediate next bounded action should route to the existing Stage3 boundary lane rather than another blind Stage34 replay.

Recommended order:

1. treat the fresh `ep7` failure as a handoff into the current Stage3 opening-transition / boundary-contract lane
2. do not treat the Stage34 single-episode demo utility as closure-grade for `ep7` until frozen `ep6` draft authority exists or the utility contract is explicitly revised
3. only after that bounded Stage3 residual is re-audited should this Arc2/3 proof lane decide whether one more downstream consume replay is still needed

This keeps the lane honest:

- Stage2 packet proof is preserved
- the real residual is surfaced without widening scope
- the queue does not silently reopen broader Stage234 runtime on the strength of one bounded Stage3 replay failure

## 8. 2026-04-16 Exact Failed-Lineage Stage3 Follow-up Addendum

Evidence basis:

- `modules/core/episode_state_arbiter.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_stage3_blueprint_state_precision_guardrail.py`
- `tests/test_stage3_npc_capital_carryforward_guardrail.py`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r1/logs/stage3_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r1/logs/session/ui_events.jsonl`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2/logs/stage3_canary_summary.json`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2/logs/session/ui_events.jsonl`
- `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2/logs/session/llm_io.jsonl`

Merged addendum findings:

1. The first packet-side follow-up was necessary but not sufficient.
   - the failed-lineage `stage3_from_stage3r1_ep7_r1` rerun still ended `FAILED`
   - `ui_events.jsonl` already showed `episode_state_packet_summary.time_source = arc_data.state_changes.timeline`
   - that means the new timeline authority was reaching the packet, but another higher-priority prompt surface was still winning
2. The real root cause was the immutable previous-opening `[FACT-LOCK]` block.
   - prompt evidence on the failed lineage still carried the previous blueprint's opening-specific location/time/ending-hook anchors as immutable facts
   - those anchors outranked the repaired Arc2 opening packet truth and kept the stale hotel / January / direct-continuation pressure alive at the prompt boundary
3. The bounded compiler fix now suppresses those previous-opening immutable anchors when authoritative arc-opening location/timeline truth already exists.
   - non-opening fact locks such as item/institution truth stay intact
   - the packet render path now also surfaces `opening.transition_expectation` so the prompt sees the intended opening move explicitly instead of inferring it from the stale previous ending
4. The fresh exact-lineage Stage3 rerun now passes in bounded scope.
   - `projects/_canary/canary_0_0_stage234_arc23_postpatch_stage3_from_stage3r1_ep7_r2/logs/stage3_canary_summary.json` records `ep7` as `PASS`
   - the final score is `95`, attempt `2`
   - `prevalidation = 0`, `binding = 0`
   - `sink_alignment_summary.status = ok`

Current authoritative consequence:

- the previously assigned Stage3 `arc_timeline` / `opening_transition` residual is resolved in bounded scope on the exact failed lineage
- the remaining blocker for closure-grade downstream replay is the Stage34 single-episode demo utility's source-contract gap (`frozen_authority_draft_missing:ep6`), not a reopened Stage3 boundary defect
- do not route the next action back into blind Stage3 opening-transition patching from the historical clean `stage34_ep7_r2` failure alone
- if another downstream replay is required, do it only after the frozen-authority source contract is satisfied or the utility contract is explicitly revised
