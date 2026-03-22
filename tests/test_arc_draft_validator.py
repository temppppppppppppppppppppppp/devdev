"""Regression tests for ArcDraftValidator grant timeline checks."""

from modules.domain.agents.arc_draft_validator import ArcDraftValidator


def test_validate_grant_timeline_detects_duplicate_from_state_constraints():
    validator = ArcDraftValidator()

    prev_arcs = [
        {
            "state_constraints": {"grants_received": ["\ucca0\ud608\uc0ac\uc790\ud328"]},
            "tactical_doc": "",
        }
    ]
    arc = {
        "state_constraints": {"grants_received": ["\ucca0\ud608\uc0ac\uc790\ud328"]},
        "tactical_doc": "",
    }

    result = validator._validate_grant_timeline(arc, prev_arcs)

    assert result["penalty"] >= 25
    assert any("\ucca0\ud608\uc0ac\uc790\ud328" in msg and "state_constraints" in msg for msg in result["critical"])


def test_genre_suffixes_loaded_for_non_wuxia():
    validator = ArcDraftValidator(genre="sports")
    assert "\ud2b8\ub85c\ud53c" in validator.weapon_keywords


def test_coerce_tactical_doc_value_converts_dict_payloads():
    validator = ArcDraftValidator()

    tactical, warnings, penalty = validator._coerce_tactical_doc_value(
        {
            "tactical_doc": {
                "scene_1": "A" * 80,
                "scene_2": "B" * 80,
            }
        }
    )

    assert len(tactical) >= 160
    assert "\n" in tactical
    assert penalty == 0
    assert any("dict" in warning for warning in warnings)


def test_validate_tactical_episode_layout_reports_missing_short_balance_and_order():
    validator = ArcDraftValidator()

    warnings, penalty = validator._validate_tactical_episode_layout(
        {
            3: "x" * 120,
            1: "y" * 900,
        },
        [1, 2, 3],
    )

    assert any("\ub204\ub77d\ub41c \ud654" in warning for warning in warnings)
    assert any("\ubd84\ub7c9 \ubd80\uc871 \ud654" in warning for warning in warnings)
    assert any("\ud654\ubcc4 \ubd84\ub7c9 \ubd88\uade0\ud615" in warning for warning in warnings)
    assert any("\ud654 \uc21c\uc11c \ubd88\uc77c\uce58" in warning for warning in warnings)
    assert penalty == 28


def test_collect_tactical_relationship_npcs_merges_state_sources():
    validator = ArcDraftValidator()

    names = validator._collect_tactical_relationship_npcs(
        {
            "state_constraints": {
                "relationship_changes": [{"target": "ally"}, {"npc": "mentor"}, {"target": "a"}],
            },
            "state_changes": {
                "relationship_changes": [{"target": "rival"}, {"npc": "mentor"}, {"npc": None}],
            },
        }
    )

    assert names == ["ally", "mentor", "rival"]


def test_validate_tactical_doc_preserves_orchestrated_penalty_warning_and_suggestions(monkeypatch):
    validator = ArcDraftValidator()
    arc = {"tactical_doc": "TACTICAL", "ep_start": 5, "ep_count": 2}

    monkeypatch.setattr(
        validator,
        "_coerce_tactical_doc_value",
        lambda _arc: ("TACTICAL", ["coerce-warning"], 4),
    )
    monkeypatch.setattr(
        validator,
        "_resolve_tactical_doc_expectations",
        lambda _arc: (5, 2, [5, 6], 1000, 800),
    )
    monkeypatch.setattr(
        validator,
        "_validate_tactical_length",
        lambda length, **_kwargs: ([f"length={length}"], 5),
    )
    monkeypatch.setattr(validator, "_extract_episode_sections", lambda tactical, ep_start, ep_count: {5: "x" * 350})
    monkeypatch.setattr(
        validator,
        "_validate_tactical_episode_layout",
        lambda episode_sections, expected_eps: (["layout-warning"], 6),
    )
    monkeypatch.setattr(
        validator,
        "_validate_tactical_episode_density",
        lambda episode_sections: (["density-warning"], ["density-suggestion"], 7),
    )
    monkeypatch.setattr(
        validator,
        "_validate_tactical_episode_metadata",
        lambda episode_sections, _arc: (["metadata-warning"], 8),
    )
    monkeypatch.setattr(
        validator,
        "_validate_tactical_relationship_mentions",
        lambda tactical, _arc: (["relationship-warning"], 9),
    )
    monkeypatch.setattr(
        validator,
        "_validate_tactical_action_density",
        lambda tactical: ["action-suggestion"],
    )

    result = validator._validate_tactical_doc(arc)

    assert result["critical"] == []
    assert result["penalty"] == 39
    assert result["warnings"] == [
        "coerce-warning",
        "length=8",
        "layout-warning",
        "density-warning",
        "metadata-warning",
        "relationship-warning",
    ]
    assert result["suggestions"] == ["density-suggestion", "action-suggestion"]
