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
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
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
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
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
            "score": 95,
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
                "modules.core.stage2_finalizer.validate_arc",
                side_effect=lambda x: x,
            ),
        ):
            result = asyncio.run(s2_orch._preflight_finalize(**kwargs))

        assert result["action"] == "break"
        assert "last_refined_context" in result
        assert "st_snapshot" in result
        director_mock.audit_strategic_plan.assert_called_once()

    def test_next_on_director_reject(self, s2_orch, valid_refined_arc):
        """Director REJECT → action=retry"""
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
        )
        with patch("modules.core.spinners.V50_MODULES_AVAILABLE", False):
            result = asyncio.run(s2_orch._preflight_finalize(**kwargs))

        assert result["action"] == "retry"
        assert "current_feedback" in result
        assert "director_feedback_for_fourphase" in result
        # director_feedback_for_fourphase should contain reject reason
        assert "구조적 문제" in result["director_feedback_for_fourphase"]


# ══════════════════════════════════════════════════════════════
# [4-R3-g] _preflight_enrichment — undefined-variable hardening
# ══════════════════════════════════════════════════════════════


class TestPreflightEnrichmentDefaults:
    """FourPhase 미사용/실패 시 안전 기본값 반환 확인."""

    REQUIRED_KEYS = {
        "four_phase_passed",
        "refined_arc",
        "generation_method",
        "draft_validator_passed",
        "consensus_passed",
        "st_snapshot",
        "director_feedback_for_fourphase",
        "was_patch",
        "patch_fallback",
        "prev_score",
    }

    def _make_enrichment_kwargs(self):
        return {
            "attempt": 0,
            "global_arc_no": 1,
            "current_ep_start": 1,
            "current_vol_strategy": {},
            "enriched_block": {"block_theme": "test"},
            "all_refined_arcs": [],
            "bible_root": {},
            "protagonist_name": "이청풍",
            "director_feedback_for_fourphase": "",
            "entity_registry_for_director": None,
            "genre_for_tracker": "wuxia",
        }

    def test_no_fourphase_agent_returns_safe_defaults(self, s2_orch):
        """FourPhase 에이전트가 없으면 모든 키가 안전 기본값으로 반환."""
        s2_orch.ctx.agents = {}  # four_phase 없음
        result = s2_orch._preflight_enrichment(**self._make_enrichment_kwargs())

        assert self.REQUIRED_KEYS == set(result.keys())
        assert result["four_phase_passed"] is False
        assert result["refined_arc"] is None
        assert result["generation_method"] == "analyst"
        assert result["draft_validator_passed"] is False
        assert result["consensus_passed"] is False
        assert result["st_snapshot"] is None

    def test_fourphase_exception_returns_safe_defaults(self, s2_orch):
        """FourPhase가 예외를 던지면 안전 기본값 + 에러 피드백 반환."""
        fp_mock = MagicMock()
        fp_mock.generate.side_effect = RuntimeError("boom")
        s2_orch.ctx.agents = {"four_phase": fp_mock}
        s2_orch.ctx.memory = None

        result = s2_orch._preflight_enrichment(**self._make_enrichment_kwargs())

        assert self.REQUIRED_KEYS == set(result.keys())
        assert result["four_phase_passed"] is False
        assert result["refined_arc"] is None
        assert result["generation_method"] == "analyst"
        assert "boom" in result["director_feedback_for_fourphase"]

    def test_fourphase_reject_returns_safe_defaults(self, s2_orch):
        """FourPhase REJECT(내부 검증 실패) 시 안전 기본값 반환."""
        fp_mock = MagicMock()
        fp_mock.generate.return_value = (
            None,  # four_phase_arc = None → REJECT path
            {"final_verdict": "REJECT", "phases": {"validate": {"issues_count": 3}}},
        )
        s2_orch.ctx.agents = {"four_phase": fp_mock}
        s2_orch.ctx.memory = None

        result = s2_orch._preflight_enrichment(**self._make_enrichment_kwargs())

        assert result["four_phase_passed"] is False
        assert result["refined_arc"] is None
        assert result["generation_method"] == "analyst"
        assert "검증 실패" in result["director_feedback_for_fourphase"]


# ══════════════════════════════════════════════════════════════
# [4-R3-h] _preflight_validation — REJECT path coverage
# ══════════════════════════════════════════════════════════════


