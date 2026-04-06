# Block 011 Audit

- Source sync:
  - Canonical source: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json / Block 11`.
  - `candidate.json` and `fixed.json` are locked to the accepted unnumbered canonical TR source.

- Opponent uniqueness:
  - Current block opponent count: `1`.
  - Opponent: `윤석진`.
  - Verdict: PASS.

- Weakness uniqueness:
  - Current block weakness count: `1`.
  - Weakness: `비용표 숫자만 맞추면 현장 권력도 계속 재무실 아래에 묶여 있다고 믿는 CFO 시야. 특히 '객실보다 린넨' 같은 린넨 운영권 일부 양수이 결국 세탁/린넨 통제권으로 커진다는 점을 늦게 본다.`.
  - Verdict: PASS.

- Density:
  - Bundle chars: `989`.
  - Breakdown: `242 / 248 / 274 / 108 / 117`.
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
  - `block_011` is usable as a sequential production unit inside the preprocess base.
  - Next unit: `03_tr_blocks/block_012/`.
