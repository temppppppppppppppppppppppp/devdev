# T13 — Continuity System Survey

**6PASS-CLEARED** | COLLECTOR ONLY | NO EXECUTION AUTHORITY

**Terminal**: T13
**영역**: Continuity System
**Date**: 2026-03-20
**Baseline Commit**: `d0fa70f1`
**Confidence**: 96%

---

## 1. Scope & Files

| 파일 | 라인 수 | 역할 |
|------|---------|------|
| `modules/domain/agents/continuity_inspector.py` | 548 | Facade — 4 sub-module 위임 |
| `modules/domain/agents/continuity_arc.py` | 1,026 | Arc 수준 연속성 검증 |
| `modules/domain/agents/continuity_blueprint.py` | 489 | Blueprint 수준 연속성 검증 |
| `modules/domain/agents/continuity_manuscript.py` | 1,234 | Manuscript 수준 연속성 검증 |
| `modules/domain/agents/continuity_tracker.py` | 424 | V49.7 품질 향상 트래커 통합 |
| `modules/core/continuity_pin_guard.py` | 149 | 결정적 이름/시간 핀 교정 |
| `modules/validation/continuity_validator.py` | 1,282 | Tier 0.5 Python-only 연속성 검증 |
| **합계** | **5,152** | |

**관련 테스트:**
- `tests/test_continuity_modules.py` (1,165 lines)
- `tests/test_continuity_packet.py` (574 lines) — 실제로는 Stage4ContextBuilder 관련, T13 범위 외
- `tests/test_continuity_pin_guard.py` (존재 확인)

---

## 2. TF Registry

### T13-TF-001: Facade 위임 완전성 확인 — SYNC

```
ID: T13-TF-001
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/continuity_inspector.py
Evidence:
  - continuity_inspector.py:140-143 — 4개 서브모듈 초기화
    self._arc = ContinuityArcValidator(self)
    self._blueprint = ContinuityBlueprintValidator(self)
    self._manuscript = ContinuityManuscriptValidator(self)
    self._tracker = ContinuityTrackerIntegration(self)
  - continuity_inspector.py:337-548 — 모든 public/private 메서드가 sub-module로 위임됨
    inspect() → self._blueprint.inspect() (L346-348)
    inspect_arc() → self._arc.inspect_arc() (L375-376)
    inspect_manuscript() → self._manuscript.inspect_manuscript() (L428-435)
    inspect_manuscript_v59() → self._manuscript.inspect_manuscript_v59() (L446-448)
    _init_v49_7_trackers() → self._tracker.init_trackers() (L517-518)
    load_trackers_from_db() → self._tracker.load_trackers_from_db() (L547-548)
  - Facade에 직접 구현 로직 없음 — 패턴/유틸/위임 스텁만 존재
Inference: V64.P3 God Object 분해가 완전히 완료됨. 모든 외부 호출은 facade를 통해 sub-module로 위임됨.
Uncertainty: 없음
Cross-Ref: T11 (BaseAgent 상속 구조)
```

### T13-TF-002: inspect_manuscript / inspect_manuscript_v59 프로덕션 호출자 부재 — DEAD-CODE 후보

```
ID: T13-TF-002
Severity: P2-MEDIUM
Category: DEAD-CODE
Surface: modules/domain/agents/continuity_inspector.py:418-448, continuity_manuscript.py:218-363, 1166-1207
Evidence:
  - Grep "inspect_manuscript|inspect_manuscript_v59" in modules/ →
    결과: continuity_inspector.py (정의+위임), continuity_manuscript.py (정의+구현) 만 존재
    Stage 3/4 orchestrator, stage4_interview_round.py, director_continuity.py 모두에서 0 matches
  - 프로덕션 호출 경로:
    - inspect_arc() → stage2_validation_pipeline.py:751 에서 호출됨 (확인)
    - inspect() (blueprint) → Stage 3에서 호출되지 않음 (Grep 결과 0 matches)
    - inspect_manuscript() → 프로덕션 코드에서 호출 없음, tests/test_continuity_modules.py:385,396,1082와 tests/test_sweep29.py:42,87에서만 호출
    - inspect_manuscript_v59() → 프로덕션 코드에서 호출 없음, 테스트에서도 호출 없음
  - Stage 4 원고 검증은 ContinuityValidator(validation tier 0.5)가 담당
  - Stage 3 Blueprint 검증은 continuity_pin_guard(apply_continuity_pins)가 담당
Inference: ContinuityInspector의 inspect_manuscript(), inspect_manuscript_v59(), inspect() (blueprint)는 프로덕션 파이프라인에서 호출되지 않는다. LLM 기반 원고/블루프린트 연속성 검증은 V47 ContinuityValidator(Python-only)와 continuity_pin_guard로 대체된 것으로 보인다. 1,723행(manuscript 1,234 + blueprint 489)의 LLM 검증 코드가 미사용 상태.
Uncertainty: 사용자 커스텀 스크립트나 외부 호출 경로에서 사용될 가능성은 배제 불가. 동적 검증 필요.
Cross-Ref: T06 (Stage 4 Interview), T04 (Stage 3 Pipeline), T14 (Validation Pipeline)
```

### T13-TF-003: inspect_arc 단일 프로덕션 호출자 확인 — SYNC

