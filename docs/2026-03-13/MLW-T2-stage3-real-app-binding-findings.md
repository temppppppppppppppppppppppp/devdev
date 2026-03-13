# [MLW-T2] Stage3 Real-App Binding Findings

> 작성일: 2026-03-13
> 작성자: `opus 초안 / codex 재감리`
> 상태: `re-executed / PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / source-report cross-check / UTF-8 only`
> 기준 오더: `main_a-live-wiring-contract-detail-full-survey-audit-order.md`

이 문서는 `T2` (Stage3 Real-App Binding) 범위를 OPUS 초안에 의존하지 않고 다시 조사한 보강본이다. 기존 초안의 후보를 그대로 수용하지 않고, `main_a.py` Stage3 진입점 4곳, `Stage3Context.from_app()`, `Stage3Orchestrator`의 `self.app`/`ctx` 혼용, Stage3 unit/e2e 테스트, 기존 control-plane/facade 감리 문서를 다시 교차 검증했다.

재감리 결론은 단순하다. `main_a.py -> Stage3Context.from_app() -> Stage3Orchestrator`의 진입 wiring 자체는 현재 일관적이다. 실제로 남아 있는 live-wiring blind spot은 `quality_dashboard` app-only bypass, 실앱 surface에 없는 `constraint_db` fallback, unspecced `MagicMock` 기반 false green, 그리고 Stage3Context 계약의 불완전성 4건이다.

---

## 조사 범위

- `main_a.py`
  - `__init__()` L272: `self._stage3_orch = Stage3Orchestrator(app=self)`
  - `_stage_3_batch_blueprinting()` L2912-2921: `Stage3Context.from_app(self)` 후 thin delegate
  - final close path L3671-3675: `Stage3Context.from_app(self)` 후 `target_ep` 지정 호출
  - frontier sync path L3786-3790: 동일 패턴
  - one-arc pipeline path L4009-4013: 동일 패턴
- 직접 downstream
  - `modules/core/stage3_context.py`: Stage3Context slot/callback contract
  - `modules/core/stage3_orchestrator.py`: Stage3 consumer의 실제 `ctx`/`self.app` 소비면
- 교차 참조 문서
  - `docs/2026-03-13/MFS-T3-stage3-stage4-audit-callback-findings.md`
  - `docs/2026-03-13/main_a-control-plane-detail-consolidated-findings-3pass-reaudit.md`

## 필수 근거

- `tests/test_stage3_orchestrator.py`
- `tests/e2e/test_l3_stage3_smoke.py`
- `modules/core/stage3_context.py`
- `modules/core/stage3_orchestrator.py`
- `main_a.py`

## 추가 검증

- 회귀 테스트
  - `pytest -q tests/test_stage3_orchestrator.py` -> `62 passed in 3.26s`
  - `pytest -q tests/e2e/test_l3_stage3_smoke.py -rs` -> `5 skipped`
  - skip 사유: `projects/코덱스_테스트/project_data.db` 부재로 real-project smoke 미실행
- synthetic verification
  - bare `MagicMock`에 대해 `Stage3Context.from_app(app)` 실행 시 `ctx.pass_rate_monitor`, `ctx.adversarial_self_play`가 둘 다 truthy `MagicMock`으로 채워짐을 확인
  - 같은 synthetic check에서 `Stage3Context`에는 `quality_dashboard`, `constraint_db` slot이 없음을 확인

---

## PASS 기록

### PASS 1 - 표면 수집

후보 7건 수집:

1. `main_a.py`의 Stage3 진입점 4곳이 모두 같은 `Stage3Context.from_app(self)` wiring을 쓰는지
2. `Stage3Context.from_app()`의 10개 callback + `session_logger` 이름 매핑이 실제 `main_a.py` facade와 일치하는지
3. `quality_dashboard` 관측성 경로가 `ctx`가 아니라 `self.app`를 직접 보는지
4. `_detect_inventory_gaps()`의 `constraint_db` fallback이 실앱 surface와 맞물리는지
5. `current_project.get_latest_episode_number()`와 `ctx.get_max_episode_from_manuscripts()` 혼용이 Stage3 live wiring 신규 finding인지
6. `tests/test_stage3_orchestrator.py`와 `tests/e2e/test_l3_stage3_smoke.py`의 `MagicMock` app이 real app surface drift를 숨기는지
7. `Stage3Context`가 실제 Stage3 consumer가 쓰는 surface를 다 싣고 있는지

