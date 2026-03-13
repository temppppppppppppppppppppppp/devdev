# XC-DI: Protocol & 계약 준수 — 3-Pass 재감사 최종본

> Track: XC-DI
> 감사일: 2026-03-13
> 상태: PASS 3 완료 (오탐 제거, 최종 확정)

---

## PASS 3 오탐 제거 결과

### 제거된 항목: 0건
- PASS 1-2에서 식별된 14건 모두 코드 근거 확인됨. 오탐 없음.

### 심각도 조정

| ID | PASS 2 심각도 | PASS 3 심각도 | 사유 |
|----|--------------|--------------|------|
| XC-DI-001/006 | P3 | P3 유지 | `from_app()` 경로에서 항상 바인딩되므로 프로덕션 미발현. 테스트 전용 위험 |
| XC-DI-005 | P2 | P2 유지 | DI 패턴 일관성 위반이며, 테스트 고립성에 영향. Stage3 단독 테스트 시 app 의존 필수 |
| XC-DI-013 | P2 | P2 유지 | 패턴 불일치. Stage2/4와 동일 보호 수준 적용 권장 |
| 기타 12건 | P3 | P3 유지 | 코드 품질/일관성 이슈. 기능 영향 없음 |

### XC-DI-001과 XC-DI-006 통합

XC-DI-001 (T1)과 XC-DI-006 (T2)은 동일 현상 (Stage4 `get_int_input` None 가드). **XC-DI-001로 통합**, XC-DI-006은 중복 처리.

---

## 최종 Finding 목록 (13건, 중복 제거 후)

### P2 (2건)

#### [XC-DI-005] P2 | Stage3 `_init_*` DI 우회

| 필드 | 내용 |
|------|------|
| ID | XC-DI-005 |
| Severity | P2 |
| 현상 요약 | Stage3 orchestrator의 3개 초기화 메서드가 `self.app` 직접 접근으로 DI 컨텍스트 우회. ctx와 app 간 상태 불일치 및 테스트 고립성 저해 |
| 코드 근거 | `modules/core/stage3_orchestrator.py:630-690` — `app.state_tracker = StateTracker(...)` 등 3곳 |
| 영향 경계 | Stage3 단위 테스트에서 ctx-only 주입 불가. DI 패턴 일관성 위반 |
| 테스트 근거 | e2e에서 app mock으로 커버. 단위 테스트 ctx-only 경로 미커버 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | `_init_*` 로직을 ctx 기반으로 전환. 공수 1시간 |

#### [XC-DI-013] P2 | Stage3 `from_app()` 안전 접근 패턴 불일치

| 필드 | 내용 |
|------|------|
| ID | XC-DI-013 |
| Severity | P2 |
| 현상 요약 | Stage3Context.from_app()만 `getattr()` 사용. Stage2/4는 `_safe_getattr()` (inspect.getattr_static 선행) 사용 |
| 코드 근거 | `modules/core/stage3_context.py:108-127` vs `modules/core/stage4_context.py:186` |
| 영향 경계 | `__getattr__` 오버라이드 시 부작용 가능 (현재 미존재) |
| 테스트 근거 | 프로덕션 미발현 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | `_safe_getattr` 도입. 공수 15분 |

### P3 (11건)

#### [XC-DI-001] P3 | Stage4 `get_int_input` 2곳 None 가드 미적용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-001 |
| Severity | P3 |
| 현상 요약 | `stage4_orchestrator.py:1479`와 `:1535`에서 `get_int_input` None 가드 없이 직접 호출 |
| 코드 근거 | `modules/core/stage4_orchestrator.py:1479` `target_ep = self.ctx.get_int_input(...)` |
| 영향 경계 | from_app() 경로에서 미발현. 테스트 mock에서만 위험 |
| 기존 중복 여부 | XC-DI-006 통합 |
| 권장 후속 조치 | callable 가드 추가. 공수 5분 |

#### [XC-DI-002] P3 | Stage4 `write_audit_summary` Dormant 슬롯

| 필드 | 내용 |
|------|------|
| ID | XC-DI-002 |
| Severity | P3 |
| 현상 요약 | Stage4Context에 선언되었으나 Stage4 내 소비처 없음 |
| 코드 근거 | `modules/core/stage4_context.py:82` |
| 권장 후속 조치 | 향후 cleanup 시 제거 검토. 공수 무시 |

#### [XC-DI-003] P3 | Stage2 `retry_feedback_contract`/`missing_callbacks` Orphan

| 필드 | 내용 |
|------|------|
| ID | XC-DI-003 |
| Severity | P3 |
| 현상 요약 | 2개 슬롯 선언·할당되지만 소비처 0건 |
| 코드 근거 | `modules/core/stage2_context.py:188-189` |
| 권장 후속 조치 | 관측 코드 추가 또는 슬롯 제거. 공수 10분 |

