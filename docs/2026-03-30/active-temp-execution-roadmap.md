# Active Temp Execution Roadmap

Date: 2026-03-31
Status: active (3-pass audited)
Canonical Path: `docs/2026-03-30/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
- Baseline Dirty Summary: `dirty: active stage4 runtime/tests/log-db drift, active temp queue, prior 2026-03-30 docs still untracked, new 2026-03-31 CW survey/SSOT docs added`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Supersedes:
- `docs/2026-03-29/stage4-and-legacy-execution-roadmap.md`

Queue Snapshot:
- `docs/temp/0_1-stage4-cw-first-pass-false-miss-remediation-execution-ssot.md`
- `docs/temp/0_1-stage4-ep9-remediation-execution-ssot.md`
- `docs/temp/0_1-stage3-blueprint-fix-execution-ssot.md`
- `docs/temp/stage3-blueprint-validator-hardening-execution-ssot.md`
- `docs/temp/stage3-capital-unit-drift-hardening-execution-ssot.md`
- `docs/temp/stage4-provider-fallback-observability-gap-execution-ssot.md`
- `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md`
- `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`

## 1. Purpose

이 roadmap은 현재 `docs/temp/`의 active execution SSOT를 한 표로 묶는 컨트롤 문서다.

이번 refresh의 의미는 두 가지다.

1. EP9 root-cause remediation lane이 active queue에 새로 admission되었다.
2. 기존 stage3/legacy queue는 유지하되, 현재 사용자 요청과 Stage 4 shared substrate leverage를 반영해 EP9 lane을 최상단으로 재정렬한다.

Closed mirror on 2026-03-30:

- `docs/temp/material-side-block-arc-harness-normalization-execution-ssot.md`

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `0_1-stage4-cw-first-pass-false-miss-remediation` | `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-execution-ssot.md` | `docs/temp/0_1-stage4-cw-first-pass-false-miss-remediation-execution-ssot.md` | in_progress | code landed and statically validated; fresh live rerun / merged closure audit still pending |
| `0_1-stage4-ep9-remediation` | `docs/2026-03-30/0_1-stage4-ep9-remediation-execution-ssot.md` | `docs/temp/0_1-stage4-ep9-remediation-execution-ssot.md` | ready-for-execution | current Stage 4 blocker: NpcDrift authority + advisory escalation deadlock + retry attribution |
| `0_1-stage3-blueprint-fix` | `docs/2026-03-30/0_1-stage3-blueprint-fix-execution-ssot.md` | `docs/temp/0_1-stage3-blueprint-fix-execution-ssot.md` | pending | bounded artifact fix lane |
| `stage3-blueprint-validator-hardening` | `docs/2026-03-30/stage3-blueprint-validator-hardening-execution-ssot.md` | `docs/temp/stage3-blueprint-validator-hardening-execution-ssot.md` | ready-for-execution | validator contract hardening lane |
| `stage3-capital-unit-drift-hardening` | `docs/2026-03-30/stage3-capital-unit-drift-hardening-execution-ssot.md` | `docs/temp/stage3-capital-unit-drift-hardening-execution-ssot.md` | ready-for-execution | preventive Stage 3 capital drift lane |
| `stage4-provider-fallback-observability-gap` | `docs/2026-03-29/stage4-provider-fallback-observability-gap-execution-ssot.md` | `docs/temp/stage4-provider-fallback-observability-gap-execution-ssot.md` | pending | execution-ready but currently lower ROI than docs and Stage 3 integrity lanes |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | parked | non-critical soak lane |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | awaits fresh evidence and explicit reactivation |

## 3. Dependency Notes

- `material-side-block-arc-harness-normalization` was independent of the runtime lanes and is now closed.
- `0_1-stage4-cw-first-pass-false-miss-remediation` is the current user-requested Stage 4 lane and should run before older deferred Stage 4 observability work.
- `0_1-stage4-cw-first-pass-false-miss-remediation` does not replace the already-landed EP9 NpcDrift patch; it extends diagnosis fidelity and first-pass prompt/carryover hardening above that substrate.
- `0_1-stage4-ep9-remediation` is independent of the Stage 3 lanes and should not wait on them.
- `0_1-stage4-ep9-remediation` partially reuses the code-contract seam already documented in canonical-only `docs/2026-03-30/0_1-ep8-artifact-vs-code-execution-ssot.md`, but that EP8 doc is not a temp-queue authority item.
- `0_1-stage4-ep9-remediation` has higher runtime leverage than `stage4-provider-fallback-observability-gap` because it fixes a current live Stage 4 quality gate seam rather than a lower-ROI observability lane.
- the new harness lane does not unblock or block Stage 3 / Stage 4 code paths; it exists to normalize operator-facing semantics before any harness patch wave starts.
- `stage3-capital-unit-drift-hardening` references `stage3-blueprint-validator-hardening` as a related guardrail lane.
- `stage4-provider-fallback-observability-gap` remains independent but lower priority under current operator focus.
- `frontier-lag-soak-canary-wave1` and `npc-martial-state-substrate-wave1` remain parked legacy items.

## 4. Execution Order

1. `0_1-stage4-cw-first-pass-false-miss-remediation`
2. `0_1-stage4-ep9-remediation`
3. `0_1-stage3-blueprint-fix`
4. `stage3-blueprint-validator-hardening`
5. `stage3-capital-unit-drift-hardening`
6. `stage4-provider-fallback-observability-gap`
7. `frontier-lag-soak-canary-wave1`
8. `npc-martial-state-substrate-wave1`

Order rationale:

- CW false-miss remediation is the direct current user-requested Stage 4 lane
- it improves diagnosis fidelity and first-pass authority framing without reopening model/provider work
- EP9 remediation remains important but is now the second Stage 4 item
- EP9 remediation fixes a shared Stage 4 correctness seam (`NpcDrift` authority + impossible escalation contract) with bounded verification
- the Stage 3 items remain actionable but are not the active user-requested lane
- the Stage 4 provider item remains execution-ready but explicitly lower ROI than the EP9 correctness lane
- the last two items stay parked until reactivated

## 5. Per-Item Status Ledger

### material-side-block-arc-harness-normalization

- closed history:
  - docs-only harness lane realized on `2026-03-30`
  - touched Stage 0 harness docs passed 3-pass adversarial audit and UTF-8 hygiene
  - temp mirror removed during closure

### 0_1-stage3-blueprint-fix

- next action:
  - follow canonical SSOT if the operator reactivates the artifact fix lane
- temp cleanup action:
  - remove mirror after bounded artifact patch and closure validation

### 0_1-stage4-ep9-remediation

- next action:
  - use the canonical SSOT as the governing document for the next bounded Stage 4 patch wave
  - re-audit the canonical SSOT against the live workspace immediately before code edits
- temp cleanup action:
  - remove mirror after code/test realization, closure audit, roadmap refresh, and queue-state sync

### 0_1-stage4-cw-first-pass-false-miss-remediation

- next action:
  - run a fresh Stage 4 live rerun and merge the resulting evidence before any closure claim
  - if runtime misses persist, prioritize residual seams in this order: escalation contract, prompt re-anchor, carryover extractor
- temp cleanup action:
  - remove mirror after live rerun evidence, merged closure audit, roadmap refresh, and queue-state sync

### stage3-blueprint-validator-hardening

- next action:
  - follow canonical SSOT if Stage 3 validator lane is reactivated
- temp cleanup action:
  - remove mirror after code/test closure

### stage3-capital-unit-drift-hardening

- next action:
  - execute only after re-auditing the canonical SSOT against the live workspace
- temp cleanup action:
  - remove mirror after preventive validator lane lands and validates

### stage4-provider-fallback-observability-gap

- next action:
  - remain deferred unless observability ROI rises again
- temp cleanup action:
  - remove mirror only after live validation or formal park/closure decision

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

- if the harness lane is realized first, remove only `docs/temp/material-side-block-arc-harness-normalization-execution-ssot.md`
- keep the canonical dated SSOT in `docs/2026-03-30/`
- update this roadmap status after each realized item
- when the temp queue becomes empty, remove `docs/temp/execution-roadmap.md` and optional `docs/temp/queue-state.json`
