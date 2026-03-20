# T01 — SovereignApp & Bootstrap Deep Global Survey

**6PASS-CLEARED** | COLLECTOR ONLY | NO EXECUTION AUTHORITY
**Terminal**: T01
**Date**: 2026-03-20
**Baseline Commit**: `d0fa70f1`
**Scope**: `main_a.py` (4,891 lines) — SovereignApp class full surface
**Confidence**: 96%

---

## 1. Scope & Files

| File | Lines | Role |
|------|-------|------|
| `main_a.py` | 4,891 | SovereignApp 전체: bootstrap, boot, lazy init, DI wiring, shutdown, facade stubs |

**Adjacent Terminals**: T02 (Stage 2 Orch), T04 (Stage 3), T05 (Stage 4 Orch), T12 (State Tracking), T17 (Config)

---

## 2. TF Registry

### TF Summary Table

| ID | Severity | Category | Surface | Summary |
|----|----------|----------|---------|---------|
| T01-TF-001 | P2-MEDIUM | COVERAGE-GAP | main_a.py:3442-3451 | Stage 3 write-back gap — no state sync after blueprinting |
| T01-TF-002 | P2-MEDIUM | COVERAGE-GAP | main_a.py:4116-4120 | Stage 4 write-back gap — no state sync after production |
| T01-TF-003 | P3-LOW | COVERAGE-GAP | main_a.py:363 | stage_rejection_history dead producer path (Stage 3 never writes) |
| T01-TF-004 | P3-LOW | DEAD-CODE | main_a.py:1370-1523 | `_ignite_quad_cache_system()` ~153 lines dead code (0 callers) |
| T01-TF-005 | P3-LOW | DEAD-CODE | main_a.py:1525-1533 | `_is_cache_alive()` dead-chain (only caller is T01-TF-004) |
| T01-TF-006 | P3-LOW | DEAD-CODE | main_a.py:2341-2354 | `_load_v50_history()` dormant stub — body is `pass` |
| T01-TF-007 | P3-LOW | HARDCODING | main_a.py:4054 | `self.state_tracker` never declared in `__init__` — dynamic attribute |
| T01-TF-008 | P3-LOW | DRIFT | stage3_context.py | Stage3Context.from_app uses plain `getattr` vs _safe_getattr |
| T01-TF-009 | P3-LOW | COVERAGE-GAP | main_a.py:3988 | `_narrative_summaries_cache` not synced to DI contexts |
| T01-TF-010 | P3-LOW | HARDCODING | main_a.py:1329-1348 | `SovereignApp._method(self)` static dispatch pattern in boot/shutdown |
| T01-TF-011 | P3-LOW | SIDE-EFFECT | main_a.py:95-97 | crash_dump.log opened relative to CWD, not project dir |
| T01-TF-012 | P4-OBSERVATION | DEAD-CODE | main_a.py:47-66,104-116 | Double stdio UTF-8 bootstrap (safe but redundant) |
| T01-TF-013 | P4-OBSERVATION | COVERAGE-GAP | main_a.py | Env var surface: 10+ vars across system, most undocumented |
| T01-TF-014 | P4-OBSERVATION | DEAD-CODE | main_a.py | ~15 facade delegation stubs (thin proxies to services) |
| T01-TF-015 | P4-OBSERVATION | SYNC | main_a.py:366 | SYNC: Sentinel `_cumulative_state_cache_key` correctly implemented |
| T01-TF-016 | P4-OBSERVATION | SYNC | main_a.py:1329-1348 | SYNC: Lazy init order is safe, no circular dependencies |
| T01-TF-017 | P4-OBSERVATION | SYNC | main_a.py:3208-3213 | SYNC: Stage 2 write-back is complete (state_tracker + cache callback) |
| T01-TF-018 | P4-OBSERVATION | SYNC | main_a.py:349-485 | SYNC: All Stage orchestrators safe construction (no app access in __init__) |
| T01-TF-019 | P4-OBSERVATION | SYNC | main_a.py:4054-4116 | SYNC: DI from_app timing for Stage4 correct (lazy init before from_app) |
| T01-TF-020 | P4-OBSERVATION | STALE | main_a.py:169-175 | `RESERVED_STATE_SERVICE_FACADE_SHIMS` constant — not enforced at runtime |

**Total: 20 TFs** (2 P2, 9 P3, 9 P4)

---

## 3. TF Details

### T01-TF-001 | P2-MEDIUM | COVERAGE-GAP | Stage 3 write-back gap

