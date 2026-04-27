# T04 Continuity Authority Carriers

Date: 2026-04-27
Workspace: `C:\Users\wjjo\Desktop\글도비`
GitHub issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Status: read-only investigation; this terminal does not claim 5-arc readiness, does not patch code, and does not close #58.

## Scope

Map the modules that are *named* as continuity authority carriers in the codebase, decide which truth ought to be authoritative at Stage4 (POST_SELECT verdict and the candidate-quality gate that drives `POST_SELECT_CONFLICT`), and check whether Stage4 actually consumes that truth.

In-scope files (read-only inspection):
- `modules/core/authoritative_continuity_projection.py` (ACP)
- `modules/core/continuity_canary.py`
- `modules/core/continuity_pin_guard.py`
- `modules/core/episode_state_arbiter.py`
- `modules/core/stage4_immutable_fact_contract.py` (IFC)
- `modules/validation/continuity_validator.py` (Tier 0.5)
- `modules/domain/agents/continuity_arc.py`
- `modules/domain/agents/continuity_blueprint.py`
- `modules/domain/agents/continuity_inspector.py` (facade)
- `modules/domain/agents/continuity_manuscript.py`
- `modules/domain/agents/continuity_tracker.py`
- `modules/domain/agents/director_continuity.py` (DCV)

