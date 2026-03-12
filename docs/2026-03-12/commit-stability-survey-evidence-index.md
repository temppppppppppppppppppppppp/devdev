# 최신 커밋 안정성 전수조사 Evidence Index

작성일: 2026-03-12
조사 기준 문서: `docs/2026-03-12/commit-stability-survey-roadmap.md`
조사 원칙: `코드 수정 금지`, `canary run/full/live rerun 금지`, `문서/테스트/읽기만 허용`

## 1. 기준선 캡처

### Git 기준선
- 최신 커밋: `b3cfa0e`
- 최근 5개 로그 확인:
  - `git log --oneline --decorate -n 5`

### Dirty worktree
- `git status --short`
- 현재 tracked 변경: 31개
- 대표 변경군:
  - `modules/core/stage4_interview_round.py`
  - `modules/domain/agents/chief_writer.py`
  - `modules/core/failure_analyzer.py`
  - `modules/core/db_manager.py`
  - `modules/core/pass_rate_monitor.py`
  - `modules/core/metrics_collector.py`
  - `modules/core/providers/gemini_provider.py`
  - `modules/core/providers/vertex_provider.py`
  - `scripts/run_stage4_canary.py`
  - 관련 테스트와 문서군

### Diff 규모
- `git diff --stat HEAD`
- 결과: `31 files changed, 3035 insertions(+), 124 deletions(-)`

## 2. semantics / PASS_WITH_FIX 근거

### Stage 3 external success set
- `modules/core/stage3_orchestrator.py:760-768`
- 근거:
  - external success는 `PASS`, `PASS_WITH_WARNING`만 허용
  - `PASS_WITH_FIX`는 Stage 3 외부 success set에서 제외됨

### Stage 4 final score / label 정합성
- `modules/core/stage4_interview_round.py:2587-2604`
- 근거:
  - `director_result["score"]`를 `final_score`로 재해석
  - `director_score`와 `_director_quality_labels["score"]`가 final score로 저장됨

### 관련 테스트
- `tests/test_stage3_orchestrator.py`
- `tests/test_pass_with_fix.py`
- `tests/test_stage4_interview_round.py:1387-1393`

## 3. logging / sink 정합성 근거

### cross-sink 감사 로직
- `modules/core/failure_analyzer.py:323-524`
- 근거:
  - `final_sink_missing`
  - `lifecycle_sink_missing`
  - `final_verdict_mismatches`
  - `final_score_mismatches`
  - `candidate_key/content_hash/artifact_path` mismatch
  - `artifact_missing_files`
  - `legacy_key_attempts`
  를 자동 집계

### Stage 4 canary hard gate
- `modules/core/stage4_canary_tools.py:257-322`
- 근거:
  - `pass_rate_monitor_missing`는 error
  - `sink_alignment_summary_empty`는 error
  - `final/lifecycle mismatch`는 error
  - `legacy_key_attempts > 0`는 error
  - `patch_trace_not_exercised`만 warning

### manual/non-standard session residual
- `modules/core/logging_keys.py:4-34`
- `tests/test_v55_modules.py:232-237`
- 근거:
  - non-string `metrics_session_id`는 무시
  - 기본 monitor record는 빈 `attempt_key`도 허용

## 4. structural inplace 근거

### local/global 라우팅
- `modules/domain/agents/chief_writer.py:949-972`
- `modules/domain/agents/chief_writer.py:1066-1160`
- `modules/domain/agents/chief_writer.py:1174-1312`
- `modules/domain/agents/chief_writer.py:1314-1350`
- 근거:
  - local hint 분류
  - `global`이면 structural patch 포기
  - scene/block 단위 patch plan 구성
  - 실패 시 fallback reason 기록

### patch trace 전달
- `modules/core/stage4_interview_round.py:2331-2356`
- `modules/core/stage4_interview_round.py:2378-2386`
- `modules/core/stage4_interview_round.py:2641-2675`
- `modules/core/stage4_interview_round.py:3976-3982`
- 근거:
  - `_last_inplace_patch_trace` 수집
  - `unchanged_ratio` 계산
  - `episode_production.jsonl`에 `patch_trace` 기록
  - pass_rate_monitor에 structural lineage 전달

## 5. 비용/토큰 추적 근거

### provider usage 필드 확장
- `modules/core/providers/gemini_provider.py`
- `modules/core/providers/vertex_provider.py`
- 근거:
  - `thoughts_token_count`
  - `cached_content_token_count`
  추출 추가

