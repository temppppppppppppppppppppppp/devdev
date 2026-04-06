# chaebol_allowance_zero Batch 001 3-Pass Audit

## Scope

- Source planning SSOT: `docs/2026-03-10/opus_재벌3세인데용돈이0원.md`
- Source phase0: `treatments/chaebol_allowance_zero_phase0_design.json`
- Retry batch: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` Block 1~3
- Comparison baseline: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json` Block 1~3

---

## Pass 1. Contract / Continuity

Verdict: PASS

- `Block 1~3` title is identical to the planning/legacy sequence: `잘린 카드`, `장례 밥차`, `검은 리본 주차권`.
- `capital_before -> capital_after` continuity is valid.
  - Block 1: `0억 -> 0억`
  - Block 2: `0억 -> 2억`
  - Block 3: `2억 -> 1억`
- `relationship_delta.before` carry-over is valid.
  - Block 2 `박기호.before` matches Block 1 `박기호.after`
  - Block 3 `한유림.before` matches Block 2 `한유림.after`
- `deal_type` is differentiated across all three blocks.
  - Block 1: `장례 운영 총괄 임시 위임`
  - Block 2: `급식 긴급 대체 하도급`
  - Block 3: `주차·셔틀 관제 위임`
- Batch harness reports `unresolved P0=0 / P1=0 / P2=0`.

---

## Pass 2. Failure Comparison

Verdict: PASS

### Same planning, different output

- The retry keeps the same opening concept and the same three titles.
- The failure pattern is not reproduced in the retry.

### Measured delta against failed B01~03

| Metric | Failed B01~03 | Retry B01~03 | Result |
|---|---:|---:|---|
| `opponent_unique` | 2 | 3 | improved |
| `weakness_unique` | 1 | 3 | improved |
| `deal_unique` | 3 | 3 | maintained |
| `method_unique` | 3 | 3 | maintained |
| `avg_bundle_chars` | 317.00 | 850.67 | improved |
| `top_opponent_repetition` | `노현주 x2` | `노현주 x1` | improved |
| `top_weakness_repetition` | 동일 약점 `x3` | 최대 `x1` | improved |

### Block-level density

- Failed bundle chars
  - Block 1: `310`
  - Block 2: `312`
  - Block 3: `329`
- Retry bundle chars
  - Block 1: `836`
  - Block 2: `811`
  - Block 3: `905`

### Structural correction summary

- Failed Block 1~3 repeated `노현주/서도윤` rotation with one weakness template.
- Retry Block 1~3 uses `노현주 -> 최병태 -> 서도윤` progression.
- Failed Block 1~3 solved each scene with the same `라인을 자기 cashflow에 묶는다` skeleton.
- Retry Block 1~3 splits the action unit into:
  - operating window acquisition
  - emergency meal replacement
  - parking and shuttle control seizure
- Failed Block 1~3 was all-up curve.
- Retry Block 3 intentionally spends `1억` to win control, so the batch is no longer monotone growth.

---

## Pass 3. Integrity / Ready State

Verdict: PASS

- UTF-8 corruption scan on candidate, merged draft, and check/merge reports: `0 hits`
  - no question-mark replacement artifacts
  - no broken replacement glyphs
- Candidate and merged draft are identical for Block 1~3; autofix count is `0`.
- Merge report is clean and the retry draft now exists at `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`.
- This batch is production-safe for continuation to Block 4~6.

---

## Final Verdict

`Batch 001 PASS`

This retry proves the strengthened harness can produce materially different output from the failed baseline while holding the same planning source fixed.

## Next Unit

- Continue production with `Block 4~6`
- Preserve `02_chaebol_allowance_zero_tr_block_070_draft.json` as failure baseline
- Compare again after `Block 10` to verify the opponent/weakness diversity does not collapse back into a 2-person rotation
