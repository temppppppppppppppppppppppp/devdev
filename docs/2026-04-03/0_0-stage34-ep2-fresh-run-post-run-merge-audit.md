# 0_0 Stage34 ep2 Fresh Run Post-Run Merge Audit

Date: 2026-04-03
Status: final
Canonical Path: `docs/2026-04-03/0_0-stage34-ep2-fresh-run-post-run-merge-audit.md`
Source Docs:
- `docs/2026-04-03/0_0-stage34-ep2-fresh-run-watchlist-draft-live-run-pending.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-03/0_0-stage4-ep2-continuity-handoff-context.md`
Evidence Artifacts:
- `docs/2026-04-03/0_0-stage34-ep2-fresh-run-post-run-merge-evidence.json`
Commit State:
- Baseline Commit: `c011e7efdfee309a5b6d8dde443e6d40f6749328`
- Baseline Dirty Summary: `dirty: provider-toggle/runtime code+tests, Stage4 queue docs and temp mirrors, runtime project logs/db/artifacts, planning/operating drafts, and fresh-run watchlist doc active`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `fresh full run in projects/00_20260403 completed after the watchlist was created; live evidence now available for post-run merge interpretation`
Confidence: `96%`

## 1. Intent

Merge the completed `projects/00_20260403` fresh-run evidence with the active Stage4 surveys so the workspace can answer three bounded questions:

- did Stage4 actually get `ep2` through a real PASS path
- did the opening-authority / replay-suppression seam close cleanly enough to declare the child lane resolved
- what execution scope survives after fresh live evidence outranks stale canary-only inference

## 2. Scope

Included:

- `projects/00_20260403` completed fresh run through Stage4 target `ep2`
- `runtime_audit_summary.json`
- `session_20260403_124523.log`
- `episode_production.jsonl`
- sqlite checks on `project_data.db` for `stage_attempts` and `director_selections`
- `blueprint_0002.txt`
- Stage4 ep1/ep2 selected, patched, and final manuscript text artifacts
- read-only `build_stage4_canary_summary()` interpretation over the completed run

Excluded:

- new code patching
- Stage2/3 redesign
- global Stage4 closure declaration
- DB schema redesign
- queue cleanup beyond what the merged audit can safely justify

## 3. Pass 1. Inventory

### 3.1 Terminal fresh-run facts

The run reached a real terminal state.

- `projects/00_20260403/logs/runtime_audit_summary.json` closed as `shutdown_final`
- the latest event type is `stage4_complete`
- the event counts include `target_ep_reached = 1` and `stage4_complete = 1`
- the session log shows `ep2` generation complete, Stage4 session end, metrics/pass-rate persistence, DB commit, and system shutdown

The terminal-state markers matter because they beat the earlier bounded canary speculation that `ep2` remained trapped in an unresolved Stage4 fail loop.

### 3.2 Stage4 ep2 verdict persistence split

The run persisted a real bounded correction path for `ep2`.

- `director_selections` stores `ep2` Stage4 as `PASS_WITH_FIX`, score `91`, attempt key `s4:ep2:arc1:a1:20260403_124527`, artifact `selected_before_fix__A.txt`
- `episode_production.jsonl` stores the same attempt key with `final_verdict = PASS`, `final_score = 90`, and final artifact `patched_after_fix__A_InPlace.txt`
- `repair_scope`, `fix_scope`, and `authoritative_fix_scope` are all `inplace`
- the repair-contract provenance on the final persisted row is `director_authored`

This proves the live path was not just “Director liked it.” It was:

`PASS_WITH_FIX -> bounded in-place patch -> final PASS`

### 3.3 Stage4 final-authority sink gap still survives

The run did not land a complete Stage4 final row into every authoritative consumer sink.

- sqlite `stage_attempts` contains Stage2 and Stage3 rows for this session, but no Stage4 rows
- the read-only Stage4 canary helper therefore reports:
  - `hard_gates.status = fail`
  - `final_authority_contract_summary.status = missing`
  - `gate_repair_surface_summary.status = missing`
