"""[Phase 3-5B] Stage4Orchestrator 패치 모드 단위 테스트

검증 대상:
- 패치 모드 진입 (score 50~79, round 1)
- 패치 실패 시 full rewrite 폴백
- 저점(score < 50) → 기존 regenerate_with_feedback
- round 2 → score 무관 full rewrite
- round 0 → generate_ensemble (변경 없음)
- REJECT 시 best_manuscript 저장
"""

import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.chain_of_verification import ChainOfVerificationParseError
from modules.core.constants import PatchModeThresholds


def _process_pass_result_via_post_processor(orch, **kwargs):
    """[B-1-1] Stage4 post-processing delegation helper for tests."""
    from modules.core.stage4_orchestrator import _detect_cross_episode_repetition, _detect_npc_overexposure

    return orch.post_processor.process_pass_result(
        **kwargs,
        extract_chain_link_fn=orch._extract_chain_link,
        detect_npc_overexposure_fn=_detect_npc_overexposure,
        detect_cross_episode_repetition_fn=_detect_cross_episode_repetition,
    )


# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def mock_app():
    """SovereignApp mock"""
    app = MagicMock()
    app.ui = MagicMock()
    app.ui.log = MagicMock()
    app.ui.console = MagicMock()
    app.selected_genre = {"type": "wuxia", "name": "무협"}
    app.current_project = MagicMock()
    app.current_project.db = MagicMock()
    app.current_project.master_bible = {
        "MasterBible": {
            "ProjectData": {"CoreIdentity": {"desire": "천하제일"}},
            "AssetLibrary": {"KeyNPCs": [], "Key_Items": []},
            "protagonist_config": {"world_origin": "현대인", "incarnation_type": "회귀자"},
        }
    }
    app.current_project.arcs = []
    app.current_project.name = "test_project"
    app.current_project.paths = MagicMock()
    app.current_project.paths.root = Path("/tmp/test_project_root")
    app.current_project.paths.drafts = Path("/tmp/test_drafts")
    app.perf_timer = MagicMock()
    app.sys = MagicMock()
    app.sys.api_client = MagicMock()
    app.agents = {"director": MagicMock(), "writer": MagicMock(), "manager": MagicMock()}
    app.character_voice = None
    app.diversity_engine = None
    app.memory = MagicMock()
    app.failure_learner = None
    app.foreshadow_tracker = None
    app.state_tracker = None
    return app


@pytest.fixture
def mock_chief_writer():
    """ChiefWriter mock"""
    cw = MagicMock()
    cw.generate_ensemble = MagicMock(
        return_value=[
            {"text": "후보A 원고", "strategy_name": "balanced"},
            {"text": "후보B 원고", "strategy_name": "narrative"},
            {"text": "후보C 원고", "strategy_name": "tension"},
        ]
    )
    cw.regenerate_with_feedback = MagicMock(
        return_value=[
            {"text": "재작성A", "strategy_name": "balanced"},
            {"text": "재작성B", "strategy_name": "narrative"},
            {"text": "재작성C", "strategy_name": "tension"},
        ]
    )
    cw.patch_with_feedback = MagicMock(
        return_value=[
            {"text": "패치 단일 재생성", "strategy_name": "balanced"},
        ]
    )
    return cw


# ══════════════════════════════════════════════════════════════
# Test: PatchModeThresholds 상수 확인
# ══════════════════════════════════════════════════════════════


class TestPatchModeThresholds:
    def test_rewrite_threshold(self):
        assert PatchModeThresholds.REWRITE == 50

    def test_inplace_threshold(self):
        assert PatchModeThresholds.INPLACE == 60

    def test_rewrite_less_than_inplace(self):
        assert PatchModeThresholds.REWRITE < PatchModeThresholds.INPLACE


