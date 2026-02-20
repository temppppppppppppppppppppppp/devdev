# Codex Findings Crosscut Sweep100 (Manual-Only)

This file is governed by:
- `AGENTS.md` (manual sweep guard)
- `docs/codex_crosscut_sweep100_plan.md`

## Validation Command
```bash
python scripts/validate_manual_sweep.py docs/codex_findings_crosscut_sweep100.md --from-round 1 --to-round 100 --allow-empty
python scripts/validate_manual_sweep.py docs/codex_findings_crosscut_sweep100.md --from-round 1 --to-round 100
python scripts/validate_manual_sweep.py docs/codex_findings_crosscut_sweep100.md --from-round 1 --to-round 100 --max-fp-ratio 0.35 --max-fp-streak 2
```

### Round 1 - Arc generation returns empty dict `{}`

**Read Files**:
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_finalizer.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_validation_pipeline.py:170` rejects falsy/non-dict `refined_arc` and returns retry at `modules/core/stage2_validation_pipeline.py:178`.
- `modules/core/stage2_orchestrator.py:503` consumes `{"action": "retry"}` and loops attempt; invalid arc does not flow into finalizer path.
- `modules/core/stage2_finalizer.py:61` uses `refined_arc.get(...)` (dict-safe for `{}`), so direct crash is not observed in current call order.
- `modules/core/stage2_preflight.py:125` initializes `passed=False` and `current_feedback=""`, matching retry-first loop intent.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/core/stage2_finalizer.py:61` relies on upstream validation ordering; direct/bypassed invocation contract is not locally guarded.

**False Positives Excluded**:
- `modules/core/stage2_finalizer.py:61` empty dict access was excluded as crash FP because `.get()` is used and normal path is pre-validated in `modules/core/stage2_validation_pipeline.py:170`.

**Test Gaps**:
- Missing regression test for direct empty-dict `refined_arc` injection that confirms retry occurs before finalizer entry.

### Round 2 - Arc generation returns `None`

**Read Files**:
- `modules/domain/agents/base_agent.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/base_agent.py:865` converts non-string/empty input to `{"parsing_error": True, ...}` sentinel.
- `modules/core/stage2_validation_pipeline.py:170` treats `None` as invalid and returns retry via `modules/core/stage2_validation_pipeline.py:178`.
- `modules/core/stage2_orchestrator.py:503` handles retry action without committing arc state.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `None` input was excluded as immediate pipeline crash FP because stage2 has explicit invalid-arc retry guard at `modules/core/stage2_validation_pipeline.py:170`.

**Test Gaps**:
- Missing focused unit test for `None` arc response path through stage2 retry loop.

### Round 3 - Blueprint LLM response is empty string `""`

**Read Files**:
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage3_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/blueprint_ensemble.py:384` parses response, and `modules/domain/agents/blueprint_ensemble.py:391` rejects results missing `scene_breakdown` or `integrated_scenario`.
- `modules/domain/agents/blueprint_ensemble.py:253` returns `(None, [])` when all candidates fail.
- `modules/domain/agents/three_phase_blueprint_generator.py:291` detects missing blueprint and marks generate phase failed.
- `modules/core/stage3_orchestrator.py:324` only commits on `blueprint` present + PASS verdict; failure path goes to `modules/core/stage3_orchestrator.py:329`.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- Empty blueprint response was excluded as DB corruption FP because save path is gated at `modules/core/stage3_orchestrator.py:324`.

**Test Gaps**:
- Missing integration test for empty-string blueprint response ensuring no `save_episode_blueprint` call occurs.

### Round 4 - Manuscript LLM response is list `['text']` instead of dict

**Read Files**:
- `modules/domain/agents/chief_writer.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director_ensemble.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/chief_writer.py:454` parses candidate output, and `modules/domain/agents/chief_writer.py:456` returns `None` for non-dict/list-top payload.
- `modules/domain/agents/chief_writer.py:365` guarantees fallback error candidate when all generation attempts fail, avoiding raw empty list propagation.
- `modules/core/stage4_interview_round.py:262` has explicit empty-candidates guard and returns `verdict="EMPTY"` at `modules/core/stage4_interview_round.py:286`.
- `modules/domain/agents/director_ensemble.py:419` chooses candidate from index/fallback in normal contract.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `modules/domain/agents/chief_writer.py:463` list-type `content` inside a valid dict is intentionally normalized to string, so that case is not treated as bug.

**Test Gaps**:
- Missing test that forces top-level list output from writer LLM and verifies stage4 returns `EMPTY` without crash.

### Round 5 - `arc_data.get('ep_count')` is `None`

**Read Files**:
- `modules/domain/agents/analyst.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage3_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/analyst.py:814` reads `llm_ep_count`, and `modules/domain/agents/analyst.py:818` normalizes non-int values to `target_ep_count`.
- `modules/domain/agents/analyst.py:921` force-updates `ep_count` and `ep_end` with computed values.
- `modules/core/stage2_validation_pipeline.py:613` casts `ep_count` to int with fallback to `0` at `modules/core/stage2_validation_pipeline.py:615`.
- `modules/core/stage3_orchestrator.py:284` performs arc-data validation before later usage.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- `ep_count=None` was excluded as arithmetic-crash FP because analyst/path-level coercion exists at `modules/domain/agents/analyst.py:818` and flow-guard fallback at `modules/core/stage2_validation_pipeline.py:615`.

**Test Gaps**:
- Missing test where LLM emits `"ep_count": null` and verifies stage2->stage3 continuity without silent value drift.

### Round 6 - `arc_data.get('ep_start')` is string `"5"`

**Read Files**:
- `modules/core/stage2_preflight.py`
- `modules/domain/agents/analyst.py`
- `modules/models/arc.py`
- `modules/core/stage3_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_preflight.py:465` compares `current_ep_start > 1`, so non-int injection can break before downstream normalization.
- `modules/domain/agents/analyst.py:719` computes `ep_end = ep_start + target_ep_count - 1`; this assumes arithmetic-compatible `ep_start`.
- `modules/models/arc.py:175` defines `ep_start: int` and `modules/models/arc.py:212` validates via Pydantic before dump in finalizer path.
- `modules/core/stage3_orchestrator.py:277` blocks non-int `ep_start` and breaks stage3 flow at `modules/core/stage3_orchestrator.py:281`.

**Confirmed Bugs**:
- none

**Risks**:
- Contract-fragility risk: if malformed `ep_start` reaches preflight/analyst before finalizer validation, arithmetic/comparison assumptions (`modules/core/stage2_preflight.py:465`, `modules/domain/agents/analyst.py:719`) can fail.

**False Positives Excluded**:
- Stage3 non-int halt at `modules/core/stage3_orchestrator.py:277` is intentional data-integrity stop, not a bug.

**Test Gaps**:
- Missing targeted test for string `ep_start` injection at stage2 attempt loop entry and expected recovery/abort behavior.

### Round 7 - `state_changes` is string (not dict/list structure)

**Read Files**:
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/core/stage4_post_processor.py:88` assigns `_sc = arc_data['state_changes']` and calls `_sc.get(...)` at `modules/core/stage4_post_processor.py:91` without type guard.
- The same block is wrapped in broad try/except (`modules/core/stage4_post_processor.py:84` to `modules/core/stage4_post_processor.py:172`), so failure degrades to warning path.
- `modules/core/stage4_context_builder.py:421` similarly uses `_sc = arc_data['state_changes']` and `_sc.get(...)` at `modules/core/stage4_context_builder.py:425`, but inside non-blocking try (`modules/core/stage4_context_builder.py:418` to `modules/core/stage4_context_builder.py:455`).
- `modules/domain/agents/state_tracker.py:1410` explicitly checks dict type and returns early on mismatch at `modules/domain/agents/state_tracker.py:1412`.

**Confirmed Bugs**:
- none

**Risks**:
- Non-dict `state_changes` can suppress memory/context enrichment side-effects in stage4 while continuing generation, reducing observability and continuity quality.

**False Positives Excluded**:
- Full stage4 hard-crash FP excluded because both problematic access sites are inside broad non-blocking exception handlers (`modules/core/stage4_post_processor.py:171`, `modules/core/stage4_context_builder.py:455`).

**Test Gaps**:
- Missing test for malformed `state_changes` ensuring warning telemetry is emitted and required non-memory outputs remain intact.

### Round 8 - `blueprint.get('scenes')` is `None`

