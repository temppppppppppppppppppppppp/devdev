# BI/TR/GUARD Bridge: chaebol3_sector_rotation_successor

Date: 2026-05-17
Status: candidate bridge ready, work_guard WG-V1 PASS, WG-V2 manual PASS_FOR_DRAFT, Phase0-not-ready, TR/BI-not-generated
Issue: #157

## 0. Purpose

This file turns the current selection-ready candidate into a material-side bridge that can feed both:

- Geuldobi material flow: `work_guard -> Phase0 -> TR -> BI`
- Firefly mainline: `S2 -> S3 -> S4`, especially S4 scene context

This is not a 70-block TR.
This is not a production BI.
This is the missing middle layer: the material must become scene-native before full expansion.

## 1. Authority Inputs

- canon candidate:
  - `material_ssot/20_pitch/canon/chaebol3_sector_rotation_successor.md`
- working synthesis:
  - `material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_working_synthesis.md`
- Firefly handoff seed:
  - `material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_firefly_integration_handoff.md`
- guard draft:
  - `material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_work_guard_draft_v1.yaml`
- International Group guard draft v2:
  - `material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_work_guard_draft_v2.yaml`
- partial Phase0 opening-bundle draft:
  - `treatments/phase0/chaebol3_sector_rotation_successor_phase0_opening_bundle_draft_v1.json`
- full Planning / Phase0 draft:
  - `treatments/phase0/chaebol3_sector_rotation_successor_phase0_design_draft_v1.json`
- EP001-EP003 S4 canary packet:
  - `material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_ep001_003_s4_canary_packet_v1.md`
  - local working copy: `treatments/episode_packets/chaebol3_sector_rotation_successor/ep001_003_s4_canary_packet_v1.md`
- EP001-EP003 packet audit:
  - `material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_ep001_003_s4_canary_packet_3pass_audit.md`
  - local working copy: `treatments/audit_reports/chaebol3_sector_rotation_successor_ep001_003_s4_canary_packet_3pass_audit.md`
- pre-70 planning decision:
  - `material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_pre70_planning_decision_v1.md`
