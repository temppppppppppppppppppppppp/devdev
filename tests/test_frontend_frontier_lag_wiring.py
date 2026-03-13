from pathlib import Path


INDEX_HTML = Path("geuldobi-desktop/src/index.html").read_text(encoding="utf-8")


def test_frontier_lag_button_is_exposed_in_run_panel():
    assert 'data-action="one_stop_frontier_lag"' in INDEX_HTML
    assert 'data-key="7"' in INDEX_HTML
    assert ">Frontier Lag<" in INDEX_HTML


def test_frontier_lag_action_meta_is_registered():
    assert 'one_stop_frontier_lag: { title: "Frontier Lag"' in INDEX_HTML
    assert 'short: "FRONTIER"' in INDEX_HTML


def test_frontier_lag_is_in_pipeline_order_and_animation_sets():
    assert 'const PIPELINE_ORDER = ["stage_0", "stage_2", "stage_3", "stage_4", "one_stop", "one_stop_frontier_lag"]' in INDEX_HTML
    assert 'const ANIMATED_STAGES = new Set(["stage_2", "stage_3", "stage_4", "one_stop", "one_stop_frontier_lag"])' in INDEX_HTML


def test_frontier_lag_agents_and_current_stage_union_are_registered():
    assert '"stage_0" | "stage_2" | "stage_3" | "stage_4" | "one_stop" | "one_stop_frontier_lag" | null' in INDEX_HTML
    assert 'one_stop_frontier_lag: ["writer", "director", "analyst", "critic", "manager"]' in INDEX_HTML


def test_existing_one_stop_button_remains_present():
    assert 'data-action="one_stop"' in INDEX_HTML
    assert 'data-key="6"' in INDEX_HTML
    assert ">One-Stop<" in INDEX_HTML
