from pathlib import Path

from modules.core.constants import Stage2Limits, VolumeSettings
from modules.domain.agents.analyst import Analyst


def test_stage2_pacing_constants_align_with_live_two_to_six_contract():
    assert Stage2Limits.MIN_EP_COUNT == 2
    assert Stage2Limits.MAX_EP_COUNT == 6
    assert VolumeSettings.MIN_EPISODES_PER_ARC == 2
    assert VolumeSettings.MAX_EPISODES_PER_ARC == 6


def test_analyst_fallback_allows_two_episode_blitz_lane():
    analyst = Analyst.__new__(Analyst)
    draft_result, actual_ep_count = analyst._normalize_single_arc_draft_result(
        {
            "ep_count": 2,
            "pacing_decision": {
                "chosen_pacing": "Blitz(2-3화)",
            },
            "beat_sequence": ["도입", "전개"],
        },
        target_ep_count=3,
        min_ep_count=2,
        max_ep_count=6,
    )

    assert actual_ep_count == 2
    assert draft_result["ep_count"] == 2


def test_active_prompt_surfaces_use_live_pacing_contract_wording():
    ensemble_text = Path("config/prompts/ensemble.yaml").read_text(encoding="utf-8")
    analyst_text = Path("config/prompts/analyst.yaml").read_text(encoding="utf-8")

    assert "ep_count × 450" in ensemble_text
    assert "화당 450자 이상" in ensemble_text
    assert "2~6 중 최종 결정" in ensemble_text

    assert "ep_count × 450" in analyst_text
    assert "Blitz(2~3화), Standard(4~5화), Epic(6화)" in analyst_text
    assert "또는 2~6 중 사건 밀도에 맞게 직접 결정" in analyst_text