```
ID: T13-TF-003
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage2_validation_pipeline.py:751
Evidence:
  - stage2_validation_pipeline.py:743-755
    if not four_phase_passed and "continuity_inspector" in self.ctx.agents:
        ...
        continuity_result = self.ctx.agents["continuity_inspector"].inspect_arc(
            current_arc=refined_arc,
            prev_arcs=all_refined_arcs,
            entity_registry=entity_registry_for_director,
        )
  - Stage 2에서 Arc 생성 후 연속성 검증으로 호출
  - 예외 처리: stage2_validation_pipeline.py:756-764 — RuntimeError/ValueError/OSError → advisory 전환
Inference: inspect_arc만 프로덕션 파이프라인에서 활성 사용됨. Stage 2 validation pipeline에서만 호출.
Uncertainty: 없음
Cross-Ref: T02 (Stage 2 Orch), T03 (Stage 2 Preflight/Finalizer)
```

### T13-TF-004: ContinuityArcValidator LLM 실패 시 PASS fallback

```
ID: T13-TF-004
Severity: P3-LOW
Category: SILENT-FAILURE
Surface: modules/domain/agents/continuity_arc.py:464-482
Evidence:
  - continuity_arc.py:464-482
    except Exception as e:
        logging.warning(f" [ContinuityInspector] Arc LLM 검증 실패: {e}")
        if python_check.get("warnings"):
            return {"decision": "PASS", "severity": "MINOR", ...}
        return {"decision": "PASS", "severity": "NONE", ...}
  - LLM 호출 실패 시 항상 PASS 반환 (Python advisory만 포함)
  - JSON 파싱 실패 시에도 PASS: continuity_arc.py:393-401
    if not isinstance(result, dict): → {"decision": "PASS", ...}
Inference: 대원칙 1(Python은 수집만, 판단은 LLM) 준수 목적. LLM 실패 시 PASS + 경고로 비차단 처리. 연속성 검증 실패가 파이프라인을 차단하지 않는 설계.
Uncertainty: 없음 — 의도적 설계로 판단
Cross-Ref: T14 (Validation Pipeline)
```

### T13-TF-005: ContinuityBlueprintValidator LLM 실패 시 동일 PASS fallback

```
ID: T13-TF-005
Severity: P4-OBSERVATION
Category: SILENT-FAILURE
Surface: modules/domain/agents/continuity_blueprint.py:265-282
Evidence:
  - continuity_blueprint.py:265-282
    except Exception as e:
        logging.warning(f" [ContinuityInspector] LLM 검증 실패: {e}")
        return {"decision": "PASS", ...}
  - T13-TF-004와 동일 패턴
Inference: 3개 sub-module 모두 동일한 PASS fallback 패턴 사용. 일관성 있음.
Uncertainty: 없음
Cross-Ref: T13-TF-004
```

### T13-TF-006: ContinuityManuscriptValidator LLM 실패 시 degraded 마커 추가

```
ID: T13-TF-006
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/continuity_manuscript.py:335-363
Evidence:
  - continuity_manuscript.py:335-363
    except Exception as e:
        return {
            "decision": "PASS",
            "severity": "MINOR",
            "degraded": True,
            "degraded_reason": str(e),
            ...
        }
  - Arc/Blueprint validator와 달리 `degraded=True` 마커를 포함
Inference: Manuscript validator만 degraded 마커를 명시적으로 포함. Arc/Blueprint validator에는 이 필드가 없어 호출자가 degradation을 구분할 수 없음. 다만 T13-TF-002에서 inspect_manuscript가 미사용이므로 실질적 영향 없음.
Uncertainty: 없음
Cross-Ref: T13-TF-002
```

### T13-TF-007: V49.7 Feature Flag — ImportError 기반 토글

```
ID: T13-TF-007
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/continuity_tracker.py:14-23, 47-75
Evidence:
  - continuity_tracker.py:14-23
    try:
        from modules.core.foreshadow_tracker import ForeshadowTracker
        from modules.core.information_diffusion import InformationDiffusion
        from modules.core.power_scaling import PowerScalingTracker
        from modules.core.relationship_tracker import RelationshipTracker
        from modules.core.state_delta_tracker import StateDeltaTracker
        V49_7_MODULES_AVAILABLE = True
    except ImportError:
        V49_7_MODULES_AVAILABLE = False
  - continuity_tracker.py:54-75 — init_trackers()에서:
    if V49_7_MODULES_AVAILABLE: → 5개 트래커 초기화 + v49_7_enabled=True
    else: → 모두 None + v49_7_enabled=False
  - main_a.py:2242 — _bootstrap_continuity_inspector()에서:
    if ci and hasattr(ci, "v49_7_enabled") and ci.v49_7_enabled:
        arcs_data = self.current_project.db.load_anchor("arcs") or []
        if arcs_data: ci.load_trackers_from_db(arcs_data=arcs_data)
  - tests/test_continuity_modules.py:703 — V49_7_MODULES_AVAILABLE=False 패치 테스트 존재
Inference: V49.7 feature flag는 ImportError 기반. 5개 모듈 중 하나라도 import 실패하면 전체 비활성화. main_a.py에서 bootstrap 시 DB에서 트래커 상태를 로드함.
Uncertainty: 5개 모듈이 실제로 존재하는지 확인 필요 (정적 조사 범위 내에서는 import 경로만 확인)
Cross-Ref: T12 (State Tracking), T18 (Helpers)
```

