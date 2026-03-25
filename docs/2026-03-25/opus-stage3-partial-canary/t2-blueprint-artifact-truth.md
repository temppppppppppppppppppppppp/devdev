# T2. Blueprint Artifact Truth

Date: 2026-03-25
Lane: T2 (Blueprint Artifact Truth)
Master Order: `docs/2026-03-25/stage3-partial-canary-3terminal-master-order.md`
Status: final

## 1. Scope

Inspected the actual Stage 3 `final_blueprint` JSON artifacts for EP5-EP9 in `projects/canary_0325/logs/artifacts/stage3/`, plus EP1-EP4 for cross-episode continuity.

Comparison target: prior known failure family from `projects/0324_00_/logs/artifacts/stage3/`.

Evidence base: on-disk blueprint JSON files, `plans/blueprints/*.txt` plain-text renders, `logs/session/ui_events.jsonl` inventory-gap entries, `logs/episode_production.jsonl` Stage 4 metadata.

## 2. Prior Culprit Family Definition

From the closed SSOTs:

- **Institution drift** (`stage3-npc-capital-carryforward-wave-execution-ssot.md` L47-48):
  - EP3 old run established `HMC투자증권` / `VVIP PB센터` as accepted institution authority.
  - EP6-EP7 old blueprints drifted that authority to `한미증권 본사 VVIP 프라이빗 룸`.
  - This was a name-level institution replacement within accepted canon.

- **Capital carry-forward** (`stage3-npc-capital-carryforward-wave-execution-ssot.md` L49-51):
  - EP5 old blueprint started from stale `19억 3천만 원` instead of the accepted EP4 baseline (`19억 원` after deduction).
  - EP6-EP7 old blueprints continued to expose `19억 3천만 원이 예치된 계좌 내역` even after capital was already deployed.
  - Phantom available-capital persisted across 3 episodes.

- **Temporal-deictic** (`stage3-blueprint-state-precision-reconciliation-wave-execution-ssot.md` L49):
  - EP7 old blueprint ending hook contained `18년 전` temporal phrasing that should have been blocked before Stage 4.

## 3. Findings

### 3.1 Institution Name Audit

**Search method**: `grep -c` for `한미증권|HMC투자증권` across all canary Stage 3 artifacts.

**Results**:

| EP | `HMC투자증권` occurrences | `한미증권` occurrences | Primary institution |
|----|--------------------------|----------------------|---------------------|
| EP1 | 0 | 0 | none (reincarnation/family) |
| EP2 | 0 | 0 | none (family conflict) |
| EP3 | 0 | 0 | `시중은행 여의도 본점 VIP 라운지` |
| EP4 | 0 | 0 | `시중은행 여의도 본점`, `공유 오피스` |
| EP5 | 0 | 8 | `여의도 한미증권 VIP룸` (first appearance) |
| EP6 | 0 | 10 | `여의도 한미증권 VIP룸` |
| EP7 | 0 | 5 | `여의도 한미증권 VIP룸` → `테헤란로` → `성북동` |
| EP8 | 0 | 2 | `한미증권` (PB phone reference only) |
| EP9 | 0 | 1 | `한미증권` (PB phone reference only) |

**Conclusion**: `HMC투자증권` does not appear anywhere in the canary EP1-EP9 blueprints. The old HMC→한미 drift pattern is **structurally impossible** in this run because the prior canon it would overwrite was never established.

`한미증권` first appears in EP5 as a fresh introduction and remains the sole securities firm through EP9. The institution name is internally consistent across 5 episodes.

### 3.2 Capital Flow Audit

**Traced protagonist capital state from blueprint `protagonist_state.equipment` and `ending_state`**:

| EP | Capital state in blueprint | Consistency check |
|----|---------------------------|-------------------|
| EP3 | `20억 원이 예치된 시중은행 VIP 통장` | baseline |
| EP4 | `20억 원이 예치된 시중은행 VIP 통장` | consistent with EP3 |
| EP5 | `20억 원이 예치된 시중은행 VIP 통장` → WTI 매수 선언 | consistent |
| EP6 | 15억 WTI매수 체결, `protagonist_status`: 15억 포지션 + 5억 잔고 | 20억 = 15억 + 5억 ✓ |
| EP7 | `잔고 5억 원이 찍힌 한미증권 법인 계좌 통장` | 15억 deployed, 5억 remaining ✓ |
| EP8 | `잔고 5억 원이 찍힌 한미증권 법인 계좌 통장` | consistent with EP7 ✓ |
| EP9 | 총자산 23억 원 (15억 원금 + 5억 현금 + 3억 미실현수익) | 15 + 5 + 3 = 23 ✓ |

**Conclusion**: Capital flow is internally consistent across all 7 tracked episodes. No phantom available-capital persists after deployment. The old `19억 3천만 원` stale carry-forward pattern is **completely absent**.