Adjacent runtime sites consulted only to resolve "is this carrier actually consumed at Stage4":
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_postselect_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/session_memory_envelope.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/director.py`
- `modules/domain/agents/director_prompts.py`
- `modules/validation/validation_orchestrator.py`
- `tests/test_authoritative_continuity_projection.py`
- `tests/test_continuity_canary.py`
- `tests/test_continuity_pin_guard.py`
- `tests/test_continuity_validator.py`
- `scripts/run_auto_frontier_lag_harness.py` (read references only)

## Commands / Evidence

Tool-driven inspection (selected):

- `git ls-files modules/core/authoritative_continuity_projection.py modules/core/continuity_canary.py modules/core/continuity_pin_guard.py modules/core/episode_state_arbiter.py modules/core/stage4_immutable_fact_contract.py modules/validation/continuity_validator.py modules/domain/agents/continuity_arc.py modules/domain/agents/continuity_blueprint.py modules/domain/agents/continuity_inspector.py modules/domain/agents/continuity_manuscript.py modules/domain/agents/continuity_tracker.py modules/domain/agents/director_continuity.py` — all 12 files tracked.
- `wc -l` of the same set — `8,852` lines total. The two largest are `validation/continuity_validator.py` (1,265) and `domain/agents/continuity_manuscript.py` (1,234). The smallest is `continuity_pin_guard.py` (207).
- `git grep -ln "authoritative_continuity_projection|build_authoritative_continuity_projection|render_authoritative_continuity_projection_for_prompt"` — runtime consumers: `modules/core/session_memory_envelope.py`, `modules/core/stage3_orchestrator.py`, `modules/core/stage4_context_builder.py`. Test consumers: `tests/test_authoritative_continuity_projection.py`, `tests/test_session_memory_envelope.py`, `tests/test_stage3_orchestrator.py`, `tests/test_stage4_context_builder.py`.
- `git grep -ln "ImmutableFactPacket|build_packet|render_packet_for_cw|stage4_immutable_fact_contract"` — runtime consumers: `modules/core/stage4_immutable_fact_contract.py` (definition), `modules/core/stage4_post_pass_runtime.py`, `modules/core/stage4_reject_runtime.py`, `modules/domain/agents/chief_writer_context.py`. Tests: `tests/test_chief_writer_context.py`, `tests/test_stage4_immutable_fact_contract.py`.
- `git grep -ln "EpisodeStateArbiter|episode_state_arbiter|arbitrate(|cross_stage_authority_packet"` — runtime consumers cluster at Stage2 finalizer and Stage3 (`modules/core/stage2_finalizer.py`, `modules/core/stage4_context_builder.py`, `modules/core/stage4_post_pass_runtime.py`, `modules/domain/agents/blueprint_constraint_compiler.py`, `modules/domain/agents/chief_writer_context_packets.py`, `modules/domain/agents/three_phase_blueprint_runtime.py`).
- `git grep -ln "apply_continuity_pins|continuity_pin_guard|evaluate_continuity_canaries|continuity_canary"` — `apply_continuity_pins` is invoked at `modules/core/stage3_orchestrator.py:3144` and `modules/core/stage4_orchestrator.py:1036`. `evaluate_continuity_canaries` is invoked **only inside `modules/core/continuity_canary.py` itself and `tests/test_continuity_canary.py`** — no Stage3/Stage4 module calls it. `read_continuity_canary_report` is called only from `scripts/run_auto_frontier_lag_harness.py:27,1344`, which is a harness reader, not a writer.
- `git grep -n "inspect_manuscript|inspect_blueprint" -- modules` — `inspect_arc` lives inside the live Stage2 path (`modules/core/stage2_validation_pipeline.py:980`); `inspect_manuscript` and `inspect_manuscript_v59` are defined in `continuity_inspector.py` and `continuity_manuscript.py` but **have no caller in `modules/core/`, `modules/domain/`, or `main_a.py`**. Only `tests/test_continuity_modules.py` and `tests/test_sweep29.py` reference them.
- `git grep -n "post_select_conflict|POST_SELECT_CONFLICT|reject_bucket"` in `modules/core/stage4_reject_runtime.py` — `reject_bucket = "post_select_conflict"` mapping at lines 1444-1455, plus `_bucket_to_category = { "post_select_conflict": "POST_SELECT_CONFLICT", … }` at line 996.
- `git grep -n "MANUSCRIPT_HISTORY_CONFLICT_PROMPT" -- modules` — the same prompt template feeds both `check_manuscript_history_conflicts` and `check_manuscript_continuity_with_cache` (Director-side LLM continuity check). Inline definition: `modules/domain/agents/director_prompts.py:179-223`.
- Read-throughs of the inline prompt text (`director_prompts.py:175-223`) and of both DCV entry points in `modules/domain/agents/director_continuity.py:680-740, 966-1085`.
- Read-throughs of the IFC packet builder, `classify_violation_family`, `should_escalate_to_rewrite`, and the CW prompt rendering in `modules/core/stage4_immutable_fact_contract.py:130-700`.
- Read-through of `EpisodeStateArbiter.arbitrate` and `summarize_episode_state_packet` in `modules/core/episode_state_arbiter.py:447-997`.
- Read-through of `evaluate_continuity_canaries` and the four canary IDs in `modules/core/continuity_canary.py:217-340`.
- Read-through of `apply_continuity_pins`, the proper-noun / elapsed-time / opening-action heuristics in `modules/core/continuity_pin_guard.py`.
- Read-through of the Tier 0.5 `ContinuityValidator.validate` invocation in `modules/core/stage4_interview_round.py:5953-5984` (advisory-only routing into `validation_results[ci]["warnings"]`).

A full read of every file in scope was performed where size allowed; for the four ≥1k-line modules (`validation/continuity_validator.py`, `continuity_manuscript.py`, `continuity_arc.py`, `episode_state_arbiter.py`) head-and-region reads sufficed because the runtime contracts and authority labels are concentrated near the public entry points.

## Findings

### Inventory of named carriers and what they actually do

| Carrier | Self-declared authority role | Live runtime consumer | Output gating shape |
|---|---|---|---|
| `authoritative_continuity_projection.py` (ACP) | `authority_role: "typed_route_packet_not_final_verdict"`; `judgment_authority: "director_llm"`; `mutation_policy: "python_may_collect_and_route_only"` (lines 322-339) | `stage3_orchestrator.py:2256-2271` injects ACP text into Stage3 prompt; `stage4_context_builder.py:2284-2316` injects ACP text into Stage4 `tier0_parts` prompt prefix; `session_memory_envelope.py:154-214` mirrors the projection key into stage4 attempt envelopes | Pure prompt-side routing; never blocks. |
| `continuity_canary.py` | `authority_role: "objective_tripwire_not_director_verdict"`; emits findings with `requires_director_review: True` for four canary IDs that match the #58 bug shapes verbatim: `date_drift`, `location_drift`, `dead_character_active_role`, `prior_failure_replay` (lines 305-317) | **No production writer.** `evaluate_continuity_canaries` is called only from `tests/test_continuity_canary.py`. `read_continuity_canary_report` is called only from `scripts/run_auto_frontier_lag_harness.py` (post-mortem reader). No Stage3/Stage4 orchestrator, context-builder, post-select runtime, or reject runtime imports it. | Effectively dead at runtime. The harness can fail strict-success if the report exists and contains review findings, but nothing in the live pipeline writes the report. |
| `continuity_pin_guard.py` | Deterministic Python rewrites of Stage3 *blueprint* text for proper-noun pin, elapsed-time bucket, and opening-action reversal (lines 133-207) | `stage3_orchestrator.py:3144` and `stage4_orchestrator.py:1036` (both inside *blueprint* preflight, not on Stage4 candidate manuscripts) | Mutates blueprint and emits a `changes` list; `opening_action_continuity_pin` is a marker, not a rewrite. Does not run on Stage4 candidate manuscripts. |
| `episode_state_arbiter.py` | "Resolve one bounded Stage3-first episode-state packet" (file docstring lines 1-9). Returns `source_precedence`, `opening_truth`, `protagonist_truth`, `dropped_conflicts`, `rewrite_required_reasons` | Stage3 only: `domain/agents/blueprint_constraint_compiler.py:692, 805` instantiates and calls `arbitrate(...)`; the resulting packet is consumed by `blueprint_ensemble.py` and `unified_blueprint_validator.py`. Stage4 only sees a flattened `summarize_episode_state_packet` summary forwarded via `three_phase_blueprint_runtime.py:1566-1568` and `stage3_orchestrator.py:60-73,2565-2585`. | Stage3-bound. Stage4 does **not** re-arbitrate, does **not** consume `dropped_conflicts` as a gate, and does **not** read `source_precedence` for verdict purposes. |
| `stage4_immutable_fact_contract.py` (IFC) | "derived-only — never becomes a new authority owner" (docstring lines 1-12). Hard-fact families: `opening_anchor_drift`, `committed_state_regression`, `completed_event_replay`. Rewrite-biased families: those three plus `scene_order_drift`. | `domain/agents/chief_writer_context.py:584-606` renders the packet into the CW prompt. `stage4_reject_runtime.py:1471-1505` post-classifies Director rejection text into IFC families and may escalate to rewrite. `stage4_post_pass_runtime.py:1124` uses only `normalize_relationship_changes`. | Prompt-side hard contract for the writer (with explicit "⛔" bullets) plus a post-hoc family classifier on rejections. Director still owns the verdict. |
| `validation/continuity_validator.py` (Tier 0.5) | "API 호출 불필요 - 순수 Python" inventory/injury/pressure/location/personality/time checks (file header). Fail-closed degraded mode when `prev_hud` missing (lines 152-174). | `stage4_interview_round.py:5953-5984` runs it per candidate; the result is converted into `validation_results[ci]["warnings"]` rather than blocking selection. `validation_orchestrator.py:227, 477` lists it as TIER 0.5. | Advisory-only at Stage4. Even `BLOCKING` violations from this validator are appended as `[V66.1] 연속성: …` warnings, not as REJECT seeds for the Director. |
| `domain/agents/continuity_arc.py` | LLM Arc-level continuity inspection (`inspect_arc`) | `stage2_validation_pipeline.py:980` (Stage2 only) | Live Stage2 gate. |
| `domain/agents/continuity_blueprint.py` | LLM Blueprint-level inspection. The historic facade `inspect_blueprint` is implemented inside the module but the live Stage3 path uses `Director.check_blueprint_continuity_with_cache` instead (Python+cache, location-discontinuity oriented). | `three_phase_blueprint_runtime.py:2018` calls `director.check_blueprint_continuity_with_cache(...)`. The blueprint inspector's LLM prompt is reachable but is not the authoritative Stage3 continuity gate. | Stage3 cache-based location check; not a Stage4 gate. |
| `domain/agents/continuity_inspector.py` (facade) and `continuity_manuscript.py` `.inspect_manuscript()`/`.inspect_manuscript_v59()` | Designed Stage4 LLM continuity inspector consuming Entity Registry, prior manuscripts, hud history. | **No caller in `modules/core/`, `modules/domain/`, or `main_a.py`** (verified via `git grep -n "inspect_manuscript"`; only `tests/test_continuity_modules.py` and `tests/test_sweep29.py` exercise it). | Dead at runtime in current Stage4. |
| `domain/agents/continuity_tracker.py` (V49.7 trackers) | StateDelta / Relationship / PowerScaling / Foreshadow trackers, initialized by `ContinuityInspector.__init__`. | Same caller chain as the inspector. Since `inspect_manuscript` is dead, the trackers are not invoked at Stage4 either. Some trackers are still consulted directly (e.g. `state_tracker.check_destroyed_entity_in_manuscript` at `stage4_interview_round.py:6004`), but as advisory warnings. | Indirectly dead at Stage4 except for a few direct, advisory-only side-channels. |
| `domain/agents/director_continuity.py` (DCV) | Two methods that produce **the actual Stage4 POST_SELECT verdict**: `check_manuscript_history_conflicts` and `check_manuscript_continuity_with_cache` (LLM, fed by cached prior manuscripts). | `stage4_postselect_runtime.py:498-518` runs both in parallel for every selected candidate; either returning `decision == "CONFLICT"` produces a `[Continuity Conflict]` or `[V67] History Conflict` line that classifies as `POST_SELECT_CONFLICT`. | This is the only carrier with the authority to drive `POST_SELECT_CONFLICT`. |

### Where the verdict for `POST_SELECT_CONFLICT` actually comes from

`stage4_postselect_runtime.py:480-542` is the only path that emits `[Continuity Conflict]` or `[V67] History Conflict`, both of which classify as `POST_SELECT_CONFLICT` via `_classify_post_select_conflicts` (lines 544-560 of the same file) and via `_bucket_to_category = { "post_select_conflict": "POST_SELECT_CONFLICT" }` in `stage4_reject_runtime.py:996-1002`. Both fail-closed paths (`fut_continuity` exception, `fut_history` exception, lines 527-540) also produce `POST_SELECT_CONFLICT`-classifiable lines. The two LLM calls share `MANUSCRIPT_HISTORY_CONFLICT_PROMPT` defined inline in `modules/domain/agents/director_prompts.py:179-223`. Reading that prompt template:

- The *only* template variables are `{ep_num}`, `{manuscript_history}`, `{current_manuscript}`, `{story_context}`. An optional vector-memory block (`### 🔍 [SC-5] 벡터 메모리 참고 …`) is appended after rendering (DCV `director_continuity.py:688-689, 1030-1031`).
- The prompt does **not** carry ACP `non_regression_anchors`, IFC `committed_state_facts / completed_event_facts / carryover_cliffhanger / carryover_location / carryover_time_marker`, EpisodeStateArbiter `opening_truth.location_source` / `time_source` / `dropped_conflicts`, or canary findings. These structured carriers are absent from the verdict-side input even though several of them are simultaneously present on the *prompt side* of Chief Writer.

