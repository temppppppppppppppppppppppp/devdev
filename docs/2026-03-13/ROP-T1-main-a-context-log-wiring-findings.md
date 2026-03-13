# ROP-T1: main_a Context Log Wiring Findings

> 작성일: 2026-03-13
> 상태: `PASS3 completed`
> 트랙: `T1 main_a wrapper -> context -> log sink wiring`
> 기준 오더: `runtime-observability-provenance-artifact-detail-full-survey-audit-order.md`
> 검증 실행:
> - `pytest -q tests/test_stage3_orchestrator.py tests/test_stage4_context.py tests/test_stage4_post_processor.py tests/test_session_logger.py tests/test_stage4_orchestrator.py tests/test_stage4_interview_round.py tests/test_main_a_stage_entry_contracts.py` -> `279 passed`
> - runtime proof A: real `SessionLogger`로 Stage3 success path 1회 재현 -> `STAGE3_DECISION_META_KEYS=arc_no,quality_risk`, `STAGE3_DECISION_HAS_ATTEMPT_KEY=False`
> - runtime proof B: real `Stage4Context.from_app()` + `AuditService` + `Stage4PostProcessor` 재현 -> `soft_failures.jsonl` 1건, `runtime_audit_summary.json counts={"stage4_complete": 1}`

---

## 범위

- `main_a.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/session_logger.py`
- `modules/core/services/audit_service.py`
- `modules/core/soft_failure.py`

---

## PASS 1 - 표면 수집

| # | 후보 | 확신도 | 태그 | 초기 판정 |
|---|------|--------|------|-----------|
| 1 | Stage3 `session/decisions.jsonl`이 `attempt_key`/artifact linkage를 잃는다 | HIGH | `wiring`, `artifact`, `provenance` | PASS3 확정 |
| 2 | Stage4 soft-failure가 `soft_failures.jsonl`에는 남지만 `runtime_audit_summary.json`에는 누락된다 | HIGH | `wiring`, `artifact`, `runtime-proof` | PASS3 확정 |
| 3 | Stage4 completion callback source가 `ctx`가 아니라 `self.app`에 고정된다 | HIGH | `wiring`, `provenance` | PASS2 제거 |
| 4 | `main_a.py` Stage4 wrapper가 `session_logger`를 누락한다 | MED | `wiring` | PASS2 제거 |

---

## PASS 2 - 교차 검증

| 후보 | 판정 | 사유 |
|------|------|------|
| 3 | `already-covered-do-not-reopen` | `modules/core/stage4_orchestrator.py:1594-1603`의 `self.app` 직접 참조는 `MFS-T3-02`에서 이미 확정됐다. 이번 문서에서는 중복 재오픈 대신 evidence-layer 영향만 연결 근거로 사용했다. |
| 4 | 제거 | 과거 `manual Stage4Context(...)` 누락 표면은 현재 코드에 없다. 현재 `main_a.py:3542-3545`는 `Stage4Context.from_app(self)`를 사용하고, `tests/test_main_a_stage_entry_contracts.py:22-68`가 `ctx.session_logger` 유지까지 잠근다. |

---

## PASS 3 - 최종 확정

### [ROP-T1-001] P1 | Stage3 decision row가 `attempt_key` 없이 저장돼 session sink 단독 포렌식이 끊긴다

