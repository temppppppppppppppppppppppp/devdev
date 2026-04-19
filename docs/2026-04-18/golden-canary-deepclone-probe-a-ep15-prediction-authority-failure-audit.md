# Golden Canary Deepclone Probe A Ep15 Prediction-Authority Failure Audit

Date: 2026-04-18
Status: final
Scope: `probe_a_stage3_ep14pressure_r1`를 pressure-survival baseline으로 두고 `from_ep=15`, `target_ep=15` Stage3-only rerun을 통해 current Arc 3 contract 기준 `prediction-authority proof`가 닫히는지 검증했으나, 이번 턴은 성공 proof가 아니라 failure audit으로 종료한다.
Source Anchors:
- [Stage3 ep15 summary](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/stage3_canary_summary.json:1)
- [Stage3 ep15 scorecard](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/loop_canary_scorecard_backfill.json:1)
- [Episode 15 decision row](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/session/decisions.jsonl:1)
- [Episode 15 runtime UI events](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/session/ui_events.jsonl:1)
- [Episode 15 prompt trace](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/session/llm_io.jsonl:1)
- [Episode 14 blueprint](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep14pressure_r1/plans/blueprints/blueprint_0014.txt:1)
- [Arc 3 tactical doc](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep12authority_r1/plans/arcs/arc_003.txt:1)

## Executive Verdict

이번 `ep15 prediction-authority proof`는 `실패`다.

하지만 이 실패는 곧바로 `Probe-style doctrine이 여기서 무너졌다`는 뜻은 아니다. 이번 건은 더 정확히 `ep14 -> ep15 seam conflict`로 읽는 게 맞다.

[summary](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/stage3_canary_summary.json:1) 기준:

- `ep15=FAILED`
- `blueprint_db_count_short:14<15`
- `blueprint_file_count_short:14<15`
- `sink_alignment_status:warn`

즉 accepted artifact 자체가 생성되지 않았다.

## What The System Was Asked To Do

[Arc 3 tactical doc](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep12authority_r1/plans/arcs/arc_003.txt:1) 기준 `ep15`는 아주 분명하다.

- 유가가 `68달러`까지 밀린다
- 박성호 PB가 거의 애원하듯 전화를 건다
- 한시우가 `유가는 80까지 간다`고 단언한다
- 금이 아니라 여전히 `WTI pressure lane` 안에서 prediction authority를 세운다

즉 이번 화의 본질은 `새로운 타겟 제시`가 아니라 `현재 포지션 위에서 광기처럼 들리는 미래 발언을 박아 넣는 것`이다.

## Where The Seam Broke

문제는 [Episode 14 blueprint](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep14pressure_r1/plans/blueprints/blueprint_0014.txt:1)가 이미 너무 강하게 다른 방향의 next-gate를 열었다는 점이다.

`ep14`의 expected ending은:

- `마진콜 경고를 무시하고 다음 타겟인 금 시장 진입을 예고함`

으로 닫힌다.

그리고 [llm_io prompt trace](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/session/llm_io.jsonl:1) 기준 `ep15`의 IMMUTABLE end-hook에는 아예:

- `유가 이야기는 끝났습니다`
- `내일부터는... 금을 담을 바구니를 준비하십시오`

가 들어간다.

즉 system은 `ep15`를 만들려 할 때 동시에 두 가지를 강제받는다.

- 직전 화 ending truth: `금 lane 오픈`
- 이번 화 hard constraint: `WTI 80달러 예언`

이 둘은 tension은 될 수 있어도, 현재 replay guard와 함께 묶이면 같은 턴에서 아주 잘 안 풀린다.

## Replay Guard Collision

이번 실패의 진짜 핵심은 여기다.

`ep15` prompt에는 직전 화 replay 금지 규칙이 들어 있다. 구체적으로 `ep14`에서 이미 소비한 scene family:

- `소음의 차단`
- `새로운 사냥감`
- `궤도의 전환`

을 같은 장소/같은 인물축으로 다시 재연하지 말라고 되어 있다.

그런데 `ep15` hard constraint는 동시에 아래를 요구한다.

- 같은 `강남 원룸 오피스`
- 다시 `박성호 PB의 전화`
- 다시 `WTI 조정에 대한 패닉 반응`

즉 `반복하지 마라`와 `다시 그 축으로 해라`가 같은 프롬프트 안에 함께 있다.

그래서 runtime은 전부 같은 방향으로 죽었다.

