from __future__ import annotations

from scripts.stage0_handoff_validator import _validate_material_bundle_summary, _validate_phase0_design


def _opening_bundle_contract(**overrides) -> dict:
    contract = {
        "bundle_window": "TR 2~6",
        "macro_battlefield": "장례식장 뒤문",
        "macro_battlefield_map": ["밥차", "셔틀", "세탁실"],
        "bundle_goal": "첫 반복매출과 대표 재평가를 번들 안에서 벌어야 한다.",
        "first_signboard_block": 3,
        "representative_reevaluation_block": 4,
        "next_battlefield_ticket_block": 6,
        "timing_reconciliation_note": "Arc는 길어도 reader-earning은 TR 2~6에서 끝낸다.",
    }
    contract.update(overrides)
    return contract


def test_material_bundle_summary_accepts_valid_opening_bundle_contract() -> None:
    errors = _validate_material_bundle_summary(
        {
            "events": [],
            "npc_candidates": [],
            "crisis_candidates": [],
            "terms": [],
            "scene_details": [],
            "notes": "ok",
            "opening_bundle_contract": _opening_bundle_contract(),
        }
    )

    assert errors == []


def test_material_bundle_summary_rejects_opening_bundle_contract_outside_tr_2_6() -> None:
    errors = _validate_material_bundle_summary(
        {
            "events": [],
            "npc_candidates": [],
            "crisis_candidates": [],
            "terms": [],
            "scene_details": [],
            "notes": "ok",
            "opening_bundle_contract": _opening_bundle_contract(first_signboard_block=7),
        }
    )

    assert any("first_signboard_block" in error for error in errors)


def test_phase0_design_rejects_blank_opening_bundle_contract_fields() -> None:
    errors = _validate_phase0_design(
        {
            "phase0_design": {
                "opening_bundle_contract": _opening_bundle_contract(
                    bundle_goal="",
                    macro_battlefield_map=["밥차", ""],
                )
            }
        }
    )

    assert any("bundle_goal" in error for error in errors)
    assert any("macro_battlefield_map" in error for error in errors)