- the helper failure is driven by sink coverage and final-authority resolution, not by absence of final Stage4 artifacts

### 3.4 Opening text comparison

The opening consumed the blueprint’s direct-continuation setup more faithfully than the older failed picture implied.

- `blueprint_0002.txt` scene 1 stays in the family dining-room confrontation lane
- the final ep2 manuscript opens in that same confrontation lane rather than silently jumping to a different room/time band
- no new evidence supports a same-location hard lock theory; the current contract still reads as declared-transition / replay suppression, not absolute place sameness

But the opening is not cleanly normalized yet.

- the session log emits `cross-episode repetition 3건`
- the final ep2 draft and both Stage4 ep2 artifacts still contain exact phrases that already appear in the ep1 Stage4 manuscript
- this is a residual replay/repetition quality problem, even though the run still reaches PASS

## 4. Pass 2. Merged Findings

### 4.1 Strong positive runtime proof now exists

The highest-authority result changed.

Before this run, the active narrative around `ep2` was still “Stage4 cannot converge cleanly enough to finish.”

After this run, the stronger statement is:

- Stage4 can get `ep2` through a bounded correction path
- the correction can stay local (`inplace`) rather than collapsing into rewrite-class failure
- the final persisted content artifact exists and the production run reaches terminal completion

So the “ep2 can never pass Stage4” interpretation is no longer defensible.

### 4.2 The opening-authority seam improved, but did not fully close

The run does not support a clean closure claim for the flashback / replay child lane.

What improved:

- no new undeclared spatial/time jump was reproduced in the inspected ep2 opening
- Stage4 followed the direct continuation shape in the blueprint instead of inventing a new opening mode

What remains:

- exact ep1 phrases survive into the ep2 opening
- the runtime itself logged `cross-episode repetition 3건`
- a separate CoVe runtime advisory also survived, though it did not overturn the Director’s PASS path

Therefore this lane is no longer an absolute pass blocker, but it is still a real residual quality seam.

### 4.3 The surviving live blocker is narrower and more operational

The strongest surviving execution debt is now on the consumer/finalization side:

- Stage4 final authority is not fully materialized into `stage_attempts`
- the canary helper cannot build a complete `gate_repair_surface_summary` for the finished ep2 path
- `runtime_audit_summary` ends as `shutdown_final`, which is correct for a full production run, but still fails a narrower canary hard-gate expectation

This is a sink/finalization contract problem, not evidence that the ep2 content path failed.

## 5. Pass 3. Execution Consequence

Keep:

- the aggregate `0_0-stage4-consumer-contract-normalization-remediation` lane active
- the flashback continuity local-fix lane as `partially_realized`
- this fresh run as the highest-authority positive proof that `ep2` can pass Stage4

Narrow and shift:

- stop treating the flashback continuity child lane as “runtime proof still absent”
- do not declare it resolved, because replay/repetition warning evidence still survived the PASS path
- promote final-authority / final-sink normalization as the next bounded consumer-side subtask

Do not do next:

- do not reopen Stage3 opening-transition normalization now
- do not generalize this into a same-location opening lock
- do not declare global Stage4 closure from this run alone

## 6. Final Conclusion

The merged post-run result is stable:

- `ep2` now has real fresh-run Stage4 PASS proof
- the PASS path is bounded and local, not rewrite-only
- the opening-authority seam improved enough to stop being an absolute blocker
- but replay/repetition suppression is still not cleanly normalized
- and the stronger remaining debt is now final-authority / sink coverage in Stage4 consumer finalization

That means the next step is not “more upstream redesign.” It is:

- record this run as positive runtime proof
- update the active Stage4 execution docs to replace `runtime proof pending` with `runtime proof captured but residual warning remains`
- then execute the next bounded Stage4 final-sink / final-authority normalization pass
