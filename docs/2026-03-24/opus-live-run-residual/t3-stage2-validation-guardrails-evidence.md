# T3 — Stage2 Validation Guardrails — Evidence Ledger

Date: 2026-03-24
Terminal: T3
Companion: `docs/2026-03-24/opus-live-run-residual/t3-stage2-validation-guardrails.md`

---

## E-1. ArcDraftValidator Complete Axis Catalog

### Axis 1: Required Fields (`arc_draft_validator.py:197-221`)

```
required_fields = ["arc_no", "tactical_doc", "joint_docs", "state_constraints", "ep_start", "ep_end"]
required_important = ["ep_count", "items_acquired", "protagonist_items", "grants_received"]
```

Missing required → penalty 10/field. Missing important → penalty 5/field. **Never blocks.**

### Axis 2: Duplicate Item Acquisition (`arc_draft_validator.py:223-284`)

Collects all items from prev_arcs via:
- `state_constraints.protagonist_items` (or fallback `items_acquired`)
- `joint_docs.physical_inventory`
- Regex patterns on `tactical_doc` text

Cross-checks current arc's items against this set. Penalty 30/duplicate. **Advisory only (V60.94).**

### Axis 3: Location Continuity (`arc_draft_validator.py:286-311`)

Compares `prev_arc.joint_docs.final_location` vs `current_arc.state_constraints.arc_start_state.location`. If incompatible and no travel keywords in first 500 chars of tactical_doc → warning + penalty 10.

### Axis 4: Injury Continuity (`arc_draft_validator.py:313-342`)

If prev arc has injuries not in ["없음", "경미", "완치"] and current arc starts with no injuries and no recovery keywords in first 1000 chars → warning + penalty 5.

### Axis 5: Grant Timeline (`arc_draft_validator.py:344-381`)

Detects duplicate grants via `state_constraints.grants_received` and regex on `tactical_doc`. Penalty 25/duplicate.

### Axis 6: Tactical Doc (`arc_draft_validator.py:580-649`)

Sub-checks:
- Length: min `ep_count × 500` chars (penalty 25 if under `ep_count × 400`, penalty 10 if under min)
- Episode layout: missing episodes (penalty 15), short episodes <300 chars (penalty 3/ep), imbalanced (5x ratio, penalty 5)
- Density: sparse episodes (no dialogue/action), low beats (<3/ep), incomplete structure
- State checkpoints (`_validate_state_checkpoints`, L623-649): keyword presence only — counts occurrences of ["위치:", "내공:", "부상:", "소지품:", "획득:", "소모:", "종료 상태", "시작 상태"]. If <2 keywords in any episode section >300 chars → "missing checkpoint". **Does NOT validate actual values.**

### Axis 7: Constraint Block (`arc_draft_validator.py:822-862`)

Extracts forbidden items from:
- Structural `_forbidden_items` field
- Regex on constraint_block text (`❌`, `획득 금지/불가`)

Checks against `items_acquired` and tactical_doc. Penalty 30/violation.

### V60.94 Decision Gate (`arc_draft_validator.py:172-195`)

```python
# [V60.94] 죽은 NPC 등장만 REJECT, 나머지는 advisory
advisory_issues = [c for c in critical_issues if "사망한" not in c and "죽은" not in c]
is_valid = reject_reason is None  # Only dead NPC triggers reject_reason
```

**Only dead-NPC reappearance can set `valid=False`.** All other checks produce advisory_issues for LLM consumption.

---

## E-2. Stage2ValidationPipeline Chain Detail

### B1: Pre-Validation (`stage2_validation_pipeline.py:199-280`)

1. `_collect_initial_draft_advisories` (L282-310): Runs DraftValidator 1st pass, collects advisory_issues
2. `_run_self_reflection_phase` (L312-356): SelfReflector improves arc JSON (Analyst path only)
3. `_run_consensus_phase` (L358-404): 3-LLM vote. REJECT → Director advisory (V60.56)
4. `_build_invalid_refined_arc_retry` (L406-430): Structural validation (is arc a dict?)
5. `_run_arc_mapping_and_auto_correction` (L432-468): ArcMapping + Stage2Optimizer post-processing

### B2: Flow & Duplicate Guards (`stage2_validation_pipeline.py:497-617`)

1. `_stage2_flow_guard` (L1231-1375): Beat sequence structural analysis
   - Beat count ≥ ep_count
   - Non-empty beats
   - Avg words ≥ 6, min word per beat ≥ 4
   - NarrativeStructureAnalyzer stagnation detection (LLM)
   - **This is the only hard REJECT gate** (besides dead NPC)
2. Duplicate Guard (L583-600): Jaccard similarity on tactical_doc vs prev arc
3. Data validation (L602-617): Arc dict type check

### B3: Full DraftValidator + ArcCorrector (`stage2_validation_pipeline.py:619-844`)

1. Full DraftValidator run (L636-641)
2. If valid → mark passed
3. If invalid → check if CRITICAL or only MAJOR:
   - CRITICAL → advisory to Director
   - MAJOR only → ArcCorrector attempts auto-fix (L741-843)
   - Post-fix revalidation

