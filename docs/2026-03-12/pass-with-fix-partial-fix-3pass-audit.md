# PASS_WITH_FIX Partial-Fix 3-Pass Audit

작성일: 2026-03-12  
범위: Stage 2, Stage 3, Stage 4, Director prompt/schema, logging sinks, analytics, runtime artifacts, regression tests  
목적: `PASS_WITH_FIX`가 실제로 "부분 수정" 취지대로 작동하는지, 작동 중 압축/왜곡이 발생하지 않는지, 문서/구현/관측값이 같은 의미를 쓰는지 전수 재감리

관련 문서:

- `docs/2026-03-12/pass-with-fix-master-roadmap.md`
- `docs/2026-03-12/pass-with-fix-phase1-execution-spec.md`
- `docs/2026-03-12/pass-with-fix-improvement-execution-plan.md`
- `docs/2026-03-12/stage4-live-rerun-checklist.md`

## 0. 최종 판정

한 줄 결론:

- `PASS_WITH_FIX`의 "부분 수정" 철학 자체는 현재 코드베이스에서 분명히 살아 있다.
- 특히 Stage 2와 Stage 4는 `fix_scope=inplace`를 중심으로 "전면 재생성 대신 국소 패치"를 실제로 수행한다.
- 다만 시스템 전체 의미는 아직 완전히 정합하지 않다.
- 가장 큰 잔여 이슈는 `PASS_WITH_FIX`가 어떤 레이어에서는 "중간 상태", 다른 레이어에서는 "최종 성공"처럼 동시에 소비된다는 점이다.

감리 결론:

- "부분 수정 취지에 맞는가?" → `대체로 예`, 단 `Stage 3/관측 계층/분석 계층`까지 포함하면 `부분적 정합`
- "작동 중 압축 왜곡이 발생하지 않겠는가?" → `주요 manuscript shrink 경로는 현재 guard로 상당 부분 차단`, 그러나 `관측 의미 왜곡`과 `컨텍스트 trim 기반 품질 왜곡`은 잔존
- "진짜 end-to-end로 제대로 작동하는가?" → `아직 아니오`

최종 확신도: `95%`

근거:

- 코드 경로 직접 재감리
- 관련 문서 SSOT 상호 대조
- `projects/00_test_01`, `00_test_02`, `00_test_03` 산출물 교차 확인
- 관련 회귀 테스트 314개 재실행

## 1. 감사 방법

### Pass 1. 명세/문서/로깅 의도 확인

검토 문서:

- `docs/2026-03-01/verdict-logic-spec.md`
- `docs/stage_map/interfaces.md`
- `docs/stage_map/gotchas.md`
- `docs/stage_map/stage2.md`
- `docs/stage_map/stage3.md`
- `docs/stage_map/stage4.md`
- `docs/2026-03-11/TF-IPG-inplace-patch-guard.md`
- `docs/2026-03-11/logging-system-audit-95.md`
- `docs/2026-03-04/codex-order-PASS_WITH_FIX-audit.md`
- `docs/컨텍스트_활용_조사_결과.md`

중점 질문:

- `PASS_WITH_FIX`는 과도 상태인가, 최종 성공 verdict인가
- QualityGate가 `PASS_WITH_FIX`에 적용되는가
- "부분 수정"의 허용 범위와 shrink 금지 원칙이 무엇인가
- 어떤 로그 sink가 최초 verdict를 저장하고 어떤 sink가 최종 verdict를 저장하는가

### Pass 2. 실제 코드 경로 전수 확인

검토 코드:

- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_orchestrator.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/director_auditor.py`
- `modules/core/constants.py`
- `modules/core/failure_analyzer.py`
- `modules/core/db_manager.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/context_compression.py`
- `config/prompts/director.yaml`
- `config/prompts/chief_writer.yaml`
- `modules/core/response_schemas.py`

중점 질문:

- `fix_scope=inplace`가 실제로 국소 수정 경로를 타는가
- 재심사 후 `PASS`가 나왔을 때 최종 verdict/score/label/log가 모두 같은 의미로 갱신되는가
- shrink/compression guard가 실제 코드에 있는가
- Stage 3/4 외부 공개 verdict가 과도 상태를 누출하는가

### Pass 3. 테스트와 실산출물 대조

확인 산출물:

- `projects/00_test_01/logs/episode_production.jsonl`
- `projects/00_test_02/logs/episode_production.jsonl`
- `projects/00_test_03/logs/episode_production.jsonl`
- `projects/00_test_01/logs/pass_rate_monitor.json`
- `projects/00_test_02/logs/pass_rate_monitor.json`
- `projects/00_test_03/logs/pass_rate_monitor.json`
- `projects/00_test_01/project_data.db`
- `projects/00_test_02/project_data.db`
- `projects/00_test_03/project_data.db`

재실행 테스트:

```powershell
pytest -q tests/test_pass_with_fix.py tests/test_stage4_interview_round.py tests/test_stage3_orchestrator.py tests/test_stage2_finalizer.py tests/test_inplace_reliability.py tests/test_chief_writer.py tests/test_pipeline_audit_00.py tests/test_failure_analyzer.py tests/test_db_manager.py
```

결과:

```text
314 passed in 48.40s
```

## 2. "부분 수정" 취지와 실제 구현

### 2.1 Director와 Chief Writer 프롬프트는 명확히 partial-fix 지향이다

`config/prompts/director.yaml`은 반복적으로 다음을 요구한다.

- `PASS_WITH_FIX`는 score 90 이상 + 잔여 미비가 있을 때 사용
- `fix_scope`를 `inplace` / `partial` / `full` 중 하나로 반드시 판단
- 경미한 모순은 그냥 넘기지 말고 `PASS_WITH_FIX + inplace`로 교정 기회를 줄 것

즉, 의도 수준에서는 `PASS_WITH_FIX`는 "거의 합격이지만 부분 수정 필요"를 명시적으로 의미한다.

`config/prompts/chief_writer.yaml`의 patch mode도 같은 철학이다.

- 원고 전체 재작성 대신 수정 대상만 고칠 것
- 수정본은 원고 대부분을 보존할 것
- "요약성 대폭 축소 금지"
- 최소 글자 수 유지
- 끝에 `[원고_끝]` 마커 강제

이 부분은 "부분 수정" 의도와 강하게 정합적이다.

### 2.2 Stage 2는 partial-fix 철학을 비교적 잘 구현한다

`modules/core/stage2_finalizer.py` 핵심:

- `PASS_WITH_FIX`면 최대 3회 inplace patch + Director 재심사
- `fix_scope=partial/full`이면 inplace를 포기하고 retry 경로로 위임
- 재심사 `PASS`가 quality gate 미달이면 실패 처리
- 재심사 성공 시 `_score = _re_s`로 최종 점수를 갱신

이 마지막 점이 중요하다. Stage 2는 성공적으로 수정 완료된 결과를 최종 점수로 덮어써서 stale score를 남기지 않는다.

판정:

- Stage 2는 현재 의도와 기능이 `대체로 정합`

### 2.3 Stage 4도 partial-fix 철학 자체는 살아 있다

`modules/core/stage4_interview_round.py` 핵심:

- `PASS_WITH_FIX`면 `_execute_pass_with_fix_loop()` 진입
- 최대 3회 `chief_writer.inplace_patch()` + Director 재심사
- `fix_scope=partial/full`이면 inplace를 포기하고 retry 경로로 위임
- 반복 `PASS_WITH_FIX` 소진 시 마지막 patch본을 채택한 채 `REJECT` 종료 가능

즉 Stage 4도 "전면 재생성보다 국소 수정 우선"이라는 설계를 실제로 갖고 있다.

판정:

- Stage 4의 수정 철학은 `부분 수정 취지에 부합`

## 3. 압축 왜곡 리스크 판단

### 3.1 현재 가장 직접적인 shrink 리스크는 이미 방어가 들어갔다

트리거 문서 `docs/2026-03-11/TF-IPG-inplace-patch-guard.md`는 `00_test_03 ep_0003`에서 실제 문제가 있었음을 기록한다.

- Round 1: `PASS_WITH_FIX`
- inplace patch 이후 원고가 `5000+` 수준에서 `2769` 수준으로 크게 축소
- 절대 하한(`min_patched_length=2000`)만 통과하고 실질 보존 실패
- 이후 연쇄 REJECT

현재는 이 경로에 guard가 추가돼 있다.

구현 확인:

- `modules/domain/agents/chief_writer.py`
  - `[원고_끝]` 마커 검증
  - 잘림 가능성 경고
- `modules/core/stage4_interview_round.py`
  - `patch_mode.min_patched_length`
  - `patch_mode.inplace_min_preserve_ratio = 0.70`
  - 원본 대비 70% 미만 보존 시 patch 폐기
- REJECT retry 경로에도 동일 보호가 추가됨

판정:

- Stage 4 manuscript patch shrink 리스크는 `현재 기준 상당 부분 완화`

### 3.2 그래도 "압축 왜곡"이 완전히 0은 아니다

남아 있는 경로:

- `modules/core/stage4_context_builder.py`는 여전히 budget 초과 시 `_smart_trim()` 기반 trim을 수행한다
- `modules/domain/agents/director_ensemble.py`도 `mandatory_context`를 길이 제한 안에서 일부 자른다
- `modules/core/context_compression.py` 자체가 head/tail 보존 trim 전략을 사용한다

이것은 manuscript 본문 shrink와는 다른 종류의 왜곡이다.

- 본문 자체를 줄이는 왜곡은 guard가 생겼다
- 그러나 Director/Writer가 보는 문맥이 trim되며 판단 품질이 흔들리는 리스크는 여전히 있다

판정:

- "부분 수정 중 본문이 요약돼 망가지는가?" → 과거보다 크게 줄었다
- "문맥 압축으로 품질 왜곡이 완전히 사라졌는가?" → 아니다

## 4. 가장 큰 남은 문제: 의미 일관성 붕괴

### 4.1 Stage 4는 최초 verdict와 최종 verdict를 서로 다른 sink에 저장한다

`modules/core/stage4_interview_round.py` 흐름:

1. Director 최초 verdict를 받은 직후
2. session logger 기록
3. `director_selections` 저장
4. `episode_production.jsonl` append
5. 그 다음 `_process_verdict()`에서 `PASS_WITH_FIX` patch loop 수행
6. 최종 `PASS` 또는 `REJECT`를 `stage_attempts` 등에 기록

즉, 관측 계층에서 같은 시도에 대해 두 종류의 의미가 동시에 남는다.

- `episode_production.jsonl` / `director_selections` = 초기 Director 판단
- `stage_attempts` / `pass_rate_monitor.json` = patch loop 이후 최종 결과

실산출물 증거 (`projects/00_test_03`):

- `logs/episode_production.jsonl`
  - ep1 round1 = `PASS_WITH_FIX`
  - ep3 round1 = `PASS_WITH_FIX`
- `project_data.db`의 `director_selections`
  - 같은 round를 `PASS_WITH_FIX`로 저장
- 같은 DB의 `stage_attempts`
  - ep1 attempt2는 최종 `PASS`
  - ep3 attempt2는 최종 `REJECT`
- `logs/pass_rate_monitor.json`
  - 같은 시도를 `success=true/false`로 최종화된 결과만 집계

운영상 의미:

- "PWF가 발생했는지"는 잘 보인다
- 그러나 "그 시도의 최종 결과가 무엇이었는지"는 sink마다 다르게 보인다

판정:

- logging/observability 차원에서는 `정합하지 않음`

### 4.2 Stage 4는 patch 후 PASS여도 최종 score와 quality label을 갱신하지 않는다

이것이 현재 코드상 가장 강한 기능 결함이다.

`modules/core/stage4_interview_round.py`에서:

- `_execute_pass_with_fix_loop()`는 patch 후 재심사 `PASS`를 받을 수 있다
- 하지만 `_process_verdict()`가 최종 저장할 때 사용하는 `score`는 최초 Director score 변수다
- 이후 `final_state_updates["director_score"]`
- `_director_quality_labels["score"]`
- `_record_s4_attempt(... score=score ...)`
  모두 최초 점수를 사용한다

반면 Stage 2는 같은 상황에서 `_score = _re_s`로 갱신한다.

즉 Stage 4는 다음 조합이 가능하다.

- 최종 verdict = `PASS`
- 저장 score/quality labels = 최초 `PASS_WITH_FIX` 심사 점수

이것은 "부분 수정이 완료돼 PASS가 됐다"는 의미와 "아직 수정 전 audit 상태"를 한 레코드에 혼합한다.

판정:

- 기능 정합성 측면에서 `높은 심각도 불일치`

### 4.3 Stage 3는 아직 `PASS_WITH_FIX`를 외부 성공 verdict로 내보낸다

`modules/domain/agents/three_phase_blueprint_generator.py`:

- `pipeline_result["final_verdict"] = verdict`
- 초기에 `PASS_WITH_FIX`도 그대로 보존

이후 patch loop가 있긴 하지만, 오케스트레이터는 여전히:

- `modules/core/stage3_orchestrator.py`
  - `PASS`, `PASS_WITH_FIX`, `PASS_WITH_WARNING`를 모두 success 경로로 처리

테스트도 이 의미를 고정한다.

- `tests/test_pass_with_fix.py`
  - `final_verdict in ("PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING")`면 success

즉 Stage 3는 아직 "과도 상태는 외부로 노출되지 않는다"는 모델과 맞지 않는다.

판정:

- Stage 3는 현재 `PASS_WITH_FIX`를 사실상 soft success로 취급
- "반드시 PASS/REJECT로 붕괴" 모델과는 `불정합`

## 5. 문서 SSOT 자체가 갈라져 있다

### 5.1 오래된 verdict spec

`docs/2026-03-01/verdict-logic-spec.md`는 다음처럼 적고 있다.

- `PASS_WITH_FIX`는 과도 상태
- 전 Stage에서 반드시 `PASS` 또는 `REJECT`로 전환
- `score < 90`이면 `PASS_WITH_FIX`도 QualityGate로 불허

### 5.2 현재 stage_map 문서

`docs/stage_map/interfaces.md`, `gotchas.md`, `stage2.md`, `stage3.md`, `stage4.md`는 다음처럼 적고 있다.

- `PASS_WITH_FIX`는 Director verdict 3종 중 하나
- 최초 진입 시 QualityGate bypass
- patch loop 기회를 부여

이 둘은 동시에 참일 수 없다.

정리:

- 현재 런타임 구현은 `TF-46 bypass` 쪽에 더 가깝다
- 하지만 문서 SSOT가 둘로 갈라져 있으므로 "의도와 기능 정합성" 판정이 흔들린다

판정:

- 문서 레벨 SSOT 불일치 `높음`

## 6. 분석 계층도 PASS_WITH_FIX를 성공으로 소비한다

`modules/core/failure_analyzer.py`:

- `top_success_patterns()`에서 `PASS_WITH_FIX` 포함
- `compare_versions()` pass count에 포함
- `stage_pass_rates()` pass 수치에 포함

`modules/core/db_manager.py`:

- `get_recent_episode_scores()`가 `verdict IN ('PASS', 'PASS_WITH_FIX')`

즉 downstream 보고서는 `PASS_WITH_FIX`를 "수정 대기 중 상태"보다 "통과"에 가깝게 해석한다.

판정:

- 운영 분석 계층은 `PASS_WITH_FIX = pass-like success` 모델을 사용 중
- 과도 상태 모델과 `불일치`

## 7. 테스트 커버리지 평가

좋은 점:

- `tests/test_pass_with_fix.py`는 S2/S3/S4 patch loop 주요 분기를 폭넓게 커버
- `tests/test_stage4_interview_round.py`는 director metadata 저장, post-select conflict, reduced strategy budget, round cost logging, episode log 비차단 등을 커버
- `tests/test_failure_analyzer.py`, `tests/test_db_manager.py`는 downstream 집계 의미를 고정

부족한 점:

- Stage 4에서 `PASS_WITH_FIX -> patch -> PASS` 후 `director_score`와 `_director_quality_labels.score`가 재심사 점수로 갱신되는지 검증하는 테스트는 보이지 않았다
- Stage 4에서 같은 시도에 대해 `episode_production`과 `stage_attempts`가 의도적으로 서로 다른 의미를 쓰는지, 또는 같아야 하는지 검증하는 테스트도 없다

판정:

- 핵심 patch loop는 잘 커버됨
- 그러나 `최종 의미 정합성` 테스트는 아직 약하다

## 8. 종합 결론

### 8.1 "부분 수정" 취지에 맞는가

`예, 그러나 Stage 2/4 중심으로만 그렇다.`

이유:

- prompt 설계가 명확히 partial-fix 지향
- Stage 2와 Stage 4는 실제로 국소 patch loop를 수행
- `fix_scope=partial/full` 분기까지 살아 있음
- Stage 4 manuscript shrink guard도 추가됨

### 8.2 "압축 왜곡"은 발생하지 않겠는가

`주요 원고 shrink 경로는 현재 꽤 잘 막혀 있다.`

그러나 아래는 남아 있다.

- context budget trim에 따른 판단 왜곡 가능성
- `PASS_WITH_FIX` 의미가 로그/분석에서 서로 다르게 보이는 관측 왜곡
- Stage 4의 stale score 저장으로 인한 결과 의미 왜곡

### 8.3 "진짜 제대로 작동하냐"

`아직 완전한 yes는 아니다.`

가장 정확한 표현은 다음이다.

- Writer/Director 수준의 부분 수정 메커니즘은 작동한다
- Stage 4 manuscript shrink 문제도 과거 대비 실질적으로 개선됐다
- 그러나 시스템 전체 계약은 아직 하나의 의미로 닫히지 않았다

현재 상태를 한 문장으로 요약하면:

> `PASS_WITH_FIX`는 "부분 수정 기능"으로는 꽤 작동하지만, "시스템 전역에서 하나의 의미를 갖는 verdict"로는 아직 정합하지 않다.

## 9. 최종 확신도 95% 근거

95%로 판단한 이유:

- 관련 코드 경로를 Stage 2/3/4와 prompt/schema, logging, analytics까지 모두 확인했다
- 실산출물(`00_test_01~03`)에서 코드 추론과 같은 패턴을 직접 확인했다
- 관련 회귀 묶음 314개를 재실행해 현재 워크트리 기준 동작을 다시 검증했다

남은 5% 불확실성:

- live rerun을 이번 감사에서 직접 수행하지는 않았다
- 일부 과거 문서는 현재 코드 line number와 어긋나며, 운영팀이 실제로 어떤 sink를 SSOT로 쓰는지 조직적 합의는 코드만으로는 100% 확정할 수 없다

## 10. 즉시 운영 해석 가이드

현재 기준으로는 다음처럼 해석하는 것이 가장 안전하다.

- `director_selections` / `episode_production.jsonl`의 `PASS_WITH_FIX`
  - "초기 Director 판단"으로 해석
- `stage_attempts` / `pass_rate_monitor.json`
  - "patch/retry 이후 최종 결과"로 해석
- Stage 3의 `final_verdict=PASS_WITH_FIX`
  - "완전히 닫힌 최종 verdict"로 간주하지 말 것
- Stage 4의 `verdict=PASS` + 낮은 `director_score`
  - 재심사 score가 아닌 최초 score일 가능성을 의심할 것

이 문서는 코드 수정 없이 작성되었다.
