# Stage 3 전수 감사 리포트 (2026-02-22)

**감사 범위**: Stage 3 Blueprint 오케스트레이션 전체 파이프라인
**감사 파일**: 8개 주요 파일 + 관련 테스트 2개 + 프롬프트 YAML 2개

| 파일 | 줄수 | 역할 |
|------|------|------|
| `modules/core/stage3_orchestrator.py` | 582 | 메인 오케스트레이터 |
| `modules/core/stage3_context.py` | 112 | DI 컨텍스트 (20슬롯) |
| `modules/domain/agents/three_phase_blueprint_generator.py` | 586 | 3단계 파이프라인 코어 |
| `modules/domain/agents/blueprint_ensemble.py` | 770 | 앙상블 후보 생성 |
| `modules/domain/agents/blueprint_constraint_compiler.py` | 437 | 제약 수집 |
| `modules/domain/agents/unified_blueprint_validator.py` | 445 | 사전검사 + Director 판정 |
| `modules/models/blueprint.py` | 76 | Pydantic 모델 |
| `config/prompts/ensemble.yaml` | 339 | 프롬프트 템플릿 |
| `config/prompts/blueprint_generator.yaml` | 21 | 패치 모드 프롬프트 |

---

## 요약

- **P0 (차단급 버그)**: 1건
- **P1 (품질 이슈)**: 5건
- **P2 (스타일/경미)**: 4건
- **개선 아이디어**: 6건

---

## P0 -- 차단급 버그

### P0-1: `_semantic_context` 항상 빈 문자열 -- 벡터 시맨틱 검색 미작동

**파일**: `modules/core/stage3_orchestrator.py` L420
**코드**:
```python
_bp_semantic_ctx = ""
```

`_bp_semantic_ctx`는 `""` 로 초기화된 뒤 어디서도 갱신되지 않는다. `_generate_blueprint()` 안에서 값이 빈 문자열인 채로 `ctx.agents["three_phase_bp"].generate(..., semantic_context=_bp_semantic_ctx, ...)` 에 전달된다. `three_phase_blueprint_generator.py` L124에서 `semantic_context`가 빈 문자열이면 `feedback`에 추가되지 않으므로, 과거 유사 Blueprint 시맨틱 참조 기능은 완전히 비활성 상태이다.

`vec_memory`나 `context_advisor`(SC 모듈)로부터 시맨틱 컨텍스트를 조회하는 코드가 Stage 3 어디에도 없다. Stage 4에서는 이 기능이 구현되어 있으나, Stage 3에서는 파라미터만 존재하고 실제 데이터 주입이 누락된 상태이다.

**영향**: Stage 3에서 과거 에피소드와 유사한 Blueprint를 참조하여 반복/모순을 방지하는 시맨틱 컨텍스트가 전혀 활용되지 않는다. Blueprint 품질에 직접 영향.

**수정 제안**:
```python
# _generate_blueprint() 내 StageSpinner 블록 시작 부분에 추가
if hasattr(ctx, 'current_project') and ctx.current_project:
    try:
        from modules.core.vec_memory import VecMemory
        _vm = VecMemory(ctx.current_project.db)
        _query = f"제{working_ep}화 Blueprint 핵심 이벤트"
        _results = _vm.search(_query, top_k=3)
        if _results:
            _bp_semantic_ctx = "\n".join(
                f"- [ep{r.get('ep_num','?')}] {r.get('text','')[:200]}"
                for r in _results
            )
    except Exception:
        pass
```

---

## P1 -- 품질 이슈

### P1-1: `_handle_failure`에서 무조건 `break: True` 반환 -- 첫 실패에 즉시 중단

**파일**: `modules/core/stage3_orchestrator.py` L576-581
**코드**:
```python
if new_fail_count >= 3:
    ctx.ui.log(f"...")
return {
    "next_ep": working_ep,  # 현재 에피소드에 머무름
    ...
    "break": True,  # 오케스트레이터 루프 종료
}
```

`_handle_failure()`는 `fail_count` 값에 관계없이 항상 `"break": True`를 반환한다. 주석에는 "연속 3회 실패로 중단"이라 되어 있지만 실제로는 1회 실패에도 즉시 중단된다. `_process_single_episode()` → `_handle_failure()` → `result.get("break")` → `while` 루프 탈출.

이는 `three_phase_blueprint_generator.py` 내부의 `max_retries=4` (최대 5회 시도)와 모순된다. Generator 내부에서 이미 5회 재시도를 모두 소진한 후에야 `_handle_failure`로 오기 때문에 오케스트레이터 레벨의 재시도가 의미가 없다. 하지만 코드의 의도(주석 "[TF-S3-02] 순차 의존성 보존")와 실제 동작이 다르다.

