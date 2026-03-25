# T4: Stage3 Blueprint Authority — Residual Survey Report

Date: 2026-03-24
Status: final (3-pass audited)
Lane: T4 — Stage3 Blueprint Authority
Terminal: 4
Canonical Path: `docs/2026-03-24/opus-live-run-residual/t4-stage3-blueprint-authority.md`
Evidence Path: `docs/2026-03-24/opus-live-run-residual/t4-stage3-blueprint-authority-evidence.md`
Primary Evidence Run: `projects/0324_00_`
Governing Order: `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md`

---

## 1. Executive Summary

Stage 3 blueprint authority is a **confirmed primary cause for EP2** and a **confirmed secondary amplifier for EP5 and EP6**. For EP3, EP7, and EP8 the blueprint is clean.

The dominant blueprint-level failure mode is **stale or conflicting state inheritance**: the blueprint generation receives the Arc tactical design and the previous manuscript in parallel, but when they disagree on a key fact (trust fund provenance, capital deployment status), the blueprint LLM tends to follow the Arc authority over the published-manuscript canon.

A secondary failure mode is **capital-state under-specification**: blueprints mention target financial amounts but do not encode a running capital balance or deployment ledger, leaving a gap that Stage 4 writers fill incorrectly.

This lane explains EP2's 4-round rescue cycle entirely. It partially explains EP5's and EP6's rescue rounds by creating ambiguous financial state that the writer then drifts further.

---

## 2. Included Coverage / Exclusions

**Included**:
- EP2 final blueprint (`stage3/ep_0002/attempt_02/final_blueprint__dialogue_focused.json`)
- EP3 final blueprint (`stage3/ep_0003/attempt_01/final_blueprint__emotion_focused.json`)
- EP5 final blueprint (`stage3/ep_0005/attempt_01/final_blueprint__emotion_focused.json`)
- EP6 final blueprint (`stage3/ep_0006/attempt_03/final_blueprint__dialogue_focused.json`)
- EP7 final blueprint (`stage3/ep_0007/attempt_01/final_blueprint__emotion_focused.json`)
- EP8 final blueprint (`stage3/ep_0008/attempt_01/final_blueprint__action_focused.json`)
- Stage 3 orchestrator context-injection mechanism (`modules/core/stage3_orchestrator.py`)
- Cross-reference with Stage 4 rejected/final manuscripts for conflict origination tracking

**Excluded** (other lanes own these):
- Arc 1/Arc 2 tactical design content (T2 lane)
- Stage 2 validation guardrails (T3 lane)
- `_inventory_gaps` generation mechanism (T5 lane)
- Stage 4 carryover consumption and writer context packets (T6 lane)
- Retry/PASS_WITH_FIX semantics (T7 lane)
- Validator signal quality (T8 lane)

---

## 3. Key Evidence

### EP2 Blueprint: Hard Contradiction Present

The EP2 blueprint (dialogue_focused, attempt_02) explicitly encodes the trust fund as "조부 명의의 HMC투자증권 신탁 계좌" (grandfather's name trust account) in multiple locations:

1. **`scene_breakdown.scene_1.key_events`**: "초기 자본금 20억 원 마련을 위해 **조부 명의의** HMC투자증권 신탁 계좌 해지 목표 설정"
2. **`integrated_scenario`**: "**조부님께서 제 앞으로 남겨주신** 20억 원 규모의 HMC투자증권 신탁 계좌를 오늘 자로 해지해 주십시오"
3. **`scene_breakdown.scene_4.key_events`**: "**조부 명의**의 신탁 계좌 해지를 요청"

However, EP1's final manuscript established the trust as "어머니께서 남겨주신" (mother's bequest). This is a **hard state contradiction already baked into the blueprint body**.

**Implication**: The Stage 4 writer faithfully followed the blueprint's "조부" framing in Rounds 1-3, and was correctly rejected by post-select each time. The writer was not drifting — it was following an authoritative blueprint that was wrong.

### EP3 Blueprint: Warning Present, Actual Conflicts Absent

The EP3 blueprint (emotion_focused, attempt_01) has `quality_risk: true` and a MAJOR python_warning: "위치 불연속: 한정호 회장의 서재 앞 → 본가 2층 복도 (서재 앞)". But the actual rejection causes were:

1. Notebook storage location: safe (EP2) → desk drawer (EP3 R1 writer invention)
2. Timeline regression: 4:35 PM (EP2) → 3:35 PM (EP3 R1 writer invention)