class TestPreflightValidationRejectPaths:
    """_preflight_validation의 주요 REJECT 분기 단위테스트."""

    RETRY_REQUIRED_KEYS = {"action", "current_feedback"}
    PROCEED_REQUIRED_KEYS = {
        "action",
        "refined_arc",
        "draft_validator_passed",
        "consensus_passed",
        "suspected_duplicates",
        "corrections_made",  # [TF-25-09]
        "python_advisories",  # [TF-25-08]
    }

    def _base_kwargs(self, valid_refined_arc):
        return {
            "refined_arc": valid_refined_arc,
            "four_phase_passed": False,
            "all_refined_arcs": [],
            "entity_registry_for_director": None,
            "global_arc_no": 1,
            "current_ep_start": 1,
            "current_feedback": "",
            "generation_method": "analyst",
            "constraint_block": "",
            "enriched_block": {"block_theme": "test", "joint_docs": {}, "status_shadow": {}},
            "draft_validator_passed": False,
            "consensus_passed": False,
            "attempt": 0,
            "protagonist_name": "이청풍",
            "constraint_db": MagicMock(
                validate_arc_design=MagicMock(return_value={"valid": True, "violations": [], "warnings": []})
            ),
        }

    # ── 1) DraftValidator REJECT (CRITICAL issues, no corrector) ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", MagicMock())
    def test_draft_validator_reject_becomes_advisory(self, s2_orch, valid_refined_arc):
        """[TF-25-08] DraftValidator valid=False + CRITICAL → advisory로 전환, Director까지 도달."""
        s2_orch.ctx.arc_draft_validator = MagicMock()
        s2_orch.ctx.arc_draft_validator.validate.return_value = {
            "valid": False,
            "score": 35,
            "critical_issues": ["구조 불일치", "인과 단절"],
            "issues": [{"severity": "CRITICAL", "message": "구조 불일치"}],
            "advisory_issues": [],
            "warnings": [],
        }
        s2_orch.ctx.arc_corrector = None
        s2_orch.ctx.use_arc_corrector = False
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        s2_orch.ctx.stage2_optimizer = None

        kwargs = self._base_kwargs(valid_refined_arc)
        result = s2_orch._preflight_validation(**kwargs)

        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        assert any(a["source"] == "draft_validator" and "35" in a["message"] for a in advisories)
        assert any("구조 불일치" in a["message"] for a in advisories)

    # ── 2) Consensus REJECT ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    @patch("modules.core.spinners.rich_console", MagicMock())
    def test_consensus_reject_becomes_advisory(self, s2_orch, valid_refined_arc):
        """[TF-25-08] Consensus REJECT → advisory로 전환."""
        consensus_mock = MagicMock()
        consensus_mock.validate_with_consensus.return_value = (
            "REJECT",
            {
                "vote_summary": {"pass": 1, "reject": 2},
                "critical_issues": [
                    {"category": "plot_hole", "issue": "인과가 연결되지 않음"},
                ],
                "all_issues": [{"category": "plot_hole", "issue": "인과가 연결되지 않음"}],
            },
        )
        s2_orch.ctx.agents = {"consensus": consensus_mock}
        s2_orch.ctx.arc_draft_validator = None
        s2_orch.ctx.self_reflector = None
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        s2_orch.ctx.stage2_optimizer = None

        kwargs = self._base_kwargs(valid_refined_arc)
        result = s2_orch._preflight_validation(**kwargs)

        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        assert any(a["source"] == "consensus" and "Consensus" in a["message"] for a in advisories)
        assert any("plot_hole" in a["message"] for a in advisories)

    # ── 3) Flow Guard REJECT ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", None)
    def test_flow_guard_reject_becomes_advisory(self, s2_orch, valid_refined_arc):
        """[TF-25-08] FlowGuard REJECT → advisory로 전환."""
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(
            return_value={
                "status": "REJECT",
                "reason": "서사 정체",
                "feedback": "서사 폭주/정체 위험이 감지되었습니다.",
            }
        )
        s2_orch.ctx.arc_draft_validator = None
        s2_orch.ctx.stage2_optimizer = None

        kwargs = self._base_kwargs(valid_refined_arc)
        kwargs["four_phase_passed"] = True  # skip consensus/draft
        result = s2_orch._preflight_validation(**kwargs)

        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        assert any(a["source"] == "flow_guard" and "서사" in a["message"] for a in advisories)

    # ── 4) Duplicate Guard REJECT ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", None)
    def test_duplicate_guard_becomes_advisory(self, s2_orch, valid_refined_arc):
        """[TF-25-08] 직전 arc와 tactical_doc 중복 → advisory로 전환."""
        s2_orch.validation_pipeline._is_tactical_doc_duplicate = MagicMock(return_value=True)
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        s2_orch.ctx.arc_draft_validator = None
        s2_orch.ctx.stage2_optimizer = None

        prev_arc = {"arc_no": 0, "tactical_doc": "이전 아크 내용"}
        kwargs = self._base_kwargs(valid_refined_arc)
        kwargs["four_phase_passed"] = True  # skip consensus/draft
        kwargs["all_refined_arcs"] = [prev_arc]
        result = s2_orch._preflight_validation(**kwargs)

        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        assert any(a["source"] == "duplicate_guard" for a in advisories)

    # ── 5) ContinuityInspector REJECT ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", MagicMock())
    def test_continuity_reject_becomes_advisory(self, s2_orch, valid_refined_arc):
        """[TF-25-08] ContinuityInspector REJECT → advisory로 전환."""
        ci_mock = MagicMock()
        ci_mock.inspect_arc.return_value = {
            "decision": "REJECT",
            "severity": "HIGH",
            "fix_instructions": "NPC 상태를 수정하세요",
            "violations": [
                {"type": "npc_state", "description": "사망한 NPC가 활동 중"},
            ],
        }
        s2_orch.ctx.agents = {"continuity_inspector": ci_mock}
        s2_orch.ctx.failure_learner = None
        s2_orch.ctx.pass_rate_monitor = None
        s2_orch.ctx.stage2_optimizer = None
        s2_orch.ctx.arc_draft_validator = None
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})

        kwargs = self._base_kwargs(valid_refined_arc)
        result = s2_orch._preflight_validation(**kwargs)

        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        assert any(a["source"] == "continuity_inspector" for a in advisories)
        # ctx 콜백 호출 확인
        s2_orch.ctx.build_strong_kind_feedback.assert_called_once()
        s2_orch.ctx.build_focused_context.assert_called_once()

    # ── 6) enriched_block 무효 → retry ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", None)
    def test_invalid_enriched_block_returns_retry(self, s2_orch, valid_refined_arc):
        """enriched_block=None → retry + 농축 데이터 누락 피드백."""
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        s2_orch.ctx.arc_draft_validator = None
        s2_orch.ctx.stage2_optimizer = None

        kwargs = self._base_kwargs(valid_refined_arc)
        kwargs["four_phase_passed"] = True
        kwargs["enriched_block"] = None
        result = s2_orch._preflight_validation(**kwargs)

        assert result["action"] == "retry"
        assert "농축" in result["current_feedback"] or "데이터" in result["current_feedback"]

    # ── 7) proceed 경로 필수 키 회귀 확인 (보강) ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", None)
    def test_proceed_keys_with_all_validators_off(self, s2_orch, valid_refined_arc):
        """모든 validator off + 유효 arc → proceed + 필수 5키 + 값 타입 검증."""
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        s2_orch.ctx.arc_draft_validator = None
        s2_orch.ctx.stage2_optimizer = None

        kwargs = self._base_kwargs(valid_refined_arc)
        kwargs["four_phase_passed"] = True
        result = s2_orch._preflight_validation(**kwargs)

        assert result["action"] == "proceed"
        assert self.PROCEED_REQUIRED_KEYS == set(result.keys())
        assert isinstance(result["refined_arc"], dict)
        assert isinstance(result["draft_validator_passed"], bool)
        assert isinstance(result["consensus_passed"], bool)
        assert isinstance(result["suspected_duplicates"], list)

    # ── [4-R3-i] ArcCorrector correct() 실패 → retry ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", MagicMock())
    def test_arc_corrector_correct_fails_becomes_advisory(self, s2_orch, valid_refined_arc):
        """[TF-25-08] can_correct=True이지만 correct() 실패 → advisory로 전환."""
        s2_orch.ctx.arc_draft_validator = MagicMock()
        s2_orch.ctx.arc_draft_validator.validate.return_value = {
            "valid": False,
            "score": 55,
            "critical_issues": [],
            "advisory_issues": [],
            "warnings": ["인과 약함"],
        }
        corrector = MagicMock()
        corrector.can_correct.return_value = (True, [{"message": "인과 약함"}], [])
        corrector.correct.return_value = (None, {"success": False, "reason": "수정 실패"})
        s2_orch.ctx.arc_corrector = corrector
        s2_orch.ctx.use_arc_corrector = True
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        s2_orch.ctx.stage2_optimizer = None

        kwargs = self._base_kwargs(valid_refined_arc)
        result = s2_orch._preflight_validation(**kwargs)

        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        assert any("수정 불가" in a["message"] or "V60.42" in a["message"] for a in advisories)

    # ── [4-R3-i] ArcCorrector 교정 후 revalidation 실패 → retry ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", MagicMock())
    def test_arc_corrector_revalidation_fails_becomes_advisory(self, s2_orch, valid_refined_arc):
        """[TF-25-08] correct() 성공이지만 revalidation 실패 → advisory로 전환."""
        corrected_arc = dict(valid_refined_arc)
        corrected_arc["tactical_doc"] = "수정된 내용 " * 100

        validator = MagicMock()
        validator.validate.side_effect = [
            {
                "valid": True,
                "score": 80,
                "critical_issues": [],
                "advisory_issues": [],
                "warnings": [],
            },
            {
                "valid": False,
                "score": 50,
                "critical_issues": [],
                "advisory_issues": [],
                "warnings": ["인과 약함"],
            },
            {
                "valid": False,
                "score": 60,
                "critical_issues": ["여전히 부족"],
                "advisory_issues": [],
                "warnings": [],
            },
        ]
        s2_orch.ctx.arc_draft_validator = validator

        corrector = MagicMock()
        corrector.can_correct.return_value = (True, [{"message": "인과 약함"}], [])
        corrector.correct.return_value = (
            corrected_arc,
            {"success": True, "corrections_made": [{"change_summary": "인과 보강"}], "corrections_failed": []},
        )
        s2_orch.ctx.arc_corrector = corrector
        s2_orch.ctx.use_arc_corrector = True
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})
        s2_orch.ctx.stage2_optimizer = None

        kwargs = self._base_kwargs(valid_refined_arc)
        result = s2_orch._preflight_validation(**kwargs)

        assert result["action"] == "proceed"
        advisories = result.get("python_advisories", [])
        assert any("ArcCorrector" in a["message"] or "수정 후" in a["message"] for a in advisories)

    # ── [4-R3-i] SelfReflector가 arc를 변경 → 변경 arc로 진행 ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    @patch("modules.core.spinners.rich_console", None)
    def test_self_reflector_mutation_changes_arc(self, s2_orch, valid_refined_arc):
        """SelfReflector가 arc JSON을 개선 → 변경된 arc로 proceed."""
        import json

        improved = dict(valid_refined_arc)
        improved["tactical_doc"] = "개선된 전술 설계 " * 100
        improved_json = json.dumps(improved, ensure_ascii=False)

        reflection_result = MagicMock()
        reflection_result.improved = improved_json
        reflection_result.improvement_score = 15

        reflector = MagicMock()
        reflector.reflect_and_improve.return_value = reflection_result
        s2_orch.ctx.self_reflector = reflector

        s2_orch.ctx.arc_draft_validator = None
        s2_orch.ctx.stage2_optimizer = None
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})

        # SelfReflector needs: V50=True, generation_method="analyst", ReflectionTarget
        # We mock ReflectionTarget via the import mechanism
        with patch("modules.core.self_reflection.ReflectionTarget") as mock_rt:
            mock_rt.ANALYST = "ANALYST"
            kwargs = self._base_kwargs(valid_refined_arc)
            kwargs["four_phase_passed"] = True
            result = s2_orch._preflight_validation(**kwargs)

        assert result["action"] == "proceed"
        assert result["refined_arc"]["tactical_doc"].startswith("개선된")

    # ── [4-R3-i] SelfReflector JSON 파싱 실패 → 원본 유지 ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", True)
    @patch("modules.core.spinners.rich_console", None)
    def test_self_reflector_json_error_keeps_original(self, s2_orch, valid_refined_arc):
        """SelfReflector가 비정상 JSON 반환 → 원본 arc 유지, proceed."""
        reflection_result = MagicMock()
        reflection_result.improved = "NOT VALID JSON {{{}"

        reflector = MagicMock()
        reflector.reflect_and_improve.return_value = reflection_result
        s2_orch.ctx.self_reflector = reflector

        s2_orch.ctx.arc_draft_validator = None
        s2_orch.ctx.stage2_optimizer = None
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})

        with patch("modules.core.self_reflection.ReflectionTarget") as mock_rt:
            mock_rt.ANALYST = "ANALYST"
            kwargs = self._base_kwargs(valid_refined_arc)
            kwargs["four_phase_passed"] = True
            result = s2_orch._preflight_validation(**kwargs)

        assert result["action"] == "proceed"
        # 원본 arc가 그대로 유지됨
        assert result["refined_arc"]["tactical_doc"] == valid_refined_arc["tactical_doc"]

    # ── [4-R3-i] Consensus 예외 → 비전파, 다음 단계 진행 ──

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    @patch("modules.core.spinners.rich_console", MagicMock())
    def test_consensus_exception_non_propagating(self, s2_orch, valid_refined_arc):
        """Consensus 호출 중 예외 → 예외 비전파 + proceed."""
        consensus_mock = MagicMock()
        consensus_mock.validate_with_consensus.side_effect = RuntimeError("API timeout")
        s2_orch.ctx.agents = {"consensus": consensus_mock}
        s2_orch.ctx.arc_draft_validator = None
        s2_orch.ctx.self_reflector = None
        s2_orch.ctx.stage2_optimizer = None
        s2_orch.validation_pipeline._stage2_flow_guard = MagicMock(return_value={"status": "PASS"})

        kwargs = self._base_kwargs(valid_refined_arc)
        result = s2_orch._preflight_validation(**kwargs)

        # 예외가 전파되지 않고 proceed로 진행
        assert result["action"] == "proceed"
        # consensus는 스킵되었으므로 consensus_passed=False
        assert result["consensus_passed"] is False


