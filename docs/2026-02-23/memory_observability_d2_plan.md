# Memory Observability D2 플랜 (Codex 실행용)

> **작성일**: 2026-02-23
> **대상 실행자**: Codex (자동 에이전트)
> **실행 전제**: db_efficiency_plan.md 완료 + 커밋 확인 후 진행
> **원본 설계**: `docs/codex_memory_roi_boost_plan.md` § D2
> **기준 커밋**: db_efficiency_plan 완료 커밋

---

## 목적

현재 기억 회수 경로(dense / fallback / hybrid / sparse)는 대부분 블랙박스.
D1 Hybrid Retrieval을 배포했지만 실제로 어느 경로가 얼마나 쓰이는지 알 방법이 없음.

이 플랜은 **코드 변경 최소 (로그 추가만)** 으로 다음 지표를 가시화한다:
- 어떤 경로(dense / fallback / hybrid / sparse)가 호출되는가
- 쿼리당 hit 수 (dense hit, sparse hit)
- fallback이 발동됐는가
- 선택된 에피소드 번호 목록
- 반환 결과 길이 (chars)

---

## ⚠️ Codex 실행 규칙

1. **수정 파일은 `modules/core/vec_memory.py` 단 1개**
2. **로그 추가만** — 기존 로직 변경·리팩토링 금지
3. 각 작업 전 해당 라인을 Read 도구로 재확인할 것
4. 완료 후 `pytest tests/ -q` + `ruff check modules/core/vec_memory.py` 실행
5. 테스트 수 변화 없어야 정상 (로그 추가는 테스트 카운트 변화 없음)

---

## 로그 포맷 (공통)

모든 로그는 `logging.debug`로 출력. 파싱 가능하도록 필드 고정:

```
[VecMem] path=<경로> ep<N> q=<쿼리 앞 30자> hits=<N> fallback=<true|false> selected=[<ep1>,<ep2>,...] chars=<N>
```

- `path`: `dense` | `fallback` | `hybrid` | `sparse` | `multi_dense`
- `hits`: KNN 또는 FTS5 결과 수 (int)
- `fallback`: keyword fallback 발동 여부 (true/false)
- `selected`: 최종 반환된 에피소드 번호 목록
- `chars`: 반환 문자열 길이

---

## Phase 1: `retrieve_high_res_context()` 계측

**파일**: `modules/core/vec_memory.py`
**위치**: L437 `retrieve_high_res_context()` 메서드

Read로 L437-449 확인 후, 현재:

```python
def retrieve_high_res_context(self, query, current_ep: int, n_results: int = 3) -> str:
    """쿼리와 유사한 과거 에피소드 맥락 반환 (LongTermMemory 호환)."""
    if not self.has_valid_memory:
        return ""

    query_text = json.dumps(query, ensure_ascii=False) if isinstance(query, dict | list) else str(query)
    emb = self._embed_text(query_text)
    if emb is None:
        # [OpusTF-P0-2] 임베딩 실패 시 LIKE 키워드 폴백
        return self._keyword_fallback_search(query_text, current_ep, n_results)

    return self._knn_search(emb, current_ep, n_results)
```

아래로 교체:

```python
def retrieve_high_res_context(self, query, current_ep: int, n_results: int = 3) -> str:
    """쿼리와 유사한 과거 에피소드 맥락 반환 (LongTermMemory 호환)."""
    if not self.has_valid_memory:
        return ""

    query_text = json.dumps(query, ensure_ascii=False) if isinstance(query, dict | list) else str(query)
    emb = self._embed_text(query_text)
    if emb is None:
        # [OpusTF-P0-2] 임베딩 실패 시 LIKE 키워드 폴백
        result = self._keyword_fallback_search(query_text, current_ep, n_results)
        # [D2] fallback 경로 계측
        logging.debug(
            "[VecMem] path=fallback ep<%d q=%r hits=0 fallback=true selected=[] chars=%d",
            current_ep, query_text[:30], len(result),
        )
        return result

    result = self._knn_search(emb, current_ep, n_results)
    # [D2] dense 경로 계측
    logging.debug(
        "[VecMem] path=dense ep<%d q=%r fallback=false chars=%d",
        current_ep, query_text[:30], len(result),
    )
    return result
```

---

## Phase 2: `retrieve_multi_query_context()` 계측

**파일**: `modules/core/vec_memory.py`
**위치**: L450 `retrieve_multi_query_context()` 메서드

Read로 L450-545 확인 후, 메서드 내 두 return 지점에 로그 추가.

#### 2-A: fallback 분기 (모든 임베딩 실패 시)

현재:
```python
if not seen:
    # [OpusTF-P0-2] 모든 임베딩 실패 시 LIKE 키워드 폴백
    for q in queries:
        ...
        fb = self._keyword_fallback_search(qt, current_ep, max_results)
        if fb:
            return fb
    return ""
```

