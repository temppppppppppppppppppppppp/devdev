import logging

from modules.domain.agents.director_ensemble import _log_director_frame


def test_log_director_frame_emits_summary_details_and_thinking(caplog):
    with caplog.at_level(logging.DEBUG):
        _log_director_frame(
            stage="stage4",
            ep_num=8,
            decision="PASS_WITH_FIX",
            score=82,
            selected_label="B",
            selection_reason="selected for fixable structure",
            verdict_reason="needs structural repair",
            comparison_notes="candidate B preserved continuity",
            contradictions=["continuity gap in final beat"],
            fix_scope="partial",
            open_review="tighten the transition scene",
            thinking="compare candidate A and B for continuity risk",
        )

    assert "[DirectorFrame] stage=stage4 ep=8 verdict=PASS_WITH_FIX score=82 selected=B fix_scope=partial contradictions=1" in caplog.text
    assert "selection_reason=selected for fixable structure" in caplog.text
    assert "verdict_reason=needs structural repair" in caplog.text
    assert "comparison=candidate B preserved continuity" in caplog.text
    assert "open_review=tighten the transition scene" in caplog.text
    assert "contradiction_count=1" in caplog.text
    assert "[DirectorThinking] stage=stage4 ep=8 compare candidate A and B for continuity risk" in caplog.text
