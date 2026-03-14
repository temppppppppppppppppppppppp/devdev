# GDFS-T2 Persistence / Artifact / Evidence Findings

> 작성일: 2026-03-13
> 상태: `PASS3 confirmed`
> 조사 모드: `static / read-only / baseline-aware / UTF-8 only`
> 기준 오더: `docs/2026-03-13/global-detail-full-survey-master-audit-order.md`
> baseline 참조: `runtime-observability-provenance-artifact-detail-consolidated-findings-3pass-reaudit.md`, `ROP-T1-main-a-context-log-wiring-findings.md`, `ROP-T3-structured-sink-alignment-findings.md`, `XC-ERR-T3-rollback-handler-compensation-gap-findings.md`, `XC-DB-consolidated-findings-3pass-reaudit.md`

---

## 요약

이번 T2의 목적은 runtime/evidence baseline을 그대로 재출력하는 것이 아니라, **현재 코드 기준으로 아직 살아 있는 persistence / artifact / evidence layer 결함만 retained set으로 다시 잠그는 것**이다.

결론:

- 신규 P0는 없다.
- retained P1 2건, retained P2 2건을 확인했다.
- 기존 baseline 중 `ROP-T1-002 Stage4 degraded completion split`과 `_safe_commit False-path 미롤백` 계열은 현재 코드에서 해소되어 재오픈하지 않았다.

핵심은 아래 4건이다.

1. Stage 3 `session/decisions.jsonl`는 여전히 attempt/artifact join key 없이 남는다.
2. Stage 3 rationale는 여전히 `stage_attempts`가 아니라 `director_selections`에만 실질 저장된다.
3. `runtime_audit_summary.json`는 여전히 completion heartbeat일 뿐 structured sink digest가 아니다.
4. `_restore_runtime_state()`는 여전히 `emotion_tracker` / `state_delta_tracker` rollback 실패를 비보호 호출한다.

---

## 조사 범위

- `modules/core/stage3_orchestrator.py`
- `modules/core/session_logger.py`
- `modules/core/db_manager.py`
- `modules/core/services/audit_service.py`
- `modules/core/services/project_service.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_post_processor.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_audit_service.py`
- `tests/test_stage4_context.py`
- `tests/integration/test_patch_wiring.py`
- baseline 문서 5종

---

## PASS 1 후보

1. Stage4 degraded completion evidence split 잔존 여부
2. Stage3 `session/decisions.jsonl` joinability gap
3. Stage3 rationale SSOT split
4. `runtime_audit_summary.json` structured digest 부재
5. `_safe_commit()` False-path rollback gap
6. `_restore_runtime_state()` tracker rollback 무보호

---

## PASS 2 제거

### 제거 1. Stage4 degraded completion evidence split

- 기존 baseline:
  - `ROP-T1-002`
- 현재 코드:
  - `modules/core/stage4_context.py:81-84`는 `audit_event`, `write_audit_summary`, `flush_audit_buffer`, `safe_commit`를 `__slots__`에 포함한다.
  - `modules/core/stage4_context.py:233-236`는 `from_app()`에서 해당 callback을 직접 배선한다.
  - `modules/core/stage4_orchestrator.py:1594-1620`와 `modules/core/stage4_post_processor.py:35-48`는 이제 같은 context callback 경로를 쓴다.
  - `tests/test_stage4_context.py:165-203`, `tests/test_stage4_context.py:363-375`도 callback wiring을 잠근다.
- 판정:
  - `live-code-changed`
  - baseline 시점 split-brain은 현재 트리에서 재현되지 않으므로 reopen 금지

### 제거 2. `_safe_commit()` False-path 미롤백 gap

- 기존 baseline:
  - `XC-ERR-016`
  - `XC-ERR-017`
  - `XC-ERR-018`
- 현재 코드:
  - `main_a.py:411-420`의 `_safe_commit()`는 commit 예외 시 내부에서 `conn.rollback()`까지 수행한다.
  - `modules/core/services/project_service.py:190-191`
  - `modules/core/services/project_service.py:254-255`
  - `modules/core/services/project_service.py:346-347`
  - `modules/core/services/project_service.py:412-413`
    는 `_safe_commit()`가 `False`를 반환해도 `_rollback_open_transaction(project)`를 추가 호출한다.
- 판정:
  - `live-code-changed`
  - 현재 T2 retained finding으로 올리지 않음

---

## PASS 3 확정 Findings

### [GDFS-T2-001] P1 | Stage3 `session/decisions.jsonl`는 현재도 attempt/artifact join key 없이 남는다

1. ID
   - `GDFS-T2-001`
2. Severity
   - `P1`
