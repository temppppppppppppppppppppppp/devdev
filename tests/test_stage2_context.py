"""[Phase 4C-3] Stage2Context + Stage2Orchestrator DI 테스트"""

from unittest.mock import MagicMock

import pytest

from modules.core.stage2_context import Stage2Context
from modules.core.stage2_orchestrator import Stage2Orchestrator

# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def mock_deps():
    """필수 5종 의존 모의 객체"""
    return {
        "ui": MagicMock(),
        "current_project": MagicMock(),
        "agents": {"analyst": MagicMock(), "director": MagicMock()},
        "sys": MagicMock(),
        "state_tracker": MagicMock(),
    }


@pytest.fixture
def ctx(mock_deps):
    return Stage2Context(**mock_deps)


@pytest.fixture
def app_mock(mock_deps):
    """SovereignApp 모의 객체"""
    app = MagicMock()
    app.ui = mock_deps["ui"]
    app.current_project = mock_deps["current_project"]
    app.agents = mock_deps["agents"]
    app.sys = mock_deps["sys"]
    app.state_tracker = mock_deps["state_tracker"]
    app.world_state = MagicMock()
    return app


# ── Stage2Context 테스트 ─────────────────────────────────────


class TestStage2Context:
    def test_stores_required_attrs(self, ctx, mock_deps):
        """필수 5종 속성이 정확히 저장됨"""
        assert ctx.ui is mock_deps["ui"]
        assert ctx.current_project is mock_deps["current_project"]
        assert ctx.agents is mock_deps["agents"]
        assert ctx.sys is mock_deps["sys"]
        assert ctx.state_tracker is mock_deps["state_tracker"]

    def test_from_app_extracts_required_attrs(self, app_mock):
        """from_app 팩토리가 app에서 필수 5종 추출"""
        ctx = Stage2Context.from_app(app_mock)
        assert ctx.ui is app_mock.ui
        assert ctx.current_project is app_mock.current_project
        assert ctx.agents is app_mock.agents
        assert ctx.sys is app_mock.sys
        assert ctx.state_tracker is app_mock.state_tracker
        assert ctx.world_state is app_mock.world_state

    def test_optional_attrs_none_allowed(self, mock_deps):
        """확장 속성 미전달 시 None/False 기본값"""
        ctx = Stage2Context(**mock_deps)
        assert ctx.selected_genre is None
        assert ctx.preset_registry is None
        assert ctx.perf_timer is None
        assert ctx.semantic_plot_guard is None
        assert ctx.failure_learner is None
        assert ctx.memory is None
        assert ctx.world_state is None
        assert ctx.context_advisor is None
        assert ctx.stage2_optimizer is None
        assert ctx.arc_draft_validator is None
        assert ctx.arc_corrector is None
        assert ctx.constraint_compiler is None
        assert ctx.stage_rejection_history is None
        assert ctx.pass_rate_monitor is None
        assert ctx.quality_dashboard is None
        assert ctx.quality_amplifier is None
        assert ctx.agent_intelligence is None
        assert ctx.constitutional_checker is None
        assert ctx.self_reflector is None
        assert ctx.use_arc_corrector is False

    def test_slots_prevent_extra_attrs(self, ctx):
        """__slots__로 추가 속성 차단"""
        with pytest.raises(AttributeError):
            ctx.extra_attr = "should_fail"

    def test_callbacks_from_app_extracted(self, app_mock):
        """from_app가 콜백을 바운드 메서드로 채움"""
        app_mock._audit_event = MagicMock()
        app_mock._get_int_input = MagicMock()
        app_mock._safe_commit_async = MagicMock()
        app_mock._validate_arc_data_fields = MagicMock()
        app_mock._build_focused_context = MagicMock()
        app_mock._generate_arc_context_v60 = MagicMock()
        app_mock._generate_reverse_feedback_stage4_to_2 = MagicMock()

        ctx = Stage2Context.from_app(app_mock)
        assert ctx.audit_event is app_mock._audit_event
        assert ctx.get_int_input is app_mock._get_int_input
        assert ctx.safe_commit_async is app_mock._safe_commit_async
        assert ctx.validate_arc_data_fields is app_mock._validate_arc_data_fields
        assert ctx.build_focused_context is app_mock._build_focused_context
        assert ctx.generate_arc_context_v60 is app_mock._generate_arc_context_v60
        assert ctx.generate_reverse_feedback_stage4_to_2 is app_mock._generate_reverse_feedback_stage4_to_2

    def test_callbacks_default_none(self, ctx):
        """콜백 미전달 시 기본값 None"""
        assert ctx.audit_event is None
        assert ctx.get_int_input is None
        assert ctx.safe_commit_async is None
        assert ctx.validate_arc_data_fields is None
        assert ctx.build_focused_context is None
        assert ctx.generate_arc_context_v60 is None
        assert ctx.generate_reverse_feedback_stage4_to_2 is None
        assert ctx.retry_feedback_missing_callbacks == {
            "required": [],
            "optional_with_fallback": [],
            "observability_only": [],
        }

    def test_context_advisor_stored_when_injected(self, mock_deps):
        advisor = MagicMock()
        ctx = Stage2Context(**mock_deps, context_advisor=advisor)
        assert ctx.context_advisor is advisor

    def test_from_app_extracts_context_advisor(self, app_mock):
        advisor = MagicMock()
        app_mock.context_advisor = advisor
        ctx = Stage2Context.from_app(app_mock)
        assert ctx.context_advisor is advisor

    def test_from_app_missing_callbacks_none(self):
        """콜백 미구현 app에서도 from_app 정상 (None)"""
        app = MagicMock(spec=[])
        app.ui = MagicMock()
        app.current_project = MagicMock()
        app.agents = {}
        app.sys = MagicMock()
        ctx = Stage2Context.from_app(app)
        assert ctx.audit_event is None
        assert ctx.get_int_input is None
        assert ctx.state_tracker is None
        assert ctx.world_state is None
        assert ctx.context_advisor is None
        assert ctx.retry_feedback_missing_callbacks["required"] == ["analyze_rejection_pattern_v60"]
        assert "generate_arc_context_v60" in ctx.retry_feedback_missing_callbacks["optional_with_fallback"]

    def test_from_app_falls_back_to_feedback_and_prompt_builders(self):
        app = type("App", (), {})()
        app.ui = MagicMock()
        app.current_project = MagicMock()
        app.agents = {}
        app.sys = MagicMock()
        app._feedback_system = MagicMock()
        app._prompt_builder = MagicMock()
        app._feedback_system.generate_reverse_feedback_stage3_to_2 = MagicMock()
        app._feedback_system.build_minimal_arc_context = MagicMock()
        app._feedback_system.get_adaptive_feedback_intensity = MagicMock()
        app._prompt_builder.generate_arc_context_v60 = MagicMock()

        ctx = Stage2Context.from_app(app)

        assert ctx.generate_reverse_feedback_stage3_to_2 is app._feedback_system.generate_reverse_feedback_stage3_to_2
        assert ctx.build_minimal_arc_context is app._feedback_system.build_minimal_arc_context
        assert ctx.get_adaptive_feedback_intensity is app._feedback_system.get_adaptive_feedback_intensity
        assert ctx.generate_arc_context_v60 is app._prompt_builder.generate_arc_context_v60
        assert ctx.retry_feedback_missing_callbacks["required"] == ["analyze_rejection_pattern_v60"]

    def test_retry_feedback_contract_tracks_expected_tiers(self, ctx):
        assert ctx.retry_feedback_contract["analyze_rejection_pattern_v60"] == "required"
        assert ctx.retry_feedback_contract["generate_reverse_feedback_stage3_to_2"] == "optional_with_fallback"
        assert ctx.retry_feedback_contract["generate_arc_context_v60"] == "optional_with_fallback"

    def test_keyword_only_init(self):
        """위치 인자로 생성 시 TypeError"""
        with pytest.raises(TypeError):
            Stage2Context(1, 2, 3, 4, 5)

    def test_from_app_binds_real_validation_callbacks(self, mock_deps):
        class RealApp:
            def __init__(self, deps):
                self.ui = deps["ui"]
                self.current_project = deps["current_project"]
                self.agents = deps["agents"]
                self.sys = deps["sys"]
                self.state_tracker = deps["state_tracker"]
                self.repair_calls = []
                self.mapping_calls = []
                self.integrity_calls = []

            def _validate_arc_data_fields(self, arc_data, arc_idx):
                self.repair_calls.append((arc_idx, arc_data.get("arc_no")))
                repaired = dict(arc_data)
                repaired["arc_no"] = arc_idx
                return repaired

            def _validate_arc_mapping(self, refined_arc, enriched_block, expected_arc_no, expected_ep_start):
                self.mapping_calls.append((expected_arc_no, expected_ep_start))
                return refined_arc

            def _validate_arc_integrity(self, arc_data):
                self.integrity_calls.append(arc_data.get("arc_no"))
                return True

        app = RealApp(mock_deps)

        ctx = Stage2Context.from_app(app)

        assert ctx.validate_arc_data_fields.__self__ is app
        assert ctx.validate_arc_mapping.__self__ is app
        assert ctx.validate_arc_integrity.__self__ is app
        assert ctx.validate_arc_data_fields({"arc_no": 99}, 3)["arc_no"] == 3
        assert ctx.validate_arc_mapping({"arc_no": 1}, {}, 1, 1)["arc_no"] == 1
        assert ctx.validate_arc_integrity({"arc_no": 3}) is True
        assert app.repair_calls == [(3, 99)]
        assert app.mapping_calls == [(1, 1)]
        assert app.integrity_calls == [3]


