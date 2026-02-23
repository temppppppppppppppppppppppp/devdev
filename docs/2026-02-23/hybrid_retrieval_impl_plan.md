# Hybrid Retrieval 구현 플랜 (Codex 실행용)

> **작성일**: 2026-02-23
> **대상 실행자**: Codex (자동 에이전트)
> **기준 커밋**: `d5888f7` — 2494 passed, 0 ruff violations
> **원본 설계**: `docs/codex_hybrid_retrieval_refactor_plan.md`

---

## ⚠️ Codex 실행 규칙 (반드시 준수)

1. **각 Phase 완료 후 반드시 `pytest tests/ -q` 실행**, 실패하면 다음 Phase 진행 금지
2. **각 Phase 완료 후 반드시 `ruff check .` 실행**, violations 있으면 수정 후 진행
3. 파일 수정 전 반드시 해당 파일을 Read 도구로 읽을 것
4. 지시된 파일 외 다른 파일 수정 금지
5. 한글 주석은 `# [태그]` 형식으로만 추가 (중간에 임의로 한글 리팩터링 금지)
6. 이미 구현된 것처럼 보여도 직접 확인 후 판단할 것 (P0-1~P0-3 전례 있음)

---

## Phase 0: 베이스라인 스냅샷 테스트 고정

**목적**: 현재 dense-only 동작을 회귀 기준선으로 고정
**수정 파일**: `tests/test_vec_memory.py` (추가만, 기존 삭제 금지)
**전제**: 없음

### 작업

`tests/test_vec_memory.py`에 클래스 `TestDenseBaselineRegression` 추가:

```python
class TestDenseBaselineRegression:
    """Phase 0: dense-only 동작 회귀 기준선."""

    def _make_vec(self, db_conn):
        """VecMemory 공유 모드 인스턴스 생성."""
        import threading
        lock = threading.RLock()
        from modules.core.vec_memory import VecMemory
        return VecMemory(conn=db_conn, lock=lock)

    def test_retrieve_high_res_returns_str(self, tmp_path):
        """retrieve_high_res_context()는 항상 str을 반환한다."""
        import sqlite3
        conn = sqlite3.connect(":memory:")
        vm = self._make_vec(conn)
        result = vm.retrieve_high_res_context("test query", current_ep=5)
        assert isinstance(result, str)

    def test_retrieve_multi_query_returns_str(self, tmp_path):
        """retrieve_multi_query_context()는 항상 str을 반환한다."""
        import sqlite3
        conn = sqlite3.connect(":memory:")
        vm = self._make_vec(conn)
        result = vm.retrieve_multi_query_context(
            queries=["query1", "query2"],
            current_ep=5,
            max_results=3,
        )
        assert isinstance(result, str)

    def test_no_memory_returns_empty(self, tmp_path):
        """벡터 데이터 없을 때 빈 문자열 반환."""
        import sqlite3
        conn = sqlite3.connect(":memory:")
        vm = self._make_vec(conn)
        assert vm.retrieve_high_res_context("any query", current_ep=3) == ""
        assert vm.retrieve_multi_query_context(["any"], current_ep=3) == ""
```

### 검증
```
pytest tests/test_vec_memory.py -q
pytest tests/ -q --tb=short 2>&1 | tail -5
ruff check tests/test_vec_memory.py
```

**기대**: 2494 + 3 = 2497 passed

---

## Phase 1: `retrieve_hybrid_context()` 인터페이스 추가

**목적**: 새 공개 API 추가. 내부적으로는 아직 dense만 호출 (Phase 3에서 진짜 hybrid로 교체)
**수정 파일**: `modules/core/vec_memory.py`
**전제**: Phase 0 통과

### 작업

`modules/core/vec_memory.py`에서 `retrieve_multi_query_context()` 메서드 끝 부분(L521) 바로 다음에 아래 메서드를 삽입:

```python
def retrieve_hybrid_context(
    self,
    query: str,
    current_ep: int,
    dense_k: int = 10,
    sparse_k: int = 10,
    max_results: int = 5,
    current_arc_no: int | None = None,
    rrf_k: int = 60,
) -> str:
    """[Hybrid-P1] Dense + Sparse RRF 하이브리드 검색.
    Phase 1: dense passthrough (Phase 3에서 진짜 hybrid로 교체 예정).
    """
    # [Hybrid-P1] Phase 1: dense passthrough — Phase 3에서 RRF로 교체
    return self.retrieve_multi_query_context(
        queries=[query],
        current_ep=current_ep,
        n_per_query=dense_k,
        max_results=max_results,
        current_arc_no=current_arc_no,
    )
```

### 검증
```
python -c "from modules.core.vec_memory import VecMemory; print('OK')"
pytest tests/ -q --tb=short 2>&1 | tail -5
ruff check modules/core/vec_memory.py
```

**기대**: 기존 테스트 전량 통과, API만 추가됨

---

## Phase 2: SQLite FTS5 테이블 + Sparse 검색

**목적**: `episode_fts` 전문 검색 테이블 도입, 저장/삭제 시 동기화
**수정 파일**:
- `modules/core/vec_memory.py`
- `modules/core/db_manager.py`

**전제**: Phase 1 통과

---

### 2-A: FTS5 테이블 생성 (vec_memory.py)

**파일**: `modules/core/vec_memory.py`

`vec_memory.py`에서 `sync_status` 테이블 생성 직후 (현재 L176-181 근처) FTS5 테이블 생성 코드를 추가한다.

현재 초기화 코드는 `_init_db()` 또는 `__init__` 내 커넥션 초기화 블록에 있음.
해당 위치를 Read로 확인하고, `CREATE TABLE sync_status` 바로 다음에 추가:

```python
# [Hybrid-P2] FTS5 전문 검색 테이블
cur.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS episode_fts
    USING fts5(
        summary,
        event_types,
        entity_names,
        tokenize='unicode61 remove_diacritics 2'
    )
""")
```

**주의**: `CREATE VIRTUAL TABLE IF NOT EXISTS`를 사용할 것. `CREATE OR REPLACE` 금지.

---

### 2-B: memorize_v20_episode()에 FTS UPSERT 추가

**파일**: `modules/core/vec_memory.py`
**위치**: `memorize_v20_episode()` 메서드 내 `episode_meta` INSERT 직후 (현재 L376-381 근처)

현재 코드:
```python
cur.execute(
    """INSERT OR REPLACE INTO episode_meta
       (ep_num, summary, causal_data, arc_no, event_types, entity_names)
       VALUES (?,?,?,?,?,?)""",
    (ep_num, summary, causal_json, arc_no, event_types_str, entity_names_str),
)
```

이 INSERT 바로 다음에 추가:
```python
# [Hybrid-P2] FTS 동기화
cur.execute("DELETE FROM episode_fts WHERE rowid = ?", (ep_num,))
cur.execute(
    "INSERT INTO episode_fts(rowid, summary, event_types, entity_names) VALUES (?,?,?,?)",
    (ep_num, summary or "", event_types_str or "", entity_names_str or ""),
)
```

---

### 2-C: delete_episodes_from()에 FTS 삭제 추가

**파일**: `modules/core/vec_memory.py`
**위치**: `delete_episodes_from()` 메서드 내 `DELETE FROM episode_meta` 직전 (현재 L899 근처)

현재 코드:
```python
cur.execute("DELETE FROM vec_episodes WHERE rowid = ?", (ep,))
```
이 루프 내 삭제 다음에 추가:
```python
cur.execute("DELETE FROM episode_fts WHERE rowid = ?", (ep,))
```

그리고 `DELETE FROM episode_meta WHERE ep_num >= ?` 직후에 추가:
```python
cur.execute("DELETE FROM episode_fts WHERE rowid >= ?", (target_ep,))
```

---

### 2-D: db_manager.py FTS 테이블 생성 추가

**파일**: `modules/core/db_manager.py`
**위치**: `episode_meta` 테이블 생성 (L466-474) 바로 다음

```python
# [Hybrid-P2] FTS5 전문 검색 테이블 (vec_memory 공유 모드와 동기화)
self._conn.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS episode_fts
    USING fts5(
        summary,
        event_types,
        entity_names,
        tokenize='unicode61 remove_diacritics 2'
    )
""")
```