**Read Files**:
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/blueprint_ensemble.py:391` enforces `scene_breakdown`/`integrated_scenario` keys, not `scenes`.
- `modules/domain/agents/chief_writer_context.py:98` reads `blueprint.get('scene_breakdown', {})`; `scenes` key is not consumed on this path.
- `modules/core/stage4_orchestrator.py:373` only checks blueprint object existence before stage4 loop usage.

**Confirmed Bugs**:
- none

**Risks**:
- `scene_breakdown` being structurally empty still permits progression; quality risk remains even when key exists but content is weak.

**False Positives Excluded**:
- Scenario key mismatch (`scenes`) was excluded as bug because current implementation contracts on `scene_breakdown` (`modules/domain/agents/chief_writer_context.py:98`).

**Test Gaps**:
- Missing test that validates minimum usable scene structure (not just key presence) before manuscript generation.

### Round 9 - `selected_candidate` exists but value is `None`

**Read Files**:
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/chief_writer.py`

**Manual Inspection Evidence**:
- PASS path uses `director_result.get('selected_candidate', {}).get(...)` at `modules/core/stage4_interview_round.py:701` and `modules/core/stage4_interview_round.py:702`.
- REJECT path reuses same chained access at `modules/core/stage4_interview_round.py:755` and `modules/core/stage4_interview_round.py:799`; explicit `None` value would break chained `.get`.
- `modules/core/stage4_interview_round.py:788` locally normalizes `_sel_candidate` for one branch only; this does not sanitize earlier/later chained uses.
- Producer side currently returns dict candidate via `modules/domain/agents/director_ensemble.py:419` under normal contract, with writer candidates validated at `modules/domain/agents/chief_writer.py:382`.

**Confirmed Bugs**:
- none

**Risks**:
- Contract-fragility risk: if external/custom director result injects `selected_candidate=None`, chained `.get` access can raise `AttributeError` in stage4 interview round.

**False Positives Excluded**:
- Under current in-repo producer contract (`modules/domain/agents/director_ensemble.py:419`), `selected_candidate` is normally dict-like, so this is not classified as confirmed runtime bug yet.

**Test Gaps**:
- Missing defensive test for `director_result={'selected_candidate': None}` in both PASS and REJECT branches.

### Round 10 - `physical_inventory` mixed `[str, {'name':'검'}]`

**Read Files**:
- `modules/core/stage2_validation_pipeline.py`
- `modules/domain/agents/continuity_arc.py`
- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/state_extractor.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_validation_pipeline.py:397` routes arc continuity checks to `continuity_inspector.inspect_arc(...)`, so inventory normalization is downstream in continuity logic.
- `modules/domain/agents/continuity_arc.py:683` and `modules/domain/agents/continuity_arc.py:692` coerce inventory entries via `str(i)` before duplicate checks.
- `modules/core/stage2_finalizer.py:255` defines `_item_name()` to normalize dict/string when inheriting inventory at `modules/core/stage2_finalizer.py:260`.
- `modules/domain/agents/state_extractor.py:323` extends raw list inventory, and cumulative dedupe later stringifies dict entries at `modules/domain/agents/state_extractor.py:378`.

**Confirmed Bugs**:
- none

**Risks**:
- Mixed-type inventory is mostly crash-safe but can degrade semantic equality (dict stringification vs canonical item name), causing continuity false mismatch/noise.

**False Positives Excluded**:
- Immediate unhashable-type crash FP excluded because downstream dedupe stringifies dict entries (`modules/domain/agents/state_extractor.py:378`) and finalizer has dict-name normalization (`modules/core/stage2_finalizer.py:255`).

**Test Gaps**:
- Missing continuity regression test for mixed inventory list with dict+string aliases representing the same item.

## Checkpoint - Crosscut Round 10

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 0 (P0: 0, P1: 0, P2: 0, P3: 0) |
| Cumulative Risks | 6 |
| Cumulative False Positives Excluded | 10 |
| Cumulative Test Gaps | 10 |
| Phase False-Positive Ratio | 62.5% (10 / (0+6+10)) |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% (10/10 rounds) |

### Round 11 - Episode 1 boundary (`episode-1=0`) prior manuscript lookup empty

**Read Files**:
- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage4_context_builder.py:126` loads `get_manuscript(next_ep - 1)` and `modules/core/stage4_context_builder.py:127` falls back to empty `prev_text` when no row exists.
- `modules/core/stage4_context_builder.py:73` returns empty extended lookback for early episodes (`next_ep <= 3`), so ep1 does not attempt long-history digest.
- `modules/domain/agents/chief_writer_context.py:173` and `modules/domain/agents/chief_writer_context.py:174` guard empty prior manuscript by producing empty ending/digest.
- `modules/core/stage4_orchestrator.py:392` consumes prepared context and proceeds with mandatory prompts without hard dependency on non-empty previous manuscript.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- Episode 1 "previous manuscript missing" was excluded as bug because context builder has explicit null/empty fallback (`modules/core/stage4_context_builder.py:127`).

**Test Gaps**:
- Missing stage4 integration test for ep1 that asserts no DB underflow/negative-episode side effects and stable prompt assembly.

### Round 12 - Single-Arc project (`volumes_strategy=[]`) path

**Read Files**:
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight.py`
- `modules/domain/agents/state_tracker.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_orchestrator.py:128` normalizes empty volume strategy to `[]` and logs default-mode progression at `modules/core/stage2_orchestrator.py:130`.
- `modules/core/stage2_orchestrator.py:377` to `modules/core/stage2_orchestrator.py:379` resolves `current_vol_strategy` with `default_vol_strategy` fallback when list is empty.
- `modules/core/stage2_orchestrator.py:172` to `modules/core/stage2_orchestrator.py:175` still performs StateTracker incremental load/update regardless of volume strategy presence.
- `modules/core/stage2_preflight.py:129` continues pre-generation constraint build from `global_arc_no`, independent of volume strategy content.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- Empty volume strategy was excluded as config bug because stage2 explicitly defines and uses default strategy fallback (`modules/core/stage2_orchestrator.py:377`).

**Test Gaps**:
- Missing e2e test for one-arc roadmap + empty volume strategy ensuring stable arc numbering and tracker updates.

### Round 13 - Last-episode boundary and loop termination

**Read Files**:
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_context_builder.py`

**Manual Inspection Evidence**:
- `modules/core/stage3_orchestrator.py:139` drives bounded loop `while working_ep <= target_ep`, and `modules/core/stage3_orchestrator.py:141` updates episode cursor from per-episode result.
- `modules/core/stage3_orchestrator.py:559` returns `next_ep = working_ep + 1` on failure path; boundary naturally exits once cursor exceeds target.
- `modules/core/stage4_orchestrator.py:368` terminates when `next_ep > target_ep`, preventing extra episode generation after target completion.
- `modules/core/stage4_orchestrator.py:383` confines arc lookup to `ep_start <= next_ep <= ep_end`, and breaks when no matching arc exists at `modules/core/stage4_orchestrator.py:387`.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- Last-episode off-by-one FP excluded because both stage3 and stage4 loops use explicit upper-bound checks (`modules/core/stage3_orchestrator.py:139`, `modules/core/stage4_orchestrator.py:368`).

**Test Gaps**:
- Missing boundary test for exact target episode completion followed by immediate clean stop in both stage3 and stage4.

### Round 14 - Rollback case (`existing_tracker_arcs > len(all_refined_arcs)`)

**Read Files**:
- `modules/core/stage2_orchestrator.py`
- `modules/domain/agents/state_tracker.py`
- `modules/core/stage2_preflight.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_orchestrator.py:157` reads loaded tracker arc count and compares rollback/staleness at `modules/core/stage2_orchestrator.py:161`.
- On mismatch, `modules/core/stage2_orchestrator.py:163` re-instantiates `StateTracker` and resets load cursor at `modules/core/stage2_orchestrator.py:166`.
- `modules/core/stage2_orchestrator.py:172` then reloads only valid current arcs and syncs loaded count at `modules/core/stage2_orchestrator.py:175`.
- `modules/core/stage2_preflight.py:597` snapshot pattern confirms downstream rollback intent is already part of stage2 safety design.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- Tracker reset on arc-count regression was excluded as data-loss bug because code intentionally rebuilds from persisted arc source (`modules/core/stage2_orchestrator.py:163`).

**Test Gaps**:
- Missing regression test where arcs are trimmed and stage2 confirms tracker rebuild without stale NPC/plot residue.

### Round 15 - Blueprint failure followed by next-episode continuity block

**Read Files**:
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/domain/agents/blueprint_ensemble.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/three_phase_blueprint_generator.py:291` marks generate failure when no blueprint candidate survives.
- `modules/core/stage3_orchestrator.py:523` records episode blueprint failure and increments fail count in `_handle_failure`.
- `_handle_failure` returns `next_ep = working_ep + 1` at `modules/core/stage3_orchestrator.py:565`, so control moves to subsequent episode.
- Next episode enforces previous-blueprint prerequisite at `modules/core/stage3_orchestrator.py:259` to `modules/core/stage3_orchestrator.py:263`, then breaks generation.

**Confirmed Bugs**:
- none

**Risks**:
- Conservative-stop risk: one failed episode can halt later episodes through strict previous-blueprint gate, which may reduce throughput in partial-recovery workflows.

**False Positives Excluded**:
- This was excluded as sequencing bug because continuity-first policy is explicitly encoded in previous-episode blueprint gate (`modules/core/stage3_orchestrator.py:259`).

**Test Gaps**:
- Missing scenario test for failed ep N followed by controlled resume policy options (strict stop vs operator-approved skip).

### Round 16 - 5 interview REJECTs and non-interactive fallback

**Read Files**:
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_context_builder.py`

