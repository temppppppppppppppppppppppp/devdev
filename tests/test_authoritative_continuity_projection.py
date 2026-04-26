import json

from modules.core.authoritative_continuity_projection import (
    AUTHORITATIVE_CONTINUITY_PROJECTION_HEADER,
    build_authoritative_continuity_projection,
    render_authoritative_continuity_projection_for_prompt,
    summarize_authoritative_continuity_projection,
)


def test_projection_separates_approved_and_pending_bridge_proposals():
    projection = build_authoritative_continuity_projection(
        ep_num=4,
        arc_data={
            "arc_no": 2,
            "ep_start": 4,
            "ep_end": 8,
            "constraint_summary": "Do not reset the liquidation timeline.",
            "state_constraints": {"arc_start_state": {"location": "boardroom"}},
        },
        accepted_blueprint={
            "ep_num": 3,
            "end_location": "boardroom",
            "time_flow": "2006-01-03 evening",
            "ending_hook": "The board vote remains unresolved.",
        },
        bridge_proposals=[
            {
                "bridge_id": "bridge-approved",
                "target_stage": "stage4",
                "applied_status": "approved",
                "allowed_fix_scope": "candidate_only",
                "proposed_bridge": json.dumps({"ending_state.timeline": "2006-01-03"}, ensure_ascii=False),
                "director_verdict": "APPROVE",
            },
            {
                "bridge_id": "bridge-pending",
                "target_stage": "stage4",
                "applied_status": "pending_director",
                "proposed_bridge": json.dumps({"ending_state.location": "boardroom"}, ensure_ascii=False),
            },
        ],
        source_stage="stage3_blueprint",
        target_stage="stage4_manuscript",
    )

    bridges = projection["bridge_proposals"]
    assert bridges["approved"][0]["bridge_id"] == "bridge-approved"
    assert bridges["pending_director"][0]["bridge_id"] == "bridge-pending"
    assert projection["mutation_policy"] == "python_may_collect_and_route_only"

    rendered = render_authoritative_continuity_projection_for_prompt(projection)

    assert rendered.startswith(AUTHORITATIVE_CONTINUITY_PROJECTION_HEADER)
    assert "Director/LLM remains final narrative judge" in rendered
    assert "pending_director_bridge_count: 1" in rendered
    assert "do not apply as fact until Director approves" in rendered


def test_projection_summary_is_small_and_operational():
    projection = build_authoritative_continuity_projection(
        ep_num=2,
        arc_data={"arc_no": 1},
        accepted_blueprint={"ep_num": 1, "end_location": "hall", "time_flow": "immediately after"},
        source_stage="stage3_blueprint",
        target_stage="stage4_manuscript",
    )

    summary = summarize_authoritative_continuity_projection(projection)

    assert summary["schema_version"] == "authoritative-continuity-projection-v1"
    assert summary["source_stage"] == "stage3_blueprint"
    assert summary["target_stage"] == "stage4_manuscript"
    assert summary["non_regression_anchor_count"] >= 2
    assert "end_location" in summary["accepted_source_fields"]
