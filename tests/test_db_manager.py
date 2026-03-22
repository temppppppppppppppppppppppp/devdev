"""DBManager current-API regression tests."""

import json
import sqlite3
from unittest.mock import MagicMock

import pytest

from modules.core.db_bootstrap_runtime import DBBootstrapRuntime
from modules.core.db_manager import DBConnectionError, DBError, DBManager


@pytest.fixture
def db(tmp_path):
    manager = DBManager(tmp_path / "test.db")
    try:
        yield manager
    finally:
        manager.close()


def test_save_and_load_anchor(db):
    payload = {"key1": "value1", "nested": {"a": 1}}
    assert db.save_anchor("sample", payload) is True
    assert db.load_anchor("sample") == payload


def test_load_anchor_missing_default_behavior(db):
    assert db.load_anchor("missing_default") == {}
    assert db.load_anchor("missing_custom", default={"fallback": True}) == {"fallback": True}


def test_save_and_get_blueprint(db):
    blueprint = {"ep_num": 1, "title": "시작", "scenes": [{"scene_no": 1}]}
    db.save_blueprint(1, blueprint)
    loaded = db.get_blueprint(1)
    assert loaded["title"] == "시작"
    assert loaded["scenes"][0]["scene_no"] == 1


def test_save_and_get_manuscript_and_latest_episode_number(db):
    db.save_manuscript(1, "제목1", "내용1")
    db.save_manuscript(5, "제목5", "내용5")
    loaded = db.get_manuscript(5)
    assert loaded["title"] == "제목5"
    assert loaded["content"] == "내용5"
    # get_latest_episode_number는 "다음 회차 번호" 반환
    assert db.get_latest_episode_number() == 6


def test_transaction_rolls_back_on_exception(db):
    with pytest.raises(DBError):
        with db.transaction():
            db.save_anchor("tx_key", {"v": 1})
            raise RuntimeError("rollback trigger")

    assert db.load_anchor("tx_key", default=None) == {}


def test_save_stage_attempt_respects_outer_transaction_rollback(db):
    with pytest.raises(DBError):
        with db.transaction():
            persisted = db.save_stage_attempt(
                stage=4,
                verdict="PASS",
                attempt_num=1,
                ep_num=22,
                arc_num=2,
                score=91,
                attempt_key="s4:ep22:arc2:a1:sess_tx",
                candidate_key="A|balanced",
                content_hash="hash-tx",
                artifact_path="logs/artifacts/stage4/ep_0022/attempt_01/final_manuscript__A_balanced.txt",
            )
            assert persisted is True
            raise RuntimeError("rollback trigger")

    row = db.conn.execute(
        "SELECT COUNT(*) AS cnt FROM stage_attempts WHERE attempt_key = 's4:ep22:arc2:a1:sess_tx'"
    ).fetchone()
    assert row["cnt"] == 0


def test_reset_after_commit_false_keeps_changes_uncommitted(db):
    db.save_manuscript(1, "제목1", "내용1")

    db.reset_after(1, commit=False)

    assert db.conn.in_transaction is True
    other = sqlite3.connect(db.db_path)
    try:
        assert other.execute("SELECT COUNT(*) FROM manuscripts").fetchone()[0] == 1
    finally:
        other.close()
    db.conn.rollback()


def test_close_then_query_raises_connection_error(tmp_path):
    manager = DBManager(tmp_path / "closed.db")
    manager.close()
    with pytest.raises(DBConnectionError):
        manager.execute_query("SELECT 1")


def test_db_manager_attaches_bootstrap_runtime(db):
    assert db.bootstrap_runtime is not None
    assert db.bootstrap_runtime.owner is db


def test_boot_db_delegates_to_bootstrap_runtime_and_owner_migrations():
    manager = DBManager.__new__(DBManager)
    manager.bootstrap_runtime = MagicMock()
    manager._migrate_vec_memory_db = MagicMock()
    manager._migrate_world_state_timeline_if_needed = MagicMock()

    DBManager._boot_db(manager)

    manager.bootstrap_runtime.boot.assert_called_once_with()
    manager._migrate_vec_memory_db.assert_called_once_with()
    manager._migrate_world_state_timeline_if_needed.assert_called_once_with()