- post-canary International Group opportunity atlas:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/70_international_group_historical_opportunity_atlas_v1.md`
- post-canary International Group sector gate matrix:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/71_international_group_sector_gate_matrix_v1.md`
- post-canary Arc 01-02 research checklist:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/72_international_group_phase0_research_checklist_arcs01_02_v1.md`
- post-canary opening Phase0 seed:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/73_international_group_opening_phase0_seed_v1.md`
- post-canary 3-pass adversarial audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/74_international_group_opening_phase0_seed_3pass_adversarial_audit_v1.md`
- post-canary EP001 micro-canary packet:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/75_international_group_ep001_micro_canary_packet_v1.md`
- final sanity check:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/76_final_sanity_check_20260517.md`
- vicarious satisfaction pacing audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/77_vicarious_satisfaction_pacing_audit_v1.md`
- International Group EP001 micro-canary sample:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/78_international_group_ep001_micro_canary_sample_v1.md`
- International Group EP001 micro-canary director audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/79_international_group_ep001_micro_canary_director_audit_v1.md`
- International Group work_guard v2 adversarial audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/80_international_group_work_guard_v2_adversarial_audit_v1.md`
- International Group Phase0 restart v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/81_international_group_phase0_restart_v1.md`
- International Group Phase0 restart adversarial audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/82_international_group_phase0_restart_adversarial_audit_v1.md`
- International Group Arc 01 scene-ready packet:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/83_international_group_arc01_scene_ready_packet_v1.md`
- International Group Arc 01 scene-ready packet adversarial audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/84_international_group_arc01_scene_ready_packet_adversarial_audit_v1.md`
- International Group TR 1-10 planning draft:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/85_international_group_tr01_10_planning_draft_v1.md`
- International Group TR 1-10 planning draft adversarial audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/86_international_group_tr01_10_planning_adversarial_audit_v1.md`
- International Group EP001-EP003 S4 compact writer seed:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/87_international_group_ep001_003_s4_compact_writer_seed_v1.md`
- International Group EP001-EP003 S4 compact writer seed audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/88_international_group_ep001_003_s4_compact_writer_seed_audit_v1.md`
- International Group EP001 S4 canary sample v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/89_international_group_ep001_s4_canary_sample_v1.md`
- International Group EP001 S4 canary sample v1 audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/91_international_group_ep001_s4_canary_audit_v1.md`
- International Group EP001 S4 canary sample v2:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/92_international_group_ep001_s4_canary_sample_v2.md`
- International Group EP001 S4 canary sample v2 audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/93_international_group_ep001_s4_canary_sample_v2_audit.md`
- International Group EP002 S4 canary sample v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/94_international_group_ep002_s4_canary_sample_v1.md`
- International Group EP002 S4 canary sample v1 audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/95_international_group_ep002_s4_canary_audit_v1.md`
- International Group EP003 S4 canary sample v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/96_international_group_ep003_s4_canary_sample_v1.md`
- International Group EP003 S4 canary sample v1 audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/97_international_group_ep003_s4_canary_audit_v1.md`
- International Group EP001-EP003 opening ladder synthesis:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/98_international_group_ep001_003_opening_ladder_synthesis_v1.md`
- International Group EP001-EP003 opening ladder adversarial audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/99_international_group_ep001_003_opening_ladder_adversarial_audit_v1.md`
- International Group TR01-10 first-tranche handoff:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/100_international_group_tr01_10_first_tranche_handoff_v1.md`
- International Group TR01-10 first-tranche handoff audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/101_international_group_tr01_10_first_tranche_handoff_audit_v1.md`
- International Group EP004/B5 S4 canary sample v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/102_international_group_ep004_b5_s4_canary_sample_v1.md`
- International Group EP004/B5 S4 canary audit v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/103_international_group_ep004_b5_s4_canary_audit_v1.md`
- International Group EP005/B6 S4 canary sample v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/104_international_group_ep005_b6_s4_canary_sample_v1.md`
- International Group EP005/B6 S4 canary audit v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/105_international_group_ep005_b6_s4_canary_audit_v1.md`
- International Group EP006/B7 S4 canary sample v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/106_international_group_ep006_b7_s4_canary_sample_v1.md`
- International Group EP006/B7 S4 canary audit v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/107_international_group_ep006_b7_s4_canary_audit_v1.md`
- International Group EP007/B8 S4 canary sample v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/108_international_group_ep007_b8_s4_canary_sample_v1.md`
- International Group EP007/B8 S4 canary audit v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/109_international_group_ep007_b8_s4_canary_audit_v1.md`
- International Group EP008-009/B9 S4 canary sample v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/110_international_group_ep008_009_b9_s4_canary_sample_v1.md`
- International Group EP008-009/B9 S4 canary audit v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/111_international_group_ep008_009_b9_s4_canary_audit_v1.md`
- International Group EP009-010/B10 S4 canary sample v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/112_international_group_ep009_010_b10_s4_canary_sample_v1.md`
- International Group EP009-010/B10 S4 canary audit v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/113_international_group_ep009_010_b10_s4_canary_audit_v1.md`
- International Group first-tranche synthesis 102-113 v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/114_international_group_first_tranche_synthesis_102_113_v1.md`
- International Group first-tranche synthesis audit v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/115_international_group_first_tranche_synthesis_audit_v1.md`
- International Group EP004-010 S4 compact handoff v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/116_international_group_ep004_010_s4_compact_handoff_v1.md`
- International Group EP004-010 S4 compact handoff audit v1:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/117_international_group_ep004_010_s4_compact_handoff_audit_v1.md`
- International Group EP009-010 finance/file-room S4 smoke final audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/121_international_group_ep009_010_s4_context_smoke_final_audit_v1.md`
- International Group EP006 product-hand S4 smoke reaudit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/124_international_group_ep006_product_hand_s4_context_smoke_reaudit_v1.md`
- Firefly-side research dryrun plan/audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/125_firefly_side_research_dryrun_plan_v1.md`
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/126_firefly_side_research_dryrun_plan_audit_v1.md`
- EP007 buyer-desk file-only dryrun final audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/129_ep007_buyer_desk_file_only_dryrun_final_audit_v1.md`
- Firefly S4 Writer Context integration contract/audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/130_firefly_s4_writer_context_integration_contract_v1.md`
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/131_firefly_s4_writer_context_integration_contract_audit_v1.md`
- EP007 buyer-desk S4 Writer Context fill sample/audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/132_ep007_buyer_desk_s4_writer_context_fill_sample_v1.json`
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/133_ep007_buyer_desk_s4_writer_context_fill_sample_audit_v1.md`
- material-to-S4 reusable template/audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/134_material_to_s4_context_reusable_template_v1.md`
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/135_material_to_s4_context_reusable_template_audit_v1.md`
- EP007 buyer-desk file-only prose dryrun from S4 context/audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/136_ep007_buyer_desk_file_only_prose_dryrun_from_s4_context_v1.md`
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/137_ep007_buyer_desk_file_only_prose_dryrun_audit_v1.md`
- EP006 product-hand template-driven file-only prose dryrun/audit:
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/138_ep006_product_hand_template_driven_file_only_prose_dryrun_v1.md`
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/139_ep006_product_hand_template_driven_file_only_prose_dryrun_audit_v1.md`
- Firefly material-to-S4 context bridge governance/audit:
  - `material_ssot/00_governance/firefly-material-to-s4-context-bridge-harness-v1.md`
  - `material_ssot/10_research/30_work_materials/chaebol3_sector_rotation_successor/140_material_to_s4_context_bridge_harness_capture_audit_v1.md`
