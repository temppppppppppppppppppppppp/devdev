# Codex 실행 오더: DB SSOT 통합 (vec_memory.db → project_data.db)

> **목표**: 프로젝트당 DB 파일 2개 → 1개 통합 (진정한 SSOT)
> **현재**: `project_data.db` (DBManager, 16+테이블) + `memory/vec_memory.db` (VecMemory, 4테이블)
> **완료 후**: `project_data.db` 단일 파일 (기존 16+ 테이블 + vec_episodes + episode_meta)

---

## 리뷰 정정 이력 (2026-02-19)

| # | 심각도 | 위치 | 문제 | 수정 |
|---|--------|------|------|------|
| FIX-1 | **CRITICAL** | Phase 3-1 L682-683 | `self.db` → SovereignApp에 없음 (AttributeError 크래시) | `self.current_project.db.conn/._lock` |
| FIX-2 | **HIGH** | Phase 1-3 except블록 | 마이그레이션 실패 시 rollback 없음 → 부분 반영 잔류 | `conn.rollback()` 후 DETACH |
| FIX-3 | **HIGH** | Phase 1-3 L136 | sqlite-vec 미설치 시 vec_episodes 미이관인데 원본 리네임 | `_vec_available` 분기: `.migrated` vs `.partial_migrated` |
| FIX-4a/b | **MEDIUM** | Phase 1-3 L117 + Phase 2-4 L346 | UPDATE-only → 행 부재 시 no-op | UPSERT (`ON CONFLICT DO UPDATE`) |
| FIX-5 | **MEDIUM** | Phase 3-4b ep_tables | `sync_status` DELETE 선행 → 이후 UPDATE no-op | ep_tables에서 `sync_status` 제거 |
| FIX-6 | **MEDIUM** | Phase 3-4c DROP TABLE 루프 | virtual table DROP 시 sqlite-vec 미로드 → OperationalError → nuclear_reset 전체 실패 | per-table try/except 래핑 |
| FIX-8 | **LOW** | Phase 4-3 테스트 | test_migration_copies_episode_meta에 db.close() 누락 | `db.close()` 추가 |
| FIX-9 | **MEDIUM** | Phase 1-3 migration 진입부 | `.partial_migrated` 자동 감지 없음 → FIX-3의 "재시도 가능" 약속 미이행 | `.partial_migrated` + `_vec_available` 시 자동 복원 |

---

## 전제 조건

- 테스트 기준선: `set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short`
- Ruff: `python -m ruff check modules/ main_a.py RESET.py --no-fix`
- 작업 시작 전 현재 커밋 해시 기록 (롤백 기준점)

---

## Phase 1: DBManager에 sqlite-vec 로드 + vec 테이블 생성

### Phase 1-1: sqlite-vec 확장 선택적 로드

**파일**: `modules/core/db_manager.py`

`_boot_db()` 메서드 L66 (`self.cursor = self.conn.cursor()`) **직후**에 삽입:

```python
        # [DB-MERGE] sqlite-vec 확장 로드 (선택적)
        self._vec_available = False
        try:
            import sqlite_vec as _sv

            self.conn.enable_load_extension(True)
            _sv.load(self.conn)
            self.conn.enable_load_extension(False)
            self._vec_available = True
        except ImportError:
            logging.info("[DBManager] sqlite-vec 미설치 — 벡터 테이블 생략")
        except Exception as e:
            logging.info(f"[DBManager] sqlite-vec 로드 실패: {e}")
```

### Phase 1-2: vec 테이블 생성

**파일**: `modules/core/db_manager.py`

`_boot_db()` 메서드의 L358 (`self.cursor.execute("CREATE INDEX ... idx_cost_log_session ...")`) **직후**,
L360 (`self.conn.commit()`) **직전**에 삽입:

```python
        # 17. [DB-MERGE] 벡터 검색 테이블
        if self._vec_available:
            self.cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_episodes
                USING vec0(embedding float[768])
            """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episode_meta (
                ep_num      INTEGER PRIMARY KEY,
                summary     TEXT,
                causal_data TEXT,
                arc_no      INTEGER,
                event_types TEXT,
                entity_names TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
```

### Phase 1-3: 마이그레이션 메서드 추가

**파일**: `modules/core/db_manager.py`

`_boot_db()` 끝 (L360 `self.conn.commit()`) **직후**에 마이그레이션 호출 추가:

```python
        # [DB-MERGE] 기존 vec_memory.db 1회성 마이그레이션
        self._migrate_vec_memory_db()
```

그리고 `_boot_db()` 메서드 **바로 아래** (L361 이후, `begin()` 메서드 전)에 새 메서드 추가:

