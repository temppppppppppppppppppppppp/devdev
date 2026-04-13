# T3 — Producer Context Packet Audit

- Parent Order: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Terminal: T3
- Date: 2026-04-13
- Mode: survey-only, read-only, parallel
- Baseline Commit (at spawn): `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: 31 modified (incl. `blueprint_ensemble.py`, `three_phase_blueprint_runtime.py`, `chief_writer.py`, `arc_ensemble.py`, `ensemble.yaml`, `response_schemas.py`, `scene_obligation_heuristics.py`, session artifacts, tests); 9 untracked (all `docs/2026-04-13/*.md|*.json` + one `projects/.../logs/metrics/*`). No code edits by this terminal.
- Resume Commit: same (`32d6f0c8`)
- Resume Drift Summary: none
- Side-Effect Coverage: read-only static + frozen live-run artifact reads; no mutation
- Confidence: `96%`

## Purpose

> What is actually inside the context the Stage3 producer LLM receives at `BlueprintEnsembleGenerator.generate_*` time — Stage2 arc truth (full or summarized?), prior-ep blueprint (which fields?), opening contract normalization vocabulary, bible / work guard / style guide — and which parts are spending the most token budget for the least contract-leverage?

Scope boundary reminder — per §8 non-overlap invariants:
- T1 judges prompt quality. T3 only reports composition, positional order, and raw/summarized state.
- T2 judges retry-time feedback fidelity. T3 only measures the *size* of retry feedback as a context slot.
- T8 attributes cost. T3 cites char/token counts as composition evidence, not as cost conclusions.

## Evidence Anchors

Code (read-only):
- `modules/domain/agents/blueprint_ensemble.py:272-665` — `BlueprintEnsembleGenerator` top-level pipeline + `generate_ensemble`
- `modules/domain/agents/blueprint_ensemble.py:339-382` — `_prepare_blueprint_ensemble_context` (context bundle assembly + shared cache creation)
- `modules/domain/agents/blueprint_ensemble.py:303-326` — `_resolve_blueprint_arc_focus` (15 000-char ceiling via `smart_truncate`, `head_ratio=0.55`)
- `modules/domain/agents/blueprint_ensemble.py:667-823` — `_generate_single` + `_build_blueprint_prompt_bundle` (prompt slot substitution + `cached_context_stub` gating)
- `modules/domain/agents/blueprint_ensemble.py:1011-1049` — `_build_protagonist_instructions`
- `modules/domain/agents/blueprint_ensemble.py:1051-1113` — `_build_reader_feedback_context` (I-23/I-24 DB advisory, empty-safe)
- `modules/domain/agents/blueprint_ensemble.py:1115-1309` — `_format_constraints` (4-band: IMMUTABLE / HARD / CONTINUITY / ADVISORY; caps via `_fit_compact_context`)
- `modules/domain/agents/blueprint_ensemble.py:1311-1313` — `_build_hud_context` delegating to shared `hud_utils.build_hud_context(variant="blueprint")`
- `modules/domain/agents/blueprint_ensemble.py:1315-1373` — `_format_prev_info` (single direct-prev BP, uncapped chars)
- `modules/domain/agents/blueprint_ensemble.py:1547-1627` — `_format_prev_blueprint_carryover` (per-BP structured carryover, field-level `_fit_compact_context` 40–180 chars)
- `modules/domain/agents/blueprint_ensemble.py:1629-1688` — `_format_prev_info_expanded` (4-Tier bundle: Tier 1 direct / Tier 2 structured (30-BP window, 400 000-char cap) / Tier 3 last-800-char ending excerpt / Tier 4 full prev manuscript (400 000-char cap); final `smart_truncate`)
- `modules/core/hud_utils.py:15-89` — `build_hud_context` (blueprint variant = writer variant shape; ≤13 extended fields, top-8 items, top-10 active NPCs + full dead-NPC list)
- `config/prompts/ensemble.yaml:287-461` — `BLUEPRINT_GENERATION_PROMPT` template (slot order, JSON schema, checklists)
- `modules/core/stage3_orchestrator.py:1325-1612` — `_bp_semantic_ctx` pipeline (SC slot retrieval + Treatment Block injection + Timeline advisory + world/style/fact/seed/work_focus advisories, no upper cap enforced here)
- `modules/core/stage3_orchestrator.py:1727-1812` — `_bp_semantic_ctx` wired into `three_phase_blueprint_runtime` as `semantic_context` kwarg
- `modules/domain/agents/three_phase_blueprint_runtime.py:1050-1109` — `initial_feedback = semantic_context + external_feedback`
- `modules/domain/agents/three_phase_blueprint_runtime.py:2942-2993` — retry cycle merges `attempt_feedback = initial_feedback [+ strategy_feedback]` before every Phase 2 call
- `modules/domain/agents/three_phase_blueprint_runtime.py:1400-1436` — `_run_phase2_generation` passes `feedback=attempt_feedback` and `strategy_specific_feedback=strategy_feedback` straight to `BlueprintEnsembleGenerator.generate_ensemble`
- `modules/domain/agents/base_agent.py:2227-2354` — `_ask_with_cached_context` (empty `cache_name` → fallback `ask()` with `full_prompt_fallback`; DB log captures `wrapped_prompt` in cached path)
- `modules/core/stage_cross_stage_contract.py:7-9, 162-177` — `OPENING_TRANSITION_*` constants + `_normalize_opening_transition_type` alias table (9 aliases → 3 canonical)
- `modules/core/stage_cross_stage_contract.py:205-222` — `_has_scene_transition_cue` + `_has_time_shift_cue` marker-list lookups used by the validator
- `modules/core/scene_obligation_heuristics.py:28-108, 136-153` — `_GENERIC_TOKENS` + `_ACTIONLESS_OBLIGATION_TOKENS` + `_STATE_PLACEHOLDER_TOKENS` blacklists that power `has_actionable_obligation_text` / `has_meaningful_state_value`

Live-run artifacts (frozen, `projects/000_260412_a/`):
- `logs/session/llm_io.jsonl` — 513 rows total, 286 rows `agent == "BlueprintEnsembleGenerator"`
- `logs/session/llm_io.jsonl:33` — ep1 attempt, first BP producer call, `prompt_len=12854`, `input_tokens=10049`
- `logs/session/llm_io.jsonl:34` — ep1 attempt worker #2, `prompt_len=12848`, `input_tokens=20087`
- `logs/session/llm_io.jsonl:35` — ep1 attempt worker #3, `prompt_len=12851`, `input_tokens=30132`
- `logs/session/llm_io.jsonl:66` — ep2 worker, `prompt_len=14465`, `input_tokens=11612`
- `logs/session/llm_io.jsonl:461` — largest ep7 producer call, `prompt_len=26884`, `input_tokens≈33k avg` for ep7 bucket
- `logs/session/llm_io.jsonl:495` — largest observed BP prompt, ep8, `prompt_len=28994`, `input_tokens=31896`

Per-episode prompt-length distribution across all 286 BP producer calls in `llm_io.jsonl` (measured via static read; reproducible command in §Evidence commands):

| ep | n  | prompt chars (min..max, avg) | input_tokens (min..max, avg) |
|----|----|------------------------------|-------------------------------|
| ep1 | 12 | 12 848..16 610 (avg 14 790) | 10 049..38 743 (avg 22 971) |
| ep2 | 54 | 14 459..20 710 (avg 19 355) | 11 605..49 732 (avg 31 004) |
| ep3 | 18 | 15 130..21 242 (avg 19 182) | 12 286..51 679 (avg 31 102) |
| ep4 | 30 | 15 990..21 903 (avg 17 250) |     0..53 731 (avg 17 785) |
| ep5 | 27 | 17 031..23 778 (avg 22 727) | 14 209..58 015 (avg 37 253) |
| ep6 | 30 | 17 944..24 124 (avg 23 360) | 15 120..60 076 (avg 38 902) |
| ep7 | 30 | 20 055..26 884 (avg 26 115) | 16 909..66 325 (avg 43 017) |
| ep8 | 27 | 21 108..28 994 (avg 26 729) | 12 113..69 115 (avg 32 845) |

Composition counts across all 286 BP rows:

| marker | rows | fraction |
|--------|------|----------|
| `[CRITICAL] Director reject feedback` header | 228 | 79.7% |
| `[작품 메모리 소비 계약 - Stage 3 Blueprint 설계]` | 228 | 79.7% |
| `[Context Tier 1 - Direct Previous Episode Truth]` | 228 | 79.7% |
| `[Context Tier 2 - Structured Previous Blueprint Carryover]` | 216 | 75.5% |
| `[Context Tier 3 - Manuscript Ending Truth]` | 0 | 0.0% |
| `[Context Tier 4 - Archive Appendix / lower priority than Tier 1-3]` | 0 | 0.0% |
| `[V67] ═══ 이전 Blueprint 전문` | 216 | 75.5% |
| `[V67] ═══ 이전 원고 전문` | 0 | 0.0% |
| ≥ 2× occurrence of `[작품 추적 슬롯 요약]` within one prompt | 159 | 55.6% |
| ≥ 2× occurrence of `[Arc 개요` within one prompt | 159 | 55.6% |
| prompt contains `[context cached: refer to cached_content]` stub | 0 | 0.0% |

Section offset map for `llm_io.jsonl:461` (largest observed ep7 producer call, `prompt_len = 26 884`), measured by string-finding each `### [...]` / `[전략` marker:

```
  offset    size  section
  ------  ------  -----------------------------------------
      0      56  ### [AUTHOR'S ABSOLUTE DIRECTIVES]
     56     109  ### [TASK]
    165     366  ### [Stage3 장면 권위 계약]  (static)
    531     183  ### [안티 HUD / 안티 시스템 UI]  (static)
    714     589  ### [안티 크로스 장르 오염]  (static)
   1303     197  ### [Context Priority Contract]  (static)
   1500    1939  ### [Constraint Stack / 제약 조건]      ← {constraints}
   3439     192  ### [Arc Mission / 이번 화 핵심]        ← {arc_focus}
   3631   11720  [전략 …]                                ← {strategy_directive}
  15351    6218  ### [Previous Truth And Archive]        ← {prev_info}
  21569     236  ### [HUD Convenience State]             ← {hud_context}
  21805     688  ### [V60.98 씬 프리셋 - 장면/화자 전환 연출]  (static)
  22493     808  ### [주인공 고평가 연출 가이드]         (static)
  23301     164  ### [Stage3 장면 권위 계약 - 절대 준수]  (static)
  23465     579  ### [오염 금지 레지스터]                 (static)
  24044    1319  ### [출력 형식 - 반드시 JSON만 출력]     (static, schema)
  25363      44  ### [TF-I23/I24] 독자 반응 추이           ← {reader_feedback}
  25407     144  ### [V63] 독자 경험 설계                 (static)
  25551     354  ### [필수 조건]                          (static)
  25905     471  ### [자가 검증 체크리스트]               (static)
  26376     461  ### [V67] 모순 방지 - 절대 준수 사항      (static)
  26837      47  ### [FORMAT]                             (static)
```

Composition shares at ep7 (26 884 chars total):
- **{strategy_directive} block = 11 720 chars (43.6%)** — the single dominant slot.
- {prev_info} (`[Previous Truth And Archive]`) = 6 218 chars (23.1%).
- Static boilerplate (header + anti-HUD + anti-cross-genre + priority contract + presets + high-praise + contract-2 + 오염 금지 + output JSON + checklists + V67 모순) ≈ 6 018 chars (22.4%).
- {constraints} = 1 939 chars (7.2%).
- {arc_focus} = 192 chars (0.7%).
- {hud_context} = 236 chars (0.9%).
- {reader_feedback} = 44 chars (empty; 0.2%).

## Findings

Each finding carries a file:line or `llm_io.jsonl:row` anchor and a severity tag (`waste` = high cost + low contract leverage, `gap` = missing contract input, `leak` = content crosses a slot boundary, `FP` = false positive, `TP` = true positive, `hypothesis` = needs synthesis).

### F1. `{strategy_directive}` is the largest and most mislabeled dynamic slot. [waste]

- Anchors: `blueprint_ensemble.py:777-782` (assembly), `blueprint_ensemble.py:685-700` (retry wrapper that prepends `[CRITICAL] Director reject feedback`), `llm_io.jsonl:461` offset 3 631–15 351 (11 720 chars at ep7).
- Assembly order for this slot, per code: `strategy["directive"]` (≈250 chars) `+ AI_TELL_BLUEPRINT_GUARDRAIL` (≈700 chars) `+ extra_directive` (`[CRITICAL] Director reject feedback\n{feedback}\n…`) `+ work_retrieval_contract` (from `guard.get_retrieval_contract_prompt("blueprint")`).
- Observed ep1 baseline at `llm_io.jsonl:33` shows the same slot already = 4 630 chars — i.e. ≈3 680 chars of non-strategy content land in this slot even on ep1 first attempt.
- Growth to 11 720 chars at ep7 comes almost entirely from `extra_directive` accumulating `initial_feedback` (which is `semantic_context + external_feedback`, built in `three_phase_blueprint_runtime.py:1083`) and `strategy_feedback` (from `_build_retry_strategy_feedback`).
- Severity: high — this one slot is 2–6× larger than every directly contract-relevant slot combined (`constraints` + `arc_focus` + `hud_context` + `prev_info` = 8 585 chars at ep7, vs 11 720 here).

### F2. The `[CRITICAL] Director reject feedback` header is a semantic mislabel. [leak → cross-terminal]

- Anchor: `blueprint_ensemble.py:694-700`.
- The code wraps `extra_directive` under the header `[CRITICAL] Director reject feedback` whenever `merged_feedback` is non-empty, but `merged_feedback = feedback + strategy_feedback`, and `feedback` is `initial_feedback` which is `semantic_context + external_feedback` (see `three_phase_blueprint_runtime.py:1083, 2942-2993`).
- Consequence from a *composition* standpoint: content that is advisory semantic context (tracking slots, StyleGuide, Arc 개요 treatment block, timeline advisory, Arc 메모리 소비 계약, 작품 추적 슬롯) enters the prompt under a header that labels it as "Director reject feedback".
- Evidence: `llm_io.jsonl:33` is the first BP producer call in the run (pre-run; no earlier Director verdict exists) yet already contains the full `[CRITICAL] Director reject feedback` block populated with `[작품 추적 슬롯 요약]`, `[StyleGuide]`, `[Arc 개요]`, `[작품 메모리 소비 계약]`, ending with `Apply the feedback directly. Repeating the same failure will be rejected again.`
- Frequency: `228 / 286` rows (79.7%) contain the `[CRITICAL] Director reject feedback` header, matching exactly the `228 / 286` rows that contain `[작품 메모리 소비 계약]` — i.e. every semantic-context injection is wearing the reject-feedback header.
- Scope note: *whether this hurts learning* is T1 / T2 territory. T3 only records that the slot positioning is misaligned with the slot label — recorded as a cross-terminal pointer (§Cross-Terminal Pointers, CP-1, CP-2).

### F3. Semantic-context blob is duplicated inside 55.6% of all BP prompts. [waste]

- Anchor: `llm_io.jsonl:461` (ep7) shows:
  - one occurrence of `[작품 추적 슬롯 요약]` + `[Arc 개요 — 아크 7~12화 방향성 참조]` block at offset ~3 700 (inside `extra_directive` from `initial_feedback`)
  - a second occurrence at offset ~7 800 wrapped under `[이전 REJECT 피드백]`
- Count across all 286 BP rows: 159 rows contain `[작품 추적 슬롯 요약]` ≥ 2× and 159 rows contain `[Arc 개요` ≥ 2× — both numbers identical, i.e. the duplication is one coupled blob.
- Source chain: `initial_feedback` (pre-loaded semantic context) is merged with retry-strategy-feedback in `three_phase_blueprint_runtime.py:2960-2962` so the *same* semantic blob appears twice — once as initial, once again as the "previous attempt's strategy feedback" carried forward into attempt N+1.
- Per-row duplication cost measured at ep7: the duplicated tracking_slots + StyleGuide + 시간 연속성 + Arc 개요 bundle ≈ 4 000–5 500 chars depending on which advisories are present. At 159 rows this is ≈660 000 char-duplications across the run from this single pattern.
- Scope note: *how to dedupe* (one-shot vs incremental append vs diff-only feedback) is T2 territory. T3 only reports that the blob is physically duplicated in the rendered prompt.

### F4. `{arc_focus}` lands as a 192-char shell at ep7 because `must_focus.content` was re-routed into `{constraints}`. [leak]

- Anchors: `blueprint_ensemble.py:303-326` (`_resolve_blueprint_arc_focus`), `blueprint_ensemble.py:1143-1159` (`must_focus` routed into `hard_lines` inside `_format_constraints`), `llm_io.jsonl:461` offsets 1 500–3 631 (Constraint Stack block 1 939 chars) and 3 439–3 631 (Arc Mission block 192 chars).
- `_resolve_blueprint_arc_focus` tries `constraint_block["must_focus"]["content"]` first, then falls back to `extract_episode_tactical(...)`, and may prepend an `episode_details` boost. Ceiling is 15 000 chars.
- `_format_constraints` reads the same `must_focus.content` at lines 1156-1159 and renders it (capped at 500 chars) inside the HARD CONSTRAINT band of `{constraints}`.
- Observation at `llm_io.jsonl:461`: `{arc_focus}` collapsed to a 192-char bullet list (`[7화 추가 사건 (Arc 단계 보강)] …`) while `{constraints}` hard-lines already carry the full `must_focus` text. The Arc Mission slot advertised by the YAML template as "이번 화 핵심" is nearly empty.
- Severity: moderate. The producer is told by `[Context Priority Contract]` (`ensemble.yaml:317-320`) that "Arc Mission outranks previous-truth archive", but Arc Mission is physically the smallest dynamic slot in the packet. The content the producer needs for tactical grounding is present but located under a different header.
- Scope note: fixing the routing (e.g. letting `_resolve_blueprint_arc_focus` draw from a richer `tactical_doc` window while `_format_constraints` carries only the hard-limit summary) is downstream hypothesis material, not a T3 verdict.

### F5. Static boilerplate is ≈6 KB per call and is repeated raw inside every fallback prompt. [waste — conditional on cache status]

- Anchor: `llm_io.jsonl` bulk scan — 0 / 286 rows contain the `[context cached: refer to cached_content]` stub literal.
- Code path: `_build_blueprint_prompt_bundle` (blueprint_ensemble.py:751-823) builds two variants — a stub variant if `cache_name` is truthy and a full variant as `full_prompt_fallback`. `_ask_with_cached_context` (`base_agent.py:2250-2254`) returns via `ask()` with the fallback whenever `cache_name` is empty.
- Frozen-run observation: every captured BP producer prompt is a fully expanded fallback-shape body (header + anti-HUD + anti-cross-genre + priority contract + presets + high-praise + contract-2 + 오염 금지 + output JSON + checklists + V67 모순 — all present as literal strings). This means either
  - (a) `cache_name` was consistently empty during this run (cache creation failed or the blueprint cache path was skipped), or
  - (b) the DB log captured the `wrapped_prompt` of the cached path and that wrapped prompt already embeds the boilerplate. Reading `base_agent.py:2256-2264` shows that in the cached path `wrapped_prompt = f"### [AUTHOR'S ABSOLUTE DIRECTIVES]…### [TASK]\n{prompt}…"` where `prompt` is the BLUEPRINT_GENERATION_PROMPT body — so the boilerplate and the stub would still be in `wrapped_prompt`. The 0-stub count therefore rules out option (b).
- Consequence: 228 of 286 calls paid for ≈6 KB of static boilerplate each as fresh input tokens rather than as cached tokens. Whether this is in fact a "waste" depends on Gemini's per-call cache pricing — **T8 territory**. T3 only records the composition fact.
- Scope note: this is recorded as `waste — conditional` because the verdict is cost-sensitive.

### F6. `{prev_info}` Tier 3 / Tier 4 paths are dormant; producer sees Blueprint metadata only, not manuscript text. [gap — visibility]

- Anchors: `blueprint_ensemble.py:1658-1685` (Tier 3 last-800-char excerpt + Tier 4 full-manuscript body with 400 000-char cap), `llm_io.jsonl` bulk scan — 0 / 286 rows contain `[Context Tier 3` or `[Context Tier 4` or `[V67] ═══ 이전 원고 전문`.
- Source of `prev_manuscripts_text`: passed through `three_phase_blueprint_runtime.py:1414` into `generate_ensemble` from stage3_orchestrator. In this run it was empty/absent for every BP call, so `_format_prev_info_expanded` falls through to Tier 1 + Tier 2 only.
- Contract relevance: `stage_cross_stage_contract.py:205-222` checks scene-transition and time-shift markers against the incoming payload's *own* scene text, and opening-transition continuity against the *prev blueprint*, so this gap does not directly starve the opening_transition normalizer. It does, however, mean the producer cannot see whether Stage4 re-ordered scenes or changed wording vs what the prior-ep Blueprint declared.
- Severity: low-to-moderate. Recorded as a *visibility gap*, not a starvation.

### F7. `{constraints}` at ep1 carries `이전 종료 위치: 서사 시작점` as the only continuity datum. [TP — as-designed]

- Anchors: `blueprint_ensemble.py:1188-1215` (`EXPECTED CONTINUITY` band), `llm_io.jsonl:33` offset ~2 190 (`[연속성] / 이전 종료 위치: 서사 시작점`).
- Nothing in the ep1 continuity band is stale or wrong — this is correctly advising "no prior episode". Recorded to confirm the band works and is not a starvation surface at ep1.

### F8. `{hud_context}` is ≈236 chars per call regardless of ep. [TP — bounded as-designed]

- Anchors: `hud_utils.py:15-89` (blueprint variant = writer-variant shape; ≤13 extended fields, top-8 items, top-10 alive NPCs + unbounded dead-NPC list), `llm_io.jsonl:461` offset 21 569 (236 chars at ep7).
- The blueprint variant suppresses the `(상태 추적기 없음)` / `(HUD 정보 없음)` fallbacks and returns `(상태 정보 없음)` or a compact alive/dead NPC block. Size growth is bounded: ~200–400 chars across ep1-ep8.
- Recorded to confirm `{hud_context}` is not a waste surface at current data volume. One latent risk: the dead-NPC list is uncapped per `hud_utils.py:192-197` — at 100 ep+ this could grow unboundedly, but not at ep8.

### F9. Producer prompt never exposes the validator's opening_transition alias table. [gap — contract starvation]

- Anchors: `stage_cross_stage_contract.py:162-177` (alias map: 9 aliases → 3 canonical), `ensemble.yaml:411-414` (schema advertises only the three canonical enum values with no semantics), `blueprint_ensemble.py:990-1009` (`_normalize_opening_transition_contract` is a *post-hoc* candidate rewriter, not a producer-visible hint).
- The alias entries `direct`, `continuation`, `same_place_continuation`, `transition`, `scene_transition`, `cut_transition`, `jump`, `time_jump` are live contract inputs — the validator normalizes any of them into the canonical triple — but none of these strings or their semantics land in the producer's context packet.
- Consequence from a *composition* standpoint: the producer has no reference table for "what makes an opening count as `direct_continuation` vs `explicit_transition` vs `jump_opening`" inside the rendered prompt. The only guidance is the JSON schema enum line at `ensemble.yaml:411-414`.
- Scope note: *whether this is a prompt-quality gap* is T1 territory. T3 records only that an enumerated contract vocabulary exists in code but is not present in the context packet. Logged as a cross-terminal pointer.

### F10. Producer prompt never exposes the actionless-obligation blacklist. [gap — contract starvation]

- Anchors: `scene_obligation_heuristics.py:28-108` (`_GENERIC_TOKENS`, `_ACTIONLESS_OBLIGATION_TOKENS`, `_STATE_PLACEHOLDER_TOKENS`), `scene_obligation_heuristics.py:136-153` (`has_actionable_obligation_text`), `ensemble.yaml:386, 455` (the only prompt lines that touch this concern).
- The validator rejects scenes whose `key_events` / `obligations` text contains only generic tokens (`개요`, `결말`, `갈등`, `구성`, `도입`, `마무리`, `반응`, `변화`, `절정`, `진행`, `준비`, etc.). The producer prompt says "비어 있는 key_events, '진행/갈등/절정' 같은 껍데기 요약만 있는 scene shell은 금지입니다." — a rough qualitative warning covering 3 of 31 actionless tokens.
- From a composition standpoint: 28 of 31 actionless tokens in the code-side blacklist have no representative in the producer's context packet.
- Scope note: ranking this as a *producer quality* gap is T1 territory. T3 records only that the vocabulary used by the validator exists in code and is not inlined into the context packet. Logged as a cross-terminal pointer.

### F11. `{reader_feedback}` evaluates to the empty string in the observed run. [TP — empty-safe, not a waste]

- Anchors: `blueprint_ensemble.py:1051-1113`, `llm_io.jsonl:461` offset 25 363 = 44 chars (just the `### [TF-I23/I24] 독자 반응 추이 (참고용, advisory)` header, no body).
- `_build_reader_feedback_context` depends on `db.get_recent_satisfaction_tags` / `db.get_recent_pacing_records`. For this run both returned empty, so the body is "". The 44-char header cost is negligible.

### F12. `work_retrieval_contract` fetch is executed twice per producer call but only once materializes into the prompt. [FP — benign duplication]

- Anchors: `blueprint_ensemble.py:360-365` (first call inside `_prepare_blueprint_ensemble_context`, return value discarded), `blueprint_ensemble.py:767-773` (second call inside `_build_blueprint_prompt_bundle`, return value appended to `strategy_directive`).
- The first call's return value is captured and then dropped — only a "retrieval contract loaded" side-effect. The prompt-side cost is only the second call's output (and that output was empty in inspected samples, since `guard` does not expose `get_retrieval_contract_prompt` for the default work_guard config in this run).
- Scope: a defensive pre-warm pattern, not a context-packet waste. Recorded to prevent double-counting in synthesis.

## Cross-Terminal Pointers

- **CP-1 → T1 (Producer Initial-Prompt Forensics):** the `[CRITICAL] Director reject feedback` wrapper in `blueprint_ensemble.py:694-700` labels semantic_context as reject-feedback even when there has been no reject. T1 should decide whether to relabel / split that header or to reclassify the wrapped content as a dedicated `[Advisory / Memory Consumption Contract]` slot.
- **CP-2 → T2 (Retry Feedback Loop Audit):** the duplication measured in F3 (159 / 286 BP prompts carry the tracking-slot + Arc-개요 blob twice) originates in the merge at `three_phase_blueprint_runtime.py:2960-2962` (`attempt_feedback = initial_feedback [+ strategy_feedback]`). T2 should decide whether strategy_feedback can be dedup'd against initial_feedback at the source.
- **CP-3 → T1:** F9 (opening-transition alias table) and F10 (actionless-obligation blacklist) are contract-vocabulary starvation surfaces. T3 reports they are absent from the context packet; T1 decides whether that is a prompt-quality gap.
- **CP-4 → T8 (Cost-to-Outcome Attribution):** F5 (zero `[context cached]` stubs captured across 286 BP rows) needs cost-side attribution. Either cache_name was empty for BP generation in this run, or the DB logger captured the wrapped prompt including the boilerplate. T8 has access to `metrics_*.json` token-cost tables and should adjudicate.
- **CP-5 → T6 (Ensemble Candidate Diversity Audit):** per-ep1 rows 33/34/35 show 3 BP workers firing in parallel on the same cache window but with monotonically growing `input_tokens` (10 049 → 20 087 → 30 132). T3 cannot explain this pattern from composition alone — T6 already has the `final_blueprint__*.json` per-worker artifacts that would confirm whether these are truly parallel fan-out or sequential re-attempts.
- **CP-6 → T9 (Stage2 → Stage3 Handoff Quality):** F4 (`{arc_focus}` collapses to 192 chars while `{constraints}` hard-lines carry the tactical content) is *partly* a Stage2 handoff shape question — `must_focus.content` is the field Stage2 populates. T9 decides whether Stage2's packet shape should route tactical truth into `arc_focus` directly instead of piggy-backing on `must_focus`.
- **CP-7 → T10 (Stage3 → Stage4 Handoff):** F6 (Tier 3 / Tier 4 dormant) implies Stage4-emitted manuscript text is not re-entering the Stage3 producer loop. T10 judges whether the Stage4 output should be re-consumed by Stage3 for the next episode.

## Hypothesis Candidates For Synthesis

Framed explicitly as *candidates*, not directives. Anchors repeat the F-tag that produced them.

- **H-A (from F1 + F2 + F3):** The `{strategy_directive}` slot is load-bearing ~43% of dynamic budget and is the single largest high-cost / low-contract-leverage surface in the packet. Candidate: split the slot into (i) strategy-only directive (~250 chars), (ii) guardrail (~700 chars, static-cacheable), (iii) memory-consumption advisory (dedup'd between initial and retry paths), (iv) retry-only feedback under a dedicated `[Retry Feedback — attempt N of M]` header that only exists when there *was* a prior reject. Hypothesis, not a rewrite proposal.
- **H-B (from F4 + CP-6):** The `{arc_focus}` slot is under-budgeted relative to the `[Context Priority Contract]` declaration. Candidate: either widen `_resolve_blueprint_arc_focus` (which already has a 15 000-char ceiling but receives only the bullet-list excerpt) or drop the redundant `must_focus.content` render from `_format_constraints` to avoid the slot leak.
- **H-C (from F5 + CP-4):** The ~6 KB static boilerplate block is never successfully cached in the observed run. Candidate: if T8 confirms cache is inactive for BP producer calls, investigate why `_get_or_create_context_cache("blueprint_ensemble", ...)` is returning empty `cache_name`. If T8 confirms it is active but the DB log writes the fallback body, the waste is only a logging artifact and H-C drops.
- **H-D (from F9 + F10 + CP-3):** Two *contract vocabularies* (opening_transition alias table; actionless-obligation blacklist) exist in code and are never rendered into the context packet. Candidate: lift both as a small static `[Contract Vocabulary]` slot ordered immediately before `[Constraint Stack]`, so the producer can align its own output to the validator's normalization rules before generation. Hypothesis, not a prompt rewrite — T1 must adjudicate whether the prompt quality gap is real.
- **H-E (from F6 + CP-7):** Tier 3 / Tier 4 are dead code in the observed run. Candidate: either activate by feeding `prev_manuscripts_text` from the real Stage4 output, or drop the 400 000-char ceiling paths to simplify the context builder. H-E depends on T10's handoff verdict.

## Evidence commands (reproducible, read-only)

- Section-offset map at `llm_io.jsonl:461`:
  ```python
  import json
  with open('projects/000_260412_a/logs/session/llm_io.jsonl', encoding='utf-8') as f:
      for i, line in enumerate(f):
          if i != 461: continue
          p = json.loads(line)['prompt']
          markers = ['### [AUTHOR','### [TASK]','### [Stage3 장면 권위 계약]','### [안티 HUD','### [안티 크로스','### [Context Priority Contract]','### [Constraint Stack','### [Arc Mission','[전략','### [Previous Truth And Archive]','### [HUD Convenience State]','### [V60.98','### [주인공 고평가','### [Stage3 장면 권위 계약 - 절대','### [오염 금지','### [출력 형식','### [TF-I23','### [V63] 독자','### [필수 조건]','### [자가 검증','### [V67] 모순','### [FORMAT]']
          off = sorted([(p.find(m), m) for m in markers])
          for k,(idx,m) in enumerate(off):
              if idx < 0: continue
              nxt = next((ni for ni,_ in off[k+1:] if ni > idx), len(p))
              print(f'{idx:6d} {nxt-idx:6d} {m}')
          break
  ```
- Tier / duplication census:
  ```python
  import json
  tier = {f'[Context Tier {k}': 0 for k in '1234'}
  crit = dup_ts = dup_arc = 0
  with open('projects/000_260412_a/logs/session/llm_io.jsonl', encoding='utf-8') as f:
      total = 0
      for line in f:
          r = json.loads(line)
          if r.get('agent') != 'BlueprintEnsembleGenerator': continue
          total += 1; p = r.get('prompt') or ''
          for k in tier: tier[k] += (k in p)
          crit += '[CRITICAL] Director reject feedback' in p
          dup_ts += p.count('[작품 추적 슬롯 요약]') >= 2
          dup_arc += p.count('[Arc 개요') >= 2
  print(total, crit, tier, dup_ts, dup_arc)
  ```

## 3-Pass Audit Record

### Pass 1 — Draft assembly

- Built section-offset map for `llm_io.jsonl:461` (ep7 largest) and `llm_io.jsonl:33` (ep1 first BP), and a composition census across all 286 BP rows.
- Pulled each context-builder function in `blueprint_ensemble.py` (`_prepare_blueprint_ensemble_context`, `_resolve_blueprint_arc_focus`, `_format_constraints`, `_build_hud_context`, `_format_prev_info`, `_format_prev_blueprint_carryover`, `_format_prev_info_expanded`, `_build_reader_feedback_context`, `_build_protagonist_instructions`, `_build_blueprint_prompt_bundle`) and traced the slot-to-slot mapping into `BLUEPRINT_GENERATION_PROMPT` at `ensemble.yaml:287-461`.
- Traced `extra_directive` back through `three_phase_blueprint_runtime.py:2940-2993` → `stage3_orchestrator.py:1325-1612` to confirm that `initial_feedback = semantic_context + external_feedback`, i.e. that the `[CRITICAL] Director reject feedback` header wraps semantic_context by construction, not only retry feedback.
- Drafted findings F1–F12.

### Pass 2 — Evidence and consistency

- Verified 0-stub claim (F5) by searching every BP prompt for `[context cached: refer to cached_content]` — 0 / 286. Confirmed via `_ask_with_cached_context` (`base_agent.py:2227-2354`) that the stub would have appeared in the logged prompt if cache_name had been truthy.
- Verified duplicated-blob claim (F3) by counting `p.count('[작품 추적 슬롯 요약]') >= 2` and `p.count('[Arc 개요') >= 2` independently — both 159 / 286, identical, confirming one coupled blob rather than two independent repetitions.
- Verified Tier 3 / Tier 4 dormancy (F6) by scanning for `[Context Tier 3` and `[Context Tier 4` and for `[V67] ═══ 이전 원고 전문` — all 0 / 286.
- Verified `{arc_focus}` vs `{constraints}` leak (F4) by comparing `_resolve_blueprint_arc_focus` output (at `blueprint_ensemble.py:303-326`) against the `[7화 추가 사건 (Arc 단계 보강)]` bullet list observed at offsets 3 439–3 631 in `llm_io.jsonl:461`, and against the HARD CONSTRAINT band rendering `must_focus.content` at offsets ~2 200–2 600 in the same row.
- Verified the opening-transition alias table (F9) exists in code at `stage_cross_stage_contract.py:162-177` and does *not* appear in `ensemble.yaml` via `grep "alias_map\|same_place_continuation\|cut_transition\|time_jump"` on the YAML (no matches).
- Verified the actionless-obligation blacklist (F10) exists in code at `scene_obligation_heuristics.py:28-108` and the YAML at `ensemble.yaml:386` only warns about 3 of the 31 blacklisted tokens (`진행 / 갈등 / 절정`).

### Pass 3 — Execution and readability

- Re-read §8 non-overlap invariants to confirm every finding that ranks *quality* is routed through Cross-Terminal Pointers rather than stated as a T3 verdict. F2/F9/F10 in particular had their "this is bad" framings rewritten to "this is present-or-absent" composition claims, with *judgment* delegated to T1/T2.
- Re-checked cost claims (F5) to ensure they are framed as "conditional on T8 adjudication", not as a ranked cost conclusion.
- Confirmed every finding anchors to file:line or `llm_io.jsonl:row`. No `unanchored — lower confidence` tags needed.
- Removed one weaker finding from the draft ("F11.5 — `_build_protagonist_instructions` varies genre-by-genre and might be under-injected") because it reduces to a T1 quality question once the injection site is mapped; kept the positive F11 (empty-safe `reader_feedback`) because it confirms a bounded slot instead of raising a gap.
- Confidence floor check: 96% — the one residual uncertainty is CP-4 (cache-captured-vs-active). Since the deliverable treats F5 as *conditional on T8*, the uncertainty is isolated and does not block the rest.

## Final Confidence

`96%`
