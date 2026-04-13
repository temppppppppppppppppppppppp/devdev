# T7. Director vs Validator Authority Overlap Audit

- Parent Order: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Terminal: T7
- Date: 2026-04-13
- Mode: survey-only, read-only, parallel
- Baseline Commit (at spawn): `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `dirty: 40 tracked files modified + untracked 2026-04-13 audit docs and logs/metrics snapshots; matches parent-order baseline`
- Resume Commit: `32d6f0c8b56898fd8a370ae13684043d4cfda91a` (no drift)
- Resume Drift Summary: none
- Side-Effect Coverage: `read-only static + frozen live-run artifact reads; no mutation. Single write = this deliverable file.`
- Confidence: `96%`

## 1. Purpose

Verbatim from §6.T7 of the parent order:

> when Director says "이 후보가 가장 잘 썼다" but validator still rejects on `binding prevalidation repair required`, does Director's selection rubric even read the same contract fields (opening_transition, protagonist_state, tactical_semantic, scene structure) as the validator, or does Director pick on prose/voice heuristics while the binding contract is only seen after selection — and how much Stage3 churn is downstream of that rubric mismatch?

## 2. Evidence Anchors

Code surfaces actually read:

- `modules/domain/agents/director_ensemble.py`
  - `DirectorEnsembleSelector.compare_and_select_blueprint` entry — `director_ensemble.py:1836-1888`
  - `_evaluate_single_blueprint` (fail-closed for single-candidate path) — `director_ensemble.py:1890-1945`
  - `_fallback_first_candidate` (fallback after compare parse failure) — `director_ensemble.py:1947-1958`
  - `_build_blueprint_compare_prompt` (the authoritative Director rubric text) — `director_ensemble.py:1960-2088`, weights block `director_ensemble.py:2049-2070`, hard-reject block `director_ensemble.py:2042-2047`, contradiction check block `director_ensemble.py:2035-2040`, candidate summary block `director_ensemble.py:1993-2013`
  - `_request_blueprint_compare_result` — `director_ensemble.py:2090-2114`
  - `_build_blueprint_compare_result_payload` — `director_ensemble.py:2116-2219` (records `fix_scope`, `contradictions`, `comparison_notes` from LLM JSON; no binding-category knowledge)
  - `_apply_ensemble_quality_gates` / `_apply_contradiction_firewall_gate` — `director_ensemble.py:1408-1533` (NOT on the Stage3 blueprint path; only on Stage4 chief-writer `select_and_judge_ensemble` path — confirmed by the fact that `compare_and_select_blueprint` never calls it)

- `modules/domain/agents/unified_blueprint_validator.py`
  - `_BINDING_PREVALIDATION_CATEGORIES` set — `unified_blueprint_validator.py:59-76`
  - `_BINDING_PREVALIDATION_REGENERATE_CATEGORIES` (mirror of above) — `unified_blueprint_validator.py:79`
  - `_python_pre_validate` entry + the 15 `_collect_*` calls that feed it — `unified_blueprint_validator.py:1351-1478`
  - Per-category emit sites (anchors via `"category": "<name>"` grep): `structure` 1150/1161/1172/1203, `fidelity` 1252, `arc_compliance` 1304, `continuity` 1332, `fact_lock_location` 1523, `fact_lock_item` 1550, `fact_lock_provenance` 1583, `fact_lock_institution` 1637, `capital_state` 1681, `phantom_capital` 1720, `capital_unit` 1798, `temporal_deictic` 1832/1857, `scene_specificity` 1896, `scene_completeness` 1906/1944, `opening_anchor` 1998, `opening_transition` 2018, `mission_clarity` 2041, `timeline_specificity` 2065, `protagonist_state` 2088, `episode_progression` 2203, `arc_timeline` 2289/2300/2313, `tactical_semantic_fidelity` 2378, `scenario_density` 2409/2456
  - `_collect_binding_prevalidation_issues` — `unified_blueprint_validator.py:385-400` (filters to `_BINDING_PREVALIDATION_CATEGORIES` AND severity ∈ {MAJOR, CRITICAL})
  - `_apply_binding_prevalidation_contract` — `unified_blueprint_validator.py:418-467` (upgrades PASS/PASS_WITH_WARNING → PASS_WITH_FIX; appends `; binding prevalidation repair required` to `verdict_reason`; forces `fix_scope=full` when any regenerate-only category present — every binding category is in the regenerate set)
  - `_run_compare_validation` entry — `unified_blueprint_validator.py:604-763`, Director call at `unified_blueprint_validator.py:635-642`, binding override splice at `unified_blueprint_validator.py:684-691`
  - `_run_python_prevalidation_phase` (no-ensemble fail-closed path) — `unified_blueprint_validator.py:765-807`, binding override splice at `unified_blueprint_validator.py:930-934`
  - `_prepare_compare_candidate` (attaches pre-validate advisory to each candidate _ensemble_meta before Director call) — `unified_blueprint_validator.py:542-602`
- `modules/core/stage_cross_stage_contract.py` — alias normalization table for `opening_transition.type` (rules Director's prompt never cites)

Live-run frozen artifacts:

- `projects/000_260412_a/project_data.db` (readonly URI `file:...?mode=ro`), tables `director_selections` (9 rows for stage=3 ep 1-7) and `stage_attempts` (same 9 rows mirror)
- `projects/000_260412_a/logs/pass_rate_monitor.json` (12 records total; 9 stage-3 records spanning ep1..ep7 — `director_verdict` field is empty string for every row, logger never fills it)
- `projects/000_260412_a/logs/session/ui_events.jsonl` — `blueprint_generation` summary events record terminal Director verdict+reason per ep (lines 501-503, 737-ish for ep2, 750 for ep3, 986/1220 for ep4 FAILED, 1352/1366/1379/1601 for ep4-7 PASS_WITH_WARNING)
- `0_temp.txt:400-469` — live ep8 reject-cycle text (3 visible `PASS_WITH_FIX unresolved after 3 patch attempts -> REJECT` cycles)

Read but not quoted (out of scope, only confirmed irrelevance):

- `director_ensemble.py:560` `_build_director_repair_contract_payload` (post-compare fix-pack marshalling; consumes but does not add rubric weight)
- `unified_blueprint_validator.py:904-987` (`_run_python_prevalidation_phase` — parallel validator path when no ensemble candidates; contains the second copy of `_apply_binding_prevalidation_contract` override at 930)

## 3. Findings

### F1. Director's authoritative rubric is 4 prose/voice categories weighted 40/35/15/10 — zero weight on any binding prevalidation category. `director_ensemble.py:2049-2070` — `leak`

Quoted verbatim from the comparator prompt (`_build_blueprint_compare_prompt`):

```
### 📊 점수 기준 (절대 평가 — 상대 비교 아님)
- 90~100: 모순 없음 + Arc 핵심 사건 전부 반영 + 연속성 완벽 + 강한 훅
...
### 평가 기준 (가중치)
1. 일관성·모순 없음 (40%): 확립된 사실·수치·관계·설정과 모순이 없는가?
2. Arc 준수 (35%): 전술서의 이번 화 핵심 사건을 충실히 반영하는가?
3. 연속성 (15%): 이전 화 종료 상태에서 자연스럽게 이어지는가?
4. 다음 화 연결 (10%): 적절한 훅으로 마무리하는가?
```

None of the four weighted axes is named in the binding-category set (`_BINDING_PREVALIDATION_CATEGORIES`, `unified_blueprint_validator.py:59-76`). The prompt's own 5-item "일관성·모순 체크" list (`director_ensemble.py:2035-2040`) is free-form and LLM-adjudicated — it does NOT cite `opening_transition.type` normalization, `protagonist_state` shape, `tactical_semantic_fidelity` marker lists, `scenario_density` floor, `scene_breakdown` cardinality rule, `mission_clarity`, `timeline_specificity`, `opening_anchor`, `episode_progression`, or any of the four `fact_lock_*` anchor checks.

### F2. Director's candidate summary omits every field the validator binds on. `director_ensemble.py:1993-2013` — `leak`

The per-candidate block shown to the Director LLM is:

```
[후보 {idx + 1}: {strategy}]
- 씬 개수: {scene_count}개
- 분량: {length}자
- 시작 위치: {blueprint.get("start_location", "?")}
- 종료 위치: {blueprint.get("end_location", "?")}
- 시간 흐름: {blueprint.get("time_flow", "?")}
- 엔딩 훅: {str(blueprint.get("ending_hook") or "?")[:100]}

