# T08 Regression Gap Design

## Scope

- Audit existing Stage4 carryover / continuity / post-select / retry-hydration test coverage against the four bug shapes #58 calls out: institution naming drift, duplicated continuation beats, date drift, prior-failure replay.
- Map the bug shapes onto the actual seams (modules/functions) where a regression would manifest, so new tests target real boundaries instead of new ad-hoc helpers.
- Recommend specific new test names, fixtures, and target modules. Read-only — no test/code/docs writes outside this report.
- Out of scope: implementing tests, mutating runtime, restarting the 5-arc run, validating that #58 is fixed.

## Commands / Evidence

Local read-only inspection (commands shown verbatim; only the most relevant outputs summarized):

- `git ls-files tests/` (filtered for `stage4|continuity|carryover|preflight|episode_boundary|semantic_carryover|ep9|previous_attempt|hydrate|retry|post_select|reject|lineage|institution|continuation`) — confirmed the universe of relevant tests, including the 10 mandated ones plus `tests/test_continuity_canary.py`, `tests/test_stage4_orchestrator.py`, `tests/test_stage4_interview_round.py`.
- Read each of the 10 required test files end-to-end (or scoped scans for the 3,078-line `tests/test_stage4_context_builder.py`):
  - `tests/test_stage4_handoff_carryover_guardrail.py` (205 lines).
  - `tests/test_stage4_carryover_ceiling_handoff.py` (65 lines).
  - `tests/test_stage4_ep9_remediation.py` (195 lines).
  - `tests/test_stage4_context_builder.py` (3,078 lines, scoped via `Grep` for `institution|stale|lineage|previous_attempt|continuation|date|carryover|reject|post_select|cache|hydrate|retry`).
  - `tests/test_stage4_preflight_continuity.py` (128 lines).
  - `tests/test_stage2_stage3_episode_boundary_guardrail.py` (464 lines).
  - `tests/test_stage2_stage3_semantic_carryover_guardrail.py` (497 lines).
  - `tests/test_authoritative_continuity_projection.py` (75 lines).
  - `tests/test_continuity_pin_guard.py` (67 lines).
  - `tests/test_session_memory_envelope.py` (176 lines).
- Cross-checked the production seams those tests exercise:
  - `modules/core/stage4_interview_round.py:1180–1525` — `_classify_reject_bucket`, `_is_continuity_replay_reject`.
  - `modules/core/stage4_interview_round.py:2189–2469` — `_hydrate_stage4_previous_attempt_from_row`, `hydrate_persisted_stage4_previous_attempt`, including same-session/same-episode filters and PASS-skip.
  - `modules/core/stage4_reject_runtime.py:1252–1401` — `_build_reject_retry_snapshot` post-select branch and `prior_attempts` inheritance.
  - `modules/core/stage4_postselect_runtime.py:120–210` — bounded local-fix gate and post-select fingerprint.
  - `modules/core/stage4_orchestrator.py:939–1040` — `_preflight_validate_blueprint` and `apply_continuity_pins_fn` injection.
  - `modules/core/continuity_pin_guard.py:10–207` — `_TIME_BUCKET_PATTERNS`, `apply_continuity_pins`, and `opening_action_continuity_pin`.
  - `modules/core/continuity_canary.py:217–344` — `evaluate_continuity_canaries`, `merge_continuity_canary_reports` (canary IDs `date_drift`, `location_drift`, `dead_character_active_role`, `prior_failure_replay`).
  - `modules/core/episode_state_arbiter.py:985–996` — `institution_truths` projection field.
  - `modules/core/stage3_orchestrator.py:101–207` — `_STAGE3_INSTITUTION_SUFFIXES`, `_collect_stage3_current_arc_institution_mentions`.
- `git grep -l evaluate_continuity_canaries modules/ scripts/ tests/` — `continuity_canary` is currently called only by `scripts/run_auto_frontier_lag_harness.py` and itself; no production Stage4 runtime invocation.
- `git grep -l apply_continuity_pins modules/ scripts/ tests/` — pin guard is wired into `modules/core/stage3_orchestrator.py` and `modules/core/stage4_orchestrator.py`, but only in the Stage4 preflight path (pre-blueprint), not in post-select retry feedback.
- `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md:80–93,121` — confirms the bug surface ("institution naming and duplicated continuation beats", repeated POST_SELECT_CONFLICT through ep9).

