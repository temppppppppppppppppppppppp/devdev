import json
import logging
import sqlite3
import threading
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .constants import MARTIAL_METRICS  # 👈 상수 임포트
from .db_bootstrap_runtime import DBBootstrapRuntime
from .quality_signal_metrics import build_signal_stat


# [V44] DB 에러 심각도 분류
class DBErrorSeverity:
    CRITICAL = "CRITICAL"  # 데이터 손실 위험
    HIGH = "HIGH"  # 작업 실패, 복구 가능
    WARN = "WARN"  # 경고, 계속 진행 가능


# [V44] 커스텀 DB 예외 클래스
class DBError(Exception):
    """DB 작업 중 발생하는 기본 예외"""

    def __init__(self, message, severity=DBErrorSeverity.HIGH, original_error=None) -> None:
        super().__init__(message)
        self.severity = severity
        self.original_error = original_error


class DBIntegrityError(DBError):
    """데이터 무결성 오류 (제약조건 위반 등)"""

    pass


class DBConnectionError(DBError):
    """DB 연결 오류"""

    pass


class DBTransactionError(DBError):
    """트랜잭션 관련 오류"""

    pass


class DBManager:
    """[V20 Sovereign DB Engine] S등급 무결성: 트랜잭션 보호 및 로어 테이블화 완비

    [INF-P1-1] Thread-safety note:
    ``self.cursor`` is retained for backward compatibility but should NOT be used
    in new/modified code. Instead, create a **local cursor** via
    ``cur = self.conn.cursor()`` inside each method, always within ``with self._lock:``.
    This avoids shared-cursor race conditions across threads.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None  # [INF-P1-1] legacy — prefer local cursors in methods
        self.bootstrap_runtime = DBBootstrapRuntime(self)
        # [V45] 멀티스레드 안전성을 위한 Lock
        self._lock = threading.RLock()
        self._accept_runtime_telemetry_writes = True
        # [V64 P2-7] 누적 Bible 증분 캐시 {up_to_ep: cumulative_dict}
        self._cumulative_bible_cache: dict = {}
        self._boot_db()

    def _ensure_open(self) -> None:
        """[INF-P1-7] close() 후 사용 시 명확한 에러 발생"""
        if self.conn is None:
            raise DBConnectionError(
                "DB 연결이 이미 종료되었습니다. close() 호출 후 재사용 불가.",
                severity=DBErrorSeverity.CRITICAL,
            )

    @staticmethod
    def _safe_json_loads(raw, fallback: str):
        """[Sweep4] 비정상 JSON 데이터 방어 — 1행 파손이 전체 조회를 크래시하지 않도록"""
        try:
            return json.loads(raw or fallback)
        except (json.JSONDecodeError, TypeError, ValueError):
            return json.loads(fallback)

    @staticmethod
    def _normalize_ui_event_stage(stage: int | str | None) -> tuple[int | None, str | None]:
        if stage is None:
            return None, None
        if isinstance(stage, str):
            label = stage.strip()
            if not label:
                return None, None
            if label.lstrip("-").isdigit():
                return int(label), None
            lowered = label.lower()
            if lowered == "shutdown":
                return None, label
            if lowered.startswith("stage") and lowered[5:].isdigit():
                return int(lowered[5:]), label
            return None, label
        return int(stage), None

    @staticmethod
    def _merge_ui_event_stage_label(meta: dict | None, stage_label: str | None) -> dict | None:
        if stage_label is None:
            return meta
        if meta is None:
            merged: dict[str, object] = {}
        elif isinstance(meta, dict):
            merged = dict(meta)
        else:
            return meta
        merged.setdefault("stage_label", stage_label)
        return merged

    @staticmethod
    def _column_def_pairs(*pairs: tuple[str, str]) -> tuple[tuple[str, str], ...]:
        return tuple((str(name), str(definition)) for name, definition in pairs)

    def _get_table_columns(self, table_name: str) -> set[str]:
        self.cursor.execute(f"PRAGMA table_info({table_name})")  # noqa: S608
        return {str(row["name"]) for row in self.cursor.fetchall()}

    def _ensure_columns_exist(
        self,
        table_name: str,
        column_defs: tuple[tuple[str, str], ...],
        *,
        log_label: str,
    ) -> list[str]:
        existing_columns = self._get_table_columns(table_name)
        missing_columns = [(name, definition) for name, definition in column_defs if name not in existing_columns]
        if not missing_columns:
            return []

        added_columns: list[str] = []
        failure: Exception | None = None
        for column_name, column_definition in missing_columns:
            try:
                self.cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")  # noqa: S608
                self.conn.commit()
                added_columns.append(column_name)
            except Exception as exc:
                failure = exc
                try:
                    self.conn.rollback()
                except Exception:
                    pass
                break

        if added_columns:
            logging.info("[DBManager] %s compatibility migration added columns: %s", log_label, ", ".join(added_columns))
        if failure is not None:
            remaining_columns = [name for name, _ in missing_columns[len(added_columns) :]]
            logging.warning(
                "[DBManager] %s compatibility migration failed after %s: %s",
                log_label,
                ", ".join(added_columns + remaining_columns),
                failure,
            )
        return added_columns

    @staticmethod
    def _is_db_corruption_error(exc: Exception) -> bool:
        """SQLite 손상 계열 에러 판별."""
        text = str(exc).lower()
        return any(
            marker in text
            for marker in (
                "database disk image is malformed",
                "malformed",
                "file is not a database",
                "database corruption",
                "not a database",
            )
        )

    def _quarantine_corrupt_db(self, reason: str = "") -> Path | None:
        """손상 DB를 .corrupt_* 파일로 격리."""
        source = Path(self.db_path)
        if not source.exists():
            return None

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        target = source.with_name(f"{source.name}.corrupt_{timestamp}")
        try:
            source.rename(target)
            if reason:
                logging.warning("[DBManager] 손상 DB 격리: %s (reason=%s)", target, reason)
            else:
                logging.warning("[DBManager] 손상 DB 격리: %s", target)
            return target
        except Exception as e:
            logging.warning("[DBManager] 손상 DB 격리 실패: %s", e)
            return None

    def _connect_with_integrity_recovery(self) -> sqlite3.Connection:
        """DB 연결 + PRAGMA integrity_check + 자동 복구."""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row

        try:
            cur = conn.cursor()
            row = cur.execute("PRAGMA integrity_check").fetchone()
            status = str(row[0]).strip().lower() if row and len(row) > 0 else "unknown"
            if status != "ok":
                conn.close()
                self._quarantine_corrupt_db(status)
                conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
                conn.row_factory = sqlite3.Row
                logging.warning("[DBManager] integrity_check 실패로 신규 DB 재생성")
        except sqlite3.DatabaseError as e:
            conn.close()
            if self._is_db_corruption_error(e):
                self._quarantine_corrupt_db(str(e))
                conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
                conn.row_factory = sqlite3.Row
                logging.warning("[DBManager] 손상 감지로 DB 재생성")
            else:
                raise

        return conn

    def _boot_db(self) -> None:
        """DB 연결 및 10대 핵심 테이블 초기화"""
        if not hasattr(self, "bootstrap_runtime") or self.bootstrap_runtime is None:
            self.bootstrap_runtime = DBBootstrapRuntime(self)
        self.bootstrap_runtime.boot()
        self._migrate_vec_memory_db()
        self._migrate_world_state_timeline_if_needed()

    # --- [트랜잭션 제어] ---
    def _migrate_vec_memory_db(self) -> None:
        """[DB-MERGE] 기존 memory/vec_memory.db -> project_data.db 1회성 마이그레이션."""
        vec_path = Path(self.db_path).parent / "memory" / "vec_memory.db"
        partial_path = vec_path.with_suffix(".db.partial_migrated")

        # [FIX-9] sqlite-vec 설치 후 partial 파일 자동 복구
        if not vec_path.exists() and partial_path.exists() and self._vec_available:
            partial_path.rename(vec_path)

        if not vec_path.exists():
            return

        attached = False
        cur = None
        try:
            with self._lock:
                cur = self.conn.cursor()
                cur.execute("ATTACH DATABASE ? AS vec_old", (str(vec_path),))
                attached = True

                def _old_table_exists(table_name: str) -> bool:
                    row = cur.execute(
                        "SELECT 1 FROM vec_old.sqlite_master WHERE type='table' AND name=?",
                        (table_name,),
                    ).fetchone()
                    return row is not None

                # 1) episode_meta
                if _old_table_exists("episode_meta"):
                    cur.execute("""
                        INSERT OR IGNORE INTO episode_meta
                        SELECT * FROM vec_old.episode_meta
                    """)

                # 1-b) episode_fts (존재 시 직접 이관, 없으면 episode_meta 기반 백필)
                if _old_table_exists("episode_fts"):
                    old_fts_rows = cur.execute(
                        "SELECT rowid, summary, event_types, entity_names FROM vec_old.episode_fts"
                    ).fetchall()
                    _fts_fail_count = 0
                    for rowid, summary, event_types, entity_names in old_fts_rows:
                        try:
                            cur.execute(
                                "INSERT OR REPLACE INTO episode_fts(rowid, summary, event_types, entity_names) "
                                "VALUES (?, ?, ?, ?)",
                                (
                                    rowid,
                                    summary or "",
                                    event_types or "",
                                    entity_names or "",
                                ),
                            )
                        except Exception as _fts_row_err:
                            _fts_fail_count += 1
                            if _fts_fail_count <= 3:
                                logging.warning("[B4-P1-6] episode_fts 행 이관 실패 (rowid=%s): %s", rowid, _fts_row_err
                                )
                    if _fts_fail_count:
                        logging.warning("[B4-P1-6] episode_fts 이관 중 %d행 실패", _fts_fail_count)
                elif _old_table_exists("episode_meta"):
                    cur.execute("""
                        INSERT OR IGNORE INTO episode_fts(rowid, summary, event_types, entity_names)
                        SELECT ep_num, IFNULL(summary, ''), IFNULL(event_types, ''), IFNULL(entity_names, '')
                        FROM episode_meta
                    """)

                # 2) vec_episodes (sqlite-vec 사용 가능할 때만)
                if self._vec_available and _old_table_exists("vec_episodes"):
                    rows = cur.execute("SELECT rowid, embedding FROM vec_old.vec_episodes").fetchall()
                    _vec_fail_count = 0
                    for rowid, embedding in rows:
                        try:
                            cur.execute(
                                "INSERT OR REPLACE INTO vec_episodes(rowid, embedding) VALUES (?, ?)",
                                (rowid, embedding),
                            )
                        except Exception as _vec_row_err:
                            _vec_fail_count += 1
                            if _vec_fail_count <= 3:
                                logging.warning("[B4-P1-6] vec_episodes 행 이관 실패 (rowid=%s): %s", rowid, _vec_row_err
                                )
                    if _vec_fail_count:
                        logging.warning("[B4-P1-6] vec_episodes 이관 중 %d행 실패", _vec_fail_count)

                # 3) sync_status: old.synced -> main.vector_synced (UPSERT)
                if _old_table_exists("sync_status"):
                    old_synced = cur.execute("SELECT ep_num FROM vec_old.sync_status WHERE synced = 1").fetchall()
                    for (ep_num,) in old_synced:
                        cur.execute(
                            "INSERT INTO sync_status (ep_num, vector_synced, updated_at) VALUES (?, 1, CURRENT_TIMESTAMP) "
                            "ON CONFLICT(ep_num) DO UPDATE SET vector_synced = 1, updated_at = CURRENT_TIMESTAMP",
                            (ep_num,),
                        )

                # 4) anchors: old.value -> main.data (충돌 시 기존 유지)
                if _old_table_exists("anchors"):
                    old_anchors = cur.execute("SELECT key, value, updated_at FROM vec_old.anchors").fetchall()
                    for key, value, updated_at in old_anchors:
                        cur.execute(
                            "INSERT OR IGNORE INTO anchors (key, data, updated_at) VALUES (?, ?, ?)",
                            (key, value, updated_at),
                        )

                self.conn.commit()
                cur.execute("DETACH DATABASE vec_old")
                attached = False

            if self._vec_available:
                vec_path.rename(vec_path.with_suffix(".db.migrated"))
                logging.info("[DB-MERGE] vec_memory.db 마이그레이션 완료 -> .db.migrated")
            else:
                vec_path.rename(vec_path.with_suffix(".db.partial_migrated"))
                logging.warning("[DB-MERGE] sqlite-vec 미설치로 vec_episodes 미이관. "
                    "원본 보존(.partial_migrated). sqlite-vec 설치 후 재시도 가능."
                )
        except Exception as e:
            logging.warning(f"[DB-MERGE] 마이그레이션 실패 (비치명): {e}")
            # [FIX-2] rollback -> DETACH 순서
            try:
                if self.conn.in_transaction:
                    self.conn.rollback()
            except Exception:
                pass
            try:
                if attached and cur is not None:
                    cur.execute("DETACH DATABASE vec_old")
            except Exception:
                pass
        finally:
            if cur is not None:
                cur.close()

    def initialize_db(self) -> None:
        """Backward-compatible explicit initializer.

        DBManager currently boots schema in __init__. Keep this method as an
        idempotent entrypoint for test/legacy code that still calls initialize_db().
        """
        with self._lock:
            if self.conn is None:
                self._boot_db()

    def begin(self):
        # [INF-P1-2] RLock으로 트랜잭션 제어 보호 (중첩 안전)
        with self._lock:
            self._ensure_open()
            cur = self.conn.cursor()
            try:
                cur.execute("BEGIN TRANSACTION")
            finally:
                cur.close()

    def commit(self):
        # [INF-P1-2] RLock으로 트랜잭션 제어 보호
        with self._lock:
            self._ensure_open()
            self.conn.commit()

    def rollback(self):
        # [INF-P1-2] RLock으로 트랜잭션 제어 보호
        with self._lock:
            self._ensure_open()
            self.conn.rollback()

    def resolve_pending_transaction(self, commit: bool = True) -> None:
        """[TF-30-8] 미완료 트랜잭션을 commit 또는 rollback으로 정리.

        ProjectManager 등 외부 코드가 ``self._lock`` 을 직접 참조하지 않도록
        캡슐화된 공개 API.
        """
        with self._lock:
            self._ensure_open()
            if self.conn.in_transaction:
                if commit:
                    self.conn.commit()
                else:
                    self.conn.rollback()

    def close(self) -> None:
        """[Phase 4A] DB 연결 안전 종료"""
        with self._lock:
            self._accept_runtime_telemetry_writes = False
            if self.conn:
                try:
                    if self.conn.in_transaction:
                        logging.warning("[B4-P1-3] close() 호출 시 미완료 트랜잭션 발견 — rollback 수행")
                        self.conn.rollback()
                    self.conn.close()
                finally:
                    self.conn = None
                    self.cursor = None

    def begin_shutdown(self) -> None:
        """Freeze best-effort runtime telemetry writes before resource teardown."""
        with self._lock:
            self._accept_runtime_telemetry_writes = False

    @property
    def accepts_runtime_telemetry_writes(self) -> bool:
        return bool(self._accept_runtime_telemetry_writes and self.conn is not None)

    @property
    def in_transaction(self) -> bool:
        """[Phase 4A] 현재 트랜잭션 진행 여부"""
        return bool(self.conn and self.conn.in_transaction)

    # --- [범용 쿼리] ---
    def execute_query(self, sql: str, params: tuple = ()) -> list:
        """[INF-P2-1] **읽기 전용** SELECT 쿼리 실행 후 결과 리스트 반환.

        WARNING: 이 메서드에는 하드코딩된 SQL만 전달해야 합니다.
        사용자 입력을 SQL 문자열에 직접 삽입하지 마세요 — params를 사용하세요.
        INSERT/UPDATE/DELETE 등 쓰기 쿼리는 execute_update()를 사용하세요.
        """
        self._ensure_open()
        # [INF-P2-1] SELECT 전용 가드 — 실수로 쓰기 쿼리 전달 방지
        stripped = sql.strip().upper()
        if stripped and not stripped.startswith("SELECT") and not stripped.startswith("PRAGMA"):
            raise DBError(
                f"execute_query()는 읽기 전용입니다. 쓰기 쿼리는 execute_update()를 사용하세요: {sql[:60]}",
                severity=DBErrorSeverity.HIGH,
            )
        with self._lock:
            cur = self.conn.cursor()
            try:
                cur.execute(sql, params)
                return cur.fetchall()
            finally:
                cur.close()

    def execute_update(self, sql: str, params: tuple = ()):
        """INSERT/UPDATE/DELETE 쿼리 실행"""
        self._ensure_open()
        with self._lock:
            cur = self.conn.cursor()
            try:
                cur.execute(sql, params)
            finally:
                cur.close()

    # --- [Section 1: 원고 및 지표] ---
    def save_manuscript(self, ep_num, title, content, hud_snapshot=None) -> None:
        with self._lock:
            nested = self.conn.in_transaction
            cur = self.conn.cursor()
            try:
                _hud_json = ""
                if hud_snapshot and isinstance(hud_snapshot, dict):
                    import json as _json

                    _hud_json = _json.dumps(hud_snapshot, ensure_ascii=False)
                cur.execute(
                    "INSERT OR REPLACE INTO manuscripts (ep_num, title, content, hud_snapshot) VALUES (?, ?, ?, ?)",
                    (ep_num, title, content, _hud_json),
                )
                if not nested:
                    self.commit()
            finally:
                cur.close()

    def get_manuscript(self, ep_num):
        with self._lock:
            cur = self.conn.cursor()
            try:
                cur.execute("SELECT * FROM manuscripts WHERE ep_num = ?", (ep_num,))
                row = cur.fetchone()
                if not row:
                    return None
                result = dict(row)
                # [LM-Tier TF-E] hud_snapshot JSON 역직렬화
                _hud_raw = result.get("hud_snapshot", "")
                if _hud_raw and isinstance(_hud_raw, str):
                    import json as _json

                    try:
                        result["hud_snapshot"] = _json.loads(_hud_raw)
                    except (ValueError, _json.JSONDecodeError):
                        result["hud_snapshot"] = {}
                else:
                    result["hud_snapshot"] = {}
                return result
            finally:
                cur.close()

    # 📂 modules/core/db_manager.py 내부에 추가

    def get_blueprint(self, ep_num):
        """특정 회차의 설계도 JSON 인출"""
        with self._lock:
            cur = self.conn.cursor()
            try:
                cur.execute("SELECT data FROM blueprints WHERE ep_num = ?", (ep_num,))
                row = cur.fetchone()
                if not row:
                    return None
                try:
                    return json.loads(row["data"])
                except (json.JSONDecodeError, TypeError) as e:  # [V70] NULL data → TypeError 방어
                    logging.warning(f" [DB] Blueprint JSON 파싱 실패 (ep_num={ep_num}): {e}")
                    return None
            finally:
                cur.close()

    # [INF-P2-2] 안전한 SQL 식별자 패턴 (알파벳/숫자/언더스코어만 허용)
    _SAFE_COLUMN_RE = __import__("re").compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    def update_martial_tracker(self, ep_num, martial_data) -> None:
        """[V26.6 S-Grade] DB 스키마에 존재하는 컬럼만 선별하여 저장 (Mismatched Key Guard)"""
        with self._lock:
            nested = self.conn.in_transaction
            # 1. 약속된 15대 지표(MARTIAL_METRICS)만 필터링 (스키마 가드)
            sanitized_data = {k: martial_data[k] for k in MARTIAL_METRICS if k in martial_data}

            if not sanitized_data:
                return

            # [INF-P2-2] 컬럼명 SQL 안전성 검증 (화이트리스트 + 정규식 이중 방어)
            validated_data = {k: v for k, v in sanitized_data.items() if self._SAFE_COLUMN_RE.match(k)}
            if not validated_data:
                return

            # 2. 필터링된 데이터로 쿼리 생성 (동적 컬럼 매핑)
            columns = ", ".join(validated_data.keys())
            placeholders = ", ".join(["?"] * len(validated_data))
            query = f"INSERT OR REPLACE INTO martial_tracker (ep_num, {columns}) VALUES (?, {placeholders})"

            # list/dict 값은 JSON 직렬화 (SQLite는 기본 타입만 허용)
            serialized_values = [
                json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for v in validated_data.values()
            ]
            cur = self.conn.cursor()
            try:
                cur.execute(query, [ep_num] + serialized_values)
                if not nested:
                    self.commit()
            finally:
                cur.close()

        # --- [V49.5] 화별 Bible CRUD ---
        # [V60.82] causal_links, karma_matrix, knowledge_map 필드 추가

    def save_episode_bible(self, ep_num: int, bible_delta: dict):
        """화별 Bible 저장 (원고에서 추출된 설정 변화)"""
        with self._lock:
            nested = self.conn.in_transaction
            cur = self.conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO episode_bibles
                    (ep_num, new_items, lost_items, new_npcs, npc_deaths,
                     relationship_changes, state_changes, time_passed, reveals,
                     causal_links, karma_matrix, knowledge_map)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        ep_num,
                        json.dumps(bible_delta.get("new_items", []), ensure_ascii=False),
                        json.dumps(bible_delta.get("lost_items", []), ensure_ascii=False),
                        json.dumps(bible_delta.get("new_npcs", []), ensure_ascii=False),
                        json.dumps(bible_delta.get("npc_deaths", []), ensure_ascii=False),
                        json.dumps(bible_delta.get("relationship_changes", []), ensure_ascii=False),
                        json.dumps(bible_delta.get("state_changes", {}), ensure_ascii=False),
                        bible_delta.get("time_passed", ""),
                        json.dumps(bible_delta.get("reveals", []), ensure_ascii=False),
                        json.dumps(bible_delta.get("causal_links", []), ensure_ascii=False),
                        json.dumps(bible_delta.get("karma_matrix", []), ensure_ascii=False),
                        json.dumps(bible_delta.get("knowledge_map", {}), ensure_ascii=False),
                    ),
                )
                if not nested:
                    self.commit()
            finally:
                cur.close()
            # [V64 P2-7] 누적 Bible 캐시 무효화: 이 ep 이후 캐시 모두 삭제
            invalidate_eps = [k for k in self._cumulative_bible_cache if k >= ep_num]
            for k in invalidate_eps:
                del self._cumulative_bible_cache[k]

    def get_episode_bible(self, ep_num: int) -> dict:
        """특정 화의 Bible delta 조회"""
        with self._lock:
            cur = self.conn.cursor()
            try:
                cur.execute("SELECT * FROM episode_bibles WHERE ep_num = ?", (ep_num,))
                row = cur.fetchone()
            finally:
                cur.close()
            if not row:
                return {}

            # [V60.82] 새 컬럼 안전 조회 (마이그레이션 전 DB 호환)
            def safe_get(key, default="[]"):
                try:
                    return row[key] if key in row.keys() else default
                except (KeyError, IndexError, TypeError):  # [V64.P4] specific exception for row access
                    return default

            def _safe_json(val, default_str="[]"):
                try:
                    return json.loads(val or default_str)
                except (json.JSONDecodeError, TypeError):
                    return json.loads(default_str)

            return {
                "ep_num": row["ep_num"],
                "new_items": _safe_json(row["new_items"], "[]"),
                "lost_items": _safe_json(row["lost_items"], "[]"),
                "new_npcs": _safe_json(row["new_npcs"], "[]"),
                "npc_deaths": _safe_json(row["npc_deaths"], "[]"),
                "relationship_changes": _safe_json(row["relationship_changes"], "[]"),
                "state_changes": _safe_json(row["state_changes"], "{}"),
                "time_passed": row["time_passed"] or "",
                "reveals": _safe_json(row["reveals"], "[]"),
                # [V60.82] 새 필드
                "causal_links": _safe_json(safe_get("causal_links", "[]"), "[]"),
                "karma_matrix": _safe_json(safe_get("karma_matrix", "[]"), "[]"),
                "knowledge_map": _safe_json(safe_get("knowledge_map", "{}"), "{}"),
            }

    def get_cumulative_bible(self, up_to_ep: int) -> dict:
        """
        1화부터 특정 화까지의 누적 Bible 계산
        [V64 P2-7] 증분 캐시: 이전 결과를 재활용하여 새 에피소드만 DB 조회
        """
        with self._lock:
            import copy as _copy

            # [V64 P2-7] 정확히 같은 ep 캐시가 있으면 즉시 반환 (deep copy로 mutation 방지)
            if up_to_ep in self._cumulative_bible_cache:
                return _copy.deepcopy(self._cumulative_bible_cache[up_to_ep])

            # 이전 캐시 중 가장 큰 ep 찾아서 재활용
            best_cached_ep = 0
            for cached_ep in self._cumulative_bible_cache:
                if cached_ep < up_to_ep and cached_ep > best_cached_ep:
                    best_cached_ep = cached_ep

            if best_cached_ep > 0:
                cumulative = _copy.deepcopy(self._cumulative_bible_cache[best_cached_ep])
                start_ep = best_cached_ep + 1
            else:
                cumulative = {
                    "items": [],  # 현재 소지 아이템
                    "npcs": [],  # 등장한 NPC 목록
                    "dead_npcs": [],  # 사망 NPC 목록
                    "relationships": {},  # {target: current_state}
                    "states": {},  # {subject: current_state}
                    "total_time": "",  # 누적 시간 흐름
                    "all_reveals": [],  # 모든 밝혀진 사실
                }
                start_ep = 1

            cur = self.conn.cursor()
            try:
                cur.execute(
                    "SELECT * FROM episode_bibles WHERE ep_num >= ? AND ep_num <= ? ORDER BY ep_num",
                    (start_ep, up_to_ep),
                )
                rows = cur.fetchall()
            finally:
                cur.close()

            for row in rows:
                # 아이템: 획득은 추가, 분실은 제거
                new_items = self._safe_json_loads(row["new_items"], "[]")
                lost_items = self._safe_json_loads(row["lost_items"], "[]")
                cumulative["items"].extend(new_items)
                cumulative["items"] = [i for i in cumulative["items"] if i not in lost_items]

                # NPC: 등장 추가, 사망은 별도 추적
                new_npcs = self._safe_json_loads(row["new_npcs"], "[]")
                npc_deaths = self._safe_json_loads(row["npc_deaths"], "[]")
                cumulative["npcs"].extend(new_npcs)
                cumulative["dead_npcs"].extend(npc_deaths)

                # 관계: 최신 상태로 덮어씀
                rel_changes = self._safe_json_loads(row["relationship_changes"], "[]")
                for change in rel_changes:
                    if isinstance(change, dict):
                        target = change.get("target", "")
                        if target:
                            cumulative["relationships"][target] = change.get("to", "")

                # 상태: 최신 상태로 덮어씀 [V61.5] dict/list 양방향 처리
                state_changes = self._safe_json_loads(row["state_changes"], "{}")
                if isinstance(state_changes, dict):
                    # dict 형태: {"internal_energy": "80%", "realm": "기경팔맥"}
                    for subject, value in state_changes.items():
                        if isinstance(value, (str, int, float)):
                            cumulative["states"][subject] = str(value)
                elif isinstance(state_changes, list):
                    # 레거시 list 형태: [{"subject": "내공", "to": "80%"}]
                    for state in state_changes:
                        if isinstance(state, dict):
                            subject = state.get("subject", "")
                            if subject:
                                cumulative["states"][subject] = state.get("to", "")

                # 밝혀진 사실 누적
                reveals = self._safe_json_loads(row["reveals"], "[]")
                cumulative["all_reveals"].extend(reveals)
                # [TF-B-2] 누적 크기 상한
                _reveals_max = 500
                if len(cumulative["all_reveals"]) > _reveals_max:
                    cumulative["all_reveals"] = cumulative["all_reveals"][-_reveals_max:]

            # [V66.1] C-3: LRU 캐시 크기 제한 (최대 5개 — 장기 세션 메모리 안정화)
            # [Sweep53] 방금 쓴 키가 즉시 퇴출되지 않도록 쓰기 전 evict
            _MAX_BIBLE_CACHE = 5
            while len(self._cumulative_bible_cache) >= _MAX_BIBLE_CACHE:
                oldest_ep = min(self._cumulative_bible_cache.keys())
                del self._cumulative_bible_cache[oldest_ep]
            self._cumulative_bible_cache[up_to_ep] = _copy.deepcopy(cumulative)

            return cumulative

    def get_all_episode_bibles(self) -> list:
        """
        [V60.8] 모든 Episode Bible 조회
        [V60.82] causal_links, karma_matrix, knowledge_map 추가

        Returns:
            list: Episode Bible dict 목록 (ep_num 순 정렬)
        """
        with self._lock:
            cur = self.conn.cursor()
            try:
                cur.execute("SELECT * FROM episode_bibles ORDER BY ep_num")
                rows = cur.fetchall()
            finally:
                cur.close()

            bibles = []
            for row in rows:
                # [V60.82] 새 컬럼 안전 조회
                def safe_get(key, default="[]"):
                    try:
                        return row[key] if key in row.keys() else default
                    except (KeyError, IndexError, TypeError):  # [V64.P4] specific exception for row access
                        return default

                bibles.append(
                    {
                        "ep_num": row["ep_num"],
                        "new_items": self._safe_json_loads(row["new_items"], "[]"),
                        "lost_items": self._safe_json_loads(row["lost_items"], "[]"),
                        "new_npcs": self._safe_json_loads(row["new_npcs"], "[]"),
                        "npc_deaths": self._safe_json_loads(row["npc_deaths"], "[]"),
                        "relationship_changes": self._safe_json_loads(row["relationship_changes"], "[]"),
                        "state_changes": self._safe_json_loads(row["state_changes"], "{}"),
                        "time_passed": row["time_passed"] or "",
                        "reveals": self._safe_json_loads(row["reveals"], "[]"),
                        # [V60.82] 새 필드
                        "causal_links": self._safe_json_loads(safe_get("causal_links", "[]"), "[]"),
                        "karma_matrix": self._safe_json_loads(safe_get("karma_matrix", "[]"), "[]"),
                        "knowledge_map": self._safe_json_loads(safe_get("knowledge_map", "{}"), "{}"),
                    }
                )

            return bibles

    def get_episode_bibles_before(self, up_to_ep: int) -> list:
        """
        Episode Bible lightweight range query for retrospective/knowledge checks.

        Returns only fields actually needed by InfoParadoxChecker.
        """
        with self._lock:
            cur = self.conn.cursor()
            try:
                cur.execute(
                    "SELECT ep_num, reveals, knowledge_map FROM episode_bibles WHERE ep_num < ? ORDER BY ep_num",
                    (int(up_to_ep),),
                )
                rows = cur.fetchall()
            finally:
                cur.close()

            bibles = []
            for row in rows:
                bibles.append(
                    {
                        "ep_num": row["ep_num"],
                        "reveals": self._safe_json_loads(row["reveals"], "[]"),
                        "knowledge_map": self._safe_json_loads(row["knowledge_map"], "{}"),
                    }
                )

            return bibles

    def delete_episode_bibles_after(self, ep_num: int):
        """특정 화 이후의 Bible delta 삭제 (롤백용)"""
        with self._lock:
            nested = self.conn.in_transaction
            cur = self.conn.cursor()
            try:
                cur.execute("DELETE FROM episode_bibles WHERE ep_num > ?", (ep_num,))
                if not nested:
                    self.commit()
                # [V70] 누적 Bible 캐시 무효화 (save_episode_bible과 동일 패턴)
                invalidate_eps = [k for k in self._cumulative_bible_cache if k > ep_num]
                for k in invalidate_eps:
                    del self._cumulative_bible_cache[k]
                return cur.rowcount
            finally:
                cur.close()

    def delete_orphaned_seeds(self, valid_ids: list) -> None:
        """[TF-30-8] 유효 ID 목록에 없는 유령 복선 삭제 (lock 보호)."""
        if not valid_ids:
            return
        with self._lock:
            self._ensure_open()
            nested = self.conn.in_transaction  # [TF-47] commit 누락 수정
            placeholders = ", ".join(["?"] * len(valid_ids))
            query = f"DELETE FROM seeds WHERE seed_id NOT IN ({placeholders})"
            self.conn.execute(query, valid_ids)
            if not nested:
                self.commit()

    def sync_seeds(self, seeds_list) -> None:
        """[V24 Precise Mode] 데이터 누락 시 기본값 할당으로 시스템 중단 방지"""
        with self._lock:
            nested = self.conn.in_transaction
            for s in seeds_list:
                # 1. 필수 데이터 인출 (KeyError 방지를 위해 .get() 사용)
                seed_id = s.get("id") or s.get("seed_id", f"unknown_{int(time.time())}")
                category = s.get("category", "일반")  # 카테고리 누락 시 '일반'으로 처리
                content = s.get("content") or s.get("description", "내용 없음")
                status = s.get("status", "active")
                planted_ep = s.get("planted_at") or s.get("planted_ep", 0)

                # 2. DB 박제
                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO seeds (seed_id, category, content, status, planted_ep)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (seed_id, category, content, status, planted_ep),
                )

            if not nested:
                self.commit()

    def archive_seed(self, seed_id, ep_num) -> None:
        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.execute(
                "UPDATE seeds SET status = 'archived', recovered_ep = ? WHERE seed_id = ?", (ep_num, seed_id)
            )
            if not nested:
                self.commit()

    def update_lore_item(self, category, item, description) -> None:
        """[PATCHED] 카테고리+이름 복합 키 기준 저장"""
        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.execute(
                """
                INSERT INTO encyclopedia (category, item, description)
                VALUES (?, ?, ?)
                ON CONFLICT(item) DO UPDATE SET
                    category = excluded.category,
                    description = excluded.description,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (category, item, description),
            )
            if not nested:
                self.commit()

    def update_lore_items_batch(self, lore_items_list) -> None:
        """[PATCHED] 일괄 업데이트 트랜잭션"""
        with self._lock:
            if not lore_items_list:
                return
            nested = self.conn.in_transaction
            try:
                if not nested:
                    self.begin()

                self.cursor.executemany(
                    """
                    INSERT INTO encyclopedia (category, item, description)
                    VALUES (?, ?, ?)
                    ON CONFLICT(item) DO UPDATE SET
                        category = excluded.category,
                        description = excluded.description,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    lore_items_list,
                )

                if not nested:
                    self.commit()

            except sqlite3.IntegrityError as e:
                # 중복 키 등 무결성 오류 - 개별 항목으로 재시도 가능
                if not nested:
                    self.rollback()
                logging.warning(f" [{DBErrorSeverity.HIGH}] 로어 일괄 저장 무결성 오류: {e}")
                logging.info("→ 해결책: 중복 항목 확인 후 개별 저장 시도")
                if nested:
                    raise DBIntegrityError(f"로어 저장 무결성 오류: {e}", original_error=e) from e
            except sqlite3.OperationalError as e:
                if not nested:
                    self.rollback()
                error_str = str(e).lower()
                if "locked" in error_str:
                    logging.warning(f" [{DBErrorSeverity.CRITICAL}] DB 잠금 상태: {e}")
                    logging.info("→ 해결책: 다른 프로세스/연결 종료 후 재시도")
                else:
                    logging.warning(f" [{DBErrorSeverity.HIGH}] 로어 저장 운영 오류: {e}")
                if nested:
                    raise DBTransactionError(f"로어 저장 트랜잭션 오류: {e}", original_error=e) from e
            except Exception as e:
                if not nested:
                    self.rollback()
                logging.warning(f" [{DBErrorSeverity.HIGH}] 로어 일괄 저장 실패: {e}")
                logging.info(f"→ 상세: {traceback.format_exc()[:300]}")
                if nested:
                    raise DBError(f"로어 저장 기타 오류: {e}", original_error=e) from e

    def get_lore_list_by_category(self, category):
        """특정 카테고리(NPC, ITEM 등) 전체 리스트 인출. category가 None이면 전체 반환"""
        with self._lock:
            if category is None:
                cur = self.cursor.execute("SELECT * FROM encyclopedia")
            else:
                cur = self.cursor.execute("SELECT * FROM encyclopedia WHERE category = ?", (category,))
            return [dict(row) for row in cur.fetchall()]

    def save_anchor(self, key, data) -> bool:
        """S등급 데이터를 박제하고 타임스탬프를 강제 갱신함"""
        with self._lock:
            nested = self.conn.in_transaction
            try:
                json_data = json.dumps(data, ensure_ascii=False)
                # 쿼리문에 CURRENT_TIMESTAMP를 명시하여 REPLACE 시에도 시간이 갱신되게 함
                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO anchors (key, data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                    (key, json_data),
                )
                # [V44 Fix] 중첩 트랜잭션 안전성 보장
                if not nested:
                    self.commit()
                return True
            except Exception as e:
                logging.warning(f"❌ [DB Error] Anchor 저장 실패: {e}")
                return False

    def load_anchor(self, key, default=None):
        with self._lock:
            cur = self.cursor.execute("SELECT data FROM anchors WHERE key = ?", (key,))
            row = cur.fetchone()
            if not row:
                # [V61.5] default=[] 전달 시 [] or {} → {} 반환 버그 수정
                return default if default is not None else {}
            try:
                return json.loads(row["data"])
            except (json.JSONDecodeError, TypeError) as e:  # [V70] row['data']가 None일 때 TypeError 방어
                logging.warning(f" [DB] Anchor JSON 파싱 실패 (key={key}): {e}")
                return default if default is not None else {}

    def load_all_anchors(self):
        with self._lock:
            cur = self.cursor.execute("SELECT key, data FROM anchors")
            result = {}
            for row in cur.fetchall():
                try:
                    result[row["key"]] = json.loads(row["data"]) if row["data"] else {}
                except (json.JSONDecodeError, TypeError) as e:
                    logging.warning(f" [DB] Anchor JSON 파싱 실패 (key={row['key']}): {e}")
                    result[row["key"]] = {}
            return result

        # --- [Section 4: 설계도 및 로그] ---

    # --- [Phase1-L0] 캐노니컬 팩트 접근자 ---

    def upsert_canonical_fact(self, fact_key: str, fact_type: str, value, first_ep: int, last_ep: int) -> None:
        """캐노니컬 팩트 생성 또는 갱신."""
        with self._lock:
            try:
                value_json = json.dumps(value, ensure_ascii=False) if value is not None else None
                cur = self.conn.cursor()
                cur.execute(
                    """
                    INSERT INTO canonical_facts (fact_key, fact_type, value_json, first_ep, last_ep)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(fact_key) DO UPDATE SET
                        fact_type  = excluded.fact_type,
                        value_json = excluded.value_json,
                        last_ep    = excluded.last_ep
                    """,
                    (fact_key, fact_type, value_json, first_ep, last_ep),
                )
                self.conn.commit()
            except Exception as e:
                logging.warning("[canonical_facts] upsert 실패 (비치명): %s", e)

    def get_canonical_facts(self, fact_type: str | None = None) -> list[dict]:
        """캐노니컬 팩트 목록 조회. fact_type 지정 시 필터링."""
        with self._lock:
            try:
                cur = self.conn.cursor()
                if fact_type is not None:
                    rows = cur.execute(
                        "SELECT * FROM canonical_facts WHERE fact_type = ? ORDER BY fact_key",
                        (fact_type,),
                    ).fetchall()
                else:
                    rows = cur.execute("SELECT * FROM canonical_facts ORDER BY fact_key").fetchall()
                result = []
                for row in rows:
                    d = dict(row)
                    try:
                        d["value"] = json.loads(d["value_json"]) if d.get("value_json") else None
                    except (json.JSONDecodeError, TypeError):
                        d["value"] = d.get("value_json")
                    result.append(d)
                return result
            except Exception as e:
                logging.warning("[canonical_facts] 조회 실패 (비치명): %s", e)
                return []

    # --- [Phase3-Timeline] 타임라인 접근자 ---

    def upsert_timeline_entry(self, ep_no: int, story_date: str, elapsed_days, time_note: str) -> None:
        """타임라인 엔트리 생성 또는 갱신."""
        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    """
                    INSERT INTO timeline_entries (ep_no, story_date, elapsed_days, time_note)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(ep_no) DO UPDATE SET
                        story_date   = excluded.story_date,
                        elapsed_days = excluded.elapsed_days,
                        time_note    = excluded.time_note
                    """,
                    (ep_no, story_date or "", elapsed_days, time_note or ""),
                )
                self.conn.commit()
            except Exception as e:
                logging.warning("[timeline_entries] upsert 실패 (비치명): %s", e)

    def get_timeline_range(self, start_ep: int = 1, end_ep: int = 9999, limit: int = 50) -> list[dict]:
        """타임라인 엔트리 조회 (ep_no 오름차순)."""
        with self._lock:
            try:
                cur = self.conn.cursor()
                rows = cur.execute(
                    "SELECT * FROM timeline_entries WHERE ep_no >= ? AND ep_no <= ? ORDER BY ep_no LIMIT ?",
                    (start_ep, end_ep, limit),
                ).fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logging.warning("[timeline_entries] 조회 실패 (비치명): %s", e)
                return []

    # --- [Graph-Layer] NPC 관계 / Arc 의존성 접근자 ---

    def upsert_npc_relationship_edge(self, npc1: str, npc2: str, relation: str, arc_no: int, ep_no: int) -> None:
        """NPC 간 관계 upsert. npc1/npc2는 정렬된 순서로 저장."""
        a, b = sorted([npc1, npc2])
        with self._lock:
            try:
                cur = self.conn.cursor()
                # [LM-D] 이력 기록: 기존 관계 조회 → 변경 시 append
                old_row = cur.execute(
                    "SELECT relation FROM npc_relationship_edges WHERE npc1 = ? AND npc2 = ?",
                    (a, b),
                ).fetchone()
                old_relation = old_row["relation"] if old_row else None

                cur.execute(
                    """
                    INSERT INTO npc_relationship_edges (npc1, npc2, relation, since_ep, updated_ep, arc_no)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(npc1, npc2) DO UPDATE SET
                        relation   = excluded.relation,
                        updated_ep = excluded.updated_ep,
                        arc_no     = excluded.arc_no
                    """,
                    (a, b, relation, ep_no, ep_no, arc_no),
                )

                # [LM-D] 변경 시에만 이력 기록
                if old_relation is not None and old_relation != relation:
                    cur.execute(
                        "INSERT INTO npc_relationship_history "
                        "(npc1, npc2, old_relation, new_relation, change_ep, arc_no) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (a, b, old_relation, relation, ep_no, arc_no),
                    )

                self.conn.commit()
            except Exception as e:
                logging.warning("[npc_relationship_edges] upsert 실패 (비치명): %s", e)

    def get_npc_relationship_edges(self, npc_name: str | None = None) -> list[dict]:
        """NPC 관계 조회. npc_name 지정 시 해당 NPC 관련만, 없으면 최신 100쌍."""
        with self._lock:
            try:
                cur = self.conn.cursor()
                if npc_name:
                    rows = cur.execute(
                        """
                        SELECT * FROM npc_relationship_edges
                        WHERE npc1 = ? OR npc2 = ?
                        ORDER BY updated_ep DESC
                        """,
                        (npc_name, npc_name),
                    ).fetchall()
                else:
                    rows = cur.execute(
                        """
                        SELECT * FROM npc_relationship_edges
                        ORDER BY updated_ep DESC LIMIT 100
                        """
                    ).fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logging.warning("[npc_relationship_edges] 조회 실패 (비치명): %s", e)
                return []

    def get_relationship_history(self, npc1: str, npc2: str, limit: int = 50) -> list[dict]:
        """[LM-D] NPC 쌍의 관계 변경 이력 조회 (시간순)."""
        a, b = sorted([npc1, npc2])
        with self._lock:
            try:
                cur = self.conn.cursor()
                rows = cur.execute(
                    "SELECT * FROM npc_relationship_history "
                    "WHERE npc1 = ? AND npc2 = ? ORDER BY change_ep ASC, id ASC LIMIT ?",
                    (a, b, limit),
                ).fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logging.warning("[npc_relationship_history] 조회 실패 (비치명): %s", e)
                return []

    def get_all_relationship_pairs_with_history(self, min_changes: int = 2) -> list[tuple]:
        """[LM-D] 변경 이력이 min_changes 이상인 NPC 쌍 목록."""
        with self._lock:
            try:
                cur = self.conn.cursor()
                rows = cur.execute(
                    "SELECT npc1, npc2, COUNT(*) as cnt "
                    "FROM npc_relationship_history "
                    "GROUP BY npc1, npc2 HAVING cnt >= ? "
                    "ORDER BY cnt DESC",
                    (min_changes,),
                ).fetchall()
                return [(row["npc1"], row["npc2"]) for row in rows]
            except Exception as e:
                logging.warning("[npc_relationship_history] 쌍 조회 실패 (비치명): %s", e)
                return []

    def upsert_arc_dependency(
        self, from_arc: int, to_arc: int, dep_type: str = "causes", description: str = ""
    ) -> None:
        """Arc 인과 의존성 upsert."""
        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute(
                    """
                    INSERT INTO arc_dependencies (from_arc_no, to_arc_no, dep_type, description)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(from_arc_no, to_arc_no) DO UPDATE SET
                        dep_type    = excluded.dep_type,
                        description = excluded.description
                    """,
                    (from_arc, to_arc, dep_type, description or ""),
                )
                self.conn.commit()
            except Exception as e:
                logging.warning("[arc_dependencies] upsert 실패 (비치명): %s", e)

    def get_arc_dependencies(self, arc_no: int) -> list[dict]:
        """arc_no를 from 또는 to로 갖는 의존성 양방향 조회."""
        with self._lock:
            try:
                cur = self.conn.cursor()
                rows = cur.execute(
                    """
                    SELECT * FROM arc_dependencies
                    WHERE from_arc_no = ? OR to_arc_no = ?
                    ORDER BY from_arc_no, to_arc_no
                    """,
                    (arc_no, arc_no),
                ).fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logging.warning("[arc_dependencies] 조회 실패 (비치명): %s", e)
                return []

    def _migrate_world_state_timeline_if_needed(self) -> None:
        """[Phase3] WorldState anchor의 timeline 배열을 timeline_entries 테이블로 1회 이전."""
        try:
            with self._lock:
                cur = self.conn.cursor()
                count = cur.execute("SELECT COUNT(*) FROM timeline_entries").fetchone()[0]
                if count > 0:
                    return  # 이미 마이그레이션 완료
                ws_data = self.load_anchor("world_state")
                if not ws_data or not isinstance(ws_data, dict):
                    return
                timeline = ws_data.get("timeline") or []
                migrated = 0
                for entry in timeline:
                    if not isinstance(entry, dict):
                        continue
                    ep = entry.get("ep")
                    desc = entry.get("description", "")
                    if ep and desc:
                        cur.execute(
                            "INSERT OR IGNORE INTO timeline_entries (ep_no, story_date, elapsed_days, time_note) VALUES (?, ?, ?, ?)",
                            (ep, desc, None, desc),
                        )
                        migrated += 1
                if migrated:
                    self.conn.commit()
                    logging.info("[DB] timeline_entries 마이그레이션: %d건", migrated)
        except Exception as e:
            logging.warning("[timeline_entries] 마이그레이션 실패 (비치명): %s", e)

    def save_blueprint(self, ep_num, data_dict) -> None:
        with self._lock:
            nested = self.conn.in_transaction
            serialized = json.dumps(data_dict, ensure_ascii=False)
            self.cursor.execute("INSERT OR REPLACE INTO blueprints (ep_num, data) VALUES (?, ?)", (ep_num, serialized))
            # [수정] 트랜잭션 안전성 확보
            if not nested:
                self.commit()

    def get_previous_blueprint(self, current_ep):
        with self._lock:
            cur = self.cursor.execute("SELECT data FROM blueprints WHERE ep_num = ?", (current_ep - 1,))
            row = cur.fetchone()
            if not row:
                return None
            try:
                return json.loads(row["data"])
            except (json.JSONDecodeError, TypeError) as e:  # [V70] NULL data → TypeError 방어
                logging.warning(f" [DB] Blueprint JSON 파싱 실패 (ep_num={current_ep - 1}): {e}")
                return None

    def save_state_log(self, ep_num, data_dict) -> None:
        """기존 메서드 호환성 유지"""
        self.save_state_log_with_summary(ep_num, data_dict, "")

    def save_state_log_with_summary(self, ep_num, data_dict, summary) -> None:
        """[NEW] 요약 포함 로그 저장"""
        with self._lock:
            nested = self.conn.in_transaction
            serialized = json.dumps(data_dict, ensure_ascii=False)
            self.cursor.execute(
                "INSERT OR REPLACE INTO state_logs (ep_num, data, summary) VALUES (?, ?, ?)",
                (ep_num, serialized, summary),
            )
            if not nested:
                self.commit()

    def get_latest_state(self) -> dict:
        with self._lock:
            cur = self.cursor.execute("SELECT data FROM state_logs ORDER BY ep_num DESC LIMIT 1")
            row = cur.fetchone()
            if not row:
                return {}
            try:
                return json.loads(row["data"]) if row["data"] else {}
            except (json.JSONDecodeError, TypeError) as e:
                logging.warning(f" [DB] State log JSON 파싱 실패: {e}")
                return {}

    def load_state_log(self, ep_num: int) -> dict:
        """[FIX] 특정 에피소드의 state_log 조회"""
        with self._lock:
            try:
                cur = self.cursor.execute("SELECT data, summary FROM state_logs WHERE ep_num = ?", (ep_num,))
                row = cur.fetchone()
                if not row:
                    return None
                result = {"summary": row["summary"] if row["summary"] else ""}
                try:
                    result["data"] = json.loads(row["data"]) if row["data"] else {}
                except json.JSONDecodeError:
                    result["data"] = {}
                return result
            except Exception as e:
                logging.warning(f" [DB] State log 조회 실패 (ep {ep_num}): {e}")
                return None

    def get_causal_summary_chain(self, limit=5):
        """[NEW] 과거 요약 체인 인출"""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, summary FROM state_logs WHERE summary IS NOT NULL ORDER BY ep_num DESC LIMIT ?",
                (limit,),
            )
            return "\n".join([f"- [제 {r['ep_num']} 화]: {r['summary']}" for r in reversed(cur.fetchall())])

    def get_recent_causal_links(self, current_ep: int, lookback: int = 30) -> list[dict]:
        """[LM-post-1] 최근 N화의 인과 링크 목록 반환."""
        start_ep = max(1, int(current_ep) - int(lookback))
        try:
            with self._lock:
                cur = self.cursor.execute(
                    "SELECT ep_num, data FROM causal_graph WHERE ep_num >= ? AND ep_num < ? ORDER BY ep_num",
                    (start_ep, current_ep),
                )
                results: list[dict] = []
                for row in cur.fetchall():
                    raw = row["data"]
                    try:
                        link = json.loads(raw) if isinstance(raw, str) else {}
                    except (json.JSONDecodeError, ValueError, TypeError):
                        continue
                    if isinstance(link, dict) and link:
                        link.setdefault("ep", row["ep_num"])
                        results.append(link)
                return results
        except Exception as _e:
            logging.debug("[causal_graph] get_recent_causal_links 실패 (비치명): %s", _e)
            return []

    def get_causal_links_by_entities(self, entity_names: list[str], *, before_ep: int, lookback: int = 120, limit: int = 30) -> list[dict]:
        """Entity-filtered causal link lookup for long-range continuity hints."""
        names = [str(name or "").strip() for name in entity_names if str(name or "").strip()]
        if not names:
            return []

        start_ep = max(1, int(before_ep) - int(lookback))
        try:
            with self._lock:
                cur = self.cursor.execute(
                    "SELECT ep_num, data FROM causal_graph WHERE ep_num >= ? AND ep_num < ? ORDER BY ep_num DESC LIMIT ?",
                    (start_ep, int(before_ep), int(limit) * 4),
                )
                results: list[dict] = []
                for row in cur.fetchall():
                    raw = row["data"]
                    try:
                        link = json.loads(raw) if isinstance(raw, str) else {}
                    except (json.JSONDecodeError, ValueError, TypeError):
                        continue
                    if not isinstance(link, dict) or not link:
                        continue
                    link_text = json.dumps(link, ensure_ascii=False)
                    if any(name in link_text for name in names):
                        link.setdefault("ep", row["ep_num"])
                        results.append(link)
                    if len(results) >= int(limit):
                        break
                return list(reversed(results))
        except Exception as _e:
            logging.debug("[causal_graph] get_causal_links_by_entities 실패 (비치명): %s", _e)
            return []

        # --- [Section 5: 관계 및 인과] ---

    def update_karma(self, npc_name, mis_val, obs_val, ep_num) -> None:
        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.execute(
                """
                INSERT INTO karma_status (npc_name, misunderstanding, obsession, last_updated_ep)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(npc_name) DO UPDATE SET
                    misunderstanding = ?,
                    obsession = ?,
                    last_updated_ep = ?
            """,
                (npc_name, mis_val, obs_val, ep_num, mis_val, obs_val, ep_num),
            )
            if not nested:
                self.commit()

    def get_all_karma(self):
        with self._lock:
            cur = self.cursor.execute("SELECT * FROM karma_status")
            return {row["npc_name"]: dict(row) for row in cur.fetchall()}

    def save_causal_links(self, new_links, current_ep) -> None:
        with self._lock:
            nested = self.conn.in_transaction
            if not new_links:
                return
            data_to_insert = []
            for link in new_links:
                if isinstance(link, dict):
                    normalized_link = dict(link)
                else:
                    text = str(link or "").strip()
                    if not text:
                        continue
                    normalized_link = {
                        "cause": text,
                        "effect": "",
                        "raw_text": text,
                    }
                ep = normalized_link.get("ep") or normalized_link.get("ep_no") or current_ep
                normalized_link.setdefault("ep", ep)
                serialized = json.dumps(normalized_link, ensure_ascii=False)
                data_to_insert.append((ep, serialized))
            if not data_to_insert:
                return
            self.cursor.executemany("INSERT INTO causal_graph (ep_num, data) VALUES (?, ?)", data_to_insert)
            if not nested:
                self.commit()

        # --- [Sovereign Unified Transaction: 최종 박제] ---

    def commit_episode_factory(
        self,
        ep_num,
        manuscript_data,
        martial_data,
        state_data,
        causal_links,
        karma_data,
        lore_data,
        recovered_seeds=None,
    ) -> bool:
        """
        [V27.0 S-Grade] 하위 항목 문자열화 현상까지 완벽 차단하는 무결성 엔진
        - 원자적 트랜잭션 보장
        - AI 데이터 파싱 유연성 극대화
        - 하위 엔터티(카르마, 로어, 복선)의 정규화 및 박제
        """
        # [FIX] RLock으로 멀티스레드 동시 접근 보호
        # [B4-P1-7] _ensure_open()을 lock 내부로 이동 — 동시 접근 시 conn 경합 방지
        nested_transaction = False
        self._lock.acquire()
        try:
            self._ensure_open()
            # 1. 최상위 데이터 파싱 및 정규화 (딕셔너리 보장)
            if isinstance(manuscript_data, str):
                try:
                    manuscript_data = json.loads(manuscript_data)
                except (json.JSONDecodeError, ValueError):
                    manuscript_data = {"title": f"제 {ep_num} 화", "content": manuscript_data}

            if isinstance(state_data, str):
                try:
                    state_data = json.loads(state_data)
                except (json.JSONDecodeError, ValueError):
                    state_data = {"context_audit": {"summary": "데이터 파싱 오류"}}

            # 트랜잭션 중첩 상태 확인 (상위 루프에서 이미 열려있는지 체크)
            nested_transaction = self.conn.in_transaction
            # 2. 트랜잭션 시작 (최상위 트랜잭션일 때만 실행)
            if not nested_transaction:
                self.begin()

            # 3. 원고 본문 및 무학 지표(HUD) 저장
            self.save_manuscript(ep_num, manuscript_data.get("title", "무제"), manuscript_data.get("content", ""))
            if martial_data:
                self.update_martial_tracker(ep_num, martial_data)

            # 4. 상태 로그 저장 및 요약(Summary) 추출
            audit = state_data.get("context_audit", {})
            # context_audit 자체가 문자열로 들어오는 할루시네이션 방어
            summary = audit.get("summary", "") if isinstance(audit, dict) else str(audit)
            self.save_state_log_with_summary(ep_num, state_data, summary)

            # 5. 🚨 인과관계(Causal Links) 데이터 정규화 및 저장
            if causal_links:
                normalized_links = []
                for link in causal_links:
                    # AI가 {"cause": "A", "effect": "B"} 가 아니라 "A -> B" 같은 문자열을 보냈을 때 대응
                    if isinstance(link, str):
                        normalized_links.append({"cause": "서사 진행", "effect": link})
                    elif isinstance(link, dict):
                        normalized_links.append(link)

                # [수정] 인자 오류 해결: ep_num을 함께 전달하여 유실 방지
                self.save_causal_links(normalized_links, ep_num)

            # 6. 🚨 카르마(NPC 관계) 데이터 정규화 및 에피소드 번호 강제 매핑
            if karma_data:
                for k in karma_data:
                    if not isinstance(k, dict):
                        continue

                    # AI의 다양한 키값 형태(target/npc_name, misunderstanding/value)를 모두 포용
                    npc = k.get("target") or k.get("npc_name") or k.get("name", "Unknown")
                    mis = k.get("misunderstanding")
                    if mis is None:
                        mis = k.get("value")
                    if mis is None:
                        mis = k.get("point", 0)
                    obs = k.get("obsession")
                    if obs is None:
                        obs = k.get("point")
                    if obs is None:
                        obs = 0

                    # 수동 갱신 시점(ep_num)을 현재 화수로 박제하여 데이터 오염 방지
                    self.update_karma(npc, mis, obs, ep_num)

            # 7. 로어(Encyclopedia) 데이터 정규화 및 수혈
            if lore_data and isinstance(lore_data, dict):
                for cat, items in lore_data.items():
                    if not isinstance(items, list):
                        continue
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        name = item.get("name") or item.get("Item")
                        desc = item.get("description") or item.get("desc") or str(item)
                        if name:
                            self.update_lore_item(cat, name, desc)

            # 8. 복선 회수(Seeds) 처리 (ID 정규화 및 상태 갱신)
            if recovered_seeds and isinstance(recovered_seeds, list):
                for rec in recovered_seeds:
                    if not isinstance(rec, dict):
                        continue
                    sid = rec.get("seed_id") or rec.get("id")
                    if sid:
                        self.cursor.execute(
                            "UPDATE seeds SET status = 'archived', recovered_ep = ? WHERE seed_id = ?", (ep_num, sid)
                        )

            # 9. 트랜잭션 커밋 (최상위 트랜잭션일 때만)
            if not nested_transaction:
                self.commit()
                logging.info(f" [DB Transaction] 제 {ep_num}화 데이터 안전 박제 완료.")

            return True

        except sqlite3.IntegrityError as e:
            # 무결성 오류: 중복 키, 제약 조건 위반 등
            if not nested_transaction:
                try:
                    self.rollback()
                except Exception:
                    pass  # [R7-P1-2] closed DB 시 이차 예외 방지
                logging.warning(f" [{DBErrorSeverity.HIGH}] 데이터 무결성 오류(롤백 완료): {e}")
                logging.info("→ 해결책: 중복 에피소드 번호 또는 키 확인")
                return False
            else:
                logging.warning(f" [{DBErrorSeverity.HIGH}] 내부 무결성 오류 (상위 롤백 유도): {e}")
                raise DBIntegrityError(
                    f"에피소드 {ep_num} 저장 무결성 오류", severity=DBErrorSeverity.HIGH, original_error=e
                ) from e

        except sqlite3.OperationalError as e:
            # 운영 오류: DB 잠금, 디스크 오류, 쿼리 오류 등
            error_str = str(e).lower()
            if not nested_transaction:
                try:
                    self.rollback()
                except Exception:
                    pass  # [R7-P1-2] closed DB 시 이차 예외 방지

            if "locked" in error_str:
                logging.warning(f" [{DBErrorSeverity.CRITICAL}] DB 잠금 상태(롤백 완료): {e}")
                logging.info("→ 해결책: 벡터 DB LOCK 해제 또는 프로세스 재시작")
            elif "disk" in error_str or "i/o" in error_str:
                logging.warning(f" [{DBErrorSeverity.CRITICAL}] 디스크 I/O 오류(롤백 완료): {e}")
                logging.info("→ 해결책: 디스크 공간 및 권한 확인")
            else:
                logging.warning(f" [{DBErrorSeverity.HIGH}] DB 운영 오류(롤백 완료): {e}")

            if not nested_transaction:
                return False
            else:
                raise DBTransactionError(
                    f"에피소드 {ep_num} 저장 트랜잭션 오류", severity=DBErrorSeverity.CRITICAL, original_error=e
                ) from e

        except (DBError, DBIntegrityError, DBTransactionError) as e:
            # 커스텀 DB 예외 (하위 메서드에서 발생)
            if not nested_transaction:
                try:
                    self.rollback()
                except Exception:
                    pass  # [R7-P1-2] closed DB 시 이차 예외 방지
                logging.warning(f" [{e.severity}] 하위 저장 오류(롤백 완료): {e}")
                return False
            else:
                raise  # 상위로 전파

        except Exception as e:
            # 🛡️ [핵심] 기타 예외 - 롤백 및 전파 전략
            if not nested_transaction:
                try:
                    self.rollback()
                except Exception:
                    pass  # [R7-P1-2] closed DB 시 이차 예외 방지
                logging.warning(f" [{DBErrorSeverity.HIGH}] 트랜잭션 실패(롤백 완료): {e}")
                logging.info(f"→ 상세: {traceback.format_exc()[:400]}")
                return False
            else:
                logging.warning(f" [{DBErrorSeverity.HIGH}] 내부 저장 실패 (상위 롤백 유도): {e}")
                raise DBError(f"에피소드 {ep_num} 저장 기타 오류", original_error=e) from e
        finally:
            # [FIX] RLock 해제 보장
            self._lock.release()

    @contextmanager
    def transaction(self) -> None:
        """[V44] 원자적 트랜잭션 보장 가드. 에러 타입별 롤백 및 세션 보호"""
        self._lock.acquire()  # [TF-C-2] begin/commit/rollback과 동일한 lock 보호
        try:
            self._ensure_open()
        except Exception:
            self._lock.release()
            raise
        nested = self.conn.in_transaction
        try:
            if not nested:
                self.cursor.execute("BEGIN TRANSACTION")
            yield
            if not nested:
                self.conn.commit()
        except sqlite3.IntegrityError as e:
            if not nested:
                if self.conn.in_transaction:
                    self.conn.rollback()
            logging.warning(f" [{DBErrorSeverity.HIGH}] 트랜잭션 무결성 오류 - 롤백 수행: {e}")
            raise DBIntegrityError(str(e), original_error=e) from e
        except sqlite3.OperationalError as e:
            if not nested:
                self.conn.rollback()
            error_str = str(e).lower()
            severity = (
                DBErrorSeverity.CRITICAL if "locked" in error_str or "disk" in error_str else DBErrorSeverity.HIGH
            )
            logging.warning(f" [{severity}] 트랜잭션 운영 오류 - 롤백 수행: {e}")
            if "locked" in error_str:
                logging.info("→ 해결책: DB 잠금 해제 후 재시도")
            raise DBTransactionError(str(e), severity=severity, original_error=e) from e
        except Exception as e:
            if not nested:
                self.conn.rollback()
            logging.warning(f" [{DBErrorSeverity.HIGH}] 트랜잭션 오류 - 롤백 수행: {e}")
            logging.info(f"→ 상세: {traceback.format_exc()[:300]}")
            raise DBError(str(e), original_error=e) from e
        finally:
            self._lock.release()

    # --- [Utility] ---
    def get_latest_episode_number(self) -> int:
        with self._lock:
            cur = self.cursor.execute("SELECT MAX(ep_num) as max_ep FROM manuscripts")
            row = cur.fetchone()
            return (row["max_ep"] or 0) + 1

    def get_latest_blueprint_number(self) -> int:
        """Blueprint 테이블의 최대 ep_num 반환 (없으면 0)"""
        with self._lock:
            cur = self.cursor.execute("SELECT MAX(ep_num) as max_ep FROM blueprints")
            row = cur.fetchone()
            return row["max_ep"] or 0

    def get_context_manuscripts(self, current_ep, limit=3):
        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, title, content FROM manuscripts WHERE ep_num < ? ORDER BY ep_num DESC LIMIT ?",
                (current_ep, limit),
            )
            return [dict(row) for row in cur.fetchall()]

    def reset_after(self, target_ep, *, commit: bool = True) -> None:
        """전체 테이블 리셋 및 롤백"""
        with self._lock:
            try:
                started_tx = not self.conn.in_transaction
                if started_tx:
                    self.cursor.execute("BEGIN")
                tables = ["blueprints", "state_logs", "causal_graph", "manuscripts", "martial_tracker"]
                for tbl in tables:
                    self.cursor.execute(f"DELETE FROM {tbl} WHERE ep_num >= ?", (target_ep,))
                self.cursor.execute("DELETE FROM episode_bibles WHERE ep_num >= ?", (target_ep,))  # [V70] 누락 수정
                self.cursor.execute(
                    "DELETE FROM sync_status WHERE ep_num >= ?", (target_ep,)
                )  # [V70] 동기화 상태도 리셋
                self.cursor.execute("DELETE FROM karma_status WHERE last_updated_ep >= ?", (target_ep,))
                self.cursor.execute("DELETE FROM seeds WHERE planted_ep >= ?", (target_ep,))
                # [D-2] 롤백 누락 데이터 정리
                self.cursor.execute("DELETE FROM npc_history WHERE episode_no >= ?", (target_ep,))
                self.cursor.execute("DELETE FROM episode_sentence_hashes WHERE episode_number >= ?", (target_ep,))
                self.cursor.execute("DELETE FROM episode_satisfaction_tags WHERE ep_num >= ?", (target_ep,))
                _stage4_selections = self._director_stage_predicate(4)
                self.cursor.execute(
                    "DELETE FROM director_selections WHERE ep_num >= ? AND " + _stage4_selections,
                    (target_ep,),
                )
                self.cursor.execute("DELETE FROM episode_pacing WHERE ep_num >= ?", (target_ep,))
                self.cursor.execute("DELETE FROM episode_quality_labels WHERE ep_num >= ?", (target_ep,))
                self.cursor.execute("DELETE FROM episode_quality_signals WHERE ep_num >= ?", (target_ep,))
                self.cursor.execute("DELETE FROM episode_quality_observations WHERE ep_num >= ?", (target_ep,))
                self.cursor.execute("DELETE FROM stage_attempts WHERE stage IN (3, 4) AND ep_num >= ?", (target_ep,))
                # [R7-P1-1] episode_fts/episode_meta 롤백 (FTS 먼저 삭제 후 meta 삭제)
                try:
                    self.cursor.execute("DELETE FROM episode_fts WHERE rowid >= ?", (target_ep,))
                except Exception:
                    pass  # FTS table may not exist
                self.cursor.execute("DELETE FROM episode_meta WHERE ep_num >= ?", (target_ep,))
                # [D-2] vec_episodes / foreshadow 롤백 누락 수정
                if self._vec_available:
                    try:
                        self.cursor.execute("DELETE FROM vec_episodes WHERE rowid >= ?", (target_ep,))
                    except Exception:
                        pass  # sqlite-vec 가상 테이블 미지원 환경 허용
                self.cursor.execute("DELETE FROM foreshadow WHERE planted_ep >= ?", (target_ep,))
                # [Graph-Layer] NPC 관계 롤백 (updated_ep 기준)
                self.cursor.execute("DELETE FROM npc_relationship_edges WHERE updated_ep >= ?", (target_ep,))
                # [LM-D] 관계 변경 이력 롤백
                self.cursor.execute("DELETE FROM npc_relationship_history WHERE change_ep >= ?", (target_ep,))
                if commit:
                    self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                logging.error("[B4-P1-4] reset_after(ep>=%s) 트랜잭션 실패 — rollback 수행: %s", target_ep, e)
                raise
            # [V70] 누적 Bible 캐시 무효화 (트랜잭션 외부 — 메모리 전용)
            invalidate_eps = [k for k in self._cumulative_bible_cache if k >= target_ep]
            for k in invalidate_eps:
                del self._cumulative_bible_cache[k]
            # 로어는 시간 개념이 모호하므로 유지하거나 별도 정책 필요 (여기선 유지)
        # [TF-24] VACUUM은 커밋 경로에서만 lock 밖에서 실행 (장시간 lock 점유 방지)
        if commit:
            try:
                self.conn.execute("VACUUM")
            except Exception as _vac_err:
                logging.debug("[DBManager] VACUUM 실패 (비치명): %s", _vac_err)

    def get_rollback_impact(self, target_ep: int) -> dict:
        """[D-2] 롤백 영향 범위 조회 — 삭제될 데이터 건수 미리보기."""
        with self._lock:
            impact = {}
            for tbl in ["blueprints", "state_logs", "causal_graph", "manuscripts", "martial_tracker"]:
                cur = self.cursor.execute(f"SELECT COUNT(*) as cnt FROM {tbl} WHERE ep_num >= ?", (target_ep,))  # noqa: S608
                impact[tbl] = cur.fetchone()["cnt"]

            cur = self.cursor.execute("SELECT COUNT(*) as cnt FROM episode_bibles WHERE ep_num >= ?", (target_ep,))
            impact["episode_bibles"] = cur.fetchone()["cnt"]

            cur = self.cursor.execute("SELECT COUNT(*) as cnt FROM npc_history WHERE episode_no >= ?", (target_ep,))
            impact["npc_history"] = cur.fetchone()["cnt"]

            cur = self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM episode_sentence_hashes WHERE episode_number >= ?", (target_ep,)
            )
            impact["sentence_hashes"] = cur.fetchone()["cnt"]

            cur = self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM episode_satisfaction_tags WHERE ep_num >= ?", (target_ep,)
            )
            impact["satisfaction_tags"] = cur.fetchone()["cnt"]

            _stage4_selections = self._director_stage_predicate(4)
            cur = self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM director_selections WHERE ep_num >= ? AND " + _stage4_selections,
                (target_ep,),
            )
            impact["director_selections"] = cur.fetchone()["cnt"]

            cur = self.cursor.execute("SELECT COUNT(*) as cnt FROM episode_pacing WHERE ep_num >= ?", (target_ep,))
            impact["episode_pacing"] = cur.fetchone()["cnt"]

            cur = self.cursor.execute("SELECT COUNT(*) as cnt FROM episode_quality_labels WHERE ep_num >= ?", (target_ep,))
            impact["episode_quality_labels"] = cur.fetchone()["cnt"]

            cur = self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM episode_quality_signals WHERE ep_num >= ?",
                (target_ep,),
            )
            impact["episode_quality_signals"] = cur.fetchone()["cnt"]

            cur = self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM episode_quality_observations WHERE ep_num >= ?",
                (target_ep,),
            )
            impact["episode_quality_observations"] = cur.fetchone()["cnt"]

            cur = self.cursor.execute("SELECT COUNT(*) as cnt FROM foreshadow WHERE planted_ep >= ?", (target_ep,))
            impact["foreshadow"] = cur.fetchone()["cnt"]

            cur = self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM npc_relationship_edges WHERE updated_ep >= ?",
                (target_ep,),
            )
            impact["npc_relationship_edges"] = cur.fetchone()["cnt"]

            # [LM-D] 관계 변경 이력 영향도
            cur = self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM npc_relationship_history WHERE change_ep >= ?", (target_ep,)
            )
            impact["npc_relationship_history"] = cur.fetchone()["cnt"]

            cur = self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM stage_attempts WHERE stage IN (3, 4) AND ep_num >= ?",
                (target_ep,),
            )
            impact["stage_attempts_stage34"] = cur.fetchone()["cnt"]

            return impact

        # --- [Memory Sync 전용 메서드] ---

    def get_sync_status(self, ep_num):
        """특정 에피소드의 벡터 DB 동기화 여부 조회"""
        with self._lock:
            cur = self.cursor.execute("SELECT vector_synced FROM sync_status WHERE ep_num = ?", (ep_num,))
            row = cur.fetchone()
            return row["vector_synced"] if row else None

    def update_sync_status(self, ep_num, status) -> None:
        """벡터 DB 동기화 상태 업데이트 (0: 미완료, 1: 완료)"""
        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO sync_status (ep_num, vector_synced, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                (ep_num, status),
            )
            if not nested:
                self.commit()

        # modules/core/db_manager.py 에 추가하면 좋은 전용 메서드

    def get_active_seeds(self):
        with self._lock:
            cur = self.cursor.execute("SELECT * FROM seeds WHERE status = 'active'")
            return [dict(row) for row in cur.fetchall()]

    def get_all_character_voices(self) -> list[dict]:
        """character_voice 프로필 전체 조회."""
        with self._lock:
            cur = self.conn.cursor()
            try:
                rows = cur.execute(
                    "SELECT npc_name, profile_data FROM character_voice ORDER BY npc_name"
                ).fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logging.debug("[character_voice] 전체 조회 실패 (비치명): %s", e)
                return []
            finally:
                cur.close()

        # --- [V61.5] Blueprint/Manuscript 연속성 캐싱용 메서드 ---

    def get_recent_blueprints(self, before_ep: int, limit: int = 10) -> list:
        """
        [V61.5] ep_num < before_ep인 blueprint 중 최근 limit개 조회

        Args:
            before_ep: 이 에피소드 이전의 blueprint만 조회
            limit: 최대 조회 개수

        Returns:
            list: [{'ep_num': int, 'data': dict}, ...] (ep_num 오름차순)
        """
        with self._lock:
            cur = self.cursor.execute(
                """SELECT ep_num, data FROM blueprints
                   WHERE ep_num < ?
                   ORDER BY ep_num DESC
                   LIMIT ?""",
                (before_ep, limit),
            )
            results = []
            for row in cur.fetchall():
                try:
                    data = json.loads(row["data"]) if row["data"] else {}
                except json.JSONDecodeError:
                    data = {}
                results.append({"ep_num": row["ep_num"], "data": data})
            # 오름차순으로 정렬 (시간순)
            return list(reversed(results))

    def get_recent_manuscripts(self, before_ep: int, limit: int = 10) -> list:
        """
        [V61.5] ep_num < before_ep인 manuscript 중 최근 limit개 조회

        Args:
            before_ep: 이 에피소드 이전의 manuscript만 조회
            limit: 최대 조회 개수

        Returns:
            list: [{'ep_num': int, 'title': str, 'content': str}, ...] (ep_num 오름차순)
        """
        with self._lock:
            cur = self.cursor.execute(
                """SELECT ep_num, title, content FROM manuscripts
                   WHERE ep_num < ?
                   ORDER BY ep_num DESC
                   LIMIT ?""",
                (before_ep, limit),
            )
            results = [dict(row) for row in cur.fetchall()]
            # 오름차순으로 정렬 (시간순)
            return list(reversed(results))

    def get_manuscripts_range(self, start_ep: int, end_ep: int) -> list[dict]:
        """[Tier4-12] manuscript range batch query: start_ep <= ep_num < end_ep."""
        safe_start = int(start_ep)
        safe_end = int(end_ep)
        if safe_end <= safe_start:
            return []

        with self._lock:
            cur = self.cursor.execute(
                """SELECT ep_num, title, content FROM manuscripts
                   WHERE ep_num >= ? AND ep_num < ?
                   ORDER BY ep_num ASC""",
                (safe_start, safe_end),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_episode_meta_summaries(self, start_ep: int, end_ep: int) -> list[dict]:
        """Return `episode_meta` summaries for start_ep <= ep_num < end_ep."""
        safe_start = int(start_ep)
        safe_end = int(end_ep)
        if safe_end <= safe_start:
            return []

        with self._lock:
            cur = self.cursor.execute(
                """SELECT ep_num, summary FROM episode_meta
                   WHERE ep_num >= ? AND ep_num < ?
                   ORDER BY ep_num ASC""",
                (safe_start, safe_end),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_npc_recent_episodes(self, npc_name: str, before_ep: int, limit: int = 5) -> list[int]:
        """
        episode_meta.entity_names(쉼표 구분)에서 특정 NPC가 등장한 최근 에피소드 번호 조회.
        반환 순서는 최신순(ep_num DESC).
        """
        name = str(npc_name or "").strip()
        if not name:
            return []

        safe_before_ep = int(before_ep)
        safe_limit = max(1, int(limit))
        if safe_before_ep <= 0:
            return []

        # entity_names는 "a,b,c" 포맷. 토큰 경계 매칭으로 부분일치 오탐 방지.
        name_token = name.replace(" ", "")
        like_pattern = f"%,{name_token},%"

        with self._lock:
            try:
                cur = self.cursor.execute(
                    """SELECT ep_num
                       FROM episode_meta
                       WHERE ep_num < ?
                         AND (',' || REPLACE(IFNULL(entity_names, ''), ' ', '') || ',') LIKE ?
                       ORDER BY ep_num DESC
                       LIMIT ?""",
                    (safe_before_ep, like_pattern, safe_limit),
                )
                return [int(row["ep_num"]) for row in cur.fetchall()]
            except Exception as e:
                logging.warning(f"[DBManager] get_npc_recent_episodes failed: {str(e)[:80]}")
                return []

    def get_recent_manuscript_excerpts(self, before_ep: int, limit: int = 10, max_chars: int = 200) -> list:
        """
        [V66.1] B-4: ep_num < before_ep인 manuscript 중 최근 limit개의 발췌만 조회.
        SQL SUBSTR로 content의 첫 max_chars 문자만 가져와 ~100KB I/O 제거/ep.

        Args:
            before_ep: 이 에피소드 이전의 manuscript만 조회
            limit: 최대 조회 개수
            max_chars: content에서 가져올 최대 문자 수 (기본 200)

        Returns:
            list: [{'ep_num': int, 'title': str, 'content': str}, ...] (ep_num 오름차순)
        """
        with self._lock:
            cur = self.cursor.execute(
                """SELECT ep_num, title, SUBSTR(content, 1, ?) AS content FROM manuscripts
                   WHERE ep_num < ?
                   ORDER BY ep_num DESC
                   LIMIT ?""",
                (max_chars, before_ep, limit),
            )
            results = [dict(row) for row in cur.fetchall()]
            # 오름차순으로 정렬 (시간순)
            return list(reversed(results))

        # --- [Phase 3-5A] NPC 변경 이력 ---

    def insert_npc_change(
        self,
        npc_name: str,
        episode_no: int,
        arc_no: int,
        field_name: str,
        old_value: str,
        new_value: str,
        change_source: str = "arc_extraction",
        reason: str = "",
    ) -> None:
        """[Phase 3-5A] NPC 변경 이력 append-only 삽입"""
        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.execute(
                "INSERT INTO npc_history (npc_name, episode_no, arc_no, field_name, old_value, new_value, change_source, reason) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (npc_name, episode_no, arc_no, field_name, old_value, new_value, change_source, reason),
            )
            if not nested:
                self.commit()

    def get_npc_history(self, npc_name: str, limit: int = 50) -> list:
        """[Phase 3-5A] NPC 변경 이력 조회 (최신순)"""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT id, npc_name, episode_no, arc_no, field_name, old_value, new_value, "
                "change_source, reason, created_at FROM npc_history WHERE npc_name = ? ORDER BY id DESC LIMIT ?",
                (npc_name, limit),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_npc_latest_fields(self, npc_name: str) -> dict:
        """[Phase 3-5A] NPC의 각 필드별 최신 값 조회"""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT field_name, new_value FROM npc_history "
                "WHERE npc_name = ? AND id IN ("
                "  SELECT MAX(id) FROM npc_history WHERE npc_name = ? GROUP BY field_name"
                ")",
                (npc_name, npc_name),
            )
            return {row["field_name"]: row["new_value"] for row in cur.fetchall()}

    # --- [D-4] Director 앙상블 선택 기록 ---

    def save_director_selection(
        self,
        ep_num: int,
        round_num: int,
        selected_label: str,
        selected_strategy: str,
        verdict: str,
        score: int = 0,
        selection_reason: str = "",
        candidate_count: int = 3,
        fix_scope: str = "",
        advisory_warnings: dict | None = None,
        stage: int | None = None,
        verdict_reason: str = "",
        pre_firewall_score: int = 0,
        firewall_triggered: bool = False,
        firewall_reason: str = "",
        attempt_key: str = "",
        candidate_key: str = "",
        content_hash: str = "",
        artifact_path: str = "",
    ) -> None:
        """Persist director selection result."""
        if not self.accepts_runtime_telemetry_writes:
            return
        with self._lock:
            if not self.accepts_runtime_telemetry_writes:
                return
            nested = self.conn.in_transaction
            _adv_json = json.dumps(advisory_warnings, ensure_ascii=False) if advisory_warnings else None
            self.cursor.execute(
                "INSERT INTO director_selections "
                "(stage, ep_num, round_num, selected_label, selected_strategy, verdict, score, "
                "selection_reason, candidate_count, fix_scope, advisory_warnings, verdict_reason, "
                "pre_firewall_score, firewall_triggered, firewall_reason, attempt_key, "
                "candidate_key, content_hash, artifact_path) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    stage,
                    ep_num,
                    round_num,
                    selected_label,
                    selected_strategy,
                    verdict,
                    score,
                    selection_reason[:500] if selection_reason else "",
                    candidate_count,
                    fix_scope or "",
                    _adv_json,
                    verdict_reason[:500] if verdict_reason else "",
                    int(pre_firewall_score or 0),
                    1 if firewall_triggered else 0,
                    firewall_reason[:500] if firewall_reason else "",
                    str(attempt_key or ""),
                    str(candidate_key or ""),
                    str(content_hash or ""),
                    str(artifact_path or ""),
                ),
            )
            if not nested:
                self.commit()

    def update_director_selection_rationale(
        self,
        *,
        attempt_key: str,
        selection_reason: str = "",
        verdict_reason: str = "",
        fix_scope: str = "",
    ) -> bool:
        """Update the latest director selection row for an attempt with final rationale fields."""
        if not attempt_key:
            return False
        with self._lock:
            nested = self.conn.in_transaction
            cur = self.cursor.execute(
                """
                UPDATE director_selections
                SET selection_reason = ?, verdict_reason = ?, fix_scope = ?
                WHERE id = (
                    SELECT id
                    FROM director_selections
                    WHERE attempt_key = ?
                    ORDER BY id DESC
                    LIMIT 1
                )
                """,
                (
                    selection_reason[:500] if selection_reason else "",
                    verdict_reason[:500] if verdict_reason else "",
                    fix_scope or "",
                    str(attempt_key),
                ),
            )
            if not nested:
                self.commit()
            return int(cur.rowcount or 0) > 0

    def save_episode_quality_label(self, ep_num: int, labels: dict) -> None:
        """PASS 에피소드의 정규화된 품질 라벨 저장."""
        if not isinstance(labels, dict):
            return

        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.execute(
                "INSERT OR REPLACE INTO episode_quality_labels "
                "(ep_num, score, verdict, selection_reason, open_review, score_breakdown, consistency_checklist) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    ep_num,
                    int(labels.get("score", 0) or 0),
                    str(labels.get("verdict", "") or ""),
                    str(labels.get("selection_reason", "") or "")[:300],
                    str(labels.get("open_review", "") or "")[:500],
                    json.dumps(labels.get("score_breakdown", {}) or {}, ensure_ascii=False),
                    json.dumps(labels.get("consistency_checklist", {}) or {}, ensure_ascii=False),
                ),
            )
            if not nested:
                self.commit()

    @staticmethod
    def _parse_episode_quality_signal_row(row: dict) -> dict:
        result = dict(row)
        try:
            result["ai_slop_hits"] = json.loads(result.get("ai_slop_hits") or "[]")
        except (TypeError, ValueError, json.JSONDecodeError):
            result["ai_slop_hits"] = []
        try:
            result["signal_summary"] = json.loads(result.get("signal_summary") or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            result["signal_summary"] = {}
        return result

    def save_episode_quality_signal(self, ep_num: int, signals: dict) -> None:
        """최종 원고 기준 Python-only 품질 신호 저장."""
        if not isinstance(signals, dict):
            return

        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.execute(
                "INSERT OR REPLACE INTO episode_quality_signals "
                "(ep_num, ced_score, ai_slop_score, ai_slop_hits, compression_ratio, burstiness, complexity, signal_summary) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ep_num,
                    float(signals.get("ced_score", 0.0) or 0.0),
                    float(signals.get("ai_slop_score", 0.0) or 0.0),
                    json.dumps(signals.get("ai_slop_hits", []) or [], ensure_ascii=False),
                    float(signals.get("compression_ratio", 0.0) or 0.0),
                    float(signals.get("burstiness", 0.0) or 0.0),
                    float(signals.get("complexity", 0.0) or 0.0),
                    json.dumps(signals.get("signal_summary", {}) or {}, ensure_ascii=False),
                ),
            )
            if not nested:
                self.commit()

    def get_episode_quality_signal(self, ep_num: int) -> dict | None:
        """특정 회차의 Python-only 품질 신호 조회."""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, ced_score, ai_slop_score, ai_slop_hits, compression_ratio, burstiness, complexity, signal_summary "
                "FROM episode_quality_signals WHERE ep_num = ?",
                (ep_num,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return self._parse_episode_quality_signal_row(dict(row))

    @staticmethod
    def _parse_episode_quality_observation_row(row: dict) -> dict:
        result = dict(row)
        result["operator_label"] = str(result.get("operator_label") or "").strip()
        result["note"] = str(result.get("note") or "").strip()
        return result

    def save_episode_quality_observation(self, ep_num: int, observation: dict) -> None:
        """운영자 수기 품질 관측 기록 저장."""
        if not isinstance(observation, dict):
            return

        label = str(observation.get("operator_label") or observation.get("label") or "").strip()
        note = str(observation.get("note") or "").strip()
        if not label:
            return

        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.execute(
                """
                INSERT INTO episode_quality_observations (ep_num, operator_label, note, created_at, updated_at)
                VALUES (?, ?, ?, datetime('now'), datetime('now'))
                ON CONFLICT(ep_num) DO UPDATE SET
                    operator_label = excluded.operator_label,
                    note = excluded.note,
                    updated_at = datetime('now')
                """,
                (ep_num, label[:40], note[:500]),
            )
            if not nested:
                self.commit()

    def get_episode_quality_observation(self, ep_num: int) -> dict | None:
        """특정 회차의 운영자 수기 품질 관측 조회."""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, operator_label, note, created_at, updated_at "
                "FROM episode_quality_observations WHERE ep_num = ?",
                (ep_num,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return self._parse_episode_quality_observation_row(dict(row))

    def get_recent_episode_quality_observations(
        self,
        before_ep: int | None = None,
        lookback: int = 20,
    ) -> list[dict]:
        """최근 N개 회차의 운영자 수기 품질 관측을 오래된 순으로 반환."""
        safe_lookback = max(1, int(lookback))
        with self._lock:
            if before_ep is None:
                cur = self.cursor.execute(
                    "SELECT ep_num, operator_label, note, created_at, updated_at "
                    "FROM episode_quality_observations ORDER BY ep_num DESC LIMIT ?",
                    (safe_lookback,),
                )
            else:
                cur = self.cursor.execute(
                    "SELECT ep_num, operator_label, note, created_at, updated_at "
                    "FROM episode_quality_observations WHERE ep_num < ? ORDER BY ep_num DESC LIMIT ?",
                    (before_ep, safe_lookback),
                )
            rows = [dict(row) for row in cur.fetchall()]
        return [self._parse_episode_quality_observation_row(row) for row in reversed(rows)]

    def get_recent_episode_quality_signals(
        self,
        before_ep: int | None = None,
        lookback: int = 20,
    ) -> list[dict]:
        """최근 N개 에피소드의 품질 신호를 오래된 순으로 반환."""
        safe_lookback = max(1, int(lookback))
        with self._lock:
            if before_ep is None:
                cur = self.cursor.execute(
                    "SELECT ep_num, ced_score, ai_slop_score, ai_slop_hits, compression_ratio, burstiness, complexity, signal_summary "
                    "FROM episode_quality_signals ORDER BY ep_num DESC LIMIT ?",
                    (safe_lookback,),
                )
            else:
                cur = self.cursor.execute(
                    "SELECT ep_num, ced_score, ai_slop_score, ai_slop_hits, compression_ratio, burstiness, complexity, signal_summary "
                    "FROM episode_quality_signals WHERE ep_num < ? ORDER BY ep_num DESC LIMIT ?",
                    (before_ep, safe_lookback),
                )
            rows = [dict(row) for row in cur.fetchall()]

        return [self._parse_episode_quality_signal_row(row) for row in reversed(rows)]

    def get_quality_signal_summary(self, before_ep: int | None = None, lookback: int = 5) -> dict:
        """최근 품질 신호 요약을 UI/브리지 용도로 반환."""
        recent_rows = self.get_recent_episode_quality_signals(before_ep=before_ep, lookback=lookback)
        if not recent_rows:
            return {
                "available": False,
                "lookback": lookback,
                "latest_ep": None,
                "signals": {},
                "recent": [],
                "latest_ai_slop_hits": [],
            }

        latest = recent_rows[-1]
        signals = {
            "ced": build_signal_stat(field="ced_score", recent_rows=recent_rows, mode="lower_better"),
            "ai_slop": build_signal_stat(field="ai_slop_score", recent_rows=recent_rows, mode="lower_better"),
            "compression": build_signal_stat(
                field="compression_ratio", recent_rows=recent_rows, mode="deviation"
            ),
            "burstiness": build_signal_stat(field="burstiness", recent_rows=recent_rows, mode="deviation"),
            "complexity": build_signal_stat(field="complexity", recent_rows=recent_rows, mode="deviation"),
        }

        return {
            "available": True,
            "lookback": lookback,
            "latest_ep": latest.get("ep_num"),
            "signals": signals,
            "recent": [
                {
                    "ep_num": row.get("ep_num"),
                    "ced_score": row.get("ced_score", 0.0),
                    "ai_slop_score": row.get("ai_slop_score", 0.0),
                    "compression_ratio": row.get("compression_ratio", 0.0),
                    "burstiness": row.get("burstiness", 0.0),
                    "complexity": row.get("complexity", 0.0),
                }
                for row in recent_rows
            ],
            "latest_ai_slop_hits": latest.get("ai_slop_hits", [])[:5],
            "latest_signal_summary": latest.get("signal_summary", {}),
        }

    def get_episode_quality_label(self, ep_num: int) -> dict | None:
        """특정 회차의 품질 라벨 조회."""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, score, verdict, selection_reason, open_review, score_breakdown, consistency_checklist "
                "FROM episode_quality_labels WHERE ep_num = ?",
                (ep_num,),
            )
            row = cur.fetchone()
        if not row:
            return None

        result = dict(row)
        for field in ("score_breakdown", "consistency_checklist"):
            raw = result.get(field)
            try:
                result[field] = json.loads(raw) if raw else {}
            except (TypeError, ValueError, json.JSONDecodeError):
                result[field] = {}
        return result

    def get_recent_episode_quality_labels(self, before_ep: int, lookback: int = 20) -> list[dict]:
        """최근 N개 에피소드의 품질 라벨을 오래된 순으로 반환."""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, score, verdict, selection_reason, open_review, score_breakdown, consistency_checklist "
                "FROM episode_quality_labels WHERE ep_num < ? ORDER BY ep_num DESC LIMIT ?",
                (before_ep, lookback),
            )
            rows = [dict(row) for row in cur.fetchall()]

        parsed_rows: list[dict] = []
        for row in reversed(rows):
            for field in ("score_breakdown", "consistency_checklist"):
                raw = row.get(field)
                try:
                    row[field] = json.loads(raw) if raw else {}
                except (TypeError, ValueError, json.JSONDecodeError):
                    row[field] = {}
            parsed_rows.append(row)
        return parsed_rows

    @staticmethod
    def _director_stage_predicate(stage: int, *, alias: str = "") -> str:
        prefix = f"{alias}." if alias else ""
        if stage == 2:
            return (
                f"({prefix}stage = 2 OR ({prefix}stage IS NULL AND COALESCE({prefix}selected_label, '') = ''))"
            )
        if stage == 4:
            return (
                f"({prefix}stage = 4 OR ({prefix}stage IS NULL AND COALESCE({prefix}selected_label, '') != ''))"
            )
        return f"{prefix}stage = {int(stage)}"

    def get_recent_episode_scores(self, before_ep: int, lookback: int = 5) -> list[dict]:
        """최근 PASS 계열 에피소드 점수를 오래된 순으로 반환."""
        with self._lock:
            cur = self.cursor.execute(
                """
                SELECT sa.ep_num, sa.score, sa.verdict, sa.attempt_key
                FROM stage_attempts sa
                JOIN (
                    SELECT ep_num, MAX(id) AS last_id
                    FROM stage_attempts
                    WHERE ep_num < ? AND stage = 4 AND verdict IN ('PASS', 'PASS_WITH_WARNING')
                    GROUP BY ep_num
                    ORDER BY ep_num DESC
                    LIMIT ?
                ) latest ON latest.last_id = sa.id
                ORDER BY sa.ep_num ASC
                """,
                (before_ep, lookback),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_stage_attempts_for_arc(
        self,
        arc_num: int,
        stages: tuple[int, ...] = (3, 4),
        verdict: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """특정 Arc의 stage_attempts 조회."""
        if not stages:
            return []

        placeholders = ", ".join("?" for _ in stages)
        sql = (
            "SELECT stage, ep_num, arc_num, attempt_num, attempt_key, verdict, score, failure_category, reject_reason, "
            "advisory_flags, prompt_version, fix_scope, candidate_key, content_hash, artifact_path, selection_reason, "
            "verdict_reason, open_review, fix_scope_reasoning, runtime_advisory, retry_directives "
            f"FROM stage_attempts WHERE arc_num = ? AND stage IN ({placeholders})"
        )
        params: list = [arc_num, *stages]
        if verdict:
            sql += " AND verdict = ?"
            params.append(verdict)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._lock:
            cur = self.cursor.execute(sql, tuple(params))
            rows = [dict(row) for row in cur.fetchall()]

        parsed_rows: list[dict] = []
        for row in rows:
            raw_flags = row.get("advisory_flags")
            try:
                row["advisory_flags"] = json.loads(raw_flags) if raw_flags else {}
            except (TypeError, ValueError, json.JSONDecodeError):
                row["advisory_flags"] = {}
            parsed_rows.append(row)
        return parsed_rows

    def get_stage4_final_authority_rows(
        self,
        *,
        limit: int = 100,
        session_id: str | None = None,
    ) -> list[dict]:
        """Return explicit Stage 4 final-authority rows with companion-role metadata."""
        limit = max(1, int(limit or 100))
        session_id = str(session_id or "").strip()

        stage_attempt_where = "WHERE stage = 4 AND COALESCE(attempt_key, '') != ''"
        params: list[object] = []
        if session_id:
            stage_attempt_where += " AND session_id = ?"
            params.append(session_id)
        params.append(limit)

        sql = f"""
            WITH latest_stage_attempts AS (
                SELECT sa.id,
                       sa.ep_num,
                       sa.attempt_num,
                       sa.verdict,
                       sa.score,
                       sa.session_id,
                       sa.attempt_key,
                       sa.candidate_key,
                       sa.content_hash,
                       sa.artifact_path
                FROM stage_attempts sa
                JOIN (
                    SELECT MAX(id) AS last_id
                    FROM stage_attempts
                    {stage_attempt_where}
                    GROUP BY attempt_key
                    ORDER BY MAX(id) DESC
                    LIMIT ?
                ) latest ON latest.last_id = sa.id
            ),
            latest_director AS (
                SELECT ds.id,
                       ds.attempt_key,
                       ds.verdict,
                       ds.score,
                       ds.candidate_key,
                       ds.content_hash,
                       ds.artifact_path
                FROM director_selections ds
                JOIN (
                    SELECT MAX(id) AS last_id
                    FROM director_selections
                    WHERE {self._director_stage_predicate(4)} AND COALESCE(attempt_key, '') != ''
                    GROUP BY attempt_key
                ) latest ON latest.last_id = ds.id
            )
            SELECT lsa.ep_num,
                   lsa.attempt_num,
                   lsa.verdict AS final_verdict,
                   lsa.score AS final_score,
                   lsa.session_id,
                   lsa.attempt_key,
                   lsa.candidate_key AS final_candidate_key,
                   lsa.content_hash AS final_content_hash,
                   lsa.artifact_path AS final_artifact_path,
                   ld.verdict AS selection_verdict,
                   ld.score AS selection_score,
                   ld.candidate_key AS selection_candidate_key,
                   ld.content_hash AS selection_content_hash,
                   ld.artifact_path AS selection_artifact_path
            FROM latest_stage_attempts lsa
            LEFT JOIN latest_director ld ON ld.attempt_key = lsa.attempt_key
            ORDER BY lsa.id DESC
        """

        with self._lock:
            cur = self.conn.execute(sql, tuple(params))
            rows = [dict(row) for row in cur.fetchall()]

        resolved_rows: list[dict] = []
        for row in rows:
            final_content_hash = str(row.get("final_content_hash") or "").strip()
            final_artifact_path = str(row.get("final_artifact_path") or "").strip()
            selection_content_hash = str(row.get("selection_content_hash") or "").strip()
            selection_artifact_path = str(row.get("selection_artifact_path") or "").strip()
            selection_candidate_key = str(row.get("selection_candidate_key") or "").strip()

            diff_fields: list[str] = []
            if (
                final_content_hash
                and selection_content_hash
                and final_content_hash != selection_content_hash
            ):
                diff_fields.append("content_hash")
            if (
                final_artifact_path
                and selection_artifact_path
                and final_artifact_path != selection_artifact_path
            ):
                diff_fields.append("artifact_path")

            selection_row_present = bool(
                selection_candidate_key
                or selection_content_hash
                or selection_artifact_path
                or str(row.get("selection_verdict") or "").strip()
            )
            if not selection_row_present:
                companion_status = "missing"
            elif diff_fields:
                companion_status = "pre_final_candidate"
            else:
                companion_status = "same_as_final"

            resolved_rows.append(
                {
                    "ep_num": int(row.get("ep_num") or 0),
                    "attempt_num": int(row.get("attempt_num") or 0),
                    "attempt_key": str(row.get("attempt_key") or "").strip(),
                    "session_id": str(row.get("session_id") or "").strip(),
                    "final_verdict": str(row.get("final_verdict") or "").strip(),
                    "final_score": row.get("final_score"),
                    "final_candidate_key": str(row.get("final_candidate_key") or "").strip(),
                    "final_content_hash": final_content_hash,
                    "final_artifact_path": final_artifact_path,
                    "selection_verdict": str(row.get("selection_verdict") or "").strip(),
                    "selection_score": row.get("selection_score"),
                    "selection_candidate_key": selection_candidate_key,
                    "selection_content_hash": selection_content_hash,
                    "selection_artifact_path": selection_artifact_path,
                    "final_authority_sink": "stage_attempts",
                    "selection_role": "historical_companion" if selection_row_present else "missing",
                    "selection_companion_status": companion_status,
                    "selection_companion_diff_fields": diff_fields,
                    "selection_matches_final_artifact": selection_row_present and not diff_fields,
                }
            )

        return resolved_rows

    def get_latest_stage4_gate_repair_snapshot(self, session_id: str | None = None) -> dict[str, object]:
        """Return the latest Stage 4 final-authority gate/repair snapshot for operator-facing summaries."""
        session_id = str(session_id or "").strip()
        params: list[object] = [4]
        where_parts = ["stage = ?", "COALESCE(attempt_key, '') != ''"]
        if session_id:
            where_parts.append("session_id = ?")
            params.append(session_id)

        sql = f"""
            SELECT id,
                   ep_num,
                   attempt_num,
                   verdict,
                   score,
                   session_id,
                   attempt_key,
                   candidate_key,
                   content_hash,
                   artifact_path,
                   advisory_flags,
                   selection_reason,
                   verdict_reason,
                   open_review
            FROM stage_attempts
            WHERE {' AND '.join(where_parts)}
            ORDER BY id DESC
            LIMIT 1
        """

        with self._lock:
            cur = self.conn.execute(sql, tuple(params))
            row = cur.fetchone()

        if not row:
            return {}

        item = dict(row)
        advisory_flags = self._safe_json_loads(item.get("advisory_flags"), "{}")
        if not isinstance(advisory_flags, dict):
            advisory_flags = {}
        gate_semantics = advisory_flags.get("gate_semantics")
        if not isinstance(gate_semantics, dict):
            gate_semantics = {}
        fix_pack = advisory_flags.get("fix_pack")
        if not isinstance(fix_pack, dict):
            fix_pack = {}
        retry_budget_axes = advisory_flags.get("retry_budget_axes")
        if not isinstance(retry_budget_axes, dict):
            retry_budget_axes = {}

        payload: dict[str, object] = {
            "ep_num": int(item.get("ep_num") or 0),
            "attempt_num": int(item.get("attempt_num") or 0),
            "attempt_key": str(item.get("attempt_key") or "").strip(),
            "session_id": str(item.get("session_id") or "").strip(),
            "final_verdict": str(item.get("verdict") or "").strip(),
            "final_score": item.get("score"),
            "candidate_key": str(item.get("candidate_key") or "").strip(),
            "content_hash": str(item.get("content_hash") or "").strip(),
            "artifact_path": str(item.get("artifact_path") or "").strip(),
            "selection_reason": str(item.get("selection_reason") or "").strip(),
            "verdict_reason": str(item.get("verdict_reason") or "").strip(),
            "open_review": str(item.get("open_review") or "").strip(),
            "director_verdict": str(gate_semantics.get("director_verdict") or "").strip(),
            "gate_basis": str(gate_semantics.get("gate_basis") or "").strip(),
            "repair_scope": str(gate_semantics.get("repair_scope") or "").strip(),
            "fix_pack": fix_pack,
            "retry_budget_axes": retry_budget_axes,
            "final_authority_sink": "stage_attempts",
        }

        authority_rows = self.get_stage4_final_authority_rows(limit=1, session_id=session_id or None)
        if authority_rows:
            authority_row = authority_rows[0]
            if str(authority_row.get("attempt_key") or "").strip() == payload["attempt_key"]:
                payload["selection_role"] = str(authority_row.get("selection_role") or "").strip()
                payload["selection_companion_status"] = str(
                    authority_row.get("selection_companion_status") or ""
                ).strip()
                payload["selection_matches_final_artifact"] = bool(
                    authority_row.get("selection_matches_final_artifact", False)
                )

        return payload

    def save_llm_call(
        self,
        agent_name: str,
        model: str,
        prompt_chars: int,
        response_chars: int,
        duration_ms: int,
        success: bool = True,
        error_type: str | None = None,
        error_msg: str | None = None,
        stage: int | None = None,
        ep_num: int | None = None,
        verdict: str | None = None,
        context_tag: str | None = None,
        session_id: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cached_tokens: int | None = None,
        thinking_tokens: int | None = None,
        total_cost_usd: float | None = None,
        prompt_snippet: str | None = None,
        response_snippet: str | None = None,
        thinking_snippet: str | None = None,
    ) -> None:
        """[Log-1] Save one LLM call record in non-blocking mode."""
        try:
            if not self.accepts_runtime_telemetry_writes:
                return
            ts = datetime.now().isoformat(timespec="seconds")
            # [Log-Phase2] Keep DB size bounded: snippets only for failed calls.
            _prompt_snip = str(prompt_snippet)[:3000] if (not success and prompt_snippet) else None
            _response_snip = str(response_snippet) if (not success and response_snippet) else None
            # [TF-58] thinking은 성공 호출에서도 저장 (Director 구조 결함 분석용), 5000자 제한
            _thinking_snip = str(thinking_snippet)[:5000] if thinking_snippet else None
            with self._lock:
                if not self.accepts_runtime_telemetry_writes:
                    return
                self.cursor.execute(
                    """INSERT INTO llm_calls
                       (session_id, ts, stage, ep_num, agent_name, model,
                        prompt_chars, response_chars, duration_ms,
                        success, error_type, error_msg, verdict, context_tag,
                        input_tokens, output_tokens, cached_tokens, thinking_tokens, total_cost_usd,
                        prompt_snippet, response_snippet, thinking_snippet)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        session_id,
                        ts,
                        stage,
                        ep_num,
                        agent_name,
                        model,
                        prompt_chars,
                        response_chars,
                        duration_ms,
                        1 if success else 0,
                        error_type,
                        (error_msg or "")[:80],
                        verdict,
                        context_tag,
                        int(input_tokens or 0) if input_tokens is not None else None,
                        int(output_tokens or 0) if output_tokens is not None else None,
                        int(cached_tokens or 0) if cached_tokens is not None else None,
                        int(thinking_tokens or 0) if thinking_tokens is not None else None,
                        float(total_cost_usd or 0.0) if total_cost_usd is not None else None,
                        _prompt_snip,
                        _response_snip,
                        _thinking_snip,
                    ),
                )
                self.conn.commit()
        except Exception as _e:
            logging.debug("[llm_calls] save_llm_call failed (non-blocking): %s", _e)

    def save_stage_attempt(
        self,
        stage: int,
        verdict: str,
        attempt_num: int = 1,
        ep_num: int | None = None,
        arc_num: int | None = None,
        score: int | None = None,
        failure_category: str | None = None,
        reject_reason: str | None = None,
        fix_scope: str | None = None,
        model: str | None = None,
        duration_ms: int | None = None,
        advisory_flags: dict | None = None,
        session_id: str | None = None,
        attempt_key: str | None = None,
        generation_method: str | None = None,
        prompt_version: str | None = None,
        candidate_key: str | None = None,
        content_hash: str | None = None,
        artifact_path: str | None = None,
        selection_reason: str | None = None,
        verdict_reason: str | None = None,
        open_review: str | None = None,
        fix_scope_reasoning: str | None = None,
        runtime_advisory: str | None = None,
        retry_directives: str | None = None,
    ) -> bool:
        """[Log-2] Save one stage attempt record in non-blocking mode."""
        nested = False
        try:
            if not self.accepts_runtime_telemetry_writes:
                return False
            ts = datetime.now().isoformat(timespec="seconds")
            _advisory_json = json.dumps(advisory_flags, ensure_ascii=False) if advisory_flags else None
            with self._lock:
                if not self.accepts_runtime_telemetry_writes:
                    return False
                nested = self.conn.in_transaction
                self.cursor.execute(
                    """INSERT INTO stage_attempts
                       (session_id, ts, stage, ep_num, arc_num, attempt_num,
                        verdict, score, failure_category, reject_reason,
                        fix_scope, model, duration_ms, advisory_flags, attempt_key, generation_method, prompt_version,
                        candidate_key, content_hash, artifact_path, selection_reason, verdict_reason, open_review,
                        fix_scope_reasoning, runtime_advisory, retry_directives)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        session_id,
                        ts,
                        stage,
                        ep_num,
                        arc_num,
                        attempt_num,
                        verdict,
                        score,
                        failure_category,
                        (reject_reason or "")[:500],
                        fix_scope,
                        model,
                        duration_ms,
                        _advisory_json,
                        str(attempt_key or ""),
                        generation_method,
                        prompt_version,
                        str(candidate_key or ""),
                        str(content_hash or ""),
                        str(artifact_path or ""),
                        (selection_reason or "")[:500],
                        (verdict_reason or "")[:500],
                        (open_review or "")[:500],
                        (fix_scope_reasoning or "")[:500],
                        (runtime_advisory or "")[:500],
                        (retry_directives or "")[:500],
                    ),
                )
                if not nested:
                    self.conn.commit()
            return True
        except Exception as _e:
            with self._lock:
                if not nested and self.conn is not None and self.conn.in_transaction:
                    try:
                        self.conn.rollback()
                    except Exception:
                        pass
            logging.debug("[stage_attempts] save_stage_attempt failed (non-blocking): %s", _e)
            return False

    def save_ui_event(
        self,
        *,
        session_id: str | None = None,
        ts: str | None = None,
        seq: int | None = None,
        stage: int | str | None = None,
        ep_num: int | None = None,
        arc_num: int | None = None,
        round_num: int | None = None,
        attempt_key: str | None = None,
        component: str = "UI",
        event_kind: str = "log",
        level: str = "info",
        render_format: str = "text",
        message: str = "",
        visible: bool = True,
        selection_value: str | None = None,
        prompt_id: str | None = None,
        artifact_path: str | None = None,
        meta: dict | None = None,
    ) -> bool:
        """Persist one operator-visible UI event in non-blocking mode."""
        nested = False
        try:
            if not self.accepts_runtime_telemetry_writes:
                return False
            event_ts = str(ts or datetime.now().isoformat(timespec="seconds"))
            normalized_stage, stage_label = self._normalize_ui_event_stage(stage)
            meta_payload = self._merge_ui_event_stage_label(meta, stage_label)
            meta_json = json.dumps(meta_payload, ensure_ascii=False, default=str) if meta_payload is not None else None
            with self._lock:
                if not self.accepts_runtime_telemetry_writes:
                    return False
                nested = self.conn.in_transaction
                self.cursor.execute(
                    """INSERT INTO ui_events
                       (session_id, ts, seq, stage, ep_num, arc_num, round_num, attempt_key,
                        component, event_kind, level, render_format, message, visible,
                        selection_value, prompt_id, artifact_path, meta_json)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        str(session_id or ""),
                        event_ts,
                        int(seq) if seq is not None else None,
                        normalized_stage,
                        int(ep_num) if ep_num is not None else None,
                        int(arc_num) if arc_num is not None else None,
                        int(round_num) if round_num is not None else None,
                        str(attempt_key or ""),
                        str(component or "UI"),
                        str(event_kind or "log"),
                        str(level or "info"),
                        str(render_format or "text"),
                        str(message or "")[:4000],
                        1 if visible else 0,
                        str(selection_value or "")[:500] if selection_value is not None else None,
                        str(prompt_id or "")[:200] if prompt_id is not None else None,
                        str(artifact_path or "")[:1000] if artifact_path is not None else None,
                        meta_json,
                    ),
                )
                if not nested:
                    self.conn.commit()
            return True
        except Exception as _e:
            with self._lock:
                if not nested and self.conn is not None and self.conn.in_transaction:
                    try:
                        self.conn.rollback()
                    except Exception:
                        pass
            logging.debug("[ui_events] save_ui_event failed (non-blocking): %s", _e)
            return False

    def get_fix_scope_stats(self, lookback: int = 200) -> list[dict]:
        """[A-3] fix_scope × verdict 교차 집계."""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT fix_scope, verdict, COUNT(*) AS cnt "
                "FROM (SELECT fix_scope, verdict FROM director_selections "
                "      WHERE fix_scope != '' ORDER BY id DESC LIMIT ?) "
                "GROUP BY fix_scope, verdict",
                (max(lookback, 1),),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_strategy_win_rates(
        self,
        lookback: int = 20,
        *,
        selected_label: str | None = None,
        allowed_strategies: tuple[str, ...] | list[str] | set[str] | None = None,
    ) -> dict:
        """[D-4] 최근 N건의 PASS 선택에서 전략별 선택 비중 조회."""
        query = (
            "SELECT selected_strategy "
            "FROM director_selections "
            "WHERE verdict = 'PASS' AND selected_strategy IS NOT NULL AND selected_strategy != '' "
        )
        params: list[object] = []
        if selected_label is not None:
            query += "AND selected_label = ? "
            params.append(selected_label)
        query += "ORDER BY id DESC LIMIT ?"
        params.append(lookback)

        with self._lock:
            cur = self.cursor.execute(
                query,
                tuple(params),
            )
            rows = [r["selected_strategy"] for r in cur.fetchall()]

        if allowed_strategies:
            allowed = {str(strategy).strip() for strategy in allowed_strategies if str(strategy).strip()}
            rows = [strategy for strategy in rows if strategy in allowed]

        total = len(rows)
        if total == 0:
            return {"total": 0}

        result = {"total": total}
        counts = {}
        for strategy in rows:
            counts[strategy] = counts.get(strategy, 0) + 1
        for strategy, cnt in counts.items():
            result[strategy] = round(cnt / total, 2)
        return result

    def get_selection_analysis(self, lookback: int = 100) -> list[dict]:
        """최근 Director 선택 기록 조회 (편향 분석용)."""
        lookback = max(int(lookback), 0)
        if lookback == 0:
            return []

        with self._lock:
            cur = self.cursor.execute(
                "SELECT selected_strategy, verdict, score, selection_reason "
                "FROM director_selections ORDER BY id DESC LIMIT ?",
                (lookback,),
            )
            return [dict(row) for row in cur.fetchall()]

    def save_cost_record(
        self,
        *,
        session_id: str,
        scope_type: str,
        scope_id: int = 0,
        total_calls: int = 0,
        total_tokens: int = 0,
        total_cost_usd: float = 0.0,
        model_breakdown: str | dict = "{}",
    ) -> None:
        """비용 기록 저장."""
        if scope_type not in {"arc", "episode", "session"}:
            raise ValueError(f"invalid scope_type: {scope_type}")

        if isinstance(model_breakdown, dict):
            model_breakdown = json.dumps(model_breakdown, ensure_ascii=False)
        elif not isinstance(model_breakdown, str):
            model_breakdown = "{}"

        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.execute(
                "INSERT INTO cost_log (session_id, scope_type, scope_id, total_calls, total_tokens, total_cost_usd, model_breakdown) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    scope_type,
                    int(scope_id),
                    int(total_calls),
                    int(total_tokens),
                    float(total_cost_usd),
                    model_breakdown,
                ),
            )
            if not nested:
                self.commit()

    def get_cost_summary(self, scope_type: str | None = None, lookback: int = 50) -> list[dict]:
        """비용 요약 조회 (최신순)."""
        lookback = max(int(lookback), 0)
        if lookback == 0:
            return []

        with self._lock:
            if scope_type:
                cur = self.cursor.execute(
                    "SELECT * FROM cost_log WHERE scope_type = ? ORDER BY id DESC LIMIT ?",
                    (scope_type, lookback),
                )
            else:
                cur = self.cursor.execute("SELECT * FROM cost_log ORDER BY id DESC LIMIT ?", (lookback,))
            return [dict(row) for row in cur.fetchall()]

    def get_recent_selections(self, ep_num: int, lookback: int = 10) -> list:
        """[D-4] 최근 선택 이력 조회 (최신순)."""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, round_num, selected_label, selected_strategy, verdict, score, selection_reason, fix_scope "
                "FROM director_selections "
                "WHERE ep_num < ? "
                "ORDER BY id DESC LIMIT ?",
                (ep_num, lookback),
            )
            return [dict(row) for row in cur.fetchall()]

    # --- [Phase 3-B] 크로스 에피소드 문장 핑거프린트 ---

    def store_sentence_hashes(self, ep_num: int, hashes_with_preview: list) -> None:
        """[Phase 3-B] 에피소드별 문장 해시 저장.

        Args:
            ep_num: 에피소드 번호
            hashes_with_preview: [(sent_hash, preview), ...] 리스트
        """
        if not hashes_with_preview:
            return
        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.executemany(
                "INSERT OR IGNORE INTO episode_sentence_hashes "
                "(episode_number, sentence_hash, sentence_preview) VALUES (?, ?, ?)",
                [(ep_num, h, p) for h, p in hashes_with_preview],
            )
            if not nested:
                self.commit()

    def find_repeated_sentence_hashes(self, target_hashes: list, current_ep: int, lookback: int = 5) -> list:
        """[Phase 3-B] 현재 해시 중 최근 N화에 이미 존재하는 해시 조회.

        Returns:
            [{"sentence_hash": str, "episode_number": int, "sentence_preview": str}, ...]
        """
        if not target_hashes:
            return []
        min_ep = max(1, current_ep - lookback)
        with self._lock:
            placeholders = ",".join("?" for _ in target_hashes)
            cur = self.cursor.execute(
                f"SELECT sentence_hash, episode_number, sentence_preview "
                f"FROM episode_sentence_hashes "
                f"WHERE sentence_hash IN ({placeholders}) "
                f"AND episode_number >= ? AND episode_number < ? "
                f"ORDER BY episode_number ASC",
                [*target_hashes, min_ep, current_ep],
            )
            return [dict(row) for row in cur.fetchall()]

    def get_sentence_hashes(self, ep_num: int) -> list:
        """[Phase 3-B] 특정 에피소드의 문장 해시 전량 조회 (테스트/디버그용)."""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT sentence_hash, sentence_preview FROM episode_sentence_hashes "
                "WHERE episode_number = ? ORDER BY rowid",
                (ep_num,),
            )
            return [dict(row) for row in cur.fetchall()]

    # ===== [D Step 3] 에피소드 만족도 태깅 CRUD =====

    def save_satisfaction_tag(self, ep_num: int, tag_dict: dict) -> None:
        """[D Step 3] 에피소드 만족도 태그 저장 (INSERT OR REPLACE)."""
        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.execute(
                "INSERT OR REPLACE INTO episode_satisfaction_tags "
                "(ep_num, primary_tag, satisfaction_score, protagonist_agency, frustration_flag) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    ep_num,
                    tag_dict.get("primary_tag", "일상"),
                    tag_dict.get("satisfaction_score", 5),
                    tag_dict.get("protagonist_agency", "자력"),
                    1 if tag_dict.get("frustration_flag") else 0,
                ),
            )
            if not nested:
                self.commit()

    def get_satisfaction_tag(self, ep_num: int) -> dict | None:
        """[D Step 3] 특정 에피소드의 만족도 태그 조회."""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, primary_tag, satisfaction_score, protagonist_agency, frustration_flag "
                "FROM episode_satisfaction_tags WHERE ep_num = ?",
                (ep_num,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "ep_num": row["ep_num"],
                "primary_tag": row["primary_tag"],
                "satisfaction_score": row["satisfaction_score"],
                "protagonist_agency": row["protagonist_agency"],
                "frustration_flag": bool(row["frustration_flag"]),
            }

    def get_recent_satisfaction_tags(self, before_ep: int, lookback: int = 5) -> list:
        """[D Step 3] 최근 N화의 만족도 태그 조회 (시간순 반환).

        Args:
            before_ep: 이 에피소드 이전의 태그를 조회
            lookback: 조회할 에피소드 수

        Returns:
            [{"ep_num": int, "primary_tag": str, ...}, ...] (오래된 순)
        """
        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, primary_tag, satisfaction_score, protagonist_agency, frustration_flag "
                "FROM episode_satisfaction_tags "
                "WHERE ep_num < ? ORDER BY ep_num DESC LIMIT ?",
                (before_ep, lookback),
            )
            rows = [
                {
                    "ep_num": row["ep_num"],
                    "primary_tag": row["primary_tag"],
                    "satisfaction_score": row["satisfaction_score"],
                    "protagonist_agency": row["protagonist_agency"],
                    "frustration_flag": bool(row["frustration_flag"]),
                }
                for row in cur.fetchall()
            ]
            return list(reversed(rows))

    # ═══════════════════════════════════════════════════════════════
    # [TF-I24] 에피소드 호흡 분석 기록
    # ═══════════════════════════════════════════════════════════════

    def save_pacing_record(self, ep_num: int, pacing_data: dict) -> None:
        """[TF-I24] 에피소드 호흡 분석 결과 저장."""
        import json as _json

        with self._lock:
            nested = self.conn.in_transaction
            self.cursor.execute(
                "INSERT OR REPLACE INTO episode_pacing "
                "(ep_num, pacing_score, dialogue_ratio, scene_break_count, "
                "avg_sentence_length, short_sentence_ratio, long_sentence_ratio, issues) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ep_num,
                    pacing_data.get("pacing_score", 50),
                    pacing_data.get("dialogue_ratio", 0.0),
                    pacing_data.get("scene_break_count", 0),
                    pacing_data.get("avg_sentence_length", 0.0),
                    pacing_data.get("short_sentence_ratio", 0.0),
                    pacing_data.get("long_sentence_ratio", 0.0),
                    _json.dumps(pacing_data.get("issues", []), ensure_ascii=False),
                ),
            )
            if not nested:
                self.commit()

    def get_recent_pacing_records(self, before_ep: int, lookback: int = 5) -> list:
        """[TF-I24] 최근 N화의 호흡 분석 조회 (오래된 순).

        Args:
            before_ep: 이 에피소드 이전의 기록을 조회
            lookback: 조회할 에피소드 수

        Returns:
            [{"ep_num": int, "pacing_score": int, ...}, ...] (오래된 순)
        """
        import json as _json

        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, pacing_score, dialogue_ratio, scene_break_count, "
                "avg_sentence_length, short_sentence_ratio, long_sentence_ratio, issues "
                "FROM episode_pacing "
                "WHERE ep_num < ? ORDER BY ep_num DESC LIMIT ?",
                (before_ep, lookback),
            )
            rows = []
            for row in cur.fetchall():
                try:
                    issues = _json.loads(row["issues"]) if row["issues"] else []
                except (ValueError, TypeError):
                    issues = []
                rows.append(
                    {
                        "ep_num": row["ep_num"],
                        "pacing_score": row["pacing_score"],
                        "dialogue_ratio": row["dialogue_ratio"],
                        "scene_break_count": row["scene_break_count"],
                        "avg_sentence_length": row["avg_sentence_length"],
                        "short_sentence_ratio": row["short_sentence_ratio"],
                        "long_sentence_ratio": row["long_sentence_ratio"],
                        "issues": issues,
                    }
                )
            return list(reversed(rows))
