"""[Phase 4C-2a/2b/2c] Stage4Context + Stage4Orchestrator DI 테스트"""

from unittest.mock import MagicMock

import pytest

from modules.core.stage4_context import Stage4Context
from modules.core.stage4_orchestrator import Stage4Orchestrator

# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def mock_deps():
    """파일럿 5종 의존 모의 객체"""
    return {
        "ui": MagicMock(),
        "current_project": MagicMock(),
        "agents": {"director": MagicMock(), "writer": MagicMock()},
        "sys": MagicMock(),
        "state_tracker": MagicMock(),
    }


@pytest.fixture
def ctx(mock_deps):
    return Stage4Context(**mock_deps)


@pytest.fixture
def app_mock(mock_deps):
    """SovereignApp 모의 객체"""
    app = MagicMock()
    app.ui = mock_deps["ui"]
    app.current_project = mock_deps["current_project"]
    app.agents = mock_deps["agents"]
    app.sys = mock_deps["sys"]
    app.state_tracker = mock_deps["state_tracker"]
    app.context_advisor = None
    return app


# ── Stage4Context 테스트 ─────────────────────────────────────


class TestStage4Context:
    def test_stores_all_attributes(self, ctx, mock_deps):
        """5종 속성이 정확히 저장됨"""
        assert ctx.ui is mock_deps["ui"]
        assert ctx.current_project is mock_deps["current_project"]
        assert ctx.agents is mock_deps["agents"]
        assert ctx.sys is mock_deps["sys"]
        assert ctx.state_tracker is mock_deps["state_tracker"]

    def test_from_app_factory(self, app_mock):
        """from_app 팩토리가 app에서 5종 추출"""
        ctx = Stage4Context.from_app(app_mock)
        assert ctx.ui is app_mock.ui
        assert ctx.current_project is app_mock.current_project
        assert ctx.agents is app_mock.agents
        assert ctx.sys is app_mock.sys
        assert ctx.state_tracker is app_mock.state_tracker

    def test_from_app_none_tracker(self):
        """state_tracker 없는 app에서도 from_app 정상 (None)"""
        app = MagicMock(spec=[])  # state_tracker attr 없음
        app.ui = MagicMock()
        app.current_project = MagicMock()
        app.agents = {}
        app.sys = MagicMock()
        ctx = Stage4Context.from_app(app)
        assert ctx.state_tracker is None

    def test_context_advisor_default_none(self, ctx):
        assert ctx.context_advisor is None

    def test_budget_meta_default_empty_dict(self, ctx):
        assert ctx._stage4_context_budget_meta == {}

    def test_context_advisor_stored(self, mock_deps):
        advisor = MagicMock()
        with_advisor = Stage4Context(**mock_deps, context_advisor=advisor)
        assert with_advisor.context_advisor is advisor

    def test_from_app_extracts_context_advisor(self, app_mock):
        advisor = MagicMock()
        app_mock.context_advisor = advisor
        extracted = Stage4Context.from_app(app_mock)
        assert extracted.context_advisor is advisor

    def test_slots_prevent_extra_attrs(self, ctx):
        """__slots__로 추가 속성 차단"""
        with pytest.raises(AttributeError):
            ctx.extra_attr = "should_fail"

    def test_keyword_only_init(self):
        """위치 인자로 생성 시 TypeError"""
        with pytest.raises(TypeError):
            Stage4Context(1, 2, 3, 4, 5)

    def test_conditional_modules_default_empty(self, ctx):
        """[S-13] conditional_modules 기본값 빈 dict"""
        assert ctx.conditional_modules == {}
        assert ctx.get_module("non_existent") is None

    def test_conditional_modules_stored(self, mock_deps):
        """[S-13] conditional_modules 전달 시 정확히 저장 및 get_module"""
        mock_tot = MagicMock()
        cm = {"tree_of_thoughts": mock_tot}
        ctx = Stage4Context(**mock_deps, conditional_modules=cm)
        assert ctx.get_module("tree_of_thoughts") is mock_tot
        assert ctx.get_module("missing") is None

    def test_from_app_extracts_conditional_modules(self, app_mock):
        """[S-13] from_app가 조건부 모듈 8종을 dict로 추출"""
        mock_cv = MagicMock()
        mock_asp = MagicMock()
        app_mock.cross_verifier = mock_cv
        app_mock.adversarial_self_play = mock_asp
        ctx = Stage4Context.from_app(app_mock)
        assert ctx.get_module("cross_verifier") is mock_cv
        assert ctx.get_module("adversarial_self_play") is mock_asp

    def test_pass_rate_monitor_default_none(self, ctx):
        """pass_rate_monitor 기본값 None"""
        assert ctx.pass_rate_monitor is None

    def test_pass_rate_monitor_stored(self, mock_deps):
        """pass_rate_monitor 전달 시 정확히 저장"""
        monitor = MagicMock()
        ctx = Stage4Context(**mock_deps, pass_rate_monitor=monitor)
        assert ctx.pass_rate_monitor is monitor

    def test_from_app_extracts_pass_rate_monitor(self, app_mock):
        """from_app가 pass_rate_monitor를 추출"""
        app_mock.pass_rate_monitor = MagicMock()
        ctx = Stage4Context.from_app(app_mock)
        assert ctx.pass_rate_monitor is app_mock.pass_rate_monitor

    def test_callbacks_default_none(self, ctx):
        """[4C-2c] 콜백 기본값 None"""
        assert ctx.get_int_input is None
        assert ctx.build_item_acquisition_timeline is None
        assert ctx.load_narrative_summaries is None
        assert ctx.get_protagonist_name is None
        assert ctx.extract_npc_profiles is None
        assert ctx.generate_narrative_summary is None
        assert ctx.generate_reverse_feedback_stage4_to_3 is None
        assert ctx.generate_writer_guidance_v60_8 is None
        assert ctx.enrich_director_result is None
        assert ctx.audit_event is None
        assert ctx.write_audit_summary is None
        assert ctx.flush_audit_buffer is None
        assert ctx.safe_commit is None

    def test_callbacks_stored(self, mock_deps):
        """[4C-2c] 콜백 전달 시 정확히 저장"""
        cb_flush = MagicMock()
        cb_commit = MagicMock()
        cb_audit = MagicMock()
        cb_summary = MagicMock()
        cb_extract_npc_profiles = MagicMock()
        ctx = Stage4Context(
            **mock_deps,
            extract_npc_profiles=cb_extract_npc_profiles,
            audit_event=cb_audit,
            write_audit_summary=cb_summary,
            flush_audit_buffer=cb_flush,
            safe_commit=cb_commit,
        )
        assert ctx.extract_npc_profiles is cb_extract_npc_profiles
        assert ctx.audit_event is cb_audit
        assert ctx.write_audit_summary is cb_summary
        assert ctx.flush_audit_buffer is cb_flush
        assert ctx.safe_commit is cb_commit

    def test_from_app_extracts_callbacks(self, app_mock):
        """[4C-2c] from_app가 콜백 surface를 바운드 메서드로 채움"""
        app_mock._get_int_input = MagicMock()
        app_mock._build_item_acquisition_timeline = MagicMock()
        app_mock._load_narrative_summaries = MagicMock()
        app_mock._get_protagonist_name = MagicMock()
        app_mock._extract_npc_profiles = MagicMock()
        app_mock._generate_narrative_summary = MagicMock()
        app_mock._generate_reverse_feedback_stage4_to_3 = MagicMock()
        app_mock._generate_writer_guidance_v60_8 = MagicMock()
        app_mock._enrich_director_result = MagicMock()
        app_mock._audit_event = MagicMock()
        app_mock._write_audit_summary = MagicMock()
        app_mock._flush_audit_buffer = MagicMock()
        app_mock._safe_commit = MagicMock()

        ctx = Stage4Context.from_app(app_mock)
        assert ctx.get_int_input is app_mock._get_int_input
        assert ctx.build_item_acquisition_timeline is app_mock._build_item_acquisition_timeline
        assert ctx.load_narrative_summaries is app_mock._load_narrative_summaries
        assert ctx.get_protagonist_name is app_mock._get_protagonist_name
        assert ctx.extract_npc_profiles is app_mock._extract_npc_profiles
        assert ctx.generate_narrative_summary is app_mock._generate_narrative_summary
        assert ctx.generate_reverse_feedback_stage4_to_3 is app_mock._generate_reverse_feedback_stage4_to_3
        assert ctx.generate_writer_guidance_v60_8 is app_mock._generate_writer_guidance_v60_8
        assert ctx.enrich_director_result is app_mock._enrich_director_result
        assert ctx.audit_event is app_mock._audit_event
        assert ctx.write_audit_summary is app_mock._write_audit_summary
        assert ctx.flush_audit_buffer is app_mock._flush_audit_buffer
        assert ctx.safe_commit is app_mock._safe_commit

    def test_from_app_missing_callbacks_none(self):
        """[4C-2c] 콜백 미구현 app에서도 from_app 정상 (None)"""
        app = MagicMock(spec=[])
        app.ui = MagicMock()
        app.current_project = MagicMock()
        app.agents = {}
        app.sys = MagicMock()
        ctx = Stage4Context.from_app(app)
        assert ctx.get_int_input is None
        assert ctx.generate_reverse_feedback_stage4_to_3 is None
        assert ctx.generate_writer_guidance_v60_8 is None
        assert ctx.enrich_director_result is None
        assert ctx.extract_npc_profiles is None
        assert ctx.audit_event is None
        assert ctx.write_audit_summary is None
        assert ctx.flush_audit_buffer is None
        assert ctx.safe_commit is None

    def test_from_app_falls_back_to_feedback_system_reverse_feedback(self, app_mock):
        feedback_system = MagicMock()
        feedback_system.generate_reverse_feedback_stage4_to_3 = MagicMock()
        app_mock._feedback_system = feedback_system

        ctx = Stage4Context.from_app(app_mock)

        assert ctx.generate_reverse_feedback_stage4_to_3 is feedback_system.generate_reverse_feedback_stage4_to_3

    def test_from_app_binds_real_item_timeline_method(self, mock_deps):
        class RealApp:
            def __init__(self, deps):
                self.ui = deps["ui"]
                self.current_project = deps["current_project"]
                self.agents = deps["agents"]
                self.sys = deps["sys"]
                self.state_tracker = deps["state_tracker"]
                self.timeline_calls = []

            def _build_item_acquisition_timeline(self, up_to_ep):
                self.timeline_calls.append(up_to_ep)
                return f"timeline:{up_to_ep}"

        app = RealApp(mock_deps)

        ctx = Stage4Context.from_app(app)

        assert ctx.build_item_acquisition_timeline.__self__ is app
        assert ctx.build_item_acquisition_timeline(4) == "timeline:4"
        assert app.timeline_calls == [4]

    def test_from_app_binds_real_audit_callbacks(self, mock_deps):
        class RealApp:
            def __init__(self, deps):
                self.ui = deps["ui"]
                self.current_project = deps["current_project"]
                self.agents = deps["agents"]
                self.sys = deps["sys"]
                self.state_tracker = deps["state_tracker"]
                self.audit_calls = []
                self.summary_calls = []

            def _audit_event(self, event_type, message, data=None):
                self.audit_calls.append((event_type, message, data))

            def _write_audit_summary(self, tag="snapshot"):
                self.summary_calls.append(tag)

        app = RealApp(mock_deps)

        ctx = Stage4Context.from_app(app)

        assert ctx.audit_event.__self__ is app
        assert ctx.write_audit_summary.__self__ is app
        ctx.audit_event("stage4_complete", "done", {"target_ep": 4})
        ctx.write_audit_summary("stage4_complete")
        assert app.audit_calls == [("stage4_complete", "done", {"target_ep": 4})]
        assert app.summary_calls == ["stage4_complete"]

    def test_from_app_binds_real_extract_npc_profiles_callback(self, mock_deps):
        class RealApp:
            def __init__(self, deps):
                self.ui = deps["ui"]
                self.current_project = deps["current_project"]
                self.agents = deps["agents"]
                self.sys = deps["sys"]
                self.state_tracker = deps["state_tracker"]
                self.extract_calls = []

            def _extract_npc_profiles(self, arc_data):
                self.extract_calls.append(arc_data)
                return {"장현석": {"name": "장현석", "role": "적대 세력 수장"}}

        app = RealApp(mock_deps)

        ctx = Stage4Context.from_app(app)

        assert ctx.extract_npc_profiles.__self__ is app
        assert ctx.extract_npc_profiles({"summary": "장현석 등장"}) == {
            "장현석": {"name": "장현석", "role": "적대 세력 수장"}
        }
        assert app.extract_calls == [{"summary": "장현석 등장"}]


