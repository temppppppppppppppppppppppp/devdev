# T05 Memory And Cache Side Effects

Workspace: `C:\Users\wjjo\Desktop\글도비`
GitHub Issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Mode: read-only investigation. No source/doc/DB/git mutations performed beyond writing this report.
Authority note: per dispatch rules, memory and cache helpers are treated as helper telemetry. This report does not promote them into final narrative authority and does not claim 5-arc clean-run readiness.

## Scope

Audit session/vector memory and context-helper side effects that can influence future Stage4 context, with explicit separation of:

- write timing (when something becomes visible to a later Stage4 attempt) vs.
- read timing / consumption surface (how/when it actually flows into the next prompt or contract).

Files inspected (line counts, AGENTS.md UTF-8 read):

- `modules/core/session_memory_envelope.py` (237 LOC)
- `modules/core/vec_memory.py` (1384 LOC)
- `modules/core/context_advisor.py` (1158 LOC)
- `modules/core/context_compression.py` (379 LOC)
- `modules/core/narrative_context_formatter.py` (239 LOC)
- `modules/core/stage4_post_pass_runtime.py` (2025 LOC)
- `modules/core/stage4_post_processor.py` (1729 LOC)
- `modules/core/session_logger.py` (391 LOC)
- `tests/test_session_memory_envelope.py` (176 LOC)
- `tests/test_vec_memory.py` (819 LOC)
- `tests/test_memory_benchmark.py` (317 LOC)

Cross-references followed (read-only) to anchor the read-side flow:

- `modules/core/stage4_interview_round.py` for envelope build/attach/hydration call sites.
- `modules/core/stage4_context_builder.py` for vec retrieval call sites.
- `modules/core/stage4_orchestrator.py` for retry resume/hydration plumbing.
- `modules/core/stage4_retry_runtime.py` for `bounded_post_select_patch` gate logic.
- `modules/core/project_manager.py` and `modules/core/services/project_service.py` for `delete_episodes_from`/`delete_all_episodes` rollback callers.

## Commands / Evidence

The dispatch's suggested git grep was used as the discovery anchor, then narrowed to specific call sites with `Grep` (ripgrep-backed) and `Read` (UTF-8). Representative anchors below; they are not the full scan.

Vector memory write/read entry points (vec_memory.py):

- `def memorize_v20_episode(...)` — vec_memory.py:418-491. INSERT OR REPLACE into `vec_episodes`, `episode_meta`, `episode_fts`; sets `sync_status.synced=1` (or `vector_synced=1` in shared mode).
- `def retrieve_high_res_context / retrieve_multi_query_context / retrieve_hybrid_context / retrieve_npc_context` — vec_memory.py:493, 532, 648, 913. All filter `rowid < current_ep` (see lines 569, 988, 1022, 1126). No filter on `arc_no` or `session_id`.
- `def _keyword_fallback_search` — vec_memory.py:1051-1098. LIKE-keyword fallback when embedding fails. Same `ep_num < current_ep` filter (line 1079). No session/arc filter.
- `def sync_v20_drafts` — vec_memory.py:1224-1264. Globs `drafts_path/*.txt` via regex `(?:ep_)?(\d{1,5})(?:_[^.]+)?\.txt` (line 1237). Calls `memorize_v20_episode` with full file content; only fires when `force_repair=False` AND `sync_status` is unset.
- `def delete_episodes_from / delete_all_episodes` — vec_memory.py:1284-1317. Drops vec rows, episode_meta rows, episode_fts rows, AND resets sync_status for ep >= target.

Vector memory write gating in Stage4 PASS path (stage4_post_pass_runtime.py + stage4_post_processor.py):

