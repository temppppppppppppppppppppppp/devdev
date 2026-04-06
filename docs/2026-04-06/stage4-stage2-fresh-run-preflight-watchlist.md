# Stage4-Stage2 Fresh Run Preflight Watchlist

Date: 2026-04-06
Status: draft-live-run-pending
Canonical Path: `docs/2026-04-06/stage4-stage2-fresh-run-preflight-watchlist.md`
Applies To: next fresh system run paired with post-run merge audit
Commit State:
- Baseline Commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`
- Baseline Dirty Summary: `dirty workspace; active Stage4/Stage2 code-test-doc edits plus unrelated narrative/material/work-guard changes are present, so this watchlist is run-scoped evidence scaffolding rather than a closure note`
Authority Note:
- this is a pre-run watchlist, not a final conclusion
- do not convert this document into queue closure or resolved claims before the run reaches a terminal state
- do not create new `docs/temp/` execution artifacts from this watchlist during the run

## 1. Purpose

Capture the exact residual risk surfaces that are still worth checking in the next fresh run now that:

- the bounded Stage4 static/readback fixes have landed
- the bounded Stage2 persistence-authority fix has landed
- no additional confirmed parked P0-P1 remains outside the current active queue

## 2. Run Focus

Primary watch items:

1. `Stage4 consumer`
   - confirm whether valid on-page numeric change is promoted cleanly enough into the next carryover baseline
   - watch for retry/advisory pressure that still comes from numeric carryover owner-boundary split rather than real story error
2. `Stage4 repair`
   - confirm whether repair/readback metadata absence still inflates phantom mismatch summaries
   - watch for `repair_scope`, `gate_basis`, `scope_authority*`, or related readback fields being missing or over-reported
3. `Stage2 persistence-authority`
   - confirm that saved arc truth preserves LLM-authored `joint_docs.world_joint` and `status_shadow` instead of falling back to stale `enriched_block` values

Out of scope for this run watchlist:

- broad Stage3 future-wave debt
- broad cross-stage vocabulary cleanup
- Stage0 future-wave normalization
- new final queue closure claims before the run finishes

## 3. Watch Items

### W1. Stage4 Numeric Carryover Promotion

Current expectation:

- Stage4 may still be the front owner for `numeric asset authority / carryover owner-boundary`
- the recent static patches should reduce false retry pressure, not yet guarantee full closure

Watch for:

- contradiction-firewall or numeric-consistency warnings on a manuscript that legitimately changed numbers on-page
- carryover packet / next-episode numeric baseline still reflecting stale pre-change values
- repeated advisory escalation where the underlying manuscript number is already correct

Minimum evidence to capture:

- operator console lines around Stage4 numeric advisory or retry pressure
- authoritative Stage4 attempt row / summary that shows the reported mismatch family
- next-episode carryover-facing packet or equivalent readback showing whether the promoted baseline changed

Run consequence:

- if clean: keep `Stage4 consumer` narrowed and move toward closure criteria
- if noisy but bounded: keep this as the front Stage4 consumer lane
- if regressed hard: reopen the numeric promotion path before any broader queue move

### W2. Stage4 Repair Readback Phantom Mismatch

Current expectation:

- static fixes reduced root-vs-nested scope metadata loss
- the lane is still open because repair metadata may not yet read back as first-class truth across every sink

Watch for:

- mismatch summaries that mention `repair_scope`, `gate_basis`, `repair_contract_subtype`, or `scope_authority*` without a real verdict disagreement
- summary/readback surfaces looking worse than the authoritative stored attempt/gate state

Minimum evidence to capture:

- operator-facing summary or mismatch list
- matching authoritative DB/readback snapshot for the same attempt
- any sink disagreement between stored repair metadata and rendered summary text

Run consequence:

- if phantom mismatch volume is near-zero: keep the lane as closure-tail only
- if still present but bounded: keep `Stage4 repair` as the next queued substrate
- if it masks true operator understanding: re-enter bounded repair/readback normalization immediately after the run

### W3. Stage2 `world_joint` / `status_shadow` Persistence

Current expectation:

- validation/finalizer now merge `enriched_block` as fallback instead of whole-object overwrite
- explicit location/inventory authority syncs may still rewrite their own fields, but `world_joint` and non-overwritten `status_shadow` fields should survive

Watch for:

- saved arc artifact or stored arc payload showing `world_joint` replaced by stale/empty block truth
- `status_shadow.item_consumption`, `expected_injuries`, or `key_stat_change` reverting to block fallback despite richer refined-arc truth
- downstream carryover reading consumed items as if they were never consumed

Minimum evidence to capture:

- final saved arc payload
- corresponding pre-persistence refined-arc or run log context when available
- any exported artifact text that mirrors the saved carryover/state packet

Run consequence:

- if preserved: Stage2 current tranche becomes a closure candidate
- if partially preserved: keep Stage2 at rank 3 and narrow to the specific field family that still leaks
- if regressed: reopen Stage2 sink merge work before touching parked Stage3/Stage0 waves

## 4. Evidence Capture Checklist

- terminal transcript around Stage2/Stage4 warnings, retries, and PASS transitions
- authoritative DB snapshots or bounded row extracts for the same run window
- saved Stage2 arc artifact/body when the watch item is Stage2 persistence
- saved Stage4 attempt/readback summary when the watch item is Stage4 numeric or repair mismatch
- exact project/run id and terminal state: `completed`, `failed`, `stopped`, or `aborted by operator`

## 5. Post-Run Decision Map

1. If `W1`, `W2`, and `W3` are all clean:
   - treat the run as closure evidence candidate for the current bounded tranches
   - do a post-run merge audit before changing queue state
2. If only `W1` remains live:
   - keep `Stage4 consumer` front
   - keep `Stage4 repair` and `Stage2` behind it
3. If only `W2` remains live:
   - keep `Stage4 repair` as the next patch lane
   - do not reopen parked Stage3/Stage0 work
4. If only `W3` remains live:
   - keep Stage2 at active rank 3
   - do not widen into broad Stage2 normalization yet
5. If multiple items regress together:
   - stop closure claims
   - produce a post-run merge audit first

## 6. 3-Pass Audit Record

Pass 1, structure and scope:

- kept this document as a pre-run watchlist rather than a survey conclusion or execution SSOT
- limited scope to the three active residual watch items only

Pass 2, evidence and consistency:

- aligned watch items with the current queue order and active execution SSOTs
- kept parked Stage3 / cross-stage / Stage0 debt out of the live watchlist because no confirmed parked P0-P1 remains

Pass 3, execution and readability:

- made each watch item actionable with expected signal, evidence capture, and run consequence
- made the post-run branching explicit so the next audit can start from this document without reinterpretation

Confidence: `97%`
