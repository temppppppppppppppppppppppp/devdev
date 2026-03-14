# [BGA-T5] Observability / Artifact / Bridge Regression Findings

> 작성일: 2026-03-13
> 상태: `PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / artifact-proof cross-check / UTF-8 only`
> 기준 오더: `backend-global-full-survey-master-audit-order.md`
> 실행 요약: `PASS1 후보 6건 -> PASS2 제거 2건 -> PASS3 확정 4건`

---

## 조사 범위

- `modules/core/session_logger.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/services/audit_service.py`
- `modules/core/failure_analyzer.py`
- `modules/core/stage4_canary_tools.py`
- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `scripts/run_stage4_canary.py`

## 필수 근거

- 읽은 테스트:
  - `tests/test_session_logger.py`
  - `tests/test_artifact_logging.py`
  - `tests/test_failure_analyzer.py`
  - `tests/test_audit_service.py`
  - `tests/test_bridge_quality_summary.py`
  - `tests/test_stage4_canary_tools.py`
  - `tests/test_run_stage4_canary.py`
  - `tests/test_bridge_server_http_contract.py`
  - `tests/test_process_runner.py`
  - `tests/test_process_runner_stage0_inputs.py`
  - `tests/test_bridge_server_desktop_risk_gate.py`
  - `tests/test_stage4_orchestrator.py`
- 읽은 참조 문서:
  - `docs/2026-03-13/runtime-observability-provenance-artifact-detail-consolidated-findings.md`
  - `docs/2026-03-13/runtime-observability-provenance-artifact-detail-consolidated-findings-3pass-reaudit.md`
  - `docs/2026-03-13/stage4-9ep-log-full-survey-3pass-final-audit.md`
  - `docs/2026-03-13/logging-hardening-moderate-remediation-3pass-audit.md`
  - `docs/2026-03-13/ui-frontend-backend-connectivity-remediation-3pass-audit.md`
  - `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md`
- 실행 검증:
  - `pytest -q tests/test_session_logger.py tests/test_artifact_logging.py tests/test_failure_analyzer.py tests/test_audit_service.py tests/test_bridge_quality_summary.py tests/test_stage4_canary_tools.py tests/test_run_stage4_canary.py tests/test_bridge_server_http_contract.py tests/test_process_runner.py tests/test_process_runner_stage0_inputs.py tests/test_bridge_server_desktop_risk_gate.py`
  - 결과: `94 passed in 3.91s`
  - `pytest -q tests/test_stage4_orchestrator.py -k "stage4_completion_writes_runtime_audit_summary or stage4_early_return_does_not_write_runtime_audit_summary or stage4_failed_exhaustion_does_not_write_runtime_audit_summary or stage4_exception_does_not_write_runtime_audit_summary_and_flushes"`
  - 결과: `4 passed, 52 deselected in 1.40s`
- 정적 교차 검증:
  - `session_logger.log_decision()` payload shape와 Stage 3 / Stage 4 caller의 attempt metadata 계산 순서 비교
  - `AuditService.write_audit_summary()` schema와 `stage4_canary_tools` hard gate 조건 비교
  - `bridge_server._build_quality_dashboard_payload()` 노출 필드와 desktop renderer quality_dashboard merge contract 비교
  - `prepare_stage4_canary_project()` / `build_stage4_canary_summary()` 범위와 Stage 3 retained artifact 범위 비교

## PASS 기록

- PASS 1:
  - 후보 1: `session/decisions.jsonl`가 현재도 attempt-level join ledger 역할을 못 하는가
  - 후보 2: `runtime_audit_summary.json`가 structured sink digest가 아니라 heartbeat artifact에 머무는가
  - 후보 3: desktop / bridge quality dashboard가 proof-chain 상태를 operator에게 노출하지 않는가
  - 후보 4: automated runtime proof가 Stage 4 중심으로만 닫혀 Stage 3 observability regression을 비워 두는가
  - 후보 5: `soft_failures.jsonl` relay가 아직도 부분 surface에서 끊겨 있는가
  - 후보 6: `ProcessRunner` 종료 diagnostics가 너무 얇아 bridge operator surface에 의미 있는 실패 문맥을 남기지 못하는가