**Manual Inspection Evidence**:
- `modules/core/stage4_orchestrator.py:641` enters 5-failure branch when no final manuscript is accepted.
- `modules/core/stage4_orchestrator.py:646` sets default skip choice (`_choice = 2`) before optional prompt call.
- `modules/core/stage4_orchestrator.py:647` calls `get_int_input` only if callable; otherwise it keeps default skip path and returns at `modules/core/stage4_orchestrator.py:655`.
- `modules/core/stage4_interview_round.py:842` returns explicit `REJECT` result object each failed round, preserving deterministic loop state.

**Confirmed Bugs**:
- none

**Risks**:
- If `get_int_input` is callable but blocks in headless runtime, stage4 can still stall despite fallback default being pre-set.

**False Positives Excluded**:
- "Always interactive block" FP excluded because call is gated by callable check and has non-interactive default skip path (`modules/core/stage4_orchestrator.py:647`).

**Test Gaps**:
- Missing headless-run test where `get_int_input` is absent/callable stubbed and stage4 completes without blocking.

### Round 17 - CoVe `should_regenerate=True` overrides PASS candidate

**Read Files**:
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director_ensemble.py`

**Manual Inspection Evidence**:
- `modules/core/stage4_orchestrator.py:596` receives PASS from interview round and sets final manuscript.
- `modules/core/stage4_orchestrator.py:617` to `modules/core/stage4_orchestrator.py:620` runs CoVe full verify when quick check flags risk.
- If `should_regenerate` is true, `modules/core/stage4_orchestrator.py:623` rewrites feedback context, clears `final_manuscript` at `modules/core/stage4_orchestrator.py:629`, and continues round loop.
- This path preserves retry state via `previous_attempt` payload at `modules/core/stage4_orchestrator.py:624` to `modules/core/stage4_orchestrator.py:628`.

**Confirmed Bugs**:
- none

**Risks**:
- CoVe-triggered repeated regenerate loops can consume all 5 rounds even after high-scoring PASS, increasing drop risk without separate budget control.

**False Positives Excluded**:
- PASS-to-REJECT override was excluded as logic bug because CoVe safety policy is explicitly intentional at `modules/core/stage4_orchestrator.py:621`.

**Test Gaps**:
- Missing deterministic test where CoVe forces regenerate once, then verifies loop resumes with injected feedback context.

### Round 18 - DB commit failure and StateTracker snapshot rollback

**Read Files**:
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_preflight.py:597` to `modules/core/stage2_preflight.py:620` deep-copies key tracker registries into `st_snapshot` before mutation-heavy extraction.
- `modules/core/stage2_finalizer.py:311` wraps DB save/commit and treats false commit as failure at `modules/core/stage2_finalizer.py:316`.
- On commit failure, finalizer pops just-added arc at `modules/core/stage2_finalizer.py:324` and restores tracker fields from snapshot at `modules/core/stage2_finalizer.py:329`.
- Finalizer returns retry action at `modules/core/stage2_finalizer.py:334`, and orchestrator attempt loop consumes that retry path.

**Confirmed Bugs**:
- none

**Risks**:
- Snapshot restoration iterates selected fields only; newly added tracker fields outside snapshot set can still drift across failed commit retries.

**False Positives Excluded**:
- "Commit failure leaves arc persisted" FP excluded because failed-commit branch explicitly pops in-memory appended arc (`modules/core/stage2_finalizer.py:324`).

**Test Gaps**:
- Missing fault-injection test for `safe_commit_async=False` validating full tracker/arc rollback parity over multiple retries.

### Round 19 - Stage3 entry with arcless state

**Read Files**:
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage3_orchestrator.py:69` checks `if not ctx.current_project.arcs` and aborts early with prerequisite error.
- No per-episode loop starts until after this guard; main loop initialization begins at `modules/core/stage3_orchestrator.py:123`.
- Stage4 has parallel guard for missing arc mapping (`modules/core/stage4_orchestrator.py:387`) and stops before generation.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- Arcless stage3 path was excluded as null-deref bug because explicit precondition guard returns early (`modules/core/stage3_orchestrator.py:69`).

**Test Gaps**:
- Missing CLI-level test for stage3 invocation with empty arcs to verify clear operator message and zero side effects.

### Round 20 - Multi-arc recovery and original order restoration

**Read Files**:
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight.py`
- `modules/domain/agents/analyst.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_orchestrator.py:311` computes original success indices and combines with `recovery_map` to rebuild compacted batch order.
- `modules/core/stage2_orchestrator.py:318` replays original index range and re-inserts recovered entries deterministically.
- Missing indices are explicitly logged and audited at `modules/core/stage2_orchestrator.py:322` to `modules/core/stage2_orchestrator.py:323`, avoiding silent shuffle.
- If rebuild yields empty batch, orchestrator hard-stops at `modules/core/stage2_orchestrator.py:325` instead of proceeding with inconsistent state.

**Confirmed Bugs**:
- none

**Risks**:
- Partial recovery with sparse failures can still drop unrecoverable arcs by design; downstream episode planning may need explicit operator awareness for skipped arc slots.

**False Positives Excluded**:
- "Recovered batch always reorders wrongly" FP excluded because explicit index reconstruction logic exists (`modules/core/stage2_orchestrator.py:311` to `modules/core/stage2_orchestrator.py:320`).

**Test Gaps**:
- Missing deterministic test with interleaved fail/recover indices validating final enriched batch order and skip audit entries.

## Checkpoint - Crosscut Round 20

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 0 (P0: 0, P1: 0, P2: 0, P3: 0) |
| Cumulative Risks | 11 |
| Cumulative False Positives Excluded | 20 |
| Cumulative Test Gaps | 20 |
| Phase False-Positive Ratio | 64.5% (20 / (0+11+20)) |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% (20/20 rounds) |

### Round 21 - ChiefWriter 3-strategy parallel generation with one timeout

**Read Files**:
- `modules/domain/agents/chief_writer.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director_ensemble.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/chief_writer.py:252` runs 3-worker `ThreadPoolExecutor` and collects futures via `as_completed` at `modules/domain/agents/chief_writer.py:279`.
- Timeout path at `modules/domain/agents/chief_writer.py:289` appends explicit error candidate, preserving list shape for downstream handling.
- Code comment at `modules/domain/agents/chief_writer.py:274` to `modules/domain/agents/chief_writer.py:277` documents soft-timeout limitation (running threads cannot be force-stopped).
- `modules/core/stage4_interview_round.py:262` handles no-candidate outcomes with explicit EMPTY verdict instead of index-based crash.

**Confirmed Bugs**:
- none

**Risks**:
- Soft-timeout semantics can still exceed configured timeout under slow API calls, causing latency tail despite timeout handlers.

**False Positives Excluded**:
- Single-strategy timeout was excluded as immediate stage4 crash because writer appends structured error candidate (`modules/domain/agents/chief_writer.py:291`) and stage4 has empty-guard.

**Test Gaps**:
- Missing deterministic timeout test proving total wall-clock bound behavior under one RUNNING thread that cannot be canceled.

### Round 22 - `BaseAgent._context_caches` concurrent read/write pressure

**Read Files**:
- `modules/domain/agents/base_agent.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/blueprint_ensemble.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/base_agent.py:1007` defines class-level shared `_context_caches`.
- Cache hit/insert/evict is unsynchronized in `_get_or_create_context_cache` (`modules/domain/agents/base_agent.py:1041`, `modules/domain/agents/base_agent.py:1071`, `modules/domain/agents/base_agent.py:1088`).
- `modules/domain/agents/base_agent.py:1082` catches `RuntimeError` during key sorting, indicating concurrent mutation was already observed/anticipated.
- Callers in generation flows use cache utility from hot paths before/around parallel candidate production (`modules/domain/agents/chief_writer.py:226`, `modules/domain/agents/blueprint_ensemble.py:364` onward generation).

**Confirmed Bugs**:
- none

**Risks**:
- Shared class-level cache without dedicated lock can produce non-deterministic eviction/hit behavior under concurrent agent usage.

**False Positives Excluded**:
- This is not classified as confirmed crash because runtime guards/fallbacks exist (`modules/domain/agents/base_agent.py:1082`, `modules/domain/agents/base_agent.py:1094`).

**Test Gaps**:
- Missing multithread stress test validating cache hit consistency and eviction determinism across concurrent agent instances.

### Round 23 - `_quota_exhausted_models` concurrent update semantics