### BaseAgent usage 사용 방식
- `modules/domain/agents/base_agent.py:333-337`
- `modules/domain/agents/base_agent.py:605-608`
- `modules/domain/agents/base_agent.py:682-689`
- `modules/domain/agents/base_agent.py:463-475`
- 근거:
  - `_last_llm_usage`는 저장됨
  - ask 시작 시 리셋되지 않음
  - 성공/실패 cost 종료에 `prompt_token_count`, `candidates_token_count`만 사용

### MetricsCollector 종료 경로
- `modules/core/metrics_collector.py:192-240`
- `modules/core/metrics_collector.py:270-287`
- 근거:
  - `calculate_cost()`는 `cached_tokens`를 지원
  - 그러나 `end_call()`은 `cached_tokens` 인자를 받지 않고 `calculate_cost(model, input_tokens, output_tokens)`만 호출

### 관련 명세
- `docs/2026-03-12/accurate-cost-tracking-spec.md`
- 근거:
  - exact cost tracking이 아직 완결되지 않았다는 자체 명세 존재

## 6. 작업트리 오염 / 테스트 위생 근거

### 실제 오염 흔적
- `git status --short projects/test_project/logs/episode_production.jsonl MagicMock`
- 결과:
  - `M projects/test_project/logs/episode_production.jsonl`
  - `?? MagicMock/`

### tracked runtime artifact drift
- `git diff -- projects/test_project/logs/episode_production.jsonl`
- 근거:
  - tracked fixture log에 `TF49b_PREFLIGHT` row가 추가되어 있음

### MagicMock 경로 산출물
- 실제 존재 경로:
  - `MagicMock/mock.current_project.paths.root/2930521814512/logs/soft_failures.jsonl`
- 내용:
  - `stage4_post_processor.save_world_state_atomic` soft failure row 존재

### soft failure log dir 정규화
- `modules/core/stage4_post_processor.py:54-69`
- `modules/core/soft_failure.py:27-33`
- 근거:
  - truthy `root`에 대해 `Path(root) / "logs"` 시도
  - `_normalize_log_dir()`가 임의 객체를 `Path(log_dir)`로 허용

### MagicMock root를 주는 테스트 예
- `tests/test_stage01_helpers.py:26-27`
- 근거:
  - `app.current_project.paths.root = MagicMock()`

## 7. canary analyze 근거

### 준비된 canary 프로젝트
- `projects/00_test_06/logs/canary_prep.json`
- 근거:
  - source: `00_test_02`
  - `from_ep=1`
  - Stage 4 outputs reset

### analyze 결과
- 명령:
  - `python scripts/run_stage4_canary.py analyze --project 00_test_06 --target-ep 4`
- 결과:
  - `hard_gates.status == fail`
  - errors:
    - `draft_count_mismatch:0!=4`
    - `pass_rate_monitor_missing`
    - `sink_alignment_summary_empty`
  - warnings:
    - `runtime_audit_summary_missing`
    - `patch_trace_not_exercised`

## 8. 테스트 실행 근거

### 핵심 회귀군
- 명령:
```powershell
pytest -q tests/test_pass_with_fix.py tests/test_stage4_interview_round.py tests/test_stage3_orchestrator.py tests/test_failure_analyzer.py tests/test_chief_writer.py tests/test_inplace_reliability.py tests/test_stage4_canary_tools.py tests/test_run_stage4_canary.py tests/test_db_manager.py tests/test_stage2_finalizer.py tests/test_stage2_preflight_helpers.py tests/test_v55_modules.py tests/test_llm_router.py
```
- 결과:
  - `401 passed in 105.39s`

### 추가 비용/agent 회귀
- 명령:
```powershell
pytest -q tests/test_cost_tracking.py
pytest -q tests/test_base_agent.py
```
- 결과:
  - `5 passed in 1.89s`
  - `62 passed in 1.96s`

## 9. 최종 findings에 직접 연결되는 증거 요약

### F1. 비용/토큰 telemetry 불완전
- `modules/domain/agents/base_agent.py:333-337`
- `modules/domain/agents/base_agent.py:463-475`
- `modules/domain/agents/base_agent.py:605-608`
- `modules/domain/agents/base_agent.py:682-689`
- `modules/core/metrics_collector.py:192-240`
- `modules/core/metrics_collector.py:270-287`
- `docs/2026-03-12/accurate-cost-tracking-spec.md`

### F2. soft-failure / 테스트 경로 오염
- `modules/core/stage4_post_processor.py:54-69`
- `modules/core/soft_failure.py:27-33`
- `tests/test_stage01_helpers.py:26-27`
- `MagicMock/mock.current_project.paths.root/2930521814512/logs/soft_failures.jsonl`

### F3. manual/non-standard metrics session residual
- `modules/core/logging_keys.py:4-34`
- `tests/test_v55_modules.py:232-237`
- `docs/2026-03-12/logging-reinforcement-3pass-audit.md`