- PASS 2:
  - 후보 5 제거: `SessionLogger`, `artifact_logging`, `FailureAnalyzer`는 모두 `report_soft_failure()`를 실제 호출하고, `tests/test_session_logger.py`, `tests/test_artifact_logging.py`, `tests/test_failure_analyzer.py`가 해당 파일 생성까지 잠근다.
  - 후보 6 제거: `ProcessRunner.get_runtime_diagnostics()`는 `key`, `sub_key`, `mode`, `duration_ms`, `last_prompt_step`, `stdout_tail`, `stderr_tail`, `failure_phase`를 보존한다. `tests/test_process_runner.py:274-337`, `tests/test_bridge_server_http_contract.py:51-110`도 이 contract를 green으로 잠근다.
- PASS 3:
  - 확정 4건만 `BGA-T5-*`로 채택

## Finding Ledger

| ID | Severity | 상태 | 파일/함수 | 요약 |
|----|----------|------|-----------|------|
| `BGA-T5-001` | `P1` | confirmed | `session_logger.py`, `stage3_orchestrator.py`, `stage4_interview_round.py` | `session/decisions.jsonl`가 여전히 stage-agnostic attempt join ledger 역할을 하지 못한다 |
| `BGA-T5-002` | `P2` | confirmed | `services/audit_service.py`, `stage4_orchestrator.py`, `stage4_canary_tools.py` | `runtime_audit_summary.json`가 structured sink digest가 아니라 completion heartbeat에 머문다 |
| `BGA-T5-003` | `P2` | confirmed | `bridge_server.py`, `frontend-desktop-bridge` surface | desktop operator가 quality dashboard에서 proof-chain 상태를 볼 수 없다 |
| `BGA-T5-004` | `P2` | confirmed | `stage4_canary_tools.py`, `run_stage4_canary.py` | automated runtime proof가 Stage 4 중심으로만 닫혀 Stage 3 observability regression을 자동 검출하지 못한다 |

## Final Findings

### [BGA-T5-001] P1 - `session/decisions.jsonl`가 여전히 stage-agnostic attempt join ledger 역할을 하지 못한다

1. ID
   - `BGA-T5-001`
2. Severity
   - `P1`
3. 현상 요약
   - `SessionLogger.log_decision()`은 caller가 넘긴 필드만 `decisions.jsonl`에 그대로 적는다.
   - 그런데 Stage 3 success / reject path는 `attempt_key`, `candidate_key`, `artifact_path`를 계산하기 전에 먼저 `log_decision()`을 호출한다.
   - Stage 4는 `attempt_key`는 싣지만 `candidate_key`, `content_hash`, `artifact_path`는 이후 `episode_production.jsonl` / DB sink를 쓸 때에야 계산한다.
   - 결과적으로 `session/decisions.jsonl`만 보면 Stage 3은 attempt join key 자체가 없고, Stage 4도 artifact lineage를 복원할 수 없다.
4. 코드 근거
   - `modules/core/session_logger.py:111-138`의 `log_decision()`은 공통 필드와 임의 `meta`만 기록하며 join field를 강제하지 않는다.
   - `modules/core/stage3_orchestrator.py:1308-1320` success path와 `modules/core/stage3_orchestrator.py:1814-1824` reject path는 `log_decision()`을 먼저 호출한다.
   - 같은 함수의 이후 구간인 `modules/core/stage3_orchestrator.py:1324-1351`, `modules/core/stage3_orchestrator.py:1828-1864`에서야 `attempt_key`, `candidate_key`, `artifact_path`가 만들어진다.
   - `modules/core/stage4_interview_round.py:1828-1846`는 Stage 4 decision row에 `attempt_key`만 남긴다.
   - Stage 4 artifact lineage는 `modules/core/stage4_interview_round.py:4476-4487`의 `episode_production.jsonl` entry에서야 `candidate_key`, `content_hash`, `artifact_path`, `selection_artifact_path`까지 채워진다.
