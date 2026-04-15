from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.stage4_interview_round import Stage4InterviewRound


def _make_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.master_bible = {"MasterBible": {"protagonist_config": {}}}
    ctx.current_project.db = MagicMock()
    ctx.state_tracker = MagicMock()
    ctx.world_state = MagicMock()
    ctx.world_state._state = {"motivations": [], "promises": []}
    ctx.get_module = MagicMock(return_value=None)
    ctx.agents = {"director": MagicMock()}
    return ctx


def _make_round_ctx():
    return SimpleNamespace(
        blueprint={"integrated_scenario": "", "scene_breakdown": {"scene_1": {"goal": "start"}}},
        prev_text="previous manuscript",
        prev_manuscripts_text="",
        hud_report="HUD",
        current_inventory=[],
        current_martial_arts=[],
        dead_npcs=[],
        item_acquisition_timeline="",
        chain_link_section="",
        world_state_summary="",
        purism_prompt="",
        genre_name="investment",
        npc_equipment_summary="",
        effective_anti_trope="",
        intro_dna="",
        style_guide="style",
        reference_excerpt="",
        reference_anchor_prompt="",
        justification_prompt="",
        reflexion_prompt="",
        preflight_advisory="",
        arc_tactical="arc",
        arc_data={},
    )


def test_build_common_writer_kwargs_threads_arc_data_for_carryover_ceiling_authority():
    ir = Stage4InterviewRound(_make_ctx())
    round_ctx = _make_round_ctx()
    round_ctx.arc_data = {
        "arc_no": 2,
        "cross_stage_authority_packet": {"contract_version": "cross_stage_authority_packet.v1"},
    }

    _, kwargs = ir._build_common_writer_kwargs(
        round_ctx=round_ctx,
        next_ep=2,
        mandatory_context="ctx",
    )

    assert kwargs["arc_data"] == round_ctx.arc_data
