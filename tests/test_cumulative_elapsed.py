"""[LM-Tier TF-F] 누적 경과 시간 추적기 테스트."""

import pytest

from modules.core.narrative_context_formatter import NarrativeContextFormatter
from modules.core.world_state import WorldStateManager


class TestParseElapsedDays:
    """_parse_elapsed_days 정적 메서드 단위 테스트."""

    def test_parse_numeric(self):
        """숫자+단위: '3일 후' → 3, '2주' → 14"""
        assert WorldStateManager._parse_elapsed_days("3일 후") == 3
        assert WorldStateManager._parse_elapsed_days("2주") == 14
        assert WorldStateManager._parse_elapsed_days("3개월 뒤") == 90
        assert WorldStateManager._parse_elapsed_days("1년 후") == 365

    def test_parse_korean_numerals(self):
        """한국어 수사: '이틀' → 2, '사흘' → 3"""
        assert WorldStateManager._parse_elapsed_days("이틀 후") == 2
        assert WorldStateManager._parse_elapsed_days("사흘 뒤") == 3
        assert WorldStateManager._parse_elapsed_days("나흘이 지나") == 4
        assert WorldStateManager._parse_elapsed_days("닷새") == 5
        assert WorldStateManager._parse_elapsed_days("하루") == 1
        assert WorldStateManager._parse_elapsed_days("이레") == 7

    def test_parse_compounds(self):
        """복합 표현: '일주일' → 7, '보름' → 15, '한 달' → 30"""
        assert WorldStateManager._parse_elapsed_days("일주일 후") == 7
        assert WorldStateManager._parse_elapsed_days("보름이 지나고") == 15
        assert WorldStateManager._parse_elapsed_days("한 달 뒤") == 30
        assert WorldStateManager._parse_elapsed_days("한달 후") == 30
        assert WorldStateManager._parse_elapsed_days("반년이 흘러") == 180

    def test_parse_none(self):
        """파싱 불가 → None."""
        assert WorldStateManager._parse_elapsed_days("") is None
        assert WorldStateManager._parse_elapsed_days(None) is None
        assert WorldStateManager._parse_elapsed_days("내일") is None
        assert WorldStateManager._parse_elapsed_days("다음 날") is None


class TestCumulativeElapsed:
    """WorldState 누적 경과 시간 통합 테스트."""

    @pytest.fixture
    def ws(self, tmp_path):
        """WorldState 인스턴스 (mock DB)."""
        from unittest.mock import MagicMock

        db = MagicMock()
        db.load_anchor.return_value = None
        db.save_anchor = MagicMock()
        ws = WorldStateManager(db)
        return ws

    def test_cumulative_sum(self, ws):
        """다회 업데이트 후 합산 검증."""
        # 1화: 3일 후
        ws.update_from_state_changes(1, {"time_markers": [{"type": "elapsed", "description": "3일 후"}]})
        assert ws.get_cumulative_elapsed()["total_days"] == 3

        # 2화: 이틀 후
        ws.update_from_state_changes(2, {"time_markers": [{"type": "elapsed", "description": "이틀 후"}]})
        assert ws.get_cumulative_elapsed()["total_days"] == 5

        # 3화: 1주
        ws.update_from_state_changes(3, {"time_markers": [{"type": "elapsed", "description": "1주"}]})
        assert ws.get_cumulative_elapsed()["total_days"] == 12

    def test_history_cap_20(self, ws):
        """history 리스트 최대 20개 유지."""
        for i in range(25):
            ws.update_from_state_changes(
                i + 1,
                {"time_markers": [{"type": "elapsed", "description": f"{i + 1}일 후"}]},
            )
        elapsed = ws.get_cumulative_elapsed()
        assert len(elapsed["history"]) == 20
        assert elapsed["total_days"] == sum(range(1, 26))  # 1+2+...+25 = 325

    def test_no_time_markers_no_change(self, ws):
        """시간 마커 없으면 누적 변경 없음."""
        ws.update_from_state_changes(1, {"protagonist": {"name": "주인공"}})
        assert ws.get_cumulative_elapsed()["total_days"] == 0

    def test_unparseable_description_skipped(self, ws):
        """파싱 불가 description → 누적 변경 없음."""
        ws.update_from_state_changes(1, {"time_markers": [{"type": "date", "description": "봄이 왔다"}]})
        assert ws.get_cumulative_elapsed()["total_days"] == 0


class TestFormatCumulativeTime:
    """NarrativeContextFormatter.format_cumulative_time 테스트."""

    def test_zero_days(self):
        """0일 → 빈 문자열."""
        assert NarrativeContextFormatter.format_cumulative_time({"total_days": 0, "history": []}) == ""

    def test_short_days(self):
        """30일 미만 → '일' 단위."""
        result = NarrativeContextFormatter.format_cumulative_time({"total_days": 15, "history": []})
        assert "15일" in result

    def test_months(self):
        """30일 이상 365일 미만 → '개월' 표현."""
        result = NarrativeContextFormatter.format_cumulative_time({"total_days": 90, "history": []})
        assert "3개월" in result

    def test_years(self):
        """365일 이상 → '년' 표현."""
        result = NarrativeContextFormatter.format_cumulative_time({"total_days": 400, "history": []})
        assert "1년" in result

    def test_none_input(self):
        """None → 빈 문자열."""
        assert NarrativeContextFormatter.format_cumulative_time(None) == ""

    def test_format_all_includes_time(self):
        """format_all에 cumulative_elapsed 전달 시 결과에 포함."""
        result = NarrativeContextFormatter.format_all(
            active_plots={"플롯1": {"status": "진행중", "first_arc": 1, "last_mention_arc": 1}},
            npc_motivations=None,
            pending_commitments=None,
            all_refined_arcs=None,
            current_arc_no=5,
            cumulative_elapsed={"total_days": 60, "history": []},
        )
        assert "누적 경과 시간" in result
        assert "2개월" in result
