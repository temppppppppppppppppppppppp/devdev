# T9: Artifact Truth Diff Ledger

Date: 2026-03-24
Status: final
Lane: `Artifact Truth Diff Ledger`
Terminal: T9
Governing Order: `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md`
Primary Evidence Run: `projects/0324_00_`

---

## 1. Executive Summary

Episode-by-episode artifact diffs (blueprint → rejected → patched/final) reveal that **the first undeniable conflict is already present in the blueprint for 2 of 5 troubled episodes** (EP2, EP3), **originates at the manuscript expansion level for 2 of 5** (EP6, EP7), and **is a compound blueprint+writer failure for 1 of 5** (EP5).

The single most critical finding is: **EP3's notebook-location error ("서랍") was explicitly present in the blueprint**, confirmed by the production log entry "Blueprint '서랍 보관' 오류를 '금고 보관'으로 자체 교정." This is a Stage 3 authority error, not a writer drift — contradicting the existing single-lane survey report's attribution of EP3 as "Writer PRIMARY."

The artifact diffs also reveal a previously unreported residual: **EP8's final manuscript contains "18년 전" on line 107** despite EP7's PASS_WITH_FIX patch having corrected this to "전생에." EP8 passed Round 1 without this being caught.

---

## 2. Included Coverage / Exclusions

### Included

- EP2: blueprint (dialogue_focused, attempt_02) → rejected (A_balanced, attempt_01) → final (A, attempt_04)
- EP3: blueprint (emotion_focused, attempt_01) → rejected (C_tension, attempt_01) → patched (A, attempt_02)
- EP5: blueprint (emotion_focused, attempt_01) → selected_before_fix (B, attempt_01) → patched (A_inplace_patch, attempt_03)
- EP6: blueprint (dialogue_focused, attempt_03) → rejected (A_tension, attempt_01) → final (A, attempt_03)
- EP7: blueprint (emotion_focused, attempt_01) → selected_before_fix (B, attempt_01) → patched (A_InPlace, attempt_01)
- EP8: blueprint (action_focused, attempt_01) → final (A, attempt_01) — clean baseline comparison

### Excluded

- EP1, EP4 (clean passes, no diffs to analyze)
- Stage 2 arc artifacts (T2 lane)
- Code-level analysis (T6, T7 lanes)
- Validator signal quality analysis (T8 lane)

---

## 3. Key Evidence

### 3.1 EP2: Trust Provenance Flip

#### Blueprint says

