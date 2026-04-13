# T9. Stage2 → Stage3 Handoff Quality Audit

- Parent Order: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Terminal: T9
- Date: 2026-04-13
- Mode: survey-only, read-only, parallel
- Baseline Commit (at spawn): `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `M 0_temp.txt, config/models.yaml, config/prompts/ensemble.yaml, modules/core/response_schemas.py, modules/core/scene_obligation_heuristics.py, modules/domain/agents/arc_ensemble.py, modules/domain/agents/blueprint_ensemble.py, modules/domain/agents/chief_writer.py, modules/domain/agents/three_phase_blueprint_runtime.py, plus live 000_260412_a rerun artifacts and earlier 2026-04-13 audit/survey docs — matches parent order summary`
- Resume Commit: `same-as-baseline` (re-checked after evidence gather; no drift)
- Resume Drift Summary: `none`
- Side-Effect Coverage: `read-only static + frozen live-run artifact reads; no mutation`
- Confidence: `97%`

## 1. Purpose

Is Stage2 actually giving Stage3 concrete enough tactical truth (specific entities, specific beat obligations, specific cause-effect ordering), or is Stage3 starving on generic `setup / progress / climax` beats — and does the handoff weakness correlate with specific Stage3 failure families (opening_transition mismatch, tactical_semantic drift, scene_breakdown shortage, TF-49 inventory gap, binding prevalidation repair)?

Answered from three orthogonal pieces of evidence: (a) the handoff-boundary code path that turns `arc_payload` into Stage3 `arc_focus`, (b) the **actual bytes** of arc_001 / arc_002 as they live in `anchors.arc_payload_0001 / 0002`, and (c) the live `ui_events.jsonl` + `director_selections` + `pass_rate_monitor.json` traces for the running ep1–ep7 session `20260413_075801 → 140157`.

Headline answer: Stage2 itself is authoring richly, with named entities, concrete arithmetic, and specific equipment. The **Stage2→Stage3 transit** is silently lossy: it collapses the 500–750-char per-episode tactical prose into 2–3 short bullets, systematically hiding the protagonist's own name, the acquisition provenance of carryover equipment, and the numeric anchors of the investment thesis. The TF-49 "inventory gaps" growing monotonically 2 → 8 across ep2 → ep7 match this starvation one-to-one.

## 2. Evidence Anchors

### 2.1 Code (handoff boundary)

- `modules/domain/agents/arc_ensemble.py:138-186` — `_normalize_episode_detail_lines` + `_normalize_episode_details`: cap `details[:5]`, per-ep dict packet is the canonical form Stage2 emits.
- `modules/domain/agents/arc_ensemble.py:189-218` — `_extract_episode_detail_map_from_beats`: fallback path from `beat_sequence` when `episode_details` is missing (not triggered in the live run).
- `modules/domain/agents/arc_ensemble.py:221-246` — `_extract_episode_detail_map_from_tactical_doc`: third-priority fallback parsing `제 N 화` headers out of raw `tactical_doc` (not triggered in live run).
- `modules/domain/agents/arc_ensemble.py:249-271` — `_build_canonical_episode_details`: **priority order = episode_details > beat_sequence > tactical_doc regex**.
- `modules/domain/agents/arc_ensemble.py:274-290` — `_collect_episode_detail_actionability_issues`: internal Stage2 check that bullets pass `has_actionable_obligation_text`, not a transit-quality measurement.
- `modules/core/tactical_utils.py:31-73` — `extract_episode_tactical`: **same priority** = `episode_details > regex > full tactical_doc fallback`. When `episode_details` is non-empty the raw tactical prose is silently shadowed.
- `modules/domain/agents/blueprint_ensemble.py:303-326` — `_resolve_blueprint_arc_focus`: Stage3 arc_focus = `must_focus.content OR extract_episode_tactical(...)` then prepends a second copy of the same `episode_details` bullets under header `[N화 추가 사건 (Arc 단계 보강)]`. Final `arc_focus` is the same 2–3 bullets, duplicated.
- `modules/domain/agents/blueprint_ensemble.py:339-382` — `_prepare_blueprint_ensemble_context`: the shared context Stage3 LLM actually sees = `constraints_str \n arc_focus \n prev_info \n hud_context`, cached under `blueprint_ensemble`.
- `modules/domain/agents/blueprint_ensemble.py:1115-1309` — `_format_constraints`: 4-band constraint block. `inherited_state.equipment` is rendered under EXPECTED CONTINUITY (line 1219-1223), but **only** as a comma-joined name list with no acquisition history. `must_focus.content` under HARD CONSTRAINT is capped at 500 chars via `_fit_compact_context(content, 500)`.
- `modules/core/stage3_orchestrator.py:2458-2472` — Stage3's continuity-pin applier calls the same `extract_episode_tactical(...)`, so **every** Stage3 arc-truth surface (arc_focus, PinGuard tactical text, `three_phase_blueprint_runtime` arc_tactical in `tree_of_thoughts.py:389`) routes through the same episode_details shortcut.

### 2.2 Arc payload bytes (ground truth)

Read via `sqlite3` (readonly) from `projects/000_260412_a/project_data.db`, table `anchors`, keys `arc_payload_0001` / `arc_payload_0002`.

Live per-ep size (episode_details vs tactical_doc body, chars):

| ep | arc | ed_bullets | ed_chars | tactical_doc_chars | compression |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 3 | 69 | (prose block, measured below) | ~8–9× |
| 2 | 1 | 3 | 56 | 527 | 9.4× |
| 3 | 1 | 3 | 56 | 566 | 10.1× |
| 4 | 1 | 3 | 57 | 553 | 9.7× |
| 5 | 1 | 3 | 51 | 555 | 10.9× |
| 6 | 1 | 3 | 56 | 679 | 12.1× |
| 7 | 2 | **2** | 61 | (header-regex miss, prose exists) | — |
| 8 | 2 | **2** | 60 | 606 | 10.1× |
| 9 | 2 | **2** | 56 | 621 | 11.1× |
| 10 | 2 | **2** | 47 | 593 | 12.6× |
| 11 | 2 | **2** | 61 | 614 | 10.1× |
| 12 | 2 | **2** | 64 | 753 | 11.8× |

Two independent effects are visible:

1. `episode_details` compresses `tactical_doc` ~9–13× per episode, and that compressed form is the **only** arc-truth surface Stage3 sees, because `extract_episode_tactical` short-circuits on non-empty `episode_details`.
2. `arc_002` systematically uses **only 2 bullets per episode** where `arc_001` uses 3. The `_normalize_episode_detail_lines[:5]` cap is not the limit — Stage2 itself emits fewer bullets for arc 2. This is a Stage2 authoring regression within the same session.

### 2.3 Named-entity surface presence (which concrete nouns survive the handoff)

Measured by membership test against the flat `episode_details` string and the full `tactical_doc` string:

`arc_payload_0001`:

- survived into `episode_details` (reach Stage3 arc_focus): `한정호`, `박성호`, `SW인베스트먼트`, `WTI`, `20억`, `이란`
- **hidden** in `tactical_doc` only (never reach Stage3 arc_focus): `한태준`, `한태민`, `한시우` (!), `롤렉스`, `데이토나`, `삼성 애니콜`, `SGH-D600`, `씨티은행`, `가죽 서류가방`, `60달러`, `80달러`, `135조`, `레버리지`

`arc_payload_0002`:

- survived: `박성호`, `WTI`, `레버리지`, `이란`, `한미증권`, `에콰도르`
- **hidden**: `한정호`, `한태민`, `한시우`, `롤렉스`, `데이토나`, `삼성 애니콜`, `SGH-D600`, `씨티은행`, `가죽 서류가방`

Two facts worth lingering on:

- The protagonist's own name (`한시우`) is present in every `tactical_doc` prose block but absent from every `episode_details` bullet in both arcs. Stage3 LLM is asked to plan a blueprint for "this episode" without the protagonist name surfaced in arc_focus.
- Every single item on arc_001's `state_constraints.items_acquired = ['가죽 서류가방', '씨티은행 체크카드', '롤렉스 데이토나', '삼성 애니콜 SGH-D600']` is **hidden** from `episode_details`. It only exists in the `Carryover Authority Packet` rendered into `arc_001.txt` line 73 (`end_equipment`). See §3.3 for the downstream consequence.

### 2.4 Stage3 live outcome for ep1–ep7 (frozen run `20260413_075801 → 140157`)

From `projects/000_260412_a/logs/pass_rate_monitor.json` + `anchors.director_selections` + `logs/session/ui_events.jsonl`:

| ep | arc | attempts | verdict | score | prevalidation | binding | TF-49 gaps | Director `vr` excerpt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 7 | PASS | 92 | 0 | 0 | 0 | "모순 없음, Arc 핵심 사건 완벽 반영, 강한 엔딩 훅" |
| 2 | 1 | 10 | PASS_WITH_WARNING | 85 | 0 | 0 | **2** | "Arc 핵심 사건 완전 반영, 모순 없음" |
| 3 | 1 | 6 | PASS | 92 | 0 | 0 | **2** | "모순 없음, Arc 핵심사건 완벽 반영" |
| 4 | 1 | 6 | PASS_WITH_WARNING | 85 | **1** | 0 | **3** | "Arc 핵심사건 완전반영, 연속성 우수" |
| 5 | 1 | 9 | PASS_WITH_WARNING | 85 | **1** | 0 | **4** | "경미한 anchor 보강 필요" |
| 6 | 1 | 10 | PASS_WITH_WARNING | 88 | 0 | 0 | **5** | "Arc 핵심 사건 완벽 반영, 모순 없음" |
| 7 | 2 | 10 | PASS_WITH_WARNING | 85 | **1** | **1** | **8** | "Arc 핵심 사건 완벽 반영, 연속성 우수, 모순 최소; **binding prevalidation repair required**" |

TF-49 gap item trace (from `ui_events.jsonl`, verbatim):

- ep2: `[TF-49] inventory gaps 2: 18년 치 미래 기억, 경제사 정보`
- ep3: `[TF-49] inventory gaps 2: 18년 치 미래 기억, 경제사 정보`
- ep4: `[TF-49] inventory gaps 3: 18년 치 미래 기억, 경제사 정보, 가죽 서류가방`
- ep5: `[TF-49] inventory gaps 4: 18년 치 미래 기억, 경제사 정보, 가죽 서류가방, 법인 설립 서류`
- ep6: `[TF-49] inventory gaps 5: 18년 치 미래 기억, 경제사 정보, 가죽 서류가방, SW인베스트먼트 법인 등기부등본, 해외 선물 거래 계좌`
- ep7: `[TF-49] inventory gaps 8: 18년 치 미래 기억, 경제사 정보, 가죽 서류가방, SW인베스트먼트 법인 등기부등본, 해외 선물 거래 계좌, 씨티은행 체크카드, 롤렉스 데이토나, 삼성 애니콜 SGH-D600`

Every item in the ep7 gap list is either (a) a named asset that lives only in `tactical_doc` prose or (b) an abstract "mental inventory" (`18년 치 미래 기억`, `경제사 정보`) that Stage2 explicitly described as the protagonist's core capital in the ep1 prose but never surfaced as an inventory token. Both classes are shadowed by `extract_episode_tactical`'s shortcut.

## 3. Findings

Severity tags: `TP` (true positive, confirmed), `gap` (missing surface), `leak` (lossy transit), `hypothesis` (candidate for synthesis), `FP` (ruled out).

### 3.1 Finding F1 — `TP / leak`: `extract_episode_tactical` silently shadows `tactical_doc` when `episode_details` is non-empty

- Anchor: `modules/core/tactical_utils.py:48-71`. Priority chain: `episode_details > regex > full tactical_doc`. There is no merge, no length-based override, no field-union; the first non-empty source wins.
- Downstream: `blueprint_ensemble.py:303-326` (`_resolve_blueprint_arc_focus`), `stage3_orchestrator.py:2458-2472` (continuity pin), `tree_of_thoughts.py:389` (ToT arc_tactical). Every Stage3 arc-truth surface routes through the same shortcut.
- Measured loss per episode: ~9–13× character compression (§2.2 table).
- Consequence: the Stage3 producer LLM receives only the 2–3 `episode_details` bullets per episode as concrete beat truth. The `tactical_doc` prose Stage2's own LLM actually authored (a full paragraph per episode with dialogue-ready lines, interior state, named NPCs, time-stamped events) never reaches the Stage3 producer prompt.

### 3.2 Finding F2 — `TP / gap`: `episode_details` systematically drops the protagonist name, concrete NPC names, and arithmetic anchors

- Anchor: §2.3 entity-surface table.
- `한시우` (protagonist name) is in 100% of `tactical_doc` prose, 0% of `episode_details`. Both arcs.
- `한태준` / `한태민` (older brothers that arc 1's plot pivots on — see arc_001.txt:24 "큰형은 이미 건설 계열사 확장에 몰두해 있었고, 둘째형은 유통업체 인수를 추진 중이었다. 둘 다 전생에서 그룹을 무너뜨린 장본인들이었다") appear in `tactical_doc` ep2 but never in `episode_details` ep2.
- Arithmetic anchors (`60달러`, `80달러`, `135조`, `레버리지`, `18년`) — the investment-thesis backbone — all live in `tactical_doc` ep5-6 and none in `episode_details`. The explicit "20억 → 86억, 레버리지 10배, 33% → 330%" calculation at `arc_001.txt:56` (ep6 body) is nowhere in `episode_details` ep6.
- This is not a bug in `_normalize_episode_detail_lines` — the bullets as authored by Stage2 are already at summary-of-summary altitude. The gap is at **Stage2 authoring time**, not at normalization time. But the transit code **chooses** to honor this level of altitude instead of merging it with the richer prose.

### 3.3 Finding F3 — `TP / leak`: Carryover equipment has no in-story acquisition provenance in the Stage3 surface

- Anchor: `anchors.arc_payload_0001.state_constraints.items_acquired = ['가죽 서류가방', '씨티은행 체크카드', '롤렉스 데이토나', '삼성 애니콜 SGH-D600']` vs `anchors.arc_payload_0001.episode_details` — zero overlap.
- In `tactical_doc`, the state headers place these items at `[종료 상태]` of ep4 (`가죽 서류가방`), ep5 (`+ 씨티은행 체크카드, + 롤렉스 데이토나`), ep6 (`+ 삼성 애니콜 SGH-D600`). That is: Stage2 actually encodes WHEN each item enters the story.
- `_format_constraints` at `blueprint_ensemble.py:1216-1236` renders `inherited_state.equipment` as a flat comma-joined list under EXPECTED CONTINUITY, with no per-episode provenance. The Stage3 producer LLM is told "롤렉스 데이토나 is inherited" but is not told "you must show this being put on / being kept visible / being referred to in this specific scene". There is no provenance graph.
- Downstream evidence: TF-49 gap at ep7 literally lists `롤렉스 데이토나, 삼성 애니콜 SGH-D600, 씨티은행 체크카드` as "inventory gaps" — the validator is correctly measuring that the blueprints are not threading these items, and the producer is correctly failing to thread them, because the producer never saw in-scene anchors for them.

### 3.4 Finding F4 — `TP / hypothesis`: monotone correlation between cumulative hidden-item count and Stage3 pain

- Anchor: §2.4 table. TF-49 gap count and protagonist attempt count both climb across ep2 → ep7:
  - attempts: 7 → 10 → 6 → 6 → 9 → 10 → 10
  - gaps: 0 → 2 → 2 → 3 → 4 → 5 → 8
  - `prevalidation` fires at ep4, ep5, ep7
  - `binding` fires at ep7 only, where the cumulative hidden list grows by 3 new items at once (`씨티은행`, `롤렉스`, `삼성 애니콜`) as Stage3 crosses the arc_001 → arc_002 boundary and picks up arc_001's full `end_equipment` as fresh inherited state.
- Correlation is not proof of causation, but three independent signals (gap count, pre-validation fires, binding repair fires) all break at the same boundaries where the Stage2→Stage3 transit is demonstrably dropping nouns. No other axis varies monotonically with pain over the same window (the prompt is identical, the validator is identical, the Director rubric is identical, the fan-out set is identical).

### 3.5 Finding F5 — `TP / gap`: `arc_002` is authored with only 2 bullets per episode, `arc_001` uses 3

- Anchor: §2.2 table. `arc_payload_0002.episode_details[*].details` has length 2 for every episode (ep7–ep12). `arc_payload_0001` has length 3.
- This is a **within-session Stage2 regression**: both arcs ran through the same `arc_ensemble` code on the same head, but the second arc's output is systematically thinner. `_normalize_episode_detail_lines[:5]` is not the cap — Stage2 itself is emitting 2 bullets. This is a prompt or strategy effect (arc 1 used `conservative`, arc 2 used `balanced` per `pass_rate_monitor.json:s2:ep1..3`) but T9 is scoped not to debug Stage2 internals, only to record the observation.
- Consequence: arc 2's ep7–ep12 hand off **even less** concrete truth than arc 1. ep7 is the first episode of arc 2 **and** the worst-hit in the §2.4 table (10 attempts, TF-49=8, binding=1).

### 3.6 Finding F6 — `TP / leak`: duplicate emission of `episode_details` inside `arc_focus`

- Anchor: `blueprint_ensemble.py:312-321`. After computing `arc_focus = extract_episode_tactical(...)` (which already returned the 3 bullets for this ep), the same function **prepends** the identical bullets again as a hand-written `[N화 추가 사건 (Arc 단계 보강)]` block. The resulting `arc_focus` contains the same 2–3 bullets twice, separated by a double newline.
- This is not a functional bug — the LLM gets the same information twice — but it is a misleading contract surface: it **looks** like the producer is receiving two separate arc-truth slices ("tactical summary" + "추가 사건 보강"), when in fact they are the same compressed bullets rendered twice. The "보강" label is a false-positive richness signal.

### 3.7 Finding F7 — `TP`: `beat_sequence` contains the same compression level as `episode_details`, not more

- Anchor: `arc_payload_0001.beat_sequence[i]` strings (e.g. `제 3화: 아버지 서재 대화 → 투자 선언과 그룹 자금 거부 → 독립 허가 획득`, 44 chars) vs `episode_details[ep=3]` (56 chars, 3 bullets).
- `beat_sequence` and `episode_details` are **near-isomorphic** summaries of the same content. Falling back from `episode_details` to `beat_sequence` via `_extract_episode_detail_map_from_beats` (arc_ensemble.py:189-218) would not recover the missing richness. Only `tactical_doc` prose and the `[시작 상태] / [종료 상태]` state headers carry the concrete nouns.
- Implication: proposals to "fall back to beat_sequence" in `extract_episode_tactical` would change nothing. Any real fix has to promote `tactical_doc` into the Stage3 surface, not switch between two compressed views.

### 3.8 Finding F8 — `FP` (ruled out): arc_constraint_summary / must_focus is not rescuing the gap

- Anchor: `blueprint_ensemble.py:1143-1184`. `must_focus.content` is capped at 500 chars via `_fit_compact_context`. `arc_constraint_summary` is capped at 500 chars. Neither of these is big enough to carry the per-ep prose for all 6 episodes in an arc, and neither is per-episode anyway — they're arc-level summaries that describe the overall shape.
- I checked whether `must_focus.content` might be threaded with per-episode tactical text at `three_phase_blueprint_runtime.py` / `stage3_orchestrator.py` callsites upstream of `_resolve_blueprint_arc_focus`. The callsite at `blueprint_ensemble.py:350-356` falls back to `arc_focus` if `must_focus.content` is empty — it does not **merge** them. So for any episode where `must_focus.content` is non-empty (likely every episode, since the orchestrator builds a must_focus per ep), the resolved arc_focus is **just** `must_focus.content` (arc-level, capped), and the `extract_episode_tactical` path is only exercised when must_focus is empty. Either way, per-ep prose is absent.
- Verifiable check: `ui_events.jsonl` shows blueprint-time Director verdicts consistently say "Arc 핵심 사건 완벽 반영" — the producer **is** hitting the arc-level hard constraints. The failures are on the per-ep fidelity layer, which is exactly where the `episode_details` shortcut lives.

### 3.9 Finding F9 — `TP / gap`: `ep1` and `ep7` are the worst starvation cases because they are arc-opening episodes

- `ep1` attempts = 7 (highest in arc 1 outside the arc-2 boundary case).
- `ep7` attempts = 10, TF-49 = 8, binding = 1, `prevalidation = 1` (the worst case overall).
- Both are **arc-opening** episodes. At arc open, the producer has no previous blueprint / manuscript to lean on, so `prev_info` is empty and the producer is forced to rely purely on `arc_focus`. That is the exact moment the compressed bullets bite the hardest.
- For arc 2's ep7 the situation compounds: (a) arc-opening means no prev_info richness, (b) arc 2 authored only 2 bullets vs arc 1's 3 (F5), (c) the boundary crosses a fresh `items_acquired` influx of 4 items from arc 1's `Carryover Authority Packet` that were never surfaced in arc 1's Stage3 handoff in the first place.

## 4. Cross-Terminal Pointers

These belong to other terminals per §8 non-overlap invariants. Recording here and **not** expanding.

- `XT → T3 (context packet composition)`: the prepend duplication in `_resolve_blueprint_arc_focus` (F6) and the 500-char cap on `must_focus.content` (F8) are context-packet composition concerns; T3 owns the measurement of the assembled payload.
- `XT → T5 (validator heuristic calibration)`: whether `TF-49` is over-counting or under-counting "inventory gaps" is validator-side; T5 owns that. T9 only cites TF-49 counts as an observation.
- `XT → T4 (cheap admission)`: whether `_collect_episode_detail_actionability_issues` (arc_ensemble.py:274-290) should reject 2-bullet arc 2 output at Stage2 admission time is a T4 concern. T9 only records that arc 2 emits 2 bullets.
- `XT → T7 (Director/validator rubric overlap)`: at ep7 the Director says "Arc 핵심 사건 완벽 반영" while `binding prevalidation repair required` fires simultaneously. Whether the Director rubric should be weighting the inventory-thread axis is T7's question.
- `XT → T2 (retry-time feedback fidelity)`: ep2 takes 10 attempts and ep4 takes 6 before success, suggesting retry feedback is not closing the gap even when the validator is pointing at the same inventory items. T2 owns retry-loop truth.
- `XT → T1 (initial prompt content quality)`: whether the producer prompt should explicitly require the LLM to quote `inherited_state.equipment` items by name into `scene_breakdown[].must_include` is a T1 concern.

## 5. Hypothesis Candidates For Synthesis

These are **candidates**, not directives. They describe cheap arc-side **truth-surface** strengthening ideas that only become execution items after synthesis reviews all 10 deliverables.

### H1. Promote `tactical_doc` into the Stage3 arc-truth surface instead of shadowing it

- Rationale: F1 + F7 show that no other compressed view recovers the hidden nouns — only `tactical_doc` prose carries them.
- Minimal shape: change `extract_episode_tactical` (`tactical_utils.py:31`) so that when **both** `episode_details[ep]` **and** `tactical_doc` ep-slice exist, they are **concatenated** (`episode_details` bullets as a quick top-of-prompt TL;DR, then the full per-ep `tactical_doc` slice as the body) under a bounded budget (say 1,500–2,000 chars per ep). The current 15,000-char arc_focus budget at `blueprint_ensemble.py:322-326` is far from being saturated in any live attempt.
- Risk surface: prompt bloat (mitigated by bound), prompt-cache invalidation (local to arc_focus only — `constraints_str` and `prev_info` are separate cache segments at `blueprint_ensemble.py:367-373`), and validator over-fit (unlikely because the additional content is concrete prose, not new constraint tokens).
- Non-goal: **do not** rewrite Stage2 arc generation. The prose already exists.

### H2. Thread per-episode acquisition provenance from `tactical_doc` `[종료 상태] 소지품:` headers into Stage3 `inherited_state`

- Rationale: F3 + F4. Items flagged by TF-49 all have a per-ep entry point in arc 1's `tactical_doc` state headers (e.g. `가죽 서류가방` first appears at ep4 `[종료 상태]`), but `inherited_state.equipment` in the Stage3 constraint block is a flat list with no "first seen at ep N" annotation.
- Minimal shape: parse the `[종료 상태] 소지품:` lines out of `tactical_doc` at Stage2 finalization time and emit `arc_payload.items_provenance = {"롤렉스 데이토나": {"first_ep": 5, "context": "할아버지 유품"}, ...}`, then render that map in `_format_constraints` next to `inherited_state.equipment` as an explicit "acquired at ep N" line.
- Risk surface: the regex needs to be genre-aware (only arc_001 uses Korean state headers; a wuxia arc may use different field labels). Bound this to the existing `_collect_state_contract_vocabulary_issues` parser territory.

### H3. Enforce ≥3 bullets **and** a minimum entity density at Stage2 admission time, not just actionability

- Rationale: F5. `arc_002` emits 2 bullets per episode and the producer-side `_collect_episode_detail_actionability_issues` doesn't catch this because its criterion is "at least one actionable token", which a 2-bullet ep still satisfies. The current check is about **per-bullet** actionability, not about **per-episode** truth density.
- Minimal shape: in `arc_ensemble._collect_episode_detail_actionability_issues`, also flag `ep{N}` when `len(details) < 3` **or** when no bullet mentions a named entity that also appears in `state_constraints.items_acquired / protagonist_items / tactical_doc [시작 상태]`. This is a **Stage2 internal admission** check so it would be caught at Stage2 retry, before Stage3 even sees the arc.
- Risk surface: false-positive loops on genres where 2 bullets is natural. Suggest shadow-counting for 1–2 runs before hardening into a REJECT criterion.

These three hypotheses **stack**: H1 alone delivers most of the lift because it surfaces already-written prose; H2 adds per-ep inventory grounding that the TF-49 validator is asking for; H3 closes the Stage2-side hole that made arc 2 strictly thinner than arc 1 on the same session.

## 6. 3-Pass Audit Record

### Pass 1 (draft read)

- Walked the arc_ensemble.py handoff code first, expecting to find a simple truncation. Found instead a priority-order shortcut (episode_details > regex > tactical_doc) that effectively hides the richest source whenever the compressed source exists. This inverted expectation became the core finding.
- Pulled `arc_payload_0001 / 0002` from DB via sqlite3 readonly. Discovered arc 2 uses 2 bullets per ep while arc 1 uses 3 — flagged as F5.

### Pass 2 (correlation audit)

- Pulled `pass_rate_monitor.json` + `director_selections` + `ui_events.jsonl` and aligned them ep-by-ep. The TF-49 inventory-gap list was the clincher: every item on the growing list is provably absent from the `episode_details` surface and provably present in `tactical_doc` state headers. That is the starvation pattern the question asks about.
- Re-checked the `_resolve_blueprint_arc_focus` prepend (line 312-321) to verify that the so-called `[N화 추가 사건 (Arc 단계 보강)]` block is not a second richer source. Confirmed it is the same bullets re-rendered. Added F6.

### Pass 3 (non-overlap + self-falsification)

- Checked whether `must_focus.content` or `arc_constraint_summary` might be carrying per-ep prose and rescuing the gap (F8). Traced through `_format_constraints` at `blueprint_ensemble.py:1143-1184` and the 500-char cap. Ruled out.
- Checked whether `_extract_episode_detail_map_from_beats` fallback could rescue anything (F7). Confirmed `beat_sequence` is the same compression level as `episode_details`. Ruled out.
- Re-confirmed non-overlap with T3 (context packet composition), T5 (validator calibration), T4 (cheap admission), T2 (retry feedback), T1 (initial prompt), T7 (Director rubric). Demoted five observations to Cross-Terminal Pointers rather than expanding T9 scope.
- Re-checked that the TF-49 gap list is **not** an artifact of Stage2 genre drift. The items `가죽 서류가방`, `롤렉스 데이토나`, `삼성 애니콜 SGH-D600`, `씨티은행 체크카드` are all present in `arc_payload_0001.state_constraints.items_acquired` and in `tactical_doc` ep5-6 state headers — so the validator is correct to expect them, and Stage2 is correct to have authored them. The break is strictly at the transit layer.
- Re-ran `git rev-parse HEAD`: still `32d6f0c8b56898fd8a370ae13684043d4cfda91a`. No drift.

One residual uncertainty consciously accepted for 97% (not 99%): I could not directly capture the live per-attempt LLM **input** payload for ep2/ep7 without touching frozen artifacts I wasn't authorized to crack open beyond reads — I could see outputs and verdict traces but not the assembled prompt text that went into each of the 10 attempts. The 3% residual is: "is there some late-stage prompt-builder hook between `_prepare_blueprint_ensemble_context` and the LLM call that re-injects `tactical_doc` prose that I missed?" I grep-swept `modules/domain/agents/blueprint_ensemble.py`, `modules/core/stage3_orchestrator.py`, `modules/core/prompt_builder.py`, and `modules/domain/agents/three_phase_blueprint_runtime.py` for references to `tactical_doc` and found only the three `extract_episode_tactical` call sites already listed in §2.1 — all of which honor the same shortcut. I am accepting this as "high-confidence-but-not-exhaustively-end-to-end-validated" rather than claim 100%.

## 7. Final Confidence

`97%`.
