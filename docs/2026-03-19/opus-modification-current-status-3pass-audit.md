# OPUS 수정 거버넌스 현재 상태 3pass 요약

Date: 2026-03-19
Status: final
Canonical Path: `docs/2026-03-19/opus-modification-current-status-3pass-audit.md`
Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
Baseline Dirty Summary: `현재 working tree는 계속 dirty 상태이며, git status --short 기준 112개 modified/deleted/untracked entry가 존재`
Resume Commit: `same-as-baseline`
Resume Drift Summary: `같은 작업 세션 지속 중이며, governing re-audit 이후 새 커밋 앵커는 없음`
Source Governing Doc:
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`
Additional Evidence Basis:
- 저위험 realization 구간에서 실제 반영된 live code
- 항목별 targeted regression test 실행 결과
- 현재 `docs/temp/` 점검 결과: `README.md`만 존재
Scope:
- OPUS 재감리로 무엇이 확정됐는지 요약
- 그 기준 위에서 지금까지 실제로 무엇을 고쳤는지 요약
- 현재 어디까지 왔고, 다음에 무엇을 해야 하는지 정리
- non-goal: OPUS 전체를 새로 전수 재감리하는 것

---

## Pass 1. 구조와 범위

이 문서는 새 전수조사 문서가 아니다.

역할은 세 가지다.
- OPUS 문서 신뢰도 판정이 이미 어디까지 끝났는지 보여주기
- 그 판정 위에서 실제 코드 수정이 어디까지 진행됐는지 보여주기
- 이제부터는 무엇을 중위험으로 보고 다뤄야 하는지 경계를 분명히 하기

현재 OPUS 신뢰 판정의 정본은 여전히 아래 문서다.
- `docs/2026-03-19/opus-modification-governing-3pass-reaudit.md`

따라서 이 문서는 독립 패치 권한 문서가 아니라, 운영자가 빨리 상황을 파악하기 위한 한국어 현황판이다.

---

## Pass 2. 근거와 현재 상태

### 1. OPUS에 대해 이미 확정된 것

기존 재감리에서 OPUS 문서는 네 등급으로 나뉘었다.
- `VALID`
- `ADVISORY`
- `STALE`
- `NO-TRUST`

현재 실무 해석은 다음과 같다.

계획 입력으로 계속 참고 가능한 문서:
- `OPUS/ssot_execution/s2-be-fe-execution.md`
- `OPUS/ssot_execution/s3-frontend-execution.md`
- `OPUS/ssot/s5-stage0-2-internals.md`
- `OPUS/ssot/s7-rol-static-improvement.md`
- `OPUS/ssot_execution/s7-rol-improvement-execution.md`

참고용이지만 직접 패치 근거로는 못 쓰는 문서:
- `OPUS/ssot/s4-llm-integration.md`
- `OPUS/ssot_execution/s4-llm-integration-execution.md`

직접 패치 권위 문서로 쓰면 안 되는 문서:
- `OPUS/ssot/s1-architecture-overview.md`
- `OPUS/ssot_execution/s1-architecture-execution.md`
- `OPUS/ssot_execution/s5-stage0-2-execution.md`
- `OPUS/ssot/s6-stage3-4-crosscut.md`
- `OPUS/ssot_execution/s6-stage3-4-execution.md`
- `OPUS/ssot_execution/s8-0_260318-project-deepdive-execution.md`

이 판정 이후 운영 원칙도 이미 정해졌다.
- OPUS를 그대로 집행하지 않는다
- 매 항목은 live code로 다시 대조한다
- 한 번에 1개 이슈만 bounded realization 한다

### 2. 지금까지 실제로 한 일

현재 워크스페이스는 더 이상 "문서만 정리한 상태"가 아니다.
저위험 구간은 이미 상당 부분 실제 코드 반영까지 진행됐다.

완료된 작업 묶음은 크게 네 갈래다.

1. 데스크톱과 control-plane 정합성
- 프론트엔드 경로 sanitization 보강
- websocket/transport 오류 가시화
- empty `catch` 제거
- settings 복구와 restart-limit UX 보강
- preload/control-plane/package 계약 가드 추가

2. Stage 0-4 안전장치와 degraded 계약 보강
- `generate_bible` 빈 결과 fail-closed
- `ConstraintDB` degraded 계약 surface
- `FactLedger` degraded 계약 surface
- `Analyst` silent return 식별자 추가
- Stage 4 emergency manuscript dump 및 partial-save rollback 보강
- `ChainOfVerification` fail-open 차단

3. 메트릭과 ROL 관측성 보강
- Stage 2/3 `token_cost`, timing 전파
- `quality_risk` 정합성 수정
- cost table 정리
- episode ROL, arc-cost correlation 노출

4. LLM 입력 절삭 정리
- Stage 0, Stage 2, Stage 3, Stage 4
- Director, Arc, Blueprint, Critic, Continuity, CoVe, ChiefWriter
- 여러 validator/query builder

이 축에서는 앞부분만 잘라서 보내던 경로를 상당수 tail-preserving 방식으로 바꿨다.

즉 현재 상태는:
- OPUS 불신 상태에서 거버넌스를 다시 세웠고
- 그 위에서 저위험 항목은 이미 실제로 고쳤고
- 지금은 중위험 경계 앞까지 온 상태다

### 3. 지금 어디까지 왔는가

현재 경계는 분명하다.
- 쉬운 `head-only truncation` 보정은 대부분 수확했다
- 쉬운 observability/degraded/silent-failure 보정도 대부분 수확했다
- 남은 후보는 더 이상 단순 위생 수정이 아니다

남은 대표 후보는 이런 성격이다.

1. opening-only continuity 검사
- 예: `manuscript[:1000]`, `manuscript[:500]`
- 이건 단순 절삭 보정이 아니라
- "초반부에 반드시 나와야 한다"는 규칙 의미 자체를 건드린다
- 현재는 `docs/2026-03-19/continuity-opening-window-semantics-3pass-audit.md`로 정책 경계임을 고정했고,
  `tests/test_continuity_modules.py`에 rapid recovery / same-day carry-over / time-pass override 회귀를 추가했다
- 따라서 blanket patch 후보가 아니라 `keep unless policy rewrite` 구간으로 본다

2. `WriterTemplate` opening-anchor 검사
- 예: `prev_ending[-300:]`, `manuscript[:600]`
- 이건 단순 절삭 보정이 아니라
- "직전 화 말미를 현재 화 오프닝이 바로 이어받아야 한다"는 구조 규칙을 건드린다
- 현재는 `docs/2026-03-19/writer-template-opening-anchor-semantics-3pass-audit.md`로 정책 경계임을 고정했고,
  `tests/test_v55_modules.py`에 opening-anchor tail 보존 / opening 600자 검사 회귀를 추가했다
- 따라서 이것도 `keep unless policy rewrite` 구간으로 본다

3. `_inplace_patch_arc()`의 `30KB` fail-closed 정책
- 이건 단순 잘림 보정이 아니라
- patch와 rewrite를 어디서 갈라치는지 정책 경계를 건드린다

4. `ValidationOrchestrator` episode-type adaptive threshold
- 예: opening `+5`, transition `-3`, arc finale `+5`, volume finale `+7`
- 이건 단순 매직넘버 정리가 아니라
- 화수 유형별로 PASS 기준 압력을 다르게 거는 운영 규칙을 건드린다
- 현재는 `docs/2026-03-19/validation-orchestrator-episode-threshold-semantics-3pass-audit.md`로 정책 경계임을 고정했고,
  `tests/test_validation_orchestrator.py`에 opening `+5`, ep5 `+2`, ep50 `+7` 회귀를 추가했다
- 따라서 이것도 `keep unless policy rewrite` 구간으로 본다

5. `Blueprint` local patch safety/routing semantics
- 이건 단순 잘림 보정이 아니라
- Blueprint 로컬 수정의 `30KB` 가드, `partial/full/inplace` 라우팅, `F-2` advisory를 어디서 갈라치는지 정책 경계를 건드린다
- 현재는 `docs/2026-03-19/blueprint-inplace-30kb-fallback-consistency-3pass-audit.md`와
  `docs/2026-03-19/stage3-blueprint-local-patch-routing-semantics-3pass-audit.md`로
  `30KB 가드 유지`, `Stage 3 partial=single-strategy regenerate`, `Stage 3 full=full regenerate`, `inplace 실패 시 fallback`, `F-2 warning-only`, `Stage 4 B-Light 1회 regen fallback`을 고정했다
- `tests/test_blueprint_patch_mode.py`, `tests/test_inplace_reliability.py`, `tests/test_v75b_escalation.py`로 회귀를 확인했다
- 따라서 이것도 `keep unless policy rewrite` 구간으로 본다

6. `ChiefWriter` in-place `150K` truncation 정책
- 이건 단순 head-cut 보정이 아니다. 긴 원고를 local patch 경로에서 어디까지 prompt budget 안에 싣고 계속 진행할지에 대한 정책 경계를 건드린다
- 현재는 `docs/2026-03-19/chief-writer-inplace-150k-truncation-semantics-3pass-audit.md`로 `150K cap 유지`, `warn + continue`, `tail-preserving 유지`를 고정했다
- `tests/test_chief_writer.py`에 direct prompt/feedback tail 보존 회귀를 추가했다
- 따라서 이것도 `keep unless policy rewrite` 구간으로 본다

7. `Stage4InterviewRound` local patch decision tree
- 이건 단순 분기 정리가 아니다. retry round에서 `inplace_patch`, `patch_with_feedback`, `regenerate_with_feedback`를 어떤 계약으로 갈라치는지에 대한 정책 경계를 건드린다
- 현재는 `docs/2026-03-19/stage4-local-patch-decision-tree-semantics-3pass-audit.md`로 `round0=ensemble`, `Director contract -> runtime repair lane routing`, `retry=explicit local contract only`, `post_select_conflict는 1회 force-patch`, `REJECT patch는 single-strategy bounded regenerate`, `PASS_WITH_FIX는 valid fix_pack 필수`를 고정했다
- `tests/test_stage4_interview_round.py`와 `tests/test_pass_with_fix.py`의 stale 기대값도 live semantics에 맞게 정렬했다
- 따라서 이것도 `keep unless policy rewrite` 구간으로 본다

8. `Stage4` `F-2` high patch-pressure advisory
- 이건 단순 로그 문구가 아니다. inplace patch 변경 비율이 높을 때 자동 차단으로 볼지, Director 재심사 warning으로 볼지에 대한 정책 경계를 건드린다
- 현재는 `docs/2026-03-19/stage4-f2-patch-pressure-advisory-semantics-3pass-audit.md`로 `change_ratio 기록`, `patch_trace 유지`, `Director 재심사 warning 주입`, `자동 REJECT 아님`, `Director 주권 하의 judgment input`을 고정했다
- `tests/test_pass_with_fix.py`에 direct advisory 회귀를 추가했다
- 따라서 이것도 `keep unless policy rewrite` 구간으로 본다

9. `Stage4` local patch hard guards
- 이건 단순 품질 경고가 아니다. `min_patched_length`와 `inplace_min_preserve_ratio`를 warning으로 볼지, 실제 차단 guard로 볼지에 대한 정책 경계를 건드린다
- 현재는 `docs/2026-03-19/stage4-local-patch-hard-guards-semantics-3pass-audit.md`로 `PASS_WITH_FIX 루프에서는 inplace contract fail을 명시 기록하고 next retry를 partial patch로 이관`, `retry 경로에서는 inplace 차단 후 patch fallback`, `F-2와 별도`, `same-attempt emergency patch 확장은 보류`를 고정했다
- 기존 회귀는 `tests/test_pass_with_fix.py`, `tests/test_stage4_interview_round.py`에 이미 있다
- 따라서 이것도 `keep unless policy rewrite` 구간으로 본다

10. `Stage2` `F-2` high patch-pressure advisory
- 이건 단순 warning이 아니다. inplace Arc patch 변경 비율이 높을 때 verdict까지 강등할지, 아니면 Director warning + metadata persistence로 처리할지에 대한 정책 경계를 건드린다
- 현재는 `docs/2026-03-19/stage2-f2-patch-pressure-downgrade-semantics-3pass-audit.md`로 `patch_pressure 기록`, `advisory_flags 저장`, `Director 재심사 story_context에 F-2 warning 주입`, `Director PASS면 PASS 유지`로 정렬했다
- 기존 회귀는 `tests/test_stage2_finalizer.py`에 이미 있다
- 따라서 이것도 `keep unless policy rewrite` 구간으로 본다

11. `Stage2` explicit `fix_scope` authority 정렬
- 이건 단순 구현 흔들림이 아니라, `PASS_WITH_FIX`에서 명시 scope가 없을 때 score fallback을 허용하던 Stage2를 Stage4식 explicit contract에 맞춘 정책 정렬이다
- 현재는 `docs/2026-03-19/stage2-fix-scope-explicit-contract-alignment-3pass-audit.md`로 `Stage2Finalizer`와 `Stage2Preflight` 모두 `fix_scope` 누락 시 local patch 권한 없음으로 정렬했다
- 관련 회귀는 `tests/test_pass_with_fix.py`, `tests/test_stage2_preflight.py`에 반영했다
- 따라서 이전 cross-stage divergence는 active boundary가 아니라 `resolved alignment`로 본다

12. `Stage2` local patch hard guards
- 이건 단순 patch 실패 처리 메모가 아니다. Stage2 local Arc patch에서 무엇이 blocking guard이고, 무엇이 advisory인지에 대한 정책 경계를 건드린다
- 현재는 `docs/2026-03-19/stage2-local-patch-hard-guards-semantics-3pass-audit.md`로 `missing/falsy patch는 blocking`, `patch pressure는 advisory`, `patch_guard_signals는 관찰용`, `Stage4와 동일 스택 아님`을 고정했다
- 기존 회귀는 `tests/test_stage2_finalizer.py`, `tests/test_pass_with_fix.py`에 이미 있다
- 따라서 이것도 `keep unless policy rewrite` 구간으로 본다

13. `Stage2` local patch hard guards 비교
- 이건 Stage4 항목의 단순 복제가 아니다. Stage2가 manuscript text가 아니라 structured Arc dict를 패치하기 때문에 같은 `min_patched_length` / `preserve_ratio` guard 비교 자체가 비적용에 가깝다
- 현재는 `docs/2026-03-19/stage2-local-patch-hard-guards-applicability-3pass-audit.md`와 `docs/2026-03-19/stage2-arc-patch-observability-signals-3pass-audit.md`로 `Stage4식 hard guard는 없음`, `대신 patch pressure`, `explicit fix_scope authority`, `patch_guard_signals`가 실제 경계`, `signal 승격은 live evidence 전까지 보류`라는 점을 고정했다
- 따라서 이 항목은 `bug`가 아니라 `non-applicable/absent boundary`로 본다

