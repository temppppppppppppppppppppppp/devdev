# loss_sensing_auditor consistency adversarial 3-pass audit

Date: 2026-05-02
Mode: narrative material-side audit
Focus: consistency first, adversarial stance
Target pair:
- TR: `treatments/loss_sensing_auditor_tr_block_070_draft.json`
- BI: `bible/0_bi_loss_sensing_auditor.json`
- Phase0: `treatments/phase0/loss_sensing_auditor_phase0_design.json`
- work_guard: `work_guards/loss_sensing_auditor.yaml`

## Executive verdict

CONDITIONAL PASS.

The TR+BI pair remains usable and immediate-production-capable when `TR.blocks` / `MasterBible.plot_roadmap` are treated as the runtime SSOT. The spine is strong: 70 blocks, TR-BI roadmap exact sync, block-level cider and authority receipts present, no pain-only block pattern, and Stage0/pair consumability validation already passes.

However, it is not a clean "no-open-consistency-risk" pass. BI still carries a stale Phase0-derived overlay in `MasterBible.HistoricalEvents` and related arc/resource surfaces. This does not break JSON, pair ingestion, or the main plot roadmap, but it can mislead a manuscript/runtime lane if that lane reads `HistoricalEvents` as current arc timing or current resource ladder.

Required classification:
- P0 blockers: 0
- P1 consistency findings: 1
- P2 metadata findings: 1
- Overall: green-plus spine retained, active-baseline cleanliness pending a small BI metadata sync patch

## Evidence snapshot

- Router result: family `blockguide`, stage `complete`, Stage0/Phase0/TR/BI all present, work_guard present, manual audit pass true.
- Pair consumability validator: `tr_consumability=pass`, `bi_standalone_roadmap_readiness=pass`, `pair_consumability=pass`, canonical block count 70.
- Stage0 handoff validator: PASS for `loss_sensing_auditor`.
- UTF-8 hygiene validator: PASS on touched TR/BI/status/audit files.
- TR block list and BI `MasterBible.plot_roadmap`: exact object equality, length 70.
- Block contract scan: all 70 blocks have `genre_ext.block_cider.has_cider=true`, receipt line, `pain_only_exit=false`, primary incident, distinct additional incident, public signboard event, representative reevaluation, and next battlefield ticket.
- BI execution support exists: `ImmediateProductionKit`, `OpeningEpisodeSceneCards`, and `RecognitionRewardCadenceGuide`.

## Pass 1: structural and contract consistency

Verdict: PASS.

Checks:
- TR contains exactly 70 blocks and no B071+ draft.
- BI contains exactly 70 `plot_roadmap` entries.
- TR `blocks` and BI `MasterBible.plot_roadmap` are exact-equal, not merely title-aligned.
- TR `_bi_ref` points to the active BI.
- Stage0/Phase0/work_guard pointers exist and resolve.
- Every block carries same-block reward receipt and no pain-only exit marker.
- Opening macro-battlefield rotation is coherent: seven 10-block macro battlefields.
- Receipt/deal type repetition is not template-collapsed: top receipt/deal types are singletons in the scan.

Adversarial conclusion:
The pair is not a hollow schema pass. The main runtime-consumed TR/BI surfaces are structurally consistent and contain the reward/right-to-act logic demanded by the work_guard.

## Pass 2: source-to-TR-to-BI semantic consistency

Verdict: CONDITIONAL PASS with one P1 issue.

Finding P1: stale Phase0 arc overlay survives inside BI.

Details:
- Phase0 arc windows and resource targets remain visible in BI `MasterBible.HistoricalEvents[0..6]`.
- Current TR/BI portfolio and plot roadmap have evolved to a more granular/compressed ladder:
  - Block 20 current state: 2026년 5월 넷째 주, `Lv5++ 공급망 조건표 승인권...`
  - Block 30 current state: 2026년 6월 말, `Lv7- 고객사 패널티 협상권...`
  - Block 40 current state: 2026년 7월 말, `Lv8- 품질 데이터 표준권...`
  - Block 70 current state: 2028년 4월 중순, `Lv12 그룹 리스크전략실 실권자...`
