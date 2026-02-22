"""TF-3 Tier-1 장르 완전성 회귀 테스트."""

import pytest

from modules.core.narrative_diversity import NarrativeDiversityEngine
from modules.domain.agents.state_tracker_npc import StateTrackerNPC
from modules.validation.scoring_validator import ScoringValidator


def test_scoring_validator_thresholds_cover_all_supported_genres():
    expected = {
        "wuxia",
        "hunter",
        "investment",
        "fantasy",
        "composer",
        "cooking",
        "alt_history",
        "actor",
        "sports",
        "medical",
    }
    assert expected.issubset(ScoringValidator.GENRE_THRESHOLDS)


@pytest.mark.parametrize(
    "genre",
    ["fantasy", "composer", "cooking", "alt_history", "actor", "sports", "medical"],
)
def test_scoring_validator_genre_specific_feedback_for_extended_genres(genre):
    validator = ScoringValidator(client=None, genre=genre)
    feedback = validator._get_genre_specific_feedback("", {}, genre)

    assert isinstance(feedback, list)
    assert feedback


def test_state_tracker_skill_log_label_has_composer_and_alt_history():
    labels = StateTrackerNPC._SKILL_LOG_LABEL
    assert "composer" in labels
    assert "alt_history" in labels
    assert labels["composer"][1]
    assert labels["alt_history"][1]


def test_narrative_diversity_contrastive_examples_include_fantasy_and_composer():
    examples = NarrativeDiversityEngine.CONTRASTIVE_EXAMPLES
    for genre in ("fantasy", "composer"):
        assert genre in examples
        assert "이렇게 쓰지 마라" in examples[genre]