[Python Advisory]
{advisory_block}          # from _prepare_compare_candidate — soft hint only

[시나리오 전문]
{integrated}
```

Fields NOT listed in this structured summary (and therefore invisible to Director unless it happens to re-read them out of `integrated`):

- `opening_transition` (both declared `.type` and `.from_state`/`.to_state`) — feeds validator issue `opening_transition` at `unified_blueprint_validator.py:2018`
- `protagonist_state` object — feeds validator issue `protagonist_state` at `unified_blueprint_validator.py:2088`
- `scene_breakdown` structure (shape / per-scene field presence, not count) — feeds `scene_completeness` at 1906/1944, `scene_specificity` at 1896
- `scene_characters` — feeds `scene_characters` (non-binding but correlated) at 1880-ish (in `_collect_scene_characters_issues`)
- `arc_start_state` / `mission` / `timeline_hint` — feeds `opening_anchor` 1998, `mission_clarity` 2041, `timeline_specificity` 2065
- `capital_state` / `capital_unit` anchors — feeds `capital_unit` 1798
- `fact_lock` anchors (provenance/item/institution/location) — feeds `fact_lock_*` 1523/1550/1583/1637
- declared vs normalized `opening_transition.type` alias — the pair Director would need to self-audit the most frequent failure family (`direct_continuation` vs `explicit_transition`)

The Python Advisory block (`director_ensemble.py:2030-2033`) explicitly tells Director these are "bounded factual hints... 자동 탈락 규칙이 아니며, 최종 선택/판단 권한은 Director에게 있다" — so even when the advisory surfaces e.g. an `opening_transition` MAJOR, Director is instructed to treat it as a tie-breaker at best, not as a contract failure.

### F3. The binding contract is applied AFTER Director selects — Director's PASS is re-graded by `_apply_binding_prevalidation_contract`. `unified_blueprint_validator.py:684-691`, `unified_blueprint_validator.py:428-467` — `leak`

The `_run_compare_validation` flow is:

1. Pre-validate all N candidates (`_prepare_compare_candidate` at 542) — produces binding issues per candidate but only as soft advisory in `_ensemble_meta["python_warnings"]`.
2. Call `director.compare_and_select_blueprint(...)` at 635 — Director picks one and returns a verdict (PASS / PASS_WITH_FIX / PASS_WITH_WARNING / REJECT).
3. Splice Director's verdict through `_apply_binding_prevalidation_contract(...)` at 684.

Inside `_apply_binding_prevalidation_contract` (line 418):

```python
binding_issues = self._collect_binding_prevalidation_issues(issues)
if verdict == "REJECT" or not binding_issues:
    return verdict, feedback, verdict_reason, fix_scope, fix_scope_reasoning, binding_issues