- bridge harness:
  - `material_ssot/00_governance/firefly-s4-scene-native-material-bridge-v1.md`
- B1-B2 micro-canary before 70 harness:
  - `material_ssot/00_governance/firefly-b1-b2-micro-canary-before-70-harness-v1.md`

## 2. Material Truth To Preserve

Current planning truth:

> If the canary passes, this becomes an International Group-inspired 1984-85 collapse/restoration work: a weak but legitimate grandson returns before the group is destroyed by grandfather's fatal judgment, his father's old accident death leaves him isolated, and he rebuilds the family name through sector gates until the Korean group becomes a world-top industrial-investment group.

Canary exception:

- The existing 2008 liquidity/NDF opening packet remains useful only as a scene-engine canary.
- It is not the post-canary planning baseline.

The work is still not "a clever rich kid makes investments."

Do not let later BI/TR flatten this into:

- market prediction parade;
- family-meeting lecture;
- lucky investment fantasy;
- humiliation-only grandson opening;
- broad sector encyclopedia.

## 3. Work Guard Translation Lock

The legacy `work_guard_draft_v1` compresses the old 2008/NDF opening-engine candidate.

For the current International Group baseline, `work_guard_draft_v2` supersedes v1.

Current v2 runtime doctrine:

- 문도윤 is a fatherless direct-line grandson, not a self-made outsider and not a generic repentant wastrel;
- first reward is procedure/access movement before money: memo route, stamp delay, chair, telex access, bank question;
- LC buys only time, never group rescue;
- bank/secretary/grandfather move because of responsibility, exposure, face, and condition, not trust;
- every later sector must rotate room, resistant actor, proof object, human cost, and authority reward;
- Firefly S4 receives compact scene-native payload, not the full canon/guard packet.

This is why the next step is not immediate 70-block generation.

The binding harness is now stricter: no production TR70, production BI, final Phase0 declaration, or immediate-use/range-complete claim until B1-B2 or EP001 has passed a Firefly/S4 micro-canary and director readback.

The guard must first pass:

```powershell
python -X utf8 scripts/run_work_guard_v1.py --path material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_work_guard_draft_v2.yaml
```

Then the operator should run WG-V2 manual audit before freezing or publishing it into `work_guards/`.

## 4. TR / Phase0 Intake Contract

When this candidate enters Phase0/TR, each planning bundle must carry scene-native handoff semantics.

Required per bundle:

- expected published episode range;
- inherited reward or opening pressure;
- room/surface where the pressure is visible;
- human cost;
- rational resisting actor;
- narrow protagonist action;
- visible object/access change;
- money/info-to-authority conversion;
- next named gate.

If a bundle cannot answer those, it is not ready for TR expansion.

## 5. Opening Bundle Bridge

The opening bundle is the canary. If this fails, the full material will fail.