#### [XC-DI-004] P3 | Stage3 `preset_registry` ctx 미참조

| 필드 | 내용 |
|------|------|
| ID | XC-DI-004 |
| Severity | P3 |
| 현상 요약 | ctx.preset_registry 미참조, app 직접 접근 |
| 코드 근거 | `modules/core/stage3_orchestrator.py:637` vs `modules/core/stage3_context.py:29` |
| 권장 후속 조치 | ctx 경유 전환. 공수 5분 |

#### [XC-DI-007] P3 | `build_item_acquisition_timeline` TypeError 묵인

| 필드 | 내용 |
|------|------|
| ID | XC-DI-007 |
| Severity | P3 |
| 현상 요약 | None 콜백 직접 호출 → TypeError → try-except 묵인 |
| 코드 근거 | `modules/core/stage4_context_builder.py:1864` |
| 권장 후속 조치 | callable 가드 추가. 공수 5분 |

#### [XC-DI-008] P3 | Stage2 콜백 섹션에 데이터 슬롯 혼재

| 필드 | 내용 |
|------|------|
| ID | XC-DI-008 |
| Severity | P3 |
| 현상 요약 | `cumulative_state_cache` 등 3개 데이터 슬롯이 콜백 섹션에 위치 |
| 코드 근거 | `modules/core/stage2_context.py:163-170` |
| 권장 후속 조치 | 섹션 주석 분리. 공수 5분 |

#### [XC-DI-009] P3 | `inspect.getattr_static` 불필요 사용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-009 |
| Severity | P3 |
| 현상 요약 | __slots__ 클래스에서 inspect.getattr_static 불필요 |
| 코드 근거 | `modules/core/stage4_interview_round.py:844`, `modules/core/stage4_context_builder.py:2514` |
| 권장 후속 조치 | callable(getattr(...)) 패턴으로 통일. 공수 5분 |

#### [XC-DI-010] P3 | Stage2 `generate_arc_context_v60` None 가드 미적용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-010 |
| Severity | P3 |
| 현상 요약 | 직접 호출. retry_feedback 체계 전부 실패 시 None 가능 |
| 코드 근거 | `modules/core/stage2_orchestrator.py:381` |
| 권장 후속 조치 | callable 가드 + fallback. 공수 10분 |

#### [XC-DI-011] P3 | 5개 Protocol `@runtime_checkable` 미활용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-011 |
| Severity | P3 |
| 현상 요약 | @runtime_checkable 선언, isinstance 검사 0건 |
| 코드 근거 | `modules/protocols/app_services.py:20/45/75/120/219` |
| 권장 후속 조치 | Phase 4B에서 활용 또는 제거. 공수 5분 |

#### [XC-DI-012] P3 | DI Context __init__ Protocol 타입힌트 미적용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-012 |
| Severity | P3 |
| 현상 요약 | Context 클래스 __init__에 Protocol 타입힌트 없음 |
| 코드 근거 | `modules/core/stage4_context.py:90-130` 등 3개 Context 전부 |
| 권장 후속 조치 | Phase 4B에서 타입힌트 추가. 공수 30분 |

#### [XC-DI-014] P3 | Protocol docstring 라인번호 drift

| 필드 | 내용 |
|------|------|
| ID | XC-DI-014 |
| Severity | P3 |
| 현상 요약 | Protocol docstring 라인번호가 코드 변경으로 불일치 가능 |
| 코드 근거 | `modules/protocols/app_services.py:25-28` |
| 권장 후속 조치 | 메서드명 참조로 변경. 공수 10분 |

---

## 총평

XC-DI 트랙에서 P0/P1 findings 없음. DI 전환이 전체적으로 잘 수행되었으며, 콜백 None 가드도 대부분 적절하게 적용됨.

주요 개선 포인트:
1. **Stage3 DI 일관성** (P2 2건): Stage3만 `_safe_getattr` 미사용 + `_init_*`에서 `self.app` 직접 접근. Stage2/4와 동일 수준으로 전환 권장
2. **콜백 가드 통일** (P3 다수): 일부 콜백에서 None 가드 패턴이 불일치. `callable(getattr(self.ctx, "name", None))` 패턴으로 일괄 통일 권장
3. **Protocol 활용도** (P3): 5개 Protocol이 정의되었으나 런타임 검사에 활용되지 않음. Phase 4B에서 DI 전환 완료 시 활성화 권장

총 공수 추정: P2 2건 (~1시간 15분) + P3 11건 (~1시간 30분) = **약 2시간 45분**
