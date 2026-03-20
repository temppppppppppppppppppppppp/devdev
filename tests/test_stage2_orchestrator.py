from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.constants import VolumeSettings
from modules.core.stage2_orchestrator import Stage2Orchestrator


def _make_ctx(arcs, calculate_arc_from_episode=None):
    ui = MagicMock()
    ui.log = MagicMock()
    return SimpleNamespace(
        ui=ui,
        current_project=SimpleNamespace(arcs=arcs),
        calculate_arc_from_episode=calculate_arc_from_episode,
    )


def test_resolve_arc_number_for_episode_uses_actual_arc_boundaries_when_callback_missing():
    ctx = _make_ctx(
        arcs=[
            {"arc_no": 1, "ep_start": 1, "ep_end": 4},
            {"arc_no": 2, "ep_start": 5, "ep_end": 7},
            {"arc_no": 3, "ep_start": 8, "ep_end": 11},
        ]
    )
    orch = Stage2Orchestrator(app=MagicMock(), context=ctx)

    result = orch._resolve_arc_number_for_episode(5)

    assert result == 2
    ctx.ui.log.assert_any_call("⚠️ [Stage2] arc mapping callback 부재 - fallback 사용")


def test_resolve_arc_number_for_episode_falls_back_to_default_bucket_when_boundaries_missing():
    ctx = _make_ctx(arcs=[{"arc_no": 1, "ep_start": 1, "ep_end": 4}])
    orch = Stage2Orchestrator(app=MagicMock(), context=ctx)

    result = orch._resolve_arc_number_for_episode(9)

    expected = (9 - 1) // VolumeSettings.EPISODES_PER_ARC + 1
    assert result == expected


def test_fit_prompt_text_preserves_tail_context_for_failure_report():
    orch = Stage2Orchestrator(app=MagicMock(), context=_make_ctx(arcs=[]))

    text = "HEAD-CONSTRAINT\n" + ("C" * 8000) + "\nTAIL-STAGE2-CONSTRAINT"
    result = orch._fit_prompt_text(text, 6000)

    assert "TAIL-STAGE2-CONSTRAINT" in result
    assert "...(중간 생략)..." in result


def test_stage2_failure_report_source_normalizes_constraints_before_reporting():
    src = Path("modules/core/stage2_orchestrator.py").read_text(encoding="utf-8")

    assert "current_constraints = self._fit_prompt_text(" in src
    assert "constraint_db.generate_constraint_block(global_arc_no) if constraint_db else \"N/A\"" in src
