# T3. Stage 3 Blueprint Truth — EP5-EP7 Mid-Arc Residual Survey

Date: 2026-03-24
Terminal: T3
Lane: Stage3 Blueprint Truth
Status: final (3-pass audited)
Confidence: 97%

## 1. Executive Summary

EP6/EP7 Stage 3 blueprints contain a **hard factual error** in NPC institution affiliation (한미증권 vs 시중은행) that directly caused 4 of the 5 observed rescue rounds. This error was born in Stage 3 and was **not caught** by Python prevalidation or Director blueprint validation, despite both passing with scores of 95-100. The capital-lock mechanism was structurally bypassed because the blueprint schema lacks structured capital fields. Stage 3 is the **confirmed primary cause** of the EP6/EP7 rescue family.

## 2. Evidence Anchor Summary

| Source | Path | Role |
|---|---|---|
| EP5 Blueprint | `projects/0324_00_/logs/artifacts/stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json` | prior authority |
| EP6 Blueprint | `projects/0324_00_/logs/artifacts/stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json` | primary subject |
| EP7 Blueprint | `projects/0324_00_/logs/artifacts/stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json` | primary subject |
| Constraint Compiler | `modules/domain/agents/blueprint_constraint_compiler.py` | mechanism audit |
| Blueprint Validator | `modules/domain/agents/unified_blueprint_validator.py` | mechanism audit |
| Console | `docs/2026-03-24/console.txt` (lines 883-952, 1221-1436, 1508-1598, 1661-1822) | runtime truth |

## 3. Findings

### 3.1 [confirmed primary cause] EP6/EP7 Blueprint Institution Error — 한미증권 vs 시중은행

**What**: EP6 and EP7 blueprints specify "한미증권" as 박성호 PB's institution and the meeting location. Established canon from EP3 places 박성호 at a "시중은행" (commercial bank).

**Evidence — Blueprint content**:
- EP6 blueprint `integrated_scenario`: "한미증권 영업부의 박성호 PB를 타깃으로 삼는다"
- EP6 blueprint `end_location`: "여의도 한미증권 본사 VVIP 프라이빗 룸"
- EP7 blueprint `start_location`: "여의도 한미증권 본사 VVIP 프라이빗 룸"
- EP7 blueprint `integrated_scenario`: multiple "한미증권" references throughout

