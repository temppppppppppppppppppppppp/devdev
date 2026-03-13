# Stage 4 Director-CW Feedback Loop Full Survey 3PASS Audit

archive note:
- `projects/00_test_07` absolute links are historical references only.
- see `docs/2026-03-13/stage4-canary-archive-locator-note.md` for current archive guidance.

작성일: 2026-03-13  
대상 범위: Stage 4의 `Director -> ChiefWriter` 피드백 루프 전면 조사  
조사 원칙: 읽기 전용, 코드 수정 금지, 테스트 실행 금지  
최종 판정: `retained P2 1건`, `Observation 2건`, 확신도 `95%`

## Executive Summary

이번 조사 기준에서 Stage 4의 `Director-CW` 피드백 루프는 전반적으로 건강하다.

- `REJECT -> regenerate_with_feedback` 경로는 `action_items`, `fix_scope_reasoning`, `open_review`, `retry history`, `selection_reason`를 현재 코드상 명시적으로 보존한다.
- `PASS_WITH_FIX -> inplace patch -> Director 재심사` 경로도 예전 감사에서 문제였던 `patch provenance story_context 미주입`은 현재 닫혔다.
- 현재 남아 있는 실제 retained finding은 1건이다.
  - `P2`: `PASS_WITH_FIX`가 두 번 이상 반복될 때, 두 번째 patch부터는 `CW`에 전달되는 수정 피드백이 다시 `action_items` 중심 문자열로 축소된다. 이때 재심사 결과의 `fix_scope_reasoning`과 `open_review`가 다음 patch 반복에 충분히 실리지 않을 수 있다.

즉 결론은 이렇다.

- `Director-CW 루프가 전반적으로 깨져 있다`는 진단은 오탐다.
- `REJECT regenerate 경로는 현재 꽤 잘 잠겨 있다`.
- `local PASS_WITH_FIX 반복 루프`만 아직 완전히 clean하지 않다.

## Scope

조사 버킷은 아래 6개로 고정했다.

1. Stage 4 Orchestrator가 `Director feedback`를 어떻게 유지·변형하는지
2. `DirectorEnsembleSelector`가 어떤 구조화 필드를 결과로 내보내는지
3. `Stage4InterviewRound`가 `PASS`, `PASS_WITH_FIX`, `REJECT`를 어떻게 분기하는지
4. `ChiefWriter.regenerate_with_feedback()`와 `ChiefWriter.inplace_patch()`가 무엇을 실제로 받는지
5. 관련 테스트가 어떤 계약을 보장하고 어떤 계약을 놓치는지
6. tracked runtime log와 artifact가 현재 코드 계약을 실제로 따르는지

주요 증거는 아래 파일에서 수집했다.

- [stage4_interview_round.py](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py)
- [stage4_orchestrator.py](/C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py)
- [chief_writer.py](/C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py)
- [director_ensemble.py](/C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py)
- [test_pass_with_fix.py](/C:/Users/User/Desktop/글도비/tests/test_pass_with_fix.py)
- [test_stage4_interview_round.py](/C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py)
- [test_a2_open_review_cw.py](/C:/Users/User/Desktop/글도비/tests/test_a2_open_review_cw.py)
- [session_20260312_165217.log](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/session_20260312_165217.log)
- [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/episode_production.jsonl)
- [canary_summary.json](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/canary_summary.json)
- [stage4-context-contract-full-survey-3pass-audit.md](/C:/Users/User/Desktop/글도비/docs/2026-03-12/stage4-context-contract-full-survey-3pass-audit.md)

## Pass 1. Facts

### 1. Director output boundary는 현재 구조화돼 있다

`DirectorEnsembleSelector`는 결과 dict에 아래 구조를 명시적으로 실어 보낸다.

- `feedback`
- `action_items`
- `open_review`
- `fix_scope_reasoning`
- `state_updates`

근거:

- [director_ensemble.py#L1198](/C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L1198)
- [director_ensemble.py#L1202](/C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L1202)
- [director_ensemble.py#L1253](/C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L1253)
- [director_ensemble.py#L1258](/C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L1258)
- [director_ensemble.py#L1263](/C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py#L1263)

또 `open_review`는 필요할 때 `[자유 리뷰]` prefix로 `feedback.issues`에도 붙여 보존하려고 한다.

### 2. REJECT regenerate 경로는 현재 보존력이 강하다

`ChiefWriter.regenerate_with_feedback()`는 단순 `director_feedback` 문자열만 받는 것이 아니다. `previous_attempt`에서 다시 꺼내 아래를 `enhanced_feedback`에 덧붙인다.

- `score_breakdown`
- `validation_warnings`
- `fix_scope_reasoning`
- `open_review`
- `retry history`
- `selection_reason`

근거:

- [chief_writer.py#L783](/C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L783)
- [chief_writer.py#L851](/C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L851)
- [chief_writer.py#L876](/C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L876)
- [chief_writer.py#L881](/C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L881)
- [test_a2_open_review_cw.py#L24](/C:/Users/User/Desktop/글도비/tests/test_a2_open_review_cw.py#L24)

`Stage4InterviewRound._handle_reject()`도 `previous_attempt`에 `fix_scope_reasoning`, `open_review`, `selection_reason`, `state_updates`, `reject_bucket`, `prior_attempts`를 실어 다음 regenerate path로 넘긴다.

근거:

- [stage4_interview_round.py#L2703](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2703)
- [stage4_interview_round.py#L2848](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2848)
- [stage4_interview_round.py#L2861](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2861)

### 3. PASS_WITH_FIX local loop는 초기 1회만 구조화 피드백을 확실히 받는다

`Stage4InterviewRound._execute_pass_with_fix_loop()`의 첫 진입은 아래처럼 시작한다.

- `director_result` 전체에서 `_extract_fix_feedback()`를 호출
- `_extract_fix_feedback()`는 `action_items`, `fix_scope_reasoning`, non-review `feedback.issues`, `open_review`를 합쳐 `CW`용 patch feedback 문자열을 만든다

근거:

- [stage4_interview_round.py#L2288](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2288)
- [stage4_interview_round.py#L2312](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2312)
- [stage4_interview_round.py#L3839](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3839)
- [test_stage4_interview_round.py#L140](/C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py#L140)

### 4. Stage 4 re-audit는 이제 patch provenance를 story_context에 주입한다

2026-03-12 감사에서 열려 있던 `story_context 미주입` 이슈는 현재 닫혔다.

- `_summarize_patch_provenance()`가 `scope`, `fix_scope_reasoning`, `open_review`, compact feedback, patch targets, strategy를 요약한다.
- `_build_reaudit_story_context()`가 이를 `[PASS_WITH_FIX 재심사 — 이미 적용된 패치]` 블록으로 붙인다.
- PASS_WITH_FIX 재심사 호출은 이 재조립된 `story_context`를 Director에 넘긴다.

근거:

- [stage4_interview_round.py#L3876](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3876)
- [stage4_interview_round.py#L3910](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3910)
- [test_stage4_interview_round.py#L157](/C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py#L157)
- [stage4-context-contract-full-survey-3pass-audit.md#L408](/C:/Users/User/Desktop/글도비/docs/2026-03-12/stage4-context-contract-full-survey-3pass-audit.md#L408)

### 5. 오케스트레이터는 순수 Director feedback만 전달하지 않는다

`Stage4Orchestrator`는 REJECT 반복 중 아래 시스템 advisory를 `director_feedback` 문자열 앞에 직접 붙인다.

- plateau advisory
- repeated reject bucket advisory
- contradiction-type structural advisory
- V75-D/V75-B blueprint escalation advisory

근거:

- [stage4_orchestrator.py#L1021](/C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L1021)
- [stage4_orchestrator.py#L1059](/C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L1059)
- [stage4_orchestrator.py#L1090](/C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L1090)
- [stage4_orchestrator.py#L1148](/C:/Users/User/Desktop/글도비/modules/core/stage4_orchestrator.py#L1148)

이는 루프가 실제로는 `Director 단독 피드백`이 아니라 `Director + orchestration advisory` 복합 입력이라는 뜻이다.

## Pass 2. Cross Validation

### 1. REJECT path의 open_review 손실 우려는 기각된다

코드 증거:

- [stage4_interview_round.py#L2862](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2862)
- [chief_writer.py#L881](/C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L881)

테스트 증거:

- [test_a2_open_review_cw.py#L24](/C:/Users/User/Desktop/글도비/tests/test_a2_open_review_cw.py#L24)

판정:

- `REJECT -> regenerate` 경로는 현재 `open_review`를 잃지 않는다.

### 2. Stage 4 patch-history 미주입 우려는 기각된다

코드 증거:

- [stage4_interview_round.py#L3910](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3910)

테스트 증거:

- [test_stage4_interview_round.py#L157](/C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py#L157)

판정:

- 2026-03-12 감사의 old finding 중 `story_context 미주입`은 현재 더는 retained가 아니다.

### 3. 반복 PASS_WITH_FIX 루프의 축약 문제는 현재도 남아 있다

코드 증거 1:

- 첫 patch 진입은 `_extract_fix_feedback()`를 사용한다: [stage4_interview_round.py#L2312](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2312)

코드 증거 2:

- 그러나 재심사 결과가 다시 `PASS_WITH_FIX`일 때는 `_current_fb`를 `feedback.action_items` 또는 raw `feedback`에서만 다시 만든다: [stage4_interview_round.py#L2483](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2483), [stage4_interview_round.py#L2490](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2490)

테스트 증거:

- `_extract_fix_feedback()` helper 자체는 reasoning/open_review 보존을 검증한다: [test_stage4_interview_round.py#L140](/C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py#L140)
- 하지만 multi-pass PASS_WITH_FIX 테스트는 `call_count`와 최종 verdict만 확인하고, 두 번째 patch prompt가 `fix_scope_reasoning/open_review`를 다시 포함하는지는 검증하지 않는다: [test_pass_with_fix.py#L321](/C:/Users/User/Desktop/글도비/tests/test_pass_with_fix.py#L321), [test_pass_with_fix.py#L364](/C:/Users/User/Desktop/글도비/tests/test_pass_with_fix.py#L364)

런타임 증거:

- 실제 canary 세션에서 `PASS_WITH_FIX -> patch #1 -> 재심사 PASS_WITH_FIX -> patch #2` 경로가 실행됐다: [session_20260312_165217.log#L1969](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/session_20260312_165217.log#L1969), [session_20260312_165217.log#L2010](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/session_20260312_165217.log#L2010), [session_20260312_165217.log#L2131](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/session_20260312_165217.log#L2131), [session_20260312_165217.log#L2133](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/session_20260312_165217.log#L2133)

판정:

- 이 경로는 dead code가 아니다.
- 따라서 `반복 PASS_WITH_FIX에서 structured rationale이 다시 action_items-only 형태로 좁아질 수 있다`는 우려는 retained finding으로 승격 가능하다.

### 4. runtime observability는 현재 충분히 usable하다

현재 canary는 hard gate pass이며, Stage 4 결과물은 `episode_production.jsonl`에서 아래를 구조화해 남긴다.

- `action_items`
- `open_review`
- `selection_reason`
- `verdict_reason`
- `patch_trace`
- `initial_verdict/final_verdict`

근거:

- [episode_production.jsonl](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/episode_production.jsonl)
- [canary_summary.json](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/canary_summary.json)

다만 `project_data.db`의 `stage_attempts`는 훨씬 얇다. 즉 postmortem용 structured persistence는 `episode_production.jsonl`과 session log 의존도가 높다.

근거:

- [project_data.db](/C:/Users/User/Desktop/글도비/projects/00_test_07/project_data.db)

판정:

- blocker는 아니다.
- 다만 structured DB만으로 Director-CW rationale을 완전 복원하긴 어렵다.

## Pass 3. Retained Findings

### P2. 반복 PASS_WITH_FIX loop가 second-pass feedback를 `action_items` 중심으로 다시 축약한다

깨진 계약:

- 초기 `PASS_WITH_FIX`에서는 `action_items + fix_scope_reasoning + open_review + issues`를 합친 patch feedback가 `CW`에 간다.
- 그러나 첫 재심사가 다시 `PASS_WITH_FIX`면, 다음 patch부터는 `_extract_fix_feedback()`를 재사용하지 않고 `feedback.action_items` 또는 raw `feedback` 텍스트만 `_current_fb`로 삼는다.

직접 근거:

- [stage4_interview_round.py#L2312](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2312)
- [stage4_interview_round.py#L2483](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2483)
- [stage4_interview_round.py#L2490](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2490)

반대 근거 검토:

- `REJECT regenerate` 경로는 `open_review/fix_scope_reasoning`을 잘 보존한다.
- `story_context patch history`도 현재 주입된다.
- 따라서 loop 전체가 무너진 것은 아니다.

왜 오탐이 아닌가:

- multi-pass PASS_WITH_FIX 테스트는 존재하지만, `second-pass prompt`에 `fix_scope_reasoning/open_review`가 유지되는지 확인하지 않는다.
- runtime log도 실제로 patch #2 경로가 살아 있음을 보여 준다.

사용자 영향:

- 국소 patch가 두 번 이상 반복되는 케이스에서 `Director`의 자유 리뷰나 수정 범위 근거가 뒤 반복에서 약해질 수 있다.
- 결과적으로 `CW`가 같은 결함을 다시 맞고 patch loop가 길어지거나, `Director`가 재지적하는 비용이 늘 수 있다.

테스트 미실행 사유:

- 이번 감사는 read-only 조사만 수행했다.

## Rejected Findings

### R1. `REJECT` 경로에서 `open_review`가 사라진다

기각.

- [chief_writer.py#L881](/C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L881)
- [test_a2_open_review_cw.py#L24](/C:/Users/User/Desktop/글도비/tests/test_a2_open_review_cw.py#L24)

### R2. Stage 4 재심사 루프는 아직도 patch provenance를 `story_context`에 넣지 않는다

기각.

- [stage4_interview_round.py#L3910](/C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3910)
- [test_stage4_interview_round.py#L157](/C:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py#L157)

### R3. 현재 canary 기준으로 Director-CW loop observability가 sink에서 깨져 있다

기각.

- [canary_summary.json](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/canary_summary.json)
- current canary는 `hard_gates.status = pass`, `sink_alignment_summary.status = ok`다.

## Observations

### O1. Director-CW loop는 순수 1:1 loop가 아니라 orchestration advisory가 섞인 hybrid loop다

`Stage4Orchestrator`는 plateau, repeated bucket, contradiction-type, blueprint escalation 진단을 `director_feedback` 앞에 prepend한다.

이건 현재 기준 defect가 아니라 정책이다. 다만 “CW가 받은 것은 Director 순수 원문”이라고 가정하면 틀린 모델이다.

### O2. 현재 local patch는 structured field보다 flattened text cue에 더 민감하다

현재 canary의 유일한 patch case는 `patch_strategy=inplace_patch`, `fallback_reason=unclassified_feedback`였다.

근거:

- [canary_summary.json](/C:/Users/User/Desktop/글도비/projects/00_test_07/logs/canary_summary.json)

이건 즉시 defect는 아니다. 실제로 canary는 pass했다. 다만 patch routing이 `structured reasoner`보다 `text cue`에 더 의존한다는 뜻이다.

## Confidence Ledger

- `70` Stage 4 Director-CW 관련 코드, 테스트, 문서, runtime artifact 전량 인벤토리 완료
- `+10` `REJECT -> regenerate` handoff를 코드와 테스트 두 계층으로 교차 검증
- `+10` `PASS_WITH_FIX` path를 코드, 테스트, runtime log 세 계층으로 교차 검증
- `+5` 2026-03-12 old finding 재검토 후 `story_context 미주입` 문제 해소 확인
- `+5` false positive 3건 제거
- `-5` fresh runtime에서 `non-empty open_review/fix_scope_reasoning`가 second-pass PASS_WITH_FIX에도 끝까지 유지되는지 직접 관측한 로그는 없음

최종 확신도: `95%`

## Final Verdict

현재 Stage 4의 Director-CW feedback loop는 `대체로 건강`하다.

- `REJECT regenerate`는 현재 잘 보존된다.
- `runtime sink`도 현재 canary 기준으로 깨끗하다.
- old finding 하나는 이미 닫혔다.
- 남은 실질 retained issue는 `반복 PASS_WITH_FIX second-pass feedback 축약` 한 건뿐이다.

즉 `전반 붕괴`는 아니고, `inner patch loop semantics`에 국한된 `P2` 한 건이 남아 있는 상태로 판정한다.