## Findings

The four bug shapes from the dispatch break down against the existing test surface as follows.

### F1. Institution naming drift

- **Existing coverage.**
  - `tests/test_stage3_orchestrator.py` (`_collect_stage3_institution_mentions`, `_reconcile_stage3_entity_registry_with_draft_authority`) and `tests/test_stage3_blueprint_state_precision_guardrail.py` cover Stage3 reconciliation of organization names from draft authority.
  - `tests/test_continuity_pin_guard.py::test_apply_continuity_pins_replaces_proper_noun_from_previous_text` covers a single-quoted-token mismatch ("이클립스" → "아퀼라").
  - `tests/test_session_memory_envelope.py::test_build_stage4_session_memory_envelope_preserves_structured_truth_pin_items` covers `family=proper_noun_group` truth pin flow.
- **Gap.** No test exercises the case the handoff explicitly cites: a Stage4 retry where ep_n+1's blueprint or candidate manuscript reintroduces a stale institution name (e.g. "SW인베스트먼트") even though the authoritative current-arc institution (e.g. "한미증권 파생상품 데스크") has been recorded by `WorldStateManager` (`tests/test_stage4_ep9_remediation.py::test_world_state_snapshot_prefers_current_position_as_authoritative_role` exists for **role**, not institution). `_collect_stage3_current_arc_institution_mentions` and `episode_state_arbiter._normalize_progression_truth.institution_truths` have no end-to-end Stage4 test that asserts those institution truths actually reach the Stage4 mandatory context or trigger a `proper_noun_group` truth pin in `apply_continuity_pins`.
- **Why this matters for #58.** ep4–ep9 share a single arc; if Stage4's post-select truth-pin build doesn't fire when the current institution is already canon, Director may reject as POST_SELECT_CONFLICT but retry feedback does not actually carry the institution truth into the next round, so the LLM produces the same drift again.

### F2. Duplicated continuation beats

- **Existing coverage.**
  - `tests/test_continuity_pin_guard.py::test_apply_continuity_pins_marks_opening_action_reversal_against_previous_exit` and `tests/test_stage4_preflight_continuity.py::test_stage4_preflight_attaches_opening_action_continuity_pin_to_blueprint` cover the **blueprint-side** opening-action reversal pin (Stage4 preflight only).
  - `tests/test_stage4_orchestrator.py:2723–2779,3250` and `:2620–2660` cover `handle_reject_round_result` escalation when `contradiction_types=["opening_action_continuity"]`, and a `numeric_carryover_authority+opening_action_continuity` payload.
  - `tests/test_stage4_interview_round.py::test_post_select_continuity_conflict_downgrades_pass` and the firewall-promotes-patch tests cover `_is_continuity_replay_reject` membership for the `opening_action_continuity` contradiction key.
  - `tests/test_stage2_stage3_episode_boundary_guardrail.py::TestStopLineExpansion::test_ep1_stop_line_covers_all_future` covers Stage2/3 stop-line-future-eps prohibitions but at constraint-block level, not at Stage4 candidate level.
- **Gap.** No test covers a **manuscript-level** duplicated continuation beat: the Stage4 candidate text replays the previous episode's ending beat verbatim or near-verbatim, and Director either (a) misses it because `_is_continuity_replay_reject` only looks at `contradiction_types`/`firewall_reason` strings, or (b) catches it but the post-select retry guidance does not surface a manuscript-bearing fix scope (`reject_runtime._build_reject_retry_snapshot`). `_compose_director_work_focus_text` (modules/core/stage4_interview_round.py:1538) feeds prev_ending into the work-focus text but no test asserts that an n-gram-overlap or "동일 비트 반복" signal flows through the post-select retry guidance back to the next round.
- **Why this matters for #58.** ep5–ep8 each had one POST_SELECT_CONFLICT-then-PASS; ep9 had two POST_SELECT_CONFLICT and never landed. If continuation-beat duplication is detected as a Director-side reject but the runtime guidance keeps the same blueprint and same opening-scene wording, retries replay the duplicate.