### How those carriers reach Stage4 today

- ACP is injected into the Stage4 CW prompt as a `tier0_parts` prefix (`stage4_context_builder.py:2284-2316`). The render header is `[Authoritative Continuity Projection]` and includes the line "role: typed route packet; Director/LLM remains final narrative judge."
- IFC is rendered into the CW prompt's hard-canon section by `chief_writer_context.py:573-609`. The render starts with "### [IFC] 불변 사실 계약" and contains "⛔ 위 anchor를 무전환으로 덮어쓰거나, 직전 화에서 이미 끝난 행동을 opening에서 다시 재연하면 즉시 불합격." — but the only place that actually *enforces* this assertion in the pipeline is the writer prompt itself; verdict enforcement still goes through the LLM Director cache check.
- EpisodeStateArbiter's resolved truth is consumed at Stage3 by `blueprint_constraint_compiler.py` and surfaces into `chief_writer_context_packets.py`; Stage4 only sees a flattened summary.
- `apply_continuity_pins` runs on the *Stage3 blueprint* during preflight. If a Stage4 candidate manuscript itself drifts on quotation marks, elapsed-time bucket, or opening-action reversal, the pin guard does not see the manuscript text.
- `continuity_canary.py` is not invoked by any production writer path. The harness in `scripts/run_auto_frontier_lag_harness.py` *reads* `logs/continuity_canary_report.json` only if it exists and only as a strict-success gap source. There is no production caller of `evaluate_continuity_canaries` or `write_continuity_canary_report`.
- `validation/continuity_validator.py` runs per candidate (`stage4_interview_round.py:5953-5984`) but its violations are folded into `validation_results[ci]["warnings"]`. Its severity-`BLOCKING` `prev_hud_missing` finding is not promoted into a hard reject by the surrounding routing — the loop only logs and moves on.
- `ContinuityInspector.inspect_manuscript(...)` has no live caller. Stage4 has no LLM-anchor-aware continuity inspector that consumes Entity Registry + prior manuscripts + the typed packets together.

