from modules.core.db_manager import DBManager


def test_reset_after_deletes_quality_tables_and_stage34_attempts(tmp_path):
    db = DBManager(tmp_path / "safe_ops.db")
    try:
        db.save_episode_quality_label(3, {"score": 70, "verdict": "PASS"})
        db.save_episode_quality_label(5, {"score": 71, "verdict": "PASS"})
        db.save_episode_quality_signal(3, {"ced_score": 0.3})
        db.save_episode_quality_signal(5, {"ced_score": 0.5})
        db.save_episode_quality_observation(3, {"operator_label": "good", "note": "keep"})
        db.save_episode_quality_observation(5, {"operator_label": "warn", "note": "drop"})
        db.save_stage_attempt(stage=2, verdict="PASS", ep_num=5, arc_num=5)
        db.save_stage_attempt(stage=3, verdict="PASS", ep_num=5, arc_num=3)
        db.save_stage_attempt(stage=4, verdict="REJECT", ep_num=5, arc_num=3)

        db.reset_after(4)

        assert db.get_episode_quality_label(3) is not None
        assert db.get_episode_quality_label(5) is None
        assert db.get_episode_quality_signal(3) is not None
        assert db.get_episode_quality_signal(5) is None
        assert db.get_episode_quality_observation(3) is not None
        assert db.get_episode_quality_observation(5) is None

        rows = [dict(row) for row in db.execute_query("SELECT stage, ep_num, arc_num FROM stage_attempts ORDER BY stage, ep_num")]
        assert rows == [{"stage": 2, "ep_num": 5, "arc_num": 5}]
    finally:
        db.close()


def test_get_rollback_impact_includes_new_episode_tables(tmp_path):
    db = DBManager(tmp_path / "impact.db")
    try:
        db.save_episode_quality_label(5, {"score": 71, "verdict": "PASS"})
        db.save_episode_quality_signal(5, {"ced_score": 0.5})
        db.save_episode_quality_observation(5, {"operator_label": "warn", "note": "drop"})
        db.save_stage_attempt(stage=3, verdict="PASS", ep_num=5, arc_num=3)

        impact = db.get_rollback_impact(4)

        assert impact["episode_quality_labels"] == 1
        assert impact["episode_quality_signals"] == 1
        assert impact["episode_quality_observations"] == 1
        assert impact["stage_attempts_stage34"] == 1
    finally:
        db.close()


def test_reset_after_preserves_stage2_director_selections(tmp_path):
    db = DBManager(tmp_path / "safe_ops_stage.db")
    try:
        db.save_director_selection(2, 1, "", "creative", "PASS", 88, "arc ok", stage=2)
        db.save_director_selection(5, 1, "A", "balanced", "PASS", 91, "writer ok", stage=4)

        db.reset_after(4)

        rows = [dict(row) for row in db.execute_query(
            "SELECT stage, ep_num, selected_label FROM director_selections ORDER BY id"
        )]
        assert rows == [{"stage": 2, "ep_num": 2, "selected_label": ""}]
    finally:
        db.close()
