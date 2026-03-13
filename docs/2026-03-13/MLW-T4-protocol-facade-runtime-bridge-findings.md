# MLW-T4: Protocol / Facade / Runtime Slot Bridge — Findings

> 작성일: 2026-03-13
> 작성자: `Claude Opus`
> 터미널: T4
> 상태: `PASS3 확정`
> 오더: `main_a-live-wiring-contract-detail-full-survey-audit-order.md`
> 초점: `app_services.py` Protocol ↔ service facade ↔ context slot ↔ consumer 경계

---

## 0. 조사 범위 요약

| 대상 | 파일 |
|------|------|
| Protocol 정의 | `modules/protocols/app_services.py` (5 Protocols) |
| Service 구현체 | `modules/core/services/audit_service.py`, `state_service.py`, `ui_service.py`, `project_service.py` |
| DI Context `from_app()` | `stage2_context.py`, `stage3_context.py`, `stage4_context.py` |
| App Surface | `main_a.py` SovereignApp |
| 테스트 | `test_protocols_services.py`, `test_audit_service.py`, `test_state_service.py` |

---

## 1. 확정 Findings

---

### MLW-T4-001 — Protocol이 production code에서 import되지 않음

| 필드 | 값 |
|------|------|
| **ID** | MLW-T4-001 |
| **Severity** | P2 |
| **현상 요약** | `app_services.py`의 5개 Protocol (`UIServiceProtocol`, `AuditServiceProtocol`, `ProjectRepositoryProtocol`, `StateServiceProtocol`, `ConfigServiceProtocol`)은 `@runtime_checkable`로 선언되어 있지만, production code(`modules/`, `main_a.py`) 어디에서도 import되거나 `isinstance()` 검사에 사용되지 않는다. 오직 `test_protocols_services.py`에서만 사용된다. |
| **코드 근거** | `grep -r "from modules.protocols" modules/ main_a.py` → 0건. `grep -r "isinstance.*Protocol" modules/` → 0건. |
| **downstream 영향 경계** | Protocol 정의가 실제 app surface와 drift해도 production path는 영향받지 않지만, Protocol이 제공해야 할 "계약 감시" 기능이 작동하지 않는다. 현재 계약 보증은 `from_app()` 내 `getattr()` 패턴에 전적으로 의존한다. |
| **현재 테스트 근거** | `test_protocols_services.py` — Mock class로 `isinstance` 통과/실패만 확인. SovereignApp 실체와의 정합성 테스트 없음. |
| **기존 문서 중복 여부** | `none` — Protocol 자체의 production 미사용은 기존 문서에서 다루지 않음. |
| **권장 후속 조치** | (1) Protocol을 documentation artifact로 명시 격하하거나, (2) `from_app()` 내부에서 `assert isinstance(app, ConfigServiceProtocol)` 등 construction-time 검증 도입 고려. |

---

### MLW-T4-002 — AuditServiceProtocol 메서드 이름 ↔ SovereignApp 메서드 이름 불일치

| 필드 | 값 |
|------|------|
| **ID** | MLW-T4-002 |
| **Severity** | P2 |
| **현상 요약** | `AuditServiceProtocol`은 public 메서드(`audit_event`, `flush_audit_buffer`, `write_audit_summary`)를 정의한다. SovereignApp은 동일 기능을 private 메서드(`_audit_event`, `_flush_audit_buffer`, `_write_audit_summary`)로 구현한다. 따라서 `isinstance(app, AuditServiceProtocol)` → `False`. Protocol이 모델링하려는 대상(SovereignApp)을 실제로 검증하지 못한다. |
| **코드 근거** | Protocol(`app_services.py` L58-67): `def audit_event(...)`, `def flush_audit_buffer(...)`, `def write_audit_summary(...)`. SovereignApp(`main_a.py` L2786-2794): `def _audit_event(...)`, `def _flush_audit_buffer(...)`, `def _write_audit_summary(...)`. 모든 context `from_app()`: `getattr(app, "_audit_event", None)` (private name 사용). |
| **downstream 영향 경계** | production path에 영향 없음 (Protocol이 runtime에 사용되지 않으므로). 그러나 Protocol 기반 conformance 검증이 실질적으로 불가능한 상태. |
| **현재 테스트 근거** | `test_protocols_services.py` TestAuditServiceProtocol — `MockAudit` class로 public name만 테스트. SovereignApp은 private name이므로 대상에서 제외됨. `test_audit_service.py` — AuditService 구현체 직접 테스트 (8건). |
| **기존 문서 중복 여부** | `none` — 의도적 설계라는 주석이 Protocol docstring에 존재하나("원본은 private(_) 메서드이나 Protocol에서는 public으로 정의"), 이 불일치가 Protocol 무용화를 초래한다는 점은 기존 문서에서 미다룸. |
| **권장 후속 조치** | (1) Protocol이 AuditService 구현체를 대상으로 한다면 `isinstance(AuditService(...), AuditServiceProtocol)` 테스트 추가. (2) Protocol이 SovereignApp facade를 대상으로 한다면 private name 허용 여부 재정의. |

