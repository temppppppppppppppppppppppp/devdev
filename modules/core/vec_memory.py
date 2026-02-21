"""[Phase 4D] sqlite-vec 기반 벡터 메모리 엔진

sqlite-vec 확장으로 KNN 벡터 검색을 수행하며,
메타데이터는 일반 SQLite 테이블에 저장한다.

공개 인터페이스: retrieve_high_res_context, retrieve_multi_query_context,
memorize_v20_episode, sync_v20_drafts, is_operational,
save_v20_anchor, load_v20_anchor, get_status, close,
delete_episodes_from, delete_all_episodes
"""

import json
import logging
import os
import sqlite3
import struct
import time
from contextlib import contextmanager
from pathlib import Path

# ── 임베딩 모델 설정 ────────────────────────────────────────
EMBED_DIM = 768  # gemini-embedding-001 기본 차원
EMBED_MODEL = "gemini-embedding-001"
MAX_EMBED_CHARS = 10000

# ── 선택적 의존성 ────────────────────────────────────────────
try:
    import sqlite_vec

    _VEC_AVAILABLE = True
except ImportError:
    _VEC_AVAILABLE = False

try:
    from google import genai

    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


def _serialize_f32(vec: list) -> bytes:
    """float 리스트 → little-endian float32 BLOB"""
    return struct.pack(f"{len(vec)}f", *vec)


