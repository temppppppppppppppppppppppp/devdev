from unittest.mock import MagicMock

from modules.core.studio_visualizer import StudioVisualizer


def test_log_emits_operator_event_payload():
    ui = StudioVisualizer()
    ui.console = MagicMock()
    sink = MagicMock()
    ui.set_operator_event_sink(sink)

    ui.log(
        "operator-visible message",
        component="Stage4",
        stage=4,
        ep_num=9,
        round_num=2,
        attempt_key="s4:ep9:arc1:a2:sess_ui",
        meta={"origin": "unit"},
    )

    ui.console.print.assert_called_once()
    event = sink.call_args.args[0]
    assert event["seq"] == 1
    assert event["component"] == "Stage4"
    assert event["stage"] == 4
    assert event["ep_num"] == 9
    assert event["round_num"] == 2
    assert event["attempt_key"] == "s4:ep9:arc1:a2:sess_ui"
    assert event["message"] == "operator-visible message"
    assert event["meta"]["origin"] == "unit"


def test_log_merges_extra_context_into_meta():
    ui = StudioVisualizer()
    ui.console = MagicMock()
    sink = MagicMock()
    ui.set_operator_event_sink(sink)

    ui.log("message", component="UI", custom="value", visible=False)

    event = sink.call_args.args[0]
    assert event["visible"] is False
    assert event["meta"]["custom"] == "value"


def test_prompt_avoids_duplicate_console_render_and_keeps_prompt_metadata():
    ui = StudioVisualizer()
    ui.console = MagicMock()
    ui.console.input.return_value = "3"
    sink = MagicMock()
    ui.set_operator_event_sink(sink)

    result = ui.prompt("prompt: ", component="Stage0")

    assert result == "3"
    ui.console.print.assert_not_called()
    ui.console.input.assert_called_once_with("prompt: ")
    prompt_event = sink.call_args_list[0].args[0]
    response_event = sink.call_args_list[1].args[0]
    assert prompt_event["event_kind"] == "prompt"
    assert prompt_event["message"] == "prompt: "
    assert prompt_event["visible"] is True
    assert response_event["event_kind"] == "prompt_response"
    assert response_event["message"] == "[prompt_response]"
    assert response_event["selection_value"] == "3"
    assert response_event["meta"]["prompt_text"] == "prompt: "