- `Stage4PostPassRuntime._memorize_and_validate` — stage4_post_pass_runtime.py:567-651. Calls `self.ctx.memory.memorize_v20_episode(...)` at line 636.
- Caller chain: `Stage4PostProcessor._run_pass_result_post_settlement_side_effects` (line 1325) → invokes `_memorize_and_validate` (line 1349). Caller's caller is at stage4_post_processor.py:1669, gated by the prior code path returning success after `_emit_stage4_settlement_status(status="fully_settled", ...)` at line 1664.
- The `_SETTLEMENT_STATUS_FLAGS` dict (stage4_post_processor.py:24-67) shows that of seven settlement statuses, only `fully_settled` sets `fully_settled=True`. All earlier failure statuses (`artifact_contract_failed`, `primary_db_failed`, `primary_persisted_meta_failed`, `settlement_packet_failed`, `human_export_failed`) return early before `_run_pass_result_post_settlement_side_effects` is reached.
- `Stage4PostProcessor.run_post_episode_tasks` — stage4_post_processor.py:1691-1729. End-of-Stage4-session vec sync; calls `self.ctx.memory.sync_v20_drafts(drafts_path=_drafts_path)` at line 1726. `_drafts_path` resolves to `current_project.paths.drafts` (stage4_orchestrator.py:2662 confirms `paths.drafts` as the only Stage4 manuscript output dir).
- Confirmed there is no `memorize_v20_episode` call from any REJECT, partial-settle, or per-attempt code path; the only writers are these two (PASS settlement and end-of-session sync).

Session memory envelope (session_memory_envelope.py + stage4_interview_round.py):

- `build_stage4_session_memory_envelope` — session_memory_envelope.py:100-218. Reads from `advisory_flags` (which already contains `gate_semantics`, `conflict_contract`, `fix_pack`, `retry_budget_axes`, `truth_pins`, `cache_lineage`, `authoritative_continuity_projection`, `coverage_warnings`) and emits a structured envelope with `verdict_surface`, `retry_surface`, `truth_pins`, `truth_pin_items`, `carryover_refs`, `coverage_warnings`, `cache_lineage`, plus `authoritative_continuity_projection` pass-through.
- `attach_session_memory_envelope` — session_memory_envelope.py:221-231. Deep-copies advisory_flags and merges envelope under `SESSION_MEMORY_ENVELOPE_KEY`. Source advisory dict is not mutated; the new dict is returned.
- `get_session_memory_envelope` — session_memory_envelope.py:234-237. Deep copy back; mutations of the returned envelope do not bleed into the source advisory_flags (`tests/test_session_memory_envelope.py:116-127` asserts this).
- Build/attach call sites: stage4_interview_round.py:8409-8435 wraps an existing advisory dict with the envelope. Triggered from:
  - `_build_stage4_pass_rate_attempt_payload` (stage4_interview_round.py:8556-8631), which builds the per-attempt pass-rate payload regardless of success/failure (line 8580 attach unconditional).
  - `_build_stage4_db_attempt_payload` (stage4_interview_round.py:8633-…), which builds the persisted DB attempt row (line 8665 attach unconditional).
- Hydration read site: `_hydrate_stage4_previous_attempt_from_row` (stage4_interview_round.py:2189-2415) deep-copies `attempt_row.advisory_flags`, calls `get_session_memory_envelope`, then projects envelope fields (`retry_surface`, `verdict_surface`, `candidate`, `truth_pin_items`, `truth_pins`, `carryover_refs`, `coverage_warnings`, `cache_lineage`) onto the next-attempt context payload. Includes `payload["prior_attempts"] = history[-3:]` (line 2414).
- Persistent retry resume: `hydrate_persisted_stage4_previous_attempt` (stage4_interview_round.py:2417-2486). Calls `db.get_stage_attempts_for_arc(arc, stages=(4,), limit=12, session_id=...)`, filters to `same_episode_rows` AND `session_id == current_session_id` (line 2452), and only hydrates if `latest_verdict not in {"PASS", "PASS_WITH_FIX"}`. Logs `[Stage4Resume] Persisted previous attempt hydrated from stage_attempts` on hit.
- Orchestrator wiring: stage4_orchestrator.py:1795-1822. After per-round dispatch, if `loop_state.previous_attempt` is empty, the persistent hydrator is called, the hydrated payload becomes the next round's `previous_attempt`, and `director_feedback` falls back to `merged_feedback` / `rejection_reason` from the hydrated record.

Vector memory consumed by Stage4 (read side):