### B4: ContinuityInspector (`stage2_validation_pipeline.py:865-1000`)

1. LLM-based arc continuity inspection
2. REJECT → advisory conversion + failure recording + feedback assembly
3. PASS → apply continuity updates to arc

---

## E-3. Arc 1 Provenance Evidence

### Triple-Source in tactical_doc (EP3 section)

```
"할아버지가 어릴 적부터 쥐여준 용돈을 모은 계좌, 승마 국가대표 시절 스폰서십으로 받은 누적 수익,
그리고 어머니가 몰래 신탁해 둔 자산의 일부까지 전부 해지한다."
```

### Triple-Source in status_shadow.item_consumption

```json
"item_consumption": [
    "조부의 현금성 유산",
    "승마 스폰서십 누적 수익",
    "모친 명의 신탁 자산"
]
```

### Simplified in beat_sequence

```json
"제 3화: 조부의 유산, 승마 스폰서십, 모친 명의 신탁 자산 등 흩어진 개인 자산을 긁어모아 20억 원의 시드머니 확보"
```

**All three surfaces agree**: triple-source provenance is correctly encoded in Arc 1. Stage 3 EP2 blueprint's collapse to "조부 only" is a downstream divergence.

---

## E-4. Arc 2 Capital Tracking Evidence

### Arc Start State

```json
"arc_start_state": {
    "capital": "20억원",
    "portfolio_position": "현금 100%",
    "total_assets": "20억원"
}
```

### Investment Calculation

```json
"investment_calc": {
    "final_cash": 500000000,
    "final_total_assets": 2375000000,
    "transactions": [{
        "action": "매수",
        "asset": "WTI 원유 6월물",
        "entry_price": 60,
        "exit_price": 65,
        "leverage": 3,
        "principal": 1500000000,
        "stated_profit": 375000000
    }]
}
```

Math verification:
- 20B total - 15B deployed = 5B cash ✓
- 15B × 3x leverage = 45B exposure
- (65-60)/60 × 45B = 3.75B profit ✓
- 5B cash + 15B principal + 3.75B profit = 23.75B total ✓

### Arc End State

```json
"arc_end_state": {
    "capital": "5억원",
    "total_assets": "23억 7500만원",
    "portfolio_position": "WTI 6월물 3배 레버리지 롱 15억 진입 (미실현 수익 +3.75억)"
}
```

**All fields are internally consistent.** The 15B deployment is clearly specified. Stage 3 EP5 blueprint's "~19.3B full deployment" diverges from this plan.

---

## E-5. 20B vs 19.3B Fee Gap Chain

| Stage | Capital | Source |
|-------|---------|--------|
| Arc 1 EP3 plan | 20B ("정확히 20억 원") | `final_arc__conservative.json:240` tactical_doc |
| Arc 1 end state | 20B (equipment: "20억 원이 찍힌 법인 통장") | `final_arc__conservative.json:142` |
| Arc 2 start state | 20B ("20억원") | `final_arc__balanced.json:241` |
| Stage 3 EP3 blueprint | 19.3B (after 3.5% fee) | `ep_0003 blueprint: "19억 3천만 원"` |
| Stage 3 EP5 blueprint | 19.3B full deployment | `ep_0005 blueprint: "1,930,000,000원"` |
| Arc 2 plan | 15B deployed | `final_arc__balanced.json:278` |

The 3.5% fee is introduced by Stage 3, not Stage 2. The 15B→19.3B divergence is also a Stage 3 issue: EP5 blueprint deploys the full 19.3B instead of following Arc 2's 15B plan.

---

## E-6. NS-3-B Numeric Check (Only Post-Generation Numeric Validation)

`four_phase_arc_generator.py:97-188`: Compares `arc_end_state.capital/total_assets/assets` against `curr_block.genre_ext.capital_after`. If divergence > 30% threshold → warning string.

This check is:
- **Post-generation** (runs after ensemble selection, not during validation pipeline)
- **Advisory only** (produces a note, doesn't block)
- **Block-target scoped** (compares against treatment block target, not against prev arc)
- **Does NOT check inter-arc capital continuity**

---

## E-7. `_load_execution_state` — State Available to Arc 2 Generator

`four_phase_arc_generator.py:1011-1093`:

```python
# 1) WorldState — protagonist assets, location, status
_ws = _db.load_anchor("world_state")
result["protagonist_assets"] = _protag.get("assets", {})
result["protagonist_location"] = _protag.get("location", "")

# 2) FactLedger — key numeric facts
_fl = _db.load_anchor("fact_ledger")
result["fact_ledger"] = _key_facts  # value, unit, established_value, established_ep, last_ep
result["fact_ledger_summary"] = _fl_summary

# 3) Latest episode_bible
result["last_episode_state"] = {
    "capital": _eb.get("capital"),
    "total_assets": _eb.get("total_assets"),
    "new_items": _eb.get("new_items", []),
    "location": _eb.get("location", ""),
}
```

This state is injected into the Arc 2 generation prompt. The fact that Arc 2 correctly starts with 20B confirms the state injection worked. But the state is only used by the LLM generator — there is no Python-level validation that the generated arc honors these values.