```python
    def _migrate_vec_memory_db(self) -> None:
        """[DB-MERGE] 기존 memory/vec_memory.db → project_data.db 1회성 마이그레이션."""
        vec_path = Path(self.db_path).parent / "memory" / "vec_memory.db"

        # [FIX-9] MEDIUM: FIX-3에서 sqlite-vec 미설치 시 .partial_migrated로 리네임하지만,
        # 이후 sqlite-vec 설치 후 재실행해도 vec_memory.db가 없어 migration이 skip됨.
        # "재시도 가능" 약속이 거짓이 되므로, .partial_migrated를 자동 감지하여 복원.
        partial_path = vec_path.with_suffix(".db.partial_migrated")
        if not vec_path.exists() and partial_path.exists() and self._vec_available:
            partial_path.rename(vec_path)  # vec_episodes 이관 재시도

        if not vec_path.exists():
            return

        try:
            with self._lock:
                self.cursor.execute("ATTACH DATABASE ? AS vec_old", (str(vec_path),))

                # 1. episode_meta
                self.cursor.execute("""
                    INSERT OR IGNORE INTO episode_meta
                    SELECT * FROM vec_old.episode_meta
                """)

                # 2. vec_episodes (virtual table — row-by-row만 가능)
                if self._vec_available:
                    rows = self.cursor.execute(
                        "SELECT rowid, embedding FROM vec_old.vec_episodes"
                    ).fetchall()
                    for rowid, embedding in rows:
                        try:
                            self.cursor.execute(
                                "INSERT OR REPLACE INTO vec_episodes(rowid, embedding) VALUES (?, ?)",
                                (rowid, embedding),
                            )
                        except Exception:
                            pass

                # 3. sync_status: old.synced → main.vector_synced
                # [FIX-4a] MEDIUM: UPDATE-only는 대상 행이 없으면 0 rows affected → 동기화 상태 유실.
                # 원인: project_data.db의 sync_status는 에피소드 처리 시에만 행이 생김.
                # 구 vec_memory.db에만 기록된 ep_num은 main DB에 행이 없을 수 있음.
                # 해결: UPSERT (INSERT ... ON CONFLICT DO UPDATE)로 행 부재 시에도 안전.
                old_synced = self.cursor.execute(
                    "SELECT ep_num FROM vec_old.sync_status WHERE synced = 1"
                ).fetchall()
                for (ep_num,) in old_synced:
                    self.cursor.execute(
                        "INSERT INTO sync_status (ep_num, vector_synced, updated_at) VALUES (?, 1, CURRENT_TIMESTAMP) "
                        "ON CONFLICT(ep_num) DO UPDATE SET vector_synced = 1, updated_at = CURRENT_TIMESTAMP",
                        (ep_num,),
                    )

                # 4. anchors: old.value → main.data (충돌 시 기존 유지)
                old_anchors = self.cursor.execute(
                    "SELECT key, value, updated_at FROM vec_old.anchors"
                ).fetchall()
                for key, value, updated_at in old_anchors:
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO anchors (key, data, updated_at) VALUES (?, ?, ?)",
                        (key, value, updated_at),
                    )

                self.conn.commit()
                self.cursor.execute("DETACH DATABASE vec_old")

            # [FIX-3] HIGH: sqlite-vec 미설치 환경에서 vec_episodes를 못 옮긴 채
            # 원본을 .migrated로 치우면 재시도 기회를 잃음.
            # 자아비판: 원래 코드는 _vec_available 여부와 무관하게 무조건 리네임했음.
            # episode_meta/anchors는 이관되지만 vec_episodes(핵심 벡터 데이터)는 누락된 상태.
            # 해결: vec 이관 성공 시에만 .migrated, 미이관 시 .partial_migrated로 보존.
            if self._vec_available:
                vec_path.rename(vec_path.with_suffix(".db.migrated"))
                logging.info("[DB-MERGE] vec_memory.db 마이그레이션 완료 → .db.migrated")
            else:
                vec_path.rename(vec_path.with_suffix(".db.partial_migrated"))
                logging.warning(
                    "[DB-MERGE] sqlite-vec 미설치 — vec_episodes 미이관. "
                    "원본 보존(.partial_migrated). sqlite-vec 설치 후 재시도 가능."
                )

        except Exception as e:
            # [FIX-2] HIGH: 비원자적 마이그레이션 — rollback 없이 DETACH만 수행하면
            # 부분 반영 상태가 남을 수 있음.
            # 자아비판: DETACH는 DDL 계열로 implicit commit을 트리거할 수 있고,
            # 그 경우 INSERT는 됐는데 sync_status UPDATE는 안 된 중간 상태가 DB에 커밋됨.
            # 해결: rollback → DETACH 순서로 부분 반영 원천 차단.
            logging.warning(f"[DB-MERGE] 마이그레이션 실패 (비차단): {e}")
            try:
                self.conn.rollback()
                self.cursor.execute("DETACH DATABASE vec_old")
            except Exception:
                pass
```

### Phase 1 검증

```bash
python -m py_compile modules/core/db_manager.py
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q -x -k "db_manager" --tb=short
```

---

## Phase 2: VecMemory 듀얼모드 생성자

**파일**: `modules/core/vec_memory.py`

### Phase 2-1: import 추가

L7 (`from pathlib import Path`) **직후**에:

```python
from contextlib import contextmanager
```

### Phase 2-2: `__init__` 시그니처 변경

L55-69 전체를 교체:

**Before** (L55-69):
```python
    def __init__(self, db_path, api_key: str = "", *, ui_log=None) -> None:
        self._db_path = str(db_path)
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self._ui_log = ui_log or (lambda msg: print(f"[VecMemory] {msg}"))

        # 상태 플래그
        self.has_valid_memory = False
        self.initialization_error: str | None = None

        # 리소스
        self._conn: sqlite3.Connection | None = None
        self._genai_client = None

        self._init_db()
        self._init_genai()
```

**After**:
```python
    def __init__(self, db_path=None, api_key: str = "", *, ui_log=None, conn=None, lock=None) -> None:
        self._db_path = str(db_path) if db_path else ":shared:"
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self._ui_log = ui_log or (lambda msg: print(f"[VecMemory] {msg}"))

        # 상태 플래그
        self.has_valid_memory = False
        self.initialization_error: str | None = None

        # 리소스
        self._conn: sqlite3.Connection | None = None
        self._genai_client = None

        # [DB-MERGE] 듀얼모드: shared (프로덕션) vs standalone (테스트)
        self._shared_mode = conn is not None
        self._lock = lock  # shared 모드에서만 사용

        if self._shared_mode:
            self._conn = conn
            try:
                conn.execute("SELECT COUNT(*) FROM vec_episodes LIMIT 0")
                self.has_valid_memory = True
            except Exception:
                self.initialization_error = "vec_episodes table not available in shared connection"
                self._ui_log("[VecMemory] shared 모드: vec_episodes 테이블 없음 — 벡터 검색 비활성")
        else:
            self._init_db()

        self._init_genai()
```