class TestStage4AuditSummary:
    def test_stage4_writer_forwards_skip_pause_to_interview_loop(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.agents = mock_app.agents
        ctx.state_tracker = None
        ctx.memory = None
        ctx.context_advisor = None
        ctx.perf_timer = MagicMock()
        ctx.sys = mock_app.sys
        ctx.audit_event = MagicMock()
        ctx.write_audit_summary = MagicMock()

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._prepare_stage4_session = MagicMock(return_value=object())
        orch._run_interview_loop = MagicMock(return_value=False)

        orch.stage_4_v2_chief_writer(skip_pause=True)

        orch._run_interview_loop.assert_called_once_with(ANY, skip_pause=True)

    def test_stage4_completion_writes_runtime_audit_summary(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.agents = mock_app.agents
        ctx.state_tracker = None
        ctx.memory = None
        ctx.context_advisor = None
        ctx.perf_timer = MagicMock()
        ctx.sys = mock_app.sys
        ctx.audit_event = MagicMock()
        ctx.write_audit_summary = MagicMock()
        mock_app._audit_event = None
        mock_app._write_audit_summary = None

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._prepare_stage4_session = MagicMock(return_value=object())
        orch._run_interview_loop = MagicMock(return_value=False)

        orch.stage_4_v2_chief_writer()

        ctx.audit_event.assert_called_once()
        ctx.write_audit_summary.assert_called_once_with("stage4_complete")

    def test_stage4_completion_is_blocked_after_settlement_failure(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.agents = mock_app.agents
        ctx.state_tracker = None
        ctx.memory = None
        ctx.context_advisor = None
        ctx.perf_timer = MagicMock()
        ctx.sys = mock_app.sys
        ctx.audit_event = MagicMock()
        ctx.write_audit_summary = MagicMock()

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._prepare_stage4_session = MagicMock(return_value=object())

        def _fail_settlement(*_args, **_kwargs):
            orch._stage4_completion_blocked = True
            return False

        orch._run_interview_loop = MagicMock(side_effect=_fail_settlement)

        orch.stage_4_v2_chief_writer()

        ctx.audit_event.assert_not_called()
        ctx.write_audit_summary.assert_not_called()

    def test_log_target_ep_reached_writes_control_decision_and_audit_event(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.agents = mock_app.agents
        ctx.state_tracker = None
        ctx.memory = None
        ctx.context_advisor = None
        ctx.perf_timer = MagicMock()
        ctx.sys = mock_app.sys
        ctx.session_logger = MagicMock()
        ctx.audit_event = MagicMock()
        ctx.current_project.metrics_session_id = "sess-stage4"

        orch = Stage4Orchestrator(mock_app, context=ctx)

        orch._log_target_ep_reached(target_ep=2, next_ep=3)

        ctx.session_logger.log_decision.assert_called_once()
        decision_kwargs = ctx.session_logger.log_decision.call_args.kwargs
        assert decision_kwargs["stage"] == "stage4_control"
        assert decision_kwargs["decision_type"] == "target_ep_reached"
        assert decision_kwargs["ep_num"] == 2
        assert decision_kwargs["session_id"] == "sess-stage4"
        assert decision_kwargs["next_ep"] == 3

        ctx.audit_event.assert_called_once_with(
            "target_ep_reached",
            "stage4 target episode reached",
            {"session_id": "sess-stage4", "target_ep": 2, "next_ep": 3},
        )

    def test_log_stage4_session_scope_writes_control_decision_and_audit_event(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.metrics_session_id = "sess-scope"
        ctx.agents = mock_app.agents
        ctx.state_tracker = None
        ctx.memory = None
        ctx.context_advisor = None
        ctx.perf_timer = MagicMock()
        ctx.sys = mock_app.sys
        ctx.session_logger = MagicMock()
        ctx.audit_event = MagicMock()

        orch = Stage4Orchestrator(mock_app, context=ctx)

        orch._log_stage4_session_scope(start_ep=2, target_ep=3, total_planned_ep=10)

        ctx.session_logger.log_decision.assert_called_once()
        decision_kwargs = ctx.session_logger.log_decision.call_args.kwargs
        assert decision_kwargs["decision_type"] == "session_scope"
        assert decision_kwargs["result"] == "START"
        assert decision_kwargs["ep_num"] == 2
        assert decision_kwargs["session_id"] == "sess-scope"
        assert decision_kwargs["target_ep"] == 3
        assert decision_kwargs["total_planned_ep"] == 10

        ctx.audit_event.assert_called_once_with(
            "stage4_session_scope",
            "stage4 session scope declared",
            {
                "session_id": "sess-scope",
                "start_ep": 2,
                "target_ep": 3,
                "total_planned_ep": 10,
            },
        )

    def test_stage4_early_return_does_not_write_runtime_audit_summary(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.agents = mock_app.agents
        ctx.state_tracker = None
        ctx.memory = None
        ctx.context_advisor = None
        ctx.perf_timer = MagicMock()
        ctx.sys = mock_app.sys
        ctx.write_audit_summary = MagicMock()

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._prepare_stage4_session = MagicMock(return_value=object())
        orch._run_interview_loop = MagicMock(return_value=True)

        orch.stage_4_v2_chief_writer()

        ctx.write_audit_summary.assert_not_called()

    def test_stage4_failed_exhaustion_does_not_write_runtime_audit_summary(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.agents = mock_app.agents
        ctx.state_tracker = None
        ctx.memory = None
        ctx.context_advisor = None
        ctx.perf_timer = MagicMock()
        ctx.sys = mock_app.sys
        ctx.write_audit_summary = MagicMock()

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._prepare_stage4_session = MagicMock(return_value=object())
        # 5라운드 소진 후 인간 검토 필요 → _run_interview_loop() returns True
        orch._run_interview_loop = MagicMock(return_value=True)

        orch.stage_4_v2_chief_writer()

        ctx.write_audit_summary.assert_not_called()

    def test_stage4_interrupt_does_not_write_runtime_audit_summary(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.agents = mock_app.agents
        ctx.state_tracker = None
        ctx.memory = None
        ctx.context_advisor = None
        ctx.perf_timer = MagicMock()
        ctx.sys = mock_app.sys
        ctx.flush_audit_buffer = MagicMock()
        ctx.safe_commit = MagicMock()
        ctx.write_audit_summary = MagicMock()

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._prepare_stage4_session = MagicMock(return_value=object())
        orch._run_interview_loop = MagicMock(side_effect=KeyboardInterrupt)

        orch.stage_4_v2_chief_writer()

        ctx.write_audit_summary.assert_not_called()
        ctx.flush_audit_buffer.assert_called_once()
        ctx.safe_commit.assert_called_once()

    def test_stage4_interrupt_logs_commit_failure(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.agents = mock_app.agents
        ctx.state_tracker = None
        ctx.memory = None
        ctx.context_advisor = None
        ctx.perf_timer = MagicMock()
        ctx.sys = mock_app.sys
        ctx.flush_audit_buffer = MagicMock()
        ctx.safe_commit = MagicMock(return_value=False)
        ctx.write_audit_summary = MagicMock()

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._prepare_stage4_session = MagicMock(return_value=object())
        orch._run_interview_loop = MagicMock(side_effect=KeyboardInterrupt)

        orch.stage_4_v2_chief_writer()

        assert any("interrupt cleanup commit failed" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)

    def test_log_escalation_event_uses_project_root_logs_dir(self, mock_app, tmp_path, monkeypatch):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        monkeypatch.chdir(tmp_path)
        mock_app.current_project.name = "fallback_project"
        mock_app.current_project.paths.root = tmp_path / "actual_project"
        ctx = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._log_escalation_event(3, "TEST_EVENT", 2, success=True)

        expected_path = mock_app.current_project.paths.root / "logs" / "episode_production.jsonl"
        fallback_path = tmp_path / "projects" / "fallback_project" / "logs" / "episode_production.jsonl"
        assert expected_path.exists()
        assert not fallback_path.exists()
        rows = [json.loads(line) for line in expected_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert rows[-1]["event"] == "TEST_EVENT"

    def test_log_escalation_event_includes_optional_runtime_context(self, mock_app, tmp_path, monkeypatch):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        monkeypatch.chdir(tmp_path)
        mock_app.current_project.name = "context_project"
        mock_app.current_project.paths.root = tmp_path / "context_project"
        ctx = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._log_escalation_event(
            5,
            "TEST_EVENT",
            3,
            success=False,
            round_num=2,
            attempt_key="s4:ep5:r3",
            fix_scope="partial",
            reason="history conflict repeated",
            contradiction_type="timeline",
            candidate_key="V75-D|blueprint_inplace",
            content_hash="hash-123",
            artifact_path="logs/artifacts/stage4/ep_0005/attempt_02/patched_blueprint_after_fix__V75-D_blueprint_inplace.json",
        )

        expected_path = mock_app.current_project.paths.root / "logs" / "episode_production.jsonl"
        rows = [json.loads(line) for line in expected_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        payload = rows[-1]
        assert payload["round_num"] == 2
        assert payload["attempt_key"] == "s4:ep5:r3"
        assert payload["fix_scope"] == "partial"
        assert payload["reason"] == "history conflict repeated"
        assert payload["contradiction_type"] == "timeline"
        assert payload["candidate_key"] == "V75-D|blueprint_inplace"
        assert payload["content_hash"] == "hash-123"
        assert payload["artifact_path"].endswith("patched_blueprint_after_fix__V75-D_blueprint_inplace.json")


class TestPrepareStage4SessionLimits:
    def test_initialize_session_agents_builds_all_agents_with_selected_genre(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionAgentBootstrap

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.sys = mock_app.sys
        ctx.selected_genre = {"type": "investment"}

        orch = Stage4Orchestrator(mock_app, context=ctx)
        chief_writer_cls = MagicMock(return_value="chief")
        manuscript_validator_cls = MagicMock(return_value="validator")
        consistency_validator_cls = MagicMock(return_value="consistency")
        blocking_validator_cls = MagicMock(return_value="blocking")
        continuity_validator_cls = MagicMock(return_value="continuity")

        result = orch._initialize_session_agents(
            chief_writer_cls=chief_writer_cls,
            manuscript_validator_cls=manuscript_validator_cls,
            consistency_validator_cls=consistency_validator_cls,
            blocking_validator_cls=blocking_validator_cls,
            continuity_validator_cls=continuity_validator_cls,
            writer_model="writer-model",
        )

        assert isinstance(result, _SessionAgentBootstrap)
        assert result.s4_genre_type == "investment"
        assert result.chief_writer == "chief"
        assert result.manuscript_validator == "validator"
        assert result.consistency_validator == "consistency"
        assert result.blocking_validator == "blocking"
        assert result.continuity_validator == "continuity"
        chief_writer_cls.assert_called_once_with(
            context=ctx.current_project,
            client=ctx.sys.api_client,
            model_tier="writer-model",
        )
        manuscript_validator_cls.assert_called_once_with(
            context=ctx.current_project,
            genre_type="investment",
            llm_client=ctx.sys.api_client,
        )
        consistency_validator_cls.assert_called_once_with(
            guard=ctx.sys.guard,
            genre="investment",
        )
        blocking_validator_cls.assert_called_once_with(context=ctx.current_project)
        continuity_validator_cls.assert_called_once_with(context=ctx.current_project)

    def test_initialize_session_agents_falls_back_to_wuxia_without_selected_genre(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionAgentBootstrap

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.sys = mock_app.sys
        ctx.selected_genre = None

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._initialize_session_agents(
            chief_writer_cls=MagicMock(return_value="chief"),
            manuscript_validator_cls=MagicMock(return_value="validator"),
            consistency_validator_cls=MagicMock(return_value="consistency"),
            blocking_validator_cls=MagicMock(return_value="blocking"),
            continuity_validator_cls=MagicMock(return_value="continuity"),
            writer_model="writer-model",
        )

        assert isinstance(result, _SessionAgentBootstrap)
        assert result.s4_genre_type == "wuxia"

    def test_prepare_session_environment_creates_output_dir_and_reads_episode_counters(self, mock_app, tmp_path):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionEnvironmentPayload

        drafts_dir = tmp_path / "drafts"
        mock_app.current_project.paths.drafts = drafts_dir
        mock_app.current_project.db.get_latest_blueprint_number.return_value = 7
        mock_app.current_project.get_latest_episode_number.return_value = 5

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._prepare_session_environment()

        assert isinstance(result, _SessionEnvironmentPayload)
        assert result.output_dir == drafts_dir
        assert result.total_planned_ep == 7
        assert result.current_written == 4
        assert drafts_dir.exists()

    def test_prepare_session_environment_clamps_current_written_to_zero(self, mock_app, tmp_path):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionEnvironmentPayload

        drafts_dir = tmp_path / "drafts"
        mock_app.current_project.paths.drafts = drafts_dir
        mock_app.current_project.db.get_latest_blueprint_number.return_value = 0
        mock_app.current_project.get_latest_episode_number.return_value = 0

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._prepare_session_environment()

        assert isinstance(result, _SessionEnvironmentPayload)
        assert result.output_dir == drafts_dir
        assert result.total_planned_ep == 0
        assert result.current_written == 0

    def test_prepare_session_ui_logs_banner_and_clears_console(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.ui.console = MagicMock()
        ctx.ui.title = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)

        orch._prepare_session_ui(writer_model="writer-model")

        assert ctx.ui.log.call_count == 4
        ctx.ui.log.assert_any_call("🎬 [V60.80] Stage 4 V2 - Chief Writer 주권주의 아키텍처 가동")
        ctx.ui.log.assert_any_call("   • Chief Writer 모델: writer-model")
        ctx.ui.console.clear.assert_called_once()
        ctx.ui.title.assert_called_once_with("V60.80 CHIEF WRITER", "Director 주권주의 아키텍처")

    def test_build_session_config_maps_bootstrap_environment_and_prompt_fields(self, mock_app):
        from modules.core.stage4_orchestrator import (
            Stage4Orchestrator,
            _SessionAgentBootstrap,
            _SessionConfig,
            _SessionEnvironmentPayload,
        )

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        agent_bootstrap = _SessionAgentBootstrap(
            chief_writer="chief",
            manuscript_validator="validator",
            consistency_validator="consistency",
            blocking_validator="blocking",
            continuity_validator="continuity",
            s4_genre_type="investment",
        )
        session_environment = _SessionEnvironmentPayload(
            output_dir=Path("/tmp/session-drafts"),
            total_planned_ep=12,
            current_written=4,
        )

        result = orch._build_session_config(
            agent_bootstrap=agent_bootstrap,
            story_context="story",
            style_guide="style",
            reference_excerpt="reference",
            target_ep=8,
            session_environment=session_environment,
            v50_modules_available=True,
        )

        assert isinstance(result, _SessionConfig)
        assert result.chief_writer == "chief"
        assert result.manuscript_validator == "validator"
        assert result.consistency_validator == "consistency"
        assert result.blocking_validator == "blocking"
        assert result.continuity_validator == "continuity"
        assert result.s4_genre_type == "investment"
        assert result.story_context == "story"
        assert result.style_guide == "style"
        assert result.reference_excerpt == "reference"
        assert result.target_ep == 8
        assert result.output_dir == Path("/tmp/session-drafts")
        assert result.v50_modules_available is True
        assert result.total_planned_ep == 12

    def test_validate_session_prerequisites_accepts_project_with_bible_and_arcs(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.master_bible = {"MasterBible": {}}
        ctx.current_project.arcs = [{"arc_no": 1}]

        orch = Stage4Orchestrator(mock_app, context=ctx)

        assert orch._validate_session_prerequisites(error_emoji="ERR") is True
        ctx.ui.log.assert_not_called()

    def test_validate_session_prerequisites_logs_when_project_data_is_missing(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.master_bible = {}
        ctx.current_project.arcs = []

        orch = Stage4Orchestrator(mock_app, context=ctx)

        assert orch._validate_session_prerequisites(error_emoji="ERR") is False
        ctx.ui.log.assert_called_once_with(
            "ERR [System] Bible 또는 Arc 데이터가 없습니다. Stage 1-2를 먼저 실행하세요."
        )

    def test_prepare_session_style_payload_applies_character_voice_to_resolved_style(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionStyleGuidePayload

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._resolve_session_style_guide = MagicMock(
            return_value=_SessionStyleGuidePayload(style_guide="base style", reference_excerpt="ref excerpt")
        )
        orch._apply_character_voice_guide = MagicMock(return_value="voice-applied style")

        result = orch._prepare_session_style_payload(stage0_available=True)

        assert isinstance(result, _SessionStyleGuidePayload)
        assert result.style_guide == "voice-applied style"
        assert result.reference_excerpt == "ref excerpt"
        orch._resolve_session_style_guide.assert_called_once_with(stage0_available=True)
        orch._apply_character_voice_guide.assert_called_once_with(style_guide="base style")

    def test_load_session_runtime_dependencies_returns_expected_runtime_bundle(self, mock_app):
        from modules.core.constants import AIModels, Emojis
        from modules.core.spinners import STAGE0_AVAILABLE, V50_MODULES_AVAILABLE
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionRuntimeDependencies
        from modules.domain.agents.chief_writer import ChiefWriter
        from modules.domain.agents.manuscript_validator import ManuscriptValidator
        from modules.validation.blocking_validator import BlockingValidator
        from modules.validation.consistency_validator import ConsistencyValidator
        from modules.validation.continuity_validator import ContinuityValidator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        result = orch._load_session_runtime_dependencies()

        assert isinstance(result, _SessionRuntimeDependencies)
        assert result.ai_models is AIModels
        assert result.emojis is Emojis
        assert result.stage0_available is STAGE0_AVAILABLE
        assert result.v50_modules_available is V50_MODULES_AVAILABLE
        assert result.chief_writer_cls is ChiefWriter
        assert result.manuscript_validator_cls is ManuscriptValidator
        assert result.blocking_validator_cls is BlockingValidator
        assert result.consistency_validator_cls is ConsistencyValidator
        assert result.continuity_validator_cls is ContinuityValidator

    def test_build_session_story_context_includes_incarnation_guidance_and_core_traits(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.master_bible = {
            "MasterBible": {
                "protagonist_config": {
                    "name": "진우",
                    "world_origin": "현대 한국",
                    "incarnation_type": "회귀자",
                    "core_traits": "냉정, 집요",
                }
            }
        }

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._build_session_story_context(s4_genre_type="investment")

        assert "- 장르: investment" in result
        assert "- 주인공 이름: 진우" in result
        assert "- 세계 출신: 현대 한국" in result
        assert "- 환생 유형: 회귀자" in result
        assert "현재 역사를 의도적으로 변경" in result
        assert "- 핵심 특성: 냉정, 집요" in result

    def test_build_session_story_context_falls_back_to_genre_line_on_malformed_bible(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.master_bible = object()

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._build_session_story_context(s4_genre_type="wuxia")

        assert result == "- 장르: wuxia"

    def test_apply_character_voice_guide_appends_prompt_and_logs(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.character_voice = MagicMock()
        ctx.character_voice.profiles = [{"name": "진우"}, {"name": "연홍"}]
        ctx.character_voice.get_writer_injection.return_value = "voice guidance"

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._apply_character_voice_guide(style_guide="base style")

        assert result == "base style\n\nvoice guidance"
        ctx.character_voice.get_writer_injection.assert_called_once()
        ctx.ui.log.assert_called_once()

    def test_apply_character_voice_guide_noops_when_profiles_missing(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.character_voice = MagicMock()
        ctx.character_voice.profiles = []

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._apply_character_voice_guide(style_guide="base style")

        assert result == "base style"
        ctx.character_voice.get_writer_injection.assert_not_called()
        ctx.ui.log.assert_not_called()

    def test_resolve_session_style_guide_uses_saved_style_with_bible_pov_override_even_when_stage0_flag_is_false(
        self, mock_app
    ):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionStyleGuidePayload

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.get_int_input = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        loaded_sg = MagicMock()
        loaded_sg.pov = "3인칭"
        loaded_sg.tone = "냉소적"
        loaded_sg.reference_excerpt = "참고 발췌"
        loaded_sg.to_prompt.return_value = "saved style prompt"
        fake_stage0 = MagicMock()
        fake_stage0.StyleGuide.from_dict.return_value = loaded_sg

        with (
            patch.dict(sys.modules, {"modules.core.stage0": fake_stage0}),
            patch("modules.core.stage4_orchestrator.load_style_guide_anchor", return_value={"tone": "냉소적"}),
            patch("modules.core.stage4_orchestrator.resolve_project_bible_pov", return_value="1인칭"),
        ):
            result = orch._resolve_session_style_guide(stage0_available=False)

        assert isinstance(result, _SessionStyleGuidePayload)
        assert result.style_guide == "saved style prompt"
        assert result.reference_excerpt == "참고 발췌"
        assert loaded_sg.pov == "1인칭"
        ctx.get_int_input.assert_not_called()
        ctx.ui.log.assert_called_once()

    def test_resolve_session_style_guide_uses_stage0_output_file_before_prompt(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionStyleGuidePayload

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.get_int_input = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)

        with (
            patch("modules.core.stage4_orchestrator.load_style_guide_anchor", return_value=None),
            patch(
                "modules.core.stage4_orchestrator.load_style_guide_file",
                return_value={
                    "fallback_style_prompt": "file style prompt",
                    "tone": "진지",
                    "pov": "혼합",
                    "reference_excerpt": "파일 참고",
                },
            ),
            patch("modules.core.stage4_orchestrator.resolve_project_bible_pov", return_value="혼합"),
        ):
            result = orch._resolve_session_style_guide(stage0_available=False)

        assert isinstance(result, _SessionStyleGuidePayload)
        assert result.style_guide == "file style prompt"
        assert result.reference_excerpt == "파일 참고"
        ctx.get_int_input.assert_not_called()
        ctx.ui.log.assert_called_once()

    def test_resolve_session_style_guide_builds_minimal_guide_from_bible_pov(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionStyleGuidePayload

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.get_int_input = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        fake_stage0 = MagicMock()
        fake_stage0.StyleGuide.return_value.to_prompt.return_value = "minimal style prompt"

        with (
            patch.dict(sys.modules, {"modules.core.stage0": fake_stage0}),
            patch("modules.core.stage4_orchestrator.load_style_guide_anchor", return_value=None),
            patch("modules.core.stage4_orchestrator.resolve_project_bible_pov", return_value="1인칭"),
        ):
            result = orch._resolve_session_style_guide(stage0_available=True)

        assert isinstance(result, _SessionStyleGuidePayload)
        assert result.style_guide == "minimal style prompt"
        assert result.reference_excerpt == ""
        fake_stage0.StyleGuide.assert_called_once_with(pov="1인칭")
        ctx.get_int_input.assert_not_called()

    def test_resolve_session_style_guide_prompts_and_persists_fallback_when_no_project_style_truth_exists(
        self, mock_app
    ):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionStyleGuidePayload

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.get_int_input = MagicMock(return_value=2)
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)

        with (
            patch("modules.core.stage4_orchestrator.load_style_guide_anchor", return_value=None),
            patch("modules.core.stage4_orchestrator.load_style_guide_file", return_value=None),
            patch("modules.core.stage4_orchestrator.resolve_project_bible_pov", return_value=""),
        ):
            result = orch._resolve_session_style_guide(stage0_available=False)

        assert isinstance(result, _SessionStyleGuidePayload)
        assert "네이버" in result.style_guide
        assert result.reference_excerpt == ""
        ctx.get_int_input.assert_called_once()
        mock_app.current_project.save_v20_anchor.assert_called_once()
        saved_key, saved_payload = mock_app.current_project.save_v20_anchor.call_args.args
        assert saved_key == "style_guide"
        assert saved_payload["fallback_style_prompt"] == result.style_guide
        assert saved_payload["effective_primary_pov"] == "1인칭"

    def test_resolve_session_target_ep_skips_when_explicit_target_already_written(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionTargetDecision

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.get_int_input = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._resolve_session_target_ep(
            target_ep=3,
            limit_mode=False,
            current_written=4,
            total_planned_ep=6,
        )

        assert isinstance(result, _SessionTargetDecision)
        assert result.should_abort is True
        assert result.target_ep is None
        ctx.ui.log.assert_called_once()
        ctx.get_int_input.assert_not_called()

    def test_resolve_session_target_ep_prompts_in_limit_mode(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionTargetDecision

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.get_int_input = MagicMock(return_value=6)
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._resolve_session_target_ep(
            target_ep=None,
            limit_mode=True,
            current_written=3,
            total_planned_ep=6,
        )

        assert isinstance(result, _SessionTargetDecision)
        assert result.should_abort is False
        assert result.target_ep == 6
        prompt_call = ctx.get_int_input.call_args
        assert "현재 3화" in prompt_call.args[0]
        assert prompt_call.kwargs["default"] == 6
        assert prompt_call.kwargs["min_val"] == 4
        assert prompt_call.kwargs["max_val"] == 6

    def test_resolve_session_target_ep_aborts_when_limit_mode_has_no_blueprints(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _SessionTargetDecision

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.get_int_input = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._resolve_session_target_ep(
            target_ep=None,
            limit_mode=True,
            current_written=0,
            total_planned_ep=0,
        )

        assert isinstance(result, _SessionTargetDecision)
        assert result.should_abort is True
        assert result.target_ep is None
        ctx.ui.log.assert_called_once()
        ctx.get_int_input.assert_not_called()

    def test_limit_mode_prompt_uses_current_written_floor(self, mock_app, tmp_path):
        from modules.core.stage4_context import Stage4Context
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        mock_app.current_project.paths.drafts = tmp_path / "drafts"
        mock_app.current_project.db.get_latest_blueprint_number.return_value = 5
        mock_app.current_project.get_latest_episode_number.return_value = 4
        mock_app.current_project.arcs = [{"ep_end": 5}]

        ctx = Stage4Context.from_app(mock_app)
        ctx.get_int_input = MagicMock(side_effect=[4, 1])

        orch = Stage4Orchestrator(mock_app, context=ctx)

        with (
            patch("modules.domain.agents.chief_writer.ChiefWriter", return_value=MagicMock()),
            patch("modules.domain.agents.manuscript_validator.ManuscriptValidator", return_value=MagicMock()),
            patch("modules.validation.consistency_validator.ConsistencyValidator", return_value=MagicMock()),
            patch("modules.validation.blocking_validator.BlockingValidator", return_value=MagicMock()),
            patch("modules.validation.continuity_validator.ContinuityValidator", return_value=MagicMock()),
            patch("modules.core.stage4_orchestrator.load_style_guide_anchor", return_value=None),
        ):
            session = orch._prepare_stage4_session(limit_mode=True)

        assert session is not None
        first_call = ctx.get_int_input.call_args_list[0]
        assert "현재 3화" in first_call.args[0]
        assert first_call.kwargs["min_val"] == 4
        assert first_call.kwargs["max_val"] == 5
        assert session.target_ep == 4

    def test_limit_mode_returns_early_when_all_blueprints_already_written(self, mock_app, tmp_path):
        from modules.core.stage4_context import Stage4Context
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        mock_app.current_project.paths.drafts = tmp_path / "drafts"
        mock_app.current_project.db.get_latest_blueprint_number.return_value = 3
        mock_app.current_project.get_latest_episode_number.return_value = 4
        mock_app.current_project.arcs = [{"ep_end": 3}]

        ctx = Stage4Context.from_app(mock_app)
        ctx.get_int_input = MagicMock()

        orch = Stage4Orchestrator(mock_app, context=ctx)

        with (
            patch("modules.domain.agents.chief_writer.ChiefWriter", return_value=MagicMock()),
            patch("modules.domain.agents.manuscript_validator.ManuscriptValidator", return_value=MagicMock()),
            patch("modules.validation.consistency_validator.ConsistencyValidator", return_value=MagicMock()),
            patch("modules.validation.blocking_validator.BlockingValidator", return_value=MagicMock()),
            patch("modules.validation.continuity_validator.ContinuityValidator", return_value=MagicMock()),
            patch("modules.core.stage4_orchestrator.load_style_guide_anchor", return_value=None),
        ):
            session = orch._prepare_stage4_session(limit_mode=True)

        assert session is None
        ctx.get_int_input.assert_not_called()

    def test_stage4_exception_does_not_write_runtime_audit_summary_and_flushes(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.agents = mock_app.agents
        ctx.state_tracker = None
        ctx.memory = None
        ctx.context_advisor = None
        ctx.perf_timer = MagicMock()
        ctx.sys = mock_app.sys
        ctx.flush_audit_buffer = MagicMock()
        ctx.safe_commit = MagicMock()
        ctx.write_audit_summary = MagicMock()

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._prepare_stage4_session = MagicMock(return_value=object())
        orch._run_interview_loop = MagicMock(side_effect=RuntimeError("boom"))

        orch.stage_4_v2_chief_writer()

        ctx.write_audit_summary.assert_not_called()
        ctx.flush_audit_buffer.assert_called_once()
        ctx.safe_commit.assert_called_once()

    def test_stage4_exception_logs_commit_failure(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.agents = mock_app.agents
        ctx.state_tracker = None
        ctx.memory = None
        ctx.context_advisor = None
        ctx.perf_timer = MagicMock()
        ctx.sys = mock_app.sys
        ctx.flush_audit_buffer = MagicMock()
        ctx.safe_commit = MagicMock(return_value=False)
        ctx.write_audit_summary = MagicMock()

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._prepare_stage4_session = MagicMock(return_value=object())
        orch._run_interview_loop = MagicMock(side_effect=RuntimeError("boom"))

        orch.stage_4_v2_chief_writer()

        assert any("exception cleanup commit failed" in call.args[0] for call in ctx.ui.log.call_args_list if call.args)


class TestRoundContextAnnotations:
    def test_inventory_and_martial_arts_are_list_annotations(self):
        from modules.core.stage4_orchestrator import _RoundContext

        assert _RoundContext.__annotations__["current_inventory"] is list
        assert _RoundContext.__annotations__["current_martial_arts"] is list


# ══════════════════════════════════════════════════════════════
# Test: 패치 모드 분기 로직 (stage4_orchestrator.py 핵심)
# ══════════════════════════════════════════════════════════════


class TestPatchModeBranching:
    """Stage4의 interview loop 내 분기 로직을 직접 테스트.

    실제 Stage4Orchestrator의 전체 루프를 돌리지 않고,
    분기 조건 로직만 검증한다.
    """

    def _should_use_patch(self, previous_attempt, interview_round):
        """stage4_orchestrator.py의 분기 조건 재현"""
        _prev_score = previous_attempt.get("score", 0) if previous_attempt else 0
        _prev_manuscript = previous_attempt.get("best_manuscript", "") if previous_attempt else ""
        return _prev_score >= PatchModeThresholds.REWRITE and interview_round == 1 and bool(_prev_manuscript)

    def test_patch_mode_entry(self):
        """score=65, round=1, best_manuscript 있음 → 패치 모드 진입"""
        prev = {"score": 65, "best_manuscript": "원본 원고 텍스트"}
        assert self._should_use_patch(prev, interview_round=1) is True

    def test_patch_mode_boundary_50(self):
        """score=50 (경계값) → 패치 모드 진입"""
        prev = {"score": 50, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=1) is True

    def test_patch_mode_boundary_79(self):
        """score=79 → 패치 모드 진입 (80 미만은 Director REJECT 가능)"""
        prev = {"score": 79, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=1) is True

    def test_low_score_full_rewrite(self):
        """score=30 → 패치 모드 미진입 (full rewrite)"""
        prev = {"score": 30, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=1) is False

    def test_low_score_boundary_49(self):
        """score=49 (경계값 미만) → 패치 미진입"""
        prev = {"score": 49, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=1) is False

    def test_round0_always_generate(self):
        """round=0 → 패치 미진입 (generate_ensemble 사용)"""
        prev = {"score": 70, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=0) is False

    def test_round2_always_rewrite(self):
        """round=2 → score 무관 패치 미진입"""
        prev = {"score": 70, "best_manuscript": "원본"}
        assert self._should_use_patch(prev, interview_round=2) is False

    def test_no_manuscript_no_patch(self):
        """best_manuscript 없으면 패치 미진입"""
        prev = {"score": 70, "best_manuscript": ""}
        assert self._should_use_patch(prev, interview_round=1) is False

    def test_empty_previous_attempt(self):
        """previous_attempt={} → 패치 미진입"""
        assert self._should_use_patch({}, interview_round=1) is False

    def test_none_previous_attempt(self):
        """previous_attempt=None → 패치 미진입"""
        assert self._should_use_patch(None, interview_round=1) is False


# ══════════════════════════════════════════════════════════════
# Test: ChiefWriter.patch_with_feedback 호출 계약
# ══════════════════════════════════════════════════════════════


class TestPatchWithFeedbackContract:
    """patch_with_feedback()의 호출 규약과 bounded regenerate 반환값 검증."""

    def test_patch_returns_single_strategy_candidate(self, mock_chief_writer):
        """패치 모드는 selected-strategy bounded regenerate 1후보 계약으로 본다."""
        result = mock_chief_writer.patch_with_feedback(
            ep_num=10,
            blueprint={},
            prev_manuscript="",
            hud_report="",
            arc_doc="",
            master_bible={},
            style_guide="",
            original_manuscript="원본 원고",
            director_feedback="피드백",
            previous_attempt={"score": 65, "action_items": []},
            attempt_number=2,
        )
        assert len(result) == 1
        assert result[0]["strategy_name"] == "balanced"
        mock_chief_writer.patch_with_feedback.assert_called_once()

    def test_patch_fallback_on_empty(self, mock_chief_writer):
        """패치 빈 리스트 → 폴백 판정"""
        mock_chief_writer.patch_with_feedback.return_value = []
        result = mock_chief_writer.patch_with_feedback(
            ep_num=10,
            blueprint={},
            prev_manuscript="",
            hud_report="",
            arc_doc="",
            master_bible={},
            style_guide="",
            original_manuscript="원본",
            director_feedback="피드백",
            previous_attempt={"score": 65, "action_items": []},
            attempt_number=2,
        )
        assert result == []
        # 호출측에서 빈 리스트 감지 후 regenerate_with_feedback 폴백
        assert not result  # falsy → 폴백 트리거

    def test_patch_has_original_manuscript_param(self, mock_chief_writer):
        """patch_with_feedback에 original_manuscript 파라미터 전달 확인"""
        mock_chief_writer.patch_with_feedback(
            ep_num=5,
            blueprint={},
            prev_manuscript="",
            hud_report="",
            arc_doc="",
            master_bible={},
            style_guide="",
            original_manuscript="패치 대상 원고 전문",
            director_feedback="3번 문단 수정",
            previous_attempt={"score": 55},
            attempt_number=2,
        )
        call_kwargs = mock_chief_writer.patch_with_feedback.call_args
        assert call_kwargs.kwargs.get("original_manuscript") == "패치 대상 원고 전문"


# ══════════════════════════════════════════════════════════════
# Test: REJECT 경로에서 best_manuscript 저장
# ══════════════════════════════════════════════════════════════


class TestRejectPathBestManuscript:
    """REJECT 시 previous_attempt에 best_manuscript 저장 검증."""

    def test_previous_attempt_stores_manuscript(self):
        """director_result에서 selected_candidate.manuscript 추출"""
        director_result = {
            "verdict": "REJECT",
            "score": 65,
            "selected": "A",
            "feedback": {"issues": ["3번 문단 연속성 오류"]},
            "action_items": ["3번 문단 수정"],
            "selected_candidate": {"manuscript": "선택된 원고 전문", "title": "테스트"},
        }
        # REJECT 경로 로직 재현
        feedback = director_result.get("feedback", {})
        action_items = director_result.get("action_items", [])
        score = director_result.get("score", 0)
        selected = director_result.get("selected", "A")
        director_feedback = "\n".join(action_items) if action_items else str(feedback.get("issues", []))

        previous_attempt = {
            "strategy": selected,
            "rejection_reason": director_feedback,
            "action_items": action_items,
            "score": score,
            "best_manuscript": director_result.get("selected_candidate", {}).get("manuscript", ""),
        }

        assert previous_attempt["best_manuscript"] == "선택된 원고 전문"
        assert previous_attempt["score"] == 65

    def test_missing_selected_candidate(self):
        """selected_candidate 없을 때 빈 문자열"""
        director_result = {"verdict": "REJECT", "score": 30, "selected": "B"}
        best = director_result.get("selected_candidate", {}).get("manuscript", "")
        assert best == ""

    def test_empty_manuscript_in_candidate(self):
        """selected_candidate.manuscript 빈 문자열"""
        director_result = {
            "verdict": "REJECT",
            "score": 55,
            "selected_candidate": {"manuscript": "", "title": ""},
        }
        best = director_result.get("selected_candidate", {}).get("manuscript", "")
        assert best == ""


# ══════════════════════════════════════════════════════════════
# Test: _handle_round_outcome 에러 경로 반환 구조 (4-R2-b-hotfix)
# ══════════════════════════════════════════════════════════════


class TestHandleRoundOutcomeErrorPaths:
    """_handle_round_outcome의 에러 경로에서 올바른 _RoundOutcome을 반환하는지 검증.

    회귀 대상: 9ade2db 핫픽스 (return {{...}} → return {...})
    + 4-R2-d: dict → _RoundOutcome dataclass 전환
    """

    @pytest.fixture
    def orch_with_ctx(self, mock_app):
        """Stage4Orchestrator + ctx mock 조립"""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        orch = Stage4Orchestrator(mock_app)
        # ctx mock 설정
        orch._ctx = MagicMock()
        orch._ctx.ui = MagicMock()
        orch._ctx.ui.log = MagicMock()
        orch._ctx.agents = {
            "director": MagicMock(),
            "writer": MagicMock(),
        }
        orch._ctx.current_project = MagicMock()
        orch._ctx.current_project.master_bible = {"MasterBible": {}}
        orch._ctx.get_protagonist_name = MagicMock(return_value="이청풍")
        orch._ctx.get_int_input = MagicMock(return_value=1)  # abort (not 4)
        orch._ctx.get_module = MagicMock(return_value=None)
        return orch

    @pytest.fixture
    def minimal_round_ctx(self):
        """_RoundContext 최소 구성"""
        from modules.core.stage4_orchestrator import _RoundContext

        return _RoundContext(
            chief_writer=MagicMock(),
            manuscript_validator=MagicMock(),
            consistency_validator=MagicMock(),
            blocking_validator=MagicMock(),
            continuity_validator=MagicMock(),
            next_ep=1,
            blueprint={"integrated_scenario": "테스트 시나리오"},
            arc_data={"arc_no": 1},
            arc_pos=1,
            total_ep_in_arc=10,
            arc_tactical="전술 문서",
            prev_text="이전 원고",
            prev_ending="이전 결말",
            prev_manuscripts_text="",
            episode_digest="",
            hud_report="HUD",
            current_inventory="",
            current_martial_arts="",
            dead_npcs=[],
            item_acquisition_timeline="",
            chain_link_section="",
            world_state_summary="",
            purism_prompt="",
            genre_name="무협",
            npc_equipment_summary="",
            effective_anti_trope="",
            intro_dna="CYNICAL",
            story_context="",
            style_guide="표준",
            reference_anchor_prompt="",
            mandatory_context="",
            justification_prompt="",
            reflexion_prompt="",
            preflight_advisory="",
        )

    def test_all_rounds_reject_returns_should_return(self, orch_with_ctx, minimal_round_ctx, monkeypatch):
        """5라운드 모두 REJECT → _RoundOutcome(should_return=True) 반환"""
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx

        # 5라운드 모두 REJECT (B-1-3: interview_round.run 위임)
        orch._interview_round = MagicMock()
        orch._interview_round.run = MagicMock(
            return_value=_InterviewRoundResult(
                verdict="REJECT",
                director_feedback="피드백",
                previous_attempt={"score": 30},
            )
        )

        # StageSpinner is locally imported inside _handle_round_outcome
        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())

        result = orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        # Core assertion: returns _RoundOutcome, not dict or set
        from modules.core.stage4_orchestrator import _RoundOutcome

        assert isinstance(result, _RoundOutcome), f"Expected _RoundOutcome, got {type(result).__name__}"
        assert result.should_return is True
        assert result.final_manuscript is None
        assert result.final_title is None
        assert result.final_state_updates == {}
        # 라운드 전량 소진 확인 (retry.director_max_attempts 설정값)
        assert orch._interview_round.run.call_count >= 5

    def test_round_count_respects_retry_director_max_attempts(self, orch_with_ctx, minimal_round_ctx, monkeypatch):
        """[L-3] interview 라운드 수는 retry.director_max_attempts 설정값을 따른다."""
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
        orch._interview_round = MagicMock()
        orch._interview_round.run = MagicMock(
            return_value=_InterviewRoundResult(
                verdict="REJECT",
                director_feedback="피드백",
                previous_attempt={"score": 30},
            )
        )

        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())

        orch._get_stage4_max_rounds = MagicMock(return_value=2)
        orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        assert orch._interview_round.run.call_count == 2

    def test_round_count_prefers_stage4_policy_max_rounds_override(self, orch_with_ctx, minimal_round_ctx, monkeypatch):
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
        orch._interview_round = MagicMock()
        orch._interview_round.run = MagicMock(
            return_value=_InterviewRoundResult(
                verdict="REJECT",
                director_feedback="policy retry",
                previous_attempt={"score": 30},
            )
        )

        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())
        orch._get_stage4_max_rounds = MagicMock(return_value=1)

        orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        assert orch._interview_round.run.call_count == 1

    def test_handle_round_outcome_hydrates_persisted_previous_attempt_before_first_round(
        self,
        orch_with_ctx,
        minimal_round_ctx,
        monkeypatch,
    ):
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
        orch._interview_round = MagicMock()
        orch._interview_round.hydrate_persisted_stage4_previous_attempt = MagicMock(
            return_value={
                "score": 61,
                "fix_scope": "partial",
                "rejection_reason": "persisted reject",
                "feedback_provenance": {"merged_feedback": "persisted reject\nruntime advisory"},
            }
        )
        orch._interview_round.run = MagicMock(
            return_value=_InterviewRoundResult(
                verdict="REJECT",
                director_feedback="retry feedback",
                previous_attempt={"score": 30},
            )
        )

        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())
        orch._get_stage4_max_rounds = MagicMock(return_value=1)

        orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        orch._interview_round.hydrate_persisted_stage4_previous_attempt.assert_called_once_with(
            next_ep=1,
            arc_num=1,
            previous_attempt={},
        )
        run_kwargs = orch._interview_round.run.call_args.kwargs
        assert run_kwargs["previous_attempt"]["fix_scope"] == "partial"
        assert run_kwargs["director_feedback"] == "persisted reject\nruntime advisory"

    def test_handle_round_outcome_injects_stage4_to_3_feedback_into_inplace_patch(
        self,
        orch_with_ctx,
        minimal_round_ctx,
        monkeypatch,
    ):
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
        orch._ctx.generate_reverse_feedback_stage4_to_3 = MagicMock(return_value="[S4->S3] blueprint hint")
        bp_agent = MagicMock()
        bp_agent._inplace_patch_blueprint.return_value = {"patched": True}
        orch._ctx.agents["three_phase_bp"] = bp_agent
        orch._interview_round = MagicMock()
        orch._interview_round.run = MagicMock(
            side_effect=[
                _InterviewRoundResult(
                    verdict="REJECT",
                    director_feedback="후반 밀도 부족",
                    previous_attempt={
                        "score": 40,
                        "open_review": "후반 이벤트가 부족합니다.",
                        "action_items": ["scene 6 보강"],
                        "consistency_checklist": {
                            "items": [{"name": "continuity", "passed": False, "message": "frontier"}]
                        },
                    },
                    error_category="LOGIC_ERROR",
                ),
                _InterviewRoundResult(
                    verdict="PASS",
                    director_feedback="",
                    previous_attempt={},
                    final_manuscript="통과 원고",
                    final_title="제1화",
                    final_state_updates={},
                ),
            ]
        )
        minimal_round_ctx = dataclasses.replace(minimal_round_ctx, blueprint={"_stage3_meta": {"quality_risk": True}})

        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())

        result = orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        assert result.should_return is False
        patch_feedback = bp_agent._inplace_patch_blueprint.call_args.kwargs["director_feedback"]
        assert "[S4->S3] blueprint hint" in patch_feedback
        assert "[Stage4 원문 피드백]" in patch_feedback

    def test_regenerate_blueprint_passes_external_feedback(self, orch_with_ctx, minimal_round_ctx):
        orch = orch_with_ctx
        bp_agent = MagicMock()
        bp_agent.generate.return_value = ({"scene_breakdown": {}}, {})
        orch._ctx.agents["three_phase_bp"] = bp_agent
        orch._ctx.agents["state_extractor"] = MagicMock()
        orch._ctx.agents["state_extractor"].extract_cumulative_state.return_value = {"entity_registry": {}}
        orch._ctx.current_project.get_blueprint = MagicMock(return_value=None)
        orch._ctx.current_project.save_episode_blueprint = MagicMock()
        orch._ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {"name": "이청풍"}}}
        orch._ctx.current_project.db = MagicMock()

        result = orch._regenerate_blueprint(
            2,
            {"arc_no": 1},
            minimal_round_ctx,
            external_feedback="translated reverse feedback",
        )

        assert result["scene_breakdown"] == {}
        assert result["_stage3_meta"]["lineage_schema_version"] == "stage3-blueprint-lineage-v1"
        assert result["_stage3_meta"]["source_prev_manuscript_ep"] == 1
        assert bp_agent.generate.call_args.kwargs["external_feedback"] == "translated reverse feedback"
        assert bp_agent.generate.call_args.kwargs["prev_manuscripts_text"] == minimal_round_ctx.prev_manuscripts_text

    def test_prepare_current_episode_inputs_blocks_stale_frontier_against_accepted_manuscript(self, orch_with_ctx):
        orch = orch_with_ctx
        orch._ctx.current_project.arcs = [
            {
                "arc_no": 2,
                "ep_start": 5,
                "ep_count": 3,
                "tactical_doc": "제6화: 한미증권 VIP룸에서 WTI 6월물 15억 원 매수 지시를 완료한다.",
            }
        ]
        blueprints = {
            6: {
                "ep_num": 6,
                "scene_breakdown": {
                    "scene_1": {"summary": "가승인 서류를 들고 15억 원 규모의 WTI 6월물 매수 지시를 반복한다."}
                },
            },
            7: {"ep_num": 7, "summary": "후속 시장 압박"},
        }
        orch._ctx.current_project.get_blueprint.side_effect = lambda ep: blueprints.get(ep)
        saved_blueprints = {}
        orch._ctx.current_project.save_episode_blueprint.side_effect = lambda ep, bp: saved_blueprints.setdefault(
            ep, bp
        )
        orch._ctx.current_project.db.get_manuscript.return_value = {
            "content": "박성호 PB가 WTI 원유 선물 3월물 매수 포지션에 전량 진입했다. 딸깍."
        }
        orch._preflight_validate_blueprint = MagicMock()
        orch._log_escalation_event = MagicMock()

        result = orch._prepare_current_episode_inputs(next_ep=6)

        assert result is None
        assert orch._stage4_completion_blocked is True
        orch._preflight_validate_blueprint.assert_not_called()
        orch._log_escalation_event.assert_called_once()
        assert orch._log_escalation_event.call_args.args[:2] == (6, "STAGE4_FRONTIER_STALE_PREFLIGHT")
        assert set(saved_blueprints) == {6, 7}
        assert saved_blueprints[6]["_frontier_status"]["status"] == "requires_director_frontier_adjudication"
        assert saved_blueprints[7]["_frontier_status"]["affected_ep"] == 7

    @pytest.mark.parametrize(
        "frontier_status",
        [
            "requires_actual_manuscript_revalidation",
            "requires_director_frontier_adjudication",
            "contaminated_requires_regeneration",
        ],
    )
    def test_prepare_current_episode_inputs_blocks_persisted_frontier_status_before_generation(
        self, orch_with_ctx, frontier_status
    ):
        orch = orch_with_ctx
        orch._ctx.current_project.arcs = [{"arc_no": 1, "ep_start": 1, "ep_end": 3, "tactical_doc": ""}]
        orch._ctx.current_project.get_blueprint.return_value = {
            "ep_num": 2,
            "_frontier_status": {"status": frontier_status},
        }
        orch._preflight_validate_blueprint = MagicMock()
        orch._log_escalation_event = MagicMock()

        result = orch._prepare_current_episode_inputs(next_ep=2)

        assert result is None
        assert orch._stage4_completion_blocked is True
        orch._preflight_validate_blueprint.assert_not_called()
        assert orch._log_escalation_event.call_args.args[:2] == (2, "STAGE4_FRONTIER_STATUS_BLOCK")

    def test_prepare_current_episode_inputs_allows_revalidated_lineage_hash_match(self, orch_with_ctx):
        orch = orch_with_ctx
        prev_text = "새로 확정된 계약 체결 완료. 모두가 서명본을 확인했다."
        prev_hash = hashlib.sha256(prev_text.encode("utf-8")).hexdigest()
        orch._ctx.current_project.arcs = [{"arc_no": 1, "ep_start": 1, "ep_end": 3, "tactical_doc": ""}]
        orch._ctx.current_project.get_blueprint.return_value = {
            "ep_num": 2,
            "_frontier_status": {
                "status": "requires_actual_manuscript_revalidation",
                "evidence": {"accepted_ep": 1, "accepted_manuscript_hash": prev_hash},
            },
            "_stage3_meta": {"source_prev_manuscript_ep": 1, "source_prev_manuscript_hash": prev_hash},
        }
        orch._ctx.current_project.db.get_manuscript.return_value = {"content": prev_text}
        orch._preflight_validate_blueprint = MagicMock(return_value={"ok": True})
        orch._log_escalation_event = MagicMock()

        result = orch._prepare_current_episode_inputs(next_ep=2)

        assert result is not None
        assert orch._stage4_completion_blocked is False
        orch._preflight_validate_blueprint.assert_called_once()
        orch._log_escalation_event.assert_not_called()

    def test_handle_round_outcome_keeps_pass_when_cove_verify_raises(
        self, orch_with_ctx, minimal_round_ctx, monkeypatch, tmp_path
    ):
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
        orch._ctx.current_project.name = "cove_project"
        orch._ctx.current_project.paths.root = tmp_path / "cove_project"
        orch._ctx.audit_event = MagicMock()
        cove = MagicMock()
        cove.quick_verify.side_effect = [
            (False, "관계 변화 의심"),
            (True, ""),
        ]
        cove.verify.side_effect = ChainOfVerificationParseError("invalid cove json")
        orch._ctx.get_module = MagicMock(side_effect=lambda name: cove if name == "chain_of_verification" else None)
        orch._interview_round = MagicMock()
        orch._interview_round.run = MagicMock(
            side_effect=[
                _InterviewRoundResult(
                    verdict="PASS",
                    director_feedback="",
                    previous_attempt={},
                    final_manuscript="초안 원고",
                    final_title="제1화",
                    final_state_updates={"hp": 10},
                ),
                _InterviewRoundResult(
                    verdict="PASS",
                    director_feedback="",
                    previous_attempt={},
                    final_manuscript="수정 원고",
                    final_title="제1화",
                    final_state_updates={"hp": 10},
                ),
            ]
        )

        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())

        result = orch._handle_round_outcome(round_ctx=minimal_round_ctx)
        log_path = tmp_path / "cove_project" / "logs" / "episode_production.jsonl"
        rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        advisory_rows = [row for row in rows if row.get("event") == "STAGE4_COVE_RUNTIME_ADVISORY"]
        pathology_rows = [row for row in rows if row.get("event") == "STAGE4_RETRY_PATHOLOGY"]
        assert result.should_return is False
        assert result.final_manuscript == "초안 원고"
        assert result.final_title == "제1화"
        assert result.final_state_updates == {"hp": 10}
        assert orch._interview_round.run.call_count == 1
        assert cove.verify.call_count == 1
        assert advisory_rows
        assert advisory_rows[-1]["source"] == "llm_verify"
        assert advisory_rows[-1]["error_type"] == "ChainOfVerificationParseError"
        assert advisory_rows[-1]["director_pass_preserved"] is True
        assert advisory_rows[-1]["quick_warning"] == "관계 변화 의심"
        assert pathology_rows == []
        orch._ctx.audit_event.assert_any_call(
            "stage4_cove_runtime_advisory",
            "stage4 CoVe runtime advisory observed",
            ANY,
        )


# ══════════════════════════════════════════════════════════════
# Test: Stage4Orchestrator 초기화 + import
# ══════════════════════════════════════════════════════════════


class TestHandleRoundOutcomeRetryPathology:
    @pytest.fixture
    def orch_with_ctx(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        orch = Stage4Orchestrator(mock_app)
        orch._ctx = MagicMock()
        orch._ctx.ui = MagicMock()
        orch._ctx.ui.log = MagicMock()
        orch._ctx.agents = {
            "director": MagicMock(),
            "writer": MagicMock(),
        }
        orch._ctx.current_project = MagicMock()
        orch._ctx.current_project.master_bible = {"MasterBible": {}}
        orch._ctx.get_protagonist_name = MagicMock(return_value="hero")
        orch._ctx.get_int_input = MagicMock(return_value=1)
        orch._ctx.get_module = MagicMock(return_value=None)
        return orch

    @pytest.fixture
    def minimal_round_ctx(self):
        from modules.core.stage4_orchestrator import _RoundContext

        return _RoundContext(
            chief_writer=MagicMock(),
            manuscript_validator=MagicMock(),
            consistency_validator=MagicMock(),
            blocking_validator=MagicMock(),
            continuity_validator=MagicMock(),
            next_ep=1,
            blueprint={"integrated_scenario": "test scenario"},
            arc_data={"arc_no": 1},
            arc_pos=1,
            total_ep_in_arc=10,
            arc_tactical="tactical doc",
            prev_text="previous manuscript",
            prev_ending="previous ending",
            prev_manuscripts_text="",
            episode_digest="",
            hud_report="HUD",
            current_inventory="",
            current_martial_arts="",
            dead_npcs=[],
            item_acquisition_timeline="",
            chain_link_section="",
            world_state_summary="",
            purism_prompt="",
            genre_name="genre",
            npc_equipment_summary="",
            effective_anti_trope="",
            intro_dna="CYNICAL",
            story_context="",
            style_guide="style",
            reference_anchor_prompt="",
            mandatory_context="",
            justification_prompt="",
            reflexion_prompt="",
            preflight_advisory="",
        )

    def test_handle_round_outcome_logs_cove_runtime_advisory(
        self, orch_with_ctx, minimal_round_ctx, monkeypatch, tmp_path
    ):
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
        orch._ctx.current_project.name = "cove_project"
        orch._ctx.current_project.paths.root = tmp_path / "cove_project"
        orch._ctx.audit_event = MagicMock()
        cove = MagicMock()
        cove.quick_verify.side_effect = [
            (False, "hint"),
            (True, ""),
        ]
        cove.verify.side_effect = ChainOfVerificationParseError("invalid cove json")
        orch._ctx.get_module = MagicMock(side_effect=lambda name: cove if name == "chain_of_verification" else None)
        orch._interview_round = MagicMock()
        orch._interview_round.run = MagicMock(
            return_value=_InterviewRoundResult(
                verdict="PASS",
                director_feedback="",
                previous_attempt={},
                final_manuscript="draft manuscript",
                final_title="draft title",
                final_state_updates={"hp": 10},
            )
        )

        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())

        result = orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        assert result.final_manuscript == "draft manuscript"
        log_path = tmp_path / "cove_project" / "logs" / "episode_production.jsonl"
        rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        advisory_rows = [row for row in rows if row.get("event") == "STAGE4_COVE_RUNTIME_ADVISORY"]
        assert advisory_rows
        assert advisory_rows[-1]["source"] == "llm_verify"
        assert advisory_rows[-1]["director_pass_preserved"] is True
        orch._ctx.audit_event.assert_any_call(
            "stage4_cove_runtime_advisory",
            "stage4 CoVe runtime advisory observed",
            ANY,
        )

    def test_handle_round_outcome_keeps_pass_when_cove_quick_verify_raises(
        self, orch_with_ctx, minimal_round_ctx, monkeypatch, tmp_path
    ):
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
        orch._ctx.current_project.name = "quick_project"
        orch._ctx.current_project.paths.root = tmp_path / "quick_project"
        orch._ctx.audit_event = MagicMock()
        cove = MagicMock()
        cove.quick_verify.side_effect = RuntimeError("quick boom")
        orch._ctx.get_module = MagicMock(side_effect=lambda name: cove if name == "chain_of_verification" else None)
        orch._interview_round = MagicMock()
        orch._interview_round.run = MagicMock(
            return_value=_InterviewRoundResult(
                verdict="PASS",
                director_feedback="",
                previous_attempt={},
                final_manuscript="draft manuscript",
                final_title="draft title",
                final_state_updates={"hp": 10},
            )
        )

        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())

        result = orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        assert result.final_manuscript == "draft manuscript"
        assert orch._interview_round.run.call_count == 1
        log_path = tmp_path / "quick_project" / "logs" / "episode_production.jsonl"
        rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        advisory_rows = [row for row in rows if row.get("event") == "STAGE4_COVE_RUNTIME_ADVISORY"]
        assert advisory_rows
        assert advisory_rows[-1]["source"] == "quick_verify"
        assert advisory_rows[-1]["director_pass_preserved"] is True

    def test_handle_round_outcome_persists_full_cove_runtime_advisory_detail(
        self, orch_with_ctx, minimal_round_ctx, monkeypatch, tmp_path
    ):
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
        orch._ctx.current_project.name = "cove_detail_project"
        orch._ctx.current_project.paths.root = tmp_path / "cove_detail_project"
        orch._ctx.audit_event = MagicMock()
        cove = MagicMock()
        long_hint = "semantic warning " * 24
        cove.quick_verify.side_effect = [
            (False, long_hint),
            (True, ""),
        ]
        cove.verify.side_effect = ChainOfVerificationParseError("invalid cove json")
        orch._ctx.get_module = MagicMock(side_effect=lambda name: cove if name == "chain_of_verification" else None)
        orch._interview_round = MagicMock()
        orch._interview_round.run = MagicMock(
            return_value=_InterviewRoundResult(
                verdict="PASS",
                director_feedback="",
                previous_attempt={},
                final_manuscript="draft manuscript",
                final_title="draft title",
                final_state_updates={"hp": 10},
            )
        )

        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())

        orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        log_path = tmp_path / "cove_detail_project" / "logs" / "episode_production.jsonl"
        rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        advisory_rows = [row for row in rows if row.get("event") == "STAGE4_COVE_RUNTIME_ADVISORY"]
        assert advisory_rows[-1]["quick_warning"] == long_hint.strip()

    def test_handle_round_outcome_still_retries_when_cove_requests_regeneration(
        self, orch_with_ctx, minimal_round_ctx, monkeypatch, tmp_path
    ):
        from types import SimpleNamespace

        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
        orch._ctx.current_project.name = "semantic_project"
        orch._ctx.current_project.paths.root = tmp_path / "semantic_project"
        orch._ctx.audit_event = MagicMock()
        cove = MagicMock()
        cove.quick_verify.side_effect = [
            (False, "semantic warning"),
            (True, ""),
        ]
        cove.verify.return_value = SimpleNamespace(
            should_regenerate=True,
            correction_hints="rewrite needed",
            summary="rewrite needed",
            issues=[],
        )
        orch._ctx.get_module = MagicMock(side_effect=lambda name: cove if name == "chain_of_verification" else None)
        orch._interview_round = MagicMock()
        orch._interview_round.run = MagicMock(
            side_effect=[
                _InterviewRoundResult(
                    verdict="PASS",
                    director_feedback="",
                    previous_attempt={},
                    final_manuscript="draft manuscript",
                    final_title="draft title",
                    final_state_updates={"hp": 10},
                ),
                _InterviewRoundResult(
                    verdict="PASS",
                    director_feedback="",
                    previous_attempt={},
                    final_manuscript="repaired manuscript",
                    final_title="repaired title",
                    final_state_updates={"hp": 10},
                ),
            ]
        )

        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())

        result = orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        assert result.final_manuscript == "repaired manuscript"
        assert orch._interview_round.run.call_count == 2
        second_round_kwargs = orch._interview_round.run.call_args_list[1].kwargs
        assert second_round_kwargs["director_feedback"].startswith("[CoVe 사후검증 실패]")
        assert second_round_kwargs["previous_attempt"]["cove_fail_closed"] is True
        assert second_round_kwargs["previous_attempt"]["cove_runtime_failure"] is False
        log_path = tmp_path / "semantic_project" / "logs" / "episode_production.jsonl"
        rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        advisory_rows = [row for row in rows if row.get("event") == "STAGE4_COVE_RUNTIME_ADVISORY"]
        pathology_rows = [row for row in rows if row.get("event") == "STAGE4_RETRY_PATHOLOGY"]
        assert advisory_rows == []
        assert pathology_rows
        assert pathology_rows[-1]["pathology_source"] == "cove_fail_closed"
        assert pathology_rows[-1]["cove_runtime_failure"] is False

    def test_handle_pass_round_result_requests_retry_on_cove_regeneration(self, orch_with_ctx, minimal_round_ctx):
        from types import SimpleNamespace

        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        cove = MagicMock()
        cove.quick_verify.return_value = (False, "semantic warning")
        cove.verify.return_value = SimpleNamespace(
            should_regenerate=True,
            correction_hints="rewrite needed",
            summary="rewrite needed",
            issues=[],
        )
        orch._ctx.get_module = MagicMock(side_effect=lambda name: cove if name == "chain_of_verification" else None)
        runtime.emit_retry_pathology_signal = MagicMock()
        round_result = SimpleNamespace(
            verdict="PASS",
            final_manuscript="draft manuscript",
            final_title="draft title",
            final_state_updates={"hp": 10},
        )
        pathology_counts = {}
        pathology_repeat_emitted = set()
        minimal_round_ctx = dataclasses.replace(
            minimal_round_ctx,
            prev_manuscripts_text="x" * 2001,
            blueprint={"integrated_scenario": "patched blueprint"},
        )

        result = runtime.handle_pass_round_result(
            round_ctx=minimal_round_ctx,
            round_result=round_result,
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            pathology_counts=pathology_counts,
            pathology_repeat_emitted=pathology_repeat_emitted,
        )

        assert result.accepted is False
        assert result.should_continue is True
        assert result.final_manuscript is None
        assert result.final_title is None
        assert result.final_state_updates == {"hp": 10}
        assert result.director_feedback.startswith("[CoVe")
        assert result.previous_attempt["best_manuscript"] == "draft manuscript"
        assert result.previous_attempt["cove_fail_closed"] is True
        assert result.previous_attempt["cove_runtime_failure"] is False
        assert result.previous_attempt["provisional_pass_downgrade"] is True
        cove.quick_verify.assert_called_once()
        _, cove_context = cove.quick_verify.call_args.args
        assert cove_context["prev_manuscript"] == ("x" * 1500)
        assert cove_context["blueprint"] == {"integrated_scenario": "patched blueprint"}
        runtime.emit_retry_pathology_signal.assert_called_once_with(
            ep_num=1,
            round_num=0,
            previous_attempt=result.previous_attempt,
            pathology_counts=pathology_counts,
            pathology_repeat_emitted=pathology_repeat_emitted,
        )

    def test_build_cove_pass_context_clamps_previous_manuscript(self, orch_with_ctx):
        runtime = orch_with_ctx.outcome_runtime

        cove_context = runtime._build_cove_pass_context(
            prev_manuscripts_text="x" * 2001,
            blueprint={"integrated_scenario": "patched blueprint"},
        )

        assert cove_context["prev_manuscript"] == ("x" * 1500)
        assert cove_context["blueprint"] == {"integrated_scenario": "patched blueprint"}

    def test_run_cove_llm_verification_logs_non_blocking_issue_summary(self, orch_with_ctx):
        from types import SimpleNamespace

        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        cove = MagicMock()
        cove.verify.return_value = SimpleNamespace(
            should_regenerate=False,
            issues=[
                SimpleNamespace(description="first issue " * 5),
                SimpleNamespace(description="second issue " * 5),
            ],
        )

        result = runtime.run_cove_llm_verification(
            request=runtime._build_cove_llm_request(
                cove=cove,
                final_manuscript="draft manuscript",
                final_state_updates={"hp": 10},
                cove_context={"quick_verify_warnings": "hint"},
                quick_msg="hint",
                next_ep=1,
                interview_round=0,
                max_rounds=5,
                pathology_counts={},
                pathology_repeat_emitted=set(),
            ),
        )

        assert result is None
        cove.verify.assert_called_once_with(
            "draft manuscript", {"quick_verify_warnings": "hint"}, content_type="manuscript"
        )
        assert any(
            "LLM 검증 경고 (비차단)" in call.args[0]
            and "first issue" in call.args[0]
            and "second issue" in call.args[0]
            for call in orch._ctx.ui.log.call_args_list
            if call.args
        )

    def test_run_cove_llm_verification_logs_all_issue_descriptions_without_caps(self, orch_with_ctx):
        from types import SimpleNamespace

        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        cove = MagicMock()
        third_issue = "third issue " * 14
        cove.verify.return_value = SimpleNamespace(
            should_regenerate=False,
            issues=[
                SimpleNamespace(description="first issue " * 5),
                SimpleNamespace(description="second issue " * 5),
                SimpleNamespace(description=third_issue),
            ],
        )

        runtime.run_cove_llm_verification(
            request=runtime._build_cove_llm_request(
                cove=cove,
                final_manuscript="draft manuscript",
                final_state_updates={"hp": 10},
                cove_context={"quick_verify_warnings": "hint"},
                quick_msg="hint",
                next_ep=1,
                interview_round=0,
                max_rounds=5,
                pathology_counts={},
                pathology_repeat_emitted=set(),
            ),
        )

        assert any(
            "third issue" in call.args[0] and third_issue.strip() in call.args[0]
            for call in orch._ctx.ui.log.call_args_list
            if call.args
        )

    def test_handle_cove_llm_verification_result_requests_retry_when_regeneration_needed(self, orch_with_ctx):
        from types import SimpleNamespace

        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        runtime._build_cove_retry_disposition = MagicMock(return_value=SimpleNamespace(should_continue=True))

        request = runtime._build_cove_llm_request(
            cove=MagicMock(),
            final_manuscript="draft manuscript",
            final_state_updates={"hp": 10},
            cove_context={"quick_verify_warnings": "hint"},
            quick_msg="hint",
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            pathology_counts={"cove_fail_closed": 1},
            pathology_repeat_emitted={"bucket"},
        )
        cove_result = SimpleNamespace(should_regenerate=True, issues=[])

        result = runtime._handle_cove_llm_verification_result(
            request=request,
            cove_result=cove_result,
        )

        assert result.should_continue is True
        runtime._build_cove_retry_disposition.assert_called_once_with(
            final_manuscript="draft manuscript",
            final_state_updates={"hp": 10},
            cove_result=cove_result,
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            pathology_counts={"cove_fail_closed": 1},
            pathology_repeat_emitted={"bucket"},
        )

    def test_build_cove_retry_kwargs_returns_payload_only_when_regeneration_needed(self, orch_with_ctx):
        from types import SimpleNamespace

        runtime = orch_with_ctx.outcome_runtime
        request = runtime._build_cove_llm_request(
            cove=MagicMock(),
            final_manuscript="draft manuscript",
            final_state_updates={"hp": 10},
            cove_context={"quick_verify_warnings": "hint"},
            quick_msg="hint",
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            pathology_counts={"cove_fail_closed": 1},
            pathology_repeat_emitted={"bucket"},
        )

        retry_kwargs = runtime._build_cove_retry_kwargs(
            request=request,
            cove_result=SimpleNamespace(should_regenerate=True, issues=[]),
        )
        no_retry_kwargs = runtime._build_cove_retry_kwargs(
            request=request,
            cove_result=SimpleNamespace(should_regenerate=False, issues=[]),
        )

        assert retry_kwargs == {
            "final_manuscript": "draft manuscript",
            "final_state_updates": {"hp": 10},
            "cove_result": ANY,
            "next_ep": 1,
            "interview_round": 0,
            "max_rounds": 5,
            "pathology_counts": {"cove_fail_closed": 1},
            "pathology_repeat_emitted": {"bucket"},
        }
        assert no_retry_kwargs is None

    def test_build_cove_retry_request_fields_preserves_manuscript_and_state_updates(self, orch_with_ctx):
        runtime = orch_with_ctx.outcome_runtime

        request = runtime._build_cove_llm_request(
            cove=MagicMock(),
            final_manuscript="draft manuscript",
            final_state_updates={"hp": 10},
            cove_context={"quick_verify_warnings": "hint"},
            quick_msg="hint",
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            pathology_counts={"cove_fail_closed": 1},
            pathology_repeat_emitted={"bucket"},
        )

        fields = runtime._build_cove_retry_request_fields(request=request)

        assert fields == {
            "final_manuscript": "draft manuscript",
            "final_state_updates": {"hp": 10},
        }

    def test_build_cove_retry_state_fields_preserves_episode_and_pathology_state(self, orch_with_ctx):
        runtime = orch_with_ctx.outcome_runtime

        request = runtime._build_cove_llm_request(
            cove=MagicMock(),
            final_manuscript="draft manuscript",
            final_state_updates={"hp": 10},
            cove_context={"quick_verify_warnings": "hint"},
            quick_msg="hint",
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            pathology_counts={"cove_fail_closed": 1},
            pathology_repeat_emitted={"bucket"},
        )

        fields = runtime._build_cove_retry_state_fields(request=request)

        assert fields == {
            "next_ep": 1,
            "interview_round": 0,
            "max_rounds": 5,
            "pathology_counts": {"cove_fail_closed": 1},
            "pathology_repeat_emitted": {"bucket"},
        }

    def test_build_cove_retry_episode_state_fields_preserves_episode_range(self, orch_with_ctx):
        runtime = orch_with_ctx.outcome_runtime

        request = runtime._build_cove_llm_request(
            cove=MagicMock(),
            final_manuscript="draft manuscript",
            final_state_updates={"hp": 10},
            cove_context={"quick_verify_warnings": "hint"},
            quick_msg="hint",
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            pathology_counts={"cove_fail_closed": 1},
            pathology_repeat_emitted={"bucket"},
        )

        fields = runtime._build_cove_retry_episode_state_fields(request=request)

        assert fields == {
            "next_ep": 1,
            "interview_round": 0,
            "max_rounds": 5,
        }

    def test_build_cove_retry_pathology_fields_preserves_pathology_state(self, orch_with_ctx):
        runtime = orch_with_ctx.outcome_runtime

        request = runtime._build_cove_llm_request(
            cove=MagicMock(),
            final_manuscript="draft manuscript",
            final_state_updates={"hp": 10},
            cove_context={"quick_verify_warnings": "hint"},
            quick_msg="hint",
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            pathology_counts={"cove_fail_closed": 1},
            pathology_repeat_emitted={"bucket"},
        )

        fields = runtime._build_cove_retry_pathology_fields(request=request)

        assert fields == {
            "pathology_counts": {"cove_fail_closed": 1},
            "pathology_repeat_emitted": {"bucket"},
        }

    def test_handle_cove_runtime_failure_logs_and_emits_advisory(self, orch_with_ctx):
        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        runtime._log_cove_runtime_advisory = MagicMock()

        runtime.handle_cove_runtime_failure(
            source="llm_verify",
            exc=RuntimeError("boom"),
            next_ep=2,
            interview_round=1,
            max_rounds=5,
            quick_warning="hint",
        )

        orch._ctx.ui.log.assert_any_call("   ⚠️ [CoVe] LLM 검증 런타임 실패 → Director PASS 유지")
        runtime._log_cove_runtime_advisory.assert_called_once_with(
            ep_num=2,
            round_num=1,
            source="llm_verify",
            error=ANY,
            quick_warning="hint",
        )

    def test_emit_cove_runtime_failure_logs_uses_quick_label(self, orch_with_ctx):
        orch = orch_with_ctx
        runtime = orch.outcome_runtime

        with patch("modules.core.stage4_outcome_runtime.logging.warning") as mock_warning:
            runtime._emit_cove_runtime_failure_logs(
                source_label="Quick",
                exc=RuntimeError("boom"),
                next_ep=2,
                interview_round=1,
                max_rounds=5,
            )

        orch._ctx.ui.log.assert_any_call("   ⚠️ [CoVe] Quick 검증 런타임 실패 → Director PASS 유지")
        assert mock_warning.call_count == 2

    def test_build_cove_runtime_failure_messages_returns_advisory_and_ui_text(self, orch_with_ctx):
        advisory_warning, ui_message = orch_with_ctx.outcome_runtime._build_cove_runtime_failure_messages(
            source_label="Quick",
            exc=RuntimeError("boom"),
        )

        assert advisory_warning == "[Advisory:CoVeRuntime:Quick] boom"
        assert ui_message == "   ⚠️ [CoVe] Quick 검증 런타임 실패 → Director PASS 유지"

    def test_build_cove_runtime_stage_warning_args_increments_round_number(self, orch_with_ctx):
        args = orch_with_ctx.outcome_runtime._build_cove_runtime_stage_warning_args(
            source_label="Quick",
            next_ep=2,
            interview_round=1,
            max_rounds=5,
        )

        assert args == (2, 2, 5, "Quick")

    def test_build_cove_runtime_round_fields_increments_round_number(self, orch_with_ctx):
        fields = orch_with_ctx.outcome_runtime._build_cove_runtime_round_fields(
            next_ep=2,
            interview_round=1,
            max_rounds=5,
        )

        assert fields == (2, 2, 5)

    def test_build_cove_runtime_source_field_preserves_source_label(self, orch_with_ctx):
        field = orch_with_ctx.outcome_runtime._build_cove_runtime_source_field(source_label="Quick")

        assert field == "Quick"

    def test_run_interview_round_step_breaks_on_accepted_pass(self, orch_with_ctx, minimal_round_ctx):
        from types import SimpleNamespace

        orch = orch_with_ctx
        orch._interview_round = MagicMock()
        orch._interview_round.run = MagicMock(return_value=SimpleNamespace(verdict="PASS"))
        orch.outcome_runtime.handle_pass_round_result = MagicMock(
            return_value=SimpleNamespace(
                accepted=True,
                should_continue=False,
                final_manuscript="accepted manuscript",
                final_title="accepted title",
                final_state_updates={"hp": 10},
                director_feedback="accepted feedback",
                previous_attempt={"score": 91},
            )
        )
        orch.outcome_runtime.handle_reject_round_result = MagicMock()
        loop_state = orch._build_interview_round_loop_state()

        result = orch._run_interview_round_step(
            round_ctx=minimal_round_ctx,
            loop_state=loop_state,
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            stage4_spinner=MagicMock(),
        )

        assert result.should_break is True
        assert result.should_continue is False
        assert result.round_ctx == minimal_round_ctx
        assert result.loop_state.final_manuscript == "accepted manuscript"
        assert result.loop_state.final_title == "accepted title"
        assert result.loop_state.final_state_updates == {"hp": 10}
        assert result.loop_state.director_feedback == "accepted feedback"
        assert result.loop_state.previous_attempt == {"score": 91}
        orch.outcome_runtime.handle_pass_round_result.assert_called_once()
        orch.outcome_runtime.handle_reject_round_result.assert_not_called()

    def test_apply_pass_round_step_disposition_returns_continue(self, orch_with_ctx, minimal_round_ctx):
        from modules.core.stage4_orchestrator import _PassRoundDisposition

        orch = orch_with_ctx
        loop_state = orch._build_interview_round_loop_state()
        pass_disposition = _PassRoundDisposition(
            should_continue=True,
            final_manuscript="retry manuscript",
            final_title="retry title",
            final_state_updates={"hp": 10},
            director_feedback="keep going",
            previous_attempt={"score": 81},
        )

        result = orch._apply_pass_round_step_disposition(
            round_ctx=minimal_round_ctx,
            loop_state=loop_state,
            pass_disposition=pass_disposition,
        )

        assert result is not None
        assert result.should_continue is True
        assert result.should_break is False
        assert result.loop_state.final_manuscript == "retry manuscript"
        assert result.loop_state.final_title == "retry title"
        assert result.loop_state.final_state_updates == {"hp": 10}
        assert result.loop_state.director_feedback == "keep going"
        assert result.loop_state.previous_attempt == {"score": 81}

    def test_handle_reject_round_result_chains_analysis_and_escalation(self, orch_with_ctx, minimal_round_ctx):
        from types import SimpleNamespace

        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        round_result = SimpleNamespace(
            director_feedback="retry feedback",
            previous_attempt={"score": 77},
        )
        runtime.analyze_reject_round = MagicMock(
            return_value=SimpleNamespace(
                director_feedback="analyzed feedback",
                previous_attempt={"score": 66, "reject_bucket": "quality_issue"},
                logic_error_streak=2,
                prev_reject_bucket="quality_issue",
                bucket_streak=3,
                prev_dominant_contradiction="timeline",
                contradiction_type_streak=2,
                score_history=[91, 88, 66],
                plateau_advisory_emitted=True,
                tf29_advisory="[bucket]",
                tf29_advisory_emitted=True,
                dominant_contradiction="timeline",
            )
        )
        escalated_round_ctx = dataclasses.replace(minimal_round_ctx, blueprint={"patched": True})
        runtime.apply_retry_repair_escalation = MagicMock(
            return_value=SimpleNamespace(
                round_ctx=escalated_round_ctx,
                director_feedback="escalated feedback",
                previous_attempt={"score": 66, "reject_bucket": "quality_issue", "escalated": True},
                logic_error_streak=3,
                inplace_attempted=True,
                blueprint_regenerated=True,
            )
        )

        result = runtime.handle_reject_round_result(
            round_ctx=minimal_round_ctx,
            round_result=round_result,
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            logic_error_streak=1,
            inplace_attempted=False,
            blueprint_regenerated=False,
            prev_reject_bucket="quality_issue",
            bucket_streak=2,
            prev_dominant_contradiction="timeline",
            contradiction_type_streak=1,
            score_history=[91, 88],
            plateau_advisory_emitted=False,
            tf29_advisory_emitted=False,
            pathology_counts={},
            pathology_repeat_emitted=set(),
        )

        assert result.round_ctx == escalated_round_ctx
        assert result.director_feedback == "escalated feedback"
        assert result.previous_attempt["escalated"] is True
        assert result.logic_error_streak == 3
        assert result.inplace_attempted is True
        assert result.blueprint_regenerated is True
        assert result.prev_reject_bucket == "quality_issue"
        assert result.bucket_streak == 3
        assert result.prev_dominant_contradiction == "timeline"
        assert result.contradiction_type_streak == 2
        assert result.score_history == [91, 88, 66]
        assert result.plateau_advisory_emitted is True
        runtime.analyze_reject_round.assert_called_once()
        runtime.apply_retry_repair_escalation.assert_called_once()
        escalation_kwargs = runtime.apply_retry_repair_escalation.call_args.kwargs
        assert escalation_kwargs["director_feedback"] == "analyzed feedback"
        assert escalation_kwargs["previous_attempt"]["reject_bucket"] == "quality_issue"
        assert escalation_kwargs["tf29_advisory"] == "[bucket]"
        assert escalation_kwargs["dominant_contradiction"] == "timeline"

    def test_apply_retry_repair_escalation_respects_quality_risk_threshold_override(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        round_ctx = dataclasses.replace(minimal_round_ctx, blueprint={"_stage3_meta": {"quality_risk": True}})
        orch.get_stage4_policy_int = MagicMock(
            side_effect=lambda *path, default: {
                "quality_risk_inplace_threshold": 2,
                "default_inplace_threshold": 3,
                "blueprint_regeneration_after_inplace_streak": 4,
            }.get(path[-1], default)
        )
        orch._apply_v75d_inplace_repair = MagicMock()

        result = runtime.apply_retry_repair_escalation(
            round_ctx=round_ctx,
            next_ep=1,
            interview_round=0,
            director_feedback="retry feedback",
            previous_attempt={"score": 61},
            logic_error_streak=1,
            inplace_attempted=False,
            blueprint_regenerated=False,
            tf29_advisory="",
            dominant_contradiction="timeline",
            pathology_counts={},
            pathology_repeat_emitted=set(),
        )

        orch._apply_v75d_inplace_repair.assert_not_called()
        assert result.round_ctx == round_ctx
        assert result.logic_error_streak == 1
        assert result.inplace_attempted is False
        assert result.blueprint_regenerated is False

    def test_apply_retry_repair_escalation_uses_stage3_binding_repair_signal(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        from types import SimpleNamespace

        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        round_ctx = dataclasses.replace(
            minimal_round_ctx,
            blueprint={
                "_stage3_meta": {
                    "revision_required": True,
                    "final_verdict": "PASS_WITH_FIX",
                    "binding_prevalidation_issue_count": 1,
                    "binding_prevalidation_categories": ["dead_npc"],
                }
            },
        )
        orch.get_stage4_policy_int = MagicMock(
            side_effect=lambda *path, default: {
                "quality_risk_inplace_threshold": 1,
                "default_inplace_threshold": 3,
                "blueprint_regeneration_after_inplace_streak": 4,
            }.get(path[-1], default)
        )
        escalated = SimpleNamespace(
            round_ctx=dataclasses.replace(round_ctx, blueprint={"patched": True}),
            director_feedback="patched",
            previous_attempt={"score": 61, "reject_bucket": "quality_issue"},
            logic_error_streak=0,
            inplace_attempted=True,
            blueprint_regenerated=False,
        )
        orch._apply_v75d_inplace_repair = MagicMock(return_value=escalated)

        result = runtime.apply_retry_repair_escalation(
            round_ctx=round_ctx,
            next_ep=1,
            interview_round=0,
            director_feedback="retry feedback",
            previous_attempt={"score": 61},
            logic_error_streak=1,
            inplace_attempted=False,
            blueprint_regenerated=False,
            tf29_advisory="",
            dominant_contradiction="timeline",
            pathology_counts={},
            pathology_repeat_emitted=set(),
        )

        orch._apply_v75d_inplace_repair.assert_called_once()
        assert result is escalated

    def test_apply_retry_repair_escalation_respects_blueprint_regeneration_threshold_override(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        from types import SimpleNamespace

        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        orch.get_stage4_policy_int = MagicMock(
            side_effect=lambda *path, default: {
                "quality_risk_inplace_threshold": 1,
                "default_inplace_threshold": 2,
                "blueprint_regeneration_after_inplace_streak": 4,
            }.get(path[-1], default)
        )
        regen_result = SimpleNamespace(
            round_ctx=dataclasses.replace(minimal_round_ctx, blueprint={"regenerated": True}),
            director_feedback="regen",
            previous_attempt={},
            logic_error_streak=0,
            inplace_attempted=True,
            blueprint_regenerated=True,
        )
        orch._apply_v75b_blueprint_regeneration = MagicMock(return_value=regen_result)

        result = runtime.apply_retry_repair_escalation(
            round_ctx=minimal_round_ctx,
            next_ep=1,
            interview_round=0,
            director_feedback="retry feedback",
            previous_attempt={"score": 61},
            logic_error_streak=4,
            inplace_attempted=True,
            blueprint_regenerated=False,
            tf29_advisory="",
            dominant_contradiction="timeline",
            pathology_counts={},
            pathology_repeat_emitted=set(),
        )

        orch._apply_v75b_blueprint_regeneration.assert_called_once()
        assert result is regen_result

    def test_apply_retry_repair_escalation_reroutes_repeated_qr7_plateau_to_full_rewrite(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        orch._apply_v75d_inplace_repair = MagicMock()
        previous_attempt = {
            "score": 88,
            "fix_scope": "partial",
            "repair_scope": "partial",
            "reject_bucket": "post_select_conflict",
            "error_category": "POST_SELECT_CONFLICT",
            "fix_scope_reasoning": "narrow patch",
            "plateau_detected": True,
            "provisional_pass_downgrade": True,
            "retry_budget_axes": {"repair": "patch_revision", "strategy": "patch"},
        }
        fingerprint = runtime.build_retry_pathology_payload(
            ep_num=1,
            round_num=0,
            previous_attempt=previous_attempt,
        )["pathology_fingerprint"]

        result = runtime.apply_retry_repair_escalation(
            round_ctx=minimal_round_ctx,
            next_ep=1,
            interview_round=0,
            director_feedback="retry feedback",
            previous_attempt=previous_attempt,
            logic_error_streak=1,
            inplace_attempted=False,
            blueprint_regenerated=False,
            tf29_advisory="",
            dominant_contradiction="timeline",
            pathology_counts={fingerprint: 1},
            pathology_repeat_emitted=set(),
        )

        orch._apply_v75d_inplace_repair.assert_not_called()
        assert result.round_ctx is minimal_round_ctx
        assert result.previous_attempt["fix_scope"] == "full"
        assert result.previous_attempt["repair_scope"] == "full"
        assert result.previous_attempt["retry_budget_axes"]["repair"] == "rewrite_regenerate"
        assert result.previous_attempt["qr7_contract"]["mode"] == "rewrite_reroute"
        assert result.previous_attempt["qr7_contract"]["repeat_count"] == 2
        assert result.director_feedback.startswith("[QR-7 escalation]")
        qr7_call = next(
            call
            for call in orch._ctx.ui.log.call_args_list
            if call.args and "repeated plateau -> local retry" in call.args[0]
        )
        assert qr7_call.kwargs["event_kind"] == "policy"
        assert qr7_call.kwargs["attempt_key"] == "s4:ep1:arc1:a1"

    def test_build_retry_pathology_payload_preserves_typed_contract_metadata(
        self,
        orch_with_ctx,
    ):
        runtime = orch_with_ctx.outcome_runtime
        previous_attempt = {
            "score": 83,
            "reject_bucket": "post_select_conflict",
            "gate_basis": "director_primary_reject",
            "fix_scope": "partial",
            "authoritative_fix_scope": "partial",
            "repair_scope": "partial",
            "error_category": "POST_SELECT_CONFLICT",
            "retry_pathology_source": "post_select_conflict",
            "contradiction_types": [
                "numeric_carryover_authority",
                "numeric_carryover_authority",
                "opening_action_continuity",
            ],
            "fix_pack_reason": "runtime_synthesized",
            "repair_contract": {"subtype": "numeric_carryover_authority", "mode": "bounded_patch"},
            "scope_authority": {"fix_scope": "director_authoritative"},
            "scope_origin": {"fix_scope": "runtime_widened"},
            "fix_pack_origin": {"source": "post_select_conflict"},
        }

        payload = runtime.build_retry_pathology_payload(
            ep_num=2,
            round_num=1,
            previous_attempt=previous_attempt,
        )

        assert payload["contradiction_type"] == "numeric_carryover_authority"
        assert payload["dominant_contradiction_type"] == "numeric_carryover_authority"
        assert payload["contradiction_types"] == [
            "numeric_carryover_authority",
            "numeric_carryover_authority",
            "opening_action_continuity",
        ]
        assert payload["fix_pack_reason"] == "runtime_synthesized"
        assert payload["repair_contract"] == {"subtype": "numeric_carryover_authority", "mode": "bounded_patch"}
        assert payload["scope_authority"] == {"fix_scope": "director_authoritative"}
        assert payload["scope_origin"]["fix_scope"] == "runtime_widened"
        assert payload["fix_pack_origin"] == {"source": "post_select_conflict"}

    def test_handle_reject_round_result_escalates_ifc_quality_issue_into_v75d_candidate(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        from types import SimpleNamespace

        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        orch.get_stage4_policy_int = MagicMock(
            side_effect=lambda *path, default: {
                "quality_risk_inplace_threshold": 1,
                "default_inplace_threshold": 2,
                "blueprint_regeneration_after_inplace_streak": 4,
            }.get(path[-1], default)
        )
        escalated = SimpleNamespace(
            round_ctx=dataclasses.replace(minimal_round_ctx, blueprint={"patched": True}),
            director_feedback="ifc escalated",
            previous_attempt={"score": 50, "reject_bucket": "quality_issue", "escalated": True},
            logic_error_streak=0,
            inplace_attempted=True,
            blueprint_regenerated=False,
        )
        orch._apply_v75d_inplace_repair = MagicMock(return_value=escalated)
        round_result = SimpleNamespace(
            director_feedback="retry feedback",
            previous_attempt={
                "score": 50,
                "reject_bucket": "quality_issue",
                "error_category": "QUALITY_ISSUE",
                "fix_scope_reasoning": "[IFC] immutable fact conflict detected; local patch is unsafe",
                "plateau_detected": True,
            },
        )

        result = runtime.handle_reject_round_result(
            round_ctx=minimal_round_ctx,
            round_result=round_result,
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            logic_error_streak=1,
            inplace_attempted=False,
            blueprint_regenerated=False,
            prev_reject_bucket="quality_issue",
            bucket_streak=1,
            prev_dominant_contradiction="",
            contradiction_type_streak=0,
            score_history=[50],
            plateau_advisory_emitted=True,
            tf29_advisory_emitted=False,
            pathology_counts={},
            pathology_repeat_emitted=set(),
        )

        orch._apply_v75d_inplace_repair.assert_called_once()
        assert result.round_ctx == escalated.round_ctx
        assert result.director_feedback == "ifc escalated"
        assert result.previous_attempt["escalated"] is True
        assert result.inplace_attempted is True

    def test_handle_reject_round_result_escalates_opening_continuity_quality_issue_into_v75d_candidate(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        from types import SimpleNamespace

        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        orch.get_stage4_policy_int = MagicMock(
            side_effect=lambda *path, default: {
                "quality_risk_inplace_threshold": 1,
                "default_inplace_threshold": 2,
                "blueprint_regeneration_after_inplace_streak": 4,
            }.get(path[-1], default)
        )
        escalated = SimpleNamespace(
            round_ctx=dataclasses.replace(minimal_round_ctx, blueprint={"patched": True}),
            director_feedback="continuity escalated",
            previous_attempt={"score": 50, "reject_bucket": "quality_issue", "escalated": True},
            logic_error_streak=0,
            inplace_attempted=True,
            blueprint_regenerated=False,
        )
        orch._apply_v75d_inplace_repair = MagicMock(return_value=escalated)
        round_result = SimpleNamespace(
            director_feedback="retry feedback",
            previous_attempt={
                "score": 50,
                "reject_bucket": "quality_issue",
                "error_category": "QUALITY_ISSUE",
                "contradiction_types": ["opening_action_continuity"],
                "open_review": "EP1 ending duplication in EP2 opening creates spatial continuity drift.",
                "fix_scope_reasoning": "opening continuity mismatch remains unresolved",
            },
        )

        result = runtime.handle_reject_round_result(
            round_ctx=minimal_round_ctx,
            round_result=round_result,
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            logic_error_streak=1,
            inplace_attempted=False,
            blueprint_regenerated=False,
            prev_reject_bucket="quality_issue",
            bucket_streak=1,
            prev_dominant_contradiction="",
            contradiction_type_streak=0,
            score_history=[50],
            plateau_advisory_emitted=False,
            tf29_advisory_emitted=False,
            pathology_counts={},
            pathology_repeat_emitted=set(),
        )

        orch._apply_v75d_inplace_repair.assert_called_once()
        assert result.round_ctx == escalated.round_ctx
        assert result.director_feedback == "continuity escalated"
        assert result.previous_attempt["escalated"] is True
        assert result.inplace_attempted is True

    def test_handle_reject_round_result_keeps_plain_quality_issue_outside_v75d_candidate(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        from types import SimpleNamespace

        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        orch.get_stage4_policy_int = MagicMock(
            side_effect=lambda *path, default: {
                "quality_risk_inplace_threshold": 1,
                "default_inplace_threshold": 2,
                "blueprint_regeneration_after_inplace_streak": 4,
            }.get(path[-1], default)
        )
        orch._apply_v75d_inplace_repair = MagicMock()
        round_result = SimpleNamespace(
            director_feedback="retry feedback",
            previous_attempt={
                "score": 50,
                "reject_bucket": "quality_issue",
                "error_category": "QUALITY_ISSUE",
                "fix_scope_reasoning": "style drift and weak engagement",
                "plateau_detected": True,
            },
        )

        result = runtime.handle_reject_round_result(
            round_ctx=minimal_round_ctx,
            round_result=round_result,
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            logic_error_streak=1,
            inplace_attempted=False,
            blueprint_regenerated=False,
            prev_reject_bucket="quality_issue",
            bucket_streak=1,
            prev_dominant_contradiction="",
            contradiction_type_streak=0,
            score_history=[50],
            plateau_advisory_emitted=True,
            tf29_advisory_emitted=False,
            pathology_counts={},
            pathology_repeat_emitted=set(),
        )

        orch._apply_v75d_inplace_repair.assert_not_called()
        assert result.round_ctx == minimal_round_ctx
        assert result.logic_error_streak == 0
        assert result.inplace_attempted is False
        assert result.blueprint_regenerated is False

    def test_run_interview_round_step_updates_loop_state_from_reject_path(self, orch_with_ctx, minimal_round_ctx):
        from types import SimpleNamespace

        orch = orch_with_ctx
        next_round_ctx = dataclasses.replace(minimal_round_ctx, blueprint={"patched": True})
        orch._interview_round = MagicMock()
        orch._interview_round.run = MagicMock(
            return_value=SimpleNamespace(
                verdict="REJECT",
                director_feedback="retry feedback",
                previous_attempt={"score": 77},
            )
        )
        orch.outcome_runtime.handle_pass_round_result = MagicMock()
        orch.outcome_runtime.handle_reject_round_result = MagicMock(
            return_value=SimpleNamespace(
                round_ctx=next_round_ctx,
                director_feedback="escalated feedback",
                previous_attempt={"score": 66, "reject_bucket": "quality_issue"},
                logic_error_streak=3,
                inplace_attempted=True,
                blueprint_regenerated=True,
                prev_reject_bucket="quality_issue",
                bucket_streak=3,
                prev_dominant_contradiction="timeline",
                contradiction_type_streak=2,
                score_history=[91, 88, 66],
                plateau_advisory_emitted=True,
                tf29_advisory_emitted=False,
            )
        )
        loop_state = orch._build_interview_round_loop_state()

        result = orch._run_interview_round_step(
            round_ctx=minimal_round_ctx,
            loop_state=loop_state,
            next_ep=1,
            interview_round=0,
            max_rounds=5,
            stage4_spinner=MagicMock(),
        )

        assert result.should_break is False
        assert result.should_continue is False
        assert result.round_ctx == next_round_ctx
        assert result.loop_state.director_feedback == "escalated feedback"
        assert result.loop_state.previous_attempt == {"score": 66, "reject_bucket": "quality_issue"}
        assert result.loop_state.logic_error_streak == 3
        assert result.loop_state.inplace_attempted is True
        assert result.loop_state.blueprint_regenerated is True
        assert result.loop_state.prev_reject_bucket == "quality_issue"
        assert result.loop_state.bucket_streak == 3
        assert result.loop_state.prev_dominant_contradiction == "timeline"
        assert result.loop_state.contradiction_type_streak == 2
        assert result.loop_state.score_history == [91, 88, 66]
        assert result.loop_state.plateau_advisory_emitted is True
        orch.outcome_runtime.handle_pass_round_result.assert_not_called()
        orch.outcome_runtime.handle_reject_round_result.assert_called_once()

    def test_finalize_round_outcome_loop_rejects_last_best_adoption_even_when_user_chooses_continue(
        self, orch_with_ctx
    ):
        orch = orch_with_ctx
        orch._ctx.get_int_input = MagicMock(return_value=1)

        result = orch._finalize_round_outcome_loop(
            next_ep=3,
            max_rounds=5,
            final_manuscript=None,
            final_title=None,
            final_state_updates={},
            previous_attempt={
                "best_manuscript": "best manuscript",
                "score": 77,
                "state_updates": {"hp": 10},
            },
            blueprint_regenerated=False,
            rounds_attempted=5,
        )

        assert result.should_return is True
        assert result.final_manuscript is None
        assert result.final_title is None
        assert result.final_state_updates == {}
        orch._ctx.get_int_input.assert_not_called()

    def test_finalize_round_outcome_loop_requests_human_review_when_no_best(self, orch_with_ctx):
        orch = orch_with_ctx

        result = orch._finalize_round_outcome_loop(
            next_ep=3,
            max_rounds=5,
            final_manuscript=None,
            final_title=None,
            final_state_updates={},
            previous_attempt={},
            blueprint_regenerated=True,
            rounds_attempted=5,
        )

        assert result.should_return is True
        assert result.final_manuscript is None
        assert result.final_title is None
        assert result.final_state_updates == {}
        orch._ctx.get_int_input.assert_not_called()

    def test_finalize_round_outcome_loop_ignores_policy_default_choice_for_last_best(self, orch_with_ctx):
        orch = orch_with_ctx
        orch._ctx.get_int_input = None
        orch._get_stage4_exhaustion_default_choice = MagicMock(return_value=1)

        result = orch._finalize_round_outcome_loop(
            next_ep=3,
            max_rounds=5,
            final_manuscript=None,
            final_title=None,
            final_state_updates={},
            previous_attempt={
                "best_manuscript": "best manuscript",
                "score": 77,
                "state_updates": {"hp": 10},
            },
            blueprint_regenerated=False,
            rounds_attempted=5,
        )

        assert result.should_return is True
        assert result.final_manuscript is None
        assert result.final_title is None
        assert result.final_state_updates == {}
        orch._get_stage4_exhaustion_default_choice.assert_not_called()

    def test_emit_stage4_retry_shadow_compare_logs_clip_decision_and_audit(self, orch_with_ctx):
        orch = orch_with_ctx
        orch._ctx.session_logger = MagicMock()
        orch._ctx.audit_event = MagicMock()
        orch._get_stage4_shadow_max_rounds = MagicMock(return_value=8)
        orch._stage4_shadow_log_all_episodes = MagicMock(return_value=False)

        orch._emit_stage4_retry_shadow_compare(
            next_ep=5,
            max_rounds=10,
            rounds_attempted=9,
            final_result="PASS",
            accepted=True,
            used_best_manuscript=False,
            blueprint_regenerated=False,
        )

        orch._ctx.session_logger.log_decision.assert_called_once()
        decision_kwargs = orch._ctx.session_logger.log_decision.call_args.kwargs
        assert decision_kwargs["stage"] == "stage4_control"
        assert decision_kwargs["decision_type"] == "retry_shadow_compare"
        assert decision_kwargs["result"] == "WOULD_CLIP"
        assert decision_kwargs["shadow_max_rounds"] == 8
        assert decision_kwargs["actual_max_rounds"] == 10
        assert decision_kwargs["rounds_attempted"] == 9
        assert decision_kwargs["accepted"] is True

        orch._ctx.audit_event.assert_called_once_with(
            "stage4_retry_shadow_compare",
            "stage4 retry shadow comparison recorded",
            {
                "shadow_max_rounds": 8,
                "actual_max_rounds": 10,
                "rounds_attempted": 9,
                "final_result": "PASS",
                "accepted": True,
                "used_best_manuscript": False,
                "blueprint_regenerated": False,
                "shadow_clipped": True,
            },
        )

    def test_finalize_round_outcome_loop_emits_shadow_compare_with_round_count(self, orch_with_ctx):
        orch = orch_with_ctx
        orch._emit_stage4_retry_shadow_compare = MagicMock()

        result = orch._finalize_round_outcome_loop(
            next_ep=3,
            max_rounds=10,
            final_manuscript="ok",
            final_title="제3화",
            final_state_updates={"hp": 10},
            previous_attempt={},
            blueprint_regenerated=False,
            rounds_attempted=7,
        )

        assert result.should_return is False
        orch._emit_stage4_retry_shadow_compare.assert_called_once_with(
            next_ep=3,
            max_rounds=10,
            rounds_attempted=7,
            final_result="PASS",
            accepted=True,
            used_best_manuscript=False,
            blueprint_regenerated=False,
        )

    def test_analyze_reject_round_emits_plateau_bucket_and_contradiction_advisories(
        self,
        orch_with_ctx,
    ):
        from types import SimpleNamespace

        runtime = orch_with_ctx.outcome_runtime
        previous_attempt = {
            "score": 88,
            "fix_scope_reasoning": "narrow patch",
            "reject_bucket": "quality_issue",
            "contradiction_types": ["타임라인", "타임라인"],
        }
        round_result = SimpleNamespace(
            error_category="LOGIC_ERROR",
        )

        result = runtime.analyze_reject_round(
            round_result=round_result,
            director_feedback="base feedback",
            previous_attempt=previous_attempt,
            logic_error_streak=1,
            prev_reject_bucket="quality_issue",
            bucket_streak=2,
            prev_dominant_contradiction="타임라인",
            contradiction_type_streak=1,
            score_history=[95, 92],
            plateau_advisory_emitted=False,
            tf29_advisory_emitted=False,
            blueprint_regenerated=False,
        )

        assert result.logic_error_streak == 2
        assert result.bucket_streak == 3
        assert result.prev_reject_bucket == "quality_issue"
        assert result.contradiction_type_streak == 2
        assert result.prev_dominant_contradiction == "타임라인"
        assert result.dominant_contradiction == "타임라인"
        assert result.plateau_advisory_emitted is True
        assert result.score_history == [95, 92, 88]
        assert result.previous_attempt["plateau_detected"] is True
        assert result.previous_attempt["score_history"] == [95, 92, 88]
        assert "narrow patch" in result.previous_attempt["fix_scope_reasoning"]
        assert "[⚠️ 점수 하락 추세]" in result.director_feedback
        assert "[⚠️ 반복 실패 패턴 감지]" in result.director_feedback
        assert "[⚠️ A-4 구조 진단]" in result.director_feedback
        assert result.tf29_advisory.startswith("[⚠️ 반복 실패 패턴 감지]")

    def test_apply_reject_bucket_advisory_emits_tf29_only_once(self, orch_with_ctx):
        runtime = orch_with_ctx.outcome_runtime
        previous_attempt = {"reject_bucket": "quality_issue"}

        first = runtime._apply_reject_bucket_advisory(
            previous_attempt=previous_attempt,
            director_feedback="base feedback",
            prev_reject_bucket="quality_issue",
            bucket_streak=2,
            blueprint_regenerated=False,
            tf29_advisory_emitted=False,
        )

        second = runtime._apply_reject_bucket_advisory(
            previous_attempt=previous_attempt,
            director_feedback=first.director_feedback,
            prev_reject_bucket=first.prev_reject_bucket,
            bucket_streak=first.bucket_streak,
            blueprint_regenerated=False,
            tf29_advisory_emitted=first.tf29_advisory_emitted,
        )

        assert first.tf29_advisory
        assert first.tf29_advisory_emitted is True
        assert second.tf29_advisory == ""
        assert second.tf29_advisory_emitted is True

    def test_apply_reject_score_trend_advisory_marks_plateau_and_reasoning(self, orch_with_ctx):
        runtime = orch_with_ctx.outcome_runtime
        previous_attempt = {
            "score": 88,
            "fix_scope_reasoning": "narrow patch",
        }

        result = runtime._apply_reject_score_trend_advisory(
            previous_attempt=previous_attempt,
            director_feedback="base feedback",
            score_history=[95, 92],
            plateau_advisory_emitted=False,
        )

        assert result.plateau_advisory_emitted is True
        assert result.score_history == [95, 92, 88]
        assert previous_attempt["plateau_detected"] is True
        assert previous_attempt["score_history"] == [95, 92, 88]
        assert "narrow patch" in previous_attempt["fix_scope_reasoning"]
        assert "[⚠️ 점수 하락 추세]" in result.director_feedback

    def test_analyze_reject_round_treats_post_select_conflict_as_logic_like_failure(
        self,
        orch_with_ctx,
    ):
        from types import SimpleNamespace

        runtime = orch_with_ctx.outcome_runtime
        round_result = SimpleNamespace(error_category="")
        previous_attempt = {
            "score": 88,
            "reject_bucket": "post_select_conflict",
            "error_category": "POST_SELECT_CONTINUITY_CONFLICT",
            "provisional_pass_downgrade": True,
        }

        result = runtime.analyze_reject_round(
            round_result=round_result,
            director_feedback="base feedback",
            previous_attempt=previous_attempt,
            logic_error_streak=1,
            prev_reject_bucket="quality_issue",
            bucket_streak=0,
            prev_dominant_contradiction="",
            contradiction_type_streak=0,
            score_history=[92],
            plateau_advisory_emitted=False,
            tf29_advisory_emitted=False,
            blueprint_regenerated=False,
        )

        assert result.logic_error_streak == 2
        assert result.prev_reject_bucket == "post_select_conflict"

    def test_analyze_reject_round_can_disable_post_select_logic_like_escalation(
        self,
        orch_with_ctx,
    ):
        from types import SimpleNamespace

        orch = orch_with_ctx
        runtime = orch.outcome_runtime
        orch.get_stage4_policy_bool = MagicMock(return_value=False)
        round_result = SimpleNamespace(error_category="")
        previous_attempt = {
            "score": 88,
            "reject_bucket": "post_select_conflict",
            "error_category": "POST_SELECT_CONTINUITY_CONFLICT",
            "provisional_pass_downgrade": True,
        }

        result = runtime.analyze_reject_round(
            round_result=round_result,
            director_feedback="base feedback",
            previous_attempt=previous_attempt,
            logic_error_streak=1,
            prev_reject_bucket="quality_issue",
            bucket_streak=0,
            prev_dominant_contradiction="",
            contradiction_type_streak=0,
            score_history=[92],
            plateau_advisory_emitted=False,
            tf29_advisory_emitted=False,
            blueprint_regenerated=False,
        )

        assert result.logic_error_streak == 0
        assert result.prev_reject_bucket == "post_select_conflict"

    def test_analyze_reject_round_treats_ifc_quality_issue_as_logic_like_failure(
        self,
        orch_with_ctx,
    ):
        from types import SimpleNamespace

        runtime = orch_with_ctx.outcome_runtime
        round_result = SimpleNamespace(error_category="QUALITY_ISSUE")
        previous_attempt = {
            "score": 50,
            "reject_bucket": "quality_issue",
            "error_category": "QUALITY_ISSUE",
            "fix_scope_reasoning": "[IFC] immutable fact conflict detected; local patch is unsafe",
            "plateau_detected": True,
        }

        result = runtime.analyze_reject_round(
            round_result=round_result,
            director_feedback="base feedback",
            previous_attempt=previous_attempt,
            logic_error_streak=1,
            prev_reject_bucket="quality_issue",
            bucket_streak=1,
            prev_dominant_contradiction="",
            contradiction_type_streak=0,
            score_history=[50],
            plateau_advisory_emitted=True,
            tf29_advisory_emitted=False,
            blueprint_regenerated=False,
        )

        assert result.logic_error_streak == 2
        assert result.prev_reject_bucket == "quality_issue"

    def test_analyze_reject_round_treats_opening_continuity_quality_issue_as_logic_like_failure(
        self,
        orch_with_ctx,
    ):
        from types import SimpleNamespace

        runtime = orch_with_ctx.outcome_runtime
        round_result = SimpleNamespace(error_category="QUALITY_ISSUE")
        previous_attempt = {
            "score": 50,
            "reject_bucket": "quality_issue",
            "error_category": "QUALITY_ISSUE",
            "contradiction_types": ["opening_action_continuity"],
            "open_review": "EP1 ending duplication in EP2 opening creates spatial continuity drift.",
            "fix_scope_reasoning": "opening continuity mismatch remains unresolved",
        }

        result = runtime.analyze_reject_round(
            round_result=round_result,
            director_feedback="base feedback",
            previous_attempt=previous_attempt,
            logic_error_streak=1,
            prev_reject_bucket="quality_issue",
            bucket_streak=1,
            prev_dominant_contradiction="",
            contradiction_type_streak=0,
            score_history=[50],
            plateau_advisory_emitted=False,
            tf29_advisory_emitted=False,
            blueprint_regenerated=False,
        )

        assert result.logic_error_streak == 2
        assert result.prev_reject_bucket == "quality_issue"

    def test_analyze_reject_round_keeps_plain_quality_issue_outside_logic_like_failure(
        self,
        orch_with_ctx,
    ):
        from types import SimpleNamespace

        runtime = orch_with_ctx.outcome_runtime
        round_result = SimpleNamespace(error_category="QUALITY_ISSUE")
        previous_attempt = {
            "score": 50,
            "reject_bucket": "quality_issue",
            "error_category": "QUALITY_ISSUE",
            "fix_scope_reasoning": "style drift and weak engagement",
            "plateau_detected": True,
        }

        result = runtime.analyze_reject_round(
            round_result=round_result,
            director_feedback="base feedback",
            previous_attempt=previous_attempt,
            logic_error_streak=1,
            prev_reject_bucket="quality_issue",
            bucket_streak=1,
            prev_dominant_contradiction="",
            contradiction_type_streak=0,
            score_history=[50],
            plateau_advisory_emitted=True,
            tf29_advisory_emitted=False,
            blueprint_regenerated=False,
        )

        assert result.logic_error_streak == 0
        assert result.prev_reject_bucket == "quality_issue"

    def test_apply_v75d_inplace_repair_resets_attempt_state_and_logs_snapshot(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        orch = orch_with_ctx
        bp_agent = MagicMock()
        bp_agent._inplace_patch_blueprint.return_value = {"patched": True}
        orch._ctx.agents["three_phase_bp"] = bp_agent
        orch._ctx.audit_event = MagicMock()
        orch._build_stage4_to_3_reverse_feedback = MagicMock(return_value="[S4->S3] hint")
        orch._merge_blueprint_feedback = MagicMock(return_value="merged blueprint feedback")
        orch._log_escalation_event = MagicMock()

        with (
            patch(
                "modules.core.stage4_orchestrator.snapshot_logged_artifact",
                return_value={
                    "candidate_key": "V75-D|blueprint_inplace",
                    "content_hash": "hash-123",
                    "artifact_path": "logs/artifacts/stage4/ep_0001/patched.json",
                },
            ),
            patch("modules.core.constants.calc_patch_change_ratio", return_value=0.2),
            patch("modules.core.constants.log_patch_diff"),
        ):
            result = orch._apply_v75d_inplace_repair(
                round_ctx=minimal_round_ctx,
                next_ep=1,
                interview_round=0,
                director_feedback="director feedback",
                previous_attempt={"fix_scope": "patch", "score": 72},
                logic_error_streak=2,
                tf29_advisory="[bucket]",
                dominant_contradiction="timeline",
            )

        assert result.inplace_attempted is True
        assert result.blueprint_regenerated is False
        assert result.logic_error_streak == 0
        assert result.previous_attempt == {}
        assert result.round_ctx.blueprint == {"patched": True}
        assert result.director_feedback.startswith("[bucket]\n[V75-D 블루프린트 inplace 패치 완료]")
        bp_agent._inplace_patch_blueprint.assert_called_once()
        assert bp_agent._inplace_patch_blueprint.call_args.kwargs["director_feedback"] == "merged blueprint feedback"
        orch._ctx.audit_event.assert_called_once()
        orch._log_escalation_event.assert_called_once()
        escalation_args = orch._log_escalation_event.call_args.args
        escalation_kwargs = orch._log_escalation_event.call_args.kwargs
        assert escalation_args[:3] == (1, "V75-D_INPLACE", 0)
        assert escalation_kwargs["candidate_key"] == "V75-D|blueprint_inplace"
        assert escalation_kwargs["content_hash"] == "hash-123"
        assert escalation_kwargs["artifact_path"].endswith("patched.json")

    def test_stage4_to_3_reverse_feedback_appends_completed_event_replay_contract(self, orch_with_ctx):
        orch = orch_with_ctx
        orch._ctx.generate_reverse_feedback_stage4_to_3 = MagicMock(return_value="[S4->S3] base hint")

        feedback = orch._build_stage4_to_3_reverse_feedback(
            director_feedback="[V67] History Conflict: already completed admission scene was replayed",
            previous_attempt={
                "rejection_reason": "completed_event_replay",
                "open_review": "do not use the old event as scene_1 again",
            },
        )

        assert feedback.startswith("[Completed prior event replay contract]")
        assert "must not become the next episode's scene_1/opening event again" in feedback
        assert "continue from its aftermath, consequence, or a new decision/action" in feedback
        assert "[S4->S3] base hint" in feedback

    def test_stage4_to_3_reverse_feedback_returns_completed_event_contract_without_callback(self, orch_with_ctx):
        orch = orch_with_ctx
        orch._ctx.generate_reverse_feedback_stage4_to_3 = None

        feedback = orch._build_stage4_to_3_reverse_feedback(
            director_feedback="History Conflict: completed event replay",
            previous_attempt={},
        )

        assert feedback.startswith("[Completed prior event replay contract]")
        assert "Regenerate scene_breakdown.scene_1.title" in feedback

    def test_stage4_to_3_reverse_feedback_detects_structured_korean_history_conflict(self, orch_with_ctx):
        orch = orch_with_ctx
        orch._ctx.generate_reverse_feedback_stage4_to_3 = MagicMock(return_value="")

        feedback = orch._build_stage4_to_3_reverse_feedback(
            director_feedback="이전 화에서 이미 완료된 입단 선언을 4화 opening에서 다시 중복 묘사했습니다.",
            previous_attempt={
                "reject_bucket": "post_select_conflict",
                "contradiction_types": ["history", "continuity"],
                "conflict_contract": {
                    "completed_event_replay": True,
                    "contradiction_types": ["history"],
                },
            },
        )

        assert feedback.startswith("[Completed prior event replay contract]")
        assert "must not become the next episode's scene_1/opening event again" in feedback

    def test_run_v75d_patch_attempt_keeps_state_when_patch_returns_empty(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        orch = orch_with_ctx
        bp_agent = MagicMock()
        bp_agent._inplace_patch_blueprint.return_value = None
        orch._ctx.agents["three_phase_bp"] = bp_agent
        orch._build_stage4_to_3_reverse_feedback = MagicMock(return_value="[S4->S3] hint")
        orch._merge_blueprint_feedback = MagicMock(return_value="merged blueprint feedback")

        payload = orch._run_v75d_patch_attempt(
            round_ctx=minimal_round_ctx,
            next_ep=1,
            interview_round=0,
            director_feedback="director feedback",
            previous_attempt={"fix_scope": "patch", "score": 72},
            logic_error_streak=2,
            tf29_advisory="[bucket]",
        )

        assert payload.success is False
        assert payload.round_ctx is minimal_round_ctx
        assert payload.director_feedback == "director feedback"
        assert payload.previous_attempt == {"fix_scope": "patch", "score": 72}
        assert payload.logic_error_streak == 2
        assert payload.artifact_payload.artifact_meta["candidate_key"] == ""
        orch._build_stage4_to_3_reverse_feedback.assert_called_once_with(
            director_feedback="director feedback",
            previous_attempt={"fix_scope": "patch", "score": 72},
        )
        orch._merge_blueprint_feedback.assert_called_once_with("director feedback", "[S4->S3] hint")
        bp_agent._inplace_patch_blueprint.assert_called_once()
        assert any("inplace 패치 실패" in call.args[0] for call in orch._ctx.ui.log.call_args_list if call.args)

    def test_attempt_v75d_inplace_blueprint_patch_returns_none_on_exception(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        orch = orch_with_ctx
        orch._request_v75d_inplace_blueprint_patch = MagicMock(side_effect=RuntimeError("boom"))

        with patch("modules.core.stage4_orchestrator.logging.warning") as mock_warning:
            patched_bp = orch._attempt_v75d_inplace_blueprint_patch(
                round_ctx=minimal_round_ctx,
                next_ep=1,
                director_feedback="director feedback",
                previous_attempt={"fix_scope": "patch", "score": 72},
                logic_error_streak=2,
            )

        assert patched_bp is None
        orch._request_v75d_inplace_blueprint_patch.assert_called_once_with(
            round_ctx=minimal_round_ctx,
            next_ep=1,
            director_feedback="director feedback",
            previous_attempt={"fix_scope": "patch", "score": 72},
        )
        mock_warning.assert_called_once()

    def test_build_failed_v75d_patch_attempt_payload_preserves_state_and_blank_artifact(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        orch = orch_with_ctx

        payload = orch._build_failed_v75d_patch_attempt_payload(
            round_ctx=minimal_round_ctx,
            director_feedback="director feedback",
            previous_attempt={"fix_scope": "patch", "score": 72},
            logic_error_streak=2,
        )

        assert payload.success is False
        assert payload.round_ctx is minimal_round_ctx
        assert payload.director_feedback == "director feedback"
        assert payload.previous_attempt == {"fix_scope": "patch", "score": 72}
        assert payload.logic_error_streak == 2
        assert payload.artifact_payload.artifact_meta == {
            "candidate_key": "",
            "content_hash": "",
            "artifact_path": "",
        }

    def test_request_v75d_inplace_blueprint_patch_merges_feedback_before_agent_call(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        orch = orch_with_ctx
        bp_agent = MagicMock()
        bp_agent._inplace_patch_blueprint.return_value = {"patched": True}
        orch._ctx.agents["three_phase_bp"] = bp_agent
        orch._build_stage4_to_3_reverse_feedback = MagicMock(return_value="[S4->S3] hint")
        orch._merge_blueprint_feedback = MagicMock(return_value="merged blueprint feedback")

        patched_bp = orch._request_v75d_inplace_blueprint_patch(
            round_ctx=minimal_round_ctx,
            next_ep=1,
            director_feedback="director feedback",
            previous_attempt={"fix_scope": "patch", "score": 72},
        )

        assert patched_bp == {"patched": True}
        orch._build_stage4_to_3_reverse_feedback.assert_called_once_with(
            director_feedback="director feedback",
            previous_attempt={"fix_scope": "patch", "score": 72},
        )
        orch._merge_blueprint_feedback.assert_called_once_with("director feedback", "[S4->S3] hint")
        bp_agent._inplace_patch_blueprint.assert_called_once_with(
            original_blueprint=minimal_round_ctx.blueprint,
            director_feedback="merged blueprint feedback",
            ep_num=1,
            arc_data=minimal_round_ctx.arc_data,
        )

    def test_request_v75d_inplace_blueprint_patch_appends_opening_replay_correction_contract(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        orch = orch_with_ctx
        bp_agent = MagicMock()
        bp_agent._inplace_patch_blueprint.return_value = {"patched": True}
        orch._ctx.agents["three_phase_bp"] = bp_agent
        orch._build_stage4_to_3_reverse_feedback = MagicMock(return_value="[S4->S3] hint")
        orch._merge_blueprint_feedback = MagicMock(
            return_value="merged blueprint feedback\ncontinuity replay\nflashback\nhistory conflict\nalready completed"
        )
        minimal_round_ctx = dataclasses.replace(
            minimal_round_ctx,
            blueprint={
                "start_location": "본가 저택 서재 앞 복도",
                "time_flow": "오전",
                "opening_transition": {"type": "direct_continuation"},
                "scene_breakdown": {
                    "scene_1": {
                        "location": "본가 저택 서재 앞 복도",
                        "summary": "통화 직후 후속 비트",
                        "key_events": ["통화 마무리"],
                    }
                },
            },
            prev_ending="한시우가 본가 저택 서재 앞 복도에서 박성호와의 통화를 마무리했다.",
            chain_link_section="pending_actions: PB 반응 확인 후 이동한다.",
        )

        orch._request_v75d_inplace_blueprint_patch(
            round_ctx=minimal_round_ctx,
            next_ep=2,
            director_feedback="director feedback",
            previous_attempt={
                "fix_pack": {
                    "must_fix": [
                        "EP2 opening에서 EP1 통화 장면을 회상처럼 재연하지 말고 직후 비트로 이어갈 것.",
                        "신탁 자산 20억 원 기준으로 수치를 정합하게 맞출 것.",
                    ],
                    "success_condition": "scene_1 summary와 key_events가 직전 화 후속 비트로 정렬되면 성공",
                }
            },
        )

        patch_feedback = bp_agent._inplace_patch_blueprint.call_args.kwargs["director_feedback"]
        assert "[V75-D correction contract]" in patch_feedback
        assert "[Completed prior event replay contract]" in patch_feedback
        assert "must not become the next episode's scene_1/opening event again" in patch_feedback
        assert "scene_breakdown.scene_1.summary" in patch_feedback
        assert "EP1에서 이미 완료된 전화/행동을 EP2 opening에서 회상·재연 장면으로 다시 쓰지 마세요." in patch_feedback
        assert "authoritative opening location은 '본가 저택 서재 앞 복도'" in patch_feedback
        assert "authoritative opening_transition.type은 'direct_continuation'" in patch_feedback
        assert "integrated_scenario, scene_1.summary, scene_1.key_events, expected_ending" in patch_feedback

    def test_apply_v75d_patch_success_captures_artifact_and_returns_reset_payload(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        orch = orch_with_ctx
        orch._capture_v75d_patch_artifact = MagicMock(
            return_value=MagicMock(artifact_meta={"candidate_key": "V75-D|blueprint_inplace"})
        )
        orch._build_v75d_success_payload = MagicMock(
            return_value=MagicMock(
                round_ctx=dataclasses.replace(minimal_round_ctx, blueprint={"patched": True}),
                director_feedback="[bucket]\n[V75-D 블루프린트 inplace 패치 완료]",
                previous_attempt={},
                logic_error_streak=0,
            )
        )

        payload = orch._apply_v75d_patch_success(
            round_ctx=minimal_round_ctx,
            patched_bp={"patched": True},
            next_ep=1,
            interview_round=0,
            director_feedback="director feedback",
            previous_attempt={"fix_scope": "patch", "score": 72},
            logic_error_streak=2,
            tf29_advisory="[bucket]",
        )

        assert payload.success is True
        assert payload.round_ctx.blueprint == {"patched": True}
        assert payload.director_feedback.startswith("[bucket]")
        assert payload.previous_attempt == {}
        assert payload.logic_error_streak == 0
        orch._capture_v75d_patch_artifact.assert_called_once_with(
            round_ctx=minimal_round_ctx,
            patched_bp={"patched": True},
            next_ep=1,
            interview_round=0,
        )
        orch._build_v75d_success_payload.assert_called_once_with(
            round_ctx=minimal_round_ctx,
            patched_bp={"patched": True},
            tf29_advisory="[bucket]",
        )

    def test_capture_v75d_patch_artifact_emits_audit_with_change_ratio(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        orch = orch_with_ctx
        orch._ctx.audit_event = MagicMock()

        with (
            patch(
                "modules.core.stage4_orchestrator.snapshot_logged_artifact",
                return_value={
                    "candidate_key": "V75-D|blueprint_inplace",
                    "content_hash": "hash-123",
                    "artifact_path": "logs/artifacts/stage4/ep_0001/patched.json",
                },
            ),
            patch("modules.core.constants.calc_patch_change_ratio", return_value=0.25),
            patch("modules.core.constants.log_patch_diff"),
        ):
            payload = orch._capture_v75d_patch_artifact(
                round_ctx=minimal_round_ctx,
                patched_bp={"patched": True},
                next_ep=1,
                interview_round=0,
            )

        assert payload.artifact_meta["candidate_key"] == "V75-D|blueprint_inplace"
        assert payload.change_ratio == 0.25
        orch._ctx.audit_event.assert_called_once_with(
            "stage4_v75d_blueprint_patch_snapshot",
            "stage4 V75-D blueprint patch snapshot persisted",
            {
                "ep_num": 1,
                "round_num": 1,
                "candidate_key": "V75-D|blueprint_inplace",
                "content_hash": "hash-123",
                "artifact_path": "logs/artifacts/stage4/ep_0001/patched.json",
                "change_ratio": 0.25,
            },
        )

    def test_build_v75d_success_payload_resets_state_and_prepends_tf29(self, orch_with_ctx, minimal_round_ctx):
        orch = orch_with_ctx

        payload = orch._build_v75d_success_payload(
            round_ctx=minimal_round_ctx,
            patched_bp={"patched": True},
            tf29_advisory="[bucket]",
        )

        assert payload.round_ctx.blueprint == {"patched": True}
        assert payload.logic_error_streak == 0
        assert payload.previous_attempt == {}
        assert payload.director_feedback.startswith("[bucket]\n[V75-D 블루프린트 inplace 패치 완료]")

    def test_apply_v75b_blueprint_regeneration_resets_attempt_state_on_success(
        self,
        orch_with_ctx,
        minimal_round_ctx,
    ):
        orch = orch_with_ctx
        orch._build_stage4_to_3_reverse_feedback = MagicMock(return_value="[S4->S3] hint")
        orch._merge_blueprint_feedback = MagicMock(return_value="merged blueprint feedback")
        orch._regenerate_blueprint = MagicMock(return_value={"regenerated": True})
        orch._log_escalation_event = MagicMock()

        result = orch._apply_v75b_blueprint_regeneration(
            round_ctx=minimal_round_ctx,
            next_ep=2,
            interview_round=1,
            director_feedback="director feedback",
            previous_attempt={"fix_scope": "rewrite", "score": 63},
            logic_error_streak=3,
            tf29_advisory="[bucket]",
            dominant_contradiction="timeline",
        )

        assert result.inplace_attempted is True
        assert result.blueprint_regenerated is True
        assert result.logic_error_streak == 0
        assert result.previous_attempt == {}
        assert result.round_ctx.blueprint == {"regenerated": True}
        assert result.director_feedback.startswith("[bucket]\n[V75-B 블루프린트 재생성 완료]")
        orch._regenerate_blueprint.assert_called_once_with(
            2,
            minimal_round_ctx.arc_data,
            minimal_round_ctx,
            external_feedback="merged blueprint feedback",
        )
        orch._log_escalation_event.assert_called_once()
        escalation_args = orch._log_escalation_event.call_args.args
        assert escalation_args[:3] == (2, "V75-B_FULL_REGEN", 0)

    def test_handle_round_outcome_emits_retry_pathology_repeat(
        self, orch_with_ctx, minimal_round_ctx, monkeypatch, tmp_path
    ):
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
        orch._ctx.current_project.name = "pathology_project"
        orch._ctx.current_project.paths.root = tmp_path / "pathology_project"
        orch._ctx.audit_event = MagicMock()
        orch._ctx.get_module = MagicMock(return_value=None)
        orch._interview_round = MagicMock()
        repeated_attempt = {
            "score": 95,
            "fix_scope": "partial",
            "reject_bucket": "post_select_conflict",
            "gate_basis": "post_select_conflict",
            "repair_scope": "partial",
            "fix_scope_reasoning": "Fix Pack is missing",
            "retry_pathology_source": "post_select_conflict",
            "provisional_pass_downgrade": True,
        }
        orch._interview_round.run = MagicMock(
            side_effect=[
                _InterviewRoundResult(
                    verdict="REJECT",
                    director_feedback="retry one",
                    previous_attempt=dict(repeated_attempt),
                    error_category="",
                ),
                _InterviewRoundResult(
                    verdict="REJECT",
                    director_feedback="retry two",
                    previous_attempt=dict(repeated_attempt),
                    error_category="",
                ),
                _InterviewRoundResult(
                    verdict="PASS",
                    director_feedback="done",
                    previous_attempt={},
                    final_manuscript="final manuscript",
                    final_title="final title",
                    final_state_updates={"hp": 10},
                ),
            ]
        )

        import modules.core.spinners

        monkeypatch.setattr(modules.core.spinners, "StageSpinner", MagicMock())

        result = orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        assert result.final_manuscript == "final manuscript"
        log_path = tmp_path / "pathology_project" / "logs" / "episode_production.jsonl"
        rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        pathology_rows = [row for row in rows if row.get("event") == "STAGE4_RETRY_PATHOLOGY"]
        repeat_rows = [row for row in rows if row.get("event") == "STAGE4_RETRY_PATHOLOGY_REPEAT"]
        assert len(pathology_rows) >= 2
        assert len(repeat_rows) == 1
        assert repeat_rows[0]["pathology_source"] == "post_select_conflict"
        assert repeat_rows[0]["provisional_pass_downgrade"] is True
        assert repeat_rows[0]["repeat_count"] == 2
        orch._ctx.audit_event.assert_any_call(
            "stage4_retry_pathology_repeat",
            "stage4 retry pathology repeated",
            ANY,
        )


class TestStage4OrchestratorImport:
    def test_import_succeeds(self):
        """Stage4Orchestrator import 성공"""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        assert Stage4Orchestrator is not None

    def test_trim_mandatory_context_for_budget_preserves_recent_tail_context(self):
        from modules.core.stage4_orchestrator import _trim_mandatory_context_for_budget

        text = "[MANDATORY]\nHEAD-CONTEXT\n" + ("A" * 260) + "\nTAIL-CONTEXT"
        trimmed = _trim_mandatory_context_for_budget(text, max_chars=180)

        assert len(trimmed) <= 180
        assert "HEAD-CONTEXT" in trimmed
        assert "TAIL-CONTEXT" in trimmed

    def test_fit_mandatory_context_budget_drops_low_priority_sections(self):
        from modules.core.stage4_orchestrator import (
            _fit_mandatory_context_budget,
            _MandatoryContextBudgetResult,
        )

        text = "[A]\n" + ("A" * 50) + "\n[B]\n" + ("B" * 50) + "\n[C]\n" + ("C" * 50)

        result = _fit_mandatory_context_budget(text, max_chars=130)

        assert isinstance(result, _MandatoryContextBudgetResult)
        assert result.removed_count == 1
        assert result.removed_chars > 0
        assert result.used_fallback is False
        assert "[A]" in result.mandatory_context
        assert "[B]" in result.mandatory_context
        assert "[C]" not in result.mandatory_context

    def test_fit_mandatory_context_budget_falls_back_for_single_section(self):
        from modules.core.stage4_orchestrator import _fit_mandatory_context_budget

        text = "[MANDATORY]\nHEAD-CONTEXT\n" + ("A" * 260) + "\nTAIL-CONTEXT"

        result = _fit_mandatory_context_budget(text, max_chars=180)

        assert result.removed_count == 0
        assert result.used_fallback is True
        assert len(result.mandatory_context) <= 180
        assert "HEAD-CONTEXT" in result.mandatory_context
        assert "TAIL-CONTEXT" in result.mandatory_context

    def test_apply_mandatory_context_budget_logs_section_removal(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx._stage4_context_budget_meta = {
            "budget_ledger": {"effective_cap": 130, "dropped_chars": 0, "overflow_chars": 10}
        }

        orch = Stage4Orchestrator(mock_app, context=ctx)
        text = "[A]\n" + ("A" * 50) + "\n[B]\n" + ("B" * 50) + "\n[C]\n" + ("C" * 50)

        with patch("modules.core.stage4_orchestrator._threshold", return_value=130):
            result = orch._apply_mandatory_context_budget(text)

        assert "[C]" not in result
        ctx.ui.log.assert_called_once()

    def test_apply_mandatory_context_budget_logs_fallback_truncation(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        text = "[MANDATORY]\nHEAD-CONTEXT\n" + ("A" * 260) + "\nTAIL-CONTEXT"

        with patch("modules.core.stage4_orchestrator._threshold", return_value=180):
            result = orch._apply_mandatory_context_budget(text)

        assert len(result) <= 180
        assert "TAIL-CONTEXT" in result
        ctx.ui.log.assert_called_once()

    def test_consume_episode_round_outcome_runs_post_tasks_on_return(self, mock_app):
        from modules.core.stage4_orchestrator import (
            Stage4Orchestrator,
            _EpisodeLoopDisposition,
            _RoundOutcome,
        )

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._post_processor = MagicMock()

        result = orch._consume_episode_round_outcome(
            outcome=_RoundOutcome(
                final_manuscript=None,
                final_title=None,
                final_state_updates={},
                should_return=True,
            ),
            next_ep=5,
            blueprint={"scene_breakdown": {}},
            arc_data={"arc_no": 1},
            output_dir=Path("."),
            v50_modules_available=False,
            skip_pause=True,
        )

        assert isinstance(result, _EpisodeLoopDisposition)
        assert result.should_return is True
        assert result.should_break is False
        orch.post_processor.run_post_episode_tasks.assert_called_once_with(skip_pause=True)

    def test_consume_episode_round_outcome_delegates_pass_processing(self, mock_app, tmp_path):
        from modules.core.stage4_orchestrator import (
            Stage4Orchestrator,
            _EpisodeLoopDisposition,
            _RoundOutcome,
        )

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._process_episode_pass = MagicMock(return_value=True)

        result = orch._consume_episode_round_outcome(
            outcome=_RoundOutcome(
                final_manuscript="final manuscript",
                final_title="episode title",
                final_state_updates={"k": "v"},
                should_return=False,
            ),
            next_ep=7,
            blueprint={"scene_breakdown": {"a": 1}},
            arc_data={"arc_no": 2},
            output_dir=tmp_path,
            v50_modules_available=True,
            skip_pause=False,
        )

        assert isinstance(result, _EpisodeLoopDisposition)
        assert result.should_return is False
        assert result.should_break is False
        orch._process_episode_pass.assert_called_once_with(
            next_ep=7,
            final_manuscript="final manuscript",
            final_title="episode title",
            final_state_updates={"k": "v"},
            blueprint={"scene_breakdown": {"a": 1}},
            arc_data={"arc_no": 2},
            output_dir=tmp_path,
            v50_modules_available=True,
        )

    def test_consume_episode_round_outcome_returns_break_on_pass_save_failure(self, mock_app, tmp_path):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _RoundOutcome

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._process_episode_pass = MagicMock(return_value=False)

        result = orch._consume_episode_round_outcome(
            outcome=_RoundOutcome(
                final_manuscript="final manuscript",
                final_title=None,
                final_state_updates={},
                should_return=False,
            ),
            next_ep=9,
            blueprint={"scene_breakdown": {"b": 2}},
            arc_data={"arc_no": 3},
            output_dir=tmp_path,
            v50_modules_available=False,
            skip_pause=False,
        )

        assert result.should_return is False
        assert result.should_break is True

    def test_checkpoint_episode_loop_breaks_on_safety_limit(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _EpisodeLoopCheckpoint

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._checkpoint_episode_loop(
            loop_guard=6,
            max_loops=5,
            target_ep=None,
            chief_writer=MagicMock(),
        )

        assert isinstance(result, _EpisodeLoopCheckpoint)
        assert result.should_break is True
        assert result.next_ep is None
        ctx.ui.log.assert_called_once()

    def test_checkpoint_episode_loop_breaks_on_target_ep_reached(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _EpisodeLoopCheckpoint

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.get_latest_episode_number = MagicMock(return_value=6)

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._interview_round = MagicMock()
        orch._set_agent_telemetry_context = MagicMock()
        orch._log_target_ep_reached = MagicMock()

        result = orch._checkpoint_episode_loop(
            loop_guard=1,
            max_loops=5,
            target_ep=5,
            chief_writer=MagicMock(),
        )

        assert isinstance(result, _EpisodeLoopCheckpoint)
        assert result.should_break is True
        assert result.next_ep is None
        orch._set_agent_telemetry_context.assert_called_once_with(ep_num=6, extra_agents=[ANY])
        orch._log_target_ep_reached.assert_called_once_with(target_ep=5, next_ep=6)
        ctx.ui.log.assert_called_once()

    def test_checkpoint_episode_loop_returns_next_ep_and_resets_warnings(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _EpisodeLoopCheckpoint

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.get_latest_episode_number = MagicMock(return_value=4)

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._interview_round = MagicMock()
        orch._interview_round.time_warnings = ["stale"]
        orch._set_agent_telemetry_context = MagicMock()

        result = orch._checkpoint_episode_loop(
            loop_guard=1,
            max_loops=5,
            target_ep=5,
            chief_writer=MagicMock(),
        )

        assert isinstance(result, _EpisodeLoopCheckpoint)
        assert result.should_break is False
        assert result.next_ep == 4
        assert orch.interview_round.time_warnings == []
        orch._set_agent_telemetry_context.assert_called_once_with(ep_num=4, extra_agents=[ANY])
        ctx.ui.log.assert_not_called()

    def test_prepare_current_episode_inputs_returns_none_when_blueprint_missing(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.get_blueprint = MagicMock(return_value=None)

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._prepare_current_episode_inputs(next_ep=3)

        assert result is None
        ctx.ui.log.assert_called_once()

    def test_prepare_current_episode_inputs_returns_none_when_arc_missing(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.get_blueprint = MagicMock(return_value={"scene_breakdown": {}})
        ctx.current_project.arcs = []

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._prepare_current_episode_inputs(next_ep=3)

        assert result is None
        ctx.ui.log.assert_called_once()

    def test_prepare_current_episode_inputs_applies_preflight_patch_and_advisory(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _EpisodeLoopInputs

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.get_blueprint = MagicMock(return_value={"scene_breakdown": {"a": 1}})
        ctx.current_project.arcs = [{"arc_no": 1, "ep_start": 1, "ep_end": 10}]

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._preflight_validate_blueprint = MagicMock(
            return_value={"patched_blueprint": {"scene_breakdown": {"a": 2}}, "advisory": "watch pacing"}
        )

        result = orch._prepare_current_episode_inputs(next_ep=3)

        assert isinstance(result, _EpisodeLoopInputs)
        assert result.blueprint == {"scene_breakdown": {"a": 2}}
        assert result.arc_data == {"arc_no": 1, "ep_start": 1, "ep_end": 10}
        assert result.preflight_advisory == "watch pacing"

    def test_build_blueprint_preflight_request_applies_pins_and_formats_prompt(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _BlueprintPreflightRequest

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.db.get_manuscript.return_value = {"content": "prev manuscript"}
        ctx.world_state = MagicMock()
        ctx.world_state.get_summary.return_value = "world {state}"
        ctx.fact_ledger = MagicMock()
        ctx.fact_ledger.get_canonical_summary.return_value = "facts {ledger}"

        orch = Stage4Orchestrator(mock_app, context=ctx)
        apply_pins = MagicMock(return_value={"changes": ["pin-a"], "blueprint": {"scene_breakdown": {"a": 1}}})
        extract_tactical = MagicMock(return_value="tactical {note}")

        result = orch._build_blueprint_preflight_request(
            blueprint={"scene_breakdown": {"a": 0}},
            arc_data={"tactical_doc": "doc", "episode_details": {"beats": []}},
            ep_num=4,
            prompt_template="WS={world_state_summary}\nFL={fact_ledger_summary}\nARC={arc_tactical_excerpt}\nEP={ep_num}\nBP={blueprint_json}",
            apply_continuity_pins_fn=apply_pins,
            extract_episode_tactical_fn=extract_tactical,
        )

        assert isinstance(result, _BlueprintPreflightRequest)
        assert result.patched_blueprint["_continuity_pins"] == ["pin-a"]
        assert "world {{state}}" in result.prompt
        assert "facts {{ledger}}" in result.prompt
        assert "tactical {{note}}" in result.prompt
        apply_pins.assert_called_once_with(
            {"scene_breakdown": {"a": 0}},
            previous_published_text="prev manuscript",
            arc_tactical_text="tactical {note}",
        )

    def test_resolve_blueprint_preflight_result_demotes_false_positive_and_emits_advisory(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._log_escalation_event = MagicMock()

        result = orch._resolve_blueprint_preflight_result(
            ep_num=4,
            result={
                "passed": False,
                "summary": "summary",
                "issues": [
                    {"severity": "high", "category": "출처 불분명", "description": "출처가 불분명한 근거"},
                    {"severity": "high", "category": "사망 NPC", "description": "deceased NPC acts in scene"},
                ],
            },
            patched_blueprint={"scene_breakdown": {"a": 1}},
        )

        assert result["passed"] is True
        assert result["issues"][0]["severity"] == "low"
        assert result["issues"][1]["severity"] == "high"
        assert "advisory" in result
        orch._log_escalation_event.assert_called_once_with(4, "TF49b_PREFLIGHT", 2, success=True)
        assert ctx.ui.log.call_count >= 2

    def test_prepare_interview_loop_runtime_builds_anchor_and_budget(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _InterviewLoopRuntime, _SessionConfig

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.get_latest_episode_number = MagicMock(return_value=2)
        ctx.world_state = MagicMock()
        ctx.world_state.get_world_laws.return_value = []

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._register_bible_world_laws = MagicMock()
        session = _SessionConfig(
            chief_writer=MagicMock(),
            manuscript_validator=MagicMock(),
            consistency_validator=MagicMock(),
            blocking_validator=MagicMock(),
            continuity_validator=MagicMock(),
            s4_genre_type="wuxia",
            story_context="story",
            style_guide="style",
            target_ep=None,
            output_dir=Path("/tmp/stage4"),
            v50_modules_available=True,
            total_planned_ep=10,
            reference_excerpt="ref",
        )

        with patch("modules.core.reference_anchor.ReferenceAnchor", return_value="anchor") as anchor_cls:
            result = orch._prepare_interview_loop_runtime(session)

        assert isinstance(result, _InterviewLoopRuntime)
        assert result.chief_writer is session.chief_writer
        assert result.max_loops == 13
        assert result.anchor_sys == "anchor"
        assert result.output_dir == Path("/tmp/stage4")
        assert result.v50_modules_available is True
        anchor_cls.assert_called_once_with(ctx.current_project)
        orch._register_bible_world_laws.assert_called_once()

    def test_run_episode_loop_iteration_chains_round_preparation_and_outcome(self, mock_app):
        from modules.core.stage4_orchestrator import (
            Stage4Orchestrator,
            _EpisodeLoopDisposition,
            _EpisodeLoopInputs,
            _InterviewLoopRuntime,
            _SessionConfig,
        )

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._prepare_current_episode_inputs = MagicMock(
            return_value=_EpisodeLoopInputs(
                blueprint={"scene_breakdown": {"a": 1}},
                arc_data={"arc_no": 1},
                preflight_advisory="watch pacing",
            )
        )
        round_ctx = MagicMock()
        outcome = MagicMock()
        disposition = _EpisodeLoopDisposition(should_break=True)
        orch._prepare_episode_round = MagicMock(return_value=round_ctx)
        orch._handle_round_outcome = MagicMock(return_value=outcome)
        orch._consume_episode_round_outcome = MagicMock(return_value=disposition)
        session = _SessionConfig(
            chief_writer=MagicMock(),
            manuscript_validator=MagicMock(),
            consistency_validator=MagicMock(),
            blocking_validator=MagicMock(),
            continuity_validator=MagicMock(),
            s4_genre_type="wuxia",
            story_context="story",
            style_guide="style",
            target_ep=None,
            output_dir=Path("/tmp/stage4"),
            v50_modules_available=True,
            total_planned_ep=10,
            reference_excerpt="ref",
        )
        runtime = _InterviewLoopRuntime(
            chief_writer=session.chief_writer,
            output_dir=session.output_dir,
            v50_modules_available=True,
            max_loops=10,
            anchor_sys="anchor",
        )

        result = orch._run_episode_loop_iteration(
            session=session,
            runtime=runtime,
            next_ep=5,
            skip_pause=True,
        )

        assert result == disposition
        orch._prepare_current_episode_inputs.assert_called_once_with(next_ep=5)
        orch._prepare_episode_round.assert_called_once()
        round_kwargs = orch._prepare_episode_round.call_args.kwargs
        assert round_kwargs["next_ep"] == 5
        assert round_kwargs["blueprint"] == {"scene_breakdown": {"a": 1}}
        assert round_kwargs["arc_data"] == {"arc_no": 1}
        assert round_kwargs["anchor_sys"] == "anchor"
        orch._handle_round_outcome.assert_called_once_with(round_ctx=round_ctx)
        orch._consume_episode_round_outcome.assert_called_once_with(
            outcome=outcome,
            next_ep=5,
            blueprint={"scene_breakdown": {"a": 1}},
            arc_data={"arc_no": 1},
            output_dir=Path("/tmp/stage4"),
            v50_modules_available=True,
            skip_pause=True,
        )

    def test_build_episode_prompt_bundle_delegates_context_builder_and_writer_supplements(self, mock_app):
        from modules.core.stage4_orchestrator import (
            Stage4Orchestrator,
            _EpisodePromptBundle,
            _WriterPromptSupplements,
        )

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.genre = {"name": "무협"}
        ctx.agents = {"writer": MagicMock()}
        ctx.pacing_analyzer = MagicMock()

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._context_builder = MagicMock()
        orch._context_builder.build_mandatory_context.return_value = {
            "mandatory_context": "mandatory",
            "anti_trope_prompt": "anti",
            "reference_anchor_prompt": "",
            "justification_prompt": "",
            "reflexion_prompt": "",
        }
        orch._build_writer_prompt_supplements = MagicMock(
            return_value=_WriterPromptSupplements(
                purism_prompt="purism",
                npc_equipment_summary="equip",
                effective_anti_trope="anti++",
                intro_dna="CYNICAL",
            )
        )

        result = orch._build_episode_prompt_bundle(
            next_ep=5,
            arc_data={"arc_no": 1},
            blueprint={"scene_breakdown": {}},
            arc_tactical="전술",
            prev_text="prev",
            prev_ending="ending",
            hud_report="HUD",
            anchor_sys=MagicMock(),
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        assert isinstance(result, _EpisodePromptBundle)
        assert result.genre_name == "무협"
        assert result.ctx_prompts["mandatory_context"] == "mandatory"
        assert result.prompt_supplements.purism_prompt == "purism"
        orch._context_builder.build_mandatory_context.assert_called_once()
        orch._build_writer_prompt_supplements.assert_called_once_with(anti_trope_prompt="anti")

    def test_build_episode_round_context_delegates_with_prompt_bundle_fields(self, mock_app):
        from modules.core.stage4_orchestrator import (
            Stage4Orchestrator,
            _EpisodePromptBundle,
            _RoundContext,
            _WriterPromptSupplements,
        )

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._context_builder = MagicMock()
        orch._context_builder.build_round_context.return_value = MagicMock(spec=_RoundContext)
        prompt_bundle = _EpisodePromptBundle(
            genre_name="무협",
            ctx_prompts={"mandatory_context": "mandatory", "anti_trope_prompt": "anti"},
            prompt_supplements=_WriterPromptSupplements(
                purism_prompt="purism",
                npc_equipment_summary="equip",
                effective_anti_trope="anti++",
                intro_dna="CYNICAL",
            ),
        )

        result = orch._build_episode_round_context(
            ep_ctx={"prev_text": "prev"},
            ctx_prompts={"mandatory_context": "mandatory", "anti_trope_prompt": "anti"},
            chief_writer=MagicMock(),
            manuscript_validator=MagicMock(),
            consistency_validator=MagicMock(),
            blocking_validator=MagicMock(),
            continuity_validator=MagicMock(),
            next_ep=5,
            blueprint={"scene_breakdown": {}},
            arc_data={"arc_no": 1},
            story_context="story",
            style_guide="style",
            reference_excerpt="ref",
            preflight_advisory="watch pacing",
            prompt_bundle=prompt_bundle,
        )

        assert isinstance(result, MagicMock)
        call_kwargs = orch._context_builder.build_round_context.call_args.kwargs
        assert call_kwargs["purism_prompt"] == "purism"
        assert call_kwargs["genre_name"] == "무협"
        assert call_kwargs["npc_equipment_summary"] == "equip"
        assert call_kwargs["effective_anti_trope"] == "anti++"
        assert call_kwargs["intro_dna"] == "CYNICAL"
        assert call_kwargs["mandatory_context"] == "mandatory"
        assert call_kwargs["preflight_advisory"] == "watch pacing"

    def test_prepare_episode_round_chains_context_prompt_budget_and_round_context(self, mock_app):
        from modules.core.stage4_orchestrator import (
            Stage4Orchestrator,
            _EpisodePromptBundle,
            _RoundContext,
            _WriterPromptSupplements,
        )

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project

        orch = Stage4Orchestrator(mock_app, context=ctx)
        orch._context_builder = MagicMock()
        orch._context_builder.prepare_episode_context.return_value = {
            "arc_pos": 2,
            "total_ep_in_arc": 10,
            "arc_tactical": "전술",
            "prev_text": "prev",
            "prev_ending": "ending",
            "prev_manuscripts_text": "",
            "episode_digest": "",
            "hud_report": "HUD",
            "current_inventory": [],
            "current_martial_arts": [],
            "dead_npcs": [],
            "item_acquisition_timeline": "",
            "chain_link_section": "",
            "world_state_summary": "",
        }
        prompt_bundle = _EpisodePromptBundle(
            genre_name="무협",
            ctx_prompts={"mandatory_context": "mandatory", "anti_trope_prompt": "anti"},
            prompt_supplements=_WriterPromptSupplements(
                purism_prompt="purism",
                npc_equipment_summary="equip",
                effective_anti_trope="anti++",
                intro_dna="CYNICAL",
            ),
        )
        orch._build_episode_prompt_bundle = MagicMock(return_value=prompt_bundle)
        orch._apply_mandatory_context_budget = MagicMock(return_value="trimmed mandatory")
        orch._build_episode_round_context = MagicMock(return_value=MagicMock(spec=_RoundContext))

        result = orch._prepare_episode_round(
            next_ep=5,
            arc_data={"arc_no": 1},
            blueprint={"scene_breakdown": {}},
            chief_writer=MagicMock(),
            manuscript_validator=MagicMock(),
            consistency_validator=MagicMock(),
            blocking_validator=MagicMock(),
            continuity_validator=MagicMock(),
            story_context="story",
            style_guide="style",
            reference_excerpt="ref",
            preflight_advisory="watch pacing",
            anchor_sys=MagicMock(),
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

        assert isinstance(result, MagicMock)
        orch._build_episode_prompt_bundle.assert_called_once_with(
            next_ep=5,
            arc_data={"arc_no": 1},
            blueprint={"scene_breakdown": {}},
            arc_tactical="전술",
            prev_text="prev",
            prev_ending="ending",
            hud_report="HUD",
            anchor_sys=ANY,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )
        orch._apply_mandatory_context_budget.assert_called_once_with("mandatory")
        call_kwargs = orch._build_episode_round_context.call_args.kwargs
        assert call_kwargs["ep_ctx"]["arc_pos"] == 2
        assert call_kwargs["ctx_prompts"]["mandatory_context"] == "trimmed mandatory"
        assert call_kwargs["prompt_bundle"] is prompt_bundle
        assert call_kwargs["preflight_advisory"] == "watch pacing"
        assert ctx.ui.log.call_count == 3

    def test_build_writer_prompt_supplements_combines_guard_diversity_and_bible_fields(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator, _WriterPromptSupplements

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.sys = mock_app.sys
        ctx.diversity_engine = MagicMock()
        ctx.diversity_engine.get_writer_injection.return_value = "diversity note"
        ctx.current_project.master_bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "노사부", "NPC_Martial_HUD": {"equipment": ["죽봉", "호리병"]}},
                    ]
                },
                "protagonist_config": {"personality": "CYNICAL"},
            }
        }
        ctx.sys.guard.get_v20_purism_prompt.return_value = "purism"
        ctx.sys.guard.get_retrieval_contract_prompt.return_value = "retrieval contract"

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._build_writer_prompt_supplements(anti_trope_prompt="anti")

        assert isinstance(result, _WriterPromptSupplements)
        assert result.purism_prompt == "purism\n\nretrieval contract"
        assert result.npc_equipment_summary == "- 노사부: ['죽봉', '호리병']"
        assert result.effective_anti_trope == "anti\n\ndiversity note"
        assert result.intro_dna == "CYNICAL"

    def test_build_writer_prompt_supplements_handles_guard_failure_and_missing_bible_fields(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        ctx = MagicMock()
        ctx.ui = MagicMock()
        ctx.ui.log = MagicMock()
        ctx.current_project = mock_app.current_project
        ctx.current_project.master_bible = {"MasterBible": {"AssetLibrary": {}, "protagonist_config": {}}}
        ctx.sys = mock_app.sys
        ctx.diversity_engine = None
        ctx.sys.guard.get_v20_purism_prompt.side_effect = RuntimeError("guard boom")

        orch = Stage4Orchestrator(mock_app, context=ctx)

        result = orch._build_writer_prompt_supplements(anti_trope_prompt="anti")

        assert result.purism_prompt == ""
        assert result.npc_equipment_summary == "NPC 장비 정보 없음"
        assert result.effective_anti_trope == "anti"
        assert result.intro_dna == ""
        ctx.ui.log.assert_called_once()

    def test_patch_threshold_imported(self):
        """_PATCH_REWRITE_THRESHOLD 모듈 상수 존재"""
        from modules.core.stage4_types import _PATCH_REWRITE_THRESHOLD

        assert _PATCH_REWRITE_THRESHOLD == PatchModeThresholds.REWRITE

    def test_init_with_mock_app(self, mock_app):
        """mock_app으로 초기화 성공"""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        orch = Stage4Orchestrator(mock_app)
        assert orch.app is mock_app

    def test_outcome_runtime_attached(self, mock_app):
        from modules.core.stage4_orchestrator import Stage4Orchestrator
        from modules.core.stage4_outcome_runtime import Stage4OutcomeRuntime

        orch = Stage4Orchestrator(mock_app)

        assert isinstance(orch.outcome_runtime, Stage4OutcomeRuntime)


# ══════════════════════════════════════════════════════════════
# Test: [Phase 3-QR] Quality Regression in _process_pass_result
# ══════════════════════════════════════════════════════════════


class TestQualityRegressionHook:
    """_process_pass_result 내 품질 회귀 감지 advisory hook 테스트."""

    @pytest.fixture
    def s4_orch_with_dashboard(self, mock_app):
        """Stage4Orchestrator with quality_dashboard in ctx."""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        orch = Stage4Orchestrator(mock_app)
        orch.ctx.quality_dashboard = MagicMock()
        orch.ctx.world_state = None
        orch.ctx.fact_ledger = None
        orch.ctx.memory = None
        orch.ctx.flush_audit_buffer = MagicMock()
        orch.ctx.perf_timer = MagicMock()
        orch.ctx.character_voice = None
        orch.ctx.foreshadow_tracker = None
        orch.ctx.failure_learner = None
        return orch

    @pytest.fixture
    def pass_result_kwargs(self, tmp_path):
        """_process_pass_result 호출용 기본 kwargs."""
        return {
            "next_ep": 5,
            "final_manuscript": "테스트 원고입니다. " * 300,
            "final_title": "테스트 에피소드",
            "final_state_updates": {},
            "blueprint": {"ep_number": 5},
            "arc_data": {"arc_no": 1, "state_changes": {}},
            "output_dir": tmp_path,
            "v50_modules_available": False,
        }

    def test_regression_detected_logs_warning(self, s4_orch_with_dashboard, pass_result_kwargs):
        """regression 감지 시 UI 경고 로그 출력."""
        orch = s4_orch_with_dashboard
        orch.ctx.quality_dashboard.detect_score_regression.return_value = {
            "is_regression": True,
            "severity": "regression",
            "delta": 25,
            "baseline_avg": 80.0,
            "recent_avg": 55.0,
            "reason": "직전 대비 25점 하락",
        }
        result = _process_pass_result_via_post_processor(orch, **pass_result_kwargs)
        assert result is True
        orch.ctx.quality_dashboard.detect_score_regression.assert_called_once_with(stage=4)
        # UI에 경고 메시지 출력 확인
        log_calls = [str(c) for c in orch.ctx.ui.log.call_args_list]
        assert any("품질 회귀" in c for c in log_calls)

    def test_warning_severity_logs_info(self, s4_orch_with_dashboard, pass_result_kwargs):
        """warning severity 시 정보성 로그 출력."""
        orch = s4_orch_with_dashboard
        orch.ctx.quality_dashboard.detect_score_regression.return_value = {
            "is_regression": False,
            "severity": "warning",
            "delta": 12,
            "baseline_avg": 80.0,
            "recent_avg": 68.0,
            "reason": "직전 대비 12점 하락",
        }
        result = _process_pass_result_via_post_processor(orch, **pass_result_kwargs)
        assert result is True
        log_calls = [str(c) for c in orch.ctx.ui.log.call_args_list]
        assert any("품질 경고" in c for c in log_calls)

    def test_dashboard_exception_non_propagating(self, s4_orch_with_dashboard, pass_result_kwargs):
        """dashboard 예외 시 비전파, _process_pass_result는 True 반환."""
        orch = s4_orch_with_dashboard
        orch.ctx.quality_dashboard.detect_score_regression.side_effect = RuntimeError("crash")
        result = _process_pass_result_via_post_processor(orch, **pass_result_kwargs)
        assert result is True  # 비전파: 정상 반환

    def test_no_dashboard_skips_silently(self, mock_app, pass_result_kwargs, tmp_path):
        """quality_dashboard=None이면 조용히 스킵."""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        orch = Stage4Orchestrator(mock_app)
        orch.ctx.quality_dashboard = None
        orch.ctx.world_state = None
        orch.ctx.fact_ledger = None
        orch.ctx.memory = None
        orch.ctx.flush_audit_buffer = MagicMock()
        orch.ctx.perf_timer = MagicMock()
        orch.ctx.character_voice = None
        orch.ctx.foreshadow_tracker = None
        orch.ctx.failure_learner = None
        result = _process_pass_result_via_post_processor(orch, **pass_result_kwargs)
        assert result is True  # 크래시 없이 정상 완료


# ══════════════════════════════════════════════════════════════
# [Phase 3-5C] NPC 과잉 등장 감지 테스트
# ══════════════════════════════════════════════════════════════


class TestNpcOverexposureDetection:
    """_detect_npc_overexposure() 순수 함수 단위 테스트."""

    def test_overexposure_detected(self):
        """임계값 초과 엑스트라 NPC → warning dict 반환."""
        from modules.core.stage4_orchestrator import _detect_npc_overexposure

        manuscript = "흑풍이 " * 20  # "흑풍" 20회
        result = _detect_npc_overexposure(manuscript, ["흑풍", "노사부"], max_mentions=15)
        assert result is not None
        assert "흑풍" in result["npcs"]
        assert result["max_count"] >= 20
        assert result["total"] >= 1
        assert "과잉 등장" in result["warning"]
        assert "excluded_core_npcs" in result

    def test_below_threshold_returns_none(self):
        """임계값 미만이면 None."""
        from modules.core.stage4_orchestrator import _detect_npc_overexposure

        manuscript = "흑풍이 등장했다. 노사부가 말했다."
        result = _detect_npc_overexposure(manuscript, ["흑풍", "노사부"], max_mentions=15)
        assert result is None

    def test_protagonist_excluded(self):
        """주인공 이름은 과잉 등장 대상에서 제외."""
        from modules.core.stage4_orchestrator import _detect_npc_overexposure

        manuscript = "이청풍이 " * 30  # 주인공 30회
        result = _detect_npc_overexposure(manuscript, ["이청풍", "흑풍"], protagonist_name="이청풍", max_mentions=5)
        assert result is None  # 주인공 제외 → 흑풍 0회 → None

    def test_default_threshold_applied(self):
        """max_mentions 미지정 시 기본값 15 적용."""
        from modules.core.stage4_orchestrator import _detect_npc_overexposure

        manuscript = "흑풍 " * 14  # 14회 → 기본 15 미만
        result = _detect_npc_overexposure(manuscript, ["흑풍"])
        assert result is None
        manuscript_over = "흑풍 " * 16  # 16회 → 기본 15 이상
        result2 = _detect_npc_overexposure(manuscript_over, ["흑풍"])
        assert result2 is not None

    # ── [정교화] core NPC 제외 + 이름 매칭 개선 ──

    def test_core_npc_keynpcs_excluded(self):
        """KeyNPCs에 포함된 핵심 NPC는 임계 초과여도 경고 제외."""
        from modules.core.stage4_orchestrator import _detect_npc_overexposure

        manuscript = "노사부가 " * 20 + "흑풍이 " * 20
        result = _detect_npc_overexposure(
            manuscript,
            ["노사부", "흑풍", "무명소졸"],
            core_npc_names=frozenset({"노사부", "흑풍"}),
            max_mentions=5,
        )
        assert result is None  # 둘 다 core → 엑스트라 0명 → None

    def test_core_npc_key_npcs_variant_excluded(self):
        """Key_NPCs 변형 키로 전달된 핵심 NPC도 동일하게 제외."""
        from modules.core.stage4_orchestrator import _detect_npc_overexposure

        manuscript = "노사부가 " * 20 + "무명소졸이 " * 3
        result = _detect_npc_overexposure(
            manuscript,
            ["노사부", "무명소졸"],
            core_npc_names=frozenset({"노사부"}),
            max_mentions=5,
        )
        # 노사부: core 제외, 무명소졸: 3회 < 5 → None
        assert result is None
        assert True  # core_npc_names에 노사부만 넣었으므로 흑풍은 candidate

    def test_extra_npc_triggers_warning(self):
        """core에 없는 엑스트라 NPC만 임계 초과 시 경고 발생."""
        from modules.core.stage4_orchestrator import _detect_npc_overexposure

        manuscript = "노사부가 " * 20 + "무명소졸이 " * 20
        result = _detect_npc_overexposure(
            manuscript,
            ["노사부", "무명소졸"],
            core_npc_names=frozenset({"노사부"}),
            max_mentions=5,
        )
        assert result is not None
        assert "무명소졸" in result["npcs"]
        assert "노사부" not in result["npcs"]  # core → 제외
        assert "노사부" in result["excluded_core_npcs"]

    def test_substring_dedup_longest_first(self):
        """'흑풍대인' 반복 시 '흑풍' 과다 카운트 방지 (longest-match-first 마스킹)."""
        from modules.core.stage4_orchestrator import _detect_npc_overexposure

        # "흑풍대인" 20회 + "흑풍" 단독 2회 → 흑풍 카운트는 2 (20이 아님)
        manuscript = "흑풍대인이 " * 20 + "흑풍이 나타났다. 흑풍은 강했다."
        result = _detect_npc_overexposure(
            manuscript,
            ["흑풍대인", "흑풍"],
            max_mentions=5,
        )
        assert result is not None
        # 흑풍대인: 20회 → 과잉
        assert "흑풍대인" in result["npcs"]
        # 흑풍: 마스킹 후 2회만 카운트 → 5 미만 → 경고 아님
        assert "흑풍" not in result["npcs"]

    def test_single_char_name_skipped(self):
        """1글자 NPC 이름은 min_name_length=2 기본값으로 skip."""
        from modules.core.stage4_orchestrator import _detect_npc_overexposure

        manuscript = "풍 " * 100  # 1글자 "풍" 100회
        result = _detect_npc_overexposure(manuscript, ["풍"], max_mentions=5)
        assert result is None  # 1글자 → skip

    def test_single_char_counted_when_min_length_1(self):
        """min_name_length=1이면 1글자도 카운트."""
        from modules.core.stage4_orchestrator import _detect_npc_overexposure

        manuscript = "풍 " * 100
        result = _detect_npc_overexposure(manuscript, ["풍"], max_mentions=5, min_name_length=1)
        assert result is not None
        assert "풍" in result["npcs"]


class TestNpcOverexposureHook:
    """Stage4 파이프라인 내 NPC 과잉 등장 hook 통합 테스트."""

    @pytest.fixture
    def s4_orch_with_npc(self, mock_app):
        """state_tracker.npc_registry + Bible KeyNPCs가 있는 Stage4Orchestrator."""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        orch = Stage4Orchestrator(mock_app)
        tracker = MagicMock()
        tracker.npc_registry = {
            "흑풍": {"status": "alive"},
            "노사부": {"status": "alive"},
            "무명소졸": {"status": "alive"},
        }
        orch.ctx.state_tracker = tracker
        orch.ctx.quality_dashboard = None
        orch.ctx.world_state = None
        orch.ctx.fact_ledger = None
        orch.ctx.memory = None
        orch.ctx.flush_audit_buffer = MagicMock()
        orch.ctx.perf_timer = MagicMock()
        orch.ctx.character_voice = None
        orch.ctx.foreshadow_tracker = None
        orch.ctx.failure_learner = None
        orch.ctx.get_protagonist_name = lambda: "이청풍"
        # Bible에 KeyNPCs로 노사부, 흑풍이 핵심 NPC
        orch.ctx.current_project.master_bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "노사부", "role": "조력자"},
                        {"name": "흑풍", "role": "적대자"},
                    ]
                }
            }
        }
        return orch

    def _make_kwargs(self, tmp_path, manuscript="테스트 원고"):
        return {
            "next_ep": 3,
            "final_manuscript": manuscript,
            "final_title": "시련의 날",
            "final_state_updates": {},
            "blueprint": {"ep_number": 3},
            "arc_data": {"arc_no": 1, "state_changes": {}},
            "output_dir": tmp_path,
            "v50_modules_available": False,
        }

    def test_overexposure_hook_logs_warning_extras_only(self, s4_orch_with_npc, tmp_path):
        """핵심 NPC(노사부·흑풍) 제외, 엑스트라(무명소졸) 과잉만 경고."""
        orch = s4_orch_with_npc
        # 노사부 30회(core), 무명소졸 20회(extra)
        ms = "노사부가 " * 30 + "무명소졸이 " * 20
        result = _process_pass_result_via_post_processor(orch, **self._make_kwargs(tmp_path, ms))
        assert result is True
        log_calls = [str(c) for c in orch.ctx.ui.log.call_args_list]
        assert any("과잉 등장" in c and "무명소졸" in c for c in log_calls)
        # 노사부는 경고 텍스트에 없어야 함
        warning_logs = [c for c in log_calls if "과잉 등장" in c]
        assert all("노사부" not in c for c in warning_logs)

    def test_hook_exception_non_propagating(self, s4_orch_with_npc, tmp_path):
        """state_tracker 예외 시 비전파, _process_pass_result는 True 반환."""
        orch = s4_orch_with_npc
        orch.ctx.state_tracker.npc_registry = MagicMock()
        orch.ctx.state_tracker.npc_registry.keys.side_effect = RuntimeError("crash")
        result = _process_pass_result_via_post_processor(orch, **self._make_kwargs(tmp_path))
        assert result is True  # 비전파: 정상 반환


# ══════════════════════════════════════════════════════════════
# [Phase 3-B] 크로스 에피소드 반복 감지 hook 테스트
# ══════════════════════════════════════════════════════════════


class TestCrossEpisodeRepetitionHook:
    """Stage4 _process_pass_result 내 크로스 반복 감지 hook."""

    @pytest.fixture
    def s4_orch_with_db(self, mock_app, tmp_path):
        from modules.core.db_manager import DBManager
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        orch = Stage4Orchestrator(mock_app)
        db = DBManager(tmp_path / "test.db")
        orch.ctx.current_project.db = db
        orch.ctx.state_tracker = None
        orch.ctx.quality_dashboard = None
        orch.ctx.world_state = None
        orch.ctx.fact_ledger = None
        orch.ctx.memory = None
        orch.ctx.flush_audit_buffer = MagicMock()
        orch.ctx.perf_timer = MagicMock()
        orch.ctx.character_voice = None
        orch.ctx.foreshadow_tracker = None
        orch.ctx.failure_learner = None
        orch.ctx.get_protagonist_name = lambda: "이청풍"
        yield orch
        db.close()

    def _make_kwargs(self, tmp_path, manuscript="테스트 원고", next_ep=3):
        return {
            "next_ep": next_ep,
            "final_manuscript": manuscript,
            "final_title": "시련의 날",
            "final_state_updates": {},
            "blueprint": {"ep_number": next_ep},
            "arc_data": {"arc_no": 1, "state_changes": {}},
            "output_dir": tmp_path,
            "v50_modules_available": False,
        }

    def test_cross_repetition_warning_logged(self, s4_orch_with_db, tmp_path, caplog):
        """이전 에피소드와 동일 문장 다수 → WARNING 로그."""
        orch = s4_orch_with_db
        shared = "이청풍은 검을 높이 들어 창공을 향해 검기를 뿜어냈다"
        sentences = [f"{shared} 변형{i}번째 문장이다." for i in range(5)]
        past_ms = ". ".join(sentences) + "."
        # ep1 핑거프린트 사전 저장
        from modules.core.repetition_guard import RepetitionGuard

        fps = RepetitionGuard.extract_sentence_fingerprints(past_ms, min_length=10)
        orch.ctx.current_project.db.store_sentence_hashes(1, fps)
        # ep2에서 동일 원고 → 반복 감지
        import logging

        with caplog.at_level(logging.WARNING):
            result = _process_pass_result_via_post_processor(orch, **self._make_kwargs(tmp_path, past_ms, next_ep=2))
        assert result is True
        assert any("크로스 에피소드 반복" in r.message for r in caplog.records)

    def test_cross_repetition_no_warning_below_threshold(self, s4_orch_with_db, tmp_path, caplog):
        """반복 문장이 임계값 미만이면 WARNING 없음."""
        orch = s4_orch_with_db
        # ep1: 고유 문장
        orch.ctx.current_project.db.store_sentence_hashes(1, [("unique_hash_1", "고유 문장 1")])
        # ep2: 완전히 다른 원고
        ms = "완전히 새로운 문장으로 구성된 원고입니다. 이전 에피소드와 겹치는 부분이 없습니다."
        import logging

        with caplog.at_level(logging.WARNING):
            result = _process_pass_result_via_post_processor(orch, **self._make_kwargs(tmp_path, ms, next_ep=2))
        assert result is True
        assert not any("크로스 에피소드 반복" in r.message for r in caplog.records)

    def test_cross_repetition_db_exception_non_propagating(self, s4_orch_with_db, tmp_path):
        """DB 예외 시 비전파."""
        orch = s4_orch_with_db
        mock_db = MagicMock()
        mock_db.find_repeated_sentence_hashes.side_effect = RuntimeError("DB crash")
        orch.ctx.current_project.db = mock_db
        result = _process_pass_result_via_post_processor(
            orch,
            **self._make_kwargs(tmp_path, "정상 원고 내용입니다. " * 20, next_ep=2),
        )
        assert result is True