# ══════════════════════════════════════════════════════════════
# Test: [Phase 3-QR] Quality Trend in _preflight_arc_analysis
# ══════════════════════════════════════════════════════════════


class TestQualityTrendInjection:
    """_preflight_arc_analysis 내 품질 추세 주입 테스트."""

    @staticmethod
    def _base_kwargs():
        """_preflight_arc_analysis 최소 호출 kwargs."""
        return {
            "attempt": 0,
            "current_feedback": "",
            "constraint_block": "",
            "last_refined_context": "기존 컨텍스트",
            "all_refined_arcs": [],
            "protagonist_name": "이청풍",
            "global_arc_no": 1,
            "cached_preflight_injection": "",
            "cached_preflight_result": None,
        }

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_trend_summary_injected(self, s2_orch):
        """quality_dashboard 추세 경로가 반환 계약을 깨지 않는지 확인."""
        s2_orch.ctx.stage2_optimizer = None  # optimizer 비활성화하여 문자열 보존
        s2_orch.ctx.quality_dashboard = MagicMock()
        s2_orch.ctx.quality_dashboard.get_score_trend_summary.return_value = {
            "trend": "down",
            "summary": "최근 3화 평균 72점, 추세: 하락 (직전 대비 -8)",
            "window_size": 5,
            "avg": 72.0,
            "min": 65,
            "max": 80,
            "delta": -8,
            "samples": 3,
        }
        s2_orch.ctx.stage_rejection_history = []
        result = s2_orch._preflight_arc_analysis(**self._base_kwargs())
        s2_orch.ctx.quality_dashboard.get_score_trend_summary.assert_called_once_with(stage=2)
        assert "enhanced_context" not in result

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_trend_insufficient_data_no_injection(self, s2_orch):
        """데이터 부족 경로에서도 반환 계약이 유지되는지 확인."""
        s2_orch.ctx.quality_dashboard = MagicMock()
        s2_orch.ctx.quality_dashboard.get_score_trend_summary.return_value = {
            "trend": "insufficient_data",
            "summary": "데이터 부족 (1화)",
            "window_size": 5,
            "avg": 0,
            "min": 0,
            "max": 0,
            "delta": 0,
            "samples": 1,
        }
        s2_orch.ctx.stage_rejection_history = []
        result = s2_orch._preflight_arc_analysis(**self._base_kwargs())
        s2_orch.ctx.quality_dashboard.get_score_trend_summary.assert_called_once_with(stage=2)
        assert "enhanced_context" not in result

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_dashboard_none_no_crash(self, s2_orch):
        """quality_dashboard=None이면 크래시 없이 진행."""
        s2_orch.ctx.quality_dashboard = None
        s2_orch.ctx.stage_rejection_history = []
        result = s2_orch._preflight_arc_analysis(**self._base_kwargs())
        assert "enhanced_context" not in result

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_dashboard_exception_non_propagating(self, s2_orch):
        """quality_dashboard 예외 시 비전파."""
        s2_orch.ctx.stage2_optimizer = None  # optimizer 비활성화하여 문자열 보존
        s2_orch.ctx.quality_dashboard = MagicMock()
        s2_orch.ctx.quality_dashboard.get_score_trend_summary.side_effect = RuntimeError("crash")
        s2_orch.ctx.stage_rejection_history = []
        result = s2_orch._preflight_arc_analysis(**self._base_kwargs())
        s2_orch.ctx.quality_dashboard.get_score_trend_summary.assert_called_once_with(stage=2)
        assert "enhanced_context" not in result