### Phase 2-3: `_db_lock()` 컨텍스트 매니저 추가

`_init_genai()` 메서드 (L97-104) **직후**, `_ensure_tables()` (L106) **직전**에 삽입:

```python
    @contextmanager
    def _db_lock(self):
        """[DB-MERGE] shared 모드일 때 DBManager의 RLock 사용."""
        if self._lock:
            with self._lock:
                yield
        else:
            yield
```

### Phase 2-4: `memorize_v20_episode` Lock 래핑 + sync_status 분기

L180-233 전체를 교체:

**Before** (L180-233):
```python
    def memorize_v20_episode(
        self,
        ep_num: int,
        text: str,
        summary: str,
        causal_links,
        arc_no: int | None = None,
        event_types=None,
        entity_names=None,
    ) -> bool:
        """Store one episode into vec DB (LongTermMemory-compatible)."""
        if not self.has_valid_memory:
            self._ui_log(f"[VecMemory] DB not initialized -> skip episode {ep_num}")
            return False

        emb = self._embed_text(text)
        if emb is None:
            self._ui_log(f"[VecMemory] embedding failed -> skip episode {ep_num}")
            return False

        cur = None
        try:
            cur = self._conn.cursor()

            cur.execute("DELETE FROM vec_episodes WHERE rowid = ?", (ep_num,))
            cur.execute(
                "INSERT INTO vec_episodes(rowid, embedding) VALUES (?, ?)",
                (ep_num, _serialize_f32(emb)),
            )

            causal_str = json.dumps(causal_links, ensure_ascii=False)[:2000] if causal_links else ""
            evt_str = ",".join(str(e) for e in event_types)[:500] if event_types else ""
            ent_str = ",".join(str(n) for n in entity_names)[:1000] if entity_names else ""
            cur.execute(
                """INSERT OR REPLACE INTO episode_meta
                   (ep_num, summary, causal_data, arc_no, event_types, entity_names)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (ep_num, summary[:1000], causal_str, arc_no, evt_str, ent_str),
            )

            cur.execute(
                "INSERT OR REPLACE INTO sync_status (ep_num, synced, synced_at) VALUES (?, 1, CURRENT_TIMESTAMP)",
                (ep_num,),
            )

            self._conn.commit()
            return True

        except Exception as e:
            self._ui_log(f"[VecMemory] failed to save episode {ep_num}: {e}")
            return False
        finally:
            if cur is not None:
                cur.close()
```

**After**:
```python
    def memorize_v20_episode(
        self,
        ep_num: int,
        text: str,
        summary: str,
        causal_links,
        arc_no: int | None = None,
        event_types=None,
        entity_names=None,
    ) -> bool:
        """Store one episode into vec DB (LongTermMemory-compatible)."""
        if not self.has_valid_memory:
            self._ui_log(f"[VecMemory] DB not initialized -> skip episode {ep_num}")
            return False

        emb = self._embed_text(text)
        if emb is None:
            self._ui_log(f"[VecMemory] embedding failed -> skip episode {ep_num}")
            return False

        with self._db_lock():
            cur = None
            try:
                cur = self._conn.cursor()

                cur.execute("DELETE FROM vec_episodes WHERE rowid = ?", (ep_num,))
                cur.execute(
                    "INSERT INTO vec_episodes(rowid, embedding) VALUES (?, ?)",
                    (ep_num, _serialize_f32(emb)),
                )

                causal_str = json.dumps(causal_links, ensure_ascii=False)[:2000] if causal_links else ""
                evt_str = ",".join(str(e) for e in event_types)[:500] if event_types else ""
                ent_str = ",".join(str(n) for n in entity_names)[:1000] if entity_names else ""
                cur.execute(
                    """INSERT OR REPLACE INTO episode_meta
                       (ep_num, summary, causal_data, arc_no, event_types, entity_names)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (ep_num, summary[:1000], causal_str, arc_no, evt_str, ent_str),
                )

                # [DB-MERGE] shared 모드: DBManager의 sync_status.vector_synced 사용
                # [FIX-4b] MEDIUM: FIX-4a와 동일 원인 — memorize 시점에 sync_status 행이
                # 아직 없을 수 있음 (에피소드 첫 저장 시). UPSERT로 통일.
                if self._shared_mode:
                    cur.execute(
                        "INSERT INTO sync_status (ep_num, vector_synced, updated_at) VALUES (?, 1, CURRENT_TIMESTAMP) "
                        "ON CONFLICT(ep_num) DO UPDATE SET vector_synced = 1, updated_at = CURRENT_TIMESTAMP",
                        (ep_num,),
                    )
                else:
                    cur.execute(
                        "INSERT OR REPLACE INTO sync_status (ep_num, synced, synced_at) VALUES (?, 1, CURRENT_TIMESTAMP)",
                        (ep_num,),
                    )

                self._conn.commit()
                return True

            except Exception as e:
                self._ui_log(f"[VecMemory] failed to save episode {ep_num}: {e}")
                return False
            finally:
                if cur is not None:
                    cur.close()
```

### Phase 2-5: `retrieve_high_res_context` Lock 래핑

