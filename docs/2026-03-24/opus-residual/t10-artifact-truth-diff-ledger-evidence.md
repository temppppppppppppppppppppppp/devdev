Date: 2026-03-24
Status: final (3-pass audited)
Document Type: raw evidence ledger (T10 supporting artifact)
Canonical Path: `docs/2026-03-24/opus-residual/t10-artifact-truth-diff-ledger-evidence.md`

---

# T10 Evidence Ledger: Artifact Truth Diff

## 1. Stage 2 Arc Payload (`final_arc__balanced.json`)

### 1.1 `episode_details` (per-episode, correctly scoped)

| EP | Items | Content |
|---|---|---|
| 1 | 2 | "2024년 고독사 후 2006년 본가 침실에서 눈을 뜸"; "18년 치 거시경제 데이터 복기 및 두통 극복" |
| 2 | 2 | "아버지 한정호의 서재로 호출됨"; "형들의 무관심 속에서 그룹 지원을 거절하고 독자적인 투자사 설립 선언" |
| 3 | 2 | "은행 PB 박성호를 만나 신탁 펀드 및 스폰서십 해지 강행"; "자산 20억 원 현금화 완료" |
| 4 | 2 | "여의도 낡은 오피스텔 계약 및 SW인베스트먼트 설립 완료"; "저녁 뉴스에서 이란 핵 문제 보도를 보며 WTI 투자 준비" |

### 1.2 `state_changes` (ep-tagged, but formerly unfiltered)

```json
"major_items": [
    {"action": "획득", "episode": 4, "name": "SW인베스트먼트 법인 인감도장"},
    {"action": "획득", "episode": 4, "name": "20억 예치 법인 계좌 OTP"}
]
"npc_introductions": [
    {"episode": 3, "name": "박성호"}
]
"relationship_changes": [
    {"episode": 2, "npc": "한정호", ...},
    {"episode": null, "npc": "한정호 (아버지)", ...},
    {"episode": null, "npc": "한태준 (큰형)", ...},
    {"episode": null, "npc": "한태민 (둘째형)", ...}
]
```

Wave 1 filters `state_changes` by `episode <= current_ep`. For ep1, only `episode: null` items should survive. All `episode: 2/3/4` items should be excluded.

### 1.3 `joint_docs` (arc-global, NOT episode-filtered)

```json
"final_location": "서울 여의도 증권가 이면도로에 위치한 낡은 오피스텔 4층, SW인베스트먼트 임시 사무실",
"physical_inventory": "SW인베스트먼트 법인 인감도장, 20억 원이 예치된 법인 계좌의 보안 매체(OTP), 2006년 1월 기준 WTI 원유 선물 차트가 빼곡히 인쇄된 A4 용지 뭉치",
"world_joint": "한시우의 가용 자산 20억 원이 해외 선물 시장 진입을 위해 달러(USD)로 환전 대기 중이며, 한정호 회장을 비롯한 일가는 막내의 행보를 '일시적인 외도'로 치부하여 감시망을 완전히 거둔 상태."
```

Critical observation: All three fields describe the ARC-END state, not the arc start. `physical_inventory` contains ep4 items. `world_joint` describes ep4 world state. `final_location` is ep4 destination.

### 1.4 `semantic_carryover` (arc-global, NOT episode-filtered)

```json
"continuity_checkpoints": [
    "20억 자본금 확보 완료",
    "가족의 감시망에서 완전히 벗어남",
    "여의도 임시 사무실 계약 및 법인 설립 완료"
],
"foreshadow_anchors": [
    "저녁 뉴스에서 '유가 상승세, 이란 핵 문제 재점화' 보도",
    "아버지가 '그룹 일은 형들이 알아서 할 거다'라고 발언",
    "한시우의 '그룹 돈은 한 푼도 안 받겠다'는 선언"
],
"growth_justification": "미래 18년 치의 거시경제 지식 각성 및 초기 투자 자본 20억 원 확보"
```

All `continuity_checkpoints` describe arc-END milestones. These enter the ep1 prompt directly via `constraint_block["semantic_carryover"]`.

### 1.5 `state_constraints` (arc-level boundaries)

```json
"arc_start_state": {
    "capital": "0원",
    "equipment": ["개인 명의 예금통장", "신탁 펀드 증서", "승마 스폰서십 계약서"],
    "location": "서울 성북동, 재벌가 본가 저택 침실"
},
"arc_end_state": {
    "capital": "20억원",
    "equipment": ["SW인베스트먼트 법인 인감도장", "20억 예치 법인 계좌 OTP", "WTI 원유 선물 차트"],
    "location": "서울 여의도 증권가 이면도로에 위치한 낡은 오피스텔 4층, SW인베스트먼트 임시 사무실"
}
```

Code verification: `_extract_inherited_state()` at `bcc:478-487` reads only `arc_start_state` (not `arc_end_state`). For ep1, `inherited_state.equipment` correctly shows arc-start items. However, `joint_docs.physical_inventory` is read first (bcc:452-459) and then overwritten by `arc_start_state.equipment` (bcc:487). This path is clean.