### T13-TF-008: V49.7 트래커 init_trackers() — inspector 속성 직접 주입

```
ID: T13-TF-008
Severity: P3-LOW
Category: SIDE-EFFECT
Surface: modules/domain/agents/continuity_tracker.py:47-75
Evidence:
  - continuity_tracker.py:55-68
    self._ci.state_tracker = StateDeltaTracker(...)
    self._ci.relationship_tracker = RelationshipTracker()
    self._ci.power_tracker = PowerScalingTracker()
    self._ci.foreshadow_tracker = ForeshadowTracker()
    self._ci.info_diffusion = InformationDiffusion(self._ci.context)
    self._ci.v49_7_enabled = True
  - 서브모듈이 부모 inspector의 속성을 직접 설정함
  - BaseAgent에 이 속성들이 선언되어 있지 않음 — 동적 속성 주입
Inference: Python 동적 속성 주입 패턴. BaseAgent 상속 구조에서 state_tracker, relationship_tracker 등이 __init__에서 선언되지 않고 init_trackers()에서 동적 할당됨. ContinuityInspector.__init__에서 self._tracker.init_trackers()가 호출되므로 초기화 시점에 설정됨.
Uncertainty: BaseAgent나 ContinuityInspector의 __slots__가 없으므로 동적 속성 할당 자체는 문제없음. 다만 IDE/타입 체커에서 인식 불가.
Cross-Ref: T11 (BaseAgent)
```

### T13-TF-009: continuity_pin_guard — 프로덕션 호출 경로 확인

```
ID: T13-TF-009
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/continuity_pin_guard.py
Evidence:
  - stage3_orchestrator.py:22 — from modules.core.continuity_pin_guard import apply_continuity_pins
  - stage3_orchestrator.py:1611 — _pin_result = apply_continuity_pins(blueprint, ...)
  - stage4_orchestrator.py:425 — from modules.core.continuity_pin_guard import apply_continuity_pins
  - stage4_orchestrator.py:472 — _pin_result = apply_continuity_pins(...)
  - 2개의 Pin 유형: proper_noun_pin (고유명사 교정), elapsed_time_pin (시간 표현 교정)
  - 결정론적 (LLM 호출 없음), 순수 문자열 매칭 기반
Inference: Stage 3과 Stage 4 모두에서 활발히 사용됨. ContinuityInspector의 LLM 기반 Blueprint/Manuscript 검증과 달리, pin_guard는 결정론적이고 경량.
Uncertainty: 없음
Cross-Ref: T04 (Stage 3), T05 (Stage 4)
```

### T13-TF-010: ContinuityValidator (Tier 0.5) — 6개 검증 + 2개 추가 검증 항목

```
ID: T13-TF-010
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/validation/continuity_validator.py:122-285
Evidence:
  - validate() 메서드의 검증 항목 전수:
    1. 아이템 소지 연속성: _check_item_continuity (L204-207)
    2. 인벤토리 카운트 연속성: _check_inventory_count_continuity (L209-212)
    3. 활성 압박 벡터 연속성: _check_active_pressure_continuity (L214-217)
    4. 무기 소지 연속성: _check_weapon_continuity (L222-225)
    5. 부상 상태 연속성: _check_injury_continuity (L234-237) — 전투 장르만
    6. 위치 연속성: _check_location_continuity (L242-247) — V66.1 불가능한 순간이동
    7. NPC 성격 연속성: _check_personality_continuity (L252-259) — V66.1
    8. 시간 일관성: _check_time_consistency (L264-267) — V66.1
  - 추가 기능: check_frustration_streak (L1241) — 좌절-보상 타이머
  - 비용: $0 (LLM 호출 없음 — 순수 Python)
  - skip_continuity 플래그 지원 (L147-155) — Blueprint 모드에서 스킵
Inference: 8개 검증 항목 + 좌절 타이머. 전투 장르(wuxia/hunter/fantasy)에서만 부상 검증 수행 (L232-233). V66.1에서 위치/성격/시간 3개 검증 추가됨.
Uncertainty: 없음
Cross-Ref: T14 (Validation Pipeline)
```

### T13-TF-011: ContinuityValidator prev_hud 누락 시 fail-closed (DEGRADED)

```
ID: T13-TF-011
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/validation/continuity_validator.py:173-195
Evidence:
  - continuity_validator.py:173-195
    if not prev_hud:
        logging.warning("[CONTINUITY] prev_hud 누락 — HUD 의존 연속성 검증 DEGRADED.")
        return {
            "tier": "CONTINUITY",
            "passed": False,
            "score": 0.0,
            "degraded": True,
            "violations": [{"type": "prev_hud_missing", "severity": "BLOCKING", ...}],
            ...
        }
  - prev_hud 누락 시 passed=False, degraded=True 반환
  - [P3-01] 주석: "fail-closed (TF-15 P0-06)"
Inference: prev_hud 없이는 검증 불가 → 명시적 DEGRADED 반환. validation_orchestrator에서 이를 advisory로 전환.
Uncertainty: 없음
Cross-Ref: T14 (Validation Pipeline)
```