L235-245 (`retrieve_high_res_context`) — `_knn_search` 호출 부분만 Lock으로 감싼다.
실제로는 `_knn_search` 내부에서 DB 접근하므로, `_knn_search` 메서드 자체에 Lock을 건다.

L311-340 (`_knn_search`) 전체를 교체:

**Before** (L311 이후):
```python
    def _knn_search(self, query_emb: list, current_ep: int, n_results: int) -> str:
        """벡터 KNN 검색 후 맥락 블록 문자열 반환."""
        try:
            # current_ep 이전만 필터링하기 위해 넉넉히 검색 후 필터
            fetch_n = n_results + 10
            rows = self._conn.execute(
                """SELECT rowid, distance FROM vec_episodes
                   WHERE embedding MATCH ? ORDER BY distance LIMIT ?""",
                (_serialize_f32(query_emb), fetch_n),
```

`_knn_search` 메서드 본문 전체를 `with self._db_lock():` 으로 감싼다:

**After**:
```python
    def _knn_search(self, query_emb: list, current_ep: int, n_results: int) -> str:
        """벡터 KNN 검색 후 맥락 블록 문자열 반환."""
        with self._db_lock():
            try:
```

그리고 기존 try 블록의 들여쓰기를 4칸 추가 (with 블록 안으로). except/return 도 동일.
`_knn_search`의 마지막 `return ""` 까지 `with` 블록 안에 포함.

### Phase 2-6: `retrieve_multi_query_context` Lock 래핑

L247-309 — DB 접근 루프 (L266-281) 부분을 `with self._db_lock():` 으로 감싼다.

L266-281의 `try:` 블록만 래핑:

**Before** (L266):
```python
            try:
                rows = self._conn.execute(
```

**After**:
```python
            with self._db_lock():
                try:
                    rows = self._conn.execute(
```

그리고 L266-281 블록 전체의 들여쓰기를 4칸 추가.

### Phase 2-7: `save_v20_anchor` shared 모드 분기 + Lock

L370-384 전체를 교체:

**Before**:
```python
    def save_v20_anchor(self, key: str, data) -> bool:
        """JSON 앵커 저장."""
        if not self._conn:
            return False
        try:
            serialized = json.dumps(data, ensure_ascii=False) if isinstance(data, dict | list) else str(data)
            self._conn.execute(
                "INSERT OR REPLACE INTO anchors (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key, serialized),
            )
            self._conn.commit()
            return True
        except Exception as e:
            self._ui_log(f"[VecMemory] 앵커 저장 실패 ({key}): {e}")
            return False
```

**After**:
```python
    def save_v20_anchor(self, key: str, data) -> bool:
        """JSON 앵커 저장."""
        if not self._conn:
            return False
        with self._db_lock():
            try:
                serialized = json.dumps(data, ensure_ascii=False) if isinstance(data, dict | list) else str(data)
                col = "data" if self._shared_mode else "value"
                self._conn.execute(
                    f"INSERT OR REPLACE INTO anchors (key, {col}, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (key, serialized),
                )
                self._conn.commit()
                return True
            except Exception as e:
                self._ui_log(f"[VecMemory] 앵커 저장 실패 ({key}): {e}")
                return False
```

### Phase 2-8: `load_v20_anchor` shared 모드 분기 + Lock

L386-399 전체를 교체:

**Before**:
```python
    def load_v20_anchor(self, key: str):
        """JSON 앵커 로드."""
        if not self._conn:
            return None
        try:
            row = self._conn.execute("SELECT value FROM anchors WHERE key = ?", (key,)).fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    return row[0]
        except Exception as e:
            self._ui_log(f"[VecMemory] 앵커 로드 실패 ({key}): {e}")
        return None
```

**After**:
```python
    def load_v20_anchor(self, key: str):
        """JSON 앵커 로드."""
        if not self._conn:
            return None
        with self._db_lock():
            try:
                col = "data" if self._shared_mode else "value"
                row = self._conn.execute(f"SELECT {col} FROM anchors WHERE key = ?", (key,)).fetchone()
                if row:
                    try:
                        return json.loads(row[0])
                    except (json.JSONDecodeError, TypeError):
                        return row[0]
            except Exception as e:
                self._ui_log(f"[VecMemory] 앵커 로드 실패 ({key}): {e}")
            return None
```

### Phase 2-9: `sync_v20_drafts` sync_status 분기

L403-437 (`sync_v20_drafts`) 중 L422:

**Before** (L422):
```python
                row = self._conn.execute("SELECT synced FROM sync_status WHERE ep_num = ?", (ep_num,)).fetchone()
```

**After**:
```python
                sync_col = "vector_synced" if self._shared_mode else "synced"
                row = self._conn.execute(f"SELECT {sync_col} FROM sync_status WHERE ep_num = ?", (ep_num,)).fetchone()
```

### Phase 2-10: `get_sync_status` shared 모드 분기 + Lock

L439-447 전체를 교체:

**Before**:
```python
    def get_sync_status(self, ep_num: int) -> int:
        """특정 에피소드 동기화 상태 조회. 0=미동기화, 1=완료."""
        if not self._conn:
            return 0
        try:
            row = self._conn.execute("SELECT synced FROM sync_status WHERE ep_num = ?", (ep_num,)).fetchone()
            return row[0] if row else 0
        except Exception:
            return 0
```

**After**:
```python
    def get_sync_status(self, ep_num: int) -> int:
        """특정 에피소드 동기화 상태 조회. 0=미동기화, 1=완료."""
        if not self._conn:
            return 0
        with self._db_lock():
            try:
                col = "vector_synced" if self._shared_mode else "synced"
                row = self._conn.execute(f"SELECT {col} FROM sync_status WHERE ep_num = ?", (ep_num,)).fetchone()
                return row[0] if row else 0
            except Exception:
                return 0
```

