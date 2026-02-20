# Stage 2/3/4 통과율 개선 Codex 실행 오더 (정리본)

> 목표: 재시도 루프의 실통과율을 올리되, 오버엔지니어링 없이 실제 품질/비용 효율을 개선한다.
> 원칙: Director 최종 판정권 유지, 기존 패치 모드 유지, 실패 시 비차단(fail-open) 운영.

---

## 0. 현재 파이프라인 요약

### Stage 4
- `modules/core/stage4_interview_round.py`
- `ChiefWriter.generate_ensemble()` 3후보 생성 (`balanced / narrative / tension`)
- Director 평가 후 PASS/REJECT
- REJECT 시 `previous_attempt`로 다음 라운드 전달

### Stage 3
- `modules/core/stage3_orchestrator.py`
- `three_phase_blueprint_generator.generate()` 호출
- 내부에서 `BlueprintEnsembleGenerator.generate_ensemble()` 3후보 생성 (`action_focused / emotion_focused / dialogue_focused`)
- Director 평가 후 PASS/REJECT

### Stage 2
- `modules/core/stage2_preflight.py`
- `four_phase.generate()` 호출
- Director 평가 후 PASS/REJECT, 피드백 전달

---

## 1. 핵심 문제

1. 전략별 피드백이 분리되지 않아 후보 3개가 비슷한 방향으로 수렴함.
2. 패치 가능 구간에서도 3후보를 매번 다시 생성해 비용이 불필요하게 증가함.

---

## 2. 대원칙

1. Director만 PASS/REJECT 최종 판정.
2. 보조 모듈(ASP/ToT/MAD)은 제안/교정만 수행.
3. 모듈 실패 시 파이프라인 중단 금지(기존 경로로 폴백).
4. API/DB 계약은 현재 코드 기준으로 맞춘다.

---

## Phase 1: 피드백 분리 (공통 vs 전략별)

### 1-1. ChiefWriter 쪽 분리
- 파일: `modules/domain/agents/chief_writer.py`
- `generate_ensemble()` 시그니처 확장:
  - `strategy_specific_feedback: str = ""`
  - `rejected_strategy: str = ""`

핵심 루프 예시:

```python
for strategy in strategies:  # strategy: "balanced" | "narrative" | "tension"
    if strategy == rejected_strategy:
        _feedback = director_feedback + strategy_specific_feedback
    else:
        _feedback = director_feedback
```

### 1-2. BlueprintEnsembleGenerator 쪽 분리
- 파일: `modules/domain/agents/blueprint_ensemble.py`
- `generate_ensemble()` 시그니처 확장:
  - `strategy_specific_feedback: str = ""`
  - `rejected_strategy: str = ""`

핵심 루프 예시:

```python
for strategy in self.strategies:  # dict, strategy["name"] 사용
    if strategy["name"] == rejected_strategy:
        _fb = feedback + strategy_specific_feedback
    else:
        _fb = feedback
```

### 1-3. Stage 3에서 전략 메타 유지
- 파일: `modules/domain/agents/three_phase_blueprint_generator.py`
- REJECT 시 다음 라운드를 위해 아래 정보 저장:
  - `rejected_strategy`
  - `score_breakdown`
  - `selection_reason`

---

## Phase 2: 단일 후보 정제 모드

### 2-1. Stage 4 단일 후보 정제
- 파일: `modules/core/stage4_interview_round.py`, `modules/domain/agents/chief_writer.py`
- 조건: 패치 구간(score >= rewrite threshold)에서 전체 3후보 재생성 대신 이전 선택 전략 1개 우선 정제.
- 실패 시 기존 3후보 경로로 폴백.
- 중요: 현재 `stage4_interview_round.py`의 `previous_attempt["strategy"]`는 Director 선택 라벨(`A/B/C`)일 수 있으므로, 단일 전략 키로 직접 쓰면 안 된다.
  - `previous_attempt["selected_strategy_key"]`를 별도로 저장해 `single_strategy` 입력으로 사용한다.
  - 저장값은 `director_result["selected_candidate"]["strategy"]` 기준(`balanced/narrative/tension`).

### 2-2. ChiefWriter single_strategy
- 파일: `modules/domain/agents/chief_writer.py`
- `generate_ensemble(..., single_strategy: str = "")` 추가.

```python
if single_strategy:
    _target = [s for s in strategies if s == single_strategy]
    if _target:
        strategies = _target
```

### 2-3. BlueprintEnsembleGenerator single_strategy
- 파일: `modules/domain/agents/blueprint_ensemble.py`
- `generate_ensemble(..., single_strategy: str = "")` 추가.

```python
_active_strategies = self.strategies
if single_strategy:
    _filtered = [s for s in self.strategies if s["name"] == single_strategy]
    if _filtered:
        _active_strategies = _filtered
```

---

## Phase 3: 피드백 스키마 정규화