### F3. Date drift

- **Existing coverage.**
  - `tests/test_continuity_canary.py::test_continuity_canaries_flag_date_location_dead_character_and_replay` exercises `evaluate_continuity_canaries` for `date_drift` (`2006-01-03` → `2006-01-01`) and `prior_failure_replay`. **However, the canary is currently only consumed by `scripts/run_auto_frontier_lag_harness.py`; production Stage4 does not call it.**
  - `tests/test_continuity_pin_guard.py::test_apply_continuity_pins_replaces_elapsed_time_bucket_from_arc_tactical` covers the relative-time bucket pin ("다음 날 오후" → "약 2주 후") but only via `_TIME_BUCKET_PATTERNS`, which has six relative buckets; no absolute-date or month-day patterns.
  - `tests/test_session_memory_envelope.py::test_build_stage4_session_memory_envelope_preserves_authoritative_continuity_projection` preserves `accepted_source_state.end_location` but not `time_flow`.
  - `tests/test_authoritative_continuity_projection.py::test_projection_summary_is_small_and_operational` confirms `time_flow` enters `accepted_source_fields`, but no test confirms it is loaded into Stage4 mandatory context for retries.
- **Gap.** No regression covers (a) absolute-date drift inside `apply_continuity_pins`, (b) date-drift canary running inside the Stage4 post-select pipeline, or (c) Stage4 carrying `accepted_source_state.time_flow` into a retry's truth pins. The `2026-04-26 frontier-lag-5arc-post-run-merge-audit.md:78–107` Jan1/Jan3 incident shape is therefore covered only at the canary unit level, not at the runtime level, and only after the live run already failed.
- **Why this matters for #58.** Director can reject for date drift (POST_SELECT_CONFLICT firewall), but if the retry feedback doesn't pin `time_flow`, the next candidate may pick a different wrong date and the same conflict family repeats.

### F4. Prior-failure replay

- **Existing coverage.**
  - `tests/test_continuity_canary.py::test_continuity_canaries_flag_date_location_dead_character_and_replay` covers the canary itself.
  - `tests/test_stage4_interview_round.py::test_hydrate_persisted_stage4_previous_attempt_reads_db_envelope_and_artifact`, `:test_hydrate_persisted_stage4_previous_attempt_skips_latest_pass_row`, `:test_hydrate_persisted_stage4_previous_attempt_filters_current_session` cover the DB-row → previous_attempt hydration including PASS-skip and `session_id` filtering.
  - `tests/test_stage4_orchestrator.py::test_handle_round_outcome_hydrates_persisted_previous_attempt_before_first_round` covers single-call hydration.
  - `tests/test_stage4_carryover_ceiling_handoff.py::test_build_common_writer_kwargs_threads_arc_data_for_carryover_ceiling_authority` confirms `cross_stage_authority_packet.v1` reaches writer kwargs.
- **Gap.** No regression covers:
  - cross-session prior-failure replay: a stale REJECT row from `session_id="sess-old"` is correctly skipped (existing test asserts return `{}`), but no test asserts that **Stage4 still produces a fresh attempt** in that situation, i.e. no silent freeze or empty `previous_attempt` chained downstream.
  - same-session, same-episode multi-round replay: ep_n is REJECT round 1 → REJECT round 2 → PASS in the **same** run. `prior_attempts[-3:]` slicing is implicit but not asserted to actually surface duplicated `conflict_contract.contradiction_types` repeated three times in a row, which is the operational shape #58 describes for ep9.
  - prior-failure-replay canary firing inside Stage4 (because the canary is unwired from production runtime).
  - retry-feedback merge collisions: when both `runtime_advisory` and `retry_directives` already mention a prior signature and the new round adds a third copy, that the merged feedback de-duplicates instead of growing unboundedly. Today the de-dup logic is in `_FW-1` block of `_build_retry_feedback_provenance` (modules/core/stage4_interview_round.py:1386–1400) but no targeted test asserts the order-of-operations.

