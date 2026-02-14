# Phase 4D: sqlite-vec SSOT 통합 + ChromaDB 비활성 경로 재연결

> 기준: `phase4c-complete` 태그 (2026-02-13)
> 목표: ChromaDB 전면 교체 → sqlite-vec 단일 벡터 엔진으로 통합

---

## 1. 현황 분석

### 1-1. ChromaDB 현재 상태

| 상태 | 설명 |
|------|------|
| **비활성화** | Windows Rust binding segfault (V66.3) → `memory_engine.py` L113-121에서 초기화 스킵 |
| **결과** | 모든 벡터 검색 메서드가 빈 결과(`""`, `[]`, `False`) 반환 |
| **영향** | Stage 2/4의 벡터 맥락 주입, 에피소드 박제, 동기화 모두 무효 |

### 1-2. ChromaDB 참조 파일 목록 (프로덕션 코드)

| 파일 | 참조 유형 | 용도 |
|------|-----------|------|
| `modules/core/memory_engine.py` | `import chromadb`, `GoogleEmbeddingFunction`, `LongTermMemory` | 핵심 벡터 엔진 (비활성) |
| `modules/core/blueprint_memory.py` | `import chromadb`, `BlueprintMemory`, `SuccessPatternMemory` | Blueprint 시맨틱 검색 (비활성) |
| `modules/core/semantic_plot_guard.py` | `genai` 임베딩 직접 호출 (ChromaDB 미사용) | 플롯 중복 감지 (in-memory) |
| `modules/core/semantic_cache.py` | Pure Python Jaccard (ChromaDB 미사용) | 의미 캐시 (벡터 불필요) |
| `modules/core/error_helper.py` | ChromaDB 에러 분류 문자열 | 에러 메시지 |
| `modules/core/db_manager.py` | ChromaDB LOCK 해결책 로그 문자열 | 로그 메시지 |
| `modules/core/stage01_helpers.py` | `persist_to_chromadb()` 호출 | Stage 0 벡터화 |
| `modules/core/stage0/reverse_expander.py` | `persist_to_chromadb()` 구현 | 원고 벡터화 |
| `modules/core/project_manager.py` | ChromaDB 동기화 + 기억 소거 | 프로젝트 관리 |
| `modules/domain/agents/four_phase_arc_generator.py` | `vector_context` 필드 docstring | Arc 생성기 |
| `modules/core/stage2_orchestrator.py` | `self.ctx.memory.retrieve_high_res_context()` | Stage 2 벡터 맥락 |
| `modules/core/stage4_orchestrator.py` | `self.ctx.memory.*` (4곳) | Stage 4 벡터 맥락 + 박제 + 동기화 |
| `main_a.py` | `LongTermMemory`, `BlueprintMemory` 초기화 + shutdown | 엔트리포인트 |
| `RESET.py` | ChromaDB 벡터 소거/삭제 | 리셋 도구 |

### 1-3. 호출 경로 맵

```
main_a.py
├── self.memory = LongTermMemory(project)      # L906 (비활성)
├── self.blueprint_memory = BlueprintMemory()   # L908-914 (비활성, 미사용)
├── Stage 0: stage01_helpers → reverse_expander.persist_to_chromadb()
├── Stage 2: stage2_orch.ctx.memory.retrieve_high_res_context()   # → ""
├── Stage 4: stage4_orch.ctx.memory
│   ├── .retrieve_multi_query_context()  # L693-719 → ""
│   ├── .memorize_v20_episode()          # L1457-1458 → False
│   └── .sync_v20_drafts()              # L1782-1785 → no-op
└── Shutdown: self.memory = None
```

### 1-4. 변경 불필요 파일

| 파일 | 사유 |
|------|------|
| `semantic_plot_guard.py` | ChromaDB 미사용, genai 직접 호출 + in-memory 리스트. 변경 불필요 |
| `semantic_cache.py` | Pure Python, 벡터 불필요. 변경 불필요 |
| `four_phase_arc_generator.py` | docstring만. 변경 불필요 (Phase 5에서 정리) |

---

## 2. sqlite-vec 기술 명세

### 2-1. 설치

```bash
pip install sqlite-vec
```

Windows 호환. Python 3.11+ 지원. Pure SQLite 확장 — Rust 의존성 없음.

### 2-2. 핵심 API

```python
import sqlite3
import sqlite_vec

# 1. 확장 로드
db = sqlite3.connect(":memory:")
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)

# 2. 가상 테이블 생성
db.execute("""
    CREATE VIRTUAL TABLE vec_episodes USING vec0(
        embedding float[768]
    )
""")

# 3. 벡터 삽입
from sqlite_vec import serialize_float as sf
db.execute(
    "INSERT INTO vec_episodes(rowid, embedding) VALUES (?, ?)",
    (ep_num, sf(embedding_list))
)

# 4. KNN 검색
db.execute("""
    SELECT rowid, distance
    FROM vec_episodes
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT 5
""", (sf(query_vector),))
```

