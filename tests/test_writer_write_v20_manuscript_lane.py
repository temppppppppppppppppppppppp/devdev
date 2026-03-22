import json
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

import modules.domain.agents.writer as writer_module
from modules.domain.agents.writer import Writer


@pytest.fixture
def writer_context(tmp_path):
    ctx = SimpleNamespace()
    ctx.author_directives = ""
    ctx.paths = SimpleNamespace(config=tmp_path)
    (tmp_path / "prompts").mkdir(parents=True, exist_ok=True)
    ctx.guard = None
    ctx.db = MagicMock()
    ctx.master_bible = {}
    ctx.genre = {"name": "fantasy"}
    return ctx


@pytest.fixture
def writer_agent(writer_context):
    return Writer(context=writer_context, client=MagicMock(), model_tier="gemini-2.5-flash")


def _install_fake_google_genai(monkeypatch):
    google_mod = ModuleType("google")
    genai_mod = ModuleType("google.genai")
    types_mod = ModuleType("google.genai.types")

    class DummyGenerateContentConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    types_mod.GenerateContentConfig = DummyGenerateContentConfig
    genai_mod.types = types_mod
    google_mod.genai = genai_mod
    monkeypatch.setitem(sys.modules, "google", google_mod)
    monkeypatch.setitem(sys.modules, "google.genai", genai_mod)
    monkeypatch.setitem(sys.modules, "google.genai.types", types_mod)


def test_write_v20_manuscript_delegates_to_helper_family(writer_agent, monkeypatch):
    calls = []

    def fake_collect(**kwargs):
        calls.append(("collect", kwargs["ep_num"]))
        return {"ctx": True}

    def fake_build(**kwargs):
        assert kwargs["prompt_context"] == {"ctx": True}
        calls.append(("build", kwargs["breakdown_doc"]))
        return "PROMPT"

    def fake_dispatch(dynamic_prompt):
        calls.append(("dispatch", dynamic_prompt))
        return "RESULT"

    monkeypatch.setattr(writer_agent, "_collect_writer_prompt_context", fake_collect)
    monkeypatch.setattr(writer_agent, "_build_writer_dynamic_prompt", fake_build)
    monkeypatch.setattr(writer_agent, "_dispatch_writer_dynamic_prompt", fake_dispatch)

    result = writer_agent.write_v20_manuscript(
        ep_num=7,
        breakdown_doc="breakdown",
        master_bible={},
        hud_report="HUD",
        purism_prompt="PURISM",
        prev_full_manuscript="prev",
        arc_doc={"MUST_FOCUS_ON": "focus"},
    )

    assert result == "RESULT"
    assert calls == [("collect", 7), ("build", "breakdown"), ("dispatch", "PROMPT")]


def test_collect_writer_prompt_context_normalizes_defaults(writer_agent, writer_context, monkeypatch):
    master_bible = {
        "MasterBible": {
            "ProjectData": {"CoreIdentity": {"desire": "rise"}},
            "AssetLibrary": {
                "KeyNPCs": [
                    {"name": "NPC_A", "NPC_Martial_HUD": {"equipment": ["sword"]}},
                ]
            },
            "protagonist_config": {"world_origin": "원시인", "incarnation_type": "회귀자"},
        }
    }
    writer_context.master_bible = master_bible

    monkeypatch.setattr(writer_agent, "_build_writer_reference_anchor_prompt", lambda *_args: "[ANCHOR]")
    monkeypatch.setattr(writer_agent, "get_genre_rules_prompt", lambda: "[GENRE]")
    monkeypatch.setattr(writer_module, "_build_anti_trope_instructions_shared", lambda genre: f"[ANTI:{genre}]")
    monkeypatch.setattr(writer_module, "_build_mandatory_context_shared", lambda db, bible, ep: f"[MANDATORY:{ep}]")
    monkeypatch.setattr(
        writer_module, "_build_justification_guidance_shared", lambda hud_report, genre: f"[JUSTIFY:{genre}]"
    )
    monkeypatch.setattr(writer_module, "_get_hud_trend_safe_shared", lambda context, ep_num: f"HUD:{ep_num}")

    prompt_context = writer_agent._collect_writer_prompt_context(
        ep_num=1,
        master_bible=master_bible,
        hud_report="HUD",
        intro_dna="DNA",
        feedback="retry",
        arc_doc={
            "MUST_FOCUS_ON": "battle",
            "PATTERN_PROFILE": {"primary": "P1", "secondary": ["S1"]},
            "PATTERN_MIXING_LOGIC": "mix",
        },
        tactical_references="",
        entity_registry={"items": ["amulet"]},
    )

    assert prompt_context["focus_tag"] == "battle"
    assert prompt_context["dna_instruction"] == "[제1화 특수 DNA 적용]: DNA"
    assert prompt_context["tactical_references"] == "특이 사항 없음."
    assert "NPC_A" in prompt_context["safe_npc_equipment"]
    assert "원시인 모드" in prompt_context["protagonist_instructions_text"]
    assert "회귀자" in prompt_context["protagonist_instructions_text"]
    assert prompt_context["reference_anchor_prompt"] == "[ANCHOR]"
    assert prompt_context["anti_trope"] == "[ANTI:fantasy]"
    assert prompt_context["genre_rules_prompt"] == "[GENRE]"
    assert prompt_context["mandatory_context"] == "[MANDATORY:1]"
    assert prompt_context["justification_guidance"] == "[JUSTIFY:fantasy]"
    assert prompt_context["hud_trend"] == "HUD:1"
    assert "retry" in prompt_context["feedback_section"]


def test_dispatch_writer_dynamic_prompt_uses_cached_router(writer_agent, monkeypatch):
    _install_fake_google_genai(monkeypatch)
    writer_agent.cache_name = "cache/test"
    captured = {}

    def fake_router(*, client, model, contents, config):
        captured["client"] = client
        captured["model"] = model
        captured["contents"] = contents
        captured["config"] = config.kwargs
        return SimpleNamespace(text=json.dumps({"content": "ok"}))

    monkeypatch.setattr(writer_module, "generate_content_via_router", fake_router)

    result = writer_agent._dispatch_writer_dynamic_prompt("PROMPT")

    assert json.loads(result)["content"] == "ok"
    assert captured["contents"] == "PROMPT"
    assert captured["config"]["cached_content"] == "cache/test"
    assert captured["config"]["response_mime_type"] == "application/json"


def test_dispatch_writer_dynamic_prompt_falls_back_on_router_error(writer_agent, monkeypatch):
    _install_fake_google_genai(monkeypatch)
    writer_agent.cache_name = "cache/test"
    monkeypatch.setattr(writer_module, "generate_content_via_router", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError))
    monkeypatch.setattr(writer_agent, "_fallback_full_request", lambda dynamic_prompt: f"fallback::{dynamic_prompt}")

    result = writer_agent._dispatch_writer_dynamic_prompt("PROMPT")

    assert result == "fallback::PROMPT"