def test_create_foundation_tables_delegates_to_family_helpers():
    runtime = DBBootstrapRuntime.__new__(DBBootstrapRuntime)
    runtime.owner = MagicMock()
    runtime._create_sync_and_anchor_tables = MagicMock()
    runtime._create_story_state_tables = MagicMock()
    runtime._create_reflexion_and_martial_tables = MagicMock()
    runtime._create_seed_and_reference_tables = MagicMock()
    runtime._create_bible_and_history_tables = MagicMock()
    runtime._create_sentence_and_selection_tables = MagicMock()

    DBBootstrapRuntime._create_foundation_tables(runtime)

    runtime._create_sync_and_anchor_tables.assert_called_once_with()
    runtime._create_story_state_tables.assert_called_once_with()
    runtime._create_reflexion_and_martial_tables.assert_called_once_with()
    runtime._create_seed_and_reference_tables.assert_called_once_with()
    runtime._create_bible_and_history_tables.assert_called_once_with()
    runtime._create_sentence_and_selection_tables.assert_called_once_with()


def test_resolve_validated_martial_metrics_filters_invalid_names(monkeypatch):
    runtime = DBBootstrapRuntime.__new__(DBBootstrapRuntime)
    monkeypatch.setattr(
        "modules.core.db_bootstrap_runtime.MARTIAL_METRICS",
        ["qi_flow", "bad metric", "123bad", "sword_intent"],
    )

    metrics = DBBootstrapRuntime._resolve_validated_martial_metrics(runtime)

    assert metrics == ["qi_flow", "sword_intent"]


def test_create_selection_and_logging_tables_delegates_to_family_helpers():
    runtime = DBBootstrapRuntime.__new__(DBBootstrapRuntime)
    runtime._create_llm_call_tables = MagicMock()
    runtime._create_stage_attempt_tables = MagicMock()
    runtime._create_ui_event_tables = MagicMock()
    runtime._create_cost_log_tables = MagicMock()

    DBBootstrapRuntime._create_selection_and_logging_tables(runtime)

    runtime._create_llm_call_tables.assert_called_once_with()
    runtime._create_stage_attempt_tables.assert_called_once_with()
    runtime._create_ui_event_tables.assert_called_once_with()
    runtime._create_cost_log_tables.assert_called_once_with()


def test_create_retrieval_and_quality_tables_delegates_to_family_helpers():
    runtime = DBBootstrapRuntime.__new__(DBBootstrapRuntime)
    runtime._create_episode_retrieval_tables = MagicMock()
    runtime._create_episode_quality_tables = MagicMock()
    runtime._create_reference_world_tables = MagicMock()
    runtime._create_relationship_dependency_tables = MagicMock()

    DBBootstrapRuntime._create_retrieval_and_quality_tables(runtime)

    runtime._create_episode_retrieval_tables.assert_called_once_with()
    runtime._create_episode_quality_tables.assert_called_once_with()
    runtime._create_reference_world_tables.assert_called_once_with()
    runtime._create_relationship_dependency_tables.assert_called_once_with()


def test_get_all_episode_bibles_handles_malformed_json(db):
    db.save_episode_bible(1, {"new_items": ["철검"], "time_passed": "1일"})
    db.cursor.execute(
        "INSERT OR REPLACE INTO episode_bibles (ep_num, new_items, lost_items, new_npcs, npc_deaths, "
        "relationship_changes, state_changes, time_passed, reveals) "
        "VALUES (2, '{broken', '[]', '[]', '[]', '[]', '{}', '', '[]')"
    )
    db.conn.commit()

    rows = db.get_all_episode_bibles()
    assert len(rows) == 2
    assert rows[0]["new_items"] == ["철검"]
    assert rows[1]["new_items"] == []


def test_get_episode_bibles_before_filters_rows(db):
    db.save_episode_bible(1, {"reveals": ["비밀"], "knowledge_map": {"new_witnesses": ["목격"]}})
    db.save_episode_bible(5, {"reveals": ["현재 화"], "knowledge_map": {"new_misled": ["오해"]}})

    rows = db.get_episode_bibles_before(5)

    assert len(rows) == 1
    assert rows[0]["ep_num"] == 1
    assert rows[0]["reveals"] == ["비밀"]
    assert rows[0]["knowledge_map"]["new_witnesses"] == ["목격"]


def test_episode_meta_arc_no_index_exists(db):
    rows = db.cursor.execute("PRAGMA index_list('episode_meta')").fetchall()
    names = {row["name"] for row in rows}
    assert "idx_episode_meta_arc_no" in names


