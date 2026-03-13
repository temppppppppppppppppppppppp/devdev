# [MLW-T2] Stage3 Real-App Binding Findings

> 작성일: 2026-03-13
> 작성자: `opus`
> 상태: `executed / PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-live-wiring-contract-detail-full-survey-audit-order.md`

이 문서는 `T2` (Stage3 Real-App Binding) 범위 실조사 결과다. 조사 중 코드 직접 수정은 하지 않았다.

---

## 조사 범위

- `main_a.py`: Stage3에 export하는 bound method 전반
  - `__init__()` L272: `self._stage3_orch = Stage3Orchestrator(app=self)`
  - `_stage_3_batch_blueprinting()` L2867-2876: thin delegate (ctx 갱신 후 위임)
  - OneStop/FrontierLag 진입점: L3627-3630, L3742-3745, L3965-3968
- 직접 downstream
  - `modules/core/stage3_context.py`: Stage3Context (23 __slots__)
  - `modules/core/stage3_orchestrator.py`: Stage3Orchestrator (~2000줄)

## 필수 근거

- `tests/test_stage3_orchestrator.py`
- `tests/e2e/test_l3_stage3_smoke.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`
- `docs/2026-03-13/MFS-T3-stage3-stage4-audit-callback-findings.md` (기존 facade 감리)

## PASS 기록

### PASS 1 — 표면 수집

후보 8건 수집:

1. **[HIGH] `self.app` 직접 참조 3곳 — DI context 우회**: `_handle_success()` L1543, `_handle_failure()` L1978, `_detect_inventory_gaps()` L1749가 `self.app.quality_dashboard` / `self.app.constraint_db`를 직접 참조한다. `quality_dashboard`와 `constraint_db`는 Stage3Context `__slots__`에 없다.
2. **[HIGH] `_record_retrieval_observation()` L1193에서 `self.app` 직접 전달**: 자유 함수 `_record_retrieval_observation(app, ...)` 호출 시 `self.app`을 전달한다. `quality_dashboard`는 ctx에 없으므로 self.app 경유가 필수이나, DI 설계와 불일치.
3. **[HIGH] lazy init 3종이 `self.app`에 직접 write-back**: `_init_state_tracker_if_needed()`, `_init_world_state_if_needed()`, `_init_fact_ledger_if_needed()` 전부 `self.app`에 할당한 뒤 L511-513에서 `ctx`에 재동기화. app→ctx 단방향 동기화 패턴은 의도적이지만, lazy init이 실패하면 ctx에 None이 남고, app에도 None이 남는 교차 무결성은 보장된다.
4. **[MED] spec 없는 MagicMock fixture — app_mock()**: `tests/test_stage3_orchestrator.py` L18-77의 `app_mock()`이 `MagicMock()`으로 생성된다. `spec=SovereignApp`이 없으므로 실제 app surface에 없는 속성 접근이 자동으로 MagicMock을 반환하여 false green을 생성할 수 있다.
5. **[MED] e2e smoke test의 `_build_mock_app()`도 spec 없음**: `tests/e2e/test_l3_stage3_smoke.py` L92-182의 mock도 spec이 없다. 다만 필요한 콜백을 명시적으로 side_effect로 설정하므로 unit test보다 현실적이다.
6. **[MED] `get_latest_episode_number` vs `get_max_episode_from_manuscripts` 이중 소스**: L528-534에서 `ctx.current_project.get_latest_episode_number()`를 먼저 시도하고, 없으면 `ctx.get_max_episode_from_manuscripts()`로 폴백. `get_latest_episode_number`는 Stage3Context에도 main_a.py facade에도 명시적으로 매핑되지 않는 Project 메서드이므로, main_a.py surface 관점에서는 Project 객체가 이 메서드를 제공하는지에 의존한다. → Project 내부 메서드이므로 app binding 문제는 아님. `duplicate candidate`.
7. **[LOW] `session_logger` 슬롯 — `from_app()`에서 `app._session_logger`로 매핑**: Stage3Context L127에서 `session_logger=getattr(app, "_session_logger", None)` — `main_a.py` L280에서 `self._session_logger = SessionLogger(...)` 로 선언. 이름 매핑 정확. 테스트에서도 L54 `app._session_logger = MagicMock()` 설정.
8. **[LOW] `adversarial_self_play` 슬롯 — ctx에 존재하지만 `from_app()`에서 `getattr(app, "adversarial_self_play", None)` 으로 공개 속성 참조**: `main_a.py` L360 `self.adversarial_self_play = None`, L1857에서 lazy init. public 속성이므로 이름 매핑 정확.

