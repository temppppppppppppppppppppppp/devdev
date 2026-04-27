# T06 Retry Hydration And Prior-Failure Replay

## Scope

- Issue: GitHub #58 — Stage4 POST_SELECT_CONFLICT carryover drift across 5-arc runs
  (institution naming + duplicated continuation beats).
- Lane: Terminal T06 — read-only audit of the retry loops, previous-attempt
  hydration paths, and prior-failure replay surfaces in Stage 4.
- Sources audited:
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_retry_runtime.py`
  - `modules/core/stage4_reject_runtime.py`
  - `modules/core/stage4_orchestrator.py`
  - `modules/core/db_manager.py`
  - `modules/core/failure_analyzer.py`
  - `modules/core/logging_keys.py`
  - `modules/domain/agents/chief_writer.py` (writer-side patch path)
  - Tests: `tests/test_stage4_interview_round.py`,
    `tests/test_stage4_handoff_carryover_guardrail.py`,
    `tests/test_stage4_carryover_ceiling_handoff.py`,
    `tests/test_stage4_ep9_remediation.py`
- Out of scope: edits to source/docs/DB/git, narrative-side artifacts, other
  terminal lanes.

The audit traces (a) how a failed Stage 4 attempt becomes a `previous_attempt`
dict, (b) how that dict feeds the next round/episode, and (c) which surfaces can
re-inject prior-failure text or feedback into the new attempt.

## Commands / Evidence

Evidence was gathered with read-only Grep + Read against the production tree.
Key search anchors:

- `git grep -n -i -E "previous_attempt|prev_attempt|prior_attempt|hydrate|rehydrat|replay" --
  modules/core/stage4_interview_round.py modules/core/stage4_retry_runtime.py
  modules/core/stage4_reject_runtime.py modules/core/stage4_orchestrator.py
  modules/core/db_manager.py modules/core/failure_analyzer.py`
- `git grep -n -i -E "POST_SELECT_CONFLICT|post_select_conflict" -- modules/core/`

Anchor citations (file:line — what it shows):

- `modules/core/stage4_interview_round.py:2189–2486` — `hydrate_persisted_stage4_previous_attempt`
  and `_hydrate_stage4_previous_attempt_from_row`. Pulls the latest non-PASS
  Stage 4 row for the same `(arc, episode, session)`, loads `best_manuscript`
  via `_load_stage4_attempt_artifact_text(artifact_path)`, and rebuilds a
  `previous_attempt` dict (rejection_reason, fix_scope, fix_pack,
  conflict_contract, reuse_contract, truth_pins, prior_attempts, etc.).
- `modules/core/stage4_interview_round.py:2096–2121` —
  `_load_stage4_attempt_artifact_text`. Reads the failed attempt's saved
  manuscript file from disk (UTF-8, with utf-8-sig fallback). No content
  filtering or scrubbing.
- `modules/core/stage4_interview_round.py:2340–2342` — hydration prefers
  `scope_authority.get("fix_scope")` > `attempt_row.get("fix_scope")` >
  `retry_surface.get("fix_scope")` for the resumed `fix_scope`. The first wins
  when present.
- `modules/core/stage4_interview_round.py:4553` — `prev_manuscript =
  previous_attempt.get("best_manuscript", "")` is the entry point that turns
  the persisted/in-memory failed text into the next round's patch source.
- `modules/core/stage4_orchestrator.py:1794–1822` —
  `_hydrate_round_loop_resume_state` runs once per `_handle_round_outcome`
  (per episode). If `loop_state.previous_attempt` is empty, it pulls from
  `hydrate_persisted_stage4_previous_attempt` and also seeds
  `loop_state.director_feedback` from the prior session's
  `feedback_provenance.merged_feedback / merged_director_feedback /
  rejection_reason`.
- `modules/core/stage4_orchestrator.py:1896–1922` — exhaustion path can adopt
  `previous_attempt["best_manuscript"]` (the last *rejected* candidate) as the
  final episode manuscript when `_allow_stage4_best_manuscript_adoption()` is
  true, gated by `get_int_input` with `default=2 (skip)` but configurable.
- `modules/core/stage4_retry_runtime.py:1185–1368` —
  `_resolve_retry_lane_routing`. Decides `use_inplace`, `use_patch`,
  `force_patch` based on `prev_manuscript`, `reject_bucket`, `fix_scope`,
  `round_num <= 1`. `force_patch` line 1305–1312:

      force_patch = (
          patch_enabled
          and prev_manuscript
          and reject_bucket == "post_select_conflict"
          and fix_scope != "full"
          and round_num <= 1
          and not _consecutive_empty_patch
      )

  This is the explicit POST_SELECT_CONFLICT replay-via-patch surface.
- `modules/core/stage4_retry_runtime.py:144–234` —
  `_should_allow_bounded_post_select_patch_retry`. Allows a *bounded local
  patch* on a POST_SELECT_CONFLICT REJECT even when `fix_scope == "full"`,
  as long as `conflict_contract.bounded_local_fix_hint` is set, no
  `rewrite_required_reasons`, and effective conflict types are within the
  continuity / movement / location / facing / dialogue /
  opening_action_continuity set. Excludes `proper_noun`, `history`, and
  `proper_noun_group` truth-pin families.
- `modules/core/stage4_retry_runtime.py:1465–1470` —
  `chief_writer.patch_with_feedback(original_manuscript=prev_manuscript,
  previous_attempt=previous_attempt, attempt_number=round_num + 1)`. This is
  where the prior-attempt text is handed back to the writer.
- `modules/domain/agents/chief_writer.py:2240–2280` —
  `_build_patch_with_feedback_section`. Embeds the prior manuscript
  (head-truncated to 150 000 chars / 20 000 head chars) into the prompt and
  instructs the model to keep the rest as-is. This is the literal replay of
  the failed manuscript body into the next attempt.
- `modules/core/stage4_reject_runtime.py:1243–1407` —
  `_build_reject_retry_snapshot`. After REJECT, builds the next round's
  `previous_attempt`. Sets `best_manuscript` from the rejected candidate
  (line 1331), inherits `prior_attempts` history, copies `fix_pack`,
  `conflict_contract`, `reuse_contract`, `truth_pins`, `truth_pin_items`,
  `repair_contract`, `scope_authority`, `fix_pack_origin` from the prior
  `previous_attempt` via `_build_stage4_retry_contract_carryover_fields`.
- `modules/core/stage4_reject_runtime.py:1444–1455, 1507–1519` — runtime
  promotes `reject_bucket` to `post_select_conflict` when `gate_basis ==
  "post_select_conflict"`, then forces `resolved_fix_scope = "full"`. This is
  the in-memory guardrail that *should* keep `force_patch` from firing on
  the next round of the *same* loop.
- `modules/core/stage4_reject_runtime.py:1806` — when persisting the reject
  artifact, `artifact_payload = (previous_attempt or {}).get("best_manuscript",
  "") or prev_manuscript`. This is a fallback that can write hydrated /
  prior-session text into the *new* row's artifact file.
- `modules/core/stage4_reject_runtime.py:615–682` —
  `_merge_reject_sink_source` and `_enrich_reject_gate_semantics` carry the
  prior `fix_pack`, `repair_contract`, `scope_authority`, `scope_origin`,
  `fix_pack_origin`, `conflict_contract`, `reuse_contract` forward into the
  next snapshot. `_enrich_reject_gate_semantics` deep-copies the prior
  `reuse_contract` (line 681) onto the next round's `gate_semantics`.
- `modules/core/db_manager.py:2806–2849` — `get_stage_attempts_for_arc`. The
  `session_id` filter is applied **only when** `session_id` is a non-empty
  string. When the caller cannot resolve a session id, the query returns
  every session's rows for the arc (subject only to the limit).
- `modules/core/logging_keys.py:4–34` — `resolve_logging_session_id` returns
  `None` when no `metrics_session_id`/`session_id` attribute is set on the
  current project. MagicMock-heavy unit tests deliberately fall through to
  `None`; live runtime is only safe if `current_project.metrics_session_id`
  is populated by the bootstrap.
- `modules/core/stage4_interview_round.py:2432–2456` — hydration calls
  `getter(arc, stages=(4,), limit=12, session_id=session_id)` only when
  session_id is truthy; otherwise calls `getter(arc, stages=(4,), limit=12)`
  with no session filter, then filters `same_episode_rows` by `ep_num` only.
  No second-pass session filter is applied in the no-session-id branch.
- `modules/core/stage4_interview_round.py:2417–2425` — the public
  `hydrate_persisted_stage4_previous_attempt` short-circuits if the caller
  already passed a non-empty `previous_attempt`. Cross-session pollution
  therefore happens primarily on cold resume / first round of an episode.
- `modules/core/stage4_interview_round.py:1484` and
  `modules/core/stage4_reject_runtime.py:1450–1468` — `_is_continuity_replay_reject`
  + the `[A-4 continuity replay]` notice. When the firewall REJECTs a
  continuity replay, the reject_runtime **forces** `fix_scope = "full"`,
  which is the intended block on patch-mode reuse for replay drift.
- `tests/test_stage4_interview_round.py:3220–3322` — confirms the hydration
  tests expect:
    1. `best_manuscript` is restored from the rejected artifact.
    2. `reject_bucket = "post_select_conflict"` and `fix_scope = "full"`
       round-trip through hydration.
    3. PASS rows skip hydration.
    4. Stale-session rows are dropped — *only when* the current project has
       `metrics_session_id` set (`test_hydrate_persisted_stage4_previous_attempt_filters_current_session`).
- `tests/test_stage4_handoff_carryover_guardrail.py:114–205` — confirms
  POST_SELECT_CONFLICT guidance escalates to full rewrite *and* the snapshot
  drops praise-first signals (selection_reason, open_review, fix_pack)
  unless the bounded local fix-pack contract holds. `fix_pack == {}` is the
  expected post-elision state.

## Findings

### F1. Hydrated previous-attempt rebuilds the rejected manuscript on disk-load

`hydrate_persisted_stage4_previous_attempt` reads the latest non-PASS Stage 4
row for `(arc, episode)` and loads its `artifact_path` content into
`payload["best_manuscript"]` (`stage4_interview_round.py:2189–2486`). The
full `previous_attempt` envelope is restored, including `conflict_contract`,
`reuse_contract`, `truth_pins`, `truth_pin_items`, `fix_pack`,
`scope_authority`, and the merged `feedback_provenance`. There is no
content-side scrubbing of the rehydrated manuscript text.

This is the primary surface where a prior session's failed manuscript becomes
visible to the new attempt loop.

### F2. Per-round in-memory `best_manuscript` is the rejected candidate verbatim

`_build_reject_retry_snapshot` (`stage4_reject_runtime.py:1324–1369`)
unconditionally sets:

    "best_manuscript": selected_candidate.get("manuscript", "")

That snapshot is then pushed back as `loop_state.previous_attempt` by the
orchestrator (`stage4_orchestrator.py:1782`), and `_run_generation_phase`
reads `prev_manuscript = previous_attempt.get("best_manuscript", "")`
(`stage4_interview_round.py:4553`). The next round therefore holds the
exact text of the rejected candidate, with no normalization or
content-class filtering applied.

### F3. Patch-mode replays the failed body into the next attempt

`patch_with_feedback` (`chief_writer.py:2324–2387`) and the
`_build_patch_with_feedback_section` helper (`chief_writer.py:2240–2280`)
embed `original_manuscript = prev_manuscript` into the writer prompt with
`smart_truncate(... max_chars=150_000, head_chars=20_000)` and instruct
the model to **preserve** the original body and only apply the
`fix_pack` / director feedback edits. Anything the surface `fix_pack`
does not target (e.g. an institution name appearing in the middle of the
preserved body, or the duplicated continuation beat that opens the
chapter) is reproduced verbatim into the new attempt.

This is the most direct replay vector for "duplicated continuation beats /
repeated institution naming drift".

### F4. POST_SELECT_CONFLICT `force_patch` for `round_num <= 1`

`_resolve_retry_lane_routing` (`stage4_retry_runtime.py:1305–1340`)
explicitly enables a *forced* patch lane for the first two rounds when:

    reject_bucket == "post_select_conflict"
    AND prev_manuscript truthy
    AND fix_scope != "full"
    AND round_num <= 1

Combined with F3, this guarantees patch-mode replay of the failed body
whenever a POST_SELECT_CONFLICT REJECT is observed with a non-full
fix_scope and a non-empty `prev_manuscript`. The reject-runtime guard
(`stage4_reject_runtime.py:1507–1519`) widens `resolved_fix_scope` to
`"full"` for `post_select_conflict`, which *should* defuse `force_patch`
inside the same loop. F5 and F6 below describe the slip lanes.

### F5. Hydration prefers `scope_authority.fix_scope` over `attempt_row.fix_scope`

`_hydrate_stage4_previous_attempt_from_row` (line 2340–2342) resolves the
hydrated `fix_scope` as:

    str(scope_authority.get("fix_scope")
        or attempt_row.get("fix_scope")
        or retry_surface.get("fix_scope")
        or "")

`scope_authority` comes from `advisory_flags["scope_authority"]`, which
the reject path persists from `gate_bundle.scope_authority`
(`stage4_reject_runtime.py:1791`). That bundle is enriched from the
prior round's `gate_semantics`, which carries the **director's**
authoritative `fix_scope` (e.g. `inplace` / `partial`) — not the
runtime-widened `"full"` that the reject_runtime later writes into the DB
column.

Concretely: a `post_select_conflict` REJECT row can land in
`stage_attempts` with `fix_scope = "full"` *and* with
`advisory_flags.scope_authority.fix_scope = "inplace" | "partial"`. On
resume, the hydration restores `fix_scope = "inplace"` and the new
`force_patch` evaluation passes — the very next round on the resumed
episode patches the disk-loaded prior manuscript.

This is a strong candidate for the EP6/EP8/EP9 carryover drift in the
referenced 5-arc handoff log.

### F6. Bounded post-select patch lane allows `fix_scope == "full"` patching

`_should_allow_bounded_post_select_patch_retry`
(`stage4_retry_runtime.py:144–234`) carves out a "bounded local fix" path
that is taken even when `fix_scope == "full"`. It requires
`conflict_contract.bounded_local_fix_hint == True` and effective conflict
types within `{continuity, timeline, movement, location, facing,
dialogue, opening_action_continuity}`, and excludes `proper_noun /
history / proper_noun_group` families.

Two structural risks:

1. The exclusion set targets `proper_noun` *family*. Institution-name drift
   that gets classified as `entity_ref` `local_phrase` `local_sentence`
   (`target_kind` allowed list line 198) instead of as `proper_noun`
   passes the gate and gets bounded-patched. The classification depends
   on upstream `truth_pin_items.family` and `conflict_contract.contradiction_types`
   accuracy — an upstream miss leaks straight into this lane.
2. `opening_action_continuity` is in the *allowed* effective-types set.
   A duplicated-continuation-beat conflict that the firewall labels as
   continuity (rather than as `history`) flows through bounded-patch,
   which then patches the prior body — exactly the failure mode the
   issue describes.

### F7. Cross-session contamination when `session_id` is unavailable

`hydrate_persisted_stage4_previous_attempt` (line 2432–2456) calls the DB
getter without `session_id` whenever `resolve_logging_session_id(...)` is
falsy. The DB getter then drops the `WHERE session_id = ?` clause
entirely (`db_manager.py:2831–2833`), and the in-Python filter only
matches `ep_num`. A prior session's POST_SELECT_CONFLICT row for the
same arc / episode can therefore become the new session's seed.

The unit test `test_hydrate_persisted_stage4_previous_attempt_filters_current_session`
documents the *intended* filter, but only proves it for the case where
`metrics_session_id` is already set on the project. The no-session-id
branch is not exercised.

### F8. Rejected-artifact persistence falls back to hydrated text

`_record_reject_attempt_artifact` (`stage4_reject_runtime.py:1806`)
chooses the artifact body as:

    artifact_payload = (previous_attempt or {}).get("best_manuscript", "")
                       or prev_manuscript

If the *new* round produced an empty-candidate REJECT, both
`previous_attempt.best_manuscript` and `prev_manuscript` resolve to the
hydrated / prior-round manuscript. That text is then written to the
current row's `artifact_path` and becomes a valid hydration source for
any future resume — laundering a stale failed manuscript into a row that
*looks* like it belongs to this session.

### F9. Director-feedback replay through resume seeding

`_hydrate_round_loop_resume_state` (`stage4_orchestrator.py:1812–1821`)
seeds `loop_state.director_feedback` from
`hydrated["feedback_provenance"]["merged_feedback"] |
hydrated["merged_director_feedback"] | hydrated["rejection_reason"]`.

The merged feedback frequently contains directive lines such as
`[Conflict-first retry] ... authoritative carryover 기준 재작성으로 처리하세요`
(`stage4_reject_runtime.py:593–597`) and
`[A-4 continuity replay] 직전 화와 충돌하는 frontier/연속성 신호가
방화벽 REJECT로 재발했습니다.` (line 1459). On a fresh round 0 ensemble
generation those directives steer the writer toward the same opening
choice that was already a continuity conflict — a self-fulfilling
replay even before any patch-mode is engaged.

### F10. Loop exhaustion adopts the failed `best_manuscript`

`_finalize_round_outcome_loop` (`stage4_orchestrator.py:1898–1922`) lets
the operator (or autonomous default) accept the last failed
`previous_attempt["best_manuscript"]` as the episode's final manuscript
when `_allow_stage4_best_manuscript_adoption()` returns true. Default
`get_int_input` is `2 (skip)`, but autonomous flows can override
`_get_stage4_exhaustion_default_choice()`. When taken, the rejected
text becomes the next-episode `prev_text` upstream — a one-step replay
that propagates carryover drift downstream rather than within the loop.

## Root-Cause Candidates

Ranked by my read of how cleanly each path explains the EP6–EP9
POST_SELECT_CONFLICT carryover drift symptom (institution naming +
duplicated continuation beats):

1. **F5 — `scope_authority.fix_scope` shadowing the runtime widening.**
   Highest-confidence vector. Rationale:
   - The reject_runtime widens `fix_scope` to `"full"` only on the
     in-memory snapshot and the `stage_attempts.fix_scope` column. The
     `advisory_flags.scope_authority` payload reflects the original
     director judgement (often `inplace`/`partial`).
   - On *any* resume (including resume *within* the same session if the
     loop_state previous_attempt has been cleared, or across sessions),
     the hydrated `fix_scope` is the director-original value, which makes
     `force_patch` (F4) fire on round 0–1 against the disk-loaded prior
     manuscript (F3).
   - Matches the EP9 "two POST_SELECT_CONFLICT rejects, no PASS" trail
     because the second reject is a patch over the first reject's body.

2. **F6 — Bounded post-select patch lane misclassification.**
   The bounded lane was designed to keep narrow continuity fixes off the
   full-rewrite hot path, but its exclusion logic is purely contract /
   family driven. If upstream classification mislabels institution-name
   drift as `entity_ref / local_phrase / local_sentence` instead of as
   `proper_noun_group`, or marks a duplicated continuation beat as
   `opening_action_continuity` (which is *allowed*), patch-mode runs on
   the failed body and reproduces the drift.

3. **F3 + F4 combined — patch lane preserves any non-targeted drift.**
   Once patch-mode is taken (whether via F5, F6, or a non-`post_select_conflict`
   `partial` REJECT), `_build_patch_with_feedback_section` instructs the
   model to keep the rest of the body intact. Anything that the reject's
   `fix_pack.must_fix / patch_targets / do_not_regress` did not name is
   preserved verbatim — including institution names already wrong and
   continuation beats already duplicated.

4. **F9 — Director-feedback replay on resume.** Even when the body is
   fresh, the prior session's `[Conflict-first retry]` /
   `[A-4 continuity replay]` lines steer the new round 0 toward the same
   opening structure that was rejected. This is enough to reproduce the
   continuity conflict on the first try post-resume; F1+F3+F4 then turn
   it into a patch-replay loop on rounds 1–2.

5. **F7 — Cross-session hydration without session_id.** Lower-likelihood
   in steady-state but a clear contamination route for any run where
   `current_project.metrics_session_id` is not yet bound at the moment
   `_hydrate_round_loop_resume_state` runs (e.g. very early after
   project re-bind, or if metrics bootstrap fails).

6. **F8 — Reject-artifact fallback laundering.** Lower-likelihood as a
   first-cause, but a *chronification* path: once any of the routes
   above produces a stale-text artifact under the current session_id,
   F8 ensures it persists across subsequent resumes.

7. **F10 — Exhaustion best_manuscript adoption.** Cross-episode rather
   than intra-episode. Less likely to explain the within-episode
   POST_SELECT_CONFLICT chain, but matches the broader "carryover
   mistake" framing if accepted-from-failure becomes downstream
   `prev_text`.

## Regression / Test Candidates

All proposed tests are read-only audit suggestions; this terminal does
not author or commit code. Suggested coverage to add (caller's
discretion which terminal owns them):

1. **F5 regression:** assert that
   `_hydrate_stage4_previous_attempt_from_row` returns
   `fix_scope == "full"` for any row where
   `attempt_row["fix_scope"] == "full"` *or*
   `gate_semantics.gate_basis == "post_select_conflict"` *or*
   `attempt_row.failure_category == "POST_SELECT_CONFLICT"`, regardless
   of `advisory_flags.scope_authority.fix_scope`. Failing fixture:
   craft a row with `fix_scope="full"` and
   `advisory_flags={"scope_authority":{"fix_scope":"inplace"}}`.

2. **F4 regression:** assert that
   `_resolve_retry_lane_routing` does not return `force_patch=True`
   when `previous_attempt.reject_bucket == "post_select_conflict"`,
   `previous_attempt.gate_basis == "post_select_conflict"` (or
   `error_category == "POST_SELECT_CONFLICT"`), and `prev_manuscript`
   is non-empty — even if `previous_attempt.fix_scope` is `"inplace"`
   (i.e. a stale director-authoritative value).

3. **F6 regression:** unit-test
   `_should_allow_bounded_post_select_patch_retry` with a
   `conflict_contract` whose `contradiction_types == ["proper_noun"]`
   but whose `target_kind == "local_sentence"`. The current implementation
   already short-circuits on line 207 (`"proper_noun" in effective_types
   ... return False`); add a fixture that asserts this specifically for
   institution-name-style fix_packs (e.g. fix_pack.evidence_summary
   referencing `회사명 / 기관명 / 조직명`). Also add a fixture for a
   duplicated-continuation-beat case that mislabels the conflict as
   `opening_action_continuity` and assert the lane *does* return False
   when the truth_pin family is `proper_noun_group`.

4. **F7 regression:** add a hydration fixture where
   `current_project.metrics_session_id` is `None` (or the project lacks
   the attribute entirely) and `db.get_stage_attempts_for_arc` is asked
   to return rows from two distinct sessions for the same `(arc,
   episode)`. Assert that `hydrate_persisted_stage4_previous_attempt`
   either returns `{}` or filters to rows whose `session_id`
   field is `None` (i.e. legacy unsessioned rows only).

5. **F8 regression:** assert that, on an empty-candidate REJECT, the
   reject artifact is *not* serialized using a `best_manuscript` whose
   `attempt_key`/`session_id` differs from the current attempt's
   `attempt_key`/`session_id`.

6. **F9 regression:** add a hydration fixture whose
   `feedback_provenance.merged_feedback` includes the
   `[A-4 continuity replay]` and `[Conflict-first retry]` markers. After
   the first round 0 ensemble run, assert the seeded
   `director_feedback` is sanitized so that prior-attempt-specific
   institution names / opening-beat phrasing are not lifted verbatim
   into the new prompt context.

7. **F10 regression:** under autonomous mode, assert
   `_finalize_round_outcome_loop` does *not* default to
   "1=adopt last best" for an exhausted episode whose last
   `previous_attempt.reject_bucket == "post_select_conflict"` and
   `error_category == "POST_SELECT_CONFLICT"`.

8. **End-to-end seam:** an integration-style test that runs
   `hydrate_persisted_stage4_previous_attempt` →
   `_run_interview_round_step` (round 0) →
   `_handle_reject_round_result` → `_resolve_retry_lane_routing` (round
   1) and asserts `use_patch == False` whenever the original REJECT was
   POST_SELECT_CONFLICT, end-to-end, without any per-component mocking
   of `fix_scope`.

## Dependencies On Other Terminals

- **Director-side classification audit (likely T01 / T02 / T03):**
  F5 and F6 both depend on whether the director-authored
  `gate_semantics`, `scope_authority`, `conflict_contract`, and
  `truth_pin_items` correctly tag institution-name drift as a
  `proper_noun_group` family with a `proper_noun` `contradiction_type`.
  If those upstream classifications are correct, F6 closes naturally;
  if they are not, the patch lanes here are downstream symptoms.
- **POST_SELECT firewall classifier (probable T04 / T05):**
  `_classify_reject_bucket` and `_is_continuity_replay_reject` decide
  whether the runtime widens to `"full"` or not. T06 confirms the
  *retry-side* widening exists (line 1444–1446, 1507–1519) but cannot
  judge whether the firewall always reaches it. Coordinate to confirm
  every POST_SELECT_CONFLICT path enters the widening branch.
- **Stage 3 / blueprint carryover (likely a frontier/blueprint terminal):**
  F9 says the prior session's continuity-replay directive can re-steer
  the next round 0 generation. The longer-term fix may sit in Stage 3
  blueprint-level continuity contracts, not in the Stage 4 retry
  surface. Defer to the terminal owning carryover/frontier authority
  before patching the seeding text.
- **Resume / orchestrator session-id terminal:** F7 needs the resume /
  bootstrap owner to confirm whether `metrics_session_id` is *always*
  bound on `current_project` before `_handle_round_outcome` runs. If
  yes, F7 is a defensive concern; if no, F7 is a live-path bug.
- **DB authority / stage_attempts terminal:** F5 also needs
  agreement that `advisory_flags.scope_authority` should mirror the
  runtime-widened `fix_scope` rather than the director-original value
  (or alternatively, that the hydration should ignore
  `scope_authority.fix_scope` for `post_select_conflict` rows).

## Open Questions

1. Is `current_project.metrics_session_id` guaranteed non-empty by the
   time `_hydrate_round_loop_resume_state` runs in production? If not,
   F7 is a live cross-session contamination route.
2. What is the intended semantic split between
   `attempt_row.fix_scope`, `gate_semantics.fix_scope`, and
   `scope_authority.fix_scope` after a POST_SELECT_CONFLICT runtime
   widening? F5 reads as an unintentional shadowing — but if
   `scope_authority` is *meant* to preserve the pre-widening value as
   an audit trail, the hydration logic should at minimum not surface it
   as the active runtime `fix_scope`.
3. Is the `force_patch` round-budget (`round_num <= 1`) deliberately
   broad, or was it intended to apply only after a *bounded* fix_pack
   contract is in place? The current condition only checks
   `prev_manuscript` truthiness, not the bounded contract.
4. Are EP6/EP8/EP9's POST_SELECT_CONFLICT REJECT chains running as
   *patch* attempts or as *full rewrite* attempts? `is_patch` /
   `is_patch_fallback` are persisted on `stage_attempts` (line 8909–
   8911) — confirming that data on the live run would discriminate F3+F4
   from F9 directly.
5. Does the hydration intentionally re-load the failed manuscript text
   (`best_manuscript`) on resume, or is the intent only to surface the
   contract / feedback metadata? If the latter, dropping
   `best_manuscript` from the hydrated payload would close F1, F3, F8
   together with no behavioural change on full rewrites.
6. Does the autonomous runner use `_get_stage4_exhaustion_default_choice()
   == 1`? If so, F10 is a live propagation route across episodes.

## Closure Recommendation

I recommend **NOT closing** Issue #58 on T06 evidence alone, and instead
treating this report as one input to a multi-terminal fix decision.

Concretely, I would gate closure on:

- **Live-run evidence triangulation.** The EP6/EP8/EP9
  POST_SELECT_CONFLICT chains in
  `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md` should be
  re-checked against `stage_attempts` rows for `(is_patch, fix_scope,
  advisory_flags.scope_authority.fix_scope)` per attempt. If
  `is_patch == 1` appears on any second-or-later POST_SELECT_CONFLICT
  reject in those chains, F3/F4/F5 are confirmed live and need the F5
  shadow fix before any close.
- **Decision on F5.** The `scope_authority.fix_scope` shadowing in
  `_hydrate_stage4_previous_attempt_from_row` is the single most
  load-bearing finding. Either the hydration should pin `fix_scope =
  "full"` for `post_select_conflict` reject_buckets, or the reject
  persistence path should write the runtime-widened value into
  `scope_authority.fix_scope` before saving advisory_flags.
- **Decision on F1/F3.** If the team agrees that POST_SELECT_CONFLICT
  resume should never patch the prior body, the simplest closure is to
  drop `best_manuscript` (or null it for `post_select_conflict` /
  continuity-replay rows) inside `_hydrate_stage4_previous_attempt_from_row`,
  forcing a fresh ensemble on round 0 and forcing the rewrite lane on
  rounds 1+.
- **Confirm F7 is dead.** If the bootstrap can prove
  `metrics_session_id` is always set before hydration, F7 becomes an
  audit-only concern; otherwise it should be fixed alongside F5.
- **Add the regression suite in §Regression / Test Candidates** so the
  closed state is enforced.

Until those gates are answered (and ideally validated against a fresh
5-arc live merge run per `live-run-merge-survey-harness.md`), my
recommendation for #58 is **keep open, escalate F5 first**.
