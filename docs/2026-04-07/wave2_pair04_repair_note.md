# Wave2 Pair 04 Repair Note

Date: 2026-04-07
Status: active
Scope: bounded `content.reward` same-block receipt injection for flagged no-cider blocks only
Pair: `04` / `defense_defect_engineer` (blockguide family)
Source audit: `docs/2026-04-07/10pair_true_benchmark_terminal04_pair04_report.md`
Mutated file: `treatments/04_defense_defect_engineer_tr_block_070_draft.json`

## Repair Scope (closed)

- flagged no-cider blocks only: **B1, B3, B5, B7, B11, B19, B24, B31, B43, B49, B55, B63, B67** (13 blocks)
- touched field: `blocks[*].content.reward` only — single-sentence append per block
- not touched: `title`, `stakes`, `context`, `event_villain`, `solution`, `power_shift`, `relationship_delta`, `foreshadow`, `callback`, `emotional_beat`, `tension_level`, `pov_character`, `location`, `time_span`, `genre_ext` (all sub-fields including `capital_before` / `capital_after` / `capital_delta` / `section_rotation`), `regression_ext`
- phase 0 checkpoint structure (B10/B20/B30/B40/B50/B60/B69): untouched
- other blocks (non-flagged 57 blocks): untouched
- total block count preserved: 70

## Repair Recipe Applied

| Block | Type | Injected receipt (1 line, same-block) |
| --- | --- | --- |
| B1 | future-prep token | 정해윤 시야 가장자리에 14년 메모 모서리 한 줄 노출 → B4 첫 의심선의 사전 등록 영수증 |
| B3 | defeat #1 receipt | 48시간 유예권 구두 발행 사실이 이사회 회의록 공식 문장으로 고정 → 되돌릴 수 없는 결재 절차 영수증 |
| B5 | quiet access-shift token | 출입 대장 '전략조정실 상무보 명의' 란에 이름 첫 등록 → B8/B16 상시 출입 권한 1종 즉시 발급 |
| B7 | defeat #2 receipt | 윤소라 하중표 여백의 '3일 뒤 14:00 / 격납고 G-4' 메모 → 재접선 약속 영수증 1건 |
| B11 | defeat #3 receipt | 감사장부 2차 묶음 전략조정실 결재번호(SJ-2010-0412) 즉시 등록 → 감사 권한 상향 영수증 |
| B19 | defeat #4 receipt | 박성우 '3개월 공백 = 내 명의 접수' 메모 → ARC-03 공식 접수창구 1종 |
| B24 | defeat #5 receipt | 감사장부 2차 '부분 개봉' 사실 가족회의 속기록 명문화 → 민태수 라인 상시 압박 영수증 |
| B31 | defeat #6 receipt | 서면 답변 국회 사무처 접수번호(NA-2011-1207) 등록 → Block 40 카르텔 역제압 선공 증빙 |
| B43 | defeat #7 receipt | UAE '개조 진행 중' 공식 수용 전문 삽입 + 공군 시험평가대대 확인서 부속서화 → 신뢰 카드 1종 |
| B49 | defeat #8 receipt | 정책금융공사 검토관이 ENBD 단독 채널 리스크를 선행 검토 항목으로 서면 지정 → 검토 라벨 1장 |
| B55 | defeat #9 receipt | 윤문희 차명 보증 감사실 별건 등록번호(KM-2012-0317) 분리 접수 + SPV 발동 제약 원문 고정 → 즉시 탈취 봉쇄 영수증 |
| B63 | defeat #10 receipt | 비상 의결권 위임장 비서실 등록번호(CE-2013-1121) 즉시 등재 + 이사회 회의록 공식 문장 → 권한 수령 서류 영수증 |
| B67 | defeat #11 receipt | DGA 재심 요청서 접수번호(DGA-2014-0629) 즉시 등록 + 엘렌 크로프트 조건표 '1차 작동' 도장 → 방어 카드 2종 동시 접수 영수증 |

Each injected line is a procurement / standard / approval / control / access shift receipt countable inside the same block — not a later-payoff promise, not a domain explanation, not a setup note.

## Non-Negotiable Adherence

- defeat framing preserved: 각 defeat block의 `(패배 #N — ...)` 태그·capital_delta 수치는 그대로 유지. receipt는 패배 위에 얹힌 same-block 영수증이지 defeat 자체의 취소가 아니다.
- WG custom_rules 준수: '반격 예약 없는 손해 금지' 원칙을 same-block 단위로도 만족시키도록 한 줄만 부착. forbidden_flattenings의 '안전 위장으로 자기이익 흐림' 톤 강화 없음.
- WG tracking_slots 누적 경로 불변: 지분 1.4→19.6% 곡선, 권한 축 회수 순서, Phase0 체크포인트 5개(B10/B20/B40/B60/B69) 모두 원형 유지.
- full-wave surgery 없음: non-flagged 57 블록은 어떤 필드도 건드리지 않음.

## Expected Benchmark Effect (not re-run here)

- full-block cider scan에서 13개 no-cider 블록은 모두 same-block receipt 1장을 얻어 `has_cider: true` 쪽으로 전환 가능해진다.
- 전환이 재감리에서 확정되면 spec §6의 'any no-cider block → YELLOW ceiling' cap rule이 해제되어, P0 6/6 PASS + P1 18/20 조합으로 GREEN~GREENPLUS 승격 후보로 재분류될 수 있다.
- 단, 본 노트는 repair 기록이며 재감리는 별도 오더(wave3 등)에서 read-only로 재실행한다. 본 노트만으로 grade를 올리지 말 것.

## Diff Summary

- modified file: `treatments/04_defense_defect_engineer_tr_block_070_draft.json`
- modified blocks: 13 (`block_no` 1, 3, 5, 7, 11, 19, 24, 31, 43, 49, 55, 63, 67)
- modified field per block: `content.reward` (append-only, trailing sentence)
- added characters (approximate): B1 ~94 / B3 ~121 / B5 ~116 / B7 ~107 / B11 ~107 / B19 ~104 / B24 ~123 / B31 ~141 / B43 ~125 / B49 ~129 / B55 ~144 / B63 ~145 / B67 ~157
- BI, WG, manifest, other pair files: **not mutated**
- other docs: **not mutated**

wave2 pair 04 bounded repair complete; only `content.reward` fields of 13 flagged blocks were mutated; no other TR fields, no other blocks, no phase checkpoint structure touched.
