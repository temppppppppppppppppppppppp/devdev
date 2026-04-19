# Golden Canary Deepclone Probe A A-B Repair Implementation Spec

Date: 2026-04-18
Status: final
Scope: [seam repair design memo](/c:/Users/PC/Desktop/글도비/docs/2026-04-18/golden-canary-deepclone-probe-a-seam-repair-design-memo.md:1)를 코드 착수 가능한 수준으로 구체화한다. 이번 tranche는 `A = Next-Gate Strength Modulator`와 `B = Lawful Repetition Window`만 다루고, `C = Mid-Arc Carryover Flex Band`는 보류한다.
Source Anchors:
- [A-B repair design memo](/c:/Users/PC/Desktop/글도비/docs/2026-04-18/golden-canary-deepclone-probe-a-seam-repair-design-memo.md:1)
- [Ep14-Ep15 seam conflict audit](/c:/Users/PC/Desktop/글도비/docs/2026-04-18/golden-canary-deepclone-probe-a-ep14-ep15-seam-conflict-audit.md:1)
- [Episode 14 blueprint](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep14pressure_r1/plans/blueprints/blueprint_0014.txt:1)
- [Episode 15 failure audit](/c:/Users/PC/Desktop/글도비/docs/2026-04-18/golden-canary-deepclone-probe-a-ep15-prediction-authority-failure-audit.md:1)

## Executive Intent

이번 spec의 목적은 단순하다.

- `ep15`를 억지로 통과시키는 것이 아니라
- `next-gate 과강조`와 `replay guard 과경직`이 동시에 발생할 때
- Stage3가 lawful forward motion을 잃지 않도록 국소적으로 완화한다

즉 이번 patch는:

- prompt 계약
- validator 판정
- retry guidance

까지만 건드린다.

`episode_state_arbiter` 같은 carryover truth surface는 이번 tranche에서 건드리지 않는다.

## Tranche Boundary

### In Scope

- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- 관련 단위 테스트

### Out Of Scope

- `modules/core/episode_state_arbiter.py`
- cross-stage packet authority precedence 변경
- Stage2 arc tactical rewrite
- broad replay guard global loosening

이번 tranche는 `A+B만` 다룬다.

## Patch Surface 1

### `blueprint_constraint_compiler.py`

핵심 역할:

- `episode_progression_packet` 생성
- `surface_guidance` 생성
- `future_beat_reservations` 생성

현재 seam conflict의 진원지이기도 하다. 이유는:

- [1054-1237] `blocked_scene_families`를 이전 화 기준으로 빌드
- [1241-1288] replay 회피용 `surface_guidance`를 하드하게 넣음
- [1291-1328] future beat reservation을 강하게 넣음

### Patch A1

새 packet field를 추가한다.

- `next_gate_strength_mode`
  - 값 예시:
    - `direct_handoff_ok`
    - `foreshadow_only`

판정 휴리스틱:

- `stop_line.content`가 다음 화에서도 현재 target의 unresolved payoff/proof를 강하게 요구하고
- `must_focus.content` 안에 새로운 target/자산/전장 씨앗이 동시에 보이면
- `foreshadow_only`

이번 케이스에선:

- ep14 must_focus: 금 조짐이 열림
- ep15 stop_line/current hard slot: 아직 WTI 예언이 남아 있음

이므로 `foreshadow_only`가 맞다.

### Patch A2

`_build_episode_progression_surface_guidance()`에서 `next_gate_strength_mode=foreshadow_only`면 아래 guidance family를 추가한다.

- `새로운 자산/전장을 감지해도 이번 화 ending에서는 direct handoff나 command형 지시로 닫지 말라. foreshadow 수준으로만 남겨라.`
- `current target unresolved 상태에서는 next target을 선언형 종결 문장으로 확정하지 말라.`

즉 이 guidance가 `ep14` 생성 시점부터 prompt에 들어가게 만든다.

### Patch B1

같은 함수에서 새 field를 추가한다.

- `lawful_repetition_window`
  - 예시:
    - `allow_same_location_if_goal_changes`
    - `allow_same_counterparty_if_market_state_changes`
    - `allow_same_channel_if_authority_delta_changes`

판정 휴리스틱:

- same-location 축이더라도
- must_focus가 직전 화와 다른 의사결정 단계나 위험 임계값을 요구하면
- replay guard를 절대 금지가 아니라 `짧은 carryover + 새 장면 목표`로 읽게 한다

## Patch Surface 2

### `blueprint_ensemble.py`

핵심 역할:

- producer prompt에 progression packet을 인간/LLM이 읽는 constraint 문장으로 펼친다

직접 target:

- [1460-1503] `blocked_scene_families`, `surface_guidance`, `future_beat_reservations`를 하드라인으로 주입

### Patch A3

`next_gate_strength_mode=foreshadow_only`일 때 새 constraint block을 명시적으로 출력한다.

예시 문구:

- `[Next-Gate Strength Guard]`
- `이번 화에서 새로운 target은 예감/감지/서막 수준으로만 남겨라`
- `직접 지시, handoff 선언, 내일부터/이제부터 류 command형 closing을 금지한다`

### Patch B2

`lawful_repetition_window`가 있으면 replay block 아래에 예외 허용 문구를 붙인다.

예시:

- `같은 장소/같은 통화 채널이라도 시장 상태, 권력 위계, 장면 목표가 바뀌면 lawful continuation으로 본다`
- `직전 화 confrontation을 장면 요약으로 반복하지 말되, 더 높은 임계값의 새 결정 장면은 허용한다`

중요한 건 `guard 삭제`가 아니라 `guard 예외 조건을 명문화`하는 것이다.

## Patch Surface 3

### `unified_blueprint_validator.py`

핵심 역할:

- Python pre-validation에서 `episode_progression` replay를 CRITICAL로 띄운다

직접 target:

- [2196-2311] `_collect_episode_progression_issues()`

현재 문제:

- same location + same characters가 2개 이상 겹치면
- 거의 자동으로 `CRITICAL/episode_progression`으로 올라간다

이번 seam처럼:

- location은 같고
- counterparty도 같지만
- 시장 상태와 장면 목표는 다를 때

이 차이를 읽지 못한다.

### Patch B3

`progression_packet`에서 `lawful_repetition_window`를 읽고, 아래 조건이면 CRITICAL replay 판정을 완화한다.

완화 조건 예시:

- scene goal이 blocked family label과 실질적으로 다름
- scene type이 바뀜
- must_focus가 새로운 임계값/예언/승인 축을 직접 요구함

최소 구현은:

- `matched_families`를 쌓기 전에
- `lawful_repetition_window`가 있으면
- `scene.type`, `scene.goal/summary`, `must_focus`를 함께 보고 skip 가능성 판단

즉 validator도 prompt와 같은 법을 읽어야 한다.

## Patch Surface 4

### `three_phase_blueprint_runtime.py`

핵심 역할:

- retry 시 operator-facing reroute guidance를 만든다

직접 target:

- [1538-1562] `_compose_replay_reroute_reason()`

현재 문제:

- guidance가 항상
  - `직전 대치 이후 단계로 이동하라`

로만 나온다

그래서 lawful repetition이 가능한 seam에서도 계속 `다른 장면으로 가라`는 쪽으로만 민다.

### Patch B4

`surface_guidance`와 별도로, lawful repetition이 설정된 packet이면 retry guidance에 아래 계열을 추가한다.

- `같은 공간/같은 채널을 쓰더라도 장면 목표와 시장 상태를 바꿔 새로운 결정 장면으로 전진하라`
- `직전 대치의 요약 반복은 금지하지만, higher-stakes decision pass는 허용된다`

이렇게 해야 retry가 실제 해결 방향으로 유도된다.

## Proposed Validation Set

이번 patch는 아래 순서로 검증한다.

### Test 1

`tests/test_blueprint_ensemble_generate_ensemble.py`

추가할 것:

- `foreshadow_only`일 때 prompt에 direct handoff 금지 문구가 노출되는지
- `lawful_repetition_window`일 때 replay guard 아래 예외 문구가 노출되는지

### Test 2

`tests/test_unified_blueprint_validator_lane_c.py`

추가할 것:

- same location + same counterparty라도
- must_focus가 higher-stakes prediction axis면
- `episode_progression` CRITICAL로 바로 뜨지 않는 케이스

### Test 3

`tests/test_blueprint_patch_mode.py`

추가할 것:

- replay reroute guidance가 lawful repetition 힌트를 같이 싣는지

### Test 4

bounded runtime rerun

- `ep14 -> ep15`
  - 1차 목표: accepted artifact 생성
- 성공 시 `ep15 -> ep16`
  - 2차 목표: fix가 stop line을 깨지 않는지 확인

## No-Go Rules

이번 구현에서 하면 안 되는 것:

- replay guard 자체를 약화하는 global flag 추가
- validator에서 same location/same counterparty를 전부 통과시키는 broad exemption
- carryover truth surface를 느슨하게 만드는 packet precedence 수정
- Stage2 arc tactical doc 수정으로 문제를 우회

즉 이번 patch는 `정교한 예외 창`이지 `규칙 해제`가 아니다.

## Recommended Commit Shape

이번 tranche는 하나의 commit으로 너무 크게 묶지 않는 게 좋다.

추천 순서는:

1. compiler + ensemble prompt surface
2. validator relaxation
3. runtime reroute guidance
4. tests
5. bounded rerun

이 순서면 원인-표면-판정이 한 단계씩 맞물리는지 보기 좋다.

## Exit Criteria

이번 A+B tranche가 성공으로 간주되려면:

- `ep14 -> ep15` rerun에서 적어도 accepted artifact가 생성될 것
- `ep15`가 replay CRITICAL만으로 입구에서 죽지 않을 것
- `ep16` rerun에서 stop line 파괴가 없을 것
- global replay guard regression test가 깨지지 않을 것

이 넷을 동시에 만족해야 한다.

## Pass 1

- audit와 repair memo를 implementation surface에 매핑했다.
- 어떤 파일이 원인 생산, prompt 주입, validator 판정, retry 유도에 각각 대응하는지 분해했다.

## Pass 2

- 이번 tranche에서 `C`까지 욕심내지 않고 `A+B`만 다루는 게 맞는지 다시 점검했다.
- broad loosening으로 흘러갈 위험이 있는 안을 제외했다.

## Pass 3

- 테스트 순서와 runtime rerun 순서가 bounded하게 잡혔는지 재확인했다.
- 이번 spec이 실제 코드 착수 문서로 써도 충분한지 다시 검토했다.

Confidence: 98/100