5. downstream 영향 경계
   - `session/decisions.jsonl` 단독 포렌식
   - Stage 3 / Stage 4 attempt lineage 수동 재구성
   - operator가 JSONL만 보고 candidate/artifact provenance를 판단하는 지원 절차
   - Stage 3 observability regression의 early warning surface
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_session_logger.py:57-74`, `tests/test_session_logger.py:228-236`은 decision row 생성과 임의 meta 저장만 검증한다.
   - `tests/test_failure_analyzer.py:214-348`은 `stage_attempts`, `director_selections`, `pass_rate_monitor`, `episode_production` alignment를 보지만 `decisions.jsonl`은 proof chain에 포함하지 않는다.
   - 현재 회귀망에는 `decisions.jsonl`만으로 attempt / candidate / artifact join이 가능한지 검증하는 테스트가 없다.
7. 기존 문서와의 중복 여부
   - `cross-track-confirmed-and-widened`
   - `ROP-T1-001`의 Stage 3 joinability gap을 유지하되, 이번 전역 조사에서는 Stage 4 session sink도 artifact lineage SSOT가 아님을 함께 묶었다.
8. 권장 후속 조치
   - Stage 3은 `attempt_key`, `candidate_key`, `artifact_path`를 계산한 뒤 `log_decision()`을 호출하도록 순서를 맞춰야 한다.
   - Stage 4도 `decisions.jsonl` row에 `candidate_key`, `content_hash`, `artifact_path`를 추가해야 한다.
   - 회귀 테스트를 추가해야 한다: `decisions.jsonl` 한 줄만으로 같은 attempt의 DB / artifact sink를 join할 수 있는지 검증.

### [BGA-T5-002] P2 - `runtime_audit_summary.json`가 structured sink digest가 아니라 completion heartbeat에 머문다

1. ID
   - `BGA-T5-002`
2. Severity
   - `P2`
3. 현상 요약
   - `AuditService.write_audit_summary()`는 audit buffer flush 뒤 `tag`, `total_events`, `counts`, `latest_event_type`, `recent_events`만 요약한다.
   - 이 파일은 Stage 4 정상 종료 시점에 `stage4_complete` tag로 닫히지만, `stage_attempts`, `director_selections`, `episode_production`, `pass_rate_monitor`, artifact lineage 상태는 전혀 포함하지 않는다.
   - 따라서 `runtime_audit_summary.json`은 "완료 heartbeat"로는 쓸 수 있어도, operator가 structured sink가 같은 사실을 보존했는지 확인하는 proof artifact는 아니다.
4. 코드 근거
   - `modules/core/services/audit_service.py:72-102`는 summary schema를 `tag`, `timestamp`, `total_events`, `counts`, `latest_event_type`, `recent_events`로 고정한다.
   - `modules/core/stage4_orchestrator.py:1594-1603`은 정상 종료 시 `ctx.audit_event("stage4_complete", ...)` 뒤 `ctx.write_audit_summary("stage4_complete")`만 호출한다.
   - `modules/core/stage4_canary_tools.py:137-154`는 runtime summary를 읽지만, hard gate에서 보는 값은 사실상 `tag`와 `total_events`다.
   - `modules/core/stage4_canary_tools.py:347-357`은 `runtime_tag == "stage4_complete"`와 `runtime_total_events > 0`만 확인한다.
5. downstream 영향 경계
   - operator가 보는 `runtime_audit_summary.json`
   - Stage 4 런 종료 판정
   - postmortem에서 completion artifact를 structured sink proof로 오독할 위험
   - canary / audit 문서의 "정상 종료" 1차 근거
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_audit_service.py:87-97`은 summary 파일 존재, `tag`, `total_events`, `counts`만 검증한다.
   - `tests/test_stage4_orchestrator.py:123-148`은 Stage 4 완료 시 `write_audit_summary("stage4_complete")` 호출만 검증한다.
   - `tests/test_stage4_canary_tools.py:134-147`은 `{"tag":"stage4_complete","total_events":1}` 수준의 최소 summary도 유효 입력으로 받아 hard gate 계산을 계속 진행함을 보여준다.
   - 현재 회귀망에는 runtime summary와 structured sinks를 한 파일 안에서 재구성 가능하게 만드는 테스트가 없다.
7. 기존 문서와의 중복 여부
   - `cross-track-confirmed`
   - `ROP-T3-003`, `ROP-T5-001`의 heartbeat / proof gap을 현행 Stage 4 completion path와 canary gate 기준으로 재확인했다.