**주의**: `self._conn.execute` 또는 `cur.execute` — 파일의 기존 패턴과 일치시킬 것. Read로 확인 후 적용.

---

### 2-E: `_fts_search()` 메서드 추가 (vec_memory.py)

`_keyword_fallback_search()` 메서드(L713) 바로 다음에 추가:

```python
def _fts_search(self, query: str, current_ep: int, n_results: int = 10) -> list[dict]:
    """[Hybrid-P2] FTS5 전문 검색. 결과를 dict 리스트로 반환.

    Returns:
        list of {"ep_num": int, "summary": str, "event_types": str,
                 "entity_names": str, "fts_rank": int}
    """
    keywords = [w for w in __import__("re").split(r"[\s,.\-|/]+", query) if len(w) >= 2]
    if not keywords:
        return []

    # FTS5 쿼리 구성 (각 키워드 OR 결합)
    fts_query = " OR ".join(f'"{kw}"' for kw in keywords[:5])

    try:
        with self._db_lock():
            rows = self._conn.execute(
                """SELECT rowid, summary, event_types, entity_names
                   FROM episode_fts
                   WHERE episode_fts MATCH ?
                     AND rowid < ?
                   ORDER BY rank
                   LIMIT ?""",
                (fts_query, current_ep, n_results),
            ).fetchall()
    except Exception as _e:
        logging.debug("[VecMemory] FTS search failed: %s", _e)
        return []

    results = []
    for rank, (ep_num, summary, event_types, entity_names) in enumerate(rows):
        results.append({
            "ep_num": ep_num,
            "summary": summary or "",
            "event_types": event_types or "",
            "entity_names": entity_names or "",
            "fts_rank": rank,
        })
    return results
```

**주의**: `self._db_lock()` 이 파일에 없으면 파일 내 실제 lock 패턴 확인 후 일치시킬 것.

---

### Phase 2 검증
```
python -c "
import sqlite3, threading
from modules.core.vec_memory import VecMemory
conn = sqlite3.connect(':memory:')
vm = VecMemory(conn=conn, lock=__import__('threading').RLock())
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print([t[0] for t in tables])
assert any('episode_fts' in str(t) for t in tables), 'episode_fts not found'
print('OK')
"
pytest tests/ -q --tb=short 2>&1 | tail -5
ruff check modules/core/vec_memory.py modules/core/db_manager.py
```

---

## Phase 3: RRF Fusion 랭킹 구현

**목적**: `retrieve_hybrid_context()`를 진짜 hybrid로 교체
**수정 파일**: `modules/core/vec_memory.py`
**전제**: Phase 2 통과

### 3-A: `_rrf_score()` 헬퍼 추가

`_fts_search()` 바로 다음에 추가:

```python
@staticmethod
def _rrf_score(dense_rank: int | None, sparse_rank: int | None, k: int = 60) -> float:
    """[Hybrid-P3] Reciprocal Rank Fusion 점수 계산.

    score = 1/(k + dense_rank) + 1/(k + sparse_rank)
    rank가 없으면 해당 항 제외.
    """
    score = 0.0
    if dense_rank is not None:
        score += 1.0 / (k + dense_rank)
    if sparse_rank is not None:
        score += 1.0 / (k + sparse_rank)
    return score
```

---

### 3-B: `_knn_search_raw()` 추가 (dict 리스트 반환)

현재 `_knn_search()` (L672-711)는 포맷된 문자열을 반환한다.
RRF에는 raw dict 리스트가 필요하므로 내부 헬퍼를 추가한다.

`_knn_search()` 메서드 바로 앞에 추가:

```python
def _knn_search_raw(
    self,
    emb: list,
    current_ep: int,
    n_results: int = 10,
    current_arc_no: int | None = None,
) -> list[dict]:
    """[Hybrid-P3] KNN 검색 결과를 dict 리스트로 반환 (RRF용).

    Returns:
        list of {"ep_num": int, "summary": str, "event_types": str,
                 "entity_names": str, "distance": float, "dense_rank": int}
    """
    ser = _serialize_f32(emb)
    try:
        with self._db_lock():
            rows = self._conn.execute(
                """SELECT vec_episodes.rowid, distance,
                          m.summary, m.event_types, m.entity_names, m.arc_no
                   FROM vec_episodes
                   LEFT JOIN episode_meta m ON m.ep_num = vec_episodes.rowid
                   WHERE embedding MATCH ?
                     AND vec_episodes.rowid < ?
                   ORDER BY distance
                   LIMIT ?""",
                (ser, current_ep, n_results),
            ).fetchall()
    except Exception as _e:
        logging.debug("[VecMemory] KNN raw search failed: %s", _e)
        return []

    results = []
    for rank, (ep_num, distance, summary, event_types, entity_names, arc_no) in enumerate(rows):
        # arc bonus: same arc gets distance * 0.9
        adj_distance = distance
        if current_arc_no is not None and arc_no == current_arc_no:
            adj_distance = distance * 0.9
        results.append({
            "ep_num": ep_num,
            "summary": summary or "",
            "event_types": event_types or "",
            "entity_names": entity_names or "",
            "distance": adj_distance,
            "dense_rank": rank,
        })
    return results
```

**주의**: `_db_lock()` 이 없으면 파일 내 실제 lock 패턴 확인 후 일치시킬 것.
**주의**: `vec_episodes.rowid < ?` — 파일 내 기존 KNN 쿼리 패턴과 일치하는지 Read로 확인.

---

### 3-C: `retrieve_hybrid_context()` Phase 1 stub 교체

Phase 1에서 추가한 `retrieve_hybrid_context()` 메서드 전체를 아래로 교체:

```python
def retrieve_hybrid_context(
    self,
    query: str,
    current_ep: int,
    dense_k: int = 10,
    sparse_k: int = 10,
    max_results: int = 5,
    current_arc_no: int | None = None,
    rrf_k: int = 60,
) -> str:
    """[Hybrid-P3] Dense (KNN) + Sparse (FTS5) RRF 하이브리드 검색.

    1. Dense: KNN embedding search → dense_rank 부여
    2. Sparse: FTS5 keyword search → fts_rank 부여
    3. RRF score = 1/(rrf_k+dense_rank) + 1/(rrf_k+fts_rank)
    4. 상위 max_results 포맷 반환
    """
    if not self.has_valid_memory:
        return ""

    query_text = query.strip()
    if not query_text:
        return ""

    # 1. Dense search
    dense_results: list[dict] = []
    emb = self._embed_text(query_text)
    if emb is not None:
        dense_results = self._knn_search_raw(
            emb, current_ep, n_results=dense_k, current_arc_no=current_arc_no
        )

    # 2. Sparse FTS search
    sparse_results = self._fts_search(query_text, current_ep, n_results=sparse_k)

    # 3. RRF fusion
    ep_scores: dict[int, dict] = {}

    for item in dense_results:
        ep = item["ep_num"]
        ep_scores[ep] = {**item, "dense_rank": item["dense_rank"], "sparse_rank": None}

    for item in sparse_results:
        ep = item["ep_num"]
        if ep in ep_scores:
            ep_scores[ep]["sparse_rank"] = item["fts_rank"]
        else:
            ep_scores[ep] = {**item, "dense_rank": None, "sparse_rank": item["fts_rank"]}

    # 4. 점수 계산 및 정렬
    scored = []
    for ep, info in ep_scores.items():
        score = self._rrf_score(info.get("dense_rank"), info.get("sparse_rank"), k=rrf_k)
        scored.append((score, ep, info))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max_results]

    if not top:
        logging.debug("[VecMemory] hybrid search: no results for ep<%d", current_ep)
        return ""

    # 5. 결과 포맷
    blocks = []
    for score, ep_num, info in top:
        source_label = "hybrid"
        if info.get("dense_rank") is not None and info.get("sparse_rank") is not None:
            source_label = "hybrid"
        elif info.get("dense_rank") is not None:
            source_label = "dense"
        else:
            source_label = "sparse"

        block = (
            f"=== EP {ep_num} [{source_label}, rrf={score:.4f}] ===\n"
            f"{info.get('summary', '')}"
        )
        if info.get("event_types"):
            block += f"\n[events] {info['event_types']}"
        if info.get("entity_names"):
            block += f"\n[entities] {info['entity_names']}"
        blocks.append(block)

    return "\n\n".join(blocks)
```

