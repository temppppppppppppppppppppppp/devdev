# Debug Sweep 12 - ops-quality 커밋 후속 버그 수정 (2차)

## Execution Status (2026-02-17)

- A-1 completed: fixed misleading warning message for `perf_timer.start()` failure.
- A-2 completed: wrapped `financial_registry` extraction/save with non-blocking `try/except`.
- B-1 completed: strengthened `test_priority_order_included` with expected length assertion.
- B-2 completed: strengthened `test_no_issues` to assert exact empty list.
- Verification:
  - `pytest -q tests/test_feedback_system.py tests/test_stage2_preflight_helpers.py` -> pass
  - `pytest -q tests/test_stage2_preflight.py tests/test_stage2_preflight_helpers.py tests/test_feedback_system.py` -> `119 passed`

## Context

`af32192` 커밋(ops-quality 6대 개선, 1,440줄 추가)에 대해 Sweep 11에서 4건 수정 완료.
추가 4-에이전트 병렬 탐색 후 수동 코드 검증으로 **확인된 실제 버그 2건 + 테스트 품질 2건** 정리.

---

## A-1 (MEDIUM): `perf_timer.start()` 예외 메시지가 "장르 레지스트리 갱신 실패"로 오표기

**파일**: `modules/core/stage2_preflight.py:463`

**문제**:
```python
# L460-463
try:
    self.ctx.perf_timer.start(f"s2_arc_{global_arc_no}_generate")
except Exception as e:
    logging.warning(f"[SilentPass:Preflight] 장르 레지스트리 갱신 실패: {e!s:.100}")
```
- 실제 코드는 `perf_timer.start()` 호출인데 에러 메시지는 "장르 레지스트리 갱신 실패"
- L579-584의 try-except 에러 메시지가 복사-붙여넣기된 것으로 추정
- 디버깅 시 혼란 유발

**수정**:
```python
except Exception as e:
    logging.warning(f"[SilentPass:Preflight] perf_timer start 실패: {e!s:.100}")
```

---

## A-2 (MEDIUM): `financial_registry` 저장이 try-except 밖 → 실패 시 후속 처리 전체 중단

**파일**: `modules/core/stage2_preflight.py:586-590`

**문제**:
```python
# L579-590
try:
    self.ctx.state_tracker._populate_genre_registries_from_arc(refined_arc)
except Exception as _e:
    logging.warning("[Sweep5-D] genre registry update failed: %s", _e)
if genre_for_tracker == "investment":
    self.ctx.state_tracker.extract_financial_events_from_arc(refined_arc)  # ← 보호 없음
    self.ctx.current_project.save_v20_anchor(                              # ← 보호 없음
        "financial_registry", self.ctx.state_tracker.export_financial_registry()
    )
```
- L579-584의 try-except는 `_populate_genre_registries_from_arc`만 보호
- L586-590의 financial_registry 코드는 보호 없음
- 실패 시 상위 except(L700)가 잡지만, 그러면 SemanticPlotGuard 인덱싱(L592), chain link(L602), WorldState(L634), FactLedger(L651) 등 후속 처리 전체 중단
- 비차단 패턴 위반

**수정**:
```python
if genre_for_tracker == "investment":
    try:
        self.ctx.state_tracker.extract_financial_events_from_arc(refined_arc)
        self.ctx.current_project.save_v20_anchor(
            "financial_registry", self.ctx.state_tracker.export_financial_registry()
        )
    except Exception as _fin_err:
        logging.warning("[SilentPass:Preflight] financial registry save failed: %s", _fin_err)
```

---

## B-1 (LOW): `test_priority_order_included` — 약한 타입 전용 단언문

**파일**: `tests/test_feedback_system.py:105`

**문제**:
```python
def test_priority_order_included(self, fs, sample_violations):
    """priority_order가 포함됨"""
    result = fs.build_structured_feedback(decision="REJECT", reason="test", violations=sample_violations)
    assert isinstance(result["priority_order"], list)  # ← 빈 리스트여도 통과
```
- `sample_violations`에 3건 위반 제공 → `priority_order`는 비어있으면 안 됨
- 현재 단언은 `[]`도 통과시킴

**수정**:
```python
assert isinstance(result["priority_order"], list)
assert len(result["priority_order"]) == 3
```

---

## B-2 (LOW): `test_no_issues` — 빈 리스트 검증 누락

**파일**: `tests/test_feedback_system.py:202`

**문제**:
```python
def test_no_issues(self, fs):
    """문제 없으면 빈 리스트"""
    result = fs.quantify_reject_feedback(reason="기타 문제", content_length=6000, audit_result={})
    assert isinstance(result, list)  # ← 비어있는지 확인 안 함
```
- 독스트링은 "빈 리스트"라고 명시, 실제 단언은 타입만 확인
- "기타 문제"는 어떤 키워드 패턴에도 매칭 안 됨 + content_length=6000 > WARNING_LENGTH → 빈 리스트 보장

**수정**:
```python
assert result == []
```

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/core/stage2_preflight.py` | 에러 메시지 1줄 수정 |
| A-2 | `modules/core/stage2_preflight.py` | try-except 래핑 +3줄 |
| B-1 | `tests/test_feedback_system.py` | 단언문 1줄 추가 |
| B-2 | `tests/test_feedback_system.py` | 단언문 1줄 수정 |

**총 ~6줄 변경**

---

## 오탐 제거 기록

탐색 에이전트가 보고했으나 수동 검증 후 오탐 확인된 항목:

| 보고 | 실제 | 이유 |
|------|------|------|
| `quality_dashboard.py:880` 0 나누기 | ✗ 오탐 | `len(scores) >= 3` 가드 → `scores[:len//2]` 최소 1, `scores[len//2:]` 최소 2 |
| `pass_rate_monitor.py:299` ternary 0 나누기 | ✗ 오탐 | Python ternary `a/b if cond else default` → cond 먼저 평가, False이면 나눗셈 미실행 |
| `pass_rate_monitor.py:385` 0 나누기 | ✗ 오탐 | `len(stage_records) < window*2` 가드 → `recent`, `previous` 모두 정확히 window개 |
| `db_manager.py:1139` SQL 인젝션 | ✗ 오탐 | 하드코딩 테이블 리스트, 외부 입력 불가 |
| `db_manager.py:1512` SQL 인젝션 | ✗ 오탐 | 표준 DB-API `"?"` placeholder IN절 패턴 |
| `stage2_preflight.py:338` prev_difficulty None | ✗ 오탐 | `get_arc_difficulty()` 항상 dict 반환 (모든 경로에 "difficulty" 키 포함) |
| `Stage4Context.from_app()` pass_rate_monitor 누락 | ✗ 오탐 | `main_a.py:2933`에서 수동 생성, `from_app()` 미사용 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_feedback_system.py tests/test_stage2_preflight_helpers.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```
