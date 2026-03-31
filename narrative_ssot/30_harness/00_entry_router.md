# Entry Router

Status: scaffold draft
Date: 2026-03-31

## Purpose

요청이 들어왔을 때 어떤 하네스를 먼저 읽을지 결정한다.

## Routing

- few-shot 수집, 카드 저장, source 확인:
  `12_reference_selection_harness.md` 이전에 reference layer를 확인한다.
- card 선택, shortlist, contamination 검토:
  `12_reference_selection_harness.md`
- `source_manifest`, `profile_lock`, `material_bundle_summary`, `phase0_ready_snapshot`:
  `20_stage0_preprocess_harness.md`
- `phase0_design` 작성 또는 수정:
  `30_phase0_planning_harness.md`
- `TR` 생산, resume, repair:
  `40_tr_production_harness.md`
- `BI` 생성 또는 sync:
  `50_bi_build_harness.md`
- legacy와 scaffold 공존, export, cutover:
  `70_compat_cutover_harness.md`

## Guardrail

- 기존 작품 repair는 default로 legacy path 기준을 먼저 확인한다.
- 신규 작품 pilot만 scaffold path 우선 적용을 허용한다.

