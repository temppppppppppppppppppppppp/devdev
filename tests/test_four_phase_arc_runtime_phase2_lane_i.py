from tests.test_four_phase_arc_generator import _make_generator


def test_prepare_director_candidate_input_filters_force_reject_and_blank_tactical_doc():
    gen = _make_generator()

    envelope = gen.runtime._prepare_director_candidate_input(
        all_candidates=[
            {"_strategy": "bad", "tactical_doc": "reject me"},
            {"_strategy": "good", "tactical_doc": "keep me"},
            {"_strategy": "blank", "tactical_doc": ""},
        ],
        candidate_quality_flags=[
            {"force_reject": True},
            {"force_reject": False, "note": "ok"},
            {"force_reject": False},
        ],
    )

    assert envelope.valid_for_director == [{"_strategy": "good", "tactical_doc": "keep me"}]
    assert envelope.valid_quality_flags == [{"force_reject": False, "note": "ok"}]
