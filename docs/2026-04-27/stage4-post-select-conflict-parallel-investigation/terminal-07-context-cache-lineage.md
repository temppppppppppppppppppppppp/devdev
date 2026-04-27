# T07 Context-Cache Lineage

Date: 2026-04-27
Track: System order — read-only investigation
Issue: #58 [Stage4] Reduce POST_SELECT_CONFLICT carryover drift in 5-arc runs
Terminal: T07 — context-cache lineage and stale-source suppression

## Scope

Audit whether cached prompt/context content can bypass updated lineage after Stage2/Stage3/Stage4 state changes, and whether the cache layer can reintroduce stale institution names, old dates, or old continuation beats into Stage4 prompts during 5-arc runs that exhibit POST_SELECT_CONFLICT carryover drift.

In-scope files (all confirmed tracked by `git ls-files`):

- `modules/domain/agents/base_agent.py` (cache key, lineage gate, `_ask_with_cached_context`, `_get_or_create_context_cache`)
- `modules/domain/agents/director_caching.py` (Director-level manuscript cache)
- `modules/core/stage0_handoff.py` (`build_plot_roadmap_lineage`, `cached_arcs_source_lineage_matches`)
- `modules/core/stage4_context_packets.py` (Tier1/Tier2 context assembly, lineage probe)
- `modules/core/stage4_context_builder.py` (mandatory_context, retrieval, prompt bases)
- `modules/core/stage3_orchestrator.py` (treatment block injection, lineage probe)
- `modules/core/stage2_orchestrator.py` (`_stage2_cached_arcs_lineage_ready`, cumulative_state_cache reset)
- `tests/test_base_agent.py` (lineage success/failure/missing/stale_model coverage)
- `tests/test_audit_stage34_cache_gate_corpus.py`, `tests/test_audit_stage34_cache_proof.py`
- `scripts/audit_stage34_cache_gate_corpus.py`, `scripts/audit_stage34_cache_proof.py`

Out-of-scope (read-only mode):
- Editing source, docs (other than this report), DBs, GitHub state, or git history.

## Commands / Evidence

```text
$ git ls-files modules/domain/agents/base_agent.py modules/domain/agents/director_caching.py \
    modules/core/stage0_handoff.py modules/core/stage4_context_packets.py \
    modules/core/stage4_context_builder.py modules/core/stage3_orchestrator.py \
    modules/core/stage2_orchestrator.py tests/test_base_agent.py \
    tests/test_audit_stage34_cache_gate_corpus.py tests/test_audit_stage34_cache_proof.py \
    scripts/audit_stage34_cache_gate_corpus.py scripts/audit_stage34_cache_proof.py
→ all 12 paths tracked.

$ wc -l (above set)
→ base_agent.py 2870 / director_caching.py 183 / stage0_handoff.py 744
  stage4_context_packets.py 823 / stage4_context_builder.py 3428
  stage3_orchestrator.py 4552 / stage2_orchestrator.py 1862
  tests/test_base_agent.py 1507 / tests/test_audit_*_corpus 508 / proof 356
  scripts audit_*_corpus 708 / proof 563
```

Key code anchors collected:

- `base_agent.py:109-173` — `_sanitize_context_cache_token`, `_context_cache_provider_token`, `_build_context_cache_key`, and the **lineage gate** `_context_cache_lineage_bypass_reason`. The gate covers four signals only: `cache_key`, `content_hash`, `model`, `provider`. There is **no episode, arc, run-id, or stage-state component** in the lineage record.
- `base_agent.py:2391-2424` — `_context_caches` class dict (cache_key → {name, created_at, content_hash, model, provider}); `_evict_context_cache_by_name` only evicts on cached-context API failure or explicit name match.
- `base_agent.py:2426-2592` — `_get_or_create_context_cache`: hashes the content (`md5[:16]` truncated), enforces `_MIN_CACHE_CONTENT` (50_000 chars from `system.yaml.cache.min_content_chars`), reuses by `created_at + ttl_seconds`. **No upstream lineage signal is mixed into `content_hash`** (e.g. plot_roadmap fingerprint, arc_no, ep_num are absent).
- `base_agent.py:2630-2810` — `_ask_with_cached_context`: hard-bypasses the cache when `_context_cache_lineage_bypass_reason` returns non-empty, and on RuntimeError/Exception evicts the cache by name then falls back to `ask()`. Lineage check covers `missing_lineage`, `stale_model_lineage`, `stale_provider_lineage` only.
- `base_agent.py:285-298` — `refresh_runtime_provider_state` clears `_context_caches` on key/auth rotation.
- `director_caching.py:68-165` — `DirectorCachingManager.create_manuscript_cache`: builds a single Gemini cache from compiled prior-episode manuscripts; **reuse predicate is count-only**: `if self.manuscript_cache_name and self._cached_manuscript_count == len(manuscripts_compiled): return self.manuscript_cache_name` (L130). No content_hash, no provider token, no model token, no episode-set fingerprint, no plot_roadmap lineage gate.
- `director.py:110-118` — `Director.invalidate_caches` exists but has **no callers** in `modules/` or `scripts/` (verified via `grep -rn "invalidate_caches\(\)"` — empty). The cache survives rollback / POST_SELECT_CONFLICT retries unless TTL expires or count changes.
- `director_continuity.py:759-801` — `check_manuscript_history_with_cache` passes `cached_content=self._d._caching.manuscript_cache_name` directly to `generate_content_via_router`, bypassing the lineage gate from `_ask_with_cached_context` entirely. The fast-path `if not self._d._caching.manuscript_cache_name: return PASS` makes the audit silently degrade if the cache is missing or stale.
- `director_continuity.py:880-1085` — `check_blueprint_continuity_with_cache` and `check_manuscript_continuity_with_cache` use `_get_or_create_context_cache(... project_name=self._d._context_cache_project_namespace("ep", ep_num) ...)` so the cache is namespaced by `work_id+ep`. **However**, both methods short-circuit a refetch with an instance flag (`_cached_manuscript_ep != ep_num`); when ep_num is unchanged but the upstream Stage 3 selection or arc state changed, the existing `recent_manuscripts` snapshot is reused without checking content_hash freshness against the DB.
- `chief_writer.py:667-686, 1178-1203` — `_get_or_create_context_cache(cache_type="manuscript", content=common_context, ttl_seconds=600, project_name=ep:N)` and `_request_single_candidate_response` route the call through `_ask_with_cached_context(... full_prompt_fallback=full_prompt)`. Cache is content-hash-keyed and re-created when `common_context` differs.
- `chief_writer.py:2506-2542` — local `_manuscript_cache` (DB readback memo for prior eps) is gated only by `_cache_ep_num`. `invalidate_manuscript_cache()` exists but has **no callers** (`grep -rn invalidate_manuscript_cache modules/ scripts/` returns only the definition). Rollback / `db.reset_after` paths in `project_service.py` and `project_manager.py` do not invoke it.
- `stage0_handoff.py:23-355` — `PLOT_ROADMAP_LINEAGE_SCHEMA="stage0.plot_roadmap_lineage.v1"`, `PLOT_ROADMAP_LINEAGE_ANCHOR="stage2_arcs_source_lineage"`. `build_plot_roadmap_lineage(roadmap)` only fingerprints `normalize_treatment_blocks(roadmap)` — i.e. the **raw treatment blocks**, not the post-Stage2/Stage3 refined arcs that carry `state_changes`, selected blueprints, or blueprint-derived continuation beats.
- `stage2_orchestrator.py:315-344, 405-406, 485-486, 705-720` — Stage 2 saves `stage2_arcs_source_lineage` once (or refuses to proceed). On retry it resets `cumulative_state_cache=None`, `cumulative_state_cache_key=None`, and invokes `state_extractor.invalidate_cache(global_arc_no)` only when present. The `manuscript_cache_name` and `_get_or_create_context_cache` registry are not touched here.
- `stage3_orchestrator.py:2110-2180` — `_inject_stage3_treatment_block_context` calls `cached_arcs_source_lineage_matches(_project, cached_arcs=_cached_arcs, roadmap=_plot_roadmap)`. If the fingerprint matches it injects raw block fields (title, emotional_beat, foreshadow, content.context, genre_ext) into the Stage 3 prompt. The same lineage check is **not** sensitive to refined-arc state_changes drift.
- `stage4_context_packets.py:625-658` — same `cached_arcs_source_lineage_matches` probe. On lineage mismatch it skips Treatment genre_ext injection only; the rest of the Stage 4 packet (state_tracker auxiliary, foreshadow, semantic guard, lookback, manuscript_history, fact_ledger, world_state, numeric carryover) is built unconditionally from `owner.ctx.current_project.arcs[arc_idx]` and DB tables.
- `stage4_context_builder.py:96-1284, 1611-1700, 1840-1937` — chain-link carryover (cliffhanger, pending_actions, location, time_marker) and numeric carryover blocks read from `arc_data.state_changes` and `fact_ledger`. There is no fingerprint that ties the resulting `common_context` back to a Stage 0 / Stage 2 lineage anchor so a downstream auditor cannot detect that the carryover was computed from a stale arc revision.
- `stage4_context_builder.py:2764` — comment confirms reliance on `DBManager._cumulative_bible_cache`, an LRU keyed by `up_to_ep`. `db_manager.py:697-700, 924-926, 2011-2014` invalidate it on episode_bibles writes and `reset_after`. POST_SELECT_CONFLICT does **not** call any of these write paths, so an in-memory cumulative bible captured before a re-selection is not invalidated by the post-select retry alone.
- `tests/test_base_agent.py:994-1093` — covers the four lineage outcomes only: lineage-success logging, failure-eviction, missing_lineage bypass, stale_model_lineage bypass. There is no test for `stale_provider_lineage`, no test that institutional names / dates / continuation beats survive a content_hash-stable rebuild, and no test against Director.create_manuscript_cache count-based reuse.
- `tests/test_audit_stage34_cache_gate_corpus.py:132-end` and `tests/test_audit_stage34_cache_proof.py:153-357` — verify aggregate cached_tokens proof and prompt-char vs gate accounting only. They do not test stale-source suppression.

