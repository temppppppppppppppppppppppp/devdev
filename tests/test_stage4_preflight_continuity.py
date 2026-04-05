import json
from unittest.mock import MagicMock, patch

from modules.core.stage4_orchestrator import Stage4Orchestrator


def _preflight_threshold_mock(key, default=None):
    if "enabled" in key:
        return True
    if "min_episode" in key:
        return 2
    return default


def test_stage4_preflight_returns_patched_blueprint_when_continuity_pin_applies():
    app = MagicMock()
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.sys = MagicMock()
    ctx.sys.api_client = MagicMock()
    ctx.world_state = MagicMock()
    ctx.world_state.get_summary.return_value = "자산: 15억"
    ctx.fact_ledger = MagicMock()
    ctx.fact_ledger.get_canonical_summary.return_value = "총자산 15억"
    ctx.current_project = MagicMock()
    ctx.current_project.name = "test_project"
    ctx.current_project.db.get_manuscript.return_value = {"content": '직전 원고에는 "아퀼라"만 나온다.'}
    ctx.agents = {"three_phase_bp": MagicMock()}

    orch = Stage4Orchestrator(app, context=ctx)

    llm_response = MagicMock()
    llm_response.text = json.dumps({"passed": True, "issues": [], "summary": "ok"})
    ctx.sys.api_client.models.generate_content.return_value = llm_response

    blueprint = {
        "episode_number": 3,
        "scene_breakdown": {"scene_1": '주인공은 "이클립스"를 떠올린다.'},
        "integrated_scenario": '다음 날 오후 그는 "이클립스"를 다시 찾는다.',
    }
    arc_data = {
        "ep_start": 1,
        "ep_end": 5,
        "tactical_doc": '약 2주 후 주인공은 "아퀼라"를 정리한다.',
        "episode_details": [{"ep_num": 3, "details": ['약 2주 후 "아퀼라" 관련 정리']}],
    }

    with (
        patch("modules.core.stage4_orchestrator._threshold", _preflight_threshold_mock),
        patch(
            "modules.core.prompt_loader.PromptLoader.load",
            return_value="WS={world_state_summary}\nFL={fact_ledger_summary}\nARC={arc_tactical_excerpt}\nEP={ep_num}\nBP={blueprint_json}",
        ),
        patch("modules.core.stage4_orchestrator.generate_content_via_router", return_value=llm_response),
    ):
        result = orch._preflight_validate_blueprint(
            blueprint=blueprint,
            arc_data=arc_data,
            ep_num=3,
        )

    assert result["passed"] is True
    assert result["patched_blueprint"] is not None
    patched_text = json.dumps(result["patched_blueprint"], ensure_ascii=False)
    assert "아퀼라" in patched_text
    assert "약 2주 후" in patched_text
    assert result["patched_blueprint"]["_continuity_pins"]


def test_stage4_preflight_attaches_opening_action_continuity_pin_to_blueprint():
    app = MagicMock()
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.sys = MagicMock()
    ctx.sys.api_client = MagicMock()
    ctx.world_state = MagicMock()
    ctx.world_state.get_summary.return_value = "위치: 본가"
    ctx.fact_ledger = MagicMock()
    ctx.fact_ledger.get_canonical_summary.return_value = "이전 화 baseline 존재"
    ctx.current_project = MagicMock()
    ctx.current_project.name = "test_project"
    ctx.current_project.db.get_manuscript.return_value = {
        "content": (
            "아버지의 목소리가 들려왔지만 시우는 멈추지 않았다. "
            "현관문 손잡이를 움켜쥔 채 그대로 밖을 향해 걸어 나갔다."
        )
    }
    ctx.agents = {"three_phase_bp": MagicMock()}

    orch = Stage4Orchestrator(app, context=ctx)

    llm_response = MagicMock()
    llm_response.text = json.dumps({"passed": True, "issues": [], "summary": "ok"})
    ctx.sys.api_client.models.generate_content.return_value = llm_response

    blueprint = {
        "episode_number": 2,
        "integrated_scenario": (
            "집을 나서려던 한시우는 아버지의 부름에 걸음을 멈췄다. "
            "몸을 돌려 아버지를 마주 보자, 아버지는 그를 서재로 불렀고 "
            "한시우는 그의 뒤를 따라 복도를 걸었다."
        ),
        "scene_breakdown": {
            "scene_1": "한시우가 걸음을 멈추고 아버지를 마주 본다.",
            "scene_2": "한시우가 아버지의 뒤를 따라 서재로 향한다.",
        },
    }

    with (
        patch("modules.core.stage4_orchestrator._threshold", _preflight_threshold_mock),
        patch(
            "modules.core.prompt_loader.PromptLoader.load",
            return_value="WS={world_state_summary}\nFL={fact_ledger_summary}\nARC={arc_tactical_excerpt}\nEP={ep_num}\nBP={blueprint_json}",
        ),
        patch("modules.core.stage4_orchestrator.generate_content_via_router", return_value=llm_response),
    ):
        result = orch._preflight_validate_blueprint(
            blueprint=blueprint,
            arc_data={"tactical_doc": "", "episode_details": []},
            ep_num=2,
        )

    assert result["passed"] is True
    assert result["patched_blueprint"] is not None
    continuity_pins = result["patched_blueprint"]["_continuity_pins"]
    assert any(pin["type"] == "opening_action_continuity_pin" for pin in continuity_pins)
