# Block 007 Audit

- Source sync:
  - Canonical source: `treatments/chaebol_allowance_zero_tr_block_070_draft.json / Block 7`.
  - `candidate.json` and `fixed.json` are locked to the accepted unnumbered canonical TR source.

- Opponent uniqueness:
  - Current block opponent count: `1`.
  - Opponent: `강미선`.
  - Verdict: PASS.

- Weakness uniqueness:
  - Current block weakness count: `1`.
  - Weakness: `장례 세탁실 반장로서 '장례식장 세탁실'를 단순한 세탁/린넨 잡무나 비용으로 보고, 세탁 물량 공동관리가 다음 운영권과 정산권으로 이어진다는 사실을 읽지 못한다.`.
  - Verdict: PASS.

- Density:
  - Bundle chars: `973`.
  - Breakdown: `248 / 234 / 267 / 106 / 118`.
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
  - `block_007` is usable as a sequential production unit inside the preprocess base.
  - Next unit: `03_tr_blocks/block_008/`.