### Phase 2-11: `delete_episodes_from` Lock 래핑

L450-470 — 메서드 본문을 `with self._db_lock():` 으로 감싼다:

**Before** (L450):
```python
    def delete_episodes_from(self, target_ep: int) -> int:
        """Delete vectors/meta for episodes >= target_ep and return deleted count."""
        if not self._conn:
            return 0
        cur = None
        try:
```

**After**:
```python
    def delete_episodes_from(self, target_ep: int) -> int:
        """Delete vectors/meta for episodes >= target_ep and return deleted count."""
        if not self._conn:
            return 0
        with self._db_lock():
            cur = None
            try:
```

그리고 L455-470의 try/except/finally 블록 전체 들여쓰기 4칸 추가.

또한 L462의 sync_status 삭제도 분기 처리:

**Before** (L462):
```python
            cur.execute("DELETE FROM sync_status WHERE ep_num >= ?", (target_ep,))
```

**After**:
```python
            if self._shared_mode:
                cur.execute(
                    "UPDATE sync_status SET vector_synced = 0 WHERE ep_num >= ?", (target_ep,)
                )
            else:
                cur.execute("DELETE FROM sync_status WHERE ep_num >= ?", (target_ep,))
```

### Phase 2-12: `get_status` Lock 래핑

L482-498 — DB 접근 부분만 Lock:

L492-497의 `if self._conn:` 블록을 `with self._db_lock():` 으로 감싼다.

### Phase 2-13: `close()` shared 모드 분기

L506-515 전체를 교체:

**Before**:
```python
    def close(self) -> None:
        """연결 종료 및 리소스 정리."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
        self._genai_client = None
        self.has_valid_memory = False
```

**After**:
```python
    def close(self) -> None:
        """연결 종료 및 리소스 정리."""
        if self._shared_mode:
            # [DB-MERGE] 공유 커넥션은 종료하지 않음 (DBManager 소유)
            self._conn = None
        else:
            if self._conn:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None
        self._genai_client = None
        self.has_valid_memory = False
```

### Phase 2 검증

```bash
python -m py_compile modules/core/vec_memory.py
set PYTHONIOENCODING=utf-8 && python -m pytest tests/test_vec_memory.py -q -x --tb=short
```

> 기존 테스트는 모두 standalone 모드 (`:memory:`) → 변경 없이 통과해야 함.

---

## Phase 3: Caller 업데이트

### Phase 3-1: main_a.py VecMemory 생성 변경

**파일**: `main_a.py`

L932-943 전체를 교체:

**Before**:
```python
        # [Phase 4D-2] sqlite-vec 벡터 메모리 초기화 (ChromaDB 대체)
        vec_db_path = self.current_project.paths.memory / "vec_memory.db"
        self.current_project.paths.memory.mkdir(parents=True, exist_ok=True)
        self.memory = VecMemory(
            db_path=vec_db_path,
            api_key=os.getenv("GOOGLE_API_KEY", ""),
            ui_log=self.ui.log,
        )
        if self.memory.is_operational():
            self.ui.log("✅ [VecMemory] sqlite-vec 벡터 엔진 초기화 완료")
        else:
            self.ui.log(f"⚠️ [VecMemory] 벡터 엔진 비활성: {self.memory.initialization_error}")
```

**After**:
```python
        # [DB-MERGE] VecMemory → DBManager 커넥션 공유 (SSOT)
        self.current_project.paths.memory.mkdir(parents=True, exist_ok=True)
        self.memory = VecMemory(
            api_key=os.getenv("GOOGLE_API_KEY", ""),
            ui_log=self.ui.log,
            # [FIX-1] CRITICAL: self.db는 SovereignApp에 없음.
            # 실코드 접근 체인: self.current_project (ProjectContext) → .db (DBManager) → .conn/.._lock
            # self.db 사용 시 AttributeError로 초기화 단계 즉시 크래시.
            conn=self.current_project.db.conn,
            lock=self.current_project.db._lock,
        )
        if self.memory.is_operational():
            self.ui.log("✅ [VecMemory] sqlite-vec 벡터 엔진 초기화 완료 (SSOT)")
        else:
            self.ui.log(f"⚠️ [VecMemory] 벡터 엔진 비활성: {self.memory.initialization_error}")
```

### Phase 3-2: main_a.py `_check_vector_db_lock` 업데이트

**파일**: `main_a.py`

L1136-1155 전체를 교체:

**Before**:
```python
    def _check_vector_db_lock(self, project_name: str) -> bool:
        """[Phase 4D] 벡터 DB 무결성 점검 (sqlite-vec).

        Args:
            project_name: 프로젝트 이름

        Returns:
            bool: 무결성 검증 통과 여부 (True=정상, False=손상 감지)
        """
        memory_path = Path(self._PROJECTS_DIR) / project_name / "memory"

        # 1. sqlite-vec DB 파일 점검
        vec_db = memory_path / "vec_memory.db"
        if vec_db.exists() and vec_db.stat().st_size == 0:
            self.ui.log(f"🚨 [Critical] 벡터 DB 파일({vec_db.name}) 손상 감지 (0KB).")
            self.ui.log("👉 [해결] 파일 삭제 후 Stage 0을 재실행하십시오.")
            return False

        self.ui.log("✅ [System] 벡터 DB 엔진 무결성 점검 완료.")
        return True
```

