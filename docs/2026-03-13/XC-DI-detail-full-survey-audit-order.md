# XC-DI: Protocol & 계약 준수 — 전수조사 감사 명세

> Track: XC-DI
> 감사일: 2026-03-13
> 감사 범위: DI Context 슬롯 완전성, 콜백 타입 안전, Protocol 등록 갭

---

## 1. 감사 대상 파일

| 파일 | 역할 | 슬롯/메서드 수 |
|------|------|---------------|
| `modules/core/stage4_context.py` | Stage4 DI 컨텍스트 | 37 slots |
| `modules/core/stage2_context.py` | Stage2 DI 컨텍스트 | 47 slots |
| `modules/core/stage3_context.py` | Stage3 DI 컨텍스트 | 23 slots |
| `modules/protocols/app_services.py` | 서비스 Protocol 5종 | 51+ methods |
| `modules/core/services/project_service.py` | 프로젝트 파괴적 연산 서비스 | 11 methods |
| `main_a.py` | SovereignApp 진입점 (DI 배선) | 4,200+ lines |

### 소비처 파일 (교차 검증)

| 파일 | 역할 |
|------|------|
| `modules/core/stage4_orchestrator.py` | Stage4 메인 오케스트레이터 |
| `modules/core/stage4_interview_round.py` | Stage4 인터뷰 라운드 |
| `modules/core/stage4_post_processor.py` | Stage4 후처리 |
| `modules/core/stage4_context_builder.py` | Stage4 컨텍스트 빌더 |
| `modules/core/stage2_orchestrator.py` | Stage2 메인 오케스트레이터 |
| `modules/core/stage2_preflight.py` | Stage2 Preflight 분석 |
| `modules/core/stage2_finalizer.py` | Stage2 Finalizer |
| `modules/core/stage2_validation_pipeline.py` | Stage2 검증 파이프라인 |
| `modules/core/stage3_orchestrator.py` | Stage3 메인 오케스트레이터 |

---

## 2. 서브 태스크

| ID | 제목 | 산출물 |
|----|------|--------|
| XC-DI-T1 | Context Slot 완전성 vs 실제 소비 | `XC-DI-T1-context-slot-completeness-consumption-findings.md` |
| XC-DI-T2 | Closure 타입 안전 (DI Callback) | `XC-DI-T2-closure-type-safety-di-callback-findings.md` |
| XC-DI-T3 | Protocol 등록 갭 | `XC-DI-T3-protocol-registration-gap-findings.md` |

---

## 3. 3-Pass 방법론

### PASS 1: 수집
- 각 Context 클래스의 `__slots__` 전수 목록 추출
- 소비처 파일에서 `self.ctx.{slot}` grep으로 실제 참조 횟수 파악
- 콜백 호출 시 None 가드 패턴 분류 (A: callable guard, B: inspect+callable, C: try-except, D: 가드 없음)
- Protocol 메서드 vs 구현체 메서드 대조

### PASS 2: 교차 검증
- `from_app()` 경로에서 실제로 None이 주입되는 경우 식별
- 테스트 mock에서 콜백 누락 시 발현 여부 확인
- Protocol의 isinstance 런타임 검사 사용 여부 확인

### PASS 3: 오탐 제거
- `from_app()` 경로에서 항상 바인딩되는 콜백 → P3 이하로 하향
- 의도적 미구현 (docstring에 명시된 것) → finding에서 제외
- Stage3의 `self.app` 직접 접근 → DI 우회이나 기능적 문제 없음 확인

---

## 4. 결과 요약

| 심각도 | 건수 | 대표 사례 |
|--------|------|-----------|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | 2 | Stage3 DI 우회, Stage3 _safe_getattr 미사용 |
| P3 | 12 | 콜백 None 가드 불일치, orphan 슬롯, Protocol 미활용 등 |
| **합계** | **14** | |

---

## 5. 전체 Finding ID 인덱스

| ID | Severity | 제목 | 출처 |
|----|----------|------|------|
| XC-DI-001 | P3 | Stage4 `get_int_input` 2곳 None 가드 미적용 | T1 |
| XC-DI-002 | P3 | Stage4 `write_audit_summary` Dormant | T1 |
| XC-DI-003 | P3 | Stage2 `retry_feedback_contract`/`missing` Orphan | T1 |
| XC-DI-004 | P3 | Stage3 `preset_registry` ctx 미참조 | T1 |
| XC-DI-005 | P2 | Stage3 `_init_*` DI 우회 (self.app 직접 접근) | T1 |
| XC-DI-006 | P3 | (XC-DI-001 통합) Stage4 get_int_input None 가드 | T2 |
| XC-DI-007 | P3 | `build_item_acquisition_timeline` TypeError 묵인 | T2 |
| XC-DI-008 | P3 | Stage2 콜백 섹션에 데이터 슬롯 혼재 | T2 |
| XC-DI-009 | P3 | inspect.getattr_static 불필요 사용 | T2 |
| XC-DI-010 | P3 | Stage2 `generate_arc_context_v60` None 가드 미적용 | T2 |
| XC-DI-011 | P3 | 5개 Protocol @runtime_checkable 미활용 | T3 |
| XC-DI-012 | P3 | DI Context __init__ Protocol 타입힌트 미적용 | T3 |
| XC-DI-013 | P2 | Stage3 from_app() _safe_getattr 미사용 | T3 |
| XC-DI-014 | P3 | Protocol docstring 라인번호 drift | T3 |
