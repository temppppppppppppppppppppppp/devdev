# [MFS-T3] Stage3 / Stage4 Audit Callback Findings

> 작성일: 2026-03-13
> 상태: `executed / PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-facade-shim-detail-full-survey-audit-order.md`

이 문서는 `T3` 범위 실조사 결과다. 조사 중 코드 직접 수정은 하지 않았다.

---

## 조사 범위

- `main_a.py`: audit callback / stage context facade
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage3_context.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_orchestrator.py`

## 필수 근거

- `tests/test_stage3_orchestrator.py`
- `tests/test_stage4_orchestrator.py`
- `tests/test_run_stage4_canary.py`
- `modules/core/services/audit_service.py`
- `docs/2026-03-11/00-test-02-03-system-improvement-final-audit-codex.md`

## PASS 기록

- PASS 1: 후보 6건 수집
  - 후보 유지: Stage3 실패/중단 후 `stage3_complete` 기록, Stage4 completion callback의 `self.app` 직결, unresolved continuity pin 로그 mojibake
  - 후보 보류: Stage4 `stage4_complete` 오염 재발 여부, canary의 `flush -> summary -> analyze` 순서 불일치, `_classify_rejection_feedback()` 실소비 여부
- PASS 2: 후보 3건 제거
  - 제거 1: `stage4_complete` 오염은 현재 코드와 테스트에서 이미 닫혔다. `modules/core/stage4_orchestrator.py`는 `_run_interview_loop()`가 `True`면 summary 전에 return하고, `tests/test_stage4_orchestrator.py`가 early return / failed exhaustion / interrupt / exception 경로를 잠근다.
  - 제거 2: canary의 `flush -> summary -> analyze` 순서는 현재 consumer 기준 문제로 확정되지 않았다. `AuditService.write_audit_summary()`가 내부에서 `flush_audit_buffer()`를 먼저 호출하고, `scripts/run_stage4_canary.py`는 Stage4 종료 후 추가 flush 뒤 analyze를 수행한다.
  - 제거 3: `_classify_rejection_feedback()`는 이번 T3의 직접 downstream(`stage3_context.py`, `stage4_context.py`, `stage4_orchestrator.py`)에서 실제 사용처를 찾지 못해 finding이 아니라 coverage gap으로 이관한다.
- PASS 3: 아래 3건 확정

## Finding Ledger

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| `MFS-T3-01` | `P1` | confirmed | `stage3_orchestrator.stage_3_batch_blueprinting()` | Stage3 루프가 실패/중단으로 끊겨도 `stage3_complete` summary를 무조건 기록한다 |
| `MFS-T3-02` | `P2` | confirmed | `main_a._audit_event()`, `main_a._write_audit_summary()`, `Stage4Context`, `Stage4Orchestrator.stage_4_v2_chief_writer()` | Stage4 completion callback이 DI context를 우회하고 `self.app`에만 결합돼 성공/실패 경로의 callback source가 분리된다 |
| `MFS-T3-03` | `P3` | confirmed | `stage3_orchestrator._handle_success()` unresolved pin log | unresolved continuity pin 로그 문자열에 깨진 문자 `?슚`가 남아 있다 |

## 추가 검증

- 정적 대조:
  - `main_a.py:2719-2731`, `main_a.py:2804-2809`, `main_a.py:3432-3464`
  - `modules/core/stage3_context.py:94-120`
  - `modules/core/stage4_context.py:149-179`
  - `modules/core/stage4_orchestrator.py:1516-1549`
  - `modules/core/services/audit_service.py:41-103`
- 회귀 테스트:
  - `pytest -q tests/test_stage3_orchestrator.py tests/test_stage4_orchestrator.py tests/test_run_stage4_canary.py`
  - 결과: `112 passed in 3.32s`
- synthetic verification:
  - Stage3에서 `_generate_blueprint()`를 `REJECT`로 강제한 뒤 `stage_3_batch_blueprinting(target_ep=1)` 실행
  - 결과: `_write_audit_summary("stage3_complete")` 호출 확인
  - Stage4에 `ctx.audit_event` / `ctx.write_audit_summary`를 주입하고 `app._audit_event` / `app._write_audit_summary`도 분리 주입
  - 결과: success path는 `ctx`가 아니라 `app` callback만 호출함

## 상세 Findings

### [MFS-T3-01] `stage3_complete` summary가 Stage3 실패/중단 경로도 성공처럼 덮는다

1. ID
   - `MFS-T3-01`
2. Severity
   - `P1`
3. 현상 요약
   - `Stage3Orchestrator.stage_3_batch_blueprinting()`는 루프 종료 사유와 무관하게 마지막에 `ctx.write_audit_summary("stage3_complete")`를 호출한다. 그래서 `continuity_block`, arc context 미확보, blueprint integrity fail, DB commit fail, retry exhaustion 같은 Stage3 비완주 경로도 `stage3_complete` tag로 닫힐 수 있다.
4. 코드 근거
   - `modules/core/stage3_orchestrator.py:585-598` 루프 종료 직후 summary 무조건 기록
   - `modules/core/stage3_orchestrator.py:715-721` continuity block 시 `break=True`
   - `modules/core/stage3_orchestrator.py:724-737` arc context 미확보 / `ep_start` 누락 시 `break=True`
   - `modules/core/stage3_orchestrator.py:1489-1498` blueprint integrity fail 시 `break=True`
   - `modules/core/stage3_orchestrator.py:1503-1512` DB commit fail 시 `break=True`
   - `modules/core/stage3_orchestrator.py:1938-1996` retry exhaustion 후 `break=True`
   - synthetic check 결과 `_generate_blueprint() -> REJECT`만으로도 `_write_audit_summary("stage3_complete")`가 호출됐다.
5. downstream 영향 경계
   - 영향 있음:
     - `runtime_audit_summary.json` tag를 종료 상태의 source-of-truth로 읽는 감리 문서/운영 스크립트
     - Stage3 단독 실행 또는 Stage4 진입 전 중단 케이스의 종료 판정
   - 영향 제한:
     - blueprint 저장/DB commit/pass_rate 기록 자체를 바꾸지는 않는다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage3_orchestrator.py:845-861`는 성공 경로에서만 summary 호출을 검증한다.
   - `tests/test_stage3_orchestrator.py:651-655`, `805-812`, `829-839`는 break/failure 경로를 보지만 summary 미기록을 검증하지 않는다.
   - 전체 회귀(`112 passed`)가 green이어도 이 semantic drift는 놓친다.