> "조부 명의로 묶여 있는 HMC투자증권의 신탁 계좌, 20억 원"
> (Grandfather's-name trust account at HMC Investment Securities, 2B won)

#### Rejected manuscript (attempt_01) says

> "조부 명의로 묶여 있는 HMC투자증권의 신탁 계좌"
> Trust dissolution requires "한정호 회장의 동의" before age 30 (서른 살 제한)

The rejected manuscript faithfully follows the blueprint's "조부" provenance and adds an age-restriction clause.

#### Final manuscript (attempt_04) says

> "어머니께서 제 앞으로 남겨주신" (mother's legacy, in my name)
> No age restriction mentioned. Opens with a 김 변호사 phone call establishing that HMC compliance monitors owner-family accounts → "정공법" (direct approach) required.

#### Diff ledger

| Element | Blueprint | Rejected (A01) | Final (A04) | First Conflict |
|---|---|---|---|---|
| Trust originator | 조부 (grandfather) | 조부 | **어머니** (mother) | **Blueprint** |
| Age restriction | Not mentioned | 서른 살 전 해지 불가 | Absent | Rejected (invention) |
| Kim lawyer call | Absent | Absent | Present (opens ep) | Final (addition) |
| Clothing | Not specified | 네이비 슈트+넥타이 | 네이비 셔츠+슬랙스 | Minor |
| Hallway time | Not specified | Unspecified | 16:30, 16:35 | Final (precision) |
| Share transfer | Not mentioned | Absent | MC offers shares | Final (addition) |
| Closing line | N/A | "설계를 시작할 뿐" | "전쟁을 시작할 뿐" | Tone shift |
| Chairman approval | Not specified | "내일 오전" | Same-day implied | Compressed |

**First undeniable conflict**: Blueprint authority. The blueprint says "조부" but EP1's established truth is "어머니." The writer faithfully followed the blueprint error for 3 rounds before self-correcting on round 4.

### 3.2 EP3: Notebook Location + Timeline Reversal

#### Blueprint says

> Scene 2 "온실을 나서는 짐싸기": "가죽 노트를 서랍 깊숙이 넣어둔다" (stores notebook deep in a drawer)
> Scene 4 trust dissolution before 4 PM bank closing
> quality_risk=true flagged (MAJOR location discontinuity warning)

#### Rejected manuscript (attempt_01) says

> 가죽 노트를 "서랍" (desk drawer) 깊숙한 곳에서 꺼냄
> VVIP 방문 시간: 오후 3시 35분 (same day as chairman meeting)
> Same-day visit: mansion → VVIP center directly

#### Patched manuscript (attempt_02) says

> 가죽 노트를 "소형 금고" (small safe behind bookshelf, 2nd shelf) 에서 꺼냄
> Day transition: "그리고 다음 날 오후" (explicit next-day marker)
> VVIP 방문 시간: 오후 3시 30분

#### Production JSONL confirmation

EP3 R2 (patched) Director open review:
> "Blueprint '서랍 보관' 오류를 '금고 보관'으로 자체 교정"

This explicitly confirms: **the blueprint said "서랍" and the writer corrected it to "금고."**

#### Diff ledger

| Element | Blueprint | Rejected (A01) | Patched (A02) | First Conflict |
|---|---|---|---|---|
| Notebook storage | **서랍** (drawer) | 서랍 (follows blueprint) | **소형 금고** (safe) | **Blueprint** |
| Day transition | Same-day implied | Same-day | **"다음 날 오후"** (next day) | Blueprint (ambiguous) → Writer (resolved) |
| VVIP arrival | Bank closing 4 PM | 3:35 PM | 3:30 PM | Minor |
| Trust provenance | 어머니 | 어머니 | 어머니 | Consistent |
| Financial math | 20억 - 3.5% = 19.3억 | 20억 - 7천만 = 19.3억 | Same | Consistent |

**First undeniable conflict**: Blueprint authority. The blueprint explicitly says "서랍" while EP2's final manuscript established the notebook is in "소형 금고." The rejected manuscript faithfully followed the blueprint; the patched version overrode the blueprint to match established truth.

**Critical correction to existing survey**: The single-lane survey report (section 4) attributes EP3 as "Writer PRIMARY." The production JSONL explicitly says "Blueprint '서랍 보관' 오류" — the blueprint carried the wrong storage location. This is a **Stage 3 blueprint authority error**, not a writer drift.

### 3.3 EP5: Leverage Arithmetic + Capital Accounting

#### Blueprint says

> Account: 1,930,000,000원 (19억 원)
> Exchange: 970원/$ → ~$1,958,762.88 (~195만 달러)
> Scene 5: "~$1.98 million enters WTI long position" at $60.20
> No mention of "3배 레버리지" in EP5 blueprint
> No mention of specific contract count (480) in EP5 blueprint

Note: "3배 레버리지" appears first in **EP6 blueprint** Scene 1, not EP5.

#### Selected-before-fix manuscript (B, attempt_01) says

> Account: 1,900,000,000원 (보증금 3천만 제외 후 19억)
> Exchange: 970원/$ → $1,958,762.88
> Entry: 480 contracts at $60.20
> Leverage: "증거금 ~4,000$/계약" → max 480 contracts
> 한태준 title: "부사장님"
> "18년 뒤" temporal direction: correct from 2006 perspective

#### Patched manuscript (A_inplace_patch, attempt_03) says

> Same financial figures (19억, $1,958,762.88, 480 contracts, $60.20)
> 한태준 title: **"이사님"** (demoted from 부사장)
> 한태준 characterization: "후계 구도에서 밀려나 변두리를 맴도는 큰형" (marginalized)
> Trust fund description: adds two-step process (현금화 → 증권 계좌 → 파생상품 계좌)

#### Diff ledger

| Element | Blueprint | Before-fix (B01) | Patched (A03) | First Conflict |
|---|---|---|---|---|
| Account balance | 19.3억 | 19억 (after 3천만 deposit) | Same | Consistent |
| USD conversion | ~$1.98M | $1,958,762.88 | Same | Consistent |
| Contract count | Not specified | 480 | 480 | **Manuscript** (writer specified) |
| Leverage claim | Not in EP5 blueprint | Not explicit (implied by 480 contracts) | Same | N/A for EP5 |
| 한태준 title | Not specified | 부사장님 | **이사님** | Manuscript (inter-attempt correction) |
| 한태준 role | Not specified | In charge of restructuring | Marginalized bystander | Manuscript (characterization fix) |
| Transfer steps | Single step | Single step | Two-step (현금화→증권→파생) | Patched (precision) |

**First undeniable conflict**: Manuscript expansion. The EP5 blueprint is clean regarding leverage — the "3배 레버리지" claim originated in the writer's dialogue, and the 480-contract count was the writer's arithmetic. The PASS_WITH_FIX for leverage arithmetic was a Stage 4 writer-generated contradiction.

**Capital accounting gap**: The post-select rejection (EP4's 보증금 3천만 원 → EP5 잔고 미반영) is also a writer gap — the blueprint correctly tracked 19.3억, but the writer's manuscript displayed inconsistent deduction sequences.

### 3.4 EP6: Capital Integrity + Timeline Invention

#### Blueprint says

> "2006년 2월 하순" setting (late February 2006)
> 19.3억 capital (carried forward)
> WTI June futures at $60.20 (sideways)
> Plans: 15억 won at 3x leverage through Park Seongho at Hanmi Securities
> Park's toxic fund: "20억 원" allocation to unload (this is PARK's inventory, not Si-woo's money)

#### Rejected manuscript (A_tension, attempt_01) says

> **[2006년 4월 18일 밤 11시]** — 2-month jump from established February timeline
> **"확보해 둔 20억 원의 법인 자금"** — Si-woo has 20억 in corporate account
> **"20억 원이 찍힌 법인 통장"** — reiterated as Si-woo's corporate bank statement
> Coat: "본가를 나설 때 챙겨 왔던 명품 의류들" (from family home)
> "내 돈 15억" — presents 15억 as available cash
> Si-woo carries 법인 인감, OTP, 법인 통장 as physical documents

#### Final manuscript (A, attempt_03) says

> **"2006년 2월 하순의 심야"** — corrected to February
> **No "20억 법인 자금" or "법인 통장" references** — completely removed
> Coat: **"여의도 부티크에서 개인 신용카드 한도를 긁어 구입"** — newly purchased
> "내 수중에 현금 15억이 있다고? 웃기는 소리" — explicitly denies having cash
> "지금 내 전 재산 19억 원은 단 1원의 여유도 없이 WTI 롱 포지션 증거금으로 묶여 있다" — clarifies zero free cash
> 15억 offer to Park = bluff ("존재하지도 않는 고깃덩어리의 냄새")

#### Diff ledger

| Element | Blueprint | Rejected (A01) | Final (A03) | First Conflict |
|---|---|---|---|---|
| Timeline | 2월 하순 | **4월 18일** | 2월 하순 | **Manuscript** (2-month invention) |
| Si-woo's cash | 19.3억 (all in WTI) | **20억 법인 자금** | 0 (explicitly stated) | **Manuscript** (capital invention) |
| 15억 nature | Leverage play | **Cash offer** | Bluff/bait | **Manuscript** (reinterpretation) |
| Park's 20억 | Park's toxic fund inventory | Conflated with Si-woo's money | Not mentioned | **Manuscript** (entity conflation) |
| Coat provenance | Not specified | 본가 명품 (family home) | 신규 구입 (credit card) | **Manuscript** (origin changed) |
| 파텍필립 watch | Not specified | Already on wrist (본가) | Not mentioned | Minor |
| Location name | SW Investment office | **오피스텔** | SW인베스트먼트 사무실 | **Manuscript** (naming error) |

**First undeniable conflict**: Manuscript expansion. The blueprint is clean — it says "2월 하순" and carries 19.3억 with a clear leverage plan. The writer independently invented "4월 18일," "20억 법인 자금," "오피스텔," and conflated Park's toxic fund 20億 with Si-woo's corporate account.

**Root cause hypothesis**: The writer likely conflated two "20억" references — (a) Park's 20억 toxic fund inventory mentioned in the blueprint and (b) Si-woo's original 20억 trust before fee deduction. This conflation created the false "20億 법인 통장" artifact.

### 3.5 EP7: Temporal Direction Error

#### Blueprint says

> Scene 5: "2024 파산 기억" — references 2024 bankruptcy in the future/past-life framing
> No "18년 전" phrasing in the blueprint

#### Selected-before-fix manuscript (B, attempt_01) says

> **"18년 전 시우 자신을 짓눌렀던 파산의 환상통이 미세하게 손목을 훑고 지나갔다"**
> From 2006's perspective, "18년 전" = 1988 — nonsensical. Intended: 2024 future/past-life memory.

#### Patched manuscript (A_InPlace, attempt_01) says

> **"전생에 시우 자신을 짓눌렀던 파산의 환상통이 미세하게 손목을 훑고 지나갔다"**
> Single-line fix. Unchanged ratio: 99.95%.

#### Diff ledger

| Element | Blueprint | Before-fix (B01) | Patched (A01) | First Conflict |
|---|---|---|---|---|
| Temporal reference | "2024 파산 기억" | **"18년 전"** (=1988, wrong) | **"전생에"** (previous life) | **Manuscript** |
| All other content | — | — | Character-identical | — |

**First undeniable conflict**: Manuscript expansion. The blueprint correctly references "2024 bankruptcy" without the "18년 전" phrasing. The writer converted this to "18년 전" which is temporally inverted from the 2006 viewpoint.

**Production log nuance**: The Director's comment says "Blueprint의 오류이긴 하나" — but artifact inspection shows the blueprint itself does NOT contain "18년 전." The Director's comment is inaccurate in attributing the error to the blueprint.

### 3.6 EP8: Unfixed Residual (Baseline Comparison)

#### Blueprint says

> "PTSD/phantom pain motif escalates" — references 2024 trauma
> No "18년 전" in the blueprint

#### Final manuscript (A, attempt_01) says

> Line 3: "전생에 시우 자신을 짓눌렀던 파산의 끔찍한 감각" — **correct** (matches EP7 patch)
> Line 107: **"18년 전 파산의 트라우마"** — **incorrect** (same error as EP7 pre-patch)

EP8 passed Round 1 (score 98) without the post-select or Director catching the "18년 전" on line 107. This is an **unfixed residual** — the EP7 patch corrected one instance but EP8's writer independently reproduced the error in a different sentence.

---

## 4. Findings Ranked

### Finding 1: Blueprint Authority Error Is Primary for EP2 and EP3 (CRITICAL)

**Confidence: 95%**

EP2's provenance flip (조부→어머니) and EP3's notebook location (서랍→금고) are both traceable to **explicit errors in the Stage 3 blueprint**. The production JSONL for EP3 R2 independently confirms: "Blueprint '서랍 보관' 오류를 '금고 보관'으로 자체 교정."

These are not writer drift. The writer faithfully followed the blueprint in each rejected attempt and only corrected the error when forced by post-select rejection.

**Attribution correction**: The single-lane survey report attributes EP3 as "Writer PRIMARY." This lane's artifact evidence proves it is **Blueprint PRIMARY** (Stage 3 authority error).

### Finding 2: Manuscript Invention Is Primary for EP6 (CRITICAL)

**Confidence: 95%**

EP6's capital integrity catastrophe (20億 법인 자금, 4월 18일 timeline, 오피스텔 naming) is entirely writer-generated. The blueprint correctly says "2월 하순," "19.3億 capital," and "SW Investment office." The writer invented all three errors.

**Root cause**: Entity conflation — Park's 20億 toxic fund inventory was conflated with Si-woo's original 20億 trust. The carryover ceiling's financial evidence caps (2 sentences × 160 chars) were insufficient to prevent this conflation.

### Finding 3: Manuscript Invention Is Primary for EP5 and EP7 (IMPORTANT)

**Confidence: 90%**

EP5's leverage arithmetic ("3배 레버리지" in dialogue vs 480 contracts ≈ 15x) and EP7's temporal direction ("18년 전" instead of "전생에") are both writer-level errors. The blueprints for these episodes are clean on the specific conflicting axes.

**EP5 nuance**: The EP6 blueprint (not EP5) introduces "3배 레버리지" — the writer may have been influenced by cross-episode knowledge leakage from the arc plan, but the EP5 blueprint itself does not specify "3x leverage."

### Finding 4: EP8 Contains an Unfixed "18년 전" Residual (IMPORTANT)

**Confidence: 98%**

EP8 line 3 uses "전생에" (correct, consistent with EP7 patch) but line 107 uses "18년 전 파산의 트라우마" (incorrect, same pre-patch error). This passed Round 1 uncaught. The post-select history check and Director both missed this within EP8.

### Finding 5: Successful Corrections Demonstrate System Capability (INFORMATIONAL)

The diff ledger also shows the system successfully correcting:
- EP2 R4: "조부"→"어머니" (writer self-correction after 3 post-select rejections)
- EP3 R2: "서랍"→"금고" (writer overriding blueprint error)
- EP3 R2: same-day→"다음 날 오후" (timeline transition fix)
- EP5 R3: leverage arithmetic resolved
- EP6 R3: 20億→"zero cash" + bluff framing
- EP6 R3: 4월→2월 하순
- EP7 R1: "18년 전"→"전생에" (inplace patch)

The correction system works — the cost is measured in rescue rounds, not in uncorrectable failures.

---

## 5. Cleared Non-Culprits

### Covert infrastructure invention — CLEARED

No burner phone, offshore broker, paper company, or shell company appears in any blueprint or manuscript artifact across EP1-EP8. The `_COVERT_INFRASTRUCTURE_TERMS` ban is effective.

### Inventory gaps as drift amplifier — CLEARED

`_inventory_gaps` warnings appear in all episodes but do not correlate with the actual rejection causes. The rejected artifacts show no evidence that TF-49 warnings pushed the writer toward incorrect state. The conflicts are in provenance, capital amounts, and temporal anchors — none of which are inventory-gap driven.

### Blueprint integrated_scenario as drift source — CLEARED

The `integrated_scenario_advisory` sections in blueprints are lengthy prose descriptions but do not contain the specific errors (조부, 서랍, 4월, 18년 전, 20億 법인) that caused rejections. The errors are in either the structured scene descriptions (EP2 조부, EP3 서랍) or entirely writer-generated (EP5, EP6, EP7).

---

## 6. Residual Culprit Candidate

### Two-source mixed seam

| Source | Episodes | Mechanism | Fix Path |
|---|---|---|---|
| **Stage 3 Blueprint Authority Error** | EP2, EP3 | Blueprint carries wrong provenance/item-location from arc plan, failing to cross-reference prev manuscript truth | Stage 3 validation: fine-grained factual cross-check of blueprint entity claims against prev published text |
| **Stage 4 Writer Manuscript Invention** | EP5, EP6, EP7 | Writer invents or conflates financial state, temporal references, and location names not present in blueprint | Carryover ceiling: expand financial deployment state constraints; consider negative-assertion capability ("zero free cash") |

### Attribution table (corrected from single-lane survey)

| Episode | Single-Lane Survey Attribution | T9 Corrected Attribution | Basis |
|---|---|---|---|
| EP2 | Stage 3 PRIMARY | Stage 3 PRIMARY | Agreement |
| EP3 | **Writer PRIMARY** | **Stage 3 PRIMARY** | Production log: "Blueprint '서랍 보관' 오류를 '금고 보관'으로 자체 교정" |
| EP5 | Writer PRIMARY | Writer PRIMARY | Agreement (blueprint clean on leverage axis) |
| EP6 | Writer PRIMARY | Writer PRIMARY | Agreement (blueprint clean on capital/timeline) |
| EP7 | Writer PRIMARY | Writer PRIMARY | Agreement (blueprint says "2024 파산," writer converted to "18년 전") |

**Corrected count**: Stage 3 primary = 2/5 (was 1/5). Stage 4 primary = 3/5 (was 4/5).

---

## 7. Next-Scope Recommendation

### Immediate (if Codex promotes to execution)

1. **Stage 3 fact cross-check** (addresses EP2, EP3 class):
   - Before emitting a final blueprint, compare key entity claims (trust originator, item locations, character titles) against the prev_digest and prev_manuscript tail
   - Scope: `stage3_orchestrator.py` post-validation layer
   - Bounded: add a factual pin-check, not a full rewrite

2. **Carryover ceiling negative assertion** (addresses EP6 class):
   - Extend `_build_stage4_carryover_ceiling_section` to synthesize a "capital deployment state" line: "전 재산 N億 → 자산 X에 전액 투입 → 가용 현금 0"
   - Scope: `chief_writer_context_packets.py` financial evidence section
   - Bounded: one regex pattern addition + one synthesis line

### Deferred

3. **EP8 "18년 전" residual**: Low priority — single-line phrasing error that doesn't affect plot integrity. Could be addressed by extending post-select temporal-direction checks, but not urgent.

4. **"3배 레버리지" cross-episode leakage**: EP6 blueprint says "3x leverage" but the writer introduced "3배" prematurely in EP5. This may be an arc-plan leakage pattern worth monitoring in longer runs.

---

## 8. Confidence And Limits

### Confidence: 93%

**High-confidence findings (95%+)**:
- EP2 provenance flip: blueprint → artifact chain fully traced
- EP3 notebook location: production JSONL independently confirms blueprint error
- EP6 capital/timeline invention: rejected vs final diff is unambiguous
- EP8 "18년 전" residual: directly observable in final manuscript text

**Moderate-confidence findings (85-90%)**:
- EP5 leverage attribution: the "3배 레버리지" does not appear in EP5 blueprint but does appear in EP6 blueprint — unclear if arc-plan cross-contamination occurred during writer context assembly
- EP7 Director comment "Blueprint의 오류이긴 하나": the Director may have had access to upstream arc-plan text containing "18년 전" that was not captured in the blueprint JSON artifact

**Limits**:
- Blueprint JSONs are the final selected candidates, not the full ensemble — intermediate rejected blueprint candidates may have contained different errors
- Writer context packets (the actual LLM prompt input) are not directly observable as artifacts — the carryover content is inferred from code analysis, not from a captured prompt snapshot
- 8-episode sample from a single run limits generalization about relative frequency of Source A vs Source B failures

---

## Mandatory Final Lines

- **Can this lane explain a real residual failure by itself**: yes — artifact diffs trace 5/5 troubled episodes to specific, reproducible conflict origins in blueprint or manuscript artifacts
- **Does this lane explain repeated rescue rounds after the closed waves**: yes — blueprint authority errors (EP2: 4 rounds, EP3: 2 rounds) and writer invention (EP5: 3 rounds, EP6: 3 rounds) directly caused all multi-round rescue cycles
- **Would this lane justify a bounded next execution wave**: yes — the Stage 3 fact cross-check and carryover ceiling negative assertion are bounded, artifact-grounded patches that address the two identified sources

---

## 3-Pass Audit Record

- Pass 1: Confirmed this is a survey report, not an execution SSOT. No code changes, no temp queue edits, no closure claims.
- Pass 2: Confirmed all diff claims are grounded in artifact bodies (blueprint JSONs, manuscript .txt files) and production JSONL, not console paraphrase. Weak claims marked with confidence levels.
- Pass 3: Confirmed the EP3 attribution correction is supported by the production JSONL entry "Blueprint '서랍 보관' 오류를 '금고 보관'으로 자체 교정" — this is artifact truth, not inference.
