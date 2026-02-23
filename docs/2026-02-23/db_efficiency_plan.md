# DB 효율화 플랜 (Codex 실행용)

> **작성일**: 2026-02-23
> **대상 실행자**: Codex (자동 에이전트)
> **실행 전제**: D1 Hybrid Retrieval (hybrid_retrieval_impl_plan.md) 완료 + 커밋 확인 후 진행
> **감사 기반**: DB SSOT 감사 2026-02-23 (Explore agent)

---

## ⚠️ Codex 실행 규칙

1. **각 Phase 완료 후 `pytest tests/ -q` 실행** — 실패 시 다음 Phase 진행 금지
2. **각 Phase 완료 후 `ruff check .` 실행** — violations 있으면 수정 후 진행
3. 파일 수정 전 반드시 해당 파일을 Read 도구로 읽을 것
4. Phase 0은 **코드 변경 없음** — 파일/디렉토리 삭제만
5. Phase 1~2는 새 DB 테이블 추가 + 기존 파일 I/O 제거
6. Phase 3~4는 스키마 보강 (인덱스, 정책)
7. 한글 주석은 `# [태그]` 형식으로만

---

## 현황 진단 요약

### DB SSOT 점수: 6.2/10

| 항목 | 현황 | 심각도 |
|------|------|--------|
| `chroma_db/` 폴더 | 완전 미사용 레거시 | 즉시 삭제 |
| `character_voice.json` | DB 없음, 파일만 존재 | 높음 |
| `foreshadow.json` | DB 없음, 파일만 존재 | 높음 |
| `failure_learning.json` | reflexion_memory 테이블 + 파일 이중 저장 | 중간 |
| `stage0_output/*.json` | anchors 테이블 + 파일 이중 저장 | 낮음(export 허용) |
| `plans/arcs/*.txt`, `plans/blueprints/*.txt` | blueprints 테이블 + 파일 이중 저장 | 낮음(export 허용) |
| `anchors` 테이블 | 4개 키만 사용 (arcs, bible, genre_info, sys_caches) | 정책 명시 필요 |
| 인덱스 | 8개 존재, manuscripts/blueprints 미인덱스 | 보강 권고 |

---

## Phase 0: 레거시 chroma_db 삭제

**목적**: Phase 4D(sqlite-vec 전환) 완료 후 방치된 ChromaDB 폴더 제거
**코드 변경**: 없음 (파일/폴더 삭제만)
**위험도**: 없음 (코드 내 참조 0건 확인됨)

### 작업

#### 0-A: 코드 참조 없는지 재확인
```bash
grep -rn "chroma_db\|chromadb\|long_term_anchor" modules/ main_a.py --include="*.py"
```
→ **결과가 0건이어야 함**. 1건 이상이면 진행 중단하고 보고.

#### 0-B: 삭제 대상 목록 확인
```bash
find projects/ -name "chroma_db" -type d
```

#### 0-C: 삭제 실행
```bash
# 각 프로젝트별 chroma_db 폴더 삭제
find projects/ -name "chroma_db" -type d -exec rm -rf {} +
```

#### 0-D: 삭제 확인
```bash
find projects/ -name "chroma_db" -type d
# → 결과 없어야 함
find projects/ -name "long_term_anchor.db"
# → 결과 없어야 함
```

### 검증
```
pytest tests/ -q --tb=short 2>&1 | tail -5
# 기존 테스트 전량 통과 확인
```

**커밋 메시지**: `chore: chroma_db 레거시 폴더 전량 삭제 (Phase 4D 잔여)`

---

## Phase 1: character_voice + foreshadow → DB 전환

**목적**: 파일 기반 상태 저장을 DB 테이블로 전환 → 롤백/마이그레이션 안전성 확보
**수정 파일**:
- `modules/core/db_manager.py` (테이블 추가)
- `main_a.py` (파일 I/O → DB I/O 전환)
**전제**: Phase 0 통과

---

### 1-A: db_manager.py에 테이블 추가

**파일**: `modules/core/db_manager.py`
**위치**: `episode_pacing` 테이블 생성 (L481-493) 바로 다음에 추가

```python
# [DB-Eff-P1] character_voice 프로필 테이블
self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS character_voice (
        npc_name TEXT PRIMARY KEY,
        profile_data TEXT NOT NULL,   -- JSON: CharacterVoiceProfile 직렬화
        updated_at TEXT DEFAULT (datetime('now'))
    )
""")

# [DB-Eff-P1] foreshadow 복선 테이블
self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS foreshadow (
        seed_id TEXT PRIMARY KEY,
        category TEXT,
        content TEXT NOT NULL,
        status TEXT DEFAULT 'planted',   -- planted | triggered | resolved
        planted_ep INTEGER,
        resolved_ep INTEGER,
        data TEXT,                        -- JSON: 원본 데이터 보존
        updated_at TEXT DEFAULT (datetime('now'))
    )
""")
self.cursor.execute(
    "CREATE INDEX IF NOT EXISTS idx_foreshadow_status ON foreshadow(status)"
)
```

