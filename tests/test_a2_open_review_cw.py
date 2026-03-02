"""[A-2] Director open_review → CW enhanced_feedback 명시 전달 테스트."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def _cw_instance():
    """ChiefWriter 인스턴스 생성 (최소 mock)."""
    from modules.domain.agents.chief_writer import ChiefWriter

    with patch.object(ChiefWriter, "__init__", lambda self: None):
        cw = ChiefWriter.__new__(ChiefWriter)
        cw._quality_gate = MagicMock()
        cw._context_builder = MagicMock()
        cw.logger = MagicMock()
        return cw


class TestOpenReviewCWDelivery:
    """A-2: open_review가 enhanced_feedback 명시 섹션으로 포함되는지 확인."""

    def test_open_review_included_in_enhanced_feedback(self, _cw_instance):
        """open_review 텍스트가 enhanced_feedback에 명시적 섹션으로 포함."""
        cw = _cw_instance
        captured = {}

        def _capture_generate(**kwargs):
            captured.update(kwargs)
            return [{"content": "test", "strategy_name": "A"}]

        cw.generate_ensemble = _capture_generate

        previous_attempt = {
            "score": 65,
            "open_review": "톤이 2장에서 급변합니다. 감정선이 비약적입니다.",
            "action_items": ["톤 조절"],
        }
        cw.regenerate_with_feedback(
            ep_num=5,
            blueprint={"scenes": []},
            prev_manuscript="이전 원고",
            hud_report="",
            arc_doc="",
            master_bible={},
            style_guide="",
            director_feedback="기본 피드백",
            previous_attempt=previous_attempt,
            attempt_number=2,
        )

        feedback = captured.get("director_feedback", "")
        assert "[Director 서사 관찰 — 반드시 개선할 것]" in feedback
        assert "톤이 2장에서 급변합니다" in feedback

    def test_open_review_skipped_when_empty(self, _cw_instance):
        """open_review가 비어있거나 '없음'이면 섹션 미포함."""
        cw = _cw_instance
        captured = {}

        def _capture_generate(**kwargs):
            captured.update(kwargs)
            return [{"content": "test", "strategy_name": "A"}]

        cw.generate_ensemble = _capture_generate

        for empty_val in ["", "없음", "특이사항 없음"]:
            previous_attempt = {
                "score": 70,
                "open_review": empty_val,
                "action_items": ["수정"],
            }
            cw.regenerate_with_feedback(
                ep_num=5,
                blueprint={"scenes": []},
                prev_manuscript="이전 원고",
                hud_report="",
                arc_doc="",
                master_bible={},
                style_guide="",
                director_feedback="기본 피드백",
                previous_attempt=previous_attempt,
                attempt_number=2,
            )
            feedback = captured.get("director_feedback", "")
            assert "[Director 서사 관찰" not in feedback, f"open_review='{empty_val}'인데 섹션 포함됨"
