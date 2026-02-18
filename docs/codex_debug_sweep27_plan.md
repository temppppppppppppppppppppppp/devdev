# Debug Sweep 27 — KeyError + 방어적 빈 컬렉션 가드

## Context

Sweep 26(2,007 passed) 완료 후, 5-에이전트 병렬 탐색으로 새로운 버그 패턴 집중 스윕:
division by zero, dict KeyError, empty collection, return type contract, first/last episode boundary.
수동 코드 검증으로 **확인된 실제 버그 2건** 정리.

---

## A-1 (HIGH): `director_auditor.py:248` — V0128 early REJECT 시 `result["detailed_feedback"]` KeyError

**파일**: `modules/domain/agents/director_auditor.py:244-250`

**문제**:
```python
legacy_result = {
    "decision": result["final_decision"],
    "score": result["total_score"],
    "reason": result["feedback"],
    "feedback": result["detailed_feedback"],  # ← KeyError!
    "v0128_full_result": result,
}
```

`ValidationOrchestrator.validate()`의 반환 경로 분석:
- **CONTINUITY REJECT** (L282-290): `"detailed_feedback"` 키 없음 ❌
- **BLOCKING REJECT** (L310-319): `"detailed_feedback"` 키 없음 ❌
- **PRE-LLM REJECT** (L252-261): `"detailed_feedback"` 키 없음 ❌
- **CONSISTENCY REJECT** (L334-344): `"detailed_feedback"` 키 있음 ✅ (L342)
- **정상 PASS/REJECT** (L537): `"detailed_feedback"` 키 있음 ✅ (L537에서 생성)

→ CONTINUITY/BLOCKING/PRE-LLM 경로에서 early REJECT 시 `result["detailed_feedback"]` → `KeyError`
→ 외부 `except Exception as e:` (L260)가 잡아서 크래시는 방지하지만, 실제 피드백 데이터 전량 소실

**수정** — L248에서 `.get()` 사용:
```python
legacy_result = {
    "decision": result["final_decision"],
    "score": result["total_score"],
    "reason": result["feedback"],
    "feedback": result.get("detailed_feedback", result.get("feedback", "")),
    "v0128_full_result": result,
}
```

**테스트**: CONTINUITY REJECT 반환값으로 `audit_manuscript` 호출 시 크래시 없이 `legacy_result["feedback"]`에 feedback 문자열 포함 검증

---

## A-2 (MEDIUM): `stage3_orchestrator.py:96` — `arcs[-1]` 빈 리스트 시 IndexError

**파일**: `modules/core/stage3_orchestrator.py:96`

**문제**:
```python
total_planned_ep = ctx.current_project.arcs[-1].get("ep_end", 50)
```
- `ProjectManager.arcs`는 `__init__`에서 `[]`로 초기화 (L72)
- Stage 2가 arcs를 생성한 후 Stage 3가 실행되므로 정상 흐름에서는 비어있지 않음
- 그러나 데이터 로드 실패, 테스트 환경, 또는 직접 호출 시 빈 리스트 가능
- `[][-1]` → `IndexError`

**수정**:
```python
total_planned_ep = ctx.current_project.arcs[-1].get("ep_end", 50) if ctx.current_project.arcs else 50
```

**테스트**: `ctx.current_project.arcs = []` 상태에서 `run_blueprint_stage()` 호출 시 `total_planned_ep = 50` 기본값 사용 검증

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/domain/agents/director_auditor.py` | 1줄 수정 (`.get()` 폴백) |
| A-2 | `modules/core/stage3_orchestrator.py` | 1줄 수정 (빈 리스트 가드) |

**총 ~2줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `semantic_item_registry.py:199` division by zero | ✗ 오탐 | L193에 `union == 0` early return 가드 |
| `narrative_structure_analyzer.py:analyze()` → None 반환 | ✗ 오탐 | L97-98에서 `_extract_narrative_elements` None을 캐치하고 dict 반환 |
| `project_manager.py:705` `force_sync_v25_dna` → None | ✗ 오탐 | 호출자 `if dna_success:` 방어적 |
| `action_scene_evaluator.py:404` → None | ✗ 오탐 | 호출자 `if current_effect` 방어적 |
| `db_manager.py:860` `load_state_log` → None | ✗ 오탐 | 호출자 4곳 모두 `if log_data and isinstance(...)` |
| `director_grading.py:277,348` → None | ✗ 오탐 | 호출자 `if revision_task:`, `if example:` 방어적 |
| `director_caching.py:66` → None | ✗ 오탐 | 호출자 필드 체크 방어적 |
| `analyst.py:1177` `analyze_context` → None | ✗ dead code | 프로덕션에서 호출처 없음 |
| 모든 division-by-zero 패턴 | ✗ 오탐 | 전량 가드 확인 (semantic_item_registry, pass_rate_monitor 등) |
| 모든 first/last episode 경계 | ✗ 오탐 | `if ep_num > 1:`, `max(1, ep-N)`, None 체크 전량 확인 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_director_modules.py tests/test_stage3_context.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Status (2026-02-18)

- [x] A-1 `modules/domain/agents/director_auditor.py`
  - `audit_manuscript_v0128`의 legacy 변환에서 `detailed_feedback` 직접 인덱싱 제거
  - `feedback`: `result.get("detailed_feedback", result.get("feedback", ""))`로 fallback 적용
- [x] A-2 `modules/core/stage3_orchestrator.py`
  - `total_planned_ep` 계산 시 empty arcs 가드 추가
  - `ctx.current_project.arcs[-1].get("ep_end", 50) if ctx.current_project.arcs else 50`

## Added Regression Tests

- `tests/test_sweep27.py` 추가 (2 tests)
  - `test_director_auditor_v0128_handles_missing_detailed_feedback_key`
    - early-REJECT 형태(= `detailed_feedback` 없음)에서도 KeyError 없이 `feedback` fallback 동작 검증
  - `test_stage3_orchestrator_total_planned_ep_has_empty_arcs_guard`
    - Stage3 total_planned_ep 라인에 empty arcs 가드 표현 존재 검증

## Validation Results

- `python -m pytest tests/test_sweep27.py tests/test_director_modules.py tests/test_stage3_orchestrator.py -q -x`
  - **108 passed**
- `python -m pytest tests/ -q -p no:capture`
  - **2009 passed, 68 xfailed, 1 warning**

## Notes

- 전체 테스트 종료 후 표시되는 faulthandler traceback은 기존 mock 시나리오 출력이며, pytest 종료코드(0)에는 영향이 없습니다.