- `Stage4ContextBuilder._collect_stage4_retrieval_context` — stage4_context_builder.py:2350-2464. Calls `advisor.plan_stage4_retrieval(... is_reject_retry=False, ...)` at line 2388 (note hardcoded False; see Findings F5). Then runs `_execute_retrieval_plan` (line 2397). Legacy fallback path also calls `retrieve_multi_query_context` directly at line 2448.
- `Stage4ContextBuilder._execute_retrieval_plan` — stage4_context_builder.py:1547-1605. Branches on `slot.source` between `db_npc_history` (NPC search), `manuscript_db` (excerpt), `db_npc_relationship`, `static`, and default vec retrieval (`hybrid` / `dense` / `sparse` / fallback). Each branch ends with `compressor._smart_trim` to slot budget.
- `Stage4InterviewRound` flashback verifier — stage4_interview_round.py:7346-7367. For each detected flashback, calls `retrieve_high_res_context(_q, next_ep, n_results=2)` and then `fetch_manuscript_snippet(ep, max_chars=500)` for cross-reference. Filtered by `ep_num < current_ep` inside the retriever.
- Stage2 preflight and Stage3 also use the retrievers (stage2_preflight.py:291/305/323/334; stage3_orchestrator.py:2068/2081). Out of T05 primary scope but they share the same vec store.

Drafts directory writers (the only writers that feed `sync_v20_drafts`):

- `Stage4PostProcessor._write_human_facing_manuscript_export` — stage4_post_processor.py:190-200. Writes `paths.drafts/ep_{next_ep:04d}.txt`. Caller stage4_post_processor.py:1632, gated on PASS settlement (returns False on failure before reaching `_run_pass_result_post_settlement_side_effects`).
- `Stage4PostProcessor._write_emergency_manuscript_dump` — stage4_post_processor.py:159-166. Writes `output_dir/emergency_ep_{next_ep:04d}.txt`. Filename does not match the `(?:ep_)?(\d{1,5})(?:_[^.]+)?\.txt` regex used by `sync_v20_drafts` (it begins with `emergency_…` and `re.match` is anchored at the start), so emergency dumps are NOT re-embedded by sync.

session_logger surface:

- `SessionLogger` module docstring (session_logger.py:1-19) explicitly self-classifies as OPTIONAL best-effort telemetry; states authoritative truth lives in `db_manager` (`stage_attempts`, `director_selections`) and `episode_production.jsonl`; says "If JSONL files are lost, no durable pipeline truth is lost"; default `enabled=False`.
- All four log methods (`log_llm_call`, `log_decision`, `log_state_change`, `log_ui_event`) early-return when `self._enabled` is False (lines 124, 166, 192, 232).
- Stage4 invocations: stage4_post_pass_runtime.py:1626-1636 (`world_state` change) and 1668-1678 (`fact_ledger` change). Both inside the atomic-save flow, i.e., only on PASS settlement. There is no Stage4 `session_logger.log_*` call on a REJECT/POST_SELECT_CONFLICT path.

context_advisor:

- `ContextAdvisor.plan_stage4_retrieval` — context_advisor.py:513-537. Builds heuristic slots based on `arc_data`, `blueprint`, `prev_ending`, `npc_roster`, plus `is_arc_boundary` and `is_reject_retry` triggers for LLM enrichment.
- `_should_use_llm` — context_advisor.py:642-656. LLM enrichment fires on `is_arc_boundary`, `is_reject_retry`, `npc_count >= 5`, or director-low-confidence. The Stage4 retrieval site at stage4_context_builder.py:2388 hardcodes `is_reject_retry=False`, so this trigger never fires from the Stage4 mainline retrieval call (Findings F5).
- Slot budgets: `_assign_slot_budgets` (context_advisor.py:1103-1112) splits stage budget proportionally by priority (1→3, 2→2, 3→1) with floor `slot_max_chars_default` (default 1500). Stage budget defaults: `{"stage4": 50000}` (context_advisor.py:1149-1154).

context_compression:

- `ContextCompressor.compress` — context_compression.py:83-161. Pure heuristic: keeps essential fields, summarizes/trims the rest. No persistent state, no DB, no vec writes/reads.
- `_smart_trim` — context_compression.py:187-199. Used by `_execute_retrieval_plan` per-slot trim. Adds `[...중략...]` marker.

narrative_context_formatter:

- All four formatters (`format_motivations`, `format_promises`, `format_arc_scales`, `format_cumulative_time`) and `format_all` (narrative_context_formatter.py:14-239). Pure dict→string formatters. No DB, no vec writes/reads. The data they format (`active_plots`, `npc_motivations`, `pending_commitments`, `all_refined_arcs`, `cumulative_elapsed`) is sourced upstream from `WorldState`/`StateTracker`; this module is read-only with respect to those structures.

Rollback / cleanup callers (delete_episodes_from path):

