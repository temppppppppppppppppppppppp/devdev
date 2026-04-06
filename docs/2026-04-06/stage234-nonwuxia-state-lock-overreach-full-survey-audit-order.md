# Stage234 Nonwuxia State-Lock Overreach Full Survey Audit Order

Date: 2026-04-06
Status: ready_for_parallel_read_only_survey
Canonical Path: `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md`
Doc Type: system-track parallel survey order
Mode: survey-only, read-only, no code changes
Audit Authority: Codex 3-pass audited before save
Temp Mirror Path: not applicable

## 1. Answer First

This order exists to determine whether the current `non-wuxia fatigue / recovery / opening continuity` behavior is a `Stage2-local quirk` or a `shared Stage2 -> Stage3 -> Stage4 contract overreach`.

The current operator concern is narrow and explicit:

- preserve `natural healing`
- do not immediately patch code
- determine whether investment / modern business-power works are being over-bound by the same continuity machinery that is more appropriate for severe physical injury or wuxia-native exhaustion
- identify the exact owner surfaces before any implementation order is promoted

This survey is not a patch order. No code, config, DB, artifact, or queue-state mutation is allowed.

## 2. Operator Intent Snapshot

The operator is specifically worried about Director feedback of this shape:

- mild or genre-ordinary fatigue is treated like a hard continuity lock
- an investment / office / business-power arc gets rejected because the opening does not explicitly stage a recovery beat
- `natural healing` exists in parts of the system, but adjacent prompts, pins, or consumers may still escalate non-critical fatigue into de facto hard-fail behavior

The operator does **not** want:

- natural healing removed
- immediate implementation
- a generic broad repo audit that loses the concrete symptom

## 3. Survey Questions

The merged survey must answer all of the following:

1. Is the observed overreach really present in `Stage2`, `Stage3`, and `Stage4`, or only in a subset?
2. Which surfaces currently turn `soft carryover` into `hard canon`?
3. Where is `natural healing` already recognized, and where is that recognition later overwritten, ignored, or re-hardened?
4. For non-wuxia works, which conditions are currently treated as hard when they should likely be soft advisory?
5. Which exact files, prompts, tests, DB anchors, artifacts, or docs encode the overreach?
6. Is the issue primarily `prompt wording`, `deterministic pinning`, `post-pass persistence`, `consumer authority`, or `cross-stage owner collision`?
7. What is the smallest future patch surface that could preserve natural healing while stopping false hard-fail pressure?

## 4. Non-Negotiables

- preserve `natural healing` as a valid system behavior
- do not conflate `mental fatigue / stress / overwork / waiting / mild headache / ordinary exhaustion` with `physical injury / structural damage / true mobility loss`
- do not patch code in this order
- do not write to `docs/temp/`
- do not write the final merged survey from multiple terminals
- do not overclaim beyond inspected evidence

## 5. Required First Read

Every lane must read these first:

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. this order doc

## 6. Optional Prior Art

These are optional context aids, not required first reads:

- `docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`

Use them only to avoid duplicating known queue context. Live code and live artifacts win.

## 7. Included Scope

Default included surfaces:

- prompt and policy wording
- deterministic pinning / continuity patching
- cross-stage context handoff
- chain-link extraction / persistence / consumption
- tests that codify the current behavior
- real operator-facing evidence such as `0_temp.txt`
- prior runtime or canary evidence when directly relevant

Minimum side-effect categories to inspect:

- prompt injection / prompt builder surfaces
- blueprint patching / preflight mutation surfaces
- manuscript post-pass extraction and anchor persistence
- DB anchor or state handoff points
- logs / UI text / reject wording
- tests that intentionally enforce the current policy

## 8. Excluded Scope

- no implementation
- no execution SSOT promotion yet
- no broad Stage2/3/4 unrelated debt inventory
- no temp queue cleanup
- no artifact rewrites
- no retry / live run unless explicitly ordered later

## 9. Output Contract

Each lane writes exactly one document in `docs/2026-04-06/`.

Lane outputs:

- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane1-stage2-origin.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane2-stage3-carryover.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane3-stage4-opening-authority.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane4-stage4-chainlink-postpass.md`
- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane5-runtime-evidence-and-tests.md`

Final merged survey path:

- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-bounded-survey.md`

Only Codex writes the final merged survey.

## 10. Lane Split

### Lane 1: Stage2 Origin / Prompt / State-Lock Producer

Primary question:

- where does `non-wuxia fatigue` first become a structured or implied recovery obligation?

Inspect at minimum:

- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/state_extractor.py`
- `modules/domain/agents/analyst_prompts.py`
- `config/prompts/analyst.yaml`
- `modules/domain/agents/preflight_checker.py`
- `modules/domain/agents/four_phase_arc_generator.py`
- `tests/test_arc_ensemble_lane_a.py`

