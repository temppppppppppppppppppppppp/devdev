import logging
from unittest.mock import MagicMock

from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator
from modules.domain.agents.director_continuity import DirectorContinuityValidator
from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator


def test_arc_noise1_investment_no_internal_energy_warning(caplog):
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen._genre = "investment"

    arc = {
        "state_constraints": {"arc_end_state": {"injuries": "없음", "internal_energy": 90}},
        "status_shadow": {"expected_injuries": "없음"},
    }

    with caplog.at_level(logging.WARNING):
        gen._check_arc_end_state(arc)

    assert not any("내공 미복원" in rec.message for rec in caplog.records)


def test_arc_noise1_wuxia_still_warns(caplog):
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen._genre = "wuxia"

    arc = {
        "state_constraints": {"arc_end_state": {"injuries": "없음", "internal_energy": 90}},
        "status_shadow": {"expected_injuries": "없음"},
    }

    with caplog.at_level(logging.WARNING):
        gen._check_arc_end_state(arc)

    assert any("내공 미복원" in rec.message for rec in caplog.records)


def test_arc_noise2_prohibition_summary_clean():
    gen = ArcEnsembleGenerator.__new__(ArcEnsembleGenerator)
    constraint = "│   ❌ 한미증권 해외 선물 계좌 거래내역서 (Arc 1에서 획득)                    │"

    result = gen._generate_prohibition_summary("", constraint)

    assert "│" not in result
    assert "Arc 1에서" not in result
    assert "한미증권 해외 선물 계좌 거래내역서" in result


def _make_continuity_validator(extract_result: dict) -> DirectorContinuityValidator:
    director = MagicMock()
    director.entity_consistency_enabled = True
    director._escape_braces.side_effect = lambda value: value
    director.ask.return_value = "raw"
    director._extract_json_robust.return_value = extract_result
    return DirectorContinuityValidator(director)


def test_arc_noise3_abbreviation_filtered():
    validator = _make_continuity_validator(
        {
            "decision": "WARNING",
            "mismatches": [
                {
                    "category": "concept",
                    "registered_name": "WTI 원유 선물 6월물 롱 포지션",
                    "found_variant": "WTI 6월물 롱 포지션",
                    "severity": "MAJOR",
                    "context": "WTI 6월물 롱 포지션 진입",
                }
            ],
            "fix_instructions": "용어 통일",
        }
    )

    result = validator.validate_entity_consistency(
        content="WTI 6월물 롱 포지션 진입",
        entity_registry={"concepts": [{"name": "WTI 원유 선물 6월물 롱 포지션"}]},
        content_type="arc",
    )

    assert result["mismatches"] == []
    assert result["decision"] == "PASS"


def test_arc_noise3_location_alias_filtered():
    validator = _make_continuity_validator(
        {
            "decision": "WARNING",
            "mismatches": [
                {
                    "category": "location",
                    "registered_name": "사무실",
                    "found_variant": "오피스",
                    "severity": "MAJOR",
                    "context": "오피스에서 회의를 시작한다",
                }
            ],
            "fix_instructions": "장소 표기 통일",
        }
    )

    result = validator.validate_entity_consistency(
        content="오피스에서 회의를 시작한다",
        entity_registry={"locations": [{"name": "사무실"}]},
        content_type="arc",
    )

    assert result["mismatches"] == []
    assert result["decision"] == "PASS"


def test_arc_noise3_real_mismatch_passes_through():
    validator = _make_continuity_validator(
        {
            "decision": "WARNING",
            "mismatches": [
                {
                    "category": "character",
                    "registered_name": "박성호",
                    "found_variant": "이성호",
                    "severity": "MAJOR",
                    "context": "이성호가 등장한다",
                }
            ],
            "fix_instructions": "이름 통일",
        }
    )

    result = validator.validate_entity_consistency(
        content="이성호가 등장한다",
        entity_registry={"characters": [{"name": "박성호"}]},
        content_type="arc",
    )

    assert result["decision"] == "WARNING"
    assert len(result["mismatches"]) == 1
    assert result["mismatches"][0]["registered_name"] == "박성호"


def test_arc_noise3_market_move_alias_filtered():
    validator = _make_continuity_validator(
        {
            "decision": "WARNING",
            "mismatches": [
                {
                    "category": "concept",
                    "registered_name": "유가 급등",
                    "found_variant": "원유 랠리",
                    "severity": "MAJOR",
                    "context": "원유 랠리가 시장을 흔든다",
                }
            ],
            "fix_instructions": "용어 통일",
        }
    )

    result = validator.validate_entity_consistency(
        content="원유 랠리가 시장을 흔든다",
        entity_registry={"concepts": [{"name": "유가 급등"}]},
        content_type="blueprint",
    )

    assert result["mismatches"] == []
    assert result["decision"] == "PASS"
    assert result["fix_instructions"] == ""