**After**:
```python
    def _check_vector_db_lock(self, project_name: str) -> bool:
        """[DB-MERGE] 벡터 DB 무결성 점검 (project_data.db 통합).

        Args:
            project_name: 프로젝트 이름

        Returns:
            bool: 무결성 검증 통과 여부 (True=정상, False=손상 감지)
        """
        db_file = Path(self._PROJECTS_DIR) / project_name / "project_data.db"
        if db_file.exists() and db_file.stat().st_size == 0:
            self.ui.log(f"🚨 [Critical] DB 파일({db_file.name}) 손상 감지 (0KB).")
            self.ui.log("👉 [해결] 파일 삭제 후 Stage 0을 재실행하십시오.")
            return False

        self.ui.log("✅ [System] 벡터 DB 엔진 무결성 점검 완료.")
        return True
```

### Phase 3-3: reverse_expander.py 폴백 업데이트

**파일**: `modules/core/stage0/reverse_expander.py`

L414-425 전체를 교체:

**Before**:
```python
        if memory is None:
            try:
                import os

                from modules.core.vec_memory import VecMemory

                vec_db_path = ctx.paths.memory / "vec_memory.db"
                ctx.paths.memory.mkdir(parents=True, exist_ok=True)
                memory = VecMemory(db_path=vec_db_path, api_key=os.getenv("GOOGLE_API_KEY", ""))
            except Exception as e:
                logging.warning(f"[!] VecMemory 초기화 실패: {e}")
                return 0
```

**After**:
```python
        if memory is None:
            try:
                import os

                from modules.core.vec_memory import VecMemory

                # [DB-MERGE] shared 모드 우선 시도
                if hasattr(ctx, "db") and ctx.db and hasattr(ctx.db, "conn") and ctx.db.conn:
                    memory = VecMemory(
                        api_key=os.getenv("GOOGLE_API_KEY", ""),
                        conn=ctx.db.conn,
                        lock=getattr(ctx.db, "_lock", None),
                    )
                else:
                    # standalone 폴백 (레거시 vec_memory.db 경로 유지)
                    # 주의: project_data.db는 sync_status/anchors 스키마가 달라
                    # standalone VecMemory와 직접 호환되지 않음.
                    vec_db_path = ctx.paths.memory / "vec_memory.db"
                    ctx.paths.memory.mkdir(parents=True, exist_ok=True)
                    memory = VecMemory(db_path=vec_db_path, api_key=os.getenv("GOOGLE_API_KEY", ""))
            except Exception as e:
                logging.warning(f"[!] VecMemory 초기화 실패: {e}")
                return 0
```

### Phase 3-4: RESET.py 업데이트

**파일**: `RESET.py`

#### 3-4a: `selective_reset()` — vec_db_path 파라미터 제거

L35 삭제:
```python
    vec_db_path = project_root / "memory" / "vec_memory.db"
```

L49 변경:
**Before**:
```python
            perform_selective_rewind(int(target_ep), db_path, vec_db_path, drafts_path)
```
**After**:
```python
            perform_selective_rewind(int(target_ep), db_path, drafts_path)
```

L53 변경:
**Before**:
```python
            perform_nuclear_reset(db_path, vec_db_path, drafts_path, project_root)
```
**After**:
```python
            perform_nuclear_reset(db_path, drafts_path, project_root)
```

#### 3-4b: `perform_selective_rewind()` — 시그니처 + ep_tables 수정 + vec 블록 교체

> **[FIX-5] MEDIUM — 자아비판**: 원래 오더는 L122-136(vec 블록)만 교체하고 L68-75의
> `ep_tables` 리스트는 건드리지 않았음. 그 결과 `"sync_status"`가 ep_tables에 남아
> `DELETE FROM sync_status WHERE ep_num >= ?`가 먼저 실행된 뒤, 교체된 vec 블록에서
> `UPDATE sync_status SET vector_synced = 0 WHERE ep_num >= ?`를 수행 → 이미 삭제된
> 행에 UPDATE → no-op → vector_synced 리셋 의도가 무효.
>
> **해결**: DB 통합 후 sync_status는 DELETE가 아니라 vector_synced 컬럼만 0으로 리셋해야
> 하므로 ep_tables 리스트에서 제거하고, vec 블록 교체 코드에서 UPDATE로 처리.

L68-75 `ep_tables` 리스트에서 `"sync_status"` 제거:

**Before**:
```python
        ep_tables = [
            "manuscripts",
            "blueprints",
            "state_logs",
            "martial_tracker",
            "sync_status",
            "causal_graph",
        ]
```

**After**:
```python
        # [FIX-5] sync_status는 DB-MERGE 후 DELETE 대신 vector_synced=0 UPDATE로 처리
        ep_tables = [
            "manuscripts",
            "blueprints",
            "state_logs",
            "martial_tracker",
            "causal_graph",
        ]
```

L56 시그니처 변경:
**Before**:
```python
def perform_selective_rewind(target_ep, db_path, vec_db_path, drafts_path):
```
**After**:
```python
def perform_selective_rewind(target_ep, db_path, drafts_path):
```

L122-136 (벡터 DB 기억 소거 블록) 전체를 교체:

**Before** (L122-136):
```python
        # 5. 벡터 DB 기억 소거 (VecMemory — sqlite-vec)
        if vec_db_path.exists():
            try:
                vec_conn = sqlite3.connect(vec_db_path)
                # episode_meta에서 대상 rowid 조회 후 vec_episodes + 메타 삭제
                rows = vec_conn.execute("SELECT ep_num FROM episode_meta WHERE ep_num >= ?", (target_ep,)).fetchall()
                for (ep,) in rows:
                    vec_conn.execute("DELETE FROM vec_episodes WHERE rowid = ?", (ep,))
                vec_conn.execute("DELETE FROM episode_meta WHERE ep_num >= ?", (target_ep,))
                vec_conn.execute("DELETE FROM sync_status WHERE ep_num >= ?", (target_ep,))
                vec_conn.commit()
                vec_conn.close()
                print(f"   🌌 벡터 메모리 소거 완료 ({len(rows)}건)")
            except Exception as vdb_err:
                print(f"   ⚠️ 벡터 DB 소거 건너뜀: {vdb_err}")
```

