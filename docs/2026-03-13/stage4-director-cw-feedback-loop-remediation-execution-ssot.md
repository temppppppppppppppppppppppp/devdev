# Stage 4 Director-CW Feedback Loop Remediation Execution SSOT

작성일: 2026-03-13  
범위: Stage 4 `Director -> ChiefWriter` 피드백 루프와 그 인접 low-severity debt  
실행 목표: retained `P2` 1건 + 관련 `P2/P3/Observation` 전량 처리  
기준 문서:

- [stage4-director-cw-feedback-loop-full-survey-3pass-audit.md](/C:/Users/User/Desktop/글도비/docs/2026-03-13/stage4-director-cw-feedback-loop-full-survey-3pass-audit.md)
- [TF-HEALTH-codebase-full-audit.md](/C:/Users/User/Desktop/글도비/docs/2026-03-12/TF-HEALTH-codebase-full-audit.md)
- [system-wide-full-audit-3pass.md](/C:/Users/User/Desktop/글도비/docs/2026-03-12/system-wide-full-audit-3pass.md)
- [system-wide-full-audit-3pass-merged-final.md](/C:/Users/User/Desktop/글도비/docs/2026-03-12/system-wide-full-audit-3pass-merged-final.md)

## 1. Summary

이번 오더는 `Stage 4 Director-CW loop`를 기준으로 한다. 즉 broad health 문서의 Stage 4/Cross-cutting low-severity 항목 중에서도, 아래 조건을 동시에 만족하는 것만 실행 대상으로 올린다.

1. 현재 코드 기준으로 아직 닫히지 않았다.
2. `Director -> ChiefWriter` handoff, `PASS_WITH_FIX` local patch loop, `re-audit`, `advisory provenance`, `loop observability`에 직접 붙는다.
3. `P3급까지 전량 처리` 목표에 맞게, 단순 blocker뿐 아니라 low-severity hygiene와 provenance clarity까지 이번 범위에 포함하는 편이 ROI가 높다.

이번 실행에서 닫을 최종 범위는 5개다.

- `E-1` 반복 `PASS_WITH_FIX` second-pass feedback narrowing 제거
- `E-2` orchestration advisory provenance 분리
- `E-3` loop observability 보강
- `E-4` advisory/feedback logging hygiene 보강
- `E-5` type guard / feedback builder hygiene 정리

## 2. Why This Order

현재 남아 있는 실제 loop defect는 1건이지만, 그 주변에 low-severity debt가 붙어 있다.

- 우리 최신 감사 retained:
  - repeated `PASS_WITH_FIX`에서 `_current_fb`가 다시 `action_items` 중심으로 좁아짐
  - `Director-CW` loop가 실제로는 `Director + orchestration advisory` hybrid인데 provenance 구분이 약함
  - DB structured sink는 얇고, loop rationale은 `episode_production.jsonl`와 session log 의존도가 높음
- `TF-HEALTH` broad debt 중 이번 범위에 직접 연결되는 것:
  - `S4-P2-002` advisory 예외 `debug` 로깅
  - `S4-P2-003` feedback 문자열 조립 hygiene
  - `S4-P2-004` Director 결과 type guard 부분 누락
  - `CC-P2-003` advisory 로깅 레벨 일관성

반대로 이번 오더에서 제외하는 항목도 명시한다.

- 이미 닫힌 old finding
  - Stage 4 patch provenance story_context 미주입
  - Stage 4 re-audit QualityGate 미적용
  - Stage 4 `state_updates` merge drift
- 범위 밖 broad debt
  - Stage 0/2/3 일반 코드 위생
  - provider/router 비용 telemetry
  - canary/untracked 재현성
  - TruthGate, SemanticPlotGuard, KRW regex 등 Stage 4 loop 외부 축

## 3. Execution Scope

### E-1. PASS_WITH_FIX second-pass feedback narrowing 제거

대상:

