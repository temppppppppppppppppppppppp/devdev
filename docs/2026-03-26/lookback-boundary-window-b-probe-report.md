# Lookback-Boundary Window B Probe Report

Date: 2026-03-26
Type: bounded lookback-boundary continuity probe (Window B from long-run probe plan)
Source Project: `00_001`
Target Project: `canary_0326_lookback_boundary`
Probe Window: EP8-EP12 (lookback boundary at EP12, where EP1 exits 10-episode retrospective validator window)
Run Status: completed (exit code 0)
Prior Reports:
- `docs/2026-03-26/long-run-continuity-probe-plan.md`
- `docs/2026-03-26/arc-boundary-window-a-probe-report.md`

## Evidence Artifacts

| Artifact | Path |
|----------|------|
| Canary summary | `projects/canary_0326_lookback_boundary/logs/stage3_canary_summary.json` |
| Session log | `projects/canary_0326_lookback_boundary/logs/session_20260326_123358.log` |
| EP12 final blueprint | `projects/canary_0326_lookback_boundary/plans/blueprints/blueprint_0012.txt` |
| EP10 final blueprint | `projects/canary_0326_lookback_boundary/plans/blueprints/blueprint_0010.txt` |
| EP1-EP7 source manuscripts | `projects/canary_0326_lookback_boundary/drafts/ep_0001.txt` through `ep_0007.txt` |

## Findings

### EP8-EP12 Generation Summary

| EP | Verdict | Score | Attempts | LLM Calls | Cost | Arc |
|---|---|---|---|---|---|---|
| 8 | PASS | 95 | 1 | 12 | $0.56 | 2 |
| 9 | PASS | 90 | 1 | 42 | $0.74 | 3 |
| 10 | PASS | 95 | 1 | 11 | $0.24 | 3 |
| 11 | PASS_WITH_WARNING | 87 | 1 | 41 | $0.69 | 3 |
| 12 | PASS | 90 | 1 | 10 | $0.19 | 3 |

**All 5 episodes passed on first attempt.** No retry amplification at the lookback boundary. EP12 (the primary target) passed cleanly with score=90, 10 LLM calls, $0.19.

Contrast with Window A: EP5 required 4 attempts. The lookback boundary is materially smoother than the arc boundary.

### EP1 Fact Survival at EP12

**FactLedger state** (`last_updated_ep=6`):

| EP1 Fact | Category | Still in FactLedger at EP12? | Referenced in EP12 Blueprint? |
|----------|----------|------------------------------|-------------------------------|
| SW인베스트먼트 법인 계좌 OTP | item | YES (history: ep1→ep6) | YES (implied via "잔여 5억" context) |
| SW인베스트먼트 법인 인감도장 | item | YES (history: ep1→ep6) | NO (not needed in EP12 plot) |
| SW인베스트먼트 법인 서류 | item | YES (destroyed EP5) | NO (correctly absent — destroyed) |
| 박성호 | character | YES (history: ep1→ep6) | YES (major NPC in EP12) |
| 한정호 | character | YES (history: ep1→ep4) | NO (not in EP12 plot) |
| 한태준 / 한태민 | character | YES (history: ep1→ep3) | NO (not in EP12 plot) |

**Director contradiction check at EP10-EP12**: Zero contradictions at all three episodes.

- EP10: "✅ [Director] 모순·일관성 이상 없음"
- EP11: "contradictions: [] (None found)"
- EP12: No contradiction reported; clean PASS at score=90

**EP12 blueprint content analysis**: The final EP12 blueprint correctly references:
- SW인베스트먼트 (EP1-established entity) as the protagonist's operating company
- 여의도 SW인베스트먼트 임시 사무실 → 강남 원룸 오피스 이전 (EP12 event, consistent with prior state)
- 박성호 PB (EP1-established NPC) as the protagonist's broker with established loyalty dynamic
- 원유 롱 포지션 → 매도 실현 (state carry-forward from EP8-EP10)
- 30억 총 자산 (correctly accumulated: 20억 원금 + 5억 실현 + 5억 미실현)
- 이스라엘-헤즈볼라 7월 사태 예고 (new forward-looking hook, consistent with established time period)

No EP1 fact was contradicted. No completed event was reopened.

### Persistence Layer Status at EP12

| Layer | Status | Evidence |
|-------|--------|----------|
| **FactLedger** | HELD | `last_updated_ep=6`. 11 characters, 11 items all preserved. EP1-origin items (OTP, 인감도장, 법인 서류) intact with full history chains. |
| **WorldState** | HELD | `last_updated_ep=6`. 11 relationships preserved. |
| **Reference Anchors** | NOT TESTABLE | 0 anchors — anchor extraction is a Stage 4 responsibility, not triggered in Stage 3-only runs. |
| **Cumulative Bible** | HELD | EP1-EP7 episode bibles available for context assembly. EP12 generation had access to all prior bibles. |
| **Entity Registry** | HELD | 74 entities (Arc 1) → 99 entities (Arc 2) — grew correctly across arcs. |
| **Inventory Tracking** | HELD | TF-49 tracked EP1 items through EP12. Gap count decreased from 2 (EP10) to 1 (EP12) as items were narratively consumed. |

