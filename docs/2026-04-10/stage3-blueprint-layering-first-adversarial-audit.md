# Stage3 Blueprint Layering-First Adversarial Audit

Date: 2026-04-10
Status: final
Canonical Path: `docs/2026-04-10/stage3-blueprint-layering-first-adversarial-audit.md`
Baseline Commit: `e597a7bf4836dab71547e350b015f6658a1cfb03`
Baseline Dirty Summary: `dirty: 46 tracked_modified, 29 untracked; hotspots: docs/, modules/, tests/, material_ssot/, scripts/, secrets/`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `same-turn final design audit after the later current-HEAD Stage3 rerun merged the earlier structural survey, the aborted-run merge audit, and the newest `session_20260410_160214.log` evidence into one execution-facing conclusion`
Source Docs:
- `docs/2026-04-10/stage3-blueprint-first-pass-structural-survey.md`
- `docs/2026-04-10/00_000-stage3-fresh-run-abort-post-run-merge-audit.md`
- `docs/2026-04-02/0_0-stage3-contract-tightening-remediation-execution-ssot.md`
- `docs/2026-04-07/0_0-stage3-partial-fix-hardening-remediation-execution-ssot.md`
- `docs/2026-04-01/active-temp-execution-roadmap.md`
Evidence Artifacts:
- `0_temp.txt`
- `projects/00_000/logs/session_20260410_160214.log`
- `projects/00_000/logs/runtime_audit_summary.json`
- `projects/00_000/logs/session/llm_io.jsonl`
Side-Effect Coverage: covered for prompt/runtime/operator-observability surfaces
Confidence: `97%`

## 1. Question

Stage3 BP가 ep1에서 계속 질척이는 상황에서, 다음 realization 방향은 `그냥 적재를 덜하게 만드는 slimming`인가, 아니면 `ep-local packet layering`을 먼저 세우는 쪽인가.

추가로, 이 판단을 execution으로 승격하기 전에 더 많은 broad survey가 필요한지도 같이 묻는다.

## 2. Answer Summary

결론은 `layering first`다.

- 1순위 원인은 `arc item 자체 빈곤`이 아니라 `ep1 task에 서로 다른 성격의 packet이 같은 레벨로 실리는 구조 충돌`이다.
- 그래서 `단순 slimming`만으로는 부족하고, 먼저 `ep-local hard packet / allowed soft advisory / future substrate`를 분리해야 한다.
- 추가 broad survey는 지금 시점에서 과하다. 현재 evidence는 이미 execution 결정을 내릴 정도로 충분하다.
- execution 승격은 맞다. 다만 새 queue lane을 여는 대신 기존 `0_0-stage3-contract-tightening-remediation` 부모 lane에 `packet layering -> threshold alignment -> canonical patch anchors -> optional later slimming` 순서를 승격하는 것이 맞다.

## 3. Evidence Basis

### 3.1 Arc material poverty가 1순위라는 가설은 약하다

두 fresh run 모두 ep1 first-pass candidate는 `PASS_WITH_FIX score=95`까지 도달한다. 즉 "애초에 쓸 재료가 없다"는 설명은 현재 evidence와 잘 맞지 않는다.

- `projects/00_000/logs/session_20260410_143423.log`
- `projects/00_000/logs/session_20260410_160214.log`

좋은 first-pass가 나오는데도 final PASS로 잘 안 닫히는 쪽이 더 큰 문제다.

### 3.2 최신 rerun에서도 구조 pressure는 여전히 packet-side에 있다

나중 rerun에서도 Stage3는 완전히 망가진 것이 아니라 `83 PASS`, `87 PASS`, `81 PASS_WITH_FIX` 같은 결과까지는 계속 만든다. 그런데 runtime quality gate `90`과 fidelity / density pressure가 다시 그것을 patch loop로 밀어 넣는다.

대표 evidence:

- `16:13:36` `score=83`, `760자 < 800자`, `Arc 관계 변화 NPC 3명 blueprint 미언급`
- `16:22:58` `score=87`, `Arc 관계 변화 NPC 3명 blueprint 미언급`, `구체적 앵커 3개 < 5개`
- `16:27:34` `score=81`, `PASS_WITH_FIX - ep1 blueprint finalized`, 이어서 patch #1 진입

즉 현재 Stage3는 "완전히 못 씀"이 아니라 "괜찮은 후보를 계속 repair loop로 밀어 넣는 구조"다.

### 3.3 단순 slimming만으로는 부족하다는 evidence가 있다

latest run에서 patch/repair prompt 길이는 계속 커진다.

- `retry=2` patch prompt_len `5304`
- `retry=3` patch prompt_len `6263`
- `PASS_WITH_FIX` 후 patch #1 prompt_len `9556`

