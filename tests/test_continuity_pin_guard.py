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


def test_apply_continuity_pins_marks_opening_action_reversal_against_previous_exit():
    blueprint = {
        "integrated_scenario": (
            "집을 나서려던 한시우는 아버지의 부름에 걸음을 멈췄다. "
            "천천히 몸을 돌려 아버지를 마주 보자, 아버지는 그를 서재로 불렀고 "
            "한시우는 그의 뒤를 따라 복도를 걸었다."
        ),
        "scene_breakdown": {
            "scene_1": "한시우가 걸음을 멈추고 아버지를 마주 본다.",
            "scene_2": "한시우가 아버지의 뒤를 따라 서재로 향한다.",
        },
    }

    result = apply_continuity_pins(
        blueprint,
        previous_published_text=(
            "아버지의 목소리가 등 뒤에서 들려왔지만 그는 멈추지 않았다. "
            "오히려 손에 힘을 주어 현관문 손잡이를 단단히 움켜쥐고 "
            "현관문을 향해 나아갔다."
        ),
        arc_tactical_text="",
    )

    assert result["blueprint"]["integrated_scenario"] == blueprint["integrated_scenario"]
    opening_pin = next(change for change in result["changes"] if change["type"] == "opening_action_continuity_pin")
    assert opening_pin["before"].startswith("멈추지 않")
    assert "걸음을 멈춤" in opening_pin["observed"]
    assert "몸을 돌림" in opening_pin["observed"]
