# Block 030 Audit

- Source sync:
  - Canonical source: `treatments/chaebol_allowance_zero_tr_block_070_draft.json / Block 30`.
  - `candidate.json` and `fixed.json` are locked to the accepted unnumbered canonical TR source.

- Opponent uniqueness:
  - Current block opponent count: `1`.
  - Opponent: `윤석진`.
  - Verdict: PASS.

- Weakness uniqueness:
  - Current block weakness count: `1`.
  - Weakness: `비용표 숫자만 맞추면 현장 권력도 계속 재무실 아래에 묶여 있다고 믿는 CFO 시야. 특히 '밥값이 아니라 가동률' 같은 운영성과 연동 계약이 결국 급식 통제권으로 커진다는 점을 늦게 본다.`.
  - Verdict: PASS.

- Density:
  - Bundle chars: `990`.
  - Breakdown: `251 / 249 / 267 / 105 / 118`.
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
  - `block_030` is usable as a sequential production unit inside the preprocess base.
  - Next unit: `03_tr_blocks/block_031/`.