**주의**: Read로 L481 이후 실제 코드 확인 후 적절한 위치에 삽입.

---

### 1-B: CharacterVoiceTracker에 DB 저장/로드 메서드 추가

**파일**: `modules/core/character_voice.py`

Read로 파일 구조 확인 후, 클래스 내 다음 메서드 추가:

```python
def save_to_db(self, db) -> None:
    """[DB-Eff-P1] character_voice 테이블에 저장."""
    import json
    for name, profile in self.profiles.items():
        profile_json = json.dumps(
            profile.__dict__ if hasattr(profile, "__dict__") else profile,
            ensure_ascii=False,
        )
        db.conn.execute(
            """INSERT OR REPLACE INTO character_voice(npc_name, profile_data, updated_at)
               VALUES (?, ?, datetime('now'))""",
            (name, profile_json),
        )
    db.conn.commit()

def load_from_db(self, db) -> int:
    """[DB-Eff-P1] character_voice 테이블에서 로드. 로드된 수 반환."""
    import json
    rows = db.conn.execute(
        "SELECT npc_name, profile_data FROM character_voice"
    ).fetchall()
    for name, data in rows:
        self.profiles[name] = json.loads(data)
    return len(rows)
```

**주의**: `profile.__dict__` 직렬화 방식은 실제 CharacterVoiceProfile 구조 확인 후 조정.

---

### 1-C: ForeshadowTracker에 DB 저장/로드 메서드 추가

**파일**: `modules/core/foreshadow_tracker.py`

Read로 파일 구조 확인 후, 클래스 내 다음 메서드 추가:

```python
def save_to_db(self, db) -> None:
    """[DB-Eff-P1] foreshadow 테이블에 저장."""
    import json
    for item in self._get_all_items():   # 실제 내부 데이터 접근 방식 확인 필요
        db.conn.execute(
            """INSERT OR REPLACE INTO foreshadow
               (seed_id, category, content, status, planted_ep, resolved_ep, data, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (
                item.get("id", ""),
                item.get("category", ""),
                item.get("content", ""),
                item.get("status", "planted"),
                item.get("planted_ep"),
                item.get("resolved_ep"),
                json.dumps(item, ensure_ascii=False),
            ),
        )
    db.conn.commit()

def load_from_db(self, db) -> int:
    """[DB-Eff-P1] foreshadow 테이블에서 로드. 로드된 수 반환."""
    import json
    rows = db.conn.execute(
        "SELECT data FROM foreshadow"
    ).fetchall()
    for (data,) in rows:
        self._add_item(json.loads(data))   # 실제 내부 추가 방식 확인 필요
    return len(rows)
```

**주의**: ForeshadowTracker 내부 데이터 구조(`_get_all_items`, `_add_item` 등)는
Read로 파일 확인 후 실제 메서드명에 맞게 조정.

---

### 1-D: main_a.py 로드/저장 경로 전환

**파일**: `main_a.py`

#### 로드 부분 (L1650-1665 근처)

현재:
```python
self.character_voice = _v50["CharacterVoiceTracker"]()
voice_log_path = os.path.join(...)
if os.path.exists(voice_log_path):
    self.character_voice.load_from_json(voice_log_path)

self.foreshadow_tracker = _v50["ForeshadowTracker"]()
foreshadow_log_path = os.path.join(...)
if os.path.exists(foreshadow_log_path):
    self.foreshadow_tracker.load_from_json(foreshadow_log_path)
```

교체:
```python
self.character_voice = _v50["CharacterVoiceTracker"]()
# [DB-Eff-P1] DB 우선 로드, 폴백: 파일
_cv_db_count = self.character_voice.load_from_db(self.current_project.db)
if _cv_db_count == 0:
    voice_log_path = os.path.join(
        self._PROJECTS_DIR, self.current_project.name, "logs", "character_voice.json"
    )
    if os.path.exists(voice_log_path):
        self.character_voice.load_from_json(voice_log_path)
        self.character_voice.save_to_db(self.current_project.db)  # 한 번만 마이그레이션
        self.ui.log("   🎭 [DB-Eff] character_voice JSON→DB 마이그레이션 완료")
else:
    self.ui.log(f"   🎭 [V51.5] 캐릭터 음성 {len(self.character_voice.profiles)}명 로드(DB)")

self.foreshadow_tracker = _v50["ForeshadowTracker"]()
# [DB-Eff-P1] DB 우선 로드, 폴백: 파일
_ft_db_count = self.foreshadow_tracker.load_from_db(self.current_project.db)
if _ft_db_count == 0:
    foreshadow_log_path = os.path.join(
        self._PROJECTS_DIR, self.current_project.name, "logs", "foreshadow.json"
    )
    if os.path.exists(foreshadow_log_path):
        self.foreshadow_tracker.load_from_json(foreshadow_log_path)
        self.foreshadow_tracker.save_to_db(self.current_project.db)  # 한 번만 마이그레이션
        self.ui.log("   🔮 [DB-Eff] foreshadow JSON→DB 마이그레이션 완료")
```

