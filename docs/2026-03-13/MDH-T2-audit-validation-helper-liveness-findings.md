# MDH-T2: Audit / Validation Helper Liveness Findings

> 작성일: 2026-03-13
> 작성자: Claude Opus
> 트랙: `main_a.py` dormant helper / live consumer inventory — Terminal 2
> 상태: `PASS3 확정`
> 초점: audit, validation, arc context helper의 live consumer 여부

---

## 0. 조사 대상 helper 목록

| # | Helper | 정의 위치 |
|---|--------|-----------|
| 1 | `_classify_rejection_feedback()` | `main_a.py:2780` |
| 2 | `_audit_event()` | `main_a.py:2786` |
| 3 | `_flush_audit_buffer()` | `main_a.py:2790` |
| 4 | `_write_audit_summary()` | `main_a.py:2794` |
| 5 | `_get_arc_context_for_episode()` | `main_a.py:2798` |
| 6 | `_validate_arc_data_fields()` | `main_a.py:2847` |
| 7 | `_validate_blueprint_integrity()` | `main_a.py:2859` |
| 8 | `_build_item_acquisition_timeline()` | `main_a.py:2718` |

---

## 1. Helper별 Liveness 판정

### 1.1 `_classify_rejection_feedback()` — **DORMANT**

- **정의**: `main_a.py:2780` → thin delegate → `StateService.classify_rejection_feedback()` → `FeedbackSystem.classify_rejection_feedback()`
- **production caller 검색 결과**: **0건**
  - `modules/` 전역에서 `_classify_rejection_feedback` 호출 0건
  - Stage2/3/4 Context에 바인딩 없음 (Stage2Context, Stage3Context, Stage4Context 모두 슬롯 없음)
  - `stage4_interview_round.py`에서 호출 없음
- **테스트 caller**: `tests/test_feedback_system.py` (FeedbackSystem 직접 호출), `tests/test_state_service.py` (StateService 직접 호출). `main_a._classify_rejection_feedback` 자체를 호출하는 테스트 0건
- **기존 문서 근거**: `MFS-T3` 문서가 "T3 직접 downstream에서 사용처를 찾지 못해 coverage gap으로 이관"으로 기록

### 1.2 `_audit_event()` — **LIVE**

- **정의**: `main_a.py:2786` → thin delegate → `AuditService.audit_event()`
- **production caller**:
  - `main_a.py` 내부: 10+ 직접 호출 (L402, L406, L429, L886, L944, L956, L1266, L1278, L1465, L2827, L2834, L2840)
  - `modules/core/prompt_builder.py:574,586-587` — `self._app._audit_event()` 직접 참조
  - `modules/core/stage01_helpers.py:210,701,763,780` — `app._audit_event()` 직접 참조
  - `modules/core/services/state_service.py` — 생성자에서 `audit_event_fn` 주입, 14+ 내부 호출
  - DI Context: `Stage2Context`(L236), `Stage3Context`(L118) → `audit_event` 콜백 슬롯으로 포획
  - `stage2_orchestrator.py:331,382,387,404,451` — `self.ctx.audit_event()` 경유
  - `stage4_orchestrator.py:1530` — `getattr(self.app, "_audit_event")` 직접 참조 (DI 우회)
  - `validation_orchestrator.py:289` — `validation_context.get("_audit_event")` 동적 조회
- **상태**: 완전히 live. 가장 많은 consumer를 가진 helper

### 1.3 `_flush_audit_buffer()` — **LIVE**

- **정의**: `main_a.py:2790` → thin delegate → `AuditService.flush_audit_buffer()`
- **production caller**:
  - `main_a.py:301` — `atexit.register(self._flush_audit_buffer)` (프로세스 종료 hook)
  - `main_a.py:888` — `_emergency_shutdown()` 내부 호출
  - `modules/core/stage4_context.py:176` — `flush_audit_buffer` 콜백 슬롯으로 `Stage4Context.from_app()`에서 포획
  - `stage4_orchestrator.py:1543` — `self.ctx.flush_audit_buffer()` (KeyboardInterrupt path)
  - `scripts/run_stage4_canary.py:97-98` — canary 종료 시 호출
- **테스트**: `tests/test_run_stage4_canary.py:28`, `tests/test_stage4_context.py:178`, `tests/test_main_a_stage_entry_contracts.py:60`
- **상태**: 완전히 live. atexit + emergency + canary + Stage4 interrupt 4개 경로

