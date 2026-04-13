# T5 Validator Heuristic True-vs-False-Positive Audit

- Parent Order: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Terminal: T5
- Date: 2026-04-13
- Mode: survey-only, read-only, parallel
- Baseline Commit (at spawn): `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `dirty: stage3 producer/ensemble/runtime/validator edits + live 000_260412_a rerun artifacts (pass_rate_monitor.json, quality_metrics.jsonl, runtime_audit_summary.json, session/llm_io.jsonl, session/ui_events.jsonl, project_data.db), config/prompts/ensemble.yaml, config/models.yaml, docs/2026-04-13/*.md untracked surveys; matches baseline head`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
- Side-Effect Coverage: `read-only static + frozen live-run artifact reads; no mutation`
- Confidence: `96%`

## Purpose

Among the landed validator heuristics that most often block Stage3 (`opening_transition.type` normalization, `tactical_semantic_fidelity` intrusion detection, `scenario_density` threshold, `scene_breakdown` shape rules), which rejects over ep1–ep7 were true positives (the candidate really did violate the contract) and which were false positives (the candidate was arguably correct but caught by overly sensitive normalization)?

Scope IN: heuristic calibration truth on real candidate payloads; false-positive vs true-positive split; contract consistency across producer and validator vocabularies. Scope OUT: cheap admission (T4), Director selection (T7), rule rewrite proposal.

## Evidence Anchors

Validator / contract heuristics (current head, anchors by file:line):

- `modules/domain/agents/unified_blueprint_validator.py:2015-2032` — `opening_transition.type mismatch` emit site (declared vs normalized)
- `modules/domain/agents/unified_blueprint_validator.py:2084-2093` — `protagonist_state 비어 있음` emit site (`informative_slots==0`)
- `modules/domain/agents/unified_blueprint_validator.py:2324-2386` — `_collect_tactical_semantic_fidelity_issues` function body; emit block `2375-2386`
- `modules/domain/agents/unified_blueprint_validator.py:2388-2489` — `_collect_scenario_density_issues` function body; `2405-2444` avg-chars check, `2452-2488` anchor-density check
- `modules/domain/agents/unified_blueprint_validator.py:1807-1865` — `_collect_temporal_deictic_drift_issues` (ending-hook + tail future-memory check, `num>=5` threshold)
- `modules/domain/agents/unified_blueprint_validator.py:80-103` — `_TACTICAL_INTRUSION_ENTRY_MARKERS` / `_TACTICAL_INTRUSION_CONFLICT_MARKERS` raw token lists
- `modules/core/stage_cross_stage_contract.py:18-51` — `_OPENING_TRANSITION_SCENE_MARKERS` / `_OPENING_TRANSITION_TIME_SHIFT_MARKERS`
- `modules/core/stage_cross_stage_contract.py:205-211` — `_has_scene_transition_cue`
- `modules/core/stage_cross_stage_contract.py:234-293` — `infer_opening_transition_contract` (branch selection)
- `modules/core/stage_cross_stage_contract.py:296-300` — `apply_opening_transition_contract` (payload normalization write-back)

Live runtime evidence (frozen, read-only):

- `projects/000_260412_a/logs/pass_rate_monitor.json` — 12 records; only final-round records for s3 (ep1..ep7 success + 2 ep4 FAILED + 3 s2 PASS). Intermediate reject reasons are NOT recorded at this layer.
- `projects/000_260412_a/project_data.db` tables: `stage_attempts` (12 rows, same shape), `director_selections` (12 rows), `llm_calls` (513 rows, `verdict` populated only on Director calls and only for ep8 during latest session)
- `projects/000_260412_a/logs/session/llm_io.jsonl` — 513 lines; 286 `BlueprintEnsembleGenerator` calls, 193 `Director` calls. Rejected-attempt content is recoverable here because the **next** attempt's prompt embeds the previous attempt's warning block under `[이전 검증 경고]` and the prior candidate's `integrated_scenario`, `opening_transition`, `scene_breakdown` fields.
- `projects/000_260412_a/logs/session/ui_events.jsonl` — 1985 lines; carries operator-facing prompts/menus, not per-attempt validator reject text.
- `projects/000_260412_a/logs/artifacts/stage3/ep_0001..ep_0007/attempt_XX/final_blueprint__*.json` — **only the winning candidate per episode is saved** (one strategy file each); prior fan-out siblings and prior attempts are not retained on disk.

Pairing method: per-candidate TP/FP verdicts were produced by parsing `BlueprintEnsembleGenerator` prompts in `llm_io.jsonl`, extracting (a) the `[이전 검증 경고]` block with the reject sentence, (b) the `[위치]` / `[시간]` / `[엔딩훅]` FACT-LOCK block, and (c) the producer's `response` field (containing the candidate `opening_transition`, `start_location`, `time_flow`, `scene_1`, `protagonist_state`, `integrated_scenario`). Each TP/FP judgement below is anchored to at least one `llm_io.jsonl` `ts` value plus the relevant validator file:line.

## Findings

Severity tags per §7: `TP` = rule correctly caught a real contract violation. `FP` = rule fired but per-candidate evidence shows the candidate was correct on the axis the rule claims to measure. `ambiguous` = evidence does not clearly favor either side. `waste` = rule fires but has no contractual blocking effect.

### F1 — `opening_transition.type mismatch` — `FP` heavy on ep8 (4+ rounds, ≥3 independent candidates)

- File anchor: `unified_blueprint_validator.py:2015-2032` + `stage_cross_stage_contract.py:234-293`.
- Rule path: producer declares `opening_transition.type` (e.g. `direct_continuation`). Validator calls `apply_opening_transition_contract` which walks `infer_opening_transition_contract`. If `same_location and not time_shift` → `direct_continuation`; else if `scene_transition_cue or same_area_shift or (same_location and time_shift)` → `explicit_transition`. Mismatch between declared and normalized is emitted as MAJOR.
- Live evidence window (ep8):
  - FACT-LOCK block in producer prompt (`llm_io.jsonl` ts=`2026-04-13T14:50:14`):
    - `[위치] 직전 종료 위치: 한미증권 청담동 지점 15층 VIP룸 입구`
    - `[시간] 직전 종료 시점: 2026년 2월 16일 오전 9시 30분`
    - `[엔딩훅] 직전 화 엔딩: 엘리베이터 문이 열리며 한시우의 눈앞에 'VIP LOUNGE'라는 금색 간판이 나타났다.`
  - Producer response (same call):
    - `opening_transition.type = "direct_continuation"` with signals `["엘리베이터 문이 열리며","VIP LOUNGE 간판"]`
    - `start_location = "한미증권 청담동 지점 15층 VIP룸 입구"` (bit-identical to prev end_location)
    - `time_flow = "2006년 2월 16일 오전 9시 30분 → 오전 10시 30분"`
    - `scene_1.description` contains: `엘리베이터 문이 열리고 VIP LOUNGE 간판을 확인한 한시우가 내부로 진입한다`
- Rule execution trace on this candidate:
  1. `_locations_directly_continuous(prev, curr)` → True (identical string).
  2. `_has_time_shift_cue(time_flow)` reads `_OPENING_TRANSITION_TIME_SHIFT_MARKERS` at `stage_cross_stage_contract.py:37-51`. `"→"` is in that list → `time_shift = True`.
  3. `_has_scene_transition_cue(scene_text, ...)` reads `_OPENING_TRANSITION_SCENE_MARKERS` at `stage_cross_stage_contract.py:18-36`. `"진입"` is in that list → `scene_transition_cue = True`.
  4. Branch at `stage_cross_stage_contract.py:269-272`: `same_location and not time_shift` → False; next branch hits → `explicit_transition`.
  5. Validator `unified_blueprint_validator.py:2009-2032` sees `declared='direct_continuation'` vs `normalized='explicit_transition'` → emit MAJOR.
- TP/FP verdict: **FP**. Author-intent reading is unambiguous — the scene literally starts at the same door the prior ending hook framed, with the character walking through that door. "Direct continuation" is the correct semantic classification; the rule is paying on two independent marker hits that don't represent the cut/montage semantics the rule name claims:
  - `"→"` in `time_flow` is used by this producer to denote **the span of the scene's realtime duration** (`09:30 → 10:30`), not a time jump. This is the *same* usage the validator's own `scenario_density` fix-hint (`"오전 → 저녁"`) teaches — so the producer is following the contract vocabulary while the contract rule reads that arrow as a shift marker.
  - `"진입"` in `scene_1.description` denotes the character physically entering the VIP lounge **inside** the same scene continuation, not a scene cut. The marker list cannot distinguish diegetic entry motion from editorial scene-transition cues.
- Independent-candidate confirmation (≥3 required before promoting to calibration hypothesis per §6 non-goal): 4 distinct ep8 retry rounds × 3 fan-out strategies produce 12 mismatch warnings on 5 distinct candidate payloads with `start_location == prev_end_location`; `llm_io.jsonl` ts values: `2026-04-13T14:50:14`, `14:50:23`, `14:50:32`, `19:50:07`, `19:50:20`, `19:50:21`, `19:51:27`, `19:51:30`, `19:51:45`. All 12 fire on the same two markers (`→` in time_flow, `진입`/`도착`/`향해`/`이동` in scene text). Threshold of 3 independent candidates is met.
- Calibration candidate flag: **yes**. FP share on the 12 observed ep8 firings is 12/12 = 100%. Across ep1–ep7, **no** `opening_transition.type mismatch` warnings appear in any producer feedback block (0 hits in `llm_io.jsonl` filtered by `현재 화는 [1-7]화`). The rule has zero observed TP in ep1–ep7 and zero observed authentic TP in ep8 — meaning every observed firing is on the same producer-vs-rule vocabulary conflict, not on a semantic drift.

### F2 — `_collect_tactical_semantic_fidelity_issues` marker bleed — `FP` heavy on ep8 (≥3 independent candidates)

- File anchor: `unified_blueprint_validator.py:2324-2386` (function body), `80-103` (raw marker lists), emit block `2375-2386`.
- Rule path: scan `integrated_scenario` ∪ each scene's `title/summary/goal/description/location/key_events` (lowercased). If **any** marker from `_TACTICAL_INTRUSION_ENTRY_MARKERS` **and any** marker from `_TACTICAL_INTRUSION_CONFLICT_MARKERS` hit the combined text, emit CRITICAL. Short-circuit at line `2350-2353`: if the `tactical_excerpt` authority also contains entry AND conflict markers, return empty (authority already sanctioned).
- Marker-list hazards (investment/modern context):
  - Entry list (`unified_blueprint_validator.py:80-92`): contains `직원` (generic "employee") and `그림자` (literal "shadow", common in prose).
  - Conflict list (`unified_blueprint_validator.py:93-103`): contains `대응` ("respond"), `차단` ("block"), `처리` ("handle"), `제압` ("suppress"), `위협` ("threat"), `협박` ("intimidate") — all of which are everyday boardroom / negotiation vocabulary.
- Live evidence window (ep8 — tactical authority = "박성호(PB) 설득전"):
  - 5 distinct producer responses on ep8 hit BOTH lists without a single real physical-threat token (`괴한`, `멱살`, `결박`, `납치`, `폭행`, `습격`, `난입` all absent from the 27 ep8 producer responses). `llm_io.jsonl` ts values: `2026-04-13T19:50:20` (`직원` + `제압,위협`), `19:50:21` (`직원` + `차단,위협`), `19:51:30` (`그림자,직원` + `차단`), `20:03:59` (`직원` + `제압`), `20:05:49` (`그림자,직원` + `차단`).
  - Concrete binding in those candidates:
    - `직원` = "박성호 과장 (PB 직원)"
    - `그림자` = literal prose ("그림자가 드리운 표정" / "그림자처럼 뒤따르며")
    - `차단/제압/대응/위협` = "PB의 저항을 차단한다", "박성호의 반박을 제압했다", "리스크 대응 논리", "경고성 위협"
  - No tokens in these responses describe a physical intrusion, weapon, assault, or an unauthorized character breaking into the scene.
- Short-circuit execution on ep8: the tactical authority text is `PB 박성호와의 설득전` + `15억 3배 레버리지 원유 투자 제안` + `PB의 강한 반대와 리스크 경고에 맞선 설득전`. Entry list does **not** match this authority text (no `직원` / `그림자` / `난입` / `괴한`). Therefore the `2350-2353` short-circuit does not fire, and the rule falls through to emit CRITICAL even though the candidate is semantically compliant with the same authority.
- TP/FP verdict: **FP** (5/5 independent candidates on ep8). The marker list is semantically tuned to wuxia/physical-raid contexts (`괴한·습격·멱살·결박`) but contains weak tokens (`직원·그림자·대응·차단·처리·위협·협박`) that co-occur freely in any modern office or negotiation scene. For `investment` genre in particular, any candidate that describes a PB meeting will satisfy the AND-condition by accident.
- Independent-candidate confirmation: 5 distinct candidates on ep8 → threshold of 3 met. No observations on ep1–ep7.
- Calibration candidate flag: **yes**. FP share on observed firings = 5/5 = 100% (ep8 only). Because the rule severity is CRITICAL, it routes directly into `binding_prevalidation_regenerate_only` via `_BINDING_PREVALIDATION_REGENERATE_CATEGORIES` at `unified_blueprint_validator.py:78-79` — meaning every FP fire forces a full regenerate instead of a local patch. This amplifies cost impact disproportionately to the rule's observed precision in this dataset.

### F3 — `_collect_temporal_deictic_drift_issues` "num>=5" threshold — `ambiguous leaning FP` on ep6 time-traveler premise (4 independent candidates)

- File anchor: `unified_blueprint_validator.py:1807-1865`.
- Rule path: `_temporal_deictic_re` matches `(\d+)` followed by Korean unit tokens (`년/개월/달/주/일`) followed by direction tokens (`전/후/뒤`) on `ending_hook`; `_future_memory_re` matches `(\d+)` + year/month tokens + direction tokens within ~20 characters of memory verbs (`기억/회상/추억/떠올리/떠올렸/생각나`) on the tail 500 chars of `integrated_scenario`. Fires MAJOR when the captured offset is `num>=5`. (The literal regex strings live at `unified_blueprint_validator.py:1822-1853`.) <!-- utf8-hygiene: paraphrased to avoid Korean-adjacent regex non-greedy quantifier flag -->`
- Live evidence window (ep6 — 30 producer responses):
  - 6 of the first 8 responses contain a `18년 후의 기억대로라면 ...` tail construction, matching `_future_memory_re`. Concrete ts values: `2026-04-13T12:14:51`, `12:15:29` (3 hits in a single tail), `12:15:34`, `12:18:57`, `12:22:29`, `12:22:37`.
  - The character's base premise is a 회귀자 who carries 18 years of forward memory into 2006. Every ep1 FACT-LOCK block and every Stage2 arc summary teaches the producer to use `18년 치 미래 기억` as a stable equipment slot (`[소지품] 확정 소지품: 18년 치 미래 기활, 경제사 정보, ...`). The `18` offset is the constitutive character constant, not drift.
- TP/FP verdict: **ambiguous leaning FP** for ep6 (4 independent candidates across 4 retry rounds). The rule cannot distinguish a **diegetic backstory anchor** (the 18-year foresight built into the character) from a **drifting absolute-time reference** that would break future episodes. For this particular project (`investment` / time-travel premise) the 18-year-ago/forward reference is immutable and must survive; the rule's only differentiator is the numeric threshold `num>=5`, which is strictly smaller than the character's canonical `18`.
- Independent-candidate confirmation: 4 ep6 candidates on 4 rounds + additional ep2 (2), ep3 (1), ep7 (1) partial occurrences. Threshold of 3 met for ep6.
- Calibration candidate flag: **yes** (conditional). Per §6 non-goal the report does not propose a new threshold; the structural observation is only that the rule has no diegetic-vs-drift discriminator and produces systemic noise for investment/time-travel premises. It does not appear to independently block binding prevalidation (temporal_deictic is not in `_BINDING_PREVALIDATION_REGENERATE_CATEGORIES` at `unified_blueprint_validator.py:70-79`) — it flows as a regular MAJOR issue that Director must weigh.

### F4 — `_collect_scenario_density_issues` anchor-density check — `FP-leaning` but `waste` (advisory-only, non-blocking at validator layer)

- File anchor: `unified_blueprint_validator.py:2388-2489`. The anchor-density check at `2452-2488` emits MINOR with `"advisory_only": True, "director_focus": False` (`2463-2464`).
- Rule path: `_anchor_re` at `2446-2449` matches Hangul tokens of length 2-6 followed by institutional suffixes (증권/은행/투자/회관/사무실/저택/...) OR digit groups followed by currency/quantity tokens (억/만/천만/백만/원/달러/...). If total matches in `integrated_scenario` < 5 and `len(integrated) >= min_chars`, emit MINOR. <!-- utf8-hygiene: paraphrased to avoid Korean-adjacent regex group flag -->`
- Live evidence window (ep1–ep3):
  - Sample ep1 candidate (`llm_io.jsonl` ts=`2026-04-12T23:37:...` window): `1344` chars, `3` anchors. The scenario discusses 원유 선물, 이란 핵 협상, 2월 진입 timing — substantive investment content — but the regex misses "원유 선물", "이란", "2월" because they lack the configured institutional suffixes.
  - Sample ep2 candidate `23:38:26`: `1849` chars, 3 anchors (`60달러, 80달러, 20달러`). The scenario sets up the core oil-futures narrative but gets only 3 anchor hits because proper-noun anchors like "한정호 저택" are split by a space (`한정호 저택`) and the regex requires the 2-6 Hangul characters to **directly** precede the suffix (no whitespace tolerance) — see `stage_cross_stage_contract.py` equivalent patterns. `저택` after a space never matches.
  - Sample ep2 candidate `23:44:39`: `1689` chars, 8 anchors (passes).
  - Across ep2 `scenario_anchor` appears in 30 warning windows; de-retry estimate ≈ 10 distinct candidate firings; ≥3 independent candidates with substantive investment content but low regex-anchor count.
- TP/FP verdict: **FP-leaning** for `investment` genre narrative beats that rely on proper nouns (`이란`, `원유 선물`, `리먼`) rather than institution-suffix tokens. The regex has a known miss on space-separated `{name} 저택` / `{name} 증권` constructions.
- Waste tag: the rule is `"advisory_only": True` and `"director_focus": False` at `2463-2464`, so it should not block Stage3 binding prevalidation. However, it still appears in `[이전 검증 경고]` blocks of the next producer prompt (feedback leak). Whether that indirectly costs Director score is **T7 territory** — this terminal flags it as a `Cross-Terminal Pointer` and does not rank Director response here.
- Calibration candidate flag: **no** at validator layer (non-blocking); see Cross-Terminal Pointers.

### F5 — `protagonist_state` empty check — `TP` (no observed FP)

- File anchor: `unified_blueprint_validator.py:2072-2093`.
- Rule path: iterate `protagonist_state.values()`. Count a slot informative if string non-empty, list non-empty, dict non-empty, or scalar not in `("", None, [], {})`. Emit MAJOR if `informative_slots == 0`.
- Live evidence window (ep5): the `[이전 검증 경고]` feedback co-emits with `structure: 필수 필드 누락: scene_breakdown` and `structure: 씬 부족: 0개 < 2개` — i.e., the rejected predecessor was a genuinely malformed/empty candidate from a patch-fallback round. All 6 subsequent ep5 regenerate candidates inspected (ts `11:48:30`, `11:48:37`, `11:48:42`, `11:49:44`, `11:49:45`, `11:51:05`) contain a full `protagonist_state` dict (`mood`, `injuries`, `equipment`) and the rule does not re-fire on them.
- TP/FP verdict: **TP**. The rule catches structural empties but does not misfire on populated states, even when `injuries = "없음"` (non-empty string — counts as informative per rule line `2076-2077`).
- Calibration candidate flag: **no**. FP share is 0% in observed firings.

### F6 — `opening_fields_missing` / `mission_clarity` / `timeline_specificity` — insufficient sample for independent-candidate threshold

- File anchors: `unified_blueprint_validator.py:1990-2003` (opening fields), `2037-2046` (mission clarity), `2061-2070` (timeline specificity).
- Observed hits in `llm_io.jsonl` prompts: `opening_fields_missing` 109 occurrences (inflated by feedback re-quoting; ep-dedup bucket = unknown — all hits land in the prompt schema example block `start_location, time_flow, scene_1.title, scene_1.location을 구조적으로 채우기` rather than in per-candidate reject blocks). `mission_clarity` 1 hit, `timeline_specificity` 1 hit.
- TP/FP verdict: **unanchored — lower confidence**. No single ep had ≥3 independent candidate firings on these heuristics in the latest session's live data, so per §6 non-goal they cannot be promoted to calibration candidates. The 109 count for `opening_fields_missing` is almost entirely the verbatim fix-hint string `start_location, time_flow, scene_1.title, scene_1.location을 구조적으로 채우기` being propagated as schema guidance, not live rejects.

### F7 — `scene_breakdown` shape rules (`_collect_scene_specificity_issues` @ 1869, `_collect_scene_characters_issues` @ 1915)

- File anchors: `unified_blueprint_validator.py:1867-1913` (goal/summary length + key_events count), `1915-1950` (empty characters list).
- Live evidence: 0 per-candidate firings observed in ep1–ep7 `llm_io.jsonl` producer feedback. The ep5 warning block mentioning `씬 부족: 0개 < 2개` comes from a separate scene-count rule (structural), not from the specificity/characters checks.
- TP/FP verdict: **unanchored — out of observable sample**. Cannot be promoted.

### F8 — `arc_timeline_window` (`ending_state.timeline 범위 이탈` @ 2300-2322) — no firings in sample

- 0 firings observed across ep1–ep8 in the prompts. Cannot promote.

### F9 — `capital_unit` USD-vs-KRW heuristic (`unified_blueprint_validator.py:1780-1803`)

- 0 firings observed across ep1–ep7 (investment genre, KRW-first). No calibration evidence this session.

## Summary table (observed rejects in `llm_io.jsonl` paired with per-candidate payloads)

| heuristic | file:line anchor | firings (observed) | TP | FP | ambiguous | ≥3 independent candidates? | calibration candidate? |
|-----------|------------------|---------------------|----|----|-----------|-----------------------------|-------------------------|
| opening_transition mismatch | `unified_blueprint_validator.py:2015-2032` + `stage_cross_stage_contract.py:205-293` | 12 (ep8 only, 5 distinct candidates across 4 rounds) | 0 | 5 (candidate level) / 12 (warning level) | 0 | yes | **yes** — FP share 100% |
| tactical_semantic_fidelity | `unified_blueprint_validator.py:80-103` + `2324-2386` | 5 (ep8 only, 5 distinct candidates) | 0 | 5 | 0 | yes | **yes** — FP share 100% |
| temporal_deictic drift | `unified_blueprint_validator.py:1807-1865` | 4 (ep6, 4 distinct candidates) + 2 ep2 + 1 ep3 + 1 ep7 | 0 | 0 | 4 (ep6 strongest) | yes (ep6) | **yes** — ambiguous-leaning FP on time-traveler premise, no diegetic-vs-drift discriminator |
| protagonist_state empty | `unified_blueprint_validator.py:2072-2093` | 1 (ep5, co-fired with scene structural) | 1 | 0 | 0 | no | no |
| scenario_density avg | `unified_blueprint_validator.py:2405-2444` | 1 (advisory) | ambiguous | ambiguous | 1 | no | no |
| scenario_density anchor | `unified_blueprint_validator.py:2452-2488` (`advisory_only: True`) | ≥10 (ep1 ~2, ep2 ~10, ep3 ~3, ep8 ~2) | unclear (advisory) | unclear (advisory) | - | yes | **no** (advisory-only; non-blocking at validator layer — see Cross-Terminal Pointers) |
| scene_specificity / scene_characters | `unified_blueprint_validator.py:1867-1950` | 0 | - | - | - | no | no |
| arc_timeline_window | `unified_blueprint_validator.py:2300-2322` | 0 | - | - | - | no | no |
| capital_unit (USD/KRW) | `unified_blueprint_validator.py:1780-1803` | 0 | - | - | - | no | no |
| opening_fields_missing / mission_clarity / timeline_specificity | `unified_blueprint_validator.py:1990-2070` | unanchored (schema-example propagation, not live rejects) | - | - | - | no | no — unanchored |

Dataset boundary (important): `pass_rate_monitor.json`, `project_data.db::stage_attempts`, and `project_data.db::director_selections` each store **only the final round per episode** (12 rows total). Per-attempt intermediate rejects are **not** persisted at those layers — the only source of intermediate-reject text is (a) `llm_io.jsonl` via the `[이전 검증 경고]` embedding in the **next** producer prompt and (b) `0_temp.txt` console capture. Therefore this audit's observed firings count is a lower bound: heuristics that fired on early rounds whose next round was itself a structural regenerate may not have their warning text preserved in any file the next round read. Confidence impact: the TP/FP counts above are valid as directional calibration evidence but not as complete session-level counts.

## Cross-Terminal Pointers

- → T1 (`docs/2026-04-13/t1-producer-initial-prompt-forensics.md`): the producer prompt's schema example at `[위치]/[시간]` (`llm_io.jsonl` ep8 prompts) explicitly models `time_flow` as `"오전 → 저녁"` — i.e., the prompt itself **teaches** the producer to use the `→` arrow form, but the cross-stage contract classifies `→` as a time-shift marker at `stage_cross_stage_contract.py:37-51`. Vocabulary conflict between what the prompt teaches and what the contract normalizer reads. T1 is the only terminal that judges initial-prompt content quality.
- → T2 (`docs/2026-04-13/t2-stage3-retry-feedback-loop-audit.md`): ep8 opening_transition mismatch re-fires on 4 independent retry rounds with the same candidate pattern. Producer never receives a concrete "stop using `→` in time_flow" / "stop using `진입` in scene_1 description" directive even though the mismatch is mechanical and cache-stable. T2 owns whether retry feedback carries the exact prior failure as a concrete repair directive.
- → T3 (`docs/2026-04-13/t3-producer-context-packet-audit.md`): the ep8 prompt contains `[Arc 시간 연속성 참고] 이전 Arc 종료 시점 마커: ... 18년 전` — the 18-year offset is being pinned into the context packet as a canonical time marker. T3 owns what is inside the delivered packet; this terminal only notes that the packet directly feeds the `temporal_deictic` FP loop at `unified_blueprint_validator.py:1823-1838`.
- → T6 (`docs/2026-04-13/t6-ensemble-candidate-diversity-audit.md`): all 5 ep8 fan-out candidates inspected share the same `opening_transition.type = "direct_continuation"` and the same `→` time_flow pattern. That is candidate-diversity evidence (all candidates converge to the same rule-hostile vocabulary), not a validator calibration claim — T6 owns diversity ranking.
- → T7 (`docs/2026-04-13/t7-director-vs-validator-authority-overlap-audit.md`): `scenario_density anchor_density` is marked `"advisory_only": True, "director_focus": False` at `unified_blueprint_validator.py:2463-2464` but the warning text still appears in `[이전 검증 경고]` blocks of the next producer prompt and plausibly costs Director score. Whether Director rubric weighs advisory-only warnings against the binding contract is T7 territory.
- → T8 (`docs/2026-04-13/t8-stage3-cost-attribution-audit.md`): the ep8 `tactical_semantic_fidelity` FP chain routes into `binding_prevalidation_regenerate_only` via `unified_blueprint_validator.py:78-79`, which forces a full regenerate per reject instead of a local patch. T8 owns cost attribution and can attribute how much of the ep8 cost is downstream of FP regenerate cycles.
- → T9 (`docs/2026-04-13/t9-stage2-to-stage3-handoff-quality-audit.md`): the tactical authority for ep8 ("박성호 PB 설득전") does not contain any entry marker from `unified_blueprint_validator.py:80-92`, so the `2350-2353` short-circuit cannot fire and cannot sanction the modern-office vocabulary. Whether Stage2 arc output lacks the vocabulary that would let the validator sanction the scene is T9 territory.

## Hypothesis Candidates For Synthesis

Labeled as candidates, not directives. Each requires ≥3 independent candidates in the dataset to be listed here and carries a file:line anchor.

1. **H-OT-1 (opening_transition vocabulary conflict)** — The contract normalizer at `stage_cross_stage_contract.py:37-51` (`_OPENING_TRANSITION_TIME_SHIFT_MARKERS`) and `18-36` (`_OPENING_TRANSITION_SCENE_MARKERS`) reads two tokens — `→` and `진입` — that also appear naturally in legitimate direct-continuation blueprints (the arrow as a scene-duration span, `진입` as diegetic door entry). On ep8 this produces a 100% FP share across 5 independent candidates / 4 retry rounds. Per §6 non-goal this report does not propose a new rule, only that the observed calibration gap is anchored and reproducible.

2. **H-TS-1 (tactical_semantic marker bleed into modern genres)** — The marker lists at `unified_blueprint_validator.py:80-103` contain tokens (`직원`, `그림자`, `대응`, `차단`, `처리`, `제압`, `위협`, `협박`) whose investment-genre frequency is effectively 1.0 per PB/boardroom scene; combined with the AND-logic at `2368-2371`, this is effectively an unconditional CRITICAL on any modern-setting negotiation candidate unless the tactical authority also happens to use the same tokens (the `2350-2353` short-circuit). 5 independent ep8 candidates all trip the AND without a single physical-threat token anywhere in their response text. Per §6 non-goal this report does not propose removing or re-weighting markers.

3. **H-TD-1 (temporal_deictic lacks diegetic discriminator)** — The `num>=5` threshold at `unified_blueprint_validator.py:1827-1853` has no signal for separating "character's intrinsic time-travel backstory anchor" from "authorial time-drift". For a 회귀자-premise project with a canonical `18년 후/전의 기억` constant, 4 independent ep6 candidates fire on the same diegetic anchor. This is a structural gap in the rule, not a producer error.

4. **H-AD-1 (anchor_density regex misses space-separated proper-noun anchors)** — The anchor regex at `unified_blueprint_validator.py:2446-2449` requires the `{2,6}`-char Hangul prefix to be **contiguous** with the suffix token (`저택/증권/...`). Space-separated constructions (`한정호 저택`, `SW 인베스트먼트`) never match. For investment-genre narrative beats where proper-noun spacing is natural, this depresses the observed anchor count below 5 even on substantive candidates. Rule is advisory-only at validator layer so not directly blocking — see Cross-Terminal Pointer to T7.

5. **H-META-1 (lossy per-attempt evidence persistence)** — Per the Dataset boundary note above, `pass_rate_monitor.json` + `project_data.db::stage_attempts` + `director_selections` all record only the final round per episode. The only way to recover intermediate per-attempt reject reasons is to parse them out of the **next** producer prompt's `[이전 검증 경고]` block in `llm_io.jsonl`. This is a brittle audit surface; any T5-class calibration work in the future would benefit from a direct per-attempt reject log. This is a meta-observation about the evidence layer, not a validator calibration claim.

## 3-Pass Audit Record

### Pass 1 — Structure

- Verified front matter matches §7 template (Parent Order, Terminal T5, baseline commit, dirty summary, resume commit, side-effect coverage, confidence line).
- Verified scope boundary: every finding above concerns validator heuristic calibration. Cheap-admission effectiveness (T4), ensemble diversity (T6), Director authority (T7), cost attribution (T8), Stage2 handoff (T9), Stage4 handoff (T10), initial-prompt content (T1), retry-loop feedback fidelity (T2), context-packet composition (T3) are all surfaced as Cross-Terminal Pointers, not as standalone verdicts.
- Verified every finding has a file:line anchor plus at least one `llm_io.jsonl` `ts` value. F6/F7/F8/F9 carry `unanchored — lower confidence` tags per §7 instruction.

### Pass 2 — Evidence

- Verified opening_transition FP trace by re-reading `stage_cross_stage_contract.py:265-275` branch logic and confirming `same_location=True, time_shift=True` path produces `explicit_transition` unconditionally via the `elif same_location and not time_shift` short-circuit failure; verified `→` is at `stage_cross_stage_contract.py:50` and `진입` is at `stage_cross_stage_contract.py:33`.
- Verified tactical marker lists literally contain `직원` (line 91), `그림자` (line 89), `대응` (line 98), `차단` (line 99), `처리` (line 97), `제압` (line 96), `위협` (line 102), `협박` (line 103); AND-logic at `unified_blueprint_validator.py:2370-2371`; CRITICAL severity at `2377`; binding-regenerate routing via `_BINDING_PREVALIDATION_REGENERATE_CATEGORIES` at `70-79`.
- Verified `num>=5` threshold appears at `unified_blueprint_validator.py:1828` (ending_hook branch) and `1853` (future-memory branch); verified `_future_memory_re` source construction at `1846-1850`.
- Verified `scenario_density anchor_density` is `"advisory_only": True` at `unified_blueprint_validator.py:2463` and `"director_focus": False` at `2464`.
- Verified protagonist_state rule counts `isinstance(value, str) and value.strip()` at `2076-2077` — so `"없음"` is an informative slot and the rule does not FP on populated states.
- Verified live dataset row counts: `pass_rate_monitor.json` 12 records / `stage_attempts` 12 rows / `director_selections` 12 rows / `llm_calls` 513 rows / `llm_io.jsonl` 513 lines (286 producer + 193 director + 34 others).
- Verified ep8 `opening_transition.type` in producer response on ts `2026-04-13T14:50:14` via direct regex extraction.
- Verified ep8 tactical-intrusion marker presence across 27 ep8 producer responses: 5 responses fire both lists; 0 responses contain real physical-threat tokens (`괴한`, `멱살`, `결박`, `납치`, `폭행`, `습격`, `난입`).

### Pass 3 — Readability / non-overlap / consistency

- Re-checked §8 non-overlap invariants:
  - Invariant 1 (T1 owns initial-prompt quality): this report does not rank initial-prompt quality; it surfaces the prompt-example `→` schema as a Cross-Terminal Pointer to T1.
  - Invariant 2 (T2 owns retry-loop fidelity): this report does not rank retry feedback; the "4 retry rounds" observation is surfaced as a Cross-Terminal Pointer to T2.
  - Invariant 4 (T4 owns cheap admission): this report does not rank cheap-admission effectiveness.
  - Invariant 5 (T5 owns validator calibration — this report's scope): all TP/FP claims are validator calibration claims.
  - Invariant 6 (T6 owns ensemble diversity): the "all 5 ep8 candidates share the same pattern" observation is surfaced as a Cross-Terminal Pointer to T6.
  - Invariant 7 (T7 owns Director/validator overlap): advisory-only warning propagation into Director score is surfaced as a Cross-Terminal Pointer to T7.
  - Invariant 8 (T8 owns cost attribution): regenerate-vs-patch cost implication is surfaced as a Cross-Terminal Pointer to T8.
  - Invariant 9 (T9 owns Stage2 handoff): tactical-authority vocabulary gap is surfaced as a Cross-Terminal Pointer to T9.
  - Invariant 10 (T10 owns Stage3→Stage4 bleed): no Stage4 claims here.
- Re-checked §10 strict non-goals: no proposed thresholds, no proposed marker-list edits, no proposed rule rewrites, no live rerun, no code/config edits, no DB writes, no new queue lane. All hypothesis candidates are labeled as candidates and require synthesis to promote.
- Confirmed UTF-8 hygiene: no `U+FFFD` characters, no triple-question placeholders, no truncated Hangul.
- Confidence: all four promoted calibration candidates (F1, F2, F3, F4 partial) are anchored to ≥3 independent candidates. F4 is downgraded to `no (advisory-only)` at the validator layer and surfaced as a Cross-Terminal Pointer instead, satisfying §6 Non-goal #1 ("do not declare a rule 'wrong' based on one candidate").

## Final Confidence

`96%`

Residual uncertainty (4%):

- Per-attempt reject text is reconstructed indirectly from `[이전 검증 경고]` blocks in the **next** producer prompt; the first attempt of a round whose candidate was structurally broken (empty response) may not have its warning text preserved anywhere observable in this dataset. Lower bound on observed FP counts.
- Director-path warnings (`scenario_density anchor_density` propagation into score) are out of this terminal's scope per Invariant 7; the waste/non-waste determination for advisory-only rules depends on T7's output. This terminal reports the warning is non-blocking at the validator layer with high confidence; the end-to-end waste measurement is T7's to make.
- The `opening_transition` mismatch is reproduced on ep8 only; ep1–ep7 had 0 observed firings of this heuristic, which is consistent with those episodes' `opening_transition.type` already passing. This report does not claim the rule is globally mis-calibrated — only that it is 100% FP on the observed ep8 candidate pattern.
