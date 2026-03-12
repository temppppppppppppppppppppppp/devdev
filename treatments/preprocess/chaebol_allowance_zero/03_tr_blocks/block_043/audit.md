# Block 043 Audit

- Source sync:
  - Canonical source: `treatments/chaebol_allowance_zero_tr_block_070_draft.json / Block 43`.
  - `candidate.json` and `fixed.json` are locked to the accepted unnumbered canonical TR source.

- Opponent uniqueness:
  - Current block opponent count: `1`.
  - Opponent: `박정선`.
  - Verdict: PASS.

- Weakness uniqueness:
  - Current block weakness count: `1`.
  - Weakness: `계열 회계팀장로서 '세금계산서 14분'를 단순한 정산/회전율 잡무나 비용으로 보고, 청구 타임테이블 계약가 다음 운영권과 정산권으로 이어진다는 사실을 읽지 못한다.`.
  - Verdict: PASS.

- Density:
  - Bundle chars: `956`.
  - Breakdown: `241 / 235 / 249 / 111 / 120`.
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
  - `block_043` is usable as a sequential production unit inside the preprocess base.
  - Next unit: `03_tr_blocks/block_044/`.