| 필드 | 내용 |
|------|------|
| ID | `ROP-T1-001` |
| Severity | `P1` |
| 현상 요약 | Stage3는 `ctx.session_logger`까지는 정상 주입되지만, 실제 `session/decisions.jsonl` row를 쓸 때 `attempt_key`, `candidate_key`, `artifact_path`를 넘기지 않는다. 같은 attempt의 DB/summary sink는 모두 이 필드를 갖는데 session decision row만 빠져 join contract가 끊긴다. |
| 코드 근거 | `main_a.py:2916-2921`와 `modules/core/stage3_context.py:100-128`은 `session_logger`를 정상 배선한다. 그러나 `modules/core/stage3_orchestrator.py:1306-1318` success path는 `arc_no`, `quality_risk`만 `log_decision()`에 넘기고, `modules/core/stage3_orchestrator.py:1324-1419`에서야 `attempt_key`/`candidate_key`/`artifact_path`를 DB·summary sink에 기록한다. reject path도 동일하게 `modules/core/stage3_orchestrator.py:1812-1822`에서는 bare decision row만 쓰고, `modules/core/stage3_orchestrator.py:1829-1923`에서만 `attempt_key`를 만든다. `modules/core/session_logger.py:111-138`은 call-site가 넘긴 meta만 기록하므로 logger 자체 문제가 아니다. |
| downstream 영향 경계 | operator가 `logs/session/decisions.jsonl`만으로 Stage3 retry를 추적할 때 같은 `ep_num`의 여러 attempt를 구분할 수 없다. `stage_attempts`, `director_selections`, `[STAGE3_EPISODE_SUMMARY]` 로그에는 있는 attempt-level provenance/artifact linkage가 session sink에서만 사라져 cross-sink join이 깨진다. |
| 현재 테스트 근거 또는 테스트 부재 | `tests/test_stage3_orchestrator.py:743-775`, `tests/test_stage3_orchestrator.py:815-838`는 `attempt_key`를 `pass_rate_monitor`, DB, summary log에서만 검증한다. `_session_logger.log_decision()` call kwargs를 검증하는 테스트는 없다. real `SessionLogger` 재현에서도 `STAGE3_DECISION_META_KEYS=arc_no,quality_risk`, `STAGE3_DECISION_HAS_ATTEMPT_KEY=False`가 확인됐다. |
| 기존 문서와의 중복 여부 | `related-but-new-evidence-layer-surface` — `stage3-10ep-log-remediation-postfix-3pass-closure.md`는 DB selection persistence와 `attempt_key` alignment를 닫았지만, `session/decisions.jsonl`의 Stage3 joinability는 다루지 않았다. `logging-hardening` postfix closure도 Stage4 decision rows만 범위였다. |
| 권장 후속 조치 | Stage3 success/reject 경로에서 `_attempt_key`, `_candidate_key`, `_artifact_meta["artifact_path"]`를 계산한 뒤 `session_logger.log_decision()` meta로 동일하게 넘긴다. regression은 MagicMock call assertion만으로 끝내지 말고 실제 `decisions.jsonl` row를 읽어 `attempt_key` 존재를 확인하는 형태가 적절하다. |

### [ROP-T1-002] P1 | Stage4 degraded completion이 `soft_failures.jsonl`과 `runtime_audit_summary.json`에 서로 다른 사실로 남는다