14. `재귀개선` follow-up 분리
- 이건 현재 Stage2 Arc patch 관찰 신호 작업에 붙여서 바로 구현할 항목이 아니다
- `patch_guard_signals`를 다음 retry prompt와 `previous_attempt` handoff로 다시 흘리는 순간, observability가 아니라 retry-policy / prompt-shaping 정책 변경이 된다
- 현재는 `docs/2026-03-19/recursive-improvement-followup-separation-3pass-audit.md`로 `별도 후속`, `현재는 보류`, `나중에 system-design item으로 재개`를 고정했다
- 따라서 이 항목은 `현재 활성 수정 항목`이 아니라 `deferred follow-up`으로 본다

15. `failure_analyzer` proof-digest DB facade mismatch
- 이건 project-specific S8에서 올라온 이슈 중 예외적으로 live generic code defect로 재검증된 항목이다
- 현재는 `docs/2026-03-19/failure-analyzer-proof-digest-db-facade-3pass-audit.md`로 `proof-digest read-only facade가 FailureAnalyzer 최소 DB contract를 만족`, `DBManager boot 재진입 없음`, `runtime health soft failure 회귀 차단`까지 반영했다
- 관련 회귀는 `tests/test_audit_service.py`, `tests/test_bridge_quality_summary.py`에 반영했다
- 따라서 이 항목은 `완료된 high-ROI 예외 수정`으로 본다

