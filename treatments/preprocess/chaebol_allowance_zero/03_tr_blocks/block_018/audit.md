# Block 018 Audit

- Source sync:
  - Canonical source: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json / Block 18`.
  - `candidate.json` and `fixed.json` are locked to the accepted unnumbered canonical TR source.

- Opponent uniqueness:
  - Current block opponent count: `1`.
  - Opponent: `홍계상`.
  - Verdict: PASS.

- Weakness uniqueness:
  - Current block weakness count: `1`.
  - Weakness: `호텔 정산팀장로서 '카드키보다 영수증'를 단순한 정산/지급 잡무나 비용으로 보고, 정산 코드 통합가 다음 운영권과 정산권으로 이어진다는 사실을 읽지 못한다.`.
  - Verdict: PASS.

- Density:
  - Bundle chars: `957`.
  - Breakdown: `232 / 228 / 270 / 108 / 119`.
  - Verdict: PASS.

- Field coverage:
  - business_sector: `present`.
  - section_rotation: `present`.
  - power_shift: `present`.
  - relationship_delta count: `2`.
  - foreshadow count: `1`.
  - callback count: `2`.
  - Verdict: PASS.

- UTF-8:
  - `candidate.json` parse: PASS.
  - `fixed.json` parse: PASS.
  - Replacement-marker scan: clean.
  - Verdict: PASS.

- Manual verdict:
  - PASS.
  - `block_018` is usable as a sequential production unit inside the preprocess base.
  - Next unit: `03_tr_blocks/block_019/`.