class VecMemory:
    """sqlite-vec 기반 벡터 메모리 엔진.

    Args:
        db_path: DB 파일 경로 (str | Path). ':memory:' 허용.
        api_key: Google API 키 (임베딩용). 없으면 환경변수에서 로드.
        ui_log:  로그 콜백 ``(msg: str) -> None``. 없으면 print 사용.
    """

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

        # [DB-MERGE] 단일모드: shared(프로덕션) vs standalone(테스트)
        self._shared_mode = conn is not None
        self._lock = lock

        if self._shared_mode:
            self._conn = conn
            try:
                conn.execute("SELECT COUNT(*) FROM vec_episodes LIMIT 0")
                self.has_valid_memory = True
            except Exception:
                self.initialization_error = "vec_episodes table not available in shared connection"
                self._ui_log("[VecMemory] shared 모드: vec_episodes 테이블 없음 -> 벡터 검색 비활성")
        else:
            self._init_db()
        self._init_genai()

    # ── 초기화 ──────────────────────────────────────────────

    def _init_db(self) -> None:
        """SQLite 연결 + sqlite-vec 확장 로드 + 테이블 생성"""
        if not _VEC_AVAILABLE:
            self.initialization_error = "sqlite-vec not installed"
            self._ui_log("[VecMemory] sqlite-vec 미설치 — 벡터 검색 비활성")
            return

        try:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.enable_load_extension(True)
            sqlite_vec.load(self._conn)
            self._conn.enable_load_extension(False)
            self._ensure_tables()
            self.has_valid_memory = True
        except Exception as e:
            self.initialization_error = f"DB init failed: {e}"
            self._ui_log(f"[VecMemory] DB 초기화 실패: {e}")
            if self._conn:
                try:
                    self._conn.close()
                except Exception:
                    pass
            self._conn = None

    def _init_genai(self) -> None:
        """Google genai 클라이언트 초기화"""
        if not _GENAI_AVAILABLE or not self._api_key:
            return
        try:
            self._genai_client = genai.Client(api_key=self._api_key)
        except Exception as e:
            logging.warning(f"[VecMemory] genai 클라이언트 초기화 실패: {str(e)[:80]}")

    @contextmanager
    def _db_lock(self):
        """[DB-MERGE] shared 모드에서 DBManager RLock 사용."""
        if self._lock:
            with self._lock:
                yield
        else:
            yield

    def _ensure_tables(self) -> None:
        """Create vec/meta/sync/anchor tables."""
        cur = self._conn.cursor()
        try:
            cur.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_episodes
                USING vec0(embedding float[{EMBED_DIM}])
            """)
            cur.execute("""
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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sync_status (
                    ep_num    INTEGER PRIMARY KEY,
                    synced    INTEGER DEFAULT 0,
                    synced_at TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS anchors (
                    key        TEXT PRIMARY KEY,
                    value      TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._conn.commit()
        finally:
            cur.close()

    def _embed_text(self, text: str) -> list | None:
        """텍스트 → 임베딩 벡터. 실패 시 None."""
        if not self._genai_client or not text:
            return None

        clean = text.replace("\n", " ").strip()
        if not clean:
            return None

        # 서사 샘플링: 앞 4000 + 중간 3000 + 뒤 3000 (LongTermMemory V63.3 호환)
        if len(clean) > MAX_EMBED_CHARS:
            mid = len(clean) // 2 - 1500
            clean = clean[:4000] + " " + clean[mid : mid + 3000] + " " + clean[-3000:]

        max_retries = 3
        for attempt in range(max_retries):
            try:
                res = self._genai_client.models.embed_content(model=EMBED_MODEL, contents=clean)
                val = None
                if hasattr(res, "embeddings") and res.embeddings:
                    val = res.embeddings[0].values
                elif hasattr(res, "embedding") and res.embedding:
                    val = res.embedding.values
                if val is not None:
                    return list(val)
                time.sleep(0.5)
            except Exception as e:
                if any(c in str(e) for c in ("429", "503", "504")) and attempt < max_retries - 1:
                    wait = min(5 * (2**attempt), 60)
                    logging.info(f"[VecMemory] 임베딩 재시도 {attempt + 1}/{max_retries}, {wait}s 대기")
                    time.sleep(wait)
                    continue
                logging.warning(f"[VecMemory] 임베딩 실패: {str(e)[:80]}")
                break
        return None

    # ── 에피소드 저장 ───────────────────────────────────────
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

                # [DB-MERGE] shared 모드: DBManager sync_status.vector_synced 사용
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
                # [Sweep4] 명시적 rollback — SQLite 자동 rollback에 의존하지 않음
                try:
                    self._conn.rollback()
                except Exception:
                    pass
                self._ui_log(f"[VecMemory] failed to save episode {ep_num}: {e}")
                return False
            finally:
                if cur is not None:
                    cur.close()

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

    def retrieve_multi_query_context(
        self,
        queries: list,
        current_ep: int,
        n_per_query: int = 3,
        max_results: int = 5,
    ) -> str:
        """멀티쿼리 벡터 검색 — 다양한 쿼리로 검색 후 merge+dedup (LongTermMemory 호환)."""
        if not self.has_valid_memory:
            return ""

        seen: dict[int, tuple[float, dict]] = {}  # ep_num → (distance, meta)
        for q in queries:
            if not q or not str(q).strip():
                continue
            query_text = json.dumps(q, ensure_ascii=False) if isinstance(q, dict | list) else str(q)
            emb = self._embed_text(query_text)
            if emb is None:
                continue
            try:
                with self._db_lock():
                    rows = self._conn.execute(
                        """SELECT rowid, distance FROM vec_episodes
                           WHERE embedding MATCH ? ORDER BY distance LIMIT ?""",
                        (_serialize_f32(emb), n_per_query),
                    ).fetchall()
                for rowid, dist in rows:
                    if rowid >= current_ep:
                        continue
                    if rowid not in seen or dist < seen[rowid][0]:
                        meta = self._load_episode_meta(rowid)
                        if meta:
                            seen[rowid] = (dist, meta)
            except Exception as e:
                self._ui_log(f"[VecMemory] 멀티쿼리 검색 오류: {str(e)[:50]}")
                continue

        if not seen:
            # [OpusTF-P0-2] 모든 임베딩 실패 시 LIKE 키워드 폴백
            for q in queries:
                if not q or not str(q).strip():
                    continue
                qt = json.dumps(q, ensure_ascii=False) if isinstance(q, dict | list) else str(q)
                fb = self._keyword_fallback_search(qt, current_ep, max_results)
                if fb:
                    return fb
            return ""

        # [OpusTF-P0-1] 거리(유사도) 기반 랭킹 + 연속 에피소드 중복 제거
        max_results = max(1, max_results)
        sorted_by_dist = sorted(seen.items(), key=lambda x: x[1][0])  # distance ASC
        # 다양성 보정: 연속 에피소드(±1) 중 더 먼 것 제거
        selected: list[int] = []
        for ep, (_dist, _meta) in sorted_by_dist:
            if any(abs(ep - s) <= 1 for s in selected):
                continue
            selected.append(ep)
            if len(selected) >= max_results:
                break
        sorted_eps = selected

        blocks = []
        for ep in sorted_eps:
            _, meta = seen[ep]
            summary = meta.get("summary", "")
            evt = meta.get("event_types", "")
            ent = meta.get("entity_names", "")
            header = f"### [제 {ep} 화의 기억]"
            if evt:
                header += f" ({evt})"
            block = f"{header}\n요약: {summary}"
            if evt:
                block += f"\n사건: {evt}"
            if ent:
                block += f"\n인물: {ent}"
            blocks.append(block)

        return "\n\n".join(blocks)

    def _knn_search(self, query_emb: list, current_ep: int, n_results: int) -> str:
        """벡터 KNN 검색 후 맥락 블록 문자열 반환."""
        with self._db_lock():
            try:
                # current_ep 이전만 필터링하기 위해 넉넉히 검색 후 후필터
                fetch_n = n_results + 10
                rows = self._conn.execute(
                    """SELECT rowid, distance FROM vec_episodes
                       WHERE embedding MATCH ? ORDER BY distance LIMIT ?""",
                    (_serialize_f32(query_emb), fetch_n),
                ).fetchall()

                results = [(rowid, dist) for rowid, dist in rows if rowid < current_ep]
                results = results[:n_results]

                if not results:
                    return ""

                blocks = []
                for rowid, _dist in results:
                    meta = self._load_episode_meta(rowid)
                    if not meta:
                        continue
                    summary = meta.get("summary", "요약 정보가 없는 기억입니다.")
                    block = f"### [제 {rowid} 화의 기억]\n요약: {summary}"
                    evt = meta.get("event_types", "")
                    ent = meta.get("entity_names", "")
                    if evt:
                        block += f"\n사건: {evt}"
                    if ent:
                        block += f"\n인물: {ent}"
                    blocks.append(block)

                return "\n\n".join(blocks)

            except Exception as e:
                self._ui_log(f"[VecMemory] KNN 검색 오류: {e}")
                return ""

    def _keyword_fallback_search(self, query_text: str, current_ep: int, n_results: int) -> str:
        """[OpusTF-P0-2] 임베딩 실패 시 episode_meta LIKE 키워드 폴백 검색."""
        # 쿼리에서 핵심 키워드 추출 (2글자 이상 단어)
        import re

        keywords = [w for w in re.split(r"[\s,.\-|/]+", query_text) if len(w) >= 2]
        if not keywords:
            return ""
        # 최대 5개 키워드만 사용
        keywords = keywords[:5]
        try:
            with self._db_lock():
                conditions = " OR ".join(
                    "summary LIKE ? OR event_types LIKE ? OR entity_names LIKE ?" for _ in keywords
                )
                params: list = []
                for kw in keywords:
                    like = f"%{kw}%"
                    params.extend([like, like, like])
                params.append(current_ep)
                rows = self._conn.execute(
                    f"SELECT ep_num, summary, event_types, entity_names FROM episode_meta "
                    f"WHERE ({conditions}) AND ep_num < ? ORDER BY ep_num DESC LIMIT ?",
                    (*params, n_results),
                ).fetchall()
            if not rows:
                return ""
            blocks = []
            for ep_num, summary, evt, ent in rows:
                header = f"### [제 {ep_num} 화의 기억 (키워드)]"
                if evt:
                    header += f" ({evt})"
                block = f"{header}\n요약: {summary or ''}"
                if evt:
                    block += f"\n사건: {evt}"
                if ent:
                    block += f"\n인물: {ent}"
                blocks.append(block)
            return "\n\n".join(blocks)
        except Exception as e:
            self._ui_log(f"[VecMemory] 키워드 폴백 검색 오류: {str(e)[:50]}")
            return ""

    def _load_episode_meta(self, ep_num: int) -> dict | None:
        """에피소드 메타데이터 로드."""
        with self._db_lock():
            try:
                row = self._conn.execute(
                    "SELECT summary, causal_data, arc_no, event_types, entity_names FROM episode_meta WHERE ep_num = ?",
                    (ep_num,),
                ).fetchone()
                if row:
                    return {
                        "summary": row[0] or "",
                        "causal_data": row[1] or "",
                        "arc_no": row[2],
                        "event_types": row[3] or "",
                        "entity_names": row[4] or "",
                    }
            except Exception:
                pass
        return None

    # ── 앵커 저장소 (LongTermMemory 호환) ───────────────────

    def save_v20_anchor(self, key: str, data) -> bool:
        """JSON 앵커 저장."""
        if not self._conn:
            return False
        with self._db_lock():
            try:
                serialized = json.dumps(data, ensure_ascii=False) if isinstance(data, dict | list) else str(data)
                if self._shared_mode:
                    self._conn.execute(
                        "INSERT OR REPLACE INTO anchors (key, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                        (key, serialized),
                    )
                else:
                    self._conn.execute(
                        "INSERT OR REPLACE INTO anchors (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                        (key, serialized),
                    )
                self._conn.commit()
                return True
            except Exception as e:
                self._ui_log(f"[VecMemory] 앵커 저장 실패 ({key}): {e}")
                return False

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

    def sync_v20_drafts(self, force_repair: bool = False, drafts_path: Path | None = None) -> None:
        """원고 파일 → 벡터 DB 동기화 (LongTermMemory 호환)."""
        if not self.has_valid_memory or drafts_path is None:
            return

        if not drafts_path.exists():
            return

        draft_files = sorted(drafts_path.glob("*.txt"))
        chunk_counter = 0
        chunk_size = 5

        for f_path in draft_files:
            if not f_path.name[:4].isdigit():
                continue
            ep_num = int(f_path.name[:4])

            # 동기화 상태 확인
            if not force_repair:
                sync_col = "vector_synced" if self._shared_mode else "synced"
                with self._db_lock():
                    row = self._conn.execute(
                        f"SELECT {sync_col} FROM sync_status WHERE ep_num = ?",
                        (ep_num,),
                    ).fetchone()
                if row and row[0] == 1:
                    continue

            try:
                content = f_path.read_text(encoding="utf-8")
                excerpt = content[:500].replace("\n", " ").strip()
                self.memorize_v20_episode(ep_num, content, f"[동기화] {excerpt}", {})
                chunk_counter += 1
                if chunk_counter >= chunk_size:
                    time.sleep(0.5)
                    chunk_counter = 0
                else:
                    time.sleep(0.1)
            except Exception as e:
                self._ui_log(f"[VecMemory] 동기화 실패 — 제 {ep_num}화: {e}")

    def get_sync_status(self, ep_num: int) -> int:
        """특정 에피소드 동기화 상태 조회. 0=미동기화, 1=완료."""
        if not self._conn:
            return 0
        with self._db_lock():
            try:
                if self._shared_mode:
                    row = self._conn.execute(
                        "SELECT vector_synced FROM sync_status WHERE ep_num = ?",
                        (ep_num,),
                    ).fetchone()
                else:
                    row = self._conn.execute("SELECT synced FROM sync_status WHERE ep_num = ?", (ep_num,)).fetchone()
                return row[0] if row else 0
            except Exception:
                return 0

    # ── 삭제 ────────────────────────────────────────────────
    def delete_episodes_from(self, target_ep: int) -> int:
        """Delete vectors/meta for episodes >= target_ep and return deleted count."""
        if not self._conn:
            return 0
        with self._db_lock():
            cur = None
            try:
                cur = self._conn.cursor()
                rows = cur.execute("SELECT ep_num FROM episode_meta WHERE ep_num >= ?", (target_ep,)).fetchall()
                count = len(rows)
                for (ep,) in rows:
                    cur.execute("DELETE FROM vec_episodes WHERE rowid = ?", (ep,))
                cur.execute("DELETE FROM episode_meta WHERE ep_num >= ?", (target_ep,))
                if self._shared_mode:
                    cur.execute("UPDATE sync_status SET vector_synced = 0 WHERE ep_num >= ?", (target_ep,))
                else:
                    cur.execute("DELETE FROM sync_status WHERE ep_num >= ?", (target_ep,))
                self._conn.commit()
                return count
            except Exception as e:
                self._ui_log(f"[VecMemory] delete episodes failed (>={target_ep}): {e}")
                return 0
            finally:
                if cur is not None:
                    cur.close()

    def delete_all_episodes(self) -> int:
        """모든 에피소드 벡터+메타 삭제. 삭제된 건수 반환."""
        return self.delete_episodes_from(0)

    # ── 상태 조회 ───────────────────────────────────────────

    def is_operational(self) -> bool:
        """벡터 검색 가능 여부."""
        return self.has_valid_memory and self._conn is not None

    def get_status(self) -> dict:
        """메모리 엔진 상태 진단."""
        status = {
            "engine": "sqlite-vec",
            "has_valid_memory": self.has_valid_memory,
            "db_available": self._conn is not None,
            "genai_available": self._genai_client is not None,
            "initialization_error": self.initialization_error,
            "db_path": self._db_path,
        }
        if self._conn:
            with self._db_lock():
                try:
                    row = self._conn.execute("SELECT COUNT(*) FROM episode_meta").fetchone()
                    status["episode_count"] = row[0] if row else 0
                except Exception:
                    status["episode_count"] = "unknown"
        return status

    def ui_log(self, msg: str) -> None:
        """외부 호출용 로그 (LongTermMemory 호환)."""
        self._ui_log(msg)

    # ── 리소스 정리 ─────────────────────────────────────────

    def close(self) -> None:
        """연결 종료 및 리소스 정리."""
        if self._conn:
            try:
                if not self._shared_mode:
                    self._conn.close()
            except Exception:
                pass
            self._conn = None
        self._genai_client = None
        self.has_valid_memory = False

    def __del__(self) -> None:
        self.close()
