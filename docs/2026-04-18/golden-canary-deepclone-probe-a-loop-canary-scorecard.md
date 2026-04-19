# Golden Canary Deepclone Probe A Loop Canary Scorecard

Date: 2026-04-18
Status: final
Scope: `golden_canary_deepclone_probe_a_fullblock_v1`의 bounded canary를 `style score`가 아니라 `loop completion / receipt transport / anti-contamination / anti-fatigue` 기준으로 판정하기 위한 운영 scorecard를 고정한다.
Source Anchors:
- [loop doctrine upgrade plan](C:\Users\PC\Desktop\글도비\docs\2026-04-18\golden-canary-deepclone-probe-a-loop-doctrine-upgrade-plan.md:1)
- [loop improvement options](C:\Users\PC\Desktop\글도비\docs\2026-04-18\golden-canary-deepclone-probe-a-loop-improvement-options.md:1)
- [midcheck adversarial audit](C:\Users\PC\Desktop\글도비\docs\2026-04-18\golden-canary-deepclone-probe-a-midcheck-adversarial-audit.md:1)
- [loop abstraction packet](C:\Users\PC\Desktop\글도비\treatments\preprocess\golden_canary_deepclone_probe_a_fullblock_v1\loop_abstraction_packet.json:1)
- [Phase0 design](C:\Users\PC\Desktop\글도비\treatments\phase0\golden_canary_deepclone_probe_a_fullblock_v1_phase0_design.json:1)
- [work_guard](C:\Users\PC\Desktop\글도비\work_guards\golden_canary_deepclone_probe_a_fullblock_v1.yaml:1)
- [Stage2 canary summary](C:\Users\PC\Desktop\글도비\projects\golden_canary_deepclone_probe_a_stage23probe_r1_arc45only_r2\logs\stage2_canary_summary.json:1)
- [Stage3 canary summary](C:\Users\PC\Desktop\글도비\projects\_canary\probe_a_stage34ab_ep12_r2\logs\stage3_canary_summary.json:1)

## Executive Purpose

이 scorecard의 목적은 `PASS/FAILED + style score`를 대체하는 것이 아니라, 그 옆에서 `loop가 실제로 살아남았는가`를 별도로 재는 것이다.

이 문서는 특히 아래 두 문제를 잡기 위해 만든다.

- `문체 점수는 높지만 receipt/next gate/carryover가 죽는 경우`
- `Probe-style surface가 먹힌 것처럼 보여도 donor contamination이나 fatigue가 쌓이는 경우`

따라서 이 scorecard는 `점수표`라기보다 `bounded realization 진입 전 게이트`다.

## Evaluation Unit

기본 단위는 아래 셋이다.

1. `Stage2 bounded arc tranche`
2. `Stage3 bounded episode tranche`
3. `Stage2 -> Stage3 seam audit`

기본 입력면은 아래를 같이 본다.

- canary summary json
- final artifact / blueprint 본문
- carryover pair 또는 다음 화 opening
- canonical law surface인 `Phase0`, `work_guard`, `loop_abstraction_packet`

summary만 보고 채점하지 않는다. `receipt_visible`, `observer_shift_visible`, `next_gate_visible`는 artifact 본문 기준으로 다시 확인한다.

## Hard Gates

숫자 점수보다 먼저 아래 게이트를 본다. 하나라도 fail이면 총점과 무관하게 `execution hold`다.

### Gate A. Episode Loop Contract Floor

기준:

- `pressure_visible`
- `execution_visible`
- `proof_visible`
- `receipt_visible`
- `observer_shift_visible`
- `next_gate_visible`

판정:

- 6개 중 최소 4개 충족
- `receipt_visible`과 `next_gate_visible`을 동시에 놓치면 즉시 fail

### Gate B. Receipt Transport Gate

기준:

- 현재 tranche에서 structural receipt가 생겼다면, summary/artifact/carryover/opening 중 최소 2개 이상 surface에서 그 흔적이 살아 있어야 한다.

판정:

- receipt가 artifact에만 있고 다음 surface에서 사라지면 fail
- receipt가 generic admiration/profit 언어로만 바뀌면 fail

### Gate C. Anti-Contamination Gate

기준:

- donor noun은 `example family`로만 남아야 한다.
- donor 사건, donor 조직, donor gimmick, donor-specific beat를 canonical law나 실현 output에 직접 복제하면 안 된다.

판정:

- generalized slot 없이 donor surface만 남으면 fail
- donor scene-copy 흔적이 보이면 fail

### Gate D. Lawful Bridge Gate

기준:

- next gate는 lawful bridge여야 한다.
- replay loop, setup-only delay, future beat 선소비는 금지다.

판정:

- 현재 화가 다음 화 사건을 먹어버리면 fail
- 현재 화가 아무 receipt 없이 setup만 늘리면 fail

## Weighted Score

하드게이트 통과 뒤에만 100점 척도로 읽는다.

### 1. `loop_deadline_hit` 15점

질문:

- opening/target tranche 안에서 proof, receipt, next gate가 선언된 기한 안에 나왔는가

