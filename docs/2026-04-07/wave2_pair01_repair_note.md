# Wave 2 Pair 01 Repair Note

Date: 2026-04-07
Status: applied
Scope: canonical pair `01` (`투자물_골든_카나리아 테스트_canonical_v1`)
Input contract: flagged-block sweep only — no other blocks or asset curves touched
Parent report: `docs/2026-04-07/10pair_true_benchmark_terminal01_pair01_report.md`
Target file: `treatments/01_tr_투자물_골든_카나리아 테스트_canonical_v1.json`

## Contract

- flagged no-cider blocks (from parent report full-block scan): `1, 5, 8, 19, 25, 27, 31, 32, 33, 34, 44`
- each flagged block receives **exactly one** appended sentence inside the existing `reward` field:
  - either an observer-tier update beat, or
  - a same-block next-card receipt
- must not worsen the early-reward thin-pass structure (TR B2~B6 reward shape untouched)
- must not edit non-flagged blocks
- must not edit any asset-curve number (capital_before / capital_after / instruments / yearly_summary / etc.)
- drought `B31 → B32 → B33 → B34` is addressed first
- final file must remain valid JSON with `_total_blocks = 60`

## Sweep Order

1. **B31 → B32 → B33 → B34** (drought 우선 분쇄)
2. **B1 / B5 / B8 / B19 / B25 / B27 / B44** (나머지 7블록 순차)

## Inserted Beats

| Block | Mode | Inserted sentence (appended to existing `reward`) |
| ---- | ---- | ---- |
| B31 | observer-update | 박성호 내부 메모 "관망도 저 분의 매수 캘린더에는 한 칸이다" + 리스크팀이 모니터링 양식에 반영 — 하락장이 평가 주체의 기록 형식 자체를 움직인 첫 내부 변경 |
| B32 | observer-update | 마이클이 260달러 평단 체결표를 보고 처음으로 "왜 지금이냐"가 아니라 "이게 몇 번째 cycle이냐"로 질문 형식 승격 |
| B33 | observer-update | 정민재가 14조 포지션 구조도를 훑은 뒤 "이건 투자가 아니라 운용 시스템인데요" — 외부 실행 라인에서 한시우 구조가 처음으로 '시스템'으로 호명 |
| B34 | next-card receipt | 마이클이 "이걸 같이 사는 이유가 뭐냐"고 묻고 한시우가 답하지 않음 — 다음 블록에서 회수될 카드가 같은 블록 안에 예약 (same-block receipt) |
| B1 | observer-update | 한정호 회장이 비서를 부르려다 손을 도로 내림 — '재롱' 프레임에 맞지 않는 막내의 눈빛을 어떻게 파일링할지 몰라 넘긴 첫 기록 공백 |
| B5 | observer-update | 한태준 비서가 귀가길에 "잔고 움직임이 평소와 다릅니다" 한 줄 보고 → 한태준 "...다시 말해봐" — 15년 만에 처음으로 막내가 큰형의 내부 계산표에 한 칸으로 입력 |
| B8 | observer-update | 마이클 첸이 호텔 방에서 개인 노트에 "HAN, Korea, called BNP date, said Lehman not saved" 기록 — 한시우 이름이 골드만 아시아 데스크의 사적 기록 라인에 최초 파일 |
| B19 | observer-update | 제이슨이 OTC 딜러 모임에서 "미친 부자가 아니라 우리 라인 안 사람으로 분류해야 한다" — '미친놈' 라벨이 처음으로 '라인 안 사람'으로 교체 |
| B25 | observer-update | 제이슨이 OTC 내부 로그에 한시우 태그를 'bottom accumulator'로 갱신 — 공포장에서 파는 사람과 사는 사람을 구분하는 새 분류 생성 |
| B27 | observer-update | 이더리움 재단 쪽 관계자가 마이클에게 "이 형식은 기록해둬라, Asian family office는 처음이다" — 재단 내부 메모에서도 한시우의 운용 형식 최초 호명 |
| B44 | next-card receipt | 정민재가 손익표를 덮으며 "이 평가손은 다음 매수표의 예산선입니다" — 평가손 자체가 다음 카드의 자금선으로 같은 블록 안에서 재라벨 |

## Non-interference Checks

- asset curves untouched: no `capital_before` / `capital_after` / `instruments` / `yearly_summary` / 자산 숫자 수정 없음; 모든 추가 문장은 reward 필드 말미에 observer/record 레이어로만 삽입
- early reward thin-pass (TR B2~B6): 건드리지 않음. B1 추가 문장은 game-opening 레이어에 대한 observer beat이며 TR B2~B6의 reward token 강도에 영향 없음
- non-flagged blocks: 건드리지 않음. B53(line 6067)의 기존 문구 "대표님은 하락도 재료로 쓰시네요" 와 중복을 피하기 위해 B31은 별도 문구 "관망도 저 분의 매수 캘린더에는 한 칸이다" 로 사용
- drought 이웃(B30, B35): 건드리지 않음 — 이미 cider 블록이므로 신호 오염 위험 없음
- custom_rules / mandatory_scene_engines / role_fit_constraints (in WG): 건드리지 않음. 본 sweep은 TR 단독 수정

## Post-sweep Ledger

- TR total blocks: 60 (`_total_blocks` 불변)
- JSON validity: `python -m json.tool` 통과 (structural parse OK)
- no-cider blocks after sweep: `0` (기대치) — 11개 블록 전수에 same-block receipt 1줄씩 삽입 완료
- longest consecutive drought after sweep: `0` (기대치)
- ceiling rule `any no-cider block → YELLOW` (spec §6): 본 sweep의 단일 조건 — 0 달성 시 해제 예정
- 최종 재채점은 parent report 재실행(true benchmark audit 2차 pass)에서 확정. 본 note는 입력 패치만 기록

## Change Footprint

- files mutated: `treatments/01_tr_투자물_골든_카나리아 테스트_canonical_v1.json` (11 reward-field edits)
- files created: `docs/2026-04-07/wave2_pair01_repair_note.md` (this file)
- files NOT mutated: `bible/01_bi_...`, `work_guards/01_...`, parent report, any other pair
