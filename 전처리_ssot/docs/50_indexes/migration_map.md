# migration_map

> snapshot: 2026-03-12
> 목적: 기존 루트 경로와 `전처리_ssot/docs/` 허브 경로의 관계를 기록하기 위한 지도

## 1. 원칙

- 기존 루트 폴더는 건드리지 않는다.
- 당장은 `move`가 아니라 `copy / mirror / curated-copy / indexed-reference` 원칙으로 본다.
- 실제 물리 이동이 필요하면 `docs/30_ops/migration_notes/`에서 먼저 계획을 잠근다.

## 2. 상위 규칙 / SSOT 계층

| root path | preprocess hub path | policy | status |
| --- | --- | --- | --- |
| `docs/blockguide/SSOT_blockguide-integrated-order.md` | `전처리_ssot/docs/blockguide/SSOT_blockguide-integrated-order.md` | `mirror` | active |
| `docs/blockguide/treatment-planning-harness.md` | `전처리_ssot/docs/blockguide/treatment-planning-harness.md` | `mirror` | active |
| `docs/blockguide/treatment-production-harness-v2.md` | `전처리_ssot/docs/blockguide/treatment-production-harness-v2.md` | `mirror` | active |
| `docs/blockguide/bi-production-harness-v1.md` | `전처리_ssot/docs/blockguide/bi-production-harness-v1.md` | `mirror` | active |
| `docs/blockguide/modern_fantasy_material_harness.md` | `전처리_ssot/docs/blockguide/modern_fantasy_material_harness.md` | `mirror` | active |

## 3. 전처리 설계 배경 / TF 감리

| source path | target hub path | policy | status |
| --- | --- | --- | --- |
| `docs/2026-03-12/codex_stage0_preprocess_tr_bi_foundation_plan.md` | `전처리_ssot/docs/2026-03-12/codex_stage0_preprocess_tr_bi_foundation_plan.md` | `copy` | active |
| `전처리_ssot/00_전처리_SSOT_1차_기획안.md` 성격 문서 | `전처리_ssot/docs/00_전처리_SSOT_1차_기획안.md` | `canonical-in-hub` | active |
| `전처리_ssot/01_TF_전처리기획_재감리_3pass.md` 성격 문서 | `전처리_ssot/docs/01_TF_전처리기획_재감리_3pass.md` | `canonical-in-hub` | active |
| `전처리_ssot/02_TF_생산기지_감리_및_경로.md` 성격 문서 | `전처리_ssot/docs/02_TF_생산기지_감리_및_경로.md` | `canonical-in-hub` | active |

## 4. 기획안 루트 -> 10_pitches 허브

| source path | target hub path | policy | status |
| --- | --- | --- | --- |
| `docs/2026-03-10/opus_재벌3세인데용돈이0원.md` | `전처리_ssot/docs/10_pitches/canon/chaebol_allowance_zero/` | `curated-copy` | active |
| `docs/2026-03-10/us_ai_exile_monopoly_onboarding_prompt.md` | `전처리_ssot/docs/10_pitches/canon/us_ai_exile_monopoly/` | `curated-copy` | active |
| `docs/2026-03-10/defense_defect_engineer_onboarding_prompt.md` | `전처리_ssot/docs/10_pitches/fixed/defense_defect_engineer/` | `curated-copy` | active |
| `docs/2026-03-09/컨셉기획_방산물A.md` | `전처리_ssot/docs/10_pitches/fixed/defense_defect_engineer/` | `curated-copy` | active |

## 5. 로컬 참고 / 프로젝트 자료 -> 20_db_and_materials

| source path | target hub path | policy | status |
| --- | --- | --- | --- |
| `docs/2026-03-10/top3_replanning_brief_for_tr_bi.md` | `전처리_ssot/docs/20_db_and_materials/local_refs/project_refs/us_ai_exile_monopoly/` | `curated-copy` | active |
| `docs/2026-03-11/codex_chaebol_allowance_zero_failed_vs_retry_comparison.md` 계열 | `전처리_ssot/docs/20_db_and_materials/local_refs/project_refs/chaebol_allowance_zero/` | `curated-copy` | active |
| `docs/2026-03-10/chaebol_ent_empire_tr_bi_3pass_audit.md` | `전처리_ssot/docs/20_db_and_materials/local_refs/project_refs/chaebol_ent_empire/` | `curated-copy` | active |

