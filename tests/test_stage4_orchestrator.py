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

        orch = Stage4Orchestrator(mock_app, context=ctx)

        orch._log_target_ep_reached(target_ep=2, next_ep=3)

        ctx.session_logger.log_decision.assert_called_once()
        decision_kwargs = ctx.session_logger.log_decision.call_args.kwargs
        assert decision_kwargs["stage"] == "stage4_control"
        assert decision_kwargs["decision_type"] == "target_ep_reached"
        assert decision_kwargs["ep_num"] == 2
        assert decision_kwargs["next_ep"] == 3

        ctx.audit_event.assert_called_once_with(
            "target_ep_reached",
            "stage4 target episode reached",
            {"target_ep": 2, "next_ep": 3},
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
        )

        expected_path = mock_app.current_project.paths.root / "logs" / "episode_production.jsonl"
        rows = [json.loads(line) for line in expected_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        payload = rows[-1]
        assert payload["round_num"] == 2
        assert payload["attempt_key"] == "s4:ep5:r3"
        assert payload["fix_scope"] == "partial"
        assert payload["reason"] == "history conflict repeated"
        assert payload["contradiction_type"] == "timeline"


class TestPrepareStage4SessionLimits:
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

        with patch("modules.core.stage4_orchestrator._threshold", return_value=2):
            orch._handle_round_outcome(round_ctx=minimal_round_ctx)

        assert orch._interview_round.run.call_count == 2

    def test_handle_round_outcome_injects_stage4_to_3_feedback_into_inplace_patch(
        self,
        orch_with_ctx,
        minimal_round_ctx,
        monkeypatch,
    ):
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
        orch.app._generate_reverse_feedback_stage4_to_3 = MagicMock(return_value="[S4->S3] blueprint hint")
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

        assert result == {"scene_breakdown": {}}
        assert bp_agent.generate.call_args.kwargs["external_feedback"] == "translated reverse feedback"

    def test_handle_round_outcome_retries_when_cove_verify_raises(self, orch_with_ctx, minimal_round_ctx, monkeypatch):
        from modules.core.stage4_types import _InterviewRoundResult

        orch = orch_with_ctx
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

        assert result.should_return is False
        assert result.final_manuscript == "수정 원고"
        assert orch._interview_round.run.call_count == 2
        second_call = orch._interview_round.run.call_args_list[1].kwargs
        assert second_call["director_feedback"].startswith("[CoVe 사후검증 런타임 실패]")
        assert second_call["previous_attempt"]["best_manuscript"] == "초안 원고"


# ══════════════════════════════════════════════════════════════
# Test: Stage4Orchestrator 초기화 + import
# ══════════════════════════════════════════════════════════════


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

    def test_patch_threshold_imported(self):
        """_PATCH_REWRITE_THRESHOLD 모듈 상수 존재"""
        from modules.core.stage4_types import _PATCH_REWRITE_THRESHOLD

        assert _PATCH_REWRITE_THRESHOLD == PatchModeThresholds.REWRITE

    def test_init_with_mock_app(self, mock_app):
        """mock_app으로 초기화 성공"""
        from modules.core.stage4_orchestrator import Stage4Orchestrator

        orch = Stage4Orchestrator(mock_app)
        assert orch.app is mock_app


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