Focus:

- `V60.10`
- `next_arc_constraints`
- `must_start_with`
- `recovery_scene_required`
- non-wuxia recovery penalty
- prompt wording that treats soft fatigue as hard-fail
- existing natural-healing carveouts already present in producer-side code

Deliverable must answer:

- which exact producer surfaces create the overreach
- whether producer logic already distinguishes physical injury vs soft fatigue
- whether current tests intentionally preserve the problematic behavior

### Lane 2: Stage3 Blueprint Carryover / Opening Pin Intake

Primary question:

- does `Stage3` merely pass through Stage2 pressure, or does it add new opening-hardening behavior of its own?

Inspect at minimum:

- `modules/core/stage3_orchestrator.py`
- `modules/core/continuity_pin_guard.py`
- `tests/test_stage3_orchestrator.py`
- any directly related `tests/test_continuity_pin_guard.py` evidence needed for Stage3 claims

Focus:

- `apply_continuity_pins()`
- `_continuity_pins`
- unresolved pin behavior
- how `constraint_summary`, `tactical_doc`, and prior manuscript are used to patch opening behavior
- whether Stage3 already injects hard opening continuity assumptions inappropriate for non-wuxia works

Deliverable must answer:

- whether Stage3 is a passive carrier or an active overreach amplifier
- whether the current pin logic is spatial/action continuity only, or if it can indirectly intensify fatigue-state rigidity
- whether Stage3 has a clean seam for future bounded normalization

### Lane 3: Stage4 Opening Authority / Preflight / Consumer Intake

Primary question:

- once Stage4 receives a blueprint, how hard does it bind opening continuity and state carryover before manuscript generation?

Inspect at minimum:

- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/continuity_pin_guard.py`
- `tests/test_stage4_preflight_continuity.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage4_interview_round.py`

Focus:

- Stage4 preflight blueprint patch/advisory path
- `[Stage4 Opening Scene Authority]`
- `opening_action_continuity_pin`
- `carryover_pending_actions`
- carryover location / time / motion hard-binding
- whether Stage4 intake language is strong enough to force false continuity failures in investment works

Deliverable must answer:

- whether Stage4 is the strongest current hardening layer
- which Stage4 intake texts or pins are truly hard canon today
- whether the overreach is opening-motion only or broader physical-state / recovery-state pressure

### Lane 4: Stage4 Chain-Link / Post-Pass Persistence / Next-Episode State Pressure

Primary question:

- after a Stage4 PASS, does manuscript-derived `chain_link` turn soft fatigue into a sticky next-episode obligation?

Inspect at minimum:

- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_post_pass_runtime.py`
- `modules/core/stage4_context_builder.py`
- `tests/test_stage4_post_processor.py`
- `tests/test_stage4_context.py`
- `tests/test_stage4_context_builder.py`

Focus:

- `_extract_chain_link()`
- `physical_state`
- `pending_actions`
- DB anchor save/load flow for `chain_link_*`
- how chain-link fields re-enter the next episode mandatory context
- whether mild fatigue is persisted in a way that later becomes effectively mandatory

Deliverable must answer:

- whether Stage4 post-pass persistence is part of the overreach
- whether `physical_state` is merely descriptive or effectively normative
- whether chain-link carryover currently lacks a soft/hard distinction

### Lane 5: Runtime Evidence / Operator Symptom / Test Codification

Primary question:

- does live evidence support the claim that this is a real cross-stage operator-facing problem rather than a source-only hypothesis?

Inspect at minimum:

- `0_temp.txt`
- `tests/test_arc_ensemble_lane_a.py`
- `tests/test_continuity_pin_guard.py`
- `tests/test_stage4_preflight_continuity.py`
- relevant prior docs only when needed:
  - `docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
  - `docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
  - `docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md`

Optional:

- canary or project runtime artifacts that clearly demonstrate the same symptom chain

Focus:

- real reject wording
- whether tests explicitly lock in the current behavior
- whether queue docs already recognize part of this debt
- whether the operator complaint is best described as `false hardening`, `genre misclassification`, `opening continuity overreach`, or a combination

Deliverable must answer:

- whether there is enough evidence to promote a future execution SSOT
- the most likely severity band for the issue
- whether the complaint is `Stage2-only`, `Stage4-only`, or genuinely `cross-stage`

## 11. Required Findings Format For Each Lane

Each lane output must include:

1. `Scope`
2. `Files Inspected`
3. `Evidence`
4. `Findings`
5. `Open Questions`
6. `Provisional Severity`
7. `Recommended Merge Notes`

Severity must stay bounded:

- `P0`: catastrophic data corruption / guaranteed hard failure / unsafe broad regression
- `P1`: real operator-facing false hard-fail or hard contract mismatch
- `P2`: meaningful overreach, rigidity, or owner collision that can produce bad rejects or poor runtime pressure
- `P3`: clarity, observability, naming, or indirect drift

If confidence is below `95%`, the lane must say so explicitly and leave the point provisional.

## 12. Merge Rules

The merged survey should synthesize, not copy-paste, lane findings.

The merged survey must explicitly classify the current overreach into these buckets:

- producer-side hardening
- Stage3 handoff amplification
- Stage4 intake hardening
- Stage4 post-pass persistence hardening
- runtime evidence / operator symptom confirmation

The merged survey must also answer whether this future repair should likely be:

- a `single bounded cross-stage patch`
- a `Stage2 + Stage4 dual-owner patch`
- a `prompt-only normalization`
- a `policy split between hard injury and soft fatigue`

## 13. Paste-Ready Terminal Orders

### Terminal 1

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\AGENTS.md
2. C:\Users\wjjo\Desktop\글도비\docs\implementation\system-order-init-harness.md
3. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md

Task:
- read-only survey only
- own Lane 1 only
- inspect Stage2 producer/origin surfaces that may harden non-wuxia fatigue into recovery/state-lock pressure
- preserve the operator premise that natural healing must remain valid
- do not patch code
- do not write docs/temp
- write exactly one output file only:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\stage234-nonwuxia-state-lock-overreach-lane1-stage2-origin.md
```

### Terminal 2

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\AGENTS.md
2. C:\Users\wjjo\Desktop\글도비\docs\implementation\system-order-init-harness.md
3. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md

Task:
- read-only survey only
- own Lane 2 only
- inspect Stage3 carryover / continuity pin intake behavior
- determine whether Stage3 is passive carryover or an active overreach amplifier
- do not patch code
- do not write docs/temp
- write exactly one output file only:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\stage234-nonwuxia-state-lock-overreach-lane2-stage3-carryover.md
```

### Terminal 3

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\AGENTS.md
2. C:\Users\wjjo\Desktop\글도비\docs\implementation\system-order-init-harness.md
3. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md

Task:
- read-only survey only
- own Lane 3 only
- inspect Stage4 preflight / opening authority / consumer intake hardening
- determine how hard opening continuity and state carryover are bound before manuscript generation
- do not patch code
- do not write docs/temp
- write exactly one output file only:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\stage234-nonwuxia-state-lock-overreach-lane3-stage4-opening-authority.md
```

### Terminal 4

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\AGENTS.md
2. C:\Users\wjjo\Desktop\글도비\docs\implementation\system-order-init-harness.md
3. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md

Task:
- read-only survey only
- own Lane 4 only
- inspect Stage4 chain_link extraction / persistence / next-episode carryover pressure
- determine whether physical_state or pending_actions make mild fatigue too sticky
- do not patch code
- do not write docs/temp
- write exactly one output file only:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\stage234-nonwuxia-state-lock-overreach-lane4-stage4-chainlink-postpass.md
```

### Terminal 5

```text
Read first:
1. C:\Users\wjjo\Desktop\글도비\AGENTS.md
2. C:\Users\wjjo\Desktop\글도비\docs\implementation\system-order-init-harness.md
3. C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md

Task:
- read-only survey only
- own Lane 5 only
- inspect runtime/operator evidence and tests that codify the current behavior
- use 0_temp.txt as a real symptom anchor
- determine whether the issue is truly cross-stage and whether future execution-ssot promotion is justified
- do not patch code
- do not write docs/temp
- write exactly one output file only:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-06\stage234-nonwuxia-state-lock-overreach-lane5-runtime-evidence-and-tests.md
```

## 14. Final Merge Reservation

Codex will read all five lane outputs and, if evidence is sufficient, write:

- `docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-bounded-survey.md`

No Opus terminal should write that merged file.

## 15. 3-Pass Audit Record

Draft complete.

Pass 1:

- document type matches `system-track parallel survey order`
- scope and exclusions are explicit
- output contract and lane split are explicit

Pass 2:

- paths verified against live workspace
- filenames follow canonical naming contract
- lane scopes align with inspected source surfaces

Pass 3:

- document is operationally actionable
- ownership split is clear
- merge reservation prevents write collision

Estimated confidence before save: `96%`
