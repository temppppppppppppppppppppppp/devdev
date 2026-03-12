# work_registry

> snapshot: 2026-03-12
> 목적: 현재 `work_id`별 정본, 레거시, 전처리 기지 상태를 한 장에서 파악하기 위한 레지스트리

## 1. 읽는 법

- `canonical` = 현재 우선 참조 대상
- `legacy` = 과거 numbered 자산 또는 파생 자산
- `preprocess base` = `treatments/preprocess/{work_id}/`가 실제로 만들어졌는지 여부
- 이 문서는 "무엇이 현재 진실인가"를 정리하는 색인이다.

## 2. 작품 레지스트리

| work_id | primary profile | canonical pitch / planning source | canonical phase0 | canonical TR | canonical BI | legacy assets | preprocess base | snapshot |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `chaebol_allowance_zero` | `business_growth + office_power` | `docs/2026-03-10/opus_재벌3세인데용돈이0원.md` | `treatments/chaebol_allowance_zero_phase0_design.json` | `treatments/chaebol_allowance_zero_tr_block_070_draft.json` | `bible/0_bi_chaebol_allowance_zero.json` | `treatments/02_...`, `bible/02_...` 실패본 유지 | `initialized at treatments/preprocess/chaebol_allowance_zero/` | canonical full set exists + preprocess Stage 0 completed + TR seed baseline initialized |
| `chaebol_ent_empire` | `entertainment_media + business_growth` | `docs/2026-03-09/문피아30_배치3_엔터배우작가.md` | `treatments/chaebol_ent_empire_phase0_design.json` | `canonical pending` | `canonical pending` | `treatments/03_chaebol_ent_empire_tr_block_070_draft.json`, `bible/03_bi_chaebol_ent_empire_bi.json`, `bible/09_bi_chaebol_ent_empire_entertainment.json` | `not initialized` | phase0 exists, canonical output pending |
| `us_ai_exile_monopoly` | `tech_startup + business_growth` | `docs/2026-03-10/us_ai_exile_monopoly_onboarding_prompt.md`, `docs/2026-03-10/top3_replanning_brief_for_tr_bi.md` | `treatments/us_ai_exile_monopoly_phase0_design.json` | `treatments/us_ai_exile_monopoly_tr_block_070_draft.json` | `bible/0_bi_us_ai_exile_monopoly.json` | `treatments/08_...`, `bible/11_bi_us_ai_exile_monopoly_ai_business.json` | `not initialized` | canonical full set exists |
| `defense_defect_engineer` | `business_growth` | `docs/2026-03-09/컨셉기획_방산물A.md` | `canonical pending` | `canonical pending` | `canonical pending` | `treatments/04_defense_defect_engineer_tr_block_070_draft.json`, `bible/04_defense_defect_engineer_bi.json`, `bible/10_bi_defense_defect_engineer_defense_business.json` | `not initialized` | SSOT conflict first, then rebuild |
| `fallen_prince_buys_joseon` | `alt_history` | `docs/2026-03-09/컨셉기획_조선대체역사AB.md` | `canonical pending` | `canonical pending` | `canonical pending` | `treatments/05_fallen_prince_buys_joseon_tr_block_070_draft.json`, `bible/05_bi_fallen_prince_buys_joseon.json` | `not initialized` | legacy alt-history pair only |
| `imf_kukje_heir` | `investment_market + business_growth` | `pitch unresolved in preprocess hub` | `canonical pending` | `canonical pending` | `canonical pending` | `treatments/06_imf_kukje_heir_tr_block_070_draft.json`, `bible/06_imf_kukje_heir_bi.json` | `not initialized` | legacy pair only |
| `pantech_cyworld_reborn` | `tech_startup + business_growth` | `pitch unresolved in preprocess hub` | `canonical pending` | `canonical pending` | `canonical pending` | `treatments/07_pantech_cyworld_reborn_tr_block_070_draft.json` | `not initialized` | TR only legacy |
| `investment_sample` | `investment_market` | `sample-only` | `not applicable` | `not applicable` | `canonical pending` | `bible/01_bi_투자물_골든_sample.json` | `not initialized` | sample BI only |

## 3. 현재 우선 작업 대상

### priority A

- `chaebol_allowance_zero`
- `us_ai_exile_monopoly`

이유:

- phase0 / TR / BI canonical 세트가 이미 있다.
- 전처리 허브 기준으로 역매핑하기 좋다.
- 비교/감리 기록이 많다.

### priority B

- `chaebol_ent_empire`
- `defense_defect_engineer`

이유:

- Phase 0 또는 기획 축은 있지만 canonical output이 아직 비어 있다.
- 전처리 허브를 새로 적용해 볼 테스트 케이스다.

### priority C

- `fallen_prince_buys_joseon`
- `imf_kukje_heir`
- `pantech_cyworld_reborn`

이유:

- legacy 자산이 먼저 존재한다.
- preprocess hub 기준으로 pitch 잠금과 source manifest 정리가 선행돼야 한다.

## 4. preprocess base 상태

현재 실제 작품별 생산기지는 아직 없다.

- 존재: `treatments/preprocess/_template/`
- 존재: `treatments/preprocess/chaebol_allowance_zero/`
- 생산 상태: `03_tr_blocks/block_001..070/` + `04_tr_final/` seeded as `seed_baseline_sync`
- 미존재: `treatments/preprocess/chaebol_ent_empire/`
- 미존재: `treatments/preprocess/us_ai_exile_monopoly/`

즉, 지금은 "허브와 템플릿은 준비됐고, `chaebol_allowance_zero`는 실제 인스턴스이자 Stage 0 + TR seed baseline 사례이며, 나머지 work_id는 생성 전" 상태다.

## 5. 다음 갱신 규칙

이 문서는 아래 상황이 생길 때마다 갱신한다.

1. 새 `work_id`가 생겼을 때
2. canonical pitch가 확정됐을 때
3. canonical `phase0`, `TR`, `BI`가 생겼을 때
4. legacy 자산을 canonical로 승격하거나 폐기했을 때
5. `treatments/preprocess/{work_id}/`가 실제로 생성됐을 때