### Which continuity truth *should* be authoritative at Stage4 (per design labels)

The codebase already declares the answer:

- ACP (`accepted_source_state` and `non_regression_anchors`) is the typed Stage3→Stage4 route packet. Every `non_regression_anchor` carries `route_instruction` text such as "Honor this location or explicitly transition away before new action." This is the carrier that should be authoritative for ep-boundary continuity routing.
- IFC (`carryover_cliffhanger`, `carryover_location`, `carryover_time_marker`, `committed_state_facts`, `completed_event_facts`, `scene_obligations`) is the derived-only contract that should bind the writer and bind reject classification. The render explicitly states "불변 사실과 로컬 개연성이 충돌하면, 불변 사실이 우선합니다."
- EpisodeStateArbiter packet is the upstream Stage3 source-precedence resolver; at Stage4 its `dropped_conflicts` should be visible as evidence that a `mid_arc_*_override_blocked` reason exists and that the candidate must not silently re-introduce the dropped value.
- `continuity_canary` covers exactly the four #58-shaped tripwires: date drift, location drift (a close cousin of institution drift), dead character active role, prior failure replay. The design intent — Director-reviewed deterministic tripwires — fits the bug shape almost word-for-word.

### Whether Stage4 actually consumes that truth

Yes for the writer prompt; no for the verdict.

