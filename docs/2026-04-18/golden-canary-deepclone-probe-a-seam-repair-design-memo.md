# Golden Canary Deepclone Probe A Seam Repair Design Memo

Date: 2026-04-18
Status: final
Scope: [ep14-ep15 seam conflict audit](/c:/Users/PC/Desktop/글도비/docs/2026-04-18/golden-canary-deepclone-probe-a-ep14-ep15-seam-conflict-audit.md:1)에서 드러난 구조 충돌을 실제 repair branch 후보로 변환한다. 목표는 `ep15 응급처치`가 아니라, 비슷한 압박-예언-전환 seam 전반에 재사용 가능한 system-side repair shape를 고정하는 것이다.
Source Anchors:
- [Seam conflict audit](/c:/Users/PC/Desktop/글도비/docs/2026-04-18/golden-canary-deepclone-probe-a-ep14-ep15-seam-conflict-audit.md:1)
- [Episode 14 blueprint](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep14pressure_r1/plans/blueprints/blueprint_0014.txt:1)
- [Episode 15 failure audit](/c:/Users/PC/Desktop/글도비/docs/2026-04-18/golden-canary-deepclone-probe-a-ep15-prediction-authority-failure-audit.md:1)
- [Episode 15 scorecard](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/loop_canary_scorecard_backfill.json:1)
- [Episode 15 prompt trace](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/session/llm_io.jsonl:1)
- [Arc 3 tactical doc](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep12authority_r1/plans/arcs/arc_003.txt:18)

## Executive Direction

이번 repair branch의 목적은 하나다.

`next-gate`, `replay guard`, `mid-arc carryover`가 동시에 강하게 걸릴 때도, 시스템이 lawful forward motion을 열 수 있게 만드는 것.

즉 지금 필요한 건:

- replay guard를 무너뜨리는 것
- 다음 target foreshadow를 없애는 것

이 아니다.

대신:

- 강도 조절
- lawful repetition 허용 범위 명시
- mid-arc 유연성 회복

을 해 주는 쪽이 맞다.

## Root Cause Recap

이번 seam은 세 축이 동시에 물어뜯었다.

1. `ep14`가 금 next-gate를 너무 강하게 닫음
2. `ep15`는 여전히 `WTI 80달러 예언`을 강하게 요구함
3. replay guard는 같은 오피스/전화 confrontation surface를 재연으로 간주함

이 상태에서 carryover packet은 또:

- 위치 유지
- 장비 유지
- 포지션 유지

를 강하게 고정한다.

그래서 generator 입장에선:

- current target으로 가면 replay 위반
- next target으로 가면 hard constraint 위반
- 새 공간으로 빼면 carryover rigidity와 충돌

이 된다.

## Design Goal

repair는 아래 4가지를 동시에 만족해야 한다.

- Arc tactical contract는 유지할 것
- replay guard의 진짜 효용은 보존할 것
- 같은 장소/같은 인물축도 lawful variation이면 허용할 것
- next-gate를 열되, unresolved current target을 먹어치우지 않게 할 것

## Repair Candidate A

### Next-Gate Strength Modulator

핵심 아이디어:

- 다음 화가 아직 `current target`의 결정을 요구하면
- 이번 화 ending hook의 `new target declaration` 강도를 자동으로 낮춘다

실무 규칙으로는 이렇게 정리할 수 있다.

- `direct handoff`
  - 금지 조건:
    - next episode hard constraint가 현재 target 위에 남아 있음
    - current target payoff/proof가 아직 unresolved
- `soft foreshadow`
  - 허용 조건:
    - 새로운 target의 존재만 감지
    - command형 directive는 금지

이번 케이스라면:

- 현재 문장
  - `다음 타겟인 금 시장 진입을 예고함`
  - `금을 담을 바구니를 준비하십시오`
- 더 안전한 문장 family
  - `금 사이클의 서막을 감지함`
  - `원유 이후의 체스판이 어렴풋이 열린다`

즉 next-gate를 없애는 게 아니라, `강도`를 낮추는 것이다.

### 추천 적용 위치

- 1순위: Stage3 ending hook / expected ending 가드
- 2순위: work_guard의 loop contract
- 3순위: loop scorecard의 `cross-target transition` watch 항목

## Repair Candidate B

### Lawful Repetition Window

핵심 아이디어:

같은:

- 장소
- 인물
- 통신 매체

라도 아래 중 둘 이상이 변하면 `replay`가 아니라 `lawful continuation`으로 본다.

- 시장 상태
- 장면 목표
- 권력 위계
- 의사결정 임계값
- 정보 비대칭 수준

이번 케이스에 대입하면:

- `ep14`
  - 마진콜 경고를 파쇄하고 금 cycle을 감지
