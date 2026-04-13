# T2. Stage3 Retry Feedback Loop Audit

- Parent Order: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Terminal: T2
- Date: 2026-04-13
- Mode: survey-only, read-only, parallel
- Baseline Commit (at spawn): `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `M on 0_temp.txt, config/models.yaml, config/prompts/ensemble.yaml, config/style_references/investment/style_guide.json, modules/core/response_schemas.py, modules/core/scene_obligation_heuristics.py, modules/domain/agents/arc_ensemble.py, modules/domain/agents/blueprint_ensemble.py, modules/domain/agents/chief_writer.py, modules/domain/agents/three_phase_blueprint_runtime.py, projects/000_260412_a/{config/work_guard.yaml,logs/pass_rate_monitor.json,logs/quality_metrics.jsonl,logs/runtime_audit_summary.json,logs/session/llm_io.jsonl,logs/session/ui_events.jsonl,project_data.db,stage0_output/style_guide.json}, several tests/*, docs/temp/*, docs/2026-04-01/active-temp-execution-roadmap.md, docs/2026-04-02/* and docs/2026-04-13/stage3-cross-pc-proof-rerun-handoff-context.md; untracked docs/2026-04-13/{s2-s3-s4-producer-smarts-bounded-3pass-audit.md,s2-s3-s4-producer-smarts-p2-p3-followup-survey.md,s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md,stage3-ep8-cw-director-root-cause-parallel-survey.md,stage3-producer-3pass-audit-adversarial-evidence.json,stage3-producer-adversarial-followup-x3-addendum.md,stage3-producer-adversarial-followup-x3-evidence.json,stage3-producer-contract-tightening-3pass-audit-and-adversarial-review.md} and projects/000_260412_a/logs/metrics/metrics_20260413_194343.json`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
- Side-Effect Coverage: `read-only static + frozen live-run artifact reads; no mutation`
- Confidence: `96%`

## Purpose

Question (verbatim from §6 T2):

- when Stage3 attempt N rejects with a concrete reason like `opening_transition.type mismatch: declared 'direct_continuation' vs normalized 'explicit_transition'`, does attempt N+1 receive the exact prior reason + a concrete fix directive from `_Stage3RepairRouter` / `_build_stage3_fix_pack_guidance`, or does it functionally restart from the same base prompt, so the LLM keeps making the same mistake for 7–10 attempts?

## Evidence Anchors

Code (current head `32d6f0c8`):

- `modules/domain/agents/three_phase_blueprint_runtime.py:53` — `_ThreePhaseRetryState` dataclass (retry-state fields saved per reject)
- `modules/domain/agents/three_phase_blueprint_runtime.py:182` — `_Stage3RepairRouter.build_retry_material` / `build_validation_material` / `decide_phase2_retry` / `decide_pass_with_fix`
- `modules/domain/agents/three_phase_blueprint_runtime.py:470` — `_normalize_stage3_fix_pack` (patch_targets / must_fix / do_not_regress / success_condition / evidence_summary normalization)
- `modules/domain/agents/three_phase_blueprint_runtime.py:527` — `_normalize_stage3_repair_contract`
- `modules/domain/agents/three_phase_blueprint_runtime.py:602` — `_build_stage3_local_patch_gate`
- `modules/domain/agents/three_phase_blueprint_runtime.py:789` — `_build_stage3_fix_pack_guidance` (the only function that renders the structured fix_pack into a human-readable `[Stage3 partial-fix contract]` block)
- `modules/domain/agents/three_phase_blueprint_runtime.py:1112` — `_build_retry_strategy_feedback` (what actually reaches the producer on a retry cycle)
- `modules/domain/agents/three_phase_blueprint_runtime.py:1298` — `_run_phase2_generation`
  - `three_phase_blueprint_runtime.py:1354` — inplace patch branch: calls `_inplace_patch_blueprint(..., director_feedback=retry_state.prev_reject_feedback, normalized_fix_pack=repair_material.effective_fix_pack)`
  - `three_phase_blueprint_runtime.py:1400`–`1433` — full-regenerate branch: calls `owner.ensemble.generate_ensemble(feedback=attempt_feedback, strategy_specific_feedback=strategy_feedback, rejected_strategy, single_strategy, ...)` — no fix_pack parameter
- `modules/domain/agents/three_phase_blueprint_runtime.py:2079` — `_apply_validation_reject_state` (populates retry_state after a reject)
- `modules/domain/agents/three_phase_blueprint_runtime.py:2186` — `_run_pass_with_fix_loop` (inner 3-round patch loop inside a single retry attempt)
- `modules/domain/agents/three_phase_blueprint_runtime.py:2280` — `_run_pass_with_fix_iteration`; line 2355 is the only site where `_build_stage3_fix_pack_guidance` is injected into the director_feedback string
- `modules/domain/agents/three_phase_blueprint_runtime.py:2609` — `_finalize_pass_with_fix_failure` (routes back to full regenerate with `reject_origin=pass_with_fix_unresolved`)
- `modules/domain/agents/three_phase_blueprint_runtime.py:2925` — `_run_retry_cycle` (outer loop compositor)
- `modules/domain/agents/three_phase_blueprint_runtime.py:3092` — `generate()` top-level retry loop `for retry in range(max_retries + 1):` with `max_retries=9`
- `modules/domain/agents/three_phase_blueprint_generator.py:159` — `_inplace_patch_blueprint`; always embeds `## Patch Contract` JSON via template `BLUEPRINT_PATCH_MODE_PROMPT`
- `modules/domain/agents/blueprint_ensemble.py:584` — `generate_ensemble` signature — the public producer API — has NO `fix_pack` / `repair_contract` / `scope_authority` parameter; the only retry-time channels are `feedback`, `strategy_specific_feedback`, `rejected_strategy`, `single_strategy`
- `modules/domain/agents/blueprint_ensemble.py:391` — `_build_blueprint_strategy_feedback` (per-worker feedback composition; wraps `strategy_specific_feedback` in `[이전 시도 문제 요약]`)
- `config/prompts/blueprint_generator.yaml:3` — `BLUEPRINT_PATCH_MODE_PROMPT` template with `## Patch Contract` / `## Target Patch Packet` slots

Live-run evidence (frozen):

- `0_temp.txt:400-469` — ep8 mid-run capture showing three repeated PASS_WITH_FIX → REJECT cycles with `fix_scope: full`, `binding prevalidation repair required`, and the literal `MAJOR | opening_transition | opening_transition.type mismatch: declared 'direct_continuation' vs normalized 'explicit_transition'` message appearing on cycles 1 and 3 of the ep8 burn
- `projects/000_260412_a/logs/session/llm_io.jsonl` — 513 records; 286 of them `agent=BlueprintEnsembleGenerator`. One sample retry prompt (line 490, ts `2026-04-13T19:50:07`, prompt_len 28384) containing the literal string `opening_transition.type mismatch: declared 'direct_continuation' vs normalized 'explicit_transition'` inside a `[이전 검증 경고]` block
- `projects/000_260412_a/logs/pass_rate_monitor.json` — 12 records total; **only 9 Stage3 records, all of them terminal-per-episode** (ep1 att7, ep2 att10, ep3 att6, ep4 att1 FAILED ×2, ep4 att6, ep5 att9, ep6 att10, ep7 att10). Intermediate retry attempts are not serialised per-attempt in this file
- `projects/000_260412_a/logs/artifacts/stage3/ep_0001..ep_0007/` — each episode has exactly one `attempt_NN/` directory holding only the terminal selected candidate (`final_blueprint__<strategy>.json`); intermediate rejected attempts are not persisted as artifact files

Quantitative aggregates computed over `llm_io.jsonl` (all 286 `BlueprintEnsembleGenerator` prompts):

| Metric | Count | Share of 286 |
|--------|------:|-------------:|
| Total BlueprintEnsembleGenerator prompts | 286 | 100% |
| Prompts carrying `[이전 검증 경고]` (retry feedback) | 183 | 64% |
| Prompts carrying `[Stage3 partial-fix contract]` block (fix_pack_guidance rendered) | 16 | 5.6% |
| Prompts mentioning `patch_targets` | 19 | 6.6% |
| Prompts mentioning `must_fix` | 19 | 6.6% |
| Prompts mentioning `do_not_regress` | 19 | 6.6% |
| Prompts mentioning `[Director fix_scope]` | 159 | 55.6% |
| Prompts mentioning `opening_transition` anywhere | 70 | 24.5% |
| Prompts mentioning `explicit_transition` (validator normalization vocabulary) | 64 | 22.4% |

Per-episode breakdown (approximate; episode key extracted by `현재 화는 N화` / `제N화` regex, so a small fraction of calls without the marker are unresolved):

| ep | total | retry_fb | inplace (template or fallback) | fix_pack_block | patch_targets |
|----|------:|---------:|-------------------------------:|---------------:|--------------:|
| 1  | 18 | 9  | 6  | 3  | 6 |
| 2  | 77 | 45 | 23 | 10 | 10 |
| 3  | 22 | 15 | 4  | 3  | 3 |
| 4  | 32 | 15 | 2  | 0  | 0 |
| 5  | 30 | 24 | 3  | 0  | 0 |
| 6  | 39 | 27 | 9  | 0  | 0 |
| 7  | 40 | 27 | 10 | 0  | 0 |
| 8  | 28 | 21 | 1  | 0  | 0 |

Interpretation:

- ep1–ep3 still see some inplace-with-fix_pack calls (3 + 10 + 3 = 16 prompts rendering `[Stage3 partial-fix contract]`)
- **ep4–ep8 have exactly zero prompts rendering the `[Stage3 partial-fix contract]` block, and zero prompts mentioning `patch_targets` / `must_fix` / `do_not_regress`**. Some of the flagged "inplace" calls in ep4–ep8 pass through `BLUEPRINT_PATCH_MODE_PROMPT` with an **empty** `patch_contract` JSON (the template slot rendered as `{}`), which means the LLM sees the template header but no directive content
- every ep's retry attempts DO carry `[이전 검증 경고]` (183/183 ≈ 100% of retries) — so "cold retry with no feedback at all" is not the failure mode

## Findings

### F1. The producer API has no channel for the validator-authored repair contract — the cold-retry leak is architectural, not a forgotten render call. [`leak`, `blueprint_ensemble.py:584`]

`BlueprintEnsembleGenerator.generate_ensemble(...)` at `modules/domain/agents/blueprint_ensemble.py:584` accepts `feedback`, `strategy_specific_feedback`, `rejected_strategy`, `single_strategy` — and nothing else that could carry the structured repair contract. A full-text grep over `blueprint_ensemble.py` for `fix_pack`, `patch_target`, `partial-fix`, `must_fix`, `do_not_regress`, `success_condition`, `repair_contract` returns zero hits. The runtime stores a fully normalised `prev_fix_pack` dict in `retry_state` at `three_phase_blueprint_runtime.py:2127-2129` and a fully normalised `prev_repair_contract` dict at `2130-2133`, but `_run_phase2_generation` (`three_phase_blueprint_runtime.py:1400-1433`) passes only `feedback=attempt_feedback`, `strategy_specific_feedback=strategy_feedback` into `generate_ensemble`. On every retry that routes to full regenerate (including every `binding_regenerate_only` case, which is the dominant class per §2.1 symptom), the validator-authored repair contract **does not reach the producer worker prompt at all**.

### F2. `_build_retry_strategy_feedback` ignores `prev_fix_pack` entirely. [`leak`, `three_phase_blueprint_runtime.py:1112`]

`_build_retry_strategy_feedback` (`three_phase_blueprint_runtime.py:1112-1144`) emits up to seven labelled sections: `[이전 당선 전략]`, `[이전 선택 근거]`, `[이전 REJECT 피드백]`, `[Director fix_scope]`, `[Local patch gate]`, `[이전 검증 경고]`, `[이전 점수 분해]`. None of them references `prev_fix_pack`, `prev_repair_contract`, or `prev_scope_authority`. `_build_stage3_fix_pack_guidance` — the only renderer that converts the structured fix_pack into a human-readable directive block — is called from exactly one site (`three_phase_blueprint_runtime.py:2355`, inside `_run_pass_with_fix_iteration`), which feeds `_inplace_patch_blueprint`, not the full-regenerate producer. Full-regenerate retries therefore never receive `patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, or `evidence_summary` on the prompt surface.

### F3. The `[이전 검증 경고]` block carries descriptive issue text, not a directive — the LLM sees the symptom but not the repair directive nor the allowed values. [`leak`, `three_phase_blueprint_runtime.py:2155-2174`]

`_apply_validation_reject_state` populates `retry_state.prev_validation_warnings` from `validation_result["issues"]` (up to 10 entries) as `f"{category}: {message}"` (`three_phase_blueprint_runtime.py:2167-2174`). Live sample from `llm_io.jsonl` line 490 (ts `2026-04-13T19:50:07`, 28384-char retry prompt for ep8):

```
[이전 검증 경고]
- binding_regenerate_only: Structural binding prevalidation requires regenerate-only repair: opening_transition
- opening_transition: opening_transition.type mismatch: declared 'direct_continuation' vs normalized 'explicit_transition'
- retry_plateau: pass_with_fix_unresolved; binding_prevalidation_reopen:1
```

This tells the LLM that `direct_continuation` was normalised to `explicit_transition` and that this is a mismatch. It does **not** tell the LLM:

- the finite set of allowed `opening_transition.type` values (the validator's normalization vocabulary lives in `modules/core/stage_cross_stage_contract.py`)
- why the normalisation rule rewrote the value (what heuristic fired and on what evidence)
- a positive example of the correct declaration shape
- a concrete directive like "declare `explicit_transition` with `reason=…` because the arc beat crosses scene time of day"

On the next retry cycle the LLM repeats `direct_continuation` because the warning pattern looks like a post-hoc annotation rather than a repair directive — and the LLM has no anchor to know which alternative value would have been accepted. The ep8 burn in `0_temp.txt:406-465` shows this exact repetition across three consecutive PASS_WITH_FIX → REJECT cycles.

### F4. `[이전 REJECT 피드백]` is sourced from `validation_result["feedback"]`, which is populated by Director's score commentary — not by a targeted reject directive. [`leak`, `three_phase_blueprint_runtime.py:2088,2124,2149`]

`_apply_validation_reject_state` sets `retry_state.prev_reject_feedback = validation_result.get("feedback", "validation failed")` at `three_phase_blueprint_runtime.py:2088,2124`. The live sample (`llm_io.jsonl` line 491) shows this field rendered as a Director score report — `### 세부 점수 - prose_rhythm: 5/5점 (이상적) - vocabulary_diversity: 5/5점 (우수) …` — 20+ lines of stylistic scoring, none of it pointing at the `opening_transition` binding mismatch that actually caused the reject. That section runs **before** the `[이전 검증 경고]` block, so the first reject signal the LLM parses is Director's prose scoring, not the validator's binding mismatch. The binding issue is buried under the stylistic warnings.

### F5. `[이전 선택 근거]` frequently contains a **praise sentence** for the rejected candidate. [`leak`, `three_phase_blueprint_runtime.py:2149-2154`]

`retry_state.prev_selection_reason` is assigned from `validation_result["selection_reason"] or validation_result["summary"] or validation_result["comparison_notes"] or validation_result["feedback"]` (`three_phase_blueprint_runtime.py:2149-2154`). Director's `selection_reason` is written at pick-time when Director says "I'm choosing candidate X because …", which is a praise sentence for the selected candidate — not a reject directive. ep8 console at `0_temp.txt:410` preserves this form literally:

```
사유: 대화의 텐션이 훌륭하며, 주인공의 카리스마를 보여주는 엔딩 훅이 매우 강력함.; binding prevalidation repair required
```

And `0_temp.txt:439`:

```
사유: 설득전의 경제적 논리가 가장 정교하며 인물 간의 긴장감 묘사가 우수함.
```

The retry prompt therefore ends up showing the producer LLM two competing signals on the same retry: "Director loved this candidate's dialogue tension" and "this candidate was rejected by binding prevalidation". A reasonable LLM prioritises the first and re-emits the same structural mistake.

### F6. `[Director fix_scope]` and `[Local patch gate]` sections leak routing-internal control flow into the producer prompt without adding directive content. [`waste`, `three_phase_blueprint_runtime.py:1120-1136`]

Live sample shows the producer receiving:

```
[Director fix_scope]
full

[Local patch gate]
scope=full | ready=False | reason=missing_local_contract
```

These are state-machine internals — `fix_scope` is a router decision, `local_patch_gate.reason` describes why the runtime could not build a local patch contract for the retry. Neither is actionable from the LLM's perspective. They occupy ~6 lines of retry-feedback budget and displace what could have been a concrete fix-pack directive.

### F7. `_inplace_patch_blueprint` is called from two sites with asymmetric fix_pack visibility — one embeds the human-readable guidance, the other only the raw JSON. [`leak`, `three_phase_blueprint_runtime.py:1381` vs `2375`]

Both call sites pass `normalized_fix_pack=` so the `{patch_contract}` template slot in `BLUEPRINT_PATCH_MODE_PROMPT` (`config/prompts/blueprint_generator.yaml:9-13`) is populated with JSON content in both cases. Asymmetry:

- `_run_pass_with_fix_iteration` (`three_phase_blueprint_runtime.py:2354-2357,2375-2382`): prepends `fix_pack_guidance = _build_stage3_fix_pack_guidance(effective_fix_pack)` to the free-text feedback string, so the producer sees **both** the human-readable `[Stage3 partial-fix contract]` block (inside `{feedback_text}`) **and** the raw `## Patch Contract` JSON
- `_run_phase2_generation` inplace branch (`three_phase_blueprint_runtime.py:1381-1388`): passes `director_feedback=retry_state.prev_reject_feedback` directly without prepending fix_pack_guidance. The producer sees the raw `## Patch Contract` JSON but not the human-readable directive block

This is a minor but real leak: the secondary inplace retry path is worse-instrumented than the primary one inside the same retry cycle. Because JSON-only contract tends to be parsed less reliably by small-model generators, the 16 prompts rendering the human-readable block should probably be all ~19 `patch_targets`-bearing prompts — the 3 prompts delta is the measurable asymmetry.

### F8. The inplace route can fire with an **empty** `patch_contract` — the template header is rendered but the contract dict is `{}`. [`waste`, `three_phase_blueprint_generator.py:204-239`]

`_inplace_patch_blueprint` (`three_phase_blueprint_generator.py:159,204-239`) does not guard against an empty `normalized_fix_pack`. If `repair_material.effective_fix_pack` is `{}`, `patch_contract_json = json.dumps({} , ...)` renders as `{}`, the template still embeds `## Patch Contract\n{}`, and the LLM sees the patch-mode scaffolding with no directive. Aggregate counts show ep4 (2), ep5 (3), ep6 (9), ep7 (10), ep8 (1) — approximately 25 such degenerate inplace calls in the live session. These calls consume an LLM turn but transmit no repair content; they are effectively "cold patch mode" — the producer re-reads its own prior blueprint, the free-text feedback, and is asked to "fix what Director pointed at" with nothing else.

### F9. `constraint_block` is cached and re-used across every retry of a single episode, so the retry-time delta is almost entirely `_build_retry_strategy_feedback` output. [`observation`, `three_phase_blueprint_runtime.py:1160-1191`]

`_resolve_constraint_block` (`three_phase_blueprint_runtime.py:1160-1166`) re-uses `retry_state.cached_constraint_block` on `retry > 0`. Combined with the fact that `generate_ensemble` produces prompts averaging 18,311 chars (max 28,994 chars; computed over all 286 BP prompts in `llm_io.jsonl`), the retry-time delta between attempts N and N+1 is a ~1-3KB strategy_feedback block attached to a ~17KB static base. From the LLM's perspective, attempts N and N+1 are almost the same prompt, and the strategy_feedback block at the top has the structural problems listed in F3–F6. This is not itself a leak — it is a visibility constraint the leak above rides on: if the strategy_feedback block is weak, the retry is weak.

### F10. Visibility gap — per-attempt intermediate artifacts are not serialised. [`gap`, `projects/000_260412_a/logs/artifacts/stage3/ep_0001..ep_0007/`]

Each episode directory under `projects/000_260412_a/logs/artifacts/stage3/` contains exactly one `attempt_NN/` subdirectory, matching only the terminal successful (or terminally FAILED) attempt for that episode. Intermediate rejected candidate artifacts are not persisted. Consequence: the payload the producer produced at attempt N (rejected) cannot be read from disk to correlate with the payload produced at attempt N+1. The only canonical source for per-attempt retry-payload reconstruction is `llm_io.jsonl`, and the only canonical source for reject-reason per intermediate attempt is `0_temp.txt` console capture. `pass_rate_monitor.json` records 9 Stage3 terminal rows only; intermediate per-attempt pass/fail information is absent from this file. **Cold-retry detection across intermediate attempts therefore has to ride on `llm_io.jsonl` exclusively** — T2 has used that path.

### F11. Retry path categorisation for ep1–ep7 (aggregates over all 286 BlueprintEnsembleGenerator calls in `llm_io.jsonl`). [`observation`]

Using the order's three bins:

- `local patch (contract-ready, patch-IR eligible)` — defined as a prompt that renders `[Stage3 partial-fix contract]` (Route A of F7): **16 prompts**, concentrated in ep1 (3), ep2 (10), ep3 (3); ep4–ep8 = 0
- `full regenerate with feedback` — defined as a prompt that carries `[이전 검증 경고]` without the `[Stage3 partial-fix contract]` block and without the inplace template headers: ≈ **164 prompts** across ep1–ep8 (ep1 6, ep2 35, ep3 12, ep4 15, ep5 21, ep6 18, ep7 17, ep8 20; rounded to the per-ep `retry_fb - fix_pack_block` delta with inplace-only promptage subtracted)
- `full regenerate without feedback (cold restart)` — defined as a prompt with neither retry feedback nor inplace template headers: ≈ **45 prompts** spread across ep1–ep8 as first-attempt calls (ep1 3, ep2 9, ep3 3, ep4 15, ep5 3, ep6 3, ep7 3, ep8 6). The ep4 value (15) is an outlier tied to the two early failed runs recorded as `att1 FAILED` in `pass_rate_monitor.json`; those two bursts included re-initialised cycles that re-attempted the ep from cold. All of the cold-restart bucket maps to **first-attempt calls** — i.e., the new-episode retry index 0 where there is no prior reject to carry; none of them is a "cold retry that lost prior feedback mid-episode"

The cold-restart-mid-episode leak (the "retry attempt that dropped feedback vocabulary") count is **0**. The leak family this audit reports is not "lost feedback at attempt boundaries"; it is "present feedback is the wrong shape" (F1–F6) plus "structured contract not in the producer API" (F1).

### F12. When `pass_with_fix` inner loop exhausts 3 inplace patches, control returns to the outer retry loop with `reject_origin=pass_with_fix_unresolved`, and the next `generate_ensemble` call runs without the previously-consumed fix_pack. [`leak`, `three_phase_blueprint_runtime.py:2609-2699` → `1400-1433`]

`_finalize_pass_with_fix_failure` (`three_phase_blueprint_runtime.py:2609-2699`) calls `_apply_validation_reject_state` (line 2682-2688) to re-populate `retry_state` from `current_validation`, then returns `_ThreePhasePassWithFixResult(should_continue=True)` at line 2699. The outer retry loop then fires a new Phase 2 cycle via `_run_retry_cycle` → `_run_phase2_generation` (`three_phase_blueprint_runtime.py:1298-1479`). `repair_material` is rebuilt from `retry_state` on entry (`build_retry_material` at line 1323), so the fix_pack is technically "still known" internally. But because the binding-regenerate-only path forces `should_break_to_generate=True` and forbids `use_inplace_patch`, control takes the `generate_ensemble` branch — the architectural cold-retry leak from F1. The LLM spends three inplace patch turns converging on a binding mismatch, then the orchestrator burns a full `generate_ensemble` fan-out of 5 candidates on a prompt that never sees the fix_pack. This is the ep8 console pattern at `0_temp.txt:406-466`: three consecutive `PASS_WITH_FIX unresolved after 3 patch attempts -> REJECT` blocks followed by `[Phase 2] 후보 생성 (full_ensemble)` and the same binding mismatch reappearing.

## Cross-Terminal Pointers

- The validator's `opening_transition` normalization rules live in `modules/core/stage_cross_stage_contract.py:205,267,296` and `modules/domain/agents/unified_blueprint_validator.py:2020` — whether those rules are correctly calibrated is the T5 question, not T2's
- Whether `config/prompts/ensemble.yaml` teaches the allowed `opening_transition.type` vocabulary and positive examples in a learnable way (which would at least prevent the LLM from guessing `direct_continuation` on retry 0) is the T1 question
- Whether the base context packet (Stage2 arc, prior blueprint, bible, work guard) is starving the producer of the grounding it needs to pick the right transition type in the first place is the T3 question
- The asymmetric Director praise-vs-validator-reject observation in F5 — Director's `selection_reason` leaking into retry feedback as a praise sentence alongside a binding reject — is a rubric-overlap symptom relevant to T7 (Director vs Validator authority overlap); T2 stops at the observation and flags the pointer
- Stage4 chief_writer has its own retry feedback paths (`chief_writer.py:117`, `1330`, `1506`, `1945`, `2232`, `2382`, plus `chief_writer_inplace_local_ops.py:126-139` which **does** embed `[fix_pack]\n{fix_pack_guidance}` into the writer's inplace prompt — an interesting contrast to Stage3's Route B asymmetry in F7). Per parent §6 T2 Scope OUT, T2 does not audit those paths; they belong to T10

## Hypothesis Candidates For Synthesis

Explicitly labelled as candidates, not directives. Each carries file:line anchor.

### H1. Add a `fix_pack` / `repair_contract` channel to the producer API so retry payloads can carry structured directives.

`BlueprintEnsembleGenerator.generate_ensemble` signature at `blueprint_ensemble.py:584` would accept an optional `fix_pack: dict` (and/or `repair_contract: dict`) argument, and the workers at `blueprint_ensemble.py:403-465` would render `_build_stage3_fix_pack_guidance(fix_pack)` alongside the existing strategy feedback when present. `_run_phase2_generation` at `three_phase_blueprint_runtime.py:1401-1415` would forward `fix_pack=repair_material.effective_fix_pack` / `repair_contract=repair_material.repair_contract` into `ensemble_kwargs`. This is the architectural closure of F1.

### H2. Replace descriptive `[이전 검증 경고]` lines with a rewrite directive that names the allowed vocabulary and a concrete positive example.

`_apply_validation_reject_state` at `three_phase_blueprint_runtime.py:2167-2174` currently stores `f"{category}: {message}"` lines. A directive-shaped line would add, for each known validator-normalization family (`opening_transition`, `protagonist_state`, `tactical_semantic_fidelity`, `scenario_density`), an `allowed_values=[...]` + `example=…` suffix populated from the contract module. Anchoring file: `modules/core/stage_cross_stage_contract.py` holds the normalization vocabulary; `_build_retry_strategy_feedback` at `three_phase_blueprint_runtime.py:1137-1140` is where the rewrite would be rendered. This targets F3.

### H3. Stop sourcing `prev_reject_feedback` from `validation_result["feedback"]` when a binding reject is active; source it from `validation_result["issues"]` + `binding_regenerate_only_reason` only.

`three_phase_blueprint_runtime.py:2088,2124` assigns `feedback = validation_result.get("feedback", "validation failed")`. When `reject_origin` is `pass_with_fix_unresolved` or `binding_prevalidation_reopen`, the Director-written stylistic score commentary should not be the leading reject text — the binding issue list and the `binding_regenerate_only_reason` should be. This targets F4.

### H4. Drop `prev_selection_reason` from the retry feedback when it is Director praise.

`three_phase_blueprint_runtime.py:1116-1117` unconditionally emits `[이전 선택 근거]\n{prev_selection_reason}`. When the selection_reason sentence is a praise-for-selected-candidate string (the current behaviour for every PASS-with-binding-reject case), this praise line competes with the reject signal inside the same retry prompt. A simple filter — "only emit `[이전 선택 근거]` when the candidate was not rejected by binding prevalidation" — would cut F5. Alternative: relabel it as `[Director 선정 코멘트]` so the LLM parses it as context, not as reject feedback.

### H5. Drop `[Director fix_scope]` and `[Local patch gate]` from the producer-facing prompt; keep them in operator telemetry only.

`three_phase_blueprint_runtime.py:1120-1136` emits both sections. F6 shows they are routing-internal and not actionable. Removing them from `_build_retry_strategy_feedback` and keeping them only in `_log_operator_retry_context` telemetry would reclaim ~6 lines of prompt budget for H1 / H2 content.

### H6. Symmetrise the two `_inplace_patch_blueprint` call sites so both prepend `_build_stage3_fix_pack_guidance` to `director_feedback`.

`three_phase_blueprint_runtime.py:1381-1388` passes `director_feedback=retry_state.prev_reject_feedback`; the pass_with_fix variant at `three_phase_blueprint_runtime.py:2354-2357` prepends `fix_pack_guidance`. Changing the Phase 2 retry site to match the pass_with_fix site is a one-line delta and targets F7.

### H7. Gate the inplace patch route on a non-empty `effective_fix_pack`.

`_inplace_patch_blueprint` (`three_phase_blueprint_generator.py:204`) does not short-circuit when `normalized_fix_pack` is `{}`. The 25+ empty-contract inplace calls in ep4–ep8 burn LLM turns with no directive content. A guard at `three_phase_blueprint_generator.py:204` — "if contract is empty, return None so the caller falls back to full regenerate with H1-grade feedback" — would delete the F8 waste class.

## 3-Pass Audit Record

### Pass 1 — structure and scope

- confirmed T2 scope is retry-time feedback fidelity only; Stage4 chief_writer paths explicitly excluded per parent §6 T2 Scope OUT
- confirmed all findings reference file:line anchors on `three_phase_blueprint_runtime.py`, `three_phase_blueprint_generator.py`, `blueprint_ensemble.py`, `config/prompts/blueprint_generator.yaml`, `0_temp.txt`, `projects/000_260412_a/logs/session/llm_io.jsonl`, `pass_rate_monitor.json`
- no T5/T7/T1/T3 claims sneaked into findings — cross-terminal pointers emit only when an observation belongs to another terminal
- no retuning / rewrite directives — all candidates are filed under `Hypothesis Candidates For Synthesis`

### Pass 2 — evidence and consistency

- re-anchored `git rev-parse HEAD` at spawn and at final — both return `32d6f0c8b56898fd8a370ae13684043d4cfda91a`, no drift
- verified line anchors by direct Read calls (`three_phase_blueprint_runtime.py:1`–`3140`, `three_phase_blueprint_generator.py:140-289`, `blueprint_ensemble.py:380-665`). All cited anchors resolved on current head
- verified the aggregate `286 / 183 / 16 / 19 / 19 / 19 / 159 / 70 / 64` counts by a single pass over `projects/000_260412_a/logs/session/llm_io.jsonl` (513 lines) filtered on `agent == "BlueprintEnsembleGenerator"`
- verified the ep8 reject cycle quote at `0_temp.txt:400-469` renders literally as described in findings F3–F5 — the praise sentence `대화의 텐션이 훌륭하며, 주인공의 카리스마를 보여주는 엔딩 훅이 매우 강력함.` is adjacent to `binding prevalidation repair required` in the same `사유:` line (`0_temp.txt:410`)
- verified `blueprint_ensemble.py` has zero mentions of `fix_pack | partial-fix | patch_target | must_fix | do_not_regress | success_condition | repair_contract` — the architectural-leak claim in F1 is based on a full-file grep, not a partial scan
- verified that 183 / 183 retries carry `[이전 검증 경고]` — the "cold restart mid-episode" bucket is 0 in F11
- verified `pass_rate_monitor.json` has 9 Stage3 records, all terminal (attempt 1, 6, 7, 9, 10); it does not contain per-attempt intermediate rows — F10 visibility gap confirmed
- verified only 1 artifact directory per episode under `projects/000_260412_a/logs/artifacts/stage3/ep_000N/` — F10 confirmed
- corrected a draft over-reach: originally wrote "cold-retry leaks count ≥ 15" based on ep4 cold_first=15 in the per-ep table. After re-inspection, those 15 ep4 cold-first calls are tied to two `att1 FAILED` bursts recorded in `pass_rate_monitor.json` — which are new-episode initial calls, not mid-episode lost-feedback retries. Findings revised to report "cold-restart mid-episode = 0" in F11
- double-checked that `chief_writer_inplace_local_ops.py:139` is cited only as a cross-terminal pointer (T10), not as a T2 finding

### Pass 3 — execution and readability

- purpose statement quotes the order §6 T2 verbatim
- evidence anchors subdivide code / live-run / aggregates for operator readability
- findings are numbered F1–F12 and each has a severity tag (`leak` / `waste` / `gap` / `observation`) matching the parent deliverable template
- cross-terminal pointers are each tied to a specific sibling terminal
- hypothesis candidates H1–H7 are each anchored to a file:line where a change would land, but explicitly labelled as candidates for synthesis — not implementation directives
- confidence computed after the two revisions above; no residual open questions above the 95% floor except the visibility gap in F10 which is flagged as a structural constraint

## Final Confidence

`96%`.

Residual uncertainty (4 points):

1. Per-episode retry path category counts in F11 use a regex episode extractor over `llm_io.jsonl` prompts (`현재 화는 N화` / `제N화`). A small fraction of producer calls (~0 at spot-check) without these markers would sit under the `unknown` key; the aggregate values are rounded because of this
2. The 25+ "empty patch_contract inplace" count in F8 is inferred from the delta between `is_inplace` and `patch_targets` per ep. A precise count would require reading each inplace prompt's rendered template — this is survey-only and that precision is not required for T2's gap claim
3. The asymmetric praise-sentence selection_reason leak in F5 is grounded on two ep8 console lines plus one live llm_io sample. A third independent sample would raise confidence but is not required to establish the existence of the leak (the selection_reason data-flow path is explicitly traced in code at `three_phase_blueprint_runtime.py:2149-2154` and emit site `1116-1117`)
4. F12's claim that "fix_pack is technically still in retry_state but the code takes the generate_ensemble branch anyway" is a code-flow inference, not a per-attempt log trace. The conclusion is solid (generate_ensemble has no fix_pack parameter, so taking the branch discards the fix_pack regardless of retry_state contents) but an ep-level audit log capturing "we had fix_pack X at retry entry, we called generate_ensemble without it" does not exist in the current telemetry — that is itself a telemetry gap