### Cross-cutting findings

- **Canary unwired.** `evaluate_continuity_canaries` and `merge_continuity_canary_reports` are unit-tested but not integration-tested against `Stage4InterviewRound` or `Stage4PostSelectRuntime`. From the 5-arc handoff perspective this is the single biggest false-negative surface for #58: a deterministic tripwire exists for date_drift, location_drift, dead_character_active_role, and prior_failure_replay, but does not currently route into POST_SELECT_CONFLICT triage.
- **Pin guard scope.** `apply_continuity_pins` is invoked only in `_preflight_validate_blueprint` (Stage4) and `stage3_orchestrator`. The pin guard does not run on the **selected candidate manuscript** at post-select time, so manuscript-bearing date/proper-noun drift cannot be auto-pinned in retry feedback.
- **Institution truths weakly bound.** `episode_state_arbiter._normalize_progression_truth.institution_truths` projects truths but `tests/test_authoritative_continuity_projection.py` and `tests/test_stage4_context_builder.py` only assert that `accepted_source_state.end_location`/`time_flow`/`director_approved_bridges` reach the mandatory context. There is no test that `institution_truths` actually populate retry-side truth pins.

## Root-Cause Candidates

These are candidate hypotheses that the proposed regression tests should make falsifiable, not concluded root causes.

1. **Canary integration gap.** Continuity canaries exist but never enter the Stage4 reject-route path. POST_SELECT_CONFLICT classification therefore relies on Director string-matching plus `_is_continuity_replay_reject` markers. When the LLM phrases a duplicated beat in fresh prose, those markers can miss, and even when they fire, the subsequent retry guidance has no authoritative date/institution truth to pin against.
2. **Truth-pin coverage gap for institution and date.** The pin guard handles relative time buckets (`다음 날` etc.) and a single quoted-token swap. It does not handle absolute dates or institution suffix groups (`투자증권`, `자산운용`, `PB센터`, …) that already exist in `_STAGE3_INSTITUTION_SUFFIXES`.
3. **Manuscript-level duplication blindness at post-select.** Stage4 has a Director firewall for duplicated openings and a preflight pin against opening reversal, but no manuscript-level n-gram or beat-overlap signal at the moment a candidate is selected.
4. **Prior-failure feedback growing instead of converging.** The `_FW-1` directive de-dup keeps the most recent advisory, but the live run shows two consecutive POST_SELECT_CONFLICT on ep9 with the same conflict family. If contradiction_types/truth_pins recur with the same fingerprint, retry guidance is supposed to escalate (`_resolve_retry_lane_routing` TF-4 / TF-PATCH-GATE), but no end-to-end test asserts that escalation actually changes the writer-side blueprint or fix scope across rounds.

## Regression / Test Candidates

These are recommendations only — Director decides which to implement and where. Names follow project convention (`test_<unit>_<observable>_<expectation>`). Each entry lists a target module, a target seam, the proposed test file (preferring an existing file when scope matches), and the fixture style that matches today's test patterns (mock-based, no live API calls). Suggested fixtures reuse `_make_ctx()` patterns already present in target test files; new fixtures are flagged.

### R1. Institution naming drift

