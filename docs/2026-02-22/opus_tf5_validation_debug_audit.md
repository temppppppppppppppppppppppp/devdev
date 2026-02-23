# Opus TF-5: Validation Pipeline Debug Audit (TF-K)

> 감사일: 2026-02-23  
> 범위: `modules/validation/validation_orchestrator.py`, `modules/validation/scoring_validator.py`, `modules/validation/continuity_validator.py`, `modules/validation/consistency_validator.py`, `modules/validation/blocking_validator.py`, `modules/validation/blocking_validator_entity_checks.py`, `modules/validation/blocking_validator_scene_checks.py`, `modules/validation/blocking_validator_consistency_checks.py`, `modules/validation/pre_llm_validator.py`, `modules/validation/advisory_validator.py`, `modules/validation/retrospective_validator.py`, `modules/validation/catharsis_timer.py`  
> 호출 경로 확인: `modules/core/stage4_orchestrator.py` → `modules/core/stage4_interview_round.py` → `modules/validation/blocking_validator.py`, `modules/domain/agents/director_auditor.py` → `modules/validation/validation_orchestrator.py`

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 1 |
| LOW | 0 |

### [K-1] `required_scenes`가 Blueprint 장면 수와 무관하게 최소 4개를 강제해 소규모 Blueprint를 항상 REJECT함 — HIGH
- **위치**: `modules/validation/blocking_validator_scene_checks.py:53`, `modules/validation/blocking_validator_scene_checks.py:55`, `modules/validation/blocking_validator_scene_checks.py:70`, `modules/validation/blocking_validator.py:77`
- **코드 인용**:
```python
# blocking_validator_scene_checks.py
scene_count = len(scene_breakdown)
min_required = 4
...
if scenes_found < min_required:
    return {"passed": False, ...}
```
```python
# blocking_validator.py
if validation_context.get("mode") == "MANUSCRIPT":
    scene_check = self._check_required_scenes(manuscript, validation_context)
```
- **현상**: `scene_breakdown`이 1~3개인 Blueprint는 원고가 모든 장면을 반영해도 `scenes_found < 4` 조건으로 실패한다.
- **재현 시나리오**: `scene_breakdown` 3개, 원고에 3개 장면 키워드 모두 포함 → `3/3 반영`이어도 `최소 4개` 조건으로 REJECT.
- **영향**: Stage 4 검증에서 정상 원고가 체계적으로 오판정된다.
- **수정 제안**:
```python
min_required = min(4, scene_count)
# 또는 _threshold("scene.min_count", 4)와 scene_count를 함께 사용
```

### [K-2] Stage4 검증 컨텍스트에서 `blueprint`가 누락되어 Scene 계열 Blocking 검사 4종이 사실상 비활성화됨 — HIGH
- **위치**: `modules/core/stage4_interview_round.py:261`, `modules/core/stage4_interview_round.py:354`, `modules/validation/blocking_validator_scene_checks.py:46`, `modules/validation/blocking_validator_scene_checks.py:49`
- **코드 인용**:
```python
# stage4_interview_round.py
_cv_context = {
    "mode": "MANUSCRIPT",
    "martial_hud": {},
    ...
}
...
bv_result = blocking_validator.validate(_bv_ms, _cv_context)
```
```python
# blocking_validator_scene_checks.py
blueprint = context.get("blueprint", {})
scene_breakdown = blueprint.get("scene_breakdown", {})
if not scene_breakdown or not isinstance(scene_breakdown, dict):
    return {"check": "required_scenes", "passed": True}
```
- **현상**: Stage4 후보 검증 시 `_cv_context`에 `blueprint`를 넣지 않아, `required_scenes`/`scope_overflow`/`scene_completeness`/`cliffhanger_ending`가 Blueprint 정보 없이 스킵된다.
- **재현 시나리오**: Stage4 면담 라운드에서 후보 원고 검증 실행 시, BlockingValidator는 항상 `context["blueprint"] == {}` 경로로 진입.
- **영향**: 장면 반영/범위 초과/씬 완성도/클리프행어 누락 검사가 실제로는 수행되지 않아 품질 게이트가 약화된다.
- **수정 제안**:
```python
_cv_context["blueprint"] = blueprint or {}
_cv_context["blueprint_text"] = str(blueprint or "")
```

### [K-3] V0128 경로에서 ConsistencyValidator가 3장르 외 Guard를 로드하지 못해 핵심 일관성 검사가 장르별로 비활성화됨 — MEDIUM
- **위치**: `modules/validation/consistency_validator.py:51`, `modules/validation/consistency_validator.py:68`, `modules/validation/consistency_validator.py:288`, `modules/validation/consistency_validator.py:348`, `modules/domain/agents/director_auditor.py:232`
- **코드 인용**:
```python
# consistency_validator.py
if genre == "wuxia": ...
elif genre == "hunter": ...
elif genre == "investment": ...
else:
    logging.warning(f"[WARNING] 미지원 장르 '{genre}' - 기본 검증만 수행")
    return None
```
```python
# consistency_validator.py
if not self.guard:
    return {"passed": True, "violations": []}
```
```python
# director_auditor.py
self.v0128_orchestrator = ValidationOrchestrator(..., genre=genre, ...)
```
- **현상**: V0128 ValidationOrchestrator는 `ConsistencyValidator(genre=...)`를 사용하지만, ConsistencyValidator 내부 Guard 로더는 `wuxia/hunter/investment`만 지원한다.
- **재현 시나리오**: `genre="sports"`(또는 `medical`, `actor` 등)로 V0128 심사 시 `self.guard=None`이 되어 상태-행동/직위-호칭/권위위임/빌런반응 계열이 통과 처리된다.
- **영향**: 장르별 일관성 검증 강도가 실제 운영 장르 간 비대칭이 되어 silent validation hole이 발생한다.
- **수정 제안**:
```python
from modules.core.genre_guards import create_genre_guard
self.guard = create_genre_guard(genre)
```

## 비고
- `modules/validation/continuity_validator.py`의 좌절-보상 스택 순서는 `db_manager.get_recent_satisfaction_tags()`와 함께 역순 보정되어 실제 최신 화 기준으로 평가됨을 확인함.
- `modules/validation/scoring_validator.py`의 장르 가중치/임계값 로딩은 `validation.yaml` 키 경로와 일치함을 확인함.
