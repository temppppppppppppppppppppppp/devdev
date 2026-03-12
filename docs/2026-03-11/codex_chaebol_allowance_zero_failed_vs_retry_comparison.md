# chaebol_allowance_zero 실패본 vs 재시도본 비교

## Findings

1. `Major` 재시도 TR은 같은 기획 축에서 실패본의 핵심 결함을 실질적으로 해소했다. 실패본은 초반 10블록이 `노현주/서도윤` 2인 교대였고 상위 weakness가 섹터별 `10회`씩 반복됐지만, 재시도본은 초반 10블록에 `8명`의 opponent가 들어가고 top weakness repetition이 `1회`에 머문다.
2. `Major` BI 5-pass 자체는 실패본을 걸러내지 못했다. 2026년 3월 11일 재실행 기준으로 실패 BI와 재시도 BI가 둘 다 5-pass `PASS`였고, 차이는 BI 구조가 아니라 source TR 품질에서 발생했다.
3. `Medium` 기존 실패 평가의 `sector missing`은 내용 결함이 아니라 필드명 드리프트 성격이 강하다. 실패본과 재시도본 모두 `business_sector`, `section_rotation`가 `70/70` 채워져 있어 `sector missing`으로 다시 판정할 수 없다.
4. `Minor` 기존 감리 문서의 핵심 수치는 직접 재계산과 일치했다. 다만 `실패 BI도 source TR 기준으로는 5-pass PASS`라는 점은 이번 직접 재검증으로 명시적으로 확인됐다.

## TR Comparison

같은 기획 기준 비교는 유효하다. [opus_재벌3세인데용돈이0원.md](/c:/Users/wjjo/Desktop/글도비/docs/2026-03-10/opus_재벌3세인데용돈이0원.md)는 `재벌 3세인데 용돈이 0원`, `윤재이`, `가문보다 먼저 돈줄의 주인이 된다` 축을 명시하고, [chaebol_allowance_zero_phase0_design.json](/c:/Users/wjjo/Desktop/글도비/treatments/chaebol_allowance_zero_phase0_design.json)도 같은 제목·주인공·코어 프레미스를 유지한다. 실패본과 재시도본 TR은 70개 title sequence가 동일하므로, 이번 비교는 같은 기획본 재시도 비교로 볼 수 있다.

| Metric | 실패본 | 재시도본 | 차이 |
| --- | ---: | ---: | --- |
| `opponent_unique` | 4 | 31 | +27 |
| `weakness_unique` | 7 | 70 | +63 |
| `deal_unique` | 70 | 70 | 동일 |
| `method_unique` | 70 | 70 | 동일 |
| `avg_bundle_chars` | 321.29 | 972.93 | +651.64 |
| top opponent repetition | `서도윤 29`, `윤석진 28`, `백도현 8` | `윤석진 17`, `노현주 5`, `서도윤 5` | 집중도 완화 |
| top weakness repetition | 동일 weakness 최대 `10회` | 최대 `1회` | 반복 해소 |
| `validate_treatment_structure` | `true` | `true` | 동일 |
| 70블록 완성 | `true` | `true` | 동일 |
| UTF-8 이상 | 없음 | 없음 | 동일 |

직접 읽은 반복 패턴 차이도 명확하다.

- 실패본 `B01~10`은 `노현주/서도윤`만 번갈아 나오고, `weakness_exploited`가 전부 `작아 보이는 운영비가 멈추면...`로 고정된다.
- 실패본 `B01~10`의 solution은 모두 `~~ 방식으로 장례 의전 라인을 자기 cashflow에 묶는다`와 `주도권을 자기 쪽으로 당긴다` 골격을 반복한다.
- 재시도본 `B01~06`은 `노현주, 최병태, 서도윤, 오세란, 임상규, 박선오`로 적대자가 분화되고, deal도 `운영 총괄 위임`, `급식 대체 하도급`, `주차·셔틀 관제 위임`, `화환 대금 채권 선인수`, `셔틀 노선권 양수 예약`, `정산 누수 감사 착수`로 갈라진다.
- 재시도본도 `B07~10` 구간에는 국소 템플릿 재사용이 남아 있다. 다만 실패본처럼 70블록 전역에 걸친 2인 로테이션/10회 약점 복붙 수준은 아니다.

