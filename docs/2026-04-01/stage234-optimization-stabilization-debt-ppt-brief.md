Date: 2026-04-01
Status: final (3-pass audited)
Confidence: 96%
Scope: `Stage2/3/4` 최적화/안정화 관점 부채 정리 및 발표용 브리핑
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`
Queue Impact: none
Related Docs:
- `docs/2026-04-01/0_0-stage2-stage3-context-hierarchy-bounded-survey.md`
- `docs/2026-04-01/0_0-stage2-stage3-stage4-readiness-remediation-execution-ssot.md`
- `docs/2026-04-01/0_0-stage3-semantic-fidelity-runtime-closure-audit.md`
- `docs/2026-04-01/stage23-architecture-simplification-long-term-memo.md`

# Stage2/3/4 최적화·안정화 부채 브리핑

## 1. Answer-First

현재 파이프라인의 핵심 문제는 `5천 자 원고를 쓰는 일 자체`가 아니라, 그 원고를 만들기 위해 `같은 truth를 여러 단계에서 다시 번역하고 다시 포장하는 구조`에 있다.

이 부채는 세 갈래로 정리된다.

1. `구조 부채`
2. `용어 부채`
3. `계약 부채`

운영상 체감되는 현상은 다음과 같다.

- upstream에서 약하게 정리된 정보가 downstream에서 다시 해석된다
- stage별로 같은 개념을 다른 이름으로 부른다
- 어떤 곳에서는 hard constraint인 것이 다른 곳에서는 advisory로 약해진다
- 그 결과 retry, 검증, handoff, 재요약이 계속 늘어난다

즉 지금의 문제는 `단순 품질 문제`보다 `운영비를 키우는 구조적 비용 문제`에 가깝다.

## 2. 부채 정의

### 2.1 구조 부채

정의:

- 스테이지 수가 많고 handoff가 길다
- 중간 단계가 authority를 전달하기보다 다시 번역한다
- fail-late 구조가 많아 뒤 단계가 앞 단계의 부담을 대신 진다

현재 이슈:

- `Stage2 -> Stage3 -> Stage4`로 갈수록 동일 truth가 prose/summary/constraint/advisory로 반복 전달된다
- `Stage3`는 장면 구체화 단계라는 원래 취지와 달리, 실제로는 `Stage2 authority`를 재해석하는 중간 번역층으로 비대해진 구간이 있다
- downstream gate가 upstream의 약점을 보정하느라 시스템 전체가 무거워진다

### 2.2 용어 부채

정의:

- 같은 개념을 stage마다 다른 이름, 다른 밀도, 다른 포맷으로 부르는 상태

현재 이슈:

- `Stage2`: `tactical_doc`, `constraint_summary`, `episode_details`
- `Stage3`: `must_focus`, `arc_focus`, `constraint_block`, `continuity`, `semantic_carryover`
- `Stage4`: `opening anchor`, `mission`, `carryover`, `director_feedback`, `advisory`

결과:

- 운영자가 같은 truth를 여러 이름으로 추적해야 한다
- stage가 바뀔 때마다 의미가 살짝 이동한다
- handoff가 기술적으로는 성공해도 의미적으로는 약화될 수 있다

### 2.3 계약 부채

정의:

- 같은 규칙이 stage마다 다른 강도로 적용되는 상태

현재 이슈:

- 어떤 제약은 Stage2에서는 사실상 핵심 전술인데, Stage3에서 advisory처럼 약해진다
- 일부 structural issue는 clean PASS로 통과하고, 나중에야 PASS_WITH_FIX 또는 retry로 승격된다
- hard truth, mission, carryover, advisory의 우선순위가 곳곳에서 일관되지 않다

결과:

- fail-early가 아니라 fail-late가 된다
- 검증 비용이 커진다
- retry loop가 비대해진다

## 3. 왜 이렇게 복잡해졌나

핵심 원인:

- 연재물 특성상 continuity 압력이 강하다
- quality를 올리기 위해 stage를 나눈 것은 맞았지만,
- 시간이 지나면서 `품질 장치`와 `보정층`이 함께 누적되었다

즉 원래 의도는:

- `Stage2`: 스켈레톤
- `Stage3`: 구체화
- `Stage4`: 최종 원고화

였지만, 실제 운영에서는:

- `Stage2`: 전술 원천
- `Stage3`: 구체화 + 재해석 + 재번역
- `Stage4`: 원고화 + gate + 일부 upstream 보정

이 되어버렸다.

## 4. 지금까지 개선된 것

이번 웨이브에서 좋아진 핵심은 아래와 같다.

### 4.1 Stage3 semantic drift 억제

- 전술서에 없는 `외부 침입`, `뜬금없는 물리 위협`, `장르 밖 액션 활극` 같은 off-arc invention을 더 어렵게 만들었다
- 실제 `0_0` canary 기준 `ep5 intrusion subplot`은 final Stage3 artifact에서 제거됐다

### 4.2 Stage2 current-block authority 강화

- raw `curr_block` JSON dump를 그대로 넘기던 구조에서 벗어나,
- `Current Block Authority Packet`으로 현재 블록 DNA를 우선 노출하게 바꿨다

효과:

- 현재 블록 정보가 이전 arc 장문 context에 덜 묻힌다
- 블록 경계와 허용 사건 범위가 더 명시적으로 보인다

### 4.3 Stage3 hierarchy 정렬

- `Constraint Stack`이 `Arc Mission`보다 먼저 오게 바꿨다
- `prev_info`는 `truth/archive` tier로 분리했다
- cached shared context도 같은 우선순위를 따르도록 맞췄다

효과:

- hard constraint와 mission prose가 같은 높이에서 경쟁하는 구조가 줄었다
- 이전 화 거대 payload가 현재 화 제약을 누르는 현상이 완화됐다

## 5. 지금 시점의 정확한 평가

### 5.1 좋아진 점

- Stage2/3는 이전보다 더 계층적이고 덜 난잡해졌다
- Stage3 semantic fidelity는 실 runtime evidence로도 일부 닫혔다
- Stage4에서 뒤늦게 떠안던 일부 부담이 upstream으로 이동했다

### 5.2 아직 남은 점

- `Stage2 -> Stage3 -> Stage4` 구조 자체는 여전히 길다
- 용어/계약 불일치는 아직 완전히 정리되지 않았다
- parent lane의 최종 runtime closure는 추가 canary/audit이 필요하다

즉 현재 상태는:

- `불확실한 상태`는 지났다
- `운영 가능한 안정권 직전`까지는 왔다
- `장기적으로 단순한 구조`까지는 아직 중간이다

## 6. 장기 목표

장기 목표는 `stage 숫자 줄이기` 그 자체보다 `authority handoff 줄이기`다.

잠정 목표 상태:

1. `Stage2 -> Stage4`
2. `Stage2 -> (internal Stage3 compiler/substep) -> Stage4`

즉 질문은 `Stage3를 없앨까`가 아니라,

- `Stage3가 독립 창작 단계여야 하나`
- 아니면 `중간 compiler/substep`으로 낮춰도 되나

로 보는 것이 더 정확하다.

현재 판단:

- 장기적으로 가장 먼저 압축 검토할 단계는 `Stage3`
- 하지만 바로 삭제하는 것이 아니라, `중복 번역층 제거`가 우선

## 7. 발표용 메시지

발표에서 핵심 메시지는 아래처럼 가져가면 된다.

### 메시지 1

`문제는 모델이 5천 자를 못 쓰는 것이 아니라, 같은 truth를 여러 단계에서 다시 번역하는 구조에 있다.`

### 메시지 2

`현재 부채는 구조, 용어, 계약 세 층으로 나뉘며, 이 부채가 운영비와 디버깅비를 키운다.`

### 메시지 3

`최근 개선으로 Stage2/3 authority는 더 계층적이 되었고, off-arc invention은 실제로 줄었다.`

### 메시지 4

`다음 목표는 더 많은 장치 추가가 아니라, authority handoff와 중복 번역층을 줄이는 구조 단순화다.`

## 8. PPT 6장 뼈대

### 1장. 문제 정의

- 5천 자 원고보다 비싼 것은 handoff와 재해석 비용
- 현재 시스템은 품질 문제 + 구조 비용 문제가 섞여 있음

### 2장. 부채 지도

- 구조 부채
- 용어 부채
- 계약 부채

### 3장. 실제 증상

- Stage3 semantic drift
- Stage4 retry/gate churn
- 같은 truth의 다중 재포장

### 4장. 최근 개선

- Stage2 authority packet
- Stage3 constraint-first hierarchy
- semantic fidelity hardening

### 5장. 현재 위치

- 큰 blocker는 많이 제거
- 안정권 직전
- 다만 최종 runtime closure는 추가 확인 필요

### 6장. 장기 방향

- stage 수보다 authority handoff 수를 줄인다
- Stage3를 독립 창작층이 아니라 compiler/substep으로 낮출 가능성 검토
- 공통 vocabulary / contract normalization 추진

## 9. 한 줄 결론

`지금 시스템의 핵심 문제는 단순 성능 부족이 아니라 구조·용어·계약 부채이며, 최근 개선으로 upstream authority는 분명 좋아졌고, 다음 단계는 더 많은 handoff가 아니라 handoff 자체를 줄이는 방향이다.`
