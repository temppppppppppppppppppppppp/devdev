"""[B-1-7] Unit tests for Stage2Finalizer extracted from Stage2Orchestrator."""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.stage2_finalizer import Stage2Finalizer


@pytest.fixture
def finalizer_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.pass_rate_monitor = MagicMock()
    ctx.quality_dashboard = MagicMock()
    ctx.stage2_optimizer = MagicMock()
    ctx.stage2_optimizer.failure_memory = MagicMock()
    ctx.perf_timer = MagicMock()
    ctx.stage_rejection_history = []
    ctx.audit_event = MagicMock()
    ctx.semantic_plot_guard = None
    ctx.validate_arc_integrity = MagicMock(return_value=True)
    ctx.current_project = MagicMock()
    ctx.safe_commit_async = AsyncMock(return_value=True)
    ctx.generate_arc_context_v60 = MagicMock(return_value="context_text")
    ctx.cumulative_state_cache = None
    ctx.cumulative_state_cache_key = 0
    ctx.get_adaptive_feedback_intensity = MagicMock(return_value={"guidance": "guide"})
    ctx.state_tracker = SimpleNamespace(foo=0, bar=0)

    director = MagicMock()
    director.audit_strategic_plan.return_value = {"decision": "PASS", "score": 95, "reason": "ok"}
    director.ask.return_value = "volume summary text long enough"
    ctx.agents = {"director": director}
    return ctx


@pytest.fixture
def finalizer(finalizer_ctx):
    host = MagicMock()
    host.ctx = finalizer_ctx
    return Stage2Finalizer(host)


@pytest.fixture
def valid_refined_arc():
    return {
        "arc_no": 1,
        "ep_start": 1,
        "ep_end": 10,
        "ep_count": 10,
        "tactical_doc": "A" * 1600,
        "state_changes": {"npc_deaths": [], "relationship_changes": []},
        "hybrid_composition": {
            "primary": "standard_progression",
            "secondary": [],
            "mixing_logic": "default",
        },
        "joint_docs": {
            "final_location": "market",
            "physical_inventory": [],
            "world_joint": "stable",
        },
        "status_shadow": {
            "internal_energy_loss": "10%",
            "expected_injuries": "none",
            "item_consumption": [],
        },
        "state_constraints": {"items_acquired": []},
    }


def _make_finalize_kwargs(refined_arc, **overrides):
    constraint_db = overrides.pop("constraint_db", MagicMock(arc_states=[]))
    defaults = {
        "refined_arc": refined_arc,
        "enriched_block": {
            "joint_docs": {"final_location": "city", "physical_inventory": [], "world_joint": "stable"},
            "status_shadow": {"internal_energy_loss": "5%", "expected_injuries": "none", "item_consumption": []},
            "joint_docs_brief": "brief",
        },
        "arc_drive": {"desire_vector": "test"},
        "all_refined_arcs": [],
        "global_arc_no": 1,
        "current_ep_start": 1,
        "current_feedback": "",
        "protagonist_name": "hero",
        "suspected_duplicates": [],
        "entity_registry_for_director": {},
        "constraint_block": "",
        "draft_validator_passed": True,
        "consensus_passed": True,
        "attempt": 0,
        "generation_method": "four_phase",
        "st_snapshot": None,
        "director_feedback_for_fourphase": "",
        "last_refined_context": "prev context",
        "bible_root": {"protagonist_config": {"name": "hero", "incarnation_type": "회귀자"}},
        "genre": "fantasy",
        "constraint_db": constraint_db,
    }
    defaults.update(overrides)
    return defaults


class TestFinalizerStructure:
    def test_host_is_required_for_ctx_proxy(self):
        f = Stage2Finalizer(None)
        with pytest.raises(AttributeError):
            _ = f.ctx

    def test_ctx_proxy(self, finalizer, finalizer_ctx):
        assert finalizer.ctx is finalizer_ctx

    def test_methods_exist(self, finalizer):
        assert hasattr(finalizer, "run_finalize")
        assert hasattr(finalizer, "_record_s2_pass_metrics")
        assert hasattr(finalizer, "_record_s2_reject_metrics")


class TestMetricsRecording:
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_pass_metrics_with_monitor(self, finalizer):
        finalizer._record_s2_pass_metrics(global_arc_no=1, attempt=0, generation_method="analyst", audit={"score": 88})
        kw = finalizer.ctx.pass_rate_monitor.record_attempt.call_args[1]
        assert kw["success"] is True
        assert kw["stage"] == 2
        qd_kw = finalizer.ctx.quality_dashboard.record_validation.call_args[1]
        assert qd_kw["result"]["decision"] == "PASS"

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_pass_metrics_without_monitor(self, finalizer):
        finalizer.ctx.pass_rate_monitor = None
        finalizer.ctx.quality_dashboard = None
        finalizer._record_s2_pass_metrics(global_arc_no=2, attempt=1, generation_method="analyst", audit={"score": 80})
        finalizer.ctx.perf_timer.log_summary.assert_called_once()
        finalizer.ctx.perf_timer.reset.assert_called_once()

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_pass_metrics_clears_optimizer_failures(self, finalizer):
        finalizer._record_s2_pass_metrics(global_arc_no=3, attempt=0, generation_method="analyst", audit={})
        finalizer.ctx.stage2_optimizer.failure_memory.clear_arc_failures.assert_called_once_with(3)

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_reject_metrics_with_monitor(self, finalizer):
        finalizer._record_s2_reject_metrics(
            global_arc_no=4,
            attempt=1,
            generation_method="analyst",
            audit={"score": 42, "reason": "bad structure"},
        )
        kw = finalizer.ctx.pass_rate_monitor.record_attempt.call_args[1]
        assert kw["success"] is False
        assert len(finalizer.ctx.stage_rejection_history) == 1
        assert finalizer.ctx.stage_rejection_history[0]["arc_no"] == 4

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_reject_metrics_without_monitor(self, finalizer):
        finalizer.ctx.pass_rate_monitor = None
        finalizer.ctx.quality_dashboard = None
        finalizer._record_s2_reject_metrics(
            global_arc_no=5,
            attempt=0,
            generation_method="analyst",
            audit={"reason": "x"},
        )
        assert len(finalizer.ctx.stage_rejection_history) == 1

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_reject_metrics_records_optimizer_failure(self, finalizer):
        finalizer._record_s2_reject_metrics(
            global_arc_no=6,
            attempt=0,
            generation_method="analyst",
            audit={"reason": "reject reason"},
        )
        finalizer.ctx.stage2_optimizer.failure_memory.record_failure.assert_called_once()


