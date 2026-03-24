Date: 2026-03-24
Status: final (3-pass audited)
Document Type: survey report (T10 lane)
Canonical Path: `docs/2026-03-24/opus-residual/t10-artifact-truth-diff-ledger.md`
Temp Mirror Path: none (survey report, not execution SSOT)
Source Survey Docs:
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave2-survey-report.md`
Evidence Artifacts:
- `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json`
- `projects/00_001/logs/artifacts/stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`
- `projects/00_001/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__dialogue_focused.json`
- `projects/00_001/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__dialogue_focused.json`
- `projects/00_001/logs/artifacts/stage3/ep_0004/attempt_02/final_blueprint__emotion_focused.json`
- `projects/00_001/logs/episode_production.jsonl`
- `modules/domain/agents/blueprint_constraint_compiler.py`
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; Wave 1 closed, Wave 2 survey finalized, fresh live-run evidence updated`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

---

# T10. Artifact Truth Diff Ledger

## 1. Executive Summary

By tracing the exact content flow from Stage 2 arc through Stage 3 blueprint to Stage 4 verdict for ep1-4, this ledger identifies the precise remaining leakage seam after Wave 1.

**Key finding**: `semantic_carryover` is the dominant residual leakage vector. Its `continuity_checkpoints` contain arc-END milestones ("20억 자본금 확보 완료", "여의도 임시 사무실 계약 및 법인 설립 완료") that enter the ep1 blueprint prompt unfiltered after Wave 1. These are the exact items that ep1's blueprint overconsumes.

Wave 1 correctly fixed `state_changes`, treatment block events, and stop line. But `semantic_carryover` was classified as "arc-global by design" and left unfiltered. The fresh live-run evidence proves this field is now the primary leakage surface.

## 2. Included Coverage / Exclusions

### Included

- Stage 2 arc payload: all fields in `final_arc__balanced.json` that enter Stage 3
- Stage 3 blueprints: ep1-4 final blueprint artifacts (content, ending_state, protagonist_state, scenes)
- Stage 4 verdicts: ep1-4 production log entries (verdict, score, gate, firewall, open_review)
- Constraint compiler code: `_extract_inherited_state()`, `_summarize_state_changes()`, constraint_block assembly
- Cross-episode content replay chain

### Excluded

- LLM I/O trace (T9 lane)
- Stage 3 prompt assembly beyond constraint_block (T6 lane)
- Blueprint ensemble synthesis internals (T7 lane)
- Stage 2 validation pipeline (T3 lane)
- Episodes 5-11

## 3. Key Evidence

### 3.1 The Replay Chain

```
Stage 2 Arc Allocation:
  ep1 = 회귀 인지 + 데이터 각성
  ep2 = 서재 호출 + 독립 선언
  ep3 = 은행 PB + 20억 현금화
  ep4 = 오피스텔 + 법인 설립 + WTI 준비

EP1 Blueprint (attempt_09, 9 Stage 3 attempts):
  Scene 1: 회귀 인지 (ep1 material)              ← correct
  Scene 2: 편두통 + 데이터 각성 (ep1 material)    ← correct
  Scene 3: 자산 현금화 → 20억 확보 (ep3 material) ← LEAKED
  Scene 4: 여의도 사무실 + 법인 인감 + OTP (ep4)  ← LEAKED
  Scene 5: 이란 핵 뉴스 + WTI 준비 (ep4)         ← LEAKED
  ending_state: "자본금 20억 확보 및 법인 설립 완료"
  → This is the ARC END STATE, not ep1 scope.

EP1 Manuscript: PASS (score 96, round 0)
  → Director accepts: internally coherent + faithful to blueprint

EP2 Blueprint & Manuscript: PASS (score 96, round 0)
  → Coherent: 서재 대면 + 독립 선언 (not fully consumed by ep1)

EP3 Blueprint: mandates 은행 PB + 20억 현금화
  → R0: PASS(95) → REJECT (post_select_conflict)
  → R1: REJECT(50) — firewall: "EP1에서 이미 완료된 20억 현금화가 반복"
  → R2: PASS(95) after V75-D blueprint rewrite

EP4 Blueprint: mandates 오피스텔 + HTS + WTI 매수
  → R0: REJECT(30) — firewall: "오피스텔 계약, HTS 세팅, WTI 매수가 모두 반복"
  → R1-R2: PASS after V75-D blueprint rewrite
```

### 3.2 Content Replay Inventory

6 concrete content items from ep3/ep4 scope were consumed by ep1's blueprint:

| # | Content Item | Arc Assignment | Consumed by EP1? | EP3/EP4 Replay Caught? |
|---|---|---|---|---|
| 1 | 자산 현금화 20억 확보 | ep3 | Scene 3 | EP3 R1 firewall |
| 2 | 여의도 오피스텔 계약 | ep4 | Scene 4 | EP4 R0 firewall |
| 3 | SW인베스트먼트 법인 설립 | ep4 | Scene 4 | EP4 R0 firewall |
| 4 | 법인 인감도장 획득 | ep4 | Scene 4 | EP4 R0 firewall |
| 5 | 20억 OTP 획득 | ep4 | Scene 4 | EP4 R0 firewall |
| 6 | WTI 투자 준비 + 이란 핵 뉴스 | ep4 | Scene 5 | EP4 R0 firewall |

