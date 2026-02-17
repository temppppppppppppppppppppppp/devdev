"""
[Sweep9-E] ActionSceneEvaluator 단위 테스트
전투/액션 씬 평가의 기본 동작을 검증합니다.
"""

import pytest

from modules.validation.action_scene_evaluator import ActionSceneEvaluator


@pytest.fixture(params=["wuxia", "hunter", "investment"])
def evaluator(request):
    return ActionSceneEvaluator(genre=request.param)


class TestInstantiation:
    def test_create(self, evaluator):
        assert evaluator is not None

    def test_action_keywords_populated(self, evaluator):
        assert isinstance(evaluator.ACTION_KEYWORDS, dict)
        assert len(evaluator.ACTION_KEYWORDS) > 0


class TestEvaluate:
    def test_returns_dict(self, evaluator):
        result = evaluator.evaluate("그는 검을 휘둘렀다. 상대의 공격을 피했다.")
        assert isinstance(result, dict)

    def test_score_in_range(self, evaluator):
        result = evaluator.evaluate("그는 검을 휘둘렀다. 상대의 공격을 피했다.")
        assert 0 <= result["total_score"] <= 10

    def test_empty_manuscript(self, evaluator):
        result = evaluator.evaluate("")
        assert isinstance(result, dict)


class TestExtractActionScenes:
    def test_returns_list(self, evaluator):
        scenes = evaluator._extract_action_scenes("그는 검을 휘둘렀다. 피가 튀었다.")
        assert isinstance(scenes, list)


class TestEvaluateChoreography:
    def test_returns_dict(self, evaluator):
        result = evaluator.evaluate_choreography(["그는 검을 휘둘렀다."])
        assert isinstance(result, dict)

    def test_empty_scenes(self, evaluator):
        result = evaluator.evaluate_choreography([])
        assert isinstance(result, dict)


class TestEvaluateStakesEscalation:
    def test_returns_dict(self, evaluator):
        result = evaluator.evaluate_stakes_escalation(["첫 장면", "두 번째 장면"])
        assert isinstance(result, dict)

    def test_single_scene(self, evaluator):
        result = evaluator.evaluate_stakes_escalation(["유일한 장면"])
        assert isinstance(result, dict)