### 2-3. 임베딩 모델

기존 `GoogleEmbeddingFunction` (`gemini-embedding-001`, 768차원) 재사용.
ChromaDB wrapper 제거 → genai 직접 호출로 단순화.

---

## 3. 아키텍처 설계

### 3-1. 신규 모듈: `modules/core/vec_memory.py`

LongTermMemory + BlueprintMemory 기능 통합.

```
VecMemory
├── __init__(db_path, api_key)
├── _load_extension()           # sqlite-vec 로드
├── _ensure_tables()            # vec_episodes + vec_blueprints + metadata
├── embed_text(text) → list     # genai 직접 호출 (GoogleEmbeddingFunction 로직 이관)
├── memorize_episode(ep, text, summary, ...) → bool
├── retrieve_context(query, current_ep, n=3) → str
├── retrieve_multi_query(queries, current_ep, ...) → str
├── index_blueprint(ep, bp_data) → bool
├── search_related_blueprints(query, n=5, exclude=[]) → list
├── sync_drafts(drafts_path) → int
├── is_operational() → bool
├── get_status() → dict
├── close()
```

**핵심 원칙**: 단일 SQLite 연결에 vec0 확장 로드. 기존 `project_data.db`와 별도 파일(`vec_memory.db`).

### 3-2. 테이블 스키마

```sql
-- 에피소드 벡터
CREATE VIRTUAL TABLE vec_episodes USING vec0(
    embedding float[768]
);

-- 에피소드 메타데이터 (rowid = ep_num)
CREATE TABLE episode_meta (
    ep_num INTEGER PRIMARY KEY,
    summary TEXT,
    causal_data TEXT,
    arc_no INTEGER,
    event_types TEXT,
    entity_names TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Blueprint 벡터
CREATE VIRTUAL TABLE vec_blueprints USING vec0(
    embedding float[768]
);

-- Blueprint 메타데이터
CREATE TABLE blueprint_meta (
    ep_num INTEGER PRIMARY KEY,
    title TEXT,
    arc_no INTEGER,
    items TEXT,
    document TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3-3. 마이그레이션 경로

```
Before:
  main_a.py → LongTermMemory (ChromaDB, 비활성)
            → BlueprintMemory (ChromaDB, 비활성)
  stage2/4  → self.ctx.memory.retrieve_*()  → ""
  stage4    → self.ctx.memory.memorize_*()  → False

After:
  main_a.py → VecMemory (sqlite-vec, 활성)
  stage2/4  → self.ctx.memory.retrieve_*()  → 실제 벡터 검색 결과
  stage4    → self.ctx.memory.memorize_*()  → True
