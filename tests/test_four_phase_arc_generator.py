"""FourPhaseArcGenerator regression tests for pre-collected state normalization."""

from unittest.mock import MagicMock

from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator


def _make_generator() -> FourPhaseArcGenerator:
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen.context = MagicMock()
    gen.context.master_bible = {}
    gen.stats = {
        "total_attempts": 0,
        "phase1_complete": 0,
        "phase2_complete": 0,
        "phase3_pass": 0,
        "phase3_reject": 0,
    }
    gen.preflight = MagicMock()
    gen.preflight.analyze.return_value = {}
    gen.preflight.generate_analyst_injection.return_value = "preflight"
    gen.compiler = MagicMock()
    gen.compiler.compile.return_value = "constraints"
    gen.negative_injector = MagicMock()
    gen.negative_injector.generate_injection.return_value = "neg"
    gen.negative_injector.generate_self_check_prompt.return_value = "self_check"
    gen.negative_injector.record_rejection = MagicMock()
    gen.ensemble = MagicMock()
    gen.ensemble.generate_ensemble.return_value = ({"_ensemble_meta": {"best_strategy": "balanced"}}, [{}])
    gen.validator = MagicMock()
    gen.validator.validate.return_value = ("PASS", {"issues": [], "confidence": 90})
    gen._determine_ep_count = MagicMock(return_value=(5, "reason"))
    gen._generate_prev_context = MagicMock(return_value="prev")
    gen._check_arc_end_state = MagicMock(side_effect=lambda arc: arc)
    return gen


def test_pre_collected_items_normalizes_dict_item_name():
    gen = _make_generator()
    prev_arcs = [
        {
            "state_constraints": {
                "items_acquired": [
                    {"name": "철검"},
                    {"item": "현천패"},
                ]
            }
        }
    ]

    arc, pipeline_result = gen.generate(
        arc_no=1,
        ep_start=1,
        vol_strategy="std",
        curr_block={},
        prev_arcs=prev_arcs,
    )

    assert arc is not None
    assert pipeline_result["final_verdict"] == "PASS"
    pre_collected_items = gen.validator.validate.call_args.kwargs["pre_collected_items"]
    assert "철검" in pre_collected_items
    assert "현천패" in pre_collected_items
    assert "{'name': '철검'}" not in pre_collected_items


def test_pre_collected_grants_normalizes_dict_item_name():
    gen = _make_generator()
    prev_arcs = [
        {
            "state_constraints": {
                "grants_received": [
                    {"name": "공훈패"},
                    {"item": "명예훈장"},
                ]
            }
        }
    ]

    arc, pipeline_result = gen.generate(
        arc_no=1,
        ep_start=1,
        vol_strategy="std",
        curr_block={},
        prev_arcs=prev_arcs,
    )

    assert arc is not None
    assert pipeline_result["final_verdict"] == "PASS"
    pre_collected_grants = gen.validator.validate.call_args.kwargs["pre_collected_grants"]
    assert "공훈패" in pre_collected_grants
    assert "명예훈장" in pre_collected_grants
    assert "{'name': '공훈패'}" not in pre_collected_grants