#### 저장 부분 (L2176-2193 근처)

현재 `save_to_json` 호출을 `save_to_db`로 교체:
```python
# [DB-Eff-P1] DB 저장 (파일 저장 제거)
if V50_MODULES_AVAILABLE and self.character_voice and self.current_project:
    try:
        self.character_voice.save_to_db(self.current_project.db)
    except Exception as _e:
        logging.debug("[DB-Eff] character_voice save_to_db 실패: %s", _e)

if V50_MODULES_AVAILABLE and self.foreshadow_tracker and self.current_project:
    try:
        self.foreshadow_tracker.save_to_db(self.current_project.db)
    except Exception as _e:
        logging.debug("[DB-Eff] foreshadow save_to_db 실패: %s", _e)
```

### Phase 1 검증
```
python -c "
from modules.core.db_manager import DBManager
import tempfile, os
with tempfile.TemporaryDirectory() as d:
    db = DBManager(os.path.join(d, 'test.db'))
    tables = db.conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
    names = [t[0] for t in tables]
    assert 'character_voice' in names, f'character_voice missing: {names}'
    assert 'foreshadow' in names, f'foreshadow missing: {names}'
    print('OK — tables:', [n for n in names if n in ('character_voice','foreshadow')])
"
pytest tests/ -q --tb=short 2>&1 | tail -5
ruff check modules/core/db_manager.py modules/core/character_voice.py modules/core/foreshadow_tracker.py main_a.py
```

**커밋 메시지**: `feat(db): character_voice + foreshadow JSON→DB 전환 [DB-Eff-P1]`

---

## Phase 2: failure_learning.json 중복 제거

**목적**: `reflexion_memory` 테이블(DB)과 `failure_learning.json`(파일) 이중 저장 해소
**수정 파일**: `main_a.py`
**전제**: Phase 1 통과

### 배경

현재 `FailureLearner`가:
1. `reflexion_memory` 테이블에 저장 (DB)
2. `logs/failure_learning.json`에도 저장 (파일)

`reflexion_memory`가 이미 SSOT이므로 파일 저장은 제거.

### 작업

**파일**: `main_a.py`
**위치**: L2168 근처 (`failure_log_path` 관련 코드)

Read로 L2160-2175 확인 후, `failure_learning.json` 파일 저장 코드 제거.
FailureLearner가 DB에 직접 저장하는지 확인 후:
- DB 직접 저장이면 → 파일 저장 코드만 제거
- 파일을 통해서만 저장하면 → DB 저장 메서드로 교체

**주의**: 로드 경로도 확인. 파일에서 로드 중이면 DB로 전환 필요.

### 검증
```
pytest tests/ -q --tb=short 2>&1 | tail -5
ruff check main_a.py
```

**커밋 메시지**: `refactor(db): failure_learning.json 이중 저장 제거 [DB-Eff-P2]`

---

## Phase 3: 스키마/인덱스 보강

**목적**: 누락 인덱스 추가 + anchors 테이블 정책 명시화
**수정 파일**: `modules/core/db_manager.py`
**전제**: Phase 2 통과

### 3-A: 누락 인덱스 추가

현재 인덱스 8개 중 아래 테이블에 인덱스 없음:

| 테이블 | 조회 패턴 | 추가 인덱스 |
|--------|---------|-----------|
| `manuscripts` | ep_num (PK이므로 자동 인덱스 ✓) | 불필요 |
| `blueprints` | ep_num (PK이므로 자동 인덱스 ✓) | 불필요 |
| `seeds` | status별 조회 | `idx_seeds_status ON seeds(status)` |
| `encyclopedia` | category별 조회 | `idx_encyclopedia_category ON encyclopedia(category)` |
| `episode_satisfaction_tags` | ep_num (PK ✓) | 불필요 |

**파일**: `modules/core/db_manager.py`
**위치**: 기존 마지막 `CREATE INDEX` 줄 다음에 추가:

```python
# [DB-Eff-P3] 누락 인덱스 보강
self.cursor.execute(
    "CREATE INDEX IF NOT EXISTS idx_seeds_status ON seeds(status)"
)
self.cursor.execute(
    "CREATE INDEX IF NOT EXISTS idx_encyclopedia_category ON encyclopedia(category)"
)
```

### 3-B: anchors 테이블 용도 주석 명시화

