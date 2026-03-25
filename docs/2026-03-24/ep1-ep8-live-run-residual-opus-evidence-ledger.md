# EP1-EP8 Live-Run Residual Opus Evidence Ledger

Date: 2026-03-24
Companion to: `docs/2026-03-24/ep1-ep8-live-run-residual-opus-survey-report.md`
Status: supplementary evidence (Terminal 3)
Evidence Run: `projects/0324_00_`

---

## Purpose

This ledger documents artifact-level evidence that diverges from or supplements the primary survey report. Six divergence points are recorded with line-level evidence.

---

## Divergence 1: EP1 Trust Provenance Is Dual-Source, Not Single-Source

**Primary report says**: EP1 established "어머니 신탁" (mother's trust), and EP2 blueprint contradicted it with "조부" (grandfather).

**Artifact evidence**: EP1 actually established a **dual-source** provenance. The canonical EP1 line (from EP2 rejected manuscript cross-reference) reads:

> "할아버지가 남겨주신 차명 계좌, 어머니가 몰래 신탁해 둔 자산"

This means **both** grandfather (차명 계좌) and mother (신탁 자산) are canonical. The EP2 blueprint collapsed this dual source to grandfather-only ("조부님께서 제 앞으로 남겨주신"). The EP2 final manuscript (attempt_04) then independently re-resolved to mother-only ("어머니께서 제 앞으로 남겨주신").

**Implication**: The root cause is not "blueprint said X but EP1 said Y" — it's "EP1 said X+Y, blueprint collapsed to X, writer later collapsed to Y." The Stage 3 blueprint generator failed to preserve a compound factual claim. This is a harder problem than simple fact lookup.

**Evidence paths**:
- EP2 attempt_01 rejected L17: "조부 명의로 묶여 있는 HMC투자증권의 신탁 계좌"
- EP2 attempt_04 final L90: "어머니께서 제 앞으로 남겨주신 20억 원 규모의 HMC투자증권 신탁 계좌"
- EP2 blueprint: "조부님께서 제 앞으로 남겨주신 20억 원" (consistent throughout)

---

## Divergence 2: EP5 "5천만 원 Gap" May Be Validator False Positive

**Primary report says**: Writer manuscript invention — EP4의 5천만 원 법인설립비가 EP5 잔고에 미반영.

**Artifact evidence**: Both EP5 manuscript versions show **internally consistent** accounting:

| Version | Account display | Explanation |
|---------|----------------|-------------|
| attempt_01 before_fix | `[예수금: 1,900,000,000원]` + "보증금 3천만 원을 제외하고 남은 19억 원" | 19.3B - 0.3B deposit = 19.0B |
| attempt_03 patched | `[예수금: 1,900,000,000원] 사무실 보증금 3천만 원을 지출하고 남은 19억 원` | Same math, clearer framing |

Math check: 19.3억 (EP3 liquidation) - 0.3억 (office deposit) = 19.0억. Both versions show 19.0억. The "5천만 원 법인설립비" that post-select flagged is **not visible in either manuscript** — the manuscripts account for 3천만 원 deposit only.

**Implication**: The post-select validator may have flagged a discrepancy that doesn't exist in the manuscripts, or the "5천만 원" figure comes from a different source (perhaps EP4 canonical state that the writer didn't reference but also didn't contradict). If this is a validator false positive, the EP5 attribution shifts from "writer invention" to "validator overreach on this specific axis."

**Caveat**: EP4 artifacts were not in the required evidence surfaces. If EP4 established a specific 5천만 원 corporate capitalization spend, then the validator is correct that 19.0억 should have been lower. Without EP4 artifact verification, this is **inconclusive but worth flagging**.

---

## Divergence 3: EP6 Blueprint Is NOT Clean — 15B vs 19.3B Capital Gap

**Primary report says**: EP6 blueprint was clean; writer invented the conflicts.

**Artifact evidence**: The EP5-EP6 blueprint pair contains an **irreconcilable capital state**:

| Blueprint | Capital deployed to WTI | Venue | Amount |
|-----------|------------------------|-------|--------|
| EP5 | Full seed money | Direct HTS at SW인베스트먼트 | ~198万$ (~19.3B at 970₩/$) |
| EP6 | Partial | via 한미증권 PB (박성호) | 15B at 3x leverage |

The EP6 blueprint's scene_1 content says "19억 3천만 원의 시드머니" while simultaneously referencing "15억 원어치의 자금을 WTI 6월물" in scene_2. The 4.3B gap (19.3B - 15B) is **never explained in any blueprint**. This means:

- EP5 writer is told to go all-in with ~19.3B
- EP6 writer is told the position is 15B
- No intermediate blueprint establishes a partial exit or account restructuring

The EP6 R2 continuity firewall rejection (score 44, "2B in corporate account as if money was never invested") stems directly from this **blueprint-level capital inconsistency**, not purely from writer invention.

**Evidence paths**:
- EP5 blueprint equipment: "약 198만 달러가 예치된 파생상품 계좌"
- EP6 blueprint scene_2 content: "15억 원어치의 자금을 WTI 6월물 3배 레버리지"
- EP6 blueprint scene_1 content: "19억 3천만 원의 시드머니"
- EP6 R3 final manuscript L70: "내 전 재산 19억 원은 단 1원의 여유도 없이 WTI 롱 포지션 증거금으로 묶여 있다" (writer resolved via narrative bluff)

**Implication**: The EP6 attribution should include "Stage 3 blueprint capital tracking error" alongside "Stage 4 writer invention." The primary report's clean-blueprint assessment for EP6 is incorrect on this axis.

---

## Divergence 4: EP7 Blueprint Seeds the "18년 전" Error

**Primary report says**: EP7 blueprint was clean; writer invented the temporal metaphor error.

**Artifact evidence**: The EP7 blueprint's `integrated_scenario` text contains:

> "18년 전 수백억의 부채에 짓눌려 숨을 헐떡이던 원룸에서의 기억"

This phrase feeds directly into manuscript generation. All 3 candidate writers reproduced the "18년 전" error because **the blueprint itself seeded it**.

Additionally, the EP7 blueprint is structurally the weakest in the set:
- `goal` fields: **ALL EMPTY** (vs all filled in EP2-EP6, EP8)
- `target_beat`: **EMPTY**
- `pacing_notes`: **EMPTY**

**Structural completeness comparison**:

| Field | EP2 | EP3 | EP5 | EP6 | EP7 | EP8 |
|-------|-----|-----|-----|-----|-----|-----|
| scene goals | Filled | Filled | Filled | Filled | **EMPTY** | Filled |
| target_beat | Filled | Filled | Filled | Filled | **EMPTY** | Filled |
| pacing_notes | Filled | Filled | Filled | Filled | **EMPTY** | Filled |

**Implication**: EP7's PASS_WITH_FIX was partially a blueprint-seeded issue, not purely writer invention. The attribution should be "Stage 3 blueprint (seeded) + Stage 4 writer (reproduced)."

---

## Divergence 5: `_inventory_gaps` WorldState Lag Creates False Positives

**Primary report says**: Net-helpful but off-axis.

**Code + artifact evidence**: The gap detection mechanism has a structural timing problem:

1. `_detect_inventory_gaps()` compares against `WorldState.get_owned_items()` (stage3_orchestrator.py L2383-2447)
2. WorldState updates **after episode acceptance**, not during blueprint generation
3. If Stage 3 generates blueprints in batch-ahead mode, gaps are computed against stale ownership records

Observed false positives:
- EP2: "leather notebook" flagged as not-held when EP1 already acquired it
- EP7-8: "WTI futures 1.5B purchase confirmation" flagged as not-held despite EP5 establishing the position

The consumption side (chief_writer_context_packets.py L92-108) uses reject-threat language: "Using it without setup is reject-worthy." This creates direct contradicting-authority pressure when the blueprint assumes the item is available in a specific scene.

**Implication**: The gap system is net-harmful in its current form due to (a) stale WorldState producing false positives and (b) reject-threat language creating ambiguous writer pressure that conflicts with blueprint scene instructions.

---

## Divergence 6: `prev_digest` Has No Financial/Numeric Extraction Patterns

**Not in primary report.** New finding from code analysis.

The `prev_digest` regex patterns (chief_writer_context_packets.py, _generate_episode_digest) extract:
- Deaths / character exits
- Item gains/losses
- Injuries
- Locations
- Skills / techniques

The patterns do **NOT** extract:
- Account balances (N억 원, N천만 원)
- Position entries (WTI 롱/숏, 레버리지 N배)
- Transaction records (입금, 출금, 체결)
- Capital deployment state (증거금, 예수금)
- Price levels (배럴당 N달러)

This means the most real-time carryover source (prev_digest, no update lag) is **blind to the dominant conflict axis** for investment fiction. The writer must rely on fact_ledger (1-episode lag) or prev_manuscripts_section (full text, potentially truncated) for financial state.

**Multiple overlapping numeric truth sources with no reconciliation**:

| Source | Lag | Financial coverage | Priority |
|--------|-----|-------------------|----------|
| prev_digest | 0 (real-time) | **NONE** | STEP 2 in prompt |
| prev_ending (2,500 chars) | 0 | Partial (if ending mentions numbers) | STEP 2 |
| fact_ledger_summary | 1 episode | Full | tier0_parts |
| world_state_summary | 1 episode | Full | tier0_parts |
| canonical_numeric | 1 episode | Curated | tier0_parts |
| immutable_fact_section | Mixed | Contract-based | STEP 1 |
| prev_manuscripts_section | 0 | Full (if not truncated) | STEP 2 |

When these disagree (e.g., fact_ledger says 19.3B but prev_manuscript says 19.0B after deposit), the writer has no explicit reconciliation signal.

**Implication**: Adding financial/numeric extraction patterns to `prev_digest` is the most infrastructure-actionable finding from this survey. It would give the writer a real-time financial state digest that can correct blueprint authority errors without requiring Stage 3 redesign.

---

## Revised Stage Attribution Ledger (Based on Artifact Evidence)

| Episode | Primary report attribution | Revised attribution | Change reason |
|---------|---------------------------|--------------------|----|
| EP2 | Stage 3 blueprint PRIMARY | **Stage 3 blueprint PRIMARY** (unchanged) | Same — but note EP1 was dual-source, not single-source |
| EP3 | Writer drift PRIMARY | **Writer-packet gap PRIMARY** + manuscript expansion SECONDARY | prev_digest didn't carry safe-location detail |
| EP5 | Writer invention PRIMARY | **Inconclusive** — possible validator false positive on 5천만 axis; leverage/NPC title are genuine writer errors | Need EP4 artifact to confirm |
| EP6 | Writer invention PRIMARY | **Blueprint capital tracking error PRIMARY** + writer timeline invention SECONDARY | 15B vs 19.3B is blueprint-level, not writer-level |
| EP7 | Writer invention PRIMARY | **Blueprint-seeded (18년 전 in integrated_scenario)** + writer reproduction | Blueprint fed the error to all 3 candidates |

**Revised attribution counts**:
- Stage 3 blueprint authority error: **3-4** of 5 (EP2, EP6, EP7, possibly EP5 if validator false positive)
- Stage 4 writer-packet gap: **1** (EP3 safe-location)
- Stage 4 manuscript expansion: **2-3** (EP3 timeline, EP5 leverage/NPC, EP6 timeline)
- Validator false positive: **0-1** (EP5 capital axis, inconclusive)

---

## Revised Dominant Seam Assessment

The primary report concludes "Stage 4 writer drift" accounts for 4/5 troubled episodes. Artifact-level evidence revises this:

**Stage 3 blueprint authority errors are the primary upstream cause in at least 3 of 5 troubled episodes** (EP2 provenance, EP6 capital tracking, EP7 temporal wording). The writer faithfully reproduces blueprint errors, and post-select validators correctly catch them. The rescue-round pattern is predominantly a Stage 3 → Stage 4 error propagation chain, not independent Stage 4 invention.

The secondary infrastructure gap is `prev_digest` lacking financial extraction — this removes the writer's corrective power against blueprint errors in the dominant conflict axis (capital/numeric state).

---

## Agreement Points with Primary Report

Both analyses agree on:
1. **Dominant seam = mixed seam** ✓
2. **Post-select rejects mostly valid = yes** ✓
3. **Should open SSOT = no** ✓
4. **Cleared non-culprits** align ✓
5. **PASS_WITH_FIX vs post-select = correct separation of concerns** ✓
6. **EP8 = clean due to narrow scope + mature carryover** ✓

The disagreement is on **weight distribution** within the mixed seam: primary report weights Stage 4 writer invention heavier (4/5), this ledger weights Stage 3 blueprint authority errors heavier (3-4/5).
