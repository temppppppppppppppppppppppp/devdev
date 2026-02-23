# TF-7 Risk 패치 오더 (1차/3차/6차/7차)

> **생성일**: 2026-02-23
> **범위**: TF-7 Risk 백로그 + 확정 미패치 항목 중 우선 4개 배치
> **제외**: 2차(동적 장르 이벤트), 4차(캐시 라이프사이클), 5차(설정 SSOT) — 후순위 관찰 대기
> **전제 기준선**: `pytest tests/ -q` → **2,377 passed**, ruff 0 violations (commit `9f0de73` + TF-7 P0/P1/P2)

---

## 배치별 패치 요약

| # | 패치 ID | 배치 | 심각도 원출처 | 대상 파일 | 핵심 변경 |
|---|---|---|---|---|---|
| 1 | TF7R-P1-01 | 1차 | TF-7-E-R1 | `state_delta_tracker.py` | `rollback_to(ep_num)` + `reset()` 메서드 추가 |
| 2 | TF7R-P1-02 | 1차 | TF-7-J (emotion gap) | `emotion_tracker.py` | `rollback_to(ep_num)` + `clear()` 메서드 추가 |
| 3 | TF7R-P1-03 | 1차 | TF-7-J (emotion gap) | `project_service.py`, `main_a.py` | rollback_episode에서 emotion rollback 호출, main_a 성공 블록에 emotion clear 추가 |
| 4 | TF7R-P1-04 | 1차 | 신규 | `project_service.py` | rollback 완료 후 post-invariant 검사 (state_tracker/world/fact/foreshadow/emotion 경계 확인) |
| 5 | TF7R-P3-01 | 3차 | TF-7-D-R1 | `continuity_validator.py` | `prev_hud` None 시 silent skip → DEGRADED 플래그 반환 |
| 6 | TF7R-P3-02 | 3차 | TF-7-D-R2 | `stage4_interview_round.py` | `protagonist_name` 항상 `validation_context`에 주입 보장 |
| 7 | TF7R-P3-03 | 3차 | TF-7-H-R1 | `director_auditor.py` | V0128 경로에서 `encyclopedia.npcs` 누락 시 DEGRADED 플래그 |
| 8 | TF7R-P3-04 | 3차 | TF-7-B-R1 | `context_advisor.py` | `slot.max_chars` 하드코딩 500 → `validation.yaml` `slot_max_chars_default` 참조, 불일치 시 startup 경고 |
| 9 | TF7R-P6-01 | 6차 | TF-7-I-R1 | `validation_orchestrator.py` | Stage4 ValidationOrchestrator TIER1 BLOCKING 실패 → `FailureLearner.record_failure(stage=4)` 환류 |
| 10 | TF7R-P6-02 | 6차 | TF-7-L-R1 | `stage3_orchestrator.py` | Stage3 완료(PASS/REJECT) 시 `quality_dashboard.record_validation(stage=3, ...)` 추가 |
| 11 | TF7R-P7-01 | 7차 | 신규 | `tests/chaos/test_rollback_boundary.py` | rollback_episode 경계 시나리오 3종 |
| 12 | TF7R-P7-02 | 7차 | 신규 | `tests/chaos/test_blueprint_none.py` | blueprint=None 전 경로 degrade 확인 |
| 13 | TF7R-P7-03 | 7차 | 신규 | `tests/chaos/test_dead_npc_hard_block.py` | dead NPC 하드차단 경계 확인 |
| 14 | TF7R-P7-04 | 7차 | 신규 | `tests/chaos/test_partial_commit.py` | DB partial commit 후 rollback 원자성 |
| 15 | TF7R-P7-05 | 7차 | 신규 | `tests/chaos/test_validation_degrade.py` | prev_hud/encyclopedia.npcs 누락 시 DEGRADED 반환 확인 |
| 16 | TF7R-P7-06 | 7차 | 신규 | `tests/chaos/test_feedback_loop.py` | Stage4 REJECT → FailureLearner/QualityDashboard 단일 루프 확인 |
| 17 | TF7R-P7-07 | 7차 | 신규 | `tests/chaos/test_stage3_metrics.py` | Stage3 QualityDashboard 계측 확인 |

---

## 1차: 롤백 SSOT 완결

### [TF7R-P1-01] StateDeltaTracker rollback/reset 계약 추가

**원출처**: TF-7-E-R1
**파일**: `modules/core/state_delta_tracker.py`

**현황**:
- `StateDeltaTracker`는 `energy_history`, `injury_history`를 append-only로 관리
- rollback/reset 메서드 전혀 없음 → rollback 이후 state_delta history가 오염된 채 잔존