- 파일: `modules/domain/agents/three_phase_blueprint_generator.py`, `modules/core/stage2_preflight.py`
- 문자열 피드백만 넘기지 말고 구조화 메타를 함께 전달:
  - `score_breakdown`
  - `selection_reason`
  - `validation_warnings`

---

## Phase 4: Stage 3 PASS_WITH_WARNING 수용

- 파일: `modules/core/stage3_orchestrator.py`
- 현 상태 점검: generator는 `PASS_WITH_WARNING`을 낼 수 있음.
- orchestrator 성공 분기 조건 확장:

```python
if blueprint and pipeline_result.get("final_verdict") in ("PASS", "PASS_WITH_WARNING"):
    ...
```

- `PASS_WITH_WARNING`이면 `quality_gate_failed=True`(기존 generator 필드) 또는 동등 alias(`quality_risk`)를 다음 단계 context에 포함.
- 주의: 현재 코드에서는 `pipeline_result`가 Stage3 내부 로컬로 끝나기 쉬워 Stage4로 자동 전달되지 않는다.
  - 전달 경로를 명시적으로 추가해야 한다.
  - 예: blueprint 저장 시 메타(`quality_gate_failed`) 함께 저장하거나, Stage4ContextBuilder 입력으로 전달.

---

## Phase 5: ASP 조건부 확장 (Stage 2/3)

### 5-1. 기준
- 재시도 2회차 이상에서만 ASP 발동.
- ASP는 교정안 생성만, 판정은 Director.

### 5-2. Stage 3 배선
- 파일: `modules/core/stage3_context.py`, `modules/core/stage3_orchestrator.py`, `modules/domain/agents/three_phase_blueprint_generator.py`
- 주입 키는 반드시 실제 앱 속성명 사용:

```python
adversarial_self_play=getattr(app, "adversarial_self_play", None)
```

- `stage3_orchestrator.py` 호출부에서 실제 전달도 필요:

```python
blueprint, pipeline_result = ctx.agents["three_phase_bp"].generate(
    ...,
    adversarial_self_play=ctx.adversarial_self_play,
)
```

- ASP 결과 사용 시 API 계약:

```python
_asp_result = self._asp.generate_with_adversary(...)
if _asp_result and getattr(_asp_result, "final_output", ""):
    _asp_bp = json.loads(_asp_result.final_output)
```

### 5-3. Stage 2 배선
- 파일: `modules/core/stage2_context.py`, `modules/core/stage2_preflight.py`, `modules/domain/agents/four_phase_arc_generator.py`

- `stage2_context.py`에도 슬롯/주입 추가:

```python
__slots__ = (..., "adversarial_self_play", ...)
...
adversarial_self_play=getattr(app, "adversarial_self_play", None)
```

```python
if attempt >= 2 and adversarial_self_play and best_arc:
    _asp_result = adversarial_self_play.generate_with_adversary(...)
    if _asp_result and getattr(_asp_result, "final_output", ""):
        _asp_arc = json.loads(_asp_result.final_output)
```

---

## Phase 6: ToT/MAD 조건부 배선

### 6-1. 모듈/파일 기준
- ToT: `modules/core/tree_of_thoughts.py` (`TreeOfThoughts.explore`)
- MAD: `modules/core/multi_agent_deliberation.py` (`MultiAgentDeliberation.deliberate`)

### 6-2. Stage 4 조건부 발동
- 파일: `modules/core/stage4_interview_round.py`
- 구조 오류 버킷 -> ToT
- 제약 충돌 버킷 -> MAD

```python
_tot_result = self.ctx.tree_of_thoughts.explore(
    task=f"원고 구조 개선: {director_feedback}",
    context={"manuscript": _prev_manuscript[:3000], "blueprint": blueprint},
)
if _tot_result and getattr(_tot_result, "best_path", None):
    director_feedback += _tot_result.best_path.output[:1000]
```

```python
_mad_result = self.ctx.multi_agent_deliberation.deliberate(
    content=_prev_manuscript,
    content_type="manuscript",
    context={"blueprint": blueprint, "director_feedback": director_feedback},
)
if _mad_result and getattr(_mad_result, "consensus_output", ""):
    director_feedback += _mad_result.consensus_output[:1000]
```

### 6-3. DI 키 정합성
- 파일: `modules/core/stage4_context.py`

```python
tree_of_thoughts=getattr(app, "tree_of_thoughts", None)
multi_agent_deliberation=getattr(app, "multi_agent_deliberation", None)
```

### 6-4. 1회 발동 보장
- `_tot_used`, `_mad_used`를 함수 로컬로만 두면 라운드마다 초기화될 수 있음.
- `previous_attempt` 또는 orchestrator 상태에 저장해 retry window 내 1회만 보장.

---

## Phase 7: 거절 사유 메트릭