- `test_apply_continuity_pins_replaces_institution_suffix_from_arc_truth` — `tests/test_continuity_pin_guard.py`. Target: `modules/core/continuity_pin_guard.py::apply_continuity_pins`. Asserts that when `arc_tactical_text` contains "한미증권 파생상품 데스크" and the blueprint integrated_scenario contains "SW인베스트먼트 PB센터", the pin guard emits a `proper_noun_pin` (or new `institution_pin`) replacing the stale token. Fixture: pure data, no ctx.
- `test_stage4_postselect_truth_pin_uses_institution_truths_from_projection` — `tests/test_stage4_postselect_runtime.py` (NEW). Target: `modules/core/stage4_postselect_runtime.py::_build_post_select_conflict_contract` plus its caller chain. Asserts that when `episode_state_arbiter._normalize_progression_truth.institution_truths = ["한미증권 파생상품 데스크"]` and a candidate manuscript contains "SW인베스트먼트", the constructed `truth_pins` list includes `{family: "proper_noun_group", pin_key: "institution_name", expected: "한미증권…", observed: "SW인베스트먼트…"}`. Fixture: existing post-select payload builders.
- `test_build_mandatory_context_surfaces_institution_truths_from_progression_truth` — `tests/test_stage4_context_builder.py`. Target: `modules/core/stage4_context_builder.py::Stage4ContextBuilder.build_mandatory_context`. Asserts that the `[Authoritative Continuity Projection]` block surfaces `institution_truths` (currently only `time_flow`/`end_location` are asserted). Fixture pattern: identical to existing `test_build_mandatory_context_injects_authoritative_continuity_projection`.
- `test_world_state_snapshot_prefers_authoritative_institution_when_position_changed` — `tests/test_stage4_ep9_remediation.py`. Target: `modules/core/world_state.py::WorldStateManager.get_npc_role_snapshot` (sibling to the existing role test). Asserts that when `known_attrs.position.value` carries a new institution, the `authoritative_role`/`authoritative_role_source` keys reflect the new institution rather than the role-at-intro.

### R2. Duplicated continuation beats

- `test_apply_continuity_pins_flags_duplicated_continuation_beat_against_prev_ending` — `tests/test_continuity_pin_guard.py`. Target: `modules/core/continuity_pin_guard.py::apply_continuity_pins`. Asserts that when `previous_published_text` ends with a strong action sentence and the new blueprint `integrated_scenario` opens with a near-verbatim repetition of that sentence (>= 25-token overlap), a new finding `{type: "duplicated_continuation_beat_pin", before: <repeated span>, observed: <same span>, expected: "explicit transition or scene cut"}` is emitted. This expands the existing `opening_action_continuity_pin` shape but at sentence-overlap granularity rather than reversal pattern.
- `test_is_continuity_replay_reject_detects_duplicated_continuation_beat_marker` — `tests/test_stage4_interview_round.py`. Target: `modules/core/stage4_interview_round.py::_is_continuity_replay_reject`. Asserts that `contradiction_types=["duplicated_continuation_beat"]` (proposed new contradiction key) flips the helper to True without relying on Korean string heuristics. If the new contradiction key is rejected, fall back to asserting that `firewall_reason` containing `"duplicated continuation beat"` triggers True via the existing `continuity_markers` table.
- `test_reject_runtime_post_select_pins_duplicated_continuation_beat_into_truth_pins` — `tests/test_stage4_handoff_carryover_guardrail.py` (extend, fixtures already present). Target: `modules/core/stage4_reject_runtime.py::_build_reject_retry_snapshot` post-select branch. Asserts that when the previous round flagged `duplicated_continuation_beat`, the next-round `previous_attempt["truth_pins"]` carries the offending span and `previous_attempt["fix_pack"]["do_not_regress"]` includes "do not reopen with the same prior-ending sentence".
- `test_handle_reject_round_result_escalates_after_two_consecutive_duplicated_beat_rejects` — `tests/test_stage4_orchestrator.py`. Target: `modules/core/stage4_outcome_runtime.py::Stage4OutcomeRuntime.handle_reject_round_result` (already has `:2723` test for opening_action_continuity). Asserts that two consecutive REJECTs with the same contradiction_type cause `_apply_v75d_inplace_repair` to be called with a regenerate (not patch) lane, and that `bucket_streak`/`contradiction_type_streak` advance.

### R3. Date drift

