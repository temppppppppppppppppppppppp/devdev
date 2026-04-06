# 04-06 Stage4 And Material Daily Roadmap

Date: 2026-04-06
Status: active
Scope: 2026-04-06 하루 동안 소화 가능한 Stage4 stabilization, queue hygiene, and material production plan grounded in the live temp queue and current material-side philosophy work
Canonical Path: `docs/2026-04-06/04-06-stage4-material-daily-roadmap.md`
Supersedes: none
Does Not Supersede:
- `docs/2026-04-01/active-temp-execution-roadmap.md`
Commit State:
- Baseline Commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`
- Baseline Dirty Summary: `dirty: 2 tracked + 2 untracked under material_ssot/20_pitch (README, pitch-philosophy, pitch-selection-checklist, protagonist-first-constitution)`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Docs:
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/temp/execution-roadmap.md`
- `docs/temp/queue-state.json`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-03/0_0-stage4-numeric-asset-authority-carryover-bounded-survey.md`
- `docs/2026-04-03/material-ssot-cross-pc-handoff.md`
- `docs/2026-04-05/00_0405-stage2-artifact-truth-observability-bounded-survey.md`
- `material_ssot/20_pitch/README.md`
- `material_ssot/20_pitch/pitch-philosophy.md`
- `material_ssot/20_pitch/pitch-selection-checklist.md`
- `material_ssot/20_pitch/protagonist-first-constitution.md`
- `material_ssot/20_pitch/intake/fresh_20260406_batch01/README.md`

## 1. Answer First

오늘 front queue를 다시 넓히는 날이 아니다.

The bounded 2026-04-06 reading is:

1. keep the system-track front on `Stage4 consumer umbrella -> numeric asset authority / carryover seam -> repair-contract sink/provenance follow-up`
2. do not reopen parked `Stage3`, `Stage2`, `cross-stage`, or `Stage0` waves as if they were today blockers
3. lock the newly forming `20_pitch` philosophy as a reusable bridge contract
4. produce fresh material outputs only within the philosophy's own `single` operating rule

So the realistic day shape is:

1. queue hygiene and active-lane reclassification
2. one bounded Stage4 stabilization tranche
3. one bounded material production tranche

Not:

1. broad cross-stage refactor
2. multi-candidate canon explosion
3. Stage2 or Stage3 promotion above Stage4

## 2. Current System Reading

### 2.1 Queue controller is still Stage4-first

The controlling roadmap already says the active order is:

1. `0_0-stage4-consumer-contract-normalization-remediation`
2. `0_0-stage4-repair-contract-normalization-remediation`
3. `0_0-stage2-stage3-stage4-readiness-remediation`
4. parked future waves below that

That remains the correct high-level reading on 2026-04-06.

### 2.2 Stage4 is no longer blocked by "can it pass at all"

The latest Stage4 evidence stack says:

- `ep2` can PASS through Stage4
- Stage4-only sinkproof is now positive
- flashback and `NpcDrift relation-tag` are no longer the front explanation
- the remaining bounded seam is `numeric asset authority / carryover owner-boundary`
- the nearest support lane beneath that seam is `repair-contract grammar / sink visibility`

This means today's Stage4 work should tighten owner boundary and evidence visibility, not relitigate old canary legitimacy.

### 2.3 Queue-state machine snapshot is stale relative to live doc truth

`docs/temp/queue-state.json` still marks several items as `in_progress` or `completed` in a way that no longer matches the actual temp execution docs and roadmap text.

On the 2026-04-06 readback, at least `11 / 16` queue items diverge between machine snapshot status and the live temp execution-doc status line.

The important consequence is operational, not archival:

- do not use `queue-state.json` alone as today's priority source
- use the roadmap plus live temp doc status lines first
- if queue tooling is touched today, reconcile the machine snapshot early

### 2.4 Stage2 and Stage3 are specified better, but still parked

The 2026-04-05 Stage2 survey improves the problem statement to:

- `content-sufficient but schema-fragile`
- `artifact packet -> txt round-trip drift`
- `observability weakness`

That is useful, but it still does not justify pulling Stage2 ahead of Stage4 today.

### 2.5 Material-side philosophy is now the live dirty worktree

The only live dirty paths are under `material_ssot/20_pitch`.

This is good drift, not random drift:

- `pitch-philosophy.md` is actively defining the bridge contract from `research -> pitch -> Stage0`
- `protagonist-first-constitution.md` and `pitch-selection-checklist.md` make the new house-law explicit
- `fresh_20260406_batch01` already provides three selection-ready candidates

So today's material work can move immediately from philosophy lock to one bounded production unit.

## 3. Today Priority Stack

Priority basis:

- active Stage4 queue ownership
- shared leverage over later queue work
- risk reduction from stale operator state
- compatibility with the new material-side `single` default

Today's stack:

1. queue hygiene for `actual active vs historical backing vs stale machine state`
2. Stage4 numeric carryover / authority stabilization under the consumer umbrella
3. repair-contract sink/provenance normalization only to the extent required by item 2
4. one selected fresh pitch tightened into the next stable material unit
5. reserve candidate ranking only if time remains

## 4. Bounded Daily Plan

### Tranche A. Queue Hygiene And Reclassification

Goal:

- make sure today's execution reading is driven by the real active queue, not stale machine residue

Tasks:

1. compare `docs/temp/queue-state.json` against the status lines in the temp execution SSOT files
2. classify each temp item into:
   - active front lane
   - parked future wave
   - historical runtime-positive substrate
   - blocked holding lane
3. refresh queue machine state only if the system-track work will actually rely on it today

Completion signal:

- one trustworthy "today active set" is explicit before any Stage4 code change

Why first:

- this is the cheapest way to prevent false reprioritization and wasted reopening of completed child lanes

### Tranche B. Stage4 Stabilization

Goal:

- reduce the remaining Stage4 front seam from "numeric asset authority / carryover mismatch exists" to one bounded owner-aligned implementation slice

Primary owner surfaces:

- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/core/fact_ledger.py`
- `modules/core/numeric_consistency_checker.py`
- Stage4 consumer-side retry/finalization owners only where boundary propagation is required