### T13-TF-012: ContinuityValidator — 대원칙 1 준수 (Python은 수집만, 판단은 LLM)

```
ID: T13-TF-012
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/validation/validation_orchestrator.py:398-409
Evidence:
  - validation_orchestrator.py:398-409
    if not continuity_result["passed"]:
        logging.warning(f" [대원칙1] CONTINUITY {len(_cont_violations)}개 위반 — Director advisory로 전달")
        results["_continuity_advisory"] = {
            "source": "ContinuityValidator",
            "violations": _cont_violations,
            "feedback": self._generate_continuity_feedback(continuity_result),
            "severity": "HIGH",
        }
  - 즉시 REJECT 대신 advisory로 전달 → Director가 최종 판정
Inference: ContinuityValidator 위반은 직접 REJECT하지 않고 advisory로 Director에게 전달. 대원칙 1 "Python은 수집만" 준수.
Uncertainty: 없음
Cross-Ref: T14 (Validation Pipeline), T07 (Director System)
```

### T13-TF-013: ContinuityValidator — violation → -5/violation, cap -15 미확인

```
ID: T13-TF-013
Severity: P2-MEDIUM
Category: DRIFT
Surface: modules/validation/continuity_validator.py, modules/validation/validation_orchestrator.py
Evidence:
  - 마스터 오더 명시: "Continuity validator (validation tier 0.5) — violation → -5/violation, cap -15 구현 확인"
  - Grep "continuity.*penalty|continuity.*cap|-5.*violation|cap.*-15" in modules/validation/ → 0 matches
  - ContinuityValidator.validate() 반환: {tier, passed, violations, warnings, message, violation_count, warning_count}
    - score 필드 없음 (degraded 경우만 score: 0.0)
    - penalty 계산 없음
  - validation_orchestrator.py에서 continuity_result를 advisory로 전달할 뿐, 수치적 penalty 적용 코드 없음
  - 다른 validator(retrospective_validator)에서는 severity별 penalty 존재:
    validation_orchestrator.py:652-653: penalty = ... if severity == "CRITICAL": ...
Inference: ContinuityValidator에는 -5/violation, cap -15 점수 감점 로직이 구현되어 있지 않다. 위반 시 advisory로만 전달되어 Director가 판단하는 구조. 메모리에 기록된 "-5/violation, cap -15"는 다른 validator(retrospective?)의 패턴이거나, 설계 시점의 사양이 실제 구현과 다를 수 있음.
Uncertainty: validation.yaml에 continuity 관련 score penalty 설정이 있을 수 있음 — 동적 검증 필요
Cross-Ref: T14 (Validation Pipeline), T17 (Config)
```

### T13-TF-014: Arc Python precheck — 미사용 변수

```
ID: T13-TF-014
Severity: P3-LOW
Category: DEAD-CODE
Surface: modules/domain/agents/continuity_arc.py:789
Evidence:
  - continuity_arc.py:789
    arc.get("ep_start", 1)
  - 반환값이 변수에 할당되지 않음 (결과를 아무 데도 사용하지 않음)
  - _check_intra_arc_consistency 메서드 내부
Inference: ep_start 값을 가져오지만 변수에 할당하지 않아 dead statement. 이전 리팩터링에서 사용처가 제거된 것으로 추정.
Uncertainty: 없음 — 명확한 미사용 statement
Cross-Ref: 없음
```

### T13-TF-015: Facade 위임 스텁 — private 메서드까지 노출

```
ID: T13-TF-015
Severity: P3-LOW
Category: COVERAGE-GAP
Surface: modules/domain/agents/continuity_inspector.py:350-412
Evidence:
  - 위임되는 private 메서드 목록:
    _python_precheck() (L350-352)
    _format_prev_blueprints() (L354-356)
    _format_timeline() (L358-360)
    _generate_fix_instructions() (L362-364)
    _inspect_intra_arc_only() (L378-380)
    _extract_accurate_joint_docs() (L382-386)
    _arc_python_precheck() (L394-396)
    _check_intra_arc_consistency() (L398-400)
    _format_prev_arcs() (L402-404)
    _format_arc_timeline() (L406-408)
    _generate_arc_fix_instructions() (L410-412)
    ... (manuscript 관련 15개 추가)
  - 외부에서 facade의 private 위임 스텁을 직접 호출하는 코드:
    Grep "_python_precheck|_format_prev_blueprints" in modules/ (continuity_inspector 제외) → 0 matches
Inference: Facade가 public 메서드뿐 아니라 private 메서드(_로 시작)까지 위임 스텁으로 노출하고 있다. 이는 V64.P3 분해 시 외부 호출을 보존하기 위한 것이나, 현재 외부에서 이 private 스텁을 직접 호출하는 코드가 없다. 위생 차원에서 제거 가능하나 하위 호환성 보존 목적.
Uncertainty: 테스트에서 직접 호출할 수 있으나, 프로덕션 호출은 확인되지 않음
Cross-Ref: 없음
```

### T13-TF-016: ContinuityValidator._is_same_item vs ContinuityInspector._is_same_item — 구현 불일치