3. 현상 요약
   - Stage3 success path의 `session_logger.log_decision(...)`는 `arc_no`, `quality_risk`만 meta로 넘기고, `attempt_key`, `candidate_key`, `artifact_path`는 그 뒤 DB / pass-rate / summary sink를 쓸 때에야 계산된다.
   - reject path도 동일하게 `result`, `score`만 남긴 뒤 나중에 `_attempt_key`와 `_candidate_key`를 만든다.
   - `SessionLogger`는 call-site가 준 meta만 `decisions.jsonl`에 기록하므로, Stage3 decision row는 여전히 session sink 단독 join이 불가능하다.
4. 코드 근거
   - `modules/core/stage3_orchestrator.py:1312-1318` — success decision row는 `arc_no`, `quality_risk`만 기록
   - `modules/core/stage3_orchestrator.py:1328-1393` — 같은 success path에서 나중에 `attempt_key`, `candidate_key`, `artifact_path` 생성 및 DB/pass-rate 기록
   - `modules/core/stage3_orchestrator.py:1818-1823` — reject decision row도 bare write
   - `modules/core/stage3_orchestrator.py:1834-1905` — reject path에서 나중에 `attempt_key`, `candidate_key` 생성
   - `modules/core/session_logger.py:111-138` — logger는 주어진 meta만 그대로 저장
5. downstream 영향 경계
   - `logs/session/decisions.jsonl` 단독 포렌식
   - Stage3 multi-attempt 추적, decision row와 DB artifact row의 조인, 운영자 incident replay가 session sink만으로는 닫히지 않는다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage3_orchestrator.py:805-859`는 `pass_rate_monitor`와 `save_stage_attempt()`의 `attempt_key` / `artifact_path`는 확인한다.
   - 그러나 `_session_logger.log_decision()` call kwargs 또는 실제 `decisions.jsonl` row에 `attempt_key`가 있어야 한다는 회귀 테스트는 없다.
7. baseline과의 관계
   - `related-but-retained`
   - `ROP-T1-001`의 evidence-layer 관점 재확인. 현재 코드 재검증 결과 여전히 open
8. 권장 후속 조치
   - Stage3 success/reject 경로에서 `_attempt_key`, `_candidate_key`, `_artifact_meta["artifact_path"]`를 계산한 뒤 `log_decision()` meta로 같이 넘겨야 한다.

### [GDFS-T2-002] P1 | Stage3 rationale는 아직도 `stage_attempts`가 아니라 `director_selections`에만 실질 저장된다

1. ID
   - `GDFS-T2-002`
2. Severity
   - `P1`
3. 현상 요약
   - `DBManager.save_stage_attempt()` 스키마는 이미 `selection_reason`, `verdict_reason`, `open_review`, `fix_scope_reasoning`, `runtime_advisory`, `retry_directives`를 받을 수 있다.
   - 그러나 Stage3 success/reject write path는 `save_stage_attempt()`에 그 필드를 넘기지 않고, rationale는 `_build_stage3_director_selection_kwargs()`를 통해 `director_selections`에만 보낸다.
   - 결과적으로 Stage3 final lineage sink와 rationale sink가 현재도 단일 table SSOT로 수렴하지 않는다.
4. 코드 근거
   - `modules/core/db_manager.py:3095-3143` — `save_stage_attempt()`는 rationale 계열 필드를 저장할 수 있음
   - `modules/core/stage3_orchestrator.py:1378-1393` — success `save_stage_attempt()` 호출은 `attempt_key`, `candidate_key`, `artifact_path`까지만 넘기고 rationale는 비움
   - `modules/core/stage3_orchestrator.py:1890-1905` — reject path도 동일
   - `modules/core/stage3_orchestrator.py:1652-1736` — Stage3는 `selection_reason`, `verdict_reason`, `attempt_key`, `candidate_key`, `artifact_path`를 별도 `director_selections` payload로 조립
5. downstream 영향 경계
   - `stage_attempts` 단독 기반 리포트
   - Stage 간 비교 리포트, failure analysis, operator summary가 Stage3만 별도 `director_selections` join 없이는 이유를 복원하지 못한다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage3_orchestrator.py:314-324`는 `save_director_selection()` payload의 rationale와 `attempt_key` 정합성만 잠근다.
   - `tests/test_db_manager.py:332-357`는 Stage4가 `stage_attempts`에 rationale를 넣을 수 있음을 검증한다.
   - Stage3 `stage_attempts(stage=3)`에도 rationale가 채워져야 한다는 테스트는 찾지 못했다.
7. baseline과의 관계
   - `related-but-retained`
   - `ROP-T3-001`의 현재형 재확인. schema capability는 늘었지만 Stage3 writer는 아직 따라오지 못했다.
