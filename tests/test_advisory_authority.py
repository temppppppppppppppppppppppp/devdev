from modules.core.advisory_authority import (
    ensure_stage4_historical_companion_authority,
    ensure_stage4_route_authority,
)


def test_stage4_route_authority_promotes_historical_companion_payloads():
    historical = ensure_stage4_historical_companion_authority(
        {
            "fix_pack": {"target_kind": "scene_model"},
            "retry_budget_axes": {"repair": "patch_revision"},
        },
        source="director_selections",
    )

    promoted = ensure_stage4_route_authority(
        historical,
        route_payloads={
            "fix_pack": {"target_kind": "scene_model"},
            "retry_budget_axes": {"repair": "patch_revision"},
        },
        source="stage_attempts",
    )

    assert promoted["advisory_authority_levels"]["fix_pack"] == "route"
    assert promoted["advisory_authority_levels"]["retry_budget_axes"] == "route"
    assert promoted["advisory_authority_sources"]["fix_pack"] == "stage_attempts"


def test_stage4_historical_companion_authority_does_not_demote_route_payloads():
    routed = ensure_stage4_route_authority(
        {
            "repair_contract": {"subtype": "movement"},
            "scope_authority": {"fix_scope": "partial"},
        },
        source="stage_attempts",
    )

    historical = ensure_stage4_historical_companion_authority(
        routed,
        source="director_selections",
    )

    assert historical["advisory_authority_levels"]["repair_contract"] == "route"
    assert historical["advisory_authority_levels"]["scope_authority"] == "route"
    assert historical["advisory_authority_sources"]["repair_contract"] == "stage_attempts"
