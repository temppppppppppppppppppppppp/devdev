# ROL Live-Merge Current Context Note

Date: 2026-03-30
Status: draft-live-run-pending
Canonical Path: `docs/2026-03-30/rol-live-merge-current-context-note.md`
Temp Mirror Path: `(none during active live run)`
Baseline Commit: `9ad4efcc`
Baseline Dirty Summary: `dirty: Stage 3 validator/tests touched; live 0_1 Stage 3/4 artifacts and logs advancing; multiple 2026-03-30 docs untracked`
Source Docs:
- `docs/2026-03-30/rol-live-merge-global-survey-rolling-watchlist.md`
- `docs/2026-03-30/0_1-stage4-ep1-6-live-run-bounded-survey.md`
- `docs/2026-03-30/0_1-stage4-ep1-6-fix-execution-ssot.md`
- `docs/2026-03-30/rol-live-merge-global-survey-bounded-merge-audit.md`
- `docs/2026-03-30/rol-live-merge-global-survey-bounded-execution-ssot.md`

## 1. Purpose

This note is the compressed handoff context for the current `ROL live-merge` state.

Use it when:
- resuming work after context loss
- handing off to another operator or model
- deciding whether to realize a lane now or defer

Do not use it as a closure document.

## 2. Current Situation

- active mode: `live-merge`
- project with fresh live-run evidence: `projects/0_1`
- bounded live-run survey scope currently stabilized: `Stage 4 ep_0001` through `ep_0006`
- active run constraint still applies:
  - no `docs/temp/` mutation
  - no queue cleanup
  - no final closure claim

## 3. Authoritative Current Picture

### Live-confirmed
- `ep1-6` manuscripts are structurally clean
- no P0 blocker found in the bounded Stage 4 slice
- one live-confirmed P1 exists:
  - EP5 -> EP6 order amount contradiction
  - EP5 says `전액` / `전량`
  - EP6 executes `15억 + 4.71억`
  - bridging narration is absent

### Static high-risk
- consensus timeout can degrade into synthetic PASS
- Stage 4 strong advisories are not fully binding
- Stage 4 `authoritative_fix_scope` violations are warning-only

### Static medium
- Stage 3 lazy-init authority overlap
- Stage 2 / OneStop duplicated dispatch plus human-interactive failure path
- authoritative telemetry shared-cursor writes
- `episode_production.jsonl` schema/key drift
- desktop phantom settings and model/API-key truth drift

### Post-run only
- temp roadmap / queue sync closure

## 4. Manuscript Repair Authority

The Stage 4 EP1-6 repair lane has already been corrected to the proper authority contract:
- manuscript truth is DB `manuscripts`
- `drafts/ep_*.txt` is export mirror only
- repair order is:
  1. DB authoritative repair
  2. txt export sync
  3. DB/txt read-back verification

txt-only repair is forbidden.

## 5. Current Execution Priority

1. `confirmed-by-live-run`
   - Stage 4 EP5 -> EP6 manuscript amount-bridge repair
2. `static-high-risk`
   - Stage 4 binding + fix-scope contract hardening
3. `static-high-risk`
   - consensus-timeout synthetic PASS hardening
4. `static-medium`
   - sink contract normalization
5. `static-medium`
   - runtime authority/init seam hardening
6. `static-medium`
   - desktop operator-truth alignment
7. `post-run-only`
   - roadmap / queue closure sync

## 6. What Is Safe To Do Now

Safe now:
- bounded documentation
- bounded merge audit
- bounded execution planning
- read-only re-audit
- preparing a manual repair order for Lane 1

Not safe now:
- `docs/temp/` mirror generation/update
- queue cleanup
- post-run closure labels
- roadmap closure

Implementation timing rule:
- realization should wait for a safe edit window or run completion
- if fresh live-run evidence contradicts current priority, re-audit first

## 7. Immediate Operator Guidance

If continuing during the active run:
- preserve the run
- keep this context note and the bounded execution SSOT as the current planning authority
- if a repair must happen before post-run, Lane 1 is the first candidate

If resuming after the run:
- start from the bounded execution SSOT
- re-run 3-pass audit on the source docs
- realize lanes in order unless new live evidence forces reordering

## 8. Re-Audit Triggers

Re-audit is mandatory if any of the following happens:
- the active Stage 4 run produces a stronger P1/P0 than the current EP5 -> EP6 contradiction
- fresh evidence weakens or resolves the live-confirmed P1 without repair
- Stage 4 runtime shows concrete failure of the advisory/binding seam
- queue state changes enough to invalidate the current post-run closure plan

## 9. One-Line Summary

Current state: `bounded execution justified, but still draft-live-run-pending; one live-confirmed manuscript P1 exists, three static high-risk seams remain queued behind it, and queue/temp closure still waits for post-run.`

## 10. 3-Pass Audit Record

Pass 1 — Source fidelity:
- compressed only what is already established in the merge audit, bounded execution SSOT, and Stage 4 EP1-6 survey

Pass 2 — Scope discipline:
- kept live-confirmed, static-high-risk, static-medium, and post-run-only lanes separated

Pass 3 — Governance fit:
- preserved `draft-live-run-pending`
- no `docs/temp/` mutation
- no closure claim

Confidence: 96%