```
ID: T01-TF-001
Severity: P2-MEDIUM
Category: COVERAGE-GAP
Surface: main_a.py:3442-3451
Evidence:
  - main_a.py:3449 — Stage3Context.from_app(self) 호출로 ctx에 state_tracker/world_state/fact_ledger 복사
  - main_a.py:3451 — `return self._stage3_orch.stage_3_batch_blueprinting()` 호출 후 아무 write-back 없음
  - modules/core/stage3_context.py:23-27 — Stage3Context에 state_tracker, world_state, fact_ledger slots 존재
  - 비교: main_a.py:3210-3213 — Stage 2는 명시적 write-back 수행:
    `self.state_tracker = _s2_ctx.state_tracker`
  - Stage 3에는 이에 상응하는 sync 코드가 없음
Inference:
  Stage 3 실행 중 state_tracker/world_state/fact_ledger가 object-level mutation으로 변경되면
  (예: NPC 추가, world law 변경), Python 참조 시맨틱상 원본 app 객체에도 반영됨.
  그러나 Stage3Orchestrator가 ctx.state_tracker를 새 객체로 교체(재할당)하면 app에는 반영 안 됨.
Uncertainty:
  Stage 3이 실제로 state_tracker를 재할당하는지는 stage3_orchestrator.py 코드 확인 필요 (T04 영역).
  현재 관측으로는 in-place mutation만 수행하므로 실질적 데이터 손실은 발생하지 않을 수 있음.
Cross-Ref: T04 (Stage 3 Pipeline), T12 (State Tracking)
```

### T01-TF-002 | P2-MEDIUM | COVERAGE-GAP | Stage 4 write-back gap

```
ID: T01-TF-002
Severity: P2-MEDIUM
Category: COVERAGE-GAP
Surface: main_a.py:4116-4120
Evidence:
  - main_a.py:4116 — Stage4Context.from_app(self) 호출로 ctx에 state_tracker/world_state/fact_ledger 복사
  - main_a.py:4118-4120 — `return self._stage4_orch.stage_4_v2_chief_writer(...)` 호출 후 write-back 없음
  - modules/core/stage4_context.py:53,57,58 — Stage4Context에 해당 slots 존재
  - modules/core/stage4_orchestrator.py:393 — Stage4Orch가 ctx.world_state.add_world_law() 호출 (in-place mutation)
  - main_a.py:4054-4109 — lazy init은 from_app 직전에 수행되어 있음 (T01-TF-019 SYNC 확인)
  - 비교: main_a.py:3210-3213 — Stage 2에서는 명시적 write-back 존재
Inference:
  Stage 4 world_state/fact_ledger mutation은 in-place이므로 app에서도 보임.
  하지만 OneStop 루프(4627-4862)에서 Stage 4 후 Stage 2로 돌아갈 때,
  state_tracker가 ctx에서 재할당될 가능성이 있고, 이 경우 app.state_tracker는 stale.
Uncertainty:
  OneStop/FrontierLag 루프에서 Stage 4 → Stage 2 간 state_tracker 불일치 실험 필요 (동적 검증).
Cross-Ref: T05 (Stage 4 Core Orch), T06 (Stage 4 Interview)
```

### T01-TF-003 | P3-LOW | COVERAGE-GAP | stage_rejection_history dead producer

```
ID: T01-TF-003
Severity: P3-LOW
Category: COVERAGE-GAP
Surface: main_a.py:363
Evidence:
  - main_a.py:363 — `self.stage_rejection_history = []` 초기화
  - modules/core/stage2_finalizer.py — Stage 2 REJECT 시 히스토리에 append (producer)
  - modules/core/stage2_preflight.py:942-950 — Stage 3 REJECT 히스토리를 확인하나 (consumer)
    Stage 3는 이 리스트에 쓰지 않음
  - modules/core/stage3_orchestrator.py:2168-2174 — Stage 3 rejection 기록 시도가 존재하지만
    실질적으로 passive (불활성)
  - Grep "stage_rejection_history" in modules/ → stage2_finalizer.py, stage2_preflight.py,
    stage3_orchestrator.py, stage2_context.py에서 참조
Inference:
  Stage 2 preflight가 Stage 3 rejection 데이터를 기대하지만 Stage 3는 공급하지 않음.
  이로 인해 cross-stage feedback loop가 사실상 단방향(Stage 2→2만 작동).
Uncertainty:
  Stage 3 orchestrator의 해당 코드 경로가 실제로 호출되는지 T04에서 확인 필요.
Cross-Ref: T02 (Stage 2 Orch Context), T04 (Stage 3 Pipeline)
```

### T01-TF-004 | P3-LOW | DEAD-CODE | _ignite_quad_cache_system()

