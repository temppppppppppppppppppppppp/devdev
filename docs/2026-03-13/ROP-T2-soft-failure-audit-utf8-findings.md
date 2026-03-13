# ROP-T2 Soft-Failure / Audit / UTF-8 Findings

> 작성일: 2026-03-13
> 상태: `PASS3 completed`
> 담당 터미널: `T2`
> 범위: `modules/validation/validation_orchestrator.py`, `modules/core/soft_failure.py`, `modules/core/failure_analyzer.py`, `modules/core/artifact_logging.py`, `main_a.py::_write_audit_summary`, operator-facing runtime health / canary consumer
> 기준 오더: `docs/2026-03-13/runtime-observability-provenance-artifact-detail-full-survey-audit-order.md`

## PASS 1 - 표면 수집

- 후보 1 `HIGH` / tags=`wiring,artifact,runtime-proof`
  - `ValidationOrchestrator`의 실제 sync/parallel 예외 경로가 `soft_failures.jsonl` / audit summary로 relay되지 않는지 점검
- 후보 2 `HIGH` / tags=`artifact,provenance,runtime-proof`
  - `artifact_logging` soft-failure가 `runtime_audit_summary.json`과 canary hard gate에 보존되는지 점검
- 후보 3 `MED` / tags=`wiring,provenance`
  - tagged audit summary contract가 protocol/context green 뒤에 계속 숨는지 점검
- 후보 4 `LOW` / tags=`utf8`
  - 현재 T2 범위 코드/테스트/대표 artifact에서 mojibake literal이 남아 있는지 점검

## PASS 2 - 교차 검증

- 후보 1 유지
  - `validation_orchestrator.py`는 `_report_soft_failure()` helper를 갖고도 실제 validator 예외 경로에서는 거의 사용하지 않는다.
  - `bridge_server.py`의 `runtime_health`는 `soft_failures.jsonl`만 읽는다.
  - 로컬 재현에서 sync 예외는 구조화 sink 없이 그대로 raise, parallel 예외는 `PASS` 반환까지 가능했다.
- 후보 2 유지
  - `artifact_logging.py`의 snapshot write failure는 `soft_failures.jsonl`에만 남고 audit relay가 없다.
  - `AuditService.write_audit_summary()`는 `runtime_audit`만 요약한다.
  - `stage4_canary_tools.py` hard gate는 `runtime_audit_summary.json`만 보고 `soft_failures.jsonl`을 보지 않는다.
- 후보 3 제거
  - 기존 `MFS-T5-001`, `OPUS-TF-T1`에서 이미 닫힌 blind spot이다.
  - 이번 트랙에서는 신규 evidence-layer drift가 아니라 기존 facade/protocol 계약 재확인 수준이었다.
- 후보 4 제거
  - 대상 파일과 대표 canary artifact에서 replacement character, triple-question sentinel, 깨진 한글을 확인하지 못했다.
  - 현재 T2 범위에서는 UTF-8 operator-surface 신규 finding을 확정할 근거가 부족했다.

## PASS 3 - 최종 확정

| ID | Severity | 상태 | 핵심 |
|----|----------|------|------|
| `ROP-T2-001` | `P1` | confirmed | 실제 validation 예외가 soft-failure/audit evidence layer로 relay되지 않아 branch별로 `REJECT`/`PASS`가 갈리면서도 구조화 증거는 남지 않는다 |
| `ROP-T2-002` | `P1` | confirmed | artifact snapshot write failure가 `soft_failures.jsonl`에만 남아 `runtime_audit_summary`와 canary hard gate는 `stage4_complete`로 계속 녹색일 수 있다 |

---

## [ROP-T2-001] 실제 validation 예외가 soft-failure/audit evidence layer로 relay되지 않는다

1. ID
   - `ROP-T2-001`
2. Severity
   - `P1`
3. 현상 요약
   - `ValidationOrchestrator`는 `_report_soft_failure()` 경로를 갖고 있지만 실제 validator runtime exception에는 거의 연결되지 않는다.
   - live sync 경로에서는 예외가 구조화 sink 없이 상위로 올라가고, unused-but-supported parallel 경로에서는 예외를 synthetic advisory로 바꾼 뒤 `soft_failures.jsonl`/audit relay 없이 `PASS`까지 반환할 수 있다.
