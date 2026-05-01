# shipbuilding_ocean_heir Block 040 Manual Audit

- Date: 2026-05-01
- Scope: TR Block 040 only
- Source TR: `treatments/shipbuilding_ocean_heir_tr_block_010_draft.json`

## Block

- Block 040: `안 사는 것도 매입 전략이다`
- Episode bundle: 2-6 serialized episodes
- Primary incident: 중고선 리스크 재가격 기준표와 해운 투자 포기권 확보
- Secondary incident: 성진 계열 해운사의 원 조건 근접 매입 협상 진입

## Continuity

- Capital before: `정비 범위별 재견적권과 매도자 책임 에스크로 요구권`
- Capital after: `중고선 리스크 재가격 기준표와 해운 투자 포기권`
- Continuity result: PASS

Block 040 spends Block 039's repricing and escrow authority by converting the deal into a formal buy/reprice/walk-away standard.

## Pacing And Cider

- Same-block cider: PASS
- Pain-only exit: PASS, `false`
- Receipt type: 포기권
- Receipt line: 서준은 중고선 리스크 재가격 기준표와 해운 투자 포기권을 얻는다.

The block contains a primary repricing/walk-away incident and a separate Sungjin-purchase pressure incident.

## Protagonist Logic

- Self-interest and efficiency: PASS
- Moral rescue framing: PASS
- Authority capture: PASS

Seo-jun does not pass because he is timid. He captures the right to walk away when hidden cost exceeds option value.

## Regression Control

- Regression type: 회귀
- Knowledge use: 전생에서 싸게 산 자산을 포기하지 못해 더 큰 정비비와 보험료를 떠안은 기억
- Slip-up control: PASS

The block uses sunk-cost pattern memory without future loss specifics.

## Next Block Ticket

Block 041 should use `중고선 리스크 재가격 기준표와 해운 투자 포기권` as capital_before. Recommended next battlefield: 성진 매입 리스크의 시장 신호화. The primary incident should turn Sungjin's risky purchase into an external signal without open defamation. A secondary incident can involve an analyst asking why Taesung walked away.

## Verdict

PASS. Block 040 is fit to remain in the source TR sequence. The current 5-block continuation window, Blocks 036-040, is complete.