`return fb` 직전에 추가:
```python
# [D2] multi_dense fallback 계측
logging.debug(
    "[VecMem] path=fallback ep<%d q=%r hits=0 fallback=true selected=[] chars=%d",
    current_ep, qt[:30], len(fb),
)
```

#### 2-B: 정상 반환 지점 계측

메서드 마지막 `return "\n\n".join(blocks)` 직전에 추가:
```python
# [D2] multi_dense 정상 경로 계측
_selected = sorted(seen.keys())[:max_results]
logging.debug(
    "[VecMem] path=multi_dense ep<%d q_count=%d hits=%d fallback=false selected=%s chars=%d",
    current_ep, len(queries), len(seen), _selected, len("\n\n".join(blocks)),
)
```

**주의**: `_selected` 변수명이 기존 코드와 충돌하는지 Read로 확인 후 필요시 `_d2_selected`로 변경.

---

## Phase 3: `retrieve_hybrid_context()` 계측 보강

**파일**: `modules/core/vec_memory.py`
**위치**: `retrieve_hybrid_context()` 내 기존 logging.debug 위치

현재 로그:
```python
logging.debug(
    "[Hybrid] ep<%d query=%r dense=%d sparse=%d fused=%d top_score=%.4f",
    ...
)
```

이 로그를 아래로 교체 (포맷 통일 + fallback 여부 추가):
```python
# [D2] hybrid 경로 계측 (포맷 통일)
_d2_selected = [ep for _, ep, _ in top]
logging.debug(
    "[VecMem] path=hybrid ep<%d q=%r hits=%d fallback=false selected=%s chars=pending top_score=%.4f",
    current_ep, query_text[:30],
    len(dense_results) + len(sparse_results),
    _d2_selected,
    scored[0][0] if scored else 0.0,
)
```

최종 `return "\n\n".join(blocks)` 직전에 추가:
```python
# [D2] hybrid 결과 길이 계측
logging.debug(
    "[VecMem] path=hybrid ep<%d chars=%d",
    current_ep, len("\n\n".join(blocks)),
)
```

---

## Phase 4: `_keyword_fallback_search()` 진입 계측

**파일**: `modules/core/vec_memory.py`
**위치**: L880 `_keyword_fallback_search()` 메서드 진입부

Read로 L880-922 확인 후, 메서드 첫 줄(docstring 다음)에 추가:

```python
# [D2] keyword fallback 진입 계측
logging.debug(
    "[VecMem] path=fallback_entry ep<%d q=%r n=%d",
    current_ep, query_text[:30], n_results,
)
```

---

## 검증

```bash
pytest tests/ -q --tb=short 2>&1 | tail -5
# 기대: 기존 테스트 수 그대로 (로그 추가는 카운트 변화 없음)

ruff check modules/core/vec_memory.py

# 로그 동작 확인 (수동)
python -c "
import sqlite3, threading, logging
logging.basicConfig(level=logging.DEBUG)
from modules.core.vec_memory import VecMemory
conn = sqlite3.connect(':memory:')
vm = VecMemory(conn=conn, lock=threading.RLock())
vm.retrieve_high_res_context('테스트 쿼리', current_ep=5)
vm.retrieve_multi_query_context(['쿼리1', '쿼리2'], current_ep=5)
vm.retrieve_hybrid_context('테스트', current_ep=5)
print('로그 출력 확인')
"
```

**기대 로그 예시:**
```
DEBUG [VecMem] path=fallback ep<5 q='테스트 쿼리' hits=0 fallback=true selected=[] chars=0
DEBUG [VecMem] path=fallback_entry ep<5 q='테스트 쿼리' n=3
DEBUG [VecMem] path=multi_dense ep<5 q_count=2 hits=0 fallback=true selected=[] chars=0
DEBUG [VecMem] path=hybrid ep<5 q='테스트' hits=0 fallback=false selected=[] chars=pending top_score=0.0000
DEBUG [VecMem] path=hybrid ep<5 chars=0
```

---

## 커밋 메시지

```
feat(obs): memory retrieval 경로별 observability 계측 [D2]
```

---

## 완료 기준 (Definition of Done)

| 항목 | 확인 방법 |
|------|---------|
| `retrieve_high_res_context` dense/fallback 구분 로그 | 검증 스크립트 실행 |
| `retrieve_multi_query_context` hits/selected 로그 | 검증 스크립트 실행 |
| `retrieve_hybrid_context` 포맷 통일 | 검증 스크립트 실행 |
| `_keyword_fallback_search` 진입 로그 | 검증 스크립트 실행 |
| 기존 테스트 회귀 없음 | pytest 전량 통과 |
| ruff clean | 0 violations |

---

## 수정 요약

| 파일 | 변경 내용 |
|------|---------|
| `modules/core/vec_memory.py` | `retrieve_high_res_context` dense/fallback 로그, `retrieve_multi_query_context` hits/selected 로그, `retrieve_hybrid_context` 포맷 통일, `_keyword_fallback_search` 진입 로그 |