4. 코드 근거
   - `modules/validation/validation_orchestrator.py:276-305` `_report_soft_failure()`는 audit relay + `soft_failures.jsonl` persist를 모두 지원한다.
   - `modules/validation/validation_orchestrator.py:440-447`, `modules/validation/validation_orchestrator.py:1224-1231` 실제 호출처는 `FailureLearner.record_failure()` helper 예외뿐이다.
   - `modules/validation/validation_orchestrator.py:465`, `modules/validation/validation_orchestrator.py:499`, `modules/validation/validation_orchestrator.py:539` sync 본체의 `consistency/scoring/advisory` 호출은 예외 guard가 없다.
   - `modules/validation/validation_orchestrator.py:1270-1297` parallel 본체는 `asyncio.gather(..., return_exceptions=True)` 뒤 `logging.warning()`만 남기고 `_report_soft_failure()`를 호출하지 않는다.
   - `modules/api/bridge_server.py:1107-1144` operator-facing `runtime_health`는 `soft_failures.jsonl`만 읽는다.
   - `modules/domain/agents/director_auditor.py:304-335` live sync consumer는 예외를 `REJECT` 결과로 바꾸지만 audit/soft-failure structured sink 추가 기록은 없다.
5. downstream 영향 경계
   - `DirectorAuditor` 경유 sync validation 실패는 operator가 `reason="V0128 검증 시스템 오류"`만 보게 되고, runtime health / audit summary에는 동일 사실이 남지 않는다.
   - `BatchValidator`는 예외를 `{success: False, error: ...}`로만 반환하므로 배치 포렌식에서 structured soft-failure join이 불가능하다.
   - parallel API를 다시 소비하게 되면 동일 runtime error가 branch에 따라 `PASS`와 함께 표면화될 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_validation_orchestrator_soft_failure.py:6-25`는 helper 직접 호출만 검증한다.
   - `tests/test_validation_orchestrator.py:58-64`는 `validate_parallel_sync_v59()` wrapper fallback만 확인하고 실제 예외 relay를 보지 않는다.
   - `tests/test_validation.py:393-409`는 `unjustifiable_violations`가 있어도 `final_decision == "PASS"`를 기대해 runtime error synthetic advisory가 PASS로 남을 가능성을 가린다.
7. 기존 문서와의 중복 여부
   - `related-but-new-evidence-layer-surface`
   - `MFS-T5-002`는 "helper direct-call test blind spot"을 확정했다. 이번 finding은 그 blind spot이 실제 sink drift와 branch별 verdict divergence로 이어진다는 점을 runtime proof까지 포함해 확정한 것이다.
8. 권장 후속 조치
   - sync/parallel의 `consistency/scoring/advisory` 예외를 `_report_soft_failure()`로 공통 relay하고, audit_event가 있으면 `soft_failure` audit row도 남긴다.
   - runtime error를 synthetic advisory로 바꿀 때는 최소 `final_decision != PASS` invariant를 강제한다.
   - helper 직접 호출이 아니라 실제 `validate()` / `validate_parallel_v59()` 예외 경로를 재현하는 focused regression을 추가한다.
9. Artifact / runtime proof
   - 2026-03-13 로컬 재현에서 sync `consistency.validate()` 예외는 `RuntimeError`로 그대로 상승했고 `soft_failures.jsonl`/audit call은 모두 0건이었다.
   - 같은 날 parallel 재현에서는 `consistency.validate()` 예외 후 `final_decision="PASS"`와 feedback advisory만 남고 `soft_failures.jsonl`/audit call은 모두 0건이었다.

## [ROP-T2-002] artifact snapshot soft-failure가 runtime_audit_summary / canary hard gate에 보존되지 않는다

1. ID
   - `ROP-T2-002`
2. Severity
   - `P1`
3. 현상 요약
   - `snapshot_logged_artifact()` write failure는 `soft_failures.jsonl`에만 남고 `runtime_audit_summary.json`에는 반영되지 않는다.
   - Stage 4 canary hard gate는 `runtime_audit_summary`만 확인하므로 artifact snapshot persistence 실패가 있어도 `stage4_complete` evidence를 녹색으로 읽을 수 있다.
4. 코드 근거
   - `modules/core/artifact_logging.py:68-83` snapshot write failure는 `report_soft_failure(...)`만 호출하고 audit relay 입력은 없다.
   - `modules/core/services/audit_service.py:72-101` `write_audit_summary()`는 `runtime_audit` 이벤트만 집계한다.
   - `main_a.py:2839-2841` `_write_audit_summary(tag)`는 이 summary writer의 thin delegate다.
   - `modules/core/stage4_canary_tools.py:268-279` hard gate는 `runtime_audit_summary.tag`와 `total_events`만 보고 `soft_failures.jsonl`은 검사하지 않는다.
5. downstream 영향 경계
   - canary / rerun proof가 `runtime_audit_summary.tag == stage4_complete`만으로 green 판정될 수 있어 artifact snapshot persistence 실패가 별도 확인 없이 묻힌다.
   - operator가 `runtime_audit_summary.json`과 `soft_failures.jsonl`을 함께 보지 않으면 artifact sink degradation을 놓칠 수 있다.
   - 후속 sink alignment는 artifact file missing으로 뒤늦게 잡을 수 있지만, runtime completion proof 단계에서는 이미 false-green이 가능하다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_artifact_logging.py:36-55`는 write failure 시 `soft_failures.jsonl` 생성만 확인하고 audit summary parity를 보지 않는다.
   - `tests/test_stage4_canary_tools.py:132-144`는 `runtime_audit_summary={"tag":"stage4_complete","total_events":1}`만으로 canary summary 입력을 구성하고 soft-failure 존재 여부는 고려하지 않는다.
   - `tests/test_bridge_quality_summary.py:172-221`는 runtime health가 `soft_failures.jsonl` 기반임을 확인하지만 canary / audit summary와의 정합성은 검증하지 않는다.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - artifact snapshot 실패를 audit_event에도 relay하거나, canary / live-run proof가 `soft_failures.jsonl` 최근 이벤트를 함께 읽게 한다.
   - `runtime_audit_summary`를 evidence SSOT로 유지할 생각이면 soft-failure count 또는 last_soft_failure를 summary에 병합한다.
   - canary hard gate에 `recent_soft_failures_present` 같은 explicit 경고/실패 조건을 추가한다.