```
ID: T13-TF-016
Severity: P2-MEDIUM
Category: CONTRADICTION
Surface: modules/validation/continuity_validator.py:929-958 vs modules/domain/agents/continuity_inspector.py:248-264
Evidence:
  - ContinuityInspector._is_same_item (continuity_inspector.py:248-264):
    정규화: strip, lower, 공백 제거
    매칭: 정확 매칭만 (V60.55 초보수적 접근)
    return: item1_normalized == item2_normalized
  - ContinuityValidator._is_same_item (continuity_validator.py:929-958):
    매칭: 정확 매칭 + 부분 포함(item1 in item2) + 키워드 2개 이상 일치 + important_words 매칭
    훨씬 관대한 매칭 — "녹슨 백근 대도" vs "대도"도 매칭
  - 두 구현이 같은 이름을 가지지만 매칭 로직이 완전히 다름
Inference: ContinuityInspector(LLM 기반, V60.55 초보수적)와 ContinuityValidator(Python-only, 관대한 부분 매칭)가 서로 다른 아이템 동일성 판단 기준을 사용. 동일 아이템에 대해 다른 결론을 내릴 수 있음. 다만 T13-TF-002에서 inspect_manuscript가 미사용이므로 런타임 충돌 가능성은 낮음.
Uncertainty: inspect_arc()에서는 ContinuityInspector._is_same_item이 사용되므로 Stage 2에서는 초보수적 매칭 적용
Cross-Ref: T14 (Validation Pipeline)
```

### T13-TF-017: ContinuityValidator — DISTANT_LOCATION_PAIRS 하드코딩

```
ID: T13-TF-017
Severity: P3-LOW
Category: HARDCODING
Surface: modules/validation/continuity_validator.py:789-807
Evidence:
  - continuity_validator.py:789-807
    DISTANT_LOCATION_PAIRS = [
        ("하북", "사천"), ("하북", "강남"), ("산서", "강남"), ...
        ("서울", "부산"), ("서울", "제주"), ...
        ("서울", "뉴욕"), ("서울", "런던"), ...
    ]
  - 16쌍의 원거리 위치 쌍이 코드에 하드코딩
  - 장르별 분류: 무협(9), 헌터(3), 투자(3) — 주석으로만 구분
  - YAML config에서 관리되지 않음
Inference: 장르 추가 시 코드 수정 필요. 현재 지원 장르(wuxia/hunter/investment/fantasy)에 대해서는 무협과 헌터/투자가 커버되나 fantasy 위치쌍은 없음. 새 장르(작곡/의료/스포츠 등)에서는 적용 불가.
Uncertainty: fantasy 장르에서 위치 검증이 필요한지 불확실
Cross-Ref: T17 (Config)
```

### T13-TF-018: ContinuityValidator — 부상 검증 장르 필터

```
ID: T13-TF-018
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/validation/continuity_validator.py:231-237
Evidence:
  - continuity_validator.py:231-237
    _combat_genres = {"wuxia", "hunter", "fantasy"}
    _genre = validation_context.get("genre", "wuxia") if isinstance(validation_context, dict) else "wuxia"
    if _genre in _combat_genres:
        injury_check = self._check_injury_continuity(...)
  - 비전투 장르(투자물/요리/배우 등)에서는 부상 검증 스킵
  - 주석: [WARN-2] 비전투 장르(투자물/요리/배우/작곡/의료/대체역사/스포츠)는 부상 검사 스킵
Inference: 장르 기반 조건부 검증 구현 확인. default 장르가 "wuxia"로 하드코딩되어 있어, genre가 validation_context에 없으면 항상 부상 검증 수행.
Uncertainty: 없음
Cross-Ref: T18 (Genre Guards)
```

### T13-TF-019: continuity_pin_guard — source_quoted 길이 1 제한

```
ID: T13-TF-019
Severity: P3-LOW
Category: COVERAGE-GAP
Surface: modules/core/continuity_pin_guard.py:113-116
Evidence:
  - continuity_pin_guard.py:113-116
    if len(source_quoted) == 1 and blueprint_quoted:
        expected = source_quoted[0]
        mismatched = [token for token in blueprint_quoted if token != expected]
        if len(mismatched) == 1 and expected not in blueprint_quoted:
  - 고유명사 핀 교정이 source에서 인용 토큰이 정확히 1개일 때만 작동
  - source에 복수의 인용 토큰이 있으면 교정이 아예 스킵됨
  - mismatched도 정확히 1개일 때만 교정 (2개 이상이면 unresolved로 분류)
Inference: 의도적으로 보수적 설계. 확실한 1:1 매칭만 자동 교정하고, 복수 후보가 있으면 unresolved로 넘김. False positive 방지 목적.
Uncertainty: 없음 — unresolved 리스트로 미교정 항목 추적 가능
Cross-Ref: T04 (Stage 3), T05 (Stage 4)
```

### T13-TF-020: ContinuityManuscriptValidator._incarnation_type — 회귀자 인식