### PASS 2 - 교차 검증

- 후보 1 제거: Stage3 진입점 분기별 wiring 차이는 현재 없다.
  - `main_a.py:2919`, `main_a.py:3674`, `main_a.py:3789`, `main_a.py:4012`가 모두 `Stage3Context.from_app(self)` 후 동일 orchestrator를 호출한다.
  - 따라서 menu/manual/final-close/frontier/one-arc 경로 간 `ctx` source split은 현재 관측되지 않는다.
- 후보 2 제거: callback 이름 드리프트는 없다.
  - `Stage3Context.from_app()`가 참조하는 `_safe_commit`, `_get_int_input`, `_get_protagonist_name`, `_audit_event`, `_write_audit_summary`, `_get_arc_context_for_episode`, `_get_max_episode_from_manuscripts`, `_validate_arc_data_fields`, `_validate_blueprint_integrity`, `_fix_entity_registry_protagonist`, `_session_logger`는 현재 `main_a.py`에 모두 존재한다.
- 후보 5 제거: hybrid production-head source는 이번 트랙에서 재오픈하지 않는다.
  - `ctx.current_project.get_latest_episode_number()` vs `ctx.get_max_episode_from_manuscripts()` 혼용은 이미 control-plane 재감리에서 다룬 영역이며, 이번 T2에서는 `already-covered-do-not-reopen`으로 처리한다.

### PASS 3 - 최종 확정

4건 확정:

| ID | Sev | 상태 | 파일/함수 | 요약 |
|----|-----|------|-----------|------|
| `MLW-T2-01` | `P2` | confirmed | `stage3_orchestrator._record_retrieval_observation()`, `._handle_success()`, `._handle_failure()` | `quality_dashboard` 관측성 경로가 `ctx` 대신 `self.app`에 직접 결합돼 있다 |
| `MLW-T2-02` | `P2` | confirmed | `stage3_orchestrator._detect_inventory_gaps()` | `constraint_db` fallback이 real app surface에 존재하지 않는 dead/ghost binding이다 |
| `MLW-T2-03` | `P2` | confirmed | `tests/test_stage3_orchestrator.py`, `tests/e2e/test_l3_stage3_smoke.py` | unspecced `MagicMock`과 always-on optional helper가 Stage3 live wiring drift를 false green으로 숨긴다 |
| `MLW-T2-04` | `P3` | confirmed | `stage3_context.py`, `main_a.py` Stage3 entrypoints | `Stage3Context` 계약이 실제 Stage3 consumer surface를 완전히 표현하지 못한다 |

---

## [MLW-T2-01] `quality_dashboard` 관측성 경로가 `ctx` 대신 `self.app`에 직접 결합돼 있다

### 1. ID
`MLW-T2-01`

### 2. Severity
`P2`

### 3. 현상 요약
Stage3의 `quality_dashboard` 소비는 `ctx` 계약 밖에 남아 있다. `_record_retrieval_observation()` helper는 `app` 객체를 직접 받아 `quality_dashboard`를 조회하고, `_handle_success()` / `_handle_failure()`도 각각 `getattr(self.app, "quality_dashboard", None)`으로 PASS/REJECT validation을 기록한다. `Stage3Context`에는 `quality_dashboard` slot이 없고 `from_app()` 매핑도 없다. 즉 real-app에서는 우연히 동작하지만, DI context 기준 계약은 완결돼 있지 않다.

### 4. 코드 근거
```python
# modules/core/stage3_orchestrator.py:399-404
def _record_retrieval_observation(app, *, ep_num: int, stage: str, observation: dict) -> None:
    dashboard = getattr(app, "quality_dashboard", None)
    if dashboard is None or not hasattr(dashboard, "record_retrieval_observation"):
        return

# modules/core/stage3_orchestrator.py:1192-1193
_record_retrieval_observation(self.app, ...)

# modules/core/stage3_orchestrator.py:1543
_qd = getattr(self.app, "quality_dashboard", None)

# modules/core/stage3_orchestrator.py:1978
_qd = getattr(self.app, "quality_dashboard", None)
```

추가 교차 근거:

- `modules/core/stage3_context.py`에는 `quality_dashboard` slot과 매핑이 없다.
- `main_a.py:370`은 `self.quality_dashboard = None`으로 시작하고, `main_a.py:1946`에서야 V50 module init 성공 시 `QualityDashboard`를 붙인다.

