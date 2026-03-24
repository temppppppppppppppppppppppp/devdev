Date: 2026-03-24
Document Type: evidence ledger (T5 lane)
Canonical Path: `docs/2026-03-24/opus-residual/t5-constraint-compiler-residuals-evidence.md`

---

# T5. Constraint Compiler Residuals — Evidence Ledger

## A. IFC Bypass Evidence

### A1. Code path: no `_within_ep()` in IFC

```
bcc:505  @staticmethod
bcc:506  def _extract_immutable_fact_carryover(arc_data: dict, arc_position: int) -> str:
bcc:512      if arc_position <= 1:
bcc:513          return ""
bcc:515      state_changes = arc_data.get("state_changes", {})
bcc:522      deaths = state_changes.get("npc_deaths", [])
bcc:523      for d in (deaths or [])[:5]:    # ← no _within_ep()
bcc:529      for rel in (state_changes.get("relationship_changes") or [])[:5]:    # ← no _within_ep()
bcc:537      for item in (state_changes.get("major_items") or [])[:5]:    # ← no _within_ep()
bcc:545      for skill in (state_changes.get("skill_acquisitions") or [])[:3]:    # ← no _within_ep()
```

Contrast with `_summarize_state_changes()` which applies `_within_ep()`:

```
bcc:564  def _within_ep(entry: object) -> bool:
bcc:565      if ep_num <= 0: return True
bcc:567      if not isinstance(entry, dict): return True
bcc:569      ep_val = entry.get("episode")
bcc:570      if ep_val is None: return True
bcc:573      return int(ep_val) <= ep_num
bcc:580  deaths = [d for d in (state_changes.get("npc_deaths") or []) if _within_ep(d)]    # ← filtered
bcc:599  skills = [s for s in (state_changes.get("skill_acquisitions") or []) if _within_ep(s)]    # ← filtered
```

### A2. 00_001 major_items that would leak through IFC

From `final_arc__balanced.json`:

```json
"major_items": [
    {"action": "획득", "episode": 4, "name": "SW인베스트먼트 법인 인감도장"},
    {"action": "획득", "episode": 4, "name": "20억 예치 법인 계좌 OTP"}
]
```

For ep2 (arc_position=2), IFC would emit:
```
- 아이템 확정: SW인베스트먼트 법인 인감도장 (획득)
- 아이템 확정: 20억 예치 법인 계좌 OTP (획득)
```

These ep4 items appear as "확정" (committed) facts in ep2's blueprint prompt.

### A3. IFC prompt label is misleading

`bcc:218-222`:
```python
lines.append("### [IFC] 불변 사실 계승 (Prior-Arc Carryover)")
lines.append("아래 사실은 이전 Arc에서 확정된 불변 조건입니다.")
```

Label says "Prior-Arc" but code reads from **current** arc's `state_changes`. Docstring says "prior episode state_changes" but implementation reads ALL entries without episode filter.

---

## B. semantic_carryover Evidence

### B1. Arc data continuity_checkpoints

From `final_arc__balanced.json:156-159`:
```json
"continuity_checkpoints": [
    "20억 자본금 확보 완료",
    "가족의 감시망에서 완전히 벗어남",
    "여의도 임시 사무실 계약 및 법인 설립 완료"
]
```

### B2. Rendered in prompt (compile_to_prompt)

`bcc:132-136` places semantic_carryover **before** the constraint block header:
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

============================================================
[V60.80 BLUEPRINT CONSTRAINTS] 제1화
...
```

The semantic_carryover block is the **first structured context** the LLM sees, followed by constraints. The continuity checkpoints describe arc-end state as established facts.

### B3. Correlation with ep1 overconsumption

ep1 blueprint (`attempt_09/final_blueprint__emotion_focused.json`):
- `integrated_scenario` includes: "SW인베스트먼트 법인 인감도장과 20억 예치 법인 계좌 OTP가 쥐어졌다"
- `ending_state.protagonist_status`: "자본금 20억 확보 및 법인 설립을 완료하고 첫 투자를 목전에 둔 상태"

These directly echo the continuity_checkpoints. The LLM treated "20억 자본금 확보 완료" and "법인 설립 완료" as goals to reach within ep1.

---

## C. inherited_state joint_docs Fallback Evidence

### C1. joint_docs arc-end items

From `final_arc__balanced.json:142-146`:
```json
"joint_docs": {
    "physical_inventory": "SW인베스트먼트 법인 인감도장, 20억 원이 예치된 법인 계좌의 보안 매체(OTP), ..."
}
```

### C2. Overwrite chain

```
Step 1 (bcc:452-459): joint_docs.physical_inventory → inherited["equipment"]
  → ["SW인베스트먼트 법인 인감도장", "20억 원이 예치된 법인 계좌의 보안 매체(OTP)", ...]

Step 2 (bcc:478-487): state_constraints.arc_start_state.equipment → inherited["equipment"]
  → ["개인 명의 예금통장", "신탁 펀드 증서", "승마 스폰서십 계약서"]

Step 3 (bcc:489-501): prev_blueprint.protagonist_state.equipment → inherited["equipment"]
  → (skipped for ep1 — no prev_blueprint)

Final: ["개인 명의 예금통장", "신탁 펀드 증서", "승마 스폰서십 계약서"]  ← correct
```

Step 2 masks the joint_docs leakage. If step 2 data were missing, step 1's arc-end items would persist.

---

## D. null-episode Relationship Pass-Through Evidence

### D1. Arc state_changes relationship_changes

From `final_arc__balanced.json:205-236`:
```json
"relationship_changes": [
    {"episode": 2, "npc": "한정호", ...},
    {"episode": null, "npc": "한정호 (아버지)", "to": "의외라는 시선, 약간의 관심..."},
    {"episode": null, "npc": "한태준 (큰형)", "to": "무관심 유지..."},
    {"episode": null, "npc": "한태민 (둘째형)", "to": "무관심 유지..."}
]
```

### D2. `_within_ep()` behavior for null

`bcc:569-571`:
```python
ep_val = entry.get("episode")
if ep_val is None:
    return True    # ← null passes through
```

For ep1 (ep_num=1):
- `episode: 2` → int(2) <= 1 → False → excluded
- `episode: null` → None check → True → **included**

The three null-episode entries describe arc-end relationship states. For 00_001, these are benign ("무관심 유지") but architecturally the filter does not distinguish between "no episode assigned" and "valid for all episodes."

---

## E. Fresh-Run Production Evidence

### E1. ep1-ep4 production outcomes

| EP | S3 Result | S4 R0 | S4 Final | Failure Pattern |
|----|-----------|-------|----------|-----------------|
| 1 | PASS (95, attempt 9) | PASS (96) | PASS (96) | Blueprint overconsumes ep3/4 scope |
| 2 | PASS (88) | PASS (96) | PASS (96) | — |
| 3 | PASS (90) | Director PASS (95) | REJECT (post_select_conflict) | Replays 20억 현금화 |
| 4 | PASS (95) | Director PASS (95) | REJECT (post_select_conflict) | Replays 오피스텔/WTI |

Source: `projects/00_001/logs/episode_production.jsonl` lines 1-4, `docs/2026-03-24/console.txt` lines 424-488

### E2. Stage 3 ep1 took 9 blueprint attempts

Console line 423: `semantic_ctx=2176자` — the semantic context size is consistent with the full arc semantic_carryover being injected.

The 9 attempts suggest the blueprint ensemble struggled to stay within ep1 scope despite constraints. The final attempt (emotion_focused strategy) still overconsumes.
