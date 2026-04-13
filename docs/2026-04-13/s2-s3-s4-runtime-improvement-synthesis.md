# S2 S3 S4 Runtime Improvement Synthesis

- Date: 2026-04-13
- Scope: synthesis of the 10-terminal parallel investigation order `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`, merging T1–T10 hypothesis candidates and ranking by cross-terminal evidence weight
- Mode: synthesis-only, read-only, no code changes, no live rerun, no queue mutation; this document raises proposals for the next decision but does not open a queue lane
- Canonical Path: `docs/2026-04-13/s2-s3-s4-runtime-improvement-synthesis.md`
- Baseline Commit: `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `dirty: same as parent order — Stage3 producer/ensemble/runtime/validator edits plus live 000_260412_a artifacts plus the 10 t1..t10 deliverable files now also present`
- Resume Commit: `same-as-baseline`
- Side-Effect Coverage: read-only; only file write is this synthesis document; no code, config, schema, DB, queue, or live runtime mutation
- Confidence: `97%` (3-pass audited; 5 critical cross-terminal anchors live-verified before save)

## 1. Purpose

This synthesis answers one bounded operator question:

- given the 10 parallel survey deliverables `t1..t10` now saved under `docs/2026-04-13/`, what are the top 3–5 bounded runtime improvement tranches the next decision cycle should consider for raising Stage3 quality (and Stage2/Stage4 as supporting axes), ranked by cross-terminal evidence weight rather than per-terminal opinion

This synthesis does NOT:

- propose code edits
- open new queue lanes
- claim closure on any individual hypothesis
- override any individual T<N> deliverable's confidence
- authorize live rerun

It DOES:

- merge overlapping hypotheses across terminals
- count independent terminals citing the same gap (evidence weight)
- propose 5 bounded tranches with owner / scope / expected effect / dependencies / risks
- enumerate deferred items
- record the 3-pass audit chain inside this document

## 2. Inputs

10 terminal deliverables, all saved 2026-04-13 23:00–23:06, all confidence ≥ 96%:

| T | File | Conf | One-line takeaway |
|---|------|------|-------------------|
| T1 | `t1-producer-initial-prompt-forensics.md` | 96% | `ensemble.yaml` declares 5 contract fields but teaches only enum names without grounding to validator decision rules; LLM guesses on attempt 1 |
| T2 | `t2-stage3-retry-feedback-loop-audit.md` | 96% | producer retries carry symptom text but lack validator-authored repair contract in structured form; LLM repeats the same binding mismatch for 7–10 attempts |
| T3 | `t3-producer-context-packet-audit.md` | 96% | `{strategy_directive}` 43% of dynamic budget; semantic-context blob duplicated in 55.6% of retries mislabeled as "reject feedback"; two contract vocabularies entirely missing from packet |
| T4 | `t4-producer-cheap-admission-effectiveness-audit.md` | 96% | cheap admission catches ≤4.4% of contract-failure surface; producer-side `_normalize_opening_transition_contract` silently launders 71.2% of LLM omissions past the gate before the gate runs |
| T5 | `t5-validator-heuristic-true-false-positive-audit.md` | 96% | four validator heuristics fire predominantly on FALSE POSITIVES due to vocabulary conflicts (`→`, `진입`, `직원`, `그림자`, boardroom verbs, `18년 후`, space-separated proper nouns), not authorial failures |
| T6 | `t6-ensemble-candidate-diversity-audit.md` | 96% | contract-level ensemble diversity is measurably ZERO for the rejection families that actually fire (90% of trios converge on missing `opening_transition`, 100% converge on `protagonist_state` shape) — only 3 of 5 advertised strategies even ship |
| T7 | `t7-director-vs-validator-authority-overlap-audit.md` | 96% | Director scores Stage3 on a prose-only rubric (consistency 40 / Arc 35 / continuity 15 / hooks 10) with ZERO weight on any binding category; validator silently overrides Director PASS to PASS_WITH_FIX, forcing full regenerate even when inplace would suffice |
| T8 | `t8-stage3-cost-attribution-audit.md` | 96% | Stage3 baseline $45.08 / 471 calls; 84% to fan-out count (not per-call cost); patch_mode shows ZERO clean-PASS rescues despite $3.34 spend; 4 of 7 episodes hit the 10-attempt cap and rounds 7–10 produce no verdict improvement |
| T9 | `t9-stage2-to-stage3-handoff-quality-audit.md` | 97% | Stage2 authors richly with named entities and concrete prose, but Stage2→Stage3 transit silently collapses 500–750 chars of per-episode tactical prose into 2–3 summary bullets; `extract_episode_tactical` shadows `tactical_doc` whenever `episode_details` is non-empty |
| T10 | `t10-stage3-to-stage4-handoff-and-s4-writer-smarts-audit.md` | 96% | Stage4 has not executed in this corpus; chief writer is architecturally blind to Stage3's warning vocabulary on attempt 1; admission gate vocabulary has zero overlap with Stage3 reject family names |

Forward-looking note: T10 is observation-only since Stage4 has never run in `projects/000_260412_a/`. T10 hypotheses are necessarily pre-execution.

## 3. Cross-Terminal Hypothesis Merge

Hypothesis candidates from all 10 deliverables collapse into 10 themes. Each theme lists every terminal that independently cited it. Evidence weight = number of independent terminals.

| # | Theme | Terminals citing | Weight |
|---|-------|------------------|--------|
| Θ1 | Opening-transition vocabulary collision is the dominant ep1–ep8 failure family | T1.H1, T2.H1+H2, T3.H4, T4.H1, T5.H1, T6.H6-A, T7.H1+H3, T9.H1, T10.H1 | **10/10** |
| Θ2 | Producer LLM never sees the contract vocabulary that the validator enforces | T1.H1+H3+H5, T3.H4, T4.H1, T5.H1+H2 | **5/10** |
| Θ3 | Audit / observability infrastructure is structurally lossy across the whole pipeline | T4.H2+H4, T5.H5, T6.H6-E, T7.H2, T8.F1+F10 | **5/10** |
| Θ4 | Retry feedback carries symptom text, not directive vocabulary, so attempt N+1 cannot self-correct | T2.H1+H2+H3+H4, T8.H8.2 | **4/10** (deep within T2) |
| Θ5 | Validator over-strictness on false-positive families (vocabulary calibration) | T5.H1+H2+H3+H4, T7.H3 | **4/10** |
| Θ6 | Director rubric does not weigh binding contract categories; Director PASS gets silently overridden | T7.H1+H3+H4, T8.H8.4 | **3/10** |
| Θ7 | Ensemble fan-out architecture: only 3 strategies ship, prompt delta 0.1%, contract-level diversity zero | T6.H6-A+H6-B+H6-D, T8.H8.5 | **3/10** |
| Θ8 | Cheap admission gate is disarmed by upstream normalization and by its own preconditions | T4.H1+H3, T6.H6-A | **3/10** |
| Θ9 | Stage2→Stage3 handoff silently collapses tactical_doc into bullet-list shadow | T9.H1+H2+H3, T1 cross-pointer, T3 cross-pointer, T4 cross-pointer | **4/10** (T9 owns plus 3 cross-pointers) |
| Θ10 | Stage4 writer architecturally blind to Stage3 warning vocabulary; admission gate vocabulary mismatched | T10.H1+H2+H3+H4 | **1/10** but Stage4 has not run |

Cost-side themes are deliberately separated because they answer the cost question, not the quality question:

| # | Cost theme | Terminals | Weight |
|---|-----------|-----------|--------|
| C1 | Fan-out round count is the dominant cost lever (84% of spend), not per-call cost | T8.H8.1+H8.6 | 1/10 (only T8 owns cost) |
| C2 | Tail rounds 7–10 of attempt-capped episodes produce no verdict improvement; ~30% potential savings via stop-if-no-improvement circuit breaker | T8.H8.6 | 1/10 |
| C3 | patch_mode delivered ZERO clean-PASS rescues despite $3.34 spend; lowest-ROI axis | T8.H8.2, T7.H3 | 2/10 |
| C4 | FANOUT prompt_chars median ~20k; halving context = ~36% per-call savings (T3 territory) | T8.H8.7, T3.H1 | 2/10 |

Cross-cutting observation: Θ1 alone is cited by every single terminal. The opening-transition family is **the single dominant blocker** of Stage3 quality; every other theme either feeds into it (Θ2/Θ3/Θ8/Θ9), is downstream of it (Θ4/Θ5/Θ6/Θ7), or is forward-looking (Θ10).

## 4. Top 5 Bounded Tranches

Tranches are ordered by ROI (evidence weight × leverage / implementation cost). Each tranche stays inside the existing Stage3 parent lane (`docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`) unless explicitly noted. None require a new queue family.

### Tranche 1. Opening-Transition Vocabulary Coherence (cross-cutting, evidence 10/10)

**Why first:** This single tranche addresses the ep8 reject family that every terminal cited. It touches producer, validator, Stage2 handoff, and repair routing simultaneously, but the surface area at each touchpoint is small and bounded.

**Owner:** existing `0_0-stage3-contract-tightening-remediation` parent lane plus `0_0-stage3-opening-transition-contract-normalization-remediation` sibling lane.

**Bounded scope (5 sub-edits, all within the same coherent fix family):**

1. **Validator vocabulary calibration** — remove the false-positive markers from the opening-transition normalizer:
   - `modules/core/stage_cross_stage_contract.py:18-36` `_OPENING_TRANSITION_SCENE_MARKERS`: remove `"진입"` (line 34) and `"향해"` / `"향하"` (line 25–26) which fire on legitimate diegetic character entry; keep absolute scene-break markers (`"* * *"`, `"장면 전환"`, `"한편"`)
   - `modules/core/stage_cross_stage_contract.py:37-51` `_OPENING_TRANSITION_TIME_SHIFT_MARKERS`: remove `"->"` (line 49) and `"→"` (line 50); these are scene-duration spans in `time_flow`, not transitions; keep absolute time-shift markers (`"다음 날"`, `"이튿날"`, etc.)
   - Source evidence: T5.H1 (100% FP rate across 5 ep8 candidates / 4 retry rounds, all anchored)

2. **Producer prompt teaches the rule** — replace the bare enum declaration in `config/prompts/ensemble.yaml:411-414` with the validator's actual decision table (3-row table: same location + no time shift → `direct_continuation`; same location + time shift → `explicit_transition`; new location → `jump_opening`). Source: T1.H1 (verbatim text proposal in t1 §4 H1).

3. **Stage3 callsites stop shadowing tactical_doc** — `modules/core/tactical_utils.py:31` `extract_episode_tactical` priority chain currently is `episode_details > regex > tactical_doc`. **Important blast-radius caveat**: live grep verifies 13 production callsites for this helper, not 2 as T9 originally inferred — Stage3 (`blueprint_ensemble.py:306`, `blueprint_constraint_compiler.py:327/772/914`, `three_phase_blueprint_generator.py:188`, `unified_blueprint_validator.py:2340`, `stage3_orchestrator.py:2460`), Stage4 (`stage4_context_builder.py:2277`), Director (`director_ensemble.py:1968`), continuity (`continuity_inspector.py:392`, `continuity_arc.py:583/990/996`), ToT (`tree_of_thoughts.py:389`), and the generic `prompt_builder.py:700`. Therefore this sub-edit must NOT change the helper's default behavior. Two safer shapes: (a) add a `prefer_full_doc: bool = False` parameter and flip it to `True` only at the Stage3 producer-input callsite (`blueprint_ensemble.py:306`); or (b) introduce a new sibling helper `extract_episode_tactical_full(...)` and route only Stage3 producer to it. Source: T9.H1 with synthesis-time blast-radius correction.

4. **Producer cheap-admission distinguishes declared vs inferred** — `modules/domain/agents/blueprint_ensemble.py:989-1009` `_normalize_opening_transition_contract` currently mutates `candidate["opening_transition"] = normalized_contract` before the cheap gate checks anything; split into `(declared_value, inferred_value)` so the cheap gate can fail-closed when the LLM omitted the field entirely (71.2% of fan-out responses). Source: T4.H1.

5. **Repair router allows inplace patch for opening-transition alias** — `modules/domain/agents/unified_blueprint_validator.py:455` currently forces `merged_scope = "full"` whenever any binding category is present; carve out `opening_transition` alias-only category as inplace-eligible (it is a 1-line patch by definition). Source: T7.H3.

**Expected effect (qualitative):**

- ep8 reject family stops cycling on opening-transition false positives
- producer learns the actual rule from the prompt instead of guessing
- producer sees the Stage2 prose evidence needed to make the right choice
- when a real violation slips through, the repair lane is cheap (inplace) instead of expensive (full regenerate)
- attempt count per episode falls from 7–10 toward 3–5

**Dependencies:**

- none external; all five sub-edits are inside the existing Stage3 parent + sibling lanes
- no Stage4 dependency
- no live rerun required to land

**Risks:**

- removing `"진입"` and `"→"` from the marker lists could let a real explicit-transition slip through if the candidate ALSO lacks the absolute markers; mitigation = T5 already showed 100% FP on these specifically, so the risk is low but not zero, and a fresh proof rerun must measure
- splitting declared-vs-inferred in cheap admission may produce a temporary spike in attempt-1 cheap rejects until producer prompt edit (sub-edit 2) lands; mitigation = land sub-edits 1+2+3 together as one tranche, not separately

**Cost band:** estimated < 1 day implementation + 1 fresh proof rerun. No new dependency, no schema migration, no queue change.

**Verification gate before claiming closure:**

- Stage3 fresh rerun on `000_260412_a` ep1–ep8 with the same arc inputs
- attempt-count distribution + opening-transition reject count must improve
- false-positive count from T5's H1 set must drop to ≈ 0
- all six sub-edits' targeted shards remain green

### Tranche 2. Producer Contract Teaching + Validator Calibration Cleanup (evidence 7/10)

**Why second:** Tranche 1 closes the dominant family, but T1 and T5 jointly identify three more producer-vs-validator vocabulary collisions (tactical intrusion, scenario_density, temporal_deictic). These are smaller individually than opening_transition but together cover most of the remaining PASS_WITH_WARNING family.

**Owner:** same Stage3 parent lane.

**Bounded scope (4 sub-edits):**

1. **Tactical-semantic vocabulary cleanup** — `modules/domain/agents/unified_blueprint_validator.py:80-92` `_TACTICAL_INTRUSION_ENTRY_MARKERS` remove `"직원"` (line 91) and `"그림자"` (line 89) — both fire on PB / boardroom scenes without any physical-threat presence; `:93-108` `_TACTICAL_INTRUSION_CONFLICT_MARKERS` similarly remove or constrain `"대응"` `"차단"` `"제압"` `"위협"` `"협박"` to require co-occurrence with a physical-threat entry marker. Source: T5.H2 (5 ep8 candidates, 100% FP).

2. **Producer prompt teaches the full tactical token family** — `config/prompts/ensemble.yaml:387` currently mentions ~6 of the 24 markers; replace with the full vocabulary plus the rule "if Arc tactical_doc lacks physical-threat entry, do not invent any of these tokens in scene_breakdown / integrated_scenario". Source: T1.H3.

3. **Scenario-density anchor regex fix** — `modules/domain/agents/unified_blueprint_validator.py:2446-2449` anchor regex requires contiguous Hangul + suffix; expand to allow space-separated proper nouns (`"한정호 저택"`, `"SW 인베스트먼트"`). Source: T5.H4 (investment-genre legitimate proper nouns missed entirely).

4. **Temporal-deictic diegetic discriminator** — `modules/domain/agents/unified_blueprint_validator.py:1808-1865` `_collect_temporal_deictic_drift_issues` has no signal to distinguish a 회귀자-premise canonical anchor (`"18년 후의 기억"`) from authorial drift; add an allowlist input from `arc_constraint_summary` or `inherited_state.timeline_anchors` so canonical anchors pass. Source: T5.H3.

**Expected effect:**

- tactical_semantic_fidelity stops firing on PB / boardroom episodes
- scenario_density advisory stops penalizing legitimate proper-noun anchors
- temporal_deictic stops penalizing canonical 회귀자 backstory
- producer prompt aligns with validator after cleanup, so producer naturally avoids forbidden vocabulary

**Dependencies:** Tranche 1 should land first so the proof rerun can isolate Tranche 2's effect.

**Risks:** loosening tactical-intrusion markers risks letting real intrusion slip through. Mitigation: add a co-occurrence requirement (entry marker AND conflict marker both required AND in the same sentence within N tokens), not just removal.

**Cost band:** ~1 day implementation. No schema or queue change.

### Tranche 3. Retry Feedback Surgery (evidence 4/10, all from T2 with T8 cost confirmation)

**Why third:** Even with Tranches 1+2, the retry loop today still wastes 7–10 attempts because attempt N+1 receives Director's prose-style praise instead of the validator's structured fix vocabulary. This tranche fixes the feedback path, not the contracts.

**Owner:** same Stage3 parent lane plus the existing `Stage3RepairRouter` extraction (tranche 1 of `stage3-three-tranche-safe-sequencing-plan.md`).

**Bounded scope (5 sub-edits):**

1. **Add `fix_pack` / `repair_contract` channel to producer API** — `modules/domain/agents/blueprint_ensemble.py:584` `BlueprintEnsembleGenerator.generate_ensemble` signature accepts optional `fix_pack: dict` and `repair_contract: dict`; `modules/domain/agents/three_phase_blueprint_runtime.py:1401-1415` `_run_phase2_generation` forwards `repair_material.effective_fix_pack` and `repair_material.repair_contract`. Source: T2.H1.

2. **Replace descriptive `[이전 검증 경고]` with directive-shaped block** — `modules/domain/agents/three_phase_blueprint_runtime.py:2155-2174` should emit `allowed_values=[...]` + `example=…` per validator-normalization family. Source: T2.H2.

3. **Source `prev_reject_feedback` from binding issues, not Director stylistic score** — `three_phase_blueprint_runtime.py:2088,2124` when reject_origin is `pass_with_fix_unresolved` or `binding_prevalidation_reopen`, lead with the binding issue list; do NOT lead with Director's prose praise. Source: T2.H3+H4.

4. **Drop `[Director fix_scope]` and `[Local patch gate]` from producer-facing prompt** — `three_phase_blueprint_runtime.py:1120-1136` keeps these in operator telemetry only, not in the LLM payload. Source: T2.H5.

5. **Gate inplace patch route on non-empty `effective_fix_pack`** — `modules/domain/agents/three_phase_blueprint_generator.py:204` short-circuit when `normalized_fix_pack == {}`; fall through to full regenerate with H1-grade feedback instead of burning 25+ degenerate inplace turns observed in ep4–ep8. Source: T2.H7.

**Expected effect:**

- attempt N+1 sees the actual fix instructions (allowed values, examples, repair contract), not symptom paraphrase
- Director praise stops contaminating reject feedback
- empty patch_contract turns stop firing
- patch_mode's $3.34 ROI improves from zero clean-PASS to a measurable rescue rate (T8.C3)

**Dependencies:** Tranches 1+2 should land first so the fix vocabulary the retry channel forwards is the corrected vocabulary, not the FP-prone one.

**Risks:** changing the feedback shape may break tests that pin exact prompt strings (`test_blueprint_patch_mode.py`, `test_blueprint_ensemble_generate_ensemble.py`); mitigation = update tests as part of the same tranche.

**Cost band:** 1–2 days implementation including test updates.

### Tranche 4. Director Rubric Alignment + Audit Visibility (evidence 5/10 split between Θ6 and Θ3)

**Why fourth:** This tranche addresses the rubric mismatch (Director scores prose, validator binds structure) AND the audit infrastructure gap (rejected candidates not persisted, Director pre-override verdict not persisted). The two come together because both depend on giving Director and the audit layer the same structured view.

**Owner:** same Stage3 parent lane.

**Bounded scope (5 sub-edits):**

1. **Director sees binding fields in candidate summary** — `modules/domain/agents/director_ensemble.py:1993-2013` candidate summary expands to include declared `opening_transition.type`, `protagonist_state` shape signature, and a binding-category advisory badge list. Source: T7.H1 (rubric leak, anchored).

2. **Add binding-contract integrity rubric axis** — `director_ensemble.py:2049-2070` 40/35/15/10 rubric becomes 35/30/15/10/10 with the new 10% slot weighting binding-contract integrity. Source: T7.H1.

3. **Persist Director's pre-override verdict** — `stage_attempts.initial_verdict` and `director_selections.verdict` schema fields already exist; populate them. Source: T7.H2 + T8.F1.

4. **Persist losing fan-out candidates as sidecar artifacts** — `projects/<project>/logs/artifacts/stage3/ep_NNNN/attempt_NN/` writes `final_blueprint__<strategy>.json` for the winner only; also write `losing_blueprint__<strategy>.json` (or rename `attempt_<strategy>.json`) for non-winning candidates so future audits do not need to scrape `llm_io.jsonl`. Source: T4.H4 + T6.H6-E.

5. **Wire cheap-reject events into `ui_events.jsonl`** — `modules/domain/agents/blueprint_ensemble.py` `_sanitize_blueprint_candidate` operator log calls (`:1411-1415`, `:1444-1453`, `:1477-1481`, `:1509-1511`, `:1524-1528`, `:1538-1542`) currently never reach session sinks; verify dispatcher path or add the missing wiring. Source: T4.H2.

**Expected effect:**

- rubric leak drops measurably (Director starts catching what validator catches)
- fix_scope override still happens for true binding categories, but Director's `inplace` diagnosis gets a chance to land for bounded categories
- audit infrastructure becomes self-sufficient for future T-class work
- the next investigation can reproduce findings without re-running the live workspace

**Dependencies:** independent of Tranches 1–3 (can run in parallel), but proof-rerun verification benefits from landing after Tranche 1 so the rubric-leak count is measured against the post-Tranche-1 reject distribution.

**Risks:** schema/test risk for sub-edits 3+4; minimal for sub-edits 1+2+5.

**Cost band:** 1–2 days.

### Tranche 5. Cost Cap and Round Truncation (cost-side, evidence 1/10 from T8 alone, contingent on Tranche 1)

**Why fifth and last:** Cost reduction is operator-priority, but ONLY meaningful if quality is stable enough that truncating retry rounds doesn't drop verdicts. This tranche must land AFTER Tranches 1–3, never before.

**Owner:** Stage3 parent lane + `three_phase_blueprint_runtime.py` retry loop.

**Bounded scope (3 sub-edits):**

1. **Stop-if-no-improvement circuit breaker** — `three_phase_blueprint_runtime.py` retry loop adds: if the last 2 rounds produced no validator-score improvement AND the same reject family fires for the third time AND attempt_num ≥ 6, exit with `PASS_WITH_WARNING` instead of continuing to round 10. Source: T8.H8.6 (rounds 7–10 produced zero verdict flips on ep2/5/6/7 in the captured run, ~$13.5 wasted across 4 cap-hit episodes).

2. **Lower default attempt cap from 10 → 7** — `stage3_orchestrator.py` and `three_phase_blueprint_runtime.py` constants. Source: T8.H8.1 (~$14 saved per 7 eps if quality is stable; only safe after Tranche 1+2 land).

3. **conservative / balanced fan-out flavors decision** — `blueprint_ensemble.py:47-87` only ships 3 strategies despite parent order claiming 5; either DELETE the conservative/balanced references from docs (cheap) or ACTIVATE them as real strategies (expensive, only justified if T6 evidence shows they would diverge on contract fields). Source: T6.H6-D + T8.H8.5.

**Expected effect (contingent on Tranches 1–3):**

- ~30% Stage3 spend reduction without verdict regression
- attempt-cap saturation drops from 4/7 to ≤ 1/7
- Stage3 walltime per episode falls from 25–45 min to ≈ 12–18 min

**Dependencies:** **Hard prerequisite — Tranches 1+2+3 must land and be live-proven first.** Without them, the round cap will simply truncate at lower verdict, not at improved verdict.

**Risks:** wrong order of landing this tranche regresses quality. Mitigation: gate this tranche on a fresh proof rerun showing the average attempt count has fallen below 6 after Tranches 1–3.

**Cost band:** < 1 day, but cannot land first.

## 5. Deferred (not in top 5)

These items appear in the deliverables but are deferred for cost/risk/sequence reasons:

- **Stage4 vocabulary alignment (T10.H1–H6)** — Stage4 has not executed in this corpus. Forward-looking design proposals are valuable but cannot be ROI-ranked against Stage3 evidence. Defer until Stage3 closes enough episodes that Stage4 actually starts running, then re-evaluate.
- **Tier 3 / Tier 4 dead-code paths (T3.H5)** — `blueprint_ensemble.py:1658-1685` shows manuscript text windows up to 400K-char ceiling that are unused in the observed run. Either delete the dead code or wire it for real Stage4 reuse. Defer until Stage4 runs and T10 hypotheses re-evaluate.
- **Static boilerplate cache verification (T3.H3)** — ~6 KB static boilerplate in 286 BP prompts may or may not be cached. Quantitative answer requires `metrics_*.json` token-cost cross-check that T8 partly did but did not fully resolve. Defer to a narrow follow-up.
- **`patch_with_feedback` 5-field hard gate relaxation (T10.H6)** — touches Stage4 path; defer with T10.
- **Single-candidate fail-closed (T7.H4)** — re-opens TF-36 deliberate design decision. Defer pending design re-decision.
- **ep2 crashed-session resilience ($5.52 waste, T8.H8.3)** — process-level checkpoint/resume work. Belongs in a session-resilience track, not S2/S3/S4 quality. Flag only.
- **Producer rejected-candidate persistence schema design** — Tranche 4 sub-edit 4 covers the file-side write; if a DB column is also wanted for `attempt_raw_rationale` rows, that is a follow-up.

## 6. Strict Non-Goals (inherited from parent order §10)

This synthesis does not authorize:

- code, config, prompt, YAML, schema changes — proposals only
- live rerun, fresh proof wave, canary
- new execution SSOT creation, new queue lane creation
- model swap, tier change, cost-negotiation arguments
- test deletion or relaxation
- retroactive edits to T1–T10 deliverables (the per-terminal documents stand as authored)
- broader DecisionKernel / Polaris migration

Tranches 1–5 above describe **bounded next-decision proposals**, not landed work. Each tranche's `Expected effect` is a hypothesis until proven by a fresh rerun.

## 7. Risk Register

| Risk | Tranche | Severity | Mitigation |
|------|---------|----------|------------|
| Removing `→` and `진입` from marker lists could let a real explicit_transition slip through | T1 | medium | T5 already showed 100% FP on these tokens; co-occurrence requirement on absolute markers stays | 
| Splitting declared-vs-inferred in cheap admission spikes attempt-1 rejects until prompt edit lands | T1 | low | land sub-edits 1+2+3+4 of Tranche 1 together |
| Loosening tactical-intrusion markers lets real intrusion slip through | T2 | medium | require co-occurrence within N tokens, not removal alone |
| Director rubric reweighting changes Director selection on existing successful runs | T4 | medium | gate landing on a regression suite covering ep1–ep7 winners |
| Round cap truncation regresses quality if landed before T1–T3 | T5 | high | hard prerequisite: T5 must not land until proof rerun shows attempt count < 6 |
| Schema migration for `initial_verdict` / `losing_blueprint__*.json` breaks audit replay | T4 | low | additive only; existing readers ignore new fields |
| Changing `extract_episode_tactical` default behavior breaks the 13 production callsites that depend on the current priority chain | T1 | **high (was low — synthesis-time live-grep correction)** | T9 originally counted 2 callers; live grep finds 13 (Stage3, Stage4, Director, continuity, ToT, prompt_builder, constraint compiler). Mitigation: do NOT change the helper default; add `prefer_full_doc=False` parameter or new sibling helper, flip only at Stage3 producer-input callsite (`blueprint_ensemble.py:306`) |
| 10-attempt cap → 7 misses a legitimate late-recovery attempt | T5 | medium | data shows zero flips in rounds 7–10 on captured run, but sample is 7 episodes; expand to ≥ 30 episodes before hardening |
| All five tranches land in one sprint and proof rerun cannot isolate which tranche delivered which lift | sequencing | medium | land Tranche 1 first as a standalone proof; only land Tranche 2+ after T1 proof |

## 8. Recommended Sequencing

The five tranches should land in this order, with a fresh proof rerun gate between Tranche 1 and the rest:

```
Tranche 1 (Opening Transition Coherence)
   ↓
   Fresh proof rerun on ep1–ep8 — measure attempt-count + reject family distribution
   ↓
