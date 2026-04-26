# Frontier Lag Clean 5-Arc — Lane A Failure Forensics

Date: 2026-04-26
Track: system order / read-only forensics
Lane: A (Failure Forensics)
Order Pack: `docs/2026-04-26/frontier-lag-clean-5arc-6terminal-order-pack.md`
Status: final, embedded 3-pass audited
Confidence: 95%

This report is read-only forensics. No code is patched, no DB is mutated, no factsheet is rewritten. Python collected and routed evidence; the contradiction itself is a content-layer fact whose authority belongs to LLM/Director.

## Scope

Trace where the Stage3 ep4 timeline contradiction (`2006년 1월 1일` vs `2006년 1월 3일`) entered the upstream-to-downstream chain in the 2026-04-26 Frontier Lag run, and explain why it survived ten attempts before the harness hit the HIL stop boundary.

In scope:

- Source-of-truth lineage for the `Jan 3` constraint.
- Surface lineage for the `Jan 1` blueprint output.
- Detection / routing / retry / persistence path.
- Observability gaps.

Out of scope:

- Designing a fix.
- Judging narrative correctness of either Jan 1 or Jan 3.
- Evaluating Stage4 ep2 retry pathology (separate lane).
- Recommending implementation changes (later lanes own that).

## Evidence

### Subagent split

- DB / source-artifact lineage subagent ran sqlite3 against `projects/0_골든카나리아/project_data.db` and read `plans/arcs/arc_002.txt`, the Stage2 final-arc JSONs, and the Stage3 artifact tree.
- Log / harness lineage subagent read `logs/session/decisions.jsonl`, `logs/session/llm_io.jsonl`, `logs/runtime_audit.jsonl`, `logs/pass_rate_monitor.json`, `logs/quality_metrics.jsonl`, `logs/episode_production.jsonl`, the auto-frontier-lag analysis/digest pair, the 620 KB session log, and the relevant code paths in `main_a.py`, `modules/core/stage3_orchestrator.py`, `modules/domain/agents/three_phase_blueprint_runtime.py`, `modules/domain/agents/unified_blueprint_validator.py`, `modules/domain/agents/blueprint_ensemble.py`, and `modules/core/session_memory_envelope.py`.

The two lanes corroborate each other on every material fact. See `Subagent Cross-Check` below for the detail.

### Authority surface (where `Jan 3` actually lives)

- `projects/0_골든카나리아/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json` carries the only day-precise terminal-date authority for arc 1:

  ```json
  "timeline": {
    "start": { "year": 2006, "month": 1, "day": 1, "description": "회귀 직후" },
    "end":   { "year": 2006, "month": 1, "day": 3, "description": "법인 설립 서류 준비 완료" }
  }
  ```

- The same struct is mirrored in DB anchor `anchors.arc_payload_0001.state_changes.timeline.end`.
- `projects/0_골든카나리아/plans/arcs/arc_001.txt` (the human-readable arc plan) does **not** contain `1월 3일`, `Jan 3`, or any other day-precise end date. The closest temporal cues are `2006년 1월 초` (line 12) and `2~3주 내` (line 24).
- Therefore the `Jan 3` requirement exists only as a Stage2 metadata field, not as prose narrative truth visible in the human-readable plan.

### Surface lineage (where `Jan 1` came from)

The `2006년 1월 1일` (or `1월 1일`) string was observed in the following surfaces and only the following surfaces:

| Surface | Where |
|---|---|
| DB `blueprints.data` ep_num=1 | `time_flow: 2006년 1월 1일 아침`, ending_state.timeline 표현: `2006년 1월 1일 오전`; also `탁상달력의 2006년 1월 1일` in prose |
| DB `blueprints.data` ep_num=2 | `time_flow: 2006년 1월 1일 오전 -> 낮`, ending_state.timeline 표현: `2006년 1월 1일 낮` |
| DB `blueprints.data` ep_num=3 | `time_flow: 2006년 1월 1일 낮 -> 오후`, ending_state.timeline 표현: `2006년 1월 1일 늦은 오후` |
| DB `manuscripts.content` ep_num=1 | opening line `2006년 1월 1일 아침. 서울 성북동 본가 침실.` |
| DB `manuscripts.hud_snapshot` ep_num=1 | timeline 표현: `2006년 1월 1일 낮` |
| DB `episode_sentence_hashes.sentence_preview` ep_num=1 | `2006년 1월 1일 아침` |
| DB `attempt_raw_rationale.payload` rowid=10 (ep=2 stage=4) | dialogue `지금은 2006년 1월` |
| DB `director_selections.advisory_warnings` id=9 | the contradiction quote |
| DB `stage_attempts.advisory_flags` / `reject_reason` / `runtime_advisory` id=9 | the contradiction quote |
| DB `ui_events.message` ids 675, 676, 678 | mirrored contradiction quote |
| `logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__action_focused.json` | 5 occurrences |
| `logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__action_focused.json` | 2 occurrences |
| `logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json` | 2 occurrences |

