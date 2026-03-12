# Commit Stability 전량 패치 실행 계획

작성일: 2026-03-12  
인코딩: UTF-8  
기준 문서:
- `docs/2026-03-12/commit-stability-survey-final-audit.md`
- `docs/2026-03-12/commit-stability-survey-evidence-index.md`
- `docs/2026-03-12/accurate-cost-tracking-spec.md`

## 1. 목적

최신 커밋 전후 전수조사에서 남은 실질 findings를 코드로 닫는다.

이번 패치의 직접 목표는 아래 3축이다.

1. 비용 / 토큰 telemetry를 문서 수준이 아니라 구현 수준으로 완결
2. soft-failure log 경로를 실제 Path만 허용하도록 정리
3. non-standard/manual 경로에서도 빈 `attempt_key`가 남지 않도록 기본값 보강

## 2. 비대상

이번 패치에서 직접 하지 않는 것:

- canary `run/full` 실행
- live rerun 실행
- tracked runtime artifact 강제 정리
- CW 일반 글쓰기 본체 변경
- PASS_WITH_FIX 의미 재설계

주의:
- `projects/test_project/logs/episode_production.jsonl` 같은 tracked artifact drift는 코드 패치 대상이 아니라 작업트리 위생 이슈로 분리한다.

## 3. 패치 범위

### WP-1. Cost Telemetry Completion

대상 파일:
- `modules/domain/agents/base_agent.py`
- `modules/core/metrics_collector.py`
- 관련 테스트

수정 목표:
- `ask()` 시작 시 `_last_llm_usage`를 초기화해 stale usage 재사용을 차단
- continuation / fallback / backup이 있더라도 ask 단위 누적 usage를 합산
- 성공/실패 종료 메트릭에서 `cached_content_token_count`를 실제 비용 계산에 반영
- backup recovery 경로도 실측 usage 우선 사용으로 정렬
- `MetricsCollector.end_call()`이 `cached_tokens`와 관측용 `thinking_tokens`를 받을 수 있게 확장
- scope/session 집계가 새 필드를 깨뜨리지 않게 유지

수용 기준:
- usage가 없는 경우 기존 추정 fallback 유지
- usage가 여러 번 발생한 ask는 마지막 usage가 아니라 누적 usage 기준으로 집계
- usage가 있는 경우 `cached_tokens`가 비용 계산에 반영
- 이전 호출 usage가 다음 실패 호출 비용에 섞이지 않음
- backup recovery 경로도 실측 usage 우선, fallback 추정 보조로 정렬
- 기존 metrics snapshot / summary 포맷은 하위호환 유지

### WP-2. Soft-Failure Path Hygiene

대상 파일:
- `modules/core/soft_failure.py`
- `modules/core/stage4_post_processor.py`
- `modules/validation/validation_orchestrator.py`
- 관련 테스트

수정 목표:
- `log_dir`는 `str | Path | os.PathLike`만 허용
- truthy `MagicMock`나 임의 객체는 soft-failure log 경로로 승격하지 않음
- Stage 4 post-processor와 validation orchestrator의 project root 해석이 같은 기준을 사용

수용 기준:
- 정상 `tmp_path` / 실제 project root는 계속 동작
- mock root가 들어와도 `MagicMock/.../soft_failures.jsonl`가 생성되지 않음
- soft-failure audit_event relay는 기존처럼 유지

### WP-3. Attempt Key Default Hardening

대상 파일:
- `modules/core/pass_rate_monitor.py`
- 관련 테스트

수정 목표:
- `record_attempt()`에 `attempt_key`가 비어 들어오면 `stage/episode/arc/attempt_num` 기반 기본 key를 생성
- 표준 런타임에서 이미 전달하는 `attempt_key`는 그대로 우선 사용

수용 기준:
- non-standard/manual record도 빈 key가 남지 않음
- 기존 Stage 2/3/4 explicit attempt_key 경로는 동작 불변

## 4. 순차 체크리스트

### Phase A. 문서 고정
- [x] 본 문서를 SSOT로 사용
- [x] canary `run/full/live rerun` 금지 유지
- [x] patch 범위와 비대상 범위를 고정

### Phase B. WP-1 구현
- [x] `BaseAgent` stale usage reset
- [x] `BaseAgent` success/failure/backup metrics 경로 공통화
- [x] `MetricsCollector.end_call()` 확장
- [x] cost 관련 회귀 테스트 추가

### Phase C. WP-2 구현
- [x] shared path normalization 강화
- [x] Stage 4 / validation soft-failure 경로 적용
- [x] MagicMock root regression test 추가

### Phase D. WP-3 구현
- [x] `PassRateMonitor.record_attempt()` 기본 attempt_key 생성
- [x] 관련 테스트 기대값 갱신

### Phase E. 검증
- [x] `tests/test_cost_tracking.py`
- [x] `tests/test_base_agent.py`
- [x] `tests/test_stage4_post_processor.py`
- [x] `tests/test_validation_orchestrator_soft_failure.py`
- [x] `tests/test_v55_modules.py`
- [x] 필요 시 관련 회귀 묶음 추가 실행

## 5. 리스크와 방어선

### R1. cost telemetry 변경이 기존 통계 포맷을 깨뜨릴 수 있음
- 방어: 기존 필드는 유지하고 선택적 필드만 추가

### R2. path normalization 강화가 정상 log 기록까지 막을 수 있음
- 방어: `str`, `Path`, `os.PathLike`는 그대로 허용

### R3. 기본 attempt_key 생성이 기존 테스트/소비자 기대값과 충돌할 수 있음
- 방어: 명시적 attempt_key 우선 원칙 유지

## 6. 완료 조건

- `WP-1 ~ WP-3` 코드와 테스트가 모두 반영됨
- 관련 회귀 테스트 green
- canary는 실행하지 않고 execution-ready 상태에서 정지
- 결과는 별도 구현 요약으로 정리
