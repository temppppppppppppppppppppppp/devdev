"""[Sweep23] Regression tests for guard/default fixes."""

import inspect
import re
from types import SimpleNamespace
from unittest.mock import MagicMock

import main_a
from modules.core.stage2_orchestrator import Stage2Orchestrator
from modules.domain.agents.analyst import Analyst
from modules.domain.agents.director_auditor import DirectorQualityAuditor


def test_stage2_orchestrator_initializes_genre_before_try_block():
    src = inspect.getsource(Stage2Orchestrator.stage_2_arcs_async_logic)
    assert re.search(r"protagonist_name\s*=\s*None\s*\n\s*genre\s*=\s*\"\"\s*\n\s*try:", src)


def test_generate_narrative_summary_handles_none_manuscripts_without_len_crash():
    ui = SimpleNamespace(log=MagicMock())
    db = SimpleNamespace(get_recent_manuscripts=MagicMock(return_value=None))
    app = SimpleNamespace(ui=ui, current_project=SimpleNamespace(db=db))

    main_a.SovereignApp._generate_narrative_summary(app, up_to_ep=10)

    logs = [c.args[0] for c in ui.log.call_args_list if c.args]
    assert any("(0" in m for m in logs)


def test_select_genre_uses_default_when_int_input_returns_none(monkeypatch):
    monkeypatch.setattr(main_a, "STAGE0_AVAILABLE", False)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: "")

    app = SimpleNamespace(
        _get_int_input=MagicMock(return_value=None),
        ui=SimpleNamespace(
            log=MagicMock(),
            title=MagicMock(),
            console=SimpleNamespace(clear=MagicMock()),
        ),
    )

    selected = main_a.SovereignApp._select_genre(app)

    assert isinstance(selected, dict)
    assert selected.get("type") in {
        "wuxia",
        "hunter",
        "investment",
        "fantasy",
        "composer",
        "cooking",
        "alt_history",
        "actor",
        "sports",
        "medical",
    }


def test_director_auditor_v0128_block_has_no_unreachable_none_guard():
    src = inspect.getsource(DirectorQualityAuditor.audit_manuscript)
    block = re.search(
        r"if self\._d\.use_v0128 and validation_context:(?P<body>[\s\S]*?)return self\._audit_with_v0128\(",
        src,
    )
    assert block is not None
    assert "if validation_context is None:" not in block.group("body")


def test_analyst_injects_protagonist_config_even_with_generic_prompt(monkeypatch):
    monkeypatch.setattr("modules.domain.agents.analyst.get_plan_volume_prompt_v25", lambda **_kwargs: "prompt")

    ctx = SimpleNamespace(
        guard=SimpleNamespace(get_v20_purism_prompt=lambda: "[genre]"),
        genre="wuxia",
        author_directives="",
        db=SimpleNamespace(load_anchor=lambda *_args, **_kwargs: None),
    )
    analyst = Analyst(context=ctx, client=MagicMock(), model_tier="gemini-2.5-flash")
    analyst.ask = MagicMock(return_value='{"vol_no": 1, "strategy_doc": "문서"}')

    bible = {
        "MasterBible": {
            "AssetLibrary": {},
            "protagonist_config": {"world_origin": "원시인", "incarnation_type": "회귀자"},
        }
    }
    analyst.plan_single_volume_v20(vol_no=1, master_bible=bible, treatment_raw_part="[]")

    sent_prompt = analyst.ask.call_args.args[0]
    assert "원시인" in sent_prompt
    assert "회귀자" in sent_prompt