- `test_apply_continuity_pins_replaces_absolute_date_from_arc_tactical` — `tests/test_continuity_pin_guard.py`. Target: `modules/core/continuity_pin_guard.py::apply_continuity_pins` (extend `_TIME_BUCKET_PATTERNS` with absolute-date matchers, e.g. `2006-01-03`, `1월 3일`). Asserts replacement when arc_tactical_text says "2006년 1월 3일 저녁" and blueprint says "2006년 1월 1일 저녁".
- `test_stage4_postselect_runtime_runs_continuity_canaries_against_selected_candidate` — `tests/test_stage4_postselect_runtime.py` (NEW or co-locate with R1). Target: a new integration seam in `modules/core/stage4_postselect_runtime.py` that calls `evaluate_continuity_canaries(projection=…, candidate=…, dead_characters=…, prior_failure_signatures=…)` and merges findings into POST_SELECT_CONFLICT route. Asserts the canary report enters `conflict_contract.canary_findings` and `truth_pins` for `date_drift`/`location_drift`/`dead_character_active_role`/`prior_failure_replay`. **Note**: this test will fail until the canary is wired into Stage4. That is the purpose — make the integration gap visible.
- `test_session_memory_envelope_preserves_time_flow_truth_for_retry_hydration` — `tests/test_session_memory_envelope.py`. Target: `modules/core/session_memory_envelope.py::build_stage4_session_memory_envelope`. Asserts that when `advisory_flags["authoritative_continuity_projection"]["accepted_source_state"]` carries `time_flow`, the envelope surfaces it under a `truth_pins["time_flow"]` (or `carryover_refs["time_flow"]`) so `_hydrate_stage4_previous_attempt_from_row` can reload it without re-querying the projection.
- `test_continuity_canary_report_routes_to_director_review_on_review_required` — `tests/test_continuity_canary.py`. Target: `modules/core/continuity_canary.py::merge_continuity_canary_reports` plus a new "router" seam (or inline assertion in the integration test). Asserts that `status=review_required` findings carry `judgment_authority="director_llm"` and trip `requires_director_review=True` even when only one of N parallel candidate reports is review_required. Reinforces the existing AGENTS.md "Python-judgment limit" rule.

### R4. Prior-failure replay

- `test_hydrate_persisted_stage4_previous_attempt_skips_cross_session_returns_empty_without_pollution` — `tests/test_stage4_interview_round.py`. Target: existing `:test_hydrate_persisted_stage4_previous_attempt_filters_current_session`. Extension: assert that the **subsequent** `Stage4InterviewRound.run` call still produces a normal first-round attempt with empty `prior_attempts` and **no** session_id leakage from the stale row's advisory_flags. Ensures the cross-session filter does not leave half-merged state.
- `test_hydrate_persisted_stage4_previous_attempt_carries_three_round_history_with_distinct_fingerprints` — `tests/test_stage4_interview_round.py`. Target: `modules/core/stage4_interview_round.py::_hydrate_stage4_previous_attempt_from_row` `prior_attempts[-3:]` block. Asserts that when 4 prior REJECT rows exist for the same `(arc=1, ep=9, session_id=current)`, the hydrated `previous_attempt["prior_attempts"]` keeps the latest 3 in chronological order and each carries its own `attempt_key`/`reject_bucket` without collapsing duplicates.
- `test_post_select_retry_feedback_dedupes_repeated_prior_failure_signature` — `tests/test_stage4_handoff_carryover_guardrail.py` (extend) or `tests/test_stage4_advisory_escalation_seam.py`. Target: `modules/core/stage4_interview_round.py::_build_retry_feedback_provenance` `_FW-1` directive de-dup. Asserts that when round 0 advisory and round 1 advisory both contain the same persistent retry directive line (e.g. "post-select truth-pin reroute: institution_name=한미증권"), the merged round-2 feedback shows it once, and that round-2 advisory ordering keeps the most recent advisory at the bottom.
- `test_outcome_runtime_qr8_logs_prior_failure_replay_when_canary_signature_recurs` — `tests/test_stage4_ep9_remediation.py` (extend, mirrors existing QR-7 test). Target: `modules/core/stage4_outcome_runtime.py::Stage4OutcomeRuntime._apply_reject_score_trend_advisory` (or sibling). Asserts that when the canary `prior_failure_replay` finding repeats across two consecutive rounds, an operator-visible advisory line tagged `[QR-8]` is logged with `stage="stage4"`, `ep_num=9`, `attempt_key="s4:ep9:arc0:aN"`. **Note**: requires R3 integration; couples R3 and R4.
- `test_handle_round_outcome_hydrates_persisted_previous_attempt_when_session_match_yields_only_pass` — `tests/test_stage4_orchestrator.py`. Target: `modules/core/stage4_orchestrator.py::Stage4Orchestrator._handle_round_outcome`. Asserts that when `hydrate_persisted_stage4_previous_attempt` returns `{}` because the latest row was PASS, the orchestrator does **not** reuse a prior arc's `previous_attempt` and starts fresh. Closes a gap not covered by `:test_hydrate_persisted_stage4_previous_attempt_skips_latest_pass_row`, which only checks the helper itself.

