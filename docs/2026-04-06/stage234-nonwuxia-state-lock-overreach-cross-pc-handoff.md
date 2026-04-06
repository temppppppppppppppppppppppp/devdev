# Stage234 Nonwuxia State-Lock Overreach Cross-PC Handoff

Date: 2026-04-06
Type: handoff context note
Scope: `Stage2 -> Stage3 -> Stage4` non-wuxia fatigue / recovery / opening continuity overreach
Status: handoff-ready
Confidence: 96%

## Answer-First

- This is **not** believed to be a `Stage2-only` issue.
- The current suspicion is a `cross-stage hardening chain`:
  - Stage2 produces or phrases soft fatigue as if it were a recovery/state-lock obligation
  - Stage3 can carry or amplify opening continuity pressure through deterministic pinning
  - Stage4 hardens opening carryover and post-pass chain-link state strongly enough that mild fatigue may become sticky or falsely mandatory
- `natural healing` must remain valid.
- No code patch is authorized yet.
- A `5-lane read-only parallel survey order` already exists and is the current authoritative next step.

## 1. Why This Investigation Exists

The operator surfaced a real Director reject pattern from [0_temp.txt](/Users/wjjo/Desktop/글도비/0_temp.txt):

- an investment / business-power arc was criticized for not honoring a `V60.10 STATE LOCK`
- the complaint treated protagonist fatigue and a missing recovery beat as if they were hard continuity violations
- the operator explicitly said this is the wrong genre posture for modern investment fiction

The operator's clarified requirements are:

- preserve `natural healing`
- do not remove the ability for ordinary fatigue to resolve naturally
- stop the system from acting as though mild fatigue is equivalent to severe injury
- do not immediately patch code

## 2. What Was Already Confirmed Locally

These are provisional findings from live source inspection before the parallel survey was commissioned.

### A. Stage2 producer-side hardening is real

Likely owner surfaces already found:

- [arc_ensemble.py](/Users/wjjo/Desktop/글도비/modules/domain/agents/arc_ensemble.py#L386)
  - non-wuxia recovery penalty logic exists
- [arc_ensemble.py](/Users/wjjo/Desktop/글도비/modules/domain/agents/arc_ensemble.py#L490)
  - returns `opening recovery beat too implicit for non-wuxia carryover fatigue`
- [state_extractor.py](/Users/wjjo/Desktop/글도비/modules/domain/agents/state_extractor.py#L419)
  - emits `V60.10 STATE LOCK`
- [state_extractor.py](/Users/wjjo/Desktop/글도비/modules/domain/agents/state_extractor.py#L533)
  - fallback can set `must_start_with`
- [state_extractor.py](/Users/wjjo/Desktop/글도비/modules/domain/agents/state_extractor.py#L625)
  - fallback can set `recovery_scene_required`
- [analyst.yaml](/Users/wjjo/Desktop/글도비/config/prompts/analyst.yaml#L211)
  - V60.10 hard-lock wording still exists
- [analyst_prompts.py](/Users/wjjo/Desktop/글도비/modules/domain/agents/analyst_prompts.py#L224)
  - similar hard-lock wording exists in code prompt builder path

### B. Natural healing is already partially recognized

This matters because the future fix should normalize authority, not delete recovery semantics wholesale.

- [four_phase_arc_generator.py](/Users/wjjo/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py#L1692)
  - already treats mental fatigue residue as naturally recoverable advisory in at least one path
- [preflight_checker.py](/Users/wjjo/Desktop/글도비/modules/domain/agents/preflight_checker.py#L405)
  - still carries `must_start_with` style guidance in a generic way

Current working hypothesis:

- parts of the system already know `soft fatigue` should be lighter
- adjacent producer/prompt/fallback surfaces re-harden it later

### C. Stage3 is at least a continuity pressure carrier

- [stage3_orchestrator.py](/Users/wjjo/Desktop/글도비/modules/core/stage3_orchestrator.py#L2043)
  - Stage3 applies `apply_continuity_pins()`
- [continuity_pin_guard.py](/Users/wjjo/Desktop/글도비/modules/core/continuity_pin_guard.py#L133)
  - deterministic continuity patching exists for Stage3/4 handoff
- [continuity_pin_guard.py](/Users/wjjo/Desktop/글도비/modules/core/continuity_pin_guard.py#L196)
  - `opening_action_continuity_pin` is emitted

At this point it was not yet proven that Stage3 directly hardens fatigue/recovery semantics, but it clearly participates in opening carryover hardening.

### D. Stage4 opening authority is strong and likely relevant

- [stage4_orchestrator.py](/Users/wjjo/Desktop/글도비/modules/core/stage4_orchestrator.py#L910)
  - Stage4 preflight applies continuity pins
- [stage4_context_builder.py](/Users/wjjo/Desktop/글도비/modules/core/stage4_context_builder.py#L874)
  - chain-link carryover fields are pulled into mandatory context
- [stage4_context_builder.py](/Users/wjjo/Desktop/글도비/modules/core/stage4_context_builder.py#L894)
  - `[Stage4 Opening Scene Authority]` language is strong
- [stage4_context_builder.py](/Users/wjjo/Desktop/글도비/modules/core/stage4_context_builder.py#L925)
  - `carryover_pending_actions` are rendered as opening obligations
- [stage4_interview_round.py](/Users/wjjo/Desktop/글도비/modules/core/stage4_interview_round.py#L196)
  - `opening_action_continuity_pin` metadata is consumed into contradiction details

### E. Stage4 post-pass persistence may make mild state sticky

- [stage4_orchestrator.py](/Users/wjjo/Desktop/글도비/modules/core/stage4_orchestrator.py#L1058)
  - chain-link extraction asks for `physical_state` and allows fatigue/state description
- [stage4_context_builder.py](/Users/wjjo/Desktop/글도비/modules/core/stage4_context_builder.py#L1677)
  - non-`정상` physical state is re-injected into the next episode carryover section

This does not yet prove false hard-fail by itself, but it is a credible place where mild fatigue could become too sticky.

### F. Tests already codify part of the disputed behavior

- [test_arc_ensemble_lane_a.py](/Users/wjjo/Desktop/글도비/tests/test_arc_ensemble_lane_a.py#L509)
  - explicitly expects the non-wuxia recovery penalty
- [test_continuity_pin_guard.py](/Users/wjjo/Desktop/글도비/tests/test_continuity_pin_guard.py#L40)
  - opening continuity pin behavior is intentionally tested
- [test_stage4_preflight_continuity.py](/Users/wjjo/Desktop/글도비/tests/test_stage4_preflight_continuity.py#L71)
  - Stage4 preflight continuity pin attachment is intentionally tested

## 3. What Is Still Unknown

The parallel survey was created because the following questions were still unresolved:

- Is the main false-hardening owner `Stage2 producer prompts`, `Stage4 intake`, or `Stage4 post-pass persistence`?
- Is Stage3 merely carrying opening continuity, or is it also amplifying the fatigue-state problem materially?
- Does the observed operator pain mostly come from:
  - `genre misclassification`
  - `soft fatigue treated as hard`
  - `opening continuity overreach`
  - or a mixture of all three
- Is the future fix best expressed as:
  - `Stage2 + Stage4 dual-owner normalization`
  - a smaller `cross-stage policy split`
  - or a tightly bounded `prompt-and-pin realignment`

## 4. Current Authority Documents

The current operational authority for the survey itself is:

- [stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md](/Users/wjjo/Desktop/글도비/docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md)

Useful prior queue context, but lower authority than live code:

- [0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md](/Users/wjjo/Desktop/글도비/docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md)
- [0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md](/Users/wjjo/Desktop/글도비/docs/temp/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md)
- [0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md](/Users/wjjo/Desktop/글도비/docs/temp/0_0-stage234-cross-stage-contract-normalization-remediation-execution-ssot.md)

## 5. Parallel Survey Contract

This investigation is already split into five read-only lanes.

Lane outputs:

- [stage234-nonwuxia-state-lock-overreach-lane1-stage2-origin.md](/Users/wjjo/Desktop/글도비/docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane1-stage2-origin.md)
- [stage234-nonwuxia-state-lock-overreach-lane2-stage3-carryover.md](/Users/wjjo/Desktop/글도비/docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane2-stage3-carryover.md)
- [stage234-nonwuxia-state-lock-overreach-lane3-stage4-opening-authority.md](/Users/wjjo/Desktop/글도비/docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane3-stage4-opening-authority.md)
- [stage234-nonwuxia-state-lock-overreach-lane4-stage4-chainlink-postpass.md](/Users/wjjo/Desktop/글도비/docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane4-stage4-chainlink-postpass.md)
- [stage234-nonwuxia-state-lock-overreach-lane5-runtime-evidence-and-tests.md](/Users/wjjo/Desktop/글도비/docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-lane5-runtime-evidence-and-tests.md)

Final merged survey target:

- [stage234-nonwuxia-state-lock-overreach-bounded-survey.md](/Users/wjjo/Desktop/글도비/docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-bounded-survey.md)

Important:

- each terminal writes only its own lane file
- no terminal writes the final merged survey
- `docs/temp` must not be edited
- code changes are forbidden in this wave

## 6. Recommended Read Order On Another PC

If resuming on another PC, read in this exact order:

1. `AGENTS.md`
2. `docs/implementation/system-order-init-harness.md`
3. this handoff doc
4. [stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md](/Users/wjjo/Desktop/글도비/docs/2026-04-06/stage234-nonwuxia-state-lock-overreach-full-survey-audit-order.md)
5. the lane file assigned to that terminal

Optional only after that:

- the three temp execution SSOTs listed above

## 7. Resume Guidance

If the other PC is only running Opus survey terminals:

- use the existing survey order directly
- do not reinterpret the task as implementation
- keep findings bounded to the specific overreach problem

If the other PC is later asked to merge:

- do not merge until all five lane outputs exist
- synthesize by owner surface, not by file dump
- preserve the operator's central constraint:
  - natural healing must survive
  - false hardening must be reduced

## 8. Path Note For Another PC

This handoff assumes the same workspace root:

- `C:\Users\wjjo\Desktop\글도비`

If the other PC uses a different root path, keep filenames the same and only replace the root prefix.

## 9. Boundaries

- This is a `handoff context note`.
- It is not a closure document.
- It is not a remediation SSOT.
- It does not authorize implementation.
- Its purpose is to let another machine resume the survey with the right problem framing intact.

## 10. 3-Pass Audit Record

Draft complete.

Pass 1:

- document type fixed to `handoff context note`
- scope, status, and boundaries are explicit
- read order and next-action contract are present

Pass 2:

- live paths verified
- references align with current workspace files
- findings remain bounded to inspected evidence

Pass 3:

- handoff is actionable from another PC
- operator intent is preserved
- survey order and merge reservation are clear

Estimated confidence before save: `96%`
