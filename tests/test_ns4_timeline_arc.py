"""[NS-4] Arc 간 시간 연속성 체크 테스트 (5개)"""

import re
import unittest


def _extract_arc_time_markers(arc_data: dict) -> list:
    """stage3_orchestrator._extract_arc_time_markers() 로직 복제 (임포트 없이 테스트)."""
    _text = (arc_data.get("tactical_doc") or "") + "\n" + (arc_data.get("beat_sequence") or "")
    _patterns = [
        r"\d{4}년\s*\d{1,2}월(?:\s*\d{1,2}일)?",    # 2006년 7월 12일
        r"\d{1,2}월\s*\d{1,2}일",                     # 7월 12일
        r"\d{1,2}월(?:\s*(?:말|초|중순|하순|상순))?",  # 5월 말
        r"\d+(?:일|주|달|개월|년)\s*(?:후|전)",         # 2달 후
    ]
    _found = []
    for _p in _patterns:
        _found.extend(re.findall(_p, _text))
    return list(dict.fromkeys(_found))[:5]


class TestExtractArcTimeMarkers(unittest.TestCase):
    def test_extract_time_markers_investment(self):
        """투자물 arc_doc에서 날짜 마커 추출."""
        arc_data = {
            "tactical_doc": "2006년 7월 12일 자산 매각 완료. Arc 4는 9월 말까지 진행.",
            "beat_sequence": "",
        }
        markers = _extract_arc_time_markers(arc_data)
        assert any("7월" in m for m in markers), f"날짜 마커 미추출: {markers}"
        assert len(markers) <= 5

    def test_extract_time_markers_empty(self):
        """tactical_doc/beat_sequence 없으면 빈 리스트 반환."""
        assert _extract_arc_time_markers({}) == []
        assert _extract_arc_time_markers({"tactical_doc": None, "beat_sequence": None}) == []

    def test_extract_time_markers_relative(self):
        """상대 시간 마커('3달 후', '2주 전') 추출."""
        arc_data = {
            "tactical_doc": "계약 후 3달 후 계획. 사건 발생 2주 전 복선.",
            "beat_sequence": "1개월 후 귀국.",
        }
        markers = _extract_arc_time_markers(arc_data)
        assert any("달" in m or "주" in m or "개월" in m for m in markers), (
            f"상대 마커 미추출: {markers}"
        )

    def test_extract_time_markers_dedup_and_limit(self):
        """중복 제거 및 최대 5개 제한."""
        repeated = "7월 말 " * 10
        arc_data = {"tactical_doc": repeated, "beat_sequence": "5월 초 3달 후 2주 전 1년 후"}
        markers = _extract_arc_time_markers(arc_data)
        assert len(markers) <= 5
        assert len(markers) == len(set(markers)), "중복 포함"


class TestNc3TimelineKeyInEnsemble(unittest.TestCase):
    def test_timeline_arc_consistency_in_nc3_keys(self):
        """director_ensemble._nc3_keys에 timeline_arc_consistency 포함."""
        import pathlib

        src = pathlib.Path("modules/domain/agents/director_ensemble.py").read_text(encoding="utf-8")
        assert "timeline_arc_consistency" in src, (
            "director_ensemble.py에 timeline_arc_consistency 미발견"
        )


if __name__ == "__main__":
    unittest.main()
