Date: 2026-03-24
Status: final
Document Type: evidence ledger (T2)
Lane: Stage 2 Arc Payload
Canonical Path: `docs/2026-03-24/opus-residual/t2-stage2-arc-payload-evidence.md`

---

# T2 Evidence Ledger — Stage 2 Arc Payload

## EV-1. Arc Payload `semantic_carryover` Raw Content

Source: `projects/00_001/logs/artifacts/stage2/arc_001/attempt_01/final_arc__balanced.json:155-184`

```json
"semantic_carryover": {
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
    "growth_justification": "미래 18년 치의 거시경제 지식 각성 및 초기 투자 자본 20억 원 확보",
    "relationship_rationale": [
        { "npc": "한정호 (아버지)", "trigger": "독자적인 투자사 설립 및 자립 선언", "justification": "항상 순종적이던 막내가 처음으로 자신의 길을 가겠다고 명확히 선언함" },
        { "npc": "한태준 (큰형)", "trigger": "막내의 사업 선언", "justification": "막내가 무엇을 하든 자신의 후계 경쟁에는 전혀 영향이 없다고 판단함" },
        { "npc": "한태민 (둘째형)", "trigger": "막내의 사업 선언", "justification": "경쟁자가 될 수도 있었던 막내가 알아서 그룹 밖으로 빠져준다고 생각함" }
    ]
}
```

Episode attribution:
- `continuity_checkpoints[0]` "20억 자본금 확보 완료" → EP3 event (은행 PB 만나 현금화)
- `continuity_checkpoints[1]` "가족의 감시망에서 완전히 벗어남" → EP2 event (서재 선언)
- `continuity_checkpoints[2]` "여의도 임시 사무실 계약 및 법인 설립 완료" → EP4 event (오피스텔 계약, 법인 설립)
- `foreshadow_anchors[0]` → EP4 event (뉴스 시청)
- `foreshadow_anchors[1]` → EP2 event (아버지 발언)
- `foreshadow_anchors[2]` → EP2 event (시우 선언)
- `growth_justification` → EP3 result (20억 확보)
- `relationship_rationale` → all EP2 events (사업 선언)

## EV-2. `semantic_carryover` Prompt Rendering Path

Code path: `compile()` L97 → `_normalize_semantic_carryover()` L654-699 → `compile_to_prompt()` L132-136 → `_format_semantic_carryover_lines()` L702-729

`_format_semantic_carryover_lines()` at `blueprint_constraint_compiler.py:702-729`:
```python
def _format_semantic_carryover_lines(payload: object) -> list[str]:
    lines = []
    for entry in payload.get("relationship_rationale", []) or []:
        npc = str(entry.get("npc", "") or "").strip() or "?"
        cue = str(entry.get("trigger", "") or entry.get("justification", "") or "").strip()
        if cue:
            lines.append(f"- relationship {npc}: {cue[:120]}")
    growth = str(payload.get("growth_justification", "") or "").strip()
    if growth:
        lines.append(f"- growth_justification: {growth[:140]}")
    for anchor in (payload.get("foreshadow_anchors", []) or [])[:3]:
        text = str(anchor or "").strip()
        if text:
            lines.append(f"- foreshadow: {text[:120]}")
    checkpoints = [str(item or "").strip()[:80] for item in (payload.get("continuity_checkpoints", []) or [])[:3]]
    checkpoints = [item for item in checkpoints if item]
    if checkpoints:
        lines.append(f"- continuity: {'; '.join(checkpoints)}")
    return lines
```

**No `ep_num` parameter. No episode filtering. All content passes through to prompt.**

Rendered output for EP1 (reconstructed):
```
### ARC semantic carryover
- relationship 한정호 (아버지): 독자적인 투자사 설립 및 자립 선언
- relationship 한태준 (큰형): 막내의 사업 선언
- relationship 한태민 (둘째형): 막내의 사업 선언
- growth_justification: 미래 18년 치의 거시경제 지식 각성 및 초기 투자 자본 20억 원 확보
- foreshadow: 저녁 뉴스에서 '유가 상승세, 이란 핵 문제 재점화' 보도
- foreshadow: 아버지가 '그룹 일은 형들이 알아서 할 거다'라고 발언
- foreshadow: 한시우의 '그룹 돈은 한 푼도 안 받겠다'는 선언
- continuity: 20억 자본금 확보 완료; 가족의 감시망에서 완전히 벗어남; 여의도 임시 사무실 계약 및 법인 설립 완료
```

## EV-3. EP1 Blueprint Overconsumption Match

Source: `stage3/ep_0001/attempt_09/final_blueprint__emotion_focused.json`

| semantic_carryover content | EP1 blueprint match |
|---|---|
| continuity: "20억 자본금 확보 완료" | ending_state: "자본금 20억 확보" |
| continuity: "법인 설립 완료" | ending_state: "법인 설립을 완료" |
| continuity: "가족의 감시망에서 완전히 벗어남" | scene_4: "가족들의 무관심 속에서... 독자적인 투자사 설립을 완료" |
| growth: "투자 자본 20억 원 확보" | equipment: ["20억 예치 법인 계좌 OTP"] |
| foreshadow: "이란 핵 문제 재점화" | scene_5: "이란 핵 문제 관련 뉴스 보도 확인" |
| relationship: "투자사 설립 선언" | scene_4: "SW인베스트먼트 법인 인감도장... 획득" |

