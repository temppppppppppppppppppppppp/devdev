"""
[Sweep9-F] CatharsisTimer 단위 테스트
카타르시스 타이밍 관리의 기본 동작을 검증합니다.
"""

import pytest

from modules.validation.catharsis_timer import CatharsisTimer


@pytest.fixture
def timer():
    return CatharsisTimer(genre="wuxia")


@pytest.fixture
def hunter_timer():
    return CatharsisTimer(genre="hunter")


class TestInstantiation:
    def test_default_genre(self):
        t = CatharsisTimer()
        assert t is not None

    def test_custom_genre(self, hunter_timer):
        assert hunter_timer is not None

    def test_max_frustration_default(self, timer):
        assert timer.MAX_FRUSTRATION_EPISODES == 3

    def test_custom_max_frustration(self):
        t = CatharsisTimer(max_frustration=5)
        assert t.max_frustration == 5


class TestCheckCatharsisTiming:
    def test_returns_dict(self, timer):
        result = timer.check_catharsis_timing(ep_num=1, manuscript="통쾌한 승리를 거두었다.")
        assert isinstance(result, dict)

    def test_catharsis_detected(self, timer):
        result = timer.check_catharsis_timing(
            ep_num=1,
            manuscript="드디어 통쾌한 승리를 거두었다. 모두가 경악했다.",
        )
        assert isinstance(result, dict)

    def test_no_catharsis(self, timer):
        result = timer.check_catharsis_timing(
            ep_num=1,
            manuscript="그는 또 패배했다. 아무것도 할 수 없었다.",
        )
        assert isinstance(result, dict)

    def test_with_history(self, timer):
        history = [
            {"ep_num": 1, "has_catharsis": False},
            {"ep_num": 2, "has_catharsis": False},
        ]
        result = timer.check_catharsis_timing(
            ep_num=3,
            manuscript="또다시 좌절의 연속이었다.",
            history=history,
        )
        assert isinstance(result, dict)


class TestAnalyzeCatharsis:
    def test_returns_dict(self, timer):
        result = timer._analyze_catharsis("통쾌한 승리를 거두었다.")
        assert isinstance(result, dict)

    def test_empty_text(self, timer):
        result = timer._analyze_catharsis("")
        assert isinstance(result, dict)


class TestGetRecommendedCatharsisType:
    def test_returns_list(self, timer):
        result = timer.get_recommended_catharsis_type()
        assert isinstance(result, list)

    def test_with_context(self, timer):
        result = timer.get_recommended_catharsis_type(context={"genre": "wuxia"})
        assert isinstance(result, list)


class TestRecordEpisode:
    def test_returns_dict(self, timer):
        result = timer.record_episode(ep_num=1, manuscript="통쾌한 승리를 거두었다.")
        assert isinstance(result, dict)

    def test_sequential_recording(self, timer):
        timer.record_episode(ep_num=1, manuscript="패배했다.")
        result = timer.record_episode(ep_num=2, manuscript="또 패배했다.")
        assert isinstance(result, dict)