def test_causal_graph_ep_num_index_exists(db):
    rows = db.cursor.execute("PRAGMA index_list('causal_graph')").fetchall()
    names = {row["name"] for row in rows}
    assert "idx_causal_graph_ep_num" in names


def test_save_llm_call_persists_token_and_cost_fields(db):
    db.save_llm_call(
        agent_name="chief_writer",
        model="gemini-2.5-pro",
        prompt_chars=100,
        response_chars=200,
        duration_ms=321,
        success=True,
        session_id="sess-1",
        input_tokens=120,
        output_tokens=80,
        cached_tokens=20,
        thinking_tokens=10,
        total_cost_usd=0.0123,
    )

    row = db.cursor.execute(
        """
        SELECT input_tokens, output_tokens, cached_tokens, thinking_tokens, total_cost_usd
        FROM llm_calls
        WHERE session_id = 'sess-1'
        """
    ).fetchone()

    assert row["input_tokens"] == 120
    assert row["output_tokens"] == 80
    assert row["cached_tokens"] == 20
    assert row["thinking_tokens"] == 10
    assert row["total_cost_usd"] == pytest.approx(0.0123)


def test_runtime_telemetry_writes_are_blocked_after_begin_shutdown(db):
    db.begin_shutdown()

    db.save_llm_call(
        agent_name="chief_writer",
        model="gemini-2.5-pro",
        prompt_chars=100,
        response_chars=200,
        duration_ms=321,
        success=True,
        session_id="sess-frozen",
    )
    director_written = db.save_stage_attempt(
        stage=4,
        verdict="PASS",
        attempt_num=1,
        ep_num=2,
        arc_num=1,
        attempt_key="s4:ep2:arc1:a1:sess-frozen",
    )
    ui_written = db.save_ui_event(
        session_id="sess-frozen",
        seq=1,
        stage=4,
        component="Stage4",
        message="should be dropped",
    )
    db.save_director_selection(
        2,
        1,
        "A",
        "balanced",
        "PASS",
        attempt_key="s4:ep2:arc1:a1:sess-frozen",
        stage=4,
    )

    llm_row = db.conn.execute("SELECT COUNT(*) AS cnt FROM llm_calls WHERE session_id = 'sess-frozen'").fetchone()
    stage_row = db.conn.execute(
        "SELECT COUNT(*) AS cnt FROM stage_attempts WHERE attempt_key = 's4:ep2:arc1:a1:sess-frozen'"
    ).fetchone()
    ui_row = db.conn.execute("SELECT COUNT(*) AS cnt FROM ui_events WHERE session_id = 'sess-frozen'").fetchone()
    ds_row = db.conn.execute(
        "SELECT COUNT(*) AS cnt FROM director_selections WHERE attempt_key = 's4:ep2:arc1:a1:sess-frozen'"
    ).fetchone()

    assert director_written is False
    assert ui_written is False
    assert llm_row["cnt"] == 0
    assert stage_row["cnt"] == 0
    assert ui_row["cnt"] == 0
    assert ds_row["cnt"] == 0


def test_get_manuscripts_range_returns_ordered_rows(db):
    db.save_manuscript(1, "t1", "c1")
    db.save_manuscript(2, "t2", "c2")
    db.save_manuscript(3, "t3", "c3")

    rows = db.get_manuscripts_range(1, 3)

    assert [row["ep_num"] for row in rows] == [1, 2]


def test_save_and_get_episode_quality_label(db):
    db.save_episode_quality_label(
        7,
        {
            "score": 94,
            "verdict": "PASS",
            "selection_reason": "연속성과 몰입감 우수",
            "open_review": "특이사항 없음",
            "score_breakdown": {"continuity_contradiction": 38, "blueprint_coverage": 19},
            "consistency_checklist": {"scene_variety": "OK", "pacing_quality": "OK"},
        },
    )

    row = db.get_episode_quality_label(7)

    assert row is not None
    assert row["score"] == 94
    assert row["score_breakdown"]["continuity_contradiction"] == 38
    assert row["consistency_checklist"]["pacing_quality"] == "OK"