### PASS 2 — 교차 검증

- **후보 3 (lazy init write-back)**: 코드 L511-513에서 `ctx.state_tracker = getattr(self.app, ...)` 패턴이 lazy init 후 즉시 재동기화하므로, lazy init 성공 시 ctx와 app이 동일 객체를 가리킨다. 실패 시 양쪽 모두 None. 의도적 설계로 확인. → finding에서 제거. 다만 후보 1과 합쳐 `self.app` 직접 참조 패턴은 유지.
- **후보 6 (`get_latest_episode_number`)**: Project 메서드이며 app surface 문제가 아님. → 제거. `duplicate candidate: Project 내부 인터페이스`.
- **후보 7, 8**: 이름 매핑 정확 확인. → 제거.
- **후보 4, 5 (spec 없는 MagicMock)**: 코드 대조 결과, `app_mock()`에서 명시적으로 설정된 속성/콜백은 17종이고, Stage3Context `from_app()`가 읽는 속성은 20종(필수 2 + 속성 10 + 콜백 10 + session_logger 1 = 23). `app_mock()`에서 누락된 속성 중 `memory`, `context_advisor`는 `app.memory = None`, `app.context_advisor = None`으로 명시적 설정됨. 그러나 `adversarial_self_play`, `pass_rate_monitor`는 MagicMock 자동 생성에 의존 — real app에서는 초기값 `None`이므로 테스트에서 MagicMock 객체가 truthy하게 동작하면 실제와 다른 경로를 탈 수 있다. 이는 후보 1의 ctx 미포함 속성과는 별개의 test realism 문제. → T5 범위와 중복 가능성 있으나, real-app binding 관점에서 신규 유지.

### PASS 3 — 최종 확정

5건 확정:

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| `MLW-T2-01` | `P1` | confirmed | `stage3_orchestrator._handle_success()` L1543, `._handle_failure()` L1978 | `quality_dashboard` 접근이 `self.app` 직접 참조 — DI context 우회 |
| `MLW-T2-02` | `P2` | confirmed | `stage3_orchestrator._detect_inventory_gaps()` L1749 | `constraint_db` 접근이 `self.app` 직접 참조 — DI context 우회 |
| `MLW-T2-03` | `P2` | confirmed | `stage3_orchestrator._generate_blueprint()` L1193 | `_record_retrieval_observation(self.app, ...)` 호출이 DI context를 우회해 `quality_dashboard`에 접근 |
| `MLW-T2-04` | `P2` | confirmed | `tests/test_stage3_orchestrator.py` L18-77 | spec 없는 MagicMock fixture가 `pass_rate_monitor`/`adversarial_self_play` 등에서 real app과 다른 truthy 값을 반환해 false green 위험 |
| `MLW-T2-05` | `P3` | confirmed | Stage3Context `__slots__` / `from_app()` | `quality_dashboard`, `constraint_db` 2개 속성이 Stage3Context에 없어 DI 완전성이 깨진 상태 |

---

## [MLW-T2-01] `quality_dashboard` 접근이 `self.app` 직접 참조 — DI context 우회

### 1. ID
`MLW-T2-01`

### 2. Severity
`P1`

### 3. 현상 요약
`Stage3Orchestrator._handle_success()` L1543과 `._handle_failure()` L1978에서 `getattr(self.app, "quality_dashboard", None)`으로 직접 `self.app`에 접근한다. Stage3Orchestrator는 Phase 4C DI 전환 완료 후 모든 소비를 `self.ctx`를 통해야 하는 설계인데, `quality_dashboard`가 Stage3Context `__slots__`에 포함되지 않아 `self.app` 우회가 남아 있다.