### 1.4 `_write_audit_summary()` — **LIVE (source 분리 주의)**

- **정의**: `main_a.py:2794` → thin delegate → `AuditService.write_audit_summary(tag)`
- **production caller**:
  - `stage4_orchestrator.py:1537` — `getattr(self.app, "_write_audit_summary")` 직접 참조 (success path, DI 우회)
  - `stage3_orchestrator.py:600-601` — `ctx.write_audit_summary("stage3_complete")` (DI 경유)
  - `stage2_orchestrator.py:891-892` — `self.ctx.write_audit_summary("stage2_complete")` (DI 경유)
  - DI Context: `Stage2Context`(L239), `Stage3Context`(L119) → `write_audit_summary` 콜백 포획
  - **Stage4Context에는 미포획** — Stage4 success path는 `self.app` 직접 참조
- **테스트**: `tests/test_stage4_orchestrator.py` (5+ 검증), `tests/test_stage3_orchestrator.py:906,917,1003`
- **기존 문서**: `MFS-T3-02`가 "Stage4 completion callback이 DI context를 우회하고 self.app에만 결합" finding 확정
- **상태**: live. 단 Stage4는 DI 경유가 아닌 `self.app` 직접 참조 (MFS-T3-02에서 이미 커버됨)

### 1.5 `_get_arc_context_for_episode()` — **LIVE**

- **정의**: `main_a.py:2798` — 실제 로직 보유 (thin delegate 아님). `self.current_project.arcs`를 순회하여 ep_num에 해당하는 arc_idx, arc_data 반환
- **production caller**:
  - `modules/core/stage3_context.py:120` — `get_arc_context_for_episode` 콜백 슬롯으로 포획
  - `modules/core/stage3_orchestrator.py:745` — `ctx.validate_arc_data_fields(arc_data, arc_idx)` 직전에 `ctx.get_arc_context_for_episode()` 호출 (간접 확인 필요)
- **실제 Stage3 호출 확인**: Stage3Orchestrator에서 `ctx.get_arc_context_for_episode(working_ep)` 호출 (project_full_source.md:2967 확인)
- **테스트**: `tests/test_stage3_orchestrator.py:67,709,1004`, `tests/e2e/test_l3_stage3_smoke.py:125,133`
- **상태**: live. Stage3에서 DI 경유로 정상 소비

### 1.6 `_validate_arc_data_fields()` — **LIVE (Stage3 only, Stage2 dormant)**

- **정의**: `main_a.py:2847` → thin delegate → `StateService.validate_arc_data_fields()`
- **production caller**:
  - `modules/core/stage3_context.py:124` — `validate_arc_data_fields` 콜백 슬롯으로 포획
  - `modules/core/stage3_orchestrator.py:745-746` — `ctx.validate_arc_data_fields(arc_data, arc_idx)` 호출
  - `modules/core/stage2_finalizer.py:905-906` — `self.ctx.validate_arc_data_fields(refined_arc, global_arc_no)` 호출
  - **그러나** `Stage2Context`에는 `validate_arc_data_fields` 슬롯이 없음 → Stage2Finalizer의 이 코드는 `getattr(self.ctx, "validate_arc_data_fields", None)` 가드로 보호돼 있으므로 **Stage2에서는 dormant**
- **기존 문서**: `MFS-T2-001`이 "Stage2 context에 바인딩되지 않아 production Stage2 repair path가 죽어 있다" (P1) 확정
- **테스트**: `tests/test_stage3_orchestrator.py:70,1008`, `tests/test_stage2_finalizer.py:265`
- **상태**: Stage3 live, Stage2 dormant (MFS-T2-001에서 이미 커버)

### 1.7 `_validate_blueprint_integrity()` — **LIVE**

- **정의**: `main_a.py:2859` → thin delegate → `StateService.validate_blueprint_integrity()`
- **production caller**:
  - `modules/core/stage3_context.py:125` — `validate_blueprint_integrity` 콜백 슬롯으로 포획
  - `modules/core/stage3_orchestrator.py:1493` — `ctx.validate_blueprint_integrity(blueprint)` 호출
- **테스트**: `tests/test_stage3_orchestrator.py:71,862,1009`, `tests/e2e/test_l3_stage3_smoke.py:135`
- **상태**: live. Stage3에서 DI 경유로 정상 소비

### 1.8 `_build_item_acquisition_timeline()` — **LIVE**

