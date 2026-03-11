from modules.core.continuity_pin_guard import apply_continuity_pins


def test_apply_continuity_pins_replaces_proper_noun_from_previous_text():
    blueprint = {
        "integrated_scenario": '주인공은 "이클립스"를 마지막으로 쓰다듬었다.',
        "ending_hook": '"이클립스"를 보며 결심했다.',
    }

    result = apply_continuity_pins(
        blueprint,
        previous_published_text='직전 원고에는 "아퀼라"만 나온다.',
        arc_tactical_text="",
    )

    patched = result["blueprint"]
    assert '"아퀼라"' in patched["integrated_scenario"]
    assert '"아퀼라"' in patched["ending_hook"]
    assert any(change["type"] == "proper_noun_pin" for change in result["changes"])


def test_apply_continuity_pins_replaces_elapsed_time_bucket_from_arc_tactical():
    blueprint = {
        "integrated_scenario": "다음 날 오후 그는 사무실에 도착했다.",
        "ending_hook": "다음 날 오후 계약을 마무리한다.",
    }

    result = apply_continuity_pins(
        blueprint,
        previous_published_text="",
        arc_tactical_text="약 2주 후 주인공은 처음으로 회사를 세운다.",
    )

    patched = result["blueprint"]
    assert "약 2주 후" in patched["integrated_scenario"]
    assert "약 2주 후" in patched["ending_hook"]
    assert any(change["type"] == "elapsed_time_pin" for change in result["changes"])
