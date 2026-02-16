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

    def test_slots_prevent_extra_attrs(self, ctx):
        """__slots__로 추가 속성 차단"""
        with pytest.raises(AttributeError):
            ctx.extra_attr = "should_fail"

    def test_keyword_only_init(self):
        """위치 인자로 생성 시 TypeError"""
        with pytest.raises(TypeError):
            Stage4Context(1, 2, 3, 4, 5)

    def test_callbacks_default_none(self, ctx):
        """[4C-2c] 콜백 7종 기본값 None"""
        assert ctx.get_int_input is None
        assert ctx.build_item_acquisition_timeline is None
        assert ctx.load_narrative_summaries is None
        assert ctx.get_protagonist_name is None
        assert ctx.generate_narrative_summary is None
        assert ctx.flush_audit_buffer is None
        assert ctx.safe_commit is None

    def test_callbacks_stored(self, mock_deps):
        """[4C-2c] 콜백 전달 시 정확히 저장"""
        cb_flush = MagicMock()
        cb_commit = MagicMock()
        ctx = Stage4Context(
            **mock_deps,
            flush_audit_buffer=cb_flush,
            safe_commit=cb_commit,
        )
        assert ctx.flush_audit_buffer is cb_flush
        assert ctx.safe_commit is cb_commit

    def test_from_app_extracts_callbacks(self, app_mock):
        """[4C-2c] from_app가 콜백 7종을 바운드 메서드로 채움"""
        app_mock._get_int_input = MagicMock()
        app_mock._build_item_acquisition_timeline = MagicMock()
        app_mock._load_narrative_summaries = MagicMock()
        app_mock._get_protagonist_name = MagicMock()
        app_mock._generate_narrative_summary = MagicMock()
        app_mock._flush_audit_buffer = MagicMock()
        app_mock._safe_commit = MagicMock()

        ctx = Stage4Context.from_app(app_mock)
        assert ctx.get_int_input is app_mock._get_int_input
        assert ctx.build_item_acquisition_timeline is app_mock._build_item_acquisition_timeline
        assert ctx.load_narrative_summaries is app_mock._load_narrative_summaries
        assert ctx.get_protagonist_name is app_mock._get_protagonist_name
        assert ctx.generate_narrative_summary is app_mock._generate_narrative_summary
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
        assert ctx.flush_audit_buffer is None
        assert ctx.safe_commit is None


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