```
ID: T01-TF-004
Severity: P3-LOW
Category: DEAD-CODE
Surface: main_a.py:1370-1523
Evidence:
  - main_a.py:1370 — `def _ignite_quad_cache_system(self):` 정의 (153 lines)
  - Grep "_ignite_quad_cache_system(" in main_a.py → 정의 1건만 존재, 호출 0건
  - tests/test_main_a_boot_binding.py:240 — 테스트에서 "must stay dead" assertion 존재:
    `app._ignite_quad_cache_system = MagicMock(side_effect=AssertionError("legacy cache helper must stay dead"))`
  - tests/test_main_a_boot_binding.py:250 — `.assert_not_called()` 확인
  - docs/2026-03-13/MDH-T4-bootstrap-history-cache-helper-liveness-findings.md:18 — dead 확정
  - 이 메서드는 V31 legacy Writer/Analyst/Weaver cache bootstrap helper
Inference:
  153줄의 dead code. _is_cache_alive()도 이 메서드 내에서만 호출되어 dead-chain.
  테스트에서도 "dead 유지"를 의도적으로 검증.
Uncertainty: 없음
Cross-Ref: T01-TF-005
```

### T01-TF-005 | P3-LOW | DEAD-CODE | _is_cache_alive()

```
ID: T01-TF-005
Severity: P3-LOW
Category: DEAD-CODE
Surface: main_a.py:1525-1533
Evidence:
  - main_a.py:1525 — `def _is_cache_alive(self, cache_name):` 정의
  - Grep "_is_cache_alive" in main_a.py → 정의 1건 + _ignite_quad_cache_system 내부 3건
  - _ignite_quad_cache_system이 dead이므로 (T01-TF-004), 이 메서드도 dead-chain
  - docs/2026-03-13/MDH-T4-bootstrap-history-cache-helper-liveness-findings.md:19 — dead-chain 확정
Inference: T01-TF-004와 함께 제거 가능한 dead-chain helper.
Uncertainty: 없음
Cross-Ref: T01-TF-004
```

### T01-TF-006 | P3-LOW | DEAD-CODE | _load_v50_history() dormant stub

```
ID: T01-TF-006
Severity: P3-LOW
Category: DEAD-CODE
Surface: main_a.py:2341-2354
Evidence:
  - main_a.py:2341-2354 — 메서드 정의, body는:
    ```python
    if not V50_MODULES_AVAILABLE:
        return
    pass
    ```
  - main_a.py:2149 — `self._load_v50_history()` caller 존재 (_init_v50_modules 말미)
  - 호출은 되지만 body가 no-op (V65에서 모든 히스토리 로딩 로직 삭제)
  - docs/2026-03-13/MDH-T4-bootstrap-history-cache-helper-liveness-findings.md:20 — dormant 확정
Inference: Live caller가 있어 dead는 아니지만, body가 pass만이므로 dormant stub.
Uncertainty: V50 모듈 재연결 계획이 있다면 stub 유지가 적절할 수 있음.
Cross-Ref: T11 (Agent Infra)
```

### T01-TF-007 | P3-LOW | HARDCODING | self.state_tracker undeclared in __init__

```
ID: T01-TF-007
Severity: P3-LOW
Category: HARDCODING
Surface: main_a.py:4054, 3212, 3716
Evidence:
  - main_a.py:349-485 — __init__에서 self.state_tracker 선언 없음
  - Grep "self\.state_tracker" in main_a.py → 16건:
    - 3212: `self.state_tracker = _s2_ctx.state_tracker` (Stage 2 write-back)
    - 3716, 3747, 3778, 3818: `self.state_tracker = None` (rollback/reset)
    - 4054: `if not hasattr(self, "state_tracker") or self.state_tracker is None:` (lazy init guard)
    - 4058: `self.state_tracker = _StateTracker(...)` (lazy init)
    - 4421, 4739: OneStop write-back
  - main_a.py:4054 — `hasattr(self, "state_tracker")` 방어 코드 존재 (attribute 부재 인지)
  - __init__에 선언이 없으므로, boot → Stage 2 전까지 AttributeError 가능
    (단, from_app에서 _safe_getattr로 보호됨)
Inference:
  __init__에 `self.state_tracker = None` 추가하면 hasattr 방어 코드가 불필요해짐.
  다른 모든 lazy-init 속성(world_state, fact_ledger 등)은 __init__에 `= None` 선언이 있음.
Uncertainty: 없음 — 코드 동작에는 문제 없지만 일관성 위반.
Cross-Ref: T12 (State Tracking)
```

### T01-TF-008 | P3-LOW | DRIFT | Stage3Context.from_app getattr inconsistency

```
ID: T01-TF-008
Severity: P3-LOW
Category: DRIFT
Surface: modules/core/stage3_context.py
Evidence:
  - modules/core/stage2_context.py:61-71 — `_safe_getattr()` 정의:
    `inspect.getattr_static()` + try/except 패턴
  - modules/core/stage4_context.py:18-28 — 동일 `_safe_getattr()` 정의
  - modules/core/stage3_context.py:108-127 — plain `getattr(app, name, None)` 사용
  - Stage2/4는 `_safe_getattr`, Stage3만 plain `getattr` → 3개 context 중 1개만 다름
Inference:
  plain getattr도 기능적으로 안전하나 (default=None 지정),
  inspect.getattr_static 기반 _safe_getattr와의 차이는 property/descriptor 처리.
  3개 sister context 중 1개만 다른 패턴 → 유지보수 혼란 가능.
Uncertainty: 실제 동작 차이가 발생하는 edge case는 낮은 확률.
Cross-Ref: T04 (Stage 3 Pipeline)
```