16. `BlueprintEnsemble` `last_error_type` shared-state race
- 이건 OPUS remaining high/ROI screening에서 살아남은 bounded high-ROI 항목이다
- 현재는 `docs/2026-03-19/blueprint-ensemble-last-error-type-race-3pass-audit.md`로 `worker error bundle 집계`, `schema_incompatible 우선 fast-fail`, `stale single-field state 완화`까지 반영했다
- 관련 회귀는 `tests/test_tier4_ensemble_caching.py`, `tests/test_blueprint_patch_mode.py`에 반영했다
- 따라서 이 항목은 `완료된 bounded high-ROI 수정`으로 본다

17. `BaseAgent` ambiguous `429` classification
- 이건 OPUS remaining high/ROI screening에서 살아남은 bounded high-ROI 항목이다
- 현재는 `docs/2026-03-19/base-agent-ambiguous-429-classification-3pass-audit.md`로 `bare 429는 same-model backoff 대신 fallback/quota lane`, `explicit rate-limit wording은 기존 backoff 유지`까지 반영했다
- 관련 회귀는 `tests/test_base_agent.py`, `tests/test_sweep18.py`, `tests/test_edge_cases.py`에 반영했다
- 따라서 이 항목은 `완료된 bounded high-ROI 수정`으로 본다

