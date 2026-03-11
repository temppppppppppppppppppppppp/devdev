"""DBManager current-API regression tests."""

import pytest

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


def test_close_then_query_raises_connection_error(tmp_path):
    manager = DBManager(tmp_path / "closed.db")
    manager.close()
    with pytest.raises(DBConnectionError):
        manager.execute_query("SELECT 1")


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
    assert len(attempts) == 2
    assert {row["failure_category"] for row in attempts} == {"continuity", "pacing"}
    assert attempts[0]["prompt_version"]


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