---

### Phase 3 검증
```
python -c "
import sqlite3, threading
from modules.core.vec_memory import VecMemory
conn = sqlite3.connect(':memory:')
vm = VecMemory(conn=conn, lock=threading.RLock())
# retrieve_hybrid_context는 빈 DB에서 빈 문자열을 반환해야 함
result = vm.retrieve_hybrid_context('test query', current_ep=5)
assert isinstance(result, str), f'Expected str, got {type(result)}'
print('retrieve_hybrid_context OK:', repr(result))
"
pytest tests/ -q --tb=short 2>&1 | tail -5
ruff check modules/core/vec_memory.py
```

---

## Phase 4: 설정 플래그 + 호출부 전환

**목적**: `retrieval_mode` 플래그 추가, Stage2/Stage4 호출부를 hybrid 경로로 연결
**수정 파일**:
- `config/settings/validation.yaml`
- `modules/core/stage2_preflight.py`
- `modules/core/stage4_context_builder.py`

**전제**: Phase 3 통과

---

### 4-A: validation.yaml에 설정 추가

**파일**: `config/settings/validation.yaml`
`smart_retrieval` 섹션 끝에 추가 (현재 `max_npcs_per_slot: 5` 다음):

```yaml
  # [Hybrid-P4] 하이브리드 검색 설정
  retrieval_mode: dense          # dense | hybrid | sparse
  dense_k: 10                   # KNN 후보 수
  sparse_k: 10                  # FTS 후보 수
  rrf_k: 60                     # RRF k 파라미터
```

**주의**: YAML 들여쓰기는 `smart_retrieval` 하위 항목과 동일하게 맞출 것 (스페이스 2칸).

---

### 4-B: stage2_preflight.py 호출부 수정

**파일**: `modules/core/stage2_preflight.py`
**위치**: L133-146 (현재 `retrieve_high_res_context` / `retrieve_multi_query_context` 분기)

Read로 파일 확인 후, 현재:
```python
        elif vec_slot_count <= 1:
            result = memory.retrieve_high_res_context(
                query_text,
                current_ep,
                n_results=max_results,
            )
        else:
            result = memory.retrieve_multi_query_context(
                queries=[query_text],
                current_ep=current_ep,
                n_per_query=3,
                max_results=max_results,
                current_arc_no=current_arc_no,
            )
```

를 아래로 교체:

```python
        else:
            # [Hybrid-P4] retrieval_mode 플래그 기반 경로 분기
            _retrieval_mode = _threshold("smart_retrieval.retrieval_mode", "dense")
            if _retrieval_mode == "hybrid" and hasattr(memory, "retrieve_hybrid_context"):
                result = memory.retrieve_hybrid_context(
                    query=query_text,
                    current_ep=current_ep,
                    dense_k=int(_threshold("smart_retrieval.dense_k", 10)),
                    sparse_k=int(_threshold("smart_retrieval.sparse_k", 10)),
                    max_results=max_results,
                    current_arc_no=current_arc_no,
                    rrf_k=int(_threshold("smart_retrieval.rrf_k", 60)),
                )
            elif _retrieval_mode == "sparse" and hasattr(memory, "_fts_search"):
                _fts = memory._fts_search(query_text, current_ep, n_results=max_results)
                result = "\n\n".join(
                    f"=== EP {r['ep_num']} [sparse] ===\n{r['summary']}"
                    for r in _fts
                ) if _fts else ""
            elif vec_slot_count <= 1:
                result = memory.retrieve_high_res_context(
                    query_text,
                    current_ep,
                    n_results=max_results,
                )
            else:
                result = memory.retrieve_multi_query_context(
                    queries=[query_text],
                    current_ep=current_ep,
                    n_per_query=3,
                    max_results=max_results,
                    current_arc_no=current_arc_no,
                )
```

