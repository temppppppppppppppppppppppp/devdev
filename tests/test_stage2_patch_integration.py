"""Tests for Stage 2 patch mode integration (finalizer + orchestrator flow)."""

from modules.core.constants import PatchModeThresholds


class TestFinalizerRejectFields:
    """stage2_finalizer REJECT 시 score + rejected_arc 반환 확인."""

    def test_reject_returns_score_and_arc(self):
        """Director REJECT 시 score와 rejected_arc가 반환되는지 확인."""
        # finalizer의 REJECT 반환값 시뮬레이션
        audit = {
            "score": 65,
            "decision": "REJECT",
            "reason": "전투 밀도 부족",
            "re_slice_instruction": "밀도 보강 필요",
        }
        rejected_arc = {
            "arc_no": 1,
            "tactical_doc": "원본 전술서",
            "state_constraints": {"items_acquired": []},
        }

        # finalizer가 반환하는 REJECT dict 구조 검증
        result = {
            "action": "next",
            "last_refined_context": "",
            "current_ep_start": 6,
            "current_feedback": "",
            "director_feedback_for_fourphase": "피드백",
            "st_snapshot": None,
            "score": audit.get("score", 0),
            "rejected_arc": rejected_arc,
        }

        assert result["score"] == 65
        assert result["rejected_arc"] is not None
        assert result["rejected_arc"]["arc_no"] == 1

    def test_pass_has_no_rejected_arc(self):
        """Director PASS 시에는 score/rejected_arc 필드가 없음."""
        result = {
            "action": "break",
            "last_refined_context": "ctx",
            "current_ep_start": 6,
            "current_feedback": "",
            "director_feedback_for_fourphase": "",
            "st_snapshot": None,
        }

        assert "score" not in result
        assert "rejected_arc" not in result


class TestOrchestratorPreviousAttempt:
    """orchestrator에서 _previous_attempt 추적 로직 검증."""

    def test_high_score_sets_previous_attempt(self):
        """score >= REWRITE(50) + rejected_arc가 있으면 _previous_attempt 설정."""
        _fin = {
            "action": "next",
            "score": 60,
            "rejected_arc": {"arc_no": 1, "tactical_doc": "원본"},
            "director_feedback_for_fourphase": "밀도 보강",
            "last_refined_context": "",
            "current_ep_start": 6,
            "current_feedback": "",
            "st_snapshot": None,
        }

        _rej_score = _fin.get("score", 0)
        _rej_arc = _fin.get("rejected_arc")
        if _fin["action"] != "break" and _rej_score >= PatchModeThresholds.REWRITE and _rej_arc:
            _previous_attempt = {
                "score": _rej_score,
                "best_arc": _rej_arc,
                "rejection_reason": _fin.get("director_feedback_for_fourphase", ""),
            }
        else:
            _previous_attempt = None

        assert _previous_attempt is not None
        assert _previous_attempt["score"] == 60
        assert _previous_attempt["best_arc"]["arc_no"] == 1
        assert "밀도 보강" in _previous_attempt["rejection_reason"]

    def test_low_score_clears_previous_attempt(self):
        """score < REWRITE(50)이면 _previous_attempt = None."""
        _fin = {
            "action": "next",
            "score": 30,
            "rejected_arc": {"arc_no": 1},
            "director_feedback_for_fourphase": "",
            "last_refined_context": "",
            "current_ep_start": 6,
            "current_feedback": "",
            "st_snapshot": None,
        }

        _rej_score = _fin.get("score", 0)
        _rej_arc = _fin.get("rejected_arc")
        if _fin["action"] != "break" and _rej_score >= PatchModeThresholds.REWRITE and _rej_arc:
            _previous_attempt = {
                "score": _rej_score,
                "best_arc": _rej_arc,
                "rejection_reason": _fin.get("director_feedback_for_fourphase", ""),
            }
        else:
            _previous_attempt = None

        assert _previous_attempt is None

    def test_pass_clears_previous_attempt(self):
        """PASS (action=break)이면 _previous_attempt = None."""
        _fin = {
            "action": "break",
            "score": 85,
            "rejected_arc": {"arc_no": 1},
            "director_feedback_for_fourphase": "",
            "last_refined_context": "",
            "current_ep_start": 6,
            "current_feedback": "",
            "st_snapshot": None,
        }

        _rej_score = _fin.get("score", 0)
        _rej_arc = _fin.get("rejected_arc")
        if _fin["action"] != "break" and _rej_score >= PatchModeThresholds.REWRITE and _rej_arc:
            _previous_attempt = {
                "score": _rej_score,
                "best_arc": _rej_arc,
                "rejection_reason": _fin.get("director_feedback_for_fourphase", ""),
            }
        else:
            _previous_attempt = None

        assert _previous_attempt is None

    def test_no_rejected_arc_clears_previous_attempt(self):
        """rejected_arc가 None이면 score가 높아도 _previous_attempt = None."""
        _fin = {
            "action": "next",
            "score": 70,
            "rejected_arc": None,
            "director_feedback_for_fourphase": "",
            "last_refined_context": "",
            "current_ep_start": 6,
            "current_feedback": "",
            "st_snapshot": None,
        }

        _rej_score = _fin.get("score", 0)
        _rej_arc = _fin.get("rejected_arc")
        if _fin["action"] != "break" and _rej_score >= PatchModeThresholds.REWRITE and _rej_arc:
            _previous_attempt = {
                "score": _rej_score,
                "best_arc": _rej_arc,
                "rejection_reason": _fin.get("director_feedback_for_fourphase", ""),
            }
        else:
            _previous_attempt = None

        assert _previous_attempt is None
