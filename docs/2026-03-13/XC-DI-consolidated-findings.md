# XC-DI: Protocol & 계약 준수 — 통합 Findings (PASS 1-2)

> Track: XC-DI
> 감사일: 2026-03-13
> 상태: PASS 1-2 완료 (교차 검증까지)

---

## 요약 통계

| 심각도 | 건수 |
|--------|------|
| P0 (Critical) | 0 |
| P1 (High) | 0 |
| P2 (Medium) | 2 |
| P3 (Low/Info) | 12 |
| **합계** | **14** |

---

## P2 Findings

### [XC-DI-005] P2 | Stage3 `_init_*` 메서드가 ctx가 아닌 self.app 직접 접근 — DI 우회

| 필드 | 내용 |
|------|------|
| ID | XC-DI-005 |
| Severity | P2 |
| 현상 요약 | `stage3_orchestrator.py`의 `_init_state_tracker_if_needed()`, `_init_world_state_if_needed()`, `_init_fact_ledger_if_needed()` 3개 메서드가 `self.app`에 직접 속성을 할당하여 DI 컨텍스트를 우회 |
| 코드 근거 | `stage3_orchestrator.py:630-690` — `app.state_tracker = StateTracker(...)`, `app.world_state = WorldStateManager(...)`, `app.fact_ledger = FactLedger(...)`. 이후 `:511-513`에서 `ctx.state_tracker = getattr(self.app, "state_tracker", None)` 으로 ctx에 재주입 |
| 영향 경계 | (1) `self.app`이 None이거나 테스트 stub이면 AttributeError. (2) ctx와 app 간 상태 불일치 가능. (3) 테스트에서 ctx-only 주입 시 이 경로 미통과 |
| 테스트 근거 | e2e 테스트에서 `app` mock으로 커버. 단위 테스트에서 ctx-only 주입 시 미통과 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `_init_*` 로직을 ctx 기반으로 전환하거나, `from_app()` 시점에 lazy init 포함. 공수 1시간 |

### [XC-DI-013] P2 | Stage3Context.from_app()에서 `getattr` 사용 — `_safe_getattr` 미사용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-013 |
| Severity | P2 |
| 현상 요약 | `stage3_context.py:108-127`의 `from_app()`에서 `getattr(app, "xxx", None)` 사용. Stage2/4는 `_safe_getattr()`로 `inspect.getattr_static` 선행 검사를 수행하나 Stage3만 미적용 |
| 코드 근거 | `stage3_context.py:108` `state_tracker=getattr(app, "state_tracker", None)` vs `stage4_context.py:186` `state_tracker=_safe_getattr(app, "state_tracker", None)` |
| 영향 경계 | `app` 객체에 `__getattr__` 오버라이드가 있으면 부작용 발생 가능. 현재 SovereignApp에는 `__getattr__` 없으므로 실질 위험 낮음 |
| 테스트 근거 | 프로덕션에서 문제 미발현 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | Stage3Context에도 `_safe_getattr` 도입하여 패턴 통일. 공수 15분 |

---

## P3 Findings

### [XC-DI-001] P3 | Stage4 `get_int_input` 콜백 2곳 None 가드 미적용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-001 |
| Severity | P3 |
| 현상 요약 | `stage4_orchestrator.py:1479`와 `:1535`에서 `get_int_input` 콜백을 None 가드 없이 직접 호출 |
| 코드 근거 | `:1479` `target_ep = self.ctx.get_int_input(...)`. 동일 파일 `:1276`에서는 `callable(getattr(...))` 가드 사용 — 불일치 |
| 영향 경계 | `from_app()` 경로에서는 미발현. 테스트 mock 경로에서만 위험 |
| 테스트 근거 | 테스트에서 mock ctx 사용 시 `get_int_input` 바인딩 미확인 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `:1276` 패턴으로 통일. 공수 5분 |

### [XC-DI-002] P3 | Stage4 `write_audit_summary` 콜백 슬롯 Stage4 내 소비처 없음

| 필드 | 내용 |
|------|------|
| ID | XC-DI-002 |
| Severity | P3 |
| 현상 요약 | `Stage4Context`에 `write_audit_summary` 슬롯 선언되었으나 Stage4 내부에서 미소비 |
| 코드 근거 | `stage4_context.py:82` 슬롯 선언. Stage4 소비처 0건 |
| 영향 경계 | 슬롯 메모리 낭비만 존재 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | Protocol 통일 목적이면 유지. 아니면 제거. 공수 무시 |