## Findings

F1. **Lineage gate is provider/model-only, not content-source-aware.** `_context_cache_lineage_bypass_reason` (base_agent.py:161-173) accepts the cache as long as cache_key, content_hash, model, and provider all match. There is no arc lineage, plot_roadmap fingerprint, ep_num, or selected-blueprint hash in the record. As a result, two Stage 4 attempts that produce **identical `common_context` bytes from different upstream selections** would hit the same cache and re-feed prior content even if Stage 3 has just chosen a different blueprint (content_hash diverges in practice, but the gate has no defense if content_hash collides or if upstream state flips back to a previously cached snapshot).

F2. **Director-owned manuscript cache reuses on count alone.** `DirectorCachingManager.create_manuscript_cache` returns the existing `manuscript_cache_name` whenever `_cached_manuscript_count == len(manuscripts_compiled)` (director_caching.py:130-132). It does **not** verify content_hash, model, provider, or work_id parity. Because `Director.invalidate_caches()` has no callers (`grep -rn "invalidate_caches\(\)" modules/ scripts/` empty), a POST_SELECT_CONFLICT retry that does not change the *count* of prior episodes — for example, a same-ep retry where Stage 3 selected a different blueprint after Stage 4 emitted a conflict — will silently reuse the cache. Any institution names, dates, or continuation beats embedded in that compiled manuscript text remain authoritative for the next history-conflict probe.

F3. **`check_manuscript_history_with_cache` bypasses the lineage gate.** `director_continuity.py:791-801` calls the Gemini API with `config.cached_content=self._d._caching.manuscript_cache_name` directly through `generate_content_via_router`, **not** through `_ask_with_cached_context`. The four-signal lineage gate (F1) and the eviction-on-failure logic (`_evict_context_cache_by_name`) are therefore **only enforced on chief_writer / blueprint_ensemble / Director-continuity ep-namespaced caches**, not on the Director-global manuscript cache. This is the same cache that decides whether a continuation beat is "in history" and therefore whether the post-select check fires.

