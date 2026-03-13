from main_a import SovereignApp


def _make_app():
    return SovereignApp.__new__(SovereignApp)


def test_normalize_rejection_reason_maps_live_reason_samples():
    app = _make_app()

    assert app._normalize_rejection_reason("반복 전개로 후반부가 정체됨") == "반복 전개/서사 정체"
    assert app._normalize_rejection_reason("설정 충돌과 continuity mismatch") == "설정/연속성 충돌"
    assert app._normalize_rejection_reason("인과 붕괴로 logic error 발생") == "인과/구조 붕괴"
    assert app._normalize_rejection_reason("후반부 밀도 부족") == "밀도/분량 부족"


def test_analyze_rejection_pattern_includes_specific_issue_block():
    app = _make_app()

    result = app._analyze_rejection_pattern_v60(
        [
            {"reason": "반복 전개", "specific_issue": "후반부 이벤트 부족"},
            {"reason": "반복 전개", "specific_issue": "씬 5 이후 갈등이 멈춤"},
            {"reason": "설정 충돌"},
        ],
        current_arc_no=3,
    )

    assert "Arc 3" in result
    assert "반복 전개/서사 정체" in result
    assert "구체적 문제 지점" in result
    assert "후반부 이벤트 부족" in result


def test_get_rejection_fix_guide_returns_generic_for_other_bucket():
    app = _make_app()

    assert app._get_rejection_fix_guide("기타")
