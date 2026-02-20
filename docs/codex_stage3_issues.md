# 📋 Codex Stage 3 이슈 리포트

> **생성일**: 2026-02-20  
> **대상 범위**: `modules/core/stage3_*.py` (2개) + `modules/domain/agents/blueprint_*.py`, `three_phase_blueprint_generator.py`, `continuity_blueprint.py` (5개) + `models/blueprint.py` (1개)  
> **총 코드량**: ~3,400 LOC (8개 파일)

---

## 이슈 요약

| # | 심각도 | 파일 | 이슈 | 라인 |
|---|--------|------|------|------|
| 1 | 🟠 Medium | `blueprint_ensemble.py` | genre 폴백 `"wuxia"` 하드코딩 (조건부 리스크) | L166, L171, L321 |
| 2 | 🟠 Medium | `blueprint_ensemble.py` | `arc_ensemble.py`와 ThreadPoolExecutor 보일러플레이트 ~70줄 중복 | L186-L245 |
| 3 | 🟠 Medium | `three_phase_blueprint_generator.py` | `generate()` 메서드 382줄 | L57-L438 |
| 4 | 🟠 Medium | `continuity_blueprint.py` | 117줄 인라인 프롬프트 (모듈 스코프) | L16-L132 |
| 5 | 🟡 Minor | `stage3_orchestrator.py` | DI 트레이드오프: `app` lazy init 후 `ctx` 동기화 패턴 | L182, L205, L222, L89-L91 |
| 6 | 🟡 Minor | `continuity_blueprint.py` | 아이템 비교 기준 이원화 (공통 함수 재사용 vs Stage 2 별도 기준) | L317 |

---

## 상세 분석

---

### 🟠 이슈 #1: genre 폴백 `"wuxia"` 하드코딩

