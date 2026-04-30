import hashlib

from modules.core.blueprint_lineage import (
    BLUEPRINT_LINEAGE_SCHEMA_VERSION,
    FRONTIER_BASIS_VERSION,
    attach_stage3_blueprint_lineage_meta,
    build_stage3_blueprint_lineage_meta,
)


class _Db:
    def __init__(self, rows):
        self.rows = rows

    def get_final_accepted_episode_context(self, ep_num, *, stage=4):
        return self.rows.get(ep_num)


def test_build_lineage_meta_records_final_accepted_prev_manuscript():
    prev_text = "accepted previous manuscript"
    db = _Db({1: {"content": prev_text, "manuscript_created_at": "2026-04-30T00:00:00"}})
    blueprint = {
        "_ensemble_meta": {
            "genre_strategy_contract": {
                "contract_id": "investment_business_power.action_focused.v1",
            }
        }
    }

    meta = build_stage3_blueprint_lineage_meta(db=db, ep_num=2, blueprint=blueprint, generated_at="now")

    assert meta["lineage_schema_version"] == BLUEPRINT_LINEAGE_SCHEMA_VERSION
    assert meta["frontier_basis_version"] == FRONTIER_BASIS_VERSION
    assert meta["source_prev_manuscript_ep"] == 1
    assert meta["source_prev_manuscript_hash"] == hashlib.sha256(prev_text.encode("utf-8")).hexdigest()
    assert meta["source_prev_manuscript_created_at"] == "2026-04-30T00:00:00"
    assert meta["lineage_complete"] is True
    assert meta["lineage_missing_reason"] == ""
    assert meta["genre_strategy_contract_id"] == "investment_business_power.action_focused.v1"


def test_build_lineage_meta_records_contract_transport_proof_fields():
    db = _Db({1: {"content": "accepted previous manuscript"}})
    blueprint = {
        "_ensemble_meta": {
            "genre_strategy_contract": {
                "contract_id": "investment_business_power.action_focused.v1",
                "contract_hash": "abc123",
                "authority_level": "route",
                "strategy_name": "action_focused",
            },
            "prompt_envelope": {
                "genre_strategy_contract_coverage": [
                    {
                        "strategy_name": "action_focused",
                        "coverage_outcome": "route_contract_applied",
                    }
                ]
            },
        }
    }

    meta = build_stage3_blueprint_lineage_meta(db=db, ep_num=2, blueprint=blueprint, generated_at="now")

    assert meta["genre_strategy_contract_id"] == "investment_business_power.action_focused.v1"
    assert meta["genre_strategy_contract_hash"] == "abc123"
    assert meta["genre_strategy_contract_authority_level"] == "route"
    assert meta["genre_strategy_contract_strategy"] == "action_focused"
    assert meta["genre_strategy_contract_source"] == "_ensemble_meta.genre_strategy_contract"
    assert meta["genre_strategy_contract_coverage_outcome"] == "route_contract_applied"


def test_build_lineage_meta_uses_selected_strategy_for_prompt_envelope_contracts():
    db = _Db({1: {"content": "accepted previous manuscript"}})
    blueprint = {
        "_ensemble_meta": {
            "strategy": "emotion_focused",
            "prompt_envelope": {
                "genre_strategy_contracts": [
                    {
                        "strategy_name": "action_focused",
                        "contract_id": "investment_business_power.action_focused.v1",
                        "contract_hash": "abc123",
                        "authority_level": "route",
                    }
                ],
                "genre_strategy_contract_coverage": [
                    {
                        "strategy_name": "action_focused",
                        "coverage_outcome": "route_contract_applied",
                    },
                    {
                        "strategy_name": "emotion_focused",
                        "coverage_outcome": "no_route_specific_contract_required",
                    },
                ],
            },
        }
    }

    meta = build_stage3_blueprint_lineage_meta(db=db, ep_num=2, blueprint=blueprint, generated_at="now")

    assert "genre_strategy_contract_id" not in meta
    assert meta["genre_strategy_contract_strategy"] == "emotion_focused"
    assert meta["genre_strategy_contract_coverage_outcome"] == "no_route_specific_contract_required"


def test_build_lineage_meta_marks_no_prior_episode_complete():
    meta = build_stage3_blueprint_lineage_meta(db=_Db({}), ep_num=1, blueprint={}, generated_at="now")

    assert meta["source_prev_manuscript_ep"] == 0
    assert meta["source_prev_manuscript_hash"] == ""
    assert meta["lineage_complete"] is True
    assert meta["lineage_missing_reason"] == "no_prior_episode"


def test_build_lineage_meta_marks_missing_prev_manuscript_incomplete():
    meta = build_stage3_blueprint_lineage_meta(db=_Db({}), ep_num=3, blueprint={}, generated_at="now")

    assert meta["source_prev_manuscript_ep"] == 2
    assert meta["source_prev_manuscript_hash"] == ""
    assert meta["lineage_complete"] is False
    assert meta["lineage_missing_reason"] == "missing_final_accepted_prev_manuscript"


def test_attach_lineage_meta_preserves_existing_stage3_fields():
    blueprint = {"_stage3_meta": {"final_verdict": "PASS", "generated_at": "existing"}}

    attach_stage3_blueprint_lineage_meta(blueprint, db=_Db({}), ep_num=1)

    assert blueprint["_stage3_meta"]["final_verdict"] == "PASS"
    assert blueprint["_stage3_meta"]["generated_at"] == "existing"
    assert blueprint["_stage3_meta"]["lineage_complete"] is True
