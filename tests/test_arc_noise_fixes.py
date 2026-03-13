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
