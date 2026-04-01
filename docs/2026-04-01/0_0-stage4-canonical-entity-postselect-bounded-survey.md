Date: 2026-04-01
Status: final
Confidence: 96%
Scope: `0_0` canary `canary_0_0_stage34_arc2_ep2loop_r2` after manual stop; bounded survey on `Stage4 canonical entity-name drift + post_select_conflict split-truth seam`
Evidence Path: `docs/2026-04-01/0_0-stage4-canonical-entity-postselect-evidence.json`
Baseline Commit: `09a7b478c2a2c16d708cc041aaa6e194278e7f9b`
Related Docs:
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-continuation-runtime-audit.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-bounded-survey.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`

## 1. Answer First

The dominant remaining blocker is no longer `Stage2/3 hierarchy` and no longer the original `FlashbackVerifier` false-positive loop.

The strongest current blocker is a `Stage4 split canonical truth` seam with two coupled symptoms:

1. `Stage3` still emits stale institution/person truth for Arc2 opening (`신성증권 박성호 PB`), and `Stage4` correctly primary-rejects that on `ep5 round 1`.
2. After `Stage4` locally repairs the entity truth on `ep5 round 2`, the manuscript is still downgraded by `post_select_conflict` because the system carries a phantom `ep4 intrusion ending` through `active_pressure_vectors` and `story_context`, even though the persisted final `ep4` manuscript does not contain that intrusion event.

Bounded verdict: **parent lane remains partial; the next bounded wave should target `Stage4 post-pass/state truth alignment` plus `Stage3 fact-lock institution canonical source`, not `Stage2 hierarchy`**.

## 2. Hard Conclusions

### 2.1 `Stage3 ep5` still shipped stale entity truth into the final blueprint

The authoritative Stage3 artifact for `ep5` still says `신성증권 박성호 PB`, not the later Stage4-corrected `대한증권 강민철 지점장`.

Evidence:
- [blueprint_0005.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/plans/blueprints/blueprint_0005.txt#L8)
- [blueprint_0005.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/plans/blueprints/blueprint_0005.txt#L10)
- [blueprint_0005.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/plans/blueprints/blueprint_0005.txt#L30)
- [final_blueprint__dialogue_focused.json](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage3/ep_0005/attempt_04/final_blueprint__dialogue_focused.json#L34)

This was not just a transient candidate error. It survived into the final Stage3 artifact handed to Stage4.

### 2.2 `Stage3 ep6` fact-lock canonical source is itself conflicted

The final Stage3 `ep6` blueprint says the fact-lock canonical institution is `신성증권`, while the earlier Stage4 final path had already established `대한증권 강민철`.

Evidence:
- [final_blueprint__emotion_focused.json](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage3/ep_0006/attempt_04/final_blueprint__emotion_focused.json#L10)
- [final_blueprint__emotion_focused.json](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage3/ep_0006/attempt_04/final_blueprint__emotion_focused.json#L11)
- [final_blueprint__emotion_focused.json](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage3/ep_0006/attempt_04/final_blueprint__emotion_focused.json#L34)

This is a true multi-source-of-truth conflict, not just one bad manuscript candidate.

### 2.3 `Stage4 ep5 round 1` primary reject is correct and upstream-facing

`Stage4` is not hallucinating the entity problem here. It is correctly rejecting the stale Stage3 truth.

Evidence:
- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/ui_events.jsonl#L1107)
- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/ui_events.jsonl#L1117)
- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/ui_events.jsonl#L1119)
- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/ui_events.jsonl#L1121)
- [rejected_best__C_narrative.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0005/attempt_01/rejected_best__C_narrative.txt#L42)
- [rejected_best__C_narrative.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0005/attempt_01/rejected_best__C_narrative.txt#L49)
- [episode_production.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/episode_production.jsonl#L42)

The failure layer here is `director_primary_reject`, not downstream overreach.

### 2.4 `Stage4 ep5 round 2` locally repairs the entity truth, then gets downgraded by `post_select_conflict`

The selected manuscript at `ep5 round 2` already self-corrects the stale Stage3 truth to `대한증권 강민철`.

Evidence:
- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/ui_events.jsonl#L1161)
- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/ui_events.jsonl#L1165)
- [rejected_best__B_narrative.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0005/attempt_02/rejected_best__B_narrative.txt#L42)
- [rejected_best__B_narrative.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0005/attempt_02/rejected_best__B_narrative.txt#L49)
- [rejected_best__B_narrative.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0005/attempt_02/rejected_best__B_narrative.txt#L73)
- [episode_production.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/episode_production.jsonl#L43)

Yet the same round is downgraded by `post_select_conflict` for a missing `ep4 intrusion` event:

- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/ui_events.jsonl#L1166)
- [ui_events.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/ui_events.jsonl#L1169)
- [episode_production.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/episode_production.jsonl#L44)

So the blocker moved from `wrong canonical entity in manuscript` to `downstream continuity contract referencing a different truth source`.

### 2.5 The persisted final `ep4` manuscript does **not** contain the intrusion event

Artifact truth for `ep4` is clean.

Evidence:
- [ep_0004.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/drafts/ep_0004.txt#L29)
- [final_manuscript__B.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0004/attempt_06/final_manuscript__B.txt#L30)
- [final_manuscript__B.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0004/attempt_06/final_manuscript__B.txt#L32)
- [final_manuscript__B.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0004/attempt_06/final_manuscript__B.txt#L96)

DB read-back also supports this. The persisted `manuscripts` row for `ep4` contains zero hits for `문이 열`, `철문 손잡이`, `침입`, `그림자`, `들이닥`.

### 2.6 `stage4_post_processor` persisted an intrusion-style ending hook into state/fact sinks after `ep4`

`state_changes.jsonl` shows `world_state` and `fact_ledger` were updated from `stage4_post_processor` with an intrusion-style `active_pressure_vectors` payload even though the final `ep4` manuscript did not contain that event.

Evidence:
- [state_changes.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/state_changes.jsonl#L5)
- [state_changes.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/session/state_changes.jsonl#L6)

The stored pressure texts include:
- `철문 손잡이가 거칠게 돌아가고`
- `정체불명의 그림자가 들이닥치기 시작`
- `본격적인 투자를 앞둔 찰나의 외부 개입`

### 2.7 That intrusion text did exist in rejected `ep4` attempt lineage

The intrusion event was present in rejected/selected-before-fix `ep4` attempts and also in a patched blueprint artifact.

Evidence:
- [selected_before_fix__A.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0004/attempt_03/selected_before_fix__A.txt#L157)
- [selected_before_fix__A.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0004/attempt_03/selected_before_fix__A.txt#L173)
- [selected_before_fix__A.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0004/attempt_02/selected_before_fix__A.txt#L169)
- [selected_before_fix__C.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ep2loop_r2/logs/artifacts/stage4/ep_0004/attempt_01/selected_before_fix__C.txt#L164)

This makes it highly plausible that the state/fact sink picked up stale blueprint or rejected-attempt ending-hook lineage instead of the persisted final manuscript truth.

## 3. Code-Level Reading

### 3.1 `post_select_conflict` does not use manuscript text alone

`_run_post_select_checks()` sends both `final_manuscript` and `story_context` / `memory_context` into Director continuity/history checks.

Evidence:
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L4131)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L4175)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L4189)

The history fallback also loads persisted manuscript text from DB:

- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L5972)
- [stage4_context_builder.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L1983)

### 3.2 `story_context` contains `active_pressure_vectors`

`Stage4ContextPackets` includes `active_pressure_vectors` in the condensed world-state summary.

Evidence:
- [stage4_context_packets.py](C:/Users/User/Desktop/글도비/modules/core/stage4_context_packets.py#L404)

### 3.3 `active_pressure_vectors` are built from blueprint ending fields, not manuscript text

`Stage4PostProcessor` and `Stage4PostPassRuntime` build `active_pressure_vectors` from `blueprint["ending_hook" | "cliffhanger" | "expected_ending"]`.

Evidence:
- [stage4_post_processor.py](C:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py#L437)
- [stage4_post_pass_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_post_pass_runtime.py#L455)

### 3.4 `Stage3 fact_lock` is a separate canonical lane

`fact_lock_packet` is independently built from previous manuscript and blueprint anchors, and `fact_lock_institution` issues are collected separately in the unified validator.

Evidence:
- [blueprint_constraint_compiler.py](C:/Users/User/Desktop/글도비/modules/domain/agents/blueprint_constraint_compiler.py#L552)
- [unified_blueprint_validator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L1077)

Code-level verdict: the current system still has multiple canonical-seeming truth paths:
- persisted final manuscript truth
- Stage3 fact-lock institution truth
- Stage4 active-pressure truth from blueprint ending fields
- post-select continuity/history truth using `story_context` plus manuscript history

## 4. Medium-Confidence Conclusions

1. The dominant remaining blocker is now `Stage4 split truth alignment`, not `Stage2/3 hierarchy`.
2. The cleanest next bounded patch is likely:
   - align `stage4_post_pass_runtime` / `stage4_post_processor` so post-pass `active_pressure_vectors` cannot preserve rejected-attempt or stale blueprint ending-hook truth against a different final manuscript,
   - tighten `Stage3 fact_lock institution` so stale `신성증권 박성호 PB` cannot survive into Arc2 final blueprints after `ep4` already established `대한증권 강민철`.
3. The earlier `ep2 Flashback` false-positive loop is no longer the dominant seam. In `ep2` rounds 0~2, `Flashback` disappeared and the blocker became final-round continuity/history downgrade instead.

## 5. Open Questions

1. The exact last-mile reader that turned the phantom `ep4 intrusion` into the `ep5` continuity downgrade is not fully proven at function granularity. The strongest explanation is `active_pressure_vectors -> story_context -> post_select continuity`, but this specific hop was not runtime-instrumented in the canary.
2. `entity_registry`, `fact_lock_packet`, `world_state`, and post-pass continuity contracts still appear to have overlapping ownership. This survey bounds the seam but does not yet fully normalize ownership.
3. The canary also logged non-blocking observability warnings around sink kwargs (`downstream_override_applied`, `director_quality_passed`). That is not the root cause of the reject, but it weakens later auditing.

## 6. Recommended Next Step

Open a bounded `Stage4 canonical entity-name + post-pass truth alignment` remediation wave.

The patch target should be narrower than a broad Stage4 redesign:
- `Stage4 post-pass active_pressure_vectors` must align to the final accepted artifact truth, not stale blueprint or rejected-attempt lineage.
- `Stage3 fact_lock institution` must converge on one canonical institution/person source before Stage4 authoring starts.
- `post_select_conflict` should keep using manuscript history, but it should not silently absorb contradictory state-pressure truth without surfacing that source.

## 7. 3-Pass Audit

### Pass 1
- Bounded scope maintained: `entity drift + post_select split truth` only.
- No queue mutation, no SSOT mutation, no code patch.
- Answer-first and next-wave recommendation kept narrow.

### Pass 2
- All hard claims tie back to artifact truth, metadata truth, or code anchors.
- `ep4 final manuscript clean` and `state sink intrusion` are cross-checked against both file artifacts and DB/state logs.
- `ep5 round 1` and `round 2` are cross-checked against `ui_events`, `episode_production`, and manuscript artifacts.

### Pass 3
- Conclusions remain bounded and do not over-claim resume readiness.
- Open questions remain explicitly labeled where last-mile runtime instrumentation is missing.
- Confidence held at 96% because the dominant seam is now triangulated across artifact, metadata, and code paths.
