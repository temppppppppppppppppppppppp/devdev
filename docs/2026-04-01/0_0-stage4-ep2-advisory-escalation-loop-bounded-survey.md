Date: 2026-04-01
Status: final
Confidence: 96%
Scope: `0_0` canary `canary_0_0_stage34_arc2_ctxnorm_r1`, Stage4 `ep2` advisory escalation loop only
Evidence Path: `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-evidence.json`
Related Docs:
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-context-normalization-runtime-closure-audit.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`

## 1. Answer First

`ep2` Stage4 loop의 주원인은 `Stage2/3 context normalization` 회귀가 아니다.

실제 원인은 2단 결합이다.

1. `FlashbackVerifier`가 `ep1`의 "휴대전화 화면의 통화 버튼"과 `ep2`의 "폴더폰 / 종료 버튼 / 폴더를 닫음"을 `스마트폰 vs 폴더폰` 물리 모순으로 과해석해 `Flashback` MAJOR advisory를 반복 발화시킨다.
2. 그 advisory가 `PASS -> PASS_WITH_FIX`로 올라간 뒤에도 local `fix_pack`이 준비되지 않아 `Lane2-G2b`에서 `strong_advisory_escalation_non_local_fix` REJECT로 강등되고, retry lane은 `TF-PATCH-GATE`와 `TF-4`를 거쳐 patch 대신 rewrite를 반복한다.

마지막 `Round 10`은 별도 seam이다.

- Director는 `PASS_WITH_FIX(96)`까지 다시 올렸지만,
- 최종 `round_execution`은 `REJECT`로 끝났다.
- 기존 closure audit/evidence가 이미 `R10 gate_basis=post_select_conflict`로 기록하고 있고,
- live `ui_events`도 Director provisional pass 뒤 즉시 `Round 10/10 REJECT`를 찍는다.

즉 `ep2`는

- 중반부에는 `Flashback` strong-advisory loop,
- 마지막에는 `post_select_conflict` downgrade

가 번갈아 걸린 케이스다.

## 2. Hard Conclusions

### 2.1 Strong advisory loop의 직접 발화 family는 `Flashback`

Live `ui_events`에서 `ep2` strong-advisory 라운드는 계속 `FlashbackVerifier`가 먼저 뜬다.

- round 2: `Flashback` MAJOR 후 `PASS -> PASS_WITH_FIX` 강등
- round 4, 5, 6, 9: `Flashback` MAJOR 후 `strong_advisory_escalation_non_local_fix`

근거:

- `projects/canary_0_0_stage34_arc2_ctxnorm_r1/logs/session/ui_events.jsonl`
  - `2026-04-01T11:38:20` round 1 detail
  - `2026-04-01T11:57:28` round 3 detail
  - `2026-04-01T12:05:02` round 4 detail
  - `2026-04-01T12:11:03` round 5 detail
  - `2026-04-01T12:28:05` round 8 detail
  - `2026-04-01T12:32:19` round 9 detail

### 2.2 이 `Flashback` advisory는 high-precision truth hit가 아니라 과해석 성격이 강하다

`ep1` authoritative draft는 이미 `폴더폰`과 `휴대전화 화면의 통화 버튼`을 함께 쓴다.

- [ep_0001.txt](C:/Users/User/Desktop/글도비/projects/0_0/drafts/ep_0001.txt#L93)
- [ep_0001.txt](C:/Users/User/Desktop/글도비/projects/0_0/drafts/ep_0001.txt#L95)
- [ep_0001.txt](C:/Users/User/Desktop/글도비/projects/0_0/drafts/ep_0001.txt#L99)

`ep2` final-round selected manuscript도 같은 계열 표현이다.

- `폴더폰`을 손에 쥔다
- `휴대전화 화면의 종료 버튼`을 누른다
- 이어서 `폴더를 닫는다`

근거:

- [selected_before_fix__B.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ctxnorm_r1/logs/artifacts/stage4/ep_0002/attempt_10/selected_before_fix__B.txt#L5)
- [selected_before_fix__B.txt](C:/Users/User/Desktop/글도비/projects/canary_0_0_stage34_arc2_ctxnorm_r1/logs/artifacts/stage4/ep_0002/attempt_10/selected_before_fix__B.txt#L31)

따라서 현재 advisory는 `화면의 버튼`을 곧바로 `터치스크린/스마트폰`으로 읽어버린다.
이건 artifact truth보다 detector inference가 더 앞선 경우다.

### 2.3 loop가 길어진 직접 메커니즘은 `local fix contract fail-close`

코드상 strong advisory는 plain `PASS`를 `PASS_WITH_FIX`로 올린다.

- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2077)

하지만 local fix contract가 준비되지 않으면 곧바로 `REJECT`로 강등한다.

- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2159)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2169)

retry lane은 non-ready `fix_pack`이면 patch를 막고 rewrite로 보낸다.

- [stage4_retry_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_retry_runtime.py#L1032)
- [stage4_retry_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_retry_runtime.py#L1042)

그리고 `missing_patch_targets`가 연속되면 `TF-4`로 full rewrite 전환이 붙는다.

- [stage4_retry_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_retry_runtime.py#L976)
- [stage4_retry_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_retry_runtime.py#L990)

live evidence도 이 흐름과 일치한다.

- `2026-04-01T11:58:20` round 4: `TF-PATCH-GATE`
- `2026-04-01T12:06:01` round 5: `TF-4 patch_targets 연속 부재`
- `2026-04-01T12:12:04` round 6: `TF-4 patch_targets 연속 부재`
- `2026-04-01T12:30:04` round 9: `TF-PATCH-GATE`

### 2.4 Round 10 최종 실패는 advisory 하나만의 문제가 아니라 `post_select_conflict` downgrade다

Final round live `ui_events`는 이렇게 끝난다.

1. Director result: `PASS_WITH_FIX | 초기: PASS | gate: strong_advisory_escalation | 점수: 96 | 선택: 후보 B`
2. 직후 round_execution: `Round 10/10 REJECT -> 다음 라운드`

근거:

- `projects/canary_0_0_stage34_arc2_ctxnorm_r1/logs/session/ui_events.jsonl`
  - `2026-04-01T12:33:04` director result
  - `2026-04-01T12:33:30` round_execution result

그리고 canonical closure audit/evidence는 이미 `R10 gate_basis=post_select_conflict`로 정리돼 있다.

- [0_0-stage2-stage3-stage4-readiness-context-normalization-runtime-closure-audit.md](C:/Users/User/Desktop/글도비/docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-context-normalization-runtime-closure-audit.md)
- [0_0-stage2-stage3-stage4-readiness-context-normalization-runtime-closure-evidence.json](C:/Users/User/Desktop/글도비/docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-context-normalization-runtime-closure-evidence.json)

이 downgrade path는 코드상 provisional pass를 post-select conflict로 뒤집는 seam과 맞는다.

- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L4168)
- [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L4205)

그리고 reject snapshot은 이 경우 `fix_pack`를 비우고 rationale 일부를 지운다.

- [stage4_reject_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_reject_runtime.py#L385)
- [stage4_reject_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_reject_runtime.py#L392)
- [stage4_reject_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_reject_runtime.py#L582)

## 3. Medium-Confidence Conclusions

### 3.1 마지막 `post_select_conflict`의 실제 본문 충돌은 `Flashback`보다는 opening carryover/continuity 쪽일 가능성이 높다

round 9 Director warnings는 모든 후보에 대해 `[V66.1] 직전 화의 지속 압박/위협이 opening 초반에서 감지되지 않음`을 반복한다.
반면 Director summary는 후보 B가 `이면지 보관 위치 등 디테일한 연속성도 완벽하게 지켜졌다`고 말한다.

즉 final selected manuscript는 `폰/이면지` 디테일은 맞췄는데,
selection 이후 다른 continuity heuristic이 final door를 닫은 가능성이 높다.

다만 `post_select_conflict` 본문 메시지 자체가 `ui_events`에 persistence되지 않아 여기까지는 medium confidence다.

### 3.2 이 case는 `Stage2/3 readiness` parent lane의 회귀가 아니다

부모 canary audit의 `partial` 판정은 유지해야 하지만,
그 의미는 `Stage2/3 normalization 실패`가 아니라 `Stage4 ep2 advisory/finalize seam 별도 blocker`다.

## 4. Open Questions

1. `Round 10`에서 실제로 어떤 `post_select_conflict` 문자열이 발화했는가
2. `FlashbackVerifier` severity를 낮출지, 아니면 `화면의 버튼 -> 터치스크린/스마트폰` 추론 규칙을 좁힐지
3. `post_select_conflict` downgrade 시 operator sink에 conflict detail을 왜 남기지 않는지

## 5. Recommended Next Wave

다음 wave는 `Stage2/3`가 아니라 `Stage4 ep2 advisory escalation loop` bounded patch가 맞다.

우선순위:

1. `FlashbackVerifier` literal mismatch 기준 축소
   - `화면의 버튼`만으로 `스마트폰/터치스크린`까지 승격 금지
2. `strong_advisory_escalation` persistence 보강
   - 어떤 family가 escalation을 일으켰는지 final sink에 명시
3. `post_select_conflict` operator observability 보강
   - final downgrade message를 `ui_events`/audit sink에 남기기

## 6. 3-Pass Audit Record

### Pass 1. Structure and Scope

- scope를 `ep2 Stage4 loop`로만 제한했다
- `Stage2/3 regression`과 `Stage4 advisory/finalize seam`를 분리했다
- artifact truth / metadata truth / code truth를 함께 봤다

### Pass 2. Evidence and Consistency

- canary closure audit/evidence의 `R10 post_select_conflict`와 live `ui_events`의 final REJECT를 교차 확인했다
- `FlashbackVerifier` 메시지와 실제 `ep1`/`ep2` 본문을 직접 대조했다
- local fix contract fail-close는 code anchor와 retry policy log가 일치한다

### Pass 3. Execution and Readability

- 결론을 `FP advisory + fail-close contract + final post-select downgrade` 3점으로 압축했다
- 다음 wave가 `Stage2/3`가 아니라 `Stage4 ep2 bounded patch`임을 명확히 했다
- 남은 불확실성은 `Round 10 post_select conflict detail 미기록` 하나로 한정했다

Confidence: `96%`
