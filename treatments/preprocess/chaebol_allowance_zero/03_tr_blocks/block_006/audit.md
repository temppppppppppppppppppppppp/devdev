# Block 006 Audit

- Source sync:
  - Canonical source: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json / Block 6`.
  - `candidate.json` and `fixed.json` are locked to the accepted unnumbered canonical TR source.

- Opponent uniqueness:
  - Current block opponent count: `1`.
  - Opponent: `박선오`.
  - Verdict: PASS.

- Weakness uniqueness:
  - Current block weakness count: `1`.
  - Weakness: `조의금 봉투 번호와 외주 영수증을 끝까지 대조하는 사람은 없었다고 믿는 손장부 관성`.
  - Verdict: PASS.

- Density:
  - Bundle chars: `938`.
  - Breakdown: `178 / 182 / 293 / 163 / 122`.
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
  - `block_006` is usable as a sequential production unit inside the preprocess base.
  - Next unit: `03_tr_blocks/block_007/`.
