# T4: Stage3 Blueprint Authority — Evidence Ledger

Date: 2026-03-24
Lane: T4 — Stage3 Blueprint Authority
Terminal: 4
Parent Report: `docs/2026-03-24/opus-live-run-residual/t4-stage3-blueprint-authority.md`

---

## E1. EP2 Blueprint Provenance Contradiction Evidence

### Source: `projects/0324_00_/logs/artifacts/stage3/ep_0002/attempt_02/final_blueprint__dialogue_focused.json`

**Location 1 — `scene_breakdown.scene_1.key_events[2]`**:
```
"초기 자본금 20억 원 마련을 위해 조부 명의의 HMC투자증권 신탁 계좌 해지 목표 설정"
```

**Location 2 — `integrated_scenario` (paragraph 4)**:
```
"조부님께서 제 앞으로 남겨주신 20억 원 규모의 HMC투자증권 신탁 계좌를 오늘 자로 해지해 주십시오."
```

**Location 3 — `scene_breakdown.scene_4.key_events`**:
```
"조부 명의의 신탁 계좌 해지를 요청"
```

### Counter-evidence: EP1 Final Manuscript Canon

EP1 final manuscript established: "어머니께서 제 앞으로 남겨주신" (mother's bequest)

EP2 final manuscript (attempt_04, after 3 rejections) correctly uses: "어머니께서 몰래 남겨주신" (mother secretly bequeathed)

### Conflict Summary

| Source | Trust Fund Provenance |
|--------|----------------------|
| EP2 Blueprint (attempt_02) | 조부 (grandfather) |
| EP1 Final Manuscript | 어머니 (mother) |
| EP2 Final Manuscript (attempt_04) | 어머니 (mother) — corrected after 3 rejects |

---

## E2. EP5 Blueprint Stale Capital Figure Evidence

### Source: `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`

**`scene_breakdown.scene_2.description`**:
```
"공인인증서 로그인을 마치고 계좌 잔고를 확인한다. 1,930,000,000원."
```

**`scene_breakdown.scene_2.key_events[1]`**:
```
"19억 3천만 원을 해외 선물용 달러(약 198만 달러)로 환전"
```

### Cross-reference: EP3 and EP4 Capital State

| Episode | Event | Amount |
|---------|-------|--------|
| EP3 | Trust dissolution (20B - 3.5% fee) | 19,300,000,000 won received |
| EP4 | SW Investment corporate capital deduction | -50,000,000 won |
| EP5 expected balance | After EP4 deduction | ~19,250,000,000 won |
| EP5 blueprint states | Account balance | 1,930,000,000 won (= EP3 figure, ignoring EP4) |

**Note**: The blueprint uses 1,930,000,000 (1.93B), not 19,300,000,000 (19.3B). This is internally consistent within the blueprint (19.3B = 19억 3천만 원 = 1,930,000,000원 in Korean won notation). The issue is that it doesn't subtract EP4's 50M corporate capital.

---

## E3. EP6 Blueprint Capital Deployment Gap Evidence

### Source: `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`

**`scene_breakdown.scene_1.content`**:
```
"19억 3천만 원의 시드머니를 온전히 쏟아부을 3배 레버리지"
```

**`scene_breakdown.scene_2.content`**:
```
"15억 원어치의 자금을 WTI 6월물 3배 레버리지 롱 포지션에 밀어 넣는 미친 짓이다."
```

### Cross-reference: EP5 Ending State

EP5 blueprint `ending_state`:
```json
{
  "location": "여의도 SW인베스트먼트 사무실 데스크 앞",
  "protagonist_status": "WTI 롱 포지션 진입을 완료하고 호가창을 응시하는 상태",
  "timeline": { "expression": "2006년 1월 늦은 밤" }
}
```

EP5 `integrated_scenario` (final line):
```
"마우스 좌클릭. 건조한 클릭음과 함께 약 198만 달러의 자본이 WTI 롱 포지션에 쏟아져 들어간다."
```

**Gap**: EP5 ends with ~198만 달러 (entire capital) deployed into WTI. EP6 blueprint opens with "19.3B seed money to be fully deployed in 3x leverage" as if the deployment hasn't happened. No reconciliation between the two states.

### EP6 Rejection Cascade

| Round | Gate | Score | Primary Cause |
|-------|------|-------|---------------|
| R1 | director_primary_reject | 78 | Timeline (2월→4월), location/item drift |
| R2 | continuity_firewall | 44 | Capital state: 19B already in WTI, 20B available impossible |
| R3 | director_primary_pass | 98 | Full rewrite with correct state |

The continuity_firewall rejection at R2 is directly traceable to the blueprint's failure to specify capital deployment state.

---

## E4. EP3 Blueprint Warning vs Actual Rejection Axis

### Source: `projects/0324_00_/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json`

**Blueprint self-assessment**:
```json
{
  "quality_risk": true,
  "python_warnings": ["위치 불연속: 한정호 회장의 서재 앞 -> 본가 2층 복도 (서재 앞)"]
}
```

**Actual EP3 R1 rejection causes** (from console post-select):
1. "가죽 노트의 보관 위치 (금고 vs 서랍) 불일치" — **NOT in blueprint**
2. "서재 독대 시간 모순" (4:35 PM → 3:35 PM timeline) — **NOT in blueprint**

**Assessment**: Blueprint's warning axis (location discontinuity) ≠ actual rejection axis (item storage + timeline). The blueprint's `quality_risk` flag correctly detected *a* problem but not *the* problems that mattered.

---

## E5. Stage 3 Context Injection Evidence

### Source: `modules/core/stage3_orchestrator.py`

**EP2 blueprint generation console output**:
```
제2화 Blueprint 대기: ThreePhase runtime 호출 중 (anchors=0, window=1, semantic_ctx=2176자)
```

**Interpretation**:
- `anchors=0`: No anchor manuscripts (EP2 is only the 2nd episode)
- `window=1`: 1 previous episode manuscript available (EP1)
- `semantic_ctx=2176자`: Smart retrieval context is 2,176 characters

**Code path** (line 1406-1499):
```python
_recent_manuscripts = ctx.current_project.db.get_recent_manuscripts(
    ep_num=working_ep, count=36
)
_selected_manuscripts = _select_stage3_anchor_recent_window(_recent_manuscripts)
```

The blueprint LLM receives the full EP1 manuscript via `prev_manuscripts_text`, plus the `semantic_ctx` (2,176 chars from smart retrieval), plus the `arc_data` (Arc 1 tactical design).

**Key gap**: There is no explicit priority rule in the prompt that says "for already-published facts, the previous manuscript is the higher authority than the Arc tactical design." The LLM resolves conflicts between these two sources at its own discretion.

---

## E6. Blueprint Financial State Schema Gap

### Current blueprint `protagonist_state` schema:

```json
{
  "equipment": ["list of physical items"],
  "injuries": "string",
  "mood": "string"
}
```

### Current blueprint `ending_state` schema:

```json
{
  "location": "string",
  "protagonist_status": "string",
  "timeline": { "expression": "string" }
}
```

**Missing fields** (not present in any of the 6 examined blueprints):
- `entering_capital_balance`
- `deployed_capital`
- `available_cash`
- `active_positions`
- `cumulative_expenditures`

Financial amounts appear only in free-text fields (scene content, integrated_scenario, key_events) without structured schema enforcement. This makes cross-episode capital consistency a free-text matching problem rather than a structured validation problem.

---

## E7. Cross-Episode Blueprint Comparison Matrix

| Field | EP2 | EP3 | EP5 | EP6 | EP7 | EP8 |
|-------|-----|-----|-----|-----|-----|-----|
| quality_risk | false | **true** | false | false | false | false |
| prevalidation_issues | 0 | **1** | 0 | 0 | 0 | 0 |
| python_warnings | 0 | **1** | 0 | 0 | 0 | 0 |
| Hard provenance error | **YES** | no | no | no | no | no |
| Stale capital figure | no | no | **YES** | no | no | no |
| Capital deployment gap | no | no | no | **YES** | no | no |
| Blueprint caused rejection | **YES** (primary) | no | amplified | amplified | no | no |
| Blueprint self-detected issue | no | yes (wrong axis) | no | no | no | no |

---

## E8. Console Evidence: EP2 Rejection Chain

From `docs/2026-03-24/console.txt`:

**Round 1**: Director PASS (96) → Post-select: "신탁 계좌 출처가 1화에서는 '어머니', 2화에서는 '조부(할아버지)'로 다르게 서술" → REJECT

**Round 2**: Director PASS (90) → Post-select: "1화에서 설정된 신탁 자산의 특성(어머니가 몰래 남김)과 주인공의 행동 계획(가족 관련) 충돌" → REJECT

**Round 3**: Director PASS (96) → Post-select: "제1화 결말부와 제2화 도입부 시간적 단절 관련 설정 충돌" + IFC 불변사실 위반 → REJECT. TF-29: "제약 위반 유형 REJECT 3연속 — 블루프린트 단계 문제 가능성 경고"

**Round 4**: Director PASS (96) → Post-select: PASS → FINAL

**Note**: The TF-29 warning at Round 3 explicitly suggests "블루프린트 단계 문제 가능성" — the system itself detected that the repeated rejection pattern may originate at the blueprint level.
