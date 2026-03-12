# `chaebol_allowance_zero` 실패 TR/BI 사실관계 감리

> 작성일: 2026-03-11
> 목적: 실패 샘플의 사실관계, 현재 하네스와의 충돌 지점, 보강 대상 TF를 고정
> 범위: 문서화만 수행. 본 SSOT와 JSON 산출물은 수정하지 않음.

---

## 1. 대상

- 활성 TR: `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`
- 활성 BI: `bible/02_bi_chaebol_allowance_zero.json`
- 실패작 보관 TR: `docs/blockguide/실패작들/02_chaebol_allowance_zero_tr_block_070_draft.json`
- 실패작 보관 BI: `docs/blockguide/실패작들/02_bi_chaebol_allowance_zero.json`

해시 확인:

- TR active SHA256: `B7E26B611407A3990F06AB26A56892FC365109D6CEFB9A9CF05AA4A9BE2CED3E`
- TR failed SHA256: `B7E26B611407A3990F06AB26A56892FC365109D6CEFB9A9CF05AA4A9BE2CED3E`
- BI active SHA256: `50B85963C8D0D6185CA6A8540310D1A353E10CD9A2805CE4363AC6EE1FA85F64`
- BI failed SHA256: `50B85963C8D0D6185CA6A8540310D1A353E10CD9A2805CE4363AC6EE1FA85F64`

판정:

- 실패작 폴더본은 과거 참고본이 아니라 현재 운용본과 동일하다.
- 따라서 이번 감리는 보관본 평가가 아니라 현행 파이프라인 결과물 평가다.

---

## 2. 확정 수치

### 2.1 핵심 수치

- `opponent_unique = 4`
- `avg_context = 80.79`
- `avg_event_villain = 43.14`
- `avg_solution = 86.50`
- `avg_reward = 57.71`
- `avg_stakes = 53.14`
- `avg_bundle = 321.29`
- `business_sector_missing = 0`
- `section_rotation_missing = 0`

### 2.2 반복 관련 수치

- `weakness_unique = 7`
- `top_opponent_repetition = 29`
- `top_opponent_weakness_pair_repetition = 5`
- `window_10_opponent_unique_counts = [2, 2, 2, 2, 2, 2, 3]`
- `method_unique = 70`

해석:

- `method`는 70개로 겉보기엔 분화돼 있다.
- 그러나 `solution`과 `method`의 문장 골격이 거의 고정이라 실질 반복을 가린다.
- 상대 수는 4명뿐이고, 10블록 구간 기준 적대 분화가 거의 일어나지 않는다.

---

## 3. 사용자 평가와 사실 대조

### 3.1 사실로 확인된 항목

- `opponent` 반복 문제: 사실이다.
  - 전체 적대자는 4명뿐이다.
  - 10블록 단위 opponent unique count가 `[2, 2, 2, 2, 2, 2, 3]`이라 장기 연재용 갈등 분화가 부족하다.
- `weakness_exploited` 섹터별 복붙: 사실이다.
  - 완전 동일 문장 고정은 아니지만, 섹터 단위 고정 약점이 길게 반복된다.
  - `opponent + weakness` 조합 최다 반복이 5회다.
- `solution` 문장 템플릿 동일: 사실이다.
  - `윤재이는 [방식]으로 [상황]의 주도권을 자기 쪽으로 당긴다` 계열 구조가 전 블록에서 반복된다.
- 저밀도 skeleton: 사실이다.
  - 평균 핵심 묶음 길이 `321.29`자는 현행 생산 하네스의 skeleton 경계 `350`보다 낮다.

### 3.2 바로잡아야 하는 항목

- `sector 필드 누락`: 그대로 받아들이면 오판이다.
  - 실제 JSON에는 `genre_ext.business_sector`와 `genre_ext.section_rotation`가 전 블록에 존재한다.
  - 이번 건은 순수 생성 실패가 아니라 `sector` vs `business_sector/section_rotation` 명칭 드리프트가 섞인 평가 문제다.

판정:

- `sector missing`은 content defect가 아니라 `schema_or_field_drift`를 동반한 평가 mismatch로 분류한다.

---

## 4. 현재 하네스와의 충돌 지점

### 4.1 TR 하네스와 충돌

[treatment-production-harness-v2.md](c:/Users/wjjo/Desktop/글도비/docs/blockguide/treatment-production-harness-v2.md)에는 이미 아래 규칙이 있다.

- `opponent.weakness_exploited 동일 표현 3회 이상 금지`
- `문장 템플릿 재사용 금지`
- `대단원 슬롯 반복 금지`
- `avg bundle 350 미만이면 skeleton draft`

그런데 현재 실패 샘플은 이 규칙을 사실상 위반한 상태로 남아 있다.

판정:

- 핵심 실패는 규칙 부재보다 `TR 생산 밀도/반복 실패가 감리 출력과 handoff 게이트에 충분히 연결되지 않은 상태`다.

### 4.2 BI handoff와 충돌

[chaebol_allowance_zero_bi_5pass_audit.md](c:/Users/wjjo/Desktop/글도비/docs/2026-03-10/chaebol_allowance_zero_bi_5pass_audit.md)는 BI 구조와 동기화는 PASS로 본다.

하지만 이 문서는 아래를 확인하지 않는다.

- source TR `production_density_gate`
- source TR 반복 실패
- source TR opponent 다양성
- source TR avg bundle 저밀도

판정:

- BI는 `TR 실패를 구조 정합성만 보고 운반`한 상태다.
- 핵심 실패는 `오더 누락`보다 `TR 생산 밀도/반복 실패`와 `BI handoff 과신`이다.

---

## 5. 실패 유형 분류

이번 샘플은 아래 4분류 중 이렇게 판정한다.

| 분류 | 판정 | 이유 |
| --- | --- | --- |
| `routing_gap` | 부분 해당 | 실패작/평가 메모가 들어왔을 때 triage 모드로 들어가는 오더가 약하다 |
| `schema_or_field_drift` | 해당 | `sector` 평가와 `business_sector/section_rotation` 실제 필드명이 어긋난다 |
| `production_density_failure` | 핵심 | avg bundle 321.29, opponent 분화 부족, template 반복 |
| `handoff_false_pass` | 핵심 | 실패 TR이 BI PASS처럼 보이게 handoff됐다 |

---

## 6. TF 매트릭스

| 대상 문서 | 보강 필요 | 강도 | 이유 |
| --- | --- | --- | --- |
| `SSOT_blockguide-integrated-order.md` | `T` | minor | 실패작/감리 FAIL 입력 시 `Failure Triage` 오더를 명시할 필요가 있다 |
| `treatment-production-harness-v2.md` | `T` | major | 이번 실패의 주 원인인 반복/밀도/감리 출력 연결을 직접 보강해야 한다 |
| `bi-production-harness-v1.md` | `T` | medium | source TR FAIL이 있으면 BI PASS 불가라는 연결 게이트가 필요하다 |
| `treatment-planning-harness.md` | `F` | none | 이번 샘플은 planning보다 production/handoff 문제에 가깝다 |

---

## 7. 최종 결론

- `chaebol_allowance_zero` 현재 TR/BI는 구조상 존재하지만 생산용으론 실패다.
- 이 실패는 단순히 상대 수가 적은 문제가 아니라, 반복 금지 규칙이 감리 수치와 handoff 게이트로 끝까지 강제되지 않은 문제다.
- 후속 보강은 본 SSOT 직접 수정이 아니라, 먼저 `Failure Triage -> TR 반복/밀도 수치화 -> BI source TR gate`를 문서화하는 순서가 맞다.