**Read Files**:
- `modules/domain/agents/base_agent.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/base_agent.py:136` declares `_quota_exhausted_models` as class-shared dict.
- Ask path reads exhaustion map at `modules/domain/agents/base_agent.py:277` and writes fallback cache at `modules/domain/agents/base_agent.py:452`.
- Rotation path clears model cache under lock at `modules/domain/agents/base_agent.py:193`, but normal ask-path read/write around it is not lock-guarded.
- Stage4/Writer concurrent generation increases call concurrency on shared BaseAgent code paths (`modules/core/stage4_interview_round.py:96`, `modules/domain/agents/chief_writer.py:252`).

**Confirmed Bugs**:
- none

**Risks**:
- Concurrent read/write timing on shared quota cache can cause transient stale skip/fallback decisions across workers.

**False Positives Excluded**:
- Hard data-corruption FP excluded because values are simple timestamps and failures still fall back through model-switch/exception handling.

**Test Gaps**:
- Missing concurrency test where multiple parallel asks hit mixed quota/rate-limit responses and verify consistent model selection order.

### Round 24 - `DBManager._cumulative_bible_cache` growth control

**Read Files**:
- `modules/core/db_manager.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage2_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/db_manager.py:58` introduces in-memory `_cumulative_bible_cache` map.
- `modules/core/db_manager.py:736` to `modules/core/db_manager.py:740` enforces pre-write LRU-like cap (`_MAX_BIBLE_CACHE = 5`).
- `modules/core/db_manager.py:791` to `modules/core/db_manager.py:794` invalidates cached entries after rollback delete operations.
- Stage context consumers continue using DB-level APIs without directly retaining unbounded per-episode copies in orchestrators.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- Memory leak claim was excluded because explicit cache-size cap and invalidation path are present (`modules/core/db_manager.py:736`, `modules/core/db_manager.py:791`).

**Test Gaps**:
- Missing long-session test confirming cache key count never exceeds limit during 100+ episode operations.

### Round 25 - Stage2 preflight ThreadPool timeout and shutdown behavior

**Read Files**:
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_orchestrator.py`
- `modules/domain/agents/base_agent.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_preflight.py:103` launches two futures and waits with per-result timeout at `modules/core/stage2_preflight.py:106`.
- On timeout/error, code falls back to empty defaults (`modules/core/stage2_preflight.py:108` to `modules/core/stage2_preflight.py:112`).
- No explicit future cancel path exists in this block; context-manager exit handles executor teardown only.
- Stage2 orchestrator consumes preflight outputs immediately in attempt loop (`modules/core/stage2_orchestrator.py:402` onward), assuming prompt teardown.

**Confirmed Bugs**:
- none

**Risks**:
- Potential delayed shutdown risk if one preflight worker remains RUNNING after timeout, because explicit cancel/join strategy is absent in this block.

**False Positives Excluded**:
- Immediate crash FP excluded: exception branch explicitly sets safe defaults (`modules/core/stage2_preflight.py:110` to `modules/core/stage2_preflight.py:112`).

**Test Gaps**:
- Missing fault test with one hung preflight future verifying total teardown latency stays bounded.

### Round 26 - `arc_ensemble` future cancel behavior

**Read Files**:
- `modules/domain/agents/arc_ensemble.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/arc_ensemble.py:159` iterates `as_completed` with global timeout and per-future timeout handling at `modules/domain/agents/arc_ensemble.py:163`.
- Cleanup only calls `f.cancel()` in finally (`modules/domain/agents/arc_ensemble.py:183`) without checking cancel result.
- Empty-candidate fallback returns `(None, [])` at `modules/domain/agents/arc_ensemble.py:199`, avoiding direct index failure.
- Stage2 orchestrator already handles no-data batch via critical-stop guard (`modules/core/stage2_orchestrator.py:325`).

**Confirmed Bugs**:
- none

**Risks**:
- Running futures may outlive timeout window because cancel is best-effort; tail latency can exceed configured ensemble timeout.

**False Positives Excluded**:
- "Always crashes on timeout" FP excluded due explicit timeout/exception branches and empty-result guard (`modules/domain/agents/arc_ensemble.py:173`, `modules/domain/agents/arc_ensemble.py:199`).

**Test Gaps**:
- Missing executor-behavior test with RUNNING future that ignores cancel and validates bounded control return.

### Round 27 - `blueprint_ensemble` future cancel behavior

**Read Files**:
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage3_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/blueprint_ensemble.py:214` runs `as_completed` with timeout and per-future timeout branch at `modules/domain/agents/blueprint_ensemble.py:223`.
- Cleanup again uses best-effort `cancel()` only (`modules/domain/agents/blueprint_ensemble.py:237`).
- If no candidate survives, function returns `(None, [])` at `modules/domain/agents/blueprint_ensemble.py:253`.
- Three-phase generator handles missing blueprint as failed generation and continues retry flow (`modules/domain/agents/three_phase_blueprint_generator.py:291`).

**Confirmed Bugs**:
- none

**Risks**:
- Timeout does not guarantee worker stop; residual running tasks can increase episode latency under heavy model delays.

**False Positives Excluded**:
- Immediate stage3 crash FP excluded because missing-candidate path is explicitly handled and escalated as generation failure (`modules/domain/agents/three_phase_blueprint_generator.py:292`).

**Test Gaps**:
- Missing concurrency test for blueprint ensemble with partial completion + lingering future cancellation behavior.

### Round 28 - `consensus_validator` timeout/cancel and conservative PASS

**Read Files**:
- `modules/domain/agents/consensus_validator.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/consensus_validator.py:222` processes validator futures with timeout and per-vote timeout handling.
- On timeout/error, results are appended as PASS-like fallback (`modules/domain/agents/consensus_validator.py:231` to `modules/domain/agents/consensus_validator.py:248`).
- Cleanup uses `f.cancel()` only (`modules/domain/agents/consensus_validator.py:263`).
- If all validators fail, code forces conservative PASS fallback at `modules/domain/agents/consensus_validator.py:280`.

**Confirmed Bugs**:
- none

**Risks**:
- Conservative PASS on validator failure can under-report true quality/continuity violations when all workers fail under load.

**False Positives Excluded**:
- Hard crash FP excluded because validator has explicit empty-result fallback and returns synthesized consensus result (`modules/domain/agents/consensus_validator.py:280`).

**Test Gaps**:
- Missing chaos test where all consensus futures timeout to validate acceptable false-negative bounds and telemetry.

### Round 29 - `director_auditor` self-consistency vote thread handling

**Read Files**:
- `modules/domain/agents/director_auditor.py`
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/director_ensemble.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/director_auditor.py:875` runs vote ensemble with thread pool and as_completed timeout at `modules/domain/agents/director_auditor.py:880`.
- Vote-level timeout/error branches keep process alive (`modules/domain/agents/director_auditor.py:888`, `modules/domain/agents/director_auditor.py:891`).
- Cleanup is best-effort cancel only (`modules/domain/agents/director_auditor.py:898`).
- Stage4 interview consumes director verdict in loop, so prolonged vote completion directly impacts round latency (`modules/core/stage4_interview_round.py:635` onward).

**Confirmed Bugs**:
- none

**Risks**:
- Timeout-bound expectation can be violated by non-cancelable running vote calls, stretching stage4 interview latency.

**False Positives Excluded**:
- "Vote timeout causes immediate abort" FP excluded because timeouts are non-fatal and auditor still composes result from completed votes.

**Test Gaps**:
- Missing stress test for delayed SC votes confirming bounded total round duration and stable verdict derivation.

### Round 30 - `adaptive_retry` failure history growth controls

**Read Files**:
- `modules/core/adaptive_retry.py`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/adaptive_retry.py:516` stores failures per episode in `_failures`.
- Per-episode list is capped by `max_history` at `modules/core/adaptive_retry.py:557`.
- Episode-key count is also capped by `_max_episode_keys` at `modules/core/adaptive_retry.py:561`.
- Access/update paths are lock-guarded (`modules/core/adaptive_retry.py:552`, `modules/core/adaptive_retry.py:590`), reducing concurrent growth anomalies.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- Unbounded `_failures` memory leak claim was excluded because both per-episode and episode-key caps are explicitly implemented (`modules/core/adaptive_retry.py:557`, `modules/core/adaptive_retry.py:561`).

**Test Gaps**:
- Missing long-run memory test asserting adaptive-retry record footprint remains bounded over many episodes and agents.

## Checkpoint - Crosscut Round 30

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 0 (P0: 0, P1: 0, P2: 0, P3: 0) |
| Cumulative Risks | 19 |
| Cumulative False Positives Excluded | 30 |
| Cumulative Test Gaps | 30 |
| Phase False-Positive Ratio | 61.2% (30 / (0+19+30)) |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% (30/30 rounds) |

### Round 31 - `cumulative_state_cache` ctx↔app sync mismatch risk