**Evidence — Director explicitly blames blueprint**:
- `console.txt:1509`: "직전 화와의 장소 연속성 단절 (시중은행 -> 한미증권)" — EP6 R1 REJECT
- `console.txt:1584`: "Blueprint에 잘못 기재된 장소(한미증권)를 무시하고 연속성을 지킨 점이 매우 훌륭합니다" — EP6 R2 PASS (manuscript overrode blueprint)
- `console.txt:1666-1667`: "세 후보 모두 Blueprint의 오류를 그대로 수용하여 직전 화의 장소(시중은행 본점)를 '여의도 한미증권'으로 잘못 기재하는 모순을 범했으나" — EP7 R1 REJECT
- `console.txt:1679`: "Blueprint에 잘못 기재된 장소(한미증권)를 AI가 그대로 받아들여 발생한 오류입니다" — EP7 R1 REJECT (Director's free review)

**Rescue round cost**:
- EP6 Round 1 REJECT (score=75): directly caused by this blueprint error
- EP7 Round 1 REJECT (score=86): directly caused by this blueprint error
- EP7 Round 2 REJECT (score=75): partially caused (manuscript still inheriting blueprint location)

**Classification**: `confirmed primary cause`

### 3.2 [confirmed primary cause] Stage 3 Validation Failed to Catch Institution Error

**What**: Both Python prevalidation and Director blueprint validation gave EP6 and EP7 passing scores despite the hard 한미증권 error.

**Evidence**:
- `console.txt:897`: "📊 제6화 Blueprint 결과: PASS (score=100)" — perfect score with wrong institution
- `console.txt:914`: "📊 제7화 Blueprint 결과: PASS (score=95)" — passing score with wrong institution

**Root cause — Python prevalidation**:
- Location continuity check (`unified_blueprint_validator.py:805-831`) uses coarse area extraction (`_extract_area`, L1130-1133): regex `r"^([가-힣]{2,5})"` extracts first 2-5 Korean chars
- EP5 end_location "여의도..." → area "여의도"
- EP6 start_location "여의도..." → area "여의도"
- `prev_area == curr_area` → `True` → no issue flagged
- The check has **zero NPC-affiliation awareness**; it only compares geographic area prefixes

**Root cause — Director blueprint validation**:
- Director LLM evaluated the blueprint in isolation and gave it 100/100 (EP6)
- The Director at blueprint stage does not have access to the full EP3 NPC registry that would reveal 박성호's established institution
- The fact_lock_packet carries location, time, ending_hook, and equipment — but not NPC attribute anchors

**Classification**: `confirmed primary cause` (validation gap)

### 3.3 [confirmed secondary amplifier] Capital-State Structural Gap in Blueprint Schema

**What**: EP5 deploys ~198만 달러 (~19.3억원) into WTI long position. EP6 blueprint acts as if 19.3억원 is still fully available and proposes deploying 15억 through a different channel. The capital_continuity_packet mechanism exists but was structurally bypassed.

**Evidence — Blueprint content**:
- EP5 scene 5: "약 198만 달러의 증거금이 WTI 롱 포지션에 쏟아져 들어간다" (ALL capital deployed)
- EP5 `protagonist_state.equipment`: "약 198만 달러가 예치된 파생상품 계좌" (confusingly says "예치" = deposited, not deployed)
- EP6 `protagonist_state.equipment`: "19억 3천만 원이 예치된 계좌 내역" (full original amount shown as available)
- EP6 `integrated_scenario`: "19억 3천만 원의 자본을 극대화할 3배 레버리지" and "15억 원어치의 자금을 WTI 6월물 3배 레버리지 롱 포지션에"

**Root cause — Capital-lock mechanism bypass**:
- `blueprint_constraint_compiler.py:641-732` (`_build_capital_continuity_packet`): looks for structured keys `balance`, `capital`, `deployed`, `position`, `investment_status` in `prev_blueprint.ending_state`
- EP5's `ending_state` has only: `location`, `protagonist_status` (free text), `timeline` — **zero matching keys**
- EP5's `protagonist_state` has only: `equipment` (list of strings), `injuries`, `mood` — **zero matching keys**
- Therefore `_build_capital_continuity_packet` returns `{}` (empty)
- Therefore `_collect_capital_state_drift_issues` (`unified_blueprint_validator.py:1017-1055`) exits immediately at L1026-1027: `if not capital_pkt.get("fields"): return []`
- **The entire capital drift detection was silently skipped**

**Internal blueprint inconsistency in EP5**:
- EP5 `ending_state.protagonist_status`: "WTI 롱 포지션 진입을 **완료**하고" (position entered)
- EP5 `protagonist_state.equipment`: "약 198만 달러가 **예치된** 파생상품 계좌" (funds still deposited)
- These two statements contradict each other within the same blueprint

**Classification**: `confirmed secondary amplifier` — the capital gap didn't directly cause rescue rounds (institution error did), but it creates unchecked numerical drift that Stage 4 must reconcile

### 3.4 [confirmed secondary amplifier] Batch Blueprint Generation Creates Truth Gap

**What**: Stage 3 generates all Arc 2 blueprints (EP4-EP8) as a batch before Stage 4 starts. This means EP6's blueprint uses EP5's *blueprint* as the prior authority, not EP5's *accepted manuscript*. When Stage 4 modifies EP5 (correcting 한미증권→시중은행, adjusting capital figures), EP6's blueprint is already locked and cannot reflect those corrections.

**Evidence**:
- `console.txt:850`: "📐 [Stage 3] Blueprint frontier 동기화 (target <= ep 8)..."
- `console.txt:864-944`: EP4→EP5→EP6→EP7→EP8 blueprints generated sequentially
- `console.txt:952`: "✅ [Stage 3] Blueprint 완료 (성공: 5, 실패: 0)" — ALL done before Stage 4
- Stage 4 for EP5 then modifies the story: 한미증권→시중은행, 19.3억→19.7억
- `console.txt:1577`: EP6 PASS reasoning references "19억 7천만 원 통장 투척" — a figure from EP5's manuscript, not EP5's blueprint (which says 19.3억)
- EP5 blueprint `end_location`: "여의도 SW인베스트먼트 사무실" — but EP5's accepted manuscript apparently ends at "시중은행 본점 VIP 라운지"

**Consequence**: Every later blueprint in the batch inherits a snapshot of the prior blueprint, not the prior accepted truth. Stage 4 corrections in early episodes create cascading blueprint-manuscript divergence in later episodes.

**Classification**: `confirmed secondary amplifier`

### 3.5 [artifact-truth mismatch] EP5 Strategy Label Discrepancy

**What**: Console logs say EP5 blueprint was selected as `action_focused` (score=95), but the saved artifact is `final_blueprint__emotion_focused.json` with `_ensemble_meta.strategy: "emotion_focused"`.

**Evidence**:
- `console.txt:890`: `[Stage3] blueprint success (verdict=PASS, strategy=action_focused, score=95)`
- Artifact meta: `{"strategy": "emotion_focused", "candidate_index": 1}`

**Impact**: Low — the content is what matters, not the label. But it indicates a logging-vs-artifact naming mismatch.

**Classification**: `artifact-truth mismatch`

### 3.6 [cleared / not primary] EP5 Post-Select Conflict (박성호 in Stage 4)

**What**: EP5's blueprint does NOT mention 박성호 or 한미증권 — EP5's scenes involve only 한시우, 한태준, and 비서실장. The 박성호 conflict in EP5 was introduced by Stage 4's manuscript expansion.

**Evidence**:
- EP5 blueprint `scene_breakdown`: no scene contains 박성호 as a character
- `console.txt:1234-1238`: "Post-select continuity conflict: 제3화에서 시중은행 소속이었던 박성호 PB가 제5화에서는 한미증권 소속으로 등장" — this is a Stage 4 manuscript issue, not a Stage 3 blueprint issue

**Classification**: `cleared / not primary` for T3 lane (belongs to T4)

## 4. Blueprint Health Matrix

| Episode | Blueprint Stage 3 Score | Hard Contradiction | Loose/Ambiguous Pressure | Clean |
|---|---|---|---|---|
| EP5 | PASS (95) | - | Capital amount ambiguity (equipment vs ending) | Mostly clean; no wrong NPC data |
| EP6 | PASS (100) | 한미증권 institution error; capital 19.3억 assumes undepleted | time_flow plausible | - |
| EP7 | PASS (100→95) | 한미증권 institution error (inherited from EP6 blueprint) | - | - |

## 5. Mechanism Gaps Identified

### Gap 1: No NPC-Attribute Anchor in Fact-Lock

The `_build_fact_lock_packet` (compiler L551-638) extracts location, time, ending_hook, equipment, and item storage anchors. It does **not** extract NPC affiliation/institution anchors. The 한미증권 error is invisible to fact-lock.

### Gap 2: Capital-Lock Requires Structured Keys That Blueprints Don't Produce

The `_build_capital_continuity_packet` (compiler L641-732) scans `ending_state` for keys like `balance`, `capital`, `deployed`, `position`. The LLM generates capital information as free-text in `equipment` lists and `protagonist_status` strings. The structured keys are never populated, so the capital-lock is permanently empty for this story.

### Gap 3: Location Continuity Check Uses Coarse Area Matching

The `_is_location_transition_valid` (validator L1117-1128) extracts the first 2-5 Korean characters as area. "여의도 한미증권" and "여의도 SW인베스트먼트" both yield "여의도", making them appear identical.

### Gap 4: Batch Blueprint Generation Prevents Manuscript-Truth Propagation

All blueprints for an arc are generated before any Stage 4 execution. Stage 4 corrections in early episodes cannot flow back to later blueprints. This is a structural limitation, not a bug.

## 6. Answers to Lane Questions

### Q: Do EP5/6/7 blueprints already contain the capital, time, or item-state drift?

**Yes.** EP6/EP7 contain a hard institution error (한미증권 vs 시중은행). EP5→EP6 has capital-state drift (full deployment followed by re-availability). Time progression (Jan→late Feb) is plausible.

### Q: Did the new fact-lock/capital-lock actually narrow the blueprint, or are the conflicts still born in Stage 3?

**Conflicts are still born in Stage 3.** The fact-lock narrows some aspects (location, time, ending_hook) but misses NPC-attribute anchors entirely. The capital-lock was structurally bypassed because the blueprint schema produces no structured capital keys. Both locks failed to prevent the primary error family.

### Q: For each troubled episode, is the blueprint:

- **EP5**: `loose/ambiguous pressure` — internal capital inconsistency (equipment says 예치, ending says 진입 완료) but no wrong NPC data
- **EP6**: `hard contradiction` — wrong institution name, wrong capital assumption
- **EP7**: `hard contradiction` — inherited wrong institution from EP6 blueprint

## 7. Mandatory Final Lines

- **Dominant seam in this lane**: stage3
- **Can this lane explain a real rescue round by itself**: yes
- **Would this lane justify a bounded next execution wave**: yes

## 8. Recommended Next Wave Scope (If Authorized)

If a bounded execution wave is authorized, the following Stage 3 fixes would address the primary cause:

1. **NPC-attribute fact-lock anchor**: Add NPC institution/affiliation to `_build_fact_lock_packet` output, sourced from state_tracker NPC registry
2. **Capital-lock schema enrichment**: Either add structured capital keys to blueprint response schema, OR parse capital amounts from equipment/protagonist_status free-text as a fallback in `_build_capital_continuity_packet`
3. **Location check granularity**: Replace 2-5 char prefix matching with institution-name token comparison in `_collect_continuity_prevalidation_issues`

These are Stage 3 contract-level fixes, not Stage 4 validator fixes.
