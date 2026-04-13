# Stage234 EP3 Continuity Replay / Season Truth Live-Run Follow-up Parallel Survey

Date: 2026-04-12
Status: active_followup_survey
Scope: `projects/000_0412-1` current bounded proof run follow-up after the operator-stopped Stage4 ep3 retry loop; inspect whether the live blocker belongs to Stage2, Stage3, Stage4, or a cross-stage seam.
Baseline Commit: `2b7cb64f2d1fe2cd1152806a5cc37795609f9755`
Baseline Dirty Summary: `dirty workspace; live proof logs plus previously landed Stage2/Stage3/Stage4/code/doc deltas present`
Evidence Type: `live runtime log + artifact/body truth + upstream plan truth`
Confidence: `96%`

## 1. Evidence Scope

Included:
- live operator log: `0_temp.txt`
- Stage2 upstream arc truth:
  - `projects/000_0412-1/plans/arcs/arc_001.txt`
  - `projects/000_0412-1/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`
- Stage3 current-episode truth:
  - `projects/000_0412-1/plans/blueprints/blueprint_0002.txt`
  - `projects/000_0412-1/plans/blueprints/blueprint_0003.txt`
  - `projects/000_0412-1/logs/artifacts/stage3/ep_0002/attempt_04/final_blueprint__action_focused.json`
  - `projects/000_0412-1/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__dialogue_focused.json`
- Stage4 live owner surfaces:
  - `modules/core/stage4_postselect_runtime.py`
  - `modules/core/stage4_retry_runtime.py`
  - `modules/domain/agents/chief_writer.py`

Excluded:
- new code patching
- fresh rerun
- queue closure claims

## 2. Finding Summary

### Finding A — `P1`
Stage2 is not the direct owner of the live ep3 failure. The current blocker is a Stage3 episode-boundary / progression drift that Stage4 is only catching downstream.

Evidence:
- Stage2 arc truth is cleanly partitioned:
  - ep2 = independent declaration / family confrontation
  - ep3 = law-firm setup + asset liquidation
  - ep4 = office + IAEA news trigger
- `arc_001.txt` keeps `대한그룹`, `2006년 1월`, and the early progression sequence coherent.
- `blueprint_0002.txt` already over-consumes the TV-news cliffhanger that should have remained a later progression step.
- `blueprint_0003.txt` then repeats the legal setup / asset liquidation / father-study confrontation family instead of progressing beyond the ep2 carryover.

Representative anchors:
- `projects/000_0412-1/plans/arcs/arc_001.txt:16`
- `projects/000_0412-1/plans/arcs/arc_001.txt:60`
- `projects/000_0412-1/plans/blueprints/blueprint_0002.txt:7`
- `projects/000_0412-1/plans/blueprints/blueprint_0002.txt:47`
- `projects/000_0412-1/plans/blueprints/blueprint_0003.txt:7`
- `projects/000_0412-1/plans/blueprints/blueprint_0003.txt:46`

### Finding B — `P1`
Stage3 ep3 also drifts on canonical proper-noun truth before Stage4 ever judges the manuscript. The current blueprint says `한강그룹`, while upstream arc truth says `대한그룹`.

Evidence:
- Stage2 / arc truth: `대한그룹 한정호 회장의 철없는 막내아들`
- Stage3 ep3 blueprint: `한강그룹 한정호 회장 아들, 한시우입니다`
- This is upstream canonical-name drift, not merely a Stage4 overreaction.

Representative anchors:
- `projects/000_0412-1/plans/arcs/arc_001.txt:16`
- `projects/000_0412-1/plans/blueprints/blueprint_0003.txt:7`
- `projects/000_0412-1/plans/blueprints/blueprint_0003.txt:16`

### Finding C — `P1`
Stage4 is correctly rejecting the replayed / season-shifted ep3 manuscript family rather than causing the main defect.

Evidence:
- Round 5 reaches Director `PASS 100`, but post-select correctly downgrades on `봄날` vs `겨울(2006년 1월)` season/timeline contradiction.
- Round 6 is not the old ep2 truth-pin family; it downgrades because ep3 replays two ep2 scene families:
  - morning corridor / housekeeper interaction
  - father-study declaration exchange
- The system itself promotes the situation to `Arc 구조 진단`, which matches the artifact comparison.

Representative anchors:
- `0_temp.txt:900`
- `0_temp.txt:907`
- `0_temp.txt:929`
- `0_temp.txt:1077`
- `0_temp.txt:1089`
- `0_temp.txt:1150`

### Finding D — `P2`
There is still Stage4-side retry feedback carryover noise. Round 6 surfaces the new replay conflict, but the visible retry feedback also drags forward the older spring/winter conflict text and an extra flashback advisory bundle.

Evidence:
- Round 6 downgrade is a single continuity conflict.
- The immediately following retry guidance still includes the earlier spring/winter conflict prose and extra advisory bundles, which is noisy for operators and may blur the true next-fix target.

Representative anchors:
- `0_temp.txt:1089`
- `0_temp.txt:1092`
- `0_temp.txt:1112`
- `0_temp.txt:1141`

## 3. Ownership Judgment

Primary owner now:
- `0_0-stage3-contract-tightening-remediation`

Sibling supporting owner:
- `0_0-stage3-opening-transition-contract-normalization-remediation`

Downstream verifier / consumer:
- `0_0-stage4-consumer-contract-normalization-remediation`

Shared supporting substrate:
- `0_0-stage234-cross-stage-contract-normalization-remediation`

Not the front owner:
- `0_0-stage2-contract-normalization-remediation`

## 4. Execution Consequence

1. Do not reopen Stage2 first. Keep Stage2 as indirect seam only.
2. Promote the live blocker as a Stage3-owned fail-only family:
   - ep-boundary replay leakage
   - canonical institution proper-noun drift
   - weak season / next-day progression truth for the ep2 -> ep3 handoff
3. Keep the recently landed Stage4 `truth_pin / retry-lane hardening` tranche as landed and successful against the older ep2 family.
4. Keep Stage4 consumer as the downstream proof gate, but do not lead with another Stage4 retry-only patch before Stage3 truth is tightened.

## 5. Recommended Next Slice

Bounded follow-up before the next rerun:
- tighten Stage3 ep-boundary replay suppression against already-consumed prior-episode beat families
- hard-pin canonical institution / group-name truth in Stage3 blueprint generation and validation
- strengthen the immediate-next-day / winter-season continuity packet used by ep3 opening construction
- leave Stage4 as verifier first, not primary rewriter
