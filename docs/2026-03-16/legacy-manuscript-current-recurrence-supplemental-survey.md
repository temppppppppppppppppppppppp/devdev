<!-- [참고자료] -->
<\!-- [참고자료] -->
Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/legacy-manuscript-current-recurrence-supplemental-survey.md`
Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
Baseline Dirty Summary: `dirty: desktop icon/version files, stage4/continuity runtime modules and tests, project runtime artifacts/db, opus memo edits, runtime persistence/context modules, and untracked 2026-03-16 survey docs`
Scope: `current-code recurrence recheck for legacy manuscript contradiction classes`, `authority sink alignment`, `carryover continuity`
Evidence Artifact: `docs/2026-03-16/legacy-manuscript-current-recurrence-supplemental-survey-evidence.txt`
Confidence: `97%`

# Legacy Manuscript Current Recurrence Supplemental Survey

## 1. Question

직전 실물 원고 조사에서 확인한 문제는 `예전 코드베이스`에서 생성된 산출물 기준이었다. 이번 문서는 그 findings를 현재 코드에 다시 투영해서, 같은 종류의 문제가 `지금도 터질 수 있는지`를 추가 조사한 결과다.

조사 축은 둘뿐이다.

1. `authority sink alignment`
   - patched 이후 `director_selections`, `stage_attempts`, final manuscript authority가 지금도 어긋날 수 있는가
2. `carryover continuity`
   - 자산/장비/충성도/직책/시간경과 같은 화간 연속성 충돌이 지금도 published manuscript로 새어 나갈 수 있는가

## 2. Short Answer

짧게 말하면 이렇다.

- `예, 일부는 지금도 터질 수 있다.`
- 다만 `터지는 위치`가 예전과 똑같지는 않다.

정확히는:

1. `stale metadata authority`는 지금도 구조적으로 재발 가능하다.
2. `published final manuscript hard contradiction`은 예전보다 훨씬 덜 터지지만, 완전히 불가능해진 것은 아니다.

즉 현재 위험은 `실물 원고가 바로 깨질 위험`보다 `authority 해석 surface가 어긋날 위험`이 더 크다.

## 3. Finding A: Metadata Authority Drift Can Still Recur Now

이건 `가능`이 아니라, 현재 save flow 기준으로는 거의 `설계된 분리`에 가깝다.

### 3.1 Current Save Flow

현재 Stage 4는 `PASS_WITH_FIX`일 때 `director_selections`에 pre-fix 선택 원고를 기록한다.

- [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2025)~[L2042](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2042)
  - `PASS_WITH_FIX -> selected_before_fix`
  - 그 artifact path/hash를 `save_director_selection(...)`에 저장

반면 최종 채택 원고는 `stage_attempts`에 `patched_after_fix` 또는 `final_manuscript`로 저장된다.

- [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2118)~[L2145](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2145)
- [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3376)~[L3385](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3376)
- [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L5015)~[L5039](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L5015)

즉 현재도:

- `director_selections = selected_before_fix`
- `stage_attempts = patched_after_fix/final_manuscript`

의 이중 구조가 그대로 남아 있다.

### 3.2 Why This Still Matters

더 중요한 건 `update_director_selection_rationale(...)`가 rationale/fix_scope만 동기화하고, `content_hash`나 `artifact_path`는 고치지 않는다는 점이다.

- [db_manager.py](/c:/Users/User/Desktop/글도비/modules/core/db_manager.py#L2837)~[L2871](/c:/Users/User/Desktop/글도비/modules/core/db_manager.py#L2837)

즉 patch 이후에도 `director_selections` row는 pre-fix artifact pointer를 그대로 들고 있을 수 있다. 이건 우리가 `00_260315 ep4-5`에서 직접 본 stale authority 패턴과 동일한 클래스다.

### 3.3 Current Tests Confirm The Split

이 분리는 우연한 레거시 흔적이 아니라 현재 테스트로도 고정돼 있다.

- [test_db_manager.py](/c:/Users/User/Desktop/글도비/tests/test_db_manager.py#L405)~[L448](/c:/Users/User/Desktop/글도비/tests/test_db_manager.py#L405)
  - test가 아예 `director_selections.artifact_path == selected_before_fix`
  - `stage_attempts.artifact_path == final_manuscript`
  - 를 기대한다

판정:

- `legacy stale metadata authority`는 `지금도 재발 가능`
- 더 정확히는 `현재 구조상 의도적으로 분리되어 있으며, 잘못 읽으면 같은 오판을 재현할 수 있음`

## 4. Finding B: Current Tooling Knows About The Split

그렇다고 지금 코드가 이 문제를 완전히 방치하는 건 아니다. 예전보다 나아진 지점도 분명 있다.

### 4.1 Stage 4 Canary / Audit Stance

현재 canary tooling은 이 분리를 명시적으로 인정한다.

- [stage4_canary_tools.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_canary_tools.py#L509)~[L518](/c:/Users/User/Desktop/글도비/modules/core/stage4_canary_tools.py#L509)
  - `stage_attempts provenance/rationale fields must stand on their own`
  - `director_selections is companion evidence only`

즉 운영 원칙 자체는 이미 `stage_attempts 우선`으로 기울어 있다.

### 4.2 Sink Alignment Analyzer Compensates

현재 failure analyzer는 final sink 정렬을 `stage_attempts + pass_rate_monitor + session_decisions + episode_production` 쪽으로 본다.

- [failure_analyzer.py](/c:/Users/User/Desktop/글도비/modules/core/failure_analyzer.py#L554)~[L599](/c:/Users/User/Desktop/글도비/modules/core/failure_analyzer.py#L554)
- [failure_analyzer.py](/c:/Users/User/Desktop/글도비/modules/core/failure_analyzer.py#L614)~[L624](/c:/Users/User/Desktop/글도비/modules/core/failure_analyzer.py#L614)

그리고 이 보정은 테스트로도 고정돼 있다.

- [test_failure_analyzer.py](/c:/Users/User/Desktop/글도비/tests/test_failure_analyzer.py#L550)~[L640](/c:/Users/User/Desktop/글도비/tests/test_failure_analyzer.py#L550)
  - `episode_production.selection_candidate_key`가 있으면
  - `director_selections`와 final artifact 사이의 split을 false mismatch로 보지 않도록 설계돼 있다

판정:

- `bug가 완전히 사라진 것`은 아니다
- 대신 현재는 `known split + compensating audit logic` 상태다

즉 같은 문제가 지금 재발하더라도, 예전보다 `숨은 오염`이 아니라 `감지 가능한 stale-authority risk`에 더 가깝다.

## 5. Finding C: Carryover Narrative Contradictions Can Still Be Born Upstream

화간 모순 후보가 `지금도 생길 수 있냐`에 대한 답은 `예`다. current code는 아직도 continuity를 완전한 hard gate로 쓰지 않는다.

### 5.1 Continuity Is Still Advisory-First

- [validation_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/validation/validation_orchestrator.py#L395)~[L409](/c:/Users/User/Desktop/글도비/modules/validation/validation_orchestrator.py#L395)
  - continuity failure는 즉시 hard reject가 아니라 advisory로 적재된다
- [validation_orchestrator.py](/c:/Users/User/Desktop/글도비/modules/validation/validation_orchestrator.py#L678)~[L705](/c:/Users/User/Desktop/글도비/modules/validation/validation_orchestrator.py#L678)
  - 이후 감점만 받고 `PASS / CONDITIONAL_PASS`가 여전히 가능하다

즉, `candidate stage에서 continuity drift가 발생할 가능성`은 지금도 남아 있다.

### 5.2 prev_hud Dependency Still Exists

연속성 검증은 여전히 `prev_hud` 주입 의존이 크다.

- [continuity_validator.py](/c:/Users/User/Desktop/글도비/modules/validation/continuity_validator.py#L118)~[L145](/c:/Users/User/Desktop/글도비/modules/validation/continuity_validator.py#L118)
  - `prev_hud` 없으면 degraded fail-closed
- [continuity_validator.py](/c:/Users/User/Desktop/글도비/modules/validation/continuity_validator.py#L227)~[L239](/c:/Users/User/Desktop/글도비/modules/validation/continuity_validator.py#L227)
  - DB reconstruct fallback는 없다
- [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3942)~[L3955](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L3942)
  - 실제 주입은 runtime HUD source에서 이뤄진다

즉 `carryover continuity`는 지금도 runtime context 품질에 흔들릴 수 있다.

## 6. Finding D: Current Code Also Has Stronger Guards Than The Legacy Runs Had

여기서 끝나면 과장이다. 현재는 legacy 시점보다 분명 강해진 fail-closed 장치도 있다.

### 6.1 Post-Select Continuity / History Conflict Downgrade

선택된 원고가 candidate 단계에서 통과했더라도, post-select에서 continuity/history conflict가 잡히면 `PASS -> REJECT`로 강등된다.

- [stage4_interview_round.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2852)~[L2965](/c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L2852)

이 장치는 테스트로도 살아 있다.

- [test_stage4_interview_round.py](/c:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py#L874)~[L955](/c:/Users/User/Desktop/글도비/tests/test_stage4_interview_round.py#L874)
  - post-select continuity conflict downgrade
  - post-select history conflict downgrade
  - no-conflict keep-pass

### 6.2 Failure Context Injection

이전 실패 이유와 retry directive는 현재 Stage 4 mandatory context로 다시 들어간다.

- [stage4_context_builder.py](/c:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L1681)~[L1736](/c:/Users/User/Desktop/글도비/modules/core/stage4_context_builder.py#L1681)

관련 회귀도 통과했다.

- `python -m pytest tests/test_stage4_context_builder.py -k "stage2_failure_context"`

판정:

- 현재도 모순 후보는 생길 수 있다
- 하지만 published final로 새는 경로는 legacy 시점보다 더 좁아졌다

## 7. Risk Classification

### 7.1 `stale metadata authority`

위험도: `높음`

이유:

- 현재 save flow 자체가 pre-fix / post-fix sink를 분리한다
- `update_director_selection_rationale`는 path/hash를 동기화하지 않는다
- 따라서 `director_selections 단독 사용`은 지금도 오판을 낳을 수 있다

다만:

- current tooling은 이를 `known split`로 인식하고 있으며
- `stage_attempts + episode_production`를 final authority로 보정하는 길이 생겼다

실무 판정:

- `실제 원고가 깨질 위험`이라기보다 `audit authority를 잘못 읽을 위험`

### 7.2 `carryover continuity contradiction`

위험도: `중간`

이유:

- continuity validator는 여전히 advisory-first
- `prev_hud` 의존은 여전히 남아 있다
- bounded context / trimming 구조도 근본적으로 사라진 건 아니다

다만:

- post-select fail-closed
- contradiction/history conflict downgrade
- failure context reinjection
- retry / patch loop

가 있기 때문에 `legacy final manuscript급 충돌`로 straight-through 되는 확률은 내려갔다.

실무 판정:

- `후보 단계에서는 지금도 생길 수 있음`
- `published final까지 그대로 살아남을 확률은 예전보다 낮음`

## 8. Final Answer

질문에 대한 정답은 이렇다.

1. `예전 코드베이스라서 지금은 괜찮다`는 말은 틀리다.
   - 같은 클래스의 문제가 지금도 일부는 재발 가능하다.
2. 가장 현실적인 현재 위험은 `stale metadata authority`다.
   - 이건 현재 save flow상 구조적으로 남아 있다.
3. `실물 원고 hard contradiction`은 지금도 이론상 재발 가능하지만, current code는 legacy 때보다 fail-closed 장치가 강하다.

즉 현재 운영 원칙은 이렇게 잡아야 한다.

- `director_selections`를 final authority로 쓰지 않는다.
- `stage_attempts + final/patched artifact + episode_production`을 우선한다.
- continuity 쪽은 `생성 단계에서 아직 흔들릴 수 있다`는 전제로 보되, 최종 publish 직전 fail-closed가 작동하는지 계속 감시한다.

결론적으로, `지금도 터질 수 있다`. 다만 `무엇이`, `어디서`, `어떤 형태로` 터지는지는 legacy 시점과 다르다. 현재 가장 취약한 곳은 `본문 자체`보다 `authority sink 해석 계층`이다.