**패치 내용**:
```python
def rollback_to(self, ep_num: int) -> None:
    """ep_num보다 큰 회차의 delta history를 제거한다."""
    self.energy_history = [e for e in self.energy_history if e.get("ep_num", 0) <= ep_num]
    self.injury_history = [i for i in self.injury_history if i.get("ep_num", 0) <= ep_num]

def reset(self) -> None:
    """전체 history를 초기화한다 (새 프로젝트 또는 전체 롤백용)."""
    self.energy_history = []
    self.injury_history = []
```

**호출 위치**: `project_service.py` rollback_episode 성공 블록 (WorldState/FactLedger 롤백 직후)

---

### [TF7R-P1-02] EmotionArcTracker rollback_to / clear 메서드 추가

**원출처**: TF-7-J (emotion rollback gap)
**파일**: `modules/core/emotion_tracker.py`

**현황**:
- `EmotionArcTracker.history`는 `(ep_num, emotion_state, intensity)` 튜플 append-only
- rollback/clear 메서드 없음 → rollback 후 삭제된 회차 감정 이력이 남아 다음 Stage4 컨텍스트 오염

**패치 내용**:
```python
def rollback_to(self, ep_num: int) -> None:
    """ep_num보다 큰 회차의 감정 이력을 제거한다."""
    self.history = [(ep, st, intens) for (ep, st, intens) in self.history if ep <= ep_num]

def clear(self) -> None:
    """전체 감정 이력을 초기화한다."""
    self.history = []
```

---

### [TF7R-P1-03] rollback_episode + main_a 성공 블록에 emotion rollback 호출 추가

**파일**: `modules/core/services/project_service.py`, `main_a.py`

**현황**:
- `project_service.py` rollback_episode 단계 10: WorldState/FactLedger 롤백 호출은 있음
- EmotionArcTracker 롤백 호출 없음
- `main_a.py` `_rollback_episode()` 성공 블록: foreshadow clear는 있음, emotion clear 없음

**project_service.py 패치**:
```python
# 단계 10 (기존 WorldState/FactLedger 롤백) 바로 다음에 추가
if self._emotion_tracker_fn and callable(self._emotion_tracker_fn):
    _et = self._emotion_tracker_fn()
    if _et is not None and hasattr(_et, "rollback_to"):
        _et.rollback_to(target_ep)

if self._state_delta_tracker_fn and callable(self._state_delta_tracker_fn):
    _sdt = self._state_delta_tracker_fn()
    if _sdt is not None and hasattr(_sdt, "rollback_to"):
        _sdt.rollback_to(target_ep)
```

**main_a.py 패치** (성공 블록, foreshadow clear 직후):
```python
_et = getattr(self, "emotion_tracker", None)
if _et is not None and hasattr(_et, "rollback_to"):
    _et.rollback_to(target_ep)
```

**ProjectService.__init__ 파라미터 추가**:
```python
self._emotion_tracker_fn = emotion_tracker_fn  # 신규
self._state_delta_tracker_fn = state_delta_tracker_fn  # 신규
```

**main_a.py ProjectService 생성 호출 파라미터 추가**:
```python
emotion_tracker_fn=lambda: getattr(self, "emotion_tracker", None),
state_delta_tracker_fn=lambda: getattr(self, "state_delta_tracker", None),
```

---

### [TF7R-P1-04] 롤백 완료 후 post-invariant 검사 추가

**파일**: `modules/core/services/project_service.py`

**현황**: rollback 완료 후 실제로 모든 상태 객체의 ep 경계가 올바른지 검증하는 로직 없음

**패치 내용**: rollback_episode 마지막 단계에 invariant 확인 로그 추가
```python
def _assert_rollback_invariants(self, target_ep: int) -> None:
    """롤백 후 상태 경계 invariant를 로그로 검증한다. 위반 시 WARNING."""
    checks = []
    # state_tracker
    if self._state_tracker_fn and callable(self._state_tracker_fn):
        st = self._state_tracker_fn()
        if st and hasattr(st, "current_ep"):
            checks.append(("state_tracker.current_ep", st.current_ep, target_ep))
    # emotion_tracker
    if self._emotion_tracker_fn and callable(self._emotion_tracker_fn):
        et = self._emotion_tracker_fn()
        if et and hasattr(et, "history") and et.history:
            max_ep = max(ep for ep, *_ in et.history)
            checks.append(("emotion_tracker.max_ep", max_ep, target_ep))
    # state_delta_tracker
    if self._state_delta_tracker_fn and callable(self._state_delta_tracker_fn):
        sdt = self._state_delta_tracker_fn()
        if sdt and hasattr(sdt, "energy_history") and sdt.energy_history:
            max_ep = max(e.get("ep_num", 0) for e in sdt.energy_history)
            checks.append(("state_delta_tracker.max_ep", max_ep, target_ep))

    for label, actual, expected in checks:
        if actual > expected:
            logging.warning(
                "[ROLLBACK-INVARIANT] %s=%s > target_ep=%s — 경계 초과 감지",
                label, actual, expected,
            )
        else:
            logging.debug("[ROLLBACK-INVARIANT] %s=%s OK (target=%s)", label, actual, expected)
```