**파일**: `modules/core/db_manager.py`
**위치**: `anchors` 테이블 CREATE 문 (L197-204 근처)

현재 코드 바로 위에 주석 추가:
```python
# [DB-Eff-P3] anchors 테이블 SSOT 정책:
# 허용 키: "bible" (세계관), "arcs" (볼륨 Arc), "genre_info" (장르), "sys_caches" (시스템 캐시)
# 금지: character_voice, foreshadow, failure_learning → 전용 테이블 사용
# 추가 키 등록 시 이 목록에 명시 후 진행
```

### 검증
```
python -c "
from modules.core.db_manager import DBManager
import tempfile, os
with tempfile.TemporaryDirectory() as d:
    db = DBManager(os.path.join(d, 'test.db'))
    idx = db.conn.execute(\"SELECT name FROM sqlite_master WHERE type='index'\").fetchall()
    names = [i[0] for i in idx]
    assert 'idx_seeds_status' in names, f'missing: {names}'
    assert 'idx_encyclopedia_category' in names, f'missing: {names}'
    print('OK — indices:', [n for n in names if 'seeds' in n or 'encyclopedia' in n])
"
pytest tests/ -q --tb=short 2>&1 | tail -5
ruff check modules/core/db_manager.py
```

**커밋 메시지**: `refactor(db): 인덱스 보강 + anchors 정책 주석 [DB-Eff-P3]`

---

## Phase 4: export 정책 명시화 (코드 변경 없음)

**목적**: SSOT 위반이 아닌 케이스를 명시적으로 "export" 패턴으로 문서화
**수정 파일**: `modules/core/project_manager.py` (주석만)
**전제**: Phase 3 통과

### 4-A: project_manager.py export 함수 주석 추가

Read로 `_save_blueprint_to_txt`, `_save_arc_to_txt` 등 파일 저장 메서드 확인 후,
각 메서드 상단에 주석 추가:

```python
# [DB-Eff-P4] export 전용: DB(blueprints 테이블)가 primary source.
# 이 파일은 human-readable 참조용. 배포/롤백 대상 아님.
```

### 4-B: reverse_expander.py stage0_output 주석 추가

Read로 `stage0_output` 저장 코드 확인 후, 각 `json.dump` 위에 추가:

```python
# [DB-Eff-P4] export 전용: DB anchors 테이블이 primary source.
# stage0_output/*.json은 편집/참조용 사본.
```

### 검증
```
pytest tests/ -q --tb=short 2>&1 | tail -5
# 코드 변경 없으므로 테스트 카운트 변화 없어야 함
ruff check modules/core/project_manager.py modules/core/stage0/reverse_expander.py
```

**커밋 메시지**: `docs(db): export 정책 주석 명시화 [DB-Eff-P4]`

---

## 전체 완료 기준 (Definition of Done)

| 항목 | 확인 방법 |
|------|---------|
| chroma_db 완전 삭제 | `find projects/ -name "chroma_db" -type d` → 0건 |
| character_voice DB 저장/로드 | Phase 1 검증 통과 |
| foreshadow DB 저장/로드 | Phase 1 검증 통과 |
| failure_learning 이중 저장 제거 | Phase 2 코드 확인 |
| seeds, encyclopedia 인덱스 추가 | Phase 3 검증 통과 |
| 기존 테스트 회귀 없음 | 전체 pytest 통과 |
| ruff clean | `ruff check .` 0 violations |

---

## 파일별 수정 요약

| 파일 | Phase | 변경 내용 |
|------|-------|---------|
| `projects/*/chroma_db/` | 0 | 디렉토리 삭제 |
| `modules/core/db_manager.py` | 1, 3 | character_voice + foreshadow 테이블, 인덱스 2개, anchors 정책 주석 |
| `modules/core/character_voice.py` | 1 | save_to_db(), load_from_db() 추가 |
| `modules/core/foreshadow_tracker.py` | 1 | save_to_db(), load_from_db() 추가 |
| `main_a.py` | 1, 2 | DB 우선 로드 + 파일 폴백, 저장 DB 전환, failure_learning 파일 저장 제거 |
| `modules/core/project_manager.py` | 4 | export 정책 주석 |
| `modules/core/stage0/reverse_expander.py` | 4 | export 정책 주석 |

---

## DB 효율성 최종 평가 (완료 후 예상)

| 항목 | 이전 | 완료 후 |
|------|------|--------|
| SSOT 준수율 | 6.2/10 | **8.5/10** |
| 파일 기반 상태 저장 | 3개 (character_voice, foreshadow, failure_learning) | 0개 |
| 레거시 DB 폐기물 | chroma_db × 5 | 0 |
| 인덱스 누락 | 2개 | 0 |
| 이중 저장 테이블 | 1개 (reflexion_memory + 파일) | 0 |
| 허용된 export 패턴 | 암묵적 | 명시적 주석 |