---

### MLW-T4-003 — `write_audit_summary(tag)` 파라미터가 Protocol에 누락

| 필드 | 값 |
|------|------|
| **ID** | MLW-T4-003 |
| **Severity** | P2 |
| **현상 요약** | `AuditServiceProtocol.write_audit_summary(self) -> None`은 파라미터 없이 정의. 실제 AuditService 구현은 `write_audit_summary(self, tag: str = "snapshot")`. Stage2 consumer(`stage2_orchestrator.py` L892)는 `ctx.write_audit_summary("stage2_complete")`, Stage3 consumer(`stage3_orchestrator.py` L601)는 `ctx.write_audit_summary("stage3_complete")`로 tag를 전달한다. Protocol이 실제 계약을 반영하지 못한다. |
| **코드 근거** | Protocol(`app_services.py` L65): `def write_audit_summary(self) -> None: ...`. AuditService(`audit_service.py` L72): `def write_audit_summary(self, tag: str = "snapshot") -> None:`. Stage2(`stage2_orchestrator.py` L892): `self.ctx.write_audit_summary("stage2_complete")`. Stage3(`stage3_orchestrator.py` L601): `ctx.write_audit_summary("stage3_complete")`. |
| **downstream 영향 경계** | 현재 runtime 영향 없음 (Protocol이 production에 미사용). Python duck typing으로 정상 동작. 단, Protocol 기반 검증 도입 시 tagged 호출이 type error로 잡힐 위험. |
| **현재 테스트 근거** | `test_audit_service.py` TestWriteAuditSummary — `write_audit_summary("my_tag")`, `write_audit_summary("test_tag")` 등 tag 포함 테스트 존재. Protocol 테스트는 tag 없이만 검증. |
| **기존 문서 중복 여부** | `related-but-new-live-wiring-surface` — `MFS-T5-001`(facade-shim track)에서 동일 현상 지적. 본 finding은 Protocol 정의 자체의 시그니처 불일치에 초점. |
| **권장 후속 조치** | Protocol 시그니처를 `def write_audit_summary(self, tag: str = "snapshot") -> None: ...`로 갱신. |

---

### MLW-T4-004 — StateService ↔ StateServiceProtocol 명칭 혼동

| 필드 | 값 |
|------|------|
| **ID** | MLW-T4-004 |
| **Severity** | P3 |
| **현상 요약** | `StateServiceProtocol`은 `StateTracker` (50+ 메서드)를 모델링한다고 docstring에 명시. `StateService` (`services/state_service.py`)는 검증/패턴 helper 14개 메서드를 가진 별개 클래스. 두 클래스는 의도적으로 conform 관계가 아님(`test_protocols_services.py` L268-280에서 명시적 non-conform 테스트). 그러나 클래스명 `State + Service`가 공유되어 명칭 혼동 발생. |
| **코드 근거** | `state_service.py` L7-8: "본 helper service의 conform target이 아니다." `app_services.py` L128-130: "StateService는 … 의도적으로 이 Protocol 전체를 구현하지 않는다." `test_protocols_services.py` L268-280: `assert not isinstance(helper, StateServiceProtocol)`. |
| **downstream 영향 경계** | production 영향 없음. 코드 리딩 시 혼동 가능성만 존재. |
| **현재 테스트 근거** | `test_protocols_services.py` TestActualHelperServiceParity — 명시적 non-conform 테스트 존재 (양호). |
| **기존 문서 중복 여부** | `none` |
| **권장 후속 조치** | 관측성 개선 — `StateService`를 `ValidationHelperService` 등으로 rename 고려. 또는 현 docstring 수준 유지. |

