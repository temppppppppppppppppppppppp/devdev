# Active Temp Execution Roadmap

Date: 2026-04-19
Status: active (2026-04-19 queue refresh plus Stage2 sibling-lane closure reviews, all four Stage3 closure reviews, the Stage4 consumer closure review, the Stage4 repair closure review, the Stage4 interview-round owner-surface reactivation refresh, the Stage0 treatment-enrich retirement reactivation refresh, the Stage0 BI/TR production-harness normalization reactivation refresh, the frontier lag soak canary reactivation refresh, the npc-martial substrate reactivation refresh, the readiness-lane reactivation refresh, the parked-board compaction closure review, and the audit-report candidate revalidation parking refresh; the older 2026-04-01 controller remains compacted, no honest front-active implementation tranche remains on the board, the queue now sits in parked mode with the Stage4 interview-round owner-surface lane still confirmed as the next parked candidate while the audit-report candidate lane is added as a second parked governance item, and historical-backing temp mirrors remain retired from the live temp surface in this wave)
Canonical Path: `docs/2026-04-19/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `029df1a74af89a7b5387c449f4723a5df0d000d4`
Baseline Dirty Summary: `dirty: many tracked/untracked runtime, canary, docs/temp, tests, and project-data deltas already present; this roadmap refresh only reprioritizes parked queue semantics and adds one candidate-only lane`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `none`

## 1. Why This Refresh Exists

The old active roadmap kept too many items reading as live front queue work long after their practical next action had become proof-only, historical, or parked architecture debt.

The 2026-04-19 refresh applies three rules:

- promote only the items whose next real action is still queue-worthy now
- downgrade proof anchors and landed substrate lanes to `historical backing only`
- park broader architecture or Stage0 hygiene lanes that are real but not the current operating focus
- absorb the formal audit-report revalidation lane as a parked candidate rather than letting raw `P0/P1` rhetoric bypass the queue contract

## 2. Priority Basis

- Stage2 pacing honesty is now closed canonical backing rather than live front work.
- Stage2 contract normalization is now closed canonical backing rather than live front work.
- Stage3 contract tightening is now closed canonical backing rather than live front work.
- Stage3 opening-transition is now closed canonical backing rather than live front work.
- Stage4 consumer contract normalization is now closed canonical backing rather than live front work.
- Stage4 repair contract normalization is now closed canonical backing rather than live front work.
- Stage3 state-arbiter envelope is now closed canonical backing rather than live front work.
- no honest front-active implementation tranche remains after the Stage3 state-arbiter and quality-closure reviews.
- the next visible move is a parked Stage4 architecture candidate, not an immediate implementation order.
- the Stage4 interview-round owner-surface lane remains honest parked architecture debt and should stay visible.
- the audit-report candidate revalidation lane is now an honest parked governance item and should stay visible below the Stage4 architecture candidate rather than being mistaken for a front-active implementation order.
- the Stage0 treatment-enrich retirement lane remains honest parked hygiene debt and should stay visible below the Stage4 architecture candidate.
- the Stage0 BI/TR production-harness normalization lane remains honest parked source-of-truth debt and should stay visible below the Stage0 treatment-enrich lane.
- the `0_0` readiness lane remains honest blocked operator context and should stay visible until fresh proof authorization exists.
- the frontier lag soak canary lane remains honest parked low-priority reference-validation debt and should stay visible near the tail of the board.
- the npc-martial substrate lane remains honest blocked follow-up debt and should stay visible as blocked holding rather than being silently parked or closed.
- historical-backing items no longer need temp mirrors once the parked board semantics are stable.
- Older Stage234 proof chains remain important evidence, but they are no longer the front implementation queue.
- Stage4 architecture and Stage0 hygiene stay visible without pretending they are the current immediate move.

## 3. Queue Semantics

- `front active`: the next bounded action can honestly start from this queue item now
- `parked future wave`: keep visible, but do not let it crowd the front board
- `historical backing only`: preserve as evidence and reference, not as active workload
- `blocked holding`: still blocked by dependencies or by explicit operator policy
- `parked mode`: no `front active` implementation lane is honest right now; the next visible item is only a parked candidate until explicit runtime authorization or fresh reopen evidence appears

Working order:
Working order:
1. `0_0-stage4-interview-round-owner-surface-reduction-remediation` (parked future wave; the next visible parked candidate, and the 2026-04-19 reactivation refresh confirms it should remain parked rather than be closed or promoted)
2. `audit-report-candidate-revalidation-remediation` (parked future wave; cross-cutting candidate-only governance lane created by the formal 2026-04-19 revalidation audit, and it must remain parked rather than be mistaken for immediate implementation authority)
3. `stage0-treatment-enrich-retirement-remediation` (parked future wave; Stage0 hygiene lane, and the 2026-04-19 reactivation refresh confirms it should remain parked rather than be closed or promoted)
4. `stage0-bi-tr-production-harness-normalization-remediation` (parked future wave; Stage0 source-of-truth lane, and the 2026-04-19 reactivation refresh confirms it should remain parked rather than be closed or promoted)
5. `0_0-stage2-stage3-stage4-readiness-remediation` (blocked holding; still blocked behind explicit proof authorization)
6. `frontier-lag-soak-canary-wave1` (parked future wave; low-priority reference-validation lane, and the 2026-04-19 reactivation refresh confirms it should remain parked rather than be closed or promoted)
7. `npc-martial-state-substrate-wave1` (blocked holding; historical blocked substrate, and the 2026-04-19 reactivation refresh confirms it should remain blocked rather than be reopened or closed)

Compacted out of the live temp queue surface on 2026-04-19:

- `0_0-stage234-arc23-post-patch-rerun-proof`
- `0_0-stage234-global-authority-alignment-bounded-remediation`
- `0_0-stage234-cross-stage-contract-normalization-remediation`
- `0_0-stage234-nonwuxia-state-lock-overreach-remediation`
- `0_0-stage4-partial-fix-hardening-remediation`
- `0_0-stage3-partial-fix-hardening-remediation`
- `0_0-stage2-partial-fix-hardening-remediation`
- `0_0-stage34-ep2-single-episode-demo-canary`
- `0_0-stage4-ep2-advisory-escalation-loop-remediation`
- `0_0-stage4-canonical-entity-postselect-remediation`
- `0_0-stage4-flashback-continuity-localfix-remediation`
- `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation`

## 4. Immediate Next Moves

1. keep the closed Stage2 sibling lanes, all closed Stage3 sibling lanes, and both closed Stage4 sibling lanes as canonical historical backing rather than temp-queue workload
2. keep the audit-report candidate lane parked as candidate-only governance debt and do not let it bypass the queue into direct implementation
3. remove the old Stage3 quality-closure parked lane from the active queue surface because its remaining work is proof-contingent rather than queue-ready
4. read the board as parked mode with `0_0-stage4-interview-round-owner-surface-reduction-remediation` as the next visible parked candidate and `audit-report-candidate-revalidation-remediation` as the next parked governance lane rather than as front-active implementation items
5. keep `docs/temp/queue-state.json` and the ClickUp mirror aligned to the same parked-mode semantics

## 5. Cleanup Rule

- keep canonical dated execution SSOTs as evidence
- keep temp mirrors only while the item is still part of the live temp queue surface
- remove the pacing-lane temp mirror during this closure tranche because the item is now closed
- remove the Stage3 contract-tightening temp mirror during this closure tranche because the item is now closed
- remove the Stage3 opening-transition temp mirror during this closure tranche because the item is now closed
- remove the Stage4 consumer temp mirror during this closure tranche because the item is now closed
- remove the Stage4 repair temp mirror during this closure tranche because the item is now closed
- remove the Stage3 state-arbiter temp mirror during this closure tranche because the item is now closed
- remove the Stage3 quality-closure temp mirror during this closure tranche because the item is now closed
- remove `historical backing only` temp mirrors during this compaction tranche because the parked board semantics are now stable
- keep the audit-report candidate revalidation temp mirror while the parked board still needs a bounded candidate-only governance lane
- after this compaction wave, the temp queue should contain only parked or blocked items

## 6. ClickUp Reflection

Once the canonical roadmap, temp mirror, and queue-state are aligned:

1. validate queue artifacts
2. sync the system queue mirror into ClickUp
3. treat the repo queue as authoritative if ClickUp wording diverges

## Pass 1

- the refresh removes the stale implication that the old Stage3 quality-closure plan is still the top parked continuation after the parent and sibling Stage3 lanes are already closed
- the refresh keeps the board in parked mode instead of pretending a proof-contingent Stage3 backlog is still queue-ready
- the refresh adds the formal audit-report candidate lane without letting raw severity rhetoric jump ahead of the existing parked-board ordering

## Pass 2

- the queue is compacted without deleting canonical evidence
- parked and historical items remain visible, but their semantics are now explicit
- the new candidate lane is visible, but its candidate-only semantics are explicit enough that it does not masquerade as implementation authority

## Pass 3

- the roadmap is short enough to read operationally
- queue-state parsing remains compatible because the working order is explicit and machine-readable
- the parked board now reflects the fresh audit/revalidation work without reopening the whole queue

Confidence: 97/100