**Note**: FactLedger and WorldState were not updated beyond EP6 because this is a Stage 3-only probe. State updates happen during Stage 4 (manuscript generation). The test was whether EP6-era persistence state is correctly injected into EP12 context — and it was.

### What Long-Gap Continuity Held

1. **EP1 entity preservation**: SW인베스트먼트 (EP1 entity) correctly referenced at EP12, 11 episodes later. No drift in entity identity.

2. **EP1 NPC preservation**: 박성호 (EP1 NPC) has a coherent character arc from EP1 (initial contact) through EP12 (complete loyalty/subordination). The relationship evolution is narratively consistent.

3. **Item state continuity**: OTP, 인감도장 correctly tracked from EP1 through EP12. Destroyed items (법인 서류 at EP5, 계산기 at EP6, 핸드폰 at EP3) correctly absent from later episodes.

4. **Financial state carry-forward**: Asset progression (20억 원금 → 30억 총 자산) correctly computed and referenced at EP12.

5. **Zero contradictions at target window**: Director found 0 contradictions at EP10, EP11, and EP12.

6. **No retry amplification at lookback boundary**: EP12 passed in 1 attempt with score=90. The lookback boundary did not cause the same retry cost as the arc boundary.

### What Weakened

1. **EP11 quality gate friction**: EP11 scored 86-89 across 4+ internal validation cycles, repeatedly hitting the 90-point quality gate. Final verdict: PASS_WITH_WARNING (score=87). This was a **score-quality issue** (entity naming drift: 2-3 불일치), not a continuity failure. Director found 0 contradictions.

2. **NPC encyclopedia gap**: EP11-EP12 logs show repeated "[V66.1] NPC 프로필/특성 DB 비어있음" and "[V0128] encyclopedia.npcs 누락". The NPC encyclopedia was empty for EP8+ because the Stage 3-only probe doesn't populate it. This caused **degraded validation** ("ConsistencyValidator: 3 checks skipped") — not a continuity failure, but a validation coverage gap.

3. **PinGuard warning at EP10**: "unresolved continuity pins" — advisory only, did not cause REJECT. Suggests some deferred plot elements were not resolved, but without blocking impact.

4. **Persistence layer stasis**: FactLedger, WorldState, and anchors all frozen at EP6 because Stage 3 doesn't update them. This means EP8-EP12 blueprint generation relied on EP6-era state + cumulative bible + entity registry. The system worked, but a full Stage 3+4 run would provide stronger evidence by updating persistence layers at each episode.

### What Was Not Observed

- No EP1 fact contradiction at EP12
- No completed-event reopening
- No ownership/resource loss across the lookback boundary
- No relationship reversal or entity identity drift
- No retry amplification at EP12 (contrast: Window A had 4 attempts at EP5)
- No Stage 3 handoff miss at the lookback boundary

### Key Architectural Insight

**The retrospective validator's 10-episode lookback is not the binding constraint for long-run continuity.** The lookback window limits automated consistency _validation_, but the _generation context_ receives facts from all persistence layers (FactLedger, WorldState, cumulative bible) regardless of the lookback window. EP1 facts survived at EP12 because they are permanently stored in the FactLedger and injected into the LLM context.

The real long-run risk is not "facts fall out of the validator window" but rather:
- Context size growth as FactLedger/WorldState/cumulative bible accumulate (not yet a problem at EP12)
- Anchor pruning for non-critical types after 30 episodes (untested — this is Window C territory)
- LLM attention degradation on very long context (not yet observable at EP12)

### Is Escalation to Window C Justified?

**Not urgently.** Window B showed clean results. The lookback boundary is not the bottleneck. Window C (EP20+) would test context size growth and anchor pruning, but these are lower-risk seams than the arc-boundary hook seam found in Window A. The most impactful next action would be a full Stage 3+4 probe to test whether persistence layers update correctly at longer ranges — but this changes the probe type, not just the window.

## Recommendation

**Stop here for now.** Both windows have been probed:
- Window A (arc boundary): mixed — hook reconciliation costly but persistence held
- Window B (lookback boundary): pass — no degradation, no retry amplification, EP1 facts survived at EP12

The system's long-run continuity is stronger than expected. The dominant weakness is the arc-boundary hook reconciliation cost (Window A), not the lookback boundary. If a next step is desired, a compact survey of the Director's hook-context injection path would be higher value than Window C.

---

## 3-Pass Audit Notes

- Pass 1: probe scope bounded to EP8-EP12 lookback boundary; 5 persistence layers inspected; EP1 fact survival verified through FactLedger, WorldState, and EP12 blueprint content; session log evidence from EP10-EP12 analyzed for contradictions and warnings
- Pass 2: all attempt counts verified from canary summary (5/5 single-attempt); EP12 score=90 confirmed; FactLedger item histories verified from DB; Director contradiction count=0 confirmed from session log; EP11 quality gate friction correctly attributed to score issue, not continuity
- Pass 3: recommendation is singular (stop here); correctly distinguishes lookback boundary (pass) from arc boundary (mixed); no scope creep into Window C or code changes
- Confidence: 97%

---

- Lookback-boundary continuity: **pass** (EP1 facts survived at EP12; 0 contradictions; no retry amplification)
- Best next single move: **stop here** (arc-boundary hook seam from Window A is more impactful than Window C)
- Should Codex open an execution SSOT now: **no**
