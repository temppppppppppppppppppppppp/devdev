# Active Temp Execution Roadmap

Date: 2026-04-23
Status: active (2026-04-23 issue-5 formalization re-audit; an independent proof-governor lane is now inserted ahead of session-memory rollout, leaving 3 honest parked items)
Canonical Path: `docs/2026-04-23/active-temp-execution-roadmap.md`
Temp Mirror Path: `docs/temp/execution-roadmap.md`
Baseline Commit: `30b9436fc3a5c3fcc3f6397bf23bfe45d24af918`
Baseline Dirty Summary: `dirty: prior queue-refresh temp docs plus untracked 2026-04-23 docs; no unrelated project-data cleanup performed`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `issue #5 was promoted from embedded governor posture to a standalone parked execution lane`

## 1. Why This Refresh Exists

The earlier 2026-04-23 queue refresh fixed the stale Golden Canary and `00_0420` front-blocker assumptions, but it still left too many old parked and blocked items visible.

The first live compaction re-audit reduced that residue to four parked items, but the remaining board still mixed true cross-stage debt with lanes whose debt was real yet no longer worthy of visible queue authority.

The ROI re-audit then checked each remaining item against current code or current project-anchor truth:

- candidate-only audit memo lanes must not stay visible unless they still represent a bounded execution order
- missing-anchor blocked lanes must not stay visible just because backups still exist
- already-landed substrate work must not stay visible as fake blocked debt

After that compaction, one more governance mismatch remained:

- GitHub issue `#5` existed as a real proof and benchmark governor, but the visible queue still hid it inside `stage234-session-memory-max-utilization`

The fresh codebase-centered re-audit on `2026-04-23` confirmed that `#5` has enough live authority and benchmark substrate to become its own parked execution lane.

## 2. Priority Basis

- `authority-alignment-benchmark-operating-model-hardening` is now first because it is the proof and benchmark governor for `stage234-session-memory-max-utilization` and a reusable substrate for later donor or ensemble experiments
- `stage234-session-memory-max-utilization` remains the highest-upside rollout lane, but it now sits second because its first honest tranche depends on the new standalone `#5` proof lane
- `stage0-bi-tr-production-harness-normalization-remediation` remains honest because runtime handoff still flows through a declared compatibility bridge and `db_anchor:bible`
- `0_0-stage4-interview-round-owner-surface-reduction-remediation` is retired because the current owner pressure is real but purely architectural, with no active consumer pressure justifying visible queue authority
- `stage0-treatment-enrich-retirement-remediation` is retired because the path is already explicit opt-in non-canonical utility behavior with separate `*_enriched.json` output
- `audit-report-candidate-revalidation-remediation`, `00_0420-s2-s3-s4-authority-alignment-remediation`, `0_0-stage2-stage3-stage4-readiness-remediation`, `npc-martial-state-substrate-wave1`, `frontier-lag-soak-canary-wave1`, `0_0-stage4-interview-round-owner-surface-reduction-remediation`, and `stage0-treatment-enrich-retirement-remediation` are retired from the visible queue and preserved canonically as historical backing only

## 3. Queue Semantics

- `parked future wave`: still-real execution debt, but not current implementation authority
- `historical backing`: keep the canonical SSOT for audit history, remove the temp mirror from the active queue

Working order:
1. `authority-alignment-benchmark-operating-model-hardening` (parked future wave; upstream proof and benchmark governor for `#3` and related experiment lanes)
2. `stage234-session-memory-max-utilization` (parked future wave; cross-stage memory/cache rollout lane now dependent on item 1)
3. `stage0-bi-tr-production-harness-normalization-remediation` (parked future wave; Stage0 runtime handoff normalization remains open)

Closed historical backing in this compaction:

- `audit-report-candidate-revalidation-remediation`
- `00_0420-s2-s3-s4-authority-alignment-remediation`
- `0_0-stage2-stage3-stage4-readiness-remediation`
- `npc-martial-state-substrate-wave1`
- `frontier-lag-soak-canary-wave1`
- `0_0-stage4-interview-round-owner-surface-reduction-remediation`
- `stage0-treatment-enrich-retirement-remediation`

## 4. Immediate Next Moves

1. keep only the 3 still-honest parked items on the visible temp queue
2. expose `#5` explicitly ahead of `#3`
3. refresh `docs/temp/queue-state.json`
4. validate the queue after promotion
5. reflect the queue to ClickUp only if the user explicitly asks for it

## 5. Cleanup Rule

- keep temp mirrors only for the 3 still-live parked items
- preserve retired items canonically, but do not keep them as visible queue residue
- do not reopen the retired missing-anchor lanes without a fresh live anchor and a fresh bounded survey
- do not reopen the retired npc-martial substrate lane unless a new post-wave consumer lane is explicitly opened
- do not reopen frontier-lag soak unless a future operator explicitly reprioritizes the durability-surface audit block
- do not reopen the retired Stage4 owner-surface lane unless a fresh Stage4 functional wave or explicit reprioritization creates a bounded extraction need
- do not reopen Stage0 enrich unless a future operator explicitly opens a hard quarantine, default-off hardening, or removal wave

## Pass 1

- every remaining parked or blocked item was rechecked against live code or live anchor truth
- missing-anchor items were not given special treatment merely because backup trees existed
- already-landed substrate work was not allowed to remain visible as blocked debt

## Pass 2

- the board now separates live parked debt from historical reference memos
- the 3 kept items each still have a direct current code reason to remain visible
- the 7 retired items each have a concrete reason they no longer belong on the visible queue

## Pass 3

- the compacted board remains small but now matches the real dependency graph better
- ClickUp no longer drives the queue; if mirrored later, it should reflect this 3-item parked board rather than a stale 2-item snapshot
- historical backing stays preserved without polluting the active temp surface

Confidence: 98/100