`sector missing` 재판정 결과도 다르다. 실패본과 재시도본 모두 `business_sector_missing = 0`, `section_rotation_missing = 0`이라서, 기존 실패 평가는 `sector` 단일 키만 본 필드명 드리프트가 섞여 있었다고 보는 편이 맞다.

## BI Comparison

BI는 둘 다 자기 source TR과는 정합적이었다. 차이는 BI 구조 자체보다, BI가 실어 나르는 source TR의 밀도와 반복도에 있다.

| Metric | 실패본 | 재시도본 | 차이 |
| --- | ---: | ---: | --- |
| `plot_roadmap_len` | 70 | 70 | 동일 |
| `plot_roadmap` title sequence 정합성 | `true` | `true` | 동일 |
| source TR과 roadmap hash 정합성 | `true` | `true` | 동일 |
| `FinanceHUD.portfolio_history` ↔ source TR 동기화 | `true` | `true` | 동일 |
| 최종 자산 | `1320억` | `1318억` | source TR 차이 반영 |
| 5-pass 결과 | `PASS` | `PASS` | 동일 |
| UTF-8 이상 | 없음 | 없음 | 동일 |

이번에 [audit_bi_5pass.py](/c:/Users/wjjo/Desktop/글도비/scripts/audit_bi_5pass.py)를 2026년 3월 11일 기준으로 실패 pair와 재시도 pair에 다시 실행한 결과, 둘 다 `PASS`였다. 이 점은 중요하다.

- 실패 BI는 실패 TR의 약한 구조를 그대로 운반하지만, 자기 TR과의 동기화만 보면 문제없다.
- 재시도 BI도 재시도 TR을 그대로 운반하며, `plot_roadmap`, `portfolio_history`, 제목, 주인공, 회사 축이 모두 맞다.
- 따라서 BI 비교의 본질은 `failed BI가 깨졌다 vs retry BI가 멀쩡하다`가 아니라 `failed BI가 약한 TR을 정확히 싣고 있고, retry BI가 개선된 TR을 정확히 싣고 있다`에 가깝다.

기존 문서와의 차이도 이 지점에 한정된다.

- [chaebol_allowance_zero_full_retry_vs_failed_audit.md](/c:/Users/wjjo/Desktop/글도비/treatments/audit_reports/chaebol_allowance_zero_full_retry_vs_failed_audit.md), [chaebol_allowance_zero_bi_retry_vs_failed.md](/c:/Users/wjjo/Desktop/글도비/bible/audit_reports/chaebol_allowance_zero_bi_retry_vs_failed.md), [chaebol_allowance_zero_bi_5pass.md](/c:/Users/wjjo/Desktop/글도비/bible/audit_reports/chaebol_allowance_zero_bi_5pass.md)의 핵심 수치와 직접 계산값은 일치했다.
- 다만 기존 비교 문서는 `실패 BI도 failed TR 기준으로는 5-pass PASS`라는 점을 전면에 두지 않았고, 이번 재검증으로 그 사실을 명확히 고정했다.

## Final Verdict

`대체 가능`

재시도본은 같은 기획 축과 같은 70개 타이틀을 유지하면서도, 실패본의 핵심 결함이던 opponent 2인 로테이션, weakness 10회 반복, 저밀도 TR 문제를 수치상으로 명확하게 줄였다. BI도 재시도 TR과 완전히 동기화돼 있어 산출물 체인은 정상이다. 다만 이번 비교는 `BI 5-pass PASS`가 곧 좋은 BI라는 뜻이 아니라, `좋은 source TR을 실은 BI가 더 낫다`는 점을 함께 보여 준다. 결론적으로 재시도본은 실패본을 실무 기준에서 대체할 수 있다.
