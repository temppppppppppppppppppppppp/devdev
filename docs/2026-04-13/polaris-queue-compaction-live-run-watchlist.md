# Polaris Queue Compaction Live-Run Watchlist

- Date: 2026-04-13
- Status: draft-live-run-pending
- Scope: bounded queue-compaction watchlist for the current system execution queue while the active live run remains in flight on current `main`
- Mode: live-merge support note; this is a compaction proposal, not a final queue rewrite
- Canonical Path: `docs/2026-04-13/polaris-queue-compaction-live-run-watchlist.md`
- Baseline Commit: `347acac374f7246cca433d4be9c7466e802c9883`
- Baseline Dirty Summary: `dirty: active live-run artifacts plus current Stage3 runtime/tests/docs patches already present in worktree`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none at watchlist capture; live-run evidence is still moving and final queue mutation must wait for post-run merge`
- Confidence: `95% for the static queue watchlist; 0% for any final queue cleanup claim until the run terminates`

## Purpose

This watchlist answers one bounded question:

How much of the current queue can be compressed with low or medium loss once the active live run reaches a terminal state?

This document does not change:

- `docs/temp/` mirrors
- `docs/temp/queue-state.json`
- ClickUp tasks

## Evidence Anchors

- Current machine-readable queue snapshot:
  - [docs/temp/queue-state.json](/c:/Users/wjjo/Desktop/글도비/docs/temp/queue-state.json:1)
- Current canonical roadmap:
  - [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:120)
- Temp-queue contract:
  - [temp-queue-state-contract-v1.json](/c:/Users/wjjo/Desktop/글도비/docs/implementation/temp-queue-state-contract-v1.json:1)
- Queue harness:
  - [temp-execution-queue-roadmap-harness.md](/c:/Users/wjjo/Desktop/글도비/docs/implementation/temp-execution-queue-roadmap-harness.md:17)
- Cross-stage Polaris anchor:
  - [stage0-stage2-stage3-stage4-cross-stage-north-star-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage0-stage2-stage3-stage4-cross-stage-north-star-operating-note.md:1)

## Queue Snapshot

Static snapshot from the current `docs/temp/queue-state.json`:

- `active_item_count = 21`
- queue roles:
  - `front_active = 13`
  - `blocked_holding = 3`
  - `historical_backing = 5`
- statuses:
  - `in_progress = 18`
  - `blocked = 2`
  - `completed = 1`

This already shows visible inflation:

- `historical_backing` items still count inside the active temp queue
- many items remain `in_progress` even when their canonical text now says “proof pending,” “deferred verifier,” or “no longer active queue work”
- `active_item_count` is therefore a total queue-membership count, not a true active-surface count under the current v1 contract

## Immediate Low-Loss Compression Candidates

These candidates are the safest post-run removals because their canonical roadmap text already calls them historical or closed:

1. `0_0-stage34-ep2-single-episode-demo-canary`
2. `0_0-stage4-ep2-advisory-escalation-loop-remediation`
3. `0_0-stage4-canonical-entity-postselect-remediation`
4. `0_0-stage4-flashback-continuity-localfix-remediation`
5. `0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation`

Evidence:

- these five items already sit in `queue_role = historical_backing` inside the machine-readable queue
- the roadmap explicitly describes them as `historical backing only`, `runtime-positive substrate`, or `no longer active queue work`: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:133), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:137)

Loss assessment:

- evidence loss: none, because canonical docs remain
- operator loss: low, because active temp count drops without deleting canonical history
- automation risk: low, because the queue contract already recognizes `historical_backing`

## Medium-Loss Reclassification Candidates

These are not immediate deletions. They are candidates for status/role compression after the run completes.

### A. Proof-pending rather than active-realization

Candidate items:

1. `0_0-stage3-opening-transition-contract-normalization-remediation`
2. `0_0-stage2-contract-normalization-remediation`
3. `0_0-stage4-consumer-contract-normalization-remediation`
4. `0_0-stage4-repair-contract-normalization-remediation`
5. `0_0-stage234-nonwuxia-state-lock-overreach-remediation`

Why:

- their current canonical text emphasizes `proof remains pending`, `verification-pending`, or `fresh proof rather than a new broad patch`: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:68), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:69), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:70), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:71)

Loss assessment:

- evidence loss: none
- operator loss: low to medium, because the visual urgency drops
- contract risk: medium, because `temp-queue-state-contract-v1` does not yet encode `proof_pending` explicitly; it is currently inferred from canonical text rather than stored as a first-class field

### B. Deferred debt rather than front-active execution

Candidate items:

1. `0_0-stage3-partial-fix-hardening-remediation`
2. `0_0-stage2-partial-fix-hardening-remediation`
3. `0_0-stage4-interview-round-owner-surface-reduction-remediation`
4. `stage0-treatment-enrich-retirement-remediation`
5. `stage0-bi-tr-production-harness-normalization-remediation`
6. `frontier-lag-soak-canary-wave1`

Why:

- the roadmap already describes these as `deferred verifier`, `operator-parked-by-default`, `below the current functional proof stack`, or long-horizon hygiene/normalization rather than near-front action: [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:73), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:74), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:77), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:78), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:79), [active-temp-execution-roadmap.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-01/active-temp-execution-roadmap.md:81)

Loss assessment:

- evidence loss: none
- operator loss: medium, because these items become less visible in the main queue
- contract risk: medium, because the current queue-state schema only supports `front_active`, `blocked_holding`, `parked_future_wave`, and `historical_backing`

## Compression Boundary

The current queue-state contract can already support only part of the desired compression:

- historical backing cleanup: yes
- blocked holding: yes
- parked future wave: yes
- explicit proof-pending and explicit deferred-debt: not yet first-class in `temp-queue-state-contract-v1`
- true `active_surface_count` separate from total queue membership: not yet first-class in `temp-queue-state-contract-v1`

This means post-run compaction should likely happen in two steps:

1. immediate low-loss cleanup using the current contract
2. later contract/harness upgrade so proof and deferred-debt are first-class rather than implied by prose

Current repo vs ClickUp reality:

- repo queue-state v1 is intentionally strict and cannot carry extra posture fields without a schema revision: [temp-queue-state-contract-v1.json](/c:/Users/wjjo/Desktop/글도비/docs/implementation/temp-queue-state-contract-v1.json:5)
- ClickUp already infers `Proof Pending` from canonical prose, but that is still heuristic reflection rather than repo-side truth: [sync_clickup_queue.py](/c:/Users/wjjo/Desktop/글도비/scripts/sync_clickup_queue.py:166), [sync_clickup_queue.py](/c:/Users/wjjo/Desktop/글도비/scripts/sync_clickup_queue.py:245)

Minimal v2 boundary worth considering later:

- keep current `status`
- keep current `queue_role`
- add `execution_posture`
- split `active_surface_count` from `total_item_count`

## ClickUp Consequence

The existing ClickUp operating note already points in the right direction:

- `Proof Pending` exists as a ClickUp status
- `historical_backing` should be treated as `Closed`
- historical backing should leave the main active view: [clickup-system-development-direction-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-10/clickup-system-development-direction-operating-note.md:201), [clickup-system-development-direction-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-10/clickup-system-development-direction-operating-note.md:204), [clickup-system-development-direction-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-10/clickup-system-development-direction-operating-note.md:405)

Provisional implication:

- once the run finishes and repo-side queue artifacts are updated, ClickUp compression should be low-risk for historical and proof-only items

## Post-Run Action Ladder

After the active live run reaches a terminal state:

1. run the post-run merge audit
2. remove the five `historical_backing` temp mirrors if the merged audit does not reopen them
3. refresh the canonical roadmap wording so proof-only and deferred-debt items stop masquerading as front-active
4. refresh `docs/temp/queue-state.json`
5. run `python scripts/ops_validator.py --strict`
6. then reflect the compressed queue into ClickUp

## Loss Judgment

Bottom line:

- compressing the five historical-backing items is low-loss and high-value
- compressing proof-only and deferred-debt items is medium-loss but still worthwhile
- the bigger risk is not loss of evidence; it is temporary friction while the queue contract catches up to the truer status model

## 3-Pass Audit Notes

Pass 1:

- document type is a live-run watchlist, not a final roadmap rewrite
- scope is bounded to queue compression and loss analysis

Pass 2:

- claims are grounded in the current queue-state snapshot, the canonical roadmap, and the current temp-queue contract
- no final queue cleanup claim is made while the run is active

Pass 3:

- the note is actionable because it identifies immediate low-loss cleanup vs medium-loss reclassification
- no temp mirror deletion or ClickUp sync is authorized from this draft