7. 기존 문서와의 중복 여부
   - `related-but-new-facade-surface`
   - `docs/2026-03-11/00-test-02-03-system-improvement-final-audit-codex.md`는 Stage4의 `stage4_complete` 오염을 다뤘고, 이번 finding은 Stage3 summary semantics에 대한 신규 facade-contract 문제다.
8. 권장 후속 조치
   - `stage3_complete` 기록 조건을 "루프가 실패/중단 없이 target 범위를 정상 완료"로 좁힌다.
   - `continuity_block`, `no_arc_context`, `integrity_fail`, `db_commit_fail`, `retry_exhaustion` 경로에서 summary 미기록 회귀 테스트를 추가한다.

### [MFS-T3-02] Stage4 completion callback source가 `ctx`와 `app`로 갈라져 facade contract가 분열돼 있다

1. ID
   - `MFS-T3-02`
2. Severity
   - `P2`
3. 현상 요약
   - `main_a.py`는 `_audit_event()` / `_write_audit_summary()` facade를 제공하지만 Stage4 DI 컨텍스트에는 이 callback들을 싣지 않는다. 실제 Stage4 성공 경로는 `ctx`가 아니라 `self.app`에서 audit/summary callback을 다시 조회하고, 실패/중단 경로의 flush/commit은 `ctx`를 사용한다. 즉 Stage4 completion audit contract의 source가 success와 non-success에서 다르다.
4. 코드 근거
   - `main_a.py:2719-2729` audit facade 메서드 존재
   - `main_a.py:3432-3461` Stage4Context 주입 시 callback 7종만 연결하고 `_audit_event` / `_write_audit_summary`는 제외
   - `modules/core/stage4_context.py:25-27`, `modules/core/stage4_context.py:55-62`, `modules/core/stage4_context.py:149-179` Stage4Context callback surface는 `flush_audit_buffer`와 `safe_commit`까지이며 completion audit callback은 빠져 있다
   - `modules/core/stage4_orchestrator.py:1524-1533` success path는 `getattr(self.app, "_audit_event")`, `getattr(self.app, "_write_audit_summary")` 호출
   - `modules/core/stage4_orchestrator.py:1537-1549` interrupt/exception path는 `self.ctx.flush_audit_buffer()` / `self.ctx.safe_commit()` 호출
   - synthetic check 결과 `ctx.audit_event` / `ctx.write_audit_summary`를 별도로 넣어도 success path는 `app` callback만 호출했다.