채점:

- 15: declared deadline을 모두 지켰다
- 8: 하나는 늦었지만 tranche 안에서는 회수했다
- 0: deadline miss가 loop 체감을 무너뜨렸다

### 2. `structural_receipt_conversion` 20점

질문:

- reward가 generic profit이 아니라 structural asset / access shift / authority receipt로 환전됐는가

채점:

- 20: reward가 명확한 구조 자산으로 잠겼다
- 10: proof는 있으나 receipt가 약하거나 generic하다
- 0: profit 또는 admiration만 남았다

### 3. `receipt_transport_survival` 15점

질문:

- receipt truth가 artifact -> summary -> seam surface로 이동하면서 살아남았는가

채점:

- 15: transport 손실이 없다
- 8: 일부 축약은 있었지만 identity는 살아남는다
- 0: receipt가 flattening됐다

### 4. `carryover_persistence` 15점

질문:

- Stage2 또는 multi-episode seam에서 이전 tranche의 receipt/equipment/access state가 다음 tranche opening에 보존됐는가

채점:

- 15: carryover가 clean하게 이어진다
- 8: 일부 누락이 있지만 다음 tranche driving truth는 살아 있다
- 0: carryover가 깨지거나 generic summary로 대체됐다

비적용 규칙:

- single-episode bounded canary라 carryover면이 없으면 `N/A`로 두고, 총점 환산에서 분모를 줄인다

### 5. `legal_bridge_efficiency` 15점

질문:

- next gate가 replay 없이, future beat 선소비 없이, 현재 화의 합법적 전진으로 열렸는가

채점:

- 15: bridge가 자연스럽고 retry 없이 다음 tranche를 연다
- 8: bridge는 있지만 다소 무겁거나 반복적이다
- 0: replay/setup-only/future beat consumption이 크다

### 6. `anti_contamination_pass` 10점

질문:

- generalized slot law가 donor noun보다 우선했는가

채점:

- 10: example family는 남아도 canonical mechanic은 generalized slot으로 읽힌다
- 5: donor surface가 다소 진하지만 복제선은 넘지 않았다
- 0: donor contamination이 law 또는 output를 지배한다

### 7. `reward_rotation_health` 10점

질문:

- reward/hook가 같은 surface만 반복되지 않았는가

채점:

- 10: reward portfolio와 hook portfolio가 건강하게 회전한다
- 5: rotation 의도는 보이지만 surface 반복이 있다
- 0: 같은 receipt/hook 표면이 닳는다

## Watchlists

점수와 별도로 아래 watchlist를 남긴다.

### Anti-Fatigue Risk

red flags:

- 같은 receipt family가 2개 tranche 이상 연속 반복
- observer shift 없이 proof만 커짐
- next gate가 cliffhanger 또는 meeting notice 한 종류로 고정
- access가 earned access가 아니라 gifted access처럼 보임

### Saturation Trigger

red flags:

- authority gain은 커지는데 새 constraint가 사라짐
- reward 규모는 커지는데 독자 체감은 평평해짐
- signboard와 next gate가 분리되지 않고 같은 장치로만 반복

## Interpretation Bands

- `gate_fail`: 숫자 점수와 무관하게 실행 보류
- `85-100`: strong pass, bounded realization 후보
- `70-84`: pass with repair, 한 번의 targeted fix 후 재실행
- `55-69`: weak pass, doctrine promotion 보류
- `<55`: fail, 현재 tranche 설계 또는 doctrine 해석 재검토

## Operator Reading Order

실제 적용 순서는 아래가 맞다.

1. hard gate부터 본다
2. 그다음 weighted score를 계산한다
3. 마지막에 fatigue/saturation watchlist를 본다

즉 `92점인데 gate_fail`이면 fail이고, `78점인데 gate_all_pass`면 repair-first로 읽는다.

## Immediate Operating Consequence

이 문서부터는 아래를 고정한다.

- `receipt_transport_survival`
- `carryover_persistence`
- `anti_contamination_pass`

이 3개는 더 이상 후보 지표가 아니라 active gate 또는 active score 축이다.

다음 bounded canary부터는 최소한 이 문서 기준으로 수기 score라도 같이 남겨야 한다.

## Pass 1

- midcheck audit가 지적한 `scorecard 선언만 있고 운영면이 없다`는 문제를 직접 닫았다.
- summary 중심이 아니라 artifact/seam/canonical law를 함께 보게 했다.

## Pass 2

- hard gate와 weighted score를 분리해 `점수는 높지만 loop는 죽은` 케이스를 걸러내게 했다.
- anti-fatigue는 즉시 fail gate가 아니라 watchlist로 분리해 과잉 보수화를 막았다.

## Pass 3

- 바로 다음 canary에서 쓸 수 있게 입력면, 채점 기준, 해석 밴드를 한 문서 안에 닫았다.
- `receipt transport`, `carryover`, `contamination`, `fatigue`를 각각 어디서 읽을지 명확히 적었다.

Confidence: 97/100