The `Jan 1` string was **not** observed in:

- `plans/arcs/arc_001.txt`, `plans/arcs/arc_002.txt`
- `logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json`
- `logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`
- DB anchors `arc_payload_0001`, `arc_payload_0002`

### DB persistence facts

- `stage_attempts` for stage=3 has only four rows total: ep1 a1, ep2 a1, ep3 a1, ep4 a10. Attempts 1–9 of ep4 produced no `stage_attempts` row.
- `director_selections` for ep4 has only `round_num=10`. Rounds 1–9 produced no row.
- `attempt_raw_rationale` has zero rows for stage=3 (any episode).
- The terminal row id=9 has `verdict='FAILED'`, `score=95`, `failure_category='validation_contradiction'`, `content_hash=''`, `artifact_path=''`, `initial_verdict='PASS_WITH_FIX'`, `downstream_override_applied=1`.
- The terminal row's `advisory_flags.selected_candidate_advisory_struct.python_warnings[0]`:

  ```json
  {"source":"python_prevalidate","severity":"MAJOR","category":"arc_timeline",
   "message":"ending_state.timeline 불일치: blueprint '2006년 1월 1일 밤' vs arc '{'year':2006,'month':1,'day':3,'description':'법인 설립 서류 준비 완료'}'",
   "focus":"ending_state.timeline과 time_flow를 arc state_changes.timeline 종료 시점에 맞추기"}
  ```

- The terminal row's `retry_directives`:

  ```text
  기관명/인물명/수치 anchor를 1~2개 이상 보강 (현재 3개) | success_condition: integrated_scenario가 구체적 기관명, 인물명, 수치 anchor를 추가한다
  ```

  This is the anchor-boost fix-pack must_fix, not the `arc_timeline` fix-pack must_fix.

- `runtime_audit_summary.json` reports `stage3.issue_counts.artifact_metadata_missing=2` and `stage3_live_session.artifact_path_coverage={"present":3,"total":4,"status":"partial"}`.
- `logs/artifacts/stage3/` directory has only `ep_0001/`, `ep_0002/`, `ep_0003/`. No `ep_0004/` exists for any of the ten attempts.

### LLM I/O lineage

- `logs/session/decisions.jsonl` contains a single Stage3 ep4 record (the terminal a10 row). Attempts 1–9 wrote nothing here.
- `logs/session/llm_io.jsonl` lines 93–130 cover all ten Stage3 ep4 cycles. Each cycle is three `BlueprintEnsembleGenerator` calls plus one `Director` call.
- For every one of the 27 BlueprintEnsembleGenerator prompts (line numbers 93, 94, 95, 97, 98, 99, 101…127):
  - The `[FACT-LOCK]` and `[Episode Progression]` blocks contain the **previous episode's** ending timeline (`2006년 1월 1일 늦은 오후`) and re-state `시간 truth: 직전 화 시간 진실: 2006년 1월 1일 낮 -> 오후`.
  - The string `1월 3일` does not appear anywhere in any BP prompt.
  - The strings `arc_timeline`, `Python Advisory`, `Arc 기준`, `must_fix` do not appear in any BP prompt.
  - The `[CRITICAL] Director reject feedback` block carries entity-registry / anchor-boost feedback (e.g., attempt 10: `'코트'은 '외투'으로, '가죽 수첩'은 '개인 수첩'으로`).
- For every Director prompt (lines 96, 100, 104, 108, 112, 116, 120, 124, 130):
  - The prompt does include the `[Python Advisory] [MAJOR/arc_timeline]` block carrying `'year':2006,'month':1,'day':3,'description':'법인 설립 서류 준비 완료'`.
  - The Director response identifies the contradiction in `contradictions[]` and proposes `fix_scope=inplace`.

### Detection, routing, retry, persistence code path

