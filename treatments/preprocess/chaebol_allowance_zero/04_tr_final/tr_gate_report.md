# TR Gate Report

- Scope:
  - Source: preprocess `03_tr_blocks/block_001..070/fixed.json`
  - Output: `04_tr_final/chaebol_allowance_zero_tr_block_070_draft.json`
  - Mode: canonical seed completion of the preprocess production base

- Structural checks:
  - block_count: `70`
  - capital_continuity_failures: `0`
  - business_sector_missing: `0`
  - section_rotation_missing: `0`
  - verdict: PASS

- Diversity metrics:
  - opponent_unique: `31`
  - weakness_unique: `70`
  - deal_unique: `70`
  - method_unique: `70`
  - top_opponent: `윤석진 / 17`
  - top_weakness: `유언 문구만 완벽하면 장례 현장도 저절로 굴러간다고 믿는 법률 중심 사고 / 1`
  - top_deal: `장례 운영 총괄 임시 위임 / 1`
  - top_method: `가문 자금을 쓰지 않고 사고 책임과 민원 방패를 대신 서는 방식으로 장례식장 운영 총괄 창구를 따낸다. / 1`

- Density metrics:
  - avg_bundle_chars: `972.93`
  - density_gate: PASS

- Manual verdict:
  - PASS
  - The preprocess production base now has a complete 70-block working set aligned with the canonical unnumbered TR.
  - This report does not claim a fresh rerun. It certifies that the preprocess working base is fully populated and structurally usable.
