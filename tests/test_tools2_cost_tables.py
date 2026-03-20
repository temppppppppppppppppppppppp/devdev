import io
import runpy
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from modules.core.metrics_collector import MODEL_COSTS


ROOT = Path(__file__).resolve().parent.parent


def _run_script(path: str) -> dict:
    with redirect_stdout(io.StringIO()):
        return runpy.run_path(str(ROOT / path), run_name="__main__")


def test_cost_calculation_uses_runtime_cost_table():
    data = _run_script("tools2/cost_calculation.py")
    flash = MODEL_COSTS["gemini-2.5-flash"]
    pro = MODEL_COSTS["gemini-2.5-pro"]

    assert data["director_cost_per_call"] == pytest.approx(
        (data["director_input"] / 1_000_000 * flash["input"]) + (data["director_output"] / 1_000_000 * flash["output"])
    )
    assert data["architect_cost_per_call"] == pytest.approx(
        (data["architect_input"] / 1_000_000 * flash["input"])
        + (data["architect_output"] / 1_000_000 * flash["output"])
    )
    assert data["advisory_cost"] == pytest.approx(
        (data["advisory_input"] / 1_000_000 * flash["input"]) + (data["advisory_output"] / 1_000_000 * flash["output"])
    )
    assert data["writer_cost_per_call"] == pytest.approx(
        (data["writer_input"] / 1_000_000 * pro["input"]) + (data["writer_output"] / 1_000_000 * pro["output"])
    )
    assert data["scoring_cost"] == pytest.approx(
        (data["scoring_input"] / 1_000_000 * pro["input"]) + (data["scoring_output"] / 1_000_000 * pro["output"])
    )


def test_full_project_cost_uses_runtime_cost_table():
    data = _run_script("tools2/full_project_cost.py")
    flash = MODEL_COSTS["gemini-2.5-flash"]
    pro = MODEL_COSTS["gemini-2.5-pro"]

    assert data["bible_cost"] == pytest.approx(
        (data["analyst_bible_input"] / 1_000_000 * pro["input"])
        + (data["analyst_bible_output"] / 1_000_000 * pro["output"])
    )
    assert data["volume_cost"] == pytest.approx(
        (data["analyst_volume_input"] / 1_000_000 * pro["input"])
        + (data["analyst_volume_output"] / 1_000_000 * pro["output"])
    )
    assert data["arc_cost"] == pytest.approx(
        (data["analyst_arc_input"] / 1_000_000 * pro["input"])
        + (data["analyst_arc_output"] / 1_000_000 * pro["output"])
    )
    assert data["weaver_cost"] == pytest.approx(
        (data["weaver_input"] / 1_000_000 * pro["input"]) + (data["weaver_output"] / 1_000_000 * pro["output"])
    )
    assert data["writer_cost"] == pytest.approx(
        (data["writer_input"] / 1_000_000 * pro["input"]) + (data["writer_output"] / 1_000_000 * pro["output"])
    )
    assert data["scoring_cost"] == pytest.approx(
        (data["scoring_input"] / 1_000_000 * pro["input"]) + (data["scoring_output"] / 1_000_000 * pro["output"])
    )
    assert data["director_arc_cost"] == pytest.approx(
        (data["director_arc_input"] / 1_000_000 * flash["input"])
        + (data["director_arc_output"] / 1_000_000 * flash["output"])
    )
    assert data["architect_cost"] == pytest.approx(
        (data["architect_input"] / 1_000_000 * flash["input"])
        + (data["architect_output"] / 1_000_000 * flash["output"])
    )
    assert data["director_bp_cost"] == pytest.approx(
        (data["director_bp_input"] / 1_000_000 * flash["input"])
        + (data["director_bp_output"] / 1_000_000 * flash["output"])
    )
    assert data["director_ms_cost"] == pytest.approx(
        (data["director_ms_input"] / 1_000_000 * flash["input"])
        + (data["director_ms_output"] / 1_000_000 * flash["output"])
    )
    assert data["advisory_cost"] == pytest.approx(
        (data["advisory_input"] / 1_000_000 * flash["input"]) + (data["advisory_output"] / 1_000_000 * flash["output"])
    )
