# Active Temp Execution Roadmap

Date: 2026-04-01
Status: active (3-pass audited, ep2 advisory patch landed; runtime closure pending)
Canonical Path: `docs/2026-04-01/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Baseline Dirty Summary: `dirty: 0_0 runtime logs/db/artifacts active; legacy temp queue mirrors present; 2026-03-31 0_0 survey docs untracked`
Resume Commit: `094ee9b50cad33b1aec89ca4f097103ece5b1938`
Resume Drift Summary: `ep2 advisory loop T1-T3 landed; targeted static validation closed; lane remains open for runtime closure`
Supersedes:
- `docs/2026-03-31/active-temp-execution-roadmap.md`

Queue Snapshot:
- `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`
- `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
- `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md`
- `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`

## 1. Purpose

This roadmap is the active controller for the current `docs/temp/` execution queue.

This refresh adds the ep2 advisory escalation loop remediation lane:

1. `0_0-stage4-ep2-advisory-escalation-loop-remediation` (new — highest priority)
2. `0_0-stage2-stage3-stage4-readiness-remediation` (partial — Stage3 closed, Stage4 blocked by #1)

The advisory loop lane outranks all other items because:

- it is the direct blocker for Stage4 ep2 progression
- the parent upstream lane's Stage4 sub-verdict depends on this lane completing
- the bounded survey confirmed the advisory loop is a separate seam, not a Stage2/3 regression
- the remaining legacy temp items were already `parked` or `blocked`

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `0_0-stage4-ep2-advisory-escalation-loop-remediation` | `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | `docs/temp/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md` | partial — code landed; runtime closure pending | 3 tranche: FlashbackVerifier precision + advisory persistence + post_select observability |
| `0_0-stage2-stage3-stage4-readiness-remediation` | `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | partial — Stage3 closure candidate; Stage4 blocked by advisory loop lane | ctxnorm_r1 canary complete; Stage3 sub-verdict: closure_candidate; Stage4 sub-verdict: blocked |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | parked | non-critical soak lane |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | awaits fresh evidence and explicit reactivation |

## 3. Dependency Notes

- `0_0-stage4-ep2-advisory-escalation-loop-remediation` is a prerequisite for `0_0-stage2-stage3-stage4-readiness-remediation` Stage4 sub-verdict advancement.
- `0_0-stage2-stage3-stage4-readiness-remediation` Stage3 side is closure_candidate; Stage4 side is blocked by the advisory loop lane.
- `0_0-stage3-semantic-fidelity-remediation` is now closed via `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`.
- `frontier-lag-soak-canary-wave1` stays parked; it is not a prerequisite for either upstream lane.
- `npc-martial-state-substrate-wave1` stays blocked and does not constrain any active lane.

## 4. Execution Order

1. `0_0-stage4-ep2-advisory-escalation-loop-remediation`
2. `0_0-stage2-stage3-stage4-readiness-remediation`
3. `frontier-lag-soak-canary-wave1`
4. `npc-martial-state-substrate-wave1`

Order rationale:

- priority 1 is the advisory loop remediation — direct Stage4 blocker, bounded 3-tranche patch
- priority 2 is the parent upstream lane — Stage4 sub-verdict depends on priority 1 completing
- priority 3 remains a parked soak lane
- priority 4 remains blocked and cannot outrank an executable lane

## 5. Per-Item Status Ledger

### 0_0-stage4-ep2-advisory-escalation-loop-remediation

- bounded survey completed (2026-04-01)
- execution SSOT: `partially_realized`
- 3 tranches: FlashbackVerifier prompt precision + strong advisory persistence + post_select_conflict observability
- next action:
  - keep Stage4 paused
  - run bounded runtime closure proof for ep2 advisory loop
  - defer canary execution to separate operator order after closure-proof decision
- temp cleanup action:
  - do not remove mirror until 3 tranches realized + tests pass + closure audit complete
- Stage4 remains paused throughout

### 0_0-stage2-stage3-stage4-readiness-remediation

- ctxnorm_r1 canary complete (2026-04-01)
- Stage3 sub-verdict: closure_candidate
- Stage4 sub-verdict: blocked_upstream_advisory_escalation_loop
- parent lane verdict: partial
- next action:
  - wait for advisory loop remediation lane to complete
  - then: consider ep5 tactical_semantic_fidelity CRITICAL confirmation
  - then: canary re-verification decision
  - Stage4 remains paused until advisory loop remediation completes + canary passes
- temp cleanup action:
  - do not remove mirror until Stage4 sub-verdict advances beyond blocked

### frontier-lag-soak-canary-wave1

- next action:
  - stay parked
- temp cleanup action:
  - remove mirror on explicit closure or replacement

### npc-martial-state-substrate-wave1

- next action:
  - stay blocked pending fresh evidence
- temp cleanup action:
  - remove mirror only after reactivation decision or formal closure

## 6. Cleanup Rule

- canonical execution SSOTs remain in dated `docs/`
- temp mirrors remain the active queue only until each item is realized or formally closed
- when the queue is exhausted, remove:
  - temp execution SSOT mirrors
  - `docs/temp/execution-roadmap.md`
  - `docs/temp/queue-state.json`

## 7. 3-Pass Audit Record (Refresh)

### Pass 1. Structure and Scope

- queue inventory updated to 4 items
- new advisory loop lane added as priority 1
- parent readiness lane demoted to priority 2 (dependency on advisory loop)
- execution order reflects the dependency

### Pass 2. Evidence and Consistency

- canonical and temp paths for new lane verified against filesystem
- parent lane's Stage4 blocked status consistent with advisory loop lane being prerequisite
- parked/blocked items unchanged

### Pass 3. Execution and Readability

- per-item status ledger updated with concrete next actions for new lane
- dependency chain: advisory loop → parent readiness → canary → Stage4 resume
- no overreach: canary not promoted, Stage4 resume not declared

Confidence: `96%`
