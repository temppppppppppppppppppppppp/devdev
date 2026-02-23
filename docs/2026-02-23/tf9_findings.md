# TF-9 Findings

> 베이스라인: 2,542 passed, 0 violations (commit `2fcffff`)

---

## 현재 위치

```
Last Completed Step: Step 5 (TF-9 완료)
Next Step: 없음
Status: 완료
```

---

## 진행 테이블

| Step | 내용 | 상태 | 비고 |
|------|------|------|------|
| Step 1 | arc_no 전달 수정 (TF8R-1) | ✅ 완료 | `stage4_context_builder.py:140,149,740-741` |
| Step 2 | invalid mode 경고 로그 (TF8-F-2) | ✅ 완료 | `stage2_preflight.py:159-163`, `stage4_context_builder.py:187-191` |
| Step 3 | retrieval_mode 라우팅 테스트 (TF8-I-2) | ✅ 완료 | `tests/test_retrieval_mode_routing.py` 신규(5 tests) |
| Step 4 | D2 로그 caplog 테스트 (TF8-I-3) | ✅ 완료 | `tests/test_vec_memory.py:792-819` |
| Step 5 | 최종 검증 + 커밋 | ✅ 완료 | `pytest 2549 passed`, `ruff all passed` |

---

## Step별 수정 기록

### Step 1: arc_no 전달 수정
- 대상: `modules/core/stage4_context_builder.py`
- 수정 전:
  - `modules/core/stage4_context_builder.py:140`
    - `def _execute_retrieval_plan(self, plan: "RetrievalPlan") -> list[str]:`
  - `modules/core/stage4_context_builder.py:149`
    - `current_arc_no = getattr(plan, "arc_no", None)`
  - `modules/core/stage4_context_builder.py:740`
    - `for _retrieved in self._execute_retrieval_plan(_retrieval_plan):`
- 수정 후:
  - `modules/core/stage4_context_builder.py:140`
    - `def _execute_retrieval_plan(self, plan: "RetrievalPlan", arc_no: int | None = None) -> list[str]:`
  - `modules/core/stage4_context_builder.py:149`
    - `current_arc_no = arc_no`
  - `modules/core/stage4_context_builder.py:740-741`
    - `_arc_no_s4 = arc_data.get("arc_no", None) if arc_data else None`
    - `for _retrieved in self._execute_retrieval_plan(_retrieval_plan, arc_no=_arc_no_s4):`
- 검증:
  - `pytest tests/ -q --tb=short`: property 테스트 수집 단계에서 기존 오류 4건으로 중단 (당시 `hypothesis` 미설치)
  - `python -m ruff check modules/core/stage4_context_builder.py`: 통과

### Step 2: invalid mode 경고 로그
- 대상: `modules/core/stage2_preflight.py`, `modules/core/stage4_context_builder.py`
- 수정 전:
  - `modules/core/stage2_preflight.py:158-159`
    - `else:`
    - `result = memory.retrieve_multi_query_context(...`
  - `modules/core/stage4_context_builder.py:186-187`
    - `else:`
    - `result = memory.retrieve_multi_query_context(...`
- 수정 후:
  - `modules/core/stage2_preflight.py:159-163`
    - `if _retrieval_mode not in ("dense", "hybrid", "sparse"):`
    - `logging.warning("[Retrieval] 알 수 없는 retrieval_mode '%s', dense로 폴백", _retrieval_mode)`
  - `modules/core/stage4_context_builder.py:187-191`
    - `if _retrieval_mode not in ("dense", "hybrid", "sparse"):`
    - `logging.warning("[Retrieval] 알 수 없는 retrieval_mode '%s', dense로 폴백", _retrieval_mode)`
- 검증:
  - `python -m ruff check modules/core/stage2_preflight.py modules/core/stage4_context_builder.py`: 통과
  - `pytest tests/ -q --tb=short`: property 테스트 수집 단계 기존 오류 4건으로 중단

### Step 3: retrieval_mode 라우팅 테스트
- 신규 파일: `tests/test_retrieval_mode_routing.py`
- 수정 전:
  - `tests/test_retrieval_mode_routing.py`: 파일 없음
- 수정 후:
  - `tests/test_retrieval_mode_routing.py:1-123` 신규 작성
  - `retrieval_mode` 라우팅 3개 경로 테스트:
    - hybrid: `tests/test_retrieval_mode_routing.py:40`
    - sparse: `tests/test_retrieval_mode_routing.py:57`
    - invalid→dense fallback: `tests/test_retrieval_mode_routing.py:74`
  - `arc_no` 전달 테스트 2개:
    - hybrid 전달: `tests/test_retrieval_mode_routing.py:91`
    - dense 전달: `tests/test_retrieval_mode_routing.py:108`
- 테스트 수: 5개 추가 완료
- 검증:
  - `python -m ruff check tests/test_retrieval_mode_routing.py`: 통과
  - `pytest tests/test_retrieval_mode_routing.py -v --tb=short`: 5 passed

### Step 4: D2 로그 caplog 테스트
- 대상: `tests/test_vec_memory.py`
- 수정 전:
  - `tests/test_vec_memory.py:792` 이후 `test_d2_*` 테스트 없음
- 수정 후:
  - `tests/test_vec_memory.py:792-804` `test_d2_fallback_log_format` 추가
  - `tests/test_vec_memory.py:806-819` `test_d2_dense_log_format` 추가
- 추가 테스트: 2개 완료
- 검증:
  - `python -m ruff check tests/test_vec_memory.py`: 통과
  - `pytest tests/test_vec_memory.py -k "test_d2" -v --tb=short`: 2 passed

### Step 5: 최종 검증
- pytest:
  - `pytest tests/ -q --tb=short`: `2549 passed, 1 warning`
  - 참고: property 테스트 수집 오류 해결을 위해 `python -m pip install hypothesis` 수행
- ruff:
  - `python -m ruff check modules/ main_a.py tests/`: `All checks passed!`
- 커밋:
  - 커밋 메시지: `fix(tf9): arc_no retrieval 전달 수정 + MEDIUM 백로그 패치 (TF8R-1/F-2/I-2/I-3)`

---

## 이슈 목록 (TF-8 감리 → TF-9 패치 대상)

| ID | 등급 | 내용 | 상태 |
|----|------|------|------|
| TF8R-1 | HIGH | stage4_context_builder arc_no 항상 None (죽은 코드) | ✅ |
| TF8-F-2 | MEDIUM | invalid retrieval_mode silent 폴백 (경고 없음) | ✅ |
| TF8-I-2 | MEDIUM | retrieval_mode 라우팅 단위 테스트 부재 | ✅ |
| TF8-I-3 | MEDIUM | D2 로그 caplog 포맷 검증 테스트 부재 | ✅ |

---

## 보류 이슈 (이번 TF 범위 외)

| ID | 등급 | 내용 | 사유 |
|----|------|------|------|
| TF8-E-2 | MEDIUM | dense 로그 hits/selected 보강 | `_knn_search` 내부 리팩터 필요 — 별도 TF |
| TF8-G-2 | MEDIUM | hybrid 0-hit 폴백 전략 | 설계 결정 필요 — 별도 TF |
| TF8-INFO-1 | INFO | tokenizer 없음 | 설계 결정 필요 |
| TF8-INFO-2 | INFO | EMBED_DIM 하드코딩 | 현재 영향 없음 |
