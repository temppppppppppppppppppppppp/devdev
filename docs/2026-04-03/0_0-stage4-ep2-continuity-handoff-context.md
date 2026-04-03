# 0_0 Stage4 ep2 Continuity Handoff Context

Date: 2026-04-03
Type: handoff context note
Scope: `0_0` / `ep2` / Stage3+Stage4 bounded canary follow-up
Status: active debugging context (revalidated against `r5` latest runtime and current Stage4 intake surfaces)
Confidence: 96%

## Answer-First

- 현재 `ep2`는 아직 **Stage4에서 실패**한다.
- `ep1 frozen`은 계속 유지됐고, `Stage3 ep2 blueprint`도 PASS였다.
- 본체는 이제 `감지 실패`가 아니라 **Stage4 correction quality 부족**이다.
- `V75-D`는 이제 실제로 발동하고 blueprint inplace patch도 성공한다.
- 최신 runtime artifact는 이제 `r5`지만, correction-path 관찰값은 `r4`가 더 풍부하다. 즉 `r5 = latest`, `r4 = richest correction-path snapshot`으로 읽는 것이 맞다.
- 하지만 `V75-D 1회 패치`로는 `opening 장소 고정`까진 되더라도 `flashback/replay 모순 억제`까지는 닫히지 않았다.
- `r4` 이후에는 두 가지가 추가 landed됐다:
  - `V75-D correction v2`
  - `Stage4 opening transition global contract`
- 현재 구현 포인트는 `same location always`가 아니라 `undeclared replay/jump 차단 + declared transition 허용` 쪽이다.
- 일부 Stage4 opening-anchor surface는 아직 이 계약을 과도하게 hard-lock처럼 서술하므로, 다음 bounded 구현은 그 intake surface alignment가 우선이다.

## 1. Latest and Richest Runtime Snapshots

현재 authoritative runtime baseline은 아래 두 묶음으로 읽는 것이 맞다.

- latest runtime snapshot:
- `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r5-audit.md`
- `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r5-evidence.json`
- richest correction-path snapshot:
- `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r4-audit.md`
- `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r4-evidence.json`

요약:

- `r5 최신성`: YES, 단 1라운드 + API 지연으로 correction-path 관찰은 제한적
- `r4 풍부도`: YES, V75-D 발동 / inplace patch / post-patch 재실패까지 관찰
- `ep2 통과 여부`: FAILED
- `ep1 frozen 유지`: YES
- `Stage3 ep2 blueprint`: PASS (`r4=95`, `r5=98`)
- `Stage4 ep2 draft`: 저장 실패
- `최종 round`: `r4=3 완료 + R4 진입 시 종료`, `r5=1 완료 + R2 진행 중 종료`
- `V75-D`: `r4=YES`, `r5=미관찰(1R만 완료)`
- `dominant blocker`: Flashback/Spatial continuity

핵심 해석:

- `r2` 대비 `V75-D 미발동` 문제는 해소됐다.
- `quality_issue -> logic-like 집계`도 실제로 먹었다.
- `r5`는 `[A-4 continuity replay]` 감지까지는 재확인했지만, suppression이 LLM 원고 단계에서 아직 충분히 먹지 않는다는 쪽으로 읽힌다.
- 따라서 현재 병목은 `trigger`가 아니라 `patched blueprint를 써도 Stage4 manuscript가 계속 opening replay/flashback drift를 만든다`는 점이다.
- 동시에 이 문제를 `same-location hard lock`으로 오독하면 Stage3 parked lane의 결론과 충돌한다.

## 2. What Is Already Ruled Out

아래는 현재 우선 원인에서 내려도 되는 것들이다.

1. `ep1 canary baseline corruption`
- 현재 evidence상 `ep1 frozen`은 계속 유지됐다.
- 따라서 이번 디버깅의 주축은 `copy corruption`이 아니다.

2. `Stage3 outright failure`
- `Stage3 ep2 blueprint` 자체는 PASS였다.
- 따라서 "S3가 바로 죽어서 Stage4가 망가진다"는 그림은 현재 근거가 약하다.

3. `V75-D trigger not firing`
- `r4`에서 이미 해결됐다.
- 이제는 `발동 후 correction quality`를 봐야 한다.

## 3. Current Main Hypothesis

현재 가장 강한 가설은 아래다.

`Stage4가 opening transition contract를 보는 것 자체는 나아졌지만, correction payload가 manuscript opening을 충분히 강하게 구속하지 못해 completed-event replay와 flashback drift를 계속 허용한다.`

좀 더 풀면:

- `opening 장소 고정`은 일부 성공
- 그러나 `scene_1.summary`, `scene_1.key_events`, 실제 manuscript opening 사이의 결속이 아직 약함
- 그 결과 LLM이 직전 화에서 이미 끝난 통화/행동을 `회상 재연`처럼 다시 써 버림
- 그리고 일부 Stage4 opening-authority surface는 이 contract를 `다른 장소/시간이면 즉시 불합격`처럼 과도하게 서술하고 있어, 현재 구현 리스크는 `consumption weakness`와 `surface wording overshoot`가 함께 존재한다.

보조 가설:

- `S3 opening-transition contract`가 여전히 러프할 수는 있다
- 다만 현재는 Stage4 correction/consumption 쪽이 더 우선이다
- S3는 `defer`로 올려둔 `opening-transition contract normalization`이 이미 있으므로, Stage4 correction을 더 본 뒤 판단해도 된다
- 즉 `다른 장소/시간/POV opening 자체`를 막는 것이 아니라, `선언 없는 replay/jump`를 막는 쪽으로 정렬해야 한다.

## 4. Landed After r4

`r4` 이후 다음 두 패치가 들어갔다.

### A. V75-D correction v2

주요 파일:

- `modules/core/stage4_orchestrator.py`
- `tests/test_stage4_orchestrator.py`

요지:

- V75-D가 더 이상 top-level opening field만 고치지 않도록 확장
- 아래를 함께 맞추도록 correction contract 강화:
  - `start_location`
  - `time_flow`
  - `scene_breakdown.scene_1.location`
  - `scene_breakdown.scene_1.summary`
  - `scene_breakdown.scene_1.key_events`
- replay 신호가 있으면 아래도 같이 지시:
  - `EP1에서 이미 완료된 전화/행동을 EP2 opening에서 회상·재연 장면으로 다시 쓰지 말 것`
  - `새 공간/새 행동은 explicit transition 없이 먼저 등장시키지 말 것`

주의:

- 이것은 `회상 전면 금지`가 아니다
- `opening replay suppression`에 더 가깝다

### B. Stage4 opening transition global contract

주요 파일:

- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_chief_writer_context.py`

요지:

- 이건 `ep2 하드코딩`이 아니라 전역 규칙이다
- 핵심 규칙:
  - completed prior-episode event replay 금지
  - 새 장소/새 행동/시간 점프는 `전환 문장` 또는 `* * *` 같은 장면 전환 마커를 거칠 것
  - 단, `* * *`만 두고 끝내지 말고 직후 1~2문장 안에 바뀐 장소/시간/행동 상태를 명시할 것
  - 전환 신호 없이 새 방, 차량, 외부 이동 경로, 더 늦은 시간대로 바로 점프하지 말 것

중요 해석:

- 이 규칙은 `오프닝은 항상 엔딩과 같은 장소여야 한다`는 뜻이 아니다
- 차이가 나도 되지만, `왜/어떻게 달라졌는지`가 명시돼야 한다는 계약이다
- 따라서 `ep2` local-fix를 전역 `same-location hard lock`으로 승격시키면 오히려 잘못된 방향이다.

## 5. Recommended Next Session Starting Point

다음 세션은 아래 순서로 시작하는 것이 좋다.

1. `r4`와 `r5` audit/evidence를 함께 읽되, `latest`와 `richest`를 구분한다
2. landed patch와 현재 Stage4 opening-authority surface wording을 함께 확인한다
3. governing Stage4 consumer SSOT를 `declared transition contract` 기준으로 재감리한다
4. 그 뒤 bounded Stage4 intake-surface alignment를 구현한다
5. 이후 결과를 아래 두 갈래로 해석한다

### Case A. 초반 라운드 수가 줄고 수렴이 보임

- Stage4 opening transition contract 강화가 실제로 먹는다는 뜻
- 계속 Stage4 correction quality 쪽으로 미세조정하면 된다

### Case B. 여전히 V75-D 이후에도 replay/flashback 모순이 반복됨

- 그때는 아래 두 항목을 좁게 다시 본다
  - `patched blueprint scene_1 semantics -> manuscript opening consumption`
  - `S3 opening-transition contract가 실제로 너무 러프한지`

## 6. What To Look At First If It Still Fails

실패가 다시 나면, 아래 순서로 본다.

1. `pre-patch blueprint` vs `post-V75-D blueprint`
- `scene_1.location`
- `scene_1.summary`
- `scene_1.key_events`
- `start_location`
- `time_flow`

2. 실제 `R+1 manuscript opening`
- replay suppression이 깨졌는지
- explicit transition 없이 새 장소/새 행동으로 튀었는지
- `* * *`를 썼다면 직후 상태 명시가 있는지
- declared transition이나 작품 POV 정책상 허용되는 alternate opening까지 false reject로 묶지는 않았는지

3. canary summary/operator sink
- `repair_contract`
- `scope_authority`
- `gate_repair_surface_summary`

즉 디버깅 질문은 이렇게 좁히면 된다.

- `patch는 바뀌었는데 manuscript가 못 따라오나?`
- 아니면
- `patch 자체가 아직 scene_1 semantics를 충분히 못 바꾸나?`

## 7. Relevant Files

런타임 evidence:

- `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r4-audit.md`
- `docs/2026-04-03/0_0-stage34-ep2-focused-bounded-canary-r4-evidence.json`

현재 코드 핵심:

- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_canary_tools.py`

관련 SSOT:

- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-repair-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`

## 8. Boundaries

- 이 문서는 `handoff context note`다
- closure 문서가 아니다
- `Stage4 solved` 선언이 아니다
- `ep2 runtime blocker`를 다음 세션이 이어받기 위한 상태 기록이다

## 9. 3-Pass Audit Note

- pass 1: scope 정리
- pass 2: r4 audit/evidence와 landed code 사실 일치 확인
- pass 3: 다음 세션 actionability 점검
- final confidence: 96%