### 5. Downstream 영향 경계

- 영향 있음:
  - Stage3 retrieval/validation observability가 `ctx` 기반 adapter/injected context에서 재현되지 않는다.
  - `quality_dashboard` surface rename/remove가 `Stage3Context` 계약으로는 감지되지 않는다.
- 영향 제한:
  - 현재 `SovereignApp` 실경로에서는 `self.app`가 존재하므로 즉시 Stage3 생성 실패로 번지지는 않는다.
  - 이 surface는 서사 산출물 자체보다 관측성과 품질 기록에 영향을 준다.

### 6. 현재 테스트 근거 또는 테스트 부재

- `tests/test_stage3_orchestrator.py:644-678`만 `app_mock.quality_dashboard = MagicMock()`을 명시 세팅하고 retrieval observation 경로를 확인한다.
- 반면 `_handle_success()` / `_handle_failure()`의 `record_validation()` 경로는 전용 회귀 테스트가 없다.
- `app_mock`가 bare `MagicMock`이기 때문에, quality dashboard를 명시하지 않은 테스트에서도 `getattr(self.app, "quality_dashboard", None)`가 truthy child mock을 돌려 false green이 가능하다.

### 7. 기존 문서와의 중복 여부
`related-but-new-live-wiring-surface`

### 8. 권장 후속 조치

- `quality_dashboard`를 Stage3Context에 명시적으로 싣고 `ctx`만 소비하게 통일하거나,
- 반대로 app-only surface로 유지할 거면 `Stage3Context` 문서/테스트에서 "관측성은 DI 대상이 아님"을 명시해야 한다.
- 최소 회귀로는 `_handle_success()` / `_handle_failure()`에서 `quality_dashboard=None`일 때와 실객체일 때를 각각 잠그는 테스트가 필요하다.

---

## [MLW-T2-02] `constraint_db` fallback이 real app surface에 존재하지 않는 dead/ghost binding이다

### 1. ID
`MLW-T2-02`

### 2. Severity
`P2`

### 3. 현상 요약
`_detect_inventory_gaps()`는 `ctx.world_state`가 비어 있을 때 `getattr(self.app, "constraint_db", None)` fallback을 시도한다. 그러나 현재 `main_a.py`는 `constraint_db`를 app attribute로 공개하지 않고, `Stage3Context`에도 slot이 없다. Stage2 쪽에서는 `ConstraintDB`를 local variable로 생성해 쓰고 끝난다. 즉 Stage3의 fallback은 real app wiring 기준으로는 ghost binding에 가깝다.

### 4. 코드 근거
```python
# modules/core/stage3_orchestrator.py:1748-1754
if not owned:
    _cdb = getattr(self.app, "constraint_db", None)
    if _cdb:
        owned = set(_cdb.get_current_inventory(...))
```

추가 교차 근거:

- `rg -n "constraint_db" main_a.py` -> hit 없음
- `modules/core/stage3_context.py`에는 `constraint_db` slot이 없다
- `modules/core/stage2_orchestrator.py:314`는 `constraint_db = ConstraintDB(self.ctx.current_project)`를 local variable로만 생성한다

### 5. Downstream 영향 경계

- 영향 있음:
  - Stage3 consumer는 존재하지 않는 app surface에 대한 fallback을 품고 있어, 계약 관점에서 죽은 분기를 유지한다.
  - 테스트에서는 `MagicMock` auto-attribute 때문에 이 dead path가 살아 있는 것처럼 보일 수 있다.
- 영향 제한:
  - 현재 실앱에서는 `world_state`가 있으면 main path가 유지되고, `constraint_db` fallback은 대부분 실행되지 않거나 `None`으로 건너뛴다.

### 6. 현재 테스트 근거 또는 테스트 부재

- `_detect_inventory_gaps()` 전용 테스트는 없다.
- `tests/test_stage3_orchestrator.py`의 `app_mock`는 unspecced `MagicMock`이므로, `constraint_db`에 대한 잘못된 접근도 새 child mock을 받아 통과할 수 있다.
- real-project smoke는 `projects/코덱스_테스트/project_data.db` 부재로 5건 전부 skip되어 이 경로를 실행 기반으로 검증하지 못했다.

### 7. 기존 문서와의 중복 여부
`none`

### 8. 권장 후속 조치

