# Geuldobi V2 Quality Maximization Follow-On Aggregate Execution Roadmap

Date: 2026-03-17
Status: completed
Canonical Path: `docs/2026-03-17/geuldobi-v2-quality-maximization-follow-on-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Commit State:
- Baseline Commit: `2352b26a293ac330a0ff24da320363f9abdbbba1`
- Baseline Dirty Summary: `dirty: lane1~3 code/tests/docs edits, temp mirror deletions, runtime log, survey bundle docs/evidence, and unrelated local drafts; preserve as-is`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `same commit; all 4 items realized and closed; queue empty`
Queue Snapshot:
- (empty — all items completed)

## 1. Purpose
- govern the first follow-on execution cycle opened from the merged `geuldobi-v2-quality-maximization` survey bundle
- provide the only roadmap with SSOT authority for this active execution queue
- keep the queue to four substrate-first items rather than fragmenting it into parallel proof or telemetry micro-lanes

## 2. Queue Inventory

| Item | Canonical Path | Temp Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `context-provenance-and-budget-contract` | `docs/2026-03-17/geuldobi-v2-context-provenance-budget-contract-execution-ssot.md` | removed after closure | completed | Stage 2/3/4 lineage and budget substrate |
| `gate-repair-observability-chain` | `docs/2026-03-17/geuldobi-v2-gate-repair-observability-chain-execution-ssot.md` | removed after closure | completed | durable/operator-visible survival of lane2/3 semantics |
| `prompt-config-authority-hygiene` | `docs/2026-03-17/geuldobi-v2-prompt-config-authority-hygiene-execution-ssot.md` | removed after closure | completed | canonical authority precedence and effective-source visibility |
| `runtime-control-plane-authority-hygiene` | `docs/2026-03-17/geuldobi-v2-runtime-control-plane-authority-hygiene-execution-ssot.md` | removed after closure | completed | supported runtime path and operator-truth normalization |

## 3. Dependency Graph
- `context-provenance-and-budget-contract -> gate-repair-observability-chain`
- `context-provenance-and-budget-contract -> prompt-config-authority-hygiene`
- `gate-repair-observability-chain -> runtime-control-plane-authority-hygiene`
- `prompt-config-authority-hygiene -> runtime-control-plane-authority-hygiene`
- shared substrate:
  - durable truth versus snapshot truth
  - config provenance and effective-source visibility
  - bounded operator-surface projection
- merge opportunities:
  - proof-path normalization belongs in per-item verification plus shared roadmap gating, not a separate SSOT
  - cost and long-run telemetry should ride with prompt/config and gate/observability work instead of splitting off

## 4. Execution Order
Priority basis:
- `docs/implementation/queue-priority-rubric.md`

1. `context-provenance-and-budget-contract`
2. `gate-repair-observability-chain`
3. `prompt-config-authority-hygiene`
4. `runtime-control-plane-authority-hygiene`

Priority rationale:
- item 1 has the highest shared substrate leverage and blocks cleaner reasoning about later drift
- item 2 gives the highest user-visible quality return after lane2/3 code already landed
- item 3 reduces repo-wide authority drift after provenance and semantic-survival targets are clearer
- item 4 has the broadest blast radius and should absorb clearer upstream truth rather than invent it first

## 5. Per-Item Plan

### context-provenance-and-budget-contract
- goal:
  - establish one Stage 2/3/4 provenance and budget ledger
- prerequisites:
  - none beyond current merged survey bundle
- execution notes:
  - keep Python as collector/router only
  - do not widen Stage 4 context payloads with debug noise
- completion signal:
  - provenance and budget facts are durable and test-covered
- temp cleanup action:
  - remove only this mirror after closure and mark roadmap item completed

### gate-repair-observability-chain
- goal:
  - carry lane2/3 semantics from raw Stage 4 truth to durable and operator-visible surfaces
- prerequisites:
  - item 1 completed
- execution notes:
  - keep final-authority versus snapshot semantics explicit
  - fold proof-path normalization into this lane's verification plan
- completion signal:
  - `gate_basis`, `repair_scope`, `fix_pack`, and related truth survive to intended consumers
- temp cleanup action:
  - remove only this mirror after closure and mark roadmap item completed

### prompt-config-authority-hygiene
- goal:
  - define one precedence map per prompt/config family and surface effective-source truth
- prerequisites:
  - item 1 completed
- execution notes:
  - absorb telemetry-source cleanup here instead of spinning out a separate telemetry SSOT
- completion signal:
  - key budgets, thresholds, and prompts have one visible authority story
- temp cleanup action:
  - remove only this mirror after closure and mark roadmap item completed

### runtime-control-plane-authority-hygiene
- goal:
  - codify the supported runtime/control-plane path and normalize operator truth
- prerequisites:
  - items 2 and 3 completed
- execution notes:
  - quarantine compatibility residue only after supported-path semantics are clearer
- completion signal:
  - public authority path, compatibility labels, and boot/runtime truth routing are coherent
- temp cleanup action:
  - remove only this mirror after closure and mark roadmap item completed

## 6. Shared Risks and Side-Effects
- shared write paths:
  - Stage 4 metadata sinks, runtime logs, bridge/operator payloads, and config-linked summaries
- shared DB/schema touchpoints:
  - durable truth or provenance fields may require schema or JSON payload adjustments
- shared logs/UI surfaces:
  - dashboard, bridge, desktop, and audit logs
- rollback/recovery concerns:
  - provenance or authority changes must not silently fall back to stale snapshot fields
- queue collision or ordering risks:
  - item 3 should not run first just because it looks local; provenance and semantic-survival work define what it needs to expose

## 7. Status Ledger

| Item | Status | Last Update | Blocker |
| --- | --- | --- | --- |
| `context-provenance-and-budget-contract` | completed | 2026-03-17 | none |
| `gate-repair-observability-chain` | completed | 2026-03-17 | none |
| `prompt-config-authority-hygiene` | completed | 2026-03-17 | none |
| `runtime-control-plane-authority-hygiene` | completed | 2026-03-17 | authority contract wired into live payload helpers; `/quality/summary` labeled; desktop-vs-engine boot surfaces split; smoke tests extended |

Allowed statuses:
- pending
- in_progress
- completed
- blocked

## 8. Queue Cleanup Rule
- remove a temp execution SSOT mirror immediately after that item is realized and closed
- keep canonical dated docs
- when all items are completed, remove `docs/temp/execution-roadmap.md`
- remove `docs/temp/queue-state.json` if present
- leave `docs/temp/README.md`
