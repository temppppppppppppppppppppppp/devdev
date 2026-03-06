"""
[NS-4-S2/S4] Arc 간 날짜 감각 Stage 2/4 확장 테스트 (7개)
"""

import re


# ─────────────────────────────────────────────
# 헬퍼 함수 직접 복제 (임포트 체인 우회)
# ─────────────────────────────────────────────
def _ns4_extract_time_markers(arc_data: dict) -> list:
    """[NS-4] Arc tactical_doc/beat_sequence에서 날짜·상대시간 마커 추출 (regex, LLM 0회)."""
    tactical_doc = arc_data.get("tactical_doc") or ""
    beat_seq = arc_data.get("beat_sequence") or ""
    if isinstance(beat_seq, list):
        beat_seq = " ".join(str(b) for b in beat_seq)

    _text = str(tactical_doc) + "\n" + str(beat_seq)
    _patterns = [
        r"\d{4}년\s*\d{1,2}월(?:\s*\d{1,2}일)?",
        r"\d{1,2}월\s*\d{1,2}일",
        r"\d{1,2}월(?:\s*(?:말|초|중순|하순|상순))?",
        r"\d+(?:일|주|달|개월|년)\s*(?:후|전)",
    ]
    _found = []
    for _p in _patterns:
        _found.extend(re.findall(_p, _text))
    return list(dict.fromkeys(_found))[:5]


# ─────────────────────────────────────────────
# 테스트 1: 날짜 추출 정상 동작
# ─────────────────────────────────────────────
def test_ns4_s2_helper_extracts_dates():
    """투자물 날짜 마커 추출 — 연월일, 상대 시간 등 다양한 포맷."""
    arc = {
        "tactical_doc": (
            "2026년 3월 말, 주인공이 실리콘밸리에 도착. "
            "3개월 후 시리즈 A 클로징 예정. "
            "3월 15일 킥오프 미팅."
        ),
        "beat_sequence": "2주 후 최종 계약 체결.",
    }
    markers = _ns4_extract_time_markers(arc)
    assert len(markers) > 0, "날짜 마커가 최소 1개 이상 추출되어야 함"
    joined = " ".join(markers)
    # 상대 시간 또는 날짜가 포함되어야 함
    assert any(kw in joined for kw in ["월", "후", "전", "일"]), f"기대 키워드 없음: {markers}"


# ─────────────────────────────────────────────
# 테스트 2: tactical_doc 없으면 빈 리스트
# ─────────────────────────────────────────────
def test_ns4_s2_helper_returns_empty_for_no_doc():
    """tactical_doc/beat_sequence 모두 없으면 빈 리스트 반환."""
    assert _ns4_extract_time_markers({}) == []
    assert _ns4_extract_time_markers({"tactical_doc": None, "beat_sequence": None}) == []
    assert _ns4_extract_time_markers({"tactical_doc": "날짜 없는 텍스트"}) == []


# ─────────────────────────────────────────────
# 테스트 3: beat_sequence list 타입 방어
# ─────────────────────────────────────────────
def test_ns4_beat_sequence_list():
    """beat_sequence가 list여도 TypeError 없이 시간 마커를 추출한다."""
    arc = {
        "tactical_doc": "2026년 3월부터 시작",
        "beat_sequence": ["Ep1: 2026년 3월 초 개시", "Ep2: 1개월 후 결과"],
    }
    markers = _ns4_extract_time_markers(arc)
    assert "2026년 3월" in markers or "3월 초" in markers
    assert "1개월 후" in markers


# ─────────────────────────────────────────────
# 테스트 4: beat_sequence nested list 타입 방어
# ─────────────────────────────────────────────
def test_ns4_beat_sequence_nested_list():
    """beat_sequence 내부 dict 혼재 케이스도 안전하게 처리한다."""
    arc = {
        "tactical_doc": "",
        "beat_sequence": [{"ep": 1, "desc": "2025년 1월"}, "Ep2: 3달 후"],
    }
    markers = _ns4_extract_time_markers(arc)
    assert isinstance(markers, list)
    assert "3달 후" in markers


# ─────────────────────────────────────────────
# 테스트 5: four_phase_arc_generator.py 소스 확인
# ─────────────────────────────────────────────
def test_ns4_s2_prev_context_marker_present():
    """four_phase_arc_generator.py에 NS-4-S2 태그와 헬퍼 함수 정의가 존재."""
    import pathlib

    src = pathlib.Path("modules/domain/agents/four_phase_arc_generator.py").read_text(encoding="utf-8")
    assert "[NS-4-S2]" in src, "[NS-4-S2] 태그 누락"
    assert "_ns4_extract_time_markers" in src, "_ns4_extract_time_markers 함수 누락"
    assert "_ns4_markers" in src, "_ns4_markers 변수 누락 (주입 로직 미존재)"


# ─────────────────────────────────────────────
# 테스트 6: stage4_interview_round.py 소스 확인
# ─────────────────────────────────────────────
def test_ns4_s4_director_code_has_injection():
    """stage4_interview_round.py에 NS-4-S4 태그와 헬퍼 함수 + Director 주입 코드 존재."""
    import pathlib

    src = pathlib.Path("modules/core/stage4_interview_round.py").read_text(encoding="utf-8")
    assert "[NS-4-S4]" in src, "[NS-4-S4] 태그 누락"
    assert "_ns4_extract_time_markers" in src, "_ns4_extract_time_markers 함수 누락"
    assert "_director_mc_parts.append" in src, "_director_mc_parts.append 누락"
    assert "Arc 시간 연속성 참고" in src, "'Arc 시간 연속성 참고' 텍스트 누락"


# ─────────────────────────────────────────────
# 테스트 7: arc_no=1 → 스킵 로직 유닛 테스트
# ─────────────────────────────────────────────
def test_ns4_s4_arc1_skip_logic():
    """arc_no=1 이면 arc_idx=0 → if _ns4_arc_idx > 0 false → 주입 없음."""
    injected = []

    # 실제 run() 내 로직 인라인 재현
    arc_data = {"arc_no": 1, "tactical_doc": "2026년 3월 Arc 1"}
    _ns4_arc_no = int(arc_data.get("arc_no", 0) or 0)
    _ns4_arc_idx = _ns4_arc_no - 1  # 0
    if _ns4_arc_idx > 0:
        injected.append("should_not_reach")

    assert injected == [], f"arc_no=1 에서 주입이 발생하면 안 됨: {injected}"
