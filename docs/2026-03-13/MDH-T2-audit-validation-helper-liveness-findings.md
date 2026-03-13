# MDH-T2: Audit / Validation Helper Liveness Findings

> 작성일: 2026-03-13
> 작성자: Codex (OPUS 초안 재감리 보강)
> 트랙: `main_a.py` dormant helper / live consumer inventory — Terminal 2
> 상태: `PASS3 재확정`
> 초점: audit, validation, arc context helper의 live consumer 여부

---

## 0. 조사 대상 helper 목록

| # | Helper | 정의 위치 |
|---|--------|-----------|
| 1 | `_classify_rejection_feedback()` | `main_a.py:2825` |
| 2 | `_audit_event()` | `main_a.py:2831` |
| 3 | `_flush_audit_buffer()` | `main_a.py:2835` |
| 4 | `_write_audit_summary()` | `main_a.py:2839` |
| 5 | `_get_arc_context_for_episode()` | `main_a.py:2843` |
| 6 | `_validate_arc_data_fields()` | `main_a.py:2892` |
| 7 | `_validate_blueprint_integrity()` | `main_a.py:2904` |
| 8 | `_build_item_acquisition_timeline()` | `main_a.py:2763` |

---

## 1. Helper별 Liveness 판정

### 1.1 `_classify_rejection_feedback()` — **DORMANT**

- **정의**: `main_a.py:2825-2829` → thin delegate → `StateService.classify_rejection_feedback()` → `FeedbackSystem.classify_rejection_feedback()`
- **production caller 검색 결과**: **0건**
  - `modules/` 전역에서 `_classify_rejection_feedback` 호출 0건
  - `Stage2Context`, `Stage3Context`, `Stage4Context` 어디에도 슬롯/배선 없음
  - Stage4 rejection 분류는 별도 정적 메서드 `stage4_interview_round.py:245` `_classify_reject_bucket()`를 사용하며 실제 호출도 `stage4_interview_round.py:3105`에 존재
- **테스트 caller**:
  - `tests/test_feedback_system.py`는 `FeedbackSystem.classify_rejection_feedback()` 직접 검증
  - `tests/test_state_service.py:230-236`은 `StateService.classify_rejection_feedback()` 직접 검증
  - `main_a._classify_rejection_feedback()` 자체를 호출하는 테스트는 없음
- **상태**: production facade 기준 dormant. 실제 분류 로직은 살아 있으나 `main_a` helper는 downstream에서 소비되지 않음

### 1.2 `_audit_event()` — **LIVE (단, Stage4 consumer surface 일부 미배선)**

- **정의**: `main_a.py:2831-2833` → thin delegate → `AuditService.audit_event()`
- **production caller**:
  - `main_a.py` 내부에서 10+ 직접 호출
  - `modules/core/prompt_builder.py:574,586-587` — `self._app._audit_event()` 직접 참조
  - `modules/core/stage01_helpers.py:210,701,763,780` — `app._audit_event()` 직접 참조
  - `modules/core/stage2_context.py:338` / `modules/core/stage3_context.py:118` — `audit_event` 콜백 슬롯으로 포획
  - `modules/core/stage3_orchestrator.py:719-720,739-740,1486-1496,1509-1526,1942-1943` — `ctx.audit_event()` 경유
  - `modules/core/stage4_orchestrator.py:1594-1599` — success path에서 `getattr(self.app, "_audit_event", None)` 직접 참조
- **Stage4 consumer split**:
  - `modules/core/stage4_post_processor.py:38-51`는 `getattr(self.ctx, "audit_event", None)`를 soft-failure relay에 사용
  - 같은 파일 `815-816`, `840-841`, `1023-1024`는 `manager_parse_failure`, `manager_complete_failure`, `episode_bible_save_failed`를 `self.ctx.audit_event(...)`로 남기려 함
  - 그러나 `modules/core/stage4_context.py:72-79`의 콜백 슬롯 목록과 `191-197`의 `from_app()` 배선에는 `audit_event`가 없음
- **테스트**:
  - `tests/test_stage4_orchestrator.py:134-144`는 `mock_app._audit_event = MagicMock()`로 app 직접 참조만 검증
  - `tests/test_stage4_post_processor.py:858,918`는 `ctx.audit_event = MagicMock()`를 수동 주입해 테스트함
- **상태**: helper 자체는 명백히 live. 다만 real `Stage4Context.from_app()` 경로에서는 post-processor의 `ctx.audit_event` 소비면이 잠겨 있어 Stage4 일부 audit trail이 비활성