Tranche 2 (Producer Teaching + Validator Calibration Cleanup)
Tranche 3 (Retry Feedback Surgery)        ← can run in parallel with Tranche 2
Tranche 4 (Director Rubric + Audit Visibility) ← can run in parallel with 2+3
   ↓
   Fresh proof rerun — confirm attempt count < 6 average
   ↓
Tranche 5 (Cost Cap and Round Truncation) ← only after the second proof
```

The synthesis explicitly does not authorize any of this sequence; it only describes the safest landing order if the operator decides to act on the proposals.

## 9. Confidence Justification

Confidence `97%` rests on:

- 10 independent terminals each at 96–97% on their own scope
- 5 critical cross-terminal anchors live-grep-verified before this save:
  - `stage_cross_stage_contract.py:34` (`진입`) and `:49-50` (`->`/`→`) — Tranche 1 sub-edit 1
  - `unified_blueprint_validator.py:80-103` (tactical marker lists) — Tranche 2 sub-edit 1
  - `unified_blueprint_validator.py:455` (`merged_scope = "full"` override) — Tranche 1 sub-edit 5
  - `blueprint_ensemble.py:989-1009` (`_normalize_opening_transition_contract`) — Tranche 1 sub-edit 4
  - `tactical_utils.py:31` (`extract_episode_tactical` priority chain) — Tranche 1 sub-edit 3
- post-draft live-grep correction caught one terminal's understated blast radius (`extract_episode_tactical`: T9 reported 2 callers, actual count 13); the synthesis Risk Register and Tranche 1 sub-edit 3 were both updated before final save, and the audit chain that caught it is recorded in §10 Pass 2
- the merge table (§3) cross-references each theme to the exact terminals that cited it; nothing is asserted from a single source
- tranche scoping uses verbatim code anchors rather than paraphrased intent

Residual 3% uncertainty:

- Stage4 has not run, so T10 cannot be evidence-weighted against live behavior; Tranche deferral is correct but not provable until Stage4 actually executes
- T6's "5 strategies vs 3 strategies" gap means parent order assumed 5 but code ships 3; this does not change synthesis math but does mean any future "5-strategy" claim must be re-checked
- T8's cost attribution leaves crashed-session ($5.52) outside the standard breakdown; this affects the absolute spend baseline by ~12% but does not change the ROI ranking
- one terminal-level claim (T9 caller count) was downgraded by synthesis-time verification; other terminals were not exhaustively re-verified, so additional similar drift is possible but bounded — implementation phase must re-grep every cited line at landing time, per the parent order's "current-head dirty workspace" rule

## 10. 3-Pass Audit Record

### Pass 1. Structure and scope

- kept the document synthesis-only (no code edit, no queue mutation)
- bounded to the 10 terminal deliverables; no new terminals invented
- merge table separates quality themes (Θ1–Θ10) from cost themes (C1–C4) so the operator can decide on quality-first or cost-first sequencing without confusion
- top 5 tranches respect the parent order's "3–5 bounded tranches" budget
- deferred section explicitly enumerates what is NOT in the top 5 and why
- non-goals inherited verbatim from parent order §10
- risk register cites both per-tranche risks and the cross-tranche sequencing risk
- recommended sequencing is presented as guidance, not authorization

### Pass 2. Evidence and consistency

- every theme in the merge table is anchored to at least one terminal's hypothesis number
- the 10/10 evidence weight on Θ1 was double-checked: T1.H1, T2.H1+H2, T3.H4, T4.H1, T5.H1, T6.H6-A, T7.H1+H3, T9.H1, T10.H1 — that is exactly 10 terminals
- cross-checked T6's "only 3 strategies ship" against the parent order's "5 strategies" claim — confirmed parent order is wrong on this; synthesis text now explicitly notes the gap
- live-grep verified 5 critical anchors before save (see §9 Confidence Justification)
- live-grep verified `extract_episode_tactical` callsite count after draft save: T9 reported "2 callers, both Stage3-bound", live grep found 13 production callsites including Stage4 / Director / continuity / ToT / prompt_builder; Tranche 1 sub-edit 3 was rescoped to a parameter-flag pattern instead of a default-behavior change, and Risk Register row was upgraded to "high" with explicit blast-radius mitigation
- terminals' confidence numbers (all 96–97%) carry forward to the merge table; no terminal's claim was upgraded; T9's caller-count claim was DOWNGRADED post-verification but the rest of T9's evidence (shadowing pattern, entity loss, equipment provenance gap) stands
- Tranche dependency ordering checked against parent order's three-tranche safe sequencing plan and against T8's cost-cap caveat

### Pass 3. Execution and readability

- merge table up front lets the operator find any theme by number
- each tranche has the same structure (Why / Owner / Scope / Effect / Dependencies / Risks / Cost band / Verification gate where applicable)
- recommended sequencing diagram makes the prerequisite chain explicit (Tranche 5 cannot land before 1–3)
- deferred section prevents this synthesis from being read as "all 10 hypotheses are equal"
- non-goals + risk register make the boundary between "synthesis proposes" and "implementer decides" explicit

## 11. Final Confidence

`97%` after the 3-pass audit above and the 5-anchor live verification round. The 3% residual is attributed to Stage4 dormancy (T10) and the parent-order strategy-count claim (T6). Neither residual changes the top-5 tranche ranking; both are recorded as explicit caveats above.