- `ProjectManager.backtrack_to` — project_manager.py:1080-1108. After DB rollback, calls `memory.delete_episodes_from(target_ep)`, then `world_state.rollback_to`, then `fact_ledger.rollback_to`.
- `ProjectService.rewind_to_stage_2` — services/project_service.py:530-537. Calls `_delete_draft_files_from_episode` then `delete_episodes_from(target_ep)`.
- `ProjectService` rollback episode and reset paths — services/project_service.py:461, 627, 677. Other rewind/reset entry points.

## Findings

F1 — Vector memory write is gated on `fully_settled` PASS only. `_memorize_and_validate` (stage4_post_pass_runtime.py:567) is reached only via `_run_pass_result_post_settlement_side_effects` (stage4_post_processor.py:1325) which is only called at stage4_post_processor.py:1669, after `_emit_stage4_settlement_status(status="fully_settled", ...)` at line 1664. Every earlier failure status returns False before this side-effect block. There is no Stage4 path that writes to `vec_episodes`/`episode_meta`/`episode_fts` from a REJECT or POST_SELECT_CONFLICT outcome. A rejected manuscript cannot, by direct write, become a future-search hit through the vec store. (Authority caveat: per dispatch rule, this is helper-evidence; it does not by itself prove that no other module writes vec — see Open Questions OQ1.)

F2 — `sync_v20_drafts` is the secondary write path. `Stage4PostProcessor.run_post_episode_tasks` (stage4_post_processor.py:1691-1729) calls `sync_v20_drafts(drafts_path=paths.drafts)` at session end. The regex `(?:ep_)?(\d{1,5})(?:_[^.]+)?\.txt` (vec_memory.py:1237) is anchored at the start of the filename; `emergency_ep_*.txt` does not match. The only Stage4 writers that produce files matching the regex are `_write_human_facing_manuscript_export` (PASS-only). However the `force_repair=False` branch (vec_memory.py:1243-1251) skips episodes where `sync_status.synced/vector_synced == 1`, which is set by every successful `memorize_v20_episode` call. So in normal flow `sync_v20_drafts` is a backfill catch-up for episodes whose memorize step failed — not a redundant write. If a fresh live run reads `force_repair=True` (not observed in the Stage4 caller, but the API allows it), every `ep_*.txt` in the drafts dir is re-embedded; cross-run drift in older PASS drafts could re-enter the vec store with current-run timestamps.

F3 — Vector memory reads always filter `rowid < current_ep`, never on `session_id` and never on `arc_no` boundary. Confirmed in:

- `_knn_search` (vec_memory.py:1010-1049), filter at line 1022.
- `retrieve_multi_query_context` (vec_memory.py:532-646), filter at line 569.
- `_knn_search_raw` (vec_memory.py:955-1008), filter at line 988.
- `_fts_search` (vec_memory.py:1100-1146), filter via SQL `rowid < ?`.
- `_keyword_fallback_search` (vec_memory.py:1051-1098), SQL `ep_num < ?`.
- `_collect_npc_entity_candidates` and `_collect_npc_vector_candidates` (vec_memory.py:764-866), `ep_num < current_ep`.

This is correct for forward continuity but means: any prior PASS episode in the same project DB is reachable, including episodes from a previous run/session whose institution names, dates, and continuation beats may already be drifted. The vec store is project-DB-scoped, not session-scoped; it has no native session_id column.

F4 — `arc_no == current_arc_no` distance bonus (`× 0.9`) in `retrieve_multi_query_context` (vec_memory.py:600-606) and `_knn_search_raw` (lines 991-995) preferentially surfaces same-arc prior episodes. This is a legitimate continuity preference, but it amplifies the impact of any drift already embedded in same-arc earlier eps.

F5 — `is_reject_retry` is hardcoded False in the Stage4 mainline retrieval call. `Stage4ContextBuilder._collect_stage4_retrieval_context` calls `advisor.plan_stage4_retrieval(... is_reject_retry=False, ...)` (stage4_context_builder.py:2388). `ContextAdvisor._should_use_llm` (context_advisor.py:642-656) lists `is_reject_retry` as one of four LLM-enrichment triggers. With this hardcoded False, REJECT-retry attempts do NOT receive LLM-enriched retrieval slots even though the retry context arguably needs richer or differently-aimed retrieval to break a POST_SELECT_CONFLICT loop. This affects the SC retrieval plan only, not the legacy `retrieve_multi_query_context` fallback that runs alongside it.