### 1.3 `_flush_audit_buffer()` — **LIVE**

- **정의**: `main_a.py:2835-2837` → thin delegate → `AuditService.flush_audit_buffer()`
- **production caller**:
  - `main_a.py:301` — `atexit.register(self._flush_audit_buffer)`
  - `main_a.py:888` — `_emergency_shutdown()` 내부 호출
  - `modules/core/stage4_context.py:76,197` — `flush_audit_buffer` 콜백 슬롯으로 포획
  - `modules/core/stage4_orchestrator.py:1607-1608,1616-1617` — interrupt / exceptional path에서 `self.ctx.flush_audit_buffer()`
  - `scripts/run_stage4_canary.py:97-98` — canary 종료 시 호출
- **테스트**: `tests/test_run_stage4_canary.py:28`, `tests/test_stage4_context.py:158-184,268-272`, `tests/test_main_a_stage_entry_contracts.py:60`
- **상태**: live. 종료 hook, emergency path, canary, Stage4 exceptional path가 모두 연결됨

### 1.4 `_write_audit_summary()` — **LIVE (Stage4는 app 직접 참조)**

- **정의**: `main_a.py:2839-2841` → thin delegate → `AuditService.write_audit_summary(tag)`
- **production caller**:
  - `modules/core/stage3_orchestrator.py:600-601` — `ctx.write_audit_summary("stage3_complete")`
  - `modules/core/stage2_context.py:341` / `modules/core/stage3_context.py:119` — Stage2/3에서는 콜백 슬롯 정상 포획
  - `modules/core/stage4_orchestrator.py:1601-1604` — Stage4 success path는 `getattr(self.app, "_write_audit_summary", None)` 직접 참조
  - `modules/core/stage4_context.py:72-79,191-197` — Stage4Context에는 `write_audit_summary` 슬롯/배선 없음
- **테스트**: `tests/test_stage4_orchestrator.py:135-167,182-216`, `tests/test_stage3_orchestrator.py:906-917,1003`
- **상태**: live. 단 Stage4는 DI context가 아니라 `self.app`에 직접 결합

### 1.5 `_get_arc_context_for_episode()` — **LIVE**

- **정의**: `main_a.py:2843-2890` — `self.current_project.arcs`를 순회해 episode별 `arc_idx`, `arc_data`를 찾아 반환하는 실제 로직 보유
- **production caller**:
  - `modules/core/stage3_context.py:120` — `get_arc_context_for_episode` 콜백 슬롯으로 포획
  - `modules/core/stage3_orchestrator.py:728-729` — `ctx.get_arc_context_for_episode(working_ep)` 호출
- **테스트**:
  - `tests/test_stage3_orchestrator.py:67,709,1004`는 `app_mock._get_arc_context_for_episode`를 주입
  - `tests/e2e/test_l3_stage3_smoke.py:125,133`도 테스트 파일 내부 stub를 `MagicMock(side_effect=...)`로 바인딩
- **상태**: live. Stage3에서 정상 소비되지만 real `main_a` facade의 arc 순회 semantics를 잠그는 테스트는 얇음

### 1.6 `_validate_arc_data_fields()` — **LIVE (Stage3 only, Stage2 dormant)**

- **정의**: `main_a.py:2892-2902` → thin delegate → `StateService.validate_arc_data_fields()`
- **production caller**:
  - `modules/core/stage3_context.py:124` — 콜백 슬롯 정상 포획
  - `modules/core/stage3_orchestrator.py:745-746` — `ctx.validate_arc_data_fields(arc_data, arc_idx)` 호출
  - `modules/core/stage2_finalizer.py:905-906` — Stage2에서도 호출을 시도
  - 그러나 `modules/core/stage2_context.py`에는 `validate_arc_data_fields` 슬롯이 없어서 Stage2는 `getattr(..., None)` 가드로 skip
- **테스트**:
  - `tests/test_stage3_orchestrator.py:70,1008` — Stage3 mock callback 경유
  - `tests/test_stage2_finalizer.py:266` — mock ctx에 직접 바인딩
  - `tests/test_state_service.py:245-283` — service 레벨 직접 검증
- **상태**: Stage3 live, Stage2 dormant. production dormant 표면은 기존 P1 finding과 동일

### 1.7 `_validate_blueprint_integrity()` — **LIVE**

