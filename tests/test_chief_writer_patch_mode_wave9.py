import json
from unittest.mock import MagicMock, patch

from modules.domain.agents.chief_writer import ChiefWriter


def _make_writer() -> ChiefWriter:
    writer = ChiefWriter.__new__(ChiefWriter)
    writer._last_inplace_patch_trace = {}
    writer._inplace_patch_blueprint = None
    writer._inplace_patch_genre_name = ""
    writer.ask = MagicMock()
    writer.generate_ensemble = MagicMock()
    return writer


def test_extract_inplace_patch_payload_strips_korean_end_marker():
    writer = _make_writer()
    patched = ("patched manuscript " * 140) + "[원고_끝]"

    payload = writer._extract_inplace_patch_payload(
        json.dumps(
            {
                "content": patched,
                "patch_state_updates": {"tone": "dry"},
            },
            ensure_ascii=False,
        )
    )

    assert payload == (patched[: -len("[원고_끝]")].rstrip(), {"tone": "dry"})


def test_inplace_patch_shell_delegates_prompt_payload_and_result_helpers():
    writer = _make_writer()
    built_result = [{"manuscript": "patched manuscript " * 140, "strategy": "inplace_patch"}]

    with (
        patch.object(writer, "_normalize_fix_pack", return_value={}) as mock_normalize,
        patch.object(writer, "_build_fix_pack_guidance", return_value="GUIDE") as mock_guidance,
        patch.object(
            writer,
            "_resolve_inplace_patch_strategy",
            return_value=(None, "focus", "fallback", True),
        ) as mock_resolve,
        patch.object(writer, "_build_inplace_patch_prompt", return_value="PROMPT") as mock_prompt,
        patch.object(
            writer,
            "_extract_inplace_patch_payload",
            return_value=("patched manuscript " * 140, {"tone": "dry"}),
        ) as mock_payload,
        patch.object(writer, "_build_inplace_patch_result", return_value=built_result) as mock_result,
    ):
        writer.ask.return_value = "RAW RESPONSE"
        result = writer.inplace_patch(
            original_manuscript="original manuscript " * 160,
            director_feedback="fix continuity only",
            attempt_number=4,
            style_guide="keep tone",
            fix_pack={"patch_targets": ["anchor_a"]},
        )

    assert result == built_result
    mock_normalize.assert_called_once_with({"patch_targets": ["anchor_a"]})
    mock_guidance.assert_called_once_with({})
    mock_resolve.assert_called_once()
    mock_prompt.assert_called_once_with(
        original_manuscript="original manuscript " * 160,
        director_feedback="fix continuity only",
        style_guide="keep tone",
        fix_pack_guidance="GUIDE",
    )
    writer.ask.assert_called_once_with("PROMPT", temperature=0.3, thinking_level="medium")
    mock_payload.assert_called_once_with("RAW RESPONSE")
    mock_result.assert_called_once_with(
        manuscript="patched manuscript " * 140,
        state_updates={"tone": "dry"},
        normalized_fix_pack={},
        fallback_reason="fallback",
        focus="focus",
        structural_attempted=True,
    )


def test_build_patch_with_feedback_director_feedback_appends_history_and_fix_pack():
    writer = _make_writer()

    with (
        patch.object(writer, "_build_retry_history_feedback", return_value="[history]"),
        patch.object(writer, "_build_fix_pack_guidance", return_value="[fix-pack]"),
    ):
        result = writer._build_patch_with_feedback_director_feedback(
            patch_section="[section]",
            attempt_number=3,
            previous_attempt={"fix_pack": {"patch_targets": ["anchor_a"]}},
        )

    assert "[🔧 3차 수정" in result
    assert "[section]" in result
    assert "[history]" in result
    assert "[fix-pack]" in result


def test_build_fix_pack_guidance_includes_patch_target_records():
    writer = _make_writer()

    result = writer._build_fix_pack_guidance(
        {
            "patch_targets": ["scene_1"],
            "patch_target_records": [
                {
                    "summary": "opening transition",
                    "scene_id": "scene_1",
                    "target_kind": "scene_boundary",
                    "paragraph_span": {"start": 1, "end": 3},
                }
            ],
            "must_fix": ["make the opening bridge explicit"],
            "target_kind": "scene_boundary",
        }
    )

    assert "patch_target_records" in result
    assert "summary=opening transition" in result
    assert "scene_id=scene_1" in result
    assert "target_kind=scene_boundary" in result
    assert "paragraph_span=1-3" in result


def test_patch_with_feedback_shell_uses_extracted_patch_helpers():
    writer = _make_writer()
    writer.generate_ensemble.return_value = [{"manuscript": "patched"}]
    previous_attempt = {
        "selected_strategy_key": "strategy_a",
        "fix_pack": {
            "patch_targets": ["anchor_a"],
            "must_fix": ["fix the selected sentence"],
            "do_not_regress": ["preserve the surrounding paragraph"],
            "success_condition": "selected sentence corrected",
            "target_kind": "local_sentence",
        },
    }

    with (
        patch.object(writer, "_build_patch_with_feedback_section", return_value="[section]") as mock_section,
        patch.object(
            writer,
            "_build_patch_with_feedback_director_feedback",
            return_value="[enhanced]",
        ) as mock_feedback,
        patch.object(
            writer,
            "_build_patch_with_feedback_retry_args",
            return_value=("constraints", "strategy_a", "selection note", {"strategy_a": "selection note"}),
        ) as mock_retry_args,
    ):
        result = writer.patch_with_feedback(
            ep_num=7,
            blueprint={"ep_num": 7},
            prev_manuscript="prev",
            hud_report="hud",
            arc_doc="arc",
            master_bible={},
            style_guide="keep tone",
            original_manuscript="original manuscript " * 160,
            director_feedback="fix continuity only",
            previous_attempt=previous_attempt,
            attempt_number=2,
        )

    assert result == [{"manuscript": "patched"}]
    mock_section.assert_called_once()
    mock_feedback.assert_called_once_with(
        patch_section="[section]",
        attempt_number=2,
        previous_attempt=previous_attempt,
    )
    mock_retry_args.assert_called_once_with(previous_attempt)
    kwargs = writer.generate_ensemble.call_args.kwargs
    assert kwargs["director_feedback"] == "[enhanced]"
    assert kwargs["failure_constraints"] == "constraints"
    assert kwargs["rejected_strategy"] == "strategy_a"
    assert kwargs["single_strategy"] == "strategy_a"
    assert kwargs["strategy_specific_feedback"] == "selection note"
    assert kwargs["strategy_feedback_map"] == {"strategy_a": "selection note"}