F6 — Session memory envelope is unconditionally attached to every persisted Stage4 attempt, including REJECT/POST_SELECT_CONFLICT attempts. `_with_stage4_session_memory_envelope` is invoked at stage4_interview_round.py:8580 (pass-rate payload) and 8665 (DB attempt payload) with no success/verdict gate. That envelope carries `verdict_surface`, `retry_surface`, `truth_pins`, `truth_pin_items`, `carryover_refs`, `coverage_warnings`, `cache_lineage`, and the authoritative continuity projection pass-through. This is the per-attempt structured surface that flows back into the next attempt via hydration.

F7 — Persisted retry hydration is session-scoped and same-episode-scoped. `hydrate_persisted_stage4_previous_attempt` (stage4_interview_round.py:2417-2486) explicitly:

- Resolves `session_id` via `resolve_logging_session_id(current_project)` (line 2432).
- Reads `db.get_stage_attempts_for_arc(arc, stages=(4,), limit=12, session_id=session_id)` (line 2435).
- Filters in Python to `int(row.ep_num) == int(next_ep)` (line 2448-2450).
- Filters again to `row.session_id == session_id` (line 2452-2454) when `session_id` is non-empty.
- Skips if latest verdict in `{"PASS","PASS_WITH_FIX"}` (line 2460).

So cross-session hydration is structurally blocked by the session_id filter, and same-session same-episode prior REJECTs are the intended hydration source. If `session_id` resolves to empty (e.g., logging not initialized or a project that bypasses logging), the second filter is skipped and DB-side filter alone gates — `db.get_stage_attempts_for_arc(... session_id=session_id)` would receive empty session_id; behavior depends on the DB-layer interpretation of empty session_id, which is out of T05's primary file scope but is a soft seam (Open Questions OQ2).

F8 — Vector memory deletion on rewind/rollback is correctly wired but only fires on explicit user-initiated paths. `delete_episodes_from` is invoked at:

- `ProjectManager.backtrack_to` — project_manager.py:1089-1094.
- `ProjectService.rewind_to_stage_2` — services/project_service.py:534-537.
- `ProjectService.rollback_episode` — services/project_service.py:627-628.
- `ProjectService` reset operations — services/project_service.py:461, 677.

There is no automatic deletion path triggered by a 5-arc run that detects POST_SELECT_CONFLICT drift in earlier episodes. The vec store carries forward whatever was embedded in PASS settlements of the current and any prior run on the same project DB.

F9 — `cache_lineage` is an opaque pass-through in the envelope. `build_stage4_session_memory_envelope` simply assigns `_as_dict(advisory.get("cache_lineage"))` (session_memory_envelope.py:217). `_hydrate_stage4_previous_attempt_from_row` projects `dict(envelope.get("cache_lineage") or {})` onto the next-attempt payload (stage4_interview_round.py:2381). T05 did not find any branch inside session_memory_envelope.py / vec_memory.py / context_advisor.py / context_compression.py / narrative_context_formatter.py / stage4_post_pass_runtime.py / stage4_post_processor.py / session_logger.py that validates cache_lineage freshness or invalidates a stale Vertex cache reference. T07 owns the context-cache lineage authority and should treat cache_lineage as a surface that can carry forward without local guard from the memory layer.

F10 — `session_logger` is structurally non-authoritative for verdict adjudication. The module docstring (session_logger.py:1-19) explicitly states `enabled=False` by default and that authoritative truth lives in DB tables. All four log methods short-circuit on disabled. Stage4 uses session_logger only on the PASS atomic-save path (stage4_post_pass_runtime.py:1626 and 1668). Even if enabled, this is best-effort telemetry; it cannot influence Stage4 retry decisions because Stage4 read paths do not consume session JSONL files.

F11 — `narrative_context_formatter` and `context_compression` are pure helpers. They have no DB read/write, no vec read/write, no global mutable state. They cannot inject stale or rejected content; they only re-shape data passed in by the caller. Drift therefore must enter via the caller's input data (e.g., active_plots/pending_commitments dict from WorldState/StateTracker), which is out of T05's primary scope and overlaps T04 (continuity authorities) and T03 (Stage3→Stage4 handoff).