F4. **`cached_arcs_source_lineage_matches` only fingerprints raw treatment blocks.** `build_plot_roadmap_lineage` (stage0_handoff.py:311-321) hashes `normalize_treatment_blocks(roadmap)` — i.e. the Stage 0 / Stage 2 *source* shape. Stage 3 selected blueprints, Stage 2 refined `state_changes`, and Stage 4 chain-link carryover are not in the fingerprint. Stage 3 and Stage 4 use this probe only to gate two narrow injections (treatment block context, genre_ext); the rest of the Stage 4 packet — chain-link carryover, fact_ledger numeric carryover, manuscript history, world_state, foreshadow — is rebuilt unconditionally and can carry stale arc revisions even when the lineage probe passes.

F5. **No invalidation hook from rollback / reset_after to Director or chief_writer caches.** `db_manager.reset_after` only invalidates `_cumulative_bible_cache` (db_manager.py:2011-2014). `project_service.py` / `project_manager.py` invoke `reset_after` but do not call `Director.invalidate_caches()` or `chief_writer.invalidate_manuscript_cache()`. After an arc-level rollback, `chief_writer._manuscript_cache` (memo of prior-ep manuscripts) and `Director._caching.manuscript_cache_name` (compiled prior-ep cache) can still hold pre-rollback content.

F6. **`_cached_manuscript_ep == ep_num` instance shortcut skips DB refetch.** In `director_continuity.py:1000-1016`, when ep_num is unchanged, `recent_manuscripts` is **not** refetched and the cache name is reused with the previously cached `_cached_context_text_manuscript`. POST_SELECT_CONFLICT retries inside the same ep_num therefore probe history against a context_text that was assembled **before** the post-select retry began. If a new manuscript was committed for the prior ep mid-run (e.g. parallel arc work or a separate Stage 4 attempt), the freshness signal never reaches the conflict check.

F7. **`min_content_chars=50_000` gate hides Stage 3 from cache (intended) but enlarges Stage 4 reuse window.** `system.yaml.cache.min_content_chars` (50_000 chars) means short prompts skip caching outright. Stage 4 `common_context` typically exceeds this gate (audit corpus uses 62k/88k examples), so Stage 4 producer caches are the dominant surface for stale-source suppression. The `audit_stage34_cache_proof.py` script proves cache *use*, but does not prove cache *freshness* against the upstream lineage.

F8. **Test coverage stops at the four lineage outcomes.** `tests/test_base_agent.py:994-1093` covers success / failure-with-eviction / missing_lineage / stale_model_lineage. There is no coverage for `stale_provider_lineage`, no coverage for the Director-global manuscript-cache count-only reuse, and no end-to-end coverage that mutates upstream Stage 2 / Stage 3 state and asserts the Stage 4 cached path detects the drift.

F9. **Stage 0 plot_roadmap lineage anchor is single-write.** `_save_stage2_arcs_source_lineage` (stage2_orchestrator.py:315-323) writes `stage2_arcs_source_lineage` only when `saved_lineage` is empty (L340-343). A subsequent Stage 0 / Stage 2 rebuild (e.g. mid-run treatment patch) writes a fresh fingerprint, but the chief_writer / Director caches are not subscribed to that anchor — they have no callback, no invalidate hook, no lineage record from this anchor in their cache key tuple.

## Root-Cause Candidates

R1. (most likely contributor to POST_SELECT_CONFLICT carryover) **Director-global manuscript cache count-only reuse + no rollback hook (F2 + F5 + F3).** When Stage 3 reselects after a Stage 4 conflict and the prior-ep count is unchanged, `_caching.manuscript_cache_name` keeps pointing at a Gemini cache built from manuscripts that include the *previous* round's continuation beats / institution names. The next `check_manuscript_history_with_cache` runs against this stale cache and either fails to flag the genuine new-vs-old conflict or carries old institution/date references back into the prompt that conditions the continuation beat.