```

---

## 4. 파일별 변경 목록

### 4-1. 신규 파일 (2건)

| 파일 | 내용 | 예상 크기 |
|------|------|-----------|
| `modules/core/vec_memory.py` | VecMemory 클래스 | ~350줄 |
| `tests/test_vec_memory.py` | 단위 테스트 | ~200줄 |

### 4-2. 수정 파일 (8건)

| 파일 | 변경 내용 | 위험도 |
|------|-----------|--------|
| `main_a.py` | `LongTermMemory` → `VecMemory` 교체 (L906), `BlueprintMemory` 제거 (L908-914), shutdown 정리 (L771-777), `_check_vector_db_lock` ChromaDB→sqlite 변경 (L1106-1144) | **HIGH** |
| `modules/core/memory_engine.py` | `GoogleEmbeddingFunction` 유지 (genai 래퍼), `LongTermMemory` 클래스 deprecated 주석 | LOW |
| `modules/core/blueprint_memory.py` | `BlueprintMemory` ChromaDB import 제거, deprecated 주석 또는 삭제 | LOW |
| `modules/core/stage01_helpers.py` | `persist_to_chromadb()` 호출 → `VecMemory.sync_drafts()` 경유 | MEDIUM |
| `modules/core/stage0/reverse_expander.py` | `persist_to_chromadb()` → `persist_to_vec()` 리네임 + sqlite-vec 사용 | MEDIUM |
| `modules/core/project_manager.py` | ChromaDB 동기화/소거 → VecMemory 경유 | MEDIUM |
| `modules/core/error_helper.py` | ChromaDB 에러 문자열 → sqlite-vec 에러로 갱신 | LOW |
| `RESET.py` | ChromaDB 벡터 소거 → VecMemory DB 파일 삭제/rewind | MEDIUM |
| `requirements.txt` | `chromadb` 주석 유지, `sqlite-vec` 주석 해제 | LOW |

### 4-3. 미변경 파일 (호출부 — 인터페이스 호환으로 무변경)

| 파일 | 사유 |
|------|------|
| `stage2_orchestrator.py` | `self.ctx.memory.retrieve_high_res_context()` — VecMemory가 동일 시그니처 제공 |
| `stage4_orchestrator.py` | `self.ctx.memory.*` 4곳 — VecMemory가 동일 시그니처 제공 |
| `stage4_context.py` | `memory` 슬롯 유지 — 타입만 변경 |
| `stage2_context.py` | `memory` 콜백 유지 |

---

## 5. 단계별 실행 계획

### Step 1: VecMemory 모듈 신규 작성 (커밋 1)

**작업**:
1. `modules/core/vec_memory.py` 작성
2. `tests/test_vec_memory.py` 작성
3. `requirements.txt` 갱신

**게이트**:
```bash
pip install sqlite-vec
python -m py_compile modules/core/vec_memory.py
set PYTHONIOENCODING=utf-8 && pytest tests/test_vec_memory.py -v
```

**검증 항목**:
- [ ] sqlite-vec 확장 로드 성공
- [ ] vec0 테이블 생성 성공
- [ ] 임베딩 삽입/검색 왕복 성공
- [ ] retrieve_context() 반환 형식이 LongTermMemory와 동일
- [ ] is_operational() 정상 판정
- [ ] close() 리소스 정리

### Step 2: main_a.py 교체 (커밋 2)

**작업**:
1. `LongTermMemory` import → `VecMemory` import
2. `self.memory = LongTermMemory(...)` → `self.memory = VecMemory(...)`
3. `BlueprintMemory` 초기화 블록 제거 (L908-914)
4. `self.blueprint_memory` 참조 정리
5. `_check_vector_db_lock()` ChromaDB 경로 → VecMemory DB 경로
6. Shutdown 블록 (L771-777) VecMemory.close() 호출로 변경

**게이트**:
```bash
python -m py_compile main_a.py
python -c "from main_a import SovereignApp; print('OK')"
set PYTHONIOENCODING=utf-8 && pytest tests/ -v --timeout=60
```

### Step 3: Stage 0 벡터화 경로 교체 (커밋 3)

**작업**:
1. `stage01_helpers.py`: `persist_to_chromadb()` 호출 → VecMemory 경유
2. `reverse_expander.py`: `persist_to_chromadb()` → VecMemory API 사용

**게이트**:
```bash
python -m py_compile modules/core/stage01_helpers.py
python -m py_compile modules/core/stage0/reverse_expander.py
set PYTHONIOENCODING=utf-8 && pytest tests/ -v
```

### Step 4: 보조 파일 정리 (커밋 4)

**작업**:
1. `project_manager.py`: ChromaDB 동기화/소거 → VecMemory 경유
2. `error_helper.py`: ChromaDB 에러 문자열 갱신
3. `RESET.py`: ChromaDB 벡터 소거 → VecMemory DB 파일 기반 리셋
4. `memory_engine.py`: deprecated 주석 추가
5. `blueprint_memory.py`: deprecated 주석 추가 (SuccessPatternMemory는 순수 Python이므로 유지)

**게이트**:
```bash
python -m py_compile modules/core/project_manager.py
python -m py_compile modules/core/error_helper.py
python -m py_compile RESET.py
python -m py_compile modules/core/memory_engine.py
python -m py_compile modules/core/blueprint_memory.py
set PYTHONIOENCODING=utf-8 && pytest tests/ -v
```

### Step 5: 통합 검증 + 태그 (커밋 5)

**작업**:
1. `requirements.txt`에서 `chromadb` 주석 라인 유지 (히스토리)
2. 전체 회귀 테스트
3. 수동 연기 테스트 (Stage 0 → 2 → 4 순차 실행, 벡터 검색 결과 확인)

**게이트**:
```bash
# 1. 전체 py_compile
python -m py_compile main_a.py modules/core/vec_memory.py modules/core/memory_engine.py modules/core/blueprint_memory.py modules/core/stage01_helpers.py modules/core/stage0/reverse_expander.py modules/core/project_manager.py modules/core/error_helper.py RESET.py

# 2. SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# 3. 전체 pytest
set PYTHONIOENCODING=utf-8 && pytest tests/ -v

# 4. ChromaDB import 잔여 검사 (deprecated 파일 제외)
rg "import chromadb" --type py -l | findstr /v "memory_engine.py blueprint_memory.py"
# 기대: 0건 (RESET.py는 제거됨)