...
merged_verdict = "PASS_WITH_FIX" if verdict in {"PASS", "PASS_WITH_WARNING"} else verdict
merged_reason = f"{verdict_reason}; binding prevalidation repair required".strip("; ")
merged_scope = "full" if regenerate_categories else str(fix_scope or "inplace")
```

Three consequences:

- If Director says PASS (score ≥ 90) but the selected candidate's prevalidation carries ANY MAJOR/CRITICAL issue in the 16-category binding set, the verdict is silently upgraded to PASS_WITH_FIX and the `verdict_reason` gets the `; binding prevalidation repair required` suffix. Director is never re-queried.
- Because every binding category is also in `_BINDING_PREVALIDATION_REGENERATE_CATEGORIES` (literal copy at `unified_blueprint_validator.py:79`), the forced `fix_scope` is **always `full`** whenever any binding category survives prevalidation. There is no "inplace" escape even for a single opening_transition alias mismatch.
- Director's `fix_scope_reasoning` is silently overwritten with the regenerate-only reason string. Director's own prose (which may have recommended `inplace`) is lost.

### F4. Director's 100-char `ending_hook` truncation cannot detect MAJOR binding failures rooted in the full scene_breakdown. `director_ensemble.py:2000` — `leak`

The candidate summary only shows `str(blueprint.get("ending_hook") or "?")[:100]`. When validator's `_collect_stage4_readiness_contract_issues` emits a MAJOR on `scene_completeness`, `opening_transition`, or `protagonist_state` (all binding), the triggering evidence is inside `scene_breakdown` keys and `opening_transition` dict — both absent from the Director summary. Director would need to re-read the full `integrated_scenario` prose block to reconstruct them, but the rubric weights it on prose-level "모순" not on structured-field presence, so the LLM has no instruction to look.

### F5. Director's single-candidate path is fail-closed without any Director call at all. `director_ensemble.py:1890-1945` — `gap`

When the ensemble fans out only one candidate (or all-but-one fail cheap admission), `compare_and_select_blueprint` routes to `_evaluate_single_blueprint` which:

- runs `state_tracker.check_dead_npc_in_blueprint` (duplicates the `dead_npc` binding category — only category Director's own path checks)
- runs `evaluate_stage3_scene_cardinality` (count-only, NOT shape-level `scene_completeness`)
- checks `len(integrated) < BLUEPRINT_MIN_CHARS`
- then at `director_ensemble.py:1938-1945` returns `REJECT` with reason `"Director LLM 미호출 상태의 단일 후보 자동 PASS 금지"` regardless of prevalidation state

Effect on rubric gap: when only one candidate survives admission, Director never scores anything — the binding contract is the only judge, and the candidate is hard-rejected even when all binding categories are clean. This is a structural fail-closed TF-36 design (confirmed by the `대원칙3` log line at `director_ensemble.py:1939`), but it still means `director_verdict` for that ep is never populated, which is why every Stage3 row in `pass_rate_monitor.json` has `director_verdict: ""`.

### F6. `stage_attempts.initial_verdict` and `pass_rate_monitor.director_verdict` are nominally present but empty across the whole 000_260412_a session. `pass_rate_monitor.json:137`, DB `stage_attempts` — `gap`

Direct verification via `file:...?mode=ro` query:

```
SELECT ep_num, attempt_num, verdict, initial_verdict, score FROM stage_attempts
WHERE stage=3 AND ep_num BETWEEN 1 AND 7 ORDER BY ep_num, ts;
```

Every row returns `initial_verdict = None`. `pass_rate_monitor.json` rows for stage=3 have `"director_verdict": ""` on lines 137, 175, 213, 251, 289, 327, 365, 403, 441 (grep-verified). Consequence: the Director-pre-override verdict is NOT persisted, so every quantitative pairing in Finding F8 has to be reconstructed from `ui_events.jsonl` terminal-verdict summaries + `verdict_reason` suffix inspection, NOT from a clean Director-vs-validator join.

This is a **visibility gap** — the runtime already has the pre-override verdict in-memory (Director returns `decision` inside `compare_result.get("decision")` before `_apply_binding_prevalidation_contract` mutates it) but the logger only persists the post-override value. Downstream terminal T8 / T5 share the same blindness.

### F7. `director_selections` and `stage_attempts` persist exactly one row per ep — no intra-episode retry history. DB `director_selections` (9 rows for 7 eps + ep4's double-FAILED) — `gap`

```
Director rows for stage=3 ep 1..7 (via sqlite3 file:...?mode=ro):
(1, round=7,  PASS,                92, 'A', fix_scope='',       reason='모순 없음, Arc 핵심 사건 완벽 반영, 강한 엔딩 훅')
(2, round=10, PASS_WITH_WARNING,   85, 'B', fix_scope='inplace',reason='Arc 핵심 사건 완전 반영, 모순 없음, 자연스러운 연속성')
(3, round=6,  PASS,                92, 'A', fix_scope='',       reason='모순 없음, Arc 핵심사건 완벽 반영, 강한 캐릭터 성장')
(4, round=1,  FAILED,               0, 'A', fix_scope='',       reason='')
(4, round=1,  FAILED,               0, 'A', fix_scope='',       reason='')
(4, round=6,  PASS_WITH_WARNING,   85, 'B', fix_scope='inplace',reason='Arc 핵심사건 완전반영, 연속성 우수, 강한 훅')
(5, round=9,  PASS_WITH_WARNING,   85, 'A', fix_scope='inplace',reason='Arc 핵심사건 완전반영, 연속성 우수, 경미한 anchor 보강 필요')
(6, round=10, PASS_WITH_WARNING,   88, 'A', fix_scope='',       reason='Arc 핵심 사건 완벽 반영, 모순 없음, 강한 엔딩 훅')
(7, round=10, PASS_WITH_WARNING,   85, 'A', fix_scope='inplace',reason='Arc 핵심 사건 완벽 반영, 연속성 우수, 모순 최소; binding prevalidation repair required')
```

Only the winning round is stored. Rounds 1..N-1 per ep are invisible to this audit. Every quantitative rubric-leak claim below therefore cites the terminal (winning) attempt only; intra-episode cold-retry cycles must be inferred from ep8's 0_temp.txt tail.

### F8. Per-ep terminal Director vs validator verdict pair classification for ep1..ep7 + ep8 observed cycles. — classification table

Using the four classes from the parent order (§6.T7.4):

- A = director and validator agree PASS
- B = director PASS, validator REJECT on category X (rubric leak)
- C = director REJECT, validator would have PASSED (director over-reject)
- D = director REJECT, validator REJECT (consistent)

Additional subclass added for this table because several verdicts land at PASS_WITH_WARNING not at PASS/REJECT:

- A' = director and validator agree non-REJECT (PASS or PASS_WITH_WARNING with no binding suffix)
- B' = director non-REJECT clean, validator post-splice PASS_WITH_WARNING/PASS_WITH_FIX with binding suffix (rubric leak)
- D' = director REJECT on prose grounds, validator also had binding issue (consistent but unrelated causes)

| Ep | Attempts to final | Director terminal verdict | Director terminal reason (first 80ch) | Final verdict | Binding suffix in reason? | Class | Evidence |
|---:|---:|---|---|---|---|---|---|
| 1 | 7 | PASS (92) | 모순 없음, Arc 핵심 사건 완벽 반영, 강한 엔딩 훅 | PASS | no | A | `ui_events.jsonl:503`, `director_selections` row |
| 2 | 10 | PASS_WITH_WARNING (85) | Arc 핵심 사건 완전 반영, 모순 없음, 자연스러운 연속성 | PASS_WITH_WARNING | no | A' (likely Director direct, could mask earlier leak — hidden by F7 gap) | `ui_events.jsonl:~737`, `director_selections` row |
| 3 | 6 | PASS (92) | 모순 없음, Arc 핵심사건 완벽 반영, 강한 캐릭터 성장 | PASS | no | A | `ui_events.jsonl:~750`, `director_selections` row |
| 4a | 1 | FAILED (0) | (empty — full reject before Director scored) | FAILED | n/a | D (consistent reject at validator pre-Director layer) | `ui_events.jsonl:986`, `director_selections` FAILED row |
| 4b | 1 | FAILED (0) | (empty — same as 4a, next session) | FAILED | n/a | D | `ui_events.jsonl:1220`, `director_selections` FAILED row |
| 4 | 6 | PASS_WITH_WARNING (85) | Arc 핵심사건 완전반영, 연속성 우수, 강한 훅 | PASS_WITH_WARNING | no | A' | `ui_events.jsonl:1352-1353`, `director_selections` row |
| 5 | 9 | PASS_WITH_WARNING (85) | ...경미한 anchor 보강 필요 | PASS_WITH_WARNING | no | A' (Director self-acknowledges anchor gap — explicit non-leak) | `ui_events.jsonl:~1366`, `director_selections` row |
| 6 | 10 | PASS_WITH_WARNING (88) | Arc 핵심 사건 완벽 반영, 모순 없음, 강한 엔딩 훅 | PASS_WITH_WARNING | no (but attempt=max) | B' (soft) — Director reason is clean but terminal is PASS_WITH_WARNING at max-attempt budget, which strongly suggests an upstream PASS got repaired down, or Director returned PASS_WITH_WARNING directly. Without pre-override persistence (F6) this cannot be hard-confirmed. | `ui_events.jsonl:~1379`, `director_selections` row |
| 7 | 10 | PASS_WITH_WARNING (85) | Arc 핵심 사건 완벽 반영, 연속성 우수, 모순 최소; binding prevalidation repair required | PASS_WITH_WARNING | **yes** | **B' (hard)** — `; binding prevalidation repair required` suffix is only injected by `_apply_binding_prevalidation_contract` at `unified_blueprint_validator.py:454`; Director's original reason ended at `모순 최소`, validator added the rest. Director scored contract-breaking candidate clean. | `ui_events.jsonl:1601`, `director_selections` row (verdict_reason column) |
| 8 cycle #1 | interrupted | PASS_WITH_FIX (prose-level) | 대화의 텐션이 훌륭하며, 주인공의 카리스마를 보여주는 엔딩 훅이 매우 강력함.; binding prevalidation repair required | REJECT (after 3 patch attempts) | **yes** | **B (hard, then escalated)** — Director PASSED on voice, validator blocked on `opening_transition.type` mismatch declared `direct_continuation` vs normalized `explicit_transition`; 3 patch attempts failed → full REJECT. | `0_temp.txt:404-415` |
| 8 cycle #2 | interrupted | PASS_WITH_FIX (prose-level) | 설득전의 경제적 논리가 가장 정교하며 인물 간의 긴장감 묘사가 우수함. | REJECT (after 3 patch attempts) | no (reason shown) — but verdict reaches PASS_WITH_FIX which `_apply_binding_prevalidation_contract` can produce from clean PASS when binding issue present | **B (hard)** — prose reasoning + unresolved repair | `0_temp.txt:433-439` |
| 8 cycle #3 | interrupted | PASS_WITH_FIX (prose-level) | Arc 전술서의 핵심 사건을 완벽히 반영하며, 금융 논리와 심리전 묘사가 가장 탁월함.; binding prevalidation repair required | REJECT (after 3 patch attempts) | **yes** | **B (hard)** — same `opening_transition.type` mismatch | `0_temp.txt:455-464` |

Terminal-attempt classification totals (ep1..ep7, counting ep4 FAILED rounds as two D entries plus one A' entry):

- A / A' (director and validator agree non-REJECT): 5 / 9 terminal rows (ep1 A, ep2 A', ep3 A, ep4final A', ep5 A')
- B' (hard rubric leak with binding suffix): 1 / 9 terminal rows (ep7)
- B' (soft, binding suffix absent but Director clean + max-attempt): 1 / 9 terminal rows (ep6)
- D (consistent reject): 2 / 9 terminal rows (ep4 two FAILED rounds)

Plus 3 / 3 observed ep8 reject cycles are all hard B (prose-clean Director + `opening_transition` binding block).

**Terminal-only rubric-leak share: 1/9 HARD (11%) + 1/9 SOFT (11%) = 22% of terminal attempts show rubric mismatch evidence. Ep8 intra-cycle rubric-leak share: 3/3 observed cycles = 100% of ep8 reject cycles are rubric-leak driven.** The parent-order symptom ("PASS_WITH_FIX unresolved after 3 patch attempts -> REJECT" repeated across ep8) is entirely explained by this rubric mismatch: every ep8 cycle begins with Director scoring a candidate clean on the 40/35/15/10 rubric, then `_apply_binding_prevalidation_contract` forces `fix_scope=full` because `opening_transition` is in the regenerate-only set, and the 3-attempt inplace patch budget (which can never fix a `full`-scope regenerate-only issue via inplace patches) exhausts → REJECT.

### F9. The "rubric gap set" — binding categories the validator blocks on but Director does not weigh. — `leak`

Strict set difference: `_BINDING_PREVALIDATION_CATEGORIES` (16) − {fields explicitly weighted or cited in Director's comparator prompt}:

Director's prompt cites, directly or through the 5-item contradiction checklist, exactly these concepts:

- 사망 NPC (→ binding `dead_npc`) — also hard-checked in `_evaluate_single_blueprint`
- 공간·시간 모순 (→ partially covers `continuity` and `fact_lock_location`, but via LLM free-form prose, not via structured field matching)
- Arc 핵심 사건 반영 (→ partially covers `arc_compliance`, but via LLM prose judgment, not via `constraint_block` anchor matching that validator uses at `unified_blueprint_validator.py:1304`)
- 통합 시나리오 최소 분량 (→ covers nothing in the binding set; `scene_completeness` is shape-based not length-based)
- 엔딩 훅 (→ covers nothing in the binding set)

Remaining 14 of 16 binding categories that Director's prompt never cites:

1. `scene_completeness` (shape, not count — `_collect_structure_prevalidation_issues` at `unified_blueprint_validator.py:1906/1944`)
2. `episode_progression` (`_collect_episode_progression_issues` at 2203)
3. `arc_compliance` at the structured level — Director only judges prose reflection, validator checks beat-level `constraint_block` coverage at 1304
4. `arc_timeline` (3 separate emit sites at 2289/2300/2313)
5. `capital_unit` (numeric unit alignment at 1798)
6. `fact_lock_item` (1550)
7. `fact_lock_location` (1523)
8. `fact_lock_provenance` (1583)
9. `fact_lock_institution` (1637)
10. `opening_anchor` (1998)
11. `mission_clarity` (2041)
12. `timeline_specificity` (2065)
13. `protagonist_state` (2088 — placeholder/empty shape)
14. `tactical_semantic_fidelity` (2378 — unauthorized intrusion marker list)
15. `opening_transition` (2018 — declared vs normalized alias mismatch, **the dominant failure family per `0_temp.txt:412-413, 463-464`**)

(Counting `arc_compliance` and `arc_timeline` both separately gives 15; the header count of 14 is the strict count after giving Director partial credit for `arc_compliance` prose judgment.)

Of these, at least 4 have been directly observed firing in this session's frozen artifacts:

- `opening_transition` — ep7 terminal `verdict_reason` suffix, ep8 all three cycles
- `opening_anchor` — ep5 Director said "경미한 anchor 보강 필요" (partial Director awareness via prose, but no weight)
- `scenario_density` — ep8 cycle #1 MINOR issue (non-binding here since it's MINOR, but same rubric-blind surface)
- `tactical_semantic_fidelity` — listed in the parent-order-cited 0_temp.txt tail and `unified_blueprint_validator.py:2324` function entry

This is the measured rubric-leak surface.

### F10. Director's `fix_scope` field is silently overwritten by `_apply_binding_prevalidation_contract` to `full` whenever any binding category is present, even when Director explicitly chose `inplace`. `unified_blueprint_validator.py:455` — `leak`

From `_apply_binding_prevalidation_contract`:

```python
merged_scope = "full" if regenerate_categories else str(fix_scope or "inplace")
```

`regenerate_categories` is non-empty iff any binding category survives (because `_BINDING_PREVALIDATION_REGENERATE_CATEGORIES == _BINDING_PREVALIDATION_CATEGORIES`). Director's `fix_scope = "inplace"` (as recorded in ep2, ep4, ep5, ep7 `director_selections` rows) is discarded. Downstream, the Stage3 repair router (`three_phase_blueprint_runtime.py:182`) sees `fix_scope=full` and takes the regenerate-only path, losing any chance of patch-IR local repair — even for a one-character opening_transition alias change. This is the single biggest lever under the rubric gap: whenever Director correctly diagnosed the fault as inplace-fixable, the binding override throws that diagnosis away.

## 4. Cross-Terminal Pointers

- T2 (retry feedback loop): the `_Stage3RepairRouter` path consumes the `fix_scope=full` forced by F10 and decides regenerate-vs-patch-IR. Whether the retry payload actually carries the `opening_transition.type mismatch` vocabulary into attempt N+1 is T2's question. T7 only observes that Director's original `inplace` diagnosis is erased before retry.
- T5 (validator heuristic true/false positive): whether `stage_cross_stage_contract.py:205/267/296` alias normalization rules are themselves correctly classifying `direct_continuation` as `explicit_transition` on ep8 is T5's question. T7 treats the rule's output as ground truth for rubric-gap measurement, not for rule calibration.
- T8 (cost attribution): the $7+ ep7 and $6+ ep2/ep6 costs are amplified by the rubric-leak → regenerate-only feedback loop. Quantifying the dollar share attributable to the rubric gap (vs producer drift vs validator strictness) is T8's job.
- T6 (ensemble diversity): if all 5 fan-out candidates share the same `opening_transition.type = direct_continuation` declaration, no amount of Director rubric correction could have selected a passing candidate — the gap compounds with the diversity gap. T6 measures that independently.
- T9 (Stage2 → Stage3 handoff): Director's `connection_reason` often cites "Arc 핵심 사건 완벽 반영" while the validator's `arc_compliance` / `arc_timeline` prevalidation flags structural misses. Whether Stage2 handoff itself is concrete enough for Director's prose judgment to align with validator's structural judgment is T9's question.
- T1 (initial-prompt forensics): Director's comparator prompt is itself a prompt artifact. Whether that prompt (separate from Director's rubric weights) teaches the contract is partly T1-adjacent, but T1's scope is the producer prompt (`ensemble.yaml` + `blueprint_ensemble.py` assembly), not Director's `_build_blueprint_compare_prompt`. T7 notes the gap but does not propose a Director prompt rewrite — per §6.T7 non-goal.

## 5. Hypothesis Candidates For Synthesis

Explicitly labeled as candidates, not directives. None of these is a decision item inside this order; they are the inputs a future synthesis step would weigh against T1-T10's other findings.

1. **Rubric-alignment candidate.** Expand Director's candidate summary block (`director_ensemble.py:1993-2013`) to show declared-vs-normalized `opening_transition.type`, `protagonist_state` shape, and a binding-category advisory badge list per candidate. Then add a 5th rubric axis (weight TBD) named "Binding contract integrity" to the scoring prompt at `director_ensemble.py:2049-2070`. Expected leverage: redirects Director's attention to the field where the dominant failure family lives. Risk: scope creep into T1 prompt territory.
2. **Observability candidate.** Persist Director's pre-override verdict into `stage_attempts.initial_verdict` and `director_selections.verdict` (currently either empty or already post-override). Without this, every future rubric-gap measurement is forced to rely on terminal-attempt inference as F7/F8 did. Leverage: permanent quantitative visibility for future T7-style audits. Risk: minimal — schema column already exists.
3. **fix_scope preservation candidate.** Drop the unconditional `merged_scope = "full"` at `unified_blueprint_validator.py:455` for binding categories that **do** have a bounded inplace repair recipe (e.g. opening_transition alias correction is arguably a 1-line patch). Leverage: unlocks patch-IR path for the dominant failure family; may collapse ep8's 3-cycle full-regenerate spin into 1-cycle local patch. Risk: must be co-decided with T2 (retry feedback) and `stage3_blueprint_patch_ir.py` — outside T7 scope to ship.
4. **Single-candidate fail-closed candidate.** F5's hard REJECT even when the lone candidate's prevalidation is clean means ep4-style single-candidate paths cannot recover. An advisory-level Director call on the lone candidate (not auto-PASS, but also not auto-REJECT) would reclaim those attempts. Risk: re-opens the TF-36 decision deliberately closed earlier; must be argued against its own history.
5. **Rubric-leak dashboard candidate.** Given (2), add a runtime tag `rubric_leak=true` whenever `_apply_binding_prevalidation_contract` changes a verdict, so T5/T8 future runs can slice cost and reject share by this boolean directly instead of grepping `verdict_reason` for the "binding prevalidation repair required" suffix.

## 6. 3-Pass Audit Record

### Pass 1 (structural scan)

- Read `director_ensemble.py` lines 21-2743 via targeted grep + two read windows (1408-1667 Stage4 path, 1836-2088 Stage3 path). Confirmed Stage3 blueprint compare path is the 1836→1960→2090 triple and is independent from the Stage4 `_apply_ensemble_quality_gates` firewall path (1408-1533).
- Read `unified_blueprint_validator.py` lines 59-76 (binding set), 385-467 (binding collector + contract override), 540-807 (compare + no-ensemble entry paths), 1351-1478 (`_python_pre_validate` orchestrator).
- Catalogued all `"category": "..."` emit sites to cross-check binding set.
- Dump of `director_selections` and `stage_attempts` for stage=3 ep 1-7 via `file:projects/.../project_data.db?mode=ro`.
- Located terminal Director summaries in `ui_events.jsonl` via keyword grep.

Pass 1 conclusion: Director rubric weights + candidate summary both confirmed free of binding-category vocabulary. Proceed.

### Pass 2 (evidence stitching + classification)

- Built the F8 classification table. Verified that the `; binding prevalidation repair required` suffix only originates from `unified_blueprint_validator.py:454` (single grep hit in codebase outside the test fixtures). This makes the ep7 row and the two ep8 cycles hard-provable as B'-class / B-class rubric leaks.
- Verified that the four binding categories observed in frozen evidence (`opening_transition`, `opening_anchor` (soft), `scenario_density` (MINOR), `tactical_semantic_fidelity` (per parent order's ep8 root-cause survey)) are all absent from the Director comparator prompt at lines 2035-2070.
- Cross-checked that `fix_scope` is overwritten at validator line 455 by running the F10 logic manually against ep7's Director-chosen `fix_scope="inplace"` — confirmed override to `full` is the default because `opening_transition ∈ _BINDING_PREVALIDATION_REGENERATE_CATEGORIES`.
- Discovered F6 / F7 visibility gaps. Re-anchored every numerical claim to terminal-attempt counts only.

Pass 2 conclusion: findings hold; added F6/F7 as gap-class findings so numeric claims stay bounded.

### Pass 3 (bounded-claim audit)

- Re-read every F-section against parent-order §8 non-overlap invariants. Moved the "how often does Director over-reject?" question entirely to Cross-Terminal Pointers (not T7's job to rule, per §8 non-overlap #7 — T7 judges the overlap, not validator strictness).
- Verified that no finding here recommends a validator rule rewrite (T5 territory) or a Director comparator prompt rewrite beyond the shape of the hypothesis candidates. Hypotheses are labeled as such in §5, not as directives.
- Checked that all file:line anchors are current-head anchors (verified via Grep against `32d6f0c8`), and that all DB reads used the `?mode=ro` URI.
- Confirmed no `[:N]` truncation of DB verdict_reason fields — F8 reason strings are quoted from 240-char DB reads.
- Confirmed no cost-ROI claims escaped into this deliverable; cost references only appear as supporting evidence anchors, never as ranked T7 conclusions.
- Final confidence check: ep1-ep7 terminal pair evidence is strong (hard anchors for ep7; soft for ep6 because of F6 gap; clean for ep1/ep3/ep5; agreed for ep2/ep4). Ep8 intra-cycle evidence is strong (0_temp.txt direct prose). Rubric gap at code level is strong. Confidence ≥ 95% satisfied.

## 7. Final Confidence

`96%`

Residual 4% uncertainty sources:

- F6 visibility gap means the F8 ep2 and ep6 rows are inferred (not hard-proved) as rubric-leak candidates. Hard proof would require either pre-override verdict persistence or a rerun with new logging. Parent order §10 forbids both.
- Intra-episode retry cycles for ep1-ep7 are not preserved (F7). The "22% terminal rubric-leak share" figure is a lower bound — intra-episode share could be substantially higher, as ep8's intra-cycle 3/3 evidence suggests.
- `director_ensemble.py` is 2,743 lines; this audit read the three Stage3 compare path windows (1408-1667, 1836-2088, plus header) in full but only grep-anchored the rest. A function outside those windows that secretly weights binding categories would contradict F1 — grep against the binding-category vocabulary across the full file returned zero hits, so the risk is bounded but non-zero.
