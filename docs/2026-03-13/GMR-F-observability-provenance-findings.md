# GMR-F Observability & Provenance Findings

> Date: 2026-03-13
> Commit: `d9825a69`
> Workspace State: dirty

## PASS 1 관찰

- backend는 `run_id` 중심 WS/HTTP 이벤트를 사용한다.
- engine는 `runtime_audit`, `session_logger`, `metrics_session_id`를 별도로 유지한다.
- Stage 4 완료 시에만 `stage4_complete` audit summary가 기록된다.

## PASS 2 교차 검증

- `bridge_server.py`는 `run_id`를 envelope와 WS event에 넣는다.
- `SessionLogger`는 `llm_io.jsonl`, `decisions.jsonl`, `state_changes.jsonl`를 category별로 쓴다.
- `MetricsCollector`는 독립 `session_id`와 metrics 파일을 쓴다.
- `AuditService`는 `runtime_audit.jsonl`과 `runtime_audit_summary.json`를 쓴다.

## PASS 3 최종 findings

### [GMR-F-001] observability plane마다 correlation key가 다르고 단일 provenance key가 없다

- Severity: `P1`
- Evidence:
  - `modules/api/bridge_server.py:141-173`, `1265-1363`
  - `modules/core/services/audit_service.py:37-101`
  - `modules/core/session_logger.py:1-165`
  - `modules/core/metrics_collector.py:58-190`
  - `main_a.py:1083-1086`
- Why macro risk:
  - desktop/backend는 `run_id`, metrics는 `session_id`, engine audit는 runtime list 기반이다.
  - 같은 실행을 UI -> backend -> engine -> DB artifact까지 하나의 key로 종단 추적하기 어렵다.

### [GMR-F-002] audit summary는 completion-biased이며 중단/예외 경로는 flush 위주로 닫힌다

- Severity: `P2`
- Evidence:
  - `modules/core/stage4_orchestrator.py:1591-1603`
  - `modules/core/stage4_orchestrator.py:1605-1620`
  - `tests/test_stage4_orchestrator.py:107-200`
- Why macro risk:
  - 정상 completion만 `stage4_complete` summary를 남기고, early return/interrupt/exception은 flush/commit cleanup까지만 보장한다.
  - 결과적으로 실패 실행의 provenance가 정상 실행보다 얕게 남는다.

## Last Verified
- Date: 2026-03-13
- Commit: `d9825a69`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
