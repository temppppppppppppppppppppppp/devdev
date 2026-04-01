# Active Temp Execution Roadmap

Date: 2026-04-01
Status: active (3-pass audited)
Canonical Path: `docs/2026-04-01/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Baseline Dirty Summary: `dirty: 0_0 runtime logs/db/artifacts active; legacy temp queue mirrors present; 2026-03-31 0_0 survey docs untracked`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `user explicitly redirected away from parked legacy items to Stage2/3 Stage4-readiness remediation`
Supersedes:
- `docs/2026-03-31/active-temp-execution-roadmap.md`

Queue Snapshot:
- `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
- `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md`
- `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`

## 1. Purpose

This roadmap is the active controller for the current `docs/temp/` execution queue.

This refresh keeps the parent upstream lane active after closing its semantic-fidelity follow-up:

1. `0_0-stage2-stage3-stage4-readiness-remediation`

The new lane outranks the older temp items because:

- the user explicitly redirected work to the fresh `0_0` upstream blocker
- the new survey proved this blocker is currently gating Stage 4 progression
- the remaining legacy temp items were already `parked` or `blocked`

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `0_0-stage2-stage3-stage4-readiness-remediation` | `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | `docs/temp/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md` | in_progress | substrate lane; semantic fidelity follow-up closed |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | parked | non-critical soak lane |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | awaits fresh evidence and explicit reactivation |

## 3. Dependency Notes

- `0_0-stage3-semantic-fidelity-remediation` is now closed via `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`.
- `0_0-stage2-stage3-stage4-readiness-remediation` now has its semantic-fidelity blocker removed and becomes the next operator decision point.
- `frontier-lag-soak-canary-wave1` stays parked; it is not a prerequisite for the new upstream lane.
- `npc-martial-state-substrate-wave1` stays blocked and does not constrain the new upstream lane.

## 4. Execution Order

1. `0_0-stage2-stage3-stage4-readiness-remediation`
2. `frontier-lag-soak-canary-wave1`
3. `npc-martial-state-substrate-wave1`

Order rationale:

- priority 1 is the parent upstream lane, now unblocked by the closed semantic-fidelity follow-up
- priority 2 remains a parked soak lane
- priority 3 remains blocked and cannot outrank an executable lane

## 5. Per-Item Status Ledger

### 0_0-stage2-stage3-stage4-readiness-remediation

- next action:
  - keep Stage 4 paused
  - treat tranche A/B plus semantic-fidelity follow-up as landed substrate
  - decide whether to close the parent lane or run a bounded `Stage3 -> Stage4` restart canary before Stage 4 is reconsidered
- temp cleanup action:
  - remove mirror after implementation and closure audit

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

Confidence: `96%`