### 4. 코드 근거
```python
# stage3_orchestrator.py L1543 (_handle_success)
_qd = getattr(self.app, "quality_dashboard", None)

# stage3_orchestrator.py L1978 (_handle_failure)
_qd = getattr(self.app, "quality_dashboard", None)
```

`Stage3Context.__slots__`에 `quality_dashboard`가 없다. `from_app()`에서도 매핑하지 않는다.

### 5. Downstream 영향 경계
- `quality_dashboard.record_validation()` 호출 여부가 `self.app` 존재에 의존.
- DI context만으로 Stage3를 실행하는 경로(예: 테스트, 향후 독립 실행)에서는 quality_dashboard 기록이 silent skip된다.
- 현재 production path에서는 `self.app`이 항상 존재하므로 즉시 실패는 아님. 그러나 DI 경계 원칙 위반.

### 6. 현재 테스트 근거
- `tests/test_stage3_orchestrator.py`의 `app_mock = MagicMock()`이므로 `app_mock.quality_dashboard`는 자동 생성 MagicMock → 항상 truthy → `record_validation()` 호출은 MagicMock에 흡수됨.
- 실제 real app에서 `self.quality_dashboard`가 `None`이면 (프로젝트 미로드 시) getattr 패턴으로 안전하게 skip. 동작은 맞으나 DI 계약 위반.

### 7. 기존 문서와의 중복 여부
`related-but-new-live-wiring-surface`. MFS-T3-02가 Stage4의 `self.app` 직접 참조를 다뤘으나, Stage3의 `quality_dashboard` 직접 참조는 별도 표면.

### 8. 권장 후속 조치
- Stage3Context `__slots__`에 `quality_dashboard` 추가
- `from_app()`에 `quality_dashboard=getattr(app, "quality_dashboard", None)` 매핑 추가
- `_handle_success()`/`_handle_failure()`에서 `getattr(self.app, ...)` → `getattr(ctx, ...)` 전환

---

## [MLW-T2-02] `constraint_db` 접근이 `self.app` 직접 참조 — DI context 우회

### 1. ID
`MLW-T2-02`

### 2. Severity
`P2`

### 3. 현상 요약
`_detect_inventory_gaps()` L1749에서 `getattr(self.app, "constraint_db", None)`으로 직접 접근한다. `constraint_db`는 `main_a.py`에 선언 자체가 없는 속성이다 (grep 0 hit). 따라서 real app에서 이 코드 경로는 항상 None을 반환하여 fallback에 의존하지만, `self.app` 참조 자체가 DI 원칙 위반이며, 미래에 `constraint_db`가 추가되더라도 ctx를 통하지 않는 문제가 남는다.

### 4. 코드 근거
```python
# stage3_orchestrator.py L1749
_cdb = getattr(self.app, "constraint_db", None)
if _cdb:
    try:
        owned = set(_cdb.get_current_inventory(arc_data.get("arc_no", 1) - 1))
    except ...
```

`main_a.py`에 `constraint_db` 선언 없음 (grep 0 match). `Stage3Context.__slots__`에도 없음.

### 5. Downstream 영향 경계
- 현재: dead code path. `self.app`에 `constraint_db`가 없으므로 항상 `None` → 무조건 skip.
- `_detect_inventory_gaps()`의 `owned` 집합이 비어 있으면 `world_state.get_owned_items()`에만 의존. world_state가 있으면 문제 없음.

### 6. 현재 테스트 근거
- 테스트에서 `_detect_inventory_gaps` 전용 테스트 없음. `_handle_success`에서 간접 실행되지만 MagicMock auto-attribute가 `constraint_db`를 truthy로 반환하여 실제와 다른 경로를 탄다.

### 7. 기존 문서와의 중복 여부
`none`. 신규 발견.

### 8. 권장 후속 조치
- `constraint_db`가 실제로 필요한 기능이면 main_a.py + Stage3Context에 추가
- 불필요하면 해당 fallback 코드 경로 제거 (dead code 정리)

---

