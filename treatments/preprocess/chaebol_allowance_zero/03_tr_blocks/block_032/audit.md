# Block 032 Audit

- Source sync:
  - Canonical source: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json / Block 32`.
  - `candidate.json` and `fixed.json` are locked to the accepted unnumbered canonical TR source.

- Opponent uniqueness:
  - Current block opponent count: `1`.
  - Opponent: `주민석`.
  - Verdict: PASS.

- Weakness uniqueness:
  - Current block weakness count: `1`.
  - Weakness: `격리물류 브로커로서 '격리병동 린넨'를 단순한 세탁/린넨 잡무나 비용으로 보고, 감염세탁 전용 계약가 다음 운영권과 정산권으로 이어진다는 사실을 읽지 못한다.`.
  - Verdict: PASS.

- Density:
  - Bundle chars: `951`.
  - Breakdown: `234 / 230 / 262 / 108 / 117`.
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
  - `block_032` is usable as a sequential production unit inside the preprocess base.
  - Next unit: `03_tr_blocks/block_033/`.
