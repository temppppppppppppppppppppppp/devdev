# 0_0 Stage4 Interview-Round Owner-Surface Reduction Bounded Survey

Date: 2026-04-07
Status: final
Document Type: bounded complexity / owner-surface survey
Canonical Path: `docs/2026-04-07/0_0-stage4-interview-round-owner-surface-reduction-bounded-survey.md`
Scope: `modules/core/stage4_interview_round.py` owner surface plus its immediate Stage4 runtime helper boundary
Execution Mode: `static code/AST survey -> parked future-wave routing`
Owner: `Codex`
Commit State:
- Baseline Commit: `5a2ef92ab04e46d47ee73b9d56d3e546544576c0`
- Baseline Dirty Summary: `dirty: tracked narrative TR/BI artifacts modified; 2026-04-07 in-flight meta cleanup docs untracked`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Source Inputs

Policy and queue anchors:

- `AGENTS.md`
- `docs/temp/execution-roadmap.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`

Direct code anchors:

- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_lane2_binding_contract.py`
- `tests/test_stage4_advisory_escalation_seam.py`

## 2. Executive Verdict

This seam is not currently represented as its own execution queue item.

It is real, but it is not a fresh runtime blocker.
The bounded conclusion is:

- promote it as a `parked future wave`
- classify it as `owner-surface / boundary refactor`, not `same-file helper cleanup`
- keep it below the current functional Stage4 / Stage2 / Stage3 / Stage0 future waves
- keep it above soak-only references because the owner-pressure evidence is strong and local to live runtime code

Severity:

- `P2` on maintainability / execution velocity
- `P0/P1`: none

## 3. Evidence Inventory

### 3.1 Owner pressure is materially above the workspace pressure line

Static AST recount on 2026-04-07:

- `Stage4InterviewRound` direct methods: `158`
- `180+ LOC` methods: `3`
- `120+ LOC` methods: `6`

Current top hotspots:

- `_run_post_select_checks`: `294 LOC`
- `_normalize_director_gate_semantics`: `219 LOC`
- `_append_episode_log`: `210 LOC`
- `_backfill_strong_advisory_fix_pack`: `157 LOC`
- `_build_retry_feedback_provenance`: `121 LOC`
- `_run_advisory_chain`: `120 LOC`

This crosses the workspace owner-pressure threshold even though the high-risk band count is already much lower than older Stage4 states.

### 3.2 Boundary precedent already exists

The owner is not a pure monolith anymore.
The class already delegates to:

- `Stage4DirectorRuntime`
- `Stage4RejectRuntime`
- `Stage4RetryRuntime`

That means future extraction is not speculative architecture.
The codebase already accepts the pattern.

### 3.3 The remaining heavy families are still concentrated in the owner

The heaviest remaining families are still directly owned by `Stage4InterviewRound`:

1. post-select downgrade / continuity / reuse decision flow
2. director gate normalization and pass-with-fix repair-contract shaping
3. episode-log and attempt-sink payload assembly

These families are semantically distinct enough to become boundaries.
Keeping them in the owner primarily preserves historical locality, not conceptual unity.

### 3.4 Test surface confirms refactor risk, not blocker urgency

The direct regression surface is wide:

- `tests/test_stage4_interview_round.py`
- `tests/test_stage4_lane2_binding_contract.py`
- `tests/test_stage4_advisory_escalation_seam.py`

This means the lane should be parked until it is intentionally opened with a contract-freeze mindset.
It does not mean the issue is fake.

## 4. Semantic Classification

### Class A. Real future-wave debt

- `Stage4InterviewRound` owner-surface reduction
- module-boundary extraction of post-select handling
- module-boundary extraction of gate-semantics normalization
- module-boundary extraction of attempt / episode-log sink assembly

### Class B. Secondary bounded follow-on

- retry feedback provenance packaging
- strong-advisory fix-pack backfill helper cleanup
- test harness narrowing around newly extracted boundaries

### Class C. Explicitly deferred

- any behavior-changing Stage4 consumer fix
- any repair-contract semantics change
- Stage2 / Stage3 upstream changes
- DB schema redesign
- broad same-file helper accretion

## 5. Queue Placement Reading

This lane should be parked:

- below `0_0-stage4-consumer-contract-normalization-remediation`
- below `0_0-stage4-repair-contract-normalization-remediation`
- below `0_0-stage234-nonwuxia-state-lock-overreach-remediation`
- below the broader parked functional future waves
- above `frontier-lag-soak-canary-wave1`

Reason:

- the current front queue is still functional/runtime debt
- this new lane is structure-first and should not preempt functional truth normalization
- but it is still closer to live ROI than soak-only references because the owner-pressure evidence is immediate and local

## 6. Recommended Next Step

Promote one parked execution SSOT with these rules:

1. module-boundary first, not same-file helper growth
2. no activation before current functional Stage4 front seams and current parked functional waves are intentionally reprioritized
3. contract-freeze tests must lead the future implementation, not trail it

## 7. Non-Goals

This survey does not authorize:

- refactoring `Stage4InterviewRound` in the current turn
- reprioritizing it above active functional queue items
- broad Stage4 redesign
- changing verdict semantics, sink ownership, or retry policy as part of the parked promotion

## 8. 3-Pass Audit

Pass 1:

- confirmed the target is system-track structure debt, not a narrative or runtime-bug queue jump
- kept scope bounded to one owner class plus immediate extracted runtime siblings

Pass 2:

- rechecked current queue docs to confirm no dedicated parked execution item already exists for this owner-surface lane
- grounded the claim in direct AST counts and concrete hotspot functions rather than general “Stage4 is big” wording

Pass 3:

- trimmed the recommendation to parked promotion only
- confirmed the route is boundary extraction, not ad hoc same-file cleanup
- confirmed the lane stays below active and parked functional waves

Confidence: `96%`
