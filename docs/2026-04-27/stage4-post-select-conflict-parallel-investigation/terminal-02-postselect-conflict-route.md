# T02 Post-Select Conflict Route

Date: 2026-04-27
Workspace: `C:\Users\wjjo\Desktop\글도비`
Baseline commit: `a3d826978d530ab61d3765e5e095890fa6533ea7`
Mode: read-only investigation. No source, test, doc (other than this report), DB, GitHub, or git mutation.
Authority note: Python (this report's analytical layer) is for transport and structuring. Director-LLM verdicts remain the narrative authority; closure recommendations below preserve that ranking.

## Scope

Map the production, normalization, persistence, and operator surface of `POST_SELECT_CONFLICT` for #58. Identify whether the bucket is detecting stale carryover correctly, over-triggering, or masking a more specific failure family. Enumerate authority layers from Director ensemble verdict through final stage_attempts persistence.

In scope (per dispatch):
- `modules/core/stage4_postselect_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_types.py`
- `modules/core/db_manager.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_stage4_interview_round.py`

Out of scope: stage3 handoff lineage (T03), continuity authority carriers (T04), memory/cache effects (T05), retry hydration (T06), context-cache lineage (T07), regression test bodies (T08), artifact-truth sampling (T09).

## Commands / Evidence

Static surface scan (read-only):

```bash
git grep -n -E "POST_SELECT_CONFLICT|post_select_conflict" -- modules tests
```

Returns 1 production reference to the upper-case token (`stage4_reject_runtime.py:997`) plus extensive lower-case `post_select_conflict` references across `stage4_postselect_runtime.py`, `stage4_outcome_runtime.py`, `stage4_reject_runtime.py`, `stage4_retry_runtime.py`, `stage4_interview_round.py`, `stage4_policy_digest.py`, `feedback_system.py`, and the corresponding tests.

Compile gate (read-only):

```bash
python -m py_compile modules/core/stage4_postselect_runtime.py \
                     modules/core/stage4_outcome_runtime.py \
                     modules/core/stage4_reject_runtime.py \
                     modules/core/stage4_interview_round.py \
                     modules/core/stage4_orchestrator.py
```

Exit 0. No tests were executed (read-only investigation).

Live UI evidence (current 5-arc run, target project `projects/01_골든카나리아/logs/session/ui_events.jsonl`, sessions `20260427_022220` and `20260427_070604`):

| ep | session | conflict subfamily | post-select Director-LLM summary (excerpt) |
| --- | --- | --- | --- |
| 3 | 20260427_022220 | continuity + history | "이전 회차에서 확립된 그룹 회장(아버지)의 이름이 현재 회차에서 다르게 표기" + "제1화에서 확립된 갑을 관계 및 사건 진행이 제3화에서 무시되고 초기화" |
| 5 | 20260427_022220 | history | "제4화에서 이미 발생한 핵심 사건(이란 핵 위기 뉴스 보도)이 제5화에서 날짜만 2월 1일로 바뀐 채 동일하게 반복" |
| 4 | 20260427_070604 | history | "제4화는 제2화 및 제3화에서 이미 완료된 지시(법인 설립 로펌 수배)를 처음 지시하는 것처럼 중복 묘사" |
| 7 | 20260427_070604 | continuity | "제5화에서 이미 보도된 이란 핵 속보가 제7화에서 다시 최초 발생 사건처럼" + "증권사 명칭(H&T 증권 → 한미증권) 일관성 누락" |
| 8 | 20260427_070604 | continuity | "H&T 증권 → 한미증권 변경 충돌" |
| 8 (round 1) | 20260427_070604 | history | "7화 엔딩의 유가 급등 촉발 뉴스(나이지리아 피격 + EIA 재고 감소)가 8화 도입부에서 '이란 우라늄 농축 재개 선언'으로 잘못 기재" |
| 9 | 20260427_070604 | continuity + history | "제5화에서 이미 발생한 이란 우라늄 농축 재개 속보가 제9화에서 2월 28일에 다시 새로운 속보로" + "H&T 증권 vs 한미증권 혼용" |

These are the four bug shapes #58 names: institution-name drift (H&T 증권 vs 한미증권), date drift (2월 1일 → 2월 28일), duplicated continuation beats (제5화의 속보가 제7·9화에서 재발), prior-state initialization (제1화에서 확립된 갑을 관계가 제3화에서 무시).

Earlier session evidence (`projects/골든 카나리아/logs/session/ui_events.jsonl:2255`):

```
"   ⚠️ [TF-29] 'post_select_conflict' 유형 REJECT 3연속 → 블루프린트 단계 문제 가능성"
```

The advisory text shows the raw bucket key leaking into operator UI rather than a human label.

## Findings

F1. Post-select is a **downgrade-from-PASS layer**, not a primary classifier.
- `Stage4PostSelectRuntime.run_post_select_checks` is invoked only from `_run_positive_verdict_transition` (`modules/core/stage4_interview_round.py:6387`) which itself only fires when the Director ensemble has already returned `verdict ∈ {PASS, PASS_WITH_FIX, CONDITIONAL_PASS}`.
- The route exists to catch the case where Director ensemble said PASS but the same Director's `check_manuscript_continuity_with_cache` / `check_manuscript_history_conflicts` post-select queries return `decision == "CONFLICT"`.
- Python here normalizes the LLM verdict, it does not invent it. (`modules/core/stage4_postselect_runtime.py:520-540`).

F2. Authority layers, top to bottom:
1. **Director ensemble** (`select_and_judge_ensemble`) → `verdict=PASS / PASS_WITH_FIX`.
2. **Director post-select continuity check** (`check_manuscript_continuity_with_cache`) and **Director post-select history check** (`check_manuscript_history_conflicts`) → each returns `decision=CONFLICT|PASS` plus `summary`. These are LLM judgments executed in parallel via a `ThreadPoolExecutor` (`stage4_postselect_runtime.py:492-518`).
3. **Python post-select route** (`Stage4PostSelectRuntime.run_post_select_checks`):
   - Mutates `verdict` to `REJECT` (`stage4_postselect_runtime.py:440`).
   - Calls `_apply_director_gate_update(...)` to set `gate_basis="post_select_conflict"`, `final_verdict="REJECT"`, `repair_scope="full"`, then forces `director_result["fix_scope"]="full"` (`stage4_postselect_runtime.py:441-447`).
   - Builds `_PostSelectConflictClassification` from the conflict text shape: each line containing `Continuity` → `continuity`, `History` → `history`, else `check_error`.
   - Derives `error_category` ∈ `{POST_SELECT_CONTINUITY_AND_HISTORY, POST_SELECT_CONTINUITY_CONFLICT, POST_SELECT_HISTORY_CONFLICT, POST_SELECT_CHECK_ERROR}` (`stage4_postselect_runtime.py:601-610`).
   - Builds a `previous_attempt` whose `reject_bucket="post_select_conflict"`, `retry_pathology_source="post_select_conflict"`, `provisional_pass_downgrade=True`, plus `conflict_contract`, `truth_pins`, `reuse_contract` for the next round.
4. **Reject runtime guidance** (`Stage4RejectRuntime._build_reject_guidance_payload`, `stage4_reject_runtime.py:1409-1528`):
   - First runs the text-based `_classify_reject_bucket` (`stage4_interview_round.py:1181`). That classifier scans for `("constraint", "consistency", "conflict", "contradiction", "logic", "validation", "continuity")` and returns `constraint_violation` first. So a feedback string containing "Continuity Conflict" would be bucketed `constraint_violation` by the text classifier alone.
   - The **C-2 seam fix** (`stage4_reject_runtime.py:1444-1446`) promotes `reject_bucket` to `post_select_conflict` when `gate_basis == "post_select_conflict"`. This compensates for the text-classifier's miscategorization but only at this single seam.
   - When `reject_bucket == "post_select_conflict"` and `resolved_fix_scope == "full"`, line 1289-1300 blanks `selection_reason` and `open_review` (rationale elision) and tags `_rationale_blanked_by="runtime_post_select_conflict_elision"`. Exception: `preserve_downgraded_pass_rationale` keeps the high-score (≥80) provisional_pass_downgrade rationale (`stage4_reject_runtime.py:1283-1288`).
   - Forces `resolved_fix_scope="full"`, blanks `resolved_fix_pack` unless a bounded fix-pack qualifies (`_should_preserve_post_select_fix_pack`, `stage4_reject_runtime.py:599-613`), prepends the conflict-first-retry notice.
5. **Persisted attempt row** (`db_manager.save_stage_attempt`, `stage4_interview_round._record_s4_attempt` → `_save_stage4_db_attempt`):
   - `verdict="REJECT"`.
   - `failure_category` carries the specific subfamily error_category (e.g., `POST_SELECT_CONTINUITY_CONFLICT`).
   - `reject_reason` carries the merged Director feedback text.
   - **`reject_bucket` is not a top-level column** — it lives only inside `advisory_flags` JSON and inside the session-memory envelope under `retry_surface.reject_bucket`.
   - `primary_failure_layer` from `_build_verdict_layers_payload`: `downstream_gate` if the Director ensemble passed (the post-select case), else `director_quality`.
6. **Final settlement** (`mark_stage4_attempt_settlement_failed`, `db_manager.py:3617`): a separate path that demotes a previously-PASS row to `SETTLEMENT_FAILED`. This is unrelated to post-select; settlement failure is its own family.
7. **Outcome runtime advisory** (`Stage4OutcomeRuntime._apply_reject_bucket_advisory`, `stage4_outcome_runtime.py:908-950`): tracks bucket-streak and emits TF-29. The bucket-label map only covers `quality_issue / constraint_violation / structure_error`, so for `post_select_conflict` it falls back to the raw key — visible in `projects/골든 카나리아/logs/session/ui_events.jsonl:2255`.

F3. POST_SELECT_CONFLICT is **not over-triggering** at the classifier seam. Live evidence (Findings F1 Commands table) shows the post-select Director-LLM is correctly identifying real institution-name drift, date drift, duplicated continuation beats, and prior-state initialization. These are precisely the four narrative-truth families #58 cares about. The Python layer is fail-closed transport, not noise.

F4. POST_SELECT_CONFLICT **does mask subfamilies** at the operator-visible bucket layer:
- `error_category` keeps continuity/history/both/check-error apart and is persisted in `failure_category`.
- `reject_bucket` collapses all of them to a single token, and the bucket-streak / TF-29 advisory only sees the bucket. So the streak signal cannot tell "institution-name-drift 3연속" apart from "duplicated continuation beat 3연속" — both raise the same blueprint-regeneration hint.
- `bucket_label` in `_apply_reject_bucket_advisory` does not have a mapping for `post_select_conflict`, so the operator UI shows the raw key.

F5. The text-based `_classify_reject_bucket` (`stage4_interview_round.py:1181-1192`) is **a latent shadow path**. If `gate_basis` is ever lost in transport (resume hydration, advisory_flags round-trip without retry_surface, cross-process reject) the bucket silently regresses to `constraint_violation`. The C-2 seam fix only protects the in-process reject-guidance call site; it does not guard `_resolve_stage4_resume_reject_bucket` (`stage4_interview_round.py:2153-2179`), which itself does honor `gate_basis` but only after exhausting `retry_surface.reject_bucket → advisory.reject_bucket → semantics.reject_bucket → primary_failure_layer`.

F6. `_is_continuity_replay_reject` (`stage4_interview_round.py:1484-1525`) requires `director_result["firewall_triggered"]==True`. `Stage4PostSelectRuntime.run_post_select_checks` does **not** set `firewall_triggered`. So post-select-only conflicts do not enter the continuity-replay escalation, which is the path that would force `error_category=LOGIC_ERROR` and the "[A-4 continuity replay]" notice. They get the standard `post_select_conflict` "full rewrite" path plus the bounded-flashback patch exception.

F7. `treat_post_select_conflict_as_logic_like` policy (default `True`, `stage4_policy_digest.py:43`) is consumed by `Stage4OutcomeRuntime._is_logic_like_failure` (`stage4_outcome_runtime.py:738-774`). When set, post-select conflicts feed the `logic_error_streak` counter that drives V75-B blueprint regeneration. The companion test `test_analyze_reject_round_treats_post_select_conflict_as_logic_like_failure` confirms the wiring (`tests/test_stage4_orchestrator.py:3136`).

F8. The **bounded local-fix exception** (`_should_allow_bounded_post_select_local_fix`, `stage4_postselect_runtime.py:127-162` and `_should_allow_bounded_post_select_patch_retry`, `stage4_retry_runtime.py:144-234`) lets a continuity-only patch use `target_kind ∈ {entity_ref, local_phrase, local_sentence}` if no rewrite-required reason exists and the conflict types are constrained. Truth-pin families that include `proper_noun_group` or `asset_state` block the bounded patch. Live evidence at ep8 (`stage4` `s4:ep8:arc2:a2:20260427_070604`, ui_events `seq=985`) shows this exception correctly firing for a continuity-only conflict.

F9. **Provisional-PASS rationale elision can hide why Director PASSed**:
- When `reject_bucket == "post_select_conflict"` and `fix_scope == "full"` and the score is below 80, the runtime blanks `selection_reason` and `open_review` on the persisted attempt (`stage4_reject_runtime.py:1289-1300`). This is intentional ("rationale_blanked_by=runtime_post_select_conflict_elision") to prevent stale PASS reasoning from misleading the next round, but it also means **operators looking at the persisted reject row cannot recover the original Director PASS rationale**.
- For high-score (≥80) downgraded-PASS, the rationale is preserved (covered by `test_post_select_conflict_snapshot_preserves_high_score_downgraded_pass_rationale`, `tests/test_stage4_interview_round.py:9414`).

F10. Director-PASS / post-select-CONFLICT **disagreement is the real signal**.
- Live evidence shows the same Director model issues `verdict=PASS` from `select_and_judge_ensemble` and immediately afterwards issues `decision=CONFLICT` from `check_manuscript_continuity_with_cache` / `check_manuscript_history_conflicts`.
- Today the runtime treats this as "post-select drift", but at the system level it is a **Director context-coverage gap** at the ensemble step. The post-select layer is not the bug; it is the canary that exposes it.
- This is consistent with the dispatch's prior framing that session/vector memory and context cache are helper telemetry, not the authority for date / institution / prior-state pins.

## Root-Cause Candidates

Stage 4 post-select layer is correctly transporting the LLM verdict. Therefore the root-cause candidates within T02 scope are not "POST_SELECT_CONFLICT is wrong" but "POST_SELECT_CONFLICT is too coarse" and "Director ensemble is too permissive given the available context".

RC1 (T02 primary, **classifier resolution**) — Bucket coarseness.
- `reject_bucket` collapses 4 distinct narrative subfamilies (institution-name drift, date drift, duplicated continuation beats, prior-state initialization) into one token, while `error_category` only keeps continuity vs history vs both vs check-error apart.
- Downstream advisory (TF-29 streak detection, plateau detection) consumes only `reject_bucket`, so subfamily streaks cannot trigger different remediation. This is a structural reason 5-arc runs accumulate the same bucket without escaping.

RC2 (T02 secondary, **bucket label leak**) — Operator UI shows raw key.
- `_apply_reject_bucket_advisory` `bucket_label` map does not include `post_select_conflict`. Confirmed by `projects/골든 카나리아/logs/session/ui_events.jsonl:2255`.
- Low-severity but degrades operator situational awareness and increases pressure on T08 regression naming.

RC3 (T02 secondary, **shadow-path bucket downgrade risk**) — Text classifier vs gate_basis.
- `_classify_reject_bucket` would return `constraint_violation` for any post-select feedback because the keyword scan hits `conflict` / `continuity` first. The C-2 seam fix mitigates this at one site; if any future caller (resume, cross-session hydration, retry path) bypasses that seam and runs the text classifier directly, `reject_bucket` silently flips to `constraint_violation` and `treat_post_select_conflict_as_logic_like` becomes inert.

RC4 (out of T02 scope, but **most likely real root**) — Director ensemble context-coverage gap.
- Same Director model issues PASS at ensemble, CONFLICT at post-select. The post-select context contains `prev_manuscripts_text` and the prior-history slice; the ensemble context may not (or may be served from a different cache lineage).
- This must be answered by T03 (Stage3→Stage4 handoff packets), T04 (continuity authority carriers / pin guard), T05 (memory/cache helper writes), T07 (context-cache lineage). T02 cannot close it.

RC5 (out of T02 scope) — Continuity-pin drift past the post-select check.
- Truth-pin building (`_extract_post_select_truth_pins`, `stage4_postselect_runtime.py:51-98`) only extracts `proper_noun_group` and `asset_state` families from the conflict text. Date drift and prior-state initialization do not become structured truth pins, so the next round's `conflict_contract` does not carry them as machine-checkable constraints. Owned by T04.

## Regression / Test Candidates

R1. **Bucket promotion via gate_basis at the text-classifier site.**
- New test in `tests/test_stage4_interview_round.py` exercising `_classify_reject_bucket` with `director_feedback="...continuity conflict..."` AND `gate_basis="post_select_conflict"` flowing through `_build_reject_guidance_payload`. Assert `reject_bucket == "post_select_conflict"` end-to-end. Currently only the seam-fix branch is covered by indirect tests; an explicit assertion would catch any future caller that bypasses the seam.

R2. **TF-29 advisory bucket-label coverage.**
- New test in `tests/test_stage4_orchestrator.py` for `_apply_reject_bucket_advisory` with `prev_reject_bucket="post_select_conflict"`. Today the test surface only verifies streak counting (`test_handle_round_outcome_emits_retry_pathology_repeat`, `tests/test_stage4_orchestrator.py:3674`); it does not assert the human-readable label. Add an assertion that the emitted advisory text uses a non-raw label (e.g., "후속 정합성 충돌") rather than the raw bucket key.

R3. **Persisted `failure_category` subfamily distinctness.**
- New test confirming each of the four `error_category` outcomes (`POST_SELECT_CONTINUITY_CONFLICT`, `POST_SELECT_HISTORY_CONFLICT`, `POST_SELECT_CONTINUITY_AND_HISTORY`, `POST_SELECT_CHECK_ERROR`) flows into `save_stage_attempt` as `failure_category` distinctly. Today the post-select tests stop at the `previous_attempt["error_category"]` field; no test asserts the DB-side projection.

R4. **Director ensemble vs post-select agreement contract.**
- Owned narratively by T03/T04, but T02 can propose a contract test: with `check_manuscript_continuity_with_cache.return_value = {"decision": "CONFLICT", "summary": ...}` and `select_and_judge_ensemble` configured to receive the same `prev_manuscripts_text`, fail the test if the ensemble returns PASS. Use a mocked Director that only consults `prev_manuscripts_text`.

R5. **Resume / hydration bucket survival.**
- Test that `_hydrate_stage4_previous_attempt_from_row` (`stage4_interview_round.py:2189`) returns `reject_bucket=="post_select_conflict"` from a DB row whose `advisory_flags.gate_semantics.gate_basis == "post_select_conflict"` even when `failure_category` is missing. Coverage today is implicit through `test_resolve_stage4_resume_reject_bucket`-shaped paths but no fixture exercises a row with only gate_basis and no retry_surface.

R6. **Provisional-PASS rationale elision contract.**
- Negative test: when `provisional_pass_downgrade=True` and `score=72`, `selection_reason` is blanked and `rationale_blanked_by="runtime_post_select_conflict_elision"`. Positive test for `score=85` already exists. The negative case keeps the elision contract from drifting silently.

All test candidates are descriptions only; **no test files were created or modified by this report**.

## Dependencies On Other Terminals

- **T01 (current-run forensic baseline)**: needs to confirm whether `failure_category` column actually carries `POST_SELECT_CONTINUITY_CONFLICT` / `POST_SELECT_HISTORY_CONFLICT` distinctly across ep4–ep9 attempt rows, and whether `advisory_flags.gate_semantics.gate_basis="post_select_conflict"` is present. T02's classifier analysis is meaningless without DB-side proof of persistence.
- **T03 (Stage3→Stage4 handoff)**: must answer whether the Director ensemble call gets the same `prev_manuscripts_text` and continuity context as the post-select Director call. RC4's resolution lives here.
- **T04 (continuity authority carriers)**: must answer whether institution names, prior dates, prior-state authority pins live in `_continuity_pins` / `episode_state_arbiter` / `authoritative_continuity_projection`. RC5's resolution lives here.
- **T05 (memory/cache side effects)**: must rule out whether memory/cache reads serve different prior content to ensemble vs post-select. RC4 alternative explanation.
- **T06 (retry hydration / replay)**: must answer whether failed-attempt previous_attempt envelopes can replay stale fix_pack or stale `provisional_pass_downgrade` flags into a new attempt and trigger spurious post-select-conflict bucket transitions.
- **T07 (context-cache lineage)**: must answer whether cached prompt content reintroduces stale institution names / dates after blueprint or treatment changes.
- **T08 (regression gap design)**: should consume R1–R6 above as candidate test names, plus subfamily-specific coverage for institution / date / continuation-beat / prior-state-init.
- **T09 (artifact truth)**: should validate that the rejected manuscripts whose post-select feedback is logged in ui_events.jsonl actually contain the alleged contradictions in narrative truth (vs hallucinated by post-select Director).
- **T10 (synthesis)**: T02's classifier-coarseness finding (RC1) and Director-ensemble disagreement framing (F10/RC4) are the two pieces T10 must merge with T03/T04/T05/T07 conclusions.

## Open Questions

OQ1. Why does the same Director model issue PASS at ensemble and CONFLICT at post-select? Three competing hypotheses:
- (a) Ensemble prompt does not include `prev_manuscripts_text` / continuity slice that post-select includes.
- (b) Ensemble does include the same context, but its scoring weight under-penalizes continuity vs creativity / pacing axes.
- (c) Ensemble and post-select hit different cached contents (different cache lineage). T07 owns this.

OQ2. Is `reject_bucket="post_select_conflict"` ever lost in transport? Specifically, does the resume path always carry `gate_basis` through `advisory_flags.gate_semantics`? T01 should sample DB rows.

OQ3. Should `failure_category` be promoted to a subfamily-aware bucket? Today it carries `POST_SELECT_CONTINUITY_CONFLICT`-class strings but the streak/plateau advisories ignore it. Either the streak advisory should be widened to consume `failure_category`, or `reject_bucket` should fork into `post_select_continuity` / `post_select_history` / `post_select_both`. This is a design call, not a T02 closure.

OQ4. Why does `_extract_post_select_truth_pins` only handle `proper_noun_group` and `asset_state`? Date drift and duplicated-event detection (the two most common subfamilies in current live evidence) do not become structured truth-pins, so the conflict_contract carried into the next round cannot machine-check them. T04 owns this; T02 only flags it.

OQ5. Is the bounded-flashback patch path (`_should_allow_bounded_post_select_patch_retry`) ever firing for the wrong subfamily? The exception list (`continuity, timeline, movement, location, facing, dialogue, opening_action_continuity`) does not include `history`. Live ep8 evidence shows it correctly fired for a continuity-only conflict, but the subfamily classification is text-pattern-based and could misclassify mixed conflicts.

## Closure Recommendation

**Do not close #58 on T02 evidence alone.** The post-select layer is correctly catching real Director-LLM-judged narrative drift. POST_SELECT_CONFLICT is the canary; the underlying carriage failure lives upstream in Stage3→Stage4 context lineage and continuity authority pins (T03/T04/T05/T07).

For the T02-scope post-select route layer, the recommendation is:

1. **Preserve POST_SELECT_CONFLICT as fail-closed transport.** Do not relax, gate, or short-circuit the post-select Director-LLM checks. They are the only layer currently catching institution-name drift, date drift, and prior-state initialization end-to-end. Disabling or rate-limiting them would silently regress 5-arc quality.
2. **Surface subfamily, not bucket.** Make TF-29 streak detection consume `failure_category` (continuity / history / both / check-error) rather than the collapsed bucket. This is a design proposal, not a patch — owned by T08/T10's execution-readiness call.
3. **Tighten the classifier seam.** R1 + R5 close the latent shadow-path risk (text classifier + resume hydration) at minimal scope. Land them before any further routing changes.
4. **Add the bucket label.** R2 fixes the operator-UI raw-key leak.
5. **Defer Director-ensemble vs post-select disagreement to T03/T04/T05/T07.** The real lever for #58 carryover drift is closing the context-coverage gap that lets the ensemble issue PASS for a manuscript the same Director will reject 30 seconds later. T02 cannot patch this from the post-select side without becoming Python narrative judge, which AGENTS.md forbids.

Authority preservation: this report's analysis is Python-side classification of Director-LLM verdicts. All narrative-truth verdicts in the live UI evidence remain Director's. Any closure decision on #58 must come from Director review of the synthesized T01–T09 evidence, not from this layer's structural analysis alone.