| 필드 | 내용 |
|------|------|
| ID | `ROP-T1-002` |
| Severity | `P1` |
| 현상 요약 | Stage4 post-processor의 degraded event는 `soft_failures.jsonl`에는 기록되지만, `Stage4Context`가 `audit_event`를 운반하지 않아 `runtime_audit`/`runtime_audit_summary.json`에는 반영되지 않는다. 반면 Stage4 완료 summary는 `self.app` 경로로 계속 기록돼 operator-facing evidence layer가 split-brain이 된다. |
| 코드 근거 | `modules/core/stage4_context.py:45-80`의 `__slots__`와 `modules/core/stage4_context.py:190-221`의 `from_app()`에는 `audit_event`/`write_audit_summary`가 없다. `modules/core/stage4_post_processor.py:27-53`는 `_report_soft_failure()`에서 `getattr(self.ctx, "audit_event", None)`를 relay로 사용하고, `modules/core/stage4_post_processor.py:815-816`, `modules/core/stage4_post_processor.py:840-841`, `modules/core/stage4_post_processor.py:1023-1024`도 동일 패턴이다. `modules/core/soft_failure.py:158-170`은 `audit_event`가 callable일 때만 `soft_failure`를 `runtime_audit`로 relay하고, 아니면 sidecar JSONL만 남긴다. 동시에 `modules/core/stage4_orchestrator.py:1594-1603`은 completion audit와 summary를 여전히 `self.app`에서 직접 호출한다. |
| downstream 영향 경계 | 같은 Stage4 run에서 `logs/soft_failures.jsonl`은 degradation을 보여 주는데 `logs/runtime_audit_summary.json`은 `stage4_complete`만 집계할 수 있다. operator가 summary나 `runtime_audit.jsonl`만 보면 degraded completion을 놓치고, sidecar까지 열어야만 실제 상태를 복원할 수 있다. |
| 현재 테스트 근거 또는 테스트 부재 | `tests/test_stage4_post_processor.py:880-896`은 `soft_failures.jsonl` 생성만 확인하고 `runtime_audit_summary.json` alignment를 보지 않는다. `tests/test_stage4_orchestrator.py:121-144`는 app-level `stage4_complete` summary 호출만 확인한다. `tests/test_stage4_context.py:140-185`의 callback extraction 목록에도 `audit_event`/`write_audit_summary`가 없다. real `Stage4Context.from_app()` + `AuditService` 재현에서는 `soft_failures.jsonl` 1건이 생성됐지만 `runtime_audit_summary.json`의 counts는 `{"stage4_complete": 1}`만 남았고 `soft_failure`는 없었다. |
| 기존 문서와의 중복 여부 | `related-but-new-evidence-layer-surface` — `MFS-T3-02`는 Stage4 completion callback source split을, `MLW-T3-002`는 `audit_event` 미배선을 각각 다뤘다. 이번 finding은 둘이 결합돼 `soft_failures.jsonl`과 `runtime_audit_summary.json`이 서로 다른 사실을 보존한다는 evidence-layer contract 붕괴를 새로 확정한다. |
| 권장 후속 조치 | Stage4는 `audit_event`/`write_audit_summary`를 `Stage4Context`에 명시 배선하고 `self.app` 직접 참조를 제거하거나, 반대로 post-processor soft-failure relay가 app-level audit service를 직접 쓰도록 단일 source를 정한다. 회귀 테스트는 real `Stage4Context.from_app()`와 real `AuditService`를 함께 사용해 `soft_failures.jsonl`과 `runtime_audit_summary.json`이 같은 degradation을 보존하는지 검증해야 한다. |

---

## PASS1 -> PASS2 -> PASS3 요약

| 단계 | 후보 수 | 비고 |
|------|--------|------|
| PASS1 | 4 | Stage3 session decision contract 1건, Stage4 audit/soft-failure split 1건, 기존/해결 항목 2건 수집 |
| PASS2 제거 | 2 | `MFS-T3-02` 중복 1건, 이미 수정된 Stage4 wrapper session_logger 누락 1건 제거 |
| PASS3 확정 | 2 | `ROP-T1-001`, `ROP-T1-002` |

### Severity 합계

| Severity | 건수 |
|----------|------|
| P0 | 0 |
| P1 | 2 |
| P2 | 0 |
| P3 | 0 |
| 합계 | 2 |

---

## Coverage Gap / Open Question

1. live project rerun에서 `Stage3 decisions.jsonl`이 실제 multi-attempt row를 남길 때 operator tooling이 `ep_num`만으로 오판하는지까지는 재현하지 않았다. 그러나 코드와 real row 샘플만으로 `attempt_key` 부재는 이미 확인됐다.
2. Stage4 failure-exit path(`stage4_complete`가 쓰이지 않는 경로)에서 `soft_failures.jsonl`과 `runtime_audit.jsonl` 간 불일치 규모가 success path와 동일한지는 추가 runtime proof가 필요하다.

---

## 결론

- `main_a.py`의 현재 Stage4 wrapper는 `Stage4Context.from_app(self)`로 정리돼 `session_logger` 누락 문제는 재현되지 않았다.
- 그러나 evidence-layer contract 관점에서는 `Stage3 session decision row joinability`와 `Stage4 degraded-completion audit split` 두 항목이 아직 live다.
- T1 기준 우선 remediation 순서는 `Stage4 audit source 단일화 -> Stage3 session decision attempt_key/artifact linkage 보강`이 적절하다.
