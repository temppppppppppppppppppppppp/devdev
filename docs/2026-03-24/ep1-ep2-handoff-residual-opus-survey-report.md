# EP1→EP2 Handoff Residual Survey Report

> Survey Date: 2026-03-24
> Surveyor: Antigravity (Opus-class)
> Project: `projects/00_0324_2`
> Scope: ep1 → ep2 handoff only — survey only, no code changes

---

## 1. Executive Summary

The ep2 production run failed 3 consecutive times before passing on attempt 4, with all rejections caused by post-select continuity/history conflict detection. This survey traces each conflict to its origin layer (Stage 3 blueprint vs Stage 4 candidate expansion) using direct artifact evidence.

**Verdict: Mixed seam, Stage 3 primary.**

The EP2 blueprint's `integrated_scenario` field introduced three foundational violations that do not appear in the EP1 artifact trail:
1. An encrypted burner phone ("대포폰") and pre-existing criminal-finance network
2. Complete WTI calculation repetition (already completed in EP1)
3. Offshore broker infrastructure (Virgin Islands paper company, Swiss accounts)

Stage 4's writer LLM then amplified these with its own errors:
- Body position mismatch (침대 vs 창가) — corrected by attempt 3
- Note content state mismatch (빈 종이 vs 절반 채워짐) — corrected by attempt 4
- Re-opening the drawer for an already-out notebook — corrected by attempt 2

The post-select rejects were **mostly valid** — the conflicts they detected were real artifact-truth violations.

---

## 2. Included Coverage / Exclusions

### Evidence Surfaces Read
| Surface | Path | Status |
|---|---|---|
| EP1 Blueprint | `logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__emotion_focused.json` | ✅ Read |
| EP2 Blueprint | `logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json` | ✅ Read |
| EP1 Final Manuscript | `logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__A.txt` | ✅ Read |
| EP2 Attempt 1 (rejected) | `logs/artifacts/stage4/ep_0002/attempt_01/rejected_best__A_tension.txt` | ✅ Read |
| EP2 Attempt 2 (rejected) | `logs/artifacts/stage4/ep_0002/attempt_02/rejected_best__A_inplace_patch.txt` | ✅ Read |
| EP2 Attempt 3 (rejected) | `logs/artifacts/stage4/ep_0002/attempt_03/rejected_best__A_inplace_patch.txt` | ✅ Read |
| EP2 Attempt 4 (selected) | `logs/artifacts/stage4/ep_0002/attempt_04/selected_before_fix__A.txt` | ✅ Read |
| Console log | `docs/2026-03-24/console.txt` | ✅ Read (user-provided earlier) |

### Exclusions
- Stage 2 arc design quality is out of scope per user constraint.
- Code-path analysis of stage3/stage4 orchestrators not performed (survey-only).
- `episode_production.jsonl` not read in full — console log was sufficient for reject-reason tracing.

---

## 3. EP1 Fact Ledger

Facts established by EP1 final manuscript (`final_manuscript__A.txt`, 103 lines, 10008 bytes):

| Fact | Evidence Line(s) | Anchor |
|---|---|---|
| **Ending location**: 침실 창가 (standing at window) | L87: "노트의 마지막 장을 덮고…창가로 다가섰다" | Hard |
| **Body position**: standing upright at window | L103: "창문에 비친…얼굴…겹쳐졌다" | Hard |
| **Note ownership**: 가죽 양장 노트 + 몽블랑 만년필 | L62: "서랍을 열어…꺼냈다" | Hard |
| **Note content state**: 절반 빼곡히 채워짐 | L82: "노트의 절반을 빼곡하게 채운 뒤에야" | Hard |
| **Note physical location**: 책상 위 (closed, after use) | L87: "노트의 마지막 장을 덮고" → moved to window | Note is on desk, not in drawer |
| **WTI planning state**: fully calculated | L78: "원금 20억으로 3배 레버리지…수익금만 18억" | Hard — complete computation done |
| **WTI entry/exit**: 60달러 진입, 78달러 청산 | L70, L78 | Hard |
| **Persona**: 온실 속 화초, 승마 국가대표 | L91-95 | Hard |
| **Available network**: NONE — no phone calls, no broker contacts, no operational infrastructure | Entire manuscript is internal monologue only | Hard |
| **Available assets mentioned**: 가죽 양장 노트, 몽블랑 만년필 only | L62 | Hard |
| **SW인베스트먼트 mention**: name + 20억 시드머니 goal stated | L101 | Planning only — not executed |

---

## 4. EP2 Blueprint Conflict Ledger

Analysis of EP2 blueprint (`final_blueprint__emotion_focused.json`, 120 lines):

### 4A. Correctly Handled

| Item | Blueprint Field | Assessment |
|---|---|---|
| Start location: 침실 (window) | `start_location`: "성북동 본가 저택 한시우의 침실" | ✅ Consistent with ep1 ending |
| Scene 1 opening: window position | `scene_1.key_events[0]`: "창문에 비친 자신의 모습을 보며" | ✅ Correct handoff |
| Equipment carryover | `protagonist_state.equipment`: 가죽 양장 노트, 몽블랑 만년필 | ✅ Correct |