**After**:
```python
        # 5. [DB-MERGE] 벡터 테이블 기억 소거 (project_data.db 내)
        try:
            rows = cursor.execute(
                "SELECT ep_num FROM episode_meta WHERE ep_num >= ?", (target_ep,)
            ).fetchall()
            for (ep,) in rows:
                cursor.execute("DELETE FROM vec_episodes WHERE rowid = ?", (ep,))
            cursor.execute("DELETE FROM episode_meta WHERE ep_num >= ?", (target_ep,))
            cursor.execute(
                "UPDATE sync_status SET vector_synced = 0 WHERE ep_num >= ?", (target_ep,)
            )
            conn.commit()
            print(f"   벡터 메모리 소거 완료 ({len(rows)}건)")
        except Exception as vdb_err:
            print(f"   벡터 테이블 소거 건너뜀: {vdb_err}")
```

#### 3-4c: `perform_nuclear_reset()` — 시그니처 + vec 삭제 제거

L148 시그니처 변경:
**Before**:
```python
def perform_nuclear_reset(db_path, vec_db_path, drafts_path, project_root):
```
**After**:
```python
def perform_nuclear_reset(db_path, drafts_path, project_root):
```

L155-157 DROP TABLE 루프에 per-table try/except 추가 + L160-163 vec 삭제 블록 삭제:

> **[FIX-6] MEDIUM**: 병합 후 `vec_episodes`(virtual table, vec0 모듈)가 project_data.db에 존재.
> RESET.py는 순수 `sqlite3.connect()`로 연결하므로 sqlite-vec 확장이 로드되지 않음.
> `DROP TABLE` on virtual table without module → `OperationalError: no such module: vec0`.
> per-table try/except가 없어 한 테이블 실패 시 나머지 전부 미삭제 → nuclear_reset 실패.
> 병합 전에는 vec_memory.db를 `os.remove()`로 파일째 삭제해서 문제 없었음.

L155-157 변경:
**Before**:
```python
            for t in tables:
                if t != "sqlite_sequence" and t.isidentifier():
                    cursor.execute(f"DROP TABLE IF EXISTS [{t}]")
```
**After**:
```python
            for t in tables:
                if t != "sqlite_sequence" and t.isidentifier():
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS [{t}]")
                    except Exception:
                        pass  # [FIX-6] virtual table (sqlite-vec 미로드 시 무시)
```

L160-163 (VecMemory DB 삭제 블록) 삭제:
```python
    # VecMemory DB 삭제
    if vec_db_path.exists():
        os.remove(vec_db_path)
        print("   🗑️ vec_memory.db 삭제 완료")
```

### Phase 3 검증

```bash
python -m py_compile main_a.py
python -m py_compile modules/core/stage0/reverse_expander.py
python -m py_compile RESET.py
```

---

## Phase 4: 에러 헬퍼 + 테스트 업데이트

### Phase 4-1: error_helper.py 경로 업데이트

**파일**: `modules/core/error_helper.py`

L154 변경:
**Before**:
```python
        solution="memory/vec_memory.db 파일의 잠금을 해제하거나 프로세스를 재시작하세요",
```
**After**:
```python
        solution="project_data.db 파일의 잠금을 해제하거나 프로세스를 재시작하세요",
```

L161 변경:
**Before**:
```python
        solution="memory/vec_memory.db 파일을 삭제하고 Stage 0을 재실행하세요",
```
**After**:
```python
        solution="project_data.db에서 vec_episodes/episode_meta 테이블을 삭제하고 Stage 0을 재실행하세요",
```

### Phase 4-2: test_edge_cases.py 업데이트

**파일**: `tests/test_edge_cases.py`

L247-253 부근 — `vec_memory.db` 경로 참조를 `project_data.db` 기반으로 변경.

> **주의**: 이 테스트가 `_check_vector_db_lock`을 테스트한다면, Phase 3-2에서 변경한 로직에 맞게 경로를 `project_data.db`로 변경해야 함. 테스트 내용을 읽고 정확히 맞는 assertion으로 수정.

### Phase 4-3: 신규 테스트 `tests/test_db_merge.py`

**파일**: `tests/test_db_merge.py` (신규 생성)