## [MLW-T2-03] `_record_retrieval_observation(self.app, ...)` 호출이 DI context를 우회

### 1. ID
`MLW-T2-03`

### 2. Severity
`P2`

### 3. 현상 요약
`_generate_blueprint()` L1192-1209에서 자유 함수 `_record_retrieval_observation(self.app, ...)` 를 호출한다. 이 함수는 `getattr(app, "quality_dashboard", None)`으로 `quality_dashboard`에 접근한다. MLW-T2-01과 같은 근본 원인이지만, 다른 메서드/경로에서 발생한다.

### 4. 코드 근거
```python
# stage3_orchestrator.py L399-406
def _record_retrieval_observation(app, *, ep_num, stage, observation):
    dashboard = getattr(app, "quality_dashboard", None)
    if dashboard is None or not hasattr(dashboard, "record_retrieval_observation"):
        return
    ...

# stage3_orchestrator.py L1192-1193 (호출부)
_record_retrieval_observation(
    self.app,
    ep_num=working_ep,
    ...
)
```

### 5. Downstream 영향 경계
- MLW-T2-01과 동일 패턴. `quality_dashboard`가 ctx에 없어 self.app 경유 필수.
- 관측성(observability) 기록이 누락될 수 있으나 비차단.

### 6. 현재 테스트 근거
- 테스트에서 `_record_retrieval_observation`에 대한 직접 테스트 없음. MagicMock에 의해 흡수.

### 7. 기존 문서와의 중복 여부
`related-but-new-live-wiring-surface`. MLW-T2-01과 같은 근본 원인이지만 다른 코드 경로.

### 8. 권장 후속 조치
- MLW-T2-01 해결과 동시에 진행. `_record_retrieval_observation`의 시그니처를 `app` → `quality_dashboard` 직접 전달로 변경하거나, ctx에서 가져오도록 전환.

---

## [MLW-T2-04] spec 없는 MagicMock fixture — real app surface drift 위험

### 1. ID
`MLW-T2-04`

### 2. Severity
`P2`

### 3. 현상 요약
`tests/test_stage3_orchestrator.py` L18-77의 `app_mock()` fixture가 `MagicMock()`으로 생성된다. `spec=SovereignApp` 없이 생성되므로, 실제 SovereignApp에 존재하지 않는 속성에 접근해도 MagicMock가 자동으로 새 MagicMock을 반환하여 테스트가 통과한다. 대표적 위험:

- `app_mock.quality_dashboard` — real app에서는 `None`일 수 있으나, MagicMock에서는 truthy 객체 반환
- `app_mock.constraint_db` — real app에는 존재조차 하지 않으나, MagicMock에서는 truthy
- `app_mock.pass_rate_monitor` — fixture에서 명시적으로 `MagicMock()` 설정, real app에서는 `None` 가능
- `app_mock.adversarial_self_play` — fixture에서 미설정, MagicMock auto-attribute로 truthy

### 4. 코드 근거
```python
# tests/test_stage3_orchestrator.py L18-20
@pytest.fixture
def app_mock():
    app = MagicMock()  # spec 없음
```

Stage3Context `from_app()` L101-128이 `getattr(app, ...)` 패턴을 사용하므로, spec 없는 MagicMock에서는 모든 속성이 non-None MagicMock → truthy 경로를 타게 된다.

### 5. Downstream 영향 경계
- 속성 이름 오타/제거/리네임이 테스트에서 감지 불가
- real app에서 `None`인 속성이 테스트에서 truthy → 분기 차이 → false green
- 특히 `pass_rate_monitor.record_attempt()`, `quality_dashboard.record_validation()` 호출이 테스트에서는 항상 실행되나 real app에서는 conditional

### 6. 현재 테스트 근거
- 현재 112+ 테스트가 이 fixture 기반으로 통과 중
- `tests/e2e/test_l3_stage3_smoke.py`의 `_build_mock_app()`은 콜백을 명시적 side_effect로 설정하므로 상대적으로 현실적

### 7. 기존 문서와의 중복 여부
`related-but-new-live-wiring-surface`. T5 범위(test realism)와 교차하지만, Stage3 특유의 `quality_dashboard`/`constraint_db` 부재가 real-app binding 관점에서 신규.

