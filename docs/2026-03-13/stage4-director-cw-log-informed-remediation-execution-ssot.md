# Stage 4 Director-CW 로그 반영 통합 수정 실행 SSOT

작성일: 2026-03-13  
범위: `Director -> ChiefWriter` feedback loop 수정 오더 + `000__t` Stage 4 9화 런타임 로그 retained finding 통합  
최종 목표: runtime에서 드러난 `P1/P2`와 기존 feedback-loop `P2/P3`를 한 실행 축으로 묶어 닫는다  
기준 문서:

- [stage4-director-cw-feedback-loop-remediation-execution-ssot.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-execution-ssot.md)
- [stage4-director-cw-feedback-loop-remediation-5pass-audit.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-5pass-audit.md)
- [stage4-director-cw-feedback-loop-full-survey-3pass-audit.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md)
- [stage4-9ep-log-full-survey-3pass-final-audit.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-9ep-log-full-survey-3pass-final-audit.md)

## 1. Summary

이 문서는 기존 `Director-CW feedback loop remediation` 실행 SSOT를 버리지 않고, 방금 확인한 `000__t` Stage 4 9화 런타임 증거까지 합쳐서 재구성한 통합 실행 문서다.

핵심은 두 축이다.

1. 기존에 정적으로 잡혀 있던 loop debt
2. 실제 런타임에서 다시 드러난 8화 continuity debt와 observability/provenance debt

이번 통합 오더의 retained target은 아래 6개다.

- `R-1` 8화형 frontier continuity 충돌 방지
- `R-2` 반복 `PASS_WITH_FIX` second-pass narrowing 제거
- `R-3` Director feedback와 orchestration advisory provenance 분리
- `R-4` Stage 4 structured sink observability 보강
- `R-5` final-row warning semantics 정리
- `R-6` advisory logging / feedback builder hygiene 마감

기존 실행 SSOT는 계속 유효하지만, `000__t` 런타임 findings를 포함해 실제 수정에 들어갈 때는 이 문서를 상위 SSOT로 쓴다.

## 2. Why A Merged SSOT Is Needed

기존 문서는 맞았지만 범위가 좁았다. 그 문서는 주로 아래를 겨냥했다.

- repeated `PASS_WITH_FIX` narrowing
- advisory provenance ambiguity
- thin DB sink
- feedback builder/type-guard hygiene

반면 이번 런타임 보고서는 한 가지를 더 확정했다.

- 8화는 `LLM 일반 품질 문제`가 아니라 `Blueprint frontier와 직전 화 엔딩 충돌` 때문에 5회 시도와 4회 reject를 소모했다.

즉 지금부터는 `feedback loop만` 고쳐서는 안 된다. runtime에서 비싼 비용으로 드러난 continuity handoff debt도 같이 쳐야 ROI가 맞는다.

## 3. Retained Findings Mapped To Execution

### F-1. 8화 continuity debt

요약:

- `000__t` 8화는 5회 시도 끝에 PASS
- 3차, 4차 시도는 `Contradiction Firewall: CRITICAL 1건`으로 강제 REJECT
- Director review와 open_review는 모두 `직전 7화에서 이미 끝난 사건을 8화 Blueprint가 다시 반복`한다고 수렴

근거:

- [session_20260313_000215.log#L6361](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log#L6361)
- [session_20260313_000215.log#L6828](/C:/Users/User/Desktop/글도비/projects/000__t/logs/session_20260313_000215.log#L6828)
- [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/000__t/logs/episode_production.jsonl)

대응:

- `R-1`

### F-2. repeated PASS_WITH_FIX second-pass narrowing

요약:

- 첫 `PASS_WITH_FIX`는 `_extract_fix_feedback()`로 `action_items + fix_scope_reasoning + open_review`를 구조화한다.
- 하지만 재심사가 다시 `PASS_WITH_FIX`면 다음 patch 입력은 다시 `action_items` 중심으로 좁아질 수 있다.

근거:

- [stage4-director-cw-feedback-loop-full-survey-3pass-audit.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md)

대응:

- `R-2`

### F-3. provenance ambiguity

요약:

- runtime reject_reason blob에는 `Director action_items`, `자유 리뷰`, `이전 지시`, `Advisory 요약`이 한 문자열로 섞인다.

근거:

- [pass_rate_monitor.json](/C:/Users/User/Desktop/글도비/projects/000__t/logs/pass_rate_monitor.json)

대응:

- `R-3`

### F-4. thin DB sink

요약:

- `stage_attempts(stage=4)`는 `selection_reason`, `verdict_reason`가 비어 있다.
- 같은 attempt의 rationale은 `director_selections`와 `episode_production.jsonl`에만 있다.

근거:

- [project_data.db](/C:/Users/User/Desktop/글도비/projects/000__t/project_data.db)

대응:

- `R-4`

### F-5. warning semantics ambiguity

요약:

- final PASS row의 `warnings`에 rejected candidate성 경고가 섞인다.
- 9화 final PASS row에도 `3176자`, `4개 씬 중 0개 감지` 같은 과거 후보 경고가 남아 있다.

근거:

- [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/000__t/logs/episode_production.jsonl)
- [final_manuscript__A.txt](/C:/Users/User/Desktop/글도비/projects/000__t/logs/artifacts/stage4/ep_0009/attempt_01/final_manuscript__A.txt)

대응:

- `R-5`

### F-6. low-severity logging / builder hygiene

요약:

- advisory logging level, builder concat, type guard는 여전히 broad health debt로 남아 있다.

근거:

- [stage4-director-cw-feedback-loop-remediation-5pass-audit.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-5pass-audit.md)

대응:

- `R-6`

## 4. Execution Scope

### R-1. Frontier continuity hardening

대상:

- `stage3` blueprint handoff surface
- `stage4` continuity/firewall handoff surface
- 필요한 경우 blueprint validator / director precheck

문제:

- 8화는 직전 7화 엔딩에서 이미 소모된 사건을 다시 밟는 blueprint를 들고 Stage 4로 왔다.
- 현재 Stage 4는 이를 reject로 복구할 수는 있지만, 비용이 너무 크다.

수정 목표:

- 직전 화 end-state와 event consumption을 blueprint frontier 검증에 더 강하게 반영한다.
- `scene_overlap`, `event_ordering` 충돌이 명확하면 Stage 4에서 4회 reject를 소모하기 전에 더 이른 계층에서 걸리게 만든다.
- `Blueprint를 그대로 따를지`, `직전 확정 서사를 우선할지` 우선순위를 규칙으로 잠근다.

완료 조건:

- 8화형 케이스에서 반복된 동일 이벤트 재소모가 early gate 또는 blueprint-level advisory로 포착된다.
- Stage 4가 recovery를 담당하더라도 `full -> partial -> firewall -> firewall -> patch` 같은 장쇄를 줄인다.

### R-2. PASS_WITH_FIX second-pass narrowing 제거

대상:

- `stage4_interview_round.py`
- 관련 테스트

문제:

- 반복 `PASS_WITH_FIX`에서 reasoning과 open_review가 다시 action_items 중심으로 축약될 수 있다.

수정 목표:

- 2차, 3차 patch에서도 `_extract_fix_feedback()` 동등 수준의 structured feedback을 유지한다.

완료 조건:

- multi-pass PASS_WITH_FIX 테스트가 second-pass prompt에 `fix_scope_reasoning`, `open_review`를 요구한다.

### R-3. Director / orchestration provenance 분리

대상:

- `stage4_orchestrator.py`
- `stage4_interview_round.py`
- reject reason / previous_attempt / log sink 조립부

문제:

- Director-origin feedback과 orchestrator advisory가 한 문자열로 붙는다.

수정 목표:

- 최소 한 계층에서 provenance를 구조화한다.
- `director_feedback`, `runtime_advisory`, `prior_retry_directives`를 분리 저장하거나 분리 렌더링한다.

완료 조건:

- postmortem 기준으로 “Director가 말한 것”과 “시스템이 덧붙인 것”을 복원할 수 있다.

### R-4. Stage 4 structured sink observability 보강

대상:

- DB `stage_attempts` 기록부
- Stage 4 attempt persistence surface

문제:

- 현재 DB 단독으로는 rationale 복원이 불가능하다.

수정 목표:

- `selection_reason`
- `verdict_reason`
- compact `open_review`
- compact `fix_scope_reasoning`
- compact advisory provenance

를 `stage_attempts` 또는 동등 structured sink에 남긴다.

완료 조건:

- `director_selections`나 JSONL을 열지 않고도 DB만으로 attempt 판단 근거를 최소 복원할 수 있다.

### R-5. final-row warning semantics 정리

대상:

- `episode_production` 최종 row 조립부
- warning aggregation surface

문제:

- final PASS row warnings가 final manuscript defect와 rejected candidate warnings를 구분하지 않는다.

수정 목표:

- final manuscript 전용 warnings와 candidate aggregate warnings를 분리한다.
- 이름이든 필드든, 보고서 작성 시 오해가 없게 만든다.

완료 조건:

- PASS final row를 읽을 때 “최종 원고 문제”와 “과거 후보 경고”를 구분할 수 있다.

### R-6. advisory logging / builder hygiene 마감

대상:

- `stage4_interview_round.py`
- 관련 helper / logging surface

문제:

- low-severity debt가 여전히 feedback loop 해석 비용을 높인다.

수정 목표:

- advisory exception/degrade/fallback을 적절한 level로 올린다.
- feedback builder/type guard를 helper화한다.
- `unclassified_feedback` fallback을 줄일 근거를 만든다.

완료 조건:

- Stage 4 진단 로그의 의미가 더 직접적으로 읽힌다.

## 5. Non-Goals

이번 통합 오더에서 하지 않는 것:

- 모델 교체
- scoring rubric 전체 개편
- Stage 4 UI/build 작업
- unrelated Stage 0/2/3 broad cleanup
- live run 자체를 이 문서 안에서 수행하는 것

## 6. Execution Order

1. `R-1` frontier continuity hardening
2. `R-2` PASS_WITH_FIX second-pass narrowing 제거
3. `R-3` provenance 분리
4. `R-4` structured sink 보강
5. `R-5` warning semantics 정리
6. `R-6` logging / builder hygiene 마감

이 순서가 맞는 이유:

- 8화형 P1이 실제 비용을 가장 크게 만들었다.
- `R-2`, `R-3`, `R-4`는 같은 payload surface를 공유한다.
- `R-5`는 payload/sink shape가 정리된 다음에 들어가는 게 안전하다.
- `R-6`은 마감성 성격이 강하다.

## 7. Verification Matrix

### Focused tests

- `tests/test_pass_with_fix.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_a2_open_review_cw.py`
- Stage 4 persistence / JSONL / DB 관련 테스트
- 필요 시 8화형 continuity replay regression 추가

### Required assertions

1. 반복 `PASS_WITH_FIX` second-pass에서도 `fix_scope_reasoning`, `open_review`가 유지된다.
2. reject reason / previous attempt payload에서 provenance가 분리된다.
3. DB `stage_attempts`가 rationale field를 가진다.
4. final PASS row warnings는 final manuscript용과 candidate aggregate용이 분리된다.
5. 8화형 continuity replay가 early gate 또는 더 이른 remediation path로 잡힌다.
6. continuity gate가 정상 이어쓰기 케이스를 과잉 차단하지 않는다.
7. `scene_overlap`, `event_ordering` 검출이 true positive 1건과 false positive 방지 1건으로 함께 고정된다.

### Runtime proof

- 수정 후 limited Stage 4 rerun 또는 동등 proof
- 가능하면 `000__t`와 유사한 continuity-sensitive 에피소드에서:
  - 8화형 중복 사건 재소모가 줄었는지
  - reject chain 길이가 줄었는지
  - DB/JSONL/log provenance가 더 선명해졌는지 확인
- 가능하면 first-pass PASS가 나오는 일반 에피소드에서도 continuity gate가 과잉 경보를 만들지 않는지 확인

## 8. Acceptance Line

이 문서가 닫히려면 아래가 필요하다.

- 8화형 continuity debt가 Stage 4 장쇄 reject로만 복구되지 않는다.
- repeated `PASS_WITH_FIX` narrowing code-path가 닫힌다.
- provenance ambiguity가 로그/DB/JSONL 중 최소 한 계층에서 해소된다.
- `stage_attempts` thin sink가 보강된다.
- final-row warning semantics가 더는 오해를 만들지 않는다.

## 9. Final Use

지금부터 Stage 4 feedback-loop 관련 수정에 들어갈 때는 아래처럼 쓰면 된다.

- low-severity loop debt만 볼 때: 기존 [stage4-director-cw-feedback-loop-remediation-execution-ssot.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-remediation-execution-ssot.md)
- 실제 9화 런타임 evidence까지 합쳐 수정할 때: 이 문서

즉 현재 기준 상위 실행 SSOT는 이 문서다.
