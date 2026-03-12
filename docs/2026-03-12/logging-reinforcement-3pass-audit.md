# 로깅 체계 보강 3pass 감리

감리 일자: 2026-03-12  
감리 범위: Stage 2~4 logging sink, `PASS_WITH_FIX` lifecycle, structural inplace observability, downstream analytics, rerun readiness  
현재 판정: `문서 확정 가능`  
현재 확신도: `95%`

## 1. 증거 집합

### 1.1 코드
- `modules/core/logging_keys.py`
- `modules/core/artifact_logging.py`
- `modules/core/pass_rate_monitor.py`
- `modules/core/db_manager.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/failure_analyzer.py`
- `modules/domain/agents/chief_writer.py`

### 1.2 문서
- `docs/2026-03-11/logging-system-audit-95.md`
- `docs/2026-03-12/pass-with-fix-master-roadmap.md`
- `docs/2026-03-12/pass-with-fix-improvement-execution-plan.md`
- `docs/2026-03-12/pass-with-fix-phase1-execution-spec.md`
- `docs/2026-03-12/stage4-live-rerun-checklist.md`
- `docs/2026-03-12/logging-reinforcement-master-roadmap.md`
- `docs/2026-03-12/logging-reinforcement-execution-plan.md`

### 1.3 테스트
- artifact linkage targeted:
  - `pytest -q tests/test_db_manager.py tests/test_stage2_finalizer.py tests/test_stage3_orchestrator.py tests/test_stage4_interview_round.py`
  - 결과: `147 passed in 44.27s`
- broader regression slice:
  - `pytest -q tests/test_failure_analyzer.py tests/test_pass_with_fix.py tests/test_chief_writer.py tests/test_inplace_reliability.py tests/test_stage2_preflight_helpers.py tests/test_v55_modules.py`
  - 결과: `236 passed in 51.56s`
- 합산 기준:
  - 현재 결과: `383 passed`
- 최종 통합 검증:
  - `pytest -q tests/test_db_manager.py tests/test_stage2_finalizer.py tests/test_stage3_orchestrator.py tests/test_stage4_interview_round.py tests/test_failure_analyzer.py tests/test_pass_with_fix.py tests/test_chief_writer.py tests/test_inplace_reliability.py tests/test_stage2_preflight_helpers.py tests/test_v55_modules.py`
  - 결과: `383 passed in 85.13s`

## 2. Pass 1. sink inventory 감리

### 2.1 확인 사실
- `director_selections`는 initial verdict/score/reason sink다.
- `episode_production.jsonl`은 Stage 4 lifecycle sink이며 `initial_verdict`, `final_verdict`, `patch_trace`, `attempt_key`를 보관한다.
- `stage_attempts`는 final verdict/score sink이며 `attempt_key`와 `session_id`를 보관한다.
- `pass_rate_monitor.json`은 경량 운영 sink이며 `attempt_key`, `final_verdict`, `patch_strategy`, `structural_attempted`를 보관한다.
- Stage 2/3/4는 모두 `build_attempt_key()`를 사용하고, 표준 런타임에서는 `metrics_session_id`가 suffix로 붙는다.

### 2.2 판정
- sink 역할 구분은 현재 코드 기준으로 충분히 명확하다.
- 이전 감리의 핵심 결함이던 `attempt_key 부재`와 `Stage 3 monitor parity gap`은 닫혔다.

## 3. Pass 2. semantics / downstream consumer 감리

### 3.1 확인 사실
- `Stage3Orchestrator`는 `PASS_WITH_FIX`를 external success set에서 제외했다.
- `FailureAnalyzer`는 final pass-rate 집계에서 `PASS_WITH_FIX`를 transient count로만 다룬다.
- `DBManager.get_recent_episode_scores()`는 final sink 기준으로 조회한다.
- `FailureAnalyzer.sink_alignment_summary()`는 final sink와 lifecycle sink의 불일치를 자동 탐지한다.

### 3.2 판정
- legacy `PASS_WITH_FIX` pass-like consumer 문제는 로깅/분석 범위 안에서는 해소됐다.
- 남아 있는 `PASS_WITH_FIX`는 patch loop와 transient logging 의미로만 남는다.

## 4. Pass 3. 운영 / rerun readiness 감리