### [XC-DI-003] P3 | Stage2 `retry_feedback_contract`/`retry_feedback_missing_callbacks` Orphan 슬롯

| 필드 | 내용 |
|------|------|
| ID | XC-DI-003 |
| Severity | P3 |
| 현상 요약 | 2개 슬롯이 선언·할당되지만 소비처 0건 |
| 코드 근거 | `stage2_context.py:188-189` 선언, 4개 소비처 파일 모두 참조 0건 |
| 영향 경계 | 기능 무관. Observability 목적 미완성 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | 관측 코드 추가 또는 슬롯 제거. 공수 10분 |

### [XC-DI-004] P3 | Stage3Context `preset_registry` ctx 미참조

| 필드 | 내용 |
|------|------|
| ID | XC-DI-004 |
| Severity | P3 |
| 현상 요약 | `ctx.preset_registry` 미참조. `app.preset_registry`로 직접 접근 |
| 코드 근거 | `stage3_context.py:29` 선언, `stage3_orchestrator.py:637` `app.preset_registry` 직접 접근 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `app.preset_registry` → `ctx.preset_registry` 전환. 공수 5분 |

### [XC-DI-007] P3 | `build_item_acquisition_timeline` TypeError 묵인

| 필드 | 내용 |
|------|------|
| ID | XC-DI-007 |
| Severity | P3 |
| 현상 요약 | None 콜백 직접 호출 시 TypeError가 상위 try-except로 묵인됨 |
| 코드 근거 | `stage4_context_builder.py:1864` |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `callable` 가드 추가. 공수 5분 |

### [XC-DI-008] P3 | Stage2 콜백 섹션에 데이터 슬롯 혼재

| 필드 | 내용 |
|------|------|
| ID | XC-DI-008 |
| Severity | P3 |
| 현상 요약 | `cumulative_state_cache`, `cumulative_state_cache_key`, `state_tracker_loaded_arcs` 가 콜백 섹션에 위치 |
| 코드 근거 | `stage2_context.py:163-170` |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | 섹션 주석 분리. 공수 5분 |

### [XC-DI-009] P3 | `inspect.getattr_static` 불필요 사용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-009 |
| Severity | P3 |
| 현상 요약 | `__slots__` 클래스에서 `inspect.getattr_static` 불필요 |
| 코드 근거 | `stage4_interview_round.py:844`, `stage4_context_builder.py:2514` |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `callable(getattr(...))` 패턴으로 통일. 공수 5분 |

### [XC-DI-010] P3 | Stage2 `generate_arc_context_v60` None 가드 미적용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-010 |
| Severity | P3 |
| 현상 요약 | `stage2_orchestrator.py:381` 직접 호출. retry_feedback 체계에서 해소되나 전부 실패 시 None 가능 |
| 코드 근거 | `stage2_orchestrator.py:381` |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | `callable` 가드 + fallback 추가. 공수 10분 |

### [XC-DI-011] P3 | 5개 Protocol `@runtime_checkable` 미활용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-011 |
| Severity | P3 |
| 현상 요약 | `@runtime_checkable` 선언되었으나 isinstance 검사 0건 |
| 코드 근거 | `app_services.py:20/45/75/120/219` |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | Phase 4B에서 활용 또는 제거. 공수 5분 |

### [XC-DI-012] P3 | DI Context __init__ Protocol 타입힌트 미적용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-012 |
| Severity | P3 |
| 현상 요약 | Context 클래스 __init__ 파라미터에 Protocol 타입힌트 없음 |
| 코드 근거 | `stage4_context.py:90-130` |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | Phase 4B에서 타입힌트 추가. 공수 30분 |

### [XC-DI-014] P3 | Protocol docstring 라인번호 drift

| 필드 | 내용 |
|------|------|
| ID | XC-DI-014 |
| Severity | P3 |
| 현상 요약 | docstring의 라인번호 참조가 코드 변경으로 불일치 가능 |
| 코드 근거 | `app_services.py:25-28` |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | 메서드명 참조로 변경. 공수 10분 |
