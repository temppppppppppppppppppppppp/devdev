# shipbuilding_ocean_heir Block 036 Manual Audit

- Date: 2026-05-01
- Scope: TR Block 036 only
- Source TR: `treatments/shipbuilding_ocean_heir_tr_block_010_draft.json`

## Block

- Block 036: `보험료는 거짓말을 안 한다`
- Episode bundle: 2-6 serialized episodes
- Primary incident: 보험료-정비비 확정 검증권과 중고선 계약금 지급 보류권 확보
- Secondary incident: 보험사의 엔진 정비 이력 공백 할증 가능성 비공식 통보

## Continuity

- Capital before: `해운 투자심사 게이트 설정권과 통제계좌 잉여금 사용 승인권`
- Capital after: `보험료-정비비 확정 검증권과 중고선 계약금 지급 보류권`
- Continuity result: PASS

Block 036 spends Block 035's investment gate by making insurance and maintenance pricing mandatory before deposit release.

## Pacing And Cider

- Same-block cider: PASS
- Pain-only exit: PASS, `false`
- Receipt type: 보류권
- Receipt line: 서준은 보험료-정비비 확정 검증권과 중고선 계약금 지급 보류권을 얻는다.

The block contains a primary hidden-cost verification incident and a separate insurer warning incident.

## Protagonist Logic

- Self-interest and efficiency: PASS
- Moral rescue framing: PASS
- Authority capture: PASS

Seo-jun is not rejecting cheap assets out of caution. He is controlling when cash can leave and which hidden costs must be priced first.

## Regression Control

- Regression type: 회귀
- Knowledge use: 전생에서 보험료 할증과 엔진 오버홀 비용이 뒤늦게 터져 중고선 매입 이익을 지운 기억
- Slip-up control: PASS

The block uses hidden-cost sequence memory without revealing future accident specifics.

## Next Block Ticket

Block 037 should use `보험료-정비비 확정 검증권과 중고선 계약금 지급 보류권` as capital_before. Recommended next battlefield: 브로커 정보 은폐 추적. The primary incident should uncover that the broker omitted a prior repair or inspection note. A secondary incident can be the broker threatening to sell the vessel to Sungjin.

## Verdict

PASS. Block 036 is fit to remain in the source TR sequence.