class TestRunFinalize:
    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_director_pass_returns_break(self, _validate, finalizer, valid_refined_arc):
        kwargs = _make_finalize_kwargs(valid_refined_arc)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        assert result["current_ep_start"] == 11
        assert len(kwargs["all_refined_arcs"]) == 1
        finalizer.ctx.current_project.save_v20_anchor.assert_called()

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_director_pass_records_arc_cost(self, _validate, finalizer, valid_refined_arc):
        collector = MagicMock()
        collector.session_id = "sess_test"
        collector.snapshot_and_reset_scope.return_value = {
            "total_calls": 2,
            "total_tokens": 1500,
            "total_cost_usd": 0.0123,
            "model_breakdown": "{}",
        }

        kwargs = _make_finalize_kwargs(valid_refined_arc)
        with patch("modules.core.stage2_finalizer.get_metrics_collector", return_value=collector):
            result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        finalizer.ctx.current_project.db.save_cost_record.assert_called_once()
        cost_kw = finalizer.ctx.current_project.db.save_cost_record.call_args.kwargs
        assert cost_kw["session_id"] == "sess_test"
        assert cost_kw["scope_type"] == "arc"
        assert cost_kw["scope_id"] == 1
        assert cost_kw["total_calls"] == 2

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_director_reject_returns_retry(self, finalizer, valid_refined_arc):
        finalizer.ctx.agents["director"].audit_strategic_plan.return_value = {
            "decision": "REJECT",
            "score": 30,
            "reason": "reject reason",
            "re_slice_instruction": "fix structure",
        }
        kwargs = _make_finalize_kwargs(
            valid_refined_arc,
            draft_validator_passed=False,
            consensus_passed=False,
        )
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "retry"
        assert "reject reason" in result["director_feedback_for_fourphase"]

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_quota_fallback_warning_only(self, _validate, finalizer, valid_refined_arc):
        """[TF-25-07] V60.43 API 쿼터 실패 패턴 감지 시 REJECT 유지 + 경고만."""
        finalizer.ctx.agents["director"].audit_strategic_plan.return_value = {
            "decision": "REJECT",
            "score": 0,
            "reason": "quota",
            "self_consistency": {"scores": [50, 50]},
        }
        kwargs = _make_finalize_kwargs(valid_refined_arc, draft_validator_passed=True, consensus_passed=True)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        # [TF-25-07] Director REJECT 유지 — Python이 판정을 변경하지 않음
        assert result["action"] == "retry"  # REJECT → retry (오케스트레이터 재시도)
        audit = finalizer.ctx.agents["director"].audit_strategic_plan.return_value
        assert audit.get("v60_43_api_warning") is True

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_missing_critical_data_returns_retry(self, finalizer, valid_refined_arc):
        arc = dict(valid_refined_arc)
        arc.pop("hybrid_composition", None)
        kwargs = _make_finalize_kwargs(
            arc,
            enriched_block={"joint_docs": {}, "status_shadow": {}},
        )
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "retry"
        assert "current_feedback" in result

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_state_tracker_rollback_on_reject(self, finalizer, valid_refined_arc):
        finalizer.ctx.agents["director"].audit_strategic_plan.return_value = {
            "decision": "REJECT",
            "score": 20,
            "reason": "rollback needed",
            "re_slice_instruction": "retry",
        }
        finalizer.ctx.state_tracker = SimpleNamespace(foo=0, bar=0)
        kwargs = _make_finalize_kwargs(
            valid_refined_arc,
            generation_method="four_phase",
            st_snapshot={"foo": 9, "bar": 3},
            draft_validator_passed=False,
            consensus_passed=False,
        )
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "retry"
        assert finalizer.ctx.state_tracker.foo == 9
        assert finalizer.ctx.state_tracker.bar == 3
        assert result["st_snapshot"] is None

    @patch("modules.core.stage2_finalizer.validate_arc", side_effect=lambda x: x)
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_volume_summary_generation(self, _validate, finalizer, valid_refined_arc):
        def _load_anchor(key):
            if key.startswith("arc_summary_"):
                return "arc summary"
            if key == "series_summary":
                return "series summary"
            return None

        finalizer.ctx.current_project.load_v20_anchor.side_effect = _load_anchor
        finalizer.ctx.agents["director"].ask.return_value = "summary result long enough"

        kwargs = _make_finalize_kwargs(valid_refined_arc, global_arc_no=10)
        result = asyncio.run(finalizer.run_finalize(**kwargs))

        assert result["action"] == "break"
        save_calls = [call.args[0] for call in finalizer.ctx.current_project.save_v20_anchor.call_args_list]
        assert "volume_summary_1" in save_calls
        assert "series_summary" in save_calls
