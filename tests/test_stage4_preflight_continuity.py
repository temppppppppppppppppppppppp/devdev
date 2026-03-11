import json
from unittest.mock import MagicMock

from modules.core.stage4_orchestrator import Stage4Orchestrator


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
