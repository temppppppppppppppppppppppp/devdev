"""Agent constructor/DI smoke tests (updated for current signatures)."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.domain.agents.analyst import Analyst
from modules.domain.agents.base_agent import BaseAgent
from modules.domain.agents.director import Director
from modules.domain.agents.manager import Manager
from modules.domain.agents.weaver import Weaver
from modules.domain.agents.writer import Writer


@pytest.fixture
def agent_context(tmp_path):
    ctx = SimpleNamespace()
    ctx.author_directives = ""
    ctx.paths = SimpleNamespace(config=tmp_path)
    (tmp_path / "prompts").mkdir(parents=True, exist_ok=True)
    ctx.guard = None
    return ctx


@pytest.fixture
def mock_client():
    client = MagicMock()
    response = MagicMock()
    response.text = json.dumps({"status": "ok", "content": "test"})
    response.candidates = [MagicMock(finish_reason="STOP")]
    client.models.generate_content.return_value = response
    return client


def test_base_agent_ask_returns_json_text(agent_context, mock_client, monkeypatch):
    agent = BaseAgent(context=agent_context, client=mock_client, model_tier="gemini-2.5-flash")
    monkeypatch.setattr(agent, "API_DELAY", 0)
    result = agent.ask("테스트 프롬프트")
    parsed = json.loads(result)
    assert parsed["status"] == "ok"


def test_writer_initialization(agent_context, mock_client):
    writer = Writer(agent_context, mock_client)
    assert writer is not None
    assert writer.genre == "wuxia"


def test_director_initialization(agent_context, mock_client):
    director = Director(agent_context, mock_client)
    assert director is not None
    assert director._continuity is not None
    assert director._auditor is not None


def test_analyst_genre_library_path_fantasy(agent_context, mock_client):
    analyst = Analyst(agent_context, mock_client)
    path = analyst._get_genre_library_path("fantasy")
    assert str(path).endswith("config\\prompts\\analyst_libraries_fantasy.json") or str(path).endswith(
        "config/prompts/analyst_libraries_fantasy.json"
    )


def test_manager_update_state_and_lore_returns_dict(agent_context, mock_client, monkeypatch):
    manager = Manager(agent_context, mock_client)
    monkeypatch.setattr(manager, "API_DELAY", 0)
    mock_client.models.generate_content.return_value = MagicMock(
        text=json.dumps(
            {
                "context_audit": {"integrity_score": 90, "summary": "ok", "evidence_check": "ok"},
                "state_updates": {"actual_truth": {"internal_energy": 60}},
                "new_lore": {"Key_NPCs": [], "Key_Items": []},
            }
        ),
        candidates=[MagicMock(finish_reason="STOP")],
    )

    result = manager.update_state_and_lore_v20(
        ep_num=1,
        manuscript="원고",
        current_state={},
        lore_list=[],
        active_seeds=[],
        causal_history="",
    )
    assert isinstance(result, dict)
    assert "state_updates" in result


def test_weaver_generate_arc_drive_cached_mode(agent_context, mock_client):
    weaver = Weaver(agent_context, mock_client)
    weaver.cache_name = "cache/test"
    mock_client.models.generate_content.return_value = MagicMock(
        text=json.dumps(
            {
                "short_term_objective": "단기 목표",
                "mid_term_objective": "중기 목표",
            }
        )
    )

    result = weaver.generate_arc_drive(current_arc_dna={}, analyst_lack_report={}, grand_objective="장기 목표")
    assert isinstance(result, dict)
    assert result["status"] == "LOCKED"
    assert result["short_term_objective"] == "단기 목표"