- The writer (Chief Writer) is given ACP and IFC text as hard-canon prefix, and the DDC tactical/blueprint context that descends from EpisodeStateArbiter. So the writer is informed.
- The Stage4 candidate-quality gate is `validation_orchestrator` (Tier 0.5–3) plus per-round Director scoring. None of those tiers consume ACP or IFC structurally; Tier 0.5 is HUD-driven and downgraded to advisory warnings.
- The Stage4 *POST_SELECT* gate that emits `POST_SELECT_CONFLICT` is `DirectorContinuityValidator.check_manuscript_continuity_with_cache` plus `DirectorContinuityValidator.check_manuscript_history_conflicts`. Both run the same LLM template fed by `manuscript_history`, `current_manuscript`, `story_context`, and an optional memory blob. They do not receive ACP `non_regression_anchors`, IFC `carryover_*`, EpisodeStateArbiter resolution, canary findings, or pin-guard markers. The verdict is therefore re-derived from raw cached manuscript text rather than from the structured carriers the rest of the system already produced.

This is the central authority gap.

## Root-Cause Candidates

These are continuity-authority candidates only; T01/T02/T05/T06/T07/T09 still need to confirm whether the live ep4–ep9 attempts match each shape. The strength column reflects how well the carrier's design matches the visible #58 bug shape; it is not a claim that this is the actual cause.