- **정의**: `main_a.py:2718` → thin delegate → `PromptBuilder.build_item_acquisition_timeline()`
- **production caller**:
  - `modules/core/stage4_context.py:57,96,126,172` — `build_item_acquisition_timeline` 콜백 슬롯으로 포획
  - `modules/core/stage4_context_builder.py:1863` — `self.ctx.build_item_acquisition_timeline(next_ep - 1)` 호출
- **테스트**: `tests/test_stage4_context.py:165,174`, `tests/test_main_a_stage_entry_contracts.py:56`, `tests/test_prompt_builder.py:471`
- **상태**: live. Stage4에서 DI 경유로 정상 소비

---

## 2. 확정 Findings

### MDH-T2-001

| 필드 | 내용 |
|------|------|
| **ID** | MDH-T2-001 |
| **Severity** | P2 |
| **현상 요약** | `_classify_rejection_feedback()`는 production caller가 0건이다. `main_a.py`에서 정의되어 있고 `StateService` → `FeedbackSystem`까지 delegation chain이 존재하지만, Stage2/3/4 Context 어디에도 바인딩되지 않으며, stage orchestrator, interview round 등 어디에서도 호출하지 않는다. |
| **코드 근거** | `main_a.py:2780-2784` 정의. `modules/core/stage2_context.py`, `stage3_context.py`, `stage4_context.py` 모두 `classify_rejection_feedback` 슬롯 없음. `modules/` 전역 grep에서 `_classify_rejection_feedback` 호출 0건 |
| **downstream 영향 경계** | 없음. dormant facade이므로 제거해도 production path에 영향 없음. `FeedbackSystem.classify_rejection_feedback()` 자체는 테스트에서 직접 호출되므로 실구현은 살아있음 |
| **테스트 근거** | `tests/test_feedback_system.py:516-553` (FeedbackSystem 직접), `tests/test_state_service.py:230-236` (StateService 직접). `main_a._classify_rejection_feedback` 경유 테스트 0건 |
| **기존 문서 중복 여부** | `related-but-new-live-consumer-surface` — `MFS-T3` 문서가 coverage gap으로 이관했으나 dormant 확정까지는 하지 않았음. 본 finding이 dormant 확정을 처음으로 잠금 |
| **권장 후속 조치** | Stage4 interview round의 rejection feedback classification이 이 helper를 의도적으로 사용해야 하는지 확인. 사용 의도가 없다면 facade 제거 후보 |

### MDH-T2-002

| 필드 | 내용 |
|------|------|
| **ID** | MDH-T2-002 |
| **Severity** | P2 |
| **현상 요약** | `_write_audit_summary()`와 `_audit_event()`가 Stage4 success path에서 DI context를 우회하고 `self.app` 직접 참조로 호출된다. Stage4Context에는 `write_audit_summary` 슬롯이 없고, `_audit_event`도 Stage4Context에 미포획이다. Stage2/3은 DI 경유, Stage4만 `getattr(self.app, ...)` 패턴 |
| **코드 근거** | `stage4_orchestrator.py:1530-1539` — `getattr(self.app, "_audit_event", None)`, `getattr(self.app, "_write_audit_summary", None)`. `stage4_context.py` 슬롯에 `audit_event`, `write_audit_summary` 없음. 반면 `stage2_context.py:236,239`, `stage3_context.py:118,119`는 정상 포획 |
| **downstream 영향 경계** | production 동작은 정상 (self.app에서 resolve됨). 그러나 DI 일관성이 깨져 Stage4를 app 없이 단위 테스트하려면 mock_app에 직접 바인딩 필요 |
| **테스트 근거** | `tests/test_stage4_orchestrator.py:134,143` — `mock_app._write_audit_summary` 직접 pinning으로 테스트 통과 |
| **기존 문서 중복 여부** | `already-covered-do-not-reopen` — `MFS-T3-02`에서 동일 현상 P2 confirmed. 본 finding은 live consumer inventory 관점에서 재확인만 수행 |
| **권장 후속 조치** | `MFS-T3-02` remediation에서 일괄 처리 |

### MDH-T2-003

