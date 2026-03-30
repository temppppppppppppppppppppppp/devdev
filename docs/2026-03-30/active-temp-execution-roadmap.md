# Active Temp Execution Roadmap

Date: 2026-03-30
Status: active (3-pass audited)
Canonical Path: `docs/2026-03-30/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `e52c061ac1f3fdb95a4b1149b4ea66243961656a`
- Baseline Dirty Summary: `dirty: tracked narrative docs and stage0 harness docs, tracked chaebol TR/BI artifacts, many pre-existing untracked temp/reference assets`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Supersedes:
- `docs/2026-03-29/stage4-and-legacy-execution-roadmap.md`

Queue Snapshot:
- `docs/temp/0_1-stage3-blueprint-fix-execution-ssot.md`
- `docs/temp/stage3-blueprint-validator-hardening-execution-ssot.md`
- `docs/temp/stage3-capital-unit-drift-hardening-execution-ssot.md`
- `docs/temp/stage4-provider-fallback-observability-gap-execution-ssot.md`
- `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md`
- `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md`

## 1. Purpose

이 roadmap은 현재 `docs/temp/`의 active execution SSOT를 한 표로 묶는 컨트롤 문서다.

이번 refresh의 의미는 두 가지다.

1. 기존 stage4/legacy queue 위에 새 `material-side harness semantics` lane이 추가되었다.
2. 그 lane은 현재 realized + closed 상태이며, 사용자의 우선순위가 `runtime code`가 아니라 `하네스 semantics`였다는 점을 queue history에 반영한다.

Closed mirror on 2026-03-30:

- `docs/temp/material-side-block-arc-harness-normalization-execution-ssot.md`

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `0_1-stage3-blueprint-fix` | `docs/2026-03-30/0_1-stage3-blueprint-fix-execution-ssot.md` | `docs/temp/0_1-stage3-blueprint-fix-execution-ssot.md` | pending | bounded artifact fix lane |
| `stage3-blueprint-validator-hardening` | `docs/2026-03-30/stage3-blueprint-validator-hardening-execution-ssot.md` | `docs/temp/stage3-blueprint-validator-hardening-execution-ssot.md` | ready-for-execution | validator contract hardening lane |
| `stage3-capital-unit-drift-hardening` | `docs/2026-03-30/stage3-capital-unit-drift-hardening-execution-ssot.md` | `docs/temp/stage3-capital-unit-drift-hardening-execution-ssot.md` | ready-for-execution | preventive Stage 3 capital drift lane |
| `stage4-provider-fallback-observability-gap` | `docs/2026-03-29/stage4-provider-fallback-observability-gap-execution-ssot.md` | `docs/temp/stage4-provider-fallback-observability-gap-execution-ssot.md` | pending | execution-ready but currently lower ROI than docs and Stage 3 integrity lanes |
| `frontier-lag-soak-canary-wave1` | `docs/2026-03-27/frontier-lag-soak-canary-wave1-execution-ssot.md` | `docs/temp/frontier-lag-soak-canary-wave1-execution-ssot.md` | parked | non-critical soak lane |
| `npc-martial-state-substrate-wave1` | `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md` | `docs/temp/npc-martial-state-substrate-wave1-execution-ssot.md` | blocked | awaits fresh evidence and explicit reactivation |

## 3. Dependency Notes

- `material-side-block-arc-harness-normalization` was independent of the runtime lanes and is now closed.
- the new harness lane does not unblock or block Stage 3 / Stage 4 code paths; it exists to normalize operator-facing semantics before any harness patch wave starts.
- `stage3-capital-unit-drift-hardening` references `stage3-blueprint-validator-hardening` as a related guardrail lane.
- `stage4-provider-fallback-observability-gap` remains independent but lower priority under current operator focus.
- `frontier-lag-soak-canary-wave1` and `npc-martial-state-substrate-wave1` remain parked legacy items.

## 4. Execution Order

1. `0_1-stage3-blueprint-fix`
2. `stage3-blueprint-validator-hardening`
3. `stage3-capital-unit-drift-hardening`
4. `stage4-provider-fallback-observability-gap`
5. `frontier-lag-soak-canary-wave1`
6. `npc-martial-state-substrate-wave1`

Order rationale:

- the docs-only harness lane that had current operator priority is now closed
- the Stage 3 items remain actionable but are not the active user-requested lane
- the Stage 4 provider item remains execution-ready but explicitly lower ROI
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