이건 토큰량이 많다는 뜻이기도 하지만, 더 본질적으로는 `ep-local task`, `future relationship pressure`, `style/rule pack`, `repair obligations`가 한 prompt plane에 계속 누적된다는 뜻이다.

즉 문제는 `많음`만이 아니라 `섞임`이다.

### 3.4 Authoritative closure evidence는 여전히 아니다

`runtime_audit_summary.json`은 여전히 `stage3_live_session.status = "absent"`다. 최신 run도 `KeyboardInterrupt()`로 종료됐기 때문이다.

그래서 이번 evidence는:

- Stage3 closure evidence는 아님
- 하지만 Stage3 next execution decision을 바꾸기에 충분한 action-bearing evidence는 맞음

## 4. 3-Pass Audit Record

### Pass 1. Structure and Scope

- question을 `layering vs slimming`으로 고정했다
- 이 문서를 새 queue lane 제안서가 아니라 `existing Stage3 execution promotion audit`로 제한했다
- broad survey 확장 여부와 execution 승격 여부를 같은 문서에서 판정하게 만들었다

### Pass 2. Evidence and Consistency

- latest rerun log, earlier aborted-run merge audit, first-pass structural survey를 함께 대조했다
- `좋은 후보는 나오지만 final PASS로 잘 안 닫힌다`는 공통 사실을 유지했다
- closure evidence와 action-bearing runtime evidence를 분리해 과대주장을 피했다

### Pass 3. Execution and Readability

- next code action을 `ep-local packet layering -> threshold alignment -> canonical patch anchors -> optional slimming` 순서로 명시했다
- child lane와 parent lane의 owner split을 명확히 했다
- rerun은 사라진 것이 아니라 `parent structural tranche 이후`로 밀린다는 operating consequence를 분명히 적었다

## 5. Adversarial Audit

### Challenge A. 정말 arc item 자체가 약한 것 아닌가

반박: 그렇다면 first-pass가 반복적으로 `PASS_WITH_FIX 95`까지 올라오기 어렵다. 현재 evidence는 `raw story material`보다 `surrounding contract pressure`가 더 큰 설명력을 가진다.

판정: 기각.

### Challenge B. 그냥 prompt를 줄이기만 하면 되는 것 아닌가

반박: 지금 핵심 충돌은 단순 길이보다 `hard stop`과 `future relationship requirement`가 같은 레벨로 같이 들어가는 데 있다. 순수 slimming은 토큰은 줄여도 `무엇이 이번 화 hard packet인지`를 결정하지 못한다.

판정: 부분 타당하지만 주원인 설명으로는 부족.

### Challenge C. 지금 남은 건 child lane repair loop뿐이고 parent design은 과한 것 아닌가

반박: child runtime hardening 이후의 최신 rerun에서도 여전히 `83/87/81` quality-gate churn, `relationship_changes` pressure, prompt inflation `9556`, patch drift가 남는다. 즉 child-only loop bugfix 하나로 끝나는 그림은 아니다.

판정: 기각.

### Challenge D. execution 승격 전 추가 survey를 더 해야 하지 않나

반박: 현재는 구조 원인이 네 번 이상 반복 확인됐다.

- first-pass strong candidate 존재
- threshold mismatch 반복
- relationship-change pressure 반복
- prompt inflation 반복
- authoritative closure 부재 반복

이 상태에서 broad survey를 더 늘려도 새 owner fact보다 같은 결론만 더 강하게 반복할 가능성이 높다.

판정: 기각.

## 6. Final Verdict

최종 판정은 아래와 같다.

1. `추가 broad survey`: 불필요
2. `execution 승격`: 필요
3. `새 queue lane 생성`: 불필요
4. `다음 parent-lane structural realization order`: 필요

권장 실행 순서:

1. `ep-local packet layering / gating`
2. `threshold alignment`
3. `canonical patch anchors`
4. `optional later prompt slimming`

owner split:

- parent lane `0_0-stage3-contract-tightening-remediation`
  - ep-local packet layering / gating
  - threshold alignment
  - canonical patch-anchor transport
- child lane `0_0-stage3-partial-fix-hardening-remediation`
  - local verifier hardening
  - retry exhaustion keyed by repeated targets
  - local patch-preservation / locality hardening

execution consequence:

- rerun은 취소가 아니라 `parent structural tranche 뒤`로 이동
- ClickUp 반영은 canonical execution docs -> temp mirrors -> queue-state -> ops validator 뒤에만 수행

## 7. Save Gate

- Pass 1 complete
- Pass 2 complete
- Pass 3 complete
- Adversarial audit complete
- Confidence gate: `97%`