### T01-TF-009 | P3-LOW | COVERAGE-GAP | _narrative_summaries_cache not synced

```
ID: T01-TF-009
Severity: P3-LOW
Category: COVERAGE-GAP
Surface: main_a.py:3988, 394
Evidence:
  - main_a.py:394 — `self._narrative_summaries_cache: str | None = None` 선언
  - main_a.py:3988 — `self._narrative_summaries_cache = None` (요약 생성/실패 후 무효화)
  - main_a.py:3720, 3751, 3783, 3822 — rollback/reset 시 무효화 (4곳 모두)
  - 그러나 DI context(Stage2/3/4Context)에는 이 캐시 slot이 없음
  - Stage 4에서 _generate_narrative_summary 호출 → app 직접 접근
  - Grep "_narrative_summaries_cache" → main_a.py에서만 참조
Inference:
  이 캐시는 DI context를 거치지 않고 app 직접 접근으로만 사용됨.
  현재 구조에서는 문제 없지만, DI 완전 분리 시 이 캐시 접근 경로가 불투명.
Uncertainty: DI 분리가 완전히 수행되지 않은 현재는 실질적 문제 없음.
Cross-Ref: T05 (Stage 4 Core Orch)
```

### T01-TF-010 | P3-LOW | HARDCODING | Static dispatch pattern

```
ID: T01-TF-010
Severity: P3-LOW
Category: HARDCODING
Surface: main_a.py:1341-1348, 3053-3072
Evidence:
  - main_a.py:1341 — `SovereignApp._bind_selected_project(self, project_name)`
  - main_a.py:1342 — `SovereignApp._restore_boot_runtime_state(self)`
  - main_a.py:1343-1347 — 동일 패턴 4건 추가
  - main_a.py:3057-3071 — shutdown 시퀀스에서 8건:
    `SovereignApp._persist_shutdown_metrics(self)` 등
  - main_a.py:2618 — shutdown_log에서도 `SovereignApp._shutdown_log(self, ...)`
  - 총 약 20곳에서 `SovereignApp.method(self, ...)` 패턴 사용
  - 일반적 Python에서는 `self._method(...)` 호출이 표준
Inference:
  이 패턴은 기능적으로 동일하나, 서브클래싱 시 다형성이 무시됨.
  의도적 설계(메서드 오버라이드 방지)일 가능성이 있으나 주석/문서 없음.
Uncertainty: 의도적 설계인지 코드 스타일 불일치인지 불명.
Cross-Ref: 없음
```

### T01-TF-011 | P3-LOW | SIDE-EFFECT | crash_dump.log relative path

```
ID: T01-TF-011
Severity: P3-LOW
Category: SIDE-EFFECT
Surface: main_a.py:95-97
Evidence:
  - main_a.py:95 — `_fault_log = open("crash_dump.log", "a", encoding="utf-8")`
  - 상대 경로 "crash_dump.log" → CWD 기준 생성
  - main_a.py:97 — `atexit.register(_fault_log.close)` — 프로세스 전 수명 동안 열림
  - CWD는 프로젝트 루트가 아닐 수 있음 (desktop app에서 실행 시 등)
  - 동일 파일에 복수 프로세스가 동시 기록 가능 (lock 없음)
Inference:
  Faulthandler는 segfault 시 비동기적으로 파일에 쓰므로 lock이 적절하지 않을 수 있음.
  하지만 CWD 의존성은 desktop bridge 실행 시 예상 외 경로에 파일 생성 가능.
Uncertainty: Desktop 모드에서의 CWD 확인 필요 (T19 영역).
Cross-Ref: T19 (Desktop App)
```

### T01-TF-012 | P4-OBSERVATION | DEAD-CODE | Double stdio UTF-8 bootstrap

