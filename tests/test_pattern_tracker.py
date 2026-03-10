"""[TF-54a] PatternTracker 단위 테스트."""

from modules.core.pattern_tracker import PatternReport, PatternTracker


def test_count_expressions_basic():
    tracker = PatternTracker()
    manuscripts = ["사무실의 공기가 얼어붙었다. 동공이 흔들렸다."]
    freq = tracker._count_expressions(manuscripts)
    assert freq.get("사무실의 공기", 0) >= 1
    assert freq.get("동공이 흔들", 0) >= 1


def test_classify_endings_선언문():
    tracker = PatternTracker()
    patterns = tracker._classify_endings(["이것이 진짜 시작이었다."])
    assert patterns[0] == "선언문"


def test_classify_endings_조용한여운():
    tracker = PatternTracker()
    patterns = tracker._classify_endings(["그는 조용히 창밖을 바라보았다."])
    assert patterns[0] == "조용한여운"


def test_count_metaphors():
    tracker = PatternTracker()
    manuscripts = ["전쟁이 시작되었다. 총알처럼 빠르게. 맹수처럼 달려들었다."]
    cats = tracker._count_metaphors(manuscripts)
    assert cats["군사"] >= 1
    assert cats["사냥"] >= 1


def test_emotion_diversity_low():
    tracker = PatternTracker()
    text = "차가운 만족. 차가운 만족. 차가운 만족."
    emotions = tracker._extract_emotions(text)
    unique = len(set(emotions))
    total = len(emotions)
    diversity = unique / total if total else 0
    assert diversity <= 0.5


def test_to_summary_text_not_empty():
    report = PatternReport(
        expression_freq={"사무실의 공기": 5, "동공이 흔들": 3},
        ending_patterns=["선언문", "선언문", "선언문"],
        metaphor_categories={"군사": 10, "사냥": 5, "음식": 0},
        emotion_diversity=0.2,
        protagonist_emotions=["차가운 만족"] * 5,
    )
    text = report.to_summary_text()
    assert len(text) > 10
    assert "반복 표현" in text or "엔딩" in text


def test_build_report_no_db():
    tracker = PatternTracker()
    report = tracker.build_report(db=None, ep_num=5)
    assert isinstance(report, PatternReport)


def test_build_report_db_returns_none():
    class FakeDB:
        def get_manuscript(self, ep):
            return None

    tracker = PatternTracker()
    report = tracker.build_report(db=FakeDB(), ep_num=5, lookback=3)
    assert isinstance(report, PatternReport)
    assert report.expression_freq == {}


def test_build_report_collects_npc_reaction_patterns():
    class FakeDB:
        def __init__(self):
            self._rows = {
                1: {"content": "민수는 경악했다."},
                2: {"content": "민수는 침묵했다."},
                3: {"content": "민수는 분노했다."},
            }

        def get_manuscript(self, ep):
            return self._rows.get(ep)

    tracker = PatternTracker()
    report = tracker.build_report(db=FakeDB(), ep_num=4, lookback=4)

    assert report.npc_reaction_patterns["민수"][-3:] == ["경악", "침묵", "분노"]


def test_to_summary_text_warns_on_recent_emotion_streak_even_with_ok_diversity():
    report = PatternReport(
        emotion_diversity=0.5,
        protagonist_emotions=["안도", "분노", "안도", "분노"],
        episode_emotion_sequence=["안도", "안도", "안도"],
    )

    text = report.to_summary_text()

    assert "감정 고착" in text