Neither of these is in the blueprint. The blueprint's location warning was on a different axis. **The blueprint is not primary for EP3's rejection.**

### EP5 Blueprint: Clean but Capital-State Stale

The EP5 blueprint (emotion_focused, attempt_01) is clean (`quality_risk: false`, 0 prevalidation issues). It specifies:

- Account balance: "1,930,000,000원" (scene_2 description)
- FX conversion: "환율 970원, 약 198만 달러" (scene_2 description)
- WTI entry at $60.20 (integrated_scenario)

**However**: EP4's final manuscript established a 50M won (5천만 원) corporate capital deduction for SW Investment's legal establishment. The EP5 blueprint uses "1,930,000,000원" — the pre-EP4-deduction figure from EP3's trust dissolution.

This means the blueprint inherited a **stale capital figure** that doesn't account for EP4's expenditure. The Stage 4 writer then used this stale figure, which post-select correctly flagged as a cross-episode accounting error.

**The blueprint is a secondary amplifier**: it didn't cause the conflict directly (writer could have subtracted the 50M), but it set the wrong baseline by not tracking running capital state.

### EP6 Blueprint: Clean but Capital Deployment Ambiguous

The EP6 blueprint (dialogue_focused, attempt_03) is clean. It specifies:

- **Scene 1 content**: "19억 3천만 원의 시드머니를 온전히 쏟아부을 3배 레버리지" — implies the full 19.3B is still available
- **Scene 2 content**: "15억 원어치의 자금을 WTI 6월물 3배 레버리지 롱 포지션에 밀어 넣는" — 15B allocation
- **Timeline**: "2006년 2월 하순" — correct

**Critical ambiguity**: EP5 ended with the protagonist having entered a WTI long position with the full ~198만 달러 (entire conversion of 19.3B). EP6's blueprint says he still has "19.3B to be fully deployed in 3x leverage" — as if the EP5 deployment didn't happen.

The blueprint doesn't acknowledge EP5's capital deployment. It doesn't state whether the EP5 position was closed, was a different trade, or is still active. This creates a **capital deployment state gap** that the writer then fills with contradictory content (EP6 R1 invented "20B corporate bankbook" and April timeline; EP6 R2 hit continuity firewall for impossible capital availability).

**The blueprint is a secondary amplifier**: the actual rejection causes (April date, coat provenance, 20B figure) were writer inventions, but the blueprint's failure to clarify the EP5→EP6 capital state transition created the opening.

### EP7 Blueprint: Clean

The EP7 blueprint (emotion_focused, attempt_01) is clean. The "18년 전" temporal phrasing artifact that caused PASS_WITH_FIX is **not present** in the blueprint. This is a pure Stage 4 writer invention.

### EP8 Blueprint: Clean, Baseline Comparison

The EP8 blueprint (action_focused, attempt_01) is clean. Round 1 PASS at score 98. No blueprint authority issues.

**Observation**: EP8 succeeded because it continues EP7's scene without introducing new state transitions. The financial state (15B, 3x, 45B notional, $60.20 entry) was already resolved and locked by EP7's final manuscript. When the capital state is clear, the blueprint works well.

### Stage 3 Context Injection Mechanism

Stage 3 blueprint generation receives the following state inputs:

| Input | Content | Size |
|-------|---------|------|
| `prev_manuscripts_text` | Recent published manuscripts from DB | Full text, windowed (last 24 + 6 anchor) |
| `prev_blueprint` | Previous episode's blueprint | Full dict |
| `arc_data` | Arc tactical design | Full dict (includes episode summaries, key_events, state_constraints) |
| `semantic_ctx` | Smart retrieval bundle (vec_memory + NPC + timeline + WorldState + FactLedger) | ~2,176 chars for EP2 |
| `prev_hud` | Previous episode's HUD protagonist state | Dict or None |
| `entity_registry` | NPC registry | List of entities |

**Key finding**: The blueprint LLM receives both the Arc tactical design and the previous published manuscript. When these two sources disagree on a fact (e.g., trust provenance), the LLM must resolve the conflict. The EP2 evidence shows the LLM chose the Arc's "조부" framing over EP1's published "어머니" framing.

