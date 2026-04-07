# 0_0 Stage3 Opening Transition Contract Normalization Remediation Execution SSOT

Date: 2026-04-02
Status: pending (promoted from parked on 2026-04-07 roadmap reorder; context-only upstream lane kept below broader Stage3 functional work)
Canonical Path: `docs/2026-04-02/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
Temp Mirror Path: `docs/temp/0_0-stage3-opening-transition-contract-normalization-remediation-execution-ssot.md`
Commit State:
- Baseline Commit: `current-workspace`
- Baseline Dirty Summary: `dirty: active Stage4 consumer-contract edits and recent ep2 bounded canary evidence remain in workspace`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-04-02/0_0-stage34-ep2-focused-bounded-canary-audit.md`
- `docs/2026-04-02/0_0-stage34-ep2-single-episode-demo-run-audit.md`
- `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-remediation-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage34-ep2-focused-bounded-canary-evidence.json`
- `docs/2026-04-02/0_0-stage34-ep2-single-episode-demo-run-evidence.json`
Side-Effect Coverage: context-only pending lane; no code changes in this lane yet

## 1. Answer First

이 lane은 `지금 당장 구현할 본선`이 아니라, 나중에 반드시 정리해야 할 `Stage3/BP opening-transition contract`를 queue에 명시해 두기 위한 promoted pending context다.

핵심 문제는 `EP1 ending -> EP2 opening`이 언제나 같은 장소 직접 연결이어야 한다는 뜻이 아니다.

진짜 문제는 현재 blueprint contract가 아래를 구조적으로 충분히 구분하지 못한다는 점이다.

- direct continuation
- scene transition with explicit movement/time cut
- intentional jump opening

이 구분이 BP에 구조화돼 있지 않으면, Stage4가 opening continuity를 과도하게 추론하거나 잘못된 동선을 발명할 수 있다.

다만 현재 직접 blocker는 여전히 `Stage4 opening spatial continuity hard-binding`이며, 그 코드는 이미 landed 상태다.

따라서 이 lane은 `upstream normalization pending lane`으로 보관한다.

## 2. Why This Exists

최근 ep2 bounded canary와 demo run에서 드러난 사실은 같다.

1. Stage3 ep2 blueprint 자체는 high score로 통과한다.
2. Stage4가 EP1 -> EP2 opening continuity를 반복적으로 틀린다.
3. 하지만 장기적으로는 Stage4만의 문제가 아니다.
4. opening이 direct continuation인지, time cut인지, location cut인지, deliberate jump인지 BP가 더 명시적으로 소유해야 Stage4가 억측을 줄일 수 있다.

즉 이 lane은 `Stage4 repair`가 아니라 `BP contract disambiguation` lane이다.

## 3. Scope

Included:

- Stage3/blueprint opening-transition contract inventory
- `start_location`, `time_flow`, `scene_1.location`, `scene_1.title`의 owner 재검토
- `prev ending -> next opening` transition type 구조화 필요성 검토
- `direct continuation / explicit transition / jump opening` 분기 contract 설계
- Stage4가 downstream consumer로 받을 최소 machine-readable field 정의

Excluded:

- 지금 당장 Stage3 generator patch
- active Stage4 remediation stack
- canary execution
- Stage2 block split redesign
- broad narrative schema rewrite

## 4. Current Findings

1. 현 구조는 opening anchor를 주지만, `transition type` 자체는 구조화되어 있지 않다.
2. 그래서 opening continuity가 direct continuation처럼 읽혀야 할지, 시간/장소 전환으로 읽혀야 할지 Stage4가 prose와 직전 ending에서 많이 추론한다.
3. 이 추론 여지가 Stage4 spatial continuity churn을 키운다.
4. 따라서 장기적으로는 BP가 opening transition contract를 더 강하게 소유하는 편이 맞다.
5. 그러나 현재 immediate blocker는 Stage4 runtime이며, upstream BP contract normalization은 defer가 맞다.

## 5. Hard Conclusions

1. `오프닝과 엔딩은 항상 직접 연결`이라는 규칙은 틀리다.
2. 필요한 건 direct sameness가 아니라 `설명 가능한 transition contract`다.
3. 이 contract는 장기적으로 Stage3/BP가 더 직접 소유해야 한다.
4. 하지만 지금 active blocker는 Stage4이므로 이 lane을 본선으로 올리면 우선순위가 흐려진다.
5. 따라서 이 lane은 promoted pending context lane으로 유지한다.

## 6. Non-Goals

- Stage4 opening hard-binding 대체
- immediate Stage3 execution
- Stage2 arc/block repartition 재설계
- canary closure 근거 만들기

## 7. Acceptance Criteria

이 lane이 나중에 활성화될 경우 최소 acceptance criteria는 아래다.

1. blueprint가 opening transition type을 구조적으로 표현한다.
2. `direct continuation / explicit transition / jump opening`이 contract 상 구분된다.
3. Stage4는 transition type을 prose 추론이 아니라 structured contract로 받는다.
4. 기존 `start_location / time_flow / scene_1.location` 의미와 충돌하지 않는다.
5. direct continuation이 아닌 경우에도 false drift 없이 opening을 해석할 수 있다.
6. Stage4 repair lane과 owner boundary가 명확히 분리된다.

## 8. Execution Shape

### Tranche 1

opening transition type inventory

- current blueprint fields가 어떤 transition semantics를 실질적으로 담고 있는지 정리

### Tranche 2

contract normalization

- direct continuation
- explicit transition
- jump opening

세 가지를 구조적으로 구분하는 bounded field set 설계

### Tranche 3

downstream handoff tightening

- Stage4 intake가 transition contract를 직접 받도록 transport normalization

## 9. Queue Placement

이 lane은 `promoted pending context lane`이다.

- active Stage4 remediation 아래
- `0_0-stage3-contract-tightening-remediation` 아래
- `0_0-stage2-contract-normalization-remediation`, `0_0-stage234-cross-stage-contract-normalization-remediation` 아래

이유:

- 지금 직접 런을 막는 blocker는 아니다
- Stage3 general contract tightening보다도 더 뒤의 optional refinement다
- ep2 evidence와 직접 연결되더라도, broader Stage2/cross-stage contract lanes보다 먼저 열 bounded behavior slice는 아니다

## 10. Next Action

지금은 구현하지 않는다. 다만 정식 pending queue에서는 유지한다.

기억만 유지한다.

- Stage4 opening hard-binding은 already code-landed
- 나중에 upstream을 손볼 때 BP opening-transition contract normalization이 필요하다

## 11. 3-Pass Audit

Pass 1. Structure/Scope
- pending context lane 성격 명시
- active blocker와 장기 substrate를 분리
- included/excluded scope 분리 완료

Pass 2. Evidence/Consistency
- recent ep2 bounded canary and demo audit와 정합
- current Stage4 opening hard-binding lane과 owner boundary 충돌 없음

Pass 3. Execution/Readability
- 지금 구현 금지 명시
- later contract shape only로 bounded
- queue placement 보수적으로 설정

Confidence: `96%`