8. 권장 후속 조치
   - `runtime_audit_summary.json`에 최소한 `sink_alignment_summary digest`, `latest attempt_key`, `artifact coverage`, `pass_rate_monitor present` 같은 structured fields를 넣어야 한다.
   - 아니면 이 파일을 명시적으로 heartbeat artifact로만 규정하고, operator용 proof summary를 별도 파일로 분리해야 한다.
   - 회귀 테스트를 추가해야 한다: summary 하나만 읽어도 최소 proof-chain 상태를 재구성할 수 있는지 검증.

### [BGA-T5-003] P2 - desktop operator가 quality dashboard에서 proof-chain 상태를 볼 수 없다

1. ID
   - `BGA-T5-003`
2. Severity
   - `P2`
3. 현상 요약
   - desktop renderer는 `quality_dashboard` 응답을 operator 메인 surface로 merge해 사용한다.
   - 그런데 backend dashboard payload는 `runtime_health`를 `soft_failures.jsonl` 최근 행으로만 보여 주고, `runtime_audit_summary`, `sink_alignment_summary`, canary hard gate 결과는 아예 포함하지 않는다.
   - 그래서 UI는 `quality_summary`, `artifact_ladder`, `safe_ops`, `runtime_health`가 모두 보이는 상태여도, 실제 evidence chain이 join 가능한지 여부는 operator가 알 수 없다.
4. 코드 근거
   - `modules/api/bridge_server.py:189-260`의 `_quality_dashboard_defaults()`에는 `safe_ops`, `artifact_ladder`, `quality_summary`, `result_summary`, `failure_patterns`, `runtime_health`, `retrieval_summary`, `calibration`만 있다.
   - `modules/api/bridge_server.py:1107-1178`은 `runtime_health`를 `soft_failures.jsonl`로 만들고, 같은 payload에 `artifact_ladder`, `safe_ops`, `quality_summary`를 넣지만 `FailureAnalyzer.sink_alignment_summary()`나 `runtime_audit_summary.json`은 읽지 않는다.
   - `docs/2026-03-12/frontend-desktop-bridge-full-survey-3pass-final-audit.md:113-120`은 renderer가 `quality_dashboard` 응답을 그대로 merge해 쓴다고 정리한다.
5. downstream 영향 경계
   - desktop quality dashboard
   - operator의 live triage / support flow
   - proof-chain 문제를 UI healthy state로 오독하는 위험
   - bridge/API contract가 frontend에게 전달하는 runtime evidence 범위
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_bridge_quality_summary.py:205-237`은 `runtime_health`, `artifact_ladder`, `safe_ops`, `calibration`이 채워진 green payload를 검증한다.
   - 그러나 같은 테스트와 `tests/test_bridge_server_http_contract.py:51-110` 어디에도 `runtime_audit_summary`, `sink_alignment_summary`, canary hard gate 노출을 요구하는 assertion은 없다.
   - 현재 API contract 회귀망은 operator proof-chain state를 dashboard 응답에 포함하도록 강제하지 않는다.
7. 기존 문서와의 중복 여부
   - `cross-track-related-but-new`
   - frontend/bridge 문서들은 quality dashboard merge surface를 정리했지만, 이번 finding은 그 surface가 backend evidence proof 상태를 싣지 않는다는 점을 T5 operator 관점에서 새로 묶는다.
8. 권장 후속 조치
   - `/quality/dashboard`에 `runtime_audit_summary digest`, `sink_alignment_summary status`, `proof_status` 같은 필드를 추가해야 한다.
   - renderer는 quality score와 evidence proof 상태를 분리 렌더링해야 한다.
   - 회귀 테스트를 추가해야 한다: sink mismatch가 있을 때 dashboard payload가 `proof_status=warn/fail`을 내보내는지 검증.

### [BGA-T5-004] P2 - automated runtime proof가 Stage 4 중심으로만 닫혀 Stage 3 observability regression을 자동 검출하지 못한다

1. ID
   - `BGA-T5-004`
2. Severity
   - `P2`
3. 현상 요약
   - 현재 canary tooling은 이름 그대로 Stage 4 output reset / rerun / analyze에 집중한다.
   - canary prep는 Stage 4 산출물만 지우고 Stage 3 blueprints와 Stage 3 DB row는 그대로 남겨 둔다.
   - summary 단계도 `sink_alignment_summary(stage=4)`, `stage4_attempts`, `director_stage4_rows`, Stage 4 rationale contract만 본다.
   - 따라서 Stage 3 observability regression은 automated runtime proof 바깥에 남는다.
4. 코드 근거
   - `modules/core/stage4_canary_tools.py:47-54`, `modules/core/stage4_canary_tools.py:80-100`은 canary prep가 "Stage 4 outputs만 reset"한다고 명시한다.
   - `modules/core/stage4_canary_tools.py:112-123`, `modules/core/stage4_canary_tools.py:146-173`은 summary 대상도 Stage 4 DB / sink로 고정한다.
   - `scripts/run_stage4_canary.py:24-29` 경로는 `_stage_4_v2_chief_writer()` 실행 후 바로 Stage 4 canary summary를 분석한다.
5. downstream 영향 경계
   - automated runtime proof matrix
   - Stage 3 observability regression detection
   - canary green을 backend-wide proof closure로 오독하는 위험
   - 단계 간 observability continuity 검증
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage4_canary_tools.py:45-80`은 prep 후 `stage4_count == 0`, `stage3_count == 1`을 기대한다. 즉 Stage 3은 의도적으로 보존된다.
   - `tests/test_stage4_canary_tools.py:139-149`는 summary 결과가 `stage4_attempts`, Stage 4 rationale, Stage 4 hard gate를 기준으로 계산됨을 보여 준다.
   - `tests/test_run_stage4_canary.py:7-30`도 `_stage_4_v2_chief_writer(..., target_ep=4)` 호출과 Stage 4 analyze 경로만 잠근다.
   - 현재 회귀망에는 Stage 3 `decisions.jsonl` / Stage 3 attempt lineage를 자동 proof로 닫는 canary가 없다.
