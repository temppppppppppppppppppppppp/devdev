# Opus TF-5: Ops Metrics + Config Consistency Debug Audit (TF-L)

> 감사일: 2026-02-23  
> 범위: `modules/core/quality_dashboard.py`, `modules/core/pass_rate_monitor.py`, `modules/core/stage2_optimizer.py`, `modules/core/data_collector.py`, `modules/core/narrative_diversity.py`, `modules/core/self_reflection.py`, `config/settings/validation.yaml`, `config/models.yaml`, `config/system.yaml`, `config/smart_retrieval/genre_hints.yaml`  
> 호출 경로 확인: `modules/core/stage4_post_processor.py` → `modules/core/quality_dashboard.py`, `modules/core/stage2_validation_pipeline.py` → `modules/core/stage2_optimizer.py`

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 1 |
| LOW | 0 |

### [L-1] Stage4 품질 회귀/드리프트 감지가 Stage4 데이터를 기록하지 않아 실질적으로 작동하지 않음 — HIGH
- **위치**: `modules/core/stage4_post_processor.py:558`, `main_a.py:2116`, `modules/core/stage2_finalizer.py:572`, `modules/core/stage2_finalizer.py:580`, `modules/core/quality_dashboard.py:992`
- **코드 인용**:
```python
# stage4_post_processor.py
_regression = self.ctx.quality_dashboard.detect_score_regression(stage=4)
```
```python
# main_a.py
drift = self.quality_dashboard.detect_quality_drift(stage=4, min_windows=3, window_size=10)
```
```python
# stage2_finalizer.py
self.ctx.quality_dashboard.record_validation(..., stage=2)
```
```python
# quality_dashboard.py
if len(windows) < min_windows:
    return {"drift": "insufficient_data", ...}
```
- **현상**: Stage4에서는 회귀/드리프트 탐지 함수를 호출하지만, 실제 `record_validation()` 쓰기는 Stage2(`stage=2`)만 존재한다.
- **재현 시나리오**: Stage4를 여러 화 운영해도 QualityDashboard의 Stage4 히스토리는 비어 있어 `insufficient_data`만 반환.
- **영향**: 운영 지표상 Stage4 품질 저하를 조기 탐지하지 못하고 경고 체인이 무력화된다.
- **수정 제안**:
```python
# Stage4 PASS/REJECT 확정 지점에서
self.ctx.quality_dashboard.record_validation(ep_num=next_ep, result={...}, stage=4)
```

### [L-2] Stage2Optimizer 중복 제거에서 dict 아이템 정규화가 비대칭이라 `{"item": ...}` 포맷이 중복 필터를 우회함 — HIGH
- **위치**: `modules/core/stage2_optimizer.py:210`, `modules/core/stage2_optimizer.py:231`, `modules/core/stage2_optimizer.py:238`, `modules/core/stage2_validation_pipeline.py:188`
- **코드 인용**:
```python
# stage2_optimizer.py (기존 아이템 수집)
_n = _it.get("name", _it.get("item", ""))
```
```python
# stage2_optimizer.py (현재 Arc 정규화)
current_items = [x.get("name", str(x)) if isinstance(x, dict) else str(x) for x in current_items]
```
```python
# stage2_validation_pipeline.py
refined_arc, corrections = self.ctx.stage2_optimizer.post_process_arc(...)
```
- **현상**: 기존 Arc 쪽은 `name/item` 둘 다 처리하지만, 현재 Arc 쪽은 dict에서 `name`만 본다. `{"item": "철검"}`은 `"{'item': '철검'}"`로 문자열화된다.
- **재현 시나리오**: 이전 Arc `items_acquired=[{"item":"철검"}]`, 현재 Arc도 동일 포맷으로 반환 → 중복 제거 실패.
- **영향**: Stage2 자동 보정이 중복 획득 제약을 누락하여 후속 검증/수정 루프 비용 증가와 품질 저하를 유발한다.
- **수정 제안**:
```python
current_items = [x.get("name", x.get("item", str(x))) if isinstance(x, dict) else str(x) for x in current_items]
```

### [L-3] `validation.yaml`의 `retry.director_max_attempts` 설정이 Stage4 루프에 연결되지 않아 운영자가 재시도 횟수를 조정할 수 없음 — MEDIUM
- **위치**: `config/settings/validation.yaml:76`, `modules/core/stage4_orchestrator.py:539`
- **코드 인용**:
```yaml
# validation.yaml
retry:
  director_max_attempts: 5
```
```python
# stage4_orchestrator.py
for interview_round in range(5):
```
- **현상**: 설정 파일에 재시도 키가 존재하지만 Stage4 구현은 하드코딩 `5`를 사용해 설정 변경이 반영되지 않는다.
- **재현 시나리오**: `director_max_attempts`를 3 또는 7로 바꿔도 Stage4 면담 라운드 횟수는 항상 5회.
- **영향**: 운영 환경별 비용/속도 튜닝이 불가능하고 설정-코드 정합성이 깨진다.
- **수정 제안**:
```python
max_rounds = int(_threshold("retry.director_max_attempts", 5))
for interview_round in range(max_rounds):
```

## 비고
- `config/models.yaml`의 `manager: gemini-2.5-flash` 반영은 실제 로더(`modules/domain/agents/base_agent.py`)에서 정상 확인.
- `config/system.yaml`의 `thinking_budget_map`, `api.timeout`, `api.max_context_chars`, `key_rotation.min_interval`는 BaseAgent 클래스 상수에 정상 주입됨.