```python
"""[DB-MERGE] DB SSOT 통합 테스트."""

import sqlite3
from unittest.mock import MagicMock

import pytest

from modules.core.db_manager import DBManager
from modules.core.vec_memory import VecMemory

# sqlite-vec 설치 여부 확인
try:
    import sqlite_vec

    _VEC_AVAILABLE = True
except ImportError:
    _VEC_AVAILABLE = False


@pytest.fixture
def tmp_db(tmp_path):
    """임시 DBManager 인스턴스."""
    db_path = tmp_path / "project_data.db"
    db = DBManager(db_path)
    try:
        yield db
    finally:
        db.close()


class TestSharedMode:
    """VecMemory shared 모드 (DBManager 커넥션 공유) 테스트."""

    def test_shared_mode_creation(self, tmp_db):
        """shared 모드 VecMemory 생성."""
        vm = VecMemory(
            api_key="",
            ui_log=MagicMock(),
            conn=tmp_db.conn,
            lock=tmp_db._lock,
        )
        assert vm._shared_mode is True
        assert vm._conn is tmp_db.conn
        assert vm._lock is tmp_db._lock

    @pytest.mark.skipif(not _VEC_AVAILABLE, reason="sqlite-vec not installed")
    def test_shared_mode_operational(self, tmp_db):
        """sqlite-vec 설치 시 shared 모드 operational."""
        vm = VecMemory(
            api_key="",
            ui_log=MagicMock(),
            conn=tmp_db.conn,
            lock=tmp_db._lock,
        )
        assert vm.is_operational() is True

    def test_shared_mode_close_preserves_connection(self, tmp_db):
        """shared 모드 close()가 DBManager 커넥션을 종료하지 않음."""
        vm = VecMemory(
            api_key="",
            ui_log=MagicMock(),
            conn=tmp_db.conn,
            lock=tmp_db._lock,
        )
        vm.close()
        # DBManager 커넥션은 살아있어야 함
        row = tmp_db.conn.execute("SELECT 1").fetchone()
        assert row[0] == 1

    def test_standalone_mode_unchanged(self, tmp_path):
        """standalone 모드 (테스트용)는 기존 동작 유지."""
        vm = VecMemory(db_path=":memory:", api_key="", ui_log=MagicMock())
        assert vm._shared_mode is False
        vm.close()


class TestMigration:
    """기존 vec_memory.db 마이그레이션 테스트."""

    def test_migration_copies_episode_meta(self, tmp_path):
        """마이그레이션이 episode_meta 데이터를 이전함."""
        # 1. 구 형식 vec_memory.db 생성
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        old_db = memory_dir / "vec_memory.db"
        conn = sqlite3.connect(old_db)
        conn.execute("""
            CREATE TABLE episode_meta (
                ep_num INTEGER PRIMARY KEY, summary TEXT,
                causal_data TEXT, arc_no INTEGER,
                event_types TEXT, entity_names TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE sync_status (ep_num INTEGER PRIMARY KEY, synced INTEGER DEFAULT 0, synced_at TIMESTAMP)
        """)
        conn.execute("""
            CREATE TABLE anchors (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        """)
        conn.execute("INSERT INTO episode_meta (ep_num, summary) VALUES (1, 'test summary')")
        conn.execute("INSERT INTO sync_status (ep_num, synced) VALUES (1, 1)")
        conn.execute("INSERT INTO anchors (key, value) VALUES ('test_key', '{}')")
        conn.commit()
        conn.close()

        # 2. DBManager 초기화 → 마이그레이션 자동 실행
        db = DBManager(tmp_path / "project_data.db")

        # 3. episode_meta 이전 확인
        row = db.conn.execute("SELECT summary FROM episode_meta WHERE ep_num = 1").fetchone()
        assert row is not None
        assert row[0] == "test summary"

        # 4. sync_status 이전 확인
        row = db.conn.execute("SELECT vector_synced FROM sync_status WHERE ep_num = 1").fetchone()
        assert row is not None
        assert row[0] == 1

        # 5. anchors 이전 확인
        row = db.conn.execute("SELECT data FROM anchors WHERE key = 'test_key'").fetchone()
        assert row is not None
        assert row[0] == "{}"

        # 6. 원본 리네임 확인
        assert not old_db.exists()
        if _VEC_AVAILABLE:
            assert (memory_dir / "vec_memory.db.migrated").exists()
        else:
            assert (memory_dir / "vec_memory.db.partial_migrated").exists()

        # [FIX-8] 자원 정리
        db.close()

    def test_no_migration_when_no_old_db(self, tmp_path):
        """vec_memory.db가 없으면 마이그레이션 건너뜀 (에러 없음)."""
        db = DBManager(tmp_path / "project_data.db")
        # 에러 없이 정상 초기화
        assert db.conn is not None
        db.close()
```

### Phase 4 검증

```bash
python -m ruff check modules/core/error_helper.py tests/test_db_merge.py tests/test_edge_cases.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/test_db_merge.py -q -x --tb=short
```

---

## Phase 5: 최종 검증

### Phase 5-1: Ruff 전체

```bash
python -m ruff check modules/ main_a.py RESET.py --no-fix
```

### Phase 5-2: 전체 테스트 스위트

```bash
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short
```

### Phase 5-3: CLAUDE.md 업데이트

**파일**: `CLAUDE.md`

L78 변경:
**Before**:
```
- `memory_engine.py` — **삭제됨** (Phase 4D 완료). VecMemory(`vec_memory.py`)가 단일 벡터 경로.
```
**After**:
```
- `memory_engine.py` — **삭제됨** (Phase 4D 완료). VecMemory(`vec_memory.py`)가 DBManager 커넥션을 공유 (DB-MERGE). `project_data.db` 단일 파일 = SSOT.
```

---

## 커밋 전략

| 커밋 | Phase | 메시지 |
|------|-------|--------|
| 1 | 1+2 | `feat(db-merge): DBManager sqlite-vec 로드 + VecMemory 듀얼모드 생성자` |
| 2 | 3 | `refactor(db-merge): caller 배선 — main_a, reverse_expander, RESET` |
| 3 | 4+5 | `test(db-merge): 통합 테스트 + 문서 업데이트` |

---

## 롤백 전략

- 각 커밋 독립 → `git revert` 가능
- 마이그레이션은 원본을 `.db.migrated` 또는 `.db.partial_migrated`로 리네임 (삭제 아님) → 되돌리기 가능
- VecMemory standalone 모드는 절대 삭제하지 않음 → 즉시 롤백 가능