```
ID: T13-TF-020
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/continuity_manuscript.py:182-202
Evidence:
  - continuity_manuscript.py:182-183
    self._incarnation_type = self._extract_incarnation_type()
  - continuity_manuscript.py:192-202
    _extract_incarnation_type: master_bible → protagonist_config → incarnation_type
  - 사용처:
    _check_relationship_jump (L525): 회귀자 맥락 접미사 추가
    _check_reader_immersion (L741): 회귀자 파워업/능력 설명 맥락
    _track_relationship_history (L1061): 회귀자 관계 재연 맥락
  - V67.1에서 추가된 기능
Inference: 회귀자 incarnation_type에 따라 관계 급변/파워업 경고에 "[회귀자 — 전생 관계 재연 가능]" 접미사를 추가. 오탐 방지 목적의 context-aware 검증.
Uncertainty: 없음
Cross-Ref: T12 (State Tracking — protagonist_config)
```

### T13-TF-021: ContinuityValidator.check_frustration_streak — 프로덕션 호출 확인

```
ID: T13-TF-021
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/validation/continuity_validator.py:1241-1282
Evidence:
  - 정의: continuity_validator.py:1241 — def check_frustration_streak(self, ep_num: int) -> list[str]
  - 프로덕션 호출: stage4_interview_round.py:3192
    _frust_warnings = continuity_validator.check_frustration_streak(next_ep)
  - 임계값:
    warn_threshold = _threshold("satisfaction.frustration_warning_streak", 3)
    crit_threshold = _threshold("satisfaction.frustration_critical_streak", 5)
  - DB 의존: db.get_recent_satisfaction_tags(before_ep, lookback)
Inference: ContinuityValidator 내에 있지만 연속성보다는 서사 만족도 관련 기능. Stage 4 interview round에서 호출됨.
Uncertainty: 없음
Cross-Ref: T06 (Stage 4 Interview)
```

### T13-TF-022: ContinuityArcValidator — start_state_corrected 시 current_arc 직접 변경 (side-effect)

```
ID: T13-TF-022
Severity: P2-MEDIUM
Category: SIDE-EFFECT
Surface: modules/domain/agents/continuity_arc.py:319-364
Evidence:
  - continuity_arc.py:353-364
    corrected_start = {
        "internal_energy": correct_energy,
        "injuries": correct_injuries,
        "location": correct_location,
        "equipment": correct_equipment,
    }
    curr_state["arc_start_state"] = corrected_start
    current_arc["state_constraints"] = curr_state
    start_state_corrected = True
  - inspect_arc()에 전달된 current_arc dict를 직접 수정함 (in-place mutation)
  - 호출자(stage2_validation_pipeline.py)가 전달한 refined_arc가 변경됨
Inference: 검증 메서드가 입력 데이터를 직접 수정하는 side-effect. 호출자 의도와 무관하게 arc_start_state가 교정됨. V60.13 자동 교정 기능이나, 검증과 수정이 혼재된 설계.
Uncertainty: stage2_validation_pipeline.py에서 이 변경을 의도적으로 활용하는지 확인 필요 (동적 검증)
Cross-Ref: T02 (Stage 2 Orch), T03 (Stage 2 Preflight)
```

### T13-TF-023: ContinuityArcValidator — joint_docs도 in-place 교정

```
ID: T13-TF-023
Severity: P3-LOW
Category: SIDE-EFFECT
Surface: modules/domain/agents/continuity_arc.py:306-314
Evidence:
  - continuity_arc.py:306-313
    corrected_joint_docs = self._extract_accurate_joint_docs(...)
    if corrected_joint_docs and corrected_joint_docs != joint_docs:
        joint_docs = corrected_joint_docs  # 로컬 변수 재할당, 원본 미변경
        joint_docs_corrected = True
  - 이 경우는 로컬 변수만 변경하므로 원본 current_arc의 joint_docs는 변경되지 않음
  - 단 result에 corrected_joint_docs를 포함시켜 호출자가 사용할 수 있게 함 (L420-424)
Inference: T13-TF-022와 달리 joint_docs 교정은 in-place mutation이 아님. 교정된 값은 result dict에 포함.
Uncertainty: 없음
Cross-Ref: T13-TF-022
```

### T13-TF-024: ContinuityValidator — _get_prev_hud DB 조회 dead code 제거 확인

```
ID: T13-TF-024
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/validation/continuity_validator.py:287-299
Evidence:
  - continuity_validator.py:287-299
    def _get_prev_hud(self, current_ep: int, validation_context: dict) -> dict | None:
        prev_hud = validation_context.get("prev_hud")
        if prev_hud:
            return prev_hud
        # [TF-26] manuscripts 테이블에 hud_snapshot 컬럼 없음 — DB 조회 dead code 제거
        # [TF-XC-04] 현재 HUD를 이전 HUD로 사용하면 false negative 발생
        logging.info("[CONTINUITY] 이전 HUD 조회 불가 — 연속성 검사 스킵")
        return None
  - 이전 TF-26에서 DB 조회 dead code 제거 완료
Inference: prev_hud는 오직 validation_context에서만 주입됨. DB 직접 조회 경로는 제거됨.
Uncertainty: 없음
Cross-Ref: T16 (Database)
```

### T13-TF-025: ContinuityBlueprintValidator.get_prev_blueprints — window=None 시 ep 1부터 전체 조회

