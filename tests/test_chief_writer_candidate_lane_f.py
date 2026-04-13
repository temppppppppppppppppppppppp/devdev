import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from modules.domain.agents.chief_writer import ChiefWriter


def _make_writer() -> ChiefWriter:
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
    writer._extract_json_robust = MagicMock()
    writer.ask = MagicMock()
    writer._ask_with_cached_context = MagicMock()
    return writer


def test_generate_single_candidate_shell_coordinates_helper_family():
    writer = _make_writer()
    request_bundle = {
        "strategy_config": {"name": "Balanced", "emphasis": "steady"},
        "temperature": 0.7,
        "strategy_feedback_block": "",
        "output_block": "schema",
    }
    parsed = {"content": "body", "title": "title", "state_updates": {}, "key_scenes_covered": ["s1"]}

    writer._prepare_single_candidate_request = MagicMock(return_value=request_bundle)
    writer._request_single_candidate_response = MagicMock(return_value='{"content":"body"}')
    writer.quality_gate.sanitize_leakage.return_value = '{"content":"body"}'
    writer._extract_json_robust.return_value = parsed
    writer._extract_single_candidate_manuscript_payload = MagicMock(return_value=("body", '{"content":"body"}'))
    writer._extract_candidate_npcs = MagicMock(return_value=[{"name": "npc"}])
    writer.quality_gate.apply_self_critique.return_value = '{"content":"body revised"}'
    writer._finalize_single_candidate_critique = MagicMock(return_value=("body revised", "title", {"hp": 10}))
    writer._build_single_candidate_result = MagicMock(
        return_value={"strategy": "balanced", "manuscript": "body revised"}
    )

    result = writer._generate_single_candidate(
        ep_num=7,
        strategy="balanced",
        blueprint={"scene": 1},
        common_context="ctx",
        hud_report="hud",
        master_bible={"MasterBible": {"AssetLibrary": {"KeyNPCs": [{"name": "npc"}]}}},
        genre_name="wuxia",
        cache_name="cache/x",
        strategy_feedback="fix focus",
        motivations=["goal"],
        promises=["promise"],
        strategy_temperature=0.9,
    )

    assert result == {"strategy": "balanced", "manuscript": "body revised"}
    writer._prepare_single_candidate_request.assert_called_once_with(
        strategy="balanced",
        genre_name="wuxia",
        strategy_feedback="fix focus",
        strategy_temperature=0.9,
    )
    writer._request_single_candidate_response.assert_called_once_with(
        common_context="ctx",
        cache_name="cache/x",
        request_bundle=request_bundle,
    )
    writer._build_single_candidate_result.assert_called_once()


def test_generate_single_candidate_normalizes_list_payload_from_extract_json():
    writer = _make_writer()
    request_bundle = {
        "strategy_config": {"name": "Balanced", "emphasis": "steady"},
        "temperature": 0.7,
        "strategy_feedback_block": "",
        "output_block": "schema",
    }
    parsed = [{"content": "body", "title": "title", "state_updates": {}, "key_scenes_covered": ["s1"]}]

    writer._prepare_single_candidate_request = MagicMock(return_value=request_bundle)
    writer._request_single_candidate_response = MagicMock(return_value='[{"content":"body"}]')
    writer.quality_gate.sanitize_leakage.return_value = '[{"content":"body"}]'
    writer._extract_json_robust.return_value = parsed
    writer._extract_single_candidate_manuscript_payload = MagicMock(return_value=("body", '{"content":"body"}'))
    writer._extract_candidate_npcs = MagicMock(return_value=[{"name": "npc"}])
    writer.quality_gate.apply_self_critique.return_value = '{"content":"body revised"}'
    writer._finalize_single_candidate_critique = MagicMock(return_value=("body revised", "title", {"hp": 10}))
    writer._build_single_candidate_result = MagicMock(
        return_value={"strategy": "balanced", "manuscript": "body revised"}
    )

    result = writer._generate_single_candidate(
        ep_num=7,
        strategy="balanced",
        blueprint={"scene": 1},
        common_context="ctx",
        hud_report="hud",
        master_bible={"MasterBible": {"AssetLibrary": {"KeyNPCs": [{"name": "npc"}]}}},
        genre_name="wuxia",
        cache_name="cache/x",
        strategy_feedback="fix focus",
        motivations=["goal"],
        promises=["promise"],
        strategy_temperature=0.9,
    )

    assert result == {"strategy": "balanced", "manuscript": "body revised"}
    writer._extract_single_candidate_manuscript_payload.assert_called_once_with(parsed[0])


def test_prepare_single_candidate_request_uses_strategy_temperature_and_schema():
    writer = _make_writer()
    writer._get_critical_keys_for_genre = MagicMock(return_value=["hp", "wealth"])

    bundle = writer._prepare_single_candidate_request(
        strategy="balanced",
        genre_name="wuxia",
        strategy_feedback="fix cadence",
        strategy_temperature=0.91,
    )

    assert bundle["temperature"] == 0.91
    assert "[Strategy-Specific Feedback]" in bundle["strategy_feedback_block"]
    assert '"writing_strategy": "balanced"' in bundle["output_block"]
    assert "state_updates" in bundle["output_block"]
    writer._get_critical_keys_for_genre.assert_called_once()