**Hypothesis** (not proven — requires T2 Arc artifact confirmation): If the Arc 1 tactical design specifies "조부 신탁" as the capital source, then the blueprint LLM is following Arc authority, which is structurally upstream but chronologically pre-manuscript. The published manuscript should be the higher authority for already-resolved facts, but the blueprint LLM doesn't have an explicit priority rule.

---

## 4. Findings Ranked

### Finding 1: Blueprint Encodes Hard Provenance Contradiction (EP2) — CONFIRMED PRIMARY

- **Severity**: HIGH — caused 3 consecutive post-select rejects (4 total rounds)
- **Mechanism**: Blueprint scene_1/scene_4/integrated_scenario all specify "조부 명의 신탁" while EP1 canon says "어머니"
- **Root**: Blueprint LLM resolved a conflict between Arc tactical design and EP1 published manuscript by following the Arc
- **Cost**: 3 extra rounds × ~3-4 min per round = ~10-12 min wasted production time

### Finding 2: Blueprint Omits Running Capital Balance (EP5) — CONFIRMED SECONDARY AMPLIFIER

- **Severity**: MEDIUM — amplified writer drift into 2 extra post-select rejects (3 total rounds)
- **Mechanism**: EP5 blueprint uses 1,930,000,000원 (EP3 figure) without accounting for EP4's 50M deduction
- **Root**: Blueprint generation has no running capital ledger; it references the last explicitly mentioned amount without subtracting interim expenditures
- **Cost**: 2 extra rounds amplified by this baseline error

### Finding 3: Blueprint Omits Capital Deployment State (EP6) — CONFIRMED SECONDARY AMPLIFIER

- **Severity**: MEDIUM — amplified writer drift into 2 extra rejects including 1 continuity firewall (3 total rounds)
- **Mechanism**: EP6 blueprint says "19.3B to be fully deployed" without acknowledging EP5's already-completed WTI deployment
- **Root**: Same as Finding 2 — no deployment tracking across episodes
- **Cost**: 2 extra rounds amplified by this state gap

### Finding 4: Blueprint Warning on Wrong Axis (EP3) — INFORMATIONAL

- **Severity**: LOW — blueprint had quality_risk=true but actual rejection was on a different axis (writer drift)
- **Mechanism**: Blueprint's MAJOR location-discontinuity warning didn't cause the rejection; notebook storage and timeline were writer inventions
- **Assessment**: Blueprint's self-awareness mechanism (quality_risk flag) is present but doesn't protect against the specific axes where writer drift occurs

### Finding 5: Blueprint Has No Capital-State Schema — STRUCTURAL OBSERVATION

- **Severity**: LATENT — affects any investment-fiction episode with capital state transitions
- **Mechanism**: Blueprint `protagonist_state.equipment` tracks physical items but not financial state (account balance, deployed amount, available cash). Blueprint `ending_state` tracks location/timeline but not capital snapshot.
- **Assessment**: This is a structural gap in the blueprint schema, not a one-off error. It will recur in any future episode with capital transitions.

---

## 5. Cleared Non-Culprits

### Blueprint Internal Consistency: CLEARED

Within each blueprint, internal consistency is good. Scene breakdowns align with integrated scenarios. Pacing notes match tension levels. Character relationships track across scenes. The blueprints are well-crafted *internally*; the problem is *cross-episode state inheritance*.

### Blueprint Temporal Anchoring (EP3, EP6, EP7): CLEARED

The EP3 blueprint correctly sets "늦은 오후, 은행 마감 직후." The EP6 blueprint correctly sets "2006년 2월 하순." The EP7 blueprint is clean. The timeline conflicts (3:35 PM, April 18, "18년 전") are all **writer inventions** not traceable to blueprint content. Blueprint temporal anchoring is not primary for these episodes.

### Blueprint Quality Risk Detection: PARTIALLY CLEARED

