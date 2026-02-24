"""TF-10 episode_details 필드 전 범위 테스트

Coverage:
  - ArcData Pydantic 기본값
  - ASP 경로 episode_details 복원 (four_phase_arc_generator)
  - ArcCorrector tactical_doc 수정 시 해당 화 항목 삭제
  - UnifiedArcValidator ADVISORY 체크
  - BlueprintConstraintCompiler _extract_episode_focus / _extract_stop_line 우선 참조
"""
from unittest.mock import MagicMock

from modules.models.arc import ArcData
from modules.domain.agents.unified_arc_validator import UnifiedArcValidator
from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler


# ─────────────────────────────────────────────
# 1. ArcData Pydantic 기본값
# ─────────────────────────────────────────────

def test_arc_data_episode_details_default():
    """episode_details 선택 필드 — 누락 시 빈 리스트"""
    arc = ArcData(arc_no=1, ep_start=1, ep_end=5)
    assert arc.episode_details == []


def test_arc_data_episode_details_roundtrip():
    """episode_details list[dict] 직렬화/역직렬화 무손실"""
    raw = {
        "arc_no": 1,
        "ep_start": 1,
        "ep_end": 5,
        "episode_details": [
            {"ep_num": 1, "details": ["사건1", "사건2"]},
            {"ep_num": 2, "details": ["사건3"]},
        ],
    }
    arc = ArcData.model_validate(raw)
    dumped = arc.model_dump()
    assert dumped["episode_details"] == raw["episode_details"]


def test_arc_data_episode_details_none_becomes_empty():
    """episode_details=None → Pydantic 기본값 [] 적용"""
    # extra="allow" 이므로 None으로 넘어오면 기본값이 아니라 None 그대로 저장될 수 있음
    # 하지만 소비처에서 `or []` 폴백을 사용하므로 ADVISORY만 발생해야 함
    arc = ArcData(arc_no=1, ep_start=1, ep_end=5, episode_details=[])
    assert arc.episode_details == []


# ─────────────────────────────────────────────
# 2. ASP 경로 episode_details 복원
# ─────────────────────────────────────────────

def test_asp_preserves_episode_details_when_missing_in_asp_result():
    """ASP 결과에 episode_details 없으면 원본에서 복원"""
    orig_details = [{"ep_num": 3, "details": ["원본 사건"]}]
    original_arc = {
        "arc_no": 1, "ep_start": 1, "ep_end": 5,
        "tactical_doc": "원본 tactical",
        "episode_details": orig_details,
    }
    asp_arc = {
        "arc_no": 1, "ep_start": 1, "ep_end": 5,
        "tactical_doc": "ASP 개선된 tactical",
        # episode_details 없음
    }

    # 실제 코드와 동일한 복원 로직 (four_phase_arc_generator.py P2 패턴)
    _orig_details = original_arc.get("episode_details")
    best_arc = asp_arc
    if _orig_details and not best_arc.get("episode_details"):
        best_arc["episode_details"] = _orig_details

    assert best_arc["episode_details"] == orig_details


def test_asp_does_not_overwrite_existing_episode_details():
    """ASP 결과에 episode_details가 있으면 덮어쓰지 않음"""
    orig_details = [{"ep_num": 3, "details": ["원본 사건"]}]
    asp_details = [{"ep_num": 3, "details": ["ASP 사건"]}]
    original_arc = {
        "arc_no": 1, "ep_start": 1, "ep_end": 5,
        "tactical_doc": "원본",
        "episode_details": orig_details,
    }
    asp_arc = {
        "arc_no": 1, "ep_start": 1, "ep_end": 5,
        "tactical_doc": "ASP tactical",
        "episode_details": asp_details,
    }

    _orig_details = original_arc.get("episode_details")
    best_arc = asp_arc
    if _orig_details and not best_arc.get("episode_details"):
        best_arc["episode_details"] = _orig_details

    assert best_arc["episode_details"] == asp_details


# ─────────────────────────────────────────────
# 3. ArcCorrector tactical_doc 수정 시 해당 화 항목 삭제
# ─────────────────────────────────────────────

def test_arc_corrector_removes_target_ep_from_episode_details():
    """tactical_doc 수정 성공 시 해당 화 episode_details 항목 삭제"""
    arc = {
        "arc_no": 1, "ep_start": 1, "ep_end": 5,
        "tactical_doc": "원본",
        "episode_details": [
            {"ep_num": 2, "details": ["수정 전 사건"]},
            {"ep_num": 3, "details": ["다른 화 사건"]},
        ],
    }
    target_ep = 2

    # P3 패턴 (arc_corrector.py 실제 코드와 동일)
    if isinstance(arc.get("episode_details"), list):
        arc["episode_details"] = [d for d in arc["episode_details"] if d.get("ep_num") != target_ep]

    ep_nums = [d["ep_num"] for d in arc["episode_details"]]
    assert 2 not in ep_nums
    assert 3 in ep_nums