def test_save_and_summarize_episode_quality_signals(db):
    db.save_episode_quality_signal(
        7,
        {
            "ced_score": 1.4,
            "ai_slop_score": 2.2,
            "ai_slop_hits": [{"pattern": "그야말로", "count": 2}],
            "compression_ratio": 0.34,
            "burstiness": 11.5,
            "complexity": 31.2,
            "signal_summary": {"sentence_count": 42},
        },
    )
    db.save_episode_quality_signal(
        8,
        {
            "ced_score": 0.9,
            "ai_slop_score": 1.1,
            "ai_slop_hits": [{"pattern": "어느새", "count": 1}],
            "compression_ratio": 0.29,
            "burstiness": 13.0,
            "complexity": 34.4,
            "signal_summary": {"sentence_count": 50},
        },
    )

    row = db.get_episode_quality_signal(8)
    summary = db.get_quality_signal_summary(lookback=5)

    assert row is not None
    assert row["ai_slop_hits"][0]["pattern"] == "어느새"
    assert summary["available"] is True
    assert summary["latest_ep"] == 8
    assert summary["signals"]["ced"]["status"] in {"good", "watch", "alert"}
    assert summary["latest_signal_summary"]["sentence_count"] == 50


def test_save_and_read_episode_quality_observations(db):
    db.save_episode_quality_observation(8, {"operator_label": "AI 티", "note": "후반부 상투구 반복"})
    db.save_episode_quality_observation(9, {"operator_label": "좋음", "note": "리듬 안정"})

    row = db.get_episode_quality_observation(8)
    recent = db.get_recent_episode_quality_observations(lookback=5)

    assert row is not None
    assert row["operator_label"] == "AI 티"
    assert row["note"] == "후반부 상투구 반복"
    assert [item["ep_num"] for item in recent] == [8, 9]
    assert recent[-1]["operator_label"] == "좋음"


def test_recent_episode_scores_and_stage_attempts_queries(db):
    db.save_director_selection(2, 1, "", "creative", "PASS", score=77, selection_reason="arc ok", stage=2)
    db.save_director_selection(3, 1, "A", "balanced", "PASS", score=91, selection_reason="좋음", stage=4)
    db.save_director_selection(4, 1, "A", "balanced", "PASS_WITH_FIX", score=88, selection_reason="수정 필요", stage=4)
    db.save_director_selection(4, 2, "B", "balanced", "PASS", score=93, selection_reason="개선됨", stage=4)
    db.save_stage_attempt(
        stage=4,
        verdict="PASS",
        attempt_num=1,
        ep_num=3,
        arc_num=1,
        score=91,
        attempt_key="s4:ep3:arc1:a1",
        prompt_version="chief_writer@v1|director@v1",
    )
    db.save_stage_attempt(
        stage=4,
        verdict="PASS_WITH_WARNING",
        attempt_num=2,
        ep_num=4,
        arc_num=2,
        score=93,
        attempt_key="s4:ep4:arc2:a2",
        prompt_version="chief_writer@v1|director@v1",
    )
    db.save_stage_attempt(
        stage=4,
        verdict="REJECT",
        attempt_num=1,
        ep_num=4,
        arc_num=2,
        failure_category="continuity",
        prompt_version="chief_writer@v1|director@v1",
    )
    db.save_stage_attempt(
        stage=3,
        verdict="REJECT",
        attempt_num=1,
        ep_num=3,
        arc_num=2,
        failure_category="pacing",
        prompt_version="ensemble@v1|director@v1",
    )

    scores = db.get_recent_episode_scores(before_ep=5, lookback=3)
    attempts = db.get_stage_attempts_for_arc(2, stages=(3, 4), verdict="REJECT", limit=10)

    assert [row["ep_num"] for row in scores] == [3, 4]
    assert scores[-1]["score"] == 93
    assert scores[0]["attempt_key"] == "s4:ep3:arc1:a1"
    assert len(attempts) == 2
    assert {row["failure_category"] for row in attempts} == {"continuity", "pacing"}
    assert attempts[0]["prompt_version"]