5. downstream 영향 경계
   - 영향 있음:
     - context-injected harness, adapter app, partial migration 경로에서 success completion audit event/summary가 누락될 수 있다
     - Stage4 callback contract를 `ctx` 기준으로 읽는 테스트/감리가 실제 동작과 어긋날 수 있다
   - 영향 제한:
     - 현재 `SovereignApp` 실서비스 경로는 `self.app`에 facade가 있어 즉시 장애로 드러나지 않는다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage4_orchestrator.py:120-143`는 success path에서 `mock_app._audit_event` / `mock_app._write_audit_summary`만 확인한다.
   - `tests/test_stage4_context.py:140-179`는 callback 7종만 검증하고 audit/summary callback 부재를 문제로 보지 않는다.
   - `tests/test_run_stage4_canary.py:7-29`는 flush 후 analyze 순서만 보고 success completion callback source는 검증하지 않는다.
7. 기존 문서와의 중복 여부
   - `related-but-new-facade-surface`
   - 기존 `MCP-T2` 계열 문서는 Stage3 bootstrap/app bypass를 다뤘고, 이번 finding은 Stage4 audit callback surface에 한정된 신규 contract 분열이다.
8. 권장 후속 조치
   - Stage4 completion callback의 단일 source-of-truth를 정한다.
   - `Stage4Context`를 계약으로 유지할 거면 `audit_event` / `write_audit_summary`도 명시적으로 싣고 orchestrator가 `ctx`만 사용하게 맞춘다.
   - 반대로 `self.app` 직결을 유지할 거면 `Stage4Context` 문서와 테스트에서 completion audit은 DI 대상이 아님을 명시한다.

### [MFS-T3-03] unresolved continuity pin 로그가 이미 mojibake 상태다

1. ID
   - `MFS-T3-03`
2. Severity
   - `P3`
3. 현상 요약
   - unresolved continuity pin 경로의 UI 로그 prefix가 `?슚`로 깨져 있다. payload/audit은 남지만 운영자가 화면/로그에서 즉시 읽는 관측성 문자열은 이미 손상돼 있다.
4. 코드 근거
   - `modules/core/stage3_orchestrator.py:1479-1481`
   - UTF-8로 직접 읽은 결과 해당 문자열은 literal `"?슚 [PinGuard] ep {working_ep} unresolved continuity pins"`였다.
5. downstream 영향 경계
   - 영향 있음:
     - 운영자 콘솔 로그
     - grep 기반 문자열 탐색, 수동 장애 확인
   - 영향 제한:
     - `_continuity_pin_unresolved` payload 저장과 `audit_event("continuity_pin_unresolved", ...)` 자체는 계속 수행된다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage3_orchestrator.py:813-827`는 unresolved payload와 `audit_event` 발생만 확인한다.
   - 로그 문자열/UTF-8 품질을 검증하는 테스트는 없다.
7. 기존 문서와의 중복 여부
   - `none`
8. 권장 후속 조치
   - 해당 로그 prefix를 정상 UTF-8 문자열로 교체한다.
   - 최소한 unresolved continuity pin 경로의 log string snapshot 또는 인코딩 sentinel 검사를 추가한다.

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `_classify_rejection_feedback()` | `main_a.py`와 `StateService` 정의만 확인됐고, 이번 T3 직접 downstream과 필수 테스트에서는 사용처를 찾지 못했다 | `stage4_interview_round.py` 또는 feedback classification 실제 소비 경로를 포함한 별도 audit |
| 실제 `main_a._get_arc_context_for_episode()` semantic coverage | `tests/test_stage3_orchestrator.py`는 대부분 callback을 `MagicMock`으로 대체해 real facade의 malformed arcs 처리 의미를 잠그지 않는다 | real `SovereignApp` 또는 facade 단위 테스트로 `ep_start`/`ep_end` 타입 오류, `arc_data` 비dict, `arcs` lookup 예외를 직접 검증 |

## PASS 요약

- PASS1 후보 수집: 6건
- PASS2 제거: 3건
  - Stage4 `stage4_complete` 오염 재발 없음
  - canary `flush -> summary -> analyze` 순서 이상 없음
  - `_classify_rejection_feedback()`는 finding 확정 대신 coverage gap 이관
- PASS3 확정: 3건
  - `MFS-T3-01`
  - `MFS-T3-02`
  - `MFS-T3-03`

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- PASS1 후보 -> PASS2 제거 -> PASS3 확정 요약 포함
