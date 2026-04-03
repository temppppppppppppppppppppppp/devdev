# 0_0 Stage34 ep2 Fresh-Run Watchlist

Date: 2026-04-03
Status: draft-live-run-pending
Canonical Path: `docs/2026-04-03/0_0-stage34-ep2-fresh-run-watchlist-draft-live-run-pending.md`
Temp Mirror Path: none by design
Applies To:
- bounded `ep2` fresh run / canary review while live evidence is still being generated

## 1. Purpose

Keep one operator-facing watchlist ready for the current `ep2` fresh run so post-run interpretation can start immediately without reopening the full Stage4 context stack.

This document is intentionally not a closure audit, not a final SSOT, and not a queue-control artifact.

## 2. Governing References

- `docs/implementation/live-run-merge-survey-harness.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-03/0_0-stage4-ep2-continuity-handoff-context.md`
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`

## 3. Guardrails

- Do not use this document to declare Stage4 closure while the run is still active.
- Do not save final findings from mid-run DB or log state alone.
- Do not convert the current `ep2` opening seam into a global same-location hard lock.
- Read declared transition / replay suppression as the active contract, not same-place sameness.

## 4. First Artifacts To Inspect After The Run

Expected Stage34 demo summary sink:

- `projects/<target-project>/logs/stage34_ep_demo_canary_summary.json`

Expected Stage4 summary sink when a Stage4-only canary helper is used:

- `projects/<target-project>/logs/canary_summary.json`
- `projects/<target-project>/logs/canary_companion_audit.json`

Primary supporting artifacts:

- `projects/<target-project>/logs/runtime_audit_summary.json`
- `projects/<target-project>/project_data.db`
- `projects/<target-project>/logs/artifacts/stage4/...`
- `projects/<target-project>/logs/canary_prep.json`

## 5. Immediate Post-Run Questions

### Q1. Did Stage4 stop replaying already-completed prior-episode action?

Check:

- opening no longer replays a completed prior-episode beat as if it is happening again
- flashback/replay contradiction no longer survives into the selected manuscript opening

Primary evidence:

- blueprint `scene_1` fields versus selected Stage4 manuscript opening
- Stage4 attempt artifact text
- Stage4 rejection/advisory summary if present

### Q2. Did Stage4 preserve allowed transition openings without false reject?

Check:

- changed place/time opening is still allowed when the opening explicitly declares the transition
- alternate opening remains acceptable when the changed state is named quickly and clearly

Reject only if:

- new place/time/action jump happens without a transition signal
- the opening silently replays a completed prior-episode event

### Q3. Did the repair contract surface cleanly into operator-visible sinks?

Check these fields when present:

- `gate_repair_surface_summary.status`
- `repair_contract_subtype`
- `repair_contract_provenance`
- `fix_scope`
- `authoritative_fix_scope`
- `scope_origin`
- `widened`
- `mismatch_counts`

Desired shape:

- structured repair metadata is visible without inferring it from prose logs
- `authoritative_fix_scope` is not silently lost when runtime scope widens
- `mismatch_counts` stays zero or at least does not spike on the active session

### Q4. Did the run remain closure-eligible at the summary-contract level?

Check:

- `hard_gates.status`
- `rationale_contract_summary.status`
- `companion_audit_summary.status`
- `proof_scope_summary`

If these are red for unrelated sink/rationale reasons, do not over-attribute the failure to opening continuity.

## 6. Target Comparison Slice

If the run still fails, compare in this order:

1. pre-patch blueprint
2. post-V75-D blueprint
3. selected Stage4 manuscript opening

Minimum fields to compare:

- `scene_1.location`
- `scene_1.summary`
- `scene_1.key_events`
- opening paragraph 1-2 of the selected manuscript
- explicit transition sentence or scene-break marker presence

## 7. Interpretation Rules

### Positive signal

- round count drops or convergence improves
- replay contradiction is suppressed
- declared transition openings remain allowed

Interpretation:

- opening-authority alignment is landing in Stage4 consumption
- continue bounded Stage4 correction-quality tuning

### Negative signal

- replay/flashback contradiction still reappears after V75-D
- changed opening state is ignored even when transition is explicit
- repair contract fields exist internally but disappear from operator-visible sinks

Interpretation:

- first inspect `patched blueprint scene_1 semantics -> manuscript opening consumption`
- only escalate to the parked repair-contract normalization lane if the runtime result exposes shared naming / provenance / sink visibility drift rather than a pure opening-consumption failure

## 8. Why The Parked Repair-Contract Lane Still Matters

`0_0-stage4-repair-contract-normalization-remediation` is not the current blocker-closing lane.

Use it only if the fresh run shows:

- subtype naming drift across Stage4 families
- operator sink blackout for structured repair metadata
- hidden widening from authoritative to runtime-derived scope

Do not reopen that parked lane just because the run fails on opening continuity alone.

## 9. Promotion Rule

After the run reaches a terminal state:

1. merge this watchlist with actual run evidence
2. perform the normal 3-pass audit
3. only then promote conclusions into a canonical audit or closure document
