# XC-DI-T3: Protocol 등록 갭

> Track: XC-DI (Protocol & 계약 준수)
> 대상: app_services.py (5 Protocols), project_service.py, services/*.py
> 감사일: 2026-03-13
> 방법론: 3-Pass (수집 → 교차 검증 → 오탐 제거)

---

## 1. Protocol 목록 및 의도된 구현체

### 1.1 UIServiceProtocol (app_services.py:21)

| 메서드 | 시그니처 | 의도된 구현체 |
|--------|----------|---------------|
| `log` | `(message: str) -> None` | `main_a.py` SovereignApp의 `self.ui` (StudioVisualizer) |
| `title` | `(title: str, subtitle: str = "") -> None` | 동일 |

**NOTE** (app_services.py:33): `modules/core/services/ui_service.py::UIService`는 별도의 입력/선택 helper이며 이 Protocol의 conform 대상이 아님.

**검증 결과:**
- `StudioVisualizer`에 `log()`, `title()` 메서드 존재 → **구조적 서브타이핑 충족**
- `UIService` (services/ui_service.py)는 `log()` 메서드 없음 → Protocol 불일치 (의도적)

### 1.2 AuditServiceProtocol (app_services.py:46)

| 메서드 | 시그니처 | 의도된 구현체 |
|--------|----------|---------------|
| `audit_event` | `(event_type, message, data=None) -> None` | SovereignApp `_audit_event` |
| `flush_audit_buffer` | `() -> None` | SovereignApp `_flush_audit_buffer` |
| `write_audit_summary` | `(tag: str = "snapshot") -> None` | SovereignApp `_write_audit_summary` |

**검증 결과:**
- SovereignApp에 3개 메서드 존재 (private `_` prefix)
- DI 전환 시 public으로 전환 예정 (Phase 4B)
- 현재는 **콜백으로 주입** (ctx.audit_event = app._audit_event) → Protocol 직접 isinstance 검사 미사용

### 1.3 ProjectRepositoryProtocol (app_services.py:76)

| 멤버 | 타입 | 의도된 구현체 |
|------|------|---------------|
| `name` | property → str | `current_project.name` |
| `master_bible` | property + setter → dict | `current_project.master_bible` |
| `volumes` | property + setter → list | `current_project.volumes` |
| `arcs` | property + setter → list | `current_project.arcs` |
| `paths` | property → Any | `current_project.paths` (ProjectPaths) |
| `db` | property → Any | `current_project.db` (DBManager) |

**검증 결과:**
- `current_project` 객체가 이 모든 속성을 갖추고 있음 → **구조적 서브타이핑 충족**
- `ProjectService` (services/project_service.py)는 이 Protocol을 구현하지 않음 (의도적 — ProjectService는 파괴적 연산 서비스이지 저장소가 아님)

### 1.4 StateServiceProtocol (app_services.py:121)

| 메서드 그룹 | 수량 | 의도된 구현체 |
|-------------|------|---------------|
| 아크 상태 추출 | 18개 (`extract_*`) | StateTracker |
| 동반자/플롯 갱신 | 4개 (`update_*`, `check_*`) | StateTracker |
| 요약 | 18개 (`get_*_summary`) | StateTracker |
| 검증 | 3개 (`check_*_in_manuscript`) | StateTracker |
| 아크 요약 | 2개 (`generate_arc_summary`, `format_*`) | StateTracker |
| 프로퍼티 | 3개 (`npc_registry`, `item_state_registry`, `in_world_timeline`) | StateTracker |
| 재정/NPC | 3개 (`import/export_financial_registry`, `cleanup_npc_registry_with_llm`) | StateTracker |

**NOTE** (app_services.py:129): `modules/core/services/state_service.py::StateService`는 검증/패턴 helper 서비스이며 이 Protocol 전체를 의도적으로 구현하지 않음.

**검증 결과:**
- StateTracker가 51개 메서드/프로퍼티 중 대부분을 구현 → 별도 확인 필요하나 구조적 충족 추정
- `StateService`는 `extract_npc_profiles`, `build_validation_context` 등 PromptBuilder 위임 메서드만 보유 → Protocol 불일치 (의도적)

### 1.5 ConfigServiceProtocol (app_services.py:219)

| 멤버 | 타입 | 의도된 구현체 |
|------|------|---------------|
| `selected_genre` | property → dict\|None | SovereignApp.selected_genre |
| `sys` | property → Any | SovereignApp.sys (SystemService) |
| `agents` | property → dict | SovereignApp.agents |
| `perf_timer` | property → Any | SovereignApp.perf_timer |

**검증 결과:**
- SovereignApp이 4개 속성 보유 → **구조적 서브타이핑 충족**

---

## 2. Protocol 실제 사용 현황

### 2.1 isinstance 검사 미사용

5개 Protocol 모두 `@runtime_checkable` 데코레이터가 적용되어 있지만, 코드베이스 전체에서 `isinstance(xxx, UIServiceProtocol)` 등의 런타임 검사가 **한 곳도 없음**.

이는 Protocol이 **문서화/타입힌트 목적**으로만 사용되고, 실제 DI 검증에는 활용되지 않음을 의미.

### 2.2 DI 컨텍스트와의 관계

현재 DI 패턴:
```
SovereignApp → Stage{2,3,4}Context.from_app(app) → ctx 슬롯 주입
```

Protocol은 `from_app()` 경로에서 참조되지 않음. `__init__`에도 Protocol 타입힌트 없음 (전부 `Any` 또는 미지정).

### 2.3 ProjectService의 Protocol 준수

`ProjectService`는 어떤 Protocol도 구현하지 않으며, 구현할 의도도 없음 (독립 서비스 클래스). Protocol 등록 갭이 아닌 **설계 의도**.

---

## 3. Findings

### [XC-DI-011] P3 | 5개 Protocol `@runtime_checkable` 선언되었으나 isinstance 검사 0건

| 필드 | 내용 |
|------|------|
| ID | XC-DI-011 |
| Severity | P3 |
| 현상 요약 | `UIServiceProtocol` 등 5개 Protocol에 `@runtime_checkable` 적용되었으나, 코드베이스 전체에서 isinstance 런타임 검사가 한 곳도 사용되지 않음 |
| 코드 근거 | `app_services.py:20/45/75/120/219` — 전부 `@runtime_checkable`. grep `isinstance.*Protocol` 결과 app_services.py 내 Protocol 참조 0건 |
| 영향 경계 | 기능 영향 없음. `@runtime_checkable`은 불필요한 메타클래스 오버헤드만 추가 |
| 테스트 근거 | `test_protocols_services.py`에서 Protocol 구조 검증 테스트 존재 여부 확인 필요 |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | (1) Phase 4B/4C에서 DI 전환 시 isinstance 검사 추가하여 활용하거나, (2) `@runtime_checkable` 제거하여 단순 typing.Protocol로 유지. 공수 5분 |

### [XC-DI-012] P3 | DI Context `__init__`에 Protocol 타입힌트 미적용

| 필드 | 내용 |
|------|------|
| ID | XC-DI-012 |
| Severity | P3 |
| 현상 요약 | `Stage4Context.__init__`의 `ui`, `current_project`, `sys` 등 파라미터에 Protocol 타입힌트가 적용되지 않아 정적 분석 활용 불가 |
| 코드 근거 | `stage4_context.py:90-130` — 모든 파라미터가 타입 미지정 (`ui`, `current_project`, `agents`, `sys`, `state_tracker` 등). Protocol이 정의되어 있지만 연결 안 됨 |
| 영향 경계 | mypy/pyright 등 정적 분석 도구에서 타입 불일치 감지 불가 |
| 테스트 근거 | N/A (타입 체계 이슈) |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | Phase 4B에서 DI 전환 시 타입힌트 추가. 공수 30분 |

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

### [XC-DI-014] P3 | Protocol docstring의 호출 건수·라인번호가 최신 코드와 불일치 가능

| 필드 | 내용 |
|------|------|
| ID | XC-DI-014 |
| Severity | P3 |
| 현상 요약 | `app_services.py` Protocol docstring에 기재된 라인번호 (예: `stage4_orchestrator.py:260`, `stage2_orchestrator.py:79`)가 코드 변경으로 인해 현재 라인과 불일치할 가능성 |
| 코드 근거 | `app_services.py:25-28` `stage4_orchestrator.py:260 self.app.ui.log(...)` 등 — 코드 분할/리팩터링 이후 라인번호 drift |
| 영향 경계 | 문서 정확성만 영향. 기능 무관 |
| 테스트 근거 | N/A |
| 기존 중복 여부 | 없음 |
| 권장 후속 조치 | 라인번호 대신 메서드명 참조로 변경. 공수 10분. 우선순위 낮음 |