- Stage3에서 정말 필요한 surface라면 `main_a.py`와 `Stage3Context`에 명시적으로 올려 계약화해야 한다.
- 아니면 `_detect_inventory_gaps()`의 `constraint_db` fallback을 제거하고 `world_state` 단일 source로 정리하는 편이 낫다.
- 최소 회귀로는 `constraint_db`가 없는 real-app shape에서 `_detect_inventory_gaps()`가 어떤 경로를 타는지 명시 테스트가 필요하다.

---

## [MLW-T2-03] unspecced `MagicMock`과 always-on optional helper가 Stage3 live wiring drift를 false green으로 숨긴다

### 1. ID
`MLW-T2-03`

### 2. Severity
`P2`

### 3. 현상 요약
Stage3 unit/e2e 테스트의 app fixture는 둘 다 `MagicMock()` 기반이며 real app shape를 엄격히 잠그지 않는다. unit fixture는 `pass_rate_monitor`를 항상 `MagicMock()`으로 켜 두고, `adversarial_self_play`/`quality_dashboard`/`constraint_db`는 생략해도 접근 시 child mock이 생긴다. e2e `_build_mock_app()`도 같은 방식이며, 더구나 이번 환경에서는 real-project DB가 없어 5건 전부 skip됐다. 따라서 Stage3 테스트가 green이어도 live wiring drift를 충분히 막는다고 보기 어렵다.

### 4. 코드 근거
```python
# tests/test_stage3_orchestrator.py:18-20
app = MagicMock()

# tests/test_stage3_orchestrator.py:61
app.pass_rate_monitor = MagicMock()

# tests/e2e/test_l3_stage3_smoke.py:94
app = MagicMock()
```

추가 교차 근거:

- `main_a.py:360`, `main_a.py:369`, `main_a.py:370`은 real app의 `adversarial_self_play`, `pass_rate_monitor`, `quality_dashboard` 기본값이 `None`임을 보여 준다.
- synthetic check 결과 bare `MagicMock`에 대한 `Stage3Context.from_app(app)`는 `ctx.pass_rate_monitor`와 `ctx.adversarial_self_play`를 둘 다 truthy `MagicMock`으로 채운다.
- `tests/test_stage3_orchestrator.py:997-1000`의 slot mapping 검증도 `MagicMock` 속성 auto-materialization 영향을 받는다.

### 5. Downstream 영향 경계

- 영향 있음:
  - optional helper의 부재/rename/None 상태가 테스트에서 감지되지 않을 수 있다.
  - `quality_dashboard`, `constraint_db`, `adversarial_self_play`, `pass_rate_monitor` 분기가 real app과 다른 truthy 경로를 탄다.
  - real-project smoke가 skip된 상태에서는 Stage3 live wiring의 실행 근거가 사실상 unit mock에 치우친다.
- 영향 제한:
  - 현재 unit suite 자체는 안정적으로 green이며, callback 이름 오타 같은 일부 회귀는 여전히 잡을 수 있다.

### 6. 현재 테스트 근거 또는 테스트 부재

- `pytest -q tests/test_stage3_orchestrator.py` -> `62 passed`
- `pytest -q tests/e2e/test_l3_stage3_smoke.py -rs` -> `5 skipped`
- skip 사유는 `projects/코덱스_테스트/project_data.db` 부재다. 즉 e2e smoke 파일은 존재하지만, 현재 환경에서는 실행 근거가 아니다.

### 7. 기존 문서와의 중복 여부
`related-but-new-live-wiring-surface`

### 8. 권장 후속 조치

- `MagicMock(spec_set=...)` 또는 최소한 explicit fake app으로 전환해 optional slot을 `None`으로 고정한다.
- `app_mock`와 `_build_mock_app()` 모두 `quality_dashboard`, `constraint_db`, `adversarial_self_play`, `pass_rate_monitor`, `_session_logger`를 의도적으로 세팅하도록 바꿔야 한다.
- e2e smoke는 fixture DB를 저장소에 포함하거나, smoke 미실행을 CI에서 실패로 승격하는 방안이 필요하다.

---

## [MLW-T2-04] `Stage3Context` 계약이 실제 Stage3 consumer surface를 완전히 표현하지 못한다

### 1. ID
`MLW-T2-04`

### 2. Severity
`P3`