def test_get_stage_attempts_for_arc_returns_rich_rationale_and_artifact_fields(db):
    db.save_stage_attempt(
        stage=4,
        verdict="REJECT",
        attempt_num=2,
        ep_num=9,
        arc_num=2,
        score=61,
        attempt_key="s4:ep9:arc2:a2",
        failure_category="continuity",
        reject_reason="The previous ending is being contradicted.",
        fix_scope="inplace",
        prompt_version="chief_writer@v2|director@v2",
        candidate_key="A|balanced",
        content_hash="hash-stage4",
        artifact_path="logs/artifacts/stage4/ep_0009/attempt_02/rejected_best__A_balanced.txt",
        selection_reason="Best local candidate, but still inconsistent.",
        verdict_reason="Contradiction Firewall: CRITICAL 1",
        open_review="Carry over the prior ending state instead of resetting it.",
        fix_scope_reasoning="Local ending repair is sufficient.",
        runtime_advisory="[Advisory digest] keep the prior ending state visible.",
        retry_directives="Do not repeat the previous ending beat verbatim.",
    )

    attempts = db.get_stage_attempts_for_arc(2, stages=(4,), verdict="REJECT", limit=5)

    assert len(attempts) == 1
    row = attempts[0]
    assert row["attempt_key"] == "s4:ep9:arc2:a2"
    assert row["candidate_key"] == "A|balanced"
    assert row["content_hash"] == "hash-stage4"
    assert row["artifact_path"].endswith("rejected_best__A_balanced.txt")
    assert row["selection_reason"] == "Best local candidate, but still inconsistent."
    assert row["verdict_reason"] == "Contradiction Firewall: CRITICAL 1"
    assert row["open_review"] == "Carry over the prior ending state instead of resetting it."
    assert row["fix_scope_reasoning"] == "Local ending repair is sufficient."
    assert "Advisory digest" in row["runtime_advisory"]
    assert row["retry_directives"] == "Do not repeat the previous ending beat verbatim."
    assert row["advisory_flags"] == {}


def test_save_stage_attempt_and_director_selection_persist_attempt_key(db):
    db.save_director_selection(
        5,
        2,
        "A",
        "balanced",
        "PASS_WITH_FIX",
        score=88,
        selection_reason="needs local fix",
        stage=4,
        attempt_key="s4:ep5:arc2:a2",
        candidate_key="A|balanced",
        content_hash="hash-director",
        artifact_path="logs/artifacts/stage4/ep_0005/attempt_02/selected_before_fix__A_balanced.txt",
    )
    db.save_stage_attempt(
        stage=4,
        verdict="PASS",
        attempt_num=2,
        ep_num=5,
        arc_num=2,
        score=97,
        attempt_key="s4:ep5:arc2:a2",
        prompt_version="chief_writer@v1|director@v1",
        candidate_key="A|balanced",
        content_hash="hash-stage-attempt",
        artifact_path="logs/artifacts/stage4/ep_0005/attempt_02/final_manuscript__A_balanced.txt",
    )

    ds_row = db.conn.execute(
        "SELECT attempt_key, candidate_key, content_hash, artifact_path FROM director_selections WHERE ep_num=5"
    ).fetchone()
    sa_row = db.conn.execute(
        "SELECT attempt_key, candidate_key, content_hash, artifact_path FROM stage_attempts WHERE ep_num=5 AND stage=4"
    ).fetchone()

    assert ds_row["attempt_key"] == "s4:ep5:arc2:a2"
    assert sa_row["attempt_key"] == "s4:ep5:arc2:a2"
    assert ds_row["candidate_key"] == "A|balanced"
    assert ds_row["content_hash"] == "hash-director"
    assert ds_row["artifact_path"].endswith("selected_before_fix__A_balanced.txt")
    assert sa_row["candidate_key"] == "A|balanced"
    assert sa_row["content_hash"] == "hash-stage-attempt"
    assert sa_row["artifact_path"].endswith("final_manuscript__A_balanced.txt")