### 4B. Blueprint-Originated Conflicts

| Conflict | Blueprint Field | Severity | EP1 Evidence |
|---|---|---|---|
| **C1: 대포폰 + criminal-finance network** | `integrated_scenario`: "대포폰을 집어 들고 단축 번호를 눌렀다"…"박 사장"…"청담동의 음성적인 딜러" | **MAJOR** | EP1 has zero operational infrastructure. Protagonist is described as 온실 속 화초 with no business experience. The blueprint introduces a ready-to-use encrypted phone, a trusted fence ("박 사장"), and "음성적인 딜러" network with no narrative justification. |
| **C2: Overseas broker + offshore infrastructure** | `integrated_scenario`: "해외에 있는 프라이빗 브로커"…"버진아일랜드 쪽에 페이퍼 컴퍼니"…"스위스" | **MAJOR** | EP1 establishes protagonist as spoiled rich kid who never earned money independently. Having an offshore broker on speed-dial contradicts the "온실 속 화초" persona established in EP1. |
| **C3: WTI calculation repetition** | `scene_3.key_events`: "배럴당 60달러 선의 조정기를 진입 타이밍으로 설정"…"78달러 부근에서 청산" plus `integrated_scenario` re-computes 레버리지/수익 | **MODERATE** | EP1 L78 already computed this identically: "원금 20억으로 3배 레버리지…수익금만 18억". Blueprint asks the writer to redo this calculation, creating narrative redundancy. |
| **C4: Note content state ambiguity** | Blueprint scene_2 does not specify note state | **MINOR (planning pressure)** | EP1 established note as "절반 빼곡히 채워짐". Blueprint doesn't carry this fact, leaving Stage 4 to guess. Not a hard contradiction — an omission. |

### 4C. Key Observation

