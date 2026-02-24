"""[Sweep18] Regression tests for DI freshness, fallback schema, and init/runtime guards."""

from __future__ import annotations

import logging
from dataclasses import fields
from pathlib import Path
from unittest.mock import MagicMock


def _make_stage4_app():
    app = MagicMock()
    app.ui = MagicMock()
    app.ui.log = MagicMock()
    app.ui.console = MagicMock()
    app.current_project = MagicMock()
    app.current_project.db = MagicMock()
    app.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}
    app.current_project.arcs = []
    app.current_project.name = "test_project"
    app.current_project.paths = MagicMock()
    app.sys = MagicMock()
    app.sys.api_client = MagicMock()
    app.agents = {}
    app.state_tracker = None
    return app


def test_stage4_orchestrator_ctx_swap_rebuilds_lazy_modules():
    from modules.core.stage4_orchestrator import Stage4Orchestrator

    app = _make_stage4_app()
    ctx1 = MagicMock(name="ctx1")
    ctx2 = MagicMock(name="ctx2")

    orch = Stage4Orchestrator(app, context=ctx1)

    pp1 = orch.post_processor
    cb1 = orch.context_builder
    ir1 = orch.interview_round
    assert pp1.ctx is ctx1
    assert cb1.ctx is ctx1
    assert ir1.ctx is ctx1

    orch.ctx = ctx2

    pp2 = orch.post_processor
    cb2 = orch.context_builder
    ir2 = orch.interview_round
    assert pp2 is not pp1
    assert cb2 is not cb1
    assert ir2 is not ir1
    assert pp2.ctx is ctx2
    assert cb2.ctx is ctx2
    assert ir2.ctx is ctx2


def test_base_agent_quota_fallback_keeps_response_schema(monkeypatch):
    from modules.domain.agents import base_agent as base_agent_module

    class _Candidate:
        finish_reason = "STOP"

    class _Response:
        def __init__(self, text: str) -> None:
            self.text = text
            self.candidates = [_Candidate()]

    captured_calls = []

    def _fake_generate_content(*, model, contents, config):
        captured_calls.append({"model": model, "config": config})
        if len(captured_calls) == 1:
            raise RuntimeError("resource_exhausted: quota exceeded")
        return _Response('{"content":"ok"}')

    monkeypatch.setattr(base_agent_module, "METRICS_ENABLED", False)
    monkeypatch.setattr(base_agent_module.time, "sleep", lambda *_: None)
    monkeypatch.setattr(base_agent_module.types, "GenerateContentConfig", lambda **kwargs: kwargs)

    context = MagicMock()
    context.author_directives = ""
    client = MagicMock()
    client.models.generate_content = MagicMock(side_effect=_fake_generate_content)

    agent = base_agent_module.BaseAgent(context=context, client=client, model_tier="gemini-3.1-pro-preview")
    agent.backup_model = "gemini-2.5-pro"
    base_agent_module.BaseAgent._quota_exhausted_models.clear()

    response_schema = {"type": "object", "properties": {"content": {"type": "string"}}}
    out = agent.ask("테스트 프롬프트", response_schema=response_schema)

    assert out == '{"content":"ok"}'
    assert len(captured_calls) == 2
    assert captured_calls[0]["config"].get("response_schema") == response_schema
    assert captured_calls[1]["config"].get("response_schema") == response_schema


def test_style_guide_post_init_initializes_all_list_fields():
    from modules.core.stage0.style_extractor import StyleGuide

    guide = StyleGuide()
    list_fields = [f.name for f in fields(StyleGuide) if str(f.type) == "list[str]"]

    assert list_fields
    for field_name in list_fields:
        assert getattr(guide, field_name) == []


def test_main_a_stage2_sync_writes_loaded_arcs():
    source = Path("main_a.py").read_text(encoding="utf-8")
    assert 'self._state_tracker_loaded_arcs = getattr(_s2_ctx, "state_tracker_loaded_arcs", 0)' in source


def test_negative_constraint_amplifier_no_relationship_history_method():
    from modules.core.stage2_optimizer import NegativeConstraintAmplifier

    amp = NegativeConstraintAmplifier()

    # _build_relationship_history was dead code and has been removed
    assert not hasattr(amp, "_build_relationship_history")

    out = amp.amplify_constraints([{"arc_no": 1, "state_constraints": {"items_acquired": [], "grants_received": []}}])

    assert "절대 금지 사항" in out


def test_state_extractor_logs_warning_on_llm_failure_fallback(caplog):
    from modules.domain.agents.state_extractor import StateExtractor

    context = MagicMock()
    context.author_directives = ""
    extractor = StateExtractor(context=context, client=MagicMock(), model_tier="gemini-2.5-flash")
    extractor.ask = MagicMock(side_effect=RuntimeError("boom"))
    extractor._fallback_extraction = MagicMock(return_value={"arc_no": 1, "status": "fallback"})

    with caplog.at_level(logging.WARNING):
        result = extractor.extract_state({"arc_no": 1})

    assert result["status"] == "fallback"
    assert any("[StateExtractor] LLM 추출 실패 (fallback 사용):" in r.message for r in caplog.records)


def test_action_scene_outcome_keywords_are_unique():
    from modules.validation.action_scene_evaluator import ActionSceneEvaluator

    evaluator = ActionSceneEvaluator(genre="wuxia")
    assert len(set(evaluator.OUTCOME_KEYWORDS)) == len(evaluator.OUTCOME_KEYWORDS)