def test_arc_noise3_named_event_alias_filtered():
    validator = _make_continuity_validator(
        {
            "decision": "WARNING",
            "mismatches": [
                {
                    "category": "concept",
                    "registered_name": "리먼 브라더스 사태",
                    "found_variant": "리먼 브라더스의 파산",
                    "severity": "MAJOR",
                    "context": "리먼 브라더스의 파산 이후 시장이 무너졌다",
                }
            ],
            "fix_instructions": "용어 통일",
        }
    )

    result = validator.validate_entity_consistency(
        content="리먼 브라더스의 파산 이후 시장이 무너졌다",
        entity_registry={"concepts": [{"name": "리먼 브라더스 사태"}]},
        content_type="blueprint",
    )

    assert result["mismatches"] == []
    assert result["decision"] == "PASS"


def test_arc_noise3_generic_location_surface_downgraded():
    validator = _make_continuity_validator(
        {
            "decision": "REJECT",
            "mismatches": [
                {
                    "category": "location",
                    "registered_name": "서울 성북동 본가",
                    "found_variant": "저택",
                    "severity": "MAJOR",
                    "context": "저택 복도에서 내려다본다",
                }
            ],
            "fix_instructions": "장소 표기 통일",
        }
    )

    result = validator.validate_entity_consistency(
        content="저택 복도에서 내려다본다",
        entity_registry={"locations": [{"name": "서울 성북동 본가"}]},
        content_type="blueprint",
    )

    assert result["decision"] == "PASS"
    assert result["mismatches"][0]["severity"] == "MINOR"
    assert result["mismatches"][0]["normalization_note"] == "generic_location_surface"


def test_arc_noise3_generic_role_surface_downgraded():
    validator = _make_continuity_validator(
        {
            "decision": "REJECT",
            "mismatches": [
                {
                    "category": "character",
                    "registered_name": "가사도우미",
                    "found_variant": "집사",
                    "severity": "MAJOR",
                    "context": "집사가 문을 열었다",
                }
            ],
            "fix_instructions": "호칭 통일",
        }
    )

    result = validator.validate_entity_consistency(
        content="집사가 문을 열었다",
        entity_registry={"characters": [{"name": "가사도우미"}]},
        content_type="blueprint",
    )

    assert result["decision"] == "PASS"
    assert result["mismatches"][0]["severity"] == "MINOR"
    assert result["mismatches"][0]["normalization_note"] == "generic_role_surface"


def test_arc_noise3_object_surface_variant_downgraded():
    validator = _make_continuity_validator(
        {
            "decision": "WARNING",
            "mismatches": [
                {
                    "category": "object",
                    "registered_name": "구형 피처폰",
                    "found_variant": "은색 피처폰",
                    "severity": "MAJOR",
                    "context": "은색 피처폰을 꺼내 통화했다",
                }
            ],
            "fix_instructions": "아이템 표기 통일",
        }
    )

    result = validator.validate_entity_consistency(
        content="은색 피처폰을 꺼내 통화했다",
        entity_registry={"objects": [{"name": "구형 피처폰"}]},
        content_type="blueprint",
    )

    assert result["decision"] == "PASS"
    assert result["mismatches"][0]["severity"] == "MINOR"
    assert result["mismatches"][0]["normalization_note"] == "object_surface_variant"


def test_arc_noise3_prompt_mentions_surface_alias_examples():
    director = MagicMock()
    director.entity_consistency_enabled = True
    director._escape_braces.side_effect = lambda value: value
    director.ask.return_value = "raw"
    director._extract_json_robust.return_value = {"decision": "PASS", "mismatches": [], "fix_instructions": ""}
    validator = DirectorContinuityValidator(director)

    validator.validate_entity_consistency(
        content="서울 성북동 본가에서 집사가 피처폰을 건넨다",
        entity_registry={"locations": [{"name": "서울 성북동 본가"}]},
        content_type="blueprint",
    )

    prompt = director.ask.call_args.args[0]
    assert "서울 성북동 본가" in prompt
    assert "저택" in prompt
    assert "리먼 브라더스 사태" in prompt
    assert "원유 랠리" in prompt
    assert "집사" in prompt
    assert "가사도우미" in prompt
