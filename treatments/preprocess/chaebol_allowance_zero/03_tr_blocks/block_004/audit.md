# Block 004 Audit

- Source sync:
  - Canonical source: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json / Block 4`.
  - `candidate.json` and `fixed.json` are locked to the accepted unnumbered canonical TR source.

- Opponent uniqueness:
  - Current block opponent count: `1`.
  - Opponent: `오세란`.
  - Verdict: PASS.

- Weakness uniqueness:
  - Current block weakness count: `1`.
  - Weakness: `체면 산업에서는 을이 먼저 무너질 거라 믿고 정산 지연을 상습적으로 굴리는 단기 장사 습관`.
  - Verdict: PASS.

- Density:
  - Bundle chars: `958`.
  - Breakdown: `216 / 182 / 301 / 132 / 127`.
  - Verdict: PASS.

- Field coverage:
  - business_sector: `present`.
  - section_rotation: `present`.
  - power_shift: `present`.
  - relationship_delta count: `2`.
  - foreshadow count: `1`.
  - callback count: `1`.
  - Verdict: PASS.

- UTF-8:
  - `candidate.json` parse: PASS.
  - `fixed.json` parse: PASS.
  - Replacement-marker scan: clean.
  - Verdict: PASS.

- Manual verdict:
  - PASS.
  - `block_004` is usable as a sequential production unit inside the preprocess base.
  - Next unit: `03_tr_blocks/block_005/`.