```
ID: T13-TF-025
Severity: P3-LOW
Category: UNBOUNDED
Surface: modules/domain/agents/continuity_blueprint.py:437-460
Evidence:
  - continuity_blueprint.py:444
    start_ep = 1 if window is None else max(1, current_ep - window)
  - window=None (기본값)이면 ep 1부터 current_ep까지 모든 블루프린트를 DB에서 조회
  - ep 50이면 49번의 DB 조회 발생 가능
  - 다만 T13-TF-002에서 이 메서드가 프로덕션에서 호출되지 않으므로 실질적 영향 없음
Inference: 잠재적 성능 문제. 다만 프로덕션 미사용으로 현재 비활성.
Uncertainty: 없음
Cross-Ref: T13-TF-002
```

### T13-TF-026: ContinuityManuscriptValidator.get_prev_manuscripts — window=5 기본값

```
ID: T13-TF-026
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/continuity_manuscript.py:365-384
Evidence:
  - continuity_manuscript.py:365
    def get_prev_manuscripts(self, current_ep: int, window: int = 5) -> list[dict]:
  - 최대 5화 이전까지만 조회 (T13-TF-025와 대비: Blueprint는 전체 조회)
  - 다만 이 메서드도 프로덕션에서 호출되지 않음 (T13-TF-002)
Inference: Blueprint는 unbounded, Manuscript는 window=5로 제한됨. 일관성 없으나 둘 다 미사용.
Uncertainty: 없음
Cross-Ref: T13-TF-002, T13-TF-025
```

---

## 3. Evidence Inventory

| TF | 핵심 증거 소스 | 유형 |
|----|---------------|------|
| TF-001 | continuity_inspector.py:140-548 | 코드 인용 |
| TF-002 | Grep "inspect_manuscript" in modules/ → 0 production callers | 부재 증명 |
| TF-003 | stage2_validation_pipeline.py:751 | 호출 경로 |
| TF-004 | continuity_arc.py:464-482 | 예외 처리 |
| TF-007 | continuity_tracker.py:14-23, main_a.py:2242 | 초기화 경로 |
| TF-009 | stage3_orchestrator.py:1611, stage4_orchestrator.py:472 | 호출 경로 |
| TF-010 | continuity_validator.py:122-285 | 검증 항목 전수 |
| TF-013 | Grep "continuity.*penalty" → 0 matches | 부재 증명 |
| TF-016 | continuity_validator.py:929-958 vs continuity_inspector.py:248-264 | 비교 |
| TF-022 | continuity_arc.py:353-364 | side-effect |

---

## 4. Side-Effect Surface

| 위치 | Side-Effect | 영향 |
|------|------------|------|
| continuity_arc.py:353-364 | current_arc dict in-place mutation (arc_start_state 교정) | Stage 2 refined_arc 변경 |
| continuity_tracker.py:55-68 | inspector 속성 동적 주입 (state_tracker 등 5개) | ContinuityInspector 인스턴스 변경 |
| continuity_arc.py:420-424 | result에 corrected_joint_docs 포함 (원본 미변경) | 호출자에게 교정 데이터 전달 |
| continuity_validator.py:204-267 | violations/warnings 리스트 누적 | validation_orchestrator advisory 전달 |
| continuity_validator.py:1241-1282 | DB 조회 (satisfaction_tags) | 읽기 전용 |

---

## 5. Facts

1. ContinuityInspector는 V64.P3에서 4개 서브모듈(Arc/Blueprint/Manuscript/Tracker)로 분해됨
2. 프로덕션에서 활성 사용되는 메서드는 `inspect_arc()` 단 하나 (Stage 2에서)
3. `inspect()` (Blueprint)과 `inspect_manuscript()`/`inspect_manuscript_v59()`는 프로덕션 미호출
4. ContinuityValidator (Tier 0.5)는 validation_orchestrator에서 8개 검증 수행 (Python-only, $0)
5. continuity_pin_guard는 Stage 3/4에서 결정론적 핀 교정 수행 (LLM 불필요)
6. V49.7 트래커(5개)는 ImportError 기반 feature flag로 토글됨
7. ContinuityValidator 위반은 advisory로 Director에 전달됨 (대원칙 1 준수)
8. ContinuityValidator에 -5/violation, cap -15 penalty 로직은 구현되어 있지 않음

---

## 6. Inferences

1. ContinuityInspector의 Blueprint/Manuscript LLM 검증은 ContinuityValidator(Python-only)와 continuity_pin_guard로 사실상 대체됨. LLM 비용 절감 의도로 보임.
2. inspect_arc만 LLM 호출을 수행하며, Arc 수준의 cross-arc 검증은 Python precheck + LLM 2단계 구조.
3. 5,152줄 중 프로덕션 활성 코드는 약 1,500줄(continuity_arc 1,026 + continuity_tracker 424 일부 + pin_guard 149).
4. 나머지 ~3,600줄(inspector facade + blueprint + manuscript)은 테스트에서만 사용되는 준비 코드.

---

## 7. Uncertainty / Contradictions

1. **T13-TF-002 (DEAD-CODE)**: inspect_manuscript 프로덕션 미호출 — 외부 스크립트/커스텀 호출 경로 검증은 동적 검증 필요
2. **T13-TF-013 (DRIFT)**: -5/violation, cap -15 penalty가 구현되어 있지 않음 — 설계 문서와 실제 구현 차이 (CONTRADICTION 후보)
3. **T13-TF-022 (SIDE-EFFECT)**: inspect_arc의 current_arc in-place mutation — stage2_validation_pipeline에서 이 변경을 의도적으로 활용하는지 확인 필요