- Detection: `modules/domain/agents/unified_blueprint_validator.py:3077` `_collect_arc_timeline_alignment_issues()` parses `arc.state_changes.timeline.end` into a normalized point and compares to `blueprint.ending_state.timeline`. When they differ on the arc-end episode, it emits a `MAJOR / arc_timeline` python_warning with a fix_pack.
- Promotion: `_summarize_binding_prevalidation_categories` (same module, line 725) gathers categories and stamps them into the validator result at lines 1064 and 1314 as `binding_prevalidation_categories`.
- Routing: `main_a.py:2675` reads that field and stamps it on `blueprint["_stage3_meta"]["binding_prevalidation_categories"]` at line 2701. Downstream `[TF-33]` logic in `three_phase_blueprint_runtime.py` refuses to honor `fix_scope=inplace` for any binding-prevalidation category and forces `fix_scope=full`. The session log shows eight distinct `[TF-33] binding_prevalidation_categories=['arc_timeline'] block inplace; force full regenerate` events for ep4 (session_20260426_171125.log lines 3633, 3738, 3854, 4112, 4227, 4361, 4478, 4688).
- Retry feedback assembly: `modules/core/stage3_orchestrator.py:252` `_build_stage3_fix_pack_retry_directives()` reads the merged `validate["fix_pack"]["must_fix"]` (lines 259–262). On every ep4 attempt the merged must_fix that survived the merge ranking was the anchor-boost advisor's, not the `arc_timeline` advisor's. That is what landed in `retry_directives`.
- Next-prompt builder: `modules/domain/agents/blueprint_ensemble.py:990–996` injects the upstream `feedback` and the `fix_pack`-derived `repair_guidance` into the BP prompt's `[CRITICAL] Director reject feedback` block. Because the merged `fix_pack.must_fix` was anchor-boost, the BP prompt never received the `Jan 3` constraint as a hard must_fix. The BP LLM was therefore asked to fix the wrong thing on every retry.
- Per-attempt persistence: only the terminal attempt is persisted to `stage_attempts`, `director_selections`, `decisions.jsonl`, and `pass_rate_monitor.json`. Rejected attempts 1–9 leave no row anywhere.
- Terminal stop: `modules/core/stage3_orchestrator.py:4120` emits `ep_4_all_retries_exhausted` (the `runtime_audit.jsonl` `blueprint_fail` event). `main_a.py:4174-4208` (`_run_frontier_lag_stage3_sync`) then prompts the operator with `1=건너뛰기 / 2=중단, 기본: 2`. The operator returned a default Enter; line 4197 routes that to `stop_reason="stage3_user_abort"`.

### Authority alignment observation

- The Python validator **detected and described** the contradiction.
- The Director **explicitly endorsed** the contradiction call in its response (`contradictions[...]`) and proposed an `inplace` fix.
- Python routing then **overrode** the Director's `inplace` preference because of the binding-category policy and forced full regenerate.
- The next-attempt prompt did **not** carry `Jan 3` as a must_fix; the BP LLM never had the information needed to satisfy the validator.

This sequence does not break the workspace principle that Python may not decide narrative truth — Python is detecting a structural-metadata mismatch (a number-vs-number comparison), not adjudicating story content. But Python is making a **routing** decision (force-full vs honor-inplace) on the LLM's behalf that drains the retry budget without ever giving the BP LLM the corrective fact.

## Findings

The findings below are bounded to Lane A's question: where did the contradiction enter and why did it survive to attempt 10. They are descriptive only.