# ── Stage4Orchestrator ctx 테스트 ────────────────────────────


class TestStage4OrchestratorCtx:
    def test_ctx_none_by_default(self, app_mock):
        """초기 _ctx=None"""
        orch = Stage4Orchestrator(app=app_mock)
        assert orch._ctx is None

    def test_ctx_auto_builds_from_app(self, app_mock):
        """property 접근 시 app에서 자동 빌드"""
        orch = Stage4Orchestrator(app=app_mock)
        ctx = orch.ctx
        assert isinstance(ctx, Stage4Context)
        assert ctx.ui is app_mock.ui
        assert ctx.current_project is app_mock.current_project

    def test_ctx_auto_build_cached(self, app_mock):
        """자동 빌드 후 동일 객체 재사용"""
        orch = Stage4Orchestrator(app=app_mock)
        ctx1 = orch.ctx
        ctx2 = orch.ctx
        assert ctx1 is ctx2

    def test_ctx_injected_at_init(self, app_mock, ctx):
        """context= 키워드로 주입"""
        orch = Stage4Orchestrator(app=app_mock, context=ctx)
        assert orch.ctx is ctx

    def test_ctx_setter(self, app_mock, ctx):
        """ctx setter로 교체"""
        orch = Stage4Orchestrator(app=app_mock)
        orch.ctx = ctx
        assert orch.ctx is ctx
        assert orch._ctx is ctx

    def test_helper_extract_chain_link_uses_ctx(self, app_mock, ctx):
        """_extract_chain_link가 ctx.agents 경유"""
        ctx.agents["director"]._escape_braces.return_value = "escaped"
        ctx.agents["director"].ask.return_value = '{"cliffhanger": "test"}'
        ctx.agents["director"]._extract_json_robust.return_value = {"cliffhanger": "test"}

        orch = Stage4Orchestrator(app=app_mock, context=ctx)
        result = orch._extract_chain_link(1, "x" * 300)  # 200자 이상 필요
        ctx.agents["director"].ask.assert_called_once()
        assert result.get("cliffhanger") == "test"

    def test_helper_load_chain_link_uses_ctx(self, app_mock, ctx):
        """_load_chain_link_section이 ctx.current_project 경유"""
        ctx.current_project.db.load_anchor.return_value = {
            "cliffhanger": "주인공이 위기에 처했다",
            "pending_actions": ["도주"],
        }
        orch = Stage4Orchestrator(app=app_mock, context=ctx)
        result = orch._load_chain_link_section(5)
        ctx.current_project.db.load_anchor.assert_called_once_with("chain_link_4")
        assert "주인공이 위기에 처했다" in result

    def test_helper_load_chain_link_no_data(self, app_mock, ctx):
        """chain_link 데이터 없으면 빈 문자열"""
        ctx.current_project.db.load_anchor.return_value = None
        orch = Stage4Orchestrator(app=app_mock, context=ctx)
        result = orch._load_chain_link_section(1)
        assert result == ""

    def test_callback_flush_via_ctx(self, app_mock, mock_deps):
        """[4C-2c] flush_audit_buffer 콜백이 ctx 경유 호출"""
        cb_flush = MagicMock()
        ctx = Stage4Context(**mock_deps, flush_audit_buffer=cb_flush)
        orch = Stage4Orchestrator(app=app_mock, context=ctx)
        orch.ctx.flush_audit_buffer()
        cb_flush.assert_called_once()

    def test_callback_safe_commit_via_ctx(self, app_mock, mock_deps):
        """[4C-2c] safe_commit 콜백이 ctx 경유 호출"""
        cb_commit = MagicMock()
        ctx = Stage4Context(**mock_deps, safe_commit=cb_commit)
        orch = Stage4Orchestrator(app=app_mock, context=ctx)
        orch.ctx.safe_commit()
        cb_commit.assert_called_once()

    def test_callback_get_int_input_via_ctx(self, app_mock, mock_deps):
        """[4C-2c] get_int_input 콜백이 ctx 경유 호출 및 반환값"""
        cb_input = MagicMock(return_value=3)
        ctx = Stage4Context(**mock_deps, get_int_input=cb_input)
        orch = Stage4Orchestrator(app=app_mock, context=ctx)
        result = orch.ctx.get_int_input("prompt", default=1, min_val=1, max_val=5)
        cb_input.assert_called_once_with("prompt", default=1, min_val=1, max_val=5)
        assert result == 3

    def test_backward_compat_app_still_works(self, app_mock):
        """self.app 접근 유지 (레거시 호환)"""
        orch = Stage4Orchestrator(app=app_mock)
        assert orch.app is app_mock