def test_update_director_selection_rationale_updates_latest_attempt_row(db):
    db.save_director_selection(
        5,
        1,
        "A",
        "balanced",
        "PASS_WITH_FIX",
        score=88,
        selection_reason="initial rationale",
        verdict_reason="initial verdict",
        fix_scope="inplace",
        stage=4,
        attempt_key="s4:ep5:arc2:a2",
    )

    updated = db.update_director_selection_rationale(
        attempt_key="s4:ep5:arc2:a2",
        selection_reason="re-audited rationale",
        verdict_reason="re-audited verdict",
        fix_scope="ending_only",
    )

    row = db.conn.execute(
        """
        SELECT selection_reason, verdict_reason, fix_scope
        FROM director_selections
        WHERE attempt_key = 's4:ep5:arc2:a2'
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    assert updated is True
    assert row["selection_reason"] == "re-audited rationale"
    assert row["verdict_reason"] == "re-audited verdict"
    assert row["fix_scope"] == "ending_only"


def test_get_stage4_final_authority_rows_marks_selection_as_companion_when_patch_changes_artifact(db):
    attempt_key = "s4:ep5:arc2:a2:sess-authority"
    db.save_director_selection(
        5,
        1,
        "A",
        "balanced",
        "PASS_WITH_FIX",
        score=88,
        selection_reason="initial rationale",
        stage=4,
        attempt_key=attempt_key,
        candidate_key="A|balanced",
        content_hash="hash-selected",
        artifact_path="logs/artifacts/stage4/ep_0005/attempt_02/selected_before_fix__A_balanced.txt",
    )
    db.save_stage_attempt(
        stage=4,
        verdict="PASS",
        attempt_num=2,
        ep_num=5,
        arc_num=2,
        score=97,
        session_id="sess-authority",
        attempt_key=attempt_key,
        prompt_version="chief_writer@v1|director@v1",
        candidate_key="A|balanced",
        content_hash="hash-final",
        artifact_path="logs/artifacts/stage4/ep_0005/attempt_02/patched_after_fix__A_balanced.txt",
    )

    rows = db.get_stage4_final_authority_rows(limit=5)

    assert len(rows) == 1
    row = rows[0]
    assert row["attempt_key"] == attempt_key
    assert row["final_authority_sink"] == "stage_attempts"
    assert row["selection_role"] == "historical_companion"
    assert row["selection_companion_status"] == "pre_final_candidate"
    assert row["selection_companion_diff_fields"] == ["content_hash", "artifact_path"]
    assert row["selection_matches_final_artifact"] is False


def test_save_stage_attempt_persists_rationale_fields(db):
    db.save_stage_attempt(
        stage=4,
        verdict="REJECT",
        attempt_num=2,
        ep_num=6,
        arc_num=2,
        score=61,
        attempt_key="s4:ep6:arc2:a2",
        selection_reason="best candidate",
        verdict_reason="Contradiction Firewall: CRITICAL 1",
        open_review="The previous episode event is being repeated.",
        fix_scope_reasoning="frontier conflict",
        runtime_advisory="[Advisory digest - apply on retry]\n- keep continuity",
        retry_directives="keep the ending distinct",
    )

    row = db.conn.execute(
        """
        SELECT selection_reason, verdict_reason, open_review, fix_scope_reasoning, runtime_advisory, retry_directives
        FROM stage_attempts
        WHERE ep_num = 6 AND stage = 4
        """
    ).fetchone()

    assert row["selection_reason"] == "best candidate"
    assert row["verdict_reason"] == "Contradiction Firewall: CRITICAL 1"
    assert row["open_review"] == "The previous episode event is being repeated."
    assert row["fix_scope_reasoning"] == "frontier conflict"
    assert "Advisory digest" in row["runtime_advisory"]
    assert row["retry_directives"] == "keep the ending distinct"


def test_save_ui_event_persists_meta_json(db):
    persisted = db.save_ui_event(
        session_id="sess-ui",
        seq=7,
        stage=4,
        ep_num=12,
        round_num=1,
        attempt_key="s4:ep12:arc2:a1:sess-ui",
        component="Stage4",
        event_kind="log",
        level="info",
        message="director frame visible",
        meta={"origin": "unit"},
    )

    row = db.conn.execute(
        """
        SELECT session_id, seq, stage, ep_num, round_num, attempt_key, component, message, meta_json
        FROM ui_events
        WHERE session_id = 'sess-ui'
        """
    ).fetchone()

    assert persisted is True
    assert row["seq"] == 7
    assert row["stage"] == 4
    assert row["ep_num"] == 12
    assert row["round_num"] == 1
    assert row["attempt_key"] == "s4:ep12:arc2:a1:sess-ui"
    assert row["component"] == "Stage4"
    assert row["message"] == "director frame visible"
    assert "origin" in row["meta_json"]


def test_save_ui_event_normalizes_stage_labels_and_preserves_original_label(db):
    persisted_stage = db.save_ui_event(
        session_id="sess-ui-stage",
        seq=8,
        stage="stage4",
        ep_num=12,
        component="Stage4",
        message="director frame visible",
        meta={"origin": "unit"},
    )
    persisted_shutdown = db.save_ui_event(
        session_id="sess-ui-shutdown",
        seq=9,
        stage="shutdown",
        component="System",
        message="shutdown visible",
    )

    stage_row = db.conn.execute(
        """
        SELECT stage, meta_json
        FROM ui_events
        WHERE session_id = 'sess-ui-stage'
        """
    ).fetchone()
    shutdown_row = db.conn.execute(
        """
        SELECT stage, meta_json
        FROM ui_events
        WHERE session_id = 'sess-ui-shutdown'
        """
    ).fetchone()

    stage_meta = json.loads(stage_row["meta_json"])
    shutdown_meta = json.loads(shutdown_row["meta_json"])

    assert persisted_stage is True
    assert persisted_shutdown is True
    assert stage_row["stage"] == 4
    assert stage_meta["origin"] == "unit"
    assert stage_meta["stage_label"] == "stage4"
    assert shutdown_row["stage"] is None
    assert shutdown_meta["stage_label"] == "shutdown"


def test_save_ui_event_preserves_unknown_stage_labels_without_dropping_write(db):
    persisted = db.save_ui_event(
        session_id="sess-ui-unknown-stage",
        seq=10,
        stage="preflight",
        component="System",
        message="preflight visible",
        meta={"origin": "unit"},
    )

    row = db.conn.execute(
        """
        SELECT stage, meta_json
        FROM ui_events
        WHERE session_id = 'sess-ui-unknown-stage'
        """
    ).fetchone()

    meta = json.loads(row["meta_json"])

    assert persisted is True
    assert row["stage"] is None
    assert meta["origin"] == "unit"
    assert meta["stage_label"] == "preflight"


def test_save_ui_event_respects_outer_transaction_rollback(db):
    with pytest.raises(DBError):
        with db.transaction():
            persisted = db.save_ui_event(
                session_id="sess-ui-tx",
                seq=1,
                stage=3,
                ep_num=5,
                component="Stage3",
                message="buffered event",
            )
            assert persisted is True
            raise RuntimeError("rollback trigger")

    row = db.conn.execute(
        "SELECT COUNT(*) AS cnt FROM ui_events WHERE session_id = 'sess-ui-tx'"
    ).fetchone()
    assert row["cnt"] == 0


def test_get_strategy_win_rates_supports_stage2_filters(db):
    db.save_director_selection(2, 1, "", "creative", "PASS", score=88, selection_reason="arc ok")
    db.save_director_selection(3, 1, "A", "balanced", "PASS", score=91, selection_reason="writer ok")
    db.save_director_selection(4, 1, "", "analyst", "PASS", score=86, selection_reason="legacy")

    result = db.get_strategy_win_rates(
        lookback=10,
        selected_label="",
        allowed_strategies=("conservative", "balanced", "creative"),
    )

    assert result["total"] == 1
    assert result["creative"] == 1.0


def test_save_director_selection_persists_firewall_metadata(db):
    db.save_director_selection(
        4,
        2,
        "A",
        "balanced",
        "REJECT",
        score=44,
        selection_reason="최우수 후보 선택",
        verdict_reason="Contradiction Firewall: CRITICAL 1건",
        pre_firewall_score=100,
        firewall_triggered=True,
        firewall_reason="Contradiction Firewall: CRITICAL 1건",
        stage=4,
    )

    row = db.cursor.execute(
        """
        SELECT selection_reason, verdict_reason, pre_firewall_score, firewall_triggered, firewall_reason
        FROM director_selections
        WHERE ep_num = 4 AND round_num = 2
        """
    ).fetchone()

    assert row["selection_reason"] == "최우수 후보 선택"
    assert row["verdict_reason"] == "Contradiction Firewall: CRITICAL 1건"
    assert row["pre_firewall_score"] == 100
    assert row["firewall_triggered"] == 1
    assert row["firewall_reason"] == "Contradiction Firewall: CRITICAL 1건"

def test_save_director_selection_keeps_selection_reason_up_to_500_chars(db):
    long_reason = "r" * 450

    db.save_director_selection(
        8,
        1,
        "B",
        "balanced",
        "PASS",
        score=95,
        selection_reason=long_reason,
        verdict_reason="ready to use",
        stage=4,
        attempt_key="s4:ep8:arc2:a1",
    )

    row = db.cursor.execute(
        """
        SELECT selection_reason
        FROM director_selections
        WHERE attempt_key = 's4:ep8:arc2:a1'
        """
    ).fetchone()

    assert row["selection_reason"] == long_reason