- `ep15`
  - 68달러 조정 속에서 `80달러` 예언 권위를 박아야 함

이 둘은 같은 전화 축이더라도 장면 목적과 위험 강도가 다르다. 이 차이를 system이 읽을 수 있어야 한다.

### 추천 판정 규칙

아래 중 둘 이상이면 replay penalty를 약화한다.

- `market_state_changed=true`
- `authority_delta_changed=true`
- `thesis_strength_changed=true`
- `scene_goal_changed=true`

## Repair Candidate C

### Mid-Arc Carryover Flex Band

핵심 아이디어:

mid-arc에서는 carryover truth를 유지하되, scene surface까지 고정하지 않는다.

지켜야 하는 것:

- same asset truth
- same position truth
- same place family truth
- same carried authority object

유연하게 풀어야 하는 것:

- exact subspace
- confrontation class
- mediation line
- timing surface

즉:

- `원룸 오피스`는 유지
- 하지만 `데스크 앞 직접 통화 대치`만 강제하진 않음

같은 식의 유연성이 필요하다.

### 추천 적용 위치

- EpisodeStatePacket rewrite policy
- mid-arc override blocked 계열 규칙
- source_anchor_summary 기반 replay 판정기

## Repair Candidate D

### Cross-Target Transition Fence

핵심 아이디어:

새 target을 여는 타이밍을 `current target unresolved` 여부와 연결한다.

간단한 판정은 이렇다.

- `current_target_unresolved=true`
- `next_episode_hard_constraint_same_target=true`

이면:

- next target은 `foreshadow only`
- command형 directive 금지
- explicit switching verb 금지

이 fence가 있으면 `ep14`는 금을 열더라도 `시장 전환 선언`까지는 가지 않았을 가능성이 크다.

## Implementation Order

이번 repair branch는 작게 가는 게 맞다. 추천 순서는 이렇다.

1. `Next-Gate Strength Modulator` 설계 반영
2. `Lawful Repetition Window` 설계 반영
3. `ep14 -> ep15` bounded rerun
4. 필요하면 그 다음에만 `Mid-Arc Carryover Flex Band`를 건드린다

이 순서를 추천하는 이유는 단순하다.

- A, B는 prompt/contract layer에서 비교적 국소적으로 실험 가능
- C는 carryover truth surface에 손대므로 범위가 커진다
- D는 scorecard/watch와 함께 규칙화할 때 가장 안정적이다

## Validation Plan

수리 검증도 bounded로 간다.

### Validation 1

- 대상: `ep14 -> ep15`
- 목표: `ep15 prediction-authority`가 accepted artifact까지 도달하는지

### Validation 2

- 대상: `ep15 -> ep16`
- 목표: seam repair가 stop line을 깨지 않고 `에콰도르 쇼크`로 자연 연결되는지

### Validation 3

- 대상: 다른 pressure-to-prophecy seam 1건
- 목표: 이번 수리가 특정 화수 봉합이 아니라 reusable rule인지 확인

## No-Go Rules

이번 repair branch에서 하지 말아야 할 것도 분명하다.

- replay guard를 global하게 약화시키지 말 것
- `ep15`의 WTI 80달러 slot을 삭제하지 말 것
- `ep14`의 금 foreshadow를 완전히 제거하지 말 것
- carryover truth를 단순 loose mode로 풀어 버리지 말 것

즉 이번 repair는 `완화`이지 `포기`가 아니다.

## Suggested Repair Hypothesis

지금 단계에서 제일 가능성 높은 가설은 이거다.

`ep15 failure의 주원인은 model 품질이 아니라, ep14 ending hook의 target handoff 강도와 ep15 replay guard의 허용 범위가 동시에 너무 빡빡했던 것이다.`

따라서 가장 먼저 실험할 조합은:

- A: next-gate downshift
- B: lawful repetition 허용

이다.

이 둘로도 안 풀리면 그때 C까지 보자.

## Pass 1

- seam audit에서 뽑은 원인들을 repair candidate로 바꿀 수 있는지 먼저 점검했다.
- 전역 완화가 아니라 국소 제어로 갈 수 있는 축만 남겼다.

## Pass 2

- 각 후보가 실제로 어디에 걸려야 하는지 prompt/contract/carryover 층으로 다시 분해했다.
- 적용 순서를 잘못 잡아 큰 리스크를 만드는 후보를 뒤로 뺐다.

## Pass 3

- 이번 메모가 `ep15 응급처치`가 아니라 reusable repair branch로 읽혀도 과장 아닌지 다시 확인했다.
- 다음 액션을 구현 직행이 아니라 bounded validation 포함한 설계 branch로 두는 게 맞는지 재검토했다.

Confidence: 98/100