1. **Authority-gap between prompt-side carriers and verdict-side LLM cache check.** ACP `non_regression_anchors` and IFC `carryover_*` reach the writer but are absent from `MANUSCRIPT_HISTORY_CONFLICT_PROMPT`'s variables. The verdict that drives `POST_SELECT_CONFLICT` re-derives "did this drift?" from raw cached manuscripts. This is structurally the cleanest explanation for repeated date drift and duplicated continuation beats surviving multiple retries — the system has the anchors, but the verdict gate cannot reach them. Strength: **High**.
2. **`continuity_canary.evaluate_continuity_canaries` is dead at runtime.** The four canary IDs (`date_drift`, `location_drift`, `dead_character_active_role`, `prior_failure_replay`) cover the four #58-named bug shapes. No Stage3/Stage4 module calls the function and no production writer emits `logs/continuity_canary_report.json`. The deterministic tripwire that should fire at exactly the bug surface in the issue body is silent. Strength: **High** for "this is why structural detection misses".
3. **`ContinuityInspector.inspect_manuscript` is unwired in the live Stage4 path.** The class is constructed (`sovereign_bootstrap_runtime.py:65, 96`), `inspect_arc` is alive at Stage2, but `inspect_manuscript` has no caller in `modules/core/` or `main_a.py`. Stage4 therefore has no LLM-anchor-aware continuity inspector that combines Entity Registry, prior manuscripts, hud history, and Blueprint at once. Institution-name drift in particular — a category the Entity Registry was built to police — has no Stage4 detector. Strength: **Medium-High**.
4. **`validation/continuity_validator.py` is downgraded to advisory.** Even hard violations from this Tier 0.5 validator end up as `validation_results[ci]["warnings"]`. The validator is also fail-closed-but-non-blocking when `prev_hud` is missing — the warning string `[V66.1] 연속성: …` is emitted but the candidate continues. So inventory/injury/pressure drift cannot drive the candidate's verdict. Strength: **Medium**.
5. **`apply_continuity_pins` does not run on Stage4 candidate manuscripts.** Both invocations live in *blueprint* preflight. So Stage4 cannot deterministically self-correct quoted-name mismatches, elapsed-time bucket mismatches, or opening-action reversals in the candidate text itself. Strength: **Low-Medium** (this is more of a missing safety net than a primary cause).
6. **EpisodeStateArbiter dropped-conflict evidence does not gate Stage4.** The arbiter records `mid_arc_arc_start_location_override_blocked`, `mid_arc_cross_stage_packet_location_override_blocked`, `mid_arc_arc_start_equipment_override_blocked`, etc. (lines 593-633, 808-877). At Stage4 only a flat summary is forwarded; the verdict gate cannot use these reasons to suppress a candidate that re-introduces the blocked value. Strength: **Medium**.
7. **POST_SELECT failure-mode amplifies the gap.** When DCV throws (timeout, parsing, safety), `fail-closed` appends `[Continuity Check Error]`, which classifies as `POST_SELECT_CONFLICT`, and `stage4_reject_runtime.py:1507-1545` then forces `resolved_fix_scope = "full"` and may blank the fix_pack. So repeated retries do not accumulate IFC/ACP anchors targeted at the actual drift; each retry restarts the rewrite without structural anchors. Strength: **Medium**.
8. **DCV's `summary` collapses anchor-specific drift to free-form text.** The conflict prompt only asks for `decision`, `conflicts[]`, and `summary`. The post-hoc IFC `classify_violation_family` then bins the free-form text into families — but free-form text is the only signal, so binning quality is bounded by what the LLM happened to write. This explains why the same family of drift can recur across rounds without retry guidance becoming sharper. Strength: **Medium**.

## Regression / Test Candidates

Test designs only. Do not implement here.

