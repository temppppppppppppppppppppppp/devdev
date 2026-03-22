from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a
import modules.core.sovereign_bootstrap_runtime as bootstrap_runtime_module
from modules.core.sovereign_bootstrap_runtime import SovereignBootstrapRuntime


class _FakeLLMAgent:
    def __init__(self, context, client, model_tier=None, flash_ask=None):
        self.context = context
        self.client = client
        self.model_tier = model_tier
        self.flash_ask = flash_ask


class _FakeValidator:
    def __init__(self, genre=""):
        self.genre = genre


class _FakeCorrector:
    def __init__(self, context=None, client=None, model_tier=None):
        self.context = context
        self.client = client
        self.model_tier = model_tier


def _make_agent_catalog():
    return {
        "Analyst": _FakeLLMAgent,
        "ArcCorrector": _FakeCorrector,
        "ArcCritic": _FakeLLMAgent,
        "ArcDraftValidator": _FakeValidator,
        "ArcEnsembleGenerator": _FakeLLMAgent,
        "ConsensusValidator": _FakeLLMAgent,
        "ConstraintCompiler": _FakeValidator,
        "ContinuityInspector": _FakeLLMAgent,
        "Critic": _FakeLLMAgent,
        "Director": _FakeLLMAgent,
        "FourPhaseArcGenerator": _FakeLLMAgent,
        "Manager": _FakeLLMAgent,
        "PreflightChecker": _FakeLLMAgent,
        "StateExtractor": _FakeLLMAgent,
        "StateLockedArcGenerator": _FakeLLMAgent,
        "ThreePhaseBlueprintGenerator": _FakeLLMAgent,
        "Weaver": _FakeLLMAgent,
        "Writer": _FakeLLMAgent,
    }


def test_build_flash_analysis_callback_returns_none_when_flag_disabled(monkeypatch):
    app = SimpleNamespace(sys=SimpleNamespace(api_client=object()))
    monkeypatch.setattr(main_a, "_val_threshold", lambda *_args, **_kwargs: False)
    runtime = SovereignBootstrapRuntime(app)

    callback = runtime._build_flash_analysis_callback()

    assert callback is None


def test_build_flash_analysis_callback_routes_prompt(monkeypatch):
    calls = []
    app = SimpleNamespace(sys=SimpleNamespace(api_client="client"))
    monkeypatch.setattr(main_a, "_val_threshold", lambda *_args, **_kwargs: True)
    runtime = SovereignBootstrapRuntime(app)

    def _fake_router(*, client, model, contents):
        calls.append((client, model, contents))
        return SimpleNamespace(text="flash-ok")

    monkeypatch.setattr(bootstrap_runtime_module, "generate_content_via_router", _fake_router)

    callback = runtime._build_flash_analysis_callback()

    assert callback("prompt-body") == "flash-ok"
    assert calls == [("client", main_a.AIModels.FLASH_ANALYSIS_MODEL, "prompt-body")]


def test_build_core_llm_agents_wires_models_and_flash_callback():
    app = SimpleNamespace(
        current_project="project",
        sys=SimpleNamespace(api_client="client"),
    )
    runtime = SovereignBootstrapRuntime(app)
    registry = runtime._build_core_llm_agents(
        _agents=_make_agent_catalog(),
        models={"writer": "writer-tier", "weaver": "weaver-tier"},
        default_model="default-tier",
        flash_ask_cb="flash-callback",
    )

    assert registry["writer"].model_tier == "writer-tier"
    assert registry["analyst"].model_tier == "default-tier"
    assert registry["weaver"].model_tier == "weaver-tier"
    assert registry["four_phase"].flash_ask == "flash-callback"


def test_init_stage2_support_agents_wires_helpers_and_optimizer():
    app = SimpleNamespace(
        current_project="project",
        sys=SimpleNamespace(api_client="client"),
        selected_genre={"type": "investment"},
        ui=SimpleNamespace(log=MagicMock()),
    )
    runtime = SovereignBootstrapRuntime(app)

    optimizer = object()
    runtime._init_stage2_support_agents(
        _agents=_make_agent_catalog(),
        _v50={"create_stage2_optimizer": lambda: optimizer},
    )

    assert app.arc_draft_validator.genre == "investment"
    assert app.constraint_compiler.genre == "investment"
    assert app.arc_corrector.context == "project"
    assert app.arc_corrector.client == "client"
    assert app.arc_corrector.model_tier == main_a._FLASH_ANALYSIS_MODEL
    assert app.stage2_optimizer is optimizer
    assert app.use_arc_corrector is True
    assert app.ui.log.call_count == 4


def test_init_core_agents_runtime_bootstraps_agent_registry_and_support_modules():
    app = SimpleNamespace(
        current_project="project",
        sys=SimpleNamespace(api_client="client"),
        selected_genre={"type": "investment"},
        ui=SimpleNamespace(log=MagicMock()),
    )
    runtime = SovereignBootstrapRuntime(app)

    runtime.init_core_agents(
        _agents=_make_agent_catalog(),
        _v50={"create_stage2_optimizer": lambda: None},
        models={"writer": "writer-tier"},
        default_model="default-tier",
    )

    assert app.agents["writer"].model_tier == "writer-tier"
    assert app.arc_draft_validator.genre == "investment"