---

### MLW-T4-005 — `safe_commit` 반환값 해석이 Stage3 ↔ Stage4에서 diverge

| 필드 | 값 |
|------|------|
| **ID** | MLW-T4-005 |
| **Severity** | P2 |
| **현상 요약** | Stage3은 `safe_commit()` 반환값을 fail-gate로 사용한다: `if callable(ctx.safe_commit) and not ctx.safe_commit(): ctx.ui.log("커밋 실패")` (L1507). Stage4는 cleanup path에서 반환값을 무시한다: `self.ctx.safe_commit()` (L1546, L1555). 동일 콜백의 계약 해석이 stage 간 불일치. |
| **코드 근거** | Stage3(`stage3_orchestrator.py` L1507): `if callable(ctx.safe_commit) and not ctx.safe_commit():` → 실패 시 오류 로깅. Stage4(`stage4_orchestrator.py` L1545-1546): `if callable(getattr(self.ctx, "safe_commit", None)): self.ctx.safe_commit()` → fire-and-forget. |
| **downstream 영향 경계** | Stage4 cleanup에서 DB commit 실패가 조용히 무시될 수 있다. Stage3와 동일 수준의 fail-gate 적용 여부는 의도적 설계일 수 있으나, 계약이 명시되어 있지 않다. |
| **현재 테스트 근거** | Stage4 orchestrator 테스트에서 `safe_commit` 반환값 검증 없음. |
| **기존 문서 중복 여부** | `related-but-new-live-wiring-surface` — `MPN-T5-002`에서 동일 현상 지적. 본 finding은 runtime bridge 계약 관점에서 분리 기술. |
| **권장 후속 조치** | Stage4 cleanup path에서도 `safe_commit()` 반환값 로깅 추가하거나, 두 stage의 의도적 차이를 주석/문서로 명시. |

---

### MLW-T4-006 — Stage2 orchestrator 콜백 unguarded 호출 2건

| 필드 | 값 |
|------|------|
| **ID** | MLW-T4-006 |
| **Severity** | P1 |
| **현상 요약** | Stage2Context의 콜백은 모두 optional (default=None). 그러나 Stage2Orchestrator는 두 곳에서 None 검사 없이 콜백을 직접 호출한다. (1) L224: `self.ctx.calculate_arc_from_episode(existing_ms_max_ep)` — `if existing_ms_max_ep > 0:` 조건 내부에서 guard 없이 호출. (2) L495: `self.ctx.analyze_rejection_pattern_v60(arc_rejections, global_arc_no)` — `if arc_rejections:` 조건 내부에서 guard 없이 호출. 콜백이 None이면 `TypeError: 'NoneType' object is not callable`. |
| **코드 근거** | `stage2_orchestrator.py` L224: `skip_arc_no = self.ctx.calculate_arc_from_episode(existing_ms_max_ep)` — 앞선 L219-220에서 `get_max_episode_from_manuscripts`는 `callable()` guard가 있으나 L224에는 없음. L495: `pattern_analysis = self.ctx.analyze_rejection_pattern_v60(arc_rejections, global_arc_no)` — guard 없음. |
| **downstream 영향 경계** | real-app path에서는 `main_a.py`가 두 콜백 모두 제공하므로 crash 발생하지 않음. 그러나 (1) 단위 테스트에서 MagicMock auto-attribute가 이를 은닉, (2) partial DI 주입 시나리오에서 crash 가능. |
| **현재 테스트 근거** | Stage2 테스트는 MagicMock(spec 없음)으로 context를 구성하므로 모든 attribute가 자동 생성되어 이 drift가 감지되지 않음. |
| **기존 문서 중복 여부** | `related-but-new-live-wiring-surface` — `MRF-T1-001`에서 `analyze_rejection_pattern_v60` 동일 지적. `calculate_arc_from_episode`는 신규. 본 finding은 runtime bridge 관점에서 두 건을 통합 기술. |
| **권장 후속 조치** | L224, L495에 `if callable(getattr(self.ctx, "...", None)):` guard 추가. 기존 codebase 패턴(`stage4_orchestrator.py` L1211, `stage3_orchestrator.py` L533)과 동일 방식. |

