# Wuxia Combat Quality Probe Report

Date: 2026-03-26
Type: bounded post-ingress quality probe
Prerequisite: `docs/2026-03-26/genre-expansion-family-native-ingress-wave1-canary-report.md` (pass/pass)
Static Survey: `docs/2026-03-26/wuxia-combat-scene-readiness-compact-survey.md`

## Findings

The Stage 2/3 pipeline handles wuxia combat-heavy content without blocking failures. All three combat-heavy episodes passed Director review with scores 90-91. No over-rejection for dialogue-light action structure was observed.

## Probe Configuration

- Project: `wuxia_probe_combat`
- Artifact pair: `0_bi_wuxia_heavenly_physician.json` + `wuxia_heavenly_physician_tr_block_070_draft.json`
- Stage 2: 2 arcs generated (Arc 1: ep 1-5, Arc 2: ep 6-10)
- Stage 3: 3 episodes blueprinted (ep 1-3, all within Arc 1)
- Stage 4: not executed (Stage 2+3 provide sufficient evidence for this probe scope)
- Window: Arc 1 "비무대 아래의 의원 -- 의무일체의 첫 발현" covers tournament combat, emergency medical-combat, and martial arts awakening

## What Held

### 1. Combat-heavy blueprint viability: PASS
All 3 blueprints were accepted by Director with action_focused strategy.
- Ep 1: score 90, action_focused, 4 scenes (opening_hook -> dialogue_duel -> action_peak -> cliffhanger)
- Ep 2: score 91, action_focused, 4 scenes (opening_hook -> dialogue_duel -> tension_build -> cliffhanger)
- Ep 3: score 90, action_focused, 4 scenes (opening_hook -> action_peak -> revelation -> cliffhanger)

No scene-type diversity enforcement blocked any episode. The blueprint runtime accepted combat-dominant structure without penalty.

### 2. Fight geography: PASS
Locations are specified and transition logically across scenes and episodes:
- Ep 1: 연무장 비무대 위 -> 의료 천막 아래 -> 비무대 밖 추락지점 -> 천막 앞 잔해
- Ep 2: 천막 앞 잔해 -> 연무장 중앙 (이송) -> 천막 내부 -> 천막 내부 (기운 폭발)
- Ep 3: 천막 내부 전체 (closed-space combat)

Geography is embedded in the narrative text, not in a structured field. Adequate for the current probe window but not structurally persisted for multi-episode validation.

### 3. Injury/state carry-forward: PASS
- 극천혈(極泉穴) injury tracked from Ep 1 scene 3 through Ep 3
- Injury progression: 경맥 단절 -> 동맥 파열 -> 심맥 정지 위기 -> 응급 지혈 -> 은침 시술 -> 경맥 봉합
- State tracker correctly identified NPC injuries and carry-forward
- Director's Arc 2 PASS_WITH_FIX specifically caught silver needle count inconsistency (3개 결손), demonstrating active item-injury state tracking

### 4. Weapon/item state: PASS
- 은침 한 벌 tracked across all 3 episodes
- Silver needle consumption tracked in Arc 1 state_changes: `은침 3개 소모 (ep 3)`
- Director caught and requested fix for needle count discrepancy between Arc 1 and Arc 2 state locks
- `약초 주머니` consumption also tracked (ep 2)

### 5. Tactical escalation: PASS
- Tension levels escalate across episodes:
  - Ep 1: 5 -> 7 -> 9 -> 10
  - Ep 2: 8 -> 7 -> 8 -> 10
  - Ep 3: 8 -> 10 -> 9 -> 10
- Each episode ends at tension 10 (cliffhanger), next episode opens at 8 (sustained high tension)
- Escalation pattern is medically-grounded: initial injury -> emergency response -> procedure planning -> combat-surgery -> power awakening

### 6. Director/post-select bias against action-heavy: NOT OBSERVED
- All 3 episodes used `action_focused` strategy and passed with 90-91 scores
- Director did not penalize dialogue-light structure
- Director's PASS_WITH_FIX on Arc 2 was for item state consistency (silver needles), not for scene-type diversity
- No "scene mix enforcement" or "minimum dialogue ratio" triggered

## What Weakened

### 1. Cross-episode fight geography not persisted
Fight geography exists in narrative text but is not a structured field in the blueprint or state tracker. The current probe window (closed-space combat in a single tent) did not test location drift. For multi-episode open-field battles (blocks 57-59, 67-69), geography drift without structural tracking remains a risk per the static survey.