---

## 3차: 검증 체인 fail-close화

### [TF7R-P3-01] prev_hud 부재 시 CONTINUITY 체크 degrade 플래그 (TF-7-D-R1)

**파일**: `modules/validation/continuity_validator.py`

**현황**:
- `prev_hud` 가 None이거나 validation_context에 없으면 CONTINUITY 핵심 체크가 조용히 스킵됨
- 감지 불가 → silent PASS 위험

**패치 내용**:
```python
# validate() 진입부에서 prev_hud 검사
prev_hud = context.get("prev_hud") or context.get("martial_hud")
if not prev_hud:
    logging.warning("[ContinuityValidator] prev_hud 누락 — DEGRADED 모드로 전환 (핵심 체크 스킵)")
    return ValidationResult(
        passed=True,
        score=0.5,
        degraded=True,
        warnings=["prev_hud 누락으로 연속성 검증 DEGRADED"],
        failures=[],
    )
```

> **주의**: `ValidationResult`에 `degraded: bool = False` 필드가 없으면 추가 필요.

---

### [TF7R-P3-02] protagonist_name 항상 validation_context에 주입 (TF-7-D-R2)

**파일**: `modules/core/stage4_interview_round.py`

**현황**:
- ConsistencyValidator validation_context 구성 시 `protagonist_name` 주입 여부 확인 필요
- POV 검사기(V70)의 민감도가 protagonist_name 없으면 저하됨

**패치 내용** (validation_context 구성 직후):
```python
# protagonist_name 항상 보장
if "protagonist_name" not in validation_context:
    _proto_name = (
        round_ctx.project_data.get("protagonist_name")
        or getattr(round_ctx, "protagonist_name", None)
        or ""
    )
    if _proto_name:
        validation_context["protagonist_name"] = _proto_name
    else:
        logging.warning("[Stage4] protagonist_name 주입 실패 — POV 검사 민감도 저하 가능")
```

---

### [TF7R-P3-03] encyclopedia.npcs 누락 시 V0128 경로 DEGRADED 플래그 (TF-7-H-R1)

**파일**: `modules/domain/agents/director_auditor.py`

**현황**:
- V0128 `run_v0128_validation()` 경로: validation_context가 빈 dict로 시작 가능
- `encyclopedia.npcs` 없으면 NPC 기반 검증이 silent skip

**패치 내용** (run_v0128_validation 진입부):
```python
encyclopedia = validation_context.get("encyclopedia") or {}
npcs = encyclopedia.get("npcs") or {}
if not npcs:
    logging.warning(
        "[V0128] encyclopedia.npcs 누락 — NPC 일관성 검증 DEGRADED. "
        "validation_context에 encyclopedia.npcs를 주입하세요."
    )
    # degraded 플래그를 결과에 포함
    _degraded = True
else:
    _degraded = False
# 이후 결과 dict에 degraded=_degraded 포함
```

---

### [TF7R-P3-04] slot.max_chars 하드코딩 500 → validation.yaml 참조 (TF-7-B-R1)

**파일**: `modules/core/context_advisor.py`

**현황**:
- `_assign_slot_budgets()` L629: `slot.max_chars = max(500, int(total_budget * (weight / weight_sum)))`
- `validation.yaml`에는 `smart_retrieval.slot_max_chars_default: 1500`으로 정의
- 두 값이 다름 → 소비자별 기본값 불일치

**패치 내용**:
```python
def _assign_slot_budgets(self, stage: str, slots: list[RetrievalSlot]) -> None:
    total_budget = self._get_stage_budget(stage)
    if not slots or total_budget <= 0:
        return
    # validation.yaml에서 min 기본값 로드
    _min_chars = self._threshold("smart_retrieval.slot_max_chars_default", default=1500)
    weight_map = {1: 3, 2: 2, 3: 1}
    weights = [weight_map.get(slot.priority, 1) for slot in slots]
    weight_sum = sum(weights) or 1
    for slot, weight in zip(slots, weights, strict=False):
        slot.max_chars = max(_min_chars, int(total_budget * (weight / weight_sum)))
```

