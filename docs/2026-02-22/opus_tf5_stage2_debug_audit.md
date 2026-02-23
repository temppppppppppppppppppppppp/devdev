# Opus TF-5: Stage 2 Debug Audit (TF-A)

> 감사일: 2026-02-22
> 범위: `modules/core/stage2_orchestrator.py`, `modules/core/stage2_preflight.py`, `modules/core/stage2_finalizer.py`, `modules/core/stage2_validation_pipeline.py`, 호출 계약 추적 파일 `main_a.py`, `modules/core/feedback_system.py`
> 방법: 수동 라인 단위 검토 (Read/cat), 호출자→피호출자 추적

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 1 |
| LOW | 0 |

### [A-1] Preflight 타임아웃이 실질적으로 무력화됨 (ThreadPoolExecutor 종료 대기) — HIGH
- **위치**: `modules/core/stage2_preflight.py:273`
- **코드 인용**:
```python
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as _parallel_exec:
    _fut_drive = _parallel_exec.submit(_compute_arc_drive)
    _fut_preflight = _parallel_exec.submit(_compute_preflight)
    _fut_constraint = _parallel_exec.submit(_compute_constraint_block)
    arc_drive = _fut_drive.result(timeout=300)
```
- **현상**: `result(timeout=...)`에서 타임아웃 예외가 나도 `with ThreadPoolExecutor(...)` 블록을 빠져나갈 때 `shutdown(wait=True)`로 장시간 대기하여, fail-fast 의도가 깨진다.
- **재현 시나리오**: `_compute_arc_drive()`가 장시간 블로킹되면 `result(timeout=300)` 예외 발생 후에도 함수가 즉시 복귀하지 않고 워커 종료까지 대기한다.
- **영향**: Stage 2가 타임아웃 상황에서 계속 정지/지연되어 배치 진행이 멈춘다. 프로덕션에서 LLM/API 지연 시 회복성이 크게 떨어진다.
- **수정 제안**:
```python
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
try:
    ...
except TimeoutError:
    executor.shutdown(wait=False, cancel_futures=True)
```

### [A-2] 연속성 구조화 피드백이 생성만 되고 재시도 피드백에 반영되지 않음 — MEDIUM
- **위치**: `modules/core/stage2_validation_pipeline.py:505`, `modules/core/stage2_validation_pipeline.py:523`, `main_a.py:692`, `modules/core/feedback_system.py:364`
- **코드 인용**:
```python
self.ctx.generate_structured_arc_feedback(
    continuity_result=continuity_result, prev_arcs=all_refined_arcs, arc_no=global_arc_no
)
...
current_feedback = f"{strong_kind_feedback}\n\n{focused_context}{banned_items_warning}{prev_state_reminder}{intensity_guide}"
```
- **현상**: `generate_structured_arc_feedback()`의 반환 문자열이 어디에도 저장/병합되지 않는다. 호출자(`main_a.py:692`)와 피호출자(`feedback_system.py:364`, `:454`)를 추적하면 이 함수는 순수 문자열 반환 함수이며 부작용이 없다.
- **재현 시나리오**: ContinuityInspector REJECT 분기에서 위 코드가 실행되면, 구조화 피드백 생성은 수행되지만 `current_feedback`에는 포함되지 않는다.
- **영향**: Arc 재시도 프롬프트가 의도보다 빈약해져 같은 오류 재발 확률이 올라간다(재시도 효율 저하/토큰 낭비).
- **수정 제안**:
```python
structured_feedback = self.ctx.generate_structured_arc_feedback(...)
current_feedback = f"{structured_feedback}\n{strong_kind_feedback}\n\n{focused_context}..."
```

## 비고
- `[NPC-L1]` 회귀 점검: `modules/core/stage2_orchestrator.py:155`의 `bind_db()` 배선은 정상 확인.
- 본 TF 범위에서 CRITICAL(크래시/데이터 손실/무한루프)은 미발견.
