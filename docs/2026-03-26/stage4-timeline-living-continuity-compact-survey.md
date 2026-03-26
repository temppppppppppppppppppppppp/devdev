# Stage 4 Timeline / Living-Continuity Gap — Compact Survey

Date: 2026-03-26
Type: static survey (compact, post-Wave-2 classification)
Scope: remaining non-IFC Stage 4 timeline handoff and living-state continuity seam
Mode: survey-only, no code changes
Prior Evidence:
- `docs/2026-03-25/stage4-ifc-structural-extraction-wave2-canary-report.md`
- `docs/2026-03-25/stage4-chiefwriter-state-injection-wave1-canary-report.md`

## Evidence Surfaces Inspected

| Surface | Path | Key Lines |
|---------|------|-----------|
| CW prompt template | `chief_writer_prompts.py` | L108 (chain_link slot), L129-134 (STEP 0.5 authority hierarchy) |
| CW context builder | `chief_writer_context.py` | L150 (chain_link param), L206-212 (IFC build), L260 (direct injection) |
| CW context packets | `chief_writer_context_packets.py` | L313-438 (digest: location yes, time_marker no, pending_actions no, transportation no) |
| Stage4 context builder | `stage4_context_builder.py` | L1369-1404 (chain_link rendering: all 6 fields included) |
| IFC extraction | `stage4_immutable_fact_contract.py` | L114 (chain_link param), L200-233 (completed_event_facts extraction) |
| chain_link_4 DB anchor | canary project DB | cliffhanger, pending_actions, location, time_marker — all populated |
| EP4 final manuscript | `canary_0325_stage4_wave2/artifacts/stage4/ep_0004/attempt_01/` | Ends mid-sentence: "레버리지 한도 끝까지 열어서..." |
| EP5 attempt_01 manuscript | `canary_0325_stage4_wave2/artifacts/stage4/ep_0005/attempt_01/` | "내일 오전 9시, 지점으로 직접 가서 최종 서명" + "검은색 세단" |
| EP5 attempt_03 manuscript | `canary_0325_stage4_wave2/artifacts/stage4/ep_0005/attempt_03/` | "위험고지서" 추가됨 but "검은색 세단" 지속 |
| EP5 attempt_04 manuscript | `canary_0325_stage4_wave2/artifacts/stage4/ep_0005/attempt_04/` | "모범택시" + 시스템 제약 우회 → PASS |

## Findings

### F1. chain_link timeline facts ARE present in the CW prompt — but NOT ranked in the authority hierarchy

**chain_link rendering** (`stage4_context_builder.py` L1369-1404): All 6 fields are rendered into `chain_link_section`:
- `cliffhanger` → "진행 중 상황"
- `pending_actions` → "해야 할 행동"
- `emotional_state` → "감정 상태"
- `physical_state` → "신체 상태" (only if != "정상")
- `location` → "현재 위치"
- `time_marker` → "작중 시간"

The section header is: `### [V68] 직전 화 연결고리 - 반드시 이어받을 것`

**chain_link injection** (`chief_writer_prompts.py` L108): Injected standalone between `{incarnation_context_section}` and `{ending_hook_section}` — relatively high placement (before scene_breakdown).

**Authority hierarchy** (`chief_writer_prompts.py` L129-134):
```
1. Opening Anchor
2. Immutable Facts / prior manuscript facts / prev digest
3. Structured scene breakdown
4. Advisory integrated scenario prose
```

**chain_link is NOT listed.** When blueprint scene_breakdown contradicts chain_link timeline, CW has no explicit priority rule. chain_link says "반드시 이어받을 것" inside its own section, but this self-declared authority is not reinforced by the STEP 0.5 hierarchy that CW is trained to follow.

### F2. prev_digest does NOT extract time_marker or pending_actions

**Digest extraction** (`chief_writer_context_packets.py` L313-438): The Python-based digest (`_generate_episode_digest`) extracts:
- ✓ 마지막 위치 (last location) — L374
- ✓ 부상 상태 (injury) — L363
- ✓ 사망 NPC — L340
- ✓ 클리프행어 꼬리 (cliffhanger tail) — L415
- ✓ 확정 자본 (capital amounts) — L419-425
- ✓ 소도구/장비 (props: 수트, 재킷, 모니터) — L427-436
- ✗ **작중 시간** (time_marker) — NOT extracted
- ✗ **미완 행동** (pending_actions) — NOT extracted
- ✗ **교통수단** (transportation mode) — NOT extracted

