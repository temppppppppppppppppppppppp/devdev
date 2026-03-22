from tests.test_four_phase_arc_generator import _make_generator


def test_run_generation_patch_attempt_marks_patch_pass():
    gen = _make_generator()
    gen.patch_arc_with_feedback = lambda **_: ({"tactical_doc": "patched"}, {"final_verdict": "PASS"})
    pipeline_result = {"phases": {}}

    envelope = gen.runtime._run_generation_patch_attempt(
        retry=1,
        arc_no=2,
        ep_start=6,
        vol_strategy="std",
        curr_block={},
        prev_arcs=[],
        assets=None,
        protagonist_name="주인공",
        entity_registry=None,
        state_tracker=None,
        vector_context="",
        adversarial_self_play=None,
        prev_rejected_arc={"tactical_doc": "rejected"},
        prev_reject_feedback="fix this",
        pipeline_result=pipeline_result,
    )

    assert envelope.patch_succeeded is True
    assert envelope.best_arc["tactical_doc"] == "patched"
    assert pipeline_result["patch_used"] is True
    assert pipeline_result["final_verdict"] == "PASS"
    assert pipeline_result["phases"]["generate"]["selected_strategy"] == "patch"