F12 — Embedding LRU cache is per-VecMemory instance and content-keyed. `_embed_cache` (vec_memory.py:79-81) is OrderedDict, max 512 entries, MD5(text) key. `_embed_cache_put` (vec_memory.py:361-370) updates existing keys in place (`[TF-30-3]` comment), preventing stale-vector-on-model-change at the cache layer; but vectors already inside `vec_episodes` are migrated only when `_check_embedding_version` detects a dim mismatch (vec_memory.py:262-293). A model-name change WITHOUT a dim change emits a warning and clears the embed cache but does NOT re-embed existing rows. So a long-lived project DB can carry vectors from an older embedding model alongside new ones, which can produce silently degraded similarity hits — relevant for cross-run drift recurrence in carryover families (e.g., institution names repeatedly retrieved by same-arc bonus).

F13 — `episode_meta.entity_names` is hard-truncated at 1000 chars, `event_types` at 500 chars, `causal_data` at 2000 chars (vec_memory.py:449-457). The truncation is applied at memorize time. NPC matching in `_collect_npc_entity_candidates` (vec_memory.py:764-808) and FTS5 search depend on what survived this truncation. For a high-NPC episode, late-listed NPCs are silently absent from FTS hits; vec recall then falls back to dense KNN only. This is a secondary risk for NPC-ID drift — not specifically POST_SELECT_CONFLICT — but it shapes the realistic recall ceiling of the helper.

## Root-Cause Candidates

Per dispatch rules, T05 must not promote helper evidence into final narrative authority. The following are candidates, not conclusions; final authority rests on T01-T04 and T07 evidence and on Director judgment.

R1 (LIKELY HELPER, NOT PRIMARY) — Vector store retrieving same-arc earlier-episode content with `arc_no == current_arc_no` ×0.9 distance bonus. Because the only writes are gated on `fully_settled` PASS, the content reached through retrieval is by construction a PASS-state record. If a prior PASS episode's settled state itself contained the eventual conflict (e.g., institution name fixed at value X, but a later Director truth_pin says canonical is Y), the helper amplifies the drift it inherited from the upstream Stage3 source / continuity authority — it does not invent it. POST_SELECT_CONFLICT during ep4-ep9 is consistent with same-arc PASS records reinforcing a value that contradicts the truth_pin contract surfaced by the post-select gate. T04 owns whether the truth_pin canonical is correct; T03 owns whether Stage3 introduced the drift; T05's contribution is: the vec helper structurally cannot self-correct without a `delete_episodes_from` / re-memorize cycle, which is not on the Stage4 mainline.

R2 (HELPER WITH SOFT SEAM) — Persisted previous-attempt hydration carries the rejected attempt's `truth_pins`, `truth_pin_items`, `conflict_contract`, and `cache_lineage` into the next attempt. This is intentional for retry feedback (the next Director needs to know what was rejected and why). But the `bounded_post_select_patch` gate (stage4_retry_runtime.py:144-208) relies on the previous attempt's `conflict_contract.truth_pins`, `contradiction_types`, and `rewrite_required_reasons` being correctly populated. If POST_SELECT_CONFLICT classification at the source emits a sparse or under-populated contract, the gate may permit a bounded patch retry where a full rewrite is warranted, leading to repeat POST_SELECT_CONFLICT on the same family. T02 owns the post-select classifier; T05's note is that the envelope is faithful to its input — a sparse input produces a sparse hydration.

R3 (HELPER, OUT OF T05 PRIMARY AUTHORITY) — `cache_lineage` is opaque pass-through. Its freshness is not validated by anything inspected in T05 scope. T07 should determine whether stale Vertex cache references can be carried forward via the envelope.

R4 (HELPER, LOWER LIKELIHOOD) — `is_reject_retry=False` hardcoded in `Stage4ContextBuilder._collect_stage4_retrieval_context` means the SC retrieval plan never gets LLM enrichment on a retry. This is unlikely the root of POST_SELECT_CONFLICT drift but it does narrow the helper's ability to surface different/better historical anchors specifically when the prior attempt failed. A retry-aware retrieval plan could increase recall on the conflict family.

R5 (HELPER, LOWER LIKELIHOOD) — Drafts→vec backfill via `sync_v20_drafts(force_repair=False)` is normally a no-op for already-synced eps. If any non-Stage4 caller invokes `sync_v20_drafts(force_repair=True)` (T05 did not find one in scope), the entire drafts dir would be re-embedded in current order, potentially overwriting same-rowid vectors with newer-content embeddings. This is a contained risk and not a known active path.

