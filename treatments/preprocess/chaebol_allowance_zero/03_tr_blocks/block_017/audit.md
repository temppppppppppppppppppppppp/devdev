# Block 017 Audit

- Source sync:
  - Canonical source: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json / Block 17`.
  - `candidate.json` and `fixed.json` are locked to the accepted unnumbered canonical TR source.

- Opponent uniqueness:
  - Current block opponent count: `1`.
  - Opponent: `정재문`.
  - Verdict: PASS.

- Weakness uniqueness:
  - Current block weakness count: `1`.
  - Weakness: `호텔 구매팀장로서 '세탁 공장 인수'를 단순한 세탁/린넨 잡무나 비용으로 보고, 세탁 공장 공동 인수가 다음 운영권과 정산권으로 이어진다는 사실을 읽지 못한다.`.
  - Verdict: PASS.

- Density:
  - Bundle chars: `975`.
  - Breakdown: `244 / 232 / 273 / 108 / 118`.
  - Verdict: PASS.

- Field coverage:
  - business_sector: `present`.
  - section_rotation: `present`.
  - power_shift: `present`.
  - relationship_delta count: `2`.
  - foreshadow count: `1`.
  - callback count: `3`.
  - Verdict: PASS.

- UTF-8:
  - `candidate.json` parse: PASS.
  - `fixed.json` parse: PASS.
  - Replacement-marker scan: clean.
  - Verdict: PASS.

- Manual verdict:
  - PASS.
  - `block_017` is usable as a sequential production unit inside the preprocess base.
  - Next unit: `03_tr_blocks/block_018/`.