| Unit | Function | Scene-native handoff | Required receipt |
|---|---|---|---|
| B1 | return price tag only | speed-storage room, unpaid care text, liquidation report, wrist/date mismatch | regression ignition only |
| B2 | first proof | foundation reception desk, VIP file, interpretation brief, secretary protecting event risk | secretary changes route/envelope and moves memo to top of file |
| B3 | conditioned access | chairman room, limited account memo, staff interview list, report condition | 30-day account, 3 staff interviews, weekly report |
| B4 | helper by contract | rejected overseas bond report, resignation interview calendar, messenger thread | analyst delays resignation and joins trial cell under loss/bonus/NDA terms |
| B5 | price becomes tradable | temporary investment room, external bank quote, NDF condition sheet | external quote and executable terms prove the judgment |
| B6 | money converts to authority | settlement call, clearing statement, bonus transfer, audit schedule, logistics collateral file | bonus, team attitude shift, audit badge, next sector file time |

Opening pacing:

- recommended published episodes: 4
- acceptable range: 3~5
- hard watch: proof/receipt/next gate cannot land after episode 5

## 6. First-Block Cider Ledger

This section repeats the validator-facing opening ledger in bridge form. The ledger is still upstream material, not S4 prose.

- block_no: 2
  has_cider: true
  same_block_receipt: 비서실장이 주인공의 메모 때문에 VIP 동선과 브리프 봉투를 바꾸고, 행사 파일 상단에 그 메모를 올린다.
  receipt_kind: evaluation_revision_and_access_route
  bridge_or_payback_note: 칭찬이 아니라 파일 위치와 동선 변경으로 첫 평가 수정이 보인다.

- block_no: 3
  has_cider: true
  same_block_receipt: 회장이 30일 제한 관찰 계좌, 직원 3명 면담권, 주간 보고 조건을 붙인 메모를 준다.
  receipt_kind: conditioned_seed_capital_and_staff_access
  bridge_or_payback_note: 권한은 공짜 인정이 아니라 제한, 보고, 손실조건이 붙은 시험권으로 열린다.

- block_no: 4
  has_cider: true
  same_block_receipt: 주인공이 밀려난 금융 인재를 손실 보전, 성과 보너스, 비공개 조건으로 묶어 시험 팀에 들인다.
  receipt_kind: transactional_helper_acquisition
  bridge_or_payback_note: 조력자는 감화가 아니라 커리어 리스크와 보상 조건 때문에 붙는다.

- block_no: 5
  has_cider: true
  same_block_receipt: 외부 은행 quote와 작은 NDF 조건이 붙으며 주인공의 달러 유동성 판단이 거래 가능한 가격표로 검증된다.
  receipt_kind: external_price_and_tradeability_proof
  bridge_or_payback_note: 미래 설명이 아니라 margin, maturity, custody 조건이 판단을 가격으로 만든다.

- block_no: 6
  has_cider: true
  same_block_receipt: 첫 청산 명세, 보너스 이체 확인, 팀의 태도 변화가 같은 블록 안에서 붙고, 주인공은 계열사 헤지 손실 감사 참석권과 물류 담보 파일 열람 시간을 받는다.
  receipt_kind: money_to_team_loyalty_to_authority_token
  pain_only_exit: false
  bridge_or_payback_note: 돈은 최종 자랑이 아니라 팀 충성, 감사 접근권, 다음 섹터 파일로 환전된다.

## 7. BI Amplification Contract

BI may deepen the material but must preserve the following:

- first 300-500 characters show where the protagonist is, what he is doing, and why it costs him personally;
- regression ignition uses body, object, date, debt, and report surface before future-knowledge explanation;
- protagonist weapon appears through current data handling, not omniscient briefing;
- opening reward is evaluation/access movement before money;
- each reward is translated into file, account, team, badge, meeting, or next file;
- later sector rotation is not "same meeting, new industry";
- family authority is earned by proof and condition, not gifted recognition.

BI should carry an explicit downstream handoff pack equivalent to:

- `opening_bundle_seed`
- `authority_ladder`
- `sector_rotation_surface_rules`
- `forbidden_flattenings`
- `s4_scene_native_handoff`

## 8. TR Expansion Stop Conditions

