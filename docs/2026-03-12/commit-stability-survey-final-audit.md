# 최신 커밋 안정성 전수조사 최종 감사

작성일: 2026-03-12
기준 문서: `docs/2026-03-12/commit-stability-survey-roadmap.md`
근거 문서: `docs/2026-03-12/commit-stability-survey-evidence-index.md`

## 1. 결론

현재 판정은 다음과 같다.

- `P0`: 없음
- `P1`: 2건
- `Observation / known residual`: 2건
- canary readiness: `P0 기준 blocked 아님`
- 단, `P1-1`, `P1-2`는 canary 전 명시적으로 수용하거나 후속 수정 계획을 확정하는 편이 안전하다

즉, 최신 커밋 이후 들어온 `PASS_WITH_FIX / Stage 3·4 semantics / logging reinforcement / structural inplace / canary automation`의 주 경로에서는 즉시 중단해야 할 `P0`는 보이지 않았다. 다만 비용 telemetry 완결성과 soft-failure/test path 위생 문제는 `P1`로 남아 있다.

## 2. Phase 진행 결과

### Phase 0. 기준선 고정
- 최신 커밋은 `b3cfa0e`
- `HEAD` 대비 dirty worktree는 tracked 31개 파일 변경 상태
- `git diff --stat HEAD` 기준 `+3035/-124`
- 이번 조사 동안 코드 수정과 canary run/full/live rerun은 수행하지 않음

### Phase 1. 변경 인벤토리
- 변경은 크게 6축으로 묶였다.
  - `PASS_WITH_FIX / Stage 3·4 semantics`
  - `Stage 4 structural inplace`
  - `logging / analytics / sink alignment`
  - `attempt_key / artifact linkage`
  - `canary automation`
  - `metrics / provider cost telemetry`

### Phase 2. 계약 / semantics 감사
- `Stage3Orchestrator`는 external success를 `PASS`, `PASS_WITH_WARNING`으로 제한한다.
- `Stage4InterviewRound`는 `PASS_WITH_FIX -> patch -> PASS` 후 final score를 `director_score`와 `_director_quality_labels`에 반영한다.
- 관련 회귀 테스트는 현재 dirty state에서도 통과했다.

판정:
- 이 축에서는 `P0` 없음

### Phase 3. logging / sink 정합성 감사
- `FailureAnalyzer.sink_alignment_summary()`는 final/lifecycle sink mismatch를 자동 감지한다.
- `attempt_key`, `candidate_key`, `content_hash`, `artifact_path`는 Stage 4 핵심 sink에 반영돼 있다.
- `stage4_canary_tools.py`의 hard gate는 `pass_rate_monitor_missing`, `sink_alignment_summary_empty`, mismatch 계열을 fail-close로 처리한다.

판정:
- standard runtime 기준으로는 `P0` 없음
- manual/non-standard context의 `metrics_session_id` 운영 규칙은 residual로 남음

### Phase 4. structural inplace / ChiefWriter 감사
- structural patch는 local issue에서만 시도되고, `global`은 fallback 사유로 빠진다.
- `patch_trace`는 strategy/targets/fallback_reason/focus/structural_attempted/unchanged_ratio를 전달한다.
- `CW generate_ensemble()` 중심 일반 글쓰기 본체를 직접 바꾸는 구조는 아님

판정:
- 설계 취지와 구현은 대체로 정합
- 이 축에서도 `P0` 없음

### Phase 5. canary 자동화 감사
- `from_ep != 1`은 코드와 문서 모두에서 차단돼 있다.
- `run_canary()`는 `pass_rate_monitor.save()`, audit flush, post-analyze를 포함한다.
- `00_test_06` analyze는 의도대로 `fail-closed`였다.

판정:
- automation 자체에서 즉시 중단해야 할 `P0` 없음

### Phase 6. 테스트 재검토
- 핵심 회귀군: `401 passed`
- 추가 비용/agent 회귀: `67 passed`
- 테스트 결과로는 dirty state 기준 명시적 failure 없음

판정:
- 숨은 `P0`는 테스트 수준에서 재현되지 않음

## 3. Findings

### P1-1. 비용/토큰 telemetry가 아직 완결되지 않았다

요약:
- provider는 `thoughts_token_count`, `cached_content_token_count`까지 추출하지만, 실제 종료 비용 계산은 그 정보를 끝까지 쓰지 않는다.
- 또 `_last_llm_usage`가 ask 시작 시 리셋되지 않아, 실패 호출이 직전 성공 호출의 usage를 재사용할 가능성이 남아 있다.

근거:
- `modules/domain/agents/base_agent.py:333-337`
- `modules/domain/agents/base_agent.py:463-475`
- `modules/domain/agents/base_agent.py:605-608`
- `modules/domain/agents/base_agent.py:682-689`
- `modules/core/metrics_collector.py:192-240`
- `modules/core/metrics_collector.py:270-287`
- `docs/2026-03-12/accurate-cost-tracking-spec.md`

해석:
- 이 문제는 story generation correctness를 직접 깨는 `P0`는 아니다.
- 하지만 `Google API vs Vertex API` 비용/운영 비교 근거를 만들려는 시점에서는 관측 왜곡이 생길 수 있다.

