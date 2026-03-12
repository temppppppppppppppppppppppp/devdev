# Block 038 Audit

- Source sync:
  - Canonical source: `treatments/chaebol_allowance_zero_tr_block_070_draft.json / Block 38`.
  - `candidate.json` and `fixed.json` are locked to the accepted unnumbered canonical TR source.

- Opponent uniqueness:
  - Current block opponent count: `1`.
  - Opponent: `황지운`.
  - Verdict: PASS.

- Weakness uniqueness:
  - Current block weakness count: `1`.
  - Weakness: `소모품 창고관리자로서 '발열 체크 부스'를 단순한 셔틀/운행 잡무나 비용으로 보고, 선별동선 패키지 계약가 다음 운영권과 정산권으로 이어진다는 사실을 읽지 못한다.`.
  - Verdict: PASS.

- Density:
  - Bundle chars: `970`.
  - Breakdown: `243 / 236 / 263 / 110 / 118`.
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
  - `block_038` is usable as a sequential production unit inside the preprocess base.
  - Next unit: `03_tr_blocks/block_039/`.