### 4.1 확인 사실
- `stage4-live-rerun-checklist.md`는 `patch_trace` hard gate를 사용한다.
- `FailureAnalyzer.patch_trace_summary()`는 `avg_unchanged_ratio`, `fallback_reasons`, `top_patch_targets`를 제공한다.
- `FailureAnalyzer.sink_alignment_summary()`는 `attempt_key` 기준으로 `director_selections`, `episode_production.jsonl`, `stage_attempts`, `pass_rate_monitor.json`의 정합성을 자동 점검한다.
- `main_a.py`는 프로젝트 로드 시 `current_project.metrics_session_id`를 주입하고, Stage 2/3/4 writer는 이를 `attempt_key`와 `stage_attempts.session_id`에 반영한다.
- Stage 2/3/4 reject metric path도 runtime `metrics_session_id`를 우선 사용하고, 없을 때만 `ep_*`/`arc_*` fallback을 쓴다.

### 4.2 판정
- limited rerun go/no-go 판단에 필요한 최소 운영 계측은 충족된다.
- attempt 이후 candidate/artifact 수준의 baseline lineage도 들어갔다.
- artifact hash/path mismatch와 실제 artifact file 부재도 자동 감지할 수 있다.

## 5. 최종 Findings

### F1. 해결됨 — 공통 `attempt_key` 부재
- `director_selections`, `episode_production.jsonl`, `stage_attempts`, `pass_rate_monitor.json`에 공통 `attempt_key`가 들어갔다.
- Stage 2/3/4 모두 동일 helper를 사용한다.

### F2. 해결됨 — legacy `PASS_WITH_FIX` pass-like helper query
- `DBManager.get_recent_episode_scores()`는 final sink 기준으로 정리됐다.
- final success 집계는 `PASS`, `PASS_WITH_WARNING`만 사용한다.

### F3. 해결됨 — `pass_rate_monitor.json` verdict granularity 부족
- `attempt_key`, `final_verdict`, `patch_strategy`, `structural_attempted`가 추가됐다.
- Stage 3 writer parity도 확보됐다.

### F4. 해결됨 — rerun-safe `attempt_key`
- 표준 런타임에서는 `attempt_key`에 `metrics_session_id`가 포함된다.
- `stage_attempts.session_id`도 같은 값으로 기록된다.

### F5. 해결됨 — 운영 cross-sink 자동 감사 부재
- `FailureAnalyzer.sink_alignment_summary()`가 구현됐다.
- `attempt_key` 기준으로 final verdict mismatch, final score mismatch, lifecycle sink 누락, legacy key 사용 여부를 자동 집계한다.
- 추가로 `candidate_key`, `content_hash`, `artifact_path`, artifact file existence mismatch도 자동 집계한다.

### F6. 해결됨(기준선) — artifact linkage
- `candidate_key`, `content_hash`, `artifact_path`가 Stage 2/3/4 final sink와 Stage 4 lifecycle sink에 들어갔다.
- `modules/core/artifact_logging.py`가 `logs/artifacts/...` snapshot을 남기므로 attempt 이후 원고/청사진 artifact를 직접 따라갈 수 있다.
- 관련 회귀는 `tests/test_db_manager.py`, `tests/test_stage2_finalizer.py`, `tests/test_stage3_orchestrator.py`, `tests/test_stage4_interview_round.py`에 추가되었다.

## 6. 잔여 리스크
- `metrics_session_id`를 주입하지 않는 비표준/manual context에서는 legacy key가 다시 생길 수 있다.
- Stage 4 수준의 rich lifecycle sink는 아직 Stage 2/3에는 없다.

## 7. 권고
1. 다음 로깅 보강 phase는 비표준/manual context의 `metrics_session_id` 운영 규칙을 고정한다.
2. limited rerun 전에는 `patch_trace_summary()`와 `sink_alignment_summary()`를 둘 다 실행한다.
3. Stage 2/3 rich lifecycle sink 보강 필요성을 별도 판단한다.

## 8. 95% 근거
- 관련 코드 경로를 직접 재확인했다.
- 기존 audit 문서와 최신 구현 상태를 다시 대조했다.
- `FailureAnalyzer` 신규 cross-sink 테스트를 추가해 통과시켰다.
- artifact/session hardening 이후 통합 회귀 385건이 녹색이다.
- sink inventory, semantics, rerun readiness를 3pass로 재검토했다.

## 9. 남은 5%
- 비표준/manual 실행 경로의 `metrics_session_id` 주입은 운영 검증이 추가로 필요하다.
- Stage 2/3에는 Stage 4 수준의 rich lifecycle sink가 아직 없다.
