from modules.core.constants import GenreTypes
from modules.domain.agents.blueprint_ensemble import build_genre_strategy_contract
from modules.domain.agents.director_ensemble import (
    _collect_compare_candidate_advisories,
    _format_compare_python_warning_block,
)


def test_compare_python_warning_block_includes_advisory_fix_pack_summary():
    block = _format_compare_python_warning_block(
        {
            "prevalidation_issue_count": 2,
            "quality_risk": False,
            "advisory_fix_pack": {
                "patch_targets": ["integrated_scenario"],
                "patch_target_records": [
                    {
                        "summary": "integrated_scenario",
                        "field_path": "integrated_scenario",
                        "target_kind": "local_sentence",
                    }
                ],
                "target_kind": "local_sentence",
                "must_fix": ["add one named market anchor"],
                "evidence_summary": "anchor_count=0",
            },
        }
    )

    assert "- issue_count: 2" in block
    assert "- advisory_target_kind: local_sentence" in block
    assert "- advisory_evidence: anchor_count=0" in block
    assert "- advisory_focus: add one named market anchor" in block


def test_collect_compare_candidate_advisories_surfaces_advisory_fix_pack():
    advisories = _collect_compare_candidate_advisories(
        [
            {
                "_ensemble_meta": {
                    "strategy": "steady",
                    "prevalidation_issue_count": 1,
                    "quality_risk": False,
                    "advisory_fix_pack": {
                        "patch_targets": ["integrated_scenario"],
                        "patch_target_records": [
                            {
                                "summary": "integrated_scenario",
                                "field_path": "integrated_scenario",
                                "target_kind": "local_sentence",
                            }
                        ],
                        "target_kind": "local_sentence",
                        "must_fix": ["add one named market anchor"],
                        "evidence_summary": "anchor_count=0",
                    },
                }
            }
        ]
    )

    assert advisories[0]["candidate_index"] == 0
    assert advisories[0]["strategy"] == "steady"
    assert advisories[0]["advisory_target_kind"] == "local_sentence"
    assert advisories[0]["advisory_fix_pack"]["patch_targets"] == ["integrated_scenario"]
    assert advisories[0]["advisory_fix_pack"]["evidence_summary"] == "anchor_count=0"


def test_collect_compare_candidate_advisories_surfaces_genre_strategy_contract_summary():
    contract = build_genre_strategy_contract(GenreTypes.INVESTMENT, "action_focused")

    advisories = _collect_compare_candidate_advisories(
        [
            {
                "_ensemble_meta": {
                    "strategy": "action_focused",
                    "genre_strategy_contract": contract,
                }
            }
        ]
    )

    summary = advisories[0]["genre_strategy_contract"]
    assert summary["contract_id"] == "investment_business_power.action_focused.v1"
    assert summary["contract_hash"] == contract["contract_hash"]
    assert summary["authority_level"] == "route"