18. `BaseAgent` key-exhaustion operator signal
- 이건 OPUS remaining high/ROI screening에서 살아남은 bounded high-ROI 항목이다
- 현재는 `docs/2026-03-19/base-agent-key-exhaustion-operator-signal-3pass-audit.md`로 `key rotation unavailable reason surface`, `all_keys_exhausted operator warning`, `fallback policy 유지`까지 반영했다
- 관련 회귀는 `tests/test_base_agent.py`, `tests/test_sweep18.py`에 반영했다
- 따라서 이 항목은 `완료된 bounded high-ROI 수정`으로 본다

19. `Stage3` degraded-success dashboard observability
- 이건 OPUS remaining high/ROI screening에 남아 있던 `Stage 3 emergency fallback returns PASS_WITH_WARNING` 항목의 bounded follow-up이다
- 현재는 `docs/2026-03-19/stage3-pass-with-warning-dashboard-observability-3pass-audit.md`로 `PASS_WITH_WARNING dashboard preservation`, `quality_gate_failed / quality_risk warning surface`, `dashboard pass aggregation 정합화`까지 반영했다
- 관련 회귀는 `tests/chaos/test_stage3_metrics.py`, `tests/test_stage3_orchestrator.py`, `tests/test_bridge_quality_summary.py`, `tests/integration/test_patch_wiring.py`에 반영됐다
- 이 항목은 `관측성 보강은 완료`, `emergency fallback semantic policy는 keep unless policy rewrite`로 본다