The digest reaches CW via `{prev_digest}` at prompt L154 (STEP 2: 연속성 확인). It has a structured format but no time-of-day or pending-action continuity.

### F3. IFC completed_event_facts only extract COMPLETION keywords from chain_link — not PENDING actions

**IFC extraction** (`stage4_immutable_fact_contract.py` L200-233): `_extract_completed_event_facts()` reads chain_link_section and extracts lines containing completion verbs (`완료`, `달성`, `세팅`, etc.).

chain_link_4 `pending_actions`:
```
- 박성호 팀장을 통한 WTI 원유 선물 최대 레버리지 매수 주문 완료
```
This line contains "완료" → would be extracted as a **completed event** fact with ⛔ "이미 끝난 사건을 미해결인 것처럼 다시 서술하면 불합격."

**But the other pending_actions**:
```
- 주문 체결 후 이란 핵 위기 뉴스에 따른 유가 폭등 및 차트 변동 확인
- 막대한 평가 수익 발생 확인 및 포지션 유지/청산 결정
```
These contain "확인" (Wave 2 keyword) → also extracted. But they're **FUTURE actions**, not completed ones. Labeling them "이미 끝난 사건" is semantically incorrect — they're things that NEED to happen, not things that already happened.

**Structural mismatch**: The IFC completed_event path treats all chain_link lines with completion keywords as "done" — but chain_link pending_actions are "to-do" items. The extraction pipeline doesn't distinguish between completed vs pending.

### F4. Canary EP5 confirms chain_link timeline is present but overridden by CW improvisation

**chain_link_4 says**:
- cliffhanger: "매수 주문 지시를 내리는 찰나에 끊김"
- location: "SW인베스트먼트 사무실 (새로 구축된 통제실)"
- time_marker: "다음 날 오후 늦은 시간"
- pending_actions[0]: "WTI 원유 선물 최대 레버리지 매수 주문 완료"

**EP5 R1 CW wrote**: "내일 오전 9시, 제가 지점으로 직접 가서 최종 서명하고 진입할 겁니다" + "검은색 세단"

CW violations against chain_link:
- ✗ Location: chain_link says "사무실" → CW wrote "지점 방문"
- ✗ Timeline: chain_link says "찰나에 끊김" (즉시 계속) → CW wrote "내일"
- ✗ Transportation: chain_link has no transportation data → CW improvised "세단" (inconsistent with EP1-4 "택시")

**EP5 R4 (PASS) resolved it**: CW invented a system constraint ("위험고지서 대면 서명 전에는 3배 레버리지 주문이 시스템상 안 됨") to justify the timeline gap, used "모범택시", and avoided reopening setup.

### F5. EP4 shows the same pattern at smaller scale

**EP4 R1**: post-select caught "이미 완료된 가계약을 다시 진행" — CW reopened a completed action.
**EP4 R2 (PASS)**: CW resolved it with "어제 가계약했던 사무실의 잔금을 치르고 즉시 입주" — creative reinterpretation.

chain_link_3 had `pending_actions: ["WTI 원유 선물 롱 포지션 진입"]` and `location: "증권사 인근 고급 라운지 카페"`. EP4 R1 CW moved the location correctly but repeated a completed action.

## Classification

### Facts Already Injected But Not Obeyed

| Fact | Injection Path | Authority | CW Compliance |
|------|---------------|-----------|---------------|
| chain_link cliffhanger ("매수 주문 찰나에 끊김") | Direct injection L108 | MEDIUM ("반드시 이어받을 것") | **Ignored R1-R3**, obeyed R4 |
| chain_link pending_actions ("매수 주문 완료") | Direct injection L108 + IFC completed_event (⛔) | MEDIUM+HIGH mixed | **Confused**: treated as "to-do" not "done" in R1 |
| chain_link location ("사무실") | Direct injection L108 | MEDIUM | **Overridden** by CW's "지점" in R1-R3 |
| chain_link time_marker ("오후 늦은 시간") | Direct injection L108 | MEDIUM | **Replaced** by "내일 오전 9시" in R1-R3 |
| prev_ending_bridge (EP4 mid-sentence) | IFC opening anchor | MEDIUM (raw text) | **Not continued** — R1 started new dialogue |

### Facts Missing From Injection

