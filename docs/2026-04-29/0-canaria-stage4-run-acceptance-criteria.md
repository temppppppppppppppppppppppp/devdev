# 0 Canary Stage4 Run Acceptance Criteria

Date: 2026-04-29
Status: final - post-run acceptance checklist
Track: system
Project: `projects/0_카나리아`
Scope: Stage4 manuscript run through target episode 15
Canonical Path: `docs/2026-04-29/0-canaria-stage4-run-acceptance-criteria.md`
Runtime Guard: do not touch or restart the active run while applying this checklist.

## 1. Purpose

Define a realistic pass/fail bar for the current Stage4 live production run.

This run is accepted if it proves the system can produce usable first-draft manuscripts through episode 15 without fatal runtime collapse, unrecoverable artifact loss, or severe narrative/state corruption. It does not need to prove final publication quality.

## 2. Verdict Levels

### PASS

Use `PASS` if all are true:

- Episodes 1-15 manuscript files exist.
- Stage4 reaches the requested target without fatal process death or unrecovered terminal failure.
- Final manuscript artifacts and `drafts/ep_XXXX.txt` agree for completed episodes.
- Core financial/state continuity is readable and not catastrophically wrong.
- ep13/ep14 watchlist items do not break downstream manuscript logic.
- Prose is at least editable first-draft quality, not discard-only output.

### CONDITIONAL PASS

Use `CONDITIONAL PASS` if the run reaches episode 15 and remains usable, but has P2 issues requiring cleanup:

- awkward location transitions
- minor item/reference omissions
- repeated phrasing or style drift
- local scene compression
- advisory warnings that Director accepted
- isolated `PASS_WITH_FIX` or retry churn that recovered

The run can still count as a system proof if fixes are ordinary editorial or bounded bugfix follow-up.

### FAIL

Use `FAIL` if any P0/P1 blocker appears and remains unresolved at run end.

## 3. P0/P1 Blockers

### P0 - hard fail

- Missing final manuscript for any requested completed episode.
- Duplicate or out-of-order episode overwrite that makes artifact truth ambiguous.
- DB/file corruption or invalid UTF-8 in touched manuscript/artifact outputs.
- Unrecoverable active process death before target episode completion.
- Silent data loss in `drafts/`, Stage4 artifacts, or episode production logs.

### P1 - fail unless bounded repair is obvious

- Core asset/capital/position continuity collapses.
- Episode order or causal order is broken in a way readers cannot follow.
- A dead or nonexistent character acts/speaks in current time.
- Wrong project/genre/material leaks into the manuscript.
- Stage4 accepts a manuscript that contradicts hard Stage3 blueprint carryover on a central fact.
- Repeated retry loop exhausts attempts for a target episode.
- ep13/ep14 watchlist breaks the gold/WTI/Exception Account/subprime chain in final manuscript.

## 4. P2 Watchlist

These do not fail the run by themselves:

- location bridge is clunky but understandable
- a carried item is omitted once but not contradicted
- `PASS_WITH_FIX` patch succeeds
- CoVe parse/advisory error occurs while Director PASS is preserved
- blueprint coverage metric is low but Director and final validation pass
- style warnings such as dialogue ratio, ai-slop hits, or CED drift remain advisory
- local post-select conflict occurs and recovers in the next round

P2 items should be listed after the run, not used to stop the live production proof.

## 5. Required Post-Run Checks

### Artifact Truth

Check:

- `projects/0_카나리아/drafts/ep_0001.txt` through `ep_0015.txt`
- `projects/0_카나리아/logs/artifacts/stage4/ep_0001` through `ep_0015`
- `projects/0_카나리아/logs/episode_production.jsonl`
- `projects/0_카나리아/logs/quality_metrics.jsonl`

Minimum expectations:

- every completed episode has a final manuscript artifact
- every completed episode has a draft file
- production log final verdict is `PASS` or recovered `PASS_WITH_FIX -> PASS`

### Metadata Truth

Check:

- `director_selections` stage 4 rows
- `stage_attempts` stage 4 rows
- episode production records
- settlement files

Minimum expectations:

- no unresolved terminal reject for episodes 1-15
- selected candidate path points to existing artifact
- patch/retry records explain recovered failures

### Narrative Truth

Read enough of the actual manuscripts to verify:

- episode starts and endings connect in order
- major financial moves are understandable
- capital/position changes are not nonsensical
- major NPC roles remain stable
- no physical-action genre drift dominates the investment plot

## 6. Special Watchlist

### ep13

Check:

- `베테랑 PB` does not become a new person separate from 박성호.
- `절반 청산된 WTI 원유 선물 거래 내역서` or an equivalent clear WTI liquidation record survives.
- The transition from WTI profit proof to next gold-market setup is understandable.

### ep14

Check:

- Hanmi VIP room to SW Investment office movement is explicit enough.
- Exception Account approval remains tied to the gold futures move.
- Gold long entry is framed as investment/business pressure, not physical action.
- Subprime/safe-asset setup remains legible.

### Genre Contract Gap

Because issue #120 confirms the Stage3 genre strategy contract did not attach in this run, verify selected action-heavy manuscripts by content rather than metadata:

- no combat/chase/intruder/vehicle-attack default dominates
- action/tension reads as market, institutional, liquidity, reputation, or legal pressure

## 7. Minimum Quality Floor

The run passes the quality floor if:

- manuscript is readable without needing complete regeneration
- each episode has a clear beginning, middle, and ending hook
- the target beat is recognizable
- prose may be rough but is editable
- errors are local enough for post-edit or bounded follow-up fixes

The run fails the quality floor if:

- output is mostly summary instead of scenes
- episode logic cannot be reconstructed
- financial premise becomes incoherent
- repeated generic prose makes the episode unusable as a draft

## 8. Recommended Closure Summary

After the run completes, report:

- target reached: yes/no
- completed episodes count
- failed episodes count
- retry-heavy episodes
- P0/P1 blockers
- P2 watchlist items
- ep13/ep14 watchlist verdict
- overall verdict: `PASS`, `CONDITIONAL PASS`, or `FAIL`

## 9. Document 3-Pass Audit

Pass 1 - Structure and scope:
- PASS. This is an acceptance checklist, not an execution SSOT.
- It defines verdict levels, blockers, watchlists, and post-run checks.
- It does not instruct operators to interfere with the active run.

Pass 2 - Evidence and consistency:
- PASS. Criteria reflect the observed current run shape: recovered PWF/retry events, active Stage4 manuscript artifacts, and the known issue #120 genre-contract gap.
- It separates fatal artifact/state failures from ordinary P2 quality/editing issues.
- It preserves Director authority and treats Python metrics as advisory unless they imply artifact/state failure.

Pass 3 - Execution and readability:
- PASS. The checklist is actionable after the run completes.
- It sets a realistic first-draft proof bar rather than publication-quality requirements.
- Estimated confidence: 96%.

