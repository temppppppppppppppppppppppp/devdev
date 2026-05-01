# shipbuilding_ocean_heir Block 035 Manual Audit

- Date: 2026-05-01
- Scope: TR Block 035 only
- Source TR: `treatments/shipbuilding_ocean_heir_tr_block_010_draft.json`

## Block

- Block 035: `싼 배가 제일 비싸다`
- Episode bundle: 2-6 serialized episodes
- Primary incident: 해운 투자심사 게이트 설정권과 통제계좌 잉여금 사용 승인권 확보
- Secondary incident: 중고선 검사 보고서의 엔진 정비 이력 공백과 보험료 재산정 가능성 발견

## Continuity

- Capital before: `해운 통제계좌 설계권과 운임 수입 우선배분권`
- Capital after: `해운 투자심사 게이트 설정권과 통제계좌 잉여금 사용 승인권`
- Continuity result: PASS

Block 035 spends Block 034's freight-allocation authority by gating use of freight-account surplus for shipping investments.

## Pacing And Cider

- Same-block cider: PASS
- Pain-only exit: PASS, `false`
- Receipt type: 승인권
- Receipt line: 서준은 해운 투자심사 게이트 설정권과 통제계좌 잉여금 사용 승인권을 얻는다.

The block has a primary shipping investment gate incident and a separate inspection/insurance risk incident.

## Protagonist Logic

- Self-interest and efficiency: PASS
- Moral rescue framing: PASS
- Authority capture: PASS

Seo-jun does not reject cheap assets by instinct. He forces hidden maintenance and insurance costs through an approval gate before cash can leave.

## Regression Control

- Regression type: 회귀
- Knowledge use: 전생에서 싼 중고선 매입 뒤 정비비와 보험료가 운임 수익을 잠식한 기억
- Slip-up control: PASS

The block uses remembered risk structure without naming a future vessel accident.

## Next Block Ticket

Block 036 should use `해운 투자심사 게이트 설정권과 통제계좌 잉여금 사용 승인권` as capital_before. Recommended next battlefield: 보험사와 정비 이력 검증. The primary incident should force the insurer and maintenance yard to price the hidden risk before any deposit. A secondary incident can involve the broker threatening to sell the vessel to Sungjin.

## Verdict

PASS. Block 035 is fit to remain in the source TR sequence. The current 5-block continuation window, Blocks 031-035, is complete.
