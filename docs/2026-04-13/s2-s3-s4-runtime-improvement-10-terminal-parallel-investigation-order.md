# S2 S3 S4 Runtime Improvement 10-Terminal Parallel Investigation Order

- Date: 2026-04-13
- Scope: current `main@32d6f0c8` S2/S3/S4 runtime quality investigation with primary focus on "Stage3 작가 AI 통과율이 너무 낮다" symptom, structured as a 10-terminal parallel survey
- Mode: survey-only, read-only, 10-way parallel, no code changes, no live rerun, no new queue lane in this order
- Canonical Path: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Baseline Commit: `32d6f0c8b56898fd8a370ae13684043d4cfda91a`
- Baseline Dirty Summary: `dirty: Stage3 producer/ensemble/runtime/validator edits plus live 000_260412_a rerun artifacts, earlier 2026-04-13 audit/survey docs, and config/prompts/ensemble.yaml, config/models.yaml edits already present in worktree`
- Resume Commit: `same-as-baseline` (each terminal must re-`git rev-parse HEAD` at spawn and record drift)
- Side-Effect Coverage: read-only static + frozen live-run artifact reads; no file write outside each terminal's designated deliverable path; no DB/log/queue mutation; no live rerun
- Confidence: `97%` (3-pass audited and live-grep verified)

## 1. Purpose

This order answers one bounded operator question:

- given that Stage3 (특히 작가 AI) 통과율이 여전히 낮고, 현재까지 이미 producer-side `cheap admission`, `opening-transition` parity, `placeholder protagonist_state` 차단, `scenario_density` advisory 처리, three-tranche repair router/contract gate/patch-IR 등이 모두 landed 된 상태인데도 불구하고 ep7/ep8급 에피소드가 여전히 `opening_transition mismatch` + `binding prevalidation repair required` family에서 반복 PASS_WITH_FIX → REJECT → 재생성 사이클에 갇혀 있는 이유는 무엇이고, 남아 있는 고-ROI 개선 축은 어디에 있는가

The question is not "S3 통과율을 즉시 고쳐라". It is "다음 개선 사이클이 근거 있는 증거 위에 서도록 지금 당장 확인 가능한 10개 독립 축을 동시에 조사해 오라".

This order is survey-only and ends with per-terminal written deliverables plus one synthesis pass. It does not authorize code changes, prompt changes, validator retuning, Director retuning, live rerun, or new queue lane creation.

## 2. Why Now

### 2.1 Symptom reconfirmation on current head

The latest live 0_temp.txt tail (`0_temp.txt:400-469`) shows the most recent rerun crashed mid-ep8 with the same reject family the formal `ep8` root-cause survey already described:

- `PASS_WITH_FIX unresolved after 3 patch attempts -> REJECT`
- `fix_scope: full`
- 사유: `binding prevalidation repair required`
- 이슈: `MAJOR | opening_transition | opening_transition.type mismatch: declared 'direct_continuation' vs normalized 'explicit_transition'`

`projects/000_260412_a/logs/pass_rate_monitor.json` shows the live session 통계:

- ep1 → success at `attempt 7`, duration 1,261,839 ms, cost $2.25
- ep2 → `PASS_WITH_WARNING` at `attempt 10`, 2,399,290 ms, $6.61
- ep3 → success at `attempt 6`, 969,722 ms, $3.66
- ep4 → 2 full fail runs, then `PASS_WITH_WARNING` at `attempt 6`, 915,340 ms, $3.38
- ep5 → `PASS_WITH_WARNING` at `attempt 9`, 1,593,364 ms, $5.82
- ep6 → `PASS_WITH_WARNING` at `attempt 10`, 2,264,554 ms, $6.76
- ep7 → `PASS_WITH_WARNING` at `attempt 10`, 2,708,901 ms, $7.36
- ep8 → interrupted mid-run; prior four visible reject cycles inside the same session before process termination

Aggregate reading:

- avg ≥ 8 attempts per Stage3 episode even after every landed producer/repair tranche
- avg ≥ 25–45 minutes wall-clock per Stage3 episode
- cumulative cost ≈ $35+ per 7 episodes before ep8 even closes
- `PASS` (clean) is now the exception, `PASS_WITH_WARNING` is the dominant terminal state

This alone is evidence that the remaining Stage3 failure is **not** "one more cheap-admission tighten away". The producer-validator-runtime coupling is structurally loose against the current contract level.

### 2.2 Why the existing landed tranches did not close the gap

Already on current head:

- `s2-s3-s4-producer-smarts-bounded-3pass-audit.md` (landed)
- `s2-s3-s4-producer-smarts-p2-p3-followup-survey.md` (landed)
- `stage3-ep8-cw-director-root-cause-parallel-survey.md` (landed)
- `stage3-producer-contract-tightening-3pass-audit-and-adversarial-review.md` (landed)
- `stage3-three-tranche-safe-sequencing-plan.md` tranches 1–3 (landed)
- `stage3-cost-first-decision-surface-static-survey.md` Tranche A + B (landed)
- `stage3-producer-adversarial-followup-x3-addendum.md` (landed)

These cover:

- upstream prompt/schema/admission parity (T1/T4 territory — partially)
- repair router extraction, local-fix contract gate, patch IR (T2 territory — partially)
- binding-family static kill (T5 territory — partially)
- P2/P3 shortlist honesty, placeholder rejection, degraded fallback ordering

But none of them has yet independently answered:

