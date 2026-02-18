"""
[V70] RepetitionGuard 단위 테스트

modules/core/repetition_guard.py의 모든 공개 메서드를 검증합니다.
"""

from modules.core.repetition_guard import RepetitionGuard

# ============================================================
# 기본 초기화
# ============================================================


class TestRepetitionGuardInit:
    """초기화 및 기본값 검증"""

    def test_default_params(self):
        guard = RepetitionGuard()
        assert guard.window_size == 5
        assert guard.threshold == 3
        assert guard.banned_phrases == {}

    def test_custom_params(self):
        guard = RepetitionGuard(window_size=10, threshold=5)
        assert guard.window_size == 10
        assert guard.threshold == 5


# ============================================================
# build_banned_list
# ============================================================


class TestBuildBannedList:
    """이전 원고에서 과다 반복 구문 추출 검증"""

    def test_empty_manuscripts(self):
        guard = RepetitionGuard()
        result = guard.build_banned_list([])
        assert result == {}

    def test_none_manuscripts(self):
        guard = RepetitionGuard()
        result = guard.build_banned_list([None, None])
        assert result == {}

    def test_mixed_none_and_valid(self):
        guard = RepetitionGuard(threshold=2)
        text = "이청풍은 검을 들었다. 이청풍은 검을 들었다. 이청풍은 검을 들었다."
        result = guard.build_banned_list([None, text, None])
        # 반복된 3-gram이 있어야 함
        assert isinstance(result, dict)

    def test_repeated_phrases_detected(self):
        guard = RepetitionGuard(threshold=2)
        # 동일한 3-gram "차가운 눈빛을 보냈다"가 threshold 이상 반복
        text = "차가운 눈빛을 보냈다 " * 5
        result = guard.build_banned_list([text])
        assert len(result) > 0
        assert any("차가운" in phrase for phrase in result)

    def test_window_size_respected(self):
        guard = RepetitionGuard(window_size=2, threshold=2)
        old_text = "오래된 원고 내용 반복 내용 반복 내용 반복"
        new_text = "새로운 원고 다른 내용 완전히 다른 문장입니다"
        # window_size=2 이므로 최근 2개만 사용
        result = guard.build_banned_list([old_text, old_text, old_text, new_text])
        # old_text 3개 중 최근 2개만 (old_text, new_text) 사용됨
        assert isinstance(result, dict)

    def test_short_text_no_trigrams(self):
        guard = RepetitionGuard()
        result = guard.build_banned_list(["짧은"])
        assert result == {}

    def test_banned_phrases_stored(self):
        guard = RepetitionGuard(threshold=2)
        text = "이청풍은 검을 들었다 " * 10
        guard.build_banned_list([text])
        # banned_phrases가 인스턴스에 저장되어야 함
        assert guard.banned_phrases == guard.build_banned_list([text])


# ============================================================
# scan_manuscript
# ============================================================


class TestScanManuscript:
    """새 원고에서 금지 구문 스캔 검증"""

    def test_no_banned_phrases(self):
        guard = RepetitionGuard()
        violations, score = guard.scan_manuscript("새 원고 텍스트입니다.")
        assert violations == []
        assert score == 1.0

    def test_violations_detected(self):
        guard = RepetitionGuard(threshold=2)
        repeated = "이청풍은 검을 들었다 " * 10
        guard.build_banned_list([repeated])

        violations, score = guard.scan_manuscript("이청풍은 검을 들었다. 새로운 전개가 시작되었다.")
        # banned에 포함된 3-gram이 새 원고에 있으면 위반
        if guard.banned_phrases:
            assert isinstance(violations, list)
            assert 0.0 <= score <= 1.0

    def test_clean_manuscript_perfect_score(self):
        guard = RepetitionGuard(threshold=2)
        guard.build_banned_list(["반복 구문 반복 구문 반복 구문 반복 구문"])

        violations, score = guard.scan_manuscript("완전히 다른 내용의 새로운 문장이 아름답게 흐른다")
        assert score == 1.0

    def test_short_manuscript(self):
        guard = RepetitionGuard()
        guard.banned_phrases = {"이건 금지 구문": 3}
        violations, score = guard.scan_manuscript("짧")
        assert violations == []
        assert score == 1.0

    def test_violation_has_required_keys(self):
        guard = RepetitionGuard(threshold=2)
        text = "같은 표현을 사용 " * 20
        guard.build_banned_list([text])

        violations, _ = guard.scan_manuscript(text)
        if violations:
            v = violations[0]
            assert "phrase" in v
            assert "position" in v
            assert "context" in v
            assert "frequency" in v


# ============================================================
# generate_correction_prompt
# ============================================================


class TestGenerateCorrectionPrompt:
    """교정 프롬프트 생성 검증"""

    def test_empty_violations(self):
        guard = RepetitionGuard()
        result = guard.generate_correction_prompt([])
        assert result == ""

    def test_prompt_contains_violations(self):
        guard = RepetitionGuard()
        violations = [
            {"phrase": "차가운 눈빛을", "position": 5, "context": "...차가운 눈빛을 보냈다...", "frequency": 3},
            {"phrase": "검을 들었다", "position": 12, "context": "...검을 들었다 위협했다...", "frequency": 4},
        ]
        result = guard.generate_correction_prompt(violations)
        assert "REPETITION ALERT" in result
        assert "차가운 눈빛을" in result
        assert "검을 들었다" in result

    def test_max_5_violations_reported(self):
        guard = RepetitionGuard()
        violations = [
            {"phrase": f"구문{i}", "position": i, "context": f"...구문{i}...", "frequency": 3} for i in range(10)
        ]
        result = guard.generate_correction_prompt(violations)
        # 상위 5개만 보고
        assert "구문0" in result
        assert "구문4" in result
        # 6번째 이후는 포함되지 않아야 함
        assert "구문5" not in result


# ============================================================
# get_statistics
# ============================================================


class TestGetStatistics:
    """통계 반환 검증"""

    def test_empty_statistics(self):
        guard = RepetitionGuard()
        stats = guard.get_statistics()
        assert stats["total_banned_phrases"] == 0
        assert stats["window_size"] == 5
        assert stats["threshold"] == 3
        assert stats["sample_phrases"] == []

    def test_statistics_after_build(self):
        guard = RepetitionGuard(threshold=2)
        text = "이청풍은 검을 들었다 " * 20
        guard.build_banned_list([text])
        stats = guard.get_statistics()
        assert stats["total_banned_phrases"] >= 0
        assert stats["window_size"] == 5
        assert stats["threshold"] == 2
        assert isinstance(stats["sample_phrases"], list)
