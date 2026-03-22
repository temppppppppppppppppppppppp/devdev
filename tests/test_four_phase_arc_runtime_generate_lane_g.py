from unittest.mock import MagicMock

from modules.domain.agents.four_phase_arc_runtime import (
    _FourPhaseConstraintEnvelope,
    _FourPhaseGenerationEnvelope,
)
from tests.test_four_phase_arc_generator import _make_generator


def test_run_generate_retry_cycle_short_circuits_on_generation_continue():
    gen = _make_generator()
    state = gen.runtime._initialize_generate_state(
        arc_no=1,
        curr_block={},
        prev_arcs=[],
        director_feedback="",
    )
    pipeline_result = state.pipeline_result
    gen.runtime._resolve_constraint_phase = MagicMock(
        return_value=_FourPhaseConstraintEnvelope(
            full_constraint_block="constraints",
            preflight_result={},
            cached_constraint_block=None,
            cached_preflight=None,
        )
    )
    gen.runtime._run_generation_phase = MagicMock(
        return_value=_FourPhaseGenerationEnvelope(
            best_arc=None,
            all_candidates=[],
            prev_arc_context="",
            feedback="retry feedback",
            prev_rejected_arc=None,
            prev_reject_feedback="",
            prev_selected_strategy="",
            spare_candidates=[],
            should_continue=True,
        )
    )
    gen.runtime._prepare_candidates_for_selection = MagicMock()

    envelope = gen.runtime._run_generate_retry_cycle(
        retry=0,
        arc_no=1,
        ep_start=1,
        vol_strategy="std",
        curr_block={},
        prev_arcs=[],
        assets=None,
        max_internal_retries=1,
        protagonist_name="주인공",
        entity_registry=None,
        state_tracker=None,
        vector_context="",
        adversarial_self_play=None,
        director=None,
        state=state,
        pipeline_result=pipeline_result,
    )

    assert envelope.should_continue is True
    assert envelope.should_return is False
    assert state.feedback == "retry feedback"
    gen.runtime._prepare_candidates_for_selection.assert_not_called()