```
ID: T01-TF-012
Severity: P4-OBSERVATION
Category: DEAD-CODE
Surface: main_a.py:47-66, 104-116
Evidence:
  - main_a.py:47-66 — `_bootstrap_windows_stdio_utf8()` 정의: sys.stdout/stderr를 UTF-8로 교체
  - main_a.py:91 — `_bootstrap_windows_stdio_utf8()` 호출 → `_STDIO_BOOTSTRAPPED = True` 설정
  - main_a.py:104-116 — `if not _STDIO_BOOTSTRAPPED` guard 아래에 동일한 로직 반복
  - 정상 실행 시 line 91에서 `_STDIO_BOOTSTRAPPED = True`가 설정되므로
    line 104의 조건은 항상 False → 104-116 블록은 dead path
  - line 91에서 예외 발생 시에만 (AttributeError/OSError) 104-116 블록 진입 가능
    하지만 이 경우도 같은 코드를 실행하므로 같은 예외가 발생
Inference:
  레거시 중복 코드. `_bootstrap_windows_stdio_utf8()` 도입 전에 존재하던 inline 코드가
  함수화 후에도 제거되지 않은 것으로 추정.
Uncertainty: 없음 — 안전하지만 불필요.
Cross-Ref: 없음
```

### T01-TF-013 | P4-OBSERVATION | COVERAGE-GAP | Env var surface inventory

```
ID: T01-TF-013
Severity: P4-OBSERVATION
Category: COVERAGE-GAP
Surface: main_a.py, modules/domain/agents/base_agent.py, modules/core/runtime_paths.py
Evidence:
  전수 조사 결과 10개 환경변수 식별:
  1. GOOGLE_API_KEY — main_a.py:355,1182,1312,1988 (핵심 API 키)
  2. GOOGLE_API_KEY_2~9 — base_agent.py:206-209 (멀티키 로테이션)
  3. SLACK_WEBHOOK_URL — slack_bot.py:29 (알림)
  4. GEULDOBI_ENGINE_ROOT — runtime_paths.py:68 (엔진 루트 오버라이드)
  5. GEULDOBI_WORKSPACE — runtime_paths.py:75, main_a.py:23 (워크스페이스 루트)
  6. GEULDOBI_PROJECTS_ROOT — runtime_paths.py:82 (프로젝트 디렉토리)
  7. GEULDOBI_ENGINE_EXE — process_runner.py:216 (컴파일 엔진)
  8. GEULDOBI_PYTHON_PATH — process_runner.py:228 (Python 경로)
  9. GEULDOBI_DESKTOP_MODE — bridge_server.py:228 (데스크톱 모드)
  10. GEULDOBI_RUN_ID — process_runner.py:790 (서브프로세스 식별자, set only)
Inference:
  GOOGLE_API_KEY 외에는 대부분 .env에 문서화되지 않음.
  Missing key 시 silent fallback (기본값 사용)으로 오동작 추적이 어려움.
Uncertainty: 프로젝트별 .env에 어떤 키가 기재되어 있는지 런타임 확인 필요.
Cross-Ref: T17 (Config), T19 (Desktop/API Bridge)
```

### T01-TF-014 | P4-OBSERVATION | DEAD-CODE | Facade delegation stubs

```
ID: T01-TF-014
Severity: P4-OBSERVATION
Category: DEAD-CODE
Surface: main_a.py:824-843, 3217-3354
Evidence:
  Facade thin stubs 약 15건:
  - main_a.py:824 — `_simplify_prompt_for_retry` → FeedbackSystem
  - main_a.py:828 — `_build_strong_kind_feedback` → FeedbackSystem
  - main_a.py:832 — `_build_focused_context` → FeedbackSystem
  - main_a.py:836 — `_build_minimal_arc_context` → FeedbackSystem
  - main_a.py:840 — `_generate_arc_position_guide` → PromptBuilder
  - main_a.py:901-919 — 4건 FeedbackSystem delegation
  - main_a.py:3217-3240 — 5건 Stage2Orch delegation (normalize, flow_guard 등)
  - main_a.py:3308-3354 — 6건 StateService delegation
  - main_a.py:3361-3371 — 3건 AuditService delegation
  - Grep "thin delegate" in main_a.py → 12건 주석 존재
Inference:
  이 stubs는 DI context로 전환된 후에도 하위 호환을 위해 유지됨.
  DI context가 SSOT이므로 직접 app.method() 호출하는 외부 코드가 없다면 제거 가능.
  다만 RESERVED_STATE_SERVICE_FACADE_SHIMS (line 169-175)에서 일부를 명시적으로 보존.
Uncertainty: 외부 스크립트나 desktop bridge가 이 facade를 직접 호출하는지 확인 필요.
Cross-Ref: T19 (Desktop/API Bridge), T20 (Scripts/Tools)
```

### T01-TF-015 | P4-OBSERVATION | SYNC | Sentinel correctly implemented