# ══════════════════════════════════════════════════════════════
# [Item4] Stage 4→2 reverse feedback injection in _preflight_arc_analysis
# ══════════════════════════════════════════════════════════════


class TestStage4To2FeedbackInjection:
    @staticmethod
    def _base_kwargs():
        return {
            "attempt": 0,
            "current_feedback": "",
            "constraint_block": "",
            "last_refined_context": "기존 컨텍스트",
            "all_refined_arcs": [],
            "protagonist_name": "이청풍",
            "global_arc_no": 2,
            "cached_preflight_injection": "",
            "cached_preflight_result": None,
        }

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_injects_stage4_to_2_feedback_when_hard(self, s2_orch):
        s2_orch.ctx.stage2_optimizer = None
        s2_orch.ctx.quality_dashboard = None
        s2_orch.ctx.stage_rejection_history = []
        s2_orch.ctx.generate_reverse_feedback_stage4_to_2 = MagicMock(return_value="[S4->S2] 난이도 완화 지시")
        s2_orch.ctx.pass_rate_monitor.get_arc_difficulty = MagicMock(
            return_value={"arc_no": 1, "difficulty": "hard", "avg_attempts": 3.2, "hard_episodes": [7, 8]}
        )

        result = s2_orch._preflight_arc_analysis(**self._base_kwargs())

        assert "enhanced_context" not in result
        s2_orch.ctx.audit_event.assert_any_call(
            "s4_to_s2_feedback",
            "Arc difficulty feedback injected",
            {
                "arc_no": 2,
                "prev_difficulty": {"arc_no": 1, "difficulty": "hard", "avg_attempts": 3.2, "hard_episodes": [7, 8]},
            },
        )

    @patch("modules.core.spinners.V50_MODULES_AVAILABLE", False)
    def test_no_injection_when_feedback_empty(self, s2_orch):
        s2_orch.ctx.stage2_optimizer = None
        s2_orch.ctx.quality_dashboard = None
        s2_orch.ctx.stage_rejection_history = []
        s2_orch.ctx.generate_reverse_feedback_stage4_to_2 = MagicMock(return_value="")
        s2_orch.ctx.pass_rate_monitor.get_arc_difficulty = MagicMock(
            return_value={"arc_no": 1, "difficulty": "normal", "avg_attempts": 1.8, "hard_episodes": []}
        )

        result = s2_orch._preflight_arc_analysis(**self._base_kwargs())

        assert "enhanced_context" not in result
        assert not any(c.args and c.args[0] == "s4_to_s2_feedback" for c in s2_orch.ctx.audit_event.call_args_list)