**Read Files**:
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_context.py`
- `modules/core/prompt_builder.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_preflight.py:141` checks ctx cache/key and may reuse ctx-local `cumulative_state_cache`.
- On refresh, `modules/core/stage2_preflight.py:147` updates ctx cache and `modules/core/stage2_preflight.py:151` optionally syncs app cache via callback.
- App-side consumer `modules/core/prompt_builder.py:530` reads `_app._cumulative_state_cache` and `_app._cumulative_state_cache_key` directly.
- Sync callback semantics are defined in `modules/core/stage2_context.py:232` to `modules/core/stage2_context.py:235`.

**Confirmed Bugs**:
- none

**Risks**:
- If callback is absent or partial, ctx and app cache sources can diverge and produce stale state prompt generation in app-level builder path.

**False Positives Excluded**:
- Immediate crash FP excluded because both preflight and prompt_builder have fallback extraction paths when cache miss/mismatch occurs.

**Test Gaps**:
- Missing integration test that mutates arc count and verifies ctx/app cache parity across stage2 preflight and prompt_builder call sequence.

### Round 32 - `_cumulative_state_cache_key` key-only sync path

**Read Files**:
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_context.py`
- `modules/core/prompt_builder.py`

**Manual Inspection Evidence**:
- Secondary preflight branch sets ctx cache/key at `modules/core/stage2_preflight.py:387` to `modules/core/stage2_preflight.py:388`.
- It then performs key-only sync (`sync_cache_key_to_app(arc_count)`) at `modules/core/stage2_preflight.py:391`.
- Callback in `modules/core/stage2_context.py:234` updates app cache object only when `cache is not None`.
- App prompt path may trust matching key and reuse app cache at `modules/core/prompt_builder.py:530`.

**Confirmed Bugs**:
- none

**Risks**:
- Key-only sync can leave app cache payload stale while key appears current, increasing stale-hit probability when app-level cache is consulted.

**False Positives Excluded**:
- This is not confirmed deterministic bug because key-only sync may be intentional optimization for branches where app cache is not consumed immediately.

**Test Gaps**:
- Missing regression test that asserts app cache object refresh behavior for key-only sync branch.

### Round 33 - Arc count changes and cache hit/miss transitions

**Read Files**:
- `modules/core/prompt_builder.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/prompt_builder.py:529` uses arc count as cache key discriminator for cumulative state extraction.
- On miss, builder recomputes via extractor and rewrites app cache/key (`modules/core/prompt_builder.py:533` to `modules/core/prompt_builder.py:535`).
- Stage2 preflight uses the same `arc_count` key basis (`modules/core/stage2_preflight.py:139`, `modules/core/stage2_preflight.py:383`).
- Stage2 orchestrator mutates arc list over retries/commits, which changes count and drives hit/miss behavior.

**Confirmed Bugs**:
- none

**Risks**:
- Shared dependence on arc-count-only key may miss semantic cache invalidation cases where arc content changes but count is unchanged.

**False Positives Excluded**:
- "Always stale cache" FP excluded because both preflight and builder recompute when count differs (`modules/core/prompt_builder.py:533`).

**Test Gaps**:
- Missing test for content-changed/same-count scenario validating cache invalidation strategy adequacy.

### Round 34 - Entity registry cache invalidation on extract failure

**Read Files**:
- `modules/core/stage3_orchestrator.py`
- `modules/domain/agents/state_extractor.py`
- `modules/core/stage3_context.py`

**Manual Inspection Evidence**:
- Stage3 caches entity registry per arc index (`modules/core/stage3_orchestrator.py:338` and `modules/core/stage3_orchestrator.py:361`).
- On extraction error, it clears cached payload and resets cache index to `-1` (`modules/core/stage3_orchestrator.py:363` to `modules/core/stage3_orchestrator.py:366`).
- Next call re-enters fresh extraction path due index mismatch check.
- Stage3 context keeps extractor dependencies optional/fail-soft via `from_app` getattr bindings (`modules/core/stage3_context.py:93` onward).

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- Cache poisoning FP excluded because failure branch explicitly invalidates cache key (`modules/core/stage3_orchestrator.py:366`).

**Test Gaps**:
- Missing test that simulates first-call extractor failure then successful retry with cache reset verification.

### Round 35 - Stage4 ctx reset and lazy submodule invalidation

**Read Files**:
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_post_processor.py`

**Manual Inspection Evidence**:
- Stage4 orchestrator stores lazy submodule handles (`modules/core/stage4_orchestrator.py:229` to `modules/core/stage4_orchestrator.py:231`).
- Context setter invalidates all three cached submodules (`modules/core/stage4_orchestrator.py:245` to `modules/core/stage4_orchestrator.py:248`).
- `ctx` property rebuilds DI context on demand when absent (`modules/core/stage4_orchestrator.py:236` to `modules/core/stage4_orchestrator.py:239`).
- This pattern ensures new ctx is bound before next builder/post-processor/interview-round usage.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- Stale-submodule-context FP excluded due explicit invalidation on ctx assignment (`modules/core/stage4_orchestrator.py:245`).

**Test Gaps**:
- Missing test that swaps ctx mid-run and verifies recreated submodules consume the new ctx.

### Round 36 - `stage_rejection_history=None` guard

**Read Files**:
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_context.py`
- `modules/core/stage2_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_finalizer.py:668` guards append with `is not None` check before touching rejection history.
- Stage2 context wiring allows optional `stage_rejection_history` from app via getattr (`modules/core/stage2_context.py:202`).
- Orchestrator retry-pattern analyzer also checks truthiness before iterating history (`modules/core/stage2_orchestrator.py:420`).

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- Null-append crash FP excluded because explicit None guard is present in finalizer path (`modules/core/stage2_finalizer.py:668`).

**Test Gaps**:
- Missing test with `stage_rejection_history=None` ensuring retry analysis and finalizer paths both remain non-fatal.

### Round 37 - Scoring threshold dynamics and path consistency

**Read Files**:
- `modules/validation/scoring_validator.py`
- `modules/validation/validation_orchestrator.py`
- `modules/validation/threshold_helper.py`

**Manual Inspection Evidence**:
- `modules/validation/scoring_validator.py:47` loads threshold defaults during validator initialization, then stores `self.pass_threshold`.
- Orchestrator normal path compares against static `self.scoring.pass_threshold` (`modules/validation/validation_orchestrator.py:529`).
- Adaptive threshold logic is actively applied in parallel path (`modules/validation/validation_orchestrator.py:960` to `modules/validation/validation_orchestrator.py:963`) and restored after run (`modules/validation/validation_orchestrator.py:1149`).
- Shared `_threshold` helper reads config at call time (`modules/validation/threshold_helper.py:10`), but existing validator instances do not auto-refresh threshold fields.

**Confirmed Bugs**:
- none

**Risks**:
- Threshold behavior differs between sequential `validate()` and adaptive `validate_parallel_v59()` paths, which can create inconsistent pass/fail decisions for identical inputs.

**False Positives Excluded**:
- This is not a type/runtime crash; it is a policy-consistency risk between two intended validation modes.

**Test Gaps**:
- Missing parity test comparing `validate()` vs `validate_parallel_v59()` decisions under identical context and adaptive-threshold settings.

### Round 38 - WorldState rollback vs FactLedger rollback consistency

