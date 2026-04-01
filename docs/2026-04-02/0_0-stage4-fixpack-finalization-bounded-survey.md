# 0_0 Stage4 FixPack Finalization Bounded Survey

Date: 2026-04-02
Status: final
Confidence: 96%
Scope: `canary_0_0_stage34_arc2_entitypost_r1` post-run bounded survey on the next dominant Stage4 seam: `strong_advisory` local-fix contract generation plus `post_select_conflict` finalization continuity handling
Evidence Path: `docs/2026-04-02/0_0-stage4-fixpack-finalization-evidence.json`
Related Docs:
- `docs/2026-04-02/0_0-stage4-canonical-entity-postselect-runtime-closure-audit.md`
- `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-remediation-execution-ssot.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`

## 1. Answer First

The next dominant blocker is no longer Stage2/3 hierarchy and no longer the original Flashback false-positive loop.

It is now a Stage4 **finalization contract** seam with two coupled branches:

1. `ep3`: runtime `strong_advisory_escalation` converts Director `PASS` into `REJECT`, but the result has no actionable local `fix_pack.patch_targets`, so the round loops through `strong_advisory_escalation_non_local_fix`.
2. `ep4`: Director reaches `PASS_WITH_FIX`, but post-select continuity/history downgrade converts the round to `REJECT` and the reject snapshot blanks the `fix_pack`, so the runtime later sees `fix_pack:missing_fix_pack` even when earlier fix targets existed.

Bounded verdict: **the next wave should target Stage4 fix-pack target synthesis/preservation and post-select continuity finalization, not reopen Stage2/3 normalization**.

## 2. Hard Conclusions

### 2.1 ep3 is a runtime-created PASS_WITH_FIX contract gap

`episode_production.jsonl` shows `ep3 round 0-3` all follow the same pattern:

- `director_verdict = PASS`
- `final_verdict = REJECT`
- `gate_basis = strong_advisory_escalation_non_local_fix`
- `authoritative_fix_scope = inplace`
- `fix_pack.target_kind` exists
- but `fix_pack.patch_targets = []` and `must_fix = []`

This is not a Director-authored `PASS_WITH_FIX` contract. It is a runtime escalation after Director selection.

### 2.2 Director prompt contract currently protects PASS_WITH_FIX, not runtime-escalated PASS

`config/prompts/director.yaml` explicitly requires structured `fix_pack` for:

- `PASS_WITH_FIX`
- `REJECT` with local scopes

But `ep3` starts as raw Director `PASS`. The runtime later adds `PASS_WITH_FIX/REJECT` semantics because of strong advisory classes.

So the missing `fix_pack.patch_targets` on `ep3` is structurally expected under the current contract split.

### 2.3 The runtime gate is behaving as designed, but the design now exposes the next seam

`stage4_interview_round._normalize_director_gate_semantics()` does the following:

- detect strong advisory classes
- escalate `PASS -> PASS_WITH_FIX`
- require a ready local fix contract for advisory-driven `PASS_WITH_FIX`
- fail closed to `REJECT` if `patch_targets` or other fix-pack fields are missing

This logic is internally coherent. The problem is that there is no bounded runtime backfill when the advisory escalation is the first moment a local fix contract becomes necessary.

### 2.4 ep4 preserves fix targets at the Director layer, then loses them in reject snapshotting

`episode_production.jsonl` shows:

- `ep4 round 0`: local proper-noun entity patch targets exist
- `ep4 round 1`: `PASS_WITH_FIX(92)` also carries explicit timeline/document-anchor patch targets

But `runtime_audit.jsonl` still records:

- `post_select_conflict|...|fix_pack:missing_fix_pack`

The code explains why:

- `stage4_reject_runtime._build_reject_retry_snapshot()` blanks `snapshot_fix_pack = {}`
- this happens when `reject_bucket == post_select_conflict` and `resolved_fix_scope == full`

So the runtime is intentionally discarding structured fix targets in conflict-first retry snapshots.

### 2.5 The current blocker is not "wrong entity truth" but "how Stage4 carries repair contracts across gates"

The earlier canonical-entity/post-select lane improved `ep2` materially and moved the canary into `ep3`/`ep4`.

The current residual failures are about:

- synthesizing a local fix contract when strong advisory escalation creates one too late
- preserving or intentionally classifying local-vs-rewrite continuity repairs when post-select conflict downgrades a provisional pass

## 3. Medium-Confidence Conclusions

### 3.1 ep3 likely needs runtime fix-pack backfill, not another Director prompt expansion

Because the raw Director verdict is `PASS`, widening the Director prompt alone may not reliably fix this seam. The more bounded fix is runtime-side:

- if advisory escalation creates the first repair obligation
- and a partial `fix_pack` already exists
- complete or backfill the missing local fix contract from runtime evidence

Confidence: 84%

### 3.2 ep4 likely needs selective fix-pack preservation, not blanket retention

The current snapshot intentionally blanks fix-pack for `post_select_conflict/full` rewrites. That behavior should not be removed wholesale.

The likely correct bounded change is:

- preserve structured local repair hints only when the conflict is specific and bounded
- keep full rewrite behavior for broad continuity collapse

Confidence: 79%

## 4. Open Questions

1. What is the safest bounded source for `ep3` fix-pack backfill:
   - candidate warnings
   - runtime advisory payload
   - contradiction details
   - action items
2. Should `ep4` preserve the original Director fix-pack in `previous_attempt`, or store a separate `post_select_fix_pack` alongside the rewrite contract?
3. Is `repair_scope=full` too coarse for the current `ep4` proper-noun/timeline cases?

## 5. Operating Consequence

- keep `Stage4` paused
- open a new bounded execution lane for:
  1. runtime fix-pack backfill under strong advisory escalation
  2. selective fix-pack preservation/classification for post-select conflict retries
- do not reopen Stage2/3 hierarchy work