판정:
- `P1`

### P1-2. soft-failure / 테스트 로그 경로가 MagicMock류 입력에 오염될 수 있다

요약:
- soft-failure 기록 경로 해석이 너무 관대해서, truthy한 비-Path 객체가 들어오면 `Path(root)`로 변환을 시도한다.
- 현재 workspace에는 실제로 `MagicMock/mock.current_project.paths.root/.../soft_failures.jsonl`가 생성돼 있다.

근거:
- `modules/core/stage4_post_processor.py:54-69`
- `modules/core/soft_failure.py:27-33`
- `tests/test_stage01_helpers.py:26-27`
- 실제 산출물:
  - `MagicMock/mock.current_project.paths.root/2930521814512/logs/soft_failures.jsonl`

해석:
- 운영 runtime의 정상 프로젝트에서는 대개 진짜 `Path`가 들어오므로 치명적 `P0`는 아니다.
- 그러나 테스트 격리와 로컬 조사 정확도를 해치고, soft-failure 관련 증거를 오염시킨다.

판정:
- `P1`

### Observation-1. manual/non-standard context의 attempt key는 여전히 residual이 있다

요약:
- `resolve_logging_session_id()`는 non-string session source를 의도적으로 무시한다.
- standard runtime에선 괜찮지만, manual/non-standard 경로는 legacy key로 남을 수 있다.

근거:
- `modules/core/logging_keys.py:4-34`
- `tests/test_v55_modules.py:232-237`
- `docs/2026-03-12/logging-reinforcement-3pass-audit.md`

판정:
- `Observation`

### Observation-2. worktree에 tracked runtime artifact drift가 남아 있다

요약:
- `projects/test_project/logs/episode_production.jsonl`가 dirty 상태다.
- 현재 evidence로는 이번 최신 변경이 직접 만든 결함이라고 단정하기보다, 로컬 실행/테스트 잔재로 보는 편이 안전하다.

근거:
- `git status --short projects/test_project/logs/episode_production.jsonl MagicMock`
- `git diff -- projects/test_project/logs/episode_production.jsonl`

판정:
- `Observation`

## 4. canary readiness 판정

현재 판정:
- `P0 없음`이므로 `hard blocked`는 아님
- 다만 아래 2건은 canary 전에 의식적으로 처리 여부를 정해야 한다.
  - `P1-1` 비용 telemetry 불완전
  - `P1-2` soft-failure/test path 오염

실무적 해석:
- story correctness / PASS_WITH_FIX / sink alignment / canary automation만 보면 canary 전환은 가능하다
- 비용 비교나 작업트리 순도까지 같이 보려면 `P1-1`, `P1-2`를 먼저 닫는 편이 더 안전하다

## 5. 3-pass 감리

### Pass 1. 계약 / 코드 / 문서 대조
- 초기에 의심했던 `Stage 3 PASS_WITH_FIX external success`, `Stage 4 final score stale`, `canary hard gate looseness`는 현재 dirty worktree 기준으로는 닫혀 있었다.
- 따라서 이 축의 초기 우려는 최종 findings에서 제외했다.

### Pass 2. 테스트 / 로그 / 런타임 근거 대조
- `401 passed` + `67 passed`로 핵심 변경축 회귀는 녹색이었다.
- `00_test_06 analyze`는 문서대로 fail-closed였다.
- soft-failure path 오염은 실제 filesystem 증거가 있어 유지했다.
- cost telemetry 축은 테스트가 깨지지 않았지만, 구현 연결이 부분적이라는 코드 증거가 충분해 유지했다.

### Pass 3. 오탐 제거 / severity 재판정
- manual/non-standard `metrics_session_id` residual은 `P1`에서 `Observation`으로 낮췄다.
- tracked fixture log drift도 직접 결함으로 단정하지 않고 `Observation`으로 낮췄다.
- 최종 `P1`은 2건만 유지했다.

## 6. 최종 판정

- 최종 상태: `P0 없음 / P1 2건 / Observation 2건`
- 확신도: `95%`

95% 근거:
- 로드맵 Phase 0~8 순차 수행
- 코드 수정 없이 diff/코드/문서/로그/테스트만으로 검증
- 핵심 회귀군 `401 passed`, 추가 회귀 `67 passed`
- fail-closed canary analyze 확인
- 3-pass 감리 후 중복/과대평가 항목 제거 완료

남은 5%:
- 실제 canary run/full/live rerun은 아직 수행하지 않았음
- manual/non-standard runtime path는 여전히 운영 규칙 의존성이 남아 있음

## 7. 후속 권고

우선순위는 아래 순서가 적절하다.

1. `P1-2` 정리 또는 명시적 수용
- soft-failure/test path 오염 문제를 먼저 닫으면 조사/운영 로그 신뢰도가 올라간다.

2. `P1-1` 정리 또는 명시적 수용
- Vertex 전환 논의를 하려면 비용 telemetry 축은 가능한 한 먼저 닫는 편이 낫다.

3. 그다음 canary
- 이번 감사 범위에서는 canary를 실행하지 않았고, 여기서 멈춘다.