# 5. 벡터 검색 수동 테스트 (선택)
python -c "from modules.core.vec_memory import VecMemory; m = VecMemory(':memory:'); print(m.get_status())"
```

---

## 6. 인터페이스 호환성 매트릭스

VecMemory가 LongTermMemory의 기존 인터페이스를 완전 호환해야 하는 메서드:

| 메서드 | LongTermMemory 시그니처 | VecMemory 시그니처 | 호출부 |
|--------|------------------------|--------------------|----|
| `retrieve_high_res_context` | `(query, current_ep, n_results=3) → str` | 동일 | stage2_orch L753 |
| `retrieve_multi_query_context` | `(queries, current_ep, n_per_query=3, max_results=5) → str` | 동일 | stage4_orch L715 |
| `memorize_v20_episode` | `(ep_num, text, summary, causal_links, arc_no=None, event_types=None, entity_names=None) → bool` | 동일 | stage4_orch L1458 |
| `sync_v20_drafts` | `(force_repair=False) → None` | 동일 | stage4_orch L1785 |
| `is_operational` | `() → bool` | 동일 | stage4_orch L1457, L1782 |
| `save_v20_anchor` | `(key, data) → bool` | 동일 | main_a.py 간접 |
| `load_v20_anchor` | `(key) → Any` | 동일 | main_a.py 간접 |
| `get_status` | `() → dict` | 동일 | 진단용 |
| `close` | `() → None` | 동일 | shutdown |

---

## 7. 롤백 플랜

### 7-1. 커밋 단위 롤백

각 커밋은 독립적이고 `git revert`로 안전하게 롤백 가능.

| 커밋 | 롤백 시 영향 |
|------|------------|
| 커밋 1 (VecMemory 신규) | 파일 삭제만. 기존 코드 무영향 |
| 커밋 2 (main_a.py 교체) | LongTermMemory 복원. ChromaDB 비활성 상태로 복귀 |
| 커밋 3 (Stage 0) | persist_to_chromadb 복원. 비활성 상태로 복귀 |
| 커밋 4 (보조 파일) | 문자열/주석 복원 |
| 커밋 5 (통합 검증) | 태그/문서만 |

### 7-2. 전체 롤백

```bash
git revert HEAD~4..HEAD --no-commit
git commit -m "revert: Phase 4D rollback — sqlite-vec → ChromaDB (비활성) 복원"
```

### 7-3. 데이터 롤백

- `vec_memory.db` 파일 삭제로 벡터 데이터 초기화
- 기존 `project_data.db` (SQLite anchor)는 무변경 → 데이터 손실 없음
- ChromaDB `chroma_db/` 디렉토리는 삭제하지 않음 (Phase 5에서 정리)

---

## 8. 리스크 및 완화

| 리스크 | 확률 | 영향 | 완화 |
|--------|------|------|------|
| sqlite-vec Windows 로드 실패 | 낮음 | 높음 | Step 1에서 즉시 검증, 실패 시 Phase 중단 |
| 임베딩 API 비용 증가 | 낮음 | 중간 | 기존과 동일 모델/호출 빈도, 변경 없음 |
| 벡터 차원 불일치 | 낮음 | 높음 | `gemini-embedding-001` 고정 (768), vec0 테이블에 명시 |
| 기존 테스트 회귀 | 중간 | 중간 | 인터페이스 호환으로 mock 기반 테스트 무영향 |
| Stage 0 벡터화 실패 | 중간 | 낮음 | 비차단 (try/except), 기존과 동일 정책 |
| RESET.py 호환 | 낮음 | 중간 | 파일 삭제 기반으로 단순화 |

---

## 9. 정량 예측

| 지표 | Before | After |
|------|--------|-------|
| ChromaDB import 파일 | 6 | 2 (deprecated) |
| 벡터 검색 활성 | 0% (비활성) | 100% (sqlite-vec) |
| 외부 의존성 (Rust) | chromadb (segfault) | sqlite-vec (Pure C) |
| 벡터 엔진 파일 | 2 (memory_engine + blueprint_memory) | 1 (vec_memory) |
| 코드 줄 수 변화 | +350 (신규) / -0 (deprecated만) | 순증 ~350줄 |

---

## 10. 커밋 분할 전략

```
커밋 1: feat(4D-1): VecMemory sqlite-vec 벡터 엔진 신규 작성
커밋 2: refactor(4D-2): main_a.py ChromaDB → VecMemory 교체
커밋 3: refactor(4D-3): Stage 0 벡터화 경로 sqlite-vec 전환
커밋 4: chore(4D-4): 보조 파일 ChromaDB 참조 정리
커밋 5: test(4D-5): Phase 4D 통합 검증 + 태그
```

각 커밋은 `py_compile` + `pytest` 게이트 통과 필수.
커밋 2 이후부터 벡터 검색 실제 활성화.

---

## 부록: SuccessPatternMemory 처리

`blueprint_memory.py`의 `SuccessPatternMemory`는 ChromaDB를 사용하지 않음 (순수 Python dict).
현재 `main_a.py`에서 import만 되고 실제 사용처 없음 (L103).
Phase 4D에서는 deprecated 주석만 추가하고, Phase 5에서 활용 여부 결정.
