# Stage234 Nonwuxia State-Lock Overreach Bounded Survey

Date: 2026-04-06
Status: final
Canonical Path: `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-bounded-survey.md`
Order File: `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md`
Source Docs:
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane1-stage2-origin.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane2-stage3-carryover.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane3-stage4-opening-authority.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane4-stage4-chainlink-postpass.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane5-runtime-evidence-and-tests.md`
Evidence Artifacts:
- `0_temp.txt`
- `tests/test_arc_ensemble_lane_a.py`
- `tests/test_continuity_pin_guard.py`
- `tests/test_stage4_preflight_continuity.py`
- `tests/test_stage4_context_builder.py`
Side-Effect Coverage:
- Stage2 prompt wording and deterministic scoring
- Stage3 constraint carryover and blueprint prompt authority
- Stage4 opening authority, immutable-fact intake, and chain_link persistence
- runtime/operator reject wording and test codification
Confidence: `96%`
3-Pass Audit: `completed`
Commit State:
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8`
- Baseline Dirty Summary: `dirty: 5 untracked lane survey docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Answer First

The non-wuxia fatigue / recovery problem is real, operator-facing, and genuinely cross-stage, but the ownership is not flat.

- `Stage2` is the primary producer of the overreach.
- `Stage4` is the primary hardening and stickiness layer.
- `Stage3` is mostly a passive carrier with one bounded amplification seam.
- `natural healing` already exists in the codebase, but it is not the authority that currently governs `V60.10`, `recovery_scene_required`, opening carryover wording, or chain-link persistence.

The strongest merged reading is:

- soft non-wuxia fatigue is being treated too often like hard continuity debt
- the current system does not consistently distinguish `hard injury` from `soft fatigue`
- the smallest coherent future repair is not `prompt-only`
- the best future repair shape is a `Stage2 + Stage4 dual-owner patch` anchored by a `policy split between hard injury and soft fatigue`

Severity is `P1`.

Reason:

- a live investment-fiction run produced a Director REJECT for missing an explicit recovery beat around `신경계 피로 Moderate`
- the retry passed once the forced recovery framing was added
- the system therefore creates false hard-fail pressure and measurable rerun cost even though the work is recoverable

This survey is still `survey-only`. It does not authorize code changes.

## 2. Scope

Included:

- the five lane surveys required by the audit order
- Stage2 producer surfaces
- Stage3 carryover and blueprint authority surfaces
- Stage4 opening authority and post-pass chain-link persistence
- runtime operator evidence and tests that codify the behavior

Excluded:

- code patching
- `docs/temp` mutation
- new execution SSOT promotion in this document
- fresh live run or DB audit beyond the inspected lane evidence

## 3. Merged Findings By Required Bucket

### 3.1 Producer-Side Hardening

The Stage2 producer path is the first real owner of the overreach.

Confirmed producer-side hardening surfaces:

- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/state_extractor.py`
- `config/prompts/analyst.yaml`
- `modules/domain/agents/analyst_prompts.py`
- `tests/test_arc_ensemble_lane_a.py`

Merged reading:

- `[NR-1]` correctly says mental fatigue is not physical injury and can recover through ordinary activity
- but the same block then demands an explicit opening recovery action and frames repeated non-recovery as reject-worthy
- `_collect_non_wuxia_recovery_issues()` hardens this further with deterministic scoring
- the token set is too broad and can treat ordinary elapsed time or waiting language as fatigue pressure
- `state_extractor` injects `recovery_scene_required` and `must_start_with` without a non-wuxia genre split
- the `V60.10 STATE LOCK` formatter wraps the result in `즉시 REJECT` style language

So Stage2 already contains the central contradiction:

- the codebase knows soft fatigue should be naturally recoverable
- but the producer path still emits it as a structured opening obligation

Natural-healing surfaces already present on the producer side:

- `modules/domain/agents/four_phase_arc_generator.py` advisory downgrade for mental fatigue
- `modules/domain/agents/four_phase_arc_generator.py` injury sanitization between arcs
- `modules/domain/agents/constraint_compiler.py` fallback reset behavior

Those surfaces are real, but they do not currently control the Stage2 producer authority path that generates the false hardening.

### 3.2 Stage3 Handoff Amplification

Stage3 is not the main owner of this problem.

Confirmed Stage3 surfaces:

- `modules/core/stage3_orchestrator.py`
- `modules/core/continuity_pin_guard.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`

Merged reading:

- `stage3_orchestrator.py` itself does not contain native fatigue or recovery hardening logic
- `apply_continuity_pins()` is narrow, annotation-oriented, and not the source of the fatigue symptom
- the real Stage3 risk is the carryover supply chain:
  - genre-blind inherited injury passthrough in `blueprint_constraint_compiler.py`
  - Band 2 placement of Stage2 `constraint_summary` inside `blueprint_ensemble.py`
  - strong prev-blueprint wording that tells the LLM not to generate contradictions

So Stage3 is best classified as:

- not a primary producer
- not the main enforcer
- a passive carrier that can amplify Stage2 overreach if Stage2 has already encoded soft-fatigue recovery pressure as hard constraint text

This matters because it narrows the future fix:

- Stage3 orchestrator changes are probably unnecessary
- a bounded normalization seam exists in the constraint compiler and prompt formatter if Stage2 output keeps arriving over-hardened

### 3.3 Stage4 Intake Hardening

Stage4 is the strongest current opening-hardening layer.

Confirmed Stage4 intake surfaces:

- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/continuity_pin_guard.py`
- `modules/core/constitutional_checker.py`
- `tests/test_stage4_preflight_continuity.py`
- `tests/test_stage4_context_builder.py`

Merged reading:

- `[Stage4 Opening Scene Authority]` uses genre-blind `hard canon` language
- carryover fields like `pending_actions`, `location`, and `time_marker` are framed as things to `honor`, `resolve`, or explicitly transition from
- the opening-authority packet is injected at tier-0 priority
- the wording does not distinguish hard injury, soft fatigue, routine room-to-room movement, and ordinary business carryover
- Stage4 preflight has no fatigue-specific relief valve

This means Stage4 is where soft carryover becomes operationally close to hard canon for the manuscript writer, even when the underlying condition is mild or genre-ordinary.

The continuity pin guard itself is not the problem here. The stronger problem is the surrounding authority language that wraps carryover into mandatory opening behavior.

### 3.4 Stage4 Post-Pass Persistence Hardening

Stage4 post-pass persistence is a second independent owner of the overreach.

Confirmed post-pass surfaces:

- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_immutable_fact_contract.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_stage4_context_builder.py`

Merged reading:

- chain-link extraction is genre-blind and lumps `부상/피로/상태` into one free-text `physical_state` field
- persistence has no soft/hard distinction
- re-load uses a `반드시 이어받을 것` header
- `pending_actions` is the strongest overreach channel because it is promoted into:
  - writer authority context
  - opening-scene authority
  - immutable-fact style contradiction logic
- `physical_state` is weaker than `pending_actions`, but it is still effectively normative because it sits under mandatory carryover language

The schema-level issue is important:

- the current chain-link structure has no `binding`, `severity`, or `decay` concept
- because of that, mild fatigue and plot-critical obligations travel through the same pipe

So the post-pass layer is not a passive recorder. It materially contributes to sticky false carryover.

### 3.5 Runtime Evidence And Operator Symptom Confirmation

The runtime evidence confirms this is not just a source-level hypothesis.

Confirmed operator symptom anchors:

- `0_temp.txt`
- `tests/test_arc_ensemble_lane_a.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_continuity_pin_guard.py`
- `tests/test_stage4_preflight_continuity.py`

Merged reading:

- a real investment-fiction run produced a Director REJECT citing `V60.10 STATE LOCK`
- the cited defect was not severe bodily injury but `신경계 피로 Moderate`
- the correction demanded an early recovery or rest depiction
- once the forced recovery framing was added, the arc passed

This confirms three things:

1. the issue is operator-facing, not theoretical
2. the system can self-correct, so this is not `P0`
3. the cost is still real because false hardening burns retries, time, and opening-scene bandwidth

Lane 5 also confirms that the currently parked temp execution docs do not directly cover this specific symptom. This is a fresh bounded seam, not a duplicate of the existing queue language.

## 4. Answers To The Audit Questions

### 4.1 Is the overreach really present in Stage2, Stage3, and Stage4?

Yes, but unevenly.

- `Stage2`: yes, primary producer
- `Stage3`: yes, but mostly as passive carrier / formatter
- `Stage4`: yes, primary hardener and sticky persister

The problem should not be described as `Stage2-only`.

### 4.2 Which surfaces turn soft carryover into hard canon?

The strongest surfaces are:

- Stage2 `V60.10` formatting and `recovery_scene_required`
- Stage2 non-wuxia recovery scoring in `arc_ensemble.py`
- Stage3 Band 2 carryover of Stage2 `constraint_summary`
- Stage4 `[Stage4 Opening Scene Authority]`
- Stage4 chain-link re-injection and immutable-fact style carryover handling

### 4.3 Where is natural healing already recognized, and where is it overwritten or ignored?

Already recognized:

- Stage2 advisory mental-fatigue downgrade
- inter-arc injury reset behavior
- some non-wuxia carveout wording in prompts

Ignored or re-hardened:

- `recovery_scene_required` generation
- `V60.10` reject-threat prompt formatting
- deterministic opening recovery penalty
- Stage4 opening authority wording
- Stage4 chain-link persistence without soft/hard distinction

### 4.4 Which non-wuxia conditions are currently treated too hard?

The merged survey supports this list:

- mild fatigue
- stress
- burnout-like residue
- headache or overwork-like non-normal physical state
- ordinary elapsed-time carryover that gets interpreted as fatigue pressure
- mundane pending actions that should not be treated like plot-critical unfinished obligations

### 4.5 Which files and tests encode the overreach?

Primary owner files:

- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/state_extractor.py`
- `config/prompts/analyst.yaml`
- `modules/domain/agents/analyst_prompts.py`
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_immutable_fact_contract.py`

Primary codifying tests:

- `tests/test_arc_ensemble_lane_a.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_preflight_continuity.py`
- `tests/test_continuity_pin_guard.py`

### 4.6 Is this mainly prompt wording, deterministic pinning, post-pass persistence, consumer authority, or cross-stage owner collision?

Mainly:

- Stage2 prompt wording
- Stage2 deterministic scoring and constraint generation
- Stage4 consumer authority
- Stage4 post-pass persistence
- cross-stage owner collision between natural-healing logic and stronger carryover authority surfaces

Not mainly:

- Stage3 deterministic continuity pinning

### 4.7 What is the smallest future patch surface?

The smallest coherent fix is:

- a `Stage2 + Stage4 dual-owner patch`
- driven by an explicit `hard injury vs soft fatigue` policy split

Why not `prompt-only`:

- Stage2 deterministic scoring is part of the problem
- Stage4 chain-link schema and carryover enforcement are part of the problem

Why not `Stage2-only`:

- even if Stage2 stops over-producing the pressure, Stage4 still lacks a soft/hard distinction for carryover and persistence

Why not `Stage4-only`:

- the live symptom begins upstream when Stage2 emits `recovery_scene_required`, `V60.10`, and non-wuxia recovery penalties

## 5. Future Repair Classification

Best fit:

- `Stage2 + Stage4 dual-owner patch`
- with a `policy split between hard injury and soft fatigue`

Possible bounded Stage3 follow-up:

- normalize inherited injury/fatigue carryover in `blueprint_constraint_compiler.py`
- soften only the Stage3 supply-chain formatting that still forwards Stage2 overreach unchanged

Not recommended as standalone strategies:

- `prompt-only normalization`
- `Stage3-first patch`
- `continuity-pin-only patch`

## 6. Execution Consequence

This survey is strong enough to justify a future execution order.

Recommended future implementation shape:

1. Stage2 normalization
   - split true injury from soft fatigue when deriving `recovery_scene_required`
   - soften or narrow the non-wuxia opening recovery penalty
   - keep natural healing valid

2. Stage4 normalization
   - add soft/hard semantics to carryover intake and chain-link persistence
   - stop treating mild fatigue and routine pending actions like hard canon by default

3. Optional Stage3 seam
   - only if Stage2 output still arrives over-hardened at the constraint compiler boundary

This document itself does not promote or write an execution SSOT. It only establishes that such a promotion would now be evidence-backed.

## 7. Boundaries

- no code changes were made
- no `docs/temp` files were edited
- no closure claim is made
- no claim is made that every non-wuxia recovery warning is false

The bounded claim is narrower:

- the current system over-hardens some non-wuxia fatigue / recovery / opening continuity cases enough to create real false REJECT pressure

## 8. 3-Pass Audit Record

Pass 1:

- verified the merged document stays within the audit-order scope
- grouped findings by required bucket instead of file dump
- kept the document as survey-only, not execution SSOT

Pass 2:

- reconciled all five lane outputs into one owner map
- kept only findings supported by live lane evidence
- recorded minimal commit-state metadata per contract

Pass 3:

- answered the audit order's required questions directly
- made the future repair shape explicit without authorizing code changes
- checked canonical path and queue boundaries

Estimated confidence before save: `96%`
