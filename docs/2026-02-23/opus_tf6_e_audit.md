# TF-6-E: 엣지 케이스 경계값 (Boundary Edge Cases)

## 감사 범위
- 파일: `modules/core/stage2_orchestrator.py`, `modules/core/stage2_preflight.py`, `modules/core/stage4_orchestrator.py`, `modules/core/stage4_context_builder.py`, `modules/domain/agents/state_tracker.py`, `modules/core/stage3_orchestrator.py`, `modules/core/stage0/__init__.py`, `modules/core/stage2_validation_pipeline.py`
- 코드 줄 수: 약 1,100줄 수동 확인

## 발견 사항

### [TF-E-1] 단일 에피소드 아크(`ep_count=1`)가 Flow Guard에서 구조적으로 REJECT됨 (HIGH)
- **파일**: `modules/core/stage2_validation_pipeline.py:622`, `modules/core/stage2_validation_pipeline.py:626`, `modules/core/stage2_validation_pipeline.py:629`
- **현재 코드**:
```python
ep_count = int(refined_arc.get("ep_count", 0))
...
if not isinstance(beats, list) or len(beats) < max(3, ep_count):
    return {"status": "REJECT", ...}
```
- **문제**: `ep_count=1`이어도 최소 비트 요구치가 3으로 강제된다.
- **영향**: 단화/브리지 아크 설계를 의도적으로 넣어도 Stage2에서 자동 차단된다.
- **수정안**:
```python
min_beats = max(1, ep_count)
# 또는 threshold: scope.min_beats_floor
if not isinstance(beats, list) or len(beats) < min_beats:
    ...
```
- **테스트**: `ep_count=1`, `beat_sequence` 1개 케이스가 PASS되는 단위 테스트 추가.

## 요약
| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 0 |