**영향**: 연속 실패 카운터(`fail_count >= 3`)가 로깅 외에는 무의미. 코드가 의도와 다르게 동작하지만, 현재 파이프라인에서는 "Blueprint 미생성 시 후속 에피소드 불가" 특성상 즉시 중단이 올바른 행동이므로, 실제 런타임 손상은 없다.

**수정 제안**: 주석을 실제 동작과 일치시키거나, `fail_count < 3`이면 `break: False`를 반환하여 재시도 허용.

---

### P1-2: Validator가 `self.context`에서 `get_causal_history_summary()` 호출 -- ProjectManager에만 존재

**파일**: `modules/domain/agents/unified_blueprint_validator.py` L220-222
**코드**:
```python
history_summary=str(self.context.get_causal_history_summary())
if hasattr(self.context, "get_causal_history_summary")
else "",
```

`self.context`는 `UnifiedBlueprintValidator.__init__()`에서 받은 `context` 인자인데, 이는 `ThreePhaseBlueprintGenerator.__init__()` → `BlueprintEnsembleGenerator.__init__()` 경로에서 `ProjectManager` 인스턴스(`self.current_project`)가 전달된다. `ProjectManager`에는 `get_causal_history_summary()`가 존재하므로(`project_manager.py` L627) 동작은 한다.

그러나 `hasattr` 체크 없이 `str(self.context.get_causal_history_summary())`가 먼저 평가될 수 있는 위치에 놓여 있다. 실제로는 Python의 삼항 연산자 특성상 `hasattr`가 먼저 평가되므로 현재는 안전하다.

**실제 문제**: `get_causal_history_summary()`는 `db.get_causal_summary_chain(limit=5)`를 호출하는데, DB에 `causal_summaries` 테이블이 없으면 SQLite 에러가 발생한다. `hasattr` 보호만으로는 DB 에러를 잡지 못한다.

**수정 제안**: try-except 래핑 추가:
```python
try:
    history_summary = str(self.context.get_causal_history_summary()) if hasattr(self.context, "get_causal_history_summary") else ""
except Exception:
    history_summary = ""
```

---

### P1-3: `_strategy_feedback`이 rejected_strategy에만 전달 -- 전략 미매치 시 피드백 손실

**파일**: `modules/domain/agents/blueprint_ensemble.py` L191-195
**코드**:
```python
_strategy_feedback = (
    strategy_specific_feedback
    if (strategy.get("name") == rejected_strategy and strategy_specific_feedback)
    else ""
)
```

재시도 시 `strategy_specific_feedback`(점수 분해, 검증 경고 등 구체적 피드백)이 이전에 REJECT된 전략과 이름이 일치하는 전략에게만 전달된다. 만약 3개 전략 모두 다른 이름이라면 (action_focused, emotion_focused, dialogue_focused), rejected_strategy가 `"action_focused"`이면 나머지 2개 전략은 `_strategy_feedback=""`를 받게 된다.

**영향**: 동일 전략이 재시도될 때만 구체적 피드백을 받고, 다른 전략들은 점수 분해나 경고 없이 생성한다. 이는 의도적일 수 있으나, rejected 전략과 다른 전략 모두에게 공통 피드백(왜 REJECT되었는지)을 전달하면 전반적 품질이 올라갈 수 있다.

**수정 제안**: 공통 피드백은 `feedback` 파라미터로 이미 전달되므로 현재 동작이 의도적이라면 주석 보강. 아니라면 `_strategy_feedback`을 전 전략에 전달.

---

### P1-4: `continuity_feedback` REJECT 후 `feedback` 변수에 누적 -- retry간 피드백 오염

**파일**: `modules/domain/agents/three_phase_blueprint_generator.py` L329
**코드**:
```python
feedback += f"\n[연속성 오류]\n{continuity_feedback}"
```

Phase 3의 연속성 검사 REJECT 시 `feedback` 지역변수에 문자열을 `+=`로 누적한다. 하지만 L157-166에서 `[TF-S3-04]` 패치로 `_initial_feedback`을 보존하고 매 retry마다 `_attempt_feedback = _initial_feedback`로 리셋하고 있다.

문제: L329의 `feedback += ...`는 `_attempt_feedback`이 아닌 `feedback`(외부 루프 변수)를 수정한다. 그런데 `feedback`는 L297에서도 `feedback = "Blueprint 생성 실패. 다시 시도하세요."`로 덮어쓰일 수 있고, L390에서 `feedback = validation_result.get("feedback", "검증 실패")`로도 덮어쓰인다.