- **정의**: `main_a.py:2904-2905` → thin delegate → `StateService.validate_blueprint_integrity()`
- **production caller**:
  - `modules/core/stage3_context.py:125` — 콜백 슬롯 포획
  - `modules/core/stage3_orchestrator.py:1493-1496` — blueprint integrity check 실패 시 audit까지 연결
- **테스트**:
  - `tests/test_stage3_orchestrator.py:71,862,1009` — Stage3 mock callback 경유
  - `tests/e2e/test_l3_stage3_smoke.py:135` — stub 주입
  - `tests/test_state_service.py:347-357` — service 레벨 직접 검증
- **상태**: live. Stage3에서 정상 소비되지만 real `main_a` facade contract test는 별도 부재

### 1.8 `_build_item_acquisition_timeline()` — **LIVE**

- **정의**: `main_a.py:2763-2765` → thin delegate → `PromptBuilder.build_item_acquisition_timeline()`
- **production caller**:
  - `modules/core/stage4_context.py:72-79,191-197` — Stage4Context callback으로 포획
  - `modules/core/stage4_context_builder.py:1864` — `self.ctx.build_item_acquisition_timeline(next_ep - 1)` 호출
- **테스트**:
  - `tests/test_stage4_context.py:167-178` — `from_app()` wiring 검증
  - `tests/test_main_a_stage_entry_contracts.py:56` — Stage4 wrapper가 context를 세우는 엔트리 계약 확인
  - `tests/test_prompt_builder.py:383-420,471` — `PromptBuilder.build_item_acquisition_timeline()` 직접 검증
- **상태**: live. 다만 real `main_a._build_item_acquisition_timeline()` facade 자체의 의미 검증은 없음

---

## 2. 확정 Findings

### MDH-T2-001

| 필드 | 내용 |
|------|------|
| **ID** | MDH-T2-001 |
| **Severity** | P2 |
| **현상 요약** | `_classify_rejection_feedback()`는 production caller가 0건이다. delegation chain은 존재하지만 Stage2/3/4 Context 어디에도 바인딩되지 않으며 orchestrator, interview round, post-processor 어디에서도 호출되지 않는다. |
| **코드 근거** | `main_a.py:2825-2829` 정의. `modules/core/stage4_interview_round.py:245,3105`는 별도 `_classify_reject_bucket()`를 사용. `stage2_context.py`, `stage3_context.py`, `stage4_context.py` 어디에도 해당 helper 배선 없음. |
| **downstream 영향 경계** | dormant facade이므로 제거해도 현재 production path 영향은 없다. 단 `FeedbackSystem.classify_rejection_feedback()` 자체는 살아 있으므로 설계 의도 재확인이 필요하다. |
| **테스트 근거** | `tests/test_feedback_system.py`와 `tests/test_state_service.py:230-236`는 하위 구현만 검증한다. `main_a._classify_rejection_feedback()` 경유 테스트는 없다. |
| **기존 문서 중복 여부** | `related-but-new-live-consumer-surface` — OPUS 초안은 coverage gap 수준에 머물렀고, 본 재감리에서 dormant facade로 확정했다. |
| **권장 후속 조치** | Stage4 rejection 분류가 이 helper를 의도적으로 폐기한 것인지 확인하고, 사용 의도가 없다면 `main_a` facade 제거 후보로 분류. |

### MDH-T2-002

| 필드 | 내용 |
|------|------|
| **ID** | MDH-T2-002 |
| **Severity** | P2 |
| **현상 요약** | `_write_audit_summary()`와 `_audit_event()`가 Stage4 success path에서 DI context를 우회하고 `self.app` 직접 참조로 호출된다. Stage2/3은 context callback을 쓰지만 Stage4만 `getattr(self.app, ...)` 패턴이다. |
| **코드 근거** | `modules/core/stage4_orchestrator.py:1594-1604` — `_audit_event`, `_write_audit_summary`를 `self.app`에서 직접 lookup. `modules/core/stage4_context.py:72-79,191-197`에는 두 callback이 없다. 반면 `stage2_context.py:338,341`, `stage3_context.py:118-119`는 정상 포획한다. |
| **downstream 영향 경계** | production 동작은 유지되지만, Stage4만 `app` 실체에 직접 결합돼 context-only unit test 또는 wiring consistency가 깨진다. |
| **테스트 근거** | `tests/test_stage4_orchestrator.py:134-144`는 `mock_app._audit_event`, `mock_app._write_audit_summary`를 직접 심어 통과한다. |
| **기존 문서 중복 여부** | `already-covered-do-not-reopen` — `MFS-T3-02`와 동일 현상. 본 문서에서는 live consumer inventory 관점으로 재확인만 수행한다. |
| **권장 후속 조치** | `MFS-T3-02` remediation과 함께 Stage4도 context callback 기반으로 정렬. |

