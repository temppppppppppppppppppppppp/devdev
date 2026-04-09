from unittest.mock import MagicMock

from modules.core.confidence_calibration import ConfidenceCalibrator, ConfidenceLevel, ConfidenceResult


def test_assess_manuscript_delegates_to_helper_family():
    calibrator = ConfidenceCalibrator()
    expected = ConfidenceResult(
        score=77,
        level=ConfidenceLevel.HIGH,
        factors={"length_adequacy": 10},
        concerns=["seed"],
        needs_extra_verification=False,
        recommendation="verify",
    )
    calibrator._score_manuscript_length = MagicMock(return_value=10)
    calibrator._score_manuscript_structure = MagicMock(return_value=11)
    calibrator._score_manuscript_continuity = MagicMock(return_value=12)
    calibrator._score_manuscript_dialogue = MagicMock(return_value=13)
    calibrator._score_manuscript_sensory = MagicMock(return_value=14)
    calibrator._score_manuscript_scene_coverage = MagicMock(return_value=15)
    calibrator._score_manuscript_ending_hook = MagicMock(return_value=16)
    calibrator._build_confidence_result = MagicMock(return_value=expected)

    result = calibrator._assess_manuscript("manuscript text", {"blueprint": {"scene_breakdown": {}}})

    assert result is expected
    calibrator._score_manuscript_length.assert_called_once()
    calibrator._score_manuscript_structure.assert_called_once()
    calibrator._score_manuscript_continuity.assert_called_once()
    calibrator._score_manuscript_dialogue.assert_called_once()
    calibrator._score_manuscript_sensory.assert_called_once()
    calibrator._score_manuscript_scene_coverage.assert_called_once()
    calibrator._score_manuscript_ending_hook.assert_called_once()
    calibrator._build_confidence_result.assert_called_once_with(
        factors={
            "length_adequacy": 10,
            "structure_quality": 11,
            "continuity_signals": 12,
            "dialogue_ratio": 13,
            "sensory_detail": 14,
            "scene_coverage": 15,
            "ending_hook": 16,
        },
        concerns=[],
    )


def test_score_manuscript_scene_coverage_flags_low_match_ratio():
    calibrator = ConfidenceCalibrator()
    concerns = []
    manuscript = "주인공은 시장에 도착했다."
    context = {
        "blueprint": {
            "scene_breakdown": {
                "scene1": {
                    "summary": "시장 잠입",
                    "key_events": ["봉인 확인", "경비 회피", "탈출"]
                }
            }
        }
    }

    score = calibrator._score_manuscript_scene_coverage(manuscript, context, concerns)

    assert score == 5
    assert concerns == ["Blueprint 씬 반영 부족"]


def test_score_manuscript_continuity_reports_missing_overlap():
    calibrator = ConfidenceCalibrator()
    concerns = []

    score = calibrator._score_manuscript_continuity(
        "새로운 도시에서 전혀 다른 인물만 등장한다.",
        {"prev_manuscript": "검은 검을 든 주인공이 봉인된 문을 열었다."},
        concerns,
    )

    assert score == 5
    assert concerns == ["직전 화와의 연결이 거의 없음"]


def test_build_confidence_result_uses_thresholds_without_behavior_change():
    calibrator = ConfidenceCalibrator()

    result = calibrator._build_confidence_result(
        factors={
            "length_adequacy": 15,
            "structure_quality": 20,
            "continuity_signals": 20,
            "dialogue_ratio": 10,
            "sensory_detail": 10,
            "scene_coverage": 15,
            "ending_hook": 10,
        },
        concerns=[],
    )

    assert result.score == 100
    assert result.level is ConfidenceLevel.VERY_HIGH
    assert result.needs_extra_verification is False
    assert result.recommendation == "pass"


def test_assess_blueprint_allows_two_scene_blueprint_without_scene_count_concern():
    calibrator = ConfidenceCalibrator()

    result = calibrator._assess_blueprint(
        {
            "integrated_scenario": "가" * 1200,
            "scene_breakdown": {
                "scene_1": {"goal": "도입"},
                "scene_2": {"goal": "결말"},
            },
            "ending_hook": "다음 화 떡밥",
        },
        {},
    )

    assert result.factors["scene_count"] == 20
    assert "씬 부족" not in " ".join(result.concerns)