### 1.6 `beat_sequence` (correctly per-episode)

```
"제 1화: 2024년 고독사 직후 2006년으로 회귀 → 18년 치 거시경제 데이터 복기 및 상황 수용 → 수동적 한량의 삶을 반복하지 않겠다는 결의",
"제 2화: 아버지 한정호 회장의 서재 호출 → 형들의 무관심 속에서 독자적인 투자사 설립 선언 → 그룹 지원 거절을 통한 완벽한 방관 확보",
"제 3화: 은행 PB 박성호와의 대면 → 신탁 펀드 해지 및 스폰서십 위약금 지불 강행 → 가용 자금 20억 원 전액 현금화 완료",
"제 4화: 여의도 낡은 오피스텔 임대 및 SW인베스트먼트 설립 → 법인 인감 및 계좌 OTP 확보 → 뉴스 보도를 통한 WTI 원유 투자 준비 완료"
```

---

## 2. Stage 3 Blueprint Truth

### 2.1 EP1 Blueprint (`attempt_09/final_blueprint__emotion_focused.json`)

Actual content covered:

| Scene | Content | Arc Episode Source |
|---|---|---|
| Scene 1 | 2024년 고독사 → 2006년 회귀 인지 | ep1 ✓ |
| Scene 2 | 편두통 → 18년 치 데이터 각성 | ep1 ✓ |
| Scene 3 | 승마 스폰서십/자산 현금화 → **20억 시드 머니 확보** | **ep3 LEAKED** |
| Scene 4 | **여의도 임시 사무실** → **법인 인감 + OTP 획득** | **ep4 LEAKED** |
| Scene 5 | **이란 핵 뉴스** → **WTI 레버리지 투자 준비** → 아버지 호출 | **ep4 LEAKED** |

`ending_state.protagonist_status`: "자본금 20억 확보 및 법인 설립을 완료하고 첫 투자를 목전에 둔 상태"
→ This is the ARC END STATE, not ep1's scope.

`protagonist_state.equipment`: ["SW인베스트먼트 법인 인감도장", "20억 예치 법인 계좌 OTP"]
→ EP4 items present at ep1 ending.

### 2.2 EP2 Blueprint (`attempt_01/final_blueprint__dialogue_focused.json`)

Content: 비서실장 호출 → 서재 대면 → 독립 선언 → 한정호 여의도 사무실 서류 발견

`ending_state.protagonist_status`: "초기 목적(독립 선언)을 달성했으나 아버지의 정보력에 허를 찔린 상태"

This is coherent with ep2's arc allocation. No overconsumption detected in the ep2 blueprint itself.

### 2.3 EP3 Blueprint (`attempt_01/final_blueprint__dialogue_focused.json`)

Content: 한정호 서재 결착 → K뱅크 PB 박성호 → 자금 현금화 → 20억 입금 확인

`ending_state.protagonist_status`: "법인 계좌로 20억 원 입금 확인 완료"

**Contradiction**: EP1's manuscript already depicted 20억 현금화 완료 and 법인 설립. EP3's blueprint mandates the same events again. Blueprint itself was generated correctly from arc allocation, but ep1's overconsumption made this redundant.

### 2.4 EP4 Blueprint (`attempt_02/final_blueprint__emotion_focused.json`)

Content: 비서실장 경고전화 → 오피스텔 계약 → HTS 세팅 → WTI 매수 직전

`ending_state.protagonist_status`: "WTI 매수 직전 과거의 트라우마와 마주하며 심리적 갈등을 겪음"

**Contradiction**: EP1's manuscript already depicted 오피스텔 계약, 법인 설립, WTI 투자 준비. EP4's blueprint mandates the same events again.

---

## 3. Stage 4 Verdict Chain

### 3.1 EP1 — Stage 4 Round 0

- Verdict: **PASS** (score 96)
- Gate: `director_primary_pass`
- Director reason: "Blueprint의 씬 구성과 타임라인을 가장 정확하게 반영했으며, 자본금 확보 과정과 레버리지 계산 등 투자물의 핵심 요소가 수학적 오류 없이 깔끔하게 서술"
- Observation: Director accepted because the manuscript was internally coherent and faithfully followed the (overconsummed) blueprint.

### 3.2 EP2 — Stage 4 Round 0

- Verdict: **PASS** (score 96)
- Gate: `director_primary_pass`
- Director reason: "직전 화 엔딩(비서실장의 호출과 손에 쥔 OTP)에서 완벽하게 이어지는 도입부"
- Observation: EP2 continues coherently from EP1 despite EP1's overconsumption.

### 3.3 EP3 — Stage 4 Rounds 0-2

| Round | Verdict | Score | Gate | Key Finding |
|---|---|---|---|---|
| R0 | PASS→REJECT | 95 | post_select_conflict | "Minor transition issue" — initially PASS, downgraded to REJECT |
| R1 | REJECT | 44/50 | continuity_firewall | "이전 화(EP 1)에서 이미 완료된 20억 원 현금화 및 OTP 수령 사건이 현재 화에서 다시 반복" |
| R2 | PASS | 95 | director_primary_pass | V75-D blueprint rewrite → new content bypasses the replay |

