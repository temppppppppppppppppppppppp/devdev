# Interfaces

Purpose:
- Capture caller-callee contracts across stages.
- Keep stage boundaries explicit, testable, and aligned to the current workspace.

## Contract Matrix

| From | To | Input Contract | Output Contract | Failure / Degraded Contract | Owner |
|---|---|---|---|---|---|
| Stage 0 | Stage 1 | `anchors["bible"]` / `current_project.master_bible`; optional `preset_state`, optional `style_guide` | Stage 1 reads `MasterBible.plot_roadmap` and may write `anchors["volumes"]` | Missing or malformed anchors degrade to reload / defaults; Stage 1 is optional for downstream flow | Stage 0 / Stage 1 |
| Stage 1 | Stage 2 | Optional `anchors["volumes"]`; Stage 2 still requires Bible + plot roadmap | Stage 2 writes `anchors["arcs"]` as list[Arc-like dict] | If `volumes` is absent, Stage 2 uses `strategy_doc=""` fallback | Stage 1 / Stage 2 |
| Stage 2 | Stage 3 | `anchors["arcs"]` plus Arc dict fields such as `arc_no`, `ep_start`, `ep_end`, `tactical_doc`, `joint_docs`, `status_shadow`, `episode_details` | Stage 3 reads Arc context and writes `blueprints.data` plus optional `_stage3_meta` | Arc schema can be repaired via `validate_arc_data_fields`; malformed data may retry or fail-closed per episode | Stage 2 / Stage 3 |
| Stage 3 | Stage 4 | `db.get_blueprint(ep_num)` returns blueprint dict; txt export is not an input contract | Stage 4 consumes blueprint dict and may read optional `_stage3_meta` (`quality_risk`, `last_score`, `final_verdict`) | Missing / JSON-broken blueprint returns `None`; Stage 4 stops at the missing episode | Stage 3 / Stage 4 |
| Stage 4 | Downstream state | PASS-family manuscript, director result, state updates, episode metadata | `manuscripts`, `state_logs`, `episode_bibles`, `world_state`, `fact_ledger`, memory / quality sinks | `PASS_WITH_WARNING` remains a valid degraded stored outcome; `EMPTY` caller result is logged as attempt `ERROR` with `reject_reason="empty_candidates"` | Stage 4 |

## Shared Invariants
- Invariant 1: DB is the durable handoff surface.
  - `anchors`, `blueprints`, `manuscripts`, `episode_bibles`, `state_logs` carry the real cross-stage contract.
  - human-readable txt exports are operational artifacts, not upstream input truth.
- Invariant 2: Stage 2 / 3 / 4 all use `scoring.quality_gate_score = 90` as the live QualityGate.
  - `PASS_WITH_FIX` bypasses the initial gate entry.
  - a later re-review that resolves to plain `PASS` still goes through the 90-point gate.
- Invariant 3: Stage 3 may emit degraded blueprint metadata.
  - `_stage3_meta.quality_risk`
  - `_stage3_meta.quality_gate_failed`
  - `_stage3_meta.last_score`
  - Stage 4 may tighten escalation behavior when this metadata is present.
- Invariant 4: JSON contract failures prefer controlled degradation over silent schema invention.
  - `load_anchor()` returns defaults on parse failure.
  - `get_blueprint()` returns `None` on JSON parse failure.
  - Arc repair is routed through `validate_arc_data_fields` when the seam is available.
- Invariant 5: Director verdict family remains:
  - `PASS`
  - `REJECT`
  - `PASS_WITH_FIX`
  - `PASS_WITH_WARNING` can appear as a degraded stored result in Stage 3 and Stage 4 flows.
- Invariant 6: Stage 4 `state_updates` merge priority remains `Director > Chief Writer > {}`.
  - In-place patch merges patch state into the current final state update set instead of replacing it wholesale.

## Key Persistence Surfaces
- `anchors`
  - `bible`
  - `preset_state`
  - `style_guide`
  - `volumes`
  - `arcs`
  - `series_summary`
  - `volume_summary_*`
  - `arc_summary_*`
  - `world_state`
  - `fact_ledger`
- tables
  - `blueprints`
  - `manuscripts`
  - `episode_bibles`
  - `state_logs`
  - `stage_attempts`
  - `director_selections`
  - `episode_meta`
  - `episode_fts`
  - `episode_pacing`
  - `npc_history`
  - `npc_relationship_history`
  - `cost_log`
  - `foreshadow`

## Breaking Change Checklist
- Was an input field added, removed, or renamed?
- Was an output field added, removed, or renamed?
- Did a stage switch from DB truth to export-file truth, or vice versa?
- Did verdict semantics or degraded outcomes change?
- Did retry or QualityGate rules change?
- Did a safe-op delete / preserve boundary move?

## Last Verified
- Date: 2026-03-13
- Commit: `e18f9910`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
