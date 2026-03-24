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
        blueprint={"integrated_scenario": "원본 통합 흐름", "scene_breakdown": {"scene_1": {"goal": "대치"}}},
        prev_text="이전 원고",
        prev_manuscripts_text="",
        hud_report="HUD",
        current_inventory=[],
        current_martial_arts=[],
        dead_npcs=[],
        item_acquisition_timeline="",
        chain_link_section="",
        world_state_summary="",
        purism_prompt="",
        genre_name="투자물",
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


def test_normalize_writer_blueprint_moves_integrated_scenario_to_advisory():
    normalized = Stage4InterviewRound._normalize_writer_blueprint(
        {"integrated_scenario": "통합 초안", "scene_breakdown": {"scene_1": {"goal": "대치"}}}
    )

    assert normalized["integrated_scenario"] == ""
    assert normalized["integrated_scenario_advisory"] == "통합 초안"
    assert normalized["scene_breakdown"]["scene_1"]["goal"] == "대치"


def test_build_common_writer_kwargs_prefers_writer_blueprint_override():
    ir = Stage4InterviewRound(_make_ctx())
    round_ctx = _make_round_ctx()
    writer_blueprint = Stage4InterviewRound._normalize_writer_blueprint(round_ctx.blueprint)

    _, kwargs = ir._build_common_writer_kwargs(
        round_ctx=round_ctx,
        next_ep=2,
        mandatory_context="ctx",
        writer_blueprint=writer_blueprint,
    )

    assert kwargs["blueprint"]["integrated_scenario"] == ""
    assert kwargs["blueprint"]["integrated_scenario_advisory"] == "원본 통합 흐름"


def test_post_select_conflict_guidance_escalates_to_full_rewrite():
    ir = Stage4InterviewRound(_make_ctx())
    ir._build_retry_feedback_provenance = MagicMock(
        return_value={
            "merged_feedback": "merged reject feedback",
            "director_feedback_text": "director note",
            "runtime_advisory": "runtime digest",
            "retry_directives": "retry directives",
        }
    )
    ir._classify_reject_bucket = MagicMock(return_value="constraint_violation")
    ir._is_continuity_replay_reject = MagicMock(return_value=True)

    payload = ir.reject_runtime._build_reject_guidance_payload(
        director_result={
            "selected_candidate": {"manuscript": "candidate manuscript"},
            "feedback": {"issues": ["continuity drift"]},
            "action_items": ["repair continuity"],
            "fix_scope": "inplace",
            "fix_scope_reasoning": "local retry",
            "fix_pack": {"must_fix": ["anchor"], "do_not_regress": ["burner phone reveal"]},
        },
        director_feedback="initial reject",
        validation_results=[{}],
        selected="A",
        round_num=0,
        blueprint={"episode": 2},
        prev_manuscript="previous manuscript",
        tot_used=False,
        mad_used=False,
        error_category="",
    )

    assert payload.reject_bucket == "post_select_conflict"
    assert payload.resolved_fix_scope == "full"
    assert payload.resolved_fix_pack == {}
    assert "Conflict-first retry" in payload.director_feedback


def test_post_select_conflict_snapshot_drops_praise_first_signals():
    ir = Stage4InterviewRound(_make_ctx())
    ir._collect_validation_warning_lines = MagicMock(return_value=["warn-a"])
    ir._inherit_attempt_history = MagicMock(return_value=[{"old": True}])
    ir._set_retry_budget_axes = MagicMock(return_value={"repair": "rewrite_regenerate"})

    payload = ir.reject_runtime._build_reject_retry_snapshot(
        director_result={
            "selected_candidate": {
                "manuscript": "candidate manuscript",
                "strategy_name": "balanced",
            },
            "selection_reason": "best candidate because covert network felt sharp",
            "verdict_reason": "sharp covert network",
            "director_verdict": "REJECT",
            "final_verdict": "REJECT",
            "gate_basis": "post_select_conflict",
            "repair_scope": "full",
            "consistency_checklist": {"rule": "keep"},
            "state_updates": {"hud": "snapshot"},
            "open_review": "keep the burner phone idea",
            "contradiction_types": ["scene_overlap"],
            "contradiction_details": ["detail-1"],
            "firewall_triggered": True,
            "firewall_reason": "firewall",
        },
        selected="A",
        director_feedback="conflict-first reject feedback",
        action_items=["rebuild from prior authority"],
        score=44,
        validation_results=[{}],
        reject_bucket="post_select_conflict",
        tot_used=True,
        mad_used=False,
        resolved_fix_scope="full",
        resolved_fix_scope_reasoning="conflict-first rewrite",
        resolved_fix_pack={"patch_targets": ["anchor"], "do_not_regress": ["burner phone"]},
        error_category="LOGIC_ERROR",
        feedback_provenance={
            "director_feedback_text": "director note",
            "runtime_advisory": "runtime digest",
            "retry_directives": "retry directives",
        },
        previous_attempt={"old": True},
        round_num=0,
    )

    assert payload.previous_attempt["selection_reason"] == ""
    assert payload.previous_attempt["open_review"] == ""
    assert payload.previous_attempt["fix_pack"] == {}
    assert payload.previous_attempt["rejection_reason"] == "conflict-first reject feedback"
    assert payload.previous_attempt["retry_budget_axes"] == {"repair": "rewrite_regenerate"}