1. does the prompt actually **teach** the LLM the current contract in a learnable way, or does it just **declare** it with abstract field names
2. does the retry loop **carry forward** the exact prior failure into the next attempt as a concrete repair directive, or does it restart from a stale base prompt
3. what exactly is **inside** the context packet the producer LLM receives at Phase 2 — is Stage2 arc fully delivered, is prior blueprint delivered, is opening contract delivered, or is the budget burnt on boilerplate
4. for the 62 live Stage3 attempts captured in session/metrics, is the dominant failure **producer drift** or **validator over-strictness** — neither side has been measured against the other with per-attempt evidence
5. do the 5 fan-out candidates (`conservative / balanced / action_focused / dialogue_focused / emotion_focused`) actually produce **different** blueprints, or do they all fail the same contract because they share base context
6. does Director's selection score **correlate** with validator's pass/reject, or does Director pick a contract-broken candidate because its selection rubric does not weigh the binding contract
7. where is cost actually going per episode — ensemble fan-out vs local patch vs full regenerate vs Director compare — and which spend has the lowest ROI
8. is Stage2 arc output concrete enough to anchor Stage3, or is Stage3 starving on generic `setup/progress/climax` beats
9. given imperfect Stage3 blueprint, does Stage4 compound or repair the error — is the Stage4 writer contract meaningfully protective

These are the 10 gaps this order covers, one per terminal.

## 3. Operating Rules (apply to all 10 terminals)

1. **Read-only.** No code edit, no config edit, no test edit, no DB write, no queue mutation, no live rerun, no PR, no git mutation beyond `git rev-parse HEAD` and `git status`.
2. **Survey-only deliverable.** One markdown file per terminal under `docs/2026-04-13/` with a filename matching the per-terminal section below.
3. **Baseline re-check at spawn.** Each terminal must start by running `git rev-parse HEAD` and `git status --short`, then record the actual commit + dirty summary in its own front matter. If the HEAD drifted from `32d6f0c8`, that terminal must note the drift and continue against its actual baseline.
4. **No scope bleed.** A terminal must not investigate a question assigned to another terminal. If a terminal finds evidence that **materially belongs** to another terminal, it records a one-line `cross-terminal pointer` and stops that thread rather than widening its own scope.
5. **No new queue lane.** No terminal may open a new execution SSOT, promote a finding into the active queue, or call for code realization. Findings become execution items only after the synthesis step reviews all 10 deliverables.
6. **No retuning claims.** No terminal may declare "validator is over-strict so relax it" or "prompt should be rewritten so do it" as a standalone conclusion. Claims must be anchored to file:line evidence and framed as candidate hypotheses for the synthesis step.
7. **UTF-8 hygiene.** All deliverables saved as UTF-8. No triple-question placeholders, no `U+FFFD`, no mixed-script mojibake. Console-rendered output must not be the sole evidence anchor — when quoting live-run text, the terminal must also record the source file path + line offsets so the quote can be re-decoded by bytes.
8. **DB max-preservation policy.** No `[:N]` truncation when reading diagnostic / verdict / reason fields from DB. Quote verbatim up to what is needed for evidence.
9. **Confidence floor.** Each terminal must end with a confidence score. Below 95% the terminal must add one extra audit pass before saving. If still below 95%, it must mark the deliverable `draft-only` and enumerate the residual uncertainty.
10. **3-pass audit inside each deliverable.** Per workspace `Document Save Rule`, each terminal runs its own `draft → pass1 → pass2 → pass3 → final save` inside its deliverable file.

## 4. Shared Evidence Anchors (available to every terminal)

Live runtime evidence (frozen, read-only):

- `0_temp.txt` — latest live Stage3 run console capture, most recent tail shows ep8 failure family (`0_temp.txt:400-469`)
- `projects/000_260412_a/logs/pass_rate_monitor.json` — per-attempt pass/fail records with `attempt_key`, `duration_ms`, `token_cost`, `final_verdict`
- `projects/000_260412_a/logs/metrics/metrics_20260413_194343.json` — latest aggregate agent/model stats
- `projects/000_260412_a/logs/quality_metrics.jsonl` — per-call quality metrics stream
- `projects/000_260412_a/logs/runtime_audit_summary.json`
- `projects/000_260412_a/logs/session/ui_events.jsonl` — operator-facing timeline
- `projects/000_260412_a/logs/session/llm_io.jsonl` — LLM input/output pairs
- `projects/000_260412_a/logs/artifacts/stage3/ep_0001..ep_0007/attempt_XX/*.json` — per-attempt fan-out candidates and final selections
- `projects/000_260412_a/plans/arcs/arc_001.txt`, `arc_002.txt` — Stage2 arc tactical truth
- `projects/000_260412_a/plans/blueprints/blueprint_0001.txt..blueprint_0007.txt` — accepted Stage3 blueprints
- `projects/000_260412_a/project_data.db` — full sink-of-truth (read via `sqlite3` in readonly mode only)

Current code owners (read-only):

- `modules/core/response_schemas.py` (1,088 lines)
- `modules/core/stage_cross_stage_contract.py` (360 lines)
- `modules/core/scene_obligation_heuristics.py` (305 lines)
- `modules/core/stage3_orchestrator.py` (3,533 lines)
- `modules/domain/agents/blueprint_ensemble.py` (1,693 lines)
- `modules/domain/agents/three_phase_blueprint_runtime.py` (3,139 lines)
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/domain/agents/unified_blueprint_validator.py` (2,512 lines)
- `modules/domain/agents/arc_ensemble.py` (2,172 lines)
- `modules/domain/agents/chief_writer.py` (2,593 lines)
- `modules/domain/agents/director_ensemble.py` (2,743 lines)
- `modules/domain/agents/stage3_blueprint_patch_ir.py` (211 lines)
- `config/prompts/ensemble.yaml` (475 lines)
- `config/prompts/blueprint_generator.yaml`
- `config/prompts/chief_writer.yaml`
- `config/prompts/director.yaml`
- `config/models.yaml`

Governing context (do not mutate):

- `AGENTS.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- All `docs/2026-04-13/stage3-*.md` surveys

