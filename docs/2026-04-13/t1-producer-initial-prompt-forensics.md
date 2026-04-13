# T1. Producer Initial-Prompt Forensics

- Parent Order: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Terminal: T1
- Date: 2026-04-13
- Mode: survey-only, read-only, parallel
- Baseline Commit (at spawn): `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `M 0_temp.txt, config/models.yaml, config/prompts/ensemble.yaml, modules/core/response_schemas.py, modules/core/scene_obligation_heuristics.py, modules/domain/agents/{arc_ensemble,blueprint_ensemble,chief_writer,three_phase_blueprint_runtime}.py, projects/000_260412_a/* live artifacts, tests/test_* partial edits; ?? includes this deliverable and 7 peer 2026-04-13 docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none (no mutation performed except this deliverable write)`
- Side-Effect Coverage: `read-only static + frozen live-run artifact reads; no mutation`
- Confidence: `96%`

## 1. Purpose

Does `config/prompts/ensemble.yaml` plus the initial-call prompt assembly in `modules/domain/agents/blueprint_ensemble.py` actually **teach** the Stage3 contract (`opening_transition`, `protagonist_state`, `scene_breakdown` structure, `tactical_semantic_fidelity`, `scenario_density`) in a form the LLM can learn from, or does it only **declare** abstract field names that an LLM cannot ground without concrete examples?

Scope per §6 T1 is the **initial** producer prompt only. Retry-time feedback (T2), context packet composition (T3), cheap admission effectiveness (T4), validator calibration (T5), ensemble diversity (T6), Director/validator overlap (T7) are out of scope.

## 2. Evidence Anchors

Primary read surfaces:

- `config/prompts/ensemble.yaml` (475 lines, dirty in worktree)
  - `ENSEMBLE_ARC_PROMPT` template (Stage2 arc generator) — `config/prompts/ensemble.yaml:4-285`
  - `BLUEPRINT_GENERATION_PROMPT` template (Stage3 blueprint generator — the relevant one for T1) — `config/prompts/ensemble.yaml:287-475`
- `modules/domain/agents/blueprint_ensemble.py` (1,693 lines, dirty in worktree)
  - `BLUEPRINT_STRATEGIES` list — `blueprint_ensemble.py:47-87`
  - `AI_TELL_BLUEPRINT_GUARDRAIL` constant — `blueprint_ensemble.py:89-99`
  - `build_external_pov_policy_constraint` — `blueprint_ensemble.py:189-253`
  - `BlueprintEnsembleGenerator.generate_*` entry and context bundling — `blueprint_ensemble.py:272-750`
  - `_build_blueprint_prompt_bundle` — `blueprint_ensemble.py:751-823`
  - `_format_constraints` (4-tier authority band) — `blueprint_ensemble.py:1115-1309`
  - `_has_meaningful_protagonist_state` cheap-admission helper — `blueprint_ensemble.py:897-906`
  - `_blueprint_contract_admission_reason` — `blueprint_ensemble.py:908-915` (`missing_opening_transition` / `invalid_opening_transition` / `missing_protagonist_state` emit sites)
- `modules/core/stage_cross_stage_contract.py` (360 lines)
  - Enum constants — `stage_cross_stage_contract.py:7-17`
  - Scene transition markers — `stage_cross_stage_contract.py:18-36`
  - Time shift markers — `stage_cross_stage_contract.py:37-51`
  - Alias map `_normalize_opening_transition_type` — `stage_cross_stage_contract.py:162-177`
  - Inference rules `infer_opening_transition_contract` — `stage_cross_stage_contract.py:234-293`
- `modules/core/scene_obligation_heuristics.py`
  - `_STATE_PLACEHOLDER_TOKENS` set — `scene_obligation_heuristics.py:84-107`
  - `has_meaningful_state_value` — `scene_obligation_heuristics.py:156-176`
  - `has_actionable_obligation_text` — `scene_obligation_heuristics.py:136-153`
- `modules/core/genre_guards/work_guard.py`
  - `get_retrieval_contract_prompt("blueprint")` — `work_guard.py:632-678` (cross-checked; does NOT add any opening_transition vocabulary, only tracking_slots/scene_engines/registry)

Supporting frozen artifact anchors (consulted to reconfirm the ep8 symptom is the same family this terminal is analyzing, not a new one):

- `0_temp.txt:400-469` — latest live ep8 reject cycles (`opening_transition.type mismatch: declared 'direct_continuation' vs normalized 'explicit_transition'`)
- `projects/000_260412_a/logs/pass_rate_monitor.json` — per-attempt pass rate (ep1–ep7 closed, ep8 interrupted)

## 3. Findings

Severity tags per §7: `TP` = true positive (contract gap real), `FP` = false positive, `gap` = missing teach-surface, `leak` = contradiction between prompt and validator, `waste` = prompt text that consumes tokens without moving the contract, `hypothesis` = needs T4/T5 evidence to confirm.

### F1 — `opening_transition` is declared, not taught (gap)

File anchors: `config/prompts/ensemble.yaml:411-414`, `:457`; normalization truth at `modules/core/stage_cross_stage_contract.py:162-177` (alias map), `:205-221` (scene+time cue rules), `:267-274` (inference rules).

What the prompt says about `opening_transition`:

```
411:      "opening_transition": {{
412:          "type": "direct_continuation | explicit_transition | jump_opening",
413:          "signals": ["opening contract를 설명하는 짧은 근거"]
414:      }},
```

And the self-check checklist:

```
457:  □ opening_transition.type을 direct_continuation / explicit_transition / jump_opening 중 하나로 명시했는가?
```

That is the **entire** surface the prompt dedicates to `opening_transition`. The prompt:

1. Lists three enum values and says "pick one."
2. Says the `signals` field is "a short rationale."
3. Asks the self-check to confirm the `type` field is present.

What the normalization contract at `stage_cross_stage_contract.py:267-274` actually demands:

- `direct_continuation` is only legal when `prev_end_location == start_location` (or containment) **and** there is no time shift marker in `time_flow`.
- `explicit_transition` is the **required** value when there is a scene transition cue (`* * *`, `장면 전환`, `전환`, `컷`, `이동`, `향해`, `향하`, `옮기`, `걸음을 옮`, `발을 옮`, `나서`, `들어서`, `빠져나와`, `도착`, `진입`, `한편` — full list at `stage_cross_stage_contract.py:18-36`), or when the prev/current locations share an area but differ, or when the locations are the same but a time shift marker fires.
- `jump_opening` is the fallback when there is no prior anchor or when the locations are fully disjoint without a transition cue.
- Time shift markers (`stage_cross_stage_contract.py:37-51`): `다음 날`, `다음날`, `이튿날`, `사흘 후`, `며칠 후`, `몇 시간 후`, `한 시간 후`, `잠시 후`, `한참 후`, `이후`, `뒤`, `->`, `→` — but **suppressed** by `직후 / 곧바로 / 바로` at `stage_cross_stage_contract.py:214-221`.

Conclusion: the prompt names the three enum values but **never grounds them to the decision rule the validator actually runs**. An LLM that reads only the prompt has no way to learn "if my `start_location` equals the previous `end_location` **and** my `time_flow` does not begin with `다음 날 / 잠시 후`, then `direct_continuation`; otherwise `explicit_transition`." It must guess. The live ep8 reject chain in `0_temp.txt:400-469` (`declared 'direct_continuation' vs normalized 'explicit_transition'`) is exactly the reject the prompt cannot prevent. Tag: `gap` + `TP` (the mismatch-family reject is real and the prompt gap is the upstream cause).

### F2 — `protagonist_state` schema hint uses a value the cheap admission gate rejects (leak)

File anchors: `config/prompts/ensemble.yaml:420-424`, `:458`; cheap admission check at `modules/domain/agents/blueprint_ensemble.py:897-906`, `:917-918`; placeholder token set at `modules/core/scene_obligation_heuristics.py:84-107`.

The prompt schema hint:

```
420:      "protagonist_state": {{
421:          "mood": "감정 상태",
422:          "injuries": "부상 상태",
423:          "equipment": ["소지품"]
424:      }},
```

The cheap admission helper at `blueprint_ensemble.py:897-906`:

```
898:    def _has_meaningful_protagonist_state(protagonist_state: object) -> bool:
899:        if not isinstance(protagonist_state, dict):
900:            return False
901:
902:        for value in protagonist_state.values():
903:            if has_meaningful_state_value(value):
904:                return True
905:
906:        return False
```

`has_meaningful_state_value` at `scene_obligation_heuristics.py:156-168` tokenizes the string and rejects the value if every token is in `_STATE_PLACEHOLDER_TOKENS`. That set (at `scene_obligation_heuristics.py:84-107`) contains exactly `감정`, `상태`, `기분`, `변화`, `정상`, `보통`, `무난`, `동일`, `현재`, plus the English equivalents.

Apply to the prompt's schema hint:

- `"mood": "감정 상태"` → tokens `{감정, 상태}` → both are placeholder tokens → `has_meaningful_state_value` returns `False`.
- `"injuries": "부상 상태"` → tokens `{부상, 상태}` → `부상` survives → `True`.
- `"equipment": ["소지품"]` → tokens `{소지품}` → survives → `True`.

Because `_has_meaningful_protagonist_state` is an **any-slot** check (`for value ... if has_meaningful_state_value(value): return True` at `blueprint_ensemble.py:902-904`), a literal copy of the prompt's example slots would still narrowly pass the cheap gate (`injuries` alone saves it). But the **mood slot itself** is the only slot the prompt offers an example for that is a named content primitive, and that example is precisely the shape the producer-side gate is engineered to reject. The prompt teaches the LLM the placeholder pattern **explicitly** for the one slot where placeholder rejection is strictest.

Severity: `leak` — a concrete prompt↔validator vocabulary collision, not a gap. The LLM is being shown the forbidden shape as the canonical shape. Rewording to `"mood": "<현재 감정을 한 단어로, 예: 분노·초조·자조>"` would both teach the shape and stay out of the placeholder blacklist.

### F3 — `tactical_semantic_fidelity` is enforced by name but never taught by name (gap)

File anchors: `config/prompts/ensemble.yaml:386-387`; validator sites at `modules/domain/agents/unified_blueprint_validator.py:2324` (function entry `_collect_tactical_semantic_fidelity_issues`) per parent order §6 T5 citations; producer cheap detector `_detect_unauthorized_tactical_intrusion` at `modules/domain/agents/blueprint_ensemble.py:970` per parent order §6 T4 citation; intrusion keyword sets at `blueprint_ensemble.py:140-169`.

What the prompt says about tactical fidelity:

```
386:  6. **장면 완성도 계약**: 모든 씬은 최소 1개의 구체적 action/event가 key_events에 들어 있어야 합니다. 비어 있는 key_events, "진행/갈등/절정" 같은 껍데기 요약만 있는 scene shell은 금지입니다.
387:  7. **전술 권위 계약**: Arc tactical authority에 없는 난입/괴한/물리 충돌 이벤트를 새로 발명하지 마세요. tactical excerpt에 없는 `난입/괴한/습격/멱살/제압/협박`류 이벤트는 금지입니다.
```

That is the entire surface. What the validator and the cheap detector actually check for (per the producer intrusion marker tables at `blueprint_ensemble.py:140-169`) is a much larger keyword family: entry markers `취객 / 난입 / 들이닥 / 무단침입 / 괴한 / 습격 / 침입자 / 철문 / 그림자 / 심부름센터 / 직원` and conflict markers `멱살 / 결박 / 제압 / 처리 / 대응 / 차단 / 쫓아낸 / 도망치 / 위협 / 협박 / 박살 / 쇠파이프 / 쇠지렛대 / 군화`.

The prompt only mentions six of those tokens (`난입 / 괴한 / 습격 / 멱살 / 제압 / 협박`) and never explains the rule the validator actually runs: "if Arc `tactical_doc` does not list a physical-threat event, then `key_events` must not contain any token from these two families." The LLM is told `난입` is illegal but is not told that `취객`, `들이닥`, `쇠파이프`, `군화`, `심부름센터`, `도망치` are equally illegal. Missing-rule → producer invents a plausible-looking tactical beat that still trips the validator. Tag: `gap`.

### F4 — `scenario_density` is not named in the prompt at all (gap)

File anchors: `config/prompts/ensemble.yaml:409`, `:443`; validator site at `unified_blueprint_validator.py:2388 / :2458` per parent order §6 T5 citations; floor constant `BLUEPRINT_ENSEMBLE_MIN_INTEGRATED_SCENARIO_CHARS` imported at `blueprint_ensemble.py:26`.

What the prompt says about scenario density:

```
409:      "integrated_scenario": "전체 에피소드 시나리오 (1000자 이상, 씬별 흐름을 자연스럽게 연결)",
...
442:  1. scene_breakdown은 최소 2개, 최대 5개 씬
443:  2. integrated_scenario는 최소 1000자 이상
```

That is all. The word `scenario_density` does not appear in the prompt (`grep` confirmed on `config/prompts/ensemble.yaml`). The prompt gives a 1000-char floor and nothing about density per scene, obligation coverage, or the advisory routing that the landed tranche introduced. An LLM that hits 1000 characters with one dense scene and four empty shells passes the prompt's stated floor but fails the validator's per-scene density check. Tag: `gap`.

### F5 — `scene_breakdown` structural rules are stated as shapes but not as "why" (partial gap)

File anchors: `config/prompts/ensemble.yaml:395-408`, `:442`, `:455`; producer check `_scene_has_meaningful_payload` / `_scene_has_actionable_key_events` at `blueprint_ensemble.py:862-895`; validator sites per parent order §6 T5.

The prompt declares the schema shape at `:395-408` and the self-check at `:455`:

```
455:  □ 씬 개수가 2~5개 범위이며, 각 씬에 구체적 사건/행동이 포함되고 key_events가 비어 있지 않은가?
```

It says `key_events` must not be empty. It does not explain that `has_actionable_obligation_text` at `scene_obligation_heuristics.py:136-153` uses a `_ACTIONLESS_OBLIGATION_TOKENS` blacklist (generic labels like `진행 / 절정 / 도입 / 갈등 / 상황 / 구성 / 요약 / beat / climax / setup / progress` at `:46-82`) and will reject `["진행", "전개", "갈등 고조"]` as non-actionable even though those strings are non-empty. The prompt even shows `"진행/갈등/절정"` as a **negative** example at `:386` but frames it as `"scene shell"` language, without naming the actionable-token rule. The LLM knows those three Korean tokens are bad but will happily produce `"도입 전개"` or `"상황 정리"`, which are equally blacklisted. Tag: `gap` (lesser severity than F1–F4 because the prompt at least gestures at one example family).

### F6 — Initial prompt assembly is a direct substitution with zero dynamic contract injection (structural observation, not a defect)

File anchors: `blueprint_ensemble.py:751-823` (`_build_blueprint_prompt_bundle`).

Confirmed the initial-call assembly path: `_prompt_loader.load("ensemble", "BLUEPRINT_GENERATION_PROMPT", ...)` with variable substitutions at `blueprint_ensemble.py:783-801` and an optional full-prompt fallback at `:803-818` for the cached-context path. The template text at `config/prompts/ensemble.yaml:287-475` is the entire prompt body; nothing else injects contract vocabulary at initial-call time. Specifically:

- `strategy_directive` at `blueprint_ensemble.py:777-782` injects only `strategy["directive"]` + `AI_TELL_BLUEPRINT_GUARDRAIL` + `extra_directive` + the work-guard retrieval contract. None of those sources mention `opening_transition`, `tactical_semantic_fidelity`, `scenario_density`, or the placeholder token rules.
- `AI_TELL_BLUEPRINT_GUARDRAIL` at `blueprint_ensemble.py:89-99` only covers "do not write briefing prose / do not invent UI / do not repeat cadence" — it does not teach any contract field.
- `_format_constraints` at `blueprint_ensemble.py:1115-1309` emits a 4-tier authority band (`IMMUTABLE / HARD / CONTINUITY / ADVISORY`) but names `이전 종료 위치` under `[연속성]` without tying it to the `opening_transition.type` decision rule. The LLM sees the prev end-location but is never told "therefore set `opening_transition.type = direct_continuation` unless you also set a time shift marker."

This is T1-relevant because it confirms the prompt template is the only initial-call contract-teaching surface. Any gap in `config/prompts/ensemble.yaml:287-475` is an unmitigated gap on attempt 1. Tag: structural observation (no defect), confirms F1–F5's anchor scope.

### F7 — Vocabulary matches between prompt and contract alias map (no leak, positive finding)

File anchors: `config/prompts/ensemble.yaml:412`, `:457` vs `modules/core/stage_cross_stage_contract.py:162-177`.

The three enum strings the prompt offers (`direct_continuation / explicit_transition / jump_opening`) **do** match the canonical tokens in `_OPENING_TRANSITION_TYPES` (`stage_cross_stage_contract.py:11-17`). Aliases like `direct`, `continuation`, `scene_transition`, `cut_transition`, `transition`, `jump`, `time_jump` exist in the alias map at `:164-176` and would normalize correctly, but the prompt already shows the canonical form, so there is no vocabulary leak here — only the decision-rule gap identified in F1. Tag: not a defect.

### F8 — 3 concrete weakest-passage quotes (required by §6 T1.4)

All three are verbatim from `config/prompts/ensemble.yaml`, current head 32d6f0c8 worktree:

**W1 — `opening_transition` declaration (`config/prompts/ensemble.yaml:411-414`):**

```
      "opening_transition": {{
          "type": "direct_continuation | explicit_transition | jump_opening",
          "signals": ["opening contract를 설명하는 짧은 근거"]
      }},
```

Weakness: tells the LLM "choose one of three" without any grounding rule, any example-of-good-vs-bad, or any cross-reference to `start_location` / `time_flow` / previous `end_location`. The field the validator rejects most on is the field the prompt teaches least. This is the primary suspect for the ep8 reject family (`0_temp.txt:400-469`).

**W2 — `protagonist_state` schema hint (`config/prompts/ensemble.yaml:420-424`):**

```
      "protagonist_state": {{
          "mood": "감정 상태",
          "injuries": "부상 상태",
          "equipment": ["소지품"]
      }},
```

Weakness: the `mood` example is a literal placeholder pattern that the producer-side cheap-admission helper `has_meaningful_state_value` at `scene_obligation_heuristics.py:156-168` is engineered to reject (both `감정` and `상태` are in `_STATE_PLACEHOLDER_TOKENS` at `scene_obligation_heuristics.py:84-107`). Teaches the LLM the forbidden shape.

**W3 — `integrated_scenario` single-sentence directive (`config/prompts/ensemble.yaml:409`):**

```
      "integrated_scenario": "전체 에피소드 시나리오 (1000자 이상, 씬별 흐름을 자연스럽게 연결)",
```

Weakness: the only guidance on the highest-token-count field in the entire blueprint is "1,000+ characters" and "connect scenes naturally." No density rule, no per-scene coverage rule, no density-vs-1000-char distinction. The integrated_scenario is where `scenario_density` issues (`unified_blueprint_validator.py:2388`) actually fire, and the prompt offers exactly one floor and zero positive examples.

### F9 — Per-contract-field coverage table

For each contract field the parent order names in T1 scope, whether the prompt has (a) a positive example, (b) a negative example, (c) a "why this matters" sentence:

| Contract field | Prompt site | Positive example | Negative example | Why-this-matters | Verdict |
|---|---|---|---|---|---|
| `opening_transition.type` enum semantics | `:411-414`, `:457` | No | No | No | gap (F1) |
| `opening_transition.signals` rationale style | `:413` | No | No | No | gap (F1) |
| `protagonist_state.mood` | `:421`, `:458` | Placeholder pattern (leak) | No | No | leak (F2) |
| `protagonist_state.injuries` | `:422`, `:458` | Placeholder pattern | No | No | leak (F2, partial) |
| `protagonist_state.equipment` | `:423`, `:458` | Generic label | No | No | gap (F2) |
| `scene_breakdown` shape (2–5 scenes) | `:395-408`, `:442` | Schema shell | `:386` "진행/갈등/절정" shell | Partial | partial gap (F5) |
| `scene_breakdown.key_events` content rule | `:296`, `:386`, `:455` | No | `:386` three tokens | No | partial gap (F5) |
| `tactical_semantic_fidelity` (intrusion authority) | `:387` | No | 6 tokens (out of ~24) | Yes (one sentence) | partial gap (F3) |
| `scenario_density` | not present | No | No | No | total gap (F4) |
| `start_location` vs prev `end_location` continuity | `:460` | No | No | Yes (one line) | gap — feeds F1 |
| `time_flow` marker semantics | none | No | No | No | total gap — feeds F1 |

## 4. Cross-Terminal Pointers

One-liners — evidence observed while reading the T1 surfaces but belonging to another terminal per §8:

- **T6 (ensemble diversity)** — `BLUEPRINT_STRATEGIES` at `blueprint_ensemble.py:47-87` only defines three strategies (`action_focused / emotion_focused / dialogue_focused`), not the five the parent order mentions (`conservative / balanced / action_focused / dialogue_focused / emotion_focused`). Whether the "five" figure in the order came from Stage2 arc strategies or from a stale description, T6 must determine. T1 does not judge this.
- **T3 (context packet)** — `_format_constraints` at `blueprint_ensemble.py:1115-1309` emits `이전 종료 위치` inside `[연속성]` but never labels it as the authoritative input for `opening_transition.type`. That framing gap is a context-packet hypothesis for T3, not a prompt-text defect for T1.
- **T2 (retry feedback)** — `_blueprint_contract_admission_reason` at `blueprint_ensemble.py:908-915` returns stable strings (`missing_opening_transition`, `invalid_opening_transition`, `missing_protagonist_state`). Whether those strings are carried into the next attempt's prompt body is T2's question.
- **T5 (validator calibration)** — the placeholder-token blacklist at `scene_obligation_heuristics.py:84-107` is used only by the producer-side cheap gate, not by the main validator's `protagonist_state` check at `unified_blueprint_validator.py:2074-2093` (which only counts non-empty strings). Whether this asymmetry causes false-positive cheap rejects is T4/T5's question; T1 only records the anchor.
- **T4 (cheap admission effectiveness)** — the placeholder example at `config/prompts/ensemble.yaml:421` would narrowly pass `_has_meaningful_protagonist_state` (any-slot check) because `injuries` and `equipment` slots survive; T4 must measure whether real live runs show the mood-only-placeholder shape landing in rejects or warnings.
- **T7 (Director vs validator)** — Director rubric coverage of `opening_transition` is not read by T1; only observed that the prompt does not direct Director's own scoring path.
- **T9 (Stage2 handoff)** — the `_format_constraints` `이전 종료 위치` field is sourced from `constraint_block["continuity"]["location"]`, which upstream of T1 is built by the Stage2 → Stage3 handoff. T9 must judge whether that upstream location is concrete.

## 5. Hypothesis Candidates For Synthesis

Per §6 T1.5, the top 5 concrete, minimal **prompt-delta** candidates (pure text deltas, no code changes; hypotheses for synthesis, not directives). Each is the smallest possible edit that would most raise attempt-1 contract-pass probability.

### H1 — Add a decision table for `opening_transition.type` at or near `config/prompts/ensemble.yaml:411`

Replace the declaration block with a teaching block that names the decision rule in the same vocabulary `stage_cross_stage_contract.py:267-274` runs:

```
"opening_transition": 아래 표를 따르세요:
  - prev_end_location == start_location이고 time_flow에 '다음 날/잠시 후/이튿날/며칠 후/→' 같은 시간 전이 표현이 없으면 → "direct_continuation"
  - 위치는 같거나 같은 구역이지만 time_flow에 시간 전이 표현이 있거나 scene_1 summary에 '장면 전환/이동/도착/한편/* * *' 같은 전환 단서가 있으면 → "explicit_transition"
  - 이전 화 정보가 없거나 start_location이 prev_end_location과 완전히 다른 구역이면 → "jump_opening"
  (signals 예시: same_location_anchor, time_shift, scene_transition_cue, location_shift, no_prev_anchor)
```

ROI rationale: the single highest-frequency ep1–ep7 reject family (`0_temp.txt:400-469`) is `direct_continuation vs explicit_transition` normalization mismatch. The LLM currently cannot learn this rule from the prompt. One paragraph maps the validator's decision tree into the template directly and borrows the same `signals` vocabulary the validator already normalizes.

### H2 — Replace the placeholder `mood` example at `config/prompts/ensemble.yaml:421-423`

From:

```
"mood": "감정 상태",
"injuries": "부상 상태",
"equipment": ["소지품"]
```

To:

```
"mood": "<현재 감정을 한 단어로 구체화. 예: 분노·초조·자조·결의. '감정 상태/보통/동일' 같은 placeholder 금지>",
"injuries": "<구체 부위+정도. 예: 왼팔 자상(봉합)·갈비뼈 금. '부상 상태/없음' 금지>",
"equipment": ["<구체 아이템명. 예: 진액 단도·비단주머니. '소지품' 금지>"]
```

ROI rationale: removes the direct prompt↔cheap-admission vocabulary collision (F2) and gives the LLM three concrete shape examples for each of the three slots. Stays inside the existing schema hint and costs roughly 120 extra characters of template.

### H3 — Add `tactical_semantic_fidelity` decision rule + full intrusion token list near `config/prompts/ensemble.yaml:387`

Replace the six-token list in the existing clause with the full family from `blueprint_ensemble.py:140-169`, plus a one-sentence rule:

```
[전술 권위 규칙] Arc tactical_doc에 물리 위협/난입/충돌 이벤트가 명시되어 있지 않으면, 다음 토큰 중 어느 것도 key_events·summary·integrated_scenario에 새로 발명해 넣지 마세요:
  entry 계열: 취객, 난입, 들이닥, 무단침입, 괴한, 습격, 침입자, 철문, 그림자, 심부름센터, 직원
  conflict 계열: 멱살, 결박, 제압, 처리, 대응, 차단, 쫓아낸, 도망치, 위협, 협박, 박살, 쇠파이프, 쇠지렛대, 군화
이 규칙은 Arc tactical 권위 계약이며, 어길 경우 REJECT됩니다.
```

ROI rationale: eliminates the "I only know `난입/괴한` is banned so I'll write `쇠파이프를 들고 들이닥쳤다`" failure path observed in the earlier ep8 survey. Costs one paragraph of template.

### H4 — Add a `scenario_density` floor-vs-density contract around `config/prompts/ensemble.yaml:409`

Replace the one-line directive with a two-part rule:

```
"integrated_scenario": "최소 1000자 이상 + 씬별 최소 180자 (scene_breakdown의 모든 씬이 integrated_scenario에서 동일 순서로 구체 장면화되어야 함). 한 씬에 몰아쓰기 금지."
```

ROI rationale: prevents the "hit 1000 characters with one dense scene + four shells" failure path that the prompt currently cannot block. Mirrors the validator's per-scene density check without claiming to replicate it exactly.

### H5 — Add one positive + one negative paired example near `config/prompts/ensemble.yaml:455`

Append a short paired-example block to the self-check checklist:

```
[contract 예시 — 이 한 쌍만이라도 암기하고 출력하세요]
GOOD: prev_end_location="진영 동사". start_location="진영 동사 후원". time_flow="진각 오후 → 진각 초저녁". opening_transition={{"type":"direct_continuation","signals":["same_location_anchor"]}}. protagonist_state={{"mood":"결의","injuries":"왼팔 자상(봉합)","equipment":["진액 단도"]}}.
BAD: prev_end_location="진영 동사". start_location="진영 동사 후원". time_flow="다음 날 아침". opening_transition={{"type":"direct_continuation"}}  ← 다음 날이 있으므로 explicit_transition이어야 함. protagonist_state={{"mood":"감정 상태"}}  ← placeholder 금지.
```

ROI rationale: this is the smallest possible "show, don't tell" patch. A single paired example covers F1+F2 in 250 characters and is cheaper than rewriting the whole schema block. In-context-learning evidence generally shows paired examples move LLM behavior faster than rule lists alone.

Meta-note: these 5 hypotheses are **not** a directive. They are ranked candidates for the synthesis step to decide whether the ROI justifies a text delta, whether to bundle them into one edit, or whether to defer. Any of them landing requires T4 to confirm the cheap-admission catch rate on the current session after the delta, and T5 to confirm the validator false-positive share does not move adversely. T1 does not authorize any of these edits to be made.

## 6. 3-Pass Audit Record

### Pass 1 — Structure and scope check

- Confirmed deliverable is T1-only: judged initial-prompt content only; did not measure retry feedback (T2), did not touch validator correctness (T5), did not judge Director rubric (T7), did not rank cheap-admission effectiveness (T4).
- Confirmed all findings carry file:line anchors.
- Confirmed the 5 hypothesis candidates are framed as candidates, not directives, per §6 T1 non-goals ("do not rewrite the prompt — only list minimal text deltas as hypotheses").
- Confirmed no git mutation, no code change, no prompt change was made.
- Confirmed baseline commit was re-recorded at spawn and matches `32d6f0c8b56898fd8a370ae13684043d4cfda91a`.

### Pass 2 — Evidence and consistency check

- Re-ran live grep for `opening_transition|protagonist_state|tactical_semantic|scenario_density|scene_breakdown` against `config/prompts/ensemble.yaml` — only hits are `:296, :378, :385, :395, :411, :420, :442, :457, :458`. No occurrence of `scenario_density` or `tactical_semantic_fidelity` by name. F3 and F4 claims stand.
- Re-verified `_STATE_PLACEHOLDER_TOKENS` contents at `scene_obligation_heuristics.py:84-107`: includes `감정 / 상태 / 기분 / 변화 / 정상 / 보통 / 무난 / 동일 / 현재`. F2 leak claim stands.
- Re-verified `_has_meaningful_protagonist_state` is any-slot at `blueprint_ensemble.py:902-904`: any single slot passing the check short-circuits the return. This means the F2 leak does not single-handedly fail cheap admission when `injuries` and `equipment` survive, but the **mood example itself** still teaches the forbidden shape. F2 severity stays at `leak` (vocabulary collision), not `TP reject anchor`.
- Re-verified `stage_cross_stage_contract.py:267-274` decision rules match the plain-text rewrite in H1. Cross-checked alias map at `:162-177` to ensure the H1 wording uses tokens that would survive normalization.
- Re-verified `BLUEPRINT_STRATEGIES` count = 3 at `blueprint_ensemble.py:47-87`. The parent order §2.2 names five strategies; that is a Cross-Terminal Pointer for T6 and recorded as such.
- Re-verified `_build_blueprint_prompt_bundle` at `blueprint_ensemble.py:751-823` is a direct `_prompt_loader.load` call with variable substitution, no extra contract injection. F6 stands as a structural observation.
- Re-verified the ep8 symptom in `0_temp.txt:400-469` is exactly the `direct_continuation vs explicit_transition` mismatch that F1 attributes to the prompt-teaching gap. Correlation, not causation — T5 holds the true/false-positive split — but the correlation supports F1's severity ranking.

### Pass 3 — Execution and readability check

- Each finding leads with file:line, carries a severity tag, names the concrete code/prompt evidence, and is one readable paragraph.
- Cross-Terminal Pointers are one-liners, not re-analyses.
- The 5 hypotheses are in ROI order, each with a one-sentence rationale and an explicit meta-note that they are not directives.
- Front matter matches the §7 template verbatim.
- Deliverable filename matches §5 matrix (`t1-producer-initial-prompt-forensics.md`) and saves to `docs/2026-04-13/` as UTF-8.
- No triple-question placeholders, no U+FFFD, no ellipsis-truncated evidence quotes. All three weakest-passage quotes (W1/W2/W3) are verbatim and carry exact line anchors.

### Residual uncertainty

- Whether F2's leak is a **hard** reject path under current cheap admission cannot be stated without live-run counter evidence. Any-slot check at `blueprint_ensemble.py:902-904` means only a full 3-slot copy of the prompt example (all placeholders) would fail. Partial placeholder copies that preserve at least one concrete slot pass. Recorded as lowered-severity `leak`, not `TP reject anchor`; the real reject measurement is T4's job.
- Whether H1–H5 actually move attempt-1 pass rate is a live-run question, out of scope. T1 only ranks them by theoretical ROI.

## 7. Final Confidence

`96%` after 3-pass audit and live grep verification.

Residual 4% uncertainty enumerated above:

1. F2 severity anchor (`leak` vs `TP`) hangs on T4's live measurement of how often LLMs produce mood-only-placeholder shapes.
2. The parent order's "five strategies" count (§2.2) conflicts with `BLUEPRINT_STRATEGIES` having three entries (`blueprint_ensemble.py:47-87`). This is recorded as a Cross-Terminal Pointer for T6; it is not a T1 defect but could reshape T6's diversity measurement surface.
3. H1–H5 are theoretical candidates; their actual ROI needs synthesis-step decision plus downstream T4/T5 confirmation.

Above the `95%` floor required by §6 T1, so no `draft-only` flag. Deliverable saved.
