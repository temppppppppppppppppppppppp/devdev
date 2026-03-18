import logging
from unittest.mock import MagicMock

import pytest

from modules.core.constraint_db import ConstraintDB
from modules.core.response_schemas import BLUEPRINT_SCHEMA
from modules.core.stage0.story_expander import StoryExpander
from modules.core.stage01_helpers import Stage01Helpers
from modules.domain.agents.arc_draft_validator import ArcDraftValidator
from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler
from modules.domain.agents.unified_blueprint_validator import UnifiedBlueprintValidator
from modules.models.blueprint import Blueprint, BlueprintScene


def test_story_expander_bible_gate_uses_top_level_protagonist_facts():
    expander = StoryExpander(genre="wuxia")
    expander.preset_registry = MagicMock()
    expander.preset_registry.build_initial_hud.return_value = {}
    expander.extracted = {
        "title_suggestions": ["Test Title"],
        "protagonist": {"main_goal": "Win", "background": "Street origin"},
        "world_laws": ["Cause and effect"],
        "timeline": {"start_era": "Late dynasty"},
    }
    expander._generate_protagonist_detail = MagicMock(
        return_value={
            "name": "Seo Jun",
            "core": {"protagonist": "Seo Jun", "edge": "calm", "desire": "survive", "crisis": "pursuit"},
            "persona": "measured",
        }
    )
    expander._generate_npcs = MagicMock(return_value=[{"name": "A"}, {"name": "B"}])

    bible = expander.generate_bible()

    assert "_completeness_warnings" not in bible


def test_ensure_plot_roadmap_validates_existing_entries(caplog):
    bible = {"MasterBible": {"plot_roadmap": [{"block_no": 1}]}}

    with caplog.at_level(logging.WARNING):
        count = Stage01Helpers._ensure_plot_roadmap(MagicMock(), bible, [])

    assert count == 1
    assert any("plot_roadmap not Stage 2 ready (existing)" in record.message for record in caplog.records)


def test_constraint_db_snapshot_restores_item_registry():
    db = ConstraintDB(None)
    if db.item_registry is None:
        pytest.skip("semantic item registry disabled in this environment")

    db.arc_states[1] = {"state": "before"}
    db.item_registry.register_item("청검", 1)
    snap = db.snapshot()

    db.arc_states[2] = {"state": "after"}
    db.item_registry.register_item("흑도", 2)
    db.restore(snap)

    assert 2 not in db.arc_states
    assert 2 not in db.item_registry._arc_acquisitions
    assert 1 in db.item_registry._arc_acquisitions


def test_blueprint_schema_scene_breakdown_is_typed():
    scene_schema = BLUEPRINT_SCHEMA.properties["scene_breakdown"]

    assert scene_schema.additional_properties is not None
    assert scene_schema.additional_properties.any_of is not None
    assert len(scene_schema.additional_properties.any_of) == 2


def test_blueprint_model_uses_typed_scene_entries():
    bp = Blueprint.model_validate(
        {
            "episode_number": 3,
            "scene_breakdown": {
                "scene_1": {"goal": "Secure the clue", "characters": ["Seo Jun"], "location": "Archive"},
                "scene_2": "Short fallback",
            },
            "integrated_scenario": "Scenario",
        }
    )

    assert isinstance(bp.scene_breakdown["scene_1"], BlueprintScene)
    assert bp.scene_breakdown["scene_1"].goal == "Secure the clue"
    assert bp.model_dump()["scene_breakdown"]["scene_2"] == "Short fallback"


def test_blueprint_constraint_compiler_preserves_semantic_carryover():
    compiler = BlueprintConstraintCompiler()
    block = compiler.compile(
        arc_data={
            "arc_no": 1,
            "ep_start": 1,
            "ep_count": 5,
            "tactical_doc": "",
            "state_changes": {},
            "semantic_carryover": {
                "relationship_rationale": [{"npc": "Han", "trigger": "Han hides the ledger"}],
                "growth_justification": "Hero secures leverage after the audit leak",
                "continuity_checkpoints": ["Keep Han suspicious of the forged numbers"],
            },
        },
        ep_num=1,
        prev_blueprint=None,
        prev_blueprints=[],
        genre="investment",
    )

    assert block["semantic_carryover"]["relationship_rationale"][0]["npc"] == "Han"
    prompt = compiler.compile_to_prompt(block)
    assert "ARC semantic carryover" in prompt
    assert "Han" in prompt


def test_arc_draft_validator_promotes_specificity_signals_to_advisory():
    validator = ArcDraftValidator()
    tactical = ("분위기가 무겁다. 설명이 길다. 감정이 복잡하다. " * 30).strip()
    arc = {
        "arc_no": 1,
        "tactical_doc": tactical,
        "joint_docs": {"final_location": "market"},
        "state_constraints": {"relationship_changes": [{"target": "연화"}]},
        "state_changes": {"relationship_changes": []},
        "ep_start": 1,
        "ep_end": 5,
        "ep_count": 5,
        "items_acquired": [],
        "grants_received": [],
    }

    result = validator.validate(arc, prev_arcs=[], constraint_block="")

    assert any(str(issue).startswith("[warning]") for issue in result["advisory_issues"])
    assert any(str(issue).startswith("[suggestion]") for issue in result["advisory_issues"])


def test_unified_blueprint_validator_compare_mode_keeps_python_prevalidation_issues():
    selected_blueprint = {
        "episode_number": 3,
        "scene_breakdown": {"scene_1": {}, "scene_2": {}, "scene_3": {}},
        "integrated_scenario": "주인공은 혼자 계획을 세우고 또 혼자 움직인다. " * 60,
    }
    other_blueprint = {
        "episode_number": 3,
        "scene_breakdown": {
            "scene_1": {"goal": "Meet ally"},
            "scene_2": {"goal": "Trace clue"},
            "scene_3": {"goal": "Escape"},
        },
        "integrated_scenario": "연화가 계획에 직접 관여한다. " * 40,
    }
    director = MagicMock()
    director.compare_and_select_blueprint.return_value = {
        "decision": "PASS",
        "selected_blueprint": selected_blueprint,
        "selected_index": 0,
        "score": 88,
        "reason": "selected",
        "feedback": "",
        "comparison_notes": "ok",
        "contradictions": [],
    }
    state_tracker = MagicMock()
    state_tracker.check_dead_npc_in_blueprint.return_value = []

    validator = UnifiedBlueprintValidator(context=MagicMock(), client=MagicMock())
    verdict, result = validator.validate(
        blueprint=selected_blueprint,
        arc_data={"arc_no": 3, "state_constraints": {"relationship_changes": [{"target": "연화"}]}},
        constraint_block={},
        prev_blueprint=None,
        director=director,
        working_ep=3,
        arc_idx=1,
        state_tracker=state_tracker,
        all_candidates=[selected_blueprint, other_blueprint],
    )

    assert verdict == "PASS"
    assert result["phase"] == "director_compare+python_prevalidate"
    categories = {issue["category"] for issue in result["issues"]}
    assert "structure" in categories
    assert "fidelity" in categories
    assert result["quality_risk"] is True
    assert result["candidate_count"] == 2
    assert result["selected_candidate_advisory"]["quality_risk"] is True
    assert len(result["candidate_advisories"]) == 2
    assert selected_blueprint["_ensemble_meta"]["python_warnings"]