7. 기존 문서와의 중복 여부
   - `cross-track-confirmed-and-expanded`
   - `ROP-T5-001`의 canary proof gap을 유지하되, 이번 전역 조사에서는 그 공백이 Stage 3 observability retained defect를 그대로 비워 둔다는 점까지 범위를 넓혔다.
8. 권장 후속 조치
   - Stage 4 canary와 별도로 Stage 3 observability canary를 추가하거나, 현 canary summary를 multi-stage proof matrix로 확장해야 한다.
   - 최소한 Stage 3 `decisions.jsonl`, `stage_attempts(stage=3)`, blueprint artifact snapshot을 같은 gate에서 함께 비교해야 한다.
   - 회귀 테스트를 추가해야 한다: Stage 3 join-key regression이 생기면 canary hard gate가 바로 실패하는지 검증.

## Rejected Candidates

| 후보 | PASS2 판정 | 근거 |
|------|------------|------|
| `soft_failures.jsonl` relay가 아직 부분 surface에서 끊겨 있다 | removed | `modules/core/session_logger.py:262-287`, `modules/core/failure_analyzer.py:28-48`, `modules/core/artifact_logging.py:68-83`이 모두 `report_soft_failure()`를 호출한다. `tests/test_session_logger.py:319-330`, `tests/test_artifact_logging.py:45-55`, `tests/test_failure_analyzer.py:534-545`도 파일 생성을 잠근다. |
| `ProcessRunner` 종료 diagnostics가 너무 얇아 bridge operator surface에 의미 있는 실패 문맥을 남기지 못한다 | removed | `modules/api/process_runner.py:425-442`는 `failure_phase`, `stdout_tail`, `stderr_tail`, `last_prompt_step`, `duration_ms`를 포함한다. `tests/test_process_runner.py:274-337`, `tests/test_bridge_server_http_contract.py:51-110`도 이를 검증한다. |

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `decisions.jsonl` join contract | 테스트 공백 | Stage 3 / Stage 4 decision row 하나만으로 attempt / artifact join이 가능한지 검증 |
| desktop proof surface | API contract 공백 | `/quality/dashboard`가 `proof_status`, `sink_alignment_summary`, `runtime_audit_summary digest`를 싣는지 검증 |
| backend-wide runtime proof | canary scope 공백 | Stage 3 + Stage 4를 함께 닫는 multi-stage canary 또는 proof matrix |

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- `PASS1 -> PASS2 -> PASS3` 요약 포함
