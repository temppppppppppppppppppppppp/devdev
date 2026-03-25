# T3 — Stage2 Validation Guardrails

Date: 2026-03-24
Lane: `Stage2 Validation Guardrails`
Status: final (3-pass audited)
Terminal: T3
Master Order: `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md`
Evidence Run: `projects/0324_00_`

---

## 1. Executive Summary

Stage 2 validation guardrails are **not a primary cause** of the residual rescue-round failures.

The Arc artifacts themselves are clean and well-specified: Arc 1 correctly encodes triple-source trust provenance, Arc 2 clearly specifies 15B deployment from 20B capital with 5B reserve. The validation pipeline checks 7 structural axes but has **zero numeric/financial state validation** and **zero provenance consistency validation**. However, these blind spots are moot because the live-run failures originate downstream in Stage 3 (blueprint diverging from Arc plan) and Stage 4 (writer manuscript expansion), not from Stage 2 emitting ambiguous payloads.

Stage 2 can be **downgraded to non-primary** for this run.

---

## 2. Included Coverage / Exclusions

**Included**:
- `modules/core/stage2_validation_pipeline.py` (1,380+ lines) — full pipeline chain
- `modules/domain/agents/arc_draft_validator.py` (870+ lines) — Python-only pre-validation
- `modules/domain/agents/four_phase_arc_generator.py` (1,400+ lines) — generation + `_load_execution_state`
- `projects/0324_00_/logs/artifacts/stage2/arc_001/attempt_01/final_arc__conservative.json`
- `projects/0324_00_/logs/artifacts/stage2/arc_002/attempt_01/final_arc__balanced.json`

**Excluded**:
- `unified_arc_validator.py` (LLM-based, Consensus validator internals)
- `continuity_inspector.py` (LLM-based, ContinuityInspector agent internals)
- `arc_corrector.py` (ArcCorrector internals)
- Stage 3/4 code (covered by T4-T9)

---

## 3. Key Evidence

### 3A. ArcDraftValidator — 7 Validation Axes (all Python, $0)

| # | Axis | Location | Mechanism | Blocking? |
|---|------|----------|-----------|-----------|
| 1 | Required fields | `arc_draft_validator.py:197-221` | Checks 6 required + 4 important fields exist | Warning only (penalty) |
| 2 | Duplicate item acquisition | `arc_draft_validator.py:223-284` | Cross-arc regex match on tactical_doc + items_acquired | Advisory (since V60.94) |
| 3 | Location continuity | `arc_draft_validator.py:286-311` | prev arc final_location vs current arc_start_state.location | Warning only |
| 4 | Injury continuity | `arc_draft_validator.py:313-342` | Sudden recovery without recovery scene | Warning only |
| 5 | Grant timeline | `arc_draft_validator.py:344-381` | Duplicate grant detection | Advisory |
| 6 | tactical_doc validation | `arc_draft_validator.py:580-599` | Length, episode layout, density, beat count, state checkpoints | Warning + penalty |
| 7 | Constraint block | `arc_draft_validator.py:822-862` | Forbidden items in items_acquired / tactical_doc | Advisory |

**Critical design decision** (V60.94, `arc_draft_validator.py:184-185`): Only dead-NPC reappearance triggers REJECT. Everything else is advisory → LLM (ConsensusValidator) makes final judgment. This means even if the validator detects a problem, it cannot block the arc.

### 3B. Stage2ValidationPipeline — 4-Block Chain

| Block | Location | Components | Can REJECT? |
|-------|----------|------------|-------------|
| B1 | `stage2_validation_pipeline.py:199-280` | DraftValidator (1st) + SelfReflector + Consensus + ArcMapping + AutoCorrector | Consensus can advisory-REJECT |
| B2 | `stage2_validation_pipeline.py:497-617` | Flow Guard + Duplicate Guard + data validation | Flow Guard can hard REJECT |
| B3 | `stage2_validation_pipeline.py:619-844` | Full DraftValidator + ArcCorrector | Dead NPC only |
| B4 | `stage2_validation_pipeline.py:865-1000` | ContinuityInspector (LLM) + feedback assembly | CI REJECT → advisory |

**Flow Guard** (`stage2_validation_pipeline.py:1231-1375`): Checks beat_sequence structure — beat count, word density, narrative diversity. Uses LLM-based NarrativeStructureAnalyzer for stagnation detection. This is the **only hard REJECT gate** in Stage 2 validation (besides dead NPC).

### 3C. FourPhaseArcGenerator — Numeric State Injection

The generator loads execution state for Arc 2+ via `_load_execution_state()` (`four_phase_arc_generator.py:1011-1093`):

| Source | What it loads | Line |
|--------|--------------|------|
| WorldState | protagonist_assets, location, status, motivations, promises, active_items | `1023-1052` |
| FactLedger | Key numeric facts (value, unit, established_value, established_ep, last_ep) | `1054-1077` |
| episode_bible | Last episode's capital, total_assets, new_items, location | `1079-1090` |

