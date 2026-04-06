# chaebol_allowance_zero BI Retry vs Failed Audit

## Scope

- Retry BI: `bible/02_bi_chaebol_allowance_zero.json`
- Failed BI: `bible/02_bi_chaebol_allowance_zero.json`
- Shared planning SSOT: `docs/2026-03-10/opus_재벌3세인데용돈이0원.md`

---

## Core Comparison

| Metric | Failed BI | Retry BI | Result |
|---|---:|---:|---|
| `plot_roadmap_len` | 70 | 70 | maintained |
| `opponent_unique` | 4 | 31 | improved |
| `weakness_unique` | 7 | 70 | improved |
| `avg_bundle_chars` | 321.29 | 972.93 | improved |
| `portfolio_history_last` | 1320억 | 1318억 | changed with source TR |

Retry top opponents:

- `윤석진` x 17
- `노현주` x 5
- `서도윤` x 5

Failed top opponents:

- `서도윤` x 29
- `윤석진` x 28
- `백도현` x 8

Key verdict:

- retry BI는 새 TR을 그대로 `plot_roadmap`에 복사하므로 실패 TR의 2인 반복 구조를 더 이상 운반하지 않는다.
- `FinanceHUD.portfolio_history`도 retry TR 자본 곡선을 따르므로 최종 자산은 `1318억`으로 동기화된다.
- title, protagonist, company 축은 동일하게 유지되어 같은 기획안 재시도 비교가 가능하다.

## Final Verdict

`RETRY BI PASS / FAILED BI SUPERSEDED`