## 6. 골든 샘플 / 비교 샘플 -> samples

| source path | target hub path | policy | status |
| --- | --- | --- | --- |
| `bible/01_bi_투자물_골든_sample.json` | `전처리_ssot/docs/20_db_and_materials/samples/golden/investment_sample/` | `indexed-reference` | active |
| `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` | `전처리_ssot/docs/20_db_and_materials/samples/golden/chaebol_allowance_zero/` | `indexed-reference` | active |
| `bible/02_bi_chaebol_allowance_zero.json` | `전처리_ssot/docs/20_db_and_materials/samples/golden/chaebol_allowance_zero/` | `indexed-reference` | active |
| `treatments/us_ai_exile_monopoly_tr_block_070_draft.json` | `전처리_ssot/docs/20_db_and_materials/samples/golden/us_ai_exile_monopoly/` | `indexed-reference` | active |
| `bible/0_bi_us_ai_exile_monopoly.json` | `전처리_ssot/docs/20_db_and_materials/samples/golden/us_ai_exile_monopoly/` | `indexed-reference` | active |

## 7. 작품별 생산기지 매핑

| source path | target path | policy | status |
| --- | --- | --- | --- |
| `treatments/preprocess/_template/` | `treatments/preprocess/{work_id}/` | `copy-on-start` | active |
| `treatments/{work_id}_phase0_design.json` | keep in place | `final-output` | active |
| `treatments/{work_id}_tr_block_070_draft.json` | keep in place | `final-output` | active |
| `bible/0_bi_{work_id}.json` | keep in place | `final-output` | active |

## 8. MD / JSON 전환 준비 문서

| source path | target hub path | policy | status |
| --- | --- | --- | --- |
| new canonical prep docs | `전처리_ssot/docs/30_ops/migration_notes/md_json_migration_charter.md` | `canonical-in-hub` | active |
| new canonical prep docs | `전처리_ssot/docs/30_ops/migration_notes/md_json_contract_inventory.md` | `canonical-in-hub` | active |
| new canonical prep docs | `전처리_ssot/docs/30_ops/migration_notes/json_contracts_roadmap.md` | `canonical-in-hub` | active |
| new canonical prep docs | `전처리_ssot/docs/30_ops/migration_notes/json_schema_package_plan.md` | `canonical-in-hub` | active |
| new canonical prep docs | `전처리_ssot/docs/30_ops/migration_notes/md_json_migration_95_confidence_audit.md` | `canonical-in-hub` | active |
| new canonical prep docs | `전처리_ssot/docs/30_ops/migration_notes/json_contracts_seed_3pass_audit.md` | `canonical-in-hub` | active |

## 8A. 실행 계약층

| source path | target path | policy | status |
| --- | --- | --- | --- |
| new execution contracts | `전처리_ssot/contracts/schema_version.json` | `canonical-execution` | active |
| new execution contracts | `전처리_ssot/contracts/stage_machine.json` | `canonical-execution` | active |
| new execution contracts | `전처리_ssot/contracts/artifact_contracts.json` | `canonical-execution` | active |
| new execution contracts | `전처리_ssot/contracts/quality_gates.json` | `canonical-execution` | active |
| new execution contracts | `전처리_ssot/contracts/profile_catalog.json` | `canonical-execution` | active |
| new execution contracts | `전처리_ssot/contracts/handoff_rules.json` | `canonical-execution` | active |
| new execution contracts | `전처리_ssot/contracts/sequential_run_status.schema.json` | `canonical-execution` | active |
| new execution contracts | `전처리_ssot/contracts/audit_status.schema.json` | `canonical-execution` | active |

## 9. 핵심 기억할 것

1. `전처리_ssot/docs/`는 허브다.
2. 루트 문서는 지금 당장 옮기지 않는다.
3. 필요한 문서만 선별해서 `copy`, `mirror`, `curated-copy`, `indexed-reference` 원칙으로 모은다.
4. 작품별 실제 생산은 `treatments/preprocess/{work_id}/`에서 한다.
5. 최종 정본은 계속 `treatments/`, `bible/`에 둔다.
6. `md + json` 전환 준비 문서는 `migration_notes/`에서 먼저 잠근다.
7. 상위 실행 계약은 `전처리_ssot/contracts/`에 두고, 설명 문서는 계속 `docs/`에 둔다.