**주의**: `_threshold`가 이 파일에서 어떻게 import/사용되는지 Read로 확인 후 동일 패턴 적용.
`_threshold`가 없으면 `ThresholdHelper.get()` 패턴 사용.

---

### 4-C: stage4_context_builder.py 호출부 수정

**파일**: `modules/core/stage4_context_builder.py`
**위치**: L166-172 (현재 `retrieve_multi_query_context` 호출)

Read로 파일 확인 후, 현재:
```python
        else:
            result = memory.retrieve_multi_query_context(
                queries=[query_text],
                current_ep=plan.episode_num,
                n_per_query=3,
                max_results=max_results,
            )
```

를 아래로 교체:

```python
        else:
            # [Hybrid-P4] retrieval_mode 플래그 기반 경로 분기
            _retrieval_mode = _threshold("smart_retrieval.retrieval_mode", "dense")
            if _retrieval_mode == "hybrid" and hasattr(memory, "retrieve_hybrid_context"):
                result = memory.retrieve_hybrid_context(
                    query=query_text,
                    current_ep=plan.episode_num,
                    dense_k=int(_threshold("smart_retrieval.dense_k", 10)),
                    sparse_k=int(_threshold("smart_retrieval.sparse_k", 10)),
                    max_results=max_results,
                    rrf_k=int(_threshold("smart_retrieval.rrf_k", 60)),
                )
            elif _retrieval_mode == "sparse" and hasattr(memory, "_fts_search"):
                _fts = memory._fts_search(query_text, plan.episode_num, n_results=max_results)
                result = "\n\n".join(
                    f"=== EP {r['ep_num']} [sparse] ===\n{r['summary']}"
                    for r in _fts
                ) if _fts else ""
            else:
                result = memory.retrieve_multi_query_context(
                    queries=[query_text],
                    current_ep=plan.episode_num,
                    n_per_query=3,
                    max_results=max_results,
                )
```

**주의**: `_threshold` 사용 패턴 Read로 확인 필수.

---

### Phase 4 검증
```
python -c "
from modules.validation.threshold_helper import ThresholdHelper
mode = ThresholdHelper.get('smart_retrieval.retrieval_mode', 'dense')
print('retrieval_mode:', mode)
assert mode == 'dense', f'Expected dense (default), got {mode}'
print('OK — default is dense, no behavior change')
"
pytest tests/ -q --tb=short 2>&1 | tail -5
ruff check modules/core/stage2_preflight.py modules/core/stage4_context_builder.py config/settings/validation.yaml
```

---

## Phase 5: 관측성 + 품질 테스트

**목적**: 로깅 보강 + hybrid 경로 테스트
**수정 파일**:
- `modules/core/vec_memory.py` (로그 추가)
- `tests/test_vec_memory.py` (테스트 추가)

**전제**: Phase 4 통과

---

### 5-A: retrieve_hybrid_context()에 관측성 로그 추가

**파일**: `modules/core/vec_memory.py`
`retrieve_hybrid_context()` 내 scored.sort() 직후, `if not top:` 분기 전에 추가:

```python
logging.debug(
    "[Hybrid] ep<%d query=%r dense=%d sparse=%d fused=%d top_score=%.4f",
    current_ep,
    query_text[:40],
    len(dense_results),
    len(sparse_results),
    len(scored),
    scored[0][0] if scored else 0.0,
)
```

---

### 5-B: 테스트 추가

`tests/test_vec_memory.py`에 클래스 `TestHybridRetrieval` 추가:

