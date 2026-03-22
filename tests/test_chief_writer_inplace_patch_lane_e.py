import json
from unittest.mock import MagicMock, patch

from modules.domain.agents.chief_writer import ChiefWriter


def _make_writer() -> ChiefWriter:
    writer = ChiefWriter.__new__(ChiefWriter)
    writer._last_inplace_patch_trace = {}
    writer._inplace_patch_blueprint = None
    writer._inplace_patch_genre_name = ""
    writer.ask = MagicMock()
    return writer


def test_resolve_inplace_patch_strategy_records_fix_pack_targets_without_structural_attempt():
    writer = _make_writer()

    result, focus, fallback_reason, structural_attempted = writer._resolve_inplace_patch_strategy(
        original_manuscript="original manuscript " * 160,
        director_feedback="fix only continuity",
        attempt_number=1,
        style_guide="",
        normalized_fix_pack={"patch_targets": ["anchor_a", "anchor_b"]},
    )

    assert result is None
    assert focus == ""
    assert fallback_reason == ""
    assert structural_attempted is False
    assert writer._last_inplace_patch_trace == {
        "patch_strategy": "inplace_patch",
        "patch_targets": ["anchor_a", "anchor_b"],
        "fallback_reason": "",
        "focus": "",
        "structural_attempted": False,
    }


def test_resolve_inplace_patch_strategy_returns_structural_result_when_available():
    writer = _make_writer()
    writer._inplace_patch_blueprint = {
        "scene_breakdown": {
            "scene_1": {"description": "opening"},
            "scene_2": {"description": "ending"},
        }
    }

    structural_result = [
        {
            "manuscript": "patched manuscript " * 140,
            "strategy": "inplace_patch_structural",
            "state_updates": {"ending": "tightened"},
            "patch_targets": ["scene_2"],
        }
    ]

    with (
        patch.object(writer, "_classify_structural_patch_focus", return_value="ending"),
        patch.object(writer, "_attempt_structural_inplace_patch", return_value=structural_result) as mock_structural,
    ):
        result, focus, fallback_reason, structural_attempted = writer._resolve_inplace_patch_strategy(
            original_manuscript="original manuscript " * 160,
            director_feedback="ending needs a local fix",
            attempt_number=2,
            style_guide="keep tone",
            normalized_fix_pack={},
        )

    assert result == structural_result
    assert focus == "ending"
    assert fallback_reason == ""
    assert structural_attempted is True
    mock_structural.assert_called_once()


def test_inplace_patch_shell_returns_structural_result_without_llm_call():
    writer = _make_writer()

    structural_result = [
        {
            "manuscript": "patched manuscript " * 140,
            "strategy": "inplace_patch_structural",
            "state_updates": {"ending": "tightened"},
            "patch_targets": ["scene_2"],
        }
    ]

    with (
        patch.object(writer, "_normalize_fix_pack", return_value={}),
        patch.object(writer, "_build_fix_pack_guidance", return_value=""),
        patch.object(
            writer,
            "_resolve_inplace_patch_strategy",
            return_value=(structural_result, "ending", "", True),
        ) as mock_resolve,
    ):
        result = writer.inplace_patch(
            original_manuscript="original manuscript " * 160,
            director_feedback="ending needs a local fix",
            attempt_number=3,
        )

    assert result == structural_result
    mock_resolve.assert_called_once()
    writer.ask.assert_not_called()