### 3.3 Contamination Source Trace

Wave 1 closed three seams. This ledger identifies which fields STILL carry the leaked content:

| Field | Arc-END Content Present? | Enters EP1 Prompt? | Wave 1 Fixed? | Residual? |
|---|---|---|---|---|
| `state_changes.major_items` | YES (ep4 인감, OTP) | Was YES | **YES** (ep filter) | NO |
| treatment block events | YES (event_villain etc.) | Was YES | **YES** (quarantine) | NO |
| stop line | undercover | Was incomplete | **YES** (expanded) | NO |
| **`semantic_carryover.continuity_checkpoints`** | **YES** ("20억 확보", "법인 설립") | **YES** | **NO** | **YES** |
| **`semantic_carryover.foreshadow_anchors`** | **YES** ("이란 핵", "그룹 돈 안 받겠다") | **YES** | **NO** | **YES** |
| **`semantic_carryover.growth_justification`** | **YES** ("초기 투자 자본 20억 확보") | **YES** | **NO** | **YES** |
| `joint_docs.physical_inventory` | YES (ep4 items) | Indirect | Overwritten by arc_start | NO |
| `state_constraints.arc_end_state` | YES | NO (only arc_start enters) | N/A | NO |

### 3.4 Code Path Verification

`semantic_carryover` enters the ep1 constraint block:

- `blueprint_constraint_compiler.py:97`: `semantic_carryover = self._normalize_semantic_carryover(arc_data.get("semantic_carryover"))`
- `blueprint_constraint_compiler.py:113`: constraint_block includes `"semantic_carryover": semantic_carryover`
- `blueprint_constraint_compiler.py:132-134`: `compile_to_prompt()` formats it as `### ARC semantic carryover` section

No episode filtering is applied to `semantic_carryover` at any point. The field is passed through to the LLM verbatim.

The `continuity_checkpoints` within `semantic_carryover` contain:
```
"20억 자본금 확보 완료"           → exact match to ep3 scope
"여의도 임시 사무실 계약 및 법인 설립 완료" → exact match to ep4 scope
```

These are the same items that appear in ep1's blueprint scenes 3-4.

## 4. Findings Ranked

### P0. `semantic_carryover` is the dominant residual leakage vector (confirmed residual leakage)

The `continuity_checkpoints` and `growth_justification` fields contain arc-END milestones that enter every episode's blueprint prompt unfiltered. For ep1, these checkpoints ("20억 확보", "법인 설립 완료") are interpreted by the LLM as goals to accomplish in the current episode, causing it to compress the entire arc's scope into ep1.

Evidence:
- `final_arc__balanced.json` semantic_carryover checkpoints = arc-end items
- `blueprint_constraint_compiler.py:97,113` passes them to constraint_block unfiltered
- EP1 blueprint scenes 3-5 reproduce the exact content described by these checkpoints
- EP3/EP4 Stage 4 firewalls explicitly cite these same items as replay violations

### P1. `foreshadow_anchors` amplify the leakage (likely residual leakage)

The foreshadow anchors describe future events ("이란 핵 문제 재점화") that belong to ep4's narrative scope. While designed as arc-level narrative signposts, they provide the LLM with specific future-episode narrative fuel that accelerates overconsumption.

Evidence:
- EP1 blueprint scene 5 directly incorporates the "이란 핵" foreshadow anchor
- The anchor itself is ep4 content; the LLM consumed it as ep1 material

### P2. Stage 4 firewall is effective but expensive (secondary amplifier)

The continuity firewall correctly caught the ep3/ep4 replay at Stage 4, triggering V75-D blueprint rewrites. This is the system's safety net working as intended. However, the firewall triggers only after manuscripts are generated and evaluated, costing 2-3 additional rounds and significant tokens per affected episode.

### P3. EP2 escapes the contamination cascade (cleared non-culprit)

EP2 passed cleanly because its arc-allocated content (서재 호출, 독립 선언) was not fully consumed by ep1's overconsumption. The ep1 blueprint ended with "아버지 서재 호출" as a cliffhanger, leaving the actual 서재 scene for ep2.

## 5. Cleared Non-Culprits

| Surface | Why Cleared |
|---|---|
| `episode_details` | Correctly per-episode scoped. 2 items/ep is sparse but not the contamination source. |
| `must_focus` | Derived from episode_details, correctly scoped. |
| `inherited_state` | For ep1, correctly shows arc_start equipment (not arc_end). Code path verified at `bcc:478-487`. |
| `joint_docs` (direct) | Does NOT enter constraint_block directly. Only enters via `inherited_state.equipment`, which is overwritten by `arc_start_state`. |
| `state_constraints.arc_end_state` | Does NOT enter Stage 3 directly. Only `arc_start_state` is read at `bcc:481`. |
| `state_changes` | Wave 1 filter (`_within_ep()`) confirmed active. |
| `stop_line` | Wave 1 expansion to all future episodes confirmed. |
| `continuity_pins` | Past-verified, correctly scoped. |
| `world_state` / `fact_ledger` advisory | Past-verified, correctly scoped. |

