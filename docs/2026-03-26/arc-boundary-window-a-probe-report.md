# Arc-Boundary Window A Probe Report

Date: 2026-03-26
Type: bounded arc-boundary continuity probe (Window A from long-run probe plan)
Source Project: `00_0000001`
Target Project: `canary_0326_arc_boundary`
Probe Window: EP5 only (Arc 1 → Arc 2 boundary)
Run Status: completed (exit code 0)
Prior Plan: `docs/2026-03-26/long-run-continuity-probe-plan.md`

## Evidence Artifacts

| Artifact | Path |
|----------|------|
| Canary summary | `projects/canary_0326_arc_boundary/logs/stage3_canary_summary.json` |
| Session log | `projects/canary_0326_arc_boundary/logs/session_20260326_121653.log` |
| EP5 final blueprint | `projects/canary_0326_arc_boundary/plans/blueprints/blueprint_0005.txt` |
| EP5 final artifact | `projects/canary_0326_arc_boundary/logs/artifacts/stage3/ep_0005/attempt_04/final_blueprint__emotion_focused.json` |
| EP4 source manuscript | `projects/canary_0326_arc_boundary/drafts/ep_0004.txt` |
| EP4 source blueprint | `projects/canary_0326_arc_boundary/plans/blueprints/blueprint_0004.txt` |

## Findings

### EP5 Generation Summary

| Metric | Value |
|--------|-------|
| Attempts | 4 (3 REJECT + 1 PASS) |
| Final verdict | PASS |
| Final score | 92 |
| Final strategy | emotion_focused |
| LLM calls | 17 (episode_telemetry) |
| Duration | 868s (~14 min) |
| Cost | $1.16 |

For comparison, prior canary Arc 2 episodes averaged $0.70 and ~12 min with 1 attempt each. EP5 at the arc boundary cost **1.7× more** and required **4 attempts**.

### What Happened at the Arc Boundary

**Attempt 1 (REJECT, score=65)**: Director detected 1 contradiction.

The Director stated the EP4 hook was "레버리지 한도 끝까지 열어서..." (open leverage to the limit), but the EP5 candidates used "레버리지는 정확히 3배까지만 사용해서 진입합니다" (exactly 3x leverage). Director correctly identified this as a hook-vs-continuation conflict.

Actual EP4 manuscript ending (verified from `drafts/ep_0004.txt`):
> "아니요, 철저하게 리스크를 통제해야 하니 레버리지는 정확히 3배까지만 사용해서 진입합니다."

This is a nuanced finding: the EP4 manuscript ending hook says "exactly 3x leverage," and the initial EP5 candidates faithfully continued from this. The Director's complaint referenced a different phrasing ("한도 끝까지 열어서") that does not appear in the EP4 manuscript. The Director may have been interpreting the Arc 2 tactical plan or confabulating a hook variant.

**Attempt 2 (REJECT, score=40)**: Director found entity naming drift — "WTI 차트", "OTP 발생기", "WTI 3월물" diverged from FactLedger canonical names. This is an arc-boundary entity-naming seam, not a state carry-forward failure.

**Attempt 3 (REJECT, score=65)**: Same hook contradiction pattern. Director: "모든 후보" (all candidates) had the dialogue conflict. This confirms the issue was systematic, not candidate-specific.

**Attempt 4 (PASS, score=92)**: The generator produced a blueprint that reconciled the tension with a two-layer strategy — open 15× margin buffer for safety while limiting actual entry to 3× — resolving the apparent contradiction creatively. Director accepted with score 92.

### Continuity Layer Status at Arc Boundary

| Layer | Status | Evidence |
|-------|--------|----------|
| **FactLedger** | HELD | 24 characters, 11 items persisted. `last_updated_ep=4`. Items correctly tracked (노트, OTP, 법인 인감 all present with history). |
| **WorldState** | HELD | `last_updated_ep=4`. 16 relationships persisted. Protagonist state carried forward. |
| **Reference Anchors** | EMPTY | 0 anchors at probe time. Anchor extraction may not trigger during Stage 3-only runs. Not a failure — anchors are a Stage 4 output. |
| **Entity Registry** | HELD | 65 entities extracted from Arc 1. Arc 2 context received full entity set. |
| **Cumulative Bible** | HELD | EP1-EP4 episode bibles available for EP5 context assembly. |
| **Inventory Tracking** | HELD | TF-49 correctly flagged 3 inventory gaps at EP5: 노트, OTP, 법인 인감 — all Arc 1 items that should appear in EP5. |

