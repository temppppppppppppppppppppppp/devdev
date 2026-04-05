# Authority Map

Status: active scaffold map
Date: 2026-04-05

## Current Authority

- reference card inventory:
  `material_ssot/10_research/20_fewshot_bank/reference_card_manifest.json`
- reference card content:
  `material_ssot/10_research/20_fewshot_bank/cards/`
- preprocess live artifacts:
  `treatments/preprocess/{work_id}/`
- phase0 live artifacts:
  `treatments/{work_id}_phase0_design.json`
- TR live artifacts:
  `treatments/{work_id}_tr_block_070_draft.json`
- BI live artifacts:
  `bible/0_bi_{work_id}.json`

## Scaffold Target Authority

cutover 이후 목표 canonical 후보:

- project vertical artifacts:
  `narrative_ssot/50_projects/{work_id}/...`
- shared governance and contracts:
  `narrative_ssot/00_governance/`, `narrative_ssot/40_contracts/`

## Safe Interpretation

현 시점에서는 아래처럼 해석한다.

- `narrative_ssot/`는 구조 실험용 scaffold다.
- 기존 경로가 여전히 실운영 authority다.
- pilot 작품만 `narrative_ssot/50_projects/{work_id}/`를 우선 실험할 수 있다.
- `narrative_ssot/10_reference_bank/reference_card_manifest.json`와
  `narrative_ssot/10_reference_bank/cards/`는 mirror copy다.
- `narrative_ssot/10_reference_bank/selection/`은 shared sink가 아니라 pointer note다.
- `narrative_ssot/10_reference_bank/idea_engine_db/`는 draft archive residue다.
- old reference-bank `source_corpora` root는 transition residue다.