**Direct 1:1 match between `semantic_carryover` content and EP1 overconsumption.**

## EV-4. `_extract_immutable_fact_carryover()` No-Filter Code

Source: `blueprint_constraint_compiler.py:506-550`

```python
def _extract_immutable_fact_carryover(arc_data: dict, arc_position: int) -> str:
    if arc_position <= 1:
        return ""
    state_changes = arc_data.get("state_changes", {})
    # NPC deaths — NO episode filter
    deaths = state_changes.get("npc_deaths", [])
    for d in (deaths or [])[:5]:
        ...
    # Relationship changes — NO episode filter
    for rel in (state_changes.get("relationship_changes") or [])[:5]:
        ...
    # Major items — NO episode filter
    for item in (state_changes.get("major_items") or [])[:5]:
        ...
    # Skill acquisitions — NO episode filter
    for skill in (state_changes.get("skill_acquisitions") or [])[:3]:
        ...
```

Contrast with `_summarize_state_changes()` (L552-651) which has `_within_ep()` filter (Wave 1 fix).

## EV-5. `state_changes` Entries with `episode: null`

Source: `final_arc__balanced.json:213-235`

```json
"relationship_changes": [
    { "episode": 2, "npc": "한정호", "from": "기대 제로", "to": "의외라는 시선" },
    { "episode": null, "npc": "한정호 (아버지)", "from": "귀여운 막내, 기대 제로", "to": "의외라는 시선, 약간의 관심..." },
    { "episode": null, "npc": "한태준 (큰형)", "from": "무관심", "to": "무관심 유지..." },
    { "episode": null, "npc": "한태민 (둘째형)", "from": "무관심", "to": "무관심 유지..." }
]
```

`_within_ep()` filter at L564-575:
```python
ep_val = entry.get("episode")
if ep_val is None:
    return True  # null entries pass through
```

For EP1 (`ep_num=1`): the `episode=2` entry is correctly filtered out, but all three `episode=null` entries pass through.

## EV-6. `joint_docs` Override Chain

Source: `blueprint_constraint_compiler.py:445-503`

Step 1 (L452-459): `joint_docs.physical_inventory` sets equipment to EP4 items:
```
["SW인베스트먼트 법인 인감도장", "20억 예치 법인 계좌 OTP", "WTI 원유 선물 차트"]
```

Step 2 (L478-487): `arc_start_state.equipment` OVERRIDES to EP1 items:
```
["개인 명의 예금통장", "신탁 펀드 증서", "승마 스폰서십 계약서"]
```

Step 3 (L490-501): For EP2+, `prev_blueprint.protagonist_state.equipment` overrides both.

Net result for EP1: equipment = correct EP1 start items. **Not a practical leak.**

## EV-7. Production Pattern Summary

Source: `projects/00_001/logs/episode_production.jsonl`

| EP | Stage 3 Attempts | Stage 4 Round | Final Result |
|----|-----------------|---------------|-------------|
| 1 | 9 | R0 | PASS (attempt_09, final_manuscript__A) |
| 2 | ? | R0 | PASS (attempt_01, final_manuscript__A) |
| 3 | 1 | R2 | PASS (attempt_03, final_manuscript__A) |
| 4 | 2 | R2 | PASS (attempt_03, patched_after_fix__A) |
| 5 | ? | R1 | PASS (attempt_02, patched_after_fix__A) |
| 6 | ? | R2 | PASS (attempt_03, patched_after_fix__A) |
| 7 | ? | R1 | PASS (attempt_02, patched_after_fix__A) |

EP1 required 9 Stage 3 attempts — the most of any episode. This is consistent with the constraint compiler providing weak positive guidance (sparse episode_details) while simultaneously pushing arc-end state via `semantic_carryover`.

## EV-8. Wave 1 Treatment Block Quarantine Verification

Source: `stage3_orchestrator.py:1127-1157`

Allowed fields: `title`, `emotional_beat`, `foreshadow`, `content.context`
Removed fields: `event_villain`, `solution`, `reward`, `power_shift`

Header: "구체적 사건(빌런 등장, 해결책, 보상, 전력 변화)은 제거되었습니다."

**Confirmed: treatment block quarantine is in place.**

## EV-9. Wave 1 Stop Line Expansion Verification

Source: `blueprint_constraint_compiler.py:353-371`

```python
# [W1] 모든 미래 에피소드 정지선 수집 (ep+2 이후)
future_eps: list[dict] = []
if isinstance(_ep_details, list):
    for _item in _ep_details:
        if isinstance(_item, dict):
            _fep = _item.get("ep_num")
            if isinstance(_fep, int) and _fep > next_ep:
                ...
                future_eps.append({"ep": _fep, "content": _brief})
```

Prompt rendering (L168-174):
```python
for _fe in stop_line.get("future_eps", []):
    lines.append(f"[제{_fe['ep']}화]: ...")
lines.append("⚠️ 현재 화 이후의 모든 에피소드 사건·NPC·전개를 이번 화에서 소비하거나 언급하면 즉시 REJECT")
```

**Confirmed: stop line now covers all future episodes.**