1. **ACP+IFC injection symmetry test (Stage4 verdict path).** Build a Stage4 fixture with ep≥2, an arc_data containing `state_constraints.arc_start_state.location` and a non-empty `time_flow`, an `accepted_blueprint` with `end_location`/`time_flow`/`ending_hook`, and a `prev_manuscript_ending`. Assert that whatever prompt or evidence object is handed to `DirectorContinuityValidator.check_manuscript_continuity_with_cache` carries the ACP `non_regression_anchors` block and the IFC `carryover_cliffhanger`/`carryover_location`/`carryover_time_marker`. Today this assertion would fail by design — that is the regression to design.
2. **Continuity-canary live-wiring test.** Construct a candidate manuscript that violates each of the four canary IDs (`date_drift`, `location_drift`, `dead_character_active_role`, `prior_failure_replay`) given a built ACP. Assert that during a Stage4 round the `evaluate_continuity_canaries` output is computed, persisted to `logs/continuity_canary_report.json`, and either routed to Director feedback or appended to `validation_results[ci]["warnings"]` with a `requires_director_review: True` flag. Today this assertion fails because the function has no production caller.
3. **`inspect_manuscript` dead-code test.** Either revive the inspector at Stage4 with a packet-aware prompt that consumes Entity Registry + IFC + ACP + prior manuscripts, and add a test that exercises it on an Entity-Registry-named institution drift; or, if the design intent is to retire it, add a test asserting it is no longer constructed and its dependencies are removed. The current state — alive in code, dead in main flow — is the regression.
4. **Pin-guard on Stage4 candidate test.** Add a test that runs `apply_continuity_pins` (or a Stage4-specific analogue) on a candidate manuscript whose only drift is a quoted institution name conflicting with the previous published text. Assert that the pin emits a `proper_noun_pin` change and that the pin result is routed back to the candidate or to Director feedback. Today no such pipeline exists at Stage4.
5. **EpisodeStateArbiter dropped-conflict gate test (Stage4 side).** Build a fixture where `arbitrate(...)` returns a non-empty `dropped_conflicts` with reason `mid_arc_arc_start_location_override_blocked`. Assert that a Stage4 candidate that re-introduces the dropped location triggers a Director-visible REJECT signal, not just a free-form LLM continuity check. Today the dropped-conflict evidence exists at Stage3 but cannot block at Stage4.
6. **Retry-anchor preservation test.** When `reject_bucket == "post_select_conflict"` and `resolved_fix_scope` is forced to `"full"` (`stage4_reject_runtime.py:1507-1545`), assert that the next round's writer prompt still contains the IFC packet's `carryover_cliffhanger`/`carryover_location`/`carryover_time_marker` and the ACP packet's `non_regression_anchors`. Today the runtime advisory and fix_pack may be blanked at full scope; whether the IFC/ACP prefix survives depends on how `stage4_context_builder.build_round_context` is called per round, which T06 should confirm.
7. **Tier 0.5 promotion test.** Add a test that, when `validation/continuity_validator.py` returns `passed=False, severity=BLOCKING` for `prev_hud_missing` or `weapon_reset` or `injury_continuity` violations, the result is escalated into the Director's reject signal rather than appended as a warning. Today the loop folds it into `warnings` only.

## Dependencies On Other Terminals

- T01 (current-run forensics): confirm the actual `reject_reason` and `verdict_reason` strings persisted for ep4–ep9 attempts so this terminal's claim that DCV is the sole `POST_SELECT_CONFLICT` source can be checked against the live attempt rows.
- T02 (post-select route): confirm that no additional path emits `[Continuity Conflict]` or `[V67] History Conflict` outside `stage4_postselect_runtime.py:480-542`, and confirm whether `_bucket_to_category` is the only mapping that produces `POST_SELECT_CONFLICT` strings on disk.
- T03 (Stage3↔Stage4 handoff): confirm whether `arc_data`, `accepted_blueprint`, and `prev_manuscript_ending` are correctly populated when `build_authoritative_continuity_projection` runs at the Stage4 site (`stage4_context_builder.py:2292-2300`). If any of these are empty or wrong, ACP enters Stage4 hollow regardless of the wiring.
- T05 (memory/cache side effects): the `MANUSCRIPT_HISTORY_CONFLICT_PROMPT` accepts `manuscript_history` as text; this terminal could not confirm whether that text is ever served from a stale or rejected-attempt source. T05 should pinpoint whether the cache keyed in `_get_or_create_context_cache` ever contains rejected manuscripts.
- T06 (retry hydration / replay): confirm whether IFC/ACP anchors survive across retries when `resolved_fix_scope == "full"` and whether `_consecutive_empty_patches` actually reaches the IFC `should_escalate_to_rewrite` thresholds in real ep4–ep9 traces.
- T07 (context-cache lineage): confirm whether the Director cache used by `check_manuscript_continuity_with_cache` is keyed by `_context_cache_project_namespace("ep", ep_num)` only, and whether stale Stage3 blueprint state can pollute it.
- T08 (regression gap design): aligns directly with §"Regression / Test Candidates" above; any of #1–#7 should be fold-able into T08's test plan.
- T09 (artifact truth samples): confirm at the artifact level whether the four #58 bug shapes (institution naming drift, duplicated continuation beats, date drift, prior-failure replay) actually appear in ep4–ep9 candidate texts; if so, that strengthens root-cause #1 and #2 above.

