"""[Phase 4D] sqlite-vec 기반 벡터 메모리 엔진

sqlite-vec 확장으로 KNN 벡터 검색을 수행하며,
메타데이터는 일반 SQLite 테이블에 저장한다.

공개 인터페이스: retrieve_high_res_context, retrieve_multi_query_context,
memorize_v20_episode, sync_v20_drafts, is_operational,
save_v20_anchor, load_v20_anchor, get_status, close,
delete_episodes_from, delete_all_episodes
"""

import hashlib
import json
import logging
import os
import re
import sqlite3
import struct
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path

# ── 임베딩 모델 설정 ────────────────────────────────────────
EMBED_DIM = 3072  # gemini-embedding-001 기본 차원 (2025-12 이후 3072)
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

        # [INF-I2] 임베딩 결과 LRU 캐시 (MD5 해시 키, 최대 128개)
        self._embed_cache: OrderedDict[str, list] = OrderedDict()
        self._embed_cache_max = 128
        self._embed_cache_lock = threading.Lock()

        # [DB-MERGE] 단일모드: shared(프로덕션) vs standalone(테스트)
        self._shared_mode = conn is not None
        self._lock = lock

        if self._shared_mode:
            self._conn = conn
            try:
                conn.execute("SELECT COUNT(*) FROM vec_episodes LIMIT 0")
                self.has_valid_memory = True
                # shared 모드에서도 메타데이터 테이블 + 차원 마이그레이션 검사
                self._ensure_metadata_and_migrate()
                # [TF8] hybrid 테이블 보장 + 누락된 FTS 행 백필
                self._ensure_hybrid_tables()
            except Exception:
                # [Hybrid-P2] shared 모드에서도 최소 테이블을 자체 부트스트랩 시도
                try:
                    if _VEC_AVAILABLE:
                        conn.enable_load_extension(True)
                        sqlite_vec.load(conn)
                        conn.enable_load_extension(False)
                    self._ensure_tables()
                    self._ensure_hybrid_tables()
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

    def _ensure_metadata_and_migrate(self) -> None:
        """shared 모드: vec_metadata 생성 + 차원 불일치 시 자동 마이그레이션."""
        try:
            cur = self._conn.cursor()
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS vec_metadata (
                        key   TEXT PRIMARY KEY,
                        value TEXT
                    )
                """)
                self._conn.commit()
                self._check_embedding_version(cur)
            finally:
                cur.close()
        except Exception as e:
            logging.warning(f"[VecMemory] shared 모드 메타데이터 초기화 실패 (비차단): {str(e)[:80]}")

    def _ensure_hybrid_tables(self) -> None:
        """shared 모드에서 episode_fts 테이블 및 기존 episode_meta 기반 FTS 백필 보장."""
        try:
            cur = self._conn.cursor()
            try:
                cur.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS episode_fts
                    USING fts5(
                        summary,
                        event_types,
                        entity_names,
                        tokenize='unicode61 remove_diacritics 2'
                    )
                """)
                cur.execute("""
                    INSERT OR IGNORE INTO episode_fts(rowid, summary, event_types, entity_names)
                    SELECT ep_num, IFNULL(summary, ''), IFNULL(event_types, ''), IFNULL(entity_names, '')
                    FROM episode_meta
                """)
                self._conn.commit()
            finally:
                cur.close()
        except Exception as e:
            logging.warning(f"[VecMemory] hybrid 테이블 보장 실패 (비차단): {str(e)[:80]}")

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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS anchors (
                    key        TEXT PRIMARY KEY,
                    value      TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # [B6] 임베딩 모델 버전 추적
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vec_metadata (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            self._conn.commit()
            # [B6] 모델 버전 저장 및 불일치 검증
            self._check_embedding_version(cur)
        finally:
            cur.close()

    def _check_embedding_version(self, cur) -> None:
        """[B6] 임베딩 모델 버전 저장 + 테이블 차원 실측 검증 + 자동 마이그레이션."""
        try:
            # 실제 테이블 차원 검증 (메타데이터와 무관하게 항상 확인)
            if self._table_needs_migration():
                logging.warning(
                    f"[VecMemory] vec_episodes 차원 불일치 감지 (현재={EMBED_DIM}) — 자동 마이그레이션 시작"
                )
                self._migrate_vec_table(cur)
                return

            # 모델 불일치 경고 (차원은 OK지만 모델명이 다를 때)
            row = cur.execute("SELECT value FROM vec_metadata WHERE key = 'embed_model'").fetchone()
            if row:
                if row[0] != EMBED_MODEL:
                    logging.warning(f"[VecMemory] 임베딩 모델 불일치: DB={row[0]}, 현재={EMBED_MODEL} — 재색인 권장")

            # 메타데이터 갱신
            cur.execute(
                "INSERT OR REPLACE INTO vec_metadata (key, value) VALUES (?, ?)",
                ("embed_model", EMBED_MODEL),
            )
            cur.execute(
                "INSERT OR REPLACE INTO vec_metadata (key, value) VALUES (?, ?)",
                ("embed_dim", str(EMBED_DIM)),
            )
            self._conn.commit()
        except Exception as e:
            logging.warning(f"[VecMemory] 임베딩 버전 체크 실패 (비차단): {str(e)[:60]}")

    def _table_needs_migration(self) -> bool:
        """vec_episodes 테이블의 실제 차원이 EMBED_DIM과 다른지 테스트 인서트로 확인."""
        try:
            test_vec = [0.0] * EMBED_DIM
            self._conn.execute(
                "INSERT INTO vec_episodes(rowid, embedding) VALUES (?, ?)",
                (-999999, _serialize_f32(test_vec)),
            )
            self._conn.execute("DELETE FROM vec_episodes WHERE rowid = -999999")
            self._conn.commit()
            return False  # 차원 일치
        except Exception:
            self._conn.rollback()
            return True  # 차원 불일치

    def _migrate_vec_table(self, cur) -> None:
        """차원 불일치 시 vec_episodes 재생성 + 메타데이터 갱신."""
        try:
            cur.execute("DROP TABLE IF EXISTS vec_episodes")
            cur.execute(f"""
                CREATE VIRTUAL TABLE vec_episodes
                USING vec0(embedding float[{EMBED_DIM}])
            """)
            # sync_status 리셋 — shared/standalone 스키마 모두 지원
            try:
                cur.execute("UPDATE sync_status SET synced = 0, synced_at = NULL")
            except Exception:
                cur.execute("UPDATE sync_status SET vector_synced = 0, updated_at = CURRENT_TIMESTAMP")
            # 메타데이터 갱신
            cur.execute(
                "INSERT OR REPLACE INTO vec_metadata (key, value) VALUES (?, ?)",
                ("embed_model", EMBED_MODEL),
            )
            cur.execute(
                "INSERT OR REPLACE INTO vec_metadata (key, value) VALUES (?, ?)",
                ("embed_dim", str(EMBED_DIM)),
            )
            self._conn.commit()
            logging.warning(
                f"[VecMemory] vec_episodes 재생성 완료 (dim={EMBED_DIM}). 기존 벡터 삭제됨 — 새 에피소드부터 자동 색인."
            )
        except Exception as e:
            logging.warning(f"[VecMemory] 마이그레이션 실패 (비차단): {str(e)[:80]}")

    def _embed_cache_key(self, text: str) -> str:
        """[INF-I2] 텍스트 → MD5 해시 캐시 키."""
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _embed_cache_get(self, key: str) -> list | None:
        """[INF-I2] 캐시에서 임베딩 벡터 조회 (LRU 순서 갱신)."""
        with self._embed_cache_lock:
            if key in self._embed_cache:
                self._embed_cache.move_to_end(key)
                return self._embed_cache[key]
        return None

    def _embed_cache_put(self, key: str, vec: list) -> None:
        """[INF-I2] 캐시에 임베딩 벡터 저장 (최대 128개, LRU 퇴출)."""
        with self._embed_cache_lock:
            if key in self._embed_cache:
                self._embed_cache.move_to_end(key)
            else:
                self._embed_cache[key] = vec
                while len(self._embed_cache) > self._embed_cache_max:
                    self._embed_cache.popitem(last=False)

    def _embed_text(self, text: str) -> list | None:
        """텍스트 → 임베딩 벡터. 실패 시 None. [INF-I2] LRU 캐시 적용."""
        if not self._genai_client or not text:
            return None

        clean = text.replace("\n", " ").strip()
        if not clean:
            return None

        # 서사 샘플링: 앞 4000 + 중간 3000 + 뒤 3000 (LongTermMemory V63.3 호환)
        if len(clean) > MAX_EMBED_CHARS:
            mid = len(clean) // 2 - 1500
            clean = clean[:4000] + " " + clean[mid : mid + 3000] + " " + clean[-3000:]

        # [INF-I2] 캐시 조회 — 동일 텍스트 재임베딩 방지
        cache_key = self._embed_cache_key(clean)
        cached = self._embed_cache_get(cache_key)
        if cached is not None:
            return cached

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
                    result = list(val)
                    # [INF-I2] 성공한 임베딩 결과 캐시 저장
                    self._embed_cache_put(cache_key, result)
                    return result
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
                # [Hybrid-P2] FTS 동기화
                cur.execute("DELETE FROM episode_fts WHERE rowid = ?", (ep_num,))
                cur.execute(
                    "INSERT INTO episode_fts(rowid, summary, event_types, entity_names) VALUES (?,?,?,?)",
                    (ep_num, summary or "", evt_str or "", ent_str or ""),
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
            result = self._keyword_fallback_search(query_text, current_ep, n_results)
            # [D2] fallback 경로 계측
            logging.debug(
                "[VecMem] path=fallback ep<%d q=%r hits=0 fallback=true selected=[] chars=%d",
                current_ep,
                query_text[:30],
                len(result),
            )
            return result

        result = self._knn_search(emb, current_ep, n_results)
        # [D2] dense 경로 계측
        logging.debug(
            "[VecMem] path=dense ep<%d q=%r fallback=false chars=%d",
            current_ep,
            query_text[:30],
            len(result),
        )
        return result

    def retrieve_multi_query_context(
        self,
        queries: list,
        current_ep: int,
        n_per_query: int = 3,
        max_results: int = 5,
        current_arc_no: int | None = None,
    ) -> str:
        """멀티쿼리 벡터 검색 — 다양한 쿼리로 검색 후 merge+dedup (LongTermMemory 호환).

        [INF-P1-5] Thread-safety note:
        이 메서드 내부에서 ``_db_lock()``으로 KNN 쿼리를 보호한 뒤
        ``_load_episode_meta()``를 호출하는데, ``_load_episode_meta``도
        ``_db_lock()``을 사용합니다. shared 모드에서 ``self._lock``은
        **DBManager의 RLock** 이므로 동일 스레드 내 재진입이 안전합니다.
        standalone 모드에서는 ``self._lock``이 None이므로 no-op입니다.
        이 패턴을 변경할 경우 Lock → RLock 요구사항을 반드시 유지하세요.
        """
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
                    # [D2] multi_dense fallback 계측
                    logging.debug(
                        "[VecMem] path=fallback ep<%d q=%r hits=0 fallback=true selected=[] chars=%d",
                        current_ep,
                        qt[:30],
                        len(fb),
                    )
                    return fb
            return ""

        # [OpusTF-P0-1] 거리(유사도) 기반 랭킹 + 연속 에피소드 중복 제거
        max_results = max(1, max_results)

        # [B3] 같은 Arc 에피소드에 distance 보너스 (×0.9 = 10% 우대)
        def _arc_adjusted_dist(item):
            ep, (dist, meta) = item
            if current_arc_no and meta.get("arc_no") == current_arc_no:
                return dist * 0.9
            return dist

        sorted_by_dist = sorted(seen.items(), key=_arc_adjusted_dist)  # distance ASC + arc bonus
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
            _dist, meta = seen[ep]
            summary = meta.get("summary", "")
            evt = meta.get("event_types", "")
            ent = meta.get("entity_names", "")
            # [B5] 유사도 점수 노출
            _sim_label = f" 유사도:{1.0 - _dist:.2f}" if _dist < 1.0 else ""
            header = f"### [제 {ep} 화의 기억{_sim_label}]"
            if evt:
                header += f" ({evt})"
            block = f"{header}\n요약: {summary}"
            if evt:
                block += f"\n사건: {evt}"
            if ent:
                block += f"\n인물: {ent}"
            blocks.append(block)

        # [D2] multi_dense 정상 경로 계측
        _d2_result = "\n\n".join(blocks)
        _d2_selected = sorted(seen.keys())[:max_results]
        logging.debug(
            "[VecMem] path=multi_dense ep<%d q_count=%d hits=%d fallback=false selected=%s chars=%d",
            current_ep,
            len(queries),
            len(seen),
            _d2_selected,
            len(_d2_result),
        )
        return _d2_result

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
        # [D2] hybrid 경로 계측 (포맷 통일)
        _d2_selected = [ep for _, ep, _ in top]
        logging.debug(
            "[VecMem] path=hybrid ep<%d q=%r hits=%d fallback=false selected=%s chars=pending top_score=%.4f",
            current_ep,
            query_text[:30],
            len(dense_results) + len(sparse_results),
            _d2_selected,
            scored[0][0] if scored else 0.0,
        )

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

        # [D2] hybrid 결과 길이 계측
        _d2_result = "\n\n".join(blocks)
        logging.debug(
            "[VecMem] path=hybrid ep<%d chars=%d",
            current_ep,
            len(_d2_result),
        )
        return _d2_result

    def retrieve_npc_context(self, npc_names: list[str], current_ep: int, max_results: int = 5) -> str:
        """
        Retrieve NPC-focused context by combining:
        - episode_meta.entity_names token matching
        - vector similarity search with NPC-aware queries
        """
        if not self.has_valid_memory:
            return ""

        cleaned_names: list[str] = []
        for name in npc_names or []:
            text = str(name).strip()
            if text and text not in cleaned_names:
                cleaned_names.append(text)
        if not cleaned_names:
            return ""

        safe_max = max(1, int(max_results))
        core_cap = 5
        core_names = cleaned_names[:core_cap]
        overflow_names = cleaned_names[core_cap:]
        candidates: dict[int, dict] = {}

        # 1) Direct entity token match from comma-separated entity_names.
        try:
            with self._db_lock():
                like_conditions = " OR ".join(
                    "((',' || REPLACE(IFNULL(entity_names, ''), ' ', '') || ',') LIKE ? ESCAPE '\\')"
                    for _ in core_names
                )

                def _escape_like(s: str) -> str:
                    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

                like_params = [f"%,{_escape_like(name.replace(' ', ''))},%" for name in core_names]
                rows = self._conn.execute(
                    f"""SELECT ep_num, summary, arc_no, event_types, entity_names
                        FROM episode_meta
                        WHERE ep_num < ? AND ({like_conditions})
                        ORDER BY ep_num DESC
                        LIMIT ?""",
                    (current_ep, *like_params, safe_max * 3),
                ).fetchall()

            for ep_num, summary, arc_no, event_types, entity_names in rows:
                candidates[int(ep_num)] = {
                    "dist": float("inf"),
                    "meta": {
                        "summary": summary or "",
                        "arc_no": arc_no,
                        "event_types": event_types or "",
                        "entity_names": entity_names or "",
                    },
                    "entity_hit": True,
                    "vector_hit": False,
                }
        except Exception as e:
            self._ui_log(f"[VecMemory] NPC entity match search failed: {str(e)[:60]}")

        # 2) Vector search with bounded query plan.
        # Max query count: core(<=5) + core aggregate(1) + overflow aggregate(1) = <=7.
        vector_queries = [f"{name} 과거 행적 상태 변화 관계 사건" for name in core_names]
        if len(core_names) > 1:
            vector_queries.append(f"{' '.join(core_names)} 과거 관계 사건 연속성")
        if overflow_names:
            overflow_phrase = " ".join(overflow_names[:20])
            vector_queries.append(f"{overflow_phrase} 외 등장 NPC 과거 관계 사건 연속성")

        for query_text in vector_queries:
            emb = self._embed_text(query_text)
            if emb is None:
                continue

            try:
                with self._db_lock():
                    rows = self._conn.execute(
                        """SELECT rowid, distance FROM vec_episodes
                           WHERE embedding MATCH ? ORDER BY distance LIMIT ?""",
                        (_serialize_f32(emb), max(6, safe_max * 2)),
                    ).fetchall()

                for rowid, dist in rows:
                    ep_num = int(rowid)
                    if ep_num >= current_ep:
                        continue
                    meta = self._load_episode_meta(ep_num)
                    if not meta:
                        continue

                    entry = candidates.get(ep_num)
                    if entry is None:
                        candidates[ep_num] = {
                            "dist": float(dist),
                            "meta": meta,
                            "entity_hit": False,
                            "vector_hit": True,
                        }
                    else:
                        entry["vector_hit"] = True
                        if float(dist) < float(entry["dist"]):
                            entry["dist"] = float(dist)
            except Exception as e:
                self._ui_log(f"[VecMemory] NPC vector search failed: {str(e)[:60]}")

        if not candidates:
            _fallback_query = " ".join(cleaned_names)
            _fallback_result = self._keyword_fallback_search(_fallback_query, current_ep, safe_max)
            logging.debug(
                "[VecMem] path=npc ep<%d q=%r hits=0 fallback=true selected=[] chars=%d",
                current_ep,
                _fallback_query[:30],
                len(_fallback_result),
            )
            return _fallback_result

        def _sort_key(item):
            ep_num, info = item
            both_hit = info["entity_hit"] and info["vector_hit"]
            if both_hit:
                source_rank = 0
            elif info["entity_hit"]:
                source_rank = 1
            else:
                source_rank = 2
            dist = info["dist"] if info["dist"] != float("inf") else 9.0
            return (source_rank, dist, -ep_num)

        selected = sorted(candidates.items(), key=_sort_key)[:safe_max]

        blocks: list[str] = []
        for ep_num, info in selected:
            meta = info["meta"]
            summary = meta.get("summary", "")
            evt = meta.get("event_types", "")
            ent = meta.get("entity_names", "")

            sim_label = ""
            if info["vector_hit"] and float(info["dist"]) < 1.0:
                sim_label = f" similarity {1.0 - float(info['dist']):.2f}"

            tags = []
            if info["entity_hit"]:
                tags.append("entity")
            if info["vector_hit"]:
                tags.append("vector")
            tag_label = f" ({'/'.join(tags)})" if tags else ""

            header = f"### [EP{ep_num} NPC context{sim_label}]{tag_label}"
            block = f"{header}\nsummary: {summary}"
            if evt:
                block += f"\nevents: {evt}"
            if ent:
                block += f"\nentities: {ent}"
            blocks.append(block)

        _d2_selected = [ep_num for ep_num, _ in selected]
        _d2_result = "\n\n".join(blocks)
        logging.debug(
            "[VecMem] path=npc ep<%d q=%r hits=%d fallback=false selected=%s chars=%d",
            current_ep,
            " ".join(cleaned_names)[:30],
            len(candidates),
            _d2_selected,
            len(_d2_result),
        )
        return _d2_result

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
        for ep_num, distance, summary, event_types, entity_names, arc_no in rows:
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
            })
        results.sort(key=lambda item: float(item["distance"]))
        for rank, item in enumerate(results):
            item["dense_rank"] = rank
        return results

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
                    # [B5] 유사도 점수 노출 (distance 낮을수록 유사)
                    _sim_label = f" (유사도: {1.0 - _dist:.2f})" if _dist < 1.0 else ""
                    block = f"### [제 {rowid} 화의 기억{_sim_label}]\n요약: {summary}"
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
        # [D2] keyword fallback 진입 계측
        logging.debug(
            "[VecMem] path=fallback_entry ep<%d q=%r n=%d",
            current_ep,
            query_text[:30],
            n_results,
        )
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

    def _fts_search(self, query: str, current_ep: int, n_results: int = 10) -> list[dict]:
        """[Hybrid-P2] FTS5 전문 검색. 결과를 dict 리스트로 반환.

        Returns:
            list of {"ep_num": int, "summary": str, "event_types": str,
                     "entity_names": str, "fts_rank": int}
        """
        keywords = [
            w.replace('"', "").replace("'", "").strip()
            for w in re.split(r"[\s,.\-|/]+", query)
            if len(w) >= 2
        ]
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
                cur.execute("DELETE FROM episode_fts WHERE rowid >= ?", (target_ep,))
                if self._shared_mode:
                    cur.execute("UPDATE sync_status SET vector_synced = 0 WHERE ep_num >= ?", (target_ep,))
                else:
                    cur.execute("DELETE FROM sync_status WHERE ep_num >= ?", (target_ep,))
                self._conn.commit()
                return count
            except Exception as e:
                try:
                    self._conn.rollback()
                except Exception:
                    pass
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