1. [EVIDENCE] The `Jan 3` requirement exists only as Stage2 metadata (`final_arc__conservative.json` → `state_changes.timeline.end`). It is absent from the human-readable arc plan `arc_001.txt`. The plan-level prose authority and the metadata-level authority disagree about how precise the terminal-date constraint is.
2. [EVIDENCE] Stage3 ep1 BP introduced the `2006년 1월 1일` literal calendar-day claim, anchored on `state_changes.timeline.start.day=1`. Stage3 ep2/ep3/ep4 BP carried it forward via the `previous-blueprint` continuity surface. Each prior episode's `revision_required: true` (ep1) or silent pass (ep2, ep3) did not block propagation.
3. [EVIDENCE] The `arc_timeline` validator only triggers on the arc-end episode where `ending_state.timeline` is compared against `arc.state_changes.timeline.end`. ep4 was the first arc-end episode, so the validator's first hard fail occurred there — by which point three earlier episodes already encoded `Jan 1` as continuity ground truth.
4. [EVIDENCE] The BP prompt for every Stage3 ep4 attempt (1–10) contained `Jan 1` (from previous-blueprint anchors) and contained no occurrence of `1월 3일`, `arc_timeline`, `Python Advisory`, `must_fix`, or `Arc 기준`. The BP LLM literally could not see the constraint it was being failed for.
5. [EVIDENCE] The validator built a correct `arc_timeline` fix_pack each round. The orchestrator's merged `fix_pack.must_fix` ranked the anchor-boost advisor's must_fix above the `arc_timeline` advisor's must_fix. The retry feedback channel (`blueprint_ensemble.py:990-996`) therefore propagated only the anchor-boost guidance to the next BP prompt.
6. [EVIDENCE] Director sees the `[Python Advisory] [MAJOR/arc_timeline]` block in its prompt and explicitly proposes `fix_scope=inplace`. Downstream `[TF-33]` logic categorically refuses inplace for `arc_timeline` and forces `fix_scope=full`. `downstream_override_applied=1` records the override.
7. [EVIDENCE] Eight `[TF-33] ... block inplace; force full regenerate` events occurred for ep4. Each forced a regenerate against an unchanged Jan-1 BP prompt, with the predictable result of another Jan-1 candidate set. The retry budget exhausted on a structurally guaranteed loop.
8. [EVIDENCE] Only attempt 10 is persisted. `stage_attempts`, `director_selections`, `decisions.jsonl`, and `pass_rate_monitor.json` all contain no record of attempts 1–9. There are no Stage3 ep4 artifact files. `attempt_raw_rationale` has zero stage=3 rows.
9. [EVIDENCE] `quality_metrics.jsonl` records the failure with `dominant_contradiction_type="blueprint_max_retries"` and `violations=["blueprint_max_retries"]`. The structural root category (`arc_timeline`) is not surfaced at this sink.
10. [EVIDENCE] `runtime_audit.jsonl` emits one `blueprint_fail` event for ep4 (`ep_4_all_retries_exhausted`). It does not emit per-attempt `binding_failure`, `prevalidation_reject`, or `continuity_drift` events.
11. [EVIDENCE] `auto_frontier_lag_failure_digest.json` summarizes the failure as `root_cause="requested_arc_boundary_not_reached"`. The contradiction itself is not named at this surface.
12. [EVIDENCE] `modules/core/session_memory_envelope.py` exposes only Stage4 builders/attachers (`build_stage4_session_memory_envelope`). There is no Stage3 envelope builder, so no Stage3 envelope row could have carried Jan 3 forward as carry-over truth.
13. [EVIDENCE] `main_a.py:4174-4208` routes operator default-Enter to `stop_reason="stage3_user_abort"`. The label conflates an explicit operator abort with operator inaction after the system itself has exhausted retries.
14. [INFERENCE] The contradiction entered at the Stage3 ep1 BP step, when the LLM materialized `state_changes.timeline.start.day=1` into a literal calendar-day claim because no other day-precise authority was present in its prompt. It survived through ep4 attempt 10 because (a) the validator's `arc_timeline` fix_pack never reached the BP retry prompt as the dominant must_fix, (b) `[TF-33]` blocked the inplace path that the Director itself preferred, and (c) the only way the BP LLM could have learned the corrective fact was a path that did not exist in the prompt builder.
15. [INFERENCE] An inplace metadata patch on attempt 1 (Director's actual preference) would have plausibly succeeded because it is a number-field rewrite, not a narrative regenerate. The current routing policy treats `arc_timeline` mismatch as a structural binding rather than a metadata edit and so denies the cheapest correct path.

## Risks

Risks are scoped to what Lane A can see. Bridge design, governance, and harness redesign live in Lanes D / F / E.

1. **Information starvation in BP retry loop.** The BP LLM is regenerated against the same prompt that produced the failing candidate, with feedback that names a different problem. Any future retry-bound contradiction with the same fix_pack-merge-ranking shape will reproduce this exact pattern, regardless of which arc or date.
2. **Authority handoff lossy at the inplace/full boundary.** Director's `fix_scope=inplace` is overridden by Python routing without surfacing that as a Director-visible decision. The Director cannot challenge or revise the override because the override happens after the Director response.
3. **Retro-observability gap on the unsuccessful path.** Nine of ten attempts are invisible. Forensic reconstruction of why a retry budget drained relies on tail-only evidence (final attempt + raw llm_io.jsonl). That makes operator-level tuning and lane-D bridge design slower and less certain.
4. **Mis-labeled stop reason.** `stage3_user_abort` is fired on default-Enter after the system has already exhausted retries. Treating this label as evidence of operator intent is incorrect; treating it as evidence of harness-side exhaustion is also incorrect because the same label fires on a real abort. Any downstream report or analyzer that branches on this label will be reading conflated state.
5. **Surface-level root cause masking.** `quality_metrics.jsonl`'s `dominant_contradiction_type="blueprint_max_retries"` and `auto_frontier_lag_failure_digest.json`'s `root_cause="requested_arc_boundary_not_reached"` both suppress the actual structural cause (`arc_timeline`). Operator dashboards built off these sinks will under-detect this class of failure.
6. **Plan-vs-metadata authority drift.** `arc_001.txt` does not contain `1월 3일`. The Stage2 producer materialized `day:3` autonomously into JSON metadata. If the Stage2 producer's day-precise inference is wrong (or if the Director and operator would have preferred Jan 1 as the arc end), no human-readable plan-side authority can disagree, and the structural validator will hard-fail any BP that doesn't match the metadata.

## Recommendation

Lane A is read-only; this section is a recommendation for what *Lane D / Lane E / Lane F* should consider, not a request to implement.

1. The clean-5-arc redesign should treat the BP retry feedback channel as a load-bearing surface and ensure that any binding-prevalidation `must_fix` reaches the next BP prompt as a hard constraint with the corrective fact embedded literally (e.g., `ending_state.timeline = "2006년 1월 3일"`).
2. The clean-5-arc redesign should reconsider the categorical inplace-block for `arc_timeline`. A metadata-only field rewrite is the cheapest possible correct path; refusing it here forces narrative regenerate against an unchanged prompt and structurally guarantees retry exhaustion.
3. Per-attempt persistence on the failing path is required for forensics. At minimum: `stage_attempts` row per attempt with `verdict`, `failure_category`, `dominant_python_warning`, and (optionally) the rejected candidate's `ending_state.timeline` snippet. Rejected blueprint candidate JSON does not need to be retained on disk, but the structural advisory record must be.
4. The `stage3_user_abort` label should be split into `stage3_retries_exhausted_user_default` and `stage3_user_explicit_stop`, or the harness should auto-resolve to a non-default policy when the system has already exhausted retries.
5. Lane D's continuity bridge should include the case where the Director's preferred fix_scope is denied by Python routing. The bridge needs a Director-visible record of the override, since otherwise Director authority is silently downgraded.
6. The plan-vs-metadata authority drift (item 6 in Risks) is a Lane D / Lane F question. If Stage2 metadata is allowed to assert day-precise dates that have no human-readable plan authority, the validator's `arc_timeline` check is enforcing a fact whose own provenance is opaque to operators and to the Director.

## Subagent Cross-Check

Two subagents ran in parallel: one over DB and source artifacts, one over JSONL logs and code paths. They were briefed independently and did not share intermediate state.

Agreements (every material fact below was independently confirmed by both subagents):

- `stage_attempts`, `director_selections`, `decisions.jsonl`, `pass_rate_monitor.json` all contain only the terminal attempt 10 row for Stage3 ep4. Attempts 1–9 are unpersisted at every per-attempt sink.
- `logs/artifacts/stage3/ep_0004/` does not exist; `content_hash` and `artifact_path` are empty for the failed row.
- The `Jan 3` constraint lives only in `final_arc__conservative.json` / `arc_payload_0001`; `arc_001.txt` has no day-precise terminal date.
- The `Jan 1` string appears in DB blueprints rows for ep1, ep2, ep3 and in their persisted Stage3 artifact files; it does **not** appear in any plans/arcs file or any Stage2 final-arc JSON.
- The validator emits `MAJOR / arc_timeline` with the corrective fix_pack; the Director sees it via the `[Python Advisory]` block; the Director proposes `fix_scope=inplace`; downstream routing overrides to `full`; `downstream_override_applied=1`.
- The retry feedback that reached the BP LLM was the anchor-boost / entity-registry must_fix, not the `arc_timeline` must_fix.
- `runtime_audit.jsonl` emits exactly one `blueprint_fail` event for ep4; per-attempt audit events are absent.
- `session_memory_envelope.py` has no Stage3 builder, only Stage4.
- `stage3_user_abort` fires on operator default-Enter after retries have already been exhausted.

Independent contributions:

- DB subagent contributed the schema inventory, the literal `retry_directives` field value, the `python_warnings` JSON struct, the cross-file `Jan 1` provenance table, the observation that Stage3 ep1 had `revision_required: true` while ep2/ep3 did not, and the `fix_scope='full'` vs `repair_contract.fix_scope='inplace'` mismatch.
- Log subagent contributed the prompt-vs-response cross-tab over `llm_io.jsonl` (BP prompts never see `Jan 3`; Director prompts do), the eight `[TF-33]` event count, the exact code lines for detection / routing / retry / persistence, the observation that `quality_metrics.jsonl` collapses to `blueprint_max_retries`, and the observation that `auto_frontier_lag_failure_digest.json` calls the run `requested_arc_boundary_not_reached` with no contradiction text.

Conflicts: none material. The log subagent at one point describes the merged `fix_pack` as "director-authored" and at another as "validator's"; the precise attribution is `validator-built, orchestrator-merged, ranked, then consumed by the BP prompt builder`. This wording variance does not change the factual core (the `arc_timeline` must_fix lost the merge ranking and the BP prompt never carried `Jan 3`).

## Observability Gaps

- Per-attempt records on the unsuccessful path are absent at every sink: `stage_attempts`, `director_selections`, `decisions.jsonl`, `pass_rate_monitor.json`, `runtime_audit.jsonl`, `attempt_raw_rationale`.
- Rejected blueprint candidate bodies for attempts 1–10 are not on disk. Only the structural advisory text on the terminal row survives.
- No prompt-cache hit/miss visibility is recorded at the per-attempt level for the 27 BP calls, even though `llm_io.jsonl` carries the prompts themselves.
- `timeline_entries` (DB) is empty across the run. `episode_bibles.time_passed` is an empty string for every persisted episode. There is no live ledger of story-time progression that could have surfaced the Jan 1 → Jan 3 drift earlier than the arc-end episode.
- `quality_metrics.jsonl`'s `dominant_contradiction_type` collapses to `blueprint_max_retries` rather than `arc_timeline`. Any dashboard or analyzer keyed on this field under-detects the class.
- `auto_frontier_lag_failure_digest.json` summarizes the run as `root_cause="requested_arc_boundary_not_reached"` without naming the contradiction.
- No Stage3 session-memory-envelope path exists in `modules/core/session_memory_envelope.py`. The carryover that propagated `Jan 1` from ep1 to ep4 flowed through previous-blueprint windows in the BP prompt, not through any envelope.
- The `stage3_user_abort` label conflates operator inaction after system retry exhaustion with explicit operator abort.

## 3-Pass Mini Audit

Pass 1 — structure and scope: PASS.

The report covers the order pack's required sections (Scope, Evidence, Findings, Risks, Recommendation, Subagent Cross-Check, 3-Pass Mini Audit), separates evidence from inference, names which component recorded or routed each outcome, and stays within Lane A boundaries. It does not propose code changes, does not adjudicate narrative truth, and does not write to `docs/temp/`.

Pass 2 — evidence and consistency: PASS.

Every numeric or string claim is anchored to a literal artifact (DB row, JSONL line, code path, or file path). Subagent-A and subagent-B independently confirmed each material fact. The two areas where the subagents framed an observation slightly differently (`arc_timeline` provenance, the wording of the `fix_pack` merge step) are reconciled in the cross-check section without changing the factual core. Console mojibake was not used as evidence; all Korean strings were taken from byte-level reads (DB and UTF-8 JSONL).

Pass 3 — readability and decision audit: PASS.

The chain "Stage2 metadata authority → Stage3 ep1 BP introduces Jan 1 → ep2/ep3 carry it forward → ep4 validator hard-fails → Director endorses inplace → Python routes full → BP retry prompt missing Jan 3 → 10 attempts fail identically → operator default-Enter → `stage3_user_abort`" is traceable and falsifiable. Each link points at concrete files and line ranges. The report does not claim the contradiction is resolved, does not propose a fix, and does not promote inference to evidence.

Confidence: 95%. The score is bounded by the unpersisted attempts 1–9; we read the terminal-attempt rows directly but reconstruct the prior nine attempts from `llm_io.jsonl` cycles and from the validator code path. That reconstruction is consistent with every other surface and with the eight `[TF-33]` events visible in the session log, so we treat the lineage as established but acknowledge that direct per-attempt rows do not exist to falsify it line-for-line.