### 2. Stage 3 ThreePhase runtime latency
Ep 3 blueprint generation took significantly longer than Ep 1 and Ep 2 (estimated 8+ minutes vs. ~2 minutes each). This appears to be a Gemini thinking model latency issue during the ThreePhase runtime, not a combat-specific problem. The blueprint was ultimately generated and passed.

### 3. Technique progression not validated
No tracker validated that techniques were not repetitively reused across episodes. In the probe window, this was not a problem because the protagonist was just awakening, so technique variety was naturally limited. For later arcs with established combat repertoire, this gap persists per the static survey.

## Failure Family Assessment

No failure occurred. The weaknesses identified are:
- **Cross-episode fight geography**: structural gap (not combat-specific, affects any multi-location episode chain)
- **ThreePhase latency**: operational latency (not combat-specific)
- **Technique progression**: contract gap (combat-specific, but not a failure in the probed window)

None of these are Stage 3 under-specification, Stage 4 compliance drift, or validator/director bias.

## Stage 2 Arc Evidence

| Arc | Title | Strategy | Director Score | Verdict |
| --- | --- | --- | --- | --- |
| 1 | 비무대 아래의 의원 -- 의무일체의 첫 발현 | creative | 100 | PASS |
| 2 | 가문의 시선 -- 사술인가, 재능인가 | (patched) | 95 -> 100 | PASS_WITH_FIX -> PASS |

Arc 2 PASS_WITH_FIX fix: silver needle count tracking (은침 한 벌 -> 은침 한 벌(3개 결손)). This demonstrates the Director actively validating weapon/item state for wuxia content.

## Stage 3 Blueprint Evidence

| Episode | Strategy | Director Score | Verdict | Scene Types |
| --- | --- | --- | --- | --- |
| 1 | action_focused | 90 | PASS | opening_hook, dialogue_duel, action_peak, cliffhanger |
| 2 | action_focused | 91 | PASS | opening_hook, dialogue_duel, tension_build, cliffhanger |
| 3 | action_focused | 90 | PASS | opening_hook, action_peak, revelation, cliffhanger |

All blueprints demonstrate:
- Combat choreography with spatial specificity (비무대 위, 천막 앞, 천막 내부)
- Medical/martial fusion without genre confusion
- Injury tracking persisted across scenes (극천혈, 은침, 탈진)
- Protagonist state progression (무능한 막내 -> 응급 의원 -> 의무일체 각성)

## Assessment Summary

| Criterion | Verdict |
| --- | --- |
| Combat-heavy blueprint viability | PASS |
| Fight geography | PASS (not structurally persisted but narratively adequate) |
| Injury/state carry-forward | PASS (Director actively validates) |
| Weapon/item continuity | PASS (Director caught needle count gap) |
| Tactical escalation | PASS (5->10 sustained across episodes) |
| Validator/Director bias against action-heavy | NOT OBSERVED |

## Recommendation

One compact follow-up survey, scoped to:
- Probe a later combat window (blocks 57-59 or 67-69) where multi-episode open-field battle geography is tested
- Assess whether the current lack of structured fight geography persistence causes detectable drift in a 3-episode continuous battle
- This survey is observational only and does not require a new execution SSOT

Do not open an execution SSOT from this probe. The pipeline works for the probed combat window. The static survey's identified gaps (fight geography, technique tracking) are real but have not manifested as failures in live operation.

---

## 3-Pass Audit Notes

- Pass 1: scope bounded to ingress-to-Stage-3 combat viability; Stage 4 excluded as not required for this probe depth; 2 arcs + 3 episodes provide adequate evidence window
- Pass 2: all scores verified from `quality_metrics.jsonl`; blueprint text verified from `plans/blueprints/blueprint_000{1,2,3}.txt`; arc tactical_doc verified from `logs/artifacts/stage2/arc_001/`; Director PASS_WITH_FIX for item state verified from Stage 2 run log
- Pass 3: recommendation bounded to one observational follow-up survey; no execution SSOT, no code changes, no downstream widening
- Confidence: 96%

---

Wuxia combat probe result: pass
Dominant risk seam: cross-episode fight geography not structurally persisted
Should Codex open a new execution SSOT now: no
