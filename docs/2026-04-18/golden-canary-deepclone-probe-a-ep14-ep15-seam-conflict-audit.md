# Golden Canary Deepclone Probe A Ep14-Ep15 Seam Conflict Audit

Date: 2026-04-18
Status: final
Scope: `probe_a_stage3_ep14pressure_r1 -> probe_a_stage3_ep15predict_r1` bounded canary chain을 기준으로, `ep15` failure를 개별 화수 미스가 아니라 reusable seam-conflict pattern으로 분석한다. 목표는 `ep15` 임시 봉합이 아니라 future tranche에도 적용 가능한 근본 개선 포인트를 좁히는 것이다.
Source Anchors:
- [Episode 14 blueprint](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep14pressure_r1/plans/blueprints/blueprint_0014.txt:1)
- [Episode 15 failure audit](/c:/Users/PC/Desktop/글도비/docs/2026-04-18/golden-canary-deepclone-probe-a-ep15-prediction-authority-failure-audit.md:1)
- [Episode 15 summary](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/stage3_canary_summary.json:1)
- [Episode 15 scorecard](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/loop_canary_scorecard_backfill.json:1)
- [Episode 15 prompt trace](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/session/llm_io.jsonl:1)
- [Episode 15 UI events](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/session/ui_events.jsonl:1)
- [Arc 3 tactical doc](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep12authority_r1/plans/arcs/arc_003.txt:18)

## Executive Verdict

이번 seam은 `특정 화수 미스`라기보다 `세 가지 계약이 서로 물어뜯는 구조 충돌`이다.

충돌한 축은 아래 셋이다.

- `next-gate strength`
- `replay guard strictness`
- `mid-arc carryover rigidity`

그래서 이번 failure는 `ep15만 고치면 끝`이 아니라, 앞으로도 비슷한 압박-예언-전환 구간에서 반복될 수 있는 일반 패턴으로 보는 게 맞다.

## Conflict Map

### 1. Ep14 Ends Too Hard Toward Gold

[Episode 14 blueprint](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep14pressure_r1/plans/blueprints/blueprint_0014.txt:11)부터 이미 방향이 확실하다.

- 유가 차트에서 시선이 벗어난다
- 금 가격 상승세를 읽는다
- `새로운 사냥감`으로 금을 잡는다
- [예상 결말](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep14pressure_r1/plans/blueprints/blueprint_0014.txt:66)는 `다음 타겟인 금 시장 진입을 예고함`으로 닫힌다

즉 `ep14`는 단순 foreshadow가 아니라 거의 `target handoff`처럼 끝난다.

### 2. Ep15 Still Demands WTI Prediction Authority

반면 [Arc 3 tactical doc](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep12authority_r1/plans/arcs/arc_003.txt:22)는 `ep15`에 매우 강한 WTI slot을 요구한다.

- 유가 `68달러` 하락
- 박성호 PB의 패닉콜
- `유가는 80까지 간다`
- 에콰도르 직전 공포 버티기

즉 `ep15`의 본질은 `다음 자산 탐색`이 아니라 `현재 원유 포지션 위에서 광기처럼 들리는 예언 권위`다.

### 3. Replay Guard Forbids The Most Natural Surface

[Episode 15 prompt trace](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/session/llm_io.jsonl:1)는 여기에 세 번째 잠금을 건다.

- 직전 화 replay 금지
- 같은 장소/같은 인물축 재연 금지
- 이미 소비한 scene family:
  - `소음의 차단`
  - `새로운 사냥감`
  - `궤도의 전환`

그리고 같은 trace 안에서 또:

- 직전 화 ending hook: `유가 이야기는 끝났습니다 ... 금을 담을 바구니를 준비하십시오`
- 이번 화 hard constraint: `유가는 80달러까지 간다`

를 동시에 강제한다.

즉 시스템은 사실상 이렇게 말하고 있다.

- `금으로 넘어가라`
- `하지만 아직 WTI로 예언해라`
- `그리고 그걸 가장 자연스러운 전화/오피스 confrontation surface로는 하지 마라`

이 조합이면 generator가 안정적으로 들어갈 수 있는 입구가 급격히 줄어든다.

## Runtime Behavior Supports The Same Reading

[Episode 15 summary](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/stage3_canary_summary.json:1)와 [UI events](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/session/ui_events.jsonl:1)를 합쳐 보면 행동 패턴이 단순하다.

- `full_ensemble`가 10회 모두 실패
- 실패 사유는 전부 `replay/authority/구조 계약 미달`
- reroute guidance도 계속 동일
  - `시작 anchor 계승은 짧게 처리`
  - `직전 대치의 결과 이후 단계로 이동`

즉 모델이 엉뚱한 걸 써서 죽은 게 아니라, allowed surface가 너무 좁아져서 계속 같은 벽에 부딪힌 것이다.

## Why This Is Generalizable

이 패턴은 `ep14/15`에만 고유하지 않다. 웹소 대리만족 루프를 길게 돌리면 자주 생긴다.

