"""[Phase 4-R3] Unit tests for extracted stage2 preflight helper methods.

Tests the 7 methods extracted in R3-a through R3-f:
- _preflight_state_setup, _preflight_arc_analysis, _preflight_enrichment
- _preflight_validation, _preflight_finalize
- _record_s2_pass_metrics, _record_s2_reject_metrics
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.stage2_orchestrator import Stage2Orchestrator

# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def s2_ctx():
    """Stage2Orchestrator에 주입할 ctx mock (metrics helpers + validation 공용)"""
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
    ctx.state_tracker = None
    ctx.current_project = MagicMock()
    ctx.agents = {}
    ctx.arc_draft_validator = None
    ctx.self_reflector = None
    ctx.arc_corrector = None
    ctx.continuity_inspector = None
    ctx.semantic_plot_guard = None
    ctx.constraint_compiler = None
    ctx.memory = None
    ctx.use_arc_corrector = False
    ctx.cumulative_state_cache = None
    ctx.cumulative_state_cache_key = 0
    ctx.safe_commit_async = AsyncMock(return_value=True)
    ctx.validate_arc_mapping = MagicMock(side_effect=lambda arc, *a, **kw: arc)
    ctx.validate_arc_integrity = MagicMock(return_value=True)
    ctx.generate_arc_context_v60 = MagicMock(return_value="context_text")
    ctx.write_audit_summary = MagicMock()
    ctx.generate_structured_arc_feedback = MagicMock(return_value="feedback")
    ctx.get_adaptive_feedback_intensity = MagicMock(return_value={"guidance": "guide"})
    ctx.build_strong_kind_feedback = MagicMock(return_value="strong")
    ctx.build_focused_context = MagicMock(return_value="focused")
    return ctx


@pytest.fixture
def s2_orch(s2_ctx):
    """Stage2Orchestrator with mocked ctx"""
    app = MagicMock()
    app.semantic_plot_guard = None
    orch = Stage2Orchestrator(app=app)
    orch._ctx = s2_ctx
    return orch


@pytest.fixture
def valid_refined_arc():
    """Flow Guard + PASS block을 통과하는 유효한 refined_arc"""
    return {
        "arc_no": 1,
        "ep_start": 1,
        "ep_end": 10,
        "ep_count": 10,
        "tactical_doc": "이청풍이 청풍산장에서 수련을 시작한다. " * 100,  # ~2400자
        "beat_sequence": [
            "첫 번째 비트: 이청풍이 아침에 일어난다 " * 5,
            "두 번째 비트: 노사부를 만난다 " * 5,
            "세 번째 비트: 수련을 시작한다 " * 5,
            "네 번째 비트: 첫 시련을 겪는다 " * 5,
            "다섯 번째 비트: 깨달음을 얻는다 " * 5,
        ],
        "state_changes": {"npc_deaths": [], "relationship_changes": []},
        "hybrid_composition": {
            "primary": "standard_progression",
            "secondary": [],
            "mixing_logic": "기본 전개",
        },
        "joint_docs": {
            "final_location": "청풍산장",
            "physical_inventory": ["청풍검"],
            "world_joint": "변화 없음",
        },
        "status_shadow": {
            "internal_energy_loss": "10%",
            "expected_injuries": "없음",
            "item_consumption": [],
        },
    }


# ══════════════════════════════════════════════════════════════
# Test 1: All extracted methods exist
# ══════════════════════════════════════════════════════════════


class TestPreflightMethodsExist:
    """All 7 extracted methods exist on Stage2Orchestrator."""

    METHODS = [
        "_preflight_state_setup",
        "_preflight_arc_analysis",
        "_preflight_enrichment",
        "_preflight_validation",
        "_preflight_finalize",
        "_record_s2_pass_metrics",
        "_record_s2_reject_metrics",
    ]

    @pytest.mark.parametrize("method_name", METHODS)
    def test_method_exists(self, s2_orch, method_name):
        assert hasattr(s2_orch, method_name)
        assert callable(getattr(s2_orch, method_name))


# ══════════════════════════════════════════════════════════════
# Test 2: _record_s2_pass_metrics
# ══════════════════════════════════════════════════════════════


class TestRecordS2PassMetrics:
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_calls_all_subsystems(self, s2_orch):
        """PassRateMonitor(success=True), QualityDashboard(PASS), Optimizer clear 호출 확인"""
        s2_orch._record_s2_pass_metrics(
            global_arc_no=1,
            attempt=0,
            generation_method="analyst",
            audit={"score": 85},
        )
        # PassRateMonitor
        s2_orch.ctx.pass_rate_monitor.record_attempt.assert_called_once()
        kw = s2_orch.ctx.pass_rate_monitor.record_attempt.call_args[1]
        assert kw["success"] is True
        assert kw["attempt_num"] == 1
        assert kw["stage"] == 2

        # QualityDashboard
        s2_orch.ctx.quality_dashboard.record_validation.assert_called_once()
        qd_kw = s2_orch.ctx.quality_dashboard.record_validation.call_args[1]
        assert qd_kw["result"]["decision"] == "PASS"
        assert qd_kw["result"]["score"] == 85

        # Optimizer clear
        s2_orch.ctx.stage2_optimizer.failure_memory.clear_arc_failures.assert_called_once_with(1)

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_perf_timer_reset(self, s2_orch):
        """PerfTimer log_summary + reset 호출 확인"""
        s2_orch._record_s2_pass_metrics(
            global_arc_no=2,
            attempt=1,
            generation_method="four_phase",
            audit={"score": 90},
        )
        s2_orch.ctx.perf_timer.log_summary.assert_called_once()
        s2_orch.ctx.perf_timer.reset.assert_called_once()

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_silent_on_monitor_exception(self, s2_orch):
        """PassRateMonitor 예외 → 전파 안 됨, 후속 subsystem 정상 호출"""
        s2_orch.ctx.pass_rate_monitor.record_attempt.side_effect = RuntimeError("boom")
        # Should NOT raise
        s2_orch._record_s2_pass_metrics(
            global_arc_no=1,
            attempt=0,
            generation_method="analyst",
            audit={},
        )
        # QualityDashboard still called despite PassRateMonitor failure
        s2_orch.ctx.quality_dashboard.record_validation.assert_called_once()


# ══════════════════════════════════════════════════════════════
# Test 3: _record_s2_reject_metrics
# ══════════════════════════════════════════════════════════════


class TestRecordS2RejectMetrics:
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_calls_all_subsystems(self, s2_orch):
        """PassRateMonitor(success=False), QualityDashboard(REJECT), Optimizer failure 호출 확인"""
        s2_orch._record_s2_reject_metrics(
            global_arc_no=3,
            attempt=1,
            generation_method="analyst",
            audit={"score": 40, "reason": "구조 불안정"},
        )
        # PassRateMonitor
        kw = s2_orch.ctx.pass_rate_monitor.record_attempt.call_args[1]
        assert kw["success"] is False
        assert kw["reject_reason"] == "구조 불안정"

        # QualityDashboard
        qd_kw = s2_orch.ctx.quality_dashboard.record_validation.call_args[1]
        assert qd_kw["result"]["decision"] == "REJECT"
        assert qd_kw["result"]["score"] == 40

        # Optimizer failure recording
        s2_orch.ctx.stage2_optimizer.failure_memory.record_failure.assert_called_once()

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_rejection_history_format(self, s2_orch):
        """stage_rejection_history에 올바른 dict 형식으로 추가"""
        s2_orch._record_s2_reject_metrics(
            global_arc_no=5,
            attempt=2,
            generation_method="four_phase",
            audit={"reason": "반복 전개"},
        )
        assert len(s2_orch.ctx.stage_rejection_history) == 1
        entry = s2_orch.ctx.stage_rejection_history[0]
        assert entry["stage"] == 2
        assert entry["arc_no"] == 5
        assert entry["reason"] == "반복 전개"
        assert entry["attempt"] == 3  # attempt + 1

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    def test_silent_on_dashboard_exception(self, s2_orch):
        """QualityDashboard 예외 → 전파 안 됨, rejection_history 정상 기록"""
        s2_orch.ctx.quality_dashboard.record_validation.side_effect = RuntimeError("dashboard crash")
        # Should NOT raise
        s2_orch._record_s2_reject_metrics(
            global_arc_no=1,
            attempt=0,
            generation_method="analyst",
            audit={"reason": "test"},
        )
        # rejection_history still appended
        assert len(s2_orch.ctx.stage_rejection_history) == 1


# ══════════════════════════════════════════════════════════════
# Test 4: _preflight_validation
# ══════════════════════════════════════════════════════════════


class TestPreflightValidation:
    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", None)
    def test_retry_on_none_arc(self, s2_orch):
        """refined_arc=None → action=retry (데이터 검증 실패)"""
        result = s2_orch._preflight_validation(
            refined_arc=None,
            four_phase_passed=True,
            all_refined_arcs=[],
            entity_registry_for_director=None,
            global_arc_no=1,
            current_ep_start=1,
            current_feedback="",
            generation_method="analyst",
            constraint_block="",
            enriched_block={},
            draft_validator_passed=False,
            consensus_passed=False,
            attempt=0,
            protagonist_name="이청풍",
            constraint_db=MagicMock(),
        )
        assert result["action"] == "retry"
        assert "current_feedback" in result
        assert len(result["current_feedback"]) > 0

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", None)
    def test_proceed_with_valid_arc(self, s2_orch, valid_refined_arc):
        """유효한 arc + 모든 validator 비활성 → action=proceed"""
        s2_orch._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        s2_orch.ctx.stage2_optimizer = None

        constraint_db = MagicMock()
        constraint_db.validate_arc_design.return_value = {
            "valid": True,
            "violations": [],
            "warnings": [],
        }

        result = s2_orch._preflight_validation(
            refined_arc=valid_refined_arc,
            four_phase_passed=True,
            all_refined_arcs=[],
            entity_registry_for_director=None,
            global_arc_no=1,
            current_ep_start=1,
            current_feedback="",
            generation_method="four_phase",
            constraint_block="",
            enriched_block={"joint_docs": {}},
            draft_validator_passed=True,
            consensus_passed=True,
            attempt=0,
            protagonist_name="이청풍",
            constraint_db=constraint_db,
        )
        assert result["action"] == "proceed"

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", None)
    def test_proceed_returns_required_keys(self, s2_orch, valid_refined_arc):
        """proceed 반환 dict에 필수 키 5개 존재"""
        s2_orch._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        s2_orch.ctx.stage2_optimizer = None

        constraint_db = MagicMock()
        constraint_db.validate_arc_design.return_value = {
            "valid": True,
            "violations": [],
            "warnings": [],
        }

        result = s2_orch._preflight_validation(
            refined_arc=valid_refined_arc,
            four_phase_passed=True,
            all_refined_arcs=[],
            entity_registry_for_director=None,
            global_arc_no=1,
            current_ep_start=1,
            current_feedback="",
            generation_method="four_phase",
            constraint_block="",
            enriched_block={"block_theme": "test"},
            draft_validator_passed=True,
            consensus_passed=True,
            attempt=0,
            protagonist_name="이청풍",
            constraint_db=constraint_db,
        )
        required = ["action", "refined_arc", "draft_validator_passed", "consensus_passed", "suspected_duplicates"]
        for key in required:
            assert key in result, f"Missing key: {key}"


# ══════════════════════════════════════════════════════════════
# Test 5: _preflight_finalize (async)
# ══════════════════════════════════════════════════════════════


class TestPreflightFinalize:
    def _make_finalize_kwargs(self, refined_arc, **overrides):
        """_preflight_finalize 기본 kwargs 생성"""
        defaults = {
            "refined_arc": refined_arc,
            "enriched_block": {"joint_docs": {}, "block_theme": "test"},
            "arc_drive": {"desire_vector": "test"},
            "all_refined_arcs": [],
            "global_arc_no": 1,
            "current_ep_start": 1,
            "current_feedback": "",
            "protagonist_name": "이청풍",
            "suspected_duplicates": [],
            "entity_registry_for_director": None,
            "constraint_block": "",
            "draft_validator_passed": True,
            "consensus_passed": True,
            "attempt": 0,
            "generation_method": "four_phase",
            "st_snapshot": None,
            "use_analyst_fallback": False,
            "director_feedback_for_fourphase": "",
            "last_refined_context": "이전 컨텍스트",
            "bible_root": {"protagonist_config": {"name": "이청풍"}},
            "genre": "wuxia",
            "constraint_db": MagicMock(),
        }
        defaults.update(overrides)
        return defaults

    def test_break_on_director_pass(self, s2_orch, valid_refined_arc):
        """Director PASS → action=break"""
        director_mock = MagicMock()
        director_mock.audit_strategic_plan.return_value = {
            "decision": "PASS",
            "score": 85,
            "reason": "좋은 설계",
        }
        s2_orch.ctx.agents = {"director": director_mock}
        s2_orch.ctx.pass_rate_monitor = None
        s2_orch.ctx.quality_dashboard = None
        s2_orch.ctx.stage2_optimizer = None

        kwargs = self._make_finalize_kwargs(valid_refined_arc)
        with (
            patch("modules.core.spinners.V50_MODULES_AVAILABLE", False),
            patch(
                "modules.core.stage2_orchestrator.validate_arc",
                side_effect=lambda x: x,
            ),
        ):
            result = asyncio.run(s2_orch._preflight_finalize(**kwargs))

        assert result["action"] == "break"
        assert "last_refined_context" in result
        assert "st_snapshot" in result
        director_mock.audit_strategic_plan.assert_called_once()

    def test_next_on_director_reject(self, s2_orch, valid_refined_arc):
        """Director REJECT + use_analyst_fallback=False → action=next"""
        director_mock = MagicMock()
        director_mock.audit_strategic_plan.return_value = {
            "decision": "REJECT",
            "score": 40,
            "reason": "구조적 문제",
        }
        s2_orch.ctx.agents = {"director": director_mock}
        s2_orch.ctx.pass_rate_monitor = None
        s2_orch.ctx.quality_dashboard = None
        s2_orch.ctx.stage2_optimizer = None

        kwargs = self._make_finalize_kwargs(
            valid_refined_arc,
            draft_validator_passed=False,
            consensus_passed=False,
            use_analyst_fallback=False,
        )
        with patch("modules.core.spinners.V50_MODULES_AVAILABLE", False):
            result = asyncio.run(s2_orch._preflight_finalize(**kwargs))

        assert result["action"] == "next"
        assert "current_feedback" in result
        assert "director_feedback_for_fourphase" in result
        # director_feedback_for_fourphase should contain reject reason
        assert "구조적 문제" in result["director_feedback_for_fourphase"]