9. Artifact / runtime proof
   - 2026-03-13 로컬 재현에서 `artifact_logging._write_artifact_snapshot = OSError("disk full")`로 강제한 뒤에도 `runtime_audit_summary.json`은 `{"tag":"stage4_complete","counts":{"stage4_complete":1}}`만 남았다.
   - 같은 재현에서 `soft_failures.jsonl`에는 `artifact_logging.snapshot_logged_artifact` failure row가 별도로 기록됐다.

## 제거 후보

- tagged audit summary facade blind spot
  - `already-covered-do-not-reopen`
  - 기존 `MFS-T5-001`, `OPUS-TF-T1-25`가 protocol/facade 계약 문제를 이미 확정했다.
- UTF-8 / mojibake literal
  - `already-covered-do-not-reopen` 아님
  - 이번 T2 범위 코드, 테스트, 대표 canary artifact에서는 신규 깨짐 문자열을 확인하지 못해 PASS3 채택하지 않았다.

## Coverage Gap / Open Question

- `validate_parallel_v59()`는 현재 코드 검색상 live consumer가 없고 테스트에서만 직접 호출된다. 다만 public helper로 남아 있고 오더가 명시적으로 parallel branch를 포함하므로 dormant surface로만 치부하지는 않았다.
- 현재 확인한 real project artifact에는 `soft_failures.jsonl` 자체가 드물다. 이것이 "문제가 적다"기보다는 해당 경로들이 structured sink로 잘 내려오지 않는 결과인지 live rerun proof가 추가로 필요하다.

## PASS 요약

- PASS1 후보 4건
- PASS2 제거 2건
- PASS3 확정 2건
