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
        # [V45] 멀티스레드 안전성을 위한 Lock
        self._lock = threading.RLock()
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
        # [V45] check_same_thread=False 사용 시 RLock으로 보호
        self.conn = self._connect_with_integrity_recovery()
        self.cursor = self.conn.cursor()

        # [INF-I3] WAL 모드 활성화 — 읽기/쓰기 동시성 향상, 크래시 복구 안전성 강화
        try:
            self.cursor.execute("PRAGMA journal_mode=WAL")
            self.cursor.execute("PRAGMA synchronous=NORMAL")
        except sqlite3.OperationalError as e:
            logging.warning(f"[DBManager] WAL 모드 설정 실패 (비차단): {e}")

        # [DB-MERGE] sqlite-vec 확장 로드 (선택적)
        self._vec_available = False
        try:
            import sqlite_vec as _sv

            self.conn.enable_load_extension(True)
            _sv.load(self.conn)
            self.conn.enable_load_extension(False)
            self._vec_available = True
        except ImportError:
            logging.info("[DBManager] sqlite-vec 미설치 - 벡터 테이블 생략")
        except Exception as e:
            logging.warning(f"[DBManager] sqlite-vec 로드 실패: {e}")

        # 1. 앵커 데이터 (Bible, Volumes, Arcs)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_status (
                ep_num INTEGER PRIMARY KEY,
                vector_synced INTEGER DEFAULT 0, -- 0: 미동기화, 1: 완료
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

        # [DB-Eff-P3] anchors 테이블 SSOT 정책:
        # 허용 키: "bible", "arcs", "genre_info", "sys_caches"
        # 금지: character_voice, foreshadow, failure_learning → 전용 테이블 사용
        # 추가 키 등록 시 이 목록에 명시 후 진행
        # anchors 테이블: 'key'가 유니크해야 REPLACE가 작동함
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS anchors (
                key TEXT PRIMARY KEY,
                data TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

        # 2. 설계도 (Blueprints)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS blueprints (
                ep_num INTEGER PRIMARY KEY,
                data TEXT
            )
        """)

        # 3. 상태 로그 (Logs - summary 컬럼 포함)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS state_logs (
                ep_num INTEGER PRIMARY KEY,
                data TEXT,
                summary TEXT
            )
        """)
        # (기존 테이블 마이그레이션용: 컬럼 없으면 추가)
        # [V45] ALTER TABLE 오류 처리 강화 - commit/rollback 추가
        try:
            self.cursor.execute("PRAGMA table_info(state_logs)")
            existing_cols = {row["name"] for row in self.cursor.fetchall()}
            if "summary" not in existing_cols:
                self.cursor.execute("ALTER TABLE state_logs ADD COLUMN summary TEXT")
                self.conn.commit()  # [V45] 마이그레이션 성공 시 즉시 커밋
        except sqlite3.OperationalError as e:
            # 테이블 자체가 없는 경우 (CREATE TABLE IF NOT EXISTS에서 처리됨)
            if "no such table" not in str(e).lower():
                logging.warning(f"[WARNING] state_logs 마이그레이션 실패: {e}")
                try:
                    self.conn.rollback()  # [V45] 실패 시 롤백
                except Exception as e:
                    logging.debug(f"[SILENT] state_logs rollback: {e}")
                    pass

        # 4. 인과 그래프 (Causal Graph)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS causal_graph (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ep_num INTEGER,
                data TEXT
            )
        """)

        # 5. NPC 관계 (Karma)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS karma_status (
                npc_name TEXT PRIMARY KEY,
                misunderstanding INTEGER DEFAULT 0,
                obsession INTEGER DEFAULT 0,
                last_updated_ep INTEGER
            )
        """)

        # 6. 원고 본문 (Manuscripts)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS manuscripts (
                ep_num INTEGER PRIMARY KEY,
                title TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # [LM-Tier TF-E] hud_snapshot 컬럼 마이그레이션
        try:
            self.cursor.execute("ALTER TABLE manuscripts ADD COLUMN hud_snapshot TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # 이미 존재

        # [Phase 5.2.2] 7. Reflexion Memory (과거 실패 패턴 학습)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reflexion_memory (
                pattern_type TEXT PRIMARY KEY,
                description TEXT,
                frequency INTEGER DEFAULT 1,
                solution TEXT,
                first_seen TEXT,
                last_seen TEXT,
                first_ep INTEGER,
                last_ep INTEGER
            )
        """)

        # ------------------------------------------------------------------
        # 🚨 [Patch 1.1] Martial Tracker 자동 스키마 마이그레이션 로직
        # ------------------------------------------------------------------
        # 1. 테이블 생성 (없을 경우)
        # [V44] SQL 컬럼명 검증 (알파벳, 숫자, 언더스코어만 허용)
        import re

        safe_column_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        validated_metrics = [k for k in MARTIAL_METRICS if safe_column_pattern.match(k)]
        if len(validated_metrics) != len(MARTIAL_METRICS):
            invalid = set(MARTIAL_METRICS) - set(validated_metrics)
            logging.warning(f"[WARNING] 잘못된 컬럼명 무시됨: {invalid}")
        columns_def = ", ".join([f"{k} TEXT" for k in validated_metrics])
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS martial_tracker (ep_num INTEGER PRIMARY KEY, {columns_def})")

        # 2. 컬럼 동기화 검사 (코드에는 있는데 DB에 없는 컬럼 찾기)
        try:
            # 현재 DB의 컬럼 목록 조회
            self.cursor.execute("PRAGMA table_info(martial_tracker)")
            existing_columns = {row["name"] for row in self.cursor.fetchall()}

            # MARTIAL_METRICS 순회하며 누락된 컬럼 추가
            for metric in validated_metrics:  # [Sweep43] MARTIAL_METRICS → validated_metrics (SQL 안전성)
                if metric not in existing_columns:
                    logging.info(f" [DB Migration] 새로운 지표 '{metric}' 발견. 테이블에 컬럼을 추가합니다.")
                    self.cursor.execute(f"ALTER TABLE martial_tracker ADD COLUMN {metric} TEXT")

            self.conn.commit()

        except sqlite3.IntegrityError as e:
            # 무결성 오류: 컬럼 이름 충돌 등
            logging.warning(f" [{DBErrorSeverity.HIGH}] 마이그레이션 무결성 오류: {e}")
            # 기존 테이블 구조 유지, 계속 진행
        except sqlite3.OperationalError as e:
            # 운영 오류: 테이블 잠금, 디스크 오류 등
            error_str = str(e).lower()
            if "locked" in error_str:
                logging.warning(f" [{DBErrorSeverity.HIGH}] DB 잠금 상태. 다른 프로세스 확인 필요: {e}")
            elif "disk" in error_str or "i/o" in error_str:
                logging.warning(f" [{DBErrorSeverity.CRITICAL}] 디스크 I/O 오류: {e}")
            else:
                logging.warning(f" [{DBErrorSeverity.HIGH}] 마이그레이션 운영 오류: {e}")
        except Exception as e:
            logging.warning(f" [{DBErrorSeverity.WARN}] 마이그레이션 기타 오류: {e}")
            logging.info(f"→ 상세: {traceback.format_exc()[:200]}")
        # 8. 복선 전용 관리 (Seeds)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS seeds (
                seed_id TEXT PRIMARY KEY,
                category TEXT,
                content TEXT,
                status TEXT DEFAULT 'active', -- active / archived
                planted_ep INTEGER,
                recovered_ep INTEGER
            )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_seeds_status ON seeds(status)")

        # 9. [NEW] 로어 백과사전 (Encyclopedia)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS encyclopedia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                item TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(item)
            )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_encyclopedia_category ON encyclopedia(category)")

        # 10. [V49.5] 화별 Bible (에피소드별 설정 변화 추적)
        # [V60.82] causal_links, karma_matrix, knowledge_map 컬럼 추가
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episode_bibles (
                ep_num INTEGER PRIMARY KEY,
                new_items TEXT,              -- JSON: 새로 획득한 아이템
                lost_items TEXT,             -- JSON: 잃어버린/파괴된 아이템
                new_npcs TEXT,               -- JSON: 새로 등장한 NPC
                npc_deaths TEXT,             -- JSON: 사망한 NPC
                relationship_changes TEXT,   -- JSON: [{target, from, to, justification}]
                state_changes TEXT,          -- JSON: 상태 변화 (부상, 경지 등)
                time_passed TEXT,            -- 경과 시간 (예: "같은 날 밤", "3일 후")
                reveals TEXT,                -- JSON: 밝혀진 사실/복선 회수
                causal_links TEXT,           -- [V60.82] JSON: 인과관계 링크
                karma_matrix TEXT,           -- [V60.82] JSON: 카르마 매트릭스
                knowledge_map TEXT,          -- [V60.82] JSON: 지식 맵 (목격자/오해자)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # [V60.82] 기존 테이블에 새 컬럼 추가 (마이그레이션)
        # [V64.P4] sqlite3.OperationalError: column already exists — expected during migration
        # [TF-R3-XC-01] "already exists" 외 OperationalError는 재발생
        for _col_name in ("causal_links", "karma_matrix", "knowledge_map"):
            try:
                self.cursor.execute(f"ALTER TABLE episode_bibles ADD COLUMN {_col_name} TEXT")  # noqa: S608
            except sqlite3.OperationalError as _e:
                if "duplicate column" not in str(_e).lower() and "already exists" not in str(_e).lower():
                    raise
                logging.debug(f"[SILENT] ALTER TABLE {_col_name}: column already exists")

        # 11. [Phase 3-5A] NPC 변경 이력 (append-only)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS npc_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                npc_name TEXT NOT NULL,
                episode_no INTEGER,
                arc_no INTEGER,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                change_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_npc_history_name ON npc_history(npc_name)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_npc_history_arc ON npc_history(arc_no)")
        # [LM-Tier TF-D] reason 컬럼 마이그레이션
        try:
            self.cursor.execute("ALTER TABLE npc_history ADD COLUMN reason TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # 이미 존재

        # 13. [Phase 3-B] 크로스 에피소드 문장 핑거프린트
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episode_sentence_hashes (
                episode_number INTEGER NOT NULL,
                sentence_hash TEXT NOT NULL,
                sentence_preview TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (episode_number, sentence_hash)
            )
        """)
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_episode_sentence_hashes_hash ON episode_sentence_hashes(sentence_hash)"
        )

        # 14. [D Step 3] 에피소드 만족도 태깅
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episode_satisfaction_tags (
                ep_num INTEGER PRIMARY KEY,
                primary_tag TEXT NOT NULL,
                satisfaction_score INTEGER DEFAULT 5,
                protagonist_agency TEXT DEFAULT '자력',
                frustration_flag INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # 15. [D-4] Director 앙상블 선택 기록
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS director_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ep_num INTEGER NOT NULL,
                round_num INTEGER NOT NULL,
                selected_label TEXT NOT NULL,
                selected_strategy TEXT,
                verdict TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                selection_reason TEXT,
                candidate_count INTEGER DEFAULT 3,
                fix_scope TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_director_selections_ep ON director_selections(ep_num)")
        # [A-3] fix_scope 컬럼 마이그레이션 (기존 DB 호환)
        try:
            self.cursor.execute("ALTER TABLE director_selections ADD COLUMN fix_scope TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # 이미 존재

        # [Log-3] Add advisory_warnings column for director selection correlation analysis
        try:
            self.cursor.execute("ALTER TABLE director_selections ADD COLUMN advisory_warnings TEXT")
        except sqlite3.OperationalError:
            pass  # already exists

        # [Log-1] Per-call LLM telemetry
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                ts TEXT NOT NULL,
                stage INTEGER,
                ep_num INTEGER,
                agent_name TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_chars INTEGER,
                response_chars INTEGER,
                duration_ms INTEGER,
                success INTEGER NOT NULL DEFAULT 1,
                error_type TEXT,
                error_msg TEXT,
                verdict TEXT,
                context_tag TEXT,
                prompt_snippet TEXT,
                response_snippet TEXT,
                thinking_snippet TEXT
            )
            """
        )
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_calls_agent ON llm_calls(agent_name)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_calls_ep ON llm_calls(ep_num)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_calls_ts ON llm_calls(ts)")
        # [Log-Phase2] Existing DB compatibility migration
        for _col in ("prompt_snippet", "response_snippet", "thinking_snippet"):
            try:
                self.cursor.execute(f"ALTER TABLE llm_calls ADD COLUMN {_col} TEXT")
                self.conn.commit()
            except Exception as _e:
                logging.debug("[DBManager] llm_calls 컬럼 마이그레이션 스킵(%s): %s", _col, _e)

        # [Log-2] Stage-level attempt telemetry
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stage_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                ts TEXT NOT NULL,
                stage INTEGER NOT NULL,
                ep_num INTEGER,
                arc_num INTEGER,
                attempt_num INTEGER NOT NULL DEFAULT 1,
                verdict TEXT NOT NULL,
                score INTEGER,
                failure_category TEXT,
                reject_reason TEXT,
                fix_scope TEXT,
                model TEXT,
                duration_ms INTEGER,
                advisory_flags TEXT,
                generation_method TEXT,
                prompt_version TEXT
            )
            """
        )
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_stage_attempts_stage_ep ON stage_attempts(stage, ep_num)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_stage_attempts_verdict ON stage_attempts(verdict)")
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_stage_attempts_category ON stage_attempts(failure_category)"
        )
        # [TF-60][OPT-3] stage_attempts 컬럼 마이그레이션 (기존 DB 호환)
        for _col in ("generation_method", "prompt_version"):
            try:
                self.cursor.execute(f"ALTER TABLE stage_attempts ADD COLUMN {_col} TEXT")
                self.conn.commit()
            except Exception as _e:
                logging.debug("[DBManager] stage_attempts %s 마이그레이션 스킵: %s", _col, _e)

        # 16. [Phase 6] 비용 추적 로그
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                scope_type TEXT NOT NULL CHECK(scope_type IN ('arc', 'episode', 'session')),
                scope_id INTEGER DEFAULT 0,
                total_calls INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_cost_usd REAL DEFAULT 0.0,
                model_breakdown TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_cost_log_scope ON cost_log(scope_type, scope_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_cost_log_session ON cost_log(session_id)")
        # 17. [DB-MERGE] 벡터 검색 테이블
        if self._vec_available:
            self.cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_episodes
                USING vec0(embedding float[3072])
            """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episode_meta (
                ep_num       INTEGER PRIMARY KEY,
                summary      TEXT,
                causal_data  TEXT,
                arc_no       INTEGER,
                event_types  TEXT,
                entity_names TEXT,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # [Hybrid-P2] FTS5 전문 검색 테이블 (vec_memory 공유 모드와 동기화)
        self.cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS episode_fts
            USING fts5(
                summary,
                event_types,
                entity_names,
                tokenize='unicode61 remove_diacritics 2'
            )
        """)
        # [Tier4-14] episode_meta / causal_graph index tuning
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_episode_meta_arc_no ON episode_meta(arc_no)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_causal_graph_ep_num ON causal_graph(ep_num)")

        # 18. [TF-I24] 에피소드 호흡 분석 기록
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episode_pacing (
                ep_num INTEGER PRIMARY KEY,
                pacing_score INTEGER DEFAULT 50,
                dialogue_ratio REAL DEFAULT 0.0,
                scene_break_count INTEGER DEFAULT 0,
                avg_sentence_length REAL DEFAULT 0.0,
                short_sentence_ratio REAL DEFAULT 0.0,
                long_sentence_ratio REAL DEFAULT 0.0,
                issues TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episode_quality_labels (
                ep_num INTEGER PRIMARY KEY,
                score INTEGER DEFAULT 0,
                verdict TEXT DEFAULT '',
                selection_reason TEXT DEFAULT '',
                open_review TEXT DEFAULT '',
                score_breakdown TEXT DEFAULT '{}',
                consistency_checklist TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_episode_quality_score ON episode_quality_labels(score)")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episode_quality_signals (
                ep_num INTEGER PRIMARY KEY,
                ced_score REAL DEFAULT 0.0,
                ai_slop_score REAL DEFAULT 0.0,
                ai_slop_hits TEXT DEFAULT '[]',
                compression_ratio REAL DEFAULT 0.0,
                burstiness REAL DEFAULT 0.0,
                complexity REAL DEFAULT 0.0,
                signal_summary TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_episode_quality_signals_created_at ON episode_quality_signals(created_at)"
        )
        # [DB-Eff-P1] character_voice 프로필 테이블
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS character_voice (
                npc_name TEXT PRIMARY KEY,
                profile_data TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # [DB-Eff-P1] foreshadow 복선 테이블
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS foreshadow (
                seed_id TEXT PRIMARY KEY,
                category TEXT,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'planted',
                planted_ep INTEGER,
                resolved_ep INTEGER,
                data TEXT,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_foreshadow_status ON foreshadow(status)")

        # [Phase1-L0] 캐노니컬 팩트 테이블 (NPC 고정 속성 + 수치 팩트 영속화)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS canonical_facts (
                fact_key    TEXT PRIMARY KEY,
                fact_type   TEXT NOT NULL,
                value_json  TEXT,
                first_ep    INTEGER,
                last_ep     INTEGER,
                confidence  TEXT DEFAULT 'confirmed'
            )
        """)

        # [Phase3-Timeline] 타임라인 전용 테이블 (WorldState 20개 제한 제거)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline_entries (
                ep_no        INTEGER PRIMARY KEY,
                story_date   TEXT,
                elapsed_days INTEGER,
                time_note    TEXT
            )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_ep_no ON timeline_entries(ep_no)")

        # [Graph-Layer] NPC 간 관계 영속화 (메모리 50쌍 한도 우회)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS npc_relationship_edges (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                npc1        TEXT NOT NULL,
                npc2        TEXT NOT NULL,
                relation    TEXT,
                since_ep    INTEGER,
                updated_ep  INTEGER,
                arc_no      INTEGER,
                UNIQUE(npc1, npc2)
            )
        """)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_npc_rel_npc1 ON npc_relationship_edges(npc1)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_npc_rel_npc2 ON npc_relationship_edges(npc2)")

        # [LM-D] NPC 관계 변경 이력 (append-only)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS npc_relationship_history (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                npc1           TEXT NOT NULL,
                npc2           TEXT NOT NULL,
                old_relation   TEXT,
                new_relation   TEXT NOT NULL,
                change_ep      INTEGER,
                arc_no         INTEGER,
                change_reason  TEXT,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rel_hist_pair ON npc_relationship_history(npc1, npc2, change_ep)"
        )

        # [Graph-Layer] Arc 인과 의존성
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS arc_dependencies (
                from_arc_no  INTEGER NOT NULL,
                to_arc_no    INTEGER NOT NULL,
                dep_type     TEXT NOT NULL DEFAULT 'causes',
                description  TEXT,
                PRIMARY KEY (from_arc_no, to_arc_no)
            )
        """)

        self.conn.commit()
        # [DB-MERGE] 기존 vec_memory.db 1회성 마이그레이션
        self._migrate_vec_memory_db()
        # [Phase3-Timeline] WorldState.timeline 배열 → DB 1회 마이그레이션
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
            if self.conn:
                try:
                    if self.conn.in_transaction:
                        logging.warning("[B4-P1-3] close() 호출 시 미완료 트랜잭션 발견 — rollback 수행")
                        self.conn.rollback()
                    self.conn.close()
                finally:
                    self.conn = None
                    self.cursor = None

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
                ep = link.get("ep") or current_ep
                serialized = json.dumps(link, ensure_ascii=False)
                data_to_insert.append((ep, serialized))
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

    def reset_after(self, target_ep) -> None:
        """전체 테이블 리셋 및 롤백"""
        with self._lock:
            try:
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
                self.cursor.execute("DELETE FROM director_selections WHERE ep_num >= ?", (target_ep,))
                self.cursor.execute("DELETE FROM episode_pacing WHERE ep_num >= ?", (target_ep,))
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
        # [TF-24] VACUUM은 lock 밖에서 실행 (장시간 lock 점유 방지)
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

            cur = self.cursor.execute("SELECT COUNT(*) as cnt FROM director_selections WHERE ep_num >= ?", (target_ep,))
            impact["director_selections"] = cur.fetchone()["cnt"]

            # [LM-D] 관계 변경 이력 영향도
            cur = self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM npc_relationship_history WHERE change_ep >= ?", (target_ep,)
            )
            impact["npc_relationship_history"] = cur.fetchone()["cnt"]

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
    ) -> None:
        """Persist director selection result."""
        with self._lock:
            nested = self.conn.in_transaction
            _adv_json = json.dumps(advisory_warnings, ensure_ascii=False) if advisory_warnings else None
            self.cursor.execute(
                "INSERT INTO director_selections "
                "(ep_num, round_num, selected_label, selected_strategy, verdict, score, "
                "selection_reason, candidate_count, fix_scope, advisory_warnings) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ep_num,
                    round_num,
                    selected_label,
                    selected_strategy,
                    verdict,
                    score,
                    selection_reason[:200] if selection_reason else "",
                    candidate_count,
                    fix_scope or "",
                    _adv_json,
                ),
            )
            if not nested:
                self.commit()

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

    def get_recent_episode_scores(self, before_ep: int, lookback: int = 5) -> list[dict]:
        """최근 PASS 계열 에피소드 점수를 오래된 순으로 반환."""
        with self._lock:
            cur = self.cursor.execute(
                """
                SELECT ds.ep_num, ds.score, ds.verdict
                FROM director_selections ds
                JOIN (
                    SELECT ep_num, MAX(id) AS last_id
                    FROM director_selections
                    WHERE ep_num < ? AND verdict IN ('PASS', 'PASS_WITH_FIX')
                    GROUP BY ep_num
                    ORDER BY ep_num DESC
                    LIMIT ?
                ) latest ON latest.last_id = ds.id
                ORDER BY ds.ep_num ASC
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
            "SELECT stage, ep_num, arc_num, attempt_num, verdict, score, failure_category, reject_reason, advisory_flags, prompt_version "
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
        prompt_snippet: str | None = None,
        response_snippet: str | None = None,
        thinking_snippet: str | None = None,
    ) -> None:
        """[Log-1] Save one LLM call record in non-blocking mode."""
        try:
            ts = datetime.now().isoformat(timespec="seconds")
            # [Log-Phase2] Keep DB size bounded: snippets only for failed calls.
            _prompt_snip = str(prompt_snippet)[:3000] if (not success and prompt_snippet) else None
            _response_snip = str(response_snippet) if (not success and response_snippet) else None
            # [TF-58] thinking은 성공 호출에서도 저장 (Director 구조 결함 분석용), 5000자 제한
            _thinking_snip = str(thinking_snippet)[:5000] if thinking_snippet else None
            with self._lock:
                self.cursor.execute(
                    """INSERT INTO llm_calls
                       (session_id, ts, stage, ep_num, agent_name, model,
                        prompt_chars, response_chars, duration_ms,
                        success, error_type, error_msg, verdict, context_tag,
                        prompt_snippet, response_snippet, thinking_snippet)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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
        generation_method: str | None = None,
        prompt_version: str | None = None,
    ) -> None:
        """[Log-2] Save one stage attempt record in non-blocking mode."""
        try:
            ts = datetime.now().isoformat(timespec="seconds")
            _advisory_json = json.dumps(advisory_flags, ensure_ascii=False) if advisory_flags else None
            with self._lock:
                self.cursor.execute(
                    """INSERT INTO stage_attempts
                       (session_id, ts, stage, ep_num, arc_num, attempt_num,
                        verdict, score, failure_category, reject_reason,
                        fix_scope, model, duration_ms, advisory_flags, generation_method, prompt_version)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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
                        generation_method,
                        prompt_version,
                    ),
                )
                self.conn.commit()
        except Exception as _e:
            logging.debug("[stage_attempts] save_stage_attempt failed (non-blocking): %s", _e)

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
