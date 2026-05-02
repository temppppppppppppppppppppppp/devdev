# ARC-03 Blocks 021-030 10-Block Adversarial Audit

work_id: `distressed_company_buyer`
scope: `Block 021` through `Block 030`
arc: `ARC-03 - 급식 계약은 느리게 끊기지 않는다`
verdict: `PASS`

## Pass 1 - Pacing And Incident Density

Verdict: `PASS`.

Each block functions as a 2-6 episode bundle rather than a single scene. Every block contains at least two distinct incident beats, a pressure turn, and a same-block receipt.

- `Block 021`: 위생점수/빈 식판/영업정지 압박 -> 48시간 grace, 재점검 접수번호, 3일 임시 배식 유지.
- `Block 022`: 공급사 계정 동결/연대보증 요구 -> 2주 공동구매 코드, 단가표 lock, 과거채무 비인수.
- `Block 023`: 학교 월요일 공백/교육청/명성급식 독점 제안 -> 580식 제한 납품, 4주 PO, 교육청 접수번호.
- `Block 024`: 병원 샘플 5종 전부 반려/위생 grace 공격 -> 4종 포기, 1종 시험식 approval, 병동 제한 검수표.
- `Block 025`: 은행 운전자금 반려/미수금 장부 오염 -> lockbox, factoring 예비 term sheet, advance 제외표.
- `Block 026`: 내부정보 프레임/책임불명확 심사 -> 제한입찰 참석권, 회의록 첨부 공개 receipt, 책임 순서표.
- `Block 027`: 공동구매 계정 재동결/대표 개인보증 요구 -> SPV 구매대행 코드, margin cap, 공급사 확인서.
- `Block 028`: 재고 떠넘기기/조리일지 소급 작성 유혹/익명 제보 -> 폐기 확인서, lot 추적표, 시정명령 종결 접수.
- `Block 029`: 전체 한도 재반려/급여 지급 압박 -> 소액 운전자금 한도, 급여 지급 안정 receipt, 대표 개인 인출 금지.
- `Block 030`: 급식 route 복귀 빈 차/리턴브릿지 폐업 압박 -> reverse-pickup pilot, seller data-room, warehouse option.

Adversarial challenge: `정식 승인 실패 후 제한권 확보`가 ARC 중반에 반복된다. 현재는 위생, 구매, 학교, 병원, 금융, 입찰, 공급사, 점검, 운전자금, 반품 gate로 대상이 충분히 바뀌어 단조롭지는 않다. 단, ARC-04에서는 보상 형태를 `승인권`만이 아니라 `data extraction`, `penalty hold`, `insurance claim`, `chargeback`, `warehouse option`, `seller ROFR`처럼 더 넓혀야 한다.

## Pass 2 - Protagonist Self-Interest And Efficiency

Verdict: `PASS`.

도윤의 선택은 선의가 아니라 이득, 효율, 법적 방어, 다음 gate 장악으로 작동한다. 그는 반복적으로 회사를 통째로 구하지 않고 살아 있는 권리만 산다.

- 빚 대신 현재 주문권을 산다: `Block 022`, `Block 027`.
- 전량 공급 대신 책임이 좁은 제한 공급을 고른다: `Block 023`, `Block 024`.
- 장부 전체 대신 회수 가능한 채권 순서만 금융화한다: `Block 025`, `Block 029`.
- 대표와 기존 운영진의 감정 요구를 자른다: `Block 021`, `Block 028`, `Block 029`.
- 급식 회생을 종착지로 보지 않고 다음 부도 회사의 data-room gate로 쓴다: `Block 030`.

Adversarial challenge: 독자가 도윤을 착한 구조조정 실사관으로 오독할 여지는 낮다. 각 block의 reward 문장이 대체로 "살린 게 아니다", "통째로 산 게 아니다", "큰 돈을 얻지 못했다" 식으로 효율 중심을 재확인한다. 이후에도 도윤이 손실을 떠안을 때는 반드시 `권리`, `우선권`, `data`, `입금 경로`, `법적 clean receipt` 중 하나로 즉시 환전해야 한다.

## Pass 3 - Proxy Satisfaction And Reward Receipts

Verdict: `PASS`.

대리만족 구조는 추상적 성공보다 서류, 번호, 권리, 계좌, 한도, option 같은 눈에 보이는 receipt로 닫힌다.

- `021`: 재점검 접수번호와 3일 임시 배식 유지.
- `022`: 공동구매 코드와 단가표 lock.
- `023`: 4주 제한 PO와 첫 주 선입금.
- `024`: 병원식 1종 시험식 approval과 영양성분 분석 접수번호.
- `025`: lockbox 계좌와 factoring 예비 term sheet.
- `026`: 제한입찰 참석권과 회의록 첨부 receipt.
- `027`: 3개 사업장 SPV 구매대행 코드와 margin cap.
- `028`: 폐기 확인서, lot 추적표, 시정명령 종결 접수.
- `029`: 소액 운전자금 한도와 급여 지급 안정 receipt.
- `030`: 1주 reverse-pickup pilot, seller data-room, warehouse option, 첫날 43박스 회수 log.

Adversarial challenge: 보상 크기는 일부러 작게 제한되어 있다. 이것은 장르 보상감이 약해질 수 있는 위험이지만, 각 보상이 다음 block의 레버리지로 즉시 회수되므로 현재는 허용된다. ARC-04에서는 `돈이 찍히는 순간`과 `상대가 권리를 빼앗기는 순간`을 더 자주 전면화해야 대리만족이 상승한다.

## Legal And Continuity Check

Verdict: `PASS`.

No block relies on hidden fraud, retroactive log writing, or magically erased debt. The arc repeatedly preserves legal cleanliness through non-assumption confirmations, public receipt dates, external filing numbers, lockbox flows, disposal photos, and omission acknowledgements.

Continuity also passes. `Block 021` starts from the `Block 020` data-room and emergency substitute PO. `Block 030` cleanly exits ARC-03 by converting stabilized cafeteria route time into ARC-04 reverse-logistics data-room access.

## Residual Watchlist

- ARC-04 should not overuse "full approval failed, limited approval obtained" as the only reward rhythm.
- 해문푸드서비스 대표의 통제권 불만 should return as a pressure source, not disappear.
- 은성재활병원 trial SKU is still not monetized. Later blocks should either harvest the 검수표 or explicitly mark it as deferred value.
- 명성급식 remains active. A later stronger counterattack should exploit their 독점/내부정보 frame rather than leaving them as background pressure only.
- Block 031 should open with ReturnBridge seller data-room triage, not a generic delivery scene. The receipt target should be `seller-by-seller return volume`, `inspection delay pattern`, `platform penalty exposure`, and `2-day field-audit access`.

## Final Gate

`Blocks 021-030` pass the 10-block gate. Proceed to `Block 031` as the next production unit. BI remains gated until the source TR reaches the required handoff shape.