---

### MLW-T4-007 — Stage4 orchestrator `get_int_input` unguarded 호출 2건

| 필드 | 값 |
|------|------|
| **ID** | MLW-T4-007 |
| **Severity** | P1 |
| **현상 요약** | Stage4Context의 `get_int_input`은 optional (default=None). Stage4Orchestrator는 두 곳에서 guard 없이 직접 호출한다. (1) L1416: `target_ep = self.ctx.get_int_input(...)` — 사용자 입력 받는 경로. (2) L1472: `style_choice = self.ctx.get_int_input(...)` — 스타일 선택 경로. 반면 L1211-1212는 `if callable(getattr(self.ctx, "get_int_input", None)):` guard가 적용되어 있음. 동일 파일 내 불일치. |
| **코드 근거** | `stage4_orchestrator.py` L1416: `target_ep = self.ctx.get_int_input(...)` — unguarded. L1472: `style_choice = self.ctx.get_int_input(...)` — unguarded. L1211: `if callable(getattr(self.ctx, "get_int_input", None)):` — guarded. |
| **downstream 영향 경계** | real-app path에서는 `main_a.py`가 콜백을 제공하므로 crash 없음. 단위 테스트에서는 MagicMock auto-attribute로 은닉. |
| **현재 테스트 근거** | Stage4 orchestrator 테스트에서 `get_int_input` None 시나리오 미검증. |
| **기존 문서 중복 여부** | `none` — 기존 문서에서 이 두 지점은 미다룸. |
| **권장 후속 조치** | L1416, L1472에 `callable()` guard 추가. 또는 `get_int_input`을 required callback으로 승격하고 `from_app()`에서 `app._get_int_input` 직접 바인딩 (None 불허). |

---

### MLW-T4-008 — `from_app()` construction-time 계약 검증 부재

| 필드 | 값 |
|------|------|
| **ID** | MLW-T4-008 |
| **Severity** | P3 |
| **현상 요약** | Stage2/3/4 Context의 `from_app(cls, app)` classmethod는 `getattr(app, "attr", None)` 패턴으로 모든 속성을 추출한다. 필수 5종(`ui`, `current_project`, `agents`, `sys`, `state_tracker`)조차 `app.ui` 직접 접근만 하고, 존재 여부나 타입 검증이 없다. Protocol이 production에서 사용되지 않으므로(MLW-T4-001), construction-time에 app surface drift를 감지할 메커니즘이 전무하다. |
| **코드 근거** | `stage2_context.py` L208-259: `from_app()` — 0건의 assert, isinstance, Protocol 검사. `stage3_context.py` L101-128: 동일. `stage4_context.py` L140-179: 동일. |
| **downstream 영향 경계** | 필수 속성(`ui`, `current_project`)이 SovereignApp에서 제거되면 `from_app()` 시점에서 `AttributeError`가 발생하므로 즉시 감지됨. 그러나 optional 콜백이 이름 변경되면 `getattr` fallback None으로 조용히 넘어가고, consumer에서 unguarded 호출 시 crash (MLW-T4-006, 007과 연결). |
| **현재 테스트 근거** | `from_app()` 자체 테스트 없음. 오케스트레이터 테스트는 수동 context 구성 또는 MagicMock 사용. |
| **기존 문서 중복 여부** | `none` |
| **권장 후속 조치** | (1) 필수 속성에 대해 `from_app()` 내 `assert hasattr(app, "ui")` 추가 고려. (2) 또는 integration test에서 `Stage2Context.from_app(real_app_fixture)` → slot 검증 추가. |