R1 firewall diagnosis: "Blueprint 자체가 이전 화의 진행 상황을 무시하고 작성되었습니다. 주인공은 이미 EP 1에서 20억 원을 법인 계좌로 이체받았고 OTP도 가지고 있는 상태"

### 3.4 EP4 — Stage 4 Rounds 0-2

| Round | Verdict | Score | Gate | Key Finding |
|---|---|---|---|---|
| R0 | REJECT | 30 | continuity_firewall | "직전 화에서 이미 완료된 오피스텔 계약, HTS 세팅, WTI 매수 진입을 모든 후보가 다시 반복" |
| R1 | inplace patch pass | 96 | post_select_conflict | constraint_violation fix |
| R2 | PASS (after V75-D) | — | — | Blueprint rewrite resolved the replay |

R0 firewall diagnosis: "Blueprint 자체가 3화의 내용을 반영하지 못하고 잘못 설계되었습니다. 작가(AI)들은 Blueprint를 따르다 보니 3화에서 이미 일어난 일들을 4화에서 다시 반복"

---

## 4. Cross-Episode Content Replay Ledger

| Content Item | Arc Assigns To | EP1 Blueprint Consumes? | EP3/EP4 Blueprint Mandates? | Stage 4 Catches? |
|---|---|---|---|---|
| 2024년 고독사 회귀 | ep1 | YES (scene 1) | — | — |
| 18년 치 데이터 각성 | ep1 | YES (scene 2) | — | — |
| 자산 현금화 20억 확보 | ep3 | **YES (scene 3)** | EP3 scene 2-4 | EP3 R1 firewall |
| 은행 PB 박성호 대면 | ep3 | NO | EP3 scene 2-3 | — |
| 여의도 오피스텔 계약 | ep4 | **YES (scene 4)** | EP4 scene 2 | EP4 R0 firewall |
| SW인베스트먼트 법인 설립 | ep4 | **YES (scene 4)** | EP4 scene 2 | EP4 R0 firewall |
| 법인 인감도장 획득 | ep4 (state_changes) | **YES (scene 4)** | EP4 scene 2 | EP4 R0 firewall |
| 20억 OTP 획득 | ep4 (state_changes) | **YES (scene 4)** | EP4 scene 2 | EP4 R0 firewall |
| 이란 핵 뉴스 확인 | ep4 | **YES (scene 5)** | EP4 scene 4 | subsumed |
| WTI 투자 준비 | ep4 | **YES (scene 5)** | EP4 scene 3-4 | EP4 R0 firewall |
| HTS 세팅 | ep4 | implied (scene 5) | EP4 scene 3 | EP4 R0 firewall |
| 아버지 서재 호출 | ep2 | YES (scene 5 hook) | EP2 scene 1 | no conflict |
| 독립 선언 | ep2 | NO | EP2 scene 3-5 | — |

---

## 5. Contamination Source Mapping

### Fields that leaked ep3/ep4 content into ep1:

| Field | Content Matching EP3/EP4 | Enters EP1 Prompt? | Wave 1 Fixed? |
|---|---|---|---|
| `state_changes.major_items` (ep4) | 법인 인감, OTP | YES (via `_summarize_state_changes`) | **YES** (filtered by ep<=current) |
| `treatment_block` event fields | event_villain, solution, reward | YES (via `_inject_stage3_treatment_block_context`) | **YES** (quarantined) |
| `stop_line` | only blocked ep+1 | YES | **YES** (expanded to all future) |
| `semantic_carryover.continuity_checkpoints` | "20억 자본금 확보", "법인 설립 완료" | **YES** (via constraint_block) | **NO** |
| `semantic_carryover.foreshadow_anchors` | "유가 상승세, 이란 핵" | **YES** (via constraint_block) | **NO** |
| `semantic_carryover.growth_justification` | "초기 투자 자본 20억 원 확보" | **YES** (via constraint_block) | **NO** |
| `joint_docs.physical_inventory` | 법인 인감, OTP, WTI 차트 | INDIRECT (via inherited_state, overwritten by arc_start) | N/A (overwritten) |
| `joint_docs.final_location` | 여의도 오피스텔 | NOT directly in constraint_block | N/A |
| `joint_docs.world_joint` | 20억 달러 환전 대기 | NOT directly in constraint_block | N/A |
| `state_constraints.arc_end_state` | 20억, 법인 인감, OTP | NOT directly (only arc_start enters) | N/A |

### Residual unfiltered paths after Wave 1:

1. **`semantic_carryover`** — enters constraint_block directly at `bcc:97`, passed to prompt at `bcc:132-134`. Contains arc-END continuity checkpoints and foreshadow anchors. NOT episode-filtered.

2. **Treatment block framing** — Wave 1 quarantined event fields but arc-framing narrative (character arcs, tactical overview) may still contain enough future-episode detail. Needs separate lane (T6) verification.
