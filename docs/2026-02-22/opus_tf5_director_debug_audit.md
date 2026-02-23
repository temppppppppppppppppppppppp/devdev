# Opus TF-5: Director 체인 디버깅 감사 (TF-E)

> 감사일: 2026-02-22  
> 감사자: Codex (GPT-5)  
> 방법: 수동 라인 단위 코드 열람 (검색 결과 단독 근거 사용 금지)  
> 대상 파일:
> - `modules/domain/agents/director.py`
> - `modules/domain/agents/director_auditor.py`
> - `modules/domain/agents/director_continuity.py`
> - `modules/domain/agents/director_ensemble.py`
> - `modules/domain/agents/director_grading.py`
> - `modules/domain/agents/director_caching.py`
> - 호출자 계약 확인: `modules/domain/agents/three_phase_blueprint_generator.py`, `modules/domain/agents/unified_blueprint_validator.py`, `modules/core/stage4_interview_round.py`, `modules/domain/agents/blueprint_ensemble.py`

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 1 |
| LOW | 0 |

---

### [E-1] Blueprint 연속성 가드가 사실상 무력화됨 (단일 불연속 PASS) — HIGH
- **위치**: `modules/domain/agents/director_continuity.py:629`, `modules/domain/agents/director_continuity.py:643`, `modules/domain/agents/three_phase_blueprint_generator.py:319`
- **코드 인용**:
```python
# director_continuity.py
issues.append({
    "type": "location_discontinuity",
    "severity": "MAJOR",
    "message": f"위치 불연속: 이전 종료 '{prev_end_location}' → 현재 시작 '{new_start_location}'",
})
...
if critical_count > 0:
    decision = "REJECT"
elif major_count >= 2:
    decision = "WARNING"
else:
    decision = "PASS"
```
```python
# three_phase_blueprint_generator.py
continuity_result = director.check_blueprint_continuity_with_cache(...)
if continuity_result.get("decision") == "REJECT":
    ...
    continue  # 다음 재시도로
```
- **현상**: 연속성 검사에서 실제로 생성되는 이슈가 `MAJOR` 1건(위치 불연속)뿐인데, 판정 조건이 `major_count >= 2`부터 `WARNING`이라 단일 불연속은 `PASS`가 된다. 호출 측은 `REJECT`만 차단하므로 연속성 가드가 실질적으로 동작하지 않는다.
- **재현 시나리오**: 직전 Blueprint 종료 위치를 `천하성`, 신규 시작 위치를 `북해`처럼 명확히 다른 값으로 넣으면 `issues`에는 MAJOR 1건이 기록되지만 최종 decision은 PASS로 반환되어 Stage 3가 그대로 진행된다.
- **영향**: Stage 3의 선행 연속성 차단 장치가 유명무실해져 위치 불연속 Blueprint가 후속 단계로 유입된다. 연속성 REJECT 루프가 기대한 대로 작동하지 않는다.
- **수정 제안**: 단일 MAJOR도 최소 `WARNING` 이상으로 올리거나(`major_count >= 1`), 호출부에서 `WARNING`도 재시도 트리거로 처리하도록 계약을 맞출 것.

### [E-2] Director REJECT 시 선택 후보 미전파로 패치 타깃 전략이 어긋남 — MEDIUM
- **위치**: `modules/domain/agents/director_ensemble.py:172`, `modules/domain/agents/three_phase_blueprint_generator.py:349`, `modules/domain/agents/three_phase_blueprint_generator.py:396`, `modules/domain/agents/blueprint_ensemble.py:202`
- **코드 인용**:
```python
# director_ensemble.py
return {
    "decision": decision,
    "selected_index": selected_idx,
    "selected_blueprint": candidates[selected_idx] if decision == "PASS" else None,
}
```
```python
# three_phase_blueprint_generator.py
if validation_result.get("selected_blueprint"):
    best_blueprint = validation_result["selected_blueprint"]
...
_selected_meta = best_blueprint.get("_ensemble_meta", {})
_selected_strategy = _selected_meta.get("strategy", "")
_prev_reject_strategy = _selected_strategy or ""
```
```python
# blueprint_ensemble.py
if strategy.get("name") == rejected_strategy and strategy_specific_feedback:
    _strategy_feedback = strategy_specific_feedback
```
- **현상**: Director가 후보를 고른 뒤 REJECT한 경우 `selected_index`는 반환되지만 `selected_blueprint`는 `None`이 된다. Stage 3는 이때 `best_blueprint`를 갱신하지 않아, 이후 `_prev_reject_strategy`가 Director가 실제로 거절한 후보 전략이 아니라 기존 대표 후보 전략으로 저장될 수 있다.
- **재현 시나리오**: 후보 A/B/C가 있고 Director가 B를 선택해 REJECT하면, `selected_blueprint=None` 때문에 `best_blueprint`는 여전히 A로 남는다. 다음 재시도에서 `rejected_strategy`가 A로 전달되어 전략별 보정 피드백이 잘못된 타깃에 붙는다.
- **영향**: 패치 루프의 전략별 피드백 정합성이 깨져 재시도 효율이 떨어지고, 같은 유형 결함이 반복될 확률이 높아진다.
- **수정 제안**: REJECT여도 `selected_blueprint`를 항상 반환하거나, Stage 3에서 `selected_index`를 사용해 거절된 전략을 명시적으로 추출하도록 수정할 것.

---

## 비이슈 확인 (회귀 점검)
- `SC-Skip` 임계값 로직(`ambiguous_lower=50`, `ambiguous_upper=60`)은 코드/로그 조건이 일치하며, 경계값(=50, =60)은 의도적으로 애매 구간으로 보내도록 구현되어 있음 (`modules/domain/agents/director_auditor.py:823`, `modules/domain/agents/director_auditor.py:832`).