20. `PASS_WITH_WARNING` verdict enum drift
- 이건 OPUS remaining high/ROI screening에서 새로 살아난 bounded high-ROI 계약 drift 항목이다
- 현재는 `docs/2026-03-19/pass-with-warning-verdict-enum-drift-3pass-audit.md`로 `DIRECTOR_AUDIT_SCHEMA`, `STRATEGIC_AUDIT_SCHEMA`의 decision enum에 `PASS_WITH_WARNING`을 반영했다
- 관련 회귀는 `tests/test_llm_schema.py`, `tests/test_pass_with_fix.py`, `tests/test_director_modules.py`에 반영됐다
- 따라서 이 항목은 `완료된 bounded high-ROI 수정`으로 본다

21. `Preflight` hollow previous-arc input gap
- 이건 Stage 2 preflight가 속 빈 이전 Arc를 그대로 `PreflightChecker.analyze()`에 넘기던 bounded 입력 위생 결함이다
- 현재는 `docs/2026-03-19/preflight-hollow-prev-arcs-input-gap-3pass-audit.md`로 `blank/missing tactical_doc skip`, `audit/log signal`, `_input_hygiene metadata`까지 반영했다
- 관련 회귀는 `tests/test_stage2_preflight.py`, `tests/test_pass_with_fix.py`에 반영됐다
- 따라서 이 항목은 `완료된 bounded high-ROI 수정`으로 본다

