# Stage3 Live Run Quality-Gate Patch-Reopen Parallel Full Survey

- Date: 2026-04-13
- Scope: `000_260412_a` live `Stage3` rerun follow-up after the landed retry-plateau breaker, with the run stopped during `ep2 retry 6/10`
- Mode: survey-only, parallel evidence collection across console log, session log, DB sinks, accepted artifacts, validator/runtime code, and execution docs
- Baseline Commit: `2b7cb64f2d1fe2cd1152806a5cc37795609f9755`
- Baseline Dirty Summary: `dirty workspace; active hotspots: Stage3 runtime/compiler/validator/orchestrator, Stage4 runtime surfaces, tests, docs/temp mirrors`
- 3-pass audit: completed before save
- Confidence: 96%

## Scope

This follow-up answers one narrower question than the earlier retry-plateau survey:

- after the landed `PASS_WITH_FIX unresolved` plateau breaker, why did the same live `Stage3` rerun still spend `ep2` inside a long retry lane?

This document does not patch code. It fixes the new blocker family and promotes it into the formal Stage3 execution queue.

## Evidence Sources

- Console run log: [0_temp.txt](/c:/Users/PC/Desktop/글도비/0_temp.txt)
- Session log: [session_20260413_003800.log](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260413_003800.log)
- DB sink truth: [project_data.db](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/project_data.db)
- Stage2 tactical authority:
  - [arc_001.txt](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/arcs/arc_001.txt)
  - [arc_002.txt](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/arcs/arc_002.txt)
- Accepted Stage3 outputs:
  - [blueprint_0001.txt](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/blueprints/blueprint_0001.txt)
  - [final_blueprint__dialogue_focused.json](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/artifacts/stage3/ep_0001/attempt_07/final_blueprint__dialogue_focused.json)
- Code paths:
  - [three_phase_blueprint_runtime.py](/c:/Users/PC/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py)
  - [stage3_orchestrator.py](/c:/Users/PC/Desktop/글도비/modules/core/stage3_orchestrator.py)
  - [scoring_validator.py](/c:/Users/PC/Desktop/글도비/modules/validation/scoring_validator.py)
  - [blueprint_constraint_compiler.py](/c:/Users/PC/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py)
- Prior follow-up survey:
  - [stage3-live-run-retry-plateau-parallel-full-survey.md](/c:/Users/PC/Desktop/글도비/docs/2026-04-13/stage3-live-run-retry-plateau-parallel-full-survey.md)

## Executive Summary

- `P0`: no crash or deadlock evidence
- `P1`: the prior plateau-breaker helped, but a new `Director PASS < quality gate -> in-place patch reopen` seam remains live
- `P1`: Stage3 scoring is likely receiving a wrong late-stage protagonist/HUD truth packet during blueprint evaluation
- `P1`: in-flight Stage3 stop/go diagnosis still depends more on the session log than on DB/runtime summary sinks
- Recommended route: promote into the existing Stage3 parent plus partial-fix child lanes, then land a fail-only patch tranche

## Findings

### 1. The live rerun was not hanging; the new waste family is `PASS < quality gate -> patch reopen`

The runtime was alive and still advancing. The new problem is not liveness. The new problem is that a real Director `PASS` can still be converted into a long retry lane by the Stage3 quality gate.

Evidence:

- The console log shows `ep2` reaching a Director-side `PASS_WITH_FIX unresolved` family first, then later a true `PASS` path:
  - [0_temp.txt#L339](/c:/Users/PC/Desktop/글도비/0_temp.txt#L339)
  - [0_temp.txt#L382](/c:/Users/PC/Desktop/글도비/0_temp.txt#L382)
  - [0_temp.txt#L404](/c:/Users/PC/Desktop/글도비/0_temp.txt#L404)
  - [0_temp.txt#L408](/c:/Users/PC/Desktop/글도비/0_temp.txt#L408)
- The session log confirms the exact sequence:
  - Director `PASS 88`
  - quality gate force-rejects because `< 90`
  - runtime immediately reopens `blueprint in-place patch`
  - [session_20260413_003800.log#L2189](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260413_003800.log#L2189)
  - [session_20260413_003800.log#L2195](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260413_003800.log#L2195)
  - [session_20260413_003800.log#L2197](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260413_003800.log#L2197)

Code anchor:

- Stage3 quality gate still force-rejects a `PASS` when `score < 90` unless only advisory residuals remain:
  - [three_phase_blueprint_runtime.py:1492](/c:/Users/PC/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py#L1492)
- The re-audit path preserves advisory-only low-score `PASS`, but the broader `PASS < gate` family can still reopen retry:
  - [three_phase_blueprint_runtime.py:1879](/c:/Users/PC/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py#L1879)
- The patch-failure finalizer explicitly adopts the latest patched blueprint for retry after sub-gate `PASS`:
  - [three_phase_blueprint_runtime.py:1972](/c:/Users/PC/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py#L1972)

Conclusion:

- The prior plateau-breaker narrowed one family.
- The current live blocker is now `quality-gate reopen churn`, not a true hang.

### 2. Stage3 scoring is likely receiving the wrong current-state truth packet

This is the most important new semantic finding from the live rerun.

Evidence from the session log scoring prompt:

- Stage3 scoring was given this protagonist state during `ep2` blueprint evaluation:
  - `rank: SW인베스트먼트 패밀리오피스 수장 / 글로벌 투자자`
  - impossible actions for `무일푼`
  - [session_20260413_003800.log#L2295](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/session_20260413_003800.log#L2295)

Why this matters:

- This is early-episode Stage3 blueprint work for a fresh project.
- That late-stage rank does not fit the current episode-local truth and can distort scoring or soft consistency penalties.

Code path evidence:

- `ScoringValidator` injects `[V46] 주인공 현재 상태` from `context["martial_hud"]` / `actual_truth`:
  - [scoring_validator.py:410](/c:/Users/PC/Desktop/글도비/modules/validation/scoring_validator.py#L410)
  - [scoring_validator.py:416](/c:/Users/PC/Desktop/글도비/modules/validation/scoring_validator.py#L416)
- `stage3_orchestrator.py` passes `ctx.sys.hud.pro_root` into Stage3 as `prev_hud`:
  - [stage3_orchestrator.py:1744](/c:/Users/PC/Desktop/글도비/modules/core/stage3_orchestrator.py#L1744)
  - [stage3_orchestrator.py:1795](/c:/Users/PC/Desktop/글도비/modules/core/stage3_orchestrator.py#L1795)

Inference:

- Stage3 scoring is probably over-consuming live HUD truth that is too global or too late for the current blueprint-evaluation context.
- This is a cross-stage truth-routing seam, not just model randomness.

### 3. Accepted Stage3 truth is still too permissive on canonical entities and market anchors

The earlier plateau survey already showed accepted drift. That remains true under the current rerun context.

Evidence:

- The accepted `ep1` blueprint still uses `한정호그룹` and strong market-history prose such as `이란 핵 협상 결렬`:
  - [blueprint_0001.txt#L7](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/blueprints/blueprint_0001.txt#L7)
  - [blueprint_0001.txt#L23](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/blueprints/blueprint_0001.txt#L23)
  - [blueprint_0001.txt#L25](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/plans/blueprints/blueprint_0001.txt#L25)
- The accepted JSON artifact preserves the same content drift:
  - [final_blueprint__dialogue_focused.json#L34](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/logs/artifacts/stage3/ep_0001/attempt_07/final_blueprint__dialogue_focused.json#L34)

Conclusion:

- The current live blocker is quality-gate churn, but the underlying Stage3 truth-routing debt is not fully clean yet.
- The new quality-gate seam should not be treated as an isolated numeric threshold issue only.

### 4. In-flight Stage3 stop/go evidence is still under-persisted outside the session log

This is an observability finding that now matters more because the new blocker happens mid-run.

Evidence:

- The DB only persists the final Stage3 `ep1 attempt 7 PASS 92` row, not the in-flight `ep2` churn:
  - [project_data.db](/c:/Users/PC/Desktop/글도비/projects/000_260412_a/project_data.db)
- Current counts:
  - `stage_attempts = 4`
  - `director_selections = 4`
  - `attempt_raw_rationale = 0`
- Latest persisted Stage3 rows are still only:
  - `stage_attempts`: `stage=3, ep_num=1, attempt_num=7, verdict=PASS, score=92`
  - `director_selections`: `stage=3, ep_num=1, round_num=7, selected_strategy=dialogue_focused, score=92`

Conclusion:

- During interrupted or operator-stopped Stage3 runs, `session_*.log` remains the authoritative source.
- DB/runtime summary sinks are still too sparse for live retry diagnosis by themselves.

## What This Survey Rejects

- This is not primarily a `Sonnet is slow` issue.
- This is not a true runtime deadlock.
- This is not purely a `PASS_WITH_FIX unresolved` replay of the earlier blocker family.

## Recommended Execution Promotion

Promote this follow-up into the existing Stage3 lanes rather than opening a brand-new queue owner.

Primary targets:

- [0_0-stage3-contract-tightening-remediation-execution-ssot.md](/c:/Users/PC/Desktop/글도비/docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md)
- [0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md](/c:/Users/PC/Desktop/글도비/docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md)
- [active-temp-execution-roadmap.md](/c:/Users/PC/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md)

Recommended fail-only patch themes:

1. deny `inplace` reopen when the immediately preceding state is `Director PASS` but `quality gate < threshold`
2. narrow Stage3 scoring truth so `prev_hud` cannot inject late/global protagonist state into early blueprint scoring
3. improve in-flight Stage3 failure sink surfacing enough that live stop/go does not depend almost entirely on the session log

## Final Judgment

The live rerun proved that the earlier plateau-breaker was useful but incomplete.

The blocker has shifted from:

- `PASS_WITH_FIX unresolved -> repeated inplace plateau`

to:

- `Director PASS < quality gate -> patch reopen`, with likely scoring distortion from a wrong current-state truth packet.

That makes the next step a narrow fail-only Stage3 patch tranche, not a broad Stage2/S4 redesign.