## Regression / Test Candidates

T08 owns regression design. T05 contributes proposed shapes only; do not implement.

RT1 — `test_memorize_skipped_on_reject_settlement` (target: stage4_post_processor.py + stage4_post_pass_runtime.py). Drive a Stage4 PASS path through every settlement-status branch except `fully_settled`; assert `ctx.memory.memorize_v20_episode` is never called. Useful to lock in F1 against future refactors.

RT2 — `test_session_memory_envelope_passes_through_truth_pin_items_on_reject` (target: session_memory_envelope.py). Build envelope with `success=False`, `verdict="REJECT"`, `reject_bucket="post_select_conflict"`, and a populated `conflict_contract.truth_pins` list; assert envelope's `truth_pin_items` and `truth_pins` are the union of `advisory.truth_pins`, `gate_semantics.truth_pins`, and `conflict_contract.truth_pins`, deduplicated by `(pin_key, family, expected, observed)`. The current `test_build_stage4_session_memory_envelope_preserves_structured_truth_pin_items` is a partial cover; expand to assert dedup behavior and to assert that `coverage_warnings` and `cache_lineage` survive.

RT3 — `test_persisted_previous_attempt_hydration_blocks_cross_session_post_select_conflict` (target: stage4_interview_round.py `hydrate_persisted_stage4_previous_attempt`). Insert two stage_attempts rows for same ep with different `session_id` values, both REJECT/post_select_conflict; resolve current session to `sess-A`; assert hydrator returns only `sess-A` content. Then repeat with empty `session_id`; assert hydrator behavior is documented (see Open Questions OQ2). Useful to lock the structural session-scope guarantee.

RT4 — `test_vec_retrieve_excludes_current_and_future_eps` (target: vec_memory.py). For every public retrieval method (`retrieve_high_res_context`, `retrieve_multi_query_context`, `retrieve_hybrid_context`, `retrieve_npc_context`, `_keyword_fallback_search`), assert that an episode rowid >= current_ep cannot appear in the result, even when fingerprinted to be the closest match. Existing tests cover several but not all retrievers in this regression family.

RT5 — `test_arc_bonus_does_not_overweight_drifted_prior_pass` (target: vec_memory.py KNN paths, behavioural). Insert two prior PASS eps where same-arc ep-N-1 has institution name "대현그룹" and a different-arc earlier ep has "대한그룹"; query embedding aligned to "대한그룹"; assert that with `current_arc_no` set, the retrieval still surfaces the canonical "대한그룹" anchor when truth_pin canon is "대한그룹". This is a sanity floor test for the ×0.9 bonus.

RT6 — `test_sync_v20_drafts_skips_emergency_dump_filenames` (target: vec_memory.py:sync_v20_drafts). Place `emergency_ep_0009.txt` and `ep_0009.txt` in the drafts dir; assert only `ep_0009.txt` is memorized.

RT7 — `test_session_logger_disabled_drops_all_writes` (target: session_logger.py). Existing tests likely cover; ensure default `enabled=False` and assert `log_decision`, `log_state_change`, `log_llm_call`, `log_ui_event` write nothing.

## Dependencies On Other Terminals

- T01 (current-run forensics): needs concrete attempt rows and artifact paths for ep4-ep9 to validate that the rejected-attempt envelopes actually contained populated `truth_pins`/`conflict_contract` (to bound R2).
- T02 (post-select conflict route): owns whether POST_SELECT_CONFLICT classification produces complete contract payloads. Without that, R2's "sparse hydration" claim cannot be confirmed or denied.
- T03 (Stage3→Stage4 handoff): owns whether the upstream context that fed into the first PASS for an arc was already drifted, which is the primary path that R1 amplifies.
- T04 (continuity authority carriers): owns whether the truth_pin canonical is the correct authority that Stage4 should be defending. T05's R1 depends on T04's verdict.
- T06 (retry hydration replay): overlaps directly. T05 covered the envelope and the persisted hydration session-scope guard; T06 owns the broader same-session prior-failure replay surface and should consume RT3 and RT2.
- T07 (context-cache lineage): owns `cache_lineage` freshness and stale-cache suppression. T05 explicitly does not promote `cache_lineage` to authority; T07 should treat F9 as input.
- T08 (regression gap design): owns final test list. T05 supplied RT1-RT7 as proposals only.
- T09 (artifact truth samples): can confirm whether ep4-ep9 PASS settlements produced drafts/ep_NNNN.txt files whose embedded content matches the eventual rejected-attempt institution-name claim — a triangulation of R1.