8. 권장 후속 조치
   - Stage3도 Stage4처럼 `save_stage_attempt()`에 rationale 필드를 직접 채우거나
   - 반대로 Stage3는 `director_selections` mandatory join이란 점을 문서/도구/체크리스트에 강제해야 한다.

### [GDFS-T2-003] P2 | `runtime_audit_summary.json`는 여전히 completion heartbeat일 뿐 structured sink digest가 아니다

1. ID
   - `GDFS-T2-003`
2. Severity
   - `P2`
3. 현상 요약
   - 현재 summary payload는 `tag`, `timestamp`, `total_events`, `counts`, `latest_event_type`, `recent_events`만 기록한다.
   - `attempt_key`, `candidate_key`, `artifact_path`, stage별 sink completeness, lifecycle coverage, latest structured lineage는 summary에 없다.
   - 즉 파일이 존재하고 `stage4_complete`가 찍혀 있어도 structured sink alignment가 닫혔다고 읽을 수 없다.
4. 코드 근거
   - `modules/core/services/audit_service.py:77-102` — summary payload 필드는 heartbeat 수준에 한정
   - `tests/test_audit_service.py:82-98` — `tag`, `total_events`, `counts`만 검증
   - `tests/test_stage4_orchestrator.py`는 summary write 호출 여부만 잠그고 structured digest contract는 검증하지 않음
5. downstream 영향 경계
   - operator-facing run summary
   - `runtime_audit_summary.json` 단독 판독 시 “completion은 됐지만 evidence sink는 비었음” 상태를 구분하기 어렵다.
6. 현재 테스트 근거 또는 테스트 부재
   - summary 생성과 기본 count는 테스트가 있다.
   - attempt-level digest가 summary에 포함돼야 한다는 회귀 테스트는 없다.
7. baseline과의 관계
   - `related-but-retained`
   - `ROP-T3-003`의 현재형 재확인. 현재 코드에서도 여전히 heartbeat-only
8. 권장 후속 조치
   - `runtime_audit_summary.json`를 completion-only heartbeat로 명시 격하하거나
   - per-stage sink count, latest attempt key, latest artifact digest, lifecycle completeness를 추가해 operator summary contract로 승격해야 한다.

### [GDFS-T2-004] P2 | `_restore_runtime_state()`는 여전히 tracker rollback 실패를 비보호 호출한다

1. ID
   - `GDFS-T2-004`
2. Severity
   - `P2`
3. 현상 요약
   - `_restore_runtime_state()`는 `WorldState`, `FactLedger`, `PresetRegistry` 복원은 try/except로 감싸지만, `emotion_tracker.rollback_to()`와 `state_delta_tracker.rollback_to()`는 그대로 호출한다.
   - 이 두 tracker 중 하나라도 예외를 던지면 이후 런타임 복원 흐름이 중단돼 partial restore가 발생할 수 있다.
4. 코드 근거
   - `modules/core/services/project_service.py:71-82` — `WorldState`, `FactLedger`는 try/except 보호
   - `modules/core/services/project_service.py:84-92` — `emotion_tracker` / `state_delta_tracker`는 직접 `rollback_to(target_ep)` 호출
   - `modules/core/services/project_service.py:94-98` — `PresetRegistry`는 다시 try/except 보호
5. downstream 영향 경계
   - rollback / rewind / wipe 이후 런타임 복원
   - DB commit은 끝났는데 tracker 예외로 후속 복원이 끊기면 operator는 partial restore 상태를 보게 된다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/integration/test_patch_wiring.py:385-452`, `tests/integration/test_patch_wiring.py:458-525`는 rollback 호출 wiring만 확인한다.
   - tracker 예외를 던졌을 때 복원이 계속 진행되는지 검증하는 테스트는 없다.
7. baseline과의 관계
   - `related-but-retained`
   - `XC-ERR-019`의 현재형 재확인. safe commit 경로는 정리됐지만 tracker compensation gap은 그대로 남아 있다.
8. 권장 후속 조치
   - `emotion_tracker` / `state_delta_tracker`도 `WorldState`와 같은 try/except + UI/audit log 패턴으로 감싸고, partial restore 여부를 명시 기록해야 한다.

---

## Current Phase / Resume Packet

1. `Current phase`
   - `T2 completed`
2. `Last completed pass`
   - `PASS3`
3. `Last completed surface`
   - `persistence / artifact / evidence layer`
4. `Next surface`
   - `T3 config / contract / SSOT drift`
5. `Reopen reason codes used`
   - `live-code-changed` for removed baseline items
6. `Stop gate or blocker`
   - `없음`

---

## 3PASS 요약

- `PASS1 6건 -> PASS2 2건 제거 -> PASS3 최종 4건 확정`
- 최종 retained set:
  - `P1 2건`
  - `P2 2건`
  - `P3 0건`