### 8. 권장 후속 조치
- `app_mock = MagicMock(spec=SovereignApp)` 전환 검토
- 최소한 `quality_dashboard=None`, `constraint_db=None` 명시적 설정
- `adversarial_self_play=None` 명시적 설정 (real app 초기값과 일치)

---

## [MLW-T2-05] Stage3Context에 `quality_dashboard` / `constraint_db` 슬롯 부재

### 1. ID
`MLW-T2-05`

### 2. Severity
`P3`

### 3. 현상 요약
`Stage3Context.__slots__`에 `quality_dashboard`와 `constraint_db`가 없다. Stage3Orchestrator가 이 두 속성을 `self.app`에서 직접 참조하는 근본 원인이 여기에 있다. DI 완전성(completeness) 관점에서 Stage3 consumer가 소비하는 모든 속성이 ctx에 있어야 하는데, 이 2개가 누락됨.

### 4. 코드 근거
```python
# stage3_context.py __slots__ (전체)
__slots__ = (
    "ui", "current_project",
    "agents", "sys", "state_tracker", "memory", "context_advisor",
    "world_state", "fact_ledger", "adversarial_self_play",
    "preset_registry", "selected_genre", "pass_rate_monitor",
    "get_protagonist_name", "audit_event", "write_audit_summary",
    "get_arc_context_for_episode", "get_max_episode_from_manuscripts",
    "get_int_input", "safe_commit", "validate_arc_data_fields",
    "validate_blueprint_integrity", "fix_entity_registry_protagonist",
    "session_logger",
)
```

`quality_dashboard`, `constraint_db` 없음.

### 5. Downstream 영향 경계
- MLW-T2-01, MLW-T2-02, MLW-T2-03의 근본 원인
- DI context만으로 Stage3를 독립 실행하면 quality_dashboard 기록이 무조건 누락

### 6. 현재 테스트 근거
- Stage3Context 직접 테스트 없음 (context 생성 자체는 `from_app()` 호출로 간접 검증)

### 7. 기존 문서와의 중복 여부
`none`. 신규 발견. MFS-T3가 audit callback 관점에서 Stage3/4를 다뤘으나, quality_dashboard 슬롯 부재는 다루지 않았다.

### 8. 권장 후속 조치
- Stage3Context에 `quality_dashboard` 슬롯 추가 + `from_app()` 매핑
- `constraint_db`는 main_a.py에 존재하지 않으므로, 해당 코드 경로 제거가 우선
- 슬롯 추가 후 MLW-T2-01 ~ MLW-T2-03 자동 해소

---

## Coverage Gap / Open Questions

1. **`from_app()` 콜백 이름 매핑 완전성**: 현재 10개 콜백 전부 `main_a.py`에서 `def _이름(...)` 형태로 존재함을 확인. 이름/signature 일치 검증 완료. 특이사항 없음.
2. **OneStop/FrontierLag 진입 경로**: L3627-3630, L3742-3745, L3965-3968 전부 `Stage3Context.from_app(self)` → `ctx` setter → `stage_3_batch_blueprinting()` 동일 패턴. 분기별 wiring 차이 없음.
3. **resume 경로**: Stage3는 자체 resume 경로가 없고, main_a.py의 `_stage_3_batch_blueprinting()`이 항상 `from_app(self)`로 ctx를 갱신하므로 stale ctx 위험 없음.

---

## PASS1 → PASS2 → PASS3 요약

| 단계 | 총 후보 | 제거 | 확정 |
|------|---------|------|------|
| PASS 1 | 8 | - | - |
| PASS 2 | - | 3 (lazy init 의도적, get_latest_episode_number 범위 외, session_logger/adversarial_self_play 매핑 정확) | - |
| PASS 3 | - | - | 5 (MLW-T2-01~05) |

## Severity 합계

| Severity | 건수 |
|----------|------|
| P0 | 0 |
| P1 | 1 |
| P2 | 3 |
| P3 | 1 |
| **합계** | **5** |