---

## 2. PASS 추적 요약

### PASS 1 후보 (8건)

| 후보 | 확신도 | 결과 |
|------|--------|------|
| Protocol production 미사용 | HIGH | → **MLW-T4-001 확정** |
| AuditServiceProtocol 명칭 불일치 | HIGH | → **MLW-T4-002 확정** |
| write_audit_summary(tag) Protocol 누락 | HIGH | → **MLW-T4-003 확정** |
| StateService 명칭 혼동 | MED | → **MLW-T4-004 확정** (P3) |
| safe_commit 반환값 divergence | HIGH | → **MLW-T4-005 확정** |
| Stage2 unguarded callbacks | HIGH | → **MLW-T4-006 확정** |
| Stage4 get_int_input unguarded | HIGH | → **MLW-T4-007 확정** |
| from_app() construction 검증 부재 | MED | → **MLW-T4-008 확정** (P3) |

### PASS 2 제거 (0건)

모든 PASS 1 후보가 코드 근거로 확인됨. 제거 대상 없음.

### PASS 3 확정 (8건)

| ID | Severity | 요약 |
|----|----------|------|
| MLW-T4-001 | P2 | Protocol이 production에서 import/사용되지 않음 |
| MLW-T4-002 | P2 | AuditServiceProtocol public name ↔ app private name 불일치 |
| MLW-T4-003 | P2 | write_audit_summary(tag) 파라미터 Protocol 누락 |
| MLW-T4-004 | P3 | StateService ↔ StateServiceProtocol 명칭 혼동 |
| MLW-T4-005 | P2 | safe_commit 반환값 Stage3 fail-gate ↔ Stage4 fire-and-forget |
| MLW-T4-006 | P1 | Stage2 orchestrator 콜백 unguarded 호출 2건 |
| MLW-T4-007 | P1 | Stage4 orchestrator get_int_input unguarded 호출 2건 |
| MLW-T4-008 | P3 | from_app() construction-time 계약 검증 부재 |

---

## 3. Severity 집계

| Severity | 건수 | IDs |
|----------|------|-----|
| P0 | 0 | — |
| P1 | 2 | MLW-T4-006, MLW-T4-007 |
| P2 | 4 | MLW-T4-001, MLW-T4-002, MLW-T4-003, MLW-T4-005 |
| P3 | 2 | MLW-T4-004, MLW-T4-008 |

---

## 4. 기존 문서 중복 대조

| Finding | 중복 판정 | 관련 기존 문서 |
|---------|-----------|---------------|
| MLW-T4-001 | `none` | — |
| MLW-T4-002 | `none` | — |
| MLW-T4-003 | `related-but-new-live-wiring-surface` | MFS-T5-001 |
| MLW-T4-004 | `none` | — |
| MLW-T4-005 | `related-but-new-live-wiring-surface` | MPN-T5-002 |
| MLW-T4-006 | `related-but-new-live-wiring-surface` | MRF-T1-001 |
| MLW-T4-007 | `none` | — |
| MLW-T4-008 | `none` | — |

---

## 5. Coverage Gap / Open Questions

1. **UIServiceProtocol ↔ UIService 분리는 의도적인가?** — Protocol docstring에 명시("conform 대상이 아니다"). 의도적 분리 확인됨. Gap 아님.
2. **ConfigServiceProtocol이 SovereignApp을 validate할 수 있는가?** — SovereignApp에 `selected_genre`, `sys`, `agents`, `perf_timer` 모두 존재. 단, property가 아니라 plain attribute이므로 `isinstance` 검사에서는 method 존재만 확인하고 property/attribute 구분은 무시. 실질적 검증 가능.
3. **ProjectRepositoryProtocol `arcs.setter` 누락 가능성** — MockProject에 `arcs.setter` 없이도 `isinstance` 통과 (`@runtime_checkable`은 setter 존재를 강제하지 않음). SovereignApp의 `current_project` 실체에서 setter 존재 여부 미검증. 관측성 수준 gap.