### MDH-T2-003

| 필드 | 내용 |
|------|------|
| **ID** | MDH-T2-003 |
| **Severity** | P1 |
| **현상 요약** | `_validate_arc_data_fields()`가 Stage2Finalizer에서 호출되지만 Stage2Context에 슬롯이 없어 real Stage2에서는 dormant다. 같은 helper는 Stage3에서만 live이다. |
| **코드 근거** | `modules/core/stage2_finalizer.py:905-906` — `self.ctx.validate_arc_data_fields(...)` 호출 시도. 그러나 `modules/core/stage2_context.py`에는 해당 슬롯/배선이 없다. Stage3 쪽은 `stage3_context.py:124`, `stage3_orchestrator.py:745-746`로 정상 연결된다. |
| **downstream 영향 경계** | Stage2 repair path가 건너뛰어져 malformed `arc_data`가 Stage3에 그대로 전달될 수 있다. Stage3에서 일부 방어가 남아 있어도 Stage2 단계의 사전 repair 보장은 깨진다. |
| **테스트 근거** | `tests/test_stage2_finalizer.py:266`은 mock ctx에 직접 콜백을 심어 초록이다. `tests/test_state_service.py:245-283`는 service 구현만 검증한다. |
| **기존 문서 중복 여부** | `already-covered-do-not-reopen` — `MFS-T2-001`의 same-root finding. 본 문서는 severity를 원 finding과 동일하게 P1로 맞춘다. |
| **권장 후속 조치** | `MFS-T2-001` remediation대로 `Stage2Context`에 `validate_arc_data_fields` 슬롯/배선을 추가. |

### MDH-T2-004

| 필드 | 내용 |
|------|------|
| **ID** | MDH-T2-004 |
| **Severity** | P2 |
| **현상 요약** | `_audit_event()`는 전체적으로 live이지만, `Stage4PostProcessor`가 기대하는 `ctx.audit_event` 소비면은 real `Stage4Context.from_app()`에서 미배선이다. 그 결과 Stage4 일부 soft-failure / post-processing audit event가 구조화 audit trail에 남지 않는다. |
| **코드 근거** | `modules/core/stage4_post_processor.py:38-51` — `_report_soft_failure()`가 `ctx.audit_event`를 조회. 동일 파일 `815-816`, `840-841`, `1023-1024`는 `self.ctx.audit_event(...)` 호출 시도. 그러나 `modules/core/stage4_context.py:72-79,191-197`에는 `audit_event` 슬롯/배선이 없다. `main_a.py:2831-2833`에는 실제 helper가 존재한다. |
| **downstream 영향 경계** | `manager_parse_failure`, `manager_complete_failure`, `episode_bible_save_failed` 3종 이벤트가 Stage4 audit 로그에 구조화 형태로 남지 않는다. 일반 logger 출력은 남아도 audit trail은 비게 된다. |
| **테스트 근거** | `tests/test_stage4_post_processor.py:858,918`는 `ctx.audit_event = MagicMock()`를 수동 주입해 통과한다. real `Stage4Context.from_app(app)` 통합 검증은 없다. |
| **기존 문서 중복 여부** | `already-covered-do-not-reopen` — `MLW-T3-002`와 동일 현상. 본 문서에서는 `_audit_event` helper의 live surface inventory에 편입했다. |
| **권장 후속 조치** | `MLW-T3-002` remediation대로 `Stage4Context`에 `audit_event` 슬롯/배선을 추가. |

---

## 3. Liveness Ledger 요약

| Helper | 상태 | Stage2 | Stage3 | Stage4 | main_a 내부 |
|--------|------|--------|--------|--------|-------------|
| `_classify_rejection_feedback()` | **dormant** | - | - | - | - |
| `_audit_event()` | **live + partial gap** | ctx 경유 | ctx 경유 | orchestrator는 app 직접 / post-processor ctx 미배선 | 10+ 직접 |
| `_flush_audit_buffer()` | **live** | - | - | ctx 경유 | atexit + emergency |
| `_write_audit_summary()` | **live** | ctx 경유 | ctx 경유 | app 직접 | - |
| `_get_arc_context_for_episode()` | **live** | - | ctx 경유 | - | - |
| `_validate_arc_data_fields()` | **partial** | dormant | ctx 경유 | - | - |
| `_validate_blueprint_integrity()` | **live** | - | ctx 경유 | - | - |
| `_build_item_acquisition_timeline()` | **live** | - | - | ctx 경유 | - |

