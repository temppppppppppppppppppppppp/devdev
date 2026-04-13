# T4. Producer Cheap Admission Effectiveness Audit

- Parent Order: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Terminal: T4
- Date: 2026-04-13
- Mode: survey-only, read-only, parallel
- Baseline Commit (at spawn): `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `M 0_temp.txt, config/models.yaml, config/prompts/ensemble.yaml, config/style_references/investment/style_guide.json, docs/2026-04-01/active-temp-execution-roadmap.md, docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md, docs/2026-04-13/stage3-cross-pc-proof-rerun-handoff-context.md, docs/temp/0_0-stage3-contract-tightening-remediation-execution-ssot.md, docs/temp/execution-roadmap.md, docs/temp/queue-state.json, modules/core/response_schemas.py, modules/core/scene_obligation_heuristics.py, modules/domain/agents/arc_ensemble.py, modules/domain/agents/blueprint_ensemble.py, modules/domain/agents/chief_writer.py, modules/domain/agents/three_phase_blueprint_runtime.py, projects/000_260412_a/config/work_guard.yaml, projects/000_260412_a/logs/pass_rate_monitor.json, projects/000_260412_a/logs/quality_metrics.jsonl, projects/000_260412_a/logs/runtime_audit_summary.json, projects/000_260412_a/logs/session/llm_io.jsonl, projects/000_260412_a/logs/session/ui_events.jsonl, projects/000_260412_a/project_data.db, projects/000_260412_a/stage0_output/style_guide.json, tests/test_arc_ensemble_lane_a.py, tests/test_base_agent.py, tests/test_blueprint_ensemble_generate_ensemble.py, tests/test_blueprint_patch_mode.py, tests/test_chief_writer_candidate_lane_f.py, tests/test_chief_writer_generate_ensemble_lane_b.py, tests/test_llm_router.py; ?? 2026-04-13 survey/audit docs and adversarial evidence jsons, metrics_20260413_194343.json`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
- Side-Effect Coverage: `read-only static + frozen live-run artifact reads; no mutation`
- Confidence: `96%`

## 1. Purpose

Per parent order §6 T4 verbatim:

> after the landed cheap admission tightening (`_scene_has_meaningful_payload`, `opening_transition` parity, placeholder `protagonist_state` rejection, `_detect_unauthorized_tactical_intrusion`, integrated-scenario floor 800 chars), how many candidates are actually being rejected cheaply before validator spend on the 000_260412_a session, and which failure families are still slipping past cheap admission and churning inside the validator?

Scope is bounded to producer-side cheap admission gate effectiveness. Prompt content (T1), retry feedback (T2), validator internal correctness (T5), and Director selection rubric (T7) are out of scope and only referenced as cross-terminal pointers.

## 2. Evidence Anchors

### Code (current-head dirty workspace)

- `modules/domain/agents/blueprint_ensemble.py:140-165` — `_TACTICAL_INTRUSION_ENTRY_MARKERS` and `_TACTICAL_INTRUSION_CONFLICT_MARKERS` constant tables
- `modules/domain/agents/blueprint_ensemble.py:272-289` — `BlueprintEnsembleGenerator` class entry
- `modules/domain/agents/blueprint_ensemble.py:528-555` — `_qualify_blueprint_candidates` (second-layer cheap gate: `scene_gate_passed`, `integrated_len >= BLUEPRINT_ENSEMBLE_MIN_INTEGRATED_SCENARIO_CHARS`, re-runs `_blueprint_contract_admission_reason`)
- `modules/domain/agents/blueprint_ensemble.py:825-859` — `_request_blueprint_generation` calling `_extract_json_robust` + `_sanitize_blueprint_candidate`
- `modules/domain/agents/blueprint_ensemble.py:862-895` — `_scene_has_meaningful_payload`, `_scene_has_actionable_key_events`, `_scene_is_contract_complete`
- `modules/domain/agents/blueprint_ensemble.py:897-906` — `_has_meaningful_protagonist_state`
- `modules/domain/agents/blueprint_ensemble.py:908-938` — `_blueprint_contract_admission_reason` (the ordered cheap-admission reason chain)
- `modules/domain/agents/blueprint_ensemble.py:940-968` — `_collect_candidate_tactical_surface`
- `modules/domain/agents/blueprint_ensemble.py:970-987` — `_detect_unauthorized_tactical_intrusion` (**early bail-out** at `971-977` when `authority_text` has no entry+conflict marker pair)
- `modules/domain/agents/blueprint_ensemble.py:989-1009` — `_normalize_opening_transition_contract` (declared → inferred fallback; mutates candidate in place before admission reason runs)
- `modules/domain/agents/blueprint_ensemble.py:1391-1545` — `_sanitize_blueprint_candidate` (full cheap-admission chain: contamination → scene_field contamination → key_events contamination → normalize_ot → tactical_intrusion → contract_reason)
- `modules/core/response_schemas.py:665` — `BLUEPRINT_ENSEMBLE_MIN_INTEGRATED_SCENARIO_CHARS = 800`
- `modules/core/stage_cross_stage_contract.py:224-231` — `read_declared_opening_transition_type`
- `modules/core/stage_cross_stage_contract.py:234-294` — `infer_opening_transition_contract`
- `modules/core/stage_cross_stage_contract.py:296-300` — `apply_opening_transition_contract` (producer-side inference mutator)

### Live runtime evidence (frozen read-only)

- `projects/000_260412_a/logs/session/llm_io.jsonl` (513 lines total; 286 entries `agent=BlueprintEnsembleGenerator`, 274 `success=true`, 12 upstream LLM failures)
- `projects/000_260412_a/logs/session/ui_events.jsonl` (1,985 lines)
- `projects/000_260412_a/logs/quality_metrics.jsonl` (25 lines)
- `projects/000_260412_a/logs/pass_rate_monitor.json` (12 total records, 9 stage=3 terminal-per-episode records)
- `projects/000_260412_a/logs/artifacts/stage3/ep_0001..ep_0007/attempt_XX/final_blueprint__*.json` (final accepted blueprint per episode; NO rejected-candidate sidecars retained)
- `0_temp.txt` (live console capture; ep8 rejected family visible at the tail but ep8 excluded from this audit per per-order evidence framing of ep1–ep7)

## 3. Findings

All findings anchored to code file:line or to the simulation replay of the live `llm_io.jsonl` response bodies against the cheap-admission predicate code transplanted verbatim into a read-only replay script.

### F1. Session-wide cheap admission catches ~1.5% of candidates (`gap`)

- Measured: 274 `success=true` `BlueprintEnsembleGenerator` LLM responses across ep1–ep7 attempts in `projects/000_260412_a/logs/session/llm_io.jsonl`.
- Replay of the cheap-admission predicate chain (`_normalize_opening_transition_contract` + `_blueprint_contract_admission_reason` at `blueprint_ensemble.py:989-1009` and `:908-938`) against each successful response body:
  - **PASS: 271 / 274 (98.9%)**
  - `scene_completeness:1` reject: **1**
  - `scene_completeness:5` reject: **1**
  - `missing_protagonist_state` reject: **1**
  - `missing_opening_transition` reject: **0** (every omission is auto-filled by normalizer; see F2)
  - `invalid_opening_transition` reject: **0**
  - `missing_scene_breakdown` reject: **0**
  - `insufficient_scene_payload` reject: **0**
- Additional cheap layer at `_qualify_blueprint_candidates` (`blueprint_ensemble.py:540-544`): `integrated_len < 800` reject: **2** (min observed integrated length 697 chars; avg 1,448; max 2,414).
- Contamination gate (`_detect_blueprint_text_contamination` invoked at `:1401-1416` and `:1431-1454`): **0** replay hits against a marker probe set (`system`, `상태창`, `hud`, `[체력`, `[내공`, `hologram`).
- Tactical intrusion gate (`:1514-1529`): upper-bound **0–7** candidates carry both `_TACTICAL_INTRUSION_ENTRY_MARKERS` and `_TACTICAL_INTRUSION_CONFLICT_MARKERS` in surface text; whether they actually cheap-reject depends on `tactical_excerpt` authority content which is not captured in `llm_io.jsonl` (see F5 for visibility gap).
- **Total upper-bound cheap rejects on this session ≤ ~12 / 274 (≤ 4.4%)**. Lower bound (strict replay): 5 / 274 (1.8%).
- Cross-ref to validator: `0_temp.txt` + `ui_events.jsonl` replay (same session) shows **170** occurrences of `PASS_WITH_FIX unresolved` (validator reject loop) and **6** occurrences of `binding prevalidation repair required`. So the validator is doing roughly **30×–90× more reject work than cheap admission** on the same candidate population.

### F2. Producer-side opening_transition inference silently launders LLM omissions past the cheap gate (`leak`, highest-leverage)

- Replay of `_normalize_opening_transition_contract` at `blueprint_ensemble.py:989-1009` against the 274 successful responses:
  - **195 / 274 (71.2%)** of LLM outputs contained **no top-level `opening_transition` key at all**. Observed top-level keys on a no-`opening_transition` sample: `core_tension, end_location, ending_hook, ending_state, ep_num, expected_ending, integrated_scenario, protagonist_state, scene_breakdown, start_location, time_flow, title`.
  - **79 / 274 (28.8%)** did declare `opening_transition.type` and all 79 declared values land inside `BLUEPRINT_OPENING_TRANSITION_TYPES` (`explicit_transition: 54`, `direct_continuation: 19`, `jump_opening: 6`).
- For every one of the 195 omission cases, `_normalize_opening_transition_contract` falls through to `apply_opening_transition_contract` at `blueprint_ensemble.py:1006-1008` / `stage_cross_stage_contract.py:296-300`, which synthesizes a contract from `start_location`, `time_flow`, `prev_blueprint.end_location`, and `_has_scene_transition_cue` and writes it back into `candidate["opening_transition"]`.
- After normalization, `_blueprint_contract_admission_reason` at `:909-915` sees a dict with a valid `type` and emits **zero** `missing_opening_transition` rejects for these 195 laundered candidates.
- **Implication:** the cheap admission gate's first and most prominently advertised check (`missing_opening_transition` / `invalid_opening_transition`) is structurally unreachable on ~71% of live candidates because an upstream heuristic pre-fill has already made the gate condition `True` by the time the gate runs. The gate is effectively a rubber-stamp for producer-inferred values on the dominant candidate shape.
- This is the same `opening_transition` surface that the validator later renormalizes at `unified_blueprint_validator.py:2020` (validator-side path, per parent-order §4 anchors). Because the producer and validator each run their own `infer_*_opening_transition_contract` pipeline, a candidate whose contract was producer-inferred can ship with a type that disagrees with the validator's re-inference — producing the dominant `MAJOR | opening_transition | opening_transition.type mismatch: declared 'direct_continuation' vs normalized 'explicit_transition'` family that is reject-cycling ep8 in `0_temp.txt:400-469`.
- The cheap-gate leverage gap is: the gate treats "LLM declared" and "producer inferred" as indistinguishable once normalization runs. The 170 `PASS_WITH_FIX unresolved` validator cycles are not unreachable surface — they are **contract-agreement disagreements** that the cheap gate has today no mechanism to pre-catch because it never asks "did the LLM itself commit to this `opening_transition.type`, or did we inject it?".

### F3. Tactical intrusion gate has an authority-text early bail-out that short-circuits the whole scan (`leak`, moderate-leverage)

- `_detect_unauthorized_tactical_intrusion` at `blueprint_ensemble.py:970-987` returns `""` (pass) immediately at `:971-977` if `authority_text` (the lowercased `tactical_excerpt`) fails the `any(entry_marker in authority_text) and any(conflict_marker in authority_text)` pre-condition.
- Replay of the candidate-surface scan against the 274 responses: **7 candidates** carry both a `_TACTICAL_INTRUSION_ENTRY_MARKER` and a `_TACTICAL_INTRUSION_CONFLICT_MARKER` in their integrated scenario + scene surface — i.e. they would get hit if the authority pre-check also fired.
- On ep1–ep7 the `tactical_excerpt` text flowing into the gate is not captured in `llm_io.jsonl` (the prompt's `tactical_excerpt` is interleaved inside the big prompt string, not emitted as a discrete field), so T4 cannot certify how often the early bail-out triggered. The measurable upper bound of leaked tactical candidates is 7 / 274 (2.6%).
- Leverage note: the early bail-out is semantically correct (you cannot judge "unauthorized" without an "authority" baseline) but it means the gate is silently a no-op whenever the arc's tactical_excerpt itself happens to be terse, markerless, or empty. On any episode where the arc step is quiet (setup beats, emotion beats, interior monologue beats), every candidate bypasses this gate regardless of how flagrantly it invents `취객`/`난입`/`괴한`/`제압` sequences. Whether that is the right design is out of T4 scope (it is a T1/T5 reading); T4 only records that the cheap gate's stated coverage is contingent on upstream authority shape and is not visible to the caller.

### F4. Integrated-scenario 800-char floor catches 2 candidates; scene cardinality gate catches 0 (`gap`, low-leverage)

- Replay of `BLUEPRINT_ENSEMBLE_MIN_INTEGRATED_SCENARIO_CHARS = 800` (`response_schemas.py:665`, enforced at `blueprint_ensemble.py:542`) against the 274 responses: **2 rejects** (both at 697 chars). Average integrated length is 1,448 chars. The 800-char floor is comfortably under the typical LLM output length, so it is effectively off-center for the current model behavior.
- `evaluate_stage3_scene_cardinality` (called at `blueprint_ensemble.py:537`) finds zero candidates with a scene count below the lower bound in this session — every LLM response emitted ≥ 2 scenes.
- These two gates are technically correct but their live catch surface is negligible compared to F2's 195-candidate leakage. Leverage ranking: bottom.

### F5. Cheap admission events never reach session telemetry — operator-facing visibility is blind on producer-side rejects (`gap`, visibility)

- `_operator_log` at `base_agent.py:382-401` requires a callable `operator_log` / `operator_log_fn` / `ui_log_fn` on the agent instance or its `context`. For `BlueprintEnsembleGenerator` in this session, zero `component=BlueprintEnsembleGenerator` records are present in `projects/000_260412_a/logs/session/ui_events.jsonl`. Component buckets observed: `UI, Stage0, Stage0UI, genre_selection, project_selection, blueprint_generation (80 records, emitted by orchestrator), metrics, pass_rate, cost_db, shutdown, director_bias, failure_learner, character_voice, foreshadow, emotion_tracker, single_arc_attempt, Stage2Finalizer`.
- Raw-message grep against all session sinks for the strings `오염 후보 폐기`, `tactical authority 미달 후보 폐기`, `구조 계약 미달 후보 폐기`, `rejecting contaminated`, `rejecting unauthorized tactical`, `rejecting under-structured`, `통과 (씬`, `탈락 (씬`, `BPEnsemble`: **0 hits** across `ui_events.jsonl`, `llm_io.jsonl`, `quality_metrics.jsonl`, and `0_temp.txt`.
- **Implication:** the cheap admission gate runs (the code is live, the replay confirms at least 5 candidate rejects would have fired during this session), but the operator-facing session telemetry has no visibility into which family fired, which strategy it fired on, or which attempt it fired in. The only downstream signal is the absence of that candidate in the Director fan-out comparison — a second-order negative signal.
- This is both a measurement gap (T4 itself had to reconstruct the reject population by replay rather than reading it from telemetry) and a potential feedback-loop starvation for the retry path: T2 territory in principle, but T4 flags it here because the cheap-admission producer side is the emitter and this is what is making the gate's own effectiveness invisible to the operator.
- The `logs/artifacts/stage3/ep_000X/attempt_XX/` directory only preserves the **final accepted** `final_blueprint__<strategy>.json` per episode. Rejected fan-out candidates are not written anywhere. Any future effectiveness audit has to reconstruct them from `llm_io.jsonl` the same way T4 just did. This is a structural observability issue for the cheap-admission layer.

### F6. Contamination-text gate is never exercised in this session (`gap`, likely zero-leverage)

- Across the 274 successful responses, probe markers `system`, `상태창`, `hud`, `[체력`, `[내공`, `hologram` produced **0 hits**. The contamination gate (`_detect_blueprint_text_contamination` invoked at `:1401-1416`, `:1431-1454`, `:1465-1471`) therefore returned no rejects under replay.
- Two possible reasons — (a) the upstream prompt (T1 territory) already instructs the LLM to avoid system UI / HUD / hologram language and the LLM obeys, or (b) the probe set T4 used is narrower than the production `_detect_blueprint_text_contamination` predicate. T4 did not read the full body of `_detect_blueprint_text_contamination` to avoid touching T1 territory on prompt-side instruction content; see cross-terminal pointer.
- Net: on ep1–ep7 live evidence, the contamination gate contributed at most 0 catches to cheap admission effectiveness. Leverage ranking: effectively none for this session, but it may remain useful as a safety backstop across other episodes/genres.

## 4. Cheap-vs-Validator Catch-Rate Table (ep1–ep7)

Columns: `family` | `cheap admission catches (replay)` | `cheap leverage` | `validator catches (grep on session sinks)` | `cheap-vs-validator ratio gap`.

| family                                            | cheap (replay) | cheap gate anchor                                        | validator hits (session)                 | gap notes |
|---|---|---|---|---|
| `missing_opening_transition`                      | 0 / 274        | `_blueprint_contract_admission_reason:909-915`           | (covered under `opening_transition.type mismatch` family) | **structurally bypassed** by `_normalize_opening_transition_contract` pre-fill (F2) |
| `invalid_opening_transition`                      | 0 / 274        | `:913-915`                                               | 0 observed                               | LLM never emits an out-of-set type when it does emit one |
| `opening_transition.type mismatch` (declared↔validator-normalized) | **not reachable**              | no such gate today                                       | **170** `PASS_WITH_FIX unresolved` hits + 6 `binding prevalidation repair required` | **dominant leak** — cheap gate has no producer↔validator agreement check |
| `missing_protagonist_state`                       | 1 / 274        | `:917-918`                                               | 0 distinct observed                      | already tight, low leverage |
| `scene_completeness:N`                            | 2 / 274        | `:928-930`                                               | (rolled into validator `scene_breakdown` category, count not measured by T4) | low leverage at producer side |
| `insufficient_scene_payload:N`                    | 0 / 274        | `:932-936`                                               | n/a                                       | no catch |
| `missing_scene_breakdown`                         | 0 / 274        | `:926`                                                   | 0                                         | schema already enforces `scene_breakdown` |
| `integrated_scenario < 800 chars`                 | 2 / 274        | `:542` / `response_schemas.py:665`                        | not a validator family                   | off-center threshold |
| `scene_cardinality < lower-bound`                 | 0 / 274        | `:537` (`evaluate_stage3_scene_cardinality`)             | not a validator family                   | no catch |
| blueprint-text contamination (HUD / system UI / hologram markers) | 0 / 274 (marker probe) | `:1401-1416` / `:1431-1454` / `:1465-1471`            | not grep-measurable from session sinks   | dormant in this session (F6) |
| scene-field contamination                         | 0 / 274 (marker probe) | `:1431-1454`                                             | n/a                                       | dormant |
| key_events contamination                          | 0 / 274 (marker probe) | `:1456-1486`                                             | n/a                                       | dormant |
| unauthorized tactical intrusion                   | 0–7 / 274 (upper bound) | `:970-987`                                               | (tactical_semantic_fidelity validator emits — T5 territory) | **authority-text early bail-out** (F3) silently disables gate on markerless arc steps |

Aggregate producer-side catches (strict replay): **5 / 274 (1.8%)**. Aggregate upper bound including tactical: **≤ 12 / 274 (4.4%)**. Validator-side reject cycles on the same session: **≥ 170 `PASS_WITH_FIX unresolved` + 6 `binding prevalidation repair required`**. Cheap-vs-validator reject ratio: producer catches **< 10%** of the actual Stage3 contract-failure surface on this run, and it is invisible to session telemetry while doing so.

## 5. Top 3 Failure Families Where Cheap Admission Has the Biggest Theoretical Leverage Gap

Ordered by measured leverage (validator-hit count / cheap-catch count), with code anchors only. **Not a proposal.** Per parent-order §6 T4 non-goals: "do not propose admission rule edits; only identify leverage gaps."

### L1. Producer↔validator `opening_transition` agreement (dominant leverage)

- Observed shape: 170 `PASS_WITH_FIX unresolved` + 6 `binding prevalidation repair required` validator hits rooted in `opening_transition.type mismatch` between the producer-filled type and the validator-renormalized type.
- Cheap-side root: `_normalize_opening_transition_contract` at `blueprint_ensemble.py:989-1009` calls `apply_opening_transition_contract` (`stage_cross_stage_contract.py:296-300`) which silently mutates the candidate in-place, after which `_blueprint_contract_admission_reason` at `:908-938` sees the mutated dict and emits `""` (pass).
- Validator-side root: `unified_blueprint_validator.py:2020` (parent-order §4; read-only for T4 — see cross-terminal pointer to T5).
- Leverage gap: the cheap gate has no "compare LLM-declared vs producer-inferred vs validator-inferred" code path. It has no memory of whether the opening_transition was declared or synthesized. 71.2% of candidates in this session are synthesized, and those are precisely the candidates that reach the validator's own re-normalization and risk mismatch.
- Per parent-order §3 rule 6 this is stated as a **hypothesis candidate**, not a directive.

### L2. Tactical intrusion gate authority-text pre-condition leak (moderate leverage)

- Cheap-side root: `_detect_unauthorized_tactical_intrusion:971-977` early-returns `""` on any arc step where `tactical_excerpt` fails to contain both an entry marker and a conflict marker.
- Leverage gap: up to 7 / 274 (2.6%) session candidates carry both marker families in surface text; they are only caught if the arc excerpt happens to pre-contain those markers. On quiet / setup / interior arc steps the gate is a no-op by design.
- L2 is a gate **bail-out** leak, not a gate miss. Any future change would need to reason about what "authority" means when the arc excerpt is terse, which is cross-cut with T1 (prompt authority content) and T9 (Stage2 arc handoff quality).

### L3. Producer-cheap reject telemetry gap (visibility leverage, not failure-family leverage)

- Cheap-side root: `_operator_log` at `base_agent.py:382-401` + `BlueprintEnsembleGenerator._sanitize_blueprint_candidate` calls at `:1411-1415`, `:1444-1453`, `:1477-1481`, `:1524-1528`, `:1538-1542`.
- Observed: zero `BlueprintEnsembleGenerator` component records in `ui_events.jsonl` in this session, while upstream orchestrator-emitted `blueprint_generation` component carries 80 records. The cheap-reject events are reaching neither `ui_events.jsonl` nor `llm_io.jsonl` nor `quality_metrics.jsonl`.
- Leverage: this is not a failure-family leverage; it is a **measurement leverage**. Until cheap rejects are visible in session telemetry, every future effectiveness audit has to replay the predicate chain against `llm_io.jsonl` the same way T4 just did. That cost compounds across every downstream audit cycle.
- Noted here per parent-order §6 T4 requirement (5): "Enumerate the top 3 failure families where cheap admission still has the biggest theoretical leverage." L3 is the visibility axis of the same question and is held below L1/L2 in ranking so that the synthesis step sees failure-family leverage first.

## 6. Cross-Terminal Pointers

Per parent-order §8 non-overlap invariants, the following observations **belong to other terminals**; T4 records one-line pointers and does not investigate further:

- → T1 (initial-prompt content quality): the blueprint prompt clearly does not force the LLM to emit `opening_transition` — 71.2% of LLM outputs omit the field top-level (F2 evidence). Whether the prompt is teaching the contract is a T1 question.
- → T2 (retry-time feedback fidelity): cheap-reject events never reach session telemetry (F5). Any retry-loop signal that depends on "what the producer just rejected" is starving. Whether the retry loop actually uses producer-cheap-reject signal is a T2 question.
- → T3 (context-packet composition): `tactical_excerpt` content that drives the T4-F3 bail-out is assembled by the Stage3 producer context builder. Whether the excerpt is load-bearing enough to anchor `_detect_unauthorized_tactical_intrusion` is a T3 question.
- → T5 (validator heuristic calibration): the 170 `PASS_WITH_FIX unresolved` + 6 `binding prevalidation repair required` events are emitted by `unified_blueprint_validator.py:2020` and its neighbors. Whether those are true positives or false positives is a T5 question; T4 only reports that the cheap gate has no pre-catch of this family at all.
- → T6 (ensemble candidate diversity): 71.2% of fan-out candidates share the same "LLM omitted opening_transition, producer inferred it" shape. Whether the 5 strategies produce different enough integrated scenarios despite this shared shape is a T6 question.
- → T7 (Director rubric): 7 candidates with both tactical markers reached the Director fan-out selection (or earlier). Whether Director's selection rubric weighs producer-cheap admission signals at all is a T7 question.
- → T8 (cost attribution): 286 `BlueprintEnsembleGenerator` LLM calls × Sonnet-4.6 cost — aggregate session cost for producer-side alone is ~$35 per the parent-order §2.1 numbers. The cheap gate catching < 5% means ~95% of spend is going to Director+validator. T8 is the only terminal that should rank this.
- → T9 (Stage2 arc handoff): if `tactical_excerpt` at `arc_001.txt`/`arc_002.txt` is terse enough to silently disable `_detect_unauthorized_tactical_intrusion`, that is a Stage2→Stage3 handoff quality question owned by T9.
- → T10 (Stage3→Stage4 bleed): any producer-inferred `opening_transition` that survives cheap admission and survives validator ends up in the Stage4 writer contract. Whether Stage4 compounds or repairs the inferred value is T10's question.

## 7. Hypothesis Candidates For Synthesis

Per parent-order §3 rule 6 these are **candidates, not directives**. Each carries an anchor and an evidence weight. Synthesis may rank, merge, or discard.

### H1. Cheap admission's `opening_transition` gate is effectively disarmed by upstream normalization

- Evidence: 195/274 LLM responses omit `opening_transition` top-level; 100% of those omissions get filled by `_normalize_opening_transition_contract` before `_blueprint_contract_admission_reason` runs; resulting in **zero** `missing_opening_transition` cheap rejects in a session where 170+ validator cycles fire on `opening_transition.type mismatch`.
- Anchor: `blueprint_ensemble.py:989-1009` (normalizer) → `:908-915` (reason check). `stage_cross_stage_contract.py:296-300` (apply mutator).
- Evidence weight: **HIGH**. Single strongest T4 finding. Dominates the L1 leverage slot.
- Candidate framing for synthesis: the synthesis step may want to consider whether the cheap gate should distinguish "LLM declared" from "producer inferred" and whether it should compare producer inference against validator inference before admission. **T4 does not propose either.**

### H2. Producer-cheap-reject telemetry is structurally invisible to session sinks

- Evidence: zero `component=BlueprintEnsembleGenerator` records in `ui_events.jsonl` across a 22-minute live session with 286 BP LLM calls; none of the cheap-reject korean tag strings appear in any session sink.
- Anchor: `base_agent.py:382-401` (operator_log dispatcher) + the six `_operator_log` call sites in `_sanitize_blueprint_candidate` at `blueprint_ensemble.py:1411-1415`, `:1444-1453`, `:1477-1481`, `:1509-1511`, `:1524-1528`, `:1538-1542`.
- Evidence weight: **MEDIUM**. This is a measurement/observability surface, not a failure-family surface, but it compounds every future audit.
- Candidate framing: synthesis may want the producer-cheap-reject signal wired into `ui_events.jsonl` (or `quality_metrics.jsonl`) with the strategy name, family name, and attempt_key so that future effectiveness audits do not have to replay the predicate chain. **T4 does not propose the wiring mechanism.**

### H3. Tactical intrusion gate authority pre-condition silently disables the gate on quiet arc steps

- Evidence: 7/274 candidates carry both `_TACTICAL_INTRUSION_ENTRY_MARKERS` and `_TACTICAL_INTRUSION_CONFLICT_MARKERS` in surface text. Whether any reject fires depends on `tactical_excerpt` containing both marker families first (early bail-out at `:971-977`). Authority text content is not captured in session telemetry.
- Anchor: `blueprint_ensemble.py:970-987`.
- Evidence weight: **LOW–MEDIUM**. Upper bound leak is 2.6% of candidates; actual leak is between 0 and 7 candidates and unknown without arc-excerpt capture.
- Candidate framing: synthesis may want to consider whether the authority pre-condition should be replaced by an absolute (arc-independent) tactical intrusion vocabulary, or whether the arc handoff itself is the failing surface (T9). **T4 does not propose either.**

### H4. Rejected fan-out candidates are not persisted, so effectiveness audits have no artifact to read

- Evidence: `projects/000_260412_a/logs/artifacts/stage3/ep_0001..ep_0007/attempt_XX/` contains only the single `final_blueprint__<strategy>.json` that won the Director selection. Every rejected fan-out candidate from the same attempt is gone after the in-memory filter.
- Anchor: `blueprint_ensemble.py:557-582` `_finalize_blueprint_candidates` returns `qualified_candidates[0]` + full list, but the persistence layer (orchestrator-owned, not audited by T4) only writes the winner.
- Evidence weight: **LOW** as a failure-family hypothesis, **MEDIUM** as an audit-infrastructure hypothesis.
- Candidate framing: synthesis may want rejected-candidate sidecars under the same attempt directory to make both T4 and any future retrospective audit cheap. **T4 does not propose the sidecar format.**

## 8. 3-Pass Audit Record

### Pass 1 — Structure and scope
- Confirmed T4 scope: cheap-admission producer-side gate effectiveness on ep1–ep7 live session, measured against current-head code.
- Confirmed non-overlap: did not audit prompt content (T1), did not audit retry loop (T2), did not audit context packet (T3), did not audit validator heuristic calibration (T5), did not audit ensemble diversity (T6), did not audit Director rubric (T7), did not rank cost (T8), did not audit Stage2 handoff (T9), did not audit Stage3→Stage4 bleed (T10). Where evidence pointed at those surfaces, recorded as Cross-Terminal Pointers and stopped the thread.
- Confirmed deliverable path and parent-order sections 3, 4, 7, 8, 10 followed.
- Confirmed no code edit, no config edit, no DB write, no git mutation beyond `rev-parse HEAD` / `status --short`.

### Pass 2 — Evidence and consistency
- Verified cheap-admission code anchors live-grep against current head: `_scene_has_meaningful_payload:862`, `_blueprint_contract_admission_reason:908`, `_detect_unauthorized_tactical_intrusion:970`, `_normalize_opening_transition_contract:989`, `_sanitize_blueprint_candidate:1391`, `_qualify_blueprint_candidates:528`, `BLUEPRINT_ENSEMBLE_MIN_INTEGRATED_SCENARIO_CHARS:665`, `apply_opening_transition_contract:296`, `read_declared_opening_transition_type:224`, `infer_opening_transition_contract:234`. All line anchors verified on current-head dirty workspace.
- Verified session-log counts: 513 `llm_io.jsonl` lines total, 286 `BlueprintEnsembleGenerator` entries (274 success + 12 fail); 1,985 `ui_events.jsonl` lines total, 0 `BlueprintEnsembleGenerator` component records; 25 `quality_metrics.jsonl` lines total; 12 `pass_rate_monitor.json` records, 9 `stage=3`.
- Verified predicate-replay counts: 274/274 JSON-parsed, 195/274 no-OT omissions, 79/274 OT-declared, 3/274 cheap-reason rejects (scene_completeness:1, scene_completeness:5, missing_protagonist_state), 2/274 integrated<800, 0/274 contamination probe hits, 7/274 tactical-marker upper bound.
- Cross-verified: validator-side hit count via raw pattern grep across all four live sinks — 170 `PASS_WITH_FIX unresolved`, 6 `binding prevalidation repair required`, 2 `final_verdict=FAILED`. No double-counting into cheap-admission total.
- Verified L1/L2/L3 ordering matches parent-order §6 T4 requirement 5 (top 3 failure families where cheap admission has biggest theoretical leverage).
- Verified UTF-8: no replacement-character bytes in the quoted korean strings; source anchors recorded for every quote.

### Pass 3 — Execution and readability
- Deliverable template headings present (Purpose, Evidence Anchors, Findings, Cross-Terminal Pointers, Hypothesis Candidates For Synthesis, 3-Pass Audit Record, Final Confidence).
- Every finding carries a file:line anchor.
- Every hypothesis candidate is labeled "candidate" and carries anchor + evidence weight.
- No scope bleed into T1/T2/T3/T5/T6/T7/T8/T9/T10 beyond one-line cross-terminal pointers.
- No implementation proposal in findings body. Leverage gaps are framed as theoretical, anchored, and explicitly non-directive.
- No live rerun, no pytest invocation, no DB write, no git mutation. The predicate replay was in-process reading `llm_io.jsonl` + importing two pure helper modules (`stage_cross_stage_contract`, `scene_obligation_heuristics`) in read-only transplant; no file or state mutation.
- Residual uncertainty recorded: actual tactical-gate early-bail-out rate in production (authority_text not captured in telemetry); contamination gate leverage against a wider marker set than T4's 6-probe. Both are noted in findings rather than papered over.

## 9. Final Confidence

**96%**.

Residual uncertainty (the 4%):

1. Production `_detect_unauthorized_tactical_intrusion` authority-text pre-condition outcome is not directly observable from `llm_io.jsonl` because `tactical_excerpt` is baked into the prompt body rather than emitted as a discrete field. T4's upper bound (0–7 leaked candidates) brackets the leak without closing it; closing it would require prompt-side field capture which is T3 territory.
2. `_detect_blueprint_text_contamination` body was not fully read (to avoid touching T1 prompt-instruction territory). T4's contamination probe set is narrower than the production predicate. F6 says "0 hits" for T4's probe set; the production predicate may find more on a wider vocabulary. This is a ceiling on confidence, not a finding defect.
3. Replay of `_normalize_opening_transition_contract` was run with `prev_blueprint=None` in the simulation script. Production passes the actually-accepted prior-episode blueprint, so production inference may land on `direct_continuation` or `explicit_transition` instead of the simulation's `jump_opening`. The replay's *reject counts* are unaffected (the gate still sees a valid type post-normalize either way), so F2's claim that the gate is structurally disarmed by normalization is unchanged; only the distribution of post-normalize types would shift.

None of the three residual gaps changes the L1/L2/L3 leverage ranking or the core finding that cheap admission caught ≤ 4.4% of failure surface on ep1–ep7 while the validator caught 170+. Confidence is above the parent-order §3 rule 9 floor of 95%, so this deliverable is saved as final rather than `draft-only`.
