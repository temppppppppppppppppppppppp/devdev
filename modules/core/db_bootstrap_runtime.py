import logging
import re
import sqlite3
import traceback
from typing import TYPE_CHECKING

from .constants import MARTIAL_METRICS

if TYPE_CHECKING:
    from .db_manager import DBManager


class DBBootstrapRuntime:
    """Boot-time schema/bootstrap authority for DBManager."""

    def __init__(self, owner: "DBManager") -> None:
        self.owner = owner

    def boot(self) -> None:
        owner = self.owner
        owner.conn = owner._connect_with_integrity_recovery()
        owner.cursor = owner.conn.cursor()

        self._configure_connection_runtime()
        self._load_sqlite_vec_extension()
        self._create_foundation_tables()
        self._create_selection_and_logging_tables()
        self._create_retrieval_and_quality_tables()
        owner.conn.commit()

    def _configure_connection_runtime(self) -> None:
        cursor = self.owner.cursor
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
        except sqlite3.OperationalError as exc:
            logging.warning(f"[DBManager] WAL mode setup failed (non-blocking): {exc}")

    def _load_sqlite_vec_extension(self) -> None:
        owner = self.owner
        owner._vec_available = False
        try:
            import sqlite_vec as _sv

            owner.conn.enable_load_extension(True)
            _sv.load(owner.conn)
            owner.conn.enable_load_extension(False)
            owner._vec_available = True
        except ImportError:
            logging.info("[DBManager] sqlite-vec unavailable; vector tables skipped")
        except Exception as exc:
            logging.warning(f"[DBManager] sqlite-vec load failed: {exc}")

    def _create_foundation_tables(self) -> None:
        self._create_sync_and_anchor_tables()
        self._create_story_state_tables()
        self._create_reflexion_and_martial_tables()
        self._create_seed_and_reference_tables()
        self._create_bible_and_history_tables()
        self._create_sentence_and_selection_tables()

    def _create_sync_and_anchor_tables(self) -> None:
        owner = self.owner
        cursor = owner.cursor

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_status (
                ep_num INTEGER PRIMARY KEY,
                vector_synced INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        owner.conn.commit()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS anchors (
                key TEXT PRIMARY KEY,
                data TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        owner.conn.commit()

    def _create_story_state_tables(self) -> None:
        cursor = self.owner.cursor

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS blueprints (
                ep_num INTEGER PRIMARY KEY,
                data TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS state_logs (
                ep_num INTEGER PRIMARY KEY,
                data TEXT,
                summary TEXT
            )
            """
        )
        self._ensure_state_logs_summary_column()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS causal_graph (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ep_num INTEGER,
                data TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS karma_status (
                npc_name TEXT PRIMARY KEY,
                misunderstanding INTEGER DEFAULT 0,
                obsession INTEGER DEFAULT 0,
                last_updated_ep INTEGER
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS manuscripts (
                ep_num INTEGER PRIMARY KEY,
                title TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        try:
            cursor.execute("ALTER TABLE manuscripts ADD COLUMN hud_snapshot TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

    def _ensure_state_logs_summary_column(self) -> None:
        owner = self.owner
        cursor = owner.cursor
        try:
            cursor.execute("PRAGMA table_info(state_logs)")
            existing_cols = {row["name"] for row in cursor.fetchall()}
            if "summary" not in existing_cols:
                cursor.execute("ALTER TABLE state_logs ADD COLUMN summary TEXT")
                owner.conn.commit()
        except sqlite3.OperationalError as exc:
            if "no such table" not in str(exc).lower():
                logging.warning(f"[WARNING] state_logs migration failed: {exc}")
                try:
                    owner.conn.rollback()
                except Exception as rollback_exc:
                    logging.debug(f"[SILENT] state_logs rollback: {rollback_exc}")

    def _create_reflexion_and_martial_tables(self) -> None:
        owner = self.owner
        cursor = owner.cursor

        cursor.execute(
            """
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
            """
        )

        validated_metrics = self._resolve_validated_martial_metrics()
        columns_def = ", ".join([f"{metric} TEXT" for metric in validated_metrics])
        cursor.execute(f"CREATE TABLE IF NOT EXISTS martial_tracker (ep_num INTEGER PRIMARY KEY, {columns_def})")

        try:
            cursor.execute("PRAGMA table_info(martial_tracker)")
            existing_columns = {row["name"] for row in cursor.fetchall()}
            for metric in validated_metrics:
                if metric not in existing_columns:
                    logging.info(" [DB Migration] adding martial_tracker column '%s'", metric)
                    cursor.execute(f"ALTER TABLE martial_tracker ADD COLUMN {metric} TEXT")
            owner.conn.commit()
        except sqlite3.IntegrityError as exc:
            logging.warning(" [HIGH] migration integrity error: %s", exc)
        except sqlite3.OperationalError as exc:
            error_str = str(exc).lower()
            if "locked" in error_str:
                logging.warning(" [HIGH] DB locked during migration: %s", exc)
            elif "disk" in error_str or "i/o" in error_str:
                logging.warning(" [CRITICAL] disk I/O error during migration: %s", exc)
            else:
                logging.warning(" [HIGH] migration operational error: %s", exc)
        except Exception as exc:
            logging.warning(" [WARN] migration unexpected error: %s", exc)
            logging.info("-> detail: %s", traceback.format_exc()[:200])

    def _resolve_validated_martial_metrics(self) -> list[str]:
        safe_column_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        validated_metrics = [metric for metric in MARTIAL_METRICS if safe_column_pattern.match(metric)]
        if len(validated_metrics) != len(MARTIAL_METRICS):
            invalid = set(MARTIAL_METRICS) - set(validated_metrics)
            logging.warning(f"[WARNING] invalid martial tracker column names ignored: {invalid}")
        return validated_metrics

    def _create_seed_and_reference_tables(self) -> None:
        cursor = self.owner.cursor

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS seeds (
                seed_id TEXT PRIMARY KEY,
                category TEXT,
                content TEXT,
                status TEXT DEFAULT 'active',
                planted_ep INTEGER,
                recovered_ep INTEGER
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_seeds_status ON seeds(status)")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS encyclopedia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                item TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(item)
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_encyclopedia_category ON encyclopedia(category)")

    def _create_bible_and_history_tables(self) -> None:
        cursor = self.owner.cursor

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS episode_bibles (
                ep_num INTEGER PRIMARY KEY,
                new_items TEXT,
                lost_items TEXT,
                new_npcs TEXT,
                npc_deaths TEXT,
                relationship_changes TEXT,
                state_changes TEXT,
                time_passed TEXT,
                reveals TEXT,
                causal_links TEXT,
                karma_matrix TEXT,
                knowledge_map TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for col_name in ("causal_links", "karma_matrix", "knowledge_map"):
            try:
                cursor.execute(f"ALTER TABLE episode_bibles ADD COLUMN {col_name} TEXT")
            except sqlite3.OperationalError as exc:
                lowered = str(exc).lower()
                if "duplicate column" not in lowered and "already exists" not in lowered:
                    raise
                logging.debug("[SILENT] ALTER TABLE %s: column already exists", col_name)

        cursor.execute(
            """
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
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_npc_history_name ON npc_history(npc_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_npc_history_arc ON npc_history(arc_no)")
        try:
            cursor.execute("ALTER TABLE npc_history ADD COLUMN reason TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

    def _create_sentence_and_selection_tables(self) -> None:
        cursor = self.owner.cursor

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS episode_sentence_hashes (
                episode_number INTEGER NOT NULL,
                sentence_hash TEXT NOT NULL,
                sentence_preview TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (episode_number, sentence_hash)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_episode_sentence_hashes_hash ON episode_sentence_hashes(sentence_hash)"
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS episode_satisfaction_tags (
                ep_num INTEGER PRIMARY KEY,
                primary_tag TEXT NOT NULL,
                satisfaction_score INTEGER DEFAULT 5,
                protagonist_agency TEXT DEFAULT '자력',
                frustration_flag INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS director_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage INTEGER,
                ep_num INTEGER NOT NULL,
                round_num INTEGER NOT NULL,
                selected_label TEXT NOT NULL,
                selected_strategy TEXT,
                verdict TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                selection_reason TEXT,
                candidate_count INTEGER DEFAULT 3,
                fix_scope TEXT DEFAULT '',
                attempt_key TEXT DEFAULT '',
                candidate_key TEXT DEFAULT '',
                content_hash TEXT DEFAULT '',
                artifact_path TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_director_selections_ep ON director_selections(ep_num)")
        for statement in (
            "ALTER TABLE director_selections ADD COLUMN fix_scope TEXT DEFAULT ''",
            "ALTER TABLE director_selections ADD COLUMN advisory_warnings TEXT",
            "ALTER TABLE director_selections ADD COLUMN stage INTEGER",
            "ALTER TABLE director_selections ADD COLUMN verdict_reason TEXT DEFAULT ''",
            "ALTER TABLE director_selections ADD COLUMN pre_firewall_score INTEGER DEFAULT 0",
            "ALTER TABLE director_selections ADD COLUMN firewall_triggered INTEGER DEFAULT 0",
            "ALTER TABLE director_selections ADD COLUMN firewall_reason TEXT DEFAULT ''",
            "ALTER TABLE director_selections ADD COLUMN attempt_key TEXT DEFAULT ''",
        ):
            try:
                cursor.execute(statement)
            except sqlite3.OperationalError:
                pass
        for col in ("candidate_key", "content_hash", "artifact_path"):
            try:
                cursor.execute(f"ALTER TABLE director_selections ADD COLUMN {col} TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass
        self.owner._ensure_columns_exist(
            "director_selections",
            self.owner._column_def_pairs(
                ("director_thinking", "TEXT"),
                ("initial_verdict", "TEXT DEFAULT ''"),
                ("final_verdict", "TEXT DEFAULT ''"),
                ("downstream_override_applied", "INTEGER DEFAULT 0"),
            ),
            log_label="director_selections",
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_director_selections_stage_ep ON director_selections(stage, ep_num)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_director_selections_attempt_key ON director_selections(attempt_key)"
        )

    def _create_adjunct_retention_tables(self) -> None:
        """Adjunct raw-payload retention for max-retention policy."""
        cursor = self.owner.cursor
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attempt_raw_rationale (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_key TEXT NOT NULL,
                stage INTEGER,
                ep_num INTEGER,
                payload_kind TEXT NOT NULL,
                payload TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_arr_attempt_key ON attempt_raw_rationale(attempt_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_arr_kind ON attempt_raw_rationale(payload_kind)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_arr_stage_ep ON attempt_raw_rationale(stage, ep_num)")

    def _create_selection_and_logging_tables(self) -> None:
        self._create_adjunct_retention_tables()
        self._create_llm_call_tables()
        self._create_stage_attempt_tables()
        self._create_ui_event_tables()
        self._create_cost_log_tables()

    def _create_llm_call_tables(self) -> None:
        owner = self.owner
        cursor = owner.cursor

        cursor.execute(
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
                input_tokens INTEGER,
                output_tokens INTEGER,
                cached_tokens INTEGER,
                thinking_tokens INTEGER,
                total_cost_usd REAL,
                prompt_snippet TEXT,
                response_snippet TEXT,
                thinking_snippet TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_calls_agent ON llm_calls(agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_calls_ep ON llm_calls(ep_num)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_calls_ts ON llm_calls(ts)")
        owner._ensure_columns_exist(
            "llm_calls",
            owner._column_def_pairs(
                ("input_tokens", "INTEGER"),
                ("output_tokens", "INTEGER"),
                ("cached_tokens", "INTEGER"),
                ("thinking_tokens", "INTEGER"),
                ("total_cost_usd", "REAL"),
                ("prompt_snippet", "TEXT"),
                ("response_snippet", "TEXT"),
                ("thinking_snippet", "TEXT"),
                # [TM-1] timing decomposition — duration_ms = ask wall clock (compat),
                # api_elapsed_ms = raw API RTT for the final successful _generate_content call
                ("api_elapsed_ms", "INTEGER"),
                ("retry_count", "INTEGER"),
                ("continuation_count", "INTEGER"),
            ),
            log_label="llm_calls",
        )

    def _create_stage_attempt_tables(self) -> None:
        owner = self.owner
        cursor = owner.cursor

        cursor.execute(
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
                attempt_key TEXT,
                generation_method TEXT,
                prompt_version TEXT,
                candidate_key TEXT,
                content_hash TEXT,
                artifact_path TEXT,
                selection_reason TEXT,
                verdict_reason TEXT,
                open_review TEXT,
                fix_scope_reasoning TEXT,
                runtime_advisory TEXT,
                retry_directives TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stage_attempts_stage_ep ON stage_attempts(stage, ep_num)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stage_attempts_verdict ON stage_attempts(verdict)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stage_attempts_category ON stage_attempts(failure_category)")
        owner._ensure_columns_exist(
            "stage_attempts",
            owner._column_def_pairs(
                ("generation_method", "TEXT"),
                ("prompt_version", "TEXT"),
                ("attempt_key", "TEXT"),
                ("candidate_key", "TEXT"),
                ("content_hash", "TEXT"),
                ("artifact_path", "TEXT"),
                ("selection_reason", "TEXT"),
                ("verdict_reason", "TEXT"),
                ("open_review", "TEXT"),
                ("fix_scope_reasoning", "TEXT"),
                ("runtime_advisory", "TEXT"),
                ("retry_directives", "TEXT"),
                ("initial_verdict", "TEXT"),
                ("score_breakdown", "TEXT"),
                ("is_patch", "INTEGER DEFAULT 0"),
                ("is_patch_fallback", "INTEGER DEFAULT 0"),
                ("patch_strategy", "TEXT"),
                ("director_quality_passed", "INTEGER DEFAULT 0"),
                ("downstream_override_applied", "INTEGER DEFAULT 0"),
                ("primary_failure_layer", "TEXT"),
            ),
            log_label="stage_attempts",
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stage_attempts_attempt_key ON stage_attempts(attempt_key)")

    def _create_ui_event_tables(self) -> None:
        cursor = self.owner.cursor

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ui_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                ts TEXT NOT NULL,
                seq INTEGER,
                stage INTEGER,
                ep_num INTEGER,
                arc_num INTEGER,
                round_num INTEGER,
                attempt_key TEXT,
                component TEXT NOT NULL,
                event_kind TEXT NOT NULL,
                level TEXT NOT NULL,
                render_format TEXT NOT NULL DEFAULT 'text',
                message TEXT NOT NULL,
                visible INTEGER NOT NULL DEFAULT 1,
                selection_value TEXT,
                prompt_id TEXT,
                artifact_path TEXT,
                meta_json TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ui_events_session ON ui_events(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ui_events_stage_ep ON ui_events(stage, ep_num)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ui_events_attempt_key ON ui_events(attempt_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ui_events_component ON ui_events(component)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ui_events_ts ON ui_events(ts)")

    def _create_cost_log_tables(self) -> None:
        cursor = self.owner.cursor

        cursor.execute(
            """
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
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cost_log_scope ON cost_log(scope_type, scope_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cost_log_session ON cost_log(session_id)")

    def _create_retrieval_and_quality_tables(self) -> None:
        self._create_episode_retrieval_tables()
        self._create_episode_quality_tables()
        self._create_reference_world_tables()
        self._create_relationship_dependency_tables()

    def _create_episode_retrieval_tables(self) -> None:
        owner = self.owner
        cursor = owner.cursor

        if owner._vec_available:
            cursor.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_episodes
                USING vec0(embedding float[3072])
                """
            )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS episode_meta (
                ep_num       INTEGER PRIMARY KEY,
                summary      TEXT,
                causal_data  TEXT,
                arc_no       INTEGER,
                event_types  TEXT,
                entity_names TEXT,
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS episode_fts
            USING fts5(
                summary,
                event_types,
                entity_names,
                tokenize='unicode61 remove_diacritics 2'
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episode_meta_arc_no ON episode_meta(arc_no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_causal_graph_ep_num ON causal_graph(ep_num)")

    def _create_episode_quality_tables(self) -> None:
        cursor = self.owner.cursor

        cursor.execute(
            """
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
            """
        )
        cursor.execute(
            """
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
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episode_quality_score ON episode_quality_labels(score)")
        cursor.execute(
            """
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
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_episode_quality_signals_created_at ON episode_quality_signals(created_at)"
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS episode_quality_observations (
                ep_num INTEGER PRIMARY KEY,
                operator_label TEXT DEFAULT '',
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_episode_quality_observations_label ON episode_quality_observations(operator_label)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_episode_quality_observations_updated_at ON episode_quality_observations(updated_at)"
        )

    def _create_reference_world_tables(self) -> None:
        cursor = self.owner.cursor

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS character_voice (
                npc_name TEXT PRIMARY KEY,
                profile_data TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        cursor.execute(
            """
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
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_foreshadow_status ON foreshadow(status)")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS canonical_facts (
                fact_key    TEXT PRIMARY KEY,
                fact_type   TEXT NOT NULL,
                value_json  TEXT,
                first_ep    INTEGER,
                last_ep     INTEGER,
                confidence  TEXT DEFAULT 'confirmed'
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS timeline_entries (
                ep_no        INTEGER PRIMARY KEY,
                story_date   TEXT,
                elapsed_days INTEGER,
                time_note    TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_ep_no ON timeline_entries(ep_no)")

    def _create_relationship_dependency_tables(self) -> None:
        cursor = self.owner.cursor

        cursor.execute(
            """
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
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_npc_rel_npc1 ON npc_relationship_edges(npc1)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_npc_rel_npc2 ON npc_relationship_edges(npc2)")
        cursor.execute(
            """
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
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rel_hist_pair ON npc_relationship_history(npc1, npc2, change_ep)"
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS arc_dependencies (
                from_arc_no  INTEGER NOT NULL,
                to_arc_no    INTEGER NOT NULL,
                dep_type     TEXT NOT NULL DEFAULT 'causes',
                description  TEXT,
                PRIMARY KEY (from_arc_no, to_arc_no)
            )
            """
        )