## Open Questions

1. Is `continuity_canary.evaluate_continuity_canaries` intended to be a runtime tripwire or only a harness post-mortem? The combination of `write_continuity_canary_report` + `merge_continuity_canary_reports` + a strict-success gap rule in `scripts/run_auto_frontier_lag_harness.py` suggests a runtime writer was planned but never wired.
2. Is `ContinuityInspector.inspect_manuscript` intended to be retired in favor of `DirectorContinuityValidator.check_manuscript_continuity_with_cache`? If yes, the retirement should be visible in module-level comments; today both are alive in code with overlapping intent.
3. Why does `apply_continuity_pins` only run on the blueprint and not on Stage4 candidate manuscripts? The pin patterns (proper-noun, elapsed-time bucket, opening-action reversal) match the bug shapes #58 names.
4. Does the Director's continuity-conflict prompt (`MANUSCRIPT_HISTORY_CONFLICT_PROMPT`) intentionally exclude ACP `non_regression_anchors` and IFC `carryover_*`, or is that an unfilled wiring gap? The prompt template only accepts `{ep_num}`, `{manuscript_history}`, `{current_manuscript}`, `{story_context}`.
5. When `prev_hud` is missing, `validation/continuity_validator.py` returns `passed=False, severity=BLOCKING`, but the Stage4 round routes it as a warning. Is this conscious "fail-soft until HUD pipeline matures" or a forgotten downgrade?
6. Is `stage4_immutable_fact_contract.classify_violation_family`'s bias toward Korean keyword matching (lines 364-451) sufficient when the Director's `summary` text could be Japanese, English, or mixed? If a CONFLICT summary uses English terms ("scene order broke", "opening location moved"), several Korean keyword branches will miss and the family will be empty.

## Closure Recommendation

Do not close #58 from this terminal. Investigation only.

The continuity authority story splits cleanly into a **prompt path** (ACP, IFC, EpisodeStateArbiter, pin-guard, the live tier-0.5 validator) and a **verdict path** (`DirectorContinuityValidator.check_manuscript_continuity_with_cache` and `check_manuscript_history_conflicts`). The prompt path is largely wired and self-describes its authority shape correctly. The verdict path runs an LLM cache check that does not consume any of the structured carriers and is fail-closed in a way that erases retry anchors. The tripwire layer (`continuity_canary`) and the LLM anchor-aware Stage4 inspector (`ContinuityInspector.inspect_manuscript`) are both written but unwired.

Recommended downstream priorities for T10's synthesis:

- Treat #58 as a **structural authority-gap** before declaring it a content-quality bug.
- Do **not** claim 5-arc readiness while the verdict path is unstructured LLM cache and the canary is dead.
- Closure of #58 should require at least one of:
  - the `continuity_canary` runtime writer is wired (Stage4 round emits the report and either DCV or the candidate gate consumes the findings),
  - DCV is fed a structured ACP `non_regression_anchors` + IFC `carryover_*` block as additional evidence,
  - or `ContinuityInspector.inspect_manuscript` is revived as a packet-aware Stage4 checker.
- Until one of those lands, even a successful 5-arc run should be considered transport-level success, not authority-level success.