Do not generate 70 blocks while any of these remain open:

- final title not locked;
- protagonist name/personality surface not finally locked;
- family tree and successor ladder not made;
- antagonist/opponent ladder not made;
- 1984-1988 first macro calendar and historical sector gate map not made;
- source-safety watch not rechecked;
- work_guard draft not WG-V1 PASS and WG-V2 PASS;
- Phase0 design not written;
- opening bundle not proven scene-native in a Firefly S4 dry run.

This candidate is close enough to build from, but not ready for full range.

## 9. Readiness Declaration

- selection-ready: yes
- guard-draft-created: yes
- work_guard_v1_result: PASS on 2026-05-17
- work_guard_v2_manual_result: PASS_FOR_DRAFT on 2026-05-17
- international_group_work_guard_draft_v2: WG-V1 PASS on 2026-05-17
- international_group_work_guard_v2_audit: PASS_AFTER_EXPOSURE_FILTER_PATCH
- international_group_work_guard_v2_status: draft, not published to `work_guards/`
- international_group_phase0_restart_v1: drafted, TR-not-ready
- international_group_phase0_restart_audit: PASS_WITH_WATCH_AFTER_HYGIENE_PATCH
- international_group_arc01_scene_ready_packet_v1: drafted
- international_group_arc01_scene_ready_packet_audit: PASS_WITH_WATCH
- international_group_tr01_10_planning_draft_v1: drafted
- international_group_tr01_10_planning_audit: PASS_WITH_WATCH
- international_group_ep001_003_s4_compact_writer_seed_v1: drafted
- international_group_ep001_003_s4_compact_writer_seed_audit: PASS_WITH_WATCH
- international_group_ep001_s4_canary_sample_v1: drafted
- international_group_ep001_s4_canary_sample_v1_audit: PASS_WITH_PATCH_RECOMMENDED
- international_group_ep001_s4_canary_sample_v2: drafted
- international_group_ep001_s4_canary_sample_v2_audit: PASS_WITH_WATCH
- international_group_ep002_s4_canary_sample_v1: drafted
- international_group_ep002_s4_canary_sample_v1_audit: PASS_WITH_WATCH
- international_group_ep003_s4_canary_sample_v1: drafted
- international_group_ep003_s4_canary_sample_v1_audit: PASS_WITH_WATCH
- international_group_ep001_003_opening_ladder_synthesis_v1: drafted
- international_group_ep001_003_opening_ladder_audit: PASS_WITH_PATCH_REQUIRED_BEFORE_WIDER_RANGE
- international_group_tr01_10_first_tranche_handoff_v1: packaged
- international_group_tr01_10_first_tranche_handoff_audit: PASS_WITH_WATCH_FOR_EP004_CANARY
- international_group_ep004_b5_s4_canary_sample_v1: drafted
- international_group_ep004_b5_s4_canary_audit: PASS_WITH_WATCH
- international_group_ep005_b6_s4_canary_sample_v1: drafted
- international_group_ep005_b6_s4_canary_audit: PASS_WITH_WATCH
- international_group_ep006_b7_s4_canary_sample_v1: drafted
- international_group_ep006_b7_s4_canary_audit: PASS_WITH_WATCH
- international_group_ep007_b8_s4_canary_sample_v1: drafted
- international_group_ep007_b8_s4_canary_audit: PASS_WITH_WATCH
- international_group_ep008_009_b9_s4_canary_sample_v1: drafted
- international_group_ep008_009_b9_s4_canary_audit: PASS_WITH_WATCH
- international_group_ep009_010_b10_s4_canary_sample_v1: drafted
- international_group_ep009_010_b10_s4_canary_audit: PASS_WITH_WATCH
- Phase0-final: no
- phase0-draft-ready-for-canary: yes
- ep001-003-s4-canary-packet: PASS_WITH_WATCH
- partial_opening_bundle_phase0_created: yes
- TR-ready: no
- BI-ready: no
- range-complete immediate-use candidate: no
- all 2~6 ledger rows have has_cider true: yes
- block 1 used as opening rescue: no
- block 7+ used as opening rescue: no
- Firefly/S4 compatibility bridge present: yes
- firefly_side_research_dryrun_plan: PASS_WITH_WATCH_FOR_FILE_ONLY_EP007_DRYRUN
- ep007_buyer_desk_file_only_dryrun: PASS_WITH_WATCH_FOR_S4_CONTEXT_INTEGRATION_DESIGN
- firefly_s4_writer_context_integration_contract: PASS_WITH_WATCH_FOR_CONTEXT_FILL_SAMPLE
- ep007_buyer_desk_s4_writer_context_fill_sample: PASS_WITH_WATCH_FOR_FILE_ONLY_PROSE_DRYRUN
- material_to_s4_context_reusable_template: PASS_WITH_WATCH_FOR_ONE_FILE_ONLY_PROSE_DRYRUN
- ep007_buyer_desk_file_only_prose_from_s4_context: PASS_WITH_WATCH_FOR_SECOND_TEMPLATE_SURFACE_OR_HARNESS_CAPTURE
- ep006_product_hand_template_driven_file_only_prose: PASS_WITH_WATCH_FOR_TEMPLATE_HARNESS_CAPTURE
- firefly_material_to_s4_context_bridge_harness: PASS_WITH_WATCH_FOR_SEPARATE_FIREFLY_INTEGRATION_ISSUE