22. `QualityDashboard` persistence operator signal
- 이건 quality metric sink write 실패가 warning 로그에만 머물던 bounded 운영 신호 결함이다
- 현재는 `docs/2026-03-19/quality-dashboard-persistence-operator-signal-3pass-audit.md`로 `persistence_health in-memory summary`, `soft_failures.jsonl append`, `runtime_health surface`까지 반영했다
- 관련 회귀는 `tests/test_quality_regression.py`, `tests/test_bridge_quality_summary.py`에 반영됐다
- 따라서 이 항목은 `완료된 bounded high-ROI 수정`으로 본다

즉 지금부터는 자동으로 계속 밀어도 되는 저위험 구간이 아니라, 항목별로 다시 승인하고 들어가야 하는 중위험 구간이다.

### 4. 검증 상태

검증 방식은 지금까지 일관됐다.
- 항목별 targeted regression test 추가
- `pytest`는 low-memory 순차 shard 위주 실행
- 각 저위험 항목의 관련 샤드는 통과 확인
- 아직 전체 저장소 full suite를 한 번에 다시 돌린 상태는 아님

현재 confidence 해석:
- 저위험 realization 완료 상태: 신뢰도 높음
- 중위험 정책 변경: 아직 이 문서만으로 착수 승인된 상태는 아님

---

## Pass 3. 운영상 의미와 다음 단계

### 이 상태가 의미하는 것

1. OPUS 신뢰 문제는 이미 한 번 정리됐다.
- 지금 다시 OPUS 신뢰 여부를 처음부터 묻는 단계는 아니다
- 그 판단은 이미 governing re-audit에 남아 있다

2. 저위험 구간은 이미 문서 단계가 아니라 실행 단계까지 왔다.
- 지금은 계획만 있는 상태가 아니다
- 실제 코드 수정과 회귀 검증이 누적된 상태다

3. 다음부터는 자동 전진이 아니라 항목별 중위험 판단이 필요하다.
- 남은 항목은 규칙 의미나 fallback 정책을 건드릴 수 있다

### 이제 해야 할 일

권장 순서:
1. 이 문서를 운영 현황판으로 유지
2. 중위험 후보를 정확히 1개 고르기
3. 그 1개만 대상으로 current-state execution note를 새로 쓰거나 갱신
4. 그 1개만 패치
5. targeted regression shard 실행
6. 다시 감리 후 다음 항목 선택

현재 추천 중위험 후보:
1. continuity opening-window semantics
- 현재는 `유지` 쪽 결론이 우세하다
- 바꾸려면 규칙별 정책 재설계로 들어가야 한다

2. `WriterTemplate` opening-anchor semantics
- 현재는 `유지` 쪽 결론이 우세하다
- 바꾸려면 opening reconnection 규칙을 다시 정의해야 한다

3. `_inplace_patch_arc()` `30KB` fail-closed 정책
- 현재는 `가드 유지`로 정리됐다
- 남은 일은 호출부 차이를 운영 문서와 회귀로 계속 명확히 하는 쪽이다

4. `ValidationOrchestrator` episode-type threshold semantics
- 현재는 `유지` 쪽 결론이 우세하다
- 바꾸려면 opening/transition/finale 압력과 overlap stacking 규칙을 다시 정의해야 한다