## 5. Terminal Assignment Matrix

| Term | Focus axis | Primary read surface | Primary output file |
|------|-----------|---------------------|--------------------|
| T1 | Producer initial-prompt forensics (does `ensemble.yaml` actually teach the contract?) | `config/prompts/ensemble.yaml`, `blueprint_ensemble.py` prompt assembly | `t1-producer-initial-prompt-forensics.md` |
| T2 | Retry feedback loop audit (does attempt N+1 see attempt N's exact failure + fix directive?) | `three_phase_blueprint_runtime.py` Phase 2/3 retry path, `_Stage3RepairRouter`, `_build_stage3_fix_pack_guidance` | `t2-stage3-retry-feedback-loop-audit.md` |
| T3 | Producer context packet audit (what does the LLM actually see as context, and what is wasted) | `blueprint_ensemble.py` context builder, Stage2 arc handoff, prior-ep blueprint injection | `t3-producer-context-packet-audit.md` |
| T4 | Cheap admission gate effectiveness measurement (post-landing) | `blueprint_ensemble.py` cheap admission gates, `quality_metrics.jsonl`, per-attempt artifacts | `t4-producer-cheap-admission-effectiveness-audit.md` |
| T5 | Validator heuristic true-vs-false-positive audit (opening_transition, tactical_semantic, scenario_density) | `unified_blueprint_validator.py` + `stage_cross_stage_contract.py` vs per-attempt artifact evidence | `t5-validator-heuristic-true-false-positive-audit.md` |
| T6 | Ensemble candidate diversity measurement | `blueprint_ensemble.py` fan-out code + per-attempt `final_blueprint__*.json` candidate family | `t6-ensemble-candidate-diversity-audit.md` |
| T7 | Director vs Validator authority overlap | `director_ensemble.py`, `unified_blueprint_validator.py`, DB/artifact Director verdict vs validator verdict pairing | `t7-director-vs-validator-authority-overlap-audit.md` |
| T8 | Cost-to-outcome attribution per Stage3 spend axis | `metrics/metrics_*.json`, `pass_rate_monitor.json`, `llm_io.jsonl`, DB cost tables | `t8-stage3-cost-attribution-audit.md` |
| T9 | Stage2 → Stage3 handoff quality audit | `arc_ensemble.py`, `plans/arcs/arc_*.txt`, `scene_obligation_heuristics.py`, Stage3 arc intake path | `t9-stage2-to-stage3-handoff-quality-audit.md` |
| T10 | Stage3 → Stage4 handoff + Stage4 writer smarts audit | `chief_writer.py`, `modules/core/writer_template.py`, Stage4 manuscript artifacts, per-ep pass/fail correlation | `t10-stage3-to-stage4-handoff-and-s4-writer-smarts-audit.md` |

Per-terminal deliverables save to `docs/2026-04-13/<filename>` as UTF-8 markdown. Each deliverable must follow the common front matter template in §7.

## 6. Per-Terminal Orders

The order below gives each terminal one bounded question, explicit read surfaces, required analyses, and strict non-goals. Every terminal is independent — none blocks another — so all 10 can spawn simultaneously.

### T1. Producer Initial-Prompt Forensics

Question:

- does `config/prompts/ensemble.yaml` plus the initial-call prompt assembly in `blueprint_ensemble.py` actually **teach** the Stage3 contract (opening_transition, protagonist_state, scene_breakdown structure, tactical_semantic_fidelity, scenario_density) in a form the LLM can learn from, or does it only **declare** abstract field names that an LLM cannot ground without concrete examples?

Required analyses:

1. Read `config/prompts/ensemble.yaml` end-to-end (475 lines) and enumerate:
   - each contract field name the prompt mentions
   - whether a positive example, a negative example, and a concrete "why this matters" sentence are present for each field
   - whether the example vocabulary matches the validator's normalization vocabulary (e.g. does the prompt use `explicit_transition` / `direct_continuation` with the same meaning as `stage_cross_stage_contract.py`)
2. Read `blueprint_ensemble.py` prompt assembly functions — wherever the YAML template is composed into an actual user/system payload for the LLM call. Record which sections are added, in what order, and what per-call variable substitution happens.
3. Cross-check ensemble.yaml against `modules/core/stage_cross_stage_contract.py` normalization rules: for each rule in the contract (opening transition alias normalization, start-location drift, time shift rules, etc.) mark whether the prompt has a corresponding concrete example.
4. Quote 3 concrete prompt passages verbatim that are the weakest — where the LLM is told "make it good" rather than "here is what good looks like". Give file:line anchors.
5. Enumerate the top 5 concrete, minimal prompt-delta candidates (not code changes; pure text deltas) that would most raise the probability the LLM gets the contract right on attempt 1.

Scope IN:

- ensemble.yaml static content and how it is substituted
- per-field contract coverage completeness
- positive / negative / anchor example density
- prompt section ordering

Scope OUT:

- retry-time feedback prompt (that is T2)
- context packet assembly (that is T3)
- validator heuristic correctness (that is T5)
- any proposal to edit ensemble.yaml in code

Non-goals:

- do not claim the prompt is "bad" without showing the specific field + the specific gap
- do not rewrite the prompt — only list minimal text deltas as hypotheses
- do not call for ensemble.yaml deprecation / replacement

Deliverable: `docs/2026-04-13/t1-producer-initial-prompt-forensics.md`.

Confidence floor: `95%`.

### T2. Stage3 Retry Feedback Loop Audit

Question:

- when Stage3 attempt N rejects with a concrete reason like `opening_transition.type mismatch: declared 'direct_continuation' vs normalized 'explicit_transition'`, does attempt N+1 receive the exact prior reason + a concrete fix directive from `_Stage3RepairRouter` / `_build_stage3_fix_pack_guidance`, or does it functionally restart from the same base prompt, so the LLM keeps making the same mistake for 7–10 attempts?

Required analyses:

1. Read `three_phase_blueprint_runtime.py` Phase 2 and Phase 3 retry loops:
   - `_ThreePhaseRetryState` (`three_phase_blueprint_runtime.py:53`)
   - `_Stage3RepairRouter` (`three_phase_blueprint_runtime.py:182`)
   - `_build_stage3_fix_pack_guidance` (`three_phase_blueprint_runtime.py:789`)
   - `_normalize_stage3_fix_pack` (`three_phase_blueprint_runtime.py:470`)
   - `_normalize_stage3_repair_contract` (`three_phase_blueprint_runtime.py:527`)
   - `_build_stage3_local_patch_gate` (`three_phase_blueprint_runtime.py:602`)
2. Trace the data flow: after a reject verdict, which fields end up in the next-attempt prompt payload, and which fields are dropped or compressed along the way.
3. For the latest `0_temp.txt:400-469` ep8 reject cycles, correlate console text ("binding prevalidation repair required", "opening_transition.type mismatch ...") to the concrete retry-payload text the runtime actually sent. If the retry payload cannot be reconstructed from code + logs alone, state that as a visibility gap.
4. Categorize retry paths into:
   - `local patch` (contract-ready, patch-IR eligible)
   - `full regenerate with feedback`
   - `full regenerate without feedback (cold restart)`
   For each category, quantify how often the ep1–ep7 historical runs took that path.
5. Enumerate any case where the same retry attempt receives the same base prompt without carrying the previous failure vocabulary — flag this as a `cold-retry leak`.

Scope IN:

- retry-time prompt assembly
- fix pack / repair contract propagation into the next call
- cold-retry detection
- per-attempt feedback fidelity

Scope OUT:

- initial prompt design (that is T1)
- cheap admission gate (that is T4)
- Director selection rubric (that is T7)
- Stage4 chief writer retry feedback paths (that is T10) — `chief_writer.py` has its own `_build_retry_reuse_feedback_block`, `_build_regeneration_feedback`, `_build_inplace_patch_prompt`, `_build_patch_with_feedback_section`, `_build_retry_history_feedback`; do not score them here
- proposing patch IR expansion — only observe what exists

Non-goals:

- do not propose new runtime code paths; only surface feedback gaps
- do not call for repair router rewrite

Deliverable: `docs/2026-04-13/t2-stage3-retry-feedback-loop-audit.md`.

Confidence floor: `95%`.

### T3. Producer Context Packet Audit

Question:

- what is actually inside the context the Stage3 producer LLM receives at `BlueprintEnsembleGenerator.generate_*` time — Stage2 arc truth (full or summarized?), prior-ep blueprint (which fields?), opening contract normalization vocabulary, bible / work guard / style guide — and which parts are spending the most token budget for the least contract-leverage?

Required analyses:

1. Read `modules/domain/agents/blueprint_ensemble.py` from `class BlueprintEnsembleGenerator` (`blueprint_ensemble.py:272`) down through the context-building methods:
   - wherever Stage2 arc content is pulled in
   - wherever prior-episode blueprint is pulled in
   - wherever `arc_start_state` / opening authority is pulled in
   - wherever work guard / style guide / bible / HUD state is injected
2. For each context section, record:
   - source file or source agent
   - whether it is passed raw or summarized
   - approximate token budget it consumes (estimate from source length)
   - whether it lands in the prompt before or after the contract explanation
3. Cross-check against `llm_io.jsonl` for at least 3 real ep1–ep7 Stage3 calls. Confirm or reject the static inference using real input payloads.
4. Identify the top 3 context sections that are large but do not appear to be directly referenced by any contract rule. These are candidate budget-waste surfaces.
5. Identify the top 3 context sections that are **missing or under-budgeted** relative to the contract the validator will later enforce. These are candidate starvation surfaces.

Scope IN:

- context packet composition at Phase 2 producer call time
- token budget distribution across context sections
- producer-visible vs producer-invisible contract inputs

Scope OUT:

- retry-time feedback (T2)
- validator heuristic surface (T5)
- Director compare context (T7 handles Director)

Non-goals:

- do not claim "remove X from context" without showing that X is both high-cost and low-contract-relevance
- do not call for new context injection — only surface gaps

Deliverable: `docs/2026-04-13/t3-producer-context-packet-audit.md`.

Confidence floor: `95%`.

### T4. Producer Cheap Admission Effectiveness Audit

Question:

- after the landed cheap admission tightening (`_scene_has_meaningful_payload`, `opening_transition` parity, placeholder `protagonist_state` rejection, `_detect_unauthorized_tactical_intrusion`, integrated-scenario floor 800 chars), how many candidates are actually being rejected cheaply before validator spend on the 000_260412_a session, and which failure families are still slipping past cheap admission and churning inside the validator?

Required analyses:

1. Read the current cheap admission code paths in `blueprint_ensemble.py` (current-head line anchors; if the file drifts, anchor by function name):
   - `BlueprintEnsembleGenerator` class entry at `blueprint_ensemble.py:272`
   - `_request_blueprint_generation` at `blueprint_ensemble.py:825`
   - `_scene_has_meaningful_payload` at `blueprint_ensemble.py:862`
   - `_detect_unauthorized_tactical_intrusion` at `blueprint_ensemble.py:970`
   - the scenario-density floor and `opening_transition` rejection sites called from those entry points
2. Reconstruct from `quality_metrics.jsonl` / `llm_io.jsonl` / per-attempt artifacts how many candidates per ep1–ep7 attempt were rejected at cheap admission vs passed through to validator.
3. For each case where a candidate passed cheap admission but later failed in validator:
   - name the validator category that caught it
   - check whether the cheap admission code has any path that **could** have caught the same family earlier
   - if yes, quantify the cheap-vs-expensive ratio gap
4. Build an effectiveness table: per-family catch-rate at cheap admission vs at validator, ep1–ep7.
5. Enumerate the top 3 failure families where cheap admission still has the biggest theoretical leverage and list the concrete code anchors that would need change (do not change them).

Scope IN:

- measured cheap-admission catch rate on live session evidence
- post-landing residual catch gaps
- per-family cheap-admission leverage analysis

Scope OUT:

- initial prompt content (T1)
- retry feedback (T2)
- validator internal correctness (T5)

Non-goals:

- do not propose admission rule edits; only identify leverage gaps
- do not blur "not caught cheaply" with "validator over-strict" — that split is T5's job

Deliverable: `docs/2026-04-13/t4-producer-cheap-admission-effectiveness-audit.md`.

Confidence floor: `95%`.

### T5. Validator Heuristic True/False Positive Audit

Question:

- among the landed validator heuristics that most often block Stage3 (`opening_transition.type` normalization, `tactical_semantic_fidelity` intrusion detection, `scenario_density` threshold, `scene_breakdown` shape rules), which rejects over ep1–ep7 were **true positives** (the candidate really did violate the contract) and which were **false positives** (the candidate was arguably correct but caught by overly sensitive normalization)?

Required analyses:

1. Read the validator heuristic sites (line numbers are current-head dirty-workspace; if the file drifts, anchor by function name):
   - `unified_blueprint_validator.py:2020` opening_transition mismatch site
   - `unified_blueprint_validator.py:2089` empty `protagonist_state` issue emit site
   - `unified_blueprint_validator.py:2324` `_collect_tactical_semantic_fidelity_issues` (function entry; flags unauthorized physical-threat / action invention)
   - `unified_blueprint_validator.py:2388` `_collect_scenario_density_issues` function entry; live emit site is `unified_blueprint_validator.py:2458`
   - `unified_blueprint_validator.py:1808` `_collect_temporal_deictic_drift_issues` (temporal-deictic ending-hook detector)
   - `stage_cross_stage_contract.py:205`, `267`, `296` opening normalization rules
2. For ep1–ep7 reject records in `pass_rate_monitor.json` and per-attempt artifacts, pair each reject reason with the actual candidate payload and judge whether the contract violation was real.
3. Build a per-heuristic table: `true positive` / `false positive` / `ambiguous` counts with file:line evidence per decision.
4. For false-positive candidates, record what the producer intended and why the normalization rule misread it. Do not claim the rule is wrong as a whole — only where per-candidate evidence shows the rule's output conflicts with the Stage2 arc truth.
5. Flag any heuristic where false-positive share exceeds 30% as `calibration candidate` — this is a hypothesis for synthesis, not an implementation directive.

Scope IN:

- heuristic calibration truth on real candidate payloads
- false-positive vs true-positive split
- contract consistency across producer and validator vocabularies

Scope OUT:

- cheap admission (T4)
- Director selection (T7)
- any rule rewrite proposal

Non-goals:

- do not declare a rule "wrong" based on one candidate; require ≥ 3 independent candidates showing the same calibration gap
- do not propose new thresholds — only report the measured false-positive share

Deliverable: `docs/2026-04-13/t5-validator-heuristic-true-false-positive-audit.md`.

Confidence floor: `95%`.

### T6. Ensemble Candidate Diversity Audit

Question:

- when `BlueprintEnsembleGenerator` fans out 5 candidates (`conservative`, `balanced`, `action_focused`, `dialogue_focused`, `emotion_focused`), do those candidates actually produce meaningfully different blueprints, or do they all share the same base drift (e.g. all declare `direct_continuation`, all miss the same scene beat, all copy the same opening_transition mistake) so the ensemble spend is near-wasted on contract-level diversity?

Required analyses:

1. Read the fan-out code in `blueprint_ensemble.py` — how each strategy is parameterized and how per-strategy prompt deltas differ.
2. Walk `projects/000_260412_a/logs/artifacts/stage3/ep_0001..ep_0007/attempt_XX/` and pair the 5 candidate files per attempt. For each attempt where all candidates are present:
   - compare `opening_transition.type`
   - compare `protagonist_state` shape
   - compare `scene_breakdown` scene count / ordering
   - compare `integrated_scenario` opening 400 characters
3. Define a diversity score per attempt: the share of candidates that **differ on contract-relevant fields**, not just on stylistic surface.
4. For attempts where all 5 candidates share the same contract failure, log them as `ensemble-wasted` rejections — the fan-out did not help the contract at all.
5. Cross-check whether `ensemble-wasted` attempts correlate with later-attempt full regenerate cycles.

Scope IN:

- fan-out strategy parameterization
- per-candidate divergence on contract fields
- ensemble ROI under contract stress

Scope OUT:

- per-strategy prompt text design (T1)
- Director selection rubric (T7)

Non-goals:

- do not recommend removing an ensemble strategy — only measure its marginal diversity
- do not treat stylistic-only diversity as contract-level diversity

Deliverable: `docs/2026-04-13/t6-ensemble-candidate-diversity-audit.md`.

Confidence floor: `95%`.

### T7. Director vs Validator Authority Overlap Audit

Question:

- when Director says "이 후보가 가장 잘 썼다" but validator still rejects on `binding prevalidation repair required`, does Director's selection rubric even read the same contract fields (opening_transition, protagonist_state, tactical_semantic, scene structure) as the validator, or does Director pick on prose/voice heuristics while the binding contract is only seen after selection — and how much Stage3 churn is downstream of that rubric mismatch?

Required analyses:

1. Read `director_ensemble.py` end-to-end, in particular the comparator and scoring path. Record which fields Director explicitly scores and which fields it does not.
2. Read `unified_blueprint_validator.py` prevalidation path (`_python_pre_validate` at `unified_blueprint_validator.py:1351`; called from `unified_blueprint_validator.py:561` and `unified_blueprint_validator.py:776`) and identify which fields block PASS before any Director call.
3. Map "Director-weighted fields" ∩ "validator-blocking fields" and record the gap. Every field that validator blocks on but Director does not weigh is a rubric leak.
4. For ep1–ep7 attempts, pull Director verdict + validator verdict pairs from DB / artifacts. Classify:
   - `director and validator agree PASS`
   - `director PASS, validator REJECT on category X` (rubric leak)
   - `director REJECT, validator would have PASSED` (director over-reject)
   - `director REJECT, validator REJECT` (consistent)
5. Quantify rubric-leak share per ep and per category.

Scope IN:

- Director comparator rubric composition
- validator prevalidation surface
- pairwise verdict agreement on real attempts

Scope OUT:

- validator heuristic correctness itself (T5)
- cheap admission (T4)
- Director prompt rewrite proposal

Non-goals:

- do not claim Director is "dumb" — measure the rubric gap and state it neutrally
- do not propose a new comparator rubric; only list gap categories

Deliverable: `docs/2026-04-13/t7-director-vs-validator-authority-overlap-audit.md`.

Confidence floor: `95%`.

### T8. Stage3 Cost-To-Outcome Attribution Audit

Question:

- for the 000_260412_a session (ep1–ep7 closed, ep8 interrupted), exactly where is the $35+ Stage3 spend going — break total cost down into `ensemble fan-out`, `local patch repair`, `full regenerate repair`, `Director compare + judge`, and any other distinguishable category — and which spend axis has the lowest cost-to-successful-contract ratio?

Required analyses:

1. Read `projects/000_260412_a/logs/metrics/metrics_*.json` and `pass_rate_monitor.json` records end-to-end. Record per-ep `token_cost`, `duration_ms`, `attempt_num`, `final_verdict`.
2. Cross-reference against `llm_io.jsonl` or whatever per-call cost attribution exists in the DB to split each ep's total spend by call type. If the data is insufficient to split cleanly, state the visibility gap.
3. Build the attribution table per ep:
   - ensemble fan-out cost
   - repair / regenerate cost
   - Director compare + judge cost
   - StateExtractor / other overhead
4. Compute `$ / successful PASS` and `$ / PASS_WITH_WARNING` per spend axis.
5. Identify the top spend axis by absolute dollars and the bottom spend axis by ROI. Tag both as cost-reduction hypotheses for synthesis.

Scope IN:

- per-ep spend breakdown
- ROI ranking across spend axes
- visibility gaps in cost attribution

Scope OUT:

- any rate-negotiation or vendor-model argument
- Director rubric (T7)
- validator heuristics (T5)

Non-goals:

- do not predict savings without a matching current-state cost anchor
- do not propose a concrete model swap — only surface ROI gaps

Deliverable: `docs/2026-04-13/t8-stage3-cost-attribution-audit.md`.

Confidence floor: `95%`.

### T9. Stage2 → Stage3 Handoff Quality Audit

Question:

- is Stage2 actually giving Stage3 concrete enough tactical truth (specific entities, specific beat obligations, specific cause-effect ordering), or is Stage3 starving on generic `setup / progress / climax` beats — and does the handoff weakness correlate with specific Stage3 failure families (opening_transition mismatch, tactical_semantic drift, scene_breakdown shortage)?

Required analyses:

1. Read `arc_ensemble.py` and the Stage2 → Stage3 handoff boundary:
   - arc output schema
   - how `episode_details` beats are assembled
   - how `scene_obligation_heuristics.py:has_actionable_obligation_text` filters them
2. Open `projects/000_260412_a/plans/arcs/arc_001.txt` and `arc_002.txt` and judge per-ep beat concreteness:
   - does each beat name concrete entities / places / actions
   - or does it stay at generic labels the Stage3 validator cannot later verify
3. For ep1–ep7, pair Stage2 arc beat content with the Stage3 reject families that actually fired. Flag every case where the arc beat was generic and Stage3 later failed on a rule that needed concrete grounding.
4. Record the arc → blueprint starvation pattern: which reject families are most often downstream of generic arc beats.
5. List the top 3 cheap arc-side strengthening candidates for synthesis — but strictly as hypotheses, not as arc-rewrite proposals.

Scope IN:

- Stage2 arc concreteness measurement
- per-ep handoff quality
- cross-stage starvation correlation

Scope OUT:

- Stage2 internal ensemble scoring (only the output matters here)
- Director selection (T7)

Non-goals:

- do not propose rewriting the arcs themselves; only score their concreteness
- do not blame Stage2 for every Stage3 fail; show the correlation before the claim

Deliverable: `docs/2026-04-13/t9-stage2-to-stage3-handoff-quality-audit.md`.

Confidence floor: `95%`.

### T10. Stage3 → Stage4 Handoff + Stage4 Writer Smarts Audit

Question:

- given that Stage3 often closes as `PASS_WITH_WARNING`, does Stage4 (chief writer + manuscript runtime) (a) actually rescue the remaining contract drift, (b) silently compound the drift into manuscript, or (c) reject-and-retry like Stage3 — and are the current Stage4 writer-side contract gates inside `_build_manuscript_contract_diagnostics` (`chief_writer.py:194`) and `_finalize_generate_ensemble_candidates` (`chief_writer.py:857`) strong enough to prevent downstream bleed?

Required analyses:

1. Read `chief_writer.py` admission and retry paths (current-head line anchors; if the file drifts, anchor by function name):
   - `_build_manuscript_contract_diagnostics` at `chief_writer.py:194` (manuscript contract diagnostic)
   - `_finalize_generate_ensemble_candidates` at `chief_writer.py:857` (degraded-mode admission and ordering)
   - downstream candidate handoff invocation around `chief_writer.py:1040`
   - Stage4 retry-time feedback assembly: `_build_retry_reuse_feedback_block` at `chief_writer.py:117`, `_build_regeneration_feedback` at `chief_writer.py:1330`, `_build_fix_pack_guidance` at `chief_writer.py:1506`, `_build_inplace_patch_prompt` at `chief_writer.py:1945`, `_build_patch_with_feedback_section` at `chief_writer.py:2232`, `_build_retry_history_feedback` at `chief_writer.py:2382`
2. Read `modules/core/writer_template.py` and the Stage4 runtime entry points touched by recent tranches.
3. For ep1–ep7, pair the Stage3 final verdict (`PASS`, `PASS_WITH_WARNING`, `FAILED`) with the Stage4 verdict on the same ep. Classify each pair:
   - Stage3 PASS → Stage4 PASS clean
   - Stage3 PASS_WITH_WARNING → Stage4 PASS (rescue)
   - Stage3 PASS_WITH_WARNING → Stage4 PASS_WITH_WARNING (bleed)
   - Stage3 PASS_WITH_WARNING → Stage4 REJECT / retry churn
4. Identify any Stage4 writer contract family that is still soft (heuristic, advisory, non-blocking).
5. List the top 3 Stage4 writer-side hardening candidates for synthesis, with file:line anchors.

Scope IN:

- Stage4 writer admission gate strength
- Stage3 → Stage4 verdict carryover
- manuscript bleed vs rescue behavior

Scope OUT:

- Stage3 internal behavior (T1–T8)
- full Stage4 semantic judge redesign

Non-goals:

- do not conflate Stage4 template errors with Stage3 blueprint errors; keep the boundary clean
- do not propose full Stage4 contract rewrite; surface the gaps only

Deliverable: `docs/2026-04-13/t10-stage3-to-stage4-handoff-and-s4-writer-smarts-audit.md`.

Confidence floor: `95%`.

## 7. Common Per-Terminal Deliverable Template

Every per-terminal deliverable MUST begin with this front matter:

```
# <Terminal Title>

- Parent Order: `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- Terminal: T<N>
- Date: 2026-04-13
- Mode: survey-only, read-only, parallel
- Baseline Commit (at spawn): `<git rev-parse HEAD>`
- Baseline Dirty Summary: `<git status --short summary>`
- Resume Commit: `<same or drift>`
- Resume Drift Summary: `<none or delta>`
- Side-Effect Coverage: `read-only static + frozen live-run artifact reads; no mutation`
- Confidence: `<final number after 3-pass>%`
```

Then body sections (each terminal may vary content but must keep these headings):

1. `Purpose` — the one bounded question verbatim from §6
2. `Evidence Anchors` — the exact file paths the terminal read, with anchor line ranges where relevant
3. `Findings` — numbered findings, each with file:line anchor + severity tag (`TP` / `FP` / `gap` / `leak` / `waste` / `hypothesis`)
4. `Cross-Terminal Pointers` — one-liners pointing at evidence that **belongs** to another terminal
5. `Hypothesis Candidates For Synthesis` — explicitly labeled as candidates, not directives
6. `3-Pass Audit Record` — Pass 1 / Pass 2 / Pass 3 notes
7. `Final Confidence` — single number

All findings must carry a file:line or artifact:path anchor. Findings without anchors must be marked `unanchored — lower confidence`.

## 8. Non-Overlap Invariants

To keep 10 terminals from fighting over the same surface:

1. T1 is the **only** terminal that judges initial-prompt content quality. T2/T3/T7 may read the prompt for flow but must not rank its quality.
2. T2 is the **only** terminal that judges retry-time feedback fidelity. T1/T3 must not touch the retry loop.
3. T3 is the **only** terminal that measures context-packet composition. T1 only reads the static prompt template; T3 reads the fully assembled payload.
4. T4 is the **only** terminal that scores cheap admission effectiveness. T5 must not rank cheap admission. T4 must not rank validator heuristics.
5. T5 is the **only** terminal that judges validator heuristic calibration. T4/T6 must not.
6. T6 is the **only** terminal that measures ensemble diversity. T1/T7 must not.
7. T7 is the **only** terminal that judges Director/validator rubric overlap. T5/T6 must not.
8. T8 is the **only** terminal that attributes cost. T1–T7 may cite cost numbers only as supporting evidence, never as a ranked conclusion.
9. T9 is the **only** terminal that ranks Stage2 handoff quality. T1–T7 may cite Stage2 content only as context.
10. T10 is the **only** terminal that judges Stage3 → Stage4 bleed. T1–T9 must not.

Any finding that would violate these invariants becomes a `Cross-Terminal Pointer` instead.

## 9. Synthesis Step (after all 10 deliverables land)

After all 10 deliverables are saved, one separate synthesis pass (not part of this order) should:

1. Read every `Hypothesis Candidates For Synthesis` section across the 10 files.
2. Merge overlapping hypotheses and rank by evidence weight (number of independent terminals pointing at the same gap).
3. Produce one `SYNTHESIS` document that names the top 3–5 bounded runtime improvement tranches for the next decision. That synthesis document is NOT part of this order and must be its own separate request.
4. No queue lane is opened by this order; the synthesis step is the earliest moment a new execution proposal can be raised.

## 10. Strict Non-Goals For This Entire Order

- no code changes, no config changes, no prompt changes, no YAML changes, no schema changes
- no live rerun, no fresh proof wave, no canary
- no validator / Director / chief writer retuning
- no model swap, no tier change, no cost negotiation
- no new execution SSOT creation, no new queue lane
- no git mutation beyond `rev-parse` and `status`
- no pytest run beyond what is already committed (terminals must not spawn new test files)
- no DB write; DB access must be sqlite readonly (`file:...?mode=ro`) or read-only reads
- no operator push / PR / merge

If any terminal finds it needs to break a non-goal to answer its question, it must stop and raise the blocker as a cross-terminal pointer to the synthesis step.

## 10b. Operator Spawn Runbook

The 10 terminals are spawn-independent — none waits on another, none reads another's deliverable. Recommended spawn pattern:

1. Open 10 terminals (or 10 fresh assistant sessions). Each one starts fresh against `C:\Users\PC\Desktop\글도비`.
2. Hand each terminal the same parent order file path (`docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`) plus a single sentence saying `너는 T<N>이다. §6의 T<N> 섹션과 공통 §3 / §4 / §7 / §8 / §10 만 따르면 된다.` where `<N>` is 1 through 10.
3. Each terminal:
   - re-runs `git rev-parse HEAD` and `git status --short` and records both
   - reads only its assigned T<N> section plus the shared sections (§3 operating rules, §4 evidence anchors, §7 deliverable template, §8 non-overlap invariants, §10 strict non-goals)
   - performs its analyses inside its scope only
   - drafts → 3-pass audits → final-saves its single deliverable file under `docs/2026-04-13/t<N>-*.md`
   - exits without touching any other terminal's deliverable
4. The synthesis pass (§9) is a separate request and only runs after all 10 deliverables are saved. Synthesis is not part of this order.

A terminal that finishes early should NOT pick up another terminal's job. Picking up another terminal's job violates non-overlap invariants (§8) and would corrupt the synthesis step.

## 11. Side-Effect Coverage Summary

- file writes: only the 10 per-terminal deliverables, each at its `docs/2026-04-13/t<N>-*.md` path, plus any final save of this parent order file
- DB writes: none
- log writes: none
- cache / global state mutation: none
- queue membership: unchanged
- git state: unchanged
- live runtime: unchanged

## 12. 3-Pass Audit Record (for this parent order file)

### Pass 1. Structure and scope
- kept the document strictly survey-only
- bounded to 10 non-overlapping terminal axes
- explicit non-goals and non-overlap invariants
- per-terminal deliverable template included
- synthesis step pushed out of this order (separate step)

### Pass 2. Evidence and consistency
- matched symptom re-read (`projects/000_260412_a/logs/pass_rate_monitor.json`, `0_temp.txt:400-469`, `projects/000_260412_a/logs/metrics/metrics_20260413_194343.json`) against the existing 2026-04-13 landing surveys so this order does not re-ask already-closed questions
- verified that each terminal's primary read surface exists on disk at current head, then ran live grep against actual code to correct line drift between earlier survey claims and the current dirty workspace:
  - `_python_pre_validate` is at `unified_blueprint_validator.py:1351` (earlier ep8 survey said `1034`; corrected here)
  - temporal-deictic detector function entry is at `unified_blueprint_validator.py:1808` (earlier text said `1810`; corrected here)
  - `_collect_tactical_semantic_fidelity_issues` is at `unified_blueprint_validator.py:2324` (earlier `2379` text described the same family but pointed deeper into the function body; corrected here)
  - `_scene_has_meaningful_payload` is at `blueprint_ensemble.py:862` (earlier producer-smarts audit said `807`; corrected here)
  - `_finalize_generate_ensemble_candidates` is at `chief_writer.py:857` (earlier `261/811` were stale survey anchors; corrected here)
  - all other cited line anchors (`three_phase_blueprint_runtime.py:53/182/470/527/602/789`, `blueprint_ensemble.py:272/825/970`, `unified_blueprint_validator.py:2020/2089/2458`, `chief_writer.py:117/194/1040/1330/1506/1945/2232/2382`) were verified live and stand
- verified that the 10 axes jointly cover the four earlier 2026-04-13 surveys' residuals without duplicating them
- kept every claim anchored to file:line, function name, or artifact path
- noted that the workspace is dirty at spawn time, so each terminal must re-anchor by function name if a citation drifts under further edits

### Pass 3. Execution and readability
- terminal assignment matrix up front (§5) so operator can spawn 10 processes quickly
- each terminal has (question, scope IN/OUT, required analyses, non-goals, deliverable path, confidence floor)
- common deliverable template (§7) makes synthesis trivial
- non-overlap invariants (§8) prevent terminals from stepping on each other
- strict non-goals (§10) prevent scope creep
- operator spawn runbook (§10b) added so the user can launch the 10 terminals with a single short instruction per terminal
- T2 vs T10 boundary made explicit: Stage3 retry feedback (`three_phase_blueprint_runtime.py`) is T2-only, Stage4 retry feedback (`chief_writer.py:117/1330/1506/1945/2232/2382`) is T10-only — added to T2's Scope OUT so the two terminals do not double-audit chief_writer
- T10 question text now anchors on stable function names (`_build_manuscript_contract_diagnostics` at `chief_writer.py:194` and `_finalize_generate_ensemble_candidates` at `chief_writer.py:857`) rather than the stale `chief_writer.py:239 / 261` anchors that earlier surveys used

## 13. Final Confidence

`97%` after the 3-pass audit above plus the live grep verification round. Residual uncertainty: whether T8 (cost attribution) can fully split per-call cost from the current DB/metrics sinks — that is flagged as an explicit visibility gap for T8 itself to report on, not a defect in this order.
