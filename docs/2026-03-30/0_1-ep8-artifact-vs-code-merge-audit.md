# 0_1 EP8 Artifact-vs-Code Merge Audit

Date: 2026-03-30
Status: final (3-pass audited)
Document Type: merge audit
Canonical Path: `docs/2026-03-30/0_1-ep8-artifact-vs-code-merge-audit.md`
Temp Mirror Path: `(none - merge audit only)`
Baseline Commit: `92ba1cf7`
Baseline Dirty Summary: `dirty: 0_temp.txt modified; 0_1 episode/log DB sinks advanced; ep_0008 Stage 4 artifact dir untracked`
Source Docs:
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane1-artifact-truth-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane2-code-contract-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane3-persistence-timeline-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane4-master-synthesis-draft.md`
Evidence Artifacts:
- `0_temp.txt`
- `projects/0_1/logs/session_20260330_161043.log`
- `projects/0_1/logs/episode_production.jsonl`
- `projects/0_1/logs/artifacts/stage4/ep_0008/attempt_05/selected_before_fix__C_asp_correction.txt`
- `projects/0_1/plans/blueprints/blueprint_0008.txt`
- `projects/0_1/drafts/ep_0007.txt`
- `projects/0_1/project_data.db`
Side-Effect Coverage:
- DB read sinks
- JSONL/session log sinks
- artifact file truth
- retry/gate control flow
- blueprint export authority

## 1. Purpose

This audit merges the three bounded EP8 survey lanes into one canonical answer:

- whether EP8 is blocked mainly by artifact truth, code contract, or both
- what the next execution lanes must be

## 2. Executive Finding

EP8 is `mixed`.

The correct split is:

- current acceptance blocker: artifact-stage blueprint truth defects
- systemic retry-budget blocker: code-stage Stage 4 contract defects

This means:

- fixing only the blueprint is not enough for systemic safety
- fixing only the code is not enough to accept the current EP8 artifact

## 3. Confirmed Artifact-Stage Findings

### A-1. Blueprint temporal contradiction

`projects/0_1/plans/blueprints/blueprint_0008.txt` carries:

- `현실의 지표가 18년 전 과거의 기억과 단 1초의 오차도 없이 맞물려 돌아가고 있었다`

That phrase is incompatible with the current timeline perspective.
The protagonist is currently in 2006, so the remembered 2024 knowledge is not "18 years ago" from the current in-story viewpoint.

The same phrase is carried forward into:

- `projects/0_1/logs/artifacts/stage4/ep_0008/attempt_05/selected_before_fix__C_asp_correction.txt`

Director and post-select validation both catch it.

### A-2. Blueprint residual-cash contradiction

`projects/0_1/plans/blueprints/blueprint_0008.txt` still says:

- `계좌에 남은 5억 원`

But EP7 authoritative manuscript truth is:

- `잔고에 4억 7,100만 원이 남아있다고는 하지만`

That mismatch is then reintroduced into EP8 and correctly fails continuity.

### A-3. Park Seong-ho title drift is real but secondary

The role drift is not the current hardest blocker.
By attempt 5, the selected candidate already self-corrects to:

- `SW인베스트먼트 전담 PB 박성호`

This remains a recurrence risk and should be hardened at the blueprint wording layer, but it is not the decisive failure once attempt 5 is reached.

## 4. Confirmed Code-Stage Findings

### C-1. Strong-advisory escalation can create an impossible PASS_WITH_FIX state

In `modules/core/stage4_interview_round.py`:

- plain `PASS` is upgraded to `PASS_WITH_FIX` when strong advisory keys fire
- the same flow does not guarantee a viable local fix pack
- the PASS_WITH_FIX contract then rejects on empty `patch_targets`

Observed result:

- attempts 1-4 are rejected for `Fix Pack patch_targets is empty`

### C-2. Post-select conflict scope can leak

The runtime correctly downgrades attempt 5 on post-select conflict, but the later reject guidance path can preserve pre-downgrade scope data too long.

Observed result:

- a runtime that should now be treated as `full` can still retain `inplace`-shaped retry intent in downstream handling

### C-3. This is a real defect, but not the final acceptance blocker for the current artifact

The code defect explains why four attempts were wasted.
It does not explain away the real artifact contradictions found in attempt 5.

## 5. Attempt Timeline Interpretation

### Attempts 1-4

- Director quality scores remain high: `95-96`
- strong advisory escalation fires
- no viable `patch_targets`
- fail-closed REJECT loop consumes budget

Interpretation:

- code-dominated failure phase

### Attempt 5

- Director returns `PASS_WITH_FIX`
- a real local patch target appears
- post-select checks then fail on blueprint-carried contradictions

Interpretation:

- artifact-dominated failure phase

### Attempt 6

- not terminal
- not persisted as a finished attempt
- not closure-grade evidence

## 6. Master Classification

`mixed`

Reason:

- lane 1 is correct that the current EP8 blueprint would still fail even with perfect code
- lanes 2 and 3 are correct that the early retry path wasted four rounds because of a code contract seam

The merged answer must preserve both truths.

## 7. Execution-Bearing Findings

### P1-A. EP8 blueprint authoritative repair

Why action-bearing:

- directly blocks successful acceptance of the current episode
- exact contradictory phrases are known
- authority path is known and bounded

### P1-B. Stage 4 advisory-escalation / post-select contract hardening

Why action-bearing:

- wastes retries
- obscures root cause
- can recur beyond EP8

### Watchlist. Dialogue ratio and opening warnings

Why not action-bearing now:

- not the current hard blocker
- mostly advisory or false-positive territory

## 8. Immediate Order

Recommended order:

1. `EP8 blueprint authoritative repair`
2. `Stage 4 contract hardening`
3. `bounded EP8 rerun and post-run audit`

This order is chosen because:

- the blueprint defects are deterministic and cheap to repair
- the code defect is systemic and should be fixed before trusting a rerun budget
- rerunning before both are addressed risks another noisy signal mix

## 9. 3-Pass Audit Record

Pass 1, structure and scope:

- merge-audit document type is correct
- source reports and evidence artifacts are explicit
- included surfaces are bounded to EP8 artifact/code split

Pass 2, evidence and consistency:

- lane 1, 2, and 3 disagreements were resolved into a bounded mixed classification
- direct spot-checks confirmed the blueprint truth, EP7 truth, and code seam anchors
- no claim depends only on terminal rendering

Pass 3, execution and readability:

- the audit yields two clear execution-bearing lanes
- priority and rationale are explicit
- residual watchlist is separated from blockers

Confidence: 97%
