# 01~10 Canonical Pair Manifest

작성일: 2026-04-07
목적: 현재 repo에서 운영 중인 **active canonical pair slots**와 retired slot 상태를 한 장에 고정한다.

## Canonical Rule

- 이 문서의 `01~10`은 active slot과 retired slot을 함께 포함하는 번호 manifest다.
- 같은 번호대에 실험/보조 자산이 있어도, 3축 정합이 없으면 canonical pair로 세지지 않는다.
- pair audit, benchmark, repair, meta-cleanup 오더는 이 manifest를 기준으로 pair 번호를 해석한다.
- retired slot은 자동 재사용하지 않는다.
- 이 문서는 **full live inventory** 문서가 아니다. unslotted live pair와 benchmark freshness는 `material_ssot/00_governance/production-pair-operational-registry-v1.md`에서 따로 읽는다.

## Pair Table

| Pair | Slug / Title | BI | TR | Work Guard | Note |
| ---- | ---- | ---- | ---- | ---- | ---- |
| `01` | `투자물_골든_카나리아 테스트` | `bible/01_bi_투자물_골든_카나리아 테스트_canonical_v1.json` | `treatments/01_tr_투자물_골든_카나리아 테스트_canonical_v1.json` | `work_guards/01_투자물_골든_카나리아 테스트_canonical_v1.yaml` | canonical v1 naming 유지 |
| `02` | `chaebol_allowance_zero` | `bible/02_bi_chaebol_allowance_zero.json` | `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` | `work_guards/02_chaebol_allowance_zero.yaml` | main pair |
| `03` | `chaebol_ent_empire` | `bible/03_bi_chaebol_ent_empire.json` | `treatments/03_chaebol_ent_empire_tr_block_070_draft.json` | `work_guards/03_chaebol_ent_empire.yaml` | main pair |
| `04` | `defense_defect_engineer` | `bible/04_bi_defense_defect_engineer.json` | `treatments/04_defense_defect_engineer_tr_block_070_draft.json` | `work_guards/04_defense_defect_engineer.yaml` | main pair |
| `05` | `retired` | `deleted` | `deleted` | `deleted` | retired 2026-04-07 |
| `06` | `retired` | `deleted` | `deleted` | `deleted` | retired 2026-04-07 |
| `07` | `office_checkup_next_day` | `bible/07_bi_office_checkup_next_day.json` | `treatments/07_office_checkup_next_day_tr_block_070_draft.json` | `work_guards/07_office_checkup_next_day.yaml` | main pair |
| `08` | `pantech_cyworld_reborn` | `bible/08_bi_pantech_cyworld_reborn.json` | `treatments/08_pantech_cyworld_reborn_tr_block_070_draft.json` | `work_guards/08_pantech_cyworld_reborn.yaml` | main pair |
| `09` | `wuxia_heavenly_physician` | `bible/09_bi_wuxia_heavenly_physician.json` | `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json` | `work_guards/09_wuxia_heavenly_physician.yaml` | wuxia family pair |
| `10` | `retired` | `deleted` | `deleted` | `deleted` | retired 2026-04-07 |

## Retirement Note

- `work_guards/10_permit_window_grade9.yaml` is **not** part of the canonical `01~10` production pair set.
- `05`, `06`, `10`은 2026-04-07에 concept retirement로 코어 자산이 삭제됐다.
- 따라서 `pair 10`이라고만 써도 더 이상 `jaebeol3se_loss_line`으로 auto-resolve하지 않는다.
- retired slot을 다시 쓰려면 새 번호 재부여 또는 명시적 revival decision이 먼저 필요하다.

## Operator Notes

- `01`은 `canonical_v1` suffix가 세 축 모두에 남아 있으므로, pair lookup 시 slug normalize를 섣불리 적용하지 않는다.
- `09`는 `wuxguide` 계열 pair라서 blockwise cider / benchmark 재감리 때 non-wuxia 규칙을 그대로 덮어씌우지 않는다.
- `09pair benchmark` 문서는 이름대로 01~09까지만 다루므로, retired slot을 다시 포함시키려면 별도 override가 필요하다.
- `jangyeongshil_industrial_revolution`, `manual_meridian_archivist` 같은 unslotted live pair는 이 문서가 아니라 pair operational registry에서 해석한다.

## Recommended Usage

- pair benchmark
  `01~10` pair 번호를 받을 때 먼저 이 manifest를 열어 active slot인지 retired slot인지부터 확인한다.
- production repair
  BI/TR/WG 셋 중 하나라도 이 표와 다른 경로를 쓰려면, 오더 본문에 `non-canonical override`를 명시한다.
- manifest drift check
  retired slot 재사용보다 `11+` 새 번호 또는 별도 experimental manifest를 우선한다.
