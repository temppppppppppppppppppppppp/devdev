# chaebol_allowance_zero Full Retry vs Failed Audit

## Scope

- Planning SSOT: `docs/2026-03-10/opus_재벌3세인데용돈이0원.md`
- Retry TR: `treatments/chaebol_allowance_zero_tr_block_070_draft.json`
- Failed baseline TR: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`

---

## Pass 1. Structure / Completion

Verdict: PASS

- Retry TR length: `70`
- First title: `잘린 카드`
- Last title: `상속보다 센 돈줄`
- Last capital: `1318억`
- `validate_treatment_structure = true`
- schema errors: `0`
- schema warnings: `0`

---

## Pass 2. Failure Comparison

Verdict: PASS

| Metric | Failed | Retry | Result |
|---|---:|---:|---|
| `opponent_unique` | 4 | 31 | improved |
| `weakness_unique` | 7 | 70 | improved |
| `deal_unique` | 70 | 70 | maintained |
| `method_unique` | 70 | 70 | maintained |
| `avg_bundle_chars` | 321.29 | 972.93 | improved |
| top opponent concentration | `서도윤 29`, `윤석진 28` | `윤석진 17`, `노현주 5`, `서도윤 5` | improved |
| top weakness repetition | same arc weakness `10회` 반복 | 최대 `1회` | improved |

핵심 판정:

- 실패본은 70블록이 사실상 `7개 섹터 x 동일 약점 문장` 구조였다.
- retry 본은 같은 제목/기획 축을 유지하면서도 적대자와 약점이 블록 단위로 분화된다.
- 실패본은 평균 묶음 길이가 `321.29`라서 원고를 거의 전부 후단 LLM이 창작해야 했다.
- retry 본은 평균 묶음 길이가 `972.93`라서 TR 자체가 실제 서사 가이드 역할을 한다.

---

## Pass 3. Integrity / Handoff Readiness

Verdict: PASS

- UTF-8 corruption scan: `0 hits`
- `method_unique = 70`
- `deal_unique = 70`
- batch check / merge loop completed through `Block 70`
- retry draft is ready for BI generation

---

## Final Verdict

`FULL TR PASS`

This retry establishes that the reinforced harness can regenerate the same planning source into a materially denser and less repetitive 70-block TR.
