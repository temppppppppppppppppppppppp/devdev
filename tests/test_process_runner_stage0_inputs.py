from modules.api.process_runner import ProcessRunner, _resolve_stage0_style_cache_choice


def test_resolve_stage0_style_cache_choice_maps_modes():
    assert _resolve_stage0_style_cache_choice({"stage0_style_cache_mode": "use"}) == "1"
    assert _resolve_stage0_style_cache_choice({"stage0_style_cache_mode": "refresh"}) == "2"
    assert _resolve_stage0_style_cache_choice({"stage0_style_cache_mode": "reset"}) == "3"
    assert _resolve_stage0_style_cache_choice({"stage0_style_cache_mode": "unknown"}) is None


def test_mode_b_stage0_style_analysis_injects_cache_choice():
    runner = ProcessRunner()
    runner._mode = "B"
    seq = runner._build_stdin_sequence("0", "6", {"stage0_style_cache_mode": "reset"})
    lines = seq.split("\n")
    assert lines[3] == "0"
    assert lines[4] == "6"
    assert lines[5] == "y"
    assert lines[6] == "3"


def test_mode_b_stage0_work_guard_does_not_inject_style_cache_choice():
    runner = ProcessRunner()
    runner._mode = "B"
    seq = runner._build_stdin_sequence("0", "7", {"stage0_style_cache_mode": "refresh"})
    lines = seq.split("\n")
    assert lines[3] == "0"
    assert lines[4] == "7"
    assert lines[5] == ""