## Open Questions

OQ1 — Are there any vec writers outside the eight files in T05 scope? T05 grep on `memorize_v20_episode|delete_episodes_from|sync_v20|save_v20_anchor|load_v20_anchor` returned only the call sites listed under F1/F2/F8 within `modules/`. A wider sweep (all `modules/`, `scripts/`, `tools/`) is outside T05's primary file set and should be confirmed by T01 or T07 if R1 is escalated.

OQ2 — `hydrate_persisted_stage4_previous_attempt` second-stage `session_id` filter is skipped when `session_id` resolves empty (stage4_interview_round.py:2451). The DB-layer behavior of `db.get_stage_attempts_for_arc(... session_id="")` is outside T05 file scope. Does it return all sessions, no rows, or current-session-only? Important because if it returns all sessions, an empty-session-id project could hydrate cross-session prior REJECTs.

OQ3 — `sync_v20_drafts` is called at session end (T05 confirmed) — does any other Stage4 path call `sync_v20_drafts(force_repair=True)` on resume? T05 did not find one in scope.

OQ4 — When `_check_embedding_version` detects a model-name mismatch (vec_memory.py:275-280), it clears the embed cache but does not migrate existing vectors. Is there any explicit re-embed-on-model-change job? Not found in T05 scope.

OQ5 — Are there any read paths where `episode_meta.entity_names` or `event_types` truncation (F13) materially affects POST_SELECT_CONFLICT family detection (institution names tend to be short tokens, so unlikely; relationship/role labels can be longer). Empirical answer requires a sample from T01/T09.

OQ6 — Stage4ContextBuilder hardcodes `is_reject_retry=False` (F5). Is this an oversight (should pass the retry flag from `loop_state.previous_attempt`) or a deliberate decision? T05 found no comment justifying it.

## Closure Recommendation

T05 closure recommendation: not the primary root-cause family for #58 POST_SELECT_CONFLICT carryover drift. The vec write surface is structurally PASS-only, the read surface filters future eps, and the persisted retry hydration is session-scoped and same-episode-scoped. The session_logger is non-authoritative by design and gated on opt-in. The session memory envelope and persisted hydration faithfully transport whatever the post-select classifier and continuity authority emit; they amplify upstream drift but do not generate it.

The most plausible memory-side contribution is helper amplification (F4, R1): same-arc PASS records being preferred during retrieval can reinforce a value that the truth_pin contract later rejects, producing repeat POST_SELECT_CONFLICT on consecutive eps in the same arc until either (a) a `fully_settled` PASS replaces the drifted vector via INSERT OR REPLACE on the same rowid, or (b) `delete_episodes_from` is manually invoked. Neither happens automatically inside a 5-arc run on the Stage4 mainline.

Recommended next steps for the dispatch coordinator (advisory, Director-decided):

1. T05 evidence (specifically R1 amplification + R2 envelope faithfulness) should be merged with T02 (classifier) and T04 (continuity authority canonical) before any vec-side mitigation is proposed. A premature "clear vec on retry" mitigation would lose legitimate continuity context.
2. T07 should treat F9 (`cache_lineage` opaque pass-through) as input to its lineage audit. T05 explicitly does not validate cache freshness.
3. RT1-RT7 should be considered by T08 only after T01-T04 settle the primary cause family; tightening tests on a helper can mask an unfixed source-side defect.
4. Do not promote any vec/session-memory mitigation as a fix for #58 on T05 evidence alone. Director authority required.

3-pass self-audit (light, in-document, per AGENTS.md document-save rule):

- Pass 1 — structure: schema matches dispatch-required fields. Each of Findings/Roots/Tests/Deps/OQ/Closure has content.
- Pass 2 — evidence: every F-claim cites a specific file path and line range; every command anchor is reproducible.
- Pass 3 — authority discipline: T05 does not declare a root cause, does not promote helper evidence into authority, does not claim 5-arc readiness, and explicitly defers to T01-T04 and Director.

Estimated investigator confidence on the F1-F13 facts (within T05 file scope): ~92%. Estimated confidence on R1-R5 root-cause family classification: not enough to claim 95%, hence "candidates" not "conclusions".
