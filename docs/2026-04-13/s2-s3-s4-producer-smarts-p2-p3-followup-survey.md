# S2 S3 S4 Producer Smarts P2 P3 Follow-up Survey

- Date: 2026-04-13
- Scope: current `main@32d6f0c8` bounded follow-up survey on the remaining `P2/P3` producer-side residuals after the first `s2-s3-s4` producer-smarts landing
- Mode: survey-only, 3-pass audit, execution consequence intended; no code changes in this document step
- Canonical Path: `docs/2026-04-13/s2-s3-s4-producer-smarts-p2-p3-followup-survey.md`
- Baseline Commit: `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `dirty: active Stage3 queue docs/temp mirrors, live 000_260412_a run artifacts, local provider/model edits, and bounded s2-s3-s4 producer-smarts code/tests already present`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none during this survey`
- Side-Effect Coverage: Stage2/Stage3/Stage4 producer code, targeted tests, canonical queue docs, and operator-visible shortlist/gate behavior inspected; no queue membership or runtime artifacts mutated in this survey step
- Confidence: `96%`

## Purpose

This survey answers one bounded follow-up question:

- after the first `s2-s3-s4` producer-smarts landing, which remaining `P2/P3` seams are cheap and safe enough to improve before the next rerun

This survey does not open a new queue family.

This survey is intended to feed one bounded follow-up tranche inside the existing queue authority.

## Evidence Anchors

Prior authority:

- `docs/2026-04-13/s2-s3-s4-producer-smarts-bounded-3pass-audit.md`
- `docs/2026-04-13/stage3-ep8-cw-director-root-cause-parallel-survey.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`

Current code owners:

- `modules/core/scene_obligation_heuristics.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/core/stage_cross_stage_contract.py`

Targeted tests in scope:

- `tests/test_arc_ensemble_lane_a.py`
- `tests/test_blueprint_ensemble_generate_ensemble.py`
- `tests/test_chief_writer_candidate_lane_f.py`
- `tests/test_chief_writer_generate_ensemble_lane_b.py`
- `tests/test_stage23_stage4_readiness_wave1.py`

## Executive Summary

- No new broad queue split is justified.
- The cheapest remaining producer-side `P2/P3` debt is not the deep validator/runtime family. It is the still-loose degraded-mode candidate admission and ordering around Stage2, Stage3, and Stage4.
- The safest bounded next tranche is:
  - Stage2 shortlist honesty when a stronger mission-packet candidate already exists
  - Stage3 placeholder-state hardening for `protagonist_state`
  - Stage4 contract-strength ordering for both qualified and degraded fallback candidates
- This tranche stays below broad validator retuning, broad Director retuning, and broad tactical-semantic surgery.

## Findings

### 1. Stage2 still lets all-generic mission packets reach the Director shortlist too easily

Current Stage2 behavior:

- `arc_ensemble.py:503` applies a bounded penalty for generic `episode_details`
- `arc_ensemble.py:1242` still builds the Director shortlist mainly from score threshold
- if a generic mission-packet candidate remains above the threshold, it can still sit beside a better candidate in the Director shortlist

This means:

- Stage2 is better than before
- but when at least one non-generic candidate already exists, the shortlist is still more permissive than necessary

Residual severity:

- `P2`

### 2. Stage3 `protagonist_state` admission still accepts placeholder payloads too easily

Current Stage3 behavior:

- `blueprint_ensemble.py:825` treats any non-empty string/list/dict slot as meaningful
- `unified_blueprint_validator.py:2072` later only checks whether the state is empty, not whether it is concretely informative

This means:

- placeholders like `상태 유지`, `기분 변화`, `정상`, or similarly vague state shells can still survive the cheap producer gate
- the current Stage3 gate is stricter than before, but the `protagonist_state` side still remains looser than the intended narrative use of that field

Residual severity:

- `P3`, but cheap and worth tightening

### 3. Stage4 degraded mode still keeps original candidate order when all candidates fail the new contract gate

Current Stage4 behavior:

- `chief_writer.py:261` returns original candidates when no candidate clears the contract gate
- `chief_writer.py:811` then hands that unchanged candidate order downstream

This means:

- the first landing correctly preserves resilience
- but in all-fail mode it still leaves the least-bad fallback implicit instead of explicitly ranking candidates by contract strength

Residual severity:

- `P2/P3`

### 4. These residuals are cheaper than deeper validator/runtime surgery

The broader remaining problems are still real:

- Stage3 tactical-semantic drift
- deeper cross-stage authority drift
- full semantic continuity checking at Stage4

But those are not the cheapest next improvements.

The current cheap residual tranche is producer-side and ordering-side:

- better shortlist honesty
- better placeholder rejection
- better degraded fallback ordering

## Ownership Verdict

- `Stage2 producer shortlist`: real residual owner
- `Stage3 producer contract gate`: real residual owner
- `Stage4 writer-side degraded fallback ordering`: real residual owner
- `validator/runtime`: still own deeper semantics, but not the cheapest next tranche

## Execution Consequence

Keep the active queue shape.

Do not open a new queue lane.

Keep the existing owner reading:

- parent owner: `0_0-stage3-contract-tightening-remediation`
- sibling support: `0_0-stage3-opening-transition-contract-normalization-remediation`
- cross-stage support remains inside existing Stage2/Stage4 lanes and the active roadmap

Bounded next tranche justified by this survey:

1. Stage2:
   - when at least one shortlist-worthy candidate has actionable mission packets, stop forwarding generic mission-packet siblings in the same shortlist
2. Stage3:
   - harden `protagonist_state` admission so placeholder state shells no longer count as meaningful state
3. Stage4:
   - rank candidates by manuscript contract strength
   - when all candidates fail the contract gate, keep resilience but return the least-bad fallback order explicitly

Explicit non-goals:

- no broad validator retuning
- no broad tactical-semantic heuristic rewrite
- no broad Director retuning
- no new queue family

## 3-Pass Audit

Pass 1. Structure and scope:

- kept the survey bounded to `P2/P3` producer-side follow-up only
- avoided widening into broad semantic-runtime debt
- kept queue consequence explicit

Pass 2. Evidence and consistency:

- rechecked the first producer-smarts audit against the live code paths
- verified the residuals in Stage2 shortlist logic, Stage3 state gate, and Stage4 degraded fallback handling
- kept ownership aligned with the current canonical queue docs

Pass 3. Execution and readability:

- translated the residuals into one bounded cross-stage tranche
- kept larger refactors explicitly deferred
- preserved the rerun as the next action after this bounded tranche lands

Confidence after 3-pass audit: `96%`