- But BI `HistoricalEvents` still preserves Phase0-style arc windows/resource targets:
  - ARC-02: `2026년 6월~7월`, `Lv3 -> Lv4 공급망 조건표 + 구매실 공동 veto`
  - ARC-03: `2026년 8월~10월`, `Lv4 -> Lv5 고객사 패널티 협상권 + 에스크로 조항 발동권`
  - ARC-04: `2026년 11월~2027년 1월`, `Lv5 -> Lv6 품질 데이터 표준권 + 시험기관 교차검증권`
  - ARC-07: `2028년 1월~6월`, `Lv8 -> Lv9 그룹 리스크전략실 실권자 + 최종 계약 veto`

Impact:
- If runtime/manuscript generation reads `plot_roadmap`, the pair remains safe.
- If a downstream lane reads `HistoricalEvents` or `WorldState.opponent_transition_plan.resource_target` as the current arc authority, it may generate outdated time windows and weaker level labels than the TR/BI portfolio currently promises.

Judgment:
This is not a P0 because the plot roadmap is exact and the production-critical block content is coherent. It is P1 because BI contains two competing arc/resource ladders.

Finding P2: BI `MetaInfo.episodes_per_arc` is misleading.

Details:
- `MetaInfo.total_episodes=350` is compatible with 70 TR blocks at a 5-episode average.
- `MetaInfo.episodes_per_arc=5` is not literally compatible with seven 10-block arcs. If interpreted literally, each arc would be only 5 episodes; the intended meaning appears closer to per-block average.

Impact:
- Low immediate risk if ignored by runtime.
- Medium editorial confusion risk if a manuscript lane uses it for arc pacing.

## Pass 3: runtime handoff and webnovel payoff consistency

Verdict: PASS with P1 watch inherited from Pass 2.

Checks:
- work_guard core promise is honored: loss sensing, responsibility attribution, public proof, private receipt, observer shift, and next gate are visible.
- Rewards are rights/access/control, not praise-only: audit hold, data room, CEO CC, TF management, joint veto, escrow, quality data standard, board dashboard, final condition-table veto.
- Defeat/cost blocks convert loss into retained right or next-gate leverage.
- Early opening is sceneable: BI has 10 opening scene cards covering EP01-EP05 with pressure, Taejun move, proof object, and payoff.
- Recognition/reward cadence is explicitly documented for manuscript endings.

Adversarial conclusion:
The main story engine is consistent enough for immediate manuscript work. The only serious consistency risk is not story logic collapse but metadata authority drift: stale Phase0/HistoricalEvents surfaces should be synchronized before calling the pair a clean active-baseline candidate.

## Recommended bounded repair

Do not rewrite TR.

Minimal BI-only repair:
1. Update `MasterBible.HistoricalEvents[0..6].time_window` to match current TR/portfolio arc timing.
2. Update `MasterBible.HistoricalEvents[0..6].resource_target` and `WorldState.opponent_transition_plan[*].resource_target` to the current TR/portfolio level ladder.
3. Clarify `ProjectData.MetaInfo.episodes_per_arc`: either change it to the literal current arc estimate or add an explicit per-block-average field and keep legacy compatibility.

After repair, rerun:
- JSON parse for BI
- `check_bi_tr_consumability.py`
- `stage0_handoff_validator.py`
- `check_utf8_hygiene.py`
- one short LLM re-audit focused only on stale overlay closure

## Final 3-pass decision

The pair passes immediate production spine consistency.

It does not pass "perfect metadata consistency" because BI contains stale Phase0 arc/resource overlays beside the current TR-derived roadmap and portfolio ladder.

Final label:
`GREEN PLUS / IMMEDIATE-PRODUCTION CAPABLE / CONSISTENCY CLEANUP REQUIRED BEFORE ACTIVE-BASELINE CLAIM`