### 3. 현상 요약
현재 `main_a.py`의 모든 Stage3 진입점은 호출 직전에 `Stage3Context.from_app(self)`를 다시 만든다. 즉 live wiring 계약의 공인 surface는 사실상 `Stage3Context`가 전부다. 그런데 실제 Stage3 consumer는 `quality_dashboard`, `constraint_db`를 `self.app` side channel로 읽고 있어, `ctx`가 "Stage3에 필요한 surface 전체"라는 전제가 성립하지 않는다.

### 4. 코드 근거
```python
# main_a.py
self._stage3_orch.ctx = Stage3Context.from_app(self)  # 2919 / 3674 / 3789 / 4012

# modules/core/stage3_context.py
__slots__ = (
    "ui", "current_project", "agents", "sys", "state_tracker", "memory",
    "context_advisor", "world_state", "fact_ledger", "adversarial_self_play",
    "preset_registry", "selected_genre", "pass_rate_monitor",
    ...
)
```

교차 근거:

- `quality_dashboard`, `constraint_db`는 `__slots__`에도 없고 `from_app()`에서도 매핑하지 않는다.
- `tests/test_stage3_orchestrator.py:985-1008`는 `from_app_all_slots`를 검증하지만, "consumer가 실제 읽는 모든 surface"까지는 잠그지 못한다.

### 5. Downstream 영향 경계

- 영향 있음:
  - adapter app, injected context, 후속 refactor가 `Stage3Context`만 맞췄다고 생각해도 실제 consumer는 여전히 app side channel에 의존한다.
  - DI 완전성 문서화가 실제 코드와 어긋난다.
- 영향 제한:
  - 현재 `SovereignApp` 경로는 app 객체를 같이 들고 있으므로 즉시 장애로 표면화되지는 않는다.

### 6. 현재 테스트 근거 또는 테스트 부재

- `tests/test_stage3_orchestrator.py:942-1060`는 `Stage3Context` 생성/주입 자체는 잘 덮는다.
- 그러나 `ctx` 계약 바깥 `self.app` 소비면까지 망라하는 contract test는 없다.

### 7. 기존 문서와의 중복 여부
`none`

### 8. 권장 후속 조치

- `Stage3Context`를 SSOT로 유지할 거면 Stage3 consumer가 읽는 surface를 전부 context에 올려야 한다.
- 그렇지 않다면 `Stage3Context`를 "partial DI"로 재정의하고, 어떤 helper는 의도적으로 `self.app`를 사용한다고 문서와 테스트에 남겨야 한다.

---

## Coverage Gap / Open Questions

1. real-project Stage3 smoke는 현재 실행 근거가 아니다.
   - `tests/e2e/test_l3_stage3_smoke.py` 5건 모두 `projects/코덱스_테스트/project_data.db` 부재로 skip됐다.
   - 따라서 이번 재감리의 실행 근거는 unit suite + 정적 대조 + synthetic check에 한정된다.

2. `quality_dashboard.record_validation()`과 `constraint_db` fallback을 직접 잠그는 회귀가 없다.
   - 현재 Stage3 테스트는 retrieval observation 한 경로만 quality dashboard를 직접 검증한다.
   - success/reject validation 기록, `constraint_db=None` 명시 경로는 아직 직접 잠기지 않았다.

3. Stage3의 entrypoint wiring 일관성은 현재 PASS지만, real `SovereignApp` 객체를 쓰는 non-mock integration은 비어 있다.
   - menu/manual/final-close/frontier/one-arc 경로 모두 같은 `from_app(self)` 패턴임은 확인했다.
   - 그러나 실제 app 인스턴스 기반 Stage3 integration test는 이번 환경에서 실행하지 못했다.

## PASS1 -> PASS2 -> PASS3 요약

| 단계 | 총 후보 | 제거 | 확정 |
|------|---------|------|------|
| PASS 1 | 7 | - | - |
| PASS 2 | - | 3 (entrypoint split 없음, callback 이름 드리프트 없음, hybrid head는 기존 control-plane과 중복) | - |
| PASS 3 | - | - | 4 (`MLW-T2-01` ~ `MLW-T2-04`) |

## Severity 합계

| Severity | 건수 |
|----------|------|
| P0 | 0 |
| P1 | 0 |
| P2 | 3 |
| P3 | 1 |
| **합계** | **4** |

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 / skip 상태 포함
- 기존 문서 중복 여부 포함
- PASS1 후보 -> PASS2 제거 -> PASS3 확정 요약 포함
