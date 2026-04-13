# Polaris Cross-Stage Grounding Parallel Survey

- Date: 2026-04-13
- Status: draft-live-run-pending
- Scope: parallel static survey that grounds the cross-stage `Polaris` anchor in current Stage0, Stage2, Stage4, control-plane, and queue-contract surfaces on current `main`
- Mode: live-merge support note; this survey strengthens future-state confidence without claiming that the active live run is already closed
- Canonical Path: `docs/2026-04-13/polaris-cross-stage-grounding-parallel-survey.md`
- Baseline Commit: `347acac374f7246cca433d4be9c7466e802c9883`
- Baseline Dirty Summary: `dirty: active live-run artifacts plus current Stage3 runtime/tests/docs patches already present in worktree`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none at survey capture; live-run evidence is still moving and post-run merge remains mandatory before queue mutation`
- Confidence: `96% for the grounding survey itself; not a claim about current runtime closure`

## Purpose

This survey answers one bounded question:

Is `Polaris` a credible long-horizon anchor on the current repo, or is it still too abstract to guide post-run work?

Current answer:

- credible enough to use as a future-state anchor now
- not yet ready to mutate the active queue mid-run
- already grounded in real code boundaries rather than wishful greenfield architecture

Parent anchor:

- [stage0-stage2-stage3-stage4-cross-stage-north-star-operating-note.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/stage0-stage2-stage3-stage4-cross-stage-north-star-operating-note.md:1)

Companion queue watchlist:

- [polaris-queue-compaction-live-run-watchlist.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-04-13/polaris-queue-compaction-live-run-watchlist.md:1)

## Live-Run Lock

The current live run is still active, so this survey does not authorize:

- `docs/temp/` mirror cleanup
- `docs/temp/queue-state.json` mutation
- ClickUp sync
- final closure claims

This note is evidence and design grounding only until post-run merge.

## Evidence Anchors

- Stage0 handoff contract surface:
  - [stage0_handoff.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0_handoff.py:10)
- Stage2 carryover and persistence surfaces:
  - [arc_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/arc_ensemble.py:57)
  - [stage2_finalizer.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage2_finalizer.py:3563)
- Stage4 settlement and proof surfaces:
  - [stage4_post_processor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_post_processor.py:154)
  - [stage4_canary_tools.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_canary_tools.py:560)
  - [stage4_raw_evidence.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_raw_evidence.py:110)
- Control-plane authority split:
  - [control_plane_contract.py](/c:/Users/wjjo/Desktop/글도비/modules/api/control_plane_contract.py:41)
  - [bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py:1591)
- Queue contract and ClickUp mirror boundaries:
  - [temp-queue-state-contract-v1.json](/c:/Users/wjjo/Desktop/글도비/docs/implementation/temp-queue-state-contract-v1.json:3)
  - [queue-state.json](/c:/Users/wjjo/Desktop/글도비/docs/temp/queue-state.json:1)
  - [sync_clickup_queue.py](/c:/Users/wjjo/Desktop/글도비/scripts/sync_clickup_queue.py:35)

## Pass 1. Code-Surface Grounding

### Stage0 already behaves like packaging authority

`Stage0` is not hypothetical in current code. The shared handoff layer already declares:

- a stable Stage0 contract key and schema: [stage0_handoff.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0_handoff.py:11)
- artifact role split between treatment truth and BI projection: [stage0_handoff.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0_handoff.py:14)
- explicit runtime handoff ownership and projection source: [stage0_handoff.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0_handoff.py:83)
- `_stage0_contract`, `opening_bundle_contract`, and `planning_seed_authority` already act as concrete Stage0 packet/provenance surfaces rather than as vague future placeholders: [stage0_handoff.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0_handoff.py:351), [stage0_opening_contract.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0_opening_contract.py:223), [stage0_phase0_seed.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage0_phase0_seed.py:307)

That means Polaris does not need to invent Stage0 packaging from scratch. It mainly needs to normalize vocabulary and finish the handoff packet story.

### Stage2 already behaves like producer truth and carryover persistence

Current Stage2 surfaces already show producer-truth behavior:

- carryover authority is extracted and rendered as a structured packet, not just freeform prompt residue: [arc_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/arc_ensemble.py:57), [arc_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/arc_ensemble.py:108)
- candidate continuity checks explicitly compare Stage2 start state against the carryover packet: [arc_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/arc_ensemble.py:1821)
- the prompt surface pushes the carryover packet to the top as binding authority: [arc_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/arc_ensemble.py:2025)
- finalized Stage2 PASS attempts persist stage attempts, director selections, and artifact hashes: [stage2_finalizer.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage2_finalizer.py:3563)
- the live proof stack already treats Stage2 as both persistence truth and proof/readback source rather than as generator-only residue: [audit_service.py](/c:/Users/wjjo/Desktop/글도비/modules/core/services/audit_service.py:428), [stagewise_manuscript_truth_report.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stagewise_manuscript_truth_report.py:272)

This is already much closer to `producer truth + contract persistence` than to a loose generator-only stage.

Important guardrail:

- Polaris should still avoid overclaiming full structure here, because major mission truth and some carryover semantics still remain partly prose- or prompt-borne rather than fully normalized contract fields.

### Stage4 already behaves like settlement, readback, and proof projection

Current Stage4 also has real Polaris-shaped surfaces:

- Stage4 settlement packets already carry `stage3_meta`, quality signals, `actual_truth`, `final_state_updates`, and `state_truth_owner_contract`: [stage4_post_processor.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_post_processor.py:170)
- Stage4 canary tools already merge sink alignment, repair surfaces, proof scope, and proof record summaries for operator proof use: [stage4_canary_tools.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_canary_tools.py:560)
- Stage4 raw evidence already projects selection, feedback provenance, patch trace, retry pathology, and contract snapshots into readback-friendly forms: [stage4_raw_evidence.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_raw_evidence.py:158), [stage4_raw_evidence.py](/c:/Users/wjjo/Desktop/글도비/modules/core/stage4_raw_evidence.py:255)

So Polaris does not need to create a proof layer from nothing. It mainly needs to stop authority confusion between durable sinks and operator projections.

Important guardrail:

- Polaris should not overstate Stage4 as a fully hard structural verifier today. Current Stage4 is already strong at settlement, provenance, and operator projection, but pre-Director checks remain advisory-heavy and some repair-contract semantics are still synthesized reactively.

## Pass 2. Projection vs Authority Split

### Durable authority already exists

The current control-plane contract already distinguishes authority from companion snapshots:

- authoritative sinks include `control_plane_provenance`, project DB, and episode production log: [control_plane_contract.py](/c:/Users/wjjo/Desktop/글도비/modules/api/control_plane_contract.py:49)
- companion snapshots include `/status`, `/quality/dashboard`, `runtime_health`, `proof_status`, and `runtime_audit_summary`: [control_plane_contract.py](/c:/Users/wjjo/Desktop/글도비/modules/api/control_plane_contract.py:54)

This is strong evidence that Polaris should preserve a split between:

- durable sink truth
- operator-facing projection truth

### Stage4 proof surfaces are mostly projections

The main operator proof surfaces are derived:

- `gate_repair_summary` is an API payload builder over stored repair/gate data: [bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py:1591)
- `runtime_health` is a digest over soft-failure telemetry: [bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py:1976)
- `proof_status` is derived from sink alignment plus runtime audit summary: [bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py:2120)

These should be treated as Polaris projection surfaces, not as the durable authority themselves.

### Two important exceptions

Two surfaces should not be misfiled under “Stage4 proof projection only”:

- `control_plane_provenance` is an authoritative control-plane sink, not just a dashboard helper: [bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py:2567)
- `artifact_ladder` is a cross-stage artifact inventory projection spanning BI/TR/Arc/Blueprint/Manuscript, not a Stage4-only proof surface: [bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py:1300), [bridge_server.py](/c:/Users/wjjo/Desktop/글도비/modules/api/bridge_server.py:2207)

This makes the parent Polaris split more concrete:

- Stage4 owns verification/readback/proof projection
- control-plane provenance remains a separate authority family
- artifact lineage belongs to a cross-stage inventory family

## Pass 3. Queue-Compaction Grounding

### Low-loss compaction is real, but only part of it is repo-native today

Queue-state v1 is intentionally strict:

- item `status` only allows `pending`, `in_progress`, `completed`, `blocked`
- item `queue_role` only allows `front_active`, `blocked_holding`, `parked_future_wave`, `historical_backing`
- extra fields are disallowed

Anchors:

- [temp-queue-state-contract-v1.json](/c:/Users/wjjo/Desktop/글도비/docs/implementation/temp-queue-state-contract-v1.json:5)
- [temp-queue-state-contract-v1.json](/c:/Users/wjjo/Desktop/글도비/docs/implementation/temp-queue-state-contract-v1.json:65)

That means the current repo queue cannot yet natively represent:

- `proof_pending`
- `deferred_debt`
- a split between `active_surface_count` and total queue membership

### The queue already overstates active load

The current snapshot still says `active_item_count = 21`, even though ranks 17-21 are already `historical_backing`: [queue-state.json](/c:/Users/wjjo/Desktop/글도비/docs/temp/queue-state.json:5), [queue-state.json](/c:/Users/wjjo/Desktop/글도비/docs/temp/queue-state.json:192)

This is not evidence loss. It is a schema and visibility problem.

### ClickUp is already richer than repo-state, but only by heuristic inference

The ClickUp sync script already:

- maps `historical_backing` to `Closed`
- scans canonical doc text for proof markers to emit `Proof Pending`

Anchors:

- [sync_clickup_queue.py](/c:/Users/wjjo/Desktop/글도비/scripts/sync_clickup_queue.py:166)
- [sync_clickup_queue.py](/c:/Users/wjjo/Desktop/글도비/scripts/sync_clickup_queue.py:235)

That is useful, but it is still doc-text inference rather than repo-side contract truth.

## Synthesis

Bottom line:

`Polaris` is credible now because the repo already contains the underlying boundaries it needs.

What is missing is mostly:

- shared vocabulary
- authoritative contract naming
- projection vs authority discipline
- honest queue semantics

This is a stronger position than “big rewrite needed.”

It is closer to “existing seams need to be made explicit and then normalized.”

## Safe Post-Run Ladder

After the live run reaches a terminal state:

1. merge this survey with the completed live-run evidence
2. remove only the five `historical_backing` temp mirrors first
3. rewrite roadmap wording so proof-only lanes stop masquerading as front-active implementation
4. let ClickUp reflect proof-pending status where the next action is rerun/proof
5. open a bounded queue-state v2 design note only if repo-side truth must distinguish `realizing` vs `proof_pending` vs `deferred_debt`

Suggested minimal queue-state v2 additions:

- `execution_posture`
- `active_surface_count`
- `total_item_count`

## 3-Pass Audit Notes

Pass 1:

- document type is a survey note, not an execution SSOT
- scope is explicit: Polaris grounding, not closure

Pass 2:

- claims are tied to current code anchors, current queue contract, and current control-plane contract
- no queue mutation or live-run closure claim is made

Pass 3:

- the note is actionable because it narrows post-run choices to low-loss compaction plus contract naming/authority cleanup
- no temp mirror or ClickUp mutation is authorized while the run remains active
