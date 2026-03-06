"""InPlace patch 신뢰성 테스트 — 절단 방지 + deep merge + Pydantic 검증.

pipeline-run-audit-01 InPlace 조사 결과 P1 3건 패치 검증.
"""

import json
from unittest.mock import MagicMock, patch

from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator
from modules.domain.agents.three_phase_blueprint_generator import ThreePhaseBlueprintGenerator


def _make_arc_generator() -> FourPhaseArcGenerator:
    gen = object.__new__(FourPhaseArcGenerator)
    gen.ensemble = MagicMock()
    gen.host = MagicMock()
    return gen


def _make_bp_generator() -> ThreePhaseBlueprintGenerator:
    gen = object.__new__(ThreePhaseBlueprintGenerator)
    gen.ensemble = MagicMock()
    gen.host = MagicMock()
    gen.stats = {"total_attempts": 0}
    return gen


def _base_arc(**overrides) -> dict:
    arc = {
        "arc_no": 1,
        "ep_count": 4,
        "tactical_doc": "test tactical",
        "joint_docs": "docs",
        "state_constraints": {
            "arc_start_state": {"location": "서울", "equipment": ["폰"]},
            "arc_end_state": {"location": "부산", "assets": "10억"},
        },
        "state_changes": "changes",
        "episode_details": [],
    }
    arc.update(overrides)
    return arc


def _base_blueprint(**overrides) -> dict:
    bp = {
        "episode_number": 1,
        "scene_breakdown": {
            "scene_1": {"title": "도입"},
            "scene_2": {"title": "전개"},
        },
        "ending_hook": "다음 화에서...",
    }
    bp.update(overrides)
    return bp


class TestInPlaceTruncationGuard:
    """30KB 초과 JSON → return None (full rewrite 폴백)."""

    def test_arc_over_30kb_returns_none(self):
        gen = _make_arc_generator()
        big_arc = _base_arc(tactical_doc="x" * 35000)
        result = gen._inplace_patch_arc(
            original_arc=big_arc,
            director_feedback="수정 필요",
            arc_no=1,
        )
        assert result is None

    def test_blueprint_over_30kb_returns_none(self):
        gen = _make_bp_generator()
        big_bp = _base_blueprint(scene_breakdown={"scene_1": {"content": "y" * 35000}})
        result = gen._inplace_patch_blueprint(
            original_blueprint=big_bp,
            director_feedback="수정 필요",
            ep_num=1,
            arc_data={"tactical_doc": ""},
        )
        assert result is None

    def test_arc_under_30kb_proceeds(self):
        """30KB 이하면 정상 진행 (LLM 호출됨)."""
        gen = _make_arc_generator()
        small_arc = _base_arc()
        # LLM이 유효한 arc 반환하도록 mock
        gen.ensemble.ask.return_value = json.dumps(small_arc, ensure_ascii=False)
        gen.ensemble._extract_json_robust.return_value = dict(small_arc)
        result = gen._inplace_patch_arc(
            original_arc=small_arc,
            director_feedback="수정 필요",
            arc_no=1,
        )
        assert result is not None
        gen.ensemble.ask.assert_called_once()


class TestInPlaceDeepMerge:
    """1-depth deep merge — 중첩 dict 서브키 보존."""

    def test_arc_preserves_arc_start_state(self):
        """LLM이 state_constraints에서 arc_start_state를 누락해도 보존."""
        gen = _make_arc_generator()
        original = _base_arc()
        # LLM이 arc_end_state만 반환, arc_start_state 누락
        llm_result = {
            "arc_no": 1,
            "ep_count": 4,
            "tactical_doc": "patched",
            "joint_docs": "docs",
            "state_constraints": {
                "arc_end_state": {"location": "대전", "assets": "20억"},
            },
            "state_changes": "changes",
            "episode_details": [],
        }
        gen.ensemble.ask.return_value = json.dumps(llm_result, ensure_ascii=False)
        gen.ensemble._extract_json_robust.return_value = dict(llm_result)

        result = gen._inplace_patch_arc(
            original_arc=original,
            director_feedback="수정 필요",
            arc_no=1,
        )
        assert result is not None
        sc = result.get("state_constraints", {})
        # arc_start_state가 원본에서 복원되어야 함
        assert "arc_start_state" in sc
        assert sc["arc_start_state"]["location"] == "서울"

    def test_arc_patched_subkey_not_overwritten(self):
        """LLM이 반환한 sub-key는 원본으로 덮어쓰지 않음."""
        gen = _make_arc_generator()
        original = _base_arc()
        llm_result = {
            "arc_no": 1,
            "ep_count": 4,
            "tactical_doc": "patched",
            "joint_docs": "docs",
            "state_constraints": {
                "arc_start_state": {"location": "인천", "equipment": ["새장비"]},
                "arc_end_state": {"location": "대전", "assets": "20억"},
            },
            "state_changes": "changes",
            "episode_details": [],
        }
        gen.ensemble.ask.return_value = json.dumps(llm_result, ensure_ascii=False)
        gen.ensemble._extract_json_robust.return_value = dict(llm_result)

        result = gen._inplace_patch_arc(
            original_arc=original,
            director_feedback="수정 필요",
            arc_no=1,
        )
        sc = result["state_constraints"]
        # LLM이 반환한 값은 유지
        assert sc["arc_start_state"]["location"] == "인천"
        assert sc["arc_end_state"]["location"] == "대전"

    def test_blueprint_preserves_missing_subkeys(self):
        """S3: LLM이 scene_breakdown의 일부 씬만 반환 — 나머지 복원."""
        gen = _make_bp_generator()
        original = _base_blueprint()
        llm_result = {
            "episode_number": 1,
            "scene_breakdown": {
                "scene_1": {"title": "수정된 도입"},
                # scene_2 누락
            },
            "ending_hook": "수정됨",
        }
        gen.ensemble.ask.return_value = json.dumps(llm_result, ensure_ascii=False)
        gen.ensemble._extract_json_robust.return_value = dict(llm_result)

        with patch("modules.domain.agents.three_phase_blueprint_generator.validate_blueprint", side_effect=lambda x: x):
            result = gen._inplace_patch_blueprint(
                original_blueprint=original,
                director_feedback="수정 필요",
                ep_num=1,
                arc_data={"tactical_doc": ""},
            )
        assert result is not None
        sb = result["scene_breakdown"]
        assert "scene_1" in sb
        assert "scene_2" in sb  # 원본에서 복원
        assert sb["scene_1"]["title"] == "수정된 도입"  # LLM 값 유지
        assert sb["scene_2"]["title"] == "전개"  # 원본 복원


class TestS2PydanticValidation:
    """S2 InPlace 후 validate_arc() 호출 확인."""

    def test_arc_inplace_calls_validate_arc(self):
        gen = _make_arc_generator()
        original = _base_arc()
        gen.ensemble.ask.return_value = json.dumps(original, ensure_ascii=False)
        gen.ensemble._extract_json_robust.return_value = dict(original)

        with patch("modules.models.arc.validate_arc", wraps=lambda x: x) as mock_va:
            result = gen._inplace_patch_arc(
                original_arc=original,
                director_feedback="수정",
                arc_no=1,
            )
        assert result is not None
        assert result["arc_no"] == 1
        mock_va.assert_called_once()