| Fact | Why Missing | Impact |
|------|------------|--------|
| Transportation mode (택시 vs 세단) | Not tracked in chain_link, fact_ledger, or digest | EP5 R1-R3 "검은색 세단" inconsistency |
| Time-of-day in prev_digest | Digest doesn't extract time_marker | CW has no structured time continuity from digest path |
| Pending vs completed action distinction | IFC extracts both as "completed events" | Semantic confusion between "to-do" and "done" |

### Facts Caught Only Late by Director / Post-Select

| Fact | Caught By | Round |
|------|-----------|-------|
| 가계약 타임라인 반복 (EP4) | Post-select | R1 |
| 계좌 세팅 완료 → 다시 서류 서명 (EP5) | Post-select | R1 |
| EP4 대사 vs EP5 대사 논리적 모순 (EP5) | **Director** | R2 |
| 택시 vs 전용 세단 (EP5) | Post-select | R3 |

## Root Cause Summary

The dominant remaining gap is: **chain_link authority underweight**.

chain_link contains all the correct timeline data (cliffhanger, pending_actions, location, time_marker), and it IS injected into the CW prompt. But:
1. It is **not ranked in STEP 0.5 authority hierarchy** — CW treats it as advisory, not as a hard constraint
2. Its `pending_actions` are **semantically misrouted** through IFC completed_event_facts — future actions labeled as "이미 끝난 사건"
3. `prev_digest` **doesn't reinforce** time-of-day or pending actions — only location and cliffhanger tail
4. Transportation/living-state is **not tracked** anywhere

Of these, (1) is the root cause. If chain_link were ranked in the authority hierarchy (between Opening Anchor and scene_breakdown), CW would not override its timeline/location data.

(2) is a secondary structural issue that would need IFC packet changes (new "pending continuation" field distinct from "completed events"). This is a larger blast radius.

(3) is nice-to-have but low ROI — digest is a backup path, not the primary timeline injection.

(4) is not addressable by any current mechanism — transportation mode would need a new fact_ledger or chain_link field.

## Single Recommendation

**No wave yet.** Rationale:

1. **Self-correction is working**: EP4 resolves in R2, EP5 in R4. The CW finds creative workarounds ("위험고지서 시스템 제약", "어제 가계약 잔금") that maintain narrative coherence.

2. **Both viable fixes touch new files outside the IFC scope**:
   - chain_link authority promotion → `chief_writer_prompts.py` (CW prompt template, affects all genres)
   - IFC pending-action section → `stage4_immutable_fact_contract.py` (new field/function/rendering, structural IFC change)

3. **Total retry cost is acceptable**: 11 attempts for 5 episodes. Baseline was 21+. The 3 extra rounds (EP4 R1 + EP5 R1-R3) cost API tokens but don't hang or fail.

4. **Insufficient episode data**: Only EP4-EP5 show the pattern. Whether this is an arc-boundary phenomenon (EP4=arc ending, EP5=new arc start) or a general pattern needs more data from EP6-EP8.

5. **Wave 1+2 ROI is already captured**: Attempts -48%, REJECT -60%, account ownership resolved, resource balance resolved. Diminishing returns on further IFC-scope work.

**If a future wave is warranted after more episode data**, the two candidate moves in priority order are:
1. **chain_link authority promotion** (1-line change in `chief_writer_prompts.py` STEP 0.5 — lowest blast radius)
2. **IFC pending-continuation section** (new packet field + extraction + rendering — proven IFC path but larger change)

## Guardrails
- Do not reopen IFC keyword expansion (Wave 1+2 scope exhausted)
- Do not redesign Director rubric in this assessment
- Do not change Stage 3 blueprint generation
- Do not modify retry/ASP/post-select policy
- Do not change world_state or fact_ledger data model

---

## 3-Pass Audit Notes
- Pass 1: scope bounded to timeline/living-continuity seam only; 7 code surfaces + canary artifacts inspected; excluded surfaces listed
- Pass 2: all findings anchored to file/line references, chain_link_4 DB content, and EP5 manuscript artifacts; no overclaiming; chain_link authority gap confirmed against both static code and live canary evidence
- Pass 3: recommendation is bounded (no action); candidate future moves identified with blast radius assessment; no scope creep
- Confidence: 96%

---

- Dominant remaining Stage 4 seam: **chain-link-authority-underweight** (timeline data present but not ⛔-ranked in CW hierarchy)
- Best next single move: **no wave yet** (self-correction working, more episode data needed, viable fixes touch new files outside IFC scope)
- Should Codex open an execution SSOT now: **no**