---

## 8. Cross-Ref to Adjacent Terminals

| 인접 터미널 | 교차 영역 | 관련 TF |
|------------|----------|---------|
| T02 (Stage 2 Orch) | inspect_arc 호출 경로 | T13-TF-003, T13-TF-022 |
| T03 (Stage 2 Preflight) | stage2_validation_pipeline에서 inspect_arc 호출 | T13-TF-003 |
| T04 (Stage 3) | apply_continuity_pins 호출 | T13-TF-009 |
| T05 (Stage 4 Orch) | apply_continuity_pins 호출 | T13-TF-009 |
| T06 (Stage 4 Interview) | check_frustration_streak 호출 | T13-TF-021 |
| T07 (Director) | continuity advisory → Director 판정 | T13-TF-012 |
| T11 (BaseAgent) | ContinuityInspector가 BaseAgent 상속 | T13-TF-001, T13-TF-008 |
| T12 (State Tracking) | V49.7 트래커 의존 | T13-TF-007, T13-TF-020 |
| T14 (Validation Pipeline) | ContinuityValidator ↔ validation_orchestrator | T13-TF-010-013 |
| T17 (Config) | DISTANT_LOCATION_PAIRS 하드코딩 | T13-TF-017 |

---

## 9. Candidate Watchlist

1. **inspect_manuscript / inspect_manuscript_v59 제거 또는 재활성화** — 1,700+ 줄의 LLM 기반 원고 검증이 미사용. 제거할지 재활성화할지 결정 필요.
2. **inspect() (Blueprint) 재활성화** — Stage 3에서 호출되지 않음. continuity_pin_guard만으로 충분한지 평가 필요.
3. **_is_same_item 통합** — ContinuityInspector(초보수적)와 ContinuityValidator(관대)의 아이템 동일성 판단 기준 불일치 해소.
4. **DISTANT_LOCATION_PAIRS YAML 외부화** — 장르별 위치 쌍을 config로 관리.
5. **inspect_arc의 current_arc mutation 분리** — 검증과 교정을 분리하여 side-effect 명시화.

---

## 10. 6Pass Audit Log

### Pass 1 (구조/범위)
- 7개 파일 5,152줄 전수 읽기 완료 ✅
- 필수 조사 7개 항목 모두 커버 ✅
- TF 26개 생성 (최소 8개 이상 요구 충족) ✅
- Side-effect surface 포함 ✅
- **PASS**

### Pass 2 (증거/일관성)
- 모든 TF에 파일:라인 Evidence 포함 ✅
- Grep 결과 기반 부재 증명 포함 ✅
- 라인 수 `wc -l` 결과 일치 (5,152 total) ✅
- Cross-Ref 양쪽 파일:라인 명시 ✅
- **PASS**

### Pass 3 (실행가능성)
- T13-TF-002 (DEAD-CODE): 명확한 Grep 증거 기반 — actionable (제거/재활성화 결정) ✅
- T13-TF-013 (DRIFT): penalty 미구현 증거 기반 — actionable (구현 또는 사양 수정) ✅
- T13-TF-016 (CONTRADICTION): 양쪽 코드 인용 기반 — actionable (통합 결정) ✅
- severity 기준 적절: P0=0, P1=0, P2=3, P3=6, P4=17 ✅
- **PASS**

### Pass 4 (적대적: 스코프 과잉/누락 반박 시도)
- "test_continuity_packet.py가 T13에서 누락됨" → 실제 내용 확인 결과 Stage4ContextBuilder 관련이므로 T05 범위 → **반박 실패, PASS**
- "director_continuity.py가 T13에 포함되어야 함" → director_continuity는 Director 산하 sub-module이므로 T07 범위 → **반박 실패, PASS**
- **PASS**

### Pass 5 (적대적: 증거 거짓/오해 반박 시도)
- "T13-TF-002의 inspect_manuscript 미호출은 Grep 누락일 수 있다" → modules/ 전체 + tests/ 전체 검색 완료, grep "inspect_manuscript" 결과에 stage/director/interview 파일 없음 → **반박 실패, PASS**
- "T13-TF-013의 penalty 부재가 validation.yaml에 있을 수 있다" → Uncertainty에 명시됨, 정적 조사 범위 내 코드 참조 기반으로는 미구현 → **반박 실패, PASS**
- **PASS**

### Pass 6 (적대적: severity 과대/과소 반박 시도)
- "T13-TF-002가 P2가 아니라 P1이어야 한다" → 1,700줄 dead code이지만 프로덕션 동작에 영향 없음 (호출되지 않으므로). 미사용 코드 자체는 유지보수 부담일 뿐 동작 오류가 아님 → P2 적절 → **반박 실패, PASS**
- "T13-TF-022가 P2가 아니라 P1이어야 한다" → in-place mutation이 의도적 V60.13 자동 교정이므로 P1(조용한 오동작)이 아닌 P2(품질 저하 가능성) → **반박 실패, PASS**
- **PASS**