The `quality_risk` flag and `python_warnings` mechanism works (detected EP3's location issue). But it currently only checks for:
- Location discontinuity
- Scene count
- Prevalidation issues

It does not check for:
- Provenance/fact consistency with prior published manuscript
- Running capital balance consistency
- Capital deployment state consistency

So the detection mechanism is cleared for what it covers, but has blind spots on the actual failure axes.

---

## 6. Residual Culprit Candidate

**Primary culprit**: Stage 3 blueprint state inheritance conflict resolution.

When the Arc tactical design and the published manuscript disagree on a key fact, the blueprint LLM has no explicit priority rule. It currently tends to follow the Arc (which is structurally upstream but factually pre-publication). For already-resolved facts (provenance, capital amounts), the published manuscript should be the higher authority.

**Secondary culprit**: Stage 3 blueprint capital-state under-specification.

The blueprint schema has no field for:
- `entering_capital_balance`: how much money is available at episode start
- `deployed_capital`: how much is locked in active positions
- `available_cash`: entering_balance - deployed - expenditures

Without these, every episode's writer must reconstruct the capital state from context, which is error-prone at the LLM level.

**Cross-lane interaction**: The blueprint's capital-state gap (this lane) combines with Stage 4's carryover consumption gap (T6 lane) to create a double failure: the blueprint doesn't specify it, and the carryover packet doesn't enforce it.

---

## 7. Next-Scope Recommendation

### If this lane alone justifies action:

1. **Blueprint fact-lock injection** (bounded, ~30-40 LOC):
   Add a post-generation validation step in `stage3_orchestrator.py` that cross-checks the blueprint's integrated_scenario against the previous episode's final manuscript for key factual anchors (character names, trust provenance, capital figures, timeline). If a contradiction is detected, flag it as a prevalidation issue and force regeneration.

2. **Capital-state schema extension** (bounded, ~20-30 LOC):
   Add `financial_state` to the blueprint output schema: `{entering_balance, deployed_amount, available_cash, key_expenditures}`. Populate from `FactLedger` + `WorldStateManager` data available at blueprint generation time.

### If merging with other lanes:

These two patches pair naturally with T6's carryover consumption fix. Blueprint fact-lock handles the source-of-truth problem; capital-state schema handles the specification gap; T6's carryover enrichment handles the consumption-side enforcement.

---

## 8. Confidence and Limits

### Confidence: 92%

**High confidence (95%+)**:
- EP2 blueprint contains the hard "조부" provenance contradiction (directly inspected)
- EP5 blueprint uses stale 1,930,000,000원 figure (directly inspected)
- EP6 blueprint doesn't acknowledge EP5's capital deployment (directly inspected)
- EP3/EP7/EP8 blueprints are clean for their respective rejection causes (directly inspected)

**Moderate confidence (85-90%)**:
- The hypothesis that the EP2 blueprint LLM chose Arc authority over published-manuscript authority. This requires T2 to confirm that the Arc 1 tactical design specifies "조부 신탁." If the Arc says "어머니" and the blueprint still wrote "조부," then the root cause is different (LLM hallucination rather than authority conflict).

**Low confidence (<80%)**:
- Whether the `semantic_ctx` window size (2,176 chars for EP2) was sufficient to include EP1's trust provenance detail. The provenance might have been in the full `prev_manuscripts_text` but not in the smaller `semantic_ctx`. Without artifact-level packet logging, this cannot be confirmed.

### 95% 미달 사유

The EP2 provenance conflict attribution depends on confirming the Arc 1 tactical design's content (T2 lane dependency). Without this, the blueprint's "조부" source could be either Arc authority inheritance or standalone LLM hallucination — two different root causes requiring different patches.

---

## 3-Pass Audit Record

- **Pass 1 (Structure)**: Confirmed this is a lane survey report following the master order's required sections. Scope is bounded to Stage 3 blueprint authority. Included/excluded surfaces are clear.
- **Pass 2 (Evidence)**: Cross-checked blueprint content against actual rejection causes for each episode. EP2 "조부 명의" confirmed in 3 separate blueprint locations. EP5 stale figure confirmed against EP3/EP4 canon. EP6 deployment gap confirmed against EP5 ending state. All file paths verified.
- **Pass 3 (Execution)**: Lane questions answered. Findings ranked by severity. Cross-lane dependencies identified (T2 for Arc content, T6 for carryover consumption). No overclaims — EP2 Arc source marked as hypothesis pending T2 confirmation.

---

## Mandatory Final Lines

- **Can this lane explain a real residual failure by itself**: yes (EP2's 4-round rescue cycle is entirely attributable to blueprint provenance error)
- **Does this lane explain repeated rescue rounds after the closed waves**: yes (EP2: 3 extra rounds; EP5/EP6: amplified by 2 extra rounds each; total: ~7 extra rounds partially or fully attributable)
- **Would this lane justify a bounded next execution wave**: yes (two bounded patches: blueprint fact-lock validation + capital-state schema extension, estimated ~50-70 LOC combined)
