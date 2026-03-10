"""[Phase 6] Cost tracking DB + metrics scope snapshot tests."""

import json

from modules.core.db_manager import DBManager
from modules.core.metrics_collector import MetricsCollector


def test_save_cost_record_and_get_cost_summary(tmp_path):
    db = DBManager(tmp_path / "cost_test.db")
    try:
        db.save_cost_record(
            session_id="sess_1",
            scope_type="arc",
            scope_id=12,
            total_calls=4,
            total_tokens=3200,
            total_cost_usd=0.0432,
            model_breakdown={"gemini-2.5-pro": {"tokens": 3200, "cost": 0.0432}},
        )

        rows = db.get_cost_summary(scope_type="arc", lookback=10)

        assert len(rows) == 1
        assert rows[0]["session_id"] == "sess_1"
        assert rows[0]["scope_type"] == "arc"
        assert rows[0]["scope_id"] == 12
        assert rows[0]["total_calls"] == 4
        assert rows[0]["total_tokens"] == 3200
        assert float(rows[0]["total_cost_usd"]) == 0.0432
        assert "gemini-2.5-pro" in rows[0]["model_breakdown"]
    finally:
        db.close()


def test_get_cost_summary_filter_and_limit(tmp_path):
    db = DBManager(tmp_path / "cost_test_limit.db")
    try:
        db.save_cost_record(session_id="s", scope_type="arc", scope_id=1, total_calls=1)
        db.save_cost_record(session_id="s", scope_type="episode", scope_id=2, total_calls=2)
        db.save_cost_record(session_id="s", scope_type="arc", scope_id=3, total_calls=3)

        rows_arc = db.get_cost_summary(scope_type="arc", lookback=10)
        rows_all_limited = db.get_cost_summary(scope_type=None, lookback=2)

        assert len(rows_arc) == 2
        assert all(r["scope_type"] == "arc" for r in rows_arc)
        assert len(rows_all_limited) == 2
    finally:
        db.close()


def test_snapshot_and_reset_scope(tmp_path):
    collector = MetricsCollector.reset(tmp_path / "metrics")
    try:
        metric_id = collector.start_call("Writer", "gemini-2.5-pro")
        collector.end_call(metric_id, success=True, input_tokens=1200, output_tokens=800)

        scope = collector.snapshot_and_reset_scope()

        assert scope["total_calls"] == 1
        assert scope["total_tokens"] == 2000
        assert scope["total_cost_usd"] > 0
        breakdown = json.loads(scope["model_breakdown"])
        assert "gemini-2.5-pro" in breakdown
        assert breakdown["gemini-2.5-pro"]["tokens"] == 2000

        after_reset = collector.snapshot_and_reset_scope()
        assert after_reset["total_calls"] == 0
        assert after_reset["total_tokens"] == 0
        assert after_reset["total_cost_usd"] == 0.0
    finally:
        MetricsCollector.reset(tmp_path / "metrics")


def test_vertex_prefixed_model_uses_gemini_costs(tmp_path):
    collector = MetricsCollector.reset(tmp_path / "metrics")
    try:
        base_cost = collector.calculate_cost("gemini-2.5-pro", input_tokens=1200, output_tokens=800)
        vertex_cost = collector.calculate_cost("vertexai:gemini-2.5-pro", input_tokens=1200, output_tokens=800)
        assert vertex_cost == base_cost
    finally:
        MetricsCollector.reset(tmp_path / "metrics")
