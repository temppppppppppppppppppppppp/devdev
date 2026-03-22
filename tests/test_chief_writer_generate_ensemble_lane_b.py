from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from modules.domain.agents.chief_writer import ChiefWriter


def _make_writer():
    with patch("modules.domain.agents.chief_writer.BaseAgent.__init__", return_value=None):
        writer = ChiefWriter.__new__(ChiefWriter)
    writer.context = SimpleNamespace(current_project=SimpleNamespace(name="Lane Project"), project_name="Lane Project")
    writer._context = writer.context
    writer._context_builder = MagicMock()
    writer._quality_gate = MagicMock()
    writer._operator_log = MagicMock()
    writer._prefetch_manuscripts = MagicMock()
    writer._get_or_create_context_cache = MagicMock(return_value={})
    writer._annotate_candidate_diversity = MagicMock()
    writer._context_cache_project_namespace = MagicMock(return_value="Lane_Project_ep_7")
    return writer


def test_generate_ensemble_owner_shell_coordinates_helper_chain():
    writer = _make_writer()
    writer._prepare_generate_ensemble_context = MagicMock(
        return_value=("ctx", "cache/manuscript", ["balanced"], {"balanced": 0.7})
    )
    worker_candidates = [{"strategy": "balanced", "manuscript": "body"}]
    writer._run_generate_ensemble_workers = MagicMock(return_value=worker_candidates)
    writer._recover_generate_ensemble_candidates = MagicMock(return_value=worker_candidates)
    writer._finalize_generate_ensemble_candidates = MagicMock(return_value=worker_candidates)

    result = writer.generate_ensemble(
        ep_num=7,
        blueprint={},
        prev_manuscript="prev",
        hud_report="hud",
        arc_doc="arc",
        master_bible={},
    )

    assert result == worker_candidates
    writer._prepare_generate_ensemble_context.assert_called_once()
    writer._run_generate_ensemble_workers.assert_called_once()
    writer._recover_generate_ensemble_candidates.assert_called_once()
    writer._finalize_generate_ensemble_candidates.assert_called_once_with(worker_candidates, 7)


def test_prepare_generate_ensemble_context_builds_context_cache_and_strategies():
    writer = _make_writer()
    writer._context_builder.build_common_context.return_value = "common-context"
    writer._select_ensemble_strategies = MagicMock(return_value=(["balanced", "tension"], {"balanced": 0.7}))

    context, cache_name, strategies, temperatures = writer._prepare_generate_ensemble_context(
        ep_num=7,
        blueprint={},
        prev_manuscript="prev",
        hud_report="hud",
        arc_doc="arc",
        master_bible={},
        style_guide="style",
        reference_excerpt="ref",
        director_feedback="fb",
        failure_constraints="fail",
        current_inventory=[],
        current_martial_arts=[],
        dead_npcs=[],
        item_acquisition_timeline="",
        reference_anchor_prompt="",
        mandatory_context="",
        anti_trope_prompt="",
        justification_prompt="",
        reflexion_prompt="",
        genre_name="무협",
        npc_equipment_summary="",
        intro_dna="",
        purism_prompt="",
        state_tracker=None,
        prev_manuscripts_text="",
        world_state_summary="",
        chain_link_section="",
        emotional_beat_section="",
        upcoming_arc_items=[],
        strategy_budget="reduced",
        preferred_strategy="tension",
        single_strategy="",
    )

    assert context == "common-context"
    assert cache_name is None
    assert strategies == ["balanced", "tension"]
    assert temperatures == {"balanced": 0.7}
    writer._prefetch_manuscripts.assert_called_once_with(7, window=10)
    writer._get_or_create_context_cache.assert_called_once()
    writer._select_ensemble_strategies.assert_called_once_with(
        strategy_budget="reduced",
        preferred_strategy="tension",
        single_strategy="",
    )


def test_recover_generate_ensemble_candidates_uses_single_fallback_after_total_failure():
    writer = _make_writer()
    writer._generate_single_candidate = MagicMock(
        return_value={"strategy": "balanced", "manuscript": "fallback", "metadata": {}}
    )

    recovered = writer._recover_generate_ensemble_candidates(
        candidates=[{"strategy": "balanced", "error": True}],
        strategies=["balanced", "tension"],
        strategy_temperatures={"balanced": 0.9},
        ep_num=7,
        blueprint={},
        common_context="ctx",
        hud_report="hud",
        master_bible={},
        genre_name="무협",
        cache_name="cache/manuscript",
        motivations=[],
        promises=[],
        strategy_specific_feedback="specific",
        rejected_strategy="balanced",
    )

    assert recovered == [{"strategy": "balanced", "manuscript": "fallback", "metadata": {}}]
    writer._generate_single_candidate.assert_called_once()
    assert writer._generate_single_candidate.call_args.kwargs["strategy_feedback"] == "specific"


def test_finalize_generate_ensemble_candidates_builds_error_fallback_and_annotations():
    writer = _make_writer()

    finalized = writer._finalize_generate_ensemble_candidates([], 7)

    assert finalized[0]["strategy"] == "error_fallback"
    assert finalized[0]["error"] is True
    writer._annotate_candidate_diversity.assert_called_once()