# ── Stage2Orchestrator ctx 테스트 ────────────────────────────


class TestStage2OrchestratorCtx:
    def test_ctx_none_by_default(self, app_mock):
        """초기 _ctx=None"""
        orch = Stage2Orchestrator(app=app_mock)
        assert orch._ctx is None

    def test_ctx_auto_builds_from_app(self, app_mock):
        """property 접근 시 app에서 자동 빌드"""
        orch = Stage2Orchestrator(app=app_mock)
        ctx = orch.ctx
        assert isinstance(ctx, Stage2Context)
        assert ctx.ui is app_mock.ui
        assert ctx.current_project is app_mock.current_project

    def test_ctx_injected_at_init(self, app_mock, ctx):
        """context= 키워드로 주입"""
        orch = Stage2Orchestrator(app=app_mock, context=ctx)
        assert orch.ctx is ctx

    def test_ctx_setter_replaces_context(self, app_mock, ctx):
        """ctx setter로 교체"""
        orch = Stage2Orchestrator(app=app_mock)
        orch.ctx = ctx
        assert orch.ctx is ctx
        assert orch._ctx is ctx

    def test_ctx_auto_build_cached(self, app_mock):
        """자동 빌드 후 동일 객체 재사용"""
        orch = Stage2Orchestrator(app=app_mock)
        ctx1 = orch.ctx
        ctx2 = orch.ctx
        assert ctx1 is ctx2

    def test_backward_compat_app_still_works(self, app_mock):
        """self.app 접근 유지 (레거시 호환)"""
        orch = Stage2Orchestrator(app=app_mock)
        assert orch.app is app_mock

    def test_rejection_pattern_helper_falls_back_to_diagnostic(self, app_mock):
        orch = Stage2Orchestrator(app=app_mock)
        orch.ctx.audit_event = MagicMock()
        orch.ctx.analyze_rejection_pattern_v60 = None

        message = orch._compose_rejection_pattern_feedback(
            [
                {"stage": 2, "arc_no": 3, "reason": "반복 전개", "specific_issue": "후반부 이벤트 부족"},
                {"stage": 2, "arc_no": 3, "reason": "반복 전개"},
            ],
            3,
        )

        assert "callback_missing" in message
        assert "반복 전개" in message
        assert "후반부 이벤트 부족" in message