5. `Blueprint` local patch safety/routing semantics
- 현재는 `가드 유지 + contract-driven routing 유지 + F-2 warning-only 유지`로 정리됐다
- 남은 일은 Stage 3 generator와 Stage 4 caller 차이를 계속 문서와 회귀로 명확히 하는 쪽이다

6. `ChiefWriter` in-place `150K` truncation 정책
- 현재는 `warn + continue + tail-preserving 유지`로 정리됐다
- 바꾸려면 manuscript local patch budget 자체를 다시 설계하는 정책 변경으로 들어가야 한다

7. `Stage4InterviewRound` local patch decision tree
- 현재는 `explicit local contract only`로 정리됐다
- 바꾸려면 Stage4 repair routing 자체를 다시 설계하는 정책 변경으로 들어가야 한다

8. `Stage4` `F-2` high patch-pressure advisory
- 현재는 `warning-only`로 정리됐다
- 바꾸려면 Stage4 local patch pressure를 hard gate로 승격할지에 대한 정책 변경으로 들어가야 한다

9. `Stage4` local patch hard guards
- 현재는 `blocking guard`로 정리됐다
- 바꾸려면 Stage4 local patch safety stack 자체를 다시 설계하는 정책 변경으로 들어가야 한다

10. `Stage2` `F-2` high patch-pressure advisory
- 현재는 `warning + metadata persistence + Director-context injection`으로 정리됐다
- 바꾸려면 Stage2 Arc local patch confidence 정책 자체를 다시 설계하는 정책 변경으로 들어가야 한다

11. `Stage2` explicit `fix_scope` authority 정렬
- 현재는 `resolved alignment`로 정리됐다
- 남은 일은 이 정렬을 다시 score fallback으로 되돌리지 않도록 회귀를 유지하는 쪽이다

12. `Stage2` local patch hard guards
- 현재는 `blocking guard + advisory split`으로 정리됐다
- 바꾸려면 Stage2 local patch safety model 자체를 다시 설계하는 정책 변경으로 들어가야 한다

12. `Stage2` local patch hard guards 비교
- 현재는 `non-applicable / absent`로 정리됐다
- 바꾸려면 Arc patch에 맞는 별도 safety model을 설계해야 한다

명시적 비권장 사항:
- OPUS 문서를 다시 queue authority처럼 직접 집행하지 말 것
- 이 현황 요약 문서를 단독 패치 권한 문서처럼 쓰지 말 것

### 추가 메모: `inplace` fail-closed caller split

`_inplace_patch_arc()`의 `30KB` fail-closed 경계는 별도 감리 결과 의도된 안전장치로 유지하는 쪽이 맞다고 정리됐다.

현재 확정된 해석:
- preflight 경로: `inplace 실패 -> 같은 시도 안에서 patch fallback`
- finalizer 경로: `inplace 실패 -> REJECT -> retry`로 상위 루프에 위임
- Stage 3 Blueprint 경로: `inplace 실패 -> 같은 시도 안의 full rewrite fallback`, `PASS_WITH_FIX + partial -> single-strategy regenerate`, `PASS_WITH_FIX + full -> full regenerate`
- Stage 4 Blueprint B-Light 경로: `inplace 실패 -> bounded Blueprint regenerate 1회`

즉 이 항목의 핵심 문제는 가드 자체보다 OPUS 문서가 이 차이를 뭉개서 서술한 점이었다.
관련 정본: `docs/2026-03-19/inplace-30kb-fallback-consistency-3pass-audit.md`
관련 비교표: `docs/2026-03-19/inplace-fail-closed-caller-split-cross-stage-map-3pass-audit.md`

---

## Confidence Gate

이 문서의 bounded status-summary 목적에 대한 추정 신뢰도: **96%**

95%를 넘는 이유:
- 기존 governing re-audit에 직접 앵커링되어 있음
- 새 전수조사를 했다고 과장하지 않음
- 현재 상태를 보수적으로만 요약함
- 저위험 구간과 중위험 경계를 흐리지 않고 분리함