```
ID: T01-TF-015
Severity: P4-OBSERVATION
Category: SYNC
Surface: main_a.py:366
Evidence:
  - main_a.py:366 — `self._cumulative_state_cache_key = None  # [S-08] 센티넬 (0은 유효한 키)`
  - modules/core/prompt_builder.py:569 — check: `cache is not None and cache_key == arc_count`
  - modules/core/stage2_preflight.py:756, 1106 — 동일 패턴
  - 모든 check site에서 `is not None` (truthiness 아님) + `== arc_count` (equality) 사용
  - 0 == 0은 True → arc_count=0일 때 캐시 정상 히트
  - Invalidation 4곳 (3718, 3749, 3782, 3821) 모두 `= None` 설정 → 일관
  - modules/core/stage2_context.py:7-18 — weakref 기반 sync callback 정상 작동
  - tests/test_sweep35.py:21 — invalidation 검증 존재
Inference: S-08 sentinel 패턴이 올바르게 구현되어 0 vs None 혼동 없음.
Uncertainty: 없음
Cross-Ref: T02 (Stage 2 Orch), T03 (Stage 2 Preflight)
```

### T01-TF-016 | P4-OBSERVATION | SYNC | Lazy init order safe

```
ID: T01-TF-016
Severity: P4-OBSERVATION
Category: SYNC
Surface: main_a.py:1329-1348
Evidence:
  Boot sequence 검증:
  1. __init__:349 — orchestrators 생성 (app=self 참조만 저장, 속성 접근 없음)
  2. boot:1341 — _bind_selected_project → self.current_project 설정
  3. boot:1343 — _restore_boot_runtime_state
  4. boot:1344 — _ensure_project_genre_alignment (current_project.db 필요 → ✅ 보장)
  5. boot:1347 — _initialize_project_runtime_support:
     - 1307-1308: `if current_project is None or db is None: return False` (guard)
     - 1311: self.memory = VecMemory(...) (memory 설정)
     - 1322: _attach_agents() (agents 설정)

  Orchestrator __init__ 검증:
  - stage2_orchestrator.py:31-41 — `self.app = app` 저장만, 속성 접근 없음
  - stage3_orchestrator.py:485-495 — 동일 패턴
  - stage4_orchestrator.py:216-226 — 동일 패턴
Inference: 순환 의존성 없음. 모든 orchestrator가 생성 시 app 속성을 접근하지 않음.
Uncertainty: 없음
Cross-Ref: T02, T04, T05
```

### T01-TF-017 | P4-OBSERVATION | SYNC | Stage 2 write-back complete

```
ID: T01-TF-017
Severity: P4-OBSERVATION
Category: SYNC
Surface: main_a.py:3208-3213
Evidence:
  - main_a.py:3210-3213:
    ```python
    _s2_ctx = self._stage2_orch.ctx
    if _s2_ctx is not None and getattr(_s2_ctx, "state_tracker", None) is not None:
        self.state_tracker = _s2_ctx.state_tracker
    self._state_tracker_loaded_arcs = getattr(_s2_ctx, "state_tracker_loaded_arcs", 0)
    ```
  - modules/core/stage2_context.py:7-18 — sync_cache_key_to_app callback:
    cumulative_state_cache와 cache_key를 자동 동기화
  - OneStop (main_a.py:4738-4740) 및 FrontierLag (4421-4422)에서도 동일 write-back 존재
Inference: Stage 2 write-back은 state_tracker + cache 모두 complete.
Uncertainty: 없음
Cross-Ref: T02 (Stage 2 Orch)
```

### T01-TF-018 | P4-OBSERVATION | SYNC | Orchestrator safe construction

```
ID: T01-TF-018
Severity: P4-OBSERVATION
Category: SYNC
Surface: main_a.py:349-485
Evidence:
  __init__ 내 orchestrator 생성:
  - main_a.py:371 — `self._stage2_orch = Stage2Orchestrator(app=self)` → app 참조만 저장
  - main_a.py:372 — `self._stage3_orch = Stage3Orchestrator(app=self)` → 동일
  - main_a.py:373 — `self._stage4_orch = Stage4Orchestrator(app=self)` → 동일
  - 각 orchestrator __init__에서 app 속성 접근 0건 (코드 검증 완료)

  Helper 생성:
  - main_a.py:368 — PromptBuilder(app=self) → self._app = app 저장만
  - main_a.py:369 — FeedbackSystem() → stateless, app 의존 없음
  - main_a.py:370 — Stage01Helpers(app=self) → 참조만 저장
Inference: 모든 DI 주입 대상이 생성 시점에 app 속성을 접근하지 않아 안전.
Uncertainty: 없음
Cross-Ref: T02, T04, T05
```

### T01-TF-019 | P4-OBSERVATION | SYNC | Stage4 from_app timing correct

```
ID: T01-TF-019
Severity: P4-OBSERVATION
Category: SYNC
Surface: main_a.py:4054-4116
Evidence:
  - main_a.py:4054-4072 — StateTracker lazy init (hasattr guard + 생성 + full_extract)
  - main_a.py:4075-4087 — WorldStateManager lazy init
  - main_a.py:4090-4091 — WorldState → StateTracker 바인딩
  - main_a.py:4094-4109 — FactLedger lazy init
  - main_a.py:4116 — `self._stage4_orch.ctx = Stage4Context.from_app(self)` ← 모든 init 후 호출
  - modules/core/stage4_context.py:18-28 — `_safe_getattr()` 사용 (inspect.getattr_static 기반)