- `pressure episode`가 다음 자산/다음 전장 foreshadow를 연다
- 바로 다음 화는 아직 현재 전장의 고비를 통과해야 한다
- replay guard는 같은 장소/같은 NPC confrontation을 재탕으로 본다
- carryover packet은 또 동일 장소/동일 장비/동일 포지션을 강하게 붙든다

이 네 가지가 한 번에 겹치면, generator는:

- 새 축으로 가면 hard constraint 위반
- 현재 축으로 가면 replay 위반
- subspace로 빼면 carryover rigidity와 충돌

하게 된다.

즉 이번 failure는 `Probe A 특유의 문제`보다 `장기 루프형 작품에서 next-gate와 replay guard를 동시에 강하게 잡을 때 생기는 보편 seam risk`다.

## Reusable Repair Candidates

여기서 바로 떠오르는 근본 개선 후보는 네 가지다.

### A. Next-Gate Strength Modulator

원칙:

- 다음 화가 아직 현재 자산/현재 전장을 소화해야 할 때는
- `next gate`를 `direct target handoff`가 아니라 `soft foreshadow`로 제한한다

이번 케이스라면:

- `금 시장 진입을 예고함`

보다

- `금 사이클의 서막을 감지함`
- `원유 이후의 체스판이 열릴 조짐을 포착함`

같은 수준이 더 안전했다.

이건 특정 화수 봉합이 아니라 `next-gate 강도 규칙`으로 일반화할 수 있다.

### B. Lawful Repetition Window

원칙:

- 같은 장소
- 같은 인물축
- 같은 커뮤니케이션 매체

라도 아래 중 둘 이상이 달라지면 replay로 치지 않는다.

- 시장 상태
- 권력 위계
- 의사결정 임계값
- 장면 목표

이번 케이스는 `같은 오피스 + 같은 전화`라도:

- 6주 횡보 압박 후
- 금 foreshadow를 이미 본 뒤
- `80달러`라는 더 높은 예언 권위를 세우는 장면

이므로 완전한 replay와는 다르다. 이걸 system이 lawful repetition으로 읽을 수 있어야 한다.

### C. Mid-Arc Carryover Flex Band

원칙:

- mid-arc에서는 carryover packet이 위치/장비/포지션을 유지하더라도
- 장면 surface까지 과도하게 고정하면 안 된다

즉:

- `same location truth`
- `same equipment truth`

는 유지하되,

- 같은 방 안의 시선
- 같은 전화의 역할
- 같은 confrontation class

는 더 유연하게 변형할 수 있게 해야 한다.

이번 failure trace의 `mid_arc_*_override_blocked`는 바로 이 유연성 부족을 보여준다.

### D. Cross-Target Transition Fence

원칙:

- 새로운 자산/전장(target)을 열었으면
- 다음 화가 아직 이전 target의 결전을 처리 중인지 먼저 본다

만약 `current target unresolved`이면:

- 새 target은 briefing/foreshadow만 허용
- command형 next directive 금지

이 fence가 있으면 `ep14`가 `금을 담을 바구니를 준비하십시오`까지 가지 않고 멈췄을 가능성이 크다.

## What Not To Do

이번 seam에서 피해야 할 것도 분명하다.

- `ep15 hard constraint를 약화시켜 버리기`
  - 그러면 Arc 3 tactical contract 자체를 잃는다
- `replay guard를 전반적으로 느슨하게 풀기`
  - 그러면 실제 반복 회귀가 다시 살아난다
- `금 foreshadow를 완전히 제거하기`
  - 그러면 ep14의 전략적 전진 의미가 사라진다

즉 필요한 건 `완전 삭제`가 아니라 `강도와 허용 범위의 조절`이다.

## Recommended Next Step

다음 한 수는 코드 패치 전에 `repair design memo`를 아주 작게 하나 더 만드는 것이다.

우선순위는 이 순서가 맞다.

1. `next-gate strength modulator` 초안
2. `lawful repetition window` 규칙 초안
3. 그다음 `ep14 -> ep15 repair rerun` 설계

즉 바로 구현보다, 먼저 `어디를 어떻게 완화해야 replay와 forward motion을 동시에 살릴 수 있는지`를 더 명시적으로 고정하는 게 좋다.

## Pass 1

- `ep15` failure를 개별 화수 미스로 볼지, seam 문제로 볼지부터 다시 점검했다.
- arc tactical doc, ep14 ending, ep15 hard constraint가 같은 방향을 보고 있는지 대조했다.

## Pass 2

- replay guard와 mid-arc carryover block가 실제로 입구를 좁혔는지 runtime evidence와 함께 재확인했다.
- `structured_sink_drift`는 root cause가 아니라 secondary symptom으로 강등했다.

## Pass 3

- 이번 결론을 `ep15만 고치자`가 아니라 `재사용 가능한 시스템 개선 후보`로 일반화해도 과장 아닌지 다시 검토했다.
- 다음 한 수를 구현 직행이 아니라 작은 repair design memo로 두는 게 맞는지 재확인했다.

Confidence: 98/100
