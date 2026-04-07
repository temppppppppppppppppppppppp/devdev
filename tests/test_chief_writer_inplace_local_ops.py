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


def test_inplace_patch_uses_deterministic_local_ops_for_local_sentence_fix_pack():
    writer = _make_writer()
    original = (
        "첫 문단은 그대로 둔다.\n\n"
        "여기서 잘못된 문장이다. 바로 뒤 문장은 그대로 남아야 한다.\n\n"
        "마지막 문단도 그대로 둔다."
    )
    writer.ask.return_value = json.dumps(
        {
            "operations": [
                {
                    "op": "replace",
                    "old_text": "여기서 잘못된 문장이다.",
                    "new_text": "여기서 수정된 문장이다.",
                    "anchor_before": "첫 문단은 그대로 둔다.",
                    "anchor_after": "바로 뒤 문장은 그대로 남아야 한다.",
                }
            ],
            "patch_state_updates": {"tone": "stable"},
        },
        ensure_ascii=False,
    )

    result = writer.inplace_patch(
        original_manuscript=original,
        director_feedback="둘째 문단의 잘못된 문장만 고쳐라",
        attempt_number=1,
        fix_pack={
            "patch_targets": ["scene_2"],
            "must_fix": ["잘못된 문장만 교정"],
            "do_not_regress": ["문단 구조", "나머지 문장"],
            "success_condition": "둘째 문단의 지정 문장만 바뀐다.",
            "target_kind": "local_sentence",
        },
    )

    assert result == [
        {
            "manuscript": original.replace("여기서 잘못된 문장이다.", "여기서 수정된 문장이다."),
            "strategy": "inplace_patch_local_ops",
            "state_updates": {"tone": "stable"},
            "patch_targets": ["scene_2"],
        }
    ]
    assert writer.ask.call_count == 1
    assert writer._last_inplace_patch_trace["patch_strategy"] == "inplace_patch_local_ops"
    assert writer._last_inplace_patch_trace["patch_targets"] == ["scene_2"]
    assert writer._last_inplace_patch_trace["fallback_reason"] == ""
    assert writer._last_inplace_patch_trace["focus"] == ""
    assert writer._last_inplace_patch_trace["structural_attempted"] is False
    assert writer._last_inplace_patch_trace["target_kind"] == "local_sentence"
    assert writer._last_inplace_patch_trace["patch_target_records"][0]["summary"] == "scene_2"
    assert writer._last_inplace_patch_trace["repair_trace"][0]["old_excerpt"] == "여기서 잘못된 문장이다."
    assert writer._last_inplace_patch_trace["repair_trace"][0]["new_excerpt"] == "여기서 수정된 문장이다."


def test_inplace_patch_falls_back_to_whole_text_when_local_ops_are_unusable():
    writer = _make_writer()
    original = "original manuscript " * 170
    whole_text_patch = "patched manuscript " * 150
    writer.ask.side_effect = [
        json.dumps(
            {
                "operations": [
                    {
                        "op": "replace",
                        "old_text": "missing anchor text",
                        "new_text": "replacement text",
                        "anchor_before": "",
                        "anchor_after": "",
                    }
                ],
                "patch_state_updates": {},
            },
            ensure_ascii=False,
        ),
        json.dumps(
            {
                "content": whole_text_patch,
                "patch_state_updates": {"location": "renamed"},
            },
            ensure_ascii=False,
        ),
    ]

    with patch("modules.core.prompt_loader.PromptLoader.load", return_value=None):
        result = writer.inplace_patch(
            original_manuscript=original,
            director_feedback="opening label만 바꿔라",
            attempt_number=1,
            fix_pack={
                "patch_targets": ["opening_location_name"],
                "must_fix": ["opening label correction"],
                "do_not_regress": ["scene order"],
                "success_condition": "지정된 label만 교정",
                "target_kind": "entity_ref",
            },
        )

    assert result == [
        {
            "manuscript": whole_text_patch,
            "strategy": "inplace_patch",
            "state_updates": {"location": "renamed"},
            "patch_targets": ["opening_location_name"],
        }
    ]
    assert writer.ask.call_count == 2
    assert writer._last_inplace_patch_trace["patch_strategy"] == "inplace_patch"
    assert writer._last_inplace_patch_trace["patch_targets"] == ["opening_location_name"]
    assert writer._last_inplace_patch_trace["fallback_reason"] == "op_1_apply_failed"
    assert writer._last_inplace_patch_trace["focus"] == ""
    assert writer._last_inplace_patch_trace["structural_attempted"] is False
    assert writer._last_inplace_patch_trace["target_kind"] == "entity_ref"
    assert writer._last_inplace_patch_trace["patch_target_records"][0]["summary"] == "opening_location_name"