The `integrated_scenario` field is where the major violations originate. This field appears to be a long narrative draft generated by the blueprint LLM that the Stage 4 writer then follows closely. The `scene_breakdown.key_events` are somewhat cleaner (they mention "사치품을 음성 딜러에게 넘겨" but don't explicitly introduce 대포폰), but the `integrated_scenario` — which carries the most narrative weight — introduces all the operational infrastructure, phone calls, and computation repetition.

**This is a Stage 3 output problem, not a Stage 4 invention.**

---

## 5. EP2 Stage4 Expansion Conflict Ledger

Conflicts introduced or amplified by Stage 4 writer beyond what the blueprint specified:

| Conflict | Attempt(s) | Severity | Origin |
|---|---|---|---|
| **S1: Body position — 침대 기상** | Attempts 1, 2 (씬1 L22: "침대에서 천천히 몸을 일으켰다") | **MAJOR** | Pure Stage 4 invention. Blueprint scene_1 clearly says "창문에 비친 자신의 모습을 보며". Writer ignored this and started protagonist from bed. **Fixed in attempt 3**: "창가에서 돌아서서 방 안을 가로질렀다". |
| **S2: Note state — 빈 종이** | Attempts 1, 2 (씬2 L29: "텅 빈 종이 위로") | **MAJOR** | Stage 4 invention. EP1 established note as half-filled. Blueprint doesn't specify, so writer defaulted to empty. **Fixed in attempt 3**: "절반쯤 채워진 종이의 여백". **Fully fixed in attempt 4**: "18년치의 미래 지표들로 절반을 빼곡히 채워 넣은 노트의 다음 여백". |
| **S3: Re-opening drawer** | Attempt 1 (씬2 L29: "서랍을 열고…꺼내 펼쳤다") | **MINOR** | EP1 ends with note on desk (closed but out of drawer, protagonist at window). Writer put notebook back in drawer. **Fixed in attempt 2**: "책상 위에 놓인 두꺼운 가죽 양장 노트를 펼쳤다". |
| **S4: 대포폰 and broker calls (faithful to blueprint)** | All 4 attempts | **MAJOR but blueprint-originated** | Stage 4 faithfully reproduced the blueprint's `integrated_scenario` phone calls. This is not a Stage 4 expansion — it's compliance with a flawed blueprint. |
| **S5: WTI repetition (faithful to blueprint)** | All 4 attempts | **MODERATE but blueprint-originated** | Stage 4 follows blueprint scene_3 which asks for WTI timeline check. Same numbers repeated. |
| **S6: Attempt 4 contact softening** | Attempt 4 씬2 L35: "서랍 구석에 방치해 두었던 예전 휴대폰" + "승마장 VIP 모임에서 알게 된…청담동 업자" | **Partial mitigation** | Attempt 4 replaced "암호화된 대포폰" with "예전 휴대폰" and "프라이빗 브로커" with "유학 시절 알게 된 해외 법인 설립 대행사의 에이전트" — somewhat more plausible for a 재벌가 2세, though still a stretch for a 26-year-old 온실 속 화초. |

---

## 6. Conflict Origin Assessment

| Conflict | Origin Layer | Confidence |
|---|---|---|
| 대포폰 / criminal-finance network | **Stage 3 blueprint** (`integrated_scenario`) | 95% — text is present verbatim in blueprint |
| Offshore broker / paper company | **Stage 3 blueprint** (`integrated_scenario`) | 95% — text is present verbatim in blueprint |
| WTI calculation repetition | **Stage 3 blueprint** (scene_3 design + `integrated_scenario`) | 90% — blueprint explicitly asks for this scene |
| Body position (침대 vs 창가) | **Stage 4 candidate expansion** | 95% — blueprint scene_1 says 창가, writer ignored it |
| Note content (빈 종이 vs 절반) | **Stage 4 candidate expansion** | 90% — blueprint omits state, writer defaulted wrong |
| Note physical location (drawer vs desk) | **Stage 4 candidate expansion** | 85% — ambiguous in blueprint, writer chose wrong |

---

## 7. Cleared Non-Culprits

| Suspect | Status | Reason |
|---|---|---|
| Stage 2 arc design | **Cleared** | Arc correctly specifies episode boundaries and events. The satchel/phone/broker issues are not in the arc. |
| Blueprint `scene_breakdown.key_events` | **Mostly cleared** | The key_events don't introduce 대포폰 or broker by name. The damage is in `integrated_scenario`. |
| Post-select reject system | **Cleared — mostly valid** | The continuity/history conflict detectors correctly identified real problems. The rejects were warranted. |
| Director primary pass scoring | **Cleared but notable** | Director gave PASS scores of 94-100 to manuscripts that were subsequently REJECT-downgraded by post-select checks. This suggests Director's primary scoring doesn't inspect inter-episode artifact continuity deeply enough, but this was caught by the post-select lane. Working as designed. |

---

## 8. Best Current Interpretation

The ep1→ep2 handoff failure is a **mixed seam with Stage 3 as the dominant contributor**.

### Stage 3 (Blueprint) — Primary Culprit

The blueprint's `integrated_scenario` field acts as a high-authority narrative draft that the Stage 4 writer follows closely. For ep2, this field introduced:
- A fully operational criminal-finance infrastructure (대포폰, 박 사장, 청담동 딜러, 해외 브로커 "제임스", 버진아일랜드 페이퍼 컴퍼니, 스위스 계좌) that is wildly inconsistent with the protagonist's established persona (온실 속 화초, no independent financial experience, 26-year-old regressor who never made money)
- A full re-computation of the WTI investment that was already completed in EP1

These are not planning pressure — they are **hard persona contradictions** baked into the blueprint's narrative draft. The Stage 4 writer cannot escape them without ignoring the blueprint, which it is not designed to do.

### Stage 4 (Writer) — Secondary Amplifier

Stage 4 added its own errors:
- Body position regression (침대 vs 창가) — fixable and was fixed
- Note state regression (빈 종이 vs 절반) — fixable and was fixed
- Drawer re-opening — fixable and was fixed

These are the kind of carryover-state errors that the Stage 4 writer commonly makes when the previous-episode context is insufficient in the prompt. They were successfully corrected through the retry loop.

### Why Attempt 4 Finally Passed

Attempt 4 resolved all Stage 4 expansion errors (body position, note state, drawer) AND softened the blueprint's persona violation (replacing 대포폰 with "예전 휴대폰" and offshore broker with "유학 시절 에이전트"). The post-select check on attempt 4 found a minor remaining continuity issue about notebook content description but after an inplace fix, it passed.

---

## 9. Confidence And Limits

| Claim | Confidence | Limit |
|---|---|---|
| 대포폰/broker originates in Stage 3 blueprint | 95% | Could verify further via `stage3_orchestrator.py` prompt injection logic |
| WTI repetition originates in Stage 3 blueprint | 90% | Blueprint scene_3 design explicitly asks for this |
| Body position error is Stage 4 only | 95% | Blueprint scene_1.key_events correctly specifies 창가 |
| Note state error is Stage 4 only | 85% | Blueprint omits state — could be improved with explicit carryover |
| Post-select rejects were valid | 90% | All detected conflicts are real artifact-truth violations |
| `integrated_scenario` is the dominant contamination vector | 85% | Would need code analysis of how Stage 4 writer uses this field vs `scene_breakdown` to confirm weight |

### Not Proven
- Whether Stage 4's writer prompt gives `integrated_scenario` higher weight than `scene_breakdown.key_events` (code analysis needed)
- Whether the constraint compiler or entity registry could have blocked the 대포폰 introduction at blueprint time
- Whether a different blueprint strategy (dialogue_focused, tension_focused) would have produced the same violations

---

## Mandatory Final Lines

- **Dominant seam**: mixed seam (Stage 3 primary, Stage 4 secondary)
- **Are the post-select rejects mostly valid**: yes
- **Should Codex open an execution SSOT immediately**: no (user constraint: survey only, no execution SSOTs)