Today's exact target:

1. lock one authoritative numeric carryover story from intake through Stage4 finalization
2. prevent stale blueprint or packet truth from silently outranking the intended active authority
3. expose enough provenance so operator-visible evidence can explain which numeric truth won and why

Acceptance shape for today:

- the owner boundary is explicit enough to patch without opening new Stage2/3 work
- the implementation slice stays bounded to the numeric/carryover seam
- targeted validation proves no regression in the current Stage4 PASS path

Stop rule:

- if the fix expands into broad contract redesign, stop and re-scope back to the numeric carryover owner-boundary only

### Tranche C. Repair-Contract Support, Not Independent Expansion

Goal:

- use the parked repair-contract lane as a support substrate only where the Stage4 numeric seam needs better provenance or sink visibility

Allowed work:

- subtype / provenance / fix-scope visibility needed to explain numeric carryover truth
- sink wiring that removes operator ambiguity for the active Stage4 patch

Not allowed today:

- broad repair-grammar normalization across every family
- general Stage4 architecture cleanup
- reopening Flashback or NpcDrift as if they were front blockers

Completion signal:

- the Stage4 patch does not depend on invisible or contradictory repair metadata

### Tranche D. Material Production

Goal:

- convert the new pitch philosophy from house-law text into one actual bounded production output

Read the philosophy literally:

- default mode is `single`
- one work-level pitch unit at a time
- do not promote multiple works into live canon on the same pass just because the batch is promising

Recommended execution:

1. select one immediate build candidate from `fresh_20260406_batch01`
2. tighten it against `pitch-philosophy.md` and `pitch-selection-checklist.md`
3. promote only that one candidate into the next stable material unit
4. leave the remaining candidates as ranked reserves, not parallel live canon

Current recommendation:

1. `01_line_stop_deputy.md` as the strongest immediate `blockguide` build
2. `03_manual_meridian_archivist.md` as the strongest reserve `wuxguide` build
3. `02_permit_window_grade9.md` stays viable, but below `line_stop_deputy` for today's single-slot production rule

Why this order:

- `line_stop_deputy` best matches the newly locked reward-token philosophy
- it has a crisp controllable resource and early reward vector
- it is likely the fastest path to a stable full canonical pitch file

Completion signal:

- one selected pitch is tightened enough to serve as the next real material anchor
- the other two remain intentionally unpromoted

## 5. Explicit Non-Goals For Today

Do not spend today's main budget on:

1. promoting parked `Stage2`, `Stage3`, or `cross-stage` waves
2. broad queue cleanup of every historical mirror if that blocks the real Stage4 tranche
3. reviving source-corpora cutover as the front material task
4. generating multiple new canon works in parallel
5. Phase0 or TR production before one selected pitch anchor is clean

## 6. Suggested Timebox

If the day needs a concrete bounded shape:

1. `60-90m`: queue hygiene and active-lane confirmation
2. `3-4h`: Stage4 numeric carryover owner-boundary tranche plus targeted validation
3. `90-150m`: one pitch selection and tightening pass under `20_pitch`
4. `30-60m`: closeout notes, reserve ranking, and next-day carryover

If only one heavy tranche can be completed today, prefer:

1. Stage4 stabilization first
2. one material production unit second

## 7. End-Of-Day Success Criteria

Call the day successful if all of the following are true:

1. the real active queue is clarified and no stale machine snapshot is silently steering work
2. Stage4 front debt is reduced at the numeric carryover owner-boundary, not broadened
3. Stage2/3 remain correctly parked
4. one material candidate is tightened under the new philosophy
5. the new material philosophy is treated as a reusable bridge contract, not only inspirational notes

## 8. 3-Pass Audit Record

### Pass 1. Structure and Scope

- kept this as a bounded daily roadmap, not a replacement for the active temp execution roadmap
- kept both system-track and material-side work, but only at today's actionable level
- excluded broad parked-wave realization and narrative pipeline promotion beyond one pitch unit

### Pass 2. Evidence and Consistency

- matched the front queue reading to `docs/temp/execution-roadmap.md` and the active Stage4 execution SSOTs
- explicitly recorded the `queue-state.json` staleness instead of treating it as authoritative
- aligned material production scope with the live dirty worktree and the new `single` pitch philosophy
- kept Stage2 as parked by the 2026-04-05 survey rather than promoting it from fresh evidence alone

### Pass 3. Execution and Readability

- reduced the day to four bounded tranches with explicit stop rules
- made the one-slot material production rule visible so the roadmap cannot overcommit
- kept the active Stage4 target narrow enough to execute without reopening parked waves

Confidence: `96%`
