# Active Temp Execution Roadmap

Date: 2026-03-31
Status: active (3-pass audited)
Canonical Path: `docs/2026-03-31/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
Baseline Dirty Summary: `dirty: active stage4 runtime/tests/log-db drift, active temp queue/roadmap already dirty, multiple 2026-03-30 and 2026-03-31 docs plus artifact outputs untracked`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `stage4-cw-webnovel-identity-context-hierarchy-remediation, 0_1-stage4-cw-first-pass-false-miss-remediation, 0_1-stage4-retry-efficiency-remediation, and 0_1-stage4-ep9-remediation all closed after runtime validation plus bounded closure audit; mirrors retired from docs/temp`
Supersedes:
- `docs/2026-03-30/active-temp-execution-roadmap.md`

Queue Snapshot:
- `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md`
- `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`

## 1. Purpose

This roadmap is the current controller for the aggregate `docs/temp/` execution queue.

This refresh now does nine specific things:

1. retires the now-validated `stage4-cw-webnovel-identity-context-hierarchy-remediation` lane from the active temp queue
2. retires the now-runtime-validated `0_1-stage4-cw-first-pass-false-miss-remediation` lane from the active temp queue
3. retires the now-runtime-bounded-validated `0_1-stage4-retry-efficiency-remediation` lane from the active temp queue
4. retires the now-runtime-validated `0_1-stage4-ep9-remediation` lane from the active temp queue
5. retires the now-closed `0_1-stage3-blueprint-fix` lane after bounded artifact synchronization
6. retires the now-validated `stage3-blueprint-validator-hardening` lane after focused validator regression closure
7. retires the now-validated `stage3-capital-unit-drift-hardening` lane after overlapping validator-owner closure
8. retires the now-validated `stage4-provider-fallback-observability-gap` lane after focused observability regression closure
9. leaves older legacy items visible without letting them outrank the current active sequence

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | parked | non-critical soak lane |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | awaits fresh evidence and explicit reactivation |

## 3. Dependency Notes

- `stage4-cw-webnovel-identity-context-hierarchy-remediation` is closed and no longer part of the active temp queue; runtime closure evidence came from `0_1` canary `EP10~14`.
- `0_1-stage4-cw-first-pass-false-miss-remediation` is closed and no longer part of the active temp queue; runtime closure evidence came from verdict-layer persistence in the same `0_1` canary window.
- `0_1-stage4-retry-efficiency-remediation` is now closed; the canary proved retry-lane attempt identity, while `[QR-7 escalation]` and `[TF-RH1]` remained runtime-not-exercised but non-contradicted and test-covered.
- `0_1-stage4-ep9-remediation` is now closed; live session `20260330_231345` published EP9 on round 1 and the mirror was retired after closure audit.
- `0_1-stage3-blueprint-fix` is now closed; EP8 txt mirror drift was synchronized to the already-repaired authoritative JSON, and EP15 alignment was revalidated without new artifact regeneration.
- `stage3-blueprint-validator-hardening` is now closed; the required collectors and binding verdict contract were already present in `unified_blueprint_validator.py` and validated by focused regression.
- `stage3-capital-unit-drift-hardening` is now closed; the `capital_unit` collector and binding escalation were already absorbed into the same validator owner and verified by the same focused regression lane.
- `stage4-provider-fallback-observability-gap` is now closed; the bounded observability correction was already present in `BaseAgent` and `MetricsCollector` and passed focused regression without further code change.
- the last two items remain parked legacy lanes.

## 4. Execution Order

1. `frontier-lag-soak-canary-wave1`
2. `npc-martial-state-substrate-wave1`

Order rationale:

- the just-closed hierarchy-remediation lane drops out of the active queue after runtime validation and temp cleanup
- the first-pass false-miss lane also drops out after runtime validation and temp cleanup
- the retry-efficiency lane also drops out after bounded runtime closure proof and targeted residual-branch test confirmation
- the EP9 lane now drops out after live pass closure and temp cleanup
- the bounded Stage 3 blueprint-fix lane now drops out after txt mirror synchronization and artifact validation
- the validator hardening lane now drops out after focused code/test closure
- the preventive capital-unit lane also drops out because its implementation already landed inside the same validator owner and test surface
- the provider-fallback observability lane now drops out after focused RC-1 through RC-4 regression closure
- the remaining legacy items keep their older lower-priority positions

## 5. Per-Item Status Ledger

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

Confidence: 96%
