# Deferred Follow-Ups Yes/No Triage 7-Terminal Merge Audit

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: merge audit
Canonical Path: `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-merge-audit.md`
Source Order:
- `docs/2026-03-25/deferred-followups-yesno-triage-7terminal-master-order.md`

Source Lane Reports:
- `docs/2026-03-25/opus-deferred-triage/t1-stage3-constitutionalchecker-wiring.md`
- `docs/2026-03-25/opus-deferred-triage/t2-stage4-inprompt-self-audit-restoration.md`
- `docs/2026-03-25/opus-deferred-triage/t3-director-scene-level-retry-feedback.md`
- `docs/2026-03-25/opus-deferred-triage/t4-scene-entry-schema-tightening.md`
- `docs/2026-03-25/opus-deferred-triage/t5-stage2-selfcheck-compliance-logging.md`
- `docs/2026-03-25/opus-deferred-triage/t6-self-audit-reasoning-persistence.md`
- `docs/2026-03-25/opus-deferred-triage/t7-self-audit-compliance-rate-tracking.md`

## 1. Executive Summary

The triage result is unambiguous:

- `yes now`: 0 lanes
- `later after canary`: 4 lanes
- `no`: 3 lanes

This means:
- no new execution SSOT should be opened now
- the next operator step is a fresh canary/live run
- deferred lanes stay parked until post-canary evidence is available

## 2. Verdict Table

| Lane | Topic | Verdict | Immediate SSOT? | Merge conclusion |
|------|-------|---------|-----------------|------------------|
| T1 | Stage 3 ConstitutionalChecker dynamic wiring | later after canary | no | plausible follow-up only if static self-audit canary is positive but incomplete |
| T2 | Stage 4 in-prompt self-audit restoration | later after canary | no | existing Self-Critique loop already too strong to justify opening now |
| T3 | scene-level Director retry feedback | later after canary | no | gap is real, but blast radius is too high before canary attribution |
| T4 | scene-entry schema tightening | no | no | safety net not currently firing; tightening would add risk without quality gain |
| T5 | Stage 2 self-check compliance logging | no | no | observability-only, no current operator consumer |
| T6 | self-audit reasoning persistence | no | no | reasoning already sufficiently preserved across existing sinks |
| T7 | self-audit compliance rate tracking | later after canary | no | may become useful only after self-audit canary produces real data |

## 3. Highest-Signal Findings

### F-1. No deferred lane is strong enough to open now

No lane returned `yes now`.
This is the most important outcome of the triage.

The workspace should not open a new bounded wave before observing:
- post-Wave1 canary behavior
- post-self-audit canary behavior

### F-2. Four lanes remain credible, but only after canary

Credible `later after canary` lanes:
- T1 Stage 3 ConstitutionalChecker dynamic wiring
- T2 Stage 4 in-prompt self-audit restoration
- T3 scene-level Director retry feedback
- T7 self-audit compliance rate tracking

These are not rejected permanently.
They are simply waiting on better attribution evidence.

### F-3. Three lanes should be treated as parked/no

Current `no` lanes:
- T4 scene-entry schema tightening
- T5 Stage 2 self-check compliance logging
- T6 self-audit reasoning persistence

These lanes are either:
- safety-net removal with no demonstrated gain
- observability-only without a live consumer
- or sink expansion without decision value

## 4. Why No Immediate Execution SSOT Was Opened

The 7-lane triage converged on the same operating rule:

- the Stage 3 clarity/density wave just closed
- the Stage 3 self-audit wave just closed
- a fresh canary has not yet measured their combined effect

Opening another wave now would:
- muddy attribution
- raise stale-survey risk
- and violate the single-culprit-first operating preference

## 5. Recommended Next Step

Run a fresh bounded canary/live run first.

After that:
- if the canary shows partial improvement but remaining Stage 3 prompt weakness, revisit T1
- if the canary shows retry inefficiency as the dominant residual, revisit T3
- if the canary shows self-audit present but low practical effect, revisit T7
- only consider T2 if Stage 4 remains the dominant unresolved quality bottleneck after the canary

## 6. Parked Lanes

Do not reopen these unless fresh evidence changes the picture:

- T4 scene-entry schema tightening
- T5 Stage 2 self-check compliance logging
- T6 self-audit reasoning persistence

## 7. Merge Conclusion

There is no `yes now` lane in the remaining defer set.

The defer triage is complete.
No execution SSOT should be opened from this batch.
The correct next move is a fresh canary/live run.

## 8. Mandatory Final Lines

- Dominant triage result: `no immediate wave`
- Best bounded next step: `fresh canary / live run`
- Should Codex open an execution SSOT now: `no`