**영향**: 연속성 REJECT 후 다음 retry에서 `feedback` 값이 `_initial_feedback`이 아닌 오염된 값을 보유하나, L161에서 `_attempt_feedback = _initial_feedback`로 리셋하므로 실제 LLM에 전달되는 피드백은 깨끗하다. 다만 `_build_strategy_feedback()`는 `_prev_selection_reason`, `_prev_validation_warnings` 등 별도 변수로 구성되므로 문제 없음. **코드 가독성 이슈**이나 실제 버그는 아님.

---

### P1-5: `_evaluate_candidate` 메서드 미사용 (Dead Code)

**파일**: `modules/domain/agents/blueprint_ensemble.py` L407-431
**메서드**: `_evaluate_candidate(self, candidate, constraint_block)`

이 메서드는 후보의 `integrated_scenario` 길이 기반으로 점수를 매기는 로직인데, 코드베이스 어디에서도 호출되지 않는다. `generate_ensemble()` 에서는 Python 최소 기준 필터링(L259-278)을 직접 수행하고, Director에게 전체 후보를 전달한다. `_evaluate_candidate`는 V60.80 이전 레거시.

**영향**: 죽은 코드. 삭제해도 무방.

---

## P2 -- 스타일/경미

### P2-1: `collect_warnings` 메서드 미사용

**파일**: `modules/domain/agents/blueprint_ensemble.py` L433-495
**메서드**: `collect_warnings(self, candidate, constraint_block)`

`_evaluate_candidate`과 마찬가지로 코드베이스에서 호출되지 않는다. V60.80 이전 Director 주의 포인트 수집용이었으나, 현재는 `UnifiedBlueprintValidator._python_pre_validate()`가 이 역할을 대체.

---

### P2-2: `_format_prev_info` 레거시 메서드 존재

**파일**: `modules/domain/agents/blueprint_ensemble.py` L636-694
**메서드**: `_format_prev_info(self, prev_blueprint)`

`_format_prev_info_expanded()`가 내부에서 `_format_prev_info()`를 호출하므로 완전한 죽은 코드는 아니다. 하지만 외부에서 직접 호출하는 곳은 없으며, `_format_prev_info_expanded`의 내부 도우미로만 사용된다. 가독성을 위해 `_`를 2개 붙이거나 축소 가능.

---

### P2-3: `ContextLimits.MAX_CONTEXT_CHARS` 200K 절삭 메시지 오해 가능

**파일**: `modules/core/stage3_orchestrator.py` L434
**코드**:
```python
_prev_ms_text_for_bp = (
    _prev_ms_text_for_bp[: ContextLimits.MAX_CONTEXT_CHARS] + "\n... (200K자 절삭)"
)
```

`ContextLimits.MAX_CONTEXT_CHARS`의 실제 값이 200,000이 아닐 수 있는데 "200K자 절삭" 하드코딩 메시지를 사용. 상수 값이 변경되면 메시지가 부정확해짐.

**수정 제안**:
```python
f"\n... ({ContextLimits.MAX_CONTEXT_CHARS:,}자 절삭)"
```

---

### P2-4: `_generate_feedback` 메서드 미사용

**파일**: `modules/domain/agents/unified_blueprint_validator.py` L417-439
**메서드**: `_generate_feedback(self, issues)`

이 메서드는 `UnifiedBlueprintValidator` 내에서 정의되어 있지만 호출되는 곳이 없다. Director REJECT 시 피드백은 Director가 직접 생성하고, Python 사전검사 결과는 `issues` 리스트로 직접 전달된다.

---

## 개선 아이디어

### I-1: Stage 3 시맨틱 컨텍스트 활성화 (P0-1 연계)

현재 `_bp_semantic_ctx`가 항상 빈 문자열이다. Stage 4에서는 `VecMemory`나 `Smart Context Retrieval`을 활용하여 과거 원고/Blueprint와의 유사도 기반 참조를 수행한다. Stage 3에도 동일한 메커니즘을 적용하면:

1. 과거 유사 Blueprint의 실패 패턴을 미리 회피
2. NPC/이벤트 중복 등장 방지
3. 위치/시간 연속성 추가 검증 소스 확보

**예상 효과**: Blueprint REJECT율 10-15% 감소 (시맨틱 중복 감지 → 사전 회피)

---

### I-2: 앙상블 전략 적응형 가중치

현재 3개 전략(action, emotion, dialogue)의 가중치는 동일하다. 이전 에피소드들의 전략 채택 이력(`director_selections` 테이블)을 참조하여:

1. 최근 3화 연속 같은 전략이 채택되면 해당 전략 가중치 감소 → 다양성 확보
2. 특정 장르에서 특정 전략의 PASS율이 높으면 해당 전략 우선 배치
3. Arc 위치(시작/중간/끝)에 따라 전략 가중치 자동 조정 (예: Arc 마지막 화는 action_focused 우선)

이 로직은 Python이 데이터 수집만 하고 LLM이 최종 판단하는 원칙에 부합.

---

### I-3: Blueprint Pydantic 모델 강화

현재 `modules/models/blueprint.py`의 `Blueprint` 모델은 `extra="allow"`로 LLM의 미정의 키를 모두 수용한다. 이는 유연하지만, Blueprint의 핵심 구조를 보장하지 못한다.

강화 제안:
- `scene_breakdown`을 `dict[str, SceneBreakdown]`으로 타입 제한 (SceneBreakdown은 type, title, location, characters, summary, tension, key_events 필드)
- `integrated_scenario`에 `min_length=800` 커스텀 validator 추가
- `ending_state`를 필수 필드로 승격 (`default_factory` 제거)

이렇게 하면 `validate_blueprint()` 호출 시 구조적 결함이 Pydantic 레벨에서 바로 감지된다.

---

### I-4: Constraint Compiler 에피소드 포커스 추출 정규식 강화

`_extract_episode_focus()` (L186)의 정규식:
```python
pattern = rf"\[제\s*{ep_num}\s*화[^\]]*\](.*?)(?=\[제\s*\d+\s*화|\Z)"
```

이 패턴은 `[제 5화]` 또는 `[제5화]` 형식만 매칭한다. LLM이 `[5화]`, `### 제5화`, `**제5화**`, `제5화:` 등 다양한 형식으로 생성할 수 있다.

**제안**: 폴백 패턴 추가:
```python
alt_patterns = [
    rf"\[제\s*{ep_num}\s*화[^\]]*\](.*?)(?=\[제\s*\d+\s*화|\Z)",
    rf"#{1,3}\s*제\s*{ep_num}\s*화(.*?)(?=#{1,3}\s*제\s*\d+\s*화|\Z)",
    rf"제\s*{ep_num}\s*화\s*[:：](.*?)(?=제\s*\d+\s*화|\Z)",
]
```

---

### I-5: 이전 원고 로드 최적화 (N+1 쿼리 문제)

`_generate_blueprint()` L425-431:
```python
for _ms_ep in range(max(1, working_ep - 30), working_ep):
    _ms_data = ctx.current_project.db.get_manuscript(_ms_ep)
```

최대 30개의 개별 DB 쿼리를 순차 실행한다. `get_manuscript()`는 매번 `SELECT * FROM manuscripts WHERE ep_num = ?`를 호출하므로, 30회 DB 접근이 발생한다.

**제안**: `db.get_recent_manuscripts(before_ep=working_ep, limit=30)` 단일 쿼리로 대체. 이미 `DBManager`에 `get_recent_manuscripts()` 메서드가 존재한다.

```python
# AS-IS (N+1)
for _ms_ep in range(max(1, working_ep - 30), working_ep):
    _ms_data = ctx.current_project.db.get_manuscript(_ms_ep)

# TO-BE (단일 쿼리)
_recent_manuscripts = ctx.current_project.db.get_recent_manuscripts(
    before_ep=working_ep, limit=30
)
for _ms_data in _recent_manuscripts:
    _ms_text = _ms_data.get("content", "")
    if _ms_text:
        _prev_ms_for_bp.append(f"━━━ 제{_ms_data['ep_num']}화 원고 ━━━\n{_ms_text}")
```

**예상 효과**: DB I/O 30회 → 1회. 30화 이상 진행된 프로젝트에서 체감 성능 향상.

---

### I-6: Blueprint 생성/저장 사이 WorldState/FactLedger 업데이트 누락

Stage 3 오케스트레이터에서 Blueprint 생성 성공 후 `save_episode_blueprint()`와 `_safe_commit()`을 호출하지만, `WorldStateManager`나 `FactLedger`에 새 Blueprint의 상태 변화를 반영하지 않는다.

현재는 Stage 4에서 원고 생성 후에만 WorldState/FactLedger를 업데이트하는 구조이므로 Stage 3에서의 업데이트가 필수는 아니다. 하지만 Stage 3 내에서 연속 에피소드 Blueprint를 생성할 때 (예: 1화~10화 연속), 2화 Blueprint 생성 시 1화 Blueprint에서 발생한 NPC 사망/이동/관계 변화가 WorldState에 반영되지 않아 정보가 stale할 수 있다.