### R5. Cross-shape integration / closure

- `test_stage4_postselect_runtime_emits_unified_truth_pin_block_for_institution_date_and_continuation_drift` — `tests/test_stage4_postselect_runtime.py` (NEW). Target: the same integration seam as R3's canary test. Asserts that one POST_SELECT_CONFLICT round can carry institution + date + duplicated-continuation truth pins simultaneously, that the merged `conflict_contract.truth_pins` is unique by `(family, pin_key)`, and that the resulting `fix_scope` is `full` (not patch) when more than one family fires.
- `test_stage4_orchestrator_post_select_routes_canary_findings_into_director_advisory_packet` — `tests/test_stage4_orchestrator.py`. Target: `modules/core/stage4_orchestrator.py` + `modules/core/stage4_director_runtime.py`. Asserts that canary findings reach `director_result.advisory_flags["continuity_canary_report"]` and that `_is_continuity_replay_reject` returns True when canary `status="review_required"`, even if Director's `firewall_triggered` is False.

Fixture notes:

- The Stage4 mocking pattern from `tests/test_stage4_handoff_carryover_guardrail.py::_make_ctx`/`_make_round_ctx` is the right baseline — small, no live agents, deterministic.
- For `tests/test_continuity_pin_guard.py` extensions, no new fixtures are needed; the module is pure-Python.
- For the new `tests/test_stage4_postselect_runtime.py` (R1/R3/R5), reuse the post-select payload builders already exercised in `tests/test_stage4_advisory_escalation_seam.py:679–776` and `tests/test_stage4_interview_round.py::test_hydrate_persisted_stage4_previous_attempt_reads_db_envelope_and_artifact:3088`.
- All recommended tests are mock-based and shard-safe under the AGENTS.md `Pytest Memory Rule`. None require pytest-xdist, network, or live API. Run order suggestion: `tests/test_continuity_pin_guard.py`, `tests/test_continuity_canary.py`, `tests/test_session_memory_envelope.py`, `tests/test_stage4_postselect_runtime.py` (NEW), `tests/test_stage4_handoff_carryover_guardrail.py`, `tests/test_stage4_ep9_remediation.py`, `tests/test_stage4_orchestrator.py`.

## Dependencies On Other Terminals

- **T02 (post-select route).** Whether `POST_SELECT_CONFLICT` is over-broad or correctly classified will determine whether R1/R2/R3 should propose new contradiction keys (e.g. `duplicated_continuation_beat`) or reuse existing ones (`opening_action_continuity`, `space_continuity`). This T08 report assumes additive keys.
- **T03 (Stage3→Stage4 handoff).** If T03 confirms that institution truths or arc-end `time_flow` already enter Stage4 via `cross_stage_authority_packet`, then R1 and R3 can skip the projection-construction step and target only the consumer side. If T03 finds the upstream packet missing, R1/R3 should expand to include packet-side regression assertions in `tests/test_stage3_orchestrator.py` or `tests/test_three_phase_blueprint_runtime.py`.
- **T04 (continuity authority carriers).** If T04 confirms `episode_state_arbiter.institution_truths` and `authoritative_continuity_projection.time_flow` are intended authority carriers, R1's `test_build_mandatory_context_surfaces_institution_truths_from_progression_truth` and R3's `test_session_memory_envelope_preserves_time_flow_truth_for_retry_hydration` are well-targeted. If T04 finds a different authority carrier, redirect those tests accordingly.
- **T05 (memory/cache side effects).** R3's `test_session_memory_envelope_preserves_time_flow_truth_for_retry_hydration` should not run before T05 confirms whether `truth_pins` vs `carryover_refs` is the correct surface key. Today both exist in `build_stage4_session_memory_envelope`.
- **T06 (retry hydration replay).** R4's tests overlap directly with T06. If T06 reveals additional hydration entry points beyond `_hydrate_stage4_previous_attempt_from_row`, add sibling tests there.
- **T07 (context-cache lineage).** `tests/test_stage4_context_builder.py::test_tier12_skips_treatment_genre_ext_when_cached_arcs_lineage_stale` is the closest precedent. If T07 finds a stale-cache injection path that bypasses lineage, R1 should add a parallel `test_tier12_skips_stale_institution_when_cached_arcs_lineage_stale`.
- **T09 (artifact truth).** R2's duplicated-continuation-beat test should use one real ep_n/ep_n+1 sentence pair surfaced by T09 as a fixture (verbatim, redacted to a tiny excerpt) so the assertion ties to the live ep4–ep9 shape rather than synthetic strings.
- **T10 (synthesis).** If T10 recommends "tests first" before any source patch, R1–R5 form a coherent first wave. If T10 recommends "execution SSOT first", T08's recommendations should be referenced by ID (R1.x, R2.x, …) inside the SSOT and not implemented standalone.

