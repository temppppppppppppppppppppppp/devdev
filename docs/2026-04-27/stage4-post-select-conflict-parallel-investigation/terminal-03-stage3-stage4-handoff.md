# T03 Stage3-To-Stage4 Handoff

Investigation date: 2026-04-27
Terminal: T03 (parallel investigation for GitHub issue #58 — Stage4 POST_SELECT_CONFLICT carryover drift)
Mode: read-only system-track audit (per AGENTS.md), Director authority preserved, UTF-8 only.

## Scope

Audit the Stage3 → Stage4 handoff path for stale arcs, stale blueprint state, old treatment / genre context, or wrong episode-boundary leakage that could feed into Stage4 and surface late as POST_SELECT_CONFLICT (continuity / history) downgrades.

In-scope source modules examined:
- `modules/core/stage3_context.py`
- `modules/core/stage3_envelope_builder.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_context_packets.py`
- `modules/core/stage4_orchestrator.py` (handoff entry; needed to close the loop)
- `modules/core/stage4_postselect_runtime.py` (downgrade semantics; needed to triangulate)
- `modules/core/stage0_handoff.py` (lineage primitives)
- `modules/core/stage2_orchestrator.py` (lineage producer)
- `modules/core/project_manager.py`, `modules/core/db_manager.py` (persistence + in-memory arc cache)
- `modules/domain/agents/stage3_prompt_envelope.py`
- `modules/domain/agents/stage3_retry_coordinator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- Tests: `tests/test_stage4_context_builder.py`, `tests/test_stage2_stage3_episode_boundary_guardrail.py`, `tests/test_stage2_stage3_semantic_carryover_guardrail.py`

## Commands / Evidence

Selected greps (all read-only):

- `grep -n -E "lineage|source|episode|arc_no|blueprint|handoff|previous|retry|stale|cache|plot_roadmap|stage4" modules/core/stage4_context_builder.py`
- `grep -n -E "lineage|source_lineage|cached_arcs|episode|arc_no|blueprint|handoff|previous|retry|stale|cache|plot_roadmap|stage4" modules/core/stage3_orchestrator.py`
- `grep -rn "PLOT_ROADMAP_LINEAGE_ANCHOR|save_anchor.*lineage|build_plot_roadmap_lineage" modules/`
- `grep -rn "save_anchor.*arcs|save_v20_anchor.*arcs" modules/ scripts/ main_a.py`
- `grep -rn "load_arc_payloads|arc_payloads" modules/`
- `grep -n -E "_continuity_pins|_source_lineage|_blueprint_lineage|_runtime_lineage|_lineage_fingerprint" modules/core/stage3_orchestrator.py modules/core/stage4_context_builder.py modules/core/stage4_orchestrator.py modules/core/stage0_handoff.py`
- `grep -n -E "POST_SELECT_CONFLICT|post_select_conflict" modules/ -r`

Anchor evidence cited inline below uses `path:line`. No DB / git mutation, no source edits, no third-party submissions.

### Handoff surface (the one place Stage4 actually crosses the boundary)

`modules/core/stage4_orchestrator.py:1264-1291` — `_prepare_current_episode_inputs`:

```
blueprint = self.ctx.current_project.get_blueprint(next_ep)         # 1265
...
arc_data = next(
    (arc for arc in self.ctx.current_project.arcs
     if isinstance(arc, dict) and arc.get("ep_start", 0) <= next_ep <= arc.get("ep_end", 0)),
    None,
)                                                                   # 1270-1277
```

That's the entire inter-stage contract. Two lookups, both unguarded.

### Blueprint persistence schema (Stage3 producer)

- `modules/core/db_manager.py:1473-1480` — `INSERT OR REPLACE INTO blueprints (ep_num, data) VALUES (?, ?)`. Sole key is `ep_num`. No `arc_no`, no source-lineage fingerprint, no roadmap-version column.
- `modules/core/db_manager.py:609-624` — `get_blueprint(ep_num)` returns the row's deserialized JSON. Lineage check is impossible at this layer.
- `modules/core/stage3_orchestrator.py:3018-3107` — `_annotate_stage3_success_blueprint` only stamps `_stage3_meta` (verdict, score, binding_prevalidation, fix_pack/repair_contract). No `_source_lineage` / `_plot_roadmap_fingerprint` / `_arc_no` is written into the blueprint payload.
- `modules/core/stage3_orchestrator.py:3186` — `ctx.current_project.save_episode_blueprint(working_ep, blueprint)` is called for every PASS / PASS_WITH_FIX / PASS_WITH_WARNING verdict (see 1848-1854 and 2665-2691). Once written, Stage4 has no way to know which generation of the roadmap produced it.

### Stage3 stale-blueprint skip path

`modules/core/stage3_orchestrator.py:1763-1770`:

```
_existing_bp = ctx.current_project.get_blueprint(working_ep)
if _existing_bp:
    prev_blueprints.append(_existing_bp)
    ...
    ctx.ui.log(f"   ⏭️  제{working_ep}화 - 기존 설계도 존재, 스킵")
    return {"next_ep": working_ep + 1, ...}
```

If a previous run produced a blueprint at `ep_num` under an older treatment / arcs lineage and the current run regenerated arcs (so the lineage anchor changed), `_process_single_episode` treats it as already done, appends it to the `prev_blueprints` window for downstream episodes, and never runs the new lineage's generator. Stage4 then reads that same DB row.

### Lineage-check coverage (advisory only, both stages)

The lineage primitives are correctly defined:

- `modules/core/stage0_handoff.py:23-24` — `PLOT_ROADMAP_LINEAGE_ANCHOR = "stage2_arcs_source_lineage"`, `PLOT_ROADMAP_LINEAGE_SCHEMA = "stage0.plot_roadmap_lineage.v1"`.
- `modules/core/stage0_handoff.py:311-355` — `build_plot_roadmap_lineage` (sha256 of normalized roadmap), `plot_roadmap_lineage_matches`, `cached_arcs_source_lineage_matches`. The last returns `True` when `cached_arcs` is empty, `False` when the saved lineage is missing, otherwise compares fingerprints.
- `modules/core/stage2_orchestrator.py:315-344` — Stage 2 persists `STAGE2_ARCS_SOURCE_LINEAGE_ANCHOR` exactly once when arcs are first cached and refuses to reuse the ordinal cache when lineage is stale.

Stage 3 and Stage 4 only consult the lineage on **two prompt-injection sites**, and both are silent-skip:

- `modules/core/stage3_orchestrator.py:2110-2129` — `_inject_stage3_treatment_block_context`. On mismatch: emits `_logging.warning(...)` and returns the input `_bp_semantic_ctx` unchanged. Generation continues with stale arcs.
- `modules/core/stage4_context_packets.py:626-658` — `build_tier12_auxiliary_sections` Treatment genre_ext injection. On mismatch: same `logging.warning(...)`, then sets `plot_roadmap = []` so the genre_ext block is skipped. Stage 4 then proceeds to assemble `tier1` / `tier2` / mandatory-context using the same stale `arc_data` and stale `blueprint` it already accepted.

There is no `audit_event`, no Director-visible flag, no halt path, and no propagation to `_prepare_current_episode_inputs`. The "lineage stale" condition is genuinely invisible to the Stage4 round/post-select pipeline.

### Stage3 prev-blueprint window has no lineage filter

- `modules/core/stage3_orchestrator.py:1913-1925` — `_load_prev_blueprint(working_ep)` returns `db.get_blueprint(working_ep - 1)` and merely warns when missing. No `_stage3_meta.final_verdict` / lineage gating.
- `modules/core/stage3_envelope_builder.py:127-202` — `run_blueprint_generation_handoff` passes `prev_blueprints=blueprint_window` (anchor-selected by content, not lineage) and `prev_manuscripts_text` straight into `ThreePhase blueprint runtime`. Phase 1 constraint compilation (`three_phase_blueprint_runtime.py:1511-1570` — `_resolve_constraint_block`) consumes those windows blindly to seed `prev_blueprint`-derived continuity (end_location, opening_transition, episode_state_packet). Stale carryover here propagates into the new blueprint as "authoritative" facts.

### PASS_WITH_FIX is persisted unchanged

- `modules/core/stage3_orchestrator.py:1848-1854` — success branch fires for `PASS`, `PASS_WITH_FIX`, `PASS_WITH_WARNING` alike.
- `modules/core/stage3_orchestrator.py:3060-3067` — `_stage3_meta.revision_required` is recorded but does **not** gate persistence.
- `modules/core/stage3_orchestrator.py:3186` — `save_episode_blueprint(working_ep, blueprint)` runs unconditionally once integrity passes.
- `modules/core/stage4_orchestrator.py:1265,1282-1289` — Stage 4 reads the persisted blueprint, runs `_preflight_validate_blueprint` (which can attach `_continuity_pins` but does not check `_stage3_meta.revision_required`), and proceeds. Pin-mediated drift is later caught as `opening_action_continuity` inside `_extract_opening_continuity_pin_metadata` (`stage4_postselect_runtime.py:293-320`) — already a known POST_SELECT_CONFLICT path.

### `current_project.arcs` is loaded once at startup

- `modules/core/project_manager.py:121-148` — `_load_from_db` calls `db.load_arc_payloads()` and stores the result on `self.arcs`. Mid-run callers must go through `save_v20_anchor("arcs", data)` (project_manager.py:255-256) to refresh the in-memory list.
- Direct `db.save_anchor("arcs", ...)` callers that bypass `save_v20_anchor`:
  - `modules/core/services/project_service.py:513`
  - `modules/core/stage0/reverse_expander.py:1034, 1176`
  - `modules/core/stage4_canary_tools.py:488`
  - `modules/core/smoke_fixture_tools.py:109`

  Any of these mutate the DB anchor without touching the cached `self.arcs` list, which is exactly the list Stage 4 reads at `stage4_orchestrator.py:1273`.

### Episode boundary semantics

- `modules/core/stage4_orchestrator.py:1552` — `next_ep = self.ctx.current_project.get_latest_episode_number()` (NEXT ep, i.e. `manuscript_count + 1`).
- `modules/core/stage4_orchestrator.py:1270-1277` — first arc whose `ep_start <= next_ep <= ep_end` wins. With `next(..., None)` this is silent on duplicate-arc overlap.
- `modules/core/stage4_context_builder.py:2712-2723` — `arc_pos = next_ep - arc_data.get("ep_start", next_ep) + 1`. If `arc_data` came from a stale arc with the wrong `ep_start`, `arc_pos` and `total_ep_in_arc` are silently wrong; downstream `arc_pos` is what feeds `is_arc_boundary` for the Stage 4 retrieval planner (`stage4_context_builder.py:2374-2389`).

### Authority projection feeds the new blueprint into Stage4

- `modules/core/stage4_context_builder.py:2284-2316` — `build_authoritative_continuity_projection(... accepted_blueprint=blueprint, prev_manuscript_ending=prev_ending, source_stage="stage3_blueprint", target_stage="stage4_manuscript")`. The projection is the canonical Tier-0 hand-over from Stage 3 to Stage 4. Source: the blueprint payload + the previous manuscript ending. There is no consistency check between the blueprint's *implicit* lineage and the current arc / roadmap fingerprint at this site.

### Existing test coverage

- `tests/test_stage4_context_builder.py:94-141` — `test_tier12_skips_treatment_genre_ext_when_cached_arcs_lineage_stale`: verifies the Stage 4 *advisory* skip (V74 / capital_before disappear). Does **not** verify that Stage 4 refuses to assemble the round with stale arcs / stale blueprint.
- `tests/test_stage2_stage3_episode_boundary_guardrail.py:335-376` — symmetric Stage 3 advisory skip test. Same gap: only checks that the treatment block disappears from `semantic_ctx`.
- `tests/test_stage2_stage3_semantic_carryover_guardrail.py` — covers `_normalize_semantic_carryover` quarantine of `continuity_checkpoints` / `growth_justification`. Does not cover stale-prev-blueprint carryover.

There are no tests for: (a) the Stage 3 "existing blueprint exists → skip + append to prev_blueprints" path, (b) Stage 4 reading a PASS_WITH_FIX blueprint persisted under an old roadmap, (c) duplicate / overlapping arcs returning a wrong arc via `next(..., None)`.

## Findings

F-1 — **Blueprint persistence has no source-lineage column.** `modules/core/db_manager.py:1473-1480` keys the blueprint table only on `ep_num`. The blueprint payload itself carries no lineage fingerprint (`stage3_orchestrator.py:3018-3107`). Stage 4 cannot detect that a row predates the current arcs / treatment generation. The lineage primitive that Stage 2 already publishes (`PLOT_ROADMAP_LINEAGE_ANCHOR`, `stage0_handoff.py:23,311-355`) is not consulted here.

F-2 — **Stage 3 "skip if blueprint exists" reuses stale rows wholesale.** `stage3_orchestrator.py:1763-1770` returns success and feeds the existing blueprint into `prev_blueprints` for the next episode. After a treatment / arcs regeneration this path silently reseeds the new run with the previous lineage's blueprint, including its end_location, time_flow, opening_transition, scene_breakdown, and `_stage3_meta.fix_pack`. Stage 4 then reads the same row and runs the authority projection on it.

F-3 — **Lineage check is advisory and fails-open, both stages.** `stage3_orchestrator.py:2110-2129` and `stage4_context_packets.py:626-658` are the only two consumers of `cached_arcs_source_lineage_matches`. Both react to a mismatch by emitting a single `logging.warning(...)` and returning early. There is no `audit_event`, no Director gate, no `current_project.arcs` refresh, no halt of `_prepare_current_episode_inputs` / `_process_single_episode`. Mismatched-lineage runs proceed to completion.

F-4 — **`current_project.arcs` is a startup-loaded cache and at least four code paths mutate the DB anchor without refreshing it.** See evidence list under "stale arcs". Stage 4's arc_data lookup (`stage4_orchestrator.py:1270-1277`) reads the cache directly; an external `db.save_anchor("arcs", ...)` is invisible until process restart.

F-5 — **Arc lookup is range-first-match.** `stage4_orchestrator.py:1270-1277` returns the first arc whose `ep_start <= next_ep <= ep_end`. If a partial regeneration leaves overlapping ranges in `current_project.arcs`, the older (earlier-indexed) arc wins. The `next(..., None)` default only catches the empty case; overlap is silent.

F-6 — **PASS_WITH_FIX blueprints are persisted and consumed by Stage 4 with no `revision_required` gate.** `stage3_orchestrator.py:1848-1854 + 3060-3067 + 3186` and `stage4_orchestrator.py:1265-1289`. Stage 3 records `revision_required=True` on the blueprint but Stage 4's preflight (`stage4_orchestrator.py:920-1064`) does not branch on it. The unfixed delta surfaces as POST_SELECT_CONFLICT later (continuity, opening_action_continuity, history) where Stage 4 already has the `_extract_opening_continuity_pin_metadata` path (`stage4_postselect_runtime.py:293-320`).

F-7 — **Stage 3 `_load_prev_blueprint` and the prev_blueprints anchor selector have no lineage filter.** `stage3_orchestrator.py:1913-1925` and `stage3_envelope_builder.py:18-90` carry stale prior-blueprint state into the new run's Phase 1 constraint compilation (`three_phase_blueprint_runtime.py:1511-1570`). Stale carryover therefore can be encoded as authoritative input to the new blueprint, which then becomes Stage 4's authority projection source (`stage4_context_builder.py:2284-2316`).

F-8 — **Authority projection trusts blueprint + prev_manuscript_ending without lineage.** `stage4_context_builder.py:2284-2316` builds the canonical Tier-0 continuity bridge from the persisted blueprint and the previous manuscript ending. Either input can outlive the lineage that produced it (F-1 for blueprint, F-2 for skipped-regeneration, F-7 for prior-blueprint carryover). The continuity / history validators that fire later (`stage4_postselect_runtime.py:51-211`) are by construction *after* the round has been written; they are not designed to catch lineage drift, only state contradictions.

F-9 — **Test coverage of the lineage check stops at advisory text suppression.** `tests/test_stage4_context_builder.py:94-141` and `tests/test_stage2_stage3_episode_boundary_guardrail.py:335-376` confirm "the V74 string disappears" / "treatment block disappears." Neither asserts that the consumer refuses to build the prompt or surfaces the mismatch upward.

## Root-Cause Candidates

RC-A — **Stale blueprint row consumed by Stage 4 after arcs / roadmap regeneration.** Combine F-1 + F-2 + F-3. Most plausible POST_SELECT_CONFLICT trigger when 5-arc runs regenerate roadmap mid-run (e.g. via reverse_expander or service-level arc rewrites). The continuity/history check at `stage4_postselect_runtime.py:405-468` then catches the embedded contradiction and downgrades the provisional PASS to REJECT with `gate_basis="post_select_conflict"`.

RC-B — **PASS_WITH_FIX blueprint with unresolved binding categories reaches Stage 4.** F-6. The `_continuity_pins` annotation captures *opening* drift, but other bindings (`fact_lock_*`, `protagonist_state`, `tactical_semantic_fidelity`, `arc_timeline`) live in `_stage3_meta.binding_prevalidation_categories` (`stage3_orchestrator.py:3041-3047`) and are not gated by Stage 4. Director's continuity / history checkers then flag them.

RC-C — **In-memory `current_project.arcs` desync from DB.** F-4 + F-5. If any of the four direct `db.save_anchor("arcs", ...)` callers fires during a long-running session, `_prepare_current_episode_inputs` returns the stale arc, `arc_pos` / `is_arc_boundary` mislabels the episode, and Stage 4 retrieval planner / authority projection use stale `state_changes` for the wrong arc.

RC-D — **Stale `prev_blueprint` poisoning Phase 1 constraint compilation.** F-7. Even on a fresh Stage 3 run, the compiler reads `db.get_blueprint(working_ep - 1)` without lineage filtering. If episode N-1 was generated under the old roadmap and not regenerated, episode N's new blueprint inherits its end_location / opening_transition. Stage 4 then projects the inherited values onto the manuscript and the post-select continuity check finds a mismatch with the *actual* prior published manuscript.

RC-E — **Episode-boundary mislabeling on overlapping arcs.** F-5. Less likely as a primary trigger but compounds RC-A / RC-C. First-match `next(...)` semantics make this path silent.

## Regression / Test Candidates

RT-1 — **Stage 4 lineage refusal test.** Mirror `test_tier12_skips_treatment_genre_ext_when_cached_arcs_lineage_stale` against `_prepare_current_episode_inputs`: when `cached_arcs_source_lineage_matches(...) is False`, Stage 4 must (current behaviour) at minimum surface an `audit_event("lineage_stale", ...)` or refuse to build the round. The test should fail today, locking the design choice.

RT-2 — **Stage 3 stale-skip carryover test.** Pre-seed `blueprints` with a row at `ep_num=3` whose `_stage3_meta.lineage_fingerprint` differs from the current `build_plot_roadmap_lineage(plot_roadmap)`; run `_process_single_episode(working_ep=3, …)`; assert that the row is *not* silently appended to `prev_blueprints` and that `prev_blueprints` for `ep_num=4` is not poisoned.

RT-3 — **PASS_WITH_FIX gate test.** Persist a blueprint with `_stage3_meta.revision_required=True` and `_stage3_meta.binding_prevalidation_categories=["fact_lock_item"]`; call `Stage4Orchestrator._prepare_current_episode_inputs`; expected (current behaviour) is that preflight surfaces a `revision_required` advisory or downgrades to a regenerate request. The test will fail today.

RT-4 — **In-memory arcs desync test.** Mutate `db.save_anchor("arcs", new_arcs)` directly without `save_v20_anchor`; call `_prepare_current_episode_inputs` and assert `arc_data` reflects the new arcs (or that `current_project.arcs` was refreshed).

RT-5 — **Overlapping arcs test.** Construct `current_project.arcs` with two arcs whose `[ep_start, ep_end]` overlap on `next_ep`; assert the lookup raises / logs / returns the *latest* arc by lineage rather than first-by-list-order.

RT-6 — **Stage 3 prev_blueprint lineage filter.** Pre-seed `ep_num - 1` blueprint with stale lineage; run `_resolve_constraint_block` for `ep_num`; assert that `prev_blueprint` is dropped or flagged before Phase 1 compiles its constraint block.

RT-7 — **End-to-end: lineage stale → POST_SELECT_CONFLICT.** Construct a 5-arc fixture, generate Stage 3 blueprints under lineage A, mutate `plot_roadmap` to lineage B, run Stage 4 manuscript generation; assert that POST_SELECT_CONFLICT is detected *and* that the post-select runtime emits a `lineage_drift` reject_bucket variant (currently absent — the bucket is only `post_select_conflict`).

## Dependencies On Other Terminals

- T01 (issue baseline / reproduction): needs to confirm the live POST_SELECT_CONFLICT trace already attaches `lineage_fingerprint` to the rejected attempt OR confirm that the absence of that field is itself the missing telemetry. RC-A presumes the latter.
- T02 (feedback / Stage4-to-Stage3 reverse-feedback path) if present: needs to confirm whether `_generate_reverse_feedback_stage4_to_3` (`stage4_context.py:31-39`) carries lineage-stale information back to Stage 3, or whether reverse feedback is lineage-blind today (likely).
- T04 / T05 (post-select runtime, Stage 4 retry runtime): the `previous_attempt.conflict_contract` shape (`stage4_postselect_runtime.py:213-290`) does not currently include a lineage-drift slot; coordinate before adding `lineage_drift` rewrite_required_reasons.
- T06 (Stage 2 producer / arcs lifecycle): owns whether `db.save_anchor("arcs", ...)` callers should be forced through `save_v20_anchor` and whether the lineage anchor should be re-stamped on every arcs mutation. F-4 lives at this seam.

## Open Questions

OQ-1 — Should `cached_arcs_source_lineage_matches` mismatch be a hard halt for Stage 3 / Stage 4 round builds, or should runs continue with a Director-visible advisory? Current code is the latter (silent log).

OQ-2 — Should the blueprint payload carry an embedded `_source_lineage` (sha256 of the roadmap at generation time) so Stage 4 can detect drift directly? F-1.

OQ-3 — Should Stage 3's "blueprint exists → skip" path be lineage-aware, regenerating when the persisted row's lineage differs from current? F-2.

OQ-4 — Should `revision_required` blueprints be allowed to flow into Stage 4 unchanged, or must Stage 4 preflight refuse / regenerate? F-6.

OQ-5 — What guarantees should we offer that `current_project.arcs` reflects the DB? F-4. Options: invalidate-on-`save_anchor`, replace direct `db.save_anchor("arcs", ...)` callers with `save_v20_anchor`, or refresh on every Stage 4 round entry.

OQ-6 — Should overlapping-arc detection be promoted from "first match wins" to a structural invariant validated at `_load_from_db`? F-5.

OQ-7 — Does the expected `POST_SELECT_CONFLICT` reject_bucket need a sub-bucket for `lineage_drift` so reverse-feedback can route differently from raw continuity / history conflicts? Affects RT-7 and T04 / T05 coordination.

## Closure Recommendation

Treat **RC-A (stale blueprint after arcs regeneration)** and **RC-B (PASS_WITH_FIX without Stage 4 gate)** as the two leading candidates for the 5-arc run drift. Both are reachable today with the lineage primitives already in `stage0_handoff.py` and `stage2_orchestrator.py`; the gap is consumer-side enforcement at the Stage 3 → Stage 4 boundary, not anchor production.

Recommended next system-track moves (read-only investigation closes here; realization deferred per AGENTS.md):

1. Tighten the lineage check at the producer and consumer of the persisted blueprint (F-1, F-2, F-3): stamp `_source_lineage` on the blueprint payload; gate Stage 3's "exists → skip" and Stage 4's `_prepare_current_episode_inputs` on lineage equality; raise `audit_event("lineage_stale", ...)` and refuse the round on mismatch.
2. Add a Stage 4 preflight gate for `_stage3_meta.revision_required=True` and any non-empty `_stage3_meta.binding_prevalidation_categories` (F-6), routing back to Stage 3 reverse-feedback rather than into the writer.
3. Close the `current_project.arcs` desync (F-4) by either routing all arc anchor writes through `save_v20_anchor` or refreshing the in-memory list at the top of `_prepare_current_episode_inputs`.
4. Land regression tests RT-1, RT-2, RT-3, RT-4 first (lowest blast radius); RT-7 after the runtime gate is in place.

Confidence in the structural findings: high (all anchors are inline source citations, no DB / live-run inference). Confidence in the *primary* root cause among RC-A / RC-B: medium — requires T01's reproduction trace to disambiguate. Per AGENTS.md document-save rule, this report is a draft analysis pending 3-pass cross-terminal review before promotion to canonical execution SSOT.