def test_regenerate_with_feedback_shell_uses_feedback_and_strategy_helpers():
    writer = _make_writer()
    writer._build_regeneration_feedback = MagicMock(return_value="enhanced")
    writer._build_regeneration_strategy_hints = MagicMock(
        return_value=("constraints", "tension", "specific", {"tension": "specific"})
    )
    writer.generate_ensemble = MagicMock(return_value=[{"manuscript": "ok"}])

    result = writer.regenerate_with_feedback(
        ep_num=3,
        blueprint={"scene": 1},
        prev_manuscript="prev",
        hud_report="hud",
        arc_doc="arc",
        master_bible={},
        style_guide="style",
        director_feedback="director",
        previous_attempt={"strategy": "balanced"},
        attempt_number=2,
        genre_name="wuxia",
    )

    assert result == [{"manuscript": "ok"}]
    writer._build_regeneration_feedback.assert_called_once_with(
        previous_attempt={"strategy": "balanced"},
        director_feedback="director",
        attempt_number=2,
    )
    writer._build_regeneration_strategy_hints.assert_called_once_with({"strategy": "balanced"})
    assert writer.generate_ensemble.call_args.kwargs["director_feedback"] == "enhanced"
    assert writer.generate_ensemble.call_args.kwargs["strategy_specific_feedback"] == "specific"
    assert writer.generate_ensemble.call_args.kwargs["strategy_feedback_map"] == {"tension": "specific"}
    assert writer.generate_ensemble.call_args.kwargs["rejected_strategy"] == "tension"
    assert writer.generate_ensemble.call_args.kwargs["failure_constraints"] == "constraints"


def test_build_regeneration_feedback_includes_open_review_score_breakdown_and_history():
    writer = _make_writer()
    writer._build_retry_history_feedback = MagicMock(return_value="[retry history]")

    feedback = writer._build_regeneration_feedback(
        previous_attempt={
            "strategy": "balanced",
            "rejection_reason": "length",
            "score_breakdown": {"length": 45, "cadence": 51},
            "validation_warnings": ["warn-a", "warn-b"],
            "fix_scope_reasoning": "local patch only",
            "open_review": "tighten the ending",
        },
        director_feedback="revise now",
        attempt_number=3,
    )

    assert "revise now" in feedback
    assert "[세부 채점]" in feedback
    assert "length: 45" in feedback
    assert "[Python 검증 경고]" in feedback
    assert "local patch only" in feedback
    assert "tighten the ending" in feedback
    assert "[retry history]" in feedback


def test_build_regeneration_feedback_includes_reuse_contract_and_structured_conflict_payload():
    writer = _make_writer()
    writer._build_retry_history_feedback = MagicMock(return_value="")

    feedback = writer._build_regeneration_feedback(
        previous_attempt={
            "strategy": "balanced",
            "rejection_reason": "post-select conflict",
            "selection_reason": "best candidate because the midpoint reveal worked",
            "open_review": "keep the burner phone beat",
            "best_manuscript": "baseline manuscript body " * 200,
            "reuse_contract": {
                "mode": "best_manuscript_baseline",
                "baseline_field": "best_manuscript",
                "conflict_field": "conflict_contract",
                "preserve_rationale": True,
            },
            "conflict_contract": {
                "contract_type": "post_select_conflict",
                "conflicts": [
                    {
                        "conflict_type": "continuity",
                        "conflict_detail": "scene overlap conflict",
                        "source_episode": "",
                        "expected_truth": "scene overlap conflict",
                    }
                ],
                "truth_pins": [
                    {
                        "pin_key": "family_group_name",
                        "family": "proper_noun_group",
                        "expected": "대한그룹",
                        "observed": "유성그룹",
                    }
                ],
                "rewrite_required_reasons": ["proper_noun_group_truth_drift"],
            },
        },
        director_feedback="revise now",
        attempt_number=2,
    )

    assert "[Near-pass Baseline Reuse Contract" in feedback
    assert "preserved_selection_reason=best candidate because the midpoint reveal worked" in feedback
    assert "preserved_open_review=keep the burner phone beat" in feedback
    assert "[Structured Conflict Contract" in feedback
    assert "type=continuity" in feedback
    assert "[Authoritative Truth Pins" in feedback
    assert "keep `대한그룹`; do not drift to `유성그룹`" in feedback
    assert "[Stored Near-pass Manuscript Baseline]" in feedback
    assert "baseline manuscript body" in feedback


def test_build_regeneration_strategy_hints_stringifies_selection_reason_dict():
    writer = _make_writer()

    failure_constraints, rejected_strategy, strategy_feedback, strategy_feedback_map = (
        writer._build_regeneration_strategy_hints(
            {
                "action_items": ["fix opening", "reduce leakage"],
                "selected_strategy_key": "balanced",
                "selection_reason": {"why": "cadence"},
            }
        )
    )

    assert "fix opening" in failure_constraints
    assert rejected_strategy == "balanced"
    assert json.loads(strategy_feedback) == {"why": "cadence"}
    assert json.loads(strategy_feedback_map["balanced"]) == {"why": "cadence"}


def test_build_regeneration_strategy_hints_prefers_existing_strategy_feedback_map():
    writer = _make_writer()

    failure_constraints, rejected_strategy, strategy_feedback, strategy_feedback_map = (
        writer._build_regeneration_strategy_hints(
            {
                "selected_strategy_key": "tension",
                "selection_reason": "legacy selection reason",
                "strategy_feedback_map": {"tension": "mapped retry focus", "balanced": "other"},
            }
        )
    )

    assert failure_constraints == ""
    assert rejected_strategy == "tension"
    assert strategy_feedback == "mapped retry focus"
    assert strategy_feedback_map["tension"] == "mapped retry focus"