## 10. WG-V2 Manual Audit

Input:

- `material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_work_guard_draft_v2.yaml`
- `docs/2026-04-06/wg-v2-freeze-checklist.md`

Validator:

- `python -X utf8 scripts/run_work_guard_v1.py --path material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_work_guard_draft_v2.yaml`
- result: `WG-V1 PASS`
- counts: tracking_slots=4, mandatory_scene_engines=3, forbidden_flattenings=8, protagonist_weapon=3, admiration_axes=5

Manual checklist:

| Item | Verdict | Reason |
|---|---|---|
| One-Line Truth | YES | ruined heir -> discarded group risk -> money/person/access/successor authority is visible |
| Protagonist-First Purity | YES | low status comes from age/order/family politics/collapse record, not repentance or deserved failure |
| Tracking Slots | YES | slots track rank/access/team/file movement, not generic growth |
| Signature Scene Engine | YES | VIP file correction, conditioned account, helper contract, external quote, audit badge are all protagonist-specific |
| Protagonist Weapon | YES | future liquidation memory is translated into current files, conditions, quotes, and limits |
| Reward Vector | YES | first reward is file position, route change, account condition, interview right, audit/file access |
| Crisis Doctrine | YES | 선독 -> 제한 조건 -> 최소 피해 -> 즉시 보상 구조가 guard에 있다 |
| Forbidden Flattenings Coverage | YES | humiliation-only, number-only profit, free faith, same-room sector drift, B7+ rescue are blocked |
| Translation Discipline | YES | philosophy is compressed into runtime slots rather than pasted as doctrine essay |
| Work Specificity | YES | this guard would be awkward on non-International-Group works because it depends on LC, bank hold, Busan payroll, telex access, grandfather condition, and public-name restoration |

WG-V2 verdict:

`PASS_FOR_DRAFT`

Freeze/publish decision:

- Do not publish to `work_guards/` yet.
- Reason: Phase0 is still not restarted from the International Group baseline and final title/family tree/opponent ladder/market calendar are open.
- The v2 draft is strong enough to drive the next Phase0/opening-bundle design.

## 11. Adversarial Audit

### Pass 1 - Are we just making another Layoff-like rights packet?

Verdict: PASS_WITH_WATCH.

The current candidate can drift into a dry rights packet if TR/BI only says "access, audit, authority." The bridge blocks that by forcing rooms, actors, objects, human cost, and visible movement. Watch remains because B4/B5 still need richer human texture before final S4 writing.

### Pass 2 - Are we actually using successful manuscript induction?

Verdict: PASS.

The adopted level is functional, not textual: ignored heir opening, first proof before long explanation, money-to-authority conversion, helper by contract, and rapid opening reward. Donor prose, names, unique object chain, and exact event chain are still forbidden.

### Pass 3 - Can Firefly S4 use this without seeing harness words?

Verdict: PASS_WITH_WATCH.

The compact handoff can become scenes: desk, file, route, memo, account, interview, report, quote, transfer, badge, next file. Watch: if S4 receives the full canon and guard text instead of the compact seed, it will likely write report-like prose.