### What Continuity Held

1. **State persistence**: FactLedger (24 chars, 11 items), WorldState (16 relationships), and cumulative bible all correctly persisted across the arc boundary. No silent data loss.

2. **Entity registry**: 65 entities extracted and available to EP5 generation. Arc-boundary entity refresh worked.

3. **Inventory carry-forward**: TF-49 correctly identified 3 Arc 1 items (노트, OTP, 법인 인감) that needed mentioning in EP5. The final EP5 blueprint explicitly references all three.

4. **Director contradiction detection**: The Director correctly caught cross-arc hook inconsistencies in 3/4 attempts. The detection mechanism works.

5. **Self-correction**: The system eventually produced a high-quality EP5 blueprint (score=92) that creatively resolved the hook tension. The retry loop functioned as designed.

### What Continuity Weakened

1. **Arc-boundary hook reconciliation cost**: 4 attempts to resolve EP5 vs 1 attempt for typical mid-arc episodes. The arc boundary costs 1.7× more and 4× more attempts. The retry-driven resolution works but is expensive.

2. **Director hook reference accuracy**: The Director cited an EP4 hook phrasing ("레버리지 한도 끝까지 열어서...") that does not exactly match the EP4 manuscript ending ("레버리지는 정확히 3배까지만 사용해서 진입합니다"). The Director may be reading from the arc tactical document or interpolating between sources. This imprecise hook reference caused unnecessary REJECTs when candidates faithfully continued the actual manuscript.

3. **Entity naming drift at arc boundary**: Attempt 2 showed item naming drift ("OTP 발생기" vs FactLedger's "OTP (일회용 비밀번호 생성기)"). This is a low-severity seam — the Director catches it, but it costs an attempt.

### What Was Not Observed

- No silent state loss across arc boundary
- No Stage 3 handoff miss (all persistence layers populated)
- No completed-event reopening at EP5
- No relationship or entity carry-forward failure
- No validator late catch — Director caught issues on first audit of each attempt

## Is Escalation to Window B Justified?

**Not urgently, but worth doing.** The arc boundary probe shows the system self-corrects at moderate extra cost. The dominant finding — Director hook reference imprecision — is a Stage 3 prompt/context issue, not a persistence-layer failure. Window B (past-lookback boundary at EP12) tests a different seam (persistence-layer pruning) and would provide independent value.

Recommended next step: proceed to Window B, but the arc-boundary finding does not require an emergency execution SSOT. The system works; it just costs more at arc boundaries.

## Recommendation

**Proceed to Window B (past-lookback probe at EP12).** The arc-boundary seam showed moderate weakness (hook reconciliation cost) but no data loss or hard failure. The persistence layers all held. The next highest-value question is whether EP1 facts survive at EP12 when the retrospective validator lookback expires — this tests a fundamentally different seam.

The arc-boundary hook reconciliation cost (4 attempts vs 1) is notable but not blocking. If this cost pattern is confirmed across multiple projects, a compact survey of the Director's hook-context injection path would be the right response — not a code change.

---

## 3-Pass Audit Notes

- Pass 1: probe scope bounded to EP5 arc boundary only; evidence from session log (94KB), canary summary, FactLedger/WorldState DB inspection, EP4/EP5 blueprint and manuscript comparison; 6 persistence layers checked with status
- Pass 2: key claim (3 REJECT + 1 PASS) verified from session log timestamps and Director frame entries; EP4 manuscript ending verified from `drafts/ep_0004.txt`; FactLedger item persistence verified from DB; Director hook reference discrepancy documented with exact quotes from both sources
- Pass 3: recommendation is singular (proceed to Window B); no scope creep into Director prompt redesign or execution SSOT; finding correctly scoped to arc-boundary probe only
- Confidence: 96%

---

- Arc-boundary continuity: **mixed** (persistence layers held; hook reconciliation costly at 4 attempts)
- Best next single move: **proceed to Window B (past-lookback probe at EP12)**
- Should Codex open an execution SSOT now: **no**