이 문제는 현재 `state_tracker.full_extract_from_arcs()`가 Arc 레벨의 state_changes를 추적하므로 부분적으로 완화되지만, Blueprint 레벨의 세밀한 상태 변화(특정 화에서 NPC가 사망하는 경우)는 놓칠 수 있다.

**제안**: Blueprint 저장 후 `state_tracker`의 NPC 레지스트리를 Blueprint의 `scene_breakdown`으로부터 증분 업데이트하는 경량 메서드 추가.

---

## 연결성 검증 결과

### Stage 2 → Stage 3 연결

| 항목 | 상태 | 비고 |
|------|------|------|
| Arc 데이터 전달 | OK | `ctx.current_project.arcs` → `get_arc_context_for_episode()` |
| tactical_doc 참조 | OK | `constraint_compiler._extract_episode_focus()` |
| state_changes 전달 | OK | `_summarize_state_changes()` |
| constraint_summary | OK (경고 있음) | `arc_data.get("constraint_summary")` -- 없으면 경고 로그만 |
| beat_sequence 폴백 | OK | 정규식 실패 시 폴백 |

### Stage 3 → Stage 4 연결

| 항목 | 상태 | 비고 |
|------|------|------|
| Blueprint DB 저장 | OK | `save_episode_blueprint()` → `save_blueprint()` |
| Blueprint DB 조회 | OK | Stage 4에서 `get_blueprint(ep_num)` |
| `_stage3_meta` 전달 | 미사용 | Stage 4에서 `_stage3_meta` 참조 없음 |
| `quality_risk` 전달 | 미사용 | Stage 4에서 `quality_risk` 참조 없음 |
| `quality_gate_failed` 전달 | 미사용 | Stage 4에서 미참조 |

`_stage3_meta`, `quality_risk`, `quality_gate_failed` 메타데이터가 Blueprint에 주입되지만 Stage 4에서는 전혀 읽지 않는다. 이 정보를 Stage 4의 Chief Writer에게 전달하면 "이 Blueprint는 품질 위험 마크가 있으니 더 신중하게 작성하라"는 시그널로 활용할 수 있다.

### DI 슬롯 검증

Stage3Context의 20슬롯 전부가 `from_app()`에서 올바르게 매핑되고, 테스트(`test_from_app_all_slots`)에서 검증됨. 누락 없음.

---

## 테스트 커버리지 평가

| 파일 | 테스트 유무 | 커버리지 수준 |
|------|------------|-------------|
| `stage3_orchestrator.py` | test_stage3_orchestrator.py (427줄, 17 테스트) | 양호 |
| `stage3_context.py` | 위 파일에 포함 | 양호 |
| `three_phase_blueprint_generator.py` | test_blueprint_patch_mode.py (191줄, 6 테스트) | 부분적 (패치 모드만) |
| `blueprint_ensemble.py` | 전용 테스트 없음 | 부족 |
| `blueprint_constraint_compiler.py` | 전용 테스트 없음 | 부족 |
| `unified_blueprint_validator.py` | 전용 테스트 없음 | 부족 |
| `models/blueprint.py` | 전용 테스트 없음 | 부족 |

`three_phase_blueprint_generator.py`의 핵심 `generate()` 메서드 전체 흐름(Phase 1→2→3, retry, continuity REJECT, quality gate, 긴급 폴백)에 대한 통합 테스트가 부족하다. 오케스트레이터 테스트는 `three_phase_bp.generate`를 모킹하므로 내부 로직은 검증하지 않는다.

---

## 총평

Stage 3 파이프라인은 전반적으로 안정적이며, 에러 핸들링과 비차단 패턴이 잘 적용되어 있다. DI 전환(19슬롯)이 완료되어 테스트 용이성이 확보되었고, 디렉터주권주의 원칙이 코드 전반에 잘 반영되어 있다.

주요 우려사항은:
1. **시맨틱 컨텍스트 미작동** (P0-1) -- Blueprint 품질에 직접 영향하는 기능이 파라미터만 존재하고 데이터가 주입되지 않음
2. **Dead code 축적** -- `_evaluate_candidate`, `collect_warnings`, `_generate_feedback` 등 V60.80 이전 레거시 메서드 4개가 잔존
3. **Stage 3 → Stage 4 메타데이터 미활용** -- `_stage3_meta`/`quality_risk`가 주입되지만 Stage 4에서 읽지 않음
4. **N+1 쿼리** -- 이전 원고 30개 개별 조회 → 단일 쿼리 최적화 가능