- 파일: `modules/core/stage4_interview_round.py`
- `cost_log` 직접 SQL(`event_type`, `detail`) 사용 금지.
- DB 계약에 맞는 `save_cost_record()` 사용.

```python
self.ctx.current_project.db.save_cost_record(
    session_id=f"ep_{next_ep}",
    scope_type="episode",
    scope_id=int(next_ep),
    total_calls=0,
    total_tokens=0,
    total_cost_usd=0.0,
    model_breakdown={
        "event": "stage4_reject",
        "bucket": _reject_bucket,
        "score": score,
        "round": round_num,
        "strategy": selected,
        "intelligence_used": {
            "asp": round_num >= 2 and bool(self.ctx.adversarial_self_play),
            "tot": _tot_used,
            "mad": _mad_used,
        },
    },
)
```

- Stage 2/3도 동일 패턴으로 `model_breakdown["event"]`만 변경:
  - `stage2_reject`
  - `stage3_reject`

---

## 실행 순서 요약

| Step | Phase | 내용 | 수정 파일 | 리스크 |
|------|-------|------|----------|--------|
| 1 | 1 | 피드백 분리 | `chief_writer.py`, `blueprint_ensemble.py`, `three_phase_blueprint_generator.py` | LOW |
| 2 | 2 | 단일 후보 정제 | `stage4_interview_round.py`, `chief_writer.py`, `blueprint_ensemble.py`, `three_phase_blueprint_generator.py` | MEDIUM |
| 3 | 3 | 피드백 스키마 정규화 | `three_phase_blueprint_generator.py`, `stage2_preflight.py` | LOW |
| 4 | 4 | PASS_WITH_WARNING 수용 | `stage3_orchestrator.py` | LOW |
| 5 | 5 | ASP Stage 2/3 배선 | `stage3_context.py`, `stage3_orchestrator.py`, `three_phase_blueprint_generator.py`, `stage2_context.py`, `stage2_preflight.py`, `four_phase_arc_generator.py` | LOW |
| 6 | 6 | ToT/MAD 조건부 배선 | `stage4_interview_round.py`, `stage4_context.py` | MEDIUM |
| 7 | 7 | 거절 사유 메트릭 | `stage4_interview_round.py`, `stage3_orchestrator.py`, `stage2_preflight.py` | LOW |

---

## 검증 명령

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

부분 검증:

```bash
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q -x -k "stage2 or stage3 or stage4"
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q -x -k "asp or adversarial"
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q -x -k "tree_of_thoughts or deliberation"
```

---

## 구현 대조 결과 (2026-02-19)

코드 실측 기준 대조 결과:

- Phase 1: 완료 (`chief_writer.py`, `blueprint_ensemble.py`, `three_phase_blueprint_generator.py`)
- Phase 2: 완료 (`stage4_interview_round.py`의 `selected_strategy_key` 저장 + `chief_writer.py` 단일 전략 정제 + 폴백 확인)
- Phase 3: 완료 (`three_phase_blueprint_generator.py`, `stage2_preflight.py`에 `selection_reason/score_breakdown/validation_warnings` 전달 확인)
- Phase 4: 완료 (`stage3_orchestrator.py`에서 `PASS_WITH_WARNING` 수용 + `quality_gate_failed/quality_risk` 메타 전파)
- Phase 5: 완료
  - Stage 3: 완료 (`stage3_context.py`, `stage3_orchestrator.py`, `three_phase_blueprint_generator.py`)
  - Stage 2: 완료 (`modules/core/stage2_preflight.py`의 `four_phase.generate(...)`에 `adversarial_self_play` 전달 연결 + post-ASP/patch 경로 유지)
- Phase 6: 완료 (`stage4_context.py` DI + `stage4_interview_round.py`의 `_tot_used/_mad_used` retry-window 1회 보장)
- Phase 7: 완료
  - `stage4_reject`: `modules/core/stage4_interview_round.py`
  - `stage3_reject`: `modules/core/stage3_orchestrator.py`
  - `stage2_reject`: `modules/core/stage2_finalizer.py` (문서 초안의 `stage2_preflight.py` 대신 최종izer 위치에 구현)

테스트 확인:
- `ruff check` 통과
- `pytest tests/` 통과 (`2100 passed, 68 xfailed`)
- Stage2/3/4 타깃 테스트 통과 (`257 passed`)

---

## 최종 체크리스트

- [x] Director 외 모듈이 PASS 확정하지 않는가?
- [x] ASP/ToT/MAD API 호출 시 반환 계약(`final_output`, `best_path`, `consensus_output`)을 지키는가?
- [x] DI 키가 실제 앱 속성명과 일치하는가?
- [x] `save_cost_record()` 계약(`session_id`, `scope_type`, `scope_id`...)을 지키는가?
- [x] 단일 후보 정제 실패 시 기존 경로로 정상 폴백하는가?

잔여 액션:
- [x] 없음