[ui_events](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/session/ui_events.jsonl:1) 기준으로 `full_ensemble`은:

- retry 1
- retry 2
- ...
- retry 10

까지 모두 같은 사유로 실패한다.

- `replay/authority/구조 계약 미달 후보만 생성됨`
- `Replay reroute guidance`
- `시작 anchor 계승은 짧게 처리하고 이번 화의 주 장면은 직전 대치의 결과 이후 단계로 이동하라`

즉 모델이 못 쓴 게 아니라, system이 계속 `그건 ep14 반복이야`라고 쳐낸 것이다.

## Additional Structural Evidence

[ui_events](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/session/ui_events.jsonl:1)의 `episode_state_packet_summary`는 또 다른 실마리를 준다.

- `dropped_conflict_count: 3`
- `mid_arc_arc_start_location_override_blocked`
- `mid_arc_cross_stage_packet_location_override_blocked`
- `mid_arc_cross_stage_packet_equipment_override_blocked`

이건 뜻이 꽤 분명하다.

- mid-arc라서 start packet을 함부로 다시 못 쓰고
- location/equipment override도 막혀 있고
- 직전 화 ending hook은 이미 금 lane으로 세게 기울어 있다

즉 `ep15`는 새 공간이나 새 surface로 우회할 여지도 좁은 상태였다.

## Sink Warning Is Secondary

[summary](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/stage3_canary_summary.json:1)의 sink warn도 기록할 필요는 있다.

- `artifact_metadata_missing.content_hash`
- `artifact_metadata_missing.artifact_path`

하지만 이건 원인이라기보다 결과다. 최종 accepted artifact가 없으니 structured sink에 path/hash가 비는 건 자연스럽다. 즉 `structured_sink_drift`는 secondary symptom이지 root cause는 아니다.

## Interpretation

이번 실패는 이렇게 읽는 게 가장 보수적이고 정확하다.

- `doctrine fail`: 아님
- `model quality collapse`: 아님
- `ep14 -> ep15 seam contract collision`: 맞음

더 직설적으로 말하면:

- `ep14`가 금 next-gate를 너무 강하게 열었고
- `ep15`는 아직 WTI 80달러 예언을 요구하며
- 동시에 replay guard가 같은 전화/오피스 confrontation surface를 막아 버렸다

그래서 generator가 10번 연속으로 입구에서 튕겼다.

## Scorecard Read

[Stage3 ep15 scorecard](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage3_ep15predict_r1/logs/loop_canary_scorecard_backfill.json:1) 기준 판정은 아래가 맞다.

- gate result: `gate_fail_prediction_authority_seam_conflict`
- weighted total: `8/100`
- band: `gate_fail`

숫자가 낮은 이유는 단순하다. accepted artifact가 없어서 loop realization 계열 항목을 거의 줄 수 없다. 다만 `anti_contamination`은 문제 아니어서 거기만 최소 점수를 남겼다.

이 숫자는 `작품이 망했다`는 점수가 아니라 `이번 질문은 current seam contract로는 풀리지 않는다`는 뜻이다.

## Best Next Step

다음 한 수는 `ep16`로 밀어붙이는 게 아니다.

가장 좋은 다음 단위는 `ep14 -> ep15 seam audit / repair options`다.

수리 후보는 작게 보면 둘 중 하나다.

- `ep14 hook moderation`
  - 금 next-gate를 너무 강한 direct-next declaration이 아니라 더 약한 foreshadow로 낮춘다
- `ep15 replay surface relaxation`
  - 같은 전화 압박 축을 완전 replay로 치지 않도록 subspace나 confrontation class를 다시 잡는다

어느 쪽이든 먼저 seam audit을 통해 작은 계약 수정안을 고정한 뒤 rerun해야 한다.

## Pass 1

- 이번 failure가 진짜 doctrine fail인지 먼저 의심했다.
- tactical doc와 runtime hard gates를 대조해 `WTI 80` slot 자체는 살아 있음을 확인했다.

## Pass 2

- `ep14` ending hook과 `ep15` hard constraint가 충돌하는지 다시 봤다.
- replay reroute가 한두 번이 아니라 10번 반복된 점을 root evidence로 올렸다.

## Pass 3

- sink warn을 root cause로 과장하지 않도록 분리했다.
- 다음 한 수를 `ep16 직행`이 아니라 `ep14->ep15 seam audit`로 좁히는 게 맞는지 다시 확인했다.

Confidence: 98/100