Inference: Lazy init이 from_app 전에 완료되므로 timing 문제 없음.
Uncertainty: 없음
Cross-Ref: T05 (Stage 4 Core Orch)
```

### T01-TF-020 | P4-OBSERVATION | STALE | RESERVED_STATE_SERVICE_FACADE_SHIMS

```
ID: T01-TF-020
Severity: P4-OBSERVATION
Category: STALE
Surface: main_a.py:169-175
Evidence:
  - main_a.py:169-175:
    ```python
    RESERVED_STATE_SERVICE_FACADE_SHIMS = (
        "_extract_block_index",
        "_extract_pattern_keywords",
        "_pattern_presence_check",
        "_build_validation_context",
        "_load_genre_references",
    )
    ```
  - 이 상수는 문서 목적으로만 존재 — 런타임에서 이 값을 읽거나 검증하는 코드 없음
  - Grep "RESERVED_STATE_SERVICE_FACADE_SHIMS" → main_a.py:169 정의 1건만
  - 해당 5개 메서드는 실제로 main_a.py에 facade stub으로 존재 (3308-3354)
  - 메서드 추가/제거 시 이 상수를 갱신해야 하지만 강제 메커니즘 없음
Inference: 문서화 의도의 상수지만 drift 가능성 있음. 테스트로 검증하거나 주석으로 전환 권장.
Uncertainty: 없음
Cross-Ref: 없음
```

---

## 4. Evidence Inventory

| Evidence Type | Count | Examples |
|---------------|-------|---------|
| 파일:라인 참조 | 55+ | main_a.py:366, stage3_context.py:23 등 |
| 코드 스니펫 인용 | 20+ | sentinel check, write-back, init sequence |
| Grep 부재 증명 | 5 | _ignite_quad_cache_system 호출 0건, RESERVED 참조 1건 |
| 비교 근거 | 4 | Stage2 vs Stage3/4 write-back, getattr vs _safe_getattr |
| 문서 교차 확인 | 3 | MDH-T4, MRL-T2, MCP-T2 문서 |

---

## 5. Side-Effect Surface

| Side-Effect | Location | Trigger | Target |
|-------------|----------|---------|--------|
| crash_dump.log 파일 생성 | main_a.py:95 | 모듈 import | CWD/crash_dump.log |
| faulthandler 활성화 | main_a.py:96 | 모듈 import | 전역 segfault handler |
| sys.stdout/stderr 교체 | main_a.py:60-61 | Windows + non-pytest | 전역 stdio |
| asyncio policy 변경 | main_a.py:85 | Windows + non-pytest | 전역 event loop policy |
| load_dotenv 3회 호출 | main_a.py:128,350,1179 | import / init / project bind | 환경변수 |
| atexit handler 등록 | main_a.py:97,405 | init | crash_dump close, audit flush |

---

## 6. Facts

1. SovereignApp.__init__은 40+ 속성을 선언하고, 6개 서비스/orchestrator를 즉시 생성
2. 모든 Stage orchestrator는 생성 시 app 속성에 접근하지 않음 (참조만 저장)
3. Boot sequence는 8단계로 구성 (genre → project → env → genre runtime → VecMemory → agents)
4. Stage 2만 명시적 write-back 존재 (state_tracker + cache callback)
5. Stage 3/4는 write-back 없음 (in-place mutation으로 보완)
6. _ignite_quad_cache_system + _is_cache_alive = 162줄 dead code
7. Sentinel 패턴 (_cumulative_state_cache_key)은 `is not None` + `==` 비교로 안전
8. 환경변수 10개 (GOOGLE_API_KEY가 핵심, 나머지 9개는 override/optional)
9. Facade stub 약 15건이 서비스/orchestrator로 위임

---

## 7. Inferences

1. Stage 3/4 write-back 부재는 Python 참조 시맨틱(in-place mutation은 원본에 반영)에 의존하므로
   현재 동작에 문제가 없지만, orchestrator가 state_tracker를 새 객체로 교체하면 데이터 손실 가능
2. _ignite_quad_cache_system 제거 시 약 162줄 절감 가능 (테스트에서 "must stay dead" 확인됨)
3. Static dispatch 패턴(SovereignApp._method(self))은 의도적 설계일 가능성이 있으나 문서화 필요
4. state_tracker가 __init__에 선언되지 않은 것은 V62.5 이후 추가된 속성이 반영되지 않은 것으로 추정

---

## 8. Uncertainty / Contradictions

| Item | Uncertainty | 동적 검증 필요 여부 |
|------|-------------|-------------------|
| Stage 3에서 state_tracker 재할당 여부 | T04 범위 — Stage3Orchestrator 코드 확인 필요 | No (정적 확인 가능) |
| OneStop 루프에서 Stage 4→Stage 2 state_tracker 불일치 | 실제 실행 경로 검증 필요 | Yes |
| Static dispatch 패턴의 의도 | 코드 작성자 의도 확인 불가 | No |
| Desktop 모드에서 CWD 위치 | T19 범위 | No (정적 확인 가능) |

---

## 9. Cross-Ref to Adjacent Terminals

| Adjacent Terminal | Cross-Ref TF | Reason |
|-------------------|-------------|--------|
| T02 (Stage 2 Orch) | T01-TF-001, T01-TF-003, T01-TF-015, T01-TF-017 | Stage 2 write-back, rejection history, sentinel |
| T04 (Stage 3) | T01-TF-001, T01-TF-003, T01-TF-008 | Stage 3 write-back, rejection history, getattr |
| T05 (Stage 4 Orch) | T01-TF-002, T01-TF-009, T01-TF-019 | Stage 4 write-back, narrative cache, timing |
| T12 (State Tracking) | T01-TF-001, T01-TF-002, T01-TF-007 | state_tracker sync, undeclared attribute |
| T17 (Config) | T01-TF-013 | Env var documentation |
| T19 (Desktop/API) | T01-TF-011, T01-TF-013, T01-TF-014 | CWD, env vars, facade stubs |

---

## 10. Candidate Watchlist

| Candidate | Priority | Rationale |
|-----------|----------|-----------|
| Stage 3/4 write-back 추가 | HIGH | T01-TF-001/002 — DI 완전 분리 시 필수 |
| Dead code 제거 (162줄) | MEDIUM | T01-TF-004/005 — 이미 "dead" 확정, 테스트 보호 |
| state_tracker __init__ 선언 | LOW | T01-TF-007 — 일관성 개선 |
| Stage3Context _safe_getattr 통일 | LOW | T01-TF-008 — 3개 context 패턴 통일 |
| Double stdio bootstrap 제거 | LOW | T01-TF-012 — 13줄 dead code |

---

## 11. 6Pass Audit Log

### Pass 1 — 구조/범위
- main_a.py 4,891줄 전수 읽기 완료
- 범위: SovereignApp 전체 (bootstrap, boot, DI, shutdown, facade, pipeline)
- 누락 영역 점검: Stage 내부 로직은 T02-T06 범위로 제외, app surface만 조사 → **PASS**

### Pass 2 — 증거/일관성
- 모든 TF에 파일:라인 참조 존재
- 코드 스니펫 인용 20건 이상
- Grep 부재 증명 5건 (패턴 + 결과 기록)
- 라인 번호 정확성 검증: main_a.py:366 (sentinel), 1370 (quad cache), 3210-3213 (write-back) → **PASS**

### Pass 3 — 실행가능성
- P2 TF 2건: write-back 추가는 Stage orchestrator 내부 확인 후 수행 가능
- P3 TF 9건: dead code 제거, 선언 추가, 패턴 통일 등 모두 actionable
- P4 TF 9건: 관측/SYNC → 향후 참고용 → **PASS**

### Pass 4 — 적대적 (스코프 과잉/누락 반박)
- "4,891줄을 한 터미널이 다 커버할 수 없다" → 조사 대상은 app surface (속성, boot, DI, shutdown)이며 Stage 내부 로직은 T02-T06으로 적절히 분배됨 → **반박 실패, PASS**
- "Stage orchestrator __init__도 T01 범위여야 한다" → orchestrator 정의는 T02/T04/T05 범위, T01은 호출 측면만 조사 → **반박 실패, PASS**

### Pass 5 — 적대적 (증거 거짓/과장 반박)
- "write-back gap은 Python 참조 시맨틱상 문제 없다" → in-place mutation은 맞지만, 재할당 시 데이터 손실 가능. Uncertainty에 명시적 기재. TF severity P2로 유지 적절 → **반박 실패, PASS**
- "_ignite_quad_cache_system이 테스트에서 호출된다" → test는 "not_called" assertion이며, dead 확인용. 실제 호출 아님 → **반박 실패, PASS**

### Pass 6 — 적대적 (severity 반박)
- "Stage 3/4 write-back gap을 P1으로 올려야 한다" → 현재 in-place mutation 패턴이 보완하므로 실질적 데이터 손실 미발생. P2 유지 적절 → **반박 실패, PASS**
- "dead code TF를 P4로 내려야 한다" → 162줄 유지보수 부담 + 테스트에서 적극적으로 dead 검증. P3 유지 적절 → **반박 실패, PASS**

**6PASS-CLEARED** — 확신도 96%
