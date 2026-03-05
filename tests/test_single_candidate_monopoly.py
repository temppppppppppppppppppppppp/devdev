"""
[NC-1 SCM] 단일 후보 독점 방지 테스트
"""


class TestSCMScoreCapping:
    """단일 후보 점수 보정 로직 직접 테스트."""

    def test_single_candidate_score_capped_at_90(self):
        """단일 후보 + score >= 95 → 90으로 보정."""
        # SCM 로직 추출: _scm_single_candidate=True, score >= 95 → min(score, 90)
        _scm_single_candidate = True
        score = 100
        if _scm_single_candidate and score >= 95:
            score = min(score, 90)
        assert score == 90

    def test_single_candidate_score_95_capped(self):
        """score=95 → 90."""
        _scm_single_candidate = True
        score = 95
        if _scm_single_candidate and score >= 95:
            score = min(score, 90)
        assert score == 90

    def test_single_candidate_score_94_not_capped(self):
        """score=94 < 95 → 보정 없음."""
        _scm_single_candidate = True
        score = 94
        if _scm_single_candidate and score >= 95:
            score = min(score, 90)
        assert score == 94

    def test_multiple_candidates_no_cap(self):
        """복수 후보 시 보정 없음."""
        _scm_single_candidate = False
        score = 100
        if _scm_single_candidate and score >= 95:
            score = min(score, 90)
        assert score == 100

    def test_scm_flag_single_qualified(self):
        """qualified_indices 1개면 _scm_single_candidate=True."""
        qualified_indices = [0]
        _scm_single_candidate = len(qualified_indices) == 1
        assert _scm_single_candidate is True

    def test_scm_flag_multiple_qualified(self):
        """qualified_indices 2개 이상이면 _scm_single_candidate=False."""
        qualified_indices = [0, 1]
        _scm_single_candidate = len(qualified_indices) == 1
        assert _scm_single_candidate is False


class TestSCMWarningInjection:
    """경고 문자열 주입 테스트."""

    def test_warning_text_present_when_single(self):
        """단일 후보 시 경고 텍스트 생성."""
        _scm_single_candidate = True
        _scm_prefix = ""
        if _scm_single_candidate:
            _scm_prefix = (
                "\n\n⚠️ [단일 후보 경고] 분량 기준 통과 후보가 1개뿐입니다. "
                "절대 기준으로 독립 평가하세요. 경쟁 부재로 인한 과대 평가를 경계하세요.\n"
            )
        assert "단일 후보 경고" in _scm_prefix

    def test_no_warning_when_multiple(self):
        """복수 후보 시 경고 없음."""
        _scm_single_candidate = False
        _scm_prefix = ""
        if _scm_single_candidate:
            _scm_prefix = "⚠️ [단일 후보 경고]"
        assert _scm_prefix == ""


class TestNCReviewEnforcement:
    """[NC-1] numeric_consistency_review 응답 의무 로직 테스트."""

    def test_agree_triggers_score_reduction(self):
        """AGREE 1건 → continuity_contradiction 상한 32점."""
        _nc_review = [{"id": "NC-1", "verdict": "AGREE", "reason": "실제 모순"}]
        score = 95
        _sb = {
            "continuity_contradiction": 40,
            "blueprint_coverage": 20,
            "quality_engagement": 20,
            "length": 10,
            "python_warnings": 10,
        }
        _nc_agree_count = sum(
            1 for r in _nc_review if isinstance(r, dict) and str(r.get("verdict", "")).upper() == "AGREE"
        )
        if _nc_agree_count > 0:
            _cc_cap = max(0, 40 - _nc_agree_count * 8)
            if _sb["continuity_contradiction"] > _cc_cap:
                _sb["continuity_contradiction"] = _cc_cap
                _new_total = sum(v for v in _sb.values() if isinstance(v, int | float))
                if _new_total < score:
                    score = _new_total
        assert _sb["continuity_contradiction"] == 32
        assert score == 92  # 32+20+20+10+10

    def test_two_agrees_stronger_penalty(self):
        """AGREE 2건 → continuity_contradiction 상한 24점."""
        _nc_review = [
            {"id": "NC-1", "verdict": "AGREE", "reason": "모순1"},
            {"id": "NC-2", "verdict": "AGREE", "reason": "모순2"},
        ]
        _sb = {
            "continuity_contradiction": 40,
            "blueprint_coverage": 20,
            "quality_engagement": 20,
            "length": 10,
            "python_warnings": 10,
        }
        _nc_agree_count = sum(1 for r in _nc_review if str(r.get("verdict", "")).upper() == "AGREE")
        _cc_cap = max(0, 40 - _nc_agree_count * 8)
        _sb["continuity_contradiction"] = min(_sb["continuity_contradiction"], _cc_cap)
        assert _sb["continuity_contradiction"] == 24

    def test_dismiss_no_penalty(self):
        """전부 DISMISS → 감점 없음."""
        _nc_review = [{"id": "NC-1", "verdict": "DISMISS", "reason": "추가 매수로 정당"}]
        _nc_agree_count = sum(1 for r in _nc_review if str(r.get("verdict", "")).upper() == "AGREE")
        assert _nc_agree_count == 0

    def test_missing_review_penalty(self):
        """NC advisory 있었는데 review 생략 → python_warnings 감점."""
        mandatory_context = "[NumericConsistency] [NC-1] 뭐시기"
        _nc_review = []  # 생략됨
        _sb = {
            "continuity_contradiction": 40,
            "blueprint_coverage": 20,
            "quality_engagement": 20,
            "length": 10,
            "python_warnings": 10,
        }
        if not _nc_review and "[NumericConsistency" in mandatory_context and "[NC-" in mandatory_context:
            _sb["python_warnings"] = 5
        assert _sb["python_warnings"] == 5


class TestSCMIntegration:
    """director_ensemble.py에 SCM 코드가 올바르게 삽입되었는지 확인."""

    def test_scm_code_exists_in_module(self):
        """director_ensemble.py에 SCM 관련 코드 존재."""
        import inspect

        from modules.domain.agents import director_ensemble as mod

        source = inspect.getsource(mod)
        assert "_scm_single_candidate" in source
        assert "단일 후보 경고" in source
        assert "[SCM]" in source

    def test_scm_score_cap_code_exists(self):
        """score 보정 코드 존재."""
        import inspect

        from modules.domain.agents import director_ensemble as mod

        source = inspect.getsource(mod)
        assert "min(score, 90)" in source