---

## 4. PASS1 → PASS2 → PASS3 요약

### PASS 1 — 표면 수집

- helper 8건 전량 수집 완료
- dormant 후보:
  - `_classify_rejection_feedback()`
  - `_validate_arc_data_fields()`의 Stage2 소비면
- live helper 중 consumer split 후보:
  - `_audit_event()`의 Stage4 post-processor 미배선
  - `_write_audit_summary()` / `_audit_event()`의 Stage4 success path app 직접 참조
- 나머지 `_flush_audit_buffer()`, `_get_arc_context_for_episode()`, `_validate_blueprint_integrity()`, `_build_item_acquisition_timeline()`는 production caller 확인으로 live 우세

### PASS 2 — 교차 검증

- `_classify_rejection_feedback()`:
  - 전역 검색에서 production caller 0건 재확인
  - Stage4 rejection 경로가 별도 `_classify_reject_bucket()`를 사용함을 확인
  - **신규 dormant facade 확정**
- `_validate_arc_data_fields()` Stage2 dormant:
  - `MFS-T2-001`과 동일 현상
  - **already-covered**
- Stage4 success path의 `_audit_event()` / `_write_audit_summary()` app 직접 참조:
  - `MFS-T3-02`와 동일 현상
  - **already-covered**
- `_audit_event()` Stage4 post-processor 미배선:
  - `MLW-T3-002`와 동일 현상
  - OPUS 초안에는 누락돼 있었음
  - **already-covered but T2 문서 보강 필요**

### PASS 3 — 최종 확정

| Finding | PASS1 상태 | PASS2 결과 | PASS3 확정 |
|---------|-----------|-----------|-----------|
| MDH-T2-001 (`_classify_rejection_feedback` dormant) | HIGH 후보 | 전역 검색 + Stage4 대체 경로 확인 | **P2 확정** (신규) |
| MDH-T2-002 (Stage4 success path audit callback app 직접 참조) | HIGH 후보 | `MFS-T3-02`와 동일 | **P2 확정** (already-covered) |
| MDH-T2-003 (`_validate_arc_data_fields` Stage2 dormant) | HIGH 후보 | `MFS-T2-001`와 동일 | **P1 확정** (already-covered) |
| MDH-T2-004 (`_audit_event` Stage4 post-processor 미배선) | HIGH 후보 | `MLW-T3-002`와 동일 | **P2 확정** (already-covered) |

- 미확정 / open question: 없음
- 오탐 제거: 없음

---

## 5. 테스트 Coverage Gap

조사 coverage 자체는 없음. 다만 regression 방어 관점의 테스트 공백은 남아 있다.

1. **`_get_arc_context_for_episode()` real facade semantics 미검증**
   - 현재 증거는 `tests/test_stage3_orchestrator.py:67,709,1004`, `tests/e2e/test_l3_stage3_smoke.py:125,133`처럼 mock/stub 주입 위주다.
   - `main_a.py:2843-2890`의 실제 arc 순회, `ep_start/ep_end` 계산, fallback 분기 자체를 잠그는 테스트가 없다.

2. **`_build_item_acquisition_timeline()` facade contract 미검증**
   - `tests/test_stage4_context.py:167-178`은 `from_app()` wiring만 검증한다.
   - `tests/test_prompt_builder.py:383-420,471`은 `PromptBuilder` 구현만 검증한다.
   - `main_a._build_item_acquisition_timeline()` bound method 이름 drift나 delegate 교체는 직접 잡지 못한다.

3. **`_validate_arc_data_fields()` / `_validate_blueprint_integrity()`는 service-level test가 중심**
   - `tests/test_state_service.py:245-283,347-357`은 하위 구현을 잘 검증한다.
   - 하지만 `Stage3Context.from_app(real app)`가 실제 `main_a` bound method를 물고 `Stage3Orchestrator`까지 흘러가는 facade contract는 mock 주입에 의존한다.

4. **Stage4 `audit_event` wiring gap을 숨기는 테스트 구조**
   - `tests/test_stage4_post_processor.py:858,918`가 `ctx.audit_event = MagicMock()`를 수동 주입한다.
   - real `Stage4Context.from_app(app)` 기반 테스트가 없어서 `MDH-T2-004` 같은 미배선이 쉽게 숨는다.