**NS-3-B check** (`four_phase_arc_generator.py:97-188`): Compares arc_end_state numeric fields against block target `capital_after`. This is the **only post-generation numeric validation** at Stage 2. It's advisory-only — produces a warning string, doesn't block.

### 3D. Arc 1 Artifact — Trust Provenance Is Triple-Source

Arc 1 tactical_doc (`final_arc__conservative.json:240`, EP3 section):

> "할아버지가 어릴 적부터 쥐여준 용돈을 모은 계좌, 승마 국가대표 시절 스폰서십으로 받은 누적 수익, 그리고 어머니가 몰래 신탁해 둔 자산의 일부까지 전부 해지한다."

`status_shadow.item_consumption` (`final_arc__conservative.json:233-237`):
- "조부의 현금성 유산"
- "승마 스폰서십 누적 수익"
- "모친 명의 신탁 자산"

`beat_sequence[2]` (`final_arc__conservative.json:94`):
> "제 3화: 조부의 유산, 승마 스폰서십, 모친 명의 신탁 자산 등 흩어진 개인 자산을 긁어모아 20억 원의 시드머니 확보"

**Verdict**: Arc 1 correctly specifies **triple-source provenance** (grandfather + sponsorship + mother). The downstream EP2 blueprint collapse to "조부 only" is a Stage 3 issue, not a Stage 2 issue.

### 3E. Arc 2 Artifact — Capital Tracking Is Clear

`state_constraints.arc_start_state` (`final_arc__balanced.json:240-247`):
- capital: "20억원"
- portfolio_position: "현금 100%"
- total_assets: "20억원"

`state_constraints.arc_end_state` (`final_arc__balanced.json:226-238`):
- capital: "5억원"
- portfolio_position: "WTI 6월물 3배 레버리지 롱 15억 진입 (미실현 수익 +3.75억)"
- total_assets: "23억 7500만원"

`investment_calc` (`final_arc__balanced.json:267-282`):
- asset: "WTI 원유 6월물"
- principal: 1,500,000,000
- leverage: 3
- entry_price: 60
- exit_price: 65
- stated_profit: 375,000,000

**Verdict**: Arc 2 clearly specifies 15B deployed from 20B, with 5B reserve. The downstream EP5 blueprint's "~19.3B full deployment" contradicts this Arc 2 plan. The 15B vs 19.3B gap originates when Stage 3 diverges from Stage 2.

### 3F. Arc 1→2 Capital Handoff — 20B vs 19.3B Fee Gap

Arc 1 ends with: "20억 원이 찍힌 법인 통장" (equipment field)
Arc 2 starts with: capital = "20억원"

The 3.5% trust liquidation fee (reducing 20B to 19.3B) is **not part of Stage 2's plan**. It was introduced by Stage 3's EP3 blueprint. Stage 2 says 20B in, 20B available. Stage 3 added the fee, creating a 0.7B discrepancy that Stage 2 had no mechanism to prevent.

---

## 4. Findings Ranked

### F-1: ZERO numeric/financial state validation (blind spot, not causal)

**Evidence**: All 7 ArcDraftValidator axes check structural properties (field existence, item duplication, location, injury, grant, tactical doc structure, constraint compliance). None checks:
- Account balance consistency across arcs
- Capital deployment math (15B + 5B = 20B?)
- Transaction arithmetic (principal × leverage × price delta = profit?)
- Cross-arc state_constraints.capital alignment

The NS-3-B check in FourPhaseArcGenerator (`four_phase_arc_generator.py:97-188`) is the sole numeric validation — it compares arc_end_state vs block target, not inter-arc consistency.

**Impact on this run**: **None**. Arc 1 and Arc 2 numeric state is internally consistent and correctly specified. The numeric failures appear downstream in Stage 3/4.

**Classification**: `not primary` — blind spot exists but is not causal for this run's failures.

### F-2: ZERO provenance consistency validation (blind spot, not causal)

**Evidence**: No validation axis checks whether provenance claims (who left the trust, who owns what) are consistent between tactical_doc, beat_sequence, status_shadow, and state_constraints within the same arc, or across arcs.

Arc 1's tactical_doc says "할아버지가 쥐여준 용돈 + 승마 스폰서십 + 어머니 신탁" (triple-source). If the LLM had written "아버지가 남겨준 신탁" instead, no validator would catch it.

**Impact on this run**: **None**. Arc 1 provenance is correct. The collapse happens in Stage 3.

**Classification**: `not primary` — blind spot exists but is not causal.

### F-3: `_validate_state_checkpoints` is keyword-only (weak signal)

**Evidence** (`arc_draft_validator.py:623-649`): State checkpoint validation only counts keyword presence ("위치:", "내공:", "부상:", etc.) in tactical_doc episode sections. It does **not** validate that values match between episodes. Having "위치: 여의도" in ep4 and "위치: 강남" in ep5 would pass if both episodes contain the keyword.

**Impact on this run**: **None**. The tactical_doc is well-structured with correct state transitions in both arcs.

**Classification**: `not primary` — weak validation but not causal.

### F-4: ContinuityInspector REJECT → advisory conversion (design trade-off)