R2. **Stage 4 chain-link carryover not rebound to lineage (F4 + F6).** Even when chief_writer's `common_context` cache is rebuilt (content_hash differs), the upstream `arc_data.state_changes` and `recent_manuscripts` snapshot used to derive carryover_cliffhanger / carryover_location / carryover_time_marker can be the pre-reselection version. The new chief_writer cache is technically fresh by content_hash, but it is fresh of *stale upstream content* — the lineage gate cannot detect this because it does not have a Stage 2 / Stage 3 fingerprint to compare against.

R3. **Cumulative bible / state caches not invalidated on POST_SELECT_CONFLICT (F5).** `_cumulative_bible_cache` is invalidated on `episode_bible` writes and `reset_after` only. POST_SELECT_CONFLICT typically does not write a new episode bible (the conflict is detected before commit). The cumulative bible cache used by Stage 4 numeric carryover and dead-NPC checks therefore reflects pre-reselection state across the retry.

R4. **`stale_provider_lineage` only fires on provider mode flip (F1 + F8).** Within a single run the provider/model are usually constant, so stage4_context_builder's reliance on `_ask_with_cached_context` only catches the rarest divergence cases. The bypass reason actually exercised in 5-arc runs is almost always `missing_lineage` or none — so the gate is mostly ornamental against carryover drift.

## Regression / Test Candidates

T-R1. **Director-global manuscript cache content-hash test.** Add a unit test that constructs `DirectorCachingManager`, calls `create_manuscript_cache` for ep=N with manuscripts {A,B,C}, mutates manuscript C content in the supplied `db_manager`, and calls `create_manuscript_cache` again with same count. Assert the second call should rebuild (or at minimum log a content drift) instead of returning the cached name. Today the second call short-circuits on count alone (director_caching.py:130-132).

T-R2. **POST_SELECT_CONFLICT cache-staleness regression.** Wire a stage4 integration test (or scripted scenario) that:
1. Runs Stage 4 for ep=N with blueprint B1 → records `manuscript_cache_name`.
2. Forces a POST_SELECT_CONFLICT retry that selects blueprint B2 for the same ep.
3. Asserts `chief_writer._manuscript_cache`, `Director._caching.manuscript_cache_name`, and `_context_caches[ep]` are either all rebuilt or explicitly logged as preserved with a lineage justification.

T-R3. **`stale_provider_lineage` coverage gap.** Add a `test_cached_context_stale_provider_lineage_bypasses_cache` mirror of the existing `test_cached_context_stale_model_lineage_bypasses_cache` (test_base_agent.py:1068-1092) — currently absent.

T-R4. **Stage 0 lineage drift propagation test.** When `stage2_arcs_source_lineage` anchor changes mid-run, assert that `_context_caches`, `Director._caching.manuscript_cache_name`, and `chief_writer._manuscript_cache` are evicted. Today there is no subscriber.

T-R5. **`audit_stage34_cache_gate_corpus` extension.** Extend the corpus auditor to surface cache_outcome=`bypassed` reason counts (already persisted via `_log_context_cache_lineage_bypass`) and to flag runs where `bypassed/missing_lineage > 0` — these are likely candidates for stale-source carryover; the current auditor only checks aggregate cached_tokens proof.

T-R6. **chief_writer / Director invalidation-on-rollback contract.** Add a regression that calls `db.reset_after(target_ep)` and asserts `chief_writer.invalidate_manuscript_cache` and `Director.invalidate_caches` were called (or the dead-code methods are removed and the contract is documented).

## Dependencies On Other Terminals

D1. **T01–T06 selection / Stage 3 reselection terminal**: confirm whether POST_SELECT_CONFLICT in 5-arc runs typically triggers a same-ep Stage 3 reselection that preserves the count of prior-ep manuscripts. If yes, R1 (Director count-only reuse) is the dominant suspect; if no (re-runs always advance ep_num), R2 / R3 take precedence.