| 필드 | 내용 |
|------|------|
| **ID** | MDH-T2-003 |
| **Severity** | P2 |
| **현상 요약** | `_validate_arc_data_fields()`가 Stage2Finalizer에서 호출되지만 Stage2Context에 슬롯이 없어 production Stage2에서 dormant. Stage3에서만 live |
| **코드 근거** | `stage2_finalizer.py:905-906` — `self.ctx.validate_arc_data_fields(refined_arc, global_arc_no)` 호출 but `stage2_context.py`에 해당 슬롯 미정의. `callable(getattr(self.ctx, "validate_arc_data_fields", None))` 가드로 None 반환 시 skip |
| **downstream 영향 경계** | Stage2 repair path가 실행되지 않아 malformed arc_data가 Stage3에 그대로 전달될 수 있음. Stage3에서 같은 helper가 live이므로 이중 방어가 일부 작동하지만 Stage2 단계 repair는 누락 |
| **테스트 근거** | `tests/test_stage2_finalizer.py:265` — 테스트는 mock ctx에 직접 바인딩하므로 통과 |
| **기존 문서 중복 여부** | `already-covered-do-not-reopen` — `MFS-T2-001` (P1)에서 동일 현상 확정 |
| **권장 후속 조치** | `MFS-T2-001` remediation에서 Stage2Context 슬롯 추가로 일괄 해결 |

---

## 3. Liveness Ledger 요약

| Helper | 상태 | Stage2 | Stage3 | Stage4 | main_a 내부 |
|--------|------|--------|--------|--------|-------------|
| `_classify_rejection_feedback()` | **dormant** | - | - | - | - |
| `_audit_event()` | **live** | ctx 경유 | ctx 경유 | app 직접 | 10+ 직접 |
| `_flush_audit_buffer()` | **live** | - | - | ctx 경유 | atexit + emergency |
| `_write_audit_summary()` | **live** | ctx 경유 | ctx 경유 | app 직접 | - |
| `_get_arc_context_for_episode()` | **live** | - | ctx 경유 | - | - |
| `_validate_arc_data_fields()` | **partial** | dormant | ctx 경유 | - | - |
| `_validate_blueprint_integrity()` | **live** | - | ctx 경유 | - | - |
| `_build_item_acquisition_timeline()` | **live** | - | - | ctx 경유 | - |

---

## 4. PASS1 → PASS2 → PASS3 요약

### PASS 1 — 표면 수집

후보 8건 전량 수집 완료:
- `_classify_rejection_feedback` → HIGH 확신 dormant 후보
- `_audit_event` → live 확정 (10+ caller)
- `_flush_audit_buffer` → live 확정 (atexit, emergency, canary, Stage4 interrupt)
- `_write_audit_summary` → live 확정 (Stage2/3/4 success path)
- `_get_arc_context_for_episode` → live 확정 (Stage3 DI)
- `_validate_arc_data_fields` → MED 확신 partial dormant 후보 (Stage2 미바인딩)
- `_validate_blueprint_integrity` → live 확정 (Stage3 DI)
- `_build_item_acquisition_timeline` → live 확정 (Stage4 DI)

### PASS 2 — 교차 검증

- `_classify_rejection_feedback`: 전역 grep에서 production caller 0건 재확인. `FeedbackSystem.classify_rejection_feedback()`은 직접 호출 가능하므로 facade만 dormant. `MFS-T3` 문서 coverage gap 이관 기록과 일치 → **dormant 확정**
- `_validate_arc_data_fields` Stage2 dormant: `MFS-T2-001` (P1)에서 이미 확정된 동일 현상. 새 finding 아닌 재확인 → **already-covered**
- `_write_audit_summary` / `_audit_event` Stage4 DI 우회: `MFS-T3-02`에서 이미 확정. 재확인만 → **already-covered**

### PASS 3 — 최종 확정

| Finding | PASS1 상태 | PASS2 결과 | PASS3 확정 |
|---------|-----------|-----------|-----------|
| MDH-T2-001 (`_classify_rejection_feedback` dormant) | HIGH 후보 | 전역 grep 재확인, 0 production caller | **P2 확정** (신규) |
| MDH-T2-002 (Stage4 audit DI 우회) | 확인 | MFS-T3-02 동일 | **P2 확정** (already-covered) |
| MDH-T2-003 (`_validate_arc_data_fields` Stage2 dormant) | MED 후보 | MFS-T2-001 동일 | **P2 확정** (already-covered) |

- 미확정 / open question: 없음
- 오탐 제거: 없음 (PASS2에서 live helper 6건은 모두 production caller 확인으로 live 확정)

---

## 5. Coverage Gap

없음. T2 담당 범위 8개 helper 전량 조사 완료.