## 6. Residual Culprit Candidate

**`semantic_carryover` — specifically `continuity_checkpoints` and `foreshadow_anchors`**

This is the remaining open seam after Wave 1. The field enters every episode's blueprint prompt at full arc scope. Its `continuity_checkpoints` contain concrete arc-END milestones that the LLM interprets as current-episode obligations. The `foreshadow_anchors` provide specific future-episode narrative detail that the LLM consumes as current-episode material.

This is the same class of bug that Wave 1 fixed for `state_changes` — an arc-global field with episode-level content that reaches the LLM without episode filtering. Wave 1's expanded survey classified `semantic_carryover` as "arc-global by design, CLEAN" because it was considered soft advisory. The fresh live-run evidence proves it is not clean enough: the LLM treats its checkpoints as hard goals.

## 7. Next-Scope Recommendation

**Bounded fix: episode-scope `semantic_carryover` filtering**

Scope: `blueprint_constraint_compiler.py:97` and/or `_normalize_semantic_carryover()`

Options (in order of conservatism):
1. **Filter `continuity_checkpoints` to `episode <= current_ep`** — Only show checkpoints that correspond to already-committed episodes. This requires either (a) each checkpoint having an episode tag (like `state_changes`), or (b) matching checkpoints against `episode_details` content to determine which episode they belong to.
2. **Relabel checkpoints as arc-level goals, not current-episode obligations** — Add hard prompt framing: "These are ARC-LEVEL milestones distributed across ALL episodes. Do NOT accomplish them all in the current episode."
3. **Suppress `continuity_checkpoints` entirely for ep1** — Since ep1 has no prior committed state, the checkpoints serve no continuity purpose and only cause forward-leakage.

Option 3 is the most conservative and bounded. Option 1 is the most complete but may require checkpoint-to-episode mapping.

For `foreshadow_anchors`: these can be retained with a prompt-level guard ("foreshadow anchors should be PLANTED as hints, not RESOLVED in this episode"). This is lower priority than the `continuity_checkpoints` fix.

Estimated blast radius: same as Wave 1 — `blueprint_constraint_compiler.py` only. No Stage 2/Stage 4/DB changes needed.

## 8. Confidence And Limits

- **Confidence: 95%**
- **Basis:**
  - The content replay chain is verified across three artifact layers (arc → blueprint → verdict) with exact item-level matching
  - The code path for `semantic_carryover` is traced to specific lines in `blueprint_constraint_compiler.py`
  - The `continuity_checkpoints` match 1:1 with the leaked content in ep1's blueprint
  - Stage 4 firewall messages explicitly name the same items as continuity violations
  - All other candidate fields were systematically cleared with code and evidence verification
- **Limits:**
  - This ledger does not trace the actual LLM I/O prompt that was sent — that is T9's scope
  - This ledger does not verify whether treatment block framing (beyond event fields) also contributes — that is T6's scope
  - The `foreshadow_anchors` contribution is classified as "likely" rather than "confirmed" because the chain from anchor to overconsumption is less direct than `continuity_checkpoints`
  - This analysis covers only `00_001` arc_001; generalization to other content types needs verification

### Mandatory Conclusions

- Can this seam alone explain ep1 overconsumption: **yes** — `continuity_checkpoints` contain the exact arc-end milestones that ep1 consumed
- Can this seam explain ep3/ep4 continuity-firewall replay: **yes** — ep1 absorbs ep3/ep4 content via checkpoints → ep3/ep4 blueprints mandate same content → firewall catches replay
- Can this seam be fixed in a bounded next wave: **yes** — filtering or prompt-guarding `semantic_carryover` in `blueprint_constraint_compiler.py` is a bounded, same-file change

---

## 9. 3-Pass Audit Record

- Pass 1
  - confirmed this is a survey report, not an execution SSOT
  - confirmed scope covers the assigned T10 lane: artifact truth diff across Stage 2 → Stage 3 → Stage 4 for ep1-4
  - confirmed the content replay ledger is concrete and item-level, not general
  - confirmed report sections match the master order's required output contract

- Pass 2
  - confirmed all evidence anchors reference real artifact paths with verified content
  - confirmed the `semantic_carryover` code path matches live code at baseline commit
  - confirmed the cleared non-culprits were verified with code path tracing, not assumed
  - confirmed no overclaiming: `foreshadow_anchors` is "likely" not "confirmed"; treatment block residual is deferred to T6

- Pass 3
  - confirmed the next-scope recommendation is bounded and actionable
  - confirmed the mandatory conclusion lines are present and answered
  - confirmed the confidence basis is grounded in multi-layer evidence (artifact + code + verdict)
  - confirmed this report does not create an execution SSOT, roadmap, or temp queue item