**파일**: [blueprint_ensemble.py](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py#L166)  
**라인**: 166, 171, 321

```python
genre = "wuxia"  # L166 — 기본값
try:
    if hasattr(self, "context") and hasattr(self.context, "db"):
        bible = self.context.db.load_anchor("bible")
        if bible:
            genre = bible.get("_genre", "wuxia")  # L171 — 폴백값
```

```python
genre: str = "wuxia",  # L321 — _generate_single 기본 파라미터
```

**문제**: Stage 2의 `arc_ensemble.py`와 동일한 패턴. DB 로드 실패 시 `"wuxia"`로 폴백되며, 특히 원시인 모드에서 장르별 제약 생성 시 잘못된 장르 컨텍스트가 주입될 수 있습니다.

**주의**: 이 리스크는 `DB 로드 실패` 또는 `장르 전달 누락`일 때 조건부로 발생합니다.

**제안**: Stage 2 이슈 #3과 동일 — `context.selected_genre`를 1차 소스로 사용.

---

### 🟠 이슈 #2: `arc_ensemble.py`와 ThreadPoolExecutor 보일러플레이트 중복

**파일**: [blueprint_ensemble.py](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/blueprint_ensemble.py#L186)  
**라인**: 186-245 (vs `arc_ensemble.py` L134-200)

**문제**: `blueprint_ensemble.py`와 `arc_ensemble.py`의 병렬 실행 블록이 사실상 동일한 패턴입니다:
1. ThreadPoolExecutor에 submit → futures dict 관리
2. `as_completed()` + `ENSEMBLE_TIMEOUT` / `SINGLE_CANDIDATE_TIMEOUT`
3. `FutureTimeoutError` 2중 처리 (개별 + 전체)
4. `finally`에서 `f.cancel()` 호출
5. 전체 `try-except`로 크래시 방지

이 ~70줄 블록이 두 파일에 거의 동일하게 복사되어 있으며, 타임아웃 값(300초/240초)도 동일합니다.

**영향**: 하나를 수정하면 다른 하나도 동일하게 수정해야 하는 "샷건 서저리" 위험.

**제안**: `modules/core/ensemble_executor.py`에 공통 병렬 실행 헬퍼를 추출:
```python
def run_ensemble(strategies, worker_fn, *, max_workers=3, 
                 ensemble_timeout=300, single_timeout=240):
    """공통 앙상블 병렬 실행"""
    ...
```

---

### 🟠 이슈 #3: `generate()` 메서드 382줄

**파일**: [three_phase_blueprint_generator.py](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/three_phase_blueprint_generator.py#L57)  
**라인**: 57-438 (382줄)

**문제**: `generate()`가 Phase 1(제약수집), Phase 2(앙상블생성), Phase 3(검증+Director판정)과 Patch Mode 분기, ASP(Adversarial Self-Play) 로직, Quality Gate 검사를 모두 포함합니다. Stage 2의 685줄 메서드보다는 낫지만, 여전히 단일 메서드로서는 과대합니다.

**영향**: 특정 Phase만 디버깅하거나 테스트하기 어려움.

**제안**: Phase별로 메서드 분리:
```
generate()
├── _phase1_compile_constraints(...)
├── _phase2_ensemble_or_patch(...)  
└── _phase3_validate_and_judge(...)
```

---

### 🟠 이슈 #4: 117줄 인라인 프롬프트 (`CONTINUITY_INSPECTION_PROMPT`)

**파일**: [continuity_blueprint.py](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/continuity_blueprint.py#L16)  
**라인**: 16-132

**문제**: `CONTINUITY_INSPECTION_PROMPT`가 117줄(~3,500자) 크기의 모듈 레벨 상수로 정의되어 있습니다. Stage 2의 `continuity_arc.py`(200줄 인라인 프롬프트)와 동일한 패턴입니다.

같은 파이프라인의 다른 에이전트들(`blueprint_ensemble.py`, `unified_blueprint_validator.py`)은 `PromptLoader`를 통해 외부 파일에서 프롬프트를 로드합니다.

**제안**: `prompts/` 디렉토리로 이동하고 `PromptLoader`를 사용.

---

### 🟡 이슈 #5: DI 트레이드오프 — `app` lazy init 후 `ctx` 동기화

**파일**: [stage3_orchestrator.py](file:///c:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py#L182)  
**라인**: 182, 205, 222

```python
# L182 — _init_state_tracker_if_needed()
app.state_tracker = StateTracker(preset_registry=app.preset_registry, ...)

# L205 — _init_world_state_if_needed()
app.world_state = WorldStateManager(app.current_project.db)

# L222 — _init_fact_ledger_if_needed()  
app.fact_ledger = FactLedger(app.current_project.db)
```

그 후 L89-91에서 `ctx`에 동기화:
```python
ctx.state_tracker = getattr(self.app, "state_tracker", None)
ctx.world_state = getattr(self.app, "world_state", None)
ctx.fact_ledger = getattr(self.app, "fact_ledger", None)
```

**문제**: `Stage3Context`를 도입했지만 lazy init은 `app` 객체를 갱신한 뒤 `L89-L91`에서 `ctx`에 재동기화합니다. 현재 흐름에서는 즉시 동기화가 있어 동작상 문제는 크지 않지만, 향후 `app` 재초기화 경로가 늘어나면 `ctx`와 분기될 여지가 있습니다.

**제안**: lazy init을 `ctx` 속성 자체에서 수행하거나, `app` 변이 대신 `ctx`에만 주입.

---

### 🟡 이슈 #6: 아이템 비교 기준 이원화 (공통 함수 재사용 vs Stage 2 별도 기준)

**파일**: [continuity_blueprint.py](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/continuity_blueprint.py#L317)  
**라인**: 317

```python
if self._ci._is_same_item(curr_item, prev_item):
```

**문제**: Stage 3은 `self._ci._is_same_item()` 공통 함수를 재사용하지만, Stage 2의 일부 검증/보정 경로는 별도 비교 기준을 사용합니다. 구현이 추가된 문제라기보다, **스테이지 간 판정 기준 불일치** 리스크가 핵심입니다.

**제안**: Stage 2 이슈 #5의 `modules/core/item_utils.py` 제안에 통합.

---

## 긍정적 관찰

Stage 3 코드베이스는 Stage 2에 비해 전반적으로 **양호**합니다:

- **`stage3_orchestrator.py`**: 약 565줄로 적절한 크기이며, `_process_single_episode`, `_handle_success`, `_handle_failure` 등으로 잘 분해됨
- **`Stage3Context`**: `__slots__` 사용, `from_app()` 팩토리 메서드로 깔끔한 DI 구현
- **`blueprint_constraint_compiler.py`**: 순수 Python, LLM 호출 없음, 잘 분리된 단일 책임
- **`models/blueprint.py`**: Pydantic v2 + graceful degradation, `validate_blueprint()`로 간결한 검증