## Open Questions

- Should `duplicated_continuation_beat` be a new `contradiction_type` or should it be a refinement under `opening_action_continuity` / `scene_overlap`? Director scope decision (T02 should resolve).
- Is `evaluate_continuity_canaries` intended to be production runtime or stays as a post-run audit harness? The 5-arc handoff treats it as a tripwire; the codebase wires it only into `scripts/run_auto_frontier_lag_harness.py`. R3/R5 assume Stage4 integration; if Director rules canaries stay audit-only, R3/R5 should re-target the audit harness instead.
- Is the post-select `truth_pin` payload schema authoritative for institution and date families? `tests/test_session_memory_envelope.py::test_build_stage4_session_memory_envelope_preserves_structured_truth_pin_items` covers `family="proper_noun_group"`; date-family pins have no schema test. Recommend Director ratify a `family` taxonomy before R1/R3 land.
- For prior-failure-replay deduplication, is the `_FW-1` window of "last round only" the right policy, or should `prior_attempts[-3:]` be considered when generating retry directives? Today the two paths run independently. R4's signature-de-dup test will surface this contradiction.

## Closure Recommendation

This terminal is investigation-only. Recommended closure path:

1. T08 stops here. No tests are written, no source is patched, no docs outside this report are touched.
2. Wait for T01–T07 and T09 to complete so T10 synthesis can rank R1–R5 against the live evidence shape. R1 and R3 are likely the highest-leverage candidates because they target the two named bug shapes ("institution naming" and "date drift") that have explicit handoff doc citations and a clean test surface.
3. After T10, if Director endorses an execution SSOT for #58, that SSOT should reference R1–R5 by ID and decide which to implement before any code change. Each R-item names a specific `test_*` function and a specific module/seam; that is the implementation contract.
4. Implementation must respect AGENTS.md `Pytest Memory Rule` — run new tests as targeted shards, not as a full suite. Suggested smoke order: `tests/test_continuity_pin_guard.py -> tests/test_continuity_canary.py -> tests/test_stage4_postselect_runtime.py (NEW) -> tests/test_stage4_handoff_carryover_guardrail.py -> tests/test_stage4_ep9_remediation.py -> tests/test_stage4_orchestrator.py`.
5. Do **not** treat any newly green test as proof that #58 is fixed. AGENTS.md mandates Director judgment for narrative-quality conclusions, and R3/R5 will only flip green once `evaluate_continuity_canaries` is wired into runtime — that wiring itself is a Director-level contract decision.

Estimated operational confidence in the gap inventory and the recommended R-set: ~80%. Confidence is bounded by (a) only sampling 10 of ~40 relevant test files in depth, (b) not yet seeing T02/T03/T04/T06 conclusions, and (c) not having sampled live ep4–ep9 manuscript artifacts (T09 territory).