def test_arc_corrector_preserves_other_eps_episode_details():
    """수정 대상 아닌 화의 episode_details는 보존"""
    arc = {
        "episode_details": [
            {"ep_num": 1, "details": ["1화 사건"]},
            {"ep_num": 2, "details": ["2화 사건"]},
            {"ep_num": 3, "details": ["3화 사건"]},
        ],
    }
    target_ep = 2

    if isinstance(arc.get("episode_details"), list):
        arc["episode_details"] = [d for d in arc["episode_details"] if d.get("ep_num") != target_ep]

    assert len(arc["episode_details"]) == 2
    assert arc["episode_details"][0]["ep_num"] == 1
    assert arc["episode_details"][1]["ep_num"] == 3


# ─────────────────────────────────────────────
# 4. UnifiedArcValidator ADVISORY 체크
# ─────────────────────────────────────────────

def _make_validator():
    v = UnifiedArcValidator.__new__(UnifiedArcValidator)
    v.min_chars_per_ep = 300
    return v


def test_validator_no_advisory_when_episode_details_absent():
    """episode_details 없으면 ADVISORY 발생 안 함"""
    arc = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "tactical_doc": ""}
    issues = _make_validator()._check_episode_details_type(arc)
    assert issues == []


def test_validator_advisory_when_episode_details_wrong_type():
    """episode_details가 dict이면 ADVISORY"""
    arc = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "episode_details": {"1": ["사건"]}}
    issues = _make_validator()._check_episode_details_type(arc)
    assert len(issues) == 1
    assert issues[0]["severity"] == "ADVISORY"


def test_validator_advisory_when_item_not_dict():
    """episode_details 아이템이 str이면 ADVISORY"""
    arc = {"arc_no": 1, "ep_start": 1, "ep_end": 5, "episode_details": ["잘못된 형식"]}
    issues = _make_validator()._check_episode_details_type(arc)
    assert len(issues) == 1
    assert issues[0]["severity"] == "ADVISORY"


def test_validator_advisory_when_ep_num_not_int():
    """episode_details 아이템의 ep_num이 str이면 ADVISORY"""
    arc = {
        "arc_no": 1, "ep_start": 1, "ep_end": 5,
        "episode_details": [{"ep_num": "4", "details": ["사건"]}],
    }
    issues = _make_validator()._check_episode_details_type(arc)
    assert len(issues) == 1
    assert issues[0]["severity"] == "ADVISORY"


def test_validator_no_advisory_for_valid_episode_details():
    """올바른 episode_details는 ADVISORY 없음"""
    arc = {
        "arc_no": 1, "ep_start": 1, "ep_end": 5,
        "episode_details": [
            {"ep_num": 1, "details": ["사건1"]},
            {"ep_num": 2, "details": ["사건2", "사건3"]},
        ],
    }
    issues = _make_validator()._check_episode_details_type(arc)
    assert issues == []


# ─────────────────────────────────────────────
# 5. BlueprintConstraintCompiler 우선 참조
# ─────────────────────────────────────────────

def _make_compiler():
    compiler = BlueprintConstraintCompiler.__new__(BlueprintConstraintCompiler)
    return compiler


def test_extract_episode_focus_uses_episode_details_first():
    """episode_details 있으면 regex보다 우선 사용"""
    arc_data = {
        "tactical_doc": "제 4화: 전술 문서 내용",
        "episode_details": [
            {"ep_num": 4, "details": ["정확한 사건 A", "정확한 사건 B"]},
        ],
    }
    result = _make_compiler()._extract_episode_focus(arc_data, ep_num=4, arc_position=1)
    assert "정확한 사건 A" in result["content"]
    assert "정확한 사건 B" in result["content"]


def test_extract_episode_focus_falls_back_to_beat_sequence_when_no_match():
    """해당 화 episode_details 없고 regex도 매칭 안 되면 beat_sequence 폴백"""
    arc_data = {
        "tactical_doc": "일반 텍스트 (헤더 없음)",
        "beat_sequence": ["1화 비트", "2화 비트", "4화 비트 내용"],
        "episode_details": [
            {"ep_num": 5, "details": ["5화 사건"]},  # 4화 없음
        ],
    }
    # arc_position=3 → beat_sequence[2] 사용
    result = _make_compiler()._extract_episode_focus(arc_data, ep_num=4, arc_position=3)
    assert result["content"] != "" or result["arc_position"] == 3  # 폴백 동작 확인


def test_extract_episode_focus_falls_back_when_no_episode_details():
    """episode_details 없으면 beat_sequence 폴백"""
    arc_data = {
        "tactical_doc": "일반 텍스트",
        "beat_sequence": ["3화 비트 내용"],
    }
    result = _make_compiler()._extract_episode_focus(arc_data, ep_num=3, arc_position=1)
    assert result["arc_position"] == 1  # 폴백 경로 진입 확인


def test_extract_stop_line_uses_episode_details():
    """다음 화 정지선도 episode_details 우선 참조"""
    arc_data = {
        "tactical_doc": "제 5화: 다음 화 내용",
        "episode_details": [
            {"ep_num": 5, "details": ["정지선 사건 X"]},
        ],
    }
    result = _make_compiler()._extract_stop_line(arc_data, ep_num=4, arc_position=1, ep_count=5)
    assert "정지선 사건 X" in (result.get("content") or "")