> `self._threshold()`가 없으면 `ThresholdHelper.get()` 또는 직접 yaml 읽기로 대체.

---

## 6차: 피드백/학습 루프 폐합

### [TF7R-P6-01] Stage4 ValidationOrchestrator TIER1 실패 → FailureLearner 환류 (TF-7-I-R1)

**파일**: `modules/validation/validation_orchestrator.py`

**현황**:
- ValidationOrchestrator TIER1(BLOCKING) 실패 결과가 호출측으로 반환되지만,
- Stage4 경로에서 FailureLearner에 환류되지 않음 (Stage2는 정상 환류)
- `stage4_interview_round.py`에서 BLOCKING 전체 탈락 분기만 FailureLearner 기록하나, ValidationOrchestrator 내부 개별 실패는 누락

**패치 내용** (`validation_orchestrator.py` TIER1 실패 로그 직후):
```python
# stage=4 컨텍스트에서 FailureLearner 환류
if context.get("stage") == 4:
    _fl = context.get("failure_learner")
    if _fl and hasattr(_fl, "record_failure"):
        for f in result.failures:
            _fl.record_failure(
                stage=4,
                failure_type=f.get("type", "BLOCKING"),
                description=f.get("description", ""),
            )
```

**호출측 패치** (`stage4_interview_round.py`):
- ConsistencyValidator 호출 시 `validation_context["stage"] = 4` 추가
- `validation_context["failure_learner"] = ctx.failure_learner` 주입 (None 허용)

---

### [TF7R-P6-02] Stage3 QualityDashboard 계측 추가 (TF-7-L-R1)

**파일**: `modules/core/stage3_orchestrator.py`

**현황**:
- Stage2(`stage2_finalizer.py:572`, `:657`)와 Stage4(`stage4_interview_round.py`)는 QualityDashboard 기록
- Stage3(Blueprint) 결과는 전혀 기록 없음 → pass_rate 통계에 Stage3 누락

**패치 내용** (Stage3 결과 반환 직전):
```python
# Blueprint PASS
if self._quality_dashboard and hasattr(self._quality_dashboard, "record_validation"):
    self._quality_dashboard.record_validation(
        stage=3,
        decision="PASS",
        score=blueprint_score,
        ep_num=ep_num,
        violations=[],
        warnings=blueprint_warnings,
    )

# Blueprint REJECT (재시도 한도 초과 시)
if self._quality_dashboard and hasattr(self._quality_dashboard, "record_validation"):
    self._quality_dashboard.record_validation(
        stage=3,
        decision="REJECT",
        score=0,
        ep_num=ep_num,
        violations=[{"type": "blueprint_reject", "description": "Blueprint 생성 최대 재시도 초과"}],
        warnings=[],
    )
```

---

## 7차: 카오스 테스트팩 (결정론적 경계 시나리오)

> **원칙**: 랜덤 fault injection 금지. 모든 테스트는 결정론적 fixture 기반.

### [TF7R-P7-01] `tests/chaos/test_rollback_boundary.py`

**시나리오**:
1. `rollback_episode(target=3)` 후 `emotion_tracker.history` 내 ep>3 항목 없음 확인
2. `rollback_episode(target=3)` 후 `state_delta_tracker.energy_history` 내 ep>3 항목 없음 확인
3. `rollback_episode(target=3)` 후 post-invariant 검사 log에 WARNING 없음 확인

---

### [TF7R-P7-02] `tests/chaos/test_blueprint_none.py`

**시나리오**:
1. `BlockingValidator.validate(manuscript, {"mode": "MANUSCRIPT", "blueprint": None})` → AttributeError 없이 degrade/PASS 반환
2. `BlockingValidator.validate(manuscript, {"mode": "MANUSCRIPT", "blueprint": {}})` → 정상 처리
3. `BlockingValidator.validate(manuscript, {"mode": "MANUSCRIPT"})` → blueprint 키 없이도 크래시 없음

---

### [TF7R-P7-03] `tests/chaos/test_dead_npc_hard_block.py`

**시나리오**:
1. `deceased=True` NPC가 행동 주체로 포함된 원고 → `stage4_interview_round` REJECT 반환 (warning 아님)
2. `deceased=True` NPC가 **회상** 텍스트에만 등장 → PASS 반환 (정상 허용)