# ══════════════════════════════════════════════════════════════
# [Phase 3-Obs] Preflight parallel PerfTimer instrumentation
# ══════════════════════════════════════════════════════════════


class TestPreflightParallelTimer:
    """ThreadPoolExecutor 병렬 구간 PerfTimer 계측 검증."""

    def _make_setup_kwargs(self):
        return {
            "all_refined_arcs": [{"arc_no": 1, "tactical_doc": "test"}],
            "arcs_source": [{"arc_no": 1}],
            "arc_idx": 0,
            "lack_report": {},
            "grand_obj": "천하제일",
            "global_arc_no": 3,
            "constraint_db": MagicMock(generate_constraint_block=MagicMock(return_value="")),
        }

    def test_outer_timer_start_stop(self, s2_orch):
        """외곽 타이머 s2_arc_{N}_preflight_parallel start/stop 호출 확인."""
        s2_orch.ctx.agents = {
            "weaver": MagicMock(generate_arc_drive=MagicMock(return_value={"desire_vector": "ok"})),
        }
        s2_orch._preflight_state_setup(**self._make_setup_kwargs())

        start_calls = [c[0][0] for c in s2_orch.ctx.perf_timer.start.call_args_list]
        stop_calls = [c[0][0] for c in s2_orch.ctx.perf_timer.stop.call_args_list]
        assert "s2_arc_3_preflight_parallel" in start_calls
        assert "s2_arc_3_preflight_parallel" in stop_calls

    def test_inner_timers_arc_drive_and_preflight(self, s2_orch):
        """개별 타이머 s2_arc_{N}_arc_drive, s2_arc_{N}_preflight_analysis 호출 확인."""
        s2_orch.ctx.agents = {
            "weaver": MagicMock(generate_arc_drive=MagicMock(return_value={"desire_vector": "ok"})),
            "preflight": MagicMock(
                analyze=MagicMock(return_value={"item_timeline": []}),
                generate_analyst_injection=MagicMock(return_value="injection"),
            ),
        }
        s2_orch._preflight_state_setup(**self._make_setup_kwargs())

        start_calls = [c[0][0] for c in s2_orch.ctx.perf_timer.start.call_args_list]
        stop_calls = [c[0][0] for c in s2_orch.ctx.perf_timer.stop.call_args_list]
        assert "s2_arc_3_arc_drive" in start_calls
        assert "s2_arc_3_arc_drive" in stop_calls
        assert "s2_arc_3_preflight_analysis" in start_calls
        assert "s2_arc_3_preflight_analysis" in stop_calls

    def test_all_three_timers_recorded(self, s2_orch):
        """3개 타이머(parallel + arc_drive + preflight_analysis) 모두 start/stop 호출."""
        s2_orch.ctx.agents = {
            "weaver": MagicMock(generate_arc_drive=MagicMock(return_value={"desire_vector": "ok"})),
            "preflight": MagicMock(
                analyze=MagicMock(return_value={"item_timeline": []}),
                generate_analyst_injection=MagicMock(return_value="injection"),
            ),
        }
        s2_orch._preflight_state_setup(**self._make_setup_kwargs())

        start_calls = {c[0][0] for c in s2_orch.ctx.perf_timer.start.call_args_list}
        stop_calls = {c[0][0] for c in s2_orch.ctx.perf_timer.stop.call_args_list}
        expected = {
            "s2_arc_3_preflight_parallel",
            "s2_arc_3_arc_drive",
            "s2_arc_3_preflight_analysis",
        }
        assert expected <= start_calls
        assert expected <= stop_calls

    def test_perf_timer_none_no_crash(self, s2_orch):
        """perf_timer=None일 때 _preflight_state_setup() 정상 반환."""
        s2_orch.ctx.perf_timer = None
        s2_orch.ctx.agents = {
            "weaver": MagicMock(generate_arc_drive=MagicMock(return_value={"desire_vector": "ok"})),
        }
        result = s2_orch._preflight_state_setup(**self._make_setup_kwargs())
        assert "arc_drive" in result
        assert result["arc_drive"]["desire_vector"] == "ok"

    def test_perf_timer_exception_non_propagating(self, s2_orch):
        """perf_timer.start/stop 예외 시 비전파, 파이프라인 정상 완료."""
        s2_orch.ctx.perf_timer = MagicMock()
        s2_orch.ctx.perf_timer.start.side_effect = RuntimeError("timer broken")
        s2_orch.ctx.perf_timer.stop.side_effect = RuntimeError("timer broken")
        s2_orch.ctx.agents = {
            "weaver": MagicMock(generate_arc_drive=MagicMock(return_value={"desire_vector": "ok"})),
        }
        result = s2_orch._preflight_state_setup(**self._make_setup_kwargs())
        assert "arc_drive" in result
        assert result["arc_drive"]["desire_vector"] == "ok"
