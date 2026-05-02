# pharma_cdmo_industry_heir Blocks 031-035 Boundary Audit

work_id: pharma_cdmo_industry_heir
range: B031-B035
scope: material-side TR boundary audit after one-by-one production
verdict: PASS
confidence: 96%

## Source Basis

- `material_ssot` entrypoint and governance were used as the material-side operating standard in this wave.
- Phase0 ARC-04 target: 원료의약품과 정밀화학, B031-B040.
- WorkGuard companion standard: TR before BI, one unit at a time, protagonist benefit must be concrete.
- Current root TR: `treatments/pharma_cdmo_industry_heir_tr_block_070_draft.json`
- Current block files: `treatments/preprocess/pharma_cdmo_industry_heir/03_tr_blocks/block_031` through `block_035`

## Pass 1 - Continuity / Capital / Callback

PASS.

- B031 turns a raw material shortage into 원료 한 드럼 우선 배정권, 90일 창고 슬롯, lot별 품질성적서 사본권, 첫 출고 지시권, 재고담보 사전검토권, and 생산 슬롯 보호 메모.
- B032 spends B031's ownership/storage split by separating patent fear from production planning, then gains 비침해 생산계획 검토권 and 파일럿 배치 2회 우선 슬롯.
- B033 spends B032's route map and B031's warehouse slot by locking A급 중간체 6개월 우선공급권, 가격밴드, 불순물 프로파일, 분할입고권, and 원료재고 담보 term sheet.
- B034 spends B033's intermediate data and B032's pilot slot by forcing 대체 합성 라인 검증권, dual-source 원료 조항, 품질성적서 비교 프로토콜, and 기술이전 폴더 열람권.
- B035 spends B034's quality comparison protocol by turning filter/media scarcity into 12개월 예약 배정권, 2차 공급사 적격성 평가권, 검증자료 사본권, and 멸균 라인 2일 생산 슬롯 보호.
- Capital chain is continuous: each block's `capital_after` equals the next block's `capital_before` across B031->B035.

## Pass 2 - Reward Substance / Same-Block Cider

PASS.

Every block contains at least two event beats, a same-block receipt, and a protagonist gain that changes money, rights, control, or production efficiency.

| Block | Main Pressure | Same-Block Receipt | Concrete Gain |
| --- | --- | --- | --- |
| B031 | API warehouse and raw-material ownership split | `api_warehouse_slot_receipt` | raw-material allocation, warehouse slot, quality-certificate copy rights, first-dispatch rights |
| B032 | patent warning and factory pilot freeze | `non_infringing_production_plan_receipt` | non-infringing production-plan review, pilot-batch slots, QA/legal document access |
| B033 | Chinese intermediate seasonal price shock | `intermediate_priority_supply_price_band_receipt` | intermediate supply priority, price band, impurity-profile submission, inventory financing |
| B034 | Japanese supplier price/certificate hostage | `dual_source_validation_right_receipt` | alternate synthesis validation, dual-source clause, tech-transfer folder access, factory-named pilot report |
| B035 | filter/media shortage and major-client hoarding | `filter_media_reserved_allocation_receipt` | filter/media reserved allocation, second-supplier qualification, validation protocol reuse, sterile-line slot protection |

Specialist terms are not decorative. CDMO/factory slot/quality certification/regulatory/raw material/order/tech transfer/production-right elements all translate into explicit rights or operational controls.

## Pass 3 - Scope / Boundary / UTF-8

PASS.

- No B036+ block file was created.
- No BI was created.
- Root TR now has `_current_block_count: 35`, `_next_block_id: Block 036`, and last block `Block 35`.
- Sequential status is advanced to last pass 35 and next block 36.
- UTF-8 byte-level checks passed on root TR, status JSON, and new B032-B035 fixed JSON files.
- Triple-question placeholder, replacement character, and stray question-mark hygiene checks returned zero on touched JSON files.

## Director Decision

B031-B035 is approved as the first half of ARC-04's raw-material and process-supply escalation. The sequence earns the protagonist recognition in the right way: not by praise alone, but by making him the person who keeps the factory moving when raw materials, patents, intermediate prices, Japanese suppliers, and hidden process consumables each try to stop it.

## Watch For Next Unit

B036 should convert the accumulated QA/validation/clean-process rights into a small chemical factory night-test document win. Cash has stepped down to 4천 8백만 while rights have accumulated, so the next block should either protect cash burn or turn one right into measurable contract leverage.