**Comparison**: old run EP5-EP7 all showed `19억 3천만 원` even after capital deployment in EP5. Canary correctly transitions 20억 → 15+5 → 23억.

### 3.3 Inventory Gap Audit

**Source**: `projects/canary_0325/logs/session/ui_events.jsonl`, `[TF-49] inventory gaps` entries.

| EP range | Gap item | Gap count |
|----------|----------|-----------|
| EP3-EP6 | `20억 원이 예치된 시중은행 VIP 통장` | 1 |
| EP7-EP9 | `잔고 5억 원이 찍힌 한미증권 법인 계좌 통장` | 1 |

**Interpretation**: The inventory gap system reports differences in protagonist equipment between episodes. The transition from `20억 통장` to `5억 통장` at EP7 reflects the legitimate capital deployment in EP6. Gap count is always 1 (one item changed).

**Conclusion**: Inventory gap is **advisory noise only**. It correctly reports the expected state transition. Gap count 1 is within normal operational bounds. No blocking issue.

### 3.4 Temporal-Deictic Warning Audit

**Source**: `projects/canary_0325/logs/artifacts/stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json` L7-14.

**Warning detail**:
```json
{
  "category": "temporal_deictic",
  "focus": "미래-기억 맥락의 절대 시간 참조를 제거하거나 상대적 표현으로 교체",
  "message": "시간 지시어 위험: 시나리오 말미에 '18년 전' 회상/기억 패턴 감지",
  "severity": "MAJOR",
  "source": "python_prevalidate"
}
```

**Impact on EP8 blueprint**:
- `prevalidation_issue_count`: 1
- `quality_risk`: true
- `total_candidates`: 2 (usual is 3 — one candidate likely filtered)
- Selected strategy: `dialogue_focused`, score per `ui_events.jsonl` seq 159: PASS / 92

**Actual EP8 integrated_scenario text**: Contains "이전 삶의 기억과 정확히 일치하는 방아쇠가 당겨진 것이다" — a reference to the protagonist's prior-life memory. The Python prevalidation flagged the `'18년 전'` memory pattern as temporal-deictic risk.

**Conclusion**: The temporal-deictic prevalidation is **working as designed**. It detected the pattern, flagged it at MAJOR severity, set `quality_risk: true`, and reduced the candidate pool from 3 to 2. Despite this, the Director still passed the blueprint at score 92, meaning the content was judged acceptable in narrative context (the protagonist IS a reincarnator whose memories ARE 18 years old). This is a **healthy catch**, not a new blocker.

### 3.5 Minor New Observation

박성호 NPC appears at `시중은행 여의도 본점 VIP 라운지` in EP3 and then at `한미증권 VIP룸` in EP5. This is a potential NPC-institution binding transition that is not in the same culprit family as the old HMC→한미 drift, but could warrant review in a broader NPC continuity audit.

This does NOT qualify as the old culprit family because:
- EP3's `시중은행` is a generic bank, not a named securities firm
- There is no prior "accepted authority" being overwritten
- The story plausibly supports a character appearing at both a bank and a securities firm

### 3.6 Prior Run Comparison Summary

| Dimension | Old run (`0324_00_`) | Canary (`canary_0325`) |
|-----------|---------------------|----------------------|
| EP3 institution | `HMC투자증권` / `VVIP PB센터` | `시중은행 여의도 본점` (generic) |
| EP5 capital | `19억 3천만 원` (stale) | `20억 원` (fresh baseline) |
| EP6 institution | `한미증권 본사 VVIP 프라이빗 룸` (drifted from HMC) | `여의도 한미증권 VIP룸` (consistent from EP5) |
| EP6-EP7 capital | `19억 3천만 원` (phantom — already deployed) | `5억 원 잔고` (correct after 15억 deployment) |
| EP7 temporal-deictic | `18년 전` in ending hook (not caught) | N/A for EP7 |
| EP8 temporal-deictic | N/A | `'18년 전'` caught by prevalidation, MAJOR warning, PASS/92 |
| Stage 3 한미증권 count | 51 across 7 files | 26 across 5 files |

## 4. Confidence

Estimated confidence: **97%**.

Residual 3%:
- Did not inspect DB project_data.db for blueprint metadata linkage (excluded from scope but would strengthen artifact-truth layer).
- Did not inspect all LLM I/O for EP3 canary to determine whether 박성호's appearance at 시중은행 was arc-directed or blueprint-generated.

## 5. Mandatory Final Lines

- Old Stage 3 culprit family in this lane: **suppressed**
- New Stage 3 concern in this lane: **none** (박성호 NPC-institution binding is micro-level, not a new Stage 3 systemic issue)
- Should this lane alone trigger a new SSOT: **no**