---

### [TF7R-P7-04] `tests/chaos/test_partial_commit.py`

**시나리오**:
1. `rollback_episode` 도중 DB write 실패 시뮬레이션(mock) → rollback 자체가 롤백되어 원래 상태 유지
2. `rollback_episode` 성공 후 `_assert_rollback_invariants` 경고 없음 확인

---

### [TF7R-P7-05] `tests/chaos/test_validation_degrade.py`

**시나리오**:
1. `prev_hud=None` → ContinuityValidator → `degraded=True`, `passed=True` 반환
2. `encyclopedia.npcs={}` → V0128 경로 → DEGRADED 경고 로그 발생
3. `protagonist_name` 누락 → validation_context 주입 시도 후 경고 로그

---

### [TF7R-P7-06] `tests/chaos/test_feedback_loop.py`

**시나리오**:
1. Stage4 BLOCKING 실패 → `FailureLearner.record_failure(stage=4)` 호출 확인
2. Stage4 REJECT → `quality_dashboard.record_validation(stage=4, decision="REJECT")` 호출 확인
3. Stage4 REJECT → `pass_rate_monitor.record_attempt()` 호출 확인
4. Stage4 REJECT → `adaptive_retry.record_failure()` 호출 확인
5. 위 4개 호출이 **단일 REJECT 경로**에서 모두 발생함 확인

---

### [TF7R-P7-07] `tests/chaos/test_stage3_metrics.py`

**시나리오**:
1. Stage3 Blueprint PASS → `quality_dashboard.record_validation(stage=3, decision="PASS")` 호출 확인
2. Stage3 Blueprint REJECT(한도 초과) → `quality_dashboard.record_validation(stage=3, decision="REJECT")` 호출 확인

---

## 패치 진행 상태

| # | 패치 ID | 상태 | 완료 커밋 |
|---|---|---|---|
| 1 | TF7R-P1-01 | ✅ 완료 | state_delta_tracker.py rollback_to/reset 추가 |
| 2 | TF7R-P1-02 | ✅ 완료 | emotion_tracker.py rollback_to/clear 추가 |
| 3 | TF7R-P1-03 | ✅ 완료 | project_service.py callbacks + main_a.py 배선 |
| 4 | TF7R-P1-04 | ✅ 완료 | _assert_rollback_invariants() 추가 |
| 5 | TF7R-P3-01 | ✅ 완료 | continuity_validator.py prev_hud DEGRADED |
| 6 | TF7R-P3-02 | ✅ 완료 | stage4_interview_round.py protagonist_name 주입 |
| 7 | TF7R-P3-03 | ✅ 완료 | director_auditor.py V0128 encyclopedia.npcs DEGRADED |
| 8 | TF7R-P3-04 | ✅ 완료 | context_advisor.py slot_max_chars_default YAML 참조 |
| 9 | TF7R-P6-01 | ✅ 완료 | validation_orchestrator.py TIER1→FailureLearner 환류 |
| 10 | TF7R-P6-02 | ✅ 완료 | stage3_orchestrator.py QualityDashboard stage=3 계측 |
| 11 | TF7R-P7-01 | ✅ 완료 | tests/chaos/test_rollback_boundary.py (8 tests) |
| 12 | TF7R-P7-02 | ✅ 완료 | tests/chaos/test_blueprint_none.py (5 tests) |
| 13 | TF7R-P7-03 | ✅ 완료 | tests/chaos/test_dead_npc_hard_block.py (7 tests) |
| 14 | TF7R-P7-04 | ✅ 완료 | tests/chaos/test_partial_commit.py (6 tests) |
| 15 | TF7R-P7-05 | ✅ 완료 | tests/chaos/test_validation_degrade.py (5 tests) |
| 16 | TF7R-P7-06 | ✅ 완료 | tests/chaos/test_feedback_loop.py (3 tests) |
| 17 | TF7R-P7-07 | ✅ 완료 | tests/chaos/test_stage3_metrics.py (4 tests) |

---

## 실행 전 확인 사항

1. `ValidationResult` 클래스에 `degraded: bool = False` 필드 존재 여부 확인 (P3-01 전제)
2. `stage3_orchestrator.py`에서 `quality_dashboard` 주입 경로 확인 (P6-02 전제)
3. `context_advisor.py`에서 `_threshold()` 또는 `ThresholdHelper` 접근 방식 확인 (P3-04 전제)
4. `tests/chaos/` 디렉토리 생성 필요 (P7 전체)