- [stage4_interview_round.py](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- [test_pass_with_fix.py](/C:/Users/User/Desktop/글도비/tests/test_pass_with_fix.py)
- [test_stage4_interview_round.py](/C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py)

문제:

- 첫 `PASS_WITH_FIX`는 `_extract_fix_feedback()`를 통해 `action_items + fix_scope_reasoning + open_review + issues`를 합친다.
- 그러나 첫 재심사가 다시 `PASS_WITH_FIX`면 다음 patch부터 `_current_fb`가 `feedback.action_items` 또는 raw `feedback`으로 좁아진다.

수정 목표:

- 반복 `PASS_WITH_FIX`에서도 `_extract_fix_feedback(_re_audit)`를 재사용한다.
- re-audit가 `action_items`만 있든, `open_review/fix_scope_reasoning`만 있든, 동일 규칙으로 patch feedback를 생성한다.
- 기존 `state_updates`, `patch_trace`, `quality_gate` semantics는 건드리지 않는다.

완료 조건:

- multi-pass PASS_WITH_FIX 테스트가 second-pass prompt의 `fix_scope_reasoning`, `open_review` 유지까지 검증한다.
- runtime log에서 patch #2 이상 반복 시에도 feedback provenance가 약화되지 않는 구조가 된다.

### E-2. orchestration advisory provenance 분리

대상:

- [stage4_orchestrator.py](/C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
- [stage4_interview_round.py](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- 관련 문서/로그 sink

문제:

- 현재 `director_feedback`는 순수 Director 원문이 아니라 plateau, reject bucket, contradiction-type, blueprint escalation advisory가 prepend된 hybrid text다.
- 이 설계 자체는 문제는 아니지만, provenance 분리가 약해 postmortem 시 “Director 지시”와 “system advisory”가 섞여 보인다.

수정 목표:

- `Director-origin feedback`와 `orchestrator-injected advisory`를 내부적으로 구분 가능하게 한다.
- 최소 요건은 아래 둘 중 하나다.
  - `previous_attempt`와 log sink에 advisory provenance field를 별도 저장
  - 혹은 CW 전달용 문자열 내부에 provenance section을 구조적으로 분리

완료 조건:

- postmortem 기준으로 “Director가 한 말”과 “orchestrator가 추가한 지시”를 분리 복원할 수 있다.
- 기존 behavior는 유지하되 provenance ambiguity만 줄인다.

### E-3. loop observability 보강

대상:

- [stage4_interview_round.py](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/episode_production.jsonl)
- DB `stage_attempts` sink 관련 코드

문제:

- 현재 rich loop evidence는 `episode_production.jsonl`와 session log에 주로 남고, DB `stage_attempts`는 얇다.
- structured DB만으로는 `open_review`, `fix_scope_reasoning`, advisory provenance, re-audit lineage를 복원하기 어렵다.

수정 목표:

- 최소한 Stage 4 attempt sink에 아래 중 필요한 핵심을 structured하게 남긴다.
  - `selection_reason`
  - `verdict_reason`
  - `open_review`
  - `action_items`
  - compact `fix_scope_reasoning`
  - compact advisory provenance
- rich JSONL sink와 DB sink의 역할 분리를 명시하되, DB도 최소 forensic 수준은 확보한다.

완료 조건:

- DB만 읽어도 Stage 4 attempt의 핵심 판단 근거를 최소 수준 복원할 수 있다.
- sink 간 의미 차이가 있으면 문서와 테스트로 고정된다.

### E-4. advisory / feedback logging hygiene 보강

대상:

- [stage4_interview_round.py](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- broad health 문서가 지적한 advisory logging level 관련 surface

문제:

- `TF-HEALTH` 기준 `S4-P2-002`, `CC-P2-003`: advisory 예외/상태가 `debug`에 묻히는 경향이 있다.
- Stage 4 loop는 실제로 runtime diagnosis가 중요하므로, 낮은 레벨의 무음 실패가 장기적으로 cost를 만든다.

수정 목표:

- advisory runtime exception, degrade, fallback, timeout 관련 로그를 `warning/info` 수준으로 재분류한다.
- noisy debug flood는 유지하지 않되, 운영자가 놓치면 안 되는 degrade는 남긴다.

완료 조건:

- Stage 4 advisory chain 실패/타임아웃/폴백이 production logs에서 추적 가능하다.
- 로그 양이 과도하게 폭증하지 않도록 메시지 수와 수준을 함께 조정한다.

### E-5. type guard / feedback builder hygiene 정리

대상:

- [stage4_interview_round.py](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)

문제:

- `TF-HEALTH` 기준 `S4-P2-003`, `S4-P2-004`: feedback 문자열 concat과 Director 결과 타입 가드가 일부 느슨하다.
- current canary에서도 `patch_trace.fallback_reason = "unclassified_feedback"`가 확인돼, local patch classifier가 flattened feedback cue에 과의존하는 면이 드러났다.
- 지금 당장 blocker는 아니지만, 반복 patch loop를 손대는 김에 builder 규칙을 정리하는 편이 낫다.

수정 목표:

- `director_result`, `feedback`, `action_items`, `open_review` 처리 규칙을 helper로 통일한다.
- string/dict/list 섞임에 대한 방어를 한 군데서 한다.
- feedback dedupe와 truncation policy를 명시화한다.
- patch focus classifier가 최소한 `fix_scope_reasoning/open_review/action_items`를 함께 참고할 수 있게 정리한다.

완료 조건:

- 같은 정보를 여러 경로에서 다른 방식으로 문자열화하지 않는다.
- helper 단위 테스트로 문자열 조립 규칙을 고정한다.
- canary patch case에서 `unclassified_feedback` fallback이 불필요하게 반복되지 않도록 분류 근거를 개선한다.

## 4. Non-Goals

이번 오더에서 하지 않는 것:

- Stage 4 prompt 자체 개편
- CW/Director 모델 변경
- Stage 4 scoring rubric 변경
- Stage 4 canary/build/UI 작업
- unrelated TF-HEALTH P2 cleanup 전량 처리

## 5. Execution Order

1. `E-1`을 먼저 처리한다.
   이유: 남아 있는 유일한 실질 loop defect다.
2. `E-2`를 처리한다.
   이유: `E-1`과 같은 feedback payload surface를 건드리므로 바로 이어서 provenance를 잠그는 편이 맞다.
3. `E-5`를 처리한다.
   이유: builder/type guard를 마지막에 정리하면 앞선 수정의 중복 분기를 줄일 수 있다.
4. `E-3`을 처리한다.
   이유: payload shape가 정해진 뒤에 observability schema를 맞추는 것이 안전하다.
5. `E-4`를 처리한다.
   이유: 구조가 안정된 후 logging level/noise를 마감하는 편이 낫다.

## 6. Verification Matrix

### Focused tests

- `tests/test_pass_with_fix.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_a2_open_review_cw.py`
- 필요 시 `tests/test_failure_analyzer.py`

### New test assertions required

1. repeated `PASS_WITH_FIX` second-pass에서도 `_extract_fix_feedback()` equivalent output이 다시 사용된다.
2. second-pass payload가 `open_review`와 `fix_scope_reasoning`을 잃지 않는다.
3. orchestrator advisory provenance가 log/sink에서 구분 가능하다.
4. DB structured sink가 최소 rationale field를 저장한다.
5. advisory degrade/fallback/timeout이 warning/info 수준으로 보인다.

### Runtime confirmation

- limited Stage 4 canary 또는 equivalent Stage 4 rerun에서:
  - `PASS_WITH_FIX -> patch #2+` 케이스가 있으면 feedback provenance 유지 확인
  - `episode_production`과 DB sink가 새 observability schema를 반영하는지 확인

## 7. Pass Map

이번 문서가 끌어온 원천 finding을 아래처럼 맵핑한다.

| Source | Original finding | Final execution mapping |
|---|---|---|
| our latest audit | repeated PASS_WITH_FIX second-pass narrowing | `E-1` |
| our latest audit | hybrid Director + orchestration advisory ambiguity | `E-2` |
| our latest audit | DB sink thin observability | `E-3` |
| TF-HEALTH `S4-P2-002` | advisory exception debug logging | `E-4` |
| TF-HEALTH `CC-P2-003` | advisory logging level inconsistency | `E-4` |
| TF-HEALTH `S4-P2-003` | feedback string concat hygiene | `E-5` |
| TF-HEALTH `S4-P2-004` | Director result type guard partial gap | `E-5` |

## 8. Done Criteria

이번 remediation이 닫혔다고 보려면 아래를 모두 만족해야 한다.

1. retained `P2` 1건이 코드상 닫힌다.
2. Stage 4 feedback payload가 repeated PASS_WITH_FIX에도 구조적 정보를 유지한다.
3. advisory provenance가 분리 가능하다.
4. low-severity logging/type-guard/builder debt가 같이 정리된다.
5. focused regression이 green이다.
6. post-fix 3pass 또는 그 이상 재감리에서 새 `P0/P1/P2`가 없다.