```python
class TestHybridRetrieval:
    """Phase 5: hybrid retrieval 경로 검증."""

    def _make_vm(self):
        import sqlite3, threading
        from modules.core.vec_memory import VecMemory
        conn = sqlite3.connect(":memory:")
        vm = VecMemory(conn=conn, lock=threading.RLock())
        return vm, conn

    def test_retrieve_hybrid_returns_str(self):
        """retrieve_hybrid_context()는 항상 str을 반환한다."""
        vm, _ = self._make_vm()
        result = vm.retrieve_hybrid_context("test query", current_ep=5)
        assert isinstance(result, str)

    def test_retrieve_hybrid_empty_db_returns_empty(self):
        """벡터 데이터 없을 때 빈 문자열 반환."""
        vm, _ = self._make_vm()
        assert vm.retrieve_hybrid_context("query", current_ep=3) == ""

    def test_rrf_score_both_ranks(self):
        """RRF 점수: dense+sparse 모두 있으면 각 단독보다 크다."""
        from modules.core.vec_memory import VecMemory
        score_both = VecMemory._rrf_score(0, 0, k=60)
        score_dense_only = VecMemory._rrf_score(0, None, k=60)
        score_sparse_only = VecMemory._rrf_score(None, 0, k=60)
        assert score_both > score_dense_only
        assert score_both > score_sparse_only

    def test_rrf_score_none_rank_excluded(self):
        """RRF 점수: rank None은 해당 항 제외."""
        from modules.core.vec_memory import VecMemory
        score = VecMemory._rrf_score(None, None, k=60)
        assert score == 0.0

    def test_fts_table_exists_after_init(self):
        """VecMemory 초기화 후 episode_fts 테이블이 존재한다."""
        vm, conn = self._make_vm()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','shadow')"
        ).fetchall()
        names = [t[0] for t in tables]
        assert any("episode_fts" in n for n in names), f"episode_fts not in {names}"

    def test_fts_search_empty_db_returns_empty_list(self):
        """FTS 검색: 빈 DB에서 빈 리스트 반환."""
        vm, _ = self._make_vm()
        result = vm._fts_search("이준혁", current_ep=10, n_results=5)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_retrieval_mode_dense_uses_existing_api(self):
        """retrieval_mode=dense일 때 retrieve_hybrid_context가 str을 반환한다."""
        vm, _ = self._make_vm()
        result = vm.retrieve_hybrid_context(
            "query", current_ep=5, dense_k=5, sparse_k=5, max_results=3
        )
        assert isinstance(result, str)
```

---

### Phase 5 최종 검증

```
pytest tests/test_vec_memory.py -v --tb=short 2>&1 | tail -30
pytest tests/ -q --tb=short 2>&1 | tail -5
ruff check modules/core/vec_memory.py tests/test_vec_memory.py
```

**기대**: 2494 + 3(Phase0) + 7(Phase5) = 2504+ passed

---

## 전체 완료 기준 (Definition of Done)

| 항목 | 확인 방법 |
|---|---|
| `retrieve_hybrid_context()` 존재 | `python -c "from modules.core.vec_memory import VecMemory; VecMemory.retrieve_hybrid_context"` |
| `episode_fts` 테이블 생성됨 | Phase 5 테스트 통과 |
| RRF 점수 계산 정확 | `test_rrf_score_*` 테스트 통과 |
| `retrieval_mode=dense` 기본값 유지 | Phase 4 검증 명령 |
| 기존 테스트 회귀 없음 | 전체 pytest 통과 |
| ruff clean | `ruff check .` 0 violations |

---

## 실행 후 설정으로 hybrid 활성화 방법

구현 완료 후 `config/settings/validation.yaml`에서:
```yaml
smart_retrieval:
  retrieval_mode: hybrid   # dense → hybrid 로 변경
```
로 변경하면 Stage2/Stage4가 즉시 hybrid 경로를 사용.
문제 발생 시 `dense`로 되돌리면 즉시 복구.

---

## 파일별 수정 요약

| 파일 | Phase | 변경 내용 |
|---|---|---|
| `tests/test_vec_memory.py` | 0, 5 | TestDenseBaselineRegression (3개), TestHybridRetrieval (7개) |
| `modules/core/vec_memory.py` | 1, 2, 3, 5 | retrieve_hybrid_context(), FTS init, FTS sync, _fts_search(), _knn_search_raw(), _rrf_score() |
| `modules/core/db_manager.py` | 2 | episode_fts CREATE TABLE |
| `config/settings/validation.yaml` | 4 | retrieval_mode, dense_k, sparse_k, rrf_k 추가 |
| `modules/core/stage2_preflight.py` | 4 | retrieval_mode 분기 추가 |
| `modules/core/stage4_context_builder.py` | 4 | retrieval_mode 분기 추가 |