D2. **Stage 2 refined-arc terminal**: need a sample of `state_changes` mutations between attempts within a single run. If `state_changes` are append-only, R2 reduces in severity; if they are rewritten in place, R2 is a strong contributor.

D3. **Persistence / DB terminal**: confirm whether POST_SELECT_CONFLICT path ever calls `db_manager.save_episode_bible` or `db.reset_after` (the only invalidators of `_cumulative_bible_cache`). If not, R3 is confirmed live.

D4. **Telemetry terminal**: pull `context_cache_attempts` rows from a 5-arc benchmark with POST_SELECT_CONFLICT events and bucket by `cache_outcome` × `cache_reason`. If `bypassed` is rare relative to `hit`, the lineage gate is dormant in practice and the in-cache stale content is being served.

## Open Questions

Q1. Is `stage2_arcs_source_lineage` the right anchor to extend with refined-arc and selected-blueprint fingerprints, or should a parallel `stage4_carryover_lineage` anchor be introduced?

Q2. Should `Director._caching.manuscript_cache_name` reuse predicate add a content_hash signal mirroring `_get_or_create_context_cache`, or should it be ported to the same registry so it inherits the four-signal lineage gate and TTL eviction?

Q3. Does the production runtime ever mutate `client._geuldobi_provider_mode` or `_geuldobi_vertex_auth_mode` mid-session? If not, `stale_provider_lineage` is an unreachable branch — the lineage gate effectively reduces to model + content_hash, weakening F1 further.

Q4. The `Director.invalidate_caches` and `chief_writer.invalidate_manuscript_cache` methods are dead (no callers). Are they intended to be wired to `db.reset_after` / project rollback paths, or are they obsolete? Either way, the gap should be closed.

Q5. Is the 50_000-char cache gate (`min_content_chars`) tuned to current Stage 4 prompt sizes? If Stage 4 sometimes falls below the gate (e.g. early eps, narrow lookback), the cache path is silently disabled and POST_SELECT_CONFLICT detection regresses to non-cached `ask()` — but the symptoms would look like cache stale, masking the real gate fall-through.

## Closure Recommendation

**ATTENTION** — context-cache lineage is **provider/model-aware but not source-aware**, and the Director-global manuscript cache lacks any lineage gate at all. Three concrete defects (F2, F3, F5) plus one structural gap (F4) are sufficient mechanism for POST_SELECT_CONFLICT carryover drift in 5-arc runs.

Recommended closure plan (read-only at this terminal; coordinate with system-track Lead before realization):

1. **Promote** F2 (Director count-only reuse) and F3 (Director-cache lineage bypass) to fix candidates — both are unambiguous gaps with localized fixes (lift Director's reuse predicate to share `_get_or_create_context_cache`'s four-signal gate, route `check_manuscript_history_with_cache` through `_ask_with_cached_context` so eviction-on-failure applies).
2. **Add** the regression tests T-R1, T-R3, T-R6 before any patch lands; T-R2 / T-R4 are richer integration tests that need a synthetic POST_SELECT_CONFLICT fixture from T01–T06.
3. **Decide** Q1 (lineage anchor scope) at Lead level — F4 is the longest lever but the largest design call: does Stage 4 deserve its own carryover-lineage anchor, or do we expand `stage2_arcs_source_lineage` to fingerprint refined arcs + selected blueprints?
4. **Audit extension**: T-R5 — surface `bypassed` × `cache_reason` in `audit_stage34_cache_gate_corpus.py` so future 5-arc runs make stale-cache pressure visible alongside cached-tokens proof.

Confidence in evidence: HIGH on F1/F2/F3/F4/F5/F8 (direct code reads). MEDIUM on R1/R2/R3 (mechanism is clear; live correlation with POST_SELECT_CONFLICT volume requires telemetry from D4). LOW on Q3/Q5 — needs runtime configuration and benchmark sampling outside the read-only scope.