**Read Files**:
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/stage4_post_processor.py`

**Manual Inspection Evidence**:
- `modules/core/world_state.py:408` resets state and replays episode bibles to `target_ep-1`.
- `modules/core/fact_ledger.py:521` performs similar reset+replay for ledger state over same episode range.
- Normal episode updates write to both systems from shared `arc_data.state_changes` in post-processor (`modules/core/stage4_post_processor.py:401` and `modules/core/stage4_post_processor.py:430`).
- Both update paths are non-blocking on failure (`modules/core/stage4_post_processor.py:426`, `modules/core/stage4_post_processor.py:450`), so partial success can temporarily diverge views.

**Confirmed Bugs**:
- none

**Risks**:
- Non-blocking independent update/rollback flows can produce transient world_state vs fact_ledger divergence when one side fails.

**False Positives Excluded**:
- "No rollback support" FP excluded because both modules include explicit rollback replay methods (`modules/core/world_state.py:408`, `modules/core/fact_ledger.py:521`).

**Test Gaps**:
- Missing coordinated rollback test that injects one-side replay failure and verifies reconciliation strategy.

### Round 39 - Stage2→Stage3 context slot transition

**Read Files**:
- `modules/core/stage2_context.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`

**Manual Inspection Evidence**:
- Stage2 context includes cache-sync callbacks and cumulative cache slots (`modules/core/stage2_context.py:212` to `modules/core/stage2_context.py:235`).
- Stage3 context has a narrower callback surface focused on blueprinting needs (`modules/core/stage3_context.py:29` to `modules/core/stage3_context.py:39`).
- Stage3 orchestrator consumes stage3-specific callbacks (arc context, blueprint integrity, save commit) and does not reference stage2 cache callbacks.
- DI boundaries are explicit and stage-specific via `from_app` mappings in each context class.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- "Missing stage2 cache slots in stage3 context" was excluded as bug because stage3 contract intentionally scopes to blueprint orchestration callbacks.

**Test Gaps**:
- Missing contract test that enforces required/optional callback sets per stage context class.

### Round 40 - Director caching invalidation timing

**Read Files**:
- `modules/domain/agents/director_caching.py`
- `modules/domain/agents/director.py`
- `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/director_caching.py:40` initializes `_protagonist_config` cache.
- `modules/domain/agents/director_caching.py:162` returns cached config immediately once set.
- No explicit invalidation/reset method exists in this module for `_protagonist_config` after bible edits.
- Director facade delegates config reads through this cache manager (`modules/domain/agents/director.py:313` to `modules/domain/agents/director.py:315`).

**Confirmed Bugs**:
- none

**Risks**:
- Runtime bible/protagonist_config edits during a long session can be ignored due sticky in-memory cache until object recreation.

**False Positives Excluded**:
- Hard crash FP excluded because stale config returns valid dict and downstream guards remain fail-soft.

**Test Gaps**:
- Missing test that mutates `master_bible.protagonist_config` mid-session and verifies cache refresh semantics.

## Checkpoint - Crosscut Round 40

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 0 (P0: 0, P1: 0, P2: 0, P3: 0) |
| Cumulative Risks | 25 |
| Cumulative False Positives Excluded | 40 |
| Cumulative Test Gaps | 40 |
| Phase False-Positive Ratio | 61.5% (40 / (0+25+40)) |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% (40/40 rounds) |

### Round 41 - Chained `.replace()` placeholder collision in state-update prompt

**Read Files**:
- `modules/domain/agents/manager.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/manager.py:140` to `modules/domain/agents/manager.py:145` constructs the update prompt by chained `.replace()` calls over `UPDATE_STATE_PROMPT_V25`.
- `modules/domain/agents/manager.py:141` injects raw `manuscript` text before `modules/domain/agents/manager.py:142` replaces `{current_state_json}` globally, so identical placeholder literals inside manuscript can be re-replaced.
- `modules/domain/agents/manager.py:149` to `modules/domain/agents/manager.py:155` sends the final prompt and parses JSON; there is no post-substitution guard for accidental second-pass replacement.

**Confirmed Bugs**:
- none

**Risks**:
- If manuscript text contains template literals like `{current_state_json}`, chained global replacement can mutate user text unintentionally before LLM submission.

**False Positives Excluded**:
- Generic "brace causes immediate crash" FP excluded because the code intentionally avoids `.format()` and handles missing `current_state` (`modules/domain/agents/manager.py:131` to `modules/domain/agents/manager.py:133`).

**Test Gaps**:
- Missing regression test where manuscript includes `{current_state_json}` and `{lore_list_json}` literals to verify no unintended substitution.

### Round 42 - Patch feedback brace escaping in patch-mode template formatting

**Read Files**:
- `modules/domain/agents/chief_writer.py`
- `config/prompts/chief_writer.yaml`
- `modules/core/prompt_loader.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/chief_writer.py:737` to `modules/domain/agents/chief_writer.py:743` escapes `{` and `}` in `director_feedback` and `original_manuscript` before `_patch_template.format(...)`.
- `config/prompts/chief_writer.yaml:53` to `config/prompts/chief_writer.yaml:70` confirms `PATCH_MODE_PROMPT` has explicit placeholders `feedback_text` and `original_manuscript`.
- `modules/domain/agents/chief_writer.py:745` to `modules/domain/agents/chief_writer.py:751` provides fallback prompt text when template loading fails.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- "director_feedback braces trigger format KeyError" FP excluded because brace escaping is explicitly applied before formatting (`modules/domain/agents/chief_writer.py:737` to `modules/domain/agents/chief_writer.py:743`).

**Test Gaps**:
- Missing test with nested braces and JSON-like director feedback in patch mode.

### Round 43 - `.format`/`format_map` failure path with brace-heavy templates

**Read Files**:
- `modules/core/prompt_loader.py`
- `modules/domain/agents/analyst_prompt_api.py`
- `modules/domain/agents/chief_writer_prompts.py`

**Manual Inspection Evidence**:
- `modules/core/prompt_loader.py:166` to `modules/core/prompt_loader.py:170` uses `SafeDict` + `format_map`, leaving unknown placeholders intact instead of failing hard.
- `modules/core/prompt_loader.py:171` to `modules/core/prompt_loader.py:173` catches substitution errors and returns the raw template.
- `modules/domain/agents/analyst_prompt_api.py:18` to `modules/domain/agents/analyst_prompt_api.py:23` repeats the same safe fallback strategy for legacy prompt formatting.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- "LLM response containing `{` causes prompt formatting KeyError in this path" FP excluded because formatting is applied to templates, not to LLM output payloads.

**Test Gaps**:
- Missing test that asserts unresolved placeholders are surfaced/flagged when loader returns partially substituted templates.

### Round 44 - Patch-mode prompt loader failure fallback behavior

**Read Files**:
- `modules/domain/agents/chief_writer.py`
- `modules/core/prompt_loader.py`
- `config/prompts/chief_writer.yaml`

**Manual Inspection Evidence**:
- `modules/domain/agents/chief_writer.py:729` loads `PATCH_MODE_PROMPT` via `PromptLoader`.
- `modules/domain/agents/chief_writer.py:730` to `modules/domain/agents/chief_writer.py:733` catches loader exceptions and forces `_patch_template = None`.
- `modules/domain/agents/chief_writer.py:745` to `modules/domain/agents/chief_writer.py:751` builds deterministic fallback instructions when template is unavailable.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- "patch mode hard-fails when YAML key is missing" FP excluded because missing/failed load is explicitly downgraded to fallback prompt generation.

**Test Gaps**:
- Missing test that simulates missing `PATCH_MODE_PROMPT` and verifies patch pipeline still produces candidates.

### Round 45 - Regex injection concern in quality gate and genre guard paths

**Read Files**:
- `modules/domain/agents/chief_writer_quality.py`
- `modules/core/genre_guards/base_guard.py`
- `modules/core/genre_guards/hunter_guard.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/chief_writer_quality.py:302` escapes NPC names with `re.escape(name)` before building regex context pattern.
- `modules/core/genre_guards/hunter_guard.py:283` escapes runtime skill names with `re.escape(skill_name)` for cooldown-based pattern checks.
- `modules/core/genre_guards/base_guard.py:326` to `modules/core/genre_guards/base_guard.py:329` evaluates regex patterns supplied by guard rules; no direct LLM text is compiled as regex in this path.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- "LLM-crafted regex metacharacters are compiled directly and execute as regex payload" FP excluded for inspected paths due explicit escaping of runtime names.

**Test Gaps**:
- Missing adversarial test with NPC/skill names containing metacharacters (`(`, `[`, `+`, `?`) across quality and guard checks.

### Round 46 - NPC name metacharacter handling across continuity checks

**Read Files**:
- `modules/domain/agents/continuity_manuscript.py`
- `modules/domain/agents/chief_writer_quality.py`
- `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/continuity_manuscript.py:529` to `modules/domain/agents/continuity_manuscript.py:550` continuity relationship-jump checks rely on fixed keyword groups and substring context, not raw NPC-name regex building.
- `modules/domain/agents/chief_writer_quality.py:302` to `modules/domain/agents/chief_writer_quality.py:304` applies `re.escape(name)` for NPC-specific regex checks.
- `modules/domain/agents/continuity_manuscript.py:1091` to `modules/domain/agents/continuity_manuscript.py:1104` relationship history tracking only covers predefined NPC keyword tokens.

**Confirmed Bugs**:
- none

**Risks**:
- Continuity relationship checks can miss real named NPC transitions when names are outside fixed keyword lists, causing false negatives despite safe metachar handling.

**False Positives Excluded**:
- "metacharacter NPC names crash continuity regex" FP excluded because inspected name-sensitive regex path escapes names before use.

**Test Gaps**:
- Missing test with explicit NPC names containing regex metacharacters and non-keyword names in continuity history tracking.

### Round 47 - YAML prompt schema vs runtime loader/caller alignment

**Read Files**:
- `modules/core/prompt_loader.py`
- `modules/domain/agents/analyst_prompt_api.py`
- `config/prompts/analyst.yaml`

**Manual Inspection Evidence**:
- `modules/core/prompt_loader.py:80` only recognizes keys matching uppercase pattern `^([A-Z][A-Z0-9_]+):\\s*\\|`.
- `modules/domain/agents/analyst_prompt_api.py:11` fetches prompts by key and silently falls back to legacy constants when loader returns `None`.
- `config/prompts/analyst.yaml:5`, `config/prompts/analyst.yaml:29`, and `config/prompts/analyst.yaml:112` show uppercase key style currently compatible with loader expectations.

**Confirmed Bugs**:
- none

**Risks**:
- Future prompt YAML edits using unsupported key style/scalar style can be silently ignored, with legacy fallback masking drift between YAML intent and runtime behavior.

**False Positives Excluded**:
- "missing YAML key immediately breaks Stage2" FP excluded because caller-level fallback to legacy prompt constants is in place.

**Test Gaps**:
- Missing key-parity test that validates required YAML keys and placeholder sets against API wrapper expectations.

### Round 48 - `arc_position_guide` boundary behavior at ratio edges

**Read Files**:
- `modules/core/prompt_builder.py`
- `modules/core/stage4_orchestrator.py`
- `modules/domain/agents/chief_writer_context.py`

**Manual Inspection Evidence**:
- `modules/core/prompt_builder.py:59` returns early for `total_eps <= 0`, preventing division faults.
- `modules/core/prompt_builder.py:66` prioritizes `arc_pos == 1` branch before final-episode branch at `modules/core/prompt_builder.py:96`.
- `modules/core/prompt_builder.py:76`, `modules/core/prompt_builder.py:86`, and `modules/core/prompt_builder.py:106` split intermediate states by ratio thresholds.

**Confirmed Bugs**:
- none

**Risks**:
- For one-episode arcs (`arc_pos=1`, `total_eps=1`), intro branch precedence can under-emphasize finale/high-impact guidance.

**False Positives Excluded**:
- "ratio boundary causes divide-by-zero crash" FP excluded due explicit `total_eps <= 0` guard.

**Test Gaps**:
- Missing boundary test matrix for `(arc_pos,total_eps)` including `(1,1)`, `(1,5)`, `(5,5)`, and out-of-range inputs.

### Round 49 - `high_impact_zone` guide boundary for small scene counts

**Read Files**:
- `modules/core/prompt_builder.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/core/stage4_orchestrator.py`

**Manual Inspection Evidence**:
- `modules/core/prompt_builder.py:131` to `modules/core/prompt_builder.py:133` returns empty guide when `total_scenes < 4`.
- `modules/core/prompt_builder.py:145` and `modules/core/prompt_builder.py:146` protect per-scene division with empty-list guards.
- `modules/core/prompt_builder.py:158` to `modules/core/prompt_builder.py:169` allocates front/back scene budgets only when guide generation is active.

**Confirmed Bugs**:
- none

**Risks**:
- Episodes with 1-3 scenes receive no high-impact budgeting guidance, which can cause quality variance between short and long blueprint structures.

**False Positives Excluded**:
- "scene boundary causes integer division failure" FP excluded due conditional guards on `front_scenes` and `back_scenes`.

**Test Gaps**:
- Missing tests for `scene_breakdown` sizes 0/1/2/3/4 verifying expected guide emission behavior.

### Round 50 - Mandatory-context downsizing and section-drop ordering

**Read Files**:
- `modules/core/stage4_orchestrator.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_context.py`

**Manual Inspection Evidence**:
- `modules/core/stage4_orchestrator.py:479` sets mandatory-context max length via threshold helper.
- `modules/core/stage4_orchestrator.py:485` to `modules/core/stage4_orchestrator.py:497` splits sections and repeatedly drops tail sections until under limit.
- `modules/core/stage4_orchestrator.py:500` to `modules/core/stage4_orchestrator.py:503` applies hard truncation fallback when a single section remains oversized.

**Confirmed Bugs**:
- none

**Risks**:
- Tail-drop truncation can remove late-appended but critical constraints (order-sensitive data loss) before interview/validation loop.

**False Positives Excluded**:
- "mandatory_context overflow always hard-crashes Stage4" FP excluded because both section-drop and fallback truncation paths ensure continuation.

**Test Gaps**:
- Missing priority-aware truncation test ensuring critical constraint sections survive when context exceeds configured max.

## Checkpoint - Crosscut Round 50

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 0 (P0: 0, P1: 0, P2: 0, P3: 0) |
| Cumulative Risks | 31 |
| Cumulative False Positives Excluded | 50 |
| Cumulative Test Gaps | 50 |
| Phase False-Positive Ratio | 61.7% (50 / (0+31+50)) |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% (50/50 rounds) |

### Round 51 - Wuxia guard forbidden-term path and regex handling boundary

**Read Files**:
- `modules/core/genre_guards/base_guard.py`
- `modules/core/genre_guards/wuxia_guard.py`
- `main_a.py`

**Manual Inspection Evidence**:
- `main_a.py:911` to `main_a.py:916` initializes genre guard through `create_genre_guard(...)` and injects it into project/runtime context.
- `modules/core/genre_guards/base_guard.py:206` to `modules/core/genre_guards/base_guard.py:208` checks forbidden terms by plain substring (`if term in manuscript`), not regex compilation.
- `modules/core/genre_guards/wuxia_guard.py:616` to `modules/core/genre_guards/wuxia_guard.py:617` performs regex checks only for predefined modern-notation patterns in `FORBIDDEN_MODERN_PATTERNS`.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- "무협 금기어에 정규식 메타문자가 섞이면 즉시 regex injection" FP excluded for the inspected path because core forbidden-term matching is substring-based, not dynamic regex compilation.

**Test Gaps**:
- Missing regression test for malformed custom modern-notation pattern entries to ensure `check_modern_notation` failure behavior remains non-blocking.

### Round 52 - Hunter guard deep-validation override and state key mismatch

**Read Files**:
- `modules/domain/agents/director_auditor.py`
- `modules/core/genre_guards/hunter_guard.py`
- `modules/core/genre_guards/base_guard.py`

**Manual Inspection Evidence**:
- `modules/domain/agents/director_auditor.py:83` calls `guard.run_deep_validation(manuscript, current_state)` as the runtime entry point for deep guard validation.
- `modules/core/genre_guards/hunter_guard.py:246` to `modules/core/genre_guards/hunter_guard.py:248` reads rank from `rank` first (fallback `realm`) in `get_impossible_actions(...)`.
- `modules/core/genre_guards/hunter_guard.py:825` to `modules/core/genre_guards/hunter_guard.py:829` uses only `current_state.get("realm", "E")` for dungeon-entry validation in `run_deep_validation(...)`.

**Confirmed Bugs**:
- none

**Risks**:
- `run_deep_validation` dungeon checks can over-reject when runtime state stores rank in `rank` but not in `realm`, because this path hard-defaults to `E`.

**False Positives Excluded**:
- "헌터 deep validation이 HIGH 위반을 critical로 승격하지 못한다" FP excluded because base and override both recompute `has_critical` with `HIGH/CRITICAL` severities (`modules/core/genre_guards/base_guard.py:229`, `modules/core/genre_guards/hunter_guard.py:861`).

**Test Gaps**:
- Missing test matrix for `{rank: "A", realm: ""}` and `{rank: "", realm: "A"}` states to verify consistent dungeon-entry verdicts.

### Round 53 - Investment guard financial registry persistence and rollback hygiene

**Read Files**:
- `modules/core/stage2_orchestrator.py`
- `modules/domain/agents/state_tracker.py`
- `modules/domain/agents/state_tracker_financial.py`

**Manual Inspection Evidence**:
- `modules/core/stage2_orchestrator.py:167` to `modules/core/stage2_orchestrator.py:170` restores `financial_registry` from DB into fresh `StateTracker` on reset/rebuild path.
- `modules/domain/agents/state_tracker.py:247` to `modules/domain/agents/state_tracker.py:249` extracts financial events only when `genre == "investment"`.
- `modules/core/stage2_orchestrator.py:178` to `modules/core/stage2_orchestrator.py:181` persists exported financial registry only if investment genre and registry is non-empty; `modules/domain/agents/state_tracker_financial.py:118` to `modules/domain/agents/state_tracker_financial.py:125` imports entries without prune logic.

**Confirmed Bugs**:
- none

**Risks**:
- On rollback/rebuild flows, stale historical financial entries can survive because import path appends/restores snapshot keys without explicit pruning against current arc set.

**False Positives Excluded**:
- "investment financial registry is never persisted" FP excluded because conditional persist path is explicitly implemented in Stage 2 orchestrator.

**Test Gaps**:
- Missing rollback regression test where arc count shrinks and financial registry must drop removed-arc keys before re-save.

### Round 54 - Fantasy guard minimum validation scope

**Read Files**:
- `modules/core/genre_guards/fantasy_guard.py`
- `modules/core/genre_guards/base_guard.py`
- `modules/domain/agents/director_auditor.py`

**Manual Inspection Evidence**:
- `modules/core/genre_guards/fantasy_guard.py:129` to `modules/core/genre_guards/fantasy_guard.py:137` declares fantasy `MANDATORY_CONCEPTS`.
- `modules/core/genre_guards/fantasy_guard.py:318` to `modules/core/genre_guards/fantasy_guard.py:333` validates only forbidden terms + parentheses in `validate_v20_manuscript(...)`.
- `modules/core/genre_guards/fantasy_guard.py:294` to `modules/core/genre_guards/fantasy_guard.py:307` deep validation adds tier/forbidden-term checks but no direct mandatory-concept presence check.

**Confirmed Bugs**:
- none

**Risks**:
- Fantasy mandatory concepts are guidance-only in inspected paths, so manuscripts can pass without core fantasy signal terms, reducing genre enforcement fidelity.

**False Positives Excluded**:
- "판타지 guard가 무협 금기어를 아예 검증하지 않는다" FP excluded because forbidden-term checks run in base path and are severity-upgraded in fantasy override.

**Test Gaps**:
- Missing negative test where manuscript omits fantasy core concepts (`마법`, `마나`, `주문`) and asserts whether warning/reject is expected.

### Round 55 - Cooking/Composer specialized guard chain depth

**Read Files**:
- `modules/core/genre_guards/__init__.py`
- `modules/core/genre_guards/cooking_guard.py`
- `modules/core/genre_guards/composer_guard.py`

**Manual Inspection Evidence**:
- `modules/core/genre_guards/__init__.py:39` to `modules/core/genre_guards/__init__.py:42` routes cooking/composer genres to dedicated guard classes.
- `modules/core/genre_guards/cooking_guard.py:165` to `modules/core/genre_guards/cooking_guard.py:181` defines restaurant/competition requirement tables, while `modules/core/genre_guards/cooking_guard.py:500` to `modules/core/genre_guards/cooking_guard.py:506` keeps deep validation as base pass-through + summary.
- `modules/core/genre_guards/composer_guard.py:175` to `modules/core/genre_guards/composer_guard.py:183` defines activity requirements, while `modules/core/genre_guards/composer_guard.py:507` to `modules/core/genre_guards/composer_guard.py:513` similarly delegates deep validation to base result envelope.

**Confirmed Bugs**:
- none

**Risks**:
- Several domain-specific requirement tables are declared but not invoked in the inspected deep-validation path, leaving potential under-enforcement for domain mechanics.

**False Positives Excluded**:
- "요리/작곡 장르는 전용 guard가 없다" FP excluded because factory mapping clearly instantiates dedicated guard classes.

**Test Gaps**:
- Missing integration tests proving restaurant-tier/activity prerequisite tables affect actual reject/warn outcomes.

### Round 56 - Unspecified genre fallback behavior in guard factory

**Read Files**:
- `main_a.py`
- `modules/core/genre_guards/__init__.py`
- `modules/core/constants.py`

**Manual Inspection Evidence**:
- `main_a.py:2423` to `main_a.py:2607` constrains UI genre selection to predefined options and resolves a selected `type`.
- `main_a.py:914` passes selected genre type into `create_genre_guard(...)`.
- `modules/core/genre_guards/__init__.py:51` to `modules/core/genre_guards/__init__.py:53` silently falls back to `WuxiaGuard()` for unknown genre keys.

**Confirmed Bugs**:
- none

**Risks**:
- Unknown/mis-typed genre values outside the UI path can silently degrade to wuxia guard behavior instead of surfacing configuration drift explicitly.

**False Positives Excluded**:
- "UI에서 미정 장르 입력 시 즉시 크래시" FP excluded because UI picker bounds are fixed and guard factory has a defensive default branch.

**Test Gaps**:
- Missing guard-factory contract test that asserts warning/error telemetry on unknown genre keys instead of silent fallback.

### Round 57 - Guard chain order (Genre -> Work -> Style) and runtime asymmetry

**Read Files**:
- `modules/core/genre_guards/work_guard.py`
- `main_a.py`
- `modules/core/genre_guards/style_guard.py`

**Manual Inspection Evidence**:
- `modules/core/genre_guards/work_guard.py:7` documents the intended chain `GenreGuard -> WorkGuard -> StyleGuard`.
- `main_a.py:914` to `main_a.py:925` creates base genre guard and wraps it with `WorkGuard` when `work_guard.yaml` exists.
- `main_a.py:1427` to `main_a.py:1434` wraps `_guard` with `StyleGuard` only for director path, while `main_a.py:1440` to `main_a.py:1442` injects `self.sys.guard` (genre/work) into writer.

**Confirmed Bugs**:
- none

**Risks**:
- Writer and Director can operate on different guard stacks (writer without style wrapper), which can widen prompt-vs-validation expectation gaps.

**False Positives Excluded**:
- "guard 체인 순서가 Work->Genre로 역전된다" FP excluded because inspected initialization path applies wrappers in documented order for director.

**Test Gaps**:
- Missing parity test verifying writer/director guard stacks for projects with both `work_guard.yaml` and `style_guide` anchor.

### Round 58 - `martial_manager` line-564 divide-by-zero suspicion check

**Read Files**:
- `modules/core/martial_manager.py`
- `main_a.py`
- `modules/core/system.py`

**Manual Inspection Evidence**:
- `modules/core/martial_manager.py:553` to `modules/core/martial_manager.py:564` computes trend deltas by subtraction/formatting; no division path exists at the referenced tail segment.
- `modules/core/martial_manager.py:525` uses bounded range start `max(1, ep_num - window)` for manuscript traversal.
- `modules/core/system.py:39` wires `MartialManager` as runtime service; no alternate mathematical wrapper is injected.

**Confirmed Bugs**:
- none

**Risks**:
- none

**False Positives Excluded**:
- "martial_manager:564에서 0 나누기 발생" FP excluded because inspected expression at line 564 is a conditional return string, not arithmetic division.

**Test Gaps**:
- Missing edge test for `get_hud_trend(ep_num=1)` and sparse manuscript snapshots to confirm stable empty-trend behavior.

### Round 59 - `power_scaling` extreme input handling

**Read Files**:
- `modules/core/power_scaling.py`
- `main_a.py`
- `modules/domain/agents/director_auditor.py`

**Manual Inspection Evidence**:
- `modules/core/power_scaling.py:164` to `modules/core/power_scaling.py:169` normalizes/clamps input in `set_power(...)` to integer range 0..100.
- `modules/core/power_scaling.py:207` to `modules/core/power_scaling.py:240` `validate_growth(...)` receives `new_power` and directly computes `delta = new_power - current_power` without type normalization.
- `main_a.py:1570` to `main_a.py:1572` initializes `PowerScalingTracker` globally, indicating this utility can be called across pipeline diagnostics.

**Confirmed Bugs**:
- none

**Risks**:
- `validate_growth` can raise type errors on non-numeric `new_power` inputs (or unstable behavior on extreme non-clamped values) because unlike `set_power`, this path lacks normalization/guarding.

**False Positives Excluded**:
- "power_scaling은 모든 입력을 무제한 허용한다" FP excluded because `set_power` path explicitly clamps numeric values to 0..100.

**Test Gaps**:
- Missing robustness tests for `validate_growth` with `new_power` as string/None/NaN-like inputs and very large numeric magnitudes.

### Round 60 - Genre-based strategy selection branch wiring check

**Read Files**:
- `main_a.py`
- `modules/domain/agents/writer.py`
- `modules/domain/strategies/base_strategy.py`

**Manual Inspection Evidence**:
- `main_a.py:2423` to `main_a.py:2591` supports 10 genre selections and stores selected genre type.
- `main_a.py:1318` to `main_a.py:1377` constructs runtime agents directly (`Writer`, `Director`, etc.) with no strategy class instantiation path in the inspected initialization sequence.
- `modules/domain/agents/writer.py:285` to `modules/domain/agents/writer.py:300` applies genre-specific prompt additions via guard methods (`get_dungeon_rules_prompt`, `get_finance_rules_prompt`) instead of strategy object dispatch.

**Confirmed Bugs**:
- none

**Risks**:
- `modules/domain/strategies/*.py` appears decoupled from the active runtime path; future maintainers may assume strategy-branch behavior that is not actually executed.

**False Positives Excluded**:
- "장르 선택 자체가 Writer 분기 없이 완전히 무시된다" FP excluded because writer still branches on `self.genre` and guard-provided genre prompts.

**Test Gaps**:
- Missing integration test proving intended strategy-class loading behavior (or explicitly validating that guard-based branching is the sole supported path).

## Checkpoint - Crosscut Round 60

| Metric | Value |
|--------|-------|
| Cumulative Confirmed Bugs | 0 (P0: 0, P1: 0, P2: 0, P3: 0) |
| Cumulative Risks | 39 |
| Cumulative False Positives Excluded | 60 |
| Cumulative Test Gaps | 60 |
| Phase False-Positive Ratio | 60.6% (60 / (0+39+60)) |
| Consecutive Empty Rounds | 0 |
| Manual Evidence Compliance Rate | 100% (60/60 rounds) |
