# T3. Stage 3 Blueprint Truth — Evidence Ledger

Date: 2026-03-24
Terminal: T3
Companion Report: `t3-stage3-blueprint-truth.md`

## E-1. EP6 Blueprint Institution Error — Direct Quotes

### E-1a. EP6 Blueprint `integrated_scenario` (excerpt)

> 한미증권 영업부의 박성호 PB를 타깃으로 삼는다. 그는 고객의 수익보다 자신의 수수료와 실적을 최우선으로 여기는 탐욕스러운 인물로, 돈만 된다면 컴플라이언스의 경고조차 무시할 사냥개로 적격이었다.

Source: `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`, `integrated_scenario` field

### E-1b. EP6 Blueprint Structured Fields

```json
"end_location": "여의도 한미증권 본사 VVIP 프라이빗 룸",
"start_location": "여의도 이면도로 낡은 빌딩 4층 SW인베스트먼트 사무실"
```

### E-1c. EP7 Blueprint Structured Fields

```json
"start_location": "여의도 한미증권 본사 VVIP 프라이빗 룸",
"end_location": "여의도 한미증권 본사 VVIP 프라이빗 룸"
```

Source: `projects/0324_00_/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json`

### E-1d. EP5 Blueprint — No 박성호 Reference

EP5 blueprint `scene_breakdown` characters:
- scene_1: ["한시우"]
- scene_2: ["한시우"]
- scene_3: ["한태준", "비서실장"]
- scene_4: ["한시우"]
- scene_5: ["한시우"]

No 박성호, no 한미증권 in EP5 blueprint. Confirms the institution error originates in EP6 Stage 3, not EP5 Stage 3.

## E-2. Console Evidence — Director Blames Blueprint

### E-2a. EP6 Round 1 REJECT (console.txt:1509-1517)

```
📊 Director 판정: REJECT (초기: REJECT, 점수: 75, 선택: 후보 C)
사유: 직전 화와의 장소 연속성 단절 (시중은행 -> 한미증권)
지시사항:
  - 배경 장소를 '여의도 한미증권 본점 VIP룸'에서 '시중은행 본점 VIP 라운지'로 수정할 것.
```

### E-2b. EP6 Round 2 PASS (console.txt:1576-1584)

```
📊 Director 판정: PASS (초기: PASS, 점수: 90, 선택: 후보 A)
사유: 직전 화(EP 5)의 엔딩 상황(시중은행 본점 VIP 라운지, 19억 7천만 원 통장 투척)을
완벽하게 이어받았으며, Blueprint에 잘못 기재된 장소(한미증권)를 무시하고 연속성을 지킨 점이
매우 훌륭합니다.
```

Director explicitly says "Blueprint에 잘못 기재된 장소(한미증권)" — the blueprint is acknowledged as wrong.

### E-2c. EP7 Round 1 REJECT (console.txt:1661-1668)

```
📊 Director 판정: REJECT (초기: REJECT, 점수: 86, 선택: 후보 C)
선택 사유: 세 후보 모두 Blueprint의 오류를 그대로 수용하여 직전 화의 장소(시중은행 본점)를
'여의도 한미증권'으로 잘못 기재하는 모순을 범했으나
```

"Blueprint의 오류를 그대로 수용" — all three manuscript candidates faithfully followed the wrong blueprint.

### E-2d. EP7 자유 리뷰 (console.txt:1679-1680)

```
Blueprint에 잘못 기재된 장소(한미증권)를 AI가 그대로 받아들여 발생한 오류입니다.
직전 화의 장소는 시중은행 본점이었습니다.
```

## E-3. Stage 3 Validation Scores — Error Not Caught

### E-3a. Blueprint generation results (console.txt:883-926)

```
📊 제5화 Blueprint 결과: PASS (score=95)
[Stage3] blueprint success (verdict=PASS, strategy=action_focused, score=95)

📊 제6화 Blueprint 결과: PASS (score=100)
[Stage3] blueprint success (verdict=PASS, strategy=dialogue_focused, score=100)

📊 제7화 Blueprint 결과: PASS (score=95)
[Stage3] blueprint success (verdict=PASS, strategy=action_focused, score=95)
```

EP6 received a **perfect 100** despite containing the hard 한미증권 error.

### E-3b. Stage 3 batch completion (console.txt:947-952)

```
📊 [V60.80] Stage 3 완료 통계
✅ [Stage 3] Blueprint 완료 (성공: 5, 실패: 0)
```

Zero failures — all errors were invisible to Stage 3 validation.

## E-4. Capital-Lock Bypass — Code Trace

### E-4a. EP5 Blueprint ending_state (no structured capital keys)