**Evidence** (`stage2_validation_pipeline.py:997-999`): When ContinuityInspector returns REJECT, it's converted to a Director advisory rather than blocking the arc. This is by design (V60.56: "Python은 정보 수집만, 최종 판정은 LLM에 위임").

For this run, Arc 1 and Arc 2 both passed ContinuityInspector on attempt_01, so this conversion wasn't exercised.

**Classification**: `not primary` — design trade-off, not exercised in this run.

### F-5: Arc 2 receives FactLedger + WorldState for state alignment (working correctly)

**Evidence** (`four_phase_arc_generator.py:1011-1093`): `_load_execution_state()` loads WorldState, FactLedger, and last episode_bible. Arc 2's arc_start_state.capital = "20억원" correctly matches Arc 1's end state.

**Classification**: `cleared / not primary` — mechanism works correctly.

### F-6: Flow Guard checks narrative structure, not factual content (by design)

**Evidence** (`stage2_validation_pipeline.py:1231-1375`): Flow Guard only checks beat_sequence for structural quality (beat count, word density, narrative diversity, stagnation). It has no factual content checking.

**Classification**: `cleared / not primary` — correct scope for its purpose.

---

## 5. Cleared Non-Culprits

| Suspected Cause | Evidence | Status |
|----------------|----------|--------|
| Stage 2 emitting ambiguous trust provenance | Arc 1 tactical_doc has explicit triple-source (조부 용돈 + 승마 스폰서십 + 모친 신탁). `final_arc__conservative.json:233-237` | **CLEARED** |
| Stage 2 capital tracking ambiguity | Arc 2 has explicit investment_calc with 15B principal, 3x leverage, entry/exit prices. `final_arc__balanced.json:267-282` | **CLEARED** |
| Stage 2 ep-count ownership error | Arc 1: ep1-5, Arc 2: ep6-10. Both attempt_01, both score 95. No retry needed. | **CLEARED** |
| Stage 2 density/allocation error | Both arcs passed Flow Guard, scored 95, 1 attempt each. | **CLEARED** |
| 20B→19.3B fee gap as Stage 2 error | Arc 1 says 20B, Arc 2 starts 20B. The 3.5% fee is a Stage 3 EP3 blueprint invention. | **CLEARED** — downstream issue |
| 15B vs 19.3B deployment gap as Stage 2 error | Arc 2 clearly says 15B deployed. EP5 blueprint's ~19.3B full deployment diverges from Arc 2 plan. | **CLEARED** — Stage 3 divergence |

---

## 6. Residual Culprit Candidate

Stage 2 validation has two structural blind spots (F-1: no numeric validation, F-2: no provenance validation) that are **latent risks for future runs** but **not causal for this run's failures**.

The residual culprit for this lane is: **Stage 2 is not a residual culprit**. The live-run failures originate downstream:
- Trust provenance collapse: Stage 3 blueprint collapsed Arc 1's triple-source to single-source
- 15B vs 19.3B gap: Stage 3 EP5 blueprint diverged from Arc 2's 15B plan
- Timeline/item/temporal errors: Stage 4 writer manuscript expansion

Stage 2 delivered clean, well-specified arc plans. The validation pipeline cannot prevent downstream stages from diverging from these plans — that's not Stage 2's architectural responsibility.

---

## 7. Next-Scope Recommendation

**No execution SSOT needed for Stage 2.**

**Optional hardening** (low priority, future hygiene):
1. Add `investment_calc` arithmetic validation to ArcDraftValidator: verify `final_total_assets = final_cash + sum(position_values)` — ~30 lines of Python, zero LLM cost.
2. Add cross-arc `capital` field continuity check: verify `arc_N.arc_start_state.capital ≈ arc_{N-1}.arc_end_state.capital` — ~20 lines.

These would strengthen defense-in-depth but would not have prevented any failure in the current run.

---

## 8. Confidence And Limits

**Confidence**: 95%

**High confidence**:
- Arc artifact analysis: 98% (direct JSON inspection, no interpretation needed)
- Validation axis catalog: 97% (full code read of all 7 ArcDraftValidator checks + pipeline chain)
- "Not primary" classification: 95% (Arc payloads are clean; failures clearly originate downstream)

**Limits**:
- Did not read ContinuityInspector or UnifiedArcValidator LLM internals (out of scope for Python guardrail analysis)
- Did not verify runtime logs for whether any Stage 2 advisory triggered during this run's Arc 1/2 generation
- Cannot confirm whether FactLedger state was correct at Arc 2 generation time (would need runtime snapshot)

---

## 3-Pass Audit Record

- Pass 1: Confirmed this is a lane survey report, not an execution SSOT. No code changes, no temp queue edits, no closure claims.
- Pass 2: Confirmed findings are grounded in file/line anchors from actual code and artifact JSON. Weak claims marked as "not proven" where applicable.
- Pass 3: Confirmed mandatory final lines present. Confirmed lane scope bounded to Stage 2 validation guardrails only.

---

## Mandatory Final Lines

- Can this lane explain a real residual failure by itself: **no**
- Does this lane explain repeated rescue rounds after the closed waves: **no**
- Would this lane justify a bounded next execution wave: **no**