## 12. Current Conclusion

Current accepted chain and next unit:

1. treat the EP001 canary from `ep001_003_s4_canary_packet_v1.md` as completed historical proof, not the live next step;
2. accept `78/79` as tiny 1984/1985 EP001 micro-canary result: `PASS_WITH_WATCH_AFTER_PATCH`;
3. create International Group `work_guard_draft_v2` with bank/telex/payroll/grandfather-condition slots;
4. use `83/84` as the Arc 01 scene-ready bridge from Phase0 into S4/TR planning;
5. use `85/86` as the controlled TR 1-10 planning tranche;
6. accept `92/93` as the current research-only EP001 S4 canary proof;
7. accept `94/95` as the current research-only EP002 S4 canary proof;
8. accept `96/97` as the current research-only EP003 S4 canary proof;
9. accept `98/99` as the current EP001-EP003 opening-ladder synthesis/audit;
10. accept `100/101` as the current TR01-10 first-tranche handoff package/audit;
11. accept `102/103` as the current research-only EP004/B5 S4 canary proof;
12. accept `104/105` as the current research-only EP005/B6 S4 canary proof;
13. accept `106/107` as the current research-only EP006/B7 S4 canary proof;
14. accept `108/109` as the current research-only EP007/B8 S4 canary proof;
15. accept `110/111` as the current research-only EP008-009/B9 S4 canary proof;
16. accept `112/113` as the current research-only EP009-010/B10 S4 canary proof;
17. accept `114` as the first-tranche synthesis: `PASS_WITH_WATCH_FOR_COMPACT_HANDOFF_DRAFT`;
18. accept `115` as the first-tranche synthesis audit: `PASS_WITH_PATCH_NOTES_FOR_COMPACT_HANDOFF_DRAFT`;
19. accept `116` as the EP004-010 S4 compact handoff;
20. accept `117` as the compact handoff audit: `PASS_WITH_WATCH_FOR_CONTROLLED_CONTEXT_SMOKE`;
21. accept `118/121` as the finance/file-room S4 context smoke proof: `PASS_WITH_WATCH_FOR_SECOND_SURFACE_SMOKE`;
22. accept `122/124` as the product-hand S4 context smoke proof: `PASS_WITH_WATCH_FOR_FIREFLY_SIDE_RESEARCH_DRYRUN`;
23. accept `125/126` as the research-only Firefly-side dryrun plan/audit: `PASS_WITH_WATCH_FOR_FILE_ONLY_EP007_DRYRUN`;
24. accept `127/129` as the EP007 buyer-desk file-only dryrun proof after external-audit patch: `PASS_WITH_WATCH_FOR_S4_CONTEXT_INTEGRATION_DESIGN`;
25. accept `130/131` as the material-to-Firefly S4 Writer Context integration contract/audit: `PASS_WITH_WATCH_FOR_CONTEXT_FILL_SAMPLE`;
26. accept `132/133` as the EP007 buyer-desk S4 Writer Context fill sample/audit: `PASS_WITH_WATCH_FOR_FILE_ONLY_PROSE_DRYRUN`;
27. accept `134/135` as the reusable material-to-S4-context template/audit: `PASS_WITH_WATCH_FOR_ONE_FILE_ONLY_PROSE_DRYRUN`;
28. accept `136/137` as the first template-driven file-only prose dryrun/audit: `PASS_WITH_WATCH_FOR_SECOND_TEMPLATE_SURFACE_OR_HARNESS_CAPTURE`;
29. accept `138/139` as the second template-driven file-only prose dryrun/audit: `PASS_WITH_WATCH_FOR_TEMPLATE_HARNESS_CAPTURE`;
30. accept `firefly-material-to-s4-context-bridge-harness-v1.md` plus `140` as governance capture/audit: `PASS_WITH_WATCH_FOR_SEPARATE_FIREFLY_INTEGRATION_ISSUE`;
31. issue #157 checkpoint update posted; stop this material-side loop at the checkpoint; any production S4 context assembly change needs a separate Firefly-side integration issue;
32. deepen sector source surfaces before later TR tranches.

This is the correct BI/TR/GUARD direction because it improves the material before multiplying it.