```json
"ending_state": {
    "location": "여의도 SW인베스트먼트 사무실 데스크 앞",
    "protagonist_status": "WTI 롱 포지션 진입을 완료하고 호가창을 응시하는 상태",
    "timeline": {
        "expression": "2006년 1월 늦은 밤",
        "표현": "2006년 1월 늦은 밤"
    }
}
```

Keys present: `location`, `protagonist_status`, `timeline`
Keys required by capital-lock: `balance`, `capital`, `deployed`, `position`, `investment_status`
Overlap: **zero**

### E-4b. EP5 Blueprint protagonist_state (no structured capital keys)

```json
"protagonist_state": {
    "equipment": [
        "SW인베스트먼트 사무실 열쇠",
        "약 198만 달러가 예치된 파생상품 계좌",
        "다중 모니터가 세팅된 PC"
    ],
    "injuries": "없음",
    "mood": "트라우마를 억누른 서늘한 결의와 통제감"
}
```

Keys present: `equipment`, `injuries`, `mood`
Keys required by capital-lock: `balance`, `capital`, `portfolio`
Overlap: **zero**

Capital information is embedded in `equipment[1]` as free text: "약 198만 달러가 예치된 파생상품 계좌"

### E-4c. Capital-lock code path (blueprint_constraint_compiler.py:654-656)

```python
def _build_capital_continuity_packet(...):
    if genre != "investment":
        return {}
    # ... scans for balance/capital/deployed/position keys
```

When none of the required keys exist → `fields` list stays empty → returns `{}` → validator skips all checks.

### E-4d. Validator bypass (unified_blueprint_validator.py:1025-1027)

```python
def _collect_capital_state_drift_issues(...):
    capital_pkt = constraint_block.get("capital_continuity_packet", {})
    if not isinstance(capital_pkt, dict) or not capital_pkt.get("fields"):
        return []  # ← exits here, no checks performed
```

## E-5. Location Check Granularity — Code Trace

### E-5a. Area extraction (unified_blueprint_validator.py:1130-1133)

```python
def _extract_area(self, location: str) -> str:
    match = re.search(r"^([가-힣]{2,5})", location)
    return match.group(1) if match else ""
```

### E-5b. EP5→EP6 transition evaluation

- EP5 end_location: "여의도 이면도로..." → area = "여의도"
- EP6 start_location: "여의도 이면도로..." → area = "여의도"
- `prev_area == curr_area` → `True` → no issue flagged
- EP6's "한미증권" vs EP3's "시중은행" difference is invisible at this granularity

## E-6. Batch Generation Sequence — Console Trace

```
console.txt:850  📐 [Stage 3] Blueprint frontier 동기화 (target <= ep 8)...
console.txt:864  제4화 Blueprint 생성 → PASS (score=100)
console.txt:883  제5화 Blueprint 생성 → PASS (score=95)
console.txt:897  제6화 Blueprint 생성 → PASS (score=100)
console.txt:914  제7화 Blueprint 생성 → PASS (score=95)
console.txt:932  제8화 Blueprint 생성 → PASS (score=95)
console.txt:952  ✅ [Stage 3] Blueprint 완료 (성공: 5, 실패: 0)
 ⟶ Stage 4 starts after this point
```

All 5 blueprints generated sequentially within Stage 3 batch. EP6 uses EP5's blueprint (not manuscript) as prior authority. EP5's manuscript corrections (시중은행, 19.7억) cannot flow back.

## E-7. Capital Amount Drift Chain

| Stage | Amount | Source |
|---|---|---|
| EP5 blueprint | 1,930,000,000원 (19억 3천만) | `scene_2.key_events` |
| EP5 blueprint | ~198만 달러 | `protagonist_state.equipment` |
| EP5 accepted manuscript | 19억 7천만 원 | `console.txt:1287` (Round 1 rejected ms shows this figure), `console.txt:1577` (EP6 PASS references it) |
| EP6 blueprint | 19억 3천만 원 | `protagonist_state.equipment` — matches EP5 blueprint, not EP5 manuscript |
| EP6 blueprint | 15억 원 (for 3x leverage) | `integrated_scenario` — partial deployment |
| EP6 accepted manuscript | 잔고 4억 7천만 원 | `console.txt:1598` — Bible entry |
| EP7 blueprint | 15억 원 3배 레버리지 | `integrated_scenario` |

The 19.3→19.7 divergence shows that Stage 4 changed the capital amount, but this correction could not propagate back to EP6/EP7 blueprints.

## E-8. EP5 Strategy Label Mismatch

Console vs artifact:
- `console.txt:890`: `strategy=action_focused, score=95`
- Artifact `_ensemble_meta`: `{"strategy": "emotion_focused", "candidate_index": 1, "total_candidates": 3}`

The artifact says candidate 1 (0-indexed) was selected with emotion_focused strategy, but console logged action_focused. This is a sink recording discrepancy — the content itself is unambiguous.
